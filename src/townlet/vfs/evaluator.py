"""VFS expression evaluator with mark-and-sweep support."""

from __future__ import annotations

from typing import Any

import torch

from townlet.vfs.profiles import CompiledGlobalProfile
from townlet.vfs.storage_dtype import storage_dtype, to_storage_dtype
from townlet.world.expression.context import ExecutionContext
from townlet.world.expression.evaluator import Evaluator
from townlet.world.expression.history import TemporalHistory

__all__ = ["VFSEvaluator"]


class VFSEvaluator:
    """Evaluates VFS expressions using compiled profiles, mark-and-sweep.

    Only the marked expressions and their in-profile dependencies are evaluated; statics
    are storage and always read their current runtime value from ``vfs_state``.
    """

    def __init__(self, history_spec: dict[str, int] | None = None):
        """Initialize VFS evaluator.

        Args:
            history_spec: Temporal history buffer lengths keyed by ``bar.*`` / ``vfs.*``
        """
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
        marks: set[str],
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
            marks: Variable names to evaluate, plus their in-profile dependencies
            device: PyTorch device

        Returns:
            Dict mapping variable names to evaluated tensors
        """
        dependencies = profile.dependencies
        unknown_marks = marks - {var.name for var in profile.variables}
        if unknown_marks:
            raise KeyError(f"VFS mark(s) not found in profile: {sorted(unknown_marks)}")

        def add_with_deps(var_name: str, acc: set[str]) -> None:
            """Add variable and its dependencies to evaluation set."""
            if var_name in acc:
                return
            acc.add(var_name)
            for dep in dependencies.get(var_name, ()):
                add_with_deps(dep, acc)

        vars_to_eval: set[str] = set()
        for marked in marks:
            add_with_deps(marked, vars_to_eval)

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

            # Static (no expression): storage, not computation. It reaches vars_to_eval
            # through the dependency chase of a marked expression or through the
            # history_spec union above (derive_evaluation_marks never marks a static).
            # context.vfs already carries its CURRENT runtime value from vfs_state; the
            # declared initial value is reported in `result` only and never fed to a
            # dependent expression (hamlet-df3a96bbac).
            if var.ast is None:
                result[var.name] = torch.tensor(var.initial_value, device=device)
                continue

            # Evaluate, then settle the DSL result into the variable's storage dtype: a
            # scalar expression may type-check to int (``where(c, 1, 0)``) and lands in
            # float32 storage; any other dtype disagreement is refused, never cast.
            value = to_storage_dtype(
                evaluator.evaluate(var.ast),
                torch.float32 if var.type == "float" else storage_dtype(var.type),
                f"Expression variable '{var.name}'",
            )

            # Store result and update context so later variables can reference this one
            result[var.name] = value
            context.vfs[var.name] = value

        # Push history after evaluating current step
        self._push_history(bars=bars, vfs_values=context.vfs, device=device, step=step)

        return result
