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
]


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

    @field_validator("on_pickup", "on_use", "on_drop")
    @classmethod
    def validate_commands(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate command structure (detailed validation in Effects compiler)."""
        for cmd in v:
            if not isinstance(cmd, dict):
                raise ValueError(f"Command must be dict, got {type(cmd)}")
            # Basic validation - detailed validation happens in Effects compiler
            command_types = ["modify", "spawn_effect", "spawn_item", "if"]
            if not any(k in cmd for k in command_types):
                raise ValueError(f"Command must have one of: {', '.join(command_types)}. Got keys: {list(cmd.keys())}")
        return v


class ItemTypeConfig(BaseModel):
    """Item type definition (experiment-level catalog)."""

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


class ItemsCatalogConfig(BaseModel):
    """Experiment-level item catalog (items.yaml)."""

    version: Literal["1.0"] = Field(
        default="1.0",
        description="Config schema version",
    )

    item_types: list[ItemTypeConfig] = Field(
        ...,
        description="Item type definitions",
    )

    max_items_per_agent: int = Field(
        default=3,
        description="Maximum items agent can carry",
        ge=1,
        le=10,
    )

    max_items_in_world: int = Field(
        default=10,
        description="Maximum items that can exist in world simultaneously",
        ge=1,
        le=1000,
    )

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

    spawn_count: int = Field(
        default=1,
        description="Number of items to spawn at level start",
        ge=0,
    )

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

    version: Literal["1.0"] = Field(
        default="1.0",
        description="Config schema version",
    )

    items: list[ItemAppearanceRuleConfig] = Field(
        default_factory=list,
        description="Item spawn rules for this level",
    )
