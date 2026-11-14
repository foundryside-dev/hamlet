# Separate recommendation: preserve failed POP diagnostic capability

2026-11-14, `/root/bac_astra_wip22_terminal_review`. Design recommendation only, not implementation approval, amended acceptance, or a change to the sealed R124 REQUEST CHANGES review. No additional APP body opened. Existing charged budget remains4171/four.

## Preserve the actual capability

The historical explicit ruling `P/T18e-FAILED-STEP-DIAGNOSTIC-PRESERVATION.md` (SHA256 `b1660b762476a40a442086397fef63bb11db65c4df3aad17ecf3b0883aad2cd0`) requires the existing public `failed_population.get_checkpoint_state()` route to retain truthful failed-vector diagnostics and actual child state inspection; a genuinely fresh receiver must reject the actual failed payload specifically as failed/in-progress before missing-parent-proof checks. Current POP source still explicitly allows `_has_failed_step_diagnostic()`. Correct BANK quarantine exposes the missing producer capability; it does not authorize removing this supported diagnostic route.

Recommend an additive **failure-specific diagnostic capture protocol**, optionally exposed as `get_failure_diagnostic_state()`, while retaining the existing `get_checkpoint_state()` failed-attempt route as an explicit delegation to it. Do not replace that call with a refusal or remove its assertion without surfacing the capability change. Healthy export retains its separate healthy producer path. The existing truthful `vector_step_progress` property remains useful, but is not a substitute for full diagnostic state.

The full diagnostic must represent all twelve previously exported top-level fields, with current captured values and their actual partial-state meaning:

| Field | Required preserved meaning |
| --- | --- |
| version | Exact current population payload/version identity |
| clock_ledger | All seven actual clocks, including unreached counters |
| vector_step_progress | Actual retained failed vector tick/stage/accepted identity |
| q_network | Current actual Q state, not a pre-step cache |
| optimizer | Current optimizer state, including any partial completed update |
| scheduler | Current scheduler state or its genuine declared absence |
| total_steps | Actual published vector counter |
| exploration_state | Current complete runtime/selector/BANK diagnostic contents under a new producer-owned inspection contract |
| universe_metadata | Existing meter/observation/action ABI metadata |
| target_network | Current actual target state |
| training_step_counter | Actual reached training count |
| replay_buffer | Current actual replay contents and metadata, including retained partial rows |

Do not silently reduce any of these to shape/count/hash summaries. Exact quarantine/failure/completion-uncertainty facts should be added as diagnostic facts rather than cleared to make existing healthy serializers work. An explicit diagnostic schema/envelope is reasonable; the full payload must remain represented. Any changed envelope/field access should be stated in the implementation plan. Keeping the old twelve-field outer representation with component diagnostic tags is another possibility, subject to supplier schema review; this memo does not prescribe an unsafe fabricated healthy child payload.

## Required producer protocol and source-owned limits

POP has no public runtime/BANK method that can currently supply the required failed-state exploration reading. The C1 source reviewer confirms runtime1174 copies cadence/selector state before forwarding to BANK; BANK1023 `checkpoint_state` and942 `snapshot_world` both call `_available`/`_healthy`, refusing `_failed` or `_completion_uncertain`. Proper `runtime_failure` sets failure/quarantine/revision. Neither clearing a latch, changing the reason back, invoking a private serializer from POP nor temporarily bypassing health checks is acceptable.

Request an exact additive producer contract from the current C1 and native owners before implementation: an **inspection-only, non-resumable** runtime/BANK export for a completion-certain ordinary local quarantine. It must retain the applicable admission, owner locks, lifetime and callback protections while owning its returned bytes. It must distinguish local quarantine from common poison or completion uncertainty, validate all required child capture capabilities, and never clear failure, grant lineage, consume restore authority or invoke a recovery path. Reuse of a producer's child serialization logic is only valid after its source owner establishes that reading the current failed native state is allowed. The source reviewer explicitly identified native failed-owner capture, after-poison metadata custody and POP Q/optimizer/replay device inventories as unresolved producer questions. These are real prerequisites, not assumed APIs.

For the actual pace failure, POP already holds a retained failed vector record, returns from its busy window, has advanced clocks and retained replay, and has not sampled/optimized at that injected seam. The intended full export should capture that real cut. The sample-failure variant reaches real replay draw but still no Q optimizer mutation. Broader failures after a partial Q/native mutation must preserve their actual state instead of extrapolating these test cuts. Quiescent ordinary CPU evidence does not grant permission to read/synchronize uncertain CUDA storage after poison.

A minimal API guard should require the same genuine private `_has_failed_step_diagnostic()` evidence and operation-idle/boundary checks as the current route, never caller-provided failed dictionaries. Stage all inspection data without mutations, copying only ordinary supported data through the responsible owner. A failure to capture must remain a failed capture, never a fabricated complete diagnostic. A best-effort unavailable-component artifact may be useful as an additional API, but it cannot satisfy the original full-export capability without explicit approval of the loss.

## Nonresumption and meaningful tests

The diagnostic is an inspection artifact, not a current ready-to-install checkpoint. Keep actual failed progress, and reject it on every normal POP restore/install path before any child publication. If a new schema is introduced, add an explicit failed-diagnostic parser refusal rather than relying solely on a generic version mismatch. Preserve the existing test's intended precise failed/in-progress rejection on a fresh compatible receiver without fabricated parent proof. Component diagnostic transport must not be accepted as a healthy native/runtime restore payload either; each supplying owner must define that boundary.

The existing four partial-failure controls and eight new real-flow cases must remain. Extend the pace control to actually obtain the full diagnostic, verify all twelve preserved fields and owned copies, compare clocks/stage/counters/replay with the reached cut, and confirm runtime/BANK stay quarantined. Verify fresh receiver rejection and unchanged destination owners/bytes. Assert a diagnostic read does not rerun physics, cleanup, sample, optimizer or restore work. Maintain tests for missing/private-unsealed failure refusing the diagnostic route; do not fabricate flags to make the positive case succeed. Preserve actual exceptions and secondary-cleanup notes.

## Explicit approval boundary

This recommendation proposes **no payload removal**. However, implementing only progress/clock summary, omitting exploration or replay, replacing tensors/optimizer state with hashes, using a before-failure cached snapshot, substituting null/unavailable values for previously captured state, changing full export to always refuse, or deleting the receiver nonrestore assertions would each lose a previously supported diagnostic capability. Such a change requires surfacing the exact loss to the user before implementation under the stated instruction. A new diagnostic method by itself is not equivalent if the existing public failed `get_checkpoint_state()` route disappears.

If producers cannot safely provide the full current payload under the relevant failure conditions, keep R124's finding open and state that concrete limit. The accepted quarantine behavior should remain; do not call a reduced artifact a no-loss replacement. Scope the supplier/implementation packets explicitly, preserve the failed R124 evidence, and run the unchanged intended selection after the agreed repair.
