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

⚠️ **`docs/` is 573 markdown files, ~90% of them last touched 2026-05, before the current
recovery work. Treat it as design intent, never as a record of what shipped.** Verified
2026-08-15 (`docs/architecture/REVIEW-2026-08-15-architecture-docs-and-hld.md`).

The sharpest case: `docs/architecture/BRAIN_AS_CODE.md` and
`docs/architecture/hld/02-brain-as-code.md` both say
*"Status: Approved for Implementation"*, while `execution_graph` / `cognitive_topology` /
`agent_architecture` return **zero grep hits** in `src/` and `configs/`. The design is the
target; the status line is false. That pattern repeats across the architecture corpus.

**Rules:**

1. **Never cite a doc as evidence something is implemented.** Check `src/townlet/` first.
2. **Where a doc disagrees with `README.md`, README is right.** It is current, honest about
   status, and carries the correct product framing.
3. `docs/architecture/` does not know about `src/townlet/oracle/`, the strangler rewrite,
   `items/`, or `effects/`. Absence there means nothing.
4. Many (not all) files carry frontmatter with an "AI-Friendly Summary" and "Reading Strategy".
   Where present, read it first to decide relevance before opening a 2000-line file.

**Current-and-trustworthy:** `README.md`, `docs/product/`, `docs/oracle/`,
`docs/architecture/vfs.md`, `docs/architecture/vfs-current-implementation.md`,
`docs/config-schemas/`.

### The oracle (strangler discipline)

Work is mid **strangler rewrite behind a pinned oracle**. Tag `oracle-2026-08-13` freezes the
previous system as the specification for preserved behaviour. From `docs/oracle/ORACLE.md`:
*"The oracle never mutates"*, and *"a diff against the oracle is a defect in the rebuild unless
the register says otherwise."* Accepted differences are registered in
`docs/oracle/known-divergences.md`. **Never edit anything under `.oracle/`.**

### Universe Compiler (UAC) Quick Reference

- **Source**: `src/townlet/universe/compiler.py` - seven-stage pipeline (parse → symbol table → resolve → cross-validate → metadata → optimization → emit/cache)
- **Docs**: `docs/UNIVERSE-COMPILER.md`. `docs/architecture/COMPILER_ARCHITECTURE.md` is
  design-era (2025-11): useful for intent, but it describes sub-compilers that were never wired
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

**Observation Encoding Modes** (configurable via pack-level `stratum.yaml`):

- **relative** (default): Normalized [0,1] coordinates - best for transfer learning, required for POMDP
- **scaled**: Coordinates scaled to grid dimensions [0, grid_size] - value range conveys grid size implicitly
- **absolute**: Raw unnormalized coordinates - for physical simulation

**Note**: All encoding modes produce **identical obs_dim** (2 dims for position). Only the value range changes, not the number of dimensions.

**Observation Dimensions** (Grid2D with "relative" encoding):

⚠️ **The per-level dimension counts previously listed here (29 / 54) were wrong by roughly 4×,
and no replacement literal is given on purpose.** Observation width moves whenever the observed
surface changes, so any number written here starts decaying immediately — that is how the old
ones got wrong. Read `universe.levels[<name>].observation_spec.total_dim` off the compiled
artifact. It is the only authority, and it is correct by construction at every commit.

**Key insight**: Observation dim is **constant** across all Grid2D grid sizes, enabling true transfer learning.

**Action Space** (global vocabulary enables checkpoint transfer):

- Grid2D: 8 actions (6 substrate + INTERACT + WAIT)
- Grid3D: 10 actions
- GridND (7D): 16 actions
- Aspatial: 4 actions

**POMDP Support**:

- ✅ **Supported**: Grid2D, Grid3D (vision_range ≤ 2), Aspatial (special case)
- ❌ **Not Supported**: Continuous substrates, GridND (N≥4) - window too large

See `tests/test_townlet/unit/environment/test_pomdp_validation.py` for validation logic.

### Variable & Feature System (VFS)

**Status**: in production. VFS is the typed state / observation / transition ABI between UAC and
BAC — not just an observation helper.

**Purpose**: Declarative state space configuration for observation specs, access control, action
dependencies, and (via VTC) compiled transitions.

**Pipeline**: `YAML Config → Schema Validation → Observation Spec → Runtime Registry → Observations`

**Key Components**:

- `schema.py`: VariableDef, ObservationField, NormalizationSpec, WriteSpec
- `registry.py`: Runtime storage with GPU tensors, access control enforcement
- `observation_builder.py`: Compile-time spec generation, dimension validation
- `vtc.py`: VFS Transition Compiler — action writes, passive dynamics, cascades, terminal
  conditions, reward components, occupancy claims

**Variable Scopes** — nine, not three (`VariableScope` in `vfs/schema.py`): `global`, `agent`,
`agent_private`, `item`, `pair`, `group`, `affordance`, `zone`, `message`.

**Access Control**: `readable_by` / `writable_by` role lists per variable, enforced at
`registry.get()` / `set()`. Roles are open strings, not a closed enum — `agent`, `engine`,
`actions`, `vtc`, `social_model` are the common ones.

**Which files a pack needs** (corrected 2026-08-15 — the previous "all packs MUST include
`variables_reference.yaml`" was **false**):

- `vfs_profiles.yaml` — **required**, pack root. Authoritative source for compiled global, agent
  and item profiles. Level directories must NOT contain one.
- `variables_reference.yaml` — **optional** static overlay for non-item variables and observation
  marks. Static only: no expressions, no item-scoped variables. `configs/default_curriculum`
  does not have one; `configs/L5_multi_agent` does.

**Documentation**: `docs/config-schemas/variables.md`, `docs/config-schemas/vfs-profiles.md`,
and `docs/architecture/vfs-current-implementation.md` (current, source-mapped).

### Action Space (Composable)

**Architecture**: Action Space = Substrate Actions + Custom Actions

- **Global Vocabulary** (pack-level `actions.yaml`, e.g. `configs/default_curriculum/actions.yaml`):
  all levels in a pack share one action vocabulary. There is no `configs/global_actions.yaml` —
  that path is dead and several docs still cite it.
- **Custom Actions**: REST (energy recovery), MEDITATE (mood boost)
- **Action Labels**: Configurable terminology (gaming, 6dof, cardinal, math presets)

See `docs/config-schemas/enabled_actions.md` for details.

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
see `docs/config-schemas/drive_as_code.md`.

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

- **Config Reference**: `docs/config-schemas/drive_as_code.md`
- **Migration Guide**: `docs/guides/dac-migration.md`

### Q-Learning Algorithm Variants

`training.yaml: use_double_dqn` selects vanilla vs Double DQN; checkpoints persist the flag.
Non-obvious cost: recurrent Double DQN needs 3 forward passes vs 2 for vanilla.
Details: `docs/config-schemas/training.md`.

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
| L2_partial_observability | POMDP, 5×5 window | genuinely differs (`active_vision: partial`) |
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
directory — that path is dead. Schemas: `docs/config-schemas/`.

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

**SimpleQNetwork** (full observability — L0, L0.5, L1) and **RecurrentSpatialQNetwork**
(POMDP — L2, L3: CNN vision encoder + LSTM). Layer shapes: read
`src/townlet/agent/networks.py`. Observation width comes only from the compiled artifact
(see State Representation above) — do not write dimension literals here.

- LSTM hidden state: resets at episode start, persists during rollout, resets per transition in batch training

**Training Details**:

- Gradient clipping: `max_norm=10.0` (prevents exploding gradients)
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
- Keep the framework/instance boundary sharp: `default_curriculum` content (its meters,
  affordances, 8×8 grid) is example data, not framework. Do not freeze it into the engine.
- Preserve "interesting failures" as teaching material; document unexpected behaviour rather
  than immediately fixing it.
- The goal is a framework others author in, not production-ready agents.
- **Work only in `src/townlet/`** — `src/hamlet/` is obsolete legacy code.

<!-- filigree:instructions:v3.1.0:c1c023c3 -->
<!-- filigree:last-writer:filigree install -->
## Filigree Issue Tracker

`filigree` tracks this project's work. Use it to find, claim, update and close
issues: `filigree session-context` at session start, then
`filigree start-next-work --assignee <name>`.

Full reference: the **filigree-workflow** skill (patterns, priorities,
observations, error codes), `filigree --help`, and the `mcp__filigree__*` tool
schemas. Prefer the MCP tools when available; fall back to the CLI.

Two rules `--help` will not tell you:

1. Claim atomically: `work_start` / `work_start_next` (MCP) or `start-work` /
   `start-next-work` (CLI). Never chain a claim with a separate status update;
   that two-step form races other agents.
2. On `SCHEMA_MISMATCH` the installed filigree is older than the project
   database. Surface it to the user; do not retry.
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
