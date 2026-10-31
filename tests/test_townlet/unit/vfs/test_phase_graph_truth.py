"""The transition phase graph is the executed schedule (WP1: V1, V6, V14).

Converted from review-2026-10-24/vfs probe6, probe1 section D and probe4 section B.
Every phase the graph admits must either apply a write scheduled there or refuse it at
compile — no phase may compile green and then do nothing, or compile green and crash.
"""

from __future__ import annotations

import dataclasses
import inspect
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
from townlet.vfs.schema_hashes import canonical_transition_graph_schema, compute_transition_graph_hash
from townlet.vfs.transition_graph import DEFAULT_TRANSITION_PHASES, TransitionPhaseGraph
from townlet.vfs.transition_schedule import VTCTransitionSchedule

WITNESS = Path(__file__).resolve().parents[4] / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"
GRAPH = TransitionPhaseGraph.default()
ACTION_PHASES = frozenset(GRAPH.action_phases)


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


def _env(universe: CompiledUniverse) -> VectorizedHamletEnv:
    env = VectorizedHamletEnv.from_universe(universe, level_name=LEVEL, num_agents=2, device="cpu")
    env.reset()
    return env


def _step(env: VectorizedHamletEnv, action_name: str) -> None:
    index = next(i for i, action in enumerate(env.action_space.actions) if action.name == action_name)
    env.step(torch.full((env.num_agents,), index, dtype=torch.long))


def _read(env: VectorizedHamletEnv, variable_id: str) -> list[float]:
    return env.vfs_registry.get(variable_id, reader="engine").tolist()


def _action_write_pack(tmp_path: Path, phase: str) -> Path:
    pack = _pack(tmp_path, f"action_{phase}")

    def edit(payload: dict[str, Any]) -> None:
        advance = next(a for a in payload["actions"]["custom_actions"] if a["name"] == "ADVANCE")
        advance["writes"] = [
            {
                "variable_id": "public_state",
                "expression": "1.0",
                "condition": None,
                "composition": "additive_delta",
                "phase": phase,
                "priority": 0,
                "clamp": None,
                "telemetry_label": "phase_probe",
            }
        ]

    _edit_yaml(pack / "actions.yaml", edit)
    return pack


def _residue_rule_pack(tmp_path: Path, phase: str, *, variable_id: str = "public_state") -> Path:
    pack = _pack(tmp_path, f"residue_{phase}")
    rule = {
        "id": "inc",
        "phase": phase,
        "condition": None,
        "writes": [
            {
                "variable_id": variable_id,
                "expression": f"{variable_id} + 1.0",
                "composition": "overwrite",
                "condition": None,
                "clamp": None,
                "effect": None,
            }
        ],
    }
    (pack / "transition_rules.yaml").write_text(yaml.safe_dump({"version": "1.0", "transition_rules": [rule]}, sort_keys=False))
    return pack


def test_step_executes_every_graph_phase_once_in_graph_order(tmp_path: Path) -> None:
    env = _env(_compile(_pack(tmp_path, "witness")))
    requested: list[str] = []
    run_phases = env.vtc_transition_runner.run_phases

    def recording(phases: Any, context: Any) -> Any:
        requested.extend(phases)
        return run_phases(phases, context)

    env.vtc_transition_runner.run_phases = recording  # type: ignore[method-assign]
    _step(env, "ADVANCE")

    assert tuple(requested) == GRAPH.ordered_phases


@pytest.mark.parametrize("phase", DEFAULT_TRANSITION_PHASES)
def test_action_write_applies_or_refuses_at_compile(tmp_path: Path, phase: str) -> None:
    pack = _action_write_pack(tmp_path, phase)
    if phase not in ACTION_PHASES:
        with pytest.raises(CompilationError) as refusal:
            _compile(pack)
        message = str(refusal.value)
        assert f"phase '{phase}'" in message
        assert "runs without the tick's actions" in message
        assert f"{pack / 'actions.yaml'}:" in message  # file:line origin
        return

    env = _env(_compile(pack))
    _step(env, "ADVANCE")
    _step(env, "ADVANCE")
    assert _read(env, "public_state") == [2.0, 2.0]


@pytest.mark.parametrize("phase", DEFAULT_TRANSITION_PHASES)
def test_transition_rule_applies_at_every_phase(tmp_path: Path, phase: str) -> None:
    env = _env(_compile(_residue_rule_pack(tmp_path, phase)))
    _step(env, "WAIT")
    _step(env, "WAIT")
    assert _read(env, "public_state") == [2.0, 2.0]


@pytest.mark.parametrize("phase", ["apply_modulations", "compute_rewards", "emit_observation_features", "emit_telemetry"])
def test_deleted_phantom_phases_refuse_with_origin(tmp_path: Path, phase: str) -> None:
    action_pack = _action_write_pack(tmp_path, phase)
    with pytest.raises(CompilationError, match=f"phase '{phase}', which is not a transition phase") as action_refusal:
        _compile(action_pack)
    assert f"{action_pack / 'actions.yaml'}:" in str(action_refusal.value)

    rule_pack = _residue_rule_pack(tmp_path, phase)
    with pytest.raises(CompilationError, match=f"phase '{phase}', which is not a transition phase") as rule_refusal:
        _compile(rule_pack)
    assert f"{rule_pack / 'transition_rules.yaml'}:" in str(rule_refusal.value)


def test_transition_graph_hash_carries_no_reward_program(tmp_path: Path) -> None:
    level = _compile(_pack(tmp_path, "witness")).get_level(LEVEL)
    schedule = level.transition_schedule

    assert "reward_component_program" not in {field.name for field in dataclasses.fields(VTCTransitionSchedule)}
    assert "reward_component_program" not in inspect.signature(compute_transition_graph_hash).parameters

    payload = canonical_transition_graph_schema(
        schedule.phase_graph,
        schedule.action_write_program,
        affordance_gate_program=schedule.affordance_gate_program,
        interaction_progress_program=schedule.interaction_progress_program,
        terminal_condition_program=schedule.terminal_condition_program,
        threshold_cascade_program=schedule.threshold_cascade_program,
        modulation_program=schedule.modulation_program,
        passive_depletion_program=schedule.passive_depletion_program,
        transition_rule_program=schedule.transition_rule_program,
        bounds_clamp_program=schedule.bounds_clamp_program,
    )
    assert payload["phase_graph"]["phases"] == list(DEFAULT_TRANSITION_PHASES)
    assert not [rule for rule in payload["rules"] if str(rule.get("kind", "")).startswith("reward")]
    assert {rule["phase"] for rule in payload["rules"]} <= set(DEFAULT_TRANSITION_PHASES)
    assert level.transition_graph_hash == compute_transition_graph_hash(
        schedule.phase_graph,
        schedule.action_write_program,
        affordance_gate_program=schedule.affordance_gate_program,
        interaction_progress_program=schedule.interaction_progress_program,
        terminal_condition_program=schedule.terminal_condition_program,
        threshold_cascade_program=schedule.threshold_cascade_program,
        modulation_program=schedule.modulation_program,
        passive_depletion_program=schedule.passive_depletion_program,
        transition_rule_program=schedule.transition_rule_program,
        bounds_clamp_program=schedule.bounds_clamp_program,
    )


def test_expressions_observe_transition_rule_writes_in_the_same_tick(tmp_path: Path) -> None:
    """V14 (probe2 F mas_control): profile evaluation runs after the residue phase."""
    pack = _residue_rule_pack(tmp_path, "apply_social_residue_effects", variable_id="gcount")

    def edit(payload: dict[str, Any]) -> None:
        base = {
            "scope": "global",
            "type": "scalar",
            "lifetime": "episode",
            "semantic_type": "custom",
            "readable_by": ["engine", "agent"],
            "writable_by": ["engine"],
            "exposed_to": [],
        }
        payload["variables"]["declarations"] += [
            {"id": "gcount", **base, "initial_value": 0.0},
            {"id": "gtwice", **base, "initial_value": 0.0, "expression": "gcount * 2.0"},
        ]

    _edit_yaml(pack / "variables.yaml", edit)
    env = _env(_compile(pack))
    for tick in range(1, 4):
        _step(env, "WAIT")
        assert env.vfs_registry.get("gcount", reader="engine").tolist() == [float(tick)] * env.num_agents
        assert env.vfs_registry.get("gtwice", reader="engine").tolist() == [2.0 * tick] * env.num_agents
