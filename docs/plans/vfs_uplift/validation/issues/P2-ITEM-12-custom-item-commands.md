# [ITEM-12] Custom Item Commands

**Priority:** P2 (Minor)
**Category:** Items
**Status:** MISSING
**Effort:** Phase 4+ feature (2-3 days when needed)

## Description

Items system lacks support for custom item-specific commands beyond standard GET/DROP/USE. Cannot define item-local commands (COMBINE, REPAIR, UPGRADE) or inventory management commands (SORT, TRANSFER, EQUIP). All item interactions currently limited to USE command with effects.

## Current State

**Working (standard commands):**
- ✅ GET: Pick up item from world
- ✅ DROP: Drop item from inventory
- ✅ USE: Use item (trigger effects)

**Missing (custom commands):**
- ❌ Local commands: Item-specific actions (COMBINE potions, REPAIR sword, UPGRADE armor)
- ❌ Inventory commands: Inventory management (SORT inventory, TRANSFER to chest, EQUIP weapon)
- ❌ Command composition: Chaining commands (COMBINE then USE)
- ❌ Conditional commands: Command gating (REPAIR only if durability < 50%)

**Use cases blocked:**
- Crafting: COMBINE apple + flour → apple_pie
- Item maintenance: REPAIR sword (restore durability)
- Progression: UPGRADE armor (improve stats)
- Inventory management: SORT inventory (organize items)
- Equipment: EQUIP sword (move to active slot)

## Required Implementation

**Note:** This is intentionally deferred to Phase 4+ as it represents advanced item interaction mechanics not needed for Phase 1-3 curriculum levels.

### 1. Schema Enhancement (1 day)

**File:** `src/townlet/items/schema.py`

**Add custom command definitions:**
```yaml
# items_catalog.yaml
items:
  sword:
    # ... existing fields ...

    # NEW: Local commands (item-specific)
    local_commands:
      - name: "REPAIR"
        description: "Restore sword durability"
        conditions:
          - path: "vfs.durability"
            operator: "<"
            value: 0.5
        effects:
          - type: "modify"
            target: "self"
            path: "vfs.durability"
            operation: "set"
            value: 1.0
        cost:
          bar.money: 10  # Costs $10 to repair

      - name: "UPGRADE"
        description: "Increase sword damage"
        conditions:
          - path: "vfs.upgrade_level"
            operator: "<"
            value: 5
        effects:
          - type: "modify"
            target: "self"
            path: "vfs.damage"
            operation: "add"
            value: 5
          - type: "modify"
            target: "self"
            path: "vfs.upgrade_level"
            operation: "add"
            value: 1

  apple:
    # ... existing fields ...

    local_commands:
      - name: "COMBINE"
        description: "Combine with flour to make pie"
        requirements:
          - item_type: "flour"  # Must have flour in inventory
            min_count: 1
        effects:
          - type: "spawn_item"
            item_type: "apple_pie"
          - type: "consume_item"
            item_type: "apple"
            count: 1
          - type: "consume_item"
            item_type: "flour"
            count: 1

# NEW: Inventory commands (global, not item-specific)
inventory_commands:
  - name: "SORT"
    description: "Sort inventory by item type"
    action: "sort_inventory"
    sort_key: "item_type"  # Or "quantity", "quality", "recent"

  - name: "TRANSFER"
    description: "Transfer item to storage"
    target_type: "item"  # Requires targeting an item
    requirements:
      - affordance: "chest"  # Must be near chest
        distance: 1
    action: "transfer_to_storage"

  - name: "EQUIP"
    description: "Equip weapon or armor"
    target_type: "item"
    requirements:
      - item_property: "equippable"
        value: true
    action: "equip_item"
```

**Schema classes:**
```python
@dataclass
class ItemCommand:
    """Custom item command definition."""
    name: str
    description: str
    conditions: Optional[List[ConditionSpec]] = None  # VFS predicates
    requirements: Optional[List[RequirementSpec]] = None  # Item/affordance requirements
    effects: List[EffectCommand] = field(default_factory=list)
    cost: Optional[Dict[str, float]] = None  # Resource costs (bar.money, etc.)

@dataclass
class ItemDefinition:
    # ... existing fields ...

    # NEW: Item-local commands
    local_commands: List[ItemCommand] = field(default_factory=list)

@dataclass
class ItemsCatalogConfig:
    # ... existing fields ...

    # NEW: Inventory-global commands
    inventory_commands: List[InventoryCommand] = field(default_factory=list)
```

### 2. Command Execution (1 day)

**File:** `src/townlet/items/manager.py`

**Add command execution logic:**
```python
class ItemManager:
    def execute_item_command(
        self,
        agent_idx: int,
        item_id: int,
        command_name: str
    ) -> bool:
        """Execute custom item command."""

        item = self.get_item(item_id)
        command = self._find_command(item.item_type, command_name)

        if not command:
            return False

        # Check conditions (VFS predicates)
        if not self._check_conditions(command.conditions, item, agent_idx):
            return False

        # Check requirements (items, affordances, resources)
        if not self._check_requirements(command.requirements, agent_idx):
            return False

        # Pay costs (resources)
        if command.cost:
            if not self._pay_costs(command.cost, agent_idx):
                return False

        # Execute effects
        context = self._create_execution_context(agent_idx, item_id)
        self.effect_executor.execute_commands(command.effects, context)

        return True

    def _check_conditions(self, conditions: List[ConditionSpec], item, agent_idx) -> bool:
        """Check if command conditions are met."""
        for condition in conditions:
            value = self._resolve_path(condition.path, item, agent_idx)
            if not self._evaluate_operator(value, condition.operator, condition.value):
                return False
        return True

    def _check_requirements(self, requirements: List[RequirementSpec], agent_idx) -> bool:
        """Check if command requirements are met."""
        for req in requirements:
            if req.item_type:
                # Check inventory for required item
                if not self.has_item(agent_idx, req.item_type, min_count=req.min_count):
                    return False
            if req.affordance:
                # Check proximity to required affordance
                if not self.is_near_affordance(agent_idx, req.affordance, max_distance=req.distance):
                    return False
        return True

    def _pay_costs(self, costs: Dict[str, float], agent_idx: int) -> bool:
        """Deduct resource costs (bar values, VFS variables)."""
        for resource, amount in costs.items():
            if resource.startswith("bar."):
                bar_name = resource[4:]
                if self.bar_manager.get(agent_idx, bar_name) < amount:
                    return False  # Insufficient resources
                self.bar_manager.subtract(agent_idx, bar_name, amount)
        return True
```

### 3. Action Space Integration (1 day)

**File:** `src/townlet/environment/action_config.py`

**Add custom command actions to action space:**
```python
# Action vocabulary expansion
# Standard: MOVE_N, MOVE_S, ..., INTERACT, WAIT, GET, DROP, USE
# Custom item commands become actions: REPAIR, UPGRADE, COMBINE, SORT, TRANSFER, EQUIP

# Action execution in environment:
if action_name == "REPAIR":
    success = item_manager.execute_item_command(agent_idx, targeted_item_id, "REPAIR")
elif action_name == "COMBINE":
    success = item_manager.execute_item_command(agent_idx, targeted_item_id, "COMBINE")
# etc.
```

### 4. Testing (1 day)

**File:** `tests/test_townlet/unit/items/test_custom_commands.py` (to be created)

**Test cases:**
- Execute REPAIR command (restore durability)
- REPAIR blocked by insufficient resources
- COMBINE command (crafting)
- COMBINE blocked by missing ingredient
- UPGRADE command (progression)
- UPGRADE blocked by max level
- SORT inventory command
- TRANSFER command requires chest affordance
- EQUIP command with equippable items

## Acceptance Criteria

**Phase 4+ Implementation (not required for Phase 1-3 merge):**
- [ ] ItemCommand schema with conditions, requirements, effects, costs
- [ ] ItemDefinition has local_commands field
- [ ] ItemsCatalogConfig has inventory_commands field
- [ ] ItemManager.execute_item_command() executes custom commands
- [ ] Condition checking (VFS predicates)
- [ ] Requirement checking (items, affordances, resources)
- [ ] Cost deduction (bars, VFS variables)
- [ ] Effect execution (reuse effects system)
- [ ] Action space integration (custom commands become actions)
- [ ] 20+ tests covering command execution, conditions, requirements, costs
- [ ] Documentation with custom command examples

## Evidence

**Source Report:** gap-report-final.md (lines 71-94), gap-report-items.md
**Status:** Intentionally deferred to Phase 4+ (not needed for Phase 1-3 curriculum)

## Implementation Notes

**Why P2 (not P1/P0):** Advanced item interaction feature for Phase 4+ gameplay mechanics. Phase 1-3 curriculum levels use simple item interactions (GET/DROP/USE sufficient). Custom commands needed for:
- Phase 4: Crafting and item progression
- Phase 5: Multi-agent trading and item transfer
- Phase 6: Complex item-based puzzles and mechanics

**Design Philosophy:**
- Reuse effects system (custom commands execute effect commands)
- Declarative configuration (YAML, not Python code)
- Flexible composition (commands can spawn items, modify VFS, trigger cascades)

**Command Types:**

1. **Local Commands (item-specific):**
   - Defined per item type
   - Context: Single item being acted upon
   - Examples: REPAIR sword, COMBINE apple, UPGRADE armor

2. **Inventory Commands (global):**
   - Defined in catalog root (not per-item)
   - Context: Entire inventory
   - Examples: SORT inventory, TRANSFER to chest

3. **Standard Commands (built-in):**
   - GET, DROP, USE (always available)
   - Cannot be overridden by custom commands

**Use Case Examples:**

**Crafting (COMBINE):**
```yaml
local_commands:
  - name: "COMBINE"
    requirements:
      - item_type: "flour"
        min_count: 1
    effects:
      - type: "spawn_item"
        item_type: "apple_pie"
      - type: "consume_item"
        item_type: "apple"
      - type: "consume_item"
        item_type: "flour"
```

**Repair (Durability):**
```yaml
local_commands:
  - name: "REPAIR"
    conditions:
      - path: "vfs.durability"
        operator: "<"
        value: 0.5
    cost:
      bar.money: 10
    effects:
      - type: "modify"
        target: "self"
        path: "vfs.durability"
        operation: "set"
        value: 1.0
```

**Upgrade (Progression):**
```yaml
local_commands:
  - name: "UPGRADE"
    conditions:
      - path: "vfs.upgrade_level"
        operator: "<"
        value: 5
    cost:
      bar.money: 50
      vfs.experience: 100
    effects:
      - type: "modify"
        target: "self"
        path: "vfs.damage"
        operation: "add"
        value: 5
```

**Integration with Existing Systems:**
- **Effects:** Commands execute effect commands (reuse effects executor)
- **VFS:** Conditions and effects use VFS paths
- **Actions:** Commands become actions in action space
- **Affordances:** Commands can require proximity to affordances

**Performance Considerations:**
- Custom commands add action space size (more actions = larger Q-network output)
- Recommendation: Limit to 5-10 custom commands per item type
- Alternative: Context-dependent action masking (only show available commands)

**Future Enhancements:**
- **Command composition:** Chain commands (COMBINE then USE)
- **Command macros:** Define multi-step command sequences
- **Command learning:** Agent learns new commands through gameplay
- **Command discovery:** Hidden commands unlocked by exploration

## References

- Schema: `src/townlet/items/schema.py` (add ItemCommand, local_commands, inventory_commands)
- Manager: `src/townlet/items/manager.py` (add execute_item_command())
- Action config: `src/townlet/environment/action_config.py` (add custom command actions)
- Test file: `tests/test_townlet/unit/items/test_custom_commands.py` (to be created when implemented)
- Documentation: `docs/config-schemas/items.md` (add custom commands section)
- Related: Phase 4+ gameplay design, crafting system, item progression
