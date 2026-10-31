"""Effects-domain compiler boundary."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from pyparsing import ParseBaseException

from townlet.config.affordances_v2_config import AffordanceParamConfig
from townlet.config.effects_config import CommandConfig, EffectsConfig
from townlet.config.items_config import ItemsCatalogConfig
from townlet.effects.catalog import EffectCatalog
from townlet.effects.compiler import CommandCompileError, CommandCompiler
from townlet.effects.parser import CommandParser
from townlet.universe.compiled import CompiledVFSProfiles
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationError, CompilationMessage
from townlet.universe.source_map import SourceMap, locate
from townlet.vfs.namespace import INTERACTION_PIPELINE, CommandSymbols, ExpressionSource, ItemBinding, Namespace, ReadContext
from townlet.vfs.profiles import CompiledItemProfile
from townlet.vfs.schema import VariableDef
from townlet.world.expression.type_checker import TypeCheckError


class EffectsCompiler:
    """Compile command pipelines (effects, affordance interactions, item interactions) against the one resolver."""

    def build_symbols(
        self,
        *,
        variables: Iterable[VariableDef],
        meter_names: Iterable[str],
        compiled_vfs_profiles: CompiledVFSProfiles | None,
        expressions: Mapping[str, ExpressionSource],
        time_enabled: bool,
    ) -> CommandSymbols:
        """The namespace every command pipeline resolves against, built as the environment builds it."""
        item_profiles: Mapping[str, CompiledItemProfile] = {}
        if compiled_vfs_profiles is not None and compiled_vfs_profiles.item_profiles is not None:
            item_profiles = compiled_vfs_profiles.item_profiles
        return CommandSymbols(
            namespace=Namespace.of_registry(variables, meters=meter_names, item_profiles=item_profiles),
            expressions=expressions,
            time_enabled=time_enabled,
        )

    def compile_catalog(
        self,
        effects_config: EffectsConfig | None,
        symbols: CommandSymbols,
    ) -> EffectCatalog | None:
        """Compile Stage 1 effects DTOs."""
        if effects_config is None:
            return None

        return EffectCatalog.from_config(effects_config, symbols)

    def check_interactions(
        self,
        pipelines: Iterable[InteractionPipeline],
        symbols: CommandSymbols,
        *,
        source_map: SourceMap | None,
    ) -> None:
        """Compile every affordance and item interaction pipeline once, refusing at the command's ``file:line``.

        The environment compiles the same pipelines with the same compiler when it
        builds its engines; this pass makes a spelling, type, context or scheduling
        refusal a compile-time diagnostic instead of a construction- or step-time
        traceback. A nested command's refusal is located at the nested command.
        """
        parser = CommandParser()
        issues: list[CompilationMessage] = []
        for pipeline in pipelines:
            compiler = CommandCompiler(
                symbols.namespace, context=pipeline.context, time_enabled=symbols.time_enabled, expressions=symbols.expressions
            )
            for index, command in enumerate(pipeline.commands):
                suffix = ""
                try:
                    compiler.compile_commands(parser.parse_commands([command]))
                except CommandCompileError as exc:
                    suffix = exc.suffix
                    message = str(exc)
                except (TypeCheckError, ValueError, ParseBaseException) as exc:
                    message = str(exc)
                else:
                    continue
                issues.append(
                    CompilationMessage(
                        code=ErrorCode.EFFECT_COMPILE,
                        message=f"{pipeline.label}[{index}]{suffix}: {message}",
                        location=locate(source_map, f"{pipeline.location}[{index}]{suffix}"),
                    )
                )
        if issues:
            raise CompilationError("Interaction pipelines", issues)


@dataclass(frozen=True)
class InteractionPipeline:
    """One authored interaction pipeline: a readable label, its positional source-map key, its read context."""

    label: str
    location: str
    context: ReadContext
    commands: list[CommandConfig]


def interaction_pipelines(
    level_name: str, affordances: Sequence[AffordanceParamConfig], items: ItemsCatalogConfig | None
) -> list[InteractionPipeline]:
    """Every authored interaction pipeline of one level.

    An item interaction is bound to its item type's static profile (``item.<x>`` reads
    that profile's state only); an affordance interaction is bound to no item.
    """
    pipelines: list[InteractionPipeline] = []
    for position, affordance in enumerate(affordances):
        for stage, commands in affordance.interactions.items():
            pipelines.append(
                InteractionPipeline(
                    label=f"levels/{level_name}/affordances:{affordance.name}:{stage}",
                    location=f"levels/{level_name}/affordances:affordances[{position}].interactions.{stage}",
                    context=INTERACTION_PIPELINE,
                    commands=list(commands),
                )
            )
    if items is not None:
        for position, item in enumerate(items.item_types):
            context = INTERACTION_PIPELINE.with_item(ItemBinding.of_profile(item.vfs_profile))
            for stage in ("on_pickup", "on_use", "on_drop"):
                pipelines.append(
                    InteractionPipeline(
                        label=f"items:{item.id}:{stage}",
                        location=f"items:item_types[{position}].interactions.{stage}",
                        context=context,
                        commands=[CommandConfig.model_validate(command) for command in getattr(item.interactions, stage)],
                    )
                )
            for stage in ("local_commands", "inventory_commands"):
                for verb_position, verb in enumerate(getattr(item.interactions, stage)):
                    pipelines.append(
                        InteractionPipeline(
                            label=f"items:{item.id}:{stage}:{verb.name}",
                            location=f"items:item_types[{position}].interactions.{stage}[{verb_position}].effects",
                            context=context,
                            commands=[CommandConfig.model_validate(command) for command in verb.effects],
                        )
                    )
    return pipelines
