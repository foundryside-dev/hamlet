# Population numerical qualification registered before runtime changes

Parent revision: `880f9c90f65aa646a0da04d7ca2ef92e48f85caa`.
Eight controlled CPU recipes use seed 42 and the compiled authored fixture:
standard/PER sequence length one and recurrent sequence lengths one/two, each
with vanilla and Double DQN. Each executes nine two/five episodes, learner
batch size two, train frequency one and RND predictor batch size seven.
Actions remain the authored WAIT/END_LANE schedule. Brain parameters and
configuration bytes are retained separately from the clean producer revision.

The coordinate identity is `(recipe, episode, tick, agent, field)`, with episodes
0 through 8, ticks 1 through 5 and agents 0/1. Parent receipts retain exact
reward, extrinsic, effective intrinsic, shaping, diagnostic intrinsic raw,
intrinsic weight and full Q-value rows, plus predecessor/successor digests,
actions, sticky dones, world ticks, reported survival and adaptive history.
Real Q and RND optimizer updates and parameter changes are observed in every
parent recipe. Each old normalization path consumes 90 observations rather
than the 63 independently eligible successor observations.

This registration grants no field-wide or stream-wide numerical exception.
After each source cut, the retained producer must repeat the same recipe and
bind every measured old/new changed coordinate to its actual causal commit.
Actions, world ticks, successor observations, meters and sticky dones remain
exact. Any changed live numerical coordinate needs the independent calculation
below and actual sample/target evidence; an unexplained change fails acceptance.
The no-exploration comparator's exact live-reward equality cannot be applied to
these learned, normalized recipes.

The independent entry ledger includes each terminal transition and gives
normalization batch sizes `[2,2,1,1,1]`, seven per episode and 63 in total.
Predictor ingestion selects the corresponding predecessor rows, retaining their
episode/tick/agent identities. No completed row enters either sample set.
Adaptive completion receives exactly 18 once-only outcomes, survival `[2,5]`
per episode. Actual replay samplers and loss hooks qualify terminal target
`reward` and nonterminal/truncated target `reward + gamma * successor Q`;
both vanilla and Double DQN retain their real target-selection paths.

The normalization reference begins at mean 0, variance 1, count `1e-4`.
For independently selected raw prediction errors, calculate the batch mean and
population variance, then combine old and batch second moments using the
parallel Welford formula. Normalize raw error by `sqrt(new_variance) + 1e-8`.
Reference raw errors come from the actual fixed/predictor networks at that
transition; retained before/after statistics and sample hashes expose omission,
phantom inclusion and repeated ingestion. Calculate the DAC total independently
from its three effective contributors; diagnostic raw novelty cannot replace
the intrinsic contributor. Dead contributions/weights are zero. Retirement
adds one to total and extrinsic once; authored death wins coincidence.

Finite reward/statistic reconciliation uses the plan's fixed numerical bounds,
`rel_tol=1e-5, abs_tol=1e-6`; identities, events, counts and sample membership
remain exact. Preserve optimizer ordering and existing warmup/cadence policy.
Exact causal receipts and independent reference assertions are still required
on the final candidate; this parent bank and registration are not acceptance.

Retained parent files are under
`runs/episode-lanes/2026-10-02/implementation/parent/population-numerics/reference/`.
Their source/import/helper/config identities and file digests belong in the
qualification receipt. Failed instrument setup and earlier captures are retained
separately. No historical training artifact or frozen fixture is rewritten.
