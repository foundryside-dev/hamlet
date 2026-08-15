# PDR-0048 — Merge gate 2 is satisfied at `1b25c99d`; both gates now stand together, and both expire on the next commit

Date: 2026-08-15   Status: **accepted** (an ACCEPT against stated criteria, squarely within the grant)
Author: Claude (standing product owner)
Related: `PDR-0039` (set the two gates and the re-verification method), `PDR-0043` (gate 1; the
"a gate restored is not a gate verified" rule), `PDR-0046` (the merge is the reversibility
boundary), `PDR-0010` (the Gates-green lesson the method exists to prevent repeating)
Tracker: `hamlet-2100105c9a` (gate 1, closed), `hamlet-cbb747a51e` (filed by this sweep)

## Context

`PDR-0039` gave the merge to `main` two named gates. Gate 1 (CI restoration) closed on remote
evidence at the previous checkpoint. Gate 2 was **README re-verification by the same method that
produced it, not a re-read** — the method being a ground-truth sweep, a draft from verified facts
only, and an adversarial pass. `PDR-0039` was explicit that a merge-time skim would not do,
because the adversarial pass had caught 24 defects in a draft written expressly not to lie.

## The call

**Gate 2 is executed and satisfied at `1b25c99d`.** Every claim in `README.md` was re-executed or
re-read against the tree; the stale ones were **fixed, not re-described** — which is what
`PDR-0039` said the owner expected of the recovery.

**Ten claims had decayed in a single day, and every one decayed because the recovery fixed the
thing being described.** That is the substantive result and it is a good sign, not a bad one:

- CI: *"no workflow has ever run on this branch, none has passed since 2025-11-28"* — false in
  both halves. The Status bullet and the entire *Continuous integration* section were rewritten.
- `validate_compiler_cli.py` exits **0**, not 1; `configs/simple` and `configs/reference/model_pack`
  both validate clean, so *"two of the five config packs do not compile"* is gone from two places.
- The harness matrix is **16 cells**, not "five levels × {cpu, cuda}".
- Commit distance 145 → 162; packs carrying `experiment.yaml` 20 → 23.
- Transition families carrying zero rules: **three → two**. `interaction_progress` is no longer
  empty everywhere, because repairing `reference/model_pack` returned the only pack that
  exercises it to the measured set. *The surface did not change; the sample did* — and the README
  now says so, because the distinction is the interesting part.

**The adversarial pass caught one defect in this draft too** — "three pushes deep" when the branch
had two. Fourth consecutive rewrite in which the pass earned its cost.

## Consequences

**1. Both gates now stand, and both are commit-scoped.** Gate 1 closed on evidence at `dd94e122`;
gate 2 on evidence at `1b25c99d`. Neither is a permanent state. **Gate 2 re-runs if further
commits land before the merge** — and further commits *have* landed (`1478363e`, `423b24d5`,
`2fd20d71`), so it is already owed again at merge time. That is by design: `PDR-0039`'s rule was
*fire the re-verification at the merge, unconditionally*.

**2. The merge remains the owner's decision, and the gates do not authorize it.** Satisfying both
gates removes the reasons to wait; it does not make the merge an agent action. `PDR-0046` is
explicit — the merge to a public default branch publishes, and publication is not undone by
pushing again.

**3. The merge checklist still inherits `PDR-0043` trigger 2.** The nightly cron is deleted and
deferred, not fixed; the scheduler reads the default branch's file. Merging without restoring it
(or recording the PDR that kills it) converts a deliberate deferral into silent capability loss.

**4. The sweep is itself a defect-finder, and should be treated as one.** It filed
`hamlet-cbb747a51e`: `configs/reference/model_pack` compiles, prints `Compilation succeeded`,
exits 0, and silently writes **no cache artifact**. CI cannot see it because the gate runs
`validate`, which writes no cache — *the covered command and the broken command are not the same
command*, which is the `hamlet-2100105c9a` lesson recurring in a new place.

## Reversal trigger

- **Re-open the publish decision** if the branch approaches merge with the README's rough-edges or
  CI sections describing conditions that are *still accurate* (`PDR-0039`'s original trigger,
  unchanged). This session moved it the other way — the sections were accurate and are now fixed —
  but the test is applied at merge, not banked here.
- **Fire gate 2 again at the merge, unconditionally.** If a merge is proposed citing *this* PDR as
  the satisfied gate rather than a fresh sweep at the merge commit, that is the trigger and the
  merge waits. Three commits have already landed since `1b25c99d`.
- **Reverse the "fixed, not re-described" reading** if a future sweep finds the stale-claim count
  rising while the tree is unchanged — that would mean the README is decaying through drift rather
  than through repair, and the expiry rule is not doing its job.
