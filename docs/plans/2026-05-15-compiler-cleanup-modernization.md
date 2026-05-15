# Compiler Cleanup and Modernization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the Hamlet universe compiler into a strict, modern, v2.1-only compiler with no fallback or backwards compatibility code.

**Architecture:** Keep `UniverseCompiler.compile()` as the public facade while extracting active compiler passes behind typed stage boundaries. Delete old flat-pipeline code and stale private tests first, then make cache/artifact loading strict, then split validation, observation, action, effects, optimization, and emission into cohesive modules.

**Tech Stack:** Python 3.13, Pydantic config DTOs, pytest, torch tensors, MessagePack cache artifacts, existing `uv run` tooling.

**Prerequisites:**
- Work from `/home/john/hamlet`.
- Keep pre-release policy front and center: no old config support, no fallback caches, no migration paths.
- Preserve the public compile entrypoint unless a task explicitly replaces all call sites.
- Start each implementation task with a focused failing regression where behavior changes.

---

## Current Evidence

- `src/townlet/universe/compiler.py` is 4,431 lines and contains active pipeline stages plus dead legacy flat-pipeline methods.
- `UniverseCompiler.compile()` currently owns cache lookup, validation, stage orchestration, hash/provenance setup, artifact emission, and cache writes.
- `CompiledUniverse.from_dict()` tolerates missing serialized fields by constructing empty/default runtime state.
- Effects command schema still includes old/new aliases and implicit defaults.
- `VectorizedHamletEnv` consumes compiled artifacts but reconstructs VFS observation config objects at runtime.
- Focused compiler verification passed before this plan was written:

```bash
uv run pytest tests/test_townlet/unit/universe/test_compiler_pipeline.py tests/test_townlet/unit/universe/test_compiler_cache.py tests/test_townlet/unit/universe/test_metadata_serialization.py -q
```

## Task 1: Pin the v2.1 Compiler Contract

**Files:**
- Modify: `tests/test_townlet/unit/universe/test_compiler_pipeline.py`
- Modify: `tests/test_townlet/unit/universe/test_compiler_cache.py`
- Modify: `tests/test_townlet/unit/universe/test_metadata_serialization.py`

**Step 1: Add or tighten tests that describe the only supported contract**

Add tests asserting:
- `primary_level` is explicit in new runtime-facing examples where possible.
- Missing current cache fields fail instead of creating empty fallback structures.
- Current compiler artifacts round-trip with non-empty `observation_activity` for configs that produce observations.
- Level-directory inputs fail with a scoping error.

**Step 2: Run the focused tests and confirm failures where behavior is about to change**

Run:

```bash
uv run pytest tests/test_townlet/unit/universe/test_compiler_cache.py tests/test_townlet/unit/universe/test_metadata_serialization.py -q
```

**Definition of Done:**
- Tests capture the v2.1-only artifact and cache contract.
- At least one strict-cache test fails before implementation.

## Task 2: Make Cache and Artifact Loading Strict

**Files:**
- Modify: `src/townlet/universe/compiled.py`
- Modify: `src/townlet/universe/compiler.py`
- Modify: `tests/test_townlet/unit/universe/test_compiler_cache.py`
- Modify: `tests/test_townlet/unit/universe/test_metadata_serialization.py`
- Close or update: `docs/bugs/JANK-05-observation-activity-backcompat-empty-masks.md`

**Step 1: Replace missing-field fallbacks with required-field validation**

In `CompiledUniverse.from_dict()`, stop using default empty payloads for required current-schema fields. Required means at least:
- `optimization_data_raw`
- `observation_activity`
- per-level `observation_activity`
- per-level `optimization_data_raw`
- `vfs_observation_fields`
- `vfs_variables`
- `compiled_schema_version`

Raise `ValueError("Compiled universe cache is missing required field '<field>'; recompile the config pack.")`.

**Step 2: Keep corrupted or stale cache recovery only at the compile facade**

`UniverseCompiler.compile(use_cache=True)` may catch strict cache errors and recompile from source configs. Direct `CompiledUniverse.load_from_cache()` should fail loudly.

**Step 3: Verify**

Run:

```bash
uv run pytest tests/test_townlet/unit/universe/test_compiler_cache.py tests/test_townlet/unit/universe/test_metadata_serialization.py -q
```

**Definition of Done:**
- Direct cache load rejects stale/missing required fields.
- `compile(use_cache=True)` can still recover by recompiling source configs.
- JANK-05 is fixed or converted into a tracked closeout.

## Task 3: Delete Legacy Flat-Pipeline Methods and Tests

**Files:**
- Modify: `src/townlet/universe/compiler.py`
- Modify: `tests/test_townlet/unit/universe/test_compiler_validation.py`
- Search/update: `docs/`, `tests/`, `src/` references to removed private methods.

**Step 1: Delete dead methods**

Delete:
- `_stage_4_cross_validate`
- `_stage_5_compute_metadata`
- `_stage_5_build_rich_metadata`
- `_stage_6_optimize`
- `_auto_generate_standard_exposures`
- `_load_observation_exposures`
- private helpers only used by those deleted methods/tests, after confirming with `rg`.

**Step 2: Replace private dead-code tests with active v2.1 compile-path tests**

The current `test_compiler_validation.py` exercises old private helpers with `MagicMock` raw config shapes. Replace those with tests that mutate real config packs under `tmp_path` and call `UniverseCompiler().compile(..., use_cache=False)`.

**Step 3: Verify no references remain**

Run:

```bash
rg -n "_stage_4_cross_validate|_stage_5_compute_metadata|_stage_5_build_rich_metadata|_stage_6_optimize|_load_observation_exposures|_auto_generate_standard_exposures" src tests
uv run pytest tests/test_townlet/unit/universe/test_compiler_validation.py tests/test_townlet/unit/universe/test_compiler_pipeline.py -q
```

**Definition of Done:**
- Old flat-pipeline methods are gone.
- Tests cover active compiler behavior, not compatibility shims.

## Task 4: Remove Effects Command Aliases and Hidden Defaults

**Files:**
- Modify: `src/townlet/config/effects_config.py`
- Modify: `src/townlet/effects/schema.py`
- Modify: `src/townlet/effects/parser.py`
- Modify: `src/townlet/effects/compiler.py`
- Modify: `tests/test_townlet/unit/effects/`
- Modify: `configs/` examples using removed aliases.

**Step 1: Pick one canonical command schema**

Use only:
- `sample`, not `distribution`
- `iterator`, not `iterator_var`
- `body`, not `do_commands`, inside internal ASTs

YAML can still use natural command keys like `if`, `else`, and `do` if those are canonical user-facing syntax. The internal AST should not carry duplicate old/new fields.

**Step 2: Make behavior explicit**

Remove implicit defaults that affect behavior:
- `target="self"` for `spawn_effect`
- `intensity=1.0`
- `cascade_strength=1.0`

Either require them in config or compute them in one clearly named normalization pass that is part of the compiler, not a schema fallback.

**Step 3: Verify**

Run:

```bash
uv run pytest tests/test_townlet/unit/effects tests/test_townlet/integration/test_effects_compilation_pipeline.py tests/test_townlet/integration/test_compile_time_wiring.py -q
```

**Definition of Done:**
- No internal AST compatibility pairs remain.
- Effects configs fail loudly when required behavior fields are omitted.

## Task 5: Extract Strict Compiler Pass Modules

**Files:**
- Create: `src/townlet/universe/pipeline.py`
- Create: `src/townlet/universe/loaders/preflight.py`
- Create: `src/townlet/universe/loaders/v21.py`
- Create: `src/townlet/universe/validation/references.py`
- Create: `src/townlet/universe/validation/semantics.py`
- Create: `src/townlet/universe/validation/feasibility.py`
- Create: `src/townlet/universe/validation/limits.py`
- Modify: `src/townlet/universe/compiler.py`
- Modify: `tests/test_townlet/unit/universe/`

**Step 1: Introduce typed stage result dataclasses**

Create stage outputs for:
- `LoadedConfigBundle`
- `ResolvedConfigBundle`
- `SharedCompilerArtifacts`
- `CompiledLevelBundle`
- `CompiledArtifactBundle`

**Step 2: Move code without changing behavior**

Move one pass at a time. After each move, run the focused compiler tests.

**Step 3: Keep `UniverseCompiler` thin**

After extraction, `UniverseCompiler.compile()` should read as stage orchestration plus cache policy only.

**Definition of Done:**
- `compiler.py` is mostly facade/orchestration.
- Stage modules have direct unit tests.
- No behavior changes beyond already-planned strictness.

## Task 6: Split Domain Compilers

**Files:**
- Create: `src/townlet/universe/compilers/observation.py`
- Create: `src/townlet/universe/compilers/actions.py`
- Create: `src/townlet/universe/compilers/effects.py`
- Create: `src/townlet/universe/compilers/metadata.py`
- Create: `src/townlet/universe/compilers/optimization.py`
- Create: `src/townlet/universe/compilers/vfs.py`
- Modify: `src/townlet/universe/compiler.py`
- Modify: domain-specific tests.

**Step 1: Extract observation first**

Move `_build_observation_spec`, `_build_observation_activity`, `_build_vfs_observation_fields`, `_build_vfs_variables`, and duplicated normalization conversion into `ObservationCompiler`.

**Step 2: Extract action metadata**

Move `_build_action_space_metadata` and label synthesis into `ActionCompiler`.

**Step 3: Extract optimization**

Move `_build_optimization_data`, cascade ID validation, and related tensor helpers into `OptimizationCompiler`.

**Step 4: Verify**

Run:

```bash
uv run pytest tests/test_townlet/unit/universe tests/test_townlet/integration/test_compile_time_wiring.py tests/test_townlet/integration/test_world_compiler_full.py -q
```

**Definition of Done:**
- Each domain compiler has focused tests.
- `UniverseCompiler` no longer contains domain implementation details.

## Task 7: Emit Runtime-Ready VFS Observation Artifacts

**Files:**
- Modify: `src/townlet/universe/compiled.py`
- Modify: `src/townlet/universe/compiler.py`
- Modify: `src/townlet/environment/vectorized_env.py`
- Modify: `tests/test_townlet/integration/test_vfs_runtime_evaluation.py`
- Modify: `tests/test_townlet/unit/environment/test_vectorized_env*.py`

**Step 1: Add runtime-ready VFS observation artifact to `CompiledUniverse`**

The compiler should emit whatever `VectorizedHamletEnv` needs to build observations without reconstructing config DTOs from compiled profiles.

**Step 2: Delete runtime rehydration logic**

Remove `_compiled_var_to_cfg_payload` and the `GlobalVFSProfileConfig`/`AgentVFSProfileConfig`/`ItemVFSProfileConfig` reconstruction block from `VectorizedHamletEnv`.

**Step 3: Verify**

Run:

```bash
uv run pytest tests/test_townlet/integration/test_vfs_runtime_evaluation.py tests/test_townlet/integration/vfs tests/test_townlet/unit/vfs -q
```

**Definition of Done:**
- Runtime consumes compiler artifacts directly.
- No config DTO reconstruction happens inside `VectorizedHamletEnv`.

## Task 8: Final Policy Sweep

**Files:**
- Modify as found by sweep.
- Update/close relevant bug docs or Filigree issues.

**Step 1: Search for policy violations**

Run:

```bash
rg -n "legacy|backward|backwards|compat|fallback|deprecated|support both|migration|hasattr\\(|getattr\\(|setdefault|\\.get\\(" src/townlet/universe src/townlet/effects src/townlet/environment tests/test_townlet/unit/universe tests/test_townlet/unit/effects
```

Review every hit. Delete compatibility hits, keep only legitimate dynamic Python cases with comments explaining why they are not fallback behavior.

**Step 2: Full relevant verification**

Run:

```bash
uv run pytest tests/test_townlet/unit/universe tests/test_townlet/unit/effects tests/test_townlet/integration/test_compile_time_wiring.py tests/test_townlet/integration/test_world_compiler_full.py -q
uv run ruff check src/townlet/universe src/townlet/effects tests/test_townlet/unit/universe tests/test_townlet/unit/effects
uv run mypy src
```

**Definition of Done:**
- No compiler/effects fallback/backcompat code remains.
- Remaining dynamic guards are explicit error handling, not old-shape support.
- Focused tests, ruff, and mypy pass or have documented unrelated blockers.

