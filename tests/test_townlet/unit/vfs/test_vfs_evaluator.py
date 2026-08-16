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
        ),
        CompiledVariable(
            name="b",
            type="int",
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
        ),
        CompiledVariable(
            name="unobserved",
            type="int",
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
        ),
        CompiledVariable(
            name="b",
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


def test_vfs_evaluator_mark_and_sweep_requires_explicit_marks():
    """Mark-and-sweep mode must not silently degrade to eager evaluation."""
    profile = CompiledGlobalProfile(
        variables=[
            CompiledVariable(
                name="observed",
                type="int",
                ast=None,
                initial_value=1,
                result_type="int",
                exposed_to=("agent",),
            )
        ],
        dependencies={"observed": tuple()},
    )

    evaluator = VFSEvaluator(mode=EvaluationMode.MARK_AND_SWEEP)

    with pytest.raises(ValueError, match="requires explicit marks"):
        evaluator.evaluate_global_profile(
            profile=profile,
            bars={},
            vfs_state={},
            marks=None,
            device=torch.device("cpu"),
        )


def test_vfs_evaluator_mark_and_sweep_rejects_unknown_marks():
    """Misspelled marks should fail loudly instead of evaluating nothing."""
    profile = CompiledGlobalProfile(
        variables=[
            CompiledVariable(
                name="observed",
                type="int",
                ast=None,
                initial_value=1,
                result_type="int",
                exposed_to=("agent",),
            )
        ],
        dependencies={"observed": tuple()},
    )

    evaluator = VFSEvaluator(mode=EvaluationMode.MARK_AND_SWEEP)

    with pytest.raises(KeyError, match="typo"):
        evaluator.evaluate_global_profile(
            profile=profile,
            bars={},
            vfs_state={},
            marks={"typo"},
            device=torch.device("cpu"),
        )


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
        ),
        CompiledVariable(
            name="var2",
            type="int",
            ast=parser.parse("2"),
            initial_value=None,
            result_type="int",
            exposed_to=("agent",),
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


def test_vfs_evaluator_handles_reference_path_access():
    """Reference paths (vfs.ref.vfs.field) should resolve via context."""
    parser = ExpressionParser()

    variables = [
        CompiledVariable(
            name="ref_target",
            type="float",
            ast=None,
            initial_value=3.0,
            result_type="float",
            exposed_to=("agent",),
        ),
        CompiledVariable(
            name="use_ref",
            type="float",
            ast=parser.parse("vfs.ref.ref_target * 2"),
            initial_value=None,
            result_type="float",
            exposed_to=("agent",),
        ),
    ]

    profile = CompiledGlobalProfile(
        variables=variables,
        dependencies={"ref_target": tuple(), "use_ref": ("ref_target",)},
    )

    bars = {}
    vfs_state = {"ref_target": torch.tensor(4.0)}  # Should be overwritten by initial_value/default

    evaluator = VFSEvaluator(mode=EvaluationMode.EAGER)
    result = evaluator.evaluate_global_profile(
        profile=profile,
        bars=bars,
        vfs_state=vfs_state,
        device=torch.device("cpu"),
    )

    assert result["ref_target"].item() == pytest.approx(3.0)
    assert result["use_ref"].item() == pytest.approx(6.0)


def test_vfs_evaluator_handles_nested_reference_paths():
    """Deep reference chains (vfs.ref.vfs.ref.*) are resolved transitively."""
    parser = ExpressionParser()

    variables = [
        CompiledVariable(
            name="a",
            type="float",
            ast=None,
            initial_value=1.5,
            result_type="float",
            exposed_to=("agent",),
        ),
        CompiledVariable(
            name="b",
            type="float",
            ast=parser.parse("vfs.ref.a + 1.0"),
            initial_value=None,
            result_type="float",
            exposed_to=("agent",),
        ),
        CompiledVariable(
            name="c",
            type="float",
            ast=parser.parse("vfs.ref.b * 2.0"),
            initial_value=None,
            result_type="float",
            exposed_to=("agent",),
        ),
    ]

    profile = CompiledGlobalProfile(
        variables=variables,
        dependencies={"a": tuple(), "b": ("a",), "c": ("b",)},
    )

    evaluator = VFSEvaluator(mode=EvaluationMode.EAGER)
    result = evaluator.evaluate_global_profile(
        profile=profile,
        bars={},
        vfs_state={},
        device=torch.device("cpu"),
    )

    assert result["a"].item() == pytest.approx(1.5)
    assert result["b"].item() == pytest.approx(2.5)
    assert result["c"].item() == pytest.approx(5.0)


def test_vfs_evaluator_threads_affordance_and_temporal_context():
    """Expressions should see real affordance state and temporal values."""
    parser = ExpressionParser()

    variables = [
        CompiledVariable(
            name="can_use_bank_late",
            type="bool",
            ast=parser.parse("affordance.bank.available and temporal.tick > 5"),
            initial_value=None,
            result_type="bool",
            exposed_to=("agent",),
        ),
    ]

    profile = CompiledGlobalProfile(
        variables=variables,
        dependencies={"can_use_bank_late": tuple()},
    )

    evaluator = VFSEvaluator(mode=EvaluationMode.EAGER)
    result = evaluator.evaluate_global_profile(
        profile=profile,
        bars={},
        vfs_state={},
        affordances={"bank": {"available": torch.tensor(True)}},
        temporal={"tick": torch.tensor(6)},
        device=torch.device("cpu"),
    )

    assert torch.equal(result["can_use_bank_late"], torch.tensor(True))
