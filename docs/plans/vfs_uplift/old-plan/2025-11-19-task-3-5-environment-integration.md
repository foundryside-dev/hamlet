# Task 3.5: Environment Integration - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development

**Goal:** Wire EffectManager into VectorizedHamletEnv step loop and verify end-to-end effects system functionality.

**Architecture:** VectorizedHamletEnv initializes EffectManager from compiled world catalog and calls `effect_manager.tick(self.state)` each step after action execution.

**Duration:** 1 day | **Tests:** 5-10

**Dependencies:**
- ✅ Task 3.1 (Effects DTOs & Catalog) - effects.yaml compilation
- ✅ Task 3.3 (Command Executor) - command execution
- ✅ Task 3.4 (EffectManager Runtime) - lifecycle management

**Scope:**
- `src/townlet/environment/vectorized_env.py` - Wire EffectManager into step()
- `tests/test_townlet/integration/test_effects_smoke.py` - End-to-end integration
- `configs/test/effects_smoke/effects.yaml` - Smoke test effects

---

## Implementation Steps

### Step 1: VectorizedHamletEnv Integration (TDD Start)

**Test First** (`tests/test_townlet/integration/test_effects_smoke.py`):

```python
"""Integration tests for effects system with VectorizedHamletEnv."""

import pytest
import torch
from pathlib import Path

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.config.hamlet_config_dto import HamletConfig


@pytest.fixture
def effects_smoke_config():
    """Load effects_smoke config."""
    config_dir = Path("/home/john/hamlet/configs/test/effects_smoke")
    return HamletConfig.from_directory(config_dir)


def test_environment_initializes_effect_manager(effects_smoke_config):
    """VectorizedHamletEnv initializes EffectManager from compiled world."""
    env = VectorizedHamletEnv(
        config=effects_smoke_config,
        batch_size=4,
        device="cpu",
    )

    # Verify EffectManager initialized
    assert hasattr(env, "effect_manager")
    assert env.effect_manager is not None
    assert env.effect_manager.catalog is not None

    # Verify catalog loaded from effects.yaml
    assert "energy_regen" in env.effect_manager.catalog.effects
    assert "health_boost" in env.effect_manager.catalog.effects


def test_environment_ticks_effects_each_step(effects_smoke_config):
    """env.step() calls effect_manager.tick()."""
    env = VectorizedHamletEnv(
        config=effects_smoke_config,
        batch_size=2,
        device="cpu",
    )

    # Spawn effect manually (before affordance interactions work)
    from townlet.effects.dtos import EffectScope
    effect = env.effect_manager.spawn_effect(
        effect_id="energy_regen",
        target_entity_id=0,
        scope=EffectScope.AGENT,
        duration=10,
        intensity=1.0,
        current_step=0,
    )

    assert effect.elapsed_ticks == 0

    # Step environment
    actions = torch.zeros(2, dtype=torch.long)  # WAIT actions
    obs, reward, done, info = env.step(actions)

    # Verify effect ticked
    assert effect.elapsed_ticks == 1
    assert effect.duration_remaining == 9


def test_effects_auto_despawn_after_duration(effects_smoke_config):
    """Effects automatically despawn when duration_remaining reaches 0."""
    env = VectorizedHamletEnv(
        config=effects_smoke_config,
        batch_size=1,
        device="cpu",
    )

    from townlet.effects.dtos import EffectScope
    effect = env.effect_manager.spawn_effect(
        effect_id="health_boost",
        target_entity_id=0,
        scope=EffectScope.AGENT,
        duration=3,
        intensity=1.0,
        current_step=0,
    )

    # Step 3 times
    actions = torch.zeros(1, dtype=torch.long)
    for _ in range(3):
        env.step(actions)

    # Effect should be despawned
    active_effects = env.effect_manager.get_all_active_effects()
    assert effect not in active_effects
```

**Run and verify failure:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_effects_smoke.py::test_environment_initializes_effect_manager -xvs
```

**Implement** (`src/townlet/environment/vectorized_env.py`):

```python
# In VectorizedHamletEnv.__init__

def __init__(
    self,
    config: HamletConfig,
    batch_size: int,
    device: str = "cpu",
    curriculum_strategy=None,
    exploration_strategy=None,
):
    """Initialize vectorized HAMLET environment.

    Args:
        config: Complete HAMLET configuration
        batch_size: Number of parallel agents
        device: PyTorch device
        curriculum_strategy: Optional curriculum for dynamic difficulty
        exploration_strategy: Optional intrinsic exploration
    """
    # ... existing initialization ...

    # NEW: Initialize EffectManager
    from townlet.effects.manager import EffectManager
    from townlet.effects.executor import CommandExecutor

    # Create command executor
    self.command_executor = CommandExecutor(
        expression_evaluator=self.expression_evaluator,  # From VFS integration
        device=self.device,
    )

    # Create effect manager
    self.effect_manager = EffectManager(
        catalog=self.compiled_universe.world.effect_catalog,
        command_executor=self.command_executor,
        device=self.device,
    )

    # ... rest of initialization ...
```

**Update `step()` method:**

```python
def step(self, actions: torch.Tensor):
    """Execute one environment step.

    Args:
        actions: [batch_size] action indices

    Returns:
        observations: [batch_size, obs_dim]
        rewards: [batch_size]
        dones: [batch_size]
        infos: dict
    """
    self.step_count += 1

    # ... existing action execution ...

    # Apply cascades (meter dependencies)
    self._apply_cascades()

    # NEW: Execute all active effects
    self.effect_manager.tick(
        current_step=self.step_count,
        env_state=self.state,  # Pass state for context building
    )

    # ... existing observation, reward, done computation ...

    return observations, rewards, dones, infos
```

**Verify tests pass:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_effects_smoke.py::test_environment_initializes_effect_manager -xvs
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_effects_smoke.py::test_environment_ticks_effects_each_step -xvs
```

**Commit:**
```bash
git add src/townlet/environment/vectorized_env.py tests/test_townlet/integration/test_effects_smoke.py
git commit -m "feat(environment): integrate EffectManager into VectorizedHamletEnv

- Initialize EffectManager from compiled world.effect_catalog
- Create CommandExecutor with expression evaluator
- Call effect_manager.tick() in step() after cascades
- Pass env_state for ExecutionContext building
- 3 passing integration tests for initialization, tick, and auto-despawn

Part of Task 3.5 (Environment Integration)
Ref: docs/plans/vfs_uplift/2025-11-19-task-3-5-environment-integration.md"
```

---

### Step 2: Effects Smoke Config (End-to-End Test Data)

**Create `configs/test/effects_smoke/effects.yaml`:**

```yaml
# Effects Smoke Test Configuration
# Tests: Basic effect definitions, reapply policies, command execution

version: "1.0"

effect_definitions:
  - id: energy_regen
    description: "Regenerates energy over time"
    scope: agent
    duration: 20
    intensity: 1.0
    reapply_policy: renew

    on_spawn: []

    on_tick:
      - modify: target.bar.energy
        value: "clamp(target.bar.energy + (0.05 * intensity), 0.0, 1.0)"

    on_despawn: []

  - id: health_boost
    description: "Instant health boost on spawn"
    scope: agent
    duration: 1
    intensity: 1.0
    reapply_policy: stack

    on_spawn:
      - modify: target.bar.health
        value: "clamp(target.bar.health + (0.2 * intensity), 0.0, 1.0)"

    on_tick: []

    on_despawn: []

  - id: poison
    description: "Damage over time"
    scope: agent
    duration: 10
    intensity: 1.0
    reapply_policy: merge

    on_spawn: []

    on_tick:
      - modify: target.bar.health
        value: "clamp(target.bar.health - (0.02 * intensity), 0.0, 1.0)"

    on_despawn: []

  - id: buff_replace
    description: "Test REPLACE policy"
    scope: agent
    duration: 15
    intensity: 1.0
    reapply_policy: replace

    on_spawn: []
    on_tick: []
    on_despawn: []

  - id: global_day_cycle
    description: "Global time-based effect"
    scope: global
    duration: 1000
    intensity: 1.0
    reapply_policy: stack

    on_spawn: []

    on_tick:
      - modify: global.vfs.is_night
        value: "temporal.tick % 24 >= 18"

    on_despawn: []
```

**Test:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_effects_smoke.py -xvs
```

**Commit:**
```bash
git add configs/test/effects_smoke/effects.yaml
git commit -m "feat(config): add effects_smoke test configuration

- energy_regen: RENEW policy, on_tick energy modification
- health_boost: STACK policy, on_spawn instant boost
- poison: MERGE policy, on_tick damage over time
- buff_replace: REPLACE policy test case
- global_day_cycle: GLOBAL scope, VFS variable modification

Part of Task 3.5 (Environment Integration)
Ref: docs/plans/vfs_uplift/2025-11-19-task-3-5-environment-integration.md"
```

---

### Step 3: Command Execution Verification

**Test First:**

```python
def test_effect_modifies_bar_values(effects_smoke_config):
    """Effects with modify commands change bar values."""
    env = VectorizedHamletEnv(
        config=effects_smoke_config,
        batch_size=1,
        device="cpu",
    )

    # Get initial energy
    initial_energy = env.state.bars[0, env.bar_name_to_idx["energy"]].item()

    # Spawn energy_regen effect
    from townlet.effects.dtos import EffectScope
    env.effect_manager.spawn_effect(
        effect_id="energy_regen",
        target_entity_id=0,
        scope=EffectScope.AGENT,
        duration=5,
        intensity=1.0,
        current_step=0,
    )

    # Step once
    actions = torch.zeros(1, dtype=torch.long)
    env.step(actions)

    # Energy should increase by 0.05
    new_energy = env.state.bars[0, env.bar_name_to_idx["energy"]].item()
    assert new_energy > initial_energy
    assert abs(new_energy - (initial_energy + 0.05)) < 1e-5


def test_on_spawn_commands_execute_immediately(effects_smoke_config):
    """on_spawn commands execute when effect spawned."""
    env = VectorizedHamletEnv(
        config=effects_smoke_config,
        batch_size=1,
        device="cpu",
    )

    # Set health to 0.5
    env.state.bars[0, env.bar_name_to_idx["health"]] = 0.5
    initial_health = 0.5

    # Spawn health_boost (on_spawn adds 0.2 health)
    from townlet.effects.dtos import EffectScope
    env.effect_manager.spawn_effect(
        effect_id="health_boost",
        target_entity_id=0,
        scope=EffectScope.AGENT,
        duration=1,
        intensity=1.0,
        current_step=0,
    )

    # Health should increase immediately (before step)
    new_health = env.state.bars[0, env.bar_name_to_idx["health"]].item()
    assert new_health > initial_health
    assert abs(new_health - 0.7) < 1e-5
```

**Run and verify failure:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_effects_smoke.py::test_effect_modifies_bar_values -xvs
```

**Implement:**

This should work if Task 3.3 (CommandExecutor) and Task 3.4 (EffectManager) are correctly implemented. If tests fail, debug:

1. Check ExecutionContext path resolution
2. Verify expression evaluation (clamp, arithmetic)
3. Ensure GPU tensor mutations work
4. Verify on_spawn commands execute in spawn_effect()

**Verify tests pass:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_effects_smoke.py::test_effect_modifies_bar_values -xvs
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_effects_smoke.py::test_on_spawn_commands_execute_immediately -xvs
```

**Commit:**
```bash
git add tests/test_townlet/integration/test_effects_smoke.py
git commit -m "test(effects): verify command execution modifies bars

- energy_regen on_tick increases energy by 0.05 per step
- health_boost on_spawn increases health by 0.2 immediately
- 2 passing tests for modify command execution

Part of Task 3.5 (Environment Integration)
Ref: docs/plans/vfs_uplift/2025-11-19-task-3-5-environment-integration.md"
```

---

### Step 4: Reapply Policy Integration Test

**Test First:**

```python
def test_renew_policy_resets_duration_in_environment(effects_smoke_config):
    """RENEW policy resets effect duration in live environment."""
    env = VectorizedHamletEnv(
        config=effects_smoke_config,
        batch_size=1,
        device="cpu",
    )

    from townlet.effects.dtos import EffectScope

    # Spawn effect with duration=5
    effect = env.effect_manager.spawn_effect(
        effect_id="energy_regen",  # Has RENEW policy
        target_entity_id=0,
        scope=EffectScope.AGENT,
        duration=5,
        intensity=1.0,
        current_step=0,
    )

    # Step twice (duration should be 3)
    actions = torch.zeros(1, dtype=torch.long)
    env.step(actions)
    env.step(actions)
    assert effect.duration_remaining == 3

    # Reapply (should reset to 5)
    env.effect_manager.spawn_effect(
        effect_id="energy_regen",
        target_entity_id=0,
        scope=EffectScope.AGENT,
        duration=5,
        intensity=1.0,
        current_step=2,
    )

    assert effect.duration_remaining == 5  # Renewed


def test_merge_policy_stacks_intensity(effects_smoke_config):
    """MERGE policy accumulates intensity for poison."""
    env = VectorizedHamletEnv(
        config=effects_smoke_config,
        batch_size=1,
        device="cpu",
    )

    from townlet.effects.dtos import EffectScope

    effect = env.effect_manager.spawn_effect(
        effect_id="poison",  # Has MERGE policy
        target_entity_id=0,
        scope=EffectScope.AGENT,
        duration=10,
        intensity=1.0,
        current_step=0,
    )

    # Apply again with intensity=0.5
    env.effect_manager.spawn_effect(
        effect_id="poison",
        target_entity_id=0,
        scope=EffectScope.AGENT,
        duration=10,
        intensity=0.5,
        current_step=1,
    )

    assert effect.intensity == 1.5  # Merged
```

**Run and verify failure:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_effects_smoke.py::test_renew_policy_resets_duration_in_environment -xvs
```

**Implement:**

Should work from Task 3.4 implementation. If tests fail, verify:
- Reapply policy handling in spawn_effect()
- _find_existing() correctly locates matching effects

**Verify tests pass:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_effects_smoke.py::test_renew_policy_resets_duration_in_environment -xvs
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_effects_smoke.py::test_merge_policy_stacks_intensity -xvs
```

**Commit:**
```bash
git add tests/test_townlet/integration/test_effects_smoke.py
git commit -m "test(effects): verify reapply policies in live environment

- RENEW policy resets duration_remaining
- MERGE policy accumulates intensity
- 2 passing integration tests for policy behavior

Part of Task 3.5 (Environment Integration)
Ref: docs/plans/vfs_uplift/2025-11-19-task-3-5-environment-integration.md"
```

---

### Step 5: Full Integration Test Suite

**Run all effects integration tests:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_effects_smoke.py -xvs
```

**Expected:** 5-10 passing tests

**Run full Phase 3 test suite:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/effects/ -xvs
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/test_effects_smoke.py -xvs
```

**Expected:** 75+ passing tests total (DTOs + Parser + Executor + Manager + Integration)

**Verify no regressions in other systems:**
```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/unit/ -x
UV_CACHE_DIR=.uv-cache PYTHONPATH=/home/john/hamlet/src uv run pytest tests/test_townlet/integration/ -x
```

---

### Step 6: Documentation Update

**Update `docs/config-schemas/effects.md`** (if not exists, create):

```markdown
# Effects Configuration Schema

**File:** `effects.yaml` (experiment-level)

**Purpose:** Declarative effect definitions with command pipeline language.

## Schema

```yaml
version: "1.0"

effect_definitions:
  - id: string                    # Unique effect identifier
    description: string           # Human-readable description
    scope: global|agent|item|affordance  # Where effect lives
    duration: int                 # Ticks until auto-despawn
    intensity: float              # Default intensity multiplier
    reapply_policy: stack|renew|merge|replace  # Reapply behavior

    on_spawn: CommandConfig[]     # Commands executed when spawned
    on_tick: CommandConfig[]      # Commands executed each step
    on_despawn: CommandConfig[]   # Commands executed before removal
```

## Example

```yaml
effect_definitions:
  - id: energy_regen
    description: "Regenerates energy over time"
    scope: agent
    duration: 20
    intensity: 1.0
    reapply_policy: renew

    on_spawn: []

    on_tick:
      - modify: target.bar.energy
        value: "clamp(target.bar.energy + (0.05 * intensity), 0.0, 1.0)"

    on_despawn: []
```

## See Also

- Command types: See `docs/plans/vfs_uplift/2025-11-19-effects-system-design.md`
- Expression language: See `docs/config-schemas/expressions.md`
- Reapply policies: See effects design document
```

**Commit:**
```bash
git add docs/config-schemas/effects.md
git commit -m "docs(effects): add effects.yaml configuration schema

- Effect definition structure
- Reapply policy semantics
- Command pipeline examples
- Cross-references to design docs

Part of Task 3.5 (Environment Integration)
Ref: docs/plans/vfs_uplift/2025-11-19-task-3-5-environment-integration.md"
```

---

## Success Criteria

**Code:**
- ✅ VectorizedHamletEnv initializes EffectManager from compiled world
- ✅ env.step() calls effect_manager.tick(self.state)
- ✅ CommandExecutor created with expression evaluator
- ✅ Effects execute commands and modify bars/VFS

**Tests:**
- ✅ 5-10 integration tests passing
- ✅ Environment initializes EffectManager
- ✅ Effects tick each step
- ✅ Auto-despawn after duration
- ✅ Modify commands change bar values
- ✅ on_spawn commands execute immediately
- ✅ Reapply policies work in live environment (RENEW, MERGE)

**Config:**
- ✅ effects_smoke/effects.yaml with 5 test effects
- ✅ Covers all reapply policies (stack, renew, merge, replace)
- ✅ Global and agent scopes

**Documentation:**
- ✅ effects.md schema documentation

**Phase 3 Complete:**
- ✅ 75+ tests passing across all tasks
- ✅ Effects system fully integrated
- ✅ No regressions in existing tests

---

## Notes for Implementer

**Integration Point:**
- EffectManager.tick() called **after** cascades in env.step()
- This ensures bars updated by actions/cascades before effects execute
- Effects can then modify bars based on current state

**State Object:**
- env.state needs to be passed to tick() for ExecutionContext
- ExecutionContext needs: bars, vfs_global, vfs_agent, vfs_item, temporal
- Verify env.state has all required attributes

**Command Executor:**
- Reuse expression_evaluator from VFS integration
- CommandExecutor wraps evaluator for command execution
- Should already exist from Task 3.3

**Testing Strategy:**
- Integration tests use real VectorizedHamletEnv
- Effects smoke config is minimal (5 effects, simple commands)
- Verify modify commands change GPU tensor values
- Test all reapply policies in live environment

**Error Handling:**
- If effects.yaml missing, EffectManager should gracefully handle empty catalog
- Invalid effect_id in spawn_effect() should raise KeyError (fail fast)
- Command execution errors should propagate (don't silently fail)

**Performance:**
- EffectManager.tick() is O(num_active_effects)
- Scoped collections prevent O(num_entities) searches
- For typical use (10-50 active effects), overhead should be <1%

---

*Ready for execution by Claude using superpowers:executing-plans or superpowers:subagent-driven-development*
