# Independent native PER/SEQ source review

2026-11-14. Reviewer task `/root/pw04_native_replay_astra_review`, independent of the production owners. Actual implementation was reviewed against the PER/SEQ route plans and POP/C API handoffs, not credited from their implementation promises. AGENTS.md and BAC evidence-process guidance were read. No application imports, tests, runtime experiments, Git operations, branches, worktrees or source copies were performed. Only this new prose record was authored. Root owns execution, candidate custody and qualification.

Disposition: one concrete P2 remains; no P1 or additional P2 identified in this bounded source review. This is not zero-P1/P2 closure or a runtime pass.

## Exact source scope

Five complete source/test bodies were inspected, totaling 4724 lines (SEQ was actually 2020, rather than the supplied 2022 estimate). Start/end SHA-256 checks agreed. No runner, POP, C, flat replay, historical-checkpoint, sampling-helper or fixture implementation body was opened. Their documented contracts are dependencies, not independently established facts here.

| Path | Whole-body lines | SHA-256 |
| --- | ---: | --- |
| src/townlet/training/prioritized_replay_buffer.py | 1370 | 673c2ffb240604c3134836c8742394f978e73f195eb73750410a817452ef2b73 |
| src/townlet/training/sequential_replay_buffer.py | 2020 | 7c474611cb917c72862774b4bc1f8468de4765a8896064d2a1c575e5183d4d0c |
| src/townlet/training/replay_contract.py | 949 | de14dd2005934bee6f564f0aaca532bfefcd962d62a76a3a93efdb60274196c8 |
| tests/test_townlet/regressions/bac/test_native_prioritized_replay_data.py | 196 | e84542160183338fa48d386ac3ac26d841611c94d9f358de937b8c2730e6d7fd |
| tests/test_townlet/regressions/bac/test_native_sequential_replay_data.py | 189 | 3197b615625881259acd748a2722fe9fd028d440019b7b0d875941faef184725 |

## NR-2 — P2: native PER staging permits historical conversion

Location: `prioritized_replay_buffer.py:1314`, in `stage_native_restore`. The new native method passes caller transport directly into `_prepare_serialized` without requiring exact current format6. The generic validator accepts formats4/5/6 at lines961–973. Its format5 branch manufactures physical-slot IDs and selects an external-global sampler (lines 1163–1166); its format4 materialization creates an archive and empty active storage (lines 1219–1235). Neither behavior is a full current native restore. By contrast, SEQ's native stage explicitly requires the receiver's current uniform6/prioritized7 format at lines 910–915.

Concrete source-derived counterexample: obtain a genuine current INITIAL POP plan for a configured PER receiver and its defensive current6 replay state through the existing real-parent fixture. Construct exact captured5 transport by setting `format_version=5` and removing exactly `unit_ids`, `next_unit_id`, `sampling_mode`, `sampling_origin`, `sampling_objective_unit`, `sampling_weight_rule`, and `sampling_rng`; retain all captured row/mask/presence/archive fields and compatible capacity/alpha/beta configuration. Call the public native stage with the genuine plan. The native stage accepts this historical shape, rebuilds IDs and records `captured5-physical-slot-adapter` with `rng=None`, instead of refusing. An empty fixture already demonstrates the silent private-generator-to-global-sampler substitution in issued data; nonempty captured5 also replaces durable IDs. This is an unexecuted source counterexample, not an observed test result.

The genuine parent verifier authenticates owner/plan association; it does not make this transport current. The finalizer correctly gates publication but does not reject the already converted candidate. Root confirmed that native-only current-format refusal is the intended contract, and upstream POP validation does not waive the native child's contract. There is no claimed ability to forge C authority or publish outside the actual finalizer.

Minimal repair: inside the real prepare operation, after parent revalidation and before `_prepare_serialized`, require a mapping with exact integer `format_version == PRIORITIZED_REPLAY_BUFFER_FORMAT_VERSION`. Preserve the separately supported generic archival import path. Add genuine-plan native refusal cases for captured5 and historical4; assert receiver and ambient RNG unchanged and no native data issued. Root should observe the causal RED and own subsequent qualification. No patch was made by this reviewer.

## Source-supported properties and limits

Both new installers authenticate opaque owner-held native records and the actual C finalizer before opening a fresh install operation, then repeat those checks inside it. Shared records pin receiver revision/capacity/device, parent weak identity, PID/thread, and do not retain RNG currentness tokens. Consumption precedes publication; publication exceptions quarantine replay, and entered device-invocation completion failure also quarantines it. Reuse after successful publication is refused by record removal/revision advancement.

PER precomputes the reverse ID map and owns tensor storage, priority/ID arrays and sampler state before publication. SEQ preconstructs its deque, owned fragments/options, priority domains/generator and merged archives. Native publication assigns those values to the existing replay owner without cloning, restoring generators, building dictionaries/deques or merging archives in the publication closure. Same-owner identity is maintained in the inspected implementation. Normal guarded mutations advance revision and invalidate staged records. This review does not treat direct writes to private registries/fields as public authority counterexamples.

PER native staging uses the existing prepare transport inventory and traverses its new payload. SEQ's native inventory includes incoming transport, live episodes and archives; its child traversal covers deque/prepared episode/archive tensors. Shared admitted planning adds all retained ordinary and native staged payloads. SEQ's prepared priority state contains NumPy arrays, scalar/tuple metadata and a private NumPy generator, so excluding that object from CUDA traversal does not itself omit a retained CUDA tensor. The inspected SEQ constructor requires concrete CUDA device metadata; materialization's existing `self.device` is therefore concrete. Actual admission/completion and hardware behavior remain unexecuted here.

The inspected tests cover genuine staging and refusal paths, not successful C finalization. PER coverage uses INITIAL empty storage and does not establish nonempty masks/history or next-sample/priority-update equivalence. SEQ includes a real nonempty producer path and malformed masks/bounds/IDs, but does not prove successful finalizer publication or populated priority-domain continuation. No positive installation, consumed reuse after success, terminal publication/completion failure, exact next-learning update or CUDA pass follows from these source assertions.

Root reported the causal R171 missing-stage RED after the real nonempty SEQ fixture and is running later GREEN qualification. Those executions were not performed or independently observed by this reviewer. Required follow-up remains exact-source runtime evidence for genuine C success, preserved complete state/no aliases, sampler receipts/IDs/weights and subsequent priority updates, retained owner identities, next real learner update, failed/uncertain completion fencing, and applicable CUDA checks. Pending runtime/coverage work is not counted as an additional proven P2. No optional P3 is raised.
