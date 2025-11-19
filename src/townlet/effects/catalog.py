"""Effects catalog compilation and loading."""

from __future__ import annotations

from dataclasses import dataclass

from townlet.config.effects_config import EffectsConfig
from townlet.effects.compiler import CommandCompiler
from townlet.effects.parser import CommandParser
from townlet.effects.schema import CommandNode

__all__ = ["CompiledEffect", "EffectCatalog"]


@dataclass
class CompiledEffect:
    """Compiled effect with parsed and validated command pipelines."""

    id: str
    scope: str
    duration: int
    intensity: float
    reapply_policy: str
    observable: bool

    # Compiled command pipelines
    on_spawn: list[CommandNode]
    on_tick: list[CommandNode]
    on_despawn: list[CommandNode]
    on_interrupt: list[CommandNode]


@dataclass
class EffectCatalog:
    """Compiled effect catalog.

    Maps effect IDs to compiled effect definitions.
    """

    effects: dict[str, CompiledEffect]

    @classmethod
    def from_config(cls, config: EffectsConfig, schema: dict[str, str] | None = None) -> EffectCatalog:
        """Compile effects catalog from config.

        Args:
            config: Effects configuration from YAML
            schema: Type schema for command validation (optional for Phase 3.1)

        Returns:
            Compiled catalog with validated command pipelines
        """
        parser = CommandParser()
        compiler = CommandCompiler(schema) if schema else None

        effects = {}
        for defn in config.effect_definitions:
            # Parse commands to AST
            on_spawn = parser.parse_commands(defn.on_spawn)
            on_tick = parser.parse_commands(defn.on_tick)
            on_despawn = parser.parse_commands(defn.on_despawn)
            on_interrupt = parser.parse_commands(defn.on_interrupt)

            # Compile (validate) if schema provided
            if compiler:
                compiler.compile_commands(on_spawn)
                compiler.compile_commands(on_tick)
                compiler.compile_commands(on_despawn)
                compiler.compile_commands(on_interrupt)

            compiled = CompiledEffect(
                id=defn.id,
                scope=defn.scope.value,
                duration=defn.duration,
                intensity=defn.intensity,
                reapply_policy=defn.reapply_policy.value,
                observable=defn.observable,
                on_spawn=on_spawn,
                on_tick=on_tick,
                on_despawn=on_despawn,
                on_interrupt=on_interrupt,
            )

            effects[defn.id] = compiled

        return cls(effects=effects)

    def get(self, effect_id: str) -> CompiledEffect:
        """Get compiled effect by ID.

        Args:
            effect_id: Effect identifier

        Returns:
            Compiled effect

        Raises:
            KeyError: If effect ID not found
        """
        if effect_id not in self.effects:
            raise KeyError(f"Effect '{effect_id}' not found in catalog. Available effects: {list(self.effects.keys())}")
        return self.effects[effect_id]

    def __contains__(self, effect_id: str) -> bool:
        """Check if effect exists in catalog."""
        return effect_id in self.effects

    def __len__(self) -> int:
        """Number of effects in catalog."""
        return len(self.effects)
