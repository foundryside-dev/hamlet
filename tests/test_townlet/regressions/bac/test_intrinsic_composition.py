"""Genuine canonical producer proofs; local bootstrap does not certify HC/T26 restore."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import torch

from tests.test_townlet.regressions.bac.test_parent_intrinsic_handoff import (
    FAMILIES,
    IDS,
    equal,
    make_parent,
    observe_runtime,
    policy,
)
from tests.test_townlet.regressions.bac.test_parent_intrinsic_handoff import (
    compiled as compiled,
)
from townlet.config.bac_options import BaCOptions
from townlet.config.drive_as_code import (
    CompositionConfig,
    DriveAsCodeConfig,
    EfficiencyBonusConfig,
    ExtrinsicStrategyConfig,
    IntrinsicStrategyConfig,
    ModifierConfig,
    RangeConfig,
)
from townlet.config.exploration_policy import resolve_exploration_policy
from townlet.config.training_v2_config import TrainingV2Config
from townlet.environment.dac_engine import DACEngine
from townlet.training.replay_contract import ReplayRequest
from townlet.universe.compiler import UniverseCompiler


def controlled_policy(compiled: Any, scope: str, scale: float) -> Any:
    """Resolve the actual authored training scale; preserve genuine scope/service declarations."""
    selected = compiled.get_level(compiled.metadata.primary_level)
    template = policy(compiled, "icm", scope, "paced_fifo")
    training_data = selected.training.model_dump()
    training_data["intrinsic"]["initial_weight"] = scale
    training = TrainingV2Config.model_validate(training_data)
    options = BaCOptions.model_validate(template.to_dict()["authored_parameters"]["bac_options"])
    drive = IntrinsicStrategyConfig(strategy="icm", base_weight=0.25, apply_modifiers=[])
    resolved = resolve_exploration_policy(drive, training, options)
    assert resolved.initial_intrinsic_weight == scale
    return resolved


def install_raw_two(runtime: Any, scope: str) -> None:
    """Ordinary INITIAL model control via owned public transport; no invented training/RMS."""
    saved = runtime.checkpoint_state()
    bank = saved["bank"]
    assert bank["initialization_origin"] is None
    if scope == "shared":
        natives = [bank["shared_backend"]["native"]]
    else:
        assert {record["world_id"] for record in bank["worlds"]} == set(IDS)
        natives = [record["backend"]["backend"] for record in bank["worlds"]]
    for native in natives:
        for name in ("encoder", "forward_model"):
            assert set(native[name]) == {"0.weight", "0.bias", "2.weight", "2.bias"}
            for tensor in native[name].values():
                tensor.zero_()
        native["forward_model"]["2.bias"].fill_(2.0)
    prepared = runtime.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    runtime.install_restore(prepared=prepared)


def real_composer(env: Any, base: float) -> None:
    config = DriveAsCodeConfig(
        version="1.0",
        intrinsic=IntrinsicStrategyConfig(strategy="icm", base_weight=base, apply_modifiers=["double"]),
        extrinsic=ExtrinsicStrategyConfig(
            type="constant_base_with_shaped_bonus", base_reward=1.0, bars=[], bar_bonuses=[], variable_bonuses=[], apply_modifiers=[]
        ),
        modifiers={"double": ModifierConfig(bar="energy", ranges=[RangeConfig(name="all", min=0.0, max=1.0, multiplier=2.0)])},
        shaping=[EfficiencyBonusConfig(type="efficiency_bonus", weight=0.1, bar="energy", threshold=0.7)],
        composition=CompositionConfig(normalize=False, clip=None, log_components=True, log_modifiers=True),
    )
    env.dac_engine = DACEngine(
        dac_config=config,
        vfs_registry=env.vfs_registry,
        device=env.device,
        num_agents=env.num_agents,
        bar_index_map=env.meter_name_to_index,
    )


def wait_control(monkeypatch: Any, rig: Any) -> None:
    """Real selector executes; declared WAIT physics control does not prove selected policy actions."""
    select = rig.runtime.select_actions
    wait = rig.env.action_ids["WAIT"]

    def controlled(q_values: Any, agent_states: Any, action_masks: Any) -> Any:
        actions = select(q_values, agent_states, action_masks)
        assert bool(action_masks[:, wait].all())
        return torch.full_like(actions, wait)

    monkeypatch.setattr(rig.runtime, "select_actions", controlled)


@pytest.mark.parametrize("scope", ("shared", "per_world"))
@pytest.mark.parametrize(
    "scale,base,intrinsic,total", ((0.5, 0.25, 0.5, 1.6), (0.0, 0.25, 0.0, 1.1), (1.0, 0.25, 1.0, 2.1), (0.5, 0.5, 1.0, 2.1))
)
def test_real_composer_applies_runtime_scale_once(
    compiled: Any, monkeypatch: Any, scope: str, scale: float, base: float, intrinsic: float, total: float
) -> None:
    rig = make_parent(compiled, "icm", scope, selected_policy=controlled_policy(compiled, scope, scale))
    install_raw_two(rig.runtime, scope)
    rig.enter()
    real_composer(rig.env, base)
    rig.env.meters[:, rig.env.meter_name_to_index["energy"]] = 0.8
    # Real test setup changes predecessor state; keep actual parent observation synchronized.
    rig.population.current_obs = rig.env._get_observations()
    wait_control(monkeypatch, rig)
    calls = observe_runtime(monkeypatch, rig)
    state = rig.population.step_population(rig.env)
    assert not bool(state.dones.any())  # These are pre-retirement arithmetic cases.
    assert len(calls["reward"]) == len(calls["service"]) == 1
    arguments, reward = calls["reward"][0]
    assert arguments["update_stats"] is True
    components = state.info["reward_components"]
    for actual, expected in (
        (reward.raw, 2.0),
        (reward.scales, scale),
        (components["provider_intrinsic_raw"], 2.0),
        (components["runtime_intrinsic_scale"], scale),
        (components["intrinsic_raw"], 2 * base),
        (components["intrinsic"], intrinsic),
        (components["extrinsic"], 1.0),
        (components["shaping"], 0.1),
        (state.info["intrinsic_weight"], 2.0),
        (state.rewards, total),
    ):
        torch.testing.assert_close(actual, torch.full_like(actual, expected))
    receipts = calls["service"][0][1]
    assert sum(receipt.admitted_rows for receipt in receipts) == len(IDS)  # Includes genuine scale0 work.
    request = ReplayRequest(len(IDS), 1, 2, "uniform_without_replacement", "feedforward", "transition")
    batch = rig.population.replay_buffer.sample_batch(request)
    equal(batch.rewards, state.rewards[batch.unit_ids])
    for name in ("extrinsic", "intrinsic", "shaping"):
        assert bool(getattr(batch, f"rewards_{name}_present").all())
        equal(getattr(batch, f"rewards_{name}"), state.info["reward_components"][name][batch.unit_ids])
    equal(batch.next_observations, state.observations[batch.unit_ids])
    equal(batch.next_action_masks, state.info["successor_action_masks"][batch.unit_ids])


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("scope", ("shared", "per_world"))
def test_provider_phase_and_transition_identity(compiled: Any, monkeypatch: Any, family: str, scope: str) -> None:
    rig = make_parent(compiled, family, scope)
    rig.enter()
    predecessor = rig.population.current_obs.clone()
    calls = observe_runtime(monkeypatch, rig)
    boundary: list[torch.Tensor] = []
    calculate = rig.env._reward_calculator._calculate_shaped_rewards

    def capture(**kwargs: Any) -> Any:
        boundary.append(rig.env._get_observations().clone())
        return calculate(**kwargs)

    monkeypatch.setattr(rig.env._reward_calculator, "_calculate_shaped_rewards", capture)
    state = rig.population.step_population(rig.env)
    handoff = state.info["intrinsic_transition"]
    assert len(boundary) == len(calls["reward"]) == len(calls["service"]) == 1
    equal(boundary[0], state.observations)
    equal(handoff.context.predecessor, predecessor)
    equal(handoff.context.successor, boundary[0])
    assert not torch.equal(predecessor, boundary[0])
    equal(handoff.context.actions, state.actions)
    equal(handoff.context.active_on_entry, state.info["active_on_entry"])
    for arguments in (calls["reward"][0][0], calls["service"][0][0]):
        assert arguments["context"] is handoff.context
        assert arguments["stamp"] is handoff.stamp
        assert arguments["accepted"] is handoff.accepted is rig.record.accepted
    reward = calls["reward"][0][1]
    equal(state.info["reward_components"]["provider_intrinsic_raw"], reward.raw)
    equal(state.info["reward_components"]["runtime_intrinsic_scale"], reward.scales)
    # Public context accessors cannot mutate the event subsequently used by cached retries.
    handoff.context.successor.add_(100)
    equal(handoff.context.successor, state.observations)
    before = rig.runtime.checkpoint_state()
    equal(rig.runtime.reward(**calls["reward"][0][0]).raw, reward.raw)
    equal(rig.runtime.admit_and_service(**calls["service"][0][0]), calls["service"][0][1])
    equal(rig.runtime.checkpoint_state(), before)


def test_claim_refusal_precedes_first_physical_write(compiled: Any) -> None:
    rig = make_parent(compiled)
    rig.enter()
    candidate = rig.candidate()
    prepared = rig.population.prepare_vector_step(**candidate)
    before = (rig.env.global_tick, rig.env._world_revision, rig.env.meters.clone(), rig.env.positions.clone())
    changed = candidate["actions"].clone()
    changed[0] = (changed[0] + 1) % rig.env.action_dim
    with pytest.raises((ValueError, RuntimeError)):
        rig.env.step(changed, vector_step=prepared)
    assert (rig.env.global_tick, rig.env._world_revision) == before[:2]
    equal(rig.env.meters, before[2])
    equal(rig.env.positions, before[3])
    assert rig.population.total_steps == 0


@pytest.fixture(scope="module")
def temporal_compiled() -> Any:
    return UniverseCompiler().compile(Path("configs/reference/model_pack"), primary_level="L0_demo", use_cache=False)


@pytest.mark.parametrize("terminal", (False, True))
def test_real_effect_pending_cancellation_preserves_successor(temporal_compiled: Any, monkeypatch: Any, terminal: bool) -> None:
    rig = make_parent(temporal_compiled)
    rig.enter()
    env = rig.env
    manager = env.effect_manager
    effect_layout = env.token_spec.compact_layout().get_type("effect")
    assert effect_layout.capacity > 0
    assert env.token_spec.get_type("item").capacity > 0
    bars = {name: env.meters[:, col] for name, col in env.meter_name_to_index.items()}
    active = manager.spawn_effect(
        effect_id="ate_food",
        target_entity_id=0,
        world=0,
        intensity=1.0,
        current_step=manager.current_step,
        bars=bars,
        vfs_registry=env.vfs_registry,
        item_manager=env.item_manager,
    )
    assert active is not None and active.observable
    manager.scheduler.schedule(
        commands=manager.catalog.effects["ate_food"].on_tick,
        delay_ticks=10,
        base_tick=manager.current_step,
        scope="agent",
        entity_id=0,
        context_overrides={"effect": active},
        effect_instance=active.instance_id,
    )
    due = manager.current_step + 10
    pending = tuple(manager.scheduler.pending[due])
    assert pending
    if terminal:
        env.meters[0, env.meter_name_to_index["health"]] = 0.001
    rig.population.current_obs = env._get_observations()
    wait_control(monkeypatch, rig)
    calculate = env._reward_calculator._calculate_shaped_rewards
    boundary: list[torch.Tensor] = []

    def capture(**kwargs: Any) -> Any:
        assert all(item in manager.scheduler.pending[due] for item in pending)
        assert active in manager.effects_in_world(0)
        boundary.append(env._get_observations().clone())
        return calculate(**kwargs)

    monkeypatch.setattr(env._reward_calculator, "_calculate_shaped_rewards", capture)
    state = rig.population.step_population(env)
    equal(boundary[0], state.observations)
    equal(state.info["intrinsic_transition"].context.successor, boundary[0])
    assert bool(state.info["newly_terminal"][0]) is terminal
    remaining = tuple(manager.scheduler.pending.get(due, ()))
    assert all((item not in remaining) is terminal for item in pending)
    assert active in manager.effects_in_world(0)
    assert active.duration_remaining == 9 and active.elapsed_ticks == 1
    block = state.observations[0, effect_layout.start : effect_layout.start + effect_layout.capacity * effect_layout.compact_row_width]
    rows = block.reshape(effect_layout.capacity, effect_layout.compact_row_width)
    assert int((rows[:, 0] > 0).sum()) == 1
    assert bool((rows[:, effect_layout.dynamic_features.index("remaining_fraction")] > 0).any())
    if terminal:
        monkeypatch.setattr(env._reward_calculator, "_calculate_shaped_rewards", calculate)
        later = rig.population.step_population(env)
        assert not bool(later.info["active_on_entry"][0])
        assert float(later.rewards[0]) == float(later.info["intrinsic_weight"][0]) == 0.0
        assert all(float(component[0]) == 0.0 for component in later.info["reward_components"].values())


def test_retirement_preserves_live_composition_then_adds_bonus(compiled: Any, monkeypatch: Any) -> None:
    rig = make_parent(compiled, "icm", selected_policy=controlled_policy(compiled, "shared", 0.5))
    install_raw_two(rig.runtime, "shared")
    rig.enter()
    real_composer(rig.env, 0.25)
    # Explicit actual ENV lifespan control; all rows retire on their first eligible transition.
    rig.env.agent_lifespan = 1
    rig.env.meters[:, rig.env.meter_name_to_index["energy"]] = 0.8
    rig.population.current_obs = rig.env._get_observations()
    wait_control(monkeypatch, rig)
    state = rig.population.step_population(rig.env)
    assert bool(state.info["newly_retired"].all())
    assert bool(state.info["active_on_entry"].all())
    components = state.info["reward_components"]
    torch.testing.assert_close(components["intrinsic"], torch.full_like(state.rewards, 0.5))
    torch.testing.assert_close(components["extrinsic"], torch.full_like(state.rewards, 2.0))
    torch.testing.assert_close(state.rewards, torch.full_like(state.rewards, 2.6))
    equal(state.info["intrinsic_transition"].context.successor, state.observations)
    request = ReplayRequest(len(IDS), 1, 2, "uniform_without_replacement", "feedforward", "transition")
    batch = rig.population.replay_buffer.sample_batch(request)
    equal(batch.rewards, state.rewards[batch.unit_ids])
    for name in ("extrinsic", "intrinsic", "shaping"):
        assert bool(getattr(batch, f"rewards_{name}_present").all())
        equal(getattr(batch, f"rewards_{name}"), state.info["reward_components"][name][batch.unit_ids])


@pytest.mark.parametrize("phase", ("bound", "role_frozen", "active"))
@pytest.mark.parametrize("replacement", ("runtime", "callback", "same"))
def test_runtime_binding_is_once_before_world_custody(compiled: Any, phase: str, replacement: str) -> None:
    """The genuine constructor binds once; even equal retry is outside the protocol."""
    rig, foreign = make_parent(compiled), make_parent(compiled)
    if phase == "role_frozen":
        pop = rig.population
        rig.env.bind_boundary_authority(
            owner=rig,
            role_owners={
                "population": pop,
                "curiosity": rig.bank,
                "curriculum": pop.curriculum,
                "exploration": rig.runtime,
                "network": pop.q_network,
                "optimizer": pop.optimizer,
                "scheduler": pop if pop.scheduler is None else pop.scheduler,
                "replay": pop.replay_buffer,
                "selection": rig.runtime,
            },
        )
    elif phase == "active":
        rig.enter()
    original_runtime, original_claim = rig.env._exploration_runtime, rig.env._claim_vector_step
    before = (rig.env.global_tick, rig.env._world_revision, rig.env.meters.clone(), rig.env.positions.clone())
    runtime = foreign.runtime if replacement == "runtime" else rig.runtime
    claim = foreign.population.claim_vector_step if replacement == "callback" else original_claim
    with pytest.raises((ValueError, RuntimeError)):
        rig.env.set_exploration_runtime(exploration=runtime, claim_vector_step=claim)
    assert rig.env._exploration_runtime is original_runtime
    assert rig.env._claim_vector_step is original_claim
    assert (rig.env.global_tick, rig.env._world_revision) == before[:2]
    equal(rig.env.meters, before[2])
    equal(rig.env.positions, before[3])
    assert rig.population.total_steps == 0
