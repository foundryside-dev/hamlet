"""Configuration schemas for Items system."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

__all__ = [
    "ItemTypeConfig",
    "ItemInteractionsConfig",
    "ItemsCatalogConfig",
    "ItemAppearanceRuleConfig",
    "ItemsAppearanceConfig",
    "ItemCustomCommand",
    "build_item_command_action_name",
]


class ItemCustomCommand(BaseModel):
    """Custom item verb definition."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Action name for the custom verb (must be unique in action space)")
    description: str | None = Field(default=None, description="Human readable description of the custom verb")
    effects: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Effects command list executed when this verb is invoked",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure command names are non-empty and use uppercase/snake for action space stability."""
        if not v or not v.strip():
            raise ValueError("Custom command name must be non-empty")
        if not v.replace("_", "").isalnum():
            raise ValueError(f"Custom command name must be alphanumeric/underscores only: {v}")
        return v

    @field_validator("effects")
    @classmethod
    def validate_effects(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Basic structure validation; detailed validation occurs in the Effects compiler."""
        if not v:
            raise ValueError("Custom commands must provide at least one effect command")
        supported_command_keys = {
            "modify",
            "spawn_effect",
            "spawn_item",
            "if",
            "switch",
            "parallel",
            "reduce",
            "delay",
            "for_each",
            "sample",
            "distribution",  # alias for sample in some fixtures
        }
        for cmd in v:
            if not isinstance(cmd, dict):
                raise ValueError(f"Effect command must be dict, got {type(cmd)}")
            if not any(k in cmd for k in supported_command_keys):
                ordered = ["modify", "spawn_effect", "spawn_item", "if", "for_each", "switch", "reduce", "parallel", "delay", "sample"]
                raise ValueError(f"Effect command must include one of: {', '.join(ordered)}. Got keys: {list(cmd.keys())}")
        return v


def build_item_command_action_name(item_id: str, command_name: str, scope: Literal["local", "inventory"]) -> str:
    """Stable action name for item custom verbs."""
    return f"ITEM_{scope.upper()}_{item_id.upper()}_{command_name.upper()}"


class ItemInteractionsConfig(BaseModel):
    """Item interaction commands (using Effects syntax).

    All interactions are Effects commands (modify, spawn_effect, etc.).
    Phase 1-3 does NOT support custom item commands.
    """

    model_config = ConfigDict(extra="forbid")  # Reject unknown fields (like local_commands, inventory_commands)

    on_pickup: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Commands executed when item picked up into inventory",
    )

    on_use: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Commands executed when USE_SLOT_N action used",
    )

    on_drop: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Commands executed when item dropped from inventory",
    )

    # Custom verbs
    local_commands: list[ItemCustomCommand] = Field(
        default_factory=list,
        description="Custom commands usable when agent is co-located with the item",
    )
    inventory_commands: list[ItemCustomCommand] = Field(
        default_factory=list,
        description="Custom commands usable only when the item is held in inventory",
    )

    @field_validator("on_pickup", "on_use", "on_drop")
    @classmethod
    def validate_commands(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate command structure (detailed validation in Effects compiler)."""
        supported_command_keys = {
            "modify",
            "spawn_effect",
            "spawn_item",
            "if",
            "switch",
            "parallel",
            "reduce",
            "delay",
            "for_each",
            "sample",
            "distribution",
        }
        for cmd in v:
            if not isinstance(cmd, dict):
                raise ValueError(f"Command must be dict, got {type(cmd)}")
            # Basic validation - detailed validation happens in Effects compiler
            if not any(k in cmd for k in supported_command_keys):
                ordered = ["modify", "spawn_effect", "spawn_item", "if", "for_each", "switch", "reduce", "parallel", "delay", "sample"]
                raise ValueError(f"Command must have one of: {', '.join(ordered)}. Got keys: {list(cmd.keys())}")
        return v


class ItemTypeConfig(BaseModel):
    """Item type definition (experiment-level catalog)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        description="Display name for UI/metadata",
    )

    icon: str = Field(
        ...,
        description="Icon/emoji for UI",
        max_length=16,
    )

    tags: list[str] = Field(
        ...,
        min_length=1,
        description="Categorization tags for expressions/UI",
    )

    id: str = Field(..., description="Unique item type identifier")

    vfs_profile: str = Field(
        ...,
        description="VFS profile ID from vfs_profiles.yaml (item scope)",
    )

    interactions: ItemInteractionsConfig = Field(
        ...,
        description="Item interaction commands (pickup/use/drop)",
    )

    duration: int | None = Field(
        default=None,
        description="Item lifetime in ticks (None = permanent)",
        ge=1,
    )

    cooldown: int | None = Field(
        default=None,
        description="Ticks before item can spawn again after despawn",
        ge=0,
    )

    description: str | None = Field(
        default=None,
        description="Human-readable description (metadata only)",
    )

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate item ID format."""
        if not v.islower():
            raise ValueError(f"Item ID must be lowercase: {v}")
        if not v.replace("_", "").isalnum():
            raise ValueError(f"Item ID must be alphanumeric with underscores: {v}")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Ensure tags are strings without whitespace."""
        for tag in v:
            if not tag or not tag.strip():
                raise ValueError("Tags must be non-empty strings")
        return v

    @field_validator("name", "icon")
    @classmethod
    def validate_metadata_str(cls, v: str, field: Any) -> str:
        """Ensure metadata strings are non-empty."""
        if not v or not str(v).strip():
            raise ValueError(f"{field.field_name} must be non-empty")
        return v


class ItemsCatalogConfig(BaseModel):
    """Experiment-level item catalog (items.yaml)."""

    model_config = ConfigDict(extra="forbid")

    version: Literal["1.0"] = Field(..., description="Config schema version")

    item_types: list[ItemTypeConfig] = Field(
        ...,
        description="Item type definitions",
    )

    max_items_per_agent: int = Field(..., description="Maximum items agent can carry", ge=1, le=10)

    max_items_in_world: int = Field(..., description="Maximum items that can exist in world simultaneously", ge=1, le=1000)

    @field_validator("item_types")
    @classmethod
    def validate_unique_ids(cls, v: list[ItemTypeConfig]) -> list[ItemTypeConfig]:
        """Ensure item type IDs are unique."""
        ids = [item.id for item in v]
        if len(ids) != len(set(ids)):
            duplicates = [id for id in ids if ids.count(id) > 1]
            raise ValueError(f"Duplicate item type IDs: {duplicates}")
        return v

    @classmethod
    def from_yaml(cls, path: Path) -> ItemsCatalogConfig:
        """Load items catalog from YAML file.

        Args:
            path: Path to items.yaml file

        Returns:
            ItemsCatalogConfig instance

        Raises:
            ValidationError: If YAML structure doesn't match schema
            FileNotFoundError: If path doesn't exist
        """
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data["items"])


class SpawnScheduleConfig(BaseModel):
    """Scheduling options for item spawns."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["periodic", "time_window", "poisson", "normal"] = Field(
        default="periodic",
        description="Scheduling strategy: periodic | time_window | poisson | normal",
    )

    period: int | None = Field(
        default=None,
        description="Ticks between spawns for periodic schedule (required for periodic)",
        ge=1,
    )

    start_tick: int | None = Field(
        default=None,
        description="Inclusive start tick for time_window schedule",
        ge=0,
    )

    end_tick: int | None = Field(
        default=None,
        description="Inclusive end tick for time_window schedule",
        ge=0,
    )

    rate: float | None = Field(
        default=None,
        description="Poisson rate (lambda) per tick for poisson schedule",
        ge=0.0,
    )

    mean: float | None = Field(
        default=None,
        description="Mean tick for normal schedule",
        ge=0.0,
    )

    std_dev: float | None = Field(
        default=None,
        description="Standard deviation for normal schedule",
        gt=0.0,
    )


class SpawnPlacementConfig(BaseModel):
    """Placement options for item spawns."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["random", "fixed", "grid", "scripted"] = Field(
        default="random",
        description="Placement mode: random | fixed | grid | scripted",
    )

    fixed_positions: list[tuple[int, int]] | None = Field(
        default=None,
        description="Explicit positions for fixed placement",
    )

    grid_spacing: int | None = Field(
        default=None,
        description="Grid spacing for grid placement (cells)",
        ge=1,
    )

    script: list[dict[str, Any]] | None = Field(
        default=None,
        description="Scripted spawn events: list of {tick: int, position: (x,y)}",
    )


class ItemAppearanceRuleConfig(BaseModel):
    """Spawn rule for an item type in a specific level."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    item_type: str = Field(..., description="Item type ID from catalog")

    spawn_count: int = Field(..., description="Number of items to spawn at level start", ge=0)

    spawn_interval: int | None = Field(
        default=None,
        description="Ticks between spawns (None = only spawn at level start). Superseded by schedule when provided.",
        ge=1,
    )

    spawn_position: Literal["random", "fixed"] = Field(
        default="random",
        description="How to choose spawn position (legacy). Superseded by placement when provided.",
    )

    placement: SpawnPlacementConfig | None = Field(
        default=None,
        description="Advanced placement configuration (fixed/grid/scripted)",
    )

    schedule: SpawnScheduleConfig | None = Field(
        default=None,
        description="Advanced scheduling configuration (time_window/poisson/normal)",
    )

    max_total: int | None = Field(
        default=None,
        description="Maximum total spawns for this rule (cumulative)",
        ge=1,
    )

    # Optional spawn predicate (compiled to when_ast at compile time)
    when: str | None = Field(
        default=None,
        description="Condition expression (bool) gating the spawn rule",
    )

    # Stored compiled expression AST (set by UniverseCompiler)
    when_ast: Any | None = Field(default=None, exclude=True, repr=False)


class ItemsAppearanceConfig(BaseModel):
    """Level-specific item spawn rules (levels/*/items.yaml)."""

    model_config = ConfigDict(extra="forbid")

    version: Literal["1.0"] = Field(..., description="Config schema version")

    items: list[ItemAppearanceRuleConfig] = Field(
        default_factory=list,
        description="Item spawn rules for this level",
    )
