# T18d none selected scale — TESTS ONLY baton

Status: authored for root's pinned-spec collection and causal RED; no runtime qualification. Only the new test source and this ignored report were written. CP, BANK and the existing conversion test remain frozen and hash-identical to the brief. No pytest, import, compile, probe, production edit, index/branch/worktree mutation, source copy, subagent, installation, deletion or publication was performed.

## Authority and inventory

Read first: T18d-NONE-SCALE-BRIEF.md. Also read AGENTS.md, wave30-preparation/T18d-original-task.md and T18d-readiness-report.md, published CURRENT-CURIOSITY-BANK-CONTRACT.md and CURRENT-CURIOSITY-CHECKPOINT-CONTRACT.md, wave32/r1-checkpoint-receipt.json, and wave29 verified owned-call/HC-replay capsules. The initial attempt to read readiness from wave33 returned missing; the required wave30 report was then read. Current owner no-backwards-compatibility ruling governs. No new global design or compatibility path is proposed.

| Whole source slot | Actual lines / ceiling | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/curiosity_checkpoint.py | 1135 / 1200 | 9499dad4774ab6df303e970ff2871436e9f018c5e5bbf8482faaf7df1873d740 |
| src/townlet/exploration/scoped_curiosity.py | 1282 / 1300 | a122097fa313e335a4213499627dc1b071aa02600984829dc08d80ddba0bb363 |
| tests/test_townlet/regressions/bac/test_pw_scope_conversion.py | 1456 / 1456 | 672a1441520b69cfda5045220a29d2abf891afa7fbad8d461c5e22c91adab893 |
| tests/test_townlet/regressions/bac/test_none_scale.py | 233 / 1000 | 646797d6f256c6396f57b0203413614bb0c4b7b2786b764ed62c425b45e53a13 |

Actual total 4106; ceiling total 4956 <= 5000. The original three-source baseline is 3873. Inspection stayed within these four source paths; no fifth implementation/test/helper/provider/RP/WS/ENV/HC source or runtime introspection. Public prose and file-name metadata are not extra implementation reads. Root remains sole integration/index/publication owner.

## Authored tests and dependencies

Actual fixture imports use `tests.test_townlet.regressions.bac.test_pw_scope_conversion`: explicit re-export of its module-scoped compiled fixture, IDS, Rig, policy, independent equal witness and actual-owned live witness. There is no copied fixture, fabricated native checkpoint, fake provider, value-only accepted token or new helper source. This path is authored but intentionally unimported pending root collection.

Rig supplies actual ENV bind/begin/reset/activation, actual BANK provider construction, actual ENV step, completion/close, real ENV completed parent preparation/callback and parent installation. Cooperative other-role receipts and synthetic 3D/two-action curiosity geometry remain the existing component boundary; full simulator/parent continuation is not claimed. None policy is explicitly fixture-authored initial_weight=0.4 and asserted positive/exact before reward work. Mixed `(True, False)` supplies both eligible and inactive rows without inventing an all-done ENV stepping guarantee.

Expected parametrized identities (22 total, statically counted; not collected):

- `test_none_bank_selected_scale_and_unchanged_retry[shared|per_world]`: genuine eligible/inactive reward; exact raw0 and selected scale0 at the BANK result; raw*scale0 separately; unchanged native none state; correct shared aggregate/private per-row receipts; zero predictor clock/counters/loss; true eligible BANK cursor advance; real exported reward/local cache; unchanged reward/service retry and BANK revision.
- `test_none_current_live_cache_restore_replays_and_continues[shared|per_world]`: current live cache roundtrip under actual accepted capability; source input edited only after preparation to demonstrate owned publication; exact unchanged restored transport; reward and service retry; healthy next ENV step, zero scale and no predictor work.
- `test_none_current_completed_parent_restore_and_next_episode[shared|per_world]`: real completion and retained completed ENV preparation, actual parent validation/install; prepared caller and retained callback views cannot mutate installed state; source remains unchanged; next genuine accepted episode/reward/service/retry.
- `test_none_invalid_current_cache_refuses_without_mutation_and_retries[fault-phase-scope]`: four faults (`selected_nonzero`, `raw_nonzero`, `missing_scale`, `old_schema`) x two phases (`live_episode`, `completed_boundary`) x two scopes. Nonzero selected scale edits both the actual local cache and step reward representation coherently; validation cannot reject only their disagreement. Exact missing-cache-field and obsolete-schema refusal remain required. Refusal preserves BANK revision, checkpoint, actual live native/IDs/storage witnesses, input and ambient Torch RNG. The unchanged current state then prepares/installs and genuinely continues on the same destination; no fallback/normalization.

The first selected-scale assertion is in `assert_reward`, after exact raw/eligibility checks. Suggested initial causal selection: `tests/test_townlet/regressions/bac/test_none_scale.py::test_none_bank_selected_scale_and_unchanged_retry` (both scopes). Expected source-backed RED is actual eligible scale0 versus current0.4. Import/fixture/API errors are not acceptable causal RED.

The later negative cases begin from a genuine zero-scale producer export and never manufacture a passing native source. They become reachable after producer repair. A producer-only repair must still fail CP's old cached-scale requirement on healthy restore; a validator-only repair must still fail the direct BANK scale assertion. Coordinated CP+BANK production repair is a separate root baton.

## Static evidence and runtime gates

Scoped `.venv/bin/black --check tests/test_townlet/regressions/bac/test_none_scale.py`: exit0, one file unchanged. Scoped `.venv/bin/ruff check` final: exit0, all checks passed. Initial Ruff reported fixture-import F811; explicit fixture re-export fixed that, then scoped Ruff import sorting was applied only to the new file. No behavior/runtime verification is inferred from formatting/lint.

`git check-ignore` confirms this report path is ignored. Last status showed only the new test untracked. Exact baseline hashes above confirm no frozen source changes. Root should perform its guarded collection/import/source/resource checks, actual causal RED and independent Astra authored review before releasing any production authorization. No runtime PASS, collected count, fixed/complete prerequisite, T18d closure or increase in original28/66 releases is claimed.

Full T18d facade/global selector/current HC/parent/POP/runner/native replay learning, T26, full/default/coverage/slow/hardware, final54requirements22lenses and exact-tip CI remain open as stated in the brief. Existing ordinary current BANK live continuation remains supported; this test adds no broader simulator promise.

## Separate CP+BANK production baton

Root explicitly authorized only CP+BANK production edits after reporting independent Astra authored SPEC/QUALITY approval with no findings, collection of22 cases in5.9403s, and two genuine causal REDs in16.7776s at actual eligible scale `[0.4, 0]` versus required `[0, 0]` for shared/private. Root reports custody355/573/13/3process PASS and all runtime CLOSED at candidate816728bf based on c1de. These are root-attributed prerequisite results, not worker-run evidence.

Implemented only two local selection changes. BANK's existing actual provider callback still computes raw novelty and follows the same observation/custody path; it now selects scale0.0 for none before the unchanged adaptive-current-weight and other-initial-weight branches. That selected value flows into the actual returned reward, pending reward and local cache in both scopes, including genuine retries. No facade rewrite or postprocessing hides a different BANK value. CP's existing nonadaptive exact cache-scale check now expects float32/device-matched0.0 for none and retains initial_intrinsic_weight for other nonadaptive families. Existing exact comparator and raw-zero requirement remain active. A cached none nonzero scale is rejected, never normalized, migrated or interpreted through an old-schema fallback.

Provider work, eligible/inactive grouping, service clocks/counters, gradients, phases, source/origin custody, explicit shared mode and adaptive bound validation are otherwise unchanged. Both existing/new test files remained frozen at their prior hashes. No fifth source inspection, test edit, pytest/import/compile/probe, index mutation, commit/push, copy/worktree/branch, installation, deletion or subagent occurred in this baton. Current status shows root's staged new test plus only the two authorized unstaged production edits; worker did not stage anything.

| Final whole source slot | Actual lines / ceiling | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/curiosity_checkpoint.py | 1138 / 1200 | 4de4c481eca21fb3d7fa9aea8804c2b2875c63df6077046e7e286470b6faeb5a |
| src/townlet/exploration/scoped_curiosity.py | 1284 / 1300 | 294ef0f8d9f11e74869567e21f2ca44b623fe1cd54ca5c3eb59819c80681a05f |
| tests/test_townlet/regressions/bac/test_pw_scope_conversion.py | 1456 / 1456 | 672a1441520b69cfda5045220a29d2abf891afa7fbad8d461c5e22c91adab893 |
| tests/test_townlet/regressions/bac/test_none_scale.py | 233 / 1000 | 646797d6f256c6396f57b0203413614bb0c4b7b2786b764ed62c425b45e53a13 |

Final actual total4111; ceilings remain4956. Exact `git diff -- src/townlet/exploration/curiosity_checkpoint.py src/townlet/exploration/scoped_curiosity.py` stdout SHA256: `78882ccc2971dd5aadd4b7a750615964a1d1eb70adbd601a95cf5626265a1a9c`. The production diff adds five net lines across the two named sources; it is not saved as a source copy.

Scoped final Black `--check` for CP+BANK: exit0, both files unchanged. Scoped Ruff check for CP+BANK: exit0, all checks passed. No worker runtime GREEN is claimed. Ready for root's focused2, then full22/coherent verification and independent Astra actual fixed-source review. Whole T18d and all previously recorded integration/release gates remain open.
