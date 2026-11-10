# Independent owned native metadata review

Status: READONLY preflight complete; actual new test and repair artifact not yet handed off. No acceptance or runtime claim.

Read the bounded brief, repository AGENTS.md, PW07 source-verified codec gap, and only the four authorized production source slots (WS, RND, PF, RP). Fifth slot remains reserved for actual new test. No excluded provider/helper/test implementation opened. No source writes, runtime, probes, index, commits or copies performed.

## Confirmed baseline facts

- WS `_owned` normalizes all Mapping values to plain dict, dropping OrderedDict kind and `_metadata`. All of callback result, native snapshot, prepare input, validation transport and load transport pass this boundary.
- WS `_same` requires matching concrete types but generic mapping keys equality ignores insertion order and does not inspect `_metadata`. Preservation alone therefore does not close metadata-only/order-only validator mutation detection.
- WS prepare invokes actual validator before actual load and requires exact native checkpoint retention afterward. Candidate mutation and transported mutation each need causal evidence; rewriting equality to accommodate loss would defeat the contract.
- Callback and snapshot observations increment destination revision. A test cannot take a destination snapshot between prepare and install unless it expects stale-handle rejection. Rejected preparation itself has no destination revision increment; source and receiver baselines should be explicit.
- RND native checkpoint emits deep-copied actual network state_dict values, optimizer state and FIFO/service counters. Positive learning uses zero_grad/backward/step and consumes a minibatch. Native load reconstructs networks and optimizer; residual Parameter.grad transport is not a native checkpoint promise.
- PF accepts real private descriptor/RNG owners and passes the candidate RNG through to genuine RND/adaptive constructors. RND private service validation requires configured options, service position equal to admitted rows, and zero step_counter; tests should service through the genuine private admission API rather than hand-writing counters.

## Pending artifact review gates

1. Actual real-provider emission controls and baseline causal failures must distinguish upstream valid OrderedDict/_metadata from owner loss. Constructor/import failures do not qualify.
2. Real RND and adaptive owned restore/continuation must compare actual native values and tail, positive learning, private RNG continuation and ambient streams, with strict type/order/recursive metadata equality in an independent oracle.
3. Separate validator candidate and transport mutations, including metadata presence/deletion, recursive values and OrderedDict order, must fail for the intended purity guard with receiver state preserved. Portable numeric nested metadata ownership may be checked through copying without assuming arbitrary metadata is retained by Torch native load.
4. Callback result and snapshot mutations must not alias live data; prepare input mutation after return must not change installed data. A successful prepare/install and stale/reused/different-destination handles need revision-aware ordering.
5. Production repair must remain limited to WS preservation/equality, preserve generic mapping and existing ownership/RNG/error/quarantine behavior, and avoid unsupported custom-type guarantees.

Factual gaps: no actual new test artifact or pinned repaired source has been supplied; no independent RED/GREEN execution is authorized yet. Adaptive implementation is excluded; its public/data capsule and real runtime controls must establish wrapper-specific behavior. CUDA remains unqualified. Await root's exact hash/diff and later independent pinned-runtime baton without polling for absent files.

## Authored SPEC/QUALITY review — R0

Reviewed actual 313-line new test and matching authored patch, plus writer report, at supplied test SHA256 3b1c6408835b43239afa920eca51d03ac82c0219caf3d7b01fc347c934ef1dbb / frozen tree 7b94a1d32a51616e3012109d013cddd7670260f7. Runtime remains unauthorized and unperformed by reviewer.

Disposition: suitable for root collection, two actual-factory prerequisite controls, then intended causal RED. No blocking authored defect found by static review. This is not production approval or runtime acceptance.

- Actual factory, resolved typed policy, descriptor and private RNG are used. Direct source is constructed under model_init; learning uses genuine private admission position 3 then 4, positive LR, batch 2, three initial rows and a one-row tail. Initial control asserts changed predictor, unchanged target, finite gradients, exact tail, actual emitted metadata and pure actual validation. Adaptive learning intentionally exercises its actual nested RND provider while envelope validation/load targets the outer provider.
- Callback witness is primitive data collected before the owner copier, so its OrderedDict evidence is not circular. Both callback and snapshot causal assertions explicitly require native OrderedDict. The independent oracle checks exact type, mapping sequence, metadata presence/content, numeric values and tensor geometry/device/dtype. It does not call production equality.
- Restore input comes from direct actual provider, preserving the defect trigger. Preparation invokes genuine validation and load, installation is followed by full envelope equality, source/input mutation isolation and another real learning update with exact native/RNG/next-update gradients. No residual pre-load gradient promise is asserted.
- Transport order-only mutation and candidate metadata-only mutation occur after genuine validation; a reached witness and exact expected purity error prevent an unrelated constructor/validator error from qualifying. Original payload and healthy receiver envelope remain exact on rejection. No raw backend escapes an owner callback.
- Portable nested numeric metadata tests recursive copying and detachment in both input/output directions, without asking native Torch load to preserve a custom format.
- Destination baseline snapshots precede prepare; install happens before further observation. Separate pure-snapshot stale-handle coverage and consumed-handle rejection respect revision custody. Ambient Python/NumPy/Torch streams are checked around test execution and exceptions.

Bounded evidence limits, to retain in final claims: the new tests do not independently enumerate transported-metadata deletion/presence mutation, candidate order mutation, cross-destination handles, or mutation of input specifically between prepare and install. Existing owner suites and fixed-source review remain necessary; these omissions do not block causal RED for this narrow codec repair. Continuation learning does not deliberately consume service randomness, so equal private RNG snapshots establish state retention here, not a new stochastic-service qualification. Arbitrary custom mapping subclasses/native formats and CUDA are unqualified.

Authored inventory is seven test functions / expected sixteen parameterized nodes. Writer's baseline prediction of four passes and twelve failures is plausible (two direct controls plus two stale-handle controls), but only root's recorded run can establish it. Keep fixture validity and causal failure assessment separate. Await pinned repaired WS artifact and runtime baton after root evidence.

## Fixed-source SPEC/QUALITY review — R1

Root reports R0 collection16, real-factory controls2 PASS, then full16 with4 PASS/12 causal RED (8 kind/metadata-loss assertions,4 impurity DID NOT RAISE), zero fixture errors; these are attributed root results, not reviewer execution.

Reviewed R0→R1 production patch and actual WS copier/equality at frozen tree 3c0052b80d24fc6387a1e186e485b808dd3bf3de. WS883 SHA256 cb8a7fd9f27c73537ec3f18f37b6cd5a3d88ca23c281b76376cece8be5f9dfb1; actual new test remains313 SHA256 3b1c6408835b43239afa920eca51d03ac82c0219caf3d7b01fc347c934ef1dbb. Writer report's R1 append read; earlier phase history retained.

Static disposition: no blocking source/spec/quality defect found in this bounded repair. The added OrderedDict branch precedes generic Mapping normalization, recursively owns keys/items and optional metadata, and retains insertion order. Tensor and NumPy copying still takes precedence inside entries and metadata; recursive Tensor data remains detached. OrderedDict equality follows the existing exact-type gate and checks ordered key sequence, metadata presence and recursively equal contents before values. Missing-versus-present metadata differs even when metadata is empty, and nested OrderedDict metadata receives the same order-sensitive comparison. Both candidate and transported-state purity comparisons use this repair without relaxing the subsequent exact native load check.

The patch changes no factory, native validation/load, RNG activation/restoration, lifecycle revision, opaque handle, quarantine or generic Mapping/list/tuple/dataclass branch. It adds no compatibility fallback and no native gradient promise. Exact standard OrderedDict and portable acyclic nested metadata are the qualified target; arbitrary subclasses, self-referential custom metadata and custom native loaders gain no new claim. No broader redesign is necessary for the evidenced gap.

Source approval is limited to the inspected R1 patch design. Runtime acceptance remains pending root GREEN and explicitly authorized independent pinned execution, followed by prior-owner/static coverage and coherent main integration. New focused16 alone cannot establish those downstream gates. Reviewer has run no runtime/probe and made no production/test edit.

## Independent pinned runtime and final bounded review — R1

Following root's explicit positive gate and runtime baton, reviewer executed the unchanged locked runner with positional wave31-r1-independent-spec.json in /workspace/hamlet, with exactly one pytest worker. Actual child exit_code was0 (not merely wrapper success). Only then reviewer invoked unchanged verify_bac_run.py with the same pinned spec.

Independent outcome:16 passed,0 skipped/xfail/xpass/warnings; wall13.91125226020813 seconds. Frozen candidate3c0052b80d24fc6387a1e186e485b808dd3bf3de, basea7c4cd0b19c410114aaabdd9284888fef159e84e; manifest SHA256 b72976dd4156fd043f690fbd2d5f1368aaaf3ea51147e003a3acf01fc9d2e51a; harness SHA256 180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791. Actual log /workspace/bac-review-2026-11-01/qualification/wave31-r1-independent/independent.log SHA256 fbcf80b464eacbf3821ce1bd12142472867fc9c216475c1d6ab18f16b67f1120.

Verifier returned0 and confirmed354 source guards,573 config digests,13 protected artifacts,2 process identities,14 worktree registry records/1 available worktree; source/index/import/threads/fixture custody PASS. No reviewer source/test/index changes, extra implementations, custom probes or duplicate broad tests.

Final bounded disposition: approve the inspected narrow WS preservation/equality design and actual fixed-source SPEC/QUALITY, supported by independently passing the sixteen real-provider focused tests at this exact candidate. Existing attributed R0 RED and this independent R1 GREEN support the causal repair without weakening metadata/equality or changing native gradient/provider promises. Prior owner suites, coherent main CP/BANK integration and remaining static qualification are separately owed to root; this result does not claim them, CUDA qualification, package release or whole-BAC completion. Earlier authored limitations remain as documented rather than being silently upgraded by this run.
