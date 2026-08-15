# Known-Divergences Register

**Stream:** WS-7 (`hamlet-e3af412673`) — the strangler's enabling stream (`PDR-0006`).
**Stood up:** 2026-08-13, as WS-7's first artifact (`PDR-0028` — routed findings need a
register that exists; routing to a register that doesn't is filing to /dev/null).
**Oracle tag:** `oracle-2026-08-13` → `0e875d7a` (pinned 2026-08-13; see `ORACLE.md`).
Entries below were re-verified at the tagged commit and are stamped `tag-stamped`.

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

- **Status:** `tag-stamped` at `oracle-2026-08-13` (re-verified at `0e875d7a`: the five
  names still appear only in `universe/compiled.py` and `universe/compiler.py`)
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

- **Status:** `tag-stamped` at `oracle-2026-08-13` (re-verified at `0e875d7a`: the
  string-matched broad `except` sits at `demo/runner.py:202`)
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

- **Status:** `built` (2026-08-15 — the seam is cut; full 16-cell matrix CPU+CUDA exit 0
  with all six DIV-003 cells `DIVERGED_AS_REGISTERED`, runs `20260815-055108` /
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

- **Status:** `built` (2026-08-15 — declared before the first cut of the programme, per this
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
`default_curriculum` declares a width-preserving `minmax`. A pack that declares
`cyclical_sin_cos` or `one_hot` on a meter widens it by design, which is pinned by
`test_a_widening_meter_kind_grows_the_observation_by_exactly_its_extra_dims`.

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


---

## Adding an entry

Record the divergence **before** cutting the seam that produces it — at knockdown plan time,
not when the harness fires. An entry needs: verified oracle behaviour (read the source, cite
the evidence), intended new behaviour, the expected diff shape and its adjudication rule,
and tracker + PDR provenance. A diff the harness finds that matches no entry is either a
rebuild defect or a failure of this process; both are findings, neither is normal.

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
