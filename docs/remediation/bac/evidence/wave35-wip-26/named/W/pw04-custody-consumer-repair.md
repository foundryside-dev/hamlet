# Current runtime/BANK consumer custody repair

2026-11-14. Integration owner executes all tests. This handoff claims no runtime result, historical baseline reproduction, package closure, or production-source change.

The R156 owner run retained 20 failures in `test_bound_component_reward_service_retry`, all at the core's unrelated same-thread reentry refusal. The test's original `bound(runtime, controller)` retains and binds runtime/BANK but opens a real controller RNG invocation without retaining or binding ENV. Source inspection of ENV `EnvCustody.call` confirms that an ENV method with no retained same-thread scope requests admission with `lineage=None`. Thus its attempted `env.step` cannot enter under that already-active unrelated invocation. A's new pure prepared-world seal is not called by this path. This establishes the current causal fixture defect, not a replayed pre-A baseline or a claim about when it was introduced.

The test now uses `bound_world`: retain ENV first and runtime second while idle; open the genuine registered controller invocation; bind both retained scopes to that exact operation; execute the original assertions; verify the invocation's own completion succeeded. The generic runtime/BANK-only `bound` helper and other tests are unchanged. Every original reward, service retry, eligibility, finite reward, epsilon, legal selection, retired-world and service-clock assertion remains.

POP owner `pw04_runner_runtime` source-qualified the direct claim preconditions against POP SHA256 `7f02f08359fa15aaa713e8e7221142d130f560cd96cea13334c64c54b088ee8a`: actual `claim_vector_step` accepts its genuine issued prepared record without requiring `_step_active` or POP's own ambient operation. It rechecks actual accepted/reset/sealed reading and exact caller geometry/activity, then marks the record executing. After a direct component ENV step, POP remains executing until its actual return path; this test does not certify continued POP learning or a healthy completed boundary. No POP implementation body was opened by this repair owner.

## Bounded inventory

Five bodies, initially 3,680 lines; after the 10-line helper addition, 3,690 lines:

- test_runtime_bank_parent_custody.py: 1,348 → 1,358; original SHA256 `7102dd35e36481713b24fc2ec37e242e8d00d2ee9bc958db018ba89dd5638872`; submitted `4ed90d6826341f5fd963eecaf488ad353b34cf545537e13cdc59ad211ac2ade6`.
- environment/parent_custody.py: 418; `fe0490b6a998fc73787bef36ef39230265bc1203079b2690c205200a597c927a`.
- exploration/parent_custody.py: 239; `1b911c653ed1b1738c4de19b646bd1965cc0825b6f85e814e5ba25a43e02944f`.
- test_parent_intrinsic_handoff.py: 900; `bbfdc1e8d60a609de6dacf7b68c0d6cb7e014df308dddddde5698ad2bf7fd673`.
- test_initial_participation_population.py: 775; `0db498e53d21f62f98ea53d6cf801476a1cac73b29a4710760a68d269dc78566`.

No extra implementation/test bodies, runtime imports, tests, formatters, Git operations, branches, worktrees, execution copies, deletion or subagents. Root may format and run the exact 20 cases, followed by the affected owner selection. Final formatted identity and actual result belong to that root execution record.
