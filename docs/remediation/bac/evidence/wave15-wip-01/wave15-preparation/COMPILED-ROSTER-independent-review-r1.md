# COMPILED-ROSTER independent review R1

Reviewer: fresh independent Solauthor review, 2026-11-10. Static specification and code review only; no Python imports, tests, runtime, Git writes, source edits, extra implementation reads, or subagents. Only this ignored report is authored.

## Verdict and binding

Specification verdict: ACCEPT the bounded implementation for execution qualification. Quality verdict: ACCEPT with no blocking defect identified in the exact scoped patch and four counted files. This is not a GREEN, owner-suite, integrated runtime, native restart, learning or final BAC acceptance verdict.

Base supplied by root: `f22d77af39cd67bb8102854f38f43baa50a1381c`; candidate tree supplied by root and manifest: `ca5c48c6002218b63733965f9a800e25fc2024e0`. Reviewed exact `wave15/r1-CU-review.diff.txt`, SHA256 `63164b2199b771efeee878529747275d009d5dc74c89830b4f27d07522794f2f`; no substitute HEAD-relative diff. Requirements: COMPILED-ROSTER-EXECUTION-BRIEF.md, COMPILED-ROSTER-implementation.md, ACCEPTED-CURRICULUM-PRODUCER-RECEIPT.md and docs/remediation/bac/CURRENT-CURRICULUM-POLICY.md. EF/OP/RP/ENV implementation sources remain outside inventory; their exact accepted contracts are consumed as receipts.

Independently measured whole files:

| Path | Lines / ceiling | SHA256 |
| --- | --- | --- |
| src/townlet/universe/compiler.py | 976 / 1200 | 521a72dd6d0a155c89a216fa038828cc8054520714a58cc0e0420c2da9d09e92 |
| src/townlet/universe/compiled.py | 1641 / 2000 | 93273470c102ea4de77c071587d8c0d2bcc643579c3272dc91fa5897e40ed7dc |
| tests/test_townlet/regressions/bac/test_effective_run.py | 323 / 500 | 1685b2c09aa59c6687a49accebf62be591e64716f91469ef85e332d8b765cdd9 |
| tests/test_townlet/regressions/bac/test_curriculum_compiled_roster.py | 340 / 700 | d3ba74c548c4398125ed8f7b793803bbb6c53c1aa6614e9c1652e21b3b810de9 |

Actual 4 files / 3280 lines, projected ceiling 4 / 4400, hard 5 / 5000. compiler.py is unchanged in the exact diff. Three changed files, 406 insertions and 47 deletions. No fifth implementation/helper/probe/fixture source opened.

## Contract assessment

- compiled.py:385-425 resolves the sole roster from selected actual bars, preserving order. Every level's bars names are checked for unique nonblank strings, declarations and meter metadata must match that order, and metadata indices must match positions. Selected summary names, count and name-to-index must match. No global vocabulary or hardcoded fallback is substituted; a coherent empty roster is not rejected by this new validator.
- The required EF argument is passed through the accepted resolver API, causally addressing the recorded missing-argument RED. Existing compiler stage-8 selected brain replacement, training, drive and explicit origins continue unchanged. Fixed policy constants and omission resolution remain with their accepted producers.
- `_validate_effective_run` independently resolves the expected view from the compiled object's actual brain/training/drive/selected bars and compares the complete transported payload through accepted canonical EF validation. This is stronger than equality of execution hashes: the new adversarial foreign-roster test deliberately demonstrates equal selected hash but different inactive static roster. Transported origins remain historical capture metadata, not invented authentication of external world identity.
- from_dict validates current version before nested interpretation, reconstructs the local candidate, checks existing token/policy coherence, decodes transported EF and validates it against actual candidate inputs before installation/return. clone builds an owned local candidate and validates before installing the transported result. to_dict validates before creating its export; save_to_cache obtains that export before any target write. The sentinel test covers refusal without overwriting existing bytes. A local candidate's initial derived view is not a published forged view.
- Native version 1.42 is the sole direct accepted format. The 1.40 field-list alias, derive branch and dual-version dispatch are removed. This is explicitly authorized migration, not accidental legacy capability loss. Original historical data remain byte-preserved and direct loads refuse. The 15-artifact manifest loop and separate original recurrent-cache digest assertion remain substantive; current authored recurrent serialization now supplies the replacement runtime witness.
- compiler.py:115-145 retains cache read, selected-level guard and freshness processing; :832 onward retains broad defensive cache miss for corrupt/unusable artifacts and normal recompilation. Old-version direct refusal therefore coexists with supported mutable authored-cache recovery. Source/content/path/dependency fingerprinting and cache path selection are unchanged. Tests exercise old and corrupt cache recovery and an authored bars edit that changes content/provenance and selected static execution identity.
- Existing five override, complete selected brain replacement, inactive preset, provider capacity/source, network weight, authored/selected hash, raw NaN and owned EF tests remain substantive. The patch adds roster arguments to direct EF calls without weakening those assertions. Canonical EF comparison is reused rather than substituting Python equality, preserving the accepted inactive NaN contract. No replay/provider/brain implementation behavior is edited.
- The real compiler-to-manager witness uses selected L1 bars in reversed order and literal baseline values .5/shaped/1 with completion/stage_band. Arbitrary authored names exercise absence of a default-name substitution. The rates test authors .01 and .1 in YAML, performs actual compilation, commits current LaneOutcome completions and compares restored native-v2 future state/decisions. Its explicit test world ID proves only this configuration/factory route; it does not qualify real ENV world lifecycle identity or physics.

## Defects and gaps

Blocking correctness/specification defects: none identified by this static review. No runtime behavior is inferred from the absence of a finding.

Outstanding acceptance evidence (required, root-owned): actual R1 GREEN for the 51 collected cases; full static/type/default guards; independent execution of the selected adversarial cases with custody; broader current compiler-owner suites; integrated consumer/full-suite/native/learning/restart/E2E and final BAC gates. Root supplied collection of 51 cases, but no passing result was assumed in this review. These are evidence obligations, not requests to redesign the selected scope.

Optional coverage, not blockers: a coherent empty selected roster and direct independent meter-index/count/map corruption cases would sharpen the new validator's branch coverage. Existing selected-roster tests mutate bars/declarations/metadata ordering and summary names; code inspection establishes the extra comparisons, but these particular branches are not independently exercised in the counted new file. Add such cases within the existing counted file only if further owner qualification identifies a need. No production change is proposed.

Refuted concerns: old direct-native refusal is required and does not remove authored compiler recovery; equal adversarial execution hash does not bypass full-view validation; compile-manager native-future tests do not establish environment lifecycle identity; the historical manifest loop was not replaced by a single digest or converted fixture. An entirely different but internally coherent authored world is outside this API's external authentication promise; this slice binds EF to the actual compiled outer candidate and does not invent an independent trusted world identifier.

## Independent execution selection

Use exactly the two counted test paths with this selector:

`-k 'self_consistent_foreign_roster or foreign_effective_view or selected_roster_products or current_effective_payload_tampering or authored_compile_preserves_cache_recovery or authored_compiled_modes_rates or inactive_raw_nan or original_historical_compiled or actual_selected_level_roster or current_native_dict'`

Static expected selection: 25 cases, 26 deselected out of 51; actual collection is authoritative. It covers static/adversarial internally valid foreign views, clone/export/write refusal, product consistency, seven EF tamper modes, mutable-cache recovery, three mode/rate/native futures, NaN preservation, original 15-cache retention, actual selected factory transport and owned current serialization. Root must authorize execution and record actual collection/result/custody before claiming independent runtime success.

Provenance retained: root's corrected R0 exact selected compile witness was 1 FAIL / 50 deselected at missing declared_meter_names, 7.7960s wall after 51 collected and source custody PASS. Earlier root selector 0/51, exit 5 is neither RED nor PASS. This reviewer executed neither run and does not upgrade those received results.

## R1 execution reconciliation — supersedes initial acceptance

Root now reports actual R1: **6 FAIL / 45 PASS / 51 cases, 231.5194 seconds wall**. All six global guards passed, including mypy exit 0 and compiler CLI; reported compiler-CLI wall 254.418 seconds. Both root jobs are closed. These are received execution results, not this reviewer's executions. Independent runtime is still not cleared. The initial static ACCEPT above is superseded: **R1 requires bounded changes before acceptance**. I missed the distinction between bars declaration order and metadata column order in the initial four-source review; actual failures and the newly authorized producer source refute that assumption.

The sole added implementation read is `src/townlet/universe/compilers/metadata.py`: 165 whole lines, ceiling 300, SHA256 `811dc301202433253832f84743cba65823f0d7c273a73d65e376d35a5e2f6beb`. Revised inventory is five files, actual 3445 lines, projection 4700, within hard 5/5000. This file is diagnostic read-only; no sixth implementation source, EF implementation, runtime, source mutation or Git write is authorized or performed. Systematic-debugging skill applied to this failure reconciliation.

### D1 — high / blocking: valid authored bars order is rejected

Witness: root reports two legitimate bars-reordering cases fail the new validator. `MetadataCompiler.build_meter_metadata` lines 44-60 enumerates `environment.environment.meters`, assigning metadata indices by that global declaration order, and obtains initial values from bars by name. `build_universe_metadata` lines 78-79 derives summary names/map from metadata. In contrast, the selected EF policy must retain actual selected bars order. Thus compiled.py's new comparison of ordered metadata names directly to bars names, and summary directly to bars names, rejects valid authored configurations. The existing test assertion that reversed selected bars imply reversed meter_metadata has the same incorrect assumption.

Approve root's finite remedy, with all these constraints:

1. Validate the global environment names as unique nonblank strings, preserving their authored order.
2. For each level, validate bars names as unique nonblank strings and require declarations to match that exact bars order.
3. Require exact name membership between bars/declarations and global vocabulary, without allowing missing, extra or duplicate names. No sorting or global-order substitution in the EF tuple.
4. Require ordered metadata names to equal the global environment order and metadata indices to equal the exact corresponding positions.
5. Require selected public summary names/count/map to agree with selected metadata's order/indices.
6. Return selected bars order to EF. Keep current full EF expected-view validation, native refusal and authored-cache behavior.

This corrects the validator's authority relationships; it does not weaken validation or change existing global meter columns. Do not reorder the metadata producer to make the old assumption pass. Preserve the two positive reorder witnesses and adjust only their mistaken metadata-order expectation. Existing corruption controls must continue rejecting disagreement within each authority and cross-view membership mismatches. The new fifth source establishes exact membership as existing producer contract, so this finite cross-check is justified rather than an arbitrary new global vocabulary restriction.

### D2 — medium / blocking test defect: native full-state comparison invokes tensor truth

Witness: root reports all three mode/rate/native-future cases fail raw dictionary equality on multi-element tensors. Counted test lines 328 onward compare nested checkpoint dictionaries after duplicate commit, defensive load ownership and future progression. Python container equality reaches tensor elementwise equality and then ambiguous multi-element truth; this cannot establish state equality. This is a comparator defect, not evidence that native state or rate semantics failed.

Approve a recursive exact full-state assertion in the existing counted test file: require matching mapping keys, sequence types/lengths and every recursive leaf; tensor leaves must both be tensors, have equal dtype and shape, and exactly equal content (torch.equal with explicit dtype/shape checks). Include device equality if device is part of these CPU-owned checkpoints' observable state. Do not flatten/stringify tensors, use approximate comparison, omit completion/counters, or reduce equality to selected fields. Preserve every existing duplicate-idempotence, defensive ownership and uninterrupted-versus-restored future comparison. Current decision equality can remain if its values are scalar/list DTOs. This helper stays inside the counted file and cannot become a sixth source. No production native-state change is justified by these reported failures.

### D3 — medium / blocking boundary defect: missing current static policy leaks KeyError

Witness: root reports the missing_policy tamper case reaches the child EF decoder and raises KeyError where the current compiled loader contract/test requires ValueError. The parent currently checks only that effective_run is a mapping before forwarding it. A malformed current required child declaration should be refused explicitly at this parent boundary before installation.

Approve a local required mapping check for `effective_run.static_policy` using the existing required-field/mapping machinery before calling EF.from_dict (and preferably before constructing the compiled candidate). Preserve the complete EF canonical validation after that check. No fallback, synthesized policy, old payload acceptance, blanket exception swallowing, or additional EF source inspection is needed. A valid static-policy mapping still belongs to the accepted child semantic validator. The missing_view case must retain its current ValueError refusal as well.

### Revised disposition and remaining gates

The three root remedy directions are **approved as finite contract corrections for implementation**, subject to root's separate source-write clearance. No whole-plan restart, cache redesign, metadata-column change or producer reopening is justified. Actual R1 negatives stay recorded, and the initial static verdict must not be used as evidence of current correctness. After edits, recompute exact candidate/diff/source hashes and whole-file bounds, rerun the failing cases and required joint suite/guards, and obtain fresh static reconciliation plus independently cleared runtime. Extend the proposed independent selector with `or authored_roster_edit` to include all six reported failing cases: expected 26 selected and 25 deselected against the original 51 cases. Actual future collection remains authoritative; no independent PASS is claimed or preauthorized. Broader current owner/full/native/learning/restart/E2E/final BAC acceptance remains owed.

Raw evidence subsequently inspected: `/workspace/bac-review-2026-11-01/qualification/wave15-r1-owned/owned.log` and `owned-result.json`. The latter binds candidate ca5c48c6/base f22d77af, exit 1, 231.5193955898285 seconds wall and log SHA256 `3f2e2294f6aa39f6a5b0af466a5a58e11339bb2405cbf57a93382b9960dac565`. The pytest log reports 6 failed / 45 passed in 222.24 seconds. Both reorder failures reach compiled.py:408, including the nonselected L1 roster while compiling L0. Missing policy reaches compiled.py:730 then child KeyError, as reported; only the traceback excerpt was read, no extra child source file opened. All three native cases first fail test line 328 with ambiguous tensor truth after their literal difficulty assertions have passed; later ownership/future assertions remain unexecuted and unqualified. This corroborates D1-D3 and the finite remedy endorsement. The 254.418-second timing belongs specifically to compiler CLI, not the six-guard aggregate.

## R2 FIX1 scoped re-review

**Static FIX1 approval: APPROVE. D1 ADDRESSED; D2 ADDRESSED; D3 ADDRESSED.** No new blocking defect identified in the finite correction diff. This supersedes the R1 changes-required disposition only for these corrected findings, not the remaining qualification gates. Old R1 six failures remain historical negative evidence above.

Binding: supplied base f22d77af39cd67bb8102854f38f43baa50a1381c, current R2 tree e18e85776f16b507040c1671310b17595fb26b21, manifest wave15/r2-candidate.json. Exact reviewed delta is wave15/r2-fix1-review.diff.txt, previous ca5c48c6 to R2 e18e8577; independently measured diff SHA256 `9af7fabd89a8e939a23f395a3a6a078e2b6c00c10a08db4e95b8c99d44b46cf1`. Only compiled.py and the counted new test changed: 46 insertions, 11 deletions.

- **D1 ADDRESSED:** global environment names are unique/nonblank; every level's bars names remain unique/nonblank and declarations must match that exact order. Exact set equality establishes vocabulary membership without erasing either order. Meter metadata must match environment declaration order and positional indices. Selected summary names/count/map match selected metadata. EF still receives the selected bars tuple. The positive test now independently obtains metadata order from authored environment YAML while retaining the reversed bars/declarations/policy/decisions assertions. No metadata producer or global-column behavior changed.
- **D2 ADDRESSED:** assert_exact_tree recursively checks exact Python types, all mapping keys/leaves, all list/tuple elements and lengths, tensor dtype/device/layout/shape and torch.equal content, then exact scalar equality. All three former dictionary comparisons are replaced, retaining duplicate commit no-op, owned loaded state and uninterrupted/restored future state checks. No state field is omitted or reduced to an approximate/string representation; decision equality remains. This corrects test semantics without changing native production behavior.
- **D3 ADDRESSED:** parent from_dict immediately requires effective_run mapping and static_policy mapping after top-level/version validation. These checks precede nested deserialization, candidate construction and child EF decode. Missing/nonmapping policy raises the parent's existing ValueError; accepted policy content still undergoes child canonical validation and full actual-compiled-input comparison. No old-state fallback or sixth source read.

Independently measured current counts: compiler.py 976; compiled.py 1651; test_effective_run.py 323; test_curriculum_compiled_roster.py 365; read-only metadata.py 165. Total 5/3480, projection 5/4700, hard 5/5000. Changed source hashes verified: compiled.py `0d994462f86e721ddd38ca32f286da05cc602d63a0e9e424e84a10320399c2dd`; new counted test `bd5a364931be94f2930c278ab5f21bf1a497814e727d93057f538da3bf7e2f38`. Other inventory files remain unchanged per exact diff and root custody.

Received covering evidence in the updated implementation report: exact R2 root command selected the six formerly failing cases and returned 6 PASS / 45 deselected, exit 0, 23.737912893295288 seconds wall. Root reports five core guards PASS and 179 source / 573 config / 13 artifact / 3 process identities, index/import/thread custody and registry checks PASS. These are received results, not reviewer execution. Root full 51 and compiler CLI remain running at this review. No full-suite or independent runtime result is inferred.

The scoped review is complete and ready for root's explicit independent 26-case / 1-CPU execution clearance and supplied wrapper specification. No runtime, source edits, Git writes, checkout copies or sixth implementation reads performed during re-review. Remaining current-owner/full/native/learning/restart/E2E/final BAC gates remain open.

## Actual independent R2 verification — completed

Following explicit root 1-CPU clearance, this reviewer executed exactly:

```text
env TMPDIR=/workspace/bac-review-2026-11-01/qualification/scratch/tmp-wave08-r3 RAYON_NUM_THREADS=1 python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave15-r2-astra-independent-spec.json
python /workspace/bac-review-2026-11-01/qualification/verify_bac_run.py /workspace/bac-review-2026-11-01/qualification/wave15-r2-astra-independent-spec.json
```

Both runner and verifier completed with exit 0; both execution sessions are CLOSED. Actual independent result: **26 PASS / 25 deselected**, no skips/xfails/xpasses/warnings; 103.91195702552795 seconds runner wall, 100.47 seconds pytest-reported time. This is execution by this reviewer, distinct from received root results. The selection includes all six original failing cases and the other selected restore/export/native/cache/NaN/historical controls. No overlap counts are summed.

Verifier binds base `f22d77af39cd67bb8102854f38f43baa50a1381c`, tree `e18e85776f16b507040c1671310b17595fb26b21`: 179 source guards, 573 config digests, 13 protected artifacts, one process identity, 14 worktree registry records / one available. Source/index/import/threads/fixture custody **PASS**. Log `/workspace/bac-review-2026-11-01/qualification/wave15-r2-astra-independent/astra-independent.log`, SHA256 `a0a8066845296fea476e316f10dcf34a3189623d1af74944277d34afea5e2d04`; manifest SHA256 `72cc8f5e7bed80912f0236ca5b60155dfbc274dc7b9d7f0b601e8c32eb77ad21`; harness SHA256 `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`.

Post-run independent SHA256 checks of all five counted files match R2: compiler `521a72dd6d0a155c89a216fa038828cc8054520714a58cc0e0420c2da9d09e92`; compiled `0d994462f86e721ddd38ca32f286da05cc602d63a0e9e424e84a10320399c2dd`; effective-run test `1685b2c09aa59c6687a49accebf62be591e64716f91469ef85e332d8b765cdd9`; compiled-roster test `bd5a364931be94f2930c278ab5f21bf1a497814e727d93057f538da3bf7e2f38`; metadata producer `811dc301202433253832f84743cba65823f0d7c273a73d65e376d35a5e2f6beb`. Scope remains five files / 3480 lines with 4700 projected ceiling.

**Final bounded handoff: specification APPROVED; quality APPROVED; D1/D2/D3 ADDRESSED, independently exercised.** No remaining blocking finding in this scoped change. Root full-51/CLI terminal outcomes are not claimed here. Broader current-owner, full-suite, actual world/lifecycle/physics, integrated native/learning/restart/E2E and final BAC acceptance gates remain separate and owed. The test-world native future witness does not authenticate actual environment world identity. R1 six failures and the earlier empty-selector non-RED remain preserved above.
