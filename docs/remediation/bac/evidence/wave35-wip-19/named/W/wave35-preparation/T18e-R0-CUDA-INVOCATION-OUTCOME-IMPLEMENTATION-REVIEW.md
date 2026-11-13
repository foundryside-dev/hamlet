# Invocation outcome — independent implementation review

2026-11-13. Reviewer `/root/bac_astra_invocation_source_review`.

**SPEC: APPROVED for the initial source implementation and staged nine-test packet. QUALITY: APPROVED at source-review level. No concrete source defect found. Full invocation acceptance remains OPEN pending the explicitly planned second-phase qualification.** These verdicts do not promote old child evidence into new invocation coverage or close the component/producer programme.

## Exact scope and evidence

Read repository AGENTS.md, the adopted complete DESIGN-FIX1, scoped design peer review, root adoption, implementation map/report, core diff and the two current implementation bodies. No other implementation body, replay writer body, application import, test/runtime execution, source/test/index edit, branch/worktree/copy or subagent was used. This review is the sole authored artifact. Current branch is `project-recovery-bac-2026-11-01`, HEAD `df8dcebc90d8faec3da82f2eb036c24fcc2eb8e9`.

Measured and SHA256-verified current bodies: `src/townlet/exploration/rng_custody.py`, 948 lines, `ed8df0b56707baa08d46dd3422b91521bbe15a02c187643cc360a565e3c8372e`; `tests/test_townlet/regressions/bac/test_rng_cuda_admission.py`, 1681 lines, `ccc74e6bac55f322d3363ac1e19c820b2b97b0d86839b392dfabedb452647a38`. Total 2629 lines/two bodies, within the paired budget.

Verified requirement/artifact hashes:

| Artifact | SHA256 |
| --- | --- |
| DESIGN-FIX1.md | `e18de5be6abaa11c1e2ba14929a917ca547c2e41b349dd9102c2ea49cf55c723` |
| DESIGN-FIX1-REVIEW.md | `71b14345eacc6a319772b33ed6043ff377e7e55da34b5a2d06277a6bf5fe6496` |
| IMPLEMENTATION-MAP.md | `3ba4a090904925006de901f154b41153d8e70cdfa24ad2e761acd8d94edd9f71` |
| IMPLEMENTATION-REPORT.md | `0f3453e817e4af6fb2167354e3fa80f19243777e227ce2cf104cab138c423116` |
| CORE.diff | `920a105e28330dbf71d5fc34a56992c383ed3e1fdcbfb65d2498467fc29645b7` |
| TESTS-ONLY.diff | `73be274ebfc2d21319579739c19a61934edb39e1123f390ddef51e6a5015a001` |
| wave35/r106-root-checks.json | `803d831ae57fbc8fd46963be58ee095301895beb6c4fcc88fb572aa6a4b05570` |

The filenames above use the `T18e-R0-CUDA-INVOCATION-OUTCOME-` prefix unless a wave35 path is shown. Root adoption `wave35/r90-device-invocation-design-adoption.json` explicitly adopts that design and peer hash while retaining implementation/qualification obligations.

R106 is root-executed evidence, not a reviewer rerun: tree `ab46784efc86bab95b031494529e06871a12f1ff`, manifest `12e5609bf4f300e608ebd6f94297fd0f2496bf95169e757864cb6ad50fbd0970`; 76 collected/unique passed = 66 nonisolated + 10 existing isolated, with recorded generic/strict child custody PASS. Ruff/Black, unchanged defaults ceiling600 and owned four-file mypy pass are bounded root results. R105's nine causal missing-API RED results are attributed through the implementation report; this review did not rerun or independently requalify them.

## Source findings and contract assessment

No severity-ranked defect is reported: no concrete supported trigger violating the adopted implementation contract was identified in these bytes.

- **Authority/API:** core59-79 and 675-699 provide the exact all-required factory and opaque single-use context surface. `_Opaque` refusals and exact-class weak-registry authentication prevent ordinary construction, copies, serialized authority and unissued/subclass lookalikes. The factory checks real PID before membership/lineage/shape lookup, performs no CUDA or exclusion work, and returns no operation authority. Real admission is repeated through `_operation` at entry; stale membership or lineage cannot be laundered by early issuance.
- **Thread/PID/lifecycle:** `_invocation_record` checks actual PID at 693 before registry access, then compares the issuing `Thread` object by identity at 697. All three public handle methods route through it before locks or CUDA. Entering/active/entry-failed getters refuse; duplicate entry/exit does not change a completed result. Clearing `record.context` before delegated exit also rejects recursive exit while leaving the result unreadable. Failed entry clears bindings; active exit seals in unconditional finally before errors reach the caller (709-753).
- **Own-phase attribution:** each factory creates its own record, passed directly to the existing `_operation` generator. `_finish` certifies False only after its actual `_complete` returns successfully (350-361); body/report/poison/error-list contents cannot certify or invalidate that observation. The initial True therefore remains for failed or unfinished completion. Nested completion receives its own admitted subset at 840; outer completion receives the existing accumulated device union at 869. Descendant failure alone cannot set the parent's result. No result is rewritten by a later sibling/parent phase.
- **Error/sealing semantics:** completion certification occurs before reported-failure aggregation and identity deduplication. `_raise` is unchanged. A same-object body/sync error can still emerge as the same E while the result differs from body-only E. `_exit_invocation` seals before outward delivery and returns False on normal completion; it does not suppress delegated errors. Later internal cleanup failures remain outward failures rather than being hidden by the result.
- **Operation/empty-path parity:** existing operation/device_operation wrappers pass explicit `completion=None`; all membership, exclusion, pinning, token/currentness, generation/revision and union behavior stays in the shared algorithm. There is no second completion pass, callback API, compatibility path, default or policy issuer. `_complete` remains the generic early-stop loop, not a newly promised tail policy; local all-device cleanup remains unchanged. Empty `_complete` touches no CUDA attribute. Historical reads neither clear poison nor revive retired operations.
- **Lifetime:** completion and failed-entry release clear participant, kind, lineage, devices and context (702-707). The weak registry value has no handle reference; retaining an exited handle does not directly retain an owner, operation, exception, traceback or generator. The issuing thread identity remains intentional authentication provenance. The current body-error weak-reference control at tests670-702 checks the ordinary completed-handle lifetime case.

## Confirmed facts for the next test/probe phase

The implementation report's eight-field record and lock-path account is accurate. Actual `_Invocation` fields at core187-195 are `thread`, `state`, `participant`, `operation_kind`, `lineage`, `cuda_devices`, `context`, `failed_completion`. Registry is `_invocations` at 216. State spellings are `issued`, `entering`, `active`, `entry_failed`, `exited`. There is no stored PID field in the record: process provenance is the domain `_pid` checked against `os.getpid()`.

The private observer is the generator's required `completion` argument; `_Operation` gained no field. During active execution the record owns the context, and its generator frame holds that completion record. During exit the context moves to a local while the record remains active/context=None, then execution fields clear and state becomes exited. Direct state tests should distinguish this transient exit shape from completed state and observe the actual context/generator references without creating retained-reference artifacts of their own.

No new lock cache or alternate acquisition path exists. Issuance, handle authentication, historical reads and release take no domain/owner lock and do not invoke `_is_owned`. Real operation entry takes `self._lock` at 795; completion failure uses existing `poison` acquisition at 932. The forwarding `LockProbe` at tests1245 remains appropriate, including its ownership and acquire-restore forwarding. However, current `guard_state` at tests1289 omits `_invocations` entirely. Current fork trials at tests1514 onward admit only admission/local actions. Their old zero-call/unchanged-state observations therefore cannot establish invocation guard coverage. Extend the exact state and action maps before expanding claims.

The nine new tests (435-702) correctly cover exact public signatures/types, empty success and body-error result, genuine token/retirement flow, lifetime, ordinary wrong-thread refusal under held locks, forgery, lifecycle and retired-member entry failure. They use authentic participants/operations and no CUDA access for the empty path. Source-only review found no fake receipt issuer, production contract activation, weakened assertion or counterfeit PID in this delta. The existing empty production manifest assertion remains at tests215-216.

## Remaining qualification, not source defects

The staged map explicitly owes nonempty success and failure, same-E/different-error identity schedules, nested/sibling receipt independence and outer-union parity, gate-reported poison with successful own completion, failed inventory/readiness entry, deterministic numeric-ID alias resistance, and direct registry/reference/state checks. In particular, ordinary wrong-thread tests do not independently prove recycled-ID resistance even though the source compares thread objects.

Invocation fork controls must prepare genuine active and exited handles before the real guard-only fork, cover active enter/exit/getter, historical getter and fresh factory PID-first refusal, and use separately reviewed exact role/action/verifier maps. The old ten child cases do not qualify any new own-invocation failure or fork schedule. Public consumer typing, owner-lock contender/seal/read/transition evidence and the designated parent-outcome consumer remain open. A child's immutable False cannot serve as a receipt for a later failed parent union, nor determine which owners the parent must quarantine.

Proceed to the bounded second test/verifier phase against these source facts. No source correction is requested by this review. Producer integration, hardware, pre-B clone-stability dependency, B6 and full programme acceptance remain separate and open.
