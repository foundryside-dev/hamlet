# Gap Report 09: Policy & Documentation Requirements

**Agent**: Agent 9 - Policy & Documentation Gap Analysis
**Date**: 2025-11-23
**Scope**: BREAK-REQ-001..002, POLICY-REQ-001..002, LIMIT-REQ-001, DOC-REQ-001..008

---

## Executive Summary

**Total Requirements**: 12
**DONE**: 8
**PARTIAL**: 3
**MISSING**: 1
**N/A**: 0

**Critical Findings**:
- ✅ Breaking change policies are well-enforced with compiler validation
- ✅ No-defaults principle enforced via Pydantic `extra="forbid"` across all DTOs
- ⚠️ Documentation gaps exist for observation modes guide and interaction radius guide
- ⚠️ Resource count limits partially implemented (max_items enforced, but no profile count limits)

---

## Breaking Change Requirements

### BREAK-REQ-001: Ban level-scoped VFS/effects
**Status**: ✅ **DONE**
**Evidence**:
- **Compiler Enforcement**: `src/townlet/universe/compiler.py:510` explicitly forbids `vfs_profiles.yaml` and `effects.yaml` at level scope
- **Error Code**: `SCOPING_FORBIDDEN_LEVEL_FILE` raised when detected
- **Test Coverage**: `tests/test_townlet/unit/universe/test_scoping_enforcement.py::test_level_scoped_shared_files_rejected`
- **File Scan**: No level-scoped VFS/effects files found in `/home/john/hamlet/configs/*/levels/*`

**Code Reference**:
```python
# src/townlet/universe/compiler.py:510
forbidden_level_files = ["vfs_profiles.yaml", "effects.yaml"]
for forbidden in forbidden_level_files:
    forbidden_path = level_dir / forbidden
    if forbidden_path.exists():
        errors.add(
            f"Found {forbidden} at level scope ({forbidden_path}). "
            "This file must live at the experiment root only.",
            code="SCOPING_FORBIDDEN_LEVEL_FILE",
            location=str(forbidden_path),
        )
```

**Recommendations**: None. Requirement fully implemented.

---

### BREAK-REQ-002: No backward-compat paths
**Status**: ✅ **DONE**
**Evidence**:
- **Pydantic Enforcement**: All DTOs use `model_config = ConfigDict(extra="forbid")` to reject unknown fields
- **No Legacy Adapters**: No `hasattr()` checks for old vs new attributes found in core modules
- **No Try/Except Fallbacks**: No silent fallback code paths for old config formats
- **Clean Breaking Changes**: VFS integration, DAC system, and Effects system all deleted old code paths

**Code References**:
```python
# src/townlet/config/items_config.py:27
model_config = ConfigDict(extra="forbid")  # Reject unknown fields

# Pattern applied across:
# - src/townlet/config/environment_config.py (11 instances)
# - src/townlet/config/cues.py (5 instances)
# - src/townlet/config/items_config.py
# - src/townlet/config/bars_v2_config.py
# - src/townlet/config/training_v2_config.py
# - src/townlet/config/affordances_v2_config.py
# - src/townlet/config/actions_config.py
# - All other config DTOs
```

**Antipattern Check**: Searched for backward-compat antipatterns:
- ❌ No `hasattr(obj, 'old_field')` checks found
- ❌ No `try/except` fallbacks for legacy configs found
- ❌ No version checks for "legacy support" found
- ❌ No "for backwards compatibility" comments found

**Recommendations**: None. Requirement fully implemented.

---

## Policy Requirements

### POLICY-REQ-001: No implicit defaults
**Status**: ✅ **DONE**
**Evidence**:
- **Pydantic Enforcement**: All behavioral fields marked with `Field(..., description=...)` (required) or explicit defaults
- **DTO Pattern**: `extra="forbid"` ensures no silent field additions
- **Compiler Validation**: Missing required fields cause validation errors at parse time
- **Documentation**: `docs/config-schemas/` files emphasize "no defaults" principle

**Code Examples**:
```python
# src/townlet/config/items_config.py:58-79
class ItemTypeConfig(BaseModel):
    id: str = Field(..., description="Unique item type identifier")
    vfs_profile: str = Field(..., description="VFS profile ID from vfs_profiles.yaml (item scope)")
    interactions: ItemInteractionsConfig = Field(..., description="Item interaction commands (pickup/use/drop)")
    duration: int | None = Field(default=None, description="Item lifetime in ticks (None = permanent)", ge=1)
    cooldown: int | None = Field(default=None, description="Ticks before item can spawn again after despawn", ge=0)
    description: str | None = Field(default=None, description="Human-readable description (metadata only)")
```

**Pattern Compliance**:
- Behavioral fields (`id`, `vfs_profile`, `interactions`): Required via `Field(...)`
- Optional metadata (`description`): Explicit `default=None`
- Range constraints (`ge=1`, `le=10`) specified explicitly
- No hidden defaults in constructors

**Exceptions (Appropriate)**:
- Metadata-only fields (`description`) can have `default=None`
- Computed values (e.g., `observation_dim`) calculated at compile time

**Recommendations**: None. Requirement fully implemented.

---

### POLICY-REQ-002: Breaking changes only
**Status**: ✅ **DONE**
**Evidence**:
- **Pre-Release Posture**: Project has zero users (per `CLAUDE.md:15`)
- **No Feature Flags**: No dual-path support for old/new systems found
- **Clean Replacements**: DAC replaced RewardStrategy, Effects replaced EffectPipeline, VFS profiles enforce experiment-level scoping
- **CLAUDE.md Policy**: Lines 15-74 explicitly mandate breaking changes without backward compatibility

**Breaking Changes Implemented**:
1. **VFS Integration**: Deleted old observation code, required `variables_reference.yaml` for all packs
2. **DAC System**: Removed `reward_strategy` field, deleted `reward_strategy.py` (583 lines), required `drive_as_code.yaml`
3. **Effects System**: Removed opaque effect dicts, required Effects catalog
4. **Scoping Enforcement**: Banned level-scoped `vfs_profiles.yaml` and `effects.yaml`

**Repository Guidelines** (`CLAUDE.md`):
```markdown
When you see:
- "Let's support the old way too" → NO. Delete it.
- "We should maintain backwards compatibility" → NO. We have zero users.
- "Let's add a fallback for old configs" → NO. Break them and update the templates.
- "What if someone was using the old API?" → They don't exist. Break it.
```

**Recommendations**: None. Policy correctly followed.

---

## Resource Limits

### LIMIT-REQ-001: Resource count limits
**Status**: ⚠️ **PARTIAL**
**Evidence**:

**Implemented Limits**:
```python
# src/townlet/universe/compiler.py:73-80
MAX_METERS = 100
MAX_AFFORDANCES = 100
MAX_CASCADES = 500
MAX_ACTIONS = 300
MAX_VARIABLES = 200
MAX_GRID_CELLS = 10000
MAX_CACHE_FILE_SIZE = 10 * 1024 * 1024  # 10MB
EFFECT_OBSERVATION_SLOTS = 8
```

```python
# src/townlet/config/items_config.py:114-126
max_items_per_agent: int = Field(default=3, description="Maximum items agent can carry", ge=1, le=10)
max_items_in_world: int = Field(default=10, description="Maximum items that can exist in world simultaneously", ge=1, le=1000)
```

**Missing Limits**:
- ❌ **No limit on item profile count**: `item_types: list[ItemTypeConfig]` has no length validation
- ❌ **No limit on VFS profile count**: No validation on number of profiles in `vfs_profiles.yaml`
- ❌ **No limit on spawn rule count**: No validation on number of spawn rules per item

**Gap Analysis**:
- **Item Profile Count**: Should add validator to `ItemsCatalogConfig.item_types` checking `len(v) <= MAX_ITEM_TYPES`
- **VFS Profile Count**: Should add validators to `VFSProfilesConfig` checking total profile count
- **Spawn Rule Count**: Should validate `ItemAppearanceRuleConfig` list length

**Recommendations**:
1. Add `MAX_ITEM_TYPES = 50` constant to `compiler.py`
2. Add `MAX_VFS_PROFILES = 100` constant to `compiler.py`
3. Add `MAX_SPAWN_RULES_PER_ITEM = 10` constant to `compiler.py`
4. Add field validators to respective config classes:
   ```python
   @field_validator("item_types")
   @classmethod
   def validate_count(cls, v: list[ItemTypeConfig]) -> list[ItemTypeConfig]:
       if len(v) > MAX_ITEM_TYPES:
           raise ValueError(f"Too many item types: {len(v)} > {MAX_ITEM_TYPES}")
       return v
   ```

---

## Documentation Requirements

### DOC-REQ-001: Reference docs update
**Status**: ✅ **DONE**
**Evidence**:
- **Items Schema**: `docs/config-schemas/items.md` (30,062 bytes, comprehensive)
- **VFS Profiles Schema**: `docs/config-schemas/vfs-profiles.md` (23,749 bytes, comprehensive)
- **Effects Schema**: `docs/config-schemas/effects.md` (50,417 bytes, comprehensive)
- **Expressions Schema**: `docs/config-schemas/expressions.md` (24,253 bytes, comprehensive)
- **No-Defaults Emphasis**: All schema docs emphasize explicit configuration requirements

**Schema Doc Quality**:
- ✅ AI-Friendly Frontmatter with purpose/summary/reading strategy
- ✅ Complete field reference sections
- ✅ Multiple complete examples (consumables, durables, collectibles)
- ✅ Integration guidance with other systems
- ✅ Validation rules and error messages documented

**Recommendations**: None. Documentation comprehensive and high-quality.

---

### DOC-REQ-002: Command DSL reference
**Status**: ✅ **DONE**
**Evidence**:
- **Command Reference**: `docs/plans/vfs_uplift/command_reference.md` exists
- **Comprehensive Coverage**: Documents all implemented commands (modify, spawn_effect, spawn_item, if, for_each, switch, parallel, reduce, delay)
- **Future Commands**: Documents `while` and `emit_event` as planned/future
- **Runtime Limits**: Includes limits section (for_each ≤256, delay ≤1000, scheduled ≤10000)

**Content Structure**:
```markdown
## Fully Implemented
- modify, spawn_effect, spawn_item, if, for_each

## Advanced Control Flow (Implemented)
- switch, parallel, reduce, delay

## Future/Planned
- while (documented but not implemented)
- emit_event (supported per design)
```

**Recommendations**:
- ✅ Reference exists and is comprehensive
- Consider moving from `docs/plans/vfs_uplift/` to `docs/config-schemas/commands.md` for better discoverability

---

### DOC-REQ-003: Observation modes guide
**Status**: ⚠️ **PARTIAL**
**Evidence**:

**Design Documentation Exists**:
- `docs/plans/vfs_uplift/2025-11-18-items-and-vfs-profiles.md:440-466` describes three observation modes:
  - `full_auto`: Automatic obs_dim calculation per level
  - `max_compact`: Single obs_dim across all levels (smallest possible)
  - `full_manual`: Manual obs_dim specification with validation

**Missing User-Facing Guide**:
- ❌ No standalone guide in `docs/config-schemas/` or `docs/guides/`
- ❌ No examples showing mode selection trade-offs
- ❌ No migration guide for switching between modes

**Content Needed**:
1. **Observation Modes Overview**: When to use each mode
2. **Trade-offs Table**: obs_dim stability vs size vs flexibility
3. **Configuration Examples**: How to specify mode in experiment config
4. **Selection Guide**: Decision tree for choosing appropriate mode
5. **Transfer Learning Impact**: How mode affects checkpoint transfer

**Recommendations**:
- Create `docs/guides/observation-modes-guide.md` with:
  - Mode comparison table
  - Use case recommendations
  - Configuration examples
  - Checkpoint transfer implications

---

### DOC-REQ-004: Edge case policies
**Status**: ✅ **DONE**
**Evidence**:
- **DENY_PICKUP Policy**: `docs/config-schemas/items.md:638-646` documents full inventory behavior
- **Test References**: `docs/config-schemas/items.md:1019` references DENY_PICKUP tests
- **Behavior Specification**: Clear description of pickup failure semantics

**Documentation Content**:
```markdown
### DENY_PICKUP Policy

When inventory full, GET action fails:
- No pickup
- No `on_pickup` Effects execute
- Item remains on ground

**Pedagogical Value**: Teaches inventory management, opportunity cost
```

**Coverage**:
- ✅ DENY_PICKUP policy fully documented
- ✅ Test references included
- ✅ Pedagogical rationale explained
- ✅ Failure semantics clearly specified

**Recommendations**: None. Requirement fully satisfied.

---

### DOC-REQ-005: Interaction radius guide
**Status**: ❌ **MISSING**
**Evidence**:

**Mentioned in Design Docs**:
- `docs/plans/vfs_uplift/2025-11-18-items-and-vfs-profiles.md:388` mentions `interaction_radius` for continuous substrates
- Compiler validation exists: `COMP-REQ-008` requires explicit `interaction_radius` for continuous substrates

**Missing User-Facing Documentation**:
- ❌ No dedicated guide for `interaction_radius` parameter
- ❌ No examples showing configuration for continuous substrates
- ❌ No validation rules documented for users
- ❌ Not covered in `docs/config-schemas/` files

**Content Needed**:
1. **Parameter Purpose**: Why `interaction_radius` is required for continuous substrates
2. **Configuration Examples**: How to specify in `substrate.yaml`
3. **Validation Rules**: Compiler rejects continuous substrates without explicit value
4. **Design Rationale**: Why no implicit defaults (prevents non-reproducible configs)
5. **Typical Values**: Common interaction radii for different game mechanics

**Recommendations**:
- Add section to `docs/config-schemas/substrate.yaml` (if exists) or create `docs/guides/interaction-radius-guide.md`
- Include examples:
  ```yaml
  # Example: Continuous2D with item interactions
  substrate:
    type: continuous
    continuous:
      dimensions: 2
      bounds: [[0.0, 10.0], [0.0, 10.0]]
      interaction_radius: 0.5  # REQUIRED for item pickup/affordance use
  ```

---

### DOC-REQ-006: Type system reference
**Status**: ✅ **DONE**
**Evidence**:
- **Type System Documentation**: `docs/config-schemas/expressions.md:337-423` comprehensive type reference
- **Primitive Types**: `int`, `float`, `bool`, `str` fully documented
- **Type Inference**: Bottom-up inference rules explained
- **Type Promotion**: Automatic numeric promotion rules documented
- **Type Errors**: Error messages and examples provided

**Coverage**:
```markdown
## Type System Reference
### Primitive Types
- int, float, bool, str

### Type Inference
- Constants: Inferred from Python type
- Variables/Paths: Looked up in schema
- Operators: Type-specific rules
- Functions: Signature lookup (Phase 2)

### Type Promotion
int + int → int
int + float → float
float + float → float

### Type Checking Rules
- Arithmetic operators (+, -, *, /, %, **)
- Comparison operators (==, !=, <, >, <=, >=)
- Logical operators (and, or, not)
- Conditional expressions (if-then-else)
```

**Missing (Future Phase)**:
- ⚠️ Reference types (`agent_ref`, `item_ref`, `affordance_ref`, `effect_ref`) mentioned in plans but not yet in user docs
- ⚠️ Tensor types (`tensor1d..tensorNd`) mentioned in design but not yet implemented

**Recommendations**:
- Current documentation adequate for implemented features
- Update when reference types and tensor types are implemented

---

### DOC-REQ-007: Reapply policy examples
**Status**: ✅ **DONE**
**Evidence**:
- **Comprehensive Examples**: `docs/config-schemas/effects.md:280-403` documents all four policies
- **Timeline Examples**: Each policy includes tick-by-tick execution timeline
- **Use Cases**: Practical use cases for each policy
- **Performance Notes**: O(n) vs O(1) characteristics documented

**Coverage**:
```markdown
##### stack - Create Independent Instances
- Timeline example (Tick 1, Tick 3, independent expiry)
- Use cases: food digestion, DOT stacking, buff stacking
- Performance: O(num_instances)

##### renew - Refresh Duration
- Timeline example (Tick 1, Tick 15, extended expiry)
- Use cases: "well fed" status, regeneration buffs
- Performance: O(1)

##### merge - Increase Intensity
- Timeline example (intensity accumulation)
- Use cases: cumulative drug dosage, poison stacking
- Performance: O(1)
- Best practice: Use intensity in expressions

##### replace - Clear Old, Spawn New
- Timeline example (despawn + spawn)
- Use cases: status replacement, buff refresh
- Performance: O(1)
```

**Recommendations**: None. Excellent comprehensive documentation.

---

### DOC-REQ-008: Expression context reference
**Status**: ⚠️ **PARTIAL**
**Evidence**:

**Partial Documentation Exists**:
- `docs/config-schemas/expressions.md:74-94` documents path namespaces:
  - `bar.*` - Meter values
  - `vfs.*` - VFS variables
  - `temporal.*` - Time-based values
  - `target.*` - Target entity in effects
  - `self.*` - Current entity
  - `item.*` - Item-local state

**Missing Context Variables**:
- ❌ `intensity` - Not explicitly listed as available context variable
- ❌ `duration` - Not explicitly listed
- ❌ `duration_remaining` - Not explicitly listed
- ❌ `elapsed_ticks` - Not explicitly listed
- ❌ `time_of_day` - Not explicitly listed
- ❌ `step_count` - Not explicitly listed

**Partial Evidence**:
- `docs/config-schemas/expressions.md:620` mentions `['intensity', 'duration', 'slot_index']` in error message example
- Context variables used in examples but not formally documented

**Gap Analysis**:
- Design docs (`2025-11-19-effects-system-design.md §5.1`) specify these variables
- User-facing expression reference doesn't explicitly list them in a "Context Variables" section
- Variables scattered across examples but no consolidated reference table

**Recommendations**:
- Add "Context Variables" section to `docs/config-schemas/expressions.md`:
  ```markdown
  ## Context Variables

  Context variables are automatically available in expressions based on evaluation scope:

  ### Effect Context
  - `intensity` (float): Effect intensity multiplier
  - `duration` (int): Total effect duration in ticks
  - `duration_remaining` (int): Ticks until effect despawns
  - `elapsed_ticks` (int): Ticks since effect spawned

  ### Temporal Context
  - `time_of_day` (float): Current time in 24-hour format [0.0, 24.0)
  - `step_count` (int): Total simulation steps elapsed
  - `temporal.tick` (int): Current tick number

  ### Item Context
  - `slot_index` (int): Inventory slot number (USE_SLOT_N actions)
  ```

---

## Summary Table

| Requirement | Title | Status | Evidence | Gaps |
|-------------|-------|--------|----------|------|
| BREAK-REQ-001 | Ban level-scoped VFS/effects | ✅ DONE | Compiler enforcement + tests | None |
| BREAK-REQ-002 | No backward-compat paths | ✅ DONE | Pydantic `extra="forbid"` everywhere | None |
| POLICY-REQ-001 | No implicit defaults | ✅ DONE | Required fields + explicit defaults | None |
| POLICY-REQ-002 | Breaking changes only | ✅ DONE | Clean replacements, no dual paths | None |
| LIMIT-REQ-001 | Resource count limits | ⚠️ PARTIAL | max_items enforced | No profile/spawn count limits |
| DOC-REQ-001 | Reference docs update | ✅ DONE | Comprehensive schema docs | None |
| DOC-REQ-002 | Command DSL reference | ✅ DONE | `command_reference.md` exists | Consider moving to config-schemas/ |
| DOC-REQ-003 | Observation modes guide | ⚠️ PARTIAL | Design docs only | No user-facing guide |
| DOC-REQ-004 | Edge case policies | ✅ DONE | DENY_PICKUP documented | None |
| DOC-REQ-005 | Interaction radius guide | ❌ MISSING | Design mention only | No user documentation |
| DOC-REQ-006 | Type system reference | ✅ DONE | Comprehensive primitives | Future: references/tensors |
| DOC-REQ-007 | Reapply policy examples | ✅ DONE | All 4 policies with timelines | None |
| DOC-REQ-008 | Expression context reference | ⚠️ PARTIAL | Paths documented | Context vars not consolidated |

---

## Priority Recommendations

### High Priority (Blocking for Production)

1. **LIMIT-REQ-001**: Add profile/spawn count limits
   - Add `MAX_ITEM_TYPES = 50`, `MAX_VFS_PROFILES = 100`, `MAX_SPAWN_RULES_PER_ITEM = 10`
   - Add field validators to config classes
   - Prevents DoS via config bomb attacks

2. **DOC-REQ-005**: Create interaction radius guide
   - Critical for continuous substrate users
   - Required parameter needs user-facing documentation
   - Include validation rules and examples

### Medium Priority (Quality Improvement)

3. **DOC-REQ-003**: Create observation modes guide
   - Important for advanced users doing transfer learning
   - Design is complete, just needs user-facing guide
   - Create `docs/guides/observation-modes-guide.md`

4. **DOC-REQ-008**: Consolidate expression context reference
   - Add "Context Variables" section to expressions.md
   - List all automatically-available variables
   - Improves discoverability for effect authors

### Low Priority (Nice to Have)

5. **DOC-REQ-002**: Move command reference to config-schemas
   - Consider moving `command_reference.md` from `docs/plans/vfs_uplift/` to `docs/config-schemas/commands.md`
   - Improves discoverability for users
   - Currently functional but non-obvious location

---

## Testing Gaps

### Policy Enforcement Tests Needed

1. **Resource Limits**:
   - Test item profile count exceeding limit
   - Test VFS profile count exceeding limit
   - Test spawn rule count exceeding limit

2. **No-Defaults Validation**:
   - Existing tests adequate (Pydantic validation)
   - No additional tests needed

3. **Breaking Changes**:
   - Existing `test_scoping_enforcement.py` adequate
   - No additional tests needed

---

## Conclusion

**Overall Assessment**: Policy requirements are **well-implemented** with strong compiler enforcement and Pydantic validation. Documentation requirements are **mostly complete** with 3 partial gaps and 1 missing guide.

**Strengths**:
- Excellent breaking change enforcement
- Comprehensive no-defaults principle via Pydantic
- High-quality schema documentation with examples
- Strong test coverage for scoping policies

**Weaknesses**:
- Missing resource count limits for profiles/spawn rules
- Observation modes guide missing user-facing documentation
- Interaction radius guide completely absent
- Expression context variables not consolidated in reference

**Risk Assessment**:
- **Low Risk**: Policy enforcement is solid (BREAK/POLICY requirements)
- **Medium Risk**: Resource limits gap could allow config bombs (LIMIT-REQ-001)
- **Low Risk**: Documentation gaps are quality issues, not functional blockers

**Recommended Action**: Address High Priority items (LIMIT-REQ-001, DOC-REQ-005) before release. Medium/Low priority items can be addressed in subsequent iterations.
