# Invocation outcome — proposed next qualification protocol

2026-11-13. **PROPOSAL ONLY; no test bytes, roles, verifier admissions or execution are authorized by this document.** Conditional on fresh Astra's verdict on frozen core948/test1681 and root's later explicit grants. The prefix author currently owns the source-write baton. This document adds only prose/metadata and does not reopen adopted DESIGN-FIX1.

Frozen implementation facts: core SHA256 `ed8df0b56707baa08d46dd3422b91521bbe15a02c187643cc360a565e3c8372e`, test SHA256 `ccc74e6bac55f322d3363ac1e19c820b2b97b0d86839b392dfabedb452647a38`. Current report SHA256 `0f3453e817e4af6fb2167354e3fa80f19243777e227ce2cf104cab138c423116`. Root R106 binds tree `ab46784efc86bab95b031494529e06871a12f1ff`, manifest `12e5609bf4f300e608ebd6f94297fd0f2496bf95169e757864cb6ad50fbd0970`, and 76 existing unique passes. Those results do not qualify the new schedules below.

## Source-verified facts versus proposed tests

Source-verified in the retained core: `_invocations` is a WeakKeyDictionary keyed by exact RNGDeviceInvocation. Each `_Invocation` has exactly eight fields: `thread`, `state`, `participant`, `operation_kind`, `lineage`, `cuda_devices`, `context`, `failed_completion`. `thread` stores an actual threading.Thread object; authentication compares its identity with `threading.current_thread()`. Domain `_pid` is compared with actual os.getpid before registry/thread/lock/CUDA access. No new lock acquisition or cache exists in issuance/authentication/getter/release. The actual context is created by the shared contextmanager-decorated `_operation`, with a required private `completion` record argument. Nested completion uses its subset; outer completion uses the final union. Only successful `_complete` return certifies False. Exit finally clears execution references and seals `exited` before outward error delivery. Existing generic first-error stopping and local all-device completion implementations are unchanged.

Every node/case/role/schema addition and event/result below is **proposed**, not an existing source or executed fact. If fresh review changes any fact, freeze the reviewed source, update this plan's source bindings/observations, and reassess the bounded test delta before writing. No external verifier implementation has been read by this worker; its owner must validate exact extension points from its own admitted source.

## Proposed nonpoison nodes

Full node prefix throughout: `tests/test_townlet/regressions/bac/test_rng_cuda_admission.py::`.

| Proposed node suffix | Causal behavior and literal expectations |
| --- | --- |
| `test_device_invocation_nonempty_completion_matches_existing_operation` | On healthy fresh seam, run equivalent existing device_operation and invocation schedules with inventory (0,1,2); compare actual ordered synchronize events. Each performs one phase, no retry. Invocation yields a genuine usable operation, then seals False. Reference/outcome schedules may share a healthy domain because neither poisons; ordinary revision/currency effects must be accounted for, not reset. |
| `test_device_invocation_nested_siblings_keep_lineage_and_receipts` | Parent subset (0), child subset (1), sibling subset (2), using genuine enrolled owners. Three distinct handles yield the same real parent operation; child/sibling False results stay independently readable while parent is active. Literal sync order: child1, sibling2, outer0/1/2. Parent False follows its actual union phase; subsequent healthy work and retirement cannot alter any result. |
| `test_device_invocation_nested_currency_preserves_currentness_rules[device_operation]` | Reference route reproduces the retained real-token rule: nested ordinary work inside open prepare has existing behavior; ordinary sibling after prepare makes the genuine token stale. No private currentness fabrication. |
| `test_device_invocation_nested_currency_preserves_currentness_rules[device_invocation]` | Same genuine participants/tokens/lineage and literal validation/refusal points through invocation contexts; exited child receipts remain False and do not restore token authority. |
| `test_device_invocation_thread_object_rejects_numeric_alias` | Real issuer thread A completes an empty invocation, then terminates. Real thread B, demonstrably a different actual Thread object, calls enter/exit/getter and receives ValueError before held locks/CUDA. Deterministically alias only the custody module's numeric-ID dependency through a forwarding threading proxy: proxy.get_ident returns A's captured real numeric ident, while proxy.current_thread forwards to the untouched actual threading module. Never patch the actual threading module, current_thread, PID or thread records. Thus B's identity remains genuine even if its real OS ID happens to differ/recycle. This is a controlled numeric-alias regression control, not a claim that the OS reused an ID. A numeric-only authentication mutation would fail the test. |
| `test_device_invocation_registry_lifetime_and_lock_paths` | Direct finite record/state observations plus the genuine RLock forwarding probe described below. Cover issued, entering at the actual inventory seam, active, exiting while completion is held, exited, and entry_failed; refusal/read paths preserve their scalar snapshots. No private record is inserted or changed to manufacture authority. |

Each test uses the existing genuine sole process domain and real weak owners/participants. Every owner registration is paired with cleanup or actual weak-owner retirement. Keep NoCUDA on empty inventory paths; use CUDASeam only at actual runtime/query/synchronize boundaries. Never clear/reset common poison, membership, generation, revision or currency. Preserve every current node and the empty production-manifest assertion. These controls do not consume producer implementation or decide producer quarantine policy.

### Authentic alias and observation prerequisites

Before aliasing, create the handle on real A and complete it there; capture A/B actual objects through the unmodified threading module and retain only the finite references needed for the test. Construct/start/join threads through that untouched module. Install the proxy only on `custody.threading`, with forwarding for all non-overridden attributes; the registry still receives/compares actual Thread objects. Assert real PID unchanged; prohibit CUDA and hold actual domain/owner locks while B attempts methods. Restore the module reference in unconditional fixture cleanup, use bounded events/joins, and collect every thread exception. A failure must not strand a lock-owning live thread.

For direct registry observations, freeze immutable scalar tuples: key id, record id, id(thread), state, participant id, kind value, lineage id, exact devices tuple, context id, and failed_completion. Observe all eight actual fields and registry membership/weak-key expiry; do not retain the context, generator frame, owner, operation or exceptions in a supposedly non-retaining snapshot. For a live actual context, inspect its actual generator/frame reference at the qualified observation point and record only scalar identity of its `completion` argument and context/generator state; discard frame/local references immediately. The expected completion reference is the same actual invocation record, not its handle. Verify post-exit/entry-failed execution fields are None/empty; completed record retains its genuine issuing thread/state/result, and weak registration disappears when the handle is collected. No proposed field is substituted for an absent source field.

Re-enumerate actual acquisition paths against reviewed source before zero-counter claims. Retain the existing LockProbe forwarding the same genuine RLock, including acquire/restore and ownership methods. Count factory issuance, pre-entry/active getters, lifecycle refusals, wrong-thread methods and repeated post-exit reads separately; these paths must acquire neither domain nor owner exclusion and touch no CUDA. Actual successful enter/exit is expected to traverse the existing shared-operation exclusion paths; compare its event trace with device_operation rather than demand zero. During actual completion, getter must still refuse; after outward error handling begins, the outcome must already be sealed. A new source cache/acquisition introduced by review invalidates this enumeration until corrected.

## Proposed isolated case/role/node/message map

Each row is one independently captured root job with workers=1 and one fresh qualified spawned child. No two poison schedules share a domain/process, and no state reset combines them. Existing `CHILD_CASES`, old nodes/roles/messages and guard-only trial records remain intact. Proposed target for these exact additions is the retained `cuda_core_child`; no generic unknown-role/prefix allowance is proposed.

| Proposed case | Proposed exact role | Proposed node suffix | Proposed exact queue message |
| --- | --- | --- | --- |
| `invocation_same_error` | `cuda_core_invocation_same_error` | `test_isolated_poison_protocol[invocation_same_error]` | `cuda core invocation_same_error fail closed` |
| `invocation_child_failure` | `cuda_core_invocation_child_failure` | `test_isolated_poison_protocol[invocation_child_failure]` | `cuda core invocation_child_failure fail closed` |
| `invocation_parent_failure` | `cuda_core_invocation_parent_failure` | `test_isolated_poison_protocol[invocation_parent_failure]` | `cuda core invocation_parent_failure fail closed` |
| `invocation_reported_failure` | `cuda_core_invocation_reported_failure` | `test_isolated_poison_protocol[invocation_reported_failure]` | `cuda core invocation_reported_failure fail closed` |
| `invocation_phase_reference` | `cuda_core_invocation_phase_reference` | `test_isolated_poison_protocol[invocation_phase_reference]` | `cuda core invocation_phase_reference fail closed` |
| `invocation_phase_failure` | `cuda_core_invocation_phase_failure` | `test_isolated_poison_protocol[invocation_phase_failure]` | `cuda core invocation_phase_failure fail closed` |

**OUT-SAME-E / invocation_same_error.** First complete a body-only error E with successful actual phase: outward error is exactly E, receipt False, no poison. Later in the same still-healthy child, body raises that same E and its own completion raises the same E: outward dedup still exposes exactly E, receipt True sealed before handling/unlock, actual sync events prove both phases ran. The second schedule poisons; no later ordinary admission is fabricated. A mutation deriving the result from exception identity cannot pass both observations.

**OUT-CHILD-FAIL / invocation_child_failure.** Real parent and child handles yield the same genuine lineage. Child's actual subset sync fails once; parent's own later union sync succeeds because the seam's finite schedule fails only the child's call. Child True, parent False, original error propagates and common poison remains. Attempt a later sibling entry after child failure, while parent is still active: refusal has no body/completion and no readable outcome. Never manufacture a successful sibling after poison.

**OUT-PARENT-FAIL / invocation_parent_failure.** Two child/sibling scopes complete successfully, seal separate False outcomes, then parent's actual outer union phase fails. Child/sibling False values remain unchanged; parent True. Keep the actual owner lock through phase exit and result read with a deterministic mutation contender blocked until release; record sealing/read ordering. This proves core phase attribution and lock-compatible reads only. It does not identify production affected owners, designate the parent consumer, or authorize blanket quarantine; the separate real parent packet owes those decisions and cross-interface controls.

**OUT-REPORTED / invocation_reported_failure.** Before poisoning, one invalid pre-entry inventory attempt must have no body, synchronization or outcome. Then a real active invocation reports a gate error through an authentic admission gate and raises the same body error as appropriate; its own actual synchronization succeeds. Receipt False, existing propagated error identity/reporting and poison persist. Do not infer outcome from common poison or reported errors. A later poisoned refusal remains entry_failed/unreadable.

**Completion parity / invocation_phase_reference and invocation_phase_failure.** Both independently start healthy with devices (0,1,2), body E and a distinct synchronization error F injected at1. Reference uses existing device_operation; counterpart uses invocation. Compare their captured actual phase event sequences and ordered outward leaves [E,F]; counterpart result True. Record the actual current trace, but compare equality rather than codify an unvisited device2 tail as a permanent public requirement. Neither receipt adds a retry/second phase. Successful nonempty completion is covered by the nonpoison node. Separate reference/outcome children avoid poison-reset fiction.

Every poison child ends by proving common domain poison persists and ordinary admission/work still refuses. Parent process must remain healthy and its Python/NumPy/Torch CPU RNG snapshot unchanged. Core owner-lock contenders test actual lock ordering/read visibility without claiming a production quarantine response.

## Proposed strict-verifier schema changes

Retain the existing bootstrap/source-manifest/import/process identity schemas and existing four-element queue message shape for all old roles. Add only the six exact case/role/node/message/target bindings above. The external verifier owner must match each to frozen authored test bytes and its actual source before accepting them; these proposed labels alone confer no admission.

For the two parity jobs only, propose one separate child-produced artifact, so cross-job comparison uses observed data rather than a literal implementation tail: `invocation-phase-{role}.json`, schema exactly `cuda-core-invocation-phase-v1`. Exact key set:

`schema, role, case, pid, ppid, base_commit, candidate_tree, manifest_sha256, source_sha256, devices, synchronize_events, exception_labels, completion_failed`.

`source_sha256` has exactly keys `townlet.exploration.rng_custody` and `test_rng_cuda_admission`, bound to actual loaded module paths/source receipts. `devices` is [0,1,2]. `synchronize_events` is the observed ordered list of integer device indices, never a prefilled expected list. `exception_labels` is the literal semantic identity order ["body","synchronization"], with actual object-identity assertions performed inside the child before recording. `completion_failed` is null for reference and true for invocation. Other metadata must exactly match the qualified child/manifest/source receipts, including actual child PID and parent PPID.

Only these two newly admitted roles may emit that exact artifact/schema. Their existing parent observation is extended by exactly `invocation_phase_sha256`, the hash independently read by the parent after successful owned child termination. The external verifier compares paired event arrays and metadata/source bindings across their two separately qualified jobs; it must reject missing/malformed/extra fields, wrong role/case/source, swapped/tampered receipt, parent/hash mismatch, wrong null/true outcome and unequal parity events. Prior-role observations retain their exact schema and cannot gain optional unknown fields. This is a proposal requiring owner review, synthetic rejection controls and root grant before any tool or protocol edits.

All six new jobs retain the existing qualified bootstrap/child_identity path, exact imported module identities and source hashes, actual spawned child PID/PPID, process exit status, queued PID/PPID correlation, manifest/base/tree bindings, configured Torch thread profile, clean parent ambient snapshot and parent domain health. Preserve ordinary unqualified test behavior without treating it as equivalent qualified evidence. Keep owned deadlines, termination/reaping and queue/process cleanup; no inherited poison or domain clone supplies freshness.

## Proposed real inherited-PID invocation trial

Preserve existing isolated parent node `test_isolated_inherited_pid_gate_refusal`, spawned role `cuda_core_inherited_pid`, target `inherited_pid_child`, four-element final queue tuple and exact final message `cuda core inherited pid gates fail closed`. Extend only its finite guard-only trial set from admission/local to admission/local/**invocation** after independent verifier review. No new generic fork executor or broad trial acceptance.

Prepare authentic completed and active empty-inventory handles in the qualified spawned child **before fork**. Complete the historical handle normally; keep the other handle actually active with the real domain and owner locks held. The invocation trial has exactly five action keys:

| Proposed action key | Actual pre-fork object/action |
| --- | --- |
| `active_enter` | Active handle.__enter__ |
| `active_exit` | Active handle.__exit__(None,None,None) |
| `active_completion_failed` | Active handle.completion_failed |
| `completed_completion_failed` | Completed historical handle.completion_failed |
| `domain_device_invocation` | Fresh factory call using authentic participant, ordinary kind, lineage=None and empty tuple |

Every action in the actual fork grandchild must raise exactly builtins.RuntimeError with exact text `RNG custody cannot be inherited by another process`, before registry/thread/lifecycle refusal. Require zero actual domain/owner acquisition, CUDA access and body calls; before/after direct state must include the new eight-field invocation registry/execution-context observations as well as existing state. No fake PID, generic-exception acceptance, Torch/NumPy call, import, queue use, CUDA work or inherited-scope unwind is permitted in the fork child.

Retain the exact existing `cuda-core-fork-guard-identity-v1` / `cuda-core-fork-guard-observation-v1` and `linux-fork-inherited-guard-only-v1` shapes, extended only for fixed trial `invocation` with the five exact action keys. Proposed files: `fork-identity-cuda_core_inherited_pid-invocation.json` and `fork-observation-cuda_core_inherited_pid-invocation.json`; exact acknowledgement message `cuda core inherited pid invocation fail closed`. The spawned-child final message remains unchanged. Preserve actual single-OS-task precondition, actual grandchild PID/PPID/inherited domain PID, immutable loaded-module/source/manifest/base/tree bindings, identity/observation hash correlation, owned pipe payload bounds, ten-second deadline and reaping. External strict verifier must require all three trials with exact actions once the new protocol is admitted, and reject missing/new/renamed trials/actions and tampered provenance. Old two-trial evidence remains valid only for its old scope.

## Line budget and ordering before a future write

Measured starting bodies: core948 + test1681 =2629. Current test ceiling2000 permits only319 added lines. Estimated finite additional test code, including reuse of existing child/bootstrap/fork machinery:

| Proposed work | Estimated added lines |
| --- | ---: |
| Healthy completion/nested/sibling/token controls | 80–110 |
| Genuine thread-object/numeric-alias control | 40–60 |
| Direct registry/generator/lock observations and checks | 50–75 |
| Six isolated case branches, finite event schedule and parity artifact | 170–220 |
| Fixed invocation fork trial, prepared handles and action mapping | 55–80 |
| Case/role lists, parameters and parent parity receipt linkage | 30–45 |
| **Total** | **425–590** |

Expected test total2106–2271 exceeds ceiling2000 by106–271; it must not be squeezed by dropping required controls, hiding code in another body, or editing past the ceiling. **Concrete root reslice needed before writing the complete phase.** Proposed reservation: keep core1250, raise this test ceiling to2350, paired reservation3600, two bodies; this is below the unchanged hard five-body/5000-line budget. It changes the prior prospective paired3250 reservation and therefore needs root's explicit recorded reslice, not an implicit worker decision. Alternatively root may stage a first bounded subset below2000 and grant the remaining reslice separately, preserving exact frozen stage evidence. External verifier implementation has its own owner/budget; no third implementation-body read is authorized here.

Required sequence: (1) receive fresh source-review verdict and resolve any actual defects through its owned tests-first route; (2) root grants test-only stage and explicit budget; (3) author/freeze exact nodes/cases/fields and measure actual lines; (4) external verifier owner reviews/implements the exact finite map and rejection controls under a separate grant; (5) root captures exact source/tests/tools/specs and runs collection/healthy prerequisites before the new jobs, each poison child in one worker1 job; (6) independently qualify generic/strict custody, parity pair and fixed invocation fork trial; (7) root publishes exact-scope disposition. No rollout to B, parent integration, hardware or package closure follows automatically.

Unresolved source facts: fresh Astra verdict may require code changes; external verifier extension points/strict schema implementation are not in this worker's admitted bodies; actual new test/protocol bytes, line counts and event receipts do not yet exist. Actual parent owner/device reachability and designated parent-outcome consumer remain separate admitted-owner work. These are concrete pending boundaries, not reasons to redesign the accepted core API or broaden this finite packet.
