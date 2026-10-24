# Second opinion: the path to green

Written 2026-10-24 against `fix/compiler-effects-remediation` at `f007daaf` (dirty tree, 155
files modified in flight). Read-only review; one scratch script was run, nothing in the repo was
edited or committed. "Green" is taken as the owner defines it: `configs/default_curriculum`
trains, reproducibly, from YAML, with a reward stream a designer can believe.

## 1. The measurement that reframes the plan

The project's only learning witness is M4 (`docs/product/baselines/2026-09-m4-token-regression/`):
four token cells on L2 with greedy mean survival 98.99, 99.00, 97.32 and 99.00, accepted against
a 79.19 floor (PDR-0141). In the feedforward-mean cell's `greedy_eval.json`, 797 of the 800
evaluation lanes report exactly 99 and the other three report 97 or 98.

A scratch script on HEAD (CPU, 8 agents, one episode, `use_cache=False`) gives the context M4 lacked:

| policy on L1 and L2 (identical results) | survival (ticks) | mean return | SLEEP interactions |
|---|---|---|---|
| WAIT every tick | 99 on all 8 lanes | 62.7 | 0 |
| uniform random over the legal mask | 37 to 49 | 29.1 | 0 |
| 40-line scripted sleeper (walk to nearest SLEEP when energy < 0.35) | 155 to 158 | 101.6 | 16 |
| M4 trained greedy policy, four cells | 99 | not recorded | not recorded |

Energy starts at 1.0, depletes 0.01 per tick and is lethal at 0: a motionless agent dies at tick
100 with `step_counts` 99. The trained policy is numerically indistinguishable from the null
policy, and the accepted floor sat 20 points below it. The feedforward-mean training curve
agrees: across 3,133 episodes and 2.28M transitions, `batch_episode_steps` averaged 94.6, peaked
at 158, and exceeded 99 in 43 episodes. Epsilon-greedy found the bed a few dozen times and the learner never kept it.
One caveat: M4 ran before the `step_counts` masking fix (PDR-0140), so its 99 may be batch length
rather than per-lane survival; the curve ceiling of 158 still says the policy never left the
WAIT basin. The scratch numbers above are per-lane on the fixed counter.

Two consequences. First, nothing in the repo has ever shown a policy learning the simplest skill
the pack rewards (walk at most 14 cells, press INTERACT), even though the measured sleeper
collects 60 percent more return and lives 60 percent longer than standing still. Second, the sleeper's own ceiling at 158 is the next
rung: satiation hits zero near tick 125 and the cascade kills through health, so beating 158
means the WORK to EAT loop closed. Those two lines, 99 and 158, are the acceptance scale the
project has been missing. Every learning claim should be plotted against them.

## 2. What the green target actually executes

`configs/default_curriculum` declares `item_types: []`, `effect_definitions: []`, and one
variable (`day_phase`, derived from engine `tick`, legitimately batch-uniform). On L1 the pack
exercises: bars and cascades (VTC passive, threshold, terminal), fourteen instant affordances
with costs and randomized placement, DAC `constant_base_with_shaped_bonus` with the
`energy_crisis` modifier, RND intrinsic, action masking, affordance and meter tokens, the DQN
learner and the episode-lane accounting. All fourteen affordances declare
`interaction_type: instant`. L3 adds the clock and opening hours.

Checked against the review findings, the L1 reward stream is close to what the YAML says:
`energy_crisis` compares energy whose bounds are already `[0,1]`, so the raw-versus-normalized
defect (items I3) is inert here; `base_reward: 0.01` dodges the `or 1.0` default (I4); every
affordance is instant so `completion_bonus` pays once (I5). The two that bite are small:
`approach_reward` is Euclidean on a manhattan grid, and the +1.0 retirement bonus at tick 1000
has never been reached. On L3
the round-2 clock findings F1 and F2 (observed hour one tick behind the gating hour; reset
observation carries the previous episode's hour) do bite and are cheap.

Not executed by any shipped level of this pack: effects WP1 to WP9, items WP1, WP5, WP6, compiler
WP1 (`items_appearance`), strata WP4 (items off Grid2D), round-2 F3, F4, F7, F8, F9, and spec
items S1, S6, S7. The cross-subsystem sequence in `docs/remediation/README.md` put compiler WP1
and effects WP1 first. Both are correct fixes. Neither moves a reward L1 has ever paid.

## 3. Verdict on pin-and-sweep (question 1)

Pin-and-sweep is the right discipline and the wrong filter. The review method is excellent: every
finding reproduced by script, refutations recorded, P1s independently re-run. Keep all of that.
The defect is in what the sweep is pointed at. It is sweeping declared surface in subsystem
order, so it will converge on a VFS that is complete and correct for pair, message, items and
effects while the one pack the owner wants green still trains to WAIT. The plan also carries an
implicit assumption that is now falsified: that the learner works and the environment is what is
wrong. The measurement says the environment is roughly right on L1 and the learning loop fails
anyway. No amount of VFS correctness changes a policy that converges to doing nothing.

Of the candidates named in the brief:

- **Thin vertical slice first.** Yes, and it is nearly free: L1, feedforward, one brain, one
  seed, scripted baselines as the floor. This is the amendment.
- **Spec-decisions-first.** Rule S1 on paper now (independent worlds is the only reading
  consistent with agent capacity 0 and with DQN over 8 lanes). Implement nothing until a pack
  with authored globals exists. The identity rule (S3) should be gated on brain type as the
  reviewer says; it is a compile refusal, not a runtime risk.
- **Test-oracle-first.** The project already has a pinned oracle and sixteen registered
  divergences; it has not stopped any of the bugs above because it freezes behaviour, including
  bugs, and the owner dropped oracle gating on 2026-10-23. Golden traces for the slice are worth
  having as regression tests after the slice learns, not before.
- **Deletion-first.** Partially. Deleting what no pack executes shrinks the review target, but a
  cross-seam deletion sweep is a large diff with no learning payoff. Delete inside the slice's
  path first (`or 1.0`, dead required fields on `training.yaml` and `drive.yaml`), the rest as
  each seam comes up.
- **Integration-earlier.** Yes, but as a standing gate rather than a periodic shakedown: a
  20-minute GPU run of L1 with survival plotted against 99 and 158 after every merge to the
  slice path.

## 4. Wasted work and what will be reopened (question 2)

Most likely wasted, in the sense of correct work that does not move green: the items and effects
packages when sequenced ahead of the learner, the `boundary_wrap` differential cell (no shipped
level uses wrap), and the per-hash checkpoint gate hardening beyond the pack hashes already
landed (there are no checkpoints to protect). Expect to spend the remaining items and effects
WPs later, once a second pack needs them; do not spend them now.

Most likely reopened after locking:

- **S1, the batch model.** Any multi-agent level (`L5_multi_agent` exists) reverses
  "independent worlds". Lock the ruling, not the storage layout.
- **The tick and clock contract.** F2 (tick published pre-increment) was pinned by comment as
  oracle-load-bearing in `vectorized_env.py`; fixing it moves the reward stream on L3 and will
  be re-litigated against the differential harness unless the oracle's authority is settled first.
- **Episode-lane accounting.** PDR-0140 refused the counter fix as out of scope; it landed anyway
  a month later under PRD-0005. The same shape will recur for anything "locked" in VFS that
  the learner later needs (persistent state in checkpoints, F13, is the next candidate).
- **The DAC vocabulary.** Deleting `composition`, `IntrinsicConfig.*_config` and the
  `training.yaml: intrinsic` duplication is a decision about where exploration lives. If made
  before anyone has watched intrinsic reward interact with survival, it will be remade.

## 5. The next two weeks (question 3)

1. **Tomorrow morning.** Run L1 on HEAD on one 4060 Ti for a fixed budget (500k transitions,
   about 20 minutes at M4's rate of 413 transitions per second), with `Rewards/*` components and
   greedy survival logged per episode. Plot survival against the 99 and 158 lines. This either reproduces the WAIT basin on
   current source or shows the episode-lane fixes changed it. Either answer sets the sprint.
2. Promote the scratch script to `tests/test_townlet/regressions/`: WAIT-only survives 99, the
   scripted sleeper survives at least 150, and any future "learning result" must beat the first
   line to be called one. Retire the 79.19 floor in `metrics.md` with the reason.
3. Finish PR 53 and the in-flight compiler and effects WPs as they stand; they are done work.
   Then stop the items and effects streams and park their remaining WPs with a note.
4. Rule S1 in `variables.md` as independent worlds, refuse authored `global` writes from
   per-agent contexts at compile until a per-world axis exists, and leave `pair` and `message`
   alone. Half a day, no runtime change.
5. Fix the small L1 reward truths: `or 1.0`, `approach_reward` by declared metric, and the L3
   clock pair F1 and F2 (with the oracle comment deleted; the register records it).
6. Diagnose the WAIT basin on the slice. Candidates, cheapest first: epsilon reaches 0.01 near
   episode 900 of 3,133 with a per-episode decay that ignores budget; intrinsic weight never
   anneals because `min_survival_fraction: 0.4` of 1000 is unreachable; replay targets or
   masking at the terminal step; randomized affordance positions making the bed unlearnable for
   a flat net without the affordance token payload carrying position. Measure each by one
   ablation run, not by reading code.
7. Iterate the slice until greedy survival beats 158 on three seeds. This is the first learning
   result the project will have had. Record it as a baseline with the scripted floors beside it.
8. Widen to L2 (same tensor, visibility only) and L3 (clock). Expect L3 to expose the opening
   hours and 24-tick literals; fix them then, when the pack exercises them.
9. Reopen the sweep with the pack as the filter: for each remaining WP, ask whether a shipped
   level executes the line. Those that do go next; those that do not wait for a second pack.
10. Only then the second pack (a world with items and effects), which is where the parked items
    and effects WPs stop being speculative and the S1 ruling gets its first real test.

## 6. The single measurement (question 4)

It has been run and is in section 1: the null-policy and scripted-policy survival on L1. It took
one script and four minutes, and it says the accepted learning evidence is a do-nothing policy.
The follow-on measurement, step 1 above, is the one that decides the first sprint: does current
HEAD still train to 99.

## 7. State facts to carry

- The working tree does not collect: `tests/test_townlet/unit/demo/test_presentation.py` fails
  on `PresentationError` import. 4,751 tests collect otherwise. Nobody should read that count as
  green until the in-flight compiler WP4 lands or the test is updated.
- M4 trained at 413 transitions per second (52 vector steps of 8 lanes) on one GPU. Two GPUs
  are present. Budget runs are cheap; the project has been treating them as expensive.
- Scratch script: `/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/null_policy.py`
  (session scratchpad; copy it into the repo under step 2 before it is lost).
