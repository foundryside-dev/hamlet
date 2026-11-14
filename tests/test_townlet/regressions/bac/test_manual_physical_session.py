"""Real manual physical operations, independent of the fixture's BANK events.

The imported fixture supplies only its real constructors/begin/close/event APIs;
its obsolete physical ``Rig.step`` is deliberately never called.
"""

from __future__ import annotations

import copy
import os
import pickle
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from tests.test_townlet.regressions.bac.test_parent_intrinsic_handoff import make_parent
from tests.test_townlet.regressions.bac.test_pw_scope_conversion import (
    BaCOptions,
    CuriosityBank,
    IntrinsicStrategyConfig,
    Rig,
    TrainingV2Config,
    WorldCuriosityDescriptor,
    policy,
    resolve_exploration_policy,
    service,
)
from townlet.config.world_roster import WorldRosterDeclaration
from townlet.environment import manual_physical
from townlet.environment.vectorized_env import VectorizedHamletEnv, WorldReceiptIssuer
from townlet.universe.compiler import UniverseCompiler


@pytest.fixture(scope="module")
def compiled():
    return UniverseCompiler().compile(Path("configs/test/token_set_smoke"), primary_level="L0_test", use_cache=False)


def bind(rig):
    factory = getattr(rig.env, "bind_manual_execution", None)
    assert callable(factory), "ENV must issue an authentic manual physical session"
    return factory(population_owner=rig)


def actions(rig):
    return rig.env.get_action_masks().to(torch.int64).argmax(dim=1)


def advance(rig, session):
    return session.step(accepted=rig.accepted, actions=actions(rig), depletion_multiplier=1.0)


def pending_items(scheduler):
    return tuple(item for bucket in scheduler.pending.values() for item in bucket)


def retire_initially(rig, retired):
    """The actual local population owns its reset reading and issued intent."""
    rig.manual_population_revision = 0
    assert rig.manual_reset_reading.shape == (rig.env.num_agents, rig.env.observation_dim)
    rig.manual_intent = rig.issuer.issue(
        kind="initial_participation_intent",
        payload={
            "accepted": rig.accepted,
            "world_ids": rig.env.world_ids,
            "retired_world_ids": retired,
            "population_revision": rig.manual_population_revision,
        },
    )
    prepared = rig.env.prepare_initial_participation(accepted=rig.accepted, intent=rig.manual_intent)
    ready = rig.issuer.issue(
        kind="initial_participation_ready",
        payload={
            "accepted": rig.accepted,
            "intent": rig.manual_intent,
            "prepared": prepared,
            "population_revision": rig.manual_population_revision,
        },
    )
    return rig.env.commit_initial_participation(prepared=prepared, population_ready=ready)


def begin_with_retirement(rig, retired):
    release = rig.authority.bootstrap(first_batch_episode=0)
    rig.release = rig.env.install_boundary_release(release)
    reservation = rig.env.prepare_episode(batch_episode=0, release=rig.release)
    reset = rig.env.reset(reservation=reservation)
    rig.manual_reset_reading = reset.observation
    rig.accepted = reset.accepted
    participation = retire_initially(rig, retired)
    population = rig.issuer.issue(kind="activation", payload={"accepted": rig.accepted})
    curiosity = rig.bank.begin_episode(accepted=rig.accepted)
    rig.env.activate_episode(accepted=rig.accepted, population_receipt=population, curiosity_receipt=curiosity)
    return participation


@pytest.mark.parametrize(
    ("ids", "membership", "seed"),
    [(("A", "B"), ("A", "B"), 701), (("B", "A"), ("A", "B"), 702), (("A", "B", "C", "D", "E"), ("A", "B", "C", "D", "E"), 703)],
)
def test_real_manual_step_uses_actual_roster_and_returns_owned_physical_state(compiled, ids, membership, seed):
    """A skipped kernel, reordered lanes or live result aliases break this."""
    rig = Rig(compiled, policy(compiled, "rnd", "per_world", "paced_fifo"), ids=ids, membership=membership, seed=seed)
    session = bind(rig)
    assert rig.env.world_phase == "fresh-bound"
    rig.begin(0)
    result = advance(rig, session)
    assert result.accepted is rig.accepted
    assert result.physical_tick == 1
    assert result.receipt.accepted is rig.accepted
    assert result.receipt.world_ids == ids
    assert result.receipt.physical_tick == 1
    assert result.receipt.step_counts.tolist() == [1] * len(ids)
    assert rig.env.step_counts.tolist() == [1] * len(ids)
    assert rig.env.global_tick == 1
    assert result.observations.shape == (len(ids), rig.env.observation_dim)
    assert "intrinsic_transition" not in result.info
    before = rig.env.meters.clone(), rig.env.dones.clone(), rig.env.positions.clone()
    result.observations.fill_(123)
    result.rewards.fill_(123)
    result.dones.fill_(True)
    result.info["step_counts"].fill_(123)
    result.info["positions"].fill_(123)
    result.receipt.step_counts.fill_(123)
    assert torch.equal(rig.env.meters, before[0])
    assert torch.equal(rig.env.dones, before[1])
    assert torch.equal(rig.env.positions, before[2])
    assert result.receipt.step_counts.tolist() == [1] * len(ids)
    assert advance(rig, session).physical_tick == 2
    assert rig.env.step_counts.tolist() == [2] * len(ids)


def test_manual_physics_keeps_real_dac_without_creating_a_bank_event(compiled, monkeypatch):
    """Dropping DAC, changing its temporal input, or touching BANK fails."""
    rig = Rig(compiled, policy(compiled, "rnd", "per_world", "paced_fifo"))
    session = bind(rig)
    rig.begin(0)
    applied = []
    original = rig.env.vtc_reward_program.apply
    original_hour = rig.env.time_of_day

    def observe(program, **kwargs):
        result = original(**kwargs)
        applied.append((kwargs, result[0].detach().clone()))
        return result

    def unexpected(**kwargs):
        pytest.fail("a manual physical vector must not call BANK reward/stamp/service")

    monkeypatch.setattr(type(rig.env.vtc_reward_program), "apply", observe)
    for name in ("prepare_step_stamp", "reward", "admit_and_service"):
        monkeypatch.setattr(rig.bank, name, unexpected)
    result = advance(rig, session)
    assert len(applied) == 1
    kwargs, shaped = applied[0]
    assert kwargs["reward_backend"] is rig.env.dac_engine
    assert kwargs["intrinsic_raw"].shape == (2,)
    assert kwargs["runtime_intrinsic_scale"].shape == (2,)
    assert kwargs["intrinsic_raw"].dtype == rig.env.meters.dtype
    assert kwargs["intrinsic_raw"].device == rig.env.device
    assert torch.equal(kwargs["intrinsic_raw"], torch.zeros(2))
    assert torch.equal(kwargs["runtime_intrinsic_scale"], torch.zeros(2))
    if rig.env.enable_temporal_mechanics:
        assert kwargs["reward_context"]["current_hour"].item() == original_hour
    bonus = result.info["newly_retired"].to(shaped.dtype)
    assert torch.equal(result.rewards, shaped + bonus)
    assert torch.equal(result.info["reward_components"]["intrinsic"], torch.zeros(2))
    assert rig.env.global_tick == 1


def test_initial_retirement_is_genuine_and_zero_count_world_stays_inactive(compiled):
    """Initial retirement must use the issued participation decision."""
    rig = Rig(compiled, policy(compiled, "rnd", "per_world", "paced_fifo"))
    session = bind(rig)
    participation = begin_with_retirement(rig, ("B",))
    result = advance(rig, session)
    assert result.info["active_on_entry"].tolist() == [True, False]
    assert result.info["step_counts"].tolist() == [1, 0]
    assert result.dones.tolist() == [False, True]
    assert result.rewards[1].item() == 0
    rig.env.validate_initial_participation(accepted=rig.accepted, participation=participation, predecessor=result.observations)
    assert advance(rig, session).info["step_counts"].tolist() == [2, 0]


def test_between_vector_retirement_leaves_four_b_effects_and_five_a_effects(compiled, monkeypatch):
    """Retirement cannot execute an extra vector/reward or revive B."""
    rig = Rig(compiled, policy(compiled, "rnd", "shared", "paced_fifo"))
    session = bind(rig)
    rig.begin(0)
    for tick in range(1, 5):
        assert advance(rig, session).physical_tick == tick
    before = rig.env.global_tick, rig.env.step_counts.clone(), rig.env.meters.clone()
    original = rig.env.vtc_reward_program.apply

    def forbidden_reward(program, **kwargs):
        pytest.fail("between-vector retirement cannot calculate a reward")

    monkeypatch.setattr(type(rig.env.vtc_reward_program), "apply", forbidden_reward)
    receipt = session.retire(accepted=rig.accepted, world_ids=("B",), reason="cap")
    assert receipt.accepted is rig.accepted
    assert receipt.world_ids == ("B",)
    assert receipt.physical_tick == 4
    assert rig.env.global_tick == before[0]
    assert torch.equal(rig.env.step_counts, before[1])
    assert torch.equal(rig.env.meters, before[2])
    assert rig.env.dones.tolist() == [False, True]
    with pytest.raises(ValueError):
        session.retire(accepted=rig.accepted, world_ids=("B",), reason="cap")
    monkeypatch.setattr(type(rig.env.vtc_reward_program), "apply", lambda program, **kwargs: original(**kwargs))
    result = advance(rig, session)
    assert result.physical_tick == 5
    assert result.info["active_on_entry"].tolist() == [True, False]
    assert result.info["step_counts"].tolist() == [5, 4]
    assert result.rewards[1].item() == 0


@pytest.mark.parametrize(
    "retired,reason",
    [((), "cap"), (("B", "A"), "cap"), (("B", "B"), "cap"), (("foreign",), "cap"), (("B",), "checkpoint")],
)
def test_retirement_input_refusals_leave_next_physical_step_healthy(compiled, retired, reason):
    rig = Rig(compiled, policy(compiled, "none", "shared", "paced_fifo"))
    session = bind(rig)
    rig.begin(0)
    advance(rig, session)
    with pytest.raises(ValueError):
        session.retire(accepted=rig.accepted, world_ids=retired, reason=reason)
    assert rig.env.step_counts.tolist() == [1, 1]
    assert not bool(rig.env.dones.any())
    assert advance(rig, session).physical_tick == 2


def test_retirement_before_first_vector_cannot_replace_initial_participation(compiled):
    rig = Rig(compiled, policy(compiled, "none", "shared", "paced_fifo"))
    session = bind(rig)
    rig.begin(0)
    with pytest.raises(ValueError):
        session.retire(accepted=rig.accepted, world_ids=("B",), reason="cap")
    assert rig.env.step_counts.tolist() == [0, 0]
    assert advance(rig, session).info["active_on_entry"].tolist() == [True, True]


def test_wrong_owner_late_binding_and_duplicate_binding_refuse(compiled):
    rig = Rig(compiled, policy(compiled, "none", "shared", "paced_fifo"))
    factory = getattr(rig.env, "bind_manual_execution", None)
    assert callable(factory), "ENV must issue an authentic manual physical session"
    with pytest.raises(ValueError):
        factory(population_owner=object())
    session = bind(rig)
    with pytest.raises(ValueError):
        bind(rig)
    rig.begin(0)
    with pytest.raises(ValueError):
        bind(rig)
    assert advance(rig, session).physical_tick == 1


def test_ordinary_population_binding_remains_exclusive_and_integrated(compiled, monkeypatch):
    """A manual binding must never displace the real POP runtime/claim."""
    rig = make_parent(compiled, family="none", scope="shared")
    factory = getattr(rig.env, "bind_manual_execution", None)
    assert callable(factory), "ENV must expose the manual binding refusal contract"
    original = rig.env.bind_boundary_authority
    checked = []

    def observe(**kwargs):
        authority = original(**kwargs)
        assert rig.env.world_phase == "fresh-bound"
        with pytest.raises(ValueError):
            factory(population_owner=rig.population)
        checked.append(True)
        return authority

    monkeypatch.setattr(rig.env, "bind_boundary_authority", observe)
    rig.enter()
    assert checked == [True]
    state = rig.population.step_population(rig.env)
    assert "intrinsic_transition" in state.info
    assert rig.env.global_tick == 1
    assert rig.env.step_counts.tolist() == [1] * 8


def test_unactivated_reset_and_empty_participation_cannot_advance(compiled):
    rig = Rig(compiled, policy(compiled, "none", "shared", "paced_fifo"))
    session = bind(rig)
    rig.release = rig.env.install_boundary_release(rig.authority.bootstrap(first_batch_episode=0))
    reservation = rig.env.prepare_episode(batch_episode=0, release=rig.release)
    reset = rig.env.reset(reservation=reservation)
    rig.accepted = reset.accepted
    rig.manual_reset_reading = reset.observation
    with pytest.raises(ValueError):
        advance(rig, session)
    retire_initially(rig, ("A", "B"))
    rig.env.activate_episode(
        accepted=rig.accepted,
        population_receipt=rig.issuer.issue(kind="activation", payload={"accepted": rig.accepted}),
        curiosity_receipt=rig.bank.begin_episode(accepted=rig.accepted),
    )
    with pytest.raises(ValueError):
        advance(rig, session)
    assert rig.env.global_tick == 0
    assert rig.env.step_counts.tolist() == [0, 0]


def test_session_and_physical_receipt_copies_cannot_gain_authority(compiled):
    rig = Rig(compiled, policy(compiled, "none", "shared", "paced_fifo"))
    session = bind(rig)
    rig.begin(0)
    for copier in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises((TypeError, ValueError)):
            copier(session)
    forged = object.__new__(type(session))
    with pytest.raises(ValueError):
        forged.step(accepted=rig.accepted, actions=actions(rig), depletion_multiplier=1.0)
    result = advance(rig, session)
    rig.env._valid_record(result.receipt, "manual_physical_step")
    with pytest.raises(ValueError):
        rig.env._valid_record(copy.copy(result.receipt), "manual_physical_step")
    assert rig.env.step_counts.tolist() == [1, 1]


@pytest.mark.parametrize("invalid", [torch.tensor([0.0, 0.0]), torch.tensor([0]), torch.tensor([-1, 0]), torch.tensor([100000, 0])])
def test_bad_actions_refuse_before_physical_effects(compiled, invalid):
    rig = Rig(compiled, policy(compiled, "none", "shared", "paced_fifo"))
    session = bind(rig)
    rig.begin(0)
    with pytest.raises((TypeError, ValueError)):
        session.step(accepted=rig.accepted, actions=invalid, depletion_multiplier=1.0)
    assert rig.env.global_tick == 0
    assert rig.env.step_counts.tolist() == [0, 0]
    assert advance(rig, session).physical_tick == 1


def test_foreign_accepted_refuses_without_consuming_current_session(compiled):
    rig = Rig(compiled, policy(compiled, "none", "shared", "paced_fifo"))
    other = Rig(compiled, policy(compiled, "none", "shared", "paced_fifo"))
    session = bind(rig)
    bind(other)
    rig.begin(0)
    other.begin(0)
    with pytest.raises(ValueError):
        session.step(accepted=other.accepted, actions=actions(rig), depletion_multiplier=1.0)
    assert rig.env.global_tick == 0
    assert advance(rig, session).physical_tick == 1


@pytest.mark.parametrize("stage", ["entered", "returned", "finish"])
def test_physical_or_finish_failure_preserves_primary_and_prevents_reexecution(compiled, monkeypatch, stage):
    """No post-entry error may leave an apparently healthy reusable session."""
    rig = Rig(compiled, policy(compiled, "none", "shared", "paced_fifo"))
    session = bind(rig)
    rig.begin(0)
    primary = RuntimeError("manual physical failure")
    original_record = rig.env._record

    def fail(*args, **kwargs):
        raise primary

    def fail_finish(kind, payload):
        if kind == "manual_physical_step":
            raise primary
        return original_record(kind, payload)

    if stage == "entered":
        monkeypatch.setattr(rig.env._action_executor, "_execute_actions", fail)
    elif stage == "returned":
        monkeypatch.setattr(rig.env, "_advance_participation_witness", fail)
    else:
        monkeypatch.setattr(rig.env, "_record", fail_finish)
    with pytest.raises(RuntimeError) as caught:
        advance(rig, session)
    assert caught.value is primary
    assert rig.env.world_phase == "quarantined"
    reached = rig.env.global_tick, rig.env.step_counts.clone()
    with pytest.raises(ValueError):
        session.step(accepted=rig.accepted, actions=torch.zeros(2, dtype=torch.int64), depletion_multiplier=1.0)
    assert rig.env.global_tick == reached[0]
    assert torch.equal(rig.env.step_counts, reached[1])


def test_cleanup_failure_is_a_note_and_cannot_replace_physical_primary(compiled, monkeypatch):
    rig = Rig(compiled, policy(compiled, "none", "shared", "paced_fifo"))
    session = bind(rig)
    rig.begin(0)
    primary, secondary = RuntimeError("physical finish failed"), RuntimeError("abandonment receipt failed")
    original = rig.env._record

    def fail(kind, payload):
        if kind == "manual_physical_step":
            raise primary
        if kind == "abandonment":
            raise secondary
        return original(kind, payload)

    monkeypatch.setattr(rig.env, "_record", fail)
    with pytest.raises(RuntimeError) as caught:
        advance(rig, session)
    assert caught.value is primary
    assert any("abandonment receipt failed" in note for note in primary.__notes__)
    assert rig.env.world_phase == "quarantined"


def test_reentrant_callback_cannot_enter_another_manual_vector(compiled, monkeypatch):
    rig = Rig(compiled, policy(compiled, "none", "shared", "paced_fifo"))
    session = bind(rig)
    rig.begin(0)
    original = rig.env._action_executor._execute_actions
    attempted = []

    def observe(actual_actions):
        with pytest.raises(ValueError):
            session.step(accepted=rig.accepted, actions=actual_actions, depletion_multiplier=1.0)
        with pytest.raises(ValueError):
            rig.env.get_action_masks()
        attempted.append(True)
        return original(actual_actions)

    monkeypatch.setattr(rig.env._action_executor, "_execute_actions", observe)
    assert advance(rig, session).physical_tick == 1
    assert attempted == [True]
    assert rig.env.step_counts.tolist() == [1, 1]


def test_wrong_thread_session_refuses_before_waiting_while_ordinary_env_reader_waits(compiled, monkeypatch):
    rig = Rig(compiled, policy(compiled, "none", "shared", "paced_fifo"))
    session = bind(rig)
    rig.begin(0)
    original = rig.env._action_executor._execute_actions
    refused, reader_started, reader_finished = threading.Event(), threading.Event(), threading.Event()
    errors, readers = [], []

    def wrong_thread():
        try:
            session.step(accepted=rig.accepted, actions=torch.zeros(2, dtype=torch.int64), depletion_multiplier=1.0)
        except ValueError:
            refused.set()
        except BaseException as exc:
            errors.append(exc)

    def ordinary_reader():
        reader_started.set()
        try:
            rig.env.get_action_masks()
        except BaseException as exc:
            errors.append(exc)
        finally:
            reader_finished.set()

    def observe(actual_actions):
        misuse = threading.Thread(target=wrong_thread, daemon=True)
        misuse.start()
        assert refused.wait(2), "wrong-thread session use must refuse before ENV lock work"
        misuse.join(2)
        reader = threading.Thread(target=ordinary_reader, daemon=True)
        readers.append(reader)
        reader.start()
        assert reader_started.wait(2)
        assert not reader_finished.wait(0.05), "ordinary reader must wait for the physical vector"
        return original(actual_actions)

    monkeypatch.setattr(rig.env._action_executor, "_execute_actions", observe)
    assert advance(rig, session).physical_tick == 1
    for reader in readers:
        reader.join(2)
    assert reader_finished.is_set()
    assert not errors


def test_sparse_bank_events_are_independent_of_sequential_physical_ticks(compiled):
    """Physical advancement must not reserve a hidden BANK event or clock."""
    rig = Rig(compiled, policy(compiled, "rnd", "per_world", "paced_fifo"))
    session = bind(rig)
    rig.begin(0)
    first = advance(rig, session)
    context1, stamp1, reward1, receipts1 = service(rig.bank, rig.accepted, 101, (True, False))
    second = advance(rig, session)
    context2, stamp2, reward2, receipts2 = service(rig.bank, rig.accepted, 401, (False, True))
    assert (first.physical_tick, second.physical_tick) == (1, 2)
    assert (context1.vector_tick, context2.vector_tick) == (101, 401)
    assert context1.predecessor.shape == context2.predecessor.shape == (2, 3)
    assert context1.active_on_entry.tolist() == [True, False]
    assert context2.active_on_entry.tolist() == [False, True]
    assert rig.env.step_counts.tolist() == [2, 2]
    # No physical observer changes the original BANK event's identity/cache.
    again = rig.bank.reward(context=context2, stamp=stamp2, accepted=rig.accepted, update_stats=True)
    assert torch.equal(again.raw, reward2.raw)


def test_initial_participation_witness_survives_positive_count_retirement(compiled):
    rig = Rig(compiled, policy(compiled, "none", "shared", "paced_fifo"))
    session = bind(rig)
    participation = begin_with_retirement(rig, ())
    for _ in range(4):
        advance(rig, session)
    session.retire(accepted=rig.accepted, world_ids=("B",), reason="cap")
    result = advance(rig, session)
    assert result.info["step_counts"].tolist() == [5, 4]
    rig.env.validate_initial_participation(accepted=rig.accepted, participation=participation, predecessor=result.observations)


def completed_source(compiled, monkeypatch=None):
    """Same real BANK learns from nine rows and closes its physical ENV."""
    rig = Rig(compiled, policy(compiled, "rnd", "shared", "paced_fifo"))
    session = bind(rig)
    rig.begin(0)
    last = None
    for tick in range(1, 6):
        if tick == 5:
            session.retire(accepted=rig.accepted, world_ids=("B",), reason="cap")
        last = advance(rig, session)
        service(rig.bank, rig.accepted, tick, (True, tick < 5))
    assert rig.env.step_counts.tolist() == [5, 4]
    if monkeypatch is not None:
        original = rig.env.prepare_episode_close

        def observe(**kwargs):
            prepared = original(**kwargs)
            with pytest.raises(ValueError):
                session.retire(accepted=rig.accepted, world_ids=("A",), reason="cap")
            with pytest.raises(ValueError):
                advance(rig, session)
            return prepared

        monkeypatch.setattr(rig.env, "prepare_episode_close", observe)
    rig.close()
    assert rig.env.world_phase == "released-completed"
    return rig, session, last


def test_genuine_nine_role_close_fences_work_and_next_episode_keeps_session_clock(compiled, monkeypatch):
    """Closure, not a fabricated step acknowledgement, releases the next reset."""
    rig, session, last = completed_source(compiled, monkeypatch)
    previous = rig.accepted
    assert rig.world_state()["last_closed_episode"]["participated_world_ids"] == ["A", "B"]
    with pytest.raises(ValueError):
        advance(rig, session)
    with pytest.raises(ValueError):
        session.retire(accepted=previous, world_ids=("A",), reason="cap")
    rig.begin(1)
    assert rig.accepted is not previous
    assert rig.accepted.world_episode_seqs == (2, 2)
    with pytest.raises(ValueError):
        session.step(accepted=previous, actions=actions(rig), depletion_multiplier=1.0)
    with pytest.raises(ValueError):
        rig.env._valid_record(last.receipt, "manual_physical_step")
    result = advance(rig, session)
    assert result.physical_tick == 6
    assert rig.env.global_tick == 1
    assert result.info["step_counts"].tolist() == [1, 1]


def test_fresh_bound_receiver_session_allows_completed_restore_but_history_cannot_step(compiled):
    """Restored last-closed accepted identity is not active physical authority."""
    source, _, _ = completed_source(compiled)
    state = source.world_state()
    receiver = Rig(compiled, policy(compiled, "rnd", "shared", "paced_fifo"), ids=("B", "A"))
    session = bind(receiver)
    prepared = receiver.env.prepare_world_restore(
        kind="COMPLETED",
        state=state,
        world_roster=receiver.roster,
        destination_world_ids=("B", "A"),
        semantic_execution_identity=receiver.env.semantic_execution_identity,
    )
    proof = receiver.issuer.issue(kind="restored_boundary", payload={"kind": "COMPLETED", "state": state, "prepared": prepared})
    release = receiver.authority.restored(restore=prepared, boundary=proof)
    receiver.env.install_world_restore(prepared=prepared, release=release)
    assert receiver.env.world_phase == "released-completed"
    historical = receiver.env._world_accepted
    assert historical is not None
    receiver.env.validate_accepted_episode(accepted=historical)
    with pytest.raises(ValueError):
        session.step(accepted=historical, actions=torch.zeros(2, dtype=torch.int64), depletion_multiplier=1.0)
    with pytest.raises(ValueError):
        session.retire(accepted=historical, world_ids=("A",), reason="cap")
    assert receiver.env.global_tick == 0
    assert receiver.env.step_counts.tolist() == [0, 0]


def test_retirement_cancels_real_pending_b_work_once_and_preserves_a_work(compiled, monkeypatch):
    """Real empty-command jobs prove cancellation routing, not command effects."""
    rig = Rig(compiled, policy(compiled, "none", "shared", "paced_fifo"))
    session = bind(rig)
    rig.begin(0)
    for _ in range(4):
        advance(rig, session)
    manager = rig.env.effect_manager
    assert manager is not None
    scheduler = manager.scheduler
    assert scheduler is not None
    assert not scheduler.pending
    scheduler.schedule(
        commands=(), delay_ticks=100, scope="agent", entity_id=0, context_overrides={}, base_tick=rig.env.global_tick, effect_instance=None
    )
    a_pending = pending_items(scheduler)
    assert len(a_pending) == 1
    a_item = a_pending[0]
    assert (a_item.scope, a_item.entity_id) == ("agent", 0)
    assert not a_item.commands
    scheduler.schedule(
        commands=(), delay_ticks=100, scope="agent", entity_id=1, context_overrides={}, base_tick=rig.env.global_tick, effect_instance=None
    )
    assert [(item.scope, item.entity_id) for item in pending_items(scheduler)] == [("agent", 0), ("agent", 1)]
    original = manager.cancel_scheduled_for_entity
    cancellations = []

    def observe(*, scope, entity_id):
        cancellations.append((scope, entity_id))
        return original(scope=scope, entity_id=entity_id)

    monkeypatch.setattr(manager, "cancel_scheduled_for_entity", observe)
    before = rig.env.global_tick, rig.env.step_counts.clone()
    session.retire(accepted=rig.accepted, world_ids=("B",), reason="cap")
    assert pending_items(scheduler) == a_pending
    assert pending_items(scheduler)[0] is a_item
    assert (a_item.scope, a_item.entity_id) == ("agent", 0)
    assert not a_item.commands
    assert cancellations == [("agent", 1)]
    assert rig.env.global_tick == before[0]
    assert torch.equal(rig.env.step_counts, before[1])
    result = advance(rig, session)
    assert result.info["step_counts"].tolist() == [5, 4]
    assert pending_items(scheduler) == a_pending
    assert pending_items(scheduler)[0] is a_item
    assert cancellations == [("agent", 1)]


class LocalTemporalController:
    """Explicit local receipt owner with real ENV/BANK, without POP attestation."""

    def __init__(self, universe):
        level = universe.get_level("L0_demo")
        drive = IntrinsicStrategyConfig.model_validate(dict(level.drive.intrinsic.model_dump(), strategy="none"))
        data = copy.deepcopy(level.training.model_dump())
        data["replay_buffer"]["batch_size"] = 2
        data["intrinsic"]["rnd"].update(feature_dim=4, learning_rate=0.001)
        data["intrinsic"].update(initial_weight=0.4, survival_window=10, min_survival_fraction=0.01)
        data["intrinsic"]["annealing"].update(min_weight=0.01, threshold=100.0, decay_rate=0.9)
        data["training_loop"]["max_steps_per_episode"] = 20
        options = BaCOptions.model_validate(
            {
                "curiosity_scope": {"scope": "shared", "seed_policy": "legacy_shared_v1"},
                "provider_parameter_source": "training",
                "rnd": {"service_mode": "paced_fifo", "max_updates_per_tick": 1, "max_pending_rows": 4, "overflow_policy": "drop_oldest"},
                "providers": {
                    "count_based": {"quantization_width": 0.125, "max_entries": 4},
                    "icm": {
                        "feature_dim": 4,
                        "hidden_dim": 8,
                        "learning_rate": 0.001,
                        "inverse_weight": 0.8,
                        "forward_weight": 0.2,
                        "training_batch_size": 2,
                        "max_pending_transitions": 4,
                    },
                },
            }
        )
        selected = resolve_exploration_policy(drive, TrainingV2Config.model_validate(data), options)
        ids, seed = ("A", "B"), 701
        self.env = VectorizedHamletEnv(
            universe=universe,
            level_name="L0_demo",
            num_agents=2,
            device="cpu",
            world_roster=WorldRosterDeclaration(ids),
            training_seed=seed,
            lane_world_ids=ids,
        )
        self.reports = []
        descriptor = WorldCuriosityDescriptor.from_policy(selected, world_ids=ids, observation_dim=3, action_dim=2, training_seed=seed)
        self.bank = CuriosityBank(
            policy=selected,
            descriptor=descriptor,
            device="cpu",
            validate_accepted_episode=self.env.validate_accepted_episode,
            issuer_factory=lambda owner: WorldReceiptIssuer(owner=owner),
            report_allocation=self.reports.append,
        )
        self.issuer = WorldReceiptIssuer(owner=self)
        roles = {
            name: self for name in ("population", "curriculum", "exploration", "network", "optimizer", "scheduler", "replay", "selection")
        }
        roles["curiosity"] = self.bank
        authority = self.env.bind_boundary_authority(owner=self, role_owners=roles)
        self.session = self.env.bind_manual_execution(population_owner=self)
        release = self.env.install_boundary_release(authority.bootstrap(first_batch_episode=0))
        reservation = self.env.prepare_episode(batch_episode=0, release=release)
        reset = self.env.reset(reservation=reservation)
        self.accepted, self.reset_reading = reset.accepted, reset.observation
        self.env.activate_episode(
            accepted=self.accepted,
            population_receipt=self.issuer.issue(kind="activation", payload={"accepted": self.accepted}),
            curiosity_receipt=self.bank.begin_episode(accepted=self.accepted),
        )
        wait_ids = [key for key, label in self.env.get_action_label_names().items() if label == "WAIT"]
        assert len(wait_ids) == 1
        self.wait_id = wait_ids[0]

    def wait(self):
        legal = self.env.get_action_masks()
        assert bool(legal[~self.env.dones, self.wait_id].all())
        selected = torch.full((2,), self.wait_id, dtype=torch.int64, device=self.env.device)
        return self.session.step(accepted=self.accepted, actions=selected, depletion_multiplier=1.0)


def test_real_temporal_dac_and_nonempty_delayed_command_survive_b_retirement(monkeypatch):
    """Authored time reaches DAC; a real compiled command changes only live A."""
    universe = UniverseCompiler().compile(Path("configs/reference/model_pack"), primary_level="L0_demo", use_cache=False)
    rig = LocalTemporalController(universe)
    env = rig.env
    assert env.universe is universe
    assert env.enable_temporal_mechanics and env.day_length == 24
    assert (env.global_tick, env.time_of_day) == (0, 0)
    manager = env.effect_manager
    assert manager is not None and manager.command_executor is not None
    assert manager.catalog is universe.compiled_effect_catalog
    scheduler = manager.scheduler
    assert scheduler is not None and scheduler.time_enabled
    original_reward, original_cancel = env.vtc_reward_program.apply, manager.cancel_scheduled_for_entity
    hours, cancellations = [], []

    def observe_reward(program, **kwargs):
        hours.append(kwargs["reward_context"]["current_hour"].item())
        return original_reward(**kwargs)

    def observe_cancel(*, scope, entity_id):
        cancellations.append((scope, entity_id))
        return original_cancel(scope=scope, entity_id=entity_id)

    def unexpected(**kwargs):
        pytest.fail("manual temporal/effect work must not create a BANK event")

    monkeypatch.setattr(type(env.vtc_reward_program), "apply", observe_reward)
    monkeypatch.setattr(manager, "cancel_scheduled_for_entity", observe_cancel)
    for name in ("prepare_step_stamp", "reward", "admit_and_service"):
        monkeypatch.setattr(rig.bank, name, unexpected)
    for tick in range(1, 5):
        assert rig.wait().physical_tick == tick
    assert (env.global_tick, env.time_of_day, scheduler.current_tick) == (4, 4, 3)
    assert env.step_counts.tolist() == [4, 4]
    assert env.vfs_registry.get("is_digesting", reader="engine").tolist() == [False, False]
    assert not pending_items(scheduler)
    commands = manager.catalog.effects["ate_food"].on_spawn
    assert commands
    for lane in (0, 1):
        scheduler.schedule(
            commands=commands,
            delay_ticks=1,
            scope="agent",
            entity_id=lane,
            context_overrides={},
            effect_instance=None,
            base_tick=scheduler.current_tick,
        )
    assert set(scheduler.pending) == {4}
    a_item, b_item = pending_items(scheduler)
    assert [(item.scope, item.entity_id) for item in (a_item, b_item)] == [("agent", 0), ("agent", 1)]
    assert a_item.commands and b_item.commands
    counts, meters = env.step_counts.clone(), env.meters.clone()
    receipt = rig.session.retire(accepted=rig.accepted, world_ids=("B",), reason="cap")
    assert receipt.physical_tick == 4
    assert env.global_tick == 4 and torch.equal(env.step_counts, counts) and torch.equal(env.meters, meters)
    assert pending_items(scheduler) == (a_item,) and pending_items(scheduler)[0] is a_item
    assert cancellations == [("agent", 1)]
    with pytest.raises(ValueError):
        rig.session.retire(accepted=rig.accepted, world_ids=("B",), reason="cap")
    result = rig.wait()
    assert result.physical_tick == 5 and result.info["step_counts"].tolist() == [5, 4]
    assert torch.equal(env.meters[1], meters[1])
    assert env.vfs_registry.get("is_digesting", reader="engine").tolist() == [True, False]
    assert not pending_items(scheduler)
    assert cancellations == [("agent", 1)]
    assert (env.global_tick, env.time_of_day, scheduler.current_tick) == (5, 5, 4)
    assert hours == [0, 1, 2, 3, 4]


def test_session_pid_mismatch_refuses_before_env_guard_and_preserves_original_owner(compiled, monkeypatch):
    """Inject only process-identity input; no actual fork qualification is claimed."""
    rig = Rig(compiled, policy(compiled, "none", "shared", "paced_fifo"))
    session = bind(rig)
    rig.begin(0)
    selected = actions(rig)
    original, entered = rig.env._step_manual, []

    def observe(**kwargs):
        entered.append(True)
        return original(**kwargs)

    monkeypatch.setattr(rig.env, "_step_manual", observe)
    with monkeypatch.context() as identity:
        identity.setattr(manual_physical, "os", SimpleNamespace(getpid=lambda: os.getpid() + 1))
        with pytest.raises(ValueError):
            session.step(accepted=rig.accepted, actions=selected, depletion_multiplier=1.0)
    assert entered == []
    assert rig.env.global_tick == 0
    assert advance(rig, session).physical_tick == 1
    assert entered == [True]
