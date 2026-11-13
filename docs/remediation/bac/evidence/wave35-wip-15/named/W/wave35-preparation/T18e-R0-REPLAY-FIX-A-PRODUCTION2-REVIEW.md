# Replay fix A production2 — scoped generic-syntax re-review

2026-11-13. **A-P1 UP047 addressed; new A-P2 UP049 requires correction. QUALITY remains CHANGES REQUIRED.** Prior bounded SPEC approval for B1/B2/B5 and flat/PER/shared B4 is preserved: no behavioral or type-contract breakage was found in this narrow diff. No R80 runtime GREEN is claimed; root deliberately held runtime after the lint prerequisite failed.

## Exact source and retained boundary

R80 supplied candidate `2b9ae797423157a2e743ab54aadcaa9f2d31c00b`, base `678513c7540a61114d59a17d1b1e0eb8a06ce0a2`, manifest SHA256 `aaf31706a22667c9ec8f9c288f355ffdb389b0ab62394c461da9143607b3602e`. Initial production review `T18e-R0-REPLAY-FIX-A-PRODUCTION1-REVIEW.md` remains unchanged at SHA256 `eedd38a65a53e6a8285928099b6ac7812cb12e29312ec1c6123f810bc84f6ea7`.

Measured and hashed the same five whole bodies before reading the changed source: contract374/flat728/PER1164/test1098/domain371 =3735 lines, within planned4471 and hard5000. Only contract differs from R79, now SHA256 `c13aa14190b5ab5be1cea2a520f920011abaf41f9b6a903537f2f47aea6c4a39`; all other four hashes match the initial production review exactly. Updated report SHA256 `841349f2b792033d70f491e6a27bf36961311caa842a5adedad02bf59365e282`; production2 diff SHA256 `d55b3c5bfde4985df6598a1090f073b09c486006ce69d6c71886fb68bc61d77c`.

Inspected the narrow diff, actual affected contract context, report and root-produced diagnostic/result evidence. No new implementation/helper/caller body, application import/runtime, source edit, Git/index operation, branch/worktree/source copy or delegation. Only this review artifact was written. Root type-checker metadata/inline public-result declarations are evidence, not a newly inspected application source body or reviewer execution.

## A-P1 closure and new A-P2 — P2: private function-local type parameter names fail Ruff

The four decorators now use modern function type parameters, and unused module-level TypeVar/ParamSpec declarations/imports are removed. The ReplayCustody owner bound, ParamSpec arguments, result-preserving Callable/Concatenate signatures and PreparedReplay return transformation are unchanged. Admission, required-lineage checking, forwarded arguments, owner guards and issuance bodies are untouched. UP047 is genuinely resolved.

However, `replay_contract.py:129,140,151,163` retains leading underscores on function-local type parameters. Actual R80 Ruff reports **11 UP049 errors**: `_Owner`, `_Result`, `_Arguments` for each read/mutation/sample decorator, plus `_Owner`, `_Arguments` for preparation. This is new mechanical quality breakage from the syntax conversion, not a change in the semantic requirement or an external gate.

Rename each function-local parameter consistently, for example to `Owner`, `Result`, `Arguments`, including its Callable/Concatenate annotations and nested wrapper annotations. Preserve the owner bound, `**Arguments`, required public keywords, result preservation and prepared-result transformation. Do not suppress UP049 or revert to erased/defaulted signatures. A targeted contract Ruff and Black development check should precede the next freeze; root retains final exact-candidate static/type/runtime verification. No broader behavioral change is requested.

## Actual R80 evidence and limits

Read `/workspace/bac-review-2026-11-01/qualification/wave35-r80-static/ruff-global.log`, SHA256 `99566d6da8b000f7e86b620b85baa954e1a02cf0ceed2e71fdf2f52e205dc99e`: exactly11 UP049 errors, no remaining UP047. Root reports collection54 PASS.

Read actual result JSON and logs in `wave35-r80-types`:

- `owned-mypy`: exit0, four producer files including recurrent,2.465806245803833s. Log SHA256 `71144743c83babea384888a735db0c4daba3d4d7b7942b6839984bd5c21b52bb`.
- `public-types`: exit0,1.4396026134490967s. Actual inline assert_type calls verify flat/PER/recurrent `prepare_serialized(..., expected_obs_dim=None, lineage=None)` returns PreparedReplay. Log SHA256 `5d4b6d285b77932e3d08212c3b4974d0a803f98ec60408ac6ccf6a063fa6c19e`.

Both result records identify the exact R80 candidate/manifest above. They confirm that syntax conversion preserved type behavior; identical short success-log hashes across revisions do not alone bind source, so the accompanying result metadata matters. Complete source/process custody remains root-owned. No new global missing-lineage run or runtime execution is inferred from these type results. R79 actual caller diagnostics and53+isolated1 runtime passes remain their original source-bound evidence; they are not relabeled R80 passes. R80 ordinary/poison and independent runtime remain **UNRUN**, appropriately held until lint is clean.

This scoped review preserves prior B1/B2/B5 SPEC approval and the existing independent test assessment, while withholding QUALITY approval for A-P2. Recurrent B3/B4/defaults/formatting, B6 CUDA capability/completion, external caller migration, final fixed-source checks and final fresh programme design/implementation reviews remain required. No package completion or scope waiver; accounting remains28 qualified/38 remaining/66 total.

Before final seal root confirmed collection54 PASS4.538585663s, owned Black PASS1.561013222s, all collection/static/type815-source custody verified, and all sessions CLOSED. These final custody/formatter outcomes are root-attributed. Default601 remains separately recurrent; runtime specifications remain deliberately UNRUN. This does not change the A-P2 QUALITY disposition.
