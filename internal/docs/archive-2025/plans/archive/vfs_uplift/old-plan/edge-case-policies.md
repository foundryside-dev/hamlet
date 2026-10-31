# Items & VFS Profiles - Edge Case Policies

**Purpose:** Authoritative reference for edge case behavior across all implementation phases.

**Status:** Final (approved with Phase 0 design decisions)

**Audience:** Engineers implementing Phases 1-4

---

## Policy 1: Inventory Overflow

**Scenario:** Agent at `max_items_per_agent` capacity attempts to pickup additional item.

### Phase 1 Policy: **DENY_PICKUP**

**Behavior:**
1. Agent executes GET action (action is NOT masked)
2. Pickup logic checks: `inventory_count == max_items_per_agent`
3. If at capacity:
   - Pickup **DENIED**
   - Item remains in world at current position
   - Agent's inventory unchanged
   - Agent receives **no item**
   - No error logged (normal behavior)
4. Optional: Apply negative shaping reward (-0.1 penalty)

**Rationale:**
- Phase 1 prioritizes simplicity and determinism
- No silent overflows or undefined behavior
- Agent learns capacity constraint through reward signal

### Phase 3+ Alternative Policies (Future)

**Config field:**
```yaml
inventory:
  max_items_per_agent: 3
  overflow_policy: "deny"  # deny | drop_oldest | priority_replace
```

**drop_oldest:**
- Drop first item in inventory (slot 0)
- Shift remaining items down (slot 1 → slot 0, slot 2 → slot 1)
- Pickup new item into last slot

**priority_replace:**
- Items have priority metadata
- Drop lowest-priority item
- Pickup new item

**Implementation:** Phase 1 hardcodes `deny`, Phase 3 makes configurable.

---

## Policy 2: Item-Scoped Custom Commands

**Scenario:** Item defines custom interaction commands beyond pickup/use/drop.

**Example:**
```yaml
# FUTURE (Phase 4+): Item-scoped commands
item_types:
  - id: umbrella
    interactions:
      local_commands:
        - name: OPEN_UMBRELLA
          description: "Open umbrella when next to it"
          effects: {...}
      inventory_commands:
        - name: CLOSE_UMBRELLA
          description: "Close umbrella while holding it"
          effects: {...}
```

### Phase 1-3 Policy: **NO_ITEM_COMMANDS**

**Behavior:**
- Item interactions limited to: `pickup`, `use`, `drop`
- Custom command fields **REJECTED** at load time (ValidationError)
- Action vocabulary remains **fixed** (7 item actions: GET, DROP_SLOT_0-2, USE_SLOT_0-2)

**Rationale:**
- Prevents action_dim explosion (checkpoint compatibility critical)
- Preserves global action vocabulary stability
- Custom commands add 2N actions per item type (N local + N inventory)

### Phase 4+ Alternative Policy: **ITEM_COMMANDS_ENABLED**

**Behavior:**
- Parse `local_commands` and `inventory_commands` from items.yaml
- Add to action vocabulary (experiment-level, NOT level-level)
- Action masking controls availability:
  - `local_commands`: Masked if item not within interaction range
  - `inventory_commands`: Masked if item not in agent inventory

**Implementation:** Phase 4 feature, requires action_config redesign.

---

## Policy 3: INTERACT Range for Continuous Substrates

**Scenario:** Agent executes INTERACT action with affordance in continuous substrate (Continuous1D/2D/3D).

### Policy: **EXPLICIT_INTERACTION_RADIUS**

**Compiler Validation:**
```python
if substrate.type in ("continuous", "continuous2d", "continuous3d", "continuousnd"):
    if num_affordances > 0 and "interaction_radius" not in substrate.config:
        raise ValidationError(
            f"Continuous substrate '{substrate.type}' with affordances requires "
            f"explicit 'interaction_radius' in substrate.yaml. "
            f"No implicit distance is used for interaction."
        )
```

**Runtime Behavior:**
```python
# Agent at position (x, y), affordance at (ax, ay)
distance = torch.norm(agent_pos - affordance_pos)

if distance <= substrate.interaction_radius:
    # INTERACT succeeds
    apply_affordance_effect(agent)
else:
    # INTERACT fails (no effect)
    pass
```

**Rationale:**
- Eliminates "magic numbers" in code
- Different substrates may need different ranges (e.g., 6DOF space sim vs 2D grid)
- Makes interaction mechanics config-driven and reproducible

**Error Message:**
```
ValidationError: Continuous substrate 'continuous2d' with 5 affordances requires explicit 'interaction_radius' in substrate.yaml.

Add to substrate.yaml:
  interaction_radius: 1.5  # Units match position coordinates
```

**Grid Substrates:** No `interaction_radius` needed (interaction is tile-based, adjacency = distance 1).

**Aspatial Substrates:** No `interaction_radius` needed (no position concept).

---

## Policy 4: VFS Circular Dependencies

**Scenario:** VFS profile A depends on profile B, B depends on A (circular dependency graph).

### Policy: **REJECT_AT_COMPILE_TIME**

**Phase 1 Behavior:**
- Phase 1 has no dependencies (static variables only)
- Circular dependency check **deferred to Phase 2**

**Phase 2+ Behavior:**
```python
# Compiler validation (Phase 2)
def validate_vfs_dependency_graph(vfs_profiles: VFSProfilesConfig) -> None:
    """Ensure VFS dependencies form a DAG (Directed Acyclic Graph)."""
    import networkx as nx

    # Build dependency graph
    G = nx.DiGraph()
    for profile in all_profiles:
        G.add_node(profile.id)
        for dep in profile.deps.get("vfs", []):
            G.add_edge(profile.id, dep)  # profile depends on dep

    # Check for cycles
    try:
        cycles = list(nx.simple_cycles(G))
        if cycles:
            cycle_str = " → ".join(cycles[0]) + f" → {cycles[0][0]}"
            raise ValidationError(
                f"Circular VFS dependency detected: {cycle_str}. "
                f"VFS profiles must form a DAG (no cycles). "
                f"Check 'deps' fields in vfs_profiles.yaml."
            )
    except nx.NetworkXNoCycle:
        pass  # Good - no cycles

    # Return topological order for evaluation
    return list(nx.topological_sort(G))
```

**Error Message Example:**
```
ValidationError: Circular VFS dependency detected: is_heavily_loaded → inventory_weight → is_heavily_loaded.

VFS profiles must form a DAG (no cycles). Check 'deps' fields in vfs_profiles.yaml.

Problematic profile:
  - id: is_heavily_loaded
    deps:
      vfs: [inventory_weight]  # inventory_weight depends on is_heavily_loaded

Fix: Remove circular dependency or use initial_value as fallback.
```

**Rationale:**
- VFS evaluation requires deterministic ordering
- Cycles create infinite loops or non-deterministic results
- DAG validation is standard for expression evaluators

---

## Policy 5: Empty Slot Masking Behavior

**Scenario:** Agent has 3 item slots but only 1 item (slots 0 = item, slots 1-2 = empty).

### Policy: **MASK_WITH_ZERO**

**Observation Encoding:**
```python
# Item VFS observations: [batch, num_item_profiles × max_items_per_agent]
# Example: 2 profiles × 3 slots = 6 dims

agent_inventory = [item_0, None, None]  # 1 item in slot 0

# Observation vector for this agent:
obs = [
    # Slot 0 (has item)
    item_0.vfs["durability"],           # 1.0
    item_0.vfs["uses_remaining"],       # 3.0

    # Slot 1 (empty)
    0.0,  # Masked durability
    0.0,  # Masked uses_remaining

    # Slot 2 (empty)
    0.0,  # Masked durability
    0.0,  # Masked uses_remaining
]
```

**Inventory Mask (for action masking):**
```python
inventory_mask = torch.tensor([True, False, False])  # Slot 0 full, 1-2 empty

# Action masking uses this:
action_mask[DROP_SLOT_0] = inventory_mask[0]  # True (can drop)
action_mask[DROP_SLOT_1] = inventory_mask[1]  # False (cannot drop)
action_mask[DROP_SLOT_2] = inventory_mask[2]  # False (cannot drop)
```

**Rationale:**
- Obs_dim remains constant regardless of how many items held
- 0.0 is semantically meaningful (no item = no durability/uses)
- Action masking prevents invalid operations on empty slots
- Checkpoint compatibility preserved (fixed layout)

**Alternative Considered (REJECTED):** Variable-length observations (obs_dim changes with item count)
- **Rejected because:** Breaks checkpoint transfer, complicates network architecture

---

## Policy 6: Spawn Rule Conflict Resolution

**Scenario:** Multiple spawn rules could spawn items simultaneously, but world has limited space or spawn budget.

### Policy: **PRIORITY_ORDERING**

**Behavior:**
```python
# Sort spawn rules by priority (descending)
sorted_rules = sorted(spawn_rules, key=lambda r: r.priority, reverse=True)

# Process in priority order
for rule in sorted_rules:
    if should_spawn(rule, current_step) and can_spawn(rule):
        spawn_item(rule.type_id, ...)
        # Higher priority items spawn first
        # If spawn budget exhausted, lower priority items don't spawn
```

**Example:**
```yaml
spawn_rules:
  - type_id: medkit
    priority: 100  # High priority (always spawn if possible)
    limits:
      max_simultaneous: 2

  - type_id: umbrella
    priority: 50   # Medium priority
    limits:
      max_simultaneous: 5

  - type_id: toy
    priority: 10   # Low priority (spawn only if budget available)
    limits:
      max_simultaneous: 3
```

**Conflict Example:**
- Step 10: Both medkit and umbrella scheduled to spawn
- Spawn budget: Only 1 item can spawn this step
- **Result:** Medkit spawns (priority 100), umbrella waits for next step

**Rationale:**
- Deterministic spawn order (reproducible across runs with same seed)
- Allows config to express "critical items" (high priority) vs "nice-to-have" (low priority)
- Prevents random spawn order causing non-deterministic training

**Default Priority:** If not specified, priority = 0 (lowest).

---

## Policy 7: Item Despawn Edge Cases

### Case 7A: Item Despawns While Held by Agent

**Scenario:** Agent holds item, item reaches `expire_step`.

**Policy:** **FORCE_DESPAWN_REMOVE_FROM_INVENTORY**

**Behavior:**
```python
def step(current_step):
    # Check all items for expiration
    for item in active_items.values():
        if current_step >= item.expire_step:
            # If held by agent, remove from inventory
            if item.holder_agent_id is not None:
                agent_idx = item.holder_agent_id
                slot_idx = find_slot(agent_idx, item.id)

                # Clear inventory slot
                inventory[agent_idx, slot_idx] = -1
                inventory_mask[agent_idx, slot_idx] = False

            # Despawn item
            despawn_item(item.id)
```

**Rationale:**
- Items have finite lifetime regardless of state (held vs in-world)
- Prevents items from becoming "permanent" by holding
- Teaches agents items are perishable

**Optional:** Apply penalty when held item despawns (agent "wasted" the item by not using it).

### Case 7B: Item at `duration_steps = -1` (Infinite Lifetime)

**Policy:** **NEVER_DESPAWN**

**Behavior:**
```python
if item.expire_step == -1:
    # Item never despawns (infinite lifetime)
    continue
```

**Use Case:** Permanent world objects (e.g., statues, landmarks) modeled as items.

---

## Policy 8: Checkpoint Compatibility

### Case 8A: Loading Checkpoint with Missing Item Types

**Scenario:** Checkpoint saved with item type "umbrella", but current config has no "umbrella" in catalog.

**Policy:** **FAIL_LOUDLY**

**Behavior:**
```python
def load_checkpoint_state(state_dict):
    for item_data in state_dict["items"]["active_items"]:
        type_id = item_data["type_id"]

        if type_id not in item_catalog:
            raise ValueError(
                f"Checkpoint contains item type '{type_id}' not found in current catalog. "
                f"Available types: {list(item_catalog.keys())}. "
                f"Cannot load checkpoint with incompatible item catalog."
            )
```

**Rationale:**
- Silent failures create non-reproducible bugs
- Checkpoints must match config exactly (no config drift tolerance)
- Forces user to use matching configs for checkpoint resume

**Error Message:**
```
ValueError: Checkpoint contains item type 'umbrella' not found in current catalog.
Available types: ['medkit', 'food'].

This checkpoint was saved with a different items.yaml catalog.
To load this checkpoint, restore the original items.yaml or create a new experiment.
```

### Case 8B: Loading Checkpoint with Different `max_items_per_agent`

**Policy:** **FAIL_LOUDLY**

**Behavior:**
```python
checkpoint_max_items = state_dict["inventory"].shape[1]
current_max_items = config.inventory.max_items_per_agent

if checkpoint_max_items != current_max_items:
    raise ValueError(
        f"Checkpoint inventory has {checkpoint_max_items} slots per agent, "
        f"but current config specifies {current_max_items}. "
        f"max_items_per_agent must match exactly for checkpoint loading."
    )
```

**Rationale:**
- `max_items_per_agent` affects obs_dim (cannot change after training starts)
- Checkpoint contains inventory state with fixed slot count
- Attempting to load with different slot count corrupts inventory state

---

## Policy 9: VFS Profile References from Items

### Case 9A: Item References Nonexistent VFS Profile

**Scenario:** Item type specifies `vfs_profiles: ["item_durability"]`, but `vfs_profiles.yaml` has no profile with id "item_durability".

**Policy:** **REJECT_AT_COMPILE_TIME**

**Behavior:**
```python
# Compiler cross-validation (Phase 1)
def validate_item_vfs_references(catalog, vfs_profiles):
    all_profile_ids = {p.id for p in vfs_profiles.all_profiles()}

    for item in catalog.item_types:
        for profile_id in item.vfs_profiles:
            if profile_id not in all_profile_ids:
                raise ValueError(
                    f"Item '{item.id}' references VFS profile '{profile_id}' "
                    f"not found in vfs_profiles.yaml. "
                    f"Available profiles: {sorted(all_profile_ids)}"
                )
```

**Error Message:**
```
ValueError: Item 'umbrella' references VFS profile 'item_wetness_resistance' not found in vfs_profiles.yaml.

Available profiles: ['item_durability', 'item_uses_remaining']

Add the missing profile to vfs_profiles.yaml:
  item_profiles:
    - id: item_wetness_resistance
      scope: item
      type: scalar
      initial_value: 0.5
```

### Case 9B: Item References Wrong Scope VFS Profile

**Scenario:** Item references agent-scoped profile instead of item-scoped.

**Policy:** **WARN_AT_COMPILE_TIME** (Phase 1), **REJECT_AT_COMPILE_TIME** (Phase 2+)

**Behavior:**
```python
# Phase 1: Warning only (profiles are metadata-only, no runtime impact)
for item in catalog.item_types:
    for profile_id in item.vfs_profiles:
        profile = vfs_profiles.get_profile(profile_id)
        if profile.scope != "item":
            warnings.warn(
                f"Item '{item.id}' references {profile.scope}-scoped profile '{profile_id}'. "
                f"Items should only reference item-scoped profiles. "
                f"This will become an error in Phase 2."
            )

# Phase 2+: Hard error
# Rationale: Runtime VFS evaluation requires correct scoping
```

---

## Policy 10: Action Masking Consistency

**Scenario:** Agent has item in slot but item has no `use` effect defined.

**Policy:** **MASK_USE_ACTION**

**Behavior:**
```python
# Action masking for USE_SLOT_N
for slot_idx in range(max_items_per_agent):
    if not inventory_mask[agent_idx, slot_idx]:
        # Slot empty: mask USE
        action_mask[USE_SLOT_0 + slot_idx] = False
    else:
        # Slot has item: check if item has use effect
        item_id = inventory[agent_idx, slot_idx]
        item = item_manager.get_item(item_id)
        item_type = catalog.get_type(item.type_id)

        if item_type.interactions.use is None:
            # Item has no use effect: mask USE
            action_mask[USE_SLOT_0 + slot_idx] = False
        else:
            # Item has use effect: allow USE
            action_mask[USE_SLOT_0 + slot_idx] = True
```

**Example:**
```yaml
item_types:
  - id: statue
    name: "Decorative Statue"
    interactions:
      pickup: {...}   # Can pickup
      # No use effect defined
      drop: {...}     # Can drop
```

**Result:**
- Agent can pickup statue
- Agent can drop statue
- Agent **cannot** use statue (USE_SLOT_N masked when holding statue)

**Rationale:**
- Prevents no-op actions (using an item with no effect)
- Improves training efficiency (agent doesn't waste actions on useless commands)
- Makes item capabilities explicit in config

---

## Policy Summary Table

| Policy | Behavior | Phase | Enforcement |
|--------|----------|-------|-------------|
| Inventory Overflow | DENY_PICKUP | 1-3 | Runtime |
| Item Commands | NO_ITEM_COMMANDS | 1-3 | Compile-time |
| INTERACT Range (Continuous) | EXPLICIT_INTERACTION_RADIUS | 1+ | Compile-time |
| VFS Circular Dependencies | REJECT_AT_COMPILE_TIME | 2+ | Compile-time |
| Empty Slot Masking | MASK_WITH_ZERO | 2+ | Runtime |
| Spawn Conflicts | PRIORITY_ORDERING | 3+ | Runtime |
| Item Despawn While Held | FORCE_DESPAWN_REMOVE | 3+ | Runtime |
| Checkpoint Item Type Mismatch | FAIL_LOUDLY | 3+ | Load-time |
| VFS Profile Nonexistent Ref | REJECT_AT_COMPILE_TIME | 1+ | Compile-time |
| Use Action on No-Effect Item | MASK_USE_ACTION | 3+ | Runtime |

---

## Implementation Checklist

### Phase 1 (DTOs + Compiler)
- [ ] Policy 3: Validate `interaction_radius` for continuous + affordances
- [ ] Policy 9A: Validate item VFS references exist
- [ ] Policy 9B: Warn if item references wrong-scope profile

### Phase 2 (VFS Engine + DynObs)
- [ ] Policy 4: Validate VFS dependency graph is DAG
- [ ] Policy 5: Implement empty slot masking (0.0 values)
- [ ] Policy 9B: Upgrade wrong-scope warning to error

### Phase 3 (Items Runtime)
- [ ] Policy 1: Implement DENY_PICKUP overflow policy
- [ ] Policy 6: Implement priority-based spawn ordering
- [ ] Policy 7A: Handle item despawn while held
- [ ] Policy 7B: Handle infinite lifetime (`duration_steps = -1`)
- [ ] Policy 8A: Validate checkpoint item type matches catalog
- [ ] Policy 8B: Validate checkpoint `max_items_per_agent` matches config
- [ ] Policy 10: Implement action masking for items with no use effect

### Phase 4 (Advanced Scheduling)
- [ ] Policy 2: (Optional) Implement item-scoped custom commands if needed

---

## Rationale: Why These Policies?

### General Principles

1. **Fail Loudly, Never Silently**
   - All errors detected at compile-time or load-time
   - Runtime failures raise exceptions (never corrupt state)
   - Example: Missing VFS profile → ValidationError, not silent skip

2. **No Implicit Defaults for Behavioral Parameters**
   - Every policy has explicit config where applicable
   - Example: `interaction_radius` REQUIRED, not defaulted to 1.0

3. **Checkpoint Compatibility is Sacred**
   - obs_dim must remain stable (breaking change = new experiment)
   - Config changes that break checkpoints: FAIL_LOUDLY
   - Example: Changing `max_items_per_agent` → cannot load old checkpoint

4. **Deterministic Behavior Always**
   - Priority ordering, not random selection
   - Topological sort for VFS, not arbitrary evaluation order
   - Fixed slot layout, not variable-length

5. **Pre-Release Freedom (No Backwards Compat)**
   - Policies can change between phases (no users to break)
   - Phase 1-3: Evolve policies as needed
   - Post-release: Policies become contracts

---

**Status:** This document is authoritative for all implementation phases. Any deviation from these policies requires updating this document first.

**Last Updated:** 2025-11-19 (Phase 0 design resolution)
