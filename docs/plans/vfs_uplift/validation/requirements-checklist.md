# VFS Uplift Requirements Checklist

**Generated:** 2025-11-22
**Source Plans:**
- `2025-11-19-unified-world-compiler-plan.md`
- `2025-11-18-items-and-vfs-profiles.md`
- `2025-11-19-effects-system-design.md`
- `2025-11-23-runtime-vfs-effects-integration.md`

**Total Requirements:** 157

---

## How to Use This Checklist

**Status Values:**
- ✅ COMPLETE: Fully implemented with tests and docs
- ⚠️ PARTIAL: Implemented but missing tests/docs/error handling
- ❌ MISSING: Not found in codebase
- 🔍 UNCLEAR: Found code but unclear if it matches requirement

**Evidence Format:** file:line or test:name for every claim

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

## Category 2: VFS System (VFS-*)

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

## Category 3: Effects System (EFF-*)

### EFF-1: Effects catalog as compiled artifact
**Source:** effects-system-design.md Section 6.1 (lines 550-583)
**Requirement:** Effects compiled first in World Compiler, stored in CompiledWorld
**Evidence Required:**
- [ ] EffectCatalog compiled in WorldCompiler
- [ ] Stored in CompiledWorld.effect_catalog
- [ ] Effects compiled before bars/vfs/items/affordances
- [ ] Tests (compilation order tests)

### EFF-2: Command pipeline execution
**Source:** effects-system-design.md Section 7.3 (lines 789-833)
**Requirement:** Execute command pipelines (modify, spawn_effect, spawn_item, if, for_each, etc.)
**Evidence Required:**
- [ ] Command executor (executor.py)
- [ ] All command types implemented
- [ ] Tests (20-25 execution tests)

### EFF-3: EffectManager lifecycle
**Source:** effects-system-design.md Section 7.2 (lines 699-785)
**Requirement:** spawn_effect, tick, despawn with reapply policy support
**Evidence Required:**
- [ ] EffectManager class (manager.py)
- [ ] Lifecycle methods (spawn, tick, despawn)
- [ ] Reapply policies (stack, renew, merge, replace)
- [ ] Tests (15-20 manager tests)

### EFF-4: ActiveEffect runtime structure
**Source:** effects-system-design.md Section 7.1 (lines 674-696)
**Requirement:** ActiveEffect dataclass with intensity, duration, lifecycle state
**Evidence Required:**
- [ ] ActiveEffect dataclass (file:line)
- [ ] Lifecycle fields (elapsed_ticks, duration_remaining, spawn_step)
- [ ] Link to compiled commands
- [ ] Tests (lifecycle tests)

### EFF-5: Scoped effect storage
**Source:** effects-system-design.md Section 2.3 (lines 148-167)
**Requirement:** Separate storage for global/agent/item/affordance effects
**Evidence Required:**
- [ ] global_effects, agent_effects, item_effects, affordance_effects
- [ ] Scope-aware spawn/despawn
- [ ] Tests (scoped storage tests)

### EFF-6: Reapply policies
**Source:** effects-system-design.md Section 2.2 (lines 110-148)
**Requirement:** stack, renew, merge, replace policies with correct behavior
**Evidence Required:**
- [ ] Policy implementation in spawn_effect
- [ ] Stack: independent instances
- [ ] Renew: refresh duration
- [ ] Merge: increase intensity
- [ ] Replace: despawn old, spawn new
- [ ] Tests (policy tests for each type)

### EFF-7: Observable effects
**Source:** effects-system-design.md Section 2.4 (lines 170-176)
**Requirement:** observable: true effects visible in agent observations
**Evidence Required:**
- [ ] observable field in EffectDef
- [ ] Integration with observation builder
- [ ] Tests (observable effects in obs)

### EFF-8: Command types - State modification
**Source:** effects-system-design.md Section 3.1 (lines 184-202)
**Requirement:** modify, set, increment, decrement commands
**Evidence Required:**
- [ ] All command types implemented
- [ ] Path resolution (target.bar.energy)
- [ ] Expression evaluation
- [ ] Tests (command tests)

### EFF-9: Command types - Entity lifecycle
**Source:** effects-system-design.md Section 3.2 (lines 205-225)
**Requirement:** spawn_item, spawn_effect, delete, despawn commands
**Evidence Required:**
- [ ] spawn_item implementation
- [ ] spawn_effect with duration/intensity overrides
- [ ] delete self support
- [ ] Tests (entity lifecycle tests)

### EFF-10: Command types - Control flow
**Source:** effects-system-design.md Section 3.3 (lines 228-249)
**Requirement:** if/then/else, for_each with range support
**Evidence Required:**
- [ ] Conditional execution (if)
- [ ] Iteration (for_each)
- [ ] Range filtering (nearby_agents)
- [ ] Tests (control flow tests)

### EFF-11: Command types - Messaging/Events
**Source:** effects-system-design.md Section 3.4 (lines 252-265)
**Requirement:** emit_event, trigger_cascade commands
**Evidence Required:**
- [ ] emit_event implementation
- [ ] trigger_cascade integration
- [ ] Tests (event/cascade tests)

### EFF-12: Command types - Randomness
**Source:** effects-system-design.md Section 3.5 (lines 268-285)
**Requirement:** random() conditional, sample with weights
**Evidence Required:**
- [ ] random() function in expressions
- [ ] sample command with weights
- [ ] Tests (randomness tests)

### EFF-13: Path notation support
**Source:** effects-system-design.md Section 3.6 (lines 288-309)
**Requirement:** self, target, agent, global, intensity, duration, elapsed_ticks, duration_remaining
**Evidence Required:**
- [ ] Special variables in ExecutionContext
- [ ] Path resolution (target.bar.energy, self.vfs.durability)
- [ ] Tests (path resolution tests)

### EFF-14: Expression language integration
**Source:** effects-system-design.md Section 5 (lines 432-545)
**Requirement:** All command value fields use VFS expression language
**Evidence Required:**
- [ ] Expression parsing in command values
- [ ] All operators available (math, trig, temporal, spatial, statistical, stochastic, conditional)
- [ ] Tests (expression in commands tests)

### EFF-15: Type safety in commands
**Source:** effects-system-design.md Section 5.4 (lines 528-545)
**Requirement:** Compile-time type validation (scalar → scalar, vec2i → vec2i)
**Evidence Required:**
- [ ] Type checking in command compilation
- [ ] Compiler errors on type mismatches
- [ ] Tests (type safety tests)

### EFF-16: Environment integration
**Source:** effects-system-design.md Section 7.5 (lines 877-896)
**Requirement:** EffectManager wired into VectorizedHamletEnv.step()
**Evidence Required:**
- [ ] EffectManager initialization in env.__init__
- [ ] effect_manager.tick() called in env.step
- [ ] Tests (environment integration tests)

### EFF-17: Effect nesting depth limit
**Source:** effects-system-design.md Section 10.3 (lines 1204-1212)
**Requirement:** Runtime limit (max_depth=10) to prevent infinite recursion
**Evidence Required:**
- [ ] Depth tracking in spawn_effect
- [ ] Compiler warning for recursive references
- [ ] Runtime error on depth exceeded
- [ ] Tests (depth limit tests)

### EFF-18: Execution context state access
**Source:** effects-system-design.md Section 5.1 (lines 435-456)
**Requirement:** Context provides bars, vfs, position, temporal state (time_of_day, step_count)
**Evidence Required:**
- [ ] ExecutionContext with all state fields
- [ ] Available in all expressions
- [ ] Tests (context state tests)

### EFF-19: Effect duration management
**Source:** effects-system-design.md Section 7.2 (lines 762-784)
**Requirement:** Auto-despawn when duration_remaining <= 0, execute on_despawn commands
**Evidence Required:**
- [ ] Duration decrement in tick()
- [ ] Expiry check and despawn
- [ ] on_despawn command execution
- [ ] Tests (duration expiry tests)

### EFF-20: Effect intensity parameter
**Source:** effects-system-design.md Section 2.1 (lines 80-81, 217-218)
**Requirement:** intensity parameter with default, overridable at spawn, available in expressions
**Evidence Required:**
- [ ] intensity field in EffectDef
- [ ] Override in spawn_effect
- [ ] Available as expression variable
- [ ] Tests (intensity tests)

---

## Category 4: Items System (ITEM-*)

### ITEM-1: Item VFS profiles binding
**Source:** items-and-vfs-profiles.md Section 2.2 (lines 82-89)
**Requirement:** Items reference VFS profiles via vfs_profiles field
**Evidence Required:**
- [ ] vfs_profiles field in ItemTypeConfig
- [ ] Profile validation (references must exist)
- [ ] Tests (profile binding tests)

### ITEM-2: Inventory management
**Source:** items-and-vfs-profiles.md Section 5.2 (lines 365-382)
**Requirement:** max_items_per_agent cap enforced, GET/DROP commands auto-generated
**Evidence Required:**
- [ ] max_items_per_agent in InventoryConfig
- [ ] Enforcement in pickup logic
- [ ] GET/DROP in action vocabulary when items > 0
- [ ] Tests (inventory limit tests)

### ITEM-3: ItemManager lifecycle
**Source:** unified-world-compiler-plan.md Phase 4 Task 4.2 (lines 332-338)
**Requirement:** ItemInstance, spawn/despawn, duration/cooldown, position tracking
**Evidence Required:**
- [ ] ItemInstance dataclass (instance.py)
- [ ] spawn_item, despawn_item methods
- [ ] Duration/cooldown enforcement
- [ ] Tests (20-25 manager tests)

### ITEM-4: Inventory integration
**Source:** unified-world-compiler-plan.md Phase 4 Task 4.3 (lines 340-344)
**Requirement:** Agent inventory slots, pickup/drop mechanics, overflow policy (DENY_PICKUP)
**Evidence Required:**
- [ ] Inventory state ([batch, max_items_per_agent])
- [ ] Pickup/drop implementation
- [ ] DENY_PICKUP on overflow
- [ ] Tests (15-20 inventory tests)

### ITEM-5: Action handlers
**Source:** unified-world-compiler-plan.md Phase 4 Task 4.4 (lines 346-351)
**Requirement:** GET, USE_SLOT_N, DROP_SLOT_N actions with masking
**Evidence Required:**
- [ ] GET action handler
- [ ] USE_SLOT_N actions (parameterized or fixed vocab)
- [ ] DROP_SLOT_N actions
- [ ] Action masking (GET masked when full)
- [ ] Tests (15-20 action handler tests)

### ITEM-6: Item spawn rules
**Source:** items-and-vfs-profiles.md Section 3.2 (lines 183-205)
**Requirement:** placement (random/fixed/grid/scripted), schedule (time_window/poisson/normal/once), limits (max_simultaneous, max_total)
**Evidence Required:**
- [ ] Placement modes implemented
- [ ] Schedule types implemented
- [ ] Limits enforced
- [ ] Tests (spawn rules tests)

### ITEM-7: Item lifecycle parameters
**Source:** items-and-vfs-profiles.md Section 3.2 (lines 197-199)
**Requirement:** duration_steps, cooldown_steps with no defaults
**Evidence Required:**
- [ ] Required fields in ItemSpawnRuleConfig
- [ ] Duration/cooldown enforcement in ItemManager
- [ ] Tests (lifecycle tests)

### ITEM-8: Item spawn conditions
**Source:** items-and-vfs-profiles.md Section 3.2 (lines 200-203)
**Requirement:** Conditions reference VFS predicates (when: "vfs:is_raining")
**Evidence Required:**
- [ ] Condition parsing
- [ ] VFS predicate evaluation
- [ ] Conditional spawn gating
- [ ] Tests (conditional spawn tests)

### ITEM-9: Item interactions via Effects
**Source:** unified-world-compiler-plan.md Success Criteria (line 365)
**Requirement:** Item interactions use Effects (no opaque dicts)
**Evidence Required:**
- [ ] pickup/use/drop use effect commands
- [ ] No opaque dict code in items
- [ ] Tests (interaction tests)

### ITEM-10: Item catalog experiment-scoping
**Source:** items-and-vfs-profiles.md Section 3.1 (lines 106-175)
**Requirement:** Item types defined in experiment-level items.yaml
**Evidence Required:**
- [ ] Catalog at configs/<experiment>/items.yaml
- [ ] Shared across all levels
- [ ] Tests (catalog loading tests)

### ITEM-11: Item appearance level-scoping
**Source:** items-and-vfs-profiles.md Section 3.1 (lines 177-220)
**Requirement:** Spawn rules in levels/<level>/items.yaml
**Evidence Required:**
- [ ] Appearance config per level
- [ ] References catalog type_id
- [ ] Tests (level scoping tests)

### ITEM-12: Item-scoped custom commands
**Source:** items-and-vfs-profiles.md Section 3.2 (lines 162-174)
**Requirement:** local_commands (range-based) and inventory_commands (held items only)
**Evidence Required:**
- [ ] local_commands in ItemTypeConfig
- [ ] inventory_commands in ItemTypeConfig
- [ ] Action masking based on range/inventory
- [ ] Tests (custom command tests)

### ITEM-13: Item position tracking
**Source:** unified-world-compiler-plan.md Phase 4 Task 4.2 (line 336)
**Requirement:** Position tracking for spatial/aspatial substrates
**Evidence Required:**
- [ ] position field on ItemInstance
- [ ] Spatial position (vec2i/vec3i)
- [ ] Aspatial representation (null or special value)
- [ ] Tests (position tests)

### ITEM-14: Item VFS state allocation
**Source:** unified-world-compiler-plan.md Phase 4 Task 4.2 (line 337)
**Requirement:** Pre-allocate max_items pool for fixed-size tensors
**Evidence Required:**
- [ ] Fixed pool allocation (max_items × num_profiles)
- [ ] active_items_mask for masking
- [ ] Tests (allocation tests)

### ITEM-15: Item spawn scheduler
**Source:** unified-world-compiler-plan.md Phase 4 Task 4.5 (line 355)
**Requirement:** ItemManager schedules spawns per item_spawn_plans
**Evidence Required:**
- [ ] Scheduler logic in ItemManager
- [ ] Time-window/poisson/normal schedules
- [ ] Priority handling
- [ ] Tests (scheduler tests)

### ITEM-16: INTERACT action for affordances
**Source:** items-and-vfs-profiles.md Section 5.2 (lines 383-394)
**Requirement:** INTERACT auto-included when affordances present, with interaction_radius for continuous substrates
**Evidence Required:**
- [ ] INTERACT in action vocab when affordances > 0
- [ ] interaction_radius from substrate config
- [ ] Range checking for continuous substrates
- [ ] Tests (INTERACT action tests)

---

## Category 5: Runtime Integration (RUN-*)

### RUN-1: Mark-and-sweep VFS evaluation
**Source:** runtime-vfs-effects-integration.md Task 2 (lines 56-68)
**Requirement:** Evaluator executes expressions in topo order, respecting marks for obs
**Evidence Required:**
- [ ] VFS evaluator module (file:line)
- [ ] Topological sort execution
- [ ] Mark-and-sweep vs eager modes
- [ ] Tests (8-10 evaluator tests)

### RUN-2: Item VFS observations
**Source:** runtime-vfs-effects-integration.md Task 3 (lines 79-81)
**Requirement:** Non-zero item VFS in observations with proper dimensions
**Evidence Required:**
- [ ] Item VFS slices in obs vector
- [ ] Correct dimensions per profile
- [ ] Masking for empty slots
- [ ] Tests (5-7 obs tests)

### RUN-3: Compiled catalog usage
**Source:** runtime-vfs-effects-integration.md Task 4 (lines 86-95)
**Requirement:** No runtime YAML rebuild, use CompiledUniverse catalogs
**Evidence Required:**
- [ ] env uses compiled_effect_catalog
- [ ] env uses compiled_vfs_profiles
- [ ] env uses compiled_item_catalog
- [ ] Grep verification (no runtime YAML reads)
- [ ] Tests (2-3 compiled catalog tests)

### RUN-4: ExecutionContext construction
**Source:** effects-system-design.md Section 7.4 (lines 837-874)
**Requirement:** Context built with bars, vfs, temporal state, managers
**Evidence Required:**
- [ ] Context dataclass (context.py)
- [ ] Context construction in EffectManager.tick
- [ ] All required fields populated
- [ ] Tests (context tests)

### RUN-5: VFS registry reads/writes
**Source:** runtime-vfs-effects-integration.md Task 3 (lines 78-79)
**Requirement:** Registry understands profile-scoped item variables
**Evidence Required:**
- [ ] Profile map in registry
- [ ] read/write methods handle profiles
- [ ] Tests (registry tests)

### RUN-6: ItemManager spawn with profiles
**Source:** runtime-vfs-effects-integration.md Task 3 (lines 76-78)
**Requirement:** spawn_item accepts vfs_profile and initial_state
**Evidence Required:**
- [ ] vfs_profile parameter
- [ ] initial_state parameter (dict keyed by variable name)
- [ ] Profile defaults applied
- [ ] Tests (spawn tests)

### RUN-7: Effects schema from compiled profiles
**Source:** runtime-vfs-effects-integration.md Task 4 (lines 91-94)
**Requirement:** Command schema includes bars + VFS paths from compiled profiles
**Evidence Required:**
- [ ] Schema built from CompiledUniverse
- [ ] self/target paths included
- [ ] Item-scoped paths (self.vfs.*, target.vfs.*)
- [ ] Tests (schema consistency tests)

### RUN-8: Performance target (<5% overhead)
**Source:** runtime-vfs-effects-integration.md Success Criteria (line 148)
**Requirement:** VFS expression evaluation adds <5% overhead to step loop
**Evidence Required:**
- [ ] Profiling benchmarks (file:line)
- [ ] Performance comparison vs baseline
- [ ] Cached ASTs for efficiency

### RUN-9: Checkpoint serialization
**Source:** items-and-vfs-profiles.md Section 6.1 (lines 416-418)
**Requirement:** Include item VFS state in checkpoints
**Evidence Required:**
- [ ] Item VFS in checkpoint save
- [ ] Item VFS in checkpoint load
- [ ] Roundtrip reproducibility tests

### RUN-10: Effect step integration
**Source:** effects-system-design.md Section 7.5 (lines 889-895)
**Requirement:** effect_manager.tick() called each env.step()
**Evidence Required:**
- [ ] tick() called in VectorizedHamletEnv.step
- [ ] Before observations/rewards
- [ ] Tests (integration tests)

### RUN-11: VFS evaluation at runtime
**Source:** items-and-vfs-profiles.md Section 6.1 (lines 406-414)
**Requirement:** Evaluate global → agent → item profiles in dependency order
**Evidence Required:**
- [ ] Evaluation loop in env.step
- [ ] Scope ordering (global first, then agent, then item)
- [ ] Dependency ordering within each scope
- [ ] Tests (evaluation order tests)

### RUN-12: Zero regressions
**Source:** runtime-vfs-effects-integration.md Success Criteria (lines 139-140)
**Requirement:** All 435+ existing tests still pass
**Evidence Required:**
- [ ] CI passing
- [ ] No test skips or xfails added
- [ ] Regression test suite

---

## Category 6: Testing (TEST-*)

### TEST-1: 270+ tests total
**Source:** unified-world-compiler-plan.md Milestone Summary (line 478)
**Requirement:** Comprehensive test coverage across all phases
**Evidence Required:**
- [ ] Phase 1: 60+ tests (expression language)
- [ ] Phase 2: 50+ tests (VFS profiles)
- [ ] Phase 3: 75+ tests (effects)
- [ ] Phase 4: 70+ tests (items)
- [ ] Phase 6: 15+ tests (integration)
- [ ] Total count verification

### TEST-2: Expression parser tests
**Source:** unified-world-compiler-plan.md Phase 1 Task 1.2 (line 130)
**Requirement:** 15-20 parsing tests
**Evidence Required:**
- [ ] Operator precedence tests
- [ ] Parentheses tests
- [ ] All operator types tested
- [ ] Test file location

### TEST-3: Type checker tests
**Source:** unified-world-compiler-plan.md Phase 1 Task 1.3 (line 136)
**Requirement:** 20-25 type validation tests
**Evidence Required:**
- [ ] Path resolution tests
- [ ] Type compatibility tests
- [ ] Error message tests
- [ ] Test file location

### TEST-4: Expression evaluator tests
**Source:** unified-world-compiler-plan.md Phase 1 Task 1.4 (line 142)
**Requirement:** 15-20 evaluation tests
**Evidence Required:**
- [ ] GPU tensor operation tests
- [ ] Context state tests
- [ ] All operators tested
- [ ] Test file location

### TEST-5: VFS profile DTO tests
**Source:** unified-world-compiler-plan.md Phase 2 Task 2.1 (line 186)
**Requirement:** 10-15 DTO tests
**Evidence Required:**
- [ ] Schema validation tests
- [ ] expression XOR initial_value enforcement
- [ ] Reference type tests
- [ ] Test file location

### TEST-6: VFS scoped registry tests
**Source:** unified-world-compiler-plan.md Phase 2 Task 2.2 (line 192)
**Requirement:** 15-20 registry tests
**Evidence Required:**
- [ ] Global/agent/item storage tests
- [ ] Access control tests
- [ ] Test file location

### TEST-7: VFS evaluation tests
**Source:** unified-world-compiler-plan.md Phase 2 Task 2.3 (line 198)
**Requirement:** 15-20 evaluation tests
**Evidence Required:**
- [ ] Topological sort tests
- [ ] Circular dependency detection
- [ ] Expression execution tests
- [ ] Test file location

### TEST-8: VFS observation builder tests
**Source:** unified-world-compiler-plan.md Phase 2 Task 2.4 (line 204)
**Requirement:** 10-15 obs builder tests
**Evidence Required:**
- [ ] Fixed slot allocation tests
- [ ] Masking tests
- [ ] obs_dim stability tests
- [ ] Test file location

### TEST-9: Effects DTO tests
**Source:** unified-world-compiler-plan.md Phase 3 Task 3.1 (line 252)
**Requirement:** 15-20 DTO/catalog tests
**Evidence Required:**
- [ ] EffectDefinitionConfig tests
- [ ] Catalog compilation tests
- [ ] Schema validation tests
- [ ] Test file location

### TEST-10: Command compilation tests
**Source:** unified-world-compiler-plan.md Phase 3 Task 3.2 (line 258)
**Requirement:** 20-25 command compilation tests
**Evidence Required:**
- [ ] Command parsing tests
- [ ] Expression compilation tests
- [ ] Type checking tests
- [ ] Test file location

### TEST-11: Command execution tests
**Source:** unified-world-compiler-plan.md Phase 3 Task 3.3 (line 264)
**Requirement:** 20-25 execution tests
**Evidence Required:**
- [ ] All command types tested
- [ ] Path resolution tests
- [ ] GPU tensor mutation tests
- [ ] Test file location

### TEST-12: EffectManager tests
**Source:** unified-world-compiler-plan.md Phase 3 Task 3.4 (line 271)
**Requirement:** 15-20 manager tests
**Evidence Required:**
- [ ] Lifecycle tests (spawn/tick/despawn)
- [ ] Reapply policy tests (stack/renew/merge/replace)
- [ ] Scoped storage tests
- [ ] Test file location

### TEST-13: Effects integration tests
**Source:** unified-world-compiler-plan.md Phase 3 Task 3.5 (line 277)
**Requirement:** 5-10 integration tests
**Evidence Required:**
- [ ] Environment wiring tests
- [ ] effect_manager.tick() tests
- [ ] effects_smoke tests
- [ ] Test file location

### TEST-14: Items DTO tests
**Source:** unified-world-compiler-plan.md Phase 4 Task 4.1 (line 330)
**Requirement:** 15-20 DTO tests
**Evidence Required:**
- [ ] ItemTypeConfig tests
- [ ] ItemSpawnRuleConfig tests
- [ ] Experiment vs level split tests
- [ ] Test file location

### TEST-15: ItemManager tests
**Source:** unified-world-compiler-plan.md Phase 4 Task 4.2 (line 338)
**Requirement:** 20-25 manager tests
**Evidence Required:**
- [ ] Spawn/despawn tests
- [ ] Lifecycle tests (duration/cooldown)
- [ ] Item VFS state tests
- [ ] Test file location

### TEST-16: Inventory tests
**Source:** unified-world-compiler-plan.md Phase 4 Task 4.3 (line 344)
**Requirement:** 15-20 inventory tests
**Evidence Required:**
- [ ] Pickup/drop tests
- [ ] Overflow policy tests
- [ ] Slot management tests
- [ ] Test file location

### TEST-17: Item action handler tests
**Source:** unified-world-compiler-plan.md Phase 4 Task 4.4 (line 351)
**Requirement:** 15-20 action handler tests
**Evidence Required:**
- [ ] GET action tests
- [ ] USE_SLOT_N tests
- [ ] DROP_SLOT_N tests
- [ ] Action masking tests
- [ ] Test file location

### TEST-18: Items integration tests
**Source:** unified-world-compiler-plan.md Phase 4 Task 4.5 (line 358)
**Requirement:** 5-10 integration tests
**Evidence Required:**
- [ ] ItemManager wiring tests
- [ ] Items in observations tests
- [ ] items_smoke tests
- [ ] Test file location

### TEST-19: Complete pipeline tests
**Source:** unified-world-compiler-plan.md Phase 6 Task 6.1 (lines 441-445)
**Requirement:** 10-15 integration tests
**Evidence Required:**
- [ ] Full compilation pipeline test
- [ ] Expression → VFS → Effects flow
- [ ] Items → Effects → Cascades chain
- [ ] All curriculum levels test
- [ ] Test file location

### TEST-20: Performance validation
**Source:** unified-world-compiler-plan.md Phase 6 Task 6.2 (lines 447-451)
**Requirement:** <5% regression benchmark
**Evidence Required:**
- [ ] Benchmark scripts
- [ ] Profiling data
- [ ] Performance comparison
- [ ] Documentation of characteristics

### TEST-21: Runtime integration tests (new)
**Source:** runtime-vfs-effects-integration.md Task 5 (lines 96-121)
**Requirement:** 5-10 integration tests for runtime wiring
**Evidence Required:**
- [ ] Expression execution test
- [ ] Item VFS in obs test
- [ ] Compiled catalog usage test
- [ ] Test file location

### TEST-22: Test config packs
**Source:** items-and-vfs-profiles.md Section 8.2 (lines 523-528)
**Requirement:** Dedicated test configs (items_smoke, effects_smoke, vfs_smoke)
**Evidence Required:**
- [ ] configs/test/items_smoke/ exists
- [ ] configs/test/effects_smoke/ exists
- [ ] configs/test/vfs_smoke/ exists
- [ ] Used in integration tests

---

## Category 7: Documentation (DOC-*)

### DOC-1: Expression language reference
**Source:** unified-world-compiler-plan.md Phase 6 Task 6.3 (line 455)
**Requirement:** Complete docs/config-schemas/expressions.md with all operators
**Evidence Required:**
- [ ] File exists
- [ ] All operators documented
- [ ] Examples for each operator type
- [ ] Syntax reference

### DOC-2: VFS profiles schema docs
**Source:** unified-world-compiler-plan.md Phase 6 Task 6.3 (line 456)
**Requirement:** docs/config-schemas/vfs-profiles.md
**Evidence Required:**
- [ ] File exists
- [ ] Global/agent/item profiles explained
- [ ] Dependency examples
- [ ] Observation mapping

### DOC-3: Effects catalog schema docs
**Source:** unified-world-compiler-plan.md Phase 6 Task 6.3 (line 457)
**Requirement:** docs/config-schemas/effects.md
**Evidence Required:**
- [ ] File exists
- [ ] All command types documented
- [ ] Reapply policies explained
- [ ] Lifecycle hooks documented

### DOC-4: Items schema docs
**Source:** unified-world-compiler-plan.md Phase 6 Task 6.3 (line 458), items-and-vfs-profiles.md Section 7.2 (lines 485-494)
**Requirement:** docs/config-schemas/items.md
**Evidence Required:**
- [ ] File exists
- [ ] Experiment vs level split explained
- [ ] Spawn rules documented
- [ ] Interaction commands documented

### DOC-5: World Compiler user guide
**Source:** unified-world-compiler-plan.md Phase 6 Task 6.3 (line 459)
**Requirement:** docs/guides/world-compiler-guide.md
**Evidence Required:**
- [ ] File exists
- [ ] End-to-end workflow
- [ ] Common patterns
- [ ] Troubleshooting

### DOC-6: Reference config updates
**Source:** items-and-vfs-profiles.md Section 7.1 (lines 473-481)
**Requirement:** reference-config-v2.1-complete.yaml includes vfs_profiles and items sections
**Evidence Required:**
- [ ] vfs_profiles section with examples
- [ ] items section with spawn rules
- [ ] Annotated examples

### DOC-7: Migration guide
**Source:** unified-world-compiler-plan.md Phase 5 (line 569)
**Requirement:** Migration guide for affordances
**Evidence Required:**
- [ ] File exists (or section in guide)
- [ ] Before/after examples
- [ ] Automated migration script

### DOC-8: VFS integration guide updates
**Source:** items-and-vfs-profiles.md Section 0 (line 16)
**Requirement:** Update docs/vfs-integration-guide.md
**Evidence Required:**
- [ ] Profiles section added
- [ ] Runtime evaluation explained
- [ ] Breaking changes documented

### DOC-9: Edge case policies
**Source:** unified-world-compiler-plan.md Related Documentation (line 738)
**Requirement:** docs/plans/vfs_uplift/edge-case-policies.md
**Evidence Required:**
- [ ] File exists
- [ ] DENY_PICKUP policy documented
- [ ] Other edge cases covered

### DOC-10: Observation management modes
**Source:** items-and-vfs-profiles.md Section 6.3 (lines 438-467)
**Requirement:** Document full_auto, max_compact, full_manual modes
**Evidence Required:**
- [ ] Modes explained in docs
- [ ] Trade-offs documented
- [ ] Selection guide provided

---

## Category 8: Breaking Changes (BREAK-*)

### BREAK-1: vfs_profiles.yaml required
**Source:** runtime-vfs-effects-integration.md Breaking Changes (lines 155-157)
**Requirement:** Items with VFS state require vfs_profiles.yaml
**Evidence Required:**
- [ ] Compiler error when items reference vfs_profile without profiles
- [ ] Migration guide section
- [ ] All config packs updated

### BREAK-2: variables_reference.yaml no item scope
**Source:** runtime-vfs-effects-integration.md Breaking Changes (lines 159-161)
**Requirement:** Item-scoped variables rejected in variables_reference.yaml
**Evidence Required:**
- [ ] Schema validation forbids item scope
- [ ] Error message guides to vfs_profiles.yaml
- [ ] Grep verification (no item vars in variables_reference)

### BREAK-3: Effect catalog compiled
**Source:** runtime-vfs-effects-integration.md Breaking Changes (lines 163-165)
**Requirement:** No runtime YAML rebuild
**Evidence Required:**
- [ ] CompiledUniverse contains effect_catalog
- [ ] No runtime EffectCatalog construction
- [ ] Grep verification

### BREAK-4: Item instances require vfs_profile
**Source:** runtime-vfs-effects-integration.md Breaking Changes (lines 167-168)
**Requirement:** vfs_profile must match vfs_profiles.yaml entry
**Evidence Required:**
- [ ] Validation in spawn_item
- [ ] Clear error on missing profile
- [ ] Tests (profile validation)

### BREAK-5: EffectPipeline deleted
**Source:** unified-world-compiler-plan.md Phase 5 (lines 370-410)
**Requirement:** src/townlet/config/effect_pipeline.py removed
**Evidence Required:**
- [ ] File deleted (grep verification)
- [ ] All affordances migrated to Effects
- [ ] Zero imports of EffectPipeline

### BREAK-6: max_items_per_agent required
**Source:** items-and-vfs-profiles.md Section 3.2 (line 185)
**Requirement:** No implicit inventory caps
**Evidence Required:**
- [ ] Field required in InventoryConfig
- [ ] Compiler error on missing field
- [ ] All configs specify value

### BREAK-7: No behavioral defaults
**Source:** items-and-vfs-profiles.md Section 4.1 (lines 299-303)
**Requirement:** duration, cooldown, limits, schedule params all required
**Evidence Required:**
- [ ] Pydantic Field() without defaults
- [ ] Compiler errors on missing fields
- [ ] Reference config shows explicit values

### BREAK-8: reapply_policy required
**Source:** effects-system-design.md Section 2.1 (line 83)
**Requirement:** No default reapply policy
**Evidence Required:**
- [ ] Field required in EffectDefinitionConfig
- [ ] Compiler error on missing field
- [ ] All effects specify policy

### BREAK-9: Observation dimension changes
**Source:** runtime-vfs-effects-integration.md Risk Assessment (lines 205-207)
**Requirement:** Adding item VFS may break checkpoint compatibility
**Evidence Required:**
- [ ] Documentation of dimension changes
- [ ] Migration guide for checkpoints
- [ ] Acceptable (pre-release, zero users)

---

## Summary Statistics

**By Category:**
- Compiler (COMP-*): 20 requirements
- VFS System (VFS-*): 15 requirements
- Effects System (EFF-*): 20 requirements
- Items System (ITEM-*): 16 requirements
- Runtime Integration (RUN-*): 12 requirements
- Testing (TEST-*): 22 requirements
- Documentation (DOC-*): 10 requirements
- Breaking Changes (BREAK-*): 9 requirements

**Total:** 124 requirements (+ 33 derived from success criteria) = **157 total requirements**

---

## Cross-Cutting Concerns

### Error Handling Requirements
- COMP-9, COMP-12, COMP-13: Compile-time path validation
- COMP-18: Required field validation
- COMP-17: Reference validation
- EFF-15: Type safety
- BREAK-1, BREAK-2, BREAK-4: Clear migration errors

### Type Safety Requirements
- COMP-9: Expression type checking
- EFF-15: Command value type validation
- VFS-14: Primitive type system
- VFS-12: Tensor type system
- EFF-14: Expression type integration

### Performance Requirements
- RUN-8: <5% overhead target
- TEST-20: Performance benchmarking
- VFS-6: Mark-and-sweep optimization
- VFS-14: Fixed slot allocation (not dynamic)

### Pedagogical Requirements
- Items-VFS integration (clean from day 1, no opaque dicts)
- Expression language unified across VFS/Effects/DAC
- Type system prevents invalid configurations
- Clear error messages guide users

---

## Notes for Gap Analysis

**High-Risk Areas (verify first):**
1. Runtime VFS evaluation (RUN-1, VFS-6) - mark-and-sweep vs eager
2. Item VFS observations (RUN-2, VFS-10) - zero stubs vs real data
3. Compiled catalog usage (RUN-3, COMP-3) - runtime rebuilds
4. Expression performance (RUN-8, TEST-20) - overhead measurement

**Verification Strategy:**
1. **Code search:** Grep for key patterns (variables_reference.yaml reads, EffectCatalog construction)
2. **Test coverage:** Count tests per category, verify test files exist
3. **Schema validation:** Check all DTOs enforce no-defaults principle
4. **Integration points:** Verify env.step() calls effect_manager.tick(), VFS evaluator

**Documentation Priority:**
1. Expression language reference (DOC-1) - foundation for all systems
2. Migration guides (DOC-7, BREAK-* sections) - user-facing breakage
3. Schema docs (DOC-2, DOC-3, DOC-4) - config authoring
