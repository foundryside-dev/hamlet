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

Repo directory is `hamlet`; the distribution and the only live source tree are `townlet`. Same
project. **Work only in `src/townlet/`** — `src/hamlet/` is obsolete legacy code.

Fuller framing, and the honest status section: `README.md` (it is current and accurate — prefer
it over anything in `docs/architecture/`). Product vision: `docs/product/vision.md`.

**Pedagogical value is a property of the framework, not the mission.** The project deliberately
preserves "interesting failures" (like reward hacking) as teaching material rather than
immediately fixing them.

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
became required; `src/hamlet/` abandoned rather than maintained alongside `src/townlet/`.

**One exception, and it is not backwards compatibility:** the pinned oracle below. It is a frozen
specification to diff against, never a code path to keep alive.

## Reading `docs/` — intent vs record

⚠️ **Most of `docs/` predates the current recovery work. Treat it as design intent, never as a
record of what shipped.** On 2026-08-24 the old architecture corpus was archived wholesale to
`docs/architecture/archive/` and replaced by a six-document HLD set (PDR-0118); archive-internal
links may dangle, by design.

The sharpest case: `docs/architecture/archive/BRAIN_AS_CODE.md` and
`docs/architecture/archive/hld/02-brain-as-code.md` both say
*"Status: Approved for Implementation"*, while `execution_graph` / `cognitive_topology` /
`agent_architecture` return **zero grep hits** in `src/` and `configs/`. The design is the
target; the status line is false. That pattern repeats across the archived corpus.

**Rules:**

1. **Never cite a doc as evidence something is implemented.** Check `src/townlet/` first.
2. **Where a doc disagrees with `README.md`, README is right.** It is current, honest about
   status, and carries the correct product framing.
3. `docs/architecture/archive/` does not know about `src/townlet/oracle/`, the strangler
   rewrite, `items/`, or `effects/`. Absence there means nothing.
4. Many (not all) files carry frontmatter with an "AI-Friendly Summary" and "Reading Strategy".
   Where present, read it first to decide relevance before opening a 2000-line file.

**Current-and-trustworthy:** `README.md`, `docs/product/`, `docs/oracle/`, the six-document HLD
set in `docs/architecture/` — `HLD.md`, `STRATA.md`, `UAC.md`, `BAC.md`, `COMPILER.md`,
`VFS.md` (all reviewed against source 2026-08-24) — and `docs/config-schemas/`.
`docs/architecture/archive/vfs-current-implementation.md` also remains accurate per the
2026-08-24 audit **except** its access-control and `agent_private` claims.

**On `docs/config-schemas/`** (restored 2026-08-26): the 2026-08-24 recut (commit `c4e8bd58`,
"zzz. archive") swept it into the archive on a fast visual pass, and a follow-up sweep
repointed every citation at the archive path. Both were reversed on 2026-08-26 — it is the
reference tier the HLD set delegates to, and nothing replaced it. It is back at
`docs/config-schemas/` and back on the trustworthy list, **with four exceptions that carry
dated staleness banners of their own**: `variables.md` (2025-11, wholesale stale),
`drive_as_code.md`, `enabled_actions.md`, and `training.md`. Trust a file in that directory
unless it opens with a banner telling you not to.

### The oracle (strangler discipline)

Work is mid **strangler rewrite behind a pinned oracle**. Tag `oracle-2026-08-13` freezes the
previous system as the specification for preserved behaviour. From `docs/oracle/ORACLE.md`:
*"The oracle never mutates"*, and *"a diff against the oracle is a defect in the rebuild unless
the register says otherwise."* Accepted differences are registered in
`docs/oracle/known-divergences.md`. **Never edit anything under `.oracle/`.**

### Universe Compiler (UAC) Quick Reference

- **Source**: `src/townlet/universe/compiler.py` - seven-stage pipeline (parse → symbol table → resolve → cross-validate → metadata → optimization → emit/cache)
- **Docs**: `docs/architecture/COMPILER.md`. `docs/architecture/archive/COMPILER_ARCHITECTURE.md`
  is design-era (2025-11): useful for intent, but it describes sub-compilers that were never wired
  (notably `CuesCompiler`, instantiated at `compiler.py:69` and never called) and asserts a
  backwards-compatibility success criterion this project rejects.
- **Tests**: `uv run pytest tests/test_townlet/unit/universe/` (use `UV_CACHE_DIR=.uv-cache` in sandboxed environments)
- **CLI**: `python -m townlet.universe {compile,inspect,validate}` - wired into CI via
  `.github/workflows/config-validation.yml`. **Caveat: no workflow has ever run on
  `project-recovery`** (filigree `hamlet-2100105c9a`) — the gates that actually hold here are
  run locally, by hand.

## Development Commands

### Setup

```bash
uv sync                                    # Runtime dependencies only
uv sync --extra dev --extra recording      # Development environment
```

**Both extras are required for development.** `mypy src/townlet` type-checks
`src/townlet/recording/`, whose imports (matplotlib, pillow) live in the
`recording` extra. Omitting it produces four spurious `import-not-found` errors.
Until the recording subsystem is removed (filigree `hamlet-16ae192d42`), the dev
environment needs both.

### Training (Townlet System)

```bash
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
uv run scripts/run_demo.py --config configs/default_curriculum --level L1_full_observability
```

Levels live under `configs/default_curriculum/levels/` — there are no flat
`configs/<level>/` packs. Live visualization: the `live-inference` skill.

### DemoRunner Context Manager Pattern

When using `DemoRunner` for checkpoint operations **without running full training**, use context manager for automatic resource cleanup:

```python
# ✅ GOOD: Guaranteed cleanup
with DemoRunner(config_dir=..., db_path=..., checkpoint_dir=...) as runner:
    runner.load_checkpoint()
    network_weights = runner.population.q_network.state_dict()

# ❌ BAD: Resources leak if run() not called
runner = DemoRunner(...)  # Opens DB connections and TensorBoard writers
runner.load_checkpoint()   # Resources stay open indefinitely!
```

## Architecture Overview

### Townlet System (ACTIVE)

**Note**: Work only in `src/townlet/` - hamlet is obsolete legacy code.

### State Representation

**Fixed Affordance Vocabulary**: All curriculum levels observe the same 14 affordances (for
transfer learning), even if not all are deployed. In `default_curriculum` these are EAT, SLEEP,
WORK, SHOWER, EXERCISE, SOCIALIZE, MEDITATE, DRINK_WATER, BRUSH_TEETH, LAUNDRY, COOK,
CLEAN_HOUSE, ENTERTAINMENT, DOCTOR — `affordances.yaml` is byte-identical across all five levels
(verified 2026-08-15). Several `docs/architecture/` documents list a *different* affordance set;
they are wrong, this one is the shipped pack.

**Position encoding** (`stratum.yaml`): `observation_encoding` is deleted. There is one token
position contract: substrate coordinates are normalized to `[0, 1]`; egocentric deltas use the
same per-axis denominator and land in `[-1, 1]`; both are padded to `MAX_POSITION_RANK`. A config
that still declares the old selector fails validation as an extra field. `observation_mode`
belongs to the separate observation-layout surface.

**Observation Dimensions** — the observation is **TOKENS**, not a raster:

⚠️ **The allocated-vs-active superset-plus-activity-mask framing this section used to teach
is DEAD** (unit-3 token cut, DIV-008). `ObservationSpec`, `ObservationField`,
`ObservationActivity`, `curriculum_active` and the per-level activity mask are deleted, not
renamed. **There is no mask and no inactive slot: every dim is real, and absence is a token's
own presence feature.** Do not carry an "allocated vs active" reading into any observation
question.

⚠️ **No dimension literal is given here, on purpose** — the old per-level counts (29 / 54)
were wrong by roughly 4×, which is how a written-down width decays. Ask the compiled artifact;
it is the only authority and is correct by construction at every commit:

```python
from townlet.universe.compiler import UniverseCompiler
u = UniverseCompiler().compile(Path("configs/default_curriculum"),
                               primary_level="L1_full_observability")
spec = u.get_level("L1_full_observability").token_spec
spec.total_dims      # serialization width of the flat view
spec.census          # {token type: count} — where the width actually goes
spec.row_layout()    # (type, slot, start, end) per row; presence leads each row
```

`compile()` requires an explicit `primary_level` — implicit selection raises. `CompiledUniverse`
is single-level by construction (`get_level` / `to_level` / `all_levels` navigate; there is no
`.levels` mapping).

**What a TokenSpec is** (spec
`docs/superpowers/specs/2026-08-22-token-observation-representation-design.md` §§1-2): seven
engine token types in a fixed canonical order — `self`, `meter`, `affordance`, `agent`,
`item`, `effect`, `variable_element` — each with a **fixed payload width across all
universes**, and a **per-universe compiled capacity** with deterministic slot bindings.
Content is per-universe; the type system is not. `total_dims = Σ_type capacity × (1 + payload
width)`. Identity is the declared payload applied recursively (a meter is its declared
parameters, an affordance carries its targets' meter signatures), never a name or a slot
index — so two entities identical in every declared parameter are refused at compile time.

**Two consequences worth holding on to:**

- **Transfer is a property of the type schema, not of the width.**
  `token_type_schema_hash` — the transfer contract — is **identical across a 2-D grid, a 3-D
  cubic grid and an aspatial universe** (measured 2026-08-26: `428982ef5d81dd26` on
  `default_curriculum`, `differential/div003_cubic_partial`, `aspatial_test` and all three
  `token_transfer_*` packs, whose `total_dims` range 162–1132). That is what
  `MAX_POSITION_RANK` padding buys, and why rank-adaptive padding is not a free width saving.
  `layout_hash` — the flat-net contract — moves per universe, as it must.
- **POMDP does not shrink or reshape the tensor**: same `TokenSpec`, same width, same
  `layout_hash`; `vision_range` is handed to `substrate.visible()` and out-of-range spatial
  tokens have presence (and payload) zeroed.

**Action Space** (corrected 2026-08-24 — the per-substrate count table previously here, "Grid2D
8 / Grid3D 10 / GridND(7D) 16 / Aspatial 4", disagreed with source): the action space is
**composed** — substrate movement actions (a function of substrate type *and* declared
parameters such as `diagonals`) plus custom actions from `actions.yaml` — under the canonical
ordering contract of `substrate/base.py`: movement, then `INTERACT` at `[-2]`, then `WAIT` at
`[-1]`; aspatial has no movement actions. Never quote a per-substrate action-count literal; ask
the compiled artifact. See `docs/architecture/STRATA.md` §5.

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

**Purpose**: Declarative state space configuration for observation specs, access control, action
dependencies, and (via VTC) compiled transitions.

**Pipeline** (corrected 2026-08-26 at the token cut): `YAML Config → Schema Validation →
TokenSpec → Runtime Registry + token publishers → Observations`

**Key Components**:

- `schema.py`: VariableDef, NormalizationSpec, WriteSpec (`ObservationField` — the VFS
  observation mirror — was **deleted** at the token cut, along with `VFSObservationSpec` and
  `vfs/observation_builder.py`: the mirror was derived one hop downstream of an
  `ObservationSpec` that no longer exists)
- `registry.py`: Runtime storage with GPU tensors, access control enforcement
- `universe/dto/token_spec.py`: the compiled `TokenSpec` — engine constants, per-type payload
  schemas, capacity derivations, the exposure refusals and the indistinguishability check
- `environment/token_publishers.py`: one publisher per token type; fills the flat view
- `vtc.py`: VFS Transition Compiler — action writes, passive dynamics, cascades, terminal
  conditions, reward components, occupancy claims

**Variable Scopes** — nine, not three (`VariableScope` in `vfs/schema.py`): `global`, `agent`,
`agent_private`, `item`, `pair`, `group`, `affordance`, `zone`, `message`.

**Access Control**: `readable_by` / `writable_by` role lists per variable, enforced at
`registry.get()` / `set()`. Roles are open strings, not a closed enum — `agent`, `engine`,
`actions`, `vtc`, `social_model` are the common ones. ⚠ Caveat (2026-08-24 audit): the
enforcement is real where it runs, but it currently has **no authoring surface** (the compiler
hardcodes the role lists on both required config files) and the observation path bypasses the
checked accessor entirely — see `docs/architecture/VFS.md` §6 caveat and
`docs/architecture/archive/REVIEW-2026-08-24-vfs-implementation-vs-spec.md`.

**Which files a pack needs** (corrected 2026-08-15 — the previous "all packs MUST include
`variables_reference.yaml`" was **false**):

- `vfs_profiles.yaml` — **required**, pack root. Authoritative source for compiled global, agent
  and item profiles. Level directories must NOT contain one.
- `variables_reference.yaml` — **optional** static overlay for non-item variables and observation
  marks. Static only: no expressions, no item-scoped variables. `configs/default_curriculum`
  does not have one; `configs/L5_multi_agent` does.

**Documentation**: `docs/architecture/VFS.md` (the authoritative VFS document, reviewed
2026-08-24), `docs/config-schemas/vfs-profiles.md`,
`docs/config-schemas/variables.md` (⚠ **stale, 2025-11** — restored 2026-08-26 with a
staleness banner; it is the only variables reference we have, but verify against source), and `docs/architecture/archive/vfs-current-implementation.md`
(accurate per the 2026-08-24 audit except its access-control and `agent_private` claims).

### Action Space (Composable)

**Architecture**: Action Space = Substrate Actions + Custom Actions

- **Global Vocabulary** (pack-level `actions.yaml`, e.g. `configs/default_curriculum/actions.yaml`):
  all levels in a pack share one action vocabulary. There is no `configs/global_actions.yaml` —
  that path is dead and several docs still cite it.
- **Custom Actions**: REST (energy recovery), MEDITATE (mood boost)
- **Action Labels**: Configurable terminology (gaming, 6dof, cardinal, math presets)

See `docs/config-schemas/enabled_actions.md` for details (⚠ carries a dated staleness
banner: it still documents the dead `configs/global_actions.yaml` path).

## Drive As Code (DAC)

**Status**: in production, runtime-integrated.

**Purpose**: Declarative reward function system for Townlet environments

Drive As Code (DAC) is a declarative reward function compiler that extracts all reward logic from Python into composable YAML configurations. Operators can A/B test reward structures without code changes. DAC compiles YAML specs into GPU-native computation graphs with provenance tracking.

### Key Components

**Files**: Each level requires `drive.yaml`. The real pack layout is pack-level shared files
plus per-level overrides — **not** a flat `configs/<level>/` directory:
```
configs/default_curriculum/
├── stratum.yaml          # substrate: grid 8×8, shared by EVERY level
├── environment.yaml      # VFS variable definitions, shared
├── brain.yaml            # network architecture, shared (no per-level override exists)
├── actions.yaml, effects.yaml, items.yaml, vfs_profiles.yaml
└── levels/<level>/
    ├── bars.yaml
    ├── affordances.yaml
    ├── drive.yaml        # DAC reward specification (REQUIRED)
    ├── training.yaml
    └── curriculum.yaml   # vision + temporal switches
```
**No file named `drive_as_code.yaml` exists in any shipped pack.** A grep for that filename
returns zero hits and will falsely "confirm" whatever you were checking.

**Architecture**: Reward logic lives in each level's `drive.yaml` → compiled by UAC →
executed by `DACEngine` (`src/townlet/environment/dac_engine.py`). RewardStrategy classes
fully removed. Checkpoint provenance via `drive_hash` (SHA256 of the compiled DAC config).

**Formula**:
```
total_reward = extrinsic + (intrinsic × effective_intrinsic_weight) + shaping

where:
    effective_intrinsic_weight = base_weight × modifier₁ × modifier₂ × ...
```

### Components

Modifier, extrinsic (9 types), intrinsic (5 types), and shaping (11 types) vocabularies:
see `docs/config-schemas/drive_as_code.md` (⚠ carries a dated staleness banner: it names
the file `drive_as_code.yaml`, which does not exist — the real file is `drive.yaml`).

### Pedagogical Pattern: "Low Energy Delirium" Bug

**Bug**: Multiplicative reward (energy × health) + high intrinsic weight → agents exploit low bars for exploration

⚠️ **THIS CURRICULUM IS NOT IMPLEMENTED.** Verified 2026-08-12: `L0_0_minimal/drive.yaml` and
`L0_5_dual_resource/drive.yaml` are **byte-identical**. Both declare
`constant_base_with_shaped_bonus` with `adaptive_rnd` at `base_weight: 0.1`. No shipped level
declares a `multiplicative` extrinsic, so the contrast the lesson depends on does not exist and
cannot be demonstrated by running these packs.

The intended design, for whoever authors it:
- **L0_0_minimal**: should demonstrate the bug (multiplicative, no suppression)
- **L0_5_dual_resource**: should fix it (constant_base_with_shaped_bonus)
- **Comparison**: students learn the importance of reward structure design

### Breaking Changes

**Old System** (DELETED):
- `training.yaml: reward_strategy` field → REMOVED
- `src/townlet/environment/reward_strategy.py` → DELETED (583 lines removed)
- Hardcoded Python reward classes → REPLACED
- All legacy reward strategy tests → DELETED (349 lines removed)

**New System** (REQUIRED):
- `drive.yaml` required for every level (see pack layout above)
- DACEngine compiles YAML → GPU computation graphs
- Checkpoint provenance via `drive_hash` (SHA256 of DAC config)
- All checkpoints must have matching `drive_hash`

**Migration**: See `docs/guides/dac-migration.md`

### Documentation

- **Config Reference**: `docs/config-schemas/drive_as_code.md` (archived
  ⚠ staleness banner — see above)
- **Migration Guide**: `docs/guides/dac-migration.md`

### Q-Learning Algorithm Variants

`training.yaml: use_double_dqn` selects vanilla vs Double DQN; checkpoints persist the flag.
Non-obvious cost on a recurrent architecture (corrected 2026-08-24 — the "3 forward passes vs 2"
previously stated here does not match the current update path): one extra single-step boundary
forward per update; action selection reuses the online unroll (`population/vectorized.py:862-880`).
Details: `docs/architecture/BAC.md` §2.5 and `docs/config-schemas/training.md` — **both now
agree** (verified 2026-08-26; `training.md` was corrected in place on 2026-08-24, so the
warning previously here that it "still carries the stale 3-vs-2 figure" is itself obsolete).

## Configuration System

Training is controlled via YAML config packs in `configs/`. The real pack layout —
pack-level shared files plus `levels/<level>/` overrides, NOT flat `configs/<level>/`
directories — is shown in the DAC "Key Components" section above.

### Active Config Packs (Curriculum)

⚠️ **What follows is the INTENDED curriculum. The shipped configs do not implement it.**
Verified by diff, 2026-08-12 — the levels live under `configs/default_curriculum/levels/`:

| level | intended | actually shipped |
|---|---|---|
| L0_0_minimal | 3×3 grid, 1 affordance | 8×8, 14 affordances |
| L0_5_dual_resource | 7×7 grid, 4 affordances | 8×8, 14 affordances — `training.yaml` **identical to L1** but for `output_subdir` |
| L1_full_observability | 8×8, 14 affordances | as intended |
| L2_partial_observability | token-filtered POMDP | genuinely differs (`active_vision: partial`) |
| L3_temporal_mechanics | 24-tick day/night | genuinely differs (`active_temporal: true`, `day_length: 24`) |

`bars.yaml`, `affordances.yaml` and `drive.yaml` are **byte-identical across all five levels**.
Grid size is set once in pack-level `stratum.yaml` (8×8) and **no level can override it**.
L0_0/L0_5/L1 differ from one another only in training hyperparameters; their `curriculum.yaml`
files differ only in comments. Five documented levels are **three distinct universes**.

**Future**: L4 (multi-zone), L5 (multi-agent), L6 (communication)

### Substrate Types

- `grid`: 2D discrete grid (Grid2DSubstrate) — or 3D with `topology: cubic` (Grid3DSubstrate).
  There is no `grid3d` type; that literal was deleted (it never had a factory branch).
- `gridnd`: 4D-100D discrete grid (GridNDSubstrate)
- `continuous`: 1D/2D/3D continuous space
- `continuousnd`: 4D-100D continuous space
- `aspatial`: No positioning, pure resource management

**Boundary Modes**: clamp (hard walls), wrap (toroidal), bounce (elastic), sticky

**Distance Metrics**: manhattan (L1), euclidean (L2), chebyshev (L∞)

Substrate config examples: the shipped packs (`configs/default_curriculum/stratum.yaml`,
`configs/aspatial_test/`, `configs/test/action_space/*/`). There is no `configs/templates/`
directory — that path is dead. Schemas: `docs/config-schemas/`. Worked substrate examples
(aspatial, toroidal grid, euclidean distance) and a side-by-side comparison:
`docs/examples/`.

### No-Defaults Principle

**All behavioral parameters must be explicitly specified in config files.** The DTO layer
enforces this, with `ConfigDict(extra="forbid")` so stray keys fail at parse time.

DTOs live in `src/townlet/config/` — `training_v2_config.py`, `environment_config.py`,
`bars_v2_config.py`, `affordances_v2_config.py`, `stratum_config.py` (`SubstrateConfig`,
`StratumConfig`), `curriculum_config.py`, `drive_as_code.py`, `vfs_profiles_config.py`,
`effects_config.py`, `items_config.py` — plus
`townlet.environment.action_config.ActionConfig`. (`townlet.substrate.config` does not exist;
`SubstrateConfig` is in `config/stratum_config.py`.)

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
  **declared training hyperparameter** `max_grad_norm` in `training.yaml`
  (`config/training_v2_config.py`), not an engine constant (corrected 2026-08-24; the
  `default_curriculum` packs declare `10.0`)
- Economic balance: WORK pays $22.5. **This became true at runtime only in WS-1(e)**
  (2026-08-12) — before that, six hardcoded `[0.0, 1.0]` clamps crushed every payout to
  `1.0` despite `money.bounds.max: 999999.0`, so six of seven priced affordances were
  permanently unaffordable. "Sustainable with proper cycles" has **never been measured**
  against a working economy; treat it as an intention, not a finding.
- Intrinsic weight annealing: threshold=100.0, requires mean survival >50 steps

## Frontend Visualization

See `frontend/CLAUDE.md` (loads automatically when working under `frontend/`).

## Testing Strategy

Tests focus on:

- Environment mechanics (vectorized operations, GPU tensors)
- Population training (batched updates, curriculum progression)
- Exploration (RND novelty, annealing logic)
- Integration (full training loop)

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
- **Work only in `src/townlet/`** — `src/hamlet/` is obsolete legacy code.

<!-- filigree:instructions:v3.1.0:65e6fb25 -->
<!-- filigree:last-writer:filigree install -->
## Filigree Issue Tracker

`filigree` tracks tasks for this project. Data lives in `.filigree/`. Prefer
the MCP tools (`mcp__filigree__*`) when available; fall back to the `filigree`
CLI otherwise.

### Workflow

```bash
# At session start
filigree session-context                            # ready / in-progress / critical path

# Pick up the next startable issue (atomic claim + transition into its working status)
filigree start-next-work --assignee <name>
# ...or claim a specific issue
filigree start-work <id> --assignee <name>

# Do the work, commit, then
filigree close <id>
```

Use the atomic claim+transition verbs — `work_start` / `work_start_next`
(MCP) or `start-work` / `start-next-work` (CLI). Do **not** chain
`work_claim` (MCP) or `filigree claim` (CLI) with a subsequent status
update — the two-step form races against other agents; the combined verb is
atomic.

**Ready ≠ startable.** The working status is type-specific (tasks →
`in_progress`, features → `building`). Bugs start at `triage`, which has no
single-hop transition into work (`triage → confirmed → fixing`), so a triage
bug is *ready* but not directly *startable*: `work_start` on one returns
`INVALID_TRANSITION` naming the next status, and `work_start_next` skips it.
`work_ready` items carry a `startable` flag (plus a `next_action` hint when
false). Pass `advance=true` (MCP) / `--advance` (CLI) to walk the soft
transitions to the nearest working status automatically.

### Observations: when (and when not) to use them

`observation_create` is a fire-and-forget scratchpad for *incidental* defects — things
you notice *outside the scope of your current task* (a code smell in a
neighbouring file, a stale TODO, a missing test for an edge case you happened
to spot). Notes expire after 14 days unless promoted. Include `file_path` and
`line` when relevant. At session end, skim `observation_list` and either
`observation_dismiss` or `observation_promote` for what has accumulated.

**You fix bugs in your currently defined scope. You do NOT use observations
to finish work prematurely.** If a defect, gap, or follow-up belongs to your
current task, you own it — handle it as part of that task: fix it now, expand
the task's scope, file a proper issue with a dependency, or surface it to the
user. Filing it as an observation and closing the task is *not* completing
the task; it is shipping known-broken work and hiding the debt in a 14-day
expiring scratchpad. The test is "would I have noticed this even if I weren't
working on this task?" If no, it's task scope, not an observation.

### Priority scale

- P0: Critical (drop everything)
- P1: High (do next)
- P2: Medium (default)
- P3: Low
- P4: Backlog

### Reaching for tools

MCP tool schemas describe each tool; `filigree --help` and `filigree <verb>
--help` are the authoritative CLI reference. You do not need to memorise
either catalogue. The verbs you will reach for most:

- **Find work:** `work_ready`, `work_blocked`, `issue_list`, `issue_search`
- **Claim work:** `work_start`, `work_start_next`
- **Update:** `comment_add`, `label_add`, `issue_update`, `issue_close`
- **Admin (irreversible):** `issue_delete` (MCP) / `delete-issue` (CLI) —
  hard-deletes a terminal issue and its rows; `admin_undo_last` cannot reverse it.
- **Scratchpad:** `observation_create`, `observation_list`, `observation_promote`, `observation_dismiss`
- **Cross-product entity bindings (ADR-029):** `entity_association_add`,
  `entity_association_remove`, `entity_association_list`,
  `entity_association_list_by_entity`. Used when a sibling tool (e.g.
  Loomweave) needs to bind a Filigree issue to a function, class, or
  module identifier it owns. The `entity_id` is an opaque external string
  from Filigree's perspective and may be a `loomweave:eid:...` SEI or a legacy
  locator; callers may also supply `entity_kind` explicitly. The consumer (the sibling tool's read
  path) does drift detection against the stored
  `content_hash_at_attach`. `entity_association_list_by_entity` is the
  reverse-lookup surface — given an opaque external entity ID, return every
  Filigree issue bound to it (project isolation is by DB file). Also
  reachable over HTTP as
  `GET/POST /api/issue/{issue_id}/entity-associations`,
  `DELETE /api/issue/{issue_id}/entity-associations?entity_id=…`,
  and `GET /api/entity-associations?entity_id=…`.
- **Health:** `stats_get`, `metrics_get`, `mcp_status_get`

Pass `--actor <name>` (CLI) so events attribute to your agent identity. It
works in either position — before the verb (`filigree --actor X update …`) or
after it (`filigree update … --actor X`); the post-verb value overrides the
group-level one.

### Error handling

Errors return `{error: str, code: ErrorCode, details?: dict}`. Switch on
`code`, not on message text. Codes: `VALIDATION`, `NOT_FOUND`, `CONFLICT`,
`INVALID_TRANSITION`, `PERMISSION`, `NOT_INITIALIZED`, `IO`,
`INVALID_API_URL`, `FILE_REGISTRY_DISPLACED`, `REGISTRY_UNAVAILABLE`,
`LOOMWEAVE_REGISTRY_VERSION_MISMATCH`, `LOOMWEAVE_OUT_OF_SYNC`,
`BRIEFING_BLOCKED`, `STOP_FAILED`, `SCHEMA_MISMATCH`, `INTERNAL`.

On `INVALID_TRANSITION`, call `workflow_transition_list` (MCP) or
`filigree transitions <id>` to see what the workflow allows from here.

Two failure modes deserve a specific response:

- **`SCHEMA_MISMATCH`** — the installed `filigree` is older than the project
  database. The error message contains upgrade guidance. Surface it to the
  user; do not retry.
- **`ForeignDatabaseError`** — filigree found a parent project's database
  but no local `.filigree.conf`. Run `filigree init` in the current
  directory. Do **not** `cd` upward to a different project unless that was
  the actual intent.
<!-- /filigree:instructions -->

<!-- loomweave:instructions:v1.5.0:39edbf6d -->
<!-- loomweave:last-writer:loomweave install -->
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
<!-- /loomweave:instructions -->

<!-- warpline:instructions:v1.3.0 -->
## Warpline (temporal change-impact)

`warpline` answers "if I touch X, what breaks, and what must I re-verify?".
Prefer the MCP tools (`mcp__warpline__*`); fall back to the `warpline` CLI.

Call `warpline_change_list` (shim: `changed`) for a rev range first, then follow
its `next_actions` into `reverify` / `blast_radius`. A `completeness` of
`NO_SNAPSHOT` means warpline cannot see, NOT that nothing is affected.

Enrich-only, local-only, advisory: warpline never gates. The `warpline-workflow`
skill carries the full tool set, the closed vocabularies, and the loop.
<!-- /warpline:instructions -->
