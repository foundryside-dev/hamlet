"""Current completion-driven curriculum state, atomic handoffs and stage policy."""

import math
import os
import re
import threading
import weakref
from abc import abstractmethod
from collections.abc import Sequence
from copy import deepcopy
from typing import Any

import torch
from pydantic import BaseModel

from townlet.curriculum.base import CurriculumManager, PreparedCurriculumOutcomes, PreparedNativeCurriculum
from townlet.training.episode import (
    LaneOutcome,
    freeze_lane_outcome,
    lane_outcome_from_state,
    lane_outcome_state,
)
from townlet.training.state import BatchedAgentState, CurriculumDecision


class StageConfig(BaseModel):
    """Authored stage labels and independently specified depletion values."""

    stage: int
    active_meters: list[str]
    depletion_multiplier: float
    reward_mode: str
    description: str


STAGE_CONFIGS = [
    StageConfig(
        stage=1,
        active_meters=["energy", "hygiene"],
        depletion_multiplier=0.2,
        reward_mode="shaped",
        description="Stage 1: Basic needs (energy, hygiene) at 20% depletion",
    ),
    StageConfig(
        stage=2,
        active_meters=["energy", "hygiene", "satiation"],
        depletion_multiplier=0.5,
        reward_mode="shaped",
        description="Stage 2: Add hunger at 50% depletion",
    ),
    StageConfig(
        stage=3,
        active_meters=["energy", "hygiene", "satiation", "money"],
        depletion_multiplier=0.8,
        reward_mode="shaped",
        description="Stage 3: Add money management at 80% depletion",
    ),
    StageConfig(
        stage=4,
        active_meters=["energy", "hygiene", "satiation", "money", "mood", "social"],
        depletion_multiplier=1.0,
        reward_mode="shaped",
        description="Stage 4: All meters at full depletion",
    ),
    StageConfig(
        stage=5,
        active_meters=["energy", "hygiene", "satiation", "money", "mood", "social"],
        depletion_multiplier=1.0,
        reward_mode="sparse",
        description="Stage 5: SPARSE REWARDS - Graduation!",
    ),
]


def finite_number(value: Any) -> bool:
    """Policy/checkpoint numbers exclude booleans and nonfinite values."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def nonnegative_integer(value: Any) -> bool:
    """Curriculum clocks are exact integer counts."""
    return type(value) is int and value >= 0


class CompletionCurriculum(CurriculumManager):
    """Shared current protocol for fixed and adaptive completion consumers.

    Effects and their identity receipts live in one owned state object. Preparing
    is pure; installing that object is the single learning-state mutation point.
    Telemetry is prepared alongside it and can be drained independently.
    """

    def __init__(self, strategy: str, config: dict[str, Any]):
        self._strategy = strategy
        self._config = deepcopy(config)
        self._state: dict[str, Any] = {}
        self._owner_token = object()
        self.num_agents = 0
        self.transition_events: list[dict[str, Any]] = []
        self._native_states: weakref.WeakKeyDictionary[PreparedNativeCurriculum, dict[str, Any]] = weakref.WeakKeyDictionary()
        self._native_participant: Any = None

    @abstractmethod
    def _initial_lane(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def _advance_lane(self, lane: dict[str, Any], event: LaneOutcome, previous_fraction: float) -> dict[str, Any] | None:
        raise NotImplementedError

    def initialize_population(self, num_agents: int) -> None:
        """Start a new population and invalidate every prior in-process receipt."""
        if type(num_agents) is not int or num_agents <= 0:
            raise ValueError("num_agents must be a positive integer")
        self.num_agents = num_agents
        self._state = {
            "version": 2,
            "strategy": self._strategy,
            "completion": {
                "config": deepcopy(self._config),
                "generation": 0,
                "lanes": [self._initial_lane() for _ in range(num_agents)],
                "events": [],
                "metrics": [None] * num_agents,
            },
        }
        self._owner_token = object()
        self.transition_events = []

    def _body(self) -> dict[str, Any]:
        if not self.num_agents:
            raise RuntimeError("Initialize the population first")
        body: dict[str, Any] = self._state["completion"]
        return body

    def prepare_episode_outcomes(self, outcomes: Sequence[LaneOutcome]) -> PreparedCurriculumOutcomes:
        """Freeze the complete batch and refuse conflicting retries without effects."""
        body = self._body()
        if not isinstance(outcomes, Sequence):
            raise ValueError("Completion outcomes must be a sequence")
        frozen = tuple(freeze_lane_outcome(event) for event in outcomes)
        known = {row["identity"]: row["fingerprint"] for row in body["events"]}
        latest = {index: lane_outcome_from_state(metric["event"]) for index, metric in enumerate(body["metrics"]) if metric is not None}
        for reading in frozen:
            event = reading.to_outcome()
            identity = (event.batch_episode, event.outcome.agent_idx)
            if not 0 <= event.outcome.agent_idx < self.num_agents:
                raise ValueError("Completion lane outside initialized population")
            if identity in known and known[identity] != reading.fingerprint:
                raise ValueError("Completion identity reused with changed content")
            if identity not in known:
                previous = latest.get(event.outcome.agent_idx)
                if previous is not None and (
                    event.world_id != previous.world_id
                    or event.world_episode_seq <= previous.world_episode_seq
                    or event.batch_episode <= previous.batch_episode
                ):
                    raise ValueError("New completion does not follow this lane's world cursor")
                latest[event.outcome.agent_idx] = event
            known[identity] = reading.fingerprint
        return PreparedCurriculumOutcomes(owner_token=self._owner_token, generation=body["generation"], outcomes=frozen)

    def commit_prepared_episode_outcomes(self, prepared: PreparedCurriculumOutcomes) -> None:
        """Install one candidate state; a completely applied equal retry is a no-op."""
        body = self._body()
        if not isinstance(prepared, PreparedCurriculumOutcomes) or prepared.owner_token is not self._owner_token:
            raise ValueError("Prepared outcomes belong to a different owner")
        if not nonnegative_integer(prepared.generation) or not isinstance(prepared.outcomes, tuple):
            raise ValueError("Invalid prepared generation/content")
        if prepared.generation > body["generation"]:
            raise ValueError("Prepared outcomes claim a future generation")
        # Revalidate even a manually forged/replaced dataclass before trusting it.
        try:
            events = tuple(reading.to_outcome() for reading in prepared.outcomes)
        except AttributeError as error:
            raise ValueError("Invalid prepared outcome") from error
        verified = self.prepare_episode_outcomes(events)
        if verified.outcomes != prepared.outcomes:
            raise ValueError("Prepared content is not canonical")
        known = {row["identity"]: row["fingerprint"] for row in body["events"]}
        if all(
            known.get((event.batch_episode, event.outcome.agent_idx)) == reading.fingerprint
            for event, reading in zip(events, prepared.outcomes, strict=True)
        ):
            return
        if prepared.generation != body["generation"]:
            raise ValueError("Prepared outcomes have a stale generation")
        candidate = deepcopy(self._state)
        next_body = candidate["completion"]
        transitions = deepcopy(self.transition_events)
        for event, reading in zip(events, prepared.outcomes, strict=True):
            identity = (event.batch_episode, event.outcome.agent_idx)
            if identity in known:
                continue
            index = event.outcome.agent_idx
            prior = next_body["metrics"][index]
            previous_fraction = 0.0
            if prior is not None:
                last = lane_outcome_from_state(prior["event"])
                if (
                    event.world_id != last.world_id
                    or event.world_episode_seq <= last.world_episode_seq
                    or event.batch_episode <= last.batch_episode
                ):
                    raise ValueError("New completion does not follow this lane's world cursor")
                previous_fraction = last.outcome.survival_time / last.planned_horizon
            transition = self._advance_lane(next_body["lanes"][index], event, previous_fraction)
            if transition is not None:
                transitions.append(transition)
            next_body["metrics"][index] = {"event": lane_outcome_state(event), "previous_fraction": previous_fraction}
            next_body["events"].append({"identity": identity, "fingerprint": reading.fingerprint})
            known[identity] = reading.fingerprint
        next_body["generation"] += 1
        self._state, self.transition_events = candidate, transitions

    def checkpoint_state(self) -> dict[str, Any]:
        """Read a fully independent current-native snapshot."""
        self._body()
        return deepcopy(self._state)

    def validate_checkpoint_state(self, state: dict[str, Any]) -> None:
        """Reject obsolete, malformed or contradictory state before installation."""
        self._body()
        if not isinstance(state, dict) or set(state) != {"version", "strategy", "completion"}:
            raise ValueError("Expected exact current curriculum schema")
        if type(state["version"]) is not int or state["version"] != 2 or state["strategy"] != self._strategy:
            raise ValueError("Current curriculum version/strategy mismatch")
        body = state["completion"]
        if not isinstance(body, dict) or set(body) != {"config", "generation", "lanes", "events", "metrics"}:
            raise ValueError("Invalid current completion schema")
        config = body["config"]
        if (
            not isinstance(config, dict)
            or set(config) != set(self._config)
            or any(type(config[key]) is not type(value) or config[key] != value for key, value in self._config.items())
        ):
            raise ValueError("Curriculum configuration mismatch")
        if not nonnegative_integer(body["generation"]):
            raise ValueError("Invalid completion generation")
        lanes, metrics, events = body["lanes"], body["metrics"], body["events"]
        if not isinstance(lanes, list) or len(lanes) != self.num_agents or not isinstance(metrics, list) or len(metrics) != self.num_agents:
            raise ValueError("Checkpoint population mismatch")
        if not isinstance(events, list):
            raise ValueError("Invalid completion identity history")
        known: dict[tuple[int, int], str] = {}
        latest: dict[int, tuple[int, int]] = {}
        for row in events:
            if not isinstance(row, dict) or set(row) != {"identity", "fingerprint"}:
                raise ValueError("Invalid completion receipt schema")
            identity, fingerprint = row["identity"], row["fingerprint"]
            if (
                not isinstance(identity, tuple)
                or len(identity) != 2
                or not nonnegative_integer(identity[0])
                or type(identity[1]) is not int
                or not 0 <= identity[1] < self.num_agents
                or identity in known
            ):
                raise ValueError("Invalid/duplicate completion identity")
            if not isinstance(fingerprint, str) or re.fullmatch(r"[0-9a-f]{64}", fingerprint) is None:
                raise ValueError("Invalid completion fingerprint")
            if identity[1] in latest and identity[0] <= latest[identity[1]][0]:
                raise ValueError("Nonmonotonic lane completion history")
            owned_identity: tuple[int, int] = (identity[0], identity[1])
            known[owned_identity], latest[owned_identity[1]] = fingerprint, owned_identity
        if (not events and body["generation"] != 0) or (events and not 1 <= body["generation"] <= len(events)):
            raise ValueError("Completion generation contradicts event history")
        for index, (lane, metric) in enumerate(zip(lanes, metrics, strict=True)):
            self._validate_lane(lane)
            if metric is None:
                if index in latest:
                    raise ValueError("Missing completed metrics")
                if lane != self._initial_lane():
                    raise ValueError("An untouched lane cannot invent stage/counter history")
                continue
            if not isinstance(metric, dict) or set(metric) != {"event", "previous_fraction"}:
                raise ValueError("Invalid canonical completion metric fields")
            previous = metric["previous_fraction"]
            if not finite_number(previous) or not 0 <= previous <= 1:
                raise ValueError("Previous fraction must be within [0, 1]")
            event = lane_outcome_from_state(metric["event"])
            identity = (event.batch_episode, event.outcome.agent_idx)
            if latest.get(index) != identity or known[identity] != freeze_lane_outcome(event).fingerprint:
                raise ValueError("Completed metrics contradict identity/content receipt")
            completion_count = sum(pair[1] == index for pair in known)
            if completion_count == 1 and previous != 0:
                raise ValueError("First completion cannot invent an earlier baseline")
            if lane["episodes_at_stage"] > completion_count or lane["dwell"] < lane["episodes_at_stage"]:
                raise ValueError("Lane counters contradict completion history")
            self._validate_effects(lane, event, previous, completion_count)

    def _validate_effects(self, lane: dict[str, Any], event: LaneOutcome, previous: float, completion_count: int) -> None:
        """Reconcile only effects derivable from retained current completion data."""
        if completion_count == 1:
            expected = self._initial_lane()
            self._advance_lane(expected, event, 0.0)
            if lane != expected:
                raise ValueError("First completion effects contradict the authored initial state")
        count, dwell, stage = lane["episodes_at_stage"], lane["dwell"], lane["stage"]
        if self._strategy == "static":
            if count != completion_count:
                raise ValueError("Static completion counters cannot reset")
        elif stage > min(5, 1 + completion_count - count):
            raise ValueError("Committed stage is unreachable from recorded completion count")
        if (count == 0) != (dwell == 0):
            raise ValueError("Stage dwell and completion count must reset together")
        if count > 0 and dwell < event.outcome.survival_time + count - 1:
            raise ValueError("Stage dwell cannot omit the latest eligible transitions")
        if self._strategy == "static":
            return
        if self._config["difficulty_mode"] == "rate_limited":
            low, high = self._config["min_difficulty"], self._config["max_difficulty"]
            rate = self._config["adaptation_rate"]
            if rate == 0:
                if lane["difficulty"] != low:
                    raise ValueError("Zero-rate difficulty must remain at its authored initial bound")
            else:
                target = low + (stage - 1) / 4 * (high - low)
                budget = rate * event.outcome.survival_time
                # The predecessor is within the band; no older payload is needed.
                # Permit one representable boundary step for arithmetic rounding.
                reachable_low = math.nextafter(min(target, low + budget), -math.inf)
                reachable_high = math.nextafter(max(target, high - budget), math.inf)
                if lane["difficulty"] < reachable_low or lane["difficulty"] > reachable_high:
                    raise ValueError("Difficulty is unreachable under the latest completion rate budget")
        fraction = event.outcome.survival_time / event.planned_horizon
        retreat = any((fraction < self._config["survival_retreat_threshold"], fraction - previous < 0))
        advance = (
            fraction > self._config["survival_advance_threshold"]
            and fraction - previous > 0
            and event.policy_entropy < self._config["entropy_gate"]
        )
        if count == 0:
            if not ((stage < 5 and retreat) or (stage > 1 and advance)):
                raise ValueError("Reset counters require a possible latest stage transition")
        elif dwell >= self._config["min_steps_at_stage"] and ((stage > 1 and retreat) or (stage < 5 and advance)):
            raise ValueError("Retained stage counters contradict the latest commitment rule")

    def _validate_lane(self, lane: Any) -> None:
        if not isinstance(lane, dict) or set(lane) != {"stage", "dwell", "episodes_at_stage", "difficulty"}:
            raise ValueError("Invalid curriculum lane fields")
        stage = lane["stage"]
        if type(stage) is not int or (not 1 <= stage <= 5 if self._strategy == "adversarial" else stage != 0):
            raise ValueError("Invalid curriculum stage")
        if not nonnegative_integer(lane["dwell"]) or not nonnegative_integer(lane["episodes_at_stage"]):
            raise ValueError("Invalid curriculum dwell/completion count")
        low, high = (
            (self._config["min_difficulty"], self._config["max_difficulty"])
            if self._strategy == "adversarial"
            else (self._config["difficulty_level"], self._config["difficulty_level"])
        )
        if not finite_number(lane["difficulty"]) or not low <= lane["difficulty"] <= high:
            raise ValueError("Invalid curriculum difficulty state")
        if self._strategy == "adversarial" and self._config["difficulty_mode"] == "stage_band":
            if not math.isclose(lane["difficulty"], low + (stage - 1) / 4 * (high - low), rel_tol=0, abs_tol=1e-12):
                raise ValueError("Stage-band difficulty contradicts committed stage")

    def load_state(self, state: dict[str, Any]) -> None:
        """Own and validate the entire current snapshot before replacing live state."""
        owned = deepcopy(state)
        self.validate_checkpoint_state(owned)
        self._state, self._owner_token, self.transition_events = owned, object(), []

    def prepare_native_state(self, state: dict[str, Any], *, parent_plan: Any) -> PreparedNativeCurriculum:
        """Prepare data only; this never grants or performs live installation."""
        from townlet.exploration.rng_custody import process_rng_domain
        from townlet.population.vectorized import validate_native_population_data

        validate_native_population_data(plan=parent_plan, owner=self)
        baseline, token = self._state, self._owner_token
        generation = self._body()["generation"]
        tensors: list[torch.Tensor] = []

        def inventory(value: Any) -> None:
            if type(value) is torch.Tensor:
                if value.__dict__ or value.layout != torch.strided or value.device.type not in ("cpu", "cuda"):
                    raise ValueError("Native curriculum requires ordinary strided CPU/CUDA tensors without overrides")
                tensors.append(value)
                return
            if type(value) is dict and all(type(key) is str for key in value):
                for item in value.values():
                    inventory(item)
                return
            if type(value) in (list, tuple):
                for item in value:
                    inventory(item)
                return
            if value is None or type(value) in (str, bool, int, float):
                return
            raise ValueError("Native curriculum requires ordinary portable state")

        def own(value: Any) -> Any:
            if type(value) is torch.Tensor:
                if (
                    value.__dict__
                    or value.layout != torch.strided
                    or value.device.type not in ("cpu", "cuda")
                    or (value.device.type == "cuda" and value.device.index not in devices)
                ):
                    raise ValueError("Native curriculum tensor changed outside the admitted device inventory")
                return torch.Tensor.clone(torch.Tensor.detach(value))
            if type(value) is dict and all(type(key) is str for key in value):
                return {key: own(item) for key, item in value.items()}
            if type(value) is list:
                return [own(item) for item in value]
            if type(value) is tuple:
                return tuple(own(item) for item in value)
            if value is None or type(value) in (str, bool, int, float):
                return value
            raise ValueError("Native curriculum requires ordinary portable state")

        inventory(state)
        domain = process_rng_domain()
        with domain.admission(lineage=None) as gate:
            devices = tuple(sorted({gate.resolve_cuda(value.device) for value in tensors if value.device.type == "cuda"}))
            if self._native_participant is None:
                self._native_participant = domain.register(owner=self, cuda_devices=devices, entrypoints=frozenset({"prepare"}))
            else:
                gate.enroll(participant=self._native_participant, cuda_devices=devices)
            with domain.device_invocation(
                participant=self._native_participant, operation_kind="prepare", lineage=None, cuda_devices=devices
            ):
                validate_native_population_data(plan=parent_plan, owner=self)
                owned = own(state)
                self.validate_checkpoint_state(owned)
                prepared = object.__new__(PreparedNativeCurriculum)
                self._native_states[prepared] = {
                    "plan": weakref.ref(parent_plan),
                    "pid": os.getpid(),
                    "thread": threading.current_thread(),
                    "baseline": baseline,
                    "token": token,
                    "generation": generation,
                    "config": deepcopy(self._config),
                    "state": owned,
                    "new_token": object(),
                    "events": [],
                    "consumed": False,
                }
                self._native_state_record(prepared, parent_plan)
        return prepared

    def _native_state_record(self, prepared: PreparedNativeCurriculum, parent_plan: Any) -> dict[str, Any]:
        from townlet.population.vectorized import validate_native_population_data

        if type(prepared) is PreparedNativeCurriculum:
            record = self._native_states.get(prepared)
        else:
            record = None
        if (
            record is None
            or record["consumed"]
            or record["plan"]() is not parent_plan
            or record["pid"] != os.getpid()
            or record["thread"] is not threading.current_thread()
        ):
            raise ValueError("Foreign, consumed or cross-execution native curriculum preparation")
        validate_native_population_data(plan=parent_plan, owner=self)
        if (
            record["baseline"] is not self._state
            or record["token"] is not self._owner_token
            or record["generation"] != self._body()["generation"]
            or record["config"] != self._config
        ):
            raise ValueError("Native curriculum preparation is stale")
        return record

    def install_native_state(self, *, prepared: PreparedNativeCurriculum, parent_plan: Any, attempt: Any, restored: Any) -> None:
        """Assignment-publish owned data without replacing this registered owner."""
        from townlet.environment.restore_attempt import validate_restore_finalizer

        record = self._native_state_record(prepared, parent_plan)
        validate_restore_finalizer(attempt=attempt, owner=self, restored=restored)
        record["consumed"] = True
        self._state, self._owner_token, self.transition_events = record["state"], record["new_token"], record["events"]

    def _stage_info(self, agent_idx: int) -> dict[str, Any]:
        body = self._body()
        if type(agent_idx) is not int or not 0 <= agent_idx < self.num_agents:
            raise ValueError("Invalid curriculum lane")
        lane = body["lanes"][agent_idx]
        metric = body["metrics"][agent_idx]
        info: dict[str, Any] = {
            "current_stage": lane["stage"],
            "steps_at_stage": lane["dwell"],
            "episodes_at_stage": lane["episodes_at_stage"],
            "commit_mode": "completion",
            "survival_rate": 0.0,
            "survival_baseline": 0.0,
            "learning_progress": 0.0,
            "completion_reason": None,
            "likely_transition_soon": False,
            "active_meters_status": "unqualified",
            "reward_mode_status": "unqualified",
            "difficulty_calibrated": False,
        }
        if metric is not None:
            event = lane_outcome_from_state(metric["event"])
            fraction = event.outcome.survival_time / event.planned_horizon
            info.update(
                survival_rate=fraction,
                survival_baseline=fraction,
                learning_progress=fraction - metric["previous_fraction"],
                completion_reason=event.outcome.reason,
            )
            info.update(
                {
                    key: getattr(event, key)
                    for key in (
                        "reward_total",
                        "reward_extrinsic",
                        "reward_intrinsic",
                        "reward_shaping",
                        "policy_entropy",
                        "world_id",
                        "world_episode_seq",
                    )
                }
            )
        return info


class AdversarialCurriculum(CompletionCurriculum):
    """Commit one stage decision from equal-unit completed survival and lane clocks."""

    def __init__(
        self,
        *,
        commit_mode: str,
        difficulty_mode: str,
        adaptation_rate: float,
        min_difficulty: float,
        max_difficulty: float,
        survival_advance_threshold: float,
        survival_retreat_threshold: float,
        entropy_gate: float,
        min_steps_at_stage: int,
        device: torch.device,
    ):
        if commit_mode != "completion" or difficulty_mode not in ("stage_band", "rate_limited"):
            raise ValueError("Only completion with stage_band/rate_limited is supported")
        numbers = (adaptation_rate, min_difficulty, max_difficulty, survival_advance_threshold, survival_retreat_threshold, entropy_gate)
        if not all(finite_number(value) for value in numbers):
            raise ValueError("Curriculum policy numbers must be finite")
        if adaptation_rate < 0 or not 0 <= min_difficulty <= max_difficulty <= 1:
            raise ValueError("Invalid difficulty band/adaptation rate")
        if not 0 <= survival_retreat_threshold <= survival_advance_threshold <= 1 or not 0 <= entropy_gate <= 1:
            raise ValueError("Invalid survival/entropy thresholds")
        if not nonnegative_integer(min_steps_at_stage) or not isinstance(device, torch.device):
            raise ValueError("Invalid curriculum dwell/device")
        config = {
            "commit_mode": commit_mode,
            "difficulty_mode": difficulty_mode,
            "adaptation_rate": float(adaptation_rate),
            "min_difficulty": float(min_difficulty),
            "max_difficulty": float(max_difficulty),
            "survival_advance_threshold": float(survival_advance_threshold),
            "survival_retreat_threshold": float(survival_retreat_threshold),
            "entropy_gate": float(entropy_gate),
            "min_steps_at_stage": min_steps_at_stage,
        }
        super().__init__("adversarial", config)
        self.device = device

    def _initial_lane(self) -> dict[str, Any]:
        return {"stage": 1, "dwell": 0, "episodes_at_stage": 0, "difficulty": self._config["min_difficulty"]}

    def _advance_lane(self, lane: dict[str, Any], event: LaneOutcome, previous_fraction: float) -> dict[str, Any] | None:
        fraction = event.outcome.survival_time / event.planned_horizon
        progress = fraction - previous_fraction
        stage = lane["stage"]
        lane["dwell"] += event.outcome.survival_time
        lane["episodes_at_stage"] += 1
        dwell = lane["dwell"]
        reason = None
        if dwell >= self._config["min_steps_at_stage"]:
            if stage > 1 and (fraction < self._config["survival_retreat_threshold"] or progress < 0):
                reason = "retreat"
            elif (
                stage < 5
                and fraction > self._config["survival_advance_threshold"]
                and progress > 0
                and event.policy_entropy < self._config["entropy_gate"]
            ):
                reason = "advance"
        transition = None
        if reason is not None:
            lane["stage"] += 1 if reason == "advance" else -1
            lane["dwell"], lane["episodes_at_stage"] = 0, 0
            transition = {
                "agent_idx": event.outcome.agent_idx,
                "world_id": event.world_id,
                "world_episode_seq": event.world_episode_seq,
                "batch_episode": event.batch_episode,
                "from_stage": stage,
                "to_stage": lane["stage"],
                "reason": reason,
                "survival_rate": fraction,
                "learning_progress": progress,
                "entropy": event.policy_entropy,
                "steps_at_stage": dwell,
            }
        low, high = self._config["min_difficulty"], self._config["max_difficulty"]
        target = low + (lane["stage"] - 1) / 4 * (high - low)
        if self._config["difficulty_mode"] == "rate_limited":
            budget = self._config["adaptation_rate"] * event.outcome.survival_time
            current = lane["difficulty"]
            # Saturation keeps the target directly instead of cancelling D+(T-D).
            if abs(target - current) > budget:
                if target > current:
                    target = current + budget
                else:
                    target = current - budget
        lane["difficulty"] = min(high, max(low, target))
        return transition

    def get_batch_decisions(self, agent_states: BatchedAgentState | None, agent_ids: list[str]) -> list[CurriculumDecision]:
        """Read committed lane decisions; state is not a completion snapshot."""
        body = self._body()
        if len(agent_ids) != self.num_agents:
            raise ValueError("Decision identities must cover the initialized lanes")
        result = []
        for lane, agent_id in zip(body["lanes"], agent_ids, strict=True):
            stage = STAGE_CONFIGS[lane["stage"] - 1]
            difficulty = lane["difficulty"]
            if self._config["difficulty_mode"] == "stage_band":
                difficulty = self._config["min_difficulty"] + (lane["stage"] - 1) / 4 * (
                    self._config["max_difficulty"] - self._config["min_difficulty"]
                )
            result.append(
                CurriculumDecision(
                    difficulty_level=difficulty,
                    active_meters=stage.active_meters.copy(),
                    depletion_multiplier=stage.depletion_multiplier,
                    reward_mode=stage.reward_mode,
                    reason=f"{stage.description} (agent {agent_id})",
                )
            )
        return result

    def get_stage_info(self, agent_idx: int = 0) -> dict[str, Any]:
        info = self._stage_info(agent_idx)
        active = self._config["difficulty_mode"] == "rate_limited"
        info.update(
            difficulty_mode=self._config["difficulty_mode"],
            adaptation_rate=self._config["adaptation_rate"],
            adaptation_rate_active=active,
            adaptation_rate_units="difficulty_per_eligible_transition" if active else "inactive",
        )
        info["likely_transition_soon"] = (
            info["current_stage"] < 5
            and info["steps_at_stage"] >= self._config["min_steps_at_stage"]
            and info["survival_rate"] >= self._config["survival_advance_threshold"]
        )
        return info
