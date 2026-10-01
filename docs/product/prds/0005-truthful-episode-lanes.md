# PRD-0005 — Truthful episode lanes

Status: **implementation planned; implementation unaccepted**.
Prepared: 2026-10-02 Australia/Canberra. Source baseline: `95b2f828` (PR #44 main).
Decision: PDR-0157; planning resolution: PDR-0158. Bet: bounded integrity package inside continuing recovery.
Existing engine bug: `hamlet-d6fc84d147` (confirmed). Product scoping:
`hamlet-e484af6168`; planning handoff: `hamlet-87d3ef8e23`.

## Problem

An author comparing declared worlds or brains needs episode outcomes and learning
budgets to describe what agents actually experienced. On current main, two agents
dying at ticks 2 and 5 publish survival `[5,5]`, although only seven live transitions
occurred. Real runtime probes also reproduce a later retirement reward, continued
replay, novelty ingestion and episode completion after death.
[Baseline evidence](../evidence/episode-lanes/baseline.md) records what was executed
and what remains source-derived. Correct these boundaries before another learning
budget, so improvements cannot be manufactured by phantom experience or inflated
survival. This package establishes trustworthy inputs to a later learning study;
it does not establish convergence itself.

## Success metric and review window

**Episode accounting error**, an input metric in `metrics.md`: absolute difference
between the sum of published per-agent survival and independently counted live
transitions. Baseline **3** in the deterministic 2/5 fixture (`10 - 7`); target
**0**, with exact individual survival `[2,5]`. Correct aggregate arithmetic alone
cannot compensate for incorrect individual lanes.

Product acceptance review: **2026-10-09 Australia/Canberra**, or the first proposed
delivery candidate if earlier. This is a review window, not a shipment forecast.
If no complete candidate exists then, keep the package unaccepted and record a
scope/forecast review; do not silently extend the window or bank partial success.
Every criterion below must pass on one identified candidate by that review.

## Required episode semantics

An eligible transition belongs to a lane active **entering** a vector step. The
step that ends its episode counts once, including its terminal observation and
declared reward. A sticky terminal flag on subsequent ticks is not another event.
World/vector ticks and live-agent transitions are separate units.

An episode completes once per lane, whether through authored termination,
retirement, or an explicit runner cap/budget stop. Completed survival, accumulated
reward, final outcome and that lane's recorded completion-history entry remain
fixed until the next episode. Shared history can receive other valid completions.
Shared world clocks and shared model updates from valid experience
may continue while another lane is active; freezing a completed outcome does not
freeze the universe or its shared learner.

Retirement bonus is one-shot, only for a lane active on entry that reaches its
lifespan without an authored terminal condition on that step. **Authored death
wins when death and lifespan coincide.** An earlier death never becomes retirement
because other lanes or the world clock advance. Runner truncation is identified
separately from authored death/retirement; its bootstrap meaning must be resolved
and documented in planning rather than silently mapped to death.

## Acceptance criteria

1. **Runtime accounting:** the normal compile/environment/population path, with
   deterministic deaths at 2/5, reports survival `[2,5]`, seven live transitions,
   five vector ticks and one completion per lane. A terminal step is retained.
   Repeat with lane order reversed, one lane, simultaneous endings and unequal
   endings. Include a committed configuration-authored lifecycle witness through
   the compiler and supported brain construction; fixture-only state injection is
   insufficient for the authoring claim. Reject if any lane or aggregate differs
   from independent event counts or the authored witness is absent.
2. **Replay:** standard and prioritized replay each admit exactly seven fixture
   transitions, including exactly one terminal transition per lane. Recurrent
   replay contains exactly two completed sequences of lengths `[2,5]`, with no
   later one-step phantom episodes or cross-episode hidden-state leakage. Reject
   if a dead lane contributes again or a genuine terminal step is missing.
3. **Exploration eligibility:** when RND/adaptive exploration is enabled, predictor
   ingestion and normalization consume exactly the seven eligible observations;
   dead lanes supply none later. Adaptive episode completion receives survival
   `[2,5]` once each, with no later annealing checks attributable to repeated death.
   A witness identifies consumed rows, not just buffer length. Execute actual
   standard/PER/recurrent learner updates and an RND predictor update using
   identifiable eligible samples; verify terminal/truncation bootstrap treatment
   and absence of phantom samples in targets or predictor training. Shared updates
   from valid history remain allowed. Reject on extra/missing samples, completion
   calls, incorrect targets or absent update evidence; no convergence run is needed.
4. **Rewards and terminal outcomes:** a lane dying at 2 receives no reward or new
   contribution to its episode totals at ticks 3–5. The lifespan-5 boundary
   witness gives no retirement bonus to that lane or to a lane dying on tick 5;
   a genuine retirement gets its bonus exactly once. Capture final outcomes at
   completion so later mutable slots cannot revise them. Reject on repeated or
   misclassified terminal rewards, stale final outcomes or unaccounted reward changes.
5. **Consumers:** database, per-agent TensorBoard, curriculum, recording/evaluation
   outcomes and curves exports agree with the same completed lane events. For
   the fixture, published lane survival is `[2,5]`, live-transition budget delta
   is seven, and any batch-length output is explicitly five vector ticks. Record
   no post-terminal per-agent transition/action/reward as live experience.
   Curriculum receives each episode once; do not duplicate the existing batch
   completion route with an additional death route. Reject on disagreement or
   ambiguous units. Aggregate reporting is not required to become a per-agent DB schema.
6. **Other endings and restart:** cap/budget exits finalize surviving feedforward
   and recurrent lanes once at their actual eligible length; already completed
   lanes stay complete. Truncation semantics are explicit and tested. At least two
   consecutive episodes reset this package's counters, completion eligibility,
   recurrent accumulation and hidden state. Reject if an episode is lost, repeated
   or contaminates the next episode's accounting.
7. **Attribution and gates:** preserve a direct-parent trace/hash/reset baseline
   before edits; independently qualify intended reward, survival, replay and
   exploration-history changes, including frozen-oracle comparisons where the
   instrument can observe them. Record exact intended differences before cutting
   the seam; no broad allowances, frozen-input rewrites or oracle re-freeze. Use
   negative controls that would detect lost terminal steps and repeated completion.
   Relevant tests, fleet/lint/type/no-defaults and an unfiltered full suite pass.
   Reject on unexplained changes, hidden deselections or missing causal evidence.
8. **Independent acceptance:** read each criterion against retained evidence and
   the production callers at the candidate identity. Planning, implementation,
   local integration, hosted delivery and learning remain separate states. Reject
   any broader completion claim based on this fixture or on a green suite alone.

## Scope and guardrails

This is the eligibility, completion and truthful-accounting contract across the
existing environment, population, exploration and episode consumers. Preserve
supported compiled declarations and live-lane time/reward ordering except where
an exact intended terminal difference is recorded. No legacy counter readers,
compatibility outputs, fallback lifecycle paths or migrations. Historical training
artifacts are retained unchanged and keep their original semantics/source stamps.

Effects surviving reset (`hamlet-d76684f549`), initial-item cache fidelity, item
ownership/locality, RNG isolation, exploration warmup policy, general optimizer
schedules, checkpoint atomicity, browser UX, BAC cognition, Murk and a convergence
campaign are separately scoped. If a real witness proves one is a prerequisite,
stop and amend the scope in a PDR; do not quietly absorb it. This package resets
its own episode bookkeeping, not every simulation subsystem.

## Questions inherited by planning

- The baseline executes real replay, statistics and finalizers, with gradients
  suppressed. Actual learner/predictor updates and persisted-output witnesses
  remain necessary; do not treat admission counts as training qualification.
- Determine the current meaning of each scheduling clock. Any schedule declared
  in transitions must count live transitions; vector-tick or learner-update clocks
  retain their declared unit. No blanket change to every `total_steps` counter.
- Explicitly qualify cap/budget truncation, including recurrent sequence completion
  and bootstrap behavior. No new partial per-lane auto-reset is required.
- Agent-local meters can currently change after death. The contract fixes completed
  outcomes and dead-lane contributions; a complete shared-world/effect suspension
  policy needs its own evidence and is not inferred from this accounting fixture.
- The oracle-retirement instrument review remains open under PDR-0058. Passing
  this PRD does not terminalize divergences or replace recovery's exit.

## Handoff

Route this top item to **axiom-planning** for a source-validated implementation
plan and prerequisite probes. Route solution shaping to **axiom-solution-architect**
only where the plan establishes a design choice; route delivery forecast to
**axiom-program-management**. No file list, architecture or implementation sequence
is prescribed here. The existing engine bug remains open until its runtime fix is
verified; this product checkpoint dispatches planning, not a learning campaign.

## Planning resolution — October 2

[Implementation plan](../../plans/2026-10-02-truthful-episode-lanes.md) and
[planning evidence](../evidence/episode-lanes/planning/receipt.md) complete
`hamlet-87d3ef8e23`; execution is `hamlet-78ad37dd49`, unclaimed.
Actual authored construction, real updates, persisted sinks and pinned-oracle
probes now establish feasibility/parent defects; candidate acceptance remains absent.

Runner truncation closes a nonempty surviving episode without changing replay
MDP done, so stored-successor bootstrap remains valid. Normal configured cap
equals environment lifespan and remains retirement. Existing vector/optimizer/
batch clocks retain their units; RND cadence follows eligible sample occupancy.
Population owns completion snapshots; reset refuses an unfinished nonempty lane
before mutation until explicit completion. Checkpoint resume remains learned-state
at a fresh episode, with old population state refused.

Strict new DB/recording contracts and the ordinary producer-to-playback witness
are required; old historical artifacts remain unchanged. Ordinary recorder
shutdown was isolated in the probe, not qualified. No acceptance criterion or
October9 review window changes, and no convergence campaign is dispatched.
