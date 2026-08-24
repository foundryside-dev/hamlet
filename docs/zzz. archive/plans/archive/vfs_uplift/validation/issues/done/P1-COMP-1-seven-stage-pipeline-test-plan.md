# Test & Implementation Plan — COMP-1 Seven-Stage Pipeline

## Goals
- Make the compiler’s seven-stage pipeline explicit (parse → symbols → resolve → cross-validate → enrich → optimize/compile → emit) without changing behavior.
- Validate with a golden compile to detect regressions quickly.
- Fail fast on missing references using a symbol table, but avoid mutating DTOs in the first pass.

## Implementation Steps (fail-fast, no-BC constraints)
1) Wrap current flow in stage methods (no behavioral change):
   - Add `_stage_1_parse`, `_stage_2_build_symbol_table`, `_stage_3_resolve_references`, `_stage_4_cross_validate`, `_stage_5_enrich`, `_stage_6_optimize`, `_stage_7_emit`.
   - Stage methods initially call existing logic in the same order; add entry/exit logging.
2) Symbol table (Stage 2):
   - Build a read-only table of identifiers: bars, affordances, items, VFS vars (global/item), effects IDs (if available).
   - Store as a simple dict/dataclass for use in resolution.
3) Resolve (Stage 3):
   - Validate all references against the symbol table; raise on missing/unknown references with precise errors.
   - Do not mutate DTOs yet; keep resolution as a validation pass.
4) Cross-validate, enrich, optimize, emit:
   - Reuse existing logic behind stage wrappers; ensure logging markers.
5) Tests:
   - Golden compile: compile a small fixture config; assert counts (bars/affordances/items/effects) and presence of compiled artifacts.
   - Stage sequence test: assert that stage log markers occur in order (parse → symbols → resolve → cross-validate → enrich → optimize → emit).
   - Resolution failures: configs with bad bar/affordance/VFS references should fail in Stage 3 with clear messages.
6) Docs:
   - Update compiler architecture docs to list 7 stages and a short sequence diagram.

## Test Checklist
- [ ] Golden compile passes for fixture config; outputs unchanged vs. baseline.
- [ ] Stage sequence test asserts ordered markers.
- [ ] Unknown bar/affordance reference → Stage 3 failure (message names the missing symbol).
- [ ] Unknown VFS variable reference → Stage 3 failure.
- [ ] Unknown item/effect reference (if used) → Stage 3 failure.
- [ ] No behavior change: existing unit/integration compiler tests still pass.

## Risks & Mitigations
- Regression from reordered flow: mitigate by wrapper-only refactor first, then iterate.
- Incomplete symbol coverage: start with known entities (bars/affordances/items/VFS/effects) and fail fast with explicit errors.
- Log brittleness: keep logs minimal and ordered; tests should assert order, not exact text beyond markers.
