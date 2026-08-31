"""Regression coverage for pre-release removal of legacy runtime APIs."""

from types import SimpleNamespace

import pytest
import torch

from townlet.config.actions_config import (
    ActionLabelsConfig,
    ActionsConfig,
    ActionsConfigRoot,
    SubstrateActionsConfig,
)
from townlet.config.stratum_config import AspatialConfig, SubstrateConfig
from townlet.curriculum.adversarial import AdversarialCurriculum
from townlet.curriculum.static import StaticCurriculum
from townlet.environment import action_builder, action_config
from townlet.environment.dac_engine import DACEngine
from townlet.environment.substrate_action_validator import SubstrateActionValidator
from townlet.universe.errors import CompilationErrorCollector
from townlet.universe.symbol_table import UniverseSymbolTable
from townlet.universe.validation.references import validate_dac_references


def test_legacy_global_actions_apis_are_deleted() -> None:
    assert not hasattr(action_builder, "ActionSpaceBuilder")
    assert not hasattr(action_config, "ActionSpaceConfig")
    assert not hasattr(action_config, "load_global_actions_config")


def test_substrate_validator_accepts_only_canonical_actions_wrapper() -> None:
    substrate = SubstrateConfig(type="aspatial", aspatial=AspatialConfig())
    root = ActionsConfigRoot(
        version="2.1",
        substrate_actions=SubstrateActionsConfig(inherit=True),
        custom_actions=[],
        labels=ActionLabelsConfig(preset="gaming"),
    )
    actions = ActionsConfig(actions=root)

    SubstrateActionValidator(substrate, actions)
    with pytest.raises(TypeError, match="ActionsConfig"):
        SubstrateActionValidator(substrate, root)  # type: ignore[arg-type]


def _uninitialized_dac_engine() -> DACEngine:
    engine = object.__new__(DACEngine)
    engine.device = torch.device("cpu")
    engine.num_agents = 1
    return engine


@pytest.mark.parametrize(
    "legacy_bonus",
    [
        SimpleNamespace(type="approach_reward", target="BED", weight=1.0, max_distance=1.0),
        SimpleNamespace(type="completion_bonus", affordance="BED", bonus=1.0),
    ],
)
def test_dac_shaping_refuses_removed_reward_field_aliases(legacy_bonus: SimpleNamespace) -> None:
    engine = _uninitialized_dac_engine()
    engine.dac_config = SimpleNamespace(shaping=[legacy_bonus])  # type: ignore[assignment]

    with pytest.raises(AttributeError):
        engine._compile_shaping()


def test_dac_reference_validation_refuses_removed_target_alias() -> None:
    config = SimpleNamespace(
        modifiers={},
        extrinsic=SimpleNamespace(bars=[], bar_bonuses=[], variable_bonuses=[]),
        shaping=[SimpleNamespace(type="approach_reward", target="MISSING")],
    )

    with pytest.raises(AttributeError):
        validate_dac_references(  # type: ignore[arg-type]
            config,
            UniverseSymbolTable(),
            CompilationErrorCollector(),
            drive_location="drive.yaml",
        )


def test_unimplemented_extrinsic_strategy_fails_loudly() -> None:
    engine = _uninitialized_dac_engine()
    engine.dac_config = SimpleNamespace(extrinsic=SimpleNamespace(type="removed_strategy"))  # type: ignore[assignment]

    with pytest.raises(ValueError, match="Unsupported extrinsic strategy.*removed_strategy"):
        engine._compile_extrinsic()


def test_dead_error_collector_alias_is_deleted() -> None:
    assert not hasattr(CompilationErrorCollector, "add_error")


@pytest.mark.parametrize("curriculum_type", [StaticCurriculum, AdversarialCurriculum])
def test_curriculum_exposes_only_canonical_checkpoint_api(curriculum_type: type[object]) -> None:
    assert not hasattr(curriculum_type, "state_dict")
    assert not hasattr(curriculum_type, "load_state_dict")
    assert not hasattr(curriculum_type, "load_checkpoint_state")
