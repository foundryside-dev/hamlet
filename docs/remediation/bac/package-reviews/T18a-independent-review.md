# T18a fix round 1 — independent scoped re-review

Verdict: **PASS for the scoped repair; both original P2 findings ADDRESSED.** No new blocking spec or quality finding was identified in the repair. This is not a full-wave release or repository-green verdict.

## Exact candidate and evidence identity

Reviewed actual joint-wave snapshot `/tmp/bac-verify-wave02-3d1d21cff5`, base `050a1a70e979aa03724219b81e848093820f044f`, staged tree `3d1d21cff5abdf60b630f97da0cdb09bf8ccd036`. The two complete added-file bodies in `task-T18a-r1-candidate.patch` independently matched the snapshot; patch SHA256 `3cadbe4b1f18123ddb8dbf8262c88c00d17a614a4d30950316a6fe795634dc8b`. Read fix patch, updated implementation receipt, scoped candidate metadata/review package and whole-wave manifest. Original review and P5a/P1 task authority remain the review baseline.

Actual inspected source inventory is exactly five files / **2391 whole lines**. Other wave files were hashed only for manifest integrity, with no source contents displayed, searched, inspected or used for code review. No sixth helper/probe/fixture/compiler source was opened or created.

| Source | Lines | SHA256 |
|---|---:|---|
| src/townlet/config/exploration_policy.py | 653 | 496b988555bc0f23f1a6e335386102acbc1450df1d064d87cfd616a0d953299a |
| tests/test_townlet/regressions/bac/test_exploration_policy.py | 447 | 77ed751bb431c5203b6c38354b3f6f6e583d4c4a699df5d94d9bd89fd35eafc2 |
| src/townlet/config/drive_as_code.py | 605 | 870e44fbc55f4bc7a221e7272cebea893ff95bfe37f23c6e4e01c4e80595150c |
| src/townlet/config/training_v2_config.py | 443 | d103aafbfe4e7fd4e957b71fd0651c6b6d8bebb98de4581d9d53e2356907ca68 |
| src/townlet/config/bac_options.py | 243 | 1de08a7cc36c49772254d8b9dc2d8adf3cac76533eecba5c36568745bc48c8f1 |

## Finding disposition

**R1 — premature training-preset capacity validation: ADDRESSED.** RP obtains the versioned omission table from unchanged OP using empty authored options, then applies original source/service declarations and selected typed > raw > derived provider values. Final selected batch participates in derived capacity and capacity validation. There is no blanket exception suppression, DTO construction bypass, or weakening of standalone OP validation.

Independent inline API probes using actual canonical training DTO batch32 confirmed, for each of RND/adaptive/ICM: selected raw batch8 with explicit capacity8 succeeds; capacity7 fails with a capacity diagnostic; omitted capacity is `max(2*N,8)` (16 in the fixture), not the overridden training32. Typed ICM batch4 overrides raw8 and accepts typed capacity4. Standalone OP still rejects authored capacity8 against training32 for both RND and ICM. These probes directly reproduce the original finding and negative controls rather than relying only on the implementer's tests.

**R2 — contradictory portable policy and role validation bypass: ADDRESSED.** Strategy-owned provider schemas now require exact parameter maps. Required selected scalars are validated independently of transported annotations; duplicate RND/adaptive values and ICM batch/service capacity must agree. Required role activity must match the selected schema. Execution identity also uses schema-owned activity, so a role edit cannot silently exclude an active knob.

Independent inline probes verified both direct dataclass reconstruction and `from_dict`: all five valid policies preserve complete portable payload and execution identity; extra provider keys fail for all five, empty provider maps fail for all non-none providers, and RND/adaptive feature conflicts, active scalar NaN hidden behind an inactive role, and finite active fields falsely marked inactive all fail. The expanded focused suite additionally exercises ICM batch/capacity and adaptive scalar conflicts. Preserved unknown nested raw presets round-trip in every valid strategy. The repair does not collapse inactive authoring into execution identity.

## Independent execution

Used `/workspace/hamlet/.venv/bin/python` from the fixed snapshot, with `PYTHONPATH=/tmp/bac-verify-wave02-3d1d21cff5/src`, `CUDA_VISIBLE_DEVICES=`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, and `torch.set_num_threads(1)`. The inline harness asserts the actual imported `townlet.__file__`, all five scoped source hashes, and all 18 source hashes in the actual whole-wave manifest before probes, before pytest and after pytest. No git operations or implementation edits were performed.

The combined bounded command is `pytest.main(['--no-cov', '-p', 'no:cacheprovider', 'tests/test_townlet/regressions/bac/test_exploration_policy.py', 'tests/test_townlet/unit/config/test_drive_as_code_dto.py', 'tests/test_townlet/unit/config/test_training_v2_config_dto.py', 'tests/test_townlet/regressions/bac/test_options.py', '-q'])`.

Result: **147 passed in 92.80s** (85 focused + 62 owner), with final imported snapshot and all 18 manifest hashes verified unchanged.

The focused suite's real compiler/compiled transport case passes within that command; compiler and owner-test source contents were not inspected. Worker-reported scoped Ruff/Black/mypy and whole defaults614 results remain attributed to its updated receipt, not claimed as independently rerun here.

## Spec, quality and downstream constraints

Both repairs are confined to the resolver and owned test module. DRIVE, training DTO and standalone OP hashes are unchanged. The additive five-provider contract, immutable ownership, authored/preset retention, exact `eligible_predecessor` phase and ICM `predictor_input_kind='transition'` remain intact. Provider factories, actual reward routing/service, continuation and strict per-world behavior remain later scope, not implied by this approval. No capability removal or reduced provider semantics is approved.

**T03 must first pass original authored partial BaCOptions to RP.** Do not materialize OP against training-preset batch32/capacity8 before RP selects actual batch8. Subsequent overall effective-options materialization must consume RP's actual selected batch/provider/service values with provenance, retain original authoring separately, and must not feed materialized provider derivations back as explicit typed declarations. The worker receipt now makes this integration constraint explicit; T03 must implement and test it.

This review closes only the two original findings on these exact bytes and checks for breakage introduced by their repair. All other wave packets retain their separate review obligations; action-executor changes were not inspected. Coordinator preflight, all scoped verdicts, standing guards and full fixed-sumtree pytest must pass before dependency release. Full suite/coverage/slow/hardware/remote CI were not run by this reviewer, per scope; next mandatory full gate remains G1 or earlier applicable trigger. No mutations except this review artifact, no delegation, no root-ledger changes, and no release authorization.
