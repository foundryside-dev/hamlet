"""A variable id equal to a meter name refuses at the symbol table (VFS WP4: V5).

Converted from review-2026-10-24/vfs probe4 section A and probe5. Meter bars and
registry variables share one runtime state namespace: VTC programs merge
``bars_state`` into ``vfs_state`` by bare name, a VFS expression ``energy`` reads the
variable while a VTC expression ``energy`` reads the bar. Before WP4 the collision
compiled green and was caught only inside ``VTCActionWriteProgram.apply`` — a crash at
the first step when any action write existed, and silent ambiguity otherwise. The
compiler's Stage 4 symbol table now refuses it, citing the variable's ``variables.yaml``
origin and the meter's ``environment.yaml`` origin.
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
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationError
from townlet.universe.stages import CompilationStage

WITNESS = Path(__file__).resolve().parents[4] / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"
METER = "energy"


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


def _declaration(variable_id: str, scope: str = "agent", **extra: Any) -> dict[str, Any]:
    declaration: dict[str, Any] = {
        "id": variable_id,
        "scope": scope,
        "type": "scalar",
        "lifetime": "episode",
        "semantic_type": "custom",
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "exposed_to": [],
        "initial_value": 0.25,
    }
    declaration.update(extra)
    return declaration


def _write(variable_id: str, expression: str, *, composition: str = "additive_delta") -> dict[str, Any]:
    return {
        "variable_id": variable_id,
        "expression": expression,
        "condition": None,
        "composition": composition,
        "phase": "apply_completion_bonuses",
        "priority": 0,
        "clamp": None,
        "telemetry_label": f"w_{variable_id}",
    }


def _declare(pack: Path, *declarations: dict[str, Any]) -> None:
    _edit_yaml(pack / "variables.yaml", lambda payload: payload["variables"]["declarations"].extend(declarations))


def _set_advance_writes(pack: Path, writes: list[dict[str, Any]]) -> None:
    def edit(payload: dict[str, Any]) -> None:
        advance = next(a for a in payload["actions"]["custom_actions"] if a["name"] == "ADVANCE")
        advance["writes"] = writes

    _edit_yaml(pack / "actions.yaml", edit)


def _line_of(path: Path, needle: str) -> int:
    return next(number for number, line in enumerate(path.read_text().splitlines(), start=1) if needle in line)


def _assert_refused_with_both_origins(pack: Path, refusal: CompilationError, *, scope: str) -> None:
    assert CompilationStage.SYMBOLS.label in str(refusal)
    (issue,) = refusal.issues
    assert issue.code == ErrorCode.SYMBOL_METER_COLLISION
    assert f"Variable '{METER}' ({scope}) collides with the meter '{METER}'" in issue.message

    variables_yaml = pack / "variables.yaml"
    assert issue.location == f"{variables_yaml}:{_line_of(variables_yaml, f'id: {METER}')}"

    environment_yaml = pack / "environment.yaml"
    assert f"declared at {environment_yaml}:{_line_of(environment_yaml, f'name: {METER}')}" in issue.message


# --- probe4 A: the collision refuses at compile, with or without an action write ---


def test_variable_named_like_a_meter_with_an_action_write_refuses_at_symbol_table(tmp_path: Path) -> None:
    """probe4 A: used to compile, then crash at the first ``env.step`` inside VTC apply."""
    pack = _pack(tmp_path, "name_collide")
    _declare(pack, _declaration(METER))
    _set_advance_writes(pack, [_write(METER, "1.0")])

    with pytest.raises(CompilationError) as refusal:
        _compile(pack)
    _assert_refused_with_both_origins(pack, refusal.value, scope="agent")


def test_variable_named_like_a_meter_read_by_an_expression_refuses_at_symbol_table(tmp_path: Path) -> None:
    """probe4 A (expression-only): ``e2: energy * 2.0`` used to read the variable, not the bar."""
    pack = _pack(tmp_path, "name_collide_expr")
    _declare(pack, _declaration(METER), _declaration("e2", expression=f"{METER} * 2.0"))

    with pytest.raises(CompilationError) as refusal:
        _compile(pack)
    _assert_refused_with_both_origins(pack, refusal.value, scope="agent")


# --- probe5: no action writes at all used to be silently ambiguous ---


def test_variable_named_like_a_meter_with_no_action_writes_refuses_at_symbol_table(tmp_path: Path) -> None:
    """probe5: with ADVANCE's writes removed the pack compiled and stepped, two ``energy`` namespaces live."""
    pack = _pack(tmp_path, "collide_silent")
    _declare(pack, _declaration(METER), _declaration("e2", expression=f"{METER} * 2.0"))
    _set_advance_writes(pack, [])

    with pytest.raises(CompilationError) as refusal:
        _compile(pack)
    _assert_refused_with_both_origins(pack, refusal.value, scope="agent")


def test_action_write_expression_naming_the_colliding_id_refuses_at_symbol_table(tmp_path: Path) -> None:
    """probe5: ``public_state := energy`` cannot be resolved while both an ``energy`` bar and variable exist."""
    pack = _pack(tmp_path, "collide_expr_vtc")
    _declare(pack, _declaration(METER))
    _set_advance_writes(pack, [_write("public_state", METER, composition="overwrite")])

    with pytest.raises(CompilationError) as refusal:
        _compile(pack)
    _assert_refused_with_both_origins(pack, refusal.value, scope="agent")


def test_global_variable_named_like_a_meter_refuses_too(tmp_path: Path) -> None:
    """Every non-item scope enters the merged namespace, not only ``agent``."""
    pack = _pack(tmp_path, "collide_global")
    _declare(pack, _declaration(METER, scope="global", readable_by=["engine"]))

    with pytest.raises(CompilationError) as refusal:
        _compile(pack)
    _assert_refused_with_both_origins(pack, refusal.value, scope="global")


# --- namespace boundaries the rule must not over-refuse ---


def test_bare_meter_name_in_a_vtc_expression_still_resolves_to_the_bar(tmp_path: Path) -> None:
    """probe5 control: without a colliding variable, ``public_state := energy`` reads the meter."""
    pack = _pack(tmp_path, "bare_meter_vtc")
    _set_advance_writes(pack, [_write("public_state", METER, composition="overwrite")])

    universe = _compile(pack)
    env = VectorizedHamletEnv.from_universe(universe, level_name=LEVEL, num_agents=2, device="cpu")
    env.reset()
    advance = next(i for i, action in enumerate(env.action_space.actions) if action.name == "ADVANCE")
    env.step(torch.full((2,), advance, dtype=torch.long))

    # The write phase (apply_completion_bonuses) precedes passive depletion in the
    # same tick, so the copied value is the bar's initial 1.0 (bars.yaml), not the
    # post-depletion 0.99 and not the variable's own initial.
    assert env.vfs_registry.get("public_state", reader="engine").tolist() == [1.0, 1.0]
    assert env.meters[:, env.meter_name_to_index[METER]].tolist() == pytest.approx([0.99, 0.99])


def test_item_variable_named_like_a_meter_is_a_separate_namespace(tmp_path: Path) -> None:
    """Item variables are profile-qualified and live in item storage; they never meet the bars.

    Uses ``trial_k_cold`` because the witness pack declares no item profile.
    """
    source = WITNESS.parent / "trial_k_cold"
    pack = tmp_path / "item_scope_meter_name"
    shutil.copytree(source, pack, ignore=shutil.ignore_patterns(".compiled"))
    _declare(
        pack,
        _declaration(
            METER,
            scope="item",
            profile="garment_stats",
            readable_by=["engine", "agent"],
            initial_value=0.6,
        ),
    )

    UniverseCompiler().compile(pack, primary_level="L0_cold", use_cache=False)
