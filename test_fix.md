# Test Fix Plan – Legacy Config Loader Removal (v2.1 Migration)

This document briefs a new agent on the current state of the config/compile pipeline, why several tests are now failing, and how to systematically bring the tests in line with the v2.1 configuration system and “no-defaults, no-BC” constraints.

The goal is **not** to reintroduce compatibility with legacy config systems, but to **move tests onto the v2.1 path** and remove dependence on deprecated loaders and shims.

---

## 1. Background: Config v2.1 vs Legacy Paths

The runtime pipeline has been migrated to the v2.1 hierarchical config structure:

- Experiment-level files (shared vocabulary/metadata):
  - `configs/<pack>/experiment.yaml`
  - `configs/<pack>/stratum.yaml`
  - `configs/<pack>/environment.yaml`
  - `configs/<pack>/actions.yaml`
  - `configs/<pack>/agent.yaml`
- Curriculum-level files (per-level runtime behavior):
  - `configs/<pack>/levels/<level>/curriculum.yaml`
  - `configs/<pack>/levels/<level>/bars.yaml`
  - `configs/<pack>/levels/<level>/affordances.yaml`
  - `configs/<pack>/levels/<level>/training.yaml`

The v2.1 compiler entry point is:

- `src/townlet/universe/compiler.py: UniverseCompiler.compile(config_dir: Path)`

Breaking change: the **legacy pack loaders** and **legacy compiler stages** for “raw config 1.0” are intentionally disabled. The live runtime path is:

1. `UniverseCompiler.compile(...)` → `RawConfigsV21.from_experiment_dir(...)` (DTO loading).
2. v2.1 semantic validation (`_validate_v21_semantics`).
3. Construction of per-level metadata/optimization data and `CompiledUniverse` (no `HamletConfig` / raw config 1.0 in the loop).
4. `VectorizedHamletEnv.from_universe(...)` consumes `CompiledUniverse` for runtime.
5. `DemoRunner` / population code (`VectorizedPopulation`) use DTOs from the compiled universe plus `agent.yaml`/`training.yaml` for training.

Legacy pieces like `HamletConfig`, the old `RawConfigs` container, and the Stage 2–7 compiler pipeline are **not** used at runtime anymore.

---

## 2. Key Code Changes That Broke Tests

These changes were made to enforce “no legacy pipelines” more strictly:

### 2.1 Deprecated environment/cascade loaders

File: `src/townlet/environment/cascade_config.py`

- `load_bars_config(filepath: Path) -> BarsConfig`
  - Already returned a `RuntimeError` (marked deprecated for v2.1).
- **New**: `load_cascades_config(filepath: Path) -> CascadesConfig`
  - Now raises `RuntimeError` instead of loading `cascades.yaml`.
- **New**: `load_environment_config(config_dir: Path) -> EnvironmentConfig`
  - Now raises `RuntimeError` instead of constructing an `EnvironmentConfig` from `bars.yaml` + `cascades.yaml`.
- **New**: `load_default_config() -> EnvironmentConfig`
  - Now raises `RuntimeError` instead of reading from `configs/test`.

Intent: nothing in the runtime should depend on the old “bars.yaml + cascades.yaml → EnvironmentConfig” loaders. Only `UniverseCompiler.compile()` + v2.1 DTOs should be used.

### 2.2 Removed legacy operating_hours fallback

File: `src/townlet/universe/compiler.py`

- `_affordance_open_for_hour(self, affordance, hour) -> bool`:
  - **Before**: Accepted both v2.1 `opening_hours` and legacy `operating_hours: [start,end]`, using `operating_hours` as a fallback.
  - **Now**:
    - Requires `opening_hours` on the affordance (`AffordanceParamConfig` / `AffordancesV2Config`).
    - Treats `opening_hours.enabled == False` as 24/7 availability.
    - Uses `opening_hours.schedule[start,end]` windows exclusively.
    - Raises `ValueError` if `opening_hours` is missing (“legacy operating_hours arrays are no longer supported”).

This aligns economic-balance checks and temporal mechanics with the v2.1 spec and removes an implicit BC adapter.

> Note: The old Stage 2–7 compiler methods (`_stage_2_build_symbol_tables`, `_stage_3_resolve_references`, `_stage_4_cross_validate`, `_stage_5_compute_metadata`, `_stage_5_build_rich_metadata`, `_stage_6_optimize`, `_stage_7_emit_compiled_universe`, `_load_observation_exposures`) still exist in `compiler.py`, but each raises immediately with a “legacy pipeline removed” error. They are structurally present but are dead code in the v2.1 path.

---

## 3. Current Failure Surface (Tests)

Running:

```bash
uv run pytest tests/test_townlet/unit/environment/test_meters.py tests/test_townlet/unit/test_configuration.py -q
```

produces many failures/errors, all of which stem from tests **calling the deprecated loaders** rather than going through the v2.1 compiler + compiled universe.

### 3.1 `tests/test_townlet/unit/environment/test_meters.py`

Key fixture:

- `cascade_config` (`tests/test_townlet/unit/environment/test_meters.py:32`)
  - Calls `from townlet.environment.cascade_config import load_environment_config` and then `load_environment_config(test_config_pack_path)`.
  - Now fails with:
    - `RuntimeError: load_environment_config (bars.yaml/cascades.yaml) is deprecated in the v2.1 pipeline. Use UniverseCompiler.compile() and the compiled universe metadata instead.`

All tests that depend on this fixture (cascade / meter dynamics) error during setup.

### 3.2 `tests/test_townlet/unit/test_configuration.py`

Key fixtures and imports:

- Imports from `townlet.environment.cascade_config`:
  - `BarConfig`, `BarsConfig`, `CascadeConfig`, `CascadesConfig`, `EnvironmentConfig`,
  - `load_bars_config`, `load_cascades_config`, `load_default_config`, `load_environment_config`.

Fixtures:

- `bars_config` (`tests/test_townlet/unit/test_configuration.py:61`)
  - Calls `load_bars_config(test_config_pack_path / "bars.yaml")`.
  - Fails with `RuntimeError: load_bars_config is deprecated in the v2.1 pipeline. Use UniverseCompiler.compile() outputs instead.`
- `environment_config` (`tests/test_townlet/unit/test_configuration.py:75`)
  - Calls `load_environment_config(test_config_pack_path)`.
  - Fails with the new `load_environment_config` RuntimeError.

The rest of the file uses these fixtures to assert on bar indices, base depletions, cascade structure, etc. All such tests now error during fixture setup.

### 3.3 What’s **not** broken by this change (yet)

- Runtime v2.1 flows (demo runner, population, vectorized env) do not depend on these loaders. They remain intact.
- Tests that already go through the `compile_universe` fixture (`tests/test_townlet/_fixtures/config.py`) and use `CompiledUniverse` objects are not directly impacted by the loader deprecation.

---

## 4. Files to Read First (for New Agent)

To get oriented before editing tests:

1. **v2.1 Config Specification**
   - `configs/reference_config/reference-config-v2.1-complete.yaml`
   - `configs/reference_config/VARIABLE_SUBSYSTEM.md`
   - Explains the hierarchical structure and semantics (experiment/stratum/environment/actions/agent + per-level configs).

2. **Compiler & Config Loading**
   - `src/townlet/universe/compiler.py`
   - `src/townlet/universe/raw_configs_v21.py`
   - `src/townlet/config/*.py` (especially `*_v2_config.py`, `experiment_config.py`, `stratum_config.py`, `environment_config.py`, `training_v2_config.py`, `affordances_v2_config.py`, `bars_v2_config.py`).

3. **Runtime Env and Training**
   - `src/townlet/environment/vectorized_env.py`
   - `src/townlet/environment/meter_dynamics.py`
   - `src/townlet/population/vectorized.py`
   - `src/townlet/agent/brain_config.py`

4. **Test Fixtures and Helpers**
   - `tests/test_townlet/_fixtures/config.py` → `compile_universe` fixture.
   - `tests/test_townlet/_fixtures/environment.py` → `env_factory`, `cpu_env_factory`, etc.
   - `tests/test_townlet/utils/builders.py` → `make_vectorized_env_from_pack`, substrate builders, etc.

5. **Legacy vs v2.1 Architecture Docs** (for context, not mandatory to change code)
   - `docs/arch-analysis-2025-11-17-0613/00-coordination.md`
   - `docs/UNIVERSE-COMPILER.md`

---

## 5. Strategy to Fix Tests (High-Level)

The guiding principles:

- **Do not restore legacy loaders** or reintroduce `HamletConfig`/raw-config 1.0 semantics.
- **Move tests to the v2.1 compiler path** (`UniverseCompiler.compile` / `compile_universe` fixture) and to v2.1 DTOs/metadata.
- Preserve the *intent* of tests (validate semantics, not specific legacy DTO shapes).

### Phase A – Fix cascade/meter tests (`test_meters.py`)

Target file: `tests/test_townlet/unit/environment/test_meters.py`

Current pattern:

- Uses `load_environment_config(test_config_pack_path)` to build an `EnvironmentConfig` that combines `bars.yaml` and `cascades.yaml`, then uses it implicitly via env fixtures.

New pattern (desired):

1. Use the `compile_universe` fixture (already provided in `_fixtures/config.py`) to compile `configs/default_curriculum`.
2. Choose a level (e.g. `L0_0_minimal` or another appropriate level for meter/cascade behavior).
3. Obtain:
   - `compiled = compile_universe(test_config_pack_path)`
   - `level_meta = compiled.get_level(<level_name>)`
   - `meter_metadata = level_meta.meter_metadata`
   - `optimization_data = level_meta.optimization_data`
4. Drive `MeterDynamics` directly using `optimization_data` instead of an `EnvironmentConfig` built from legacy loaders.
   - The existing tests already use a vectorized env via `cpu_env_factory`; that env now uses `optimization_data` from v2.1 compiler internally.
   - For some assertions, it may be sufficient to keep using `cpu_env_factory` and drop any reliance on `load_environment_config` entirely.

Concrete steps:

- Refactor `cascade_config` fixture:
  - Either remove it and base tests solely on the vectorized env (`env.meter_dynamics`, `env.meter_name_to_index`), or
  - Rebuild an equivalent lightweight “cascade view” from `compiled`/`level_meta.bars.cascades` (v2.1 DTOs), not from `load_environment_config`.
- Ensure the tests still check:
  - Base depletion behavior (via `MeterDynamics` / env behavior).
  - Cascade relationships (source/target, thresholds, strengths) using v2.1 DTOs.

### Phase B – Fix configuration tests (`test_configuration.py`)

Target file: `tests/test_townlet/unit/test_configuration.py`

This file is more complex and consolidates several historical tests:

- Bars schema (bar indices, depletion values, terminal conditions).
- Cascade config schema and alignment with meter_dynamics.
- Affordance config load/validation.
- Config pack loading tests that previously went through legacy loaders.

New pattern (desired):

1. Use `compile_universe` to get a `CompiledUniverse` for `configs/default_curriculum`.
2. Derive the equivalent of `BarsConfig`, `CascadesConfig`, etc., from:
   - `compiled.metadata` and `compiled.meter_metadata` (for meter counts/names).
   - `compiled.get_level(level_name).bars` and `.affordances` (v2.1 `BarsV2Config` / `AffordancesV2Config` DTOs).
3. For tests that purely exercise DTO validation (schema-level, not runtime), decide between:
   - **Option 1 (preferred)**: Repoint them to v2.1 DTOs (`BarsV2Config`, `AffordancesV2Config`) and associated loaders (`load_bars_v2_config`, `load_affordances_v2_config`).
   - **Option 2**: If they only exist to enforce legacy DTO shapes, remove them or move them into a clearly marked `legacy/` area and exclude from the default test run.

Concrete steps:

- Replace `bars_config` fixture:
  - Use `compile_universe(test_config_pack_path)` and `compiled.get_level(<level_name>).bars` (v2.1) instead of `load_bars_config(...)` from `environment.cascade_config`.
- Replace `environment_config` fixture:
  - Either remove it or replace with views built from `compiled` + `level_meta.bars` + `level_meta.affordances` and `compiled.environment.environment` (for vocabulary).
- Update assertions:
  - Where tests check meter indices, base depletions, etc., use v2.1 fields:
    - `BarsV2Config.meters[*].depletion.passive`, `.bounds.lethal_min`, etc.
  - Where tests check cascade semantics, use `BarsV2Config.cascades[*]` instead of `CascadesConfig` from legacy loader.

Plan: do this incrementally—convert a small cluster of tests at a time and re-run just `test_configuration.py` to keep the feedback loop short.

### Phase C – Decide what to do with legacy DTO tests

Some unit tests (under `tests/test_townlet/unit/config/`) are explicitly aimed at the old DTOs (`townlet.config.bar`, `townlet.config.cascade`, `townlet.config.affordance`, etc.). These DTOs are no longer on the runtime path.

Options:

- If they still represent valuable “specification” for those DTOs, keep them but clearly mark them as tests for **non-runtime legacy code** and consider moving them behind a separate marker (e.g., `pytest -m legacy`).
- If you want a clean v2.1-only codebase, you may eventually:
  - Deprecate and delete the legacy DTO modules.
  - Remove their tests after confirming they have no remaining call sites.

For now, this doc focuses on tests that **block v2.1 adoption** by insisting on the old loaders; the next agent can assess the DTO tests once the main suites are green again.

---

## 6. Risks and Pitfalls

Key risks when refactoring tests:

- **Overfitting tests to legacy DTO shapes**:
  - We want tests to validate behavioral invariants (e.g., “health depletes slower when fitness is high”), not that a specific legacy class exists or has a certain field layout.

- **Accidentally reintroducing BC logic**:
  - Avoid adding new shims like “if opening_hours missing, synthesize one from operating_hours”. That contradicts the “no backwards compatibility” constraint.
  - The right fix is to update config packs and/or tests to always use v2.1 fields.

- **Coupling tests directly to internal implementation details**:
  - Favor using `CompiledUniverse` and documented DTOs/metadata rather than poking internal legacy attributes.
  - Keep tests resilient to reasonable internal refactors, as long as the v2.1 public contracts hold.

- **Test pack vs production packs**:
  - Some tests use `configs/default_curriculum`, others use temporary packs built via `config_pack_factory`/`mutate_training_yaml`. Ensure any new assumptions you make about configs (e.g., specific meter names) hold for the test packs you target.

---

## 7. Suggested Working Workflow

1. **Reproduce locally**:
   - Run:
     ```bash
     uv run pytest tests/test_townlet/unit/environment/test_meters.py -q
     uv run pytest tests/test_townlet/unit/test_configuration.py -q
     ```
   - Confirm the same `RuntimeError` failures.

2. **Fix `test_meters.py` first** (smaller, more focused):
   - Remove reliance on `load_environment_config` fixture.
   - Use `cpu_env_factory` + `MeterDynamics` + `CompiledUniverse` as described above.
   - Re-run only `test_meters.py` until green.

3. **Then tackle `test_configuration.py`**:
   - Migrate fixtures from legacy loaders to `compile_universe` + v2.1 DTOs.
   - Decide which tests to keep (rewrite) vs retire.
   - Re-run only `test_configuration.py` until green.

4. **Broader sweep**:
   - After these two, run the full unit suite:
     ```bash
     uv run pytest tests/test_townlet/unit -q
     ```
   - Look for any other references to:
     - `load_bars_config`, `load_cascades_config`, `load_environment_config`, `load_default_config` (from `environment.cascade_config`).
     - `operating_hours` on affordances.

5. **Document test updates**:
   - Where you make substantial behavioral changes to tests (e.g., switching from `BarsConfig` to `BarsV2Config`), consider leaving a short note in the test file docstring referencing v2.1 migration.

---

## 8. Definition of Done (for the Next Agent)

A reasonable “done” state for this test-fix effort:

- No tests import or call:
  - `load_bars_config` / `load_cascades_config` / `load_environment_config` / `load_default_config` from `townlet.environment.cascade_config`.
- No tests rely on `operating_hours` being honored by the compiler or runtime; all tests assume `opening_hours` (v2.1) semantics.
- `tests/test_townlet/unit/environment/test_meters.py` and `tests/test_townlet/unit/test_configuration.py` both pass using the v2.1 compiler + DTOs, with no legacy shims.
- The primary test entrypoint (`uv run pytest`) passes or fails only on issues unrelated to legacy config removal.

If you need more context while working, search for “v2.1” and “legacy pipeline” in `src/townlet/universe/compiler.py` and the docs under `docs/`, as they describe the intended end-state of the migration.
