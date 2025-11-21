"""Unit tests for Scheduler (delay support)."""

import pytest

from townlet.effects.scheduler import MAX_DELAY_TICKS, MAX_SCHEDULED_ITEMS, Scheduler


def test_schedule_and_drain_due():
    sched = Scheduler(time_enabled=True)
    sched.schedule(commands=["a"], delay_ticks=0)

    due = sched.drain_due()
    assert len(due) == 1
    assert due[0].commands == ["a"]


def test_advance_drains_future_tick():
    sched = Scheduler(time_enabled=True)
    sched.schedule(commands=["a"], delay_ticks=2)

    assert sched.drain_due() == []  # nothing at tick 0
    due = sched.advance(2)
    assert len(due) == 1
    assert due[0].due_tick == 2


def test_schedule_respects_max_delay():
    sched = Scheduler(time_enabled=True)
    with pytest.raises(ValueError):
        sched.schedule(commands=[], delay_ticks=MAX_DELAY_TICKS + 1)


def test_schedule_disabled_time():
    sched = Scheduler(time_enabled=False)
    with pytest.raises(RuntimeError):
        sched.schedule(commands=[], delay_ticks=1)


def test_schedule_caps_total_items():
    sched = Scheduler(time_enabled=True)
    # Fill cap
    for i in range(MAX_SCHEDULED_ITEMS):
        sched.schedule(commands=[i], delay_ticks=0)

    with pytest.raises(RuntimeError):
        sched.schedule(commands=["overflow"], delay_ticks=0)


def test_cancel_by_scope_entity():
    sched = Scheduler(time_enabled=True)
    sched.schedule(commands=["a"], delay_ticks=1, scope="agent", entity_id=5)
    sched.schedule(commands=["b"], delay_ticks=1, scope="agent", entity_id=6)

    sched.cancel(scope="agent", entity_id=5)

    due = sched.advance(1)
    cmds = [item.commands for item in due]
    assert cmds == [["b"]]
