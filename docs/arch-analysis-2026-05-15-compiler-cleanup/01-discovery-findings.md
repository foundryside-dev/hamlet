# Compiler Discovery Findings

## Compiler Surface

The current compiler is centered on `src/townlet/universe/compiler.py`. It is already shaped like a seven-stage compiler pipeline:

1. Parse v2.1 configs.
2. Build symbol table.
3. Resolve references.
4. Cross-validate semantics.
5. Enrich shared schemas and effects.
6. Compile levels and optimization data.
7. Emit compiled universe.

The implementation is not yet modular in the same way. `UniverseCompiler` contains stage orchestration, YAML syntax checks, config scoping, schema construction, v2.1 validation, old flat-pipeline methods, metadata construction, observation layout, action metadata generation, optimization tensor generation, cache fingerprinting, cache persistence, and provenance helpers.

## Key Files

- `src/townlet/universe/compiler.py`: Main compiler orchestration and most compiler logic. 4,431 lines.
- `src/townlet/universe/raw_configs_v21.py`: v2.1 raw config loader plus broad invariants. 562 lines.
- `src/townlet/universe/compiled.py`: `CompiledUniverse` artifact, level metadata, cache serialization, cache deserialization, and runtime adapter helpers. 682 lines.
- `src/townlet/universe/symbol_table.py`: named entity registry for meters, cascades, affordances, variables, actions, and items.
- `src/townlet/effects/parser.py`: effect command config -> `CommandNode` parsing.
- `src/townlet/effects/compiler.py`: command expression parsing and type-checking.
- `src/townlet/effects/catalog.py`: effect catalog compilation and deterministic effect IDs.
- `src/townlet/environment/vectorized_env.py`: largest runtime consumer of `CompiledUniverse`; also rehydrates some compiled VFS data back into config-shaped DTOs.

## Current Compiler Flow

`UniverseCompiler.compile()` performs validation, cache lookup, stage execution, artifact emission, and optional cache write in one method. Cache lookup happens before YAML syntax validation and swallows cache-load exceptions by logging and recompiling.

The active v2.1 path is:

- `compile()`
- `_validate_config_dir()`
- `_validate_scoping()`
- `_phase_0_validate_yaml_syntax()`
- `_stage_1_load_v21_configs()`
- `_stage_2_build_symbol_table()`
- `_stage_3_resolve_references()`
- `_validate_v21_semantics()`
- `_stage_5_prepare_shared_artifacts()`
- `_stage_6_compile_levels()`
- `_stage_7_emit_artifact()`

## Runtime Consumption

`CompiledUniverse` still exposes both primary-level top-level fields and `all_levels`. Runtime entry points should prefer explicit `level_name` plus `universe.get_level(level_name)`.

`VectorizedHamletEnv.__init__()` mostly follows that rule, but it also reads top-level metadata and top-level `universe.vfs_variables`, then appends variables from compiled VFS profiles. It also reconstructs `VFSObservationSpec` by converting compiled variables back into config payloads. That round-trip is a modernization target: the runtime should consume compiler-emitted runtime DTOs directly instead of rebuilding config DTOs from artifacts.

## Backwards Compatibility and Fallback Debt

The most important cleanup candidates found in this pass:

- Old flat-pipeline private methods remain in `compiler.py`: `_stage_4_cross_validate`, `_stage_5_compute_metadata`, `_stage_5_build_rich_metadata`, `_stage_6_optimize`, and `_load_observation_exposures`. Some raise immediately, but large helper bodies remain reachable only through private tests.
- `tests/test_townlet/unit/universe/test_compiler_validation.py` still pins old private validation helpers using `MagicMock` raw config shapes instead of the v2.1 compile path.
- `CompiledUniverse.from_dict()` uses missing-key fallbacks for fields like `optimization_data_raw`, `action_mask_table`, `observation_activity`, level metadata, and VFS fields. This conflicts with the pre-release policy: stale cache artifacts should fail loudly against the schema version, not fabricate empty runtime state.
- `CommandConfig` and `CommandNode` carry compatibility aliases and hidden defaults: `distribution` as an alias for `sample`, `iterator_var` and `do_commands` alongside `iterator` and `body`, and default target/intensity/cascade strength values.
- The compiler normalizes `active_vision="local"` to `"partial"`, which is a compatibility alias unless the config schema intentionally still allows `local`.
- `RawConfigsV21.from_experiment_dir()` treats zero-capacity `items.yaml` as disabled. If the compiler contract requires `items.yaml`, zero-capacity should either be a valid explicit empty item system throughout or a hard config error.
- `VectorizedHamletEnv` has runtime fallback behavior for temporal-inactive `day_length`, VFS evaluation mode via environment variable, and rehydrated VFS observation config. Some of this may be legitimate runtime policy, but it should be made explicit in compiler artifacts instead of inferred ad hoc.

## Existing Tracker/Doc Signals

There are already open docs/bug notes aligned with this cleanup:

- `docs/bugs/JANK-05-observation-activity-backcompat-empty-masks.md`: stale cache fallback silently creates empty observation activity.
- `docs/bugs/JANK-04-allow-unfeasible-universe-masks-critical-feasibility-failures.md`: feasibility severity can be downgraded too broadly.
- `docs/plans/2025-11-25-test-suite-dead-code-cleanup.md`: existing plan for policy-violating test fallback patterns.

## Primary Recommendation

Do not start by extracting random helper functions from `UniverseCompiler`. Start by deleting compatibility surfaces and pinning the active compiler contract:

1. Make the artifact/cache schema strict.
2. Delete old flat-pipeline methods and tests.
3. Move active stages into small modules with typed stage inputs/outputs.
4. Replace runtime artifact rehydration with direct compiled runtime DTOs.
5. Then split validation, observation, action, effects, optimization, and cache/provenance into cohesive modules.

