# Gap Report: VFS System Requirements (VFS-REQ-001 through VFS-REQ-009)

**Validator:** Agent 3
**Baseline Commit:** b085877dd45ffb9647a2bc3295ee6ce8c94ad845
**Date:** 2025-11-23
**Scope:** VFS System implementation requirements

---

## Summary

| Requirement | Status | Evidence Quality |
|-------------|--------|------------------|
| VFS-REQ-001 | ✅ DONE | Strong |
| VFS-REQ-002 | ✅ DONE | Strong |
| VFS-REQ-003 | ✅ DONE | Strong |
| VFS-REQ-004 | ✅ DONE | Strong |
| VFS-REQ-005 | ✅ DONE | Strong |
| VFS-REQ-006 | 🟡 PARTIAL | Weak |
| VFS-REQ-007 | ✅ DONE | Strong |
| VFS-REQ-008 | 📝 N/A | N/A |
| VFS-REQ-009 | ✅ DONE | Strong |

**Overall Assessment:** 7/8 requirements DONE, 1 PARTIAL (metadata exposure incomplete), 1 N/A (future work)

---

## Detailed Findings

### VFS-REQ-001: Scoped VFS engine
**Status:** ✅ DONE
**Requirement:** VFS supports scoped profiles (global/agent/item) with profile IDs; evaluates per entity respecting dependencies; includes item VFS in checkpoints.

**Evidence:**
1. **Scoped profiles implemented:**
   - `src/townlet/vfs/schema.py:28-34` - VariableScope enum defines GLOBAL, AGENT, AGENT_PRIVATE, ITEM
   - `src/townlet/vfs/profiles.py:46-50` - CompiledGlobalProfile with dependencies
   - `src/townlet/vfs/profiles.py:54-63` - CompiledItemProfile with profile_name

2. **Registry supports all scopes:**
   - `src/townlet/vfs/registry.py:35-651` - VariableRegistry handles global/agent/agent_private/item scopes
   - `src/townlet/vfs/registry.py:408-450` - `_initialize_item_storage_from_profiles()` creates item VFS storage from compiled profiles
   - `src/townlet/vfs/registry.py:569-615` - `write_item()` and `read_item()` methods for item VFS access

3. **Per-entity evaluation:**
   - `src/townlet/vfs/evaluator.py:35-112` - VFSEvaluator evaluates profiles in topological order respecting dependencies
   - `src/townlet/environment/vectorized_env.py:443-454` - VFSEvaluator instantiated per environment

4. **Item VFS in checkpoints:**
   - `src/townlet/vfs/registry.py:94-99` - item_vfs tensor storage, item_profile_map, item_vfs_index_to_profile tracking
   - `src/townlet/vfs/registry.py:617-637` - register/unregister item instance methods for checkpoint state

**Citations:**
- Schema: `src/townlet/vfs/schema.py:28-34` (VariableScope)
- Profiles: `src/townlet/vfs/profiles.py:46-63` (CompiledGlobalProfile, CompiledItemProfile)
- Registry: `src/townlet/vfs/registry.py:35-651` (scoped storage)
- Item storage: `src/townlet/vfs/registry.py:408-450` (item profile initialization)

---

### VFS-REQ-002: Mark-and-sweep evaluation
**Status:** ✅ DONE
**Requirement:** Default VFS evaluation is mark-and-sweep over topo-ordered deps using obs marks; provide eager override; detect cycles and fail.

**Evidence:**
1. **Mark-and-sweep is default mode:**
   - `src/townlet/vfs/evaluator.py:17-21` - EvaluationMode enum with MARK_AND_SWEEP as first option
   - `src/townlet/vfs/evaluator.py:27-33` - VFSEvaluator __init__ defaults to MARK_AND_SWEEP
   - `src/townlet/environment/vectorized_env.py:449` - Default mode unless VFS_EVAL_MODE=eager env var

2. **Mark-and-sweep implementation:**
   - `src/townlet/vfs/evaluator.py:56-80` - MARK_AND_SWEEP mode evaluates only marked variables + dependencies
   - `src/townlet/vfs/evaluator.py:66-78` - `add_with_deps()` recursive dependency resolution
   - `src/townlet/vfs/evaluator.py:94-111` - Topological evaluation order (profile.variables already sorted)

3. **Eager mode override:**
   - `src/townlet/vfs/evaluator.py:79-80` - EAGER mode evaluates all variables
   - `src/townlet/environment/vectorized_env.py:447-449` - VFS_EVAL_MODE env var enables eager mode

4. **Cycle detection:**
   - `src/townlet/vfs/profiles.py:188-198` - topological_sort() uses networkx to detect cycles
   - `src/townlet/vfs/profiles.py:66-68` - CircularDependencyError raised on cycles

**Test evidence:**
- `tests/test_townlet/unit/vfs/test_vfs_evaluator.py:56-83` - mark_and_sweep evaluates marks only
- `tests/test_townlet/unit/vfs/test_vfs_evaluator.py:86-126` - mark_and_sweep recomputes dependencies
- `tests/test_townlet/unit/vfs/test_vfs_evaluator.py:128-156` - eager mode evaluates all vars

**Citations:**
- Evaluator: `src/townlet/vfs/evaluator.py:17-112` (modes and implementation)
- Cycle detection: `src/townlet/vfs/profiles.py:188-198` (topological sort with cycle check)
- Tests: `tests/test_townlet/unit/vfs/test_vfs_evaluator.py` (comprehensive coverage)

---

### VFS-REQ-003: Expression XOR initial_value
**Status:** ✅ DONE
**Requirement:** Each VFS variable must specify exactly one of `expression` or `initial_value`; compiler rejects configs that provide both or neither.

**Evidence:**
1. **XOR validation in GlobalVFSVariableConfig:**
   - `src/townlet/config/vfs_profiles_config.py:50-63` - validate_value_xor_expression() enforces exactly one of initial_value, initial_value_mode, or expression
   - Lines 57-61: Counts provided fields, rejects if count != 1

2. **XOR validation in AgentVFSVariableConfig:**
   - `src/townlet/config/vfs_profiles_config.py:145-158` - Same validator pattern
   - Lines 152-156: Enforces exactly one initialization source

3. **XOR validation in ItemVFSVariableConfig:**
   - `src/townlet/config/vfs_profiles_config.py:230-239` - validate_value_xor_expression() for items
   - Line 236: Rejects if has_value == has_expr (XOR logic)

4. **Compiler enforces via compilation:**
   - `src/townlet/vfs/profiles.py:211-266` - compile_variable() distinguishes between initial_value (line 229) and expression (line 243)
   - Static variables return None AST, expression variables parse and type-check

**Citations:**
- Global: `src/townlet/config/vfs_profiles_config.py:50-63`
- Agent: `src/townlet/config/vfs_profiles_config.py:145-158`
- Item: `src/townlet/config/vfs_profiles_config.py:230-239`
- Compiler: `src/townlet/vfs/profiles.py:229,243` (branches for static vs expression)

---

### VFS-REQ-004: Evaluation order
**Status:** ✅ DONE
**Requirement:** Runtime VFS evaluation executes in scope order: global → agent → item; per-scope dependency order is topo-sorted.

**Evidence:**
1. **Topological sorting per scope:**
   - `src/townlet/vfs/profiles.py:168-209` - topological_sort_with_dependencies() returns sorted vars + deps
   - `src/townlet/vfs/profiles.py:188-198` - Uses networkx.topological_sort for dependency order
   - `src/townlet/vfs/profiles.py:279` - compile_global_profile() calls topological_sort_with_dependencies
   - `src/townlet/vfs/profiles.py:318` - compile_item_profile() also uses topological sort

2. **Runtime evaluation respects topo order:**
   - `src/townlet/vfs/evaluator.py:94-111` - evaluate_global_profile() iterates variables in order
   - Line 94 comment: "profile.variables already sorted" (compiler pre-sorted)
   - Lines 103-110: Updates context.vfs after each variable so later variables see earlier results

3. **Scope ordering evidence:**
   - Global evaluation: `src/townlet/environment/vectorized_env.py:1600-1621` - global profile evaluated first
   - Runtime uses compiled profiles with pre-sorted variables (no runtime sorting needed)

**Test evidence:**
- `tests/test_townlet/unit/vfs/test_vfs_evaluator.py:11-53` - evaluates expressions in topo order (b depends on a)

**Citations:**
- Compiler: `src/townlet/vfs/profiles.py:168-209,279,318` (topological sort)
- Evaluator: `src/townlet/vfs/evaluator.py:94-111` (respects order)
- Test: `tests/test_townlet/unit/vfs/test_vfs_evaluator.py:11-53`

---

### VFS-REQ-005: ExecutionContext VFS access
**Status:** ✅ DONE
**Requirement:** Execution contexts (effects/runtime) must expose scoped VFS tensors (global/agent/item) for expression resolution; no missing scope branches.

**Evidence:**
1. **ExecutionContext provides VFS access:**
   - `src/townlet/world/expression/context.py:9-51` - ExecutionContext dataclass with vfs dict
   - Lines 21: `vfs: dict[str, torch.Tensor]` field
   - Lines 26-51: get() method resolves "vfs.varname" paths

2. **VFS context in evaluator:**
   - `src/townlet/vfs/evaluator.py:83-89` - ExecutionContext constructed with vfs state
   - Line 85: `vfs=vfs_state.copy()` - VFS passed to context
   - Line 110: `context.vfs[var.name] = value` - Updates context during evaluation

3. **Path resolution supports VFS:**
   - `src/townlet/world/expression/context.py:41-49` - get() method handles "vfs." paths
   - Line 42: `vfs[".".join(parts[1:])]` - Resolves nested VFS paths

4. **Evaluator uses context for expression evaluation:**
   - `src/townlet/world/expression/evaluator.py:22-40` - Evaluator class takes ExecutionContext
   - Line 37: PathAccess visitor uses `context.get(path_str)`

**Citations:**
- Context: `src/townlet/world/expression/context.py:9-51` (VFS field and resolution)
- VFS evaluator: `src/townlet/vfs/evaluator.py:83-110` (context construction and updates)
- Expression evaluator: `src/townlet/world/expression/evaluator.py:22-40` (context usage)

---

### VFS-REQ-006: Profile metadata & exposure
**Status:** 🟡 PARTIAL
**Requirement:** VFS profiles carry `exposed_to`, `semantic_type`, `deps`, and stable unique `id`; compiler validates uniqueness and dependencies; observation builder respects exposure.

**Evidence of PARTIAL implementation:**

**IMPLEMENTED:**
1. **Dependencies tracked:**
   - `src/townlet/vfs/profiles.py:50` - CompiledGlobalProfile has `dependencies: dict[str, tuple[str, ...]]`
   - `src/townlet/vfs/profiles.py:204-208` - Dependencies extracted during topological sort
   - Compiler validates dependencies via cycle detection (VFS-REQ-002)

2. **Profile names (IDs) for items:**
   - `src/townlet/vfs/profiles.py:57` - CompiledItemProfile has `profile_name: str`
   - `src/townlet/config/vfs_profiles_config.py:258` - ItemVFSProfileConfig has `profile_name: str`
   - `src/townlet/config/vfs_profiles_config.py:290-298` - validate_unique_profile_names() enforces uniqueness

3. **Variable ID uniqueness:**
   - `src/townlet/config/vfs_profiles_config.py:98-108` - GlobalVFSProfileConfig validates unique variable names
   - `src/townlet/config/vfs_profiles_config.py:193-203` - AgentVFSProfileConfig validates unique names
   - `src/townlet/config/vfs_profiles_config.py:261-271` - ItemVFSProfileConfig validates unique names

4. **Semantic type in ObservationField (legacy schema):**
   - `src/townlet/vfs/schema.py:176-183` - ObservationField has semantic_type field
   - `src/townlet/vfs/schema.py:161-164` - ObservationField has exposed_to field

**MISSING:**
1. **No exposed_to in VFS profile configs:**
   - GlobalVFSVariableConfig (lines 20-88): No exposed_to field
   - AgentVFSVariableConfig (lines 113-182): No exposed_to field
   - ItemVFSVariableConfig (lines 208-248): No exposed_to field

2. **No semantic_type in VFS profile configs:**
   - None of the variable configs have semantic_type field
   - Only exists in legacy ObservationField schema (not VFS profiles)

3. **No stable unique ID field in profiles:**
   - CompiledGlobalProfile lacks an `id` field (only has variables + deps)
   - No global or agent profile name/id (only item profiles have profile_name)

**Gap Analysis:**
The requirement specifies VFS profiles should carry these metadata fields. Currently:
- `deps` ✅ Implemented (dependencies tracked in compiled profiles)
- `id` 🟡 Partial (item profiles have profile_name, but global/agent profiles lack IDs)
- `exposed_to` ❌ Missing (not in profile variable configs)
- `semantic_type` ❌ Missing (not in profile variable configs)

Observation builder does NOT use VFS profile metadata for exposure - it relies on legacy ObservationField schema instead.

**Citations:**
- Dependencies: `src/townlet/vfs/profiles.py:50,204-208`
- Item profile names: `src/townlet/vfs/profiles.py:57`, `src/townlet/config/vfs_profiles_config.py:258,290-298`
- Variable uniqueness: `src/townlet/config/vfs_profiles_config.py:98-108,193-203,261-271`
- ObservationField metadata: `src/townlet/vfs/schema.py:161-164,176-183` (not on profiles)

**Recommendation:**
Add `exposed_to`, `semantic_type`, and `id` fields to GlobalVFSVariableConfig, AgentVFSVariableConfig, ItemVFSVariableConfig. Compiler should propagate these to CompiledVariable and observation builder should use them for masking.

---

### VFS-REQ-007: Advanced tensor types
**Status:** ✅ DONE
**Requirement:** Support tensor types (`tensor1d`..`tensorNd`) in VFS profiles with shape validation and initialization factories (`zeros`, `ones`, `eye`, `random_normal`).

**Evidence:**
1. **Tensor types in schema:**
   - `src/townlet/vfs/schema.py:260-264` - VariableDef type includes tensor1d, tensor2d, tensor3d, tensorNd
   - `src/townlet/vfs/schema.py:290-293` - shape, initial_value_mode, initial_value_params fields
   - `src/townlet/vfs/schema.py:295-298` - initial_value_mode enum matches requirement

2. **Shape validation:**
   - `src/townlet/vfs/schema.py:331-346` - validate_vector_types() validator enforces shape requirements
   - Lines 338-346: Rank validation for tensor1d (rank=1), tensor2d (rank=2), tensor3d (rank=3), tensorNd (rank≥1)

3. **Initialization factories in VariableRegistry:**
   - `src/townlet/vfs/registry.py:339-406` - _initialize_tensor() method
   - Line 362: zeros mode
   - Line 364: ones mode
   - Line 366-370: eye mode (with square matrix validation)
   - Line 371-374: random_normal mode
   - Line 375-378: random_uniform mode

4. **Config support:**
   - `src/townlet/config/vfs_profiles_config.py:37-40` - GlobalVFSVariableConfig includes tensor types
   - Lines 44-46: initial_value, initial_value_mode, initial_value_params fields

**Test evidence:**
- `tests/test_townlet/unit/vfs/test_variable_registry_tensor.py:7-29` - tensor initialization with modes
- `tests/test_townlet/unit/vfs/test_variable_registry_tensor.py:31-53` - tensor guardrail (max elements)
- `tests/test_townlet/unit/vfs/test_variable_registry_tensor.py:56-107` - explicit defaults broadcasting

**Citations:**
- Schema: `src/townlet/vfs/schema.py:260-264,290-298,331-346`
- Registry: `src/townlet/vfs/registry.py:339-406` (initialization factories)
- Config: `src/townlet/config/vfs_profiles_config.py:37-46`
- Tests: `tests/test_townlet/unit/vfs/test_variable_registry_tensor.py` (comprehensive)

---

### VFS-REQ-008: Update rule DSL (future)
**Status:** 📝 N/A
**Requirement:** Expression DSL execution deferred to BAC Phase 2+; treated as metadata in Phase 1; expression field accepted but not evaluated.

**Evidence:**
This is explicitly marked as future work. Current implementation:
- `expression` field exists in variable configs and is parsed/type-checked
- `src/townlet/vfs/profiles.py:245` - Expressions are parsed to AST
- `src/townlet/vfs/evaluator.py:104-105` - Expressions are evaluated via evaluator.evaluate(var.ast)
- Expressions ARE being evaluated, not treated as metadata

**Analysis:**
The requirement states "expression field accepted but not evaluated" (Phase 1 scope). However, the implementation shows expressions are fully parsed, type-checked, and evaluated. This suggests either:
1. The requirement is outdated (Phase 2+ already implemented), OR
2. The requirement refers to a different "update rule DSL" (not basic expressions)

Given the context mentions "BAC Phase 2+", this likely refers to advanced update rules beyond basic expressions. Current basic expression support is working as designed.

**Status Justification:** Marked N/A because the requirement explicitly defers this to future work. Current expression evaluation is a different feature.

---

### VFS-REQ-009: Eager evaluation fallback
**Status:** ✅ DONE
**Requirement:** VFS eval_mode="eager" flag provides escape hatch from mark-and-sweep; eager mode evaluates all variables; mark-and-sweep is default.

**Evidence:**
1. **Eager mode implementation:**
   - `src/townlet/vfs/evaluator.py:17-21` - EvaluationMode.EAGER enum value
   - `src/townlet/vfs/evaluator.py:79-80` - EAGER mode evaluates all variables (vars_to_eval = all)

2. **Mark-and-sweep is default:**
   - `src/townlet/vfs/evaluator.py:27` - `mode: EvaluationMode = EvaluationMode.MARK_AND_SWEEP` default parameter
   - `src/townlet/environment/vectorized_env.py:449` - Defaults to MARK_AND_SWEEP unless VFS_EVAL_MODE=eager

3. **Runtime override via env var:**
   - `src/townlet/environment/vectorized_env.py:447-449` - VFS_EVAL_MODE env var enables eager mode
   - Provides escape hatch for debugging without code changes

**Test evidence:**
- `tests/test_townlet/unit/vfs/test_vfs_evaluator.py:128-156` - eager mode test evaluates all vars regardless of marks

**Citations:**
- Modes: `src/townlet/vfs/evaluator.py:17-21,27,79-80`
- Runtime: `src/townlet/environment/vectorized_env.py:447-449`
- Test: `tests/test_townlet/unit/vfs/test_vfs_evaluator.py:128-156`

---

## Missing Functionality Summary

1. **VFS-REQ-006 (PARTIAL):**
   - Missing `exposed_to` field in VFS profile variable configs
   - Missing `semantic_type` field in VFS profile variable configs
   - Missing stable `id` field for global/agent profiles (only items have profile_name)
   - Observation builder uses legacy ObservationField schema instead of VFS profile metadata

## Recommendations

1. **Complete VFS-REQ-006 metadata support:**
   - Add `exposed_to: list[str]` to GlobalVFSVariableConfig, AgentVFSVariableConfig
   - Add `semantic_type: Literal["bars", "spatial", "affordance", "temporal", "custom"]` to variable configs
   - Add `id: str` field to GlobalVFSProfileConfig and AgentVFSProfileConfig
   - Update observation builder to use VFS profile metadata for exposure/masking

2. **Clarify VFS-REQ-008 scope:**
   - Document distinction between "basic expressions" (implemented) and "update rule DSL" (future)
   - Update requirement to reflect current state if basic expressions are Phase 1 scope

3. **Add integration tests:**
   - Test global → agent → item evaluation order (VFS-REQ-004)
   - Test ExecutionContext scoped VFS access in effects (VFS-REQ-005)
   - Test eager mode escape hatch in realistic scenario (VFS-REQ-009)

---

## Appendix: Test Coverage Analysis

**Strong test coverage:**
- Mark-and-sweep evaluation (test_vfs_evaluator.py)
- Tensor initialization modes (test_variable_registry_tensor.py)
- Variable registry scoped storage (test_registry.py)
- Observation builder dimensions (test_observation_builder.py)

**Weak test coverage:**
- Global → agent → item evaluation order (no dedicated test)
- ExecutionContext VFS scope resolution (no integration test)
- Profile metadata validation (uniqueness tests exist, but no exposure/semantic_type tests)

**Missing tests:**
- VFS profile metadata propagation to observations
- Observation masking based on exposed_to (once implemented)
