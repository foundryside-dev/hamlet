"""Tests for VTC social residue rule compilation and execution."""

import pytest
import torch

from townlet.vfs import compile_vtc_social_residue_rules


def test_vtc_social_residue_compiles_visibility_social_and_institutional_kinds() -> None:
    program = compile_vtc_social_residue_rules(
        [
            {
                "id": "seen_stealing_damages_trust",
                "phase": "apply_social_residue_effects",
                "kind": "visibility_effect",
                "reads": ["chosen_action", "observer_mask", "trust"],
                "condition": "observer_mask and chosen_action == 7",
                "writes": [
                    {
                        "variable_id": "trust",
                        "effect": "trust_delta",
                        "expression": "-0.15",
                        "composition": "additive_delta",
                        "clamp": (0.0, 1.0),
                    }
                ],
            },
            {
                "id": "help_creates_obligation",
                "phase": "apply_social_residue_effects",
                "kind": "social_residue",
                "reads": ["chosen_action", "recipient_actor_mask", "obligation"],
                "condition": "chosen_action == 4",
                "writes": [
                    {
                        "variable_id": "obligation",
                        "effect": "obligation_create",
                        "condition": "recipient_actor_mask",
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
    assert [rule.effect for rule in program.rules] == ["trust_delta", "obligation_create", "reputation_delta"]
    assert {rule.phase for rule in program.rules} == {"apply_social_residue_effects"}
    assert program.rules[0].reads == ("chosen_action", "observer_mask", "trust")


def test_vtc_social_residue_rejects_removed_target_field() -> None:
    with pytest.raises(ValueError, match="'target' was removed"):
        compile_vtc_social_residue_rules(
            [
                {
                    "id": "seen_stealing_damages_trust",
                    "phase": "apply_social_residue_effects",
                    "kind": "visibility_effect",
                    "reads": ["chosen_action", "observer_mask", "trust"],
                    "condition": "observer_mask and chosen_action == 7",
                    "writes": [
                        {
                            "variable_id": "trust",
                            "effect": "trust_delta",
                            "scope": "pair",
                            "target": "observer -> actor",
                            "expression": "-0.15",
                            "composition": "additive_delta",
                            "clamp": (0.0, 1.0),
                        }
                    ],
                }
            ]
        )


def test_vtc_directed_pair_write_moves_trust_ij_without_trust_ji() -> None:
    """Directionality is carried by condition data: trust[i, j] moves while trust[j, i] does not."""
    program = compile_vtc_social_residue_rules(
        [
            {
                "id": "seen_stealing_damages_trust",
                "phase": "apply_social_residue_effects",
                "kind": "visibility_effect",
                "reads": ["chosen_action", "observer_mask", "trust"],
                "condition": "observer_mask and chosen_action == 7",
                "writes": [
                    {
                        "variable_id": "trust",
                        "effect": "trust_delta",
                        "scope": "pair",
                        "expression": "-0.15",
                        "composition": "additive_delta",
                        "clamp": (0.0, 1.0),
                    }
                ],
            }
        ]
    )

    updated = program.apply(
        vfs_state={
            "trust": torch.full((2, 2), 0.8),
            "observer_mask": torch.tensor(
                [
                    [False, True],
                    [False, False],
                ]
            ),
            "chosen_action": torch.tensor([0, 7]),
        },
        active_mask=torch.tensor([True, True]),
        device=torch.device("cpu"),
    )

    assert updated["trust"][0, 1].item() == pytest.approx(0.65)
    assert updated["trust"][1, 0].item() == pytest.approx(0.8)


def test_vtc_visibility_effect_updates_directed_pair_state_for_observed_actor_actions() -> None:
    program = compile_vtc_social_residue_rules(
        [
            {
                "id": "seen_stealing_damages_trust",
                "phase": "apply_social_residue_effects",
                "kind": "visibility_effect",
                "reads": ["chosen_action", "observer_mask", "trust"],
                "condition": "observer_mask and chosen_action == 7",
                "writes": [
                    {
                        "variable_id": "trust",
                        "effect": "trust_delta",
                        "expression": "-0.15",
                        "composition": "additive_delta",
                        "clamp": (0.0, 1.0),
                    }
                ],
            }
        ]
    )

    updated = program.apply(
        vfs_state={
            "trust": torch.full((3, 3), 0.8),
            "observer_mask": torch.tensor(
                [
                    [False, True, False],
                    [False, False, False],
                    [False, True, False],
                ]
            ),
            "chosen_action": torch.tensor([0, 7, 0]),
        },
        active_mask=torch.tensor([True, True, False]),
        device=torch.device("cpu"),
    )

    expected = torch.full((3, 3), 0.8)
    expected[0, 1] = 0.65
    assert torch.allclose(updated["trust"], expected)


def test_vtc_social_and_institutional_residue_updates_pair_and_agent_variables() -> None:
    program = compile_vtc_social_residue_rules(
        [
            {
                "id": "help_creates_obligation_and_reputation",
                "phase": "apply_social_residue_effects",
                "kind": "social_residue",
                "reads": ["chosen_action", "recipient_actor_mask", "was_observed", "obligation", "public_reputation"],
                "condition": "chosen_action == 4",
                "writes": [
                    {
                        "variable_id": "obligation",
                        "effect": "obligation_create",
                        "condition": "recipient_actor_mask",
                        "expression": "0.20",
                        "composition": "additive_delta",
                        "clamp": (0.0, 1.0),
                    },
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
            "obligation": torch.zeros((3, 3)),
            "public_reputation": torch.tensor([0.5, 0.5, 0.5]),
            "recipient_actor_mask": torch.tensor(
                [
                    [False, False, False],
                    [True, False, False],
                    [False, False, False],
                ]
            ),
            "was_observed": torch.tensor([True, False, False]),
            "chosen_action": torch.tensor([4, 9, 0]),
        },
        active_mask=torch.tensor([True, True, True]),
        device=torch.device("cpu"),
    )

    expected_obligation = torch.zeros((3, 3))
    expected_obligation[1, 0] = 0.2
    assert torch.allclose(updated["obligation"], expected_obligation)
    assert torch.allclose(updated["public_reputation"], torch.tensor([0.55, 0.4, 0.5]))
