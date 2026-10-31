# PDR-0102 — `PDR-0039` gate 2 executed for the third merge: eighteen stale claims and four omissions in 43 commits, and the adversarial pass found ten defects in the sweep's own corrections

Date: 2026-08-20   Status: **accepted** (gate execution within the grant, per `PDR-0101`)
Author: Claude (standing product owner)

Related: `PDR-0039` (the gate and its method), `PDR-0048`, `PDR-0072` (the two prior executions),
`PDR-0101` (which made this a gate the agent executes rather than waits on)
Artifacts: `README.md` stamped at `da7d3f7e`; sweep findings and adversarial findings retained in
the session scratchpad; `docs/product/prds/0001-trial-protocol.md` **B.7**

## Context

`PDR-0101` made merging autonomous and converted gate 2 from an escalation into a quality gate the
agent executes. This is its first execution under that reading, and the third overall. 43 commits
had landed since the last stamp (`54132aaf`).

The method is fixed by `PDR-0039` and is **not** a re-read: ground-truth sweep → draft from
verified facts only → adversarial pass. It was run as three separate agents so the drafter could
not mark its own work.

## What it found

**A blocker the agent had introduced and not noticed.** `ruff check .` exited 1 on a 142-character
line in `configs/trial_o_bidding_blind/probe_trial_o.py`, landed with the blind-re-run pack at
`80eed80b`. **Branch Lint had been red for seven consecutive pushes**, and the standing agent had
twice reported CI as green in that window, having read it before the offending commit and never
after. Fixed by wrapping, with the probe re-run to confirm the trial record's pasted evidence is
byte-identical — a lint fix that silently altered recorded evidence would have been far worse than
the red. Protocol **B.7** closes the omission that allowed it: §10 required `validate` plus the
full suite before a trial commit but never `ruff`, and this was the **third** probe-`E501` red in
five sessions.

**Eighteen stale or misleading claims, and four material omissions**, including: the repo has two
tags, not "only one"; `configs/` holds 33 packs carrying an `experiment.yaml`, not 25; the nightly
on `main` is green four times over, not "red twice"; "the full matrix" described a workflow with no
matrix; `configs/aspatial_test` is excluded from the CI validation gate by a list whose other two
names do not exist; and three declared VFS scopes compile then crash at env construction.

**A forward promise that would have gone false on landing** — *"the merge that carries this file
closes that gap"* — the exact merge-flip trap `PDR-0072` recorded. Rewritten so `main` trailing the
branch is stated as standing design rather than as a gap about to close.

## The result that justifies the method

**The adversarial pass found ten factual defects in the sweep's own drafted corrections, before
any were applied.** Two mattered:

- The sweep proposed telling readers the suite is green over the three crashing VFS scopes because
  *"no test instantiates them"*. Four test sites instantiate them directly and pin both the working
  path and the raise. The true claim is narrower — nothing reaches them through
  `VectorizedHamletEnv`, the only real construction site — and that is what shipped.
- The sweep declared the cache-serialization defect's discriminator *"not established"*. It is: a
  **non-empty `agent_profile.variables`**, proven sufficient by controlled experiment and
  consistent across all 33 packs. Root cause is `universe/compiled.py:123`
  (`agent_profile: Any | None = None  # TODO: Add CompiledAgentProfile type`) — the untyped field
  holds a `CompiledGlobalProfile`, which is why the error names the wrong half of the config and
  why two prior filings got the trigger wrong. `hamlet-a141ab5db3` retitled accordingly.

A sweep alone would have shipped both. That is the argument for the three-step method over a
re-read, and it is why `PDR-0101`'s first reversal trigger reads *a gate-2 run that finds nothing
is a signal to distrust the gate*.

**The applier also erred, in the same class.** The standing agent wrote "eight consecutive Lint
reds" into both the README and a commit message; it is seven — `80eed80b` never got a run, having
been pushed together with `7fa6cf10`. Caught on self-check before the stamp, and recorded here
rather than quietly fixed, because the gate's credibility rests on its errors being visible.

## Call

Gate 2 is **discharged** for this merge. `README.md` is stamped at `da7d3f7e`, the last commit
with all three per-push gates green (Lint, Config Validation, Tests — verified, not assumed). The
merge proceeds.

## Reversal trigger

- If the first nightly on `main` after this merge is red, the stamp's central claim was wrong and
  gate 2's CI reading must be re-derived at merge commits rather than at branch tips.
- If the next gate-2 execution finds fewer than five stale claims across a comparable range, treat
  the method as having degenerated into a re-read and re-run it with fresh agents before merging.
- `README.md` names `configs/aspatial_test` as CI-unvalidated. If that is fixed, this claim decays;
  it is the kind of sentence the next sweep should target first.
