"""Observation-domain compiler boundary — the TokenSpec is the compiler's product.

Unit-3 Task-10 cut: the old ``ObservationSpec``/``ObservationActivity``/VFS-mirror
pipeline is DELETED (token-obs spec §2 "what dies"); this compiler now emits exactly one
observation artifact per level — the :class:`~townlet.universe.dto.token_spec.TokenSpec`
— from declarations alone. Everything that was an advisory while the token path ran
alongside the old one (exposure rules, effect budget, indistinguishability) is now the
compile refusal the spec names.
"""

from __future__ import annotations

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
    TOKEN_TRANSPORT_VERSION,
    MeterDeclaration,
    TokenSpec,
    build_token_type,
    canonical_token_bindings,
    canonical_token_contexts,
    mean_census_advisory,
    require_position_rank,
)
from townlet.vfs.schema import VariableDef


class ObservationCompiler:
    """Compile the token observation artifact for one level."""

    def build_token_spec(
        self,
        stratum: StratumConfig,
        meter_declarations: tuple[MeterDeclaration, ...],
        affordances: AffordancesV2Config,
        items_catalog: ItemsCatalogConfig | None,
        compiled_effect_catalog: EffectCatalog | None,
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
          canonical registry and item variables with authored ``exposed_to``.
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
        position_rank = require_position_rank(substrate_instance.position_dim, substrate_type=substrate_cfg.type)

        bindings = canonical_token_bindings(
            meter_declarations=meter_declarations,
            affordances=affordances,
            items_catalog=items_catalog,
            compiled_effect_catalog=compiled_effect_catalog,
            compiled_vfs_profiles=compiled_vfs_profiles,
            vfs_variables=vfs_variables,
        )
        contexts = {
            type_name: (slot_context_payloads, effect_catalog_contexts)
            for type_name, slot_context_payloads, effect_catalog_contexts in canonical_token_contexts(
                position_rank=position_rank,
                meter_declarations=meter_declarations,
                affordances=affordances,
                items_catalog=items_catalog,
                compiled_effect_catalog=compiled_effect_catalog,
                compiled_vfs_profiles=compiled_vfs_profiles,
                vfs_variables=vfs_variables,
            )
        }
        spec = TokenSpec(
            types=tuple(
                build_token_type(
                    type_name,
                    type_bindings,
                    slot_context_payloads=contexts[type_name][0],
                    effect_catalog_contexts=contexts[type_name][1],
                )
                for type_name, type_bindings in bindings
            ),
            position_rank=position_rank,
            transport_version=TOKEN_TRANSPORT_VERSION,
        )

        architecture = brain.architecture
        aggregator_type: str | None = None
        if architecture.type == "token_set" and architecture.token_set is not None:
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
            raise ValueError("The environment declaration contains duplicate meter names; meter token identity must be unique")
        bar_names = {meter.name for meter in bars.meters}
        if set(by_name) != bar_names:
            raise ValueError(
                "Meter vocabulary mismatch between environment and bars declarations while compiling token declarations: "
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
