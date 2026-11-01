# Source provenance

Original scoped review/execution retains its recorded actual identity. The final source binding verifies the reviewed files are identical in qualified source `b3003550b7c1dad76a52e596b2af01658fa2b92d`, tree `aecfaaa84cd58fafd8ac1f6ca67052639d570ed4`; no execution is relabeled as occurring at a later HEAD.

Original `T14-estimator-independent-review-r2.md`, SHA256 `630f2cafbcc6edf50a279a0f3907d30d7770201930c862e42860cb0faeb27817`, retained unchanged. Portable rendering normalizes execution paths.

# T14 estimator consumer repair — independent static review R2

Verdict: PASS for the exact bounded test repair, with no P1, P2 or P3 finding. Runtime qualification is pending coordinator evidence. This verdict does not release T14, qualify the full gate, establish native-current admission/C07, or complete BAC.

## Scope and custody

Reviewed both authorized source files in full in the existing `/workspace/hamlet`, and independently inspected their precise `git diff HEAD` rather than relying on the owner's description. Observed HEAD: `bb7cf5f9a545fab0f5b4ecfcc042571e44c34cdd`.

| Whole source | Lines | SHA-256 |
| --- | ---: | --- |
| `tests/test_townlet/regressions/bac/test_per_estimator.py` | 1238 | `2e08f44397d626a95b4b0f5142021e408250b50067fbfc16c01f2c6ae4459866` |
| `src/townlet/training/historical_checkpoint.py` | 675 | `74709ebedc0c84208c3b30debd4101bc3bc67ca73f9df1a4be8a1aafff0894a4` |
| Total | 1913 | Exactly two whole source files |

No additional helper, fixture, test, replay-buffer or other implementation source was opened. Read applicable AGENTS.md, CLAUDE.md and STATUS owner rulings, accepted T14 interface proposal R1 (including sections 4–6 and acceptance item 10), and estimator-owner causal/implementation R2 prose. The proposal's historical preparation-status wording does not override root's identification of it as the accepted contract.

Root reports the staged R2 candidate tree as `aecfaaa84cd58fafd8ac1f6ca67052639d570ed4`, with 112 guarded paths and ten changed files; only the estimator test differs from source R1. Those broader candidate facts are attributed to root, not independently audited beyond this two-source boundary.

## Independent source/spec assessment

The test delta changes only `test_hc_historical_per4_domain_and_standard_sequence_policy_versions_stay_distinct` at lines 970–999. Previously its `(standard,5)/(sequential,6)` loop inferred that every `current + 1` was unsupported. That inference contradicts accepted additive sequential7 support. Replacing the inference with explicit supported/refused sets repairs the consumer expectation without removing the boundary checks.

The resulting matrix accepts standard5 and sequential6/7. It refuses standard6/7, sequential5/8/6.0/7.0/True/"7", and unknown-kind7. The `type(version) is int` guard is necessary: numeric equality would otherwise place 6.0 and 7.0 on the accepted branch. Sequential5 remains historical-only, sequential8 is the true next unsupported version, and standard7 cannot borrow the sequential allowance. This is an explicit contract table independent of implementation introspection.

HC's sole diff against HEAD is the shared sequential tuple changing `(6,)` to `(6, 7)` at line 41. `_supported_formats` at lines 45–48 retains historical exact 9/6/kind-specific4,4,5 separately from current demo10/population7. `_formats` and `HistoricalAccessPolicy.__post_init__` each enforce exact integer versions and known exact-string replay kinds before using that same predicate. Thus the repaired policy constructor expectation matches the actual shared gateway implementation and accepted design. There is no broadened global version comparison, type coercion or wrong-kind allowance.

The historical PER4 prefix of the changed test is byte-preserved: actual archived source under demo9/population6, archive/fresh-episode mode, active-zero/count-four assertions and recorded-full-resume refusal. Neighboring flat-PER5/6 classification/codec coverage at lines 940–967 is unchanged, including PER4/7/bool refusal through both resolver and decoded-policy routes, envelope roundtrip and source immutability. Genuine archive/export tests and the rest of the estimator, finite update, RNG, mask, stable-ID, corruption and restoration controls remain unchanged.

The repaired matrix directly exercises policy construction; it must not be described as a new actual sequential producer/codec or native loader test. Both gateways sharing the predicate is source evidence, not proof of complete native admission. Actual replay schema validity, raw population6 versus planned demo10/population7, explicit attachment versus automatic selection, inference classification versus an inference loader, and evolved optimizer continuation remain distinct. Nothing in this change or the owner's notes falsely closes them.

## Static evidence and failure identity

An independent standard-library AST/hash audit compared HEAD text to current text entirely in memory. Both contain 47 test functions, 119 assert nodes, 25 pytest.raises call sites and 83 top-level AST nodes. Exactly the named function's AST differs. The HEAD test is 1234 lines at SHA-256 `6a60791ace134851ae464cbef4b12244e950065996f5e0a135da7cfa38e77fc9`; the current file matches the dispatched repair hash above. No project imports, collection, pytest or project runtime were executed by this reviewer. Counts support preservation; the concrete unchanged assertions and expanded matrix establish that this is not a count-preserving weakening.

Read external `qualification/wave08-full-r1/failed-custody-postflight.json`: FAILED, exit 2, one failed / 6622 passed / 16 skipped / 16 warnings, 1991.9018378257751 seconds. It identifies this exact test as the failure, original base `01f2f64f42c2932177729607b337419355cb2720`, candidate tree `324438ad58d9d5a85bba54e18be1ee225ada5969`, and log SHA-256 `b704b51a2468f7fcdcf3d77ef3c3ef8fe4bcbcd8e391125683b527f5fc4a456d`. Its custody counts are 112 source paths, seven reviews, five process identities, 573 configs, 13 artifacts and 14 worktrees. The causal owner note attributes the failure to the sequential7 raises context; static inspection independently confirms that contradiction. This reviewer did not rerun or independently open the raw failure log.

John's approved 32-commit email-only metadata rewrite and preserved original local bundle are root-reported governance/history facts. Original R1 runtime evidence remains attached to actual 01f2 identity; it is not relabeled as execution on bb7cf5f9 or the repaired candidate. Owner-reported Ruff/Black success is static author evidence, not a reviewer runtime result or full gate.

## Disposition

No capability removal, unapproved reduction, inference expansion or test weakening found. No repair requested. Root may continue its already authorized fixed-candidate validation; this worker remains stationary pending separate runtime clearance. Scope-limited static approval is the only approval issued here.

Only this ignored prose was written; `git check-ignore -v` confirms `.git/info/exclude:7:/.superpowers/`. Read-only worktree listing shows 14 existing worktrees; none was created, altered or removed. No source/test/index/commit edits, branches, source copies, project runtime or subdelegation occurred. Existing instructions and actual tool approvals apply: the failed durable-rule attempt created no durable rule and no user-only fallback. User preservation and approved History A remain controlling over conflicting blanket deletion guidance.
