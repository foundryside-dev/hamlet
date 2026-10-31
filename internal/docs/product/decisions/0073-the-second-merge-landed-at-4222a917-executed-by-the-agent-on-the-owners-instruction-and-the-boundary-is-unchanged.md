# PDR-0073 — The second merge landed at `4222a917` (PR #35), executed by the agent on the owner's explicit instruction; the `PDR-0046` boundary is unchanged

Date: 2026-08-17   Status: **accepted** (the *decision* to merge was the owner's — *"yes, please do
the merge now"* — the agent performed the mechanics; this PDR records that the reversibility
boundary was crossed by the owner's hand, not moved)
Author: Claude (standing product owner)
Owner sign-off: **yes** (explicit, in-session, after the checkpoint brief asked for it)

Related: `PDR-0046` (the merge is the reversibility boundary and the owner's), `PDR-0039` /
`PDR-0072` (both gates stood at the tip), `PDR-0058` (the merge is publication inside the bet;
the workspace must observe it rather than assume it), `PDR-0043` (trigger 2 — the nightly)
Tracker: none closed by the merge itself

## What happened

- Both gates were re-read at the tip before anything was created: `f023b9e7` Tests **success**
  (run `31968235680`: 3239 passed, 24 skipped, nothing deselected) alongside Lint and Config
  Validation; `905acd96` likewise. Gate 2 executed at `905acd96` (`PDR-0072`); the only commit
  after it was the `docs/product/` checkpoint, so the sweep was not re-owed.
- PR #35 created (`project-recovery-2` → `main`, 29 commits). A direct merge was refused: `main`
  is governed by **repository ruleset 9453164** — pull-request required, `non_fast_forward` and
  deletion blocked, and required status checks `lint` and `unit` on the PR's own
  `pull_request`-triggered runs (strict). That is why every merge to `main` in this project has
  been a PR merge commit and never a fast-forward (the README's corrected wording in `PDR-0072`
  is the ruleset showing through). Auto-merge is not enabled on the repository.
- The PR's own `lint` (1m3s), `unit` (26m55s) and `validate-config-packs` (1m18s) passed;
  `mergeStateStatus` read `CLEAN`; merged with `gh pr merge --merge`.
- **`main` = `4222a917`**, parents `07b26ed5` + `f023b9e7`. Verified after the fetch: branch 0
  ahead / 0 behind; `main`'s `README.md` byte-identical to the branch's; `main`'s
  `pyproject.toml` no longer carries `-m "not slow"`.

## The call

Nothing about the grant changes. `PDR-0046` still reads: the agent may push the branch; the merge
to `main` is the owner's. The owner exercised that ownership by instructing the agent to perform
it, having read the checkpoint brief that named it as the one thing awaiting sign-off. A future
session must **not** read this PDR as standing permission to merge — each merge is asked for and
answered, as this one was.

## What the merge does to the readings

- **Exit condition 3 (`Gates green` on a suite that hides nothing)** is now met on `main` as
  well as the branch — the branch *is* `main`. The row's scope caveat (*"`main` still carries all
  33 behind the marker"*) is discharged at `4222a917`; `metrics.md` states it and points at the
  reading that confirms it: the first post-merge scheduled nightly (`Full Test Suite`, 06:00
  UTC), which runs the same bare `uv run pytest` as the per-push gate.
- **`PDR-0043` trigger 2** stays discharged: the nightly is `active` and reads the merged file.
- **`PDR-0072` trigger 2** is now live: if that nightly is still red on the three named files,
  the README's account of the 31 is wrong and this PDR's "exit condition 3 met on `main`" reverts.

## Reversal trigger

- The first post-merge nightly reports failures in `test_temporal_mechanics.py`,
  `test_training_loop.py` or `test_recurrent_networks.py` → `PDR-0072` trigger 2 fires; reopen
  the "29 repaired, 2 deleted" reading and the exit-condition-3-on-`main` claim.
- Any future session that merges without an in-session owner instruction, citing this PDR → that
  is a grant breach, not a precedent; escalate and record.
