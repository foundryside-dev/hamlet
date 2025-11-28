# Task 3.1: Effects DTOs & Catalog - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the Effects system configuration DTOs and effect catalog compilation infrastructure.

**Architecture:** Pydantic DTOs for type-safe config loading. Effect catalog compiles effects.yaml into CompiledEffectCatalog with validated command pipelines. Reapply policies (stack/renew/merge/replace) enforced at config validation.

**Tech Stack:** Python 3.11+, Pydantic 2.x, YAML parsing

**Dependencies:** Task 1.1-1.4 (Expression Language complete)

**References:**
- Effects design: `docs/plans/vfs_uplift/2025-11-19-effects-system-design.md`
- Phase 3 overview: `docs/plans/vfs_uplift/2025-11-19-unified-world-compiler-plan.md`

---

## Task Breakdown

### Step 1: Create directory structure

**Action:** Set up the effects module directory

```bash
mkdir -p src/townlet/effects
mkdir -p src/townlet/config
mkdir -p configs/test/effects_smoke
mkdir -p tests/test_townlet/unit/effects
```

**Verify:**
```bash
ls -la src/townlet/effects/
ls -la tests/test_townlet/unit/effects/
```

Expected: Empty directories exist

---

### Step 2: Write failing test for ReapplyPolicy enum

**File:** `tests/test_townlet/unit/effects/test_effects_dto.py`

```python
"""Tests for Effects configuration DTOs."""
import pytest
from pydantic import ValidationError
from townlet.config.effects_config import ReapplyPolicy


def test_reapply_policy_enum():
    """ReapplyPolicy has exactly 4 values."""
    assert ReapplyPolicy.STACK.value == "stack"
    assert ReapplyPolicy.RENEW.value == "renew"
    assert ReapplyPolicy.MERGE.value == "merge"
    assert ReapplyPolicy.REPLACE.value == "replace"


def test_reapply_policy_case_insensitive():
    """ReapplyPolicy accepts mixed case strings."""
    assert ReapplyPolicy("stack") == ReapplyPolicy.STACK
    assert ReapplyPolicy("Stack") == ReapplyPolicy.STACK
    assert ReapplyPolicy("STACK") == ReapplyPolicy.STACK
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_effects_dto.py::test_reapply_policy_enum -v
```

**Expected:** FAIL - Module 'townlet.config.effects_config' not found

---

### Step 3: Implement ReapplyPolicy enum and EffectScope enum

**File:** `src/townlet/config/effects_config.py`

```python
"""Configuration DTOs for Effects system."""
from __future__ import annotations

import enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

__all__ = [
    "ReapplyPolicy",
    "EffectScope",
    "CommandConfig",
    "EffectDefinitionConfig",
    "EffectsConfig",
]


class ReapplyPolicy(str, enum.Enum):
    """Policy for handling multiple spawns of the same effect.

    - stack: Create independent instances (multiple timers)
    - renew: Refresh duration (single instance, timer resets)
    - merge: Increase intensity (single instance, intensity stacks)
    - replace: Clear old, spawn new (single instance, new replaces old)
    """

    STACK = "stack"
    RENEW = "renew"
    MERGE = "merge"
    REPLACE = "replace"

    @classmethod
    def _missing_(cls, value):
        """Case-insensitive lookup."""
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None


class EffectScope(str, enum.Enum):
    """Scope where effect can attach.

    - global: Single instance shared across all agents
    - agent: Per-agent effects (typical use case)
    - item: Per-item effects (e.g., "spoiled", "poisoned")
    - affordance: Per-affordance effects (e.g., "depleted", "locked")
    """

    GLOBAL = "global"
    AGENT = "agent"
    ITEM = "item"
    AFFORDANCE = "affordance"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_effects_dto.py -k "reapply_policy" -v
```

**Expected:** Both tests PASS

**Commit:**
```bash
git add src/townlet/config/effects_config.py tests/test_townlet/unit/effects/test_effects_dto.py
git commit -m "feat(effects): add ReapplyPolicy and EffectScope enums"
```

---

### Step 4: Write failing test for CommandConfig

**File:** `tests/test_townlet/unit/effects/test_effects_dto.py` (append)

```python
from townlet.config.effects_config import CommandConfig


def test_command_config_modify():
    """CommandConfig validates modify commands."""
    cmd = CommandConfig(
        modify="target.bar.energy",
        value="target.bar.energy + 0.05"
    )

    assert cmd.modify == "target.bar.energy"
    assert cmd.value == "target.bar.energy + 0.05"
    assert cmd.spawn_effect is None
    assert cmd.if_condition is None


def test_command_config_spawn_effect():
    """CommandConfig validates spawn_effect commands."""
    cmd = CommandConfig(
        spawn_effect="poisoned",
        target="self",
        intensity=2.0
    )

    assert cmd.spawn_effect == "poisoned"
    assert cmd.target == "self"
    assert cmd.intensity == 2.0


def test_command_config_requires_one_command_type():
    """CommandConfig requires exactly one command type."""
    with pytest.raises(ValidationError, match="exactly one command"):
        CommandConfig()  # No command specified

    with pytest.raises(ValidationError, match="exactly one command"):
        CommandConfig(
            modify="target.bar.energy",
            value="5.0",
            spawn_effect="poisoned"  # Can't have both
        )
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_effects_dto.py::test_command_config_modify -v
```

**Expected:** FAIL - CommandConfig not defined

---

### Step 5: Implement CommandConfig

**File:** `src/townlet/config/effects_config.py` (append)

```python
class CommandConfig(BaseModel):
    """Single command in an effect pipeline.

    Exactly one of: modify, spawn_effect, spawn_item, if, for_each must be set.
    """

    # modify command: Mutate VFS/bar variable
    modify: str | None = None
    value: str | None = None  # Expression to evaluate

    # spawn_effect command: Trigger another effect
    spawn_effect: str | None = None  # Effect ID
    target: str | None = "self"  # Expression: "self", "target", or path
    intensity: float | None = 1.0  # Strength multiplier

    # spawn_item command: Create item in world (Phase 4)
    spawn_item: str | None = None  # Item type ID
    position: str | None = None  # Expression for position

    # if command: Conditional execution
    if_condition: str | None = Field(None, alias="if")  # Expression (must eval to bool)
    then: list["CommandConfig"] = []
    else_: list["CommandConfig"] = Field(default=[], alias="else")

    # for_each command: Iterate over collection
    for_each: str | None = None  # Expression (must eval to list/tensor)
    as_: str | None = Field(None, alias="as")  # Iterator variable name
    do: list["CommandConfig"] = []

    @field_validator("modify", "spawn_effect", "spawn_item", "if_condition", "for_each")
    @classmethod
    def validate_exactly_one_command(cls, v, info):
        """Exactly one command type must be set."""
        fields = ["modify", "spawn_effect", "spawn_item", "if_condition", "for_each"]
        set_fields = [f for f in fields if info.data.get(f) is not None]

        if len(set_fields) != 1:
            raise ValueError(
                f"Exactly one command type required (modify/spawn_effect/spawn_item/if/for_each), "
                f"got {len(set_fields)}: {set_fields}"
            )

        return v

    @field_validator("value")
    @classmethod
    def validate_modify_requires_value(cls, v, info):
        """modify command requires value field."""
        if info.data.get("modify") and not v:
            raise ValueError("modify command requires 'value' field")
        return v

    class Config:
        populate_by_name = True  # Allow both "if" and "if_condition"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_effects_dto.py -k "command_config" -v
```

**Expected:** All 3 command_config tests PASS

**Commit:**
```bash
git add src/townlet/config/effects_config.py tests/test_townlet/unit/effects/test_effects_dto.py
git commit -m "feat(effects): add CommandConfig with modify/spawn_effect/if/for_each"
```

---

### Step 6: Write failing test for EffectDefinitionConfig

**File:** `tests/test_townlet/unit/effects/test_effects_dto.py` (append)

```python
from townlet.config.effects_config import EffectDefinitionConfig


def test_effect_definition_minimal():
    """EffectDefinitionConfig with minimal required fields."""
    effect = EffectDefinitionConfig(
        id="ate_food",
        scope="agent",
        duration=10,
        reapply_policy="stack",
    )

    assert effect.id == "ate_food"
    assert effect.scope == EffectScope.AGENT
    assert effect.duration == 10
    assert effect.reapply_policy == ReapplyPolicy.STACK
    assert effect.intensity == 1.0  # Default
    assert effect.observable is True  # Default
    assert effect.on_spawn == []
    assert effect.on_tick == []
    assert effect.on_despawn == []


def test_effect_definition_with_commands():
    """EffectDefinitionConfig with lifecycle commands."""
    effect = EffectDefinitionConfig(
        id="poisoned",
        scope="agent",
        duration=20,
        intensity=0.5,
        reapply_policy="merge",
        observable=True,
        on_spawn=[
            {"modify": "target.vfs.is_poisoned", "value": "true"}
        ],
        on_tick=[
            {"modify": "target.bar.health", "value": "target.bar.health - (0.1 * intensity)"}
        ],
        on_despawn=[
            {"modify": "target.vfs.is_poisoned", "value": "false"}
        ],
    )

    assert effect.id == "poisoned"
    assert effect.intensity == 0.5
    assert effect.reapply_policy == ReapplyPolicy.MERGE
    assert len(effect.on_spawn) == 1
    assert len(effect.on_tick) == 1
    assert len(effect.on_despawn) == 1


def test_effect_definition_requires_duration():
    """EffectDefinitionConfig requires duration field."""
    with pytest.raises(ValidationError, match="duration"):
        EffectDefinitionConfig(
            id="invalid",
            scope="agent",
            reapply_policy="stack",
            # Missing duration
        )


def test_effect_definition_requires_reapply_policy():
    """EffectDefinitionConfig requires reapply_policy (no default)."""
    with pytest.raises(ValidationError, match="reapply_policy"):
        EffectDefinitionConfig(
            id="invalid",
            scope="agent",
            duration=10,
            # Missing reapply_policy
        )
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_effects_dto.py::test_effect_definition_minimal -v
```

**Expected:** FAIL - EffectDefinitionConfig not defined

---

### Step 7: Implement EffectDefinitionConfig

**File:** `src/townlet/config/effects_config.py` (append)

```python
class EffectDefinitionConfig(BaseModel):
    """Definition of a single effect in the catalog.

    Effects are reusable simulation behaviors with lifecycle hooks.
    """

    id: str = Field(..., description="Unique effect identifier")
    scope: EffectScope = Field(..., description="Where effect can attach")

    # Lifecycle parameters (REQUIRED - no defaults to prevent surprises)
    duration: int = Field(..., description="Ticks until auto-despawn", gt=0)
    intensity: float = Field(default=1.0, description="Default strength multiplier")

    # Stacking policy (REQUIRED - must be explicit)
    reapply_policy: ReapplyPolicy = Field(..., description="Policy for multiple spawns")

    # Visibility
    observable: bool = Field(default=True, description="Visible in agent observations")

    # Lifecycle command pipelines
    on_spawn: list[CommandConfig] = Field(default=[], description="Commands on spawn")
    on_tick: list[CommandConfig] = Field(default=[], description="Commands each tick")
    on_despawn: list[CommandConfig] = Field(default=[], description="Commands on despawn")
    on_interrupt: list[CommandConfig] = Field(default=[], description="Commands on forced removal")

    @field_validator("on_spawn", "on_tick", "on_despawn", "on_interrupt", mode="before")
    @classmethod
    def parse_command_dicts(cls, v):
        """Convert list of dicts to list of CommandConfig."""
        if v is None:
            return []
        if isinstance(v, list):
            return [CommandConfig(**cmd) if isinstance(cmd, dict) else cmd for cmd in v]
        return v
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_effects_dto.py -k "effect_definition" -v
```

**Expected:** All 4 effect_definition tests PASS

**Commit:**
```bash
git add src/townlet/config/effects_config.py tests/test_townlet/unit/effects/test_effects_dto.py
git commit -m "feat(effects): add EffectDefinitionConfig with lifecycle commands"
```

---

### Step 8: Write failing test for EffectsConfig

**File:** `tests/test_townlet/unit/effects/test_effects_dto.py` (append)

```python
from townlet.config.effects_config import EffectsConfig


def test_effects_config_minimal():
    """EffectsConfig loads from YAML structure."""
    config = EffectsConfig(
        version="1.0",
        effect_definitions=[
            {
                "id": "ate_food",
                "scope": "agent",
                "duration": 10,
                "reapply_policy": "stack",
            }
        ],
    )

    assert config.version == "1.0"
    assert len(config.effect_definitions) == 1
    assert config.effect_definitions[0].id == "ate_food"


def test_effects_config_rejects_duplicate_ids():
    """EffectsConfig validates unique effect IDs."""
    with pytest.raises(ValidationError, match="Duplicate effect"):
        EffectsConfig(
            version="1.0",
            effect_definitions=[
                {"id": "poisoned", "scope": "agent", "duration": 10, "reapply_policy": "stack"},
                {"id": "poisoned", "scope": "agent", "duration": 20, "reapply_policy": "merge"},
            ],
        )


def test_effects_config_from_yaml():
    """EffectsConfig can load from YAML file."""
    yaml_content = """
version: "1.0"

effect_definitions:
  - id: "ate_food"
    scope: agent
    duration: 10
    reapply_policy: stack
    on_tick:
      - modify: target.bar.energy
        value: target.bar.energy + 0.05

  - id: "poisoned"
    scope: agent
    duration: 20
    intensity: 0.5
    reapply_policy: merge
    on_tick:
      - modify: target.bar.health
        value: target.bar.health - (0.1 * intensity)
"""

    import yaml
    data = yaml.safe_load(yaml_content)
    config = EffectsConfig(**data)

    assert len(config.effect_definitions) == 2
    assert config.effect_definitions[0].id == "ate_food"
    assert config.effect_definitions[1].id == "poisoned"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_effects_dto.py::test_effects_config_minimal -v
```

**Expected:** FAIL - EffectsConfig not defined

---

### Step 9: Implement EffectsConfig

**File:** `src/townlet/config/effects_config.py` (append)

```python
class EffectsConfig(BaseModel):
    """Top-level Effects configuration from effects.yaml."""

    version: Literal["1.0"] = Field(default="1.0", description="Config schema version")
    effect_definitions: list[EffectDefinitionConfig] = Field(
        default=[],
        description="Catalog of reusable effect definitions"
    )

    @field_validator("effect_definitions")
    @classmethod
    def validate_unique_ids(cls, definitions):
        """Effect IDs must be unique."""
        ids = [d.id for d in definitions]
        duplicates = {id for id in ids if ids.count(id) > 1}

        if duplicates:
            raise ValueError(f"Duplicate effect IDs: {duplicates}")

        return definitions
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_effects_dto.py -k "effects_config" -v
```

**Expected:** All 3 effects_config tests PASS

**Commit:**
```bash
git add src/townlet/config/effects_config.py tests/test_townlet/unit/effects/test_effects_dto.py
git commit -m "feat(effects): add EffectsConfig top-level DTO"
```

---

### Step 10: Create smoke test config

**File:** `configs/test/effects_smoke/effects.yaml`

```yaml
version: "1.0"

effect_definitions:
  # Simple energy restoration
  - id: "ate_food"
    scope: agent
    duration: 10
    intensity: 1.0
    reapply_policy: stack
    observable: true

    on_spawn:
      - modify: target.vfs.digesting
        value: "true"

    on_tick:
      - modify: target.bar.energy
        value: "target.bar.energy + (0.05 * intensity)"

    on_despawn:
      - modify: target.vfs.digesting
        value: "false"

  # Poison with merge policy
  - id: "poisoned"
    scope: agent
    duration: 20
    intensity: 0.5
    reapply_policy: merge
    observable: true

    on_tick:
      - modify: target.bar.health
        value: "target.bar.health - (0.1 * intensity)"

  # Wet status with renew policy
  - id: "wet"
    scope: agent
    duration: 15
    reapply_policy: renew
    observable: true

    on_spawn:
      - modify: target.vfs.is_wet
        value: "true"

    on_despawn:
      - modify: target.vfs.is_wet
        value: "false"

  # Currently eating (replace policy)
  - id: "eating"
    scope: agent
    duration: 3
    reapply_policy: replace
    observable: false
```

**Verify:**
```bash
cat configs/test/effects_smoke/effects.yaml
```

**Commit:**
```bash
git add configs/test/effects_smoke/effects.yaml
git commit -m "feat(effects): add smoke test config with 4 example effects"
```

---

### Step 11: Write failing test for catalog compilation

**File:** `tests/test_townlet/unit/effects/test_catalog_compilation.py`

```python
"""Tests for effects catalog compilation."""
import pytest
from pathlib import Path
import yaml

from townlet.effects.catalog import EffectCatalog
from townlet.config.effects_config import EffectsConfig


def test_catalog_from_config():
    """EffectCatalog compiles from EffectsConfig."""
    config = EffectsConfig(
        version="1.0",
        effect_definitions=[
            {
                "id": "ate_food",
                "scope": "agent",
                "duration": 10,
                "reapply_policy": "stack",
            }
        ],
    )

    catalog = EffectCatalog.from_config(config)

    assert "ate_food" in catalog.effects
    assert catalog.effects["ate_food"].id == "ate_food"
    assert catalog.effects["ate_food"].duration == 10


def test_catalog_load_smoke_config():
    """EffectCatalog loads effects_smoke config."""
    config_path = Path("configs/test/effects_smoke/effects.yaml")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    config = EffectsConfig(**data)
    catalog = EffectCatalog.from_config(config)

    # Verify all 4 smoke test effects loaded
    assert len(catalog.effects) == 4
    assert "ate_food" in catalog.effects
    assert "poisoned" in catalog.effects
    assert "wet" in catalog.effects
    assert "eating" in catalog.effects


def test_catalog_get_effect():
    """EffectCatalog.get() retrieves effect by ID."""
    config = EffectsConfig(
        version="1.0",
        effect_definitions=[
            {"id": "ate_food", "scope": "agent", "duration": 10, "reapply_policy": "stack"}
        ],
    )

    catalog = EffectCatalog.from_config(config)
    effect = catalog.get("ate_food")

    assert effect.id == "ate_food"
    assert effect.duration == 10


def test_catalog_get_missing_effect_raises():
    """EffectCatalog.get() raises KeyError for missing effect."""
    catalog = EffectCatalog.from_config(EffectsConfig(version="1.0", effect_definitions=[]))

    with pytest.raises(KeyError, match="unknown_effect"):
        catalog.get("unknown_effect")
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_catalog_compilation.py::test_catalog_from_config -v
```

**Expected:** FAIL - Module 'townlet.effects.catalog' not found

---

### Step 12: Implement EffectCatalog

**File:** `src/townlet/effects/catalog.py`

```python
"""Effects catalog compilation and loading."""
from __future__ import annotations

from dataclasses import dataclass

from townlet.config.effects_config import EffectDefinitionConfig, EffectsConfig

__all__ = ["EffectCatalog"]


@dataclass
class EffectCatalog:
    """Compiled effect catalog.

    Maps effect IDs to their definitions for runtime lookup.
    """

    effects: dict[str, EffectDefinitionConfig]

    @classmethod
    def from_config(cls, config: EffectsConfig) -> EffectCatalog:
        """Compile effects catalog from config.

        Args:
            config: Effects configuration from YAML

        Returns:
            Compiled catalog with effect ID lookup
        """
        effects = {defn.id: defn for defn in config.effect_definitions}
        return cls(effects=effects)

    def get(self, effect_id: str) -> EffectDefinitionConfig:
        """Get effect definition by ID.

        Args:
            effect_id: Effect identifier

        Returns:
            Effect definition

        Raises:
            KeyError: If effect ID not found
        """
        if effect_id not in self.effects:
            raise KeyError(
                f"Effect '{effect_id}' not found in catalog. "
                f"Available effects: {list(self.effects.keys())}"
            )
        return self.effects[effect_id]

    def __contains__(self, effect_id: str) -> bool:
        """Check if effect exists in catalog."""
        return effect_id in self.effects

    def __len__(self) -> int:
        """Number of effects in catalog."""
        return len(self.effects)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_catalog_compilation.py -v
```

**Expected:** All 4 catalog tests PASS

**Commit:**
```bash
git add src/townlet/effects/catalog.py tests/test_townlet/unit/effects/test_catalog_compilation.py
git commit -m "feat(effects): add EffectCatalog compilation from config"
```

---

### Step 13: Add module exports

**File:** `src/townlet/effects/__init__.py`

```python
"""Effects system for HAMLET World Compiler."""
from __future__ import annotations

from townlet.effects.catalog import EffectCatalog

__all__ = ["EffectCatalog"]
```

**Verify:**
```bash
UV_CACHE_DIR=.uv-cache uv run python -c "from townlet.effects import EffectCatalog; print('OK')"
```

**Expected:** Prints "OK"

**Commit:**
```bash
git add src/townlet/effects/__init__.py
git commit -m "feat(effects): export EffectCatalog in module API"
```

---

### Step 14: Type checking and formatting

**Run mypy:**
```bash
UV_CACHE_DIR=.uv-cache uv run mypy src/townlet/effects/ src/townlet/config/effects_config.py
```

**Expected:** Success

**Run ruff:**
```bash
UV_CACHE_DIR=.uv-cache uv run ruff format src/townlet/effects/ src/townlet/config/effects_config.py tests/test_townlet/unit/effects/
UV_CACHE_DIR=.uv-cache uv run ruff check src/townlet/effects/ src/townlet/config/effects_config.py
```

**Expected:** No changes needed

**Run full test suite:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/ -v
```

**Expected:** All ~18 tests PASS

**Commit if any changes:**
```bash
git add -u
git commit -m "test(effects): verify all DTOs and catalog tests pass"
```

---

## Success Criteria

✅ **18+ tests passing** (DTOs + catalog compilation)
✅ **EffectsConfig loads from YAML** (effects_smoke test config)
✅ **ReapplyPolicy validation** (stack/renew/merge/replace)
✅ **EffectCatalog compiles** (effect ID lookup working)
✅ **CommandConfig validates** (exactly one command type)
✅ **Type checking passes** (mypy clean)
✅ **Code formatted** (ruff)

---

## Next Steps

**Task 3.2: Command Parser & Compiler**

Parse command YAML to AST, compile expressions within commands, type check targets.

See: `docs/plans/vfs_uplift/2025-11-19-task-3-2-command-parser.md`
