"""`max_active_effects` is enforced at admission, per scope entity, per world (phase B3d).

Before: a `stack`-policy effect spawned twice on one agent under `agent: 1` overflowed the
effect token block at publish, and `TokenCapacityError` killed every world in the batch
(configs/reference/model_pack L0_demo, B2d verifier). Now the spawn that would exceed the
budget is not admitted in that world, the refusal is telemetry, and no other world moves.
"""

from __future__ import annotations

from pathlib import Path

import torch

from tests.test_townlet.utils.builders import make_vectorized_env_from_pack
from townlet.config.effects_config import EffectScope
from townlet.effects.catalog import CompiledEffect, EffectCatalog
from townlet.effects.manager import EffectManager, SpawnRefusal

MODEL_PACK = Path("configs/reference/model_pack")
LEVEL = "L0_demo"


def _effect(effect_id: str, policy: str) -> CompiledEffect:
    return CompiledEffect(
        id=effect_id,
        scope="agent",
        duration=10,
        reapply_policy=policy,
        observable=True,
        on_spawn=[],
        on_tick=[],
        on_despawn=[],
        on_interrupt=[],
    )


def _manager(**budget: int) -> EffectManager:
    catalog = EffectCatalog(
        effects={"stacker": _effect("stacker", "stack"), "renewer": _effect("renewer", "renew")},
        max_active_effects={"global": 0, "agent": 1, "item": 0, "affordance": 0} | budget,
    )
    return EffectManager(catalog=catalog, device="cpu")


def test_a_stack_beyond_the_budget_is_refused_in_that_world_only() -> None:
    manager = _manager(agent=1)
    first = manager.spawn_effect("stacker", 0, 1.0, current_step=3)
    assert first is not None
    assert manager.spawn_effect("stacker", 0, 1.0, current_step=4) is None

    assert [effect.instance_id for effect in manager.agent_effects[0]] == [first.instance_id]
    assert manager.spawn_refusals == [SpawnRefusal(world=0, effect_id="stacker", scope=EffectScope.AGENT, key=0, budget=1, live=1, step=4)]
    # World 1's agent still has its own budget.
    assert manager.spawn_effect("stacker", 1, 1.0, current_step=4) is not None
    assert len(manager.spawn_refusals) == 1


def test_renew_adds_no_instance_and_is_always_admitted() -> None:
    manager = _manager(agent=1)
    first = manager.spawn_effect("renewer", 0, 1.0, current_step=0)
    assert first is not None
    first.duration_remaining = 2
    assert manager.spawn_effect("renewer", 0, 1.0, current_step=5) is first
    assert first.duration_remaining == 10
    assert manager.spawn_refusals == []


def test_the_budget_counts_every_effect_on_the_entity() -> None:
    manager = _manager(agent=1)
    assert manager.spawn_effect("renewer", 0, 1.0, current_step=0) is not None
    assert manager.spawn_effect("stacker", 0, 1.0, current_step=0) is None
    assert manager.spawn_refusals[0].effect_id == "stacker"


def test_reset_clears_the_refusal_record() -> None:
    manager = _manager(agent=0)
    assert manager.spawn_effect("stacker", 0, 1.0, current_step=0) is None
    assert len(manager.spawn_refusals) == 1
    manager.reset()
    assert manager.spawn_refusals == []


def test_an_overflowing_world_does_not_kill_the_batch(tmp_path: Path) -> None:
    """model_pack L0_demo: `agent: 1`, `ate_food` stacks. Two spawns in world 0 used to raise
    TokenCapacityError at publish for all worlds."""
    env = make_vectorized_env_from_pack(MODEL_PACK, level_name=LEVEL, num_agents=2, device=torch.device("cpu"))
    env.reset()
    manager = env.effect_manager
    assert manager is not None
    bars = {name: env.meters[:, idx] for name, idx in env.meter_name_to_index.items()}
    spawn = dict(bars=bars, vfs_registry=env.vfs_registry, item_manager=env.item_manager, world=0)
    assert manager.spawn_effect("ate_food", 0, 1.0, env.global_tick, **spawn) is not None
    assert manager.spawn_effect("ate_food", 0, 1.0, env.global_tick, **spawn) is None
    meters_world1 = env.meters[1].clone()

    wait = env.action_ids["WAIT"]
    obs, _rewards, _dones, info = env.step(torch.tensor([wait, wait]))

    assert obs.shape[0] == 2
    assert len(manager.effects_in_world(0)) == 1
    assert manager.effects_in_world(1) == []
    refusals = [refusal for refusal in manager.spawn_refusals if refusal.effect_id == "ate_food"]
    assert [refusal.world for refusal in refusals] == [0]
    assert info["effect_spawn_refusals"] == ()  # the refusal happened before this step
    # World 1 only depleted passively; nothing from world 0's overflow reached it.
    assert torch.all(env.meters[1] <= meters_world1)
