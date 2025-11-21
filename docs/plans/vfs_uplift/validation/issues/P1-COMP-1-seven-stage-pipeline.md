# [COMP-1] Seven-Stage Pipeline Explicit Structure

**Priority:** P1 (Important)
**Category:** Compiler
**Status:** PARTIAL
**Effort:** 4 hours

## Description

Universe Compiler should have explicit seven-stage pipeline structure with clear stage boundaries and markers. Currently 6 of 7 stages are implemented but not explicitly delineated. Missing explicit symbol table construction (stage 2) and resolve (stage 3) stages.

## Current State

Compiler implements 6 of 7 stages but stages are not explicitly separated:
- ✅ Stage 1: Parse (raw configs → DTO objects)
- ⚠️ Stage 2: Symbol table construction (implicit, not explicit stage)
- ⚠️ Stage 3: Resolve (implicit, not explicit stage)
- ✅ Stage 4: Cross-validate (explicit in code)
- ✅ Stage 5: Metadata enrichment (implicit)
- ✅ Stage 6: Optimization (compile sub-systems)
- ✅ Stage 7: Emit/Cache (serialize CompiledUniverse)

Symbol table construction and resolution happen implicitly during parsing/validation but are not explicit stages with clear markers.

**Location:** `src/townlet/universe/compiler.py`

## Required Implementation

1. **Refactor to explicit 7-stage structure:**
   - Extract symbol table construction as explicit `_stage_2_build_symbol_table()`
   - Extract resolution as explicit `_stage_3_resolve_references()`
   - Add stage markers/logging for each stage
   - Update documentation to reflect explicit stages

2. **Symbol Table Construction (Stage 2):**
   - Build mapping of all named entities: bars, affordances, cascades, items, VFS variables
   - Store in intermediate data structure for reference resolution
   - ~50 lines

3. **Resolution Stage (Stage 3):**
   - Resolve all symbolic references (bar names, affordance names, etc.)
   - Convert string references to object references
   - Validate references exist in symbol table
   - ~50 lines

4. **Documentation Updates:**
   - Update compiler architecture docs with explicit 7 stages
   - Add stage sequence diagram
   - Document what each stage does and produces

## Acceptance Criteria

- [ ] Explicit `_stage_2_build_symbol_table()` method
- [ ] Explicit `_stage_3_resolve_references()` method
- [ ] All 7 stages have clear method boundaries
- [ ] Stage logging shows execution flow
- [ ] Symbol table contains all named entities (bars, affordances, cascades, items, VFS vars)
- [ ] Resolution validates all references exist
- [ ] Updated documentation reflects explicit 7-stage structure
- [ ] Stage sequence test validates pipeline order
- [ ] No regression in existing compilation behavior

## Evidence

**Source Report:** gap-report-final.md (lines 55-68), gap-report-compiler.md
**Related Requirements:** None (architectural clarity)
**Current Implementation:** `src/townlet/universe/compiler.py` (implicit stages)

## Implementation Notes

**Current Pipeline (6 stages implicit):**
```python
def compile():
    # Stage 1: Parse
    raw = self._load_raw_configs()

    # Stages 2-3 implicit: symbol table + resolve happen in validation
    # Stage 4: Cross-validate
    self._stage_4_cross_validate()

    # Stage 5-6: Compile subsystems (implicit metadata + optimization)
    compiled_bars = self._compile_bars()
    compiled_vfs = VFSProfileCompiler.compile()
    compiled_effects = EffectCatalog.from_config()

    # Stage 7: Emit
    return CompiledUniverse(...)
```

**Target Pipeline (7 stages explicit):**
```python
def compile():
    # Stage 1: Parse
    raw = self._stage_1_parse()

    # Stage 2: Symbol table
    symbols = self._stage_2_build_symbol_table(raw)

    # Stage 3: Resolve
    resolved = self._stage_3_resolve_references(raw, symbols)

    # Stage 4: Cross-validate
    self._stage_4_cross_validate(resolved)

    # Stage 5: Metadata enrichment
    enriched = self._stage_5_enrich_metadata(resolved)

    # Stage 6: Optimization
    optimized = self._stage_6_optimize(enriched)

    # Stage 7: Emit
    return self._stage_7_emit(optimized)
```

**Why P1 (not P0):** Architectural clarity improvement, not a functional bug. Current implicit stages work correctly, just not as clean or maintainable.

## References

- Source file: `src/townlet/universe/compiler.py`
- Documentation: `docs/UNIVERSE-COMPILER.md`, `docs/architecture/COMPILER_ARCHITECTURE.md`
- Test file: `tests/test_townlet/unit/universe/test_compiler.py` (add stage sequence test)
