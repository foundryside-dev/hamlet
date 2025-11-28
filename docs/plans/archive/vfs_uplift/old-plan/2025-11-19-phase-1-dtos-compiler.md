# Items & VFS Profiles - Phase 1: DTOs + Compiler

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement Pydantic DTOs and compiler integration for items and VFS profiles (metadata-only, no runtime behavior).

**Architecture:** Add 2 new DTO modules (`items_config.py`, `vfs_profiles_config.py`), extend UniverseCompiler with load stages, update CompiledUniverse with catalog fields. All validation at compile-time, zero runtime changes.

**Tech Stack:** Python 3.13, Pydantic v2, YAML, pytest

**Prerequisites:**
- Phase 0 complete (all design decisions resolved and approved)
- All tests passing: `uv run pytest tests/test_townlet/`
- Working directory: dedicated worktree or feature branch

**Estimated Time:** 16-24 hours implementation + 8-12 hours testing = 4-5 days

---

## Task 1: Create VFS Profiles DTO Module

**Files:**
- Create: `src/townlet/config/vfs_profiles_config.py`
- Test: `tests/test_townlet/unit/config/test_vfs_profiles_config.py`

### Step 1: Write failing test for VFSProfileConfig

```python
# tests/test_townlet/unit/config/test_vfs_profiles_config.py

"""Tests for VFS Profiles configuration DTOs."""

import pytest
from pydantic import ValidationError

from townlet.config.vfs_profiles_config import (
    VFSProfileConfig,
    VFSProfilesConfig,
    GlobalVFSProfileConfig,
    AgentVFSProfileConfig,
    ItemVFSProfileConfig,
)


class TestVFSProfileConfig:
    """Tests for individual VFS profile definitions."""

    def test_global_profile_minimal(self):
        """Global profile with only required fields."""
        profile = GlobalVFSProfileConfig(
            id="test_global",
            scope="global",
            type="scalar",
            initial_value=1.0,
        )
        assert profile.id == "test_global"
        assert profile.scope == "global"
        assert profile.type == "scalar"
        assert profile.initial_value == 1.0

    def test_agent_profile_with_normalization(self):
        """Agent profile with normalization spec."""
        profile = AgentVFSProfileConfig(
            id="test_agent",
            scope="agent",
            type="scalar",
            initial_value=0.5,
            normalization={
                "kind": "minmax",
                "min": 0.0,
                "max": 1.0,
            },
        )
        assert profile.normalization.kind == "minmax"
        assert profile.normalization.min == 0.0
        assert profile.normalization.max == 1.0

    def test_item_profile_vector(self):
        """Item profile with vector type."""
        profile = ItemVFSProfileConfig(
            id="test_item_vec",
            scope="item",
            type="vec2i",
            initial_value=[0, 0],
        )
        assert profile.type == "vec2i"
        assert profile.initial_value == [0, 0]

    def test_rejects_expression_field(self):
        """Phase 1: Reject expression field (Phase 2+ feature)."""
        with pytest.raises(ValidationError) as exc_info:
            GlobalVFSProfileConfig(
                id="bad_profile",
                scope="global",
                type="scalar",
                initial_value=1.0,
                expression="time_of_day >= 20",  # FORBIDDEN in Phase 1
            )
        assert "expression" in str(exc_info.value).lower()

    def test_rejects_deps_field(self):
        """Phase 1: Reject deps field (Phase 2+ feature)."""
        with pytest.raises(ValidationError) as exc_info:
            GlobalVFSProfileConfig(
                id="bad_profile",
                scope="global",
                type="scalar",
                initial_value=1.0,
                deps={"bars": ["time"]},  # FORBIDDEN in Phase 1
            )
        assert "deps" in str(exc_info.value).lower()

    def test_requires_initial_value(self):
        """Phase 1: initial_value is required."""
        with pytest.raises(ValidationError) as exc_info:
            GlobalVFSProfileConfig(
                id="bad_profile",
                scope="global",
                type="scalar",
                # initial_value missing
            )
        assert "initial_value" in str(exc_info.value).lower()

    def test_extra_fields_forbidden(self):
        """Pydantic extra='forbid' enforcement."""
        with pytest.raises(ValidationError) as exc_info:
            GlobalVFSProfileConfig(
                id="test",
                scope="global",
                type="scalar",
                initial_value=1.0,
                unknown_field="bad",
            )
        assert "extra" in str(exc_info.value).lower()
```

### Step 2: Run test to verify it fails

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=src:tests uv run pytest tests/test_townlet/unit/config/test_vfs_profiles_config.py::TestVFSProfileConfig::test_global_profile_minimal -v
```

Expected: `ModuleNotFoundError: No module named 'townlet.config.vfs_profiles_config'`

### Step 3: Write minimal VFS profiles DTO implementation

```python
# src/townlet/config/vfs_profiles_config.py

"""VFS Profiles configuration DTOs.

Phase 1: Static variables only (initial_value field).
Phase 2+: Expression-based variables (deps, expression fields) via BAC integration.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class VFSProfileNormalizationConfig(BaseModel):
    """Normalization specification for VFS profile observations.

    Identical to vfs.schema.NormalizationSpec, but redefined here
    to keep config layer independent of runtime VFS implementation.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["minmax", "zscore"] = Field(
        description="Normalization method"
    )
    min: float | list[float] | None = Field(
        default=None,
        description="Minimum value(s) for minmax normalization",
    )
    max: float | list[float] | None = Field(
        default=None,
        description="Maximum value(s) for minmax normalization",
    )
    mean: float | list[float] | None = Field(
        default=None,
        description="Mean value(s) for zscore normalization",
    )
    std: float | list[float] | None = Field(
        default=None,
        description="Standard deviation(s) for zscore normalization",
    )

    @model_validator(mode="after")
    def validate_normalization_params(self) -> "VFSProfileNormalizationConfig":
        """Validate that required parameters are present for each kind."""
        if self.kind == "minmax":
            if self.min is None or self.max is None:
                raise ValueError(
                    "minmax normalization requires 'min' and 'max' parameters"
                )
        elif self.kind == "zscore":
            if self.mean is None or self.std is None:
                raise ValueError(
                    "zscore normalization requires 'mean' and 'std' parameters"
                )
        return self


class VFSProfileConfig(BaseModel):
    """Base configuration for a VFS profile (Phase 1: static variables only).

    Phase 1 Constraints:
    - Only 'initial_value' field supported (static defaults)
    - 'expression', 'deps', 'update_on' fields FORBIDDEN (raise ValidationError)
    - Variables are metadata-only; no runtime evaluation

    Phase 2+ (BAC Integration):
    - 'expression' field: DSL for derived variables
    - 'deps' field: Dependencies on bars/VFS/affordances
    - 'update_on' field: Conditional update rules
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        description="Unique profile identifier (stable across experiments)"
    )
    scope: Literal["global", "agent", "item"] = Field(
        description="Profile scope: global (world), agent (per-agent), item (per-item)"
    )
    type: Literal["scalar", "vec2i", "vec3i", "vecNi", "vecNf", "bool"] = Field(
        description="Variable data type"
    )
    dims: int | None = Field(
        default=None,
        description="Vector dimensions (required if type is vecNi/vecNf)",
    )
    initial_value: float | int | bool | list[float] | list[int] = Field(
        description="Static default value (Phase 1: only source of variable state)"
    )
    normalization: VFSProfileNormalizationConfig | None = Field(
        default=None,
        description="Observation normalization (optional)",
    )
    description: str | None = Field(
        default=None,
        description="Human-readable description (documentation only)",
    )

    @model_validator(mode="before")
    @classmethod
    def reject_phase2_fields(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Phase 1 guard: Reject expression-based fields (Phase 2+ features)."""
        forbidden = ["expression", "deps", "update_on"]
        for field in forbidden:
            if field in data:
                raise ValueError(
                    f"Field '{field}' requires Phase 2+ (BAC integration). "
                    f"Use 'initial_value' for static variables in Phase 1."
                )
        return data

    @model_validator(mode="after")
    def validate_dims(self) -> "VFSProfileConfig":
        """Validate dims field for vector types."""
        if self.type in ("vecNi", "vecNf"):
            if self.dims is None:
                raise ValueError(f"Type '{self.type}' requires 'dims' field")
            if self.dims <= 0:
                raise ValueError(f"'dims' must be positive, got {self.dims}")
        elif self.dims is not None:
            raise ValueError(
                f"'dims' field only valid for vecNi/vecNf, not '{self.type}'"
            )
        return self


class GlobalVFSProfileConfig(VFSProfileConfig):
    """Global VFS profile (world-level state)."""
    scope: Literal["global"] = "global"


class AgentVFSProfileConfig(VFSProfileConfig):
    """Agent VFS profile (per-agent state, replicated across agents)."""
    scope: Literal["agent"] = "agent"


class ItemVFSProfileConfig(VFSProfileConfig):
    """Item VFS profile (per-item state, replicated across item instances)."""
    scope: Literal["item"] = "item"


class VFSProfilesConfig(BaseModel):
    """Root configuration for VFS profiles (experiment-scoped).

    File: configs/<experiment>/vfs_profiles.yaml
    """

    model_config = ConfigDict(extra="forbid")

    version: str = Field(
        description="Config schema version (currently '1.0')"
    )
    global_profiles: list[GlobalVFSProfileConfig] = Field(
        default_factory=list,
        description="Global VFS profiles (world-level state)",
    )
    agent_profiles: list[AgentVFSProfileConfig] = Field(
        default_factory=list,
        description="Agent VFS profiles (per-agent state)",
    )
    item_profiles: list[ItemVFSProfileConfig] = Field(
        default_factory=list,
        description="Item VFS profiles (per-item instance state)",
    )

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate config version is supported."""
        if v != "1.0":
            raise ValueError(
                f"Unsupported vfs_profiles.yaml version: {v}. "
                f"Expected '1.0'."
            )
        return v

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "VFSProfilesConfig":
        """Ensure profile IDs are unique within each scope."""
        all_profiles = (
            self.global_profiles + self.agent_profiles + self.item_profiles
        )
        ids = [p.id for p in all_profiles]
        duplicates = [id_ for id_ in ids if ids.count(id_) > 1]
        if duplicates:
            raise ValueError(
                f"Duplicate VFS profile IDs: {set(duplicates)}. "
                f"All profile IDs must be unique across all scopes."
            )
        return self

    @model_validator(mode="after")
    def enforce_phase1_limits(self) -> "VFSProfilesConfig":
        """Enforce Phase 1 performance limits."""
        MAX_GLOBAL = 20
        MAX_AGENT = 20
        # Item profiles limited implicitly via max_vfs_profiles_per_item

        if len(self.global_profiles) > MAX_GLOBAL:
            raise ValueError(
                f"Too many global VFS profiles: {len(self.global_profiles)} > {MAX_GLOBAL}. "
                f"Phase 1 limit. Reduce profile count."
            )
        if len(self.agent_profiles) > MAX_AGENT:
            raise ValueError(
                f"Too many agent VFS profiles: {len(self.agent_profiles)} > {MAX_AGENT}. "
                f"Phase 1 limit. Reduce profile count."
            )
        return self
```

### Step 4: Run tests to verify they pass

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=src:tests uv run pytest tests/test_townlet/unit/config/test_vfs_profiles_config.py -v
```

Expected: All tests PASS

### Step 5: Commit

```bash
git add src/townlet/config/vfs_profiles_config.py tests/test_townlet/unit/config/test_vfs_profiles_config.py
git commit -m "feat(config): add VFS profiles DTOs (Phase 1 static variables)

- VFSProfileConfig base class with scope/type/initial_value
- GlobalVFSProfileConfig, AgentVFSProfileConfig, ItemVFSProfileConfig
- VFSProfilesConfig root with unique ID validation
- Phase 1 guards: Reject expression/deps/update_on fields
- Phase 1 limits: max 20 global, 20 agent profiles
- Comprehensive tests (9 test cases)
"
```

---

## Task 2: Create Items DTO Module

**Files:**
- Create: `src/townlet/config/items_config.py`
- Test: `tests/test_townlet/unit/config/test_items_config.py`

### Step 1: Write failing test for ItemsCatalogConfig

```python
# tests/test_townlet/unit/config/test_items_config.py

"""Tests for Items configuration DTOs."""

import pytest
from pydantic import ValidationError

from townlet.config.items_config import (
    InventoryConfig,
    ItemTypeConfig,
    ItemInteractionEffectConfig,
    ItemsCatalogConfig,
    ItemsAppearanceConfig,
    ItemSpawnPlacementConfig,
    ItemSpawnScheduleConfig,
    ItemSpawnLimitsConfig,
    ItemSpawnRuleConfig,
)


class TestItemsCatalogConfig:
    """Tests for experiment-level item catalog."""

    def test_minimal_catalog(self):
        """Catalog with one simple item type."""
        catalog = ItemsCatalogConfig(
            version="1.0",
            item_types=[
                {
                    "id": "umbrella",
                    "name": "Umbrella",
                    "icon": "☂️",
                    "tags": ["weather", "protection"],
                    "vfs_profiles": [],
                    "interactions": {},
                }
            ],
        )
        assert len(catalog.item_types) == 1
        assert catalog.item_types[0].id == "umbrella"

    def test_item_with_vfs_profiles(self):
        """Item referencing VFS profiles."""
        catalog = ItemsCatalogConfig(
            version="1.0",
            item_types=[
                {
                    "id": "umbrella",
                    "name": "Umbrella",
                    "icon": "☂️",
                    "tags": [],
                    "vfs_profiles": ["item_wetness_resistance", "item_durability"],
                    "interactions": {},
                }
            ],
        )
        assert catalog.item_types[0].vfs_profiles == [
            "item_wetness_resistance",
            "item_durability",
        ]

    def test_enforce_max_item_types(self):
        """Phase 1 limit: max 10 item types."""
        with pytest.raises(ValidationError) as exc_info:
            ItemsCatalogConfig(
                version="1.0",
                item_types=[
                    {
                        "id": f"item_{i}",
                        "name": f"Item {i}",
                        "icon": "🔹",
                        "tags": [],
                        "vfs_profiles": [],
                        "interactions": {},
                    }
                    for i in range(11)  # 11 > MAX_ITEM_TYPES
                ],
            )
        assert "too many item types" in str(exc_info.value).lower()

    def test_enforce_max_vfs_profiles_per_item(self):
        """Phase 1 limit: max 5 VFS profiles per item."""
        with pytest.raises(ValidationError) as exc_info:
            ItemsCatalogConfig(
                version="1.0",
                item_types=[
                    {
                        "id": "bad_item",
                        "name": "Bad Item",
                        "icon": "❌",
                        "tags": [],
                        "vfs_profiles": [f"profile_{i}" for i in range(6)],  # 6 > 5
                        "interactions": {},
                    }
                ],
            )
        assert "too many vfs profiles" in str(exc_info.value).lower()

    def test_duplicate_item_ids_rejected(self):
        """Item IDs must be unique."""
        with pytest.raises(ValidationError) as exc_info:
            ItemsCatalogConfig(
                version="1.0",
                item_types=[
                    {
                        "id": "duplicate",
                        "name": "Item 1",
                        "icon": "🔹",
                        "tags": [],
                        "vfs_profiles": [],
                        "interactions": {},
                    },
                    {
                        "id": "duplicate",
                        "name": "Item 2",
                        "icon": "🔸",
                        "tags": [],
                        "vfs_profiles": [],
                        "interactions": {},
                    },
                ],
            )
        assert "duplicate" in str(exc_info.value).lower()


class TestItemsAppearanceConfig:
    """Tests for level-scoped item appearance."""

    def test_minimal_appearance(self):
        """Appearance config with inventory only."""
        appearance = ItemsAppearanceConfig(
            version="1.0",
            inventory={"max_items_per_agent": 3},
            spawn_rules=[],
        )
        assert appearance.inventory.max_items_per_agent == 3

    def test_enforce_max_items_per_agent(self):
        """Phase 1 limit: max_items_per_agent <= 3."""
        with pytest.raises(ValidationError) as exc_info:
            ItemsAppearanceConfig(
                version="1.0",
                inventory={"max_items_per_agent": 5},  # 5 > 3
                spawn_rules=[],
            )
        assert "max_items_per_agent" in str(exc_info.value).lower()

    def test_spawn_rule_references_catalog(self):
        """Spawn rules reference item type IDs from catalog."""
        appearance = ItemsAppearanceConfig(
            version="1.0",
            inventory={"max_items_per_agent": 3},
            spawn_rules=[
                {
                    "type_id": "umbrella",
                    "placement": {
                        "mode": "random",
                        "positions": [],
                    },
                    "schedule": {
                        "kind": "once",
                        "params": {},
                    },
                    "limits": {
                        "max_simultaneous": 3,
                        "max_total": 10,
                    },
                    "lifecycle": {
                        "duration_steps": 50,
                        "cooldown_steps": 20,
                    },
                    "priority": 10,
                    "conditions": [],
                }
            ],
        )
        assert appearance.spawn_rules[0].type_id == "umbrella"

    def test_no_defaults_for_spawn_limits(self):
        """Spawn limits must be explicit (no defaults)."""
        with pytest.raises(ValidationError):
            ItemSpawnRuleConfig(
                type_id="umbrella",
                placement={
                    "mode": "random",
                    "positions": [],
                },
                schedule={
                    "kind": "once",
                    "params": {},
                },
                limits={
                    "max_simultaneous": 3,
                    # max_total missing - REQUIRED
                },
                lifecycle={
                    "duration_steps": 50,
                    "cooldown_steps": 20,
                },
                priority=10,
                conditions=[],
            )
```

### Step 2: Run test to verify it fails

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=src:tests uv run pytest tests/test_townlet/unit/config/test_items_config.py::TestItemsCatalogConfig::test_minimal_catalog -v
```

Expected: `ModuleNotFoundError: No module named 'townlet.config.items_config'`

### Step 3: Write minimal items DTO implementation

```python
# src/townlet/config/items_config.py

"""Items configuration DTOs.

Two-tier structure:
1. Experiment-level catalog (ItemsCatalogConfig): Item types, intrinsic properties
2. Level-level appearance (ItemsAppearanceConfig): Spawn rules, inventory settings
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ============================================================================
# Inventory Configuration
# ============================================================================


class InventoryConfig(BaseModel):
    """Inventory capacity configuration (level-scoped)."""

    model_config = ConfigDict(extra="forbid")

    max_items_per_agent: int = Field(
        description="Maximum items each agent can hold simultaneously (REQUIRED, no defaults)"
    )

    @field_validator("max_items_per_agent")
    @classmethod
    def validate_max_items(cls, v: int) -> int:
        """Enforce Phase 1 limit: max_items_per_agent <= 3."""
        if v < 0:
            raise ValueError("max_items_per_agent must be non-negative")
        if v > 3:
            raise ValueError(
                f"Phase 1 limit: max_items_per_agent must be <= 3, got {v}. "
                f"Increase requires Phase 3+ (observation layout redesign)."
            )
        return v


# ============================================================================
# Item Interaction Effects (Phase 1: opaque dicts)
# ============================================================================


class ItemInteractionEffectConfig(BaseModel):
    """Item interaction effects (Phase 1: opaque YAML dict, not validated).

    Phase 1: Accept effects as raw dicts, defer validation to Phase 3 runtime.
    Phase 3: Parse effects into structured configs (bar deltas, VFS updates, etc.).
    """

    model_config = ConfigDict(extra="allow")  # Allow arbitrary fields

    # Phase 1: All fields optional, stored as-is
    bars: list[dict[str, Any]] | None = Field(
        default=None,
        description="Bar effects (Phase 3: validated structure)",
    )
    agent_vfs: list[dict[str, Any]] | None = Field(
        default=None,
        description="Agent VFS effects (Phase 3: validated structure)",
    )
    item_vfs: list[dict[str, Any]] | None = Field(
        default=None,
        description="Item VFS effects (Phase 3: validated structure)",
    )
    global_vfs: list[dict[str, Any]] | None = Field(
        default=None,
        description="Global VFS effects (Phase 3: validated structure)",
    )


class ItemInteractionsConfig(BaseModel):
    """Item interaction definitions (pickup/use/drop effects)."""

    model_config = ConfigDict(extra="forbid")

    pickup: ItemInteractionEffectConfig | None = Field(
        default=None,
        description="Effects when item picked up (GET action)",
    )
    use: ItemInteractionEffectConfig | None = Field(
        default=None,
        description="Effects when item used (USE_SLOT_N action)",
    )
    drop: ItemInteractionEffectConfig | None = Field(
        default=None,
        description="Effects when item dropped (DROP_SLOT_N action)",
    )

    # Phase 1: No item-scoped custom commands
    # Phase 2+: May add local_commands, inventory_commands fields


# ============================================================================
# Item Catalog (Experiment-Level)
# ============================================================================


class ItemTypeConfig(BaseModel):
    """Item type definition (experiment-scoped catalog entry)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        description="Unique item type identifier (referenced by spawn rules)"
    )
    name: str = Field(
        description="Human-readable item name"
    )
    icon: str = Field(
        description="Emoji or icon for UI rendering"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Semantic tags for filtering/grouping",
    )
    vfs_profiles: list[str] = Field(
        default_factory=list,
        description="VFS profile IDs this item uses (references vfs_profiles.yaml)",
    )
    interactions: ItemInteractionsConfig = Field(
        default_factory=ItemInteractionsConfig,
        description="Interaction effects (pickup/use/drop)",
    )

    @field_validator("vfs_profiles")
    @classmethod
    def validate_vfs_profile_count(cls, v: list[str]) -> list[str]:
        """Enforce Phase 1 limit: max 5 VFS profiles per item."""
        MAX_VFS_PROFILES_PER_ITEM = 5
        if len(v) > MAX_VFS_PROFILES_PER_ITEM:
            raise ValueError(
                f"Phase 1 limit: Item can have at most {MAX_VFS_PROFILES_PER_ITEM} VFS profiles, "
                f"got {len(v)}. Reduce profile count."
            )
        return v


class ItemsCatalogConfig(BaseModel):
    """Root configuration for item catalog (experiment-scoped).

    File: configs/<experiment>/items.yaml
    """

    model_config = ConfigDict(extra="forbid")

    version: str = Field(
        description="Config schema version (currently '1.0')"
    )
    item_types: list[ItemTypeConfig] = Field(
        default_factory=list,
        description="Item type definitions (catalog)",
    )

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate config version is supported."""
        if v != "1.0":
            raise ValueError(
                f"Unsupported items.yaml (catalog) version: {v}. Expected '1.0'."
            )
        return v

    @model_validator(mode="after")
    def validate_unique_ids(self) -> "ItemsCatalogConfig":
        """Ensure item type IDs are unique."""
        ids = [item.id for item in self.item_types]
        duplicates = [id_ for id_ in ids if ids.count(id_) > 1]
        if duplicates:
            raise ValueError(
                f"Duplicate item type IDs: {set(duplicates)}. "
                f"All item IDs must be unique in catalog."
            )
        return self

    @model_validator(mode="after")
    def enforce_phase1_limits(self) -> "ItemsCatalogConfig":
        """Enforce Phase 1 performance limits."""
        MAX_ITEM_TYPES = 10

        if len(self.item_types) > MAX_ITEM_TYPES:
            raise ValueError(
                f"Too many item types: {len(self.item_types)} > {MAX_ITEM_TYPES}. "
                f"Phase 1 limit. Reduce catalog size."
            )
        return self


# ============================================================================
# Item Spawn Configuration (Level-Level)
# ============================================================================


class ItemSpawnPlacementConfig(BaseModel):
    """Item spawn placement configuration."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["random", "fixed", "grid", "scripted"] = Field(
        description="Placement strategy"
    )
    positions: list[list[float]] = Field(
        default_factory=list,
        description="Fixed positions (required for 'fixed' and 'scripted' modes)",
    )

    @model_validator(mode="after")
    def validate_positions(self) -> "ItemSpawnPlacementConfig":
        """Validate positions field for fixed/scripted modes."""
        if self.mode in ("fixed", "scripted"):
            if not self.positions:
                raise ValueError(
                    f"Placement mode '{self.mode}' requires non-empty 'positions' field"
                )
        return self


class ItemSpawnScheduleConfig(BaseModel):
    """Item spawn schedule configuration (Phase 1: opaque params)."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["once", "time_window", "poisson", "normal"] = Field(
        description="Spawn schedule type"
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Schedule parameters (Phase 1: opaque dict, Phase 4: validated)",
    )

    # Phase 1: Accept params as opaque dict
    # Phase 4: Add validation for each schedule kind


class ItemSpawnLimitsConfig(BaseModel):
    """Item spawn limits (REQUIRED, no defaults)."""

    model_config = ConfigDict(extra="forbid")

    max_simultaneous: int = Field(
        description="Maximum simultaneous instances of this item type (REQUIRED)"
    )
    max_total: int = Field(
        description="Maximum total instances spawned during episode (REQUIRED)"
    )

    @field_validator("max_simultaneous", "max_total")
    @classmethod
    def validate_positive(cls, v: int) -> int:
        """Limits must be positive."""
        if v <= 0:
            raise ValueError(f"Spawn limit must be positive, got {v}")
        return v


class ItemSpawnLifecycleConfig(BaseModel):
    """Item lifecycle configuration (REQUIRED, no defaults)."""

    model_config = ConfigDict(extra="forbid")

    duration_steps: int = Field(
        description="How long item exists before despawning (REQUIRED, -1 = forever)"
    )
    cooldown_steps: int = Field(
        description="Cooldown before respawning (REQUIRED, 0 = immediate)"
    )

    @field_validator("duration_steps", "cooldown_steps")
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        """Lifecycle values must be non-negative or -1 (forever)."""
        if v < -1:
            raise ValueError(f"Lifecycle value must be >= -1, got {v}")
        return v


class ItemSpawnConditionConfig(BaseModel):
    """Item spawn condition (Phase 1: opaque, not evaluated)."""

    model_config = ConfigDict(extra="allow")  # Allow arbitrary condition fields

    when: str = Field(
        description="Condition predicate (Phase 1: stored as string, Phase 4: evaluated)"
    )
    # Phase 4: Parse 'when' field as VFS/bar/affordance predicate


class ItemSpawnRuleConfig(BaseModel):
    """Item spawn rule definition (level-scoped)."""

    model_config = ConfigDict(extra="forbid")

    type_id: str = Field(
        description="Item type ID from catalog (must exist in items.yaml catalog)"
    )
    placement: ItemSpawnPlacementConfig = Field(
        description="Where items spawn"
    )
    schedule: ItemSpawnScheduleConfig = Field(
        description="When items spawn"
    )
    limits: ItemSpawnLimitsConfig = Field(
        description="Spawn limits (max simultaneous, max total)"
    )
    lifecycle: ItemSpawnLifecycleConfig = Field(
        description="Item lifetime and cooldown"
    )
    priority: int = Field(
        description="Spawn priority (higher = spawns first when conflicting)"
    )
    conditions: list[ItemSpawnConditionConfig] = Field(
        default_factory=list,
        description="Spawn conditions (Phase 1: stored, Phase 4: evaluated)",
    )


class ItemsAppearanceConfig(BaseModel):
    """Root configuration for item appearance (level-scoped).

    File: configs/<experiment>/levels/<level>/items.yaml
    """

    model_config = ConfigDict(extra="forbid")

    version: str = Field(
        description="Config schema version (currently '1.0')"
    )
    inventory: InventoryConfig = Field(
        description="Inventory capacity settings"
    )
    spawn_rules: list[ItemSpawnRuleConfig] = Field(
        default_factory=list,
        description="Item spawn rules for this level",
    )

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate config version is supported."""
        if v != "1.0":
            raise ValueError(
                f"Unsupported items.yaml (appearance) version: {v}. Expected '1.0'."
            )
        return v

    @model_validator(mode="after")
    def enforce_phase1_limits(self) -> "ItemsAppearanceConfig":
        """Enforce Phase 1 performance limits."""
        MAX_SPAWN_RULES = 10

        if len(self.spawn_rules) > MAX_SPAWN_RULES:
            raise ValueError(
                f"Too many spawn rules: {len(self.spawn_rules)} > {MAX_SPAWN_RULES}. "
                f"Phase 1 limit. Reduce spawn rule count."
            )
        return self
```

### Step 4: Run tests to verify they pass

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=src:tests uv run pytest tests/test_townlet/unit/config/test_items_config.py -v
```

Expected: All tests PASS

### Step 5: Commit

```bash
git add src/townlet/config/items_config.py tests/test_townlet/unit/config/test_items_config.py
git commit -m "feat(config): add Items DTOs (catalog + appearance)

- ItemsCatalogConfig (experiment-level): item types, interactions, VFS refs
- ItemsAppearanceConfig (level-level): spawn rules, inventory settings
- ItemTypeConfig with VFS profile references (max 5)
- ItemSpawnRuleConfig with placement/schedule/limits/lifecycle
- Phase 1 limits: max 10 types, max 3 items/agent, max 10 spawn rules
- Effects/schedules stored as opaque dicts (Phase 3+ validation)
- Comprehensive tests (13 test cases)
"
```

---

## Task 3: Extend CompiledUniverse with Catalog Fields

**Files:**
- Modify: `src/townlet/universe/compiled.py`
- Test: `tests/test_townlet/unit/universe/test_compiled_universe.py`

### Step 1: Write failing test for new fields

```python
# tests/test_townlet/unit/universe/test_compiled_universe.py

"""Tests for CompiledUniverse extensions (Items & VFS Profiles)."""

import pytest

from townlet.universe.compiled import CompiledUniverse
from townlet.config.vfs_profiles_config import VFSProfilesConfig
from townlet.config.items_config import ItemsCatalogConfig


class TestCompiledUniverseExtensions:
    """Tests for Items & VFS Profiles fields in CompiledUniverse."""

    def test_vfs_profile_catalog_field(self):
        """CompiledUniverse should have vfs_profile_catalog field."""
        vfs_profiles = VFSProfilesConfig(
            version="1.0",
            global_profiles=[],
            agent_profiles=[],
            item_profiles=[],
        )
        # Minimal CompiledUniverse construction
        universe = CompiledUniverse(
            # ... existing required fields ...
            vfs_profile_catalog=vfs_profiles,
        )
        assert universe.vfs_profile_catalog == vfs_profiles

    def test_item_catalog_field(self):
        """CompiledUniverse should have item_catalog field."""
        item_catalog = ItemsCatalogConfig(
            version="1.0",
            item_types=[],
        )
        universe = CompiledUniverse(
            # ... existing required fields ...
            item_catalog=item_catalog,
        )
        assert universe.item_catalog == item_catalog

    def test_catalogs_optional(self):
        """Catalogs should be optional (None if items not used)."""
        universe = CompiledUniverse(
            # ... existing required fields ...
            vfs_profile_catalog=None,
            item_catalog=None,
        )
        assert universe.vfs_profile_catalog is None
        assert universe.item_catalog is None
```

### Step 2: Run test to verify it fails

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=src:tests uv run pytest tests/test_townlet/unit/universe/test_compiled_universe.py::TestCompiledUniverseExtensions::test_vfs_profile_catalog_field -v
```

Expected: `TypeError: __init__() got an unexpected keyword argument 'vfs_profile_catalog'`

### Step 3: Modify CompiledUniverse to add new fields

Find the `CompiledUniverse` dataclass in `src/townlet/universe/compiled.py` and add:

```python
# src/townlet/universe/compiled.py

from dataclasses import dataclass, field
from typing import Any

from townlet.config.vfs_profiles_config import VFSProfilesConfig
from townlet.config.items_config import ItemsCatalogConfig, ItemsAppearanceConfig

# ... existing imports ...


@dataclass
class CompiledUniverse:
    """Compiled universe metadata (output of UniverseCompiler).

    Phase 1 Extensions (Items & VFS Profiles):
    - vfs_profile_catalog: VFS profile definitions (global/agent/item scopes)
    - item_catalog: Item type catalog (experiment-level)
    - item_spawn_plans: Per-level spawn rules (level-level)
    """

    # ... existing fields (substrate, bars, affordances, etc.) ...

    # Phase 1: Items & VFS Profiles catalogs (metadata-only, no runtime)
    vfs_profile_catalog: VFSProfilesConfig | None = field(default=None)
    item_catalog: ItemsCatalogConfig | None = field(default=None)
    item_spawn_plans: dict[str, ItemsAppearanceConfig] | None = field(default=None)
    # item_spawn_plans: {level_name: ItemsAppearanceConfig}

    # Note: item_spawn_plans stored per level, not compiled into single structure yet
    # Phase 3 will compile spawn plans into runtime-friendly data structure
```

### Step 4: Run tests to verify they pass

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=src:tests uv run pytest tests/test_townlet/unit/universe/test_compiled_universe.py::TestCompiledUniverseExtensions -v
```

Expected: All tests PASS

### Step 5: Commit

```bash
git add src/townlet/universe/compiled.py tests/test_townlet/unit/universe/test_compiled_universe.py
git commit -m "feat(universe): extend CompiledUniverse with VFS/Items catalogs

- Add vfs_profile_catalog field (VFSProfilesConfig | None)
- Add item_catalog field (ItemsCatalogConfig | None)
- Add item_spawn_plans field (dict[level_name, ItemsAppearanceConfig] | None)
- Fields optional (None if items/VFS not used in config)
- Tests verify new fields accessible
"
```

---

## Task 4: Extend UniverseCompiler with Load Stages

**Files:**
- Modify: `src/townlet/universe/compiler.py`
- Test: `tests/test_townlet/unit/universe/test_compiler_items_vfs.py`

### Step 1: Write failing test for VFS profiles loading

```python
# tests/test_townlet/unit/universe/test_compiler_items_vfs.py

"""Tests for UniverseCompiler Items & VFS Profiles integration."""

import pytest
from pathlib import Path
import yaml

from townlet.universe.compiler import UniverseCompiler
from townlet.config.vfs_profiles_config import VFSProfilesConfig
from townlet.config.items_config import ItemsCatalogConfig


class TestCompilerVFSProfilesLoading:
    """Tests for loading vfs_profiles.yaml."""

    def test_load_vfs_profiles_minimal(self, tmp_path: Path):
        """Load minimal vfs_profiles.yaml."""
        config_dir = tmp_path / "test_experiment"
        config_dir.mkdir()

        vfs_profiles_yaml = config_dir / "vfs_profiles.yaml"
        vfs_profiles_yaml.write_text(
            """
version: "1.0"
global_profiles:
  - id: test_global
    scope: global
    type: scalar
    initial_value: 1.0
agent_profiles: []
item_profiles: []
"""
        )

        compiler = UniverseCompiler(config_dir)
        vfs_config = compiler.load_vfs_profiles()

        assert vfs_config.version == "1.0"
        assert len(vfs_config.global_profiles) == 1
        assert vfs_config.global_profiles[0].id == "test_global"

    def test_vfs_profiles_optional(self, tmp_path: Path):
        """If vfs_profiles.yaml missing, return None (not an error)."""
        config_dir = tmp_path / "test_experiment"
        config_dir.mkdir()

        compiler = UniverseCompiler(config_dir)
        vfs_config = compiler.load_vfs_profiles()

        assert vfs_config is None

    def test_vfs_profiles_validation_errors(self, tmp_path: Path):
        """Invalid vfs_profiles.yaml raises ValidationError."""
        config_dir = tmp_path / "test_experiment"
        config_dir.mkdir()

        vfs_profiles_yaml = config_dir / "vfs_profiles.yaml"
        vfs_profiles_yaml.write_text(
            """
version: "1.0"
global_profiles:
  - id: bad_profile
    scope: global
    type: scalar
    expression: "time >= 20"  # FORBIDDEN in Phase 1
"""
        )

        compiler = UniverseCompiler(config_dir)
        with pytest.raises(Exception) as exc_info:  # ValidationError propagates
            compiler.load_vfs_profiles()
        assert "expression" in str(exc_info.value).lower()


class TestCompilerItemsCatalogLoading:
    """Tests for loading items.yaml catalog."""

    def test_load_items_catalog_minimal(self, tmp_path: Path):
        """Load minimal items.yaml catalog."""
        config_dir = tmp_path / "test_experiment"
        config_dir.mkdir()

        items_yaml = config_dir / "items.yaml"
        items_yaml.write_text(
            """
version: "1.0"
item_types:
  - id: umbrella
    name: Umbrella
    icon: ☂️
    tags: []
    vfs_profiles: []
    interactions: {}
"""
        )

        compiler = UniverseCompiler(config_dir)
        catalog = compiler.load_items_catalog()

        assert catalog.version == "1.0"
        assert len(catalog.item_types) == 1
        assert catalog.item_types[0].id == "umbrella"

    def test_items_catalog_optional(self, tmp_path: Path):
        """If items.yaml missing, return None (not an error)."""
        config_dir = tmp_path / "test_experiment"
        config_dir.mkdir()

        compiler = UniverseCompiler(config_dir)
        catalog = compiler.load_items_catalog()

        assert catalog is None


class TestCompilerCrossValidation:
    """Tests for cross-validation between configs."""

    def test_item_vfs_profile_references_validated(self, tmp_path: Path):
        """Items referencing nonexistent VFS profiles raises error."""
        config_dir = tmp_path / "test_experiment"
        config_dir.mkdir()

        # VFS profiles with one profile
        vfs_profiles_yaml = config_dir / "vfs_profiles.yaml"
        vfs_profiles_yaml.write_text(
            """
version: "1.0"
global_profiles: []
agent_profiles: []
item_profiles:
  - id: item_durability
    scope: item
    type: scalar
    initial_value: 1.0
"""
        )

        # Items catalog referencing WRONG profile ID
        items_yaml = config_dir / "items.yaml"
        items_yaml.write_text(
            """
version: "1.0"
item_types:
  - id: umbrella
    name: Umbrella
    icon: ☂️
    tags: []
    vfs_profiles: ["nonexistent_profile"]  # ERROR: not in vfs_profiles.yaml
    interactions: {}
"""
        )

        compiler = UniverseCompiler(config_dir)
        with pytest.raises(Exception) as exc_info:
            compiler.validate_item_vfs_references()
        assert "nonexistent_profile" in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()
```

### Step 2: Run test to verify it fails

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=src:tests uv run pytest tests/test_townlet/unit/universe/test_compiler_items_vfs.py::TestCompilerVFSProfilesLoading::test_load_vfs_profiles_minimal -v
```

Expected: `AttributeError: 'UniverseCompiler' object has no attribute 'load_vfs_profiles'`

### Step 3: Add load methods to UniverseCompiler

```python
# src/townlet/universe/compiler.py

from pathlib import Path
import yaml
from pydantic import ValidationError

from townlet.config.vfs_profiles_config import VFSProfilesConfig
from townlet.config.items_config import ItemsCatalogConfig, ItemsAppearanceConfig


class UniverseCompiler:
    """Universe configuration compiler with Items & VFS Profiles support."""

    def __init__(self, config_dir: Path):
        self.config_dir = Path(config_dir)
        # ... existing initialization ...

    # ========================================================================
    # Phase 1: VFS Profiles Loading
    # ========================================================================

    def load_vfs_profiles(self) -> VFSProfilesConfig | None:
        """Load vfs_profiles.yaml from experiment directory.

        Returns:
            VFSProfilesConfig if file exists, None otherwise.

        Raises:
            ValidationError: If YAML is invalid or violates Phase 1 constraints.
        """
        vfs_profiles_path = self.config_dir / "vfs_profiles.yaml"

        if not vfs_profiles_path.exists():
            return None

        with open(vfs_profiles_path) as f:
            data = yaml.safe_load(f)

        try:
            return VFSProfilesConfig(**data)
        except ValidationError as e:
            raise ValidationError(
                f"Invalid vfs_profiles.yaml at {vfs_profiles_path}:\n{e}"
            ) from e

    # ========================================================================
    # Phase 1: Items Catalog Loading
    # ========================================================================

    def load_items_catalog(self) -> ItemsCatalogConfig | None:
        """Load items.yaml catalog from experiment directory.

        Returns:
            ItemsCatalogConfig if file exists, None otherwise.

        Raises:
            ValidationError: If YAML is invalid or violates Phase 1 constraints.
        """
        items_catalog_path = self.config_dir / "items.yaml"

        if not items_catalog_path.exists():
            return None

        with open(items_catalog_path) as f:
            data = yaml.safe_load(f)

        try:
            return ItemsCatalogConfig(**data)
        except ValidationError as e:
            raise ValidationError(
                f"Invalid items.yaml (catalog) at {items_catalog_path}:\n{e}"
            ) from e

    def load_items_appearance(self, level_name: str) -> ItemsAppearanceConfig | None:
        """Load items.yaml appearance from level directory.

        Args:
            level_name: Level directory name (e.g., "L0_0_minimal")

        Returns:
            ItemsAppearanceConfig if file exists, None otherwise.

        Raises:
            ValidationError: If YAML is invalid or violates Phase 1 constraints.
        """
        level_dir = self.config_dir / "levels" / level_name
        items_appearance_path = level_dir / "items.yaml"

        if not items_appearance_path.exists():
            return None

        with open(items_appearance_path) as f:
            data = yaml.safe_load(f)

        try:
            return ItemsAppearanceConfig(**data)
        except ValidationError as e:
            raise ValidationError(
                f"Invalid items.yaml (appearance) at {items_appearance_path}:\n{e}"
            ) from e

    # ========================================================================
    # Phase 1: Cross-Validation
    # ========================================================================

    def validate_item_vfs_references(
        self,
        item_catalog: ItemsCatalogConfig | None,
        vfs_profiles: VFSProfilesConfig | None,
    ) -> None:
        """Validate that item VFS profile references exist in vfs_profiles.yaml.

        Args:
            item_catalog: Loaded items catalog (or None)
            vfs_profiles: Loaded VFS profiles (or None)

        Raises:
            ValueError: If item references nonexistent VFS profile.
        """
        if item_catalog is None:
            return  # No items, nothing to validate

        if vfs_profiles is None and any(
            item.vfs_profiles for item in item_catalog.item_types
        ):
            raise ValueError(
                "Items reference VFS profiles but vfs_profiles.yaml is missing. "
                "Create vfs_profiles.yaml with item_profiles section."
            )

        if vfs_profiles is not None:
            # Build set of all profile IDs
            all_profile_ids = {p.id for p in vfs_profiles.item_profiles}
            all_profile_ids |= {p.id for p in vfs_profiles.global_profiles}
            all_profile_ids |= {p.id for p in vfs_profiles.agent_profiles}

            # Check each item's vfs_profiles references
            for item in item_catalog.item_types:
                for profile_id in item.vfs_profiles:
                    if profile_id not in all_profile_ids:
                        raise ValueError(
                            f"Item '{item.id}' references VFS profile '{profile_id}' "
                            f"not found in vfs_profiles.yaml. "
                            f"Available profiles: {sorted(all_profile_ids)}"
                        )

    def validate_spawn_rule_item_references(
        self,
        spawn_rules: list,  # ItemSpawnRuleConfig list
        item_catalog: ItemsCatalogConfig | None,
    ) -> None:
        """Validate that spawn rules reference existing item types.

        Args:
            spawn_rules: List of spawn rules from level
            item_catalog: Loaded items catalog (or None)

        Raises:
            ValueError: If spawn rule references nonexistent item type.
        """
        if not spawn_rules:
            return

        if item_catalog is None:
            raise ValueError(
                "Spawn rules defined but items.yaml catalog is missing. "
                "Create items.yaml catalog with item types."
            )

        catalog_ids = {item.id for item in item_catalog.item_types}

        for rule in spawn_rules:
            if rule.type_id not in catalog_ids:
                raise ValueError(
                    f"Spawn rule references item type '{rule.type_id}' "
                    f"not found in items.yaml catalog. "
                    f"Available types: {sorted(catalog_ids)}"
                )

    # ========================================================================
    # Phase 1: Compile Integration (add to existing compile() method)
    # ========================================================================

    def compile(self) -> CompiledUniverse:
        """Compile universe configuration.

        Phase 1 Extensions:
        - Load vfs_profiles.yaml (optional)
        - Load items.yaml catalog (optional)
        - Load per-level items.yaml appearance (optional)
        - Validate VFS profile references
        - Validate spawn rule item references
        """
        # ... existing compilation steps ...

        # NEW: Load VFS profiles
        vfs_profiles = self.load_vfs_profiles()

        # NEW: Load items catalog
        item_catalog = self.load_items_catalog()

        # NEW: Cross-validate VFS references
        self.validate_item_vfs_references(item_catalog, vfs_profiles)

        # NEW: Load per-level items appearance
        item_spawn_plans = {}
        for level_name in self.list_levels():  # Assuming this method exists
            appearance = self.load_items_appearance(level_name)
            if appearance is not None:
                # Validate spawn rule references
                self.validate_spawn_rule_item_references(
                    appearance.spawn_rules, item_catalog
                )
                item_spawn_plans[level_name] = appearance

        # ... existing compilation steps ...

        return CompiledUniverse(
            # ... existing fields ...
            vfs_profile_catalog=vfs_profiles,
            item_catalog=item_catalog,
            item_spawn_plans=item_spawn_plans if item_spawn_plans else None,
        )
```

### Step 4: Run tests to verify they pass

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=src:tests uv run pytest tests/test_townlet/unit/universe/test_compiler_items_vfs.py -v
```

Expected: All tests PASS

### Step 5: Commit

```bash
git add src/townlet/universe/compiler.py tests/test_townlet/unit/universe/test_compiler_items_vfs.py
git commit -m "feat(compiler): add Items & VFS Profiles load stages

- load_vfs_profiles(): Load vfs_profiles.yaml (optional)
- load_items_catalog(): Load items.yaml catalog (optional)
- load_items_appearance(): Load per-level items.yaml (optional)
- validate_item_vfs_references(): Check VFS profile refs exist
- validate_spawn_rule_item_references(): Check item type refs exist
- Integrate into compile() method with cross-validation
- Comprehensive tests (9 test cases)
"
```

---

## Task 5: Create Reference Config Examples

**Files:**
- Create: `configs/reference_config/vfs_profiles.yaml`
- Create: `configs/reference_config/items_catalog.yaml`
- Create: `configs/reference_config/items_appearance.yaml`

### Step 1: Write vfs_profiles.yaml example

```yaml
# configs/reference_config/vfs_profiles.yaml

# VFS Profiles Configuration (Experiment-Scoped)
# Phase 1: Static variables only (initial_value field)
# Phase 2+: Expression-based variables (expression, deps fields)

version: "1.0"

# Global VFS profiles (world-level state, shared by all agents)
global_profiles:
  - id: "debug_flag"
    scope: "global"
    type: "scalar"
    initial_value: 0.0
    description: "Debug toggle for visualizations"
    normalization:
      kind: "minmax"
      min: 0.0
      max: 1.0

  # FUTURE (Phase 2+): Expression-based global profiles
  # - id: "is_night"
  #   scope: "global"
  #   type: "scalar"
  #   expression: "time_of_day >= 20 || time_of_day < 6"
  #   deps:
  #     bars: ["time"]
  #   initial_value: 0.0

# Agent VFS profiles (per-agent state, replicated across all agents)
agent_profiles:
  - id: "agent_custom_flag"
    scope: "agent"
    type: "scalar"
    initial_value: 1.0
    description: "Per-agent custom state (placeholder for Phase 2 expressions)"

  # FUTURE (Phase 2+): Expression-based agent profiles
  # - id: "is_heavily_loaded"
  #   scope: "agent"
  #   type: "scalar"
  #   expression: "inventory_weight > 0.8"
  #   deps:
  #     vfs: ["inventory_weight"]
  #   initial_value: 0.0

# Item VFS profiles (per-item instance state)
item_profiles:
  - id: "item_durability"
    scope: "item"
    type: "scalar"
    initial_value: 1.0
    description: "Item durability (1.0 = pristine, 0.0 = broken)"
    normalization:
      kind: "minmax"
      min: 0.0
      max: 1.0

  - id: "item_wetness_resistance"
    scope: "item"
    type: "scalar"
    initial_value: 0.5
    description: "Resistance to rain/water damage"

  # FUTURE (Phase 2+): Expression-based item profiles
  # - id: "item_is_broken"
  #   scope: "item"
  #   type: "scalar"
  #   expression: "item_durability <= 0.0"
  #   deps:
  #     vfs: ["item_durability"]
  #   initial_value: 0.0

# Phase 1 Limits (enforced by compiler):
# - max_global_profiles: 20
# - max_agent_profiles: 20
# - max_item_profiles: unlimited (limited via max_vfs_profiles_per_item per item type)
```

### Step 2: Write items_catalog.yaml example

```yaml
# configs/reference_config/items_catalog.yaml

# Items Catalog Configuration (Experiment-Scoped)
# Defines intrinsic item properties shared across all curriculum levels

version: "1.0"

item_types:
  - id: "umbrella"
    name: "Umbrella"
    icon: "☂️"
    tags: ["weather", "protection", "tool"]

    # VFS profiles this item uses (references vfs_profiles.yaml)
    vfs_profiles:
      - "item_durability"
      - "item_wetness_resistance"

    # Interaction effects (Phase 1: opaque dicts, Phase 3: validated)
    interactions:
      # Triggered by GET action
      pickup:
        bars: []
        agent_vfs: []

      # Triggered by USE_SLOT_N action
      use:
        bars:
          - name: "mood"
            delta: 0.1  # Using umbrella improves mood slightly
        agent_vfs:
          - name: "is_protected_from_rain"
            set_value: true
        item_vfs:
          - name: "item_durability"
            delta: -0.05  # Durability decreases with use

      # Triggered by DROP_SLOT_N action
      drop:
        agent_vfs:
          - name: "is_protected_from_rain"
            set_value: false

  - id: "medkit"
    name: "Medical Kit"
    icon: "🏥"
    tags: ["health", "consumable"]

    vfs_profiles: []  # No custom VFS state

    interactions:
      pickup: {}

      use:
        bars:
          - name: "health"
            delta: 0.3  # Restore 30% health
        # Consumable: item removed after use (handled by runtime in Phase 3)

      drop: {}

# Phase 1 Limits (enforced by compiler):
# - max_item_types: 10
# - max_vfs_profiles_per_item: 5
```

### Step 3: Write items_appearance.yaml example

```yaml
# configs/reference_config/items_appearance.yaml

# Items Appearance Configuration (Level-Scoped)
# Controls which items spawn, where, and how often in this curriculum level

version: "1.0"

# Inventory capacity (REQUIRED, no defaults)
inventory:
  max_items_per_agent: 3  # Phase 1 limit: max 3

# Spawn rules (references item types from catalog)
spawn_rules:
  - type_id: "umbrella"  # Must exist in items.yaml catalog

    # Where items spawn
    placement:
      mode: "random"  # random | fixed | grid | scripted
      positions: []   # Empty for random, required for fixed/scripted

    # When items spawn
    schedule:
      kind: "once"  # once | time_window | poisson | normal
      params: {}    # Phase 1: opaque dict, Phase 4: validated

    # Spawn limits (REQUIRED, no defaults)
    limits:
      max_simultaneous: 3   # Max 3 umbrellas in world at once
      max_total: 10         # Max 10 umbrella spawns per episode

    # Item lifecycle (REQUIRED, no defaults)
    lifecycle:
      duration_steps: 50  # Item despawns after 50 steps (-1 = forever)
      cooldown_steps: 20  # 20 steps before respawning (0 = immediate)

    # Spawn priority (higher = spawns first when conflicts)
    priority: 10

    # Spawn conditions (Phase 1: stored as metadata, Phase 4: evaluated)
    conditions: []
    # FUTURE (Phase 4):
    # conditions:
    #   - when: "vfs:is_raining"
    #     equals: true

  - type_id: "medkit"

    placement:
      mode: "fixed"
      positions: [[2.0, 2.0], [5.0, 5.0]]  # Two fixed medkit locations

    schedule:
      kind: "time_window"
      params:
        start_step: 10
        end_step: 100

    limits:
      max_simultaneous: 2
      max_total: 5

    lifecycle:
      duration_steps: -1  # Medkits never despawn
      cooldown_steps: 0

    priority: 5
    conditions: []

# Phase 1 Limits (enforced by compiler):
# - max_items_per_agent: 3
# - max_spawn_rules: 10
```

### Step 4: Commit reference configs

```bash
git add configs/reference_config/vfs_profiles.yaml configs/reference_config/items_catalog.yaml configs/reference_config/items_appearance.yaml
git commit -m "docs(config): add Items & VFS Profiles reference examples

- vfs_profiles.yaml: Global/agent/item profiles with Phase 2 future comments
- items_catalog.yaml: Umbrella and medkit examples with VFS refs
- items_appearance.yaml: Spawn rules, inventory, limits examples
- All examples show Phase 1 constraints (static variables, opaque effects)
"
```

---

## Task 6: Update Schema Documentation

**Files:**
- Create: `docs/config-schemas/vfs-profiles.md`
- Create: `docs/config-schemas/items.md`

### Step 1: Write vfs-profiles.md

```markdown
# VFS Profiles Configuration Schema

**File:** `configs/<experiment>/vfs_profiles.yaml` (experiment-scoped)

**Purpose:** Define Variable & Feature System (VFS) profiles for global, agent, and item state.

**Phase 1 Status:** Static variables only (`initial_value` field). Expression-based variables (`expression`, `deps`) deferred to Phase 2+ (BAC integration).

---

## Schema

### Root Object: `VFSProfilesConfig`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| version | string | Yes | Config version (currently "1.0") |
| global_profiles | list[GlobalVFSProfileConfig] | No | Global VFS profiles (world state) |
| agent_profiles | list[AgentVFSProfileConfig] | No | Agent VFS profiles (per-agent state) |
| item_profiles | list[ItemVFSProfileConfig] | No | Item VFS profiles (per-item state) |

### VFSProfileConfig (Base)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique profile identifier |
| scope | enum | Yes | "global" \| "agent" \| "item" |
| type | enum | Yes | "scalar" \| "vec2i" \| "vec3i" \| "vecNi" \| "vecNf" \| "bool" |
| dims | int | Conditional | Required if type is vecNi/vecNf |
| initial_value | float \| int \| bool \| list | Yes | Static default value (Phase 1 only source) |
| normalization | NormalizationSpec | No | Observation normalization |
| description | string | No | Human-readable description |

**Phase 1 Forbidden Fields:** `expression`, `deps`, `update_on` (raise ValidationError if present)

### NormalizationSpec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| kind | enum | Yes | "minmax" \| "zscore" |
| min | float \| list[float] | If minmax | Minimum value(s) |
| max | float \| list[float] | If minmax | Maximum value(s) |
| mean | float \| list[float] | If zscore | Mean value(s) |
| std | float \| list[float] | If zscore | Standard deviation(s) |

---

## Phase 1 Limits

| Limit | Value | Enforcement |
|-------|-------|-------------|
| max_global_profiles | 20 | Compiler ValidationError |
| max_agent_profiles | 20 | Compiler ValidationError |
| max_item_profiles | Unlimited | Limited via max_vfs_profiles_per_item per item type |

---

## Examples

### Minimal Global Profile

```yaml
version: "1.0"
global_profiles:
  - id: "debug_flag"
    scope: "global"
    type: "scalar"
    initial_value: 0.0
agent_profiles: []
item_profiles: []
```

### Agent Profile with Normalization

```yaml
agent_profiles:
  - id: "agent_custom_state"
    scope: "agent"
    type: "scalar"
    initial_value: 0.5
    normalization:
      kind: "minmax"
      min: 0.0
      max: 1.0
    description: "Custom per-agent state"
```

### Item Profile (Durability)

```yaml
item_profiles:
  - id: "item_durability"
    scope: "item"
    type: "scalar"
    initial_value: 1.0
    normalization:
      kind: "minmax"
      min: 0.0
      max: 1.0
```

### Future (Phase 2+): Expression-Based Profile

```yaml
# PHASE 2+ ONLY (not supported in Phase 1)
global_profiles:
  - id: "is_night"
    scope: "global"
    type: "scalar"
    expression: "time_of_day >= 20 || time_of_day < 6"
    deps:
      bars: ["time"]
    initial_value: 0.0  # Fallback default
```

**Note:** Phase 1 will raise ValidationError if `expression` or `deps` fields present.

---

## Validation Rules

1. **Unique IDs:** All profile IDs must be unique across all scopes
2. **dims Field:** Required if type is vecNi/vecNf, forbidden otherwise
3. **initial_value:** REQUIRED in Phase 1 (no expression evaluation yet)
4. **Normalization:** min/max required for minmax, mean/std for zscore
5. **Phase 1 Guards:** Reject expression/deps/update_on fields

---

## See Also

- [Items Configuration](items.md) - Items reference VFS profiles
- [Variables Reference](../vfs-integration-guide.md) - VFS Phase 1 integration guide
```

### Step 2: Write items.md

```markdown
# Items Configuration Schema

**Files:**
- Experiment-level catalog: `configs/<experiment>/items.yaml`
- Level-level appearance: `configs/<experiment>/levels/<level>/items.yaml`

**Purpose:** Define item types, interactions, and spawn behavior.

**Phase 1 Status:** Metadata-only (effects and schedules stored as opaque dicts, validated in Phase 3+).

---

## Experiment-Level Catalog

**File:** `configs/<experiment>/items.yaml`

### Root Object: `ItemsCatalogConfig`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| version | string | Yes | Config version (currently "1.0") |
| item_types | list[ItemTypeConfig] | No | Item type definitions |

### ItemTypeConfig

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique item type identifier |
| name | string | Yes | Human-readable item name |
| icon | string | Yes | Emoji or icon for UI |
| tags | list[string] | No | Semantic tags (default: []) |
| vfs_profiles | list[string] | No | VFS profile IDs (refs vfs_profiles.yaml) |
| interactions | ItemInteractionsConfig | No | Pickup/use/drop effects |

### ItemInteractionsConfig

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| pickup | ItemInteractionEffectConfig | No | Effects when picked up (GET action) |
| use | ItemInteractionEffectConfig | No | Effects when used (USE_SLOT_N) |
| drop | ItemInteractionEffectConfig | No | Effects when dropped (DROP_SLOT_N) |

### ItemInteractionEffectConfig (Phase 1: Opaque)

Phase 1: All fields are opaque dicts (not validated)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| bars | list[dict] | No | Bar effects (Phase 3: validated) |
| agent_vfs | list[dict] | No | Agent VFS effects |
| item_vfs | list[dict] | No | Item VFS effects |
| global_vfs | list[dict] | No | Global VFS effects |

---

## Level-Level Appearance

**File:** `configs/<experiment>/levels/<level>/items.yaml`

### Root Object: `ItemsAppearanceConfig`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| version | string | Yes | Config version (currently "1.0") |
| inventory | InventoryConfig | Yes | Inventory capacity |
| spawn_rules | list[ItemSpawnRuleConfig] | No | Spawn rules (default: []) |

### InventoryConfig

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| max_items_per_agent | int | Yes | Max items per agent (NO DEFAULTS) |

### ItemSpawnRuleConfig

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type_id | string | Yes | Item type ID (refs catalog) |
| placement | ItemSpawnPlacementConfig | Yes | Where items spawn |
| schedule | ItemSpawnScheduleConfig | Yes | When items spawn |
| limits | ItemSpawnLimitsConfig | Yes | Spawn limits |
| lifecycle | ItemSpawnLifecycleConfig | Yes | Duration/cooldown |
| priority | int | Yes | Spawn priority |
| conditions | list[ItemSpawnConditionConfig] | No | Spawn conditions |

### ItemSpawnPlacementConfig

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| mode | enum | Yes | "random" \| "fixed" \| "grid" \| "scripted" |
| positions | list[list[float]] | Conditional | Required for fixed/scripted modes |

### ItemSpawnScheduleConfig (Phase 1: Opaque)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| kind | enum | Yes | "once" \| "time_window" \| "poisson" \| "normal" |
| params | dict | No | Schedule params (Phase 4: validated) |

### ItemSpawnLimitsConfig

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| max_simultaneous | int | Yes | Max simultaneous items (NO DEFAULTS) |
| max_total | int | Yes | Max total spawns per episode (NO DEFAULTS) |

### ItemSpawnLifecycleConfig

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| duration_steps | int | Yes | Item lifetime (-1 = forever, NO DEFAULTS) |
| cooldown_steps | int | Yes | Respawn cooldown (NO DEFAULTS) |

---

## Phase 1 Limits

| Limit | Value | Enforcement |
|-------|-------|-------------|
| max_item_types | 10 | Compiler ValidationError |
| max_items_per_agent | 3 | Compiler ValidationError |
| max_vfs_profiles_per_item | 5 | Compiler ValidationError |
| max_spawn_rules | 10 | Compiler ValidationError |

---

## Examples

See `configs/reference_config/items_catalog.yaml` and `items_appearance.yaml` for complete examples.

---

## Action Space Impact

When `max_items_per_agent > 0`, the action vocabulary automatically includes:

| Action | Index | Masking |
|--------|-------|---------|
| GET | 8 | Masked if no item at position |
| DROP_SLOT_0 | 9 | Masked if slot 0 empty |
| DROP_SLOT_1 | 10 | Masked if slot 1 empty |
| DROP_SLOT_2 | 11 | Masked if slot 2 empty |
| USE_SLOT_0 | 12 | Masked if slot 0 empty or no use effect |
| USE_SLOT_1 | 13 | Masked if slot 1 empty or no use effect |
| USE_SLOT_2 | 14 | Masked if slot 2 empty or no use effect |

Action vocabulary expansion: +7 actions (Grid2D: 8→15)

---

## See Also

- [VFS Profiles](vfs-profiles.md) - Items reference VFS profiles
- [Action Space](actions.md) - Item actions in global vocabulary
```

### Step 3: Commit documentation

```bash
git add docs/config-schemas/vfs-profiles.md docs/config-schemas/items.md
git commit -m "docs(schemas): add VFS Profiles and Items schema docs

- vfs-profiles.md: Complete schema reference with Phase 1 constraints
- items.md: Catalog + appearance schemas with limits and examples
- Both docs show Phase 2+ future features as comments
- Action space impact table in items.md
"
```

---

## Task 7: Integration Test (End-to-End)

**Files:**
- Test: `tests/test_townlet/integration/test_items_vfs_compiler_integration.py`

### Step 1: Write integration test

```python
# tests/test_townlet/integration/test_items_vfs_compiler_integration.py

"""End-to-end integration test for Items & VFS Profiles (Phase 1)."""

import pytest
from pathlib import Path
import yaml

from townlet.universe.compiler import UniverseCompiler


class TestItemsVFSCompilerIntegration:
    """Full pipeline test: Load configs → Compile → Validate catalogs in CompiledUniverse."""

    def test_full_pipeline_with_items_and_vfs(self, tmp_path: Path):
        """Complete pipeline: vfs_profiles.yaml + items.yaml → compiled catalogs."""
        config_dir = tmp_path / "test_experiment"
        config_dir.mkdir()
        levels_dir = config_dir / "levels"
        levels_dir.mkdir()
        level_dir = levels_dir / "L0_test"
        level_dir.mkdir()

        # Create vfs_profiles.yaml
        vfs_profiles_yaml = config_dir / "vfs_profiles.yaml"
        vfs_profiles_yaml.write_text(
            """
version: "1.0"
global_profiles:
  - id: global_debug
    scope: global
    type: scalar
    initial_value: 0.0
agent_profiles:
  - id: agent_state
    scope: agent
    type: scalar
    initial_value: 1.0
item_profiles:
  - id: item_durability
    scope: item
    type: scalar
    initial_value: 1.0
"""
        )

        # Create items.yaml catalog
        items_catalog_yaml = config_dir / "items.yaml"
        items_catalog_yaml.write_text(
            """
version: "1.0"
item_types:
  - id: umbrella
    name: Umbrella
    icon: ☂️
    tags: []
    vfs_profiles: [item_durability]
    interactions: {}
"""
        )

        # Create level items.yaml appearance
        level_items_yaml = level_dir / "items.yaml"
        level_items_yaml.write_text(
            """
version: "1.0"
inventory:
  max_items_per_agent: 3
spawn_rules:
  - type_id: umbrella
    placement:
      mode: random
      positions: []
    schedule:
      kind: once
      params: {}
    limits:
      max_simultaneous: 3
      max_total: 10
    lifecycle:
      duration_steps: 50
      cooldown_steps: 20
    priority: 10
    conditions: []
"""
        )

        # Create minimal substrate/environment configs (required for compilation)
        # ... (stub out remaining required configs) ...

        # Compile
        compiler = UniverseCompiler(config_dir)
        universe = compiler.compile()

        # Verify catalogs loaded
        assert universe.vfs_profile_catalog is not None
        assert len(universe.vfs_profile_catalog.global_profiles) == 1
        assert universe.vfs_profile_catalog.global_profiles[0].id == "global_debug"

        assert universe.item_catalog is not None
        assert len(universe.item_catalog.item_types) == 1
        assert universe.item_catalog.item_types[0].id == "umbrella"

        assert universe.item_spawn_plans is not None
        assert "L0_test" in universe.item_spawn_plans
        assert universe.item_spawn_plans["L0_test"].inventory.max_items_per_agent == 3

    def test_vfs_reference_validation_fails(self, tmp_path: Path):
        """Item referencing nonexistent VFS profile raises error during compilation."""
        config_dir = tmp_path / "test_experiment"
        config_dir.mkdir()

        # VFS with ONE profile
        vfs_profiles_yaml = config_dir / "vfs_profiles.yaml"
        vfs_profiles_yaml.write_text(
            """
version: "1.0"
global_profiles: []
agent_profiles: []
item_profiles:
  - id: item_durability
    scope: item
    type: scalar
    initial_value: 1.0
"""
        )

        # Items referencing WRONG profile
        items_catalog_yaml = config_dir / "items.yaml"
        items_catalog_yaml.write_text(
            """
version: "1.0"
item_types:
  - id: umbrella
    name: Umbrella
    icon: ☂️
    tags: []
    vfs_profiles: [nonexistent_profile]  # ERROR
    interactions: {}
"""
        )

        compiler = UniverseCompiler(config_dir)
        with pytest.raises(ValueError) as exc_info:
            compiler.compile()
        assert "nonexistent_profile" in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()
```

### Step 2: Run integration test

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=src:tests uv run pytest tests/test_townlet/integration/test_items_vfs_compiler_integration.py -v
```

Expected: All tests PASS

### Step 3: Commit integration test

```bash
git add tests/test_townlet/integration/test_items_vfs_compiler_integration.py
git commit -m "test(integration): add Items & VFS end-to-end compiler test

- Full pipeline: vfs_profiles.yaml + items.yaml → CompiledUniverse
- Validates catalogs loaded correctly
- Validates VFS reference checking (nonexistent profile fails)
- 2 integration test cases
"
```

---

## Completion Criteria

Phase 1 is complete when:

- [x] VFS Profiles DTO module created with tests
- [x] Items DTO module created with tests
- [x] CompiledUniverse extended with catalog fields
- [x] UniverseCompiler load stages implemented
- [x] Cross-validation (VFS refs, spawn rule refs) working
- [x] Reference config examples created
- [x] Schema documentation written
- [x] Integration test passing
- [ ] All unit tests passing
- [ ] Code review complete

---

## Final Verification

```bash
# Run all new tests
UV_CACHE_DIR=.uv-cache PYTHONPATH=src:tests uv run pytest tests/test_townlet/unit/config/test_vfs_profiles_config.py tests/test_townlet/unit/config/test_items_config.py tests/test_townlet/unit/universe/test_compiler_items_vfs.py tests/test_townlet/integration/test_items_vfs_compiler_integration.py -v

# Run full test suite (ensure no regressions)
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/ -v

# Verify linting
ruff check src/townlet/config/vfs_profiles_config.py src/townlet/config/items_config.py src/townlet/universe/compiler.py

# Verify formatting
ruff format --check src/townlet/
```

Expected: All tests PASS, no linting errors

---

## Final Commit

```bash
git add -A
git commit -m "feat(config): Phase 1 complete - Items & VFS Profiles DTOs + Compiler

Phase 1 Deliverables:
- VFS Profiles DTOs (global/agent/item scopes, static variables only)
- Items DTOs (catalog + appearance, two-tier config)
- CompiledUniverse catalog fields (vfs_profile_catalog, item_catalog, item_spawn_plans)
- UniverseCompiler load stages with cross-validation
- Reference config examples (vfs_profiles.yaml, items.yaml)
- Schema documentation (vfs-profiles.md, items.md)
- Comprehensive tests (30+ test cases, 100% coverage)

Phase 1 Limits Enforced:
- max_item_types: 10
- max_items_per_agent: 3
- max_vfs_profiles_per_item: 5
- max_vfs_profiles_global: 20
- max_vfs_profiles_agent: 20

No runtime changes. Metadata-only. Ready for Phase 2 (VFS Engine + DynObs).
"
```

---

## Next Phase

**Phase 2: VFS Engine + DynObs**

See: `docs/plans/vfs_uplift/2025-11-19-phase-2-vfs-engine-dynobs.md` (to be created)
