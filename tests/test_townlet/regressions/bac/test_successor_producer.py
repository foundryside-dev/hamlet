"""Authored producer proofs: legality belongs to the committed successor."""

import shutil
from pathlib import Path

import pytest
import torch
import yaml

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.training.replay_contract import validate_successor_masks
from townlet.universe.compiler import UniverseCompiler


def _write(path: Path, value: dict) -> None:
    path.write_text(yaml.safe_dump(value, sort_keys=False))


def _environment(tmp_path: Path, *, only_get: bool, terminal: bool, lifespan: int) -> VectorizedHamletEnv:
    """Compile real item pickup and lane death, without injecting runtime state."""
    torch.set_num_threads(1)
    source = Path(__file__).resolve().parents[4] / "configs" / "aspatial_test"
    pack = tmp_path / "successor_pack"
    shutil.copytree(source, pack)
    actions = yaml.safe_load((pack / "actions.yaml").read_text())
    actions["actions"]["custom_actions"].append({"name": "DISABLED", "description": "Global disabled control", "enabled_by_default": False})
    _write(pack / "actions.yaml", actions)
    _write(
        pack / "items.yaml",
        {
            "items": {
                "version": "1.0",
                "max_items_per_agent": 1,
                "max_items_in_world": 1,
                "item_types": [
                    {
                        "id": "token",
                        "name": "Token",
                        "icon": "T",
                        "tags": ["token"],
                        "exclusive": True,
                        "vfs_profile": "default_item",
                        "description": "Pickup legality witness",
                        "duration": None,
                        "cooldown": None,
                        "interactions": {"on_pickup": [], "on_use": [], "on_drop": []},
                    }
                ],
            }
        },
    )
    _write(
        pack / "variables.yaml",
        {
            "variables": {
                "version": "1.0",
                "item_profiles": ["default_item"],
                "declarations": [
                    {
                        "id": "quality",
                        "scope": "item",
                        "profile": "default_item",
                        "type": "scalar",
                        "lifetime": "episode",
                        "semantic_type": "custom",
                        "exposed_to": [],
                        "readable_by": ["engine", "agent"],
                        "writable_by": ["engine"],
                        "initial_value": 1.0,
                    }
                ],
            }
        },
    )
    level = pack / "levels" / "L0"
    _write(
        level / "items.yaml",
        {"version": "1.0", "items": [{"item_type": "token", "spawn_count": 1, "placement": {"mode": "random"}}]},
    )
    training = yaml.safe_load((level / "training.yaml").read_text())
    training["training"]["population"]["size"] = 2
    training["training"]["training_loop"]["max_steps_per_episode"] = lifespan
    training["training"]["enabled_actions"] = {"custom": ["GET"]} if only_get else None
    _write(level / "training.yaml", training)
    if terminal:
        _write(
            pack / "transition_rules.yaml",
            {
                "version": "1.0",
                "transition_rules": [
                    {
                        "id": "authored_lane_death",
                        "phase": "apply_transition_rules",
                        "condition": "tick >= where(agent_id == 0, 1.0, 3.0)",
                        "writes": [
                            {
                                "variable_id": "bar.energy",
                                "expression": "0.0",
                                "composition": "overwrite",
                                "condition": None,
                                "clamp": None,
                                "effect": None,
                            }
                        ],
                    }
                ],
            },
        )
    universe = UniverseCompiler().compile(pack, primary_level="L0", use_cache=False)
    env = VectorizedHamletEnv(universe=universe, level_name="L0", num_agents=2, device="cpu")
    env.reset()
    return env


def _actions(env: VectorizedHamletEnv, name: str) -> torch.Tensor:
    return torch.full((env.num_agents,), env.action_space.get_action_by_name(name).id, dtype=torch.long)


def _successor(env: VectorizedHamletEnv, name: str) -> tuple:
    observations, rewards, dones, info = env.step(_actions(env, name))
    masks = info["successor_action_masks"]
    assert masks.dtype == torch.bool
    assert masks.shape == (env.num_agents, env.action_dim)
    assert torch.equal(observations, env._get_observations())
    assert torch.equal(masks, env.get_action_masks())
    assert not masks[:, env.action_space.get_action_by_name("DISABLED").id].any()
    validate_successor_masks(masks, dones, action_dim=env.action_dim)
    return observations, rewards, dones.clone(), info


def test_mask_belongs_to_returned_successor(tmp_path: Path) -> None:
    env = _environment(tmp_path, only_get=False, terminal=False, lifespan=6)
    get_id = env.action_space.get_action_by_name("GET").id
    assert env.get_action_masks()[:, get_id].all()

    _, _, dones, pickup = _successor(env, "GET")
    assert not dones.any()
    captured = pickup["successor_action_masks"].clone()
    assert not captured[:, get_id].any()  # Actual pickup filled the inventory.
    assert env.item_inventory is not None
    assert (env.item_inventory.slots != -1).all()

    _, _, _, dropped = _successor(env, "DROP_SLOT_0")
    assert dropped["successor_action_masks"][:, get_id].all()
    assert torch.equal(pickup["successor_action_masks"], captured)
    dropped["successor_action_masks"].zero_()  # Caller owns its snapshot.
    assert env.get_action_masks()[:, get_id].all()
    assert torch.equal(pickup["successor_action_masks"], captured)
    env.reset()
    assert torch.equal(pickup["successor_action_masks"], captured)


def test_terminal_and_inactive_rows_are_valid_empty_successors(tmp_path: Path) -> None:
    env = _environment(tmp_path, only_get=False, terminal=True, lifespan=5)
    _successor(env, "WAIT")
    _, _, dones, terminal = _successor(env, "WAIT")
    assert dones.tolist() == [True, False]
    assert terminal["active_on_entry"].tolist() == [True, True]
    assert terminal["newly_terminal"].tolist() == [True, False]
    assert not terminal["successor_action_masks"][0].any()
    assert terminal["successor_action_masks"][1].any()
    historical = terminal["successor_action_masks"].clone()
    _, rewards, _, following = _successor(env, "WAIT")
    assert following["active_on_entry"].tolist() == [False, True]
    assert following["step_counts"].tolist() == [2, 3]
    assert rewards[0] == 0
    assert not following["newly_terminal"].any()
    assert torch.equal(terminal["successor_action_masks"], historical)
    _successor(env, "WAIT")
    _, rewards, dones, extra = _successor(env, "WAIT")
    assert dones.all()
    assert not extra["successor_action_masks"].any()
    assert not extra["active_on_entry"].any()
    assert not extra["newly_terminal"].any()
    assert not rewards.any()
    env.reset()
    assert torch.equal(terminal["successor_action_masks"], historical)


def test_external_cap_keeps_real_selectable_nonterminal_successor(tmp_path: Path) -> None:
    env = _environment(tmp_path, only_get=False, terminal=False, lifespan=10)
    # The runner stops collecting after two ticks; this is not an environment retirement.
    _successor(env, "WAIT")
    _, _, dones, capped = _successor(env, "WAIT")
    assert not dones.any()
    assert not capped["newly_terminal"].any()
    assert capped["successor_action_masks"].any(dim=1).all()
    snapshot = capped["successor_action_masks"].clone()
    env.reset()
    assert torch.equal(capped["successor_action_masks"], snapshot)


def test_truly_live_empty_successor_has_located_diagnostic(tmp_path: Path) -> None:
    env = _environment(tmp_path, only_get=True, terminal=False, lifespan=10)
    assert env.get_action_masks().sum(dim=1).tolist() == [1, 1]
    with pytest.raises(ValueError, match=r"nonterminal successor.*no legal action") as error:
        env.step(_actions(env, "GET"))
    message = str(error.value)
    assert str(env.config_pack_path) in message
    assert "L0" in message
    assert "tick=1" in message
    assert "[0, 1]" in message
    assert not env.dones.any()
    assert not env.get_action_masks().any()  # No fabricated rescue action.


def test_empty_mask_at_retirement_is_valid(tmp_path: Path) -> None:
    env = _environment(tmp_path, only_get=True, terminal=False, lifespan=1)
    _, _, dones, info = _successor(env, "GET")
    assert dones.all()
    assert info["newly_retired"].all()
    assert not info["successor_action_masks"].any()
