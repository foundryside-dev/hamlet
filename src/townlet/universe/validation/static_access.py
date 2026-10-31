"""Source-aware authorization of statically known authored write targets."""

from collections.abc import Iterable

from pyparsing import ParseBaseException

from townlet.config.effects_config import CommandConfig, EffectScope
from townlet.config.variables_config import VariableDeclaration
from townlet.effects.compiler import spawn_target_literal_refusal, spawn_target_reads_nothing
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationErrorCollector
from townlet.universe.raw_configs_v21 import RawConfigsV21
from townlet.universe.source_map import SourceMap, locate, variable_location_key
from townlet.vfs.schema import VariableScope
from townlet.world.expression import ExpressionParser, PathAccess


def validate_static_write_targets(raw: RawConfigsV21, source_map: SourceMap | None) -> None:
    """Refuse known denied writes independent of runtime branch selection.

    Three refusals, all citing the authored write site: a target that denies the
    engine write, a target that carries an ``expression``, and a ``spawn_effect`` target
    that is a constant row (another world's entity in every world but one, S1). Profile evaluation
    recomputes an expression variable after every authored write, so a write to one
    would be silently discarded; the second refusal also names the declaration.

    Item-hook self targets have a known qualified profile. Item-effect targets
    and reference traversal are resolved and authorized by the runtime because
    their destination is selected dynamically.
    """
    errors = CompilationErrorCollector(stage="Static write authorization")
    registry = {v.id: v for v in raw.variables.declarations if v.scope != VariableScope.ITEM}
    items = {(v.profile, v.id): v for v in raw.variables.declarations if v.scope == VariableScope.ITEM}
    parser = ExpressionParser()

    def identity(variable: VariableDeclaration) -> str:
        return f"{variable.profile}:{variable.id}" if variable.profile is not None else variable.id

    def check(variable: VariableDeclaration | None, origin: str) -> None:
        if variable is not None and "engine" not in variable.writable_by:
            errors.add(
                f"Variable '{identity(variable)}' denies engine write required by {origin}",
                code=ErrorCode.UAC_STATIC_WRITE,
                location=locate(source_map, origin),
            )

    def check_authored(variable: VariableDeclaration | None, origin: str) -> None:
        """An authored write (action, transition rule, command pipeline): authorized, and not expression-owned."""
        check(variable, origin)
        if variable is not None and variable.expression is not None:
            declared_at = locate(source_map, variable_location_key(variable.profile, variable.id))
            errors.add(
                f"{origin} writes variable '{identity(variable)}', which is computed by its expression "
                f"'{variable.expression}' (declared at {declared_at}). Profile evaluation recomputes it after every "
                f"write, so this write would be silently discarded. Write one of the expression's inputs, or declare "
                f"the variable without an expression.",
                code=ErrorCode.UAC_STATIC_WRITE,
                location=locate(source_map, origin),
            )

    def check_path(path: str, origin: str, item_profile: str | None, self_is_item: bool, target_is_item: bool) -> None:
        ast = parser.parse(path)
        if not isinstance(ast, PathAccess):
            return
        segments = ast.segments
        if segments[0] in {"self", "target", "global"}:
            prefix, segments = segments[0], segments[1:]
        else:
            prefix = ""
        if len(segments) < 2 or segments[0] != "vfs":
            return
        identifier = ".".join(segments[1:])
        if prefix == "self" and item_profile is not None:
            check_authored(items.get((item_profile, identifier)), origin)
        elif (self_is_item and prefix == "self") or (target_is_item and prefix == "target"):
            return  # The effect's item instance/profile is selected dynamically.
        else:
            check_authored(registry.get(identifier), origin)

    def commands(nodes: Iterable[CommandConfig], origin: str, item_profile: str | None, self_is_item: bool, target_is_item: bool) -> None:
        for index, node in enumerate(nodes):
            command_origin = f"{origin}[{index}]"
            if node.spawn_effect is not None and node.target is not None:
                # The entity a spawn attaches to is the write's destination: a constant row
                # is another world's entity in every world but one (S1).
                try:
                    constant = spawn_target_reads_nothing(node.target)
                except ParseBaseException as exc:
                    errors.add(
                        f"{command_origin}: spawn_effect target '{node.target}' does not parse: {exc}",
                        code=ErrorCode.EFFECT_SPAWN_TARGET,
                        location=locate(source_map, command_origin),
                    )
                    constant = False
                if constant:
                    errors.add(
                        f"{command_origin}: {spawn_target_literal_refusal(node.target)}",
                        code=ErrorCode.EFFECT_SPAWN_TARGET,
                        location=locate(source_map, command_origin),
                    )
            for path in (node.modify, node.store_in, node.reduce_into):
                if path is not None:
                    check_path(path, command_origin, item_profile, self_is_item, target_is_item)
            for field in ("then", "else_", "default", "parallel"):
                children = getattr(node, field)
                if children:
                    commands(children, f"{command_origin}.{field}", item_profile, self_is_item, target_is_item)
            if node.for_each is not None:
                # The executor changes only target_is_item when entering a loop.
                # inventory_items resolves instance/profile at runtime; all other
                # existing collection paths yield ordinary agent targets.
                commands(node.do, f"{command_origin}.do", item_profile, self_is_item, node.for_each == "inventory_items")
            if node.delay is not None:
                commands(node.delay_do, f"{command_origin}.delay_do", item_profile, self_is_item, target_is_item)
            for case_index, case in enumerate(node.cases):
                if "do" not in case:
                    continue
                children = [CommandConfig.model_validate(command) for command in case["do"]]
                commands(children, f"{command_origin}.cases[{case_index}].do", item_profile, self_is_item, target_is_item)

    for variable in raw.variables.declarations:
        if variable.expression is not None:
            check(variable, f"{variable_location_key(variable.profile, variable.id)}:expression")
    for action in raw.actions.actions.custom_actions:
        for write_index, write in enumerate(action.writes):
            check_authored(registry.get(write.variable_id), f"actions:{action.name}:writes[{write_index}]")
    for rule in raw.social_residue_rules:
        # These are lowered typed declarations, with explicit nulls removed by
        # RawConfigsV21. Validate the required projection instead of reparsing
        # it as an author DTO or inventing missing behavioral fields.
        writes = rule["writes"]
        if not isinstance(writes, tuple | list):
            raise TypeError("Lowered social rule requires a write sequence")
        for write_index, social_write in enumerate(writes):
            if not isinstance(social_write, dict) or not isinstance(social_write["variable_id"], str):
                raise TypeError("Lowered social write requires an explicit variable_id string")
            check_authored(registry.get(social_write["variable_id"]), f"transition_rules:{rule['id']}:writes[{write_index}]")
    for level in raw.levels.values():
        for affordance in level.affordances.affordances:
            for stage, pipeline in affordance.interactions.items():
                commands(pipeline, f"levels/{level.name}/affordances:{affordance.name}:{stage}", None, False, False)
    if raw.effects is not None:
        for effect in raw.effects.effect_definitions:
            for stage in ("on_spawn", "on_tick", "on_despawn", "on_interrupt"):
                commands(
                    getattr(effect, stage),
                    f"effects:{effect.id}:{stage}",
                    None,
                    effect.scope == EffectScope.ITEM,
                    effect.scope == EffectScope.ITEM,
                )
    if raw.items is not None:
        for item in raw.items.item_types:
            for stage in ("on_pickup", "on_use", "on_drop"):
                nodes = [CommandConfig.model_validate(command) for command in getattr(item.interactions, stage)]
                commands(nodes, f"items:{item.id}:{stage}", item.vfs_profile, True, False)
            for stage in ("local_commands", "inventory_commands"):
                for verb in getattr(item.interactions, stage):
                    nodes = [CommandConfig.model_validate(command) for command in verb.effects]
                    commands(nodes, f"items:{item.id}:{stage}:{verb.name}", item.vfs_profile, True, False)
    errors.check_and_raise()
