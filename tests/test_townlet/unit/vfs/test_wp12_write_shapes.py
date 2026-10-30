"""Write and rule expressions are shape-proved against the target scope (VFS WP12: F6, F7).

Converted from review-2026-10-24/vfs_round2 r4_write_expression_shape.py and
r6_rules_pair_global.py. Action-write and transition-rule expressions were type-checked
but not shape-proved: a ``pair`` (N x N) or ``message`` (N x slots) read into an
agent-row action write compiled and raised at the first step; an agent-shaped value
into a ``global`` rule target compiled and raised at the first step; and an
agent-shaped value into a ``pair`` target was silently broadcast down the column,
diagonal included (``trust[i, j] += value[j]``). Each now refuses at compile with
``[VTC-WRITE-TYPE]`` and the author's ``file:line``.
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
from townlet.vfs import compile_vtc_action_writes, compile_vtc_social_residue_rules
from townlet.vfs.schema import VariableScope
from townlet.vfs.vtc import VTCWriteRefusalError, VTCWriteTarget

WITNESS = Path(__file__).resolve().parents[4] / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"


# --- pack helpers -----------------------------------------------------------------


def _edit_yaml(path: Path, edit: Any) -> None:
    payload = yaml.safe_load(path.read_text())
    edit(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


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


def _pack(
    tmp_path: Path,
    name: str,
    *,
    declarations: list[dict[str, Any]],
    extents: dict[str, int] | None = None,
    action_write: dict[str, Any] | None = None,
    rules: list[dict[str, Any]] | None = None,
) -> Path:
    pack = tmp_path / name
    shutil.copytree(WITNESS, pack, ignore=shutil.ignore_patterns(".compiled"))

    def edit_variables(payload: dict[str, Any]) -> None:
        payload["variables"]["declarations"].extend(declarations)
        payload["variables"]["extents"].update(extents or {})

    _edit_yaml(pack / "variables.yaml", edit_variables)
    if action_write is not None:

        def edit_actions(payload: dict[str, Any]) -> None:
            (advance,) = (action for action in payload["actions"]["custom_actions"] if action["name"] == "ADVANCE")
            advance["writes"] = [action_write]

        _edit_yaml(pack / "actions.yaml", edit_actions)
    if rules is not None:
        (pack / "transition_rules.yaml").write_text(yaml.safe_dump({"version": "1.0", "social_residue": rules}, sort_keys=False))
    return pack


def _compile(pack: Path) -> CompiledUniverse:
    return UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def _action_write(variable_id: str, expression: str, *, condition: str | None = None) -> dict[str, Any]:
    return {
        "variable_id": variable_id,
        "expression": expression,
        "condition": condition,
        "composition": "additive_delta",
        "phase": "apply_completion_bonuses",
        "priority": 0,
        "clamp": None,
        "telemetry_label": f"w_{variable_id}",
    }


def _rule(rule_id: str, variable_id: str, expression: str, *, condition: str | None = None) -> dict[str, Any]:
    return {
        "id": rule_id,
        "kind": "social_residue",
        "phase": "apply_social_residue_effects",
        "reads": [variable_id],
        "condition": condition,
        "writes": [
            {
                "variable_id": variable_id,
                "expression": expression,
                "composition": "additive_delta",
                "condition": None,
                "clamp": None,
                "effect": None,
            }
        ],
    }


def _refusal(pack: Path) -> str:
    with pytest.raises(CompilationError) as excinfo:
        _compile(pack)
    return str(excinfo.value)


# --- F6: action writes reading non-agent-row state --------------------------------


@pytest.mark.parametrize(
    "declaration,extents",
    [
        (_declaration("trust", "pair", initial_value=0.5), {}),
        (_declaration("inbox", "message", initial_value=1.0), {"num_message_slots": 2}),
    ],
    ids=["pair_read", "message_read"],
)
def test_action_write_reading_a_non_agent_row_refuses_at_compile(tmp_path: Path, declaration, extents) -> None:
    """r4: compiled green, then `produced shape (N, N), expected (N,)` at the first step."""
    pack = _pack(
        tmp_path,
        declaration["id"],
        declarations=[declaration],
        extents=extents,
        action_write=_action_write("public_state", declaration["id"]),
    )
    message = _refusal(pack)
    assert "[VTC-WRITE-TYPE]" in message
    assert "actions.yaml:" in message
    assert f"expression '{declaration['id']}' is {declaration['scope']}-shaped" in message
    assert "declared scope 'agent'" in message


def test_action_write_condition_reading_pair_state_refuses_at_compile(tmp_path: Path) -> None:
    pack = _pack(
        tmp_path,
        "pair_condition",
        declarations=[_declaration("trust", "pair", initial_value=0.5)],
        action_write=_action_write("public_state", "1.0", condition="trust > 0.1"),
    )
    message = _refusal(pack)
    assert "[VTC-WRITE-TYPE]" in message
    assert "condition 'trust > 0.1' is pair-shaped" in message


def test_action_write_reading_agent_rows_and_globals_still_compiles_and_runs(tmp_path: Path) -> None:
    """The proof admits what the runtime always handled: agent rows and scalar globals."""
    pack = _pack(
        tmp_path,
        "agent_ok",
        declarations=[],
        action_write=_action_write("public_state", "hidden_score * immutable_scale", condition="bar.energy >= 0.0"),
    )
    env = VectorizedHamletEnv.from_universe(_compile(pack), level_name=LEVEL, num_agents=2, device="cpu")
    env.reset()
    advance = next(i for i, action in enumerate(env.action_space.actions) if action.name == "ADVANCE")
    env.step(torch.full((2,), advance, dtype=torch.long))
    assert env.vfs_registry.get("public_state", reader="engine").tolist() == [1.0, 1.0]


# --- F6: agent-shaped value into a global rule target -----------------------------


def test_rule_writing_an_agent_value_into_a_global_target_refuses_at_compile(tmp_path: Path) -> None:
    """r6: compiled green, then `produced shape (3,), expected broadcastable to ()` at step."""
    pack = _pack(
        tmp_path,
        "global_agent_value",
        declarations=[_declaration("gsum", "global")],
        rules=[_rule("g", "gsum", "bar.energy")],
    )
    message = _refusal(pack)
    assert "[VTC-WRITE-TYPE]" in message
    assert "transition_rules.yaml:" in message
    assert "expression 'bar.energy' is agent-shaped" in message
    assert "declared scope 'global', which admits scalar-shaped values" in message


def test_rule_with_an_agent_condition_on_a_global_target_refuses_at_compile(tmp_path: Path) -> None:
    pack = _pack(
        tmp_path,
        "global_agent_condition",
        declarations=[_declaration("gsum", "global")],
        rules=[_rule("g", "gsum", "1.0", condition="bar.energy > 0.5")],
    )
    assert "condition 'bar.energy > 0.5' is agent-shaped" in _refusal(pack)


# --- F7: agent-shaped value into a pair target ------------------------------------


@pytest.mark.parametrize("expression", ["bar.energy", "trust * 0.0 + bar.energy"], ids=["bare", "mixed_with_pair"])
def test_rule_writing_an_agent_value_into_a_pair_target_refuses_at_compile(tmp_path: Path, expression: str) -> None:
    """r6: `trust += bar.energy` wrote agent j's energy into every row's column j, diagonal included.

    Mixing the agent value with pair data inside the expression reaches the same column
    broadcast, so it refuses too: the expression language cannot name the axis yet (S7).
    """
    pack = _pack(
        tmp_path,
        "pair_agent_value",
        declarations=[_declaration("trust", "pair")],
        rules=[_rule("t", "trust", expression)],
    )
    message = _refusal(pack)
    assert "[VTC-WRITE-TYPE]" in message
    assert "transition_rules.yaml:" in message
    assert f"expression '{expression}'" in message


def test_bare_agent_condition_on_a_pair_target_refuses_at_compile(tmp_path: Path) -> None:
    pack = _pack(
        tmp_path,
        "pair_agent_condition",
        declarations=[_declaration("trust", "pair")],
        rules=[_rule("t", "trust", "0.1", condition="bar.energy > 0.5")],
    )
    message = _refusal(pack)
    assert "condition 'bar.energy > 0.5' is agent-shaped" in message
    assert "no declared pair axis" in message


def test_pair_condition_gated_by_an_agent_value_compiles_and_indexes_the_second_axis(tmp_path: Path) -> None:
    """The shipped grammar (VFS.md §16): `observer_mask and chosen_action == STEAL`. Inside a pair
    target's condition an agent operand combined with pair data indexes the second axis j."""
    pack = _pack(
        tmp_path,
        "pair_condition_ok",
        declarations=[_declaration("trust", "pair"), _declaration("watching", "pair", type="bool", initial_value=True)],
        rules=[_rule("t", "trust", "0.1", condition="watching and bar.energy > 0.5")],
    )
    env = VectorizedHamletEnv.from_universe(_compile(pack), level_name=LEVEL, num_agents=3, device="cpu")
    env.reset()
    energy = env.meter_name_to_index["energy"]
    env.meters[:, energy] = torch.tensor([0.9, 0.2, 0.9])
    wait = next(i for i, action in enumerate(env.action_space.actions) if action.name == "WAIT")
    env.step(torch.full((3,), wait, dtype=torch.long))
    trust = env.vfs_registry.get("trust", reader="engine")
    assert torch.equal(trust[:, 1], torch.zeros(3))
    assert torch.all(trust[:, 0] > 0) and torch.all(trust[:, 2] > 0)


# --- compiler-level units: admitted shapes per target scope -----------------------


def _target(scope: VariableScope, var_type: str = "scalar", *, meter: bool = False) -> VTCWriteTarget:
    return VTCWriteTarget(scope, var_type, meter=meter)


TARGETS = {
    "energy": _target(VariableScope.AGENT, meter=True),
    "public": _target(VariableScope.AGENT),
    "trust": _target(VariableScope.PAIR),
    "inbox": _target(VariableScope.MESSAGE),
    "pressure": _target(VariableScope.GLOBAL),
    "wear": _target(VariableScope.AFFORDANCE),
}


def _unit_rule(variable_id: str, expression: str, condition: str | None = None) -> dict[str, Any]:
    rule = _rule(f"r_{variable_id}", variable_id, expression, condition=condition)
    return rule


@pytest.mark.parametrize(
    "variable_id,expression",
    [
        ("public", "bar.energy"),
        ("public", "pressure"),
        ("inbox", "bar.energy"),  # an agent value spreads along the message target's agent axis
        ("inbox", "inbox * 0.5"),
        ("trust", "trust * 0.5"),
        ("pressure", "pressure + 1.0"),
        ("wear", "wear * 0.5"),
        ("public", "masked_add(public, 0.5, bar.energy > 0.5)"),
        ("public", "masked_set(public, pressure, bar.energy > 0.5)"),
        ("public", "perlin_noise(bar.energy, pressure)"),
    ],
)
def test_rule_shapes_the_runtime_handles_compile(variable_id: str, expression: str) -> None:
    program = compile_vtc_social_residue_rules([_unit_rule(variable_id, expression)], TARGETS)
    assert len(program.rules) == 1


@pytest.mark.parametrize(
    "variable_id,expression",
    [
        ("public", "trust"),
        ("public", "inbox"),
        ("public", "wear"),
        ("wear", "bar.energy"),
        ("pressure", "wear"),
        ("trust", "inbox"),
        ("inbox", "trust"),
    ],
)
def test_rule_shapes_that_would_fail_or_broadcast_by_coincidence_refuse(variable_id: str, expression: str) -> None:
    with pytest.raises(VTCWriteRefusalError) as excinfo:
        compile_vtc_social_residue_rules([_unit_rule(variable_id, expression)], TARGETS)
    (refusal,) = excinfo.value.refusals
    assert refusal.kind == "type"


def test_mixing_message_and_agent_axes_refuses_even_inside_an_expression() -> None:
    """(N,) + (N, slots) aligns trailing dimensions: agent i's value would land on slot i."""
    with pytest.raises(VTCWriteRefusalError, match="different shapes"):
        compile_vtc_social_residue_rules([_unit_rule("inbox", "inbox + bar.energy")], TARGETS)


class _Action:
    def __init__(self, writes: list[dict[str, Any]]) -> None:
        self.id = 5
        self.name = "ACT"
        self.source_affordance = None
        self.writes = writes


@pytest.mark.parametrize(
    "variable_id,expression,composition,ok",
    [
        ("public", "energy + 1.0", "additive_delta", True),
        ("public", "agent_id", "overwrite", True),
        ("inbox", "inbox * 0.5", "overwrite", True),
        ("inbox", "bar.energy", "append_event", True),
        ("inbox", "bar.energy", "overwrite", False),  # (N,) into [agents, slots] storage: crashed at step
        ("inbox", "inbox", "append_event", False),
        ("public", "trust", "overwrite", False),
        ("public", "wear", "overwrite", False),
    ],
)
def test_action_write_admitted_shapes(variable_id: str, expression: str, composition: str, ok: bool) -> None:
    write = _action_write(variable_id, expression)
    write["composition"] = composition
    write["phase"] = "apply_action_effects"
    actions = [_Action([write])]
    if ok:
        assert len(compile_vtc_action_writes(actions, TARGETS).writes) == 1
    else:
        with pytest.raises(VTCWriteRefusalError) as excinfo:
            compile_vtc_action_writes(actions, TARGETS)
        assert excinfo.value.refusals[0].kind == "type"
