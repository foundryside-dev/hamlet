"""Observation-domain compiler boundary."""

from __future__ import annotations

from typing import Any, Literal, cast

import torch

from townlet.config.curriculum_config import CurriculumConfig
from townlet.config.environment_config import EnvironmentConfig as EnvConfigV21
from townlet.config.items_config import ItemsCatalogConfig
from townlet.config.stratum_config import ObservationModeConfig, StratumConfig
from townlet.effects.catalog import EffectCatalog
from townlet.substrate.factory import SubstrateFactory
from townlet.universe.compiled import CompiledVFSProfiles
from townlet.universe.dto import ObservationActivity, ObservationField, ObservationSpec
from townlet.universe.validation.limits import EFFECT_OBSERVATION_SLOTS
from townlet.vfs.observation_builder import VFSObservationSpec
from townlet.vfs.schema import NormalizationSpec, VariableDef
from townlet.vfs.schema import ObservationField as VFSObservationField


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

        meter_count = len(environment.environment.meters)
        fields.append(
            ObservationField(
                uuid=None,
                name="obs_meters",
                type="vector",
                dims=meter_count,
                start_index=offset,
                end_index=offset + meter_count,
                scope="agent",
                description=f"{meter_count} meter values (normalized)",
                semantic_type="bars",
            )
        )
        offset += meter_count

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

        for var in environment.environment.variables:
            dims = getattr(var, "dims", 1)
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
                    semantic_type="custom",
                )
            )
            offset += dims

        max_items_per_agent = items_catalog.max_items_per_agent if items_catalog is not None else VFSObservationSpec.max_items_per_agent
        vfs_observation_spec = VFSObservationSpec.from_compiled_profiles(
            compiled_vfs_profiles,
            max_items_per_agent=max_items_per_agent,
        )
        vfs_dim = vfs_observation_spec.total_vfs_dim if vfs_observation_spec is not None else 0
        if vfs_observation_spec is not None and vfs_observation_spec.item_vfs_dim > 0 and items_catalog is None:
            raise ValueError(
                "Observation spec includes item VFS dimensions, but items are disabled (no items catalog). "
                "Enable items or remove item VFS profiles."
            )

        if vfs_dim > 0:
            fields.append(
                ObservationField(
                    uuid=None,
                    name="obs_vfs",
                    type="vector",
                    dims=vfs_dim,
                    start_index=offset,
                    end_index=offset + vfs_dim,
                    scope="agent",
                    description=f"VFS observations (global + agent + item, {vfs_dim} dims)",
                    semantic_type="custom",
                )
            )
            offset += vfs_dim

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

    def build_activity(self, obs_spec: ObservationSpec) -> ObservationActivity:
        """Build ObservationActivity grouping dims by semantic_type and honoring masking."""
        if not obs_spec.fields:
            return ObservationActivity(active_mask=(), group_slices={}, active_field_uuids=())

        active_mask_list: list[bool] = []
        active_uuids_list: list[str] = []
        group_boundaries: dict[str, int] = {}
        group_end_indices: dict[str, int] = {}
        current_idx = 0

        for field in obs_spec.fields:
            is_masked = not field.curriculum_active
            dims = field.dims
            group_name = field.semantic_type or "custom"
            if group_name not in group_boundaries:
                group_boundaries[group_name] = current_idx

            for _ in range(dims):
                active_mask_list.append(not is_masked)
                if not is_masked:
                    active_uuids_list.append(field.uuid or "")

            current_idx += dims
            group_end_indices[group_name] = current_idx

        group_slices = {name: slice(group_boundaries[name], group_end_indices[name]) for name in group_boundaries.keys()}
        return ObservationActivity(
            active_mask=tuple(active_mask_list),
            group_slices=group_slices,
            active_field_uuids=tuple(active_uuids_list),
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

        # `obs_meters` is normalized against the DECLARED bar bounds (WS-1(e)/PDR-0016).
        # bounds.max is exactly the range a minmax normalizer needs, so the same
        # declaration that ceilings the runtime also scales the observation — rather
        # than a divisor invented here, which would be papering over the magnitude.
        env_norm_by_name["obs_meters"] = self._meter_normalization(bars, meter_metadata)

        fields: list[VFSObservationField] = []
        allowed_semantic = {"bars", "spatial", "affordance", "temporal", "custom"}
        for field in obs_spec.fields:
            norm = env_norm_by_name.get(field.name)
            semantic = field.semantic_type if field.semantic_type in allowed_semantic else "custom"
            fields.append(
                VFSObservationField(
                    id=field.name,
                    source_variable=field.name,
                    exposed_to=["agent"],
                    shape=[field.dims],
                    normalization=norm,
                    semantic_type=semantic,  # type: ignore[arg-type]
                    curriculum_active=field.curriculum_active,
                )
            )
        return tuple(fields)

    @staticmethod
    def _meter_normalization(bars: Any, meter_metadata: Any) -> NormalizationSpec:
        """Build the per-meter minmax spec from declared bar bounds, in observation order."""
        bounds_by_name = {meter.name: meter.bounds for meter in bars.meters}
        ordered = sorted(meter_metadata.meters, key=lambda meter: meter.index)
        mins: list[float] = []
        maxes: list[float] = []
        for meter in ordered:
            declared = bounds_by_name.get(meter.name)
            if declared is None:
                raise ValueError(
                    "Meter present in compiled metadata has no declared bar to supply bounds.\n"
                    f"  Meter: {meter.name} (index {meter.index})\n"
                    "  Rule: every observed meter must declare bounds.min/bounds.max in bars.yaml."
                )
            if declared.max <= declared.min:
                raise ValueError(
                    "Meter bounds cannot be normalized: max must be strictly greater than min.\n"
                    f"  Meter: {meter.name}\n"
                    f"  Declared bounds: [{declared.min}, {declared.max}]"
                )
            mins.append(float(declared.min))
            maxes.append(float(declared.max))
        return NormalizationSpec(kind="minmax", min=mins, max=maxes)

    def build_vfs_variables(self, obs_spec: ObservationSpec, environment: EnvConfigV21) -> tuple[VariableDef, ...]:
        """Build VFS variables from observation fields + environment variables."""
        vars_out: list[VariableDef] = []
        user_var_names = {var.name for var in environment.environment.variables}

        for field in obs_spec.fields:
            if field.name in user_var_names:
                continue

            is_vector = field.dims > 1
            default = [0.0] * field.dims if is_vector else 0.0
            vars_out.append(
                VariableDef(
                    id=field.name,
                    scope="agent",
                    type="vecNf" if is_vector else "scalar",
                    dims=field.dims if is_vector else None,
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

        Real clamping is a genuine capability and is NOT provided by removing
        the false promise of it: no plain clamp exists in the VFS kind
        vocabulary either (`clipped_log_scaled` clamps but also log-scales).
        Adding one is a grammar extension, owner-gated under PDR-0016 —
        tracked separately rather than smuggled in here.
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
            return NormalizationSpec(kind="minmax", min=range_values[0], max=range_values[1])
        if method == "standardize":
            if mean is None or std is None:
                raise ValueError(
                    "Normalization method 'standardize' requires 'mean' and 'std' parameters in environment.yaml.\n"
                    f"  Variable: {var_name}\n"
                    "  Action: add mean/std fields to normalization, or use normalize with an explicit range."
                )
            return NormalizationSpec(kind="zscore", mean=mean, std=std)

        raise ValueError(f"Unsupported normalization method '{method}' for variable '{var_name}'. Use normalize | standardize.")
