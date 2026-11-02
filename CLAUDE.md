# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Townlet is **a rapid DRL experimentation framework for game designers** — a deep
reinforcement-learning substrate expressed as configuration. An environment (variables,
observation layout, substrate topology, affordances, effects, items, reward function) is written
in YAML, compiled into one frozen hash-carrying `CompiledUniverse`, and executed GPU-natively
against torch tensors.

**The point is authoring.** Someone with an idea for a mechanic should be able to turn it into a
running, trainable, reproducible RL environment by writing config — no environment subclass, no
observation-tensor plumbing, no reward-function code. Every subsystem exists to move a category
of "you must write Python for this" into "you can declare this."

**This is the load-bearing judgement call.** When something can only be expressed by editing
Python, that is a product defect, not a shortcut. Prefer declarative surface over engine
special-casing, even when the special case is smaller.

The survival world in `configs/default_curriculum` — eight meters, fourteen affordances, one 8×8
grid — is **the first-class demonstration of the idea, not the product**. Do not harden its
content into the framework.

Repo directory is `hamlet`; the distribution and the only source tree are `townlet`. Same
project. **Work only in `src/townlet/`.**

Fuller framing, and the honest status section: `README.md` (prefer it over anything in
`docs/architecture/archive/`). Product vision: `docs/product/vision.md`.

**Pedagogical value is a property of the framework, not the mission.** The project deliberately
preserves "interesting failures" (like reward hacking) as teaching material rather than
immediately fixing them.

## Current work and binding rulings

**`docs/remediation/STATUS.md` is the handoff and plan for the current remediation** — read it
first when resuming: phase table, open-items register, working method, the full local gate
(§4.3) and the owner rulings (§3). Do not restate it here; update it there.

Rulings that change how you write code, in brief (details in STATUS §3):

- **S1 — the batch is N independent single-agent worlds** (2026-10-25). `global` is per world;
  items, effects, affordance state and RNG are per world. The isolation check is a **world-0
  differential**: two runs that differ only in world 0's actions must leave worlds 1..N-1
  bitwise identical.
- **One spelling per reference.** `x` is a registry variable (read in this world by its declared
  scope), `bar.m` a meter, `item.x` the bound item's state. `tick`, `agent_id`, `self`, `target`,
  the effect locals (`intensity`, `elapsed_ticks`, `duration_remaining`) and the expression
  keywords are reserved. Variable ids follow the expression identifier grammar
  (`[A-Za-z_][A-Za-z0-9_]*`). Every other spelling refuses at compile, naming the one to use.
  Source: `world/expression/references.py`, `vfs/namespace.py`.
- **Hash movement is free.** No trained checkpoints exist. Note moved hashes in the commit
  message; never warn about resume compatibility.
- **No ceremony** (owner, 2026-10-23): refactor directly. Do not write PDRs, evidence receipts or
  divergence-register entries unless the owner asks.

## CRITICAL: Zero backwards compatibility

**Pre-release, zero users, zero downloads. Breaking changes are free — take them.** No fallbacks,
no deprecation warnings, no migration paths, no "support both old and new". If it's old and not
in use, **delete it**; git history preserves it. Old configs should fail loudly, not be
accommodated.

These are antipatterns here, not good practice. Recognise the shape, apply the fix:

| shape | fix |
|---|---|
| `if hasattr(obj, 'old_field')` — old vs new attribute | delete the old path, update references |
| `try/except` catching an old config format | let it raise, update the config, delete the handler |
| version check or feature flag for "legacy support" | delete both the check and the old path |
| field made `Optional` that should be required | make it required, set it explicitly in every config (see No-Defaults Principle) |
| a comment saying "for backwards compatibility" | delete the code and the comment |
| obsolete code kept "just in case" | delete it |

Done correctly before: old observation code deleted outright at VFS integration rather than
dual-pathed; `reward_strategy` removed with its `RewardStrategy` classes when `drive.yaml`
became required; the legacy `src/hamlet/` tree deleted rather than maintained alongside
`src/townlet/`; the `pair`/`message`/`agent_private` scopes deleted at S1 rather than kept
dormant.

## Reading `docs/` — intent vs record

⚠️ **Much of `docs/` is design intent, never a record of what shipped.** The old architecture
corpus lives in `docs/architecture/archive/`; archive-internal links may dangle, by design.

The sharpest case: `docs/architecture/archive/BRAIN_AS_CODE.md` and
`docs/architecture/archive/hld/02-brain-as-code.md` both say
*"Status: Approved for Implementation"*, while `execution_graph` / `cognitive_topology` /
`agent_architecture` return **zero grep hits** in `src/` and `configs/`. The design is the
target; the status line is false. That pattern repeats across the archived corpus.

**Rules:**

1. **Never cite a doc as evidence something is implemented.** Check `src/townlet/` first.
2. **Where a doc disagrees with `README.md`, README is right; where either disagrees with the
   code, the code is right.**
3. `docs/architecture/archive/` does not know about `src/townlet/oracle/`, `items/`, `effects/`,
   S1 or the token observation. Absence there means nothing.
4. Many (not all) files carry frontmatter with an "AI-Friendly Summary" and "Reading Strategy".
   Where present, read it first to decide relevance before opening a 2000-line file.

**Current-and-trustworthy:** `README.md`, `docs/product/`, `docs/remediation/STATUS.md`, the
six-document HLD set in `docs/architecture/` — `HLD.md`, `STRATA.md`, `UAC.md`, `BAC.md`,
`COMPILER.md`, `VFS.md` — and `docs/config-schemas/`. Not
`docs/architecture/archive/vfs-current-implementation.md`: its scope vocabulary, authoring
files and access-control claims all predate Cut B and S1.

**On `docs/config-schemas/`**: the reference tier the HLD set delegates to. Trust a file there
unless it opens with a banner telling you not to. Today `affordances.md` (describes a schema
that is not wired), `effects.md`, `enabled_actions.md` and `items.md` carry warning banners;
`drive_as_code.md` notes that it does not establish every strategy is implemented end to end.
`variables.md` is the canonical authoring contract. The function table in `expressions.md` is
generated by `scripts/gen_expression_functions_doc.py`; a test fails when it drifts.

### The oracle

Tag `oracle-2026-08-17` (`src/townlet/oracle/__init__.py:ORACLE_TAG`; `oracle-2026-08-13`
retained) freezes the pre-rewrite system as a reference for preserved behaviour. See
`docs/oracle/ORACLE.md`. Since 2026-10-23 it is a reference, not a gate: refactor directly, and
do not add to `docs/oracle/known-divergences.md` as a precondition for changing behaviour.
**Never edit anything under `.oracle/`.**

### Universe Compiler (UAC) Quick Reference

- **Source**: `src/townlet/universe/compiler.py`. The pipeline order has one authority,
  `CompilationStage` (`universe/stages.py`): 0 preflight → 1 parse → 2 limits → 3 semantics
  (cross-validate) → 4 symbols → 5 resolve → 6 shared schemas and effects → 7 levels and
  optimization data → 8 emit/cache. Never hand-write "Stage N" strings.
- **Docs**: `docs/architecture/COMPILER.md` (its seven-stage table is a framing; §2 maps it onto
  the source numbering). `docs/architecture/archive/COMPILER_ARCHITECTURE.md` is design-era:
  useful for intent, but it describes sub-compilers that were never wired and asserts a
  backwards-compatibility success criterion this project rejects.
- **Tests**: `uv run pytest tests/test_townlet/unit/universe/` (use `UV_CACHE_DIR=.uv-cache` in sandboxed environments)
- **CLI**: `python -m townlet.universe {compile,inspect,validate}`. CI's Config Validation job
  runs it over every pack via `scripts/validate_compiler_cli.py`.
- **CI** (`.github/workflows/`): Lint, Tests and Config Validation run on push to `main` and
  `project-recovery*`, **and on every pull request**; Full Test Suite runs nightly and on
  dispatch. A push to any other branch (e.g. `fix/*`) gets no CI until a PR is open. A "green"
  claim requires reading every row at the tip SHA (`PDR-0127`).
- **The Lint job** is `ruff check .`, `black --check src tests`, `mypy src/townlet
  --show-error-codes`, and `python scripts/no_defaults_lint.py src/townlet/ --whitelist
  .defaults-whitelist.txt --ratchet .defaults-ratchet`. **The ratchet fails when the
  whitelisted count rises *or falls***: when you remove a default, lower `.defaults-ratchet` to
  the new count in the same commit. The full local pre-commit gate (it also blacks `scripts`,
  runs `gen_expression_functions_doc.py --check`, `validate_compiler_cli.py` and pytest) is
  STATUS §4.3.
- **After a shipped pack's files change**, run `uv run python scripts/regen_frozen_live_inputs.py`
  and commit the inventory diff; a drift test pins those input digests.
- **Merging to `main` is autonomous under `PDR-0101`** once gate 1 (every CI row green at the
  tip) and gate 2 (the `PDR-0039` README re-verification by method) are discharged.
  `.claude/settings.json` allows `gh pr merge`, `gh pr create` and the read-only `gh pr` /
  `gh run` commands; the rules are prefix matches, so run `gh pr merge <n> --merge` as its own
  plain command, never inside a `;` or `&&` compound. Tags, releases and `gh pr close` are
  deliberately not allowed — they escalate to the owner.

### Git hygiene

- **`git stash` is hard-blocked by an operator hook**, even inside a compound command or as
  `git stash list`. Use a WIP commit or a separate worktree.
- **Read `git status --short` before committing.** The index is shared with parallel agents.

## Development Commands

### Setup

```bash
uv sync                                    # Runtime dependencies only
uv sync --extra dev --extra recording      # Development environment
```

**Both extras are required for development.** `mypy src/townlet` type-checks
`src/townlet/recording/`, whose imports (matplotlib, pillow) live in the
`recording` extra. Omitting it produces spurious `import-not-found` errors.
Until the recording subsystem is removed (filigree `hamlet-16ae192d42`), the dev
environment needs both. CI installs `--all-extras`.

### Training (Townlet System)

```bash
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
uv run scripts/run_demo.py --config configs/default_curriculum --level L1_full_observability
```

Levels live under `configs/default_curriculum/levels/` — there are no flat
`configs/<level>/` packs. Live visualization: the `live-inference` skill.

### DemoRunner Context Manager Pattern

`DemoRunner.__init__` compiles the pack and opens the SQLite database and TensorBoard writer;
the environment, population and curriculum are built only inside `run()` (so
`load_checkpoint()` cannot be called on a fresh runner). Use the context manager so those
resources close on every path:

```python
# ✅ GOOD: Guaranteed cleanup
with DemoRunner(config_dir=..., db_path=..., checkpoint_dir=..., level_name="L1_full_observability") as runner:
    runner.run()
    network_weights = runner.population.q_network.state_dict()

# ❌ BAD: DB connection and TensorBoard writer leak if run() is never called or fails in setup
# (run() cleans up itself only once its training loop has started)
runner = DemoRunner(...)
```

`level_name` is required.

## Architecture Overview

### State Representation

**Affordance vocabulary in `default_curriculum`**: EAT, SLEEP, WORK, SHOWER, EXERCISE, SOCIALIZE,
MEDITATE, DRINK_WATER, BRUSH_TEETH, LAUNDRY, COOK, CLEAN_HOUSE, ENTERTAINMENT, DOCTOR —
`affordances.yaml` is byte-identical across all five levels (verified 2026-10-31). Documents that
list a different set (Bed/Job/Hospital…) describe something never shipped.

**Position encoding** (`stratum.yaml`): there is one token position contract: substrate
coordinates are normalized to `[0, 1]`; egocentric deltas use the same per-axis denominator and
land in `[-1, 1]`; both are padded to `MAX_POSITION_RANK` (8, `config/stratum_config.py`).
`observation_encoding` and `observation_mode` are deleted; a config that declares either fails
validation as an extra field (PDR-0143).

**Observation Dimensions** — the observation is **TOKENS**, not a raster. There is no
`ObservationSpec`, no activity mask and no inactive slot: every dim is real, and absence is a
token's own presence feature.

⚠️ **No dimension literal is given here, on purpose** — a written-down width decays. Ask the
compiled artifact; it is the only authority and is correct by construction at every commit:

```python
from townlet.universe.compiler import UniverseCompiler
u = UniverseCompiler().compile(Path("configs/default_curriculum"),
                               primary_level="L1_full_observability")
level = u.get_level("L1_full_observability")
spec = level.token_spec
spec.total_dims      # serialization width of the flat view
spec.census          # {token type: count} — where the width actually goes
spec.row_layout()    # (type, slot, start, end) per row; presence leads each row
level.token_type_schema_hash, level.layout_hash
```

`compile()` requires an explicit `primary_level` — implicit selection raises. Every level's
compiled products live only in `CompiledUniverse.all_levels`; navigate with `get_level(name)`.
There is no `.levels` mapping and no top-level copy of the primary level's products.

**What a TokenSpec is** (spec
`docs/superpowers/specs/2026-08-22-token-observation-representation-design.md` §§1-2): seven
engine token types in a fixed canonical order — `self`, `meter`, `affordance`, `agent`,
`item`, `effect`, `variable_element` — each with a **fixed payload width across all
universes**, and a **per-universe compiled capacity** with deterministic slot bindings.
Content is per-universe; the type system is not. `total_dims = Σ_type capacity × (1 + payload
width)`. Identity is the declared payload applied recursively (a meter is its declared
parameters, an affordance carries its targets' meter signatures), never a name or a slot
index — so two entities identical in every declared parameter are refused at compile time
**when the level's effective brain is a permutation-invariant token encoder** (`token_set`,
`recurrent`); a flat brain (`feedforward`, `dueling`) reads slots by position and compiles
them unchanged (`[TOKEN-IDENTITY]`, S3 ruling 2026-10-25). The check covers exposed variables, observable effects,
and deployed affordances only where tokens carry no position lanes (aspatial): on a spatial
substrate two identical affordances differ by position.

**Two consequences worth holding on to:**

- **`token_type_schema_hash` is the transfer contract, and it must not move.** It starts with
  `de093a6e9f59924e` on every compilable shipped level — measured 2026-10-31 across
  `default_curriculum` (2-D grid), `differential/div003_cubic_partial` (3-D), `aspatial_test`,
  `test/gridnd_4d_pack` and the three `test/token_transfer_*` packs, whose `total_dims` range
  19–152. Any change that moves it is wrong. That is what `MAX_POSITION_RANK` padding buys,
  and why rank-adaptive padding is not a free width saving. `layout_hash` — the flat-net
  contract — moves per universe, as it must.
- **POMDP does not shrink or reshape the tensor**: same `TokenSpec`, same width, same
  `layout_hash`; `vision_range` is handed to `substrate.visible()` and out-of-range spatial
  tokens have presence (and payload) zeroed.

**Action Space**: **composed**, in this order — substrate movement actions (a function of
substrate type *and* declared parameters such as `diagonals`; aspatial has none), then the
substrate's `INTERACT`, then the pack's custom actions from `actions.yaml` in authored order
(`WAIT` is one of these), then engine item actions (`GET`, `USE_SLOT_n`, `DROP_SLOT_n`, item
commands) when the pack has an item arena (`universe/compilers/actions.py`). A custom action may
not reuse a substrate or engine name. Never quote an action-count literal or a fixed index;
ask the compiled artifact (`level.action_metadata`).

**POMDP Support**:

- `active_vision: partial` keeps the compiled `TokenSpec` and flat width unchanged. It passes
  the level's normalized `vision_range` to `substrate.visible()`; spatial token publishers clear
  both presence and payload for entities outside that predicate.
- Grid2D, Grid3D and GridND convert `vision_range` to a discrete radius from the longest axis:
  `max(1, ceil(vision_range * span / 2))`. Continuous and ContinuousND use the corresponding
  world-unit radius without cell quantization. All use the substrate's declared distance metric,
  and `wrap` uses toroidal shortest-path deltas.
- `substrate.egocentric_delta()` supplies bounded entity-minus-observer offsets using the same
  per-axis denominator as normalized positions. Aspatial has no spatial filtering: `visible()`
  returns all true and `egocentric_delta()` returns width-zero deltas.
- `stratum.vision_support` must admit the level's declared `active_vision`; this is a config
  capability check, not a substrate window-capability matrix.

See `docs/architecture/STRATA.md` §7 and `docs/manual/pomdp_compatibility_matrix.md`.

### Variable & Feature System (VFS)

**Status**: in production. VFS is the typed state / observation / transition ABI between UAC and
BAC — not just an observation helper.

**Pipeline**: `YAML Config → Schema Validation → TokenSpec → Runtime Registry + token
publishers → Observations`

**Key Components**:

- `vfs/schema.py`: `VariableScope`, `VariableDef`, `NormalizationSpec`, `WriteSpec`
- `vfs/registry.py`: runtime storage with GPU tensors, access control enforcement
- `vfs/namespace.py` + `world/expression/references.py`: the one reference grammar and the one
  resolver every expression consumer uses (see "One spelling per reference" above)
- `vfs/vtc.py`: VFS Transition Compiler — action writes, passive dynamics, cascades, terminal
  conditions, reward components, occupancy claims
- `vfs/random_draws.py`: counter-based random draws (`uniform`, `normal_dist`) — a pure function
  of seed, episode, tick, site, world and element; no generator state
- `vfs/history.py`: compile side of the temporal operators (`lag`, `delta`, `ema`, …)
- `universe/dto/token_spec.py`: the compiled `TokenSpec` — engine constants, per-type payload
  schemas, capacity derivations, the exposure refusals and the indistinguishability check
- `environment/token_publishers.py`: one publisher per token type; fills the flat view

**Variable Scopes** — four (`VariableScope`): `global`, `agent`, `item`, `affordance`, all
world-local under S1. `pair`, `message`, `group`, `zone` and `agent_private` are deleted until
agents-per-world is declarable. Privacy is `readable_by` / `exposed_to` on an `agent` variable.

**Access Control**: every registry variable declares `readable_by`, `writable_by` and
`exposed_to` in the pack's `variables` declaration. The vocabulary is closed
(`vfs/access_policy.py`): readers `engine`/`agent`, writers `engine` or empty, exposure `agent`,
`engine` always a reader, exposure ⊆ readers. The registry freezes one policy per variable and
checks it in `get()`/`set()`/`set_engine_value()` and the item accessors; the `variable_element`
publisher binds each exposed slot through `authorize_read(reader="agent")`, so an unexposed or
engine-only variable never reaches an observation.

**Which declarations a pack needs** (declaration-store Cut B):

- One required pack-scope `variables:` declaration supplies the explicit registry-variable
  roster and named item-profile groups.
- Every variable declares type, scope, initialization, lifetime, semantic type and access.
  Global/agent expressions and supported item state lower into internal compiled profiles.
- All variables enter the symbol inventory; item identities are profile-qualified. Token bindings
  carry typed scope, which selects the publisher independently of reference-string shape.
- Discovery reads all nested YAML/YML outside `.compiled`; duplicates and unknown declarations
  name actual source locations. Arrays retain their authored order.

**Documentation:** [canonical variables](docs/config-schemas/variables.md),
[declaration discovery](docs/config-schemas/declarations.md),
[expressions](docs/config-schemas/expressions.md), `docs/architecture/VFS.md`.

### Action Space (Composable)

- **Global Vocabulary** (pack-level `actions.yaml`, e.g. `configs/default_curriculum/actions.yaml`):
  all levels in a pack share one action vocabulary. There is no `configs/global_actions.yaml`.
- **Custom Actions** in `default_curriculum`: WAIT, REST (energy recovery), MEDITATE (mood
  boost); a level enables them through `training.yaml: enabled_actions`.
- **Action Labels**: Configurable terminology (gaming, 6dof, cardinal, math presets)

See `docs/config-schemas/enabled_actions.md` (its banner corrects where the vocabulary lives).

## Drive As Code (DAC)

**Status**: in production, runtime-integrated.

**Purpose**: Declarative reward function system for Townlet environments

Drive As Code (DAC) is a declarative reward function compiler that extracts all reward logic from Python into composable YAML configurations. Operators can A/B test reward structures without code changes. DAC compiles YAML specs into GPU-native computation graphs with provenance tracking.

### Key Components

**Declarations**: Each level requires a typed `drive` declaration. Pack versus
`levels/<level>/` determines scope; filenames and additional subfolders are transport.
The following filenames are a readable convention, not compiler dispatch:
```
configs/default_curriculum/
├── experiment.yaml       # experiment name and metadata
├── stratum.yaml          # substrate: grid 8×8, shared by EVERY level
├── environment.yaml      # meter roster, cascade/modulation graphs, affordance vocabulary
├── brain.yaml            # required pack brain; complete level overrides allowed
├── actions.yaml, effects.yaml, items.yaml, variables.yaml
└── levels/<level>/
    ├── bars.yaml
    ├── affordances.yaml
    ├── drive.yaml        # required typed DAC reward declaration
    ├── training.yaml
    └── curriculum.yaml   # vision + temporal switches
```
A declaration may move to `levels/<level>/mechanics/rewards.yml`, or share a multi-document
file with other declarations. Keep the existing `drive:` wrapper: renaming a file does not
change its content vocabulary. Required families are checked after discovery. Catalog fragments
merge in sorted pack-relative path/document order, preserving each authored list's order;
duplicates, even identical ones, refuse with both `file:line` origins.

**Architecture**: Each level's `drive` declaration → compiled by UAC →
executed by `DACEngine` (`src/townlet/environment/dac_engine.py`).

**Formula**:
```
total_reward = extrinsic + (intrinsic × effective_intrinsic_weight) + shaping

where:
    effective_intrinsic_weight = base_weight × modifier₁ × modifier₂ × ...
```

### Components

Modifiers, extrinsic strategies (9), intrinsic strategies (5, including `none`) and shaping
bonuses: the `type`/`strategy` literals in `src/townlet/config/drive_as_code.py` are the
vocabulary. Prose and examples: `docs/config-schemas/drive_as_code.md`.

### Pedagogical Pattern: "Low Energy Delirium" Bug

**Bug**: Multiplicative reward (energy × health) + high intrinsic weight → agents exploit low bars for exploration

⚠️ **THIS CURRICULUM IS NOT IMPLEMENTED.** Re-verified 2026-10-31: `drive.yaml` is
**byte-identical** across all five levels. Each declares `constant_base_with_shaped_bonus` with
`adaptive_rnd` at `base_weight: 0.1`. No shipped level declares a `multiplicative` extrinsic, so
the contrast the lesson depends on does not exist and cannot be demonstrated by running these
packs.

The intended design, for whoever authors it:
- **L0_0_minimal**: should demonstrate the bug (multiplicative, no suppression)
- **L0_5_dual_resource**: should fix it (constant_base_with_shaped_bonus)
- **Comparison**: students learn the importance of reward structure design

### Checkpoint identity

`training/checkpoint_utils.py` (`CHECKPOINT_FORMAT_VERSION = 9`) refuses a resume unless the
checkpoint's hashes match the compiled universe: the seven pack hashes (`PACK_HASH_KEYS`:
experiment, stratum, environment, actions, items, variables, effects), the five level hashes
(`LEVEL_HASH_KEYS`: curriculum, bars, affordances, training, items_appearance), `drive_hash`,
`brain_hash`, and the observation contract — `token_type_schema_hash` for a token brain
(`token_set`, `recurrent`), `layout_hash` for a flat one. A stale format version is refused, not
migrated.

### Q-Learning Algorithm Variants

`training.yaml: q_learning.use_double_dqn` selects vanilla vs Double DQN (it overrides
`brain.yaml`'s value and is covered by `brain_hash`). Recurrent learning keeps the online
current-prefix graph connected and branches each exact stored successor under no-grad.
Double DQN adds an online successor forward per real timestep in each length group
(`VectorizedPopulation._recurrent_predictions`, `population/vectorized.py:675`). Details:
`docs/architecture/BAC.md` §2.5 and `docs/config-schemas/training.md`.

## Configuration System

Training is controlled via YAML config packs in `configs/`. The real pack layout —
pack-level shared files plus `levels/<level>/` overrides, NOT flat `configs/<level>/`
directories — is shown in the DAC "Key Components" section above.

### Active Config Packs (Curriculum)

⚠️ **What follows is the INTENDED curriculum. The shipped configs do not implement it.**
Re-verified by diff 2026-10-31 — the levels live under `configs/default_curriculum/levels/`:

| level | intended | actually shipped |
|---|---|---|
| L0_0_minimal | 3×3 grid, 1 affordance | 8×8, 14 affordances |
| L0_5_dual_resource | 7×7 grid, 4 affordances | 8×8, 14 affordances — `training.yaml` **identical to L1** but for `output_subdir` |
| L1_full_observability | 8×8, 14 affordances | as intended |
| L2_partial_observability | token-filtered POMDP | genuinely differs (`active_vision: partial`) |
| L3_temporal_mechanics | 24-tick day/night | genuinely differs (`active_temporal: true`, `day_length: {period_of: day_phase}` resolves the authored clock period to 24) |

`bars.yaml`, `affordances.yaml` and `drive.yaml` are **byte-identical across all five levels**,
and no level overrides the pack `brain.yaml` (feedforward). Grid size is set once in the
pack-scope `stratum` declaration (8×8) and **no level can override it**.
For active temporal levels, `curriculum.day_length: {period_of: day_phase}` resolves the finite,
positive integral period of the declared global temporal variable derived from ambient `tick`.
An active literal day length duplicating that clock fact is refused; inactive levels keep
`day_length: null`. See [clock references](docs/config-schemas/declarations.md#clock-period-reference).
L0_0/L0_5/L1 differ only in `training.yaml` (hyperparameters, and L0_0 does not enable
MEDITATE); their `curriculum.yaml` files differ only in comments. L2 and L3 reuse L1's
`training.yaml` but for `output_subdir`. Five documented levels are **three distinct universes**.

**Future**: L4 (multi-zone), L5 (multi-agent), L6 (communication). Multi-agent and
communication wait on agents-per-world being declarable (S1); the shipped
`configs/L5_multi_agent` pack runs as N independent single-agent worlds.

### Substrate Types

- `grid`: 2D discrete grid (Grid2DSubstrate) — or 3D with `topology: cubic` (Grid3DSubstrate).
  There is no `grid3d` type.
- `gridnd`: 4D–8D discrete grid (GridNDSubstrate)
- `continuous`: 1D–3D continuous space
- `continuousnd`: 4D–8D continuous space
- `aspatial`: No positioning, pure resource management

Rank is capped at `MAX_POSITION_RANK` (8), the widest position a token carries
(`config/stratum_config.py`).

**Boundary Modes**: clamp (hard walls), wrap (toroidal), bounce (elastic), sticky

**Distance Metrics**: manhattan (L1), euclidean (L2), chebyshev (L∞)

Substrate config examples: the shipped packs (`configs/default_curriculum/stratum.yaml`,
`configs/aspatial_test/`, `configs/test/gridnd_4d_pack/`, `configs/test/action_space/*/`).
There is no `configs/templates/` directory. Schemas: `docs/config-schemas/`. Worked substrate
examples (aspatial, toroidal grid, euclidean distance) and a side-by-side comparison:
`docs/examples/`.

### No-Defaults Principle

**All behavioral parameters must be explicitly specified in config files.** The DTO layer
enforces this, with `ConfigDict(extra="forbid")` so stray keys fail at parse time.

DTOs live in `src/townlet/config/`, one module per declaration family (e.g.
`stratum_config.py` holds `SubstrateConfig`/`StratumConfig`; `training_v2_config.py`,
`bars_v2_config.py`, `affordances_v2_config.py`, `drive_as_code.py`, `variables_config.py`,
`transition_rules_config.py`, …), plus `townlet.environment.action_config.ActionConfig`.
`scripts/no_defaults_lint.py` and its ratchet (see the Lint job above) hold the line.

**Why**: Hidden defaults create non-reproducible configs. Changing code defaults silently breaks old configs.

**Exemptions**: Only metadata (descriptions) and computed values (e.g., observation_dim).

## Network Architecture Selection

`brain.yaml` selects `feedforward`, `dueling`, `token_set`, or `recurrent`. `TokenSetQNetwork`
and `RecurrentTokenQNetwork` share `TokenSetEncoder`: per-type projections and learned type
embeddings followed by the declared `mean` or `attention` aggregator. The recurrent network
folds `[batch, sequence, observation]` into frame batches for token encoding, then makes one LSTM
call over the complete pooled sequence before its Q-head. Observation width and token roster come
only from the compiled artifact; do not write dimension literals here.

- LSTM hidden state resets at episode start, persists during rollout, and observes replay sequence
  and terminal boundaries during training.

**Training Details**:

- Gradient clipping: `clip_grad_norm_(..., max_norm=self.max_grad_norm)` — the threshold is the
  **declared training hyperparameter** `max_grad_norm` in `training.yaml`, not an engine
  constant (`default_curriculum` declares `10.0`).
- Economic balance: WORK pays $22.5 (`bar.money + 22.5`). "Sustainable with proper cycles" has
  **never been measured**; treat it as an intention, not a finding.
- Intrinsic weight annealing is declared in `training.yaml: intrinsic` — variance
  `annealing.threshold`, and a survival gate of `min_survival_fraction × max_steps_per_episode`
  (`default_curriculum`: 100.0 and 0.4 × 1000 = 400 steps).

## Frontend Visualization

See `frontend/CLAUDE.md` (loads automatically when working under `frontend/`).

## Testing Strategy

Tests focus on:

- Environment mechanics (vectorized operations, GPU tensors)
- Population training (batched updates, curriculum progression)
- Exploration (RND novelty, annealing logic)
- Integration (full training loop)
- World isolation (the world-0 differential, S1)

**Do NOT test for "correct" strategies** - emergent behaviors are valuable even if unexpected.

## Development Philosophy

> From game as experience to **writing a game** as experience.

When in doubt:

- **Ask "can a designer express this in a config pack?"** If the answer is "only by editing
  Python", that is the defect worth fixing — not the symptom you were chasing.
- Prefer declarative surface over engine special-casing, even when the special case is smaller.
- **Never branch on a variable's name.** A variable is a name plus declared parameters; the
  compiler and runtime must not know that `money` is money (`PDR-0045`). Behaviour that varies
  per variable comes from a declared parameter, never from what the variable is called. The
  in-tree model: `drive_as_code.py` declares `money_bar: str` as **required, no default** — the
  engine holds the *role*, the author binds the *referent*. Name-based inference is the hardest
  form of this defect to spot, because `if name == "money"` reads as a helpful default rather
  than as a hardcoded domain fact.
- Keep the framework/instance boundary sharp: `default_curriculum` content (its meters,
  affordances, 8×8 grid) is example data, not framework. Do not freeze it into the engine.
- Preserve "interesting failures" as teaching material; document unexpected behaviour rather
  than immediately fixing it.
- The goal is a framework others author in, not production-ready agents.
- **Work only in `src/townlet/`.**

## Filigree Issue Tracker

`filigree` tracks this project's work: `filigree session-context` at session
start, then `filigree start-next-work --assignee <name>`. Name yourself on
writes: `filigree --actor <name>` (CLI) or `actor=<name>` (MCP);
`session-context` also reads `FILIGREE_ACTOR`.

Reference: the **filigree-workflow** skill, `filigree --help`, and the
`mcp__filigree__*` tool schemas. Prefer MCP tools; fall back to the CLI.

Two rules `--help` will not tell you:

1. Claim atomically: `work_start` / `work_start_next` (MCP) or `start-work` /
   `start-next-work` (CLI). Never chain a claim with a separate status update;
   that two-step form races other agents.
2. On `SCHEMA_MISMATCH` the installed filigree is older than the project
   database. Surface it to the user; do not retry.
## Loomweave (code structure + SEI identity)

Loomweave pre-extracts this repo into a queryable map — entities, their
call/reference/import/relation edges, and subsystems — each carrying a Stable
Entity Identity (SEI). Ask its `mcp__loomweave__*` tools, not grep, for "what
calls X", "what subclasses X", "where is X defined", "find the thing that
does Y".

- Never hand-construct an entity id: take it from `entity_find` / `entity_at` /
  `entity_resolve`, and bind cross-tool records on the `sei`, not the `id`.
- If `project_status_get` reports stale, re-index before answering.

Full reference: `loomweave-workflow` skill, `loomweave --help`, MCP schemas.
