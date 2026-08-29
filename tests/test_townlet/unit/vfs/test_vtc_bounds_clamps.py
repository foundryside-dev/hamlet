"""Tests for VTC bounds-clamp rules — the `clamp_and_validate` phase (hamlet-f46e2b381a).

Before this unit, `clamp_and_validate` appeared exactly once in the codebase — as a
string in DEFAULT_TRANSITION_PHASES — with no rule family ever assigned to it. Declared
bounds were enforced only by per-write clamps at the write sites, and the effect-manager
tick (which runs after cascades, before terminal conditions) could push a meter out of
its declared bounds with nothing between it and terminal/reward/observation reads.

These rules make the phase real: one compiled bounds rule per declared meter, sourced
from `bars.*.bounds`, executed at the already-scheduled `clamp_and_validate` slot.

The per-write clamps (VTC rule clamps, and the environment-level ceilings retained by
PDR-0014 B3 / PDR-0015) are NOT replaced by this phase — they are mid-tick write
contracts with different semantics (a ceiling applied before the passive tick reads
back 0.49, not 0.5). This phase is the end-of-transition invariant net.
"""

import pytest
import torch

from townlet.vfs import vtc
from townlet.vfs.transition_graph import TransitionPhaseGraph
from townlet.vfs.transition_schedule import (
    VTCTransitionContext,
    VTCTransitionRunner,
    VTCTransitionSchedule,
)


def _empty_schedule_with_bounds(program: "vtc.VTCBoundsClampProgram") -> VTCTransitionSchedule:
    return VTCTransitionSchedule(
        phase_graph=TransitionPhaseGraph.default(),
        action_write_program=vtc.VTCActionWriteProgram(writes=()),
        affordance_gate_program=vtc.VTCAffordanceGateProgram(rules=()),
        interaction_progress_program=vtc.VTCInteractionProgressProgram(progress_rules=(), completion_bonus_rules=()),
        terminal_condition_program=vtc.VTCTerminalConditionProgram(rules=()),
        passive_depletion_program=vtc.VTCPassiveDepletionProgram(rules=()),
        modulation_program=vtc.VTCModulationProgram(rules=()),
        threshold_cascade_program=vtc.VTCThresholdCascadeProgram(rules=()),
        social_residue_program=vtc.VTCSocialResidueProgram(rules=()),
        reward_component_program=vtc.VTCRewardProgram(rules=()),
        bounds_clamp_program=program,
    )


def test_compile_vtc_bounds_clamps_emits_rule_metadata() -> None:
    """Declared meter bounds should compile into explicit clamp_and_validate rules."""
    assert hasattr(vtc, "compile_vtc_bounds_clamps"), "VTC bounds-clamp compiler is required"

    program = vtc.compile_vtc_bounds_clamps(
        [
            {"name": "money", "depletion": {"passive": 0.0}, "bounds": {"min": 0.0, "max": 999999.0}},
        ]
    )

    assert len(program.rules) == 1
    rule = program.rules[0]
    assert rule.rule_id == "bounds:money"
    assert rule.kind == "bounds_clamp"
    assert rule.source_variable_id == "money"
    assert rule.variable_id == "money"
    assert rule.expression == "clamp(bar.money, 0.0, 999999.0)"
    assert rule.condition is None
    assert rule.composition == "overwrite"
    assert rule.phase == "clamp_and_validate"
    assert rule.clamp == (0.0, 999999.0)
    assert rule.telemetry_label == "bounds_clamp:money"


def test_vtc_bounds_clamps_apply_enforces_each_meters_declared_bounds() -> None:
    """apply() pulls every meter inside its OWN declared bounds and touches nothing else."""
    program = vtc.compile_vtc_bounds_clamps(
        [
            {"name": "energy", "depletion": {"passive": 0.01}, "bounds": {"min": 0.0, "max": 1.0}},
            {"name": "money", "depletion": {"passive": 0.0}, "bounds": {"min": 0.0, "max": 999999.0}},
        ]
    )
    bars_state = {
        "energy": torch.tensor([1.7, -0.3, 0.5], dtype=torch.float32),
        "money": torch.tensor([22.5, -4.0, 1000000.0], dtype=torch.float32),
        "unbound_extra": torch.tensor([9.0, 9.0, 9.0], dtype=torch.float32),
    }

    updated = program.apply(bars_state=bars_state, device=torch.device("cpu"))

    assert updated["energy"].tolist() == [1.0, 0.0, 0.5]
    assert updated["money"].tolist() == [22.5, 0.0, 999999.0]
    # A bar with no declared bounds rule is left alone — this program only enforces
    # declarations, it invents none.
    assert updated["unbound_extra"].tolist() == [9.0, 9.0, 9.0]
    # Inputs are not mutated in place.
    assert bars_state["energy"].tolist() == pytest.approx([1.7, -0.3, 0.5])


def test_transition_runner_executes_bounds_clamps_in_clamp_and_validate_phase() -> None:
    """The runner applies bounds rules at clamp_and_validate — and ONLY there."""
    program = vtc.compile_vtc_bounds_clamps(
        [
            {"name": "energy", "depletion": {"passive": 0.01}, "bounds": {"min": 0.0, "max": 1.0}},
        ]
    )
    runner = VTCTransitionRunner(_empty_schedule_with_bounds(program))
    context = VTCTransitionContext(
        vfs_state={},
        bars_state={"energy": torch.tensor([1.7, -0.3], dtype=torch.float32)},
        active_mask=torch.tensor([True, False]),
        device=torch.device("cpu"),
    )

    # A phase the rules are not scheduled for leaves the out-of-bounds value alone.
    untouched = runner.run_phase("apply_passive_depletion", context)
    assert untouched.bars_state["energy"].tolist() == pytest.approx([1.7, -0.3])

    clamped = runner.run_phase("clamp_and_validate", context)
    # Bounds are invariants: they apply to every agent, active or not.
    assert clamped.bars_state["energy"].tolist() == [1.0, 0.0]
