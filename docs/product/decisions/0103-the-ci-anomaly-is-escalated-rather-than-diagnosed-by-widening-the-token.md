# PDR-0103 — The post-merge CI anomaly is escalated, not diagnosed by widening the agent's own token scope

Date: 2026-08-20   Status: **accepted** (escalation is the grant's default; the *restraint* is the decision recorded here)
Author: Claude (standing product owner)

Related: `PDR-0101` (merge autonomy, whose second reversal trigger this bears on), `PDR-0102`
(gate 2), `PDR-0039` (the gates)
Artifacts: `hamlet-83c8e3b50e` (P1)

## Context

The third merge landed at `04062872`. **It triggered no per-push CI on `main` at all** — the tip
has zero check-runs, while both prior merges fired Lint, Config Validation and Tests within
seconds of landing. Established before concluding: all four workflows report `active`; `main` is in
the `push` trigger list of each; Actions permissions are `enabled: true, allowed_actions: all`;
nothing is queued or in progress repo-wide.

The remaining candidate causes — an Actions usage or spending limit on the account, a transient
GitHub incident, a ruleset change since 2026-08-16 — all need **account-level** visibility. The
billing endpoint returned 404 with an explicit remedy: `gh auth refresh -h github.com -s user`.

## Options

1. Run `gh auth refresh -s user`, read the billing/usage data, and diagnose it now.
2. Establish what can be established without widening scope, file it P1, and escalate.
3. Treat the PR's green checks as sufficient and say nothing.

## Call

**Option 2.** Filed `hamlet-83c8e3b50e` P1 with the full measurement set, and escalated to the
owner in `current-state.md` and the session summary.

## Rationale

Option 1 is the tempting one and it is wrong. The grant authorises the agent to merge; it does not
authorise the agent to **widen its own credentials** to the owner's account settings. A token scope
is not a tool — it is a standing capability that outlives the task it was acquired for, and
acquiring one to satisfy present curiosity is the precise shape of an agent quietly expanding its
own authority. The remedy was even printed by the tooling, which makes taking it feel routine;
that is what makes the restraint worth recording rather than assuming.

Option 3 is worse and was never close. The merged code *was* validated — PR #36's own `lint`,
`validate-config-packs` and `unit` checks all passed against the merge preview, and the full suite
ran 3281/16/0 locally — but that is not the same as `main`'s push gates reporting on `main`, and
`README.md` (freshly re-verified hours earlier) states that they do. Letting a green PR stand in
for a gate that did not run is exactly the "green over a hole" pattern this project has now found
three times (`PDR-0092`'s scopes, `hamlet-a141ab5db3`'s silent cache, and now this).

**Bearing on `PDR-0101`.** Its second reversal trigger is *"a merge that lands a red gate on
`main`"*. No gate ran at all. That is **neither fired nor cleared**, and it is recorded that way
rather than resolved in the convenient direction — the trigger's spirit is exposure on the default
branch, and an unmeasured branch is exposure of a different kind. The 06:00 UTC nightly
(`Full Test Suite`) runs against `04062872` and is the reading that settles it.

## Reversal trigger

1. **If the nightly on `04062872` is red**, `PDR-0101`'s trigger 2 has effectively fired: merge
   autonomy reopens, and the gate reading must move from branch tips to merge commits before the
   next merge.
2. **If the nightly is green but push CI still does not fire on the next merge**, the README's
   claim that the three gates trigger on `main` is false and must be corrected at the next gate 2 —
   and the repo's Actions configuration becomes a prerequisite of merge autonomy, not a detail.
3. If the owner grants the wider token scope explicitly, this PDR is superseded rather than
   quietly ignored — the restraint was the decision, so lifting it is also a decision.
