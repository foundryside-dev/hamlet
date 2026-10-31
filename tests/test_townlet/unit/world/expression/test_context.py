"""Tests for the expression execution context: one reference grammar (VFS round-2 S5)."""

import pytest
import torch

from townlet.world.expression.context import ExecutionContext


def _ctx(**extra: object) -> ExecutionContext:
    return ExecutionContext(
        bars={"energy": torch.tensor([0.5, 0.8])},
        vfs={"is_night": torch.tensor([True, False]), "tick": torch.tensor([3.0, 4.0])},
        temporal={"time_of_day": torch.tensor(6.0)},
        **extra,  # type: ignore[arg-type]
    )


def test_a_meter_is_bar_dot_name():
    assert torch.equal(_ctx().get("bar.energy"), torch.tensor([0.5, 0.8]))


def test_a_variable_is_its_bare_id():
    assert torch.equal(_ctx().get("is_night"), torch.tensor([True, False]))


def test_item_state_reads_the_bound_item():
    ctx = _ctx(item_state={"durability": torch.tensor(7.0)})
    assert ctx.get("item.durability").item() == 7.0


def test_item_state_without_a_bound_item_raises():
    with pytest.raises(KeyError, match="bound to no item"):
        _ctx().get("item.durability")


def test_the_engine_temporal_namespace_serves_generated_programs():
    assert _ctx().get("temporal.time_of_day").item() == 6.0


@pytest.mark.parametrize(
    "path",
    ["vfs.is_night", "self.vfs.is_night", "target.vfs.is_night", "global.vfs.is_night", "target.bar.energy", "energy", "friend.vfs.energy"],
)
def test_every_other_spelling_raises(path: str):
    with pytest.raises(KeyError):
        _ctx().get(path)
