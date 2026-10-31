# L1 fixed-budget canary, 2026-10-24

First fixed-budget training canary on current source (`fix/compiler-effects-remediation`,
clean worktree at `f007daaf`). Question asked: does HEAD still train to the WAIT basin?

## Run

- Command (from the worktree root; the wrapper is `scratchpad/canary/launch.sh`):
  ```
  CUDA_VISIBLE_DEVICES=0 PYTHONHASHSEED=0 PYTHONPATH=$PWD/src:$PWD \
    /home/john/hamlet/.venv/bin/python scripts/run_demo.py \
    --config configs/default_curriculum --level L1_full_observability --episodes 2000 \
    --checkpoint-dir <scratchpad>/canary/runs/L1_full_observability/canary/checkpoints \
    --inference-port 8799
  ```
  A sidecar polled `metrics.db` every 5 s and sent SIGINT once `sum(live_agent_transitions)`
  reached 500,000 (observed 503,314 at the signal). `run_demo.py` has no budget flag; the
  runner's `max_environment_steps` exists but `UnifiedServer` does not pass it.
- Seed: `training.yaml: seed: 42`, applied by `seed_all(42)` in `DemoRunner.__init__`;
  `PYTHONHASHSEED=0`. Two launches (a 700-episode trial that was stopped, then this run)
  printed identical survival at every heartbeat (episode 60: 29 steps in both) but slightly
  different intrinsic sums (1.16 vs 1.38), so the environment stream is seed-stable and the
  RND path on cuda is not bit-reproducible.
- Device: cuda, GPU 0 (RTX 4060 Ti). Wall-clock: 553 s from launch to exit (9 min 13 s),
  about 910 live-agent transitions per second, 0.4 s per episode early rising to 0.8 s at 99-tick
  episodes.
- Transitions: 503,762 live-agent transitions over 821 logged episodes (ids 0 to 820).
  820 ended `authored_terminal`; episode 820 was cut by the stop signal after 448 transitions
  (`completion_reason='shutdown'`) and is counted in the transition total but excluded from
  every survival and reward figure below.
- Outputs: `runs/L1_full_observability/canary/{metrics.db,tensorboard,checkpoints,training.log}`
  under `scratchpad/canary/`; per-lane series come from TensorBoard
  (`agent_*/Episode/Survival_Time`, `.../Total|Extrinsic|Intrinsic|Shaping_Reward`,
  `agent_*/Affordances/SLEEP`), epsilon and intrinsic weight from `metrics.db`.

## Survival against the budget

The runner has no greedy evaluation path (`training.yaml: evaluation.interval` is parsed and
nothing reads it), so these are per-lane survivals under the training policy
(epsilon-greedy). Each row is the ten complete episodes ending at the first episode whose
cumulative transition count crosses the mark; 8 lanes per episode, so 80 lane-episodes per row.

| budget | episode | transitions | mean survival | max | lanes > 99 | total reward | extrinsic | intrinsic | shaping | epsilon | intrinsic weight |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 10% | 137 | 50,521 | 51.8 | 76 | 0/80 | 36.4 | 34.4 | 1.84 | 0.15 | 0.503 | 1.0 |
| 25% | 289 | 125,985 | 70.9 | 92 | 0/80 | 49.0 | 46.4 | 2.45 | 0.19 | 0.235 | 1.0 |
| 50% | 484 | 252,196 | 86.7 | 96 | 0/80 | 58.5 | 55.5 | 2.74 | 0.23 | 0.088 | 1.0 |
| 75% | 656 | 378,341 | 94.3 | 99 | 0/80 | 62.7 | 59.8 | 2.61 | 0.29 | 0.037 | 1.0 |
| 100% | 820 | 503,762 | 97.6 | 99 | 0/80 | 64.5 | 61.8 | 2.45 | 0.24 | 0.016 | 1.0 |

Reference lines (CPU, same pack, measured by
`tests/test_townlet/regressions/test_null_policy_baseline.py`): WAIT-only 99 on every lane, mean
return 62.7 (extrinsic); uniform random 43 to 48; scripted sleeper 156 to 158.

Whole run: 6,560 lane-episodes. 36 lanes (0.55%) exceeded 99, all between episodes 110 and
674, best 157 (episode 490, lane 5). 275 lanes finished on exactly 99. SLEEP was used 161 times
across 97 episodes, falling by 100-episode bucket as 45, 44, 26, 25, 14, 5, 2, 0, 0; the last
SLEEP interaction was in episode 674. Last 100 episodes: mean 96.5, no lane above 99, 194 of
800 lanes on exactly 99, 606 below it (minimum 70); reward 63.9 total = 61.1 extrinsic +
2.56 intrinsic + 0.23 shaping.

Where the exploration knobs ended: epsilon 0.0164 (= 0.995^820; per-episode decay, the 0.01
floor was never reached). Intrinsic weight 1.0 for the entire run: `AdaptiveIntrinsicExploration.should_anneal`
(`exploration/adaptive_intrinsic.py:178`) requires survival variance below 100 **and** mean
survival over the last `survival_window` 100 episodes above `int(min_survival_fraction 0.4 x
max_steps_per_episode 1000)` = 400 ticks; no lane has ever approached 400, so the RND term
never anneals.

## Reading

1. The WAIT basin reproduces on current source: by the end of the budget mean survival is 97.6
   with a hard ceiling of 99, extrinsic return 61.8 against the null policy's 62.7.
2. The learner did not beat the null policy at any point in the budget. The best window mean is
   below 99, and the only lanes above 99 are isolated epsilon-driven episodes.
3. The rising curve is epsilon decay, not skill: survival climbs from the random-policy level
   (about 43) toward the WAIT level (99) exactly as epsilon falls from 1.0 to 0.016, and the
   residual lanes below 99 at the end are most plausibly lanes still paying movement cost
   (move 0.02 per tick); per-step actions were not logged, so that part is inference.
4. It found the bed: 161 SLEEP interactions, 36 lanes past 99, one lane at 157 (the scripted
   sleeper's ceiling), so the mechanic is reachable and the reward for it was paid.
5. It did not keep it: SLEEP use decays with epsilon and is zero in every one of the 145 complete
   episodes after 674. Nothing the learner saw in those 36 episodes moved the greedy action off WAIT.
6. The components tell the same story: extrinsic is 95% of return and is maximised by living
   99 ticks of `base_reward`; shaping stays under 0.3 per episode and intrinsic under 3, so
   neither carries a gradient toward the bed once the lane is sitting still.
7. Intrinsic weight never annealed and never will on this pack as configured; the gate is
   unreachable (`docs/remediation/second-opinion-path-to-green.md` §5 step 6, confirmed by measurement).
8. The episode-lane fixes did not change the learning outcome; they changed only what is
   counted (per-lane survival is now real, and shows the sub-99 lanes M4 could not see).
9. Mechanics note for the floors: 99 is energy passive depletion plus the declared
   satiation -> energy cascade (satiation crosses its 0.3 threshold at tick 88 and the cascade
   takes the last 0.01 one tick early); energy alone would die on tick 100. The regression test
   derives 99 from those declared parameters, not from a literal. Aside found on the way:
   `recovery.natural` is read only by the observation compiler; the runtime applies no natural
   recovery.
10. Next sprint is the WAIT-basin diagnosis, cheapest ablations first: epsilon schedule tied to
    the budget (it reached 0.03 by episode 700 with 1,300 of 2,000 episodes unused), the
    unreachable annealing gate, and whether the affordance token payload carries enough
    position signal for a flat net under `randomize_affordances: true`.
