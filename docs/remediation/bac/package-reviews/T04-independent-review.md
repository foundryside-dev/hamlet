# T04 final independent SPEC and QUALITY review

Verdict: **scoped SPEC PASS and QUALITY PASS** for the bounded T04 lossless-sidecar repair on the fixed final-r4 candidate. No remaining material supported-case finding identified. This is not whole-repository or BAC programme acceptance.

## Fixed candidate and inventory

- Root: `/workspace/hamlet`; HEAD `1f9d831a8fe76ab00e06774ef6888985f6c2aec2`; index tree `d2b46a1bd74eb187ecbe7c1cdd5e9723d351e5c4`.
- Root candidate manifest: `wave03/final-r4-candidate.json`.
- `src/townlet/universe/declarations.py`: 724 lines, SHA256 `983336171a2e49d4e91f86dbbc03f10d9e7bde58a86ab5e8a49cb51dc18f5a6c`.
- `src/townlet/universe/compiler.py`: 976 lines, SHA256 `521a72dd6d0a155c89a216fa038828cc8054520714a58cc0e0420c2da9d09e92`.
- `tests/test_townlet/regressions/bac/test_sidecars.py`: 251 lines, SHA256 `dbe04abfaa9e97aecc75dcc5d102fd7740f22f471461e0d2bb6c77f15e449e15`.
- Same single independent probe `wave03/T04-independent-probe.py`: 140 lines, SHA256 `fd3cc5dd70c2e275a0cc73e6b09ed6b531e6aa5ea489db6d61807550142e3e0b`.
- Total source inventory: 4 files / 2,091 lines. No additional implementation/test/helper sources inspected. Native YAML fixture DATA only was copied into temporary directories. No production/test/index changes, repository or source-tree copies, branch/worktree creation, or delegation.

## Independent execution

Root explicitly froze all writers and authorized one CPU slot. Exact command, from `/workspace/hamlet`:

```
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' T04_EXPECTED_HEAD=1f9d831a8fe76ab00e06774ef6888985f6c2aec2 T04_EXPECTED_TREE=d2b46a1bd74eb187ecbe7c1cdd5e9723d351e5c4 .venv/bin/python .superpowers/sdd/2026-11-01-bac-remediation-upgrades/wave03/T04-independent-probe.py > /tmp/T04-independent-probe-r4.log 2>&1
```

Exit status: **0**. JSON stdout/stderr artifact: `/tmp/T04-independent-probe-r4.log`, SHA256 `9ab25ed535daefcb9d9a6a330ec9503fed5870666abeec11aa6a69830aab82cb`. Full output was inspected. The probe asserted supplied HEAD/index identity, no unstaged tracked changes, and all three core hashes before and after execution. It asserted townlet imported under `/workspace/hamlet/src`, torch thread count was 1, and CUDA visibility was empty. All assertions passed. CPU slot released to root after completion.

## Whole-contract reassessment

The complete bounded T04 path was reassessed: authored sidecar validation before selection, independent handling of recording/run_metadata, canonical lowering, semantic duplicate comparison, provenance retention, compiler training identity, and portable cache behavior. The final bool wrapper around float.hex equality changes the declared return type without changing the comparison. No capability removal or new strict coercion policy was introduced.

Independent successful controls:

- Omitted versus explicit nullable recording defaults remain equal; precise top/nested mapping and leaf origins were asserted, including the explicitly authored nested optional field.
- Run metadata whitespace normalization remains accepted for equal duplicate values.
- Reordered criteria mappings remain equal.
- Optional-field differences, ordinary nested leaf differences, null-versus-mapping differences, and missing-versus-explicit-null members produce CompilationError. Inspected diagnostics include both relevant authored origins; the absent-member side points to the available container.
- Full compilation of isolated missing/null alternatives yields distinct training hashes; their combined duplicate now refuses.
- Boolean/integer, integer/float, nested-list boolean/integer, and signed-zero alternatives each independently compile with distinct training hashes. Their duplicates now refuse with located collision diagnostics.
- Malformed list, integer, and string sidecars refuse despite a valid duplicate. When both duplicates are malformed, both authored extra fields appear in diagnostics.
- Genuine `use_cache=True` hit succeeds while stage 6 is mocked to fail if recompilation occurs, preserving training DTO and hash.
- Moving both sidecars between accepted placements retains training identity after cache invalidation/recompilation.
- Changing nested recording.enabled invalidates the cache and changes both consumer value and training hash as expected.

The final probe verifies mixed integer/string nested-key conflict handling at declaration and full compiler entry points: it now produces located CompilationError instead of the earlier TypeError. Honest scope limit: either isolated mixed-key sidecar still encounters the existing downstream `ValueError: exploration authoring mappings require string keys`. This review does not claim fully supported mixed-key runtime authoring, change that restriction, or infer a broader engine repair requirement.

## Root evidence and review history

Original causal RED (14 intended failures, 2 controls) and original 16-case GREEN remain attributed to root, as documented in `T04-independent-review-r0.md`; they were not independently rerun. Original r0 report and `/tmp/T04-independent-probe.log` were preserved.

Root additionally reported causal RED for the three permanent missing/null and mixed-key regressions and the four typed-value variants before their corresponding repairs. Root reported 23 permanent T04 plus B07/related tests passing (48 total, 196.88 seconds) immediately before the final bool return wrapper. Root also reported configuration tests (137), B08 tests (128), and final-source mypy (187 files) passing. These are explicitly root-supplied evidence, not this reviewer's independent executions. The final pinned-source independent runtime above supplies fresh behavioral evidence after the wrapper.

The original permanent regression coverage supplies both sidecars separately/together/mixed, top-level controls, malformed duplicates in both directions, DTO and MessagePack round trips, and equal-duplicate source origins. Static reassessment found no remaining divergence between these tests, the bounded specification, and final implementation. Prior conflict findings are resolved within T04; broader repository qualification remains root-owned.
