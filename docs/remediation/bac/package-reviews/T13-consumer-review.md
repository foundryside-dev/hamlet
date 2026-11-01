# Review provenance

Final scoped source/spec review at tested tree `f88f7cb3e3d0203ab199a2d898e3b0f8370d7e48`, identical to qualified source `495360d68c167b741d8ed5016c0921f995aac1f4`. Coordinator runtime is attributed; this artifact does not assert independent runtime unless its body does.

Original `T13-native-consumer-independent-review-r4.md`, SHA256 `683ed7665c7e31b54307e5adb08860375e8f1dc84fee24b1e8dd09361851973d`, retained unchanged; portable rendering normalizes execution paths.

# T13 native consumer independent review r4

Date: 2026-11-01 UTC. **APPROVE — bounded static producer/consumer preservation assessment.** No unresolved P1/P2 or new material gap found within this review's three-file boundary. Runtime qualification remains pending; this is not full T13 or whole-BAC approval.

## Exact candidate and inventory

Workspace `/workspace/hamlet`; HEAD `41edeb0858cba98a8dcb6ba2af36355457ef4e0a`; supplied frozen staged tree `f88f7cb3e3d0203ab199a2d898e3b0f8370d7e48` (root names its manifest `wave07/green-r4-candidate.json`). Read-only index comparison against that tree exited0; scoped working/index comparison exited0. No git write-tree was used.

| Whole source file | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/training/prioritized_replay_buffer.py` | 1092 | `290eadca0305658abdd4aec361a9b167ac63d7a887438b602c19c2eaf9020de9` |
| `tests/test_townlet/unit/population/test_vectorized_population.py` | 1884 | `9e0b50095cd29470afc92d42a740a800e34c731aea12abfa96a7d60d89b1015c` |
| `tests/test_townlet/integration/test_compact_token_acceptance.py` | 854 | `5c2369f2303b417b1b6021e13444db93f2c47827b074c57f6ccbc68f376adb23` |

Three whole files,3,830 lines total. The complete current producer was reread. Both complete test files were read in this same review context during R3; fresh hashes and the R3→R4 tree diff verify they are byte-identical, allowing reassessment against their actual retained contents. No fourth implementation/test/helper file was opened. Applicable AGENTS/CLAUDE/STATUS, History A, accepted P3 and relevant checkout guidance were already read in this context and remain applicable. The root manifest was not located by the bounded internal-path filename search; candidate identity is established directly by the successful index/tree comparison and listed file hashes, not by claiming a manifest read.

## R3 failure and causal R4 repair

Root's actual R3 result remains **1FAIL/104PASS in75.84s**, log `qualification/wave07-owners-r3/native-checkpoint-consumers.log`, SHA256 `70ba525728f32036cc3cd38d3b30951a6dee1716b2a0f9bf23f086af2cbcfdf6`. This is attributed execution evidence. The preserved compact PER control at line695 expected `Buffer size` for archived empty `sample(1)` but received `PER priorities must be a nonempty one-dimensional float64 array`.

The R3→R4 diff for the three owned files is exactly seven added producer lines546–552. `sample` now checks a positive Python int or NumPy integer batch against retained size, excluding Python/NumPy booleans, before sampler delegation. For the reported case N=0,B=1 it raises exactly `Buffer size (0) < batch_size (1)`. This restores the public diagnostic and expresses actual active availability after archive import; it does not sample archived priorities or invent active rows.

The guard also correctly covers a positive integer B>N in a populated buffer. Type checks short-circuit before comparisons for other types; zero/negative integers, booleans, floats, tensors and arrays continue to the existing helper validation path. No success path for valid B<=N changes. No RNG call, state assignment, archive operation or tensor allocation precedes the new refusal, so the repaired refusal itself cannot consume the global or configured generator. The guard is only on the legacy physical-index sample adapter; qualified sampling readiness and its separate IID/successive policy remain unchanged. This avoids incorrectly imposing no-replacement limits on the qualified IID API.

**Static disposition of the R3 blocker: repaired in this R4 producer. Runtime closure still requires the replacement run.** The unchanged owner assertion continues to detect any recurrence.

## Complete local contract reassessment

The actual producer still emits PER6 with its exact34-key schema. Its closed-key validation distinguishes19-key maskless4 and27-key captured5 before materialization. The seven added keys are stable IDs/counter plus sampling mode/origin/objective/weight rule/RNG. Exact captured5 preserves active rows, recorded legality and presence, priority/ring/beta state and archive records, assigning physical-slot IDs and the explicit captured5 external-global sampler origin. A current6 dictionary merely tagged5 remains malformed. No fake historical fixture is introduced by either consumer.

Current6 IDs/counter are validated and restored, insertion retires replaced IDs while allocating monotonic replacements, clear retains the counter, and stable priority updates reject retired/unknown IDs. Physical-index priority updates and the raw push/sample adapters remain callable. Update candidates validate finite float32 representability and reduce duplicate targets before live assignment. Configured owned RNG state is cloned/restored offside; legacy sampling remains delegated to the global NumPy path. No global RNG seed/set-state call appears in this producer. Helper-level estimator mathematics and invalid-batch diagnostic details remain outside this three-file lens.

Restore still validates into owned tensors/arrays, materializes offside and clones fallible installation resources before live assignment. History A remains respected: maskless4 full resume refuses; archival import leaves zero active rows with historical data owned separately; current captured rows cannot be discarded by requesting archive/fresh mode. The empty sample diagnostic repair makes this preserved historical path satisfy its original consumer contract.

All consumer checks remain meaningful:

- Population line1051 expects current PER6 while preserving prioritized→standard wrong-kind corruption, its precise diagnostic, and whole-runtime Q/target/optimizer/scheduler/clocks/replay/exploration equality. Standard replay's format5 assertion at line1002 remains correct for that distinct producer.
- Compact lines571–580 reject PER6 payloads with both old tags5 and4. Each tag has its own input snapshot and full input/live equality check; common post-refusal checks also remain. No removed keys pretend to create authentic captured5.
- Genuine PER4 remains an independent19-key fixture with annealed beta, physical priorities and recorded reward components. Its pure validation, missing-mask full-resume refusal, source-format/count/original-state/query assertions, empty active sample refusal, input ownership, current6 archive-wrapper roundtrip and unsupported3 refusal all remain.
- Current standard and sequential matrices, sequential genuine5/current6 transport and stable identities, provenance, legality and unsupported-format controls are unchanged. No node, parameterization, diagnostic match, purity check or historical assertion was weakened to secure this repair. No stale current-PER5 reference remains in these two test files.

## Findings, limits and handoff

No new actionable scoped P1/P2 or optional P3. The accepted permanent compiled-encoder transport assertion P3 remains separate. Positive authentic captured5 runtime evidence, helper internals and full population/native loader behavior belong to separately bounded reviews; this report does not claim that the malformed-tag tests prove genuine5 execution.

No runtime/import/pytest/probe was performed here. Root's planned complete118-consumer replacement, six guards and full repository gate are not counted as passed. The failed R3 run remains failed. X04 finite mean-TD telemetry P1 remains required T15 work; complete T24/T25 native continuation/admission and final whole-BAC qualification remain OPEN.

Only this requested ignored review prose was written. No source/test/index mutation, staging/commit, branch/worktree/source-copy creation, deletion, subdelegation or git write-tree occurred. Existing14 worktrees are preserved. Root remains sole integration/index/runtime owner. No durable rule was saved, the user-only fallback was not adopted, and the failed rule grants/restricts nothing; existing instructions and actual approvals govern. Stationary after final identity recheck.
