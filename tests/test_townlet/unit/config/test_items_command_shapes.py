"""Item interaction commands are effects commands and refuse malformed shapes at parse (hamlet-5a87550adb)."""

import pytest
from pydantic import ValidationError

from townlet.config.items_config import ItemInteractionsConfig


def test_nested_spawn_effect_mapping_refuses_at_parse():
    with pytest.raises(ValidationError, match="spawn_effect"):
        ItemInteractionsConfig(on_use=[{"spawn_effect": {"effect_id": "ate_food", "target": "agent", "intensity": "self.vfs.calories"}}])


def test_sibling_key_spawn_effect_is_accepted():
    cfg = ItemInteractionsConfig(on_use=[{"spawn_effect": "ate_food", "target": "target", "intensity": 1.0}])
    assert cfg.on_use[0]["spawn_effect"] == "ate_food"


def test_unknown_command_key_refuses():
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ItemInteractionsConfig(on_drop=[{"modify": "target.bar.energy", "value": "1.0", "bogus": 1}])
