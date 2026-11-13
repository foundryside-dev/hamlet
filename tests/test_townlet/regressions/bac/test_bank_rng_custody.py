"""Actual selected BANK payload adoption with earned ENV/component authority.

These tests use the existing real nine-owner _Run controller. They do not claim
that its fresh Q/replay/curriculum after restore is full parent D continuation.
"""

import gc
import random
import weakref
from copy import deepcopy
from threading import Event, Thread

import numpy as np
import pytest
import test_world_episode_identity as identity
import torch

compiled = identity.compiled
FAMILIES = ("none", "count_based", "rnd", "adaptive_rnd", "icm")
SCOPES = ("shared", "per_world")
TRAINABLE = ("rnd", "adaptive_rnd", "icm")


def _run(compiled, family, scope, *, bootstrap=True):
    inputs = identity._selected_inputs(compiled, family=family, scope=scope)
    run = identity._Run(identity._env(compiled), bootstrap=bootstrap, **inputs)
    assert run.policy.strategy == family and run.policy.curiosity_scope == scope
    assert run.bank is run.roles["curiosity"] and run.bank_issuer.owner is run.bank
    assert set(run.roles) == set("population curiosity curriculum exploration network optimizer scheduler replay selection".split())
    return run, inputs


def _cycle(run, batch):
    run.control_horizon = 1
    _, reset = run.reset(batch, retired_world_ids=())
    assert reset.accepted is run.accepted and run.env.world_phase == "active"
    eligible_before, retained_before = run.ledger.eligible_transitions, run.replay.retained_transitions
    _, _, _, info, _ = run.step()
    admitted = int(info["active_on_entry"].sum())
    assert admitted > 0 and run.ledger.eligible_transitions == eligible_before + admitted
    assert run.replay.retained_transitions == min(run.replay_capacity, retained_before + admitted)
    assert run.ledger.vector_ticks == batch
    _, closure, dispositions = run.close(batch, run.env.world_ids)
    run.release_closed(batch, closure, dispositions)
    assert run.ledger.completed_batch_episodes == batch
    return reset


def _native(bank_state, family, scope):
    if scope == "shared":
        values = [bank_state["shared_backend"]["native"]]
    else:
        values = [row["backend"]["backend"] for row in bank_state["worlds"]]
    if family == "adaptive_rnd":
        return [value["rnd_state"] for value in values]
    return values


def _updates(bank_state, family, scope):
    values = _native(bank_state, family, scope)
    if family in ("rnd", "adaptive_rnd"):
        return sum(value["predictor_service"]["optimizer_updates"] for value in values)
    if family == "icm":
        return sum(value["counters"]["optimizer_updates"] for value in values)
    return 0


def _bank(run):
    return run.runtime.checkpoint_state()["bank"]


def _ambient():
    numpy = np.random.get_state()
    return random.getstate(), (numpy[0], numpy[1].copy(), numpy[2], numpy[3], numpy[4]), torch.get_rng_state().clone()


def _set_ambient(state):
    random.setstate(state[0])
    np.random.set_state(state[1])
    torch.set_rng_state(state[2])


def _same_ambient(left, right):
    assert left[0] == right[0] and left[1][0] == right[1][0]
    assert np.array_equal(left[1][1], right[1][1]) and left[1][2:] == right[1][2:]
    identity._same(left[2], right[2])


def _reward_content(reward):
    return dict(raw=reward.raw, scales=reward.scales, eligible=reward.eligible, event_ids=reward.event_ids, scope=reward.scope)


def _prepared_cohort_refs(bank):
    refs = []
    for record in bank._restore_tokens.values():
        cohort = record[-1]
        owners = [cohort.bank, *cohort.input_rngs, *cohort.owners.values()]
        if cohort.shared is not None:
            owners.append(cohort.shared)
        if cohort.validation_rng is not None:
            owners.append(cohort.validation_rng)
        refs.extend(weakref.ref(owner) for owner in owners)
    return refs


def _learned_boundary(compiled, family, scope):
    source, inputs = _run(compiled, family, scope)
    for batch in (1, 2, 3):
        _cycle(source, batch)
    saved_bank = _bank(source)
    if family in TRAINABLE:
        assert _updates(saved_bank, family, scope) > 0, "real service must have updated Adam"
    else:
        assert _updates(saved_bank, family, scope) == 0
    state = source.completed((1, 2, 3))
    runtime_state = source.runtime.checkpoint_state()
    saved_ledger = source.ledger
    saved_component = source.component_state()
    return source, inputs, saved_bank, state, runtime_state, saved_ledger, saved_component


def _restore_saved(compiled, inputs, state, runtime_state, saved_ledger, saved_component):
    return identity._restore(
        compiled,
        state,
        identity.IDS,
        runtime_state=runtime_state,
        component_ledger=saved_ledger,
        component_state=saved_component,
        **inputs,
    )


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("scope", SCOPES)
def test_selected_family_learns_saves_restores_and_continues(compiled, family, scope):
    source, inputs, saved_bank, state, runtime_state, saved_ledger, saved_component = _learned_boundary(compiled, family, scope)
    restored = _restore_saved(compiled, inputs, state, runtime_state, saved_ledger, saved_component)
    identity._same(_bank(restored), saved_bank)
    assert restored.ledger == saved_ledger == source.ledger and state["kind"] == "COMPLETED"
    assert restored.env.world_phase == source.env.world_phase == "released-completed"
    reset = _cycle(restored, 4)
    assert reset.accepted.world_episode_seqs == (4, 4) and restored.env.world_phase == "released-completed"
    if family in TRAINABLE:
        assert _updates(_bank(restored), family, scope) > _updates(saved_bank, family, scope)


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("scope", SCOPES)
def test_learned_bank_equal_authentic_input_continues_exactly(compiled, family, scope, monkeypatch):
    source, inputs, saved_bank, state, runtime_state, saved_ledger, saved_component = _learned_boundary(compiled, family, scope)
    receiver = _restore_saved(compiled, inputs, state, runtime_state, saved_ledger, saved_component)
    identity._same(_bank(receiver), saved_bank)
    assert receiver.ledger == saved_ledger == source.ledger and state["kind"] == "COMPLETED"
    assert receiver.env.world_phase == source.env.world_phase == "released-completed"

    # Both BANKs enter a genuine locally accepted episode. Their physical reset
    # observations may differ under the supported fresh-episode contract.
    source.control_horizon = receiver.control_horizon = 1
    source_reset = source.reset(4, retired_world_ids=())[1]
    receiver_reset = receiver.reset(4, retired_world_ids=())[1]
    assert source_reset.accepted is source.accepted and receiver_reset.accepted is receiver.accepted
    assert source.accepted is not receiver.accepted
    assert source.accepted.world_ids == receiver.accepted.world_ids == identity.IDS
    assert source.accepted.world_episode_seqs == receiver.accepted.world_episode_seqs == (4, 4)
    identity._same(_bank(source), _bank(receiver))

    reward_method, service_method = source.runtime.reward, source.runtime.admit_and_service
    captured = {}

    def observed_reward(**kwargs):
        captured["reward_before"] = _ambient()
        result = reward_method(**kwargs)
        captured["reward_after"] = _ambient()
        captured["reward_call"] = kwargs
        captured["reward"] = deepcopy(result)
        return result

    def observed_service(**kwargs):
        captured["service_before"] = _ambient()
        result = service_method(**kwargs)
        captured["service_after"] = _ambient()
        captured["service_call"] = kwargs
        captured["receipts"] = deepcopy(result)
        return result

    monkeypatch.setattr(source.runtime, "reward", observed_reward)
    monkeypatch.setattr(source.runtime, "admit_and_service", observed_service)
    eligible_before, retained_before = source.ledger.eligible_transitions, source.replay.retained_transitions
    _, _, _, info, actual_receipts = source.step()
    handoff = info["intrinsic_transition"]
    assert captured["reward_call"]["context"] is handoff.context
    assert captured["reward_call"]["stamp"] is handoff.stamp
    assert captured["reward_call"]["accepted"] is source.accepted
    assert captured["service_call"]["context"] is handoff.context
    identity._same(actual_receipts, captured["receipts"])
    context = handoff.context
    admitted = int(context.active_on_entry.sum())
    assert admitted > 0 and source.ledger.eligible_transitions == eligible_before + admitted
    assert source.replay.retained_transitions == min(source.replay_capacity, retained_before + admitted)
    receiver_ledger, receiver_replay = receiver.ledger, receiver.replay.retained_transitions
    local_stamp = receiver.bank.prepare_step_stamp(
        accepted=receiver.accepted,
        world_ids=receiver.accepted.world_ids,
        active_on_entry=context.active_on_entry,
        vector_tick=context.vector_tick,
    )
    for field in ("event_ids", "world_ids", "world_episode_seqs", "eligible_seqs", "eligible"):
        identity._same(getattr(local_stamp, field), getattr(handoff.stamp, field))

    # Ambient rewind supplies equal component input to the shared backend. It
    # is a differential-test precondition, not a production RNG-custody claim.
    ambient_after_source = _ambient()
    try:
        _set_ambient(captured["reward_before"])
        local_reward = receiver.bank.reward(
            context=context,
            stamp=local_stamp,
            accepted=receiver.accepted,
            update_stats=captured["reward_call"]["update_stats"],
        )
        _same_ambient(_ambient(), captured["reward_after"])
        _set_ambient(captured["service_before"])
        local_receipts = receiver.bank.admit_and_service(context=context, stamp=local_stamp, accepted=receiver.accepted)
        _same_ambient(_ambient(), captured["service_after"])
    finally:
        _set_ambient(ambient_after_source)
    identity._same(_reward_content(local_reward), _reward_content(captured["reward"]))
    identity._same(local_receipts, captured["receipts"])
    assert receiver.ledger == receiver_ledger and receiver.replay.retained_transitions == receiver_replay
    source_live, receiver_live = source.bank.checkpoint_state(), receiver.bank.checkpoint_state()
    assert source_live["bank_phase"] == receiver_live["bank_phase"] == "live_episode"
    identity._same(receiver_live, source_live)
    if family in TRAINABLE:
        assert _updates(source_live, family, scope) > _updates(saved_bank, family, scope)


def _owner_call(run, work):
    if run.policy.curiosity_scope == "shared":
        return run.bank._shared.call(work, lineage=None)
    return run.bank._owners[identity.IDS[0]].call(lambda provider, sources: work(provider), lineage=None)


@pytest.mark.parametrize("family", TRAINABLE)
@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("tensor_lr", (False, True))
def test_final_named_gradients_and_saved_adam_configuration(compiled, family, scope, tensor_lr):
    from townlet.exploration import curiosity_checkpoint as checkpoint

    run, inputs = _run(compiled, family, scope)
    _cycle(run, 1)

    def configure(provider):
        modules = checkpoint.gradient_modules(provider, family)
        parameters = [parameter for module in modules.values() for parameter in module.parameters()]
        for index, parameter in enumerate(parameters):
            parameter.grad = None if index % 3 == 0 else torch.full_like(parameter, 0.0 if index % 3 == 1 else 0.25)
        learning_rate = torch.tensor(0.0005, dtype=torch.float64) if tensor_lr else 0.0005
        if family == "icm":
            provider.optimizer.param_groups[0].update(lr=learning_rate, betas=(0.8, 0.95), eps=1e-7, weight_decay=0.001, foreach=False)
        else:
            native = provider.rnd if family == "adaptive_rnd" else provider
            groups = native.optimizer.param_groups
            groups[0]["lr"] = learning_rate
            groups[0]["foreach"] = False
        return checkpoint.capture_gradients(provider, family)

    expected = _owner_call(run, configure)
    saved = _bank(run)
    record = saved["shared_backend"] if scope == "shared" else saved["worlds"][0]
    identity._same(record["gradients"], expected)
    native = record["native"] if scope == "shared" else record["backend"]["backend"]
    recipe = native["rnd_state"]["adam_restore_recipe"] if family == "adaptive_rnd" else native["adam_restore_recipe"]
    assert recipe["algorithm"] == "torch.optim.Adam" and recipe["groups"][0]["options"]["lr"] == 0.0005
    assert isinstance(recipe["groups"][0]["options"]["lr"], torch.Tensor) is tensor_lr
    restored = identity._restore(
        compiled,
        run.completed((1,)),
        identity.IDS,
        runtime_state=run.runtime.checkpoint_state(),
        component_ledger=run.ledger,
        component_state=run.component_state(),
        **inputs,
    )
    identity._same(_bank(restored), saved)
    actual = _owner_call(restored, lambda provider: checkpoint.capture_gradients(provider, family))
    identity._same(actual, expected)
    _cycle(restored, 2)
    assert _updates(_bank(restored), family, scope) > _updates(saved, family, scope)


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("initialization", ("fresh_private", "clone_learned_archive_pending"))
def test_learned_shared_archive_source_precedes_private_target(compiled, monkeypatch, family, initialization):
    from townlet.exploration.world_curiosity_state import WorldRNGState

    source, _ = _run(compiled, family, "shared")
    for batch in (1, 2, 3):
        _cycle(source, batch)
    source_bank = _bank(source)
    if family in TRAINABLE:
        assert _updates(source_bank, family, "shared") > 0
    target, target_inputs = _run(compiled, family, "per_world", bootstrap=False)
    source_state = source.completed((1, 2, 3))
    assert tuple(item["batch_episode"] for item in source_state["accepted_bindings"]) == (1, 2, 3)
    parent = target.env.prepare_world_restore(
        kind="COMPLETED",
        state=source_state,
        world_roster=identity._roster(),
        destination_world_ids=identity.IDS,
        semantic_execution_identity=target.env.semantic_execution_identity,
    )
    boundary = target.boundary.receipt("restored_boundary", kind="COMPLETED", state=deepcopy(source_state), prepared=parent)
    target.restore_context = {
        "prepared": parent,
        "boundary": boundary,
        "mode": "private_initialized",
        "runtime": source.runtime.checkpoint_state(),
        "component": source.component_state(),
        "ledger": source.ledger,
        "release": None,
    }
    create, rng_refs = WorldRNGState.create, []

    def retain_rng(*args, **kwargs):
        rng = create(*args, **kwargs)
        rng_refs.append(weakref.ref(rng))
        return rng

    monkeypatch.setattr(WorldRNGState, "create", retain_rng)
    # Clear prior cases' unreachable owners before a new global membership token.
    gc.collect()
    token = target.runtime.prepare_private_initialization(
        state=target.restore_context["runtime"],
        initialization=initialization,
        parent_restore=parent,
        validate_parent_restore=target.validate_parent_restore,
    )
    cohort_refs = _prepared_cohort_refs(target.bank)
    gc.collect()
    assert cohort_refs and all(reference() is not None for reference in cohort_refs)
    assert len(rng_refs) >= len(identity.IDS) + 1 and all(reference() is not None for reference in rng_refs)
    target.runtime.install_restore(prepared=token)
    converted = target.bank.checkpoint_state()
    assert converted["initialization_origin"]["initialization"] == initialization
    identity._same(converted["initialization_origin"]["source_checkpoint"], source_bank)
    assert converted["curiosity_epoch"] == source_bank["curiosity_epoch"] + 1
    assert converted["shared_backend"] is None and all(row["backend"] is not None for row in converted["worlds"])
    if family in TRAINABLE:
        expected = _updates(source_bank, family, "shared") if initialization == "clone_learned_archive_pending" else 0
        assert _updates(converted, family, "per_world") == expected * len(identity.IDS)
    assert target.restore_context["release"] is not None
    target.ledger = source.ledger
    target.component_commitment = target.restore_context["component"]["last_committed"]
    target.current_epsilons = target.runtime.epsilon_tensor(batch_size=target.env.num_agents, device=target.env.device)
    target.release = target.env.install_world_restore(prepared=parent, release=target.restore_context["release"])
    assert target.env.install_world_restore(prepared=parent, release=target.restore_context["release"]) is target.release
    reset = _cycle(target, 4)
    assert reset.accepted.world_episode_seqs == (4, 4)
    _cycle(target, 5)
    continued = _bank(target)
    if family in TRAINABLE:
        assert _updates(continued, family, "per_world") > _updates(converted, family, "per_world")
    identity._same(continued["initialization_origin"]["source_checkpoint"], source_bank)
    continued_parent = target.completed((1, 2, 3, 4, 5))
    assert tuple(item["batch_episode"] for item in continued_parent["accepted_bindings"]) == (1, 2, 3, 4, 5)
    resumed = _restore_saved(
        compiled, target_inputs, continued_parent, target.runtime.checkpoint_state(), target.ledger, target.component_state()
    )
    identity._same(_bank(resumed), continued)
    _cycle(resumed, 6)
    _cycle(resumed, 7)
    if family in TRAINABLE:
        assert _updates(_bank(resumed), family, "per_world") > _updates(continued, family, "per_world")
    identity._same(_bank(source), source_bank)


@pytest.mark.parametrize("scope", SCOPES)
def test_quarantined_bank_can_recover_from_healthy_saved_payload(compiled, monkeypatch, scope):
    run, _ = _run(compiled, "rnd", scope)
    saved = _bank(run)

    def fail(provider):
        raise ValueError("live owner failure")

    with pytest.raises(ValueError, match="live owner failure"):
        _owner_call(run, fail)
    run.reset(1, retired_world_ids=())
    run.bank.quarantine_episode(accepted=run.accepted, reason="runtime_failure")
    assert run.bank._failed
    original = [run.bank._shared] if scope == "shared" else list(run.bank._owners.values())

    def forbid(*args, **kwargs):
        pytest.fail("recovery touched quarantined current owner")

    for owner in original:
        for name in ("call", "snapshot", "snapshot_with_capture", "prepare_restore"):
            if name != "snapshot_with_capture" or scope == "per_world":
                monkeypatch.setattr(owner, name, forbid)
    token = run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    run.bank.install_restore(prepared=token)
    identity._same(run.bank.checkpoint_state(), saved)
    assert not run.bank._failed


def test_peer_work_stales_prepared_bank_without_changing_its_revision(compiled):
    run, _ = _run(compiled, "rnd", "shared")
    peer, _ = _run(compiled, "none", "per_world")
    saved = _bank(run)
    revision = run.bank.mutation_revision
    token = run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    peer.bank.checkpoint_state()
    assert run.bank.mutation_revision == revision
    with pytest.raises((RuntimeError, ValueError)):
        run.bank.install_restore(prepared=token)
    fresh = run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    run.bank.install_restore(prepared=fresh)
    identity._same(run.bank.checkpoint_state(), saved)


@pytest.mark.parametrize("scope", SCOPES)
def test_capture_keeps_native_and_gradients_under_one_exclusion(compiled, monkeypatch, scope):
    from townlet.exploration import curiosity_checkpoint as checkpoint

    run, _ = _run(compiled, "rnd", scope)
    peer, _ = _run(compiled, "count_based", "shared")
    original = checkpoint.capture_gradients
    attempts, native_parameters = [], []

    def instrument(provider):
        native = provider.checkpoint_state

        def capture_native():
            with pytest.raises(RuntimeError):
                peer.bank.checkpoint_state()
            native_parameters.append(tuple(id(p) for p in provider.predictor_network.parameters()))
            return native()

        monkeypatch.setattr(provider, "checkpoint_state", capture_native)

    if scope == "shared":
        _owner_call(run, instrument)
    else:
        for owner in run.bank._owners.values():
            owner.call(lambda provider, sources: instrument(provider), lineage=None)

    def capture(provider, family):
        assert native_parameters[-1] == tuple(id(p) for p in provider.predictor_network.parameters())
        with pytest.raises(RuntimeError):
            peer.bank.checkpoint_state()
        attempts.append(family)
        return original(provider, family)

    monkeypatch.setattr(checkpoint, "capture_gradients", capture)
    state = run.bank.checkpoint_state()
    expected = 1 if scope == "shared" else len(identity.IDS)
    assert attempts == ["rnd"] * expected and len(native_parameters) == expected
    if scope == "shared":
        assert state["shared_backend"]["gradients"]
    else:
        assert all(row["backend"] is not None and row["gradients"] for row in state["worlds"])


@pytest.mark.parametrize("family", ("rnd", "adaptive_rnd"))
@pytest.mark.parametrize("scope", SCOPES)
def test_empty_adam_group_recipe_survives_learned_restore(compiled, family, scope):
    run, inputs = _run(compiled, family, scope)

    def configure(provider):
        native = provider.rnd if family == "adaptive_rnd" else provider
        parameters = list(native.predictor_network.parameters())
        native.optimizer = torch.optim.Adam(
            [
                {"params": [], "lr": 0.0005, "foreach": False},
                {"params": parameters[::2], "lr": 0.0007, "betas": (0.7, 0.95), "eps": 1e-7, "amsgrad": True},
                {"params": parameters[1::2], "lr": 0.001, "weight_decay": 0.001, "foreach": False},
            ]
        )

    _owner_call(run, configure)
    for batch in (1, 2, 3):
        _cycle(run, batch)
    saved = _bank(run)
    native = _native(saved, family, scope)[0]
    groups = native["adam_restore_recipe"]["groups"]
    assert len(groups) == 3 and groups[0]["parameter_names"] == [] and groups[0]["options"]["lr"] == 0.0005
    assert all(group["parameter_names"] for group in groups[1:])
    assert groups[1]["options"]["amsgrad"] is True and groups[1]["options"]["betas"] == (0.7, 0.95)
    assert _updates(saved, family, scope) > 0
    restored = identity._restore(
        compiled,
        run.completed((1, 2, 3)),
        identity.IDS,
        runtime_state=run.runtime.checkpoint_state(),
        component_ledger=run.ledger,
        component_state=run.component_state(),
        **inputs,
    )
    identity._same(_bank(restored), saved)
    _cycle(restored, 4)
    assert _updates(_bank(restored), family, scope) > _updates(saved, family, scope)


@pytest.mark.parametrize("family", TRAINABLE)
@pytest.mark.parametrize("scope", SCOPES)
def test_missing_native_recipe_refuses_without_source_or_ambient_change(compiled, family, scope):
    run, _ = _run(compiled, family, scope)
    saved = _bank(run)
    malformed = deepcopy(saved)
    _native(malformed, family, scope)[0].pop("adam_restore_recipe")
    before = _ambient()
    with pytest.raises((KeyError, TypeError, ValueError)):
        run.bank.prepare_restore(state=malformed, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    _same_ambient(_ambient(), before)
    identity._same(run.bank.checkpoint_state(), saved)
    token = run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    run.bank.install_restore(prepared=token)
    identity._same(run.bank.checkpoint_state(), saved)


def test_bank_reentry_and_peer_callback_refuse_before_nested_native_work(compiled):
    run, _ = _run(compiled, "rnd", "shared")
    peer, _ = _run(compiled, "count_based", "per_world")
    saved = _bank(run)
    original = run.bank._report
    attempts = []

    def report(estimate):
        with pytest.raises(RuntimeError):
            run.bank.checkpoint_state()
        with pytest.raises(RuntimeError):
            peer.bank.checkpoint_state()
        attempts.append(estimate.operation)
        original(estimate)

    run.bank._report = report
    token = run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    assert attempts == ["restore"]
    run.bank.install_restore(prepared=token)
    identity._same(run.bank.checkpoint_state(), saved)


def test_final_accepted_callback_cannot_launder_stale_currency(compiled):
    run, _ = _run(compiled, "count_based", "shared")
    peer, _ = _run(compiled, "none", "per_world")
    run.reset(1, retired_world_ids=())
    saved = run.bank.checkpoint_state()
    token = run.bank.prepare_restore(
        state=saved, mode="live_episode", accepted=run.accepted, parent_restore=None, validate_parent_restore=None
    )
    validate = run.bank._validate

    def active_callback(*, accepted):
        peer.bank.checkpoint_state()
        return validate(accepted=accepted)

    run.bank._validate = active_callback
    with pytest.raises(RuntimeError):
        run.bank.install_restore(prepared=token)
    run.bank._validate = validate
    fresh = run.bank.prepare_restore(
        state=saved, mode="live_episode", accepted=run.accepted, parent_restore=None, validate_parent_restore=None
    )
    run.bank.install_restore(prepared=fresh)
    identity._same(run.bank.checkpoint_state(), saved)


def test_allocation_refusal_precedes_disposable_owner_work(compiled):
    run, _ = _run(compiled, "rnd", "shared")
    saved = _bank(run)
    before = torch.get_rng_state().clone()
    source = run.bank.checkpoint_state()

    def reject(estimate):
        assert estimate.operation == "restore" and estimate.known_tensor_bytes > 0
        raise ValueError("declared allocation refused")

    run.bank._report = reject
    with pytest.raises(ValueError, match="declared allocation refused"):
        run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    assert torch.equal(torch.get_rng_state(), before)
    identity._same(run.bank.checkpoint_state(), source)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("cut", ("preload", "attached"))
def test_early_refusal_or_late_candidate_failure_preserves_original(compiled, monkeypatch, scope, cut):
    from townlet.exploration import curiosity_checkpoint as checkpoint

    run, _ = _run(compiled, "rnd", scope)
    saved = _bank(run)
    before = torch.get_rng_state().clone()
    name = "validate_native" if cut == "preload" else "attach_gradients"
    actual = getattr(checkpoint, name)
    calls = []

    def fail_once(*args, **kwargs):
        calls.append(name)
        raise ValueError("injected candidate refusal")

    monkeypatch.setattr(checkpoint, name, fail_once)
    with pytest.raises(ValueError, match="injected candidate refusal"):
        run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    assert calls and torch.equal(torch.get_rng_state(), before)
    monkeypatch.setattr(checkpoint, name, actual)
    identity._same(run.bank.checkpoint_state(), saved)
    token = run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    run.bank.install_restore(prepared=token)
    identity._same(run.bank.checkpoint_state(), saved)


@pytest.mark.parametrize("scope", SCOPES)
def test_attachment_targets_final_published_parameters(compiled, monkeypatch, scope):
    from townlet.exploration import curiosity_checkpoint as checkpoint

    run, _ = _run(compiled, "rnd", scope)
    saved = _bank(run)
    actual_attach = checkpoint.attach_gradients
    attached = []

    def observe(provider, values, family):
        actual_attach(provider, values, family)
        attached.append((id(provider), tuple(id(p) for p in provider.predictor_network.parameters())))

    monkeypatch.setattr(checkpoint, "attach_gradients", observe)
    token = run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    run.bank.install_restore(prepared=token)
    if scope == "shared":
        final = [
            run.bank._shared.call(
                lambda provider: (id(provider), tuple(id(p) for p in provider.predictor_network.parameters())), lineage=None
            )
        ]
    else:
        final = [
            run.bank._owners[world].call(
                lambda provider, sources: (id(provider), tuple(id(p) for p in provider.predictor_network.parameters())), lineage=None
            )
            for world in sorted(identity.IDS)
        ]
    assert attached == final


@pytest.mark.parametrize("scope", SCOPES)
def test_capture_blocks_peer_thread_until_both_capture_parts_finish(compiled, monkeypatch, scope):
    from townlet.exploration import curiosity_checkpoint as checkpoint

    run, _ = _run(compiled, "rnd", scope)
    peer, _ = _run(compiled, "none", "shared")
    attempted, finished = Event(), Event()
    failures = []

    def ordinary_peer():
        attempted.set()
        try:
            peer.bank.checkpoint_state()
        except BaseException as error:
            failures.append(error)
        finally:
            finished.set()

    worker = Thread(target=ordinary_peer)
    original = checkpoint.capture_gradients
    calls = []

    def capture(provider, family):
        if not calls:
            worker.start()
            assert attempted.wait(5)
        assert not finished.wait(0.05), "peer crossed the native/gradient exclusion"
        calls.append(family)
        return original(provider, family)

    monkeypatch.setattr(checkpoint, "capture_gradients", capture)
    try:
        run.bank.checkpoint_state()
    finally:
        if worker.ident is not None:
            worker.join(10)
    assert calls and finished.is_set() and not worker.is_alive() and not failures


@pytest.mark.parametrize("scope", SCOPES)
def test_restore_preserves_all_ambient_states_and_next_draws(compiled, scope):
    run, _ = _run(compiled, "rnd", scope)
    saved = _bank(run)
    entry = _ambient()
    expected = random.random(), float(np.random.random()), torch.rand(4)
    _set_ambient(entry)
    token = run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    _same_ambient(_ambient(), entry)
    run.bank.install_restore(prepared=token)
    _same_ambient(_ambient(), entry)
    actual = random.random(), float(np.random.random()), torch.rand(4)
    identity._same(actual, expected)
    identity._same(run.bank.checkpoint_state(), saved)


@pytest.mark.parametrize("scope", SCOPES)
def test_bank_restore_tokens_authenticate_destination_and_are_single_use(compiled, scope):
    from townlet.exploration.curiosity_checkpoint import PreparedCuriosityRestore

    run, _ = _run(compiled, "none", scope)
    peer, _ = _run(compiled, "none", scope)
    saved = _bank(run)
    token = run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    with pytest.raises(ValueError, match="foreign or consumed"):
        peer.bank.install_restore(prepared=token)
    with pytest.raises(ValueError, match="foreign or consumed"):
        run.bank.install_restore(prepared=PreparedCuriosityRestore())
    # Refused admitted operations stale the previous preparation too.
    with pytest.raises(ValueError):
        run.bank.install_restore(prepared=token)
    token = run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    run.bank.install_restore(prepared=token)
    with pytest.raises(ValueError, match="foreign or consumed"):
        run.bank.install_restore(prepared=token)
    identity._same(run.bank.checkpoint_state(), saved)


@pytest.mark.parametrize("scope", SCOPES)
def test_membership_change_stales_bank_token_without_native_work(compiled, scope):
    from townlet.exploration.rng_custody import process_rng_domain

    run, _ = _run(compiled, "none", scope)
    saved = _bank(run)
    token = run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)

    class Lifetime:
        pass

    lifetime = Lifetime()
    domain = process_rng_domain()
    participant = domain.register(owner=lifetime, cuda_devices=(), entrypoints=frozenset({"call"}))
    domain.unregister(participant=participant)
    with pytest.raises(ValueError, match="membership"):
        run.bank.install_restore(prepared=token)
    identity._same(run.bank.checkpoint_state(), saved)


@pytest.mark.parametrize("scope", SCOPES)
def test_offside_cohort_stays_alive_through_gc_and_token_install(compiled, monkeypatch, scope):
    from townlet.exploration.world_curiosity_state import OwnedWorldBackend, SharedWorldBackend, WorldRNGState

    run, _ = _run(compiled, "rnd", scope)
    saved = _bank(run)
    refs = []

    def track(factory):
        def record(*args, **kwargs):
            value = factory(*args, **kwargs)
            refs.append(weakref.ref(value))
            return value

        return record

    for cls, name in ((WorldRNGState, "create"), (OwnedWorldBackend, "construct"), (SharedWorldBackend, "reserve")):
        monkeypatch.setattr(cls, name, track(getattr(cls, name)))
    # Actual admission drains pre-existing retirement before sealing this token.
    gc.collect()
    token = run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    cohort_refs = _prepared_cohort_refs(run.bank)
    gc.collect()
    assert cohort_refs and all(reference() is not None for reference in cohort_refs)
    assert refs and all(reference() is not None for reference in refs), "preparation lost a registered lifetime owner"
    run.bank.install_restore(prepared=token)
    identity._same(run.bank.checkpoint_state(), saved)
    # Inputs are retained until the token outcome, then disposable roots release.
    gc.collect()
    if scope == "per_world":
        assert any(reference() is None for reference in refs)


@pytest.mark.parametrize("scope", SCOPES)
def test_managed_owner_rejects_wrong_and_expired_lineage_before_callback(compiled, scope):
    from townlet.exploration.rng_custody import process_rng_domain

    run, _ = _run(compiled, "none", scope)
    owner = run.bank._shared if scope == "shared" else run.bank._owners[identity.IDS[0]]
    calls = []

    def work(*args):
        calls.append(True)

    with pytest.raises(ValueError, match="lineage"):
        owner.call(work, lineage=object())
    domain = process_rng_domain()
    with domain.operation(participant=owner.rng_participant, operation_kind="prepare", lineage=None) as expired:
        with pytest.raises(ValueError, match="lineage"):
            owner.call(work, lineage=object())
    with pytest.raises(ValueError, match="lineage"):
        owner.call(work, lineage=expired)
    assert not calls


@pytest.mark.parametrize("family", ("rnd", "adaptive_rnd"))
@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("displacement", ("positive", "negative"))
def test_saved_signed_manual_adam_offsets_continue(compiled, family, scope, displacement):
    run, inputs = _run(compiled, family, scope)
    for batch in (1, 2, 3):
        _cycle(run, batch)

    def displace(provider):
        native = provider.rnd if family == "adaptive_rnd" else provider
        parameters = list(native.predictor_network.parameters())
        if displacement == "negative":
            native.optimizer = torch.optim.Adam(parameters, lr=0.0007, betas=(0.7, 0.95), eps=1e-7, amsgrad=True)
        else:
            for parameter in parameters:
                parameter.grad = torch.full_like(parameter, 0.125)
            native.optimizer.step()
        return native.checkpoint_state()["predictor_service"]["optimizer_step_offset"]

    offset = _owner_call(run, displace)
    assert (offset > 0) if displacement == "positive" else (offset < 0)
    saved = _bank(run)
    restored = identity._restore(
        compiled,
        run.completed((1, 2, 3)),
        identity.IDS,
        runtime_state=run.runtime.checkpoint_state(),
        component_ledger=run.ledger,
        component_state=run.component_state(),
        **inputs,
    )
    identity._same(_bank(restored), saved)
    _cycle(restored, 4)
    assert _updates(_bank(restored), family, scope) > _updates(saved, family, scope)


@pytest.mark.parametrize("family", TRAINABLE)
@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("malformation", ("label", "name", "dtype", "shape", "nonfinite"))
def test_gradient_profile_refusal_keeps_original_healthy(compiled, family, scope, malformation):
    from townlet.exploration import curiosity_checkpoint as checkpoint

    run, _ = _run(compiled, family, scope)
    saved = _bank(run)
    malformed = deepcopy(saved)
    values = malformed["shared_backend"]["gradients"] if scope == "shared" else malformed["worlds"][0]["gradients"]
    label = next(iter(values))
    name = next(iter(values[label]))
    shapes = _owner_call(
        run,
        lambda provider: {
            key: {n: torch.zeros_like(p) for n, p in module.named_parameters()}
            for key, module in checkpoint.gradient_modules(provider, family).items()
        },
    )
    if malformation == "label":
        values["foreign"] = values.pop(label)
    elif malformation == "name":
        values[label]["foreign"] = values[label].pop(name)
    elif malformation == "dtype":
        values[label][name] = shapes[label][name].double()
    elif malformation == "shape":
        values[label][name] = torch.zeros(1)
    else:
        values[label][name] = torch.full_like(shapes[label][name], float("nan"))
    entry = _ambient()
    with pytest.raises((ValueError, TypeError)):
        run.bank.prepare_restore(state=malformed, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    _same_ambient(_ambient(), entry)
    identity._same(run.bank.checkpoint_state(), saved)


@pytest.mark.parametrize("family", FAMILIES)
def test_archive_validation_uses_source_policy_and_target_model_init(compiled, monkeypatch, family):
    from townlet.exploration import curiosity_checkpoint as checkpoint
    from townlet.exploration import provider_factory
    from townlet.exploration.rng_custody import process_rng_domain
    from townlet.exploration.world_curiosity_state import WorldCuriosityDescriptor, WorldRNGState

    source, _ = _run(compiled, family, "shared")
    for batch in (1, 2, 3):
        _cycle(source, batch)
    saved = _bank(source)
    target, _ = _run(compiled, family, "per_world")
    descriptor = WorldCuriosityDescriptor.from_policy(
        target.policy,
        world_ids=tuple(reversed(identity.IDS)),
        observation_dim=target.bank.descriptor.observation_dim,
        action_dim=target.bank.descriptor.action_dim,
        training_seed=target.bank.descriptor.training_seed + 17,
    )
    first = sorted(descriptor.world_ids)[0]
    validation_rng = WorldRNGState.create(descriptor=descriptor, world_id=first, cuda_devices=())
    reference_rng = WorldRNGState.create(descriptor=descriptor, world_id=first, cuda_devices=())
    with reference_rng.activate("model_init"):
        expected_model_init = _ambient()
    entry = _ambient()
    actual_factory, attach = provider_factory.make_backend, checkpoint.attach_gradients
    observed = []

    def factory(policy, **kwargs):
        assert policy.to_dict() == source.policy.to_dict() and policy.curiosity_scope == "shared"
        assert kwargs["world_id"] is kwargs["rng"] is kwargs["descriptor"] is None
        assert kwargs["device"] == torch.device("cpu")
        _same_ambient(_ambient(), expected_model_init)
        provider = actual_factory(policy, **kwargs)
        return provider

    def observe_final(provider, values, selected):
        attach(provider, values, selected)
        observed.append(provider)

    monkeypatch.setattr(provider_factory, "make_backend", factory)
    monkeypatch.setattr(checkpoint, "attach_gradients", observe_final)
    domain = process_rng_domain()
    with domain.operation(participant=validation_rng.rng_participant, operation_kind="rng", lineage=None) as lineage:
        checkpoint.validate_archived_native(
            saved,
            descriptor=descriptor,
            device=torch.device("cpu"),
            validation_rng=validation_rng,
            lineage=lineage,
        )
    assert len(observed) == 1
    provider = observed[0]
    identity._same(provider.checkpoint_state(), saved["shared_backend"]["native"])
    identity._same(checkpoint.capture_gradients(provider, family), saved["shared_backend"]["gradients"])
    _same_ambient(_ambient(), entry)
    identity._same(_bank(source), saved)


@pytest.mark.parametrize("scope", SCOPES)
def test_final_currency_follows_callbacks_and_runtime_allocations(compiled, monkeypatch, scope):
    from townlet.exploration import curiosity_checkpoint as checkpoint
    from townlet.exploration.rng_custody import process_rng_domain

    run, _ = _run(compiled, "rnd", scope)
    run.reset(1, retired_world_ids=())
    run.step()
    saved = run.bank.checkpoint_state()
    domain = process_rng_domain()
    current, allocate = domain.current_token, checkpoint._allocate_runtime_data
    sealed, allocations = [], []
    bank_participant = run.bank._rng_participant

    def issue(*, participant, operation):
        if participant is bank_participant:
            assert allocations == ["cache", "receipt"]
            sealed.append(True)
        return current(participant=participant, operation=operation)

    def allocation(*, section, value):
        assert not sealed, "runtime allocation followed final BANK currency"
        allocations.append(section)
        return allocate(section=section, value=value)

    monkeypatch.setattr(domain, "current_token", issue)
    monkeypatch.setattr(checkpoint, "_allocate_runtime_data", allocation)
    token = run.bank.prepare_restore(
        state=saved,
        mode="live_episode",
        accepted=run.accepted,
        parent_restore=None,
        validate_parent_restore=None,
    )
    assert sealed == [True]
    run.bank.install_restore(prepared=token)
    identity._same(run.bank.checkpoint_state(), saved)


def test_domain_admission_precedes_actual_bank_lock(compiled):
    from townlet.exploration.rng_custody import process_rng_domain

    run, _ = _run(compiled, "none", "shared")
    peer, _ = _run(compiled, "none", "per_world")
    actual_lock = run.bank._lock
    entered = []

    class ObservedLock:
        def __enter__(self):
            with pytest.raises(RuntimeError, match="reentry"):
                peer.bank.checkpoint_state()
            actual_lock.acquire()
            entered.append(True)

        def __exit__(self, *error):
            actual_lock.release()

    run.bank._lock = ObservedLock()
    try:
        run.bank.checkpoint_state()
    finally:
        run.bank._lock = actual_lock
    assert entered == [True] and not process_rng_domain().status()[2]


@pytest.mark.parametrize("scope", SCOPES)
def test_idle_registration_reentry_reauthenticates_destination(compiled, monkeypatch, scope):
    from townlet.exploration.world_curiosity_state import OwnedWorldBackend, SharedWorldBackend

    run, _ = _run(compiled, "none", scope)
    saved = _bank(run)
    cls, name = (OwnedWorldBackend, "construct") if scope == "per_world" else (SharedWorldBackend, "reserve")
    original = getattr(cls, name)
    touched = []

    def interleaving(*args, **kwargs):
        value = original(*args, **kwargs)
        if not touched:
            touched.append(run.bank.checkpoint_state())
        return value

    monkeypatch.setattr(cls, name, interleaving)
    with pytest.raises(ValueError, match="idle registration"):
        run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    assert touched
    identity._same(run.bank.checkpoint_state(), saved)


@pytest.mark.parametrize("cut", ("peer", "retained_view"))
def test_final_parent_callback_cannot_refresh_currency_after_peer_work(compiled, cut):
    from townlet.exploration.rng_custody import process_rng_domain

    source, _ = _run(compiled, "rnd", "shared")
    _cycle(source, 1)
    saved, state = _bank(source), source.completed((1,))
    target, _ = _run(compiled, "rnd", "shared", bootstrap=False)
    peer, _ = _run(compiled, "none", "shared")
    parent = target.env.prepare_world_restore(
        kind="COMPLETED",
        state=state,
        world_roster=identity._roster(),
        destination_world_ids=identity.IDS,
        semantic_execution_identity=target.env.semantic_execution_identity,
    )
    boundary = target.boundary.receipt("restored_boundary", kind="COMPLETED", state=deepcopy(state), prepared=parent)
    target.restore_context = dict(
        prepared=parent,
        boundary=boundary,
        mode="completed_boundary",
        runtime=source.runtime.checkpoint_state(),
        component=source.component_state(),
        ledger=source.ledger,
        release=None,
    )
    armed, work, views = [], [], []

    def authenticate(*, prepared, curiosity_state):
        target.validate_parent_restore(prepared=prepared, curiosity_state=curiosity_state)
        views.append(curiosity_state)
        if armed:
            peer.bank._shared.call(lambda provider: None, lineage=target.bank._lineage)
            work.append(True)

    token = target.bank.prepare_restore(
        state=saved,
        mode="completed_boundary",
        accepted=None,
        parent_restore=parent,
        validate_parent_restore=authenticate,
    )
    original_owners = target.bank._shared
    assert views and len({id(view) for view in views}) == 1
    expected = "nested work"
    if cut == "peer":
        armed.append(True)
    else:
        views[-1]["worlds"][0]["cursor"]["eligible_seq"] += 1
        expected = "retained parent callback changed"
    with pytest.raises(ValueError, match=expected):
        target.bank.install_restore(prepared=token)
    assert bool(work) is (cut == "peer") and target.bank._shared is original_owners and not process_rng_domain().status()[2]
    armed.clear()
    token = target.bank.prepare_restore(
        state=saved,
        mode="completed_boundary",
        accepted=None,
        parent_restore=parent,
        validate_parent_restore=authenticate,
    )
    target.bank.install_restore(prepared=token)
    identity._same(target.bank.checkpoint_state(), saved)


@pytest.mark.parametrize("family", ("rnd", "adaptive_rnd"))
@pytest.mark.parametrize("scope", SCOPES)
def test_fixed_target_gradient_is_never_exported_as_lawful(compiled, family, scope):
    run, _ = _run(compiled, family, scope)

    def invalid_target(provider):
        native = provider.rnd if family == "adaptive_rnd" else provider
        fixed = next(native.fixed_network.parameters())
        assert not fixed.requires_grad and fixed.grad is None
        fixed.grad = torch.zeros_like(fixed)

    _owner_call(run, invalid_target)
    with pytest.raises(ValueError, match="target must remain frozen and gradient-free"):
        run.bank.checkpoint_state()
    assert run.bank._failed


@pytest.mark.parametrize("scope", SCOPES)
def test_early_and_late_offside_failures_keep_correct_candidate_health(compiled, monkeypatch, scope):
    from townlet.exploration import curiosity_checkpoint as checkpoint
    from townlet.exploration.world_curiosity_state import OwnedWorldBackend, SharedWorldBackend

    run, _ = _run(compiled, "rnd", scope)
    saved, entry = _bank(run), _ambient()
    cls, create = (OwnedWorldBackend, "construct") if scope == "per_world" else (SharedWorldBackend, "reserve")
    construct, validate, attach = getattr(cls, create), checkpoint.validate_native, checkpoint.attach_gradients
    candidates = []

    def retain(*args, **kwargs):
        owner = construct(*args, **kwargs)
        candidates.append(owner)
        return owner

    def refuse(*args, **kwargs):
        raise ValueError("early validation refusal")

    monkeypatch.setattr(cls, create, retain)
    monkeypatch.setattr(checkpoint, "validate_native", refuse)
    with pytest.raises(ValueError, match="early validation refusal"):
        run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    first = candidates[0]
    if scope == "per_world":
        assert first.snapshot(lineage=None)["healthy"] is True
    else:
        with pytest.raises(RuntimeError):
            first.snapshot(lineage=None)
        # The empty reservation remains available for a corrected bootstrap retry.
        with first.bootstrap(lineage=None) as lease:
            token = first.prepare_restore(
                dict(schema="shared-world-backend-v1", healthy=True, backend=saved["shared_backend"]["native"]),
                factory=lambda: run.bank._configured_factory(None, saved["shared_backend"]["native"], None),
                validate_backend=lambda provider, native: validate(provider, native, policy=run.policy, descriptor=run.bank.descriptor),
                lineage=lease,
            )
            first.install(token, lineage=lease)
        assert first.snapshot(lineage=None)["healthy"] is True
    _same_ambient(_ambient(), entry)
    monkeypatch.setattr(checkpoint, "validate_native", validate)
    candidates.clear()

    def late(provider, values, family):
        attach(provider, values, family)
        raise ValueError("after real final attachment")

    monkeypatch.setattr(checkpoint, "attach_gradients", late)
    with pytest.raises(ValueError, match="after real final attachment"):
        run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    failed = candidates[0]
    if scope == "per_world":
        assert failed.snapshot(lineage=None)["healthy"] is False
    else:
        with pytest.raises(RuntimeError):
            failed.snapshot(lineage=None)
    assert not run.bank._failed
    _same_ambient(_ambient(), entry)
    identity._same(run.bank.checkpoint_state(), saved)


def _bank_child_identity(role):
    import hashlib
    import json
    import os
    from pathlib import Path
    from types import SimpleNamespace

    names = ("BAC_QUAL_ROOT", "BAC_QUAL_SHA", "BAC_QUAL_TREE", "BAC_QUAL_MANIFEST", "BAC_QUAL_OUTPUT")
    supplied = [os.environ.get(name) for name in names]
    if not any(supplied):
        return False
    assert all(supplied), "partial BAC qualification environment"
    import bac_source_identity

    from townlet.exploration import rnd, rng_custody, world_curiosity_state

    bac_source_identity.pytest_configure(SimpleNamespace(workerinput={"workerid": role}))
    output = Path(os.environ["BAC_QUAL_OUTPUT"])
    original = output / f"identity-{role}.json"
    destination = output / f"spawn-identity-{role}.json"
    assert original.is_file() and not destination.exists()
    value = json.loads(original.read_text())
    value.update(
        pid=os.getpid(),
        manifest_sha256=hashlib.sha256(Path(os.environ["BAC_QUAL_MANIFEST"]).read_bytes()).hexdigest(),
        debug=__debug__,
        interop_threads=torch.get_num_interop_threads(),
        imports={
            name: str(Path(module.__file__).resolve())
            for name, module in (
                ("world_curiosity_state", world_curiosity_state),
                ("rng_custody", rng_custody),
                ("rnd", rnd),
            )
        },
    )
    original.write_text(json.dumps(value, sort_keys=True))
    original.rename(destination)
    return True


def _exception_messages(error):
    if isinstance(error, BaseExceptionGroup):
        return [message for nested in error.exceptions for message in _exception_messages(nested)]
    return [str(error)]


def _bank_restore_poison_child(queue, cut):
    import os

    from townlet.exploration import curiosity_checkpoint as checkpoint
    from townlet.exploration.rng_custody import process_rng_domain
    from townlet.exploration.world_curiosity_state import SharedWorldBackend

    role = f"bank_restore_poison_{cut}"
    message = f"bank restore poison {cut} fail closed"
    if cut == "install":
        role, message = "bank_install_poison_completion", "bank install poison completion fail closed"
    qualified = _bank_child_identity(role)
    child_compiled = identity.compiled.__wrapped__()
    run, _ = _run(child_compiled, "rnd", "shared")
    peer, _ = _run(child_compiled, "none", "per_world")
    saved = _bank(run)
    if cut == "install":
        healthy = run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
        run.bank.install_restore(prepared=healthy)
        identity._same(run.bank.checkpoint_state(), saved)
    original_owner, revision, bank_dict = run.bank._shared, run.bank.mutation_revision, run.bank.__dict__
    domain = process_rng_domain()
    patch = pytest.MonkeyPatch()
    real_torch, real_python, real_complete = torch.set_rng_state, random.setstate, domain._complete
    setters, attached, published, candidates = [], [], [], []
    actual_attach, validate = checkpoint.attach_gradients, checkpoint.validate_native
    token = None
    if cut == "install":
        reserve = SharedWorldBackend.reserve

        def retain_candidate(*args, **kwargs):
            candidate = reserve(*args, **kwargs)
            candidates.append(candidate)
            return candidate

        patch.setattr(SharedWorldBackend, "reserve", retain_candidate)
        token = run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
        patch.undo()
        assert len(candidates) == 1 and run.bank.__dict__ is bank_dict

    def partial_python(value):
        real_python(value)
        raise RuntimeError("BANK partial setter uncertainty")

    def partial_torch(value):
        real_torch(value)
        setters.append(True)
        if cut == "cleanup" or len(setters) > 1:
            raise RuntimeError("BANK cleanup setter uncertainty")

    def refuse_after_validation(*args, **kwargs):
        validate(*args, **kwargs)
        raise ValueError("BANK primary validation refusal")

    def fail_completion(devices):
        real_complete(devices)
        if cut == "install" and run.bank.__dict__ is not bank_dict:
            assert run.bank._shared is candidates[0]
            published.append(True)
            raise RuntimeError("BANK install exit completion uncertainty")
        if attached:
            raise RuntimeError("BANK declared completion uncertainty")

    def arm_after_attachment(provider, values, family):
        actual_attach(provider, values, family)
        attached.append(True)

    if cut == "setter":
        patch.setattr(random, "setstate", partial_python)
        patch.setattr(torch, "set_rng_state", partial_torch)
    elif cut == "cleanup":
        patch.setattr(torch, "set_rng_state", partial_torch)
        patch.setattr(checkpoint, "validate_native", refuse_after_validation)
    elif cut == "completion":
        patch.setattr(domain, "_complete", fail_completion)
        patch.setattr(checkpoint, "attach_gradients", arm_after_attachment)
    else:
        patch.setattr(domain, "_complete", fail_completion)
    failure = None
    try:
        try:
            if cut == "install":
                run.bank.install_restore(prepared=token)
            else:
                run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
        except BaseException as error:
            failure = error
    finally:
        patch.undo()
    assert failure is not None and domain.status()[2]
    messages = _exception_messages(failure)
    if cut == "setter":
        assert any("BANK partial setter uncertainty" in message for message in messages) and setters
    elif cut == "cleanup":
        assert any("BANK primary validation refusal" in message for message in messages)
        assert any("BANK cleanup setter uncertainty" in message for message in messages) and setters
    elif cut == "completion":
        assert attached and any("BANK declared completion uncertainty" in message for message in messages)
    else:
        assert published and any("BANK install exit completion uncertainty" in message for message in messages)
        assert run.bank.__dict__ is not bank_dict and run.bank._shared is candidates[0] and run.bank._failed
        assert run.bank.mutation_revision == revision + 1 and bank_dict["_shared"] is original_owner
    if cut != "install":
        assert run.bank.__dict__ is bank_dict and run.bank._shared is original_owner and run.bank.mutation_revision == revision
    for work in (
        lambda: run.bank.checkpoint_state(),
        lambda: peer.bank.checkpoint_state(),
        lambda: original_owner.snapshot(lineage=None),
        lambda: run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None),
        lambda: domain.register(owner=run.bank, cuda_devices=(), entrypoints=frozenset({"call"})),
    ):
        with pytest.raises(RuntimeError, match="poison"):
            work()
    queue.put((message, os.getpid(), qualified))


@pytest.mark.parametrize("cut", ("setter", "cleanup", "completion"))
def test_bank_restore_uncertainty_poisons_only_its_isolated_process(compiled, cut):
    _observe_bank_poison_child(cut)


def test_bank_install_exit_completion_failure_quarantines_assigned_candidate(compiled):
    _observe_bank_poison_child("install")


def _observe_bank_poison_child(cut):
    import hashlib
    import json
    import multiprocessing
    import os
    from pathlib import Path

    from townlet.exploration.rng_custody import process_rng_domain

    entry = _ambient()
    domain = process_rng_domain()
    assert not domain.status()[2]
    spawn = multiprocessing.get_context("spawn")
    queue = spawn.Queue()
    process = spawn.Process(target=_bank_restore_poison_child, args=(queue, cut))
    role = f"bank_restore_poison_{cut}"
    message = f"bank restore poison {cut} fail closed"
    if cut == "install":
        role, message = "bank_install_poison_completion", "bank install poison completion fail closed"
    try:
        process.start()
        process.join(60)
        assert not process.is_alive() and process.exitcode == 0
        observed, pid, qualified = queue.get(timeout=5)
        assert observed == message and pid == process.pid
        names = ("BAC_QUAL_ROOT", "BAC_QUAL_SHA", "BAC_QUAL_TREE", "BAC_QUAL_MANIFEST", "BAC_QUAL_OUTPUT")
        supplied = [os.environ.get(name) for name in names]
        assert not any(supplied) or all(supplied)
        assert qualified is bool(any(supplied))
        if qualified:
            observation = Path(os.environ["BAC_QUAL_OUTPUT"]) / f"spawn-observation-{role}.json"
            with observation.open("x") as stream:
                json.dump(
                    dict(
                        process_pid=process.pid,
                        queued_pid=pid,
                        exitcode=process.exitcode,
                        qualified=qualified,
                        message=observed,
                        manifest_sha256=hashlib.sha256(Path(os.environ["BAC_QUAL_MANIFEST"]).read_bytes()).hexdigest(),
                    ),
                    stream,
                    sort_keys=True,
                )
    finally:
        if process.is_alive():
            process.terminate()
            process.join(10)
        queue.close()
        queue.join_thread()
        process.close()
    assert not domain.status()[2]
    _same_ambient(_ambient(), entry)


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("scope", SCOPES)
def test_initial_selected_bank_roundtrip_then_real_service(compiled, family, scope):
    run, _ = _run(compiled, family, scope)
    saved, entry = _bank(run), _ambient()
    assert saved["bank_phase"] == "initial"
    token = run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    run.bank.install_restore(prepared=token)
    _same_ambient(_ambient(), entry)
    identity._same(_bank(run), saved)
    _cycle(run, 1)
    _cycle(run, 2)
    if family in TRAINABLE:
        assert _updates(_bank(run), family, scope) > 0


@pytest.mark.parametrize("scope", SCOPES)
def test_actual_count_eviction_lru_survives_saved_restore(compiled, scope):
    run, _ = _run(compiled, "count_based", scope)
    width = run.bank.descriptor.observation_dim
    observations = torch.arange(6 * width, dtype=torch.float32).reshape(6, width) * 0.25
    _owner_call(run, lambda provider: provider.compute_intrinsic_rewards(observations, update_stats=True))
    saved = _bank(run)
    native = _native(saved, "count_based", scope)[0]
    assert len(native["counts"]) == len(native["lru"]) == 4
    token = run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    run.bank.install_restore(prepared=token)
    identity._same(_bank(run), saved)
    _owner_call(run, lambda provider: provider.compute_intrinsic_rewards(observations[-2:], update_stats=True))
    changed = _native(_bank(run), "count_based", scope)[0]
    assert changed["lru"] == native["lru"] and sum(changed["counts"].values()) == sum(native["counts"].values()) + 2


@pytest.mark.parametrize("family", TRAINABLE)
def test_initial_shared_factory_retains_actual_ambient_consumption(compiled, monkeypatch, family):
    from townlet.exploration.world_curiosity_state import SharedWorldBackend

    construct = SharedWorldBackend.construct
    witnessed = []

    def observe(*, factory, cuda_devices):
        states = []

        def selected_factory():
            states.append(_ambient())
            provider = factory()
            states.append(_ambient())
            return provider

        owner = construct(factory=selected_factory, cuda_devices=cuda_devices)
        assert len(states) == 2 and not torch.equal(states[0][2], states[1][2])
        _same_ambient(_ambient(), states[1])
        witnessed.append(True)
        return owner

    monkeypatch.setattr(SharedWorldBackend, "construct", observe)
    _run(compiled, family, "shared")
    assert witnessed == [True]


@pytest.mark.parametrize("scope", SCOPES)
def test_failed_final_currency_releases_unissued_preparation_and_allows_retry(compiled, monkeypatch, scope):
    from townlet.exploration.rng_custody import process_rng_domain

    run, _ = _run(compiled, "rnd", scope)
    saved = _bank(run)
    domain, participant = process_rng_domain(), run.bank._rng_participant
    current = domain.current_token

    def refuse(*, participant, operation):
        token = current(participant=participant, operation=operation)
        if participant is run.bank._rng_participant:
            raise ValueError("final BANK currency issuance refused")
        return token

    monkeypatch.setattr(domain, "current_token", refuse)
    with pytest.raises(ValueError, match="final BANK currency issuance refused"):
        run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    assert not run.bank._restore_tokens and not run.bank._failed and run.bank._rng_participant is participant
    identity._same(_bank(run), saved)
    monkeypatch.setattr(domain, "current_token", current)
    token = run.bank.prepare_restore(state=saved, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    run.bank.install_restore(prepared=token)
    identity._same(_bank(run), saved)
