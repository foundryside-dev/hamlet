"""Tests for VFS expression evaluator."""

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
        ),
        CompiledVariable(
            name="b",
            type="int",
            ast=parser.parse("a + 10"),  # Depends on "a"
            initial_value=None,
            result_type="int",
        ),
    ]

    profile = CompiledGlobalProfile(variables=variables)

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


def test_vfs_evaluator_mark_and_sweep_only_evaluates_marked_vars():
    """Mark-and-sweep mode should only evaluate observed variables."""
    # Setup: 3 variables, only 1 marked for observation
    parser = ExpressionParser()

    variables = [
        CompiledVariable(name="observed", type="int", ast=parser.parse("1 + 1"), initial_value=None, result_type="int"),
        CompiledVariable(name="unobserved", type="int", ast=parser.parse("2 + 2"), initial_value=None, result_type="int"),
    ]

    profile = CompiledGlobalProfile(variables=variables)

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


def test_vfs_evaluator_eager_mode_evaluates_all_vars():
    """Eager mode should evaluate all variables regardless of marks."""
    # Setup: Same as mark-and-sweep test
    parser = ExpressionParser()

    variables = [
        CompiledVariable(name="var1", type="int", ast=parser.parse("1"), initial_value=None, result_type="int"),
        CompiledVariable(name="var2", type="int", ast=parser.parse("2"), initial_value=None, result_type="int"),
    ]

    profile = CompiledGlobalProfile(variables=variables)

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
