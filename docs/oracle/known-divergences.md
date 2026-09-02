# Known-Divergences Register

**Stream:** WS-7 (`hamlet-e3af412673`) — the strangler's enabling stream (`PDR-0006`).
**Stood up:** 2026-08-13, as WS-7's first artifact (`PDR-0028` — routed findings need a
register that exists; routing to a register that doesn't is filing to /dev/null).
**Oracle tag:** `oracle-2026-08-17` → `4222a917` (moved forward 2026-08-17, `PDR-0074`; see
`ORACLE.md`). Previous tag `oracle-2026-08-13` → `0e875d7a` (pinned 2026-08-13) stays as
history. Open entries were re-verified at the new tagged commit and are stamped
`tag-stamped` there; entries whose divergence dissolved at the new tag are `retired`.

**Re-stamp at `4222a917` (2026-08-17):** the oracle moved forward because the hash-only
suppression had reached its ceiling (`AGREE` unreachable on 16/16 cells and the pack-drift
guard armed on zero cells since 2026-08-15, `PDR-0056`) and because no matrix cell could see
the next cut at all (`PDR-0074`). At the new tag the matrix is **20 cells** (the ten
default_curriculum cells, the three differential packs, and two profile-variable packs
`items_smoke` / `effects_smoke`), **every fixture under `oracle_fixtures/` is a byte copy of
its live pack, and no cell declares anything** — the first time since 2026-08-15 that exit 0
means "old and new agree" — **acceptance run `20260817-072714`: 20/20 `AGREE` on CPU and CUDA,
exit 0, zero register refs in any verdict.** Terminal states after the re-stamp: DIV-001 `tag-stamped`, DIV-002
`tag-stamped`, DIV-003 `retired`, DIV-004 `retired`, DIV-005 `retired`.

**Superseded 2026-08-23 (DIV-009):** the "no cell declares anything" / "20/20 `AGREE`" claim
above was true of that one acceptance run, not of the tag going forward — six Phase B
landings after `4222a917` moved provenance hashes with no register entry, and DIV-009 now
binds all twenty cells. Left as written because it is a historical record of what that run
showed; do not read it as the current state of the matrix.

## What this register is

The strangler freezes the current system as an **oracle** and rebuilds one design-space unit
at a time against it, with a differential harness asserting old and new agree. This register
records **every place the new system is EXPECTED to differ from the oracle** — up front, at
plan time, rather than discovered as a failing diff.

An entry here means: *a diff on this surface is intended*. Adjudication is split by whether
the entry can manifest in an env trace. **Trace-visible entries** bind to the harness through
a per-cell declaration in the matrix (see *Binding a trace-visible entry* below); the harness
verifies the observed outcome against that declaration narrowly — it does not read this file
at runtime. **Checkpoint-boundary entries** (DIV-001/002) cannot appear in a trace; their
intended new behaviour is verified by the rebuilt boundary's own tests, not by the harness.
Either way, a diff matching nothing is a defect in the rebuild (or a missing entry, which is
a process failure to record before cutting the seam).

**What does NOT belong here:**

- **WS-1's ten fixes.** They landed *before* the oracle tag, so the oracle already carries
  them. They are requirements, not divergences (`PDR-0029`).
- **Silent corruption the oracle must not carry.** If freezing a behaviour would freeze
  artifact corruption itself (not a known quirk), it fails `PDR-0028`'s exception clause
  test and must be fixed pre-tag, not registered. The register carries *known, bounded,
  intended* differences only.
- **Authoring-surface gaps** (declared-but-inert, unauthorable) → WS-4 (`PDR-0028`).

## Entry lifecycle

`registered` → `tag-stamped` (oracle behaviour re-verified at the tagged commit) →
`built` (new behaviour exists; harness suppression active and adjudicated) →
`retired` (the oracle-side surface is gone, or the divergence dissolved).

## Entry schema

Each entry records: the **surface**, the **oracle behaviour** (verified against source, with
evidence — never copied from a filed issue unchecked), the **intended new behaviour**, the
**harness adjudication rule** (what diff shape is expected and how to judge it), and
**provenance** (tracker ID + PDRs).

---

## DIV-001 — Five pack-level provenance hashes: computed, serialized, compared by nobody

- **Status:** `tag-stamped` at `oracle-2026-08-17` (re-verified at `4222a917`, 2026-08-17:
  the five names appear only in `universe/compiled.py`, `universe/compiler.py`, and — as a
  docstring mention, not a compare site — `oracle/matrix.py`; no stamp/compare site
  references them; `hamlet-2dde1015fe` open). Previously `tag-stamped` at
  `oracle-2026-08-13` (re-verified at `0e875d7a`: the five names appeared only in
  `universe/compiled.py` and `universe/compiler.py`)
- **Provenance:** `hamlet-2dde1015fe` · `PDR-0021` (filed-not-folded) · `PDR-0022` (the
  `config_hash_warning` deletion's precondition — this entry existing is that condition) ·
  `PDR-0028` (routing rule)
- **Surface:** checkpoint identity enforcement for the five **pack-level** content hashes:
  `experiment_hash`, `stratum_hash`, `environment_hash`, `actions_hash`, `items_hash`.

**Oracle behaviour (verified 2026-08-13):** all five are computed by
`_compute_pydantic_hash`, carried on `CompiledUniverse`, written to the msgpack artifact,
and presence-required on load — and **never compared against a checkpoint by anything**.
Verified: the five names appear in exactly two files, `universe/compiled.py` and
`universe/compiler.py`; no stamp/compare site references them. Consequence: a change to
`stratum.yaml` (substrate), `environment.yaml` (VFS declarations), `actions.yaml` (action
vocabulary), or `experiment.yaml` does not reject a checkpoint *on that hash's own account*.
Some changes are caught incidentally (a grid change usually moves `observation_schema_hash`;
an action change usually moves `action_schema_hash`) — incidental coverage, not a guarantee.
`experiment_hash` has no proxy at all.

**Intended new behaviour:** all five stamped by the metadata-attach path and hard-compared
at every checkpoint boundary, copying the `drive_hash` pattern — **missing on either side
raises**; no `if x is not None` escape. One deliberate design point: `items_hash` is
legitimately `None` for packs declaring no items, so its guard must distinguish
*absent-because-no-items* (both sides `None` — pass) from *absent-because-unstamped*
(raise). Adjacent, same shape, fold into the same unit: `meter_count` and
`observation_schema_hash` are stamped by `attach_universe_metadata` and must be confirmed
compared (they were not, at recon time).

**Harness adjudication:** expected diff shape — **new REJECTS a checkpoint the oracle
ACCEPTS**, specifically when one of these five configs changed between save and load.
Old-accepts/new-rejects on these surfaces is the divergence working. Any diff in the
*other* direction (new accepts what old rejects), or a rejection whose cited hash did not
actually change, is a rebuild defect.

---

## DIV-002 — Two checkpoint stamp/compare paths outside the guarded boundary

- **Status:** `tag-stamped` at `oracle-2026-08-17` (re-verified at `4222a917`, 2026-08-17:
  the string-matched broad `except` sits at `demo/runner.py:199-202`; the population
  stamp/compare path at `population/vectorized.py:1150` / `:1198`; `hamlet-df2b972c49` open).
  Previously `tag-stamped` at `oracle-2026-08-13` (re-verified at `0e875d7a`:
  `demo/runner.py:202`)
- **Provenance:** `hamlet-df2b972c49` · `PDR-0008` (the breach this outlives) · `PDR-0028`
  (routing rule) · WS-1 tasks 4/5 (`hamlet-ae6601e463`, `hamlet-1029f99f4b`) which guarded
  the DemoRunner and serving paths but not these.
- **Surface:** every checkpoint read/write site that is not the two WS-1-guarded ones.
  Known today:
  1. `VectorizedPopulation.get_checkpoint_state` / `load_checkpoint_state`
     (`population/vectorized.py:1127`, `:1175`) — an independent stamp/compare path for
     population state; the identity guarantees tasks 4/5 established do not apply here.
  2. `DemoRunner._validate_checkpoint_compatibility` (`demo/runner.py:157`) — unpickles a
     checkpoint **before any universe exists**, inside `except Exception`, and decides what
     to re-raise by **string-matching its own error message** (`"Unsupported checkpoint
     format" in str(e)`); everything else is swallowed with "will fail later during actual
     load". Verified 2026-08-13 by reading the body. This is the silent-fallback antipattern
     `CLAUDE.md` names explicitly, sitting on the validation path itself.

**Oracle behaviour (verified 2026-08-13):** these paths accept/inspect checkpoints with no
identity guard, and path 2 swallows every failure it doesn't recognise by message text.

**Intended new behaviour:** the rebuild's checkpoint boundary is **enumerated, then closed**.
First unit is enumeration, not repair (the issue's own instruction): find every site that
writes or reads a checkpoint mapping — search `torch.save` / `torch.load` and every consumer
of the checkpoint dict, not callers of the known helpers — the recurring lesson is
*enumerate producers, not call shapes*. Then every surviving site routes through the shared
identity gate (`assert_checkpoint_identity` or successor); the broad `except` and its
string-match are deleted; validation failures raise loudly.

**Harness adjudication:** expected diff shape — **new RAISES where the oracle silently
proceeds**: loading population state with mismatched identity, and any checkpoint the
compatibility probe cannot actually read. Old-proceeds/new-raises on these paths is the
divergence working. The enumeration list, once produced, is appended to this entry so the
harness knows the *complete* set of boundary sites the rule covers; until then this entry's
surface is deliberately open-ended and MUST NOT be treated as "just the two known sites".

---

## DIV-003 — Substrate→observation-dim seam: three declared configs compile, then crash before producing a trace

- **Status:** `retired` (2026-08-17, `PDR-0074` — the oracle moved forward to `4222a917`,
  which carries the cut, so the three configs run on BOTH sides and the divergence
  dissolved; the three packs stay in the matrix as plain standing cells expected to
  `AGREE`). Previously `built` (2026-08-15 — the seam is cut; full 16-cell matrix CPU+CUDA
  exit 0 with all six DIV-003 cells `DIVERGED_AS_REGISTERED`, runs `20260815-055108` /
  `20260815-055207`). Previously `tag-stamped` the same day: all three crashes re-executed
  at `0e875d7a` through the harness's own driver under the oracle worktree's `src` with the
  injection probe-verified first — not copied from the 2026-08-11 assessment, which predicted
  the first two messages exactly and had never captured the third verbatim.
- **Harness shape: old-side-crash**
- **Provenance:** `hamlet-e3af412673` (WS-7, first knockdown) · `PDR-0035` (the unit) ·
  `PDR-0036` (declared-and-crashing is a divergence — authorizes this entry) · `PDR-0037`
  (record-then-bind order) · `PDR-0040` (the conjunctive match these cells are adjudicated
  by) · assessment §3/§4 (first found; superseded by the tag re-verification above)
- **Surface:** the contract by which the compiler learns a substrate's observation shape.
  `universe/compilers/observation.py` derives dims by switching on `substrate.type` string
  literals (`:64-76` grid cells, `:135-145` position/velocity dims — including a 2-D window
  formula that never reads `depth`) instead of asking the substrate instance, the pattern the
  same function already applies to `continuous`/`continuousnd` at `:146-155`; and
  `environment/vectorized_env.py:180` hard-rejects non-square grids the compiler itself
  handles correctly.

**Oracle behaviour (verified 2026-08-15 at `0e875d7a`):** three declared, schema-valid
configurations compile and then crash at env construction/reset — nonzero exit, **no trace
written**. Reproduced with the harness driver (`num_agents=4`, `steps=100`, `seed=42`,
`cpu`); final exception lines verbatim (these are the cell signatures):

| fixture pack | level | final exception |
|---|---|---|
| `configs/differential/div003_scaled` — `observation_encoding: scaled`, sole change | `L1_full_observability` | `ValueError: Observation field 'obs_position' produced shape (4, 4), expected (4, 2).` |
| `configs/differential/div003_cubic_partial` — `topology: cubic` + `depth: 3`, sole changes | `L2_partial_observability` | `ValueError: Observation field 'obs_local_window' produced shape (4, 125), expected (4, 25).` |
| `configs/differential/div003_rect` — `height: 6` (width 8), sole change | `L1_full_observability` | `ValueError: Non-square grids not yet supported: 8×6` |

Raise sites at the tag: the first two from the shape guard at
`environment/observation_encoder.py:140` — the substrate honours the declared config
(`grid2d.py` `_encode_scaled` returns `[N,4]`; `grid3d.py` partial window returns a
`(2r+1)³` cube) while the compiler hardcoded 2 position dims and a 2-D window; the third
from `environment/vectorized_env.py:180`. Each fixture pack is a copy of
`configs/default_curriculum` varying **only** the named stratum values, reduced to its one
level (shape-mismatch first dim is `num_agents`, so signatures are stable only at the
declared `num_agents=4`).

**Intended new behaviour:** the rebuilt seam asks the substrate instance for its
observation shape for **all** substrate types; all three configs compile **and run**,
producing traces valid for their cells' params. The divergence is old-crashes/new-runs —
there is no old trace to compare, which is exactly the `PDR-0037` shape.

**Harness adjudication:** bound per-cell in `src/townlet/oracle/matrix.py` via
`RegisteredDivergence("DIV-003", <verbatim final-exception line above>)`. A cell passes
as `DIVERGED_AS_REGISTERED` only on `PDR-0040`'s full conjunction (old crashed + no trace
+ signature inside the final exception text + new side ran with a valid lone trace from
the declared src root). Pre-cut, both sides crash and the cells land `NEW_SIDE_ERROR`
("not (yet) built") — red, honestly; they flip at the cut. The old side is frozen, so
`REGISTERED_DIVERGENCE_ABSENT` on these cells can only mean the oracle moved forward (new
tag) — retire the entry then.

**Deliberately NOT covered: `type: grid3d`.** The fourth crash the knockdown carries
(`ValueError: Unknown substrate type: grid3d`, `substrate/factory.py:152`, reproduced at
the tag 2026-08-15 — it dies at *compile*, via `compilers/actions.py`) is inside the seam
but outside this entry: the assessment's zero-BC disposition is to **delete the dead
literal** (the working 3-D path is `type: grid` + `topology: cubic`, and no factory branch
has ever existed), and a config that crashes on *both* sides produces no trace-visible
divergence to register. If the cut instead builds a `grid3d` factory branch, extend this
entry — or add DIV-004 — with its cell **before** cutting, per this register's own rule.

---

## DIV-004 — The normalization-vocabulary programme: the authoring surface changes, so the compiled provenance moves and behaviour does not

- **Status:** `retired` (2026-08-17, `PDR-0074` — the oracle moved forward to `4222a917`,
  which carries the whole normalization programme; the frozen fixtures were re-frozen at the
  new schema, so old and new compile the same `environment.yaml` and the provenance no longer
  moves. `PDR-0056`'s two recorded costs — `AGREE` unreachable matrix-wide, pack-drift guard
  armed on zero cells — dissolve with it, as that PDR said they would.) Previously `built`
  (2026-08-15 — declared before the first cut of the programme, per this
  register's own record-then-bind rule; W1 is the first cut it covers. Full 16-cell matrix
  exit 0 with all ten standing cells `DIVERGED_AS_REGISTERED (DIV-004)` and every trace
  stream byte-identical: runs `20260815-175940` (CPU) / `20260815-180022` (CPU+CUDA).)
- **Harness shape: hash-only**
- **Provenance:** `PDR-0054` (the plan this entry serves) · `PDR-0052` / `PDR-0053`
  (underspecification is a compile error; `range_type` is the complete type declaration) ·
  `PDR-0037` (record-then-bind order) · `hamlet-fba56feca5`, `hamlet-3d3039f340`,
  `hamlet-365e996511`
- **Surface:** the meter/variable normalization authoring surface — `environment.yaml`
  `variables[].normalization`, `MeterConfig.range_type`, and the `NormalizationSpec`
  vocabulary they compile into.

**Why one entry and not three.** W1 (the `clip` parameter), W2/W3 (`range_type` as the
complete type declaration, and per-meter normalizers), and W7 (every pack rewritten) are
three cuts of ONE continuous divergence: the frozen fixture sits at the pre-programme
`environment.yaml` schema for the whole duration regardless. Three entries would describe
three moments of one state.

**Oracle behaviour (verified at `0e875d7a`, 2026-08-15).** The frozen `NormalizationConfig`
is `ConfigDict(extra="forbid")` and rejects the new key outright — measured by parsing the
live pack with the oracle worktree's `src` on `PYTHONPATH`:

```
4 validation errors for EnvironmentConfig
environment.variables.0.normalization.clip
  Extra inputs are not permitted [type=extra_forbidden, input_value=False, input_type=bool]
```

So the frozen fixtures under `oracle_fixtures/` **stay at the old schema deliberately**
(`oracle_fixtures/README.md`: *"If it is a schema change, leave the fixture at the old
schema, set `pack_divergence` on the affected cells, and register the entry"*). This is the
first real use of the input-freeze built at `49bdf28e` for `hamlet-2090c9f16d`.

**Intended new behaviour.** The two sides compile different `environment.yaml` files, so the
compiled provenance differs; the WORLD does not. Measured across all five
`default_curriculum` levels by compiling the live tree against a git worktree at the
pre-change commit — **exactly three hashes move, uniformly, at every level**:

| hash | family | moves | why |
|---|---|---|---|
| `environment_hash` | RAW | yes | `_compute_pydantic_hash` over the whole file — moves for any edit, so it is the weakest of the four as evidence |
| `observation_schema_hash` | DERIVED | yes | the compiled `NormalizationSpec` carries a new field (W1), then one field per meter with its own spec (W3) |
| `vfs_hash` | DERIVED | yes | same specs, mirrored into the VFS observation fields |
| `variable_schema_hash` | DERIVED | **added at W2/W3/W4** | the VFS variable SET changed: one N-wide `obs_meters` became N 1-wide `obs_meter_<name>` |

`transition_graph_hash` deliberately does **not** appear. The cut is observation-side only:
the VTC reads bars through `_current_bar_state`, a name-keyed view of the STATE tensor, and
never through the observation. Its absence is an assertion, not an omission — if it ever
moves, the cut reached the transition graph and that is a finding.

`observation_spec.total_dims` is **unchanged at 124** on every level, because every meter in
`default_curriculum` declares a width-preserving `minmax`. This paragraph records the
deleted pre-token ABI: `PDR-0134` supersedes it with a fixed two-lane value block and
rejects `one_hot` on meters rather than widening the observation.

**Harness adjudication.** Bound per-cell in `src/townlet/oracle/matrix.py` via
`RegisteredHashDivergence("DIV-004", hash_fields=(...))` on every STANDING cell. A cell
passes as `DIVERGED_AS_REGISTERED` only when the observed set of moved hashes equals the
declared set **exactly** and **every trace stream matches byte-for-byte**. Specifically:

- A **fourth** hash moving → `HASH_MISMATCH`, red. The rebuild changed more than this entry
  claims.
- A declared hash **not** moving → `REGISTERED_DIVERGENCE_ABSENT`, red. The entry is stale —
  reconcile it, do not relax it. (Same treatment DIV-003 gets when the oracle stops crashing.)
- Any stream difference → `DIVERGE`, red. **This entry suppresses nothing about behaviour.**
  Before it existed, `compare_traces` returned `HASH_MISMATCH` and short-circuited *before*
  comparing a single stream — the harness could not express "provenance moved as intended,
  behaviour did not" at all, which would have made the oracle blind on precisely the surface
  WS-4 exists to change. That is `hamlet-2090c9f16d` one layer up, and fixing it is the
  second `RegisteredDivergence` shape.

The six DIV-003 fixture cells declare `pack_divergence="DIV-004"` (their packs are copies of
`default_curriculum`, so the schema change reaches them) but **no** `hash_divergence`: their
old side crashes and writes no trace, so there are no hashes to compare.

**Retire this entry** when the oracle is re-tagged past the programme. Until then, expanding
it is correct — extending the `hash_fields` tuple as later cuts move more derived hashes —
but each expansion must be re-measured, not predicted, and the measurement recorded here.

**What this entry COSTS — recorded because an adversarial review measured it, not because it
was designed in.** A six-lens review of the W2/W3 cut (2026-08-15) refuted 21 of 23 findings
with executed repros and confirmed the suppression cannot pass a stream difference — a
14-test smuggle suite failed to get one through in any of reset-obs / last-obs / reward /
done / `-0.0` vs `0.0` / NaN. But it surfaced two real losses of signal that this entry is
responsible for:

1. **`AGREE` is now unreachable for every cell in the 16-cell matrix.** All ten standing
   cells necessarily return `DIVERGED_AS_REGISTERED (DIV-004)`, and the six DIV-003 cells
   return it via the crash shape. Exit 0 therefore no longer means *"old and new agree"*; it
   means *"everything diverged exactly as registered"*. That is a weaker statement, and it
   is weaker for the whole remaining life of this entry.
2. **The pack-drift guard is armed on zero cells.** All 16 now declare
   `pack_divergence="DIV-004"`, and that field is a BOOLEAN gate — declaring it blesses
   *arbitrary* drift between the frozen fixture and the live pack, not merely the schema
   change it was declared for. The machinery built at `49bdf28e` for `hamlet-2090c9f16d` is
   inert while this entry is open.

**Reversal trigger for both.** Re-tag the oracle. This entry exists because the oracle is
pinned behind an authoring-surface change it cannot parse, and every cost above dissolves the
moment the tag moves forward. If a THIRD cut needs to widen `hash_fields` again, that is the
signal the entry has outlived its usefulness and the tag should move instead — a register
entry that suppresses more each time is converging on suppressing everything.

**Not a cost, but worth recording where the measurement lives:** the split costs roughly
**21% on `env.step` and 32% on `_get_observations`** for `default_curriculum` L1 at 32 agents
on CPU (measured twice, independently, during the same review) — eight per-meter registry
reads and writes per tick instead of one vectorized pair. Accepted deliberately: this project
trades throughput for authorability by design, and the alternative was leaving 8 of 9
normalization kinds unauthorable. Recorded so nobody rediscovers it as a mystery.

**Expansion log.** W1 measured three movers. W2/W3/W4 re-measured and found a fourth,
`variable_schema_hash`, exactly as the pre-cut recon predicted it would — the prediction was
recorded first so that a surprise would have been visible as one. Method both times: a git
worktree at the pre-cut commit, compiled against the live tree, all five levels.

## DIV-005 — `semantic_type`: one closed vocabulary, author-authoritative, `effects` admitted; the compiled provenance moves and behaviour does not

- **Status:** `retired` (2026-08-17, `PDR-0074` — the oracle moved forward to `4222a917`,
  which carries the semantic-type cut; both sides now emit the author-declared vocabulary and
  the provenance no longer moves.) Previously `built` (2026-08-16 — declared `tag-stamped`
  first, oracle behaviour re-verified
  at `0e875d7a` through the oracle worktree before any code changed; then cut, then measured
  and adjudicated: full 16-cell matrix CPU+CUDA exit 0, run `20260816-225750`, all ten standing
  cells `DIVERGED_AS_REGISTERED (DIV-004)` with exactly the four declared hashes moved and every
  stream byte-identical; the six DIV-003 cells unchanged.)
- **Harness shape: hash-only** (the second shape, `RegisteredHashDivergence`)
- **Provenance:** `PDR-0047` (the compiler is a compiler: closed vocabularies, the declaration
  is authoritative) · `PDR-0045` (name-blind) · `PDR-0037` (record-then-bind order) ·
  `hamlet-2fe1c34ebb` (the finding this entry serves) · `hamlet-45b35cfee5` (`interaction_type`,
  the same shape, resolved in the same unit — no observation surface, so no register entry of
  its own)
- **Surface:** the semantic-type vocabulary of compiled observation fields —
  `ObservationField.semantic_type` on the compiled `ObservationSpec`, the VFS mirror that
  feeds `observation_schema_hash`, `observation_activity.group_slices`, and the authoring
  side: `environment.yaml` `variables[].semantic_type` (new, required), plus the removal of
  the declared-but-unreachable `semantic_type` from `VariableDef` and the three
  `vfs_profiles.yaml` variable classes.

**Oracle behaviour (verified at `0e875d7a`, 2026-08-16, by compiling with the oracle
worktree's `src` on `PYTHONPATH` against the oracle worktree's own packs).** The compiler
assigns every field's `semantic_type` from a **hardcoded per-block literal** and never reads
an author's declaration; the vocabulary it emits is `spatial / bars / affordance / effects /
custom / temporal`, while the five declaring schema classes permit only
`bars / spatial / affordance / temporal / custom` with `default="custom"`. Measured:

- `default_curriculum` L1/L2/L3 at the tag: 11 fields, `obs_grid_encoding, obs_local_window,
  obs_position, obs_velocity → spatial`; `obs_meters → bars`; `obs_affordance_at_position →
  affordance`; the four `environment.yaml` variables → `custom` regardless of anything an
  author could write (the frozen `VariableConfig` is `extra="forbid"` and has no such key);
  `obs_temporal → temporal`. Group slices `spatial [0,93) bars [93,101) affordance [101,116)
  custom [116,120) temporal [120,124)`, `total_dims 124`. The VFS mirror carries the same
  eleven values.
- `configs/test/effects_smoke` L0_effects at the tag: the compiled field `obs_effects` carries
  **`effects`** (`compilers/observation.py:235` at the tag) while its VFS mirror carries
  **`custom`** — `build_vfs_observation_fields` filters through
  `allowed_semantic = {bars, spatial, affordance, temporal, custom}` (`:381-384` at the tag)
  and silently remaps anything else. **One field, two values**: `group_slices` says
  `effects [34,58)`, `observation_schema_hash` was computed over `custom`. This is the
  oracle's behaviour and it is what the register records as the *old* side.

**Intended new behaviour.** One authoritative closed vocabulary — `SemanticType` in
`townlet/vfs/semantic_type.py`: `bars, spatial, affordance, effects, temporal, custom` —
referenced by the compiled DTO (typed and **required**, so the DTO now constrains the compiler,
which `str | None` did not), by the compiler's own emissions, by the VFS mirror (no remap: the
mirror carries the field's value), and by the authoring schema. `effects` is **admitted** as a
deliberate extension (`PDR-0016`): it names a real compiled block with its own group slice,
and mapping it onto `custom` would have destroyed the grouping the structured encoders exist
to use. `default="custom"` is gone everywhere. The author's declaration is authoritative
where an author can make one: `environment.yaml` variables declare `semantic_type` (required),
the compiler emits exactly that value, and the field list is stable-partitioned by the fixed
group order `spatial, bars, affordance, effects, custom, temporal` so any member is legal
without breaking group contiguity — `bars` excepted, which is the meter block and has a
runtime contract (`_sync_meter_observation_to_vfs`), so an authored variable declaring it is
a **compile-time** error rather than the runtime raise it would have been. Declarations that
could reach no compiled field are removed rather than left as inert schema: `VariableDef` (a
state variable has no observation grouping) and the three profile variable classes (their
variables are flattened into the single `obs_vfs` block, which carries one value); the
follow-up that splits `obs_vfs` into per-variable fields is where that declaration returns.

**Diff shape — PREDICTED at `tag-stamped` (recorded first so a surprise would be visible as
one, DIV-004's discipline), then MEASURED at `built` by DIV-004's method** — a git worktree at
the pre-cut commit `fb60d581` compiled against the live tree, all five `default_curriculum`
levels plus `configs/test/effects_smoke`. **The measurement agreed with the prediction on every
row**, so the table stands as written:

| hash | family | moves for `default_curriculum` | why |
|---|---|---|---|
| `environment_hash` | RAW | yes | every variable gains a `semantic_type` key |
| `observation_schema_hash` | DERIVED | **no** for `default_curriculum` (its four variables declare `custom`, which is what the compiler emitted before; the mirror value is unchanged) — **yes** for any pack with `obs_effects` (mirror `custom → effects`) | the mirror now carries the field's own value |
| `vfs_hash` | DERIVED | follows `observation_schema_hash` | composite |
| `variable_schema_hash` | DERIVED | no | the variable set and its canonical entries do not include `semantic_type` |
| observation field UUIDs | — | no for `default_curriculum` | the ObservationSpec values are unchanged when the author declares what the compiler used to hardcode; `obs_effects` already carried `effects` |

`observation_spec.total_dims` and every group slice are **unchanged for every shipped pack**
— the stable partition by group order is the identity on today's layout, which is pinned by
test (`test_default_curriculum_layout_is_unchanged_by_the_cut`) and, at `built`, by every
trace stream matching byte-for-byte. Measured pre-cut vs live: field list, semantic types,
group slices, `total_dims` and the VFS mirror are identical on all five levels;
`default_curriculum` moves **only `environment_hash`**; `effects_smoke` moves
**`observation_schema_hash` and `vfs_hash`** and nothing else, with its mirror now reading
`obs_effects → effects`. In the matrix run the new-side `observation_schema_hash` for L1
(`86a10a2d76…`) is the same value the live tree produced *before* the cut — the register's
claim that this cut does not touch the derived hashes of the shipped demo is a measured fact.

**Harness adjudication.** The ten standing cells already bind `DIV-004`
(`RegisteredHashDivergence` over `environment_hash, observation_schema_hash,
variable_schema_hash, vfs_hash`) and declare `pack_divergence="DIV-004"`, because the frozen
fixture stays at the pre-programme `environment.yaml` schema. This entry's movers are a
**subset** of that declared set, so the standing cells adjudicate this cut under the *existing*
binding: `DIVERGED_AS_REGISTERED (DIV-004)` with every stream byte-exact — and **the
`hash_fields` tuple is not widened**, which is the signal DIV-004 names as the point at which
the tag should move instead. Stated plainly, the cost this inherits from DIV-004: the harness
cannot tell DIV-004's movement of `observation_schema_hash` from this entry's on the same
frozen fixture; the *behaviour* promise (no stream differs) is adjudicated at full strength,
the *provenance* promise is adjudicated only as "still exactly the four". The pack edits this
cut makes (`semantic_type: custom` on every `environment.yaml` variable) are further drift
blessed by the same boolean `pack_divergence` gate DIV-004 already holds open. The frozen
fixtures under `oracle_fixtures/` stay at the old schema, per `oracle_fixtures/README.md`.

**Retire this entry** with DIV-004, when the oracle is re-tagged past the authoring-surface
programme.


---

## DIV-006 — The `obs_vfs` block: global and agent profile variables become one field each with a declared semantic type; the item-slot sub-block becomes a named feature; the compiled provenance moves and behaviour does not

- **Status:** `retired` (2026-08-26, unit 3 Task 11 — **superseded by DIV-008**. This entry's
  intended NEW-SIDE behaviour was deleted outright by the token cut: `ObservationSpec`,
  `ObservationField`, the VFS mirror and `VFSObservationSpec` are gone, so "one
  `ObservationField` per exposed profile variable plus `obs_item_slots`" has no referent on
  the new side. Its three declared hashes still move on the four profile cells, but for
  DIV-008's cause, and DIV-008 declares them uniformly on all twenty cells; its
  `_DIV006` binding and its `pack_divergence="DIV-006"` on `effects_smoke` are removed, the
  latter re-pointed at DIV-008's per-pack drift table. Nothing about the measurement below
  is withdrawn — it was true of the tree it was taken on.) Previously `built`
  (2026-08-17 — cut at `8c5fa2c8`; full 20-cell matrix CPU+CUDA exit 0,
  run `20260817-091351` (executed by the owner): sixteen cells `AGREE`, the four
  profile-variable cells `DIVERGED_AS_REGISTERED (DIV-006)` with **exactly**
  `observation_schema_hash`, `variable_schema_hash`, `vfs_hash` moved on each — the predicted
  set, no more, no fewer — and every stream byte-identical; `environment_hash` did not move,
  as predicted.) Previously `tag-stamped` (2026-08-17 — oracle behaviour re-verified at
  `4222a917` by compiling `configs/test/items_smoke` and `configs/test/effects_smoke` with the
  `.oracle/oracle-2026-08-17` worktree's `src` on `PYTHONPATH`, before any code changed)
- **Harness shape: hash-only** (`RegisteredHashDivergence`), bound on the **four
  profile-variable cells only** (`items_smoke:L0_smoke`, `effects_smoke:L0_effects` × cpu/cuda).
  The sixteen other cells declare nothing and must stay `AGREE`: no matrix pack outside these
  two declares a profile variable, which is why the cells exist (`PDR-0074`).
- **Provenance:** `PDR-0075` (the design call, incl. the item-layout fork it filed as
  `hamlet-1ad6383186`) · `PDR-0066` (the declaration returns where it can reach a field) ·
  `PDR-0047` / `PDR-0045` · `PDR-0037` (record-then-bind) · `hamlet-f0ed709ecf` (unit 3)
- **Surface:** the compiled observation fields for VFS **profile** variables
  (`vfs_profiles.yaml` `global_profile` / `agent_profile` / `item_profiles`), the runtime path
  that assembles them, and the authoring side: `semantic_type` (required, closed vocabulary,
  `bars` reserved) on global and agent profile variables.

**Oracle behaviour (verified at `4222a917`, 2026-08-17, through the oracle worktree).** Every
exposed profile variable is flattened into ONE compiled field `obs_vfs` (`scope="agent"`,
`semantic_type="custom"`, width = global + agent + slots × max-profile-width), and one
engine-written registry primitive of the same name is minted for it (`build_vfs_variables`),
which the runtime then bypasses: `_build_observation_field_from_vfs` branches on
`field_name != "obs_vfs"` and, for that name, calls `build_vfs_observation` directly against
the compiled `VFSObservationSpec`. Measured: `items_smoke` L0_smoke — 9 fields, `total_dims`
61, `obs_vfs` width 3 (two item profiles × one exposed variable each, 3 slots), registry
primitives include `obs_vfs`; `effects_smoke` L0_effects — 8 fields, `total_dims` 59,
`obs_vfs` width 1 (global `day_count`), registry variables include both `obs_vfs` and
`day_count`. Hashes at the tag: items_smoke `observation_schema_hash 7f18e4477f25…`,
`variable_schema_hash 966d7310298a…`, `vfs_hash 38e5f3407672…`, `environment_hash
e36047b5ff6c…`; effects_smoke `3f2e8c5d01c7…` / `fa1dbe44459a…` / `aac239a3f749…` /
`4fd25f6ff6de…`. The three profile variable classes carry **no** `semantic_type` (removed by
DIV-005 because the block carried one value).

**Intended new behaviour (`PDR-0075`).** One `ObservationField` per exposed global profile
variable (`scope="global"`) and per exposed agent profile variable (`scope="agent"`), each
named after its variable and carrying the **author's declared** `semantic_type`; where any
item profile exposes variables, ONE compiler-emitted feature field `obs_item_slots`
(`semantic_type="custom"`, same slot × max-width layout as the old sub-block). `obs_vfs` and
its primitive are gone. The runtime reads every field by the compiled mirror's
`source_variable` and the variable's **declared scope** — no name branch; `obs_item_slots` is
synced each tick like the other primitives. `total_dims` unchanged by construction; every
value at the same offset.

**Diff shape — PREDICTED at `tag-stamped`, MEASURED at `built` (matrix run `20260817-091351` agreed with every row)** against a git worktree
at the pre-cut commit compiled beside the live tree, on both profile packs and all five
`default_curriculum` levels:

| hash | family | moves (profile packs) | why |
|---|---|---|---|
| `observation_schema_hash` | DERIVED | yes | the field list changes: `obs_vfs` → per-variable fields (+ `obs_item_slots`) |
| `variable_schema_hash` | DERIVED | yes | the `obs_vfs` primitive disappears; `obs_item_slots` appears where items are exposed |
| `vfs_hash` | DERIVED | yes | composite of the two above |
| `environment_hash` | RAW | **no** | `environment.yaml` is untouched by this cut |

`default_curriculum` and the differential packs: **nothing moves** (they declare no profile
variables), so their sixteen cells must read `AGREE` with no declaration.

**Harness adjudication.** The four profile-variable cells bind
`RegisteredHashDivergence(register_ref="DIV-006", hash_fields=(observation_schema_hash,
variable_schema_hash, vfs_hash))` — the measured set, exactly — with every stream byte-exact.
The frozen fixtures for the two packs stay at the pre-cut `vfs_profiles.yaml` (no
`semantic_type` key on global/agent variables), so those four cells also declare
`pack_divergence="DIV-006"`; every other fixture stays a byte copy and declares nothing. Any
fourth mover is `HASH_MISMATCH`; a declared field that does not move is
`REGISTERED_DIVERGENCE_ABSENT`; any stream difference is `DIVERGE` — all red.

**Superseded 2026-08-23 (DIV-009):** "every other fixture stays a byte copy and declares
nothing" no longer holds — the sixteen standing/differential cells now bind DIV-009. This
entry's own field set and binding on the four profile cells are unchanged; DIV-009 adds a
second, disjoint entry (`_DIV009_PROFILE`) alongside this one on those same four cells.

**Retire this entry** at the next forward move of the tag.

---

## DIV-007 — `levels/*/brain.yaml` becomes a loaded surface; items_smoke's stale, never-loaded stub is deleted from the live pack and survives in the frozen fixture

- **Status:** `built` (2026-08-22 — cut with the PDR-0027 level-override; entry written at the
  cut, not before, because the drift was DISCOVERED by the pack-freeze test rather than
  predicted: the stub predates the register and nothing documented its existence)
- **Harness shape: pack-drift-only.** No hash divergence, no stream divergence — the two
  `items_smoke` cells declare `pack_divergence="DIV-007"` and must still read `AGREE` on
  every hash DIV-006 does not already cover and on every stream.
- **Provenance:** `hamlet-0d0115383e` (the level-override unit) · `PDR-0027` (the design call)
  · `PDR-0108` (the scope decision that scheduled it) · `hamlet-2090c9f16d` (the pack-freeze
  mechanism this entry feeds)
- **Surface:** the loader's file set for `levels/<level>/` — `brain.yaml` joins it as an
  OPTIONAL complete per-level brain (PDR-0027).

**Oracle behaviour (verified against the tag's loader source).** At `oracle-2026-08-17` the
level loader reads exactly `curriculum.yaml`, `bars.yaml`, `affordances.yaml`,
`training.yaml`, `drive.yaml`, and optional `items.yaml` — a `levels/*/brain.yaml` is
**never opened**. `configs/test/items_smoke/levels/L0_smoke/brain.yaml` was a stale stub from
an older layout (q-learning scalars duplicated in `training.yaml`, its own header calling
brain.yaml the "single source of truth" it was not), inert on the oracle side by
construction.

**Intended new behaviour (`PDR-0027`).** A present `levels/<level>/brain.yaml` is loaded as a
COMPLETE `BrainConfig` and replaces the pack brain for that level; a malformed one fails
Stage 1 loudly. The stale stub is therefore deleted from the live pack — zero-backcompat:
old configs fail loudly, they are not accommodated.

**Diff shape.** Input-only: `pack_drift` reports `only_in_frozen: [levels/L0_smoke/brain.yaml]`
for `configs/test/items_smoke`. The old side reads the frozen pack (stub present, ignored by
the old loader); the new side reads the live pack (stub gone). Same universe on both sides;
every hash outside DIV-006's declared set identical, every stream byte-exact.

**Harness adjudication.** The two `items_smoke` cells (`items_smoke:L0_smoke:{cpu,cuda}:seed42`)
bind `pack_divergence="DIV-007"` alongside their existing DIV-006 hash declaration. Any
stream difference is `DIVERGE`; any hash mover outside DIV-006's set is `HASH_MISMATCH` —
all red.

**Superseded 2026-08-23 (DIV-009):** "any hash mover outside DIV-006's set is `HASH_MISMATCH`"
no longer holds on its own — these two cells also bind `_DIV009_PROFILE`, so the set a mover
must fall inside is DIV-006's ∪ DIV-009's, not DIV-006's alone. This entry's own field set and
`pack_divergence="DIV-007"` binding are unchanged.

**Amended 2026-08-26 (DIV-008).** `items_smoke` now drifts on a SECOND row this entry does
not describe: `differing: effects.yaml`, from Task 10's required `max_active_effects` budget.
`pack_divergence` is one string per cell and these two cells still name DIV-007, so that row
is enumerated in DIV-008's per-pack drift table instead — no drift is blessed by a
declaration that does not describe it. This entry's own row (`only_in_frozen:
levels/L0_smoke/brain.yaml`) and its binding are unchanged.

**Retire this entry** at the next forward move of the tag (re-freezing the fixture as a byte
copy dissolves the drift).

---

## DIV-008 — Token observations replace the superset+mask ABI: the `obs` stream diverges on every cell, world dynamics under scripted actions do not

- **Status:** `built` (2026-08-26, unit 3 Task 11 — **measured and bound on all twenty
  cells**. The cut landed at Task 10 (`4dde71a2`); the L3 temporal declaration
  (`9563dc45`, `hamlet-02684be106`) landed before the binding so it was measured against a
  stable tree. Full 20-cell matrix, both modes, **exit 0** — acceptance runs at the clean
  tree (`new_dirty: false`): `--scripted` `20260826-172349` and plain (seeded-random)
  `20260826-172441`; the first-binding runs `20260826-171622` / `20260826-171731` are
  verdict-for-verdict identical and are the measurement this entry's tables were taken
  from. All ten CPU cells
  `DIVERGED_AS_REGISTERED` with `shape: "hash+stream"`, naming `["DIV-009", "DIV-010",
  "DIV-008"]`, exactly eight movers each, and **`obs` the only diverging stream on every
  cell in both modes**; all ten CUDA cells `SKIPPED` (`--cuda` not passed). The measured
  numbers, the §5 finding and the two retirements this entry absorbs are below.)
- **Previously:** `registered` (2026-08-24 — entry recorded, per `PDR-0037`'s record-then-bind
  order, at unit 3's Task 4 (`hamlet-fa6bb6da4a`). **No matrix cell binds it yet**: every
  cell's `hash_divergences` and `stream_divergence` stay as they are today; this entry adds
  no cell declaration and flips no verdict. This is deliberately earlier than DIV-006's
  pre-built `tag-stamped` state — DIV-006 verified oracle behaviour against the tagged commit
  before its own code changed. Here there is not yet a new side to verify against at all:
  this entry is written before Task 5 (authoring-surface prerequisites) or Task 6 (the
  TokenSpec artifact itself) land. The hash movers named below are the approved design's
  **prediction** (spec §5, ruled by the owner), not a measurement — measurement, exact hash
  values, and the per-cell binding are Task 11's job, following DIV-004's own
  predict-then-measure discipline. Two things landed before this entry, from two different
  units: **unit 1** (migration sequencing step 1, spec §6) built the class this entry names
  — `RegisteredStreamDivergence` in `src/townlet/oracle/matrix.py`, whose own docstring names
  DIV-008 as the entry it was built for and states "DIV-008 binds both, under one
  register_ref"; **this unit's own Task 3** (`hamlet-fa6bb6da4a`, the comment-234/242 harness
  carry-forward batch, landed immediately before this entry within unit 3) then wired the
  small fixes those reviews named. Machinery built-and-unbound is exactly the gap
  `registered` names.)
- **Harness shape: hash-only** (`RegisteredHashDivergence` — the provenance-hash movers)
- **Harness shape: stream-scoped** (`RegisteredStreamDivergence` — the `obs` stream; unit 1's
  third divergence shape, built for exactly this entry). This entry carries **two**
  machine-readable `Harness shape:` lines, not one — the first register entry to bind both
  constructs under a single `register_ref`, which `compare_traces` itself labels the
  `"hash+stream"` shape (`trace_io.py`, the `shape` field of a `DIVERGED_AS_REGISTERED`
  detail).
- **Provenance:** `hamlet-fa6bb6da4a` (unit 3, this entry's ticket) ·
  `docs/superpowers/specs/2026-08-22-token-observation-representation-design.md` §§1-6 (the
  approved design; §5 "Transfer, provenance, and the oracle" is this entry's direct source)
  · `PDR-0037` (record-then-bind order) · `PDR-0033` (narrowness of a registered divergence
  declaration, enforced both directions in `compare_traces`) · `hamlet-56ec575ae2` (the
  binding mechanism DIV-NNN entries attach to) · `hamlet-d97b4d6b4a` (`exposed_to` fails open
  to `["agent"]`; discharged at this unit as explicit exposure) · `hamlet-bf42ac60b5` (every
  exposed profile variable ships raw today; the structural root the required-normalization-
  at-exposure rule fixes) · comment-234/comment-242 (the unit-1/unit-2 review items this
  ticket's Task 3 landed immediately before this entry, including the env-internal-RNG
  caveat below, item 3)
- **Surface:** the entire observation ABI: `ObservationSpec` (compiled artifact),
  `ObservationField` (compiled DTO), the VFS `ObservationField` mirror and
  `VFSObservationSpec`, the fixed-width superset + per-level activity mask mechanism
  (`ObservationActivity`, `curriculum_active`), the raster/window/temporal encoders, and the
  authoring surface `exposed_to` (currently fails open to `["agent"]` in every
  `vfs_profiles.yaml` block) and profile-variable normalization (currently absent —
  `VariableDef.normalization` is declared but consumed by nothing at runtime).

**Oracle behaviour (verified against the tagged commit's source and this repo's own
teaching docs, 2026-08-24).** The current system is the fixed-width superset with a
per-level activity mask that `CLAUDE.md`'s "State Representation" section documents as
current: `ObservationSpec.total_dims` is identical across every level in a pack (the
mechanism behind cross-level transfer), inactive slots are held at zero rather than
removed, and `observation_schema_hash`/`vfs_hash` are computed over that fixed-vocabulary
spec (14 affordances, engine-published raster blocks `grid_encoding`/`local_window`/
`temporal`/`affordance_at_position`). Two authoring gaps ride along, both named in the
design's §2 and both dying at this cut: (1) `exposed_to` fails OPEN to `["agent"]` in all
three `vfs_profiles.yaml` blocks today — a No-Defaults violation on exactly the field that
will size the observation (`hamlet-d97b4d6b4a`); (2) `VariableDef.normalization` is declared
authoring surface consumed by nothing at runtime, and exposed profile variables have no
normalization field at all, so every exposed profile variable ships raw
(`hamlet-bf42ac60b5`). Both gaps are inert today precisely because nothing downstream reads
them — which is also why removing/repurposing them is a provenance-hash question, not a
behaviour one.

**Intended new behaviour (spec §§1-2, ruled).** `TokenSpec` replaces `ObservationSpec` as
the compiler's product: a type roster (7 live engine types, canonical order), per-type
payload schema, and per-type compiled capacity with deterministic slot bindings — content
becomes per-universe, the type system stays fixed. The activity mask and its whole
mechanism die (`curriculum_active` on both DTOs, `ObservationActivity`, the
allocated-vs-active framing `CLAUDE.md` currently teaches); `exposed_to` becomes explicit
(the default-injection validators are deleted — empty means unexposed, every exposure is
authored); exposed `vfs_profiles.yaml` variables gain a **required** `normalization` field;
`VariableDef.normalization` — consumed by nothing — is deleted with the cut. The VFS
`ObservationField` mirror and `VFSObservationSpec` die entirely: the mirror was always
derived *from* `ObservationSpec` one hop downstream, and with `TokenSpec` hashed directly
there is nothing left for it to mirror.

**What diverges — MEASURED at Task 11 (2026-08-26), by the DIV-009 worktree method.**
Method: the harness's own comparison is the measurement — the oracle worktree at
`4222a917` reading `oracle_fixtures/<pack>` versus the live tree reading `configs/<pack>`,
which is precisely the old-tree/new-tree pair the DIV-009 entry established, run per cell
rather than per representative pack. **The measured mover set is UNIFORM across all ten
executed cells** (five `default_curriculum` levels, three `differential/div003_*`,
`items_smoke`, `effects_smoke`) and identical in both modes — eight fields:

```
actions_hash  layout_hash  observation_schema_hash  pack_brain_hash
token_type_schema_hash  transition_graph_hash  variable_schema_hash  vfs_hash
```

Three of those eight are not this entry's (`actions_hash`, `pack_brain_hash`,
`transition_graph_hash` — DIV-009's pre-token-cut drift, unmoved by this cut: Task 10's
pre/post probe shows both `actions_hash` and `transition_graph_hash` byte-identical across
the cut on every level; they differ here only because the oracle is a much older tree).
**This entry declares the other five**, and they are the set bound in
`src/townlet/oracle/matrix.py` as `_DIV008_HASH`:

| field | family | why it moves for THIS cut |
|---|---|---|
| `observation_schema_hash` | DERIVED | redefined over the TokenSpec type-schema + slot-binding content (spec §5); the artifact it was computed over no longer exists in its old form |
| `variable_schema_hash` | DERIVED | **a different deletion from this entry's headline, and the one easiest to miss.** `build_vfs_variables` stopped minting the engine-side observation primitives: `default_curriculum` loses fourteen agent-scoped `VariableDef`s (`obs_grid_encoding`, `obs_local_window`, `obs_position`, `obs_velocity`, eight `obs_meter_*`, `obs_affordance_at_position`, `obs_temporal`). `variable_schema_hash` hashes that canonical list directly (`schema_hashes.py:31`). Note the *predicted* cause — `VariableDef` losing its inert `normalization` field — is not the operative one; the primitives are |
| `vfs_hash` | DERIVED | composite: **slots 1 AND 2** of `compute_vfs_hash` both move (the predicted reasoning named slot 2 only) |
| `token_type_schema_hash` | DERIVED | the transfer contract — per-type payload feature names, filler kinds, encoding version. `<absent>` on the oracle side, which predates the field. Inherited from the retired DIV-011 |
| `layout_hash` | DERIVED | the flat-net contract — type order, capacities, slot bindings, `total_dims`. `<absent>` on the oracle side. Inherited from the retired DIV-011 |

**Predicted-vs-measured, recorded because the prediction was written first (DIV-004's
discipline).** The prediction named `obs`, `observation_schema_hash` and `vfs_hash`
correctly, and left `variable_schema_hash` explicitly open ("measured at binding, not
asserted here"). It moves — but for a cause the prediction did not name. That is the
`PDR-0033` narrowness trap working as intended: an undeclared mover would have kept every
cell red, and the honest fix was to measure the cause, not to widen the set until it
passed.

**What was predicted and stands:**

- **The `obs` trace stream, on every cell**, bound via `RegisteredStreamDivergence`
  (`streams=("obs",)`). Tokens change the observation's shape and content on every pack —
  this is not a hash-only provenance move, the stream's actual bytes (and very likely its
  shape) change, which is exactly the shape the shape/dtype preflight in `compare_traces`
  exists to tolerate for a *declared* stream rather than crash on.
- **`observation_schema_hash`** — redefined over the TokenSpec type-schema + slot-binding
  content (spec §5) rather than over `ObservationSpec`; moves on every pack, once, by
  construction (the artifact it is computed over no longer exists in its old form).
- **`vfs_hash`** — a slot-2 composition consequence (spec §5): `vfs_hash` keeps its name and
  four-term composition (`compute_vfs_hash(variable_schema_hash, observation_schema_hash,
  action_schema_hash, transition_graph_hash)`, `compiler.py:419`), but the TokenSpec-derived
  `observation_schema_hash` now occupies slot 2 of that same composition, so `vfs_hash`
  moves on every pack as a direct consequence — the same "composite moves because an input
  moves" reasoning DIV-004 and DIV-010 already established for this hash.
- **`variable_schema_hash`** — was left open at `registered` and is now measured (above): it
  moves, for the engine-minted-primitive deletion rather than the predicted
  `VariableDef.normalization` removal.

**What must NOT diverge (the criterion) — MEASURED, and it HOLDS.** Under scripted actions,
`actions`/`rewards`/`dones` stay byte-exact on every cell — none of the three is declared in
the `RegisteredStreamDivergence`, so `compare_traces` holds them to the same byte-exact bar
every undeclared stream gets. **Tokens change what agents see, never what the world does.**
This is the adjudication criterion spec §5 states directly.

**The evidence, stated in the form that distinguishes it from the absent-data error a
controller correction had to make against the Task-10 report.** In runs `20260826-171622`
(`--scripted`) and `20260826-171731` (plain), every executed cell's verdict is
`DIVERGED_AS_REGISTERED` with `shape: "hash+stream"` — which is reachable ONLY after the
hash gate has been cleared and the full per-stream loop has run, since `compare_traces`
returns `HASH_MISMATCH` before `declared_streams` is even computed. Each such verdict's
detail carries a **`streams` key that is PRESENT and contains exactly `{"obs"}`**, with
`diff_entries: 101` (the reset observation plus all 100 steps). `actions`, `dones` and
`rewards` are absent from `findings` *in a verdict that reached stream comparison* — that
is the byte-exactness proof, and it is the opposite of an absent `streams` key, which means
never compared:

| cell | mode(s) | verdict | diverging streams | obs shape old → new |
|---|---|---|---|---|
| `default_curriculum:L0_0_minimal:cpu` | scripted + plain | `DIVERGED_AS_REGISTERED` hash+stream | `{obs}` only | `(4,120)` → `(4,1132)` |
| `default_curriculum:L0_5_dual_resource:cpu` | scripted + plain | same | `{obs}` only | `(4,120)` → `(4,1132)` |
| `default_curriculum:L1_full_observability:cpu` | scripted + plain | same | `{obs}` only | `(4,120)` → `(4,1132)` |
| `default_curriculum:L2_partial_observability:cpu` | scripted + plain | same | `{obs}` only | `(4,120)` → `(4,1132)` |
| `default_curriculum:L3_temporal_mechanics:cpu` | scripted + plain | same | `{obs}` only | `(4,120)` → `(4,1132)` |
| `div003_scaled:L1_full_observability:cpu` | scripted + plain | same | `{obs}` only | `(4,122)` → `(4,1132)` |
| `div003_cubic_partial:L2_partial_observability:cpu` | scripted + plain | same | `{obs}` only | `(4,350)` → `(4,1132)` |
| `div003_rect:L1_full_observability:cpu` | scripted + plain | same | `{obs}` only | `(4,104)` → `(4,1132)` |
| `items_smoke:L0_smoke:cpu` | scripted + plain | same | `{obs}` only | `(4,61)` → `(4,1121)` |
| `effects_smoke:L0_effects:cpu` | scripted + plain | same | `{obs}` only | `(4,59)` → `(4,272)` |

Ten of ten. At Task 10 the criterion was genuinely verified on **two** cells only (the two
that happened to clear the hash gate); binding this entry is what let the other eight reach
the stream comparison, which is exactly the record-then-bind order `PDR-0037` prescribes.

**Env-internal-RNG caveat (comment-234 item 3, verbatim requirement).** Scripted mode
removes the action-draw RNG coupling — actions are replayed from a file rather than drawn
from the run's RNG stream, which is what makes an `actions`/`rewards`/`dones` byte-exact
comparison meaningful under identical actions in the first place. If `env.step` ever starts
consuming global RNG for something other than the action draw (a stochastic transition, a
randomized effect, anything reading the shared RNG stream mid-step), old and new decorrelate
**env-internally**, even under byte-identical scripted actions. The failure direction this
produces is red — a `DIVERGE` on `actions`/`rewards`/`dones` — never a false green; but a
future env change of that shape must be diagnosed as an RNG-coupling regression, not
misread as a defect in the token cut itself. **This entry's binding is therefore adjudicated
in `--scripted` mode** — it is the mode under which `actions`/`rewards`/`dones` byte-exactness
is a meaningful bar in the first place. What plain (seeded-random) mode is expected to do
post-cut is **not asserted here**: if plain mode's action draw shifts position relative to
the old side's RNG stream for any reason connected to the cut, a plain-mode `DIVERGE` on
`actions`/`rewards`/`dones` would need the same care this caveat asks for generally, and
Task 11 is where that gets established, not this entry. The scripted driver's RNG-call-order
spot-check (unit 1, spec §6 step 1) is the check that would catch such a change landing.

**Plain-mode ruling (Task 11, the question the paragraph above left open).** MEASURED: plain
(seeded-random) mode is **green too** — run `20260826-171731`, exit 0, all ten CPU cells
`DIVERGED_AS_REGISTERED` with `obs` the sole diverging stream, verdict-for-verdict identical
to the scripted run. The cut therefore does **not** shift the action draw's position in
either side's RNG stream: each side draws its own actions independently and the two `actions`
streams still match byte-for-byte. Consequence for the matrix: **`Cell.scripted_actions`
stays `False` on every DIV-008 cell.** Forcing it true would make the criterion run the
default but would also make a plain-mode run unexpressible without editing the matrix, and
the measurement says the weaker mode already passes. `--scripted` remains the stronger
verification form (it removes the action-draw RNG coupling entirely) and is the mode this
entry's binding is *adjudicated* in; plain mode is recorded beside it. A future plain-mode
`DIVERGE` on `actions`/`rewards`/`dones` is red and must be diagnosed as an RNG-coupling
regression, per the caveat above — not as a defect in the token cut.

**Pack drift under this entry (the INPUT delta, distinct from the output deltas above).**
`pack_divergence` is a separate declaration axis from `hash_divergences` and
`stream_divergence`: it names the entry under which a cell's FROZEN fixture may differ from
its live pack. Measured at HEAD with `pack_drift`, 2026-08-26 — the complete delta for every
matrix pack, with the entry each row is declared under:

| live pack | delta vs `oracle_fixtures/` | declared under | cause |
|---|---|---|---|
| `configs/default_curriculum` | `differing: vfs_profiles.yaml` | **DIV-008** | the L3 temporal declaration (`9563dc45`, `hamlet-02684be106`): a `time_of_day_phase` global profile variable over the ambient `tick` with `cyclical_sin_cos`. It is the first pack-side consequence of this cut — the engine's temporal observation block died with the raster ABI and the replacement is authored, not built in |
| `configs/differential/div003_{scaled,cubic_partial,rect}` | `differing: vfs_profiles.yaml` | **DIV-008** | the same file, synced byte-identically: a differential pack is the base pack with exactly one declared axis moved, so it must track the base on everything else (`test_differential_packs_vary_only_the_declared_axis`). One declaration, four packs |
| `configs/test/effects_smoke` | `differing: effects.yaml, vfs_profiles.yaml` | **DIV-008** | `effects.yaml`: the required `max_active_effects` budget (Task 10 Phase 1 item 3 — required iff effects are declared). `vfs_profiles.yaml`: the fixture is held at the pre-`semantic_type` schema, which DIV-006 originally declared; DIV-006 is retired at this cut, so the row moves here |
| `configs/test/items_smoke` | `only_in_frozen: levels/L0_smoke/brain.yaml` | DIV-007 | the stale, never-loaded stub the `PDR-0027` level-override cut deleted from the live pack. **DIV-007 survives and keeps this row** |
| `configs/test/items_smoke` | `differing: effects.yaml` | **DIV-008** | the same `max_active_effects` requirement. `pack_divergence` is a single string per cell, so these two cells name DIV-007; this row is enumerated here so no drift is blessed by a declaration that does not describe it |

**What that costs, recorded because DIV-004 recorded the same cost and it is real.**
`pack_divergence` is a **boolean gate**: declaring it blesses *arbitrary* drift between
fixture and live pack, not merely the rows above. With all twenty cells now declaring one,
the pack-freeze guard built at `49bdf28e` for `hamlet-2090c9f16d` is **armed on zero cells**
for as long as this entry is open — the same loss DIV-004 took, dissolving the same way, at
the next forward move of the tag. Naming it here is the substitute for the guard: the table
above is the complete delta at binding time, so a future reader can diff against it.

**Fixture-exposure note.** The explicit-exposure rule is a **new-side** rule only: the old
side runs frozen `4222a917` code, which fails `exposed_to` open to `["agent"]` regardless of
what a pack declares, so the note's force comes entirely from what the **live** matrix packs
declare, not the frozen `oracle_fixtures/` copies. Verified both sides, 2026-08-24: zero
`exposed_to` hits under `oracle_fixtures/` (`grep -rn exposed_to oracle_fixtures/`); under
`configs/`, `exposed_to` appears only in `configs/trial_f_durability`,
`configs/test/token_set_smoke`, and `configs/reference/config-complete.yaml` — **none of
them a matrix pack** (the twenty cells run `default_curriculum`, the three `differential/
div003_*` packs, `test/items_smoke`, `test/effects_smoke`). So every matrix pack's live
`vfs_profiles.yaml` declares no `exposed_to` today, on both sides of the cut. Post-cut, once
the default-injection validators are deleted and an empty `exposed_to` means unexposed rather
than fails-open-to-`["agent"]`, every profile variable in every one of these twenty cells'
live packs becomes unexposed by construction — not because any pack drifted from its fixture,
but because the explicit-exposure rule (spec §2, "Exposure is explicit at the cut") changes
what an *absent* declaration means, on the new side only. This is part of the registered
observation divergence above (it manifests as part of the `obs` stream's — and
`variable_element` token census's — content changing), not a separate pack-drift finding: no
`pack_divergence` declaration is implied or needed by this note on its own account.

**Harness adjudication (mechanics, matched to code as it stands after Task 3).** Per
`compare_traces` (`src/townlet/oracle/trace_io.py`): hash and stream adjudication are
**per-stream, non-short-circuiting** — every one of the four trace streams (`obs`,
`actions`, `dones`, `rewards`) is compared in full before a verdict is returned, so a
registered `obs` divergence can never mask an `actions`/`rewards`/`dones` verdict (SA-C1).
A shape/dtype mismatch on a stream is recorded by a **preflight** before any byte
comparison is attempted (`_stream_steps` byte-diff cannot run across differing shapes);
that preflight records the same way whether or not the stream is declared, but only a
*declared* stream's shape-changed finding is tolerated downstream — an undeclared stream
whose shape changed still lands in `undeclared_streams` and fails the cell exactly like any
other undeclared divergence. Once bound: any stream diverging outside `{"obs"}` is
`DIVERGE`; `obs` failing to diverge anywhere in the trace is `REGISTERED_DIVERGENCE_ABSENT`
(a stale entry); on the hash side, any hash mover outside this entry's declared set (unioned
with whatever else binds the same cell) is `HASH_MISMATCH`, and a declared hash field that
does not move is `REGISTERED_DIVERGENCE_ABSENT` — all red, the same treatment every other
hash-only and stream-scoped declaration gets.

**Reconciliation with DIV-006, DIV-009, DIV-010 and DIV-011 — RULED at Task 11.**
The discriminator applied to each: *does this entry's own cause independently move the
field, and does the other entry still describe something that exists?*

- **DIV-006 → `retired`.** Its declared new-side surface (the `obs_vfs` block split into one
  `ObservationField` per exposed profile variable, plus the `obs_item_slots` feature) was
  **deleted** by this cut — `ObservationSpec`, `ObservationField` and `VFSObservationSpec`
  no longer exist. Its three declared hashes still move on the profile cells, but for this
  entry's cause. Keeping it bound would certify a surface that has no referent on the new
  side; that is not narrowness, it is redundancy pointing at a ghost. Its binding is removed
  and those three fields are declared here, uniformly on all twenty cells.
- **DIV-011 → `retired` into this entry, by its own pre-registered condition** ("retire when
  DIV-008 lands … the token hashes become part of that registered surface"). Once the
  TokenSpec IS the observation ABI rather than an alongside emission,
  `token_type_schema_hash` and `layout_hash` stop being a fact about a parallel artifact and
  become this entry's own provenance. Both fields move on every cell against the pinned
  oracle (`<absent>` on the old side), so the declaration is inherited unchanged in content.
- **DIV-010 → stays `built` and stays bound, superseded in place rather than retired.** Its
  own retirement clause names this cut, but the lifecycle's bar for `retired` is "the
  oracle-side surface is gone, or the divergence dissolved", and neither holds: the engine
  tick `VariableDef` is still injected into every compiled universe and still moves
  `variable_schema_hash` against the frozen oracle, independent of anything the token cut
  did. Both entries declare `variable_schema_hash` and `vfs_hash`. That overlap is legal and
  correct here — the register's own rule prefers a disjoint set only when the causes are
  *separable*, and these are not: DIV-010's cause ADDS one entry to the canonical
  `VariableDef` list while this cut REMOVES fourteen. Two causes genuinely moving one hash
  is the DIV-010 composing shape, which is where that shape came from.
- **DIV-009 → unchanged.** Its `actions_hash` / `pack_brain_hash` / `transition_graph_hash`
  movers are on a disjoint surface (VTC / actions DTO / brain-fork lineage), and Task 10's
  pre/post probe confirms this cut moves neither `actions_hash` nor `transition_graph_hash`
  on any pack. `_DIV009_PROFILE` keeps its narrowed three-field set; it was narrowed to be
  disjoint from DIV-006's fields, and it is disjoint from this entry's too, so no re-cut is
  needed.

Net binding after the ruling — the union equals the measured eight movers exactly, on both
blocks, with each entry's own fields all moving:

| block | cells | `hash_divergences` | `stream_divergence` | `pack_divergence` |
|---|---|---|---|---|
| standing | 5 `default_curriculum` levels × cpu/cuda | `(_DIV009_STANDING, _DIV010, _DIV008_HASH)` | `_DIV008_STREAM` | `DIV-008` |
| differential | 3 `div003_*` × cpu/cuda | `(_DIV009_STANDING, _DIV010, _DIV008_HASH)` | `_DIV008_STREAM` | `DIV-008` |
| profile | `items_smoke`, `effects_smoke` × cpu/cuda | `(_DIV009_PROFILE, _DIV010, _DIV008_HASH)` | `_DIV008_STREAM` | `DIV-007` / `DIV-008` |

**The fixture-refusal decision point this entry's task pre-registered: REACHED, did not
trigger.** The Task-11 brief pre-registered a `PDR-0074` oracle-move-forward "if any fixture
cell refuses on required-field grounds" — the candidate being `effects_smoke`, a frozen
fixture that declares effects and cannot gain the now-required `max_active_effects` block.
It does not refuse, for a structural reason worth writing down: the frozen fixture is read
by the **old** side, running frozen `4222a917` code, which never required the field. Only
the live pack meets the new requirement, and Task 10 gave it one. No fixture was edited, no
oracle move-forward was executed, and nothing under `.oracle/` or `oracle_fixtures/` was
touched at this task.

**Retire this entry** — not expected soon: this is the new observation ABI, not a
transitional one. Retirement follows the same rule as every other entry: when the oracle is
re-tagged past the token cut (folding TokenSpec's provenance behaviour into the frozen
spec itself), or if the divergence otherwise dissolves.

---

## DIV-009 — Pre-token-cut compiler-surface hash drift: six Phase B landings moved provenance, behaviour did not

- **Status:** `built` (2026-08-23 — measured and bound; full 20-cell CPU+CUDA matrix run
  `20260823-024115`, **exit 0**: ten standing/differential CPU cells
  `DIVERGED_AS_REGISTERED` naming `["DIV-009"]`, the four profile CPU cells
  `DIVERGED_AS_REGISTERED` naming `["DIV-006", "DIV-009"]` (`pack_divergence="DIV-007"` on
  the two `items_smoke` cells adjudicates separately and does not appear in
  `register_refs`, which names only hash/stream declarations), every stream byte-identical;
  all ten CUDA cells `SKIPPED`. Superseded the unit-1 diagnostic runs `20260823-000034`
  (plain mode) and `20260823-000700` (scripted mode), both `HASH_MISMATCH` on all 10 CPU
  cells with zero register refs — those runs found the drift this entry now names, but
  short-circuited before any stream comparison because nothing was registered yet.)
- **Harness shape: hash-only** (`RegisteredHashDivergence`)
- **Provenance:** `hamlet-5cc071f4b6` (this ticket) · `PDR-0037` (record-then-bind order,
  observed here in the breach — the six landings shipped before this entry existed, which is
  exactly the process failure `PDR-0028`'s "Adding an entry" section warns is a finding, not
  normal) · `hamlet-ef6699ab2a` (`7cbfbff8`) · `hamlet-f46e2b381a` (`cd3557b6`) ·
  `hamlet-175bff4ed5` (`8868f237`) · `hamlet-39e1fe3c6d` / `PDR-0076` (`ebd16fce`) ·
  `hamlet-0d0115383e` / `PDR-0027` (`d60104f0`, `390769af`) · `hamlet-a141ab5db3` /
  `hamlet-cbb747a51e` (`03764c6b`)
- **Surface:** the compiler-internal surfaces the six landings touched — VTC occupancy/bounds
  compilation, the actions schema DTO, the compiled-universe schema (a new hash field), and
  the universe cache write path. None of the six edits a `default_curriculum`,
  `configs/differential/div003_rect`, or `configs/test/items_smoke` YAML file directly (the
  one exception, `0b659130`, is investigated below and found NOT to be a mover).

**Why one entry and not six.** All six commits landed as accepted Phase B work between the
`oracle-2026-08-17` tag and this ticket, each a genuine behavioural fix or a genuine new
lineage field — DIV-004's shape exactly: the authoring/compiler surface moved, the register
entry did not follow it. Three cuts of one continuous gap, not three findings.

**Measurement method.** DIV-004's worktree method, extended in two ways this entry needed:

1. **What the harness actually compares is not "commit N vs commit N-1".** The harness
   compiles the OLD side with `old_src` = the code frozen in the `.oracle/oracle-2026-08-17`
   worktree (pinned at `4222a917`, never moves) against `old_pack_root` =
   `oracle_fixtures/<pack>` **as currently committed** (`harness.py`
   `ORACLE_PACK_ROOT`/`old_pack_root=repo_root / ORACLE_PACK_ROOT`); the NEW side compiles the
   live tree's own code against `configs/<pack>`. A naive commit-to-commit bisection that
   recompiles both the fixture and the live pack with the SAME (that commit's) code measures
   something else — cumulative code+config drift over time — and can misattribute a mover.
   That happened once here (next point), so the register records it rather than silently
   discarding the false lead.
2. **`0b659130` ("delete the four writerless observation variables") looked like an
   unlisted seventh mover, and is not one.** A same-code bisection (compile `configs/` and
   `oracle_fixtures/` at each commit with THAT commit's code) shows `0b659130` moving
   `environment_hash`, `observation_schema_hash`, `variable_schema_hash`, `vfs_hash` on
   `default_curriculum`/`div003_rect` — because the commit deletes `deficit_energy` /
   `deficit_satiation` / `time_since_last_eat` / `time_since_last_sleep` from
   `configs/default_curriculum/environment.yaml`. But the SAME commit re-freezes
   `oracle_fixtures/configs/default_curriculum/environment.yaml` identically (verified:
   `git show --stat 0b659130` touches both paths). Compiled with the ACTUAL old
   code+fixture vs new code+live pair, the two sides move together and the mismatch this
   produces is empty — confirmed by rerunning the real comparison at `0b659130`'s worktree:
   no field newly mismatches. `0b659130` is investigated and cleared, not silently dropped.

For each of the three representative packs (`configs/default_curriculum` at
`L1_full_observability` for the ten standing cells, `configs/differential/div003_rect` at
`L1_full_observability` for the six differential cells, `configs/test/items_smoke` at
`L0_smoke` for the profile cells), the entry was measured by running the real comparison
(old code + `oracle_fixtures/<pack>`, new code + `configs/<pack>`, both taken from a git
worktree at each commit boundary in `4222a917..HEAD`) at every commit that touches
`src/townlet` or the three probed packs, in chronological order, and recording which
`*_hash` field newly entered the mismatch set. `effects_smoke` was not independently
bisected — `runs/differential/20260823-000034`'s per-cell report shows its mismatched set is
byte-identical to `items_smoke`'s (`actions_hash, observation_schema_hash, pack_brain_hash,
transition_graph_hash, variable_schema_hash, vfs_hash`), and all five `default_curriculum`
levels plus all three differential packs show the identical four-field standing set in that
same report — bisecting one representative per block plus confirming uniformity at HEAD from
the real, already-executed run is DIV-004's own discipline, not a shortcut around it.

**Per-commit table (chronological, `4222a917..HEAD`, real old-code+fixture vs new-code+live comparison):**

| commit | subject | hash field(s) first mismatched | why |
|---|---|---|---|
| `ebd16fce` | feat(obs): the compiled observation field says who fills it — a typed `feature` on the DTO | *(none)* | its own product checkpoint (`62b5424d`) already recorded this: "measured hash-invisible, no register entry" |
| `03764c6b` | fix(universe): agent profiles serialize to cache, and a failed cache write fails compile | *(none)* | cache round-trip / failure-mode fix touches no compiled hash input |
| `7cbfbff8` | fix(vtc): wire affordance occupancy into the transition schedule — contention is authorable from actions.yaml | `actions_hash` | `src/townlet/config/actions_config.py` gains a new field for occupancy/contention; `actions_hash` is a RAW `_compute_pydantic_hash` over the whole `ActionsConfig` (DIV-001's weak-evidence group) and moves for a DTO schema change even though no `actions.yaml` in the three probed packs was edited |
| `cd3557b6` | fix(vtc): clamp_and_validate carries compiled bounds rules — the phase graph stops lying | `transition_graph_hash`, `vfs_hash` | `src/townlet/vfs/schema_hashes.py` and `vtc.py` change what feeds the compiled transition-graph hash directly; `vfs_hash = compute_vfs_hash(variable_schema_hash, observation_schema_hash, action_schema_hash, transition_graph_hash)` (`compiler.py:419`) is a composite over four DERIVED hashes and moves whenever any one of its four inputs does — here, `transition_graph_hash` |
| `8868f237` | fix(vtc): delete the inert social-residue write 'target' field — configs that set it now fail loudly | *(none — measured both ways)* | a same-code consecutive-live bisection reads `moved=[]` at this commit too: none of the three probed packs' compiled output ever carried the deleted `target` field (the generic hasattr canonicalizer this commit touches has nothing to drop for them), so there is no second change to a field `cd3557b6` already moved for these packs to detect |
| `d60104f0` | feat(bac): brain.yaml is level-overridable as a complete file | *(none)* | implements the loading/override mechanism only; the hash field that will carry it does not exist yet |
| `390769af` | feat(bac): a brain fork is stated at load, not discovered at runtime | `pack_brain_hash` | introduces the field itself — `universe/compiled.py` adds `pack_brain_hash` and bumps `COMPILED_SCHEMA_VERSION` to `"1.19"` (comment: *"`pack_brain_hash` is required (PDR-0027 lineage legibility)"*), `compiler.py` stamps it. The OLD side's code (fixed at `4222a917`, pre-dating this commit) has no such attribute at all, so its mere introduction is a mismatch (`old: "<absent>"`) |

Also investigated and cleared as non-movers on the three probed packs (all measured, none
listed in the ticket's six): `0b659130` (above), `6b752b3c`, `7e989e8c`, `9956e95b`,
`883d5472`, `ba2766e6`, and the oracle-internal commits `9e7197e6` / `9a3b1446` / `afa09b81`
/ `922e9bea` / `4fe9a580` (these touch `src/townlet/oracle/`, not the compiler). No commit in
`4222a917..HEAD` outside this table moves a hash on any of the three probed packs.

**Why the profile packs additionally mismatch on `observation_schema_hash` and
`variable_schema_hash`.** Not this entry's doing — `_DIV006` already declares exactly those
two plus `vfs_hash` on the four profile cells (unit 3, PDR-0075), and the measured full
mismatch on `items_smoke` (`actions_hash, observation_schema_hash, pack_brain_hash,
transition_graph_hash, variable_schema_hash, vfs_hash` — six fields, `runs/differential/
20260823-000034`) is exactly DIV-006's three-field set unioned with this table's
`actions_hash` / `pack_brain_hash` / `transition_graph_hash`. `vfs_hash` moves on these cells
for BOTH causes at once (DIV-006's observation-side inputs and DIV-009's
`transition_graph_hash` input, both feeding `compute_vfs_hash`) but is declared once, under
DIV-006, since DIV-006 alone already accounts for it exactly — declaring it a second time
under DIV-009 would widen this entry's field set past what measurement requires it to cover.

**Diff shape.**

| block | cells | hash_fields |
|---|---|---|
| standing (10 cells) | all 5 `default_curriculum` levels × cpu/cuda | `actions_hash, pack_brain_hash, transition_graph_hash, vfs_hash` |
| differential (6 cells) | `div003_scaled, div003_cubic_partial, div003_rect` × cpu/cuda | `actions_hash, pack_brain_hash, transition_graph_hash, vfs_hash` (identical to standing — verified per-cell in `runs/differential/20260823-000034`) |
| profile (4 cells) | `items_smoke, effects_smoke` × cpu/cuda | `actions_hash, pack_brain_hash, transition_graph_hash` (DIV-009's own set; `observation_schema_hash, variable_schema_hash, vfs_hash` already covered by `_DIV006`) |

Every stream (`obs`, `actions`, `dones`, `rewards`) is unaffected by these six landings —
none touches an observation, action, done, or reward computation path a scripted or seeded
trace would see; all six are provenance-only (a schema DTO field, a compiled hash input, a
new lineage-stamp field, a cache-serialization fix). The unit-1 diagnostic runs
(`20260823-000034`, `20260823-000700`) short-circuited on `HASH_MISMATCH` before reaching
stream comparison, so "streams unaffected" is a design inference from reading each commit's
diff, not yet a harness-adjudicated fact — Step 4 of this ticket's task (the full matrix run
with these bindings live) is the first run where the harness actually compares streams on
these ten cells, and its result is recorded in the Status line above.

**Harness adjudication.** `_DIV009_STANDING = RegisteredHashDivergence(register_ref="DIV-009",
hash_fields=("actions_hash", "pack_brain_hash", "transition_graph_hash", "vfs_hash"))` binds
the ten standing and six differential cells alone (`hash_divergences=(_DIV009_STANDING,)`).
`_DIV009_PROFILE = RegisteredHashDivergence(register_ref="DIV-009", hash_fields=("actions_hash",
"pack_brain_hash", "transition_graph_hash"))` binds the four profile cells alongside `_DIV006`
(`hash_divergences=(_DIV006, _DIV009_PROFILE)`, composed per `hamlet-fa6bb6da4a`'s union-exact
rule: the union of every entry's declared fields must equal the observed movers exactly, and
each entry's own fields must all move or that entry alone is stale). No cell declares
`pack_divergence="DIV-009"` — none of the six landings edits a probed pack's YAML in a way
that survives to the live pack while the fixture stays behind (the one that tried,
`0b659130`, re-froze the fixture in the same commit, so there is no pack-drift to declare).
Any hash mover outside a cell's declared union is `HASH_MISMATCH`; a declared field that does
not move is `REGISTERED_DIVERGENCE_ABSENT`; any stream difference is `DIVERGE` — all red,
same as every other hash-only entry.

**Retire this entry** when the oracle is re-tagged past these six landings (or is re-frozen
to absorb them, the way `0b659130`'s companion fixture edit already absorbed its own change).

---

## DIV-010 — Authored temporality (token-obs unit 2): the engine tick variable and derived evaluation marks move compiled provenance, behaviour does not

- **Status:** `built` (2026-08-23 — measured and bound; full 20-cell CPU+CUDA matrix run
  plain-mode and `--scripted` both recorded in the Task 7 report, both **exit 0**: every CPU
  cell `DIVERGED_AS_REGISTERED` naming exactly its composed refs, every stream byte-identical
  across both modes; all ten CUDA cells `SKIPPED`.)
- **Harness shape: hash-only** (`RegisteredHashDivergence`)
- **Provenance:** `hamlet-fa6bb6da4a` (unit 2, parent) · `hamlet-df3a96bbac` (`08a9a122`,
  `c0ffb214` — evaluation marks derive from exposure, write-back skips statics) ·
  `hamlet-5d74335111` (`22caa926` — agent-profile expressions evaluate) · `hamlet-bc0a5deeff`
  (`22caa926` — item-profile expressions refuse at compile) · commits `2d14d5f7`, `f4bdf19c`,
  `15ec46bd`, `08a9a122`, `c0ffb214`, `22caa926` (`11dee204..HEAD`, unit 2 Tasks 3-6)
- **Surface:** `src/townlet/universe/compilers/vfs.py` (the injected `_engine_tick_variable_def`,
  always-on global-scope `VariableDef` id `"tick"`); `src/townlet/universe/compiler.py` /
  `pipeline.py` / `compiled.py` (the `vfs_observation_marks` field renamed and re-derived as
  `vfs_evaluation_marks`); `src/townlet/vfs/evaluator.py` / `profiles.py`
  (agent-profile expression evaluation, item-profile expression refusal, write-back statics
  skip); `src/townlet/environment/vectorized_env.py` (`time_of_day` derives from `global_tick`
  instead of a second counter).

**What changed.** Unit 2 (authored temporality) landed four compiler/runtime surfaces: (1) an
engine-written tick `VariableDef` is now injected into every compiled universe's variable list
— always-on, global scope, `readable_by=["agent","engine"]`, `writable_by=["engine"]`,
ambient in profile expressions as bare `tick`; (2) `vfs_observation_marks` is renamed to
`vfs_evaluation_marks` and its content changes from an observation-derived set to one derived
from `exposed_to` (evaluation-exposure, not observation-exposure); (3) agent-profile
expressions evaluate live (previously dead code — `evaluate_global_profile` reused for agent
profiles per `compiled.py:128-130`), and item-profile expressions now refuse at compile
(scope decision, unit 2 Task 6); (4) `time_of_day` is derived from `global_tick` rather than a
second, independently-advanced counter. Only the first of these — the tick `VariableDef`
injection — feeds a provenance hash: `variable_schema_hash = compute_variable_schema_hash
(vfs_variables)` (`schema_hashes.py:31`) hashes the canonical `VariableDef` list directly, and
a new always-on entry in that list moves it on every compiled universe, with no config
authored anywhere. `vfs_hash = compute_vfs_hash(variable_schema_hash, observation_schema_hash,
action_schema_hash, transition_graph_hash)` (`compiler.py:419`) is a composite over four
derived hashes and moves whenever any one of its inputs does — here, `variable_schema_hash`.
`vfs_evaluation_marks` is stored as its own field on `CompiledUniverse`
(`compiled.py:186`, `pipeline.py:51`) and is never an input to any `*_hash` computation
(verified: zero references to it in `src/townlet/vfs/schema_hashes.py`) — its rename and
content change move **no** hash at all, confirmed by measurement below. Same for (3) and (4):
neither touches a compiled schema or hash input; they change what the runtime *evaluates* and
*derives*, not what the compiler *declares*.

**Measurement method.** Two-worktree probe (baseline = `11dee204`, Task 2's end commit; head =
`HEAD` = `22caa926`), reusing Task 2's `probe.py` (`UniverseCompiler().compile(...)`, dump
every `*_hash` attribute) against the same three representative packs: `configs/
default_curriculum` at `L1_full_observability` (standing), `configs/differential/div003_rect`
at `L1_full_observability` (differential), `configs/test/items_smoke` at `L0_smoke` (profile).
Confirmed first that none of the three probed packs' YAML changed between `11dee204` and
`HEAD` (`git diff --stat 11dee204..HEAD -- configs/default_curriculum configs/test/items_smoke
configs/differential/div003_rect` — empty), so the two-commit compile diff isolates code-only
movement exactly, no oracle-fixture indirection needed (unlike DIV-009, both sides here compile
the SAME live pack content with different code). Then re-ran the probe at each of the six
intermediate commits (`2d14d5f7`, `f4bdf19c`, `15ec46bd`, `08a9a122`, `c0ffb214`, `22caa926`)
against `configs/default_curriculum L1_full_observability` to attribute the movement to its
first mover.

**Per-commit table (chronological, `11dee204..HEAD`, default_curriculum L1_full_observability):**

| commit | subject | hash field(s) first mismatched | why |
|---|---|---|---|
| `2d14d5f7` | feat(vfs): the engine tick variable — always-on, engine-written, ambient in profile expressions | `variable_schema_hash`, `vfs_hash` | injects `_engine_tick_variable_def()` into every universe's `vfs_variables` list; `variable_schema_hash` hashes that list directly, `vfs_hash` moves as a consequence (composite) |
| `f4bdf19c` | fix(vfs): refuse authored tick on the overlay path; pin the in-step tick write discriminately | *(none)* | write-path/validation fix, no schema-input change |
| `15ec46bd` | feat(env): time_of_day derives from global_tick — the second temporal bookkeeping dies | *(none)* | runtime derivation only; no compiled-hash input touched |
| `08a9a122` | feat(vfs): evaluation marks derive from exposure — expressions evaluate on the shipped default | *(none)* | `vfs_evaluation_marks` is not a hash input (see above) |
| `c0ffb214` | fix(vfs): write-back skips statics — dependency-chased initials no longer clobber engine writes | *(none)* | runtime write-back fix, no schema-input change |
| `22caa926` | feat(vfs): agent-profile expressions evaluate; item-profile expressions refuse at compile | *(none)* | evaluation/refusal behaviour only; the profile *schema* (what's declared) is unchanged, only what's *done with it* at runtime/compile-refusal |

Two-worktree confirmation (`11dee204` vs `HEAD`, all three probed packs, matching the
per-commit table exactly): `default_curriculum L1_full_observability` — moved
`variable_schema_hash`, `vfs_hash`; `configs/differential/div003_rect L1_full_observability` —
identical two-field move; `configs/test/items_smoke L0_smoke` — identical two-field move.
`observation_schema_hash` does **not** move on any of the three packs — checked explicitly
(the STOP condition this ticket's task named did not fire). All other `*_hash` fields
(`actions_hash`, `bars_hash`, `brain_hash`/`pack_brain_hash`, `curriculum_hash`, `drive_hash`,
`environment_hash`, `experiment_hash`, `items_hash`, `stratum_hash`, `training_hash`,
`transition_graph_hash`, `action_schema_hash`, `affordances_hash`) are unchanged at `HEAD`
relative to `11dee204` on all three packs.

**Why one entry and not four.** All four surfaces landed as one unit's accepted work
(unit 2, authored temporality) between two adjudicated matrix states (`11dee204`'s DIV-009
exit-0 and this ticket). Only one of the four — the tick `VariableDef` — moves any hash; the
entry names all four because the "what changed" story is the unit's, and because a future
reader diffing `11dee204..HEAD` needs the full surface list to understand why only two fields
moved despite four landings touching the compiler/runtime.

**Why streams cannot move.** The tick variable is not observed: `observation_schema_hash` is
unchanged (measured above), and the `VariableDef`'s own `readable_by=["agent","engine"]` marks
it evaluation-readable, not observation-exposed — a variable enters `observation_schema_hash`
only via an explicit `ObservationField`/exposure declaration, which nothing in unit 2 adds for
`tick`. No fixture pack among the three probed declares a global or agent profile with an
*expression* referencing `tick` (or anything else): `configs/default_curriculum/vfs_profiles.yaml`
and `configs/differential/div003_rect/vfs_profiles.yaml` declare no `global_profile` or
`agent_profile` at all (only an empty `default_item` item profile); `configs/test/
items_smoke/vfs_profiles.yaml` explicitly sets `global_profile: null` and `agent_profile:
null` (its three item profiles' `initial_value`s are literal floats, not expressions). So
Task 5's marks-derivation fix and Task 6's agent-profile-evaluation/item-profile-refusal
changes fire on **zero** fixture cells — there is nothing for them to evaluate differently.
`configs/test/effects_smoke` (the fourth profile-block pack, not independently bisected here —
Task 2's precedent for treating `effects_smoke` as mirroring `items_smoke`'s movement applies
identically) declares a `global_profile` with one variable, `day_count`, but its
`initial_value: 0` is also a literal, not an expression, so the same "nothing to evaluate
differently" argument holds. `time_of_day` deriving from `global_tick` (`15ec46bd`) changes an
internal computation path but not its observed *value* — the existing `time_of_day` observation
tests (`test_temporal_pipeline.py`) pin behavioural equivalence, and no probed pack's
`observation_schema_hash` moved. Step 4 (the full matrix run, both modes) is the harness-level
confirmation that this reasoning holds under actual scripted/seeded traces, not just static
analysis of the fixture YAML.

**Diff shape.**

| block | cells | hash_fields |
|---|---|---|
| standing (10 cells) | all 5 `default_curriculum` levels × cpu/cuda | `variable_schema_hash, vfs_hash` |
| differential (6 cells) | `div003_scaled, div003_cubic_partial, div003_rect` × cpu/cuda | `variable_schema_hash, vfs_hash` (identical to standing — verified per-cell) |
| profile (4 cells) | `items_smoke, effects_smoke` × cpu/cuda | `variable_schema_hash, vfs_hash` (identical to standing/differential — the tick variable is injected uniformly, independent of any authored profile) |

Every stream (`obs`, `actions`, `dones`, `rewards`) is unaffected — the reasoning above, and
the full plain-mode and `--scripted` matrix runs recorded in the Task 7 report are the
harness-adjudicated confirmation.

**Harness adjudication.** `_DIV010 = RegisteredHashDivergence(register_ref="DIV-010",
hash_fields=("variable_schema_hash", "vfs_hash"))` binds every one of the twenty cells,
appended to each cell's existing tuple: standing/differential cells carry
`(_DIV009_STANDING, _DIV010)`; profile cells carry `(_DIV006, _DIV009_PROFILE, _DIV010)`.
`_DIV010`'s field set is identical across all three blocks, unlike `_DIV009_PROFILE`'s
disjoint-from-`_DIV006` narrowing — the tick variable's injection is unconditional and adds
exactly the same two derived-hash movements everywhere, so there is no overlap to resolve.
Any hash mover outside a cell's declared union is `HASH_MISMATCH`; a declared field that does
not move is `REGISTERED_DIVERGENCE_ABSENT`; any stream difference is `DIVERGE` — all red, same
as every other hash-only entry.

**Superseded in place 2026-08-26 (DIV-008), NOT retired — ruled at unit 3 Task 11.** This
entry's retirement clause named the token cut, and the cut has landed. It stays `built` and
stays bound anyway, because the lifecycle's bar for `retired` is "the oracle-side surface is
gone, or the divergence dissolved" and neither holds: the engine tick `VariableDef` is still
injected into every compiled universe and still moves `variable_schema_hash` against the
frozen oracle, entirely independent of the token cut. DIV-008 declares the same two fields
for its own cause (it removes fourteen engine-minted `obs_*` primitives from the canonical
list while this entry adds one tick entry to it) — two causes genuinely moving one hash,
which is the composing shape this entry itself established. Both declarations stand; the
union still equals the observed movers exactly and both of this entry's fields still move.
**Retire this entry** when the oracle is re-tagged past unit 2's landings.

---

## DIV-011 — TokenSpec alongside emission (token-obs unit 3 Task 7): two new artifact hashes appear on the new side, everything pre-existing is byte-identical

- **Status:** `retired` (2026-08-26, unit 3 Task 11 — **retired INTO DIV-008 by this
  entry's own pre-registered condition**, quoted verbatim at the foot of this entry: "Retire
  this entry when DIV-008 lands (Task 10 redefines `observation_schema_hash` over the
  TokenSpec and the token hashes become part of that registered surface)". That condition is
  met. `token_type_schema_hash` and `layout_hash` are no longer a fact about an ALONGSIDE
  emission — the TokenSpec **is** the observation ABI now — so their declaration moves,
  unchanged in content, into `_DIV008_HASH`. Both fields still read `<absent>` on the old
  side and a value on the new side, on every one of the twenty cells: nothing about the
  divergence dissolved, only the entry that owns it. The `_DIV011` binding is removed.)
  Previously `built` (2026-08-25 — bound with the landing commit; plain-mode and
  `--scripted` matrix runs recorded in the unit-3 Task 7 report, both exit 0.)
- **Harness shape: hash-only** (`RegisteredHashDivergence`)
- **Provenance:** `hamlet-fa6bb6da4a` (unit 3, token observations) · token-obs spec §5
  (docs/superpowers/specs/2026-08-22-token-observation-representation-design.md) · unit-3
  plan Task 7 under the controller's ALONGSIDE ruling (the brief's severing edits are
  deferred to Task 10).
- **Surface:** `src/townlet/universe/compilers/observation.py` (`build_token_spec`),
  `src/townlet/universe/compiler.py` (stage-7 emission), `src/townlet/universe/compiled.py`
  (the `token_spec` block, `COMPILED_SCHEMA_VERSION` 1.20 → 1.21),
  `src/townlet/vfs/schema_hashes.py` (`compute_token_type_schema_hash`,
  `compute_token_layout_hash`).

**What changed.** Unit 3 Task 7 compiles the `TokenSpec` artifact (spec §§1–2) per level,
ALONGSIDE the unchanged `ObservationSpec` family, and stamps two NEW provenance hashes on
the compiled artifact: `token_type_schema_hash` (the transfer contract — per-type payload
feature names, filler kinds, encoding version) and `layout_hash` (the flat-net contract —
type order, capacities, slot bindings, `total_dims`). Neither enters `config_hash` nor the
four-term `compute_vfs_hash` composition — that movement is Task 10's, already registered
as DIV-008. The old side (oracle at `oracle-2026-08-17`) predates the fields entirely, so
on every cell both fields read `<absent>` on the old side and a value on the new side —
the harness's dynamic hash-field enumeration correctly reports that as a mover, and this
entry is the declaration that makes it a registered one.

**Measurement.** Compile-probe over all five `configs/default_curriculum` levels at the
Task-7 BASE commit (`4da3054c`) vs the Task-7 tree (probe script: dump every `*_hash`
attribute plus `observation_spec.total_dims`): all 95 pre-existing hash lines are
byte-identical; exactly 10 lines are new — the two token hashes × five levels. That
zero-movement of everything pre-existing is the Task's alongside proof; the harness
run then confirms it per cell against the oracle side (every pre-existing mismatch
remains exactly the DIV-006/DIV-009/DIV-010 sets already registered).

**Diff shape.**

| block | cells | hash_fields added by this entry |
|---|---|---|
| standing (10 cells) | all 5 `default_curriculum` levels × cpu/cuda | `token_type_schema_hash, layout_hash` (old side `<absent>`) |
| differential (6 cells) | `div003_scaled, div003_cubic_partial, div003_rect` × cpu/cuda | identical — the fields are stamped on every compiled universe unconditionally |
| profile (4 cells) | `items_smoke, effects_smoke` × cpu/cuda | identical |

Every stream (`obs`, `actions`, `dones`, `rewards`) is unaffected: the TokenSpec feeds no
runtime path yet — no publisher exists until Task 8 and no observation consumer until the
Task-10 cut — so nothing an agent sees or does can move.

**Harness adjudication.** `_DIV011 = RegisteredHashDivergence(register_ref="DIV-011",
hash_fields=("token_type_schema_hash", "layout_hash"))` binds all twenty cells, appended
to each cell's existing tuple (DIV-010's uniform pattern — the emission is unconditional,
so the field set is identical across blocks and disjoint from every bound entry's fields;
no overlap to resolve). A mover outside a cell's declared union stays `HASH_MISMATCH`; a
declared field that does not move lands `REGISTERED_DIVERGENCE_ABSENT`; any stream
difference is `DIVERGE` — all red, as for every hash-only entry.

**Retire this entry** when DIV-008 lands (Task 10 redefines `observation_schema_hash`
over the TokenSpec and the token hashes become part of that registered surface), or when
the oracle is re-tagged past unit 3's landings, whichever comes first.

---

## DIV-012 — Four undeclared hash movers surfaced by the `day_phase` run, each bisected to its causing commit

- **Status:** `built` (2026-09-02 — measured against the full cpu matrix, run
  `20260902-100802` (`UV_CACHE_DIR=.uv-cache uv run python -m townlet.oracle.harness`, no
  `--cell`, no `--cuda`), **exit 0**: all ten cpu cells `DIVERGED_AS_REGISTERED` naming
  `["DIV-009", "DIV-010", "DIV-012", "DIV-008"]` (standing and differential) or
  `["DIV-009", "DIV-010", "DIV-012", "DIV-008"]` with `_DIV012_PROFILE`'s narrower field set
  (profile — same `register_ref`, different `RegisteredHashDivergence` object, so the printed
  ref list is identical text even though the bound fields differ); all ten cuda cells
  `SKIPPED` (`cuda not requested` — genuinely unmeasured, not adjudicated either way).
  Superseded an earlier single-cell run, `20260902-092715`
  (`default_curriculum:L3_temporal_mechanics:cpu` alone), which found the same four fields
  `HASH_MISMATCH` with `register_refs: []` and an unbisected "already diverged before
  `149e2bad`" attribution for three of them — that attribution is corrected below by an
  actual per-commit bisection.)
- **Harness shape: hash-only** (`RegisteredHashDivergence`, two objects: `_DIV012` and
  `_DIV012_PROFILE`)
- **Provenance:** `hamlet-55b2826a02` (unit 5, `day_phase`, this ticket) · `PDR-0143` (unit 5,
  and its own §6 identity rule) · commit `94656527` (Task 1, "feat(stratum): delete the inert
  observation_mode key") · commit `c6c6b524` ("fix(tokens): restore executable observation
  authority", the M2 meter `range_type` migration) · commit `d554fb7f` ("feat(tokens): cut
  compact replay ABI")
- **Surface:** `src/townlet/config/stratum_config.py` (`observation_mode` deletion) ·
  `src/townlet/config/affordances_v2_config.py` (`AffordanceParamConfig`: `duration_ticks`
  gains `gt=0`, `interaction_type` narrows from `{instant, multi_tick, dual}` to
  `{instant, multi_tick}`, `validate_interaction_stages` rewritten around reachable-stage
  sets — no pack YAML edited alongside this one) · `src/townlet/config/environment_config.py`
  (`MeterRangeNone` deleted, `MeterRangeMinMax.clip` narrows `bool` → `Literal[True]`)
  **together with** every covered pack's `environment.yaml` (`clip: false` → `true` on every
  declared meter, same commit — the schema narrowing and the content edit landed together,
  so `environment_hash`'s movement is not schema-alone) · `src/townlet/config/
  brain_config.py` (`ArchitectureConfig._serialize_without_absent_token_set` — the
  `model_serializer` `cbea580f` added specifically to omit the always-`None` `token_set` key
  from `model_dump()` — deleted by `d554fb7f` alongside `SetEncoderConfig`)

**What the run found.** The single-cell run (`20260902-092715`) reported
`default_curriculum:L3_temporal_mechanics:cpu` as `HASH_MISMATCH`. Its `mismatched` set has
twelve fields; eight are already covered by the DIV-008/009/010 union (`day_phase`'s own
movement of `layout_hash`, `observation_schema_hash`, `variable_schema_hash`, `vfs_hash` —
additive on top of those entries' own reasons, DIV-010's "two causes, one hash" composing
shape). Four were undeclared: `affordances_hash`, `brain_hash`, `environment_hash`,
`stratum_hash`.

**Measurement method (bisection).** DIV-009's own method: OLD side = the frozen
`.oracle/oracle-2026-08-17` worktree's code (pinned at `4222a917`, never moves) compiled
against `oracle_fixtures/configs/default_curriculum` **as committed at the candidate
commit** (not a single frozen snapshot — `oracle_fixtures/` itself moved once in this range,
see below); NEW side = a `git worktree add --detach` checkout of the candidate commit,
compiled with that commit's own `src/` against that commit's own
`configs/default_curriculum`. `git log --oneline 4222a917..149e2bad -- configs/
default_curriculum src/townlet/config` (the only two path classes a RAW hash can move on)
narrows the walk to seventeen commits; the ones touching `affordances_v2_config.py`,
`environment_config.py`, `stratum_config.py` or `brain_config.py` are the only candidates,
probed via `UniverseCompiler().compile(..., use_cache=False)` reading every `*_hash`
attribute off the compiled level, metadata AND universe objects (an earlier pass of this
bisection only read the level object and silently dropped `brain_hash`/`environment_hash`/
`pack_brain_hash` from the comparison — caught by cross-checking against the actual harness
report before trusting the result).

`oracle_fixtures/configs/default_curriculum/environment.yaml` itself moves exactly once in
`4222a917..149e2bad`, at `0b659130` ("delete the four writerless observation variables") —
but that commit re-freezes its own `oracle_fixtures` copy in the same commit (confirmed:
`git show --stat 0b659130 -- oracle_fixtures` touches all four differential+standing
`environment.yaml` fixtures), so the live-vs-frozen comparison nets to zero movement there,
exactly DIV-009's own `0b659130` finding for `environment_hash`/`variable_schema_hash`/etc.
No other commit in range touches `oracle_fixtures/`, so the OLD side is otherwise constant
throughout — each candidate's bisection reduces to "does the NEW side's compiled value change
relative to that one constant."

**Per-field bisection (exact commit, confirmed by comparing the literal hash string, not
just mismatch/match against OLD):**

| field | value through | first moves at | commit | cause |
|---|---|---|---|---|
| `stratum_hash` | `149e2bad` (`263635d7…`) | `94656527` (`bcbf09eb…`) | `94656527` | Task 1 deletes `observation_mode` from `StratumConfig`; RAW hash over the whole config, frozen `oracle_fixtures/stratum.yaml` still declares the key |
| `affordances_hash` | `237b0c38` (`af020ccd…`, = OLD) | `c6c6b524` (`2bda63f6…`) | `c6c6b524` | `AffordanceParamConfig` schema narrows (`duration_ticks: gt=0`, `interaction_type` drops `dual`, `validate_interaction_stages` rewritten); RAW hash moves for the schema edit alone — `configs/default_curriculum/affordances.yaml` itself has an EMPTY diff in this commit |
| `environment_hash` | `237b0c38` (`6788982a…`, = OLD) | `c6c6b524` (`5bbd38d3…`) | `c6c6b524` | same commit, BOTH move together: `EnvironmentConfig`'s meter `range_type` schema narrows (`MeterRangeNone` deleted, `MeterRangeMinMax.clip: bool → Literal[True]`) AND every covered pack's `environment.yaml` content changes (`clip: false → true` on all 8 `default_curriculum` meters, same edit landing in `boundary_wrap`, `div003_cubic_partial`, `div003_rect`, `items_smoke`, `effects_smoke` in this commit) — confirmed by `git show c6c6b524 -- configs/default_curriculum/environment.yaml`; movement is NOT isolated to the schema edit, unlike `affordances_hash` above |
| `brain_hash` | `cbea580f`/`237b0c38` (`5650add3…`, = OLD — `cbea580f`'s own "zero-movement pin" fix works as designed) | `d554fb7f` (`4f10939d…`) | `d554fb7f` | deletes `ArchitectureConfig._serialize_without_absent_token_set`, the `model_serializer` `cbea580f` added specifically to omit the always-`None` `token_set` key from `model_dump()`; its removal reintroduces exactly the movement `cbea580f` had fixed — confirmed unchanged through `9d4e942f` (identical hash value, that later commit's `brain_config.py` edits do not move it further for `default_curriculum`) |

`pack_brain_hash` (already declared by `_DIV009_STANDING`) shares `brain_hash`'s value on
this pack (no per-level brain override exists) and moves at the same commit for the same
reason; not separately bisected.

**Full cpu-cell table** (run `20260902-100802`; CUDA genuinely unmeasured, all `SKIPPED`):

| pack | level | undeclared movers before this entry | binding |
|---|---|---|---|
| `default_curriculum` | `L0_0_minimal` | `affordances_hash, brain_hash, environment_hash, stratum_hash` | `_DIV012` |
| `default_curriculum` | `L0_5_dual_resource` | `affordances_hash, brain_hash, environment_hash, stratum_hash` | `_DIV012` |
| `default_curriculum` | `L1_full_observability` | `affordances_hash, brain_hash, environment_hash, stratum_hash` | `_DIV012` |
| `default_curriculum` | `L2_partial_observability` | `affordances_hash, brain_hash, environment_hash, stratum_hash` | `_DIV012` |
| `default_curriculum` | `L3_temporal_mechanics` | `affordances_hash, brain_hash, environment_hash, stratum_hash` | `_DIV012` |
| `boundary_wrap` | `L1_full_observability` | `affordances_hash, brain_hash, environment_hash, stratum_hash` | `_DIV012` |
| `div003_cubic_partial` | `L2_partial_observability` | `affordances_hash, brain_hash, environment_hash, stratum_hash` | `_DIV012` |
| `div003_rect` | `L1_full_observability` | `affordances_hash, brain_hash, environment_hash, stratum_hash` | `_DIV012` |
| `items_smoke` | `L0_smoke` | `brain_hash, environment_hash, stratum_hash` (measured — `affordances_hash` does NOT move here) | `_DIV012_PROFILE` |
| `effects_smoke` | `L0_effects` | `brain_hash, environment_hash, stratum_hash` (measured — `affordances_hash` does NOT move here) | `_DIV012_PROFILE` |

The standing and differential blocks' undeclared-mover sets are IDENTICAL to `_DIV012`'s
four-field declaration — measured directly from the `20260902-100550` pre-fix run's
`HASH_MISMATCH` detail for the three differential cells (the five standing cells were already
bound to `_DIV012` by that run, so their own undeclared-mover breakdown isn't independently
visible in that report, but their clean `DIVERGED_AS_REGISTERED` in both the pre- and
post-fix runs is the direct confirmation the union matches exactly). The two profile cells
measurably lack `affordances_hash` in their mismatched set — `items_smoke`/`effects_smoke`
declare no affordance whose `AffordanceParamConfig` schema exercises the narrowed fields
differently enough to move the RAW hash, or their affordances happen to compile to the same
dump either way; not further investigated since the measurement (not the reason) is what the
narrower `_DIV012_PROFILE` binding needs.

**Why one entry, two binding objects.** `affordances_hash`, `brain_hash` and `environment_hash`
are schema-level RAW hash movers (three separate commits, three separate causes) and
`stratum_hash` is a fourth, unrelated schema-level RAW hash mover (a fifth cause would be
none — all four are genuinely different commits touching different DTOs). They are grouped
under one `DIV-012` register_ref because that is what PDR-0037's record-then-bind discipline
and DIV-009's own precedent call for: one ticket, one landing, one entry naming everything the
ticket's own measurement surfaced, not four entries for four unrelated single-commit findings
that happen to have been discovered by the same run. Two `RegisteredHashDivergence` objects
(`_DIV012`, `_DIV012_PROFILE`) exist under that one `register_ref` because the union-exact
rule requires the declared set to match the OBSERVED set per cell exactly, and the profile
cells' observed set is measurably narrower by one field (`affordances_hash`) — declaring the
wider set there would make the entry stale (`REGISTERED_DIVERGENCE_ABSENT`) on those two
cells.

**Scope.** All ten cpu cells run and adjudicated (`20260902-100802`, exit 0). CUDA is
declared identically (per `Cell.hash_divergences`) but not run this ticket (`--cuda` not
passed) — genuinely unmeasured, not assumed to agree.

**Harness adjudication.** `_DIV012 = RegisteredHashDivergence(register_ref="DIV-012",
hash_fields=("affordances_hash", "brain_hash", "environment_hash", "stratum_hash"))` binds
the ten standing and differential cells: `(_DIV009_STANDING, _DIV010, _DIV012, _DIV008_HASH)`.
`_DIV012_PROFILE = RegisteredHashDivergence(register_ref="DIV-012", hash_fields=("brain_hash",
"environment_hash", "stratum_hash"))` binds the four profile cells alongside `_DIV009_PROFILE`:
`(_DIV009_PROFILE, _DIV010, _DIV012_PROFILE, _DIV008_HASH)`. Both field sets are disjoint from
every other bound entry's fields on their respective cells (no overlap to resolve, DIV-009's
shape). A mover outside a cell's declared union stays `HASH_MISMATCH`; a declared field that
does not move lands `REGISTERED_DIVERGENCE_ABSENT`; any stream difference is `DIVERGE` — all
red, as for every hash-only entry.

**Retire this entry** when each of its four causes is independently absorbed: `stratum_hash`
when `oracle_fixtures/stratum.yaml` is re-frozen or the oracle is re-tagged past `94656527`;
`affordances_hash`/`environment_hash` when re-frozen or re-tagged past `c6c6b524`;
`brain_hash` when re-frozen or re-tagged past `d554fb7f` — four independent retirement
conditions bound under one entry for the union-exact rule's sake, not because they share a
story.

---

## Adding an entry

Record the divergence **before** cutting the seam that produces it — at knockdown plan time,
not when the harness fires. An entry needs: verified oracle behaviour (read the source, cite
the evidence), intended new behaviour, the expected diff shape and its adjudication rule,
and tracker + PDR provenance. A diff the harness finds that matches no entry is either a
rebuild defect or a failure of this process; both are findings, neither is normal.

When a new entry's declared hash fields would overlap an existing bound entry's fields on
the same cells, prefer narrowing to a disjoint field set when the two causes are separable
(the DIV-009 shape — declare only what this entry alone accounts for, leaving the shared
field under the entry that already covers it) over an overlapping declaration, which is
correct only when two causes genuinely move the same hash (the DIV-010 shape).

**Binding a trace-visible entry to the harness** (`hamlet-56ec575ae2` / `PDR-0037`): a cell
expected to produce a registered divergence declares it in `src/townlet/oracle/matrix.py` via
`RegisteredDivergence(register_ref="DIV-NNN", old_stderr_substring=...)`. The harness passes
that cell as `DIVERGED_AS_REGISTERED` **only** when ALL of these hold: the oracle side
crashed (nonzero exit) **without writing a trace**, the declared signature appears **inside
the final exception text of its stderr** (frame paths, warnings, log noise, stdout and
harness-synthesized diagnostics can never satisfy it), and the rebuild side ran, producing a
trace valid for the cell's own params from the declared src root. Everything else stays red,
each with its own reason in the report: a crash without the signature in its final exception,
a crash with no traceback at all, a non-crash failure (exit 0, no trace), a crash that still
wrote a trace, a new side that also crashes (divergence not yet built — the honest
pre-knockdown state), and an old side that runs (`REGISTERED_DIVERGENCE_ABSENT` — this entry
is stale; reconcile it, don't ignore it). The signature must be distinctive of THE registered
crash; declaration-time validation rejects empty, bare-exception-name and
traceback-boilerplate signatures. Matrix-side tests require every declared ref to exist as a
`## DIV-NNN` heading in this file **and** that entry to carry a machine-readable
`Harness shape: old-side-crash` line — an entry predicting any other diff shape cannot be
bound, which is what stops a typo-bind from certifying the wrong entry.
