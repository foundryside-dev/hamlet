"""Command parser from config to AST."""

from __future__ import annotations

from townlet.config.effects_config import CommandConfig
from townlet.effects.collections import COLLECTION_RESOLVERS
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
            # `self` / `target` name the context's entity; anything else is an int expression
            # the compiler type-checks (an integer literal is refused there: S1).
            raw_target = config.target
            assert raw_target is not None
            resolved_target: str | None = None
            if raw_target in {"self", "target"}:
                resolved_target = raw_target

            return CommandNode(
                type=CommandType.SPAWN_EFFECT,
                effect_id=config.spawn_effect,
                target=resolved_target,
                target_expr=raw_target,
                intensity=config.intensity,
            )

        elif config.spawn_item is not None:
            return CommandNode(
                type=CommandType.SPAWN_ITEM,
                item_type=config.spawn_item,
                position=config.position,
                position_expr=config.position,
                quantity=config.quantity,
            )

        elif config.sample is not None:
            distribution = config.sample
            return CommandNode(
                type=CommandType.SAMPLE,
                sample_distribution=distribution,
                sample_params=config.params,
                sample_store_path=config.store_in,
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
            collection: str | None = None
            collection_expr: str | None = config.for_each
            if config.for_each in COLLECTION_RESOLVERS:
                collection = config.for_each
                collection_expr = None

            return CommandNode(
                type=CommandType.FOR_EACH,
                collection=collection,
                collection_expr=collection_expr,
                iterator=config.as_,
                body=[self.parse_command(cmd) for cmd in config.do],
            )

        elif config.switch is not None:
            parsed_cases: list[tuple[str, list[CommandNode]]] = []
            for case in config.cases:
                when_expr = case.get("when")
                if when_expr is None:
                    raise ValueError("Switch case 'when' expression is required")
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
