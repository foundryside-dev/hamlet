# PDR-0058 — the merge landed, and the bet's exit was mis-stated

Date: 2026-08-15   Status: **accepted**
Author: Claude (standing product owner)
Owner sign-off: **yes**, at the nineteenth checkpoint's `/own-product` resume. Offered as a fork
— *"the exit was mis-stated"* vs *"the Now bet is acceptable, declare a new Now"* vs *"leave it"* —
and the owner selected:

> *"The exit was mis-stated — the merge was an output, not the outcome. The Now bet continues;
> I restate its exit as an outcome condition in a PDR at checkpoint."*

The restatement itself was delegated to me by that option's own text, so the exit condition below
is my call under the owner's ruling, not the owner's words.

Related: `PDR-0006` (chose the strangler), `PDR-0039` / `PDR-0043` / `PDR-0048` (the two merge
gates), `PDR-0046` (push freely; the merge is the boundary), `PDR-0034` (differential ≠ wiring)
Tracker: milestone `hamlet-1ade187dcc`
Commits: `07b26ed5` (the merge), `33bfff51` (both gate conditions discharged)

## Context

**The merge to `main` happened, and this workspace did not notice.** PR #32 merged
`project-recovery` into `main` at `07b26ed5`, 2026-08-15 14:09 AEST, by the owner. It was done to
the checklist: `33bfff51` discharged both conditions first — the nightly cron restored
(`PDR-0043` reversal trigger 2, which therefore did **not** fire) and the README re-swept **at the
merge commit** per `PDR-0039`, which found five more stale claims in four commits. `main` now
carries the recovery; `project-recovery-2` was branched from it and is 13 commits ahead.

Four product checkpoints were written after that merge. All four carried forward
*"the merge remains available and untaken"* and *"both gates SATISFIED but NOT BANKED"*. By the
nineteenth checkpoint's ORIENT, `current-state.md:61` asserted, in plain text, something that had
been false for seven hours. This is the `Documentation truth` guardrail's own newest class — a
false claim inside a product-workspace document rather than an engineering one — and it is the
second time in three sessions that class has bitten.

The deeper defect is the one that let it survive four re-readings. `roadmap.md` states:

> **The merge to `main` is the bet's exit, and it now has two named gates.**

So the workspace defined the Now bet's exit as **an event it does not control and does not
perform** — the owner's merge — rather than as a condition it can evaluate. When the event fired,
nothing in the workspace was watching for it, because an exit stated as someone else's action has
no reading attached to it. A bet whose exit is an output rather than an outcome cannot be
accepted, and cannot notice that it has been.

And the exit was substantively wrong on its own terms: at `07b26ed5` the strangler had cut exactly
two units (the substrate→observation seam, `PDR-0041`; the meter type declaration, `PDR-0057`),
WS-0/3/4/5/6 were all open, and `Config-surface coverage` read ~2 of 7. Nothing about the bet was
finished. The merge was a **publication step inside the bet**, which is exactly what `PDR-0046`
already said about pushes — *publication is not undone by pushing again* — and the roadmap failed
to apply the same reading to the merge one level up.

## Options

| | | |
|---|---|---|
| (1) | the exit was mis-stated; restate it as an outcome condition | the bet continues; the merge is reclassified as an in-bet publication step |
| (2) | the bet is acceptable as written; declare a new Now | honours the recorded exit, but banks a bet that closed two of N units |
| (3) | leave it; revisit at the next merge | cheapest now, guarantees the same surprise at the next merge |

## The call — (1), with the exit restated as follows

**The Now bet — strangler rewrite behind the compiled-universe contract — exits when the pinned
oracle can be retired.** Concretely, all three must hold and be *read*, not asserted:

1. **Every entry in `docs/oracle/known-divergences.md` is terminal** — each DIV entry is either
   closed by a rebuild that the harness adjudicated, or accepted as permanent with its own PDR.
   A register with a live, unadjudicated entry means the strangler is mid-cut by definition.
2. **The harness's verdict vocabulary is re-earned, or its successor is recorded.** `PDR-0056`
   already put this on the clock: `AGREE` is now unreachable matrix-wide and the pack-drift guard
   is armed on zero cells, so "harness green" currently certifies *everything diverged exactly as
   registered*. Exiting on an instrument that can no longer say *these agree* would be exiting on
   a green light with the bulb removed.
3. **`Gates green` is read on a suite that hides nothing** — no marker-based deselection silently
   excluding tests from the reading (`PDR-0059`, `hamlet-a0832f9004`).

**Merging to `main` is explicitly NOT the exit.** It is a publication step that may happen any
number of times inside this bet, each time gated by `PDR-0039`'s unconditional re-sweep and
`PDR-0046`'s boundary. The next merge owes the sweep again — 13 commits already sit ahead of
`main`.

**And the authorability threshold is explicitly NOT this bet's exit either.** `Config-surface
coverage` 7 of 7 belongs to WS-4 (`hamlet-15050f280a`), the *Next* bet. Conflating "the strangler
is done" with "the authoring surface is closed" is what produced the mis-statement: the merge felt
like an ending because it was the only crisp event on the board. Two bets, two exits, stated
separately on purpose.

## Consequences

1. `roadmap.md`'s Now bullet is corrected: the merge is recorded as landed, the exit is restated,
   and the merge-gate checklist is re-pointed at the *next* merge rather than read as spent.
2. `current-state.md`'s false claim is deleted rather than softened. It was false, not stale-ish.
3. The bet's exit is now something a checkpoint can evaluate without an owner action occurring —
   which is the property it lacked.
4. `PDR-0048`'s "SATISFIED but NOT BANKED" framing is retired as answered: gate 1 is closed
   (`hamlet-2100105c9a`), gate 2 was re-swept at `33bfff51` and re-fires at the next merge.

## Reversal trigger

- **Reverse if a knockdown lands that the harness cannot adjudicate at all** — not diverged, not
  agreed, but uninstrumentable. Then criterion 2 is unmeetable as written and the exit needs a
  different instrument, not a different threshold.
- **Reverse if the divergence register grows for two consecutive checkpoints without a single
  entry going terminal.** That would mean the register is accumulating faster than the rebuild
  closes it, and "retire the oracle" is not an exit but a receding horizon.
- **Reopen the whole framing if the owner merges again and treats that merge as the ending.**
  The exit stated here is mine under a delegation; if the owner's actual reading of "done" is the
  merge, this PDR has the product's own definition of completion wrong and that is worth knowing.
