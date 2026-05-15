# Compiler Cleanup Architecture Analysis Coordination

## Analysis Plan

- Scope: `src/townlet/universe/`, `src/townlet/effects/`, compiler-facing config DTOs, runtime consumers in `src/townlet/environment/`, and compiler-specific tests.
- Deliverable choice: Architect-ready cleanup analysis. The user asked for a compiler map plus a cleanup/refactor plan, so this pass favors current-state topology, debt inventory, and staged implementation guidance over broad product architecture.
- Strategy: Local evidence-gathering pass. The system-archaeology workflow normally delegates subsystem reads, but subagent delegation was not explicitly requested in this session, so the pass is bounded and source-cited.
- Complexity estimate: High. The main compiler is a 4,431-line orchestration class with active v2.1 pipeline code, old flat-pipeline remnants, artifact serialization, validation policy, optimization tensor building, and runtime coupling.

## Execution Log

- 2026-05-15: Ran `filigree session-context`; ready queue showed `hamlet-74197422b3` and `hamlet-b454c1b75a`.
- 2026-05-15: Created `docs/arch-analysis-2026-05-15-compiler-cleanup/`.
- 2026-05-15: Mapped compiler files, stage methods, runtime consumers, fallback/backcompat markers, and compiler tests.
- 2026-05-15: Ran focused verification: `uv run pytest tests/test_townlet/unit/universe/test_compiler_pipeline.py tests/test_townlet/unit/universe/test_compiler_cache.py tests/test_townlet/unit/universe/test_metadata_serialization.py -q`.

## Verification Snapshot

Focused compiler slice passed:

```text
13 passed, 145 warnings in 4.14s
```

Warnings are PyParsing deprecation warnings from `src/townlet/world/expression/parser.py`; they were not investigated further because they are outside this compiler-cleanup scope.

