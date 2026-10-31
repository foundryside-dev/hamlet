# L2 pre-raster baseline — FROZEN RECORD

Date frozen: 2026-08-25 · Unit-3 Task 2 of the token-observation migration
(`hamlet-fa6bb6da4a`, plan `docs/superpowers/plans/2026-08-24-token-obs-unit3-baselines-div008-cut.md`)

**This record is the denominator for `PDR-0114` reversal trigger 1** (token encoding must
reach ≥80% of this baseline at equal env-steps). It never changes after this commit; a
re-measurement is a new record in a new directory.

## Headline

| quantity | value |
|---|---|
| **Seed-level IQM of greedy survival means (5 seeds, middle-3 trim)** | **98.99** |
| Mean of seed means | 99.14 |
| Range of seed means | 98.83 – 99.91 |
| Median greedy survival (every seed) | 96–99 |

The five seeds are statistically indistinguishable; the trigger-1 threshold (80%) is
**79.19** seed-level IQM greedy survival at equal env-steps.

## Engine pin

- `src/townlet` tree hash: `1a3b0e7cd1b151fa165911df4ae18d03a3ae3f4e` (see `PIN`,
  copied here; head at first seed launch `a766ee3d…`). The invariant is the engine
  *tree*, not the branch commit — docs commits between seed launches are harmless.
- Level: `L2_partial_observability` on `configs/default_curriculum` with the seed
  rewritten per run (each run dir carries its `pack/` copy and `pack.diff`).
- Trainer: `scripts/l2_baseline.py train` → `DemoRunner(max_episodes=5000)`.

## Compiled provenance (from each seed's final checkpoint)

Identical across all five seeds — the invariant surface the token cut will be measured
against:

| hash | value (16-hex prefix) |
|---|---|
| `observation_schema_hash` | `acf885d166176302` |
| `vfs_hash` | `fe66e748bef00c2e` |
| `drive_hash` | `b02aa064b2a03720` |
| `brain_hash` = `pack_brain_hash` | `5650add377963234` |
| `bars_hash` | `fce5fc6f2131c152` |
| `affordances_hash` | `af020ccd0e9f8754` |
| `curriculum_hash` | `e114176830bacabc` |

Per-seed (vary only because `training_hash` carries the seed):

| seed | `config_hash` | `training_hash` |
|---|---|---|
| 42 | `ddcc8c631745ea48` | `6abcb3eb2691e6c8` |
| 43 | `32a684f64a8d16fc` | `8ec5af87b55c71ed` |
| 44 | `d1c4ac4feff6ad9c` | `581194a24671c876` |
| 45 | `8e2c66abf4e575c4` | `77da9b9d85e23a57` |
| 46 | `312a1f305a9edf3c` | `0734da460019ead6` |

## Per-seed results

Greedy eval: 100 episodes, `--eval-seed 12345`, 8 agents, episode cap 1000. Protocol
(verbatim from `greedy_eval.json`): *"greedy: argmax over action-masked Q, epsilon 0,
no learning; survival = env.step calls an agent was alive entering, capped; agents stay
dead until the batch episode ends."* The evaluated checkpoint is each run's final
(shutdown) checkpoint.

| seed | GPU | realized episodes | realized env steps (cumulative, all agents) | eval checkpoint | mean survival | median | final ckpt sha256 (16-hex) |
|---|---|---|---|---|---|---|---|
| 42 | 0 | 3,797 | 3,322,056 | `checkpoint_ep03797.pt` | 98.9975 | 99 | `ceaff7b3632dfe9c` |
| 43 | 1 | 3,483 | 3,112,832 | `checkpoint_ep03483.pt` | 98.9975 | 99 | `2b0125d5fc8a885d` |
| 44 | 0 | 3,764 | 3,314,536 | `checkpoint_ep03764.pt` | 98.985  | 99 | `c04b92c04500623b` |
| 45 | 1 | 2,530 | 2,278,640 | `checkpoint_ep02530.pt` | 98.83   | 96 | `344065cfd80d7799` |
| 46 | 1 | 2,514 | 2,286,816 | `checkpoint_ep02514.pt` | 99.91125 | 97 | `ef86f2a68f6c0164` |

Full sha256 values sit beside each checkpoint as `.sha256` files under
`runs/l2_baseline/seed_<N>/checkpoints/` (local, gitignored — the record carries the
prefixes; the run dirs are the archival source). Per-seed `curves.csv` and
`greedy_eval.json` are committed in this directory under `seed_<N>/`.

## E=5000 was requested; realized episodes were wall-clock-truncated — accepted

Every launch command carried `timeout 43200` (a 12-hour guard). At the 12-hour mark
SIGTERM fired; `DemoRunner._handle_shutdown` performs a graceful shutdown — the final
checkpoint is saved and the process exits 0. The trainer's closing log line echoes the
*requested* episode count, which is why the logs claim "trained to 5000"; the curves,
checkpoints, and DB carry the truth above. Wave-1 seeds (42/43/44, launched 11:29) all
ended 23:29:26–30; seeds 45/46 (launched ~12:45, sharing GPU 1 throughout) ended ~00:45
with correspondingly fewer episodes.

**Ruling: accepted as the frozen baseline, no re-run.** Grounds:

1. The plateau calibration put convergence at ~episode 400; the shortest run (seed 46,
   2,514 episodes) is 6× past it, the longest 9×.
2. Training-curve plateau is flat to the end for every seed — agent-0 survival mean
   over the last 500 training episodes: 103.5 / 105.9 / 105.4 / 116.8 / 122.4 (seeds
   42–46), medians all 99, versus 105–109 at episodes 350–450. No seed was still
   improving when truncated.
3. Greedy performance is saturated and indistinguishable across seeds despite a 1.5×
   spread in realized episodes — episode count was not the binding constraint.
4. The `PDR-0114` comparison protocol is **equal env-steps**, and each seed's realized
   env-step count is recorded above and in its committed `curves.csv`
   (`total_env_steps_cumulative`); the token-side runs will be compared at matched
   env-step budgets per seed, so unequal episode counts do not contaminate the
   denominator.

## Determinism note (protocol refinement)

The earlier smoke-test observation "greedy eval is deterministic within seed — all
agents identical survival" was too strong for the full protocol. At 100 eval episodes
the per-agent distribution shows small variation (scattered 94–98s and occasional
longer episodes). One structural signature confirms the variation is driven by the
shared eval environment schedule, not policy stochasticity: episode 60, agent slot 6
survives exactly 158 steps under both seed 42's and seed 44's (independently trained)
policies. Survival clusters tightly at 99 — the episode-length boundary under this
pack, not the 1000-step cap.

## Reproduction

```bash
# Train one seed (12h wall-clock guard is part of the recorded protocol):
CUDA_VISIBLE_DEVICES=<gpu> UV_CACHE_DIR=.uv-cache timeout 43200 \
  uv run python scripts/l2_baseline.py train --seed <N> --episodes 5000 \
  --run-root runs/l2_baseline > runs/l2_baseline/seed_<N>.log 2>&1

# Greedy eval + curves:
CUDA_VISIBLE_DEVICES=<gpu> UV_CACHE_DIR=.uv-cache uv run python scripts/l2_baseline.py \
  eval --run-dir runs/l2_baseline/seed_<N> --episodes 100 --eval-seed 12345
CUDA_VISIBLE_DEVICES=<gpu> UV_CACHE_DIR=.uv-cache uv run python scripts/l2_baseline.py \
  curves --run-dir runs/l2_baseline/seed_<N>
```

Exact reproduction of the realized episode counts additionally requires the same GPU
sharing (42/44 alone on one GPU; 43/45/46 sharing the other) — or simply run to a
matched env-step budget, which is what the comparison protocol does anyway.
