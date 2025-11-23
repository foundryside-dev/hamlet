"""Tests for VFS expression evaluator."""

import pytest
import torch

from townlet.vfs.evaluator import EvaluationMode, VFSEvaluator
from townlet.vfs.profiles import CompiledGlobalProfile, CompiledVariable
from townlet.world.expression import ExpressionParser


def test_vfs_evaluator_evaluates_expressions_in_topo_order():
    """VFS evaluator should evaluate variables in dependency order."""
    # Setup: Create profile with dependencies (b depends on a)
    parser = ExpressionParser()

    variables = [
        CompiledVariable(
            name="a",
            type="int",
            ast=None,
            initial_value=5,
            result_type="int",
            exposed_to=("agent",),
            semantic_type="custom",
        ),
        CompiledVariable(
            name="b",
            type="int",
            ast=parser.parse("a + 10"),  # Depends on "a"
            initial_value=None,
            result_type="int",
            exposed_to=("agent",),
            semantic_type="custom",
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
    evaluator = VFSEvaluator(mode=EvaluationMode.EAGER)
    result = evaluator.evaluate_global_profile(
        profile=profile,
        bars=bars,
        vfs_state=vfs_state,
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
            name="observed",
            type="int",
            ast=parser.parse("1 + 1"),
            initial_value=None,
            result_type="int",
            exposed_to=("agent",),
            semantic_type="custom",
        ),
        CompiledVariable(
            name="unobserved",
            type="int",
            ast=parser.parse("2 + 2"),
            initial_value=None,
            result_type="int",
            exposed_to=("agent",),
            semantic_type="custom",
        ),
    ]

    profile = CompiledGlobalProfile(
        variables=variables,
        dependencies={"observed": tuple(), "unobserved": tuple()},
    )

    # Exercise: Evaluate with mark-and-sweep (only "observed")
    evaluator = VFSEvaluator(mode=EvaluationMode.MARK_AND_SWEEP)
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
            name="a",
            type="float",
            ast=parser.parse("bar.energy + 1"),
            initial_value=None,
            result_type="float",
            exposed_to=("agent",),
            semantic_type="custom",
        ),
        CompiledVariable(
            name="b",
            type="float",
            ast=parser.parse("a * 2"),
            initial_value=None,
            result_type="float",
            exposed_to=("agent",),
            semantic_type="custom",
        ),
    ]

    profile = CompiledGlobalProfile(
        variables=variables,
        dependencies={"a": tuple(), "b": ("a",)},
    )

    bars = {"energy": torch.tensor(3.0)}
    vfs_state = {"a": torch.tensor(100.0)}  # Stale value should be ignored

    evaluator = VFSEvaluator(mode=EvaluationMode.MARK_AND_SWEEP)
    result = evaluator.evaluate_global_profile(
        profile=profile,
        bars=bars,
        vfs_state=vfs_state,
        marks={"b"},  # Only "b" is marked, but "a" should be recomputed
        device=torch.device("cpu"),
    )

    assert result["a"].item() == pytest.approx(4.0)  # bar.energy + 1
    assert result["b"].item() == pytest.approx(8.0)  # (bar.energy + 1) * 2


def test_vfs_evaluator_eager_mode_evaluates_all_vars():
    """Eager mode should evaluate all variables regardless of marks."""
    # Setup: Same as mark-and-sweep test
    parser = ExpressionParser()

    variables = [
        CompiledVariable(
            name="var1",
            type="int",
            ast=parser.parse("1"),
            initial_value=None,
            result_type="int",
            exposed_to=("agent",),
            semantic_type="custom",
        ),
        CompiledVariable(
            name="var2",
            type="int",
            ast=parser.parse("2"),
            initial_value=None,
            result_type="int",
            exposed_to=("agent",),
            semantic_type="custom",
        ),
    ]

    profile = CompiledGlobalProfile(
        variables=variables,
        dependencies={"var1": tuple(), "var2": tuple()},
    )

    # Exercise: Evaluate with eager mode
    evaluator = VFSEvaluator(mode=EvaluationMode.EAGER)
    result = evaluator.evaluate_global_profile(
        profile=profile,
        bars={},
        vfs_state={},
        marks=set(),  # Empty marks, but eager should evaluate all
        device=torch.device("cpu"),
    )

    # Verify: Both variables evaluated
    assert "var1" in result
    assert "var2" in result
