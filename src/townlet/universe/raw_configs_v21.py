"""Raw config loader for Config v2.1 hierarchical structure."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, StrictInt

from townlet.config.actions_config import ActionsConfig
from townlet.config.affordances_v2_config import AffordancesV2Config
from townlet.config.bars_v2_config import BarsV2Config
from townlet.config.brain_config import BrainConfig
from townlet.config.curriculum_config import CurriculumConfig
from townlet.config.drive_as_code import DriveAsCodeConfig
from townlet.config.effects_config import EffectsConfig
from townlet.config.environment_config import EnvironmentConfig
from townlet.config.experiment_config import ExperimentConfig
from townlet.config.items_config import ItemsAppearanceConfig, ItemsCatalogConfig
from townlet.config.presentation_config import PresentationConfig
from townlet.config.stratum_config import StratumConfig
from townlet.config.training_v2_config import TrainingV2Config
from townlet.config.transition_rules_config import TransitionRulesConfig
from townlet.config.variables_config import VariablesConfig
from townlet.universe.error_codes import ErrorCode
from townlet.universe.source_map import SourceMap

if TYPE_CHECKING:
    from townlet.universe.declarations import DeclarationStore


class CustomActionLabels(BaseModel):
    """Explicit observer labels keyed by compiled action identifier."""

    model_config = ConfigDict(extra="forbid")
    custom: dict[StrictInt, str]


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CurriculumLevel:
    """All curriculum-level configs for a single level."""

    name: str
    curriculum: CurriculumConfig
    bars: BarsV2Config
    affordances: AffordancesV2Config
    drive: DriveAsCodeConfig
    training: TrainingV2Config
    # Optional COMPLETE per-level brain.yaml (PDR-0027). None = inherit the pack brain
    # unchanged. Never a partial patch: partial merges need default semantics, which the
    # No-Defaults Principle forbids.
    brain: BrainConfig | None = None
    items_appearance: ItemsAppearanceConfig | None = None

    @property
    def level_dir(self) -> str:
        """Directory name for this level."""
        return self.name


@dataclass(frozen=True)
class RawConfigsV21:
    """Container for all v2.1 hierarchical config DTOs."""

    # Experiment-level configs (shared vocabulary and metadata)
    experiment: ExperimentConfig
    stratum: StratumConfig
    environment: EnvironmentConfig
    actions: ActionsConfig
    brain: BrainConfig
    variables: VariablesConfig

    # Curriculum levels (per-level parameters)
    levels: dict[str, CurriculumLevel]

    # Provenance
    experiment_dir: Path
    source_map: SourceMap | None = None

    # Optional experiment-level configs
    items: ItemsCatalogConfig | None = None
    effects: EffectsConfig | None = None
    # Observer-only presentation (PDR-0025): carried on the artifact, validated in resolve,
    # never hashed.
    presentation: PresentationConfig | None = None
    action_label_overrides: dict[int, str] | None = None
    transition_rules: tuple[dict[str, object], ...] = ()

    def __post_init__(self) -> None:
        """Validate local DTO construction invariants."""
        if not self.levels:
            raise ValueError(f"No curriculum levels found in {self.experiment_dir}")

    @classmethod
    def from_experiment_dir(cls, experiment_dir: Path) -> RawConfigsV21:
        """Discover authored declarations independently of transport filenames."""
        from townlet.universe.declarations import DeclarationStore

        return cls.from_declarations(DeclarationStore.discover(experiment_dir))

    @classmethod
    def from_declarations(cls, store: DeclarationStore) -> RawConfigsV21:
        """Lower one validated declaration store into the existing typed products."""
        store.resolve_clock_references()
        experiment = store.parse("experiment", None, ExperimentConfig, True)
        stratum = store.parse("stratum", None, StratumConfig, True)
        environment = store.parse("environment", None, EnvironmentConfig, True)
        actions = store.parse("actions", None, ActionsConfig, True)
        brain = store.parse("brain", None, BrainConfig, False)
        items = store.parse("items", None, ItemsCatalogConfig, False)
        variables = store.parse("variables", None, VariablesConfig, False)
        effects = store.parse("effects", None, EffectsConfig, False)
        transition_rules = store.parse("transition_rules", None, TransitionRulesConfig, False)
        presentation = store.parse("presentation", None, PresentationConfig, False)

        labels_declaration = store.get("action_labels", None)
        action_label_overrides = None
        if labels_declaration is not None:
            custom = labels_declaration.payload.get("custom")
            if isinstance(custom, dict):
                identifiers: dict[int, object] = {}
                for key in custom:
                    try:
                        identifier = int(key)
                    except (ValueError, TypeError):
                        continue
                    if identifier in identifiers:
                        prior = identifiers[identifier]
                        lines = getattr(custom, "key_lines", {})
                        first = f"{labels_declaration.path}:{lines.get(prior, labels_declaration.line)}"
                        second = f"{labels_declaration.path}:{lines.get(key, labels_declaration.line)}"
                        store.errors.add(
                            f"Action label identifier {identifier} is declared twice; first declared at {first}",
                            code=ErrorCode.DECLARATION_COLLISION,
                            location=second,
                        )
                    identifiers[identifier] = key
            labels = store.parse("action_labels", None, CustomActionLabels, False)
            if labels is not None:
                action_label_overrides = labels.custom

        levels = {}
        for name in store.level_names:
            curriculum = store.parse("curriculum", name, CurriculumConfig, True)
            bars = store.parse("bars", name, BarsV2Config, False)
            affordances = store.parse("affordances", name, AffordancesV2Config, False)
            drive = store.parse("drive", name, DriveAsCodeConfig, False)
            training = store.parse("training", name, TrainingV2Config, False)
            level_brain = store.parse("brain", name, BrainConfig, False)
            appearance = store.parse("items_appearance", name, ItemsAppearanceConfig, False)
            if curriculum is not None and bars is not None and affordances is not None and drive is not None and training is not None:
                levels[name] = CurriculumLevel(
                    name=name,
                    curriculum=curriculum,
                    bars=bars,
                    affordances=affordances,
                    drive=drive,
                    training=training,
                    brain=level_brain,
                    items_appearance=appearance,
                )
        store.errors.check_and_raise()
        assert experiment is not None and stratum is not None and environment is not None
        assert actions is not None and brain is not None and variables is not None
        if items is not None and not items.item_types and items.max_items_in_world == 0 and items.max_items_per_agent == 0:
            # No item types and no arena: the declaration says the pack has no items, which is
            # what an absent declaration says. Item types declared into an empty arena never
            # reach here; `ItemsCatalogConfig.validate_item_arena` refuses them at parse.
            items = None
        return cls(
            experiment=experiment,
            stratum=stratum,
            environment=environment,
            actions=actions,
            brain=brain,
            items=items,
            variables=variables,
            effects=effects,
            presentation=presentation,
            action_label_overrides=action_label_overrides,
            transition_rules=transition_rules.rule_sources() if transition_rules is not None else (),
            levels=levels,
            experiment_dir=store.experiment_dir,
            source_map=store.source_map,
        )
