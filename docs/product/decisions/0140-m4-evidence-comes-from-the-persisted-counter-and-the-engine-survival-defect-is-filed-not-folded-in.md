# PDR-0140 — M4 evidence comes from the persisted counter; the engine survival defect is filed, not folded in

Date: 2026-09-02   Status: **accepted** (within the grant; owner-directed *"lets finish M4"*)
Author: Claude (standing product owner)
Related: `PDR-0137`, `PDR-0138`, `hamlet-25fc3fb955`, `hamlet-d6fc84d147`, `project-recovery-3@9d4e942f`

## Context

`PDR-0138` left three evidence-path defects inside M4 scope. Root-causing them on 2026-09-02:

1. **Curve import.** `cmd_train` ended with `from scripts.l2_baseline import cmd_curves`. Under
   direct script execution `sys.path[0]` is `scripts/`, not the repo root, so `scripts` is not a
   package and the import fails after a completed train. Reproduced: `ModuleNotFoundError`.
2. **False transition accounting.** The inherited extractor summed each agent's TensorBoard
   `Episode/Survival_Time`. That value is `env.step_counts[idx]` at episode end, and the
   environment increments `step_counts` for every agent, dead or alive
   (`vectorized_env.py:1178`), so each agent's "survival" is the batch episode length. Measured
   against the checkpoint-persisted `completed_live_agent_steps` on feedforward/mean: the
   overstatement is 402 transitions at episode 0 and grows monotonically to 93,478 at episode
   3133 (2,372,112 claimed versus 2,278,634 realized). The same value is what the run database
   stores as agent 0's `survival_time`, what the curriculum tracker is fed at episode end, and
   what the frozen baseline's own `curves.csv` column reports.
3. **Early-stop status.** `DemoRunner.run` wrote `training_status=completed` unconditionally in
   its `finally` block, so both half-budget recurrent pauses read `completed`.

The engine counter also feeds the reward calculator, the DAC engine and lifespan retirement.

## Options considered

1. **Mask the environment counter so per-agent survival becomes truthful, then sum agents per
   episode.** Rejected for M4: it changes reward and curriculum inputs under the pinned oracle
   and needs its own differential run and register entry. Folding an engine behaviour change
   into an evidence repair is how `PDR-0127`-shaped "green but wrong" instruments get made.
2. **Keep the TensorBoard extractor and annotate the overstatement.** Rejected: an artifact
   known to be false is not evidence, however labelled.
3. **Derive the transition artifact only from the authoritative counter the runner already
   persists in every digest-verified checkpoint, name the database column for what it is, and
   file the engine defect on its own.** Chosen.

## The call

- The M4 harness owns its artifacts and imports nothing from `scripts/l2_baseline.py`.
  `write_training_curves` writes `curves.csv` (`episode,batch_episode_steps,epsilon,
  intrinsic_weight`, straight from the run database with the column named for what the runner
  records) and `transitions.csv` (`episode,completed_live_agent_steps`, one row per checkpoint,
  each checkpoint digest-verified, monotone in episode order, and the last row equal to
  `meta.json`'s `realized_live_agent_steps` or the writer refuses). A `curves` subcommand runs it
  on any run directory, including the four cohort runs trained at `9d4e942f`.
- `summarize` refuses any cell whose `transitions.csv` is missing, non-monotone or does not
  end at the realized count. The cohort's identity gate is unchanged: the four runs stay pinned
  to `9d4e942f`; the repaired harness reads their evidence, it does not re-run them.
- `DemoRunner` records `training_status` from how the loop actually ended via
  `resolve_training_status`: `failed` on an exception, `completed` when the transition budget is
  reached, `interrupted` when a shutdown request stopped it short of the budget, and
  `completed` on the episode limit only when no shutdown truncated the final episode. Rationale
  for the ordering: a shutdown always truncates the episode it lands in.
- The two feedforward cells' old `curves.csv` files are replaced by the truthful pair; the old
  totals survive only in the `PDR-0138` and `metrics.md` readings that already flag them as
  diagnostic.
- The engine root cause is filed as **`hamlet-d6fc84d147`** (P1 bug, parent recovery
  milestone) with the measured overstatement, every consumer, and the fix shape. It is not an
  observation: it would be a defect whether or not M4 existed.

## Consequences

- Tests: five harness contracts (no baseline dependency; database-plus-checkpoint derivation;
  monotone/final-mismatch refusal; missing-digest refusal; summary gate) and six runner
  contracts (status resolution table, loop exit without cause refuses, budget completion,
  interrupted stop, training error). All written failing first.
- The four cohort databases keep `training_status=completed` for the paused attempts because
  they were written by the pinned `9d4e942f` runner; the truthful signal for those runs is
  `meta.json` (`budget_compliant`, `training_finished_at`) and `transitions.csv`. The
  continuation attempts are recorded by the same pinned runner and will also write
  `completed`, correctly, when the budget is reached.
- The frozen baseline's `curves.csv` transition column is now known-false and cited nowhere as
  budget evidence; correcting the baseline record rides on `hamlet-d6fc84d147`.

## Reversal trigger

- If any cohort run's checkpoint counters are non-monotone or the final checkpoint disagrees
  with `meta.json`, that cell's evidence is void and the `PDR-0138` per-cell discard-and-rerun
  rule applies.
- If `hamlet-d6fc84d147` lands and makes per-agent survival truthful, `curves.csv` gains a
  per-episode live-agent transition column derived from the database and `batch_episode_steps`
  is renamed or dropped under a successor PDR; `transitions.csv` remains the checkpoint-bound
  cross-check either way.
