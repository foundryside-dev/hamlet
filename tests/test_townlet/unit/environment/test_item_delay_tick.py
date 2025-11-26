"""Ensure item effects use the current tick when scheduling delays."""

from __future__ import annotations

import torch

from townlet.effects.scheduler import Scheduler
from townlet.effects.schema import CommandNode, CommandType


class DummyItemHandler:
    """Minimal handler to capture scheduled commands."""

    def __init__(self, scheduler: Scheduler):
        self.scheduler = scheduler

    def handle_use_slot_action(self, *, agent_idx: int, slot_idx: int, current_tick: int, meters):
        # Schedule a delayed no-op command to observe base_tick
        cmd = CommandNode(type=CommandType.DELAY, delay_ticks_ast=None, delay_commands=[])
        # Emulate executor scheduling with explicit base_tick/current_tick
        self.scheduler.schedule(commands=[cmd], delay_ticks=1, scope="agent", entity_id=agent_idx, base_tick=current_tick)


def test_item_delay_uses_current_tick(cpu_device):
    scheduler = Scheduler()
    handler = DummyItemHandler(scheduler)

    class DummyEnv:
        def __init__(self):
            self.item_handler = handler
            self.item_inventory = type("Inv", (), {"max_items_per_agent": 1})()
            self.action_space = type(
                "AS",
                (),
                {
                    "get_action_by_name": lambda self, name: type("A", (), {"id": 0})(),
                },
            )()
            self.step_counts = torch.tensor([5], device=cpu_device)  # simulate tick 5
            self.positions = torch.zeros((1, 2), device=cpu_device)
            self.meters = torch.zeros((1, 1), device=cpu_device)
            self.num_agents = 1
            self._movement_deltas = torch.zeros((1, 2), device=cpu_device)
            self.device = cpu_device
            self.action_ids = {"INTERACT": None}
            self.bars_config = type("BC", (), {"meters": []})()
            self.meter_count = 1
            self.meter_name_to_index = {}
            self.action_dim = 1

        def _execute_actions(self, actions):
            # Inline the relevant part of VectorizedHamletEnv._execute_actions for USE_SLOT_0
            use_action_id = 0
            use_mask = actions == use_action_id
            if use_mask.any():
                for agent_idx in torch.where(use_mask)[0]:
                    self.item_handler.handle_use_slot_action(
                        agent_idx=int(agent_idx.item()),
                        slot_idx=0,
                        current_tick=int(self.step_counts[agent_idx].item()),
                        meters=self.meters,
                    )

    env = DummyEnv()
    actions = torch.tensor([0], device=cpu_device)
    env._execute_actions(actions)

    # Ensure scheduler entry is anchored at tick 5 (not 0)
    assert scheduler.pending, "Expected a scheduled delayed command"
    due_tick, items = next(iter(scheduler.pending.items()))
    assert items, "Scheduled list should not be empty"
    scheduled = items[0]
    # due_tick = base_tick + delay_ticks (1); base_tick should be 5 → due_tick 6
    assert scheduled.due_tick == 6
