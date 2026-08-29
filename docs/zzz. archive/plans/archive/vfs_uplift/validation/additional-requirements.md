# Additional VFS Uplift Requirements

**Generated:** 2025-11-23
**Source Analysis:** 5 VFS uplift plan documents
**Purpose:** Gap analysis - requirements NOT in requirements-checklist.md (157 existing)
**New Requirements:** 89

---

## Category: CMD (Command-Specific Implementation)

### CMD-SWITCH-1: Equality-based matching
**Source:** command_reference.md lines 99-142
**Requirement:** Switch command uses equality matching only (not pattern matching or boolean guards)
**Evidence Required:**
- [ ] Switch evaluates expression once
- [ ] Cases compared using equality operator
- [ ] First matching case executes
- [ ] Default branch runs if no match
- [ ] Tests (equality matching, no-match default, type compatibility)

### CMD-SWITCH-2: Type validation
**Source:** command_reference.md lines 117-120
**Requirement:** All `when` expressions must be comparable to switch expression type
**Evidence Required:**
- [ ] Compile-time type checking of cases
- [ ] Error on type mismatch (e.g., comparing int to string)
- [ ] Tests (type mismatch rejection)

### CMD-SWITCH-3: Tensor broadcasting
**Source:** command_reference.md lines 123-125
**Requirement:** Switch supports scalar and tensor comparisons with broadcasting
**Evidence Required:**
- [ ] Scalar switch expressions work
- [ ] Tensor switch expressions work
- [ ] Broadcasting rules followed
- [ ] Tests (scalar, tensor, broadcast cases)

### CMD-FOREACH-1: Iteration cap enforcement
**Source:** command_reference.md lines 82-83
**Requirement:** MAX_COLLECTION_SIZE = 256, enforced at compile-time if size known, runtime otherwise
**Evidence Required:**
- [ ] Constant MAX_COLLECTION_SIZE = 256
- [ ] Compile-time size validation for static lists
- [ ] Runtime size validation for dynamic collections
- [ ] Fail fast with clear error on cap violation
- [ ] Tests (size=256 allowed, size=257 rejected)

### CMD-FOREACH-2: Nested for_each prohibition
**Source:** command_reference.md lines 76-77
**Requirement:** Compiler rejects nested for_each until vectorized semantics defined
**Evidence Required:**
- [ ] Compile-time check for nesting
- [ ] Clear error message explaining limitation
- [ ] Tests (nested for_each rejection)

### CMD-FOREACH-3: Iterator scope isolation
**Source:** command_reference.md lines 77-78
**Requirement:** Iterator variable scoped only to `do` block, not available outside
**Evidence Required:**
- [ ] Symbol table scope management
- [ ] Iterator unavailable after for_each
- [ ] Tests (scope isolation)

### CMD-FOREACH-4: Resolver signatures
**Source:** command_reference.md lines 83-87
**Requirement:** Specific resolver functions with typed returns
**Evidence Required:**
- [ ] `all_agents()` returns iterable[int]
- [ ] `nearby_agents(radius: float)` returns iterable[int]
- [ ] `inventory_items()` returns iterable[int]
- [ ] `active_effects()` returns iterable[int]
- [ ] Tests (each resolver function)

### CMD-FOREACH-5: No break/continue
**Source:** command_reference.md lines 74
**Requirement:** for_each iterates entire collection, no early exit
**Evidence Required:**
- [ ] Full iteration guaranteed
- [ ] No break/continue commands
- [ ] Tests (full iteration verification)

### CMD-PARALLEL-1: Disjoint-write validation
**Source:** command_reference.md lines 183-199
**Requirement:** Compiler enforces parallel branches write to different targets
**Evidence Required:**
- [ ] Static analysis of write targets
- [ ] Compile error on overlapping writes
- [ ] Tests (disjoint writes allowed, overlapping rejected)

### CMD-PARALLEL-2: Sequential execution with original context
**Source:** command_reference.md lines 189-200
**Requirement:** Branches execute sequentially but see same input context
**Evidence Required:**
- [ ] Branches execute in order listed
- [ ] Each branch sees pre-parallel context state
- [ ] Mutations from branch N don't affect branch N+1's inputs
- [ ] Tests (context isolation)

### CMD-PARALLEL-3: Empty branch rejection
**Source:** command_reference.md lines 196
**Requirement:** Parallel command requires at least one branch
**Evidence Required:**
- [ ] Validation error on empty parallel
- [ ] Tests (empty parallel rejection)

### CMD-REDUCE-1: Fixed-size collection constraint
**Source:** command_reference.md lines 219-236
**Requirement:** Reduce only accepts fixed-size tensors or lists, no ragged/unknown-length
**Evidence Required:**
- [ ] Type checker enforces list or tensor
- [ ] Runtime rejects ragged collections
- [ ] Tests (fixed-size allowed, ragged rejected)

### CMD-REDUCE-2: Accumulator type consistency
**Source:** command_reference.md lines 233-234
**Requirement:** Accumulator type inferred from init, must match across iterations and into target
**Evidence Required:**
- [ ] Type inference from reduce_init
- [ ] Type checking of reduce_body return
- [ ] Type checking of reduce_into target
- [ ] Tests (type consistency, type mismatch rejection)

### CMD-REDUCE-3: All fields required
**Source:** command_reference.md lines 238-239
**Requirement:** collection, reduce_as, reduce_init, reduce_body, reduce_into all required (no defaults)
**Evidence Required:**
- [ ] Pydantic schema with no defaults
- [ ] Validation error on missing fields
- [ ] Tests (missing field rejection)

### CMD-DELAY-1: time_enabled requirement
**Source:** command_reference.md lines 260-268
**Requirement:** Delay command requires time_enabled: true, compilation fails otherwise
**Evidence Required:**
- [ ] Compile-time check of time_enabled flag
- [ ] Clear error when time disabled
- [ ] Tests (delay with time_enabled=false rejected)

### CMD-DELAY-2: Delay limits
**Source:** command_reference.md lines 270-272
**Requirement:** MAX_DELAY_TICKS = 1,000, ticks expression must be >= 0 and <= MAX_DELAY_TICKS
**Evidence Required:**
- [ ] Constant MAX_DELAY_TICKS = 1000
- [ ] Validation of ticks range
- [ ] Tests (valid range allowed, out-of-range rejected)

### CMD-DELAY-3: Scheduler queue cap
**Source:** command_reference.md lines 272-273
**Requirement:** MAX_SCHEDULED_ITEMS = 10,000, runtime queue cap enforced
**Evidence Required:**
- [ ] Constant MAX_SCHEDULED_ITEMS = 10000
- [ ] Runtime queue size tracking
- [ ] Error on queue overflow
- [ ] Tests (queue cap enforcement)

### CMD-DELAY-4: Zero-delay semantics
**Source:** command_reference.md lines 277-278
**Requirement:** Zero-delay executes after current command completes but within same tick
**Evidence Required:**
- [ ] Scheduler processes zero-delay in same tick
- [ ] Execution order: current command → zero-delay commands → next tick
- [ ] Tests (zero-delay timing)

### CMD-DELAY-5: Scheduler persistence
**Source:** command_reference.md lines 276-277
**Requirement:** Scheduler persists commands across ticks, executes at correct time
**Evidence Required:**
- [ ] Commands survive across ticks
- [ ] Execution at exact scheduled tick
- [ ] Tests (multi-tick delay)

### CMD-WHILE-1: Status - not implemented
**Source:** command_reference.md lines 144-174
**Requirement:** While command planned but not yet implemented
**Evidence Required:**
- [ ] Command not in executor
- [ ] Documentation marks as future work
- [ ] No tests for while (or all skipped)

### CMD-EMIT-1: Status - not implemented
**Source:** command_reference.md lines 292-316
**Requirement:** Emit command planned but not yet implemented
**Evidence Required:**
- [ ] Command not in executor
- [ ] Documentation marks as future work
- [ ] No tests for emit (or all skipped)

---

## Category: LIMITS (Runtime Limits & Safeguards)

### LIMITS-1: Collection size cap
**Source:** command_reference.md line 326
**Requirement:** MAX_COLLECTION_SIZE = 256 enforced globally for all iterations
**Evidence Required:**
- [ ] Constant defined and documented
- [ ] Applied to for_each
- [ ] Applied to reduce
- [ ] Tests (at limit, over limit)

### LIMITS-2: Effect spawn depth cap
**Source:** effects-system-design.md Section 10.3 (lines 1204-1212)
**Requirement:** max_depth = 10 for effect spawning to prevent infinite recursion
**Evidence Required:**
- [ ] Depth tracking in spawn_effect
- [ ] Runtime error on depth exceeded
- [ ] Compiler warning for recursive effect references
- [ ] Tests (depth=10 allowed, depth=11 rejected)

### LIMITS-3: Delay ticks cap
**Source:** command_reference.md line 329
**Requirement:** MAX_DELAY_TICKS = 1,000
**Evidence Required:**
- [ ] Applied to delay command
- [ ] Documented limit
- [ ] Tests (enforcement)

### LIMITS-4: Scheduled items queue cap
**Source:** command_reference.md line 329
**Requirement:** MAX_SCHEDULED_ITEMS = 10,000 for scheduler queue
**Evidence Required:**
- [ ] Queue size tracking
- [ ] Overflow handling
- [ ] Tests (queue full behavior)

### LIMITS-5: Item pool allocation cap
**Source:** items-and-vfs-profiles.md Section 9, unified-world-compiler-plan.md D3
**Requirement:** Pre-allocated max_items pool with reasonable limits (e.g., 1000 items)
**Evidence Required:**
- [ ] max_items configuration parameter
- [ ] Validation of reasonable limits
- [ ] Memory allocation sizing
- [ ] Tests (allocation limits)

### LIMITS-6: VFS profile count limits
**Source:** items-and-vfs-profiles.md Section 8.2 (line 541)
**Requirement:** Compiler enforces reasonable limits on profile counts
**Evidence Required:**
- [ ] Validation of profile counts
- [ ] Clear error on excessive profiles
- [ ] Tests (reasonable count allowed, excessive rejected)

### LIMITS-7: Item spawn rule limits
**Source:** items-and-vfs-profiles.md Section 8.2 (line 541)
**Requirement:** Compiler enforces reasonable limits on spawn rules count
**Evidence Required:**
- [ ] Validation of spawn rule counts
- [ ] Clear error on excessive rules
- [ ] Tests (limit enforcement)

---

## Category: VFS-EXT (VFS Extensions)

### VFS-EXT-1: Expression XOR initial_value enforcement
**Source:** items-and-vfs-profiles.md Section 3.3 (line 232), unified-world-compiler-plan.md Phase 2 Task 2.1
**Requirement:** VFS profile must have expression OR initial_value, not both, not neither
**Evidence Required:**
- [ ] Pydantic validator enforces XOR
- [ ] Error on both present
- [ ] Error on neither present
- [ ] Tests (valid cases, invalid cases)

### VFS-EXT-2: Update rule DSL (future)
**Source:** items-and-vfs-profiles.md Section 3.3 (lines 264-267)
**Requirement:** Expression DSL execution deferred to BAC Phase 2+, treated as metadata in Phase 1
**Evidence Required:**
- [ ] Expression field accepted in schema
- [ ] Not executed in Phase 1
- [ ] Validation mode (accept but warn/ignore)
- [ ] Tests (expression accepted, not evaluated)

### VFS-EXT-3: Observation exposure control
**Source:** items-and-vfs-profiles.md Section 3.3 (lines 235-238)
**Requirement:** VFS profiles specify exposed_to field (which scopes can observe)
**Evidence Required:**
- [ ] exposed_to field in profile config
- [ ] Observation builder respects exposure
- [ ] Tests (exposure enforcement)

### VFS-EXT-4: Semantic type metadata
**Source:** items-and-vfs-profiles.md Section 3.3 (lines 237-238)
**Requirement:** VFS profiles include semantic_type field (temporal, custom, etc.)
**Evidence Required:**
- [ ] semantic_type field in schema
- [ ] Metadata carried through compilation
- [ ] Tests (semantic types preserved)

### VFS-EXT-5: Profile ID stability
**Source:** items-and-vfs-profiles.md Section 3.3 (line 265)
**Requirement:** Profile IDs stable across experiment, used for mapping
**Evidence Required:**
- [ ] ID uniqueness validation
- [ ] ID stability across levels
- [ ] Tests (ID conflicts rejected)

### VFS-EXT-6: Dependency tracking
**Source:** items-and-vfs-profiles.md Section 3.3 (lines 232-234)
**Requirement:** Profiles declare deps (bars, vfs, affordances)
**Evidence Required:**
- [ ] deps field in schema
- [ ] Dependency resolution
- [ ] Tests (dependency tracking)

### VFS-EXT-7: Evaluation ordering
**Source:** items-and-vfs-profiles.md Section 6.1 (lines 407-413)
**Requirement:** Evaluate global → agent → item profiles in scope order
**Evidence Required:**
- [ ] Scope evaluation sequence
- [ ] Within-scope topological order
- [ ] Tests (evaluation order)

### VFS-EXT-8: Item profile defaults
**Source:** runtime-vfs-effects-integration.md Task 3 (line 77)
**Requirement:** Profile defaults applied when item spawned without initial_state
**Evidence Required:**
- [ ] Default value initialization
- [ ] initial_state overrides defaults
- [ ] Tests (defaults applied, overrides work)

---

## Category: ITEM-EXT (Items Extensions)

### ITEM-EXT-1: Placement modes
**Source:** items-and-vfs-profiles.md Section 3.2 (lines 189-191)
**Requirement:** Support random, fixed, grid, scripted placement modes
**Evidence Required:**
- [ ] All modes implemented
- [ ] positions field required for fixed/scripted
- [ ] Tests (each mode)

### ITEM-EXT-2: Schedule types
**Source:** items-and-vfs-profiles.md Section 3.2 (lines 192-194)
**Requirement:** Support time_window, poisson, normal, once schedule kinds
**Evidence Required:**
- [ ] All schedule kinds implemented
- [ ] params field validated per kind
- [ ] Tests (each schedule type)

### ITEM-EXT-3: Spawn limits enforcement
**Source:** items-and-vfs-profiles.md Section 3.2 (lines 195-196)
**Requirement:** max_simultaneous and max_total limits enforced
**Evidence Required:**
- [ ] Limit tracking in ItemManager
- [ ] Spawn blocked when limit reached
- [ ] Tests (limit enforcement)

### ITEM-EXT-4: Spawn priority
**Source:** items-and-vfs-profiles.md Section 3.2 (line 197)
**Requirement:** Priority field controls spawn order when multiple items eligible
**Evidence Required:**
- [ ] Priority sorting in scheduler
- [ ] Higher priority spawns first
- [ ] Tests (priority ordering)

### ITEM-EXT-5: Conditional spawn with VFS predicates
**Source:** items-and-vfs-profiles.md Section 3.2 (lines 200-203)
**Requirement:** Spawn conditions reference global VFS (when: "vfs:is_raining")
**Evidence Required:**
- [ ] Condition parsing
- [ ] VFS predicate evaluation
- [ ] Spawn gating by condition
- [ ] Tests (conditional spawn)

### ITEM-EXT-6: Item tags
**Source:** items-and-vfs-profiles.md Section 3.2 (line 152)
**Requirement:** Items have tags field for categorization
**Evidence Required:**
- [ ] tags field in ItemTypeConfig
- [ ] Tags available in expressions (nearest_item(tag="food"))
- [ ] Tests (tag filtering)

### ITEM-EXT-7: Item visual metadata
**Source:** items-and-vfs-profiles.md Section 2.2 (lines 85-86)
**Requirement:** Items have icon, labels metadata for UI
**Evidence Required:**
- [ ] icon field (emoji or icon name)
- [ ] name field
- [ ] Metadata in compiled catalog
- [ ] Tests (metadata preservation)

### ITEM-EXT-8: Holder agent tracking
**Source:** effects-system-design.md Section 2.3 (line 157)
**Requirement:** Item instances track holder_agent_id (null when on ground)
**Evidence Required:**
- [ ] holder_agent_id field on ItemInstance
- [ ] Updated on pickup/drop
- [ ] Available in expressions (target.holder_agent)
- [ ] Tests (holder tracking)

### ITEM-EXT-9: Item durability/charges
**Source:** effects-system-design.md Section 8.5 (lines 1029-1032)
**Requirement:** Items can have durability/charges via item VFS, delete when exhausted
**Evidence Required:**
- [ ] Item VFS profiles for durability
- [ ] Decrement on use
- [ ] Delete when reaches zero
- [ ] Tests (durability consumption)

### ITEM-EXT-10: Item spoilage/decay
**Source:** effects-system-design.md Section 8.5 (lines 1048-1053)
**Requirement:** Items can have decay effects that modify item VFS over time
**Evidence Required:**
- [ ] item_decay effect type
- [ ] Effect modifies item VFS (e.g., spoilage)
- [ ] Tests (decay over time)

### ITEM-EXT-11: Item-scoped local commands
**Source:** items-and-vfs-profiles.md Section 3.2 (lines 162-174)
**Requirement:** Items can define local_commands (range-based) and inventory_commands (held only)
**Evidence Required:**
- [ ] local_commands field in interactions
- [ ] inventory_commands field in interactions
- [ ] Action masking based on range/inventory
- [ ] Tests (command availability)

### ITEM-EXT-12: Exclusive vs shared items
**Source:** items-and-vfs-profiles.md Section 2.2 (lines 81-82)
**Requirement:** Items can be exclusive (single holder) or shared (environmental)
**Evidence Required:**
- [ ] exclusivity field or policy
- [ ] Single-holder enforcement for exclusive items
- [ ] Tests (exclusivity enforcement)

### ITEM-EXT-13: Fixed item positions
**Source:** items-and-vfs-profiles.md Section 2.2 (line 76)
**Requirement:** Items can be placed at fixed coordinates
**Evidence Required:**
- [ ] Fixed placement mode
- [ ] positions field with coordinates
- [ ] Tests (fixed placement)

### ITEM-EXT-14: Random item positions
**Source:** items-and-vfs-profiles.md Section 2.2 (line 77)
**Requirement:** Items can be placed randomly under constraints
**Evidence Required:**
- [ ] Random placement mode
- [ ] Constraint parameters (bounds, avoid obstacles)
- [ ] Tests (random placement)

### ITEM-EXT-15: Item instance ID tracking
**Source:** items-and-vfs-profiles.md Section 5.1 (line 344)
**Requirement:** Each ItemInstance has unique id and type_id
**Evidence Required:**
- [ ] id field (unique instance ID)
- [ ] type_id field (references catalog)
- [ ] ID uniqueness guaranteed
- [ ] Tests (ID tracking)

### ITEM-EXT-16: Item spawn timing
**Source:** items-and-vfs-profiles.md Section 5.1 (lines 347-349)
**Requirement:** ItemInstance tracks spawn_step, expire_step, cooldown_until_step
**Evidence Required:**
- [ ] spawn_step field
- [ ] expire_step field (null if infinite)
- [ ] cooldown_until_step field
- [ ] Tests (timing enforcement)

---

## Category: COMP-EXT (Compiler Extensions)

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

## Category: EFF-EXT (Effects Extensions)

### EFF-EXT-1: Effect on_interrupt hook
**Source:** effects-system-design.md Section 2.1 (line 105)
**Requirement:** Optional on_interrupt lifecycle hook for forcibly removed effects
**Evidence Required:**
- [ ] on_interrupt field in EffectDef
- [ ] Executed when effect forcibly removed
- [ ] Tests (interrupt handling)

### EFF-EXT-2: Observable effects in observations (future)
**Source:** effects-system-design.md Section 10.1 (lines 1154-1176)
**Requirement:** Deferred to VFS Profiles integration - effects write to VFS variables
**Evidence Required:**
- [ ] Design decision documented
- [ ] Effects write to VFS for observability
- [ ] Not using fixed effect slots
- [ ] Tests (effects via VFS)

### EFF-EXT-3: Affordance availability masking
**Source:** effects-system-design.md Section 10.2 (lines 1178-1201)
**Requirement:** Effects can modify affordance.available via commands
**Evidence Required:**
- [ ] Path support for affordance.available
- [ ] Effects can set availability
- [ ] Tests (affordance masking)

### EFF-EXT-4: Cascade triggering
**Source:** effects-system-design.md Section 3.4 (lines 261-265)
**Requirement:** trigger_cascade command activates cascade rules manually
**Evidence Required:**
- [ ] trigger_cascade command
- [ ] cascade_id parameter
- [ ] strength_multiplier parameter
- [ ] Integration with cascade system
- [ ] Tests (manual cascade trigger)

### EFF-EXT-5: Event emission (future)
**Source:** effects-system-design.md Section 3.4 (lines 254-259)
**Requirement:** emit_event command for event observers/logging/analytics
**Evidence Required:**
- [ ] emit_event command (or marked future)
- [ ] Event bus integration
- [ ] Tests (event emission)

### EFF-EXT-6: Sample command with weights
**Source:** effects-system-design.md Section 3.5 (lines 277-285)
**Requirement:** Sample from list with probability distribution
**Evidence Required:**
- [ ] sample command
- [ ] from parameter (list)
- [ ] weights parameter (optional)
- [ ] assign_to parameter
- [ ] Tests (sampling, weighted sampling)

### EFF-EXT-7: Random chance conditionals
**Source:** effects-system-design.md Section 3.5 (lines 270-275)
**Requirement:** random() function in expressions for probabilistic behavior
**Evidence Required:**
- [ ] random() function
- [ ] Returns value in [0, 1)
- [ ] Used in if conditions
- [ ] Tests (random conditionals)

### EFF-EXT-8: Effect metadata in catalog
**Source:** effects-system-design.md Section 2.1 (lines 69-106)
**Requirement:** Effect catalog includes scope, duration, intensity, reapply_policy, observable
**Evidence Required:**
- [ ] All metadata fields in CompiledEffect
- [ ] Metadata accessible at runtime
- [ ] Tests (metadata preservation)

---

## Category: RUN-EXT (Runtime Extensions)

### RUN-EXT-1: Eager fallback mode
**Source:** unified-world-compiler-plan.md D2 (lines 606-607), runtime-vfs-effects-integration.md Task 2
**Requirement:** eval_mode="eager" flag as escape hatch from mark-and-sweep
**Evidence Required:**
- [ ] eval_mode configuration option
- [ ] Eager evaluates all variables
- [ ] Mark-and-sweep is default
- [ ] Tests (mode switching)

### RUN-EXT-2: VFS evaluation context
**Source:** runtime-vfs-effects-integration.md Task 2 (lines 65-67)
**Requirement:** Expression evaluation context has bars + VFS dictionaries with self/target
**Evidence Required:**
- [ ] Context includes bars tensor
- [ ] Context includes vfs_global, vfs_agent, vfs_item
- [ ] self/target support
- [ ] Tests (context completeness)

### RUN-EXT-3: Item VFS masking
**Source:** runtime-vfs-effects-integration.md Task 3 (line 80)
**Requirement:** Unused item slots masked in observations
**Evidence Required:**
- [ ] Mask tensor for item slots
- [ ] Mask applied to observations
- [ ] Tests (masking correctness)

### RUN-EXT-4: Profile-driven obs dimensions
**Source:** runtime-vfs-effects-integration.md Task 2 (line 66)
**Requirement:** Observation dimensions computed from compiled profiles
**Evidence Required:**
- [ ] Dimensions match profile count × variables per profile
- [ ] Fixed slot allocation (max_items_per_agent × max_profiles × vars)
- [ ] Tests (dimension calculation)

### RUN-EXT-5: Zero-stub removal
**Source:** runtime-vfs-effects-integration.md Task 5 (line 116)
**Requirement:** Remove zero-stub behavior from observation builder
**Evidence Required:**
- [ ] Non-zero item VFS in observations
- [ ] Actual VFS values populated
- [ ] Tests (real data, not stubs)

### RUN-EXT-6: Instrumentation for debugging
**Source:** items-and-vfs-profiles.md Section 8.2 (lines 553-558)
**Requirement:** Debug flag logs item spawns/despawns, inventory changes, VFS evaluations
**Evidence Required:**
- [ ] Debug flag (debug_items, debug_vfs)
- [ ] Logging of key events
- [ ] Tests (logging output)

### RUN-EXT-7: Assertions on state invariants
**Source:** items-and-vfs-profiles.md Section 8.2 (lines 545-546)
**Requirement:** Runtime assertions for inventory size, VFS index bounds
**Evidence Required:**
- [ ] Assert inventory <= max_items_per_agent
- [ ] Assert VFS indices in bounds
- [ ] Tests (assertions trigger on violations)

---

## Category: TEST-EXT (Testing Extensions)

### TEST-EXT-1: Dimension regression tests
**Source:** items-and-vfs-profiles.md Section 8.2 (lines 530-534)
**Requirement:** Tests derive expected obs layout from metadata and assert dimensions match
**Evidence Required:**
- [ ] Metadata-driven test generation
- [ ] obs_dim matches compiled counts
- [ ] Masking affects masks only, not dimensions
- [ ] Tests (dimension stability)

### TEST-EXT-2: Checkpoint roundtrip tests
**Source:** items-and-vfs-profiles.md Section 6.1 (line 418)
**Requirement:** Save checkpoint → load → verify exact reproduction of item VFS state
**Evidence Required:**
- [ ] Checkpoint save includes item VFS
- [ ] Load restores item VFS exactly
- [ ] Tests (roundtrip verification)

### TEST-EXT-3: Circular dependency tests
**Source:** requirements-checklist.md VFS-13
**Requirement:** VFS dependency graph detects and rejects cycles
**Evidence Required:**
- [ ] Cycle detection implementation
- [ ] Clear error on cycle
- [ ] Tests (cycles rejected, DAGs allowed)

### TEST-EXT-4: Expression operator coverage
**Source:** requirements-checklist.md VFS-1
**Requirement:** 60+ tests covering all operators from VARIABLE_SUBSYSTEM.md
**Evidence Required:**
- [ ] Mathematical operators tested
- [ ] Trigonometric operators tested
- [ ] Temporal operators tested
- [ ] Spatial operators tested
- [ ] Statistical operators tested
- [ ] Stochastic operators tested
- [ ] Tests (complete operator coverage)

### TEST-EXT-5: Type safety negative tests
**Source:** requirements-checklist.md EFF-15
**Requirement:** Tests for compile errors on type mismatches
**Evidence Required:**
- [ ] Scalar → vec2i rejected
- [ ] vec2i → scalar rejected
- [ ] Incompatible type assignments rejected
- [ ] Tests (type mismatch errors)

### TEST-EXT-6: Reapply policy tests
**Source:** requirements-checklist.md EFF-6
**Requirement:** Test each policy (stack, renew, merge, replace) with correct behavior
**Evidence Required:**
- [ ] Stack: independent instances test
- [ ] Renew: duration refresh test
- [ ] Merge: intensity increase test
- [ ] Replace: despawn old, spawn new test
- [ ] Tests (one per policy)

### TEST-EXT-7: Access control violation tests
**Source:** requirements-checklist.md VFS-7
**Requirement:** Tests for VFS registry access control enforcement
**Evidence Required:**
- [ ] Read from unreadable variable rejected
- [ ] Write to read-only variable rejected
- [ ] Tests (access violations)

### TEST-EXT-8: Action masking tests
**Source:** requirements-checklist.md ITEM-5
**Requirement:** Tests for action masking (GET masked when inventory full, etc.)
**Evidence Required:**
- [ ] GET masked when full
- [ ] USE_SLOT_N masked when empty
- [ ] DROP_SLOT_N masked when empty
- [ ] Tests (masking correctness)

---

## Category: DOC-EXT (Documentation Extensions)

### DOC-EXT-1: Command reference
**Source:** command_reference.md (entire file)
**Requirement:** Complete command DSL reference with all implemented and planned commands
**Evidence Required:**
- [ ] docs/config-schemas/command-reference.md or similar
- [ ] All commands documented (modify, spawn_effect, if, for_each, switch, parallel, reduce, delay)
- [ ] Future commands marked (while, emit)
- [ ] Runtime limits section

### DOC-EXT-2: Observation management modes documentation
**Source:** items-and-vfs-profiles.md Section 6.3 (lines 438-467)
**Requirement:** Document full_auto, max_compact, full_manual modes with trade-offs
**Evidence Required:**
- [ ] Mode descriptions
- [ ] Trade-offs explained (obs_dim stability vs size)
- [ ] Selection guide
- [ ] Examples of each mode

### DOC-EXT-3: Edge case policies documentation
**Source:** items-and-vfs-profiles.md Section 5.2 (line 374)
**Requirement:** Document DENY_PICKUP and other edge case policies
**Evidence Required:**
- [ ] DENY_PICKUP policy documented
- [ ] Other overflow policies documented
- [ ] Tests referenced

### DOC-EXT-4: Interaction radius documentation
**Source:** items-and-vfs-profiles.md Section 5.2 (lines 388-393)
**Requirement:** Document interaction_radius for continuous substrates
**Evidence Required:**
- [ ] interaction_radius parameter explained
- [ ] Required for continuous substrates
- [ ] Examples

### DOC-EXT-5: Type system reference
**Source:** effects-system-design.md Section 4 (lines 313-426)
**Requirement:** Complete type system documentation (primitives, references, tensors)
**Evidence Required:**
- [ ] scalar, bool, vec2i, vec3i, vecNi, vecNf documented
- [ ] agent_ref, item_ref, affordance_ref, effect_ref documented
- [ ] tensor1d, tensor2d, tensor3d, tensorNd documented
- [ ] Type checking rules explained

### DOC-EXT-6: Reapply policy examples
**Source:** effects-system-design.md Section 2.2 (lines 110-148)
**Requirement:** Examples showing each reapply policy's behavior
**Evidence Required:**
- [ ] Stack example (independent timers)
- [ ] Renew example (duration refresh)
- [ ] Merge example (intensity stacking)
- [ ] Replace example (single instance)

### DOC-EXT-7: Expression execution context documentation
**Source:** effects-system-design.md Section 5.1 (lines 435-456)
**Requirement:** Document all variables available in expressions
**Evidence Required:**
- [ ] self, target, agent, global documented
- [ ] intensity, duration, duration_remaining, elapsed_ticks documented
- [ ] time_of_day, step_count documented
- [ ] Examples of each

---

## Summary Statistics

**New Requirements by Category:**
- CMD (Command-Specific): 22 requirements
- LIMITS (Runtime Limits): 7 requirements
- VFS-EXT (VFS Extensions): 8 requirements
- ITEM-EXT (Items Extensions): 16 requirements
- COMP-EXT (Compiler Extensions): 8 requirements
- EFF-EXT (Effects Extensions): 8 requirements
- RUN-EXT (Runtime Extensions): 7 requirements
- TEST-EXT (Testing Extensions): 8 requirements
- DOC-EXT (Documentation Extensions): 7 requirements

**Total New Requirements:** 89

**Combined Total:** 157 (existing) + 89 (new) = **246 requirements**

---

## Priority Classification

### P0 (Critical - Implementation Blockers)
- CMD-FOREACH-1: Iteration cap (safety)
- CMD-FOREACH-2: Nested for_each prohibition (safety)
- LIMITS-1, LIMITS-2, LIMITS-3, LIMITS-4: All runtime caps (safety)
- VFS-EXT-1: Expression XOR initial_value (correctness)
- COMP-EXT-6: Expression rejection in variables_reference (breaking change enforcement)
- RUN-EXT-5: Zero-stub removal (correctness)

### P1 (High - Core Functionality)
- CMD-SWITCH-1, CMD-SWITCH-2, CMD-SWITCH-3: Switch implementation
- CMD-PARALLEL-1, CMD-PARALLEL-2: Parallel semantics
- CMD-REDUCE-1, CMD-REDUCE-2, CMD-REDUCE-3: Reduce implementation
- CMD-DELAY-1, CMD-DELAY-2, CMD-DELAY-3, CMD-DELAY-4, CMD-DELAY-5: Delay implementation
- VFS-EXT-7: Evaluation ordering (correctness)
- ITEM-EXT-5: Conditional spawn (core feature)
- RUN-EXT-1: Eager fallback (debugging essential)

### P2 (Medium - Important Features)
- CMD-FOREACH-3, CMD-FOREACH-4, CMD-FOREACH-5: for_each details
- ITEM-EXT-1, ITEM-EXT-2, ITEM-EXT-3, ITEM-EXT-4: Item spawn features
- VFS-EXT-3, VFS-EXT-4, VFS-EXT-5, VFS-EXT-6: VFS metadata
- COMP-EXT-1, COMP-EXT-2, COMP-EXT-3: Compiler wiring
- EFF-EXT-3, EFF-EXT-4, EFF-EXT-6, EFF-EXT-7: Effect commands

### P3 (Low - Polish & Future Work)
- CMD-WHILE-1, CMD-EMIT-1: Not implemented (future)
- ITEM-EXT-12, ITEM-EXT-13, ITEM-EXT-14: Item placement details
- EFF-EXT-1, EFF-EXT-2, EFF-EXT-5: Future hooks
- RUN-EXT-6: Instrumentation (debug)
- All DOC-EXT requirements: Documentation

---

## Gap Analysis Recommendations

### Immediate Validation Needs (Next Week)
1. **Verify runtime caps are enforced** (LIMITS-1 through LIMITS-7)
2. **Check command implementation status** (CMD-SWITCH-*, CMD-PARALLEL-*, CMD-REDUCE-*, CMD-DELAY-*)
3. **Validate VFS expression XOR initial_value** (VFS-EXT-1)
4. **Verify zero-stub removal** (RUN-EXT-5)
5. **Check for nested for_each rejection** (CMD-FOREACH-2)

### Testing Gaps to Address
1. **Command-specific tests** (22 CMD requirements need dedicated tests)
2. **Limit enforcement tests** (7 LIMITS requirements need boundary tests)
3. **Type safety negative tests** (TEST-EXT-5)
4. **Reapply policy tests** (TEST-EXT-6)
5. **Checkpoint roundtrip tests** (TEST-EXT-2)

### Documentation Gaps to Fill
1. **Command reference** (DOC-EXT-1) - comprehensive DSL reference
2. **Type system reference** (DOC-EXT-5) - all types documented
3. **Observation modes** (DOC-EXT-2) - selection guide
4. **Reapply policies** (DOC-EXT-6) - examples for each
5. **Expression context** (DOC-EXT-7) - available variables

---

## Notes

**Source Document Coverage:**
- ✅ command_reference.md: Fully analyzed (22 CMD requirements)
- ✅ effects-system-design.md: Additional details extracted (8 EFF-EXT)
- ✅ items-and-vfs-profiles.md: Additional details extracted (16 ITEM-EXT)
- ✅ unified-world-compiler-plan.md: Additional details extracted (8 COMP-EXT)
- ✅ runtime-vfs-effects-integration.md: Additional details extracted (7 RUN-EXT)

**Key Findings:**
- **Command reference** had the most new requirements (22) - highly detailed implementation spec
- **Runtime limits** were scattered across documents - consolidated into LIMITS category
- **Future commands** (while, emit) explicitly marked as not implemented
- **Testing requirements** need expansion - many command types lack dedicated tests
- **Documentation gaps** significant - command reference and type system need comprehensive docs
