"""Policy preflight must not execute collection selection or change command order."""

from types import SimpleNamespace

import pytest
import torch

from townlet.effects.compiler import CommandCompiler
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType
from townlet.vfs.profiles import CompiledItemProfile, CompiledVariable
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef


def _random_loop(body: list[CommandNode]) -> CommandNode:
    return CommandNode(type=CommandType.FOR_EACH, collection_expr="uniform(0.0, 2.0)", iterator="agent", body=body)


def _energy_write() -> CommandNode:
    return CommandNode(type=CommandType.MODIFY, path="target.bar.energy", value_expr="9.0")


def test_stochastic_loop_selects_once_and_reuses_the_exact_context() -> None:
    command = CommandCompiler({"target.bar.energy": "float"}).compile_command(_random_loop([_energy_write()]))
    executor = CommandExecutor()
    torch.manual_seed(1)
    selected = int((torch.rand(()) * 2).item())
    expected_rng = torch.get_rng_state().clone()
    expected = torch.full((2,), 3.0)
    expected[selected] = 9.0
    torch.manual_seed(1)
    context = ExecutionContext(bars={"energy": torch.full((2,), 3.0)})
    executor.execute(command, context)
    assert torch.equal(context.bars["energy"], expected)
    assert torch.equal(torch.get_rng_state(), expected_rng)

    # A later invocation resolves again; no plan may persist on the executor.
    selected_next = int((torch.rand(()) * 2).item())
    next_rng = torch.get_rng_state().clone()
    expected[selected_next] = 9.0
    torch.set_rng_state(expected_rng)
    executor.execute(command, context)
    assert torch.equal(context.bars["energy"], expected)
    assert torch.equal(torch.get_rng_state(), next_rng)


def test_loop_nested_under_compounds_evaluates_collection_once() -> None:
    command = CommandCompiler({"target.bar.energy": "float"}).compile_command(
        CommandNode(
            type=CommandType.PARALLEL,
            parallel_commands=[
                CommandNode(type=CommandType.IF, condition_expr="1 > 0", then_commands=[_random_loop([_energy_write()])], else_commands=[])
            ],
        )
    )
    torch.manual_seed(1)
    target = int((torch.rand(()) * 2).item())
    expected_rng = torch.get_rng_state().clone()
    expected = torch.full((2,), 3.0)
    expected[target] = 9.0
    torch.manual_seed(1)
    context = ExecutionContext(bars={"energy": torch.full((2,), 3.0)})
    CommandExecutor().execute(command, context)
    assert torch.equal(context.bars["energy"], expected)
    assert torch.equal(torch.get_rng_state(), expected_rng)


@pytest.mark.parametrize("kind", ["if", "switch"])
def test_unselected_branch_does_not_evaluate_stochastic_loop(kind: str) -> None:
    loop = _random_loop([_energy_write()])
    if kind == "if":
        command = CommandNode(type=CommandType.IF, condition_expr="0 > 1", then_commands=[loop], else_commands=[])
    else:
        command = CommandNode(type=CommandType.SWITCH, switch_expr="0", cases=[("1", [loop])], default_commands=[])
    command = CommandCompiler({"target.bar.energy": "float"}).compile_command(command)
    torch.manual_seed(1)
    before_rng = torch.get_rng_state().clone()
    context = ExecutionContext(bars={"energy": torch.full((2,), 3.0)})
    CommandExecutor().execute(command, context)
    assert torch.equal(context.bars["energy"], torch.full((2,), 3.0))
    assert torch.equal(torch.get_rng_state(), before_rng)


def test_loop_selection_sees_earlier_compound_sibling_write() -> None:
    registry = VariableRegistry(
        [
            VariableDef(
                id="selector",
                scope="global",
                type="scalar",
                lifetime="episode",
                default=0.0,
                readable_by=["engine"],
                writable_by=["engine"],
            )
        ],
        2,
        torch.device("cpu"),
    )
    command = CommandCompiler({"vfs.selector": "float", "target.bar.energy": "float"}).compile_command(
        CommandNode(
            type=CommandType.PARALLEL,
            parallel_commands=[
                CommandNode(type=CommandType.MODIFY, path="vfs.selector", value_expr="1.0"),
                CommandNode(type=CommandType.FOR_EACH, collection_expr="vfs.selector", iterator="agent", body=[_energy_write()]),
            ],
        )
    )
    context = ExecutionContext(vfs_registry=registry, bars={"energy": torch.full((2,), 3.0)})
    CommandExecutor().execute(command, context)
    assert registry.get("selector", reader="engine").item() == 1.0
    assert torch.equal(context.bars["energy"], torch.tensor([3.0, 9.0]))


def test_denied_stochastic_loop_body_precedes_compound_mutation_and_rng() -> None:
    registry = VariableRegistry(
        [VariableDef(id="constant", scope="agent", type="scalar", lifetime="episode", default=2.0, readable_by=["engine"], writable_by=[])],
        2,
        torch.device("cpu"),
    )
    command = CommandCompiler({"bar.energy": "float", "target.vfs.constant": "float"}).compile_command(
        CommandNode(
            type=CommandType.PARALLEL,
            parallel_commands=[
                CommandNode(type=CommandType.MODIFY, path="bar.energy", value_expr="9.0"),
                _random_loop([CommandNode(type=CommandType.MODIFY, path="target.vfs.constant", value_expr="2.0")]),
            ],
        )
    )
    torch.manual_seed(1)
    before_rng = torch.get_rng_state().clone()
    context = ExecutionContext(vfs_registry=registry, bars={"energy": torch.full((2,), 3.0)})
    with pytest.raises(PermissionError, match="constant"):
        CommandExecutor().execute(command, context)
    assert torch.equal(context.bars["energy"], torch.full((2,), 3.0))
    assert torch.equal(registry.get("constant", reader="engine"), torch.full((2,), 2.0))
    assert torch.equal(torch.get_rng_state(), before_rng)


def test_inventory_profile_denial_precedes_first_selected_item_mutation() -> None:
    profiles = {}
    for profile, writers in [("allowed", ("engine",)), ("constant", ())]:
        profiles[profile] = CompiledItemProfile(
            profile_name=profile,
            variables=[
                CompiledVariable(
                    name="charge",
                    type="float",
                    exposed_to=(),
                    lifetime="episode",
                    readable_by=("engine",),
                    writable_by=writers,
                    initial_value=2.0,
                )
            ],
        )
    registry = VariableRegistry([], 2, torch.device("cpu"), max_items=2, item_profiles=profiles)
    for row, profile in enumerate(profiles):
        registry._initialize_item_row(profile, row)
        registry.register_item_instance(row, profile)
    context = ExecutionContext(vfs_registry=registry, bars={"energy": torch.full((2,), 3.0)}, self_index=0)
    context.inventory = SimpleNamespace(
        slots=torch.tensor([[0, 1], [-1, -1]]), items={0: SimpleNamespace(vfs_index=0), 1: SimpleNamespace(vfs_index=1)}
    )
    command = CommandCompiler({"target.vfs.charge": "float"}).compile_command(
        CommandNode(
            type=CommandType.FOR_EACH,
            collection="inventory_items",
            iterator="item",
            body=[CommandNode(type=CommandType.MODIFY, path="target.vfs.charge", value_expr="9.0")],
        )
    )
    assert registry.item_vfs is not None
    before = registry.item_vfs.clone()
    with pytest.raises(PermissionError, match="constant"):
        CommandExecutor().execute(command, context)
    assert torch.equal(registry.item_vfs, before)
