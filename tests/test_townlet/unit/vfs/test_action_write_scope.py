"""Action writes are scope-typed; transition rules respect the tick's active agents (VFS WP2: V2, V9).

Converted from review-2026-10-24/vfs probe1 section F and probe2 section G. An action
write applies to the acting agent's row, so it must name a target whose declared scope
has one row per agent. Before WP2 the runtime decided "this target has an agent axis"
by ``target.shape[0] == num_agents``: a global tensor whose extent coincided with
``num_agents`` was silently masked per agent, any other extent crashed at step, and
whether a pack ran depended on a training hyperparameter. The target's declared scope
now decides, at compile, with the write's ``actions.yaml`` ``file:line``.

Also pins the adjacent defect: a transition rule scheduled at ``apply_passive_depletion``
or ``apply_threshold_cascades`` used to run with an all-ones active mask and write rows
for agents already done.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
import torch
import yaml

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError

WITNESS = Path(__file__).resolve().parents[4] / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"


def _pack(tmp_path: Path, name: str) -> Path:
    dest = tmp_path / name
    shutil.copytree(WITNESS, dest, ignore=shutil.ignore_patterns(".compiled"))
    return dest


def _edit_yaml(path: Path, edit: Any) -> None:
    payload = yaml.safe_load(path.read_text())
    edit(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def _compile(pack: Path) -> CompiledUniverse:
    return UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def _env(universe: CompiledUniverse, num_agents: int) -> VectorizedHamletEnv:
    env = VectorizedHamletEnv.from_universe(universe, level_name=LEVEL, num_agents=num_agents, device="cpu")
    env.reset()
    return env


def _action_index(env: VectorizedHamletEnv, name: str) -> int:
    return next(i for i, action in enumerate(env.action_space.actions) if action.name == name)


def _read(env: VectorizedHamletEnv, variable_id: str) -> list[Any]:
    return env.vfs_registry.get(variable_id, reader="engine").tolist()


def _declaration(variable_id: str, scope: str, **extra: Any) -> dict[str, Any]:
    declaration: dict[str, Any] = {
        "id": variable_id,
        "scope": scope,
        "type": "scalar",
        "lifetime": "episode",
        "semantic_type": "custom",
        "readable_by": ["engine"],
        "writable_by": ["engine"],
        "exposed_to": [],
        "initial_value": 0.0,
    }
    declaration.update(extra)
    return declaration


def _write(variable_id: str, *, composition: str = "additive_delta", phase: str = "apply_action_effects") -> dict[str, Any]:
    return {
        "variable_id": variable_id,
        "expression": "1.0",
        "condition": None,
        "composition": composition,
        "phase": phase,
        "priority": 0,
        "clamp": None,
        "telemetry_label": f"w_{variable_id}",
    }


def _scoped_write_pack(
    tmp_path: Path,
    name: str,
    declaration: dict[str, Any],
    *,
    write: dict[str, Any] | None = None,
) -> Path:
    pack = _pack(tmp_path, name)

    def edit_variables(payload: dict[str, Any]) -> None:
        payload["variables"]["declarations"].append(declaration)

    def edit_actions(payload: dict[str, Any]) -> None:
        advance = next(a for a in payload["actions"]["custom_actions"] if a["name"] == "ADVANCE")
        advance["writes"] = [write if write is not None else _write(declaration["id"])]

    _edit_yaml(pack / "variables.yaml", edit_variables)
    _edit_yaml(pack / "actions.yaml", edit_actions)
    return pack


NON_AGENT_TARGETS = {
    # probe1 F: the global tensor whose extent coincided with num_agents=2.
    "global_tensor": (_declaration("gvec", "global", type="tensor1d", shape=[2], initial_value=[0.0, 0.0]), "global"),
    # probe1 F: compiled green, crashed at step.
    "global_scalar": (_declaration("gscalar", "global"), "global"),
    # An affordance variable outside the occupancy-claim form has no row per agent either.
    "affordance": (_declaration("wear", "affordance"), "affordance"),
}


@pytest.mark.parametrize("case", sorted(NON_AGENT_TARGETS))
def test_non_agent_action_write_target_refuses_at_compile(tmp_path: Path, case: str) -> None:
    declaration, scope = NON_AGENT_TARGETS[case]
    pack = _scoped_write_pack(tmp_path, case, declaration)

    with pytest.raises(CompilationError) as refusal:
        _compile(pack)

    message = str(refusal.value)
    assert f"variable '{declaration['id']}', declared scope '{scope}'" in message
    assert "ADVANCE" in message
    assert f"{pack / 'actions.yaml'}:" in message  # file:line origin


@pytest.mark.parametrize("scope", ["zone", "group"])
def test_zone_and_group_scopes_are_deleted(tmp_path: Path, scope: str) -> None:
    """probe1 F / probe2 G wrote zone and group rows by agent index; both scopes are gone."""
    pack = _scoped_write_pack(tmp_path, scope, _declaration(f"{scope}_heat", scope))

    with pytest.raises(CompilationError, match="scope"):
        _compile(pack)


def test_agent_axis_action_write_runs_identically_at_any_num_agents(tmp_path: Path) -> None:
    """num_agents never decides whether a pack runs: the same compiled universe steps at 2 and 3."""
    universe = _compile(_scoped_write_pack(tmp_path, "agent", _declaration("own_heat", "agent")))

    for num_agents in (2, 3):
        env = _env(universe, num_agents)
        actions = [_action_index(env, "ADVANCE")] + [_action_index(env, "WAIT")] * (num_agents - 1)
        env.step(torch.tensor(actions))
        assert _read(env, "own_heat") == [1.0] + [0.0] * (num_agents - 1)


def test_affordance_occupancy_claim_is_the_one_affordance_write(tmp_path: Path) -> None:
    """A source-affordance claim at the occupancy phase is admitted against affordance scope."""
    pack = _pack(tmp_path, "claim")

    def edit_variables(payload: dict[str, Any]) -> None:
        payload["variables"]["declarations"].append(_declaration("occupied_by", "affordance", initial_value=-1.0))

    def edit_actions(payload: dict[str, Any]) -> None:
        payload["actions"]["custom_actions"].append(
            {
                "name": "CLAIM",
                "description": "Claim the bed if it is free",
                "enabled_by_default": True,
                "source_affordance": "SLEEP",
                "writes": [
                    dict(
                        _write("occupied_by", composition="claim_if_free", phase="resolve_affordance_access_and_occupancy"),
                        expression="agent_id",
                    )
                ],
            }
        )

    _edit_yaml(pack / "variables.yaml", edit_variables)
    _edit_yaml(pack / "actions.yaml", edit_actions)

    level = _compile(pack).get_level(LEVEL)
    (claim,) = (write for write in level.transition_schedule.action_write_program.writes if write.action_name == "CLAIM")
    assert claim.target_scope == "affordance"
    assert claim.affordance_index == 0


def _residue_pack(tmp_path: Path, phase: str) -> Path:
    pack = _pack(tmp_path, f"residue_{phase}")
    rule = {
        "id": "inc",
        "kind": "institutional_rule",
        "phase": phase,
        "reads": ["public_state"],
        "condition": None,
        "writes": [
            {
                "variable_id": "public_state",
                "expression": "public_state + 1.0",
                "composition": "overwrite",
                "condition": None,
                "clamp": None,
                "effect": None,
            }
        ],
    }
    (pack / "transition_rules.yaml").write_text(yaml.safe_dump({"version": "1.0", "social_residue": [rule]}, sort_keys=False))
    return pack


@pytest.mark.parametrize("phase", ["apply_passive_depletion", "apply_threshold_cascades"])
def test_transition_rule_skips_done_agents_at_depletion_and_cascade_phases(tmp_path: Path, phase: str) -> None:
    env = _env(_compile(_residue_pack(tmp_path, phase)), num_agents=2)
    env.dones[1] = True
    meters_before = env.meters.clone()

    env.step(torch.full((2,), _action_index(env, "WAIT"), dtype=torch.long))

    assert _read(env, "public_state") == [1.0, 0.0]
    assert torch.equal(env.meters[1], meters_before[1])  # a done agent's bars do not deplete either
    assert not torch.equal(env.meters[0], meters_before[0])
