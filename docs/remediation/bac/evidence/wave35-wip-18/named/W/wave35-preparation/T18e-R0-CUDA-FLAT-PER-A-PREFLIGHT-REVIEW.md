# Packet A flat/PER CUDA producer — independent preflight review

2026-11-13. Initial source/capsule assessment only; no production approval or runtime qualification. Root-supplied base is `9acd85d3ccd897051288a13fd16e610b9ee1fca1`; no Git command independently verified that base. The requested capsule SHA256 matched `3f9bbd459f2bdee7b4ec27ce46eea334fc800be4b968ad4d58370e352fab7416`.

Read repository AGENTS.md and the packet brief first, then the named design/local-gate/preflight authorities and corrections, public core/replay contracts, source capsule and supplier prose. Exactly three production bodies were admitted, measured before reading and hash-verified:

| Body under src/townlet/training | Lines | SHA256 |
| --- | ---: | --- |
| replay_contract.py | 374 | 8de53fc6814a16bafb703728ed396d7b9a1298afdb415be4ec8d1d85ac1502a1 |
| replay_buffer.py | 728 | 817495558b45a51ba5df3751f83d1985135e23d9dfe6f827e3e323c45df01214 |
| prioritized_replay_buffer.py | 1164 | b989a8f153cf6a2686140efcfb6ce1d4914f4379785c2c094e1cc5d1142033b8 |

Total 2266 lines / three bodies. Reserved fourth test body was NOT read. Production ceilings remain 650/850/1300, test ceiling1000, planned3800/four; no additional body grant is inferred. No excluded core/recurrent/old-test/helper body, imports, application runtime, tests, source copies, Git actions, branches/worktrees or delegation. This review artifact is the only authored file.

## Classification disposition

No new blocking mismatch found between the capsule's finite route classification and these actual source bodies. Initial constructor/CPU test preparation may proceed under root's existing writer grant. The implementation, tests and activation remain unreviewed and unqualified.

The two exact concrete families and 18 proposed route constants correctly distinguish the actual local tensor leaves from sample/sample_batch and genuine prepare/install. In particular, flat load_for_mode has a separately guarded private validation prelude; PER goes through public validate_serialized. Neither complete load composition is a local leaf. Flat selected-device randperm and PER direct global-vectorized versus qualified configured-Generator sampling remain real admitted stochastic work.

Owner-only retained counts, size/length, stats, clear, beta annealing and PER configuration agree with the ordinary-data source profile. Stats reads tensor metadata. Clear drops references and updates CPU metadata. PER configuration reconstructs an offside engine from explicit saved state, with no persistent/global draw. These routes must not gain a CUDA prerequisite merely because a selector, retained field or prepared material is CUDA-backed.

The tensor-local candidates contain the stated reductions/copies/indexing/allocation and archive graph, with no visible ambient random primitive on ordinary supported inputs. This is source classification, not post-poison or hardware qualification. Healthy and post-poison policy remain separate; authentic production route constants remain absent until B. No caller predicate, fixture policy or generic constant may close that dependency.

The detached _PrioritizedArchiveValidator is real and intentionally bypasses custody initialization. Its undecorated validation occurs within the caller's archive work. It must remain an unregistered detached helper, not become a new independently admitted producer. The actual caller also reaches archive reconstruction and public original_state cloning, so that work must remain inside the outer armed scope.

Issuer-held material, owner revision, original RNG tokens, final post-staging validation, one-use publication and partial-publication quarantine are accurately identified. A local successful gate cannot replace owner mutation currentness. A prepared candidate's cloned storage stays on its actual devices during install; changing self.device cannot silently migrate it.

## Finite findings and required test-plan adjustments

### F1 — separate local all-device completion from generic operation semantics

The capsule's combined local/admitted uncertainty row says all declared completions are attempted. Narrow that unconditional assertion to LOCAL complete scopes. Root explicitly requires every local index to be attempted, including after an earlier failure. Preserve the established generic device_operation/parent failure semantics instead of introducing either an early-stop API assertion or an all-device generic-cleanup expansion.

Keep separate cases for local success/body failure, local one/two-device completion failure, and admitted completion uncertainty. For admitted scopes the pending authenticated per-invocation outcome must establish quarantine even when the body and completion raise the same exception object. Exception comparison or a marker attached only to the shared nested RNGOperation cannot discharge this. This correction changes the test specification, not the accepted production behavior.

### F2 — distinguish nested completion from later outer-parent completion

The proposed preflight correctly retains owner locks/pins until the parent exits. A separate schedule remains necessary: nested replay completion succeeds, then the parent outer completion fails while preflight still owns replay exclusion. The capsule does not yet state which authenticated outcome consumer owns affected replay-owner quarantine at that later point. Do not imply that successful nested completion plus retained locks proves this failure path.

This is a REQUIRED cross-interface handoff, not an optional follow-up or a fact closed by a child True/False outcome. Carry the exact responsibility into root's scoped outcome/preflight/parent API handoff. Parent handling must establish actual owner/device reachability before assigning quarantine; per-invocation outcome attribution is distinct from producer mutation authority and cannot justify blanket quarantine. The future witness must observe the declared owner disposition before lock release and distinguish a clean parent body failure from uncertain outer CUDA completion. This is a finite integration boundary, not permission to inspect parent/core bodies here or to broaden generic cleanup. It does not block the independent constructor/CPU test groups.

### F3 — make branch-specific laziness causal

Add explicit cases under the existing planned groups, rather than treating configured device as the work inventory:

- Empty/archive-only prepare and install with an unused CUDA selector must remain lazy when all actual sources are CPU and no target tensor is allocated.
- PER declare_unconstrained_action_dim with an already matching vocabulary returns before tensor work; first declaration allocates masks/recorded columns even on empty storage. Test both branches.
- Zero-batch push may avoid destination allocation yet still validate tensor inputs and retained actions. A zero length alone is not proof of a CUDA-free call.
- CPU td_errors priority update must not complete unrelated CUDA storage; CUDA td_errors with a CPU selector must complete its actual source. Cover stable-ID and physical-slot routes, including normal invalid-ID/shape behavior.
- Readiness uses retained legality; serialization uses actual nonempty rows and archive sources. Neither resolves an unused selected destination.

These are direct source consequences, not extra features. Invalid arguments should continue to reach the original validation behavior; do not satisfy laziness tests by introducing unsupported blanket rejections.

### F4 — test independent fields and archive inventory before copying

Do not let a selected/observations-only two-device fixture stand in for every storage/input field. Include a secondary reward component or presence/legality field on a distinct metadata device, an issuer-held candidate after selector change, and an archive whose retained source differs from both active rows and target. Inventory the actual accessed sources before the first clone/reduction/transfer; assert only finite real-device tuples, never device-count-wide coverage.

For the ordinary archive witness, construct its legitimate owned input before observation begins, then observe actual producer entry. No _record/_archive_from_state/public clone-on-read accessor may run as the pre-completion inventory step. Actual ownership copies remain inside completion. Use the real algorithm and authentic dispatch after activation; simulated tensor metadata is CPU protocol evidence only.

### F5 — preserve causal exclusion and currentness witnesses

At synchronization barriers, a competing thread must signal an actual attempted owner mutation before the test concludes that it is blocked. Then observe completion or quarantine before that mutation can enter. Exercise local and admitted paths separately, success and body failure, and nested versus outer-parent lifetime separately. Keep bounded unwind handling; no generic cleanup expansion is implied.

For same-parent stale candidates, retain a positive prepare/install control and pure-read/no-op controls, then show local mutation invalidates by owner revision independently of unchanged core token fields. Failed preparations must preserve full live data and original CPU/NumPy/Torch RNG state when the actual path does not draw, followed by fresh healthy preparation. Do not reuse a stale handle as the positive recovery control.

## Supplier boundary update

Read and SHA256-verified new `T18e-R0-CUDA-ARCHIVE-INPUT-INVENTORY-FACTS.md`: `e8eaf1472efacbe5ade2605f41311e640000495cc96a045047b99a0126bf8adc`. Its independent source qualification closes the previously named metadata-access feasibility and ordinary RewardTensor-field gaps without reading those bodies here.

For exact canonical HistoricalReplayArchive, trusted internal object.__getattribute__ slot access can inspect retained original_state without clone-on-read. Metadata-only traversal must neither mutate nor return those stored references. Supported plain record original_state mappings can likewise be inspected before reconstruction. The producer's actual archive paths match this supplier boundary. Ordinary source_formats contains scalar metadata; arbitrary malformed/custom protocols do not gain purity from that fact.

Exact RewardTensor fields are plain mutable aliases, not validated owned copies. Include total and every non-None component independently; no .to/.cpu/batch_size/repr call is necessary to inventory them. The producer's visible validation accesses precisely these fields. Caller quiescence and existing custom-object cooperative limits persist. Neither supplier capsule justifies silently removing previously supported classes/inputs or declaring arbitrary Mapping/Tensor hooks pure.

The prior hash-bound historical_checkpoint/per_sampling RNG facts remain consumed as supplier prose. The admitted SamplingReceipt and successor-mask implementations close their named producer-helper edges; no extra helper inspection was needed.

## Remaining disposition

Initial finite source classification is suitable for tests-first continuation subject to F1–F5 and the named root-owned outcome/integration handoff. No reviewed test bytes or runtime results exist in this review. After author test freeze, root must provide exact test/report bytes and the separate bounded test-review grant before the reserved fourth body is read.

Production implementation review, B's authentic activation and paired core/existing-core-test update, final-byte CPU evidence, parent integration and real one-/two-device CUDA matrix remain owed. A remains staged/incomplete. No B6/programme acceptance, hardware result, capability waiver or accounting change is asserted.
