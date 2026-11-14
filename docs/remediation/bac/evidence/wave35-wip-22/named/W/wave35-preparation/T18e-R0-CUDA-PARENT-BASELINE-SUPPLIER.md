# Parent spawn baseline — exact current core public facts

2026-11-13. Supplier prose from retained core821, SHA256 `0a0f19d37ac85b1584ea028e7e7268a04d18e9f39db0e41b9780181913aae477`. No new implementation body, source edit, application import/runtime, copy, Git/branch/worktree action or delegation. No test/helper body or callable is supplied here.

## Status is a positional diagnostic tuple

Exact public signature: `AmbientRNGDomain.status(self) -> tuple[int, int, bool]`; call `process_rng_domain().status()` with no arguments.

| Position | Meaning | Type |
| --- | --- | --- |
| `0` | membership `generation` | `int` |
| `1` | operation `revision` | `int` |
| `2` | common-domain `poisoned` (`True` means poison exists) | `bool` |

It is an ordinary tuple, not an object with named fields. A healthy diagnostic check is `domain.status()[2] is False`. The method holds the real domain lock and drains idle weak retirement, which may legitimately advance generation. It exposes no currency, READY, RNG snapshot, poison cause or completion attribution and grants no admission authority. It is suitable for a standalone diagnostic with **no owner lock held**; do not assert the entire tuple is unchanged around separately admitted baseline operations.

## Supported healthy standalone custody for direct state reads

Use existing real public membership/operation APIs, with no owner lock held on admission:

1. Retain a real weak-referenceable baseline-owner instance strongly through both parent snapshots and the child launch. Plain `object()` is not weak-referenceable; the test must provide its genuine small lifetime owner.
2. Register it once: `domain.register(owner=owner, cuda_devices=indices, entrypoints=frozenset({'baseline'}))`. Here `indices` is the exact sorted/unique tuple of already initialized CUDA devices whose state the test actually intends to observe; `()` is the CPU-only inventory. Nonempty registration requires initialized valid indices and never initializes CUDA. The core does not discover which individual CUDA RNG states are already initialized.
3. For **each** before/after snapshot, enter `domain.operation(participant=participant, operation_kind='baseline', lineage=None)` and author the direct state reads inside that actual operation. It yields authentic `RNGOperation` lineage; no helper is needed to enter it. This requires the issuing thread to be idle and the common domain healthy. Completion finishes at scope exit. Keep the baseline owner alive until both snapshots/child work finish.
4. Finally call `domain.unregister(participant=participant)` under healthy idle custody. Check parent health separately via status. A baseline capture failure remains a real failure; the test must not reset poison to continue.

`'baseline'` is the explicitly registered ordinary entrypoint name in this recipe, not a special core mode. Each standalone operation advances normal core revision and ordinary-work currency; registration/unregistration change generation. These expected bookkeeping effects do not mean the observed RNG bytes changed. Compare the independently owned Python/NumPy/Torch state values, not equality of the entire status tuple. Empty registration/operation/completion accesses no CUDA attribute in the core.

Do not call `resolve_cuda`, bootstrap or enroll an unknown device just to build a parent baseline: those can legitimately initialize/invalidate state. `admission(lineage=None)` alone is only an exclusion gate and grants no RNG operation authority. The actual registered operation above is the supported ambient custody surface.

## No hidden RNG-state helper

Current `rng_custody` exports no Python-random, NumPy-global, Torch-CPU or CUDA get/set/snapshot helper. Its known public API supplies custody, membership, tokens, diagnostics and gate/device protocols. This supplier has not supplied an existing callable for capturing/asserting parent ambient state. The producer test must explicitly author its allowed direct public-state reads/copies/comparisons and include only already initialized CUDA state, as root instructed. Signatures or semantics of another test's private helper cannot be inferred or imported from this capsule. No core private state, fabricated token, guessed helper or future invocation-outcome API is required for this healthy parent baseline.
