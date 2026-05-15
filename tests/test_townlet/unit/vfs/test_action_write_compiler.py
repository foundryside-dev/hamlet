"""Tests for compiling ActionConfig writes into masked tensor updates."""

import pytest
import torch

from townlet.environment.action_config import ActionConfig
from townlet.vfs.action_writes import compile_action_writes, compile_action_writes_with_phase_graph
from townlet.vfs.schema import WriteSpec
from townlet.vfs.transition_graph import TransitionPhaseGraph


def _write(
    *,
    variable_id: str,
    expression: str,
    condition: str | None,
    composition: str,
    clamp: tuple[float, float] | None,
) -> WriteSpec:
    return _write_with_metadata(
        variable_id=variable_id,
        expression=expression,
        condition=condition,
        composition=composition,
        phase="apply_action_effects",
        priority=0,
        clamp=clamp,
        telemetry_label=f"{variable_id}_test_write",
    )


def _write_with_metadata(
    *,
    variable_id: str,
    expression: str,
    condition: str | None,
    composition: str,
    phase: str,
    priority: int,
    clamp: tuple[float, float] | None,
    telemetry_label: str,
) -> WriteSpec:
    return WriteSpec(
        variable_id=variable_id,
        expression=expression,
        condition=condition,
        composition=composition,
        phase=phase,
        priority=priority,
        clamp=clamp,
        telemetry_label=telemetry_label,
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


def test_action_write_compiler_composes_additive_and_multiplicative_writes() -> None:
    action = _action(
        action_id=4,
        name="STACK",
        writes=[
            _write_with_metadata(
                variable_id="energy",
                expression="0.2",
                condition=None,
                composition="additive_delta",
                phase="apply_action_effects",
                priority=0,
                clamp=(0.0, 1.0),
                telemetry_label="energy_add_one",
            ),
            _write_with_metadata(
                variable_id="energy",
                expression="0.15",
                condition=None,
                composition="additive_delta",
                phase="apply_action_effects",
                priority=1,
                clamp=(0.0, 1.0),
                telemetry_label="energy_add_two",
            ),
            _write_with_metadata(
                variable_id="fatigue",
                expression="0.5",
                condition=None,
                composition="multiplicative_modifier",
                phase="apply_action_effects",
                priority=0,
                clamp=None,
                telemetry_label="fatigue_half",
            ),
            _write_with_metadata(
                variable_id="fatigue",
                expression="0.8",
                condition=None,
                composition="multiplicative_modifier",
                phase="apply_action_effects",
                priority=1,
                clamp=None,
                telemetry_label="fatigue_decay",
            ),
        ],
    )

    program = compile_action_writes([action])
    updated = program.apply(
        actions=torch.tensor([4, 0]),
        vfs_state={"energy": torch.tensor([0.7, 0.7]), "fatigue": torch.tensor([2.0, 2.0])},
        active_mask=torch.tensor([True, True]),
        device=torch.device("cpu"),
    )

    assert torch.allclose(updated["energy"], torch.tensor([1.0, 0.7]))
    assert torch.allclose(updated["fatigue"], torch.tensor([0.8, 2.0]))


def test_action_write_compiler_composes_min_max_and_clamp_writes() -> None:
    action = _action(
        action_id=5,
        name="BOUNDS",
        writes=[
            _write(
                variable_id="floor_value",
                expression="0.4",
                condition=None,
                composition="max",
                clamp=None,
            ),
            _write(
                variable_id="cap_value",
                expression="0.7",
                condition=None,
                composition="min",
                clamp=None,
            ),
            _write(
                variable_id="energy",
                expression="energy + 0.5",
                condition=None,
                composition="clamp",
                clamp=(0.0, 1.0),
            ),
        ],
    )

    program = compile_action_writes([action])
    updated = program.apply(
        actions=torch.tensor([5, 0]),
        vfs_state={
            "floor_value": torch.tensor([0.2, 0.2]),
            "cap_value": torch.tensor([0.9, 0.9]),
            "energy": torch.tensor([0.8, 0.8]),
        },
        active_mask=torch.tensor([True, True]),
        device=torch.device("cpu"),
    )

    assert torch.allclose(updated["floor_value"], torch.tensor([0.4, 0.2]))
    assert torch.allclose(updated["cap_value"], torch.tensor([0.7, 0.9]))
    assert torch.allclose(updated["energy"], torch.tensor([1.0, 0.8]))


def test_action_write_compiler_resolves_priority_and_last_write_wins() -> None:
    action = _action(
        action_id=6,
        name="CONFLICT",
        writes=[
            _write_with_metadata(
                variable_id="target",
                expression="0.1",
                condition=None,
                composition="priority_write",
                phase="apply_action_effects",
                priority=10,
                clamp=None,
                telemetry_label="low_priority",
            ),
            _write_with_metadata(
                variable_id="target",
                expression="0.9",
                condition=None,
                composition="priority_write",
                phase="apply_action_effects",
                priority=20,
                clamp=None,
                telemetry_label="high_priority",
            ),
            _write_with_metadata(
                variable_id="status",
                expression="0.2",
                condition=None,
                composition="last_write_wins",
                phase="apply_action_effects",
                priority=0,
                clamp=None,
                telemetry_label="status_first",
            ),
            _write_with_metadata(
                variable_id="status",
                expression="0.7",
                condition=None,
                composition="last_write_wins",
                phase="apply_action_effects",
                priority=10,
                clamp=None,
                telemetry_label="status_last",
            ),
        ],
    )

    program = compile_action_writes([action])
    updated = program.apply(
        actions=torch.tensor([6, 0]),
        vfs_state={"target": torch.tensor([0.0, 0.0]), "status": torch.tensor([0.0, 0.0])},
        active_mask=torch.tensor([True, True]),
        device=torch.device("cpu"),
    )

    assert torch.allclose(updated["target"], torch.tensor([0.9, 0.0]))
    assert torch.allclose(updated["status"], torch.tensor([0.7, 0.0]))


def test_action_write_compiler_reads_phase_snapshot_before_committing_writes() -> None:
    action = _action(
        action_id=7,
        name="ATOMIC",
        writes=[
            _write_with_metadata(
                variable_id="energy",
                expression="energy + 1.0",
                condition=None,
                composition="overwrite",
                phase="apply_action_effects",
                priority=0,
                clamp=None,
                telemetry_label="energy_increment",
            ),
            _write_with_metadata(
                variable_id="satiation",
                expression="energy * 10.0",
                condition=None,
                composition="overwrite",
                phase="apply_action_effects",
                priority=1,
                clamp=None,
                telemetry_label="snapshot_reader",
            ),
        ],
    )

    program = compile_action_writes([action])
    updated = program.apply(
        actions=torch.tensor([7]),
        vfs_state={"energy": torch.tensor([1.0]), "satiation": torch.tensor([0.0])},
        active_mask=torch.tensor([True]),
        device=torch.device("cpu"),
    )

    assert torch.allclose(updated["energy"], torch.tensor([2.0]))
    assert torch.allclose(updated["satiation"], torch.tensor([10.0]))


def test_action_write_compiler_uses_spec_phase_order_not_lexical_order() -> None:
    action = _action(
        action_id=8,
        name="ORDER",
        writes=[
            _write_with_metadata(
                variable_id="energy",
                expression="energy + 1.0",
                condition=None,
                composition="overwrite",
                phase="ingest_actions",
                priority=0,
                clamp=None,
                telemetry_label="ingest_increment",
            ),
            _write_with_metadata(
                variable_id="energy",
                expression="energy * 10.0",
                condition=None,
                composition="overwrite",
                phase="advance_global_time",
                priority=0,
                clamp=None,
                telemetry_label="advance_scale",
            ),
        ],
    )

    program = compile_action_writes([action])
    updated = program.apply(
        actions=torch.tensor([8]),
        vfs_state={"energy": torch.tensor([1.0])},
        active_mask=torch.tensor([True]),
        device=torch.device("cpu"),
    )

    assert torch.allclose(updated["energy"], torch.tensor([20.0]))


def test_action_write_compiler_accepts_configured_transition_phase_order() -> None:
    action = _action(
        action_id=9,
        name="CUSTOM_ORDER",
        writes=[
            _write_with_metadata(
                variable_id="energy",
                expression="energy + 1.0",
                condition=None,
                composition="overwrite",
                phase="phase_a",
                priority=0,
                clamp=None,
                telemetry_label="phase_a_increment",
            ),
            _write_with_metadata(
                variable_id="energy",
                expression="energy * 10.0",
                condition=None,
                composition="overwrite",
                phase="phase_b",
                priority=0,
                clamp=None,
                telemetry_label="phase_b_scale",
            ),
        ],
    )
    phase_graph = TransitionPhaseGraph(("phase_b", "phase_a"))

    program = compile_action_writes_with_phase_graph([action], phase_graph)
    updated = program.apply(
        actions=torch.tensor([9]),
        vfs_state={"energy": torch.tensor([1.0])},
        active_mask=torch.tensor([True]),
        device=torch.device("cpu"),
    )

    assert torch.allclose(updated["energy"], torch.tensor([11.0]))


def test_action_write_compiler_rejects_unconfigured_transition_phase() -> None:
    action = _action(
        action_id=10,
        name="UNKNOWN_PHASE",
        writes=[
            _write_with_metadata(
                variable_id="energy",
                expression="energy + 1.0",
                condition=None,
                composition="overwrite",
                phase="unconfigured_phase",
                priority=0,
                clamp=None,
                telemetry_label="unknown_phase_increment",
            )
        ],
    )

    with pytest.raises(ValueError, match="Unknown transition phase"):
        compile_action_writes([action])
