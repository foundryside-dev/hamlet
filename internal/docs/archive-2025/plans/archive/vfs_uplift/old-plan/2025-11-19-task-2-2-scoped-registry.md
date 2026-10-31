# Task 2.2: Scoped Registry - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend VariableRegistry to support global/agent/item scoped storage with separate tensor management per scope.

**Architecture:** Three-tier storage (global, agent, item). Global is singleton dict, agent is batch tensors, item is profile-based nested dict. Access control enforced per scope.

**Tech Stack:** PyTorch tensors, Python 3.11+, dataclass-based storage

**Dependencies:** Task 2.1 (VFS Profiles DTOs) complete

---

## Background

Phase 1 VFS used flat `VariableRegistry` with single `_storage` dict. Phase 2 VFS needs scoped storage:

- **Global scope**: `{"day_count": tensor(42)}` - single shared state
- **Agent scope**: `{"motivation": tensor([batch])}` - per-agent tensors
- **Item scope**: `{"food_stats": {"nutrition": tensor([...])}` - per-profile, per-instance

This task refactors `VariableRegistry` to support these three scopes with proper access control.

---

## Task Breakdown

### Step 1: Write failing tests for global scope storage

**File:** `tests/test_townlet/unit/vfs/test_scoped_registry.py`

```python
"""Tests for scoped variable registry."""
import torch
import pytest
from townlet.vfs.registry import ScopedVariableRegistry


def test_set_global_variable():
    """Registry stores global variables as singleton tensors."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    registry.set_global("day_count", torch.tensor(42))

    value = registry.get_global("day_count")
    assert torch.equal(value, torch.tensor(42))


def test_get_global_variable_not_found():
    """Registry raises KeyError for missing global variables."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    with pytest.raises(KeyError, match="day_count"):
        registry.get_global("day_count")


def test_global_variables_separate_from_agent():
    """Global and agent scopes are separate namespaces."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    registry.set_global("x", torch.tensor(1))
    registry.set_agent("x", torch.tensor([2, 3]))

    assert torch.equal(registry.get_global("x"), torch.tensor(1))
    assert torch.equal(registry.get_agent("x"), torch.tensor([2, 3]))


def test_list_global_variables():
    """Registry lists all global variable names."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    registry.set_global("day_count", torch.tensor(0))
    registry.set_global("is_night", torch.tensor(False))

    names = registry.list_global()
    assert set(names) == {"day_count", "is_night"}
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_scoped_registry.py::test_set_global_variable -v
```

**Expected:** FAIL - ScopedVariableRegistry not defined

---

### Step 2: Implement global scope storage

**File:** `src/townlet/vfs/registry.py` (refactor existing VariableRegistry)

```python
"""Variable registry with scoped storage (global, agent, item)."""
import torch
from typing import Optional


class ScopedVariableRegistry:
    """Variable storage with three scopes: global, agent, item.

    Global scope: Singleton values shared across all agents
        - Storage: dict[str, torch.Tensor] (scalar tensors)
        - Example: {"day_count": tensor(42), "is_night": tensor(True)}

    Agent scope: Per-agent values (batch tensors)
        - Storage: dict[str, torch.Tensor] (batch_size tensors)
        - Example: {"motivation": tensor([1.0, 0.8, 1.2])}

    Item scope: Per-item-instance values (profile-based)
        - Storage: dict[profile_name, dict[var_name, torch.Tensor]]
        - Example: {"food_stats": {"nutrition": tensor([0.5, 0.3])}}
    """

    def __init__(self, device: torch.device = torch.device("cpu")):
        self.device = device

        # Global scope: singleton tensors
        self._global_storage: dict[str, torch.Tensor] = {}

        # Agent scope: batch tensors (populated later)
        self._agent_storage: dict[str, torch.Tensor] = {}

        # Item scope: profile -> {var -> tensor} (populated later)
        self._item_storage: dict[str, dict[str, torch.Tensor]] = {}

    # Global scope methods

    def set_global(self, name: str, value: torch.Tensor) -> None:
        """Set global variable value.

        Args:
            name: Variable name
            value: Singleton tensor (no batch dimension)
        """
        self._global_storage[name] = value.to(self.device)

    def get_global(self, name: str) -> torch.Tensor:
        """Get global variable value.

        Args:
            name: Variable name

        Returns:
            Singleton tensor

        Raises:
            KeyError: If variable not found
        """
        if name not in self._global_storage:
            raise KeyError(
                f"Global variable '{name}' not found. "
                f"Available: {list(self._global_storage.keys())}"
            )
        return self._global_storage[name]

    def list_global(self) -> list[str]:
        """List all global variable names."""
        return list(self._global_storage.keys())

    # Agent scope methods (stubs for now)

    def set_agent(self, name: str, value: torch.Tensor) -> None:
        """Set agent variable value (batch tensor)."""
        self._agent_storage[name] = value.to(self.device)

    def get_agent(self, name: str) -> torch.Tensor:
        """Get agent variable value (batch tensor)."""
        if name not in self._agent_storage:
            raise KeyError(
                f"Agent variable '{name}' not found. "
                f"Available: {list(self._agent_storage.keys())}"
            )
        return self._agent_storage[name]
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_scoped_registry.py -k "global" -v
```

**Expected:** All 4 global scope tests PASS

**Commit:**
```bash
git add src/townlet/vfs/registry.py tests/test_townlet/unit/vfs/test_scoped_registry.py
git commit -m "feat(vfs): add global scope storage to ScopedVariableRegistry"
```

---

### Step 3: Write failing tests for agent scope storage

**File:** `tests/test_townlet/unit/vfs/test_scoped_registry.py` (append)

```python
def test_set_agent_variable():
    """Registry stores agent variables as batch tensors."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    registry.set_agent("motivation", torch.tensor([1.0, 0.8, 1.2]))

    value = registry.get_agent("motivation")
    assert torch.equal(value, torch.tensor([1.0, 0.8, 1.2]))


def test_get_agent_variable_not_found():
    """Registry raises KeyError for missing agent variables."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    with pytest.raises(KeyError, match="motivation"):
        registry.get_agent("motivation")


def test_agent_batch_dimension():
    """Agent variables have batch dimension."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    batch_size = 64
    registry.set_agent("is_crisis", torch.zeros(batch_size, dtype=torch.bool))

    value = registry.get_agent("is_crisis")
    assert value.shape == (batch_size,)


def test_list_agent_variables():
    """Registry lists all agent variable names."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    registry.set_agent("motivation", torch.tensor([1.0]))
    registry.set_agent("is_crisis", torch.tensor([False]))

    names = registry.list_agent()
    assert set(names) == {"motivation", "is_crisis"}
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_scoped_registry.py::test_set_agent_variable -v
```

**Expected:** FAIL - list_agent() not implemented

---

### Step 4: Implement agent scope storage

**File:** `src/townlet/vfs/registry.py` (add method)

```python
    def list_agent(self) -> list[str]:
        """List all agent variable names."""
        return list(self._agent_storage.keys())
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_scoped_registry.py -k "agent" -v
```

**Expected:** All 4 agent scope tests PASS

**Commit:**
```bash
git add src/townlet/vfs/registry.py tests/test_townlet/unit/vfs/test_scoped_registry.py
git commit -m "feat(vfs): add agent scope storage to ScopedVariableRegistry"
```

---

### Step 5: Write failing tests for item scope storage

**File:** `tests/test_townlet/unit/vfs/test_scoped_registry.py` (append)

```python
def test_set_item_variable():
    """Registry stores item variables per profile."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    # food_stats profile has 2 instances with nutrition values
    registry.set_item("food_stats", "nutrition", torch.tensor([0.5, 0.3]))

    value = registry.get_item("food_stats", "nutrition")
    assert torch.equal(value, torch.tensor([0.5, 0.3]))


def test_get_item_variable_not_found():
    """Registry raises KeyError for missing item variables."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    with pytest.raises(KeyError, match="food_stats"):
        registry.get_item("food_stats", "nutrition")


def test_item_profiles_separate_namespaces():
    """Item profiles are separate namespaces."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    registry.set_item("food_stats", "nutrition", torch.tensor([0.5]))
    registry.set_item("weapon_stats", "damage", torch.tensor([10.0]))

    # Same variable name in different profiles
    registry.set_item("food_stats", "value", torch.tensor([1.0]))
    registry.set_item("weapon_stats", "value", torch.tensor([50.0]))

    assert torch.equal(registry.get_item("food_stats", "value"), torch.tensor([1.0]))
    assert torch.equal(registry.get_item("weapon_stats", "value"), torch.tensor([50.0]))


def test_list_item_profiles():
    """Registry lists all item profile names."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    registry.set_item("food_stats", "nutrition", torch.tensor([0.5]))
    registry.set_item("weapon_stats", "damage", torch.tensor([10.0]))

    profiles = registry.list_item_profiles()
    assert set(profiles) == {"food_stats", "weapon_stats"}


def test_list_item_variables_in_profile():
    """Registry lists all variables in a profile."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    registry.set_item("food_stats", "nutrition", torch.tensor([0.5]))
    registry.set_item("food_stats", "is_spoiled", torch.tensor([False]))

    variables = registry.list_item_variables("food_stats")
    assert set(variables) == {"nutrition", "is_spoiled"}
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_scoped_registry.py::test_set_item_variable -v
```

**Expected:** FAIL - set_item() not implemented

---

### Step 6: Implement item scope storage

**File:** `src/townlet/vfs/registry.py` (add methods)

```python
    # Item scope methods

    def set_item(self, profile_name: str, var_name: str, value: torch.Tensor) -> None:
        """Set item variable value for a profile.

        Args:
            profile_name: Item profile name (e.g., "food_stats")
            var_name: Variable name within profile
            value: Tensor with shape [num_instances] or [num_instances, ...]
        """
        if profile_name not in self._item_storage:
            self._item_storage[profile_name] = {}

        self._item_storage[profile_name][var_name] = value.to(self.device)

    def get_item(self, profile_name: str, var_name: str) -> torch.Tensor:
        """Get item variable value for a profile.

        Args:
            profile_name: Item profile name
            var_name: Variable name within profile

        Returns:
            Tensor with shape [num_instances] or [num_instances, ...]

        Raises:
            KeyError: If profile or variable not found
        """
        if profile_name not in self._item_storage:
            raise KeyError(
                f"Item profile '{profile_name}' not found. "
                f"Available: {list(self._item_storage.keys())}"
            )

        profile_vars = self._item_storage[profile_name]
        if var_name not in profile_vars:
            raise KeyError(
                f"Variable '{var_name}' not found in profile '{profile_name}'. "
                f"Available: {list(profile_vars.keys())}"
            )

        return profile_vars[var_name]

    def list_item_profiles(self) -> list[str]:
        """List all item profile names."""
        return list(self._item_storage.keys())

    def list_item_variables(self, profile_name: str) -> list[str]:
        """List all variables in an item profile.

        Args:
            profile_name: Item profile name

        Returns:
            List of variable names in profile

        Raises:
            KeyError: If profile not found
        """
        if profile_name not in self._item_storage:
            raise KeyError(
                f"Item profile '{profile_name}' not found. "
                f"Available: {list(self._item_storage.keys())}"
            )

        return list(self._item_storage[profile_name].keys())
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_scoped_registry.py -k "item" -v
```

**Expected:** All 5 item scope tests PASS

**Commit:**
```bash
git add src/townlet/vfs/registry.py tests/test_townlet/unit/vfs/test_scoped_registry.py
git commit -m "feat(vfs): add item scope storage to ScopedVariableRegistry"
```

---

### Step 7: Write failing tests for access control

**File:** `tests/test_townlet/unit/vfs/test_scoped_registry.py` (append)

```python
def test_check_global_access_allowed():
    """Registry allows valid global access."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))
    registry.set_global("day_count", torch.tensor(0))

    # Should not raise
    registry.check_access("global", "day_count", "read")


def test_check_global_access_denied():
    """Registry denies invalid global access."""
    from townlet.vfs.registry import AccessDeniedError

    registry = ScopedVariableRegistry(device=torch.device("cpu"))
    registry.set_global("day_count", torch.tensor(0))

    with pytest.raises(AccessDeniedError, match="write"):
        # Global variables are read-only for agents
        registry.check_access("global", "day_count", "write")


def test_check_agent_access_allowed():
    """Registry allows agent to read own variables."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))
    registry.set_agent("motivation", torch.tensor([1.0]))

    # Should not raise
    registry.check_access("agent", "motivation", "read")
    registry.check_access("agent", "motivation", "write")


def test_check_item_access_allowed():
    """Registry allows item to read/write own variables."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))
    registry.set_item("food_stats", "nutrition", torch.tensor([0.5]))

    # Should not raise
    registry.check_access("item", "food_stats.nutrition", "read")
    registry.check_access("item", "food_stats.nutrition", "write")
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_scoped_registry.py::test_check_global_access_allowed -v
```

**Expected:** FAIL - check_access() not implemented

---

### Step 8: Implement access control

**File:** `src/townlet/vfs/registry.py` (add exception and method)

```python
class AccessDeniedError(Exception):
    """Raised when access control check fails."""
    pass


class ScopedVariableRegistry:
    # ... existing code ...

    def check_access(self, scope: str, path: str, operation: str) -> None:
        """Check if access is allowed per VFS access control rules.

        Access control rules:
        - Global variables: read-only for all scopes
        - Agent variables: read/write for agent scope only
        - Item variables: read/write for item scope only

        Args:
            scope: Requesting scope ("global", "agent", "item")
            path: Variable path (e.g., "day_count", "food_stats.nutrition")
            operation: Access type ("read", "write")

        Raises:
            AccessDeniedError: If access denied
        """
        # Global variables are read-only
        if path in self._global_storage or "." not in path:
            if operation == "write":
                raise AccessDeniedError(
                    f"Global variable '{path}' is read-only. "
                    f"Cannot write from scope '{scope}'."
                )
            return  # Read allowed

        # Agent variables
        if path in self._agent_storage:
            if scope != "agent" and operation == "write":
                raise AccessDeniedError(
                    f"Agent variable '{path}' can only be written by agent scope. "
                    f"Scope '{scope}' denied."
                )
            return  # Read allowed, write allowed for agent scope

        # Item variables (profile.var format)
        if "." in path:
            profile, var = path.split(".", 1)
            if profile in self._item_storage:
                if scope != "item" and operation == "write":
                    raise AccessDeniedError(
                        f"Item variable '{path}' can only be written by item scope. "
                        f"Scope '{scope}' denied."
                    )
                return  # Read allowed, write allowed for item scope

        # Variable not found in any scope - allow for now (will fail at get/set)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_scoped_registry.py -k "access" -v
```

**Expected:** All 4 access control tests PASS

**Commit:**
```bash
git add src/townlet/vfs/registry.py tests/test_townlet/unit/vfs/test_scoped_registry.py
git commit -m "feat(vfs): add access control to ScopedVariableRegistry"
```

---

### Step 9: Add module exports

**File:** `src/townlet/vfs/registry.py` (add at top)

```python
"""Variable registry with scoped storage (global, agent, item)."""
from __future__ import annotations
import torch
from typing import Optional

__all__ = [
    "ScopedVariableRegistry",
    "AccessDeniedError",
]
```

**Verify:**
```bash
UV_CACHE_DIR=.uv-cache uv run python -c "from townlet.vfs.registry import ScopedVariableRegistry; print('OK')"
```

**Expected:** Prints "OK"

**Commit:**
```bash
git add src/townlet/vfs/registry.py
git commit -m "feat(vfs): export ScopedVariableRegistry in module API"
```

---

### Step 10: Type checking and formatting

**Run mypy:**
```bash
UV_CACHE_DIR=.uv-cache uv run mypy src/townlet/vfs/registry.py
```

**Expected:** Success

**Run ruff:**
```bash
UV_CACHE_DIR=.uv-cache uv run ruff format src/townlet/vfs/registry.py tests/test_townlet/unit/vfs/test_scoped_registry.py
UV_CACHE_DIR=.uv-cache uv run ruff check src/townlet/vfs/registry.py
```

**Expected:** No changes needed

**Run full test suite:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_scoped_registry.py -v
```

**Expected:** All ~17 tests PASS

**Commit:**
```bash
git add -u
git commit -m "test(vfs): verify all scoped registry tests pass"
```

---

## Success Criteria

✅ **17+ tests passing** (global, agent, item scopes + access control)
✅ **Three-tier storage working** (global singleton, agent batch, item profile-based)
✅ **Access control enforced** (global read-only, agent/item write to own scope)
✅ **Separate namespaces** (global, agent, item profiles don't collide)
✅ **Type checking passes** (mypy clean)
✅ **Code formatted** (ruff)

---

## Next Steps

**Task 2.3: Expression Evaluation Integration**

Wire expression evaluator into VFS:
- Topological sort for dependency ordering
- Circular dependency detection
- Expression execution context (bars, vfs, self, target)

See: `docs/plans/vfs_uplift/2025-11-19-task-2-3-expression-integration.md` (to be created)
