# C1 full failure diagnostic implementation mini-plan

**Goal:** Preserve actual full exploration diagnostics after ordinary local BANK runtime failure, without admitting diagnostics for resume or bypassing child health/completion.

**Spec:** [source-owned supplier v1](T18e-R0-PARENT-C1-FAILED-DIAGNOSTIC-SUPPLIER-v1.md), SHA-256 `e573705337e7b755cbe49ad7f0166bce3930d5c8644e5b234962a2c0c5560f38`.

**Mandatory correction:** [supplier v2](T18e-R0-PARENT-C1-FAILED-DIAGNOSTIC-SUPPLIER-v2.md) supersedes v1's incorrect blanket native-local-failure refusal: private capture may export `healthy=False`; shared managed call still refuses. Preserve those exact existing child contracts.

**Exact dependencies:** native `T18e-R0-NATIVE-FAILED-DIAGNOSTIC-CAPTURE-FACTS-v1.md` SHA-256 `1be66aa7f93495b6c0304fa22974af4abbe4804a740bb32536130283b8079611`; fixture `T18e-R0-PARENT-C1-DIAGNOSTIC-FIXTURE-FACTS-v1.md` SHA-256 `5b1b4f7c068669cd60e6d2edc41fa581c6fdd2b7ab1a984fa5d60f548f63add5`. BANK clears old completion on next begin; committed-history test captures before that boundary.

**Architecture:** Add distinct `failure_diagnostic_state(self) -> dict[str, Any]` public methods to `ExplorationRuntime` and `ScopedCuriosityBank`. Retain existing custody/admission/observation decorators and genuine child interfaces; factor serialization only within the source owner. Python/PyTorch; no helper change, dependency, compatibility mode, or outer POP schema change.

## Scope and schemas

The runtime result retains all current runtime transport fields, changes `schema` to `exploration-runtime-failure-diagnostic-v1`, and adds `failure_reason="runtime_failure"`. Its `bank` field is itself a BANK diagnostic. The BANK result retains every current BANK transport field, changes `schema` to `curiosity-bank-failure-diagnostic-v1`, and adds the same failure reason. No separately exposed nested healthy-schema payload is returned. Historical origin archives remain historical archives, not a current resumable snapshot.

Eligibility requires actual local `_failed` plus retained `runtime_failure` quarantine, exact authenticated accepted identity, no `_completion_uncertain`, and no pending completion transaction. Common core and native admission/completion remain authoritative; no health flags are cleared. Neither healthy state nor `empty_participation` quarantine qualifies. Normal checkpoint methods remain unchanged. Capture uses actual current child calls and full selector/cadence/native/gradients/RNG/cursor/cache/step/completion data, not a pre-error cache.

In particular, private `snapshot_with_capture` must retain truthful locally failed `healthy=False` export; do not add a stricter native-health gate. Shared `call` retains its existing local-failure refusal. Core poison, broken RNG ownership, and completion uncertainty remain refusals. This distinguishes body failure from failed completion without widening unsafe inspection.

Normal runtime and BANK `prepare_restore` and private initialization must reject diagnostic schemas before materialization or registration. Opaque `install_restore` cannot accept a diagnostic dictionary. Keep existing saved healthy-payload local recovery. Preserve observational revisions, runtime restore invalidation, genuine lineage, callback guards, own completion receipts and monotonic uncertainty.

## Bounded files and authority

Runtime <= 1450 lines; BANK <= 1600; helper unchanged 239; existing C1 test <= 1350; retained independent probe 64: maximum 4703 lines / five bodies. No sixth body/test file. Current source hashes are pinned in the supplier; exact inert `.before.txt` snapshots and inventory are in `evidence-management/parent-c1/failed-diagnostic-red-v1/`.

Only TEST-ONLY RED editing is currently authorized: append focused tests in `tests/test_townlet/regressions/bac/test_runtime_bank_parent_custody.py`. Root owns all runtime executions. Production and POP remain frozen until root observes valid RED and grants the next phase. No Git operations, branches, execution source copies, or hardware work.

## Review focus and test steps

- [ ] Append shared/per-world, five-family actual-step diagnostics comparing all fields against transparent genuine pre-quarantine capture; observe delegated native capture again after quarantine to prevent stale-cache substitution. Include actual serviced phase cache/gradients/private RNG transport and actual committed completion before the next episode clears it.
- [ ] Add healthy and empty-quarantine refusal controls, authentic pending completion and child refusal controls, and genuine own-completion uncertainty controls. No private health-bit fabrication.
- [ ] Add diagnostic receiver refusal tests at runtime/BANK prepare/private initialization/install, recording no candidate registration/materialization, plus authentic healthy restore positive control.
- [ ] Add standalone/bound callback reentry checks and fresh-process diagnostic completion failure witnesses using existing genuine completion instrumentation. A new method must not borrow a public-call permit or hide failed own completion.
- [ ] Freeze test bytes, exact node parameters, snapshots and hashes for root. Root runs positive fixture prerequisite and RED under a sealed candidate; missing API is expected, fixture/setup errors are not acceptance.
- [ ] Only after root releases production: implement the two distinct APIs and internal serializer factoring in runtime/BANK; add explicit diagnostic schema refusal at relevant producer restore boundaries. Do not modify helper or POP in this packet.
- [ ] Root runs repaired focused tests, existing C1 ordinary and fresh-process poison cases, scoped/global static gates, and independent source review. This plan does not waive wider required owner/integration failures.

The POP follow-on preserves its 12-field `get_checkpoint_state` outer shape and changes only the exploration capture selected on its actual failed route. Its receiver must reach the existing failed-progress refusal before materialization/runtime restore; POP/replay serialization validation may precede that refusal. That caller patch and full POP payload assertions belong to the separately bounded POP owner, not this test-only phase.

No payload reduction, cached substitution, after-poison raw inspection, or capability consolidation is authorized. Implementation and GREEN remain outstanding until separately released and observed.
