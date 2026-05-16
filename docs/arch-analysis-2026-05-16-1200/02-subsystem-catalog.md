# 02 — Subsystem Catalog

Eight subsystem groups derived **from source code only** (per user directive). Detailed per-subsystem
catalogs live in `temp/sg{1..8}-*.md`. This document is the **navigation surface** and the **cross-cutting
synthesis**; it deliberately does not duplicate the evidence.

## How to read this catalog

- **Per-subsystem summary** below: one-page synopsis distilled from each `codebase-explorer` run.
- **Full evidence:** every claim has a citation (`file.py:LINE`) in the corresponding `temp/sgN-*.md`.
- **Cross-cutting sections** (§9-§12) are coordinator-level synthesis across all eight reports.

## Confidence summary

| ID | Subsystem | LOC | Files | Confidence | Detail |
|----|-----------|-----:|------:|------------|--------|
| SG1 | Universe Compiler (UAC) | 5,750 | 34 | High | `temp/sg1-universe.md` |
| SG2 | Variable & Feature System (VFS) | 7,080 | 15 | High | `temp/sg2-vfs.md` |
| SG3 | Configuration DTOs | 4,728 | 22 | High | `temp/sg3-config.md` |
| SG4 | Environment & DAC | 5,041 | 15 | High | `temp/sg4-environment.md` |
| SG5 | Substrate & World DSL | 6,831 | 20 | High (substrate), High (DSL) | `temp/sg5-substrate-world.md` |
| SG6 | RL Training Stack | 6,427 | 27 | High | `temp/sg6-training.md` |
| SG7 | Effects & Items | 4,480 | 15 | High | `temp/sg7-effects-items.md` |
| SG8 | Demo / Recording / Frontend | ~14,800 | 16 py + 27 vue | High | `temp/sg8-demo-recording-frontend.md` |

---

## 1. SG1 — Universe Compiler (UAC)

**Location:** `src/townlet/universe/`

**Responsibility.** Compiles a v2.1 experiment pack (`configs/<pack>/`) into a frozen
`CompiledUniverse` consumed by every other subsystem. The compiler is the seam between the
declarative DTO layer (SG3) and all runtime systems (SG4 environment, SG2 VFS, SG7 effects/items).

**Pipeline.** Empirically **9 stages**, not 7 as CLAUDE.md claims:
preflight → cache-check → yaml-syntax → parse → limits → semantics → symbols → resolve →
shared-artifacts → per-level compile → emit/cache. Three different internal numbering schemes are
in use (`_log_stage` 1-8, inline comments 0-7, exception `stage=` labels) — this is a maintenance
hazard.

**DTOs.** Input: `RawConfigsV21` (`raw_configs_v21.py:48`, `from_experiment_dir`). Output:
`CompiledUniverse` (`compiled.py:108`, schema version `1.12`), carrying primary-level mirror
fields, raw configs, compiled VFS and effect catalog, **12 provenance hashes** (`compiled.py:55-87`:
observation_schema, variable_schema, action_schema, transition_graph, vfs, drive, brain,
experiment, stratum, environment, actions, items — the SG1 explorer's "seven" was an undercount),
and a `LevelMetadata` inner class.

**Validation.** Cleanly partitioned across `feasibility/` (geometry), `limits/` (resource caps),
`semantics/` (cross-DTO consistency), and `references/` (symbol-table name resolution). Three
duplicate referential checks were flagged.

**Notable concerns.** `CuesCompiler` is instantiated but never called from `compiler.py` (orphan
dead code); compile-time invocation of the runtime `SubstrateFactory.build()` from two
sub-compilers (compile-time/runtime mixing); in-place mutation of `rule.when_ast` in
`VFSCompiler.compile_item_spawn_conditions` violates the otherwise-frozen DTO discipline; the
universe `__init__.py` exports only `dto`, forcing external callers to depend on deep submodule
paths; `adapters/vfs_adapter.py` has no in-package callers.

**Inbound callers verified:** `training/`, `demo/`, `environment/`, `agent/`, `items/` (8 sites).
**Outbound:** `config/`, `environment/`, `substrate.factory`, `effects/`, `vfs/`, `world.expression`.

---

## 2. SG2 — Variable & Feature System (VFS)

**Location:** `src/townlet/vfs/`

**Responsibility.** Three concerns, in one package:
1. **State storage & access control** — `VariableRegistry` (`registry.py`) allocates torch tensors per
   declared variable, indexed by one of nine scopes (`global, agent, agent_private, item, pair,
   group, affordance, zone, message`), and enforces reader/writer ACLs at every `get`/`set`.
2. **Compiled transition execution** — "VTC" = "**VFS Transition Compiler**" (confirmed `vtc.py:1`).
   Nine frozen-dataclass `VTC…Program` classes with TorchScript inner kernels (`vtc_kernels.py`)
   run once per env tick.
3. **Observation construction & profile evaluation** — `observation_builder.py` flattens
   registry tensors into `[global | agent | item]` observation rows; `evaluator.py` runs
   profile-compiled ASTs over per-step `ExecutionContext`.

**VTC program catalog (9 programs).** `VTCActionWriteProgram`, `VTCThresholdCascadeProgram`,
`VTCPassiveDepletionProgram`, `VTCModulationProgram`, `VTCAffordanceGateProgram`,
`VTCInteractionProgressProgram`, `VTCTerminalConditionProgram`, `VTCSocialResidueProgram`,
`VTCRewardProgram`. The reward program runs through a `DACEngine` backend (SG4) at runtime.

**Transition-schedule abstraction.** `VTCTransitionSchedule` and `VTCTransitionRunner`
(`src/townlet/vfs/transition_schedule.py`) are now the runtime execution seam for compiled
transition phases. The compiler emits a schedule into `CompiledUniverse.transition_schedule` and
each `LevelMetadata.transition_schedule`; the environment executes phase names generically and
does not branch on experiment semantics. `VTCSocialResidueProgram` became live through this path,
and `tests/test_townlet/integration/test_vtc_transition_schedule_runtime.py` asserts that changing
`transition_rules.yaml` changes hashes and runtime VFS state without changing environment code.

**Provenance.** `schema_hashes.py` produces canonical-JSON SHA-256 fingerprints for variable,
observation, action, and transition-graph schemas; `compute_vfs_hash` combines all four —
load-bearing for checkpoint compatibility.

**Notable concerns.** `ScopedVariableRegistry` (`registry.py:877-1049`) looks like a parallel
unused scaffold; `VTCInteractionProgressProgram` IS called at `environment/action_executor.py:239`
(the SG2 explorer's hedged claim was refuted on validator re-grep); `_max_tensor_elements`
assigned twice; `VTCInteractionProgressProgram.apply` uses a Python per-agent loop in an otherwise
GPU-native pipeline; `VFSEvaluator` and `EvaluationMode` are not re-exported from `__init__.py`.

**Key consumer:** `environment/vectorized_env.py` (SG4) instantiates the registry, receives the
compiled transition schedule from the selected level, and invokes phase-graph-driven transition
wrappers from `step()` (`vectorized_env.py:1100-1257`).

---

## 3. SG3 — Configuration DTO Layer

**Location:** `src/townlet/config/`

**Responsibility.** Pydantic v2 DTOs for every YAML in a config pack, one file per logical schema.
142 BaseModels with `extra="forbid"`; two with `extra="allow"` (`RecordingConfig`,
`PerceptionConfig`/`ShapingConfig`).

**Layout.** Pack-shape DTOs (`stratum`, `environment`, `actions`, `brain`, `items`, `effects`,
`vfs_profiles`) sit at the experiment root; per-level DTOs (`curriculum`, `bars`, `affordances`,
`drive`, `training`) live under `levels/<L>/`. **The "flat" `configs/<level>/` layout claimed in
CLAUDE.md no longer exists.**

**Entry points.** Deep: `townlet.universe.raw_configs_v21.RawConfigsV21.from_experiment_dir`
(canonical load path). Shallow: `townlet.config.load_training_v2_config` (used by
`scripts/run_demo.py:23`).

**No-defaults rule.** Partial enforcement only. `base.py` is just two helpers
(`load_yaml_section`, `format_validation_error`); there is no shared `StrictBaseModel`. The
structural side of the rule lives in `scripts/no_defaults_lint.py` (whitelist-driven AST walker).
`drive_as_code.CompositionConfig` and `DriveAsCodeConfig` still carry hardcoded defaults on
reward fields.

**Anti-pattern hits (zero-backwards-compat rule).**
- `agent_config.py` (362 LOC) appears to be a legacy parallel of `brain_config.py` and
  `drive_as_code.py`. Only `DriveConfig` is imported (by `dac_engine.py`); no `agent.yaml`
  exists in any pack. **Deletion candidate.**
- `capability_config.py` and `affordance_masking.py` are unreferenced outside the config package.
  **Orphan candidates.**
- `ExtrinsicStrategyConfig` is a nine-way `type` literal with no per-variant required-field enforcement.

**Documentation drift discovered (three load-path claims):**
1. `variables_reference.yaml` is **optional**, not required (`raw_configs_v21.py:202-211`); the
   live `configs/default_curriculum/` doesn't ship one.
2. The DAC file is `drive.yaml` (key `drive:`), not `drive_as_code.yaml`.
3. Flat `configs/<level>/` layout doesn't exist — packs are `<pack>/levels/<level>/`.

---

## 4. SG4 — Environment & DAC

**Location:** `src/townlet/environment/`

**Responsibility.** The runtime: `VectorizedHamletEnv` is a GPU-tensor PettingZoo-ish env;
`DACEngine` is the reward computation engine.

**Tick loop (`vectorized_env.step()` lines 1084-1218).** **16 stages**: action exec → VTC action
writes → passive depletion → threshold cascades → effects tick → VFS evaluator → terminal
conditions → counter increments → item lifecycle → retirement check → reward computation →
temporal increment → observation assembly → info dict (+ minor steps).

**Reward routing.** `reward_calculator.py:41-48` calls `env.vtc_reward_program.apply(reward_backend=env.dac_engine, ...)`.
The DAC engine is now a backend parameter on `VTCRewardProgram`, not a direct call — an
indirection that is undocumented inside `dac_engine.py`. The `drive_hash` is computed by the
**universe compiler** (`universe/compiler.py:416`), not by `DACEngine` itself; checkpoint
validation is in `training/checkpoint_utils.py:98-107`.

**DAC engine.** Compiles modifiers, 9 extrinsic strategies, and 11 shaping bonuses into Python
closures over torch tensors at construction (`dac_engine.py:73-83, 154-501, 503-886`). Two
coexisting config schemas (DAC v2 vs `agent.yaml`) lead to **two compilation paths** in
`_compile_extrinsic` (lines 196 vs 230 for `constant_base_with_shaped_bonus`) — one should die per
the zero-backwards-compat rule.

**Verified CLAUDE.md claims.**
- `reward_strategy.py` is fully deleted (commit `4d694d73`).
- No `RewardStrategy` references remain (grep zero hits).
- `tests/test_townlet/unit/environment/test_reward_strategies.py` deletion confirmed at
  349 lines (commit `bfde7c8a`).

**Refuted CLAUDE.md claim.** CLAUDE.md states "583 lines removed" for `reward_strategy.py`; actual
diff is **234 deletions**. Documentation drift.

**Notable concerns.**
- **Per-agent Python loops in nominally GPU-native paths:** `affordance_engine.py:538-555`,
  `action_executor.py:73-134`, `vectorized_env.py:954-969, 1346-1371`, `dac_engine.py:572-577,
  747-751`. Performance leakage.
- `NullEffectManager` is incomplete (`affordance_engine.py:568-572`); only stubs `spawn_effect`.
- `VectorizedHamletEnv.__init__` is **460 lines** (73-529); `get_action_masks` is **165 lines**
  (917-1082) — God-method risk.
- `aggregation` extrinsic strategy is hardcoded to `min` (`dac_engine.py:411`) despite docstring
  promising `min/max/mean/product` — feature gap or doc lie.
- `__init__.py` is one line; no curated public surface.

---

## 5. SG5 — Substrate & World Expression DSL

**Location:** `src/townlet/substrate/` and `src/townlet/world/` (co-located, decoupled — no
cross-imports).

### 5A. Substrate

Classic ABC + factory. `SpatialSubstrate` (`base.py:12`) declares 11 abstract methods; nine
concrete substrates: Aspatial, Grid{2D,3D,ND}, Continuous{1,2,3D,ND}. `SubstrateFactory.build()`
(`factory.py:15`) is the sole construction seam. Boundary modes (clamp/wrap/bounce/sticky) and
distance metrics (manhattan/euclidean/chebyshev) implemented uniformly across families. Three
observation encodings (relative/scaled/absolute) are **duplicated per substrate** rather than
centralised.

**Concerns.** Stale `[…, INTERACT, WAIT]` ordering in base-class contract — no substrate emits
WAIT; dead magnitude-scaled cost code in `Continuous2DSubstrate._generate_discretized_actions`
(`continuous.py:583-585`); non-vectorised Python loop in `Grid2DSubstrate.encode_partial_observation`
(`grid2d.py:581-598`); semantic asymmetry between `Grid2D.encode_observation` (flat occupancy
grid) and `Continuous.encode_observation` (position only).

### 5B. World Expression DSL

Self-contained expression language. Grammar: pyparsing with packrat caching, 7-level operator
precedence, `**` right-associative (`parser.py:55-236`). AST: visitor-pattern frozen dataclasses
(`ast_nodes.py`, 10 visitor methods). Two-phase pipeline: parser → type-checker (schema-driven
bottom-up, `type_checker.py`) → evaluator (GPU-tensor-native, eager `torch.where`,
`evaluator.py`). **48 built-in functions** registered in `FUNCTION_SPECS` (`functions.py`) —
single source of truth shared by both type-checker and evaluator. Temporal operators (lag, ema,
moving_average, edges) backed by `TemporalHistory` ring buffers up to 256 ticks (`history.py`).

**Concerns.**
- `Switch` and `Reduce` AST nodes exist but are **unparseable and unimplemented** in
  `Evaluator`/`TypeChecker` — dead code in the public AST surface.
- `world/types/primitive.py` defines a `Type` protocol with **zero confirmed consumers**;
  disjoint from the string-based type system the type-checker actually uses.
- Reference-traversal logic duplicated between compile time (`type_checker.py:151-212`) and
  runtime (`context.py:75-201`).
- `ASTNode.line`/`column` fields exist but are **never populated** by the parser — fake error
  position info.

**Consumers of the DSL:** `effects/`, `items/`, `universe/`, `vfs/`. The DSL is the lingua franca
for declarative state transitions across the whole system.

---

## 6. SG6 — RL Training Stack

**Locations:** `agent/`, `population/`, `training/`, `exploration/`, `curriculum/` (5 sub-packages
sharing the same training-loop concern).

**Networks (`agent/networks.py`, 654 LOC).** 4 classes; `NetworkFactory` covers only 4 of 5.
`StructuredQNetwork` is **dead from the training loop** — implemented and unit-tested but
unreachable through the factory.

**Orchestrator.** `VectorizedPopulation.step_population` (`population/vectorized.py`, 1201 LOC) is
the sole training-step orchestrator. The `use_double_dqn` flag is honoured at line 919
(feed-forward) and 791 (recurrent).

**Training state.** `training/state.py` defines `RewardTensor`, `BatchedAgentState`,
`CurriculumDecision`, `PopulationCheckpoint`. **Three replay buffers:** `replay_buffer.py`
(uniform), `prioritized_replay_buffer.py` (Schaul), `sequential_replay_buffer.py` (LSTM
episodes). **Checkpoint provenance** uses the four-hash compatibility pipeline (`config_hash`,
`drive_hash`, `brain_hash`, `vfs_hash`) in `training/checkpoint_utils.py`.

**Exploration strategies (5 files).** `base.py`, `action_selection.py`, `epsilon_greedy.py`,
`rnd.py`, `adaptive_intrinsic.py`. **Discrepancy with CLAUDE.md:** *no `icm.py`, `count_based.py`,
or `adaptive_rnd.py` files exist*. The intrinsic strategies CLAUDE.md advertises are either
absent or have been renamed.

**Curriculum (4 files).** `base.py`, `factory.py`, `static.py`, `adversarial.py`. 5 hardcoded
adversarial stages with advance/retreat thresholds; entropy derived from Q-values.

**Notable concerns (silent bugs).**
- `decay_epsilon()` is defined on the exploration strategies and IS called once per episode from
  `demo/runner.py:933`, but is **not called from `VectorizedPopulation`** where the rest of the
  per-step exploration coordination lives — a layering concern (the schedule is driven by the
  demo runner, not the population trainer), not dead code. (Validator re-grep, was previously
  reported as dead by SG6.)
- `VectorizedPopulation.get_checkpoint_state()` **does not include adversarial curriculum tracker
  tensors**; resume-from-checkpoint with adversarial curriculum will silently lose `agent_stages`,
  `steps_at_stage`, `episodes_at_stage`.
- Only `decisions[0].depletion_multiplier` is passed to the env step — single global difficulty
  knob, never per-agent (the design seemingly intends per-agent).
- `PerformanceTracker.update_step(rewards, dones)` parameter is **misnamed** — it expects step
  counts, not rewards. Callsite `vectorized.py:1049`.
- CLAUDE.md claims `RecurrentSpatialQNetwork` LSTM input dim is 192/224; the actual value is
  **240** (with temporal features added since the doc was written).

---

## 7. SG7 — Effects & Items

**Locations:** `src/townlet/effects/`, `src/townlet/items/`

### 7A. Effects

A declarative state-mutation DSL with **10 command kinds**: `MODIFY`, `SPAWN_EFFECT`,
`SPAWN_ITEM`, `SAMPLE`, `IF`, `FOR_EACH`, `SWITCH`, `REDUCE`, `PARALLEL`, `DELAY`. Compilation
pre-parses expression ASTs onto `CommandNode`s (`effects/compiler.py:14`); the executor never
reparses at runtime (`effects/executor.py:104`). `EffectManager` (`effects/manager.py:59`) owns
lifecycle in four scope buckets (global/agent/item/affordance), with renew/merge/replace/stack
reapply policies. Tick-keyed `Scheduler` (`effects/scheduler.py:21`) handles `DELAY`
with caps (`MAX_DELAY_TICKS=1000`, `MAX_SCHEDULED_ITEMS=10000`). Cascade depth capped at
`MAX_CASCADE_DEPTH=10`.

**Concerns.**
- `EffectScope.ITEM` and `EffectScope.AFFORDANCE` buckets are populated but **never iterated** in
  `EffectManager.tick` — likely latent feature.
- `PARALLEL` is sequential at runtime; only the disjoint-writes check is "parallel".
- `_iter_positions` vs `_resolve_respawn_positions` are 95% duplicated.

### 7B. Items

Thin lifecycle owner. Per-item `on_pickup` / `on_use` / `on_drop` + custom verb pipelines compile
through the effects compiler. Inventory is **tensor-backed** (`[batch, max_items_per_agent]`
int64, `-1` = empty) with dict-sidecar metadata. The `self_is_item` flag on `ExecutionContext`
routes `self.vfs.*` resolution into the per-profile item-VFS table.

**Migration script.** `scripts/migrate_affordances_to_effects.py` is a **one-shot** with no
runtime backing for the old schema. Per the zero-backwards-compat rule, this script is a
deletion candidate.

---

## 8. SG8 — Demo, Recording, Frontend

**Locations:** `src/townlet/demo/`, `src/townlet/recording/`, `frontend/`

### 8A. Demo (3,172 LOC, 4 .py files)

`UnifiedServer` runs **two threads** (training thread + inference uvicorn) in one process;
**bridges them via the filesystem** — `checkpoint_ep*.pt` polled by
`LiveInferenceServer._check_and_load_checkpoint` (`live_inference.py:419`).
`LiveInferenceServer` is a FastAPI app with one WebSocket route (`/ws`, aliased `/ws/training`);
pushes `state_update` / `episode_start` / `episode_end` / `model_loaded` frames at **5 Hz** to all
clients. `DemoDatabase` is SQLite with WAL.

### 8B. Recording (1,603 LOC, 7 .py files)

Non-blocking producer/consumer: `EpisodeRecorder.record_step` pushes frozen `RecordedStep`
dataclasses onto a bounded `queue.Queue`; daemon `RecordingWriter` drains, buffers per episode,
then writes `episode_{id:06d}.msgpack.lz4` on `EpisodeEndMarker` (msgpack → `lz4.frame.compress`
level 0). DB-indexed via `episode_recordings` table. Separate matplotlib + ffmpeg pipeline
(`video_renderer.py`, `video_export.py`) renders MP4s via `python -m townlet.recording`.

### 8C. Frontend (10,432 LOC, 27 Vue components)

Vue 3 + Pinia + Vite. Single store `simulation.js` (668 LOC) connects to `ws://<host>:8766/ws`
with auto-reconnect (10 × 3 s) and auto-play on connect. Full server→client and client→server
frame catalogue is in `temp/sg8`. Dark-theme palette and dimensions in `frontend/src/styles/tokens.js`.

**Critical concerns.**
- **`frontend/package.json` is missing.** `npm run dev` cannot work from a fresh checkout.
- `pyproject.toml` declares `flask` + `flask-cors`, but **nothing in `src/` imports them.**
  FastAPI is the sole web stack. `msgpack` and `lz4` are also declared twice.
- CORS `allow_origins=["*"]` + uvicorn `0.0.0.0` is a localhost-only-safe combination —
  worth a callout for SG security.
- `UnifiedServer._start_frontend()` is defined but **never called** from `start()` — drifted code.
- `ACTION_ICONS` has only 5 entries while the global vocabulary is 8-16 actions.
- Replay handlers exist server-side but no Vue surface consumes them.
- `RecordingCriteria` is unreferenced by the writer thread — only the `periodic` criterion is
  honoured; `reason="periodic"` is hardcoded in the DB row.
- Affordance/meter colour palettes duplicated between `tokens.js` and `video_renderer.py`.
- Inference Q-value log path is process-CWD-relative.

---

## 9. Cross-subsystem dependency matrix

`→` reads "depends on". Arrows derived from imports observed in each subagent's report.

| Caller \ Callee | SG1 univ | SG2 vfs | SG3 cfg | SG4 env | SG5 sub | SG5 dsl | SG6 train | SG7 eff | SG7 itm | SG8 demo | SG8 rec |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SG1 universe | — | imports compiled VFS profiles + observation builder | aggregates DTOs via `RawConfigsV21` | invokes `SubstrateFactory.build` (compile-time / runtime mix) | (substrate compile path) | imports `world.expression` for parsing | — | imports `EffectCatalog` | — | — | — |
| SG2 VFS | imports `world.expression` for AST | — | imports `vfs_config`, `vfs_profiles_config` | — | — | imports parser, type-checker, history | — | — | — | — | — |
| SG3 config | (DTOs consumed by univ) | — | self-contained | — | — | — | — | — | — | — | — |
| SG4 environment | imports `universe.dto`, `RuntimeActionSpace` | uses registry, evaluator, all 8 VTC programs | imports many `*_config` | — | imports `substrate.continuous` etc. | (DSL via evaluator) | called by population | imports `EffectManager` | imports inventory state | — | — |
| SG5 substrate | — | — | imports stratum_config, action_config | — | — | — | — | — | — | — | — |
| SG5 world DSL | — | — | — | — | — | — | — | — | — | — | — |
| SG6 training | reads compiled hashes via checkpoint validator | — | imports brain_config, training_v2_config | constructs and steps `VectorizedHamletEnv` | — | — | — | — | — | — | — |
| SG7 effects | — | — | imports effects_config | — | — | imports parser+evaluator | — | — | (item respawn paths) | — | — |
| SG7 items | imports universe DTOs | imports VFS registry, observation builder | imports items_config | — | — | (effect compiler) | — | imports effects compiler | — | — | — |
| SG8 demo | imports universe | — | imports config loaders | imports `VectorizedHamletEnv` | — | — | imports population, training | — | — | — | imports recording |
| SG8 recording | — | — | imports recording_config | (recorded from env step info) | — | — | — | — | — | — | — |

**Observations.**
- SG2 (VFS) and SG7 (effects/items) are the most pervasive runtime dependencies — they sit
  *inside* the environment tick, not beside it.
- **SG5 world DSL is a leaf dependency** in the import graph but a load-bearing concept: it is the
  *only* parser used by SG1 (universe compilers), SG2 (VFS profiles), SG7 (effects, items). If
  the DSL changes, every higher subsystem must recompile.
- **SG3 config is leaf-side too** (DTOs only depend on Pydantic + helpers) but every other
  subsystem reads from it.
- The only **bidirectional concern** is SG1↔SG4: universe compiles DTOs that the environment then
  drives, but universe also calls `SubstrateFactory.build()` from compile time, which is a
  compile-time/runtime layering violation flagged by both SG1 and SG5.

---

## 10. Documentation drift catalog

A unified record of every CLAUDE.md / docs/ claim that subagents refuted or qualified.
Each row will require a document update during recreation.

| # | Stale claim | Reality | Source |
|--:|-------------|---------|--------|
| 1 | "Universe compiler has seven stages" | Empirically 9 stages with 3 inconsistent numbering schemes | SG1 |
| 2 | "Active configs: `L0_0_minimal`, `L0_5_dual_resource`, `L1`, `L2`, `L3` directly under `configs/`" | Actual: `configs/<pack>/levels/<level>/` hierarchical layout (e.g. `configs/default_curriculum/L1_full_observability/`) | Discovery + SG3 |
| 3 | "`variables_reference.yaml` is REQUIRED for all packs" | Optional (`raw_configs_v21.py:202-211`); live pack `configs/default_curriculum/` doesn't ship one | SG3 |
| 4 | "DAC config file is `drive_as_code.yaml`" | Actual file is `drive.yaml` (top-level key `drive:`) | SG3 |
| 5 | "Each config pack requires `drive_as_code.yaml`" + "All reward logic in `drive_as_code.yaml`" | The per-level file is `drive.yaml`; pack-shape uses `agent.yaml` legacy path that still exists | SG3, SG4 |
| 6 | "`reward_strategy.py` deletion removed 583 lines" | Actual diff: 234 deletions (commit `4d694d73`) | SG4 |
| 7 | "Exploration strategies: RND, ICM, count_based, adaptive_rnd, epsilon_greedy" | Only `epsilon_greedy`, `rnd`, `adaptive_intrinsic` files exist; `icm.py`, `count_based.py`, `adaptive_rnd.py` are absent | SG6 |
| 8 | "RecurrentSpatialQNetwork LSTM input dim 192" | Actual 240 (temporal features added) | SG6 |
| 9 | "Aggregation extrinsic strategy supports min/max/mean/product" | Hardcoded to `min` (`dac_engine.py:411`) | SG4 |
| 10 | "Agents pre-release with zero users; src/hamlet/ is obsolete" | `src/hamlet/` is fully deleted (zero residue) | Discovery |
| 11 | "Frontend build via `cd frontend && npm run dev`" | `frontend/package.json` is **missing**; npm cannot resolve | SG8 |
| 12 | "pyproject deps imply Flask is used" (CLAUDE.md doesn't claim this, but pyproject does) | Flask is **unused** anywhere under `src/`; FastAPI is the only web stack | SG8 |

---

## 11. Aggregated concerns by category

### 11.1 Dead / orphan / unused code (zero-backwards-compat violations)

| Item | Location | Source |
|------|----------|--------|
| `CuesCompiler` instantiated but never called | `universe/compiler.py` | SG1 |
| `ScopedVariableRegistry` parallel scaffold, unused by env | `vfs/registry.py:877-1049` | SG2 |
| `agent_config.py` (362 LOC) legacy parallel of `brain_config.py` + `drive_as_code.py`; no `agent.yaml` exists | `config/agent_config.py` | SG3 |
| `capability_config.py`, `affordance_masking.py` unreferenced outside config/ | `config/` | SG3 |
| `StructuredQNetwork` implemented + unit-tested but unreachable via `NetworkFactory` | `agent/networks.py` | SG6 |
| `decay_epsilon()` not called from `VectorizedPopulation` (it IS called once-per-episode from `demo/runner.py:933` — layering observation, not dead code) | `exploration/*.py` + `demo/runner.py:933` | SG6 (validator-corrected) |
| `Switch` and `Reduce` AST nodes unparseable and unimplemented | `world/expression/ast_nodes.py` | SG5 |
| `world/types/primitive.py` `Type` protocol — zero consumers | `world/types/primitive.py` | SG5 |
| `EffectScope.ITEM` and `EffectScope.AFFORDANCE` populated but never iterated | `effects/manager.py` | SG7 |
| `scripts/migrate_affordances_to_effects.py` — one-shot migration, no current consumer | `scripts/` | SG7 |
| `UnifiedServer._start_frontend()` defined but never called from `start()` | `demo/unified_server.py` | SG8 |
| `RecordingCriteria` unreferenced by writer thread | `recording/criteria.py` | SG8 |
| Server-side replay handlers — no Vue consumer | `demo/live_inference.py` | SG8 |
| `flask`, `flask-cors` pyproject deps — no `src/` imports | `pyproject.toml` | SG8 |
| `msgpack`, `lz4` declared twice in `pyproject.toml` | `pyproject.toml` | SG8 |

### 11.2 Latent / silent bugs

| Item | Symptom | Source |
|------|---------|--------|
| Adversarial curriculum tensors not in `get_checkpoint_state()` | Resume silently loses `agent_stages` etc. | SG6 |
| `PerformanceTracker.update_step` mis-named (`rewards` param holds step counts) | Confusing call site `vectorized.py:1049` | SG6 |
| Only `decisions[0].depletion_multiplier` passed to env step | Per-agent difficulty likely intended; only global is used | SG6 |
| In-place mutation of `rule.when_ast` in VFS compiler | Violates frozen DTO discipline | SG1 |
| Two coexisting DAC compilation paths (DAC v2 vs agent.yaml) | Maintenance burden, potential silent divergence | SG4 |
| `_max_tensor_elements` assigned twice in registry | Hidden override risk | SG2 |
| `ASTNode.line`/`column` never populated by parser | Misleading error positions | SG5 |
| `Continuous2DSubstrate._generate_discretized_actions` dead magnitude-scaled cost | Surprising no-op | SG5 |
| `RecordingCriteria` ignored; `reason="periodic"` hardcoded | Recording filters do not work | SG8 |
| `ACTION_ICONS` has 5 entries for 8-16-action vocabulary | UI gaps for unknown actions | SG8 |

### 11.3 Performance / GPU-discipline leakage

The project markets itself as "GPU-native". These per-agent Python loops in hot paths refute that
claim in spots:

| Location | Loop nature | Source |
|----------|-------------|--------|
| `affordance_engine.py:538-555` | Per-agent affordance resolution | SG4 |
| `action_executor.py:73-134` | Per-agent action dispatch | SG4 |
| `vectorized_env.py:954-969`, `1346-1371` | Per-agent state updates | SG4 |
| `dac_engine.py:572-577`, `747-751` | Per-agent reward computation paths | SG4 |
| `grid2d.py:581-598` | `encode_partial_observation` non-vectorised | SG5 |
| `vfs/vtc.py` `VTCInteractionProgressProgram.apply` | Per-agent loop | SG2 |

### 11.4 Documentation maintenance

499 markdown files in `docs/` and CLAUDE.md is empirically stale on at least 12 specific claims
(see §10). Doc maintenance is itself a finding. SG3 specifically called out
`docs/config-schemas/*.md` as needing rewrite for the hierarchical v2.1 layout.

### 11.5 Structural / coupling

| Item | Detail | Source |
|------|--------|--------|
| Compile-time/runtime mix in universe | `SubstrateFactory.build()` called from two compilers | SG1, SG5 |
| God methods in env | `VectorizedHamletEnv.__init__` 460 LOC; `get_action_masks` 165 LOC | SG4 |
| Empty / minimal `__init__.py` in many subsystems | External callers pin to deep paths (universe, environment, vfs evaluator/mode) | SG1, SG2, SG4 |
| Three duplicate cascade-validation paths | `universe/validation/` | SG1 |
| Reference-traversal duplicated between compile time and runtime | `world/expression/{type_checker,context}.py` | SG5 |
| Three observation encodings duplicated per substrate | `substrate/*.py` (relative/scaled/absolute) | SG5 |
| Affordance/meter colour palettes duplicated between Python and JS | `recording/video_renderer.py` + `frontend/src/styles/tokens.js` | SG8 |

### 11.6 Security / deployment posture

| Item | Detail | Source |
|------|--------|--------|
| CORS `allow_origins=["*"]` + uvicorn bound `0.0.0.0` | Acceptable for localhost development only; deployment via `townlet-demo.service` would expose | SG8 |
| Inference Q-value log path is CWD-relative | Operationally fragile when invoked outside repo root | SG8 |
| `flask`/`flask-cors` dependencies in pyproject but unused | Larger attack surface and false sense of stack diversity | SG8 |
| `tensorflow[and-cuda]` declared but only used (if at all) for tensorboard logging | Unnecessary CUDA-coupling | Discovery |

---

## 12. Coordinator notes for the validator and downstream phases

- **Confidence is uniformly High** across the 8 reports (per the subagent self-assessments) and
  cross-citations align (e.g. SG2 and SG4 agree on the VTC-program call sites; SG3 and SG4 agree
  on `drive.yaml` vs `drive_as_code.yaml`; SG1 and SG7 agree on the universe compiler's effect-catalog use).
- **VTC runtime call-site verification (validator results):** SG2 hedged on
  `VTCInteractionProgressProgram` and `VTCSocialResidueProgram`. Validator re-grep confirmed
  `VTCInteractionProgressProgram.apply` IS invoked from `environment/action_executor.py:239` per
  tick — alive. The later VFS deep dive supersedes the original `VTCSocialResidueProgram` concern:
  it is now executed through `VTCTransitionRunner` and the compiled transition schedule, without
  adding social-domain branches to `vectorized_env.py`.
- **The strongest evidence for documentation rot** is SG6's finding that the exploration files
  CLAUDE.md describes (`icm.py`, `count_based.py`, `adaptive_rnd.py`) **do not exist** as
  separate files. The validator should confirm by `ls src/townlet/exploration/` independently.
- **For the diagram phase:** Three diagrams are obligatory — C4 Context (Townlet as system, with
  user/operator and frontend as external), C4 Container (the 8 subsystems plus configs/scripts/
  frontend), and C4 Component for the **runtime tick** (SG2+SG4+SG7 collaboration through one
  step). A 4th "config-pack lifecycle" sequence diagram (YAML → SG3 DTOs → SG1 compiler →
  CompiledUniverse → SG4 env init) is the highest-value optional add.
- **For the security surface:** the only inbound surface is the demo's WebSocket and HTTP on
  `:8766`. There are no other listening sockets, no DB credentials (SQLite local), no
  external API consumers. Threat model is narrow.
- **For the quality assessment:** test corpus larger than source (77K vs 45K LOC) is the
  headline; the per-subsystem test directory layout is fully aligned with the runtime layout
  (one `tests/test_townlet/unit/<sg>/` per subsystem); coverage is enabled by default in
  `pyproject.toml`. Concrete coverage % is not measured here — we have a `.coverage` artifact at
  repo root (likely accidentally committed) which the quality phase can interrogate.
