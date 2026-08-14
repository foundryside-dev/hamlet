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
