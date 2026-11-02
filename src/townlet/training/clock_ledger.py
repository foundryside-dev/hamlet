"""Explicit units for advancing population events; no schedule owns another clock."""

from dataclasses import dataclass, fields, replace


@dataclass(frozen=True, slots=True)
class ClockLedger:
    """Immutable readings, replaced only by their population runtime owner.

    Predictor minibatches count successful provider receipt optimizer updates;
    optimizer_updates counts successful Q learner updates independently.
    """

    vector_ticks: int = 0
    eligible_transitions: int = 0
    optimizer_updates: int = 0
    completed_batch_episodes: int = 0
    predictor_admitted_rows: int = 0
    predictor_consumed_minibatches: int = 0
    predictor_dropped_rows: int = 0

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{field.name} must be a nonnegative integer")

    def advance(self, **increments: int) -> "ClockLedger":
        """Apply nonnegative deltas without mutating a previously published reading."""
        names = {field.name for field in fields(self)}
        if increments.keys() - names:
            raise ValueError("Unknown clock ledger unit")
        for name, value in increments.items():
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} increment must be a nonnegative integer")
        return replace(self, **{name: getattr(self, name) + value for name, value in increments.items()})
