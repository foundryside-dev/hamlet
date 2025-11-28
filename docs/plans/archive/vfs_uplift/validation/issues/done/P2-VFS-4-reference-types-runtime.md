# [VFS-4] Reference Types Runtime Support

**Priority:** P2 (Minor)
**Category:** VFS
**Status:** PARTIAL
**Effort:** 3-4 days

## Description

Reference types (`agent_ref`, `item_ref`) are declared in VFS schema but runtime resolution (traversing references to read referenced entity's VFS variables) is not implemented. Cannot express paths like `vfs:target.vfs.energy` where `target` is an agent reference, or `vfs:held_item.vfs.quality` where `held_item` is an item reference.

## Current State

**Schema support (exists):**
```python
# src/townlet/vfs/schema.py
class VariableType(str, Enum):
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"
    VECTOR3 = "vector3"
    AGENT_REF = "agent_ref"  # ✅ Declared
    ITEM_REF = "item_ref"    # ✅ Declared
```

**Runtime resolution (missing):**
- Can define variable: `target: {type: agent_ref}`
- Can store agent ID in variable: `registry.set("agent", agent_idx, "target", target_agent_idx)`
- ❌ Cannot traverse reference in expressions: `vfs:target.vfs.energy`
- ❌ No runtime reference resolution in ExecutionContext.get()

**Use cases blocked:**
- Social interactions: Read friend's mood (`vfs:friend.vfs.mood`)
- Item quality checks: Conditional on held item quality (`vfs:held_item.vfs.quality > 0.8`)
- Target-based effects: Damage based on target's defense (`vfs:target.vfs.defense`)
- Reference chains: `vfs:friend.vfs.held_item.vfs.quality` (nested references)

## Required Implementation

### 1. Reference Resolution in ExecutionContext (1-2 days)

**File:** `src/townlet/effects/context.py`

**Current path resolution:**
```python
def get(self, path: str) -> Any:
    """Resolve path to value."""
    if path.startswith("bar."):
        bar_name = path[4:]
        return self.bars[bar_name][self.agent_idx]

    elif path.startswith("vfs."):
        var_name = path[4:]
        return self.vfs_registry.get("agent", self.agent_idx, var_name)

    # Other path types...
```

**Enhanced with reference resolution:**
```python
def get(self, path: str) -> Any:
    """Resolve path to value, including reference traversal."""

    # Split path into segments
    segments = path.split(".")

    # Start with root context
    current_scope = "agent"
    current_idx = self.agent_idx

    for i, segment in enumerate(segments):
        if segment == "bar":
            # Bar access: bar.energy
            bar_name = segments[i + 1]
            return self.bars[bar_name][current_idx]

        elif segment == "vfs":
            # VFS access: vfs.energy or vfs.target.vfs.health
            var_name = segments[i + 1]
            value = self.vfs_registry.get(current_scope, current_idx, var_name)

            # Check if value is a reference
            var_type = self._get_variable_type(current_scope, var_name)
            if var_type == "agent_ref":
                # Value is agent index, traverse reference
                current_scope = "agent"
                current_idx = int(value)  # Reference value is index
                # Continue to next segment (e.g., .vfs.energy)

            elif var_type == "item_ref":
                # Value is item index, traverse reference
                current_scope = "item"
                current_idx = int(value)
                # Continue to next segment

            else:
                # Value is not a reference, return it
                return value

    raise ValueError(f"Invalid path: {path}")

def _get_variable_type(self, scope: str, var_name: str) -> str:
    """Get variable type from compiled VFS profiles."""
    profile = self._get_profile(scope)
    if profile and var_name in profile.variables:
        return profile.variables[var_name].type
    return None
```

### 2. Reference Type Checking (1 day)

**File:** `src/townlet/world/expression/type_checker.py` (depends on COMP-9)

**Type checker enhancement:**
```python
def check_path_expression(self, node: PathNode) -> str:
    """Type check path expression with reference traversal."""

    segments = node.path.split(".")
    current_type = None

    for i, segment in enumerate(segments):
        if segment == "vfs":
            var_name = segments[i + 1]
            var_type = self._lookup_variable_type(var_name)

            if var_type in ("agent_ref", "item_ref"):
                # Reference type - next segment should be .vfs or .bar
                if i + 2 < len(segments):
                    next_segment = segments[i + 2]
                    if next_segment not in ("vfs", "bar"):
                        raise TypeError(
                            f"Invalid reference traversal: {node.path}\n"
                            f"After reference, expected .vfs or .bar, got .{next_segment}"
                        )
                current_type = var_type
            else:
                # Non-reference type, return it
                current_type = var_type
                break

    return current_type
```

### 3. Reference Validation (1 day)

**File:** `src/townlet/vfs/registry.py`

**Add reference validation:**
```python
class VFSRegistry:
    def validate_reference(self, scope: str, idx: int, var_name: str) -> bool:
        """Validate that reference value points to valid entity."""
        value = self.get(scope, idx, var_name)
        var_type = self._get_variable_type(scope, var_name)

        if var_type == "agent_ref":
            # Check if referenced agent exists
            if value < 0 or value >= self.num_agents:
                raise ValueError(
                    f"Invalid agent reference: {value} (valid range: 0-{self.num_agents-1})"
                )
            return True

        elif var_type == "item_ref":
            # Check if referenced item exists
            if value < 0 or value >= len(self.items):
                raise ValueError(
                    f"Invalid item reference: {value} (valid range: 0-{len(self.items)-1})"
                )
            return True

        return False
```

### 4. Testing (1 day)

**File:** `tests/test_townlet/unit/vfs/test_reference_types.py` (new)

**Test cases:**
```python
def test_agent_ref_traversal():
    """Test traversing agent reference to read VFS variable."""
    # Agent 0 has vfs:target = 1 (references agent 1)
    # Agent 1 has vfs:energy = 0.8
    context = create_context(agent_idx=0)

    # Traverse reference
    value = context.get("vfs.target.vfs.energy")
    assert value == 0.8

def test_item_ref_traversal():
    """Test traversing item reference to read VFS variable."""
    # Agent 0 holds item 5 (vfs:held_item = 5)
    # Item 5 has vfs:quality = 0.9
    context = create_context(agent_idx=0)

    value = context.get("vfs.held_item.vfs.quality")
    assert value == 0.9

def test_nested_reference_traversal():
    """Test nested reference traversal (reference to reference)."""
    # Agent 0 has vfs:friend = 1 (references agent 1)
    # Agent 1 has vfs:held_item = 10 (references item 10)
    # Item 10 has vfs:quality = 0.7
    context = create_context(agent_idx=0)

    value = context.get("vfs.friend.vfs.held_item.vfs.quality")
    assert value == 0.7

def test_invalid_reference_value():
    """Test error handling for invalid reference (out of bounds)."""
    # Agent 0 has vfs:target = 999 (invalid agent index)
    context = create_context(agent_idx=0)

    with pytest.raises(ValueError) as exc_info:
        context.get("vfs.target.vfs.energy")

    assert "Invalid agent reference: 999" in str(exc_info.value)

def test_reference_type_checking():
    """Test type checker validates reference traversal."""
    expr = "vfs:target.vfs.energy"  # target is agent_ref
    ast = parse_expression(expr)

    type_checker = TypeChecker(vfs_profiles)
    result_type = type_checker.check(ast)
    assert result_type == "float"  # energy is float

def test_invalid_reference_traversal_rejected():
    """Test type checker rejects invalid reference paths."""
    expr = "vfs:target.invalid_segment"  # After reference, must be .vfs or .bar
    ast = parse_expression(expr)

    type_checker = TypeChecker(vfs_profiles)
    with pytest.raises(TypeError):
        type_checker.check(ast)
```

## Acceptance Criteria

- [ ] ExecutionContext.get() resolves agent_ref paths (vfs:target.vfs.energy)
- [ ] ExecutionContext.get() resolves item_ref paths (vfs:held_item.vfs.quality)
- [ ] Nested reference traversal works (vfs:friend.vfs.held_item.vfs.quality)
- [ ] Invalid references (out of bounds) raise clear errors
- [ ] Type checker validates reference traversal syntax (requires COMP-9)
- [ ] Reference validation ensures indices are valid
- [ ] 20+ tests covering reference traversal, validation, and edge cases
- [ ] Documentation updated with reference type examples

## Evidence

**Source Report:** gap-report-final.md (lines 71-94), gap-report-vfs.md
**Schema:** `src/townlet/vfs/schema.py:VariableType` (agent_ref, item_ref declared)
**Current limitation:** No runtime resolution in ExecutionContext or VFSEvaluator

## Implementation Notes

**Why P2 (not P1/P0):** Reference types are advanced feature for complex inter-agent interactions and item relationships. Phase 1-3 curriculum levels don't require reference traversal. Needed for Phase 4+ (social dynamics, item trading, collaborative tasks).

**Design Decisions:**

1. **Reference Storage:**
   - References stored as integer indices (agent index, item index)
   - Indices are 0-based, match VFS registry internal indexing
   - Invalid indices (negative, out of bounds) caught at validation time

2. **Traversal Syntax:**
   - `vfs:target.vfs.energy` - traverse agent reference, read VFS variable
   - `vfs:target.bar.health` - traverse agent reference, read bar value
   - `vfs:held_item.vfs.quality` - traverse item reference, read VFS variable
   - Nested: `vfs:friend.vfs.held_item.vfs.quality` - chain multiple references

3. **Type Checking:**
   - Type checker validates reference paths when AST exists (COMP-9)
   - For now: Runtime validation only (check indices valid)
   - Future: Compile-time validation (check paths are well-typed)

**Performance Considerations:**
- Reference traversal adds lookup overhead (2-3 registry lookups vs 1)
- Cache resolved paths to avoid repeated lookups
- Use GPU-native indexing (avoid CPU-GPU transfers)

**Use Case Examples:**

**Social Interaction:**
```yaml
# Agent wants to give gift to friend
effects:
  give_gift:
    commands:
      - type: "modify"
        target: "self"
        path: "vfs.friend.vfs.happiness"  # Increase friend's happiness
        operation: "add"
        value: 0.2
```

**Conditional Item Use:**
```yaml
# Only use item if quality is high
effects:
  use_item:
    commands:
      - type: "if"
        condition: "vfs:held_item.vfs.quality > 0.8"
        then:
          - type: "modify"
            target: "self"
            path: "bar.health"
            operation: "add"
            value: 0.5
```

**Target-Based Combat:**
```yaml
# Damage based on target's defense
effects:
  attack:
    commands:
      - type: "modify"
        target: "target"
        path: "bar.health"
        operation: "subtract"
        value: "max(0, vfs:self.vfs.attack_power - vfs:target.vfs.defense)"
```

**Edge Cases:**
- Self-reference: `vfs:self.vfs.energy` (redundant but valid)
- Null reference: Variable has no reference set (default value or None)
- Circular references: A → B → A (infinite loop, needs cycle detection)
- Reference to destroyed entity (item despawned, agent died)

**Error Handling:**
- Out-of-bounds reference: Clear error with valid range
- Reference to wrong type: "agent_ref used where item_ref expected"
- Uninitialized reference: "Reference not set" (default to None or error?)

## References

- Schema: `src/townlet/vfs/schema.py:VariableType` (agent_ref, item_ref)
- Context: `src/townlet/effects/context.py:get()` (add reference resolution)
- Type checker: `src/townlet/world/expression/type_checker.py` (validate reference paths, depends on COMP-9)
- Test file: `tests/test_townlet/unit/vfs/test_reference_types.py` (to be created)
- Documentation: `docs/config-schemas/variables.md` (add reference type examples)
- Related: COMP-9 (type checker), VFS path resolution design
