# PDR-0146 — The fifth merge landed at `ea3648db`, `main`'s per-push CI fired, and work continues on `project-recovery-4`

Date: 2026-09-02   Status: **accepted** (a landing record, the `PDR-0130` shape; the merge was
the owner's DECIDE at this session's resume — *"Merge, then declaration-store"* — and is
autonomous under `PDR-0101`)
Author: Claude (standing product owner)
Related: `PDR-0101` (merge autonomous, gate 2 as quality gate), `PDR-0127` (gate 1), `PDR-0145`
(gate 2 for this merge), `PDR-0130` (the fourth landing), `PDR-0058` (the bet's exit, not met),
`PDR-0117` (the unit the owner chose next)
Evidence: PR #38 merged 2026-09-02T08:03Z; `main` = `ea3648db` (merge commit, parents
`9efadd3c` and `4e23b3ea`); 36 commits, 610 files, `PDR-0129`–`PDR-0144` plus this session's
two records; Lint, Tests and Config Validation all `in_progress` on `ea3648db` within a minute of
landing (`gh run list --branch main`); `Protect Main` ruleset (`lint` + `unit` required, strict
up-to-date, zero approvals) satisfied without a content-empty back-merge this time because the
branch already contained `main`.

## What happened

The owner ruled the merge first at the resume; gate 1 read green at `1eb347f7` by the
`PDR-0127` method (every per-push row at the tip), gate 2 was executed by method (`PDR-0145`),
and PR #38 opened with all six checks green on both the PR and push triggers.

**The merge itself was refused twice by the Claude Code auto-mode permission classifier**, not
by GitHub. The grant makes the merge autonomous (`PDR-0101`), but the harness gate sits below the
grant and blocked `gh pr merge`. The standing agent stopped and reported rather than working
around it; the owner granted the permission via `/permissions` and the merge executed on the
next attempt. This is worth recording because it is the first time the harness, rather than the
grant or GitHub, was the boundary — and because the correct response was to stop, not to route
around a denial.

`project-recovery-4` was cut from `ea3648db` and pushed. The bet's exit (`PDR-0058`) is not met —
the oracle is still required, WS-3 and WS-4 are open — so it is a recovery branch, not a release
branch.

## The call

- **`PDR-0101` reversal trigger 2 did not fire:** `main`'s per-push CI was not silent. All three
  workflows triggered at `ea3648db` within a minute. `hamlet-83c8e3b50e` stays terminal.
- **The Now bet is unchanged** (the strangler rewrite, `PDR-0006`). Its next unit is the
  **declaration-store compiler unit** (`PDR-0117`), per the owner's DECIDE. That unit's scope
  ruling is the next session's first act and is not preauthorised beyond the owner's choice of
  unit; three concrete inputs are already banked for it — the `period: 24` / `day_length: 24`
  duplication (`PDR-0143`), the `filler_ref` string contract wanting a typed scope (`PDR-0144`),
  and the silently-ignored stray files in `items_smoke` (`hamlet-obs-982755441c`).
- **The epistemic-access unit (`PDR-0120`) stays second in Next**, unchanged.
- **The authority grant's `Last reviewed` stamp moves `2026-08-31` → `2026-09-02`**, approved
  by the owner at the resume ("Confirmed, update stamp"). Scope unchanged; this record is the
  provenance the amendment log cites.

## Rationale

Merging at a unit boundary with both gates discharged is the cheapest point to bank 36 commits;
the drift had reached the level (`PDR-0068`, 26 commits) that has bitten before. Cutting the next
branch from the merge commit rather than continuing on `-3` keeps the branch-per-merge convention
that makes `gh run list --branch` a clean instrument.

## Reversal trigger

- If `main`'s Tests run at `ea3648db` or the first post-merge nightly is red, `PDR-0145`'s
  trigger fires (gate 2's CI reading must be re-derived at merge commits).
- If any later merge is CI-silent on `main`, `hamlet-83c8e3b50e` reopens as `confirmed` and the
  account-level diagnosis becomes the owner's to run (`PDR-0103`, unchanged).
- If the harness classifier blocks the merge again on a future session, the owner should
  consider a standing Bash permission rule for `gh pr merge`; until then the agent stops and
  asks, and the grant's "autonomous" merge is autonomous in intent but gated in mechanism.
