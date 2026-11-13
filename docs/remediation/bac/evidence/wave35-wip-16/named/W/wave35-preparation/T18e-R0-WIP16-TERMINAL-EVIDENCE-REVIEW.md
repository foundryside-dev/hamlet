# WIP16 R82–R85 independent terminal evidence review

2026-11-13. **NOT READY: one material metadata-schema gap requires correction and a fresh frozen subject.** No other material gap was established in this finite review. This is evidence readiness, not a new implementation review or whole BAC/CUDA/CI acceptance.

Producer: `root + bac_astra_replay_child_verifier`.
Reviewer: `bac_astra_replay_fix_a_review; gpt-6-astra medium` (orchestration label).

## Exact reviewed subject

Paths are relative to `/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades` (W).

- Subject `evidence-management/wip16-r85-qualification-subject-v1.json`: SHA256 `b348254754624c4a9782c89072d3daebef016b191b5cc257db42499a160d2c0d`.
- Input `evidence-management/wip16-r85-terminal-review-input-v1.json`: SHA256 `23b035938c7db22766ad5fbe357ccc90cf947035252366b9ab1c5accb09fa512`, 287239 bytes.
- Contract `wave35/r85-checkpoint-contract.json`: SHA256 `ac4e1abaef775cdf7b2b9e0d97dafef97a7c918a96178bd39fee56ef38b4e6f6`.
- Candidate manifest `wave35/r85-candidate.json`: SHA256 `9df6603bae0b0ebeedecf199e222cacddb4de501e1242c148117f9c85d678246`.
- Candidate tree `e1d5bf0e123cc04eca943a34125bdfbd1e6fc42a`; base `29d0204a70b6eef0017b3cee638812e2cc5c7899`.

All four authority hashes match actual files. Four required component receipts match the contract's exact references. The subject accurately binds finite R82–R85 scope and retained package accounting.

## Material finding W16-E1

All seven top-level `dependencies` objects omit required `role`: `run_bac_packet_checks_locked.py`, `verify_bac_run.py`, `verify_bac_failed_run.py`, `verify_bac_static_run.py`, `verify_bac_replay_spawn_identity.py`, `capture_wave14_round.py`, and `bac_source_identity.py`.

Root identified the schema requirement during adoption and reported that final `validate_receipt` requires `role` alongside `required_by`; I independently confirmed its absence in every dependency object. Their actual hashes and required-by relationships are present and consistent, but that does not supply the missing classification. The draft-only selector result bypasses final validation and cannot establish readiness of this representation.

Required correction: author a new input assigning truthful nonempty dependency roles, preserve frozen v1/history, freeze a new subject, and obtain a scoped comparison/review before final sealing. No application, helper implementation, guard relaxation or runtime rerun is indicated by this gap. This review did not execute or inspect the selector implementation and does not invent an actual final-validator failure or PASS.

## Independent checks completed

There are 35 distinct check entries: 30 completed commands (27 PASSED, three FAILED) and five UNRUN specifications. The observed qualification-root interval top-level inventory exactly equals 57 entries. Actual executed-attempt descendant memberships agree with the declared lists. All 216 unique explicit-root references checked against actual sizes/SHA256 match; rootless candidate and descendant file references also match. Source, helper, synthetic-test and patch bytes were hashed only; their bodies were not read.

All 35 actual specification job argument vectors agree with the corresponding executed/planned commands. All 30 actual result commands, exit codes, positive elapsed durations and candidate/base/manifest bindings agree with declarations. Runtime log summaries substantiate the reported outcomes. The required helper references have matching top-level entries and required-by relationships; the seven missing role fields are the separate finding above. Five UNRUN records retain explicit reasons and null execution facts; four are unused generated curriculum templates, and the R82 child was explicitly withheld pending prerequisites.

Six child mappings agree with actual witness spec/result hashes and candidate/manifest identities: R83 child60791/parent60759; R84 independent66590/66511; R84 recurrent65662/65605; R84 retained replay65637/65603; R85 recurrent69160/69045; R85 retained replay69171/69023. Actual child PPIDs match their parents. I compared raw child identity and parent observations: Process PID and queued PID equal the child PID, parent matches, exit0/qualified/message match, and controller/child/observation hashes agree with the witness. Every witness records current verifier SHA256 `390c3a52837e88a716df15ff496967cb313f1fd63d892ca1eb0b4e48096e9146`. Literal `attempt_id` is absent from original witnesses; the local mapping is supported by actual spec/result/job/PID/source linkage and does not fabricate that field. Generic verifier selfhash and absent absolute UTC limitations remain explicitly disclosed.

R82 records 39 passing and 14 failing cases among 53 executed: 12 genuine mutable-DTO failures plus two fixture prerequisites. R83 records 23 selected ordinary cases plus one child PASS, not an invented full55 rerun. R84 root109 replay and independent55 recurrent overlap; the owner gate stopped after one PASS/one FAIL, leaving47 unexecuted. R85 root158 distinct cases comprise109 replay plus49 owner. Its separate first-node run and independent49 overlap the owner suite. None of those repeats increases unique coverage. R84 global Ruff/Black/defaults600 and types remain historical source-bound results, not R85 global reruns; R85 changed-owner Ruff/Black pass.

The wrong-month R83 verifier-path diagnostic remains recorded as failure before spec read, followed by a corrected invocation; it is not application execution. Prior post-WIP15 CI observations remain tied to their actual revision and observation time. No new CI success is inferred.

## Tool, source archive and document closure

Current child-verifier dependency bytes, synthetic-test bytes, independent SOL review and root synthetic observation are retained. The independent review qualifies the bounded role extension and actual36 synthetic tests; synthetic verification is not application acceptance. Actual child evidence was separately inspected above. Earlier helper bytes remain historical catalog evidence.

The four source-delta patches and manifest SHA256 `ea38108c0c5b5350afab50432d936be8f33053fdde4521e5a569fbe3495cfed9` are retained DATA. Their selected reference hashes/sizes match. I inspected manifest metadata and limitations only, without reading patch contents, reconstructing trees or asserting remote availability. Candidate source SHA256 assertions are correctly distinguished from independently recorded Git blob metadata.

The four-document application record SHA256 `0a9b07ed66ce0b8c3cb10e41f8e93b8f7d7d865d58d693fc88fb2016e1814ea2` binds actual README, STATUS, shared replay and recurrent replay contract bytes and the independent document reviews. Source-level B and owner approvals are supplied by named distinct reviews, not new source inspection here. The latest STATUS prose correctly distinguishes repaired R85 owner coverage from historical R84 failure and keeps B6/hardware/external integration open. Its protected execution hash `7dba8e1d95f734ab9dfa3ad53e8646cc661c86f44eefca1687f558b5f52f00eb` and publication hash `cbd6b402fff559066cdba196afc463e826c557140043e924e03917617e950b9c` are explicitly separate. Final publication source-equivalence proof remains root's task. Historical report/child-capsule snapshots and draft closure are retained rather than silently rewritten.

## Independence and boundary

I did not produce recurrent B, owner repair, the terminal proposal or root adoption. This is a fresh metadata/prose review distinct from the drafter and root. My earlier A source/execution and WIP15 evidence reviews do not substitute for this task. No new source body, application/tool runtime, verifier, import, Git/index/remote operation, checkout/copy, deletion or delegation occurred; only this review and its attestation were written.

Package accounting remains28 qualified/38 remaining/66 total. B6 CUDA capability/lifecycle/completion and real hardware, external BANK/ENV/POP/native/runner caller migration/integration, global typing/full repository/coverage/slow/learning/finalCI and fresh programme reviews remain required.

After W16-E1 is repaired and a new subject approved, root must create the final receipt with only status/review_subject/reviews additions, verify equivalence and complete real final selection, assembly, publication and exact remote/CI checks. Draft selection, source component approvals and this blocked v1 review do not authorize claiming those operations passed.
