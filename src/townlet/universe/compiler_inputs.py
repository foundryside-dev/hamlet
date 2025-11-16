"""Shared helper for collecting compiler input DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

import torch
import yaml

from townlet.config import HamletConfig
from townlet.config.affordance import AffordanceConfig
from townlet.config.bar import BarConfig
from townlet.config.cascade import CascadeConfig
from townlet.config.cues import CompoundCueConfig, CuesConfig, SimpleCueConfig
from townlet.config.curriculum import CurriculumConfig
from townlet.config.environment import TrainingEnvironmentConfig
from townlet.config.exploration import ExplorationConfig
from townlet.config.population import PopulationConfig
from townlet.config.training import TrainingConfig
from townlet.environment.action_config import ActionConfig, ActionSpaceConfig
from townlet.environment.cascade_config import EnvironmentConfig
from townlet.substrate.config import ActionLabelConfig, SubstrateConfig
from townlet.substrate.factory import SubstrateFactory
from townlet.universe.errors import CompilationErrorCollector
from townlet.universe.source_map import SourceMap
from townlet.vfs.schema import VariableDef

_T = TypeVar("_T")


@dataclass(frozen=True)
class RawConfigs:
    """Container of all config DTOs the compiler needs for Stage 1."""

    hamlet_config: HamletConfig
    variables_reference: list[VariableDef]  # Custom computed variables (can be empty list)
    global_actions: ActionSpaceConfig
    action_labels: ActionLabelConfig | None
    environment_config: EnvironmentConfig
    source_map: SourceMap
    config_dir: Path

    # --- Convenience accessors -------------------------------------------------

    @property
    def training(self) -> TrainingConfig:
        return self.hamlet_config.training

    @property
    def environment(self) -> TrainingEnvironmentConfig:
        return self.hamlet_config.environment

    @property
    def population(self) -> PopulationConfig:
        return self.hamlet_config.population

    @property
    def curriculum(self) -> CurriculumConfig:
        return self.hamlet_config.curriculum

    @property
    def exploration(self) -> ExplorationConfig:
        return self.hamlet_config.exploration

    @property
    def bars(self) -> tuple[BarConfig, ...]:
        return self.hamlet_config.bars

    @property
    def cascades(self) -> tuple[CascadeConfig, ...]:
        return self.hamlet_config.cascades

    @property
    def affordances(self) -> tuple[AffordanceConfig, ...]:
        return self.hamlet_config.affordances

    @property
    def cues(self) -> tuple[SimpleCueConfig | CompoundCueConfig, ...]:
        cues_config: CuesConfig = self.hamlet_config.cues
        combined: list[SimpleCueConfig | CompoundCueConfig] = list(cues_config.simple_cues)
        combined.extend(cues_config.compound_cues)
        return tuple(combined)

    @property
    def substrate(self) -> SubstrateConfig:
        return self.hamlet_config.substrate

    # --- Factory ---------------------------------------------------------------

    @classmethod
    def from_config_dir(cls, config_dir: Path) -> RawConfigs:
        """Legacy flat-config pipeline has been removed in favor of v2.1.

        RawConfigs was the Stage 1 input for the pre-v2.1 HamletConfig-based
        compiler. That pipeline is now deprecated and unsupported. Callers
        should migrate to UniverseCompiler.compile() with hierarchical v2.1
        configs (experiment/stratum/environment/actions/agent/levels/*).
        """
        raise RuntimeError(
            "RawConfigs.from_config_dir is no longer supported. "
            "The legacy flat HamletConfig pipeline has been removed. "
            "Use UniverseCompiler.compile() with v2.1 hierarchical configs instead."
        )

    @staticmethod
    def _compose_action_space(
        *,
        hamlet_config: HamletConfig,
        custom_actions: ActionSpaceConfig,
        errors: CompilationErrorCollector,
    ) -> ActionSpaceConfig | None:
        """Combine substrate default actions with global custom actions for validation."""

        try:
            substrate = SubstrateFactory.build(hamlet_config.substrate, torch.device("cpu"))
        except Exception as exc:  # pragma: no cover - defensive
            errors.add(f"substrate.yaml: failed to build substrate actions - {exc}")
            return None

        try:
            substrate_actions = substrate.get_default_actions()
        except Exception as exc:  # pragma: no cover - defensive
            errors.add(f"substrate.yaml: failed to derive default actions - {exc}")
            return None

        combined: list[ActionConfig] = []
        available_names: set[str] = set()
        next_id = 0

        enabled_lookup: set[str] | None
        training_enabled = hamlet_config.training.enabled_actions
        if training_enabled is None:
            enabled_lookup = None
        else:
            enabled_lookup = set(training_enabled)

        meter_names = {bar.name for bar in hamlet_config.bars}

        def _validate_meter_payload(
            payload: dict[str, float],
            action_name: str,
            field_name: str,  # "costs" or "effects"
        ) -> dict[str, float] | None:
            """Validate that all meters in payload are defined in bars.yaml.

            Args:
                payload: Dictionary of meter -> amount
                action_name: Name of the action being validated
                field_name: "costs" or "effects"

            Returns:
                The payload dict if valid, None if any unknown meters found (compilation error)
            """
            if not payload:
                return payload

            missing = [meter for meter in payload if meter not in meter_names]
            if missing:
                # Emit UAC-ACT-002 error for each unknown meter
                for meter in missing:
                    errors.add(
                        f"Action '{action_name}' references unknown meter '{meter}' in {field_name}. "
                        f"Ensure all meters are defined in bars.yaml.",
                        code="UAC-ACT-002",
                        location=f"global_actions.yaml:{action_name}",
                    )
                return None  # Signal compilation failure

            return payload

        def _is_enabled(action_name: str, base_enabled: bool) -> bool:
            if not base_enabled:
                return False
            if enabled_lookup is None:
                return True
            return action_name in enabled_lookup

        def _clone(action: ActionConfig) -> ActionConfig | None:
            """Clone action with validated meter references.

            Returns:
                Cloned ActionConfig if valid, None if validation fails
            """
            nonlocal next_id
            base_enabled = getattr(action, "enabled", True)

            # Validate costs and effects - None signals validation failure
            validated_costs = _validate_meter_payload(dict(action.costs), action.name, "costs")
            validated_effects = _validate_meter_payload(dict(action.effects), action.name, "effects")

            if validated_costs is None or validated_effects is None:
                return None  # Validation failed, errors already added

            cloned = action.model_copy(
                update={
                    "id": next_id,
                    "costs": validated_costs,
                    "effects": validated_effects,
                    "enabled": _is_enabled(action.name, base_enabled),
                }
            )
            next_id += 1
            return cloned

        validation_failed = False

        for action in substrate_actions:
            cloned = _clone(action)
            if cloned is None:
                validation_failed = True
                continue  # Skip this action, errors already added
            combined.append(cloned)
            available_names.add(cloned.name)

        for action in custom_actions.actions:
            cloned = _clone(action)
            if cloned is None:
                validation_failed = True
                continue  # Skip this action, errors already added
            combined.append(cloned)
            available_names.add(cloned.name)

        # If any action validation failed, abort compilation
        if validation_failed:
            return None

        if enabled_lookup is not None:
            missing = sorted(name for name in enabled_lookup if name not in available_names)
            if missing:
                missing_list = ", ".join(missing)
                errors.add(
                    "training.enabled_actions references unknown actions: "
                    f"{missing_list}. Ensure names match substrate defaults or configs/global_actions.yaml.",
                    code="UAC-ACT-001",
                    location="training.yaml:enabled_actions",
                )
                hint = (
                    "Review docs/config-schemas/enabled_actions.md for canonical action names "
                    "and confirm the training config lists only those identifiers."
                )
                if hint not in errors.hints:
                    errors.add_hint(hint)
                return None

        return ActionSpaceConfig(actions=combined)

    @staticmethod
    def _load_action_labels_config(config_dir: Path) -> ActionLabelConfig:
        yaml_path = config_dir / "action_labels.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError(f"action_labels.yaml not found in {config_dir}")

        with yaml_path.open() as handle:
            data = yaml.safe_load(handle) or {}

        payload = data.get("action_labels", data)
        if not isinstance(payload, dict):
            raise ValueError(f"action_labels.yaml must define a mapping, got {type(payload).__name__}")

        return ActionLabelConfig(**payload)
