# C1 failed diagnostic supplier contract v1

Status: source-owned design addendum, not implementation authorization or executable acceptance. No APP changes or runtime execution performed for this addendum. The proposed capability preserves full actual failed-state diagnostics while keeping training, normal checkpoint transport, and diagnostic resume fail-closed.

## Exact source boundary

Reverified unchanged sources on 2026-11-14. Paths are relative to `/workspace/hamlet`.

| Source | Lines | SHA-256 |
|---|---:|---|
| `src/townlet/config/exploration_policy.py` | 1313 | `50a738825ae151cbf7a2907660e4cd06df7e42ae78128135eda891b3c6c885f9` |
| `src/townlet/exploration/scoped_curiosity.py` | 1443 | `55e0ac73ed65932aaf19c0622c8f11c5bb3801fda8957492ccf513d270a104b4` |
| `src/townlet/exploration/parent_custody.py` | 239 | `1b911c653ed1b1738c4de19b646bd1965cc0825b6f85e814e5ba25a43e02944f` |
| `tests/test_townlet/regressions/bac/test_runtime_bank_parent_custody.py` | 854 | `ca3b0fd10c1fb49e508237901054dd655c9df34fea3745592c216e6c4d5ad5bc` |

These are the existing four bodies, 3849 lines. The already retained independent probe adds 64 lines: reviewer inventory 3913 lines / five bodies. No additional POP, native, checkpoint-codec, core, ENV, or replay implementation body was read. Native child guarantees below are supplier-qualified by `T18e-R0-PARENT-NATIVE-CURRENT-SUPPLIER.md`, SHA-256 `7cb54762da2ecffae75091d06725afac71d83097f615cd364fc79ed1f54f0ba9`; POP ordering is attributed to root and its POP reviewer, not independently read here.

## Current behavior and the precise gap

Runtime `quarantine_episode` (1009) forwards the reason unchanged. BANK `quarantine_episode` (930) authenticates the accepted episode, permits exactly `empty_participation` or `runtime_failure`, retains the exact accepted object and reason, sets `_failed`, and advances mutation revision. Repeated notification must match both. It does not call `_healthy`; genuine domain admission and own completion still surround it.

Runtime `checkpoint_state` (1174) first owns cadence, calls selector checkpoint, and validates their relation; then it delegates BANK checkpoint. Therefore BANK refusal is not a promise that runtime did no prior work. BANK `checkpoint_state` (1023) has one entry `_available()` (1027), which refuses `_failed` or `_completion_uncertain`, and refuses a pending completion transaction. `snapshot_world` (942) has the same availability gate. Neither is an existing failed diagnostic escape.

BANK checkpoint then captures actual child state using `SharedWorldBackend.call` or each native owner's `snapshot_with_capture`, passing the genuine BANK operation lineage. It captures native transport and gradients, each world's cursor and phase cache, policy/descriptor/source device/epoch/origin, actual pending or historical step, dispatch identity, and committed or historical completion. Its `finally` advances mutation revision. `_checkpoint_phase` does not itself encode a failed diagnostic phase. Runtime wraps this with actual selector, cadence, and policy. These managed observations may copy tensors, invoke callbacks and perform completion work; they are not inert metadata reads.

The C1 admission path remains domain before runtime lock before BANK lock. The runtime's delegated BANK scope, single-use forwarding permit, public-call guard, `_operation_active`, and BANK `_entered` guards prevent callbacks from borrowing authority. BANK owns a fresh device invocation for its declared exact devices and retains its lock through that invocation's completion. Its own failed completion monotonically latches `_completion_uncertain` in nonrestored storage. None of these guards provides permission to inspect poisoned storage.

## Finite additive capability

Provide distinct producer-owned runtime and BANK failed-diagnostic methods (names to be settled by the implementation plan), rather than a caller-controlled `allow_failed` option on healthy checkpoint methods. The runtime uses its existing decorated operation and exact `_bank_call` forwarding seam; BANK uses its existing serialized admission and observation boundary. Factor the full transport construction privately if needed so the diagnostic cannot silently omit fields. Existing healthy checkpoint behavior remains unchanged.

The diagnostic BANK entry may bypass only ordinary local `_failed` availability for an actual retained `runtime_failure` quarantine. It must establish the quarantine's exact accepted identity, reject `_completion_uncertain`, retain the pending-completion transaction prohibition, and leave all failure/quarantine flags intact. An arbitrary `_failed` bit, a caller-supplied reason, or a quarantine tuple alone does not prove healthy children or completed work. Genuine common-domain admission and the existing child calls remain authoritative checks; each child must still admit its actual state and finish its own operation. No temporary flag clearing, private parent access, forged lineage, or exception-based fallback is permitted.

For this exact profile—ordinary BANK local quarantine with confirmed completion and otherwise healthy native/core owners—the existing native capture interfaces already provide the required child data. No new native method is needed merely because BANK is locally quarantined: native capture receives lineage, not BANK's `_failed` flag. This is conditional on genuine native admission succeeding, not a claim that every failed POP step leaves those owners healthy.

If native/core ownership is failed, completion-uncertain, or poisoned, retain its existing refusal. Do not catch that refusal and inspect raw provider state. Full export of such states is outside this capability and would require a separate producer design; prior full checkpoint capture already depended on those child APIs succeeding. No after-poison metadata permission can be inferred from the ability to read an operation's own completion outcome.

The returned runtime and BANK diagnostic envelopes must be unmistakably nonresumable, using distinct diagnostic schemas and explicit failure classification. Preserve the full ordinary payload within them; do not relabel a healthy schema as resumable. Normal runtime parsing already requires its exact healthy schema/key set. Require explicit BANK diagnostic rejection at its public restore preparation boundary before materializing a candidate, rather than assuming unseen codec rejection ordering. Normal install accepts only authentic prepared healthy publications, never a diagnostic envelope. Saved healthy-payload standalone recovery already supported by BANK is a separate capability and is not removed by this restriction.

Read-only here means no training update, recovery, or health reset. Existing observation accounting, restore-currency invalidation, managed tensor copies and own completion still occur. Capture failure yields no purported complete diagnostic, retains failure/uncertainty, and does not make subsequent healthy operations available. The POP caller must preserve its original primary failure when capture itself fails, recording secondary diagnostic failure according to its owned error policy.

## POP boundary supplied by its owner

Root and the POP reviewer report that `get_checkpoint_state` must retain its existing 12 outer fields and actual readings. Only its `exploration_state` uses the new nested diagnostic capture on the failed route; the other 11 fields remain the same actual Q/optimizer/replay/progress/etc. readings. No new outer envelope or replay schema is required. No pre-failure cache or summary replaces any field.

They report restore ordering as outer shape/universe/Q/optimizer/replay serialized validation, then `_checkpoint_clocks` failed/in-progress refusal, before parent proof, replay materialization, or runtime restore preparation. The real failed payload must reach that precise failed-progress refusal. Do not claim it refuses before all validation. Nested runtime and BANK diagnostic refusal must also hold independently; the POP guard alone is insufficient authority for a reusable producer export. Q/optimizer/replay completeness, their health checks, and their actual copying/locking remain POP/replay-owner obligations; C1 source inspection cannot certify them.

## Required acceptance and remaining gates

1. An actual ordinary pace/body failure with successful completion quarantines using `runtime_failure`; ordinary runtime/BANK checkpoint and training remain refused. The new route returns all 12 actual POP fields and full nested runtime/BANK state, with actual post-failure Q/optimizer/replay values and diagnostic markers.
2. The unchanged failed payload reaches the exact POP failed-progress receiver refusal. Runtime and BANK healthy loaders separately reject their unmodified diagnostic envelopes before candidate materialization; no flags or latches reset.
3. Actual shared and per-world child capture preserves all supported policy-family state, gradients, counters, private RNG transport, cursors/caches, and pending/history/completion payloads. Do not qualify completeness from a metadata-only assertion or synthetic provider replacement.
4. Native/core failed, uncertain, or poisoned cases retain genuine refusal; no fresh raw tensor inspection occurs after uncertainty. Diagnostic body or completion failure yields no complete success, preserves the primary failure at the caller, and maintains each owner's own completion attribution and monotonic latch.
5. Existing callback authority, exact lineage/thread/PID checks, domain/owner lock ordering, observation invalidation and scope lifetimes remain effective for the new methods, including direct BANK callback attempts and competing threads.

This is a source-consistent additive design, ready for a bounded implementation proposal, not a claim that tests pass or full C1 integration is accepted. Root must assign an exact writer/reviewer packet and executable schedules; do not assume expanded test work fits the prior 900-line test ceiling without measuring it. Wider required owner failures and integration gates remain separate, required work.

No capability removal is proposed and no John approval is needed merely to retain full diagnostics through a safe producer API within the authorized goal. Replacing the full failed payload with a summary, a cached earlier checkpoint, or fewer fields would be a capability/payload reduction and needs explicit John approval. Preserving pre-existing native/core unsafe-state refusals is not such a reduction. This addendum grants no implementation authority.
