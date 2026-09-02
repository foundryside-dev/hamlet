# The Universe Compiler

Document date: 2026-08-24
Status: **Current** (reviewed 2026-08-24) — part of the six-document HLD set (PDR-0118).

The compiler is the thing that turns a YAML pack into one frozen, hash-carrying
`CompiledUniverse`. It is where "compile once, execute many" is enforced: **no YAML is read
past compile time**, and the runtime consumes read-only DTO proxies.

- **Source**: `src/townlet/universe/compiler.py` (+ `loaders/`, `validation/`, `compilers/`,
  `dto/`, `optimization.py`, `symbol_table.py`, `errors.py`, `source_map.py`)
- **Artifact**: `src/townlet/universe/compiled.py` — `CompiledUniverse`
- **CLI**: `python -m townlet.universe {compile,inspect,validate}`
- **Tests**: `uv run pytest tests/test_townlet/unit/universe/`
  (use `UV_CACHE_DIR=.uv-cache` in sandboxed environments)
- **Context**: `HLD.md` §5 (what the artifact guarantees), `UAC.md` (what is being compiled),
  `VFS.md` (the ABI it compiles to)

---

## 1. Scope

- **Inputs**: one config pack — pack-level shared files plus `levels/<level>/` overrides. See
  `UAC.md` §3 for the current filename convention. (⚠ The archived compiler guide lists
  `cascades.yaml`, `cues.yaml`, `substrate.yaml` and a shared `configs/global_actions.yaml`.
  **None of those paths exist**; that list predates several renames and deletions.)
- **Outputs**: an immutable `CompiledUniverse` carrying canonical DTOs, the observation spec
  and activity mask, rich metadata, optimization tensors, and the declared provenance hashes.
- **Consumers**: `VectorizedHamletEnv` (runtime), `DemoRunner` / the training pipeline,
  checkpoint utilities, the live-inference server, and the differential oracle harness.
- **Out of scope**: substrate implementations themselves (`STRATA.md`), and a standalone brain
  compiler — the brain rides *inside* the artifact as a validated `BrainConfig` plus
  `brain_hash`, not as an artifact of its own (`BAC.md` §2.4).

`compile()` requires an explicit `primary_level`; implicit selection raises. `CompiledUniverse`
is single-level by construction — `get_level` / `to_level` / `all_levels` navigate; there is no
`.levels` mapping.

---

## 2. The seven-stage pipeline

The canonical framing is seven stages: parse → symbol table → resolve → cross-validate →
metadata → optimization → emit/cache.

| stage | what it does | where |
| --- | --- | --- |
| 1. **Parse** | Load every file via shared loaders, enforce no-defaults validation at the DTO layer | `loaders/preflight.py` (scoping + YAML-syntax preflight), `loaders/v21.py`, `raw_configs_v21.py` |
| 2. **Symbol table** | Register meters, variables, actions, affordances, items, effects; fail fast on duplicates | `symbol_table.py` |
| 3. **Resolve** | Walk every cross-file reference (affordance effects, action costs, training overrides) emitting UAC error codes | `validation/references.py` |
| 4. **Cross-validate** | Safety limits, semantic checks, spatial feasibility (grid capacity), cascade cycles, temporal rules, substrate/action alignment, capability semantics | `validation/limits.py`, `validation/semantics.py`, `validation/feasibility.py` |
| 5. **Metadata & observation spec** | Build shared schemas (bars/VFS) and the effects catalog; compute the observation spec, activity mask, per-field UUIDs, counts and hashes | `compilers/vfs.py`, `compilers/observation.py`, `compilers/metadata.py`, `compilers/effects.py`, `compilers/actions.py` |
| 6. **Optimization** | Pre-compute tensors in deterministic order — base depletions, cascade/modulation tables, hourly action masks, position maps | `optimization.py`, `compilers/optimization.py` |
| 7. **Emit / cache** | Construct the frozen `CompiledUniverse`, serialize and cache via MessagePack, expose runtime DTOs | `compiler.py:_stage_7_emit_artifact` |

⚠ **The stage numbering in the source does not map one-to-one onto that table.** `compile()`
runs, in order: Stage 0 scoping preflight, Stage 0 YAML-syntax validation, Stage 1 config load,
Stage 1b safety limits, Stage 1c semantic cross-validation, Stage 2 symbol table, Stage 3
reference resolution, Stage 5 `_stage_5_prepare_shared_artifacts`, Stage 6
`_stage_6_compile_levels` (level compilation *and* optimization), Stage 7
`_stage_7_emit_artifact`. There is no `_stage_4_cross_validate` method — cross-validation runs
as 1b/1c over loaded DTOs. The archived guide's stage table names methods that no longer exist;
read the seven stages as the conceptual contract and `compiler.py:93` for the actual order.

Each stage emits an INFO log marker (`Stage N: …`) from `townlet.universe.compiler`, so pipeline
order is observable in tests and runtime diagnostics.

**Determinism.** The compiler is intentionally pure: given the same YAML content and the same
compiler version, the emitted artifact — including `metadata.config_hash` and
`metadata.provenance_id` — is stable. That is what unlocks both cache hits and checkpoint
identity checking.

---

## 3. Key data structures

- **`RawConfigs`** (`raw_configs_v21.py`) — staged DTO bundle exposing convenient properties
  over the parsed configs. Its `shared_specs` table is one of the places the 16-filename
  mandate is hardcoded (§7).
- **`UniverseSymbolTable`** (`symbol_table.py`) — the central registry for stages 2→4.
- **`CompiledUniverse`** (`compiled.py`) — frozen dataclass with DTO copies, observation spec,
  `ObservationActivity`, rich metadata, optimization tensors, and the seventeen declared `*_hash`
  fields. Navigation: `all_levels` (a dict field, not a method), `get_level`, `to_level`.
  Instantiation: `create_environment(num_agents=…, level_name=…, device=…)` — all three
  keyword-only and all three required, delegating to `VectorizedHamletEnv.from_universe`.
  Persistence: `save_to_cache` / `load_from_cache`.
  ⚠ The archived guide's `to_runtime()` and `check_checkpoint_compatibility()` **do not exist**
  (zero hits in `src/`, verified 2026-08-24). Checkpoint identity is enforced by
  `assert_checkpoint_identity` in `training/checkpoint_utils.py`, not by a method on the artifact.
- **`ObservationSpec` / `ObservationField`** — deterministic UUID-backed observation definitions
  derived from VFS exposures. The field is **`total_dims`**, not `total_dim`.
- **`ObservationActivity`** (`dto/observation_activity.py`) — `active_mask`, `group_slices`
  (bars / spatial / affordance / temporal / custom), `active_field_uuids`.
- **`OptimizationData`** — tensors and lookup tables consumed by the runtime.

---

## 4. Validation, errors, and warnings

**Error catalog.** Validation stages emit structured `CompilationMessage`s carrying a code, a
location, and an actionable hint. Any collector with accumulated issues calls
`CompilationErrorCollector.check_and_raise()`, so contributors see **all** failures at once
rather than one per run.

⚠ **Locations are file-level only today.** `SourceMap` (`source_map.py`) is fully implemented —
including a line-number-annotating YAML loader — and referenced **nowhere outside its own file**
(verified 2026-08-24), so no diagnostic currently carries a line number. Wiring it is part of
the in-flight cleanup (§7), and per-declaration `file:line` provenance is a hard requirement of
PDR-0117.

⚠ **The code vocabulary is not the one the archived guide documents.** That guide describes a
`UAC-RES-*` / `UAC-VAL-*` / `UAC-ACT-*` numeric catalog (`UAC-RES-001`, `UAC-VAL-002`, …).
Verified 2026-08-24: the only numbered `UAC-*` codes remaining in `src/townlet/` are
`UAC-VAL-005` and `UAC-VAL-009` — **both inside the unwired `cues_compiler.py`**, so neither can
fire. The codes actually emitted are semantic names, plus a numbered `DAC-REF-*` family for
drive reference resolution and three `UAC-RES-*` symbolic (not numbered) codes.

Representative, grouped by what they catch:

| area | codes |
| --- | --- |
| pack scoping / loading | `SCOPING_MISSING_EXPERIMENT_FILE`, `SCOPING_LEVEL_DIRECTORY`, `SCOPING_FORBIDDEN_LEVEL_FILE`, `MISSING_FILE`, `MISSING_LEVELS_DIR`, `NO_CURRICULUM_LEVELS`, `YAML_SYNTAX_ERROR`, `LOAD_ERROR`, `LEVEL_LOAD_ERROR` |
| reference resolution | `UAC-RES-VFS`, `UAC-RES-CASCADE`, `UAC-RES-ITEM`, `DAC-REF-001` … `DAC-REF-015` |
| vocabulary agreement | `METER_VOCAB_MISMATCH`, `AFFORDANCE_VOCAB_MISMATCH`, `ENABLED_AFFORDANCES_INVALID` |
| affordances & cascades | `AFFORDANCE_INVALID_METER`, `AFFORDANCE_OPENING_HOURS_MISSING`, `AFFORDANCE_DEPLOYMENT_POSITIONS_MISSING`, `CASCADE_CYCLE`, `CASCADE_MISSING`, `CASCADE_EXTRA`, `CASCADE_INVALID_METER`, `MODULATION_MISSING`, `MODULATION_EXTRA`, `MODULATION_INVALID_REFERENCE` |
| required declarations | `LEVEL_DRIVE_MISSING`, `LEVEL_DRIVE_EXTRINSIC_MISSING`, `LEVEL_DRIVE_INTRINSIC_MISSING` |
| substrate / temporal / vision | `SUBSTRATE_ACTION_INCOMPATIBLE`, `SUBSTRATE_ACTION_WARNING_AS_ERROR`, `INTERACTION_RADIUS_MISSING`, `TEMPORAL_DAY_LENGTH_MISSING`, `MULTI_TICK_REQUIRES_TEMPORAL`, `VISION_INCOMPATIBLE` |
| safety limits | `CONFIG_LIMIT_EXCEEDED`, `GRID_SIZE_LIMIT_EXCEEDED`, `GRID_CAPACITY_EXCEEDED`, `ITEM_TYPES_LIMIT_EXCEEDED`, `SPAWN_RULE_LIMIT_EXCEEDED` |

⚠ **Ghost filename in DAC diagnostics.** Every `DAC-REF-*` message cites `drive_as_code.yaml`
as its location (`validation/references.py:77-224`) — a file that exists in no pack; the real
file is `levels/<level>/drive.yaml`. The compiler's own diagnostics point authors at a
nonexistent filename. Slated for fix in the in-flight cleanup (§7).

**Security limits.** Hard caps guard against accidental or malicious config explosion — meter
and affordance counts, item types, spawn rules, and grid cells (a grid that would exceed the
cell ceiling raises `GRID_SIZE_LIMIT_EXCEEDED`; a grid too small to hold its affordances plus
agents raises `GRID_CAPACITY_EXCEEDED`).

**There is no warning channel in practice — every finding is a hard error.** Verified
2026-08-24: `CompilationErrorCollector.add_warning` exists but has **zero callers**; the one
producer of soft findings, `SubstrateActionValidator`, has its warnings escalated to errors
(`SUBSTRATE_ACTION_WARNING_AS_ERROR`, `validation/semantics.py:151-156`). The archived guide's
economic-imbalance *warning* has no current counterpart at all: economic-balance analysis is not
computed — `UniverseMetadata`'s `max_sustainable_income` / `total_affordance_costs` /
`economic_balance` are hardcoded to `0.0` (`compilers/metadata.py:172-174`), and
`validation/feasibility.py` contains only the grid-capacity helper, whose consumers raise hard
errors. The pedagogical *stance* stands — economically imbalanced early levels are by design,
and scarcity is teaching material — but nothing in the current compiler warns about it.

⚠ **The `allow_unfeasible_universe` escape hatch documented in the archived guide no longer
exists.** Verified 2026-08-24: zero hits in `src/` and `configs/`, and
`tests/test_townlet/_fixtures/variable_meters.py:405` records why — "v2.1 `TrainingV2Config`
forbids extra fields, so we no longer patch `allow_unfeasible_universe` into `training.yaml`;
feasibility checks should be satisfied by the constructed packs." Per-code suppression does not
exist either — consistent with the fact that nothing is emitted as a warning in the first place.

### The `CuesCompiler` caveat

`src/townlet/universe/cues_compiler.py` exists, and `CuesCompiler` is imported at
`compiler.py:46` and instantiated at `compiler.py:69` as `self._cues_compiler` — **and never
called anywhere else in the file** (verified 2026-08-24). The archived
`COMPILER_ARCHITECTURE.md` (design-era, 2025-11) lists it as an active Stage-4 participant
validating `cues.yaml`; that is design intent, not a record of what runs. Treat cue validation
as unwired. The same archived document asserts a backwards-compatibility success criterion this
project explicitly rejects. `CuesCompiler` heads the dead-seam inventory in the 2026-08-24
compiler assessment and is slated for deletion by the in-flight cleanup (§7).

---

## 5. Caching and provenance

- Cache artifacts live at `<pack_dir>/.compiled/universe-<primary_level>.msgpack` — **one
  artifact per level**, since `CompiledUniverse` is single-level by construction
  (`compiler.py:677`). The archived guide's flat `universe.msgpack` path is stale.
- The compiler normalizes YAML (sorted keys) before hashing, then folds in file names to avoid
  collisions, producing `config_hash`. `provenance_id` folds in compiler version, git SHA, and
  Python / torch / pydantic versions.
- Cache validation uses `config_hash` **plus** the maximum mtime across the pack's YAML files
  (including `levels/*/*.yaml`). If the hash changes or any config is newer than the artifact,
  the compiler recompiles rather than loading.
- `CompiledUniverse.save_to_cache` / `load_from_cache` use MessagePack with defensive fallbacks:
  a corrupt cache triggers full recompilation plus a warning.

**Checkpoint identity is a separate contract from the cache.** `config_hash` is the cache
fingerprint; the checkpoint gate is `assert_checkpoint_identity`
(`src/townlet/training/checkpoint_utils.py`), which hard-compares seven of the artifact's
seventeen declared `*_hash` fields. Full declared-vs-enforced breakdown: `HLD.md` §5.2.

A rough edge README records here is **fixed**: README §Known rough edges (stamped 2026-08-20)
describes agent-profile packs compiling green while their cache artifact silently fails to
serialize. That was repaired the next day — commit `03764c6b` (2026-08-21,
`hamlet-a141ab5db3` / `hamlet-cbb747a51e`): agent profiles now serialize
(`compiled.py:_serialize_profile`), the field is typed `CompiledGlobalProfile | None`, and a
failed cache write **fails the compile** instead of downgrading to a hidden log warning.
Re-verified empirically 2026-08-24 on `configs/trial_o_bidding_blind` (non-null
`agent_profile`), and again 2026-09-02 on `configs/test/vfs_bar_access` after that trial
pack was deleted (`PDR-0142`): a non-null `agent_profile` compiles and writes
`.compiled/universe-<level>.msgpack`.

---

## 6. Usage

```python
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler

compiled = UniverseCompiler().compile(
    Path("configs/default_curriculum"),
    primary_level="L1_full_observability",
)

env = compiled.create_environment(          # every argument keyword-only and required
    num_agents=4,
    level_name="L1_full_observability",
    device="cpu",                           # no default device; omitting it raises
)

compiled.observation_spec.total_dims              # allocated observation width
sum(compiled.observation_activity.active_mask)    # active width at this level
```

Never copy a dimension number out of a run into a document — ask the artifact
(`HLD.md` §5.3).

### CLI

**`--primary-level` is required**, on every subcommand that takes a config directory — there is
no implicit level selection anywhere, CLI included. (The archived guide's examples omit it and
will fail.)

```bash
# Compile a pack (writes .compiled/universe-<level>.msgpack)
python -m townlet.universe compile configs/default_curriculum \
    --primary-level L1_full_observability

# Inspect: either a config dir (then --primary-level is required) …
python -m townlet.universe inspect configs/default_curriculum \
    --primary-level L1_full_observability --format table

# … or the artifact path directly
python -m townlet.universe inspect \
    configs/default_curriculum/.compiled/universe-L1_full_observability.msgpack

# Validate without touching the cache — the CI lint-style check
python -m townlet.universe validate configs/default_curriculum \
    --primary-level L1_full_observability
# → "Validation succeeded in 1072.7 ms (no cache artifacts written)"
```

Flags: `compile --no-cache` skips cache reads and writes and always rebuilds;
`inspect --format {table,json}` selects human or machine-readable output (json carries the
artifact path and metadata hashes); `validate` compiles and discards, so `.compiled/` never
appears. `scripts/validate_compiler_cli.py` iterates every pack in `configs/`.

The CLI is wired into CI via `.github/workflows/config-validation.yml`. **Caveat: no workflow
has ever run on `project-recovery`** (filigree `hamlet-2100105c9a`) — the gates that actually
hold on the recovery branches are run locally, by hand.

### Testing

```bash
uv run pytest tests/test_townlet/unit/universe/
```

That directory holds the per-stage suites (pipeline, symbol table, validation, cache, CLI,
serialization, compiled-universe identity, primary-level selection, brain level override,
observation spec). Runtime integration is covered by
`tests/test_townlet/unit/environment/test_vectorized_env_runtime.py`, and
`scripts/validate_substrate_runtime.py` smoke-tests packs end to end.

---

## 7. Forward

### In flight: the cleanup unit (hamlet-af929afa06)

The 2026-08-24 compiler assessment
(`archive/REVIEW-2026-08-24-compiler-architecture-assessment.md`) inventoried the trunk's debt:
dead seams with grep-verified zero callers (`CuesCompiler` + `config/cues.py`, the unwired
`SourceMap`, `pipeline.py`'s discarded typed bundles, `OptimizationCompiler.resolve_day_length`,
six unused `__init__` result fields, the hardcoded-`0.0` economics metadata), the
self-disagreeing stage numbering, and the fragmented error-code namespaces. Its first buys —
dead-seam deletion, one authoritative stage enum, an error-code registry (including the
`drive_as_code.yaml` ghost-filename fix), and SourceMap wiring for line-level diagnostics — are
being executed as `hamlet-af929afa06` in an isolated worktree at the time of writing. **This
document describes the tree at HEAD; that unit has not landed.** The assessment's target shape,
which PDR-0117 shares: a *declaration-store* compiler — a discovery/merge front end producing
one provenance-carrying declaration store, a middle compiling typed declaration families
against one symbol table, and an emission layer serializing the artifact and hash tree
mechanically.

### Decided: the front end becomes discovery + merge

**PDR-0117 — decided, not yet implemented.** The pack layout today mandates 16 distinct
filenames, hardcoded across roughly nine compiler modules — chiefly `loaders/preflight.py`
(the `shared_files` / `optional_shared_files` lists), `raw_configs_v21.py` (the `shared_specs`
table), and the error strings that name specific files.

The decided direction: the compiler **globs the pack** (subfolders included), parses every YAML
document against the closed typed schemas, and merges into one compiled profile. Filenames
become authoring convention, never semantics. "Required file" becomes "required declaration".
Override and merge happen **by declared id**, with loud collision refusal — a compile error
naming both declaring files.

Two constraints the implementation must hold, both squarely compiler concerns:

1. **Determinism must survive.** Canonical merge order (sorted paths) so `config_hash` stays
   stable across runs and machines.
2. **Provenance must survive.** Per-declaration `file:line` must reach diagnostics. The reversal
   trigger for PDR-0117 is precisely a measurable degradation in compile-error quality that
   per-declaration provenance cannot fix — in which case a thin `pack.yaml` index returns, not
   the 16-filename mandate.

This pairs naturally with the variable-surface unification the 2026-08-24 VFS audit demands
(`environment.yaml` / `vfs_profiles.yaml` / `variables_reference.yaml` declaring variables with
divergent hardcoded semantics), because both land in the same front end. Sequencing: its own
unit, after the token-observation migration. Full text: `UAC.md` §4 and
`docs/product/decisions/0117-files-are-transport-declarations-are-the-unit.md`.

---

## 8. Related

- `HLD.md` — the artifact's guarantees; declared vs. enforced hashes
- `UAC.md` — what is being compiled, and the pack convention
- `STRATA.md` — the substrate the observation and action compilers interrogate
- `VFS.md` — the ABI the compiler targets
- `BAC.md` — how the brain rides inside the artifact
- `docs/config-schemas/` — per-surface field references (archived 2026-08-24;
  content may be stale)
- `archive/REVIEW-2026-08-24-compiler-architecture-assessment.md` — the line-level assessment of
  the as-built pipeline: clean seams, dead architecture, load-bearing tangles, and the ranked
  effort/opportunity table behind §7
- `archive/UNIVERSE-COMPILER.md` — the fuller troubleshooting narrative this document condenses.
  Accurate on caching, provenance and CLI; **stale** on the input-file list, the stage method
  names, the `UAC-RES-001`-style error catalog, `allow_unfeasible_universe`, and `total_dim`
  (the field is `total_dims`). Read it for the shape of the troubleshooting, not for identifiers.
- `archive/COMPILER_ARCHITECTURE.md` — design-era rationale and diagrams; describes sub-compilers
  that were never wired
