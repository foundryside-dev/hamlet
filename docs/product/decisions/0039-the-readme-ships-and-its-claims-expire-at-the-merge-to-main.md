# PDR-0039 — The README ships as written; its claims are branch-scoped and expire at the merge to `main`

Date: 2026-08-14   Status: **accepted** (the publish decision is **owner-made** — it is outward-facing
and outside the grant; the expiry rule and the CI sequencing that follow from it are within grant)
Author: Claude (standing product owner)
Related: `PDR-0038` (the escalation clearance this completes), `PDR-0010` (the Gates-green lesson
the CI finding repeats), `PDR-0026` (the precedent: only the owner can rule on whether a document
states a lie or an unbuilt intention), `PDR-0006` (the strangler whose completion is the merge)
Tracker: `hamlet-6730ba7915` (closed), `hamlet-2100105c9a` (CI, P1, open)

## Context

The rewritten `README.md` states publicly that CI has validated none of the recovery work, that
nothing has passed since 2025-11-28, that the frontend cannot be built as shipped, and that two of
five non-fixture config packs do not compile.

Two things made this need an explicit decision rather than an assumption:

1. **The authorization predated the finding.** The owner approved "rewrite it" *before* either of
   us knew about the CI state — that was discovered while verifying the draft's claims. A rewrite
   authorization does not automatically extend to publishing a newly-found fact about project
   health.
2. **Publication is not gated by an agent action.** The agent pushes nothing; the owner pushes the
   branch routinely (four times, the most recent sixty seconds before this session opened). So the
   file would have gone public on the next reflexive push with nobody having decided to publish it.
   Absent a decision, the default was accidental publication.

## The call

**Ships as written.** Owner, asked directly with the section quoted: *"that's fine, this is on a
recovery branch and hopefully we'll recover before we push back to main."*

The reasoning matters more than the approval, because it is not "the honesty is acceptable" — it
is **a claim about scope and time**. The README describes `project-recovery`. `main` is 145 commits
behind and its own README still carries the false coverage badge. The recovery-branch README is
therefore a *status report on a work in progress*, and the owner's expectation is that the
conditions it reports will be **fixed, not merely re-described**, before the branch reaches `main`.

Two consequences follow, and they are the reason this is a PDR and not a note.

## Consequences

**1. The README's claims have an expiry, and the merge is it.** Every rough edge it lists is a
defect the recovery intends to close. If the branch merges with the file unchanged, the sentences
stop being honest status and become *stale claims on the default branch* — the exact failure the
rewrite corrected, re-created by the passage of time rather than by carelessness. The file now says
so in its own stamp: *"This file describes the `project-recovery` branch and is expected to go out
of date as the rewrite proceeds; it is re-verified before it reaches `main`."*

**Re-verification before the merge is not optional and is not a re-read.** The verification method
is on the record (`hamlet-6730ba7915`): ground-truth sweep, draft from verified facts only,
adversarial pass hunting false claims. The adversarial pass caught **24 defects in a draft written
expressly not to lie**. A merge-time skim would not have caught those.

**2. CI restoration is a merge gate, not an interrupt.** `hamlet-2100105c9a` sits directly on the
owner's stated path — you cannot honestly "recover and push back to `main`" while no workflow has
ever run on the branch being merged. But it does not block WS-7, and the owner chose the knockdown
as the current bet with the CI finding already surfaced. So it is **sequenced before the merge and
after the current knockdown**, not raced against it. Its own ordering trap stands: fix
`validate_compiler_cli.py`'s input *before* pointing any workflow at this branch, and note that
Full Test Suite is `disabled_inactivity` — a sticky state needing an explicit `gh workflow enable`,
which no push will clear.

## Reversal trigger

- **Re-open the publish decision** if the branch is about to merge to `main` with the README's
  rough-edges or CI sections still accurate. That would mean the recovery did not recover the
  things the owner expected it to, and what ships on the default branch becomes a different
  decision from what ships on a work-in-progress branch.
- **Fire the re-verification** at the merge, unconditionally, by the same method — not a re-read.
  If a merge is proposed without it, that is the trigger, and the merge waits.
- **Re-open the sequencing** if CI restoration turns out to be a precondition of the knockdown
  rather than of the merge — for instance if the harness work needs CI to be meaningful. Nothing
  currently suggests it does; the harness is run locally by the operator.
