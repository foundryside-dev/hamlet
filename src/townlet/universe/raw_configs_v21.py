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
from townlet.config.vfs_profiles_config import VFSProfilesConfig
from townlet.universe.error_codes import ErrorCode
from townlet.universe.source_map import SourceMap
from townlet.vfs.schema import VariableDef, VFSScopeExtents, parse_variables_reference

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

    # Curriculum levels (per-level parameters)
    levels: dict[str, CurriculumLevel]

    # Provenance
    experiment_dir: Path
    source_map: SourceMap | None = None

    # Optional experiment-level configs
    items: ItemsCatalogConfig | None = None
    vfs_profiles: VFSProfilesConfig | None = None
    effects: EffectsConfig | None = None
    action_label_overrides: dict[int, str] | None = None
    variables_reference: tuple[VariableDef, ...] | None = None
    vfs_extents: VFSScopeExtents | None = None
    social_residue_rules: tuple[dict[str, object], ...] = ()

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
        vfs_profiles = store.parse("vfs_profiles", None, VFSProfilesConfig, False)
        effects = store.parse("effects", None, EffectsConfig, False)
        transition_rules = store.parse("transition_rules", None, TransitionRulesConfig, False)
        store.parse("presentation", None, PresentationConfig, False)

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

        variables_reference = None
        vfs_extents = None
        reference = store.get("variables_reference", None)
        if reference is not None:
            try:
                reference_data = parse_variables_reference(reference.payload, reference.origin)
                variables_reference = reference_data.variables
                vfs_extents = reference_data.extents
            except ValueError as exc:
                store.errors.add(str(exc), code=ErrorCode.LOAD_ERROR, location=reference.origin)

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
        assert actions is not None and brain is not None and vfs_profiles is not None
        if items is not None and (items.max_items_in_world == 0 or items.max_items_per_agent == 0):
            items = None
        return cls(
            experiment=experiment,
            stratum=stratum,
            environment=environment,
            actions=actions,
            brain=brain,
            items=items,
            vfs_profiles=vfs_profiles,
            effects=effects,
            action_label_overrides=action_label_overrides,
            variables_reference=variables_reference,
            vfs_extents=vfs_extents,
            social_residue_rules=transition_rules.social_residue_sources() if transition_rules is not None else (),
            levels=levels,
            experiment_dir=store.experiment_dir,
            source_map=store.source_map,
        )
