# PDR-0130 — The fourth merge landed at `9efadd3c`, `main`'s per-push CI fired, and `PDR-0103`'s escalation closes by observation

Date: 2026-08-29   Status: **accepted** (a landing record, the `PDR-0073` shape; the merge
itself was decided in `PDR-0129`)
Author: Claude (standing product owner)
Resolves: the escalation in `PDR-0103` (the third merge's CI silence, `hamlet-83c8e3b50e`)
Related: `PDR-0129` (the merge decision), `PDR-0127` (gate 1), `PDR-0128` (gate 2), `PDR-0101`
Evidence: PR #37 merged 2026-08-29; `main` = `9efadd3c` (merge commit, two parents); check-runs
at `9efadd3c` = 3 within ~60 s of landing; Lint and Config Validation `completed/success`,
Tests `in_progress` at the time of this record (`gh run list --branch main`); ruleset
`Protect Main` created 2025-11-05

## What happened

`gh pr merge 37 --merge` was refused once: the `Protect Main` ruleset (2025-11, predating the
recovery) requires the head to be up to date with `main` and the `lint` / `unit` PR checks to
pass. `main`'s only commit not on the branch was PR #36's own merge commit, so a
**content-empty** merge of `main` into `project-recovery-2` (`1b4020aa`, empty diff-stat)
satisfied the rule; both required checks passed on both triggered runs; the merge landed as a
merge commit, the fourth in the series (`07b26ed5`, `4222a917`, `04062872`, `9efadd3c`).

`project-recovery-3` was cut from `9efadd3c` and pushed. The bet's exit (`PDR-0058`) is not met,
so it is a recovery branch, not a release branch (`PDR-0129` call 3).

## The call

**`hamlet-83c8e3b50e` is terminal as `not_a_bug`** (the tracker refuses `triage → closed` for
bugs, and "not a bug" is the honest reading): the third merge's silence at `04062872` was real
and is unexplained, but it was **transient** — the fourth merge triggered all three per-push
workflows on `main` within a minute. `PDR-0103`'s restraint — file, escalate, do not widen the
agent's own token scope to diagnose an account-level setting — stands as the right call and
needed no reversal: the question answered itself on the next observation, at zero cost.

## Rationale

An escalation that can be closed by waiting for the next natural observation should be, rather
than by acquiring capability to force the answer. That is the general shape of `PDR-0103`, and
this is its first confirmation.

## Reversal trigger

- If `main`'s Tests run at `9efadd3c` or the first post-merge nightly is red, `PDR-0128`'s
  trigger fires (gate 2's CI reading must be re-derived at merge commits, not branch tips).
- If any later merge is CI-silent on `main` again, `hamlet-83c8e3b50e` reopens as `confirmed`
  and the account-level diagnosis becomes the owner's to run — the agent still does not widen
  its own scope.
