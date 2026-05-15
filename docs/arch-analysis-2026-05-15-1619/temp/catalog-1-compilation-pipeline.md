## Declarative Compilation Pipeline (universe + vfs + effects)

**Location:** `src/townlet/universe/`, `src/townlet/vfs/`, `src/townlet/effects/`

**Responsibility:** Compile declarative v2.1 experiment configs (YAML + Pydantic DTOs) into typed, validated CompiledUniverse artifacts with integrated VFS profiles, effect catalogs, and runtime schemas for multi-level training curricula.

**Internal Structure:**

- **universe/** — Seven-stage compiler orchestration (config load → validation → symbol table → reference resolution → shared artifact enrichment → per-level compilation → artifact emission). Breaks into domain adapters (`compilers/`), typed DTOs (`dto/`), filesystem loaders (`loaders/`), and cross-cutting validation (`validation/`).
- **vfs/** — Variable & Feature System: declarative state-space layer with Pydantic schemas, profile compilation, observation building, and runtime evaluation. Decoupled from universe/ at the interface level; compiler pulls VFS profiles and builds schemas.
- **effects/** — Effect DSL: schema (CommandNode AST), parser (config → AST), compiler (expression validation), catalog (indexed effects), and runtime executor/scheduler. Split: compile-side (parser, compiler) validates against type schema; runtime-side (executor, manager, scheduler) executes pre-compiled commands.

**Key Components:**

- **universe/compiler.py** (619 lines) — UniverseCompiler entry point; orchestrates eight-stage pipeline with cache fast-path, config mtime fingerprinting, and per-level artifact emission via domain-specialized compilers.
- **universe/pipeline.py** — Typed stage boundaries: LoadedConfigBundle, ResolvedConfigBundle, SharedCompilerArtifacts, CompiledLevelBundle, CompiledArtifactBundle. Enforces handoff contracts between stages.
- **universe/compiled.py** — CompiledUniverse artifact: immutable multi-level container with msgpack serialization, cache validation via config_hash + provenance_id + mtime, and frozen dataclass structure. REQUIRED_COMPILED_UNIVERSE_FIELDS enforces deserialization integrity.
- **universe/compilers/effects.py** — EffectsCompiler: builds runtime effect expression schema from bars + environment variables + compiled VFS profiles; delegates catalog compilation to EffectCatalog.from_config().
- **universe/compilers/vfs.py** — VFSCompiler: orchestrates VFSProfileCompiler over v21 profiles (global, agent, item scopes); builds runtime variable defs, expression schemas, item spawn condition ASTs, observation marks (curriculum active flags).
- **universe/compilers/{actions,observation,optimization,metadata}.py** — Domain boundaries: ActionCompiler, ObservationCompiler, OptimizationCompiler, MetadataCompiler (handles versioning, git_sha, config fingerprint).
- **universe/dto/\*.py** — Typed metadata DTOs: UniverseMetadata, ObservationSpec, ObservationActivity, ActionSpaceMetadata, MeterMetadata, AffordanceMetadata, RuntimeAction, RuntimeActionSpace (observation traffic shaping; action space static contracts).
- **universe/loaders/{v21,preflight}.py** — v21.py: minimal wrapper around RawConfigsV21.from_experiment_dir(). preflight.py: config directory validation, YAML syntax checking, level-vs-experiment scoping enforcement (e.g., forbids vfs_profiles.yaml at level scope).
- **universe/validation/{semantics,references,limits,feasibility}.py** — Validation phases: semantics (cross-reference checks, cascade graph cycles, primary level selection), references (symbol table + resolution pass), limits (safety bounds on cache, VFS profiles, arrays), feasibility (grid capacity).
- **universe/adapters/vfs_adapter.py** — Bridges VFS ObservationField → compiler ObservationSpec; infers field types from shape, maps variable scopes (global/agent/agent_private), builds ObservationActivity activity mask and group slices.
- **vfs/schema.py** — VariableDef, VariableScope, NormalizationSpec, WriteSpec, ObservationField (scope: global/agent/agent_private/item; type: scalar/bool/tensor1d-Nd; observable flag; shape/dims).
- **vfs/registry.py** — VariableRegistry: runtime tensor storage with scope-aware access control (reader="agent"/"engine", writer="engine" only). ScopedVariableRegistry for agent/item subsets.
- **vfs/observation_builder.py** — VFSObservationSpec: definition of what VFS variables are observed; lazy observation extraction at runtime.
- **vfs/profiles.py** — CompiledGlobalProfile, CompiledItemProfile: compiled VFS variable declarations from YAML; bound to bar schemas at compile time. VFSProfileCompiler orchestrates compilation.
- **vfs/evaluator.py** — VFSEvaluator: interprets VFS expressions at runtime against VariableRegistry; bridges expression ASTs from compilation.
- **vfs/history.py** — VFS temporal history tracking (optional); collects retention requirements from profiles.
- **effects/schema.py** — CommandNode (pre-compiled AST representation): CommandType enum (MODIFY, SPAWN_EFFECT, SPAWN_ITEM, SAMPLE, IF, FOR_EACH, SWITCH, REDUCE, PARALLEL, DELAY, etc.). Each node carries `value_ast`, `condition_ast`, `target_ast` — expressions pre-parsed by compiler.
- **effects/parser.py** — CommandParser: config DTO → CommandNode, normalizing simple literals (target="self"/"target"/int) from expression strings.
- **effects/compiler.py** — CommandCompiler: type-checks expressions against schema (bar.*, target.bar.*, vfs.*, target.vfs.*, self.vfs.*, env.* paths); compiles expressions into pre-compiled ASTs and stores in CommandNode.value_ast / condition_ast / etc.
- **effects/catalog.py** — CompiledEffect: on_spawn, on_tick, on_despawn, on_interrupt command lists. EffectCatalog: deterministic effect_name_to_id mapping for observation encoding.
- **effects/manager.py** — EffectManager, ActiveEffect: runtime lifecycle tracking (intensity, duration_remaining, elapsed_ticks, observable flag, effect_index for tensor encoding).
- **effects/executor.py** — CommandExecutor: interprets pre-compiled CommandNodes at runtime via Evaluator. _TargetAwareExecutionContext: resolves target./self. paths from effect context (target_bars, self_bars, self_vfs, etc.). NO expression parsing at runtime (perf: ASTs pre-compiled by CommandCompiler).
- **effects/scheduler.py** — EffectScheduler: manages effect dispatch across ticks (on_spawn → on_tick loop → on_despawn or on_interrupt).
- **effects/context.py** — ExecutionContext: effect command execution environment (effect instance, elapsed_ticks, duration_remaining, intensity, target).
- **effects/collections.py** — Runtime collections (for_each targets): nearby_agents, all_agents, etc.

**Pipeline Flow:**

1. **Stage 0 (Preflight):** Config directory existence, YAML syntax, level-vs-experiment scoping rules.
2. **Stage 1 (Load v2.1):** RawConfigsV21.from_experiment_dir() parses experiment/, brain/, stratum/, environment/, actions/, items/, vfs_profiles.yaml, effects.yaml, and levels/*/curriculum.yaml.
3. **Stage 2 (Limits):** Enforce MAX_CACHE_FILE_SIZE, MAX_VFS_PROFILES, array bounds, EFFECT_OBSERVATION_SLOTS.
4. **Stage 3 (Semantics):** Cross-validate cascade graph cycles, affordance references, selected primary level, action IDs.
5. **Stage 4 (Symbol Table):** Register all named entities (meters, cascades, affordances, variables, custom actions, VFS profile variables) into UniverseSymbolTable.
6. **Stage 5 (References):** Resolve drive-as-code references, effect references, VFS variable bindings against symbol table.
7. **Stage 6 (Shared Artifacts):** Compile VFS profiles → CompiledVFSProfiles; build effects schema from bars + env vars + VFS; compile EffectCatalog; collect VFS history requirements.
8. **Stage 7 (Per-Level):** For each curriculum level, compile observations, actions, meters, affordances, optimization data; emit CompiledUniverse.LevelMetadata.
9. **Stage 8 (Emit + Cache):** Serialize CompiledUniverse to msgpack at cache_path; store config_hash, provenance_id, mtime for fast-path validation on reload.

**Dependencies:**

**Inbound (who consumes compiled artifacts):**
- `townlet/environment/vectorized_env.py` — imports CompiledUniverse; bootstraps agents/environment from compiled metadata.
- `townlet/environment/affordance_engine.py` — imports EffectCatalog, CommandExecutor, ExecutionContext; manages affordance effect pipelines.
- `townlet/items/action_handlers.py`, `townlet/items/manager.py` — effects execution for item lifecycle.
- `townlet/training/checkpoint_utils.py` — unpickles CompiledUniverse from cache for training resumption.
- `townlet/demo/{runner,live_inference}.py` — entry points for experiment validation and inference.

**Outbound (what universe depends on):**
- `townlet/config/{actions,affordances_v2,bars_v2,brain,curriculum,drive_as_code,environment,experiment,items,stratum,training_v2,vfs_profiles}*.py` — Pydantic config DTOs (ground-truth schema contracts).
- `townlet/world/expression/{expression,type_checker,evaluator,context}.py` — expression parsing, type checking, runtime evaluation (used by VFS evaluator and effects compiler for expression validation).
- `townlet/environment/substrate_action_validator.py` — action feasibility checking (called from semantics validation).
- `townlet/world/{bars,agents,affordances}.py` — world model DTOs referenced in config validation.

**Patterns Observed:**

1. **Seven-stage pipeline with explicit stage boundaries (pipeline.py):** Dataclasses enforce handoff contracts; stages not reordered or parallelized.
2. **Typed DTO emission:** Pydantic at config layer; frozen dataclasses at universe layer (immutability enforced for cached artifacts).
3. **Pre-compiled ASTs for expressions:** CommandCompiler emits CommandNode with .value_ast, .condition_ast, .target_ast pre-parsed; CommandExecutor never calls parser at runtime (perf win: no string→AST overhead per tick).
4. **Dual-scope VFS:** Compile-side builds schemas and profile hierarchies; runtime VFSEvaluator + VariableRegistry manage tensor storage and scope-aware access.
5. **Domain adapters (universe/compilers/):** Each domain (effects, vfs, actions, observation, metadata, optimization) encapsulates its compiler boundary; loose coupling via schema exchanges.
6. **Cache fast-path:** CompiledUniverse.load_from_cache() with config_hash + provenance_id + mtime validates without recompile; eliminates parsing overhead on resume.
7. **Observation activity marking:** curriculum_active flags on VFSObservationField propagate through VFSAdapter → ObservationActivity.active_mask for runtime padding/truncation.

**Concerns:**

1. **VFS Profile Type Annotations (compiled.py:68–69):** `agent_profile`, `item_profiles` marked `Any` with TODO comments. Should bind to CompiledAgentProfile, dict[str, CompiledItemProfile] after refactoring vfs/profiles.py type exports. **Status:** Documented intent; not blocking (runtime works), but invites accidental type misuse.
2. **Primary level selection fallback (semantics.py:15–21):** When primary_level is None, defaults to sorted(levels.keys())[0]. Per "no backwards compatibility" rule, this should be an error (caller must pass explicit primary_level). Confirm with compiler.py:85 — it explicitly raises if None. **Status:** Safe; universe/compiler.py enforces explicit selection.
3. **Optional effects/vfs_profiles:** Both can be None throughout pipeline (shared_artifacts carries CompiledVFSProfiles | None, EffectCatalog | None). Callers must check before dereferencing. No Try-Catch fallbacks observed, but runtime guards are critical. **Status:** Safe; guards are present; schema-building is defensive.
4. **Cache fingerprinting via external functions:** compiler.py delegates _build_cache_fingerprint, _compute_config_mtime, _compute_pydantic_hash to methods; if Git or mtime logic changes, cache invalidation depends on re-implementation. **Status:** Code review required to ensure provenance_id includes experiment dir name and git SHA; currently works but fragile to refactor.

**Confidence:** **High** — The pipeline is explicitly modeled in pipeline.py dataclasses, stages are logged and numbered, and the codebase is post-refactor (prior 4,431-line monolith is now modular). All three subsystems (universe, vfs, effects) have clear ownership and validated integration points. Pre-compiled ASTs are visible in effects/schema.py and effects/compiler.py. However, VFS type annotations remain loose (Any) and cache fingerprinting logic is somewhat opaque.

