"""`interaction_type` has ONE closed vocabulary and no hidden default (PDR-0047, hamlet-45b35cfee5).

Before this: the authoring DTO permitted `instant | multi_tick | dual` with `default=None` and a
description that said "defaults to 'instant' at runtime" out loud; a dead runtime module also
admitted `continuous`, which the VTC rejects and nothing implements. Two vocabularies, one field,
and a behavioural parameter defaulted in code.
"""

from __future__ import annotations

import importlib
from typing import get_args

import pytest
from pydantic import ValidationError

from townlet.config.affordances_v2_config import AffordanceParamConfig, DeploymentConfig, OpeningHoursConfig
from townlet.config.interaction_type import INTERACTION_TYPES, PROGRESS_INTERACTION_TYPES, InteractionType


def _payload(**overrides):
    base = dict(
        name="TEST_AFFORDANCE",
        interaction_type="instant",
        costs={},
        interactions={"on_start": [], "per_tick": [], "on_completion": [], "on_early_exit": [], "on_failure": []},
        opening_hours=OpeningHoursConfig(enabled=False),
        deployment=DeploymentConfig(type="random"),
    )
    base.update(overrides)
    return base


class TestOneClosedVocabulary:
    def test_the_vocabulary_is_exactly_instant_and_multi_tick(self) -> None:
        assert INTERACTION_TYPES == frozenset({"instant", "multi_tick"})
        assert frozenset(get_args(InteractionType)) == INTERACTION_TYPES
        assert PROGRESS_INTERACTION_TYPES < INTERACTION_TYPES

    def test_the_authoring_dto_references_the_one_vocabulary(self) -> None:
        annotation = AffordanceParamConfig.model_fields["interaction_type"].annotation
        assert frozenset(get_args(annotation)) == INTERACTION_TYPES

    def test_continuous_was_never_real_and_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="interaction_type"):
            AffordanceParamConfig(**_payload(interaction_type="continuous"))

    def test_dual_has_no_distinct_runtime_behavior_and_is_rejected(self) -> None:
        with pytest.raises(ValidationError, match="interaction_type"):
            AffordanceParamConfig(**_payload(interaction_type="dual", duration_ticks=2))

    def test_the_second_vocabulary_module_is_gone(self) -> None:
        # `townlet.environment.affordance_config` had zero importers and admitted `continuous`.
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("townlet.environment.affordance_config")


class TestNoHiddenDefault:
    def test_interaction_type_is_required(self) -> None:
        payload = _payload()
        del payload["interaction_type"]
        with pytest.raises(ValidationError, match="interaction_type"):
            AffordanceParamConfig(**payload)

    def test_progress_types_still_require_duration_ticks(self) -> None:
        with pytest.raises(ValidationError, match="duration_ticks"):
            AffordanceParamConfig(**_payload(interaction_type="multi_tick"))
        AffordanceParamConfig(**_payload(interaction_type="multi_tick", duration_ticks=3))

    def test_instant_still_rejects_duration_ticks(self) -> None:
        with pytest.raises(ValidationError, match="duration_ticks"):
            AffordanceParamConfig(**_payload(interaction_type="instant", duration_ticks=3))
