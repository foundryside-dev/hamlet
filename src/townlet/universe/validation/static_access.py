"""Source-aware authorization of statically known authored write targets."""

from collections.abc import Iterable

from townlet.config.effects_config import CommandConfig, EffectScope
from townlet.config.variables_config import VariableDeclaration
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationErrorCollector
from townlet.universe.raw_configs_v21 import RawConfigsV21
from townlet.universe.source_map import SourceMap, locate, variable_location_key
from townlet.vfs.schema import VariableScope
from townlet.world.expression import ExpressionParser, PathAccess


def validate_static_write_targets(raw: RawConfigsV21, source_map: SourceMap | None) -> None:
    """Refuse known denied writes independent of runtime branch selection.

    Item-hook self targets have a known qualified profile. Item-effect targets
    and reference traversal are resolved and authorized by the runtime because
    their destination is selected dynamically.
    """
    errors = CompilationErrorCollector(stage="Static write authorization")
    registry = {v.id: v for v in raw.variables.declarations if v.scope != VariableScope.ITEM}
    items = {(v.profile, v.id): v for v in raw.variables.declarations if v.scope == VariableScope.ITEM}
    parser = ExpressionParser()

    def check(variable: VariableDeclaration | None, origin: str) -> None:
        if variable is not None and "engine" not in variable.writable_by:
            if variable.profile is not None:
                identity = f"{variable.profile}:{variable.id}"
            else:
                identity = variable.id
            errors.add(
                f"Variable '{identity}' denies engine write required by {origin}",
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
            check(items.get((item_profile, identifier)), origin)
        elif (self_is_item and prefix == "self") or (target_is_item and prefix == "target"):
            return  # The effect's item instance/profile is selected dynamically.
        else:
            check(registry.get(identifier), origin)

    def commands(nodes: Iterable[CommandConfig], origin: str, item_profile: str | None, self_is_item: bool, target_is_item: bool) -> None:
        for index, node in enumerate(nodes):
            command_origin = f"{origin}[{index}]"
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
        for write in action.writes:
            check(registry.get(write.variable_id), f"actions:{action.name}:writes")
    for rule in raw.social_residue_rules:
        # These are lowered typed declarations, with explicit nulls removed by
        # RawConfigsV21. Validate the required projection instead of reparsing
        # it as an author DTO or inventing missing behavioral fields.
        writes = rule["writes"]
        if not isinstance(writes, tuple | list):
            raise TypeError("Lowered social rule requires a write sequence")
        for social_write in writes:
            if not isinstance(social_write, dict) or not isinstance(social_write["variable_id"], str):
                raise TypeError("Lowered social write requires an explicit variable_id string")
            check(registry.get(social_write["variable_id"]), f"transition_rules:{rule['id']}:writes")
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
