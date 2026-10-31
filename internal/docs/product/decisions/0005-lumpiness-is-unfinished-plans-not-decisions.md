# PDR-0005 — Inert and missing surfaces are unfinished plan steps, not decisions; triage by cause, and recover intent from the run sheets

Date: 2026-08-11   Status: **accepted, amended** by PDR-0006   Author: Claude (standing product owner)   Owner sign-off: yes (owner supplied the framing directly)

> **Amended, same session, by `PDR-0006`.** The cause-based triage table and the **wire-not-delete**
> default stand and remain in force. What is corrected is this PDR's claim that the run sheets
> constitute *"much of the specification the assessment found missing"* — the owner later noted the
> spec carries the same spottiness as the code, so plan-archaeology is structurally blind to
> never-specified surface. Its remaining value is narrower: finding accidental drops, and dating
> artifacts by tooling stratum.
Supersedes: the deletion rule in PDR-0004 (§"What closing it takes"); PDR-0004 otherwise stands
Related: PDR-0002, PDR-0004, metrics.md (Trial 001), assessments/2026-08-11-maturity-assessment.md

## Context

`PDR-0004` adopted the assessment's mechanical rule for the ~40 declared-but-inert config fields:
every schema field must appear at a non-default value in some pack with a behavioural test, and
**"any field that fails after one pass gets deleted, not documented."** Under the zero-backcompat
contract, deletion is free.

The owner then supplied the causal frame that rule was missing:

> *"'weird gaps' are because we either made deliberate scope cuts for practicality (that is no
> longer required) or because stuff was accidentally dropped (i.e. if I went from 4a to 4c on a run
> sheet accidentally leaving out a config surface) … the codebase is 'best we could do at the time
> but uneven and lumpy in places that didn't get an extra quality pass'."*

and then, concretely, about the one caveat found in Trial 001:

> *"no partial vision support wasn't because we didn't want it, it was just step 9 on a plan we
> never got to."*

This is decisive, because `PDR-0004`'s rule would have **deleted the evidence of intent**. A field
left inert by an accidental skip is not a decision to omit the capability — but delete it and the
accident becomes permanent and unrecoverable, indistinguishable from a considered choice.

## Options considered

1. **Keep PDR-0004's rule** — pro: mechanical, unambiguous, cheap, and zero-backcompat blesses it.
   Con: it converts accidents into decisions. It treats "nobody got to step 9" identically to "we
   evaluated this and said no," which is precisely backwards for a codebase whose defining property
   is unevenness rather than wrongness.
2. **Wire everything inert** — pro: never destroys intent. Con: ~40 fields, some genuinely
   speculative, and it re-imports work that was correctly cut.
3. **Triage by cause first, then wire or delete** — pro: matches reality; the two causes have
   opposite correct treatments. Con: requires establishing cause per field, which needs evidence.

## The call

**Option 3.** Every inert or missing surface is triaged by *why* it is inert, and the disposition
follows from the cause:

| Cause | Correct treatment | Why |
|---|---|---|
| **Accidental drop** (skipped run-sheet step) | **Wire it** | Never a decision. Deleting makes the accident permanent. |
| **Deliberate cut, constraint since expired** | **Wire it** | The reason has lapsed. Cuts were made for context-window limits, weaker models, and time — constraints the owner reports no longer bind. |
| **Deliberate cut, constraint still binding** | **Delete it** | A live decision. Zero-BC makes deletion free and honest. |
| **Speculative — never had a use case** | **Delete it** | Aspirational schema is the same lie as an accidental drop, with no intent to preserve. |

The default when cause cannot be established is **wire, not delete** — inverting `PDR-0004`. The
asymmetry is deliberate: wiring a field that turns out unwanted costs some work and is reversible;
deleting a field that was an accident destroys information that only exists in the owner's head and
in stale plans, and is not.

The owner's own summary is adopted as the workspace's characterisation of the codebase, replacing
"buggy and underspecified": **"best we could do at the time, but uneven and lumpy in places that
didn't get an extra quality pass."** Lumpy is not the same problem as broken, and it takes a
different remedy: an evenness pass, not a repair campaign.

### The plan-archaeology method (adopted, and validated)

The run sheets in `docs/plans/` (9 active, 59 archived) and specs in `docs/tasks/` are the
**archaeological record of intent** — and therefore a large part of the specification the
assessment found missing (`specification` scored weak in **all 8** subsystems). Intent was written
down; it was never reconciled against what shipped.

Two mechanical signals make this cheap:

1. **Archive-vs-root split.** A phase plan in `docs/plans/archive/` was completed; one still in
   `docs/plans/` was not. For TASK-002A (spatial substrates) phases 1–8 are archived and
   **phases 9 (hex/1-D topologies) and 10 (graph substrate) are not** — the substrate subsystem is
   lumpy exactly where the plan stops.
2. **Phase-letter gaps.** The `5 / 5b / 5c` pattern is the owner's described `4a → 4c` failure mode
   made greppable.

**Validated on two independent hits this session:**

- **Trial 001's caveat is `docs/tasks/TASK-009-ND-POMDP.md`** — "N-Dimensional Partial
  Observability", *Status: Planned, Completed: [Not started]*, a fully written spec. gridnd's
  missing partial vision is an unstarted task, exactly as the owner said. Not a limitation to
  document — a task to finish, with the spec already written.
- **Convergence on the substrate fix.** Phase 9's own prescription — *"Use
  `substrate.get_observation_size()`"*, *"Refactor observation builder → substrate-agnostic"* — is
  the **same fix** the maturity assessment derived independently from source: `compilers/
  observation.py:64-150` re-derives dims from `substrate.type` strings instead of asking the
  substrate instance, and correcting that collapses three of four substrate crashes into one
  change. Two methods, no shared inputs, one answer.

That convergence is the evidence that plan-archaeology is a real recovery technique here and not a
literature review.

### Dating by tooling stratum (the reliable date signal)

The owner supplied the third mechanical signal: *"you can tell this is old because it predates
things like the filigree database (the tickets are actual files)."*

**An artifact's assumed tooling dates it more reliably than its mtime.** The assessment's pattern
P5 established that recency does not imply truth in this repo — `CLAUDE.md` and `README.md` both
carry today's mtime and are wrong about layout, filenames, required files, stage count, and
observation dimensions. Timestamps have been churned by edits that did not reconcile content.
Tooling assumptions cannot be churned that way: a document that treats markdown files as the issue
tracker was written before filigree existed, whatever its mtime says.

This yields two strata and a boundary:

- **Pre-filigree stratum** — `docs/bugs/` (60 files), `docs/tasks/`, `docs/plans/`. Tickets, specs,
  and run sheets as files. This is one coherent era's record.
- **Filigree stratum** — the live tracker (6 issues).

The boundary is a **migration that was never completed**, which is the root of the assessment's
pattern P6 (two unreconciled records of truth: 48% of verified `docs/bugs/` notes no longer
describe reality, while the source is littered with `BUG-22 FIX:` / `CRIT-07:` markers whose
markdown still reads `Status: open`).

The consequence is a cleaner retirement plan than file-by-file triage: treat the pre-filigree
stratum as **one migration**, not sixty decisions. Everything still live in it — the ~10 real bug
notes *and* the unfinished plan steps recovered by archaeology — moves into filigree; the stratum
is then retired whole. This supersedes both the assessment's "delete `docs/bugs/`" recommendation
and the narrower carve-out above: nothing in the stratum is deleted before its live content is
migrated, and nothing is kept after.

## Rationale

Option 3 beat option 1 because `PDR-0004`'s rule optimised for mechanical cheapness at the cost of
the one thing this recovery cannot replace. The codebase's problem is not that decisions were
wrong; it is that many things were never decided at all. A rule that cannot distinguish those two
states will systematically destroy the second.

It beat option 2 because triage is affordable — far more affordable than expected, since the causes
are largely *recoverable from documents that already exist*. The plans were treated by the
assessment as part of the stale-docs problem; under this frame a large subset of them are instead
the missing specification, and the archive/root split reads their status mechanically.

This also revises what the recovery *is*. `PDR-0004` framed it as wiring plus specification.
It is better framed as **finishing work that was started and interrupted** — which is a materially
more tractable job, and consistent with pattern P4 (inertness tracks recency, not quality: the cut
line runs along the newest, least-finished work).

## Consequences for the work streams

- **WS-3 (wiring harness) gains a triage input.** Its mechanical enumeration of inert fields is
  now step one; step two is assigning cause per field from the plans/tasks record.
- **WS-4 (close the authoring surface) is partly pre-specified.** Where a run sheet exists, the
  spec does not need writing — it needs finishing. TASK-009 is the worked example.
- **WS-5 (doc truth) must not delete the plans corpus wholesale.** The assessment recommended
  deleting aspirational docs under the zero-BC rule; that recommendation is **narrowed here** —
  `docs/plans/` and `docs/tasks/` are evidence and must be triaged, not swept. Aspirational
  *architecture* docs (HLD sections describing subsystems that were never built) remain deletable;
  *run sheets* do not, until their steps are reconciled.
- **A new stream is implied: WS-6 — plan reconciliation.** Walk the plans/tasks corpus, mark each
  step shipped / dropped-accidentally / cut-deliberately, and emit the resulting work. It feeds
  WS-3 and WS-4 and should precede the WS-5 deletion pass.

## Reversal trigger

Reopen this PDR if **any** of the following:

- Plan reconciliation (WS-6) finds that fewer than ~25% of inert surfaces map to an identifiable
  plan step. The archaeology would then not be paying for itself, and `PDR-0004`'s cheaper
  mechanical rule should be restored with a bias toward wiring rather than deleting.
- Wiring accidentally-dropped surfaces materially expands scope beyond what the recovery can carry
  — the "constraint since expired" test would then need re-examining, since capacity is itself a
  constraint.
- The owner determines that a specific cut is still wanted. Per the table above that is a live
  decision and the surface should be deleted; record it rather than leaving the field declared.
