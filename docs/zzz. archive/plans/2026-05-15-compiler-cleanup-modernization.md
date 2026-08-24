# Compiler Cleanup and Modernization Plan

## Goal

Make the universe compiler a strict v2.1 compiler boundary: source YAML is loaded once into typed DTOs, compiler passes exchange typed artifacts, runtime consumes compiled runtime-ready structures, and stale compatibility or fallback behavior fails loudly.

This project is pre-release. Do not preserve old config shapes, old cache schemas, old private helper call sites, or support-both behavior.

## Current State

- `UniverseCompiler.compile()` is the public facade and should stay that way until every call site is intentionally replaced.
- `src/townlet/universe/pipeline.py`, `loaders/`, `validation/`, and `compilers/` already exist. Earlier versions of this plan that ask to create those modules are stale.
- `src/townlet/universe/compiler.py` is now 619 lines. It delegates active validation and several domain passes, but it still owns cache/provenance orchestration.
- Stage 1 config loading now owns `vfs_profiles.yaml`, optional `effects.yaml`, optional `action_labels.yaml`, and optional `variables_reference.yaml`; domain compilers and later compiler stages no longer read those YAML files directly.
- The cache command-pipeline bug and CLI primary-level validation bug found during the architecture review are fixed and closed in Filigree.
- Observation masking now uses explicit field-level `curriculum_active` metadata instead of sentinel text in descriptions.
- Direct cache loading now rejects missing current-schema fields, including fields whose valid value may be explicit `None`.
- Cascade graph reference, cycle, and per-level coverage checks now live in Stage 1b semantic validation instead of `RawConfigsV21.__post_init__`.
- Modulation graph reference and per-level coverage checks now live in Stage 1b semantic validation instead of `RawConfigsV21.__post_init__`.
- Environment-to-level meter and affordance vocabulary checks now live in Stage 1b semantic validation instead of `RawConfigsV21.__post_init__`.
- Affordance meter-reference checks, `enabled_affordances` vocabulary checks, and grid entity-capacity checks now live in Stage 1b semantic validation instead of `RawConfigsV21.__post_init__` or reference resolution.
- Hard environment, catalog, grid-size, and spawn-rule limits now live in Stage 1b safety-limit validation instead of `RawConfigsV21.__post_init__`.
- `UniverseCompiler.compile()` runs Stage 1b safety-limit validation and Stage 1c semantic validation immediately after typed DTO loading and before symbol-table/reference resolution.
- Runtime VFS registry variables are now emitted by the compiler from observation/environment variables plus compiled VFS profiles; `VectorizedHamletEnv` consumes `CompiledUniverse.vfs_variables` directly.
- Runtime effect expression schemas are now emitted by the compiler and consumed directly by `VectorizedHamletEnv` and `ItemManager`.
- Runtime action spaces are now emitted by the compiler, persisted in schema `1.7`, and consumed directly by `VectorizedHamletEnv`.
- Temporal day-length normalization for optimization tensors now lives in `OptimizationCompiler` instead of the compiler facade.
- Direct source reads that remain under `src/townlet/universe/` are loader/preflight reads and cache hash normalization reads. Those are acceptable compiler-boundary responsibilities.

## Completed Review Fixes

### Cache Round Trip Preserves Effect Commands

Fixed in `src/townlet/universe/compiled.py`.

- Bumped compiled schema for artifact changes; the current schema is `1.7` after the later runtime action-space artifact change.
- Serialized and deserialized effect command pipelines.
- Rehydrated expression ASTs when loading compiled command nodes.
- Added a regression that compiles, saves, loads, and verifies non-empty effect commands.

Verification:

```bash
uv run pytest tests/test_townlet/unit/universe/test_compiled_universe_serialization.py tests/test_townlet/unit/universe/test_effects_catalog_compilation.py tests/test_townlet/unit/universe/test_metadata_serialization.py tests/test_townlet/unit/universe/test_compiler_cli.py -q
```

### CLI Validation Passes Explicit Primary Level

Fixed in `scripts/validate_compiler_cli.py`.

- The validation script reads `experiment.curriculum_levels[0]`.
- The script passes `--primary-level` to the compiler CLI.
- Invalid or missing level declarations fail loudly.

Verification:

```bash
uv run python scripts/validate_compiler_cli.py
```

### Stage 1 Owns Root Optional Artifacts

Fixed in `src/townlet/universe/raw_configs_v21.py`, `src/townlet/universe/loaders/preflight.py`, and domain compiler call sites.

- `RawConfigsV21` carries typed `vfs_profiles`, `effects`, `action_label_overrides`, and `variables_reference`.
- Preflight syntax validation covers `vfs_profiles.yaml`, optional `effects.yaml`, optional `action_labels.yaml`, and optional `variables_reference.yaml`.
- `VFSCompiler`, `EffectsCompiler`, and `ActionCompiler` consume typed DTO inputs instead of reading source files.
- Stage 6 VFS observation marks now consume `raw.variables_reference` instead of reopening `variables_reference.yaml`.

Verification:

```bash
uv run pytest tests/test_townlet/unit/universe/test_pipeline_modules.py tests/test_townlet/unit/universe/test_vfs_observation_marking.py tests/test_townlet/unit/universe/test_effects_catalog_compilation.py tests/test_townlet/unit/universe/test_effects_schema_completeness.py tests/test_townlet/unit/universe/test_compiler_cache.py tests/test_townlet/unit/universe/test_compiler_cli.py tests/test_townlet/unit/environment/test_checkpoint_validation.py::TestActionLabelLoading -q
```

### Deleted Loader-Era Compiler Helpers

Fixed in `src/townlet/universe/compiler.py`.

- Removed `_load_experiment_structure`.
- Removed `_validate_vocabulary_consistency`.
- Removed imports used only by those stale helpers.

Verification:

```bash
rg "_load_experiment_structure|_validate_vocabulary_consistency" src tests
uv run pytest tests/test_townlet/unit/universe/test_pipeline_modules.py tests/test_townlet/unit/universe/test_compiler_cli.py -q
uv run ruff check src/townlet/universe/compiler.py
uv run black --check src/townlet/universe/compiler.py
uv run mypy src/townlet/universe/compiler.py
```

### Stage 3 Owns DAC Reference Validation

Fixed in `src/townlet/universe/validation/references.py` and `src/townlet/universe/compiler.py`.

- Moved DAC bar, VFS variable, and affordance reference checks out of `UniverseCompiler`.
- Removed the temporary callback hook from `resolve_references()`.
- Removed the unused `_validate_drive_references_v21` helper that duplicated pieces of DAC and substrate-action validation.
- Added a regression proving `resolve_references()` rejects bad DAC bar references directly.

Verification:

```bash
uv run pytest tests/test_townlet/unit/universe/test_pipeline_modules.py tests/test_townlet/unit/universe/test_compiler_cli.py -q
uv run ruff check src/townlet/universe/compiler.py src/townlet/universe/validation/references.py tests/test_townlet/unit/universe/test_pipeline_modules.py
uv run black --check src/townlet/universe/compiler.py src/townlet/universe/validation/references.py tests/test_townlet/unit/universe/test_pipeline_modules.py
uv run mypy src/townlet/universe/compiler.py src/townlet/universe/validation/references.py
```

### Replaced Textual Observation Masking

Fixed in `src/townlet/universe/dto/observation_spec.py`, `src/townlet/universe/compilers/observation.py`, `src/townlet/universe/adapters/vfs_adapter.py`, and `src/townlet/universe/compiled.py`.

- Added `ObservationField.curriculum_active`.
- Observation compilation sets that flag for inactive global, local, and temporal observation fields.
- Observation activity, VFS observation field emission, and max-compact filtering read the explicit flag instead of searching descriptions.
- Display descriptions no longer encode masking state.
- Bumped compiled schema to `1.5` for the persisted field-level activity metadata. The current schema is now `1.7` after the later runtime artifact changes.

Verification:

```bash
uv run pytest tests/test_townlet/unit/universe/test_observation_modes.py tests/test_townlet/integration/test_observation_modes_integration.py tests/test_townlet/integration/test_observation_mask_parity.py -q
uv run pytest tests/test_townlet/unit/universe/test_metadata_serialization.py tests/test_townlet/unit/universe/test_compiled_universe_serialization.py -q
rg -n '"MASKED"|MASKED' src/townlet/universe tests/test_townlet/unit/universe
```

### Strict Cache Direct Load Requires Current Schema

Fixed in `src/townlet/universe/compiled.py` and `tests/test_townlet/unit/universe/test_compiler_cache.py`.

- `CompiledUniverse.from_dict()` now requires the full current top-level schema field set.
- Present-but-null artifact fields remain valid where the compiled model allows `None`; missing fields fail loudly.
- Metadata collection fields, VFS observation-spec fields, and per-level provenance hashes now use field-specific required-field errors.
- Focused cache tests prove direct `CompiledUniverse.load_from_cache()` rejects stale current-version payloads instead of silently inferring defaults.

Verification:

```bash
uv run pytest tests/test_townlet/unit/universe/test_compiler_cache.py tests/test_townlet/unit/universe/test_compiled_universe_serialization.py tests/test_townlet/unit/universe/test_metadata_serialization.py -q
uv run ruff check src/townlet/universe/compiled.py tests/test_townlet/unit/universe/test_compiler_cache.py
uv run black --check src/townlet/universe/compiled.py tests/test_townlet/unit/universe/test_compiler_cache.py
uv run mypy src/townlet/universe/compiled.py
```

### Compiler Facade No Longer Owns Validation Helpers

Fixed in `src/townlet/universe/compiler.py`, `src/townlet/universe/validation/semantics.py`, and `tests/test_townlet/unit/universe/test_pipeline_modules.py`.

- Moved Stage 1b semantic validation into `validate_v21_semantics()`.
- `UniverseCompiler.compile()` now calls the semantic validation module instead of a private compiler method.
- Added a direct module test proving loaded DTOs can be validated without going through the compiler facade.
- Deleted the unreferenced legacy `_validate_*` helper cluster and related dead economic, position, cascade, capacity, and effect-summary helpers from `compiler.py`.
- `compiler.py` is now 638 lines and `rg` finds no private `_validate*` helpers in it.

Verification:

```bash
uv run pytest tests/test_townlet/unit/universe/test_pipeline_modules.py tests/test_townlet/unit/universe/test_compiler_validation.py tests/test_townlet/unit/universe/test_compiler_cli.py tests/test_townlet/unit/universe/test_action_space_composition.py -q
uv run ruff check src/townlet/universe/compiler.py src/townlet/universe/validation/semantics.py tests/test_townlet/unit/universe/test_pipeline_modules.py
uv run black --check src/townlet/universe/compiler.py src/townlet/universe/validation/semantics.py tests/test_townlet/unit/universe/test_pipeline_modules.py
uv run mypy src/townlet/universe/compiler.py src/townlet/universe/validation/semantics.py
rg -n "def _validate|_validate_v21_semantics|_validate_economic_balance_v21|_validate_spatial_feasibility|_compute_dac_hash|_summarize_affordance_effects|_tensorize_affordance_position|_extract_money_cost" src/townlet/universe/compiler.py src/townlet/universe/validation/semantics.py tests/test_townlet/unit/universe
```

### Cascade Policy Moved Out of Raw Config Construction

Fixed in `src/townlet/universe/raw_configs_v21.py`, `src/townlet/universe/validation/semantics.py`, and `tests/test_townlet/unit/universe/test_pipeline_modules.py`.

- Removed cascade meter-reference, cycle, and per-level coverage policy from `RawConfigsV21.__post_init__`.
- Added Stage 1b semantic validation coverage for unknown cascade meters and cascade cycles.
- Kept existing per-level missing/extra cascade checks in `validate_v21_semantics()`.
- Added direct module regressions proving loaded DTOs reach semantic validation before cascade policy is enforced.

Verification:

```bash
uv run pytest tests/test_townlet/unit/universe/test_pipeline_modules.py::test_validate_v21_semantics_rejects_cascade_with_unknown_meter tests/test_townlet/unit/universe/test_pipeline_modules.py::test_validate_v21_semantics_rejects_cascade_cycle -q
uv run pytest tests/test_townlet/unit/universe/test_pipeline_modules.py tests/test_townlet/unit/universe/test_compiler_validation.py tests/test_townlet/unit/universe/test_compiler_cli.py tests/test_townlet/unit/universe/test_action_space_composition.py -q
uv run ruff check src/townlet/universe/raw_configs_v21.py src/townlet/universe/validation/semantics.py tests/test_townlet/unit/universe/test_pipeline_modules.py
uv run black --check src/townlet/universe/raw_configs_v21.py src/townlet/universe/validation/semantics.py tests/test_townlet/unit/universe/test_pipeline_modules.py
uv run mypy src/townlet/universe/raw_configs_v21.py src/townlet/universe/validation/semantics.py
```

### Modulation Policy Moved Out of Raw Config Construction

Fixed in `src/townlet/universe/raw_configs_v21.py`, `src/townlet/universe/validation/semantics.py`, and `tests/test_townlet/unit/universe/test_pipeline_modules.py`.

- Removed modulation graph reference and per-level coverage policy from `RawConfigsV21.__post_init__`.
- Added Stage 1b semantic validation coverage for unknown modulation bars or affordances.
- Kept existing per-level missing/extra modulation checks in `validate_v21_semantics()`.
- Added direct module regressions proving loaded DTOs reach semantic validation before modulation policy is enforced.

Verification:

```bash
uv run pytest tests/test_townlet/unit/universe/test_pipeline_modules.py::test_validate_v21_semantics_rejects_modulation_with_unknown_bar tests/test_townlet/unit/universe/test_pipeline_modules.py::test_validate_v21_semantics_rejects_missing_level_modulation -q
uv run pytest tests/test_townlet/unit/universe/test_pipeline_modules.py tests/test_townlet/unit/universe/test_compiler_validation.py tests/test_townlet/unit/universe/test_compiler_cli.py tests/test_townlet/unit/universe/test_action_space_composition.py -q
uv run ruff check src/townlet/universe/raw_configs_v21.py src/townlet/universe/validation/semantics.py tests/test_townlet/unit/universe/test_pipeline_modules.py
uv run black --check src/townlet/universe/raw_configs_v21.py src/townlet/universe/validation/semantics.py tests/test_townlet/unit/universe/test_pipeline_modules.py
uv run mypy src/townlet/universe/raw_configs_v21.py src/townlet/universe/validation/semantics.py
```

### Vocabulary Policy Moved Out of Raw Config Construction

Fixed in `src/townlet/universe/raw_configs_v21.py`, `src/townlet/universe/validation/semantics.py`, and `tests/test_townlet/unit/universe/test_pipeline_modules.py`.

- Removed environment-to-level meter and affordance vocabulary checks from `RawConfigsV21.__post_init__`.
- Kept `METER_VOCAB_MISMATCH` and `AFFORDANCE_VOCAB_MISMATCH` enforcement in `validate_v21_semantics()`.
- Added direct module regressions proving loaded DTOs reach semantic validation before vocabulary policy is enforced.

Verification:

```bash
uv run pytest tests/test_townlet/unit/universe/test_pipeline_modules.py::test_validate_v21_semantics_rejects_level_meter_vocab_mismatch tests/test_townlet/unit/universe/test_pipeline_modules.py::test_validate_v21_semantics_rejects_level_affordance_vocab_mismatch -q
uv run pytest tests/test_townlet/unit/universe/test_pipeline_modules.py tests/test_townlet/unit/universe/test_compiler_validation.py tests/test_townlet/unit/universe/test_compiler_cli.py tests/test_townlet/unit/universe/test_action_space_composition.py -q
uv run ruff check src/townlet/universe/raw_configs_v21.py src/townlet/universe/validation/semantics.py tests/test_townlet/unit/universe/test_pipeline_modules.py
uv run black --check src/townlet/universe/raw_configs_v21.py src/townlet/universe/validation/semantics.py tests/test_townlet/unit/universe/test_pipeline_modules.py
uv run mypy src/townlet/universe/raw_configs_v21.py src/townlet/universe/validation/semantics.py
```

### Affordance and Enabled-Affordance Policy Moved Out of Raw Config Construction

Fixed in `src/townlet/universe/raw_configs_v21.py`, `src/townlet/universe/validation/semantics.py`, `src/townlet/universe/validation/references.py`, `src/townlet/universe/compiler.py`, and `tests/test_townlet/unit/universe/test_pipeline_modules.py`.

- Removed affordance cost-meter, affordance interaction-meter, and `training.enabled_affordances` vocabulary policy from `RawConfigsV21.__post_init__`.
- Removed duplicate affordance/enabled-affordance checks from Stage 3 reference resolution.
- Stage 1b semantic validation now reports `AFFORDANCE_INVALID_METER` and `ENABLED_AFFORDANCES_INVALID`.
- Moved semantic validation earlier in `UniverseCompiler.compile()` so these failures are reported before symbol-table and reference resolution.
- Added direct module regressions proving loaded DTOs reach semantic validation before those policies are enforced.

Verification:

```bash
uv run pytest tests/test_townlet/unit/universe/test_pipeline_modules.py::test_validate_v21_semantics_rejects_affordance_cost_with_unknown_meter tests/test_townlet/unit/universe/test_pipeline_modules.py::test_validate_v21_semantics_rejects_affordance_interaction_with_unknown_meter tests/test_townlet/unit/universe/test_pipeline_modules.py::test_validate_v21_semantics_rejects_unknown_enabled_affordance -q
uv run pytest tests/test_townlet/unit/universe/test_pipeline_modules.py tests/test_townlet/unit/universe/test_compiler_validation.py tests/test_townlet/unit/universe/test_compiler_cli.py tests/test_townlet/unit/universe/test_action_space_composition.py -q
uv run ruff check src/townlet/universe/raw_configs_v21.py src/townlet/universe/validation/semantics.py src/townlet/universe/validation/references.py src/townlet/universe/compiler.py tests/test_townlet/unit/universe/test_pipeline_modules.py
uv run black --check src/townlet/universe/raw_configs_v21.py src/townlet/universe/validation/semantics.py src/townlet/universe/validation/references.py src/townlet/universe/compiler.py tests/test_townlet/unit/universe/test_pipeline_modules.py
uv run mypy src/townlet/universe/raw_configs_v21.py src/townlet/universe/validation/semantics.py src/townlet/universe/validation/references.py src/townlet/universe/compiler.py
```

### Grid Capacity Policy Moved Out of Raw Config Construction

Fixed in `src/townlet/universe/raw_configs_v21.py`, `src/townlet/universe/validation/semantics.py`, and `tests/test_townlet/unit/universe/test_pipeline_modules.py`.

- Removed per-level entity-capacity policy from `RawConfigsV21.__post_init__`.
- Stage 1b semantic validation now owns `GRID_CAPACITY_EXCEEDED` over loaded DTOs.
- Kept hard substrate-size limits in `RawConfigsV21` for now; those are security/size guardrails, not vocabulary or cross-document reference policy.
- Added a direct module regression proving an overfull grid config can load as typed DTOs and then fail in semantic validation.

Verification:

```bash
uv run pytest tests/test_townlet/unit/universe/test_pipeline_modules.py::test_validate_v21_semantics_rejects_grid_capacity_exceeded -q
uv run pytest tests/test_townlet/unit/universe/test_pipeline_modules.py tests/test_townlet/unit/universe/test_compiler_validation.py tests/test_townlet/unit/universe/test_compiler_cli.py tests/test_townlet/unit/universe/test_action_space_composition.py -q
uv run ruff check src/townlet/universe/raw_configs_v21.py src/townlet/universe/validation/semantics.py tests/test_townlet/unit/universe/test_pipeline_modules.py
uv run black --check src/townlet/universe/raw_configs_v21.py src/townlet/universe/validation/semantics.py tests/test_townlet/unit/universe/test_pipeline_modules.py
uv run mypy src/townlet/universe/raw_configs_v21.py src/townlet/universe/validation/semantics.py
```

### Runtime VFS Registry Variables Emitted by Compiler

Fixed in `src/townlet/universe/compilers/vfs.py`, `src/townlet/universe/compiler.py`, `src/townlet/environment/vectorized_env.py`, `tests/test_townlet/unit/universe/test_vfs_profile_compilation.py`, and `tests/test_townlet/unit/environment/test_vectorized_env_runtime.py`.

- Added `VFSCompiler.build_runtime_variables()` to merge observation/environment VFS variables with global and agent variables from compiled VFS profiles.
- Stage 6 now stores the registry-ready VFS variable list in `CompiledUniverse.LevelMetadata.vfs_variables`.
- `VectorizedHamletEnv` no longer appends profile-derived `VariableDef` objects at startup; it consumes the compiled list directly.
- Added compiler and environment regressions proving profile variables are emitted once and runtime registry initialization preserves the compiled variable list exactly.

Verification:

```bash
uv run pytest tests/test_townlet/unit/universe/test_vfs_profile_compilation.py::test_compiler_emits_runtime_vfs_variables_from_profiles tests/test_townlet/unit/environment/test_vectorized_env_runtime.py::test_vectorized_env_uses_compiled_vfs_variables_without_profile_synthesis -q
uv run pytest tests/test_townlet/unit/universe/test_vfs_profile_compilation.py tests/test_townlet/unit/environment/test_vectorized_env_runtime.py tests/test_townlet/unit/universe/test_compiled_universe_serialization.py tests/test_townlet/unit/universe/test_compiler_cache.py -q
uv run pytest tests/test_townlet/unit/universe/test_pipeline_modules.py tests/test_townlet/unit/universe/test_compiler_validation.py tests/test_townlet/unit/universe/test_compiler_cli.py tests/test_townlet/unit/universe/test_action_space_composition.py tests/test_townlet/unit/universe/test_vfs_observation_marking.py tests/test_townlet/unit/environment/test_vectorized_env_runtime.py -q
uv run ruff check src/townlet/universe/compilers/vfs.py src/townlet/universe/compiler.py src/townlet/environment/vectorized_env.py tests/test_townlet/unit/universe/test_vfs_profile_compilation.py tests/test_townlet/unit/environment/test_vectorized_env_runtime.py
uv run black --check src/townlet/universe/compilers/vfs.py src/townlet/universe/compiler.py src/townlet/environment/vectorized_env.py tests/test_townlet/unit/universe/test_vfs_profile_compilation.py tests/test_townlet/unit/environment/test_vectorized_env_runtime.py
uv run mypy src/townlet/universe/compilers/vfs.py src/townlet/universe/compiler.py src/townlet/environment/vectorized_env.py
```

### Runtime Effects Schema Emitted by Compiler

Fixed in `src/townlet/universe/compilers/effects.py`, `src/townlet/universe/compiler.py`, `src/townlet/universe/compiled.py`, `src/townlet/environment/vectorized_env.py`, `tests/test_townlet/unit/universe/test_effects_schema_completeness.py`, `tests/test_townlet/unit/universe/test_compiled_universe_serialization.py`, `tests/test_townlet/unit/universe/test_compiler_cache.py`, and `tests/test_townlet/unit/environment/test_vectorized_env_runtime.py`.

- Added `EffectsCompiler.build_schema()` for the effect expression schema used by effect catalog compilation and runtime affordance compilation.
- `CompiledUniverse` now persists `effects_schema` and direct cache loading treats it as a required current-schema field.
- Bumped compiled schema to `1.6` for this artifact. The current schema is now `1.7` after the runtime action-space artifact change.
- `VectorizedHamletEnv` no longer rebuilds the effect expression schema from meter/VFS metadata; it consumes `CompiledUniverse.effects_schema` and fails loudly if the artifact is missing.
- `VectorizedHamletEnv` also passes the compiled schema to `ItemManager` instead of rebuilding a separate item interaction schema at startup.
- Added regressions proving item VFS paths, bars, runtime-only effect variables, serialization, cache strictness, runtime consumption, and item-manager schema wiring all use the compiled schema.

Verification:

```bash
uv run pytest tests/test_townlet/unit/universe/test_effects_schema_completeness.py tests/test_townlet/unit/universe/test_compiled_universe_serialization.py::test_compiled_universe_serializes_effects_schema tests/test_townlet/unit/universe/test_compiled_universe_serialization.py::test_compiled_universe_deserializes_effects_schema tests/test_townlet/unit/environment/test_vectorized_env_runtime.py::test_vectorized_env_uses_compiled_effects_schema tests/test_townlet/unit/environment/test_vectorized_env_runtime.py::test_vectorized_env_passes_compiled_effects_schema_to_item_manager tests/test_townlet/unit/universe/test_compiler_cache.py::test_direct_cache_load_rejects_missing_current_schema_optional_value_fields -q
uv run pytest tests/test_townlet/unit/universe/test_effects_schema_completeness.py tests/test_townlet/unit/universe/test_compiled_universe_serialization.py tests/test_townlet/unit/universe/test_compiler_cache.py tests/test_townlet/unit/environment/test_vectorized_env_runtime.py -q
uv run pytest tests/test_townlet/unit/universe/test_pipeline_modules.py tests/test_townlet/unit/universe/test_compiler_validation.py tests/test_townlet/unit/universe/test_compiler_cli.py tests/test_townlet/unit/universe/test_action_space_composition.py tests/test_townlet/unit/universe/test_vfs_observation_marking.py tests/test_townlet/unit/environment/test_vectorized_env_runtime.py -q
uv run ruff check src/townlet/universe/compilers/effects.py src/townlet/universe/compilers/vfs.py src/townlet/universe/compiler.py src/townlet/universe/compiled.py src/townlet/environment/vectorized_env.py tests/test_townlet/unit/universe/test_effects_schema_completeness.py tests/test_townlet/unit/universe/test_compiled_universe_serialization.py tests/test_townlet/unit/universe/test_compiler_cache.py tests/test_townlet/unit/environment/test_vectorized_env_runtime.py
uv run black --check src/townlet/universe/compilers/effects.py src/townlet/universe/compilers/vfs.py src/townlet/universe/compiler.py src/townlet/universe/compiled.py src/townlet/environment/vectorized_env.py tests/test_townlet/unit/universe/test_effects_schema_completeness.py tests/test_townlet/unit/universe/test_compiled_universe_serialization.py tests/test_townlet/unit/universe/test_compiler_cache.py tests/test_townlet/unit/environment/test_vectorized_env_runtime.py
uv run mypy src/townlet/universe/compilers/effects.py src/townlet/universe/compilers/vfs.py src/townlet/universe/compiler.py src/townlet/universe/compiled.py src/townlet/environment/vectorized_env.py
```

### Runtime Action Space Emitted by Compiler

Fixed in `src/townlet/universe/dto/action_metadata.py`, `src/townlet/universe/compilers/actions.py`, `src/townlet/universe/compiler.py`, `src/townlet/universe/compiled.py`, `src/townlet/environment/vectorized_env.py`, `tests/test_townlet/unit/universe/test_compiled_universe_serialization.py`, `tests/test_townlet/unit/universe/test_compiler_cache.py`, and `tests/test_townlet/unit/environment/test_vectorized_env_runtime.py`.

- Added `RuntimeAction` and `RuntimeActionSpace` as compiler-emitted runtime DTOs.
- Stage 6 now stores a runtime-ready action space for every compiled level.
- `CompiledUniverse` persists `runtime_action_space` and direct cache loading treats it as a required current-schema field.
- Bumped compiled schema to `1.7`.
- `VectorizedHamletEnv` no longer asks the substrate for default actions while constructing the runtime action space; it consumes the compiled artifact and derives `action_ids` from it directly.
- Added a red/green runtime regression that compiles first, monkeypatches `Grid2DSubstrate.get_default_actions()` to fail, and proves environment creation consumes the compiled runtime action space.

Verification:

```bash
uv run pytest tests/test_townlet/unit/environment/test_vectorized_env_runtime.py::test_vectorized_env_uses_compiled_runtime_action_space_without_substrate_rebuild tests/test_townlet/unit/universe/test_compiled_universe_serialization.py::test_compiled_universe_serializes_runtime_action_space tests/test_townlet/unit/universe/test_compiled_universe_serialization.py::test_compiled_universe_deserializes_runtime_action_space tests/test_townlet/unit/universe/test_compiler_cache.py::test_direct_cache_load_rejects_missing_required_top_level_fields tests/test_townlet/unit/universe/test_compiler_cache.py::test_direct_cache_load_rejects_missing_metadata_collection_fields -q
```

### Safety Limits Moved Out of Raw Config Construction

Fixed in `src/townlet/universe/raw_configs_v21.py`, `src/townlet/universe/validation/limits.py`, `src/townlet/universe/compiler.py`, and `tests/test_townlet/unit/universe/test_resource_limits.py`.

- Removed hard environment, action, variable, item-catalog, grid-size, and spawn-rule limit policy from `RawConfigsV21.__post_init__`.
- Added `validate_v21_limits()` as an explicit compiler validation stage over loaded DTOs.
- `RawConfigsV21` now owns DTO construction and the local "at least one level loaded" invariant rather than cross-document safety policy.
- Existing compiler-facing resource-limit behavior still fails loudly through structured `CompilationError` diagnostics.

Verification:

```bash
uv run pytest tests/test_townlet/unit/universe/test_resource_limits.py -q
rg -n "MAX_|Too many|safety limit|spawn rules exceed|Grid size exceeds|GridND size exceeds|item_types exceeds" src/townlet/universe/raw_configs_v21.py src/townlet/universe/validation/limits.py src/townlet/universe/compiler.py
```

### Temporal Day-Length Normalization Moved to Optimization Compiler

Fixed in `src/townlet/universe/compilers/optimization.py`, `src/townlet/universe/compiler.py`, and `tests/test_townlet/unit/universe/test_pipeline_modules.py`.

- Added `OptimizationCompiler.resolve_day_length()`.
- `UniverseCompiler._stage_6_compile_levels()` now delegates optimization day-length normalization instead of embedding that domain rule inline.

Verification:

```bash
uv run pytest tests/test_townlet/unit/universe/test_pipeline_modules.py::test_optimization_compiler_normalizes_inactive_temporal_day_length -q
```

## Remaining Work

### Follow-Up: Cache/Provenance Extraction

Files:

- `src/townlet/universe/compiler.py`
- `src/townlet/universe/cache.py`
- `tests/test_townlet/unit/universe/`

The architecture-review findings are addressed. The remaining cleanup is optional follow-up: decide whether cache path, fingerprint, mtime, and provenance helpers should move behind a dedicated artifact-cache module.

Candidate targets still visible in `compiler.py`:

- cache path selection and directory preparation
- config hash and mtime normalization
- provenance-id construction

Acceptance for that follow-up:

- Cache/provenance implementation details live outside the compiler facade.
- Existing cache fast-path, stale-cache, and direct-load tests continue to pass.

Verification:

```bash
uv run pytest tests/test_townlet/unit/universe/test_compiler_cache.py tests/test_townlet/unit/universe/test_compiled_universe_serialization.py -q
uv run ruff check src/townlet/universe tests/test_townlet/unit/universe
uv run mypy src/townlet/universe
```

## Final Gate

Run this after the remaining tasks are complete:

```bash
uv run pytest tests/test_townlet/unit/universe tests/test_townlet/unit/environment tests/test_townlet/integration/test_compile_time_wiring.py tests/test_townlet/integration/test_world_compiler_full.py -q
uv run ruff check src/townlet/universe src/townlet/environment tests/test_townlet/unit/universe tests/test_townlet/unit/environment
uv run black --check src/townlet/universe src/townlet/environment tests/test_townlet/unit/universe tests/test_townlet/unit/environment
uv run mypy src
```
