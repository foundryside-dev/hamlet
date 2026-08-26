"""Component-level performance benchmarks for VFS, effects, and item observations."""

from __future__ import annotations

import torch

from townlet.effects.executor import CommandExecutor
from townlet.effects.manager import EffectManager
from townlet.effects.schema import EffectDefinition, EffectScope
from townlet.vfs.evaluator import EvaluationMode, VFSEvaluator
from townlet.vfs.registry import ScopedVariableRegistry


def _make_vfs_registry(num_agents: int = 8) -> ScopedVariableRegistry:
    registry = ScopedVariableRegistry(device=torch.device("cpu"))
    # Populate some globals/agents for evaluation
    registry.set_global("day_count", torch.tensor(0.0))
    registry.set_agent("energy", torch.ones(num_agents))
    registry.set_agent("health", torch.full((num_agents,), 0.5))
    return registry


class TestVFSBenchmarks:
    """Benchmark VFS evaluation and observation build."""

    def test_vfs_evaluation(self, benchmark):
        # Simple evaluation of globals/agents via mark-and-sweep evaluator
        registry = _make_vfs_registry()
        evaluator = VFSEvaluator(mode=EvaluationMode.MARK_AND_SWEEP)

        def _eval():
            # Simulate a handful of marks; here we just use globals/agents already set.
            return evaluator.evaluate_all(registry)

        benchmark(_eval)


class TestEffectsBenchmarks:
    """Benchmark effects execution tick."""

    def test_effects_tick(self, benchmark):
        # Minimal catalog with one effect
        effect_def = EffectDefinition(
            id="regen",
            scope=EffectScope.AGENT,
            duration=1,
            reapply_policy="stack",
            observable=True,
            intensity=1.0,
            on_spawn=[],
            on_tick=[],
            on_despawn=[],
        )

        manager = EffectManager(
            catalog={"regen": effect_def},
            command_executor=CommandExecutor(),
            device="cpu",
            time_enabled=False,
        )

        # No active effects; measure tick overhead
        def _tick():
            manager.tick(bars={}, vfs_registry=None, current_step=0, item_manager=None)

        benchmark(_tick)


