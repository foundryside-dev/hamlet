"""Command parser from config to AST."""

from __future__ import annotations

from townlet.config.effects_config import CommandConfig
from townlet.effects.schema import CommandNode, CommandType

__all__ = ["CommandParser"]


class CommandParser:
    """Parse effect commands from config DTOs to CommandNode AST."""

    def parse_command(self, config: CommandConfig) -> CommandNode:
        """Parse single command config to AST node.

        Args:
            config: Command configuration DTO

        Returns:
            Compiled CommandNode AST
        """
        # Determine command type
        if config.modify is not None:
            return CommandNode(
                type=CommandType.MODIFY,
                path=config.modify,
                value_expr=config.value,
            )

        elif config.spawn_effect is not None:
            # Normalize target: keep simple values on `target` for executor, preserve expr string
            raw_target = config.target if config.target is not None else "self"
            resolved_target: str | int | None
            if isinstance(raw_target, str):
                if raw_target in {"self", "target"}:
                    resolved_target = raw_target
                else:
                    try:
                        # Allow numeric strings (including negatives) to be treated as explicit indices
                        resolved_target = int(raw_target)
                    except ValueError:
                        resolved_target = None  # Expression resolved at runtime
            else:
                resolved_target = raw_target

            return CommandNode(
                type=CommandType.SPAWN_EFFECT,
                effect_id=config.spawn_effect,
                target=resolved_target,
                target_expr=str(raw_target) if raw_target is not None else None,
                intensity=config.intensity or 1.0,
            )

        elif config.spawn_item is not None:
            return CommandNode(
                type=CommandType.SPAWN_ITEM,
                item_type=config.spawn_item,
                position=config.position,
                position_expr=config.position,
            )

        elif config.if_condition is not None:
            return CommandNode(
                type=CommandType.IF,
                condition_expr=config.if_condition,
                then_commands=[self.parse_command(cmd) for cmd in config.then],
                else_commands=[self.parse_command(cmd) for cmd in config.else_],
            )

        elif config.for_each is not None:
            # for_each can be a registered collection name OR an arbitrary expression.
            # Only set collection when it matches a known resolver; otherwise treat as expression.
            collection = None
            collection_expr = config.for_each
            if isinstance(config.for_each, str):
                try:
                    from townlet.effects import collections as _collections

                    collection_resolvers = _collections.COLLECTION_RESOLVERS
                except Exception:
                    collection_resolvers = {}
                if config.for_each in collection_resolvers:
                    collection = config.for_each
                    collection_expr = None

            return CommandNode(
                type=CommandType.FOR_EACH,
                collection=collection,
                collection_expr=collection_expr,
                iterator=config.as_,
                iterator_var=config.as_,
                body=[self.parse_command(cmd) for cmd in config.do],
                do_commands=[self.parse_command(cmd) for cmd in config.do],
            )

        elif config.switch is not None:
            parsed_cases: list[tuple[str, list[CommandNode]]] = []
            for case in config.cases:
                when_expr = case.get("when")
                do_cmds = case.get("do") or []
                parsed_cases.append((when_expr, [self.parse_command(cmd) for cmd in do_cmds]))

            default_cmds = [self.parse_command(cmd) for cmd in config.default]

            return CommandNode(
                type=CommandType.SWITCH,
                switch_expr=config.switch,
                cases=parsed_cases,
                default_commands=default_cmds,
            )

        elif config.reduce is not None:
            return CommandNode(
                type=CommandType.REDUCE,
                reduce_expr=config.reduce,
                reduce_iterator=config.reduce_as,
                reduce_init_expr=config.reduce_init,
                reduce_body_expr=config.reduce_body,
                reduce_target=config.reduce_into,
            )

        elif config.parallel is not None:
            return CommandNode(
                type=CommandType.PARALLEL,
                parallel_commands=[self.parse_command(cmd) for cmd in config.parallel],
            )

        elif config.delay is not None:
            return CommandNode(
                type=CommandType.DELAY,
                delay_ticks_expr=config.delay,
                delay_commands=[self.parse_command(cmd) for cmd in config.delay_do],
            )

        else:
            raise ValueError("Invalid command config: no command type set")

    def parse_commands(self, configs: list[CommandConfig]) -> list[CommandNode]:
        """Parse list of command configs.

        Args:
            configs: List of command configurations

        Returns:
            List of CommandNode AST nodes
        """
        return [self.parse_command(config) for config in configs]
