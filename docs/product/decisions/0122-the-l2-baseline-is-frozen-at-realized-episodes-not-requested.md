# PDR-0122 — The L2 baseline is frozen at realized episodes, not requested; the truncation is recorded, not re-run

Date: 2026-08-25   Status: **accepted** (within grant: acceptance of dispatched work
against criteria)
Author: Claude (standing product owner)
Related: `PDR-0114` (this record is trigger 1's denominator), `PDR-0108`
Record: `docs/product/baselines/2026-08-l2-preraster/record.md` (commits `ce779a62` +
`0163d090`)   Tracker: `hamlet-fa6bb6da4a` comment 249

## Context

Unit-3 Task 2 requested E=5000 per seed. Every launch command carried a 12-hour
`timeout 43200` guard; at the 12-hour mark SIGTERM fired and `DemoRunner` shut down
gracefully — final checkpoint saved, exit 0, and the trainer's closing line echoing the
*requested* count, which is why the logs claim "trained to 5000". Realized: 3,797 /
3,483 / 3,764 / 2,530 / 2,514 episodes (seeds 42–46), the spread tracking GPU sharing.

## Options

1. Re-run all five seeds without the guard (~12h+, both GPUs).
2. Accept the realized-episode runs and freeze the record with the truncation stated.

## The call

Option 2. Seed-level IQM of greedy survival means **98.99** (5 seeds, middle-3 trim);
trigger-1 threshold **79.19** at equal env-steps.

## Rationale

Plateau calibration put convergence at ~episode 400; the shortest run is 6× past it,
curves are flat to the end for every seed, greedy performance is saturated and
indistinguishable across a 1.5× spread in realized episodes — episode count was not the
binding constraint. Decisively: the `PDR-0114` comparison protocol is **equal
env-steps**, and each seed's realized env-steps are recorded in its committed
`curves.csv`, so the token-side runs compare at matched budgets per seed. A re-run
would buy no information the protocol uses.

## Reversal trigger

If the token-side comparison cannot be run at matched env-step budgets per seed (the
protocol's assumption fails in practice), the baseline is re-minted without the
wall-clock guard as a successor record in a new directory — this record itself never
changes.
