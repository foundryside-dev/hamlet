# T07: Canonical public section loaders

Source change `f18c5f01c096f5a6b2b58a2f8fe97ebd380369a2`; qualified common release `07ce97550cf2f9dae67cb56d1d8014218c39d523`, tree `42bf1b690f523ed2bb8bf47d12f53d00ea6cb93c`.

Public exploration/curriculum loaders now use DeclarationStore's explicit selected-section producer and shared lowering, preserving original DTOs/signatures and training-only/minimal callers. Conventional, renamed and multi-document transports retain located origins. Local/direct selection precedes unrelated sibling validation; strict whole-pack discovery remains strict. Selected family admission does not unnecessarily validate unrelated training families.

Clock lowering distinguishes selected-scope validation, actual symbolic dependencies and optional ancestor evidence for numeric durations. Numeric-only sections remain usable with malformed unrelated ancestors; valid external clock evidence and recognized authoritative variable failures/collisions are retained. No broad catch-all fallback or skipped actual dependency is introduced.

## Verification

112 loader regression cases, 16 existing loader cases within the 42-case current-consumer selection, and all affected combined checks passed. Causal preservation failures in scope/family selection and numeric ancestor admission were reproduced and repaired before fresh scoped review.

The common four-worker repository gate passed **6407 tests, 16 skipped**, with 15 warnings. All six standing guards passed. Full wall time was 1829.68s. Postflight verified all 73 guarded source/document hashes, seven review artifacts, five process identities, 573 configs, seven protected artifacts and the unchanged 14-worktree registry. Only final source release `07ce97550cf2f9dae67cb56d1d8014218c39d523` has the exact tested sum tree `42bf1b690f523ed2bb8bf47d12f53d00ea6cb93c`; intermediate logical heads were not separately full-qualified.

Fresh bounded source/spec review found no unresolved P1/P2 in this package. [The review](T07-independent-review.md), [common binding](T07-common-binding.md) and [wave06 evidence](../evidence/wave06-qualification.json) preserve source identities, causal failures, repairs and commands. The original finding artifacts remain historical. Native proof review is [separate](T12-native-proof-review.md). Source-verified draft SHA256: `21a0c0e71d056f844db8d6b26997b56d7bc933371674ee70138515719128341c`.

## Required remaining acceptance

T32 actual live/evaluator hosting and readiness, T34 lifecycle/cleanup, T36 serialized provenance, integrated native contracts and final common-source acceptance remain REQUIRED OPEN.

This package does not close whole-BAC acceptance. Fresh final design/source reviews, real learning/E2E qualification, coverage, slow/applicable hardware and exact-tip remote CI remain required. CUDA was unavailable; conditional hardware skips are not passing hardware qualification.
