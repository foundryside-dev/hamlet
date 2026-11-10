# PW03 R1 independent actual implementation review

Spec verdict: CHANGES REQUIRED. Quality verdict: CHANGES REQUIRED for acceptance of this frozen producer handoff. One material contract failure reproduced; no additional material defect established in the reviewed scope. This is not an integrated-release or package-closure review.

Candidate tree 2912e724e5bec3349e8b065b7a6e4aee6fe372ed; base 50210cfec4fdccf304d4a6bfb00ae179563a5846. Reviewed original task, brief, producer report, R1 review package, approved ABI proposal, final ABI review, source-verified API capsule, current RNG binding contract and AGENTS.md together with the actual implementation. Proposal SHA256 verified d55ec8f46c1c772e4bf55002fdd3caeebc8eac10ce646380da4bfdcd5a6b3bcd.

## Material finding

P1 acceptance blocker / medium functional severity: zero-column count contract is not implemented by the current real backend. Factory lines48-51 allow obs_dim=0 for count_based; lines95-98 construct the existing CountExploration. The approved ABI explicitly promises positive none/count zero-column support. Both required positive count cases then fail on their first real reward call at test_pw_backend_factory.py:460. Authorized runtime evidence reports ValueError: count observations require shape [N,D] with D > 0, raised by the actual provider. Shared and per_world are both affected. Factory successfully returning a provider does not satisfy the promised usable zero-width behavior.

Resolve the source-verified contract discrepancy before approval. If current count is intentionally positive-width only, explicitly correct/re-review the ABI, reject zero-width count at factory preflight and test that refusal, preserving zero-width none. If zero-width count is a desired new requirement, it needs separately authorized provider work and meaningful behavior tests. Do not silently remove the failing controls or modify the read-only provider under this inventory. The five-file review cannot independently inspect Count's full implementation; the failure comes from the authorized run, whose pytest log includes its generated traceback.

## Independent behavior evidence

After root collection/run authorization, executed only:

`python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave23-r1-independent-spec.json`

Wrapper process exited0, actual pytest child exited1. 142 collected; 140 passed, 2 failed, no skips, pytest4.75s, wrapper8.8808481693s. Failures are test_nonrandom_zero_column_geometry_remains_supported[shared-count_based] and [per_world-count_based]. No positive verifier was run because authorization required childexit0. Runtime session95353 is closed. No repeat, ad hoc probe, helper source read, test/source/index edit, install, branch, worktree, copy, commit or push performed.

Log: /workspace/bac-review-2026-11-01/qualification/wave23-r1-independent/independent.log; reported log SHA25663cca68871e384868a52cf6678cfea2e25474a36c446f92917a63affb4d89485. Manifest SHA2560ceca498fcae18c1c956331205a562caaee062ead292dd9c1a00f8a4d1b36868; execution harness SHA256180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791. These are independent execution results, not restatements of producer GREEN.

## Reviewed guarantees and limits

The implementation explicitly maps all five current classes and preserves positive shared None/vector_tick construction; no copied model or compatibility wrapper was introduced. Required ownership inputs have no defaults. Validated policy roundtrip, descriptor reconstruction and actual validate_binding precede private provider construction. The same supplied candidate reaches RND/adaptive/ICM constructors; no throwaway production draw clone or private RNG-field read appears. Current binding capsule supplies stable identity and cross-owner custody semantics. RND/adaptive options and parameters match actual constructor/configure_service APIs; Count/ICM mapping matches the source-verified capsule. Global epsilon selector is independently constructed, and completion cadence remains outside factory ownership.

Passing controls cover all five exact real types, configured parameters/geometry, private model/storage/optimizer/container freshness, different-ID seeds, same-ID reproducibility despite ambient draws/reordered/spectator rosters, ambient restoration, wrong binding/config/geometry preflight, active-other-owner refusal, actual OwnedWorldBackend candidate handoff and component advancement, independent diagnostic/global epsilon, and positive zero-width none. This confirms bounded CPU construction behavior only. Optimizer states are fresh at construction; these controls do not establish genuine learning or strict isolation under optimizer updates. Count's test comment mentions LRU, but its behavioral assertion exercises quantization/repetition; selected max_entries is checked by checkpoint equivalence, not eviction execution. That is not a separate factory blocker.

Remaining mandatory gates: fix/review the count geometry mismatch and rerun sealed qualification plus custody verification; real bank optimizer-update isolation PW05; actual runtime/native/ordinary-runner integration; current owner/consumer migration work; default CI/full qualification and nine reported global mypy errors. CUDA construction/restoration has no positive execution in this packet. No PW04 integrated release, PW03 package closure or overall BAC completion follows from140 passing tests.

## Source inventory

Exactly five whole source/test files opened; rereads only within these files. Caps1100/1000/500/400/1500 total4500; actual2575, below5000. No sixth source/helper/fixture opened. Prose/API receipts replace excluded provider and owner sources. Pytest-generated failure traceback is runtime evidence, not an additional file read.

| File | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/config/exploration_policy.py | 768 | af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c |
| src/townlet/exploration/rnd.py | 834 | 0848cfe8f08635fac6843d90bdf38ca7c08f92ef8220d7859e2ce65dae4ecf0d |
| src/townlet/exploration/adaptive_intrinsic.py | 315 | cb64d78d01c0bb8422dc664206e65588eba373a0a7ed8408634a7fa0a4b80df4 |
| src/townlet/exploration/provider_factory.py | 153 | 9b2afd41ad89820f5d94477f62300fa16aae6f376ee79fa00a4fc22187f4ece1 |
| tests/test_townlet/regressions/bac/test_pw_backend_factory.py | 505 | 7535f1d9ead8ce104a73abc0072f05d4e10879078d440143fd8947fb015c29dc |

## Root reconciliation assessment

After the independent failure, root supplied a corrected source-verified public contract: actual Count rewards require D>0, while none supports zero columns. The proposed reconciliation is sound at design level: retain positive none zero-width construction/rewards; require Count obs_dim>0 at factory preflight; replace the two unsupported Count zero-width positive hypotheses with explicit shared/private refusal-before-constructor controls; first demonstrate those new controls RED against current R1 before production change. Retain every positive-width Count configuration, reward, state and ownership check.

This is a correction of an unsupported premise, not evidence that an existing operational Count zero-width capability is being removed. Independent execution already demonstrates no such capability in either scope. No Count provider algorithm/source change is required. Exact amended ABI bytes, authored regression controls and eventual implementation still require review; R1 spec/quality remain CHANGES REQUIRED until the defect and qualification are resolved. No other material finding emerged from this review.

## R2 exact proposal and test-only review before factory repair

Reviewed exact revised ABI SHA25691c7fdee450119dd50352453f5c19add103adad23a9d1e5af98fbb0c2d2036f6: SPEC APPROVED and QUALITY APPROVED at proposal level. Reviewed test-only candidate ed02906633ded82430fb3af20c6c8f154fe40d61 through PW03-r2-tests-review-package.md and the actual modified test section; test SHA256565c9279a86d3da3d1998762289c0a20f3b3823c5ccfd0f4770d32a708092061,530 lines. Factory independently rehashed unchanged at9b2afd41ad89820f5d94477f62300fa16aae6f376ee79fa00a4fc22187f4ece1. No runtime executed in this review round.

The corrected operational geometry is evidence-based: zero-width none remains a positive real-reward case in both scopes, while Count/RND/adaptive/ICM require positive width. The new two Count controls provide a valid policy and valid zero-width descriptor/RNG where private, patch the real selected class constructor to raise AssertionError and record calls, require ValueError from factory preflight, assert zero constructor calls and unchanged ambient/private streams. They cannot pass by allowing the constructor to perform the refusal. Existing R1 factory is expected to reach that constructor and fail for the intended missing guard; root must obtain genuine RED before repair. The patch preserves all remaining140 cases, including real positive-width Count config/rewards/state ownership and all five backend families. Removing two empirically refuted positive hypotheses while adding stronger preflight requirements is justified contract reconciliation, not mere deletion of failing tests.

No material defect in these proposal/test-only bytes. Proposal phrase "positive-width refusal" is read in context of explicit step1 and the dedicated tests as refusal of nonpositive widths, not refusal of valid positive inputs. Required ABI, owner handoff, shared alternative, RNG identity/restoration, global epsilon separation and service configuration remain unchanged. Five-file actual inventory is2600 within caps4500. No sixth source opened, no provider/fixture/helper introspection and no source/test/index edit. Approval is for the finite proposal and authored regressions only; R1 implementation remains unapproved pending narrow guard repair, fresh sealed GREEN/custody and final actual-source review. All previously recorded integration, optimizer learning/isolation, CUDA and full/default-CI gates remain open.

## R3 final actual fix review and independent verification

Candidate32108b7f6a869c02e0547e6297315cc2aaabfcba against base50210cfec4fdccf304d4a6bfb00ae179563a5846. Final bounded producer SPEC APPROVED; QUALITY APPROVED. Original material finding ADDRESSED. No new material fix-diff breakage found.

Read PW03-r3-review-package.md, producer's causal-RED/fix report and actual factory guard in its surrounding policy/ownership/provider path. Exact factory SHA2567ca30733720017eea4a8063be0261dfd365c9547f501649bd71d937eecd5efb0; unchanged approved test SHA256565c9279a86d3da3d1998762289c0a20f3b3823c5ccfd0f4770d32a708092061; revised ABI SHA25691c7fdee450119dd50352453f5c19add103adad23a9d1e5af98fbb0c2d2036f6. Only the existing zero-width family guard and message changed: all validated strategies other than none require positive observation width before device/ownership validation or construction. Both scopes therefore reject unusable zero-width Count without allocation/draws, while actual none zero-width support and all five positive-width real provider mappings are retained. No Count implementation, RNG owner/binding, service mapping, selector behavior or constructor default was changed. Root-attributed two constructor-called RED and negative custody preceded production authorization; independent final GREEN below confirms the actual repair.

After root142 collection/positive-custody authorization, executed the designated locked packet with /workspace/bac-review-2026-11-01/qualification/wave23-r3-independent-spec.json, then the designated positive verifier with that same spec only after observing childexit0. Independent result142PASS/0skip/0xfail/0xpass/0warnings,11.3739483356s; wrapper and child both exit0. Positive verifier exit0: custody PASS,199 source guards,573 config digests,13 protected artifacts,1 process identity,14 worktree-registry records/1 available worktree. Runtime session21187 is closed; verifier completed synchronously. No ad hoc runtime, repeat, helper-source read or sixth source file.

Independent log /workspace/bac-review-2026-11-01/qualification/wave23-r3-independent/independent.log SHA2562b73540d3dc2b0c46347e95b26284e7c3228afc340032135a098d4a4281c409a; manifest SHA256cbd5c99e820fee5ed99b5c19e3d684e6263739af47c04c688fd1aa24e662668a; harness SHA256180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791.

Final five-file inventory RP768/RND834/AI315/PF153/test530 =2600, named caps4500, hard maximum5000. First three hashes unchanged from R1 inventory; final factory/test hashes above. Read scope remained these exact five source/test files plus authorized prose/data and execution output. Only this ignored report was edited by reviewer.

Approval is limited to the actual CPU factory producer contract, including exact current class/config mapping, positive shared construction, private ownership/binding and construction isolation, real candidate handoff, and independent global epsilon. Genuine bank learning/optimizer-update isolation PW05, actual runtime/native/ordinary-runner integration, CUDA qualification, remaining owner/consumer migration work, nine reported global mypy errors and full/default-CI qualification remain mandatory open gates outside this packet.142 factory tests do not establish those guarantees or authorize PW03/PW04 integrated release, package closure or whole-BAC completion.

## Final current-contract documentation verification

Documentation spec-accuracy verdict: APPROVED. Independently verified CURRENT-BACKEND-FACTORY-CONTRACT.md SHA256538f5081c7fee3c512566c4f9071e08c2c4694eb227dc53027f6aa2141f613f6 and checked its claims against the five already reviewed actual files, approved revised ABI and attributed public API/RNG capsules. No new source or runtime was needed; no source/test/index edits occurred.

The two exact required-input APIs, current policy reconstruction, family-specific geometry (none nonnegative; Count/RND/adaptive/ICM positive), explicit shared absent ownership/vector clock, actual private candidate handoff and binding, complete constructor/service mappings for all five classes, independent global epsilon ownership and absence of factory-owned cadence match the implementation. The Count correction is correctly described as reconciliation of a refuted operational hypothesis, with unchanged positive-width provider behavior. Ownership identity, spectator behavior and continuation-validation limits are attributed to the public RNG receipt rather than claimed from an excluded source read.

Final R3 candidate/hash inventory and independent142PASS/custody evidence match this review. Root142PASS14.9746s and four global guard results are explicitly root-attributed; overlapping runs are not summed. R1 covering378PASS/2conditional CUDA skips is explicitly distinguished from final R3 qualification. Nine remaining global mypy errors, real bank optimizer-update isolation, native/parent checkpoint and ordinary-runner integration, required CLI/full qualification and CUDA/hardware/other unsatisfied gates remain visible. No unsupported integrated-release, package-closure or overall BAC-completion claim found. No material documentation defect established.
