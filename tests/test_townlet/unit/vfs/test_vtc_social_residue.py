"""Tests for VTC social residue rule compilation and execution."""

import pytest
import torch

from townlet.vfs import compile_vtc_social_residue_rules
from townlet.vfs.schema import VariableScope
from townlet.vfs.vtc import VTCSocialResidueProgram, VTCWriteRefusalError, VTCWriteTarget


def _target(scope: VariableScope, var_type: str = "scalar") -> VTCWriteTarget:
    return VTCWriteTarget(scope, var_type, meter=False)


#: Declared scope and type of every state these rules write or read.
TARGET_SCOPES = {
    "public_reputation": _target(VariableScope.AGENT),
    "pressure": _target(VariableScope.GLOBAL),
    "wear": _target(VariableScope.AFFORDANCE),
    "chosen_action": _target(VariableScope.AGENT),
    "was_observed": _target(VariableScope.AGENT, "bool"),
}


def _compile(rules: list[dict]) -> VTCSocialResidueProgram:
    return compile_vtc_social_residue_rules(rules, TARGET_SCOPES)


def test_vtc_social_residue_compiles_visibility_social_and_institutional_kinds() -> None:
    program = _compile(
        [
            {
                "id": "seen_stealing_damages_reputation",
                "phase": "apply_social_residue_effects",
                "kind": "visibility_effect",
                "reads": ["chosen_action", "was_observed", "public_reputation"],
                "condition": "was_observed and chosen_action == 7",
                "writes": [
                    {
                        "variable_id": "public_reputation",
                        "effect": "seen_delta",
                        "expression": "-0.15",
                        "composition": "additive_delta",
                        "clamp": (0.0, 1.0),
                    }
                ],
            },
            {
                "id": "working_wears_affordances",
                "phase": "apply_social_residue_effects",
                "kind": "social_residue",
                "reads": ["wear"],
                "condition": None,
                "writes": [
                    {
                        "variable_id": "wear",
                        "effect": "wear_delta",
                        "condition": None,
                        "expression": "0.20",
                        "composition": "additive_delta",
                        "clamp": (0.0, 1.0),
                    }
                ],
            },
            {
                "id": "ambulance_abuse_social_penalty",
                "phase": "apply_social_residue_effects",
                "kind": "institutional_rule",
                "reads": ["chosen_action", "public_reputation"],
                "condition": "chosen_action == 9",
                "writes": [
                    {
                        "variable_id": "public_reputation",
                        "effect": "reputation_delta",
                        "expression": "-0.10",
                        "composition": "additive_delta",
                        "clamp": (0.0, 1.0),
                    }
                ],
            },
        ]
    )

    assert [rule.kind for rule in program.rules] == ["visibility_effect", "social_residue", "institutional_rule"]
    assert [rule.effect for rule in program.rules] == ["seen_delta", "wear_delta", "reputation_delta"]
    assert {rule.phase for rule in program.rules} == {"apply_social_residue_effects"}
    assert program.rules[0].reads == ("chosen_action", "was_observed", "public_reputation")


def test_vtc_social_and_institutional_residue_updates_agent_variables() -> None:
    program = _compile(
        [
            {
                "id": "observed_help_raises_reputation",
                "phase": "apply_social_residue_effects",
                "kind": "social_residue",
                "reads": ["chosen_action", "was_observed", "public_reputation"],
                "condition": "chosen_action == 4",
                "writes": [
                    {
                        "variable_id": "public_reputation",
                        "effect": "reputation_delta",
                        "condition": "was_observed",
                        "expression": "0.05",
                        "composition": "additive_delta",
                        "clamp": (0.0, 1.0),
                    },
                ],
            },
            {
                "id": "ambulance_abuse_social_penalty",
                "phase": "apply_social_residue_effects",
                "kind": "institutional_rule",
                "reads": ["chosen_action", "public_reputation"],
                "condition": "chosen_action == 9",
                "writes": [
                    {
                        "variable_id": "public_reputation",
                        "effect": "reputation_delta",
                        "expression": "-0.10",
                        "composition": "additive_delta",
                        "clamp": (0.0, 1.0),
                    }
                ],
            },
        ]
    )

    updated = program.apply(
        vfs_state={
            "public_reputation": torch.tensor([0.5, 0.5, 0.5]),
            "was_observed": torch.tensor([True, False, False]),
            "chosen_action": torch.tensor([4, 9, 0]),
        },
        active_mask=torch.tensor([True, True, True]),
        device=torch.device("cpu"),
    ).values

    assert torch.allclose(updated["public_reputation"], torch.tensor([0.55, 0.4, 0.5]))


def _rule(variable_id: str, *, expression: str = "1.0", composition: str = "additive_delta") -> dict:
    return {
        "id": f"bump_{variable_id}",
        "phase": "apply_social_residue_effects",
        "kind": "social_residue",
        "reads": [variable_id],
        "condition": None,
        "writes": [{"variable_id": variable_id, "expression": expression, "composition": composition}],
    }


def test_global_target_advances_only_in_worlds_whose_agent_is_active() -> None:
    """A global has one row per world (S1): its rule advances each world by that world's own
    agent's activity, so a done agent's world holds while the other world moves on."""
    program = _compile([_rule("pressure")])
    (rule,) = program.rules
    assert rule.target_scope == VariableScope.GLOBAL

    updated = program.apply(
        vfs_state={"pressure": torch.zeros(2)},
        active_mask=torch.tensor([True, False]),
        device=torch.device("cpu"),
    ).values

    assert updated["pressure"].tolist() == [1.0, 0.0]


def test_affordance_target_rows_are_masked_by_their_own_worlds_agent() -> None:
    """Affordance state is per world (S1): a done world's affordance rows are frozen, a live world's advance."""
    program = _compile([_rule("wear")])
    updated = program.apply(
        vfs_state={"wear": torch.zeros(2, 3)},
        active_mask=torch.tensor([False, True]),
        device=torch.device("cpu"),
    ).values

    assert updated["wear"].tolist() == [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]


def test_agent_target_masks_the_done_agent_row() -> None:
    program = _compile([_rule("public_reputation")])
    updated = program.apply(
        vfs_state={"public_reputation": torch.zeros(3)},
        active_mask=torch.tensor([True, False, True]),
        device=torch.device("cpu"),
    ).values

    assert updated["public_reputation"].tolist() == [1.0, 0.0, 1.0]


def test_agent_target_without_an_agent_axis_is_an_assertion() -> None:
    """Storage that disagrees with the declared scope is a registry defect, not a shape to guess from."""
    program = _compile([_rule("public_reputation")])
    with pytest.raises(AssertionError, match="public_reputation"):
        program.apply(
            vfs_state={"public_reputation": torch.zeros(5)},
            active_mask=torch.tensor([True, True]),
            device=torch.device("cpu"),
        )


def test_unknown_target_refuses_at_compile() -> None:
    with pytest.raises(VTCWriteRefusalError, match="targets unknown VFS variable 'missing'"):
        _compile([_rule("missing")])
