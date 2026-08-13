# Townlet

The repository directory is named `hamlet`; the Python distribution and the only live source tree
are `townlet`. Same project.

Townlet is a deep reinforcement-learning substrate expressed as configuration. An environment —
variables, observation layout, substrate topology, affordances, effects, items and reward
function — is written in YAML, compiled into a single frozen, hash-carrying `CompiledUniverse`
artifact, and executed GPU-natively against torch tensors.

The point is authoring. The project's endorsed vision (`docs/product/vision.md`) puts the pivot in
one line: *from game as experience to writing a game as experience*. The change it exists to make
is that someone with an idea for a mechanic or a game system can turn it into a running, trainable,
reproducible RL environment by writing config — no environment subclass, no observation-tensor
plumbing, no reward-function code. Each subsystem below exists to move a category of "you must
write Python for this" into "you can declare this."

The survival world shipped in `configs/default_curriculum` — eight meters, fourteen affordances,
one 8×8 grid — is intended as the first-class demonstration of that idea, not as the product
itself.

## Status: pre-release, mid-rewrite

- Version 0.1.0, classified `Development Status :: 3 - Alpha`. There are no release tags; the
  repository's only tag, locally and on `origin`, is the oracle tag below.
- All live work is on branch `project-recovery`, **145 commits ahead of `main`**. `main`'s tip
  commit is dated 2025-11-28 and does not describe the current system: `docs/product/`,
  `docs/oracle/` and `src/townlet/oracle/` do not exist on it at all.
- The project is mid **strangler rewrite behind a pinned oracle**. Tag `oracle-2026-08-13`
  (commit `0e875d7a`) freezes the previous system as the specification for preserved behaviour.
  From `docs/oracle/ORACLE.md`: "The oracle never mutates", and "a diff against the oracle is a
  defect in the rebuild unless the register says otherwise." Accepted differences are recorded in
  `docs/oracle/known-divergences.md`.
- **CI has not validated any of this work.** No workflow has ever run on `project-recovery`, and
  none has passed anywhere since 2025-11-28. See [Continuous integration](#continuous-integration)
  — the quality gates that are actually enforced here are run locally, by hand.
- Where this file calls something shipped, it means *present and wired*, not mature. The project
  came out of a long stretch of intermittent attention and is unfinished in places; the specific
  gaps are under [Known rough edges](#known-rough-edges).
- No backwards compatibility: no fallbacks, no deprecation cycle, no migration paths. Breaking
  changes land directly.

*Every command, file path, count and quotation below was executed or read against the working tree
at commit `a099663c` (2026-08-14). There are deliberately no test counts, coverage percentages,
observation widths or training-performance figures in this README — see [Numbers](#numbers).*

## A universe is YAML

`configs/default_curriculum/stratum.yaml` declares the world's physics. This is the entire file:

```yaml
stratum:
  version: "1.0"

  substrate:
    type: grid

    grid:
      topology: square
      width: 8
      height: 8

      boundary: clamp

      distance_metric: manhattan

      observation_encoding: relative
      diagonals: true

  vision_support: both

  temporal_support: enabled

  observation_mode:
    mode: full_auto
```

Nothing else defines the substrate. The grid is 8×8 for every level in the pack: `stratum.yaml`
exists only at pack root, and the level loader reads no substrate file from a level directory.
Replacing that `substrate` block re-substrates the same experiment. The measured case is recorded
as Trial 001 in `docs/product/metrics.md`: the survival pack was moved to a 6-dimensional
`gridnd` world by editing about six lines of `stratum.yaml`, with zero lines changed under
`src/townlet/` — it compiled, reset and stepped, the movement vocabulary auto-expanded to
`DIM0_NEG … DIM5_POS`, and the entire domain carried over. That trial also found the real caveat:
`gridnd` has no partial-vision support, so the pack's POMDP levels have to be switched to
`active_vision: global` or the whole-pack compile fails.

Rewards are declarative in the same way. This is
`configs/default_curriculum/levels/L1_full_observability/drive.yaml`, in full:

```yaml
drive:
  version: '1.0'
  modifiers:
    energy_crisis:
      bar: energy
      ranges:
      - name: range_0
        min: 0.0
        max: 0.2
        multiplier: 0.0
      - name: range_1
        min: 0.2
        max: 1.0
        multiplier: 1.0
  extrinsic:
    type: constant_base_with_shaped_bonus
    base_reward: 0.01
    bar_bonuses:
    - bar: energy
      center: 0.0
      scale: 0.5
    - bar: health
      center: 0.0
      scale: 0.5
    variable_bonuses: []
    apply_modifiers: []
  intrinsic:
    strategy: adaptive_rnd
    base_weight: 0.1
    apply_modifiers:
    - energy_crisis
    adaptive_config:
      enabled: true
      threshold: 100.0
      decay_rate: 0.995
      min_weight: 0.01
  shaping:
  - type: approach_reward
    weight: 0.01
    target_affordance: EAT
    max_distance: 5.0
  - type: completion_bonus
    weight: 0.1
    affordance: SLEEP
  composition:
    normalize: false
    clip: null
    log_components: true
    log_modifiers: true
```

There are no reward classes to subclass — `src/townlet/environment/reward_strategy.py` does not
exist and no `RewardStrategy` remains anywhere under `src/`. The compiler turns that YAML into a
GPU-native computation graph and hashes it into the compiled artifact, so a checkpoint knows which
reward function produced it. Two fields in that file are inert: `composition.normalize` and
`composition.clip` validate but have no reader (see [Known rough edges](#known-rough-edges)).

### Pack layout

```
configs/default_curriculum/
  experiment.yaml       # which levels the pack declares
  stratum.yaml          # substrate, topology, observation mode
  environment.yaml      # VFS variable definitions, cascade graph
  actions.yaml          # substrate and custom actions, action labels
  brain.yaml            # architecture, optimizer, loss, Q-learning, replay
  items.yaml  effects.yaml  vfs_profiles.yaml
  levels/<level>/
    curriculum.yaml     # vision and temporal switches
    bars.yaml           # meters, bounds, cascades
    affordances.yaml    # interactions, costs, opening hours, placement
    drive.yaml          # reward specification
    training.yaml       # hyperparameters, enabled actions
```

A level directory carries those five required files plus an optional `items.yaml` declaring
level-scoped item spawns; the loader (`src/townlet/universe/raw_configs_v21.py`) reads nothing else
from it. The shared catalogs `vfs_profiles.yaml` and `effects.yaml` are rejected outright at level
scope, and a level `items.yaml` must declare the v1.0 ItemsAppearance schema
(`src/townlet/universe/loaders/preflight.py`). Notably the network architecture is pack-level: a
level's `training.yaml` overrides exactly five scalars of `brain.yaml` — gamma, target-update
frequency, the double-DQN flag, learning rate and replay capacity — and none of them live in the
`architecture` block.

**About the shipped curriculum, since older docs oversell it.** `default_curriculum` declares five
levels, but `bars.yaml`, `affordances.yaml` and `drive.yaml` are byte-identical across all five,
and the substrate is pack-level. Only two levels change the world the agent sees:
`L2_partial_observability` (`active_vision: partial`) and `L3_temporal_mechanics`
(`active_temporal: true`, `day_length: 24`). Compiling all five and comparing artifacts,
`observation_schema_hash` takes exactly three distinct values — one shared by L0_0, L0_5 and L1,
one for L2, one for L3. Five level directories, three distinct observation surfaces. Within the
first group, `L0_5_dual_resource` and `L1_full_observability` differ in one line of one file
(`output_subdir`), and `L0_0_minimal` differs from them in Q-learning and replay hyperparameters
and in enabling one fewer custom action (`REST` only, against `REST` and `MEDITATE`) — which does
move its `action_schema_hash` and `vfs_hash`.

## Install

Python 3.13 or newer (`.python-version` pins 3.13) and [uv](https://docs.astral.sh/uv/). A GPU is
optional; the runtime falls back to CPU.

```bash
git clone https://github.com/foundryside-dev/hamlet
cd hamlet
git checkout project-recovery
uv sync --all-extras
```

The `git checkout` is not optional: the remote's default branch is `main`, and the paths this file
references — `docs/product/`, `docs/oracle/`, `src/townlet/oracle/`, `configs/L5_multi_agent` — do
not exist there.

Use `--all-extras`: it is what all four CI workflows specify, and a bare `uv sync` installs runtime
dependencies only — pytest, black, ruff and mypy live in the `dev` extra. No `PYTHONPATH` export is
needed; the project installs editable. There are no console-script entry points, so everything runs
as `uv run scripts/<name>.py` or `uv run python -m townlet.<module>`.

## Run something

Check that a pack compiles (no cache written):

```bash
uv run python -m townlet.universe validate configs/default_curriculum \
    --primary-level L1_full_observability
```

Compile it, and inspect the artifact:

```bash
uv run python -m townlet.universe compile configs/default_curriculum \
    --primary-level L1_full_observability
uv run python -m townlet.universe inspect configs/default_curriculum \
    --primary-level L1_full_observability --format json
```

`--primary-level` is required by `compile` and `validate`, and by `inspect` whenever you point it
at a pack rather than at a `.msgpack` artifact. Compiling a pack compiles every level in it, but
the cache holds one artifact per primary level, at
`<pack>/.compiled/universe-<level>.msgpack` (gitignored).

Train. `--config` takes the pack root, not a level directory, and `--level` and `--inference-port`
are both required:

```bash
uv run scripts/run_demo.py --config configs/default_curriculum \
    --level L1_full_observability --episodes 10000 --inference-port 8766
```

This runs training and a WebSocket inference server in one process and writes
`runs/<output_subdir>/<timestamp>/`, where `output_subdir` is read from the level's
`training.yaml` (`run_metadata.output_subdir`, required — there is no fallback; each
`default_curriculum` level sets it to its own directory name). The run directory holds
`checkpoints/` with `.sha256` sidecars, `metrics.db`, `tensorboard/`, `training.log`, and a
`config_snapshot/` of the configuration that produced them.

Serve a trained checkpoint on its own — six positional arguments, the last two being the pack and
the level:

```bash
uv run python -m townlet.demo.live_inference <checkpoint_dir> 8766 0.2 10000 \
    configs/default_curriculum L1_full_observability
```

Run the differential harness that adjudicates the rewrite. It creates or reuses a detached git
worktree at the oracle tag under `.oracle/`, runs the same pack, level, seed, agent count and step
count on both trees as subprocesses, and compares the env-step traces:

```bash
uv run python -m townlet.oracle.harness --cell default_curriculum:L0_0_minimal
```

Its declared matrix is five levels × {cpu, cuda}; the CUDA cells are always declared and reported
SKIPPED rather than silently dropped when `--cuda` is absent. It exits 0 only when every cell is
AGREE or SKIPPED, and an empty run exits 1 so that doing nothing cannot look green. Both entries in
the divergence register are checkpoint-boundary surfaces and cannot appear in an env-step trace, so
under v1's trace-only scope the harness treats any DIVERGE or HASH_MISMATCH as a rebuild defect or
a missing register entry — both findings.

### Checks, run locally

```bash
uv run ruff check .
uv run black --check src tests
uv run mypy src/townlet --show-error-codes
uv run python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt
uv run python scripts/validate_compiler_cli.py
uv run pytest
```

## Continuous integration

Four GitHub Actions workflows exist, all specifying `uv sync --all-extras` on Python 3.13: Lint,
Config Validation, Tests, and Full Test Suite.

**None of them has ever run against this branch, and none has passed anywhere since 2025-11-28.**
Treat the badge-shaped assumption that CI is guarding this repository as false:

- Lint, Config Validation and Tests trigger on `push` to `main` and on `pull_request`.
  `project-recovery` is pushed directly and is neither, so `gh run list --branch project-recovery`
  returns nothing. No commit of the rewrite has been checked by CI.
- Full Test Suite runs on a 06:00 UTC schedule against the default branch. Every scheduled run on
  record after the last green build failed, the most recent being 2026-01-30, and none is recorded
  since: GitHub reports that workflow's state as `disabled_inactivity`. Re-enabling it is a
  deliberate act (`gh workflow enable "Full Test Suite"`), not something the next push restores.
- The last successful run of any workflow was 2025-11-28, on the merge of PR #31 into `main`.

Three of the four — every one except Lint — run `scripts/validate_compiler_cli.py` before their
other steps, and on this tree that script exits 1 (see [Known rough edges](#known-rough-edges)). No
step sets `continue-on-error`, so were CI to run here, all three would stop at that step; in Tests
and Full Test Suite it precedes pytest, which would not be reached. Restoring CI therefore means
fixing that script's input before the workflows are pointed at this branch.

## Architecture at a glance

`src/townlet/` is the only source tree — there is no `src/hamlet/` — and holds 16 packages. The
load-bearing ones:

- **`universe/` — the universe compiler (UAC).** Parses and cross-validates a pack, resolves its
  references and shared schemas, compiles every level, and emits one `CompiledUniverse`: a frozen
  dataclass carrying 16 declared `*_hash` fields plus per-level metadata. Not all sixteen are
  enforced — see checkpoint identity below. The cache is keyed on a config hash and a provenance id
  (compiler version, git sha, python, torch and pydantic versions), and is discarded when any
  config file's mtime is newer than the artifact's.
- **`vfs/` — variables, observation spec, and compiled transition programs (VTC).** Access control
  is enforced at runtime, not merely declared: `VariableRegistry` raises `PermissionError` when a
  reader or writer is not on the variable's list. The compiled transition schedule is built into
  `VectorizedHamletEnv` and drives the ordered phases of the step loop.
- **`environment/dac_engine.py` — declarative rewards (DAC),** compiled from a level's `drive.yaml`.
- **`agent/` — brain-as-code, layer 2.** `brain.yaml` selects architecture, optimizer and loss
  through `network_factory.py`, `optimizer_factory.py` and `loss_factory.py`.
- **`environment/`, `population/`, `substrate/` — the vectorized torch runtime.** Device is an
  explicit parameter: `VectorizedHamletEnv` requires one and raises rather than picking a default.
- **`training/checkpoint_utils.py` — checkpoint identity.** One shared gate,
  `assert_checkpoint_identity`, called by both the training-resume path (`demo/runner.py`) and the
  serving path (`demo/live_inference.py`). Eight of the sixteen `*_hash` fields are stamped into a
  checkpoint, and seven of those are hard-compared on load — `vfs_hash`, `drive_hash`, the
  effective `brain_hash`, and the four per-level content hashes — alongside observation dim, action
  count, observation-field UUIDs and `primary_level`, so a checkpoint refuses to load into a
  universe it does not match, including a different level of the same pack. What is *not* enforced
  is recorded rather than hidden: `observation_schema_hash` is stamped and never compared, and the
  five pack-level hashes (`experiment`, `stratum`, `environment`, `actions`, `items`) are computed
  and serialized and read by nobody — `DIV-001` in `docs/oracle/known-divergences.md`.
- **`oracle/` — the differential harness** described above.

## Delivered, and intended

Delivered and wired at this commit: a YAML pack compiles to a frozen, hash-carrying artifact
(`configs/default_curriculum` and `configs/L5_multi_agent` both validate clean); that artifact
drives the vectorized torch environment; reward functions are specified in config, with no Python
reward classes left to subclass; VFS access control is enforced at runtime; and the training entry
point runs end to end, writing a run directory whose `training.log` ends *Training loop completed
normally* beside a `config_snapshot/` of the pack that produced it.

Intent, not yet built — stated plainly because older docs blur the line:

- **Brain-as-code layers 1 and 3.** The behaviour contract (panic thresholds, forbidden actions,
  personality dials, allowed goals) and the declarative think-loop graph are specified in
  `docs/architecture/hld/02-brain-as-code.md` and have no implementation: their identifiers appear
  in zero files under `src/` and `configs/`. Layer 2, the network/optimizer/loss surface, is real.
- **One standard compiler for both halves of an experiment.** The universe compiles to an artifact;
  the brain rides inside it as a validated `BrainConfig` plus a `brain_hash`, rather than compiling
  to an artifact of its own. `CompiledBrain` exists only in `docs/`.
- **A second demonstrator that varies the domain rather than the substrate.** The substrate axis
  has a measured witness (Trial 001, above). `docs/product/vision.md` names four existing packs as
  domain-varying candidates of unverified depth (`aspatial_test`, `L5_multi_agent`, `simple`,
  `reference`); the last two of those do not compile (below).
- **The "Low Energy Delirium" reward-hacking lesson** described in older docs. It is not
  implemented: no level of the shipped curriculum declares the multiplicative reward the lesson
  depends on.

## Known rough edges

- **The frontend cannot be built as shipped.** `frontend/` holds real Vue single-file components
  and a `vite.config.js`, but there is no `package.json` or lockfile anywhere in the repository, so
  `npm run dev` cannot run — although `scripts/run_demo.py --help` still tells you to run it.
- **Two of the five config packs outside `configs/test/` do not compile.** `configs/simple` and
  `configs/reference/model_pack` both fail at parse with the same schema drift in their
  `actions.yaml` (custom actions declaring `costs`/`effects` blocks the current schema forbids).
  The repo's own `scripts/validate_compiler_cli.py` sweeps every pack it does not explicitly
  exclude and exits 1 on this tree, tripping on `reference/model_pack` in sorted order before it
  ever reaches `simple`. (`configs/` holds 20 directories carrying an `experiment.yaml`; 15 are
  fixtures under `configs/test/`, three of which the script declares expected-to-fail.)
- **The declarable surface exceeds the exercised surface.** Measured at this commit by compiling
  every pack that compiles and counting rules in-process:
  - Three of the nine compiled transition-program families — `action_write`,
    `interaction_progress` and `social_residue` — carry zero rules in every one of them.
    `action_write` is worse than unexercised: no YAML can produce one, because
    `universe/compilers/actions.py` hardcodes `writes=()` for every action.
  - `drive.yaml`'s `intrinsic.strategy` accepts `icm` and `count_based`, which have no
    implementation anywhere — those tokens occur only inside `config/drive_as_code.py`, in the
    `Literal`, its docstring and an unread `icm_config` field. `composition.normalize` and
    `composition.clip` validate but have no reader; `dac_engine.py` takes only `log_components`
    and `log_modifiers` from that block.
  - `grid3d` passes the substrate schema but has no branch in `SubstrateFactory.build`; 3-D grids
    are reachable as `type: grid` with `topology: cubic`.
  - All four VFS variables declared in `configs/default_curriculum/environment.yaml` —
    `deficit_energy`, `deficit_satiation`, `time_since_last_eat`, `time_since_last_sleep` — are
    observed but written by nothing: those names appear nowhere under `src/townlet/`, and in no
    config anywhere beyond their own declaration.
- **Documentation outside `docs/product/` and `docs/oracle/` is being reconciled.** `CLAUDE.md`,
  `scripts/README.md` and older architecture docs still name config paths, filenames and scripts
  that do not exist in the tree — `scripts/README.md`, for one, documents
  `scripts/validate_configs.py` and `scripts/validate_substrates.py`, neither of which is present.
  The count of confirmed-false claims in canonical docs is tracked as a product guardrail in
  `docs/product/metrics.md`.
- **The recording subsystem is slated for removal** once its intent is captured
  (`pyproject.toml`, `recording` extra). Its MP4 export also shells out to an `ffmpeg` binary that
  is not a Python dependency.

## Numbers

This README states no test count, no coverage percentage, no observation-vector width and no
learning-curve figures. Numbers like those start decaying the moment they are written, which is
how the last set went wrong: the README still on `main` badges a test count and a coverage
percentage and states an observation width, and `docs/product/metrics.md` records that coverage
figure as measured-false, while the width it gives is not what the compiler reports for any
`default_curriculum` level at this commit. Read them off the tree instead: compile a level and read
`Observation Dim` from the summary (the field is `metadata.observation_dim`, set from
`observation_spec.total_dims` — plural — and it is a property of the pack, not a constant of the
project); run `uv run pytest` for the suite; and read `docs/product/metrics.md` for measurements
stamped with the commit and date they were taken at.

## Documentation

Current and maintained as part of the recovery:

- `docs/product/vision.md` — purpose, audiences, anti-goals. Owner-endorsed; it separates what is
  shipped from what is intended, and tags each claim with how it was established.
- `docs/product/current-state.md` — where the rewrite stands.
- `docs/product/roadmap.md` — the current bet list, stated as intent rather than dates.
- `docs/product/metrics.md` — dated measurements and the documentation-truth guardrail.
- `docs/oracle/ORACLE.md` and `docs/oracle/known-divergences.md` — the rewrite's rules and its
  accepted divergences.

Subsystem detail lives in `docs/architecture/` and `docs/config-schemas/`. Those have not been
reconciled against the tree; the concepts are useful, but treat specific filenames, paths and
numbers there as unverified until you check them.

## License

MIT. See `LICENSE` — Copyright (c) 2025 John.
