# Subsystem Catalog

This catalog describes the 6 logical subsystems of `src/townlet/` (the active codebase; `src/hamlet/` is obsolete). Each entry was produced by an independent Explore subagent and synthesised here without alteration. See [00-coordination.md](00-coordination.md) for the analysis plan and [01-discovery-findings.md](01-discovery-findings.md) for project-level context.

## Table of Contents

1. [Declarative Compilation Pipeline](#1-declarative-compilation-pipeline-universe--vfs--effects)
2. [Configuration / DTO Layer](#2-configuration--dto-layer)
3. [Environment Runtime & DAC Reward Engine](#3-environment-runtime--dac-reward-engine)
4. [Physical Layer](#4-physical-layer-substrate--world--items)
5. [RL Core](#5-rl-core-agent--population--training--exploration)
6. [Orchestration & Periphery](#6-orchestration--periphery-curriculum--recording--demo)
7. [Cross-Subsystem Summary](#cross-subsystem-summary)

---

# 1. Declarative Compilation Pipeline (universe + vfs + effects)

**Location:** `src/townlet/universe/`, `src/townlet/vfs/`, `src/townlet/effects/`

**Responsibility:** Compile declarative v2.1 experiment configs (YAML + Pydantic DTOs) into typed, validated CompiledUniverse artifacts with integrated VFS profiles, effect catalogs, and runtime schemas for multi-level training curricula.

**Internal Structure:**

- **universe/** — Seven-stage compiler orchestration (config load → validation → symbol table → reference resolution → shared artifact enrichment → per-level compilation → artifact emission). Breaks into domain adapters (`compilers/`), typed DTOs (`dto/`), filesystem loaders (`loaders/`), and cross-cutting validation (`validation/`).
- **vfs/** — Variable & Feature System: declarative state-space layer with Pydantic schemas, profile compilation, observation building, and runtime evaluation. Decoupled from universe/ at the interface level; compiler pulls VFS profiles and builds schemas.
- **effects/** — Effect DSL: schema (CommandNode AST), parser (config → AST), compiler (expression validation), catalog (indexed effects), and runtime executor/scheduler. Split: compile-side (parser, compiler) validates against type schema; runtime-side (executor, manager, scheduler) executes pre-compiled commands.

**Key Components:**

- **universe/compiler.py** (656 lines) — `UniverseCompiler` entry point; orchestrates eight-stage pipeline with cache fast-path, config mtime fingerprinting, and per-level artifact emission via domain-specialized compilers.
- **universe/pipeline.py** — Typed stage boundaries: `LoadedConfigBundle`, `ResolvedConfigBundle`, `SharedCompilerArtifacts`, `CompiledLevelBundle`, `CompiledArtifactBundle`. Enforces handoff contracts between stages.
- **universe/compiled.py** (995 lines) — `CompiledUniverse` artifact: immutable multi-level container with msgpack serialization, cache validation via `config_hash + provenance_id + mtime`, and frozen dataclass structure. `REQUIRED_COMPILED_UNIVERSE_FIELDS` enforces deserialization integrity.
- **universe/compilers/effects.py** — `EffectsCompiler`: builds runtime effect expression schema from bars + environment variables + compiled VFS profiles; delegates catalog compilation to `EffectCatalog.from_config()`.
- **universe/compilers/vfs.py** — `VFSCompiler`: orchestrates `VFSProfileCompiler` over v21 profiles (global, agent, item scopes); builds runtime variable defs, expression schemas, item spawn condition ASTs, observation marks (curriculum active flags).
- **universe/compilers/{actions,observation,optimization,metadata}.py** — Domain boundaries: `ActionCompiler`, `ObservationCompiler`, `OptimizationCompiler`, `MetadataCompiler` (handles versioning, git_sha, config fingerprint).
- **universe/dto/\*.py** — Typed metadata DTOs: `UniverseMetadata`, `ObservationSpec`, `ObservationActivity`, `ActionSpaceMetadata`, `MeterMetadata`, `AffordanceMetadata`, `RuntimeAction`, `RuntimeActionSpace`.
- **universe/loaders/{v21,preflight}.py** — `v21.py`: minimal wrapper around `RawConfigsV21.from_experiment_dir()`. `preflight.py`: config directory validation, YAML syntax checking, level-vs-experiment scoping enforcement.
- **universe/validation/{semantics,references,limits,feasibility}.py** — Validation phases: semantics (cross-reference checks, cascade graph cycles, primary level selection), references (symbol table + resolution), limits (safety bounds), feasibility (grid capacity).
- **universe/adapters/vfs_adapter.py** — Bridges VFS `ObservationField` → compiler `ObservationSpec`; infers field types, maps variable scopes, builds `ObservationActivity` activity mask and group slices.
- **vfs/schema.py** — `VariableDef`, `VariableScope`, `NormalizationSpec`, `WriteSpec`, `ObservationField`.
- **vfs/registry.py** — `VariableRegistry`: runtime tensor storage with scope-aware access control (reader="agent"/"engine", writer="engine" only).
- **vfs/observation_builder.py** — `VFSObservationSpec`: definition of what VFS variables are observed; lazy observation extraction at runtime.
- **vfs/profiles.py** — `CompiledGlobalProfile`, `CompiledItemProfile`; `VFSProfileCompiler` orchestrates compilation.
- **vfs/evaluator.py** — `VFSEvaluator`: interprets VFS expressions at runtime against `VariableRegistry`.
- **vfs/history.py** — VFS temporal history tracking (optional).
- **effects/schema.py** — `CommandNode` (pre-compiled AST representation): `CommandType` enum (`MODIFY`, `SPAWN_EFFECT`, `SPAWN_ITEM`, `SAMPLE`, `IF`, `FOR_EACH`, `SWITCH`, `REDUCE`, `PARALLEL`, `DELAY`, etc.). Each node carries `value_ast`, `condition_ast`, `target_ast` — expressions pre-parsed by compiler.
- **effects/parser.py** — `CommandParser`: config DTO → `CommandNode`.
- **effects/compiler.py** — `CommandCompiler`: type-checks expressions against schema; compiles expressions into pre-compiled ASTs.
- **effects/catalog.py** — `CompiledEffect`: on_spawn/on_tick/on_despawn/on_interrupt command lists. `EffectCatalog`: deterministic effect_name_to_id mapping for observation encoding.
- **effects/manager.py** — `EffectManager`, `ActiveEffect`: runtime lifecycle tracking.
- **effects/executor.py** — `CommandExecutor`: interprets pre-compiled `CommandNode`s at runtime via `Evaluator`. **No expression parsing at runtime** (perf: ASTs pre-compiled).
- **effects/scheduler.py** — `Scheduler` + `ScheduledItem`: manage effect dispatch across ticks.
- **effects/context.py** — `ExecutionContext`: effect command execution environment.
- **effects/collections.py** — Runtime collections (for_each targets).

**Pipeline Flow:**

1. **Stage 0 (Preflight):** Config directory existence, YAML syntax, level-vs-experiment scoping rules.
2. **Stage 1 (Load v2.1):** `RawConfigsV21.from_experiment_dir()` parses experiment/, brain/, stratum/, environment/, actions/, items/, vfs_profiles.yaml, effects.yaml, and levels/\*/curriculum.yaml.
3. **Stage 2 (Limits):** Enforce `MAX_CACHE_FILE_SIZE`, `MAX_VFS_PROFILES`, array bounds, `EFFECT_OBSERVATION_SLOTS`.
4. **Stage 3 (Semantics):** Cross-validate cascade graph cycles, affordance references, selected primary level, action IDs.
5. **Stage 4 (Symbol Table):** Register all named entities into `UniverseSymbolTable`.
6. **Stage 5 (References):** Resolve drive-as-code references, effect references, VFS variable bindings against symbol table.
7. **Stage 6 (Shared Artifacts):** Compile VFS profiles → `CompiledVFSProfiles`; build effects schema; compile `EffectCatalog`.
8. **Stage 7 (Per-Level):** For each curriculum level, compile observations, actions, meters, affordances, optimization data; emit `CompiledUniverse.LevelMetadata`.
9. **Stage 8 (Emit + Cache):** Serialize `CompiledUniverse` to msgpack at cache_path; store `config_hash`, `provenance_id`, `mtime` for fast-path validation on reload.

**Dependencies:**

**Inbound (who consumes compiled artifacts):**
- `townlet/environment/vectorized_env.py` — bootstraps agents/environment from compiled metadata.
- `townlet/environment/affordance_engine.py` — imports `EffectCatalog`, `CommandExecutor`, `ExecutionContext`.
- `townlet/items/action_handlers.py`, `townlet/items/manager.py` — effects execution for item lifecycle.
- `townlet/training/checkpoint_utils.py` — unpickles `CompiledUniverse` from cache for training resumption.
- `townlet/demo/{runner,live_inference}.py` — entry points for experiment validation and inference.

**Outbound:**
- `townlet/config/*.py` — Pydantic config DTOs (ground-truth schema contracts).
- `townlet/world/expression/{expression,type_checker,evaluator,context}.py` — expression parsing/type-checking/runtime evaluation.
- `townlet/environment/substrate_action_validator.py` — action feasibility checking.
- `townlet/world/{bars,agents,affordances}.py` — world model DTOs.

**Patterns Observed:**

1. **Seven-stage pipeline with explicit stage boundaries (pipeline.py):** Dataclasses enforce handoff contracts.
2. **Typed DTO emission:** Pydantic at config layer; frozen dataclasses at universe layer.
3. **Pre-compiled ASTs for expressions:** `CommandCompiler` emits pre-parsed ASTs; `CommandExecutor` never calls the parser at runtime.
4. **Dual-scope VFS:** Compile-side schemas vs. runtime tensor registry.
5. **Domain adapters (universe/compilers/):** Each domain encapsulates its compiler boundary.
6. **Cache fast-path:** `CompiledUniverse.load_from_cache()` validates via `config_hash + provenance_id + mtime`.
7. **Observation activity marking:** `curriculum_active` flags propagate through `VFSAdapter` → `ObservationActivity.active_mask`.

**Concerns:**

1. **VFS Profile Type Annotations (compiled.py:92–93):** `agent_profile: Any | None`, `item_profiles: dict[str, Any] | None` with `# TODO` markers. Should bind to typed compiled profiles. Status: documented intent; not blocking but invites accidental misuse.
2. **Primary-level selection is correctly strict.** Both `validation/semantics.py:15–21` (`select_primary_level`) and `compiler.py:86–87` raise `ValueError` when `primary_level` is `None`. No fallback path exists — the no-backcompat rule is honoured here. (Initial review erroneously flagged a `sorted(levels.keys())[0]` fallback; that code does not exist.)
3. **Optional effects / vfs_profiles:** Both can be None throughout pipeline; callers must guard. Status: guards present.
4. **Cache fingerprinting via external functions:** Provenance/mtime logic split across helpers; fragile to refactor.
5. **`NullItemManager` is duplicated across `environment/null_managers.py:15`, `effects/manager.py:23`, and `effects/context.py:21`.** The catalog (Subsystem 3) says ENV-009 "Consolidates duplicates" — the consolidation is **incomplete**; three implementations still ship.

**Confidence:** **High** — Pipeline explicitly modelled in `pipeline.py` dataclasses; stages are logged and numbered; codebase is post-refactor (the prior 4,431-line `compiler.py` monolith is now 656 lines and modular). Pre-compiled ASTs are visible in `effects/schema.py` and `effects/compiler.py`. VFS type annotations remain loose (`Any`) and cache fingerprinting logic is somewhat opaque.

---

# 2. Configuration / DTO Layer

**Location:** `src/townlet/config/`

**Responsibility:** Provide strictly-typed Pydantic DTOs for all hierarchical v2.1 YAML configuration files, enforcing explicit specification of every behavioral parameter at load-time.

**Key Components:** (22 modules total)

### v2.1 Hierarchical Configuration (Primary)
- `experiment_config.py` — Experiment-level orchestration (metadata, curriculum level sequence)
- `stratum_config.py` — Substrate & temporal capability declarations per level
- `environment_config.py` — Global meter/cascade/modulation/affordance registry
- `agent_config.py` — Perception, drive (reward), and brain (network architecture) configs
- `actions_config.py` — Substrate & custom action definitions, label presets
- `bars_v2_config.py` — Per-level meter configurations
- `affordances_v2_config.py` — Per-level affordance parameters & modulations
- `training_v2_config.py` — Per-level training orchestration
- `curriculum_config.py` — Per-level vision mode, temporal settings, curriculum overrides

### Supporting Configurations
- `drive_as_code.py` — Declarative DAC reward function schemas
- `effects_config.py` — Effect pipeline definitions
- `items_config.py` — Item catalog, appearance, spawn conditions, effects
- `vfs_profiles_config.py` — VFS variable observation profiles & normalization
- `vfs_config.py` — VFS variable registry
- `brain_config.py` — Neural network architecture
- `capability_config.py` — VFS capability declarations
- `cues.py` — Internal meter state → observable cue mappings
- `affordance_masking.py` — Affordance visibility masking metadata
- `exploration.py` — Loader for `ExplorationConfig` (RND, annealing, epsilon-greedy)

### Base Infrastructure
- `base.py` — YAML loading and validation error formatting utilities
- `__init__.py` — v2.1 public API (no legacy re-exports)

**No-Defaults Discipline:**

The package enforces strict "no implicit defaults" via three mechanisms:

1. **Pydantic Field Requirements:** Required fields use `Field(...)` (ellipsis). Optional fields explicitly use `Field(default=None)` or `default_factory=list/dict` with documented intent.
2. **StrictBaseModel:** All config classes inherit from `BaseModel` with `ConfigDict(extra="forbid")` to reject unexpected YAML keys.
3. **Validators & Model Post-Validators:** `@field_validator` and `@model_validator(mode="after")` rules reject invalid configurations at parse time (e.g. `OpeningHoursConfig.validate_schedule_required_when_enabled()`, `MeterBoundsConfig.validate_bounds_order()`, `EffectDefinitionConfig.parse_command_dicts()`).
4. **Lint Enforcement:** `scripts/no_defaults_lint.py` catches function defaults, logical-OR defaults, and framework calls with implicit defaults at CI-time.

**Antipatterns Found:**

1. **`effects_config.py:245`** — `observable: bool = Field(default=True)` violates explicit-intent. Should be `Field(...)`.
2. **`effects_config.py:248–251`** — Lifecycle command lists default to `[]`; YAML omission vs. explicit `[]` not documented.
3. **`drive_as_code.py:602–605`** — `log_components`, `log_modifiers` both default to `True`; behavioural and should be explicit.
4. **`effects_config.py:267`** — `version: Literal["1.0"] = Field(default="1.0")` risks silent schema mismatches; should be required. **`drive_as_code.py:634`** — `version: str = Field(default="1.0", ...)`. The annotation is `str` (not `Literal["1.0"]`), so the silent-schema-drift risk is **worse** than a Literal-typed default: any string value will validate, including future incompatible versions.

**Versioning:**

- **v2.1 Primary:** `bars_v2_config.py`, `affordances_v2_config.py`, `training_v2_config.py` are the modern full-spec configs.
- All experiment/stratum/environment/agent/actions/curriculum configs are v2.1 (no v1 stragglers).
- DAC syntax is version-agnostic; DAC configs carry their own `version` field.
- The `__init__.py` exposes no v1 compatibility shims.

**Dependencies:**

**Inbound:** Configuration consumed by `UniverseCompiler.compile()` via `load_v21_configs()`, `RawConfigsV21.__post_init__()`, the domain compilers (`ActionCompiler`, `EffectsCompiler`, `MetadataCompiler`, `VFSCompiler`, `OptimizationCompiler`), and runtime consumers (`VectorizedHamletEnv`, `ItemManager`).

**Outbound:** Pydantic v2 `BaseModel`, PyYAML; internal cross-imports (`affordances_v2_config` imports `CommandConfig` from `effects_config`; `training_v2_config` imports from `base`).

**Patterns Observed:**

1. **One DTO per YAML.**
2. **Pydantic v2 style** — `model_config = ConfigDict(extra="forbid")`; `Field(...)` for required.
3. **`from_yaml()` classmethod** — load-friendly pattern.
4. **Error context preservation** — `base.format_validation_error()` produces actionable messages.
5. **Conditional validation** — e.g. `ModifierConfig.validate_source()` enforces "exactly one of".

**Concerns:**

1. Implicit `observable=True` default — high-risk for silent incorrect behaviour.
2. Hard-coded `version="1.0"` defaults risk silent schema drift; `drive_as_code.py:634` is `version: str` (un-Literal'd), so any string will validate — the risk is worse than the other version-default sites.
3. Empty-list-vs-omission semantics for lifecycle commands undocumented.
4. `drive_as_code.py` (~670 lines) could benefit from submodule organisation.
5. No v1 legacy visible — confirm old experiment dirs cannot silently load as v2.1.

**Confidence:** **High** — All 22 files reviewed; commit `92979107` (dead-default cleanup at experiment-root boundary) verified; `__init__.py` omits legacy loaders; `base.py` + `format_validation_error()` demonstrate intentional error-first design; no-defaults lint is active in CI.

---

# 3. Environment Runtime & DAC Reward Engine

**Location:** `src/townlet/environment/`

**Responsibility:** Vectorized batched GPU-native runtime that executes action-step-observation loops for all agents in parallel, applying meter dynamics, effects, and DAC-based reward computation.

**Key Components:**

- **`vectorized_env.py`** (2,200 lines) — Central orchestrator. `VectorizedHamletEnv` manages the full tick lifecycle: action validation, meter depletion, cascading effects, VFS evaluation, terminal conditions, effect scheduling, meter recovery from Effects, retirement checks, and DAC reward calculation. 38 methods. **Largest single file in the codebase; primary refactoring candidate.**
- **`dac_engine.py`** (1,012 lines) — `DACEngine` takes compiled DAC YAML specs (via `DriveConfig` or `DriveAsCodeConfig`) and builds GPU-native reward computation graphs. Compiles modifiers into `torch.where`-based range lookups, extrinsic strategies, and shaping bonuses. Formula: `reward = extrinsic + (intrinsic_raw × base_weight × modifier1 × modifier2...) + shaping`. Returns components dict for logging.
- **`action_builder.py` + `action_config.py` + `action_labels.py` + `substrate_action_validator.py`** — Action assembly & validation chain. `ComposedActionSpace` maintains complete action list (substrate + custom + affordance) with disabled actions masked but still assigned IDs (action_dim same across curriculum levels). `SubstrateActionValidator` ensures substrate↔action compatibility.
- **`affordance_config.py` + `affordance_engine.py` + `affordance_layout.py`** — `AffordanceEngine` (625 lines) processes instant and multi-tick affordance interactions using the Effects system; handles operating hours (via `temporal_utils.is_affordance_open()`); applies affordability checks. Converts affordance specs into `CompiledAffordance` (on_start/per_tick/on_completion/...).
- **`meter_dynamics.py`** (221 lines) — Tensor-driven meter updates: passive base depletions (curriculum-modulated), cascade rules, modulation multipliers, terminal condition checks. Pre-computes cascade/modulation tables at init for GPU performance.
- **`temporal_utils.py`** (78 lines) — **Single source of truth** for affordance operating hours. Canonical `is_affordance_open(time_of_day, operating_hours)` centralises wraparound logic (supports [8,18], [18,28], [22,6], [0,24]). Extracted from `UniverseCompiler._is_open()` to fix JANK-09.
- **`null_managers.py`** (67 lines) — Null-object pattern. `NullItemManager` provides no-op tick/process_respawns when items disabled, raises on `spawn_item`. Consolidates duplicates (ENV-009).

**Runtime Flow (One Tick):**

1. **Action Execution** → `_execute_actions()`: movement (substrate delta application), interaction (instant or multi-tick affordance), wait. Validates affordance availability via temporal masks.
2. **Meter Depletion** → `meter_dynamics.deplete_meters()`: base passive decay × curriculum multiplier.
3. **Cascading** → Three cascade passes (secondary→primary, tertiary→secondary, tertiary→primary).
4. **Effects Tick** → `effect_manager.tick()`: active Effects modify bars; results synced back to meters.
5. **VFS Evaluation** → Global profile evaluation; updated values written to `vfs_registry._storage`.
6. **Terminal Checks** → `meter_dynamics.check_terminal_conditions()`.
7. **Item Lifecycle** → `item_manager.tick()` (age/despawn), `process_respawns()`.
8. **Retirement** → Agents reaching `max_steps_per_episode` marked done + bonus +1.0 reward.
9. **DAC Reward** → `dac_engine.calculate_rewards()`: extrinsic, intrinsic×modifiers, shaping.
10. **Temporal Increment** → `time_of_day = (time_of_day + 1) % day_length` if temporal_mechanics enabled.
11. **Observation** → `_get_observations()`: build `[num_agents, obs_dim]` from meters, VFS, positions, affordances, effects.

**DAC Engine Internals:**

- **Modifier Compilation** (`_compile_modifiers()`): YAML range definitions → GPU-optimized functions using `torch.where()`. Bar indices via `bar_index_map`; VFS variables resolved at init.
- **Extrinsic Paths**: `multiplicative`, `constant_base_with_shaped_bonus`. Dual-schema (`drive_as_code` vs `agent_config`) via hasattr/getattr.
- **Intrinsic Modulation**: `intrinsic = intrinsic_raw × base_weight × Π(modifiers)`.
- **Shaping**: Placeholder reward bonuses (not yet deeply used).
- **Device Validation** (ENV-007): all tensors must match `DACEngine` device.

**Dependencies:**

- **Inbound**: `population/base.py` → `VectorizedHamletEnv.from_universe()`; `population/vectorized.py`; `demo/runner.py`, `demo/live_inference.py`.
- **Outbound**: `universe.compiled` (CompiledUniverse), `substrate.*`, `vfs.registry` / `vfs.evaluator` / `vfs.observation_builder`, `effects.executor`, `items.ItemManager`, `config.drive_as_code`, `config.agent_config`.

**Patterns Observed:**

- **Vectorization throughout** — `[num_agents, ...]` shaped tensors; zero per-agent loops in the hot path.
- **Null-object pattern** — `NullItemManager`, `null_effect_manager` for optional subsystems; fail-fast on misuse.
- **Config schema dual-path** — `DACEngine` supports both `DriveConfig` and `DriveAsCodeConfig` via hasattr/getattr.
- **Metadata-driven runtime** — action space, affordance positions, temporal masks, observation specs all materialised from `CompiledUniverse`.
- **Closure-based compiled functions** — modifiers, extrinsic, shaping compiled into lambdas capturing config at init.

**Concerns:**

1. **`vectorized_env.py` size (2,200 lines)** — natural decomposition candidates:
   - `action_executor.py` (`_execute_actions`, `_handle_interactions`, `_handle_instant_interactions`)
   - `observation_encoder.py` (`_get_observations`, `_build_affordance_encoding`, `_encode_position_observation`)
   - `env_factory.py` (expand `from_universe()` pattern)
   - `reward_calculator.py` (`_calculate_shaped_rewards`)
2. **Config rehydration from CompiledUniverse** (lines 190–199, 717–746) — rehydrates `ActionLabels`/`ActionConfigs` from runtime artifacts. Not blocking but watch for recursive unpacking.
3. **hasattr/getattr for dual schemas** (dac_engine.py:110–135, 196, 231, 243, 257) — fragile; strongly-typed schema union would be cleaner.
4. **No residue of RewardStrategy** — confirmed zero mentions of the legacy class.
5. **Temporal mask table initialization** — `action_mask_table.shape[1] == 0` check (line 702) suggests optional temporal metadata; ensure compiler always populates when `temporal_mechanics` enabled.
6. **try/except minimised in hot paths** — good hygiene.

**Confidence:** **High** — well-instrumented with `ENV-007`, `HIGH-01`, `HIGH-02`, `JANK-09` references. Clear separation of concerns. DAC is cohesive and complete. Decomposition roadmap for `vectorized_env.py` is concrete.

---

# 4. Physical Layer (substrate + world + items)

**Location:** `src/townlet/substrate/`, `src/townlet/world/`, `src/townlet/items/`

**Responsibility:** Provides spatial positioning abstractions (Grid2D/3D/ND, Continuous, Aspatial), expression evaluation for dynamic configuration (on_pickup/on_use/on_drop Effects), and inventory + item-instance lifecycle management.

**Internal Structure:**

- **substrate/** — Substrate type hierarchy (8 concrete types): `SpatialSubstrate` protocol, Grid2D/Grid3D/GridND, Continuous1D/2D/3D/ND, Aspatial.
- **world/** — Expression language runtime: type system (`ScalarType`, `BoolType`, `Vec2/3Type`), AST nodes, parser, type checker, evaluator. Used to execute `variable_reference.yaml` expressions in Effects.
- **items/** — Inventory slots `[batch, max_items]`, `ItemInstance` dataclass (position, vfs_index, exclusive, holder_agent_ids), action handlers for on_pickup/on_use/on_drop.

**Substrate Hierarchy:**

```
SpatialSubstrate (abstract protocol)
├── Grid2DSubstrate (8×8 to N×N square grids, position_dim=2)
├── Grid3DSubstrate (cubic grids, position_dim=3)
├── GridNDSubstrate (n-dimensional grids, position_dim=N)
├── Continuous1DSubstrate (1D bounded interval, position_dim=1)
├── Continuous2DSubstrate (2D rectangle, position_dim=2)
├── Continuous3DSubstrate (3D box, position_dim=3)
├── ContinuousNDSubstrate (n-dimensional continuous, position_dim=N)
└── AspatialSubstrate (no positioning, position_dim=0)
```

**Boundary Modes** (all grid types): `clamp`, `wrap`, `bounce`, `sticky`.
**Distance Metrics**: `manhattan`, `euclidean`, `chebyshev`; Aspatial always returns zero.

**World / Expression System:**

The expression evaluator (`Evaluator.evaluate()`) is the runtime interpreter for `variable_reference.yaml` constraint expressions:
- Parses constraint DSL (e.g. `bar.energy > 50 && vfs.is_day`) into AST via `ExpressionParser`.
- Type-checks at compile time via `TypeChecker` (`ScalarType`, `BoolType`, `Vec2/3Type`).
- Evaluates on GPU tensors at runtime via Visitor pattern (`ExecutionContext` provides bars/vfs/affordances/temporal).

**Integration with VFS:** `ExecutionContext.get(path)` resolves dotted paths ("bar.energy", "vfs.is_night", "affordance_positions.water") — used by the Effects compiler to bind constraint expressions and by `CommandExecutor` to evaluate on_pickup/on_use/on_drop Effect commands.

**Items / Inventory:**

- **InventoryState**: fixed-size per-agent inventory `[batch, max_items]`, slots tensor (instance IDs; -1 = empty), items dict for metadata lookup.
- **ItemInstance**: runtime state — position, vfs_index (into item_vfs tensor), exclusive flag, holder_agent_ids (multi-holder support), lifecycle timers (spawn_tick, duration_remaining).
- **ItemActionHandler**: dispatches on_pickup/on_use/on_drop via `CommandExecutor`; evaluates Effects in an execution context with the item's VFS index for self-modification.

**Dependencies:**

- **Inbound:** `environment/` calls `SubstrateFactory.build()`; reads `substrate.position_dim`, `substrate.position_dtype`; calls `substrate.get_default_actions()` (action contract: Movement[0:N] + INTERACT[-2] + WAIT[-1]). `environment/action_builder.py` composes substrate default actions with custom/affordance actions. `vectorized_env.py:185–310` validates substrate compatibility with partial_observability. `effects/` uses `world.expression`. `vfs/` evaluator binds `world.expression.ExecutionContext`.
- **Outbound:** `substrate → config/stratum_config` (read-only); `world.expression → effects/executor`; `items → environment/vectorized_env, effects/executor`. No circular dependencies.

**Patterns Observed:**

1. **Protocol/Strategy** — `SpatialSubstrate` abstract base; concrete implementations override boundary/distance.
2. **Visitor** — AST evaluation.
3. **Factory** — `SubstrateFactory.build()`.
4. **Dataclass + GPU tensors** — `ItemInstance` (Python dataclass) + `InventoryState` (GPU tensor slots).
5. **Execution context** — `ExecutionContext` scoping for expression evaluation.

**Concerns:**

- **`ItemInstance.position`** can be `tuple[int,...]` or `tuple[float,...]` (dual typing, line 23) — position mismatch risk if substrate changes at runtime without updating items.
- **`AspatialSubstrate.get_default_actions()`** (lines 141–162) returns only `[INTERACT]` (1 action), not `[INTERACT, WAIT]` as the base-class docstring implies (line 92). Missing WAIT may break downstream action indexing.
- **Half-implemented vision range** — Grid3D supports `encode_partial_observation()` but `vectorized_env.py` (lines 290, 302–308) rejects 3D POMDP unless `observation_encoding != 'relative'`. Continuous substrates also unsupported (line 262). POMDP practically limited to Grid2D with vision_range ≤ 2.
- **Continuous observation encoding** — config allows `{relative,scaled,absolute}` (`grid2d.py:40`) but `vectorized_env` silently enforces 'relative' for POMDP (line 306).
- **Expression type-mismatch risk** — `TypeChecker` validates at compile time; runtime `ExecutionContext.get()` can return mismatched types if VFS/bars not initialised correctly (no runtime type guard in `Evaluator.visit_*`).

**Confidence:** **High** — Substrate hierarchy is complete, factory pattern well-established, expression system cleanly integrated. Concerns are known limitations and soft type safety, not missing functionality.

---

# 5. RL Core (agent + population + training + exploration)

**Location:** `src/townlet/agent/`, `src/townlet/population/`, `src/townlet/training/`, `src/townlet/exploration/`

**Responsibility:** Coordinate batched DQN training (vanilla/double) with intrinsic exploration (RND, adaptive), manage GPU-resident replay buffers, and orchestrate vectorized population dynamics.

**Internal Structure:**

- `agent/` — Q-network architectures and factories (networks, losses, optimizers)
- `population/` — `VectorizedPopulation` (batched training loop), `AgentRuntimeRegistry` (per-agent state)
- `training/` — `TrainingState`, replay buffers (standard / sequential / prioritized)
- `exploration/` — RND, epsilon-greedy, adaptive intrinsic weighting

### Agent / Networks

- **`SimpleQNetwork`** — MLP `[obs_dim → hidden → hidden → action_dim]`, LayerNorm at each hidden layer.
- **`RecurrentSpatialQNetwork`** — LSTM POMDP agent: vision CNN (25-dim local window → 128), position encoder (conditional on position_dim), meter encoder (8 → 32), affordance encoder (15+none → 32), temporal encoder (4 → 16), LSTM (224 → 256), Q-head (256 → 128 → action_dim). `reset_hidden_state()` at episode boundary.
- **`DuelingQNetwork`** — Wang et al. 2016 decomposition: shared features → V + A, `Q = V + (A − mean(A))`.
- **`StructuredQNetwork`** — Group encoders for semantic observation groups (spatial, bars, affordances, temporal, custom).

Factories (`network_factory.py`, `loss_factory.py`, `optimizer_factory.py`):
- `NetworkFactory.build_feedforward()` / `build_recurrent()`.
- `LossFactory` — MSE, Huber (configurable delta), SmoothL1.
- `OptimizerFactory` — Adam/AdamW with optional LR scheduler (StepLR, ExponentialLR, CosineAnnealingLR).
- **All parameters explicitly specified via config DTOs** (no defaults, per PDR-002).

### Population

`VectorizedPopulation` (`vectorized.py`):
- All `num_agents` share a single Q-network (not one per agent). Tensors `[batch_size, ...]`.
- `AgentRuntimeRegistry`: per-agent tensors for curriculum_stage, survival_time, epsilon, intrinsic_weight; JSON-safe snapshots (`AgentTelemetrySnapshot`).
- Replay wiring: recurrent → `SequentialReplayBuffer`; feedforward → `ReplayBuffer` or `PrioritizedReplayBuffer`. PER not yet supported for recurrent (raises `NotImplementedError`).
- Separate target network, updated every `target_update_frequency` steps. Vanilla vs Double DQN via `brain_config.q_learning.use_double_dqn`.

### Training

- **`RewardTensor` DTO** — Hot-path composition semantics: total (always present) vs optional extrinsic/intrinsic/shaping components. `is_composed=True` for DAC (production); `is_composed=False` for legacy. Eliminates the misleading "zeros in intrinsic" pattern (CRIT-07).
- **`PopulationCheckpoint`**, **`CurriculumDecision`** DTOs.
- **`ReplayBuffer`** — circular GPU-resident; `has_wrapped` flag (HIGH-04).
- **`SequentialReplayBuffer`** — episode-level sequences `[batch, seq_len, obs_dim]` for LSTM training.
- **`PrioritizedReplayBuffer`** — alpha priority weighting (TASK-005 Phase 3); beta annealing from `brain_config.replay.priority_beta_annealing`. Pydantic validator enforces PER params when prioritized=True.

### Exploration

- **`RNDExploration`** — Random Network Distillation: frozen target + trained predictor. Prediction error = novelty signal. Welford running mean/std (CleanRL pattern).
- **`AdaptiveIntrinsic`** — Wraps RND with variance-based annealing. Tracks survival window=100; anneals when variance < threshold (config: **100.0**, raised from 10.0 to prevent premature annealing per comment) AND survival > `min_survival_fraction × max_episode_length`. Weight floor `min_intrinsic_weight`.
- **`EpsilonGreedy`** — vanilla baseline; exponential decay floor.
- **`action_selection.py`** — vectorized utility with optional action masks.

### Q-Learning Variants

- **Plumbing:** `brain_config.q_learning.use_double_dqn`.
- **Feedforward Double DQN** (≈ line 900): selects via online, evaluates via target.
- **Recurrent Double DQN** (lines 780–809): unrolls online to select next_actions per timestep, then evaluates with target (two separate unrolls to maintain hidden state). Vanilla uses target for both.

### Dependencies

- **Inbound:** `src/townlet/demo/runner.py` (instantiates `VectorizedPopulation`); `scripts/run_demo.py` (entry point).
- **Outbound:** `environment/vectorized_env.py` (observation_spec, step, attach_runtime_registry, set_exploration_module); `curriculum/`; `config/brain_config.py`, `config/training_v2_config.py`; `torch`.

### Patterns Observed

- **Factory pattern** for networks/losses/optimizers — declarative, config-driven.
- **Vectorized batch operations** — all Q-learning updates on `[batch, ...]` tensors on GPU; no per-agent loops.
- **DTO composition for rewards** — `RewardTensor` separates composition intent from component storage.
- **Episode-boundary state management** — LSTM hidden state reset via `reset_hidden_state` at episode start.
- **Cold/hot path separation** — checkpoint loading (Pydantic, disk I/O) vs. training loop (GPU tensors, no validation).

### Concerns

1. **Gradient clipping** (`max_grad_norm=10.0`) — config-driven via `TrainingLoopConfig.max_grad_norm`; applied during `_train_on_batch()`. Standard practice.
2. **Adaptive annealing threshold** (`variance_threshold=100.0`) — increased from 10.0 to prevent premature annealing; config-driven. Consider sensitivity analysis across curriculum difficulty.
3. **LSTM hidden-state episode resets** — confirmed correct on both q_network and target_network in recurrent path (lines 778, 783).
4. **PER beta annealing** — TASK-005 Phase 3 partial; verify schedule actually applied during sampling.
5. **Double DQN hidden-state synchronisation (recurrent)** — lines 783–790 reset online network, then unroll twice. Independent forward passes look correct.
6. **RND active mask — verified applied.** `RNDNetwork` registers `active_mask` at `rnd.py:91`; `forward()` at `rnd.py:104–105` applies it as `masked_x = x * active_mask`. (Initial review flagged this as "not visibly applied" — that was wrong.)

### Confidence

**High** — All four packages tightly integrated, well-documented with `PDR`/`TASK` labels. Factories enforce no-defaults discipline (PDR-002). Population vectorization is clear (shared single Q-network). Exploration composition (RND → AdaptiveIntrinsic) is compositional and testable. Q-learning paths plumbed into config. Minor hygiene issues (PER beta, RND mask) but no structural bugs. Pedagogical mission honoured: "interesting failures" like Low Energy Delirium are teaching moments, not bugs.

---

# 6. Orchestration & Periphery (curriculum + recording + demo)

**Location:** `src/townlet/curriculum/`, `src/townlet/recording/`, `src/townlet/demo/`

**Responsibility:** Manage difficulty progression (curriculum), capture training episodes (recording), and host live inference + replay visualization (demo).

### Internal Structure

- **curriculum/** — Strategy pattern for environment difficulty progression
- **recording/** — Asynchronous episode capture, serialization, replay, video export
- **demo/** — WebSocket inference server (port 8766), multi-day runner, SQLite state store, unified orchestrator

### Curriculum

**Protocol:** `CurriculumManager` abstract base class in `base.py`
- `get_batch_decisions()` — Computes per-agent `CurriculumDecision` once per episode (not per step).
- `checkpoint_state()` / `load_state()` — Serialization for resumption.
- `initialize_population(num_agents)` — Per-population setup hook.

**Implementations:**

1. **`AdversarialCurriculum`** (`adversarial.py`):
   - 5-stage progression: Stage 1 (easy, shaped) → Stage 5 (all meters, sparse).
   - Advance: survival rate >70% AND learning progress >0 AND entropy <0.5 AND min_steps_at_stage met.
   - Retreat: survival rate <30% OR learning progress <0.
   - Tracks `PerformanceTracker` (GPU tensors) with episode rewards, steps, baseline for learning delta.
   - Maps stage (1–5) → difficulty_level (0.0–1.0).
   - Emits `transition_events` for telemetry.

2. **`StaticCurriculum`** (`static.py`):
   - No-op; all agents receive identical decision for all episodes.
   - Used for baseline experiments and interface validation.

**Integration with Population:**
- `VectorizedPopulation` calls curriculum once per episode after step collection.
- Curriculum stage exposed in agent telemetry and database.
- Recording criteria can read `curriculum.get_stage_info()` to predict transitions.

### Recording

**Queue-based architecture:** non-blocking async capture via bounded queue + daemon writer thread.

1. **Recorder** (`recorder.py`): `EpisodeRecorder` spawns `RecordingWriter` thread; `record_step(...)` is a thread-safe queue push (clones tensors to CPU). Captures step #, position, 8 normalized meters, action, extrinsic + intrinsic rewards, Q-values, epsilon, temporal fields. Bounded queue (default 1000) prevents backpressure.
2. **Data structures** (`data_structures.py`): `RecordedStep` (frozen dataclass ~100–150 bytes; msgpack + lz4 serialisable), `EpisodeMetadata`, `EpisodeEndMarker`.
3. **Criteria** (`criteria.py`): OR logic across `periodic`, `stage_transitions`, `performance` (top/bottom percentile window=100), `stage_boundaries`.
4. **Replay** (`replay.py`): `ReplayManager` loads episodes from disk; seek + step-by-step access.
5. **Video export** (`video_export.py`, `video_renderer.py`): substrate-aware — Grid types → spatial overlay; Aspatial → abstract affordance / meter view. ffmpeg encodes frames to H.264.

**Dependencies:** core msgpack/lz4 always available; optional `[recording]` extra: ffmpeg-python, pillow, matplotlib.

**Integration:** Recorder initialised in `DemoRunner.run()` if `training_config.recording` is set. `DemoDatabase.insert_episode_recording()` stores metadata + file paths. Recording does **not** enter the training hot loop.

### Demo

**Unified architecture:** training, inference, and frontend coordinated via `UnifiedServer`.

**DemoRunner** (`runner.py`):
- Context manager — `__enter__`/`__exit__` for resource cleanup (SIGINT/SIGTERM handlers).
- Lifecycle: compile v2.1 configs → instantiate env/population/curriculum/exploration/recorder → training loop → checkpoint every 100 episodes → TensorBoard → graceful shutdown.
- `DemoDatabase` (SQLite + WAL) for multi-day resumption.

**Live Inference Server** (`live_inference.py`):
- FastAPI + WebSocket on port 8766.
- Polls filesystem for new checkpoints; hot-loads into population.
- Modes: `inference` (latest checkpoint step-by-step at 0.2s default) and `replay` (recorded trajectory).
- Substrate-aware routing: Grid → `Grid.vue`; Aspatial → `AspatialView.vue`.

**Database** (`database.py`):
- SQLite with WAL mode.
- Tables: `episodes`, `affordance_visits`, `position_heatmap`, `episode_recordings`, `system_state`.

**Unified Server** (`unified_server.py`):
- Orchestrates training thread + inference thread + frontend subprocess (`npm run dev`).
- Copies active config pack into run directory for provenance.
- Coordinates SIGINT/SIGTERM → training stop → inference cleanup → frontend kill.
- **Relationship to `live_inference.py`**: orchestrator delegates inference to `LiveInferenceServer`; no duplication.

### Data Flow (Training → Recording → Replay)

```
VectorizedPopulation.step()
  ↓
EpisodeRecorder.record_step(...)
  ↓ [non-blocking queue push + tensor clone]
RecordingWriter thread
  ↓
RecordingCriteria.should_record(metadata) → (bool, reason)
  ↓ [if yes]
msgpack.dumps() + lz4.compress() → DemoDatabase.insert_episode_recording()
  ↓ [at inference time]
ReplayManager.load_episode(episode_id)
  ↓ [for visualization]
EpisodeVideoRenderer.render_frame() → PNG frames + ffmpeg encode → MP4
```

### Dependencies

- **Inbound:** `scripts/run_demo.py` calls `UnifiedServer.start()`; training loop (population) calls `curriculum.get_batch_decisions()` and `recorder.record_step()`.
- **Outbound:** `environment/` (curriculum feeds into reward shaping + meter depletion); `population/` (curriculum_stage for telemetry); `training/` (checkpoint/resume); `universe/` (CompiledUniverse for config resolution); `substrate/` (substrate type detection for rendering).

### Patterns Observed

- **Curriculum:** Strategy pattern (pluggable `CurriculumManager` ABC).
- **Recording:** Observer (non-blocking queue) + Writer pattern (async I/O isolation).
- **Demo:** Server/Hub (unified orchestrator) + Context Manager (`DemoRunner` cleanup).
- **Replay:** Cursor pattern (`ReplayManager.seek`) for frame-by-frame playback.

### Concerns

1. **Curriculum transitions** — no hardcoding; retreat prioritised before advance; `min_steps_at_stage` prevents premature transitions.
2. **Recording runtime cost** — zero hot-loop overhead (async queue + daemon thread). Risk: if writer thread stalls, queue fills and training blocks on `queue.put()`. Mitigation: log queue depth.
3. **Video rendering substrate mode** — substrate auto-detected from environment. AspatialView.vue rendering strategy unclear from backend; document.
4. **Unified vs Live Inference boundary** — no duplication. Docstring for `UnifiedServer` could emphasise "orchestrator, not executor".
5. **Database concurrency** — SQLite WAL allows concurrent reads during write; single writer + multiple readers. Safe.

### Confidence

**High** — Curriculum logic clear and tested. Recording's async-queue pattern is standard and verifiable. Demo concerns are separated (runner / inference / orchestrator). Minor gap: AspatialView.vue rendering internals (frontend, outside this audit).

---

# Cross-Subsystem Summary

| # | Subsystem | Confidence | Major concerns |
|---|-----------|------------|----------------|
| 1 | Declarative Compilation Pipeline | High | VFS profile `Any` typing; cache fingerprint logic opacity |
| 2 | Configuration / DTO Layer | High | 4 no-defaults antipatterns in `effects_config.py` and `drive_as_code.py` |
| 3 | Environment Runtime & DAC | High | `vectorized_env.py` at 2,200 lines — next refactor target; DAC dual-schema hasattr/getattr |
| 4 | Physical Layer | High | AspatialSubstrate WAIT missing; POMDP practically limited to Grid2D; silent encoding-mode coercion |
| 5 | RL Core | High | PER beta annealing partial (TASK-005); RND active-mask may be unused |
| 6 | Orchestration & Periphery | High | Recording queue back-pressure risk; AspatialView.vue rendering undocumented |

**Headline structural observations:**

1. **The compiler reorganization is real and largely complete.** `universe/compiler.py` is 619 lines (down from 4,431); typed stage boundaries live in `pipeline.py`; domain compilers, validation phases, DTOs, loaders and adapters each have their own sub-package.
2. **`vectorized_env.py` is now the largest single file** at 2,200 lines and the next obvious decomposition target. Concrete split lines exist (action executor / observation encoder / env factory / reward calculator).
3. **DAC is the sole reward path** — `RewardStrategy` has been cleanly deleted. The dual-schema (`DriveConfig` vs `DriveAsCodeConfig`) hasattr/getattr branching in `DACEngine` is the main remaining seam.
4. **No-defaults discipline is enforced but not perfect.** The lint script catches function-level defaults; the Pydantic layer mostly uses `Field(...)`; but four specific `Field(default=...)` instances violate the discipline (`effects_config.py:245,248–251,267`; `drive_as_code.py:602–605,634`).
5. **Substrate × POMDP feasibility is documentation-vs-code drift.** Configuration accepts encoding modes the runtime silently ignores; aspatial's WAIT action is missing despite the docstring.
6. **The RL core is well-factored.** Factories drive networks/losses/optimizers from config; vectorisation is consistent; Double DQN plumbing is correct in both feedforward and recurrent paths.
7. **The demo / recording layer is non-intrusive.** Async queues keep recording out of the training hot loop; SQLite WAL keeps inference reads non-blocking; `UnifiedServer` is a thin orchestrator over the already-standalone `LiveInferenceServer`.
