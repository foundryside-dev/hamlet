# T16 scheduler observer prerequisite repair r1

Disposition: **FIXTURE PREREQUISITE, not meaningful causal RED**. Root's R0 collection selected12 cases and passed in4.07 wall seconds; Black/Ruff passed. Its two actual narrow executions failed in31.8634 harness wall seconds (pytest27.21s) while serializing the runner checkpoint, before the intended post-run ownership/eager-policy assertions. Those root-owned results are retained; this repair makes no replacement runtime/PASS claim.

Read the actual failure trace and verified its log SHA256: `/workspace/bac-review-2026-11-01/qualification/wave10-r0-narrow/narrow.log`, `9aecdf91fb0896e85404eeeab660640b7ea51d478b55e4c1ccdc5314e8b93109`. Both nodes show the same sequence: actual periodic RR950 save → RR311 torch.save → PicklingError naming `LRScheduler.step`; then the unchanged final RR974 save repeats the failure. The original test's `_run` consequently cannot return to either intended assertion. Root reports160 source paths/three process identities/14 worktrees custody PASS and unchanged production.

## Root cause and minimal repair

The test installed its local `observe_scheduler` callable directly on **the scheduler instance**. `functools.wraps(original_scheduler)` gave that local callable the original LRScheduler.step metadata, but it remained a distinct object. POP1451 saves `self.scheduler.state_dict()` inside its real population checkpoint, and RR saves that payload unchanged. Root's verified scheduler-state behavior includes the new instance `step` attribute, so checkpoint pickle receives this local, falsely qualified function and refuses it as different from the module's actual LRScheduler.step. This is an observer-induced serialization fault, not a runner/PER/StepLR production defect or evidence of the intended missing policy.

Changed only the scheduler interception in the owned test:

- Capture `scheduler_class = type(population.scheduler)` and its original unbound `step` method.
- Install the pass-through observer on that **class**, calling the original unbound method with the actual scheduler instance exactly once.
- Append the tick only when `scheduler is population.scheduler`; other instances retain their original behavior without contaminating this audit's clock counts.

The observer no longer writes a callable into the owned scheduler's instance state. Genuine StepLR calls and the original production state_dict/checkpoint path remain intact. The optimizer, target, sampler, learner and environment observers are unchanged. No checkpoint save is disabled, payload field removed/patched, learning replaced, assertion relaxed or runtime budget changed. All99 assertions/five test functions/12 expected parameterizations remain unchanged.

The owned diff against root's staged R0 test is exactly **7 additions/5 deletions**,524→526 lines. No new helper or source is introduced. The existing tests now remain the direct root-owned re-execution check for both successful checkpoint publication and the intended later causal boundaries; no extra runtime probe was created.

## Bounded source custody

Same five complete sources, now **5 files/4403 physical lines**. Effective ceilings remain RR1200/POP2200/BC600/OF200/test700 = **5/4900**. Production source hashes remain unchanged:

| Source | Lines | SHA256 |
|---|---:|---|
| `src/townlet/demo/runner.py` |1001|`94842641bdce645fdd90d188d5bbdf6e09e7f4c071d15756202e173acd47c15d`|
| `src/townlet/population/vectorized.py` |2146|`9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a`|
| `src/townlet/config/brain_config.py` |568|`6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079`|
| `src/townlet/agent/optimizer_factory.py` |162|`56af1a9c8edb70a25b43a6e10aa3080d9a7b8becff112924e21a9429d994717d`|
| `tests/test_townlet/regressions/bac/test_runner_readiness.py` |526|`4b9fdcc73192b91db199111b4c2a07186e50fa1afc5bd6a77aa1e2909660939a`|

The systematic-debugging skill was read before investigation/change. No Torch/library implementation or sixth helper/source was opened; root's explicit scheduler-state diagnosis and actual trace were consumed as evidence alongside the already counted POP/RR serialization sites. No project import/runtime, pytest, collection, compiler, linter or additional probe was executed. Standard-library AST parsing succeeds, with99 assertions and maximum physical line length133. This proves syntax/structure only, not pickle/runtime remediation or causal RED.

Only the owned test and this ignored receipt were written. No production/source-copy/branch/worktree/checkout/deletion, index/commit/push/tracker action or subdelegation occurred. Existing14 checkouts remain preserved. Root owns rechecking the same two exact nodes and their actual reached failure boundaries, including fixture/serialization checks, before any production clearance. Return stationary.
