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
    "trust": _target(VariableScope.PAIR),
    "obligation": _target(VariableScope.PAIR),
    "public_reputation": _target(VariableScope.AGENT),
    "pressure": _target(VariableScope.GLOBAL),
    "wear": _target(VariableScope.AFFORDANCE),
    "chosen_action": _target(VariableScope.AGENT),
    "observer_mask": _target(VariableScope.PAIR, "bool"),
    "recipient_actor_mask": _target(VariableScope.PAIR, "bool"),
    "was_observed": _target(VariableScope.AGENT, "bool"),
}


def _compile(rules: list[dict]) -> VTCSocialResidueProgram:
    return compile_vtc_social_residue_rules(rules, TARGET_SCOPES)


def test_vtc_social_residue_compiles_visibility_social_and_institutional_kinds() -> None:
    program = _compile(
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


def test_vtc_directed_pair_write_moves_trust_ij_without_trust_ji() -> None:
    """Directionality is carried by condition data: trust[i, j] moves while trust[j, i] does not."""
    program = _compile(
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
    ).values

    assert updated["trust"][0, 1].item() == pytest.approx(0.65)
    assert updated["trust"][1, 0].item() == pytest.approx(0.8)


def test_vtc_visibility_effect_updates_directed_pair_state_for_observed_actor_actions() -> None:
    program = _compile(
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
    ).values

    expected = torch.full((3, 3), 0.8)
    expected[0, 1] = 0.65
    assert torch.allclose(updated["trust"], expected)


def test_vtc_social_and_institutional_residue_updates_pair_and_agent_variables() -> None:
    program = _compile(
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
    ).values

    expected_obligation = torch.zeros((3, 3))
    expected_obligation[1, 0] = 0.2
    assert torch.allclose(updated["obligation"], expected_obligation)
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


def test_global_target_is_masked_by_declared_scope_not_by_storage_shape() -> None:
    """A global tensor whose extent happens to equal num_agents is still global state: with one
    agent done it is written whole. The shape[0] == num_agents guess masked it per agent."""
    program = _compile([_rule("pressure")])
    (rule,) = program.rules
    assert rule.target_scope == VariableScope.GLOBAL

    updated = program.apply(
        vfs_state={"pressure": torch.zeros(2)},
        active_mask=torch.tensor([True, False]),
        device=torch.device("cpu"),
    ).values

    assert updated["pressure"].tolist() == [1.0, 1.0]


def test_affordance_target_is_not_masked_per_agent() -> None:
    """Affordance rows are not agent rows, even when there are as many affordances as agents."""
    program = _compile([_rule("wear")])
    updated = program.apply(
        vfs_state={"wear": torch.zeros(2)},
        active_mask=torch.tensor([False, True]),
        device=torch.device("cpu"),
    ).values

    assert updated["wear"].tolist() == [1.0, 1.0]


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
