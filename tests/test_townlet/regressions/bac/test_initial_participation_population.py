"""Actual POP retirement and preserved inference; component boundaries do not attest full D/T26."""

from __future__ import annotations

import copy
import random
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch

from tests.test_townlet.regressions.bac.test_parent_intrinsic_handoff import (
    IDS,
    ParentFixture,
    equal,
    make_parent,
    observe_runtime,
)
from tests.test_townlet.regressions.bac.test_parent_intrinsic_handoff import (
    compiled as compiled,
)
from townlet.environment.vectorized_env import WorldReceiptIssuer
from townlet.population import vectorized as population_module
from townlet.training.episode import freeze_lane_outcome
from townlet.training.replay_contract import ReplayRequest
from townlet.universe.compiler import UniverseCompiler

RETIRED = IDS[1:]
LIVE = torch.tensor([True, False, False, False, False, False, False, False])
REFUSAL = (ValueError, RuntimeError)


def reserve(rig: ParentFixture, batch: int = 0) -> Any:
    """Use actual fixture role custody and current full-roster reservation."""
    if rig.boundary is None:
        rig.bind()
        rig.release = rig.boundary.bootstrap(first_batch_episode=batch)
        rig.env.install_boundary_release(rig.release)
    reservation = rig.env.prepare_episode(batch_episode=batch, release=rig.release)
    rig.env.validate_episode_reservation(reservation)
    rig.population.bind_episode_worlds(world_ids=IDS, world_episode_seqs=reservation.world_episode_seqs)
    rig.population.begin_batch_episode(batch, planned_horizon=20)
    return reservation


def activate(rig: ParentFixture, activation: Any) -> None:
    curiosity = rig.runtime.begin_episode(accepted=rig.record.accepted)
    rig.env.activate_episode(accepted=rig.record.accepted, population_receipt=activation, curiosity_receipt=curiosity)


def begin(rig: ParentFixture, retired: tuple[str, ...] = RETIRED, batch: int = 0, *, active: bool = True) -> Any:
    reservation = reserve(rig, batch)
    rig.record, activation = rig.population.reset(reservation=reservation, retired_world_ids=retired)
    if active:
        activate(rig, activation)
    return reservation, activation


def unowned(compiled: Any) -> ParentFixture:
    """Real ENV reset supplies inference data without manufacturing POP episode authority."""
    rig = make_parent(compiled)
    rig.bind()
    rig.release = rig.boundary.bootstrap(first_batch_episode=0)
    rig.env.install_boundary_release(rig.release)
    reservation = rig.env.prepare_episode(batch_episode=0, release=rig.release)
    rig.record = rig.env.reset(reservation=reservation)
    rig.population.current_obs = rig.record.observation
    rig.population.max_episodes = rig.population.max_steps_per_episode = None
    return rig


def select(pop: Any, env: Any, kind: str) -> torch.Tensor:
    return pop.select_greedy_actions(env) if kind == "greedy" else pop.select_epsilon_greedy_actions(env, float(kind))


def reading(rig: ParentFixture) -> dict[str, Any]:
    pop, env = rig.population, rig.env
    numpy_state = np.random.get_state()
    return copy.deepcopy(
        dict(
            observation=pop.current_obs,
            positions=env.positions,
            meters=env.meters,
            counts=env.step_counts,
            tick=env.global_tick,
            ledger=asdict(pop.clock_ledger),
            total=pop.total_steps,
            q=pop.q_network.state_dict(),
            target=pop.target_network.state_dict(),
            optimizer=pop.optimizer.state_dict(),
            replay=pop.replay_buffer.serialize(),
            curriculum=pop.curriculum.checkpoint_state(),
            runtime=rig.runtime.checkpoint_state(),
            torch_rng=torch.get_rng_state(),
            numpy_rng=(numpy_state[0], numpy_state[1].tolist(), *numpy_state[2:]),
            python_rng=random.getstate(),
        )
    )


def capture_participation(monkeypatch: Any, rig: ParentFixture, ready: list[Any] | None = None) -> list[Any]:
    committed, original = [], rig.env.commit_initial_participation

    def commit(**kwargs: Any) -> Any:
        result = original(**kwargs)
        committed.append(result)
        if ready is not None:
            ready.append(kwargs["population_ready"])
        return result

    monkeypatch.setattr(rig.env, "commit_initial_participation", commit)
    return committed


def prepare_close(rig: ParentFixture) -> tuple[Any, Any, Any, tuple[Any, ...], tuple[Any, ...]]:
    """Actual positive events and sink preparations; no synthetic nonparticipant event."""
    pop, accepted = rig.population, rig.record.accepted
    for lane in range(len(IDS)):
        pop.flush_episode(lane, reason="budget")
    events = pop.completed_outcomes
    participants = tuple(event.world_id for event in events)
    content = tuple((item.payload.hex(), item.fingerprint) for item in map(freeze_lane_outcome, events))
    curriculum = pop.curriculum.prepare_episode_outcomes(events)
    bank = rig.runtime.prepare_completion(
        accepted=accepted,
        boundary_key=accepted.batch_episode,
        completion_content=content,
        outcomes=events,
        participated_world_ids=participants,
    )
    closing = rig.env.prepare_episode_close(
        accepted=accepted,
        boundary_key=accepted.batch_episode,
        completion_content=content,
        participated_world_ids=participants,
        dispositions=bank.prepared_receipt,
    )
    return closing, curriculum, bank, events, content


def close(rig: ParentFixture, prepared: tuple[Any, ...], *, release: bool) -> Any:
    """Same retained cooperative effect-issuer custody as ParentFixture.complete, with real participants."""
    closing, curriculum, bank, events, content = prepared
    pop, accepted = rig.population, rig.record.accepted
    rig.env.freeze_episode_close(closing)
    pop.curriculum.commit_prepared_episode_outcomes(curriculum)
    retirement = rig.runtime.commit_completion(prepared=bank)
    pop.commit_episode_outcomes(events)
    pop.sync_exploration_metrics()
    equal(pop.current_epsilons, rig.runtime.epsilon_tensor(batch_size=len(IDS), device="cpu"))
    kinds = ("curriculum_receipt", "exploration_receipt", "population_commit_receipt", "epsilon_install_receipt", "selection_sync_receipt")
    owners = (pop.curriculum, rig.runtime, pop, rig.runtime, rig.runtime, rig)
    rig.effect_issuers = tuple(WorldReceiptIssuer(owner=owner) for owner in owners)
    payload = dict(accepted=accepted, boundary_key=accepted.batch_episode, completion_content=content)
    effects = {kind: issuer.issue(kind=kind, payload=payload) for kind, issuer in zip(kinds, rig.effect_issuers[:-1], strict=True)}
    closure = rig.env.close_episode(closing, dispositions=retirement)
    effects.update(
        batch_episode=accepted.batch_episode, accepted_identity=accepted, completion_content=content, retirement_receipt=retirement
    )
    receipt = rig.effect_issuers[-1].issue(kind="boundary_effects", payload=effects)
    rig.release = rig.boundary.completed(closure=closure, effects=receipt)
    if release:
        rig.env.install_boundary_release(rig.release)
    return retirement


def forbid_effects(monkeypatch: Any, rig: ParentFixture) -> list[str]:
    """Transparent observers distinguish entry refusal from a later error after real effects."""
    calls: list[str] = []
    targets = [(rig.population, "_rollout_q"), (rig.population, "_bind_training"), (rig.runtime, "select_actions")]
    curriculum = rig.population.curriculum
    name = "get_batch_decisions_with_qvalues" if hasattr(curriculum, "get_batch_decisions_with_qvalues") else "get_batch_decisions"
    targets.extend([(curriculum, name), (rig.env, "step")])
    for owner, method in targets:
        original = getattr(owner, method)

        def observe(*args: Any, _original: Any = original, _method: str = method, **kwargs: Any) -> Any:
            calls.append(_method)
            return _original(*args, **kwargs)

        monkeypatch.setattr(owner, method, observe)
    return calls


def test_reset_seals_retirement_before_population_activation(compiled: Any, monkeypatch: Any) -> None:
    """First causal RED: real setup reaches the absent required POP reset keyword/protocol."""
    rig = make_parent(compiled)
    reservation = reserve(rig)
    events, committed = [], capture_participation(monkeypatch, rig)
    original = WorldReceiptIssuer.issue

    def issue(issuer: Any, *, kind: str, payload: Any) -> Any:
        if issuer.owner is rig.population:
            if kind == "activation":
                assert len(committed) == 1
                equal(rig.env.dones, ~LIVE)
                equal(rig.population.episode_completed, ~LIVE)
            events.append(kind)
        return original(issuer, kind=kind, payload=payload)

    monkeypatch.setattr(WorldReceiptIssuer, "issue", issue)
    rig.record, activation = rig.population.reset(reservation=reservation, retired_world_ids=RETIRED)
    assert events == ["initial_participation_intent", "initial_participation_ready", "activation"]
    assert activation.owner is rig.population
    assert rig.env.world_phase == "active-awaiting-activation"
    equal(rig.population.current_obs, rig.record.observation)
    assert rig.population.episode_completions == [None] * len(IDS)
    assert rig.population.completed_outcomes == ()
    assert rig.population.total_steps == rig.env.global_tick == 0
    assert all(value == 0 for value in asdict(rig.population.clock_ledger).values())


def test_decision_preserves_state_and_equal_reset_cannot_reopen_it(compiled: Any, monkeypatch: Any) -> None:
    rig = make_parent(compiled, "rnd", "per_world")
    before, prepared = {}, []
    prepare = rig.env.prepare_initial_participation

    def observe(**kwargs: Any) -> Any:
        before.update(reading(rig))
        result = prepare(**kwargs)
        prepared.append(result)
        assert not bool(rig.env.dones.any())
        return result

    monkeypatch.setattr(rig.env, "prepare_initial_participation", observe)
    ready: list[Any] = []
    committed = capture_participation(monkeypatch, rig, ready)
    reservation, activation = begin(rig, active=False)
    equal(reading(rig), before)
    equal(prepared[0].action_masks[1:], torch.zeros((7, rig.env.action_dim), dtype=torch.bool))
    damaged = committed[0].observation
    damaged.add_(50)
    equal(rig.population.current_obs, before["observation"])
    masks = committed[0].action_masks
    masks.fill_(True)
    assert not bool(committed[0].action_masks[1:].any())
    with pytest.raises(REFUSAL):
        rig.env.commit_initial_participation(prepared=prepared[0], population_ready=ready[0])
    record, retry = rig.population.reset(reservation=reservation, retired_world_ids=RETIRED)
    assert record is rig.record and retry is activation and len(committed) == 1
    with pytest.raises(REFUSAL):
        rig.population.reset(reservation=reservation, retired_world_ids=())
    equal(rig.env.dones, ~LIVE)
    activate(rig, activation)
    with pytest.raises(REFUSAL):
        rig.env.commit_initial_participation(prepared=prepared[0], population_ready=activation)


def test_actual_a_learning_replay_private_b_and_next_cycle(compiled: Any, monkeypatch: Any) -> None:
    rig = make_parent(compiled, "rnd", "per_world")
    begin(rig)
    calls = observe_runtime(monkeypatch, rig)
    initial = rig.runtime.checkpoint_state()
    b_before = next(world for world in initial["bank"]["worlds"] if world["world_id"] == IDS[1])
    q_before = copy.deepcopy(rig.population.q_network.state_dict())
    selected, expected, original_select = [], [], rig.runtime.select_actions

    def selector(values: Any, state: Any, masks: Any) -> Any:
        selected.append((values.shape, state.observations.shape, masks.shape))
        return original_select(values, state, masks)

    monkeypatch.setattr(rig.runtime, "select_actions", selector)
    for tick in (1, 2):
        previous = rig.population.current_obs.clone()
        state = rig.population.step_population(rig.env)
        expected.append(
            copy.deepcopy(
                dict(
                    observations=previous[0],
                    actions=state.actions[0],
                    next_observations=state.observations[0],
                    dones=state.dones[0],
                    rewards=state.rewards[0],
                    next_action_masks=state.info["successor_action_masks"][0],
                    **{f"rewards_{name}": state.info["reward_components"][name][0] for name in ("extrinsic", "intrinsic", "shaping")},
                )
            )
        )
        handoff = state.info["intrinsic_transition"]
        equal(handoff.context.predecessor, previous)
        equal(handoff.context.active_on_entry, LIVE)
        equal(handoff.stamp.eligible, LIVE)
        assert handoff.context.vector_tick == tick
        assert rig.population.replay_buffer.retained_transitions == tick
        assert len(calls["reward"]) == len(calls["service"]) == tick
        reward_args, _ = calls["reward"][-1]
        service_args, _ = calls["service"][-1]
        for args in (reward_args, service_args):
            assert args["context"] is handoff.context and args["stamp"] is handoff.stamp and args["accepted"] is rig.record.accepted
        equal(state.rewards[1:], torch.zeros(7))
        for component in ("extrinsic", "intrinsic", "shaping"):
            equal(state.info["reward_components"][component][1:], torch.zeros(7))
    assert selected == [((1, rig.env.action_dim), (1, rig.env.observation_dim), (1, rig.env.action_dim))] * 2
    ledger = rig.population.clock_ledger
    assert ledger.vector_ticks == ledger.eligible_transitions == 2
    assert ledger.optimizer_updates == rig.population.training_step_counter == 1
    assert any(not torch.equal(value, q_before[key]) for key, value in rig.population.q_network.state_dict().items())
    batch = rig.population.replay_buffer.sample_batch(ReplayRequest(2, 1, 2, "uniform_without_replacement", "feedforward", "transition"))
    assert batch.observations.shape == (2, rig.env.observation_dim)
    assert batch.next_action_masks.shape == (2, rig.env.action_dim)
    assert bool(batch.rewards_extrinsic_present.all()) and bool(batch.rewards_intrinsic_present.all())
    assert set(batch.unit_ids.tolist()) == {0, 1}
    for field in expected[0]:
        equal(getattr(batch, field), torch.stack([row[field] for row in expected])[batch.unit_ids])
    for name in ("extrinsic", "intrinsic", "shaping"):
        assert bool(getattr(batch, f"rewards_{name}_present").all())
    assert bool(batch.legality_recorded.all()) and bool(batch.loss_mask.all())
    after = rig.runtime.checkpoint_state()
    b_after = next(world for world in after["bank"]["worlds"] if world["world_id"] == IDS[1])
    equal(b_after["backend"], b_before["backend"])
    equal(b_after["gradients"], b_before["gradients"])
    assert b_after["cursor"]["eligible_seq"] == 0 and b_after["cursor"]["participated"] is False
    equal(rig.population.episode_step_counts, torch.tensor([2, 0, 0, 0, 0, 0, 0, 0]))
    assert rig.population.episode_completions[1] is None
    assert not bool(rig.population._episode_entropy_present[1:].any())
    equal(rig.population._episode_reward_totals[1:], torch.zeros((7, 4), dtype=torch.float64))
    prepared = prepare_close(rig)
    assert len(prepared[3]) == 1 and prepared[3][0].world_id == IDS[0]
    assert prepared[3][0].outcome.survival_time == 2
    assert freeze_lane_outcome(prepared[3][0]).to_outcome().world_id == IDS[0]
    retirement = close(rig, prepared, release=True)
    assert dict(retirement.dispositions)[IDS[1]] == "retired_nonparticipating"
    assert tuple(world for world, _ in retirement.dispositions) == IDS
    completed = rig.runtime.checkpoint_state()
    assert tuple(completed["bank"]["completion"]["participated_world_ids"]) == (IDS[0],)
    assert rig.population.clock_ledger.completed_batch_episodes == 1
    begin(rig, (), batch=1)
    assert rig.record.accepted.world_episode_seqs == (2,) * len(IDS)
    assert rig.env.global_tick == 0 and rig.population.total_steps == 2
    equal(rig.env.dones, torch.zeros(len(IDS), dtype=torch.bool))
    next_state = rig.population.step_population(rig.env)
    assert bool(next_state.info["active_on_entry"].all())
    assert rig.population.total_steps == 3 and rig.population.episode_step_counts[1].item() == 1


@pytest.mark.parametrize("kind", ("step", "greedy", "0.5", "prepare", "claim"))
@pytest.mark.parametrize("damage", ("observation", "activity", "counts", "physical"))
def test_owned_corruption_refuses_before_q_replay_curriculum_rng(compiled: Any, monkeypatch: Any, kind: str, damage: str) -> None:
    rig, foreign = make_parent(compiled), unowned(compiled)
    begin(rig)
    candidate = rig.candidate()
    prepared = rig.population.prepare_vector_step(**candidate) if kind == "claim" else None
    if damage == "observation":
        rig.population.current_obs.add_(1)
        rig.env.meters.add_(1)
    elif damage == "activity":
        rig.population.episode_completed[1] = False
        rig.env.dones[1] = False
    elif damage == "counts":
        rig.population.episode_step_counts[1] = rig.env.step_counts[1] = 1
    else:
        rig.env.positions.add_(1)
    calls = forbid_effects(monkeypatch, rig)
    rng = torch.get_rng_state().clone()
    with pytest.raises(REFUSAL):
        if kind == "step":
            rig.population.step_population(rig.env)
        elif kind == "prepare":
            rig.population.prepare_vector_step(**rig.candidate())
        elif kind == "claim":
            rig.population.claim_vector_step(prepared=prepared, **candidate)
        else:
            select(rig.population, foreign.env, kind)
    assert calls == []
    equal(torch.get_rng_state(), rng)
    assert rig.population.total_steps == rig.env.global_tick == 0


@pytest.mark.parametrize("kind", ("greedy", "0.0", "1.0", "0.5"))
def test_unowned_inference_preserves_legal_actions_q_display_and_lifetime(compiled: Any, kind: str) -> None:
    rig = unowned(compiled)
    before = (rig.population.total_steps, asdict(rig.population.clock_ledger), rig.population.replay_buffer.retained_transitions)
    masks = rig.env.get_action_masks()
    for _ in range(3):
        actions = select(rig.population, rig.env, kind)
        assert actions.shape == (len(IDS),) and actions.dtype == torch.int64
        assert bool(masks.gather(1, actions[:, None]).all())
        assert rig.population.last_selected_q_values.shape == masks.shape
    assert rig.population.max_episodes is None and rig.population.max_steps_per_episode is None
    assert (rig.population.total_steps, asdict(rig.population.clock_ledger), rig.population.replay_buffer.retained_transitions) == before
    assert rig.env.world_phase == "active-awaiting-activation"


@pytest.mark.parametrize("owned", (False, True))
@pytest.mark.parametrize("kind", ("greedy", "0.0", "1.0", "0.5"))
@pytest.mark.parametrize("invalid", ("geometry", "empty"))
def test_compatible_foreign_masks_keep_their_effect_without_changing_episode_authority(
    compiled: Any, monkeypatch: Any, owned: bool, kind: str, invalid: str
) -> None:
    rig, foreign = make_parent(compiled) if owned else unowned(compiled), unowned(compiled)
    if owned:
        begin(rig)
    masks = foreign.env.get_action_masks()
    own = rig.population.select_greedy_actions(rig.env)
    alternatives = masks.clone().scatter_(1, own[:, None], False)
    assert bool(alternatives.any(dim=1).all())
    chosen = alternatives.long().argmax(dim=1)
    forced = torch.zeros_like(masks).scatter_(1, chosen[:, None], True)
    monkeypatch.setattr(foreign.env, "get_action_masks", lambda: forced.clone())
    actions = select(rig.population, foreign.env, kind)
    eligible = LIVE if owned else torch.ones(len(IDS), dtype=torch.bool)
    assert bool((chosen[eligible] != own[eligible]).all())
    equal(actions[eligible], chosen[eligible])
    if owned:
        equal(rig.population.episode_completed, ~LIVE)
    assert rig.population.total_steps == 0
    bad = forced[:-1] if invalid == "geometry" else torch.zeros_like(forced)
    monkeypatch.setattr(foreign.env, "get_action_masks", lambda: bad)
    errors = (ValueError, RuntimeError, IndexError) if invalid == "geometry" else REFUSAL
    with pytest.raises(errors):
        select(rig.population, foreign.env, kind)


@pytest.mark.parametrize("kind", ("greedy", "0.5"))
def test_owned_reading_survives_healthy_phases_without_granting_physics(compiled: Any, monkeypatch: Any, kind: str) -> None:
    rig = make_parent(compiled)
    committed = capture_participation(monkeypatch, rig)

    def refuse_physics() -> None:
        candidate = rig.candidate()
        before = rig.population.total_steps, rig.env.global_tick
        with monkeypatch.context() as observers:
            calls = forbid_effects(observers, rig)
            operations = (
                lambda: rig.env.validate_initial_participation(
                    accepted=rig.record.accepted, participation=committed[0], predecessor=rig.population.current_obs
                ),
                lambda: rig.population.step_population(rig.env),
                lambda: rig.population.prepare_vector_step(**candidate),
            )
            for operation in operations:
                rng = torch.get_rng_state().clone()
                with pytest.raises(REFUSAL):
                    operation()
                assert calls == []
                equal(torch.get_rng_state(), rng)
                assert (rig.population.total_steps, rig.env.global_tick) == before

    _, activation = begin(rig, active=False)
    select(rig.population, rig.env, kind)
    refuse_physics()
    activate(rig, activation)
    rig.population.step_population(rig.env)
    select(rig.population, rig.env, kind)
    prepared = prepare_close(rig)
    close(rig, prepared, release=False)
    assert rig.env.world_phase == "closed-awaiting-release"
    for install in (False, True):
        if install:
            rig.env.install_boundary_release(rig.release)
            assert rig.env.world_phase == "released-completed"
        actions = select(rig.population, rig.env, kind)
        assert actions.shape == (len(IDS),)
        refuse_physics()
    assert rig.population.total_steps == rig.env.global_tick == 1


def test_pending_genuine_step_blocks_the_completion_needed_to_change_reading_phase(compiled: Any) -> None:
    rig = make_parent(compiled)
    begin(rig)
    rig.population.step_population(rig.env)
    candidate = rig.candidate()
    prepared = rig.population.prepare_vector_step(**candidate)
    with pytest.raises(REFUSAL):
        rig.population.flush_episode(0, reason="budget")
    assert rig.population.episode_completions[0] is None
    assert not bool(rig.population.episode_completed[0]) and rig.env.world_phase == "active"
    assert rig.population.claim_vector_step(prepared=prepared, **candidate) == 2
    assert rig.population.total_steps == rig.env.global_tick == 1


@pytest.mark.parametrize("where", ("reset", "finalization", "prepared_step", "close_frozen", "failed"))
def test_pending_and_failed_custody_cannot_use_unowned_inference(compiled: Any, monkeypatch: Any, where: str) -> None:
    rig, foreign = make_parent(compiled), unowned(compiled)
    hits: list[str] = []

    def refuse_selection() -> None:
        previous_q = rig.population.last_selected_q_values
        for kind in ("greedy", "0.5"):
            rng = torch.get_rng_state().clone()
            with pytest.raises(REFUSAL):
                select(rig.population, foreign.env, kind)
            equal(torch.get_rng_state(), rng)
        assert rig.population.last_selected_q_values is previous_q
        hits.append(where)

    if where == "reset":
        prepare = rig.env.prepare_initial_participation

        def during_reset(**kwargs: Any) -> Any:
            refuse_selection()
            return prepare(**kwargs)

        monkeypatch.setattr(rig.env, "prepare_initial_participation", during_reset)
        begin(rig)
    elif where == "finalization":
        issue = WorldReceiptIssuer.issue

        def during_issue(issuer: Any, *, kind: str, payload: Any) -> Any:
            if issuer.owner is rig.population and kind == "activation":
                refuse_selection()
            return issue(issuer, kind=kind, payload=payload)

        monkeypatch.setattr(WorldReceiptIssuer, "issue", during_issue)
        begin(rig)
    else:
        begin(rig)
        if where == "prepared_step":
            rig.population.prepare_vector_step(**rig.candidate())
        elif where == "close_frozen":
            rig.population.step_population(rig.env)
            rig.env.freeze_episode_close(prepare_close(rig)[0])
            assert rig.env.world_phase == "boundary-pending"
        else:
            rig.env.abandon_episode(accepted=rig.record.accepted, reason="runtime_failure")
        calls = forbid_effects(monkeypatch, rig)
        refuse_selection()
        assert calls == []
    assert hits == [where]


def test_postpublication_activation_failure_quarantines_without_reusable_reset(compiled: Any, monkeypatch: Any) -> None:
    rig = make_parent(compiled)
    reservation = reserve(rig)
    committed = capture_participation(monkeypatch, rig)
    issue = WorldReceiptIssuer.issue

    def fail_activation(issuer: Any, *, kind: str, payload: Any) -> Any:
        if issuer.owner is rig.population and kind == "activation":
            assert len(committed) == 1
            raise MemoryError("activation allocation after paired publication")
        return issue(issuer, kind=kind, payload=payload)

    monkeypatch.setattr(WorldReceiptIssuer, "issue", fail_activation)
    with pytest.raises(MemoryError, match="after paired publication"):
        rig.population.reset(reservation=reservation, retired_world_ids=RETIRED)
    assert rig.env.world_phase == "quarantined"
    with pytest.raises(REFUSAL):
        rig.population.reset(reservation=reservation, retired_world_ids=RETIRED)
    assert len(committed) == 1 and rig.population.total_steps == 0


@pytest.mark.parametrize("kind", ("greedy", "0.5"))
@pytest.mark.parametrize("raises", (False, True))
def test_mutating_foreign_mask_callback_stops_selection_after_its_real_q_effects(
    compiled: Any, monkeypatch: Any, kind: str, raises: bool
) -> None:
    rig, foreign = make_parent(compiled), unowned(compiled)
    begin(rig)
    mask_read, q_calls = foreign.env.get_action_masks, []
    fault = ValueError("foreign mask callback failed after mutation")
    rollout = rig.population._rollout_q

    def observe(eligible: Any) -> Any:
        q_calls.append(None)
        return rollout(eligible)

    def mutate() -> Any:
        masks = mask_read()
        rig.population.current_obs.add_(1)
        if raises:
            raise fault
        return masks

    monkeypatch.setattr(rig.population, "_rollout_q", observe)
    monkeypatch.setattr(foreign.env, "get_action_masks", mutate)
    rng = torch.get_rng_state().clone()
    with pytest.raises(REFUSAL) as error:
        select(rig.population, foreign.env, kind)
    if raises:
        assert error.value is fault
    assert q_calls == [None]
    equal(torch.get_rng_state(), rng)
    assert rig.population.total_steps == 0
    assert rig.env.world_phase == "quarantined"
    assert rig.population._failed_step and rig.population._activation is None
    with pytest.raises(REFUSAL):
        rig.population.get_checkpoint_state()


@pytest.mark.parametrize("damage", ("observation", "status"))
def test_finalization_read_cannot_publish_activation_after_mutating_pop_state(compiled: Any, monkeypatch: Any, damage: str) -> None:
    rig = make_parent(compiled)
    reservation = reserve(rig)
    reading, visits = rig.env.validate_initial_participation_reading, []

    def mutate(**kwargs: Any) -> Any:
        result = reading(**kwargs)
        visits.append(None)
        if damage == "observation":
            rig.population.current_obs.add_(1)
        else:
            rig.population.episode_completed[1] = False
        return result

    monkeypatch.setattr(rig.env, "validate_initial_participation_reading", mutate)
    with pytest.raises(REFUSAL):
        rig.population.reset(reservation=reservation, retired_world_ids=RETIRED)
    assert visits == [None] and rig.env.world_phase == "quarantined"
    assert rig.population._failed_step and rig.population._activation is None
    with pytest.raises(REFUSAL):
        rig.population.reset(reservation=reservation, retired_world_ids=RETIRED)
    assert visits == [None] and rig.population.total_steps == rig.env.global_tick == 0


def test_current_initial_boundary_restore_does_not_import_live_decision_authority(compiled: Any) -> None:
    source, target = make_parent(compiled), make_parent(compiled)
    state = copy.deepcopy(source.population.get_checkpoint_state())
    target.population.load_checkpoint_state(state)
    begin(target)
    equal(target.env.dones, ~LIVE)
    with pytest.raises(REFUSAL):
        target.population.load_checkpoint_state(state)
    assert target.population.total_steps == 0


@pytest.mark.parametrize("epsilon", (0.0, 0.5, 1.0))
def test_public_epsilon_preserves_existing_helper_arguments_results_and_draws(compiled: Any, monkeypatch: Any, epsilon: float) -> None:
    rig = unowned(compiled)
    helper = population_module.epsilon_greedy_action_selection_eligible
    captured = []

    def observe(**kwargs: Any) -> Any:
        captured.append((kwargs, torch.get_rng_state().clone()))
        return helper(**kwargs)

    monkeypatch.setattr(population_module, "epsilon_greedy_action_selection_eligible", observe)
    result = rig.population.select_epsilon_greedy_actions(rig.env, epsilon)
    after = torch.get_rng_state().clone()
    assert len(captured) == 1
    arguments, entry = captured[0]
    equal(arguments["epsilons"], torch.full((len(IDS),), epsilon))
    equal(arguments["q_values"], rig.population.last_selected_q_values)
    torch.set_rng_state(entry)
    try:
        equal(result, helper(**arguments))
        equal(torch.get_rng_state(), after)
    finally:
        torch.set_rng_state(after)


def test_reading_identity_refuses_copies_foreign_records_and_stale_generation(compiled: Any, monkeypatch: Any) -> None:
    rig, foreign = make_parent(compiled), make_parent(compiled)
    records, other = capture_participation(monkeypatch, rig), capture_participation(monkeypatch, foreign)
    begin(rig)
    begin(foreign)
    for record in (copy.copy(records[0]), other[0]):
        with pytest.raises(REFUSAL):
            rig.env.validate_initial_participation_reading(
                accepted=rig.record.accepted, participation=record, predecessor=rig.population.current_obs
            )
    rig.population.step_population(rig.env)
    close(rig, prepare_close(rig), release=True)
    accepted, record = rig.record.accepted, records[0]
    begin(rig, (), batch=1)
    with pytest.raises(REFUSAL):
        rig.env.validate_initial_participation_reading(accepted=accepted, participation=record, predecessor=rig.population.current_obs)
    equal(rig.env.dones, torch.zeros(len(IDS), dtype=torch.bool))


def test_native_install_custody_blocks_unowned_selector_reentry(compiled: Any, monkeypatch: Any) -> None:
    source, target, masks = make_parent(compiled), make_parent(compiled), unowned(compiled)
    prepared = target.population.prepare_checkpoint_state(
        source.population.get_checkpoint_state(), mode="initial", parent_restore=None, validate_parent_restore=None, initialization=None
    )
    install, visits = target.runtime.install_restore, []

    def observe(**kwargs: Any) -> None:
        for kind in ("greedy", "0.5"):
            with pytest.raises(REFUSAL):
                select(target.population, masks.env, kind)
        assert target.population.last_selected_q_values is None
        visits.append(None)
        install(**kwargs)

    monkeypatch.setattr(target.runtime, "install_restore", observe)
    target.population.install_checkpoint_state(prepared=prepared)
    assert visits == [None] and target.population.total_steps == 0


def test_reset_prepublication_state_mutation_fails_closed_without_an_activation(compiled: Any, monkeypatch: Any) -> None:
    rig = make_parent(compiled)
    reservation = reserve(rig)
    prepare, activations = rig.env.prepare_initial_participation, []
    issue = WorldReceiptIssuer.issue

    def mutate(**kwargs: Any) -> Any:
        result = prepare(**kwargs)
        rig.population.current_obs.add_(1)
        return result

    def observe(issuer: Any, *, kind: str, payload: Any) -> Any:
        if issuer.owner is rig.population and kind == "activation":
            activations.append(None)
        return issue(issuer, kind=kind, payload=payload)

    monkeypatch.setattr(rig.env, "prepare_initial_participation", mutate)
    monkeypatch.setattr(WorldReceiptIssuer, "issue", observe)
    with pytest.raises(REFUSAL):
        rig.population.reset(reservation=reservation, retired_world_ids=RETIRED)
    assert rig.env.world_phase == "quarantined" and not activations
    assert rig.population.total_steps == rig.env.global_tick == 0


@pytest.fixture(scope="module")
def recurrent_compiled() -> Any:
    return UniverseCompiler().compile(Path("configs/test/bac_remediation/recurrent"), primary_level="L0_0_minimal", use_cache=False)


@pytest.mark.parametrize("owned", (False, True))
@pytest.mark.parametrize("kind", ("greedy", "0.5"))
def test_recurrent_reading_keeps_one_forward_hidden_advance_and_q_display(recurrent_compiled: Any, owned: bool, kind: str) -> None:
    rig = make_parent(recurrent_compiled) if owned else unowned(recurrent_compiled)
    if owned:
        begin(rig)
    pop = rig.population
    assert pop.is_recurrent
    mode, outputs = pop.q_network.training, []

    def capture(module: Any, inputs: Any, output: Any) -> None:
        values, hidden = output
        assert not values.requires_grad
        outputs.append((values.detach().clone(), tuple(value.detach().clone() for value in hidden)))

    hook = pop.q_network.register_forward_hook(capture)
    try:
        for index in range(2):
            before = tuple(value.clone() for value in pop.rollout_hidden)
            actions = select(pop, rig.env, kind)
            assert len(outputs) == index + 1
            values, hidden = outputs[-1]
            equal(pop.last_selected_q_values, values[:, 0])
            eligible = LIVE if owned else torch.ones(len(IDS), dtype=torch.bool)
            for actual, produced, previous in zip(pop.rollout_hidden, hidden, before, strict=True):
                equal(actual[:, eligible], produced[:, eligible])
                equal(actual[:, ~eligible], previous[:, ~eligible])
            assert any(not torch.equal(actual[:, eligible], previous[:, eligible]) for actual, previous in zip(pop.rollout_hidden, before))
            assert actions.shape == (len(IDS),) and pop.q_network.training is mode
    finally:
        hook.remove()
    assert pop.total_steps == rig.env.global_tick == 0


def test_whole_retirement_uses_genuine_empty_owner_proofs_and_abandonment(compiled: Any, monkeypatch: Any) -> None:
    rig = make_parent(compiled, "rnd", "per_world")
    calls = observe_runtime(monkeypatch, rig)
    begin(rig, IDS)
    before = reading(rig)
    assert bool(rig.population.episode_completed.all()) and bool(rig.env.dones.all())
    assert not bool(rig.env.get_action_masks().any())
    assert rig.population.episode_completions == [None] * len(IDS)
    assert rig.population.completed_outcomes == ()
    for owner in (rig.population, rig.runtime):
        proof = owner.prepare_empty_episode_evidence(accepted=rig.record.accepted)
        assert proof.accepted is rig.record.accepted
        assert proof.participated_world_ids == () and proof.events == ()
    with pytest.raises(REFUSAL):
        rig.population.step_population(rig.env)
    assert calls == {"reward": [], "service": []}
    equal(reading(rig), before)
    with monkeypatch.context() as attack:
        attack.setattr(rig.bank, "prepare_empty_episode_evidence", rig.population.prepare_empty_episode_evidence)
        with pytest.raises(REFUSAL):
            rig.env.abandon_episode(accepted=rig.record.accepted, reason="empty_participation")
    assert rig.env.world_phase == "active"
    rig.env.abandon_episode(accepted=rig.record.accepted, reason="empty_participation")
    assert rig.env.world_phase == "quarantined"
    assert rig.population.total_steps == rig.env.global_tick == 0
    assert all(value == 0 for value in asdict(rig.population.clock_ledger).values())
    assert rig.population.replay_buffer.retained_transitions == 0 and rig.population.completed_outcomes == ()
