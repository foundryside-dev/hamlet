"""Affordance-scope state is per world (owner ruling S1: the batch is N independent worlds).

Affordance-scope storage was one ``[num_affordances]`` store shared by every world: an
occupancy claim in world 0 took the bed in world 1, and a transition rule reading a global
had "no single world" and was refused at compile. Storage is now ``[num_worlds,
num_affordances, ...]`` (a leading world axis, as globals have), so:

- an occupancy claim lands in its own world's row; there is no cross-world contention;
- a transition rule on affordance state is masked by its own world's agent, and a global
  it reads spreads along its own world's affordance rows (never aligned with the
  affordance axis, even when there are as many worlds as affordances);
- persistent save/restore carries the world axis;
- an effect bound to a world reads and writes its world's affordance rows only.

The differential method: two runs that differ only in world 0's actions leave worlds
1..N-1 bitwise identical.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
import torch
import yaml

from tests.test_townlet.unit.vfs.test_vtc_affordance_occupancy import _affordance_action, _write
from townlet.determinism import seed_all
from townlet.effects.context import ExecutionContext
from townlet.universe.compiler import UniverseCompiler
from townlet.vfs import compile_vtc_transition_rules
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef, VariableScope
from townlet.vfs.vtc import (
    VTCWriteRefusalError,
    VTCWriteTarget,
    compile_vtc_affordance_occupancy,
    compile_vtc_transition_rules_with_phase_graph,
)

WITNESS = Path(__file__).resolve().parents[4] / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"
N = 4  # the witness level declares 4 affordances: worlds and affordances coincide in extent


def _declaration(var_id: str, scope: str, initial: float) -> dict[str, Any]:
    return {
        "id": var_id,
        "scope": scope,
        "type": "scalar",
        "lifetime": "episode",
        "semantic_type": "custom",
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "exposed_to": [],
        "initial_value": initial,
    }


def _edit(path: Path, edit: Any) -> None:
    payload = yaml.safe_load(path.read_text())
    edit(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


@pytest.fixture(scope="module")
def universe(tmp_path_factory: pytest.TempPathFactory):
    pack = tmp_path_factory.mktemp("affordance_per_world") / "pack"
    shutil.copytree(WITNESS, pack, ignore=shutil.ignore_patterns(".compiled"))
    _edit(
        pack / "variables.yaml",
        lambda v: v["variables"]["declarations"].extend(
            [
                _declaration("pressure", "global", 0.0),
                _declaration("wear", "affordance", 0.0),
                _declaration("occupied_by", "affordance", -1.0),
            ]
        ),
    )
    claim = {
        "name": "CLAIM_SLEEP",
        "description": "Claim this world's bed if it is free",
        "enabled_by_default": True,
        "source_affordance": "SLEEP",
        "writes": [
            {
                "variable_id": "occupied_by",
                "expression": "agent_id",
                "condition": None,
                "composition": "claim_if_free",
                "phase": "resolve_affordance_access_and_occupancy",
                "priority": 0,
                "clamp": None,
                "telemetry_label": "claim_sleep",
            }
        ],
    }
    _edit(pack / "actions.yaml", lambda a: a["actions"]["custom_actions"].append(claim))
    # Wear grows by its world's pressure (a global read, refused before S1-per-world
    # affordance state) and by one where its world's bed is claimed.
    rule = {
        "id": "wear_from_pressure",
        "phase": "apply_transition_rules",
        "condition": None,
        "writes": [
            {
                "variable_id": "wear",
                "expression": "pressure + where(occupied_by >= 0.0, 1.0, 0.0)",
                "composition": "additive_delta",
                "condition": None,
                "clamp": None,
                "effect": None,
            }
        ],
    }
    (pack / "transition_rules.yaml").write_text(yaml.safe_dump({"version": "1.0", "transition_rules": [rule]}, sort_keys=False))
    return UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def _action(env, name: str) -> int:
    return next(index for index, action in enumerate(env.action_space.actions) if action.name == name)


PRESSURE = torch.tensor([0.5, 1.0, 1.5, 2.0])


def _run(universe, world0_claims: bool, steps: int = 3) -> tuple[Any, list[dict[str, torch.Tensor]]]:
    seed_all(7)
    env = universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    seed_all(7)
    env.reset()
    env.vfs_registry.set("pressure", PRESSURE.clone(), writer="engine")
    wait, claim = _action(env, "WAIT"), _action(env, "CLAIM_SLEEP")
    trace = []
    for step in range(steps):
        actions = torch.full((N,), wait, dtype=torch.long)
        if world0_claims and step == 0:
            actions[0] = claim
        obs, rewards, _, _ = env.step(actions)
        trace.append(
            {
                "obs": obs.clone(),
                "rewards": rewards.clone(),
                "meters": env.meters.clone(),
                **{name: env.vfs_registry.get(name, reader="engine").clone() for name in env.vfs_registry.variables},
            }
        )
    return env, trace


def test_world0s_claim_and_wear_leave_every_other_world_bitwise_identical(universe) -> None:
    _, quiet = _run(universe, world0_claims=False)
    env, active = _run(universe, world0_claims=True)

    for step, (a, b) in enumerate(zip(quiet, active, strict=True)):
        for key in a:
            assert torch.equal(a[key][1:], b[key][1:]), f"step {step}: {key} moved in worlds 1..{N - 1}"

    sleep = universe.metadata.affordance_id_to_index["SLEEP"]
    occupied = active[-1]["occupied_by"]
    assert occupied.shape == (N, 4)
    assert occupied[0, sleep] == 0.0 and bool((occupied[1:] == -1.0).all())
    # Each world's wear grew by its own world's pressure, along every affordance row; world
    # 0's claimed bed also by one per tick from the claim on.
    steps = len(active)
    for world in range(1, N):
        assert torch.allclose(active[-1]["wear"][world], torch.full((4,), steps * float(PRESSURE[world])))
    expected0 = torch.full((4,), steps * float(PRESSURE[0]))
    expected0[sleep] += steps
    assert torch.allclose(active[-1]["wear"][0], expected0)


def test_a_done_worlds_affordance_state_is_frozen(universe) -> None:
    env = universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    env.reset()
    env.vfs_registry.set("pressure", PRESSURE.clone(), writer="engine")
    env.dones[2] = True
    env.step(torch.full((N,), _action(env, "WAIT"), dtype=torch.long))
    wear = env.vfs_registry.get("wear", reader="engine")
    assert bool((wear[2] == 0.0).all())
    assert torch.allclose(wear[3], torch.full((4,), 2.0))


# --- the transition-rule compile and runtime ------------------------------------------------

_RULE_TARGETS = {
    "pressure": VTCWriteTarget(VariableScope.GLOBAL, "scalar", meter=False, expression=None),
    "wear": VTCWriteTarget(VariableScope.AFFORDANCE, "scalar", meter=False, expression=None),
    "energy": VTCWriteTarget(VariableScope.AGENT, "scalar", meter=True, expression=None),
}


def _wear_rule(expression: str, condition: str | None = None, target: str = "wear") -> dict:
    return {
        "id": "wear_from_pressure",
        "phase": "apply_transition_rules",
        "condition": condition,
        "writes": [{"variable_id": target, "expression": expression, "composition": "additive_delta"}],
    }


@pytest.mark.parametrize(("expression", "condition"), [("wear * 0.0 + pressure", None), ("pressure", None), ("1.0", "pressure > 0.5")])
def test_an_affordance_rule_reading_a_global_reads_its_own_world(expression: str, condition: str | None) -> None:
    """Three worlds and three affordances: a global aligned by its trailing axis would pass
    by coincidence of extents and give each affordance another world's pressure."""
    program = compile_vtc_transition_rules([_wear_rule(expression, condition)], _RULE_TARGETS)
    pressure = torch.tensor([0.0, 1.0, 2.0])
    updated = program.apply(
        vfs_state={"wear": torch.zeros(3, 3), "pressure": pressure},
        active_mask=torch.tensor([True, True, True]),
        device=torch.device("cpu"),
        world_rngs=None,
    ).values
    expected = pressure if condition is None else (pressure > 0.5).float()
    assert torch.equal(updated["wear"], expected.unsqueeze(1).expand(3, 3))


def test_an_affordance_rule_reading_an_agent_value_still_refuses() -> None:
    """A per-agent read feeding affordance state is a separate authoring call (agents per
    world > 1 would make it a reduction); the shape proof keeps refusing it."""
    from townlet.vfs.transition_graph import TransitionPhaseGraph

    with pytest.raises(VTCWriteRefusalError, match="agent-shaped"):
        compile_vtc_transition_rules_with_phase_graph([_wear_rule("bar.energy")], _RULE_TARGETS, TransitionPhaseGraph.default())


# --- occupancy claims ------------------------------------------------------------------------


def test_a_failed_claim_is_still_an_attempt_and_moves_nothing() -> None:
    sleep = _affordance_action(
        action_id=20,
        name="SLEEP",
        source_affordance="bed",
        writes=[_write(variable_id="occupied_by", expression="agent_id", composition="claim_if_free")],
    )
    program = compile_vtc_affordance_occupancy(
        [sleep], {"occupied_by": VTCWriteTarget(VariableScope.AFFORDANCE, "scalar", meter=False, expression=None)}, affordance_ids=["bed"]
    )
    held = torch.tensor([[0.0], [1.0]])
    result = program.apply(
        actions=torch.tensor([20, 0]),
        vfs_state={"occupied_by": held.clone()},
        bars_state={},
        active_mask=torch.tensor([True, True]),
        device=torch.device("cpu"),
        world_rngs=None,
    )
    assert result.attempted_targets == frozenset({"occupied_by"})
    assert torch.equal(result.values["occupied_by"], held)


# --- registry, persistence and effects -------------------------------------------------------


def _registry(lifetime: str = "persistent") -> VariableRegistry:
    wear = VariableDef(
        id="wear", scope="affordance", type="scalar", lifetime=lifetime, readable_by=["engine"], writable_by=["engine"], default=0.0
    )
    return VariableRegistry(variables=[wear], num_agents=3, num_affordances=2, device=torch.device("cpu"))


def test_persistent_affordance_state_round_trips_every_worlds_rows() -> None:
    source = _registry()
    rows = torch.tensor([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    source.set_engine_value("wear", rows)
    state = source.persistent_state()
    assert torch.equal(state["wear"], rows)

    target = _registry()
    target.restore_persistent_state(state)
    assert torch.equal(target.get("wear", reader="engine"), rows)
    with pytest.raises(RuntimeError, match="shape"):
        target.validate_persistent_state({"wear": rows[0]})


def test_an_effect_bound_to_a_world_reads_and_writes_only_its_worlds_affordance_rows() -> None:
    registry = _registry(lifetime="episode")
    registry.set_engine_value("wear", torch.tensor([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]))
    bound = ExecutionContext(bars={"energy": torch.ones(3)}, vfs_registry=registry, target_index=1)

    assert torch.equal(bound.get_path("wear"), torch.tensor([3.0, 4.0]))
    bound.set_path("wear", torch.tensor([9.0, 9.0]))
    assert torch.equal(registry.get("wear", reader="engine"), torch.tensor([[1.0, 2.0], [9.0, 9.0], [5.0, 6.0]]))
