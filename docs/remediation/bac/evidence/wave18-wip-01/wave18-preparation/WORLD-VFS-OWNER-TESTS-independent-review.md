# Independent owner-fixture source review

Specification verdict: APPROVE for the R2 -> R3 four-test migration, subject to outstanding runtime qualification. Quality verdict: APPROVE. No introduced P1/P2/P3 defect found in this bounded source review. This is not a test PASS, integrated-runner approval, or overall BAC approval.

Reviewed the supplied actual-delta-only package against all five whole current files, author report, latest owner brief, CURRENT-WORLD-VFS-CONTRACT and CURRENT-RUNNER-NATIVE-RECEIPT. Root identifies R3 tree 59afaaa2ca3164e29573569dbdf5907ca8e77a94 / base d7; tree identity is attributed, not independently queried with Git. The producer sources/new test remain separately reviewed R2 evidence. I opened no sixth implementation/test/helper source, no ENV/ROSTER/constructor/runner source, ran no imports or tests, and performed no Git/index/branch/worktree/copy/deletion operations. Only this ignored report was written.

## Independently measured inventory

Measured with sha256sum and wc -l against the actual files; all match the sealed author report. Paths below are relative to /workspace/hamlet.

| File | Lines / cap | SHA256 |
|---|---:|---|
| tests/test_townlet/regressions/bac/test_world_episode_identity.py | 856 / 950 | 31a7d0d607a643f0e1f5b36f951fd10188f62d37b3981eadf5f928e39151b006 |
| tests/test_townlet/unit/vfs/test_random_expressions.py | 530 / 700 | a6e034c8fe5212c73453a3e7203a689d4f6f384f5544f2751c2f0ccfd1943613 |
| tests/test_townlet/unit/vfs/test_vtc_bounds_clamps.py | 120 / 150 | dd4f875ae554bfcf2fc84ea47b162a4dd27b304ab4be45f595c5754e7fbb23cc |
| tests/test_townlet/unit/vfs/test_verify_r3_repairs.py | 610 / 950 | fa60d49bd430f983bd53e38b21a2014338fb5e6dcae3d30a759b51be9270bd9d |
| src/townlet/vfs/random_draws.py (read only) | 254 / 350 | 751e5766b5efd99a79ccc86c410d76534c397ed9ece59ca67cf2ae4fd83ef676 |

Total 5 files / 2370 lines, within 3100. Static definitions counted independently: 28 + 14 + 3 + 22 = 67. Parameter groups yield 54 + 14 + 3 + 35 = 106 cases. The supplied actual delta changes no test names or parameter lists. No skip/xfail occurs in these files (rg returned no matches). This is static cardinality evidence; actual R3 collection remains a separate runtime gate.

## Specification assessment

The migration retains every functional assertion in the supplied R2 -> R3 delta. Old schema/constructor/reference spellings change coherently, with stronger child assertions added. World identity exact top-level key set at lines 669 onward contains all fourteen old keys plus vfs_random_context: fifteen, not sixteen. Initial snapshot at 492 onward asserts the exact five-field child and zero cursor context. v2 refusal remains and v3 refusal adds destination-state purity checking within the existing schema parameter case. Historical two-boundary/two-permutation checks remain, with explicit reversed current producer IDs, seed and sequence2 checks at 592 onward. Both old snapshot mutation checks remain and child list ownership checks are added.

Random-expression snapshots at 261 onward still include observations, meters, positions and every registry variable. Recursive equality remains bitwise with key/length checks. The 64-step world0 alternating action trajectory and checks that world0 actually changed remain intact; no mask filtering or legality assertion has been added to this trajectory. Cross-N checks retain exactly their original four-variable projection; they have not been narrowed by the migration. R3 world0 differential at 361 onward still compares observations, rewards, dones, meters and the whole eligible registry over all 24 original steps and all three N values. Existing affordance shape, per-element uniqueness, cross-N prefix, shared rule condition, declaration/reorder/unrelated-mechanic, diagnostic, compile-RNG and initialized-value assertions survive.

Factories author explicit stable exact-ID prefixes and provide the same explicit training seed to real compiled-universe construction. This is legitimate fixture declaration, not production inference of identity from row position. Numeric fixtures use actual keyword-only VFSWorldContext/VFSRandomness and actual reference_uniform arguments. Profile draw shape3/tick5/site var:x/ordinal0 remains; wrong-world-count refusal still compares3 versus2. Kernel test retains large seed 2**63+12345, sequence2, tick9, second draw ordinal1 and exact3x5 float32 tensor comparison. The separate8192-ID normal context retains both original0.05 moment tolerances. Bounds metadata, nonmutation, undeclared-bar, phase and inactive-agent assertions remain.

New _EpisodeDriver classes call actual prepare/validate/reset/activate. For tests that cross episodes, step records active-on-entry IDs and executes real ENV.step; complete refuses empty participation and calls prepare close, freeze, close, and install the authority's completed release. The receipts and opaque completion content are correctly labeled local producer-test interfaces. They do not impersonate actual bank/learner/provider preparation. No production reset is monkeypatched into a legacy no-argument API. The participant set is not used as a replacement for ENV's own participation validation.

Direct resume at R3 lines392-426 performs three real episodes with three WAIT ticks each and closes/releases each boundary before exporting COMPLETED. This deliberately adds three setup ticks in the formerly unstepped third episode, as required to make the third boundary genuine; it preserves the old WAIT action choice and the next-reset-plus-five-tick comparison trajectory. Both destinations use explicit seed11 and matching declared IDs; seed_all(999) remains immediately before fresh destination construction. Native prepare/restored attestation/install is used, and all five V3_VARS are compared bitwise at all six observed instants. No scalar-state adapter or fabricated empty episode is used. New-episode and seed-capture setup adds a real mask-selected participating step before completion, with original target draw comparisons intact.

The independent schema9/key guard at R3 lines429-432 remains unchanged against the actual public runner receipt. It is correctly separated from direct ENV resume. It cannot establish real runner save/load compatibility.

## Quality assessment and remaining gaps

No actionable introduced defect found. The small duplicated driver is readable and stays inside the explicitly constrained existing test inventory; extracting a sixth helper is neither needed nor authorized. Batch bookkeeping is local release bookkeeping; accepted live sequences originate in ENV, and restored bookkeeping derives from the validated state. Existing tests that do not close can use direct env.step without needing the helper's close-participant tracking. All current helper call sites that do close use driver.step first.

Outstanding qualification gates are gaps, not inferred successes:

- Root current collection, focused three and joint289 execution were pending in the review brief. I executed none of these and infer no owner-fixture PASS from the separate R2 producer40 PASS/4 CUDA SKIP receipt.
- Later guarded independent execution of the exact106 owner cases is still required. This review is the source/specification/quality portion only; no runtime slot has been provided to this reviewer.
- Actual runner format9 parent scalar validation and standalone restore remain OPEN per the authoritative current runner receipt. The preserved field guard cannot close that incompatibility. Genuine parent/bank/provider/NN/manifest/learning/restart integration remains required.
- Native assertions here establish intended direct ENV boundary behavior, not whole simulator independence, mid-episode continuation, real outer native parent compatibility or CUDA qualification. The full world0 snapshots remain present, so a runtime failure there must be investigated rather than narrowed away.

No source or assertion change is requested by this static review. Proceed with the already planned guarded runtime gates; retain the actual runner integration obligation explicitly OPEN.

## Guarded independent runtime receipt

Root subsequently authorized the exact wave18-r3-independent-spec.json after closing its focused/joint runtime slot. Executed that spec through /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py with TMPDIR=/workspace/bac-review-2026-11-01/qualification/scratch/tmp-wave08-r3, then executed verify_bac_run.py against the same spec.

Actual result: **106 passed, 0 skipped, 0 xfailed, 0 xpassed, 0 warnings**. Pytest reports31.32s; guarded job wall34.6787486076355s; exit0. Candidate59afaaa2ca3164e29573569dbdf5907ca8e77a94, base d7aea669ea49a88140a833c473f56b7e7ae83b01. Log: /workspace/bac-review-2026-11-01/qualification/wave18-r3-independent/independent.log, SHA256 8f5c136a8ff94ffb3bbdd5ca24541cadba6a2e911907653a7420ec1fb9e8a21c. Manifest SHA25605927bc7d4ae210515d3698dccc34b78134a8f9c6ad4ed972d352281bcce2163; harness SHA256180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791.

Verifier exit0, source_index_import_threads_fixture_custody **PASS**:190 source guards,1 process identity,573 config digests,13 protected artifacts,14 worktree registry records,1 available worktree. Exec session72724 completed with exit0 before verification; no reviewer runtime session remains active. No extra source opened or tracked mutation performed by the reviewer.

This closes the previously pending independent106 runtime gate and confirms the bounded specification/quality APPROVE on the exact candidate. Root separately reports focused3 PASS and joint285 PASS/4 CUDA SKIP; those overlapping counts are attributed and are not summed with this run. The actual runner format9 scalar-parent incompatibility remains OPEN. Neither these106 cases nor the unchanged field guard establish real runner/bank/provider/NN/manifest/learning/native-parent integration or whole-BAC completion.
