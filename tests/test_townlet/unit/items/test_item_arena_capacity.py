"""One rule for item capacity (findings_compiler F3, hamlet-45f501e15b).

The item arena is `max_items_in_world + max_items_per_agent × agents_per_world`. Either capacity
alone may be 0: a world with items on the ground and no inventory is a legitimate designer shape
and must compile and spawn. Item types declared into an empty arena are refused at parse with a
message that says exactly that; nothing is silently discarded. An `items` declaration with no
item types and no arena declares no items and lowers to no catalog.
"""

from __future__ import annotations

import shutil
from collections import Counter
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from townlet.config.items_config import ItemsCatalogConfig
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationError

ITEMS_SMOKE = Path("configs/test/items_smoke")
LEVEL = "L0_smoke"


def _items_smoke_with(tmp_path: Path, **capacities: int) -> Path:
    pack = tmp_path / "items_smoke"
    shutil.copytree(ITEMS_SMOKE, pack, ignore=shutil.ignore_patterns(".compiled"))
    items_path = pack / "items.yaml"
    text = items_path.read_text()
    for key, value in capacities.items():
        needle = f"{key}: {'3' if key == 'max_items_per_agent' else '10'}"
        assert needle in text, needle
        text = text.replace(needle, f"{key}: {value}", 1)
    items_path.write_text(text)
    return pack


def test_items_on_the_ground_with_no_inventory_compile_and_spawn(tmp_path: Path) -> None:
    """F3's reproduction: `max_items_per_agent: 0`, `max_items_in_world: 10`."""
    pack = _items_smoke_with(tmp_path, max_items_per_agent=0)

    compiled = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)

    assert compiled.items_catalog is not None
    assert compiled.items_catalog.max_items_per_agent == 0
    assert compiled.items_hash is not None
    assert compiled.get_level(LEVEL).items_appearance is not None

    env = VectorizedHamletEnv.from_universe(compiled, level_name=LEVEL, num_agents=2, device="cpu")
    env.reset()
    assert env.item_manager is not None
    assert Counter(item.item_type for item in env.item_manager.worlds[0].active.values()) == Counter({"apple": 3, "medkit": 1})

    # No inventory means no pickup, use or drop actions; the catalog itself is intact.
    action_names = {action.name for action in compiled.get_level(LEVEL).runtime_action_space.actions}
    assert "GET" not in action_names
    assert not {name for name in action_names if name.startswith(("USE_SLOT_", "DROP_SLOT_"))}


def test_item_types_declared_into_an_empty_arena_refuse_at_parse(tmp_path: Path) -> None:
    pack = _items_smoke_with(tmp_path, max_items_per_agent=0, max_items_in_world=0)

    with pytest.raises(CompilationError) as caught:
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)

    assert len(caught.value.issues) == 1, str(caught.value)
    issue = caught.value.issues[0]
    assert issue.code == ErrorCode.LOAD_ERROR
    assert issue.location == f"{pack / 'items.yaml'}:1"
    assert "max_items_in_world + max_items_per_agent × agents_per_world is 0" in issue.message
    assert "no item arena" in issue.message


def test_catalog_dto_states_the_arena_rule() -> None:
    base = {"version": "1.0", "item_types": [], "max_items_per_agent": 0, "max_items_in_world": 0}
    item = yaml.safe_load((ITEMS_SMOKE / "items.yaml").read_text())["items"]["item_types"][0]

    # Either capacity alone may be 0.
    assert ItemsCatalogConfig.model_validate({**base, "item_types": [item], "max_items_in_world": 1}).max_items_per_agent == 0
    assert ItemsCatalogConfig.model_validate({**base, "item_types": [item], "max_items_per_agent": 1}).max_items_in_world == 0
    # An empty catalog with no arena is a valid DTO; the compiler lowers it to no catalog.
    assert ItemsCatalogConfig.model_validate(base).item_types == []

    with pytest.raises(ValidationError, match="no item arena"):
        ItemsCatalogConfig.model_validate({**base, "item_types": [item]})


def test_empty_catalog_with_no_arena_lowers_to_no_catalog(test_config_pack_path: Path) -> None:
    """`configs/test/model_config/items.yaml` declares `item_types: []` at 0/0: no items, exactly
    as an absent declaration says."""
    compiled = UniverseCompiler().compile(test_config_pack_path, primary_level="L0_test", use_cache=False)

    assert compiled.items_catalog is None
    assert compiled.items_hash is None
