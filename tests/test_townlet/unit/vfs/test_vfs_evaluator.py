"""Tests for VFS expression evaluator."""

import pytest
import torch

from townlet.vfs.evaluator import VFSEvaluator
from townlet.vfs.profiles import CompiledGlobalProfile, CompiledVariable
from townlet.world.expression import ExpressionParser


def test_vfs_evaluator_evaluates_expressions_in_topo_order():
    """VFS evaluator should evaluate variables in dependency order."""
    # Setup: Create profile with dependencies (b depends on a)
    parser = ExpressionParser()

    variables = [
        CompiledVariable(
            readable_by=("engine", "agent"),
            writable_by=("engine",),
            name="a",
            lifetime="persistent",
            type="float",
            ast=None,
            initial_value=5,
            result_type="int",
            exposed_to=("agent",),
        ),
        CompiledVariable(
            readable_by=("engine", "agent"),
            writable_by=("engine",),
            name="b",
            lifetime="persistent",
            type="float",
            ast=parser.parse("a + 10"),  # Depends on "a"
            initial_value=None,
            result_type="int",
            exposed_to=("agent",),
        ),
    ]

    profile = CompiledGlobalProfile(
        variables=variables,
        dependencies={"a": tuple(), "b": ("a",)},
    )

    # Create context with initial values
    bars = {"energy": torch.tensor([1.0])}
    vfs_state = {"a": torch.tensor([5])}  # Initial value for "a"

    # Exercise: Evaluate profile
    evaluator = VFSEvaluator(history_spec=None)
    result = evaluator.evaluate_global_profile(
        profile=profile,
        bars=bars,
        vfs_state=vfs_state,
        marks={"b"},
        device=torch.device("cpu"),
    )

    # Verify: "b" should be evaluated to a + 10 = 15
    assert result["a"].item() == 5
    assert result["b"].item() == 15


def test_vfs_evaluator_mark_and_sweep_evaluates_marks_only_when_independent():
    """Mark-and-sweep should evaluate marks (and no extras) when there are no dependencies."""
    # Setup: 2 independent variables, only 1 marked for observation
    parser = ExpressionParser()

    variables = [
        CompiledVariable(
            readable_by=("engine", "agent"),
            writable_by=("engine",),
            name="observed",
            lifetime="persistent",
            type="float",
            ast=parser.parse("1 + 1"),
            initial_value=None,
            result_type="int",
            exposed_to=("agent",),
        ),
        CompiledVariable(
            readable_by=("engine", "agent"),
            writable_by=("engine",),
            name="unobserved",
            lifetime="persistent",
            type="float",
            ast=parser.parse("2 + 2"),
            initial_value=None,
            result_type="int",
            exposed_to=("agent",),
        ),
    ]

    profile = CompiledGlobalProfile(
        variables=variables,
        dependencies={"observed": tuple(), "unobserved": tuple()},
    )

    # Exercise: Evaluate with mark-and-sweep (only "observed")
    evaluator = VFSEvaluator(history_spec=None)
    result = evaluator.evaluate_global_profile(
        profile=profile,
        bars={},
        vfs_state={},
        marks={"observed"},  # Only this variable marked
        device=torch.device("cpu"),
    )

    # Verify: Only "observed" is evaluated
    assert "observed" in result
    assert "unobserved" not in result


def test_vfs_evaluator_mark_and_sweep_recomputes_dependencies():
    """Mark-and-sweep should re-evaluate dependencies of marked variables."""
    parser = ExpressionParser()

    variables = [
        CompiledVariable(
            readable_by=("engine", "agent"),
            writable_by=("engine",),
            name="a",
            lifetime="episode",
            type="float",
            ast=parser.parse("bar.energy + 1"),
            initial_value=None,
            result_type="float",
            exposed_to=("agent",),
        ),
        CompiledVariable(
            readable_by=("engine", "agent"),
            writable_by=("engine",),
            name="b",
            lifetime="episode",
            type="float",
            ast=parser.parse("a * 2"),
            initial_value=None,
            result_type="float",
            exposed_to=("agent",),
        ),
    ]

    profile = CompiledGlobalProfile(
        variables=variables,
        dependencies={"a": tuple(), "b": ("a",)},
    )

    bars = {"energy": torch.tensor(3.0)}
    vfs_state = {"a": torch.tensor(100.0)}  # Stale value should be ignored

    evaluator = VFSEvaluator(history_spec=None)
    result = evaluator.evaluate_global_profile(
        profile=profile,
        bars=bars,
        vfs_state=vfs_state,
        marks={"b"},  # Only "b" is marked, but "a" should be recomputed
        device=torch.device("cpu"),
    )

    assert result["a"].item() == pytest.approx(4.0)  # bar.energy + 1
    assert result["b"].item() == pytest.approx(8.0)  # (bar.energy + 1) * 2


def test_vfs_evaluator_mark_and_sweep_rejects_unknown_marks():
    """Misspelled marks should fail loudly instead of evaluating nothing."""
    profile = CompiledGlobalProfile(
        variables=[
            CompiledVariable(
                readable_by=("engine", "agent"),
                writable_by=("engine",),
                name="observed",
                lifetime="persistent",
                type="float",
                ast=None,
                initial_value=1,
                result_type="int",
                exposed_to=("agent",),
            )
        ],
        dependencies={"observed": tuple()},
    )

    evaluator = VFSEvaluator(history_spec=None)

    with pytest.raises(KeyError, match="typo"):
        evaluator.evaluate_global_profile(
            profile=profile,
            bars={},
            vfs_state={},
            marks={"typo"},
            device=torch.device("cpu"),
        )
