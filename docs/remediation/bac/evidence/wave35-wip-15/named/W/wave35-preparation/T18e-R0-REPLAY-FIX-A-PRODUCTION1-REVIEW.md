# Replay fix A production1 — independent SPEC and QUALITY review

2026-11-13. **SPEC: APPROVED for the bounded B1/B2/B5 and flat/PER/shared B4 repair. QUALITY: CHANGES REQUIRED.** The actual repairs satisfy the scoped behavior and typing requirements, with all54 retained cases passing at R79. One local quality finding remains: four Ruff UP047 errors in the new generic decorators. This is not whole-replay, R0/B1 or programme acceptance; recurrent and CUDA scope remains required.

## Exact reviewed source and boundary

Root's R79 candidate is `b63744a51ce4844ed6f35180d2a2e8e664407e78`, base `678513c7540a61114d59a17d1b1e0eb8a06ce0a2`, manifest SHA256 `b35815c3065890eadfb7f394c588a7b6b0b8cceddbb25095a928316077592dfd`. Reviewed actual current source changes and their retained whole-body context against the original brief/findings, prior tests/fixture reviews and updated author report. Production1 diff SHA256 `046fa77c44052eca880673bbd5d0d24553d7c7cda02b0fbd22f5d8dcd749d143`; report SHA256 `c4cdf49647b050101d596d1313ce7f1bdc0b896ae045467a68c279e0968c7422`.

Measured and hashed before changed-source reads; exactly the same five permitted whole bodies,3740 lines, within planned4471 and hard5000:

| Body relative to /workspace/hamlet | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/training/replay_contract.py |379|58f641301c6398bee4048fae8c4802850e6717e15e36f9720caaf9034eb7bf94|
| src/townlet/training/replay_buffer.py |728|817495558b45a51ba5df3751f83d1985135e23d9dfe6f827e3e323c45df01214|
| src/townlet/training/prioritized_replay_buffer.py |1164|b989a8f153cf6a2686140efcfb6ce1d4914f4379785c2c094e1cc5d1142033b8|
| tests/test_townlet/regressions/bac/test_replay_rng_custody.py |1098|5870d5315dd6f975f6e9513a492ba08f84671576f18e70f62795b122e13eabd7|
| src/townlet/exploration/rng_custody.py |371|9d6cd6fcfe62d8e53bda1e6ce7b34a89454ccc88373b5ec4cd072fe004ad66fb|

No sixth recurrent/helper/caller source body, source edit, application import/runtime, compiler, formatter, Git/index action, delegation, branch/worktree or copied source. Only this review artifact was written. Actual logs/results were inspected as root-owned evidence. Caller diagnostics below are evidence from the type checker, not an assertion that this reviewer read those callers. Recurrent signatures and helper behavior retain their source-qualified supplier boundaries.

## Material finding A-P1 — P2: new decorator definitions fail required Ruff gate

`replay_contract.py:134,145,156,168`: `replay_read`, `replay_mutation`, `replay_sample`, `replay_prepare` use module-level TypeVar/ParamSpec generic declarations that trigger four UP047 errors under the project's current Python/Ruff policy. The actual R79 global Ruff log contains exactly these four errors. This is introduced by the owned B5 repair, not the separately owned recurrent formatter/default debt.

Use the supported modern function type-parameter syntax, retaining the ReplayCustody owner bound, complete ParamSpec arguments and result preservation/transformation. Remove now-unused typing declarations/imports as appropriate. Do not suppress UP047, weaken the required public lineage, restore Any, add defaults or change runtime admission. Recheck the shared contract lint/type behavior and its affected runtime controls at exact new bytes before quality approval. No additional behavioral defect was found in this review.

## Source assessment of repaired requirements

**B1 addressed:** flat620 and PER1030 now reconstruct an owned representation of the DTO data and rerun the actual complete serialized validators before materialization and issuance. Every active tensor, component-presence/legality field and archive record is included; PER additionally preserves priorities, IDs/counter, beta and encoded sampler configuration/engine/state. Legacy DTOs clone their complete original payload and continue through the existing legacy validation/archive branch. The original expected observation width is retained, and validators independently check current allocated observation/action geometry. Owner configuration supplies the current destination constraints. Domain then owner exclusion encloses snapshot, validation, allocation/copy/merge and token issuance. Invalid mutable DTO bytes and managed stale-width schedules can no longer acquire a fresh prepared identity merely by passing the DTO class check.

The implementation reuses the existing validators rather than maintaining a weaker parallel content check. It leaves valid data DTO materialization available; it adds neither a reject-all rule nor a new public lineage default. Current flat/PER payloads and genuine old archives remain exercised by fixed-source controls. PER captured5's existing validated adapter data is representable as current6 with its adapter origin, external sampler descriptor and generated IDs; the existing validator accepts that representation. Current/history mode decisions and archive retention are unchanged. No sampler selection, draw schedule, seed or CUDA behavior was altered. The extra owned copies/validation are finite correctness work; arbitrary external object protocols and raw alias concurrency retain the existing supported-profile limits.

**B2 addressed:** PreparedReplay now has only a weak-reference slot, with public construction/reinitialization and copying/serialization refused. The actual issuer creates an identity using object.__new__ and keeps revision, current token and material together in its private weak identity record. Payload lookup uses that record; the caller-held identity cannot replace material through a payload constructor or slot. Counterfeit identities lack issuance records. The real producer seam remains usable by the finite tests to retain material, without becoming a public payload accessor. Install still stages independent storage/archive/array/Generator copies, validates owner revision and core currency immediately before assignment, consumes a successful identity once, and quarantines uncertain assignment failure. No final check was moved ahead of fallible staging.

**B5 addressed in behavior/type contract, subject to A-P1 style repair:** Concatenate plus owner-bounded TypeVar and ParamSpec preserve the method arguments, including required keyword lineage. Read/mutation/sample preserve the result type. Preparation explicitly changes the internal material result to public PreparedReplay while preserving all arguments. This is a real declared typed transformation, not Callable[..., Any], a cast or suppression. `_required_lineage` requires the supplied keyword and forwards it unchanged; actual sole-domain authentication still rejects forged/expired operations before owner work. There is no default/implicit lineage or second domain. Source inspection establishes the PreparedReplay return transformation; no fake caller probe is necessary or claimed. Runtime wraps metadata continues to expose the internal declaration, as the author explicitly distinguishes from the corrected static API.

The arrangement applies to frozen recurrent decorators without requiring an immediate recurrent declaration edit. Root's owned-four mypy result includes recurrent, and its actual external missing prepare/sample lineage diagnostics demonstrate that the prior erased call boundary is now exposed. This establishes detection, not migration of those callers.

**B4 retained and now GREEN within this slice:** formatting-only test changes preserve all reviewed assertions and fixture repairs. Real same-held nesting succeeds; sibling sampling and managed owner mutation invalidate. Full transport plus physical state, PER IDs/reverse mapping and persistent sampler state remain observed. Tensor/archive and PER Generator staging faults delegate real operations before raising, preserve complete live state and allow fresh healthy use. Assignment faults occur after real observation publication and establish sample/prepare/install/clear/serialization quarantine. Input and retained candidate array/tensor/Generator mutations leave installed state independent. Failed admitted installs correctly use fresh positive preparation rather than assuming old currency survives. These existing-correct branches need no artificial RED.

Expanded poison remains isolated in the existing child, issues authentic handles before real poison, and checks sample/new prepare/old install refusal plus nonhealing local clear. Role, message, actual import/PID/PPID pairing, manifest and exclusive observation protocol are unchanged. Status remains diagnostic outside owner exclusion. Child consumer refusal is not a restoration-failure witness or CUDA qualification.

## Actual R79 execution and remaining static results

Root confirms all execution/verifier sessions CLOSED, full815/573/13/14 inventory and MAIN1 custody verified, plus child40507/parent40434 actual PPID pairing. These complete-custody results are attributed to root. Reviewer inspected the actual logs and runtime result JSON under `/workspace/bac-review-2026-11-01/qualification/`.

| Relative log | Actual outcome | SHA256 |
| --- | --- | --- |
| wave35-r79-replay-current/replay-current.log |53 PASS, poison explicitly deselected;5.932811737s harness,2.37s pytest|3ac1ae6313cf5569a806d46dcfaa007c659bf73b0227185f55b9d78a4acca26d|
| wave35-r79-replay-poison/replay-poison.log |isolated1 PASS;6.712133884s harness,3.06s pytest|c5bd091cf75499010d6f7fb85dadf27042781fef167f21401eed2d5112ff0efb|
| wave35-r79-types/owned-mypy.log |PASS,4 producer source files including recurrent|71144743c83babea384888a735db0c4daba3d4d7b7942b6839984bd5c21b52bb|
| wave35-r79-types/mypy.log |FAIL15:oracle6 plus POP9;198 files checked|97b0acc6db53ae2cfe9037794211464b7dc01c75e6909adcf3c440a4dfa5a6e7|
| wave35-r79-static/ruff-global.log |FAIL4, all A-P1 UP047|1f200ab194ce12161ea21ee812136a7216e6a192b0768ba6560e398b6f3368d1|
| wave35-r79-static/black-global.log |only recurrent would reformat;734 others unchanged|8d3d3dfc1691dffbd3d6e0e7090f4b6988e7c9448062b2db34d039fcaa0c90b0|
| wave35-r79-static/no-defaults.log |FAIL ratchet601>600, no suppression/ceiling change|bd7169859432f6c9e1bc6516704fded9f05e2e606328c05f954acaf15da575d7|
| wave35-r79-static/expression-doc.log |PASS,48 functions current|67392c0159789f0e64e7422db75ae98c3d2ba12578f4628823c9fa575fb58cdf|

Collection54 and disjoint53+1 cover the packet once. The old R77 fourteen causal failures now pass at repaired bytes; R77 failures and R78 fixture evidence remain historical, not relabeled. Global mypy now explicitly diagnoses POP698/701 prepare_serialized,699 prepare_archived_import and800 sample_batch for all three replay families; along with three load_prepared failures this gives POP9 rather than the previously visible3. The six newly visible missing-lineage errors are the expected result of correcting producer type erasure. External caller migration remains mandatory. Root attributes owned mypy26.7047s and global25.6257s.

## Disposition

Fix A-P1 before final bounded QUALITY approval. B1/B2/B5 behavior and flat/PER/shared B4 have source and exact-run evidence; no other scoped material defect was found. Global defaults601>600 and recurrent-only Black remain required next-packet work, with the actual recurrent ASG002 provenance supplied by root rather than a sixth source read. B3 scratch classification and recurrent-specific B4, B6 ordinary lazy/unindexed CUDA capability and device-completion/owner-lock lifetime, caller migration, broader suites and final fresh design/implementation reviews remain open. This review neither waives those requirements nor replaces final programme reviews. Accounting remains28 qualified/38 remaining/66 total.
