# Generic full diagnostic capture mini-plan

Status: design only; root review precedes test or production edits. No APP changes, imports, collection, or execution performed for this plan. Existing failure-only diagnostics and their evidence remain unchanged.

**Goal:** Preserve full actual POP failed-state diagnostics when BANK remains available, as well as when BANK has an authenticated ordinary runtime-failure quarantine, without treating either diagnostic as resumable.

**Source design:** [failure diagnostic plan](T18e-R0-PARENT-C1-FAILED-DIAGNOSTIC-IMPLEMENTATION-PLAN-v1.md), SHA-256 `3137a53537a0561665dafccef940c9fe4ada035e1c0eaf2c9e351309a18bbf1a`; [corrected supplier v2](T18e-R0-PARENT-C1-FAILED-DIAGNOSTIC-SUPPLIER-v2.md), SHA-256 `b0d78028aaea09479d089646505c0b7b379fbc5c2cc2293161862f1b852d411f`.

**Required supplier facts:** native capture `T18e-R0-NATIVE-FAILED-DIAGNOSTIC-CAPTURE-FACTS-v1.md`, SHA-256 `1be66aa7f93495b6c0304fa22974af4abbe4804a740bb32536130283b8079611`; fixture `T18e-R0-PARENT-C1-DIAGNOSTIC-FIXTURE-FACTS-v1.md`, SHA-256 `5b1b4f7c068669cd60e6d2edc41fa581c6fdd2b7ab1a984fa5d60f548f63add5`. No additional implementation body was read.

## Frozen source inventory

Rehashed unchanged before this plan; all paths relative to `/workspace/hamlet`.

| Source | Lines | SHA-256 |
|---|---:|---|
| `src/townlet/config/exploration_policy.py` | 1333 | `e08309e0c55ca0d757fc33c926a21ee266b2935082826c14994208d6aebc3191` |
| `src/townlet/exploration/scoped_curiosity.py` | 1467 | `8da80d4c87f666f6df7a4260ca16dd8feeb460ffa83e6713904e739598b667cc` |
| `src/townlet/exploration/parent_custody.py` | 239 | `1b911c653ed1b1738c4de19b646bd1965cc0825b6f85e814e5ba25a43e02944f` |
| `tests/test_townlet/regressions/bac/test_runtime_bank_parent_custody.py` | 1165 | `b968c943bafccfe2f6317464380a286fe3de3ae5efa7e0e32ae09e61ede1ee4b` |

Four bodies total 4204 lines; retained independent probe adds 64, giving 4268 lines / five bodies. Caps remain runtime 1450, BANK 1600, test 1350, unchanged helper 239, probe 64: maximum 4703 / five. No sixth body or new test file. If focused test growth cannot fit the remaining 185 test lines, report a finite packet split before expanding scope.

## Concrete additional interface and schemas

Add `ExplorationRuntime.diagnostic_state(self) -> dict[str, Any]` and `ScopedCuriosityBank.diagnostic_state(self) -> dict[str, Any]`. Neither accepts a caller policy flag or claimed failure classification. Keep `checkpoint_state` and `failure_diagnostic_state` public behavior unchanged, including the failure-only API's refusal on available BANK state. No API consolidation or removal.

BANK generic output contains every current BANK transport field, with `schema="curiosity-bank-diagnostic-v1"` and additional `failure_reason` equal to exactly `None` or `"runtime_failure"`. Runtime generic output contains every current runtime transport field, with `schema="exploration-runtime-diagnostic-v1"` and the same `failure_reason`, copied from its actual returned BANK diagnostic. Its `bank` field is itself generic diagnostic transport. `failure_reason=None` means BANK was locally available; it must not be presented as a BANK runtime failure. Distinct diagnostic schemas make both variants nonresumable, including `failure_reason=None`.

The classification describes only BANK's local eligibility at capture admission. It is not a claim that POP, all children, or the whole run is healthy; it conveys no training/resume authority. In particular private native snapshot envelopes may truthfully contain `healthy=False`. No current healthy-schema payload wrapper is exposed for extraction. Historical origin archives remain historical records, not a current resume substitute. All current selector/cadence/policy, native parameters/gradients/RNG, cursor/cache/step/completion fields remain present and freshly captured.

## Exact eligibility and producer factoring

Both new methods use their current operation/serialization decorators and BANK observation boundary. Preserve domain-before-runtime-before-BANK lock order, exact scope/thread/PID/lineage, delegated single-use permits, callback guards, own invocation completion, and monotonic completion uncertainty. Runtime uses `_checkpoint_payload("diagnostic_state")`, which still owns selector/cadence before the BANK call; no stronger pre-work-refusal claim is introduced.

Inside admitted BANK generic capture, branch directly on the actual producer-owned `_failed` state; do not attempt healthy capture and catch an exception to select failure capture:

1. If `_failed` is false, call existing `_available()` to reject completion uncertainty and pending completion. Use the existing full private `_checkpoint_payload()` and set `failure_reason=None` only after capture succeeds. No accepted episode is required solely for this branch: ordinary healthy checkpoint supports initial state too.
2. If `_failed` is true, use a private `_runtime_failure_payload()` extracted from the current failure-only method's eligibility plus capture sequence: reject `_completion_uncertain`; require retained `runtime_failure` quarantine; authenticate its exact accepted identity through `_auth`; reject pending completion; then call the same full `_checkpoint_payload()`. Set `failure_reason="runtime_failure"` only after successful capture.
3. Extract this private helper without relaxing the failure-only method: it calls `_runtime_failure_payload()` and retains its existing failure schema and `failure_reason`. The generic method retags the private result with its own generic schema/classification before returning. Do not call one decorated public method from another or return a public healthy-schema intermediate.

This retains refusal for unclassified local `_failed`, empty-participation quarantine, stale/unauthenticated quarantine, pending completion, own uncertainty, broken RNG ownership, and poisoned domain. Native child calls remain exact: per-world `snapshot_with_capture` can export local `healthy=False`; shared `call` refuses an already failed shared owner. No replacement child API, raw provider access, health reset, cached-before-failure data, or invented lineage is permitted. Capture still advances observation/revision currency and invalidates runtime restore currency where it does today; completion failure returns no successful diagnostic and retains its own uncertainty latch.

Extend explicit diagnostic-schema rejection in runtime `_parse` and BANK `prepare_restore` / `prepare_private_initialization` to include their generic schemas alongside the existing failure schemas. Runtime must also reject a generic BANK diagnostic nested inside an otherwise healthy runtime envelope before copying/materialization. Unmodified generic diagnostic dictionaries cannot satisfy either owner's opaque `install_restore` authority. Preserve healthy saved-payload recovery and existing healthy checkpoint semantics.

## Test and implementation sequence

- [ ] Root reviews this mini-plan and grants TEST-ONLY phase. Append tests only to the existing C1 test file; preserve existing assertions and evidence.
- [ ] Add generic full-field comparisons on actual available initial and serviced state and actual authenticated runtime-failure state, for both scopes. Reuse transparent full capture references and real child-capture observations. Cover all five policy families across this bounded matrix; assert exact classification and nested schema, owned returned data, and no health reset.
- [ ] Keep the existing healthy/failure-only refusal controls. Add generic pending completion, empty quarantine and authenticated refusal controls. Reuse actual completion fixture protocols; do not assign private health flags. Preserve private local-failure `healthy=False` export and shared local-failure refusal through genuine native callbacks.
- [ ] Add runtime/BANK restore and private-init refusal checks for both generic classifications, including an otherwise healthy runtime envelope with a generic BANK subtree; assert no candidate registration/materialization. Add standalone/bound callback guards for generic capture.
- [ ] Add one new isolated generic diagnostic own-completion failure role through the existing fresh-process poison/self-witness mechanism; no domain reset or ordinary-worker poisoning. Keep the existing six poison roles unchanged. Root records the exact role/node/env in the sealed test handoff and runs it fresh after implementation.
- [ ] Freeze exact test/source hashes; root observes missing-API RED under qualified custody before releasing production. Root's separate POP writer supplies actual failed-prepared and pre-quarantine caller RED controls.
- [ ] On separate production release, implement only runtime/BANK methods, private factoring, and loader refusals described above. Helper remains unchanged. Run scoped AST/static checks only; root owns APP runtime execution and independent review.
- [ ] Root validates new ordinary and isolated cases, existing failure-only and C1 regressions, scoped/global static gates, and the actual POP preservation controls. Existing PASS evidence remains immutable; it does not qualify newly added behavior automatically.

## POP boundary and remaining obligations

Per root's source-qualified finding, actual failed POP progress can coexist with available BANK: prepared-stage failure intentionally skips quarantine, and cleanup can fail before producer quarantine. The new API preserves full capture for those cases without falsely asserting BANK runtime failure. POP's actual failed-progress route selects runtime `diagnostic_state`; healthy POP retains runtime `checkpoint_state`. Preserve all 12 outer fields and existing evaluation order. POP receiver still reaches its genuine failed-progress rejection before candidate materialization/runtime restore, after its existing serialized validations. POP changes are a separate writer baton and are not authorized by this plan.

No summary, cached substitution, unsafe-state inspection, capability reduction, compatibility layer, or acceptance waiver is proposed. Root-reported existing 30 ordinary failure-diagnostic cases, isolated completion case, and 12 caller controls remain evidence for their exact prior bytes only. This plan claims no new runtime result and authorizes no edits by itself.
