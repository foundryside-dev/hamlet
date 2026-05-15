# Discovery Findings

## Project Identity

- **Name**: townlet (formerly hamlet — `src/hamlet/` is obsolete, all live code is in `src/townlet/`).
- **Purpose**: Pedagogical Deep RL environment — "trick students into learning graduate-level RL by making them think they're playing The Sims."
- **Status**: Pre-release, zero users. CLAUDE.md mandates **no backwards-compatibility patterns** — old configs/code paths are deleted, not migrated.

## Scale

| Surface | Count |
|---|---|
| Python source files (`src/townlet/`) | 152 |
| Source LOC | ~39,920 |
| Test files (`tests/test_townlet/`) | 305 |
| Test-to-source ratio | >2:1 |
| Top-level subsystem directories | 15 (collapse to 8 logical subsystems) |
| Config packs (`configs/`) | 5 (aspatial_test, default_curriculum, reference, simple, test) |
| Pydantic DTO modules (`config/`) | 18 |
| CLI entry points | `python -m townlet.universe` (compile/inspect/validate), `python -m townlet.demo.live_inference`, `scripts/run_demo.py` |

**Drift note**: `CLAUDE.md` still references the legacy curriculum naming (`L0_0_minimal`, `L0_5_dual_resource`, `L1_full_observability`, `L2_partial_observability`, `L3_temporal_mechanics`). The active `configs/` directory contains a different layout (`default_curriculum`, `simple`, `reference`, …). This is documentation drift, not a code defect.

## Technology Stack

- **Python**: 3.13 only (`requires-python = ">=3.13"`, all targets pinned to py313).
- **Deep learning**: `torch >=2.9,<2.12` (upper bound pinned: filigree `hamlet-74197422b3` — triton 3.7 segfault inside pytest), TensorFlow 2.20 (with CUDA), `tensorboard >=2.15`.
- **RL frameworks**: `pettingzoo >=1.24`, `gymnasium >=1.0`.
- **Schema / config**: `pydantic >=2`, `pyyaml >=6`, `pyparsing >=3.1` (effects DSL).
- **Serving**: `fastapi`, `uvicorn[standard]`, `flask`, `websockets`, `flask-cors` — multiple HTTP/WS stacks (live inference uses websockets directly; FastAPI/Flask presence suggests other servers).
- **Experiment tracking**: `mlflow >=2.9`.
- **Recording (optional extra)**: `msgpack`, `lz4`, `ffmpeg-python`, `pillow`, `matplotlib`.
- **Tooling**: `black`, `ruff` (selects E/F/I/N/W/UP), `mypy` (lenient — `disallow_untyped_defs = false`), `hypothesis`, `vulture`, `pytest-asyncio`, `pytest-cov`.

## Top-Level Source Layout

```
src/townlet/
├── agent/              # Q-networks, factories (loss/network/optimizer)
├── config/             # 18 Pydantic DTO modules — no-defaults enforcement
├── curriculum/         # Adversarial + static curriculum strategies
├── demo/               # Live inference server (websockets), runner, database
├── effects/            # Effect DSL: schema, parser, compiler, catalog, executor, scheduler, manager
├── environment/        # VectorizedHamletEnv, DAC engine, action builder/validator, affordance engine
├── exploration/        # RND, ICM, adaptive intrinsic, epsilon-greedy
├── items/              # Inventory, instances, action handlers
├── population/         # VectorizedPopulation, runtime registry
├── recording/          # Recorder, replay, video export/render, criteria
├── substrate/          # Spatial substrate types (Grid2D/3D/ND, continuous, aspatial)
├── training/           # Training state, replay buffer
├── universe/           # ⭐ Seven-stage UAC compiler (reorganized post 2026-05)
│   ├── compilers/      #   stage modules: actions, effects, metadata, observation, optimization, vfs
│   ├── dto/            #   typed metadata DTOs (5 modules)
│   ├── loaders/        #   v21, preflight
│   ├── validation/     #   feasibility, limits, references, semantics
│   └── adapters/       #   vfs_adapter (eliminates round-trip rehydration)
├── vfs/                # Variable & Feature System: schema, registry, observation_builder, evaluator
└── world/              # World types, expression evaluator
```

## Universe Compiler — Current State (Post-Reorganization)

The pipeline described in `docs/arch-analysis-2026-05-15-compiler-cleanup/01-discovery-findings.md` referenced a 4,431-line `compiler.py` monolith. **That cleanup is now in flight and largely complete**:

- `compiler.py`: 619 lines (down from 4,431) — orchestration shell only.
- `pipeline.py`: 59 lines — new pipeline harness.
- `compiled.py`: 965 lines — `CompiledUniverse` artifact and cache.
- `compilers/`: 6 stage modules (actions, effects, metadata, observation, optimization, vfs).
- `dto/`: 5 typed metadata DTOs (action_metadata, affordance_metadata, meter_metadata, observation_activity, observation_spec, universe_metadata).
- `loaders/`: `v21.py` (renamed from `raw_configs_v21.py`?) + `preflight.py`.
- `validation/`: split into `feasibility`, `limits`, `references`, `semantics`.
- `adapters/vfs_adapter.py`: addresses the "rebuild DTOs from artifacts" round-trip noted in the prior pass.

This is the seven-stage pipeline:

1. **Parse** v2.1 configs (`loaders/v21.py`)
2. **Symbol table** (`symbol_table.py`)
3. **Resolve** references (`validation/references.py`)
4. **Cross-validate semantics** (`validation/{semantics,feasibility,limits}.py`)
5. **Metadata enrichment** (`compilers/metadata.py`, `compilers/vfs.py`, `compilers/effects.py`)
6. **Optimization tensors** (`compilers/optimization.py`)
7. **Emit / cache** (`compiled.py`)

In-progress (per `git status`): the test suite is being updated to match (`test_compiler_cli.py`, `test_compiler_pipeline.py`, `test_pipeline_modules.py`, etc. all modified).

## Runtime Hub: `VectorizedHamletEnv`

`src/townlet/environment/vectorized_env.py` is the largest single file at **2,200 lines**. It is the central runtime consumer of `CompiledUniverse` and the surface the population/training loops drive. **This is a refactoring candidate downstream of the compiler cleanup** — analogous to where the compiler stood three months ago.

Surrounding it in the same package:

- `dac_engine.py` — Drive-as-Code reward engine (GPU computation graph).
- `action_builder.py` + `action_config.py` + `action_labels.py` + `substrate_action_validator.py` — action assembly and validation.
- `affordance_config.py` + `affordance_engine.py` + `affordance_layout.py` — affordances (interactions in the world).
- `meter_dynamics.py` — meter (energy/hygiene/etc.) update logic.
- `temporal_utils.py` — day/night and tick clocks.
- `null_managers.py` — null-object pattern for disabled subsystems.

## Configuration / DTO Surface

`config/` has 18 DTO modules — most named after the YAML file they validate. The package enforces a **no-defaults principle**: every behavioral parameter must be present in the config, no implicit fallbacks. The recently-modified files in `git status` (`compiler.py`, `compilers/*`, `validation/*`) indicate the cleanup pass is reinforcing this discipline.

Modules:
`actions_config`, `affordance_masking`, `affordances_v2_config`, `agent_config`, `bars_v2_config`, `brain_config`, `capability_config`, `cues`, `curriculum_config`, `drive_as_code`, `effects_config`, `environment_config`, `experiment_config`, `items_config`, `stratum_config`, `training_v2_config`, `vfs_config`, `vfs_profiles_config`.

## Variable & Feature System (VFS)

Declarative state-space layer:
- `schema.py` — `VariableDef`, `ObservationField`, `NormalizationSpec`, `WriteSpec`.
- `registry.py` — runtime storage, GPU tensors, access control.
- `observation_builder.py` — compile-time spec generation, dimension validation.
- `evaluator.py` — runtime variable resolution (links to `world/expression`).
- `history.py` — temporal history support.
- `profiles.py` — per-level VFS profile (sliced from the compiled universe).

The compiler emits VFS variable definitions via `compilers/vfs.py`; the new `adapters/vfs_adapter.py` is intended to keep runtime consumption flowing directly off compiler artifacts without re-parsing config DTOs.

## DAC — Drive As Code

Reward functions are declared in `drive_as_code.yaml` and compiled into GPU computation graphs by `environment/dac_engine.py`. The DTO is `config/drive_as_code.py`. Per CLAUDE.md, the legacy `RewardStrategy` class hierarchy was deleted; YAML-driven DAC is the only reward path.

Formula:
```
total_reward = extrinsic + (intrinsic × effective_intrinsic_weight) + shaping
where effective_intrinsic_weight = base_weight × Π(modifiers)
```

`drive_hash` (SHA-256 of compiled DAC) is part of checkpoint provenance.

## Effects Subsystem

Compiler-side **and** runtime-side. Effect commands flow YAML → AST → CommandNode → catalog → scheduled execution:
- `schema.py`, `parser.py`, `compiler.py` — compile-time AST.
- `catalog.py` — deterministic effect IDs.
- `manager.py`, `executor.py`, `scheduler.py` — runtime application.
- `collections.py`, `context.py` — runtime helpers.

This is a substantial sub-DSL: pyparsing-based parser + type-checked compiler + scheduled executor.

## Recording Subsystem

`recording/` is an episode-replay layer (`recorder`, `replay`, `criteria`, `data_structures`, `video_export`, `video_renderer`). Optional install (extras = `recording`) bringing msgpack/lz4/ffmpeg/pillow/matplotlib.

## Demo / Live Inference

`demo/live_inference.py` is the websocket inference server documented in CLAUDE.md (port 8766). `demo/runner.py` is the `DemoRunner` context manager. `demo/database.py` and `demo/unified_server.py` indicate the demo layer has grown a persistent data layer and a combined-server entry point beyond what the docs describe.

## Test Layout

```
tests/test_townlet/
├── unit/           # per-subsystem unit tests (agent, items, training, effects, recording, ...)
├── integration/    # cross-subsystem (incl. vfs/)
├── e2e/            # end-to-end (per pytest marker)
├── performance/    # marked `slow`
├── properties/     # hypothesis-based
├── fixtures/       # fixture data
├── _fixtures/      # test helpers
├── helpers/
├── utils/
├── special/
└── test_curriculum/
```

Pytest config skips `slow` tests by default; coverage targets `townlet` source with branch coverage.

## Scripts

- `run_demo.py` — primary training entry point.
- `validate_compiler_cli.py` — exercises the compiler CLI; modified in current branch.
- `validate_substrate_configs.py`, `validate_substrate_runtime.py`, `validate_vfs_obs_dimensions.py` — validation helpers.
- `no_defaults_lint.py` — enforces the no-defaults discipline.
- `migrate_affordances_to_effects.py` — one-off migration script.

## In-Flight Work (from git status)

The current branch (`project-recovery`) is in the middle of the compiler-cleanup-modernization plan (`docs/plans/2026-05-15-compiler-cleanup-modernization.md`). Modified files cluster around:

- `src/townlet/universe/*` — pipeline split, validation modules, loaders, DTOs, adapters.
- `src/townlet/environment/vectorized_env.py` — adapting to typed compiler artifacts.
- `tests/test_townlet/unit/universe/*` — test suite catching up.
- `tests/test_townlet/unit/universe/test_compiler_*.py` — replaced helper-pinned tests.

## Confidence

- **High confidence**: source-tree topology, technology stack, subsystem boundaries, compiler reorganization status, runtime hub identity.
- **Medium confidence**: DTO-level dependency graph between `config/` modules (will be deepened in catalog phase).
- **Lower confidence**: full behavior of `effects/` runtime executor, `recording/` integration points, `unified_server` purpose — these are the most under-documented subsystems and warrant the most attention in the catalog pass.
