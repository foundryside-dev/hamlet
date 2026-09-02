"""Tests for multi-tick interaction progress compiled as VTC transition rules."""

from __future__ import annotations

import torch

from townlet.vfs import vtc


def _affordance(name: str, *, interaction_type: str, duration_ticks: int | None) -> dict[str, object]:
    return {
        "name": name,
        "interaction_type": interaction_type,
        "duration_ticks": duration_ticks,
    }


def test_compile_vtc_interaction_progress_emits_progress_and_completion_rules() -> None:
    program = vtc.compile_vtc_interaction_progress(
        [
            _affordance("Job", interaction_type="multi_tick", duration_ticks=4),
            _affordance("Park", interaction_type="instant", duration_ticks=None),
        ]
    )

    assert len(program.progress_rules) == 1
    progress_rule = program.progress_rules[0]
    assert progress_rule.rule_id == "job_advance_interaction_progress"
    assert progress_rule.kind == "interaction_progress"
    assert progress_rule.source_variable_id == "interaction_progress"
    assert progress_rule.target_affordance_id == "Job"
    assert progress_rule.variable_id == "interaction_progress"
    assert progress_rule.expression == ("where(same_affordance and affordance_is_open and chosen_interact, interaction_progress + 1, 0)")
    assert progress_rule.phase == "advance_interaction_progress"
    assert progress_rule.composition == "overwrite"
    assert progress_rule.duration_ticks == 4
    assert progress_rule.telemetry_label == "interaction_progress:Job"

    assert len(program.completion_bonus_rules) == 1
    completion_rule = program.completion_bonus_rules[0]
    assert completion_rule.rule_id == "job_completion_bonus"
    assert completion_rule.kind == "interaction_completion_bonus"
    assert completion_rule.source_variable_id == "interaction_progress"
    assert completion_rule.target_affordance_id == "Job"
    assert completion_rule.variable_id == "affordance.Job.completed"
    assert completion_rule.expression == "interaction_progress >= 4"
    assert completion_rule.phase == "apply_completion_bonuses"
    assert completion_rule.composition == "event"
    assert completion_rule.duration_ticks == 4
    assert completion_rule.telemetry_label == "interaction_completion_bonus:Job"


def test_vtc_interaction_progress_tracks_continuation_completion_and_disengagement() -> None:
    program = vtc.compile_vtc_interaction_progress(
        [
            _affordance("Bed", interaction_type="multi_tick", duration_ticks=5),
            _affordance("Job", interaction_type="multi_tick", duration_ticks=4),
        ]
    )

    result = program.apply(
        interaction_affordances={0: "Job", 1: "Job", 2: "Bed"},
        positions=torch.tensor([[1, 1], [2, 2], [3, 3]]),
        interaction_progress=torch.tensor([0, 3, 2]),
        last_affordances=[None, "Job", "Bed"],
        last_positions=torch.tensor([[0, 0], [2, 2], [3, 3]]),
        active_mask=torch.tensor([True, True, True]),
        device=torch.device("cpu"),
    )

    assert torch.equal(result.ticks_done, torch.tensor([1, 4, 3]))
    assert torch.equal(result.interaction_progress, torch.tensor([1, 0, 3]))
    assert torch.equal(result.completion_mask, torch.tensor([False, True, False]))
    assert result.completion_affordances == [None, "Job", None]
    assert result.last_affordances == ["Job", None, "Bed"]
    assert torch.equal(result.last_positions, torch.tensor([[1, 1], [2, 2], [3, 3]]))

    disengaged = program.apply(
        interaction_affordances={0: "Job"},
        positions=torch.tensor([[1, 1], [2, 2]]),
        interaction_progress=torch.tensor([1, 2]),
        last_affordances=["Job", "Job"],
        last_positions=torch.tensor([[1, 1], [2, 2]]),
        active_mask=torch.tensor([True, True]),
        device=torch.device("cpu"),
    )

    assert torch.equal(disengaged.ticks_done, torch.tensor([2, 0]))
    assert torch.equal(disengaged.interaction_progress, torch.tensor([2, 0]))
    assert disengaged.last_affordances == ["Job", None]
