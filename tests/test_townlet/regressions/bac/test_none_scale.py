"""Original T18d prerequisite: none exposes and retains zero selected BANK scale.

Actual ENV/accepted-token/completed-parent fixture; synthetic curiosity geometry.
These producer tests do not qualify full parent or simulator continuation.
"""

from copy import deepcopy

import pytest
import torch

from tests.test_townlet.regressions.bac.test_pw_scope_conversion import (
    IDS,
    Rig,
    equal,
    live,
    policy,
)
from tests.test_townlet.regressions.bac.test_pw_scope_conversion import (
    compiled as compiled,
)


def none_rig(compiled, scope):
    selected = policy(compiled, "none", scope, "paced_fifo")
    # Fixture authors initial_weight=0.4 explicitly; zero cannot mask the defect.
    assert selected.strategy == "none" and selected.initial_intrinsic_weight == 0.4
    return Rig(compiled, selected)


def assert_reward(reward, scope, active):
    equal(reward.eligible, torch.tensor(active))
    assert reward.scope == scope
    equal(reward.raw, torch.zeros(len(IDS)))
    # Causal acceptance: check the selected BANK scale, independently of raw*scale.
    equal(reward.scales, torch.zeros(len(IDS)))
    equal(reward.raw * reward.scales, torch.zeros(len(IDS)))


def assert_no_predictor_work(receipts):
    for receipt in receipts:
        assert receipt.clock is None
        assert receipt.admitted_rows == receipt.consumed_rows == receipt.dropped_rows == receipt.pending_rows == 0
        assert receipt.optimizer_updates == receipt.mandatory_service_updates == 0
        assert receipt.last_loss == 0.0


def assert_cache(state, active):
    assert state["schema"] == "curiosity-bank-state-v2"
    equal(state["step"]["reward"]["raw"], torch.zeros(len(IDS)))
    equal(state["step"]["reward"]["scales"], torch.zeros(len(IDS)))
    equal(state["step"]["reward"]["eligible"], torch.tensor(active))
    for index, record in enumerate(state["worlds"]):
        cached = record["phase_cache"]
        if active[index]:
            equal(cached["reward"]["raw"], torch.tensor(0.0))
            equal(cached["reward"]["scale"], torch.tensor(0.0))
            assert cached["reward"]["update_stats"] is True
            assert cached["reward"]["event_id"] == cached["service"]["event_id"]
        else:
            assert "reward" not in cached and "service" not in cached


def retry(rig, context, stamp, reward, receipts):
    state = rig.bank.checkpoint_state()
    revision = rig.bank.mutation_revision
    repeated = rig.bank.reward(context=context, stamp=stamp, accepted=rig.accepted, update_stats=True)
    assert_reward(repeated, rig.bank.scope, tuple(context.active_on_entry.tolist()))
    equal(repeated.raw, reward.raw)
    equal(repeated.scales, reward.scales)
    assert repeated.event_ids == reward.event_ids
    assert rig.bank.admit_and_service(context=context, stamp=stamp, accepted=rig.accepted) == receipts
    assert rig.bank.mutation_revision == revision
    equal(rig.bank.checkpoint_state(), state)


@pytest.mark.parametrize("scope", ("shared", "per_world"))
def test_none_bank_selected_scale_and_unchanged_retry(compiled, scope):
    """Fail at actual eligible BANK scale, even though contribution already vanishes."""
    rig = none_rig(compiled, scope)
    active = (True, False)
    native = {world: live(rig.bank, world)["native"] for world in IDS}
    rig.begin(0)
    context, stamp, reward, receipts = rig.step(1, active)
    equal(reward.eligible, torch.tensor(active))
    assert tuple(event.world_id for event in reward.event_ids) == IDS
    assert_reward(reward, scope, active)
    assert_no_predictor_work(receipts)
    if scope == "shared":
        assert len(receipts) == int(any(active))
        if receipts:
            assert receipts[0].eligible and receipts[0].world_id is None
            assert receipts[0].event_ids == (stamp.event_ids[0],)
    else:
        assert tuple(receipt.eligible for receipt in receipts) == active
        assert tuple(receipt.world_id for receipt in receipts) == IDS
    state = rig.bank.checkpoint_state()
    assert_cache(state, active)
    for index, world in enumerate(IDS):
        equal(live(rig.bank, world)["native"], native[world])
        cursor = state["worlds"][index]["cursor"]
        assert cursor["eligible_seq"] == cursor["cumulative_service_position"] == int(active[index])
    retry(rig, context, stamp, reward, receipts)


@pytest.mark.parametrize("scope", ("shared", "per_world"))
def test_none_current_live_cache_restore_replays_and_continues(compiled, scope):
    """Roundtrip genuine current cache without normalizing or inventing service work."""
    rig = none_rig(compiled, scope)
    rig.begin(0)
    context, stamp, reward, receipts = rig.step(1, (True, False))
    assert_reward(reward, scope, (True, False))
    saved = rig.bank.checkpoint_state()
    assert_cache(saved, (True, False))
    caller_state = deepcopy(saved)
    prepared = rig.bank.prepare_restore(
        state=caller_state, mode="live_episode", accepted=rig.accepted, parent_restore=None, validate_parent_restore=None
    )
    # Publication must use its owned candidate, not a caller's subsequently edited cache.
    caller_state["step"]["reward"]["scales"].fill_(19)
    caller_state["worlds"][0]["phase_cache"]["reward"]["scale"].fill_(19)
    rig.bank.install_restore(prepared=prepared)
    equal(rig.bank.checkpoint_state(), saved)
    retry(rig, context, stamp, reward, receipts)
    _, _, next_reward, next_receipts = rig.step(2, (True, False))
    assert_reward(next_reward, scope, (True, False))
    assert_no_predictor_work(next_receipts)
    state = rig.bank.checkpoint_state()
    assert_cache(state, (True, False))
    assert state["worlds"][0]["cursor"]["cumulative_service_position"] == 2
    assert state["worlds"][1]["cursor"]["cumulative_service_position"] == 0
    equal(saved["step"]["reward"]["scales"], torch.zeros(2))


@pytest.mark.parametrize("scope", ("shared", "per_world"))
def test_none_current_completed_parent_restore_and_next_episode(compiled, scope):
    """Use actual accepted completion and actual ENV parent preparation in both scopes."""
    source = none_rig(compiled, scope)
    source.begin(0)
    _, _, reward, receipts = source.step(1, (True, False))
    assert_reward(reward, scope, (True, False))
    assert_no_predictor_work(receipts)
    source.close()
    saved = source.bank.checkpoint_state()
    assert saved["bank_phase"] == "completed_boundary" and saved["dispatch_identity"] is None
    assert_cache(saved, (True, False))
    target = Rig(compiled, source.bank.policy)
    target.prepare_parent(source)
    caller_state = deepcopy(saved)
    prepared = target.bank.prepare_restore(
        state=caller_state,
        mode="completed_boundary",
        accepted=None,
        parent_restore=target.parent,
        validate_parent_restore=target.validate_parent,
    )
    caller_state["step"]["reward"]["scales"].fill_(23)
    for view in target.views:
        view.clear()
    target.bank.install_restore(prepared=prepared)
    target.install_parent()
    equal(target.bank.checkpoint_state(), saved)
    target.begin(1)
    context, stamp, current, current_receipts = target.step(2, (True, False))
    assert_reward(current, scope, (True, False))
    assert_no_predictor_work(current_receipts)
    retry(target, context, stamp, current, current_receipts)
    equal(source.bank.checkpoint_state(), saved)


@pytest.mark.parametrize("scope", ("shared", "per_world"))
@pytest.mark.parametrize("phase", ("live_episode", "completed_boundary"))
@pytest.mark.parametrize("fault", ("selected_nonzero", "raw_nonzero", "missing_scale", "old_schema"))
def test_none_invalid_current_cache_refuses_without_mutation_and_retries(compiled, scope, phase, fault):
    """Coherent nonzero scales must refuse; exact cache/schema validation stays strict."""
    source = none_rig(compiled, scope)
    source.begin(0)
    context, stamp, reward, receipts = source.step(1, (True, False))
    assert_reward(reward, scope, (True, False))
    if phase == "completed_boundary":
        source.close()
    saved = source.bank.checkpoint_state()
    assert_cache(saved, (True, False))
    target = source if phase == "live_episode" else Rig(compiled, source.bank.policy)
    if phase == "completed_boundary":
        target.prepare_parent(source)
    args = dict(
        mode=phase,
        accepted=target.accepted if phase == "live_episode" else None,
        parent_restore=None if phase == "live_episode" else target.parent,
        validate_parent_restore=None if phase == "live_episode" else target.validate_parent,
    )
    changed = deepcopy(saved)
    cached = changed["worlds"][0]["phase_cache"]["reward"]
    if fault == "selected_nonzero":
        # Keep both real cache representations coherent: correlation alone cannot reject.
        cached["scale"].fill_(source.bank.policy.initial_intrinsic_weight)
        changed["step"]["reward"]["scales"][0] = cached["scale"]
    elif fault == "raw_nonzero":
        cached["raw"].fill_(0.25)
        changed["step"]["reward"]["raw"][0] = cached["raw"]
    elif fault == "missing_scale":
        del cached["scale"]
    else:
        changed["schema"] = "curiosity-bank-state-v1"
    corrupt_before = deepcopy(changed)
    native_before = {world: live(target.bank, world) for world in IDS}
    before = target.bank.checkpoint_state()
    ambient = torch.get_rng_state().clone()
    revision = target.bank.mutation_revision
    with pytest.raises(ValueError):
        target.bank.prepare_restore(state=changed, **args)
    assert target.bank.mutation_revision == revision
    equal(torch.get_rng_state(), ambient)
    equal(changed, corrupt_before)
    equal(target.bank.checkpoint_state(), before)
    for world in IDS:
        equal(live(target.bank, world), native_before[world])
    equal(source.bank.checkpoint_state(), saved)
    # Exact original current state remains acceptable after refusal, without fallback.
    prepared = target.bank.prepare_restore(state=saved, **args)
    target.bank.install_restore(prepared=prepared)
    if phase == "completed_boundary":
        target.install_parent()
    equal(target.bank.checkpoint_state(), saved)
    if phase == "live_episode":
        retry(target, context, stamp, reward, receipts)
    else:
        target.begin(1)
    _, _, current, current_receipts = target.step(2, (True, False))
    assert_reward(current, scope, (True, False))
    assert_no_predictor_work(current_receipts)
    assert_cache(target.bank.checkpoint_state(), (True, False))
