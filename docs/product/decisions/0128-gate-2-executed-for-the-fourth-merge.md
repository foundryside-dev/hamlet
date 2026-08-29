# PDR-0128 — `PDR-0039` gate 2 executed for the fourth merge: 33 stale claims and 16 omissions in 143 commits, and the adversarial pass found six defects in the draft's corrections

Date: 2026-08-29   Status: **accepted** (gate execution within the grant, per `PDR-0101`)
Author: Claude (standing product owner)
Related: `PDR-0039` (the gate and its method), `PDR-0048`, `PDR-0072`, `PDR-0102` (the three
prior executions), `PDR-0127` (gate 1, restored the same morning)
Artifacts: `README.md` stamped at `1065dbf0`, committed at `6fb148fd`; sweep, draft notes and
adversarial findings retained in the session scratchpad (`gate2-sweep.md`,
`gate2-draft-notes.md`, `gate2-adversarial.md`)

## Context

The owner approved the path to the fourth merge at the 2026-08-29 resume. 143 commits had landed
since the last stamp (`4a225d84`, 2026-08-19) — the largest range any execution has covered, and
it included the unit-3 token cut, the archive recut and recovery, the compiler cleanup, and the
47-push Lint red. The method is fixed by `PDR-0039` and is not a re-read: ground-truth sweep →
draft from verified facts only → adversarial pass, run as three separate agents so the drafter
cannot mark its own work.

## What it found

**Thirty-three stale, wrong or misleading claims and sixteen material omissions.** The largest:
the observation ABI replaced outright (TokenSpec; `ObservationSpec`, the activity mask and the
raster encoders deleted) with no mention; the oracle section describing six register entries
and two adjudication shapes where there are eleven and three, and a green harness run now
meaning *diverged exactly as registered*; "seven" consecutive Lint reds where there were 47; the
third merge and `main`'s missing per-push CI (`hamlet-83c8e3b50e`) absent; 16/17 hash fields
where there are 19 and a v4 checkpoint format; `docs/config-schemas/` described as "archived
rather than maintained" three days after `PDR-0125` restored it with banners; three "known rough
edges" already fixed; a pack census of 33/15/10 where it is 38/19/11.

**Six defects in the draft's own corrections**, caught by the adversarial pass before stamping:
PR #36 carried 41 commits, not the 43 in its title; the Lint step order was inverted (the
no-defaults linter runs *last* and can mask nothing — the failing step rotated no-defaults ×7 →
Black ×9 → `ruff` ×23 → Black ×7); a commit dated 08-25 local was 08-24 UTC; `presentation.md`
was restored by a unit-3 cut commit seven minutes before `PDR-0125`'s first commit, not "under"
it; only one of three ✅ banners records a *clean* pass; a commit count taken against HEAD while
the stamp named the previous commit. Plus two time-flip risks (an unstamped nightly count; a
Tests run described as in progress that had finished) and one forward reference to a decision
record that did not yet exist.

**The sweep was wrong twice and the drafter caught it** — a banner count (12 of 13, not 11) and
a fact supplied by the controller (Black "joined from 08-25"; the run logs show it failing from
08-22). Three layers, each catching the one before, is the argument for the method.

## The result

Gate 2 is **discharged** for the fourth merge. `README.md` is stamped at `1065dbf0`, where Lint,
Config Validation and Tests all completed green; `6fb148fd` differs from it in the README only.
Every claim about `main` is written to survive becoming `main` (`PDR-0072`): the token-cut
sentence is a command the reader runs, the nightly count carries a date, and no sentence of the
form "the merge that carries this file…" survives. The draft is +125 net lines over the prior
README after ten cuts; length is not a gate and no verified claim was cut to reach a number.

## Reversal trigger

- If the first nightly on `main` after the fourth merge is red, the stamp's central CI claim
  was wrong and gate 2's CI reading must be re-derived at merge commits, not branch tips
  (`PDR-0102`'s trigger, re-armed).
- If the next execution finds fewer than ten stale claims across a comparable range, treat it as
  a sweep that was not run, not as a README that stayed true.
