# [EFF-17] Cascade Depth Limit Test

**Priority:** P2 (Minor)
**Category:** Effects / Testing
**Status:** PARTIAL
**Effort:** 1 hour

## Description

Effects executor has cascade depth limit implementation (prevents infinite effect chains) but no corresponding test. Implementation exists at `executor.py:177-179` but test coverage is missing. Need test to verify depth limit prevents runaway cascades.

## Current State

**Implementation exists:**
```python
# src/townlet/effects/executor.py:177-179
MAX_CASCADE_DEPTH = 10

def execute_effect_commands(self, commands: List[EffectCommand], context: ExecutionContext, depth: int = 0):
    """Execute effect commands with cascade depth limit."""
    if depth > MAX_CASCADE_DEPTH:
        raise RuntimeError(f"Effect cascade exceeded maximum depth {MAX_CASCADE_DEPTH}")

    for command in commands:
        # Execute command...
        if command.type == "spawn_effect":
            # Recursive call with incremented depth
            self.execute_effect_commands(spawned_effect.commands, context, depth + 1)
```

**Test missing:**
- No test validates depth limit is enforced
- No test for infinite cascade prevention
- No test for error message on exceeded depth

**Why it matters:**
- Prevents infinite loops in effect chains (effect A spawns effect B spawns effect A...)
- Prevents accidental runaway cascades (effect explosion)
- Important safety mechanism for effect system

## Required Implementation

### Test Implementation (1 hour)

**File:** `tests/test_townlet/unit/effects/test_cascade_depth_limit.py` (new)

**Test cases:**
```python
import pytest
from townlet.effects.executor import EffectExecutor, MAX_CASCADE_DEPTH
from townlet.effects.schema import EffectCommand
from townlet.effects.context import ExecutionContext


def test_cascade_depth_limit_enforced():
    """Test cascade depth limit prevents infinite effect chains."""

    # Create self-referencing effect (spawns itself)
    recursive_effect = create_effect(
        name="recursive_explosion",
        commands=[
            EffectCommand(
                type="spawn_effect",
                effect_name="recursive_explosion",  # Spawns itself
                target="self"
            )
        ]
    )

    catalog = EffectCatalog(effects={"recursive_explosion": recursive_effect})
    executor = EffectExecutor(catalog)
    context = create_execution_context()

    # Executing recursive effect should raise RuntimeError after MAX_CASCADE_DEPTH
    with pytest.raises(RuntimeError) as exc_info:
        executor.execute_effect_commands(recursive_effect.commands, context, depth=0)

    assert f"exceeded maximum depth {MAX_CASCADE_DEPTH}" in str(exc_info.value)


def test_deep_cascade_within_limit():
    """Test cascades within depth limit execute successfully."""

    # Create chain: A → B → C → ... (depth < MAX_CASCADE_DEPTH)
    effects = {}
    for i in range(MAX_CASCADE_DEPTH - 1):
        next_effect = f"effect_{i + 1}" if i < MAX_CASCADE_DEPTH - 2 else None
        effects[f"effect_{i}"] = create_effect(
            name=f"effect_{i}",
            commands=[
                EffectCommand(type="spawn_effect", effect_name=next_effect, target="self")
            ] if next_effect else []
        )

    catalog = EffectCatalog(effects=effects)
    executor = EffectExecutor(catalog)
    context = create_execution_context()

    # Chain within limit should execute successfully
    executor.execute_effect_commands(effects["effect_0"].commands, context, depth=0)
    # No exception raised


def test_cascade_exactly_at_limit():
    """Test cascade exactly at depth limit is allowed."""

    # Create chain exactly MAX_CASCADE_DEPTH deep
    effects = {}
    for i in range(MAX_CASCADE_DEPTH):
        next_effect = f"effect_{i + 1}" if i < MAX_CASCADE_DEPTH - 1 else None
        effects[f"effect_{i}"] = create_effect(
            name=f"effect_{i}",
            commands=[
                EffectCommand(type="spawn_effect", effect_name=next_effect, target="self")
            ] if next_effect else []
        )

    catalog = EffectCatalog(effects=effects)
    executor = EffectExecutor(catalog)
    context = create_execution_context()

    # Chain exactly at limit should succeed
    executor.execute_effect_commands(effects["effect_0"].commands, context, depth=0)


def test_cascade_exceeding_limit_by_one():
    """Test cascade exceeding limit by one level raises error."""

    # Create chain MAX_CASCADE_DEPTH + 1 deep
    effects = {}
    for i in range(MAX_CASCADE_DEPTH + 1):
        next_effect = f"effect_{i + 1}" if i < MAX_CASCADE_DEPTH else None
        effects[f"effect_{i}"] = create_effect(
            name=f"effect_{i}",
            commands=[
                EffectCommand(type="spawn_effect", effect_name=next_effect, target="self")
            ] if next_effect else []
        )

    catalog = EffectCatalog(effects=effects)
    executor = EffectExecutor(catalog)
    context = create_execution_context()

    # Chain exceeding limit by 1 should raise RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        executor.execute_effect_commands(effects["effect_0"].commands, context, depth=0)

    assert f"exceeded maximum depth {MAX_CASCADE_DEPTH}" in str(exc_info.value)


def test_circular_cascade_prevented():
    """Test circular effect cascade (A → B → A) is prevented."""

    # Create circular cascade: effect_a → effect_b → effect_a
    effect_a = create_effect(
        name="effect_a",
        commands=[
            EffectCommand(type="spawn_effect", effect_name="effect_b", target="self")
        ]
    )
    effect_b = create_effect(
        name="effect_b",
        commands=[
            EffectCommand(type="spawn_effect", effect_name="effect_a", target="self")
        ]
    )

    catalog = EffectCatalog(effects={"effect_a": effect_a, "effect_b": effect_b})
    executor = EffectExecutor(catalog)
    context = create_execution_context()

    # Circular cascade should be stopped by depth limit
    with pytest.raises(RuntimeError) as exc_info:
        executor.execute_effect_commands(effect_a.commands, context, depth=0)

    assert f"exceeded maximum depth {MAX_CASCADE_DEPTH}" in str(exc_info.value)


def test_depth_tracking_across_commands():
    """Test depth is tracked correctly across multiple commands."""

    # Effect with multiple spawn commands at same level
    effect = create_effect(
        name="multi_spawn",
        commands=[
            EffectCommand(type="spawn_effect", effect_name="leaf_effect", target="self"),
            EffectCommand(type="spawn_effect", effect_name="leaf_effect", target="self"),
            EffectCommand(type="spawn_effect", effect_name="leaf_effect", target="self")
        ]
    )
    leaf_effect = create_effect(name="leaf_effect", commands=[])

    catalog = EffectCatalog(effects={"multi_spawn": effect, "leaf_effect": leaf_effect})
    executor = EffectExecutor(catalog)
    context = create_execution_context()

    # Multiple spawns at same depth should all execute
    executor.execute_effect_commands(effect.commands, context, depth=0)
    # No exception raised


def test_depth_limit_configurable():
    """Test cascade depth limit is configurable (future enhancement)."""
    # Currently hardcoded as MAX_CASCADE_DEPTH = 10
    # Future: Make configurable via executor config
    assert MAX_CASCADE_DEPTH == 10  # Document current value


# Helper functions
def create_effect(name: str, commands: List[EffectCommand]):
    """Create test effect with given commands."""
    return CompiledEffect(
        name=name,
        reapply_policy="stack",
        duration=100,
        commands=commands,
        observable=True
    )

def create_execution_context():
    """Create minimal execution context for testing."""
    return ExecutionContext(
        agent_idx=0,
        bars=create_test_bars(),
        vfs_registry=create_test_vfs_registry(),
        temporal_state=create_test_temporal_state(),
        managers=create_test_managers()
    )
```

## Acceptance Criteria

- [ ] Test file created: `tests/test_townlet/unit/effects/test_cascade_depth_limit.py`
- [ ] Test validates depth limit prevents infinite cascades
- [ ] Test validates chains within limit execute successfully
- [ ] Test validates chains exactly at limit execute successfully
- [ ] Test validates chains exceeding limit by one raise RuntimeError
- [ ] Test validates circular cascades are prevented
- [ ] Test validates error message mentions depth limit
- [ ] Test documents current MAX_CASCADE_DEPTH value
- [ ] All tests pass

## Evidence

**Source Report:** gap-report-final.md (lines 71-94), gap-report-effects.md
**Implementation:** `src/townlet/effects/executor.py:177-179` (exists)
**Test coverage:** Missing test for depth limit

## Implementation Notes

**Why P2 (not P1/P0):** Implementation exists and works correctly. This is about test coverage gap, not a functional bug. Test is important for safety validation but not urgent.

**Current Implementation:**
```python
MAX_CASCADE_DEPTH = 10

if depth > MAX_CASCADE_DEPTH:
    raise RuntimeError(f"Effect cascade exceeded maximum depth {MAX_CASCADE_DEPTH}")
```

**What the test validates:**
1. **Safety:** Infinite loops cannot happen
2. **Limit enforcement:** Depth limit is actually checked
3. **Error handling:** Clear error message on exceeded depth
4. **Edge cases:** Exactly at limit, one over limit, circular cascades

**Why depth limit is important:**
- **Infinite loops:** Effect A spawns effect B spawns effect A → infinite recursion
- **Effect explosion:** Effect spawns 10 effects, each spawns 10 more → exponential growth
- **Accidental chains:** Long cascade due to config error (forgot to terminate chain)
- **Intentional abuse:** Malicious config could crash system with deep cascades

**Typical cascade depths:**
- Simple effects: 0-2 levels (direct effect, maybe one spawn)
- Complex effects: 3-5 levels (chained reactions)
- Pathological cases: >10 levels (usually errors or infinite loops)

**MAX_CASCADE_DEPTH = 10 rationale:**
- Deep enough for legitimate effect chains
- Shallow enough to prevent exponential explosion
- Tunable if needed (could make configurable in future)

**Future Enhancements:**
1. Make MAX_CASCADE_DEPTH configurable per-universe
2. Add cascade depth metrics (log max depth reached)
3. Warn on deep cascades (depth > 7) even if under limit
4. Track cascade graph for visualization (debugging tool)

## References

- Implementation: `src/townlet/effects/executor.py:177-179`
- Test file: `tests/test_townlet/unit/effects/test_cascade_depth_limit.py` (to be created)
- Related: Effect system safety mechanisms, cascade execution logic
