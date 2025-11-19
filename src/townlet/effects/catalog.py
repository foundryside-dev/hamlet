"""Effects catalog compilation and loading."""

from __future__ import annotations

from dataclasses import dataclass

from townlet.config.effects_config import EffectDefinitionConfig, EffectsConfig

__all__ = ["EffectCatalog"]


@dataclass
class EffectCatalog:
    """Compiled effect catalog.

    Maps effect IDs to their definitions for runtime lookup.
    """

    effects: dict[str, EffectDefinitionConfig]

    @classmethod
    def from_config(cls, config: EffectsConfig) -> EffectCatalog:
        """Compile effects catalog from config.

        Args:
            config: Effects configuration from YAML

        Returns:
            Compiled catalog with effect ID lookup
        """
        effects = {defn.id: defn for defn in config.effect_definitions}
        return cls(effects=effects)

    def get(self, effect_id: str) -> EffectDefinitionConfig:
        """Get effect definition by ID.

        Args:
            effect_id: Effect identifier

        Returns:
            Effect definition

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
