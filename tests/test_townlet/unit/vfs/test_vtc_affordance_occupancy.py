"""Tests for VTC affordance occupancy writes.

Affordance state is per world (S1: storage ``[worlds, affordances, ...]``) and a world has
one agent, so each world's claimant claims its own world's row: there is no cross-world
contention to resolve.
"""

import torch

from townlet.environment.action_config import ActionConfig
from townlet.vfs.schema import VariableScope, WriteSpec
from townlet.vfs.vtc import VTCWriteTarget, compile_vtc_affordance_occupancy

OCCUPANCY = VTCWriteTarget(VariableScope.AFFORDANCE, "scalar", meter=False)


def _write(
    *,
    variable_id: str,
    expression: str,
    composition: str,
    clamp: tuple[float, float] | None = None,
) -> WriteSpec:
    return WriteSpec(
        variable_id=variable_id,
        expression=expression,
        condition=None,
        composition=composition,
        phase="resolve_affordance_access_and_occupancy",
        priority=0,
        clamp=clamp,
        telemetry_label=f"{variable_id}_{composition}",
    )


def _affordance_action(
    *,
    action_id: int,
    name: str,
    source_affordance: str,
    writes: list[WriteSpec],
) -> ActionConfig:
    return ActionConfig(
        id=action_id,
        name=name,
        type="interaction",
        costs={},
        effects={},
        delta=None,
        teleport_to=None,
        enabled=True,
        description=None,
        icon=None,
        source="affordance",
        source_affordance=source_affordance,
        reads=[],
        writes=writes,
    )


def test_vtc_affordance_occupancy_claim_if_free_targets_source_affordance_row() -> None:
    sleep = _affordance_action(
        action_id=20,
        name="SLEEP",
        source_affordance="bed",
        writes=[_write(variable_id="occupied_by", expression="agent_id", composition="claim_if_free")],
    )
    work = _affordance_action(
        action_id=21,
        name="WORK",
        source_affordance="job",
        writes=[_write(variable_id="occupied_by", expression="agent_id", composition="claim_if_free")],
    )

    program = compile_vtc_affordance_occupancy([sleep, work], {"occupied_by": OCCUPANCY}, affordance_ids=["bed", "job"])
    free = [-1.0, -1.0]
    updated = program.apply(
        actions=torch.tensor([20, 20, 21, 0]),
        # World 1's bed is already held by its agent; the other worlds start free.
        vfs_state={"occupied_by": torch.tensor([free, [1.0, -1.0], free, free])},
        bars_state={},
        active_mask=torch.tensor([True, True, True, True]),
        device=torch.device("cpu"),
    ).values

    # Each world's claim lands in its own row only: world 0 takes its bed, world 1 keeps
    # its claim, world 2 takes its job, world 3 claimed nothing.
    assert torch.equal(updated["occupied_by"], torch.tensor([[0.0, -1.0], [1.0, -1.0], [-1.0, 2.0], free]))


def test_vtc_affordance_capacity_claim_fills_first_free_slots_without_overallocating() -> None:
    heal = _affordance_action(
        action_id=30,
        name="HEAL",
        source_affordance="hospital",
        writes=[_write(variable_id="slot_owner", expression="agent_id", composition="capacity_claim", clamp=(0.0, 2.0))],
    )

    program = compile_vtc_affordance_occupancy([heal], {"slot_owner": OCCUPANCY}, affordance_ids=["bed", "hospital"])
    bed = [-1.0, -1.0]
    updated = program.apply(
        actions=torch.tensor([30, 30, 30, 0]),
        vfs_state={"slot_owner": torch.tensor([[bed, [8.0, -1.0]], [bed, [-1.0, -1.0]], [bed, [5.0, 6.0]], [bed, [-1.0, -1.0]]])},
        bars_state={},
        active_mask=torch.tensor([True, True, True, True]),
        device=torch.device("cpu"),
    ).values

    # One claimant per world takes its world's first free slot; a full world is unchanged
    # and an idle world's slots stay free. The bed is never touched.
    assert torch.equal(
        updated["slot_owner"],
        torch.tensor([[bed, [8.0, 0.0]], [bed, [1.0, -1.0]], [bed, [5.0, 6.0]], [bed, [-1.0, -1.0]]]),
    )
