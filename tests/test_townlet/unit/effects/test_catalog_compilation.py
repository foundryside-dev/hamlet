"""Tests for effects catalog compilation."""

from pathlib import Path

import pytest
import yaml

from townlet.config.effects_config import EffectsConfig
from townlet.effects.catalog import EffectCatalog


def test_catalog_from_config():
    """EffectCatalog compiles from EffectsConfig."""
    config = EffectsConfig(
        version="1.0",
        effect_definitions=[
            {
                "id": "ate_food",
                "scope": "agent",
                "duration": 10,
                "reapply_policy": "stack",
            }
        ],
    )

    catalog = EffectCatalog.from_config(config)

    assert "ate_food" in catalog.effects
    assert catalog.effects["ate_food"].id == "ate_food"
    assert catalog.effects["ate_food"].duration == 10


def test_catalog_load_smoke_config():
    """EffectCatalog loads effects_smoke config."""
    config_path = Path("configs/test/effects_smoke/effects.yaml")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    config = EffectsConfig(**data)
    catalog = EffectCatalog.from_config(config)

    # Verify all 4 smoke test effects loaded
    assert len(catalog.effects) == 4
    assert "energy_regen" in catalog.effects
    assert "health_boost" in catalog.effects
    assert "poison" in catalog.effects
    assert "buff_replace" in catalog.effects


def test_catalog_get_effect():
    """EffectCatalog.get() retrieves effect by ID."""
    config = EffectsConfig(
        version="1.0",
        effect_definitions=[{"id": "ate_food", "scope": "agent", "duration": 10, "reapply_policy": "stack"}],
    )

    catalog = EffectCatalog.from_config(config)
    effect = catalog.get("ate_food")

    assert effect.id == "ate_food"
    assert effect.duration == 10


def test_catalog_get_missing_effect_raises():
    """EffectCatalog.get() raises KeyError for missing effect."""
    catalog = EffectCatalog.from_config(EffectsConfig(version="1.0", effect_definitions=[]))

    with pytest.raises(KeyError, match="unknown_effect"):
        catalog.get("unknown_effect")


def test_catalog_contains():
    """EffectCatalog.__contains__() checks effect existence."""
    config = EffectsConfig(
        version="1.0",
        effect_definitions=[{"id": "ate_food", "scope": "agent", "duration": 10, "reapply_policy": "stack"}],
    )

    catalog = EffectCatalog.from_config(config)

    assert "ate_food" in catalog
    assert "unknown_effect" not in catalog


def test_catalog_len():
    """EffectCatalog.__len__() returns number of effects."""
    config = EffectsConfig(
        version="1.0",
        effect_definitions=[
            {"id": "effect1", "scope": "agent", "duration": 10, "reapply_policy": "stack"},
            {"id": "effect2", "scope": "agent", "duration": 20, "reapply_policy": "renew"},
        ],
    )

    catalog = EffectCatalog.from_config(config)

    assert len(catalog) == 2
