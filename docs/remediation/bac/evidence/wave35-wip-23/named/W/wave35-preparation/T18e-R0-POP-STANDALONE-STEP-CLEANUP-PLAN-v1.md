# POP standalone step and cleanup prerequisite plan v1

2026-11-14. Implementation-ready preparation by `bac_pop_standalone_step_prepare`; root owns the subsequent APP/test baton after R122 component verification and durable checkpoint. Root authorized this prose artifact only. No application edits/imports/tests, Git operations, branches, worktrees, source copies or deletion. Repository AGENTS.md was read. Systematic-debugging skill used to trace the two demonstrated causes before proposing edits.

## Authority, bounds and source custody

Root adopted the finite ordering in `R121-OWNER-RECONCILIATION-v1.md`, SHA256 `91bda13dd0760a64c13322c4f3f5a5fdb47edd3baf3523f7e4463988b597284e`: this standalone prerequisite precedes full C1 acceptance. R121 remains failed; active-parent/C2/P1 integration and standalone restore remain required separate work.

| Owned implementation/test body | Current lines | SHA256 | Maximum after edits |
| --- | ---: | --- | ---: |
| `src/townlet/population/vectorized.py` | 3163 | `6c4f7ca085f0a7db34f42bebe22f0240ed12825627c13bcffb3c0d3be3f99022` | 3500 |
| `tests/test_townlet/regressions/bac/test_parent_intrinsic_handoff.py` | 791 | `6cea1235f8dc149aceb5ca7352b855ac001a8bfb1e758a9c3b116f3654f2acb0` | 850 |
| Proposed `tests/test_townlet/regressions/bac/test_population_standalone_step_cleanup.py` | absent | new focused body | 600 |

Current charged whole-file budget is 3954/two; writer and fresh reviewer ceiling is 4950/three, including any read-only helper body. Recount before mutation/review and stop/reslice on growth. Imported fixture APIs do not authorize opening their implementation bodies. The 773-line initial-participation suite remains unopened; root executes its supplied exact representative without adding that body to this packet.

Producer contracts remain opaque and attributed:

- Current replay supplier `T18e-R0-PARENT-REPLAY-CURRENT-SUPPLIER.md`, SHA256 `f6c48b621acbc26f9198a8e25f71a6f25b29fc4697d8f3e7d0bf77a0154b7b37`, supplies explicit standalone None, mandatory admitted sample lineage, and lineage-free local readiness/push/pacing/priority operations. It binds current shared881/core1195; no historical shared/core seal is substituted.
- `T18e-R0-REPLAY-FIX-B-CURRENT-API.md` supplies recurrent mandatory lineage and owner-local semantics. Root and this writer independently rehashed current sequential1930 as `e261a0caca68c74cc36bdb9469b126aa0bdae38eeababf358a20bf96f8373317`, exactly matching its source. No sequential body was opened and no new recurrent runtime qualification follows.
- Current C1 reviewer supplied exact runtime/BANK quarantine facts, now durable in `../evidence-management/parent-c1/doc-draft/CURRENT-PARENT-CUSTODY-COMPONENT-CONTRACT.md`, SHA256 `b9debb77ad27bb918f3bcc4a3923c015a68a74b3fafb0971105d4f5140b537eb`, lines78–90. This writer independently matched runtime SHA256 `50a738825ae151cbf7a2907660e4cd06df7e42ae78128135eda891b3c6c885f9` and BANK `55e0ac73ed65932aaf19c0622c8f11c5bb3801fda8957492ccf513d270a104b4`, without opening those bodies. This is supplier evidence, not an independent producer implementation review.
- ENV/runtime older supplier SHA256 `02ac16732bb18dd6613c09cf90f2b20850da402c355cd11604f000f3f91b5b33` supplies ENV `abandon_episode` runtime_failure semantics; its pre-C1 runtime facts are superseded by the current C1 addendum.
- `T18e-R0-PARENT-C1-FIRST-A-ONLY-STEP-FACTS.md`, SHA256 `9ab8e1b919f31aa14f08c6f804ba9d42ac9dc25d1016206436066238e759604c`, supplies the actual A-only first/second-step readiness distinction.

## Causal cut and exact patch intent

Normal fresh `for_training` setup binds the actual replay at POP545; `_bind_training`674–675 returns for that same owner. The normal step then performs actual ENV physics/reward, replay push2336, runtime service2348, vector advancement2359 and local pacing2361. `_learn` checks actual readiness792 and samples800. The sample currently omits mandatory lineage. A first all-active step reaches learning; an A-only first step retains one row and its second step reaches batch2. Changing readiness, participation or step count would conceal the failure.

The finite source edits are:

1. POP800: call `sample_batch(request, lineage=None)` for the current standalone operation. No optional lineage default, ambient lookup, synthetic participant, parent scope or adapter.
2. POP2115: pass `reason="runtime_failure"` to the real exploration quarantine operation. ENV already receives that reason2116. Preserve the ordered independent cleanup attempts, original bare re-raise, exception notes and failed progress/nonreexecution.
3. Existing parent-handoff444: pass explicit `lineage=None` in its standalone replay sample witness, preserving every behavioral assertion.

Current C1 runtime1009–1011 forwards the reason unchanged. BANK930–939 authenticates accepted first, permits only exact str `empty_participation` or `runtime_failure`, and records `_quarantine`, `_failed=True`, and revision advancement. An identical quarantine retry is admitted only for the same accepted/reason. Public healthy checkpoint/snapshot operations refuse failed BANK state. Unsupported `population step failure` currently refuses before those quarantine assignments but after accepted callback and within the actual BANK invocation. This cleanup is not a callback-free response to parent completion uncertainty or a common-poison bypass.

Other normal-step call seams are local readiness792, flat/PER push2336, pacing724/726, priorities849/852, and recurrent captured-store1780 during finalization; they do not acquire an invented lineage parameter. `_learn`800 is the shared sample call for flat/PER/recurrent. No broader recurrent execution claim follows from flat fixture coverage.

The constructor/rebound `_bind_training` adaptation path698–702 also contains obsolete prepare/load calls and historical format handling. It is outside this fresh-owned standalone sample prerequisite and remains explicitly unresolved for a separate constructor/replay lifecycle packet. Do not silently claim all POP entrypoints coherent. Checkpoint materialization3067, copied candidate authority, destination install3070 and restore publication remain the separately ordered restore prerequisite; no edit here touches them.

## Finite RED and GREEN evidence

After the root test baton, first execute original `test_parent_intrinsic_handoff.py::test_actual_parent_handoff_single_reward_service_and_replay[shared-none]` unchanged to retain the primary missing-lineage RED. Also execute existing `test_partial_failure_records_reached_cut_and_refuses_reexecution[env-executing-0]`; its current assertions alone do not prove cleanup reason correctness.

Add focused tests using the already-owned genuine ParentFixture API and real reset/activation/step flow:

- Observe the real sample call with required keyword lineage and assert it is explicitly None. After successful real sample, raise a retained sentinel exception before optimizer mutation. Observe and delegate the real runtime quarantine and ENV abandon calls, preserving exact accepted identity and reason. Assert the same exception object escapes; healthy cleanup adds no spurious failure note; progress is failed/advanced at tick1, physical tick1 and actual replay rows are retained, optimizer update count remains zero, ENV is quarantined, public runtime checkpoint refuses, and another POP step refuses before second physics.
- Parameterize a cleanup-failure variant whose wrapper first completes genuine runtime/BANK quarantine and then raises a second retained exception. Assert the original sample sentinel still escapes with the secondary cleanup note, ENV abandonment is still attempted, and the same failed/nonreexecution invariants hold. This exercises preservation without substituting a fake successful cleanup implementation.
- Use genuine shared and per_world rigs for both variants, keeping the new file comfortably below600 lines. Test wrappers must call real producers; no private authority writes, fake handles, forced dones or disabled assertions.

After the minimal APP edits, root executes the exact original shared-none representative first, then all ten family/scope original handoff cases, the sourced `test_initial_participation_population.py::test_actual_a_learning_replay_private_b_and_next_cycle`, all four existing partial-failure stage cases, and the focused cleanup cases. Require each intended assertion to be reached. Preserve original assertions concerning exactly-once reward/service/replay, learning, full ledger, A-only/B-inactive isolation and nonreexecution. Run source-appropriate lint/static checks under the root custody procedure; no broad gate repetition until prerequisite causal checks pass.

Fresh independent review covers the same at-most4950-line packet and the sealed opaque supplier interfaces. Root owns immutable candidate/source/process evidence and the eventual unchanged owners-gate rerun. This plan grants no active-parent claim, restore acceptance, CUDA/recurrent/runner qualification, C1 full acceptance or R121 waiver.
