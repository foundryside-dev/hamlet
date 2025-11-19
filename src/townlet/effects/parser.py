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
            return CommandNode(
                type=CommandType.SPAWN_EFFECT,
                effect_id=config.spawn_effect,
                target_expr=config.target or "self",
                intensity=config.intensity or 1.0,
            )

        elif config.spawn_item is not None:
            return CommandNode(
                type=CommandType.SPAWN_ITEM,
                item_type=config.spawn_item,
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
            return CommandNode(
                type=CommandType.FOR_EACH,
                collection_expr=config.for_each,
                iterator_var=config.as_,
                do_commands=[self.parse_command(cmd) for cmd in config.do],
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
