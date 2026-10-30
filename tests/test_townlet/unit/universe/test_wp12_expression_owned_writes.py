"""Authored writes to an expression-owned variable refuse at compile (VFS WP12: F11).

Converted from review-2026-10-24/vfs_round2 r11_lifetime_expression.py case (b). A
variable that carries an ``expression`` is recomputed by profile evaluation after every
transition, so an action write, a transition-rule write or a command-pipeline write
(effect, affordance interaction, item hook) to it compiled green and was silently
discarded: ``after ADVANCE: derived=[2.0] (action wrote 100, rule wrote derived+50;
both discarded)``. Each now refuses with ``[UAC-STATIC-WRITE]`` at the write site's
``file:line``, naming the expression variable's declaration ``file:line`` too.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError

WITNESS = Path(__file__).resolve().parents[4] / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"
#: Declared in the witness pack with ``expression: public_state * immutable_scale``.
OWNED = "scaled_public"


def _pack(tmp_path: Path) -> Path:
    pack = tmp_path / "pack"
    shutil.copytree(WITNESS, pack, ignore=shutil.ignore_patterns(".compiled"))
    return pack


def _edit_yaml(path: Path, edit: Any) -> None:
    payload = yaml.safe_load(path.read_text())
    edit(payload)
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def _declaration_line(pack: Path) -> int:
    lines = (pack / "variables.yaml").read_text().splitlines()
    return next(number for number, line in enumerate(lines, start=1) if line.strip() == f"- id: {OWNED}")


def _refusal(pack: Path) -> str:
    with pytest.raises(CompilationError) as excinfo:
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    return str(excinfo.value)


def _assert_cites_both_origins(message: str, pack: Path, write_file: str) -> None:
    assert "[UAC-STATIC-WRITE]" in message
    assert f"writes variable '{OWNED}', which is computed by its expression" in message
    assert re.search(rf"{re.escape(write_file)}:\d+", message), message
    assert f"(declared at {pack / 'variables.yaml'}:{_declaration_line(pack)})" in message


def test_action_write_to_an_expression_variable_refuses_at_compile(tmp_path: Path) -> None:
    pack = _pack(tmp_path)

    def edit_actions(payload: dict[str, Any]) -> None:
        (advance,) = (action for action in payload["actions"]["custom_actions"] if action["name"] == "ADVANCE")
        advance["writes"].append(
            {
                "variable_id": OWNED,
                "expression": "100.0",
                "condition": None,
                "composition": "overwrite",
                "phase": "apply_completion_bonuses",
                "priority": 0,
                "clamp": None,
                "telemetry_label": "overwrite_derived",
            }
        )

    _edit_yaml(pack / "actions.yaml", edit_actions)
    _assert_cites_both_origins(_refusal(pack), pack, "actions.yaml")


def test_transition_rule_write_to_an_expression_variable_refuses_at_compile(tmp_path: Path) -> None:
    pack = _pack(tmp_path)
    rule = {
        "id": "boost",
        "kind": "social_residue",
        "phase": "apply_social_residue_effects",
        "reads": [OWNED],
        "condition": None,
        "writes": [
            {
                "variable_id": OWNED,
                "expression": f"{OWNED} + 50.0",
                "composition": "overwrite",
                "condition": None,
                "clamp": None,
                "effect": None,
            }
        ],
    }
    (pack / "transition_rules.yaml").write_text(yaml.safe_dump({"version": "1.0", "social_residue": [rule]}, sort_keys=False))
    _assert_cites_both_origins(_refusal(pack), pack, "transition_rules.yaml")


def test_effect_write_to_an_expression_variable_refuses_at_compile(tmp_path: Path) -> None:
    pack = _pack(tmp_path)
    effect = {
        "id": "inflate",
        "scope": "agent",
        "duration": 3,
        "reapply_policy": "stack",
        "observable": False,
        "on_spawn": [{"modify": f"target.vfs.{OWNED}", "value": "100.0"}],
        "on_tick": [],
        "on_despawn": [],
        "on_interrupt": [],
    }
    (pack / "effects.yaml").write_text(
        yaml.safe_dump(
            {
                "version": "1.0",
                "effect_definitions": [effect],
                "max_active_effects": {"global": 0, "agent": 1, "item": 0, "affordance": 0},
            },
            sort_keys=False,
        )
    )
    _assert_cites_both_origins(_refusal(pack), pack, "effects.yaml")


def test_affordance_interaction_write_to_an_expression_variable_refuses_at_compile(tmp_path: Path) -> None:
    pack = _pack(tmp_path)
    affordances = pack / "levels" / LEVEL / "affordances.yaml"

    def edit_affordances(payload: dict[str, Any]) -> None:
        payload["affordances"]["affordances"][0]["interactions"]["on_start"].append({"modify": f"target.vfs.{OWNED}", "value": "100.0"})

    _edit_yaml(affordances, edit_affordances)
    _assert_cites_both_origins(_refusal(pack), pack, "affordances.yaml")


def test_writing_an_input_of_the_expression_still_compiles(tmp_path: Path) -> None:
    """The witness pack's own ADVANCE writes `public_state`, an input of `scaled_public`: admitted."""
    universe = UniverseCompiler().compile(_pack(tmp_path), primary_level=LEVEL, use_cache=False)
    writes = universe.get_level(LEVEL).transition_schedule.action_write_program.writes
    assert {write.variable_id for write in writes} == {"public_state", "hidden_score"}
