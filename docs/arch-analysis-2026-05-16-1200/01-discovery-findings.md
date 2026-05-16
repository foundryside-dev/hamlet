# 01 — Discovery Findings

Holistic assessment derived **from code only** (per user directive). Documentation is treated as
possibly stale and is not used as authoritative evidence.

---

## 1. Project Identity

- **Name:** `townlet` (pyproject.toml; the legacy `hamlet` package is gone)
- **Repository root:** `/home/john/hamlet` (directory name retained from earlier system)
- **Python target:** 3.13 (`requires-python = ">=3.13"`, `target-version = "py313"`)
- **Build backend:** Hatchling (`src/townlet` is the only packaged wheel target)
- **Project version:** 0.1.0 (Development Status :: 3 - Alpha)
- **License:** MIT
- **Stated purpose (from `pyproject.toml` keywords):** Pedagogical Deep RL — q-learning, LSTM,
  POMDP, curriculum learning, intrinsic motivation

## 2. Directory Topology

```
/home/john/hamlet
├── src/townlet/             # 162 .py files, 45,117 LOC — single packaged module
│   ├── universe/            # UAC compiler: pipeline.py, compiler.py, compilers/, validation/, dto/, loaders/, adapters/
│   ├── vfs/                 # Variable & Feature System: schema, registry, evaluator, VTC kernels
│   ├── config/              # Pydantic v2 DTOs for every YAML schema
│   ├── environment/         # VectorizedHamletEnv, DACEngine, action stack, affordance engine
│   ├── substrate/           # Grid2D/3D/ND, Continuous/ContinuousND, Aspatial
│   ├── world/expression/    # Hand-rolled expression DSL parser + evaluator + type checker
│   ├── world/types/         # World type system
│   ├── agent/               # Neural networks (Simple/Recurrent Q-networks)
│   ├── population/          # VectorizedPopulation training
│   ├── training/            # Replay buffer, training state
│   ├── exploration/         # RND, ICM, count-based, epsilon-greedy, adaptive RND
│   ├── curriculum/          # Adversarial and static curriculum strategies
│   ├── effects/             # Effect catalog + engine (separated from affordances)
│   ├── items/               # Inventory state + item action handler
│   ├── demo/                # UnifiedServer, live_inference entry point
│   └── recording/           # Episode/trajectory recording
├── tests/test_townlet/      # 324 .py files, 77,265 LOC (test corpus ≥ source)
│   ├── unit/{agent,config,curriculum,demo,effects,environment,exploration,
│   │         expression,items,population,recording,substrate,training,universe,vfs,world}/
│   ├── integration/{,vfs/}
│   ├── performance/, properties/, special/, test_curriculum/
│   ├── _fixtures/, fixtures/, helpers/, utils/
│   ├── TEST_WRITING_GUIDE.md
│   └── test_no_defaults_lint.py
├── frontend/                # Vue 3 SFC visualisation, 10,432 LOC
│   └── src/
│       ├── components/      # 27 Vue components (Grid, AspatialView, MeterPanel, etc.)
│       ├── stores/          # simulation.js (single store, Pinia presumed)
│       ├── styles/          # tokens.js — design system
│       └── utils/           # constants.js — affordance icons, grid sizing
├── configs/                 # YAML config packs (data, not code)
│   ├── default_curriculum/  # Active curriculum (hierarchical v2.1 layout)
│   ├── L5_multi_agent/      # Multi-agent experiment pack
│   ├── aspatial_test/, simple/, test/  # Test fixtures
│   └── reference/           # Reference / template configs
├── scripts/                 # CLI entry points
│   ├── run_demo.py          # Unified demo server (training + inference + frontend)
│   ├── validate_compiler_cli.py
│   ├── validate_substrate_configs.py
│   ├── validate_substrate_runtime.py
│   ├── validate_vfs_obs_dimensions.py
│   ├── no_defaults_lint.py
│   └── migrate_affordances_to_effects.py
├── deploy/                  # systemd unit + installer for townlet-demo service
├── docs/                    # 499 markdown files (POSSIBLY STALE — not used as source of truth)
├── runs/                    # Training artifacts (gitignored)
└── .filigree/               # Filigree issue-tracker state
```

## 3. Technology Stack (derived from `pyproject.toml`)

**Core ML / RL:**
- `torch>=2.9,<2.12` (upper bound pinned because Triton 3.7 segfaults under pytest — see filigree `hamlet-74197422b3`)
- `gymnasium>=1.0`, `pettingzoo>=1.24` (RL env interfaces)
- `tensorflow[and-cuda]>=2.20` and `tensorboard>=2.15` (logging)
- `mlflow>=2.9` (experiment tracking)
- `numpy`, `pandas`, `scikit-learn`

**Inference / Serving:**
- `fastapi>=0.100`, `uvicorn[standard]>=0.23`, `websockets>=11`, `flask>=3`, `flask-cors>=4`
  (two web stacks coexist — see Concern §7)

**Config / Serialization:**
- `pydantic>=2` (DTOs throughout `src/townlet/config/`)
- `pyyaml>=6`
- `msgpack>=1.1.2`, `lz4>=4.4.5` (recording compression)
- `cloudpickle>=3` (checkpoint payloads, presumed)

**Parsing:**
- `pyparsing>=3.1` (used by `world/expression/parser.py` for the DSL)

**Frontend:**
- Vue 3 single-file components (27 components observed)
- `vite.config.js` present → Vite build
- (Cannot confirm Pinia/router/etc. without reading `package.json`, which appears empty or missing)

**Tooling:**
- `uv` (lock file present), `pytest` + `pytest-cov` + `pytest-asyncio` + `hypothesis`
- `black` line-length 140, `ruff` (E,F,I,N,W,UP), `mypy` python 3.13, `vulture` for dead code
- Pre-commit hooks (`.pre-commit-config.yaml` present)

## 4. Entry Points

| Entry | Where | Purpose |
|-------|-------|---------|
| `python -m townlet.universe {compile,inspect,validate}` | `src/townlet/universe/__main__.py` | UAC CLI |
| `python -m townlet.demo.live_inference` | `src/townlet/demo/live_inference.py` (presumed) | WebSocket inference server |
| `python scripts/run_demo.py` | `scripts/run_demo.py` | Unified demo (training + inference + frontend coordination) |
| `npm run dev` in `frontend/` | Vite dev server | Frontend visualisation |
| `townlet-demo.service` | `deploy/townlet-demo.service` | Production systemd unit |

`run_demo.py` reveals the **live config schema** is `configs/<pack>/<level>/`, e.g.
`configs/default_curriculum/L1_full_observability/`. This is the hierarchical v2.1 layout.

## 5. Subsystem Inventory (by LOC, descending)

| LOC | Subsystem | Group | Stated role (will be verified by SG analysis) |
|-----:|-----------|-------|-----------------------------------------------|
| 7,080 | `vfs/` | SG2 | Variable & Feature System (VTC runtime, evaluator, registry, profiles) |
| 5,750 | `universe/` | SG1 | Universe Compiler (UAC) — seven-stage YAML → CompiledUniverse pipeline |
| 5,041 | `environment/` | SG4 | VectorizedHamletEnv + DACEngine + action / affordance stack |
| 4,728 | `config/` | SG3 | Pydantic DTO layer for every YAML schema |
| 3,700 | `substrate/` | SG5 | Spatial substrates (Grid2D/3D/ND, Continuous, Aspatial) |
| 3,172 | `demo/` | SG8 | Unified server, live inference |
| 3,131 | `world/` | SG5 | Expression DSL: parser, evaluator, type checker, AST, history, functions |
| 2,878 | `effects/` | SG7 | Effect catalog and engine |
| 2,228 | `training/` | SG6 | Replay buffer, training state |
| 1,603 | `recording/` | SG8 | Episode/trajectory recording |
| 1,602 | `items/` | SG7 | Inventory state, item manager, item action handler |
| 1,405 | `population/` | SG6 | Vectorized population trainer |
| 1,084 | `agent/` | SG6 | SimpleQNetwork, RecurrentSpatialQNetwork |
| 901 | `exploration/` | SG6 | RND, ICM, count-based, epsilon-greedy, adaptive RND |
| 809 | `curriculum/` | SG6 | Adversarial/static curriculum strategies |
| 10,432 (Vue) | `frontend/` | SG8 | Visualisation dashboard (27 components, 1 Pinia store) |

## 6. Cross-Subsystem Dependency Signals (preliminary)

From spot-reads of `environment/vectorized_env.py` and `universe/pipeline.py`:

- `environment` imports from: `universe.dto`, `substrate`, `items`, `vfs.{evaluator,observation_builder,registry,vtc}`
- `universe.pipeline` imports from: `effects.catalog`, `universe.{compiled,dto,raw_configs_v21,symbol_table}`, `vfs.observation_builder`
- `universe.compilers/` aligns 1:1 with subsystems: `actions.py`, `effects.py`, `observation.py`, `vfs.py`, `metadata.py`, `optimization.py`
- `universe.validation/` is dedicated to declarative validation: `feasibility`, `limits`, `references`, `semantics`

Hypothesis (to validate via SG analysis): the **Universe Compiler (SG1)** sits between
the **Config DTOs (SG3)** (input) and the **Environment runtime (SG4)** (consumer), producing a
`CompiledUniverse` that fans out to substrate, effects, items, and VFS. The VFS evaluator is the
runtime kernel for needs/rewards/affordance gates.

## 7. Initial Concerns (to be confirmed by subagents)

These are **flagged** for downstream investigation — not asserted as findings.

1. **Two web frameworks present in deps:** `fastapi/uvicorn/websockets` and `flask/flask-cors`. Either
   a real dual-stack design or a leftover that violates the project's "delete unused code" rule.
2. **Test corpus larger than source (77K LOC tests vs 45K LOC src).** Could be healthy coverage or
   bloat; SG6 / final report should comment after subsystem reviews.
3. **Docs ≈ 499 markdown files** with CLAUDE.md already empirically stale on config-pack names.
   Documentation maintenance is itself a finding.
4. **Coverage file at repo root.** `.coverage` (405,504 bytes) is present locally. **Verified
   in quality phase: it is in `.gitignore:47` and untracked** — a local working-tree artefact,
   not an accidental commit. The actual stale-at-root tracked files are the
   `DEPENDENCY_ANALYSIS_*.{txt,md}` quartet (see §5 and quality assessment §4).
5. **Stray legacy artifacts at root:** `DEPENDENCY_ANALYSIS_*.{txt,md}` and `.defaults-whitelist*.txt`
   suggest prior ad-hoc audits left files behind.
6. **CHANGELOG.md is 36 KB** — unusual for a 0.1.0 alpha; suggests heavy iteration pre-release.
7. **`tensorflow[and-cuda]>=2.20` AND `tensorflow>=2.20` both declared.** Looks redundant. Plus
   coexists with `torch`; project may use TF only for TensorBoard (likely accidental dependency).
8. **`pyparsing` for the world expression DSL** — confirmed by `world/expression/parser.py`. Custom
   DSL is a non-trivial maintenance surface; needs deliberate documentation.
9. **`universe/raw_configs_v21.py`** — explicit version suffix implies prior v1.x→v2.1 migration; check
   that all v1.x code has been removed (per project's no-backwards-compat rule).

## 8. Documentation Drift Audit (spot-check)

| CLAUDE.md claim | Reality observed |
|----|----|
| Active configs are `L0_0_minimal, L0_5_dual_resource, L1, L2, L3` directly under `configs/` | Actual: `configs/default_curriculum/L1_full_observability` etc. (hierarchical v2.1) |
| `from townlet.config.training_v2_config import load_training_v2_config` | Confirmed (used in `scripts/run_demo.py`) |
| `src/hamlet/` marked obsolete | No `src/hamlet/` exists at all — entirely deleted (matches the no-backwards-compat rule) |
| DAC is required; `reward_strategy` is removed | `src/townlet/config/drive_as_code.py` exists; needs subagent confirmation that `reward_strategy` field is genuinely removed |

The CLAUDE.md description of the v2.1 hierarchical config layout is **outdated**; it describes flat
config packs. New documentation must use the hierarchical layout actually present in the code.

## 9. Strategy & Confidence

- **Orchestration:** PARALLEL — 8 codebase-explorer subagents in one batch
- **Validation:** mandatory analysis-validator gate after catalog assembly
- **Diagrams:** dedicated diagram subagent after validated catalog
- **Quality + Security:** spawned in parallel during the diagram phase (independent inputs)
- **Confidence in this discovery file:** **High** for directory topology and LOC; **Medium** for
  subsystem responsibilities (derived from filenames and a few imports only — subagents will confirm)
