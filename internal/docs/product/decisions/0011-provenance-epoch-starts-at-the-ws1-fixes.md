# PDR-0011 — Provenance epoch: no artifact predating the WS-1 provenance fixes is trusted evidence

Date: 2026-08-11   Status: accepted   Author: Claude (standing product owner)   Owner sign-off: **yes** — owner authorised the audit and pre-declared the disposition: *"yes please audit runs now although practically we'll just draw a line in the sand and cut it loose"*
Related: PDR-0008 (provenance breach), PDR-0006 (oracle freeze), metrics.md (Provenance integrity)

## Context

`PDR-0008` established by execution that checkpoints written after a poisoned compile carry
**inverted** provenance — the wrong universe accepts them, the right one rejects them. That raised
an escalation under the authority grant: auditing, re-stamping, or deleting affected artifacts is
a data operation and needed the owner's call.

The owner authorised the audit and pre-declared the likely disposition. The audit was run.

**Result: there is nothing to cut loose.**

- `runs/` contains exactly one file, `.gitkeep`.
- **Zero `.pt` files exist anywhere in the repository.**
- No TensorBoard event files and no run databases exist in the tree.
- A bounded scan of `$HOME` found `.pt` files only in unrelated projects (`keisei`, `jumpgate`,
  `jank`, copilot session state). None are Townlet artifacts.

The expected layout is `runs/<level>/<timestamp>/checkpoints/*.pt` with a sibling `tensorboard/`
(`demo/runner.py:95-103`). Nothing has ever been written there, or it has been cleared.

## Options considered

1. **Close the escalation as moot and move on** — pro: accurate, zero work. Con: leaves the policy
   undecided, so the same question re-opens the moment a checkpoint surfaces from a backup, another
   machine, or a run started before the fix lands.
2. **Build a re-stamping / migration path for affected artifacts** — pro: salvages evidence. Con:
   there is no evidence to salvage, and a migration path is explicitly forbidden by the
   zero-backwards-compatibility rule. This would be building a compatibility shim for zero users
   *and* zero artifacts.
3. **Declare a provenance epoch** — the line in the sand, recorded as standing policy rather than
   as a one-off cleanup. The option taken.

## The call

**Option 3.** No training artifact produced before the WS-1 provenance fixes land
(`hamlet-67ffbd282a` (a), `hamlet-ae6601e463`, `hamlet-1029f99f4b`) is trusted evidence. Any such
artifact that surfaces later — from a backup, another machine, or a run started before the fix — is
**discarded, not re-stamped and not investigated.** It is cheaper to retrain than to establish what
a checkpoint with inverted provenance actually represents.

Today this policy deletes nothing, because nothing exists. That is precisely why it is worth
recording now: the decision is free to make and settles a question that would otherwise be
re-litigated under time pressure, with an artifact in hand and a temptation to keep it.

## Rationale

Option 3 beat option 1 because the escalation's *substance* was never really "which files do we
delete" — it was "what is our standard for trusting a training artifact." That question outlives
the empty directory. Answering it while the stakes are zero is the cheapest it will ever be.

Option 2 was excluded on two independent grounds, either sufficient: nothing to migrate, and the
project's zero-backcompat rule forbids migration paths on principle.

The audit's null result also improves the position materially, and that is worth stating plainly:
the provenance breach in `PDR-0008` did **zero historical damage**. It is a live hazard, not a
legacy one. The only poisoned artifact in existence is the compile cache deliberately retained as
the WS-1(a) reproduction.

## Consequences

- **The escalation is closed.** No data deletion was required or performed.
- **WS-1(a)'s spec simplifies.** No migration, no re-stamping, no known-divergences register entry
  for existing checkpoints — there are none. The fix is free to break every prior artifact format.
- **The oracle has no legacy run corpus** (`PDR-0006`, WS-7). The differential harness must generate
  its own traces from the frozen code rather than comparing against recorded history. This is
  consistent with the strategy as written — the oracle *is* the frozen system, not a trace archive —
  but it removes an option that might otherwise have been assumed available.
- **`metrics.md` rows resting on run history are unsupported by anything on disk.** Specifically
  *Runtime throughput*, recorded as "baseline runnable and recorded" — the commits exist
  (`7868dba7`/`3311bc00`) and the benchmarks are runnable, but no recorded baseline artifact is
  present. It must be re-run to be cited.

## Reversal trigger

Reopen this PDR if **any** of the following:

- **A pre-epoch artifact turns out to be genuinely irreplaceable** — e.g. a training run too
  expensive to reproduce, or one demonstrating an "interesting failure" the project wants to
  preserve as a teaching artefact per `vision.md`. Preservation would then compete with provenance
  integrity, and the trade is the owner's call, not this policy's.
- The WS-1 provenance fixes land and are **later found incomplete** — the epoch boundary would then
  be in the wrong place, and artifacts trusted under it would not deserve it. The boundary moves
  forward to the actual fix, and this PDR is superseded rather than amended.
