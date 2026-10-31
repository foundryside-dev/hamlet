"""VFS expression evaluator with mark-and-sweep support."""

from __future__ import annotations

import torch

from townlet.vfs.profiles import CompiledGlobalProfile
from townlet.vfs.random_draws import DrawInstant
from townlet.vfs.storage_dtype import storage_dtype, to_storage_dtype
from townlet.world.expression.context import ExecutionContext
from townlet.world.expression.evaluator import Evaluator
from townlet.world.expression.functions import REQUIRES_HISTORY, REQUIRES_POSITIONS, unserved_requirement
from townlet.world.expression.history import TemporalHistory

__all__ = ["VFSEvaluator"]

_SERVED_WITHOUT_STREAMS = frozenset({REQUIRES_HISTORY, REQUIRES_POSITIONS})


class VFSEvaluator:
    """Evaluates VFS expressions using compiled profiles, mark-and-sweep.

    Only the marked expressions and their in-profile dependencies are evaluated; statics
    are storage and always read their current runtime value from ``vfs_state``.

    One instant of evaluation is ``begin_instant`` → each profile's
    ``evaluate_global_profile`` (global first, then agent) → ``commit_instant``. The
    history every temporal operator reads is committed only at the end, so within an
    instant every ``lag`` read sees the previous instants, whichever profile reads it.
    """

    def __init__(self, history_spec: dict[str, int] | None):
        """Initialize VFS evaluator.

        Args:
            history_spec: The compiled history ring depth per key (``bar.*`` / ``vfs.*``), or
                None when no expression reads history
        """
        self.history_spec = dict(history_spec) if history_spec else {}
        self._history: TemporalHistory | None = TemporalHistory(self.history_spec, torch.device("cpu")) if self.history_spec else None

    def _prepare_history(self, device: torch.device) -> None:
        if self._history is not None and self._history.device != device:
            self._history.to(device)

    def begin_instant(self, bars: dict[str, torch.Tensor], vfs_state: dict[str, torch.Tensor], device: torch.device) -> None:
        """Open one instant. The episode's first instant seeds every history ring from the
        pre-evaluation state: each key's episode-start value (``world/expression/history.py``)."""
        if self._history is None:
            return
        self._prepare_history(device)
        if not self._history.seeded:
            self._history.seed(bars, vfs_state)

    def commit_instant(self, bars: dict[str, torch.Tensor], vfs_state: dict[str, torch.Tensor], live: torch.Tensor) -> None:
        """Close one instant: record every history key's committed value in the live worlds.

        ``vfs_state`` is the registry after every profile's write-back. A world outside
        ``live`` (its agent is done) keeps its history frozen.
        """
        if self._history is not None:
            self._history.commit(bars, vfs_state, live)

    def reset(self) -> None:
        """Start a new episode: drop all history; the next ``begin_instant`` re-seeds it."""
        if self._history is not None:
            self._history.reset()

    def evaluate_global_profile(
        self,
        profile: CompiledGlobalProfile,
        bars: dict[str, torch.Tensor],
        vfs_state: dict[str, torch.Tensor],
        marks: set[str],
        device: torch.device = torch.device("cpu"),
        agent_positions: torch.Tensor | None = None,
        affordance_positions: dict[str, torch.Tensor] | None = None,
        draws: DrawInstant | None = None,
    ) -> dict[str, torch.Tensor]:
        """Evaluate global VFS profile expressions.

        Args:
            profile: Compiled global profile with variables in topo order
            bars: Bar state (e.g., {"energy": tensor([batch])})
            vfs_state: Current VFS state (inputs for expressions)
            marks: Variable names to evaluate, plus their in-profile dependencies
            device: PyTorch device
            agent_positions: ``[worlds, D]`` agent positions, for the position functions
            affordance_positions: deployed affordance positions by name, likewise
            draws: this instant's counter-based draws (``townlet.vfs.random_draws``); each
                variable draws from its own sites (``var:<id>``), one value per world row.
                None only when no evaluated expression samples: a draw never falls through
                to torch's global stream.

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

        if self._history is not None and not self._history.seeded:
            raise RuntimeError("Engine defect: a profile with history evaluated outside begin_instant/commit_instant")
        sampling = {
            var.name
            for var in profile.variables
            if var.name in vars_to_eval and var.ast is not None and unserved_requirement(var.ast, _SERVED_WITHOUT_STREAMS) is not None
        }
        if sampling and draws is None:
            raise RuntimeError(
                f"Engine defect: expression variable(s) {sorted(sampling)} sample, but the profile was evaluated "
                "without the instant's draws"
            )

        # Build execution context
        context = ExecutionContext(
            bars=bars,
            vfs=vfs_state.copy(),  # Copy so we can update during evaluation
            temporal={},
            affordance_positions=affordance_positions,
            agent_positions=agent_positions,
            device=device,
            history=self._history,
        )

        evaluator = Evaluator(context)
        result = {}

        # Evaluate variables in topological order (profile.variables already sorted)
        for var in profile.variables:
            # Skip if not in evaluation set (mark-and-sweep)
            if var.name not in vars_to_eval:
                continue

            # Static (no expression): storage, not computation. It reaches vars_to_eval
            # through the dependency chase of a marked expression (derive_evaluation_marks
            # never marks a static).
            # context.vfs already carries its CURRENT runtime value from vfs_state; the
            # declared initial value is reported in `result` only and never fed to a
            # dependent expression (hamlet-df3a96bbac).
            if var.ast is None:
                # Report the runtime value (a static initialised by `initial_value_mode` has
                # no literal initial_value); write-back skips statics either way.
                if var.name in context.vfs:
                    result[var.name] = context.vfs[var.name]
                continue

            # Evaluate, then settle the DSL result into the variable's storage dtype: a
            # scalar expression may type-check to int (``where(c, 1, 0)``) and lands in
            # float32 storage; any other dtype disagreement is refused, never cast.
            if var.name in sampling:
                assert draws is not None
                context.draws = draws.stream(f"var:{var.name}", (draws.worlds,))
            else:
                context.draws = None
            value = to_storage_dtype(
                evaluator.evaluate(var.ast),
                torch.float32 if var.type == "float" else storage_dtype(var.type),
                f"Expression variable '{var.name}'",
            )

            # Store result and update context so later variables can reference this one
            result[var.name] = value
            context.vfs[var.name] = value

        return result
