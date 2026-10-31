# The Universe Compiler

Document date: 2026-08-24; authoring front end updated 2026-10-01.
Status: Part of the six-document HLD set (PDR-0118). The declaration-store Cut A sections below
supersede the old filename/loading account; Cut B uses the single canonical variables family. Other architectural descriptions retain their
original date; this update does not certify full compiler or runtime completeness.

The compiler is the thing that turns a YAML pack into one frozen, hash-carrying
`CompiledUniverse`. The world-execution contract is "compile once, execute many": runtime
consumes compiled world declarations, including the optional `presentation` family carried on
`CompiledUniverse.presentation`.

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

Variable authoring uses [one canonical contract](../config-schemas/variables.md). The old
environment/profile/overlay declaration paths are removed. Every variable reaches common
symbol resolution; compiled token scope is explicit and required through cache load.
Other dated architecture descriptions below are not a current symbol inventory.

- **Inputs**: one config pack of recursively discovered `.yaml`/`.yml` documents outside
  `.compiled`. Content identifies the closed declaration family; pack root versus
  `levels/<level>/` identifies scope. Additional subfolders and filenames are transport.
  See [the authoring contract](../config-schemas/declarations.md) for required families,
  fragments, source provenance and clock references. Conventional names such as `stratum.yaml`
  remain useful examples; no filename reader or aliases select semantics.
- **Outputs**: an immutable `CompiledUniverse` carrying canonical DTOs, each level's compiled
  `TokenSpec`, rich metadata, optimization tensors, and the declared provenance hashes.
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
| 1. **Parse** | Discover documents, classify closed content shapes, merge declarations with provenance, then validate existing strict DTOs | `declarations.py`, `loaders/preflight.py`, `raw_configs_v21.py` |
| 2. **Symbol table** | Register meters, variables, actions, affordances, items, effects; fail fast on duplicates | `symbol_table.py` |
| 3. **Resolve** | Walk every cross-file reference (affordance effects, action costs, training overrides) emitting UAC error codes | `validation/references.py` |
| 4. **Cross-validate** | Safety limits, semantic checks, spatial feasibility (grid capacity), cascade cycles, temporal rules, substrate/action alignment, capability semantics | `validation/limits.py`, `validation/semantics.py`, `validation/feasibility.py` |
| 5. **Metadata & token spec** | *Shared* (source stage 6): compile the `variables` declaration into the internal global/agent/item profiles, check item-profile bindings, collect history requirements, build the one command-pipeline namespace (`vfs/namespace.py`) and expression sources, compile the effects catalog, and check every level's affordance and item interaction pipelines. *Per level* (source stage 7): action-space metadata, meter and affordance metadata, item spawn predicates, the registry roster, the compiled `TokenSpec` (exposure, capacity and identity refusals), the VTC transition schedule, and the hashes over them (`token_type_schema_hash`, `layout_hash`, `observation_schema_hash` over the `TokenSpec`, `variable_schema_hash`, `action_schema_hash`, `transition_graph_hash`, `expression_schema_hash`, `vfs_hash`). There is no observation spec, activity mask or per-field UUID (deleted at the token cut) | `compilers/vfs.py`, `compilers/observation.py`, `compilers/metadata.py`, `compilers/effects.py`, `compilers/actions.py`, `universe/dto/token_spec.py`, `vfs/transition_schedule.py` |
| 6. **Optimization** | Pre-compute tensors in deterministic order — base depletions, cascade/modulation tables, hourly action masks, position maps | `optimization.py`, `compilers/optimization.py` |
| 7. **Emit / cache** | Construct the frozen `CompiledUniverse`, serialize and cache via MessagePack, expose runtime DTOs | `compiler.py:_stage_8_emit_artifact` |

⚠ **The stage numbering in the source does not map one-to-one onto that table.** The source
numbering has one authority, `CompilationStage` (`universe/stages.py`): 0 preflight (directory
check and declaration discovery), 1 parse, 2 safety limits, 3 semantic cross-validation,
4 symbol table, 5 reference resolution (plus presentation references and static write
targets), 6 shared schemas and effects (`_stage_6_prepare_shared_artifacts`), 7 levels and
optimization data (`_stage_7_compile_levels`), 8 emit (`_stage_8_emit_artifact`). There is no
separate cross-validate method; limits and semantics run as source stages 2 and 3 over the
loaded DTOs. Read the seven stages above as the conceptual contract and
`UniverseCompiler.compile` for the actual order. (Corrected 2026-10-31.)

Each stage emits an INFO log marker (`Stage N: …`) from `townlet.universe.compiler`, so pipeline
order is observable in tests and runtime diagnostics.

**Determinism.** The compiler is intentionally pure: given the same YAML content and the same
compiler source, the emitted artifact is stable; `metadata.config_hash` depends on content alone,
and `metadata.provenance_id` additionally on the pack path and the toolchain (§5). That is what unlocks both cache hits and checkpoint
identity checking.

---

## 3. Key data structures

- **Declaration store** (`declarations.py`) — content-classified declarations keyed by
  scope, family and declared entity identity, with actual `file:line` origins. It merges catalog
  fragments deterministically and resolves the explicit clock-period reference before DTO load.
- **`RawConfigs`** (`raw_configs_v21.py`) — staged DTO bundle built from that store. Existing
  strict config shapes remain the content vocabulary; transport names do not select loaders.
- **`UniverseSymbolTable`** (`symbol_table.py`) — the central registry for stages 2→4.
- **`CompiledUniverse`** (`compiled.py`) — frozen dataclass with DTO copies, each level's
  `token_spec` (`ObservationActivity` and the observation spec were deleted at the token cut), rich metadata, optimization tensors, and the seventeen declared `*_hash`
  fields. Navigation: `all_levels` (a dict field, not a method), `get_level`, `to_level`.
  Instantiation: `create_environment(num_agents=…, level_name=…, device=…)` — all three
  keyword-only and all three required, delegating to `VectorizedHamletEnv.from_universe`.
  Persistence: `save_to_cache` / `load_from_cache`.
  ⚠ The archived guide's `to_runtime()` and `check_checkpoint_compatibility()` **do not exist**
  (zero hits in `src/`, verified 2026-08-24). Checkpoint identity is enforced by
  `assert_checkpoint_identity` in `training/checkpoint_utils.py`, not by a method on the artifact.
- **`TokenSpec`** (`dto/token_spec.py`) — the compiled token observation: seven engine token
  types with fixed payload widths, per-universe capacities and slot bindings. `total_dims` is
  the flat width, `census` the per-type counts, `row_layout()` the per-row layout. It replaced
  `ObservationSpec`, `ObservationField` and `ObservationActivity` (deleted at the token cut,
  DIV-008); there is no activity mask.
- **`OptimizationData`** — tensors and lookup tables consumed by the runtime.

---

## 4. Validation, errors, and warnings

**Error catalog.** Validation stages emit structured `CompilationMessage`s carrying a code, a
location, and an actionable hint. Any collector with accumulated issues calls
`CompilationErrorCollector.check_and_raise()`, so contributors see **all** failures at once
rather than one per run.

**Authoring provenance.** Discovery retains YAML node locations, keyed by declaration
family/scope/entity rather than canonical filenames. Discovery, DTO and downstream validation
diagnostics use the actual declaring `file:line`; duplicate declarations name both origins.
Source-map consumers use this provenance after files move or multiple documents share a file.
This closes the front-end provenance requirement; it does not assert that every runtime fault
is a structured compiler diagnostic.

⚠ **The code vocabulary is not the one the archived guide documents.** That guide describes a
`UAC-RES-*` / `UAC-VAL-*` / `UAC-ACT-*` numeric catalog (`UAC-RES-001`, `UAC-VAL-002`, …).
Verified 2026-08-24: the only numbered `UAC-*` codes remaining in `src/townlet/` are
`UAC-VAL-005` and `UAC-VAL-009` — **both inside the unwired `cues_compiler.py`**, so neither can
fire. The codes actually emitted are semantic names, plus a numbered `DAC-REF-*` family for
drive reference resolution and three `UAC-RES-*` symbolic (not numbered) codes.

Representative, grouped by what they catch:

| area | codes |
| --- | --- |
| declaration discovery / loading | Required-family, unknown/ambiguous document, duplicate identity, misplaced scope, escaping symlink, YAML syntax and typed-load diagnostics; see `error_codes.py` for the live codes |
| reference resolution | `UAC-RES-VFS`, `UAC-RES-CASCADE`, `UAC-RES-ITEM`, `DAC-REF-001` … `DAC-REF-015` |
| vocabulary agreement | `METER_VOCAB_MISMATCH`, `AFFORDANCE_VOCAB_MISMATCH`, `ENABLED_AFFORDANCES_INVALID` |
| affordances & cascades | `AFFORDANCE_INVALID_METER`, `AFFORDANCE_OPENING_HOURS_MISSING`, `AFFORDANCE_DEPLOYMENT_POSITIONS_MISSING`, `CASCADE_CYCLE`, `CASCADE_MISSING`, `CASCADE_EXTRA`, `CASCADE_INVALID_METER`, `MODULATION_MISSING`, `MODULATION_EXTRA`, `MODULATION_INVALID_REFERENCE` |
| required declarations | `LEVEL_DRIVE_MISSING`, `LEVEL_DRIVE_EXTRINSIC_MISSING`, `LEVEL_DRIVE_INTRINSIC_MISSING` |
| substrate / temporal / vision | `EXPRESSION-POSITION-ASPATIAL` (a position function on an aspatial substrate), `SUBSTRATE_ACTION_INCOMPATIBLE`, `SUBSTRATE_ACTION_WARNING_AS_ERROR`, `INTERACTION_RADIUS_MISSING`, `TEMPORAL_DAY_LENGTH_MISSING`, `MULTI_TICK_REQUIRES_TEMPORAL`, `VISION_INCOMPATIBLE` |
| safety limits | `CONFIG_LIMIT_EXCEEDED`, `GRID_SIZE_LIMIT_EXCEEDED`, `GRID_CAPACITY_EXCEEDED`, `ITEM_TYPES_LIMIT_EXCEEDED`, `SPAWN_RULE_LIMIT_EXCEEDED` |

**Drive diagnostics follow the declaration.** `DAC-REF-*` errors refer to the authored
`drive` declaration's origin, including its location after transport relocation. `drive.yaml`
is a convention, and no `drive_as_code.yaml` alias is used to construct locations.

**Security limits.** Hard caps guard against accidental or malicious config explosion — meter
and affordance counts, item types, spawn rules, and grid cells (a grid that would exceed the
cell ceiling raises `GRID_SIZE_LIMIT_EXCEEDED`; a level with `randomize_affordances: true`
whose grid cannot hold its deployed affordances plus one agent raises `GRID_CAPACITY_EXCEEDED`
at its `randomize_affordances:` line — per world, since the batch is N independent
single-agent worlds (S1), so the population size never enters it and the runtime never falls
back to declared positions).

**There is no warning channel in practice — every finding is a hard error.** Verified
2026-08-24, re-checked 2026-10-25: the collector has no warning-adding method (the
zero-caller `add_warning` was deleted); the one
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
  collisions, producing `config_hash` (pack content only: two identical packs share it).
  `provenance_id` folds in `config_hash`, the resolved pack path (`experiment_dir`), the compiler
  version, a SHA-256 over every `.py` file of the installed `townlet` package (so an uncommitted
  source edit invalidates the cache and a docs-only commit does not), and Python / torch /
  pydantic versions. The git SHA is not a cache input; it is recorded as
  `metadata.compiler_git_sha`, resolved from the package root, never the cwd.
- Cache validation (`UniverseCompiler.cache_staleness`) requires the artifact's `experiment_dir`
  to be this pack, equal `config_hash` and `provenance_id`, and no recursively discovered
  `.yaml`/`.yml` file outside `.compiled` newer than the artifact; otherwise the compiler
  recompiles. A pack copied with its `.compiled/` therefore recompiles at the new path.
  `inspect` applies the same rule against the source pack and prints `Freshness: FRESH`,
  `STALE - <reasons>` or `UNKNOWN` (source pack gone), with a stderr warning when not fresh.
- `CompiledUniverse.save_to_cache` / `load_from_cache` use MessagePack with defensive fallbacks:
  a corrupt cache triggers full recompilation plus a warning.

**Checkpoint identity is a separate contract from the cache.** `config_hash` is the cache
fingerprint; the checkpoint gate is `assert_checkpoint_identity`
(`src/townlet/training/checkpoint_utils.py`), which hard-compares fifteen of the artifact's
declared `*_hash` fields, including the seven pack-scope hashes (`actions_hash`,
`variables_hash` and `effects_hash` are canonical declaration content, not a pydantic dump:
expression text enters as its AST, and a `variables` declaration moved between files does not
move it) and the five per-level hashes (`items_appearance_hash` joined on 2026-10-31);
`config_hash` is not stamped. Full declared-vs-enforced breakdown: `HLD.md` §5.2.

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

spec = compiled.get_level("L1_full_observability").token_spec
spec.total_dims                             # flat observation width
spec.census                                 # {token type: count}
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
artifact path, `freshness`, metadata hashes, the token census, `token_types` with payload
features and row widths, and `token_rows`: one entry per slot with its filler kind, `filler_ref`,
scope, compact `start`/`end` and network-boundary `fixed_start`/`fixed_end`); `validate`
compiles and discards, so `.compiled/` never appears. Every CLI refusal exits 1 with a
`[CODE] file:line - message` diagnostic, never a traceback. `scripts/validate_compiler_cli.py` iterates every pack in `configs/`.

The CLI is wired into CI via `.github/workflows/config-validation.yml`. **Caveat: no workflow
has ever run on `project-recovery`** — the gates that actually
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

### Declaration-store Cut A: discovery, merge and provenance

The front end discovers every `.yaml`/`.yml` document recursively outside `.compiled`, including
multiple YAML documents per file. Existing wrapped shapes (`experiment:`, `stratum:`,
`environment:`, `actions:`, and the per-level sections) and distinctive bare brain/profile/
effect/variable/transition shapes identify content. Unknown, ambiguous, misplaced or malformed
declarations refuse; symlinks outside the pack refuse. No legacy filename reader remains.

Pack scope and `levels/<id>` scope remain explicit. Required families are checked after merge,
not by file existence. Singleton identity is `(scope, family)`; catalog entries use declared
identifiers qualified by family/profile, and cascades use ordered source/target pairs. Equal
duplicates still fail, naming both `file:line` origins. Repeated structural catalog headers must
agree. Appearance rules remain a singleton because they have no rule identifier.

Fragments merge in sorted pack-relative path/document order; lists retain authored order.
Renaming or moving a file may change transport `metadata.config_hash`, while preserving
semantic identity for equivalent declarations and order. Reordering an authored array can
change semantics and ABI and is not normalized away.

An active curriculum can resolve `day_length: {period_of: <variable id>}` from a declared global
ambient-tick temporal variable's cyclical normalization period before constructing the existing
DTO. The period must be finite, positive and integral; inactive levels remain explicitly null.
Invalid targets and duplicated coupled clock facts fail with their origins. This is a narrow
front-end reference, not a redesign of runtime clocks.

See [the full authoring contract](../config-schemas/declarations.md) and
PDR-0117.

### Remaining boundaries

Cut A preserves the current typed DTOs and compiled semantic hashes. It does not complete
variable-surface unification, access/lifetime authoring, artifact round-trip fidelity, full BAC,
rendering or convergence. Those require their own contracts and evidence. The wider accepted
declaration-store direction must not be described as complete merely because discovery works.
The original PRD calendar window remains unchanged; functional acceptance is reported separately
from that expired window.

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
