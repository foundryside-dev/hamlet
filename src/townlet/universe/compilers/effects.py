"""Effects-domain compiler boundary."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from pyparsing import ParseBaseException

from townlet.config.effects_config import CommandConfig, EffectsConfig
from townlet.config.items_config import ItemsCatalogConfig
from townlet.effects.catalog import EffectCatalog
from townlet.effects.compiler import CommandCompiler
from townlet.effects.parser import CommandParser
from townlet.universe.compiled import CompiledVFSProfiles
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationError, CompilationMessage
from townlet.universe.source_map import SourceMap, locate
from townlet.vfs.namespace import INTERACTION_PIPELINE, CommandSymbols, ExpressionSource, Namespace, ReadContext
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
    ) -> CommandSymbols:
        """The namespace every command pipeline resolves against, built as the environment builds it."""
        item_profiles: Mapping[str, CompiledItemProfile] = {}
        if compiled_vfs_profiles is not None and compiled_vfs_profiles.item_profiles is not None:
            item_profiles = compiled_vfs_profiles.item_profiles
        return CommandSymbols(
            namespace=Namespace.of_registry(variables, meters=meter_names, item_profiles=item_profiles),
            expressions=expressions,
        )

    def compile_catalog(
        self,
        effects_config: EffectsConfig | None,
        symbols: CommandSymbols,
        *,
        time_enabled: bool,
    ) -> EffectCatalog | None:
        """Compile Stage 1 effects DTOs."""
        if effects_config is None:
            return None

        return EffectCatalog.from_config(effects_config, symbols, time_enabled=time_enabled)

    def check_interactions(
        self,
        pipelines: Iterable[tuple[str, ReadContext, list[CommandConfig]]],
        symbols: CommandSymbols,
        *,
        source_map: SourceMap | None,
    ) -> None:
        """Compile every affordance and item interaction pipeline once, refusing at the command's ``file:line``.

        The environment compiles the same pipelines with the same compiler when it
        builds its engines; this pass makes a spelling, type or context refusal a
        compile-time diagnostic instead of a construction-time traceback.
        """
        parser = CommandParser()
        issues: list[CompilationMessage] = []
        for origin, context, commands in pipelines:
            compiler = CommandCompiler(symbols.namespace, context=context, time_enabled=True, expressions=symbols.expressions)
            for index, command in enumerate(commands):
                command_origin = f"{origin}[{index}]"
                try:
                    compiler.compile_commands(parser.parse_commands([command]))
                except (TypeCheckError, ValueError, ParseBaseException) as exc:
                    issues.append(
                        CompilationMessage(
                            code=ErrorCode.EFFECT_COMPILE,
                            message=f"{command_origin}: {exc}",
                            location=locate(source_map, command_origin),
                        )
                    )
        if issues:
            raise CompilationError("Interaction pipelines", issues)


def interaction_pipelines(
    affordances: Iterable[tuple[str, Mapping[str, list[CommandConfig]]]],
    items: ItemsCatalogConfig | None,
) -> list[tuple[str, ReadContext, list[CommandConfig]]]:
    """Every authored interaction pipeline with its source-map origin and read context.

    ``affordances`` is ``(origin prefix, {stage: commands})`` per affordance. An item
    interaction is bound to its item (``item.<x>``); an affordance interaction is not.
    """
    pipelines: list[tuple[str, ReadContext, list[CommandConfig]]] = []
    for prefix, stages in affordances:
        for stage, commands in stages.items():
            pipelines.append((f"{prefix}:{stage}", INTERACTION_PIPELINE, list(commands)))
    if items is not None:
        item_context = INTERACTION_PIPELINE.with_item(True)
        for item in items.item_types:
            for stage in ("on_pickup", "on_use", "on_drop"):
                commands = [CommandConfig.model_validate(command) for command in getattr(item.interactions, stage)]
                pipelines.append((f"items:{item.id}:{stage}", item_context, commands))
            for stage in ("local_commands", "inventory_commands"):
                for verb in getattr(item.interactions, stage):
                    commands = [CommandConfig.model_validate(command) for command in verb.effects]
                    pipelines.append((f"items:{item.id}:{stage}:{verb.name}", item_context, commands))
    return pipelines
