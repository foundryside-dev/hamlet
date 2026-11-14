# Native failed-owner diagnostic capture facts v1

2026-11-14. Prose-only source clarification for root, C1 implementation and C1 diagnostic review. This addendum records already-verified behavior; no new implementation body, application import/runtime, test, source/API/APP edit or Git operation. Charged source budget remains four bodies/4,842 lines. No qualification or capability change.

This supplements [the original native supplier](T18e-R0-PARENT-NATIVE-CURRENT-SUPPLIER.md), SHA256 `7cb54762da2ecffae75091d06725afac71d83097f615cd364fc79ed1f54f0ba9`, which remains unchanged. The separate [completion-count clarification](T18e-R0-PARENT-NATIVE-COMPLETION-COUNT-ADDENDUM.md), SHA256 `06ea10d29fdc5ebe2537b0a4ddda6410a1e431cd2fc5cb888b8c5d920032468e`, still applies.

## Exact correction

**A failed native callback latches owner-local failure, but a later native diagnostic snapshot/capture does not necessarily refuse.** `OwnedWorldBackend.snapshot_with_capture` has no `_failed` entry guard. Its later successful return contains `healthy=False`. Private `snapshot` and shared `snapshot` likewise expose the owner-local health value without rejecting solely because that value is false. They still require usable core admission and all ordinary lifecycle/private-frame checks.

By contrast, private and shared managed `call` explicitly reject an already-failed owner before invoking the supplied callback. Therefore a test must not assert that a later genuine native capture itself refuses merely because an earlier capture callback failed. Additional BANK-level policy must be established from the actual BANK caller; no such policy is inferred here from an opaque supplier capsule.

## Source behavior and side effects

Line references W below refer to `world_curiosity_state.py` at the seal recorded below.

| Public method | Failure and later-entry behavior |
| --- | --- |
| `OwnedWorldBackend.call(operation: Callable[[Any, WorldRandomSources], Any], *, lineage: RNGOperation | None)` (W999–1013) | Enters owner scope; rejects `_failed` at W1002–1003 and noncallable input at W1004–1005, both before its guarded callback region. Inside that region, activates the private service stream, invokes the callback with actual provider and sources, and owns its result. Any escaping callback/copy/activation error latches owner failure; revision advances in `finally`. Subsequent managed call refuses before callback invocation. |
| `OwnedWorldBackend.snapshot(*, lineage: RNGOperation | None)` (W1015–1030) | No failed-owner entry guard. Captures copied native checkpoint and private RNG state, returning `healthy=not self._failed`. Escaping guarded errors latch failure; revision advances. A later successful snapshot of a locally failed owner can return `healthy=False`. |
| `OwnedWorldBackend.snapshot_with_capture(capture: Callable[[Any], Any], *, lineage: RNGOperation | None)` (W1032–1058) | No failed-owner entry guard. Noncallable capture rejects at W1039–1040 before its guarded region. Under private service activation it first copies the native checkpoint (W1043), then invokes and owns the capture result (W1044). A capture callback that delegates real capture and then raises a sentinel reaches the catch at W1054–1056: failure latches and revision advances at W1057–1058. Later successful capture can run and returns `healthy=False` at W1048. |
| `SharedWorldBackend.call(operation: Callable[[Any], Any], *, lineage: RNGOperation | None)` (W1252–1264) | Rejects already-failed owner at W1254–1255 and noncallable input at W1256–1257 before its guarded region. Callback/copy failure latches failure; revision advances. Callback receives only the actual provider. Subsequent managed call refuses before callback invocation. |
| `SharedWorldBackend.snapshot(*, lineage: RNGOperation | None)` (W1266–1278) | No failed-owner entry guard. Returns copied checkpoint with `healthy=not self._failed`; guarded failure latches failure and revision advances. |

All these methods enter `_scope`: common domain operation precedes owner RLock; private-frame quiescence and lifecycle reentry checks remain in force (W907–924). Core admission checks usable domain before the native method body. A poisoned domain therefore refuses even a diagnostic snapshot/capture; returning an unhealthy envelope is not a local-after-poison escape route.

Private `call` and snapshot/capture use service activation. On callback failure, activation still attempts to capture the selected private continuation and restore/verify ambient state (W798–852). No callback mutation or private draw rollback is promised. Shared `call` has no private activation or ambient-preservation wrapper: prior callback mutations and global RNG draws remain. Cleanup/completion failures may add errors and poison according to existing native/core rules. If cleanup and core completion succeed, the original sentinel propagates by identity; the callback-induced owner-local latch remains distinct from completion uncertainty and is not cleared by successful completion.

Prior failed-owner/noncallable rejection occurs outside each method's guarded callback region as specified above, so it does not itself execute that region's revision increment. Core operation bookkeeping/completion still follows its own entered-scope rules. This distinction is not permission to infer mutation counters from an exception class alone.

## Safe current-API recipe

1. Use the authentic existing owner at the public native invocation seam actually exercised by the test. Preserve the exact supplied `lineage`: explicit None only for standalone admission, genuine current `RNGOperation` under an ancestor. Do not fabricate lineage, substitute a foreign child, access private health fields, or obtain authority through raw provider references. The opaque BANK capsule supplies no public accessor to its native children.
2. At a genuine private `snapshot_with_capture` call, adapt its real capture callback so it first invokes the original read-only capture on the supplied provider, then raises a chosen sentinel. Discard the captured result without retaining provider/module aliases. Preserve the read-only capture contract: no lifecycle operation and no retained live aliases. The real native checkpoint copy and real capture precede injection; this is not a synthetic capture bypass.
3. With successful cleanup/completion, assert the exact sentinel escapes. While the domain remains usable, an ordinary public snapshot/capture may establish the owner-local result by returning `healthy=False`. A subsequent genuine managed `owner.call` must refuse before its callback runs. **Do not use later capture refusal as the native-only oracle.** If checking BANK propagation, assert only the extra behavior actually implemented at the real BANK caller.
4. For private managed-call injection, the callback signature is `(provider, sources)`; for shared managed-call injection it is `(provider)`. Delegate the actual intended callback work before the sentinel when that causal prefix is the behavior under test. Observe failure through public results/refusals, never by editing a private latch or exporting the provider.
5. Keep body failure and completion uncertainty separate. A healthy own/parent completion must not erase an existing child-local failure. Under core poison, assert admission refusal before diagnostic callback execution; do not bypass poison to obtain a `healthy=False` envelope. Additional cleanup/completion failures retain the established exception aggregation rather than a forced sentinel-only expectation.

These are prospective test instructions, not tests executed by this supplier. They do not establish the full BANK trace or any uninspected provider's internal callback behavior.

## Source seals

All four original source hashes were rechecked during the preceding read-only clarification and matched. Only already-charged W regions were reread; no fifth body was opened.

| Source under `src/townlet/exploration/` | Whole lines | SHA256 |
| --- | ---: | --- |
| `world_curiosity_state.py` | 1361 | `433b3563457fbf68d26d47d73dc375c1382e0cc77d0987a4c9d4f62f3cdfcce3` |
| `curiosity_checkpoint.py` | 1158 | `b45ba7627b50c123de36862a678a8db98d4ab074db23d296b6cd81a05d74b6c1` |
| `rnd.py` | 1128 | `53cccad55acad4018518bd498206129feddc5f54113560103cab60c94659ac46` |
| `rng_custody.py` | 1195 | `6cb01ca77b58db5f4c4784dc36da566c06cf68c2a7c2ce227bb780549f3344f8` |

Relevant already-inspected core references: usable-domain check C412–415/1042–1044; nested completion C1081–1091; `_finish` C530–541; exception identity/aggregation C544–576. Original supplier source/copy/inventory limitations remain in force.
