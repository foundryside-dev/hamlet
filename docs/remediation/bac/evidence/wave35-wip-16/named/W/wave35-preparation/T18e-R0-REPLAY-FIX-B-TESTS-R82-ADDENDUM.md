# Recurrent replay B tests review — R82 runtime addendum

2026-11-13. **B1 causal RED is established; tests-only correction is required before production acceptance.** This adds root's actual runtime evidence and a newly observed fixture prerequisite to the initial review. Initial `T18e-R0-REPLAY-FIX-B-TESTS-REVIEW.md` remains unchanged at SHA256 `fb76a7b0891b8b5548483519c531c8ddae052895b997a3070f4b37db706c9879`. No source/helper body was newly read, no runtime/imports or Git operations were performed, and no source edits, deletion, copies or delegation occurred. Only this addendum was written.

## Exact attributed execution

Read root's authoritative `../wave35/r82-recurrent-tests-receipt.json`. Results below are root execution, not independent reviewer execution. Source is R82 tree `690c51f8a89653b9bdcf4b52c002b3fe73c7f27c`, base `29d0204a70b6eef0017b3cee638812e2cc5c7899`, manifest SHA256 `8c8b157d1dc4c47472bc039812fbc9146758d342bc4ce7547a668011438783ee`. Production remains unchanged; the initial five-body packet is4304 lines with the hashes recorded in the initial review.

| Actual selection | Result | Seconds |
| --- | --- | ---: |
| Collection of new recurrent module | 54 collected; exit0 | 5.307809 |
| Width3, valid DTO4, selected legacy1 fixture controls | 8 PASS | 4.433219 |
| Remaining ordinary controls | 31 PASS, 2 FAIL | 4.812042 |
| Mutated DTO cases | 12 FAIL, all intended missing ValueError | 4.339579 |

These disjoint runtime selections executed53 unique cases:39 PASS and14 FAIL. Collection adds no runtime cases. All12 malformed DTO cases reached `DID NOT RAISE ValueError`; none failed on imports, signatures or fixture construction. This confirms the actual B1 validation omission under ordinary returned-data mutation, rather than merely the earlier static hypothesis. Width controls pass as existing behavior and must not be claimed as repaired defects.

The root receipt records full816 source/573 config/13 protected/14 registry MAIN1 source/process/import custody verification for all executed groups, including negative-result custody, and all sessions closed. Exact specs, logs, failure identities and hashes are sealed by that receipt under `/workspace/bac-review-2026-11-01/qualification/wave35-r82-*`. The controls log SHA256 is `7b7b13ea90f0a6c472b36819c67a6fe8c06fab20c50db25b47570a5efab9a1c8`; DTO RED log SHA256 is `aabdb4cc74b553e6252426b2e89e08077991786409785e9be63cac49b0a50f92`.

The isolated child remains intentionally UNRUN pending test corrections. Root reports the separate external verifier is now independently approved after36 synthetic checks; this removes its earlier tooling prerequisite but does not supply genuine child execution or child PASS. No child implementation was inspected here. The generated owned-spec template was also UNRUN and supplies no checks.

## Required tests-only correction round

1. **Correct the frozen-policy prerequisite without weakening immutability.** Both ordinary failures are the uniform and priority instances of `test_recurrent_install_owns_input_and_retained_candidate_material`. Root attributes them to new-test line407 assigning `material.replay_options.sequence_objective`; actual ReplayOptions is frozen, so assignment raises before the downstream priority-array/generator mutations and final installed-state comparison. This is a test-fixture assumption, not a production alias defect. Assert the genuine frozen-assignment refusal through its supported exception, then continue the remaining mutable retained-material mutations and final complete installed-state comparison. Do not bypass frozen policy with reflection, change production immutability, remove the policy check, or count the unexecuted suffix as passed. The input mapping mutation before install remains a separate valid ownership control.

2. **Assert actual scratch-work publication.** Preserve all real delegated sampler, disposable-state advance, complete ambient/persistent state and selected-algorithm continuation checks. Add direct before/after checks that the selected unit's stored priority changes to the expected value, rather than observing only max_priority. For store-refresh, observe the real appended episode values and resulting window/domain population rather than only num_transitions. The independent control owner takes the same production path, so it cannot replace these direct publication assertions. Current source does publish these values; the issue is finite test coverage, not authorization for a speculative production change.

3. **Add captured6-to-prioritized DTO capability preservation.** Create genuine uniform format6 transport and validate/materialize/install it through a real configured prioritized destination. Assert active rows, captured6 adapter provenance, retained priority configuration and persistent stream, then perform a real selected sample. Current same-profile valid DTO controls do not cover this explicitly retained adapter. No new compatibility route, fallback or source body is needed.

Root accepts all three as prerequisites before production acceptance and will transfer only the bounded test writer for round1. Retain the R82 source-bound failures and initial review as history. Measure all five whole bodies after additions, preserve the five-body/hard5000 and projected4921 bounds, then freeze/capture the corrected candidate separately. Root must verify corrected alias suffixes, stronger scratch controls and the new adapter control, retain intended DTO RED attribution, and execute the separately admitted genuine child before making corresponding acceptance claims.

B1 production repair still requires a separate writer grant. No B implementation, CUDA/B6, caller migration, whole-replay or programme closure is approved by this addendum. Accounting remains28/38/66.
