# SG1 — Universe Compiler (UAC)

**Location:** `src/townlet/universe/` (5,750 LOC, 34 files)
**Confidence:** High — all top-level source files read in full; per-stage citations grounded in source. Two areas flagged as Medium confidence (transition-graph hash construction lives largely in `townlet.vfs`, and the `compiled.py` MessagePack codec is large and only spot-sampled).

## Responsibility

The Universe Compiler ("UAC") is the **producer of a single immutable artifact, `CompiledUniverse`**, from a v2.1 hierarchical YAML config pack on disk.

- **Producer:** `UniverseCompiler.compile(experiment_dir, primary_level, use_cache=True)` (`compiler.py:102`) consumes a directory containing experiment-scoped YAML (`experiment.yaml`, `stratum.yaml`, `environment.yaml`, `actions.yaml`, `brain.yaml`, `vfs_profiles.yaml`, `items.yaml`, plus per-level `levels/<name>/{curriculum,bars,affordances,training,drive}.yaml`).
- **Consumer side:** Runtime systems load `CompiledUniverse` and treat it as the **single source of truth** for action space, observation spec, meter/affordance metadata, VFS variable schemas, drive/reward function, transition-graph hashes, and serialised cache fingerprints. Concrete consumers: `townlet.training.checkpoint_utils` (`checkpoint_utils.py:14`), `townlet.demo.runner.DemoRunner` (`runner.py:32-33`), `townlet.demo.live_inference` (`live_inference.py:30-31`), `townlet.environment.vectorized_env.VectorizedHamletEnv` (`vectorized_env.py:55,76`), `townlet.environment.env_factory.build_environment` (`env_factory.py:13,58`), `townlet.agent.network_factory`/`networks` (`network_factory.py:17`, `networks.py:11`).
- The artifact is also cached to `<experiment_dir>/.compiled/universe.msgpack` and validated against a multi-axis fingerprint (config hash + mtime + provenance ID over `compiler_version`, `git_sha`, `python_version`, `torch_version`, `pydantic_version`).

The subsystem additionally exposes a CLI (`python -m townlet.universe {compile,inspect,validate}`) used by `.github/workflows/config-validation.yml` (per `CLAUDE.md`; not verified in this scope).

## Compilation pipeline

`CLAUDE.md` claims a **seven-stage pipeline**: parse → symbol table → resolve → cross-validate → metadata → optimization → emit/cache. The actual implementation is **a 9-step pipeline with a pre-flight band and 7 logged inner stages**. The numbered `_log_stage` markers in `compiler.py:158-231` go from 1 to 8 (a logging-counter "Stage", not the conceptual stage); confusingly, comments label the same steps with a different numbering ("Stage 0" through "Stage 7"). The conceptual stages, in execution order, are:

| # | Conceptual stage | Entry point | Input → output |
|---|---|---|---|
| 0a | Config-dir preflight (path safety) | `loaders/preflight.py:validate_config_dir` (`compiler.py:109`) | `Path` → exception on missing/non-dir |
| 0b | Scoping preflight (file placement) | `loaders/preflight.py:validate_scoping` (`compiler.py:112`) | `Path` → exception if `vfs_profiles.yaml`/`items.yaml` missing at root or `effects.yaml`/`vfs_profiles.yaml` at level scope |
| 0c | Cache fast-path | `compiler.py:115-153` | `Path` + on-disk `.compiled/universe.msgpack` → returns cached `CompiledUniverse` iff config-hash + mtime + provenance-ID match |
| 0d | YAML syntax sweep | `loaders/preflight.py:validate_yaml_syntax` (`compiler.py:155`) | `Path` → exception aggregating `YAML_SYNTAX_ERROR` diagnostics |
| 1 | Parse v2.1 configs | `loaders/v21.py:load_v21_configs` → `RawConfigsV21.from_experiment_dir` (`compiler.py:159`, `raw_configs_v21.py:77-291`) | `Path` → `LoadedConfigBundle(raw=RawConfigsV21)` |
| 2 | Enforce safety limits | `validation/limits.py:validate_v21_limits` (`compiler.py:164`) | `RawConfigsV21` → exception or pass (caps: 100 meters / 100 affordances / 500 cascades / 300 actions / 200 variables / 10 000 grid cells / 200 item types / 200 VFS profiles / 200 spawn rules per item) (`limits.py:14-24`) |
| 3 | Cross-validate semantics | `validation/semantics.py:validate_v21_semantics` (`compiler.py:168`) | `RawConfigsV21` → exception (vision-support compatibility, temporal day_length, substrate-action validator, continuous interaction_radius, cascade-graph cycles, meter/affordance vocabulary alignment between `environment.yaml` and per-level files, opening-hours/deployment presence, grid-capacity feasibility, DAC presence) (`semantics.py:55-340`) |
| 4 | Build symbol table | `validation/references.py:build_symbol_table` (`compiler.py:172`) | `RawConfigsV21` → `UniverseSymbolTable` (registers meters, cascades, affordances, env variables, VFS-profile variables, custom actions, items) (`references.py:14-58`) |
| 5 | Resolve references | `validation/references.py:resolve_references` + `validate_dac_references` (`compiler.py:176`) | `(raw, symbol_table)` → `ResolvedConfigBundle`; raises `CompilationError` with codes `UAC-RES-CASCADE`, `UAC-RES-VFS`, `UAC-RES-ITEM`, `DAC-REF-001..015` (`references.py:61-294`) |
| 5.5 | Select primary level | `validation/semantics.py:select_primary_level` (`compiler.py:181`) | `(levels, requested_name)` → `str` |
| 6 | Stage 5 in source — shared artifacts | `UniverseCompiler._stage_5_prepare_shared_artifacts` (`compiler.py:279-322`) | `RawConfigsV21` → `SharedCompilerArtifacts` (bar schema, `CompiledVFSProfiles`, effects schema, `EffectCatalog`, VFS history spec, `VFSObservationSpec`); delegates to `compilers/vfs.py:VFSCompiler` and `compilers/effects.py:EffectsCompiler` |
| 7 | Stage 6 in source — per-level compilation | `UniverseCompiler._stage_6_compile_levels` (`compiler.py:324-474`) | `RawConfigsV21` + shared artifacts → `CompiledLevelBundle` (per-level `LevelMetadata` + universe metadata + VFS expression schema + observation marks). Inside the loop: `ObservationCompiler.build_spec` / `build_activity`, `ActionCompiler.build_action_space_metadata` / `build_runtime_action_space`, `MetadataCompiler.build_{meter,affordance}_metadata`, `OptimizationCompiler.build_optimization_data`, `VFSCompiler.{compile_item_spawn_conditions,build_runtime_variables}`, plus eight `compile_vtc_*_with_phase_graph` calls and a `compute_transition_graph_hash` (`compiler.py:387-413`) |
| 8 | Stage 7 in source — emit + cache | `UniverseCompiler._stage_7_emit_artifact` (`compiler.py:476-551`) | `CompiledLevelBundle` + shared artifacts → `CompiledUniverse`; persists to `<experiment_dir>/.compiled/universe.msgpack` via `CompiledUniverse.save_to_cache` (`compiled.py:509`) |

**Discrepancy with `CLAUDE.md`:** the claimed seven-stage pipeline ("parse → symbol table → resolve → cross-validate → metadata → optimization → emit/cache") is misleading in two ways.
1. The actual order is **safety-limits + cross-validate → symbol-table → resolve-references**, not the other way around. The semantic cross-validation (`validate_v21_semantics`) runs **before** the symbol table is constructed (`compiler.py:163-176`); it operates directly on raw DTOs rather than via the symbol table. The symbol table is then used only by reference-resolution and DAC reference validation.
2. There is no separate "metadata" stage. `UniverseMetadata` is built **inside** the level-compilation stage by `MetadataCompiler.build_universe_metadata` (`compiler.py:454-460`, `metadata.py:90-187`).

If we keep the seven-conceptual-stage framing for narrative purposes, the honest mapping is: **preflight → parse → limits → semantics → symbols+resolve → shared-artifacts → per-level compile → emit/cache** (eight, not seven, if we keep preflight; seven if we collapse symbols+resolve into "resolve").

## Key components

- `compiler.py` (710 lines) — `UniverseCompiler` orchestrator class. Owns sub-compiler instances (cues, observation, action, effects, metadata, optimization, VFS), the cache fast-path (`_cache_artifact_path`, `_build_cache_fingerprint`, `_compute_provenance_id` at lines 591-696), and pydantic-model SHA-256 hashing (`_compute_pydantic_hash`, `compiler.py:553-559`). The orchestration sits in `compile()` at line 102-258.
- `pipeline.py` (59 lines) — Typed stage-boundary dataclasses (`LoadedConfigBundle`, `ResolvedConfigBundle`, `SharedCompilerArtifacts`, `CompiledLevelBundle`, `CompiledArtifactBundle`). No logic — just frozen carriers between stages.
- `compiled.py` (1,009 lines) — `CompiledUniverse` frozen dataclass + `LevelMetadata` inner class + `CompiledVFSProfiles` + serialisation codec. Provides `save_to_cache` / `load_from_cache` (`compiled.py:509-528`, MessagePack), `to_dict` / `from_dict` (`compiled.py:296-507`), `clone`, `metadata_for_level`, `to_level`, `as_single_level`, `create_environment`. `COMPILED_SCHEMA_VERSION = "1.12"` at line 47.
- `raw_configs_v21.py` (291 lines) — `RawConfigsV21` and `CurriculumLevel` dataclasses; `from_experiment_dir` classmethod is the single YAML-load entry point for the v2.1 file layout.
- `__main__.py` (189 lines) — CLI entry point: `compile`, `inspect`, `validate` subcommands. All three require `--primary-level` (`__main__.py:27,48`); no implicit level selection.
- `errors.py` (107 lines) — `CompilationMessage`, `CompilationError`, `CompilationErrorCollector`. Diagnostics carry `(code, message, location)` and aggregate before raising.
- `source_map.py` (101 lines) — `_LineNumberLoader` + `SourceMap`: annotates YAML mappings with `__line__` for friendlier `path:line` error reporting. Tracks affordances, cascades, custom actions.
- `symbol_table.py` (134 lines) — `UniverseSymbolTable`: separate dicts for meters, cascades, affordances (by id and by name), variables, profile-VFS variables, actions (by integer id), cues, items. Duplicates raise `CompilationError("Stage 2: Symbol Table", ...)`.
- `cues_compiler.py` (143 lines) — `CuesCompiler.validate`. Verifies cue thresholds in `[0,1]`, references to known meters, and that visual cue ranges per meter cover `[0,1]` without gaps or overlaps. **Note:** the `CuesCompiler` instance is constructed in `compiler.py:78` but is **not invoked** by `UniverseCompiler.compile()` in the version on disk; see Concerns.
- `optimization.py` (21 lines) — `OptimizationData` frozen dataclass (cascade tensors, modulation entries, affordance position map). Docstring at line 14 admits "placeholders so downstream plumbing can be validated."

### `compilers/` (sub-compiler boundaries)

- `compilers/actions.py` (216 lines) — `ActionCompiler.build_action_space_metadata` synthesises actions from `actions.yaml` (substrate-inherited + custom) plus item commands (`GET`, `USE_SLOT_n`, `DROP_SLOT_n`, item local/inventory commands). Reserved-name enforcement at line 105-107. `build_runtime_action_space` (line 188) emits the runtime `RuntimeAction` tuple.
- `compilers/effects.py` (77 lines) — `EffectsCompiler.build_schema` constructs the runtime type schema for effect expressions (bar, vfs, target.vfs, intensity/duration). `compile_catalog` delegates to `EffectCatalog.from_config`. Reference-type whitelist at line 11.
- `compilers/metadata.py` (187 lines) — `MetadataCompiler` (instantiated in `compiler.py:88-94` with callbacks for mtime/fingerprint/git-sha). Builds `MeterMetadata`, `AffordanceMetadata`, and the top-level `UniverseMetadata` including substrate-type-dependent grid size/cells/position-dim (`metadata.py:108-126`) and explicit-`config_version` enforcement (`metadata.py:149-156`).
- `compilers/observation.py` (545 lines) — `ObservationCompiler.build_spec`. Largest sub-compiler. Builds `ObservationSpec` field-by-field with field types `spatial_grid` (global encoding, local window), `vector` (position, velocity, meters, affordance one-hot, effects, custom env vars, VFS, temporal). Vision-support × active-vision matrix enforced at lines 49-60. Continuous substrates delegate to a runtime `SubstrateFactory.build` to derive position-dim (line 148-155), which is unusual for a compile stage.
- `compilers/optimization.py` (99 lines) — `OptimizationCompiler.build_optimization_data` synthesises cascade and modulation tensors against the meter-index lookup. Performs additional referential validation (`raise ValueError` at lines 52, 71, 80) duplicating some semantics-stage checks.
- `compilers/vfs.py` (298 lines) — `VFSCompiler` is the heaviest auxiliary compiler. `compile_profiles` delegates to `VFSProfileCompiler.compile_global_profile`/`compile_item_profile`; `build_runtime_variables` synthesises registry-ready `VariableDef` tuples from profile compilations + observation/environment variables + the optional `variables_reference.yaml`; `compile_item_spawn_conditions` parses and type-checks spawn `when:` expressions into ASTs that are stored on the rule objects (line 200-203, "(type-check and store AST on rules)") — a notable **mutation through a 'frozen' compile path**, see Concerns.

### `validation/`

- `validation/feasibility.py` (24 lines) — Single helper `grid_capacity_for_substrate` reused by limits and semantics.
- `validation/limits.py` (91 lines) — Hard size caps; constants are the single source of truth (`MAX_METERS`, `MAX_AFFORDANCES`, `MAX_CASCADES`, `MAX_ACTIONS`, `MAX_VARIABLES`, `MAX_GRID_CELLS`, `MAX_CACHE_FILE_SIZE`, `EFFECT_OBSERVATION_SLOTS=8`, `MAX_ITEM_TYPES`, `MAX_VFS_PROFILES`, `MAX_SPAWN_RULES_PER_ITEM`).
- `validation/references.py` (294 lines) — Two passes: `build_symbol_table` (line 14) and `resolve_references` (line 228). The latter validates per-level cascade endpoints, affordance interaction VFS variable references, item-appearance item_type refs, then dispatches `validate_dac_references` for drive-as-code references (15 distinct error codes `DAC-REF-001..015` at lines 67-225).
- `validation/semantics.py` (341 lines) — `validate_v21_semantics`. Cycles in cascade graph (`_detect_cycles`, line 24), vision/temporal compatibility, substrate-action compatibility via `SubstrateActionValidator`, continuous substrate `interaction_radius` requirement, level-vs-experiment meter/affordance vocabulary alignment, grid-capacity feasibility, affordance opening_hours and deployment positions, DAC presence.

### `dto/`

All frozen dataclasses; module docstrings only:

- `dto/__init__.py` (31 lines) — Re-exports all public DTOs.
- `dto/action_metadata.py` (125 lines) — `ActionMetadata`, `ActionSpaceMetadata` (with `get_action_mask` PyTorch helper at line 52), `RuntimeAction`, `RuntimeActionSpace`.
- `dto/affordance_metadata.py` (43 lines) — `AffordanceInfo`, `AffordanceMetadata`.
- `dto/meter_metadata.py` (34 lines) — `MeterInfo`, `MeterMetadata`.
- `dto/observation_activity.py` (45 lines) — `ObservationActivity` carrying `active_mask`, `group_slices`, `active_field_uuids`.
- `dto/observation_spec.py` (100 lines) — `ObservationField`, `ObservationSpec`, `compute_observation_field_uuid` (SHA256-derived 16-char UUIDs).
- `dto/universe_metadata.py` (71 lines) — `UniverseMetadata` (immutable, includes provenance fields: `provenance_id`, `compiler_git_sha`, `python_version`, `torch_version`, `pydantic_version`).

### `loaders/`

- `loaders/v21.py` (13 lines) — Thin wrapper: `load_v21_configs(experiment_dir) -> LoadedConfigBundle`.
- `loaders/preflight.py` (168 lines) — `validate_config_dir`, `validate_scoping`, `validate_yaml_syntax`. The scoping pass enforces the rule that `vfs_profiles.yaml` and shared `items.yaml` live only at experiment root and `effects.yaml` may not appear in `levels/<name>/`.

### `adapters/`

- `adapters/vfs_adapter.py` (176 lines) — `vfs_to_observation_spec` adapter function + `VFSAdapter.build_observation_activity` static method. **Note:** this adapter is **not called from within `universe/`** (no callers found via grep within the universe scope of the dependency map collected above). Likely consumed by tests (`tests/.../test_vfs_adapter.py`) or by an external runtime caller.

## Public API surface

`townlet/universe/__init__.py` is a single-line module that **re-exports only `dto`** (`__init__.py:3-5`):

```python
from townlet.universe import dto  # noqa: F401
__all__ = ["dto"]
```

External callers therefore import the compiler/artifact directly from the submodules:
- `from townlet.universe.compiler import UniverseCompiler`
- `from townlet.universe.compiled import CompiledUniverse`
- `from townlet.universe.dto import ObservationSpec, ObservationActivity, MeterMetadata, RuntimeActionSpace, ...`

The `__init__.py` is **not** a curated public surface; the universe package effectively exposes its full source tree as API. (See Concerns.)

**CLI subcommands** (`__main__.py`):

| Subcommand | Required args | Effect |
|---|---|---|
| `compile <config_dir> --primary-level X [--no-cache]` | `config_dir`, `--primary-level` | Compile, print metadata + five hash digests, optionally write cache |
| `inspect <artifact-or-dir> [--format table|json]` | `artifact` | Load from `.compiled/universe.msgpack` (auto-resolves directory → artifact path), print metadata + hashes |
| `validate <config_dir> --primary-level X` | `config_dir`, `--primary-level` | Compile-without-cache lint pass; print elapsed ms |

All three exit non-zero on `CompilationError` or `FileNotFoundError` (`__main__.py:172-185`).

## DTOs (input and output)

### Input: `RawConfigsV21` (`raw_configs_v21.py:48-291`)

Frozen dataclass aggregating loaded pydantic configs:

- Experiment-scope (required): `experiment: ExperimentConfig`, `stratum: StratumConfig`, `environment: EnvironmentConfig`, `actions: ActionsConfig`, `brain: BrainConfig`
- Experiment-scope (optional): `items: ItemsCatalogConfig | None`, `vfs_profiles: VFSProfilesConfig | None`, `effects: EffectsConfig | None`, `action_label_overrides: dict[int, str] | None`, `variables_reference: tuple[VariableDef, ...] | None`
- Per-level: `levels: dict[str, CurriculumLevel]` where each `CurriculumLevel` carries `curriculum`, `bars`, `affordances`, `drive`, `training`, optional `items_appearance`
- Provenance: `experiment_dir: Path`

Load is via `RawConfigsV21.from_experiment_dir(path)` (`raw_configs_v21.py:77`). It aggregates errors into a single `CompilationErrorCollector("Stage 1: Load v2.1 Configs")` and raises one consolidated `CompilationError` on failure (`raw_configs_v21.py:215-216, 269-276`).

**The "v2.1" naming is current.** It is referenced 18+ times in source comments and stage labels (e.g. `compiler.py:158,164,167`, `validation/limits.py:27,29`, `loaders/v21.py:11`, `raw_configs_v21.py:78,82`), and in active validation stage labels visible in error output.

### Output: `CompiledUniverse` (`compiled.py:108-294`)

Frozen dataclass — schema version `1.12` (`compiled.py:47`). Required fields enumerated as a tuple at lines 49-89; the inner `LevelMetadata` class (`compiled.py:171-200`) carries per-level state, while top-level fields mirror the **primary** level. Notable groupings:

- **Primary-level mirrors:** `metadata`, `observation_spec`, `observation_activity`, `vfs_observation_fields`, `observation_schema_hash`, `vfs_variables`, `variable_schema_hash`, `action_space_metadata`, `runtime_action_space`, `action_schema_hash`, `transition_graph_hash`, `vfs_hash`, `meter_metadata`, `affordance_metadata`, `optimization_data`
- **Shared raw configs (verbatim):** `experiment`, `stratum`, `environment`, `actions`, `brain`, `items_catalog`
- **Compiled VFS/effects:** `compiled_vfs_profiles`, `compiled_effect_catalog`, `effects_schema`, `effect_observation_slots`, `vfs_expression_schema`, `vfs_history_spec`, `vfs_observation_marks`, `vfs_observation_spec`
- **Provenance hashes:** `drive_hash`, `brain_hash`, `experiment_hash`, `stratum_hash`, `environment_hash`, `actions_hash`, `items_hash`
- **Multi-level:** `all_levels: dict[str, LevelMetadata] | None`

### Side artifacts

- **Symbol table** (`UniverseSymbolTable` in `symbol_table.py`): in-memory only, lives across stages 4-5 in `compile()` (`compiler.py:172-176`) then dropped. Not part of `CompiledUniverse`.
- **`SourceMap`** (`source_map.py`): line-number registry for friendly diagnostics. Constructed implicitly via `_LineNumberLoader`; not currently wired into `UniverseCompiler.compile()` flow as observed in source.
- **`CompilationError`** (`errors.py:29`): structured exception with `stage`, `issues: list[CompilationMessage]`, `hints`, `warnings`. Raised on failure of every stage.
- **Cache artifact:** `<experiment_dir>/.compiled/universe.msgpack` written by `CompiledUniverse.save_to_cache` (`compiled.py:509`).

## Validation strategy

The compiler runs validation **in four bands** before any artifact is constructed:

1. **Filesystem preflight** (`loaders/preflight.py`): config directory existence, path-traversal-string heuristic (`validate_config_dir` at line 15-34), scoping (no `vfs_profiles.yaml`/`effects.yaml` at level scope; required `vfs_profiles.yaml`/`items.yaml` at root), and a YAML-syntax sweep across all required and optional files. Error codes: `SCOPING_LEVEL_DIRECTORY`, `SCOPING_MISSING_EXPERIMENT_FILE`, `SCOPING_FORBIDDEN_LEVEL_FILE`, `MISSING_FILE`, `MISSING_LEVELS_DIR`, `YAML_SYNTAX_ERROR`.

2. **Limits** (`validation/limits.py`): hard upper bounds on entity counts, item-type count, grid cell count, and per-item spawn rules. All caps are module-level constants. Error codes: `CONFIG_LIMIT_EXCEEDED`, `ITEM_TYPES_LIMIT_EXCEEDED`, `GRID_SIZE_LIMIT_EXCEEDED`, `SPAWN_RULE_LIMIT_EXCEEDED`.

3. **Semantics** (`validation/semantics.py`): cross-DTO consistency. Vision-support × active-vision matrix; temporal `day_length` required when temporal active; `SubstrateActionValidator` compatibility (warnings escalated to errors at `semantics.py:130-134`); continuous-substrate `interaction_radius`; modulation/cascade graph references; cascade-graph cycle detection via DFS (`_detect_cycles` at line 24-52); meter/affordance vocabulary alignment between `environment.yaml` and `levels/<name>/{bars,affordances}.yaml`; missing/extra cascades and modulations at level scope; affordance `opening_hours`/`deployment.positions` required; grid-capacity feasibility (agents + affordances). Roughly 18 distinct error codes from `VISION_INCOMPATIBLE` through `AFFORDANCE_DEPLOYMENT_POSITIONS_MISSING`, `GRID_CAPACITY_EXCEEDED`, `LEVEL_DRIVE_MISSING`, etc.

4. **References** (`validation/references.py`): build the symbol table (Stage 4) and then resolve names referenced from per-level configs. Catches affordance interaction VFS variable refs, level-scope cascade meter refs, item-appearance `item_type` refs, then dispatches DAC reference validation across modifiers, extrinsic strategies, shaping bonuses (15 distinct `DAC-REF-*` codes).

All errors flow through `CompilationErrorCollector.add(...)` (`errors.py:60-107`); each stage calls `errors.check_and_raise()` so failures of one stage never silently advance.

The classes form a clear **separation of concerns**:
- **feasibility** = pure helpers about substrate geometry,
- **limits** = "how big can this config be?" (resource caps),
- **semantics** = "do the loaded DTOs make internal sense together?" (cross-references and topology), and
- **references** = "do named identifiers all resolve?" (symbol-table-based name resolution).

There is some duplication between `semantics` and `references` (e.g. cascade-graph endpoints are checked in both `semantics.py:162-168` against env names and `references.py:243-259` against the symbol table); both paths run, so the user gets the same error twice on a malformed cascade.

## Dependencies

### Inbound (callers of universe outside the package)

Sourced from `grep -rn "from townlet.universe" src/townlet/`:

- `townlet.training.checkpoint_utils` (`checkpoint_utils.py:14`) — checkpoint-side validation: `attach_universe_metadata`, `config_hash_warning`, `assert_checkpoint_dimensions`, `assert_checkpoint_vfs_hash` (lines 22, 45, 68, 123)
- `townlet.demo.runner.DemoRunner` (`runner.py:32-33,83,111,265,326`) — constructs `UniverseCompiler()`, stores `compiled: CompiledUniverse | None`, used by `save_checkpoint` / `load_checkpoint`
- `townlet.demo.live_inference` (`live_inference.py:30-31,113-114`) — same pattern as DemoRunner
- `townlet.environment.vectorized_env.VectorizedHamletEnv` (`vectorized_env.py:29,55,76,827,836`) — top-level runtime consumer; constructor takes `universe: CompiledUniverse`
- `townlet.environment.env_factory.build_environment` (`env_factory.py:9,13,58`)
- `townlet.agent.network_factory` (`network_factory.py:17`) — uses `ObservationSpec` for input-dim derivation
- `townlet.agent.networks` (`networks.py:11`) — uses `ObservationActivity` + `ObservationSpec` for masking
- `townlet.items.manager` (`manager.py:614`) — refers to `UniverseCompiler` in a runtime error message about missing pre-compiled spawn AST
- `townlet.config.items_config:382` — comment references `UniverseCompiler` mutating `when_ast` on rule objects (confirms the AST-mutation contract)

Top-level `townlet/__init__.py:4` describes the project's central abstraction as `CompiledUniverse` artifacts produced by `UniverseCompiler`, confirming the subsystem's role as the **compile-time spine** of the runtime.

### Outbound (universe → other subsystems)

From a survey of imports in `src/townlet/universe/`:

- `townlet.config.*` — every per-domain pydantic config: `actions_config`, `affordances_v2_config`, `bars_v2_config`, `brain_config`, `cues`, `curriculum_config`, `drive_as_code`, `effects_config`, `environment_config`, `experiment_config`, `items_config`, `stratum_config`, `training_v2_config`, `vfs_profiles_config`
- `townlet.environment.action_config`, `townlet.environment.action_labels`, `townlet.environment.substrate_action_validator` — used by `compilers/actions.py` and `validation/semantics.py`
- `townlet.substrate.factory.SubstrateFactory` — called from `compilers/actions.py:70` and `compilers/observation.py:148` (compile-time invocation of runtime substrate to read defaults)
- `townlet.effects.catalog.EffectCatalog`, `townlet.effects.schema.{CommandNode, CommandType}` — effects compilation and codec
- `townlet.vfs.observation_builder.VFSObservationSpec`, `townlet.vfs.profiles.{CompiledGlobalProfile, CompiledItemProfile, VFSProfileCompiler, CircularDependencyError}`, `townlet.vfs.schema.{VariableDef, ObservationField, VariableScope, NormalizationSpec, load_variables_reference_config}`, `townlet.vfs.schema_hashes.{compute_action_schema_hash, compute_observation_schema_hash, compute_transition_graph_hash, compute_variable_schema_hash, compute_vfs_hash}`, `townlet.vfs.transition_graph.TransitionPhaseGraph`, `townlet.vfs.vtc.compile_vtc_*` — VFS/VTC is the **most-coupled** outbound dependency
- `townlet.world.expression.ExpressionParser`, `townlet.world.expression.type_checker.{TypeChecker, TypeCheckError}` — used to parse and type-check item spawn `when:` expressions in `compilers/vfs.py:187-203`

The directed dependencies are clean: universe → (config, environment, substrate.factory, effects, vfs, world.expression) and **nothing imports back into universe from those packages** within the surveyed grep results. The only flagged inversion is the compile-time call to `SubstrateFactory.build(...)` for default-action discovery and continuous-substrate observation-dim derivation — see Concerns.

## Patterns observed

- **Stage-by-stage diagnostic aggregation.** Every stage uses a `CompilationErrorCollector` (`errors.py:60`) and `errors.check_and_raise()` to batch all issues before raising. Compilation never short-circuits on the first error within a stage. Examples: `loaders/preflight.py:39,99`, `validation/limits.py:29,91`, `validation/semantics.py:57`, `validation/references.py:16,234`.
- **Frozen dataclass DTOs as inter-stage contracts.** `LoadedConfigBundle`, `ResolvedConfigBundle`, `SharedCompilerArtifacts`, `CompiledLevelBundle`, `CompiledArtifactBundle` in `pipeline.py` document the type at every transition. Plus all DTOs in `dto/` are `frozen=True`.
- **Sub-compiler boundaries inside the orchestrator.** `UniverseCompiler.__init__` (lines 77-96) constructs domain-specific compilers (`ObservationCompiler`, `ActionCompiler`, `EffectsCompiler`, `MetadataCompiler`, `OptimizationCompiler`, `VFSCompiler`, `CuesCompiler`). Each sub-compiler is stateless across calls — methods take everything they need as args.
- **Schema hashes as cache keys.** Five distinct hashes are computed at compile time (`vfs_hash`, `action_schema_hash`, `observation_schema_hash`, `variable_schema_hash`, `transition_graph_hash`) plus pydantic-model JSON-dump SHA-256 hashes on every shared and per-level config (`compiler.py:204-209, 416-420, 553-559`). These propagate into `UniverseMetadata.config_hash`, `provenance_id`, and are used at checkpoint load (`training/checkpoint_utils.py`).
- **No-defaults discipline (consistent with `CLAUDE.md`).** Multiple `raise ValueError` paths assert required-but-missing fields, e.g. `compiler.py:104` (no implicit primary_level), `compilers/optimization.py:22` (no implicit `day_length`), `compilers/metadata.py:131-156` (explicit `experiment.version` required).
- **Provenance binding.** The cache fingerprint (`compiler.py:591-604`, `_compute_provenance_id` at line 671-696) hashes not just config content but also compiler version + git SHA + python/torch/pydantic versions. The cache will not be reused if any of these differ — strong reproducibility guarantee.
- **MessagePack codec with explicit schema-version field.** `COMPILED_SCHEMA_VERSION = "1.12"` (`compiled.py:47`) and `REQUIRED_COMPILED_UNIVERSE_FIELDS` tuple (lines 49-89) is used by `from_dict` to surface missing fields explicitly. Suggests the team has hit codec-evolution pain before.

Test naming in `tests/test_townlet/unit/universe/` corroborates these patterns: `test_compiler_pipeline.py`, `test_compiler_cache.py`, `test_compiler_validation.py`, `test_compiler_normalization.py`, `test_compiler_cli.py`, `test_compiled_universe.py`, `test_compiled_universe_serialization.py`, `test_symbol_table.py`, `test_scoping_enforcement.py`, `test_resource_limits.py`, `test_pipeline_modules.py`, `test_vfs_observation_marking.py`, `test_vfs_expression_schema.py`, `test_vfs_profile_compilation.py`, `test_observation_modes.py`, `test_observation_activity.py`, `test_action_space_composition.py`, `test_effects_catalog_compilation.py`, `test_item_profile_compilation.py`, `test_vision_range_no_defaults.py`.

## Concerns

- **Dead/unused code: `CuesCompiler`.** `compiler.py:78` instantiates `self._cues_compiler = CuesCompiler()` but a grep for `_cues_compiler.` within `compiler.py` returns no callsites in the version on disk. The cue-validation pipeline (formerly Stage 4 per `cues_compiler.py:16` docstring) appears orphaned. Either (a) deliberate dead code in the middle of a refactor or (b) cues validation has been moved elsewhere (not observed in this scope). At pre-release with the no-backwards-compat rule, this should be deleted or wired in.

- **Compile-time invocation of runtime `SubstrateFactory.build()`.** Twice — `compilers/actions.py:70` to get default actions, and `compilers/observation.py:148-155` to derive continuous-substrate observation dimensions. The latter even constructs a `torch.device("cpu")` substrate. This couples compile-time correctness to runtime substrate constructors; any side effect or import-time cost in `SubstrateFactory` propagates into config-validation latency and into the CI `validate` workflow path.

- **Inconsistent stage numbering in source.** `_log_stage` markers count 1 through 8 (`compiler.py:158-231`), while inline comments use 0-7, while `errors.CompilationError(stage=...)` arguments use yet a third labelling ("Stage 1b", "Stage 2: Symbol Table", "Stage 3: Reference Resolution"). And `CLAUDE.md` claims seven. Each is internally consistent but the project lacks a single authoritative stage map.

- **Duplicate referential checks.** Cascade endpoint validity is verified in `validation/semantics.py:162-168` (against environment meter names), `validation/references.py:243-259` (against the symbol table built from environment meters), and again in `compilers/optimization.py:48-57` (raising `ValueError`). The same wrong cascade source name will surface three diagnostics from three different stages.

- **Mutation through a "compile" path on rule DTOs.** `VFSCompiler.compile_item_spawn_conditions` (`compilers/vfs.py:169-203`) parses spawn `when:` expressions and writes the parsed AST back onto the `ItemsAppearanceConfig` rule objects (`rule.when_ast = ast`, line 203). The comment at `compiler.py:364` is explicit ("type-check and store AST on rules") and `config/items_config.py:382` confirms the contract. This means the **"raw" `RawConfigsV21` is mutated in place during compilation** — it is no longer raw after `_stage_6_compile_levels` runs. Anything that captures the raw bundle before this stage and reads it after will see the mutation. The `RawConfigsV21` dataclass is `frozen=True`, but mutation of a non-frozen child object (the rule) is not prevented. This deserves either documentation or refactor to make the AST a side-table.

- **Empty `__init__.py` for the package.** `townlet/universe/__init__.py` re-exports only `dto`. Every external caller imports from deep submodule paths (`townlet.universe.compiler`, `townlet.universe.compiled`). This works but means the "public API" boundary is implicit — any submodule rename will break external code. Stronger curated re-exports (`from townlet.universe import UniverseCompiler, CompiledUniverse`) would document intent.

- **`compiled.py` is 1,009 lines, dominated by serialisation.** Roughly half of the file is hand-written MessagePack codec for nested compiled domain objects (effect catalogs, command pipelines, profile variables, affordance position tensors). Anything that adds a new field to `CompiledUniverse` requires touching `REQUIRED_COMPILED_UNIVERSE_FIELDS`, `to_dict`, `from_dict`, `clone`, plus often several `_serialize_*`/`_deserialize_*` helpers. This is the most likely site of subtle bugs as the artifact schema evolves; `COMPILED_SCHEMA_VERSION = "1.12"` already attests to that history.

- **`OptimizationData` admits incompleteness.** `optimization.py:13-17` docstring: "Stage 6 will progressively populate these fields; for now we provide placeholders so downstream plumbing can be validated." Not a defect per se, but worth flagging to the validator that this artifact is partial.

- **Vfs_adapter has no in-package caller.** `adapters/vfs_adapter.py:62` (`vfs_to_observation_spec`) and `VFSAdapter.build_observation_activity` (line 104) are not invoked from within `src/townlet/universe/`. Either consumed by tests/external callers or stale.

## Open questions for the validator

1. Is the **seven-stage** narrative in `CLAUDE.md` and `docs/UNIVERSE-COMPILER.md` aligned with the actual 9-step pipeline (`preflight → cache-check → yaml-syntax → parse → limits → semantics → symbols → resolve → shared → per-level → emit`)? Recommend updating documentation to match implementation, or pruning the implementation to match docs.
2. **Is `CuesCompiler` intentionally orphaned?** The class is instantiated in `__init__` but I could find no caller in `compiler.py`. Has cue validation been folded into `validation/semantics.py`, deferred, or simply forgotten?
3. **Is the in-place mutation of `rule.when_ast` during compilation an architectural intent or a shortcut?** It violates the otherwise-strong "frozen DTOs flow through stages" pattern. The advisor pack on `items.manager` (`items/manager.py:614`) suggests the runtime _requires_ this mutation to have happened — so the cache layer (which loads from MessagePack without re-running `compile_item_spawn_conditions`) needs to be checked for whether spawn-condition ASTs survive round-trip serialisation. If yes, the mutation can be eliminated; if no, the cache may silently re-parse on first runtime access — worth confirming.
4. **Why does the compiler build a runtime `SubstrateFactory` at compile time?** The two callsites (`compilers/actions.py:70`, `compilers/observation.py:148`) can probably be replaced with substrate-config introspection, decoupling compile time from runtime substrate constructors.
5. **Confirm whether `townlet.universe.adapters.vfs_adapter` has any consumers** (tests or external). If not, it is dead.
6. **The `transition_graph_hash` construction calls eight `compile_vtc_*` functions from `townlet.vfs.vtc`.** This places the bulk of the transition-graph compilation logic outside `universe/` — should that subsystem be classified as part of UAC, or is `vfs` truly the owner? (Subsystem boundary question that a sibling explorer covers.)
