# T09 independent SPEC + QUALITY review

Verdict: **PASS for the T09 successor-mask change; no introduced P1/P2 blocker found.** A separately reproduced **pre-existing P2 frozen-world defect** remains below. This is scoped technical review, not approval of every current lifecycle behavior or the joint release. Coordinator must disposition that current-state issue and complete the joint gates.

Reviewer: fresh other-model review of Sol-implemented T09, performed independently on the supplied fixed snapshot. User preservation/additive requirements override AGENTS blanket removal guidance. No production/index/git mutation or subagent dispatch was performed.

## Identity and read boundary

- Snapshot: `/tmp/bac-verify-wave01-6881a7488a`.
- Base HEAD: `050a1a70e979aa03724219b81e848093820f044f`.
- Actual candidate staged tree: `6881a7488a110adbd94c689b67b5241fb094d10e`. `git diff --cached 6881a7488a110adbd94c689b67b5241fb094d10e --exit-code --quiet` and unstaged `git diff --exit-code --quiet` passed, including after execution. HEAD alone was not used as candidate identity.
- Four SHA256 checks before and after execution matched the task manifest:
  - ENV: `849cacc1b94e13109d3ba5391b1d30668a89db308a3e228f3476a0f5457b595d`
  - action mask builder: `5d02f08f94c68bbd63b4491a5ed00a432a3fbadbec6b9a02572d544bfbcb7174`
  - replay contract: `3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c`
  - authored producer test: `c88043817f6996f02a1a7cb732e96b1afdc1a70c548b7b956c7da125eb605670`
- Before and after execution, asserted `townlet.__file__` resolves to `/tmp/bac-verify-wave01-6881a7488a/src/townlet/__init__.py`; Torch threads explicitly 1, OMP/MKL threads 1.
- Source inventory: exactly the four approved logical source files, 2354 candidate lines, plus one own probe `task-T09-review-probe.py`, 148 lines. Same approved ENV logical source's 1702-line base revision was additionally loaded for causal comparison. Conservatively charging both ENV versions: **4204 lines, five logical files**. No sixth implementation/test/helper source inspected. Existing B11 tests executed without opening their source. YAML, task brief, reports, candidate metadata/patch and AGENTS are reference material.

## Contract assessment

At `src/townlet/environment/vectorized_env.py:1190`, the next-action hour commits before observations and masks. At line 1195 the existing canonical builder is called and its result cloned. At lines 1196–1201 only nonterminal empty rows diagnose, with pack/level/tick/row location; terminal empty masks remain allowed. No environment semantics or working action modes are removed by this addition.

Evidence supports bool `[N,A]` shape, actual GET legality changes after pickup/drop, disabled-action zero control, historical mask independence from caller mutation/next tick/reset, entry-active terminal admission and once-only retirement. The authored cap test establishes that voluntarily stopping collection does not mark an otherwise-live successor done; it is not a full runner budget integration witness.

Independent authored probes add:

1. Real temporal support with Bed opening at hour 1 and closing at hour 2: the first successor enables INTERACT; the second disables it. Both match the canonical builder and returned observation at their committed hour; prior masks survive later step/caller mutation/reset.
2. Four independent worlds with different GET/WAIT/DROP choices: per-world GET legality diverges correctly. World 0 terminates while siblings remain live; entry activity, frozen meters/inventory under WAIT, zero old-lane reward, masks, step counts and later sibling retirement are correct. All-complete extra step emits no repeated completion/retirement.
3. GET-only two-world pack with an authored terminal condition for world 0: pickup empties both action sets, but diagnostic names **only live world 1**, at tick 1. No runtime state or mask injection.

The diagnostic is deliberately post-commit and has no rollback promise. It uses the same current `dones` as returned status. Existing immutable replay transport validation was reviewed for alignment; storage/learner integration is outside this slice.

## Pre-existing P2: inactive item action can mutate a completed world

**Trigger:** In the existing authored item/terminal pack, both worlds GET, then WAIT. World 0 becomes terminal while world 1 remains live. On the next batch step send DROP_SLOT_0 for completed world 0 and WAIT for live world 1. World 0's inventory changes from `[0]` to `[-1]`, despite its entry activity being false. No meters/dones/inventory/masks were injected. Candidate and base ENV reproduce the identical failure.

**Contract/impact:** Violates the frozen completed-world state requirement adjacent to BAC-C06. An inactive row has no legal actions, but a batched API still receives an action slot for it; that slot can currently change item state. This does not show a selectable live illegal action, a corruption of the published historical masks, or a new T09 regression. It requires that the caller supplies DROP_SLOT_0 to the inactive row; WAIT did not reproduce it. Actual population fallback behavior was not inspected and is not claimed.

**Source boundary:** ENV line 1090 computes entry activity; line 1096 forwards the full action vector to the action executor, before the newly-added capture at 1195. Later VTC phases explicitly receive activity at line 1100. These are bounded call-site evidence, not an assertion about unseen action-executor internals. Repair investigation would require a separately authorized source slice.

**Causality evidence:** `test_inactive_drop_does_not_mutate_world[candidate]` and `[base]` both fail at probe line 148 with the same `[0] -> [-1]` mutation. The base comparison executes exact base ENV source obtained with `git show 050a1a70e979aa03724219b81e848093820f044f:src/townlet/environment/vectorized_env.py`, using candidate dependency APIs; it is a controlled ENV-delta comparison, not a claim that the entire dependency tree was reverted. The T09 patch adds no writes before this trigger.

Disposition: report to coordinator as current-state P2; no removal or capability reduction proposed. It is not an introduced-diff blocker, but prevents an unqualified claim that all finished-world state is frozen.

## Executed checks

All commands ran with cwd fixed snapshot and prefix `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=/tmp/bac-verify-wave01-6881a7488a/src`, using `/workspace/hamlet/.venv/bin/python`.

```bash
python -m pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_successor_producer.py tests/test_townlet/regressions/test_episode_lane_environment.py tests/test_townlet/unit/environment/test_action_masking.py tests/test_townlet/unit/training/test_episode_accounting.py tests/test_townlet/integration/test_authored_episode_lanes.py -q
```

Result: **85 collected / 85 passed in 27.42s** (5 authored producer + 80 B11 owners).

```bash
python -m pytest --no-cov -p no:cacheprovider /workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/task-T09-review-probe.py -q
```

Final probe result: **3 passed, 2 failed in 6.40s**. Both failures are deliberately retained unmarked candidate/base instances of the pre-existing inactive-drop witness above; no xfail, skip or hidden failure. Initial exploratory run also assumed a ground item's `duration=1` implied expiration on the first WAIT; that assumption was unsupported by the inspected contracts, so that exploratory assertion was removed and is not reported as a defect or evidence. Initial four-world inactive-drop failure was narrowed into the explicit candidate/base witness; the four-world lifecycle control now uses WAIT on the completed lane and passes.

No broad full pytest or repository-wide static checks were run by this reviewer. Root owns same-tree full/integration gates and the six standing non-pytest guards. Off-scope AS/RND changes were not source-reviewed here. No whole-BAC, release, learner or GPU correctness claim.
