# PDR-0012 — Strict no-tech-debt until 1.0; the research-code exemption does not exist here

Date: 2026-08-11   Status: accepted   Author: Claude (standing product owner)   Owner sign-off: **yes** — owner stated the policy directly
Related: PDR-0007 (universality + definition-of-done), PDR-0008 (WS-1 ordering), PDR-0006 (freeze), PDR-0011, metrics.md (Gates green, Declared-but-inert config surfaces)

## Context

While confirming `PDR-0011`, the owner stated a standing policy:

> *"I have a strict 'no tech debt' policy, until we declare 1.0 we aren't carrying tech debt not
> even for RL work — when we feel like we have something worth testing then we'll freeze and test
> properly."*

This arrived at a moment when it directly contradicts a live temptation. `PDR-0008` established
that WS-1 defects (b) and (c) are confirmed but **unreachable on all 21 shipped packs** — the
classic shape of a deferral argument: *it's broken, but nothing reaches it, so it can wait.* The
policy forecloses that argument.

The second clause is the load-bearing one. **"Not even for RL work"** closes the exemption that
research and ML codebases almost universally grant themselves — that experimental code is exempt
from engineering standards because it is exploratory. This project declines that exemption.

## Options considered

1. **Treat it as a passing remark and carry on** — pro: no work. Con: it is a standing constraint
   on every future prioritization call, and an unrecorded principle is one the next session
   re-derives differently. `PDR-0007` exists because the owner's *previous* stated principle was
   worth recording; this one is at least as consequential.
2. **Record it and add "carries technical debt" to `vision.md`'s anti-goals** — pro: anti-goals are
   where refusals live, and this is a refusal. Con: `vision.md` is ENDORSED and editing it is a
   vision change that **escalates**. Not mine to do unilaterally, however obviously correct.
3. **Record it as a PDR now; ask separately whether it belongs in `vision.md`** — the option taken.

## The call

**Option 3.** Until 1.0 is declared, this project does not carry technical debt. There is no
research-code exemption, no "temporary" workaround, and no deferral justified by a defect being
currently unreachable. When something is worth testing, it gets frozen and tested properly rather
than propped up.

Whether this is promoted into `vision.md` as a formal anti-goal is **escalated to the owner** and
recorded in `current-state.md` as an open question. The PDR binds regardless; the vision edit is a
separate act.

## What counts as debt, and what explicitly does not

The policy needs an edge, or it will be misapplied to delete things this product exists to keep.

**Is debt — not carried:**
- Broken code that nothing currently reaches (WS-1 (b) and (c) are the live case).
- Failing quality gates. `Gates green` at 1 of 4 is debt, and "they're trivial" is why it accrued.
- Declared-but-inert config surfaces — schema fields that validate and do nothing (~40 of them).
  `PDR-0007`'s definition-of-done already forbids creating more; this forbids *keeping* the ones
  that exist.
- Computed-but-unconsumed outputs (`hamlet-ae6601e463`'s four per-level hashes).
- Known-wrong documentation. `Documentation truth` at ≥14 is debt.
- Duplicate code paths where one is live and weaker (WS-1 (d)).

**Is NOT debt — protected by `vision.md` and untouched by this policy:**
- **"Interesting failures."** Reward hacking and pathological emergent strategies (Low Energy
  Delirium) are *artefacts to preserve and document*, per `vision.md`'s anti-goals. They are
  product content, not defects, and this policy must never be cited to remove them.
- **Unbuilt capability.** An option nobody got to is not debt; it is an option not yet enabled
  (`PDR-0007`). Debt is what is *wired wrong*, not what is *absent* — though exposing a schema
  field for an unbuilt option converts it into debt immediately, which is exactly `PDR-0007`'s
  definition-of-done.
- **Deliberate pedagogical simplification**, where recorded as such.

## Rationale

Option 3 beat option 1 because this policy resolves a class of future arguments, not one case. Any
prioritization call of the form *"it's broken but nothing hits it"* or *"it's only research code"*
is now settled in advance, and settled arguments are the point of provenance.

The policy is also **self-consistent with the recovery strategy** in a way worth stating. A
strangler rewrite (`PDR-0006`) freezes the current system as an oracle. Debt carried into the
freeze does not stay debt — it becomes a **requirement** of the rebuilt system, because the oracle
defines correctness mechanically. So under this strategy, "we'll clean it up later" is not merely
deferred cost; it is a permanent specification change made by omission. The owner's own phrasing —
*"then we'll freeze and test properly"* — has the ordering right: freeze *after* it is clean.

One real tension is recorded rather than resolved. `PDR-0007` biases toward **yes** on capability
questions (universality and configurability as the default), and each yes carries a mandatory
wiring obligation. This policy says none of that obligation may be deferred. Together they are
demanding: every capability exposed must be wired, tested, and clean *before* moving on. That is
affordable only because the differential harness (WS-3) makes "wired and tested" mechanically
checkable. If it stops being affordable, `PDR-0007`'s second reversal trigger — *enabling options
is starving the recovery of capacity* — fires first, and the sequencing call belongs to
`/axiom-program-management`.

## Consequences

- **WS-1 (b) and (c) are not deferrable** on unreachability grounds. `PDR-0008`'s ordering stands
  (they are sequenced last because (a) and (d) are live today), but "last" now means last-in-set,
  not later-than-the-set.
- **The gates unit is promoted** from cleanup to a required member of the WS-1 fix set. `Gates
  green` must read 4 of 4 before the oracle freeze.
- **Any implementation plan containing "acceptable for now", "defer", or "follow-up" must be
  rejected or have that item pulled into scope.** This applies immediately to the WS-1 fix plan
  currently under review.
- **1.0 is undefined, so the policy is currently unbounded.** That is not a defect — it is
  presumably the intent — but it means there is no criterion that could ever end it. If a 1.0
  definition is ever wanted, it belongs in `vision.md` or `roadmap.md`, and defining it is a
  vision-level act.

## Reversal trigger

Reopen this PDR if **any** of the following:

- **1.0 is declared.** The policy is scoped to pre-1.0 by its own terms and must be restated (or
  deliberately extended) at that point rather than silently lapsing.
- **The policy is invoked to remove an "interesting failure"** or other deliberately-preserved
  artefact. That is a misapplication and means the edge stated above needs sharpening, not that the
  policy is wrong.
- **Debt-repayment is consistently displacing the recovery itself** — i.e. the WS-1…WS-7 program
  stops advancing because every session is spent restoring gates and wiring inert fields. That is
  `PDR-0007`'s capacity trigger arriving from the other direction, and the sequencing call escalates
  to `/axiom-program-management`, not to a quiet relaxation of this policy.
