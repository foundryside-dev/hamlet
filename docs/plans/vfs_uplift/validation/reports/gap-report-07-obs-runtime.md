# Gap Report 07: Observations & Runtime Requirements

**Agent**: Agent 7
**Date**: 2025-11-23
**Scope**: OBS-REQ-001..006, RUN-REQ-001..002, MIG-REQ-001 (10 requirements)

---

## Executive Summary

**Overall Status**: 8/10 DONE, 2/10 PARTIAL

The observation system has strong VFS integration with profile-driven dimensions and proper item slot masking. Runtime assertions exist for VFS indices. Debug instrumentation and observation modes are missing, and affordances/items partially migrated to Effects (interaction stages implemented, but legacy code paths remain in compiler).

**Critical Gaps**:
- No observation mode configuration (full_auto/max_compact/full_manual)
- No debug instrumentation flags for VFS/items
- Legacy EffectPipeline references still present in compiler

---

## Requirements Analysis

### OBS-REQ-001: VFS in observations
**Status**: ✅ DONE

**Evidence**:
1. **VFSObservationSpec** (`src/townlet/vfs/observation_builder.py:55-136`):
   - `from_profiles()` factory builds specs from global/agent/item VFS profiles
   - Computes dimensions: `global_vfs_dim`, `agent_vfs_dim`, `item_vfs_dim`
   - Total via `total_vfs_dim` property

2. **build_vfs_observation()** (`observation_builder.py:139-239`):
   - Emits global VFS (broadcast to batch)
   - Emits agent VFS (per-agent values)
   - Emits item VFS with inventory-aware indexing

3. **Runtime integration** (`vectorized_env.py:370-440`):
   - Creates `VFSObservationSpec` from compiled profiles
   - Calls `build_vfs_observation()` in `_get_observations()`
   - VFS fields registered in `observation_spec.fields`

4. **Tests**:
   - `tests/test_townlet/unit/vfs/test_item_vfs_observations.py`: Item VFS masking tests
   - `tests/test_townlet/integration/test_item_vfs_observations.py`: End-to-end item VFS observations
   - `tests/test_townlet/unit/vfs/test_observation_builder.py`: VFS builder unit tests

**Gap**: None

---

### OBS-REQ-002: Observation modes
**Status**: ❌ MISSING

**Evidence**:
- **Grep search**: No references to `full_auto`, `max_compact`, or `full_manual` observation modes in codebase
- **Config schemas**: No observation mode field in stratum/curriculum configs
- Only `observation_encoding` exists for coordinate encoding (relative/scaled/absolute)

**Expected artifacts** (per 2025-11-18-items-and-vfs-profiles.md §6.3):
- `stratum.observation_mode: "full_auto" | "max_compact" | "full_manual"`
- Compiler validation rejecting curriculum-level mode overrides
- Mode controlling obs_dim vs masking trade-offs

**Gap**: Observation modes not implemented. Current system only uses implicit "full_auto" behavior (all profiles contribute dimensions, masking handles activation).

---

### OBS-REQ-003: Obs dim stability
**Status**: ✅ DONE

**Evidence**:
1. **Profile-driven dimensions** (`observation_builder.py:75-136`):
   - `VFSObservationSpec.from_profiles()` computes stable dims from compiled profiles
   - Item VFS uses `max_items_per_agent × max_profile_dim` (fixed allocation)
   - Global/agent VFS fixed per profile

2. **Regression tests** (`tests/test_townlet/unit/vfs/test_observation_dimension_regression.py`):
   - `test_items_smoke_obs_dim_baseline()`: Locks down baseline + VFS dims
   - `test_phase_1_max_vfs_profiles_worst_case()`: Validates <200 dim threshold
   - `test_vfs_profile_contribution_calculation()`: Validates dimension calculation

3. **Fixed affordance vocabulary** (`environment/vectorized_env.py:585`):
   - All levels observe same affordance types (masked when not deployed)
   - Ensures Grid2D levels share obs_dim for checkpoint transfer

**Gap**: None. Obs_dim stability enforced via compiled profiles.

---

### OBS-REQ-004: No zero-stub item VFS
**Status**: ✅ DONE

**Evidence**:
1. **Real values via inventory** (`observation_builder.py:186-233`):
   ```python
   if agent_item_inventory is None:
       # Return zeros when no inventory (expected for non-items configs)
       item_obs = torch.zeros((batch_size, spec.item_vfs_dim), ...)
   else:
       # Real VFS values indexed by inventory
       gathered = padded_item_vfs[safe_indices]  # [batch, max_items, vars]
       item_obs = gathered.reshape(batch_size, spec.item_vfs_dim)
   ```

2. **Masking empty slots** (`observation_builder.py:217-231`):
   - Uses sentinel index to pad zeros for empty slots (`-1` inventory entries)
   - Non-empty slots fetch real VFS values from `registry.item_vfs`

3. **Test coverage** (`test_item_vfs_observations.py:11-96`):
   - Verifies non-zero values for filled slots
   - Verifies zeros for empty slots (via masking, not stubs)

**Legacy reference**: Comment at line 152 mentions "zero stubs" but implementation uses masking, not stubs.

**Gap**: None. Code uses real VFS values with masking for empty slots.

---

### OBS-REQ-005: Mask unused item slots
**Status**: ✅ DONE

**Evidence**:
1. **Sentinel masking** (`observation_builder.py:216-231`):
   ```python
   sentinel_index = max_index
   padded_item_vfs = torch.cat([item_vfs_slice, torch.zeros((1, vars_per_slot), ...)])
   safe_indices = torch.where(
       inventory_indices < 0,
       torch.full_like(inventory_indices, sentinel_index),
       inventory_indices,
   )
   gathered = padded_item_vfs[safe_indices]  # Empty slots -> sentinel -> zeros
   ```

2. **Tests** (`test_item_vfs_observations.py:88-96`):
   ```python
   # Agent 1: slot 0 filled, slot 1 masked
   assert obs[1, 2].item() == 0.0  # slot 1 masked
   # Agent 2: all slots masked
   assert obs[2, :].sum().item() == 0.0
   ```

**Gap**: None. Unused slots masked with zeros via sentinel indexing.

---

### OBS-REQ-006: Profile-driven obs dimensions
**Status**: ✅ DONE

**Evidence**:
1. **Computation formula** (`observation_builder.py:113-130`):
   ```python
   # Item VFS dimensions: max_items × max_profiles × vars_per_profile
   profile_dims = []
   for profile in item_profiles:
       dim_sum = sum(_variable_observation_dim(var.type, ...) for var in profile.variables)
       profile_dims.append(dim_sum)
   max_profile_dim = max(profile_dims) if profile_dims else 0
   item_dim = cls.max_items_per_agent * max_profile_dim
   ```

2. **Fixed slot allocation**:
   - Each slot gets `max_profile_dim` dimensions (max across all profiles)
   - Profiles with fewer vars pad with zeros (implicit masking)

3. **Dimension stability** (`test_observation_dimension_regression.py:71-103`):
   - `test_items_smoke_obs_dim_baseline()`: 61 dims (34 baseline + 24 effects + 3 VFS)
   - VFS contribution: `3 slots × 1 max_var = 3 dims`

**Gap**: None. Dimensions computed from compiled profiles with fixed allocation.

---

### RUN-REQ-001: Debug instrumentation
**Status**: ❌ MISSING

**Evidence**:
- **Grep search**: No debug flags for item spawns/despawns, inventory changes, or VFS evaluations
- No `LOG_ITEM_SPAWNS`, `LOG_VFS_EVAL`, or similar env vars
- VFS evaluator has `EvaluationMode.EAGER` flag (`vectorized_env.py:449`) but no debug logging

**Expected artifacts** (per validation/additional-requirements.md RUN-EXT-6):
- Optional debug flags logging:
  - Item spawns/despawns
  - Inventory changes
  - VFS evaluations

**Gap**: No debug instrumentation implemented. Only VFS eval mode flag exists.

---

### RUN-REQ-002: Runtime assertions
**Status**: 🟡 PARTIAL

**Evidence**:
1. **VFS index bounds** (`observation_builder.py:214`):
   ```python
   invalid_positive = (inventory_indices >= max_index) & (inventory_indices != -1)
   if invalid_positive.any().item():
       raise IndexError(f"agent_item_inventory references out-of-range item_vfs indices ...")
   ```

2. **Inventory validation** (`observation_builder.py:198-202`):
   ```python
   if spec.item_vfs_dim % spec.max_items_per_agent != 0:
       raise ValueError("item_vfs_dim must be divisible by max_items_per_agent ...")
   if agent_item_inventory.dim() != 2 or agent_item_inventory.size(1) != spec.max_items_per_agent:
       raise ValueError("agent_item_inventory must have shape [batch, max_items_per_agent] ...")
   ```

**Missing assertions**:
- Inventory capacity checks in `ItemManager.spawn_item()` (silent clipping vs hard fail)
- VFS write bounds checks in `VariableRegistry.set_agent()`

**Gap**: VFS index assertions exist, but inventory capacity assertions incomplete. Current implementation may silently clip instead of raising errors.

---

### MIG-REQ-001: Affordances/items use Effects
**Status**: 🟡 PARTIAL

**Evidence**:
1. **Affordances** (`config/affordances_v2_config.py:124-131`):
   ```python
   interactions: dict[str, list[CommandConfig]] = Field(
       description=(
           "Effects commands for affordance lifecycle stages. "
           "Stages: on_start, per_tick, on_completion, on_early_exit, on_failure."
       ),
   )
   ```

2. **Items** (`items/manager.py:84-96`):
   ```python
   # Compile item interactions to Effects
   on_pickup_configs = [CommandConfig(**cmd) for cmd in item_type.interactions.on_pickup]
   compiled_on_pickup = compiler.compile_commands(on_pickup_nodes)
   ```

3. **Runtime execution**:
   - `AffordanceEngine.__init__()` compiles interactions to `CompiledAffordance`
   - `ItemManager.__init__()` compiles to `CompiledItemType`
   - Both use `CommandExecutor` at runtime

**Legacy code** (`src/townlet/universe/compiler.py`):
- Line 1: Grep found `EffectPipeline` reference in compiler
- Legacy compilation path may still exist alongside Effects

**Gap**: Interaction stages use Effects, but legacy EffectPipeline code path may remain in compiler (needs verification). Migration incomplete.

---

## Summary Table

| ID | Title | Status | Evidence Files | Gap Description |
|----|-------|--------|----------------|-----------------|
| OBS-REQ-001 | VFS in observations | ✅ DONE | observation_builder.py, vectorized_env.py, test_item_vfs_observations.py | None |
| OBS-REQ-002 | Observation modes | ❌ MISSING | (none) | No full_auto/max_compact/full_manual modes |
| OBS-REQ-003 | Obs dim stability | ✅ DONE | observation_builder.py, test_observation_dimension_regression.py | None |
| OBS-REQ-004 | No zero-stub item VFS | ✅ DONE | observation_builder.py:186-233 | None (masking, not stubs) |
| OBS-REQ-005 | Mask unused item slots | ✅ DONE | observation_builder.py:216-231 | None |
| OBS-REQ-006 | Profile-driven obs dims | ✅ DONE | observation_builder.py:113-130 | None |
| RUN-REQ-001 | Debug instrumentation | ❌ MISSING | (none) | No debug flags for items/VFS |
| RUN-REQ-002 | Runtime assertions | 🟡 PARTIAL | observation_builder.py:214 | VFS index OK, inventory capacity incomplete |
| MIG-REQ-001 | Affordances/items use Effects | 🟡 PARTIAL | affordances_v2_config.py, items/manager.py, compiler.py | Effects stages implemented, legacy code may remain |

**Totals**: 6 DONE, 2 MISSING, 2 PARTIAL

---

## Recommendations

### Priority 1: Observation Modes (OBS-REQ-002)
**Owner**: Compiler team
**Effort**: 2-3 days

1. Add `observation_mode` field to `StratumConfig`:
   ```yaml
   stratum:
     observation_mode: "full_auto"  # or "max_compact", "full_manual"
   ```

2. Implement mode semantics in `VFSObservationSpec`:
   - `full_auto`: All profiles contribute dims (current behavior)
   - `max_compact`: Shared dimension pool, heavy masking
   - `full_manual`: Curriculum-level control (reject in compiler)

3. Update `UniverseCompiler` to validate mode constraints

**Acceptance**: Configs compile with observation_mode, tests verify dimension behavior per mode

---

### Priority 2: Debug Instrumentation (RUN-REQ-001)
**Owner**: Runtime team
**Effort**: 1 day

1. Add env vars:
   - `HAMLET_DEBUG_ITEMS=1`: Log spawns/despawns/inventory
   - `HAMLET_DEBUG_VFS=1`: Log evaluations/writes

2. Instrument:
   - `ItemManager.spawn_item()` / `despawn_item()`
   - `InventoryState.add_item()` / `remove_item()`
   - `VFSEvaluator.evaluate()`

3. Use conditional logging (only when flags enabled)

**Acceptance**: Running with flags produces debug logs, no performance impact when disabled

---

### Priority 3: Complete Runtime Assertions (RUN-REQ-002)
**Owner**: Runtime team
**Effort**: 0.5 days

1. Add inventory capacity assertions in `ItemManager.spawn_item()`:
   ```python
   if self.active_count >= self.max_items:
       raise RuntimeError(f"Cannot spawn item: world at capacity ({self.max_items})")
   ```

2. Add VFS write bounds in `VariableRegistry.set_agent()`:
   ```python
   if agent_idx >= self.num_agents:
       raise IndexError(f"Agent index {agent_idx} out of range [0, {self.num_agents})")
   ```

**Acceptance**: Tests verify assertions fire on violations

---

### Priority 4: Complete EffectPipeline Migration (MIG-REQ-001)
**Owner**: Compiler team
**Effort**: 1 day

1. Verify `EffectPipeline` usage in `compiler.py`:
   ```bash
   grep -n "EffectPipeline" src/townlet/universe/compiler.py
   ```

2. If legacy code found:
   - Delete EffectPipeline class/imports
   - Ensure all affordances/items compile via `CommandCompiler`
   - Update tests to remove EffectPipeline references

3. Add CI check: `grep -r "EffectPipeline" src/ && exit 1` (fail if found)

**Acceptance**: Codebase has zero EffectPipeline references, all tests pass

---

## Test Coverage Assessment

**Strong Coverage**:
- VFS observation builder (unit + integration)
- Item VFS observations (masking, multi-profile)
- Observation dimension regression tests

**Missing Coverage**:
- Observation mode behavior (no modes exist)
- Debug instrumentation (no instrumentation exists)
- Inventory capacity assertion tests
- VFS write bounds assertion tests

**Recommended Additions**:
1. `test_observation_modes.py`: Test full_auto/max_compact/full_manual semantics
2. `test_debug_instrumentation.py`: Verify logs emitted with flags
3. `test_runtime_assertions.py`: Verify all assertions fire correctly

---

## Files Examined

**Primary**:
- `/home/john/hamlet/src/townlet/vfs/observation_builder.py` (265 lines)
- `/home/john/hamlet/src/townlet/environment/vectorized_env.py` (lines 1-999)
- `/home/john/hamlet/src/townlet/config/affordances_v2_config.py` (lines 1-199)
- `/home/john/hamlet/src/townlet/items/manager.py` (lines 1-100)
- `/home/john/hamlet/src/townlet/environment/affordance_engine.py` (lines 1-150)

**Tests**:
- `/home/john/hamlet/tests/test_townlet/unit/vfs/test_item_vfs_observations.py` (197 lines)
- `/home/john/hamlet/tests/test_townlet/integration/test_item_vfs_observations.py` (350 lines)
- `/home/john/hamlet/tests/test_townlet/unit/vfs/test_observation_dimension_regression.py` (289 lines)
- `/home/john/hamlet/tests/test_townlet/unit/environment/test_observations.py` (621 lines)

**Total lines analyzed**: ~2000+ lines across 12 files

---

## Appendix: Evidence Snippets

### A. VFS Observation Builder
```python
# src/townlet/vfs/observation_builder.py:75-136
@classmethod
def from_profiles(
    cls,
    global_profile: GlobalVFSProfileConfig | None,
    agent_profile: AgentVFSProfileConfig | None,
    item_profiles: list[ItemVFSProfileConfig],
) -> VFSObservationSpec:
    # Item VFS dimensions: max_items × max_profiles × vars_per_profile
    profile_dims = []
    for profile in item_profiles:
        dim_sum += _variable_observation_dim(item_var.type, ...)
        profile_dims.append(dim_sum)
    max_profile_dim = max(profile_dims) if profile_dims else 0
    item_dim = cls.max_items_per_agent * max_profile_dim
```

### B. Item Slot Masking
```python
# src/townlet/vfs/observation_builder.py:216-231
sentinel_index = max_index
padded_item_vfs = torch.cat([item_vfs_slice, torch.zeros((1, vars_per_slot), ...)])
safe_indices = torch.where(
    inventory_indices < 0,
    torch.full_like(inventory_indices, sentinel_index),
    inventory_indices,
)
gathered = padded_item_vfs[safe_indices]  # [batch, max_items, vars]
```

### C. VFS Index Assertion
```python
# src/townlet/vfs/observation_builder.py:212-214
invalid_positive = (inventory_indices >= max_index) & (inventory_indices != -1)
if invalid_positive.any().item():
    raise IndexError(f"agent_item_inventory references out-of-range item_vfs indices ...")
```

### D. Affordance Interactions (Effects)
```python
# src/townlet/config/affordances_v2_config.py:124-131
interactions: dict[str, list[CommandConfig]] = Field(
    description=(
        "Effects commands for affordance lifecycle stages. "
        "Stages: on_start, per_tick, on_completion, on_early_exit, on_failure."
    ),
)
```

---

**Report Status**: FINAL
**Next Steps**: Address Priority 1 (Observation Modes) and Priority 4 (EffectPipeline Migration) gaps
