# VFS Uplift Evidence Standards

**Purpose:** Define what counts as valid evidence for each requirement type in gap analysis

**Date:** 2025-11-22

---

## Evidence Quality Levels

### ✅ COMPLETE
**Definition:** Requirement is fully implemented with all supporting artifacts

**Criteria:**
1. **Implementation exists** with correct semantics
   - Code location: `file:line` reference
   - Logic matches requirement specification
   - No obvious TODOs or FIXMEs in implementation

2. **Tests exist** and cover requirement
   - Test file location: `test_file:line`
   - Test count meets plan targets (where specified)
   - Tests actually verify the requirement (not just smoke tests)
   - Tests pass in CI

3. **Error handling** is appropriate
   - Invalid inputs raise clear errors
   - Edge cases handled
   - No silent failures

4. **Documentation** exists (where required)
   - Schema docs for config requirements
   - User guide sections for workflows
   - Inline code comments for complex logic

**Example:**
```
REQ: Expression parser handles operator precedence
Evidence:
- Implementation: src/townlet/world/expression/parser.py:45-120
- Tests: tests/test_townlet/unit/world/expression/test_parser.py:30-85 (18 tests)
- Error handling: Raises ParseError with line/column on invalid syntax
- Docs: N/A (internal implementation)
Status: ✅ COMPLETE
```

---

### ⚠️ PARTIAL
**Definition:** Core implementation exists but missing critical supporting artifacts

**Criteria - Any of:**
1. **Implementation exists but tests incomplete**
   - Code works but test coverage has gaps
   - Example: Only happy path tested, error cases untested

2. **Implementation exists but error handling missing**
   - Code works for valid inputs
   - Silent failures or poor errors on invalid inputs

3. **Implementation exists but required docs missing**
   - Code works but schema docs/user guide absent
   - Makes feature hard to discover/use

4. **Implementation half-done**
   - Some aspects of requirement implemented
   - Other aspects stubbed or TODO

**Example:**
```
REQ: Item spawn conditions evaluate VFS predicates
Evidence:
- Implementation: src/townlet/items/manager.py:150-180 (condition parsing)
- Missing: VFS predicate evaluation (line 165 is TODO)
- Tests: 8 tests for parsing, 0 tests for evaluation
Status: ⚠️ PARTIAL (implementation half-done)
```

---

### ❌ MISSING
**Definition:** No implementation found, requirement not addressed

**Criteria - All of:**
1. **Grep/search finds no relevant code**
   - Searched for key terms (requirement-specific)
   - No implementation location identified

2. **No tests for requirement**
   - Test search comes up empty
   - Or tests are xfailed/skipped with "not implemented"

3. **Plan explicitly lists as future work**
   - Or plan assumes it exists but it doesn't

**Example:**
```
REQ: Mark-and-sweep VFS evaluation
Evidence:
- Grep "mark_and_sweep" in src/townlet/vfs/ → No results
- Grep "VFSEvaluator" → No results
- No tests in tests/test_townlet/unit/vfs/test_evaluator.py (file doesn't exist)
Status: ❌ MISSING
```

---

### 🔍 UNCLEAR
**Definition:** Found related code but can't confirm it matches requirement

**Criteria - Any of:**
1. **Code exists but semantics unclear**
   - Found a method/function but unclear if it does what requirement asks
   - Example: Method named `evaluate()` but unclear if it handles mark-and-sweep

2. **Code exists but integration unclear**
   - Implementation present but can't confirm it's wired into the right place
   - Example: Evaluator exists but unclear if env.step() calls it

3. **Tests exist but coverage unclear**
   - Test file exists but unclear if tests cover this specific requirement
   - Example: test_executor.py has 28 tests, unclear which test the for_each command

4. **Documentation contradicts code**
   - Plan says X, code appears to do Y
   - Need deeper investigation to reconcile

**Example:**
```
REQ: Effects schema includes VFS paths from compiled profiles
Evidence:
- Found: effects/executor.py:45-60 builds schema
- Unclear: Does schema include VFS paths or only bars?
- Tests: test_executor.py exists but unclear which test covers schema
Status: 🔍 UNCLEAR (need to read schema construction logic in detail)
```

---

## Evidence Requirements by Requirement Type

### Config/Schema Requirements (DTOs)
**What to look for:**
- Pydantic model in `src/townlet/config/`
- Fields match plan specification
- No defaults for behavioral parameters (use `Field(...)`)
- `extra="forbid"` on ConfigDict
- Validators for cross-field constraints

**Evidence format:**
```
- DTO: config/items_config.py:20-45 (ItemSpawnRuleConfig)
- Fields: placement (required), schedule (required), limits (required)
- No defaults: Verified via Field(...) with no default param
- Validators: lines 40-45 (validate_limits)
- Tests: tests/test_townlet/unit/config/test_items_config.py:30-80 (15 tests)
```

**Status criteria:**
- ✅ COMPLETE: DTO + fields + validators + 10+ tests
- ⚠️ PARTIAL: DTO + fields, validators or tests missing
- ❌ MISSING: No DTO found

---

### Compiler Requirements
**What to look for:**
- Logic in `src/townlet/universe/compiler.py` or submodules
- Validation/cross-validation logic
- Error messages with file/line context
- Compilation artifacts in `CompiledUniverse`
- Hashing for provenance (where applicable)

**Evidence format:**
```
- Compilation: universe/compiler.py:200-250 (compile_vfs_profiles)
- Validation: lines 230-245 (check circular dependencies)
- Error messages: format_validation_error at line 35
- Artifact: universe/compiled.py:50 (compiled_vfs_profiles field)
- Hashing: universe/compiler.py:800 (include in world_hash)
- Tests: tests/test_townlet/unit/universe/test_compiler.py:180-220 (12 tests)
```

**Status criteria:**
- ✅ COMPLETE: Compilation + validation + errors + artifact + tests
- ⚠️ PARTIAL: Compilation exists, validation or artifacts incomplete
- ❌ MISSING: No compilation logic found

---

### Runtime Requirements
**What to look for:**
- Integration in `src/townlet/environment/vectorized_env.py`
- Manager classes (EffectManager, ItemManager, etc.)
- Lifecycle hooks (env.step, env.reset)
- State storage (GPU tensors)
- Execution context construction

**Evidence format:**
```
- Integration: environment/vectorized_env.py:450-460 (effect_manager.tick())
- Manager: effects/manager.py:20-150 (EffectManager class)
- Lifecycle: manager.py:60-80 (tick method called each step)
- State: manager.py:30-40 (scoped effect collections)
- Context: manager.py:85-95 (builds ExecutionContext)
- Tests: tests/test_townlet/integration/test_effects.py:20-80 (8 tests)
```

**Status criteria:**
- ✅ COMPLETE: Integration + manager + lifecycle + state + context + tests
- ⚠️ PARTIAL: Integration exists, some aspects incomplete
- ❌ MISSING: No runtime integration found

---

### Expression/AST Requirements
**What to look for:**
- Parser in `src/townlet/world/expression/parser.py`
- AST nodes in `ast_nodes.py`
- Type checker in `type_checker.py`
- Evaluator in `evaluator.py`
- Operator implementations

**Evidence format:**
```
- Parser: world/expression/parser.py:45-200 (parse_expression)
- AST nodes: world/expression/ast_nodes.py:10-100 (BinaryOp, PathAccess, etc.)
- Type checker: world/expression/type_checker.py:30-120 (validate_types)
- Evaluator: world/expression/evaluator.py:40-180 (eval_ast)
- Operators: evaluator.py:100-150 (all math operators)
- Tests: tests/test_townlet/unit/world/expression/ (60+ tests across 4 files)
```

**Status criteria:**
- ✅ COMPLETE: Parser + AST + type checker + evaluator + all operators + 60+ tests
- ⚠️ PARTIAL: Core components exist, some operators or tests missing
- ❌ MISSING: Parser or evaluator not found

---

### VFS Requirements
**What to look for:**
- Registry in `src/townlet/vfs/registry.py`
- Profiles in `vfs/profiles.py`
- Schema in `vfs/schema.py`
- Observation builder in `vfs/observation_builder.py`
- Scoped storage (global/agent/item)

**Evidence format:**
```
- Registry: vfs/registry.py:20-150 (VariableRegistry class)
- Scoped storage: registry.py:40-60 (global_storage, agent_storage, item_storage)
- Profiles: vfs/profiles.py:30-120 (VFSProfileCompiler)
- Schema: vfs/schema.py:10-80 (VariableDef, ObservationField)
- Obs builder: vfs/observation_builder.py:30-200 (build_observation_spec)
- Tests: tests/test_townlet/unit/vfs/ (50+ tests across 4 files)
```

**Status criteria:**
- ✅ COMPLETE: Registry + profiles + schema + obs builder + scoped storage + 50+ tests
- ⚠️ PARTIAL: Core VFS exists, profiles or obs builder incomplete
- ❌ MISSING: Registry or profiles not found

---

### Effects Requirements
**What to look for:**
- Catalog in `src/townlet/effects/catalog.py`
- Executor in `effects/executor.py`
- Manager in `effects/manager.py`
- Schema in `effects/schema.py`
- Command types (modify, spawn_effect, if, for_each, etc.)

**Evidence format:**
```
- Catalog: effects/catalog.py:20-100 (EffectCatalog class)
- Executor: effects/executor.py:30-250 (execute_commands)
- Manager: effects/manager.py:20-150 (EffectManager with lifecycle)
- Schema: effects/schema.py:10-80 (EffectDef, ActiveEffect, CommandNode)
- Commands: executor.py:50-200 (modify, spawn_effect, if, for_each, etc.)
- Tests: tests/test_townlet/unit/effects/ (75+ tests across 5 files)
```

**Status criteria:**
- ✅ COMPLETE: Catalog + executor + manager + schema + all commands + 75+ tests
- ⚠️ PARTIAL: Core effects exist, some commands missing
- ❌ MISSING: Executor or manager not found

---

### Items Requirements
**What to look for:**
- Manager in `src/townlet/items/manager.py`
- Inventory in `items/inventory.py`
- Instance in `items/instance.py`
- Spawn scheduler
- Action handlers (GET/USE/DROP)

**Evidence format:**
```
- Manager: items/manager.py:20-180 (ItemManager class)
- Instance: items/instance.py:10-40 (ItemInstance dataclass)
- Inventory: items/inventory.py:10-80 (agent inventory state)
- Scheduler: manager.py:80-120 (spawn_item with schedule)
- Actions: environment/vectorized_env.py:XXX (GET/USE/DROP handlers)
- Tests: tests/test_townlet/unit/items/ (70+ tests across 4 files)
```

**Status criteria:**
- ✅ COMPLETE: Manager + inventory + instance + scheduler + actions + 70+ tests
- ⚠️ PARTIAL: Core items exist, inventory or actions incomplete
- ❌ MISSING: ItemManager not found

---

### Testing Requirements
**What to look for:**
- Test files in `tests/test_townlet/unit/` and `tests/test_townlet/integration/`
- Test count matches plan targets
- Test coverage for happy path AND error cases
- Integration tests for end-to-end flows
- Config packs for smoke tests

**Evidence format:**
```
- Unit tests: tests/test_townlet/unit/vfs/test_profiles.py:30-180 (20 tests)
- Integration tests: tests/test_townlet/integration/test_vfs_effects.py:10-120 (8 tests)
- Test count: 20 unit + 8 integration = 28 total (target: 25+)
- Coverage: Happy path (lines 30-80), error cases (lines 90-150)
- Smoke test config: configs/test/vfs_smoke/
```

**Status criteria:**
- ✅ COMPLETE: Tests exist + count meets target + happy/error coverage + pass in CI
- ⚠️ PARTIAL: Tests exist but count below target or coverage gaps
- ❌ MISSING: No tests or test file doesn't exist

---

### Documentation Requirements
**What to look for:**
- Schema docs in `docs/config-schemas/`
- User guides in `docs/guides/`
- Reference config in `configs/reference_config/`
- Migration guides
- Inline code comments (for complex logic only)

**Evidence format:**
```
- Schema doc: docs/config-schemas/vfs-profiles.md (50 lines)
- User guide: docs/guides/world-compiler-guide.md (section 3: VFS Profiles)
- Reference config: configs/reference_config/reference-config-v2.1-complete.yaml (lines 200-250: vfs_profiles)
- Migration guide: docs/guides/vfs-migration.md
```

**Status criteria:**
- ✅ COMPLETE: Schema doc + user guide section + reference config example + migration guide (if breaking change)
- ⚠️ PARTIAL: Some docs exist, key sections missing
- ❌ MISSING: No docs found

---

### Breaking Change Requirements
**What to look for:**
- Old code deleted (grep verification)
- New validation enforces breaking change
- Clear error messages guide users
- Migration guide exists
- All configs updated

**Evidence format:**
```
- Deleted: effect_pipeline.py not found (grep verification)
- Validation: compiler.py:XXX forbids old schema
- Error message: "EffectPipeline no longer supported. Use Effects instead. See docs/guides/migration.md"
- Migration guide: docs/guides/effects-migration.md
- Configs updated: All affordances.yaml migrated (grep verification)
```

**Status criteria:**
- ✅ COMPLETE: Old code deleted + validation + error message + migration guide + configs updated
- ⚠️ PARTIAL: Validation exists but migration guide or config updates missing
- ❌ MISSING: Old code still present

---

## Common Pitfalls

### False Positives (Think it's complete but it's not)
1. **Test exists but doesn't test requirement**
   - Example: test_executor.py exists with 28 tests, but no test for `for_each` command
   - Solution: Grep test file for specific requirement keywords

2. **Code exists but not integrated**
   - Example: VFSEvaluator class exists but env.step() never calls it
   - Solution: Check integration points (env.step, manager.tick, etc.)

3. **Implementation works for happy path only**
   - Example: spawn_item works but doesn't validate vfs_profile
   - Solution: Check error handling tests

4. **Schema docs exist but incomplete**
   - Example: vfs-profiles.md exists but doesn't document global/agent/item split
   - Solution: Read doc and verify it covers all aspects of requirement

### False Negatives (Think it's missing but it's actually there)
1. **Code in unexpected location**
   - Example: Looking for VFSEvaluator but it's named ExpressionEvaluator
   - Solution: Search for related terms, check import statements

2. **Implementation merged into related component**
   - Example: VFS evaluation integrated into VariableRegistry.update()
   - Solution: Read related classes, check method names

3. **Tests in unexpected file**
   - Example: VFS profile tests in test_vfs_registry.py not test_profiles.py
   - Solution: Search test directory for requirement keywords

4. **Docs in unexpected location**
   - Example: VFS profiles documented in vfs-integration-guide.md not vfs-profiles.md
   - Solution: Grep docs/ for requirement keywords

---

## Verification Workflow

### For each requirement:

**Step 1: Search for implementation**
```bash
# Search for key terms in source code
grep -r "mark_and_sweep" src/townlet/vfs/
grep -r "VFSEvaluator" src/townlet/
grep -r "def evaluate" src/townlet/vfs/

# Check imports to find related modules
grep -r "from townlet.vfs" src/townlet/
```

**Step 2: Search for tests**
```bash
# Search test directory
find tests/test_townlet/ -name "*vfs*" -o -name "*evaluator*"
grep -r "mark_and_sweep" tests/test_townlet/

# Count tests in relevant files
pytest --collect-only tests/test_townlet/unit/vfs/test_evaluator.py
```

**Step 3: Read implementation**
- Open file at identified location
- Verify semantics match requirement
- Check for TODOs, FIXMEs, NotImplementedError
- Check error handling (try/except, validation)

**Step 4: Read tests**
- Open test file
- Find tests for requirement (search for keywords)
- Verify tests actually test the requirement
- Check happy path AND error cases

**Step 5: Check integration**
- For runtime requirements: Check env.step(), manager.tick()
- For compiler requirements: Check CompiledUniverse fields
- For config requirements: Check DTO usage in compiler

**Step 6: Check documentation**
- Search docs/ for requirement keywords
- Verify completeness (all aspects documented)
- Check examples are clear

**Step 7: Assign status**
- Use criteria above for each status level
- Provide evidence in required format
- Note any uncertainties (use 🔍 UNCLEAR)

---

## Evidence Template

Copy this template for each requirement in gap report:

```markdown
### REQ-ID: Requirement name
**Source:** [plan file:line]
**Requirement:** [requirement text]

**Implementation:**
- Location: [file:line]
- Logic: [brief description or "not found"]

**Tests:**
- Location: [test_file:line]
- Count: [X tests] (target: [Y])
- Coverage: [happy path | error cases | both | none]

**Error Handling:**
- [description or "not found"]

**Documentation:**
- [doc file:line or "not found"]

**Integration:**
- [where/how integrated or "not found"]

**Status:** [✅ | ⚠️ | ❌ | 🔍]
**Rationale:** [why this status, what's missing for next level]
```

---

## Quality Checklist

Before finalizing gap report, verify:

- [ ] All 157 requirements have status assigned
- [ ] All ✅ COMPLETE have evidence in required format
- [ ] All ⚠️ PARTIAL specify what's missing
- [ ] All ❌ MISSING have grep verification
- [ ] All 🔍 UNCLEAR specify what needs investigation
- [ ] Summary statistics match detailed evidence
- [ ] Priority breakdown (P0/P1/P2) is consistent
- [ ] Recommendations are actionable with estimates
- [ ] Risk assessment identifies blockers
