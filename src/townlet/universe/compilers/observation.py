"""Observation-domain compiler boundary — the TokenSpec is the compiler's product.

Unit-3 Task-10 cut: the old ``ObservationSpec``/``ObservationActivity``/VFS-mirror
pipeline is DELETED (token-obs spec §2 "what dies"); this compiler now emits exactly one
observation artifact per level — the :class:`~townlet.universe.dto.token_spec.TokenSpec`
— from declarations alone. Every token-spec refusal (exposure rules, capacity, identity)
leaves this compiler as a located ``CompilationError`` carrying its error code.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import Final

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
    TokenSpecRefusalError,
    TokenSubject,
    build_token_type,
    canonical_token_bindings,
    canonical_token_contexts,
    check_indistinguishability,
    mean_census_advisory,
    require_position_rank,
    token_identities,
)
from townlet.universe.errors import CompilationError, CompilationMessage
from townlet.universe.source_map import SourceMap, variable_location_key
from townlet.universe.stages import CompilationStage
from townlet.vfs.schema import VariableDef

#: Brain architectures whose Q-network pools the token set through ``TokenSetEncoder``
#: (``population/vectorized.py`` ``is_token_native``). They see tokens as a set, so two
#: declarations with equal static identity are one token to them for every weight setting.
#: ``feedforward`` and ``dueling`` read the flat view by slot position and need no such check.
PERMUTATION_INVARIANT_ARCHITECTURES: Final[frozenset[str]] = frozenset({"token_set", "recurrent"})


def reads_tokens_as_a_set(brain: BrainConfig) -> bool:
    """Whether the level's effective brain is a permutation-invariant token encoder."""
    return brain.architecture.type in PERMUTATION_INVARIANT_ARCHITECTURES


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
        *,
        enabled_affordances: Collection[str],
        level_name: str,
        source_map: SourceMap | None,
    ) -> tuple[TokenSpec, tuple[str, ...]]:
        """Compile the TokenSpec for one level (token-obs spec §§1–2).

        Capacities follow the spec §2 table through ``token_spec.py``'s derivations:

        - ``effect``: Σ per-scope declared budget × denominator; the budget is required
          by the effects DTO whenever any effect is declared (No-Defaults).
        - ``variable_element``: Σ element counts of EXPLICITLY exposed variables —
          canonical registry and item variables with authored ``exposed_to``.
          Exposure-rule failures (unbounded kind, ``one_hot``, ``rank_scaled``, missing
          normalization) are compile refusals.
        - ``agent``: 0 — no shared-world declaration surface exists; ``num_agents`` is
          a batch of independent worlds and must never size this (plan Global
          Constraints).

        The indistinguishability check (spec §1) runs only when ``brain`` — the level's
        EFFECTIVE brain — is a permutation-invariant token encoder; a flat brain reads
        slots by position and is not refused over two identical declarations. It refuses
        only what that encoder truly cannot tell apart: affordances enter it only on an
        aspatial substrate (position lanes separate them otherwise) and only when
        deployed (``enabled_affordances``); effects only when observable.

        Every refusal is raised as a ``CompilationError`` for the LEVELS stage with its
        error code and the subject declaration's ``file:line``. Returns
        (spec, advisories); the only advisory left is the ``{type: mean}`` census
        advisory (spec §2), which stays an instrument, not a refusal.
        """
        try:
            return self._build_token_spec(
                stratum,
                meter_declarations,
                affordances,
                items_catalog,
                compiled_effect_catalog,
                compiled_vfs_profiles,
                vfs_variables,
                brain,
                enabled_affordances=enabled_affordances,
            )
        except TokenSpecRefusalError as exc:
            raise self._compilation_error(exc, level_name=level_name, source_map=source_map) from exc

    def _build_token_spec(
        self,
        stratum: StratumConfig,
        meter_declarations: tuple[MeterDeclaration, ...],
        affordances: AffordancesV2Config,
        items_catalog: ItemsCatalogConfig | None,
        compiled_effect_catalog: EffectCatalog | None,
        compiled_vfs_profiles: CompiledVFSProfiles | None,
        vfs_variables: tuple[VariableDef, ...],
        brain: BrainConfig,
        *,
        enabled_affordances: Collection[str],
    ) -> tuple[TokenSpec, tuple[str, ...]]:
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

        if reads_tokens_as_a_set(brain):
            check_indistinguishability(
                token_identities(
                    meter_declarations=meter_declarations,
                    affordances=affordances,
                    enabled_affordances=enabled_affordances,
                    position_rank=position_rank,
                    compiled_effect_catalog=compiled_effect_catalog,
                    compiled_vfs_profiles=compiled_vfs_profiles,
                    vfs_variables=vfs_variables,
                )
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
    def compile_meter_declarations(
        environment: EnvConfigV21,
        bars: BarsV2Config,
        *,
        level_name: str,
        source_map: SourceMap | None,
    ) -> tuple[MeterDeclaration, ...]:
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
        try:
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
        except TokenSpecRefusalError as exc:
            raise ObservationCompiler._compilation_error(exc, level_name=level_name, source_map=source_map) from exc

    # ------------------------------------------------------------------ diagnostics

    @staticmethod
    def _compilation_error(refusal: TokenSpecRefusalError, *, level_name: str, source_map: SourceMap | None) -> CompilationError:
        message = str(refusal)
        if refusal.related is not None:
            related_location = _locate_subject(refusal.related, level_name=level_name, source_map=source_map)
            if related_location is not None:
                message = f"{message} ({refusal.related.display} is declared at {related_location}.)"
        return CompilationError(
            CompilationStage.LEVELS.label,
            [
                CompilationMessage(
                    code=refusal.code,
                    message=message,
                    location=_locate_subject(refusal.subject, level_name=level_name, source_map=source_map),
                )
            ],
        )


def _subject_location_keys(subject: TokenSubject, *, level_name: str) -> tuple[str, ...]:
    """Source-map keys for a refusal subject, most specific first.

    Level families are keyed ``levels/<level>/<family>:<entity>``; pack families
    ``<family>:<entity>``; the family key alone is the declaration's own line.
    """
    if subject.kind == "variable":
        assert subject.name is not None
        return (variable_location_key(subject.profile, subject.name), "variables")
    if subject.kind == "affordance":
        return (
            f"levels/{level_name}/affordances:{subject.name}",
            f"affordances:{subject.name}",
            f"levels/{level_name}/affordances",
            "affordances",
        )
    if subject.kind == "effect":
        return (f"effects:{subject.name}", "effects")
    if subject.kind == "meter":
        return (
            f"levels/{level_name}/bars:{subject.name}",
            f"bars:{subject.name}",
            f"environment:{subject.name}",
            f"levels/{level_name}/bars",
        )
    if subject.kind == "effects":
        return ("effects",)
    return ("stratum",)


def _locate_subject(subject: TokenSubject, *, level_name: str, source_map: SourceMap | None) -> str | None:
    if source_map is None:
        return None
    for key in _subject_location_keys(subject, level_name=level_name):
        located = source_map.lookup(key)
        if located is not None:
            return located
    return None
