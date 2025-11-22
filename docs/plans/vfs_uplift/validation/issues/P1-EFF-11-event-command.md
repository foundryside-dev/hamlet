# P1-EFF-11: Event/Messaging Command Not Implemented

**Priority:** P1 (Important - Can Defer)
**Category:** Effects System
**Estimated Effort:** 1-2 days
**Status:** Open
**Created:** 2025-11-22

---

## Problem Description

The effects system lacks an explicit `emit_event` command for event-driven programming patterns. Currently, events must be simulated via effect cascading (`spawn_effect` chains), which is less intuitive.

**Current Workaround:**
```yaml
# Instead of emitting events directly, chain effects
on_spawn:
  - command: spawn_effect
    effect: "item_pickup_notification"
    target: self
```

**Desired Syntax:**
```yaml
on_spawn:
  - command: emit_event
    event: "item_pickup"
    data:
      item_type: "{{ item.type }}"
      position: "{{ item.position }}"
```

**Impact:**
- Less intuitive for event-driven patterns
- Cannot decouple event emission from effect spawning
- **Not a blocker:** Workaround via `spawn_effect` chains works fine

**Evidence:**
- Agent 3 (Effects) report, section EFF-11
- Design doc mentioned events/messaging but not implemented
- No `emit_event` command type in `CommandType` enum

---

## Why This is P1 (Not P0)

**This is NOT a blocker because:**
- Effect cascading provides equivalent functionality
- All current use cases covered by `spawn_effect` chains
- No runtime errors - system works without explicit events

**This IS important because:**
- Pedagogical value: Event-driven programming is important RL concept
- Clean architecture: Separates event emission from effect execution
- Future extensibility: True event bus enables more patterns

---

## Design Considerations

### Option 1: Simple Event Emission (Minimal)

Add `emit_event` command that just spawns a pre-defined effect:

```python
class CommandType(Enum):
    # ... existing commands ...
    EMIT_EVENT = "emit_event"

# In executor.py
def execute_emit_event(self, cmd: CommandNode):
    """Emit event by spawning corresponding effect."""
    event_name = cmd.params['event']
    effect_name = f"on_{event_name}"  # Convention: event -> on_event effect

    # Just spawn the effect
    self.execute_spawn_effect(CommandNode(
        type=CommandType.SPAWN_EFFECT,
        params={'effect': effect_name, 'target': cmd.params.get('target', 'self')}
    ))
```

**Pros:** Simple, backward compatible
**Cons:** Not a true event system, just sugar for spawn_effect

### Option 2: Event Bus (Full Implementation)

Create proper event bus with pub/sub:

```python
class EventBus:
    def __init__(self):
        self.listeners = {}  # event_name -> List[effect_name]

    def subscribe(self, event_name: str, effect_name: str):
        self.listeners.setdefault(event_name, []).append(effect_name)

    def emit(self, event_name: str, context: ExecutionContext):
        for effect_name in self.listeners.get(event_name, []):
            # Spawn effect for each listener
            ...
```

**Pros:** True decoupling, supports multiple listeners
**Cons:** More complex, requires event registration system

### Option 3: Deferred (Current Approach)

Keep using `spawn_effect` chains until there's a concrete use case that requires events.

**Pros:** No work, existing system sufficient
**Cons:** Missing pedagogical opportunity

---

## Recommended Approach

**Implement Option 1 (Simple Event Emission) as syntactic sugar:**

1. Add `EMIT_EVENT` to `CommandType` enum
2. In executor, map event emission to effect spawning
3. Add convention: `emit_event: "foo"` → `spawn_effect: "on_foo"`
4. Document pattern in effects schema docs

**Defer Option 2** until there's a real need for pub/sub patterns.

---

## How to Fix (Option 1)

### Step 1: Add Command Type (15 minutes)

**File:** `src/townlet/effects/schema.py`

```python
class CommandType(Enum):
    MODIFY = "modify"
    SPAWN_EFFECT = "spawn_effect"
    SPAWN_ITEM = "spawn_item"
    IF = "if"
    FOR_EACH = "for_each"
    EMIT_EVENT = "emit_event"  # ADD THIS
    # ... other types ...
```

### Step 2: Implement Execution (1 hour)

**File:** `src/townlet/effects/executor.py`

```python
def execute_command(self, cmd: CommandNode):
    if cmd.type == CommandType.EMIT_EVENT:
        self.execute_emit_event(cmd)
    # ... existing command handlers ...

def execute_emit_event(self, cmd: CommandNode):
    """Emit event by spawning corresponding 'on_<event>' effect."""
    event_name = cmd.params['event']
    effect_name = f"on_{event_name}"

    # Check if effect exists
    if effect_name not in self.catalog.effects:
        raise RuntimeError(f"No effect handler for event '{event_name}' (expected effect '{effect_name}')")

    # Spawn the effect
    target = cmd.params.get('target', 'self')
    self.spawn_effect(effect_name, target, context=self.context)
```

### Step 3: Add Schema Validation (30 minutes)

**File:** `src/townlet/config/effects_config.py`

```python
class EmitEventCommandConfig(BaseModel):
    command: Literal["emit_event"]
    event: str
    target: Optional[str] = "self"
    data: Optional[Dict[str, Any]] = None  # For future extensibility
```

### Step 4: Write Tests (2 hours)

**File:** `tests/test_townlet/unit/effects/test_emit_event.py` (NEW)

```python
def test_emit_event_spawns_corresponding_effect():
    """Verify emit_event command spawns on_<event> effect."""
    # Setup: Create effect catalog with event handler
    effects = {
        "pickup_item": {
            "commands": {
                "on_spawn": [{"command": "emit_event", "event": "item_acquired"}]
            }
        },
        "on_item_acquired": {
            "commands": {
                "on_spawn": [{"command": "modify", "target": "self.bar.inventory_count", "value": "+1"}]
            }
        }
    }

    catalog = EffectCatalog.from_config(effects)
    executor = CommandExecutor(catalog)

    # Execute: Emit event
    executor.execute(CommandNode(
        type=CommandType.EMIT_EVENT,
        params={'event': 'item_acquired', 'target': 'self'}
    ))

    # Verify: on_item_acquired effect spawned
    assert executor.active_effects.has_effect("on_item_acquired")
```

### Step 5: Document Pattern (1 hour)

**File:** `docs/config-schemas/effects.md`

Add section:

```markdown
### Event Emission

The `emit_event` command provides a convenient way to trigger event handlers:

```yaml
on_pickup:
  - command: emit_event
    event: "item_acquired"
    target: self

# Convention: Creates on_<event> effect
# Must define corresponding handler:
on_item_acquired:
  on_spawn:
    - command: modify
      target: "self.bar.inventory_count"
      value: "+1"
```

**Naming Convention:** Event `foo` requires effect `on_foo` to be defined.

**Use Cases:**
- Item pickup/drop notifications
- Achievement unlocks
- State transitions
```

---

## Acceptance Criteria

- [ ] `EMIT_EVENT` added to `CommandType` enum
- [ ] `execute_emit_event` implemented in executor
- [ ] Schema validation for emit_event command
- [ ] Tests verify event → effect spawning works
- [ ] Documentation shows emit_event pattern
- [ ] Error if corresponding `on_<event>` effect missing

---

## Files to Modify

1. `src/townlet/effects/schema.py` - Add EMIT_EVENT type
2. `src/townlet/effects/executor.py` - Implement execution logic
3. `src/townlet/config/effects_config.py` - Add schema validation
4. `tests/test_townlet/unit/effects/test_emit_event.py` (NEW) - Tests
5. `docs/config-schemas/effects.md` - Document pattern

---

## Related Issues

- Related: P1-EFF-12 (sample command)
- Blocking: None (optional feature)
- Future: Event bus (Option 2) if pub/sub patterns needed

---

## Notes

- **Syntactic sugar:** This is primarily for readability/pedagogy
- **Convention over configuration:** `emit_event: "foo"` requires `on_foo` effect
- **Future-proof:** `data` field reserved for passing event context (not implemented yet)
- **Non-blocking:** Can defer if other P1 issues higher priority
- Estimated actual implementation time: 4-6 hours (much less than 1-2 days if Option 1 chosen)
