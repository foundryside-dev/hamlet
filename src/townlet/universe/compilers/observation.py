"""Observation-domain compiler boundary — the TokenSpec is the compiler's product.

Unit-3 Task-10 cut: the old ``ObservationSpec``/``ObservationActivity``/VFS-mirror
pipeline is DELETED (token-obs spec §2 "what dies"); this compiler now emits exactly one
observation artifact per level — the :class:`~townlet.universe.dto.token_spec.TokenSpec`
— from declarations alone. Everything that was an advisory while the token path ran
alongside the old one (exposure rules, effect budget, indistinguishability) is now the
compile refusal the spec names.
"""

from __future__ import annotations

from typing import Any

import torch

from townlet.config.affordances_v2_config import AffordancesV2Config
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
from townlet.universe.dto.token_spec import (
    MeterDeclaration,
    TokenSpec,
    build_token_type,
    canonical_token_bindings,
    mean_census_advisory,
    require_position_rank,
)
from townlet.vfs.schema import NormalizationSpec, VariableDef

# The custom-typed Literal cast target for environment.yaml variable types.
_VECTOR_TYPES = {"vecNi", "vecNf"}
_TENSOR_TYPES = {"tensor1d", "tensor2d", "tensor3d", "tensorNd"}


class ObservationCompiler:
    """Compile the token observation artifact for one level."""

    def build_token_spec(
        self,
        stratum: StratumConfig,
        meter_declarations: tuple[MeterDeclaration, ...],
        affordances: AffordancesV2Config,
        items_catalog: ItemsCatalogConfig | None,
        compiled_effect_catalog: EffectCatalog | None,
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

        bindings = canonical_token_bindings(
            meter_declarations=meter_declarations,
            affordances=affordances,
            items_catalog=items_catalog,
            compiled_effect_catalog=compiled_effect_catalog,
            environment=environment,
            compiled_vfs_profiles=compiled_vfs_profiles,
            vfs_variables=vfs_variables,
        )
        spec = TokenSpec(types=tuple(build_token_type(type_name, type_bindings) for type_name, type_bindings in bindings))

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
    def compile_meter_declarations(environment: EnvConfigV21, bars: BarsV2Config) -> tuple[MeterDeclaration, ...]:
        """Compile meter token identity from the two declarations that own it."""
        environment_meters = environment.environment.meters
        by_name = {meter.name: meter for meter in environment_meters}
        if len(by_name) != len(environment_meters):
            raise ValueError("environment.yaml declares duplicate meter names; meter token identity must be unique")
        bar_names = {meter.name for meter in bars.meters}
        if set(by_name) != bar_names:
            raise ValueError(
                "Meter vocabulary mismatch between environment.yaml and bars.yaml while compiling token declarations: "
                f"environment-only={sorted(set(by_name) - bar_names)}, bars-only={sorted(bar_names - set(by_name))}"
            )
        return tuple(
            MeterDeclaration(
                name=meter.name,
                normalization=by_name[meter.name].token_normalization(
                    minimum=meter.bounds.min,
                    maximum=meter.bounds.max,
                ),
                initial=meter.initial,
                min=meter.bounds.min,
                max=meter.bounds.max,
                lethal_min=meter.bounds.lethal_min,
                lethal_max=meter.bounds.lethal_max,
                passive_depletion=meter.depletion.passive,
                move_depletion=meter.depletion.move,
                interact_depletion=meter.depletion.interact,
                natural_recovery=meter.recovery.natural,
            )
            for meter in bars.meters
        )

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
