# POP failed-diagnostic caller repair plan v1

2026-11-14. PREPARE ONLY, by `bac_pop_standalone_step_prepare`. Root has not released the APP/test baton while the current R127 independent probe/P3 lease runs. No source edits, application imports/runtime/tests, Git operations or new source bodies. This prose is the sole write.

## Exact starting boundary

| Already-owned body | Lines | SHA256 |
| --- | ---: | --- |
| POP `src/townlet/population/vectorized.py` | 3163 | `ea05fddb584cc7836e663e2aa2cada3c4dca1fcbc08584e030efa1816ac4bf38` |
| Existing `test_parent_intrinsic_handoff.py` | 791 | `2621285b5d259be7f4bf8eb5e7b2ae1d2eb29c867923a7e2aa043c9e6246f7ef` |
| Existing focused cleanup test | 102 | `d59505029082a518f888bdc5937a6e23fbb56aac1681d2ce901e504ed6b37509` |
| Existing initial-participation test | 775 | `0db498e53d21f62f98ea53d6cf801476a1cac73b29a4710760a68d269dc78566` |

Current cumulative whole-body budget4831/four. Only POP and existing parent-handoff will change. Proposed aggregate growth at most50 lines gives4881/four; adding the reviewer's attributed prior115 yields4996. Recount exact post-format bytes before handoff; stop/reslice rather than exceed this ceiling. No fifth helper/test/producer body may be opened. The other two test files stay unchanged.

Opaque producer basis: `T18e-R0-PARENT-C1-FAILED-DIAGNOSTIC-IMPLEMENTATION-PLAN-v1.md`, SHA256 `3137a53537a0561665dafccef940c9fe4ada035e1c0eaf2c9e351309a18bbf1a`; `../evidence-management/parent-c1/failed-diagnostic-implementation-v1/handoff.json`, SHA256 `a9993a98f523664765235eec9498f3b42aca67802bc864b62678b26325e90452`. Root reports30 focused passes and one fresh own-completion pass plus source review with zero P1/P2; the independent thread/fork probe remains root-owned pending work. This caller packet does not requalify producer implementation from those reports.

## Minimal production intent, approximately eight added lines

Retain `get_checkpoint_state()` and its twelve outer fields. At the existing actual-failure proof guard, bind a local boolean from `_failed_step and _has_failed_step_diagnostic()`; the existing failed-but-unproven refusal tests that boolean. Keep all outstanding-reset, busy, pending batch and vector-work guards intact.

Replace only the existing `exploration_state` dictionary value with a small private helper call taking that required explicit boolean. Its ordinary `if` returns `self.exploration.failure_diagnostic_state()` for the proven failed route and `self.exploration.checkpoint_state()` for the healthy route. No default, conditional-expression addition, exception-catching, cache or fallback. The helper executes exactly at the original dictionary value position, after Q/optimizer/scheduler/total_steps capture and before universe metadata/target/training counter/replay capture. It does not hoist the producer call above the outer field evaluation sequence.

The public get_checkpoint DTO remains unchanged. Failed reset/unclassified work cannot select diagnostic export. The actual failed-proof function and retained issued vector registry remain the authority; no caller flag/payload, all-zero-counter inference or synthetic accepted token is admitted. A diagnostic capture error propagates as a failure, never substitutes healthy state or a partial dictionary.

The runtime diagnostic is the full current runtime transport with `schema=exploration-runtime-failure-diagnostic-v1` and `failure_reason=runtime_failure`; its bank is the full current BANK transport with `schema=curiosity-bank-failure-diagnostic-v1` and the same reason. Native local-private `healthy=False`, shared-native refusal, common-domain safety and producer completion uncertainty remain producer-owned contracts. POP neither transforms nor downgrades that payload.

## Existing pace-case assertions, remaining at-most42 added lines

Extend only the existing pace branch in `test_partial_failure_records_reached_cut_and_refuses_reexecution`; preserve every original assertion, real failure injection, failed progress and no-second-physics check.

1. Install a transparent observer of the real `runtime.failure_diagnostic_state`, retaining an owned copy of its actual result and forwarding it unchanged. Existing `copy.deepcopy(pop.get_checkpoint_state())` must invoke it once. Compare the complete outer exploration payload with that result; assert both diagnostic schema literals and reasons. This catches omitted fields, stale/healthy substitution and bypassed producer capture without reading a producer implementation.
2. Assert the exact twelve literal outer field names and version7. Compare current Q/target/optimizer/replay payloads with their real owners, current full seven-unit ledger and counters with POP, and the fixture's supported absent scheduler with None. The real pace failure must show vector tick1 and optimizer update0. Compare universe metadata with the genuinely fresh compatible receiver's healthy snapshot, not a fabricated dictionary.
3. Preserve the existing exact failed-progress comparison and `ValueError("Failed or in-progress...")` through the fresh receiver's public `prepare_checkpoint_state(...mode="completed_boundary", parent_restore=None, validate_parent_restore=None, initialization=None)`. That proves the parser's actual failed-progress rejection; no bound-receiver/missing-proof substitute is allowed.
4. After successful diagnostic capture and original receiver refusal, replace only the diagnostic capture seam with an injected retained exception. A second public POP export must raise that same object. This is an error-propagation control, not a fake successful diagnostic. Do not catch it into a healthy checkpoint or cache/subset result.

Use the existing `equal`, constants and real fixture only. No new test body/file or weakened producer-health assertion. Keep formatting compact and readable to honor the aggregate50-line delta ceiling; remeasure actual bytes before review.

## Root execution and remaining gates

After explicit baton and source freeze, root first executes the unchanged named pace case on the caller repair, checking full payload and exact receiver refusal, then reruns the original full23 selection at one sealed candidate. No local APP runtime is authorized by this preparation. Scoped Ruff/Black/defaults/static checks follow root's actual grant; retain failed earlier R124 evidence and remaining mypy failures instead of relabeling them. Fresh review must cover the bounded caller delta against the opaque sealed producer contract.

Standalone restore/candidate ownership, full C1 owner acceptance, active-parent/C2/P1 integration, constructor/rebound paths and broader hardware/program gates retain their existing required status. This repair preserves truthful diagnostics; it does not enable resume from them.
