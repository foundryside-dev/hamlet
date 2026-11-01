# T09 wave02 independent review refresh

**SPEC + QUALITY: PASS within the unchanged T09 source boundary.** The existing independent probe now passes all five cases on the actual wave02 dependency tree. No T09 blocker remains from this review; joint release still requires coordinator full-suite/static/integration gates.

## Candidate identity

- Snapshot: `/tmp/bac-verify-wave02-3d1d21cff5`.
- Base HEAD: `050a1a70e979aa03724219b81e848093820f044f`.
- Actual staged tree: `3d1d21cff5abdf60b630f97da0cdb09bf8ccd036`.
- Before and after execution, both `git diff --cached 3d1d21cff5abdf60b630f97da0cdb09bf8ccd036 --exit-code --quiet` and `git diff --exit-code --quiet` passed. HEAD alone was not treated as the candidate.
- Before and after execution, the four source SHA256 values matched the new manifest and prior review exactly:

| Approved source | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/environment/vectorized_env.py` | 1714 | `849cacc1b94e13109d3ba5391b1d30668a89db308a3e228f3476a0f5457b595d` |
| `src/townlet/environment/action_mask_builder.py` | 206 | `5d02f08f94c68bbd63b4491a5ed00a432a3fbadbec6b9a02572d544bfbcb7174` |
| `src/townlet/training/replay_contract.py` | 222 | `3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c` |
| `tests/test_townlet/regressions/bac/test_successor_producer.py` | 212 | `c88043817f6996f02a1a7cb732e96b1afdc1a70c548b7b956c7da125eb605670` |

Source boundary remains four approved files / 2354 candidate lines plus the existing 148-line own probe. The same approved ENV base revision is executed for the retained differential control (1702 additional version lines; conservative total 4204). No sixth implementation/helper/test source, action-executor repair source, or unused replay helper was read. No source/index/git mutation or delegation occurred.

## Current executable evidence

Ran from the wave02 snapshot with `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=/tmp/bac-verify-wave02-3d1d21cff5/src` and `/workspace/hamlet/.venv/bin/python`. Asserted `townlet.__file__` resolves to wave02 before and after execution; Torch threads 1. Also asserted the candidate ENV step code filename resolves to wave02.

Executed the existing `task-T09-review-probe.py` through `pytest.main`, arguments `--no-cov -p no:cacheprovider <absolute-probe-path> -q`. A collection hook rebound only its snapshot constant and the approved producer fixture's `__file__` to wave02 so authored YAML comes from the current snapshot. The producer helper itself is byte-identical between snapshots. No probe assertions or files were changed.

**Result: 5 collected, 5 passed in 4.76s.** This includes real opening/closing-hour successor masks, four-world divergent pickups and asynchronous completion/retirement, live-only empty-row diagnosis, and both candidate/base-ENV inactive-DROP controls.

## Causal interpretation and limits

The earlier receipt `task-T09-review.md` and its candidate/base failures remain valid historical evidence: wave01 allowed DROP_SLOT_0 to alter an already-terminal world's inventory. Both controls now pass because both use wave02's shared dependency implementation, including the coordinator-reported action-executor repair. The base-ENV control does **not** revert that dependency. Consequently this verifies the old witness against the repaired common dependency; it does not claim the original full base tree passes, refute the old red receipt, or attribute a change to unchanged T09 source.

The prior source assessment of cloned bool `[N,A]` masks after committed observation/status/hour remains applicable to identical T09 bytes, supplemented by this current execution. Action-executor repair internals were independently reviewed elsewhere per coordinator attribution and were not source-reviewed here. No full repository suite, new owner-suite run, or standing static guard was run in this refresh. The earlier 85-test result remains wave01 evidence, not a newly claimed wave02 run. No whole-BAC or joint-release green claim.
