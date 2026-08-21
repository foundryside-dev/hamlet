"""Config-in/behaviour-out tests for affordance occupancy wiring (hamlet-ef6699ab2a).

compile_vtc_affordance_occupancy existed and passed unit tests, but nothing called
it from the universe pipeline, so no config pack could express bed/queue/capacity
contention end-to-end. These tests pin the whole path: a custom action declared in
actions.yaml with `source_affordance` and a claim write compiles into the
transition schedule with its affordance row resolved, and env.step resolves two
agents contending for a capacity-1 affordance deterministically.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch
import yaml

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError

PRIMARY_LEVEL = "L0_test"

OCCUPIED_BY_VARIABLE = {
    "id": "occupied_by",
    "scope": "affordance",
    "type": "scalar",
    "default": -1.0,
    "lifetime": "episode",
    "readable_by": ["agent", "engine"],
    "writable_by": ["engine"],
    "description": "Agent id currently claiming this affordance, -1 when free",
}


def _declare_claim_action(pack: Path, *, source_affordance: str | None = "SLEEP", variable_id: str = "occupied_by") -> None:
    """Declare the occupancy variable and a CLAIM_BED custom action in the pack."""
    ref_path = pack / "variables_reference.yaml"
    ref = yaml.safe_load(ref_path.read_text())
    ref["variables"].append(OCCUPIED_BY_VARIABLE)
    ref_path.write_text(yaml.safe_dump(ref))

    actions_path = pack / "actions.yaml"
    actions = yaml.safe_load(actions_path.read_text())
    action = {
        "name": "CLAIM_BED",
        "description": "Claim the bed if it is free",
        "enabled_by_default": True,
        "source_affordance": source_affordance,
        "writes": [
            {
                "variable_id": variable_id,
                "expression": "agent_id",
                "condition": None,
                "composition": "claim_if_free",
                "phase": "resolve_affordance_access_and_occupancy",
                "priority": 0,
                "clamp": None,
                "telemetry_label": "claim_bed_occupancy",
            }
        ],
    }
    actions["actions"]["custom_actions"].append(action)
    actions_path.write_text(yaml.safe_dump(actions))


def test_claim_action_compiles_into_schedule_with_affordance_row(temp_config_pack: Path) -> None:
    """The declared claim write lands in the transition schedule's action-write
    program with its source affordance resolved to a registry row index."""
    _declare_claim_action(temp_config_pack)

    universe = UniverseCompiler().compile(temp_config_pack, primary_level=PRIMARY_LEVEL, use_cache=False)

    sleep_index = universe.metadata.affordance_id_to_index["SLEEP"]
    claim_writes = [w for w in universe.transition_schedule.action_write_program.writes if w.action_name == "CLAIM_BED"]
    assert len(claim_writes) == 1
    write = claim_writes[0]
    assert write.source_affordance == "SLEEP"
    assert write.affordance_index == sleep_index
    assert write.composition == "claim_if_free"
    assert write.phase == "resolve_affordance_access_and_occupancy"


def test_two_agents_contending_resolve_deterministically(temp_config_pack: Path) -> None:
    """Two agents both claiming a capacity-1 affordance in the same tick: the
    lower-indexed agent wins, the loser does not overwrite, other rows stay free."""
    _declare_claim_action(temp_config_pack)

    universe = UniverseCompiler().compile(temp_config_pack, primary_level=PRIMARY_LEVEL, use_cache=False)
    env = VectorizedHamletEnv.from_universe(
        universe,
        level_name=PRIMARY_LEVEL,
        num_agents=2,
        device=torch.device("cpu"),
    )
    env.reset()

    claim_id = universe.runtime_action_space.action_ids["CLAIM_BED"]
    env.step(torch.tensor([claim_id, claim_id]))

    occupied = env.vfs_registry.get("occupied_by", reader="engine")
    sleep_index = universe.metadata.affordance_id_to_index["SLEEP"]
    assert occupied[sleep_index].item() == 0.0
    for index in range(occupied.shape[0]):
        if index != sleep_index:
            assert occupied[index].item() == -1.0


def test_unknown_source_affordance_fails_at_compile(temp_config_pack: Path) -> None:
    _declare_claim_action(temp_config_pack, source_affordance="NO_SUCH_AFFORDANCE")

    with pytest.raises((CompilationError, ValueError)) as excinfo:
        UniverseCompiler().compile(temp_config_pack, primary_level=PRIMARY_LEVEL, use_cache=False)
    assert "NO_SUCH_AFFORDANCE" in str(excinfo.value)


def test_claim_write_without_source_affordance_fails_at_compile(temp_config_pack: Path) -> None:
    """claim_if_free/capacity_claim target an affordance row; without a source
    affordance the write would silently fall back to non-affordance semantics."""
    _declare_claim_action(temp_config_pack, source_affordance=None)

    with pytest.raises((CompilationError, ValueError)) as excinfo:
        UniverseCompiler().compile(temp_config_pack, primary_level=PRIMARY_LEVEL, use_cache=False)
    assert "source_affordance" in str(excinfo.value)


def test_write_targeting_unknown_variable_fails_at_compile(temp_config_pack: Path) -> None:
    _declare_claim_action(temp_config_pack, variable_id="no_such_variable")

    with pytest.raises((CompilationError, ValueError)) as excinfo:
        UniverseCompiler().compile(temp_config_pack, primary_level=PRIMARY_LEVEL, use_cache=False)
    assert "no_such_variable" in str(excinfo.value)
