"""Observation-domain compiler boundary — the TokenSpec is the compiler's product.

Unit-3 Task-10 cut: the old ``ObservationSpec``/``ObservationActivity``/VFS-mirror
pipeline is DELETED (token-obs spec §2 "what dies"); this compiler now emits exactly one
observation artifact per level — the :class:`~townlet.universe.dto.token_spec.TokenSpec`
— from declarations alone. Everything that was an advisory while the token path ran
alongside the old one (exposure rules, effect budget, indistinguishability) is now the
compile refusal the spec names.
"""

from __future__ import annotations

from typing import Any, cast

import torch

from townlet.config.bars_v2_config import BarsV2Config
from townlet.config.brain_config import BrainConfig
from townlet.config.environment_config import (
    EnvironmentConfig as EnvConfigV21,
)
from townlet.config.items_config import ItemsCatalogConfig
from townlet.config.stratum_config import StratumConfig
from townlet.effects.catalog import EffectCatalog
from townlet.substrate.factory import SubstrateFactory
from townlet.universe.compiled import CompiledVFSProfiles
from townlet.universe.dto import AffordanceMetadata
from townlet.universe.dto.token_spec import (
    EFFECT_SCOPE_VOCABULARY,
    ExposedVariable,
    SlotBinding,
    TokenSpec,
    build_token_type,
    check_indistinguishability,
    effect_capacity,
    item_capacity,
    mean_census_advisory,
    require_position_rank,
    static_payload_signature,
)
from townlet.vfs.schema import NormalizationSpec, VariableDef, VariableScope

# The custom-typed Literal cast target for environment.yaml variable types.
_VECTOR_TYPES = {"vecNi", "vecNf"}
_TENSOR_TYPES = {"tensor1d", "tensor2d", "tensor3d", "tensorNd"}


class ObservationCompiler:
    """Compile the token observation artifact for one level."""

    def build_token_spec(
        self,
        stratum: StratumConfig,
        bars: BarsV2Config,
        affordance_metadata: AffordanceMetadata,
        items_catalog: ItemsCatalogConfig | None,
        compiled_effect_catalog: EffectCatalog | None,
        max_active_effects: dict[str, int] | None,
        environment: EnvConfigV21,
        compiled_vfs_profiles: CompiledVFSProfiles | None,
        vfs_variables: tuple[VariableDef, ...],
        brain: BrainConfig,
    ) -> tuple[TokenSpec, tuple[str, ...]]:
        """Compile the TokenSpec for one level (token-obs spec §§1–2).

        Capacities follow the spec §2 table through ``token_spec.py``'s derivations:

        - ``effect``: Σ per-scope declared budget × denominator; the budget is required
          by the effects DTO whenever any effect is declared (No-Defaults) — the Task-7
          advisory is now the refusal.
        - ``variable_element``: Σ element counts of EXPLICITLY exposed variables —
          environment.yaml variables (their declaration is the exposure; normalization
          already required there) plus profile variables with authored ``exposed_to``.
          Exposure-rule failures (unbounded kind, ``one_hot``, ``rank_scaled``, missing
          normalization) and indistinguishability are compile refusals.
        - ``agent``: 0 — no shared-world declaration surface exists; ``num_agents`` is
          a batch of independent worlds and must never size this (plan Global
          Constraints).

        Returns (spec, advisories); the only advisory left is the ``{type: mean}``
        census advisory (spec §2), which stays an instrument, not a refusal.
        """
        advisories: list[str] = []

        substrate_cfg = stratum.stratum.substrate
        substrate_instance = SubstrateFactory.build(substrate_cfg, torch.device("cpu"))
        require_position_rank(substrate_instance.position_dim, substrate_type=substrate_cfg.type)

        self_type = build_token_type("self", (SlotBinding(slot_index=0, filler_kind="static", filler_ref="self"),))
        meter_type = build_token_type(
            "meter",
            tuple(SlotBinding(slot_index=i, filler_kind="static", filler_ref=meter.name) for i, meter in enumerate(bars.meters)),
        )
        # Capacity is the metadata affordance COUNT (ruling: `deployment.positions` are
        # per-instance payload inputs, not extra capacity — absent instances are padding).
        affordance_type = build_token_type(
            "affordance",
            tuple(
                SlotBinding(slot_index=i, filler_kind="static", filler_ref=affordance.id)
                for i, affordance in enumerate(affordance_metadata.affordances)
            ),
        )
        agent_type = build_token_type("agent", ())

        if items_catalog is not None:
            item_cap = item_capacity(
                max_items_in_world=items_catalog.max_items_in_world,
                max_items_per_agent=items_catalog.max_items_per_agent,
                declared_agents_per_world=None,
            )
        else:
            item_cap = 0
        item_type = build_token_type(
            "item",
            tuple(SlotBinding(slot_index=i, filler_kind="dynamic", filler_ref=f"item:{i}") for i in range(item_cap)),
        )

        declared_effects = len(compiled_effect_catalog.effects) if compiled_effect_catalog is not None else 0
        effect_cap = effect_capacity(
            max_active_effects=max_active_effects,
            declared_effect_count=declared_effects,
            declared_agents_per_world=None,
            item_capacity_value=item_cap,
            affordance_capacity_value=affordance_type.capacity,
        )
        effect_type = build_token_type(
            "effect",
            tuple(
                SlotBinding(slot_index=i, filler_kind="dynamic", filler_ref=ref)
                for i, ref in enumerate(
                    effect_slot_refs(
                        max_active_effects=max_active_effects if declared_effects else None,
                        declared_agents_per_world=None,
                        item_capacity_value=item_cap,
                        affordance_capacity_value=affordance_type.capacity,
                    )
                )
            ),
        )
        if effect_type.capacity != effect_cap:
            raise ValueError(
                f"Effect token capacity disagrees with its derivation: slot layout produced "
                f"{effect_type.capacity} slots, `effect_capacity` derived {effect_cap}. "
                "`effect_slot_refs` and `effect_capacity` must read the same declared budget and the "
                "same denominators; a divergence here is an engine bug, not an authoring error."
            )

        element_bindings = self._variable_element_bindings(environment, compiled_vfs_profiles, vfs_variables)
        variable_element_type = build_token_type("variable_element", element_bindings)

        spec = TokenSpec(
            types=(self_type, meter_type, affordance_type, agent_type, item_type, effect_type, variable_element_type),
        )

        architecture = brain.architecture
        aggregator_type: str | None = None
        if architecture.type == "set_encoder" and architecture.set_encoder is not None:
            aggregator_type = architecture.set_encoder.aggregator.type
        elif architecture.type == "token_set" and architecture.token_set is not None:
            aggregator_type = architecture.token_set.aggregator.type
        if aggregator_type is not None:
            census_note = mean_census_advisory(spec, aggregator=aggregator_type)
            if census_note is not None:
                advisories.append(census_note)

        return spec, tuple(advisories)

    @staticmethod
    def _variable_element_bindings(
        environment: EnvConfigV21,
        compiled_vfs_profiles: CompiledVFSProfiles | None,
        vfs_variables: tuple[VariableDef, ...],
    ) -> tuple[SlotBinding, ...]:
        """Slot bindings for the `variable_element` type: one slot per element of each
        EXPLICITLY exposed variable, in registry declaration order (the order
        ``build_runtime_variables`` registers them — environment.yaml declaration order,
        then each profile's compile order).

        Exposure sources (explicit-exposure cut, spec §2):

        - every ``environment.yaml`` variable — its declaration in the observation
          config file IS the exposure, and its normalization is already required there;
        - a global/agent profile variable with authored non-empty ``exposed_to``
          (normalization required by the DTO at exposure);
        - an ``exposed_to``-declaring item-profile variable REFUSES with the landing
          named: the item-arena slot-binding emission lands with the unit-5 pack
          migration (the runtime publisher exists — Task 8 — but no compile surface
          drives it yet, and no shipped pack declares one).

        Exposure-rule failures are compile refusals (ValueError from token_spec.py's
        derivations, actionable messages carried verbatim); the compile-time
        indistinguishability check refuses over the bound set (spec §1).
        """
        env_semantic: dict[str, str] = {}
        for var in environment.environment.variables:
            env_semantic[var.name] = str(var.semantic_type)

        exposed_profile: dict[str, str] = {}
        if compiled_vfs_profiles is not None:
            for profile in (compiled_vfs_profiles.global_profile, compiled_vfs_profiles.agent_profile):
                if profile is None:
                    continue
                for compiled_var in profile.variables:
                    if compiled_var.exposed_to:
                        exposed_profile[str(compiled_var.name)] = str(compiled_var.semantic_type)
            for item_profile in (compiled_vfs_profiles.item_profiles or {}).values():
                for compiled_var in item_profile.variables:
                    if compiled_var.exposed_to:
                        raise ValueError(
                            f"Item-profile variable '{item_profile.profile_name}.{compiled_var.name}' declares "
                            f"exposed_to={list(compiled_var.exposed_to)}, but item-profile exposure has no compiled "
                            "slot-binding surface yet.\n"
                            "  Landing (token-obs spec §2 scope table): `variable_element` via the item-arena "
                            "publisher with an owner/slot coordinate — the runtime publisher exists "
                            "(environment/token_publishers.py, unit-3 Task 8); the compile emission lands with the "
                            "unit-5 pack migration, which authors the first exposed item variable. Until then, "
                            "remove the exposure."
                        )

        bindings: list[SlotBinding] = []
        bound: list[ExposedVariable] = []
        for var_def in vfs_variables:
            var_id = var_def.id
            if var_id in env_semantic:
                semantic_type = env_semantic[var_id]
            elif var_id in exposed_profile:
                semantic_type = exposed_profile[var_id]
            elif var_def.exposed_to:
                # A variables_reference.yaml overlay static declaring exposed_to directly
                # on the VariableDef: no semantic_type surface exists there yet.
                raise ValueError(
                    f"Variable '{var_id}' (variables_reference.yaml overlay) declares exposed_to, but overlay "
                    "statics have no semantic_type surface and cannot bind variable_element slots yet. "
                    "Declare the variable in vfs_profiles.yaml to expose it."
                )
            else:
                continue

            scope = var_def.scope.value if isinstance(var_def.scope, VariableScope) else str(var_def.scope)
            if var_def.shape:
                shape = tuple(var_def.shape)
            elif var_def.dims is not None and var_def.dims > 1:
                shape = (int(var_def.dims),)
            else:
                shape = ()
            exposed = ExposedVariable(
                id=var_id,
                scope=scope,
                semantic_type=semantic_type,
                type=var_def.type,
                lifetime=var_def.lifetime,
                default=var_def.default,
                shape=shape,
                normalization=var_def.normalization,
            )
            signature = static_payload_signature(exposed)
            bound.append(exposed)
            # static_payload_signature returns (scope, shape, per-element descriptor blocks).
            descriptor_blocks = cast("tuple[tuple[float, ...], ...]", signature[2])
            for element_index, descriptor_block in enumerate(descriptor_blocks):
                filler_ref = exposed.id if exposed.element_count == 1 else f"{exposed.id}[{element_index}]"
                bindings.append(
                    SlotBinding(
                        slot_index=len(bindings),
                        filler_kind="static",
                        filler_ref=filler_ref,
                        static_signature=tuple(descriptor_block),
                    )
                )

        check_indistinguishability(bound)
        return tuple(bindings)

    def build_vfs_variables(
        self,
        environment: EnvConfigV21,
    ) -> tuple[VariableDef, ...]:
        """Build registry VariableDefs from environment.yaml authored variables.

        The engine-minted ``obs_*`` observation primitives that used to be emitted here
        died with the old observation path (unit-3 Task-10 cut): token publishers read
        engine state (positions, meters, affordance layout, effects) directly each tick;
        the registry holds authored state only, plus the engine ``tick``
        (``build_runtime_variables``).
        """
        vars_out: list[VariableDef] = []
        for var in environment.environment.variables:
            raw_dims = getattr(var, "dims", None)
            shape = getattr(var, "shape", None)
            var_type = getattr(var, "type", None)

            is_tensor = var_type in _TENSOR_TYPES
            is_vector = bool(raw_dims and raw_dims > 1 and not is_tensor)

            dims = raw_dims if is_vector else None
            user_var_default: list[float] | float | None = 0.0
            if is_tensor:
                user_var_default = None
            elif is_vector and raw_dims is not None:
                user_var_default = [0.0] * raw_dims

            normalization = self._convert_normalization(var.name, getattr(var, "normalization", None))

            if var_type is None:
                final_type = "vecNf" if is_vector else "scalar"
            elif is_tensor:
                final_type = str(var_type)
            else:
                final_type = "vecNf" if is_vector else "scalar"

            vars_out.append(
                VariableDef(
                    id=var.name,
                    scope=var.scope,
                    type=final_type,  # type: ignore[arg-type]
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
    def _convert_normalization(var_name: str, norm_cfg: Any) -> NormalizationSpec:
        """Map environment.yaml normalization into VFS NormalizationSpec.

        `clip` and `none` were removed from the method vocabulary
        (hamlet-1dba1910c0); real clamping arrived as the required `clip` PARAMETER on
        `normalize` (hamlet-fba56feca5). Post-cut, environment.yaml variables are always
        exposed, so the boundedness-at-exposure rule (token-obs spec §1) additionally
        requires `clip: true` on `normalize` — enforced downstream by
        `require_exposure_normalization`, which names the rule.
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


def effect_slot_refs(
    *,
    max_active_effects: dict[str, int] | None,
    declared_agents_per_world: int | None,
    item_capacity_value: int,
    affordance_capacity_value: int,
) -> tuple[str, ...]:
    """The effect token slot layout: scope-blocked, in EffectScope vocabulary order.

    One block per scope, sized budget × denominator, refs ``effect:{scope}:{i}`` with
    ``i`` dense within the scope block. This convention is shared with the runtime
    wiring (the environment maps live effect instances into their scope's block), and
    is part of the layout hash through the filler refs.
    """
    if max_active_effects is None:
        return ()
    denominators = {
        "global": 1,
        "agent": declared_agents_per_world if declared_agents_per_world is not None else 1,
        "item": item_capacity_value,
        "affordance": affordance_capacity_value,
    }
    refs: list[str] = []
    for scope in EFFECT_SCOPE_VOCABULARY:
        block = max_active_effects.get(scope, 0) * denominators[scope]
        refs.extend(f"effect:{scope}:{i}" for i in range(block))
    return tuple(refs)
