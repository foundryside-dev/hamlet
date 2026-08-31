"""Effects catalog compilation and loading."""

from __future__ import annotations

from dataclasses import dataclass

from townlet.config.effects_config import EffectsConfig, EffectScope
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
    max_active_effects: dict[str, int] | None
    effect_name_to_id: dict[str, int] | None = None
    effect_id_to_name: dict[int, str] | None = None

    def __post_init__(self) -> None:
        scope_names = tuple(scope.value for scope in EffectScope)
        if self.effects and self.max_active_effects is None:
            raise ValueError("max_active_effects is required when EffectCatalog declares effects")
        if not self.effects and self.max_active_effects is not None:
            raise ValueError("max_active_effects must be None when EffectCatalog declares no effects")
        if self.max_active_effects is not None:
            missing = [scope for scope in scope_names if scope not in self.max_active_effects]
            unknown = [scope for scope in self.max_active_effects if scope not in scope_names]
            if missing or unknown:
                raise ValueError(f"max_active_effects must declare exactly {scope_names}; missing {missing}, unknown {unknown}")
            negative = {scope: count for scope, count in self.max_active_effects.items() if count < 0}
            if negative:
                raise ValueError(f"max_active_effects values must be >= 0; got {negative}")
            self.max_active_effects = dict(self.max_active_effects)

        # Build deterministic ID mapping for encoding effects in observations.
        ordered_ids = sorted(self.effects.keys())
        self.effect_name_to_id = {name: idx for idx, name in enumerate(ordered_ids)}
        self.effect_id_to_name = {idx: name for name, idx in self.effect_name_to_id.items()}

    @classmethod
    def from_config(
        cls,
        config: EffectsConfig,
        schema: dict[str, str] | None = None,
        *,
        time_enabled: bool = True,
    ) -> EffectCatalog:
        """Compile effects catalog from config.

        Args:
            config: Effects configuration from YAML
            schema: Type schema for command validation (optional for Phase 3.1)

        Returns:
            Compiled catalog with validated command pipelines
        """
        parser = CommandParser()
        compiler = CommandCompiler(schema, time_enabled=time_enabled) if schema else None

        effects = {}
        for defn in config.effect_definitions:
            # Parse commands to AST
            on_spawn = parser.parse_commands(defn.on_spawn)
            on_tick = parser.parse_commands(defn.on_tick)
            on_despawn = parser.parse_commands(defn.on_despawn)
            on_interrupt = parser.parse_commands(defn.on_interrupt)

            # Compile (validate) if schema provided
            if compiler:
                try:
                    compiler.compile_commands(on_spawn)
                    compiler.compile_commands(on_tick)
                    compiler.compile_commands(on_despawn)
                    compiler.compile_commands(on_interrupt)
                except Exception as exc:  # pragma: no cover - error path
                    raise type(exc)(f"Effect '{defn.id}' failed to compile: {exc}") from exc

            compiled = CompiledEffect(
                id=defn.id,
                scope=defn.scope.value,
                duration=defn.duration,
                reapply_policy=defn.reapply_policy.value,
                observable=defn.observable,
                on_spawn=on_spawn,
                on_tick=on_tick,
                on_despawn=on_despawn,
                on_interrupt=on_interrupt,
            )

            effects[defn.id] = compiled

        budget = None if config.max_active_effects is None else dict(config.max_active_effects)
        return cls(effects=effects, max_active_effects=budget)

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

    def get_effect_index(self, effect_id: str) -> int:
        """Return deterministic integer ID for an effect, -1 if unknown."""
        if self.effect_name_to_id is None:
            return -1
        return self.effect_name_to_id.get(effect_id, -1)
