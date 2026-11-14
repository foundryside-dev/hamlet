# Peer-wait test-only repair: independent plan review

Date: 2026-11-14. Reviewer: delegated `/root/bac_astra_peer_wait_plan`, independent of the diagnosis producer and root's WIP20 publication work.

**SPEC: APPROVE the bounded test-only design below. QUALITY: APPROVE for implementation, subject to exact patch review and fresh qualified execution.** This is a plan verdict, not a repaired PASS or authorization to execute or change production. No runtime defect is established by the reported timeout. No compatibility restoration, invariant waiver, or scope reduction is approved.

## Immutable inputs and inspection boundary

Diagnosis: `wave35-preparation/T18e-R0-CUDA-B-PEER-WAIT-FAILURE-DIAGNOSIS.md`, SHA256 `05329b1ef7df41821cea034b367dd76240be7c3b01b8020c15087c6bd8b47b2b` (verified).

Accepted current documents under `docs/remediation/bac/` were read and hash-bound:

| Document | SHA256 |
| --- | --- |
| CURRENT-RNG-CUSTODY-CORE-CONTRACT.md | `8d2e1096bfdac94afc97691834e2418a4463de0d70c644ba14aa20ffa73fc99e` |
| CURRENT-REPLAY-CUSTODY-CONTRACT.md | `8cd7b369e2e1ac35273680ab16e346c8f540b664586904c8b4b9985f630c2137` |
| CURRENT-RECURRENT-REPLAY-CUSTODY-CONTRACT.md | `f6059c4a80e89767214a76fa794f9622d1aa680251afc8d2ec48db128e99306e` |

`AGENTS.md` and `docs/remediation/bac/EVIDENCE-PROCESS.md` were read. Implementation/test inspection was confined to these three admitted bodies (3174-line body budget); relevant control-flow sections were directly read. Some whole-file tool output was truncated, so this is not a claim that every unrelated line was reviewed.

| Path | Lines supplied | SHA256 verified |
| --- | ---: | --- |
| src/townlet/exploration/rng_custody.py |1195|`6cb01ca77b58db5f4c4784dc36da566c06cf68c2a7c2ce227bb780549f3344f8`|
| src/townlet/training/replay_contract.py |881|`8c0251c3c46e9c296e7b3bb5afcf2f6cdce8083fa22666c5a662be454a9a12f4`|
| tests/test_townlet/regressions/bac/test_replay_rng_custody.py |1098|`5870d5315dd6f975f6e9513a492ba08f84671576f18e70f62795b122e13eabd7`|

No other implementation/test snippets or imported bodies were inspected. Root supplied the dispatch metadata: flat sample386/decorator385 and PER sample651/decorator650 use `replay_device_sample`; sequential sample_sequences418/decorator417 and sample_batch1365/decorator1364 use `replay_sample`. Explicit lineage remains required everywhere. These are supplier facts, not independent producer-body inspection.

The R113 root record `wave35/r113-root-checks.json` and current contracts identify tree `b5298dec04379db31bf9107a26ead7764f53d73c`, manifest SHA256 `0f05c4f3faab3e6f5ea15b7ba8fc8c466f0e3dda9bbc87abbde47af7bd2f3daa`. Authoritative affected replay is **54 cases: 52 PASS / 2 FAIL**, including its isolated poison child. The diagnosis's healthy53 figure is **51 PASS / 2 FAIL** and excludes that child. Neither number supersedes the other scope. A later repair must not silently reduce affected54 to healthy53.

## Why the design is sound

The peer's genuine public operation holds the sole domain RLock through its private operation. Flat/PER `_device_operation` enters admission under that same lock before planning, owner exclusion or invocation issuance. After admission, it creates the original `device_invocation`, enters it through ExitStack, and yields the authentic operation while retaining owner and domain exclusion. Invocation entry directly calls private `_operation`; it does not dispatch through public `operation`. The old selected-worker public-operation observer therefore cannot signal reached on either migrated path. Recurrent still takes the public operation path.

Observing the original bound `_device_operation` immediately before entering its context supplies the missing attempted-entry witness. Observing after its yield supplies actual operation acquisition, not merely admission. Separately recording the actual original factory call preserves the participant/kind/lineage/device proof that would otherwise be lost. Both delegates can preserve original behavior without changing production or inventing authority.

The pre-entry event proves route entry, not an OS-level blocked-thread stack. Together with original source delegation, genuine held peer exclusion and the preserved bounded negative interval, it is adequate for this regression's existing causal purpose. It must not be advertised as exhaustive scheduler or concurrency proof.

## Implementation-ready boundary

Only `test_direct_ambient_sample_waits_for_registered_peer` in the admitted test body, its explanatory text, and strictly necessary test annotations/imports may change under the later test-only grant. Keep all three existing parameter cases and direct real samplers. Do not alter helpers, fixture semantics, production, registered entrypoints, CUDA policy, lock behavior or timeout constants to obtain a pass.

1. Capture the original bound helper and factory before monkeypatching. For migrated flat/PER, wrap the selected owner's `_device_operation`, selecting the exact worker Thread object. Forward kind, explicit lineage, route, args, kwargs and mutation unchanged. Set reached immediately before entering the original context; append its exact yielded `RNGOperation` and set acquired only after original entry succeeds. Yield that same object, and delegate full exit on success or failure. Do not construct a token, replace admission, wrap invocation entry/exit, or substitute a fake context.
2. Observe the selected worker's actual `domain.device_invocation` call. Delegate unchanged to the captured original and record its actual returned object, returning exactly that object. Record actual call arguments, not expected values reconstructed from the owner. Require exactly one selected issuance with participant **is** replay_participant, kind `sample`, lineage **is** None, and devices exactly `()`. Select broadly enough to detect a wrong participant in the worker rather than discarding that bad call as unrelated. Unselected calls must delegate normally.
3. Preserve the recurrent public-operation observer and its actual `(participant, kind, lineage)` assertion. Retain the exact yielded original operation for its acquisition observation as well. No route fallback or dual old/new compatibility behavior is needed: fixture kind determines the expected route.
4. Keep the original registered peer strongly alive through the full trial. Start the real sampler only inside the genuine peer hold, with explicit `lineage=None`. Retain reached wait3 seconds, done negative wait0.5 seconds, finally release and bounded join5 seconds. Keep monkeypatches live until worker cleanup finishes. Do not swallow entry/body/exit exceptions; worker exceptions remain failed outcomes.
5. While the peer is held, require reached, no acquired operation, no completion, unchanged live rows and unchanged selected ambient stream. For migrated cases require no selected invocation issuance and no token observation yet. Checking acquired again after the negative wait closes an avoidable observation race. Do not obtain an owner/domain diagnostic lock while checking the held state.
6. After release and join require acquired, completed worker, exactly one authentic yielded operation observation, the exact original invocation record for flat/PER (actual operation arguments for recurrent), and one successful real result without captured exception. Keep full serialized replay equality and selected Torch/NumPy/Python advancement. Type checks alone are not token-authenticity proof; authenticity comes from forwarding and recording the exact original context yield. Do not call invocation methods from the main thread: the handle is issuing-thread-bound.

These constraints preserve meaningful failures for absent route entry, premature authority or invocation issuance, early completion/draw, wrong actual dispatch arguments, fake acquisition, original context failure, replay-state mutation and missing real RNG advancement. They do not require a new runtime compatibility adapter.

## Finite acceptance and evidence

Before execution, root must freeze the exact revised test bytes, unchanged production identities, candidate manifest/tree, selected node inventory and intended commands under a fresh attempt. Independent patch review must confirm the delegation and assertion boundary above. Relevant changed-test style checks must pass at those bytes. No runtime or lint was executed by this reviewer.

The first focused runtime selection is exactly:

- `tests/test_townlet/regressions/bac/test_replay_rng_custody.py::test_direct_ambient_sample_waits_for_registered_peer[flat]`
- `tests/test_townlet/regressions/bac/test_replay_rng_custody.py::test_direct_ambient_sample_waits_for_registered_peer[per]`
- `tests/test_townlet/regressions/bac/test_replay_rng_custody.py::test_direct_ambient_sample_waits_for_registered_peer[recurrent]`

After those pass with their causal assertions actually reached, rerun the exact affected54 from the R113 root record: its healthy53 selection and `test_isolated_replay_poison_refuses_all_direct_samplers`, preserving the isolated child's actual source/import/PID/PPID/controller/thread custody and appropriate strong verification. Freeze the node set, not merely an expected count. Expected bounded result is54 PASS, zero failures/skips/unrun within that selection. The focused3 overlap those54 and add no unique coverage. Earlier same-byte production passes retain their own source/attempt scope; they are not fresh execution of a changed test file.

Record immutable attempts including failure/interruption/unrun facts, exact commands, source/environment/hardware/process custody, elapsed/result/log/verifier bindings and independent review. Retain R113's52/2 affected result and51/2 healthy attempt permanently. A later successful retry does not turn either historical attempt green. Any candidate drift or observer redesign requires renewed exact review; an unexpected runtime failure remains a failure to diagnose, not grounds for relaxing assertions or broad repeated retries.

Acceptance here can close only this test-observer repair and its bounded affected-replay qualification. It does not close fresh-process import ordering, parent outcome ownership/lock handoff, recurrent/runner integration, global typing, full/default suites, coverage>=70%, slow/learning checks, actual CUDA/B6, final review or exact remote CI. Original programme accounting remains28 qualified/38 remaining/66 total.

## Review actions

Read-only source/document/evidence inspection and hash checks only; the sole written artifact is this review. No application/import/test execution, production/test/tracked-document edit, Git mutation, branch/worktree/checkout, execution copy, deletion, cancellation or delegation was performed. WIP20 remains root-owned and retains the current failures. The design is ready for a separately authorized concrete test-only patch within this boundary; this review is not that patch's approval.
