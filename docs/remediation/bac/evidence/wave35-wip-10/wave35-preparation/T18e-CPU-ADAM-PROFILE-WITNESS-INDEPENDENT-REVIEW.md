# Independent CPU Adam RNG-profile witness SPEC+QUALITY review

2026-11-11. Independent bounded source review at root-attributed durable HEAD d152425faf9cfdae1eed00e19719441ce11e0f5d. Source disposition: APPROVE authored witness for execution; no P1/P2 source/spec defect found. Runtime qualification is PENDING root execution and custody evidence. This is not whole-BAC approval.

## Custody and evidence

Read AGENTS.md and applicable review workflow; the dispatched-review scope overrides further delegation, Git and tracker writes. Independently measured metadata before reading the five full implementation/test bodies, then read every line of each. No sixth implementation/test/helper/probe/Torch body, reflection, disassembly, application import, compiler, pytest, runtime probe, Git/index action, branch/worktree, copy or deletion occurred. This prose is the sole authored artifact.

| Body | Whole lines | SHA256 |
|---|---:|---|
| src/townlet/exploration/rnd.py | 910 | 30d3e9fba6ae6f90ffdda425c986bd6abecaf70e3728bdf104ca21ca832adc78 |
| src/townlet/exploration/adaptive_intrinsic.py | 335 | 1f448e07908d6b709b1e66ab5e163fa6dbc93a306b86d9eb8702d7968a47b47a |
| src/townlet/exploration/icm.py | 541 | f6cdecb466ac99b4dfe63ec00417495c3117e8947c5793e54c0dd71aa76d4964 |
| src/townlet/agent/optimizer_factory.py | 162 | 56af1a9c8edb70a25b43a6e10aa3080d9a7b8becff112924e21a9429d994717d |
| tests/test_townlet/regressions/bac/test_cpu_adam_rng_profile.py | 307 | 7c37fb24f54eda7f3e22712e1e7622f9579f8667365f7a1bc80f1048c86e5866 |

Total 2255 <= 2298, five bodies. Independently verified proposal SHA 0c12ec99906744845367f58a71c3b3546c2825b62527cb10daaf70d44390999c, hook API capsule SHA 320e9ab01689a62299a5e9b3978418c06722f07004875e95358e19bbf367c6d3 and author report SHA 73a862410bb9deed6f83ee8701a349701baa2549275b849105f722e91ab9bb9c. Read proposal including controlling addendum, hook API, complete ADAM-RNG-SOURCE-FACTS and NATIVE-ADAM-CONSTRUCTION-FACTS, and author report. Torch implementation and unread configuration/compiler claims remain attributed to those prose capsules and root execution; no independent transitive-source claim is made.

## Whole-test assertion audit

The test genuinely constructs RND, adaptive inner RND, ICM and actual OptimizerFactory outputs. Owned source confirms constructor signatures, exact Parameter ordering, actual Adam construction and native counter APIs. Q Linear is clearly a small real Parameter owner for factory qualification, not a claim about POP network/training. Compiler/resolver entrypoints are actual public APIs; execution must validate their compatibility. ICM options are explicitly authored and validated, not fabricated backend/state or monkeypatched policy.

_profile checks exact Adam and Parameter types, CPU float32 dense nonempty trainable Parameters, identity/order/uniqueness, actual flags for every group and all four exact global/instance step registries. No group rewrite or removal of existing hooks manufactures admission. Eager unmodified methods, absence of dispatch/compiler/AMP/instrumentation extensions and competing in-process RNG users remain controlled execution premises; source hashes alone do not prove them. The test refuses xdist worker execution and custom Python profiling, without pretending these two checks establish all premises.

The main parametrized witness asserts empty actual optimizer state, then measures the first and second zero-argument public steps without any step warmup. Real nonzero dense gradients are created before each interval. Every Parameter must change, remain finite, acquire actual scalar step 1 then 2, and acquire finite nonzero matching moments that progress on step 2. A no-op, absent gradients, missing state or partial Parameter update cannot pass. Native counters are real snapshots and must remain unchanged; no manual update is represented as native service.

_capture_rng owns NumPy array and Torch byte clones. _same_rng compares complete Python state, all legacy NumPy tuple fields including array/cached Gaussian, and exact Torch CPU bytes. Equality is asserted before continuation draws. _assert_continuation compares next Python, NumPy and Torch draws after independently restoring the pre-step state, and restores saved post-step state in finally. Outer fixture captures/restores original ambient state even on failure and verifies restoration. No CUDA RNG API is invoked by authored test code; pinned Adam's own availability checks remain part of its public call.

The actual instance prehook control uses the same comparator, verifies the exact optimizer/call arguments, consumes all three streams, requires all three comparisons false and one actual callback, and checks real step 2 progress. Returned handle removal and RNG restoration occur in finally. Subsequent registry checks and measured clean step 3 establish successful cleanup. It neither installs a global hook nor clears others' hooks. The ordinary baseline must pass before the detector control can pass.

Sparse refusal uses the first genuine factory Parameter, a real matching-shape sparse COO gradient, other gradients None and empty state. It requires public Adam's sparse-gradient RuntimeError, unchanged Parameters, empty state and exact RNG equality/continuation. It makes no multi-group or arbitrary-hook exception transactionality claim.

Version and both installed optimizer.py/adam.py line/hash seals are obtained in the executing process by metadata-only byte hashing at known paths. Dynamo module presence is printed before setup/construction/steps and honestly labeled presence-only. Constructor work is outside snapshots and is not qualified RNG-free. Empty state is not asserted to prove a fully cold library.

## Findings and boundaries

P1/P2: none in the frozen authored witness. Source approval does not replace the pending selected executions or their process-custody evidence.

Optional P3: explicit assertions for absent grad_scale/found_inf attributes and defaults consistency beyond the checked boolean fields would mirror the proposal admission wording more literally. They are not a blocker under the controlled unmodified actual constructors and pinned successful ordinary execution: the attributed selected single-tensor implementation rejects non-None AMP values, and no authored operation attaches such attributes or changes defaults. Do not expand this into a general reflection/profiling survey.

Refuted concerns: deterministic manual gradients are intentional scope, not fake Adam learning state; a missing native forward/backward or replacement-negative-delta scenario is not a defect in this CPU-path witness. Existing bare manual optimizer/replacement/signed-delta capabilities remain unchanged. Instance-hook stochastic work correctly defeats qualification instead of implying all Adam calls are RNG-free. Lack of global-hook/closure/CUDA execution is an explicit boundary, not authority to ban those capabilities. Runtime source seals establish candidate identity, not every mutable namespace's purity. No additional production wrapper, global ban, cohort checkpoint or exact simulator continuation obligation is introduced.

This witness alone does not close shared/private R0 enrollment, B1/reset freshness, native outer publication, same-owner mutation exclusion, native full learning/history, stochastic constructor/forward/backward/closure regions, CUDA or global release gates. Main BAC remains 28 qualified / 38 remaining / 66 total.

## Root execution evidence received (independent runtime still pending)

Root reports closed R35 evidence at candidate 22ee68664004f4cb0b0177e8f92db1686211b18e, base d152425f: collection found six nodes and passed in 3.555117845 seconds with source/config/artifact/index/import/thread/registry custody checks. Four separate fresh family processes passed individually: RND 11.3665893 seconds, adaptive 12.3632815 seconds, ICM 7.8855491 seconds and Q factory 9.5914118 seconds. Root reports 805-source custody PASS for each, exact equality of all three RNG states for both public steps and successful real-progress assertions.

Every family observed Dynamo absent before setup/construction, then present after construction and before first step. These are first-step-empty-state / warm-library results. No cold-library qualification is claimed or owed chase is inferred from these observations. Constructor work remains outside the qualified interval.

Root reports both controls passed together in 11.9325087 seconds wall time: actual stochastic prehook comparison (False, False, False), exactly one callback; clean step 3 (True, True, True); first sparse refusal (True, True, True). The controls run emitted ONE warning at test line 291: sparse_coo_tensor implicit invariant checks disabled. Do not report zero warnings. Root identified a custody-summary parser that recognized plural "warnings" only and is correcting that administrative count from the same closed log while retaining the original receipt. No test rerun or source fix is implied. Explicit sparse construction invariant checking is optional P3 documentation/hardening; successful existing assertions are not contradicted by that warning.

These results are root-received, not reviewer-executed. The independent same-six serial in-process specification is prepared at qualification/wave35-r35-independent-spec.json; independent runtime remains PENDING explicit root execution authority and subsequent root custody verification. The previously stated source approval and bounded exclusions remain unchanged.

## Independent authorized execution closed

Root explicitly authorized the exact prepared wave35-r35-independent-spec.json once after earlier runtime/custody processes closed. Executed only the prescribed locked runner, without reading its implementation or opening another source body. Runner session 38625 CLOSED with exit 0, wall 20.395822048187256 seconds. Independently read the actual closed independent.log: **6 passed, 1 warning in 16.37 seconds**. The warning is the same sparse-construction invariant-check warning at test line 291; no zero-warning claim.

Runner reported candidate 22ee68664004f4cb0b0177e8f92db1686211b18e, base d152425faf9cfdae1eed00e19719441ce11e0f5d, manifest SHA 6e73ae5db7c0846da2b851ad43deeacc39430a323938f696dfb20ddc8520a25e and trusted harness SHA 180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791. Closed log: /workspace/bac-review-2026-11-01/qualification/wave35-r35-independent/independent.log, runner-reported SHA 5b1a1ccc651d1b9165db2e6eecedc888ea6c80f6775b5634ccc5fd68c412063e.

Actual output shows Torch 2.11.0+cu130, optimizer.py 1193/ea3497233845529a212f81d4d325828eadc20f387ab94b1c21b96057f0001536 and adam.py 991/7e5c8482c91b88e355a8bdf1d4b1930e8d961fb99f00c2179946b164a03652b6 for every case. All actual groups have expected flags, beta/epsilon and zero weight decay; RND/adaptive learning rate .001 and ICM/Q factory .0001. Every family first and second step prints (True, True, True); passing nodes establish accompanying Parameter/moment/step/counter/continuation assertions succeeded. Actual hook prints (False, False, False), calls=1; clean step 3 prints all True; sparse refusal prints all True. The six-case serial process reproduces the SAME root four-family plus two-control cases, not twelve unique cases.

RND reports Dynamo absent before setup/construction and present after construction and before step 1. Later cases report it already present. This remains first-step-empty-state / warm-library evidence, not cold-library qualification. No source change or further cold chase is requested.

Independent execution is PASS. Final custody-qualified disposition awaits root's serialized verifier on this closed run; reviewer has not run the verifier or any Git/index operation. Source/spec approval and all bounded non-qualification statements above remain in effect.

## Final custody and publishable API-truth review — controlling disposition

Root's corrected serialized verifier has now CLOSED and PASSed the exact independent specification: job independent, 6 PASS / 1 warning, 20.395822048187256 seconds wall, source805/config573/artifact13/controller1/index/import/thread custody and registry14/MAIN1. This received root verification resolves all earlier pending-custody statements in this report. All named R35 runners/verifiers are CLOSED. No further application execution was performed or required for this final review.

Independently measured then read the complete publish-ready T18e-CPU-ADAM-RNG-PROFILE-CONTRACT-DRAFT.md: 51 lines, SHA256 aff0cf854f9121675239e700a63eac871a125b9f1023321d656b02652df59542. Also verified/read the updated author report SHA256 27057689303f09b631c9014c01062e085f7e628534e7ffd9056d9c12d08b745e. Compared the contract to the already reviewed five actual source bodies, pinned attributed library capsules, independently observed execution and root-received custody facts. No sixth source body, runtime/probe, Git/index or production/test mutation was used.

Final SPEC+QUALITY / API-truth disposition: **APPROVE** the exact sealed 51-line contract for root publication as docs/remediation/bac/CURRENT-CPU-ADAM-RNG-PROFILE.md. No P1/P2 defect or required correction found. The API description correctly limits RNG exemption to the admitted built-in ordinary dense CPU public-step profile; distinguishes real paired native/factory objects from full native or Q learning; identifies manual gradients and warm-library first-step observations; preserves capabilities; separates stochastic regions and same-owner exclusion/freshness; records the sparse warning and six unique overlapping nodes; and preserves the outstanding R0/B1/CUDA/outer/global gates. It does not infer constructor purity, cold-library qualification, mutation detection or complete static success. The six old oracle mypy errors remain a root-received static limitation, not newly reviewed source or a reason to expand this witness.

Final independent status: source/spec APPROVE, independent exact-six execution PASS, root serialized custody PASS, sealed public contract APPROVE. Main BAC remains 28 qualified / 38 remaining / 66 total. Root alone owns publication, status/evidence integration and any commit/push.
