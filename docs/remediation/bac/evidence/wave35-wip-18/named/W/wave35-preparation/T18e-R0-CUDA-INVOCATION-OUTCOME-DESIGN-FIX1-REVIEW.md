# Invocation outcome FIX1 — scoped independent re-review

2026-11-13. **SPEC: APPROVED AT DESIGN LEVEL. QUALITY: APPROVED AT DESIGN LEVEL.** The sole prior S1/Q1 overconstraint is resolved. No new material design defect identified in this delta. Root adoption and later actual implementation/source/runtime review remain separate.

Reviewed complete direct `T18e-R0-CUDA-INVOCATION-OUTCOME-DESIGN-FIX1.md`, verified SHA256 `e18de5be6abaa11c1e2ba14929a917ca547c2e41b349dd9102c2ea49cf55c723`, against immutable original proposal SHA256 `168205f55695cc0833a6a1b90bd6d9c5e7953ed89c21ad039861aaf4d695f7a8` and peer review SHA256 `21e81894bc0ccf611e4caab372492e4bb085911ce93837f4a2a1bb3b0d045872`. A prose diff confirms changes are confined to the fix record, generic-completion paragraph/test3 and explicit parent-outcome handoff section.

Retained source remains core821/test1409, total2230, with source seals `0a0f19d37ac85b1584ea028e7e7268a04d18e9f39db0e41b9780181913aae477` and `b044538dfe656976c0171d81fae4c3d44bba9b47f8b5072d846cfe2d9acf962e`. No new source body/read, application import/runtime, source edit, Git/index/branch/worktree/copy or delegation. This review is the sole authored artifact.

## Prior finding resolved

The revised completion paragraph preserves the existing shared generic implementation in this packet, forbids receipt-induced retry/second pass and labels current early stopping as a source fact rather than a permanent public outcome guarantee. Revised causal test3 checks failed-phase certification/sealing and parity with existing `device_operation`, explicitly removing the independently required unvisited-device2 tail. It neither expands generic cleanup solely for the receipt nor restricts a separately justified future strengthening. The local completion all-declared-devices-after-error obligation remains explicit and unchanged. **S1/Q1: addressed.**

## Preserved API and lifetime

The exact required `device_invocation` arguments, opaque `RNGDeviceInvocation` type, authentic `RNGOperation` context yield, LiteralFalse/no-suppression exit and bool outcome surface are unchanged. The identity-keyed weak source registry, real PID-first and issuing-thread-object authentication, single-use lifecycle, immutable post-exit historical reads and termination reference cleanup remain binding. No active/entry-failed handle can claim a completion result, and historical reads do not revive expired operations or tokens.

Own-phase attribution still distinguishes standalone outer-union completion from each nested subset even though nested invocations yield the same parent lineage. Failure marking remains independent of body/exception identity, reported errors and common poison; clean body failure with successful completion remains False, including the same-object error ambiguity that motivated the addition. Existing exclusion, membership, pins, currentness/revision and poison rules remain unchanged through shared implementation. No new public callback, registrar, receipt authority or compatibility path appears.

## Explicit parent handoff boundary

The new section correctly preserves a child's sealed False when later outer-union completion fails. It leaves actual affected-owner/device-effect reachability, the responsible parent-outcome consumer and justified transitions under the already-held locks to the bounded parent integration packet. It adopts no blanket quarantine, per-device receipt API, child-result reinterpretation or new core policy.

The cross-interface parent schedule and successful-parent/unrelated-owner controls make that existing producer obligation explicit. Parent CUDA integration cannot claim closure before its real handoff is decided and verified; independent constructor/CPU controls can proceed without pretending to qualify it. This is consistent with the original producer-owned lock/quarantine boundary and source facts, not a new parent implementation hidden in the core receipt.

## Remaining boundary

No further design amendment requested in this scoped round. Root may adopt FIX1. Actual bounded code must still prove source issuance, state/lifetime/reference cleanup, real PID/thread/probe order, exact public/owned types, shared-operation parity and causal producer use. New child roles require independently reviewed verifier admission. Parent integration, real GPU effects and B6/programme closure remain open; no implementation or runtime pass follows from design approval.
