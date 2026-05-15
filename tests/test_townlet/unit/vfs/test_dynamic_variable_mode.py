"""Tests for gated runtime VFS variable mutations."""

import pytest
import torch

from townlet.vfs import VariableRegistry
from townlet.vfs.schema import VariableDef


def _agent_scalar(variable_id: str, *, observable: bool = False) -> VariableDef:
    return VariableDef(
        id=variable_id,
        scope="agent",
        type="scalar",
        lifetime="episode",
        readable_by=["agent", "engine"],
        writable_by=["engine"],
        default=0.25,
        observable=observable,
    )


def test_dynamic_variable_mutations_are_disabled_by_default() -> None:
    registry = VariableRegistry(
        variables=[],
        num_agents=2,
        device=torch.device("cpu"),
    )

    with pytest.raises(ValueError, match="dynamic_variable_mode=True"):
        registry.add_variable(_agent_scalar("injury"), network_shape_effect="shape_stable_internal")

    with pytest.raises(ValueError, match="dynamic_variable_mode=True"):
        registry.remove_variable("injury", network_shape_effect="shape_stable_internal")


def test_dynamic_mode_adds_internal_variable_and_records_schema_break_metadata() -> None:
    registry = VariableRegistry(
        variables=[],
        num_agents=3,
        device=torch.device("cpu"),
        dynamic_variable_mode=True,
    )

    registry.add_variable(_agent_scalar("injury"), network_shape_effect="shape_stable_internal")

    assert "injury" in registry.variables
    assert torch.equal(registry.get("injury", reader="engine"), torch.full((3,), 0.25))
    assert registry.variable_schema_generation == 1
    assert len(registry.dynamic_variable_mutations) == 1
    mutation = registry.dynamic_variable_mutations[0]
    assert mutation.operation == "add"
    assert mutation.variable_id == "injury"
    assert mutation.network_shape_effect == "shape_stable_internal"
    assert mutation.shape == (3,)
    assert len(mutation.variable_schema_hash) == 64

    registry.set("injury", torch.tensor([0.5, 0.6, 0.7]), writer="engine")
    registry.reset_episode_scoped()

    assert torch.equal(registry.get("injury", reader="engine"), torch.full((3,), 0.25))


def test_dynamic_mode_requires_schema_change_ack_for_observable_variables() -> None:
    registry = VariableRegistry(
        variables=[],
        num_agents=2,
        device=torch.device("cpu"),
        dynamic_variable_mode=True,
    )

    with pytest.raises(ValueError, match="observation_schema_changed"):
        registry.add_variable(_agent_scalar("rumour", observable=True), network_shape_effect="shape_stable_internal")

    registry.add_variable(_agent_scalar("rumour", observable=True), network_shape_effect="observation_schema_changed")

    assert "rumour" in registry.variables
    assert registry.dynamic_variable_mutations[-1].network_shape_effect == "observation_schema_changed"


def test_dynamic_mode_removes_variables_and_rejects_implicit_observation_shape_changes() -> None:
    registry = VariableRegistry(
        variables=[_agent_scalar("rumour", observable=True), _agent_scalar("injury")],
        num_agents=2,
        device=torch.device("cpu"),
        dynamic_variable_mode=True,
    )

    with pytest.raises(ValueError, match="observation_schema_changed"):
        registry.remove_variable("rumour", network_shape_effect="shape_stable_internal")

    registry.remove_variable("rumour", network_shape_effect="observation_schema_changed")
    registry.remove_variable("injury", network_shape_effect="shape_stable_internal")

    assert "rumour" not in registry.variables
    assert "injury" not in registry.variables
    with pytest.raises(KeyError, match="rumour"):
        registry.get("rumour", reader="engine")
    assert registry.variable_schema_generation == 2
    assert [mutation.operation for mutation in registry.dynamic_variable_mutations] == ["remove", "remove"]


def test_dynamic_mode_rejects_unknown_network_shape_effects() -> None:
    registry = VariableRegistry(
        variables=[],
        num_agents=2,
        device=torch.device("cpu"),
        dynamic_variable_mode=True,
    )

    with pytest.raises(ValueError, match="network_shape_effect"):
        registry.add_variable(_agent_scalar("injury"), network_shape_effect="maybe")  # type: ignore[arg-type]
