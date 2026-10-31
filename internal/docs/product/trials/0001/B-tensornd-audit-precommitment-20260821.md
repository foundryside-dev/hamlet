# Trial B — `tensorNd` evidence audit: PRE-COMMITMENT

Date: 2026-08-21
Author: Claude (standing product owner, commissioning agent)
Pattern: `PDR-0098` (Trial F evidence audit) — outcome branches are written **before** the audit
runs, so the finding cannot be adjudicated under time pressure.
Commissioned by: the owner, at the 2026-08-21 `/own-product` resume, as `PDR-0106`'s
recommendation 1.

## Status of this document

**Written and committed before the auditing agent was dispatched.** Nothing below was authored
with knowledge of the audit's result. If this file's git history shows it landing *after* the
audit record, this pre-commitment is void and the audit must be re-run.

## The single question

> **Does a global-profile `tensorNd` VFS variable express "an entity that is a set of occupied
> cells rather than a point" at pin `1ef1d950` — as facet B-F2 pre-committed it?**

B-F2's binding text, from `B-blind-countersigned-facets-20260820.md`:

> There is readable state, belonging to one entity, whose occupied-cell count can exceed 1 and
> can change. […] **Exclusion, binding:** an "occupied set" obtained by unioning N agents'
> individual position vectors does **not** satisfy B-F2. The extent must be readable as **one
> entity's state** — one thing whose value is a set of cells.

## Why this question forks everything

Run 1 (`PDR-0087`) concluded *"every declarative route to a durable organism cell is refused
loudly"* — the corpus's deep stress, the trial's central finding, and the stated basis for four
filed tickets (`hamlet-1b9af9088c`, `hamlet-3f97369711`, `hamlet-4857e6824b`,
`hamlet-6c49488b22`). Run 2 (blind) scored the same facet **PASS on first reach** via a global
`tensorNd`. `PDR-0106` fired §7's reject branch on that disagreement and deliberately declined to
settle which run is right, on the ground that *"that call should not be made by the pass that
found it."*

## The specific discriminator the audit must resolve

Run 2's record **flags its own risk**, and the audit exists to settle it. Two facts from the
record, both to be verified rather than assumed:

1. Run 2's search plan S1 predicted *"cell-indexed write expected to be the failure point."*
2. The A.7 stress table (`B-blind-20260820.md`) records the write that produced the PASS as a
   **whole-container** write — `modify: vfs.organism_cells`, `value: "1.0"` in `GROW.on_start` —
   and notes the alternative reading under which B-F2 would be **ABSENT or INERT**: *"a spreading
   mass implies the cardinality change is growth, not a wholesale flood of the entire universe."*

So the load-bearing sub-question is:

> **Is there a declarative surface at the pin that writes an individual, index-selected cell of a
> global `tensorNd` — or is whole-container assignment the only write available?**

A container that can only go from all-zero to all-one holds a set of cells in the type-theoretic
sense while being unable to represent *a* spreading mass. Whether that satisfies B-F2 as
pre-committed is exactly what is being adjudicated.

## Pre-committed outcome branches

Three branches, fixed now. The audit's finding falls into one; who adjudicates it is fixed with it.

### Branch A — SOUND

`tensorNd` genuinely expresses one entity's state as a set of occupied cells: the state is
durable across ticks, per-cell addressable, its cardinality changes by declared means, it is not
a union of agent positions, and it is readable as pre-committed.

- Run 2's B-F2 PASS **stands**.
- `PDR-0106`'s rejection of the instrument **stands** — the largest disagreement remains genuine
  search variance between two competent executors.
- A new question opens and is **routed, not answered here**: whether run 1's four tickets
  misdescribe the substrate. That is WS-4 re-reading work.
- **Adjudicated by the standing agent** and recorded. It does not move a north-star reading —
  nothing publishes either way while criterion 3 is unmet.

### Branch B — UNSOUND

`tensorNd` does not express it — the state is not durable, not per-cell addressable, not readable
as one entity's state, unreachable from a declarative surface, or satisfied only by a construct
B-F2's exclusion bars.

- Run 2's B-F2 PASS is **executor error**, not search variance.
- The largest of the three disagreements **collapses**, and `PDR-0106`'s rejection must be
  **re-adjudicated** on what remains: the F5 ↔ B-F7 inversion, and B-F6 (which neither run
  demonstrated declarable). That re-adjudication may or may not still fire §7's branch.
- Because it bears directly on whether criterion 3 is met — and therefore on whether a north-star
  reading may ever publish from this corpus — the re-adjudication is an **OWNER ruling and is
  ESCALATED**. The standing agent prepares it; it does not decide it.

### Branch C — PARTIAL / INDETERMINATE

`tensorNd` satisfies some of B-F2's pre-committed requirements and not others — most likely:
durable and per-cell readable, but with no index-selected write, so cardinality cannot change by
growth; or readable in-process but with no observation encoding.

- B-F2 is neither cleanly sound nor cleanly unsound. The disagreement **narrows without
  collapsing**.
- Recorded by the standing agent, with the precise sub-claims that survive and that fail stated
  separately, because run 1's four tickets are affected differently by each.
- The instrument re-adjudication proceeds on the narrowed basis and is **ESCALATED** on the same
  ground as branch B.

## Constraints on the audit

- **Scope.** It adjudicates B-F2's soundness only. It does **not** re-score run 1, re-score any
  other facet of run 2, or opine on the instrument decision. `PDR-0106` and Appendix B's scope
  rule both forbid re-scoring a completed run.
- **Commit.** Findings are established at pin `1ef1d950`. `git diff --stat 1ef1d950..HEAD --
  src/townlet/` is **empty** (verified 2026-08-21 by the commissioning agent), so the `PDR-0090`
  substrate freeze held and a finding at HEAD is a finding at the pin — but the audit runs in a
  worktree pinned at `1ef1d950` regardless, so the claim needs no drift caveat.
- **Falsification duty.** Per `PDR-0098`, an audit that merely agrees has not done its job. The
  auditor must actively attempt to break the PASS — construct the negative case, make the failing
  branch observable, and rule out the false-pass classes — not confirm the record's narrative.
- **No fixing.** Gaps found are recorded for filing by the standing agent. `PDR-0090`'s substrate
  freeze is in force: `src/townlet/` is not touched. Scratchpad copies are fine.
- **Independent verification.** Per `PDR-0098`, the discriminator is verified by the standing
  agent as well, not taken from the audit.

## Reversal trigger

If a later reader establishes that any branch above was edited after the audit's result was
known, this pre-commitment is void and the adjudication reopens. The check is
`git log --follow docs/product/trials/0001/B-tensornd-audit-precommitment-20260821.md` against the
audit record's own commit.
