"""Nonmodel native reset contract; private cases prove components, not RNG ownership.

Real policy/compiled fixture APIs are consumed from the published T18d capsule.
No BANK authority, private stream custody or global selector cadence is implied.
"""

from __future__ import annotations

import copy
import math
import random
from collections.abc import Mapping

import numpy as np
import pytest
import torch

from tests.test_townlet.regressions.bac.test_pw_scope_conversion import compiled as compiled
from tests.test_townlet.regressions.bac.test_pw_scope_conversion import policy as selected_policy
from townlet.config.bac_options import BaCOptions
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.exploration_policy import resolve_exploration_policy
from townlet.exploration.count_based import CountExploration
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration, NoneExploration
from townlet.exploration.provider_factory import make_backend, make_policy_selector

SCOPES = ("shared", "per_world")
FAMILIES = ("count_based", "none")
EPS_KEYS = {"epsilon", "epsilon_decay", "epsilon_min"}
COUNT_KEYS = EPS_KEYS | {
    "schema_version",
    "policy_identity",
    "policy",
    "quantization_width",
    "max_entries",
    "counts",
    "lru",
    "eviction_count",
}


def _equal(left, right):
    """Independent owned-value comparison, including malformed NaN snapshots."""
    assert type(left) is type(right)
    if isinstance(left, torch.Tensor):
        assert left.dtype == right.dtype and left.device == right.device
        assert left.shape == right.shape and left.layout == right.layout
        assert torch.equal(left, right)
    elif isinstance(left, np.ndarray):
        assert left.dtype == right.dtype and left.shape == right.shape
        np.testing.assert_array_equal(left, right)
    elif isinstance(left, Mapping):
        assert set(left) == set(right)
        for key in left:
            _equal(left[key], right[key])
    elif isinstance(left, (tuple, list)):
        assert len(left) == len(right)
        for one, two in zip(left, right, strict=True):
            _equal(one, two)
    elif isinstance(left, float) and math.isnan(left):
        assert math.isnan(right)
    else:
        assert left == right


def _ambient():
    return torch.get_rng_state().clone(), copy.deepcopy(random.getstate()), copy.deepcopy(np.random.get_state())


def _unchanged_rng(before):
    _equal(before, _ambient())


def _new(compiled, family, scope):
    selected = selected_policy(compiled, family, scope, "paced_fifo")
    if family == "count_based":
        # Actual typed authoring from the public bounded-count policy capsule.
        authored = selected.to_dict()["authored_parameters"]
        options_data = authored["bac_options"]
        options_data.setdefault("providers", {}).setdefault("count_based", {}).update({"quantization_width": 1.0, "max_entries": 3})
        selected = resolve_exploration_policy(
            drive_intrinsic=IntrinsicStrategyConfig.model_validate(authored["drive_intrinsic"]),
            training=compiled.get_level(compiled.metadata.primary_level).training,
            options=BaCOptions.model_validate(options_data),
        )
        assert selected.provider_parameters["quantization_width"] == 1.0
        assert selected.provider_parameters["max_entries"] == 3
    before = _ambient()
    if scope == "shared":
        backend = make_backend(selected, world_id=None, obs_dim=3, action_dim=2, device="cpu", rng=None, descriptor=None)
    elif family == "count_based":
        # Native private component only: no fake private descriptor/RNG owner.
        backend = CountExploration(
            selected,
            quantization_width=selected.provider_parameters["quantization_width"],
            max_entries=selected.provider_parameters["max_entries"],
            device="cpu",
        )
    else:
        backend = NoneExploration(epsilon=selected.epsilon_start, epsilon_decay=selected.epsilon_decay, epsilon_min=selected.epsilon_end)
    _unchanged_rng(before)
    assert type(backend) is (CountExploration if family == "count_based" else NoneExploration)
    return backend


def _rows(backend, indices):
    width = backend.checkpoint_state()["quantization_width"]
    return torch.tensor([[(index + 0.25) * width, 0.0, 0.0] for index in indices], dtype=torch.float64)


def _learn_count(backend):
    """Genuine repeated visits, capacity eviction, and a changed LRU order."""
    capacity = backend.checkpoint_state()["max_entries"]
    assert capacity == 3  # Four distinct bins; no training-replay-sized setup.
    row = _rows(backend, [0])
    assert backend.compute_intrinsic_rewards(row, update_stats=True).item() == 1.0
    assert backend.compute_intrinsic_rewards(row, update_stats=True).item() == pytest.approx(1 / math.sqrt(2))
    rows = _rows(backend, range(1, capacity + 1))
    assert torch.equal(backend.compute_intrinsic_rewards(rows, update_stats=True), torch.ones(capacity, dtype=torch.float64))
    state = backend.checkpoint_state()
    assert len(state["counts"]) == capacity and len(state["lru"]) == capacity
    assert state["eviction_count"] == 1
    assert (0, 0, 0) not in state["counts"]
    last = _rows(backend, [capacity])
    assert backend.compute_intrinsic_rewards(last, update_stats=True).item() == pytest.approx(1 / math.sqrt(2))
    if capacity > 1:
        backend.compute_intrinsic_rewards(_rows(backend, [1]), update_stats=True)
        assert backend.checkpoint_state()["lru"][-1] == (1, 0, 0)
    return row


def _decay(backend):
    initial = backend.epsilon
    backend.decay_epsilon()
    assert backend.epsilon == max(backend.epsilon_min, initial * backend.epsilon_decay)
    assert backend.epsilon < initial


def _reset(backend, fresh):
    source_before, fresh_before = backend.checkpoint_state(), fresh.checkpoint_state()
    rng = _ambient()
    prepared = backend.prepare_learning_reset(fresh=fresh)
    _unchanged_rng(rng)
    _equal(backend.checkpoint_state(), source_before)
    _equal(fresh.checkpoint_state(), fresh_before)
    backend.install_state(prepared)
    _unchanged_rng(rng)
    _equal(fresh.checkpoint_state(), fresh_before)
    return prepared


@pytest.mark.parametrize("scope", SCOPES)
def test_count_reset_fresh_learning_retains_diagnostics_and_next_admission(compiled, scope):
    backend = _new(compiled, "count_based", scope)
    row = _learn_count(backend)
    _decay(backend)
    old = backend.checkpoint_state()
    fresh = _new(compiled, "count_based", scope)
    assert old["counts"] and old["eviction_count"] > 0
    assert fresh.checkpoint_state()["counts"] == {}
    assert fresh.epsilon > backend.epsilon
    owner = backend
    _reset(backend, fresh)  # First causal RED: missing operation after genuine learning.
    assert backend is owner
    state = backend.checkpoint_state()
    assert set(state) == COUNT_KEYS and state["schema_version"] == "count-state-v1"
    assert state["counts"] == {} and state["lru"] == [] and state["eviction_count"] == 0
    for key in COUNT_KEYS - {"counts", "lru", "eviction_count"}:
        _equal(state[key], old[key])
    query_before = backend.checkpoint_state()
    assert backend.compute_intrinsic_rewards(row).item() == 1.0
    backend.update({"observations": row})
    _equal(backend.checkpoint_state(), query_before)
    assert backend.compute_intrinsic_rewards(row, update_stats=True).item() == 1.0
    assert backend.compute_intrinsic_rewards(row, update_stats=True).item() == pytest.approx(1 / math.sqrt(2))
    assert backend.checkpoint_state()["counts"] == {(0, 0, 0): 2}
    _reset(backend, _new(compiled, "count_based", scope))
    first_reset = backend.checkpoint_state()
    _reset(backend, _new(compiled, "count_based", scope))
    _equal(backend.checkpoint_state(), first_reset)
    _learn_count(backend)  # Actual LRU/capacity behavior works after reset.
    assert backend.eviction_count == 1


@pytest.mark.parametrize("scope", SCOPES)
def test_none_reset_retains_diagnostics_without_learned_work(compiled, scope):
    backend = _new(compiled, "none", scope)
    _decay(backend)
    state, owner = backend.checkpoint_state(), backend
    assert set(state) == EPS_KEYS
    rows = torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    assert torch.equal(backend.compute_intrinsic_rewards(rows, update_stats=True), torch.zeros(2))
    backend.update({"observations": rows})
    _equal(backend.checkpoint_state(), state)
    for _ in range(2):
        _reset(backend, _new(compiled, "none", scope))
        assert backend is owner
        _equal(backend.checkpoint_state(), state)
    assert torch.equal(backend.compute_intrinsic_rewards(rows), torch.zeros(2))
    backend.decay_epsilon()
    assert backend.epsilon == max(state["epsilon_min"], state["epsilon"] * state["epsilon_decay"])


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("family", FAMILIES)
def test_exact_state_preparation_restore_and_load_have_real_positive_control(compiled, family, scope):
    source = _new(compiled, family, scope)
    if family == "count_based":
        _learn_count(source)
    _decay(source)
    state = source.checkpoint_state()
    target = _new(compiled, family, scope)
    owner, before = target, target.checkpoint_state()
    rng = _ambient()
    prepared = target.prepare_state(state)
    _unchanged_rng(rng)
    _equal(target.checkpoint_state(), before)
    state["epsilon"] = -123.0
    if family == "count_based":
        state["counts"].clear()
        state["lru"].clear()
        state["policy"].clear()
    target.install_state(prepared)
    _unchanged_rng(rng)
    assert target is owner
    _equal(target.checkpoint_state(), source.checkpoint_state())
    loaded = _new(compiled, family, scope)
    rng = _ambient()
    loaded.load_state(target.checkpoint_state())
    _unchanged_rng(rng)
    _equal(loaded.checkpoint_state(), source.checkpoint_state())
    if family == "count_based":
        rows = _rows(source, [source.checkpoint_state()["max_entries"]])
        expected = source.compute_intrinsic_rewards(rows, update_stats=True)
        _equal(target.compute_intrinsic_rewards(rows, update_stats=True), expected)
        _equal(loaded.compute_intrinsic_rewards(rows, update_stats=True), expected)
        _equal(target.checkpoint_state(), source.checkpoint_state())
    else:
        for backend in (source, target, loaded):
            backend.decay_epsilon()
        _equal(target.checkpoint_state(), source.checkpoint_state())
        _equal(loaded.checkpoint_state(), source.checkpoint_state())


@pytest.mark.parametrize("scope", SCOPES)
def test_count_reset_candidate_has_no_alias_to_mutated_fresh_or_export(compiled, scope):
    backend = _new(compiled, "count_based", scope)
    _learn_count(backend)
    _decay(backend)
    expected_epsilon = backend.epsilon
    original = backend.checkpoint_state()
    fresh = _new(compiled, "count_based", scope)
    rng = _ambient()
    prepared = backend.prepare_learning_reset(fresh=fresh)
    _unchanged_rng(rng)
    # Genuine post-prepare changes on fresh must not enter the owned candidate.
    fresh.compute_intrinsic_rewards(_rows(fresh, [99]), update_stats=True)
    fresh.decay_epsilon()
    changed_fresh = fresh.checkpoint_state()
    original["counts"].clear()
    original["lru"].clear()
    original["policy"].clear()
    backend.install_state(prepared)
    _unchanged_rng(rng)
    assert backend.checkpoint_state()["counts"] == {}
    assert backend.checkpoint_state()["lru"] == [] and backend.eviction_count == 0
    assert backend.epsilon == expected_epsilon
    _equal(fresh.checkpoint_state(), changed_fresh)
    backend.compute_intrinsic_rewards(_rows(backend, [3]), update_stats=True)
    _equal(fresh.checkpoint_state(), changed_fresh)
    installed = backend.checkpoint_state()
    fresh.compute_intrinsic_rewards(_rows(fresh, [4]), update_stats=True)
    _equal(backend.checkpoint_state(), installed)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("bad", ("self", "family", "subclass", "decay", "minimum", "source_nan", "source_low", "source_high"))
def test_reset_refuses_before_mutating_either_real_native(compiled, family, scope, bad):
    backend = _new(compiled, family, scope)
    if family == "count_based":
        _learn_count(backend)
    _decay(backend)
    fresh = _new(compiled, family, scope)
    if bad == "self":
        fresh = backend
    elif bad == "family":
        fresh = _new(compiled, "none" if family == "count_based" else "count_based", scope)
    elif bad == "subclass":
        if family == "none":

            class Derived(NoneExploration):
                pass

            fresh = Derived(epsilon=fresh.epsilon, epsilon_decay=fresh.epsilon_decay, epsilon_min=fresh.epsilon_min)
        else:

            class Derived(CountExploration):
                pass

            fresh = Derived(
                fresh.policy,
                quantization_width=fresh.checkpoint_state()["quantization_width"],
                max_entries=fresh.checkpoint_state()["max_entries"],
                device="cpu",
            )
    elif bad == "decay":
        fresh.epsilon_decay = backend.epsilon_decay / 2
    elif bad == "minimum":
        fresh.epsilon_min = backend.epsilon_min + 0.001
    elif bad == "source_low":
        backend.epsilon = backend.epsilon_min - 1.0
    elif bad == "source_high":
        backend.epsilon = fresh.epsilon + 1.0
    else:
        backend.epsilon = float("nan")
    before, candidate_before, rng = backend.checkpoint_state(), fresh.checkpoint_state(), _ambient()
    with pytest.raises(ValueError):
        backend.prepare_learning_reset(fresh=fresh)
    _unchanged_rng(rng)
    _equal(backend.checkpoint_state(), before)
    _equal(fresh.checkpoint_state(), candidate_before)
    if family == "count_based" and bad != "source_nan":
        row = _rows(backend, [900])
        assert backend.compute_intrinsic_rewards(row, update_stats=True).item() == 1.0


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("bad", ("learned", "eviction", "diagnostic", "policy", "device", "source_eviction"))
def test_count_rejects_nonfresh_or_mismatched_real_candidate(compiled, scope, bad):
    backend = _new(compiled, "count_based", scope)
    _learn_count(backend)
    fresh = _new(compiled, "count_based", scope)
    if bad == "learned":
        fresh.compute_intrinsic_rewards(_rows(fresh, [0]), update_stats=True)
    elif bad == "eviction":
        _learn_count(fresh)
    elif bad == "diagnostic":
        fresh.decay_epsilon()
    elif bad == "policy":
        fresh = _new(compiled, "count_based", "per_world" if scope == "shared" else "shared")
    elif bad == "device":
        fresh.device = torch.device("meta")
    else:
        backend._eviction_count = -1  # Deliberately corrupt actual owned source for refusal.
    before, fresh_before, rng = backend.checkpoint_state(), fresh.checkpoint_state(), _ambient()
    with pytest.raises(ValueError):
        backend.prepare_learning_reset(fresh=fresh)
    _unchanged_rng(rng)
    _equal(backend.checkpoint_state(), before)
    _equal(fresh.checkpoint_state(), fresh_before)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("bad", ("source_zero", "source_bool", "source_key", "fresh_width", "fresh_capacity", "fresh_eviction"))
def test_count_reset_validates_complete_actual_source_and_fresh_configuration(compiled, scope, bad):
    backend = _new(compiled, "count_based", scope)
    _learn_count(backend)
    _decay(backend)
    fresh = _new(compiled, "count_based", scope)
    genuine_policy = copy.deepcopy(fresh.policy.to_dict())
    assert fresh.checkpoint_state()["counts"] == {} and fresh.eviction_count == 0
    assert backend.checkpoint_state()["counts"] and backend.eviction_count == 1
    # Negative setup only: corrupt actual fields AFTER genuine learning/construction.
    # These are malformed candidates, never fixtures claiming authentic learned work.
    if bad == "source_zero":
        backend._counts[next(iter(backend._counts))] = 0
    elif bad == "source_bool":
        backend._counts[next(iter(backend._counts))] = True
    elif bad == "source_key":
        value = backend._counts.pop(next(iter(backend._counts)))
        backend._counts[()] = value
    elif bad == "fresh_width":
        fresh._quantization_width = 2.0
    elif bad == "fresh_capacity":
        fresh._max_entries = 4
    else:
        fresh._eviction_count = 1
        assert fresh.checkpoint_state()["counts"] == {} and fresh.checkpoint_state()["lru"] == []
    # Configuration corruption must never forge or change the genuine selected policy.
    _equal(fresh.policy.to_dict(), genuine_policy)
    before = copy.deepcopy(backend.checkpoint_state())
    fresh_before = copy.deepcopy(fresh.checkpoint_state())
    rng = _ambient()
    with pytest.raises(ValueError):
        backend.prepare_learning_reset(fresh=fresh)
    _unchanged_rng(rng)
    _equal(backend.checkpoint_state(), before)
    _equal(fresh.checkpoint_state(), fresh_before)
    _equal(fresh.policy.to_dict(), genuine_policy)
    # A valid learned-source/fresh pair still succeeds through the SAME reset route.
    control = _new(compiled, "count_based", scope)
    _learn_count(control)
    _decay(control)
    diagnostics = {key: control.checkpoint_state()[key] for key in EPS_KEYS}
    _reset(control, _new(compiled, "count_based", scope))
    state = control.checkpoint_state()
    assert state["counts"] == {} and state["lru"] == [] and state["eviction_count"] == 0
    _equal({key: state[key] for key in EPS_KEYS}, diagnostics)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("field", ("epsilon", "epsilon_decay", "epsilon_min"))
@pytest.mark.parametrize("bad", ("missing", "extra", "bool", "nan", "infinity", "string"))
def test_state_preparation_rejects_malformed_diagnostics_atomically(compiled, family, scope, field, bad):
    backend = _new(compiled, family, scope)
    if family == "count_based":
        _learn_count(backend)
    before = backend.checkpoint_state()
    state = copy.deepcopy(before)
    if bad == "missing":
        del state[field]
    elif bad == "extra":
        state["optimizer_epoch_origin"] = 0
    else:
        state[field] = {"bool": True, "nan": float("nan"), "infinity": float("inf"), "string": "0.5"}[bad]
    bad_before, rng = copy.deepcopy(state), _ambient()
    with pytest.raises(ValueError):
        backend.prepare_state(state)
    _unchanged_rng(rng)
    _equal(backend.checkpoint_state(), before)
    _equal(state, bad_before)
    with pytest.raises(ValueError):
        backend.load_state(state)
    _unchanged_rng(rng)
    _equal(backend.checkpoint_state(), before)


@pytest.mark.parametrize("bad", ("schema", "lru", "count", "capacity", "width", "eviction"))
def test_count_complete_state_refusal_retains_actual_learning(compiled, bad):
    backend = _new(compiled, "count_based", "shared")
    _learn_count(backend)
    before = backend.checkpoint_state()
    state = copy.deepcopy(before)
    if bad == "schema":
        state["schema_version"] = "other"
    elif bad == "lru":
        state["lru"].append(state["lru"][0])
    elif bad == "count":
        state["counts"][state["lru"][0]] = 0
    elif bad == "capacity":
        state["max_entries"] += 1
    elif bad == "width":
        state["quantization_width"] *= 2
    else:
        state["eviction_count"] = True
    bad_before, rng = copy.deepcopy(state), _ambient()
    with pytest.raises(ValueError):
        backend.prepare_state(state)
    _unchanged_rng(rng)
    _equal(backend.checkpoint_state(), before)
    _equal(state, bad_before)
    valid = backend.prepare_state(before)
    backend.install_state(valid)
    _unchanged_rng(rng)
    _equal(backend.checkpoint_state(), before)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("family", FAMILIES)
def test_handles_bind_exact_owner_and_family_and_are_single_use(compiled, family, scope):
    backend = _new(compiled, family, scope)
    _decay(backend)
    foreign = _new(compiled, family, scope)
    other_family = _new(compiled, "none" if family == "count_based" else "count_based", scope)
    fresh = _new(compiled, family, scope)
    prepared = backend.prepare_learning_reset(fresh=fresh)
    foreign_handle = foreign.prepare_state(foreign.checkpoint_state())
    family_handle = other_family.prepare_state(other_family.checkpoint_state())
    before, foreign_before, other_before, rng = (
        backend.checkpoint_state(),
        foreign.checkpoint_state(),
        other_family.checkpoint_state(),
        _ambient(),
    )
    for wrong in (None, {}, object(), foreign_handle, family_handle):
        with pytest.raises(ValueError):
            backend.install_state(wrong)
        _unchanged_rng(rng)
        _equal(backend.checkpoint_state(), before)
        _equal(foreign.checkpoint_state(), foreign_before)
        _equal(other_family.checkpoint_state(), other_before)
    with pytest.raises(ValueError):
        foreign.install_state(prepared)
    _unchanged_rng(rng)
    _equal(backend.checkpoint_state(), before)
    _equal(foreign.checkpoint_state(), foreign_before)
    _equal(other_family.checkpoint_state(), other_before)
    # Refusal at the wrong owner cannot consume any genuine handle.
    foreign.install_state(foreign_handle)
    other_family.install_state(family_handle)
    backend.install_state(prepared)
    _unchanged_rng(rng)
    installed = backend.checkpoint_state()
    with pytest.raises(ValueError):
        backend.install_state(prepared)
    _unchanged_rng(rng)
    _equal(backend.checkpoint_state(), installed)


@pytest.mark.parametrize("family", FAMILIES)
def test_private_factory_rejects_missing_ownership_before_construction(compiled, family):
    selected = selected_policy(compiled, family, "per_world", "paced_fifo")
    rng = _ambient()
    with pytest.raises(ValueError):
        make_backend(selected, world_id=None, obs_dim=3, action_dim=2, device="cpu", rng=None, descriptor=None)
    _unchanged_rng(rng)


@pytest.mark.parametrize("epsilon,decay,minimum", ((2.0, 1.1, -1.0), (-2.0, 2.0, -3.0)))
def test_eps_exact_transport_preserves_finite_values_outside_reset_policy_bounds(epsilon, decay, minimum):
    # Existing finite native transport is distinct from qualified selected reset.
    source = EpsilonGreedyExploration(epsilon=epsilon, epsilon_decay=decay, epsilon_min=minimum)
    target = NoneExploration(epsilon=1.0, epsilon_decay=0.9, epsilon_min=0.1)
    state = {"epsilon": epsilon, "epsilon_decay": decay, "epsilon_min": minimum}
    rng = _ambient()
    prepared = target.prepare_state(state)
    target.install_state(prepared)
    _unchanged_rng(rng)
    _equal(target.checkpoint_state(), state)
    source.load_state(state)
    _unchanged_rng(rng)
    _equal(source.checkpoint_state(), state)


@pytest.mark.parametrize("scope", SCOPES)
def test_selector_stays_plain_eps_and_native_families_keep_diagnostic_inheritance(compiled, scope):
    selected = selected_policy(compiled, "none", scope, "paced_fifo")
    rng = _ambient()
    selector = make_policy_selector(selected)
    _unchanged_rng(rng)
    assert type(selector) is EpsilonGreedyExploration
    native = _new(compiled, "none", scope)
    assert type(native) is NoneExploration and isinstance(native, EpsilonGreedyExploration)
    count = _new(compiled, "count_based", scope)
    assert isinstance(count, EpsilonGreedyExploration)
    _learn_count(count)
    count_before = count.checkpoint_state()
    marker = object()
    native.marker = marker
    diagnostics = {"epsilon": selected.epsilon_start, "epsilon_decay": selected.epsilon_decay, "epsilon_min": selected.epsilon_end}
    diagnostics["epsilon"] = max(selected.epsilon_end, selected.epsilon_start * selected.epsilon_decay)
    rng = _ambient()
    EpsilonGreedyExploration.load_state(count, diagnostics)
    EpsilonGreedyExploration.load_state(native, diagnostics)
    selector.load_state(diagnostics)
    _unchanged_rng(rng)
    _equal(selector.checkpoint_state(), diagnostics)
    _equal(native.checkpoint_state(), diagnostics)
    assert native.marker is marker
    count_after = count.checkpoint_state()
    _equal({key: count_after[key] for key in EPS_KEYS}, diagnostics)
    _equal({key: count_after[key] for key in COUNT_KEYS - EPS_KEYS}, {key: count_before[key] for key in COUNT_KEYS - EPS_KEYS})
