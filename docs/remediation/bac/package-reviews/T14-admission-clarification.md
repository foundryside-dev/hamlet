# Source provenance

Reviewed design/source-preparation provenance. This document is not executable proof or John approval; source budgets/status in its body are historical where superseded by the final binding and actual qualification.

Original `T14-interface-admission-clarification.md`, SHA256 `6015050b1a95312d019e04646223d6bf7eaef1bf4374d794d5c834fbd4479f43`, retained unchanged. Portable rendering normalizes execution paths.

# T14 admission clarification — supplement to r0

**Correction to r0:** “unsampleable” was too broad. The finite priority vector [1e-6, 1e308] at alpha=beta=1 fails PS weight preflight for B=1, but remains sampleable for successive B=N=2, with all-one weights. The r0 recommendation to apply current-beta B=1 preflight to every priority update would extend the proposal's existing overrestrictive restore/clock/storage admission policy. Do not adopt that recommendation as the resolution: it unnecessarily excludes an accepted P3 capability. The underlying roundtrip-policy inconsistency remains material, but the smallest preservation-consistent repair is to separate probability-support admission from request-specific weight representability.

## Exact source boundary

Only the same four sources remain in scope. In `per_sampling.py`, `_prepare` (68–96) validates positive finite priorities, alpha/beta/law/B, positive scaled scores and full-population normalized probabilities for all requests. Lines87–95 skip beta-weight preflight when beta=0 or successive B=N. `_receipt` (99–117) emits all-one weights for those same cases; otherwise it computes the actual beta-scaled log weights. `_final_weights` (48–55) exponentiates beta times log weights, so it does not require a representable untempered inverse weight when the fractional-beta result is representable. `sample_units` (147–154) is the reusable public boundary. No private API or new PS API is needed.

## Smallest coherent proposed amendment

1. **Persistent admission:** factory/domain/storage/update/restore state must satisfy the closed schema, finite priority reductions/configuration, identities and positive representable probability support. For each changed or restored nonempty domain, reuse public `sample_units` with the recorded alpha/law, **beta=0 and B=1**, on a discarded scratch clone. This is only a support probe: its synthetic beta and receipt are neither installed nor persisted, and it cannot change the recorded effective beta, clock, RNG or algorithm. Prepare all affected domains and max before one install; refuse genuine support/shape/reduction failures atomically. Empty admitted domains need no probe. Structural validation/readiness remain non-drawing.
2. **Weights belong to the actual request:** `sample_batch` alone checks the actual requested B with recorded effective beta, through PS on its staged RNG. A final-weight failure leaves all domains/handles/priorities/max/RNG/clocks unchanged. Successful full-population successive sampling retains all-one weights. Beta0 and fractional-beta acceptance follow PS exactly; do not first construct an untempered reciprocal or apply a sample-max normalization.
3. **Clock/restore coherence:** advancing a valid absolute vector tick installs the valid derived beta even if some future B would have unrepresentable weights. There is no batch size in the clock setter or restore ABI. A clock-only change cannot invalidate probability support because alpha/priorities are unchanged; repeating a beta0 support probe is unnecessary. Restore checks the recorded beta formula/range, then the same beta-independent probability-support invariant, so valid emitted state remains restorable even when a particular later request must refuse. This does not promise every B is serviceable at every beta. Preserve the existing readiness meaning as occupancy/law availability, not universal numerical weight feasibility.

This is a finite amendment to §§1/3/5 and acceptance controls, not a new mode or feature. Current-beta B=1 as a new-buffer admission rule could be specified mathematically, but it is stricter than accepted PS/P3 behavior and is not authorized as a silent capability reduction here. The beta0 public support probe retains exactly the relevant common PS preconditions without imposing a hypothetical B=1 weight requirement on B=N.

## Finite controls for the existing counted regression

- **Positive full population:** valid two-unit priorities approximately [1e-6, 1e308], alpha=beta=1. Accept the atomic priority update, serialize/restore it, and serve successive B=N with exactly one copy of each unit and all-one weights. This replaces r0's suggested rejection of this update.
- **Negative actual request:** on that same accepted state, B=1 at beta1 refuses with a located final-weight diagnostic and no state/RNG change. Independent replacement B=1 has the same expected refusal. A failed request must not prevent later valid successive B=N sampling or roundtrip restore.
- **Positive beta0/tiny q:** both laws at beta0 accept B=1 on the same positive representable tiny-probability vector and return unit weights; prove the receipt keeps positive q and owned RNG isolation. Advancing an annealed buffer to beta1 is permitted; afterward full successive B=N still works and actual B=1 refuses atomically.
- **Positive fractional beta:** the same priorities at alpha1/beta0.5 accept B=1 because the tempered weight is finite (approximately 7.1e156 for the tiny-probability unit), despite the beta1 weight overflow. Preserve a control with alpha0.5/beta1 as well, proving score computation does not prematurely divide priorities before tempering. Assertions must cover preflight for all possible positions, rather than rely on randomly observing the extremely unlikely unit.
- **Negative true admission failure:** retain invalid/nonfinite reductions, malformed identities/masks and restored probability-support loss controls, with all-domain all-or-nothing state and RNG checks. A deliberately forged positive vector whose scaled probability underflows can demonstrate support rejection; if the strengthened epsilon invariant rejects that artifact first, do not falsely call it a support-path witness. The float64 [1e-6, 1e308] example is explicitly NOT a support failure.

## Custody and corrected external receipt

Root now reports one shared HC `_CURRENT_REPLAY_VERSIONS` predicate consumed by two gateways (`_formats`/resolve and `Policy.__post_init__`), not two independent literals. This supersedes the earlier root-supplied “two tables” wording without any HC source read here. Root owns truthful raw POP6 versus planned HC10/7 consumer qualification. Storage admission proof closes neither T24/T25 nor T15/X04/G2.

No runtime, imports, tests, source changes or additional source reads occurred. Only this ignored supplemental prose was written. Proposal and r0 remain byte-preserved; the following identities were checked before and after the supplement:

| File | SHA256 |
|---|---|
| T14-interface-proposal.md | 3fbe22738279e03c9e6f412f64e96b3549b3c5f33d81d947da25c19fb83a86df |
| T14-interface-astra-review-r0.md | 2eb6149fd456d7c0526bc915184ecedd2533939edc7aeac8e930102aee0ae828 |
| src/townlet/training/sequential_replay_buffer.py (1237 lines) | 14196e7109120682476736e927076ca2dcd9926cdda206cac1ab4641189e3ea5 |
| src/townlet/training/per_sampling.py (163 lines) | 0efe801f01a31082aa52c4b9bd40c356d1c97f89690b07c7835b541b7f2c6de6 |
| src/townlet/training/replay_contract.py (222 lines) | 3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c |
| src/townlet/config/bac_options.py (294 lines) | 10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916 |

Source total remains 4/1916; reserved fifth remains absent. This supplement recommends a concrete preservation-consistent amendment, not approval of changed bytes not yet reviewed. Returned stationary.
