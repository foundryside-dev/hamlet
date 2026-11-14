# Invocation strict verifier — independent implementation review

2026-11-13. Reviewer `/root/bac_astra_invocation_verifier_review`.

**SPEC: PASS. QUALITY: PASS for the finite frozen tooling extension. No concrete P1/P2 finding or blocking protocol mismatch identified.** Seven independently selected synthetic probes pass. This admits the tooling packet for root's next exact capture/adoption decision; it is not application-child, fork, pair-runtime, CUDA hardware, producer, parent-owner, B6 or whole-package acceptance.

## Frozen subjects and scope

The reviewer waited for root's explicit implementation freeze before reading or executing the verifier. SHA256 values were checked before and after the independent probes:

| Subject | Lines | SHA256 |
| --- | ---: | --- |
| `/workspace/bac-review-2026-11-01/qualification/verify_bac_replay_spawn_identity.py` | 744 | `311f32e05522e1f81b7c2e130f95483568eb642a88b12ed44e7b3188084c7cd0` |
| `evidence-management/test_replay_spawn_verifier.py` | 1423 | `dc604fcab0dccbec82feb592be29108b6e4c6cb2899c3f4b5d647725e098228b` |
| `tests/test_townlet/regressions/bac/test_rng_cuda_admission.py` | 2166 | `780b1464c258d0a0162f9f0983be079b869c3868b4d24fbbc029afa154218b36` |

Exactly these three implementation bodies were admitted, conservatively counted as 4333 lines. Reviewed the verifier, synthetic assertions/fixtures and relevant actual application child/phase/fork paths. No core948, producer application, bootstrap/helper implementation or fourth implementation body was read. Core behavior is attributed to the independently reviewed source packet rather than inferred from this review.

Protocol `T18e-R0-CUDA-INVOCATION-OUTCOME-SECOND-PHASE-PROTOCOL.json` SHA256 `57d2984443217a1f31ae468173bf4d21333d5828ee3cf1df550f9963cf3414c3`; independent source review `...-SECOND-PHASE-REVIEW.md` SHA256 `7aea3ba6b7fd450afa4c9de7146e0f41cdc0cd31c7fdfcefe6e0c8ca3d602bca`; adopted pair interface `wave35/r107-invocation-pair-interface-adoption.json` SHA256 `a6b894198e2d823a899b8da62dc6a80965159568ff7a2d64657bcad36ac6d6f8`. The preparation/addendum review supplied the exact narrow pair contract.

No actual Git command, application import, spawn, poison or fork execution, branch/worktree/checkout/source copy, source/helper edit or delegation occurred. The only persistent writes are this review and the exclusive independent probe result. Existing fixture cleanup removes only generated temporary synthetic data.

## Source findings

The closed six-case inventory maps exact job, node, role and message values to the actual application `INVOCATION_CASES`, `cuda_core_child` and parameterized parent. It does not authorize arbitrary prefixes. All six invocation controls require a one-job spec. The two phase roles alone extend the parent observation and individual strict receipt with `invocation_phase_sha256`.

`check_invocation_phase` at470 requires precisely the admitted marker inventory for every selected protocol, exact top-level fields, exact module/source map, actual subject PID/PPID and manifest/source bindings, integer devices and nonempty in-inventory integer events, labels in order, and identity-null/reference versus identity-True/failure. Bool/float aliases cannot stand for integers or the completion result. Marker files on nonphase CUDA, replay or producer selections reject. Schema checks remain independent of a coherent parent rehash.

Application1593–1614 constructs the matching phase record only in qualified phase children and exclusively creates its marker; the parent hashes the actual artifact after owned child termination and queue identity correlation. Application1384–1401 derives the vector from observed synchronization calls and labels only after asserting actual outward E/F object order. The verifier appropriately checks serialized custody/parity rather than claiming those semantic facts from labels alone.

The third fork trial adds exactly active_enter, active_exit, active_completion_failed, completed_completion_failed and domain_device_invocation. Existing admission/local trials, exact inventory, ancestry, raw zero wait status, source/profile/hash and exact action/result/counter checks remain present at179. Application1981 and2094–2117 construct the corresponding genuine completed and active handles and run the specified trial. Actual guard snapshots/counters are emitted only after direct assertions at1825–1847. The existing within-fork distinct-PID policy is retained; the new pair function adds no cross-job PID uniqueness assumption.

`_validated_subject` at544 retains full binding, immutable inventory and repository validation and constructs the expected individual receipt without materializing custody output. `verify` at683 retains destination refusal plus exclusive create. `verify_invocation_phase_pair` at691 calls the validator, never the writing entry point. It rejects identical resolved specs, wrong argument role order, noncomplementary selections and duplicate resolved job directories; it requires each existing individual receipt and recursively compares exact types, fields and values via `same_typed` at534. This prevents Python bool/int/float equality from accepting a fabricated receipt.

Pair shared equality includes resolved root, base/tree, exact manifest hash, source map, devices, labels and the actual observed vector. The vector has no fixed early-stop tail. Each subject keeps its own process identity and null/True outcome. All seven top-level keys, exact shared/subject keys, eight path/byte/hash references and scope text match the adopted API. `artifact_reference` at528 re-reads bytes and verifies the earlier validation hash before constructing each reference. Missing or malformed inputs cannot yield partial pair success. Pair execution writes no custody receipt; the retained repository validator still uses its existing index lock and repository checks, so this is not a claim that the entire function performs zero filesystem operations.

## Synthetic evidence

Root's GREEN attempt1 result was inspected, not rerun: all75 methods PASS, unittest2.749s/wall2.926854s, exit0; exact verifier/tests hashes unchanged. Result SHA256 `208ee0d5701cd41c76ae2327b6335e98cf4181c35635b67560d27cc72ee800c0`; log SHA256 `e5ee64da40d172629750ff6656ee76ee6f5d99f9b81223ea5c51d92da6bd56bc`. The frozen tests independently exercise genuine positive receipt construction, old exclusive-write behavior, source/profile/identity controls, all three fork trials, exact typed existing receipts and coherent unequal phase vectors. Pair assertions were blocked on positive prerequisites in root's earlier RED, not misreported as independently exercised RED controls.

Independent command: `PYTHONDONTWRITEBYTECODE=1 /workspace/hamlet/.venv/bin/python -`, cwd `/workspace/hamlet`, using the existing frozen fixture module and an inline finite probe program. The exact probe program, setup, source hashes, individual results and elapsed time are recorded in `evidence-management/invocation-verifier-qualification/independent-astra-probes-attempt-1.json`, SHA256 `2ab2595250b4b065a32ce250539b6d0a72e7a3e89ca92e3b616c7ebbc7101815`. Result: **7/7 PASS**,0.075850s probe time, shell exit0.

- Positive pair accepts equal numeric PIDs across separate jobs and equal manifest bytes at distinct paths; all fixture files remain byte-identical.
- Existing strict receipt `parent_job_exit_code: 0.0` rejects against recomputed integer0.
- Existing strict receipt encoded as a JSON list rejects.
- Empty observed events with coherent parent rehash reject.
- Equal `[0, true]` vectors with coherent parent rehashes on both subjects reject; equality cannot bypass integer validation.
- Peer jobs encoded as an object reject.
- Deliberate phase-byte mutation between phase validation and reference capture rejects; only the deliberately changed fixture file differs, with no partial custody output.

All pair calls use the fixture's patch that makes invoking writing `verify` an assertion failure. Subprocess Git calls and flock are mocked by the existing fixtures. No broad75 rerun was performed.

## Remaining qualification boundary

No correction is requested. Root still owns exact application capture and the16 separate child qualifications, changed three-trial fork execution and explicit phase-pair receipt materialization after successful individual qualifications. These tooling probes do not establish actual parent RNG neutrality, owner-lock ordering, genuine E/F attribution or inherited state coverage at runtime. Those depend on the reviewed application assertions plus root's qualified executions. Final hash binding and immutable evidence capture remain necessary; the function does not prevent later external file mutation. No package/programme gate is closed here.
