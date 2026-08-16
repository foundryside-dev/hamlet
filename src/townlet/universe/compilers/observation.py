"""Observation-domain compiler boundary."""

from __future__ import annotations

from typing import Any, Literal, cast

import torch

from townlet.config.curriculum_config import CurriculumConfig
from townlet.config.environment_config import (
    EnvironmentConfig as EnvConfigV21,
)
from townlet.config.environment_config import (
    MeterRangeBinary,
    MeterRangeCyclicalSinCos,
    MeterRangeLogScaled,
    MeterRangeMaskedValue,
    MeterRangeMinMax,
    MeterRangeNone,
    MeterRangeOneHot,
    MeterRangeRankScaled,
    MeterRangeZScore,
)
from townlet.config.items_config import ItemsCatalogConfig
from townlet.config.stratum_config import ObservationModeConfig, StratumConfig
from townlet.effects.catalog import EffectCatalog
from townlet.substrate.factory import SubstrateFactory
from townlet.universe.compiled import CompiledVFSProfiles
from townlet.universe.dto import ObservationActivity, ObservationField, ObservationSpec
from townlet.universe.validation.limits import EFFECT_OBSERVATION_SLOTS
from townlet.vfs.observation_builder import VFSObservationSpec, agent_can_observe, profile_variable_observation_dim
from townlet.vfs.schema import NormalizationSpec, VariableDef
from townlet.vfs.schema import ObservationField as VFSObservationField
from townlet.vfs.semantic_type import METER_BLOCK_SEMANTIC, SEMANTIC_GROUP_ORDER

# Per-meter observation identifiers are NAMESPACED, and the prefix is load-bearing rather
# than cosmetic. Two in-tree mechanisms make a bare meter name unusable as a variable id:
#
#   1. `vtc.py::VTCActionWriteProgram.apply` merges the VFS registry snapshot and the bars
#      dict into ONE evaluation namespace and RAISES on a collision. A variable literally
#      named `energy` beside the bar `energy` would break every pack that writes a bar.
#   2. `build_vfs_variables` skips any observation field whose name matches a declared
#      `environment.variables[]` entry — so a collision would silently produce a field with
#      no backing variable, which is PDR-0053 shape #5 (accepted then dropped).
#
# `_assert_meter_ids_are_disjoint` turns both into a compile error rather than trusting the
# prefix to be lucky.
METER_OBSERVATION_PREFIX = "obs_meter_"

# The ONE compiler-emitted feature over an agent's item slots: the exposed variables of the
# item in each slot, slot-major, positional within a slot (PDR-0075; layout question filed as
# hamlet-1ad6383186). Defined once here and imported by the runtime's sync step — a shared
# symbol, not two literals — so the encoder publishes the feature under the name the compiler
# declared for it. Global and agent profile variables are NOT routed through this field: each
# compiles to its own observation field named after the variable.
ITEM_SLOTS_OBSERVATION_FIELD = "obs_item_slots"

# Widths the VFS normalization kinds produce from a 1-wide source
# (`vfs/observation_builder.py::apply_normalization`): `cyclical_sin_cos` concatenates sin
# and cos, `one_hot` expands to its category count, and every other kind is width-preserving.
_WIDTH_PRESERVING_KINDS = frozenset({"none", "minmax", "zscore", "binary", "log_scaled", "rank_scaled", "masked_value"})


def meter_observation_field_name(meter_name: str) -> str:
    """The observation field / VFS variable id for a meter. One definition, no f-strings at
    call sites — this string is baked into `observation_field_uuids` in every checkpoint."""
    return f"{METER_OBSERVATION_PREFIX}{meter_name}"


def meter_name_from_observation_field(field_name: str) -> str:
    """Inverse of `meter_observation_field_name`. Raises rather than guessing.

    Only ever called on fields the compiler emitted with `semantic_type="bars"`, so a name
    without the prefix means something else got into the bars group — which is a defect
    worth a loud failure, not a silently skipped meter.
    """
    if not field_name.startswith(METER_OBSERVATION_PREFIX):
        raise ValueError(
            f"Observation field '{field_name}' carries semantic_type 'bars' but is not a meter "
            f"observation (expected the '{METER_OBSERVATION_PREFIX}' prefix)."
        )
    return field_name[len(METER_OBSERVATION_PREFIX) :]


def meter_observed_width(range_type: Any) -> int:
    """How many observation dimensions a meter's declared type occupies.

    The meter's SOURCE is always one scalar; this is the width AFTER normalization, and the
    two differ for exactly the two widening kinds. Keeping the arithmetic here — rather than
    inline at the emitter — is what lets the field emitter, the VFS variable builder and the
    contiguity assertion agree by construction instead of by coincidence.
    """
    kind = range_type.kind
    if kind == "cyclical_sin_cos":
        return 2
    if kind == "one_hot":
        return int(range_type.categories)
    if kind in _WIDTH_PRESERVING_KINDS:
        return 1
    raise ValueError(
        f"Meter range_type '{kind}' has no declared observed width.\n"
        "  Rule: every member of the range_type vocabulary must state its width here. "
        "A new member added to the DTO without a width is a compile error, not a default of 1."
    )


class ObservationCompiler:
    """Compile observation specs and their VFS-facing artifacts."""

    def build_spec(
        self,
        stratum: StratumConfig,
        environment: EnvConfigV21,
        curriculum: CurriculumConfig,
        compiled_vfs_profiles: CompiledVFSProfiles | None = None,
        items_catalog: ItemsCatalogConfig | None = None,
        compiled_effect_catalog: EffectCatalog | None = None,
    ) -> ObservationSpec:
        """Build observation spec using Support/Active pattern for v2.1."""
        fields: list[ObservationField] = []
        offset = 0

        substrate = stratum.stratum.substrate
        vision_support = stratum.stratum.vision_support
        temporal_support = stratum.stratum.temporal_support
        active_vision = curriculum.curriculum.active_vision
        vision_range = curriculum.curriculum.vision_range
        active_temporal = curriculum.curriculum.active_temporal

        canon_active_vision = "partial" if active_vision in {"local", "partial"} else "global"

        if canon_active_vision == "global" and vision_support not in {"global", "both"}:
            raise ValueError(
                "Invalid vision configuration: curriculum.active_vision='global' but "
                f"stratum.vision_support='{vision_support}'. "
                "active_vision='global' requires vision_support to be 'global' or 'both'."
            )
        if canon_active_vision == "partial" and vision_support not in {"partial", "both"}:
            raise ValueError(
                "Invalid vision configuration: curriculum.active_vision indicates partial/local vision but "
                f"stratum.vision_support='{vision_support}'. "
                "Partial observability requires vision_support to be 'partial' or 'both'."
            )

        # The substrate INSTANCE is the single authority on observation shape
        # (WS-7 first knockdown, PDR-0035): every spatial dim below is asked,
        # never re-derived from substrate.type strings. The instance is built
        # through the same factory door the runtime uses, so the compiled
        # widths cannot drift from what the runtime encoders produce — the
        # drift was DIV-003's three crashes. A config the factory rejects
        # fails compilation loudly, before any level artifact exists.
        try:
            substrate_instance = SubstrateFactory.build(substrate, torch.device("cpu"))
        except Exception as exc:
            raise ValueError(
                "Failed to build substrate instance for observation dimension calculation. "
                "Fix the substrate config; compiler observation dimensions must come from the runtime substrate implementation."
            ) from exc

        grid_cells = substrate_instance.get_grid_encoding_dim()

        if vision_support in {"both", "global"} and grid_cells:
            dims = grid_cells
            is_active = canon_active_vision == "global"
            # Descriptions are presentation only — every dim above came from
            # the instance. gridnd keeps its historical wording byte-for-byte.
            width = getattr(substrate_instance, "width", 0)
            height = getattr(substrate_instance, "height", 0)
            if hasattr(substrate_instance, "dimension_sizes"):
                desc = f"{dims}-cell gridnd encoding"
            elif width and height:
                depth = getattr(substrate_instance, "depth", None)
                desc = f"{width}x{height}x{depth} grid encoding" if depth is not None else f"{width}x{height} grid encoding"
            else:
                desc = "Global grid encoding"
            fields.append(
                ObservationField(
                    uuid=None,
                    name="obs_grid_encoding",
                    type="spatial_grid",
                    dims=dims,
                    start_index=offset,
                    end_index=offset + dims,
                    scope="agent",
                    description=desc,
                    semantic_type="spatial",
                    curriculum_active=is_active,
                )
            )
            offset += dims

        if vision_support in {"both", "partial"}:
            if substrate_instance.supports_partial_vision:
                radius = substrate_instance.get_vision_radius(vision_range)
                dims = substrate_instance.get_partial_window_dim(radius)
                window_span = 2 * radius + 1
                is_active = canon_active_vision == "partial"
                desc = "x".join([str(window_span)] * substrate_instance.position_dim) + " local window"
                fields.append(
                    ObservationField(
                        uuid=None,
                        name="obs_local_window",
                        type="spatial_grid",
                        dims=dims,
                        start_index=offset,
                        end_index=offset + dims,
                        scope="agent",
                        description=desc,
                        semantic_type="spatial",
                        curriculum_active=is_active,
                    )
                )
                offset += dims
            elif canon_active_vision == "partial":
                raise ValueError(
                    f"Partial observability (local vision) is not supported for {substrate.type} substrates. "
                    "Use active_vision='global' or vision_support='global'/'both' with grid substrates."
                )

        position_dim = substrate_instance.get_position_feature_dim()
        velocity_dim = substrate_instance.position_dim

        if position_dim:
            fields.append(
                ObservationField(
                    uuid=None,
                    name="obs_position",
                    type="vector",
                    dims=position_dim,
                    start_index=offset,
                    end_index=offset + position_dim,
                    scope="agent",
                    description=f"Agent position ({position_dim}D)",
                    semantic_type="spatial",
                )
            )
            offset += position_dim

        if velocity_dim:
            fields.append(
                ObservationField(
                    uuid=None,
                    name="obs_velocity",
                    type="vector",
                    dims=velocity_dim,
                    start_index=offset,
                    end_index=offset + velocity_dim,
                    scope="agent",
                    description=f"Agent velocity ({velocity_dim}D)",
                    semantic_type="spatial",
                )
            )
            offset += velocity_dim

        # ONE FIELD PER METER, contiguous, in declaration order (PDR-0054 ruling 1).
        #
        # This was a single `obs_meters` field of width == meter count carrying ONE
        # NormalizationSpec, which is why 8 of the 9 normalization kinds were unreachable
        # for bars from any config pack (hamlet-3d3039f340): min/max were already lists so
        # per-meter PARAMETERS worked, but a block cannot carry a per-meter KIND.
        #
        # Contiguity is what keeps `group_slices["bars"]` — the name-blind replacement for
        # the old literal-name lookups — meaning "the meter block". It is asserted, not
        # assumed: see `_assert_semantic_groups_are_contiguous`.
        for meter in environment.environment.meters:
            observed_dims = meter_observed_width(meter.range_type)
            fields.append(
                ObservationField(
                    uuid=None,
                    name=meter_observation_field_name(meter.name),
                    type="vector" if observed_dims > 1 else "scalar",
                    dims=observed_dims,
                    start_index=offset,
                    end_index=offset + observed_dims,
                    scope="agent",
                    description=f"Meter '{meter.name}' observed as {meter.range_type.kind}",
                    semantic_type="bars",
                )
            )
            offset += observed_dims

        affordance_count = len(environment.environment.affordances)
        affordance_dim = affordance_count + 1
        fields.append(
            ObservationField(
                uuid=None,
                name="obs_affordance_at_position",
                type="vector",
                dims=affordance_dim,
                start_index=offset,
                end_index=offset + affordance_dim,
                scope="agent",
                description=f"{affordance_dim}-way one-hot affordance_at_position (including 'none')",
                semantic_type="affordance",
            )
        )
        offset += affordance_dim

        if compiled_effect_catalog is not None and compiled_effect_catalog.effects:
            effect_slots = EFFECT_OBSERVATION_SLOTS
            effect_dims = effect_slots * 3
            fields.append(
                ObservationField(
                    uuid=None,
                    name="obs_effects",
                    type="vector",
                    dims=effect_dims,
                    start_index=offset,
                    end_index=offset + effect_dims,
                    scope="agent",
                    description=f"Observable effects (up to {effect_slots} slots)",
                    semantic_type="effects",
                )
            )
            offset += effect_dims

        # Authored variables carry the AUTHOR'S semantic type (PDR-0047 rule 2: where an
        # author has declared, the compiler obeys — this used to hardcode "custom" and
        # ignore the declaration). `bars` is the one member an authored variable may not
        # take: it is the meter block, the runtime publishes meter columns into every
        # bars-group field, and the meter encoder is sized from the group — so the failure
        # belongs here, at compile time, not at the first observation.
        for var in environment.environment.variables:
            dims = getattr(var, "dims", 1)
            if var.semantic_type == METER_BLOCK_SEMANTIC:
                raise ValueError(
                    "An authored variable may not declare the meter block's semantic type.\n"
                    f"  Variable: {var.name}\n"
                    f"  Declared semantic_type: {var.semantic_type!r}\n"
                    f"  Rule: {METER_BLOCK_SEMANTIC!r} is the meter block — the compiler assigns it to "
                    "meter observation fields only, the runtime publishes meter state into every "
                    "field in that group, and the meter encoder is sized from it. Choose another "
                    "member of the vocabulary (townlet.vfs.semantic_type) for this variable."
                )
            fields.append(
                ObservationField(
                    uuid=None,
                    name=var.name,
                    type="vector" if dims > 1 else "scalar",
                    dims=dims,
                    start_index=offset,
                    end_index=offset + dims,
                    scope=var.scope,
                    description=var.description,
                    semantic_type=var.semantic_type,
                )
            )
            offset += dims

        # VFS PROFILE variables: one observation field per exposed global/agent variable, each
        # carrying the AUTHOR'S declared semantic type (PDR-0075). This used to be one opaque
        # `obs_vfs` block (global + agent + item, one value, `custom`) that the runtime then knew
        # by NAME — the branch PDR-0045 forbids. The item sub-block stays ONE compiler-emitted
        # feature (`obs_item_slots`): its layout is slot × profile-position, so a per-variable
        # group could reach nothing there (hamlet-1ad6383186 holds the layout question).
        max_items_per_agent = items_catalog.max_items_per_agent if items_catalog is not None else VFSObservationSpec.max_items_per_agent
        vfs_observation_spec = VFSObservationSpec.from_compiled_profiles(
            compiled_vfs_profiles,
            max_items_per_agent=max_items_per_agent,
        )
        if vfs_observation_spec is not None and vfs_observation_spec.item_vfs_dim > 0 and items_catalog is None:
            raise ValueError(
                "Observation spec includes item VFS dimensions, but items are disabled (no items catalog). "
                "Enable items or remove item VFS profiles."
            )

        taken_names: dict[str, str] = {f.name: f"compiler block ({f.semantic_type})" for f in fields}
        for var in environment.environment.variables:
            taken_names[var.name] = "environment.yaml variable"
        for scope, profile in self._exposed_profile_scopes(compiled_vfs_profiles):
            for var in profile.variables:
                if not agent_can_observe(var):
                    continue
                if var.name in taken_names:
                    raise ValueError(
                        "Observation field name collision.\n"
                        f"  Field: {var.name}\n"
                        f"  Declared by: vfs_profiles.yaml {scope}_profile variable\n"
                        f"  Already taken by: {taken_names[var.name]}\n"
                        "  Rule: every exposed profile variable compiles to its own observation field named "
                        "after the variable (PDR-0075), so the name must be unique across environment.yaml "
                        "variables, meter fields, compiler blocks, and every exposed profile variable."
                    )
                if var.semantic_type is None:
                    raise ValueError(
                        "Exposed profile variable has no declared semantic_type.\n"
                        f"  Variable: {var.name} ({scope}_profile)\n"
                        "  Rule: global and agent profile variables compile to their own observation field "
                        "and MUST declare semantic_type from townlet.vfs.semantic_type (PDR-0075)."
                    )
                if var.semantic_type == METER_BLOCK_SEMANTIC:
                    raise ValueError(
                        "A profile variable may not declare the meter block's semantic type.\n"
                        f"  Variable: {var.name} ({scope}_profile)\n"
                        f"  Declared semantic_type: {var.semantic_type!r}\n"
                        f"  Rule: {METER_BLOCK_SEMANTIC!r} is the meter block — reserved to meter observation "
                        "fields (DIV-005). Choose another member of the vocabulary (townlet.vfs.semantic_type)."
                    )
                dims = profile_variable_observation_dim(var)
                fields.append(
                    ObservationField(
                        uuid=None,
                        name=var.name,
                        type="vector" if dims > 1 else "scalar",
                        dims=dims,
                        start_index=offset,
                        end_index=offset + dims,
                        scope=cast(Literal["global", "agent"], scope),
                        description=var.description if getattr(var, "description", None) else f"VFS {scope} profile variable: {var.name}",
                        semantic_type=cast(Any, var.semantic_type),
                    )
                )
                taken_names[var.name] = f"vfs_profiles.yaml {scope}_profile variable"
                offset += dims

        item_dim = vfs_observation_spec.item_vfs_dim if vfs_observation_spec is not None else 0
        if vfs_observation_spec is not None and item_dim > 0:
            if ITEM_SLOTS_OBSERVATION_FIELD in taken_names:
                raise ValueError(
                    "Observation field name collision.\n"
                    f"  Field: {ITEM_SLOTS_OBSERVATION_FIELD}\n"
                    "  Declared by: the compiler (item-slot feature)\n"
                    f"  Already taken by: {taken_names[ITEM_SLOTS_OBSERVATION_FIELD]}\n"
                    "  Rule: the item-slot feature's name is reserved to the compiler."
                )
            fields.append(
                ObservationField(
                    uuid=None,
                    name=ITEM_SLOTS_OBSERVATION_FIELD,
                    type="vector",
                    dims=item_dim,
                    start_index=offset,
                    end_index=offset + item_dim,
                    scope="agent",
                    description=(
                        f"Item slots: exposed item-profile variables of the item in each of "
                        f"{max_items_per_agent} slots, {vfs_observation_spec.item_vars_per_slot} per slot"
                    ),
                    semantic_type="custom",
                )
            )
            offset += item_dim

        if temporal_support == "enabled":
            temporal_dims = 4
            desc = "Temporal features (sin, cos, day_progress, is_night)"
            fields.append(
                ObservationField(
                    uuid=None,
                    name="obs_temporal",
                    type="vector",
                    dims=temporal_dims,
                    start_index=offset,
                    end_index=offset + temporal_dims,
                    scope="agent",
                    description=desc,
                    semantic_type="temporal",
                    curriculum_active=active_temporal,
                )
            )
            offset += temporal_dims

        # Lay the fields out by SEMANTIC GROUP, in the fixed order the vocabulary defines. This
        # is a stable partition: within a group, emission order is kept. It is the identity on
        # every shipped pack (the compiler already emits its own blocks in this order — pinned
        # by test against default_curriculum's measured layout), and it is what lets an author
        # declare ANY member for a variable without breaking group contiguity, which
        # `_assert_semantic_groups_are_contiguous` still enforces below. The runtime assembles
        # the observation by walking these fields in order, so no runtime special case follows.
        fields.sort(key=lambda f: SEMANTIC_GROUP_ORDER.index(f.semantic_type))

        mode_cfg: ObservationModeConfig = stratum.stratum.observation_mode
        filtered_fields = self._apply_observation_mode(fields, mode_cfg)

        reindexed: list[ObservationField] = []
        offset = 0
        for field in filtered_fields:
            reindexed.append(
                ObservationField(
                    uuid=field.uuid,
                    name=field.name,
                    type=field.type,
                    dims=field.dims,
                    start_index=offset,
                    end_index=offset + field.dims,
                    scope=field.scope,
                    description=field.description,
                    semantic_type=field.semantic_type,
                    categorical_labels=field.categorical_labels,
                    curriculum_active=field.curriculum_active,
                )
            )
            offset += field.dims

        return ObservationSpec.from_fields(fields=reindexed)

    @staticmethod
    def _exposed_profile_scopes(compiled_vfs_profiles: CompiledVFSProfiles | None):
        """(scope, compiled profile) pairs for the profile scopes that compile to per-variable
        fields — global then agent, the order the old block laid them out in (PDR-0075)."""
        if compiled_vfs_profiles is None:
            return ()
        pairs = []
        if compiled_vfs_profiles.global_profile is not None:
            pairs.append(("global", compiled_vfs_profiles.global_profile))
        if compiled_vfs_profiles.agent_profile is not None:
            pairs.append(("agent", compiled_vfs_profiles.agent_profile))
        return tuple(pairs)

    def build_activity(self, obs_spec: ObservationSpec) -> ObservationActivity:
        """Build ObservationActivity grouping dims by semantic_type and honoring masking."""
        if not obs_spec.fields:
            return ObservationActivity(active_mask=(), group_slices={}, active_field_uuids=())

        active_mask_list: list[bool] = []
        active_uuids_list: list[str] = []
        group_boundaries: dict[str, int] = {}
        group_end_indices: dict[str, int] = {}
        group_dims: dict[str, int] = {}
        current_idx = 0

        for field in obs_spec.fields:
            is_masked = not field.curriculum_active
            dims = field.dims
            group_name = field.semantic_type
            if group_name not in group_boundaries:
                group_boundaries[group_name] = current_idx

            for _ in range(dims):
                active_mask_list.append(not is_masked)
                if not is_masked:
                    active_uuids_list.append(field.uuid or "")

            current_idx += dims
            group_end_indices[group_name] = current_idx
            group_dims[group_name] = group_dims.get(group_name, 0) + dims

        group_slices = {name: slice(group_boundaries[name], group_end_indices[name]) for name in group_boundaries.keys()}
        self._assert_semantic_groups_are_contiguous(group_slices, group_dims)
        return ObservationActivity(
            active_mask=tuple(active_mask_list),
            group_slices=group_slices,
            active_field_uuids=tuple(active_uuids_list),
        )

    @staticmethod
    def _assert_semantic_groups_are_contiguous(group_slices: dict[str, slice], group_dims: dict[str, int]) -> None:
        """A group's slice must contain its own fields and nothing else.

        `build_activity` records a group's start on FIRST sighting and its end on EVERY
        sighting, so a group whose fields are interleaved with another's yields a slice that
        silently SPANS the foreign dimensions. That was harmless while every group was one
        field. It stops being harmless the moment `group_slices["bars"]` becomes the
        name-blind source of the meter block — PDR-0054 W6 sizes a network layer from it, so
        a span produces a wrong tensor shape rather than a wrong answer, and the failure
        surfaces far from its cause.

        Summing each group's own dims and comparing to its span turns that into a compile
        error. `_apply_observation_mode`'s `full_manual` branch is the one path that can
        reorder fields arbitrarily, and this is what stops it reordering a group apart.
        """
        for name, span in group_slices.items():
            width = span.stop - span.start
            declared = group_dims[name]
            if width != declared:
                raise ValueError(
                    "Observation fields of one semantic group are not contiguous.\n"
                    f"  Group: {name}\n"
                    f"  Spans dims [{span.start}, {span.stop}) = {width}, but its own fields total {declared}.\n"
                    "  Rule: a semantic group must be a single contiguous run, because "
                    "observation_activity.group_slices is how consumers address a group without "
                    "knowing any field's name. Interleaving groups makes that slice span foreign "
                    "dimensions silently. If this came from observation_mode: full_manual, list a "
                    "group's fields together."
                )

    def build_vfs_observation_fields(
        self,
        obs_spec: ObservationSpec,
        environment: EnvConfigV21,
        bars: Any,
        meter_metadata: Any,
    ) -> tuple[VFSObservationField, ...]:
        """Mirror ObservationSpec fields into VFS observation fields for runtime consumption."""
        env_norm_by_name: dict[str, NormalizationSpec] = {}
        for var in environment.environment.variables:
            env_norm_by_name[var.name] = self._convert_normalization(var.name, getattr(var, "normalization", None))

        # Each meter gets its OWN spec, built from its own declared range_type. The bounds
        # half still comes from bars.yaml (PDR-0016: the declaration that ceilings the
        # runtime also scales the observation) — what changed is that the KIND now comes
        # from the author instead of being minmax for everyone.
        env_norm_by_name.update(self._meter_normalizations(environment, bars))

        fields: list[VFSObservationField] = []
        # SOURCE width, not observed width. Every meter's source is one scalar; the field's
        # `dims` may be wider (cyclical_sin_cos -> 2, one_hot -> categories). Conflating the
        # two is what made the widening kinds unusable — the runtime read the registry at
        # the OBSERVED width and tripped its own shape guard before normalization ever ran.
        source_width_by_name = {meter_observation_field_name(m.name): 1 for m in environment.environment.meters}
        for field in obs_spec.fields:
            norm = env_norm_by_name.get(field.name)
            # The mirror carries the FIELD'S value. It used to filter through a private
            # allow-list and remap anything else to "custom", so `obs_effects` was `effects`
            # on the spec and `custom` in the hash — one field, two values (DIV-005).
            fields.append(
                VFSObservationField(
                    id=field.name,
                    source_variable=field.name,
                    exposed_to=["agent"],
                    shape=[source_width_by_name.get(field.name, field.dims)],
                    normalization=norm,
                    semantic_type=field.semantic_type,
                    curriculum_active=field.curriculum_active,
                )
            )
        return tuple(fields)

    @staticmethod
    def _declared_bounds(meter_name: str, kind: str, bounds_by_name: dict[str, Any]) -> tuple[float, float]:
        """The bars.yaml bounds a range-based member scales against (PDR-0016)."""
        declared = bounds_by_name.get(meter_name)
        if declared is None:
            raise ValueError(
                "Meter declares a bounds-based observation type but has no bar to supply bounds.\n"
                f"  Meter: {meter_name}\n"
                f"  Declared range_type: {kind}\n"
                "  Rule: minmax and log_scaled take min/max from bars.yaml (PDR-0016). "
                "Declare bounds.min/bounds.max for this meter, or choose a range_type that "
                "carries its own parameters."
            )
        if declared.max <= declared.min:
            raise ValueError(
                "Meter bounds cannot be normalized: max must be strictly greater than min.\n"
                f"  Meter: {meter_name}\n"
                f"  Declared bounds: [{declared.min}, {declared.max}]"
            )
        return float(declared.min), float(declared.max)

    @staticmethod
    def _assert_one_hot_bounds_are_indexable(meter_name: str, categories: int, bounds_by_name: dict[str, Any]) -> None:
        """A one_hot meter's declared bar range must be a valid index range.

        `apply_normalization` takes `value.long()` and rejects anything outside
        `[0, categories)`. Without this, a pack declaring `categories: 5` on a bar bounded
        `[1, 1e6]` COMPILES GREEN and then dies on the first observation build with
        "one_hot normalization received category index outside configured range" — a message
        naming no meter, no value and no file. Worse, a bar that only enters the invalid
        region later fails mid-training rather than at compile time.

        The check is deliberately narrow: it rejects only ranges where an invalid index is
        REACHABLE by construction, never a range that merely looks unusual. A bar bounded
        [0, 1] with categories 5 wastes three dimensions and is left alone — wasteful is the
        author's business, unreachable-by-construction is the compiler's.
        """
        declared = bounds_by_name.get(meter_name)
        if declared is None:
            return  # a meter with no bar is caught elsewhere, with a better message
        if declared.min < 0.0 or declared.max >= float(categories):
            raise ValueError(
                "Meter declares one_hot over a bar range that is not a valid index range.\n"
                f"  Meter: {meter_name}\n"
                f"  Declared bounds: [{declared.min}, {declared.max}]\n"
                f"  Declared categories: {categories} (valid indices are 0..{categories - 1})\n"
                "  Rule: one_hot indexes into its categories, so the bar's declared range must "
                "fit inside them. Either raise `categories` above the bar's max, or lower the "
                "bar's bounds in bars.yaml."
            )

    def _meter_normalizations(self, environment: EnvConfigV21, bars: Any) -> dict[str, NormalizationSpec]:
        """One NormalizationSpec per meter, built from its declared `range_type`.

        Replaces `_meter_normalization`, which returned ONE minmax spec for the whole block
        (deleted outright, per PDR-0054's reversal trigger: growing a second path beside it
        would have meant the split was not the root fix).

        Only the two range-based members read `bars.yaml`. That asymmetry is deliberate and
        is the whole content of PDR-0016: bounds are already declared, so restating them on
        the meter would be two sources for one fact. Every other member's parameters are not
        implied by anything already written down, so the author states them inline.
        """
        bounds_by_name = {meter.name: meter.bounds for meter in bars.meters}
        specs: dict[str, NormalizationSpec] = {}

        for meter in environment.environment.meters:
            declared_type = meter.range_type
            field_name = meter_observation_field_name(meter.name)

            # isinstance dispatch, not a string switch on `.kind`: the members are distinct
            # types, so this narrows for the type checker AND makes a member added to the
            # union without a branch here fail at the `else` rather than compiling to no spec.
            if isinstance(declared_type, MeterRangeMinMax | MeterRangeLogScaled):
                bounds = self._declared_bounds(meter.name, declared_type.kind, bounds_by_name)
                specs[field_name] = NormalizationSpec(
                    kind=declared_type.kind,
                    min=bounds[0],
                    max=bounds[1],
                    clip=declared_type.clip,
                )
            elif isinstance(declared_type, MeterRangeNone):
                specs[field_name] = NormalizationSpec(kind="none")
            elif isinstance(declared_type, MeterRangeZScore):
                specs[field_name] = NormalizationSpec(kind="zscore", mean=declared_type.mean, std=declared_type.std)
            elif isinstance(declared_type, MeterRangeCyclicalSinCos):
                specs[field_name] = NormalizationSpec(kind="cyclical_sin_cos", period=declared_type.period)
            elif isinstance(declared_type, MeterRangeOneHot):
                self._assert_one_hot_bounds_are_indexable(meter.name, declared_type.categories, bounds_by_name)
                specs[field_name] = NormalizationSpec(kind="one_hot", categories=declared_type.categories)
            elif isinstance(declared_type, MeterRangeBinary):
                specs[field_name] = NormalizationSpec(kind="binary", threshold=declared_type.threshold)
            elif isinstance(declared_type, MeterRangeRankScaled):
                specs[field_name] = NormalizationSpec(kind="rank_scaled")
            elif isinstance(declared_type, MeterRangeMaskedValue):
                specs[field_name] = NormalizationSpec(
                    kind="masked_value",
                    mask_value=declared_type.mask_value,
                    fill_value=declared_type.fill_value,
                )
            else:
                # Unreachable through the DTO, which is a closed discriminated union. Present
                # so that ADDING a member without teaching this function about it fails loudly
                # here rather than silently emitting no spec — which would be PDR-0053 shape #5
                # (declaration accepted, then dropped) reintroduced by the next author.
                raise ValueError(
                    f"Meter range_type '{declared_type.kind}' has no compiled NormalizationSpec.\n"
                    f"  Meter: {meter.name}\n"
                    "  Rule: every member of the range_type vocabulary must compile to a spec here."
                )

        return specs

    @staticmethod
    def _assert_meter_ids_are_disjoint(environment: EnvConfigV21, user_var_names: set[str]) -> None:
        """A meter's observation id must collide with nothing — not a declared variable, and
        not the meter's own bar name.

        Both collisions are silent in opposite directions, which is why this is a compile
        error and not a naming convention:

        - Against `environment.variables[]`: `build_vfs_variables` SKIPS a field whose name
          matches a declared variable, so the meter would compile to an observation field
          with no backing VFS variable — accepted, then dropped (PDR-0053 shape #5).
        - Against a bar name: `vtc.py::VTCActionWriteProgram.apply` merges the registry
          snapshot and the bars dict into one namespace and raises at RUNTIME, on the first
          tick of the first pack that writes a bar. A compile error names the meter instead.

        The `obs_meter_` prefix makes both unreachable today. This asserts it rather than
        trusting it, because the prefix is one edit away from being removed by someone who
        reads it as cosmetic.
        """
        meter_names = {meter.name for meter in environment.environment.meters}
        for meter in environment.environment.meters:
            field_name = meter_observation_field_name(meter.name)
            if field_name in user_var_names:
                raise ValueError(
                    "Meter observation id collides with a declared environment variable.\n"
                    f"  Meter: {meter.name}  ->  observation id: {field_name}\n"
                    "  Rule: the meter's observation would be accepted and then silently dropped "
                    "(build_vfs_variables skips fields that shadow a declared variable). "
                    f"Rename the variable '{field_name}' in environment.yaml."
                )
            if field_name in meter_names:
                raise ValueError(
                    "Meter observation id collides with another meter's bar name.\n"
                    f"  Meter: {meter.name}  ->  observation id: {field_name}\n"
                    "  Rule: bars and VFS variables share one evaluation namespace in the VTC, "
                    "so this would raise at runtime on the first bar write."
                )

    def build_vfs_variables(
        self,
        obs_spec: ObservationSpec,
        environment: EnvConfigV21,
        compiled_vfs_profiles: CompiledVFSProfiles | None = None,
    ) -> tuple[VariableDef, ...]:
        """Build VFS variables from observation fields + environment variables.

        A field backed by a VARIABLE the registry already holds — an `environment.yaml`
        variable, or (PDR-0075) a global/agent profile variable, which `build_runtime_variables`
        adds under its own scope — gets no engine-written primitive minted here. Only compiler
        FEATURES (grid, meters, affordance, effects, temporal, `obs_item_slots`) do.
        """
        vars_out: list[VariableDef] = []
        user_var_names = {var.name for var in environment.environment.variables}
        self._assert_meter_ids_are_disjoint(environment, user_var_names)
        profile_var_names = {
            var.name for _scope, profile in self._exposed_profile_scopes(compiled_vfs_profiles) for var in profile.variables
        }

        # SOURCE widths. A meter's backing variable is always one scalar, whatever its
        # observed width — the widening kinds produce their extra dimensions at
        # normalization time, downstream of the registry. Deriving this from `field.dims`
        # (as it did) makes the variable 2-wide for a cyclical_sin_cos meter, and the
        # encoder's own shape guard then fires before `apply_normalization` ever runs.
        meter_source_widths = {meter_observation_field_name(m.name): 1 for m in environment.environment.meters}

        for field in obs_spec.fields:
            if field.name in user_var_names or field.name in profile_var_names:
                continue

            source_dims = meter_source_widths.get(field.name, field.dims)
            is_vector = source_dims > 1
            default = [0.0] * source_dims if is_vector else 0.0
            vars_out.append(
                VariableDef(
                    id=field.name,
                    scope="agent",
                    type="vecNf" if is_vector else "scalar",
                    dims=source_dims if is_vector else None,
                    lifetime="tick",
                    readable_by=["agent", "engine"],
                    writable_by=["engine"],
                    default=default,
                    description=field.description or f"System observation primitive: {field.name}",
                    normalization=None,
                )
            )

        for var in environment.environment.variables:
            raw_dims = getattr(var, "dims", None)
            shape = getattr(var, "shape", None)
            var_type = getattr(var, "type", None)

            is_tensor = var_type in {"tensor1d", "tensor2d", "tensor3d", "tensorNd"}
            is_vector = bool(raw_dims and raw_dims > 1 and not is_tensor)

            dims = raw_dims if is_vector else None
            user_var_default: list[float] | float | None = 0.0
            if is_tensor:
                user_var_default = None
            elif is_vector and raw_dims is not None:
                user_var_default = [0.0] * raw_dims

            normalization = self._convert_normalization(var.name, getattr(var, "normalization", None))

            type_literal = Literal[
                "scalar",
                "vec2i",
                "vec3i",
                "vec2f",
                "vec3f",
                "vecNi",
                "vecNf",
                "bool",
                "agent_ref",
                "item_ref",
                "tensor1d",
                "tensor2d",
                "tensor3d",
                "tensorNd",
            ]
            if var_type is None:
                final_type = cast(type_literal, "vecNf" if is_vector else "scalar")
            elif is_tensor:
                final_type = cast(type_literal, var_type)
            else:
                final_type = cast(type_literal, "vecNf" if is_vector else "scalar")

            vars_out.append(
                VariableDef(
                    id=var.name,
                    scope=var.scope,
                    type=final_type,
                    dims=dims,
                    lifetime="tick",
                    readable_by=["agent", "engine"],
                    writable_by=["engine"],
                    default=user_var_default,
                    description=var.description,
                    normalization=normalization,
                    shape=shape,
                    initial_value_mode=getattr(var, "initial_value_mode", None),
                    initial_value_params=getattr(var, "initial_value_params", None),
                )
            )
        return tuple(vars_out)

    @staticmethod
    def _apply_observation_mode(
        fields: list[ObservationField],
        mode_cfg: ObservationModeConfig,
    ) -> list[ObservationField]:
        """Filter observation fields based on observation_mode selection."""
        if mode_cfg.mode == "full_auto":
            return fields

        if mode_cfg.mode == "max_compact":
            return [f for f in fields if f.curriculum_active]

        if mode_cfg.mode == "full_manual":
            includes = mode_cfg.include_fields or []
            field_lookup = {field.name: field for field in fields}
            missing = [name for name in includes if name not in field_lookup]
            if missing:
                raise ValueError(
                    f"full_manual observation_mode requested unknown fields: {sorted(missing)}. Check names against ObservationSpec fields."
                )
            if not includes:
                raise ValueError("full_manual observation_mode produced an empty field set; include_fields must match existing fields.")
            return [field_lookup[name] for name in includes]

        raise ValueError(f"Unsupported observation_mode '{mode_cfg.mode}'.")

    @staticmethod
    def _convert_normalization(var_name: str, norm_cfg: Any) -> NormalizationSpec:
        """Map environment.yaml normalization into VFS NormalizationSpec.

        `clip` and `none` were removed from the method vocabulary
        (hamlet-1dba1910c0). Both were ambiguities of the kind PDR-0047 rule 1
        forbids, and neither is coming back in this form:

        - `clip` compiled to a byte-identical `minmax` spec — the same
          behaviour as `normalize` under a name that promised something else.
          `minmax` is `(v - min) / (max - min)`, pure rescaling with no clamp,
          so an author declaring `clip` on `[0, 1]` and feeding `7.0` got
          `7.0` back. All 25 in-tree declarations were migrated to `normalize`,
          which is behaviour-preserving precisely because the two were
          identical.
        - `none` was in the approved vocabulary and rejected unconditionally
          here — a member no author could ever select.

        Real clamping was NOT provided by removing the false promise of it, and
        it arrived separately as the owner-approved grammar extension
        `hamlet-fba56feca5`: a required `clip` PARAMETER on `normalize`, which
        composes with the range-based kinds instead of multiplying members. The
        redundant `clipped_log_scaled` kind was deleted in the same change
        (PDR-0054 ruling 3).
        """
        if norm_cfg is None:
            raise ValueError(
                "Missing normalization for variable declared in environment.yaml.\n"
                f"  Variable: {var_name}\n"
                "  Rule: every variable must declare normalization explicitly; there is no default (No-Defaults Principle).\n"
                "  Provide method: normalize (scale to [0,1] against range) | standardize (mean/std)."
            )

        method = getattr(norm_cfg, "method", None)
        range_values = getattr(norm_cfg, "range", None)
        mean = getattr(norm_cfg, "mean", None)
        std = getattr(norm_cfg, "std", None)
        clip = getattr(norm_cfg, "clip", None)

        if method is None:
            raise ValueError(
                "Normalization entry missing 'method' in environment.yaml.\n"
                f"  Variable: {var_name}\n"
                "  Provide method: normalize | standardize."
            )

        if method == "normalize":
            if not range_values or len(range_values) != 2:
                raise ValueError(
                    f"Normalization range must provide exactly two values [min, max].\n  Variable: {var_name}\n  Got: {range_values}"
                )
            return NormalizationSpec(kind="minmax", min=range_values[0], max=range_values[1], clip=clip)
        if method == "standardize":
            if mean is None or std is None:
                raise ValueError(
                    "Normalization method 'standardize' requires 'mean' and 'std' parameters in environment.yaml.\n"
                    f"  Variable: {var_name}\n"
                    "  Action: add mean/std fields to normalization, or use normalize with an explicit range."
                )
            return NormalizationSpec(kind="zscore", mean=mean, std=std)

        raise ValueError(f"Unsupported normalization method '{method}' for variable '{var_name}'. Use normalize | standardize.")
