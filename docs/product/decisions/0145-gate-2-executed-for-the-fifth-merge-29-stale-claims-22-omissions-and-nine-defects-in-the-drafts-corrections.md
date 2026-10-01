# PDR-0145 — `PDR-0039` gate 2 executed for the fifth merge: 29 stale claims and 22 omissions in 39 commits, and the adversarial pass found nine defects in the draft's corrections

Date: 2026-09-02   Status: **accepted** (gate execution within the grant, per `PDR-0101`)
Author: Claude (standing product owner)
Related: `PDR-0039` (the gate and its method), `PDR-0048`, `PDR-0072`, `PDR-0102`, `PDR-0128`
(the four prior executions), `PDR-0127` (gate 1), `PDR-0101` (the merge is autonomous; gate 2 is
a quality gate the agent executes)
Artifacts: `README.md` stamped at `1eb347f7`, committed with the CLAUDE.md corrections at
`4e23b3ea`; sweep, draft notes and adversarial findings retained in the session scratchpad
(`gate2-sweep.md`, `gate2-draft-notes.md`, `gate2-adversarial.md`, `runs.tsv`)

## Context

At the 2026-09-02 `/own-product` resume the owner chose *merge, then declaration-store* and
re-confirmed the grant with the review stamp to be updated. Thirty-nine commits had landed since
the previous stamp (`1065dbf0`, 2026-08-29): the M4 four-cell qualification, the token LSTM, the
whole of unit 5, and the fifty-first checkpoint. The method is fixed by `PDR-0039` and is not a
re-read: ground-truth sweep → draft from verified facts only → adversarial pass, three separate
agents so the drafter cannot mark its own work.

## What it found

**Twenty-nine stale, wrong or misleading claims and twenty-two omissions** (103 claims checked,
69 true). The largest: the fourth merge itself absent (PR #37 → `9efadd3c`, with `main`'s per-push
CI firing and `hamlet-83c8e3b50e` closed as not-a-bug while the README still called it an open
P1 gap); the width paragraph describing a 4,090-float projection deleted at `d554fb7f` and calling
`day_phase` "live but unexposed" when it is exposed (L1 is 118 floats compact, census self 1 /
meter 8 / affordance 14 / item 2 / variable_element 1); a register of eleven entries where there
are twelve (`DIV-012` built) and every cell binding four; CI totals two weeks stale; a pack census
half-corrected (38/35 alongside 29/26); `aspatial_test` "never validated by CI" when the pack
smoke test now exercises it under the Tests job; a closed bug listed twice as open. The
omissions: M4, the token LSTM, every unit-5 landing, the closed umbrella, the two new P1 bugs.

**Nine defects in the draft's own corrections**, caught by the adversarial pass before stamping:
"two P1 bugs open" where the tracker holds fifteen in `triage` (and the README itself named three
more ninety lines later); "the first recovery branch with no red at all" when the original
`project-recovery` was also all green (24 runs, 7 shas, one day); three dates written in local
time under the file's own "dates here are UTC" rule (`5973f79b`, `0b659130`, the
`oracle-2026-08-17` tag); a hash-field history that credited the token cut with two fields that
landed at `a1256837` beforehand (the true sequence is 16 → 17 → 19); the full-matrix adjudication
run framed as current at the stamp when `report.json` names `430eb5af`, twelve commits earlier; a
README sentence about CLAUDE.md made false by the CLAUDE.md fix in the same commit; and the
CLAUDE.md hunk itself calling three commands "the CI set" while the Lint job also runs mypy. The
adversarial agent counted fourteen P1s; the tracker's own status filter returns fifteen. Every
ratio and byte figure recomputed clean.

**The drafter also caught four slips in its own first pass** (a 25.8× ratio that is 34.7×,
`run_demo.py` mis-credited as the M4 driver, "two" profile cells that are four, "three days" that
is two) and disagreed with the sweep five times, each settled by command — including refusing to
write two sweep-supplied facts it could not reproduce (a field-union count; M4 protocol
parameters absent from `summary.json`). Three layers, each catching the one before, remains the
argument for the method.

## What else the gate surfaced

- CLAUDE.md's "no workflow has ever run on `project-recovery`" caveat, false since 2026-08-15 and
  carried as observation `hamlet-obs-5f1ea6c254` with a "fix at next touch" trigger, had
  survived a CLAUDE.md touch that morning (`1eb347f7`). Corrected in the stamp commit along with
  the dead "`CuesCompiler` instantiated at `compiler.py:69`" claim (deleted at `bb43e024`);
  the observation is dismissed as resolved.
- `configs/test/items_smoke` carries files no loader reads (`drive_as_code.yaml`,
  `substrate.yaml`, `experiment.yaml`) and pack-root duplicates of level files. Not deleted at the
  merge (fixture-diff blast radius unmeasured; the oracle fixture mirrors them); filed as
  observation `hamlet-obs-982755441c` — a concrete forcing case for `PDR-0117`'s "unknown or
  duplicate declaration refuses loudly" rule.

## The result

Gate 2 is **discharged** for the fifth merge. `README.md` is stamped at `1eb347f7`, where Lint,
Config Validation and Tests all completed green; `4e23b3ea` differs from it in README.md and
CLAUDE.md only. Every claim about `main` is written to survive becoming `main` (`PDR-0072`):
commands use `origin/main`, static numbers are dated and commit-named, and no sentence of the
form "this branch" or "the merge that carries this file" survives.

## Reversal trigger

- If the first nightly on `main` after the fifth merge is red, the stamp's CI claim must be
  re-derived at merge commits, not branch tips (`PDR-0102`'s trigger, re-armed).
- If the next execution finds fewer than ten stale claims across a comparable range, treat it as
  a sweep that was not run, not as a README that stayed true (`PDR-0101` trigger 1).
- A "fix at next touch" observation that survives a touch is a trigger that nobody read: the
  resume protocol now checks pending observations against `git log` for their named file. If a
  second one slips, observations with a file trigger become filed issues instead.
