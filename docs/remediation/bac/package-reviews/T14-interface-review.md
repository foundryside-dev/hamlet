# Source provenance

Reviewed design/source-preparation provenance. This document is not executable proof or John approval; source budgets/status in its body are historical where superseded by the final binding and actual qualification.

Original `T14-interface-astra-review-r1.md`, SHA256 `37d9bda30b9a7b00f2a084f1c70fb754d16cf293082b43e2892823346a50d2a8`, retained unchanged. Portable rendering normalizes execution paths.

# T14 interface R1 review

**Verdict: APPROVE — scoped technical interface approval of the exact R1 artifact below.** No material P1/P2 defect remains in this bounded proposal review. This approves neither unreviewed implementation nor unrun tests, native integration, dependency qualification or release. No additional permission is implied or requested.

## R1 correction and whole-interface assessment

R1 resolves the r0 roundtrip-policy inconsistency using the preservation-consistent clarification. Persistent admission validates positive representable probability support through public PS at beta0/B1 on discarded scratch RNG; actual sample requests alone validate their recorded beta and B weights. This matches the inspected PS `_prepare`/`_receipt` exceptions for beta0 and successive B=N, and its direct beta-scaled log-weight calculation. It preserves the finite extreme [1e-6,1e308] state, full-population successive all-one weights, fractional-beta support, valid clock advancement and emitted-state restoration while allowing an actual beta1/B1 request to refuse atomically. R0's current-beta/B1 update rejection is superseded, not a condition of this approval.

The acceptance matrix now includes positive extreme admission/roundtrip/fullN, beta0/tiny-q and fractional-beta cases; actual-request weight refusal with unchanged state/RNG; and genuine support/malformed-state refusals without falsely labeling epsilon-floor rejection as support evidence. Its requirement to cover all possible preflight positions avoids reliance on observing an approximately1e-314 random draw. Probability-only scratch probes neither install a synthetic beta nor advance live/source/caller RNG. Clock-only updates correctly avoid redundant probability checks because they do not change alpha or priorities.

The remainder of the complete proposal is coherent with the four inspected sources and accepted P2/P3:

- The explicit additive factory and absolute clock ABI distinguish prioritized storage from existing `for_replay`, where the resolved sampling_mode alone is not a PER discriminator. Required configuration, horizon/provenance and Generator ownership retain T15's producer responsibility; ordinary setter rewinds refuse while explicit restore remains distinct.
- Per-L context keys and globally allocated handles preserve request-owned L and distinguish changes in actual zero-start context under tail eviction. Unchanged contexts retain priorities, changed/evicted contexts retire, clear does not recycle handles, and observational readiness does not materialize domains. Atomic updates cover every affected domain and the running maximum after deterministic duplicate reduction.
- Public PS receipts retain positions/order/q/population/mode/rule and float64 weights, with only the public RC objective label adapted. Stable handles remain separate. Existing SB packing supports the required real lengths, every-real-row masks, anchor/window objectives and independent component presence. T15 still owns real unroll/bootstrap and applying a unit weight once after its objective reduction.
- The closed sequence7 extension preserves exact uniform6, the explicit captured6 active adapter, and historical5 approved-A/inspection routes. Recorded priority/RNG/clocks are restored as state, not compared against the target's mutable sampling history. Existing geometry/history preservation guards remain. The max>=initial and priority>=epsilon semantics address r0's optional precision point without adding a stronger weight-feasibility constraint.
- The five-family portable RNG contract is finite and implementable through named public state interfaces, with complete off-side reconstruction/canonical roundtrip and unsupported-family refusal at the new factory. Actual five-family transport/ownership tests remain required. No runtime or codec success is inferred from prose.

## Consumer boundary: attributed receipt, not extra source inspection

Consumed `T14-HC-native-preparation.md` as the exact root-supplied PUBLIC prose receipt only. No HC/POP source was opened. R1 now truthfully describes one shared current-version predicate consumed by two public gateways; the narrow amendment adds sequential7 while retaining all current/historical families and wrong-wrapper/version refusals. HC classification/owned transport is not full replay or learned-state validation.

The receipt says raw POP save/validate/load uses population6, whereas HC current-wrapper classification uses demo10/population7. R1 preserves that distinction, with no tag rewriting, invented inference-mode loader or invented population prepare API. Explicitly attaching the new public buffer to an otherwise real supported non-PER recurrent population is a bounded checkpoint-codec witness, not automatic authored recurrent-PER integration. Physical relocation/second resave and bounded postload greedy use have accurate claims and preserve the existing consumer.

Crucially, R1 routes complete7/6-adapter support through SB `validate_serialized` and `materialize_validated`, the entry points the receipt says POP actually consumes. Newly introduced uniform/PER target and immutable configuration incompatibilities must refuse in validation/materialization before POP's learned-state writes. Installer guards remain defense at the storage boundary; they are not the first introduction of those incompatibility refusals. R1 makes no universal rollback promise for later exploration/resource installation. This resolves the actual design/implementation boundary rather than assuming standalone storage mode-loader tests prove native behavior.

## Required limits after this approval

T13 is still RUNNING according to the root's dispatch; this review does not query, change or qualify that run. Root may reconcile bounded dispatch scopes now, but tests-first implementation begins only after actual predecessor qualification and root dispatch. Core future context is SB2000/test700/PS300/RC250/OP600 = 5/3850, hard5/5000. The separate consumer receipt reserves HC675/POP1854/SB2000/native-test350 = 4/4879; actual source growth must be recounted and reconciled, including T15/F06, before a context exceeds its limit. Required tests cannot be removed to fit a reservation.

Meaningful causal RED, production implementation, focused/affected owner tests, fresh other-model source review, six standing guards and the mandatory full serialization/public-contract gate all remain owed. Any caused existing-consumer regression requires repair/re-review before release. Full native10/7 identity/dispatch/archive-union accounting, recurrent factory/producer/learner integration, evolved optimizer continuation, inference/resource/RNG guarantees and T24/T25/C07 closure remain their existing obligations. T15/X04 unweighted finite TD telemetry remains required before release/G2. Original66 tasks,22 lenses and54 effective requirements are unchanged. No removal/degradation/consolidation is selected.

Optional P3: none added in R1. Implementation clarity and test adequacy will be reviewed against actual code, not presumed from this approval.

## Exact custody and source inventory

Existing `/workspace/hamlet` only. Observed HEAD `41edeb0858cba98a8dcb6ba2af36355457ef4e0a`. Frozen qualification tree `f88f7cb3e3d0203ab199a2d898e3b0f8370d7e48` is root-attributed; this review makes no new tree/index-equality or gate claim.

| Reviewed/retained artifact | SHA256 |
|---|---|
| wave08-preparation/T14-interface-proposal-r1.md | d6708084cb8bb63ba3febf8860b24a5f8b7a846da609c18ac2988aca35e77239 |
| wave08-preparation/T14-HC-native-preparation.md (attributed public receipt) | b3a5e3e238e25d9ece19dee987bbecd69599539dfbe42c0ecd8cb5b8518868d7 |
| wave08-preparation/T14-interface-proposal.md (preserved original) | 3fbe22738279e03c9e6f412f64e96b3549b3c5f33d81d947da25c19fb83a86df |
| wave08-preparation/T14-interface-astra-review-r0.md (preserved original) | 2eb6149fd456d7c0526bc915184ecedd2533939edc7aeac8e930102aee0ae828 |
| wave08-preparation/T14-interface-admission-clarification.md | 6015050b1a95312d019e04646223d6bf7eaef1bf4374d794d5c834fbd4479f43 |
| tasks/task-T14.md (accepted P2/P3 and own brief) | a49aeff8262be048b59a73a38741242fa02e0bcb1b527ac4fb324f25c0ed5e26 |
| docs/superpowers/plans/2026-11-01-bac-remediation-upgrades.md (byte-frozen approved plan) | 2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1 |

The complete source context remains exactly four implementation files,1916 lines, previously inspected and identity-rechecked for R1:

| Source | Lines | SHA256 |
|---|---:|---|
| src/townlet/training/sequential_replay_buffer.py |1237|14196e7109120682476736e927076ca2dcd9926cdda206cac1ab4641189e3ea5|
| src/townlet/training/per_sampling.py |163|0efe801f01a31082aa52c4b9bd40c356d1c97f89690b07c7835b541b7f2c6de6|
| src/townlet/training/replay_contract.py |222|3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c|
| src/townlet/config/bac_options.py |294|10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916|

Reserved fifth `tests/test_townlet/regressions/bac/test_recurrent_per.py` remains absent. No additional implementation/test/helper source was read; no runtime/import/pytest, code/test edits, index/staging/commit/tracker changes, branch/worktree/project-source copy/deletion or subdelegation occurred. Only this ignored review prose was written. Applicable repository guidance/skills and user preservation/History A precedence are as recorded in r0. No durable rule was saved; no user-only fallback was adopted; the failed rule grants/restricts nothing. Actual project/session instructions and tool approvals govern.

Artifact/source identities above were rechecked after writing this review and remain unchanged. Returned stationary.
