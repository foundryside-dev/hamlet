# T15 actual candidate independent scoped review r1

**Spec disposition: APPROVE inspected repairs, executable qualification pending. Code-quality disposition: APPROVE, no new confirmed material P1/P2 finding. Runtime disposition: PENDING independent selected execution and root campaign completion.** This is not T15 release or whole-BAC completion.

Reviewed frozen HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`, candidate tree `35d10aaf7656b53259eb90b4ff6a9b8199c33842`, manifest `wave09/r1-candidate.json`, and `wave09/r1-main-review.diff`. Compared the R0 and R1 patch contents and checked changed source bodies directly. Read `T15-repair-r1a.md` and `T15-optimizer-ownership-repair-r1.md`; R0 requirements/design review remains applicable. Only the same five complete sources are charged: **5/3940 lines**.

| Source | Lines | SHA256 |
|---|---:|---|
| src/townlet/population/vectorized.py |2146|9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a|
| src/townlet/training/replay_contract.py |222|3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c|
| src/townlet/training/q_targets.py |80|39485fe2447dc4065bd7b806775c93c0e66b51827b088605fba98505b100491f|
| src/townlet/config/bac_options.py |294|10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916|
| tests/test_townlet/regressions/bac/test_learner_legality.py |1198|5f6273a8054bde34f89ab77eb98c8b4c0bb9428b586511b976cecae19c33e71e|

## Findings and repair assessment

R0 residual-oracle finding is resolved in source: the expected residual tensor is explicitly float64, preserving strict dtype/value checking and production float64 subtraction/feedback. No X04 operand promotion, objective, weight or priority behavior was weakened.

R0 recurrent-cardinality evidence gap is resolved by the new `test_recurrent_one_window_readiness_distinguishes_laws` at485. It uses actual prioritized sequential construction, retained3 transitions, fixed_full L3, minimum1 and B2, and checks sampleable_units1. Successive refuses with batch_unavailable, no draw, unchanged optimizer/scheduler/target/sampler RNG; replacement samples the same real window twice and changes actual network parameters. Both advance vector tick/beta. The new live pending collector row is explicitly excluded from retained count. This is the requested causal boundary, rather than an episode-count or retained-count proxy. Root reports both cases passed in the preceding causal campaign; current frozen-candidate independent execution remains pending.

The four actual flat post-step discrepancies were correctly escalated beyond fixture suspicion. Root's R1a causal assertions confirmed shared optimizer storage at candidate `096cdb7d98a9725181658c44b3ed84a6d0d72e82`; this matches the earlier static diagnosis of a shallow nested mapping handed to same-device Torch load. The repair at POP2039 deep-copies the validated optimizer mapping before installing it at2055. Nested moment/step tensors and containers now have independent ownership while values/configuration/counters remain intact. Copy allocation occurs before live network/optimizer installation, preserving the existing validation order. This is an appropriate production repair, not a test-only workaround.

The owned restore test permanently checks disjoint optimizer storage against both the saved input and the other target, saved-input immutability, eager-optimizer immutability while lazy advances, equal initial current observations/modes, actual sampled DTOs/receipts, and exact post-update population state. Direct manual Torch attachment independently deep-copies its supplied optimizer payload, appropriately distinguishing that low-level fixture from the public population loader. Torch, NumPy and Python RNG snapshots bracket equivalent continuations; no equality tolerance was relaxed. The input/sampling/mode assertions make future divergences substantially more diagnostic.

The sequential archive fixture now uses the documented prepare_archived_import/load_prepared pair; the beta assertion reads serialized priority_state.beta. Both preserve the original state assertions and call actual public APIs. The eight formerly blocked recurrent restore cases still require execution through their formerly unreachable continuation assertions. The prior missing-Python-RNG hypothesis is addressed by exact state restoration, not by assuming recurrent continuation succeeds.

The additional production changes replace conditional expressions with equivalent explicit branches for initial tick, constructor ownership markers, explicit/compiled horizon provenance, setup selection and optional Double-DQN successor evaluation. Comparing the patch deltas shows no change in branch conditions or selected values. The root-owned ratchet change613→612 is attributed policy data; no linter or other sixth implementation source was opened. No new default or capability reduction was introduced.

No newly confirmed implementation regression was found. Existing T15 target legality, successor capture, connected prefix BPTT, once-weighted objectives, X04, lazy replay preservation and provider-selection conclusions from R0 remain supported. Full native continuation/atomicity is still T24/T25; this narrow optimizer ownership fix does not certify that whole contract.

## Runtime evidence and independent selection

Root reports original R0 owned campaign29FAIL/121PASS, with16 residual-dtype failures, eight invalid sequential archive calls, one invalid beta-property assertion and four genuine post-step discrepancies. Root reports R1a ownership causal RED in all four flat cases, then applies the one-line production ownership repair; evidence remains under `/workspace/bac-review-2026-11-01/qualification/wave09-r1a-causal/`, causal log SHA256 `cc0d546bd840e688fe3813e68aee67902c6db815231d74f349ad3fca3d764cad`. These are root-attributed results, not independent execution here.

Independent selected execution requested after root's collection/resource/identity clearance, all in the existing owned test file:

1. `test_load_before_first_step_adopts_current_replay_and_clocks[load-active-current-feedforward-True]`
2. `test_load_before_first_step_adopts_current_replay_and_clocks[load-active-current-recurrent-True]`
3. Both parametrizations of `test_recurrent_one_window_readiness_distinguishes_laws`.

These four actual cases cover the original ownership failure, the previously blocked recurrent current7 continuation path, and both sides of the newly required cardinality boundary. Root will supply collected exact IDs and its bounded import/identity/fixture harness. No custom sixth probe is needed. At this report's initial write, no project import, pytest, collection or static guard has been executed by this reviewer.

Outstanding: independent selected execution; full owned suite and affected B03/replay/population owners; six standing static guards and required full G2 on the final frozen candidate; repair/re-review any failures. Genuine ICM selector evidence remains limited to the second env.step boundary; full reward/update/continuation/E2E is REQUIRED OPEN T18e/T18f. Fresh final22 lenses/synthesis, all54 requirements, learning/E2E, coverage>=70%, slow/applicable hardware, finite T40 and exact-tip remote CI remain owed.

## Custody

No sixth implementation/test/helper/provider/buffer/network/runner/conftest/schema source was read. No source/index/branch/worktree/source-copy/deletion/subagent/commit/publication operation occurred. Manifest lists14 preserved worktrees. Root retains integration ownership. Only this ignored review prose is written; R0 report and actual failed evidence remain unchanged.
