# Episode lanes — Current-main discovery baseline

Date: 2026-10-02 Australia/Canberra. Exact source:
`95b2f828dae4f52d6e30e79600fc3491364a1eb5`. CPU, seed 42,
Python 3.13.1, torch 2.11.0+cu130. Loomweave was fresh at this commit.
No runtime implementation, test, configuration or frozen-oracle file was edited.

## Executed environment witness

Copy shipped `default_curriculum` into a temporary directory, compile
`L0_0_minimal` without cache, create the real two-agent environment and reset.
Inject starting energy `[.015,.045]` and choose WAIT. Compiled passive depletion
and terminal conditions naturally end the lanes at ticks 2 and 5. This is a
controlled discovery fixture, not a configuration-authoring acceptance witness.

| Vector tick | Active on entry | Dones after step | Returned survival | Required survival |
| --- | --- | --- | --- | --- |
| 1 | `[true,true]` | `[false,false]` | `[1,1]` | `[1,1]` |
| 2 | `[true,true]` | `[true,false]` | `[2,2]` | `[2,2]` |
| 3 | `[false,true]` | `[true,false]` | `[3,3]` | `[2,3]` |
| 4 | `[false,true]` | `[true,false]` | `[4,4]` | `[2,4]` |
| 5 | `[false,true]` | `[true,true]` | `[5,5]` | `[2,5]` |

Both environment counters and `info["step_counts"]` end `[5,5]`: ten reported
transitions versus independently counted **seven live transitions / five vector
ticks**, with one newly-terminal event per lane. Accounting error is **3**.
The normal lifespan-1000 case returns zero for the dead lane on ticks 2–5.
Changing only the copied training configuration's lifespan to five produces
reward `[1,1]` at tick 5: the early-dead lane receives a retirement bonus later,
and the second lane receives one despite dying on the lifespan boundary.

The first lane's health also changes `.990 → .975` after death. This motivates
capturing a stable completed outcome; it does not by itself specify suspension
of shared world/effect state. PRD-0005 chooses authored death over coincident
retirement and preserves global tick progression.

## Executed population witness

Use the same compiled environment and starting state with the real population,
networks, replay, RND normalization and finalizers. Valid brain DTOs come from
existing test brain fixtures; this is not qualification of a fully authored BAC
path. Instrument the policy to choose WAIT and wrap finalization to record calls
while invoking its original implementation.

Q and RND predictor batch sizes are 128; the five-tick witness performs no
gradient updates. Recurrent learning additionally needs sixteen stored episodes.
Observed learner updates and predictor loss were zero. This isolates eligibility,
insertion, statistics and completion without claiming predictor/learning quality.

| Observed quantity | Standard | Prioritized | Recurrent | Required |
| --- | --- | --- | --- | --- |
| Live transitions / vector ticks | 7 / 5 | 7 / 5 | 7 / 5 | 7 / 5 |
| Stored transitions | 10 | 10 | 10 | 7 |
| Terminal replay rows | 5 | 5 | 5 | 2 |
| Completed registry survival | `[1,5]` | `[1,5]` | `[1,5]` | `[2,5]` |
| Predictor buffer samples | 10 | 10 | 10 | 7 |
| Normalization sample delta | 10.0 | 10.0 | 10.0 | 7.0 |
| Adaptive survival history | `[2,1,1,1,5]` | same | same | `[2,5]` |

Recurrent episode lengths are `[2,1,1,1,5]`. Each variant finalizes the early
lane at ticks 2/3/4/5 with arguments `[2,1,1,1]`, then the later lane at tick 5
with survival five. Adaptive weight remains **1.0**: polluted history and repeated
completion are measured; an actual weight change is not.

## Source closure and limits

At the baseline commit:

- `environment/vectorized_env.py:1178` increments every lane; `:1194–1199`
  checks persistent lifespan and adds a bonus without active-on-entry eligibility.
  Passive depletion and cascades use all-true masks at `:1242` and `:1250`.
- `population/vectorized.py:805–849` appends every lane to recurrent accumulation,
  feedforward replay and predictor ingestion. `:1073–1082` increments all counters
  and finalizes every sticky-done lane; `:575–587` records survival, updates adaptive
  history and resets the counter/hidden state.
- `environment/reward_calculator.py:24` updates RND statistics from the full
  observation batch; `exploration/rnd.py:203` admits every sample before DAC's done
  reward mask. RND `step_counter` is not an authoritative transition counter.
- `demo/runner.py:587–607` already counts live budget on entry correctly. Its
  `:700–704` curriculum route runs once at batch completion with inflated survival,
  not once per repeated death. DB/TensorBoard/recording consumers inherit those
  counters at `:727`, `:749`, `:768`; no fresh sink execution was performed here.
- `scripts/l2_baseline.py:195` greedy survival already uses live-entry accounting;
  curves export at `:256` inherits training TensorBoard counts. Do not label both
  paths broken. The historical M4 persisted transition counter remains valid.

The first three bullets are supported by the executed witnesses and source;
downstream persisted outputs are source-traced only. Actual learner/predictor
updates, cap/budget endings, direct/cache authoring witnesses, CUDA and oracle
qualification remain candidate-acceptance work. No suite gate or convergence
campaign was rerun. Confidence is high for measured counts and source ordering;
effects on trained-policy quality are unmeasured.

## Commands and custody

Both commands exited zero. The coordinator independently repeated both and
`cmp` found byte-identical logs before this documentation checkpoint.

```bash
.venv/bin/python runs/episode-lanes/2026-10-02/episode_counts_probe.py > /tmp/hamlet-episode-counts-replay.log 2>&1
cmp runs/episode-lanes/2026-10-02/episode-counts-probe.log /tmp/hamlet-episode-counts-replay.log
.venv/bin/python runs/episode-lanes/2026-10-02/episode_consumers_probe.py > /tmp/hamlet-episode-consumers-replay.log 2>&1
cmp runs/episode-lanes/2026-10-02/episode-consumers-probe.log /tmp/hamlet-episode-consumers-replay.log
```

Byte-preserved scripts are committed as [environment probe](episode_counts_probe.py.txt)
and [population probe](episode_consumers_probe.py.txt). They assert their original
HEAD and absolute checkout path deliberately; these are archived discovery
scripts, not reusable product entry points. Run against the pinned source only.
Raw ignored output remains under `runs/episode-lanes/2026-10-02/`:

| Artifact | SHA256 |
| --- | --- |
| `episode_counts_probe.py` | `0d35ffa9265fb78e69d3031bd13f868fabd1c9396a7d71ef280cb0d00e3116b0` |
| `episode-counts-probe.log` | `ab05d5e634bc1c816dde6d8996310d7be99501a525aaf58d9b3765bc69dacd3f` |
| `episode_consumers_probe.py` | `2ce0914bf3d5fb4ac1d4b58392b893d0eebbf49c26cc501994166ad30d900ffc` |
| `episode-consumers-probe.log` | `86c3fba8e2696bc9fb42250310dbd483a4818166fc35736fdc2fc52318056864` |

Tracker `hamlet-d6fc84d147` is confirmed with these observations, still unfixed.
Planning `hamlet-87d3ef8e23` inherits the complete acceptance contract in
[PRD-0005](../../prds/0005-truthful-episode-lanes.md).
