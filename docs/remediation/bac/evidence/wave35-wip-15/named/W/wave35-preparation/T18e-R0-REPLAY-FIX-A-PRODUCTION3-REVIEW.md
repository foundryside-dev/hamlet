# Replay fix A production3 — scoped source review and independent execution

2026-11-13. **SPEC and QUALITY: APPROVED for the bounded Fix-A B1/B2/B5 and shared/flat/PER B4 slice.** A-P1 UP047 and A-P2 UP049 are addressed. No new scoped material defect was found. The reviewer independently executed the authorized exact-source checks:53 ordinary cases PASS and isolated poison1 PASS. This is bounded producer approval, not whole-replay, CUDA, R0/B1 or programme acceptance.

## Source and review custody

R81 candidate `4bcb26ec56bc2664949baab7d6b14e3c1da76b01`, base `678513c7540a61114d59a17d1b1e0eb8a06ce0a2`, manifest SHA256 `f16cff139bc7caeb8e4dab7adf995ad5f52f16ca7b058c710bc41f428b8fa80e`. Measured/hashed before changed-source inspection; same five permitted whole bodies,3735 lines, below planned4471 and hard5000:

| Body relative to /workspace/hamlet | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/training/replay_contract.py |374|8de53fc6814a16bafb703728ed396d7b9a1298afdb415be4ec8d1d85ac1502a1|
| src/townlet/training/replay_buffer.py |728|817495558b45a51ba5df3751f83d1985135e23d9dfe6f827e3e323c45df01214|
| src/townlet/training/prioritized_replay_buffer.py |1164|b989a8f153cf6a2686140efcfb6ce1d4914f4379785c2c094e1cc5d1142033b8|
| tests/test_townlet/regressions/bac/test_replay_rng_custody.py |1098|5870d5315dd6f975f6e9513a492ba08f84671576f18e70f62795b122e13eabd7|
| src/townlet/exploration/rng_custody.py |371|9d6cd6fcfe62d8e53bda1e6ce7b34a89454ccc88373b5ec4cd072fe004ad66fb|

Report SHA256 `80ff7071a1dd3c3c60dba2ce4c07ab10594f1df95c6b88546b7a055a5df65b0b`; production3 diff SHA256 `ee3ff083b160d8b1a9428471d0c812cb90c4a7cdcf2000a433cbe6357aebe323`. Earlier reviews remain separate immutable artifacts, including production1 `eedd38a65a53e6a8285928099b6ac7812cb12e29312ec1c6123f810bc84f6ea7` and production2 `79f839417078a95a0fc8337b7ede93bf9862ef5ae11f2a92fb0b55440dd82946`.

This round inspected only the scoped naming diff and affected current contract context within the previously reviewed five-body packet, the report, exact execution specs and evidence. No sixth helper/recurrent/caller implementation body, harness source, source edit, direct Git/index command, new tests/probes/mocks, delegation, branch/worktree or source copy. Only this review artifact was written directly. The two specifically authorized public harness commands executed real application tests and their intrinsic source/index checks; no independent direct verifier or other runtime command was run by this reviewer.

## Source disposition

A-P2 is addressed by consistent function-local type-parameter renaming from `_Owner/_Result/_Arguments` to `Owner/Result/Arguments` throughout all four decorator declarations and their annotations. Modern generic syntax remains, so A-P1 remains closed. The owner bound, ParamSpec arguments, read/mutation/sample result preservation and preparation's explicit PreparedReplay transformation are intact. `_required_lineage`, forwarded arguments, domain-before-owner admission, wrapped methods and issuance behavior are unchanged. There is no suppression, Any erasure, default lineage or extra runtime branch. No new defect was found in the narrow diff.

The actual R79 source assessment remains applicable to unchanged production bodies and unchanged behavior: B1 owns DTO data and reruns complete current-target/content validation before materialization/issuance; B2 binds identity/revision/token/material in the issuer registry with no caller payload surface; B5 preserves required typed arguments and actual prepared results. Real archive/history and current formats/modes remain supported under their existing validators. Final owner/current-token authentication follows staging and immediately precedes publication; successful use consumes authority, uncertain partial publication quarantines. Independent R81 execution below rechecks those claims at final bytes, rather than borrowing R79 PASS.

The adversarial controls exercise stale target DTOs, mutated validation tensors/arrays, fabricated/copied/reinitialized identities, actual other-issued material substitution, same-held authentic nesting and intervening sibling/owner work, real tensor/archive/Generator staging faults, actual partial assignment quarantine, retained-input/material alias isolation and terminal poison refusal/nonhealing. Their existing full-state, fresh-positive-after-failed-admission, fault cleanup and child identity assertions are retained. Passing already-correct B4 controls does not require artificial RED; earlier R77 genuine causal failures remain preserved history.

## Independent exact-source execution

Before launch both designated output directories were checked and absent. Each exact authorized command was invoked once by this reviewer, in parallel with one worker apiece; both completed exit0 and their execution sessions closed:

```text
python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave35-r81-independent-replay-current-spec.json
python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave35-r81-independent-replay-poison-spec.json
```

The first spec selects the regression file while explicitly deselecting its isolated poison node; the second selects exactly that node. Both use the workspace venv pytest with `--no-cov -p no:cacheprovider -p no:benchmark -p bac_source_identity -q`. The harness source was not read. Result records bind the candidate/base/manifest above and harness SHA256 `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`.

All paths below are relative to `/workspace/bac-review-2026-11-01/qualification/`:

| Receipt | Actual independent outcome | SHA256 |
| --- | --- | --- |
| wave35-r81-independent-replay-current/replay-current.log |53 PASS,1 deselected; harness6.732235908508301s, pytest2.46s|4328d83a465a579ed7e322f964b64c4c80140498fa8f654a095f3bdce58d8e78|
| wave35-r81-independent-replay-current/replay-current-result.json |exit0, exact candidate and command|3823e43ba640ab7ad48c3c84bc405624e3f347908bc8cd19871d61cddd6af99f|
| wave35-r81-independent-replay-poison/replay-poison.log |isolated1 PASS; harness8.101341724395752s, pytest4.07s|3628934394c5658b633f46c14b3950edd42447f90eacf40d1592a7bcf7f80144|
| wave35-r81-independent-replay-poison/replay-poison-result.json |exit0, exact candidate and command|f099ed185cf5750ae9ab739929e7d6afe66ec3e5654d42da6e8e7f9710f77c00|

The logs were read after actual completion and hashes checked against harness receipts. The current run collects54 and selects53; poison separately collects1. These disjoint selections cover54 existing cases once. Repeating root's same tests independently is independent execution evidence, not new unique coverage or an additional54 controls.

Read actual child-owned identity and parent observation: child/process/queued PID42369, actual child PPID and parent PID42298, role `replay_poison`, exact success message, qualified true, exit0, matching R81 manifest/tree/base and actual replay import paths beneath `/workspace/hamlet/src`. Child records debug true, intra-op1, inter-op5. This inspection does not substitute for root's full serial source/process/child verifier. The child proves public-poison consumer refusal under the current CPU profile, not CUDA or a restoration-failure scenario.

## Root static evidence and remaining gates

Root reports collection54, global Ruff PASS, owned Black PASS, owned-four mypy PASS including recurrent, and all-three-family public PreparedReplay assert_type PASS, with full815-source custody verified. Reviewer inspected their actual success logs:

| Relative log | SHA256 |
| --- | --- |
| wave35-r81-static/ruff-global.log |82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18|
| wave35-r81-static/black-owned.log |26a5fd9505f2b5608a20c4fed4b4c4795e0783d03b72ade02a6af34dae8ad086|
| wave35-r81-types/owned-mypy.log |71144743c83babea384888a735db0c4daba3d4d7b7942b6839984bd5c21b52bb|
| wave35-r81-types/public-types.log |5d4b6d285b77932e3d08212c3b4974d0a803f98ec60408ac6ccf6a063fa6c19e|

R79 actual missing-lineage diagnostics remain source-bound evidence that corrected producer typing exposes real unmigrated callers; this approval does not claim those callers were fixed. Global defaults601>600 and recurrent-only formatting remain separately owned required work, not a waiver. Recurrent B3 scratch classification and recurrent-specific B4, B6 ordinary lazy/unindexed CUDA capability and device-completion/owner lifetime, caller migration, broader suites and final fresh design/implementation programme reviews remain mandatory. No whole-package completion or CUDA claim; accounting stays28 qualified/38 remaining/66 total.

## Final custody closure

Before seal, root completed serial custody verification for all four root/independent runtime checks:815/573/13/14 inventory and MAIN1 PASS. Both strong actual-child verifiers PASS: root child42153/parent-PPID42083; independent child42369/parent-PPID42298. Root confirms all execution/verifier sessions CLOSED and source/index unchanged at R81; collection/static/types are likewise verified. These verifier results are root-attributed, distinct from this reviewer's actual two harness executions and direct receipt inspection. Root's53+1 and independent53+1 are repeated evidence for the same54 controls, never summed as108 unique tests. The bounded SPEC/QUALITY approval above is therefore sealed with exact-source independent execution and completed custody; all explicitly remaining slices/programme gates stand.

The original B1 finding also requires a bounded assessment/control of recurrent returned mutable DTOs under the same issuance rule. A closes the confirmed flat/PER B1 defect only. Shared identity-handle repair and passing retained recurrent controls do not establish recurrent malformed-DTO rejection/preservation. That retained interface qualification belongs to next slice B alongside recurrent B3/B4/defaults/style, followed by the separately required B6 design; it is not a new finding against fixed A.
