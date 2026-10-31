# Task 2.1: VFS Profiles DTOs - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create configuration DTOs for VFS profiles (global, agent, item scopes) with expression support and reference types.

**Architecture:** Pydantic DTOs with schema validation. Expression XOR initial_value constraint. Reference type support (agent_ref, item_ref, affordance_ref, effect_ref).

**Tech Stack:** Pydantic 2.x, Python 3.11+, YAML config validation

**Dependencies:** Task 1.1-1.4 (Expression Language) complete

---

## Background

Phase 1 VFS (static) stored simple values in `variables_reference.yaml`. Phase 2 VFS (dynamic) extends this with:
- **Expression-based variables**: Values computed from expressions (e.g., `bar["energy"] + 0.05`)
- **Reference types**: agent_ref, item_ref, affordance_ref, effect_ref for entity relationships
- **Scoped storage**: Global (shared), Agent (per-agent), Item (per-item-instance)

This task builds the configuration layer that specifies VFS profiles.

---

## Task Breakdown

### Step 1: Write failing test for GlobalVFSVariableConfig DTO

**File:** `tests/test_townlet/unit/config/test_vfs_profiles_dto.py`

```python
"""Tests for VFS profiles configuration DTOs."""
import pytest
from pydantic import ValidationError
from townlet.config.vfs_profiles_config import (
    GlobalVFSVariableConfig,
    GlobalVFSProfileConfig,
)


def test_global_vfs_variable_with_initial_value():
    """Global VFS variable with static initial value."""
    config = GlobalVFSVariableConfig(
        name="day_count",
        type="int",
        initial_value=0,
        description="Number of days elapsed",
    )

    assert config.name == "day_count"
    assert config.type == "int"
    assert config.initial_value == 0
    assert config.expression is None


def test_global_vfs_variable_with_expression():
    """Global VFS variable with computed expression."""
    config = GlobalVFSVariableConfig(
        name="is_night",
        type="bool",
        expression="temporal.tick % 24 >= 18",
        description="True during night time",
    )

    assert config.name == "is_night"
    assert config.type == "bool"
    assert config.expression == "temporal.tick % 24 >= 18"
    assert config.initial_value is None


def test_global_vfs_variable_requires_value_or_expression():
    """Must have either initial_value or expression."""
    with pytest.raises(ValidationError, match="exactly one"):
        GlobalVFSVariableConfig(
            name="invalid",
            type="int",
            # Missing both initial_value and expression
        )


def test_global_vfs_variable_rejects_both():
    """Cannot have both initial_value and expression."""
    with pytest.raises(ValidationError, match="exactly one"):
        GlobalVFSVariableConfig(
            name="invalid",
            type="int",
            initial_value=5,
            expression="bar.energy + 1",
        )
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/config/test_vfs_profiles_dto.py::test_global_vfs_variable_with_initial_value -v
```

**Expected:** FAIL - Module not found

---

### Step 2: Implement GlobalVFSVariableConfig DTO

**File:** `src/townlet/config/vfs_profiles_config.py`

```python
"""Configuration DTOs for VFS profiles."""
from typing import Optional, Literal
from pydantic import BaseModel, field_validator, model_validator


class GlobalVFSVariableConfig(BaseModel):
    """Configuration for a single global VFS variable.

    Global variables are shared across all agents (e.g., day_count, is_night).
    """

    name: str
    type: Literal["int", "float", "bool", "vec2i", "vec3i", "agent_ref", "item_ref"]
    initial_value: Optional[int | float | bool | list] = None
    expression: Optional[str] = None
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_value_xor_expression(self):
        """Exactly one of initial_value or expression must be set."""
        has_value = self.initial_value is not None
        has_expr = self.expression is not None

        if has_value == has_expr:  # Both true or both false
            raise ValueError(
                f"Variable '{self.name}' must have exactly one of "
                f"initial_value or expression (not both, not neither)"
            )

        return self


class GlobalVFSProfileConfig(BaseModel):
    """Configuration for global VFS profile.

    Global VFS contains variables shared across all agents.
    """

    variables: list[GlobalVFSVariableConfig]

    @field_validator("variables")
    @classmethod
    def validate_unique_names(cls, variables: list[GlobalVFSVariableConfig]):
        """Variable names must be unique within profile."""
        names = [v.name for v in variables]
        duplicates = {name for name in names if names.count(name) > 1}

        if duplicates:
            raise ValueError(f"Duplicate variable names: {duplicates}")

        return variables
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/config/test_vfs_profiles_dto.py -k "global_vfs_variable" -v
```

**Expected:** All 4 global variable tests PASS

**Commit:**
```bash
git add src/townlet/config/vfs_profiles_config.py tests/test_townlet/unit/config/test_vfs_profiles_dto.py
git commit -m "feat(vfs): add GlobalVFSVariableConfig DTO with expression support"
```

---

### Step 3: Write failing tests for AgentVFSVariableConfig DTO

**File:** `tests/test_townlet/unit/config/test_vfs_profiles_dto.py` (append)

```python
from townlet.config.vfs_profiles_config import (
    AgentVFSVariableConfig,
    AgentVFSProfileConfig,
)


def test_agent_vfs_variable_with_initial_value():
    """Agent VFS variable with static initial value."""
    config = AgentVFSVariableConfig(
        name="motivation",
        type="float",
        initial_value=1.0,
        description="Agent's intrinsic motivation",
    )

    assert config.name == "motivation"
    assert config.type == "float"
    assert config.initial_value == 1.0


def test_agent_vfs_variable_with_expression():
    """Agent VFS variable with computed expression."""
    config = AgentVFSVariableConfig(
        name="is_crisis",
        type="bool",
        expression="bar.energy < 0.2 or bar.health < 0.2",
        description="True when agent is in resource crisis",
    )

    assert config.name == "is_crisis"
    assert config.expression == "bar.energy < 0.2 or bar.health < 0.2"


def test_agent_vfs_variable_with_reference_type():
    """Agent VFS can reference other entities."""
    config = AgentVFSVariableConfig(
        name="nearest_food",
        type="item_ref",
        expression="nearest(items, self.position, type='food')",
        description="Reference to nearest food item",
    )

    assert config.type == "item_ref"


def test_agent_vfs_profile_unique_names():
    """Agent VFS profile rejects duplicate variable names."""
    with pytest.raises(ValidationError, match="Duplicate"):
        AgentVFSProfileConfig(
            variables=[
                AgentVFSVariableConfig(name="x", type="int", initial_value=0),
                AgentVFSVariableConfig(name="x", type="int", initial_value=1),
            ]
        )
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/config/test_vfs_profiles_dto.py::test_agent_vfs_variable_with_initial_value -v
```

**Expected:** FAIL - AgentVFSVariableConfig not defined

---

### Step 4: Implement AgentVFSVariableConfig DTO

**File:** `src/townlet/config/vfs_profiles_config.py` (append)

```python
class AgentVFSVariableConfig(BaseModel):
    """Configuration for a single agent VFS variable.

    Agent variables are per-agent state (e.g., motivation, is_crisis).
    """

    name: str
    type: Literal[
        "int", "float", "bool", "vec2i", "vec3i",
        "agent_ref", "item_ref", "affordance_ref", "effect_ref"
    ]
    initial_value: Optional[int | float | bool | list] = None
    expression: Optional[str] = None
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_value_xor_expression(self):
        """Exactly one of initial_value or expression must be set."""
        has_value = self.initial_value is not None
        has_expr = self.expression is not None

        if has_value == has_expr:
            raise ValueError(
                f"Variable '{self.name}' must have exactly one of "
                f"initial_value or expression (not both, not neither)"
            )

        return self


class AgentVFSProfileConfig(BaseModel):
    """Configuration for agent VFS profile.

    Agent VFS contains per-agent state (motivation, crisis flags, etc.).
    """

    variables: list[AgentVFSVariableConfig]

    @field_validator("variables")
    @classmethod
    def validate_unique_names(cls, variables: list[AgentVFSVariableConfig]):
        """Variable names must be unique within profile."""
        names = [v.name for v in variables]
        duplicates = {name for name in names if names.count(name) > 1}

        if duplicates:
            raise ValueError(f"Duplicate variable names: {duplicates}")

        return variables
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/config/test_vfs_profiles_dto.py -k "agent_vfs" -v
```

**Expected:** All 4 agent VFS tests PASS

**Commit:**
```bash
git add src/townlet/config/vfs_profiles_config.py tests/test_townlet/unit/config/test_vfs_profiles_dto.py
git commit -m "feat(vfs): add AgentVFSVariableConfig DTO with reference types"
```

---

### Step 5: Write failing tests for ItemVFSVariableConfig DTO

**File:** `tests/test_townlet/unit/config/test_vfs_profiles_dto.py` (append)

```python
from townlet.config.vfs_profiles_config import (
    ItemVFSVariableConfig,
    ItemVFSProfileConfig,
)


def test_item_vfs_variable_with_initial_value():
    """Item VFS variable with static initial value."""
    config = ItemVFSVariableConfig(
        name="nutrition",
        type="float",
        initial_value=0.5,
        description="Nutritional value of food item",
    )

    assert config.name == "nutrition"
    assert config.type == "float"
    assert config.initial_value == 0.5


def test_item_vfs_variable_with_expression():
    """Item VFS variable with computed expression."""
    config = ItemVFSVariableConfig(
        name="is_spoiled",
        type="bool",
        expression="self.age > 100",
        description="True when item has spoiled",
    )

    assert config.name == "is_spoiled"
    assert config.expression == "self.age > 100"


def test_item_vfs_variable_with_owner_reference():
    """Item VFS can reference owning agent."""
    config = ItemVFSVariableConfig(
        name="owner",
        type="agent_ref",
        expression="self.held_by",
        description="Agent currently holding this item",
    )

    assert config.type == "agent_ref"


def test_item_vfs_profile_multiple_variables():
    """Item VFS profile supports multiple variables."""
    profile = ItemVFSProfileConfig(
        profile_name="food_stats",
        variables=[
            ItemVFSVariableConfig(name="nutrition", type="float", initial_value=0.5),
            ItemVFSVariableConfig(name="is_spoiled", type="bool", expression="self.age > 100"),
        ]
    )

    assert profile.profile_name == "food_stats"
    assert len(profile.variables) == 2
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/config/test_vfs_profiles_dto.py::test_item_vfs_variable_with_initial_value -v
```

**Expected:** FAIL - ItemVFSVariableConfig not defined

---

### Step 6: Implement ItemVFSVariableConfig DTO

**File:** `src/townlet/config/vfs_profiles_config.py` (append)

```python
class ItemVFSVariableConfig(BaseModel):
    """Configuration for a single item VFS variable.

    Item variables are per-item-instance state (e.g., nutrition, age, is_spoiled).
    """

    name: str
    type: Literal[
        "int", "float", "bool", "vec2i", "vec3i",
        "agent_ref", "item_ref", "affordance_ref", "effect_ref"
    ]
    initial_value: Optional[int | float | bool | list] = None
    expression: Optional[str] = None
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_value_xor_expression(self):
        """Exactly one of initial_value or expression must be set."""
        has_value = self.initial_value is not None
        has_expr = self.expression is not None

        if has_value == has_expr:
            raise ValueError(
                f"Variable '{self.name}' must have exactly one of "
                f"initial_value or expression (not both, not neither)"
            )

        return self


class ItemVFSProfileConfig(BaseModel):
    """Configuration for item VFS profile.

    Item VFS profiles define reusable state schemas for item types
    (e.g., 'food_stats', 'weapon_stats').
    """

    profile_name: str
    variables: list[ItemVFSVariableConfig]

    @field_validator("variables")
    @classmethod
    def validate_unique_names(cls, variables: list[ItemVFSVariableConfig]):
        """Variable names must be unique within profile."""
        names = [v.name for v in variables]
        duplicates = {name for name in names if names.count(name) > 1}

        if duplicates:
            raise ValueError(f"Duplicate variable names: {duplicates}")

        return variables
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/config/test_vfs_profiles_dto.py -k "item_vfs" -v
```

**Expected:** All 4 item VFS tests PASS

**Commit:**
```bash
git add src/townlet/config/vfs_profiles_config.py tests/test_townlet/unit/config/test_vfs_profiles_dto.py
git commit -m "feat(vfs): add ItemVFSVariableConfig DTO with profile support"
```

---

### Step 7: Write failing test for VFSProfilesConfig top-level DTO

**File:** `tests/test_townlet/unit/config/test_vfs_profiles_dto.py` (append)

```python
from townlet.config.vfs_profiles_config import VFSProfilesConfig


def test_vfs_profiles_config_complete():
    """VFSProfilesConfig loads global + agent + item profiles."""
    config = VFSProfilesConfig(
        global_profile=GlobalVFSProfileConfig(
            variables=[
                GlobalVFSVariableConfig(name="day_count", type="int", initial_value=0),
            ]
        ),
        agent_profile=AgentVFSProfileConfig(
            variables=[
                AgentVFSVariableConfig(name="motivation", type="float", initial_value=1.0),
            ]
        ),
        item_profiles=[
            ItemVFSProfileConfig(
                profile_name="food_stats",
                variables=[
                    ItemVFSVariableConfig(name="nutrition", type="float", initial_value=0.5),
                ]
            ),
        ]
    )

    assert config.global_profile is not None
    assert config.agent_profile is not None
    assert len(config.item_profiles) == 1


def test_vfs_profiles_config_optional_sections():
    """VFSProfilesConfig allows missing sections."""
    config = VFSProfilesConfig(
        global_profile=None,
        agent_profile=AgentVFSProfileConfig(variables=[]),
        item_profiles=[],
    )

    assert config.global_profile is None
    assert config.agent_profile is not None
    assert len(config.item_profiles) == 0
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/config/test_vfs_profiles_dto.py::test_vfs_profiles_config_complete -v
```

**Expected:** FAIL - VFSProfilesConfig not defined

---

### Step 8: Implement VFSProfilesConfig top-level DTO

**File:** `src/townlet/config/vfs_profiles_config.py` (append)

```python
class VFSProfilesConfig(BaseModel):
    """Top-level configuration for VFS profiles.

    Loaded from vfs_profiles.yaml. Contains:
    - global_profile: Shared variables (day_count, is_night)
    - agent_profile: Per-agent variables (motivation, is_crisis)
    - item_profiles: Named profiles for item types (food_stats, weapon_stats)
    """

    global_profile: Optional[GlobalVFSProfileConfig] = None
    agent_profile: Optional[AgentVFSProfileConfig] = None
    item_profiles: list[ItemVFSProfileConfig] = []

    @field_validator("item_profiles")
    @classmethod
    def validate_unique_profile_names(cls, profiles: list[ItemVFSProfileConfig]):
        """Item profile names must be unique."""
        names = [p.profile_name for p in profiles]
        duplicates = {name for name in names if names.count(name) > 1}

        if duplicates:
            raise ValueError(f"Duplicate item profile names: {duplicates}")

        return profiles
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/config/test_vfs_profiles_dto.py -v
```

**Expected:** All tests PASS (~14 tests total)

**Commit:**
```bash
git add src/townlet/config/vfs_profiles_config.py tests/test_townlet/unit/config/test_vfs_profiles_dto.py
git commit -m "feat(vfs): add VFSProfilesConfig top-level DTO"
```

---

### Step 9: Add module exports and type annotations

**File:** `src/townlet/config/vfs_profiles_config.py` (add at top)

```python
"""Configuration DTOs for VFS profiles."""
from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, field_validator, model_validator

__all__ = [
    "GlobalVFSVariableConfig",
    "GlobalVFSProfileConfig",
    "AgentVFSVariableConfig",
    "AgentVFSProfileConfig",
    "ItemVFSVariableConfig",
    "ItemVFSProfileConfig",
    "VFSProfilesConfig",
]
```

**Verify:**
```bash
UV_CACHE_DIR=.uv-cache uv run python -c "from townlet.config.vfs_profiles_config import VFSProfilesConfig; print('OK')"
```

**Expected:** Prints "OK"

**Commit:**
```bash
git add src/townlet/config/vfs_profiles_config.py
git commit -m "feat(vfs): export VFS profiles DTOs in module API"
```

---

### Step 10: Type checking and formatting

**Run mypy:**
```bash
UV_CACHE_DIR=.uv-cache uv run mypy src/townlet/config/vfs_profiles_config.py
```

**Expected:** Success (no errors)

**Run ruff:**
```bash
UV_CACHE_DIR=.uv-cache uv run ruff format src/townlet/config/vfs_profiles_config.py tests/test_townlet/unit/config/test_vfs_profiles_dto.py
UV_CACHE_DIR=.uv-cache uv run ruff check src/townlet/config/vfs_profiles_config.py
```

**Expected:** No changes needed (already formatted)

**If changes made:**
```bash
git add -u
git commit -m "style(vfs): format VFS profiles config code"
```

---

### Step 11: Create smoke test config file

**File:** `configs/test/vfs_profiles_smoke/vfs_profiles.yaml`

```yaml
# VFS Profiles Smoke Test Configuration
# Tests: global variables, agent variables, item profiles

global_profile:
  variables:
    - name: day_count
      type: int
      initial_value: 0
      description: "Number of days elapsed"

    - name: is_night
      type: bool
      expression: "temporal.tick % 24 >= 18"
      description: "True during night hours (18:00-6:00)"

agent_profile:
  variables:
    - name: motivation
      type: float
      initial_value: 1.0
      description: "Agent's intrinsic motivation multiplier"

    - name: is_crisis
      type: bool
      expression: "bar.energy < 0.2 or bar.health < 0.2"
      description: "True when agent is in resource crisis"

    - name: crisis_duration
      type: int
      initial_value: 0
      description: "Ticks spent in crisis state"

item_profiles:
  - profile_name: food_stats
    variables:
      - name: nutrition
        type: float
        initial_value: 0.5
        description: "Energy restored when consumed"

      - name: is_spoiled
        type: bool
        expression: "self.age > 100"
        description: "True when food has spoiled"

  - profile_name: weapon_stats
    variables:
      - name: damage
        type: float
        initial_value: 10.0
        description: "Damage dealt per use"

      - name: durability
        type: int
        initial_value: 100
        description: "Remaining uses before breaking"
```

**Test loading:**
```bash
UV_CACHE_DIR=.uv-cache uv run python -c "
import yaml
from townlet.config.vfs_profiles_config import VFSProfilesConfig

with open('configs/test/vfs_profiles_smoke/vfs_profiles.yaml') as f:
    data = yaml.safe_load(f)

config = VFSProfilesConfig(**data)
print(f'Loaded {len(config.global_profile.variables)} global variables')
print(f'Loaded {len(config.agent_profile.variables)} agent variables')
print(f'Loaded {len(config.item_profiles)} item profiles')
"
```

**Expected:**
```
Loaded 2 global variables
Loaded 3 agent variables
Loaded 2 item profiles
```

**Commit:**
```bash
git add configs/test/vfs_profiles_smoke/vfs_profiles.yaml
git commit -m "test(vfs): add smoke test config for VFS profiles"
```

---

## Success Criteria

✅ **14+ tests passing** (global, agent, item variable DTOs)
✅ **VFS profiles config schema complete** (global/agent/item scopes)
✅ **Expression XOR initial_value validation** (enforced at schema level)
✅ **Reference types supported** (agent_ref, item_ref, affordance_ref, effect_ref)
✅ **Unique name validation** (within each profile scope)
✅ **Type checking passes** (mypy clean)
✅ **Code formatted** (ruff)
✅ **Smoke test config loads** (vfs_profiles_smoke/vfs_profiles.yaml)

---

## Next Steps

**Task 2.2: Scoped Registry**

Extend `VariableRegistry` for global/agent/item scopes with separate storage:
- `global_storage: dict[str, torch.Tensor]` (single shared state)
- `agent_storage: dict[str, torch.Tensor]` (per-agent tensors)
- `item_storage: dict[str, dict[str, torch.Tensor]]` (per-profile, per-instance)

See: `docs/plans/vfs_uplift/2025-11-19-task-2-2-scoped-registry.md` (to be created)
