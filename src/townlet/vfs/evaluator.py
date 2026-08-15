"""VFS expression evaluator with mark-and-sweep support."""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import Any

import torch

from townlet.vfs.profiles import CompiledGlobalProfile
from townlet.world.expression.context import ExecutionContext
from townlet.world.expression.evaluator import Evaluator
from townlet.world.expression.history import TemporalHistory

__all__ = ["VFSEvaluator", "EvaluationMode"]


class EvaluationMode(StrEnum):
    """VFS evaluation mode."""

    MARK_AND_SWEEP = "mark_and_sweep"  # Only evaluate observed variables
    EAGER = "eager"  # Evaluate all variables (debug mode)


class VFSEvaluator:
    """Evaluates VFS expressions using compiled profiles."""

    def __init__(
        self,
        mode: EvaluationMode = EvaluationMode.MARK_AND_SWEEP,
        history_spec: dict[str, int] | None = None,
        debug_logging: bool = False,
    ):
        """Initialize VFS evaluator.

        Args:
            mode: Evaluation mode (mark_and_sweep or eager)
        """
        self.mode = mode
        self._debug_vfs = debug_logging
        self._logger = logging.getLogger("hamlet.vfs")
        self.history_spec = history_spec or {}
        self._history: TemporalHistory | None = TemporalHistory(self.history_spec, torch.device("cpu")) if self.history_spec else None
        self._last_history_step: int | None = None

    def _prepare_history(self, device: torch.device) -> None:
        if self._history is None:
            return
        if self._history.device != device:
            self._history.to(device)

    def _push_history(
        self,
        bars: dict[str, torch.Tensor],
        vfs_values: dict[str, torch.Tensor],
        device: torch.device,
        step: int | None,
    ) -> None:
        if self._history is None:
            return

        if step is not None and self._last_history_step == step:
            return
        if step is None:
            step = -1 if self._last_history_step is None else self._last_history_step + 1

        self._prepare_history(device)

        for key in self.history_spec:
            if key.startswith("bar."):
                bar_name = key.split(".", 1)[1]
                value = bars.get(bar_name)
            elif key.startswith("vfs."):
                var_name = key.split(".", 1)[1]
                value = vfs_values.get(var_name)
            else:
                value = None

            if value is not None:
                self._history.push(key, value)

        self._last_history_step = step

    def reset(self) -> None:
        """Reset temporal history between episodes."""
        if self._history is not None:
            self._history.reset()
        self._last_history_step = None

    def evaluate_global_profile(
        self,
        profile: CompiledGlobalProfile,
        bars: dict[str, torch.Tensor],
        vfs_state: dict[str, torch.Tensor],
        marks: set[str] | None = None,
        device: torch.device = torch.device("cpu"),
        step: int | None = None,
        affordances: dict[str, Any] | None = None,
        temporal: dict[str, torch.Tensor] | None = None,
        agent_positions: torch.Tensor | None = None,
        affordance_positions: dict[str, torch.Tensor] | None = None,
        vfs_types: dict[str, str] | None = None,
        num_agents: int | None = None,
        item_vfs: torch.Tensor | None = None,
        item_profile_map: dict[str, dict[str, int]] | None = None,
        item_index_to_profile: dict[int, str] | None = None,
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
            # Mark-and-sweep requires explicit marks. Use EAGER mode when every
            # variable should be evaluated intentionally.
            vars_to_eval: set[str]
            if marks is None:
                raise ValueError("MARK_AND_SWEEP evaluation requires explicit marks; use EAGER mode to evaluate every variable.")
            else:
                # Evaluate marked variables plus their in-profile dependencies
                dependencies = getattr(profile, "dependencies", {}) or {}
                var_names = {var.name for var in profile.variables}
                unknown_marks = marks - var_names
                if unknown_marks:
                    raise KeyError(f"VFS mark(s) not found in profile: {sorted(unknown_marks)}")

                def add_with_deps(var_name: str, acc: set[str]) -> None:
                    """Add variable and its dependencies to evaluation set."""
                    if var_name in acc:
                        return
                    acc.add(var_name)
                    for dep in dependencies.get(var_name, ()):
                        add_with_deps(dep, acc)

                vars_to_eval = set()
                for marked in marks:
                    add_with_deps(marked, vars_to_eval)
        else:  # EAGER mode
            vars_to_eval = {var.name for var in profile.variables}

        # Temporal history requires variables to be evaluated even if unmarked
        history_vfs_vars = {key.split(".", 1)[1] for key in self.history_spec if key.startswith("vfs.")}
        vars_to_eval.update(history_vfs_vars)

        # Build execution context
        self._prepare_history(device)
        context = ExecutionContext(
            bars=bars,
            vfs=vfs_state.copy(),  # Copy so we can update during evaluation
            affordances=affordances or {},
            affordance_positions=affordance_positions,
            agent_positions=agent_positions,
            temporal=temporal or {},
            device=device,
            vfs_types=vfs_types,
            num_agents=num_agents,
            item_vfs=item_vfs,
            item_profile_map=item_profile_map,
            item_index_to_profile=item_index_to_profile,
            history=self._history,
            step=step,
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

        # Push history after evaluating current step
        self._push_history(bars=bars, vfs_values=context.vfs, device=device, step=step)

        if self._debug_vfs:
            self._logger.debug(
                "vfs_evaluation",
                extra={
                    "mode": self.mode.value,
                    "evaluated": sorted(result.keys()),
                    "marks": sorted(marks) if marks is not None else None,
                },
            )
        return result

    def evaluate_all(self, registry: Any) -> dict[str, torch.Tensor]:
        """Utility for benchmarks: return a snapshot of current VFS values."""
        snapshot: dict[str, torch.Tensor] = {}
        # Capture globals
        if hasattr(registry, "list_global") and hasattr(registry, "get_global"):
            for name in registry.list_global():
                snapshot[f"global.{name}"] = registry.get_global(name)
        # Capture agent values (batched tensors)
        if hasattr(registry, "list_agent") and hasattr(registry, "get_agent"):
            for name in registry.list_agent():
                snapshot[f"agent.{name}"] = registry.get_agent(name)
        return snapshot
