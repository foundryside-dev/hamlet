"""An agent_ref holds its own world's agent or null (owner ruling S1).

Row w of every registry scope is world w's, and world w has one agent (agent w). An
`agent_ref` naming any other agent would be a cross-world read (`x.ref.bar.y` gathered
another world's row). So:

- every write is checked: an agent_ref in world w must be w or -1 (an engine defect
  otherwise), in every scope with registry storage, in the item arena, and on restore;
- the constructs that could only produce a cross-world reference are refused at compile:
  a constant initial value (it is every world's) and a constant write expression.

The same rule holds for `item_ref` (an item row belongs to one world).

Under S1 an agent_ref is therefore a nullable self-pointer; its one in-tree use is the
affordance occupancy claimant (`claim_if_free` with `agent_id`).
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest
import torch
import yaml

from tests.test_townlet.unit.vfs.test_vtc_action_writes import _action, _write
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef, VariableScope
from townlet.vfs.vtc import VTCWriteRefusalError, VTCWriteTarget, compile_vtc_action_writes

WITNESS = Path(__file__).resolve().parents[4] / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"


def _ref(var_id: str, scope: str, var_type: str = "agent_ref", lifetime: str = "episode") -> VariableDef:
    return VariableDef(
        id=var_id, scope=scope, type=var_type, lifetime=lifetime, readable_by=["engine"], writable_by=["engine"], default=None
    )


def _registry(*variables: VariableDef) -> VariableRegistry:
    return VariableRegistry(variables=list(variables), num_agents=3, num_affordances=2, items_per_world=0, device=torch.device("cpu"))


@pytest.mark.parametrize(
    ("scope", "good", "bad", "world"),
    [
        ("agent", [0, -1, 2], [0, 2, 2], 1),
        ("global", [-1, 1, 2], [-1, 1, 0], 2),
        ("affordance", [[0, -1], [1, 1], [-1, 2]], [[0, -1], [1, 0], [-1, 2]], 1),
    ],
)
def test_an_agent_ref_names_its_own_worlds_agent_or_null(scope: str, good: list, bad: list, world: int) -> None:
    registry = _registry(_ref("buddy", scope))
    registry.set("buddy", torch.tensor(good), writer="engine")
    assert registry.get("buddy", reader="engine").tolist() == good

    with pytest.raises(RuntimeError, match=rf"Engine defect: agent_ref 'buddy' in world {world} names agent"):
        registry.set_engine_value("buddy", torch.tensor(bad))
    assert registry.get("buddy", reader="engine").tolist() == good  # a refused write applies nothing


def test_a_restored_snapshot_with_a_cross_world_ref_is_refused_whole() -> None:
    source = _registry(_ref("buddy", "agent", lifetime="persistent"))
    state = source.persistent_state()
    state["buddy"] = torch.tensor([0, 0, 2])
    target = _registry(_ref("buddy", "agent", lifetime="persistent"))
    with pytest.raises(RuntimeError, match="agent_ref 'buddy' in world 1 names agent 0"):
        target.restore_persistent_state(state)
    assert target.get("buddy", reader="engine").tolist() == [-1, -1, -1]


def test_an_item_profile_agent_ref_names_its_items_world() -> None:
    class _Var:
        name, type, initial_value = "owner", "agent_ref", None
        readable_by, writable_by, exposed_to = ("engine",), ("engine",), ()

    class _Profile:
        variables = [_Var()]

    registry = VariableRegistry(
        variables=[], num_agents=2, items_per_world=2, item_profiles={"tool": _Profile()}, device=torch.device("cpu")
    )
    registry.register_item_instance(3, "tool")  # row 3 is world 1's second slot
    registry.write_item("tool", "owner", 1, 3, writer="engine")
    registry.write_item("tool", "owner", -1, 3, writer="engine")
    with pytest.raises(RuntimeError, match=r"agent_ref 'tool.owner' on item row 3 \(world 1\) names agent 0"):
        registry.write_item("tool", "owner", 0, 3, writer="engine")


# --- compile-time refusals --------------------------------------------------------------------


def _pack_with(tmp_path: Path, declaration: dict) -> Path:
    pack = tmp_path / "pack"
    shutil.copytree(WITNESS, pack, ignore=shutil.ignore_patterns(".compiled"))
    path = pack / "variables.yaml"
    payload = yaml.safe_load(path.read_text())
    payload["variables"]["declarations"].append(declaration)
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return pack


@pytest.mark.parametrize("var_type", ["agent_ref", "item_ref"])
@pytest.mark.parametrize("initial", [0, 2])
def test_a_constant_reference_initial_value_is_refused_at_its_declaration(tmp_path: Path, var_type: str, initial: int) -> None:
    pack = _pack_with(
        tmp_path,
        {
            "id": "buddy",
            "scope": "agent",
            "type": var_type,
            "lifetime": "episode",
            "semantic_type": "custom",
            "readable_by": ["engine"],
            "writable_by": ["engine"],
            "exposed_to": [],
            "initial_value": initial,
        },
    )
    with pytest.raises(CompilationError) as refusal:
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    message = str(refusal.value)
    assert f"{var_type} initial_value {initial} names one fixed batch row" in message
    assert re.search(r"variables\.yaml:\d+", message), message


@pytest.mark.parametrize("initial", [None, -1])
def test_a_null_reference_initial_value_compiles(tmp_path: Path, initial: int | None) -> None:
    pack = _pack_with(
        tmp_path,
        {
            "id": "buddy",
            "scope": "agent",
            "type": "agent_ref",
            "lifetime": "episode",
            "semantic_type": "custom",
            "readable_by": ["engine"],
            "writable_by": ["engine"],
            "exposed_to": [],
            "initial_value": initial,
        },
    )
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    env = universe.create_environment(num_agents=3, level_name=LEVEL, device="cpu")
    env.reset()
    assert env.vfs_registry.get("buddy", reader="engine").tolist() == [-1, -1, -1]


_REF_TARGETS = {"buddy": VTCWriteTarget(VariableScope.AGENT, "agent_ref", meter=False, expression=None)}


def _ref_write(expression: str):
    return _action(
        action_id=3,
        name="BIND",
        writes=[_write(variable_id="buddy", expression=expression, condition=None, composition="overwrite", clamp=None)],
    )


@pytest.mark.parametrize("expression", ["0", "2", "1 + 1", "max(1, 2)"])
def test_a_constant_agent_ref_write_is_refused_at_compile(expression: str) -> None:
    with pytest.raises(VTCWriteRefusalError, match="assigns the constant .* to agent_ref 'buddy'"):
        compile_vtc_action_writes([_ref_write(expression)], _REF_TARGETS)


def test_agent_id_and_null_are_the_agent_ref_writes() -> None:
    program = compile_vtc_action_writes([_ref_write("agent_id")], _REF_TARGETS)
    values = program.apply(
        actions=torch.tensor([3, 0, 3]),
        vfs_state={"buddy": torch.full((3,), -1)},
        bars_state={},
        active_mask=torch.ones(3, dtype=torch.bool),
        device=torch.device("cpu"),
    ).values
    assert values["buddy"].tolist() == [0, -1, 2]
    compile_vtc_action_writes([_ref_write("-1")], _REF_TARGETS)
