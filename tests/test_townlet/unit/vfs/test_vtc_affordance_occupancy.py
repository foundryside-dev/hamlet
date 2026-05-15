"""Tests for VTC affordance occupancy and contention writes."""

import torch

from townlet.environment.action_config import ActionConfig
from townlet.vfs.schema import WriteSpec
from townlet.vfs.vtc import compile_vtc_affordance_occupancy


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

    program = compile_vtc_affordance_occupancy([sleep, work], affordance_ids=["bed", "job"])
    updated = program.apply(
        actions=torch.tensor([20, 20, 21, 0]),
        vfs_state={"occupied_by": torch.tensor([-1.0, -1.0])},
        bars_state={},
        active_mask=torch.tensor([True, True, True, True]),
        device=torch.device("cpu"),
    )

    assert torch.allclose(updated["occupied_by"], torch.tensor([0.0, 2.0]))


def test_vtc_affordance_capacity_claim_fills_first_free_slots_without_overallocating() -> None:
    heal = _affordance_action(
        action_id=30,
        name="HEAL",
        source_affordance="hospital",
        writes=[_write(variable_id="slot_owner", expression="agent_id", composition="capacity_claim", clamp=(0.0, 2.0))],
    )

    program = compile_vtc_affordance_occupancy([heal], affordance_ids=["bed", "hospital"])
    updated = program.apply(
        actions=torch.tensor([30, 30, 30, 0]),
        vfs_state={"slot_owner": torch.tensor([[8.0, -1.0], [-1.0, -1.0]])},
        bars_state={},
        active_mask=torch.tensor([True, True, True, True]),
        device=torch.device("cpu"),
    )

    assert torch.allclose(updated["slot_owner"], torch.tensor([[8.0, -1.0], [0.0, 1.0]]))
