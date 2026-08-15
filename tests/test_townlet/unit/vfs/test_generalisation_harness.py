"""Tests for held-out VFS generalisation experiment harnesses."""

import pytest

from townlet.vfs import VFSGeneralisationPack, assert_held_out_generalisation_split, operator_grammar_signature


def _variable(name: str, source_bar: str) -> dict[str, object]:
    return {
        "name": name,
        "scope": "agent",
        "type": "float",
        "semantic_type": "custom",
        "expression": f"bar.{source_bar} + 0.1",
    }


def _affordance(name: str, source_bar: str, target_bar: str, delta: float) -> dict[str, object]:
    return {
        "name": name,
        "interaction_type": "instant",
        "costs": {source_bar: 0.05},
        "opening_hours": {"enabled": False, "schedule": []},
        "deployment": {"type": "fixed", "positions": [[1, 1]]},
        "interactions": {
            "on_start": [
                {
                    "modify": f"target.bar.{target_bar}",
                    "value": f"target.bar.{target_bar} + {delta}",
                }
            ],
            "per_tick": [],
            "on_completion": [],
            "on_early_exit": [],
            "on_failure": [],
        },
    }


def test_held_out_generalisation_split_accepts_surface_label_swaps_with_shared_causal_profiles() -> None:
    train = VFSGeneralisationPack(
        variables=(
            _variable("need_alpha", "energy"),
            _variable("need_beta", "mood"),
        ),
        affordances=(
            _affordance("FORAGE", "energy", "satiation", 0.4),
            _affordance("RESTORE", "mood", "energy", 0.2),
        ),
        rules=(
            {
                "kind": "modulation",
                "source_variable_id": "energy",
                "target_affordance_id": "FORAGE",
                "variable_id": "affordance.FORAGE.multiplier",
                "expression": "where(bar.energy < 0.3, 0.5 + 0.5 * (bar.energy / 0.3), 1.0)",
                "composition": "multiplicative_modifier",
                "phase": "apply_modulations",
            },
        ),
    )
    test = VFSGeneralisationPack(
        variables=(
            _variable("need_gamma", "vitality"),
            _variable("need_delta", "spirit"),
        ),
        affordances=(
            _affordance("GRAZE", "vitality", "nourishment", 0.4),
            _affordance("RECUPERATE", "spirit", "vitality", 0.2),
        ),
        rules=(
            {
                "kind": "modulation",
                "source_variable_id": "vitality",
                "target_affordance_id": "GRAZE",
                "variable_id": "affordance.GRAZE.multiplier",
                "expression": "where(bar.vitality < 0.3, 0.5 + 0.5 * (bar.vitality / 0.3), 1.0)",
                "composition": "multiplicative_modifier",
                "phase": "apply_modulations",
            },
        ),
    )

    report = assert_held_out_generalisation_split(train, test)

    assert report.held_out_variable_names == ("need_gamma", "need_delta")
    assert report.held_out_affordance_labels == ("GRAZE", "RECUPERATE")
    assert report.variable_profile_count == 2
    assert report.affordance_profile_count == 2
    assert report.rule_profile_count == 1
    assert report.shared_operator_grammar


def test_held_out_generalisation_split_rejects_reused_variable_or_affordance_labels() -> None:
    train = VFSGeneralisationPack(
        variables=(_variable("need_alpha", "energy"),),
        affordances=(_affordance("FORAGE", "energy", "satiation", 0.4),),
    )
    test = VFSGeneralisationPack(
        variables=(_variable("need_alpha", "vitality"),),
        affordances=(_affordance("GRAZE", "vitality", "nourishment", 0.4),),
    )

    with pytest.raises(ValueError, match="held-out variable names overlap"):
        assert_held_out_generalisation_split(train, test)

    test = VFSGeneralisationPack(
        variables=(_variable("need_gamma", "vitality"),),
        affordances=(_affordance("FORAGE", "vitality", "nourishment", 0.4),),
    )

    with pytest.raises(ValueError, match="held-out affordance labels overlap"):
        assert_held_out_generalisation_split(train, test)


def test_held_out_generalisation_split_rejects_causal_profile_drift() -> None:
    train = VFSGeneralisationPack(
        variables=(_variable("need_alpha", "energy"),),
        affordances=(_affordance("FORAGE", "energy", "satiation", 0.4),),
    )
    test = VFSGeneralisationPack(
        variables=(_variable("need_gamma", "vitality"),),
        affordances=(_affordance("GRAZE", "vitality", "nourishment", 0.7),),
    )

    with pytest.raises(ValueError, match="causal profiles differ"):
        assert_held_out_generalisation_split(train, test)


def test_operator_grammar_signature_erases_surface_names_but_keeps_operations() -> None:
    assert operator_grammar_signature("where(bar.energy < 0.3, bar.energy + 0.2, 1.0)") == operator_grammar_signature(
        "where(bar.vitality < 0.9, bar.vitality + 0.7, 5.0)"
    )
    assert operator_grammar_signature("bar.energy + 0.2") != operator_grammar_signature("bar.vitality * 0.2")
