"""VFS expression evaluator with mark-and-sweep support."""

from __future__ import annotations

from enum import Enum

import torch

from townlet.vfs.profiles import CompiledGlobalProfile
from townlet.world.expression.context import ExecutionContext
from townlet.world.expression.evaluator import Evaluator

__all__ = ["VFSEvaluator", "EvaluationMode"]


class EvaluationMode(str, Enum):
    """VFS evaluation mode."""

    MARK_AND_SWEEP = "mark_and_sweep"  # Only evaluate observed variables
    EAGER = "eager"  # Evaluate all variables (debug mode)


class VFSEvaluator:
    """Evaluates VFS expressions using compiled profiles."""

    def __init__(self, mode: EvaluationMode = EvaluationMode.MARK_AND_SWEEP):
        """Initialize VFS evaluator.

        Args:
            mode: Evaluation mode (mark_and_sweep or eager)
        """
        self.mode = mode

    def evaluate_global_profile(
        self,
        profile: CompiledGlobalProfile,
        bars: dict[str, torch.Tensor],
        vfs_state: dict[str, torch.Tensor],
        marks: set[str] | None = None,
        device: torch.device = torch.device("cpu"),
    ) -> dict[str, torch.Tensor]:
        """Evaluate global VFS profile expressions.

        Args:
            profile: Compiled global profile with variables in topo order
            bars: Bar state (e.g., {"energy": tensor([batch])})
            vfs_state: Current VFS state (inputs for expressions)
            marks: Set of variable names to evaluate (for mark-and-sweep)
            device: PyTorch device

        Returns:
            Dict mapping variable names to evaluated tensors
        """
        # Determine which variables to evaluate
        if self.mode == EvaluationMode.MARK_AND_SWEEP:
            if marks is None:
                marks = set()
            # Evaluate marked variables plus their in-profile dependencies
            dependencies = getattr(profile, "dependencies", {}) or {}
            var_names = {var.name for var in profile.variables}

            def add_with_deps(var_name: str, acc: set[str]) -> None:
                """Add variable and its dependencies to evaluation set."""
                if var_name in acc:
                    return
                acc.add(var_name)
                for dep in dependencies.get(var_name, ()):
                    add_with_deps(dep, acc)

            vars_to_eval: set[str] = set()
            for marked in marks:
                # Ignore marks that are not part of this profile
                if marked in dependencies or marked in var_names:
                    add_with_deps(marked, vars_to_eval)
        else:  # EAGER mode
            vars_to_eval = {var.name for var in profile.variables}

        # Build execution context
        context = ExecutionContext(
            bars=bars,
            vfs=vfs_state.copy(),  # Copy so we can update during evaluation
            affordances={},  # TODO: Add affordance support (Task 3)
            temporal={},  # TODO: Add temporal support (Task 3)
            device=device,
        )

        evaluator = Evaluator(context)
        result = {}

        # Evaluate variables in topological order (profile.variables already sorted)
        for var in profile.variables:
            # Skip if not in evaluation set (mark-and-sweep)
            if var.name not in vars_to_eval:
                continue

            # Static initial value (no expression)
            if var.ast is None:
                value = torch.tensor(var.initial_value, device=device)
            else:
                # Evaluate expression using current context
                value = evaluator.evaluate(var.ast)

            # Store result
            result[var.name] = value
            # Update context so later variables can reference this one
            context.vfs[var.name] = value

        return result
