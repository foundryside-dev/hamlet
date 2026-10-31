# VFS Uplift Gap Analysis - Quick Reference Card

**Purpose:** Cheat sheet for common verification patterns
**Date:** 2025-11-22

---

## Status Decision Tree

```
Start: Found implementation?
├─ NO → ❌ MISSING
└─ YES → Tests exist?
    ├─ NO → ⚠️ PARTIAL (missing tests)
    └─ YES → Error handling present?
        ├─ NO → ⚠️ PARTIAL (missing error handling)
        └─ YES → Documentation complete (if required)?
            ├─ NO → ⚠️ PARTIAL (missing docs)
            └─ YES → All aspects implemented?
                ├─ NO → ⚠️ PARTIAL (half-done)
                └─ YES → ✅ COMPLETE
```

**Exception:** If semantics unclear or integration unverified → 🔍 UNCLEAR

---

## Common Grep Patterns

### Find Implementation
```bash
# VFS evaluation
grep -r "mark_and_sweep\|VFSEvaluator\|eval.*vfs" src/townlet/vfs/

# Item VFS profiles
grep -r "vfs_profile\|item.*profile" src/townlet/items/
grep -r "profile_map\|profile.*storage" src/townlet/vfs/

# Compiled catalogs
grep -r "compiled.*catalog\|CompiledEffect\|CompiledVFS" src/townlet/universe/

# Effects commands
grep -r "spawn_effect\|modify.*target\|execute.*command" src/townlet/effects/

# Runtime integration
grep -r "effect_manager.tick\|vfs.*evaluate\|evaluate.*profile" src/townlet/environment/
```

### Find Tests
```bash
# Count tests by category
pytest --collect-only tests/test_townlet/unit/world/expression/ | grep -c "test_"
pytest --collect-only tests/test_townlet/unit/vfs/ | grep -c "test_"
pytest --collect-only tests/test_townlet/unit/effects/ | grep -c "test_"
pytest --collect-only tests/test_townlet/unit/items/ | grep -c "test_"

# Find specific test
grep -r "mark_and_sweep\|def test.*evaluator" tests/test_townlet/

# Check integration tests
find tests/test_townlet/integration/ -name "*.py" -exec basename {} \;
```

### Verify Breaking Changes
```bash
# Old code deleted
test -f src/townlet/config/effect_pipeline.py && echo "OLD CODE EXISTS" || echo "DELETED"

# No runtime YAML reads
grep -r "load.*yaml\|open.*yaml" src/townlet/environment/ | grep -v "test"

# Required fields enforced
grep -r "Field(.*)" src/townlet/config/ | grep -v "default="
```

### Check Documentation
```bash
# Schema docs
ls docs/config-schemas/{expressions,vfs-profiles,effects,items}.md 2>/dev/null

# User guides
ls docs/guides/{world-compiler-guide,vfs-migration}.md 2>/dev/null

# Reference config sections
grep -E "vfs_profiles:|items:|effects:" configs/reference_config/reference-config-v2.1-complete.yaml
```

---

## Evidence Format Templates

### Implementation Evidence
```
- Location: src/townlet/vfs/evaluator.py:20-150
- Logic: Mark-and-sweep evaluation with topo sort
- Key methods: evaluate_profiles (line 45), mark_for_obs (line 80)
```

### Test Evidence
```
- Location: tests/test_townlet/unit/vfs/test_evaluator.py:30-180
- Count: 18 tests (target: 15+)
- Coverage: Happy path (30-80), error cases (90-150), topo order (160-180)
```

### Integration Evidence
```
- Wired in: environment/vectorized_env.py:450 (calls vfs_evaluator.evaluate())
- Called from: env.step() at line 450, before observations
- Context passed: ExecutionContext with bars + vfs at line 455
```

---

## Priority Triage Guide

### Assign P0 (Must Fix) if:
- Core feature completely missing (e.g., no VFS evaluator)
- Runtime YAML rebuild still present (breaks compiled catalog design)
- Zero/stub data in critical paths (e.g., item VFS observations)
- Breaking change not enforced (old code still works)

### Assign P1 (Should Fix) if:
- Feature exists but tests incomplete
- Documentation missing for user-facing features
- Error handling present but error messages unclear
- Performance benchmarking not done

### Assign P2 (Nice to Have) if:
- Edge case documentation missing
- Polish features (depth limits, better errors)
- Non-critical optimizations
- Internal code comments

---

## Quick Checklist: Is Implementation Complete?

For each requirement, ask:

**Implementation:**
- [ ] Code exists at documented location?
- [ ] Logic matches requirement specification?
- [ ] No TODOs/FIXMEs in critical paths?
- [ ] All aspects implemented (not half-done)?

**Testing:**
- [ ] Test file exists?
- [ ] Test count meets plan target?
- [ ] Happy path tested?
- [ ] Error cases tested?
- [ ] Tests pass in CI?

**Error Handling:**
- [ ] Invalid inputs caught?
- [ ] Clear error messages?
- [ ] Edge cases handled?
- [ ] No silent failures?

**Integration:**
- [ ] Wired into env/compiler/manager?
- [ ] Called at correct lifecycle point?
- [ ] Context/state passed correctly?

**Documentation (if required):**
- [ ] Schema docs exist?
- [ ] User guide section exists?
- [ ] Reference config example exists?
- [ ] Migration guide exists (if breaking)?

**If all checked:** ✅ COMPLETE
**If 1-2 missing:** ⚠️ PARTIAL
**If 3+ missing or not found:** ❌ MISSING
**If unclear:** 🔍 UNCLEAR

---

## Category-Specific Shortcuts

### Compiler Requirements
**Quick verify:**
```bash
# Check compilation stages
grep -E "def compile_|Stage [0-9]:" src/townlet/universe/compiler.py

# Check CompiledUniverse fields
grep -E "^\s+(compiled_vfs_profiles|compiled_effect_catalog):" src/townlet/universe/compiled.py

# Check error reporting
grep "format_validation_error\|CompileError" src/townlet/universe/compiler.py
```

**Status criteria:**
- ✅ If compilation logic + artifact in CompiledUniverse + validation + tests
- ⚠️ If compilation exists but validation or artifact incomplete
- ❌ If no compilation logic found

---

### Runtime Requirements
**Quick verify:**
```bash
# Check EffectManager integration
grep "effect_manager = \|effect_manager.tick()" src/townlet/environment/vectorized_env.py

# Check VFS evaluation
grep "vfs.*evaluate\|evaluate.*vfs\|mark_and_sweep" src/townlet/environment/vectorized_env.py

# Check item VFS in observations
grep -A 5 "item_vfs\|item.*observation" src/townlet/vfs/observation_builder.py
```

**Status criteria:**
- ✅ If integrated in env.step + manager class exists + lifecycle correct + tests
- ⚠️ If integration exists but some aspects missing
- ❌ If no integration in env.step

---

### Testing Requirements
**Quick verify:**
```bash
# Count all tests
pytest --collect-only tests/test_townlet/ | grep -c "test_"

# Check test count by category
for dir in world/expression vfs effects items; do
  count=$(pytest --collect-only tests/test_townlet/unit/$dir 2>/dev/null | grep -c "test_" || echo "0")
  echo "$dir: $count tests"
done

# Check integration tests
ls tests/test_townlet/integration/test_*_integration.py 2>/dev/null | wc -l
```

**Status criteria:**
- ✅ If test count meets target + happy/error coverage + pass in CI
- ⚠️ If tests exist but count below target or coverage gaps
- ❌ If no tests or test file doesn't exist

---

### Documentation Requirements
**Quick verify:**
```bash
# Check schema docs
for doc in expressions vfs-profiles effects items; do
  test -f docs/config-schemas/${doc}.md && echo "${doc}: EXISTS" || echo "${doc}: MISSING"
done

# Check user guides
for guide in world-compiler-guide vfs-migration effects-migration; do
  test -f docs/guides/${guide}.md && echo "${guide}: EXISTS" || echo "${guide}: MISSING"
done

# Check reference config completeness
grep -c "^  # " configs/reference_config/reference-config-v2.1-complete.yaml
```

**Status criteria:**
- ✅ If schema doc + user guide section + reference example + migration guide (if breaking)
- ⚠️ If some docs exist but key sections missing
- ❌ If no docs found

---

## High-Priority Verification Script

Run this to quickly check critical requirements:

```bash
#!/bin/bash
# quick-verify.sh - Check P0 requirements

echo "=== P0 REQUIREMENTS VERIFICATION ==="
echo

echo "RUN-1: VFS Evaluator"
test -f src/townlet/vfs/evaluator.py && echo "✅ File exists" || echo "❌ MISSING"
grep -q "mark_and_sweep" src/townlet/vfs/*.py && echo "✅ Mark-and-sweep found" || echo "⚠️ Not found"

echo
echo "RUN-2: Item VFS Observations"
grep -A 3 "item_vfs" src/townlet/vfs/observation_builder.py | grep -q "zeros\|stub" && echo "❌ STUB DATA" || echo "✅ Real data"

echo
echo "RUN-3: Compiled Catalogs"
grep -q "compiled_effect_catalog" src/townlet/universe/compiled.py && echo "✅ Effects in CompiledUniverse" || echo "❌ MISSING"
grep -q "compiled_vfs_profiles" src/townlet/universe/compiled.py && echo "✅ VFS in CompiledUniverse" || echo "❌ MISSING"
grep "effects.yaml\|EffectCatalog(" src/townlet/environment/vectorized_env.py && echo "❌ Runtime rebuild found" || echo "✅ No runtime rebuild"

echo
echo "TEST-1: Test Count"
total=$(pytest --collect-only tests/test_townlet/ 2>/dev/null | grep -c "test_")
echo "Total tests: $total (target: 270+)"
test "$total" -ge 270 && echo "✅ Target met" || echo "⚠️ Below target"

echo
echo "=== END VERIFICATION ==="
```

Make executable: `chmod +x quick-verify.sh`

---

## Effort Estimation Guide

**Implementation effort:**
- Create new module (100-200 lines): 0.5-1 day
- Integrate into existing system: 0.5-1 day
- Complex feature (500+ lines): 2-3 days

**Testing effort:**
- 10-15 unit tests: 0.5 day
- Integration test suite: 1 day
- Performance benchmarking: 0.5-1 day

**Documentation effort:**
- Schema doc (50-100 lines): 0.5 day
- User guide section: 0.5-1 day
- Migration guide: 1 day

**Rule of thumb:** Time to fix = Time to implement × 0.7 (faster because architecture exists)

---

## Common Mistakes to Avoid

1. **Marking as COMPLETE without checking tests**
   - Always verify test file exists and count meets target
   - Check tests actually test the requirement (not just related code)

2. **Missing runtime integration**
   - Code exists but env.step() never calls it
   - Always check integration points

3. **Assuming docs exist**
   - Schema doc file exists but doesn't cover all aspects
   - Always read doc to verify completeness

4. **Not checking error handling**
   - Happy path works but no validation
   - Always check error cases tested

5. **Grep verification without reading code**
   - Pattern found but semantics don't match requirement
   - Always read implementation after grep

---

## When to Use Each Status

**Use ✅ COMPLETE when:**
- You can answer "yes" to all checklist items
- You've verified with eyes on code/tests/docs
- No obvious gaps or TODOs

**Use ⚠️ PARTIAL when:**
- Core implementation works
- But tests/docs/error handling incomplete
- Or only some aspects implemented

**Use ❌ MISSING when:**
- Grep search finds nothing
- No test file exists
- Implementation location unknown

**Use 🔍 UNCLEAR when:**
- Found code but can't confirm semantics
- Integration unclear
- Need to read implementation in detail

**Default to 🔍 UNCLEAR if unsure, then investigate deeper**

---

## Gap Report Review Checklist

Before finalizing gap report:

- [ ] All 157 requirements have status
- [ ] Status counts match (summary = detailed)
- [ ] All ✅ have file:line evidence
- [ ] All ⚠️ specify what's missing
- [ ] All ❌ have grep verification
- [ ] All 🔍 specify investigation needed
- [ ] P0 gaps are truly blocking merge
- [ ] Effort estimates seem reasonable (use guide above)
- [ ] Recommendations are actionable
- [ ] Risk assessment identifies blockers
- [ ] Conclusion states merge readiness

---

## Quick Start Commands

```bash
# Generate new gap report
cd docs/plans/vfs_uplift/validation/
cp gap-report-template.md gap-report-$(date +%Y-%m-%d).md

# Run quick verification
bash quick-verify.sh

# Count test coverage
pytest --collect-only tests/test_townlet/ | grep -c "test_"

# Verify no runtime YAML rebuilds
! grep -r "load.*yaml\|open.*yaml" src/townlet/environment/ | grep -v test

# Check compilation stages
grep "Stage\|compile_" src/townlet/universe/compiler.py | head -20
```

---

## Need More Detail?

- **Requirement interpretation:** See requirements-checklist.md
- **Evidence standards:** See evidence-standards.md
- **Report format:** See gap-report-template.md
- **Verification workflow:** See evidence-standards.md (7-step process)
- **Overview:** See README.md
