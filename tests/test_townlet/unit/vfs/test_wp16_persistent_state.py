"""WP16 (F13): the registry captures and restores exactly the persistent-lifetime state."""

from __future__ import annotations

import pytest
import torch

from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef


def _var(var_id: str, *, scope: str, lifetime: str, default: object, type_: str = "scalar") -> VariableDef:
    return VariableDef(
        id=var_id,
        scope=scope,
        type=type_,
        lifetime=lifetime,
        readable_by=["engine", "agent"],
        writable_by=["engine"],
        default=default,
    )


def _registry() -> VariableRegistry:
    return VariableRegistry(
        variables=[
            _var("season", scope="global", lifetime="persistent", default=0.0),
            _var("standing", scope="agent", lifetime="persistent", default=0.0),
            _var("opened", scope="agent", lifetime="persistent", default=False, type_="bool"),
            _var("episode_count", scope="global", lifetime="episode", default=0.0),
            _var("tick_flag", scope="agent", lifetime="tick", default=0.0),
        ],
        num_agents=3,
        device=torch.device("cpu"),
    )


def _drive(registry: VariableRegistry) -> None:
    registry.set_engine_value("season", torch.full_like(registry.get("season", reader="engine"), 7.0))
    registry.set_engine_value("standing", torch.tensor([1.0, 2.0, 3.0]))
    registry.set_engine_value("opened", torch.tensor([True, False, True]))
    registry.set_engine_value("episode_count", torch.full_like(registry.get("episode_count", reader="engine"), 4.0))
    registry.set_engine_value("tick_flag", torch.tensor([9.0, 9.0, 9.0]))


def test_snapshot_holds_exactly_the_persistent_lifetime_variables() -> None:
    registry = _registry()
    _drive(registry)
    state = registry.persistent_state()
    assert set(state) == {"season", "standing", "opened"}
    assert torch.equal(state["standing"], torch.tensor([1.0, 2.0, 3.0]))
    assert all(value.device.type == "cpu" for value in state.values())
    # A detached copy: mutating the snapshot never reaches live storage.
    state["standing"].fill_(-1.0)
    assert torch.equal(registry.get("standing", reader="engine"), torch.tensor([1.0, 2.0, 3.0]))


def test_restore_round_trips_into_a_fresh_registry_and_its_scope_arenas() -> None:
    source = _registry()
    _drive(source)
    state = source.persistent_state()

    target = _registry()
    target.restore_persistent_state(state)
    for var_id in ("season", "standing", "opened"):
        restored = target.get(var_id, reader="engine")
        assert torch.equal(restored, source.get(var_id, reader="engine"))
        assert restored.device == target.device
    # Episode and tick lifetimes are not part of the snapshot and are not touched.
    assert float(target.get("episode_count", reader="engine").sum()) == 0.0
    assert float(target.get("tick_flag", reader="engine").sum()) == 0.0
    # Arena-backed storage stays a view: the observation publisher reads the restored value.
    offset, _ = target.scope_arenas["agent"].index["standing"]
    assert torch.equal(target.scope_arenas["agent"].tensor[:, offset], torch.tensor([1.0, 2.0, 3.0]))
    # Persistent state then survives an episode reset, as declared.
    target.reset_episode_scoped()
    assert torch.equal(target.get("standing", reader="engine"), torch.tensor([1.0, 2.0, 3.0]))


def test_a_registry_without_persistent_variables_snapshots_nothing() -> None:
    registry = VariableRegistry(
        variables=[_var("episode_count", scope="global", lifetime="episode", default=0.0)],
        num_agents=2,
        device=torch.device("cpu"),
    )
    assert registry.persistent_state() == {}
    registry.restore_persistent_state({})


def _assert_untouched(registry: VariableRegistry) -> None:
    assert float(registry.get("season", reader="engine").sum()) == 0.0
    assert torch.equal(registry.get("standing", reader="engine"), torch.zeros(3))
    assert not bool(registry.get("opened", reader="engine").any())


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda state: state.pop("opened"), r"missing=\['opened'\]"),
        (lambda state: state.update(episode_count=torch.tensor(4.0)), r"unknown=\['episode_count'\]"),
        (lambda state: state.update(standing=torch.tensor([1.0, 2.0])), r"'standing' has shape \(2,\)"),
        (lambda state: state.update(opened=torch.tensor([1.0, 0.0, 1.0])), r"'opened' has shape \(3,\) dtype torch.float32"),
        (lambda state: state.update(standing=[1.0, 2.0, 3.0]), r"'standing' is list, not a tensor"),
    ],
)
def test_a_mismatched_snapshot_is_an_engine_defect_and_applies_nothing(mutate, message: str) -> None:
    source = _registry()
    _drive(source)
    state = source.persistent_state()
    mutate(state)

    target = _registry()
    with pytest.raises(RuntimeError, match=rf"Engine defect.*{message}"):
        target.restore_persistent_state(state)
    # Validation runs over every entry before the first write: no partial restore.
    _assert_untouched(target)
