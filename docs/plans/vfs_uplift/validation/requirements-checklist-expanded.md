# VFS Uplift Requirements Checklist - EXPANDED

**Generated:** 2025-11-23
**Source Plans:**
- `2025-11-19-unified-world-compiler-plan.md`
- `2025-11-18-items-and-vfs-profiles.md`
- `2025-11-19-effects-system-design.md`
- `2025-11-23-runtime-vfs-effects-integration.md`
- `command_reference.md`

**Total Requirements:** 246 (157 original + 89 new)

---

## How to Use This Checklist

**Status Values:**
- ✅ COMPLETE: Fully implemented with tests and docs
- ⚠️ PARTIAL: Implemented but missing tests/docs/error handling
- ❌ MISSING: Not found in codebase
- 🔍 UNCLEAR: Found code but unclear if it matches requirement
- 🚫 NOT_IMPL: Explicitly marked as not implemented (future work)

**Evidence Format:** file:line or test:name for every claim

**Agent Map (10 agents):**
- Agent 1: Compiler & Schema (COMP-*, COMP-EXT-*)
- Agent 2: VFS System (VFS-*, VFS-EXT-*)
- Agent 3: Effects & Runtime Expressions (EFF-*, EFF-EXT-*)
- Agent 4: Commands (CMD-*)
- Agent 5: Items System (ITEM-*, ITEM-EXT-*)
- Agent 6: Runtime Integration (RUN-*, RUN-EXT-*, LIMITS-*)
- Agent 7: Testing (TEST-*, TEST-EXT-*)
- Agent 8: Documentation (DOC-*, DOC-EXT-*)
- Agent 9: Breaking Changes (BREAK-*)
- Agent 10: Synthesis (final integration)

---

## Category 1: Compiler (COMP-*)

### COMP-1: Seven-stage pipeline
**Source:** unified-world-compiler-plan.md (architecture overview)
**Requirement:** UniverseCompiler must implement 7 compilation stages (parse → symbol table → resolve → cross-validate → metadata → optimization → emit/cache)
**Evidence Required:**
- [ ] Implementation location (file:line)
- [ ] All 7 stages present
- [ ] Tests exist (test file:line)

### COMP-2: Load VFS profiles at compile time
**Source:** runtime-vfs-effects-integration.md Task 1 (lines 40-52)
**Requirement:** Compiler loads vfs_profiles.yaml (experiment-level) and compiles via VFSProfileCompiler
**Evidence Required:**
- [ ] Load logic (file:line)
- [ ] VFSProfileCompiler invocation (file:line)
- [ ] Stored in CompiledUniverse (file:line)
- [ ] Tests (test file:line)

### COMP-3: Load effects catalog at compile time
**Source:** runtime-vfs-effects-integration.md Task 1 (lines 46-47)
**Requirement:** Move EffectCatalog build into compiler; include in CompiledUniverse (experiment-scope)
**Evidence Required:**
- [ ] EffectCatalog compilation (file:line)
- [ ] CompiledUniverse field (file:line)
- [ ] No runtime rebuild in vectorized_env.py (grep verification)
- [ ] Tests (test file:line)

### COMP-4: VFS profile DTOs
**Source:** unified-world-compiler-plan.md Phase 2 Task 2.1 (lines 182-186)
**Requirement:** DTOs for vfs_profiles.yaml (GlobalVFSProfileConfig, AgentVFSProfileConfig, ItemVFSProfileConfig)
**Evidence Required:**
- [ ] DTO module exists (vfs_profiles_config.py)
- [ ] Schema validation (expression XOR initial_value)
- [ ] Reference type support
- [ ] Tests (10-15 DTO tests)

### COMP-5: Items catalog DTOs
**Source:** items-and-vfs-profiles.md Section 4.1 (lines 276-288)
**Requirement:** DTOs in items_config.py with no defaults for behavioral values
**Evidence Required:**
- [ ] InventoryConfig with required max_items_per_agent
- [ ] ItemTypeConfig with vfs_profiles references
- [ ] ItemSpawnRuleConfig with required limits/schedule
- [ ] Tests (15-20 DTO tests)

### COMP-6: Effects catalog DTOs
**Source:** effects-system-design.md Section 2.1 (lines 69-106)
**Requirement:** EffectDefinitionConfig with required reapply_policy and duration
**Evidence Required:**
- [ ] EffectDefinitionConfig (file:line)
- [ ] Lifecycle parameters (duration, intensity required)
- [ ] Command pipelines (on_spawn, on_tick, on_despawn)
- [ ] Tests (15-20 DTO/catalog tests)

### COMP-7: Expression parser
**Source:** unified-world-compiler-plan.md Phase 1 Task 1.2 (lines 126-130)
**Requirement:** Parse expressions like "target.bar.energy + (0.05 * intensity)" to AST
**Evidence Required:**
- [ ] Parser implementation (file:line)
- [ ] Operator precedence handling
- [ ] Parentheses support
- [ ] Tests (15-20 parsing tests)

### COMP-8: AST node types
**Source:** unified-world-compiler-plan.md Phase 1 Task 1.1 (lines 121-124)
**Requirement:** Define AST nodes (Constant, Variable, PathAccess, BinaryOp, UnaryOp, FunctionCall, IfThenElse)
**Evidence Required:**
- [ ] AST node module (ast_nodes.py)
- [ ] Visitor pattern for traversal
- [ ] Tests (10-15 unit tests)

### COMP-9: Type checker
**Source:** unified-world-compiler-plan.md Phase 1 Task 1.3 (lines 132-136)
**Requirement:** Type inference, path resolution validation, type compatibility checks
**Evidence Required:**
- [ ] Type checker implementation (type_checker.py)
- [ ] Path resolution (target.bar.energy exists)
- [ ] Type compatibility (can't assign vec2i to scalar)
- [ ] Tests (20-25 type validation tests)

### COMP-10: Expression evaluator
**Source:** unified-world-compiler-plan.md Phase 1 Task 1.4 (lines 138-142)
**Requirement:** Execute AST on GPU tensors with execution context (bars, vfs, temporal state)
**Evidence Required:**
- [ ] Evaluator implementation (evaluator.py)
- [ ] GPU tensor operations via PyTorch
- [ ] Execution context support
- [ ] Tests (15-20 evaluation tests)

### COMP-11: Command pipeline parser
**Source:** effects-system-design.md Section 6.2 (lines 588-604)
**Requirement:** Parse command YAML to CommandNode AST with expression compilation
**Evidence Required:**
- [ ] Command parser (file:line)
- [ ] CommandNode AST types
- [ ] Expression compilation in command values
- [ ] Tests (20-25 command compilation tests)

### COMP-12: Cross-validation
**Source:** effects-system-design.md Section 6.3 (lines 621-642)
**Requirement:** Validate path resolution, effect references, item references across components
**Evidence Required:**
- [ ] Cross-validation logic (file:line)
- [ ] Path resolution checks
- [ ] Reference validation (effect_id, type_id exist)
- [ ] Tests (part of integration tests)

### COMP-13: Error reporting with context
**Source:** effects-system-design.md Section 6.4 (lines 647-665)
**Requirement:** Clear error messages with file/line, suggestions for typos
**Evidence Required:**
- [ ] Error formatting (file:line)
- [ ] File/line tracking in DTOs
- [ ] Typo suggestions (Levenshtein distance)
- [ ] Tests (error message validation)

### COMP-14: CompiledUniverse schema extensions
**Source:** runtime-vfs-effects-integration.md Task 1 (lines 47-51)
**Requirement:** CompiledUniverse exposes compiled_vfs_profiles, vfs_expression_schema, compiled_effect_catalog
**Evidence Required:**
- [ ] Schema fields in CompiledUniverse (file:line)
- [ ] Serialization/deserialization support
- [ ] Hashing for provenance
- [ ] Tests (schema validation)

### COMP-15: VFS profile compilation
**Source:** unified-world-compiler-plan.md Phase 2 Task 2.3 (lines 194-198)
**Requirement:** Topological sort for dependency ordering, circular dependency detection
**Evidence Required:**
- [ ] Topological sort implementation (file:line)
- [ ] Circular dependency detection
- [ ] Dependency graph construction
- [ ] Tests (15-20 evaluation tests)

### COMP-16: VFS observation marking
**Source:** runtime-vfs-effects-integration.md Task 2 (lines 62-64)
**Requirement:** At compile time, mark VFS variables consumed by observations; emit in CompiledUniverse
**Evidence Required:**
- [ ] Marking logic (file:line)
- [ ] vfs_observation_marks in CompiledUniverse
- [ ] Used by runtime for mark-and-sweep
- [ ] Tests (marking correctness)

### COMP-17: Items-VFS profile binding validation
**Source:** items-and-vfs-profiles.md Section 4.2 (lines 308-318)
**Requirement:** Validate spawn_rules.type_id references known catalog items, vfs_profiles references exist
**Evidence Required:**
- [ ] Reference validation (file:line)
- [ ] Clear error on missing references
- [ ] Tests (validation tests)

### COMP-18: No-defaults enforcement
**Source:** items-and-vfs-profiles.md Sections 3.2, 4.1 (lines 135-220, 276-306)
**Requirement:** All behavioral parameters (duration, cooldown, max counts, limits) required in config
**Evidence Required:**
- [ ] Pydantic Field() with no default for behavioral params
- [ ] Compiler error on missing required fields
- [ ] Tests (schema validation tests)

### COMP-19: Config version tracking
**Source:** items-and-vfs-profiles.md Section 3.2 (lines 143, 181)
**Requirement:** All config files include version field (e.g., "1.0")
**Evidence Required:**
- [ ] Version field in all DTO roots
- [ ] Version validation in compiler
- [ ] Tests (version mismatch handling)

### COMP-20: Experiment vs level scoping
**Source:** items-and-vfs-profiles.md Section 3 (lines 93-124)
**Requirement:** Observation-shape changes (item types, VFS profiles) at experiment-level; masking/spawn at level-level
**Evidence Required:**
- [ ] Catalog configs in experiment dir
- [ ] Appearance configs in levels/ dir
- [ ] Compiler enforces scoping
- [ ] Tests (scoping validation)

---

## Category 2: Compiler Extensions (COMP-EXT-*)

### COMP-EXT-1: Config gating
**Source:** runtime-vfs-effects-integration.md Task 1 (lines 51-52)
**Requirement:** If vfs_profiles.yaml present, load and validate; if missing but items reference profiles, fail fast
**Evidence Required:**
- [ ] Conditional loading logic
- [ ] Fast fail on missing profiles when referenced
- [ ] Allow minimal configs without VFS
- [ ] Tests (gating scenarios)

### COMP-EXT-2: Feature flagging
**Source:** items-and-vfs-profiles.md Section 8.2 (lines 521-523)
**Requirement:** features.items_enabled flag gates runtime paths
**Evidence Required:**
- [ ] Feature flag in CompiledUniverse
- [ ] Runtime checks before item code
- [ ] Tests (feature flag behavior)

### COMP-EXT-3: Experiment vs level file layout
**Source:** items-and-vfs-profiles.md Section 3.1 (lines 106-124)
**Requirement:** Experiment files at configs/<exp>/, level files at configs/<exp>/levels/<level>/
**Evidence Required:**
- [ ] File path validation
- [ ] Correct scoping enforcement
- [ ] Tests (file layout validation)

### COMP-EXT-4: Hashing for provenance
**Source:** items-and-vfs-profiles.md Section 4.2 (line 326)
**Requirement:** New fields included in hashing where appropriate
**Evidence Required:**
- [ ] vfs_profile_catalog in hash
- [ ] item_catalog in hash
- [ ] effect_catalog in hash
- [ ] Tests (hash includes new fields)

### COMP-EXT-5: Per-level metadata
**Source:** items-and-vfs-profiles.md Section 4.2 (lines 320-324)
**Requirement:** CompiledUniverse stores item_spawn_plans per level
**Evidence Required:**
- [ ] item_spawn_plans field
- [ ] Per-level spawn plan storage
- [ ] Tests (level-specific plans)

### COMP-EXT-6: Expression rejection in variables_reference.yaml
**Source:** runtime-vfs-effects-integration.md line 32
**Requirement:** variables_reference.yaml forbids expression field (enforced rejection)
**Evidence Required:**
- [ ] Schema validation rejects expression
- [ ] Clear error message
- [ ] Tests (expression in variables_reference rejected)

### COMP-EXT-7: Levenshtein distance for typo suggestions
**Source:** requirements-checklist.md COMP-13
**Requirement:** Error messages use edit distance for suggestions (e.g., "Did you mean: 'energy'?")
**Evidence Required:**
- [ ] Levenshtein implementation or library
- [ ] Suggestion generation
- [ ] Tests (typo suggestions)

### COMP-EXT-8: File/line tracking
**Source:** requirements-checklist.md COMP-13
**Requirement:** DTOs track source file and line number for error reporting
**Evidence Required:**
- [ ] File/line metadata in DTOs
- [ ] Preserved through compilation
- [ ] Included in error messages
- [ ] Tests (error context)

---

## Category 3: VFS System (VFS-*)

### VFS-1: Expression language support
**Source:** unified-world-compiler-plan.md Phase 1 (lines 83-149)
**Requirement:** Full expression DSL with all operators from VARIABLE_SUBSYSTEM.md
**Evidence Required:**
- [ ] All operators implemented (mathematical, trigonometric, temporal, spatial, statistical, stochastic)
- [ ] Operator precedence correct
- [ ] Tests (60+ tests covering all operators)

### VFS-2: Three scopes (global/agent/item)
**Source:** items-and-vfs-profiles.md Section 2.2 (lines 62-70), unified-world-compiler-plan.md Phase 2 (lines 152-211)
**Requirement:** VFS profiles grouped by scope with separate storage
**Evidence Required:**
- [ ] GlobalVFSProfile, AgentVFSProfile, ItemVFSProfile types
- [ ] Scoped storage (global_storage, agent_storage, item_storage)
- [ ] Access control per scope
- [ ] Tests (15-20 scoped registry tests)

### VFS-3: Dynamic variables via expressions
**Source:** unified-world-compiler-plan.md Phase 2 Task 2.3 (lines 194-198)
**Requirement:** VFS variables can use expressions (e.g., "bar['energy'] + 0.05")
**Evidence Required:**
- [ ] Expression field in VariableDef
- [ ] Expression evaluation at runtime
- [ ] Tests (15-20 evaluation tests)

### VFS-4: Reference types
**Source:** effects-system-design.md Section 4.2 (lines 328-350)
**Requirement:** agent_ref, item_ref, affordance_ref, effect_ref types
**Evidence Required:**
- [ ] Reference type definitions (reference.py)
- [ ] Path traversal through references (vfs.target_food_item.vfs.spoilage)
- [ ] Tests (reference resolution tests)

### VFS-5: Observation builder integration
**Source:** unified-world-compiler-plan.md Phase 2 Task 2.4 (lines 200-204)
**Requirement:** Include VFS fields in observations with fixed slot allocation and masking
**Evidence Required:**
- [ ] VFS fields in observation spec
- [ ] Fixed slot allocation (3 slots × 5 profiles)
- [ ] Masking for empty slots
- [ ] Tests (10-15 obs builder tests)

### VFS-6: Mark-and-sweep evaluation
**Source:** unified-world-compiler-plan.md D2 (lines 591-633), runtime-vfs-effects-integration.md Task 2 (lines 56-68)
**Requirement:** Hybrid evaluation mode (mark-and-sweep default, eager fallback)
**Evidence Required:**
- [ ] Mark-and-sweep implementation (file:line)
- [ ] Eager fallback mode (eval_mode="eager" flag)
- [ ] ObservationBuilder marks variables for obs
- [ ] Tests (mark-and-sweep vs eager tests)

### VFS-7: Registry with access control
**Source:** unified-world-compiler-plan.md Phase 2 Task 2.2 (lines 188-192)
**Requirement:** VariableRegistry with readers/writers enforcement
**Evidence Required:**
- [ ] Access control fields (readable_by, writers)
- [ ] Runtime enforcement of read/write permissions
- [ ] Tests (access control violation tests)

### VFS-8: Profile-driven item storage
**Source:** runtime-vfs-effects-integration.md Task 3 (lines 72-82)
**Requirement:** Shape item storage using compiled profiles (not variables_reference.yaml)
**Evidence Required:**
- [ ] Profile map {profile_name → variable → tensor index}
- [ ] ItemManager uses profile map for initialization
- [ ] Tests (profile application tests)

### VFS-9: Item instance profiles
**Source:** runtime-vfs-effects-integration.md Task 3 (lines 76-78)
**Requirement:** ItemManager assigns vfs_profile to instances, accepts initial_state
**Evidence Required:**
- [ ] vfs_profile field on ItemInstance
- [ ] initial_state parameter in spawn_item
- [ ] Profile defaults applied
- [ ] Tests (initial_state tests)

### VFS-10: Item VFS observations
**Source:** runtime-vfs-effects-integration.md Task 3 (lines 79-81)
**Requirement:** Include item VFS slices per carried item slot with masking
**Evidence Required:**
- [ ] Item VFS in observation vector
- [ ] Masking for empty slots
- [ ] Dimensions match VFSObservationSpec
- [ ] Tests (item VFS obs tests)

### VFS-11: Observation dimension stability
**Source:** unified-world-compiler-plan.md Success Criteria (line 556)
**Requirement:** obs_dim stable across all levels (enables checkpoint transfer)
**Evidence Required:**
- [ ] Fixed slot allocation for items
- [ ] Regression tests for obs_dim
- [ ] Compile-time obs_dim validation
- [ ] Tests (dimension regression tests)

### VFS-12: Tensor types support
**Source:** effects-system-design.md Section 4.3 (lines 353-368)
**Requirement:** tensor1d, tensor2d, tensor3d, tensorNd with shape specification
**Evidence Required:**
- [ ] Tensor type definitions
- [ ] Shape validation
- [ ] Initial value modes (zeros, ones, eye, random_normal)
- [ ] Tests (tensor variable tests)

### VFS-13: Dependency graph construction
**Source:** unified-world-compiler-plan.md Phase 2 Task 2.3 (lines 194-198)
**Requirement:** Build dependency graph from expression references, detect cycles
**Evidence Required:**
- [ ] Graph construction (file:line)
- [ ] Cycle detection (networkx or custom)
- [ ] Compiler error on cycles
- [ ] Tests (circular dependency tests)

### VFS-14: Type system integration
**Source:** effects-system-design.md Section 4.1 (lines 318-327)
**Requirement:** scalar, bool, vec2i, vec3i, vecNi, vecNf primitive types
**Evidence Required:**
- [ ] Type definitions (primitive.py)
- [ ] Type checking in expressions
- [ ] Tests (type validation tests)

### VFS-15: VFS in ExecutionContext
**Source:** effects-system-design.md Section 7.4 (lines 837-874)
**Requirement:** ExecutionContext provides vfs_global, vfs_agent, vfs_item dictionaries
**Evidence Required:**
- [ ] ExecutionContext dataclass (context.py)
- [ ] VFS dictionaries populated
- [ ] Path resolution (resolve_path method)
- [ ] Tests (context tests)

---

## Category 4: VFS Extensions (VFS-EXT-*)

### VFS-EXT-1: Expression XOR initial_value enforcement
**Source:** items-and-vfs-profiles.md Section 3.3 (line 232), unified-world-compiler-plan.md Phase 2 Task 2.1
**Requirement:** VFS profile must have expression OR initial_value, not both, not neither
**Evidence Required:**
- [ ] Pydantic validator enforces XOR
- [ ] Error on both present
- [ ] Error on neither present
- [ ] Tests (valid cases, invalid cases)
**Priority:** P0 (Critical)

### VFS-EXT-2: Update rule DSL (future)
**Source:** items-and-vfs-profiles.md Section 3.3 (lines 264-267)
**Requirement:** Expression DSL execution deferred to BAC Phase 2+, treated as metadata in Phase 1
**Evidence Required:**
- [ ] Expression field accepted in schema
- [ ] Not executed in Phase 1
- [ ] Validation mode (accept but warn/ignore)
- [ ] Tests (expression accepted, not evaluated)
**Priority:** P3 (Low - future)

### VFS-EXT-3: Observation exposure control
**Source:** items-and-vfs-profiles.md Section 3.3 (lines 235-238)
**Requirement:** VFS profiles specify exposed_to field (which scopes can observe)
**Evidence Required:**
- [ ] exposed_to field in profile config
- [ ] Observation builder respects exposure
- [ ] Tests (exposure enforcement)
**Priority:** P2 (Medium)

### VFS-EXT-4: Semantic type metadata
**Source:** items-and-vfs-profiles.md Section 3.3 (lines 237-238)
**Requirement:** VFS profiles include semantic_type field (temporal, custom, etc.)
**Evidence Required:**
- [ ] semantic_type field in schema
- [ ] Metadata carried through compilation
- [ ] Tests (semantic types preserved)
**Priority:** P2 (Medium)

### VFS-EXT-5: Profile ID stability
**Source:** items-and-vfs-profiles.md Section 3.3 (line 265)
**Requirement:** Profile IDs stable across experiment, used for mapping
**Evidence Required:**
- [ ] ID uniqueness validation
- [ ] ID stability across levels
- [ ] Tests (ID conflicts rejected)
**Priority:** P2 (Medium)

### VFS-EXT-6: Dependency tracking
**Source:** items-and-vfs-profiles.md Section 3.3 (lines 232-234)
**Requirement:** Profiles declare deps (bars, vfs, affordances)
**Evidence Required:**
- [ ] deps field in schema
- [ ] Dependency resolution
- [ ] Tests (dependency tracking)
**Priority:** P2 (Medium)

### VFS-EXT-7: Evaluation ordering
**Source:** items-and-vfs-profiles.md Section 6.1 (lines 407-413)
**Requirement:** Evaluate global → agent → item profiles in scope order
**Evidence Required:**
- [ ] Scope evaluation sequence
- [ ] Within-scope topological order
- [ ] Tests (evaluation order)
**Priority:** P1 (High)

### VFS-EXT-8: Item profile defaults
**Source:** runtime-vfs-effects-integration.md Task 3 (line 77)
**Requirement:** Profile defaults applied when item spawned without initial_state
**Evidence Required:**
- [ ] Default value initialization
- [ ] initial_state overrides defaults
- [ ] Tests (defaults applied, overrides work)
**Priority:** P1 (High)

---

[Continued in next part due to length...]
