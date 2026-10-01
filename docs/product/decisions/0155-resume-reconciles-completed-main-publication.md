# PDR-0155 — Resume reconciles completed main publication

Date: 2026-10-01 Australia/Canberra
Status: **accepted — factual delivery reconciliation**
Author: Codex
Owner input: invoke the product-management skill.
Related: PDR-0154, PDR-0058; delivery `hamlet-dd9a03f787`; recovery
`hamlet-1ade187dcc`; proposed episode work `hamlet-d6fc84d147`.

## Context

The standing brief predates publication. Delivery is now closed. At the 08:17 UTC
resume reading, local main, origin/main and GitHub main all identify
`729779280820a31294013f9f7c839fbf23732ced`. PR #42 merged at 02:54:56 UTC today.

## Options considered

1. Leave the pre-publication brief unchanged: preserves history but misleads the next resume.
2. Reconcile delivery facts while retaining acceptance limits and the unresolved exit review.
3. Declare recovery complete or dispatch implementation: neither follows from delivery.

## The call

Choose option 2. Refresh current state and metrics; retain PDR-0154 as its historical snapshot.
No bet changes horizon and no recovery criterion, vision or authority grant changes.
No new implementation or learning campaign is dispatched by this invocation.

## Evidence and limits

GitHub was read directly with `gh pr view`, the main commit API and exact-commit run listing.
Actual-main Lint (36808063663), Config Validation (36808063655) and Tests (36808063683)
are completed/success. A separate Dependabot setuptools update (36808968679) failed;
this reading neither claims every workflow succeeded nor diagnoses that automation failure.
The retained hosted test log records 4,249 passed / 19 skipped / 15 warnings.
No test suite was rerun during this documentation-only resume.

The main tree equals published head `99d3d86b`; execution directories `src/townlet`,
`configs` and `frontend` are unchanged from qualified `b70fda10`. Seven retained
publication artifacts match the receipt's digests, as do both unrelated dirty skill files.
The [publication reading](../evidence/main-consolidation/hosted-publication.json)
banks delivery identities and workflow links; full logs remain under
`runs/main-consolidation/2026-10-01/`.

Tracker: 266 total, 159 done, 107 open, zero in progress; 103 ready and four blocked.
Delivery is closed; recovery remains planning and the episode bug remains triage.
No issue is claimed merely to resume ownership.

## Rationale

Completed delivery resolves the pending-publication pointer. It establishes no new
current-main authoring or learning outcome. PDR-0058's register-growth trigger remains
fired and unresolved; retaining that review prevents a merge becoming an implicit exit.

## Reversal trigger and next seam

Reopen this reading if its identities or retained receipt fail verification. Later main
changes require their own source and CI reading. Review the fired exit trigger, then
reproduce and scope truthful episode lanes before another learning campaign. Any
replacement strategy/exit proposal requires explicit provenance and the standing grant;
no replacement is enacted here. This checkpoint is local only; no push is performed.
