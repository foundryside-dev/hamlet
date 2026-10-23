"""Required current-format recording DTOs and canonical eligible reward ledgers."""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from typing import cast, get_args

from townlet.training.episode import CompletionReason

RECORDING_FORMAT_VERSION = 2
REWARD_REL_TOL = 1e-5
REWARD_ABS_TOL = 1e-6


def finite_recording_reward(value: object) -> float:
    if type(value) not in (int, float):
        raise ValueError("Recording value must be numeric and not bool")
    try:
        result = float(cast(int | float, value))
    except OverflowError as error:
        raise ValueError("Recording value must be finite") from error
    if not math.isfinite(result):
        raise ValueError("Recording value must be finite")
    return result


def reconcile_recording_reward(observed: object, expected: object) -> None:
    actual = finite_recording_reward(observed)
    reference = finite_recording_reward(expected)
    if not math.isclose(actual, reference, rel_tol=REWARD_REL_TOL, abs_tol=REWARD_ABS_TOL):
        raise ValueError("Recording reward ledger mismatch")


def build_recording_reward_payload(*, total: float, extrinsic: float, intrinsic: float, shaping: float) -> dict[str, float]:
    values = {
        "reward": finite_recording_reward(total),
        "extrinsic_reward": finite_recording_reward(extrinsic),
        "intrinsic_reward": finite_recording_reward(intrinsic),
        "shaping_reward": finite_recording_reward(shaping),
    }
    reconcile_recording_reward(
        values["reward"], math.fsum(values[key] for key in ("extrinsic_reward", "intrinsic_reward", "shaping_reward"))
    )
    return values


def _count(value: object, name: str) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"Recording {name} must be a nonnegative integer")


def _position(value: object) -> tuple[int, ...]:
    if not isinstance(value, (tuple, list)):
        raise ValueError("Recording position must contain integer coordinates")
    for coordinate in value:
        _count(coordinate, "coordinate")
    return tuple(value)


def validate_affordance_layout(value: object) -> dict[str, tuple[int, ...]]:
    if not isinstance(value, dict) or any(type(name) is not str or not name for name in value):
        raise ValueError("Recording affordance layout must be flat named positions")
    layout = {name: _position(position) for name, position in value.items()}
    if len({len(position) for position in layout.values()}) > 1:
        raise ValueError("Recording affordance position dimensions disagree")
    return layout


def _named_counts(value: object) -> None:
    if not isinstance(value, dict) or any(type(name) is not str for name in value):
        raise ValueError("Recording counters require named integer counts")
    for count in value.values():
        _count(count, "count")


@dataclass(frozen=True, slots=True)
class RecordedStep:
    """One entry-eligible transition with canonical total and composed contributors."""

    step: int
    position: tuple[int, ...]
    meters: tuple[float, ...]
    action: int
    reward: float
    extrinsic_reward: float
    intrinsic_reward: float  # Effective DAC contributor, already weighted and modulated.
    shaping_reward: float
    done: bool  # Actual MDP terminal flag; caller truncation does not fabricate it.
    q_values: tuple[float, ...] | None
    epsilon: float | None = None
    action_masks: tuple[bool, ...] | None = None
    time_of_day: int | None = None
    interaction_progress: float | None = None

    def __post_init__(self) -> None:
        _count(self.step, "step")
        _count(self.action, "action")
        _position(self.position)
        if not isinstance(self.meters, (tuple, list)) or not self.meters:
            raise ValueError("Recording meters must be a nonempty sequence")
        for value in self.meters:
            finite_recording_reward(value)
        if type(self.done) is not bool:
            raise ValueError("Recording done must be bool")
        build_recording_reward_payload(
            total=self.reward, extrinsic=self.extrinsic_reward, intrinsic=self.intrinsic_reward, shaping=self.shaping_reward
        )
        if self.q_values is not None:
            if not isinstance(self.q_values, (tuple, list)):
                raise ValueError("Recording Q-values must be a sequence")
            for value in self.q_values:
                finite_recording_reward(value)
        if self.action_masks is not None and (
            not isinstance(self.action_masks, (tuple, list)) or any(type(value) is not bool for value in self.action_masks)
        ):
            raise ValueError("Recording action masks must contain bools")
        if self.epsilon is not None:
            finite_recording_reward(self.epsilon)
        if self.time_of_day is not None:
            _count(self.time_of_day, "time of day")
        if self.interaction_progress is not None:
            finite_recording_reward(self.interaction_progress)


@dataclass(frozen=True, slots=True)
class EpisodeMetadata:
    """An owned episode summary of eligible canonical rewards and completion."""

    episode_id: int
    survival_steps: int
    completion_reason: CompletionReason
    total_reward: float
    extrinsic_reward: float
    intrinsic_reward: float
    shaping_reward: float
    curriculum_stage: int
    epsilon: float
    intrinsic_weight: float  # Context only; recorded intrinsic is not reweighted.
    timestamp: float
    affordance_layout: dict[str, tuple[int, ...]]
    affordance_visits: dict[str, int]
    custom_action_uses: dict[str, int]

    def __post_init__(self) -> None:
        _count(self.episode_id, "episode id")
        _count(self.survival_steps, "survival steps")
        if self.survival_steps == 0:
            raise ValueError("A recording requires eligible frames")
        _count(self.curriculum_stage, "curriculum stage")
        if type(self.completion_reason) is not str or self.completion_reason not in get_args(CompletionReason):
            raise ValueError("Unsupported recording completion reason")
        build_recording_reward_payload(
            total=self.total_reward, extrinsic=self.extrinsic_reward, intrinsic=self.intrinsic_reward, shaping=self.shaping_reward
        )
        for value in (self.epsilon, self.intrinsic_weight, self.timestamp):
            finite_recording_reward(value)
        layout = validate_affordance_layout(self.affordance_layout)
        _named_counts(self.affordance_visits)
        _named_counts(self.custom_action_uses)
        object.__setattr__(self, "affordance_layout", layout)
        object.__setattr__(self, "affordance_visits", dict(self.affordance_visits))
        object.__setattr__(self, "custom_action_uses", dict(self.custom_action_uses))


def _require_fields(data: object, model: type) -> dict:
    if not isinstance(data, dict) or set(data) != {field.name for field in fields(model)}:
        raise ValueError(f"Unsupported {model.__name__} fields")
    return dict(data)


def deserialize_step(data: dict) -> RecordedStep:
    """Deserialize the exact current shape without mutating the caller's payload."""
    candidate = _require_fields(data, RecordedStep)
    candidate["position"] = _position(candidate["position"])
    for key in ("meters", "q_values", "action_masks"):
        if candidate[key] is not None:
            if not isinstance(candidate[key], (list, tuple)):
                raise ValueError(f"Recording {key} must be a sequence")
            candidate[key] = tuple(candidate[key])
    return RecordedStep(**candidate)


def deserialize_metadata(data: dict) -> EpisodeMetadata:
    """Deserialize exact metadata with an owned flat named-position mapping."""
    candidate = _require_fields(data, EpisodeMetadata)
    candidate["affordance_layout"] = validate_affordance_layout(candidate["affordance_layout"])
    return EpisodeMetadata(**candidate)


def reconcile_recording_episode(metadata: Mapping[str, object], steps: Sequence[Mapping[str, object]]) -> None:
    if not steps:
        raise ValueError("A recording must contain eligible frames")
    for row in steps:
        build_recording_reward_payload(
            total=finite_recording_reward(row["reward"]),
            extrinsic=finite_recording_reward(row["extrinsic_reward"]),
            intrinsic=finite_recording_reward(row["intrinsic_reward"]),
            shaping=finite_recording_reward(row["shaping_reward"]),
        )
    for frame_key, metadata_key in (
        ("reward", "total_reward"),
        ("extrinsic_reward", "extrinsic_reward"),
        ("intrinsic_reward", "intrinsic_reward"),
        ("shaping_reward", "shaping_reward"),
    ):
        reconcile_recording_reward(metadata[metadata_key], math.fsum(finite_recording_reward(row[frame_key]) for row in steps))
    reconcile_recording_reward(
        metadata["total_reward"],
        math.fsum(finite_recording_reward(metadata[key]) for key in ("extrinsic_reward", "intrinsic_reward", "shaping_reward")),
    )


def validate_recording_episode(data: object, *, expected_episode_id: int) -> None:
    """Validate local candidates completely before writer output or replay installation."""
    if not isinstance(data, dict) or set(data) != {"version", "metadata", "steps", "affordances"}:
        raise ValueError("Unsupported recording payload fields")
    if type(data["version"]) is not int or data["version"] != RECORDING_FORMAT_VERSION:
        raise ValueError("Unsupported recording format version")
    metadata = deserialize_metadata(data["metadata"])
    if metadata.episode_id != expected_episode_id:
        raise ValueError("Recording episode identity mismatch")
    if not isinstance(data["steps"], list) or len(data["steps"]) != metadata.survival_steps:
        raise ValueError("Recording frame count must equal eligible survival")
    steps = [deserialize_step(row) for row in data["steps"]]
    layout = validate_affordance_layout(data["affordances"])
    if layout != metadata.affordance_layout:
        raise ValueError("Recording affordance layouts disagree")
    rank = len(steps[0].position)
    if any(len(step.position) != rank or step.step != index for index, step in enumerate(steps)):
        raise ValueError("Recording frame indices or position dimensions disagree")
    if any(len(position) != rank for position in layout.values()):
        raise ValueError("Recording frame and affordance position dimensions disagree")
    terminal = metadata.completion_reason in {"authored_terminal", "retirement"}
    if any(step.done for step in steps[:-1]) or steps[-1].done != terminal:
        raise ValueError("Recording terminal flags disagree with completion")
    reconcile_recording_episode(data["metadata"], data["steps"])


@dataclass
class EpisodeEndMarker:
    """Sentinel value marking a queue episode boundary."""

    metadata: EpisodeMetadata
