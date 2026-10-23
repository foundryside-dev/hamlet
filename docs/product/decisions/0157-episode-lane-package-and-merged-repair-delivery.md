# PDR-0157 — Scope episode integrity after merged repair delivery

Date: 2026-10-02 Australia/Canberra. Status: **accepted — planning scope**.
Author: Codex. Owner input: create the next-work branch; resume product management.
Standing authority: prioritize, write PRDs and dispatch within recovery strategy.
Related: PDR-0058/0155/0156; PRD-0005; recovery `hamlet-1ade187dcc`;
scope `hamlet-e484af6168`; existing bug `hamlet-d6fc84d147`.

## Context

The standing brief still says the access repairs are local. PR #44 has merged
at `95b2f828`; exact-main Lint, Config Validation and Tests are successful.
Hosted tests record 4,276 passed / 19 skipped / 15 warnings / 85% coverage,
distinct from retained local 4,277 / 18. The owner-requested next branch is
`fix/episode-lane-accounting`, created cleanly from this main.

Current-main probes reproduce deaths at ticks 2/5 reporting survival `[5,5]`
instead of `[2,5]`, ten replay/RND samples instead of seven, repeated finalization
and overwritten completed survival `[1,5]`. Recurrent lengths are `[2,1,1,1,5]`.
A lifespan-five witness grants a later bonus to the early-dead lane. Adaptive
history is polluted but weight stays 1.0; learner gradients and sink persistence
were not exercised. Existing runner live-transition budgeting already counts
correctly. [Baseline evidence](../evidence/episode-lanes/baseline.md) distinguishes
executed, source-traced and unmeasured claims.

## Options

1. Run another convergence campaign: its outcomes would depend on known phantom
   experience and inflated completion evidence.
2. Repair only the environment increment: leaves independently reproduced replay,
   RND and repeated-finalization failures and contradictory consumer outcomes.
3. Specify one bounded eligibility/completion/accounting package and hand it to
   planning, keeping unrelated reset/item/RNG and cognition work separate.
4. Redefine recovery's exit now: mixes a strategic instrument question with a
   local integrity defect and could manufacture an ending from publication.

## Call and rationale

Choose option 3. [PRD-0005](../prds/0005-truthful-episode-lanes.md) is ready for
planning in `hamlet-87d3ef8e23`; implementation remains unaccepted and no training
campaign is dispatched. Eligibility includes the terminal transition once;
sticky done is not another completion. World ticks and live transitions remain
separate. Correct completed outcomes and contribution eligibility rather than
freezing all shared world/model state.

Choose **authored death over retirement when they coincide**, with a one-shot
bonus only for genuine retirement. This removes the measured later-death bonus
and makes the boundary falsifiable; qualify the intended reward change against
parent/oracle evidence before implementation lands. Runner truncation/bootstrap
and scheduling units remain explicit planning questions, not silent defaults.

The headline input metric is episode accounting error: **3 → 0**, with exact
individual survival `[2,5]` and seven independently counted live transitions.
Product review is October 9 or the first delivery candidate, whichever is earlier;
this is not a delivery forecast. An absent or failing candidate remains unaccepted
and forces a recorded review rather than a silently extended clock.

Independent PRD review found two acceptance gaps: gradient-suppressed discovery
cannot qualify real learner/predictor updates, and shared history must still admit
other valid completions. Both are made explicit in the final criteria. The
coordinator repeated both baseline probes with byte-identical output.

## Recovery-exit disposition

PDR-0058's fired register-growth trigger remains **unresolved**, with five retired
and ten nonterminal entries in the fifteen-entry register. No existing exit
criterion, vision, strategy, authority or oracle identity changes here. The next
repair is justified by evidence integrity; its acceptance cannot be counted as
meeting a settled oracle-retirement outcome.

Route the concrete exit/instrument review to `hamlet-4554a428b2`: compare preserving
the existing three conditions with an explicitly recorded successor instrument,
using per-entry evidence and permanent-disposition PDRs where justified. Preserve
the frozen oracle and inputs throughout. Preparing that proposal is autonomous;
an actual strategy/exit change requires the owner's decision under the grant.
The task keeps the trigger actionable without pretending this checkpoint settles it.

## Delivery reconciliation and limits

[Hosted receipt](../evidence/static-access-review/hosted-delivery.md) closes the
repair's publication/CI uncertainty. The three repair bugs stay closed; the
episode bug is now confirmed, not fixed. No source qualification is inflated into
current-main convergence, CUDA, viewer or broader authorability acceptance.
No branch push, runtime edit, release, tag or deployment is performed by this PM
checkpoint. Prior PDRs remain append-only historical records.

## Reversal triggers

Re-scope before implementation if a fixture proves reset/item/shared-world
semantics are a prerequisite, if preserving the terminal transition conflicts
with an authored lifecycle contract, or if no narrow instrument can attribute the
intended behavior changes. Reject acceptance on any extra/missing live sample,
repeated completion, incorrect terminal target or consumer disagreement. Missing
the review window forces a recorded scope/forecast review; passing the package
does not reverse the separate recovery-exit warning.
