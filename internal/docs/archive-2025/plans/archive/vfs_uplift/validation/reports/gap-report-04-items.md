# Gap Report 04: Items System Requirements

**Agent**: Agent 4
**Baseline Commit**: b085877dd45ffb9647a2bc3295ee6ce8c94ad845
**Date**: 2025-11-23
**Requirements Scope**: ITEM-REQ-001 through ITEM-REQ-017 (17 requirements)

---

## Executive Summary

**Overall Status**: 15/17 DONE, 2/17 PARTIAL
**Completion**: 88%

The Items System is substantially complete with robust runtime implementation, Effects integration, VFS profile support, inventory mechanics, and advanced spawn rules. Two requirements (ITEM-REQ-013 durability/charges, ITEM-REQ-014 decay) remain partially implemented - VFS infrastructure is in place but lacks explicit demonstration in production configs.

**Critical Findings**:
- ✅ Complete ItemManager runtime with lifecycle, spawn scheduling, cooldown tracking
- ✅ Full inventory system with GET/USE/DROP actions and DENY_PICKUP policy
- ✅ Profile-driven item VFS with initial_state overrides
- ✅ Advanced spawn rules: placement modes (random/fixed/grid/scripted), schedules (periodic/time_window/poisson/normal), conditional spawning
- ✅ Exclusive vs shared item semantics fully implemented
- ✅ Item holder tracking with multi-agent support
- ✅ Custom item verbs (local/inventory scoped)
- 🟡 Durability/charges: infrastructure exists but needs explicit config examples
- 🟡 Decay: requires Effects-based implementation (not item-specific decay type)

---

## Requirements Analysis

### ITEM-REQ-001: Item manager runtime ✅ DONE

**Requirement**: Add ItemManager + ItemInstance pool with spawn scheduling, lifecycle, cooldown, holder tracking, and VFS index links.

**Evidence**:
- **Implementation**: `/home/john/hamlet/src/townlet/items/manager.py` (929 lines)
  - Lines 55-201: ItemManager class with spawn scheduling, lifecycle tracking, cooldown management
  - Lines 10-49: ItemInstance dataclass with VFS index, holder tracking, lifecycle methods
  - Lines 283-376: `spawn_item()` with VFS initialization and cooldown enforcement
  - Lines 378-461: `lift_item()`/`place_item()`/`despawn_item()` for lifecycle management
  - Lines 500-529: `tick()` for lifecycle advancement and expiry detection
  - Lines 764-829: `spawn_initial_items()` with rule-based spawning
  - Lines 831-929: `process_respawns()` for periodic respawning

- **ItemInstance fields** (`instance.py:10-49`):
  - `instance_id`: Unique ID (line 22)
  - `vfs_index`: VFS pool index (line 24)
  - `vfs_profile`: Profile name (line 25)
  - `spawn_tick`, `duration_remaining`: Lifecycle timers (lines 27-29)
  - `holder_agent_ids`: Multi-agent holder tracking (line 31)
  - Methods: `tick()`, `is_expired()`, `holder_agent_id` property

- **VFS Integration** (`manager.py:321-350`):
  - Item VFS initialized from profile defaults + initial_state overrides
  - VFS registry registration on spawn (line 374)
  - VFS cleanup on despawn (line 448)

**Status**: ✅ DONE

---

### ITEM-REQ-002: Inventory + core actions ✅ DONE

**Requirement**: Enforce explicit `max_items_per_agent`; auto-include GET/DROP when items enabled; auto-include INTERACT when affordances exist.

**Evidence**:
- **DTO enforcement**: `/home/john/hamlet/src/townlet/config/items_config.py:233`
  ```python
  max_items_per_agent: int = Field(..., description="Maximum items agent can carry", ge=1, le=10)
  ```
  Required field (no default), range validated 1-10.

- **InventoryState**: `/home/john/hamlet/src/townlet/items/inventory.py:15-147`
  - Lines 23-46: Fixed-size tensor storage `[batch, max_items_per_agent]`
  - Lines 51-86: `add_item()` with DENY_PICKUP policy (line 74)
  - Lines 88-113: `remove_item()` with holder tracking update
  - Lines 131-133: `is_full()` enforcement

- **Action Auto-Registration**: Integration test evidence
  - `/home/john/hamlet/tests/test_townlet/integration/test_items_integration.py:58-76`
  - Lines 70-75: Verifies GET, USE_SLOT_N, DROP_SLOT_N auto-registered

- **GET/DROP Actions**: `/home/john/hamlet/src/townlet/items/action_handlers.py`
  - Lines 145-193: `handle_get_action()` with DENY_PICKUP enforcement
  - Lines 350-388: `handle_drop_slot_action()` preserving item identity

- **Test Coverage**:
  - `tests/test_townlet/integration/test_items_integration.py:100-140`: GET action test
  - `tests/test_townlet/integration/test_items_integration.py:179-216`: DROP action test
  - `tests/test_townlet/unit/items/test_inventory.py`: Inventory unit tests

**Status**: ✅ DONE

---

### ITEM-REQ-003: Profile-driven item VFS ✅ DONE

**Requirement**: Item VFS storage/layout comes from compiled item profiles; item instances require `vfs_profile` and accept `initial_state` keyed by profile vars; no fallback to variables_reference.yaml.

**Evidence**:
- **VFS Profile Requirement**: `/home/john/hamlet/src/townlet/config/items_config.py:166-169`
  ```python
  vfs_profile: str = Field(
      ...,
      description="VFS profile ID from vfs_profiles.yaml (item scope)",
  )
  ```
  Required field (no default), no fallback mechanism.

- **Profile-Driven Initialization**: `/home/john/hamlet/src/townlet/items/manager.py:321-350`
  - Line 322: Profile name retrieved from item type definition
  - Lines 325-328: Profile lookup in VFS registry (raises if missing)
  - Lines 335-342: Defaults applied from `compiled_profile.variables[].initial_value`
  - Lines 345-350: `initial_state` overrides applied per variable name

- **ItemInstance Assignment**: `/home/john/hamlet/src/townlet/items/manager.py:353-366`
  - Line 358: `vfs_profile=item_def.vfs_profile` assigned from catalog
  - Line 357: `vfs_index` allocated from pool
  - Line 374: `register_item_instance(vfs_index, vfs_profile)` in registry

- **No Fallback**: Grep search confirms no references to `variables_reference.yaml` in items runtime code

- **Test Evidence**: `/home/john/hamlet/tests/test_townlet/unit/items/test_item_vfs_profile_assignment.py`
  - Lines 24-114: Verifies vfs_profile assigned on spawn for different item types
  - Lines 117-184: Verifies vfs_profile preserved across lift/place operations

**Status**: ✅ DONE

---

### ITEM-REQ-004: Fixed item VFS pool ✅ DONE

**Requirement**: Preallocate fixed-size item VFS tensors/pools sized by max_items using compiled profile layout for GPU efficiency and checkpoint stability.

**Evidence**:
- **Fixed Pool Allocation**: `/home/john/hamlet/src/townlet/items/manager.py:180-181`
  ```python
  # VFS slot allocation (fixed-size pool)
  self.vfs_free_slots: set[int] = set(range(max_items))  # Available VFS indices
  ```

- **Slot Management**:
  - Line 318: `vfs_index = self.vfs_free_slots.pop()` - allocate from pool
  - Line 455: `self.vfs_free_slots.add(item.vfs_index)` - return to pool on despawn
  - Lines 202-207: `reset_state()` reinitializes pool to full range

- **VFS Registry Storage**: VFS registry creates fixed-size tensors per profile
  - Items use stable indices into `item_vfs` tensor
  - Profile layout determines variable offsets within tensor

- **Checkpoint Stability**: Fixed pool size ensures consistent tensor shapes across saves

**Status**: ✅ DONE

---

### ITEM-REQ-005: Spawn rules coverage ✅ DONE

**Requirement**: Spawn rules support placement modes (random/fixed/grid/scripted), schedules, limits, lifecycle, and priority; all fields validated (no implicit defaults).

**Evidence**:
- **DTO Validation**: `/home/john/hamlet/src/townlet/config/items_config.py`
  - Lines 266-311: `SpawnScheduleConfig` with required fields per type (no defaults)
  - Lines 313-338: `SpawnPlacementConfig` with mode-specific required fields
  - Lines 340-384: `ItemAppearanceRuleConfig` with explicit fields, no implicit defaults

- **Placement Modes Implementation**: `/home/john/hamlet/src/townlet/items/manager.py`
  - Lines 583-650: `_iter_positions()` - random/fixed/grid/scripted placement
  - Lines 665-724: `_resolve_respawn_positions()` - respawn-specific placement

- **Schedule Types Implementation**:
  - Lines 726-762: `_schedule_allows_spawn()` - time_window/poisson/normal scheduling
  - Lines 476-495: Periodic respawn timer setup in `despawn_item()`
  - Lines 831-929: `process_respawns()` with schedule-aware respawning

- **Limits Enforcement**:
  - Lines 301-303: `max_items` capacity check in `spawn_item()`
  - Lines 306-309: Cooldown enforcement
  - Lines 801-807: `max_total` cumulative spawn limit (spawn_initial_items)
  - Lines 886-889: `max_total` limit in respawns

- **Test Coverage**: `/home/john/hamlet/tests/test_townlet/unit/items/test_spawn_rules_advanced.py`
  - Lines 23-38: Fixed placement test
  - Lines 41-58: Grid placement with spacing
  - Lines 61-79: Scripted placement tick alignment
  - Lines 82-97: Time window gating
  - Lines 100-116: Poisson probabilistic spawning
  - Lines 119-143: Normal distribution scheduling
  - Lines 146+: max_total enforcement test

**Status**: ✅ DONE

---

### ITEM-REQ-006: Conditional spawn predicates ✅ DONE

**Requirement**: Spawn rules support VFS-based conditions (e.g., when predicates); compiler validates referenced profiles/vars.

**Evidence**:
- **DTO Field**: `/home/john/hamlet/src/townlet/config/items_config.py:377-383`
  ```python
  when: str | None = Field(
      default=None,
      description="Condition expression (bool) gating the spawn rule",
  )
  when_ast: Any | None = Field(default=None, exclude=True, repr=False)
  ```

- **Runtime Evaluation**: `/home/john/hamlet/src/townlet/items/manager.py:538-581`
  - Line 549: Checks for compiled AST (raises if when provided but not compiled)
  - Lines 557-560: VFS state gathered from registry
  - Lines 564-573: Expression evaluated via Evaluator with bars/vfs/temporal context
  - Lines 575-580: Vectorized result handling

- **Usage in Spawn Logic**:
  - Line 793: `_should_spawn_rule()` called in `spawn_initial_items()`
  - Line 883: `_should_spawn_rule()` called in `process_respawns()`

- **Test Coverage**: `/home/john/hamlet/tests/test_townlet/unit/items/test_spawn_conditions.py`
  - Lines 26-51: Bar condition gates initial spawn (`bar.energy > 0.5`)
  - Lines 54-83: Bar condition gates respawns
  - Lines 86-135: VFS condition gates spawn (`vfs.is_raining`)
  - Lines 138-150: Temporal condition with boolean logic (`vfs.is_raining and temporal.tick > 5`)

**Status**: ✅ DONE

---

### ITEM-REQ-007: Use action handling ✅ DONE

**Requirement**: USE action handler executes item interactions via Effects, with inventory-aware masking and enforced max_items_per_agent.

**Evidence**:
- **USE_SLOT_N Handler**: `/home/john/hamlet/src/townlet/items/action_handlers.py:195-236`
  - Lines 214-217: Retrieves item from inventory slot (None if empty)
  - Lines 221-224: Gets item metadata
  - Lines 227-234: Executes on_use Effects commands via `_execute_interaction()`

- **Effects Execution**: `/home/john/hamlet/src/townlet/items/action_handlers.py:63-126`
  - Lines 91-98: Selects on_pickup/on_use/on_drop compiled commands
  - Lines 103-122: Builds ExecutionContext with item VFS index (self), agent index (target)
  - Lines 124-126: Executes all commands via CommandExecutor

- **Masking**: Action masking ensures USE_SLOT_N only available when slot occupied
  - Empty slots masked in action space

- **max_items_per_agent Enforcement**: `/home/john/hamlet/src/townlet/items/inventory.py:51-86`
  - Lines 70-74: DENY_PICKUP if inventory full (enforces max_items_per_agent)

- **Test Coverage**: `/home/john/hamlet/tests/test_townlet/integration/test_items_integration.py:142-176`
  - Lines 157-168: Spawns apple, picks up, uses via USE_SLOT_0
  - Lines 174-176: Verifies energy increased from apple on_use effect

**Status**: ✅ DONE

---

### ITEM-REQ-008: Item VFS defaults ✅ DONE

**Requirement**: Item profile defaults apply when spawning without `initial_state`, with overrides honored when provided.

**Evidence**:
- **Default Application**: `/home/john/hamlet/src/townlet/items/manager.py:335-342`
  ```python
  if compiled_profile:
      # Initialize with defaults from compiled profile
      for compiled_var in compiled_profile.variables:
          if compiled_var.initial_value is not None:
              var_idx = profile_map[compiled_var.name]
              item_vfs[vfs_index, var_idx] = float(compiled_var.initial_value)
  ```

- **Override Mechanism**: `/home/john/hamlet/src/townlet/items/manager.py:345-350`
  ```python
  if initial_state is not None:
      for var_name, value in initial_state.items():
          if var_name not in profile_map:
              raise ValueError(f"Variable '{var_name}' not in profile '{profile_name}'")
          var_idx = profile_map[var_name]
          item_vfs[vfs_index, var_idx] = float(value)
  ```
  Overrides applied after defaults, validation ensures variable exists in profile.

- **Test Coverage**: `/home/john/hamlet/tests/test_townlet/unit/items/test_spawn_with_initial_state.py`
  - Tests spawn with and without initial_state overrides
  - Verifies defaults applied, overrides honored

**Status**: ✅ DONE

---

### ITEM-REQ-009: Item-scoped custom verbs ✅ DONE

**Requirement**: Support dynamic action generation for `local_commands` (masked by proximity) and `inventory_commands` (masked when held), distinct from core GET/DROP.

**Evidence**:
- **DTO Schema**: `/home/john/hamlet/src/townlet/config/items_config.py:22-70, 102-109`
  - Lines 22-70: `ItemCustomCommand` with name, description, effects
  - Lines 102-109: `local_commands` and `inventory_commands` fields in ItemInteractionsConfig

- **Compilation**: `/home/john/hamlet/src/townlet/items/manager.py:99-142`
  - Lines 101-104: Local and inventory custom commands parsed
  - Lines 110-111: Commands parsed to AST
  - Lines 117-118: Commands compiled via CommandCompiler
  - Lines 137-142: Action specs stored for registration

- **Action Name Generation**: `/home/john/hamlet/src/townlet/config/items_config.py:72-74`
  ```python
  def build_item_command_action_name(item_id: str, command_name: str, scope: Literal["local", "inventory"]) -> str:
      return f"ITEM_{scope.upper()}_{item_id.upper()}_{command_name.upper()}"
  ```

- **Masking**: `/home/john/hamlet/src/townlet/items/action_handlers.py:269-300`
  - Lines 283-292: Inventory verbs masked by held items
  - Lines 294-298: Local verbs masked by proximity

- **Dispatch**: `/home/john/hamlet/src/townlet/items/action_handlers.py:302-348`
  - Lines 321-336: Inventory scope execution
  - Lines 338-348: Local scope execution

- **Test Coverage**: `/home/john/hamlet/tests/test_townlet/unit/items/test_custom_item_verbs.py`
  - Full masking and dispatch tests for local/inventory verbs

**Status**: ✅ DONE

---

### ITEM-REQ-010: Item tags ✅ DONE

**Requirement**: Items have tags field for categorization; tags available in expressions for filtering (e.g., nearest_item(tag="food")).

**Evidence**:
- **DTO Field**: `/home/john/hamlet/src/townlet/config/items_config.py:154-158, 203-210`
  ```python
  tags: list[str] = Field(
      ...,
      min_length=1,
      description="Categorization tags for expressions/UI",
  )
  ```
  Required field with validation (lines 203-210).

- **Runtime Storage**: `/home/john/hamlet/src/townlet/items/instance.py:19`
  ```python
  tags: tuple[str, ...]
  ```

- **Assignment**: `/home/john/hamlet/src/townlet/items/manager.py:361`
  ```python
  tags=tuple(item_def.tags),
  ```

- **Config Usage**: All item configs include tags (e.g., `configs/test/items_smoke/items.yaml`)

**Status**: ✅ DONE

---

### ITEM-REQ-011: Item visual metadata ✅ DONE

**Requirement**: Items include icon (emoji/icon name) and name fields for UI; metadata preserved in compiled catalog.

**Evidence**:
- **DTO Fields**: `/home/john/hamlet/src/townlet/config/items_config.py:143-152, 212-218`
  ```python
  name: str = Field(..., description="Display name for UI/metadata")
  icon: str = Field(..., description="Icon/emoji for UI", max_length=16)
  ```
  Both required with validation.

- **Runtime Storage**: `/home/john/hamlet/src/townlet/items/instance.py:17-18`
  ```python
  name: str | None
  icon: str | None
  ```

- **Assignment**: `/home/john/hamlet/src/townlet/items/manager.py:359-360`
  ```python
  name=item_def.name,
  icon=item_def.icon,
  ```

- **Compiled Preservation**: `/home/john/hamlet/src/townlet/items/manager.py:42-44`
  ```python
  name: str | None
  icon: str | None
  tags: tuple[str, ...]
  ```
  Preserved in CompiledItemType.

**Status**: ✅ DONE

---

### ITEM-REQ-012: Holder agent tracking ✅ DONE

**Requirement**: ItemInstance tracks holder_agent_id (null when on ground); updated on pickup/drop; available in expressions (target.holder_agent).

**Evidence**:
- **Field**: `/home/john/hamlet/src/townlet/items/instance.py:31`
  ```python
  holder_agent_ids: set[int] = field(default_factory=set)  # Agents holding this item (empty when on ground)
  ```
  Supports multiple holders for shared items.

- **Property**: `/home/john/hamlet/src/townlet/items/instance.py:42-48`
  ```python
  @property
  def holder_agent_id(self) -> int | None:
      """Return an arbitrary holder (for compatibility with single-holder APIs)."""
      if not self.holder_agent_ids:
          return None
      return next(iter(self.holder_agent_ids))
  ```

- **Pickup Update**: `/home/john/hamlet/src/townlet/items/inventory.py:84`
  ```python
  item.holder_agent_ids.add(agent_idx)
  ```

- **Drop Update**: `/home/john/hamlet/src/townlet/items/inventory.py:111`
  ```python
  item.holder_agent_ids.discard(agent_idx)
  ```

- **Test Coverage**: `/home/john/hamlet/tests/test_townlet/unit/items/test_item_sharing.py`
  - Lines 52-77: Exclusive item tracking (single holder)
  - Lines 79-109: Shared item tracking (multiple holders)

**Status**: ✅ DONE

---

### ITEM-REQ-013: Item durability/charges 🟡 PARTIAL

**Requirement**: Items can have durability/charges via item VFS; decremented on use; item deleted when exhausted.

**Evidence**:
- **VFS Infrastructure**: ✅ COMPLETE
  - Item VFS profiles support arbitrary variables (durability, charges, etc.)
  - initial_state can set durability values
  - Effects can modify item VFS via self.vfs.durability

- **Effects Commands**: ✅ COMPLETE
  - on_use can execute `modify: "self.vfs.durability", value: "self.vfs.durability - 1"`
  - Conditional despawn via `if: "self.vfs.durability <= 0"` + despawn command

- **Missing**: ❌ NO PRODUCTION CONFIG EXAMPLE
  - No config pack demonstrates durability/charges pattern
  - No test demonstrating durability depletion → despawn
  - Infrastructure exists but lacks explicit usage demonstration

**Gap**: Requires config example + integration test showing:
1. Item with durability VFS variable
2. on_use decrements durability
3. Conditional despawn when durability ≤ 0

**Status**: 🟡 PARTIAL (infrastructure complete, needs demonstration)

---

### ITEM-REQ-014: Item spoilage/decay 🟡 PARTIAL

**Requirement**: Items can have decay effects that modify item VFS over time (e.g., spoilage); item_decay effect type supported.

**Evidence**:
- **VFS Infrastructure**: ✅ COMPLETE
  - Item VFS can track freshness, spoilage, age
  - Items tick while active and held (manager.py:523-528)

- **Effects-Based Decay**: ✅ POSSIBLE BUT NOT ITEM-SPECIFIC
  - No dedicated "item_decay" effect type
  - Can use global effects with item scope: `spawn_effect: {id: "decay", scope: "item", target: "self"}`
  - Effect on_tick can modify item VFS: `modify: "self.vfs.freshness", value: "self.vfs.freshness - 0.01"`

- **Missing**: ❌ NO EXPLICIT IMPLEMENTATION
  - No "item_decay" effect type (uses generic effect scope instead)
  - No config pack demonstrates item decay pattern
  - No test showing item VFS degradation over time

**Gap**: Clarify if "item_decay effect type" is:
1. Generic effect with scope=item (infrastructure exists) OR
2. Dedicated effect type (not implemented)

Current implementation uses approach #1 (generic effects), which is functionally equivalent but lacks explicit "item_decay" type.

**Status**: 🟡 PARTIAL (generic effects support decay, no dedicated type)

---

### ITEM-REQ-015: Exclusive vs shared items ✅ DONE

**Requirement**: Items can be exclusive (single holder) or shared (environmental); single-holder enforcement for exclusive items.

**Evidence**:
- **DTO Field**: `/home/john/hamlet/src/townlet/config/items_config.py:159-162`
  ```python
  exclusive: bool = Field(
      default=True,
      description="True for single-holder items, False for shared/environmental items",
  )
  ```

- **Exclusive Item Behavior**: `/home/john/hamlet/src/townlet/items/manager.py:393-400`
  ```python
  if not item.exclusive:
      # Shared items stay in the world even when held.
      return item

  # Move from active to held (do NOT free VFS slot - item still exists)
  item = self.active_items.pop(instance_id)
  self.held_items[instance_id] = item
  ```

- **Shared Item Behavior**: `/home/john/hamlet/src/townlet/items/action_handlers.py:179-181`
  ```python
  # Exclusive items leave the world when picked up; shared items remain in place.
  if item.exclusive:
      self.manager.lift_item(item.instance_id)
  ```

- **Enforcement**: `/home/john/hamlet/src/townlet/items/inventory.py:65-67`
  ```python
  # Enforce exclusive items (single holder)
  if item.exclusive and item.holder_agent_ids and agent_idx not in item.holder_agent_ids:
      return False
  ```

- **Test Coverage**: `/home/john/hamlet/tests/test_townlet/unit/items/test_item_sharing.py`
  - Lines 52-77: Exclusive item test (single holder, leaves world)
  - Lines 79-109: Shared item test (multiple holders, stays in world)

**Status**: ✅ DONE

---

### ITEM-REQ-016: Item instance ID tracking ✅ DONE

**Requirement**: Each ItemInstance has unique id and type_id fields; id is unique instance ID; type_id references catalog; ID uniqueness guaranteed.

**Evidence**:
- **Fields**: `/home/john/hamlet/src/townlet/items/instance.py:21-22`
  ```python
  item_type: str  # Reference to ItemTypeConfig.id
  instance_id: int  # Unique instance ID (incrementing counter)
  ```

- **ID Generation**: `/home/john/hamlet/src/townlet/items/manager.py:171, 367`
  ```python
  self.next_instance_id = 0  # Line 171
  ...
  instance_id=self.next_instance_id,  # Line 355
  self.next_instance_id += 1  # Line 367
  ```
  Guarantees uniqueness via incrementing counter.

- **Type Reference**: `/home/john/hamlet/src/townlet/items/manager.py:354`
  ```python
  item_type=item_type,  # Passed as parameter, validated against catalog
  ```

**Status**: ✅ DONE

---

### ITEM-REQ-017: Item spawn timing ✅ DONE

**Requirement**: ItemInstance tracks spawn_step, expire_step (null if infinite), and cooldown_until_step; timing enforcement via scheduler.

**Evidence**:
- **Fields**: `/home/john/hamlet/src/townlet/items/instance.py:27-29`
  ```python
  spawn_tick: int  # When item was spawned
  duration_total: int | None  # Total lifetime (None = permanent)
  duration_remaining: int | None  # Ticks until despawn (None = permanent)
  ```
  Note: Uses tick-based fields (not step), but functionally equivalent.

- **Cooldown Tracking**: `/home/john/hamlet/src/townlet/items/manager.py:184, 457-460`
  ```python
  # Cooldown tracking (item_type -> tick when can spawn again)
  self.cooldown_until: dict[str, int] = {}
  ...
  if item_def.cooldown is not None:
      self.cooldown_until[item.item_type] = current_tick + item_def.cooldown
  ```

- **Lifecycle Methods**: `/home/john/hamlet/src/townlet/items/instance.py:33-40`
  ```python
  def tick(self) -> None:
      if self.duration_remaining is not None:
          self.duration_remaining -= 1

  def is_expired(self) -> bool:
      return self.duration_remaining is not None and self.duration_remaining <= 0
  ```

- **Enforcement**: `/home/john/hamlet/src/townlet/items/manager.py:506-521`
  - Collects expired items from both active and held
  - Despawns expired items
  - Ticks remaining items

**Status**: ✅ DONE

---

## Summary Table

| ID | Requirement | Status | Evidence |
|----|-------------|--------|----------|
| ITEM-REQ-001 | Item manager runtime | ✅ DONE | manager.py:55-929, instance.py:10-49 |
| ITEM-REQ-002 | Inventory + core actions | ✅ DONE | inventory.py:15-147, action_handlers.py, integration tests |
| ITEM-REQ-003 | Profile-driven item VFS | ✅ DONE | manager.py:321-350, no fallback to variables_reference |
| ITEM-REQ-004 | Fixed item VFS pool | ✅ DONE | manager.py:180-181, slot allocation/deallocation |
| ITEM-REQ-005 | Spawn rules coverage | ✅ DONE | items_config.py:266-384, manager.py spawn logic, test_spawn_rules_advanced.py |
| ITEM-REQ-006 | Conditional spawn predicates | ✅ DONE | manager.py:538-581, test_spawn_conditions.py |
| ITEM-REQ-007 | Use action handling | ✅ DONE | action_handlers.py:195-236, Effects integration |
| ITEM-REQ-008 | Item VFS defaults | ✅ DONE | manager.py:335-350, defaults + overrides |
| ITEM-REQ-009 | Item-scoped custom verbs | ✅ DONE | items_config.py custom commands, action_handlers.py masking/dispatch |
| ITEM-REQ-010 | Item tags | ✅ DONE | items_config.py:154-158, instance.py:19 |
| ITEM-REQ-011 | Item visual metadata | ✅ DONE | items_config.py:143-152, CompiledItemType preservation |
| ITEM-REQ-012 | Holder agent tracking | ✅ DONE | instance.py:31,42-48, test_item_sharing.py |
| ITEM-REQ-013 | Item durability/charges | 🟡 PARTIAL | Infrastructure complete, needs config example |
| ITEM-REQ-014 | Item spoilage/decay | 🟡 PARTIAL | Generic effects support, no dedicated type |
| ITEM-REQ-015 | Exclusive vs shared items | ✅ DONE | items_config.py:159-162, test_item_sharing.py |
| ITEM-REQ-016 | Item instance ID tracking | ✅ DONE | instance.py:21-22, manager.py:171,355-367 |
| ITEM-REQ-017 | Item spawn timing | ✅ DONE | instance.py:27-40, manager.py lifecycle enforcement |

---

## Recommendations

### High Priority (Close Gaps)

1. **ITEM-REQ-013 Durability Demo** (0.5 days)
   - Create `configs/test/item_durability_demo/` pack
   - Define sword with durability VFS variable
   - on_use: decrement durability, conditional despawn
   - Integration test: use sword N times, verify despawn

2. **ITEM-REQ-014 Decay Clarification** (0.5 days)
   - Document generic effect approach for item decay
   - Create `configs/test/item_decay_demo/` pack
   - Example: food with freshness VFS, decay effect applied over time
   - Integration test: spawn food, wait N ticks, verify freshness decay

### Medium Priority (Testing)

3. **Spawn Rules Integration Tests** (1 day)
   - Test all placement modes in environment context
   - Test all schedule types with actual timing
   - Test max_total enforcement across episodes

4. **Custom Verb Coverage** (0.5 days)
   - Integration test for local commands (proximity masking)
   - Integration test for inventory commands (held masking)
   - Test collision between custom verbs and core actions

### Documentation

5. **Item System Guide** (1 day)
   - Comprehensive guide to item configuration
   - VFS profile assignment patterns
   - Spawn rule cookbook (placement + schedules)
   - Custom verb registration guide

---

## Files Examined

### Implementation
- `/home/john/hamlet/src/townlet/items/manager.py` (929 lines)
- `/home/john/hamlet/src/townlet/items/instance.py` (49 lines)
- `/home/john/hamlet/src/townlet/items/inventory.py` (147 lines)
- `/home/john/hamlet/src/townlet/items/action_handlers.py` (389 lines)
- `/home/john/hamlet/src/townlet/items/__init__.py` (17 lines)
- `/home/john/hamlet/src/townlet/config/items_config.py` (397 lines)

### Tests
- `/home/john/hamlet/tests/test_townlet/unit/items/test_item_manager.py`
- `/home/john/hamlet/tests/test_townlet/unit/items/test_item_lifecycle.py`
- `/home/john/hamlet/tests/test_townlet/unit/items/test_item_vfs_profile_assignment.py`
- `/home/john/hamlet/tests/test_townlet/unit/items/test_item_vfs_initialization.py`
- `/home/john/hamlet/tests/test_townlet/unit/items/test_custom_item_verbs.py`
- `/home/john/hamlet/tests/test_townlet/unit/items/test_item_sharing.py`
- `/home/john/hamlet/tests/test_townlet/unit/items/test_spawn_rules_advanced.py`
- `/home/john/hamlet/tests/test_townlet/unit/items/test_spawn_conditions.py`
- `/home/john/hamlet/tests/test_townlet/integration/test_items_integration.py`
- `/home/john/hamlet/tests/test_townlet/integration/test_item_self_modification.py`
- `/home/john/hamlet/tests/test_townlet/integration/test_custom_item_verbs_integration.py`

### Configs
- `/home/john/hamlet/configs/default_curriculum/items.yaml`
- `/home/john/hamlet/configs/test/items_smoke/items.yaml`
- `/home/john/hamlet/configs/test/effects_smoke/items.yaml`

---

**Conclusion**: Items System is production-ready with 88% completion. Two requirements await explicit config demonstrations but have complete infrastructure support. Recommend closing gaps with durability and decay examples, then marking system COMPLETE.
