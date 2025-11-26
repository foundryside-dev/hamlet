import torch

from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef, VariableScope


def test_variable_registry_initializes_tensor_defaults():
    var_def = VariableDef(
        id="memory",
        scope=VariableScope.AGENT,
        type="tensor2d",
        shape=[2, 3],
        initial_value_mode="ones",
        lifetime="episode",
        readable_by=["engine"],
        writable_by=["engine"],
        default=None,
    )

    registry = VariableRegistry(
        variables=[var_def],
        num_agents=4,
        device=torch.device("cpu"),
    )

    tensor = registry.get("memory", reader="engine")
    assert tensor.shape == (4, 2, 3)
    assert torch.allclose(tensor, torch.ones((4, 2, 3)))


def test_variable_registry_tensor_guardrail():
    var_def = VariableDef(
        id="huge",
        scope=VariableScope.AGENT,
        type="tensor2d",
        shape=[1024, 1024],
        initial_value_mode="zeros",
        lifetime="episode",
        readable_by=["engine"],
        writable_by=["engine"],
        default=None,
    )

    try:
        VariableRegistry(
            variables=[var_def],
            num_agents=1,
            device=torch.device("cpu"),
        )
    except ValueError as exc:
        assert "exceeds max supported elements" in str(exc)
    else:
        raise AssertionError("Expected guardrail to reject oversized tensor")


def test_variable_registry_tensor_explicit_default_broadcasts_batch():
    var_def = VariableDef(
        id="memory",
        scope=VariableScope.AGENT,
        type="tensor2d",
        shape=[2, 2],
        initial_value_mode="zeros",
        lifetime="episode",
        readable_by=["engine"],
        writable_by=["engine"],
        default=[[1.0, 2.0], [3.0, 4.0]],
    )

    registry = VariableRegistry(
        variables=[var_def],
        num_agents=2,
        device=torch.device("cpu"),
    )

    tensor = registry.get("memory", reader="engine")
    assert tensor.shape == (2, 2, 2)
    expected = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    assert torch.allclose(tensor[0], expected)
    assert torch.allclose(tensor[1], expected)


def test_variable_registry_tensor_explicit_default_broadcasts_multi_agent():
    """Explicit tensor defaults are broadcast even when batch > 2."""
    var_def = VariableDef(
        id="memory",
        scope=VariableScope.AGENT,
        type="tensor2d",
        shape=[2, 2],
        initial_value_mode="zeros",
        lifetime="episode",
        readable_by=["engine"],
        writable_by=["engine"],
        default=[[1.0, 0.0], [0.0, 1.0]],
    )

    registry = VariableRegistry(
        variables=[var_def],
        num_agents=3,
        device=torch.device("cpu"),
    )

    tensor = registry.get("memory", reader="engine")
    assert tensor.shape == (3, 2, 2)
    expected = torch.tensor([[1.0, 0.0], [0.0, 1.0]])
    for i in range(3):
        assert torch.allclose(tensor[i], expected)
