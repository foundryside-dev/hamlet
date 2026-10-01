"""Read and reconcile current offline episode accounting for curve exporters."""

from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator  # type: ignore[import-untyped]


@dataclass(frozen=True)
class EpisodeAccounting:
    episode_id: int
    survival_steps_agent0: int
    batch_episode_steps: int
    live_agent_transitions: int
    epsilon: float
    intrinsic_weight: float


def read_episode_accounting(run_dir: Path) -> list[EpisodeAccounting]:
    """Require complete SQL/event agreement before an exporter writes output."""
    database = (run_dir / "demo.db").resolve()
    connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
    try:
        values = connection.execute(
            "SELECT episode_id, survival_time, batch_episode_steps, live_agent_transitions, epsilon, intrinsic_weight "
            "FROM episodes ORDER BY episode_id"
        ).fetchall()
    finally:
        connection.close()
    if not values:
        raise ValueError("No completed episode accounting to export")
    rows = []
    seen = set()
    for episode, survival, batch, live, epsilon, weight in values:
        if any(type(value) is not int or value < 0 for value in (episode, survival, batch, live)):
            raise ValueError("Episode accounting units must be nonnegative integers")
        if episode in seen or not 0 < survival <= batch <= live:
            raise ValueError("Episode accounting has duplicate episodes or inconsistent lane/batch/live units")
        if any(type(value) not in (int, float) or not math.isfinite(value) for value in (epsilon, weight)):
            raise ValueError("Episode exploration context must be finite")
        seen.add(episode)
        rows.append(EpisodeAccounting(episode, survival, batch, live, float(epsilon), float(weight)))

    event_dir = run_dir / "tensorboard"
    if not event_dir.is_dir():
        event_dir = run_dir / "checkpoints" / "tensorboard"
    if not event_dir.is_dir():
        raise ValueError("Episode accounting requires TensorBoard survival events")
    accumulator = EventAccumulator(str(event_dir), size_guidance={"scalars": 0})
    accumulator.Reload()
    tags = sorted(tag for tag in accumulator.Tags()["scalars"] if tag.endswith("/Episode/Survival_Time"))
    if "agent_0/Episode/Survival_Time" not in tags:
        raise ValueError("Episode accounting requires explicit slot-zero survival events")
    lane_values: dict[str, dict[int, int]] = {}
    for tag in tags:
        readings: dict[int, int] = {}
        for event in accumulator.Scalars(tag):
            if event.step in readings:
                raise ValueError(f"Duplicate lane survival event: {tag}/{event.step}")
            if not math.isfinite(event.value) or event.value <= 0 or not event.value.is_integer():
                raise ValueError(f"Lane survival must be a positive integer: {tag}/{event.step}")
            readings[event.step] = int(event.value)
        if readings.keys() != seen:
            raise ValueError(f"Missing or extra lane survival episodes: {tag}")
        lane_values[tag] = readings
    for row in rows:
        survival_values = [readings[row.episode_id] for readings in lane_values.values()]
        if (
            lane_values["agent_0/Episode/Survival_Time"][row.episode_id] != row.survival_steps_agent0
            or sum(survival_values) != row.live_agent_transitions
            or max(survival_values) != row.batch_episode_steps
        ):
            raise ValueError(f"Database/TensorBoard episode accounting disagreement: {row.episode_id}")
    return rows
