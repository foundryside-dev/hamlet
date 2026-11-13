# Invocation outcome strict verifier preparation

2026-11-13. Author `/root/bac_invocation_verifier_prep`. **PREPARATION ONLY; NO TOOL WRITE OR EXECUTION GRANT.** The finite extension is mapped below, but is not implementation-ready until actual application child tests and the parity-pair interface are frozen. All new roles, cases, nodes, artifacts and invocation fork actions remain proposed. No new application or synthetic result is claimed.

## Scope and exact inputs

R = `/workspace/hamlet`; W = `R/.superpowers/sdd/2026-11-01-bac-remediation-upgrades`; E = `W/evidence-management`; P = `W/wave35-preparation`; Q = `/workspace/bac-review-2026-11-01/qualification`.

Read repository AGENTS.md and `docs/remediation/bac/EVIDENCE-PROCESS.md`. Ancestor/nested AGENTS metadata searches found no additional applicable file. Read the writing-plans and verification-before-completion skills; their workflow is bounded by root's explicit preparation-only grant. The using-superpowers skill explicitly excludes dispatched subagents. No tracker claim, index refresh, application import, test collection, verifier execution, source/test/tool edit, Git mutation, branch/worktree/copy, delegation or publication occurred. This document is the sole authored artifact.

Only these two implementation bodies were read, in full:

| Body | Lines | SHA256 |
| --- | ---: | --- |
| `Q/verify_bac_replay_spawn_identity.py` | 581 | `8639eae953abe0961a4d4af941c15fbf4d3c85b9bd342d4409158a629e0eae7e` |
| `E/test_replay_spawn_verifier.py` | 989 | `36ed3c3ae1d4b0a7c5835ff95ed705a30a8ca4b548826b406eb9957d8cf4c14c` |

Total admitted implementation read: **1570 lines / two bodies**. No application core/test/bootstrap/helper body or diff was read. Source implementation facts below are attributed to the supplied review/report, not independently re-derived from application code.

| Prose/metadata input | SHA256 |
| --- | --- |
| `P/T18e-R0-CUDA-INVOCATION-OUTCOME-QUALIFICATION-PROTOCOL.md` | `d2b9d7fdfe5b9bb3db796830608aeb74a0de2ee0955f19878d495a5c997580d9` |
| `P/T18e-R0-CUDA-INVOCATION-OUTCOME-QUALIFICATION-PROTOCOL-REVIEW.md` | `ace6b4ea9acaca1d93f128901f686dc1332754cdd16bc0239ffdbc16a4bf8863` |
| `W/wave35/r106-invocation-qualification-plan-adoption.json` | `703a39904220d2717d588040200d0b9efab783542380b3d1af912e162118e458` |
| `P/T18e-R0-CUDA-INVOCATION-OUTCOME-IMPLEMENTATION-REVIEW.md` | `841eb6bc15a15161a970fb306d427f36c6a3b167d9c73fc73e16ab22b0a8789f` |
| `P/T18e-R0-CUDA-INVOCATION-OUTCOME-IMPLEMENTATION-REPORT.md` | `0f3453e817e4af6fb2167354e3fa80f19243777e227ce2cf104cab138c423116` |

All hashes/line counts in these two tables were freshly checked without running the bodies. Root's adoption approves the plan and application reservation core1250/test2350/total3600/two files, with hard5000/five files unchanged; its status expressly grants no source/test/verifier write. This is not a tooling budget grant.

## Existing extension points and preserved contracts

The current verifier has a closed `CUDA_CASES` tuple at lines70–81 and derives exact registered job/role/message/node configurations at82–91. There is no generic CUDA role or prefix admission. `check_bindings` at424 checks exact job argv, workers exactly integer1, result/log/source identity and positive finite duration. `verify(spec_path, job_index=0)` at457 verifies one selected job and exclusively writes its receipt; the CLI accepts only `SPEC [JOB_INDEX]`.

`CUDA_CHILD_FIELDS` at122 and the CUDA observation branch at484–488 use exact key sets. CUDA observations currently contain `OBSERVATION_FIELDS` plus `queued_ppid`; no optional unknown field exists. Process/queue PID/PPID, success, manifest, module paths/source inventory, controller/child roles, Torch profile, harness bytes, repository state and exclusive receipt destination checks remain prerequisites. Reuse these checks for the six exact future roles, without relaxing replay, recurrent, producer or existing CUDA observations.

`FORK_ACTIONS` at159 currently requires exactly admission/local. `check_fork_guards` at166 requires exact per-kind file inventories, exact identity/observation schemas, action/result key sets, distinct positive actual-PID witnesses, ancestry, wait status zero, hash correlation, immutable loaded-module/source bindings, actual single-task profile, exact RuntimeError/diagnostic and zero integer counters. It returns bounded fork receipts; it does not prove the source covered every state field or acquisition route.

`CudaVerifierTests.fixture` at401 constructs synthetic CUDA records; `save_guard` at471 writes/re-hashes a synthetic fork pair. Existing mapping, outer corruption, fork schema/action/hash/PID/inventory, wrong-node and unknown-job tests cover the present ten cases. Replay/recurrent and producer fixture classes remain intact. The existing qualification supplied by root is 58 synthetic test methods plus separate mutation controls; no rerun was performed here. Source-defined method counts and unittest inherited executions must not be conflated.

Preserve old protocols and retained qualification artifacts. The adopted invocation fork trial deliberately extends the current inherited-PID role's finite obligations after a future grant; old two-trial results retain only their historical scope and frozen verifier identity. Do not add a compatibility fallback accepting two trials as expanded invocation coverage.

## Exact proposed six-role map

All rows use the existing proposed target `cuda_core_child`, module `tests/test_townlet/regressions/bac/test_rng_cuda_admission.py`, and one independently captured workers1 job/fresh qualified spawn. The target is an application-source prerequisite; it is not a field in today's external child identity schema.

| Proposed case | Proposed exact job | Proposed exact role | Proposed node suffix | Proposed exact queue message |
| --- | --- | --- | --- | --- |
| `invocation_same_error` | `cuda-core-invocation-same-error` | `cuda_core_invocation_same_error` | `test_isolated_poison_protocol[invocation_same_error]` | `cuda core invocation_same_error fail closed` |
| `invocation_child_failure` | `cuda-core-invocation-child-failure` | `cuda_core_invocation_child_failure` | `test_isolated_poison_protocol[invocation_child_failure]` | `cuda core invocation_child_failure fail closed` |
| `invocation_parent_failure` | `cuda-core-invocation-parent-failure` | `cuda_core_invocation_parent_failure` | `test_isolated_poison_protocol[invocation_parent_failure]` | `cuda core invocation_parent_failure fail closed` |
| `invocation_reported_failure` | `cuda-core-invocation-reported-failure` | `cuda_core_invocation_reported_failure` | `test_isolated_poison_protocol[invocation_reported_failure]` | `cuda core invocation_reported_failure fail closed` |
| `invocation_phase_reference` | `cuda-core-invocation-phase-reference` | `cuda_core_invocation_phase_reference` | `test_isolated_poison_protocol[invocation_phase_reference]` | `cuda core invocation_phase_reference fail closed` |
| `invocation_phase_failure` | `cuda-core-invocation-phase-failure` | `cuda_core_invocation_phase_failure` | `test_isolated_poison_protocol[invocation_phase_failure]` | `cuda core invocation_phase_failure fail closed` |

The jobs above follow the existing closed-map spelling, and are proposed until matched against actual frozen authored test bytes. Their argv is the existing CUDA tuple with the exact full module/node and unchanged `REPLAY_ARGS[3:]` tail. No other invocation-like string gains admission. The existing four-element final queue tuple remains unchanged.

Only the two phase rows may add `invocation_phase_sha256` to their parent observation, and only they may produce `invocation-phase-{role}.json`. Their child identity remains the current exact CUDA child identity. Other four new rows and every prior role retain their respective exact observation schema.

## Phase artifact and parity boundary

The proposed phase artifact schema is exactly `cuda-core-invocation-phase-v1`, with exact keys:

`schema, role, case, pid, ppid, base_commit, candidate_tree, manifest_sha256, source_sha256, devices, synchronize_events, exception_labels, completion_failed`.

Future per-job validation must bind role/case to its closed configuration; exact integer positive PID/PPID to that job's own qualified child; base/tree/manifest to that job's manifest; and exactly two `source_sha256` keys (`townlet.exploration.rng_custody`, `test_rng_cuda_admission`) to manifest source hashes and the existing exact imported paths. Require devices exactly integer `[0,1,2]`, ordered observed integer synchronize events in the declared device inventory, exception labels exactly `["body","synchronization"]`, and completion_failed identity-null for reference / identity-True for failure. Reject bool/float device aliases and integer1 as True. Parent's added hash must equal the independently read exact artifact bytes, after owned successful child termination as established by the authored application test/protocol.

Compare the qualified pair's base/tree/manifest/source hashes, devices and ordered observed event arrays. PIDs/PPIDs must match each respective job; no cross-job process-identity equality is required. Neither a hard-coded `[0,1]` trace nor a newly mandated device2 tail is the parity oracle. Actual E/F object identity/order and actual observed-event construction must be asserted in the child before serialization; semantic labels alone do not establish those facts.

**Concrete unresolved protocol interface:** the adopted prose requires the external verifier to compare two separately captured jobs, but the current `verify(spec_path, job_index=0)` and CLI select only one job. The protocol defines no exact peer-spec/job reference, pair-input document, pairing invocation, pair-result destination/schema, or point at which successful pair qualification is emitted. It also says each row is independently captured, so putting both jobs in one spec cannot be silently assumed. Root has authorized the finite prose proposal immediately below; it remains unadopted. No directory-neighbor discovery, guessed filename or unknown-role inference may supply a peer. Individual child custody remains distinct from pair-parity success.

The exact two-role artifact inventory rule also needs to be made operational in that freeze: require the correctly named sole phase artifact for each phase role and reject misplaced/swapped/extra phase artifacts, including artifacts on nonphase roles. Preserve unrelated historical job artifacts; do not invent a general directory allowlist. The strict parent-observation key sets are already unambiguous.

### Minimal pair-interface proposal for root adoption

**PROPOSED ADDENDUM ONLY, at root's follow-up request; no API or schema is adopted here.** Add one public function within the admitted verifier body:

`verify_invocation_phase_pair(reference_spec_path, failure_spec_path) -> dict`.

It consumes two explicit, distinct existing one-job specs. The first must select only `cuda-core-invocation-phase-reference` / `cuda_core_invocation_phase_reference` / case `invocation_phase_reference`; the second only `cuda-core-invocation-phase-failure` / `cuda_core_invocation_phase_failure` / case `invocation_phase_failure`. Each has exact integer workers1 and its existing sealed argv. No job-index parameter, peer discovery, optional role or additional selection document is introduced. Ordinary `verify(spec_path, job_index=0)` and the old CLI retain their contracts. Root can invoke this Python function through its owned tooling caller and exclusively serialize the returned dict to its explicitly chosen output; no CLI addition is necessary.

Prerequisite: ordinary strict verification has already succeeded on each exact spec and produced the corresponding exclusive `replay-spawn-custody-{role}.json`. For these two phase roles only, propose adding exactly one per-job strict receipt field, `invocation_phase_sha256`, equal to the validated child phase artifact hash; all other per-job receipt fields keep their current meaning. The pair function must not simply trust those status strings or call the exclusive-writing `verify` again. Within this same implementation body, reuse the complete per-job validation/receipt-construction portion without custody-output materialization, run the existing repository/source checks, re-read all bound subjects, and require each existing strict receipt's full parsed value to equal the recomputed expected per-job receipt, including current verifier hash and phase hash. Preserve the existing `verify` write behavior by keeping exclusive materialization in its existing path. This internal factoring adds no second public per-job API and must itself receive regression review.

Require both resolved roots to agree; base_commit, candidate_tree, manifest_sha256, exact two-key source_sha256, devices and exception_labels must agree. Require observed synchronize_events arrays to compare equal after per-job validation. Manifest files may have distinct paths only if their exact byte hashes agree. Each phase artifact and strict receipt must bind that subject's own child and parent process; compare neither process identity across subjects nor numeric PID uniqueness across independent jobs, since sequential OS PID reuse is possible. Distinct input specs and distinct subject job directories, exact complementary roles and hash-bound per-job revalidation prevent selecting one subject twice.

Return a dict with **exactly** these top-level keys:

`schema, status, verifier_sha256, shared, reference, failure, scope`.

- `schema`: exactly `cuda-core-invocation-phase-pair-custody-v1`.
- `status`: exactly `CUDA CORE INVOCATION PHASE PARITY VERIFIED`.
- `verifier_sha256`: SHA256 of the actual current verifier body, equal to each recomputed per-job strict receipt's verifier_sha256.
- `shared`: exact keys `root, base_commit, candidate_tree, manifest_sha256, source_sha256, devices, synchronize_events, exception_labels`; values are the common validated values, with root the normalized absolute resolved repository path and the event array the common observed vector. No prefilled event trace is accepted.
- `reference` and `failure`: each has exact keys `role, case, child_pid, parent_pid, completion_failed, references`. Values bind its own validated subject; completion_failed is identity-null / identity-True respectively. `references` has exactly `spec, manifest, result, controller, child_identity, parent_observation, phase_artifact, strict_custody`. Each reference has exactly `path, bytes, sha256`: normalized absolute resolved actual artifact path, its exact positive integer byte count and lowercase64 hexadecimal SHA256 of the bytes actually read. Paths are derived only from the supplied spec's existing output/naming contracts and manifest path; no free-form caller-supplied receipt references exist.
- `scope`: exactly `Two separately qualified CPU CUDA-core phase controls; observed synchronization parity only; no CUDA hardware, producer, parent-owner, B6 or whole-package qualification.`

All exact-field/type/value/role/hash/source/process comparisons fail with ValueError and return no pair receipt; absent/unreadable files may retain existing OSError behavior and malformed JSON existing JSONDecodeError behavior. An existing strict receipt is mandatory and must equal the fully recomputed result; stale verifier/result/manifest/child/observation/phase bytes, changed repository state, missing/extra fields, swapped arguments, same-role subjects or unequal observed vectors all reject. No missing peer is UNRUN-success, no partial status is returned, and the function writes no custody output. Root owns exclusive pair-output materialization and hash binding in later evidence. Validation cannot prevent later external filesystem mutation; immutable capture and root's final rehash obligations remain in force.

For phase artifact inventory, propose the finite marker glob `invocation-phase-*.json` within the selected job directory. Phase-role inventory must equal the singleton exact expected filename; every other admitted role must have an empty such inventory. This marker is a rejection inventory, never a role-admission rule. Unknown keys remain rejected independently. Files outside this finite marker namespace retain existing job-directory policy.

Root must adopt reviewed exact addendum bytes before authoring either per-job output change or this pair function. Its synthetic controls must include exact returned schema/reference paths/byte counts/hash values; full recomputed custody versus tampered existing receipt; swapped/same input; missing/extra/malformed peer; parent/process/source substitutions; stale current verifier identity; and coherently rehashed unequal events. A narrow returned receipt proves these finite comparisons, not parent RNG/probe semantics.

## Fixed proposed invocation fork extension

Keep job `cuda-core-inherited-pid`, role `cuda_core_inherited_pid`, node `test_isolated_inherited_pid_gate_refusal`, target `inherited_pid_child`, exact final message `cuda core inherited pid gates fail closed`, and existing four-element final queue tuple. Extend only `FORK_ACTIONS` with trial `invocation`, requiring exactly:

`active_enter, active_exit, active_completion_failed, completed_completion_failed, domain_device_invocation`.

Proposed files are exactly `fork-identity-cuda_core_inherited_pid-invocation.json` and `fork-observation-cuda_core_inherited_pid-invocation.json`; acknowledgement is exactly `cuda core inherited pid invocation fail closed`. Preserve current identity/observation/profile schemas and `cuda_core_inherited_pid_guard` record role. Require all admission/local/invocation trials and distinct grandchild identities; retain every existing action and check. No optional trial, renamed action or generic fork executor is admitted.

Authored tests must prepare genuine active/completed empty-inventory handles before actual fork; extend actual direct registry/context state observations; preserve real locks; and assert PID-first exact RuntimeError before any registry/thread/lifecycle path. The external verifier continues checking exact action maps, builtins.RuntimeError, `RNG custody cannot be inherited by another process`, zero integer counters and state_unchanged identity-True. It cannot itself inspect an active context or prove the state snapshot covered the eight actual record fields.

Per the supplied source review/report, actual record fields are `thread, state, participant, operation_kind, lineage, cuda_devices, context, failed_completion`, with domain `_pid` rather than an invented invocation PID field. Current application fork state observations omit the invocation registry; future source review must confirm the expanded real snapshots and context/generator completion linkage. No expanded application observations or new serialized fields are claimed to exist now.

## Bounded future implementation and synthetic test map

Only the two admitted tooling bodies are candidates for a later write grant. No application/helper/bootstrap body, third tooling body, protocol rewrite, source copying or API redesign is required by this preparation. The following is a map for the future owner, not permission to execute.

| Proposed task | Existing location | Required bounded change / evidence |
| --- | --- | --- |
| Closed six-role admission | verifier70–91; tests381–418,481 | Add six exact tuple entries and exact mapping tests; retain all ten old cases and reject each wrong case/node/message/role substitution, including coherently altered spec/result argv and unknown invocation-like names. |
| Two-role parent schema | verifier122,484–488; CUDA fixture | Compute the extra observation key only for the two frozen phase roles; reject missing/extra phase hash, hash field on old/nonphase roles, wrong schema types and substitutions. Keep original schemas for replay/recurrent/producer. |
| Exact phase artifact | new finite checker within verifier body; existing synthetic fixture | Validate exact keys, filename/inventory, values/types, process/manifest/source binding and parent-read byte hash; return only frozen per-job receipt fields agreed in protocol freeze. |
| Parity pairing | current single-job entrypoint and root-frozen new pairing contract | Implement only after the unresolved interface is frozen. Require independently qualified reference/failure subjects, correct complementary roles, shared source identity and equal observed events. Prevent per-job success from being misreported as pair success. |
| Fixed invocation fork trial | verifier159–246; tests399–653 | Add the five exact actions; synthesize third genuine-looking data trial with distinct fake PID, preserving all existing checks. Update expected guard receipt cardinality from two to three for expanded protocol. |
| Regression and rejection qualification | whole existing tooling test body | Preserve old test methods and apply inherited base guard controls to new role fixtures; add finite targeted mutation tables. Keep synthetic source bytes inert and Git/locking mocked. Freeze, independent review, then root synthetic qualification before actual child use. |

Required targeted synthetic groups (all proposed):

1. Positive admission for all six roles, two phase artifacts and the three-trial inherited role, with receipt hashes and exclusive destinations checked. Old replay/recurrent/producer and other CUDA role protocols still pass within their existing scope.
2. Missing/malformed/extra phase key and nested source key; wrong filename, swapped role/case, misplaced artifact, missing file, corrupted bytes with stale parent hash, wrong parent hash, wrong process identity, stale base/tree/manifest/source and wrong devices/labels/outcome. Include coherent swaps/rehashes so schema/role/source checks must reject them independently of a stale hash.
3. Event arrays malformed as nonlists, bool/float/out-of-inventory entries; reference/failure null/True substitutions including 0/1 aliases; unequal observed event arrays with both per-job hash chains otherwise consistent. Pair controls also cover missing peer, same-role pair, wrong candidate/source and swapped/tampered pair subjects, using only the later frozen pair interface.
4. Old/nonphase observations must reject `invocation_phase_sha256`, unknown extra keys and phase artifact presence. Phase observations must reject omission of that exact required field. No arbitrary optional-field branch is acceptable.
5. Invocation trial missing from either inventory, extra/lone/renamed trial records, missing/extra/renamed actions and result fields; mismatched message/trial/profile/role/source/manifest/hash; reused ancestor/sibling grandchild PID; wrong wait/exit status or numeric type; nonzero/boolean counters, false unchanged-state or wrong exception/diagnostic. Exercise admission/local and invocation, not just one representative trial.
6. Preserve configured thread/import/source/controller/job/result/log/repository/custody destination checks. Reuse existing broad corruption helpers; add explicit new-role checks where inheritance does not cover them. Do not execute application imports or real Git in synthetic qualification.

Synthetic acceptance certifies tooling behavior on the frozen synthetic subjects only. The strict verifier has no serialized before/after RNG snapshot in today's CUDA observation schema. Parent RNG neutrality/healthy domain, one-shot child sync fault, real E/F identity, observed-event provenance, owner-lock ordering, expanded direct state and genuine pre-fork handles must therefore be established by actual authored assertions plus independent source/test review and root execution. Do not silently import the producer baseline schema or add CUDA observation fields to fill this boundary.

## Readiness, budget and ordered handoff

**Ready:** closed-role constants, existing per-job validation hooks, exact two-role observation distinction, finite fork extension and synthetic rejection obligations are mapped from the two retained bodies.

**Not ready for a tooling write:** actual application child/fork tests have not been supplied/frozen/qualified for this extension; the minimal cross-job pair input/result addendum above remains proposed. Root must bind actual node/role/target/message/artifact bytes and adopt the reviewed finite interface first. A preparation hash is not an admission or execution receipt.

Tooling estimate, not a grant: verifier +150–250 lines, synthetic tests +250–400 lines, for prospective totals verifier731–831 / tests1239–1389 / combined1970–2220, still two bodies. Pair-interface requirements can affect that estimate. A possible later reservation is verifier900/test1450/combined2350/two bodies, subject to root's explicit tooling allocation; it must not be added to the application's independent3600 reservation as though both were one worker's granted slice. No tests, fields or rejection controls may be removed merely to fit an estimate. Measure actual final bodies, and request root reslice before exceeding a granted ceiling or reading any third body.

- [ ] Root finishes current separate source/test work, grants the actual application test stage, and freezes authored child/fork protocol bytes and source manifest identities.
- [ ] Root/protocol owner resolves the authenticated parity-pair interface, exact success/output contract and phase artifact inventory enforcement; bind the resulting exact protocol bytes/review/adoption.
- [ ] Root grants only the two tooling bodies and explicit tooling line ceilings; owner implements tests-first within that grant, retaining all old-role checks.
- [ ] Freeze tooling hashes/line counts; obtain independent review of the exact finite extension, rejection controls and source/test linkage.
- [ ] Root performs synthetic qualification and mutation controls on frozen tooling; preserve failed/unrun attempts and exact tool/test hashes.
- [ ] Root captures exact application/tool/spec subjects and performs collection/healthy prerequisites, six separate qualified children, paired parity qualification and fixed three-trial inherited-PID qualification.
- [ ] Independently assess actual child/fork/source custody and exact bounded behavior; publish only through root's EVIDENCE-PROCESS chain. No hardware, parent-consumer/producer integration, B activation, B6, package/coverage/global type or final CI gate closes automatically.

Preparation verification is limited to authorized full text reads, input hashes/line counts, map self-review against the adopted protocol, and exact output-file verification. No passing new synthetic or application test is claimed.
