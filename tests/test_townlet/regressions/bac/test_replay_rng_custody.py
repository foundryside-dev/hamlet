"""Direct replay RNG, owner exclusion and prepared publication controls.

Every domain-entering call supplies explicit lineage. The direct and owner
controls observe real acquisition boundaries and selected sampler effects;
their earlier R73/R74 RED evidence remains tied to its original source.
"""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import multiprocessing
import os
import pickle
import random
import sys
import threading
from collections.abc import Mapping
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import test_world_rng_bootstrap as bootstrap
import torch

from townlet.config.bac_options import ReplayOptions
from townlet.exploration.rng_custody import RNGOperation, process_rng_domain
from townlet.training.prioritized_replay_buffer import PrioritizedReplayBuffer
from townlet.training.replay_buffer import ReplayBuffer
from townlet.training.replay_contract import PreparedReplay, ReplayCustody, ReplayRequest
from townlet.training.sequential_replay_buffer import SequentialReplayBuffer
from townlet.training.state import RewardTensor

_CPU = torch.device("cpu")
_SUCCESSIVE = "successive_without_replacement"


def _assert_same_transport(left: Any, right: Any) -> None:
    """Compare complete owned checkpoint data, including tensor and RNG arrays."""
    assert type(left) is type(right)
    if isinstance(left, torch.Tensor):
        assert torch.equal(left, right)
    elif isinstance(left, np.ndarray):
        assert np.array_equal(left, right)
    elif isinstance(left, Mapping):
        assert set(left) == set(right)
        for key in left:
            _assert_same_transport(left[key], right[key])
    elif isinstance(left, (tuple, list)):
        assert len(left) == len(right)
        for item, other in zip(left, right, strict=True):
            _assert_same_transport(item, other)
    else:
        assert left == right


def _assert_same_selected_batch(left: Any, right: Any) -> None:
    for name in ("observations", "actions", "rewards", "unit_ids", "weights"):
        _assert_same_transport(getattr(left, name), getattr(right, name))
    for name in (
        "indices",
        "weights",
        "population_size",
        "conditional_draw_probabilities",
        "mode",
        "objective_unit",
        "weight_rule",
    ):
        _assert_same_transport(getattr(left.sampling, name), getattr(right.sampling, name))


def _assert_live_rows_unchanged(owner: ReplayBuffer | PrioritizedReplayBuffer | SequentialReplayBuffer, saved: Mapping[str, Any]) -> None:
    """Observe exposed real storage without reentering a held owner/domain guard."""
    if isinstance(owner, SequentialReplayBuffer):
        assert owner.num_transitions == saved["num_transitions"]
        assert len(owner.episodes) == len(saved["episodes"])
        for live, recorded in zip(owner.episodes, saved["episodes"], strict=True):
            _assert_same_transport(live["observations"], recorded["observations"])
    elif isinstance(owner, PrioritizedReplayBuffer):
        assert owner.size_current == saved["size_current"]
        _assert_same_transport(owner.priorities, saved["priorities"])
        _assert_same_transport(owner.observations[: owner.size_current], saved["observations"])
    else:
        assert owner.size == saved["size"]
        _assert_same_transport(owner.observations[: owner.size], saved["observations"])


def _ambient_cpu_state() -> tuple[object, object, torch.Tensor]:
    return random.getstate(), np.random.get_state(), torch.get_rng_state().clone()


@pytest.fixture(autouse=True)
def _restore_cpu_ambient_states() -> Any:
    """Keep genuine direct draws from changing other tests' starting streams."""
    python_state = random.getstate()
    numpy_state = np.random.get_state()
    torch_state = torch.get_rng_state().clone()
    try:
        yield
    finally:
        random.setstate(python_state)
        np.random.set_state(numpy_state)
        torch.set_rng_state(torch_state)


def _flat_rows(offset: float = 0.0) -> tuple[torch.Tensor, torch.Tensor, RewardTensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    observations = torch.tensor([[1.0 + offset], [2.0 + offset], [3.0 + offset]], dtype=torch.float32)
    actions = torch.tensor([0, 1, 0], dtype=torch.int64)
    rewards = RewardTensor(total=torch.tensor([1.0 + offset, 2.0 + offset, 3.0 + offset], dtype=torch.float32))
    successors = torch.tensor([[2.0 + offset], [3.0 + offset], [4.0 + offset]], dtype=torch.float32)
    dones = torch.tensor([False, False, True], dtype=torch.bool)
    masks = torch.tensor([[True, True], [True, True], [True, True]], dtype=torch.bool)
    return observations, actions, rewards, successors, dones, masks


def _flat() -> ReplayBuffer:
    owner = ReplayBuffer(capacity=8, device=_CPU)
    owner.push_recorded(*_flat_rows())
    return owner


def _per(*, local: bool) -> PrioritizedReplayBuffer:
    owner = PrioritizedReplayBuffer(capacity=8, alpha=0.6, beta=0.4, beta_annealing=False, device=_CPU)
    owner.push_recorded(*_flat_rows())
    if local:
        owner.configure_sampling(sampling_mode=_SUCCESSIVE, rng=np.random.Generator(np.random.PCG64(719)), origin="authored")
    return owner


def _episode() -> dict[str, torch.Tensor]:
    return {
        "observations": torch.tensor([[1.0], [2.0], [3.0]], dtype=torch.float32),
        "actions": torch.tensor([0, 1, 0], dtype=torch.int64),
        "rewards": torch.tensor([1.0, 2.0, 3.0], dtype=torch.float32),
        "next_observations": torch.tensor([[2.0], [3.0], [4.0]], dtype=torch.float32),
        "dones": torch.tensor([False, False, True], dtype=torch.bool),
    }


def _sequence_direct() -> SequentialReplayBuffer:
    owner = SequentialReplayBuffer(capacity=8, device=_CPU)
    owner.store_episode(_episode())
    return owner


def _options() -> ReplayOptions:
    return ReplayOptions(
        sampling_mode=_SUCCESSIVE,
        uniform_sequence_adapter="legacy_episode_length_with_replacement",
        sequence_mode="fixed_full",
        retention_mode="whole_episode",
        sequence_objective="window_mean",
        priority_reduction="max_abs",
    )


def _sequence_qualified(*, prioritized: bool) -> SequentialReplayBuffer:
    options = _options()
    if prioritized:
        owner = SequentialReplayBuffer.for_prioritized_replay(
            8,
            _CPU,
            options=options,
            action_dim=2,
            legality_mode="captured",
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            beta_vector_tick_horizon=100,
            current_vector_tick=0,
            rng=np.random.Generator(np.random.PCG64(911)),
            origin="authored",
        )
    else:
        owner = SequentialReplayBuffer.for_replay(8, _CPU, options=options, action_dim=2, legality_mode="captured")
    episode = {
        **_episode(),
        "rewards_extrinsic": None,
        "rewards_intrinsic": None,
        "rewards_shaping": None,
    }
    owner.store_captured_episode(
        episode,
        next_action_masks=torch.tensor([[True, True], [True, True], [True, True]], dtype=torch.bool),
        legality_recorded=torch.tensor([True, True, True], dtype=torch.bool),
    )
    return owner


def _flat_request() -> ReplayRequest:
    return ReplayRequest(1, 1, 1, "uniform_without_replacement", "feedforward", "transition")


def _per_request() -> ReplayRequest:
    return ReplayRequest(1, 1, 1, _SUCCESSIVE, "feedforward", "transition")


def _sequence_request() -> ReplayRequest:
    return ReplayRequest(1, 2, 1, _SUCCESSIVE, "fixed_full", "window_mean")


def test_healthy_flat_recorded_rows_and_both_sample_apis() -> None:
    owner = _flat()
    assert owner.readiness(_flat_request()).ready
    direct = owner.sample(1, lineage=None)
    batch = owner.sample_batch(_flat_request(), lineage=None)
    assert direct["observations"].shape == (1, 1)
    assert batch.observations.shape == (1, 1)
    assert batch.legality_recorded.tolist() == [True]
    assert batch.sampling.population_size == 3


@pytest.mark.parametrize("local", [False, True], ids=["global", "owned-generator"])
def test_healthy_per_recorded_rows_and_both_sample_apis(local: bool) -> None:
    owner = _per(local=local)
    assert owner.readiness(_per_request()).ready
    direct = owner.sample(1, lineage=None)
    batch = owner.sample_batch(_per_request(), lineage=None)
    assert direct["observations"].shape == (1, 1)
    assert batch.observations.shape == (1, 1)
    assert batch.legality_recorded.tolist() == [True]
    assert batch.sampling.population_size == 3


def test_healthy_recurrent_direct_episode_and_sample() -> None:
    owner = _sequence_direct()
    batch = owner.sample_sequences(1, 2, lineage=None)
    assert batch["observations"].shape == (1, 2, 1)
    assert batch["mask"].tolist() == [[True, True]]


def test_healthy_per_live_active_prefix_matches_serialized_rows() -> None:
    """Fixture control: live PER storage is capacity-sized; transport holds active rows."""
    owner = _per(local=False)
    saved = owner.serialize()
    assert owner.observations.shape[0] == owner.capacity == 8
    assert saved["observations"].shape[0] == owner.size_current == 3
    _assert_live_rows_unchanged(owner, saved)


@pytest.mark.parametrize("prioritized", [False, True], ids=["uniform", "owned-generator-priority"])
def test_healthy_recurrent_qualified_readiness_and_sample(prioritized: bool) -> None:
    owner = _sequence_qualified(prioritized=prioritized)
    assert owner.readiness(_sequence_request()).ready
    batch = owner.sample_batch(_sequence_request(), lineage=None)
    assert batch.observations.shape == (1, 2, 1)
    assert batch.legality_recorded.tolist() == [[True, True]]
    assert batch.sampling.population_size > 0


def _direct_owner(kind: str) -> ReplayBuffer | PrioritizedReplayBuffer | SequentialReplayBuffer:
    if kind == "flat":
        return _flat()
    if kind == "per":
        return _per(local=False)
    if kind == "recurrent":
        return _sequence_direct()
    raise AssertionError(kind)


def _direct_draw(kind: str, owner: ReplayBuffer | PrioritizedReplayBuffer | SequentialReplayBuffer) -> object:
    if kind == "recurrent":
        assert isinstance(owner, SequentialReplayBuffer)
        return owner.sample_sequences(1, 2, lineage=None)
    if kind == "per":
        assert isinstance(owner, PrioritizedReplayBuffer)
        return owner.sample(1, lineage=None)
    assert isinstance(owner, ReplayBuffer)
    return owner.sample(1, lineage=None)


class _DomainPeer:
    """A real registered lifetime owner, not a private-world stand-in."""


def _peer() -> tuple[_DomainPeer, Any]:
    owner = _DomainPeer()
    participant = process_rng_domain().register(owner=owner, cuda_devices=(), entrypoints=frozenset({"hold"}))
    return owner, participant


@pytest.mark.parametrize("kind", ["flat", "per", "recurrent"])
def test_direct_ambient_sample_waits_for_registered_peer(kind: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prospective API RED: observe the real replay domain operation before acquisition.

    The original Stage A source at SHA 70cb5aa0 demonstrated actual bypass.
    This stronger node requires the new replay participant and explicit lineage.
    """
    owner = _direct_owner(kind)
    peer, participant = _peer()
    replay_participant = owner.rng_participant
    domain = process_rng_domain()
    original_operation = domain.operation
    reached, acquired, done = threading.Event(), threading.Event(), threading.Event()
    observed: list[tuple[object, str, object]] = []
    outcome: list[object] = []
    worker: threading.Thread

    @contextmanager
    def observed_operation(_domain: object, *, participant: object, operation_kind: str, lineage: object) -> Any:
        selected = threading.current_thread() is worker and participant is replay_participant
        if selected:
            observed.append((participant, operation_kind, lineage))
            reached.set()
        with original_operation(participant=participant, operation_kind=operation_kind, lineage=lineage) as lease:
            if selected:
                acquired.set()
            yield lease

    monkeypatch.setattr(type(domain), "operation", observed_operation)

    def draw() -> None:
        try:
            if kind == "recurrent":
                assert isinstance(owner, SequentialReplayBuffer)
                outcome.append(owner.sample_sequences(1, 2, lineage=None))
            else:
                assert isinstance(owner, (ReplayBuffer, PrioritizedReplayBuffer))
                outcome.append(owner.sample(1, lineage=None))
        except BaseException as error:
            outcome.append(error)
        finally:
            done.set()

    worker = threading.Thread(target=draw, name=f"replay-direct-{kind}", daemon=True)
    live_before = owner.serialize()
    if kind == "flat":
        ambient_before: object = torch.get_rng_state().clone()
    elif kind == "per":
        ambient_before = pickle.dumps(np.random.get_state())
    else:
        ambient_before = random.getstate()
    try:
        with domain.operation(participant=participant, operation_kind="hold", lineage=None):
            worker.start()
            assert reached.wait(3), "direct replay did not enter its genuine domain operation"
            assert not acquired.is_set(), "replay acquired the domain while the peer held it"
            assert not done.wait(0.5), "direct replay sampling bypassed the held process domain"
            _assert_live_rows_unchanged(owner, live_before)
            if kind == "flat":
                assert torch.equal(ambient_before, torch.get_rng_state())
            elif kind == "per":
                assert ambient_before == pickle.dumps(np.random.get_state())
            else:
                assert ambient_before == random.getstate()
    finally:
        if worker.ident is not None:
            worker.join(timeout=5)
        if worker.is_alive():
            raise AssertionError("direct sampler survived bounded cleanup") from sys.exc_info()[1]
    assert acquired.is_set(), "replay did not acquire after peer release"
    assert observed == [(replay_participant, "sample", None)]
    assert len(outcome) == 1 and not isinstance(outcome[0], BaseException)
    _assert_same_transport(live_before, owner.serialize())
    if kind == "flat":
        assert not torch.equal(ambient_before, torch.get_rng_state())
    elif kind == "per":
        assert ambient_before != pickle.dumps(np.random.get_state())
    else:
        assert ambient_before != random.getstate()
    assert peer is not None


def test_explicit_lineage_refuses_unrelated_reentry_and_allows_authentic_nesting() -> None:
    """API RED first: frozen ReplayBuffer.sample has no required lineage keyword.

    Once the signature exists, both calls exercise the actual common domain.
    """
    owner = _flat()
    peer, participant = _peer()
    before = torch.get_rng_state().clone()
    with process_rng_domain().operation(participant=participant, operation_kind="hold", lineage=None) as lease:
        with pytest.raises(RuntimeError, match="Unrelated same-thread RNG reentry is forbidden"):
            owner.sample(1, lineage=None)
        assert torch.equal(before, torch.get_rng_state())
        batch = owner.sample(1, lineage=lease)
        assert batch["observations"].shape == (1, 1)
    assert peer is not None


class _PausingReplayBuffer(ReplayBuffer):
    """Pause only before the real torch.randperm; never replace its sampler."""

    def __init__(self) -> None:
        super().__init__(capacity=8, device=_CPU)
        self.entered = threading.Event()
        self.resume = threading.Event()
        self.clear_reached = threading.Event()
        self.clear_acquired = threading.Event()
        self.clear_worker: threading.Thread | None = None

    @contextmanager
    def _owner_operation(self, *, mutation: bool) -> Any:
        """Observe the prospective real guard; delegate its full acquisition/exit."""
        selected = mutation and threading.current_thread() is self.clear_worker
        if selected:
            self.clear_reached.set()
        with super()._owner_operation(mutation=mutation) as guard:
            if selected:
                self.clear_acquired.set()
            yield guard

    def _indices(self, batch_size: int) -> torch.Tensor:
        self.entered.set()
        if not self.resume.wait(5):
            raise AssertionError("sample pause was not released")
        return super()._indices(batch_size)


def test_same_owner_clear_waits_until_real_sample_finishes() -> None:
    """Prospective API RED: owner clear must reach the real guard and wait.

    Original Stage A SHA 70cb5aa0 showed actual owner bypass. This stronger
    node requires the real shared `_owner_operation(*, mutation)` helper;
    the current sample call must gain explicit lineage at GREEN.
    """
    owner = _PausingReplayBuffer()
    owner.push_recorded(*_flat_rows())
    sample_done, clear_done = threading.Event(), threading.Event()
    results: list[object] = []

    def sample() -> None:
        try:
            results.append(owner.sample(1, lineage=None))
        except BaseException as error:
            results.append(error)
        finally:
            sample_done.set()

    def clear() -> None:
        try:
            owner.clear()
        except BaseException as error:
            results.append(error)
        finally:
            clear_done.set()

    sampler = threading.Thread(target=sample, name="replay-same-owner-sample", daemon=True)
    clearer = threading.Thread(target=clear, name="replay-same-owner-clear", daemon=True)
    owner.clear_worker = clearer
    live_before = owner.serialize()
    ambient_before = torch.get_rng_state().clone()
    try:
        sampler.start()
        assert owner.entered.wait(3), "real sampling did not reach its pause"
        clearer.start()
        assert owner.clear_reached.wait(3), "clear did not enter its genuine owner guard"
        assert not owner.clear_acquired.is_set(), "clear acquired the owner during sampling"
        assert not clear_done.wait(0.5), "clear mutated the owner during its sample"
        _assert_live_rows_unchanged(owner, live_before)
        assert torch.equal(ambient_before, torch.get_rng_state())
    finally:
        owner.resume.set()
        if sampler.ident is not None:
            sampler.join(timeout=5)
        if clearer.ident is not None:
            clearer.join(timeout=5)
        if sampler.is_alive() or clearer.is_alive():
            raise AssertionError("same-owner workers survived bounded cleanup") from sys.exc_info()[1]
    assert sample_done.is_set() and clear_done.is_set()
    assert owner.clear_acquired.is_set(), "clear never acquired after sample completion"
    assert len(results) == 1 and not isinstance(results[0], BaseException)
    assert not torch.equal(ambient_before, torch.get_rng_state())
    assert owner.retained_transitions == 0


def test_flat_prepared_restore_is_stale_after_same_owner_clear() -> None:
    """RED: a destination-issued candidate must not overwrite newer same-size rows."""
    owner = _flat()
    candidate = owner.prepare_serialized(owner.serialize(), expected_obs_dim=1, lineage=None)
    owner.clear()
    owner.push_recorded(*_flat_rows(offset=20.0))
    before = owner.serialize()
    with pytest.raises(ValueError, match="[Pp]repared|[Dd]estination|[Ss]tale"):
        owner.load_prepared(candidate, lineage=None)
    _assert_same_transport(before, owner.serialize())


def test_flat_prepared_restore_is_one_use() -> None:
    """RED: a second publication of the same prepared identity is forbidden."""
    owner = _flat()
    candidate = owner.prepare_serialized(owner.serialize(), expected_obs_dim=1, lineage=None)
    owner.load_prepared(candidate, lineage=None)
    before = owner.serialize()
    with pytest.raises(ValueError, match="[Pp]repared|[Cc]onsumed"):
        owner.load_prepared(candidate, lineage=None)
    _assert_same_transport(before, owner.serialize())


def test_per_prepared_restore_is_bound_to_issuing_owner() -> None:
    """RED: equal geometry cannot authorize another buffer's prepared handle."""
    source = _per(local=True)
    other = _per(local=True)
    source.update_unit_priorities(np.array([0], dtype=np.int64), torch.tensor([9.0], dtype=torch.float32))
    source.sample_batch(_per_request(), lineage=None)
    other.clear()
    other.push_recorded(*_flat_rows(offset=30.0))
    other.update_unit_priorities(np.array([3], dtype=np.int64), torch.tensor([0.02], dtype=torch.float32))
    other.configure_sampling(sampling_mode=_SUCCESSIVE, rng=np.random.Generator(np.random.PCG64(1337)), origin="authored")
    candidate = source.prepare_serialized(source.serialize(), expected_obs_dim=1, lineage=None)
    before = other.serialize()
    with pytest.raises(ValueError, match="[Pp]repared|[Ff]oreign|[Dd]estination"):
        other.load_prepared(candidate, lineage=None)
    _assert_same_transport(before, other.serialize())


def test_flat_prepared_restore_refuses_intervening_peer_operation() -> None:
    """RED: even a released no-draw peer lease invalidates a prior token."""
    owner = _flat()
    source = _flat()
    source.clear()
    source.push_recorded(*_flat_rows(offset=40.0))
    peer, participant = _peer()
    candidate = owner.prepare_serialized(source.serialize(), expected_obs_dim=1, lineage=None)
    with process_rng_domain().operation(participant=participant, operation_kind="hold", lineage=None):
        pass
    before = owner.serialize()
    with pytest.raises(ValueError, match="[Pp]repared|[Ss]tale|[Cc]urrency"):
        owner.load_prepared(candidate, lineage=None)
    _assert_same_transport(before, owner.serialize())
    assert peer is not None


def _repair_owner(kind: str) -> ReplayBuffer | PrioritizedReplayBuffer:
    return _flat() if kind == "flat" else _per(local=True)


def _live_replay_state(owner: ReplayBuffer | PrioritizedReplayBuffer) -> dict[str, Any]:
    """Include physical capacity rows and bookkeeping omitted by transport.

    Authority revisions may advance conservatively; they are not replay data.
    """
    fields = (
        "observations",
        "actions",
        "rewards",
        "rewards_extrinsic",
        "rewards_intrinsic",
        "rewards_shaping",
        "next_observations",
        "dones",
        "next_action_masks",
        "legality_recorded",
        "rewards_extrinsic_present",
        "rewards_intrinsic_present",
        "rewards_shaping_present",
    )
    state = {
        "transport": owner.serialize(),
        "storage": {name: None if (value := getattr(owner, name)) is None else value.clone() for name in fields},
        "capacity": owner.capacity,
        "device": owner.device,
        "position": owner.position,
        "healthy": owner._replay_healthy,
    }
    if isinstance(owner, PrioritizedReplayBuffer):
        state["id_to_slot"] = owner._id_to_slot.copy()
    else:
        state["has_wrapped"] = owner.has_wrapped
    return state


@pytest.mark.parametrize("kind", ["flat", "per"])
def test_validated_replay_cannot_bless_stale_destination_width(kind: str) -> None:
    """B1 causal RED: new issuance cannot authorize an old target-dependent DTO."""
    owner = _repair_owner(kind)
    saved = owner.serialize()
    validated = owner.validate_serialized(saved, expected_obs_dim=1)
    observations, actions, rewards, successors, dones, masks = _flat_rows(offset=20.0)
    owner.clear()
    owner.push_recorded(observations.repeat(1, 2), actions, rewards, successors.repeat(1, 2), dones, masks)
    before = _live_replay_state(owner)
    with pytest.raises(ValueError, match="[Oo]bs|[Ww]idth"):
        owner.prepare_serialized(saved, expected_obs_dim=2, lineage=None)
    _assert_same_transport(before, _live_replay_state(owner))
    with pytest.raises(ValueError):
        owner.materialize_validated(validated, lineage=None)
    _assert_same_transport(before, _live_replay_state(owner))


@pytest.mark.parametrize(
    ("kind", "field"),
    [
        ("flat", "observations"),
        ("flat", "next_action_masks"),
        ("per", "observations"),
        ("per", "next_action_masks"),
        ("per", "priorities"),
        ("per", "unit_ids"),
    ],
    ids=["flat-nonfinite", "flat-illegal-successor", "per-nonfinite", "per-illegal-successor", "per-priorities", "per-ids"],
)
def test_mutated_validation_material_cannot_gain_prepared_authority(kind: str, field: str) -> None:
    """B1 causal RED: returned mutable bytes must be revalidated before issuance."""
    owner = _repair_owner(kind)
    validated = owner.validate_serialized(owner.serialize(), expected_obs_dim=1)
    value = getattr(validated, field)
    if field == "unit_ids":
        value[0] = -1
    elif field == "next_action_masks":
        value[0].fill_(False)
    else:
        value[0] = float("nan")
    before = _live_replay_state(owner)
    with pytest.raises(ValueError):
        owner.materialize_validated(validated, lineage=None)
    _assert_same_transport(before, _live_replay_state(owner))


def test_prepared_replay_has_no_public_material_constructor() -> None:
    """B2 causal RED: callers cannot construct a payload-bearing authority object."""
    with pytest.raises(TypeError):
        PreparedReplay(object())


def test_prepared_replay_has_no_writable_payload_storage() -> None:
    """B2 causal RED: authentic identity must have no caller-rebindable material."""
    owner = _flat()
    candidate = owner.prepare_serialized(owner.serialize(), expected_obs_dim=1, lineage=None)
    before = _live_replay_state(owner)
    with pytest.raises(AttributeError):
        setattr(candidate, "_payload", object())
    _assert_same_transport(before, _live_replay_state(owner))


@pytest.mark.parametrize("kind", ["flat", "per"])
@pytest.mark.parametrize("attack", ["fabricated", "copied", "reinitialized"])
def test_prepared_handle_substitution_refuses_and_fresh_handle_publishes_once(kind: str, attack: str) -> None:
    owner = _repair_owner(kind)
    candidate = owner.prepare_serialized(owner.serialize(), expected_obs_dim=1, lineage=None)
    before = _live_replay_state(owner)
    if attack == "reinitialized":
        with pytest.raises(TypeError):
            type(candidate).__init__(candidate, object())
    else:
        if attack == "copied":
            try:
                counterfeit = copy.copy(candidate)
            except TypeError:
                counterfeit = None
        else:
            counterfeit = object.__new__(PreparedReplay)
        if counterfeit is not None:
            assert counterfeit is not candidate
            with pytest.raises(ValueError, match="[Pp]repared|[Ff]oreign|[Ff]abricated"):
                owner.load_prepared(counterfeit, lineage=None)
    _assert_same_transport(before, _live_replay_state(owner))
    # A refused admitted install advances domain currency: reprepare for success.
    fresh = owner.prepare_serialized(owner.serialize(), expected_obs_dim=1, lineage=None)
    owner.load_prepared(fresh, lineage=None)
    installed = _live_replay_state(owner)
    with pytest.raises(ValueError, match="[Pp]repared|[Cc]onsumed"):
        owner.load_prepared(fresh, lineage=None)
    _assert_same_transport(installed, _live_replay_state(owner))


def _incoming_repair_state(owner: ReplayBuffer | PrioritizedReplayBuffer) -> dict[str, Any]:
    incoming = owner.serialize()
    for name in ("observations", "next_observations", "rewards"):
        incoming[name].add_(40.0)
    incoming["actions"] = 1 - incoming["actions"]
    return incoming


@pytest.mark.parametrize("kind", ["flat", "per"])
def test_same_held_outer_lineage_prepares_and_installs_replay(kind: str) -> None:
    owner = _repair_owner(kind)
    peer, participant = _peer()
    incoming = _incoming_repair_state(owner)
    with process_rng_domain().operation(participant=participant, operation_kind="hold", lineage=None) as lease:
        candidate = owner.prepare_serialized(incoming, expected_obs_dim=1, lineage=lease)
        owner.load_prepared(candidate, lineage=lease)
        _assert_same_transport(incoming, owner.serialize())
    assert peer is not None


@pytest.mark.parametrize("kind", ["flat", "per"])
@pytest.mark.parametrize("interference", ["sibling-sample", "owner-mutation"])
def test_held_outer_preparation_refuses_intervening_work(kind: str, interference: str) -> None:
    owner, sibling = _repair_owner(kind), _flat()
    peer, participant = _peer()
    with process_rng_domain().operation(participant=participant, operation_kind="hold", lineage=None) as lease:
        candidate = owner.prepare_serialized(_incoming_repair_state(owner), expected_obs_dim=1, lineage=lease)
        if interference == "sibling-sample":
            assert sibling.sample(1, lineage=lease)["observations"].shape == (1, 1)
        else:
            owner.clear()
            owner.push_recorded(*_flat_rows(offset=20.0))
        before = _live_replay_state(owner)
        with pytest.raises(ValueError, match="[Pp]repar|[Dd]estination|[Ss]tale|[Cc]urrency"):
            owner.load_prepared(candidate, lineage=lease)
        _assert_same_transport(before, _live_replay_state(owner))
    assert peer is not None


class _PublicationObserver(ReplayCustody):
    """Retain real issued material and fail only an actual publication assignment."""

    _retained_material: Any

    def _issue_replay(self, payload: object, lease: RNGOperation) -> PreparedReplay:
        self._retained_material = payload
        return super()._issue_replay(payload, lease)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "actions" and getattr(self, "_fail_publication", False):
            raise RuntimeError("assignment fault after observations publication")
        super().__setattr__(name, value)


class _ObservedFlatReplay(_PublicationObserver, ReplayBuffer):
    pass


class _ObservedPrioritizedReplay(_PublicationObserver, PrioritizedReplayBuffer):
    pass


def _publication_owner(kind: str) -> _ObservedFlatReplay | _ObservedPrioritizedReplay:
    if kind == "flat":
        owner: _ObservedFlatReplay | _ObservedPrioritizedReplay = _ObservedFlatReplay(capacity=8, device=_CPU)
    else:
        owner = _ObservedPrioritizedReplay(capacity=8, alpha=0.6, beta=0.4, beta_annealing=False, device=_CPU)
        owner.configure_sampling(sampling_mode=_SUCCESSIVE, rng=np.random.Generator(np.random.PCG64(719)), origin="authored")
    owner.push_recorded(*_flat_rows())
    return owner


def _install_real_historical_archive(owner: ReplayBuffer | PrioritizedReplayBuffer) -> None:
    observations, actions, rewards, successors, dones, masks = _flat_rows()
    owner.clear()
    owner.push_recorded(
        observations,
        actions,
        RewardTensor(
            total=rewards.total,
            extrinsic=rewards.total,
            intrinsic=torch.zeros_like(rewards.total),
            shaping=torch.zeros_like(rewards.total),
        ),
        successors,
        dones,
        masks,
    )
    saved = owner.serialize()
    fields = (
        "replay_kind",
        "format_version",
        "capacity",
        "position",
        "observations",
        "actions",
        "rewards",
        "rewards_extrinsic",
        "rewards_intrinsic",
        "rewards_shaping",
        "next_observations",
        "dones",
    )
    if isinstance(owner, PrioritizedReplayBuffer):
        fields += ("alpha", "beta", "beta_initial", "beta_annealing", "priorities", "max_priority", "size_current")
    else:
        fields += ("size",)
    legacy = {name: saved[name] for name in fields}
    legacy["format_version"] = 4
    owner.load_from_serialized(legacy, lineage=None)
    assert len(owner.historical_archives) == 1
    owner.push_recorded(*_flat_rows(offset=10.0))


@pytest.mark.parametrize("kind", ["flat", "per"])
def test_reinitialized_authentic_handle_cannot_substitute_other_issued_material(kind: str) -> None:
    """B2 causal RED: current identity cannot authenticate another issuance's bytes."""
    owner = _publication_owner(kind)
    substitution = _incoming_repair_state(owner)
    substitution["observations"].add_(30.0)
    earlier = owner.prepare_serialized(substitution, expected_obs_dim=1, lineage=None)
    other_material = owner._retained_material
    intended = _incoming_repair_state(owner)
    current = owner.prepare_serialized(intended, expected_obs_dim=1, lineage=None)
    assert current is not earlier
    before = _live_replay_state(owner)
    try:
        type(current).__init__(current, other_material)
    except TypeError:
        pass
    else:
        with pytest.raises(ValueError, match="[Pp]repar|[Mm]aterial|[Ii]ssu"):
            owner.load_prepared(current, lineage=None)
    _assert_same_transport(before, _live_replay_state(owner))
    fresh = owner.prepare_serialized(intended, expected_obs_dim=1, lineage=None)
    owner.load_prepared(fresh, lineage=None)
    _assert_same_transport(intended, owner.serialize())


@pytest.mark.parametrize("kind", ["flat", "per"])
@pytest.mark.parametrize("stage", ["tensor-copy", "archive-copy"])
def test_replay_staging_fault_preserves_full_live_state_and_healthy_use(kind: str, stage: str, monkeypatch: pytest.MonkeyPatch) -> None:
    owner = _publication_owner(kind)
    if stage == "archive-copy":
        _install_real_historical_archive(owner)
    incoming = _incoming_repair_state(owner)
    candidate = owner.prepare_serialized(incoming, expected_obs_dim=1, lineage=None)
    material = owner._retained_material
    before = _live_replay_state(owner)
    staged: list[Any] = []
    original_clone, original_merge = torch.Tensor.clone, owner._merge_archives

    def clone_then_fail(value: torch.Tensor, *args: Any, **kwargs: Any) -> torch.Tensor:
        owned = original_clone(value, *args, **kwargs)
        if value.shape == material.observations.shape and torch.equal(value, material.observations):
            staged.append(owned)
            raise RuntimeError("staged tensor copy fault")
        return owned

    def merge_then_fail(incoming_archives: Any) -> Any:
        owned = original_merge(incoming_archives)
        assert len(owned) == 1
        staged.extend(owned)
        raise RuntimeError("staged archive copy fault")

    with monkeypatch.context() as fault:
        if stage == "tensor-copy":
            fault.setattr(torch.Tensor, "clone", clone_then_fail)
        else:
            fault.setattr(owner, "_merge_archives", merge_then_fail)
        with pytest.raises(RuntimeError, match="staged .* copy fault"):
            owner.load_prepared(candidate, lineage=None)
    assert len(staged) == 1, "fault must follow one real selected staging operation"
    if stage == "tensor-copy":
        _assert_same_transport(staged[0], material.observations)
    _assert_same_transport(before, _live_replay_state(owner))
    fresh = owner.prepare_serialized(incoming, expected_obs_dim=1, lineage=None)
    owner.load_prepared(fresh, lineage=None)
    _assert_same_transport(incoming, owner.serialize())
    assert owner.sample(1, lineage=None)["observations"].shape == (1, 1)


def test_per_generator_staging_fault_preserves_full_live_state_and_healthy_use(monkeypatch: pytest.MonkeyPatch) -> None:
    owner = _publication_owner("per")
    assert isinstance(owner, PrioritizedReplayBuffer)
    incoming = _incoming_repair_state(owner)
    candidate = owner.prepare_serialized(incoming, expected_obs_dim=1, lineage=None)
    before = _live_replay_state(owner)
    original = owner._clone_sampler
    staged: list[Any] = []

    def clone_sampler_then_fail(sampler: Any) -> Any:
        owned = original(sampler)
        assert owned.rng is not None and owned.rng is not sampler.rng
        _assert_same_transport(owner._sampler_metadata(sampler), owner._sampler_metadata(owned))
        staged.append(owned)
        raise RuntimeError("staged PER generator copy fault")

    with monkeypatch.context() as fault:
        fault.setattr(owner, "_clone_sampler", clone_sampler_then_fail)
        with pytest.raises(RuntimeError, match="staged PER generator copy fault"):
            owner.load_prepared(candidate, lineage=None)
    assert len(staged) == 1
    _assert_same_transport(before, _live_replay_state(owner))
    fresh = owner.prepare_serialized(incoming, expected_obs_dim=1, lineage=None)
    owner.load_prepared(fresh, lineage=None)
    _assert_same_transport(incoming, owner.serialize())
    assert owner.sample_batch(_per_request(), lineage=None).observations.shape == (1, 1)


@pytest.mark.parametrize("kind", ["flat", "per"])
def test_partial_replay_publication_quarantines_sample_prepare_install_and_clear(kind: str) -> None:
    owner = _publication_owner(kind)
    incoming = _incoming_repair_state(owner)
    before = _live_replay_state(owner)
    candidate = owner.prepare_serialized(incoming, expected_obs_dim=1, lineage=None)
    owner._fail_publication = True
    with pytest.raises(RuntimeError, match="assignment fault after observations publication"):
        owner.load_prepared(candidate, lineage=None)
    assert not torch.equal(before["storage"]["observations"], owner.observations)
    _assert_same_transport(owner.observations[:3], incoming["observations"])
    _assert_same_transport(owner.actions, before["storage"]["actions"])
    for operation in (
        lambda: owner.sample(1, lineage=None),
        lambda: owner.prepare_serialized(incoming, expected_obs_dim=1, lineage=None),
        lambda: owner.load_prepared(candidate, lineage=None),
        owner.clear,
        owner.serialize,
    ):
        with pytest.raises(RuntimeError, match="quarantined after uncertain publication"):
            operation()


@pytest.mark.parametrize("kind", ["flat", "per"])
def test_installed_replay_owns_bytes_independent_of_input_and_retained_candidate(kind: str) -> None:
    owner = _publication_owner(kind)
    incoming = _incoming_repair_state(owner)
    expected = copy.deepcopy(incoming)
    candidate = owner.prepare_serialized(incoming, expected_obs_dim=1, lineage=None)
    material = owner._retained_material
    incoming["observations"].fill_(900.0)
    if isinstance(owner, PrioritizedReplayBuffer):
        incoming["priorities"].fill(70.0)
        incoming["unit_ids"].fill(999)
    owner.load_prepared(candidate, lineage=None)
    _assert_same_transport(expected, owner.serialize())
    installed = _live_replay_state(owner)
    material.observations.fill_(800.0)
    material.next_observations.fill_(700.0)
    material.actions.fill_(0)
    if isinstance(owner, PrioritizedReplayBuffer):
        material.priorities.fill(60.0)
        material.unit_ids.fill(888)
        material.sampler.rng.random()
    _assert_same_transport(installed, _live_replay_state(owner))


def test_owned_per_sampling_advances_only_its_transport_generator() -> None:
    """Healthy algorithm control: qualified local PER does not draw global NumPy."""
    owner = _per(local=True)
    ambient_before = _ambient_cpu_state()
    local_before = owner.serialize()["sampling_rng"]
    owner.sample_batch(_per_request(), lineage=None)
    state = owner.serialize()
    _assert_same_transport(ambient_before, _ambient_cpu_state())
    assert pickle.dumps(state["sampling_rng"]) != pickle.dumps(local_before)
    restored = PrioritizedReplayBuffer(capacity=8, alpha=0.6, beta=0.4, beta_annealing=False, device=_CPU)
    restored.load_from_serialized(state, lineage=None)
    _assert_same_transport(state["sampling_rng"], restored.serialize()["sampling_rng"])
    first = owner.sample_batch(_per_request(), lineage=None)
    second = restored.sample_batch(_per_request(), lineage=None)
    _assert_same_selected_batch(first, second)
    _assert_same_transport(owner.serialize()["sampling_rng"], restored.serialize()["sampling_rng"])
    _assert_same_transport(ambient_before, _ambient_cpu_state())


def test_recurrent_priority_sampling_advances_only_its_transport_generator() -> None:
    """Healthy algorithm control: qualified local sequence priority owns its draws."""
    owner = _sequence_qualified(prioritized=True)
    ambient_before = _ambient_cpu_state()
    local_before = owner.serialize()["priority_state"]["rng"]
    owner.sample_batch(_sequence_request(), lineage=None)
    state = owner.serialize()
    _assert_same_transport(ambient_before, _ambient_cpu_state())
    assert pickle.dumps(state["priority_state"]["rng"]) != pickle.dumps(local_before)
    restored = _sequence_qualified(prioritized=True)
    restored.load_from_serialized(state, lineage=None)
    _assert_same_transport(state["priority_state"]["rng"], restored.serialize()["priority_state"]["rng"])
    first = owner.sample_batch(_sequence_request(), lineage=None)
    second = restored.sample_batch(_sequence_request(), lineage=None)
    _assert_same_selected_batch(first, second)
    _assert_same_transport(owner.serialize()["priority_state"]["rng"], restored.serialize()["priority_state"]["rng"])
    _assert_same_transport(ambient_before, _ambient_cpu_state())


def test_direct_configured_per_uses_global_numpy_not_its_owned_generator() -> None:
    """Healthy characterization: direct adapter keeps its selected global route."""
    owner = _per(local=True)
    local_before = owner.serialize()["sampling_rng"]
    python_before, numpy_before, torch_before = _ambient_cpu_state()
    batch = owner.sample(1, lineage=None)
    assert batch["observations"].shape == (1, 1)
    _assert_same_transport(local_before, owner.serialize()["sampling_rng"])
    assert random.getstate() == python_before
    assert pickle.dumps(np.random.get_state()) != pickle.dumps(numpy_before)
    assert torch.equal(torch.get_rng_state(), torch_before)


def test_global_sample_primitives_advance_their_selected_ambient_stream() -> None:
    """Healthy characterization: direct flat/PER/recurrent paths keep their streams."""
    torch_before = torch.get_rng_state().clone()
    _flat().sample(1, lineage=None)
    assert not torch.equal(torch_before, torch.get_rng_state())

    numpy_before = pickle.dumps(np.random.get_state())
    _per(local=False).sample(1, lineage=None)
    assert pickle.dumps(np.random.get_state()) != numpy_before

    python_before = random.getstate()
    _sequence_direct().sample_sequences(1, 2, lineage=None)
    assert random.getstate() != python_before


_REPLAY_IMPORTS = (
    "townlet.training.replay_buffer",
    "townlet.training.prioritized_replay_buffer",
    "townlet.training.sequential_replay_buffer",
    "townlet.training.replay_contract",
)


def _resolved_module_path(name: str) -> str:
    location = importlib.import_module(name).__file__
    assert location is not None
    return str(Path(location).resolve())


def _replay_poison_child(queue: Any) -> None:
    role = "replay_poison"
    qualified = bootstrap._child_identity(role)
    if qualified:
        path = Path(os.environ["BAC_QUAL_OUTPUT"]) / f"spawn-identity-{role}.json"
        identity = json.loads(path.read_text())
        identity["ppid"] = os.getppid()
        identity["replay_imports"] = {name: _resolved_module_path(name) for name in _REPLAY_IMPORTS}
        path.write_text(json.dumps(identity, sort_keys=True))
    flat, per, recurrent = _flat(), _per(local=False), _sequence_direct()
    saved = [(owner, owner.serialize()) for owner in (flat, per, recurrent)]
    physical = [(owner, _live_replay_state(owner)) for owner in (flat, per)]
    ambient = _ambient_cpu_state()
    domain = process_rng_domain()
    with domain.operation(participant=flat.rng_participant, operation_kind="prepare", lineage=None) as lease:
        prepared = [owner.prepare_serialized(state, expected_obs_dim=1, lineage=lease) for owner, state in saved]
        domain.poison(operation=lease, error=RuntimeError("replay poison control"))
    for owner, draw in (
        (flat, lambda: flat.sample(1, lineage=None)),
        (per, lambda: per.sample(1, lineage=None)),
        (recurrent, lambda: recurrent.sample_sequences(1, 2, lineage=None)),
    ):
        with pytest.raises(RuntimeError, match="Ambient RNG domain is poisoned after failed restoration"):
            draw()
        assert owner is not None
    for owner, state in saved:
        _assert_live_rows_unchanged(owner, state)
        _assert_same_transport(state, owner.serialize())
    for owner, state in physical:
        _assert_same_transport(state, _live_replay_state(owner))
    for (owner, state), candidate in zip(saved, prepared, strict=True):
        for operation in (
            partial(owner.prepare_serialized, state, expected_obs_dim=1, lineage=None),
            partial(owner.load_prepared, candidate, lineage=None),
        ):
            with pytest.raises(RuntimeError, match="Ambient RNG domain is poisoned after failed restoration"):
                operation()
            _assert_same_transport(state, owner.serialize())
        owner.clear()
        cleared = owner.serialize()
        assert owner.retained_transitions == 0
        assert domain.status()[2], "owner-local clear cannot heal the process domain"
        for operation in (
            partial(owner.prepare_serialized, state, expected_obs_dim=1, lineage=None),
            partial(owner.load_prepared, candidate, lineage=None),
            partial(_direct_draw, "recurrent" if owner is recurrent else "per" if owner is per else "flat", owner),
        ):
            with pytest.raises(RuntimeError, match="Ambient RNG domain is poisoned after failed restoration"):
                operation()
            _assert_same_transport(cleared, owner.serialize())
    _assert_same_transport(ambient, _ambient_cpu_state())
    queue.put(("replay poison fail closed", os.getpid(), os.getppid(), qualified))


def test_isolated_replay_poison_refuses_all_direct_samplers() -> None:
    """Consumer fail-closed control; public poison occurs only in a fresh child."""
    role = "replay_poison"
    qualified = bootstrap._qualification_active()
    parent_pid = os.getpid()
    ambient = _ambient_cpu_state()
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    process = context.Process(target=_replay_poison_child, args=(queue,), name=role)
    started = False
    try:
        process.start()
        started = True
        process.join(90)
        assert not process.is_alive() and process.exitcode == 0
        message, queued_pid, child_ppid, child_qualified = queue.get(timeout=5)
        assert message == "replay poison fail closed"
        assert queued_pid == process.pid and child_ppid == parent_pid
        assert child_qualified is qualified
        if qualified:
            manifest_sha = hashlib.sha256(Path(os.environ["BAC_QUAL_MANIFEST"]).read_bytes()).hexdigest()
            observation = {
                "process_pid": process.pid,
                "queued_pid": queued_pid,
                "exitcode": process.exitcode,
                "qualified": qualified,
                "message": message,
                "manifest_sha256": manifest_sha,
                "parent_pid": parent_pid,
            }
            destination = Path(os.environ["BAC_QUAL_OUTPUT"]) / f"spawn-observation-{role}.json"
            with destination.open("x") as output:
                json.dump(observation, output, sort_keys=True)
    finally:
        if started and process.is_alive():
            process.terminate()
            process.join(10)
        survived = started and process.is_alive()
        queue.close()
        queue.join_thread()
        if not survived:
            process.close()
        if survived:
            raise AssertionError("replay poison child survived bounded cleanup") from sys.exc_info()[1]
    assert not process_rng_domain().status()[2]
    _assert_same_transport(ambient, _ambient_cpu_state())
