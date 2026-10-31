"""Engine writes validate; hashes bind initialization; resets redraw (VFS WP7: V11, V12, V13).

Converted from review-2026-10-24/vfs probe2 D and H, probe4 C and probe1 G.

V11 — ``set_engine_value`` used to ``.to(dtype=expected)`` where ``set`` refused, so a
float batch landed in a bool variable as ``[True, True]``; the VTC programs cast every
expression to the target dtype the same way, so ``additive_delta "1.0"`` on a bool and
``overwrite 0.6`` on an ``agent_ref`` compiled green and mangled at step. Both now share
``set``'s check, and a write whose expression type-checks against a target of another
type is a located compile error (``actions.yaml`` / ``transition_rules.yaml`` ``file:line``).

V12 — ``variable_schema_hash`` ignored ``shape``, ``initial_value_mode``,
``initial_value_params`` and ``initial_value``.

V13 — a random initializer drew once at construction and every reset restored that
draw. A reset now re-runs the declared initializer: literals restore, random modes
redraw from torch's global RNG (the ``seed_all`` stream), reproducible per seed.
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
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef
from townlet.vfs.schema_hashes import compute_variable_schema_hash

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


def _read(env: VectorizedHamletEnv, variable_id: str) -> torch.Tensor:
    return env.vfs_registry.get(variable_id, reader="engine")


def _declaration(variable_id: str, scope: str = "agent", **extra: Any) -> dict[str, Any]:
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


def _write(variable_id: str, expression: str, *, composition: str = "additive_delta", condition: str | None = None) -> dict[str, Any]:
    return {
        "variable_id": variable_id,
        "expression": expression,
        "condition": condition,
        "composition": composition,
        "phase": "apply_completion_bonuses",
        "priority": 0,
        "clamp": None,
        "telemetry_label": f"w_{variable_id}",
    }


def _declare(pack: Path, *declarations: dict[str, Any]) -> None:
    _edit_yaml(pack / "variables.yaml", lambda payload: payload["variables"]["declarations"].extend(declarations))


def _advance_writes(pack: Path, *writes: dict[str, Any]) -> None:
    def edit(payload: dict[str, Any]) -> None:
        advance = next(a for a in payload["actions"]["custom_actions"] if a["name"] == "ADVANCE")
        advance["writes"] = list(writes)

    _edit_yaml(pack / "actions.yaml", edit)


def _transition_rule(pack: Path, write: dict[str, Any]) -> None:
    rule = {
        "id": "typed",
        "phase": "apply_social_residue_effects",
        "condition": None,
        "writes": [{**write, "effect": None}],
    }
    (pack / "transition_rules.yaml").write_text(yaml.safe_dump({"version": "1.0", "transition_rules": [rule]}, sort_keys=False))


def _variable(**fields: Any) -> VariableDef:
    base: dict[str, Any] = dict(scope="global", lifetime="episode", readable_by=["engine"], writable_by=["engine"], default=None)
    return VariableDef(**{**base, **fields})


# --- V11: the registry validates engine writes the way set() does (probe2 D) -------------


def _bool_registry() -> VariableRegistry:
    flag = _variable(id="flag", scope="agent", type="bool", default=False)
    return VariableRegistry(variables=[flag], num_agents=2, device=torch.device("cpu"))


def test_set_engine_value_refuses_dtype_like_set() -> None:
    registry = _bool_registry()
    value = torch.tensor([0.7, 2.5])

    with pytest.raises(ValueError, match="dtype torch.float32, expected torch.bool") as engine_error:
        registry.set_engine_value("flag", value)
    with pytest.raises(ValueError, match="dtype torch.float32, expected torch.bool") as set_error:
        registry.set("flag", value, writer="engine")

    assert str(engine_error.value) == str(set_error.value)
    assert _registry_flag(registry) == [False, False]

    registry.set_engine_value("flag", torch.tensor([True, False]))
    assert _registry_flag(registry) == [True, False]


def _registry_flag(registry: VariableRegistry) -> list[bool]:
    return registry.get("flag", reader="engine").tolist()


# --- V11: a write that type-checks against the wrong declared type refuses at compile -----


TYPE_MISMATCHES = {
    # probe4 C: additive_delta "1.0" on a bool compiled green and stored [True, True].
    "float_delta_into_bool": (_declaration("flag", type="bool", initial_value=False), _write("flag", "1.0"), "declared bool"),
    # probe4 C: overwrite "0.0" on a bool.
    "float_overwrite_into_bool": (
        _declaration("flag", type="bool", initial_value=False),
        _write("flag", "0.0", composition="overwrite"),
        "declared bool",
    ),
    # probe4 C: a reference overwritten with 0.6 stored [0, 0].
    "float_into_agent_ref": (
        _declaration("buddy", type="agent_ref", initial_value=None),
        _write("buddy", "0.6", composition="overwrite"),
        "declared agent_ref",
    ),
    # probe2 D: a bool expression overwriting scalar storage.
    "bool_into_scalar": (_declaration("num"), _write("num", "bar.energy > 0.5", composition="overwrite"), "declared scalar"),
    # A condition is a bool, not a number.
    "numeric_condition": (_declaration("num"), _write("num", "1.0", condition="bar.energy"), "condition 'bar.energy' is float"),
}


@pytest.mark.parametrize("case", sorted(TYPE_MISMATCHES))
def test_action_write_type_mismatch_refuses_at_compile_with_location(tmp_path: Path, case: str) -> None:
    declaration, write, expected = TYPE_MISMATCHES[case]
    pack = _pack(tmp_path, f"action_{case}")
    _declare(pack, declaration)
    _advance_writes(pack, write)

    with pytest.raises(CompilationError, match="VTC-WRITE-TYPE") as error:
        _compile(pack)

    message = str(error.value)
    assert expected in message
    assert "actions.yaml:" in message


@pytest.mark.parametrize("case", ["float_delta_into_bool", "float_into_agent_ref", "bool_into_scalar"])
def test_transition_rule_type_mismatch_refuses_at_compile_with_location(tmp_path: Path, case: str) -> None:
    declaration, write, expected = TYPE_MISMATCHES[case]
    pack = _pack(tmp_path, f"rule_{case}")
    _declare(pack, declaration)
    _transition_rule(pack, write)

    with pytest.raises(CompilationError, match="VTC-WRITE-TYPE") as error:
        _compile(pack)

    message = str(error.value)
    assert expected in message
    assert "transition_rules.yaml:" in message


def test_typed_writes_still_apply(tmp_path: Path) -> None:
    """The same targets accept expressions of their declared type; an int widens into scalar storage."""
    pack = _pack(tmp_path, "typed_ok")
    _declare(pack, _declaration("flag", type="bool", initial_value=False), _declaration("buddy", type="agent_ref", initial_value=None))
    _advance_writes(
        pack,
        _write("flag", "bar.energy > 0.0", composition="overwrite"),
        _write("buddy", "agent_id", composition="overwrite"),
        _write("public_state", "2"),
    )
    env = _env(_compile(pack), num_agents=2)

    env.step(torch.full((2,), _action_index(env, "ADVANCE"), dtype=torch.long))

    assert _read(env, "flag").tolist() == [True, True]
    assert _read(env, "buddy").tolist() == [0, 1]
    assert _read(env, "buddy").dtype == torch.long
    assert _read(env, "public_state").tolist() == [2.0, 2.0]


# --- V12: variable_schema_hash binds shape and initialization (probe2 H) ------------------


UNIFORM_0_1 = {"low": 0.0, "high": 1.0}
UNIFORM_0_2 = {"low": 0.0, "high": 2.0}


def _tensor(**fields: Any) -> VariableDef:
    return _variable(**{"id": "t", "type": "tensor2d", "shape": [2, 2], **fields})


@pytest.mark.parametrize(
    "changed",
    [
        pytest.param(_tensor(shape=[4, 4]), id="shape"),
        pytest.param(_tensor(initial_value_mode="ones"), id="initial_value_mode"),
        pytest.param(_tensor(default=[[1.0, 0.0], [0.0, 1.0]]), id="initial_value"),
        pytest.param(_tensor(initial_value_mode="random_uniform", initial_value_params=UNIFORM_0_2), id="initial_value_params"),
    ],
)
def test_variable_schema_hash_moves_with_shape_and_initialization(changed: VariableDef) -> None:
    baseline = (
        _tensor()
        if changed.initial_value_params is None
        else _tensor(initial_value_mode="random_uniform", initial_value_params=UNIFORM_0_1)
    )
    assert compute_variable_schema_hash([baseline], {}) != compute_variable_schema_hash([changed], {})


# --- V13: a reset re-runs a random initializer from the seeded stream (probe1 G) ----------


def _noise_registry() -> VariableRegistry:
    noise = _variable(id="noise", type="tensor1d", shape=[4], initial_value_mode="random_uniform", initial_value_params=UNIFORM_0_1)
    return VariableRegistry(variables=[noise], num_agents=2, device=torch.device("cpu"))


def _draws(seed: int) -> list[list[list[float]]]:
    torch.manual_seed(seed)
    registry = _noise_registry()
    draws = [registry.get("noise", reader="engine").tolist()]
    for _ in range(2):
        registry.set_engine_value("noise", torch.zeros(2, 4))  # [num_worlds, 4]
        registry.reset_episode_scoped()
        draws.append(registry.get("noise", reader="engine").tolist())
    return draws


def test_random_initializer_redraws_on_every_reset_reproducibly_per_seed() -> None:
    first = _draws(7)
    assert len({tuple(map(tuple, draw)) for draw in first}) == 3, first  # three distinct draws, not one frozen draw
    assert all(world[0] != world[1] for world in first)  # each world draws its own global (S1)
    assert all(0.0 <= value < 1.0 for draw in first for world in draw for value in world)
    assert _draws(7) == first
    assert _draws(8) != first


def test_literal_and_deterministic_initializers_restore_on_reset() -> None:
    literal = _variable(id="score", scope="agent", type="scalar", default=1.5)
    eye = _variable(id="eye", type="tensor2d", shape=[2, 2], initial_value_mode="eye")
    keep = _variable(id="keep", type="scalar", lifetime="persistent", default=0.0)
    registry = VariableRegistry(variables=[literal, eye, keep], num_agents=2, device=torch.device("cpu"))
    registry.set_engine_value("score", torch.tensor([9.0, 9.0]))
    registry.set_engine_value("eye", torch.zeros(2, 2, 2))  # [num_worlds, 2, 2]
    registry.set_engine_value("keep", torch.tensor([4.0, 5.0]))

    registry.reset_episode_scoped()

    assert registry.get("score", reader="engine").tolist() == [1.5, 1.5]
    assert registry.get("eye", reader="engine").tolist() == [[[1.0, 0.0], [0.0, 1.0]]] * 2
    assert registry.get("keep", reader="engine").tolist() == [4.0, 5.0]


def test_env_reset_redraws_a_random_global_tensor(tmp_path: Path) -> None:
    pack = _pack(tmp_path, "random_reset")
    noise = _declaration(
        "noise", "global", type="tensor1d", shape=[4], initial_value_mode="random_uniform", initial_value_params=UNIFORM_0_1
    )
    del noise["initial_value"]
    _declare(pack, noise)

    env = _env(_compile(pack), num_agents=2)
    first = _read(env, "noise").tolist()
    env.reset()
    second = _read(env, "noise").tolist()

    assert first != second
