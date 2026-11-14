# R112 B fixture repair — implementation freeze

2026-11-13. Tests-only repair is frozen for root qualification and independent actual-patch review. No new runtime PASS is claimed by the author.

## Authority and scope

Applied independent plan review SHA256 `f8936611f9ce317c0818750bbfd5823b4a4e0dc322984dfb1979863960c3f486` and final tests-only grant `wave35/r112-fixture-repair-grant.json`, personally hash-verified SHA256 `b3e5aece7ffedcbc0dac3dcf9f547d9ca1fd43ab27bca31a9562ae821b085467`. Root's supplied R112 checks SHA256 is `b80a99c3519a55f5bf4597e45006b5cab706090abba1e370288af619e994755e`.

Root reports R112 collected838 with every prior836 ID retained, four canonical roundtrip controls and two new late-membership negatives PASS, and all four strengthened operator fixtures FAIL at the exact digest mismatch during their second genuine restoration, zero errors/skips/warnings. This establishes the reviewed causal prerequisite RED before operator repair. It is attributed root execution, not a new author run.

Only application/test write is `tests/test_townlet/regressions/bac/test_replay_cuda_producer.py`. Shared replay_contract881 and historical_checkpoint675 remain read-only and byte-unchanged. No family/core/activation body was opened. No application/test import or execution, child protocol execution, branch/worktree/checkout/execution copy, production edit, token refresh or delegation occurred. This new report is the requested implementation record; historical reports are untouched.

## Final source seals and budget

| Body | Final whole-file lines | SHA256 |
| --- | ---: | --- |
| tests/test_townlet/regressions/bac/test_replay_cuda_producer.py | 2558 | e629acf35a89bb5719945b4c8c9a5578de2dc1c69791038ba2072bb71dabe801 |
| src/townlet/training/replay_contract.py | 881 | 8c0251c3c46e9c296e7b3bb5afcf2f6cdce8083fa22666c5a662be454a9a12f4 |
| src/townlet/training/historical_checkpoint.py | 675 | 74709ebedc0c84208c3b30debd4101bc3bc67ca73f9df1a4be8a1aafff0894a4 |

Actual4114 lines /3 bodies, under reserved4256 /3 (test ceiling2700) and hard5000 /5. Relative to the R112 tests-first freeze48998e43639a1334a752629656a526df7f3bc85ca2bddfe58bfc7d1d947877fd at2516 lines, final repair adds42 lines. Relative to the R111 original2468-line producer, complete tests-first plus repair adds90 lines.

## Implemented changes and preservation

1. `_ArchiveComparison` at1979 delegates to the real superclass tensor implementation and rewraps only detach/clone results as its comparison subclass. Native tensor work/event recording and the final clone's independent storage are retained. Reductions/arithmetic retain base `_CUDAData` results, leaving `self.sum() != 0` behavior unchanged and preventing recursive comparison dispatch. No change to generic `_CUDAData`, HC ownership or production digest guards.
2. Existing `test_archive_clone_repairs_later_count` at2325 preserves all24 stages, the four raw cross-field/sibling hooks, first-restore count3→4 and real clone2/sum1, and separate recording/second-restore observations. Its operator roundtrip now has the local fixture repair needed to satisfy the new type/value/device/fresh-storage postconditions. Public validate begins with its original unnormalized raw witness and keeps digest1, source2/live3 and prepare-only destination4 inventories and effects. Canonical controls and public prepare retain their authentic string digest. Runtime GREEN remains pending root.
3. `test_archive_declared_count_boundaries` at2173 retains all192 Cartesian IDs and exact original metadata-plan/synchronization/clone/target-equality assertions. Count acceptance is separated from family compatibility. Earlier count-invalid cases retain the original count-error expectation, including when kind is incompatible. Count-valid compatible cases still require success. Count-valid incompatible actual calls now require the full anchored family-specific late-kind diagnostic, with clone2 retained and later work on live3/destination4 forbidden. Earlier count negatives continue forbidding digest1/live3/destination4 work. Pure plans keep conservative possible-continuation inventories unchanged; synchronized devices are not mistaken for executed tensor work.
4. Original positive membership test at574 uses real idle owner preflight of explicit0/1 before preparation through installation, retaining standalone lineage=None, prepare selector1 and install selector2. It retains installed values/device1, full serialized equality, install sync exactly(0,1) and no current-selector lookup. Device2 is not enrolled by this setup. The two R112-qualified late-membership negatives at592 remain unchanged: released original candidate, real idle addition0, exact membership refusal, no live publication, stage/complete effects preserved.
5. Added `test_archive_digest_operator_clone_preserves_rejection` at1996 for each family. It uses genuine HC cloning on a digest probe of literal1, checks subclass/value/device and independent plain storage without permissive operator equality, then clears observations and requires exact digest refusal during genuine HC restoration with second-phase clone2 and sum1 work. This explicitly guards rejection preservation alongside the accepted literal0 roundtrip. No blanket acceptance or digest bypass is introduced.

## Static verification personally executed

- `./.venv/bin/black --check tests/test_townlet/regressions/bac/test_replay_cuda_producer.py`: exit0; one file would be left unchanged.
- `./.venv/bin/ruff check tests/test_townlet/regressions/bac/test_replay_cuda_producer.py`: exit0; all checks passed.
- Standard-library AST parse and comparison to an in-memory pre-repair AST metadata snapshot: all57 existing top-level test function names retained; no changed existing decorator AST; one added function, the rejection control. No application imports or collection were performed by this check. No existing parameter list, custom ID list or dynamic case builder was edited.
- Final whole-file line count and all three SHA256 seals above confirmed after static checks.

Root must still verify exact collection and runtime; static AST preservation supports, but does not replace, root's exact node comparison. Expected final collection is840: all838 R112 IDs, plus exactly the two rejection controls. Relative to original R111836, the only four additions are the two R112 membership negatives and two final rejection controls.

## Exact node changes and root follow-up

All nodes share prefix `tests/test_townlet/regressions/bac/test_replay_cuda_producer.py::`.

Added in this repair:

- `test_archive_digest_operator_clone_preserves_rejection[flat]`
- `test_archive_digest_operator_clone_preserves_rejection[per]`

Preserved R112 additions:

- `test_released_preparation_refuses_late_membership_enrollment[flat]`
- `test_released_preparation_refuses_late_membership_enrollment[per]`

Primary previously observed causal RED nodes now repaired, requiring root GREEN:

- `test_archive_clone_repairs_later_count[fixture-formats-flat]`
- `test_archive_clone_repairs_later_count[fixture-formats-per]`
- `test_archive_clone_repairs_later_count[fixture-sibling-flat]`
- `test_archive_clone_repairs_later_count[fixture-sibling-per]`
- `test_archive_clone_repairs_later_count[validate-formats-flat]`
- `test_archive_clone_repairs_later_count[validate-formats-per]`
- `test_archive_clone_repairs_later_count[validate-sibling-flat]`
- `test_archive_clone_repairs_later_count[validate-sibling-per]`
- `test_install_inventories_issuer_material_without_selector_migration[flat]`
- `test_install_inventories_issuer_material_without_selector_migration[per]`

The24 original count-boundary failures are exactly actual route {validate,prepare} × accepted-count case {match,clone,mapping} × incompatible kind/family {standard-per,prioritized-flat,sequential-flat,sequential-per}. Every existing exact ID remains; their now-correct expected result is the exact late family diagnostic, with count and effect-order preservation assertions intact.

Required reviewed root selection remains all192 declared-count boundaries, all24 clone-repair stages, all24 declared-count fixtures, all34 native archive clone boundaries, all21 clone classifications, complete semantic-operator/schema/record-prefix selections, both positive membership cases and both negatives, plus the two rejection clone controls. Preserve the membership diagnosis's neighboring stale revision/currency, real admitted roundtrip, empty/archive-only lazy-selector and preflight controls. Root then owns complete frozen producer scope, required static/core/activation/custody and isolated evidence, exact provenance and independent actual-patch review. Focused or historical PASS must not be summed into overlapping new totals or treated as hardware/B6/whole-BAC acceptance.

No further edit after this freeze is authorized without root's new baton. Unexpected runtime results return to bounded diagnosis rather than production relaxation or assertion deletion.
