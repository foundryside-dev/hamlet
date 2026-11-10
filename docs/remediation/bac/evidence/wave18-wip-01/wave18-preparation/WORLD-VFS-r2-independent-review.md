# Actual direct-world VFS R2 independent review

Specification verdict: **APPROVE** the bounded source/test implementation against the approved ABI. Quality verdict: **APPROVE**. No material P1/P2/P3 defect found by static review. Independent fixed-source execution remains pending root's exact guarded runtime slot; neither these approvals nor attributed root receipts are an independent runtime PASS.

## Exact reviewed candidate and custody

Received base d7aea669ea49a88140a833c473f56b7e7ae83b01 and staged R2 tree e800bc81ff0487823596a754a499685009c7a945. No Git/index command was used to reproduce those identifiers. Whole current file hashes and line counts independently checked:

| File | Lines | SHA256 |
|---|---:|---|
| src/townlet/environment/vectorized_env.py | 2399 | 5508110716c38d89497c6d3c0443d6eba15f7bd546b9f2231dd86a41f5b6c166 |
| src/townlet/vfs/random_draws.py | 254 | 751e5766b5efd99a79ccc86c410d76534c397ed9ece59ca67cf2ae4fd83ef676 |
| src/townlet/config/world_roster.py | 312 | 1c3f4ad0f29e663a3f7976b10593e08223bba2b46420b2d4472451a78c667f33 |
| tests/test_townlet/regressions/bac/test_world_vfs_identity.py | 586 | 3a7ae1dd63d56b2f81b7a3a2d8a8b7302355747d7c61431bbcc6fb8dec4ab675 |

Exactly 4/3551, within ENV2600/VR700/ROSTER400/test1200 and 4/4900. Review reused the previously read whole frozen constructor ENV and received identity/constructor contracts, examined all supplied production diff hunks and corresponding actual current functions, and read the complete current VR, ROSTER and assigned new test. No fifth implementation/test/helper/fixture/substrate/provider/runner body was read. This review is the only write in this phase. No imports/runtime/tests/formatters/Git/index/branch/worktree/source-copy/deletion/subagent/source edits occurred.

Additional review inputs: WORLD-VFS-brief.md including root's appended adoption/watchpoints; exact approved ABI proposal 16c334d0d1917d663d2f2f87796c6821b11b649628efb3886c5415c7b1fc5419; prior WORLD-VFS-ABI-REVIEW-R1.md; WORLD-VFS-r2-review-brief.md SHA256 40d9bb6894cb922471191d22917dee8a9f53d353a2af5c3030d27700d9d249ce; WORLD-VFS-r2-review-package.md SHA256 06145d6d6ec4fde5cf3b485651bc9691d40ae4545316d5e6a7599247a566d8fa; WORLD-VFS-report.md SHA256 85f0ba803d429531913f27e47d9fa7631467afdfdd748e47a4048060829d9abb; CURRENT-RUNNER-NATIVE-RECEIPT.md SHA256 02a46a7e0b23f240995c8b0a67696f4cce2109077676743744974a7243535647. The inherited AGENTS.md and identity/constructor contract hashes are recorded in R1.

## Specification assessment

**Identity and math.** VR's frozen keyword-only context validates every seed/ID/sequence, rejects aliases such as bool/float integers, keeps independent per-world sequence tuples and returns owned serialized lists. The BLAKE2b8 compact ensure_ascii JSON framing exactly matches the accepted domain recipe and preserves large seeds and exact Unicode/whitespace IDs. It excludes row, N, authored membership/config hash, other-world action/context and batch counters. `_mix64`, tensor logical shifts and signed constants agree modulo 2**64. Scalar and tensor paths implement M(base XOR tick), M(M(instant XOR site_hash) XOR ordinal), then M(site XOR element) >>40. `_signed(ordinal)` is consistent with the scalar modulo arithmetic. Uniform conversion is exact dyadic float32; normal keeps two element lanes, safe positive u1, float64 intermediates and float32 results.

**Shape, device, shared prefix.** Existing DrawInstant stream signatures, DrawStream.worlds, broadcast checks and flatten/reshape conventions remain. Site keys are an N-vector and element lanes broadcast on the second axis; numeric rows no longer enter random identity. Shared prefix retains shared-site original ordinals and write tails restart at zero. No inspected mechanic, family, shared-layout alternative or shape is removed. Context/stream setup remains O(N) host work, with device-local vectorized output mixing, not a Python loop per output element.

**Reset and retry.** ENV constructs sequence-zero context without drawing. Public reset's existing accepted-retry early return precedes producer construction. New reservation/context/producer validation is pure and occurs before resetting; pending context and producer install before `_reset_world_state`, whose old VFS increment is removed. `_vfs_draws` checks the pending candidate during reset and authoritative current projection otherwise. Success accepts the same reservation identity; failure quarantines and finally clears pending state. Native export rejects resetting/restoring/quarantined states. Strict standalone restore validates equal current context only in fresh/bootstrap/released boundary phases and cannot grant release or import cursors. Public step activation gate remains.

**Native and history.** ROSTER validates required v4 VFS child against parent seed, producer destination lanes and exact-ID cursors before INITIAL's early return. COMPLETED history checks remain intact. ENV checkpoints only after existing boundary authorization. Restore preparation validates the saved producer child first, then explicitly derives the fresh destination context without rewriting historical saved/accepted order. The prepared record stores portable owned maps/lists/tuples, not dataclasses/producers/capabilities. Installation validates/builds its producer before mutation, installs it inside the existing guarded operation, consumes no RNG/reset/tick/completion action, and preserves existing equal-install early return. These changes implement all three root watchpoints without expanding the serializer or source inventory.

**Tests and causal evidence.** Actual test bodies use the published current compilation and constructor route plus actual ENV reset/activation/step. Local receipt issuers are labeled producer-only. Literal normative vectors precede production-reference/tensor assertions and are independent of production helper code. The tests exercise lane reversal/leading spectator, action control, unequal pure sequences, uniform/normal/broadcast/device behavior, shared prefix, reset-time projection, accepted retry, late quarantine, owned state, contradictory child refusal, INITIAL/COMPLETED destination remapping and a second snapshot whose producer order differs from historical saved order. Root's reported 2 intended row-domain RED failures, action control PASS, and four locked scalar vectors before old-API TypeError are attributed causal evidence, not executions by this reviewer. No skip hides missing CPU implementation; CUDA unavailability is explicitly marked.

## Quality assessment and finite limits

No material finding. The change is confined to the accepted seam and exact current-native schema replacement; no legacy scalar fallback, independent lifecycle counter, test-only production hook, or helper/source fanout was introduced. Pure validation and producer construction precede expected-refusal mutations. Existing unexpected install/reset failures retain quarantine, without an unsupported rollback claim. Frozen value objects and portable prepared data fit the existing cooperative receipt model.

The assigned test does not cover every malformed shape or every shared-prefix length, and the direct domain tests do not prove whole-simulator state equality. These are limits of the exercised matrix, not observed implementation failures or grounds to narrow supported mechanics. Runtime results and guards remain necessary before integration.

The received actual runner/native receipt establishes an outstanding required incompatibility: checkpoint_utils outer schema9 still requires scalar {seed, episode}, while this implementation exports vfs-world-random-v1. Real runner save/load/world authority/manifest/joint native integration must be repaired and qualified in the existing T23–T26 scope. No producer test count can close that gap, and no outer schema version is guessed here. Old direct VFS/world-native fixture updates remain the separately bounded maintenance task; no old test was opened as a fifth source or v4 check weakened.

Ambient Torch spawn/layout, shared affordance placement, actual learner-reset interference, real bank/private learned state, initialized owner/native parent atomicity, broader family/E2E/restart and final BAC gates remain required. This review approves only the direct VFS consumer source/test packet and explicitly does not approve an integrated BAC release.

## Independent execution

Pending: wait for root's exact guarded fixed-source CPU/spec slot. Append actual command/result/custody here after execution; source and index remain frozen.

### Independent fixed-source execution completed

Root subsequently granted the exact controller-only one-CPU slot, with source/tests/index/tracked docs frozen. Executed only the two authorized positional commands, without opening either helper's source:

```
python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave18-r2-independent-spec.json
python /workspace/bac-review-2026-11-01/qualification/verify_bac_run.py /workspace/bac-review-2026-11-01/qualification/wave18-r2-independent-spec.json
```

Actual independent result: **44 collected; 40 PASS, 4 CUDA SKIP, 0 xfail/xpass, 0 warnings**, exit0. Harness wall10.176632404327393s; pytest reported6.00s. CUDA unavailable cases remain unrun and unqualified. Actual subprocess selection was the complete same counted test file, with --no-cov, no cacheprovider, and bac_source_identity enabled. This is execution against the reviewed fixed candidate, not a substituted fixture or proposal-only test.

Verifier confirms exact candidate tree e800bc81ff0487823596a754a499685009c7a945/base d7aea669ea49a88140a833c473f56b7e7ae83b01; **source_index_import_threads_fixture_custody PASS**, 187 source guards, 573 configuration digests, 13 protected artifacts, 1 process identity, 14 worktree registry records and 1 available worktree. Post-run independent SHA256 of all four counted files still equals the table above. No source/index/tracked documentation mutation or leftover running execution session was introduced; the controller session finished exit0 before verification.

Evidence: qualification/wave18-r2-independent/independent.log SHA256 8c9041859390114d75f90a09c1a3fb834d3090e3e728191fbcab81c6bf028211; manifest SHA256 478a3e6992958a63eea8745f4607411dc8816a863b453a9aeb76f0e305902ec3; harness SHA256 180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791. Log was read as evidence, not additional implementation source.

Specification and quality approvals remain **APPROVE**, now accompanied by this independent CPU execution PASS. Old-owner test maintenance, actual scalar outer-parent schema9 repair, ambient Torch/real learner/bank qualifications and all broader native/E2E/final gates remain open as stated above. These counts do not approve an integrated BAC release.
