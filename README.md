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
  repository's only tags, locally and on `origin`, are the two oracle tags below —
  `oracle-2026-08-13` (`0e875d7a`) and `oracle-2026-08-17` (`4222a917`).
- **`main` carries the recovery.** The 168 commits of the `project-recovery` rewrite were merged
  through PR #32 (merge commit `07b26ed5`) on 2026-08-15, after both of the merge gates it was
  held behind were satisfied — CI restoration, and a claim-by-claim re-verification of this file.
  Before that merge, `main`'s tip was dated 2025-11-28 and described a system that no longer
  existed. A second merge landed through PR #35 at `4222a917` on 2026-08-16, carrying the
  `slow`-marker deletion and the integration-test repairs; the nightly on `main` has been green
  ever since (see [Continuous integration](#continuous-integration)). Repair continues on a
  `project-recovery*` branch and reaches `main` only through the same gates, so between merges
  `main` trails the branch by design — it is the last state that passed both gates, not the newest
  state.
- The project is mid **strangler rewrite behind a pinned oracle**. Tag `oracle-2026-08-17`
  (commit `4222a917`, the tip of `main` after the second merge) freezes the previous system as
  the specification for preserved behaviour; it superseded `oracle-2026-08-13` (`0e875d7a`) on
  2026-08-17, which stays as history. From `docs/oracle/ORACLE.md`: "The oracle never
  mutates" — it moves *forward* to a new tag, never edits the old one — and "a diff against the
  oracle is a defect in the rebuild unless the register says otherwise." Accepted differences
  are recorded in `docs/oracle/known-divergences.md`.
- **CI runs, and all three per-push gates are green at `da7d3f7e`** — the last commit CI had
  reported on when this file was stamped, read at 2026-08-19T18:05Z. A commit cannot report on itself:
  the commit carrying this file is pushed after it is written, so its own runs land afterwards.
  Lint, Config Validation and Tests fire on every push, and that has been true since 2026-08-15
  and not before; across the recovery branches, 162 of 177 completed runs passed.
  Since `a725bf66` the default suite deselects nothing: the `slow` marker that had kept 31 red
  integration tests out of every per-push gate is deleted, 29 of them are repaired and 2 deleted
  as dead, and the Tests job runs the whole suite.
  Read this as young rather than settled: before 2026-08-15 nothing had run on the recovery at
  all, nothing had passed anywhere since 2025-11-28, and the Lint gate has since spent seven
  consecutive pushes red without being noticed. See
  [Continuous integration](#continuous-integration).
- Where this file calls something shipped, it means *present and wired*, not mature. The project
  came out of a long stretch of intermittent attention and is unfinished in places; the specific
  gaps are under [Known rough edges](#known-rough-edges).
- No backwards compatibility: no fallbacks, no deprecation cycle, no migration paths. Breaking
  changes land directly.

*Every command, file path, count and quotation below was executed or read against the working tree
at commit `da7d3f7e`; the repository-state facts under [Continuous integration](#continuous-integration)
were read from the GitHub API at 2026-08-19T18:05Z. Dates here are UTC, which is why the second merge is
dated 2026-08-16 although its commit carries 2026-08-17 in local time. This is the **fourth** full
claim-by-claim re-verification of this file. The first (`1b25c99d`) found **ten claims stale in a
single day**, every one because the recovery had fixed the thing being described; the second
(`33bfff51`, at the first merge) found five more in four commits; the third (`905acd96`, at the
second merge) found twenty-one in 27; this one found **eighteen stale or misleading claims and
four material omissions in 43 commits**, itemised in the `docs/product/` decision record
that accompanies this commit. Two of those came from the gate finding its own blind spots: the CI
gate had been red for seven consecutive pushes while this file called it green, and a defect
described here as afflicting one pack turned out to be a class affecting any pack that declares an
agent-profile variable. **The adversarial half of the method also found ten factual defects in the
sweep's own corrections before they were applied** — which is the argument for the method over a
re-read, and the reason a sweep that finds nothing is treated here as a sweep that was not run.
There are deliberately no test counts, coverage percentages, observation widths or
training-performance figures here — see [Numbers](#numbers). **This file decays fast because the
project moves fast**: it is a status report stamped at a commit, not a standing description, and
it is re-verified by sweep — not by re-reading — whenever it is published.*

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
  environment.yaml      # meter observation types (range_type), VFS variables, cascade graph
  actions.yaml          # substrate and custom actions, action labels
  brain.yaml            # architecture, optimizer, loss, Q-learning, replay
  items.yaml  effects.yaml  vfs_profiles.yaml
  presentation.yaml     # optional; rendering hints for the live viewer — never compiled
  levels/<level>/
    curriculum.yaml     # vision and temporal switches
    bars.yaml           # meters, bounds, cascades
    affordances.yaml    # interactions (interaction_type required), costs, hours, placement
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

Three declarations are worth knowing about because older docs predate them. Each meter's
observation type is declared per meter as `range_type` in `environment.yaml` — a closed,
parameterized vocabulary of nine normalization kinds (`minmax`, `log_scaled`, `zscore`, …); the
shipped pack uses `minmax` with `clip: false` for all eight. Each `environment.yaml` variable
declares a `semantic_type` from a closed vocabulary, and each affordance declares its
`interaction_type` (`instant`, `multi_tick` or `dual`) — required, no default. And a pack may carry
an optional `presentation.yaml` at its root: the live-inference server reads it to render meters and
affordances (labels, colours, icons, plain/percent/currency formats), the compiler never does, so it enters no hash and
cannot change behaviour (`src/townlet/demo/presentation.py`, `docs/config-schemas/presentation.md`).
No shipped pack carries one; without it the viewer renders every meter honestly from its declared
bounds — a bar as a fraction of the declared range, the plain value, no `%` or `$` inferred from a
name.

**About the shipped curriculum, since older docs oversell it.** `default_curriculum` declares five
levels, but `bars.yaml`, `affordances.yaml` and `drive.yaml` are byte-identical across all five,
and the substrate is pack-level. Only two levels change the world the agent sees:
`L2_partial_observability` (`active_vision: partial`) and `L3_temporal_mechanics`
(`active_temporal: true`, `day_length: 24`). Compiling all five and comparing artifacts,
`observation_schema_hash` takes exactly three distinct values — one shared by L0_0, L0_5 and L1,
one for L2, one for L3. Five level directories, three distinct observation surfaces. Within the
first group, `L0_5_dual_resource` and `L1_full_observability` differ, outside comments, in one
line of one file (`output_subdir`), and `L0_0_minimal` differs from them in training hyperparameters — the
double-DQN flag, target-update frequency, batch size, intrinsic-annealing floor, episode budget
and checkpoint interval — and in enabling one fewer custom action (`REST` only, against `REST` and
`MEDITATE`) — which does move its `action_schema_hash` and `vfs_hash`.

## Install

Python 3.13 or newer (`.python-version` pins 3.13) and [uv](https://docs.astral.sh/uv/). A GPU is
optional; the runtime falls back to CPU.

```bash
git clone https://github.com/foundryside-dev/hamlet
cd hamlet
uv sync --all-extras
```

No branch checkout is needed: `main` carries the recovery. Ongoing repair lands on a
`project-recovery*` branch first and reaches `main` only through the merge gates, so `main` trails
active work by design — it is the last state that passed both gates, not the newest state.

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
worktree at the oracle tag under `.oracle/` (checking on reuse that it sits at the tag's commit and
is clean), runs the same logical pack, level, seed, agent count and step count on both trees as
subprocesses — each side is a (code root, pack root) pair: the oracle side reads its frozen copies
of the packs under `oracle_fixtures/`, the rebuild side reads the live `configs/` — and compares
the env-step traces (observations, rewards, dones) plus the compiled provenance hashes. Verdicts
and a `report.json` land under `runs/differential/<run-id>/`; a `--cell` names both device rows of
a pack/level, so this prints two verdicts:

```bash
uv run python -m townlet.oracle.harness --cell default_curriculum:L0_0_minimal
```

Its declared matrix is twenty cells: five levels of `default_curriculum` × {cpu, cuda}, three
single-axis packs under `configs/differential/` × {cpu, cuda}, and two packs whose
`vfs_profiles.yaml` declares variables (`configs/test/items_smoke`, `configs/test/effects_smoke`)
× {cpu, cuda} — the only runnable packs that expose VFS profile variables, added so the cut that
split the old `obs_vfs` block into per-variable fields (`PDR-0075`, register entry `DIV-006`) was
visible to the harness at all. The CUDA cells
are always declared and reported SKIPPED rather than silently dropped when `--cuda` is absent. It
exits 0 only when every cell is AGREE, SKIPPED, or DIVERGED_AS_REGISTERED — the last meaning the
cell's declared binding to a divergence-register entry matched narrowly, in one of two shapes.
*Old-side crash*: the oracle side crashed without producing a trace, the registered signature
appearing in the final exception text of its stderr, *and* the rebuild side ran and produced a
valid trace. *Hash-only*: both sides ran, exactly the enumerated provenance hashes differ — no more
and no fewer — and every trace stream matches byte-for-byte. Behaviour is never suppressed: any
stream difference is DIVERGE, an undeclared hash moving is HASH_MISMATCH, and a declared divergence
that fails to manifest is REGISTERED_DIVERGENCE_ABSENT — all red. An unmatched red of any kind
still fails, and an empty or all-SKIPPED run exits 1 so that doing nothing cannot look green.
**At `oracle-2026-08-17` the sixteen `default_curriculum` and differential cells declare no
divergence and their frozen fixtures under `oracle_fixtures/` are byte copies of the live packs**,
so for them a green run means *old and new agree* — the first time since 2026-08-15 that exit 0 has
meant that. (Between 2026-08-15 and the re-tag, all ten standing cells bound the hash-only entry
`DIV-004` and AGREE was unreachable; the register records that as a cost, and its dissolution as
the reason the tag moved.) The four profile-variable cells bind `DIV-006`, the first entry written against the
new tag. All four declare the hash-only shape, permitting and requiring exactly
`observation_schema_hash`, `variable_schema_hash` and `vfs_hash` to move. The two
`configs/test/effects_smoke` cells additionally declare an *input* divergence under the same entry:
the cut requires `semantic_type` on global and agent profile variables, their frozen fixture is
held at the pre-cut schema, and the live pack differs from it by exactly that one key. A declared
input delta and a declared output delta are two separate decisions, and neither blesses the other. The register holds six entries, in its own lifecycle vocabulary: `DIV-001` and `DIV-002` are
checkpoint-boundary, `tag-stamped` at the new tag, and cannot appear in an env-step trace;
`DIV-003`, `DIV-004` and `DIV-005` are `retired` at it; `DIV-006` is `built`. The harness treats any DIVERGE or HASH_MISMATCH with no matched entry as a
rebuild defect or a missing register entry — both findings.

### Checks, run locally

```bash
uv run ruff check .
uv run black --check src tests
uv run mypy src/townlet --show-error-codes
uv run python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt
uv run python scripts/validate_compiler_cli.py
uv run pytest
cd frontend && npm test          # vitest; local only — no workflow runs it
```

`uv run pytest` runs the whole suite: since `a725bf66` there is no `slow` marker and no `-m` in
`addopts`, so the default command deselects nothing. The frontend gate exists as of `a5cca764` —
`frontend/package.json` had never been in the repository before that commit.

## Continuous integration

Four GitHub Actions workflows exist, all specifying `uv sync --all-extras` on Python 3.13: Lint,
Config Validation, Tests, and Full Test Suite.

**Three of the four run on every push, and 162 of the 177 completed runs on the
recovery branches have passed** (read from the GitHub API at 2026-08-19T18:05Z). That became true on
2026-08-15 and had never been true before: between 2025-11-28 and that date no workflow had run
against the recovery at all — the 168 commits it merged in PR #32 landed across only seven pushed
shas, all on 2026-08-15, and nothing before them was checked. 57 shas have been checked in
all across `project-recovery` and `project-recovery-2` — treat the gates as restored, not as
seasoned.

- Lint, Config Validation and Tests trigger on `push` to `main` and to `project-recovery*` (and
  on `pull_request`). The glob is deliberate: the original defect was that the recovery branch
  simply was not named in the trigger list, so naming the *next* branch individually would have
  rebuilt the same trap on the next rename. The first runs in the recovery's history were green —
  Lint 1m11s, Config Validation 1m14s, Tests 24m21s. Of the 177 completed runs since,
  15 have failed: thirteen Lint and two Tests. Twelve of the Lint reds were `ruff`
  line-length violations in trial probe scripts under `configs/` — one of which stood red for
  seven consecutive pushes before a merge gate caught it, having twice been reported green in the
  meantime; the thirteenth was the no-defaults linter at `8c5fa2c8`, on product source
  (`environment/observation_encoder.py`), not on an experiment artefact. The two Tests reds were
  the wall-clock ratio flake at `bf0f2fe4` (run 31870278368), which passed on the same code at the
  neighbouring commits, and a hosted-runner communication loss at `e65f59e1` (run 32269773738).
  **No red has been a product regression** — but do not read that as "only lint and
  infrastructure": one was a real gate catching real product source, and one hid in plain sight
  for seven pushes.
- **The Tests job now runs the whole suite.** Until `a725bf66` the default `pytest` invocation
  carried `-m "not slow"`, and the `slow` marker covered four files — three of them holding 31
  tests that had been failing unseen (`test_temporal_mechanics.py`, `test_training_loop.py`,
  `test_recurrent_networks.py`): some broken by the recovery's own constructor and layout
  changes, some already stale on `main` before it began (the temporal file asserted `Bed`/`Job`
  against a pack that named `SLEEP`/`WORK` at `f0a9ae8a`). No per-push gate had ever run them;
  the first post-merge nightly was what surfaced the red. Of the 31, 29 were repaired and 2
  deleted as dead (`2ba1f530`, `e62a5e4a`), the marker was deleted, and the per-push Tests job
  now executes the rest — every Tests run since `a725bf66` has deselected nothing.
- Full Test Suite — the same suite on a nightly trigger — had its nightly 06:00 UTC cron **deleted during the
  recovery and restored at the 2026-08-15 merge**. The reason is worth knowing, because it is a
  property of GitHub rather than of this repo: the scheduler reads the workflow file from the
  **default** branch, so while the recovery lived on a branch, an enabled cron would have kept
  testing a `main` frozen at `f0a9ae8a`, ~160 commits behind the branch. That workflow has never
  passed — every scheduled run since 2025-11-03 was red, the last 64 of them (2025-11-28 to
  2026-01-30) against an untouched `main` — until GitHub's dormancy rule disabled it; re-enabling
  it from the branch would only have resumed that stream against the wrong tree. The workflow is
  `active` again, and it now passes. It fired twice against `main` at `07b26ed5` and was red both
  times, with the same 31 failures — the tests above, which that `main` still deselected from every
  other gate and had not yet repaired. Since the second merge carried the marker deletion and the
  repairs to `main` at `4222a917`, every run has been green: a `workflow_dispatch` on 2026-08-17
  (run 31981122221) and the three scheduled runs since (runs 32003077539, 32107696959 and
  32224227011, on 2026-08-17, -08-18 and -08-19). Those readings are all against `4222a917`; the
  merge that carries this file puts commits on `main` that the nightly has never run against, so
  the first nightly after it is the next reading to check. Since `a725bf66` the nightly and the
  per-push Tests job are the same bare `uv run pytest` and differ only in trigger.
- Three of the four — every one except Lint — run `scripts/validate_compiler_cli.py` before their
  other steps, and no step sets `continue-on-error`, so that script gates the rest. It exits 0,
  sweeping every pack it does not explicitly exclude. Read the exclusions, because one of them
  matters: `EXCLUDED_DIRS` names `templates`, `aspatial_test` and `reference_config`, and only
  `aspatial_test` exists — the other two are dead names. So `configs/aspatial_test`, one of the
  packs this file names as a working non-Town universe, is **never validated by CI**. It does
  validate by hand (exit 0), which is how the claim below is supported; it is simply not gated.

What CI does not cover, stated so the green is not read as wider than it is: the harness that
adjudicates the rewrite (`townlet.oracle.harness`) is run locally by the operator, not in CI; the
frontend's `npm test` and `npm run build` run locally only — no workflow installs Node; and two
members of the default suite — wall-clock ratio assertions (a 5% VFS-overhead ratio and a 1.5×
scripted-kernel ratio) taken under always-on coverage instrumentation — are flaky by
construction; one of them is the `bf0f2fe4` red above. Tracked as one defect
(`hamlet-f9090ec3e8`).

## Architecture at a glance

`src/townlet/` is the only source tree — there is no `src/hamlet/` — and holds 16 packages. The
load-bearing ones:

- **`universe/` — the universe compiler (UAC).** Parses and cross-validates a pack, resolves its
  references and shared schemas, compiles every level, and emits one `CompiledUniverse`: a frozen
  dataclass carrying 16 declared `*_hash` fields plus per-level metadata *(update 2026-08-24:
  now 17 — `pack_brain_hash` landed 2026-08-22, PDR-0027)*. Not all of them are
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
  serving path (`demo/live_inference.py`). Eight of the `*_hash` fields are stamped into a
  checkpoint *(update 2026-08-24: nine, with `pack_brain_hash` — stamped and required present,
  compared only to state a brain-lineage fork, PDR-0027)*, and seven of those are hard-compared
  on load — `vfs_hash`, `drive_hash`, the
  effective `brain_hash`, and the four per-level content hashes — alongside observation dim, action
  count, observation-field UUIDs and `primary_level`, so a checkpoint refuses to load into a
  universe it does not match, including a different level of the same pack. What is *not* enforced
  is recorded rather than hidden: `observation_schema_hash` is stamped and never compared, and the
  five pack-level hashes (`experiment`, `stratum`, `environment`, `actions`, `items`) are computed
  and serialized and compared by no checkpoint consumer — only the differential harness reads
  them, as a provenance diff between two compiles — `DIV-001` in
  `docs/oracle/known-divergences.md`.
- **`oracle/` — the differential harness** described above.
- **`demo/` — training runner and live-inference server.** The server is the only reader of the
  optional `presentation.yaml` (`demo/presentation.py`, DTO in `config/presentation_config.py`):
  it validates the file against the compiled universe's meter and affordance names at startup
  and raises `PresentationError` on an unknown one, forwards each meter's declared bounds and
  lethal edges to the viewer on connect, and no compiler stage or hash ever sees it.

## Delivered, and intended

Delivered and wired at this commit: a YAML pack compiles to a frozen, hash-carrying artifact
(`configs/default_curriculum` and `configs/L5_multi_agent` both validate clean); that artifact
drives the vectorized torch environment; reward functions are specified in config, with no Python
reward classes left to subclass; VFS access control is enforced at runtime; and the training entry
point runs end to end, writing a run directory whose `training.log` records *Training loop completed
normally* beside a `config_snapshot/` of the pack that produced it.

Intent, not yet built — stated plainly because older docs blur the line:

- **Brain-as-code layers 1 and 3.** The behaviour contract (panic thresholds, forbidden actions,
  personality dials, allowed goals) and the declarative think-loop graph are specified in
  `docs/architecture/archive/hld/02-brain-as-code.md` (archived 2026-08-24; the current honest
  treatment is `docs/architecture/BAC.md`) and have no implementation: their identifiers appear
  in zero files under `src/` and `configs/`. Layer 2, the network/optimizer/loss surface, is real.
- **One standard compiler for both halves of an experiment.** The universe compiles to an artifact;
  the brain rides inside it as a validated `BrainConfig` plus a `brain_hash`, rather than compiling
  to an artifact of its own. `CompiledBrain` exists only in `docs/`.
- **A second demonstrator that varies the domain rather than the substrate.** The substrate axis
  has a measured witness (Trial 001, above). `docs/product/vision.md` names four existing packs as
  domain-varying candidates of unverified depth (`aspatial_test`, `L5_multi_agent`, `simple`,
  `reference` — the pack is `reference/model_pack`). All four validate clean at this commit;
  whether any varies the *domain* enough to count as a witness is unassessed, and that — not the
  compile status — is the open question.
- **The "Low Energy Delirium" reward-hacking lesson** described in older docs. It is not
  implemented: no level of the shipped curriculum declares the multiplicative reward the lesson
  depends on.

## Known rough edges

- **The frontend builds and has a test gate, but the gate is local only.** `frontend/package.json`
  and its lockfile were restored at `a5cca764` — before that commit neither had ever been in the
  repository, so `npm run dev` could not run although `scripts/run_demo.py --help` told you to.
  Now `npm run build` succeeds and `npm test` runs the vitest suite (three files under
  `frontend/src/`); no CI workflow installs Node or runs either. One component is dead code: `AffordanceGraph.vue` is
  mounted behind an `affordance_graph` message that no server emits (`hamlet-102db4c2e0`).
- **A compiled pack can fail to cache without failing the command, and it is a class of failure
  rather than one pack.** *(Fixed 2026-08-21, commit `03764c6b` — agent profiles now serialize,
  the field is typed `CompiledGlobalProfile | None`, and a failed cache write fails the compile.
  Re-verified 2026-08-24: a pack with a non-null `agent_profile` compiles and writes its cache
  artifact. The record below is kept as stamped at 2026-08-20.)*
  `configs/reference/model_pack` compiles, prints `Compilation succeeded`,
  and exits 0 — while its cache artifact is *not* written: serialization raises `can not serialize
  'CompiledGlobalProfile' object`, the failure is downgraded to a log warning the CLI never
  displays, and nothing propagates it to the exit code. `inspect` then fails with `Artifact not
  found`. The trigger is a **non-empty `agent_profile.variables`** in a pack's `vfs_profiles.yaml`:
  packs declaring zero agent-profile variables cache normally, packs declaring one or more do not,
  and adding a single agent-profile variable to a pack that caches is enough to reproduce it. The
  error names the *global* class because `universe/compiled.py:123` types the field as
  `agent_profile: Any | None = None  # TODO: Add CompiledAgentProfile type` — the untyped field is
  the root cause, and the message points at the wrong half of the config. Compiling every pack in
  `configs/` from a cleared cache, exactly two fail this way today. CI cannot see any of it,
  because the gate runs `validate`, which writes no cache. This is the project's recurring shape —
  a failure that is not loud — and it is tracked as a defect rather than left as folklore.
  (`configs/` holds 33 directories carrying an `experiment.yaml`; 15 are fixtures under
  `configs/test/`, three of which the script declares expected-to-fail; the other 18 are
  `default_curriculum`, `L5_multi_agent`, `aspatial_test`, `simple`, `reference/model_pack`, three
  `differential/div003_*` harness packs, and ten authoring-trial packs — two `trial002_*` and eight
  `trial_*` — written for the trials recorded in `docs/product/metrics.md` and
  `docs/product/trials/`. The two packs that used to fail at parse on schema drift,
  `configs/simple` and `configs/reference/model_pack`, were repaired on 2026-08-15 and both
  validate clean.)
- **The declarable surface exceeds the exercised surface.** Measured at this commit by compiling
  all 30 packs in `configs/` that compile — every pack except the three negative fixtures — and
  counting rules in-process:
  - Two of the nine compiled transition-program families — `action_write` and `social_residue` —
    carry zero rules in every one of them. `action_write` is worse than unexercised: no YAML can
    produce one, because `universe/compilers/actions.py` hardcodes `writes=()` for every action.
    (A third, `interaction_progress`, was also empty everywhere until 2026-08-15; repairing
    `configs/reference/model_pack` brought the only pack that exercises it back into the measured
    set, where it carries two progress rules and two completion-bonus rules — still the only pack
    in `configs/` that produces any, after ten trial packs were added to the sample. The surface
    did not change — the sample did.)
  - `drive.yaml`'s `intrinsic.strategy` accepts `icm` and `count_based`, which have no
    implementation anywhere — those tokens occur only inside `config/drive_as_code.py`, in the
    `Literal`, its docstring and an unread `icm_config` field. `composition.normalize` and
    `composition.clip` validate but have no reader; `dac_engine.py` takes only `log_components`
    and `log_modifiers` from that block.
  - `type: grid3d` was deleted from the substrate schema (it never had a
    `SubstrateFactory.build` branch, so it could only compile toward a guaranteed crash); 3-D
    grids are `type: grid` with `topology: cubic`.
  - Three of the nine declared variable scopes — `zone`, `group` and `message` — validate and
    compile clean and then hard-crash at environment construction. `VariableRegistry` sizes them
    from `num_zones` / `num_groups` / `num_message_slots`, constructor parameters that default to 0
    and that `environment/vectorized_env.py` never passes, so `_positive_extent` raises for any
    pack that declares one; no YAML or DTO can set them either. Unit tests *do* cover the registry
    in isolation — they pass the extents directly, and pin both the working path and the raise —
    so the suite is green while the scopes remain unreachable from every real pack. (`affordance`
    scope works, because `num_affordances` *is* passed.) Measured in the authoring trials recorded
    under `docs/product/trials/`.
  - The four VFS variables `configs/default_curriculum/environment.yaml` used to declare —
    `deficit_energy`, `deficit_satiation`, `time_since_last_eat`, `time_since_last_sleep` — were
    observed but written by nothing, so agents saw frozen zeros in slots the ABI claimed were
    live. Deleted 2026-08-22 (`hamlet-dc8f887cd5`); the shipped pack now declares no custom
    variables. Trial L (`docs/product/trials/0001/L-20260818.md`) demonstrated the counter
    mechanic is authorable without them: a bar with a negative passive rate advances per tick,
    an `on_start` `modify` resets it on use.
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
how the last set went wrong: the README that sat on `main` until the 2026-08-15 merge (`f0a9ae8a`)
badged a test count and a coverage percentage and stated an observation width; `docs/product/metrics.md`
records that coverage figure as measured-false, and the width it gave is not what the compiler
reports for any `default_curriculum` level at this commit. Read them off the tree instead: compile a level and read
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
- `docs/product/decisions/` — every product decision as a numbered record with its reversal
  trigger; `docs/product/prds/` and `docs/product/trials/` hold the authoring-trial instrument and
  the per-trial records this file cites for measured authorability claims.
- `docs/oracle/ORACLE.md` and `docs/oracle/known-divergences.md` — the rewrite's rules and its
  accepted divergences.

Subsystem detail lives in `docs/architecture/` and `docs/config-schemas/`. *(Updated
2026-08-24, PDR-0118:)* the old architecture corpus — including
`docs/architecture/archive/UNIVERSE_AS_CODE.md` (corrected 2026-08-16) and
`docs/architecture/archive/vfs-current-implementation.md` (corrected then and again on
2026-08-17, when the compiled observation field gained a typed `feature`) — was archived
wholesale to `docs/architecture/archive/` and replaced by a six-document HLD set reviewed
against source on 2026-08-24: `HLD.md`, `STRATA.md`, `UAC.md`, `BAC.md`, `COMPILER.md`, and
`VFS.md` (the former `vfs.md`, promoted). Treat the archive as history, never as a record of
what shipped; `docs/config-schemas/presentation.md` is source-verified, and the rest of
`docs/config-schemas/` is per-surface reference (its `variables.md` is stale, 2025-11).

## License

MIT. See `LICENSE` — Copyright (c) 2025 John.
