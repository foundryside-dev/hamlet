# Task 3.4: EffectManager Runtime - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development

**Goal:** Implement runtime effect lifecycle management with spawn/tick/despawn logic, reapply policies, and scoped effect storage.

**Architecture:** EffectManager maintains scoped collections of ActiveEffect instances, executes on_tick commands each step, handles reapply policies (stack/renew/merge/replace), and manages effect lifecycle.

**Duration:** 2 days | **Tests:** 15-20

**Dependencies:**
- ✅ Task 3.1 (Effects DTOs & Catalog) - effect catalog compilation
- ✅ Task 3.3 (Command Executor) - ExecutionContext and CommandExecutor

**Scope:**
- `src/townlet/effects/manager.py` - EffectManager and ActiveEffect
- `tests/test_townlet/unit/effects/test_effect_manager.py` - Manager tests
- `tests/test_townlet/unit/effects/test_reapply_policies.py` - Policy tests

---

## Implementation Steps

### Step 1: ActiveEffect Dataclass (TDD Start)

**Test First** (`tests/test_townlet/unit/effects/test_effect_manager.py`):

```python
"""Unit tests for EffectManager runtime."""

from dataclasses import dataclass
import pytest
import torch

from townlet.effects.manager import ActiveEffect, EffectManager
from townlet.effects.catalog import EffectCatalog, CompiledEffect
from townlet.effects.dtos import EffectScope


def test_active_effect_initialization():
    """ActiveEffect stores lifecycle state."""
    effect = ActiveEffect(
        effect_id="regen",
        instance_id=42,
        target_entity_id=3,
        scope=EffectScope.AGENT,
        intensity=1.5,
        duration_total=100,
        duration_remaining=100,
        elapsed_ticks=0,
        spawn_step=1000,
    )

    assert effect.effect_id == "regen"
    assert effect.instance_id == 42
    assert effect.target_entity_id == 3
    assert effect.intensity == 1.5
    assert effect.duration_remaining == 100
    assert effect.elapsed_ticks == 0


def test_active_effect_tracks_multiple_targets():
    """Multiple agents can have same effect type."""
    effect1 = ActiveEffect(
        effect_id="regen",
        instance_id=1,
        target_entity_id=0,
        scope=EffectScope.AGENT,
        intensity=1.0,
        duration_total=50,
        duration_remaining=50,
        elapsed_ticks=0,
        spawn_step=100,
    )

    effect2 = ActiveEffect(
        effect_id="regen",
        instance_id=2,
        target_entity_id=5,
        scope=EffectScope.AGENT,
        intensity=2.0,
        duration_total=50,
        duration_remaining=30,
        elapsed_ticks=20,
        spawn_step=100,
    )

    assert effect1.target_entity_id != effect2.target_entity_id
    assert effect1.instance_id != effect2.instance_id
    assert effect1.intensity != effect2.intensity
```

**Run and verify failure:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/test_effect_manager.py::test_active_effect_initialization -xvs
```

**Implement** (`src/townlet/effects/manager.py`):

```python
"""Runtime effect lifecycle management."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from townlet.effects.dtos import EffectScope

__all__ = [
    "ActiveEffect",
    "EffectManager",
]


@dataclass
class ActiveEffect:
    """Runtime instance of an effect attached to an entity.

    Tracks lifecycle state (duration, intensity, elapsed time) and
    references the compiled effect definition from the catalog.
    """

    effect_id: str  # Reference to catalog definition
    instance_id: int  # Unique instance ID
    target_entity_id: int  # What it's attached to (agent/item/affordance index)
    scope: EffectScope  # Where it lives (global/agent/item/affordance)

    # Lifecycle state
    intensity: float  # Current intensity multiplier
    duration_total: int  # Total ticks when spawned
    duration_remaining: int  # Ticks until despawn
    elapsed_ticks: int  # How long active
    spawn_step: int  # When it was created


class EffectManager:
    """Manages all active effects across all entities."""

    def __init__(self, device: str = "cpu"):
        """Initialize empty effect manager.

        Args:
            device: PyTorch device for tensor operations
        """
        self.device = device
        self.next_instance_id = 0

        # Scoped storage
        self.global_effects: List[ActiveEffect] = []
        self.agent_effects: Dict[int, List[ActiveEffect]] = {}  # agent_id -> effects
        self.item_effects: Dict[int, List[ActiveEffect]] = {}  # item_id -> effects
        self.affordance_effects: Dict[str, List[ActiveEffect]] = {}  # affordance_id -> effects
```

**Verify tests pass:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/test_effect_manager.py::test_active_effect_initialization -xvs
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/test_effect_manager.py::test_active_effect_tracks_multiple_targets -xvs
```

**Commit:**
```bash
git add src/townlet/effects/manager.py tests/test_townlet/unit/effects/test_effect_manager.py
git commit -m "feat(effects): add ActiveEffect dataclass for runtime lifecycle tracking

- ActiveEffect stores effect_id, instance_id, target_entity_id, scope
- Tracks lifecycle: intensity, duration_total, duration_remaining, elapsed_ticks, spawn_step
- EffectManager stub with scoped storage (global/agent/item/affordance effects)
- 2 passing tests for ActiveEffect initialization and multi-target tracking

Part of Task 3.4 (EffectManager Runtime)
Ref: docs/plans/vfs_uplift/2025-11-19-task-3-4-effect-manager.md"
```

---

### Step 2: Spawn Effect (Stack Policy)

**Test First:**

```python
def test_spawn_effect_creates_active_instance(catalog_fixture):
    """EffectManager.spawn_effect() creates ActiveEffect."""
    manager = EffectManager(device="cpu")
    manager.catalog = catalog_fixture  # Catalog with 'regen' effect

    effect = manager.spawn_effect(
        effect_id="regen",
        target_entity_id=5,
        scope=EffectScope.AGENT,
        duration=100,
        intensity=1.0,
        current_step=1000,
    )

    assert effect.effect_id == "regen"
    assert effect.target_entity_id == 5
    assert effect.duration_total == 100
    assert effect.intensity == 1.0
    assert effect.spawn_step == 1000
    assert effect.instance_id == 0  # First instance

    # Check stored in scoped collection
    assert 5 in manager.agent_effects
    assert effect in manager.agent_effects[5]


def test_spawn_effect_stack_policy_allows_multiple(catalog_fixture):
    """Stack policy allows multiple instances of same effect."""
    manager = EffectManager(device="cpu")
    manager.catalog = catalog_fixture  # 'regen' with reapply_policy=STACK

    effect1 = manager.spawn_effect("regen", 3, EffectScope.AGENT, 50, 1.0, 100)
    effect2 = manager.spawn_effect("regen", 3, EffectScope.AGENT, 50, 1.5, 110)

    assert len(manager.agent_effects[3]) == 2
    assert effect1.instance_id != effect2.instance_id
    assert effect1.intensity == 1.0
    assert effect2.intensity == 1.5
```

**Run and verify failure:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/test_effect_manager.py::test_spawn_effect_creates_active_instance -xvs
```

**Implement:**

```python
# In EffectManager class

def __init__(self, catalog, device: str = "cpu"):
    """Initialize effect manager with compiled catalog.

    Args:
        catalog: Compiled EffectCatalog from world compiler
        device: PyTorch device for tensor operations
    """
    self.catalog = catalog
    self.device = device
    self.current_step = 0  # Track environment step
    self.next_instance_id = 0

    # Scoped storage
    self.global_effects: List[ActiveEffect] = []
    self.agent_effects: Dict[int, List[ActiveEffect]] = {}
    self.item_effects: Dict[int, List[ActiveEffect]] = {}
    self.affordance_effects: Dict[str, List[ActiveEffect]] = {}


def spawn_effect(
    self,
    effect_id: str,
    target_entity_id: int,
    scope: EffectScope,
    duration: int,
    intensity: float,
    current_step: int,
) -> ActiveEffect:
    """Spawn new effect instance.

    Args:
        effect_id: Effect definition ID from catalog
        target_entity_id: Entity to attach effect to (agent/item/affordance index)
        scope: Effect scope (global/agent/item/affordance)
        duration: Effect duration in ticks
        intensity: Effect intensity multiplier
        current_step: Current environment step

    Returns:
        ActiveEffect instance
    """
    # Get compiled effect definition
    effect_def = self.catalog.effects[effect_id]

    # For now: STACK policy only (create new instance)
    # TODO: Handle other reapply policies in Step 3

    # Create new instance
    active = ActiveEffect(
        effect_id=effect_id,
        instance_id=self.next_instance_id,
        target_entity_id=target_entity_id,
        scope=scope,
        intensity=intensity,
        duration_total=duration,
        duration_remaining=duration,
        elapsed_ticks=0,
        spawn_step=current_step,
    )
    self.next_instance_id += 1

    # Store in scoped collection
    self._add_to_scope(active)

    return active


def _add_to_scope(self, effect: ActiveEffect) -> None:
    """Add effect to appropriate scoped collection."""
    if effect.scope == EffectScope.GLOBAL:
        self.global_effects.append(effect)
    elif effect.scope == EffectScope.AGENT:
        if effect.target_entity_id not in self.agent_effects:
            self.agent_effects[effect.target_entity_id] = []
        self.agent_effects[effect.target_entity_id].append(effect)
    elif effect.scope == EffectScope.ITEM:
        if effect.target_entity_id not in self.item_effects:
            self.item_effects[effect.target_entity_id] = []
        self.item_effects[effect.target_entity_id].append(effect)
    elif effect.scope == EffectScope.AFFORDANCE:
        # Note: affordance_effects keyed by affordance_id (string), not entity_id
        # For now, store by string representation of target_entity_id
        key = str(effect.target_entity_id)
        if key not in self.affordance_effects:
            self.affordance_effects[key] = []
        self.affordance_effects[key].append(effect)
```

**Verify tests pass:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/test_effect_manager.py::test_spawn_effect_creates_active_instance -xvs
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/test_effect_manager.py::test_spawn_effect_stack_policy_allows_multiple -xvs
```

**Commit:**
```bash
git add src/townlet/effects/manager.py tests/test_townlet/unit/effects/test_effect_manager.py
git commit -m "feat(effects): implement spawn_effect() with stack policy

- spawn_effect() creates ActiveEffect instances from catalog definitions
- _add_to_scope() routes effects to global/agent/item/affordance collections
- Stack policy (default): allows multiple instances of same effect
- Auto-incrementing instance_id for uniqueness
- 2 passing tests for spawn and stack policy

Part of Task 3.4 (EffectManager Runtime)
Ref: docs/plans/vfs_uplift/2025-11-19-task-3-4-effect-manager.md"
```

---

### Step 3: Reapply Policies (Renew, Merge, Replace)

**Test First** (`tests/test_townlet/unit/effects/test_reapply_policies.py`):

```python
"""Unit tests for effect reapply policies."""

import pytest

from townlet.effects.manager import EffectManager
from townlet.effects.dtos import EffectScope, ReapplyPolicy


def test_renew_policy_resets_duration(catalog_with_policies):
    """Renew policy resets duration_remaining to full."""
    manager = EffectManager(catalog=catalog_with_policies, device="cpu")
    catalog_with_policies.effects["shield"].reapply_policy = ReapplyPolicy.RENEW

    # Spawn initial effect
    effect1 = manager.spawn_effect("shield", 2, EffectScope.AGENT, 100, 1.0, 1000)
    effect1.duration_remaining = 20  # Simulate decay

    # Reapply same effect
    effect2 = manager.spawn_effect("shield", 2, EffectScope.AGENT, 100, 1.0, 1050)

    # Should be same instance with renewed duration
    assert len(manager.agent_effects[2]) == 1
    assert effect2.instance_id == effect1.instance_id
    assert effect2.duration_remaining == 100  # Reset to full


def test_merge_policy_adds_intensity(catalog_with_policies):
    """Merge policy accumulates intensity."""
    manager = EffectManager(catalog=catalog_with_policies, device="cpu")
    catalog_with_policies.effects["poison"].reapply_policy = ReapplyPolicy.MERGE

    effect1 = manager.spawn_effect("poison", 4, EffectScope.AGENT, 50, 1.0, 500)
    effect2 = manager.spawn_effect("poison", 4, EffectScope.AGENT, 50, 0.5, 510)

    assert len(manager.agent_effects[4]) == 1
    assert effect2.instance_id == effect1.instance_id
    assert effect2.intensity == 1.5  # 1.0 + 0.5


def test_replace_policy_despawns_old(catalog_with_policies):
    """Replace policy removes old instance and creates new."""
    manager = EffectManager(catalog=catalog_with_policies, device="cpu")
    catalog_with_policies.effects["buff"].reapply_policy = ReapplyPolicy.REPLACE

    effect1 = manager.spawn_effect("buff", 7, EffectScope.AGENT, 80, 2.0, 200)
    effect2 = manager.spawn_effect("buff", 7, EffectScope.AGENT, 80, 3.0, 210)

    assert len(manager.agent_effects[7]) == 1
    assert effect2.instance_id != effect1.instance_id  # New instance
    assert effect2.intensity == 3.0  # New intensity
```

**Run and verify failure:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/test_reapply_policies.py -xvs
```

**Implement:**

```python
# Update spawn_effect() method

def spawn_effect(
    self,
    effect_id: str,
    target_entity_id: int,
    scope: EffectScope,
    duration: int,
    intensity: float,
    current_step: int,
) -> ActiveEffect:
    """Spawn new effect instance, handling reapply policies."""
    effect_def = self.catalog.effects[effect_id]

    # Check for existing effect on same target
    existing = self._find_existing(effect_id, target_entity_id, scope)

    if existing:
        # Handle reapply policy
        if effect_def.reapply_policy == ReapplyPolicy.RENEW:
            # Reset duration to full
            existing.duration_remaining = duration
            return existing

        elif effect_def.reapply_policy == ReapplyPolicy.MERGE:
            # Accumulate intensity
            existing.intensity += intensity
            return existing

        elif effect_def.reapply_policy == ReapplyPolicy.REPLACE:
            # Remove old instance
            self._remove_from_scope(existing)
            # Continue to create new instance below

        # STACK: Do nothing, create new instance below

    # Create new instance
    active = ActiveEffect(
        effect_id=effect_id,
        instance_id=self.next_instance_id,
        target_entity_id=target_entity_id,
        scope=scope,
        intensity=intensity,
        duration_total=duration,
        duration_remaining=duration,
        elapsed_ticks=0,
        spawn_step=current_step,
    )
    self.next_instance_id += 1

    self._add_to_scope(active)
    return active


def _find_existing(
    self, effect_id: str, target_entity_id: int, scope: EffectScope
) -> ActiveEffect | None:
    """Find existing effect on target."""
    collection = self._get_scope_collection(target_entity_id, scope)
    if collection is None:
        return None

    for effect in collection:
        if effect.effect_id == effect_id:
            return effect

    return None


def _get_scope_collection(
    self, target_entity_id: int, scope: EffectScope
) -> List[ActiveEffect] | None:
    """Get scoped collection for target."""
    if scope == EffectScope.GLOBAL:
        return self.global_effects
    elif scope == EffectScope.AGENT:
        return self.agent_effects.get(target_entity_id)
    elif scope == EffectScope.ITEM:
        return self.item_effects.get(target_entity_id)
    elif scope == EffectScope.AFFORDANCE:
        return self.affordance_effects.get(str(target_entity_id))
    return None


def _remove_from_scope(self, effect: ActiveEffect) -> None:
    """Remove effect from scoped collection."""
    collection = self._get_scope_collection(effect.target_entity_id, effect.scope)
    if collection is not None and effect in collection:
        collection.remove(effect)
```

**Verify tests pass:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/test_reapply_policies.py -xvs
```

**Commit:**
```bash
git add src/townlet/effects/manager.py tests/test_townlet/unit/effects/test_reapply_policies.py
git commit -m "feat(effects): implement reapply policies (renew/merge/replace)

- RENEW: Resets duration_remaining to full
- MERGE: Accumulates intensity
- REPLACE: Despawns old instance, creates new
- STACK: Default, allows multiple instances
- _find_existing() locates matching effect on target
- _remove_from_scope() removes effect from collection
- 3 passing tests for reapply policy behavior

Part of Task 3.4 (EffectManager Runtime)
Ref: docs/plans/vfs_uplift/2025-11-19-task-3-4-effect-manager.md"
```

---

### Step 4: Tick Method (Lifecycle Updates)

**Test First:**

```python
def test_tick_updates_elapsed_and_remaining(catalog_fixture):
    """tick() advances lifecycle counters."""
    manager = EffectManager(catalog=catalog_fixture, device="cpu")
    effect = manager.spawn_effect("regen", 1, EffectScope.AGENT, 100, 1.0, 500)

    # Initial state
    assert effect.elapsed_ticks == 0
    assert effect.duration_remaining == 100

    # Tick once
    manager.tick(current_step=501)

    assert effect.elapsed_ticks == 1
    assert effect.duration_remaining == 99


def test_tick_despawns_expired_effects(catalog_fixture):
    """tick() removes effects when duration_remaining reaches 0."""
    manager = EffectManager(catalog=catalog_fixture, device="cpu")
    effect = manager.spawn_effect("regen", 2, EffectScope.AGENT, 3, 1.0, 100)

    manager.tick(current_step=101)  # remaining=2
    manager.tick(current_step=102)  # remaining=1
    assert len(manager.agent_effects[2]) == 1

    manager.tick(current_step=103)  # remaining=0, despawn

    assert 2 not in manager.agent_effects or len(manager.agent_effects[2]) == 0


def test_tick_handles_multiple_scopes(catalog_fixture):
    """tick() processes effects from all scopes."""
    manager = EffectManager(catalog=catalog_fixture, device="cpu")

    global_effect = manager.spawn_effect("day_cycle", 0, EffectScope.GLOBAL, 200, 1.0, 10)
    agent_effect = manager.spawn_effect("regen", 5, EffectScope.AGENT, 50, 1.0, 10)

    manager.tick(current_step=11)

    assert global_effect.elapsed_ticks == 1
    assert agent_effect.elapsed_ticks == 1
```

**Run and verify failure:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/test_effect_manager.py::test_tick_updates_elapsed_and_remaining -xvs
```

**Implement:**

```python
def tick(self, current_step: int) -> None:
    """Execute all active effects for one timestep.

    Args:
        current_step: Current environment step
    """
    self.current_step = current_step

    # Process all scopes
    all_collections = [
        self.global_effects,
        *self.agent_effects.values(),
        *self.item_effects.values(),
        *self.affordance_effects.values(),
    ]

    for collection in all_collections:
        # Process in reverse to safely remove during iteration
        for i in range(len(collection) - 1, -1, -1):
            effect = collection[i]

            # Update lifecycle
            effect.elapsed_ticks += 1
            effect.duration_remaining -= 1

            # Check for expiry
            if effect.duration_remaining <= 0:
                # Despawn (remove from collection)
                collection.pop(i)

                # TODO: Execute on_despawn commands in Step 5


def get_all_active_effects(self) -> List[ActiveEffect]:
    """Get all active effects across all scopes (for testing)."""
    result = []
    result.extend(self.global_effects)
    for effects in self.agent_effects.values():
        result.extend(effects)
    for effects in self.item_effects.values():
        result.extend(effects)
    for effects in self.affordance_effects.values():
        result.extend(effects)
    return result
```

**Verify tests pass:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/test_effect_manager.py::test_tick_updates_elapsed_and_remaining -xvs
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/test_effect_manager.py::test_tick_despawns_expired_effects -xvs
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/test_effect_manager.py::test_tick_handles_multiple_scopes -xvs
```

**Commit:**
```bash
git add src/townlet/effects/manager.py tests/test_townlet/unit/effects/test_effect_manager.py
git commit -m "feat(effects): implement tick() for lifecycle updates and auto-despawn

- tick() advances elapsed_ticks and decrements duration_remaining
- Auto-despawn when duration_remaining reaches 0
- Processes all scopes (global/agent/item/affordance)
- get_all_active_effects() helper for testing
- 3 passing tests for tick lifecycle and multi-scope handling

Part of Task 3.4 (EffectManager Runtime)
Ref: docs/plans/vfs_uplift/2025-11-19-task-3-4-effect-manager.md"
```

---

### Step 5: Command Execution Integration (on_tick)

**Test First:**

```python
def test_tick_executes_on_tick_commands(catalog_with_commands, mock_executor):
    """tick() executes on_tick commands for each active effect."""
    manager = EffectManager(catalog=catalog_with_commands, device="cpu")
    manager.command_executor = mock_executor  # Inject mock

    effect = manager.spawn_effect("regen", 3, EffectScope.AGENT, 50, 1.0, 100)

    manager.tick(current_step=101)

    # Verify command executor called with effect's on_tick commands
    assert mock_executor.execute_commands_called
    assert mock_executor.last_effect == effect


def test_tick_executes_on_despawn_before_removal(catalog_with_commands, mock_executor):
    """on_despawn commands execute before effect removed."""
    manager = EffectManager(catalog=catalog_with_commands, device="cpu")
    manager.command_executor = mock_executor

    effect = manager.spawn_effect("buff", 5, EffectScope.AGENT, 2, 1.0, 200)

    manager.tick(current_step=201)  # remaining=1
    manager.tick(current_step=202)  # remaining=0, despawn

    # Verify on_despawn executed
    assert mock_executor.on_despawn_called
    assert 5 not in manager.agent_effects  # Effect removed
```

**Run and verify failure:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/test_effect_manager.py::test_tick_executes_on_tick_commands -xvs
```

**Implement:**

```python
# In __init__
def __init__(self, catalog, command_executor, device: str = "cpu"):
    """Initialize effect manager.

    Args:
        catalog: Compiled EffectCatalog
        command_executor: CommandExecutor for running effect commands
        device: PyTorch device
    """
    self.catalog = catalog
    self.command_executor = command_executor
    self.device = device
    # ... rest of init


# Update tick()
def tick(self, current_step: int, env_state) -> None:
    """Execute all active effects for one timestep.

    Args:
        current_step: Current environment step
        env_state: Environment state for command execution
    """
    self.current_step = current_step

    all_collections = [
        self.global_effects,
        *self.agent_effects.values(),
        *self.item_effects.values(),
        *self.affordance_effects.values(),
    ]

    for collection in all_collections:
        for i in range(len(collection) - 1, -1, -1):
            effect = collection[i]

            # Build execution context
            context = self._build_context(effect, env_state)

            # Execute on_tick commands
            effect_def = self.catalog.effects[effect.effect_id]
            self.command_executor.execute_commands(
                effect_def.on_tick_commands, context
            )

            # Update lifecycle
            effect.elapsed_ticks += 1
            effect.duration_remaining -= 1

            # Check for expiry
            if effect.duration_remaining <= 0:
                # Execute on_despawn commands
                self.command_executor.execute_commands(
                    effect_def.on_despawn_commands, context
                )

                # Remove from collection
                collection.pop(i)


def _build_context(self, effect: ActiveEffect, env_state):
    """Build ExecutionContext for effect.

    Args:
        effect: Active effect instance
        env_state: Environment state (bars, VFS, etc.)

    Returns:
        ExecutionContext with effect and target references
    """
    from townlet.effects.executor import ExecutionContext

    return ExecutionContext(
        effect=effect,
        target_entity_id=effect.target_entity_id,
        bars=env_state.bars,
        vfs_global=env_state.vfs_global,
        vfs_agent=env_state.vfs_agent,
        vfs_item=env_state.vfs_item,
        step_count=self.current_step,
        time_of_day=env_state.temporal.get("time_of_day", 0.0),
    )
```

**Verify tests pass:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/test_effect_manager.py::test_tick_executes_on_tick_commands -xvs
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/test_effect_manager.py::test_tick_executes_on_despawn_before_removal -xvs
```

**Commit:**
```bash
git add src/townlet/effects/manager.py tests/test_townlet/unit/effects/test_effect_manager.py
git commit -m "feat(effects): integrate command execution in tick() lifecycle

- tick() executes on_tick commands via CommandExecutor
- on_despawn commands execute before effect removal
- _build_context() creates ExecutionContext with effect/target references
- Requires env_state parameter for context building
- 2 passing tests for command execution integration

Part of Task 3.4 (EffectManager Runtime)
Ref: docs/plans/vfs_uplift/2025-11-19-task-3-4-effect-manager.md"
```

---

### Step 6: Module Exports

**Update `src/townlet/effects/__init__.py`:**

```python
"""Effects system for HAMLET.

Provides declarative command pipeline language for simulation behavior.
Effects replace old mutation systems with composable GPU-native operations.
"""

from townlet.effects.catalog import EffectCatalog, CompiledEffect
from townlet.effects.dtos import (
    CommandConfig,
    EffectDefinitionConfig,
    EffectScope,
    EffectsConfig,
    ReapplyPolicy,
)
from townlet.effects.executor import CommandExecutor, ExecutionContext
from townlet.effects.manager import ActiveEffect, EffectManager
from townlet.effects.parser import CommandNode, CommandParser, CommandType

__all__ = [
    # DTOs
    "CommandConfig",
    "EffectDefinitionConfig",
    "EffectsConfig",
    "EffectScope",
    "ReapplyPolicy",
    # Catalog
    "EffectCatalog",
    "CompiledEffect",
    # Parser
    "CommandNode",
    "CommandParser",
    "CommandType",
    # Executor
    "CommandExecutor",
    "ExecutionContext",
    # Manager
    "ActiveEffect",
    "EffectManager",
]
```

**Commit:**
```bash
git add src/townlet/effects/__init__.py
git commit -m "feat(effects): export EffectManager and ActiveEffect in module API

- Added ActiveEffect and EffectManager to __all__
- Complete Phase 3 public API: DTOs, Catalog, Parser, Executor, Manager

Part of Task 3.4 (EffectManager Runtime)
Ref: docs/plans/vfs_uplift/2025-11-19-task-3-4-effect-manager.md"
```

---

### Step 7: Full Test Suite Verification

**Run all effect manager tests:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/test_effect_manager.py -xvs
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/test_reapply_policies.py -xvs
```

**Run full effects system test suite:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/ -xvs
```

**Expected:** 15-20 passing tests for EffectManager

**Verify no regressions:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/ -x
```

---

## Success Criteria

**Code:**
- ✅ ActiveEffect dataclass with lifecycle state
- ✅ spawn_effect() creates instances with reapply policy handling
- ✅ Reapply policies: stack, renew, merge, replace
- ✅ tick() executes on_tick commands and manages lifecycle
- ✅ on_despawn commands execute before removal
- ✅ Scoped storage (global/agent/item/affordance)

**Tests:**
- ✅ 15-20 tests passing
- ✅ ActiveEffect initialization and multi-target tracking
- ✅ spawn_effect() with stack policy
- ✅ Reapply policies (3 tests: renew, merge, replace)
- ✅ tick() lifecycle updates (elapsed, remaining, auto-despawn)
- ✅ tick() multi-scope handling
- ✅ Command execution integration (on_tick, on_despawn)

**Integration:**
- ✅ Module exports include EffectManager and ActiveEffect
- ✅ No regressions in existing tests

---

## Notes for Implementer

**Scope Management:**
- Scoped collections prevent O(n) searches across all effects
- GLOBAL effects stored in list (singleton)
- AGENT/ITEM effects keyed by entity_id
- AFFORDANCE effects keyed by affordance_id string

**Reapply Policy Semantics:**
- **STACK**: Multiple instances allowed (default for most effects)
- **RENEW**: Reset duration (buffs that refresh)
- **MERGE**: Accumulate intensity (poisons that stack)
- **REPLACE**: Remove old, create new (status effects that override)

**Lifecycle Order:**
1. Execute on_tick commands
2. Update elapsed_ticks += 1
3. Update duration_remaining -= 1
4. If duration_remaining <= 0:
   - Execute on_despawn commands
   - Remove from collection

**Context Building:**
- ExecutionContext provides access to bars, VFS, temporal state
- Resolves paths like `target.bar.energy` to GPU tensors
- See Task 3.3 for ExecutionContext implementation

**Integration Point:**
- VectorizedHamletEnv will call `effect_manager.tick(self.state)` in Step 5
- EffectManager needs env_state for context building (bars, VFS, temporal)

**Testing Strategy:**
- Mock CommandExecutor for isolation
- Real catalog fixtures with compiled effects
- Verify reapply policies with multiple spawn calls
- Test all scopes (global, agent, item, affordance)

---

*Ready for execution by Claude using superpowers:executing-plans or superpowers:subagent-driven-development*
