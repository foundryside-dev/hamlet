"""Exact-ID curiosity ownership; ENV supplies identity, BANK owns local phases.

Snapshots are owned diagnostic values, not a parent restore format. Global
completion capabilities remain live and never enter world-local snapshots.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager
from copy import copy, deepcopy
from dataclasses import dataclass, replace
from functools import partial, wraps
from threading import RLock
from typing import Any, Protocol, cast

import torch

from townlet.config.exploration_policy import IntrinsicTransitionContext, ResolvedExplorationPolicy
from townlet.config.world_roster import WorldAcceptedEpisode, WorldOwnerReceipt
from townlet.exploration.parent_custody import (
    BankParentCustody,
    RestoreInstallationOutcome,
    _bank_call,
    _begin_installation,
    _check_installation_lookup,
    _finish_installation,
    _lineage,
    _new_installation_outcome,
    _retain_bank,
    _validate_installation_outcome,
)
from townlet.exploration.provider_factory import make_backend
from townlet.exploration.rng_custody import RNGOperation, process_rng_domain
from townlet.exploration.world_curiosity_state import (
    CuriosityEventId,
    CuriosityStepStamp,
    OwnedWorldBackend,
    ServiceClock,
    SharedWorldBackend,
    WorldCuriosityDescriptor,
    WorldRNGState,
)
from townlet.training.episode import LaneOutcome, freeze_lane_outcome, lane_outcome_state


class AcceptedEpisodeValidator(Protocol):
    def __call__(self, *, accepted: WorldAcceptedEpisode) -> None: ...


class ReceiptIssuer(Protocol):
    @property
    def owner(self) -> object: ...

    def issue(self, *, kind: str, payload: Mapping[str, Any]) -> WorldOwnerReceipt: ...


@dataclass(frozen=True)
class AllocationEstimate:
    schema: str
    operation: str
    scope: str
    device: str
    model_dtype: str
    observation_dtype: str
    world_count: int
    participant_count: int
    instance_count: int
    known_tensor_bytes: int
    components: tuple[tuple[str, int], ...]
    assumptions: tuple[str, ...]
    unknown_components: tuple[str, ...]


@dataclass(frozen=True)
class WorldServiceReceipt:
    scope: str
    world_id: str | None
    event_ids: tuple[CuriosityEventId, ...]
    eligible: bool
    clock: ServiceClock | None
    admitted_rows: int
    consumed_rows: int
    dropped_rows: int
    pending_rows: int
    optimizer_updates: int
    mandatory_service_updates: int
    last_loss: float


class CuriosityReward:
    def __init__(
        self, raw: torch.Tensor, scales: torch.Tensor, eligible: torch.Tensor, event_ids: tuple[CuriosityEventId, ...], scope: str
    ):
        self._raw, self._scales, self._eligible = (value.detach().clone() for value in (raw, scales, eligible))
        self.event_ids, self.scope = event_ids, scope

    @property
    def raw(self) -> torch.Tensor:
        return self._raw.clone()

    @property
    def scales(self) -> torch.Tensor:
        return self._scales.clone()

    @property
    def eligible(self) -> torch.Tensor:
        return self._eligible.clone()


@dataclass
class PreparedBankCompletion:
    destination: object
    revision: int
    accepted: WorldAcceptedEpisode
    boundary_key: int
    completion_content: Any
    participated_world_ids: tuple[str, ...]
    dispositions: tuple[tuple[str, str], ...]
    values: dict[str, tuple[list[float], float]]
    prepared_receipt: WorldOwnerReceipt
    used: bool


@dataclass(frozen=True)
class _RestoreCohort:
    bank: object
    input_rngs: list[WorldRNGState]
    owners: dict[str, OwnedWorldBackend]
    shared: SharedWorldBackend | None
    validation_rng: WorldRNGState | None


def _same(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, torch.Tensor):
        return left.shape == right.shape and left.dtype == right.dtype and left.device == right.device and torch.equal(left, right)
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(_same(left[key], right[key]) for key in left)
    if isinstance(left, (tuple, list)):
        return len(left) == len(right) and all(_same(a, b) for a, b in zip(left, right, strict=True))
    return bool(left == right)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _serialized(method: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(method)
    def invoke(self: Any, *args: Any, **kwargs: Any) -> Any:
        kind = "call"
        if method.__name__ == "install_restore":
            kind = "install"
        cell = None
        if kind == "install":
            with self._lock:
                cell = _begin_installation(self._restore_observation(kwargs.get("prepared")), self)
        try:
            with _bank_call(self, method.__name__):
                previous = self._installation_active
                if cell is not None:
                    self._installation_active = cell
                try:
                    with self._admission(kind):
                        result = method(self, *args, **kwargs)
                finally:
                    if cell is not None:
                        self._installation_active = previous
            if cell is not None:
                cell.returned_normally = True
            return result
        finally:
            if cell is not None:
                _finish_installation(cell)

    return invoke


def _preparation(method: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(method)
    def invoke(self: Any, *args: Any, **kwargs: Any) -> Any:
        # Guard spans both admitted phases and the operation-idle cohort gap.
        with _bank_call(self, method.__name__):
            return method(self, *args, **kwargs)

    return invoke


def _allocation_estimate(
    policy: ResolvedExplorationPolicy,
    descriptor: WorldCuriosityDescriptor,
    device: torch.device,
    operation: str,
    participants: int,
    outcome_bytes: int,
) -> AllocationEstimate:
    d, a = descriptor.observation_dim, descriptor.action_dim
    if policy.curiosity_scope == "per_world":
        k = len(descriptor.world_ids)
    else:
        k = 1
    model = gradients = queue = 0
    if policy.strategy in ("rnd", "adaptive_rnd"):
        e = policy.rnd_feature_dim
        p = d * 256 + 256 + 256 * 128 + 128 + 128 * e + e
        model, gradients, queue = 8 * p, 12 * p + 24, 4 * d * policy.max_pending_rows
    elif policy.strategy == "icm":
        h, f = policy.provider_parameters["hidden_dim"], policy.provider_parameters["feature_dim"]
        p = sum(x * y + y for x, y in ((d, h), (h, f), (2 * f, h), (h, a), (f + a, h), (h, f)))
        model, gradients, queue = 4 * p, 12 * p + 48, policy.max_pending_rows * (8 * d + 8)
    components: tuple[tuple[str, int], ...] = (
        ("eager_model_copy_peak", (k + 1) * model + k * queue),
        ("trained_reserve", k * (model + gradients + queue)),
    )
    if operation == "complete":
        if policy.strategy == "adaptive_rnd":
            history = 16 * (policy.survival_window + 1)
        else:
            history = 0
        components = (("outcome_transport", 2 * outcome_bytes), ("history_workspace", history), ("model_copies", 0))
    if operation == "construct":
        known_bytes = max(value for _, value in components)
    else:
        known_bytes = sum(value for _, value in components)
    return AllocationEstimate(
        "curiosity-allocation-estimate-v1",
        operation,
        policy.curiosity_scope,
        str(device),
        str(torch.float32),
        str(torch.float32),
        len(descriptor.world_ids),
        participants,
        k,
        known_bytes,
        components,
        (
            "float32 models; lazy Adam and gradients reserved",
            "sequential completion candidates; retained Python histories <= participants*window",
        ),
        ("Python containers/count integer keys", "RNG tensors", "allocator/activation/library workspace"),
    )


def allocation_estimate(
    *, policy: ResolvedExplorationPolicy, descriptor: WorldCuriosityDescriptor, device: torch.device | str
) -> AllocationEstimate:
    """Pure known-tensor estimate; unknown resident/workspace costs stay labeled."""
    return _allocation_estimate(policy, descriptor, torch.device(device), "construct", 0, 0)


class _CandidateRefusalError(ValueError):
    """Expected off-side algorithm refusal, with no live candidate publication."""


def _observation_boundary(method: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(method)
    def invoke(self: Any, *args: Any, **kwargs: Any) -> Any:
        observations, revision, publication = self._observations, self.mutation_revision, self._publications
        try:
            return method(self, *args, **kwargs)
        except BaseException as error:
            if self._observations != observations or self._publications != publication:
                if self.mutation_revision == revision:
                    self.mutation_revision += 1
                if not isinstance(error, _CandidateRefusalError):
                    self._failed = True
            raise

    return invoke


def _same_outcome(left: LaneOutcome, right: LaneOutcome) -> bool:
    for field in (
        "batch_episode",
        "planned_horizon",
        "reward_total",
        "reward_extrinsic",
        "reward_intrinsic",
        "reward_shaping",
        "policy_entropy",
        "world_id",
        "world_episode_seq",
    ):
        if not _same(getattr(left, field), getattr(right, field)):
            return False
    for field in ("agent_idx", "reason", "survival_time", "final_observation", "final_meters"):
        if not _same(getattr(left.outcome, field), getattr(right.outcome, field)):
            return False
    return True


class CuriosityBank:
    # Restore staging copies __dict__; these execution/lifetime facts cannot be staged.
    __slots__ = ("_entered", "_lineage", "_completion_uncertain", "_installation_active", "__dict__", "__weakref__")

    def __init__(
        self,
        *,
        policy: ResolvedExplorationPolicy,
        descriptor: WorldCuriosityDescriptor,
        device: torch.device | str,
        validate_accepted_episode: AcceptedEpisodeValidator,
        issuer_factory: Callable[[object], ReceiptIssuer],
        report_allocation: Callable[[AllocationEstimate], None],
    ):
        _require(isinstance(policy, ResolvedExplorationPolicy), "actual resolved policy required")
        self._lock = RLock()
        self.policy = ResolvedExplorationPolicy.from_dict(policy.to_dict())
        self.descriptor = WorldCuriosityDescriptor.from_dict(descriptor.to_dict())
        ids = self.descriptor.world_ids
        _require(
            bool(ids) and len(set(ids)) == len(ids) and all(type(world) is str and bool(world) for world in ids),
            "exact declared IDs required",
        )
        expected = WorldCuriosityDescriptor.from_policy(
            self.policy,
            world_ids=ids,
            observation_dim=descriptor.observation_dim,
            action_dim=descriptor.action_dim,
            training_seed=descriptor.training_seed,
        )
        _require(expected.to_dict() == self.descriptor.to_dict(), "policy/descriptor mismatch")
        self.device = torch.device(device)
        _require(
            self.device.type in ("cpu", "cuda") and (self.device.type != "cuda" or self.device.index is not None),
            "explicit CPU/CUDA device required",
        )
        _require(torch.get_default_dtype() == torch.float32, "bank requires declared float32 model profile")
        _require(self.policy.strategy == "none" or descriptor.observation_dim > 0, "selected provider requires positive width")
        _require(
            callable(validate_accepted_episode) and callable(issuer_factory) and callable(report_allocation), "required owner callbacks"
        )
        self._validate, self._report = validate_accepted_episode, report_allocation
        self._issuer = issuer_factory(self)
        _require(self._issuer.owner is self, "issuer must belong to actual bank")
        self.scope, self.world_ids = self.policy.curiosity_scope, ids
        self.mutation_revision = 0
        self._observations = 0
        self._publications = 0
        self._completion_payload: dict[str, Any] = {}
        self._completion_outcomes: tuple[LaneOutcome, ...] = ()
        self._completion_values: dict[str, tuple[list[float], float]] = {}
        self._failed = False
        self._completion_uncertain = False
        self._installation_active: Any = None
        self._quarantine: tuple[WorldAcceptedEpisode, str] | None = None
        self._accepted: WorldAcceptedEpisode | None = None
        self._activation: WorldOwnerReceipt | None = None
        self._pending: dict[str, Any] | None = None
        self._prepared: PreparedBankCompletion | None = None
        self._committed: tuple[PreparedBankCompletion, WorldOwnerReceipt] | None = None
        self._history: dict[str, Any] | None = None
        self._historical_step: dict[str, Any] | None = None
        self._restore_tokens: dict[object, Any] = {}
        self._initialization_origin: dict[str, Any] | None = None
        self._curiosity_epoch = 0
        self._private_initialized = False
        self._owners: dict[str, OwnedWorldBackend] = {}
        self._shared: Any = None
        self._cursor: dict[str, dict[str, Any]] = {
            world: dict(accepted_episode_seq=0, eligible_seq=0, cumulative_service_position=0, participated=False, disposition=None)
            for world in ids
        }
        self._cache: dict[str, dict[str, Any]] = {world: {} for world in ids}
        self._estimate = self._allocation("construct", 0, 0)
        self._report(self._estimate)
        devices: tuple[int, ...]
        if self.device.type == "cpu":
            devices = ()
        else:
            devices = (cast(int, self.device.index),)
        self._devices = devices
        self._entered = False
        self._lineage: RNGOperation | None = None
        self._rng_participant = process_rng_domain().register(
            owner=self, cuda_devices=devices, entrypoints=frozenset({"call", "prepare", "install"})
        )
        private_ids: tuple[str, ...] = ()
        if self.scope == "per_world":
            private_ids = tuple(sorted(ids))
        for world in private_ids:
            rng = WorldRNGState.create(descriptor=self.descriptor, world_id=world, cuda_devices=devices)
            self._owners[world] = OwnedWorldBackend.construct(rng=rng, factory=partial(self._factory, world))
        if self.scope == "shared":
            self._shared = SharedWorldBackend.construct(factory=partial(self._factory, None, None), cuda_devices=devices)

    def retain_parent_custody(self) -> AbstractContextManager[BankParentCustody]:
        """Retain this BANK for a direct controller, outside runtime delegation."""
        return _retain_bank(self)

    def _restore_observation(self, prepared: Any) -> RestoreInstallationOutcome | None:
        from townlet.exploration.curiosity_checkpoint import PreparedCuriosityRestore

        if type(prepared) is not PreparedCuriosityRestore:
            return None
        record = self._restore_tokens.get(prepared)
        return None if record is None else record[6]

    def restore_installation_outcome(self, *, prepared: Any) -> RestoreInstallationOutcome:
        """Read the preallocated first-attempt observation without a native operation.

        Lookup requires an unconsumed genuine handle. Retain the returned object
        to read its immutable result after consumption, failure or domain poison.
        An unconsumed standalone retry does not rewrite the first attempt.
        """
        with self._lock:
            _check_installation_lookup(self, busy=self._entered or self._installation_active is not None)
            outcome = self._restore_observation(prepared)
            _require(outcome is not None, "foreign or consumed restore observation handle")
            assert outcome is not None
            _validate_installation_outcome(outcome, self)
            return outcome

    @contextmanager
    def _admission(self, kind: str) -> Iterator[RNGOperation]:
        domain = process_rng_domain()
        with domain.admission(lineage=_lineage(self)), self._lock:
            if self._entered:
                raise RuntimeError("curiosity bank reentry is forbidden")
            published = self._publications
            invocation = domain.device_invocation(
                participant=self._rng_participant, operation_kind=kind, lineage=_lineage(self), cuda_devices=self._devices
            )
            entered = False
            observation = self._installation_active if kind == "install" else None
            try:
                try:
                    with invocation as lineage:
                        entered = True
                        if observation is not None:
                            observation.operation_entered = True
                            observation.refresh()
                        self._entered, self._lineage = True, lineage
                        yield lineage
                finally:
                    try:
                        if entered:
                            if observation is not None:
                                observation.completion = 3  # Uncertified until the actual invocation reports.
                                observation.refresh()
                            failed_completion = invocation.completion_failed()
                            if observation is not None:
                                observation.completion = 2 if failed_completion else 1
                                observation.refresh()
                            if failed_completion:
                                object.__setattr__(self, "_completion_uncertain", True)
                    finally:
                        self._entered, self._lineage = False, None
            except BaseException:
                if self._publications != published:
                    self._failed = True
                raise

    def _factory(self, world: str | None, rng: WorldRNGState | None) -> Any:
        descriptor = None
        if world is not None:
            descriptor = self.descriptor
        return make_backend(
            self.policy,
            world_id=world,
            obs_dim=self.descriptor.observation_dim,
            action_dim=self.descriptor.action_dim,
            device=self.device,
            rng=rng,
            descriptor=descriptor,
        )

    def _allocation(self, operation: str, participants: int, outcome_bytes: int) -> AllocationEstimate:
        return _allocation_estimate(self.policy, self.descriptor, self.device, operation, participants, outcome_bytes)

    def _healthy(self) -> None:
        if self._failed or self._completion_uncertain:
            raise RuntimeError("curiosity bank quarantined")

    def _auth(self, accepted: WorldAcceptedEpisode) -> None:
        self._validate(accepted=accepted)
        _require(accepted is self._accepted, "bank accepted identity mismatch")

    def _available(self) -> None:
        self._healthy()
        _require(self._prepared is None, "completion transaction pending")

    def _call(self, world: str, operation: Callable[[Any], Any]) -> Any:
        self._observations += 1
        try:
            if self.scope == "per_world":
                return self._owners[world].call(lambda backend, sources: operation(backend), lineage=self._lineage)
            return self._shared.call(operation, lineage=self._lineage)
        except BaseException:
            self._failed = True
            raise

    @_serialized
    def begin_episode(self, *, accepted: WorldAcceptedEpisode) -> WorldOwnerReceipt:
        self._available()
        self._validate(accepted=accepted)
        if accepted is self._accepted:
            assert self._activation is not None
            return self._activation
        _require(
            set(accepted.world_ids) == set(self.world_ids) and len(accepted.world_ids) == len(self.world_ids),
            "accepted declaration mismatch",
        )
        _require(self._pending is None or self._pending["serviced"], "unfinished step")
        for world, episode in zip(accepted.world_ids, accepted.world_episode_seqs, strict=True):
            cursor = self._cursor[world]
            _require(type(episode) is int and episode == cursor["accepted_episode_seq"] + 1, "accepted episode must advance once")
            _require(
                cursor["accepted_episode_seq"] == 0 or cursor["disposition"] is not None or self._private_initialized,
                "unfinished accepted episode",
            )
        receipt = self._issuer.issue(kind="activation", payload={"accepted": accepted})
        for world, episode in zip(accepted.world_ids, accepted.world_episode_seqs, strict=True):
            self._cursor[world].update(accepted_episode_seq=episode, eligible_seq=0, participated=False, disposition=None)
            self._cache[world] = {}
        self._accepted, self._activation, self._pending, self._committed = accepted, receipt, None, None
        self._history, self._historical_step = None, None
        self._private_initialized = False
        self._completion_payload, self._completion_outcomes, self._completion_values = {}, (), {}
        self.mutation_revision += 1
        return receipt

    @_serialized
    def prepare_step_stamp(
        self, *, accepted: WorldAcceptedEpisode, world_ids: tuple[str, ...], active_on_entry: torch.Tensor, vector_tick: int
    ) -> CuriosityStepStamp:
        self._available()
        self._auth(accepted)
        _require(world_ids == accepted.world_ids, "row binding mismatch")
        _require(type(vector_tick) is int and vector_tick >= 0, "invalid vector tick")
        _require(
            isinstance(active_on_entry, torch.Tensor)
            and active_on_entry.shape == (len(world_ids),)
            and active_on_entry.dtype == torch.bool
            and active_on_entry.layout == torch.strided
            and active_on_entry.device == self.device,
            "eligibility geometry mismatch",
        )
        _require(all(self._cursor[world]["disposition"] is None for world in world_ids), "episode disposed")
        if self._pending is not None:
            pending = self._pending
            if pending["tick"] == vector_tick and _same(pending["active"], active_on_entry):
                return cast(CuriosityStepStamp, pending["stamp"])
            _require(pending["serviced"] and vector_tick > pending["tick"], "unfinished or regressing preparation")
        sequences = tuple(self._cursor[world]["eligible_seq"] + int(active_on_entry[i]) for i, world in enumerate(world_ids))
        events = tuple(
            CuriosityEventId(self._curiosity_epoch, world, episode, seq)
            for world, episode, seq in zip(world_ids, accepted.world_episode_seqs, sequences, strict=True)
        )
        stamp = CuriosityStepStamp(
            event_ids=events,
            world_ids=world_ids,
            world_episode_seqs=torch.tensor(accepted.world_episode_seqs, dtype=torch.int64, device=self.device),
            eligible_seqs=torch.tensor(sequences, dtype=torch.int64, device=self.device),
            eligible=active_on_entry,
        )
        self._pending = dict(
            stamp=stamp,
            tick=vector_tick,
            active=active_on_entry.clone(),
            context=None,
            update_stats=None,
            reward=None,
            receipts=None,
            serviced=False,
        )
        self.mutation_revision += 1
        return stamp

    def _context(self, context: IntrinsicTransitionContext, stamp: CuriosityStepStamp, accepted: WorldAcceptedEpisode) -> dict[str, Any]:
        self._available()
        self._auth(accepted)
        _require(isinstance(context, IntrinsicTransitionContext) and isinstance(stamp, CuriosityStepStamp), "actual context/stamp required")
        pending = self._pending
        _require(pending is not None, "missing reservation")
        assert pending is not None
        _require(stamp.world_ids == accepted.world_ids and _same(stamp.eligible, context.active_on_entry), "stamp row/eligibility mismatch")
        for i, event in enumerate(stamp.event_ids):
            _require(
                event.curiosity_epoch == self._curiosity_epoch and event.world_episode_seq == accepted.world_episode_seqs[i],
                "stamp episode mismatch",
            )
            if not bool(stamp.eligible[i]):
                _require(event.eligible_seq <= self._cursor[event.world_id]["eligible_seq"], "inactive cursor is in the future")
        current = self._current(context, stamp)
        if self.scope == "shared":
            _require(current, "stamp reservation mismatch")
        elif not current:
            _require(bool(stamp.eligible.any()), "expired inactive reservation")
            for i, world in enumerate(accepted.world_ids):
                if bool(stamp.eligible[i]):
                    _require(
                        "reward" in self._cache[world] and self._cache[world]["reward"]["event_id"] == stamp.event_ids[i],
                        "expired local event",
                    )
        predecessor, successor, actions = context.predecessor, context.successor, context.actions
        _require(predecessor.shape == (len(self.world_ids), self.descriptor.observation_dim), "provider observation width mismatch")
        _require(
            predecessor.dtype == successor.dtype == torch.float32 and predecessor.device == self.device,
            "selected observation profile mismatch",
        )
        _require(bool(((actions >= 0) & (actions < self.descriptor.action_dim)).all()), "action bounds mismatch")
        content = dict(
            predecessor=predecessor, successor=successor, actions=actions, active=context.active_on_entry, vector_tick=context.vector_tick
        )
        if self.scope == "shared" and pending["context"] is not None:
            _require(_same(content, pending["context"]), "changed event content")
        if self.scope == "per_world" and not current:
            for i, world in enumerate(accepted.world_ids):
                if bool(stamp.eligible[i]):
                    _require(
                        _same(self._local_content(content, i), self._cache[world]["reward"]["content"]), "changed local event/provenance"
                    )
        return content

    def _current(self, context: IntrinsicTransitionContext, stamp: CuriosityStepStamp) -> bool:
        assert self._pending is not None
        return (
            stamp.event_ids == self._pending["stamp"].event_ids
            and _same(stamp.eligible, self._pending["active"])
            and context.vector_tick == self._pending["tick"]
        )

    def _replay(self, content: dict[str, Any], stamp: CuriosityStepStamp, phase: str) -> bool:
        indexes = stamp.eligible.nonzero().flatten().tolist()
        if self.scope != "per_world" or not indexes:
            return False
        for i in indexes:
            cache = self._cache[stamp.world_ids[i]]
            if phase not in cache or cache[phase]["event_id"] != stamp.event_ids[i]:
                return False
        for i in indexes:
            _require(
                _same(self._local_content(content, i), self._cache[stamp.world_ids[i]][phase]["content"]), "changed local event/provenance"
            )
        return True

    def _inactive_receipt(self, event: CuriosityEventId) -> WorldServiceReceipt:
        return WorldServiceReceipt(self.scope, event.world_id, (event,), False, None, 0, 0, 0, 0, 0, 0, 0.0)

    def _row_context(self, content: dict[str, Any], indexes: list[int]) -> IntrinsicTransitionContext:
        return IntrinsicTransitionContext(
            predecessor=content["predecessor"][indexes],
            actions=content["actions"][indexes],
            successor=content["successor"][indexes],
            active_on_entry=content["active"][indexes],
            vector_tick=content["vector_tick"],
        )

    def _local_content(self, content: dict[str, Any], index: int) -> dict[str, Any]:
        local = {}
        for key, value in content.items():
            if key == "vector_tick":
                local[key] = value
            else:
                local[key] = value[index].clone()
        return local

    @_serialized
    @_observation_boundary
    def reward(
        self, *, context: IntrinsicTransitionContext, stamp: CuriosityStepStamp, accepted: WorldAcceptedEpisode, update_stats: bool
    ) -> CuriosityReward:
        content = self._context(context, stamp, accepted)
        _require(type(update_stats) is bool, "update_stats must be bool")
        pending = self._pending
        assert pending is not None
        if self._replay(content, stamp, "reward"):
            raw = torch.zeros(len(stamp.world_ids), device=self.device)
            scales = torch.zeros_like(raw)
            for i, world in enumerate(stamp.world_ids):
                if bool(stamp.eligible[i]):
                    cached = self._cache[world]["reward"]
                    _require(cached["update_stats"] == update_stats, "changed reward mode")
                    raw[i], scales[i] = cached["raw"], cached["scale"]
            return CuriosityReward(raw, scales, stamp.eligible, stamp.event_ids, self.scope)
        _require(self._current(context, stamp), "expired reward event")
        if pending["reward"] is not None:
            _require(update_stats == pending["update_stats"], "changed reward mode")
            return cast(CuriosityReward, deepcopy(pending["reward"]))
        raw = torch.zeros(len(self.world_ids), device=self.device)
        scales = torch.zeros_like(raw)
        indexes = content["active"].nonzero().flatten().tolist()
        if self.scope == "per_world":
            groups = [[index] for index in indexes]
        else:
            if indexes:
                groups = [indexes]
            else:
                groups = []
        for group in groups:

            def compute(backend: Any) -> tuple[torch.Tensor, float]:
                if self.policy.strategy == "icm":
                    novelty = backend.compute_transition_novelty(self._row_context(content, group), update_stats=update_stats)
                else:
                    novelty = backend.compute_intrinsic_rewards(content["successor"][group], update_stats=update_stats)
                if self.policy.strategy == "none":
                    scale = 0.0
                elif self.policy.strategy == "adaptive_rnd":
                    scale = backend.get_intrinsic_weight()
                else:
                    scale = self.policy.initial_intrinsic_weight
                if (
                    novelty.shape != (len(group),)
                    or not bool(torch.isfinite(novelty).all())
                    or not bool(torch.isfinite(torch.tensor(scale)))
                ):
                    raise RuntimeError("provider returned invalid reward")
                return novelty, scale

            values, weight = self._call(accepted.world_ids[group[0]], compute)
            raw[group], scales[group] = values, weight
        self._publications += 1
        result = CuriosityReward(raw, scales, content["active"], stamp.event_ids, self.scope)
        pending.update(context=content, update_stats=update_stats, reward=result)
        for index in indexes:
            world = accepted.world_ids[index]
            self._cache[world]["reward"] = dict(
                event_id=stamp.event_ids[index],
                content=self._local_content(content, index),
                update_stats=update_stats,
                raw=raw[index].clone(),
                scale=scales[index].clone(),
            )
        self.mutation_revision += 1
        return deepcopy(result)

    @_serialized
    @_observation_boundary
    def admit_and_service(
        self, *, context: IntrinsicTransitionContext, stamp: CuriosityStepStamp, accepted: WorldAcceptedEpisode
    ) -> tuple[WorldServiceReceipt, ...]:
        content = self._context(context, stamp, accepted)
        pending = self._pending
        assert pending is not None
        if self._replay(content, stamp, "service"):
            cached_receipts = []
            for i, world in enumerate(stamp.world_ids):
                if bool(stamp.eligible[i]):
                    cached_receipts.append(self._cache[world]["service"]["receipt"])
                else:
                    cached_receipts.append(self._inactive_receipt(stamp.event_ids[i]))
            return tuple(cached_receipts)
        _require(self._current(context, stamp), "expired service event")
        _require(pending["reward"] is not None, "reward must precede service")
        if self.scope == "per_world":
            _require(self._replay(content, stamp, "reward") or not bool(stamp.eligible.any()), "reward source mismatch")
        if pending["serviced"]:
            return cast(tuple[WorldServiceReceipt, ...], pending["receipts"])
        indexes = content["active"].nonzero().flatten().tolist()
        if self.scope == "per_world":
            groups = [[i] for i in range(len(self.world_ids))]
        else:
            if indexes:
                groups = [indexes]
            else:
                groups = []
        receipts = []
        self._publications += 1
        for group in groups:
            world = accepted.world_ids[group[0]]
            active = bool(content["active"][group[0]])
            clock = None
            values: dict[str, Any] = dict(
                admitted_rows=0,
                consumed_rows=0,
                dropped_rows=0,
                pending_rows=0,
                optimizer_updates=0,
                mandatory_service_updates=0,
                last_loss=0.0,
            )
            if active and self.policy.strategy in ("rnd", "adaptive_rnd", "icm"):
                position = context.vector_tick
                if self.scope == "per_world":
                    position = self._cursor[world]["cumulative_service_position"] + 1
                clock = ServiceClock(self.policy.service_clock_unit, position)
                native_clock = clock
                if self.scope == "per_world" and self._initialization_origin is not None:
                    native_clock = ServiceClock(clock.unit, position + self._initialization_origin["inherited_baseline"]["admitted_rows"])

                def service(backend: Any) -> Any:
                    if self.policy.strategy == "icm":
                        payload = self._row_context(content, group)
                    else:
                        payload = content["predecessor"][group]
                    if self.scope == "per_world":
                        return backend.admit_and_service_at(payload, clock=native_clock)
                    if self.policy.strategy == "icm":
                        return backend.admit_and_service(payload)
                    return backend.admit_and_service(payload, vector_tick=context.vector_tick)

                receipt = self._call(world, service)
                if self.policy.strategy == "icm":
                    values = {key: getattr(receipt, key) for key in values}
                else:
                    values = {key: getattr(receipt, key) for key in values if key not in ("mandatory_service_updates", "last_loss")}
                    loss = receipt.last_loss
                    if loss is None:
                        loss = 0.0
                    values.update(mandatory_service_updates=receipt.overflow_optimizer_updates, last_loss=loss)
            receipt_world = None
            if self.scope == "per_world":
                receipt_world = world
            item = WorldServiceReceipt(self.scope, receipt_world, tuple(stamp.event_ids[i] for i in group), active, clock, **values)
            receipts.append(item)
            if active:
                for index in group:
                    local = accepted.world_ids[index]
                    self._cursor[local].update(eligible_seq=stamp.event_ids[index].eligible_seq, participated=True)
                    self._cursor[local]["cumulative_service_position"] += 1
                    self._cache[local]["service"] = dict(
                        event_id=stamp.event_ids[index], content=self._local_content(content, index), receipt=item
                    )
        pending.update(receipts=tuple(receipts), serviced=True)
        self.mutation_revision += 1
        return tuple(receipts)

    @_serialized
    @_observation_boundary
    def prepare_completion(
        self,
        *,
        accepted: WorldAcceptedEpisode,
        boundary_key: int,
        completion_content: Any,
        outcomes: tuple[LaneOutcome, ...],
        participated_world_ids: tuple[str, ...],
    ) -> PreparedBankCompletion:
        self._healthy()
        self._auth(accepted)
        _require(type(boundary_key) is int and boundary_key == accepted.batch_episode, "completion boundary mismatch")
        _require(type(outcomes) is tuple and all(isinstance(event, LaneOutcome) for event in outcomes), "actual lane outcomes required")
        participants = tuple(world for world in accepted.world_ids if self._cursor[world]["participated"])
        _require(bool(participants) and participated_world_ids == participants, "completion participation mismatch")
        _require(tuple(event.world_id for event in outcomes) == participants, "outcome order/membership mismatch")
        _require(self._pending is None or self._pending["serviced"], "unfinished phase at completion")
        for event in outcomes:
            index = accepted.world_ids.index(event.world_id)
            _require(
                event.world_episode_seq == accepted.world_episode_seqs[index]
                and event.batch_episode == accepted.batch_episode
                and event.outcome.agent_idx == index,
                "outcome accepted identity mismatch",
            )
        # Metadata-only size pass; admission precedes outcome cloning/candidates.
        outcome_bytes = sum(
            value.numel() * value.element_size()
            for event in outcomes
            for value in (event.outcome.final_observation, event.outcome.final_meters)
        )
        if self._prepared is not None:
            prepared = self._prepared
            _require(
                prepared.accepted is accepted
                and prepared.boundary_key == boundary_key
                and _same(self._completion_payload["completion_content"], completion_content)
                and len(outcomes) == len(self._completion_outcomes),
                "changed pending completion",
            )
            _require(
                all(_same_outcome(event, owned) for event, owned in zip(outcomes, self._completion_outcomes, strict=True)),
                "changed pending outcome",
            )
            return prepared
        _require(all(self._cursor[world]["disposition"] is None for world in self.world_ids), "episode already disposed")
        self._report(self._allocation("complete", len(participants), outcome_bytes))
        for event in outcomes:
            lane_outcome_state(event)
        canonical = tuple((frozen.payload.hex(), frozen.fingerprint) for frozen in (freeze_lane_outcome(event) for event in outcomes))
        _require(_same(canonical, completion_content), "completion content must contain exact full canonical payload and fingerprint")
        owned_outcomes = deepcopy(outcomes)
        values: dict[str, tuple[list[float], float]] = {}
        observed = False
        try:
            if self.policy.strategy == "adaptive_rnd":
                groups: list[tuple[str, tuple[LaneOutcome, ...]]]
                if self.scope == "per_world":
                    groups = [(event.world_id, (event,)) for event in outcomes]
                else:
                    groups = [(participants[0], outcomes)]
                for world, events in groups:

                    def candidate(backend: Any) -> Any:
                        offside = copy(backend)
                        offside.survival_history = list(backend.survival_history)
                        try:
                            for event in events:
                                offside.update_on_episode_end(event.outcome.survival_time)
                        except ValueError as error:
                            return (False, str(error))
                        return (True, (list(offside.survival_history), offside.current_intrinsic_weight))

                    observed = True
                    result = self._call(world, candidate)
                    if not result[0]:
                        raise _CandidateRefusalError(result[1])
                    values[world] = result[1]
        except BaseException:
            if observed:
                self.mutation_revision += 1
            raise
        disposition_rows = []
        for world in accepted.world_ids:
            disposition = "retired_nonparticipating"
            if world in participants:
                disposition = "completed"
            disposition_rows.append((world, disposition))
        dispositions = tuple(disposition_rows)
        payload = dict(
            accepted=accepted,
            boundary_key=boundary_key,
            completion_content=canonical,
            participated_world_ids=participants,
            dispositions=dispositions,
        )
        self._publications += 1
        receipt = self._issuer.issue(kind="prepared_dispositions", payload=payload)
        self.mutation_revision += 1
        prepared = PreparedBankCompletion(
            self, self.mutation_revision, accepted, boundary_key, canonical, participants, dispositions, deepcopy(values), receipt, False
        )
        self._prepared = prepared
        # Publication data is bank-owned, separate from the returned opaque token.
        self._completion_values, self._completion_payload = values, payload
        self._completion_outcomes = owned_outcomes
        return prepared

    @_serialized
    def commit_completion(self, *, prepared: PreparedBankCompletion) -> WorldOwnerReceipt:
        self._healthy()
        _require(isinstance(prepared, PreparedBankCompletion) and prepared.destination is self, "foreign completion token")
        self._auth(prepared.accepted)
        if self._committed is not None and self._committed[0] is prepared:
            return self._committed[1]
        _require(self._prepared is prepared and not prepared.used and prepared.revision == self.mutation_revision, "stale completion token")
        payload = self._completion_payload
        _require(
            prepared.boundary_key == payload["boundary_key"]
            and _same(prepared.completion_content, payload["completion_content"])
            and prepared.participated_world_ids == payload["participated_world_ids"]
            and prepared.dispositions == payload["dispositions"],
            "changed completion token",
        )
        try:
            for world, (history, weight) in self._completion_values.items():

                def publish(backend: Any) -> None:
                    backend.survival_history = history
                    backend.current_intrinsic_weight = weight

                self._call(world, publish)
            receipt = self._issuer.issue(kind="dispositions", payload=payload)
            for world, disposition in prepared.dispositions:
                self._cursor[world]["disposition"] = disposition
                if world in prepared.participated_world_ids:
                    index = prepared.participated_world_ids.index(world)
                else:
                    index = None
                local_completion = None
                if index is not None:
                    local_completion = prepared.completion_content[index]
                self._cache[world]["completion"] = dict(
                    episode=self._cursor[world]["accepted_episode_seq"],
                    disposition=disposition,
                    content=local_completion,
                )
        except BaseException:
            self._failed = True
            raise
        prepared.used = True
        self._prepared = None
        self._committed = (prepared, receipt)
        self._completion_values = {}
        self.mutation_revision += 1
        return receipt

    @_serialized
    def prepare_empty_episode_evidence(self, *, accepted: WorldAcceptedEpisode) -> WorldOwnerReceipt:
        self._available()
        self._auth(accepted)
        _require(
            not any(
                cursor["participated"] or cursor["eligible_seq"] or cursor["disposition"] is not None for cursor in self._cursor.values()
            ),
            "episode is not empty",
        )
        _require(self._pending is None or self._pending["serviced"], "pending empty phase")
        return self._issuer.issue(kind="empty_episode", payload=dict(accepted=accepted, participated_world_ids=(), events=()))

    @_serialized
    def quarantine_episode(self, *, accepted: WorldAcceptedEpisode, reason: str) -> None:
        self._auth(accepted)
        _require(type(reason) is str and reason in ("empty_participation", "runtime_failure"), "unsupported quarantine reason")
        if self._quarantine is not None:
            _require(self._quarantine[0] is accepted and self._quarantine[1] == reason, "changed quarantine notification")
            return
        self._quarantine = (accepted, reason)
        self._failed = True
        self.mutation_revision += 1

    @_serialized
    def snapshot_world(self, *, world_id: str) -> dict[str, Any]:
        from townlet.exploration import curiosity_checkpoint as checkpoint

        self._available()
        _require(type(world_id) is str and world_id in self._cursor, "unknown exact world ID")
        if self._initialization_origin is not None:
            self._report_transport(self._initialization_origin, "snapshot", None)
        try:
            if self.scope == "per_world":
                backend = self._owners[world_id].snapshot(lineage=self._lineage)
            else:
                backend = self._shared.snapshot(lineage=self._lineage)["backend"]
        except BaseException:
            self._failed = True
            raise
        finally:
            self.mutation_revision += 1
        accepted = self._accepted
        if accepted is None:
            identity = None
        else:
            identity = dict(
                batch_episode=accepted.batch_episode,
                world_ids=list(accepted.world_ids),
                world_episode_seqs=list(accepted.world_episode_seqs),
            )
        pending = None
        if self._pending is not None and not self._pending["serviced"]:
            assert accepted is not None
            index = accepted.world_ids.index(world_id)
            if bool(self._pending["active"][index]):
                local_context = None
                if self._pending["context"] is not None:
                    local_context = self._local_content(self._pending["context"], index)
                pending = dict(
                    event_id=self._pending["stamp"].event_ids[index],
                    vector_tick=self._pending["tick"],
                    context=local_context,
                )
        return dict(
            schema="curiosity-bank-world-v2",
            scope=self.scope,
            world_id=world_id,
            policy_identity=self.policy.policy_identity,
            descriptor=self.descriptor.to_dict(),
            backend=backend,
            curiosity_epoch=self._curiosity_epoch,
            initialization_origin=checkpoint.owned(self._initialization_origin),
            future_service_counters=(
                checkpoint.future_counters(backend["backend"], policy=self.policy, origin=self._initialization_origin)
                if self.scope == "per_world"
                else None
            ),
            accepted_identity=identity,
            cursor=deepcopy(self._cursor[world_id]),
            phase_cache=deepcopy(self._cache[world_id]),
            pending_step=pending,
            bank_phase=self._checkpoint_phase(),
            historical_identity=self._historical_identity(),
        )

    def _checkpoint_phase(self) -> str:
        if self._private_initialized:
            return "private_initialized"
        if self._history is not None or self._committed is not None:
            return "completed_boundary"
        if self._accepted is not None:
            return "live_episode"
        return "initial"

    def _historical_identity(self) -> dict[str, Any] | None:
        from townlet.exploration import curiosity_checkpoint as checkpoint

        if self._history is not None:
            return cast(dict[str, Any], deepcopy(self._history["original_accepted_identity"]))
        if self._committed is not None:
            return checkpoint.accepted_identity(self._committed[0].accepted)
        return None

    @_serialized
    @_observation_boundary
    def checkpoint_state(self) -> dict[str, Any]:
        """Owned current transport; historical completion never transports authority."""
        self._available()
        return self._checkpoint_payload()

    @_serialized
    @_observation_boundary
    def failure_diagnostic_state(self) -> dict[str, Any]:
        """Full local-failure observation under unchanged child capture contracts."""
        state = self._runtime_failure_payload()
        state["schema"] = "curiosity-bank-failure-diagnostic-v1"
        state["failure_reason"] = "runtime_failure"
        return state

    @_serialized
    @_observation_boundary
    def diagnostic_state(self) -> dict[str, Any]:
        """Capture available or authenticated local-failure state without resume authority."""
        reason: str | None
        if self._failed:
            state = self._runtime_failure_payload()
            reason = "runtime_failure"
        else:
            self._available()
            state = self._checkpoint_payload()
            reason = None
        state["schema"] = "curiosity-bank-diagnostic-v1"
        state["failure_reason"] = reason
        return state

    def _runtime_failure_payload(self) -> dict[str, Any]:
        if self._completion_uncertain:
            raise RuntimeError("curiosity bank completion uncertain")
        quarantine = self._quarantine
        _require(self._failed and quarantine is not None, "runtime failure quarantine required")
        assert quarantine is not None
        _require(quarantine[1] == "runtime_failure", "runtime failure quarantine required")
        self._auth(quarantine[0])
        _require(self._prepared is None, "completion transaction pending")
        return self._checkpoint_payload()

    def _checkpoint_payload(self) -> dict[str, Any]:
        from townlet.exploration import curiosity_checkpoint as checkpoint

        if self._initialization_origin is not None:
            self._report_transport(self._initialization_origin, "checkpoint", None)
        phase = self._checkpoint_phase()
        worlds = []
        shared = None
        try:
            if self.scope == "shared":
                self._observations += 1
                shared = self._shared.call(
                    lambda provider: dict(
                        native=checkpoint.owned(provider.checkpoint_state()),
                        gradients=checkpoint.capture_gradients(provider, self.policy.strategy),
                    ),
                    lineage=self._lineage,
                )
            for world in self.world_ids:
                backend = gradients = None
                if self.scope == "per_world":
                    self._observations += 1
                    backend, gradients = self._owners[world].snapshot_with_capture(
                        lambda provider: checkpoint.capture_gradients(provider, self.policy.strategy), lineage=self._lineage
                    )
                worlds.append(
                    dict(
                        world_id=world,
                        backend=backend,
                        gradients=gradients,
                        cursor=deepcopy(self._cursor[world]),
                        phase_cache=checkpoint.encode_cache(self._cache[world]),
                    )
                )
            completion = deepcopy(self._history)
            if self._committed is not None:
                payload = self._completion_payload
                completion = dict(
                    status="committed",
                    original_accepted_identity=checkpoint.accepted_identity(self._committed[0].accepted),
                    boundary_key=payload["boundary_key"],
                    completion_content=deepcopy(payload["completion_content"]),
                    participated_world_ids=payload["participated_world_ids"],
                    dispositions=payload["dispositions"],
                    outcomes=tuple(lane_outcome_state(event) for event in self._completion_outcomes),
                )
            step = deepcopy(self._historical_step)
            if self._pending is not None:
                assert self._accepted is not None
                step = checkpoint.encode_step(self._pending, checkpoint.accepted_identity(self._accepted))
            dispatch = None
            if phase == "live_episode":
                assert self._accepted is not None
                dispatch = checkpoint.accepted_identity(self._accepted)
            return dict(
                schema="curiosity-bank-state-v2",
                policy=self.policy.to_dict(),
                policy_identity=self.policy.policy_identity,
                descriptor=self.descriptor.to_dict(),
                source_device=str(self.device),
                curiosity_epoch=self._curiosity_epoch,
                initialization_origin=checkpoint.owned(self._initialization_origin),
                bank_phase=phase,
                dispatch_identity=dispatch,
                worlds=worlds,
                shared_backend=shared,
                step=step,
                completion=completion,
            )
        finally:
            self.mutation_revision += 1

    def _report_transport(self, state: Any, operation: str, parent_restore: Any) -> None:
        from townlet.exploration import curiosity_checkpoint as checkpoint

        size = checkpoint.tensor_bytes(state)
        reserve = self._allocation(operation, len(self.world_ids), 0)
        callback_bytes = 0
        if parent_restore is not None:
            callback_bytes = 2 * size
        components = reserve.components + (
            ("owned_input_candidate_workspace", 5 * size),
            ("two_retained_parent_callback_views", callback_bytes),
        )
        if operation in ("initialize_private", "snapshot", "checkpoint") or state["initialization_origin"] is not None:
            components += (("source_archive_and_disposable_native_validator", 3 * size),)
        self._report(
            replace(
                reserve,
                known_tensor_bytes=sum(value for _, value in components),
                components=components,
                assumptions=reserve.assumptions
                + (
                    "old resident plus new owners, gradients/Adam/tails, owned transport and sequential validation workspace",
                    "five input tensor inventories reserve transport, gradients, RNG, caches, outcomes and transient copies",
                    "both independently owned parent callback views may be retained; earlier preparations/external copies excluded",
                ),
                unknown_components=reserve.unknown_components + ("parent callback copies and retention from earlier preparations",),
            )
        )

    def _correlate_parent(self, saved: dict[str, Any], parent: Any, validate: Any, view: Any) -> None:
        from townlet.exploration import curiosity_checkpoint as checkpoint

        if parent is not None:
            checkpoint.match_parent(saved, parent=parent, descriptor=self.descriptor)
            _require(checkpoint.same(saved, view), "retained parent callback changed curiosity state")
            _require(validate(prepared=parent, curiosity_state=view) is None, "parent validator return")
            _require(checkpoint.same(saved, view), "parent callback changed curiosity state")

    def _preparation_identity(self) -> tuple[Any, ...]:
        return (
            self.mutation_revision,
            self._checkpoint_phase(),
            id(self._pending),
            id(self._prepared),
            id(self._accepted),
            id(self._activation),
            id(self._initialization_origin),
            self._failed,
            id(self._quarantine),
            self.policy.to_dict(),
            self.descriptor.to_dict(),
            self.device,
            self.scope,
            self.world_ids,
        )

    def _replacement_cohort(self, archived: bool, *, disposable: list[Any] | None) -> _RestoreCohort:
        """Registration/constructor work occurs only after examination releases custody."""
        inputs: list[WorldRNGState] = []
        owners: dict[str, OwnedWorldBackend] = {}
        shared = validation_rng = None
        if archived:
            validation_rng = WorldRNGState.create(
                descriptor=self.descriptor, world_id=sorted(self.world_ids)[0], cuda_devices=self._devices
            )
            if disposable is not None:
                disposable.append(validation_rng)
        if self.scope == "per_world":
            for world in sorted(self.world_ids):
                rng = WorldRNGState.create(descriptor=self.descriptor, world_id=world, cuda_devices=self._devices)
                inputs.append(rng)
                if disposable is not None:
                    disposable.append(rng)
                owners[world] = OwnedWorldBackend.construct(rng=rng, factory=partial(self._factory, world))
                if disposable is not None:
                    disposable.append(owners[world])
        else:
            shared = SharedWorldBackend.reserve(cuda_devices=self._devices)
            if disposable is not None:
                disposable.append(shared)
        return _RestoreCohort(self, inputs, owners, shared, validation_rng)

    @contextmanager
    def _disposable_cohort(self, archived: bool) -> Iterator[_RestoreCohort]:
        registrations: list[Any] = []

        def retire() -> None:
            # Construction retains input RNG registration and adopts its fork
            # into a separately registered backend owner. Retire both identities.
            participants = {item.rng_participant for item in registrations}
            for participant in participants:
                process_rng_domain().unregister(participant=participant)

        try:
            yield self._replacement_cohort(archived, disposable=registrations)
        except BaseException as failure:
            try:
                retire()
            except BaseException as cleanup:
                raise BaseExceptionGroup("restore validation failed and disposable retirement failed", [failure, cleanup]) from None
            raise
        else:
            retire()

    def _configured_factory(self, world: str | None, native: Any, rng: WorldRNGState | None) -> Any:
        provider = self._factory(world, rng)
        if self.policy.strategy in ("rnd", "adaptive_rnd", "icm"):
            provider = provider.with_restore_configuration(native)
        return provider

    def _attach_private(self, owner: OwnedWorldBackend, record: dict[str, Any]) -> None:
        from townlet.exploration import curiosity_checkpoint as checkpoint

        envelope, gradients = record["backend"], record["gradients"]
        native = owner.prepare_restore(
            envelope,
            factory=partial(self._configured_factory, record["world_id"], envelope["backend"]),
            validate_backend=partial(checkpoint.validate_native, policy=self.policy, descriptor=self.descriptor),
            lineage=self._lineage,
        )
        owner.install(native, lineage=self._lineage)
        owner.call(lambda provider, sources: checkpoint.attach_gradients(provider, gradients, self.policy.strategy), lineage=self._lineage)
        restored, captured = owner.snapshot_with_capture(
            lambda provider: checkpoint.capture_gradients(provider, self.policy.strategy), lineage=self._lineage
        )
        _require(checkpoint.same(restored, envelope), "restoration changed target native/RNG payload")
        _require(checkpoint.same(captured, gradients), "restoration changed final named gradients")

    def _populate_restore_cohort(self, saved: dict[str, Any], cohort: _RestoreCohort, mode: str, lineage: RNGOperation) -> None:
        from townlet.exploration import curiosity_checkpoint as checkpoint

        if saved["initialization_origin"] is not None:
            assert cohort.validation_rng is not None
            checkpoint.validate_archived_native(
                saved["initialization_origin"]["source_checkpoint"],
                descriptor=self.descriptor,
                device=self.device,
                validation_rng=cohort.validation_rng,
                lineage=lineage,
            )
        records = {item["world_id"]: item for item in saved["worlds"]}
        if self.scope == "per_world":
            for world, owner in cohort.owners.items():
                if saved["initialization_origin"] is not None and mode in ("initial", "private_initialized"):
                    owner.call(
                        lambda provider, sources: checkpoint.validate_boundary_template(
                            provider, records[world], origin=saved["initialization_origin"], policy=self.policy
                        ),
                        lineage=lineage,
                    )
                self._attach_private(owner, records[world])
        else:
            shared, payload = cohort.shared, saved["shared_backend"]
            assert shared is not None
            with shared.bootstrap(lineage=lineage) as lease:
                native = shared.prepare_restore(
                    dict(schema="shared-world-backend-v1", healthy=True, backend=payload["native"]),
                    factory=partial(self._configured_factory, None, payload["native"], None),
                    validate_backend=partial(checkpoint.validate_native, policy=self.policy, descriptor=self.descriptor),
                    lineage=lease,
                )
                shared.install(native, lineage=lease)
                shared.call(
                    lambda provider: checkpoint.attach_gradients(provider, payload["gradients"], self.policy.strategy), lineage=lease
                )
                captured = shared.call(
                    lambda provider: dict(
                        native=provider.checkpoint_state(), gradients=checkpoint.capture_gradients(provider, self.policy.strategy)
                    ),
                    lineage=lease,
                )
                _require(checkpoint.same(captured, payload), "shared restoration changed native/gradients")

    @_preparation
    def validate_restore_data(self, *, state: Any, mode: str) -> None:
        """Reconstruct disposable native owners; grant no installation authority."""
        from townlet.exploration import curiosity_checkpoint as checkpoint

        with self._admission("prepare"):
            _require(self._prepared is None, "completion transaction pending")
            identity = self._preparation_identity()
            checkpoint.preflight(state, policy=self.policy, descriptor=self.descriptor, device=self.device, mode=mode)
            self._report_transport(state, "restore", None)
            saved = checkpoint.owned(state)
            checkpoint.validate_origin(saved, policy=self.policy, descriptor=self.descriptor, device=self.device)
            checkpoint.validate_records(saved, policy=self.policy, descriptor=self.descriptor, device=self.device)
        with self._disposable_cohort(saved["initialization_origin"] is not None) as cohort:
            with self._admission("prepare") as lineage:
                _require(self._preparation_identity() == identity, "destination changed during idle registration")
                self._populate_restore_cohort(saved, cohort, mode, lineage)
                _require(self._preparation_identity() == identity, "destination changed during data validation")

    def _seal_restore(
        self, saved: dict[str, Any], cohort: _RestoreCohort, accepted: Any, identity: tuple[Any, ...], correlate: Callable[[], None]
    ) -> Any:
        token, runtime = self._restore_publication(saved, cohort.owners, cohort.shared, accepted, identity[0])
        correlate()
        _require(self._preparation_identity() == identity, "destination changed during restore preparation")
        # Allocate every registry/retention record before issuing final currency.
        assert self._lineage is not None
        observation = _new_installation_outcome(self, token, runtime=False)
        record = [identity, runtime, accepted, None, correlate, cohort, observation]
        self._restore_tokens[token] = record
        try:
            record[3] = process_rng_domain().current_token(participant=self._rng_participant, operation=self._lineage)
        except BaseException:
            del self._restore_tokens[token]
            raise
        return token

    @_preparation
    def prepare_private_initialization(self, *, state: Any, initialization: str, parent_restore: Any, validate_parent_restore: Any) -> Any:
        """Prepare an explicit owned private origin; archived shared work stays inactive."""
        from townlet.exploration import curiosity_checkpoint as checkpoint

        with self._admission("prepare"):
            if isinstance(state, Mapping):
                _require(
                    state.get("schema") not in ("curiosity-bank-failure-diagnostic-v1", "curiosity-bank-diagnostic-v1"),
                    "diagnostics are not restore transport",
                )
            self._available()
            _require(
                type(initialization) is str and initialization in ("fresh_private", "clone_learned_archive_pending"),
                "explicit initialization required",
            )
            _require(
                self.scope == "per_world"
                and self._checkpoint_phase() == "initial"
                and self._initialization_origin is None
                and self._pending is None
                and self._activation is None
                and all(not cache for cache in self._cache.values())
                and all(not any(cursor.values()) for cursor in self._cursor.values()),
                "initialization requires an untouched INITIAL private bank",
            )
            identity = self._preparation_identity()
            source_policy, source_descriptor = checkpoint.conversion_source(
                state, policy=self.policy, descriptor=self.descriptor, device=self.device
            )
            checkpoint.check_mode(mode=state["bank_phase"], accepted=None, parent=parent_restore, validate=validate_parent_restore)
            self._report_transport(state, "initialize_private", parent_restore)
            source = checkpoint.owned(state)
            parent_view = None
            if parent_restore is not None:
                parent_view = checkpoint.owned(source)
            self._correlate_parent(source, parent_restore, validate_parent_restore, parent_view)
            checkpoint.validate_records(source, policy=source_policy, descriptor=source_descriptor, device=self.device)
        cohort = self._replacement_cohort(True, disposable=None)
        with self._admission("prepare") as lineage:
            _require(self._preparation_identity() == identity, "destination changed during idle registration")
            correlate = partial(self._correlate_parent, source, parent_restore, validate_parent_restore, parent_view)
            correlate()
            assert cohort.validation_rng is not None
            checkpoint.validate_archived_native(
                source, descriptor=self.descriptor, device=self.device, validation_rng=cohort.validation_rng, lineage=lineage
            )
            origin = checkpoint.make_origin(source, initialization=initialization, policy=self.policy, descriptor=self.descriptor)
            records = []
            for world, owner in cohort.owners.items():
                envelope, gradients = owner.snapshot_with_capture(
                    lambda provider: checkpoint.capture_gradients(provider, self.policy.strategy), lineage=lineage
                )
                if initialization == "clone_learned_archive_pending":
                    envelope["backend"] = checkpoint.clone_native(
                        source["shared_backend"]["native"], policy=self.policy, baseline=origin["inherited_baseline"]
                    )
                    gradients = source["shared_backend"]["gradients"]
                record = dict(
                    world_id=world,
                    backend=envelope,
                    gradients=checkpoint.owned(gradients),
                    phase_cache={},
                    cursor=dict(
                        accepted_episode_seq=origin["episode_baseline"][world],
                        eligible_seq=0,
                        cumulative_service_position=0,
                        participated=False,
                        disposition=None,
                    ),
                )
                self._attach_private(owner, record)
                records.append(record)
            by_world = {record["world_id"]: record for record in records}
            phase = "private_initialized"
            if source["bank_phase"] == "initial":
                phase = "initial"
            saved = dict(
                schema="curiosity-bank-state-v2",
                policy=self.policy.to_dict(),
                policy_identity=self.policy.policy_identity,
                descriptor=self.descriptor.to_dict(),
                source_device=str(self.device),
                curiosity_epoch=source["curiosity_epoch"] + 1,
                initialization_origin=origin,
                bank_phase=phase,
                dispatch_identity=None,
                worlds=[by_world[world] for world in self.world_ids],
                shared_backend=None,
                step=None,
                completion=None,
            )
            checkpoint.preflight(saved, policy=self.policy, descriptor=self.descriptor, device=self.device, mode=saved["bank_phase"])
            checkpoint.validate_origin(saved, policy=self.policy, descriptor=self.descriptor, device=self.device)
            checkpoint.validate_records(saved, policy=self.policy, descriptor=self.descriptor, device=self.device)
            return self._seal_restore(saved, cohort, None, identity, correlate)

    @_preparation
    def prepare_restore(
        self,
        *,
        state: Any,
        mode: str,
        accepted: WorldAcceptedEpisode | None,
        parent_restore: Any,
        validate_parent_restore: Any,
    ) -> Any:
        """Prepare exclusively from authenticated saved data, including local quarantine recovery."""
        from townlet.exploration import curiosity_checkpoint as checkpoint

        with self._admission("prepare"):
            if isinstance(state, Mapping):
                _require(
                    state.get("schema") not in ("curiosity-bank-failure-diagnostic-v1", "curiosity-bank-diagnostic-v1"),
                    "diagnostics are not restore transport",
                )
            _require(self._prepared is None, "completion transaction pending")
            identity = self._preparation_identity()
            checkpoint.preflight(state, policy=self.policy, descriptor=self.descriptor, device=self.device, mode=mode)
            checkpoint.check_mode(mode=mode, accepted=accepted, parent=parent_restore, validate=validate_parent_restore)
            self._report_transport(state, "restore", parent_restore)
            saved = checkpoint.owned(state)
            checkpoint.validate_origin(saved, policy=self.policy, descriptor=self.descriptor, device=self.device)
            history = saved
            if mode == "private_initialized":
                history = saved["initialization_origin"]["source_checkpoint"]
            parent_view = None
            if parent_restore is not None:
                parent_view = checkpoint.owned(history)

            def correlate() -> None:
                if mode == "live_episode":
                    assert accepted is not None
                    self._validate(accepted=accepted)
                    checkpoint.match_live(saved, accepted=accepted, descriptor=self.descriptor)
                elif parent_restore is not None:
                    self._correlate_parent(history, parent_restore, validate_parent_restore, parent_view)

            correlate()
            checkpoint.validate_records(saved, policy=self.policy, descriptor=self.descriptor, device=self.device)
        cohort = self._replacement_cohort(saved["initialization_origin"] is not None, disposable=None)
        with self._admission("prepare") as lineage:
            _require(self._preparation_identity() == identity, "destination changed during idle registration")
            correlate()
            self._populate_restore_cohort(saved, cohort, mode, lineage)
            return self._seal_restore(saved, cohort, accepted, identity, correlate)

    def _restore_publication(
        self, saved: dict[str, Any], owners: dict[str, OwnedWorldBackend], shared: Any, accepted: Any, revision: int
    ) -> tuple[Any, dict[str, Any]]:
        from townlet.exploration import curiosity_checkpoint as checkpoint

        runtime_values = checkpoint.runtime_data(saved, descriptor=self.descriptor, device=self.device)
        activation = None
        if saved["bank_phase"] == "live_episode":
            activation = self._issuer.issue(kind="activation", payload={"accepted": accepted})
        token = checkpoint.PreparedCuriosityRestore()
        runtime = dict(self.__dict__)
        runtime.update(
            _owners=owners,
            _shared=shared,
            _cursor=runtime_values["cursor"],
            _cache=runtime_values["cache"],
            _pending=runtime_values["pending"],
            _history=runtime_values["history"],
            _historical_step=runtime_values["historical_step"],
            _accepted=accepted,
            _activation=activation,
            _prepared=None,
            _committed=None,
            _failed=False,
            _quarantine=None,
            _completion_payload={},
            _completion_outcomes=(),
            _completion_values={},
            _restore_tokens={},
            _initialization_origin=checkpoint.owned(saved["initialization_origin"]),
            _curiosity_epoch=saved["curiosity_epoch"],
            _private_initialized=saved["bank_phase"] == "private_initialized",
            mutation_revision=revision + 1,
            _publications=self._publications + 1,
        )
        return token, runtime

    @_serialized
    def install_restore(self, *, prepared: Any) -> None:
        from townlet.exploration.curiosity_checkpoint import PreparedCuriosityRestore

        _require(type(prepared) is PreparedCuriosityRestore and prepared in self._restore_tokens, "foreign or consumed restore token")
        identity, runtime, accepted, currency, correlate, cohort, observation = self._restore_tokens.pop(prepared)
        active = self._installation_active
        if active is not None:
            active.handle_consumed = True
            active.refresh()
        _require(identity == self._preparation_identity() and self._prepared is None, "stale restore token")
        if accepted is not None:
            self._validate(accepted=accepted)
        correlate()
        _require(identity == self._preparation_identity(), "destination changed during final authentication")
        assert self._lineage is not None
        process_rng_domain().validate_current(token=currency, operation=self._lineage)
        if active is not None:
            active.bank_publication = 2
            active.refresh()
        try:
            self.__dict__ = runtime
        except BaseException:
            self._failed = True
            raise
        if active is not None:
            active.bank_publication = 1
            active.refresh()
