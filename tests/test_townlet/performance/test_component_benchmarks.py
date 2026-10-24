"""Component-level performance benchmarks for VFS, effects, and item observations."""

from __future__ import annotations

from townlet.effects.catalog import CompiledEffect, EffectCatalog
from townlet.effects.executor import CommandExecutor
from townlet.effects.manager import EffectManager


class TestEffectsBenchmarks:
    """Benchmark effects execution tick."""

    def test_effects_tick(self, benchmark):
        # Minimal catalog with one effect
        effect_def = CompiledEffect(
            id="regen",
            scope="agent",
            duration=1,
            reapply_policy="stack",
            observable=True,
            on_spawn=[],
            on_tick=[],
            on_despawn=[],
            on_interrupt=[],
        )

        manager = EffectManager(
            catalog=EffectCatalog(
                effects={"regen": effect_def},
                max_active_effects={"global": 0, "agent": 1, "item": 0, "affordance": 0},
            ),
            command_executor=CommandExecutor(),
            device="cpu",
            time_enabled=False,
        )

        # No active effects; measure tick overhead
        def _tick():
            manager.tick(bars={}, vfs_registry=None, current_step=0, item_manager=None)

        benchmark(_tick)
