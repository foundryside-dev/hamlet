# Review provenance

Historical finding/triage source identity remains historical; see the final implementation receipt for repaired-source qualification and required remaining X04.

Original `T13-astra-core-review-r1.md`, SHA256 `09688f2a1f8009ddab2f1f219e568fc90aa6a998a1df1d65fb8c8bcbe73173c3`, retained unchanged; portable rendering normalizes execution paths.

# T13 independent core R1 rereview — stationary

Verdict: REQUEST CHANGES. The prior legacy pre-RNG defect is fixed, and the high-max new6 refusal is fixed for the tested example; the complete maximum-priority invariant and cross-version serialization domain still have P2 gaps. All136 existing counted-core cases pass in my independent run. No new P1 is established here. The new cases below are source-confirmed deductions, not executed reproductions: no new helper/probe or test edit was authorized.

## P2 findings

**R1-P2a: validate the actual float32 insertion conversion, including underflow and round-up.** PB473–474 checks only real-valued positivity and an upper bound; PB505 then assigns the Python maximum into float32 priorities. The new6 validator at853–860 adds only the upper bound. Two otherwise well-formed empty6 states therefore pass validation/install:

- max_priority=1e-300. It is finite, positive and below float32 max. A subsequent valid push passes the same range guard and commits a zero float32 priority, while also advancing ring/IDs/rows. Sampling and reloading its serialized active state then refuse nonpositive priority. This breaks the latest-state servability/positive-priority invariant.
- max_priority=1.00000007. It rounds up on insertion to float32 approximately1.0000001192092896. The unchanged Python maximum is now lower than an active priority, so the buffer's own serialize output fails its max>=active check on restore. This is an ordinary-magnitude rounding case, independent of the extreme underflow example.

The validator and insertion must agree on the actual prospective storage value before any live writes, and insertion must leave max metadata coherent with all committed priorities. A range check on the uncast real number is insufficient. Required regressions should cover empty-state validation/load purity for underflow, insertion no-partial-write behavior, round-up continuation/serialize/reload, and positive finite subnormal/boundary values. Do not impose exact binary equality as a new blanket condition on otherwise working legacy maxima: conversion/coherence can be handled without rejecting ordinary finite values merely for rounding.

**R1-P2b: accepted captured5 can emit a new6 checkpoint that is immediately rejected.** The added maximum guard is conditional on version6. Exact original27-key5 with ordinary valid active rows/priorities and max_priority=1e300 still passes the original finite/positive/max>=active predicates, installs that maximum unchanged, and `serialize()` always emits version6. Reloading this emitted state now fails the version6 upper-bound guard. Its next insertion is also rejected by PB473. This is an inconsistent accepted-state domain in the explicit5→6 adapter, even though genuine supplied fixtures have ordinary maxima and pass.

The high maximum is a deliberately mutated schema-valid input, not evidence of an authored learner producing it or proof that it is a working old runtime capability. Reconcile the accepted captured5 operational invariants with the emitted latest schema before installing it; do not silently clamp/relabel/discard captured rows, rewrite authentic fixtures, or route5 through maskless4/fresh0. Preserve all genuine supported original5 fields and roundtrip/continuation. If such maxima are judged semantically malformed under the existing float32 storage contract, make that refusal explicit and atomic before installation rather than accepting and emitting unloadable6. Genuine old4 remains archival and must not acquire an active-current bound accidentally. Add a counted version5→6 domain/roundtrip regression and valid ordinary rounding counterpart. This is distinct from the lower-bound failure above and is caused by the version-gated repair.

## Resolved findings and complete-contract reassessment

R0's legacy float32 refusal-after-RNG issue is resolved. PB.sample alone calls the new same-file float32-preflight adapter; both qualified global64 and explicit-owned64 routes retain the wide support. PS computes final beta weights before conversion and before any choice. The bound uses initial P and largest tail; later q only increases and tail decreases. Beta0 and full-population successive explicitly remain ones. The new negative wraps real global choice yet verifies it is never invoked; three positive beta/full cases and qualified64 above-float32-range positive passed. No support clipping or sampled-max normalization was introduced.

Legacy indices now use an owning writable copy; immutable qualified receipt indices remain separate. New writable-index regression passed. The original high-max new6 validate/load tests pass with source/target/global/Torch purity. Count-bearing B>N diagnostic is restored. HC's explicit exact-type checks preserve the same supported-version semantics while allowing static narrowing; no cast bypass or unknown-version admission appears. Two default-like constructs were removed without changing priority duplicate reduction. These repairs are materially correct within their tested scopes; the maximum finding above is a further boundary reassessment, not a claim that none of R1 worked.

Reused the complete R0 five-file source context, verified every changed byte against the two immutable candidate trees, read the entire added counted tests and current PS, and re-examined current PB admission/sample/validation/materialize/install/version transitions. Unchanged methods remain part of this review's complete-source context, not omitted because outside the diff. Total3316 lines: PS163/PB1071/HC675/OP294/test1113. All helpers/oracles remain inside these five. No sixth RC/POP/Brain/native witness/owner fixture implementation was read. Accepted P2/P3 interfaces and prior task/preparation/coordination/authority prose remain binding; read new core-review-repair-r1 and review-regressions-r1 receipts as prose. Previous R0 report remains immutable historical evidence.

Actual successive residual q construction, independent replacement/repeats/B>N, explicit B=N ones, detached64 correction, log scaling and tiny-q final-beta behavior remain coherent. Independent tests enumerate forced sampler branches and actual proposal arguments against separate math.fsum/power oracles; unforced successive frequencies cover the actual law. Stable versus physical update routes remain separate; duplicate maxabs, stale overwrite/clear refusal, ID counter exhaustion and state restoration remain intact. Owned Generator configuration and known-engine state reconstruction still occur off-side without aliasing/hidden behavioral seed/global RNG installation. Full priority-update requests prepare before commit. Restore resources, clones and archive unions precede live assignments. No additional fallible-install defect was found by this static pass.

Original19-key4 remains archive/query/export/fresh0/full-resume refusal. Genuine closed27-key5 fixtures retain all original rows/masks/components/priorities/ring/beta/archives under deterministic ID adaptation; the reported synthetic maximum domain gap does not negate those positive proofs. New6 remains closed34 fields. HC's historical4/4/5 and current standard5/PER5,6/sequence6 tables and policy codec remain aligned. OP's selected modes/provenance remain unchanged; core support is not proof of actual population replacement/stable-handle wiring.

Optional gap retained from R0: a distinct final-float64-weight-overflow refusal test would strengthen PS preflight coverage beyond support-underflow; source implementation appears correct. The test warning about indexing Torch with a nonwritable receipt array is test-side and does not prove production mutation; production converts selected indices with torch.tensor/copies.

## Exact independent execution and identity

Base HEAD41edeb0858cba98a8dcb6ba2af36355457ef4e0a. Candidate aaf82a6563bfe5333be266753776fee9a4db3963. Manifest wave07/green-r1-candidate.json SHA256ac5e4627d631ebc90f621fa4ad1411c8865c8408950fd058f1007567fbaf4397. `GIT_OPTIONAL_LOCKS=0 git diff --cached --quiet aaf82a6563bfe5333be266753776fee9a4db3963` succeeded before/after; five hashes unchanged before/after. No write-tree/index/staging/commit/source/test edit/checkout/worktree/branch/copy/delete/subdelegation occurred.

Verified unique output, spec and basetemp absent first. Wrote guard metadata `qualification/wave07-astra-core-r1-spec.json`, workers1, and called:

`python qualification/run_bac_packet_checks.py qualification/wave07-astra-core-r1-spec.json`

Exactly one existing counted-core child process:

`.venv/bin/python -m pytest tests/test_townlet/regressions/bac/test_per_estimator.py -q --no-cov -p no:cacheprovider -p bac_source_identity --basetemp=/tmp/bac-wave07-astra-core-r1`

Result136 passed,1warning,5.93s pytest/11.656s runner, exit0. Log `qualification/wave07-astra-core-r1/adversarial.log` SHA25647b7c74a1287e3b30bc23bba5ef3f473bdd21cf8c6162f19cc251bfd7cfa9d79. Runner attests exact candidate/base/manifest; supplied identity plugin and Torch1 checks govern process. Runtime COMPLETE, no process active. Prior RED4fail/4pass and root-native/owner results are root-attributed, not my executions.

Five source SHA256 values:

- PS0efe801f01a31082aa52c4b9bd40c356d1c97f89690b07c7835b541b7f2c6de6
- PBc505422d64b334a94a0e6f8d3faf1c375b151fa90d7432489017471c42f1f07c
- HC33073ebc7d3a3c520d32ab74d5617084b39cdb76cded3836d6731046096cd315
- OP10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916
- Test0b47c891801781001507984d2613d2e0422b0c30cb0e86cd1b097b5f491867ab

New review inputs: T13-core-review-repair-r1.md SHA256bfa20f3e819263f0b83c5c05518efe973e5f09cdbdebbaf49197d69e7b9995cc; T13-review-regressions-r1.md SHA256a65b28f15c8b4954a9da4e6e012b413863457dfb52e6bdd8d262c6e9c54ea586. Earlier exact design/review input hashes are recorded in immutable R0 review SHA256d85f2f22dd6cb28162ca9c7d2891b0af87d121a2ea4d629e30be759d7e5b4900.

## Scope and gates

No full-suite, broad six-guard, separately owned native learner or owner-consumer execution by this reviewer. Root owns those gates and all integration/repair. Actual consumer regressions cannot be waived by future-task labels. Complete native validators, empty-PER native handling, outer/nested registry accounting and resource/RNG atomicity remain T24/T25 obligations. X04 remains required existing POP telemetry P1, owned T15 beforeG2 with T35 consumer acceptance; no POP source read and no closure or optional downgrade. C01's newly bounded real-learner evidence remains distinct from historical B04 API-only evidence. Mandatory full4-worker before T13 release and all later coverage/slow/hardware/CI gates remain required. No whole-BAC zero-P1/P2 claim.

STATIONARY. Only external guard JSON and this ignored prose were written. Existing MAIN and preservation/approved-history authority remain unchanged. No durable user-only fallback adopted; failed rule grants/restricts nothing; specific approvals do not fan out.
