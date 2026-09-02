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
  `slow`-marker deletion and the integration-test repairs; a third through PR #36 at
  `04062872` on 2026-08-19 (41 commits: the blind re-run instrument, protocol Appendices
  A.6.1/B, and a re-verification of this file); and a fourth through PR #37 at `9efadd3c` on
  2026-08-29 — the token-set observation ABI, the Lint gate restored, and this file re-verified
  again. `git rev-list --count 04062872..9efadd3c^2` gives 146 commits for that fourth merge;
  the PR title says 143, which is `04062872..1065dbf0` — the difference is the stamp commit
  (`6fb148fd`), a product checkpoint (`5f3817c1`) and a content-empty back-merge of `main`
  (`1b4020aa`). The nightly on `main` has been green since the second merge — seventeen
  consecutive runs to 2026-09-01, the last four against `9efadd3c` (see
  [Continuous integration](#continuous-integration)). Repair continues on a
  `project-recovery*` branch and reaches `main` only through the same gates, so between merges
  `main` trails the branch by design — it is the last state that passed both gates, not the newest
  state. The unit-3 token cut described below **is on `main`** as of `9efadd3c`; whether any
  later cut has reached `main` is answered by
  `git fetch && git log origin/main -1 -- <file>`, not by this file — and note the `origin/`:
  a stale local `main` ref answers wrongly (at this stamp the local ref still sat at `04062872`).
- The project is mid **strangler rewrite behind a pinned oracle**. Tag `oracle-2026-08-17`
  (commit `4222a917`, the merge commit of PR #35) freezes the previous system as
  the specification for preserved behaviour; it superseded `oracle-2026-08-13` (`0e875d7a`) on
  2026-08-16 (UTC — the tag name carries the local date), which stays as history. From `docs/oracle/ORACLE.md`: "The oracle never
  mutates" — it moves *forward* to a new tag, never edits the old one — and "a diff against the
  oracle is a defect in the rebuild unless the register says otherwise." Accepted differences
  are recorded in `docs/oracle/known-divergences.md` (twelve entries; what a green harness run
  means has changed since the 2026-08-26 token cut — see [Run something](#run-something)).
- **CI runs, and all three per-push gates are green at `1eb347f7`** — the commit this file was
  stamped against, with Lint, Config Validation and Tests all `completed` / `success` when read
  at 2026-09-02T04:52Z. A commit cannot report on itself: the commit carrying this file is
  pushed after it is written, so its own runs land afterwards.
  Lint, Config Validation and Tests fire on every push, and that has been true since 2026-08-15
  and not before; across the recovery branches, 362 of 435 completed runs have passed (read
  2026-09-02T04:55Z).
  Since `a725bf66` the default suite deselects nothing: the `slow` marker that had kept 31 red
  integration tests out of every per-push gate is deleted, 29 of them are repaired and 2 deleted
  as dead, and the Tests job runs the whole suite.
  Read this as young rather than settled: before 2026-08-15 nothing had run on the recovery at
  all, nothing had passed anywhere since 2025-11-28, and the Lint gate has twice gone red for a
  stretch that nobody watching noticed — seven pushes on 2026-08-19, then **47 consecutive
  pushes, 2026-08-22 to 2026-08-29**, while the product workspace recorded the branch as green
  (`docs/product/current-state.md`, 2026-08-26). Both were caught by a re-verification, not by
  the gate. Every one of the 63 runs on `project-recovery-3` (21 pushed shas to `1eb347f7`)
  has passed — no red at all, like the original `project-recovery` before it (24 runs on 7
  shas in one day, 2026-08-15, all green); only `project-recovery-2` ever went red. See
  [Continuous integration](#continuous-integration).
- Where this file calls something shipped, it means *present and wired*, not mature. The project
  came out of a long stretch of intermittent attention and is unfinished in places; the specific
  gaps are under [Known rough edges](#known-rough-edges).
- No backwards compatibility: no fallbacks, no deprecation cycle, no migration paths. Breaking
  changes land directly, and deleted surface is deleted — `observation_mode`, nine trial packs
  and the 4,090-wide fixed observation projection all went this way since the last stamp (see
  below), none behind a warning.

*Every command, file path, count and quotation below was executed or read against the working tree
at commit `1eb347f7` (2026-09-02, with Lint, Config Validation and Tests all green on it);
the repository-state facts under [Continuous integration](#continuous-integration)
were read from the GitHub API at 2026-09-02T04:55Z. Dates here are UTC, which is why the second
merge is dated 2026-08-16 although its commit carries 2026-08-17 in local time. This file is
written on a recovery branch and is re-verified claim by claim before it reaches `main`. This is
the **sixth** full re-verification of it. The first (`1b25c99d`) found **ten claims stale in a
single day**, every one because the recovery had fixed the thing being described; the second
(`33bfff51`, at the first merge) found five more in four commits; the third (`905acd96`, at the
second merge) found twenty-one in 27; the fourth (`4a225d84`, at the third merge) found eighteen
and four omissions in 43, and its adversarial pass found ten factual defects in the sweep's own
corrections before they were applied; the fifth (`6fb148fd`, at the fourth merge) covered 143
commits and found 33 stale, wrong or misleading claims and sixteen material omissions, its
adversarial pass six defects in the draft's corrections — which is the argument for the method
over a re-read, and the reason a sweep that finds nothing is treated here as a sweep that was not
run. This one covers **39 commits** (`git log --oneline 1065dbf0..1eb347f7 | wc -l`) and found
**29 stale, wrong or misleading claims and nineteen material omissions**, most of them because
the token-recovery milestones the previous stamp described as open had closed.
There are no test counts, coverage percentages or learning-curve figures here; the observation
widths and the one qualification reading it does quote are readings of versioned artifacts,
each named with the commit it was read at — see [Numbers](#numbers). **This file decays fast
because the project moves fast**: it is a status report stamped at a commit, not a standing
description, and it is re-verified by sweep — not by re-reading — whenever it is published.*

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

      diagonals: true

  vision_support: both

  temporal_support: enabled
```

Position encoding has no selector. Coordinates are normalized to `[0, 1]` and egocentric deltas
to `[-1, 1]` on every spatial substrate; the `observation_encoding` and `observation_mode` keys
are deleted from the schema (`b7fc3951`, `94656527`; `PDR-0133`, `PDR-0143`), and a pack that
still declares either fails validation as an extra field.

Nothing else defines the substrate. The grid is 8×8 for every level in the pack: `stratum.yaml`
exists only at pack root, and the level loader reads no substrate file from a level directory.
Replacing that `substrate` block re-substrates the same experiment. The measured case is recorded
as Trial 001 in `docs/product/metrics.md`: the survival pack was moved to a 6-dimensional
`gridnd` world by editing about six lines of `stratum.yaml`, with zero lines changed under
`src/townlet/` — it compiled, reset and stepped, the movement vocabulary auto-expanded to
`DIM0_NEG … DIM5_POS`, and the entire domain carried over. Partial observation preserves each
compiled universe's token layout on every substrate: the runtime passes `vision_range` to
`substrate.visible()` and zeroes the presence and payload of out-of-range spatial tokens. GridND
therefore needs no spatial tensor allocation to run the pack's POMDP levels.

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
  stratum.yaml          # substrate and topology — nothing about observation encoding
  environment.yaml      # meter observation types (range_type), VFS variables, cascade graph
  actions.yaml          # substrate and custom actions, action labels
  brain.yaml            # architecture, optimizer, loss, Q-learning, replay
  items.yaml  effects.yaml  vfs_profiles.yaml
  transition_rules.yaml variables_reference.yaml action_labels.yaml   # optional, compiled
  presentation.yaml     # optional; rendering hints for the live viewer — never compiled
  levels/<level>/
    curriculum.yaml     # vision and temporal switches
    bars.yaml           # meters, bounds, cascades
    affordances.yaml    # interactions (interaction_type required), costs, hours, placement
    drive.yaml          # reward specification
    training.yaml       # hyperparameters, enabled actions
    brain.yaml          # optional; a COMPLETE replacement brain, never a partial patch
```

A level directory carries those five required files plus two optional ones: an `items.yaml`
declaring level-scoped item spawns, and — since `d60104f0` (2026-08-22, `PDR-0027`) — a
complete `brain.yaml` that forks the whole brain for that level (one pack does:
`configs/test/token_set_smoke`); the loader (`src/townlet/universe/raw_configs_v21.py`) reads
nothing else from it. The shared catalogs `vfs_profiles.yaml` and `effects.yaml` are rejected
outright at level scope, and a level `items.yaml` must declare the v1.0 ItemsAppearance schema
(`src/townlet/universe/loaders/preflight.py`). Without a level `brain.yaml` the architecture
is pack-level: a level's `training.yaml` overrides exactly five scalars of the pack `brain.yaml`
— gamma, target-update frequency, the double-DQN flag, learning rate and replay capacity — and
none of them live in the `architecture` block. Of the optional pack-root files,
`transition_rules.yaml` (typed social-residue rules, `7e989e8c`) is carried by no pack in
`configs/`; `variables_reference.yaml`, where a pack declares the `extents` that size its
`zone`, `group` and `message` scopes, by thirteen (`find configs -name variables_reference.yaml`;
it was twenty before the nine trial packs were deleted at `5973f79b`).

Three declarations are worth knowing about because older docs predate them. Each meter's
observation type is declared per meter as `range_type` in `environment.yaml` — a closed,
parameterized vocabulary of four bounded, fixed-two-lane transforms: clipped `minmax`, clipped
`log_scaled`, `cyclical_sin_cos`, and `binary`. The declaration drives both the live meter-token
value and its static identity; range bounds come from the matching `bars.yaml` meter rather than
being restated, and `clip` on the two clipped kinds is `Literal[True]` — a meter value entering
a token is bounded by declaration, not by a flag. Normalization kinds that are unbounded,
batch-coupled or need more than two lanes are deleted from the meter surface, not mapped or
retained as compatibility aliases (`PDR-0134`; the DTO in `config/environment_config.py`
admits exactly those four members). Each `environment.yaml` variable
declares a `semantic_type` from a closed vocabulary, and each affordance declares its
`interaction_type` (`instant` or `multi_tick`) — required, no default. `instant` has no duration
and admits only immediate costs/`on_start` writes; `multi_tick` requires duration and admits only
per-tick costs/`per_tick`/`on_completion` writes. The old `dual` spelling is deleted because it
never executed both behaviours (`PDR-0135`). And a pack may carry
an optional `presentation.yaml` at its root: the live-inference server reads it to render meters and
affordances (labels, colours, icons, plain/percent/currency formats), the compiler never does, so it enters no hash and
cannot change behaviour (`src/townlet/demo/presentation.py`,
`docs/config-schemas/presentation.md` — archived 2026-08-24, back at the live path since
`931e26d8` on 2026-08-26, the only file in that directory that opens with no banner of any kind).
No shipped pack carries one; without it the viewer renders every meter honestly from its declared
bounds — a bar as a fraction of the declared range, the plain value, no `%` or `$` inferred from a
name.

**About the shipped curriculum, since older docs oversell it.** `default_curriculum` declares five
levels, but `bars.yaml`, `affordances.yaml` and `drive.yaml` are byte-identical across all five,
and the substrate is pack-level. Only two levels change the world the agent sees:
`L2_partial_observability` (`active_vision: partial`, `vision_range: 0.5`) and
`L3_temporal_mechanics` (`active_temporal: true`, `day_length: 24`). **Corrected 2026-08-26 at
the unit-3 token cut:** this paragraph used to say `observation_schema_hash` took three distinct
values across the five levels — one shared by L0_0/L0_5/L1, one for L2, one for L3 — and read
that as "three distinct observation surfaces". It now takes **exactly one**: compiling all five
gives an identical `observation_schema_hash`, `layout_hash`, `token_type_schema_hash` and
`total_dims` (re-measured at `1eb347f7`). The compiled observation surface is the same at every
level. Partial observability is a **runtime visibility filter** over an unchanged TokenSpec
(out-of-range spatial tokens have presence and payload zeroed), not a compiled difference; and
the day/night phase is an authored global in the pack-root `vfs_profiles.yaml` — `day_phase`,
`expression: tick`, `initial_value: 0.0`, `exposed_to: [agent]`, `cyclical_sin_cos` with
`period: 24` — so every level carries it *and observes it*, as one cyclical token, `active_temporal`
or not (`430eb5af`, `PDR-0143`). So the "five documented levels are three distinct universes"
reading — still true of the *mechanics* — is no longer visible in the observation artifact at
all, and a level's distinguishing feature has to be looked for in `curriculum.yaml`, not in a
hash. Within the first group, `L0_5_dual_resource` and `L1_full_observability` differ, outside
comments, in one line of one file (`output_subdir`), and `L0_0_minimal` differs from them in
training hyperparameters — the double-DQN flag, target-update frequency, batch size,
intrinsic-annealing floor, episode budget and checkpoint interval — and in enabling one fewer
custom action (`REST` only, against `REST` and `MEDITATE`) — which does move its
`action_schema_hash` and `vfs_hash`.

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
`default_curriculum` level sets it to its own directory name). The runner writes
`checkpoints/` with `.sha256` sidecars, `metrics.db`, `tensorboard/`, `training.log`, and a
`config_snapshot/` of the configuration that produced them (`demo/unified_server.py`,
`demo/runner.py`, `training/checkpoint_utils.py`).

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
four env-step trace streams (`obs`, `actions`, `dones`, `rewards`; trace format v4 added
`actions` as an adjudicated stream, `9e7197e6`) plus the compiled provenance hashes. Each side
draws its own seeded actions by default; `--scripted` makes the oracle side record its actions
and the rebuild side replay them verbatim, so the world's dynamics are compared under identical
inputs. Verdicts and a `report.json` land under `runs/differential/<run-id>/`; a `--cell` names
both device rows of a pack/level, so this prints two verdicts:

```bash
uv run python -m townlet.oracle.harness --cell default_curriculum:L0_0_minimal
```

Its declared matrix is twenty cells: five levels of `default_curriculum` × {cpu, cuda}, three
single-axis packs under `configs/differential/` × {cpu, cuda}, and two packs whose
`vfs_profiles.yaml` declares variables (`configs/test/items_smoke`, `configs/test/effects_smoke`)
× {cpu, cuda} — originally the only runnable packs that exposed VFS profile variables, added
under `PDR-0074` so the cut that split the old `obs_vfs` block was visible to the harness at
all. The CUDA cells
are always declared and reported SKIPPED rather than silently dropped when `--cuda` is absent. It
exits 0 only when every cell is AGREE, SKIPPED, or DIVERGED_AS_REGISTERED — the last meaning the
cell's declared binding to a divergence-register entry matched narrowly, in one of three shapes.
*Old-side crash*: the oracle side crashed without producing a trace, the registered signature
appearing in the final exception text of its stderr, *and* the rebuild side ran and produced a
valid trace. *Hash-only*: both sides ran, exactly the enumerated provenance hashes differ — no more
and no fewer — and every trace stream matches byte-for-byte. *Stream-scoped* (`afa09b81`,
2026-08-22, built for the token cut): both sides ran, exactly the enumerated trace streams
diverge — shape changes included — and every other stream matches byte-for-byte. A cell may bind
a hash entry and a stream entry together; `compare_traces` labels that `hash+stream`. Behaviour
is never suppressed: an undeclared stream difference is DIVERGE, an undeclared hash moving is
HASH_MISMATCH, and a declared divergence that fails to manifest is REGISTERED_DIVERGENCE_ABSENT
— all red. An unmatched red of any kind
still fails, and an empty or all-SKIPPED run exits 1 so that doing nothing cannot look green.
**What exit 0 means has changed since `oracle-2026-08-17`.** At the re-tag, the sixteen
`default_curriculum` and differential cells declared nothing and their fixtures were byte copies
of the live packs, so a green run meant *old and new agree*. That is no longer true — the
`matrix.py` docstring says so in those words. Since the token cut was bound on 2026-08-26
(`7b432de3`) and `DIV-012` on 2026-09-02 (`b3120870`), **every one of the twenty cells binds
four register entries** — `DIV-009` (six pre-cut compiler landings that moved provenance, not
behaviour), `DIV-010` (the engine `tick` variable), `DIV-012` (four hash movers surfaced by the
`day_phase` run and bisected one by one: `stratum_hash` to the `observation_mode` deletion at
`94656527`, `affordances_hash` and `environment_hash` to the meter-normalization cut at
`c6c6b524`, `brain_hash` to the compact-replay cut at `d554fb7f`; the four profile cells bind a
three-field variant because `affordances_hash` does not move on those two packs — measured, not
assumed), and `DIV-008` (the token cut, bound twice: as a hash entry naming five fields and as
the stream entry naming `obs` alone). Entries may overlap on a field where two causes genuinely
move one hash, but the union of every bound entry's fields must equal the observed movers
exactly, and each entry's own fields must all move. A green run now means *everything diverged
exactly as registered*: `obs` is permitted and required to differ on every cell, and `actions`,
`dones` and `rewards` — undeclared — are held byte-exact, which is what makes the token design's
acceptance criterion machine-checked rather than argued. The token cut's acceptance runs,
`runs/differential/20260826-172349` (`--scripted`) and `20260826-172441` (plain), both exit 0;
the current full-matrix adjudication is `runs/differential/20260902-100802`, taken at
`430eb5af` (`report.json` → `meta.new_commit`), twelve commits before this stamp and not re-run
at `1eb347f7` (exit 0: ten CPU cells `DIVERGED_AS_REGISTERED` naming `DIV-009`, `DIV-010`,
`DIV-012` and `DIV-008`; ten CUDA cells SKIPPED, so the finding is CPU-only). Fixtures are no longer byte copies either
(`diff -rq oracle_fixtures/configs/<pack> configs/<pack>`): every one of the six harness packs
now differs on `environment.yaml` (`clip: false → true` on every meter, `c6c6b524`),
`stratum.yaml` (the deleted encoding keys, `b7fc3951` / `94656527`) and `vfs_profiles.yaml`
(the authored `day_phase` global, `430eb5af`); `default_curriculum` and `div003_cubic_partial`
also differ in the comments of their L2 `curriculum.yaml`; the two profile packs also differ on
`effects.yaml`, and `items_smoke` on a stray `substrate.yaml` no loader reads and on a
fixture-only level `brain.yaml` (`DIV-007`). A declared input delta and a declared output delta
remain two decisions, and neither blesses the other. The vacuous `div003_scaled` cell was
replaced by `boundary_wrap`, which exercises a live boundary-semantics axis; `items_smoke`
remains demoted as evidence under `PDR-0124` and its tracker work.
The register holds twelve entries, in its own lifecycle vocabulary: `DIV-001` and `DIV-002`
are checkpoint-boundary, `tag-stamped`, and cannot appear in an env-step trace; `DIV-003`,
`DIV-004` and `DIV-005` are `retired` at the tag; `DIV-006` and `DIV-011` are `retired` into
`DIV-008`; `DIV-007`, `DIV-008`, `DIV-009`, `DIV-010` and `DIV-012` are `built`. Any DIVERGE or
HASH_MISMATCH with no matched entry is a rebuild defect or a missing register entry — both
findings.

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

**Three of the four run on every push, and 362 of the 435 completed runs on the
recovery branches have passed** (read from the GitHub API at 2026-09-02T04:55Z). That became true on
2026-08-15 and had never been true before: between 2025-11-28 and that date no workflow had run
against the recovery at all — the 168 commits it merged in PR #32 landed across only seven pushed
shas, all on 2026-08-15, and nothing before them was checked. 140 shas have been checked in
all across `project-recovery` (7), `project-recovery-2` (112) and `project-recovery-3` (21) —
treat the gates as restored, not as seasoned. The one gap the previous stamp left open on
`main` itself — the third merge, `04062872`, triggered **no** per-push Lint, Tests or Config
Validation run there — was decided by the next merge, as promised: the fourth, `9efadd3c`,
fired all three within two seconds of merging (runs 33245264384, 33245264401, 33245264455,
2026-08-29T09:20:33Z), all green, and `hamlet-83c8e3b50e` closed as `not_a_bug` (`PDR-0130`).
`04062872` remains the only merge commit on `main` with no per-push read; its nine nightlies
were green.

- Lint, Config Validation and Tests trigger on `push` to `main` and to `project-recovery*` (and
  on `pull_request`). The glob is deliberate: the original defect was that the recovery branch
  simply was not named in the trigger list, so naming the *next* branch individually would have
  rebuilt the same trap on the next rename. The first runs in the recovery's history were green —
  Lint 1m11s, Config Validation 1m14s, Tests 24m21s. Of the 435 completed runs since,
  73 have failed: 60 Lint, 13 Tests, and no Config Validation — and none of the 73 is on
  `project-recovery-3`. The Lint reds come in two
  streaks. The first, thirteen through 2026-08-19, was mostly `ruff` line-length violations in
  trial probe scripts — one stood red for seven consecutive pushes before a merge gate caught
  it — plus the no-defaults linter once at `8c5fa2c8`, on product source. The second is the one
  to read: **Lint was red for 47 consecutive pushes**, from `7dc6f66c` (2026-08-22) to
  `237b0c38` (2026-08-29), last green before it `0b659130` (2026-08-21). Three steps took
  turns being the red one — the no-defaults linter, Black (64 files) and `ruff` — and because
  the workflow runs `ruff` → Black → mypy → no-defaults and stops at the first failure, each
  red hid whatever was broken behind it. Fixed in two commits: `237b0c38` blacked the 64 files;
  `b915139e` made three real defaults required (`TokenTypeSchema.slot_bindings`,
  `owner_capacity`, `source_map`) and whitelisted the fifteen structural hits (eleven whitelist
  entries) with their reasons in `.defaults-whitelist.txt`. No Lint run has failed since.
  The thirteen Tests reds, every one on `project-recovery-2`: the
  wall-clock ratio flake at `bf0f2fe4`, a
  hosted-runner loss at `e65f59e1`, two 2026-08-22 runs where
  `test_masked_loss_during_training` completed no episode (`11c80a94`, `c9c1d50e`; passing
  again from `ba2766e6`, cause not established), eight consecutive 2026-08-24 runs where a
  test opened `docs/architecture/vfs.md` after its promotion to `VFS.md` (fixed `478ab7ee`),
  and one at `9563dc45` where the pack-freeze guard refused fixture drift no cell declared —
  closed by binding `DIV-008` at `7b432de3`. **No red has been shown to be a product
  regression**, but the 2026-08-22 pair is unexplained rather than cleared, and the honest
  reading of the second Lint streak is that a gate nobody watches is not a gate.
- **The Tests job now runs the whole suite.** Until `a725bf66` the default `pytest` invocation
  carried `-m "not slow"`, and the `slow` marker covered four files — three of them holding 31
  tests that had been failing unseen (`test_temporal_mechanics.py`, `test_training_loop.py`,
  `test_recurrent_networks.py`): some broken by the recovery's own constructor and layout
  changes, some already stale on `main` before it began (the temporal file asserted `Bed`/`Job`
  against a pack that named `SLEEP`/`WORK` at `f0a9ae8a`). No per-push gate had ever run them;
  the first post-merge nightly was what surfaced the red. Of the 31, 29 were repaired and 2
  deleted as dead (`2ba1f530`, `e62a5e4a`), the marker was deleted, and the per-push Tests job
  now executes the rest — every Tests run since `a725bf66` has deselected nothing. Since
  `079ce167` (2026-09-02) the suite also carries a discovery-driven pack smoke test
  (`tests/test_townlet/integration/test_pack_smoke.py`): every pack under `configs/` with a
  `stratum.yaml`, minus the three negative fixtures excluded by name, is compiled, constructed
  with two agents on CPU, reset and stepped four times, with every presence lane checked to be
  0 or 1 at every step and the `agent` token census asserted to be zero (`PDR-0143`).
- Full Test Suite — the same suite on a nightly trigger — had its nightly 06:00 UTC cron **deleted during the
  recovery and restored at the 2026-08-15 merge**. The reason is worth knowing, because it is a
  property of GitHub rather than of this repo: the scheduler reads the workflow file from the
  **default** branch, so while the recovery lived on a branch, an enabled cron would have kept
  testing a `main` frozen at `f0a9ae8a`, ~160 commits behind the branch. That workflow had never
  passed — every scheduled run since 2025-11-03 was red, the last 64 of them (2025-11-28 to
  2026-01-30) against an untouched `main` — until GitHub's dormancy rule disabled it; re-enabling
  it from the branch would only have resumed that stream against the wrong tree. The workflow is
  `active` again, and it now passes. It fired twice against `main` at `07b26ed5` and was red both
  times, with the same 31 failures — the tests above, which that `main` still deselected from every
  other gate and had not yet repaired. Since the second merge carried the marker deletion and the
  repairs to `main` at `4222a917`, every run has been green — seventeen in a row: a
  `workflow_dispatch` on 2026-08-17 (run 31981122221), three scheduled runs against `4222a917`
  (2026-08-17 to -08-19), nine against `04062872`, the third merge, from 2026-08-20 to
  2026-08-28 (runs 32340503178 through 33198018719), and four against `9efadd3c`, the fourth,
  from 2026-08-29 to 2026-09-01 (runs 33251995568, 33308309422, 33392649356, 33500458822).
  The cron is `0 6 * * *`, but the last six runs fired between 11:02Z and 18:09Z — five to
  twelve hours late; the runs are green, the schedule is not what the file says. Each merge puts
  commits on `main` that the nightly has never run against, so the first nightly after any merge
  is always the next reading to check; the fourth merge's first nightly (33251995568, under
  three hours after the merge) was green. Since `a725bf66` the nightly and the
  per-push Tests job are the same bare `uv run pytest` and differ only in trigger.
- Three of the four — every one except Lint — run `scripts/validate_compiler_cli.py` before their
  other steps, and no step sets `continue-on-error`, so that script gates the rest. It exits 0,
  sweeping every pack it does not explicitly exclude. Read the exclusions, because one of them
  matters: `EXCLUDED_DIRS` names `templates`, `aspatial_test` and `reference_config`, and only
  `aspatial_test` exists — the other two are dead names. So `configs/aspatial_test`, one of the
  packs this file names as a working non-Town universe, is **never validated by the Config
  Validation script**. It does validate by hand (exit 0), and since `079ce167` the pack smoke
  test in the Tests job compiles, constructs and steps it on every push — so it is now gated,
  by a different gate than the one whose name says "validation".

What CI does not cover, stated so the green is not read as wider than it is: the harness that
adjudicates the rewrite (`townlet.oracle.harness`) is run locally by the operator, not in CI; the
frontend's `npm test` and `npm run build` run locally only — no workflow installs Node; the
training entry point `scripts/run_demo.py` is not run by any workflow (the pack smoke test
constructs and steps environments, it does not train); and two
members of the default suite — wall-clock ratio assertions (a 5% VFS-overhead ratio and a 1.5×
scripted-kernel ratio) taken under always-on coverage instrumentation — are flaky by
construction; one of them is the `bf0f2fe4` red above. Tracked as one defect
(`hamlet-f9090ec3e8`).

## Architecture at a glance

`src/townlet/` is the only source tree — there is no `src/hamlet/` — and holds 16 packages. The
load-bearing ones:

- **`universe/` — the universe compiler (UAC).** Parses and cross-validates a pack, resolves its
  references and shared schemas, compiles every level, and emits one `CompiledUniverse`: a frozen
  dataclass carrying 19 declared `*_hash` fields — seven on the universe, twelve on each level's
  metadata (16 at `oracle-2026-08-17`; `pack_brain_hash` at `d60104f0` and the two token hashes,
  `token_type_schema_hash` and `layout_hash`, at `a1256837` brought it to 19). Not all of them are
  enforced — see checkpoint identity below. The cache is keyed on a config hash and a provenance id
  (compiler version, git sha, python, torch and pydantic versions), and is discarded when any
  config file's mtime is newer than the artifact's. The 2026-08-24 cleanup (`312d0fe0`,
  `PDR-0121`) gave it one authoritative stage enum (`universe/stages.py`), an error-code
  registry (`universe/error_codes.py`) and a `SourceMap`, so a compile error now carries
  `file:line`; the never-called cues seam (`CuesCompiler`, `config/cues.py`) was deleted. Since
  `cb02851d` (2026-09-02) item commands in `items.yaml` are validated through the same command
  DTO as `effects.yaml`, so a malformed `spawn_effect` or an unknown command key refuses at
  compile time instead of at environment construction.
- **`universe/dto/token_spec.py` — the observation ABI, since the unit-3 token cut
  (`4dde71a2`, 2026-08-26).** An observation is a **set of typed tokens**, not a raster: seven
  engine token types in a fixed order (`self`, `meter`, `affordance`, `agent`, `item`,
  `effect`, `variable_element`), each with a payload width fixed across all universes and a
  per-universe compiled capacity, serialized flat with a presence feature leading every row.
  `environment/token_publishers.py` fills the flat view; partial observability zeroes
  out-of-range spatial tokens and never reshapes the tensor. `token_type_schema_hash` is the
  transfer contract — at `1eb347f7` it takes one value, `8ad2b59b502a905b…`, across all 31
  compiled levels of the 26 non-negative packs in `configs/`, whose `total_dims` run from 19
  (`aspatial_test`) to 474 (`items_smoke`); `layout_hash` is the per-universe flat-net contract.
  Since the milestone-3 compact-replay cut (`d554fb7f`, 2026-08-31, `PDR-0136`)
  `TokenSpec.total_dims` is the sole environment, transition and replay width: the 4,090-wide
  fixed projection and every fixed-observation encoder and reconstruction path are deleted, and a
  runtime/AST test guards against a complete fixed-observation API coming back. The old
  fixed-width superset and its per-level activity mask — `ObservationSpec`,
  `ObservationActivity`, `vfs/observation_builder.py` — are deleted, not wrapped, and so are the
  dead `set_encoder` architecture and `SetEncoderQNetwork`. The `agent` token type has a
  capacity of zero in every compiled level (`census["agent"] == 0`) because nothing declares an
  agent-token surface; the pack smoke test asserts it so that a surface that makes them live has
  to add an exercise (`PDR-0143`).
- **`vfs/` — variables and compiled transition programs (VTC).** Access control
  is enforced at runtime, not merely declared: `VariableRegistry` raises `PermissionError` when a
  reader or writer is not on the variable's list. The compiled transition schedule is built into
  `VectorizedHamletEnv` and drives the ordered phases of the step loop; since `7cbfbff8`
  affordance occupancy is one of its phases, so contention is authorable from `actions.yaml`.
  An exposed expression-backed variable is permitted and must declare an `initial_value`
  (`430eb5af`); the shipped `day_phase` is one.
- **`environment/dac_engine.py` — declarative rewards (DAC),** compiled from a level's `drive.yaml`.
- **`agent/` — brain-as-code, layer 2.** `brain.yaml` selects `feedforward`, `dueling`,
  `token_set`, or token-native `recurrent`, plus optimizer and loss, through
  `network_factory.py`, `optimizer_factory.py` and `loss_factory.py`. `TokenSetQNetwork` and
  `RecurrentTokenQNetwork` share the declared `mean` or `attention` `TokenSetEncoder`. The
  raster recurrent network is gone: since `9d4e942f` (2026-08-31) `RecurrentTokenQNetwork` is the
  only `recurrent` architecture — it folds `[batch, sequence, observation]` into frame batches
  for token encoding, then makes one LSTM call over the pooled sequence before its Q-head — and
  `network_factory.py` was rewritten around it, with `docs/architecture/BAC.md`, `STRATA.md`,
  `VFS.md`, `docs/config-schemas/brain.md` and `docs/manual/pomdp_compatibility_matrix.md`
  rewritten in the same commit.
- **`environment/`, `population/`, `substrate/` — the vectorized torch runtime.** Device is an
  explicit parameter: `VectorizedHamletEnv` requires one and raises rather than picking a default.
- **`training/checkpoint_utils.py` — checkpoint identity.** One shared gate,
  `assert_checkpoint_identity`, called by both the training-resume path (`demo/runner.py`) and the
  serving path (`demo/live_inference.py`). Twelve `*_hash` fields are stamped into a
  checkpoint (`CHECKPOINT_FORMAT_VERSION = 6` at the token-recurrent/shared-encoder cut; a
  version-5 checkpoint refuses loudly), and eight of those are hard-compared on load — `vfs_hash`, `drive_hash`, the
  effective `brain_hash`, the four per-level content hashes, and one of the two token hashes
  chosen by architecture: `token_set` and token-native `recurrent` networks compare
  `token_type_schema_hash`; flat `feedforward` and `dueling` readers compare `layout_hash`, because
  their dims are positional — alongside action
  count and `primary_level`, so a checkpoint refuses to load into a universe it does not match,
  including a different level of the same pack. `pack_brain_hash` is stamped and required
  present but compared only to state a brain-lineage fork (`PDR-0027`); the old observation-dim
  and observation-field-UUID legs are gone with their producer. What is *not* enforced
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
(`configs/default_curriculum` and `configs/L5_multi_agent` both validate clean, and every one of
the 26 non-negative packs in `configs/` compiles, constructs, resets and steps under the
CI-gated pack smoke test); that artifact
drives the vectorized torch environment; the observation is a compiled token set whose
replacement of the raster ABI the oracle harness adjudicated on all ten CPU cells with world
dynamics byte-exact (`PDR-0124`, re-adjudicated with `DIV-012` bound at
`runs/differential/20260902-100802`, taken at `430eb5af`); reward functions are specified in config, with no Python
reward classes left to subclass; VFS access control is enforced at runtime; all nine variable
scopes construct at runtime; temporality is authored and observed (the day/night phase is a
pack-level variable over the engine's `tick`, exposed as one cyclical token, not an engine
block); and the token-recovery programme is closed — `PDR-0132` re-planned it as five
checkpointed milestones, and each is accepted: M1 position encoding (`b7fc3951`, `PDR-0133`),
M2 meter normalization (`c6c6b524`, `PDR-0134`), M3 compact replay (`d554fb7f`, `PDR-0136`),
M4 token regression qualification (`PDR-0141`) and unit 5 (`PDR-0144`), with the umbrella
`hamlet-fa6bb6da4a` closed. The training entry point `scripts/run_demo.py` is wired over the
same `DemoRunner` (`demo/runner.py`) that the M4 instrument drives, but no workflow runs it and
it was not re-run end to end for this stamp; what is asserted here is what CI and the versioned
M4 evidence assert.

The width measurement the cut left open is now closed, not hidden. The token design
(`PDR-0114`) carried a reversal trigger at 8× the pre-cut observation width, and the historical
L1 artifact compiled to `total_dims` 1132 against a pre-cut 120 — **9.43×**, costing 863.6 MiB
per 100,000 replay observation pairs. `PDR-0131` superseded the carry-debt ruling in `PDR-0126`:
immutable declaration context leaves replay rather than waiting for pack migration. The
1,580-float and 4,090-float readings the previous stamp quoted were intermediate: 4,090 was
the fixed projection the compact-replay cut deleted (`d554fb7f`, `PDR-0136`), not a width any
tensor carries. At `1eb347f7` the full L1 serialization is **118 floats** — census `self` 1,
`meter` 8, `affordance` 14, `agent` 0, `item` 2, `effect` 0, `variable_element` 1, the one
`variable_element` being `day_phase` (115 before it was exposed). At 100,000 float32
observation pairs that is 94,400,000 bytes, or 90.03 MiB — 34.7× below the deleted
4,090-wide projection's 3,120.4 MiB, and two floats narrower than the pre-cut raster's 120. Read it off the tree
rather than trusting this paragraph: `token_spec.total_dims` and `token_spec.census` on the
compiled level, as under [Numbers](#numbers).

M4 is the one training reading this file quotes, because it is versioned. It is a deterministic
engineering qualification, not a statistical study (`PDR-0137`): four cells —
`token_feedforward` and `token_recurrent`, each with the `mean` and the `attention` aggregator —
were trained by `scripts/l2_token_regression.py`, which drives `DemoRunner` on
`default_curriculum` `L2_partial_observability` with each of the four templates in
`configs/benchmarks/l2_token_regression/brain_templates/` installed as the level `brain.yaml`,
on training seed 45 to a requested budget of 2,278,640 live-agent steps under a
stop-before-vector-step rule, and scored on greedy mean survival against an acceptance floor of
79.19466666666668 — 0.8 × the frozen L2 pre-raster baseline's inter-quartile mean (`PDR-0122`).
All four passed — 98.9925, 99.0, 97.315 and 99.0 — and `summary.json` records
`all_cells_passed: true` (`PDR-0141`). The evidence is versioned at
`docs/product/baselines/2026-09-m4-token-regression/` with a `PIN` naming `git_sha`
`9d4e942f` (the `*.json`/`*.csv` ignores were negated for that directory at `8047b68c`), so the
numbers here can be checked against the file rather than against memory. Running the
qualification also surfaced a P1 it did not fold in: see [Known rough edges](#known-rough-edges).

Intent, not yet built — stated plainly because older docs blur the line:

- **Brain-as-code layers 1 and 3.** The behaviour contract (panic thresholds, forbidden actions,
  personality dials, allowed goals) and the declarative think-loop graph are specified in
  `docs/architecture/archive/hld/02-brain-as-code.md` (archived 2026-08-24; the current honest
  treatment is `docs/architecture/BAC.md`) and have no implementation: their identifiers appear
  in zero files under `src/` and `configs/`. Layer 2, the network/optimizer/loss surface, is real,
  and the token cut includes both feedforward `TokenSetQNetwork` and recurrent
  `RecurrentTokenQNetwork` architectures. Both share the same per-type `TokenSetEncoder`; the
  recurrent network feeds its pooled frame sequence through one LSTM call before the Q-head.
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

- **Fifteen P1 bugs are unresolved at this stamp, all in `triage`** (`filigree list --type bug
  -p 1 --status triage`, read 2026-09-02 at `1eb347f7`; most are WS-4 authorability gaps filed
  by the trials and the VFS audit). **The two filed by the milestone work that found them:**
  `hamlet-d6fc84d147` (2026-09-01): `VectorizedHamletEnv.step` increments `step_counts` for
  dead agents as well as live ones, so the per-agent `survival_time` written to `metrics.db`,
  TensorBoard's `Episode/Survival_Time`, the curriculum tracker and the `l2_baseline` curves
  all read as the batch episode length and overstate per-agent survival; `PDR-0140` filed it
  rather than folding it into M4, whose acceptance evidence comes from the persisted counter
  instead. `hamlet-4b931faaf4` (2026-09-02): a held or exclusive item is invisible to the
  entire `item` token type — `ItemManager.lift_item` pops the row out of `active_items`, and
  `held_items` has no observation reader — so a carried item's presence, coordinates and
  item-arena state never reach the observation; the fix will move `layout_hash` (`PDR-0144`).
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
  error names the *global* class because `universe/compiled.py` (then line 123) typed the field as
  `agent_profile: Any | None = None  # TODO: Add CompiledAgentProfile type` — the untyped field is
  the root cause, and the message points at the wrong half of the config. Compiling every pack in
  `configs/` from a cleared cache, exactly two fail this way today. CI cannot see any of it,
  because the gate runs `validate`, which writes no cache. This is the project's recurring shape —
  a failure that is not loud — and it is tracked as a defect rather than left as folklore.
  (Pack census at `1eb347f7`, `find configs -name experiment.yaml`: `configs/` holds 29
  directories carrying an `experiment.yaml` and 34 levels between them. 19 are fixtures under
  `configs/test/`, three of them declared expected-to-fail (`vfs_circular_dependency`,
  `vfs_type_mismatch`, `vfs_undefined_var`); three are the `differential/` harness packs
  (`boundary_wrap`, `div003_cubic_partial`, `div003_rect`); the other seven are
  `default_curriculum`, `L5_multi_agent`, `aspatial_test`, `simple`, `reference/model_pack`, and
  the two authoring-trial packs promoted to fixtures, `trial002_money_log_gdp` and `trial_k_cold`.
  The other nine trial packs — `trial002_money_int_capped`, `trial_b_blind_organism`,
  `trial_b_organism`, `trial_b_organism_2d`, `trial_f_durability`, `trial_l_cooldown`,
  `trial_m_combo`, `trial_o_bidding`, `trial_o_bidding_blind` — were deleted with their probe
  scripts at `5973f79b` (2026-09-01, `PDR-0142`), because PRD-0001 requires every trial pack to be
  a referenced fixture or gone; the trial records stay in `docs/product/trials/`. All 26
  non-negative packs validate clean and step under the pack smoke test. The `reference/model_pack`
  shape this record used to end on — an `items.yaml` `spawn_effect` the compiler passed and the
  runtime refused, `hamlet-5a87550adb` — is closed: since `cb02851d` item commands validate
  through the effects command DTO at compile time, and the pack constructs and steps.)
- **The declarable surface exceeds the exercised surface.** First measured on 2026-08-20 over
  the 30 packs in `configs/` that then compiled; re-measured at `1eb347f7` by compiling all 31
  levels of the 26 non-negative packs and reading the rule counts off each level's compiled
  `transition_schedule`:
  - Two of the nine compiled transition-program families — `action_write` and `social_residue` —
    carry zero rules in every one of the 31 levels. Both have an authoring surface no shipped
    pack uses: custom actions carry a `writes:` list (`universe/compilers/actions.py` no longer
    hardcodes `writes=()`, which was why `action_write` used to be unproducible), and
    social-residue rules live in a typed pack-root `transition_rules.yaml` (`7e989e8c`); no
    `writes:` key and no `transition_rules.yaml` exists under `configs/`, so by census both
    families are still empty everywhere.
    (A third, `interaction_progress`, was also empty everywhere until 2026-08-15; repairing
    `configs/reference/model_pack` brought the only pack that exercises it into the measured
    set, where it carries two progress rules — at `1eb347f7` still the only level in `configs/`
    whose `interaction_progress_program` has any.)
  - `drive.yaml`'s `intrinsic.strategy` accepts `icm` and `count_based`, which have no
    implementation anywhere — those tokens occur only inside `config/drive_as_code.py`, in the
    `Literal`, its docstring and an unread `icm_config` field. `composition.normalize` and
    `composition.clip` validate but have no reader; `dac_engine.py` takes only `log_components`
    and `log_modifiers` from that block.
  - `type: grid3d` was deleted from the substrate schema (it never had a
    `SubstrateFactory.build` branch, so it could only compile toward a guaranteed crash); 3-D
    grids are `type: grid` with `topology: cubic`.
  - Three of the nine declared variable scopes — `zone`, `group` and `message` — used to validate
    and compile clean and then hard-crash at environment construction, because nothing passed
    the registry its `num_zones` / `num_groups` / `num_message_slots` extents and no YAML could
    set them (found by Trial K, `docs/product/trials/`). **Fixed at `6b752b3c` (2026-08-21,
    `hamlet-9e1ae3b7a2` closed):** a pack declares an `extents:` block in
    `variables_reference.yaml`, the compiler carries it into the level metadata,
    `environment/vectorized_env.py` passes it to the registry, and a pack that declares one of
    those scopes without extents is refused loudly. One pack declares them (`L5_multi_agent`;
    `trial_o_bidding_blind`, the other one, was deleted at `5973f79b`).
  - The four VFS variables `configs/default_curriculum/environment.yaml` used to declare —
    `deficit_energy`, `deficit_satiation`, `time_since_last_eat`, `time_since_last_sleep` — were
    observed but written by nothing, so agents saw frozen zeros in slots the ABI claimed were
    live. Deleted 2026-08-21 (`0b659130`, `hamlet-dc8f887cd5`); the shipped pack declares no custom
    variables in `environment.yaml` (`variables: []`). Trial L
    (`docs/product/trials/0001/L-20260818.md`) demonstrated the counter
    mechanic is authorable without them: a bar with a negative passive rate advances per tick,
    an `on_start` `modify` resets it on use.
- **Nine defects landed open with the token cut** (`PDR-0124`). Since then the two semantic
  regressions — inert `observation_encoding` (`hamlet-6a4a6596bd`) and `range_type` no longer
  reaching the observation (`hamlet-1e335e0363`) — are closed by deletion and rewiring
  (`PDR-0133`, `PDR-0134`, `PDR-0135`), and the `reference/model_pack` construction crash
  (`hamlet-5a87550adb`) is closed at `cb02851d`. Six remain open in triage: item tokens carry no
  declared identity (`hamlet-559cc74246`, P1); the indistinguishability refusal has no
  declared-parameter escape hatch (`hamlet-2aca57c0f0`, P1); effects survive `env.reset()`
  (`hamlet-d76684f549`, P1); affordance tokens get only a duplicate-*name* check where meters and
  variables get `check_indistinguishability` (`hamlet-81bf807963`, P2), although their executable
  costs, hours, lifecycle writes and spawned-effect identity are now compiled into their identity;
  effect slots migrate columns on expiry and over-capacity items drop silently
  (`hamlet-4538ba909f`, P2); and the registry token publisher's `variable_element` slots were
  inert declarations across the fleet (`hamlet-aba6171ff7`, P2) — partly answered, since
  `day_phase` is now a live, exposed `variable_element` in every `default_curriculum` level and
  the effect and item-arena rows are exercised config-in/behaviour-out from the committed
  `effects_smoke` and `items_smoke` packs (`7db18ec9`, `a07b889b`); what the ticket still
  covers is the remaining inert slots elsewhere. A tenth — L3 unobservable after the cut —
  blocked and was fixed first, by declaration (`9563dc45`).
- **Documentation outside `docs/product/` and `docs/oracle/` is being reconciled, and the
  rewrite is blocked.** `scripts/README.md` still documents `scripts/validate_configs.py` and
  `scripts/validate_substrates.py`, neither of which is present; `CLAUDE.md`, regenerated and
  corrected repeatedly, described `CuesCompiler` as "instantiated at `compiler.py:69`" for
  eight days after `bb43e024` deleted it, and said "no workflow has ever run on
  `project-recovery`" for eighteen days after the first green run (observation
  `hamlet-obs-5f1ea6c254`); both lines are corrected in the commit that carries this file. The
  2026-08-24 archive and the 2026-08-26 recovery are under
  [Documentation](#documentation); the corpus rewrite itself is gated on `hamlet-ad2773718a`
  (generate from the consuming code paths, not from the Pydantic models). An independent VFS
  gap analysis (`docs/product/assessments/vfs-gap-analysis-20260821.md`) scored 129 spec cells
  as 63 WORKS / 9 INERT / 26 BLOCKED / 31 ABSENT. The count of confirmed-false claims in
  canonical docs is tracked as a product guardrail in `docs/product/metrics.md`.
- **The recording subsystem is slated for removal** once its intent is captured
  (`pyproject.toml`, `recording` extra; `hamlet-16ae192d42`). Its MP4 export also shells out to
  an `ffmpeg` binary that is not a Python dependency.

## Numbers

This README states no test count, no coverage percentage and no learning-curve figures, and the
observation widths and the one qualification reading it does state are each named with the
commit they were read at (`1eb347f7` and `9d4e942f`). Numbers like those start decaying the
moment they are written, which is how the last set went wrong: the README that sat on `main`
until the 2026-08-15 merge (`f0a9ae8a`) badged a test count and a coverage percentage and stated
an observation width; `docs/product/metrics.md` records that coverage figure as measured-false,
and the width it gave is not what the compiler reports for any `default_curriculum` level at
this commit — nor is the 4,090 the previous stamp of this file gave, which was deleted two
days after it was written. Read them off the tree instead: compile a level and read
`Observation Dim` from the summary (the field is `metadata.observation_dim`, set from
`token_spec.total_dims` — plural — and it is a property of the pack, not a constant of the
project; the attribute was `observation_spec.total_dims` until the 2026-08-26 token cut deleted
that artifact, and `token_spec.census` says where the width goes, type by type); run
`uv run pytest` for the suite; and read `docs/product/metrics.md` for measurements
stamped with the commit and date they were taken at. The trigger denominators live there and in
`docs/product/baselines/`, not here: the frozen L2 pre-raster baseline
(`docs/product/baselines/2026-08-l2-preraster/`, `PDR-0122`, five seeds), the M4 token
regression qualification derived from it (`docs/product/baselines/2026-09-m4-token-regression/`,
`PDR-0141`), and the 9.43× width reading above.

## Documentation

Current and maintained as part of the recovery:

- `docs/product/vision.md` — purpose, audiences, anti-goals. Owner-endorsed; it separates what is
  shipped from what is intended, and tags each claim with how it was established. Re-stamped
  2026-08-24 (`PDR-0119`): the loop ends with the trained model leaving for the designer's
  own game — *train here, deploy there*.
- `docs/product/current-state.md` — where the rewrite stands.
- `docs/product/roadmap.md` — the current bet list, stated as intent rather than dates.
- `docs/product/metrics.md` — dated measurements and the documentation-truth guardrail.
- `docs/product/decisions/` — every product decision as a numbered record with its reversal
  trigger (144 at this stamp, `0001` to `0144`); `docs/product/prds/` and `docs/product/trials/`
  hold the authoring-trial instrument and
  the per-trial records this file cites for measured authorability claims;
  `docs/product/assessments/` holds the independent audits (the VFS gap analysis among them)
  and `docs/product/baselines/` the frozen measurements that arm reversal triggers.
- `docs/oracle/ORACLE.md` and `docs/oracle/known-divergences.md` — the rewrite's rules and its
  accepted divergences.
- `docs/README.md` — the map of the rest of `docs/`, with a trust level per directory.

Subsystem detail lives in `docs/architecture/` and `docs/config-schemas/`. On 2026-08-24
(`PDR-0118`) the old architecture corpus — including
`docs/architecture/archive/UNIVERSE_AS_CODE.md` (corrected 2026-08-16) and
`docs/architecture/archive/vfs-current-implementation.md` (corrected then and again on
2026-08-17, when the compiled observation field gained a typed `feature`) — was archived
wholesale to `docs/architecture/archive/` and replaced by a six-document HLD set reviewed
against source that day: `HLD.md`, `STRATA.md`, `UAC.md`, `BAC.md`, `COMPILER.md`, and
`VFS.md` (the former `vfs.md`, promoted); `BAC.md`, `STRATA.md` and `VFS.md` were rewritten
again at `9d4e942f` for the token LSTM. A same-day recut (`c4e8bd58`, "zzz. archive") then
swept most of the rest of `docs/` — `docs/config-schemas/` included — into `docs/zzz. archive/`
(the literal directory name; 406 markdown files sit there as history). On 2026-08-26
(`PDR-0125`, owner-authorised) 53 files were
recovered to their live paths with 51 dated staleness banners, all thirteen
`docs/config-schemas/` files among them. At `1eb347f7` eleven of the thirteen still open with
their 2026-08-26 banner — eight naming how they are wrong (`variables.md` is wholesale 2025-11
stale; `affordances.md` documents a schema wired to nothing; `expressions.md` calls nine shipped
functions "planned"; `items.md`, `vfs-profiles.md`, `drive_as_code.md`, `effects.md` and
`enabled_actions.md` each name their own defect), three carrying a ✅ (`transition_rules.md`
verified accurate; `bars.md` and `training.md` accurate but for one known error each);
`brain.md` was rewritten at `9d4e942f` and opens with a 2026-08-31 verification note against
`config/brain_config.py` rather than a staleness banner; and only `presentation.md` opens with no
banner at all. Treat both archives as history, never as a record of what shipped.

## License

MIT. See `LICENSE` — Copyright (c) 2025 John.
