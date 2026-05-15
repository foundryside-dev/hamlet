"""Tests for compiling ActionConfig writes into masked tensor updates."""

import torch

from townlet.environment.action_config import ActionConfig
from townlet.vfs.action_writes import compile_action_writes
from townlet.vfs.schema import WriteSpec


def _write(
    *,
    variable_id: str,
    expression: str,
    condition: str | None,
    composition: str,
    clamp: tuple[float, float] | None,
) -> WriteSpec:
    return WriteSpec(
        variable_id=variable_id,
        expression=expression,
        condition=condition,
        composition=composition,
        phase="action_effects",
        priority=0,
        clamp=clamp,
        telemetry_label=f"{variable_id}_test_write",
    )


def _action(*, action_id: int, name: str, writes: list[WriteSpec]) -> ActionConfig:
    return ActionConfig(
        id=action_id,
        name=name,
        type="passive",
        costs={},
        effects={},
        delta=None,
        teleport_to=None,
        enabled=True,
        description=None,
        icon=None,
        source="custom",
        source_affordance=None,
        reads=[],
        writes=writes,
    )


def test_action_write_compiler_applies_write_only_to_selected_active_agents() -> None:
    action = _action(
        action_id=2,
        name="REST",
        writes=[
            _write(
                variable_id="energy",
                expression="energy + 0.25",
                condition=None,
                composition="overwrite",
                clamp=None,
            )
        ],
    )

    program = compile_action_writes([action])
    updated = program.apply(
        actions=torch.tensor([2, 0, 2]),
        vfs_state={"energy": torch.tensor([0.1, 0.2, 0.3])},
        active_mask=torch.tensor([True, True, False]),
        device=torch.device("cpu"),
    )

    assert torch.allclose(updated["energy"], torch.tensor([0.35, 0.2, 0.3]))


def test_action_write_compiler_combines_action_mask_with_condition() -> None:
    action = _action(
        action_id=3,
        name="RECOVER",
        writes=[
            _write(
                variable_id="energy",
                expression="energy + 0.4",
                condition="energy < 0.5",
                composition="overwrite",
                clamp=(0.0, 1.0),
            )
        ],
    )

    program = compile_action_writes([action])
    updated = program.apply(
        actions=torch.tensor([3, 3, 3]),
        vfs_state={"energy": torch.tensor([0.2, 0.8, 0.4])},
        active_mask=torch.tensor([True, True, True]),
        device=torch.device("cpu"),
    )

    assert torch.allclose(updated["energy"], torch.tensor([0.6, 0.8, 0.8]))
