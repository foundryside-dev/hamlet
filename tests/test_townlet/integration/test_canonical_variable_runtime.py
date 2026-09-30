"""Canonical declarations drive state, named consumers and cache behavior."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import torch
import yaml

from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler

LEVEL = "L0_simple"


def _pack(tmp_path: Path, declarations: list[dict]) -> Path:
    pack = tmp_path / "world"
    shutil.copytree(Path("configs/simple"), pack)
    # These tests explicitly author a complete canonical catalog, independent of
    # whatever variables the demonstration happens to contain.
    for filename in ("variables.yaml",):
        path = pack / filename
        if path.exists():
            path.unlink()
    payload = {
        "variables": {
            "version": "1.0",
            "evaluation_mode": "mark_and_sweep",
            "debug_logging": False,
            "extents": {},
            "item_profiles": ["default_item"],
            "declarations": declarations,
        }
    }
    (pack / "concepts").mkdir()
    (pack / "concepts/state.yml").write_text(yaml.safe_dump(payload, sort_keys=False))
    return pack


def _variable(identifier: str, *, scope: str = "global", lifetime: str = "episode", initial: float = 2.0) -> dict:
    return {
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "id": identifier,
        "scope": scope,
        "type": "scalar",
        "lifetime": lifetime,
        "semantic_type": "custom",
        "initial_value": initial,
        "exposed_to": [],
    }


def _compile(pack: Path) -> CompiledUniverse:
    return UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


@pytest.mark.parametrize("scope", ["global", "agent"])
@pytest.mark.parametrize("cached", [False, True])
def test_declared_mutation_and_named_reward_consume_the_same_state(tmp_path: Path, scope: str, cached: bool) -> None:
    score = _variable("score", scope=scope)
    if scope == "global":
        # Global state is updated by its supported derived-state evaluator;
        # per-agent action masks cannot target a scalar global write.
        score["expression"] = "3.0"
    pack = _pack(tmp_path, [score])
    actions_path = pack / "actions.yaml"
    actions = yaml.safe_load(actions_path.read_text())
    actions["actions"]["custom_actions"][0]["writes"] = [
        {
            "variable_id": "score",
            "expression": "1.0",
            "condition": None,
            "composition": "additive_delta",
            "phase": "apply_completion_bonuses",
            "priority": 0,
            "clamp": None,
            "telemetry_label": "advance_score",
        }
    ]
    if scope == "global":
        actions["actions"]["custom_actions"][0]["writes"] = []
    actions_path.write_text(yaml.safe_dump(actions, sort_keys=False))
    drive_path = pack / "levels" / LEVEL / "drive.yaml"
    drive = yaml.safe_load(drive_path.read_text())
    drive["drive"]["extrinsic"] = {
        "type": "vfs_variable",
        "base": 0.0,
        "bar_bonuses": [],
        "variable_bonuses": [{"variable": "score", "weight": 0.5}],
        "apply_modifiers": [],
    }
    drive["drive"]["shaping"] = []
    drive_path.write_text(yaml.safe_dump(drive, sort_keys=False))
    universe = _compile(pack)
    if cached:
        artifact = tmp_path / "world.msgpack"
        universe.save_to_cache(artifact)
        universe = CompiledUniverse.load_from_cache(artifact)
    env = universe.create_environment(num_agents=2, level_name=LEVEL, device="cpu")
    env.reset()
    wait = universe.get_level(LEVEL).runtime_action_space.action_ids["WAIT"]
    _, rewards, dones, info = env.step(torch.full((2,), wait, dtype=torch.long))
    assert not dones.any()
    assert torch.all(env.vfs_registry.get("score", reader="engine") == 3.0)
    assert torch.allclose(rewards, torch.full((2,), 1.5))
    assert torch.allclose(info["reward_components"]["extrinsic"], rewards)


@pytest.mark.parametrize("cached", [False, True])
def test_lifetime_and_derived_state_do_not_depend_on_transport(tmp_path: Path, cached: bool) -> None:
    derived = _variable("derived", initial=4.0)
    derived["expression"] = "tick + 4.0"
    declarations = [
        _variable("per_tick", lifetime="tick", initial=1.0),
        _variable("per_episode", lifetime="episode", initial=2.0),
        _variable("persistent", lifetime="persistent", initial=3.0),
        derived,
    ]
    universe = _compile(_pack(tmp_path, declarations))
    if cached:
        universe = CompiledUniverse.from_dict(universe.to_dict())
    env = universe.create_environment(num_agents=2, level_name=LEVEL, device="cpu")
    env.reset()
    for identifier in ("per_tick", "per_episode", "persistent"):
        original = env.vfs_registry.get(identifier, reader="engine")
        env.vfs_registry.set_engine_value(identifier, torch.full_like(original, 9.0))
    env.step(torch.zeros(2, dtype=torch.long))
    assert env.vfs_registry.get("per_tick", reader="engine").item() == 1.0
    assert env.vfs_registry.get("per_episode", reader="engine").item() == 9.0
    assert env.vfs_registry.get("persistent", reader="engine").item() == 9.0
    assert env.vfs_registry.get("derived", reader="engine").item() == 4.0
    env.step(torch.zeros(2, dtype=torch.long))
    assert env.vfs_registry.get("derived", reader="engine").item() == 5.0
    env.reset()
    assert env.vfs_registry.get("per_tick", reader="engine").item() == 1.0
    assert env.vfs_registry.get("per_episode", reader="engine").item() == 2.0
    assert env.vfs_registry.get("persistent", reader="engine").item() == 9.0
    assert env.vfs_registry.get("derived", reader="engine").item() == 4.0
