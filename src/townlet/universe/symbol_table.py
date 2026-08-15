"""Symbol table utilities for the Universe Compiler."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from townlet.config.cues import CompoundCueConfig, SimpleCueConfig
from townlet.environment.action_config import ActionConfig
from townlet.vfs.schema import VariableDef

from .errors import CompilationError


@dataclass
class UniverseSymbolTable:
    """Stores registered entities for cross-stage validation."""

    meters: dict[str, Any] = field(default_factory=dict)
    cascades: dict[str, Any] = field(default_factory=dict)
    affordances: dict[str, Any] = field(default_factory=dict)
    affordances_by_name: dict[str, Any] = field(default_factory=dict)
    variables: dict[str, VariableDef] = field(default_factory=dict)
    profile_vfs_variables: dict[str, Any] = field(default_factory=dict)
    actions: dict[int, ActionConfig] = field(default_factory=dict)
    cues: dict[str, SimpleCueConfig | CompoundCueConfig] = field(default_factory=dict)
    items: dict[str, Any] = field(default_factory=dict)

    def register_meter(self, config: Any) -> None:
        if config.name in self.meters:
            raise CompilationError("Stage 2: Symbol Table", [f"Duplicate meter '{config.name}' detected."])
        self.meters[config.name] = config

    def register_variable(self, config: VariableDef) -> None:
        var_id = getattr(config, "id", None) or getattr(config, "name", None)
        if var_id is None:
            raise CompilationError("Stage 2: Symbol Table", ["Variable missing identifier during registration."])
        if var_id in self.variables:
            raise CompilationError("Stage 2: Symbol Table", [f"Duplicate variable '{var_id}' detected."])
        self.variables[var_id] = config

    def register_profile_vfs_variable(self, config: Any) -> None:
        var_id = getattr(config, "id", None) or getattr(config, "name", None)
        if var_id is None:
            raise CompilationError("Stage 2: Symbol Table", ["VFS profile variable missing identifier during registration."])
        self.profile_vfs_variables.setdefault(var_id, config)

    def register_action(self, config: ActionConfig) -> None:
        action_id = getattr(config, "id", None)
        if action_id is None:
            action_id = getattr(config, "name", None)
        if action_id is None:
            raise CompilationError("Stage 2: Symbol Table", ["Action missing identifier during registration."])
        if action_id in self.actions:
            raise CompilationError("Stage 2: Symbol Table", [f"Duplicate action id '{action_id}' detected."])
        self.actions[action_id] = config

    def register_cascade(self, config: Any) -> None:
        cascade_name = getattr(config, "name", None)
        if cascade_name is None:
            source = getattr(config, "source", None)
            target = getattr(config, "target", None)
            cascade_name = f"{source}->{target}"
        if cascade_name in self.cascades:
            raise CompilationError("Stage 2: Symbol Table", [f"Duplicate cascade '{cascade_name}' detected."])
        self.cascades[cascade_name] = config

    def register_affordance(self, config: Any) -> None:
        aff_id = getattr(config, "id", None) or getattr(config, "name", None)
        aff_name = getattr(config, "name", aff_id)
        if aff_id is None or aff_name is None:
            raise CompilationError("Stage 2: Symbol Table", ["Affordance missing identifier during registration."])
        if aff_id in self.affordances:
            raise CompilationError("Stage 2: Symbol Table", [f"Duplicate affordance '{aff_id}' detected."])
        if aff_name in self.affordances_by_name:
            raise CompilationError("Stage 2: Symbol Table", [f"Duplicate affordance name '{aff_name}' detected."])
        self.affordances[aff_id] = config
        self.affordances_by_name[aff_name] = config

    def register_cue(self, cue: SimpleCueConfig | CompoundCueConfig) -> None:
        if cue.cue_id in self.cues:
            raise CompilationError("Stage 2: Symbol Table", [f"Duplicate cue '{cue.cue_id}' detected."])
        self.cues[cue.cue_id] = cue

    def register_item(self, item: Any) -> None:
        """Register items by id (preferred) or name to validate references."""
        identifier = getattr(item, "id", None) or getattr(item, "name", None)
        if identifier is None:
            raise CompilationError("Stage 2: Symbol Table", ["Item missing required identifier during registration."])
        if identifier in self.items:
            raise CompilationError("Stage 2: Symbol Table", [f"Duplicate item '{identifier}' detected."])
        self.items[identifier] = item

    def get_meter(self, name: str) -> Any:
        return self.meters[name]

    def get_meter_names(self) -> list[str]:
        return [meter.name for meter in sorted(self.meters.values(), key=lambda m: m.index)]

    def resolve_meter_reference(self, name: str, *, location: str | None = None) -> Any:
        if name not in self.meters:
            raise ReferenceError(f"References non-existent meter '{name}'. Valid meters: {list(self.meters.keys())}")
        return self.meters[name]

    def get_meter_count(self) -> int:
        return len(self.meters)

    def get_action(self, action_id: int) -> ActionConfig:
        return self.actions[action_id]

    def get_variable(self, variable_id: str) -> VariableDef:
        return self.variables[variable_id]

    def get_affordance_count(self) -> int:
        return len(self.affordances)

    @property
    def affordance_ids(self) -> list[str]:
        return sorted(self.affordances.keys())

    @property
    def affordance_names(self) -> list[str]:
        return sorted(self.affordances_by_name.keys())

    @property
    def vfs_variables(self) -> dict[str, Any]:
        """Variables that may be referenced through VFS-aware config surfaces."""
        return {**self.variables, **self.profile_vfs_variables}

    def get_affordance(self, affordance_id: str) -> Any:
        return self.affordances[affordance_id]

    def get_affordance_by_name(self, affordance_name: str) -> Any:
        return self.affordances_by_name[affordance_name]
