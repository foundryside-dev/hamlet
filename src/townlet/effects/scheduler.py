"""Tick-aligned scheduler for delayed effect commands."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

MAX_DELAY_TICKS = 1000
MAX_SCHEDULED_ITEMS = 10000


@dataclass(frozen=True)
class ScheduledItem:
    due_tick: int
    commands: list[Any]
    scope: str | None = None
    entity_id: int | str | None = None
    context_overrides: dict[str, Any] = field(default_factory=dict)


class Scheduler:
    """Simple tick-based scheduler with caps and cancellation."""

    def __init__(self, time_enabled: bool = True):
        self.time_enabled = time_enabled
        self.current_tick: int = 0
        self.pending: dict[int, list[ScheduledItem]] = {}

    def schedule(
        self,
        commands: list[Any],
        delay_ticks: int,
        scope: str | None = None,
        entity_id: int | str | None = None,
        context_overrides: dict[str, Any] | None = None,
        base_tick: int | None = None,
    ) -> None:
        """Schedule commands to run after delay_ticks, relative to base_tick (or current_tick)."""
        if not self.time_enabled:
            raise RuntimeError("Scheduling is disabled (time disabled)")
        if delay_ticks < 0:
            raise ValueError("delay_ticks must be >= 0")
        if delay_ticks > MAX_DELAY_TICKS:
            raise ValueError(f"delay_ticks {delay_ticks} exceeds cap {MAX_DELAY_TICKS}")

        anchor = self.current_tick if base_tick is None else base_tick
        due = anchor + delay_ticks
        item = ScheduledItem(
            due_tick=due,
            commands=commands,
            scope=scope,
            entity_id=entity_id,
            context_overrides=context_overrides or {},
        )

        # Enforce max items cap
        total_items = sum(len(lst) for lst in self.pending.values())
        if total_items + 1 > MAX_SCHEDULED_ITEMS:
            raise RuntimeError(f"Scheduling rejected: pending items would exceed cap {MAX_SCHEDULED_ITEMS}")

        self.pending.setdefault(due, []).append(item)

    def advance(self, tick: int) -> list[ScheduledItem]:
        """Advance scheduler to tick and drain due items."""
        if tick < self.current_tick:
            raise ValueError("Cannot decrease scheduler tick")
        self.current_tick = tick
        return self.drain_due()

    def drain_due(self) -> list[ScheduledItem]:
        """Return and remove items due at current_tick."""
        items = self.pending.pop(self.current_tick, [])
        return items

    def cancel(self, scope: str | None, entity_id: int | str | None) -> None:
        """Cancel all pending items matching scope/entity_id."""
        for tick, items in list(self.pending.items()):
            filtered = [it for it in items if not (it.scope == scope and it.entity_id == entity_id)]
            if filtered:
                self.pending[tick] = filtered
            else:
                self.pending.pop(tick, None)

    def reset(self, current_tick: int = 0) -> None:
        """Clear all pending items and reset the clock."""
        self.pending.clear()
        self.current_tick = current_tick

    def state_dict(self) -> dict[str, Any]:
        return {"current_tick": self.current_tick, "pending": self.pending}

    def load_state_dict(self, state: dict[str, Any]) -> None:
        self.current_tick = int(state.get("current_tick", 0))
        self.pending = state.get("pending", {})
