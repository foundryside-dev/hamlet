"""An item-scoped effect's `target` is the item, at compile as at runtime (VFS WP12 follow-up).

EffectManager._lifecycle_context binds an item-scoped effect with `target_is_item`, so
`target.vfs.X` reads and writes the item's profile row. The command compiler typed the
same path against the agent registry: `on_tick: modify: target.vfs.derived` (an agent
variable) compiled green and died at step with a bare `KeyError: ('food', 'derived')`.
The compiler now binds `target` per effect scope (and per for_each body), so an agent path
on an item target refuses at compile and an item-profile path compiles and runs.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
import torch
import yaml

from townlet.effects.compiler import CommandCompiler
from townlet.effects.schema import CommandNode, CommandType
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
from townlet.world.expression.type_checker import TypeCheckError

ITEMS_SMOKE = Path(__file__).resolve().parents[4] / "configs" / "test" / "items_smoke"
LEVEL = "L0_smoke"


def _pack(tmp_path: Path, command: dict[str, Any]) -> Path:
    pack = tmp_path / "pack"
    shutil.copytree(ITEMS_SMOKE, pack, ignore=shutil.ignore_patterns(".compiled"))
    variables = yaml.safe_load((pack / "variables.yaml").read_text())
    variables["variables"]["declarations"].append(
        {
            "id": "public_state",
            "scope": "agent",
            "type": "scalar",
            "lifetime": "episode",
            "semantic_type": "custom",
            "readable_by": ["engine"],
            "writable_by": ["engine"],
            "exposed_to": [],
            "initial_value": 1.0,
        }
    )
    (pack / "variables.yaml").write_text(yaml.safe_dump(variables, sort_keys=False))
    effects = yaml.safe_load((pack / "effects.yaml").read_text())
    effects["effect_definitions"].append(
        {
            "id": "poke",
            "scope": "item",
            "duration": 3,
            "reapply_policy": "renew",
            "observable": True,
            "on_spawn": [],
            "on_tick": [command],
            "on_despawn": [],
            "on_interrupt": [],
        }
    )
    (pack / "effects.yaml").write_text(yaml.safe_dump(effects, sort_keys=False))
    return pack


def _compile(pack: Path) -> CompiledUniverse:
    return UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


@pytest.mark.parametrize(
    "command",
    [
        {"modify": "target.vfs.public_state", "value": "5.0"},
        {"modify": "target.vfs.freshness", "value": "target.vfs.public_state"},
        {"modify": "target.bar.energy", "value": "0.5"},
    ],
    ids=["agent_write", "agent_read", "bar_write"],
)
def test_item_effect_naming_agent_state_on_its_target_refuses_at_compile(tmp_path: Path, command: dict[str, Any]) -> None:
    with pytest.raises(CompilationError, match=r"\[EFFECT-COMPILE\].*effects\.yaml:\d+.*Effect 'poke'"):
        _compile(_pack(tmp_path, command))


def test_item_effect_writes_its_item_through_target(tmp_path: Path) -> None:
    universe = _compile(_pack(tmp_path, {"modify": "target.vfs.freshness", "value": "target.vfs.freshness - 10.0"}))
    env = VectorizedHamletEnv.from_universe(universe, level_name=LEVEL, num_agents=2, device="cpu")
    env.reset()
    registry = env.vfs_registry
    (item,) = [item for item in env.item_manager.active_items.values() if registry.get_item_profile_for_index(item.vfs_index) == "food"][:1]
    bars = {name: env.meters[:, index] for name, index in env.meter_name_to_index.items()}
    env.effect_manager.spawn_effect(
        "poke",
        target_entity_id=item.vfs_index,
        intensity=1.0,
        current_step=0,
        bars=bars,
        vfs_registry=registry,
        item_manager=env.item_manager,
    )
    before = float(registry.read_item("food", "freshness", item.vfs_index, reader="engine"))
    wait = next(i for i, action in enumerate(env.action_space.actions) if action.name == "WAIT")
    env.step(torch.full((2,), wait, dtype=torch.long))
    after = float(registry.read_item("food", "freshness", item.vfs_index, reader="engine"))
    assert after == pytest.approx(before - 10.0)


SCHEMA = {
    "vfs.mood": "float",
    "target.vfs.mood": "float",
    "target.bar.energy": "float",
    "self.vfs.freshness": "float",
}


def _modify(path: str, value: str) -> CommandNode:
    return CommandNode(type=CommandType.MODIFY, path=path, value_expr=value)


def test_for_each_over_inventory_items_types_target_as_the_item() -> None:
    """Inside an agent pipeline, an inventory loop rebinds `target` to each item row."""
    loop = CommandNode(
        type=CommandType.FOR_EACH,
        collection="inventory_items",
        iterator="item",
        body=[_modify("target.vfs.freshness", "target.vfs.freshness * 0.5")],
    )
    CommandCompiler(SCHEMA, agent_target=True).compile_command(loop)

    agent_path_on_item = CommandNode(
        type=CommandType.FOR_EACH, collection="inventory_items", iterator="item", body=[_modify("target.vfs.mood", "1.0")]
    )
    with pytest.raises(TypeCheckError, match="target.vfs.mood"):
        CommandCompiler(SCHEMA, agent_target=True).compile_command(agent_path_on_item)
