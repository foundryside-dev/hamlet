"""Symbol table utilities for the Universe Compiler."""

from __future__ import annotations

from dataclasses import dataclass, field

from townlet.config.actions_config import CustomActionConfig
from townlet.config.environment_config import AffordanceDefinition, CascadeConfig, MeterConfig
from townlet.config.items_config import ItemTypeConfig
from townlet.config.variables_config import VariableDeclaration

from .error_codes import ErrorCode
from .errors import CompilationError, CompilationMessage
from .stages import CompilationStage


def _duplicate(message: str) -> CompilationMessage:
    """A duplicate-identity refusal; ``build_symbol_table`` supplies the declaration's location."""
    return CompilationMessage(code=ErrorCode.SYMBOL_DUPLICATE, message=message, location=None)


@dataclass
class UniverseSymbolTable:
    """Stores registered entities for cross-stage validation.

    Meter bars and non-item variables share one runtime state namespace (the VTC
    merges ``bars_state`` into ``vfs_state`` by bare name), so the collision between
    them is refused where both vocabularies are first visible together:
    ``validation.references.build_symbol_table``, which also holds the two origins.
    """

    meters: dict[str, MeterConfig] = field(default_factory=dict)
    cascades: dict[str, CascadeConfig] = field(default_factory=dict)
    affordances: dict[str, AffordanceDefinition] = field(default_factory=dict)
    variables: dict[str, VariableDeclaration] = field(default_factory=dict)
    item_variables: dict[tuple[str, str], VariableDeclaration] = field(default_factory=dict)
    actions: dict[str, CustomActionConfig] = field(default_factory=dict)
    items: dict[str, ItemTypeConfig] = field(default_factory=dict)

    def register_meter(self, config: MeterConfig) -> None:
        if config.name in self.meters:
            raise CompilationError(CompilationStage.SYMBOLS.label, [_duplicate(f"Duplicate meter '{config.name}' detected.")])
        self.meters[config.name] = config

    def register_variable(self, config: VariableDeclaration) -> None:
        identifier = config.id
        if config.scope == "item":
            assert config.profile is not None
            identity = (config.profile, identifier)
            if identity in self.item_variables:
                raise CompilationError(
                    CompilationStage.SYMBOLS.label, [_duplicate(f"Duplicate variable '{config.profile}:{identifier}' detected.")]
                )
            self.item_variables[identity] = config
            return
        if identifier in self.variables:
            raise CompilationError(CompilationStage.SYMBOLS.label, [_duplicate(f"Duplicate variable '{identifier}' detected.")])
        self.variables[identifier] = config

    def register_action(self, config: CustomActionConfig) -> None:
        if config.name in self.actions:
            raise CompilationError(CompilationStage.SYMBOLS.label, [_duplicate(f"Duplicate action id '{config.name}' detected.")])
        self.actions[config.name] = config

    def register_cascade(self, config: CascadeConfig) -> None:
        cascade_name = f"{config.source}->{config.target}"
        if cascade_name in self.cascades:
            raise CompilationError(CompilationStage.SYMBOLS.label, [_duplicate(f"Duplicate cascade '{cascade_name}' detected.")])
        self.cascades[cascade_name] = config

    def register_affordance(self, config: AffordanceDefinition) -> None:
        if config.name in self.affordances:
            raise CompilationError(CompilationStage.SYMBOLS.label, [_duplicate(f"Duplicate affordance '{config.name}' detected.")])
        self.affordances[config.name] = config

    def register_item(self, item: ItemTypeConfig) -> None:
        if item.id in self.items:
            raise CompilationError(CompilationStage.SYMBOLS.label, [_duplicate(f"Duplicate item '{item.id}' detected.")])
        self.items[item.id] = item

    @property
    def vfs_variables(self) -> dict[str, VariableDeclaration]:
        """Variables that may be referenced through VFS-aware config surfaces."""
        return self.variables
