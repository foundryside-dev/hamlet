# PDR-0138 — M4 pauses at a restart-safe evidence boundary and remains open

Date: 2026-09-01   Status: **accepted** (owner-directed product checkpoint)
Author: Codex (standing product owner)
Related: `PDR-0132`, `PDR-0137`, `hamlet-25fc3fb955`, `project-recovery-3@9d4e942f`

## Context

M4's token-native feedforward/recurrent implementation and four-cell qualification harness are
committed and pushed at `9d4e942f`. The final source gate is green: 3,822 tests passed, 11 skipped,
and Ruff, Black, mypy, no-defaults, compiler-pack validation and diff integrity passed.

The owner requested a pause while the four seed-45 runs were active. Both feedforward cells had
already reached the frozen budget and completed their fixed evaluation. The recurrent cells
stopped through the runner's signal path at restart-safe checkpoints roughly halfway through the
budget. The pause also exposed three evidence-path defects in current M4 scope:

1. the train command completes and records a valid terminal checkpoint, then direct script
   execution fails at `from scripts.l2_baseline import cmd_curves`;
2. the inherited TensorBoard curve extractor labels duplicated batch episode length as
   all-agent transition accounting, overstating the authoritative persisted counter; and
3. a graceful early stop writes database `training_status=completed` even though M4 metadata
   correctly records `budget_compliant=false` and no `training_finished_at`.

## Options considered

1. **Accept M4 from the two passing feedforward cells.** Rejected: the recurrent half of the
   falsifiable architecture matrix is unfinished and known evidence defects would become debt.
2. **Discard all artifacts and rerun after repairing the harness.** Rejected: the source-bound
   terminal and restart-safe checkpoints are internally consistent; discarding them adds compute
   without improving the engineering question and erases useful interruption evidence.
3. **Checkpoint the pause, preserve the pinned artifacts, resume recurrent training on the exact
   source snapshot, then repair the evidence path before M4 acceptance.** Chosen.

## The call

M4 remains **in progress** and Unit 5 remains blocked. The two feedforward results are accepted as
partial evidence, not as milestone acceptance:

| cell | realized / requested transitions | shortfall | raw greedy mean | verdict |
| --- | ---: | ---: | ---: | --- |
| feedforward / mean | 2,278,634 / 2,278,640 | 6 | 98.9925 | cell pass |
| feedforward / attention | 2,278,639 / 2,278,640 | 1 | 99.0 | cell pass |

The recurrent runs resume from `checkpoint_ep01763.pt` at 1,181,395 transitions (mean) and
`checkpoint_ep01722.pt` at 1,204,116 transitions (attention). Because the run metadata pins the
git SHA, source tree, harness blob and template tree, resume must execute the exact
`9d4e942f73bd3c84d56f87f129c38080a8fbe6e0` snapshot; the product-checkpoint commit must not be
passed off as the training source. A second metadata attempt with `resume=true` is expected and
truthful. No evaluation exists for either recurrent cell.

The post-processing import, false curve accounting and misleading early-stop database status are
part of `hamlet-25fc3fb955`. They are repaired and tested before M4 closes; they are not observations
or deferred cleanup. The frozen acceptance denominator is the persisted
`completed_live_agent_steps` counter. Existing `curves.csv` cumulative totals are diagnostic only
and cannot be cited as budget evidence.

## Reversal trigger

Discard and rerun only an affected cell if its checkpoint checksum, pinned identity, resume
validation or raw evaluation artifact fails. A score below 79.19466666666668 remains an
engineering failure to debug, not permission to shop for another run. Do not start Unit 5 until
all four cells pass, the three evidence defects are closed, the summary validates the raw values,
and M4 has its own committed and pushed acceptance checkpoint.
