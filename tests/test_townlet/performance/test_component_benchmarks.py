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


class TestItemObservationBenchmarks:
    """Benchmark building item VFS observations."""

    def test_item_vfs_observation_build(self, benchmark):
        # Use registry with some agent/item data
        registry = _make_vfs_registry()

        max_items_per_agent = 3
        vars_per_slot = 4
        # Fake item_vfs storage: [max_items, vars_per_slot]
        registry.item_vfs = torch.ones((10, vars_per_slot))
        agent_item_inventory = torch.full((8, max_items_per_agent), -1)
        # Give each agent one item in slot 0 pointing to item_vfs row 0
        agent_item_inventory[:, 0] = 0

        from townlet.vfs.observation_builder import VFSObservationSpec, build_vfs_observation

        spec = VFSObservationSpec(global_vfs_dim=1, agent_vfs_dim=2, item_vfs_dim=max_items_per_agent * vars_per_slot)

        def _build_obs():
            return build_vfs_observation(
                registry=registry,
                spec=spec,
                batch_size=agent_item_inventory.size(0),
                agent_item_inventory=agent_item_inventory,
            )

        benchmark(_build_obs)
