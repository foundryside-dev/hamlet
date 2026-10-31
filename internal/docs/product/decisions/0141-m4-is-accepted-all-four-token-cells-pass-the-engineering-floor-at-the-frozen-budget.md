# PDR-0141 — M4 is accepted: all four token cells pass the engineering floor at the frozen budget

Date: 2026-09-02   Status: **accepted** (within the grant; owner-directed *"lets finish M4"*)
Author: Claude (standing product owner)
Related: `PDR-0132`, `PDR-0137`, `PDR-0138`, `PDR-0140`, `hamlet-25fc3fb955`, `hamlet-55b2826a02`,
`project-recovery-3@9d4e942f` (training source), `@e1615648` (evidence harness)

## Context

`PDR-0138` paused M4 with both feedforward cells terminal and both recurrent cells restart-safe
at roughly half budget, and named the conditions for acceptance: every cell passes the raw
79.19466666666668 greedy-survival floor at the full frozen seed-45 budget, the three evidence
defects are closed, the summary validates the raw values, and M4 has its own committed and
pushed checkpoint. `PDR-0140` closed the evidence defects. This record closes the qualification.

## What ran

Both recurrent cells were resumed on 2026-09-02 from a detached worktree at the exact pinned
snapshot `9d4e942f73bd3c84d56f87f129c38080a8fbe6e0` (`git worktree add --detach
/home/john/hamlet-m4 9d4e942f`), one per GPU, with their original commands plus `--resume`:

```
cd /home/john/hamlet-m4 && CUDA_VISIBLE_DEVICES=0 /home/john/hamlet/.venv/bin/python \
  /home/john/hamlet-m4/scripts/l2_token_regression.py train --architecture token_recurrent \
  --aggregator mean --brain-template /home/john/hamlet-m4/configs/benchmarks/l2_token_regression/brain_templates/token_recurrent_mean.yaml \
  --seed 45 --env-step-budget 2278640 --run-root /home/john/hamlet/runs/l2_token_regression --resume
cd /home/john/hamlet-m4 && CUDA_VISIBLE_DEVICES=1 /home/john/hamlet/.venv/bin/python \
  /home/john/hamlet-m4/scripts/l2_token_regression.py train --architecture token_recurrent \
  --aggregator attention --brain-template /home/john/hamlet-m4/configs/benchmarks/l2_token_regression/brain_templates/token_recurrent_attention.yaml \
  --seed 45 --env-step-budget 2278640 --run-root /home/john/hamlet/runs/l2_token_regression --resume
```

Resume validation matched every pinned identity (git SHA, source tree, harness blob, template
tree, template digest, cell, seed, budget). Each run restored its restart-safe checkpoint
(`checkpoint_ep01763.pt` at 1,181,395 transitions; `checkpoint_ep01722.pt` at 1,204,116), ran
to the frozen budget under the stop-before-vector-step rule, wrote its terminal checkpoint and
finalized `meta.json`, then failed at the known `scripts.l2_baseline` import — after the
evidence was already on disk, exactly as `PDR-0138` described. Each cell's metadata records two
training attempts, the second with `resume: true`.

Each terminal recurrent checkpoint was evaluated once from the same worktree under the frozen
protocol (100 episodes, 8 agents, eval seed 12345, cap 1000, greedy argmax over masked Q,
recurrent hidden state zeroed per episode):

```
cd /home/john/hamlet-m4 && CUDA_VISIBLE_DEVICES=<gpu> /home/john/hamlet/.venv/bin/python \
  /home/john/hamlet-m4/scripts/l2_token_regression.py eval --run-dir /home/john/hamlet/runs/l2_token_regression/<cell>/seed_45
```

The repaired harness at `e1615648` then wrote every cell's `curves.csv` and checkpoint-derived
`transitions.csv` (`scripts/l2_token_regression.py curves --run-dir …`) and produced the
four-cell summary (`scripts/l2_token_regression.py summarize --run-root runs/l2_token_regression
--output runs/l2_token_regression/summary.json`), which re-validates the 100 × 8 raw survival
values of every cell against the recorded mean, the budget rule and the cohort identity.

## The result

| cell | parameters | realized / requested | shortfall | episodes | train time (s) | raw greedy mean | median | verdict |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| feedforward / mean | 62,095 | 2,278,634 / 2,278,640 | 6 | 3,133 | 5,513 | **98.9925** | 99 | pass |
| feedforward / attention | 128,143 | 2,278,639 / 2,278,640 | 1 | 3,082 | 5,810 | **99.0** | 99 | pass |
| recurrent / mean | 194,191 | 2,278,638 / 2,278,640 | 2 | 3,206 | 6,469 + 2,722 | **97.315** | 99 | pass |
| recurrent / attention | 260,239 | 2,278,637 / 2,278,640 | 3 | 3,100 | 6,101 + 3,041 | **99.0** | 99 | pass |

Floor: 79.19466666666668. `summary.json`: `all_cells_passed: true`. Every mean is the exact
arithmetic mean of 800 raw agent outcomes. Recurrent/mean's 800 outcomes range 54–158.
Train times are the sum of the recorded attempts on one RTX 4060 Ti each; they are recorded,
not gated.

**Cohort identity (one value across all four cells, enforced by `summarize`):** git SHA
`9d4e942f73bd`, source tree `cf4900b34d82`, harness blob `58d796292d25`, template tree
`36719402310c`, token type-schema hash `8ad2b59b502a`, token layout hash `1149adc56d23`,
observation schema hash `7a134f0e5297`, pack brain hash `4f10939daf7a`. Per-cell compiled
brain hashes: `73f5df3e1237`, `1ea38c2bab47`, `13d71b16ecd2`, `963888e0d20e`.

**Artifact digests (sha256, first 16):** `summary.json` `5100097790007a9e`; `greedy_eval.json`
feedforward/mean `e98d24afebc920e9`, feedforward/attention `d063147973656166`, recurrent/mean
`f06e88c3bfedd9e4`, recurrent/attention `e036e59db099f686`. Every training checkpoint carries
its own `.sha256` sidecar and every `transitions.csv` ends at its cell's realized count.

**Structural acceptance** (batch 256 viable; no visibility, checkpoint-transfer,
recurrent-memory, BPTT or checkpoint-refusal regression) is carried by the suite that gated
`e1615648`: 3,837 passed / 11 skipped, with Ruff, Black, mypy, no-defaults, compiler-pack
validation and diff integrity green.

**Note on `checkpoint_episode` in `greedy_eval.json`:** it is one above the trained episode
count in every cell (3134 / 3083 / 3207 / 3101) because the runner sets its episode index to the
*next* episode after loading a checkpoint. A labelling convention, consistent across the cohort;
not an acceptance field.

## The call

**M4 is accepted.** The token-native feedforward and recurrent paths, with mean and attention
aggregation, each learn the shipped L2 task past the engineering floor under an equal, exact
transition budget on the strictest cheap deterministic representative, with structural contracts
intact and the evidence path repaired. `hamlet-25fc3fb955` closes with this record; the
`PDR-0138` per-cell discard-and-rerun rule was never triggered.

This is an engineering qualification, not a statistical claim (`PDR-0137`): one seed, one pack,
no interval, no generalisation beyond them. Recurrent/mean's 97.315 sits below the other three
and below the frozen baseline members; it clears the floor by a wide margin and is recorded as a
raw reading, not investigated here.

## Consequences

- Unit 5 (`hamlet-55b2826a02`) is unblocked on the M4 side. Its other precondition — the
  2026-10-06 disposition of every retired-corpus trial pack (`PDR-0082`…`0085`, `PDR-0114`) —
  is ruled before it starts.
- The four run directories under `runs/l2_token_regression/` remain the pinned local evidence;
  `summary.json` and the four `greedy_eval.json` files are copied under `docs/product/` so the
  raw values survive the ignored `runs/` tree.
- The `/home/john/hamlet-m4` worktree was only a checkout of a committed SHA and is removed.

## Reversal trigger

If any cohort artifact fails re-validation — a checkpoint digest, a `transitions.csv` final
counter, or `summarize` refusing a cell — the affected cell reopens under `PDR-0138`'s rule
and this acceptance is withdrawn for that cell until it is rerun on the pinned snapshot.
