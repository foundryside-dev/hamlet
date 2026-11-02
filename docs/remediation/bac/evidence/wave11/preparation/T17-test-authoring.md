# T17 tests-first authoring receipt — awaiting root collection/RED

2026-11-02 UTC; existing `/workspace/hamlet`. Root reports T16 source `6b5fdf62` qualified with G2 6857 passed/16 skipped, six native PASS and six documentation-guard PASS; evidence checkpoint `a0802a442bc7ea529de650b8705629923a0e6c72` pushed/provider-exact verified. That root message supersedes the task brief's historical readiness-only phase **for test authoring only**. This worker reread `T17-task-brief.md` first and reused its adopted API/budget and existing readiness/supplier handoffs. No new design, plan, or review loop was opened.

Only `tests/test_townlet/regressions/bac/test_token_binding.py` and this ignored receipt were authored in this phase. NET/NF/BC/OP were read whole and left unchanged; no sixth source/helper/test was opened. No project import, runtime, compilation, collection, pytest, linter, probe, index/commit/push, subdelegation, branch/worktree/project-source copy/deletion or `.oracle` action occurred. All 14 existing checkouts remain in place. Fixture code describes future temporary DATA materialization; it has not been executed and no pack was materialized by this worker.

## Complete five-source inventory

Independent physical newline counts: `wc -l`. Byte identities: `sha256sum`. Post-authoring readback covered the entire owned test in contiguous ranges. All four production hashes match the pre-authoring snapshot.

| Alias | Exact complete source | Lines | SHA256 |
| --- | --- | ---: | --- |
| NET | `src/townlet/agent/networks.py` | 474 | `bff39c4b46820c3bc812bfa7ebdf5f8832cf4b1f94bb6038eb1c5d56dd9ae9e1` |
| NF | `src/townlet/agent/network_factory.py` | 171 | `976ff4f761c65981ce0f35812379abbdef940e81bed21e8f2715c2df02efb6fd` |
| BC | `src/townlet/config/brain_config.py` | 568 | `6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079` |
| OP | `src/townlet/config/bac_options.py` | 294 | `10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916` |
| owned test | `tests/test_townlet/regressions/bac/test_token_binding.py` | 633 | `6ca7838f97021cfd88151b7b0b9c2ef225d9e8f9affcd8d5f8cadb866bac91f3` |
| Total | Five complete sources | **2140** | — |

The owned test is within 800 lines; the five-source total is within the adopted 2662-line projection and 5000 ceiling. BC/OP remain read only. No extra helper/fixture source was added.

## Named tests and intended defect controls

Six test functions declare **34 parameter combinations by static inspection**; this is not a collection result:

| Named test | Declared combinations | Contract and meaningful failure |
| --- | ---: | --- |
| `test_from_resolved_encoder_requires_explicit_selection` | 12 | Bare encoder/token-set/recurrent × mean/attention × linear/interaction width3. Uses `getattr(..., 'from_resolved_encoder', None)` and an in-test callable assertion, then exact required `token_encoder_mode`/`token_encoder_hidden_width` keywords. Checks no missing-keyword defaults, invalid explicit pairs, direct Linear versus Sequential indices0/2, hidden geometry, selected aggregator/heads, and absence of context/scatter buffers in learned state. A missing method fails as an assertion, without importing a nonexistent symbol. |
| `test_mean_can_bind_descriptor_value` | 2 | Both factory families must construct interaction encoders before pooling. The isolated schema uses valid full variable payloads and selected deterministic tensors giving exactly `.375` versus `.125`; moving rows with their contexts preserves the witness. An ignored option/current direct Linear fails the explicit row-encoder assertion, rather than a random-weight distinction. |
| `test_attention_retains_nonuniform_row_interactions` | 4 | Both network families × both row modes retain actual attention. Selected identity Q/K/V/output projections produce a hand-derived nonuniform attention result differing from mean, preventing the masking controls' uniform-attention setting from concealing attention removal. |
| `test_authored_mean_can_bind_descriptor_value` | 2 | Both factory families consume normal compiled two-world reset/WAIT observations. Deterministic row tensors yield `pulse_right/N` with actual present count N. The token-set head's fixed reference coordinate survives LayerNorm and has an analytic selected WAIT-Q distinction using the actual layer epsilon; other Q coordinates are exactly zero. No identity LSTM or random recurrent Q separation is assumed. |
| `test_linear_mean_is_preserved` | 6 | Three direct constructor families × mean/attention. Starting at the same RNG seed, additive resolved-linear and explicit/omitted factory paths match the retained direct constructor's parameter bytes/state names and forward/hidden results. The mean control has the exact unchanged affine value-reassignment alias; omission provenance comes from the existing authoritative resolver. |
| `test_semantic_permutation_absence_and_memory` | 8 | Both network families × mean/attention × both row modes. Immutable row/binding/context permutation plus ordinary strict same-mode weight loading preserves pooled/Q/hidden results within1e-6 and target context. Row-only permutation is a distinguishing negative control for interaction mode. Poisoned absent-variable rows have exact-zero pooled values and all relevant row/type-vector gradients; a positive present-gradient control avoids a vacuous dead ReLU. All-empty poisoned inputs give finite exact-zero pooling and every encoder parameter gradient exactly zero. Recurrent cases use zero-start hidden/cell, one full-sequence LSTM call, threaded-frame equivalence, a deterministic candidate-gate memory path and nonzero recurrent-weight gradient. Same-current-frame/different-history cases preserve linear alias while interaction can carry distinguishing history. |

No skip, xfail, monkeypatch or mock masks the missing representation/API. The candidate intentionally retains linear, mean, attention, token-set and recurrent controls. It does not exercise excluded checkpoint/refusal/transfer/execution-identity consumers or make long-run learning/CUDA claims.

## Fixture assumptions and supplied API custody

Consumed supplier prose/DATA only, never its implementation links:

- `T17-fixture-api-handoff.md`, current SHA256 `c1ab2fd929960627c8e9a3bc7e96aff0680061bada5ffd7b8dbd4494c4a7ff88`. This includes root-forwarded scalar binding clarification after its preserved original 416-line prefix. Exact scalar `filler_ref` literals are `pulse_left`/`pulse_right`; the future fixture asserts exactly one match of each in `variable_element` and indexes via `binding.slot_index` plus `spec.row_layout()`.
- `T17-env-public-api.md`, SHA256 `41cb275e96e52f6e771889ba92138c4819c1bd02082903d6829b64267ec48e74`. It supplies the current compiler/environment/action interfaces and explicit external-helper limits.

The authored fixture retains the entire canonical `configs/test/token_set_smoke` DATA hierarchy in a future pytest temporary directory, replaces only the supplied complete variables71/bars49-line documents, and adds explicit interaction width1 in the root brain document. It compiles with `primary_level='L0_test', use_cache=False`, builds two CPU worlds through `VectorizedHamletEnv.from_universe`, clones reset/step observations and takes one action named exactly WAIT after checking its public legal-action mask. No environment state injection or guessed cleanup call appears.

The future runtime must verify actual observations are floating CPU tensors of selected-schema width, `.25/.75` values swap after the first step, static `.125/.875` descriptors remain distinct, pulse presences/counts are valid, all non-pulse compact fields stay exactly unchanged, both worlds remain nonterminal, and the successor mask matches the public current mask. Width147, offsets142/145, count39, WAIT5 and action dimension7 are never hard-coded. Full selected-level/training/affordance carriers are retained through the canonical pack, including unselected L1; the selected L0 meters have frozen depletion/recovery and retain original cascades.

The pure two-row witness uses the supplier's public frozen schema constructors and full `PAYLOAD_SCHEMAS['variable_element']`, binary presence and feature-name coordinate lookup. Semantic permutations use `dataclasses.replace` on public compiled TokenSpec/schema/bindings and move whole context rows with compact rows. No private assembler buffer is mutated. Diagnostic absence inputs are network tensors, not injected environment state. Fixed selected LSTM candidate weights separate memory evidence from frame expressivity; no stochastic learning result is inferred.

## Verification boundary and handback

Checks performed here are readback/count/hash/ignore-custody checks only. The destination receipt is ignored. No syntax parser, project import, compile, collection, pytest or lint was run. Consequently **RED has not yet been demonstrated**, test syntax/runtime/fixture qualification is not claimed, and no production implementation is cleared. Root owns collection, meaningful RED, any finite correction response, and the explicit production-authoring gate. Worker returns stationary with this candidate.
