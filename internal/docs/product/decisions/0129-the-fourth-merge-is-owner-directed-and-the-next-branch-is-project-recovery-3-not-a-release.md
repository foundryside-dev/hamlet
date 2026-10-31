# PDR-0129 — The fourth merge is owner-directed, the low-hanging fruit moves behind it, and the next branch is `project-recovery-3`, not a release branch

Date: 2026-08-29   Status: **accepted** (owner-directed: *"the path to merge now is approved,
create a PR and merge us back to main and then create a new branch for the next body of work as
either a recovery-3 branch or a regular release if it's more appropriate"*)
Author: Claude (standing product owner)
Related: `PDR-0058` (the merge is an output inside the bet, not its exit), `PDR-0101` (merge
autonomy), `PDR-0100` (publication = declaring 1.0), `PDR-0127` (gate 1), `PDR-0128` (gate 2),
`PDR-0103` / `hamlet-83c8e3b50e` (the per-push CI silence this merge decides)
Evidence: 143 commits / 921 files / 38 PDRs ahead of `main` at `04062872`; both gates
discharged the same morning

## Context

At the resume the owner asked *"do we have enough recovery to land main? or is there more low
hanging fruit?"* The assessment: yes — `main` is defined as the last state that passed both
gates, not as "recovered" — but not that morning, because gate 1 was red and gate 2 was owed on
140 commits. Cheap merge-relevant work was listed (delete the inert `observation_mode` /
`observation_encoding`, rule on `range_type`, close `hamlet-5fa1f7bfc0`, Dependabot #34) and
one thing explicitly *not* to take before the merge: the torch bump (#33), which can move the
oracle's bit-identical traces through TorchScript. The owner approved the path to merge as
stated.

## The calls

**1. Merge now, with both gates discharged, and move the fruit behind it.** Gate 1 was restored
(`PDR-0127`) and gate 2 executed (`PDR-0128`) before the PR. The inert-declaration tickets
(`hamlet-6a4a6596bd`, `hamlet-1e335e0363`) and the pytest bump are the first work on the next
branch, not a reason to hold the merge — the README names them honestly as open
(`PDR-0039`'s expiry rule is satisfied by re-verification, and `main` has merged with open
defects three times).

**2. The merge is a merge commit through a PR**, as the three before it, executed by the agent
under `PDR-0101`. It is also **the deciding test for `hamlet-83c8e3b50e`**: the third merge
triggered no per-push CI on `main`; if this one does, the anomaly was transient and the ticket
closes; if it does not, the escalation in `PDR-0103` stands and needs the owner's account-level
view.

**3. The next branch is `project-recovery-3`.** A release branch implies a coherent product
offering to release, and `PDR-0100` defines publication as declaring 1.0. The Now bet's exit
(`PDR-0058`: oracle retired, register terminal, verdict vocabulary re-earned) is not met; WS-3
and WS-4 are open; the tech-debt anti-goal is scoped "until 1.0". This is the third recovery
branch of the same bet, and naming it otherwise would be the roadmap-as-promise anti-pattern in
a branch name.

## Rationale

The merge is cheap and reversible in the sense that matters — `main` moves from one gated state
to the next — and holding a 143-commit branch longer only makes gate 2 dearer (43 commits cost
eighteen claims; 143 cost thirty-three). What is *not* cheap is a torch bump or a pack-census
change riding into `main` unmeasured, which is why those stay behind the merge and behind their
own PDRs.

## Reversal trigger

- If `main`'s first post-merge nightly is red, or the merge triggers no per-push CI **again**,
  the next merge waits on `hamlet-83c8e3b50e` being diagnosed, not on the next gate 2.
- If the recovery bet's exit conditions are met on `project-recovery-3`, the branch after it is
  the first that may be named for a release — and naming it so is a `PDR-0100` question for the
  owner.
