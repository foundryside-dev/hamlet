# POP standalone step and cleanup implementation handoff v1

2026-11-14. APP bytes frozen after the exact root implementation baton and separately authorized Black-only formatting correction. No application tests/imports, collection, Git operations, branches, worktrees, source checkout or deletion performed by this writer. Root owns runtime capture and qualification. This prose is a handoff, not a new acceptance record.

## Causal basis

Root supplied R123 RED result at candidate `ce0ae1e1d54bbe7042a3651f339bce6db1f54088`: source/index/import/thread custody PASS, collection23, runtime9FAIL/1PASS in15.16s. Eight focused failures split into four omitted-lineage sample failures before the sentinel and four physics failures exposing the actual unsupported quarantine reason. Original shared-none also failed at sample with a cleanup note; original env-stage control passed. This writer did not execute or independently qualify that capture. Original traces and source remain under root custody in `wave35-r123-pop-step-red-attempt-1` and `../evidence-management/pop-standalone-step/r123-executed-source`.

## Exact implementation delta

Compared with root's R123 inert executed-source files using ordinary `diff -u`, without Git:

- POP800: `sample_batch(request)` becomes `sample_batch(request, lineage=None)`.
- POP2115: exploration quarantine reason `population step failure` becomes `runtime_failure`.
- Existing parent-handoff444: its standalone replay witness adds `lineage=None`.
- New focused test91–94: Black collapses the existing `torch.equal(...) for ...` generator expression onto one line. No assertion changes.

No other implementation/test differences were present in those three comparisons. New tests retain real producer delegation, explicit standalone lineage, both curiosity scopes, physics/sample failure seams, completed-real-cleanup-then-secondary-error coverage, original exception identity, exact reasons/accepted identity, notes, health refusal, unchanged Q parameters/optimizer counts and nonreexecution.

## Frozen source seals and whole-body budget

| Body | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/population/vectorized.py` | 3163 | `ea05fddb584cc7836e663e2aa2cada3c4dca1fcbc08584e030efa1816ac4bf38` |
| `tests/test_townlet/regressions/bac/test_parent_intrinsic_handoff.py` | 791 | `2621285b5d259be7f4bf8eb5e7b2ae1d2eb29c867923a7e2aa043c9e6246f7ef` |
| `tests/test_townlet/regressions/bac/test_population_standalone_step_cleanup.py` | 102 | `d59505029082a518f888bdc5937a6e23fbb56aac1681d2ce901e504ed6b37509` |

Total4056 lines/three whole bodies, within4950/three. No extra producer/helper body was opened. The authored RED snapshot `T18e-R0-POP-STANDALONE-STEP-CLEANUP-RED-v1.py.txt` remains unchanged, SHA256 `486ea77ed0e3046c5e0f5bf907d311e6ced4c00035d1912ba3ef9a0050796909`.

## Scoped static check history, including failures

1. Initial `uv run ruff check <three paths>` and `uv run black --check <three paths>` each exited2 before tool startup: `Failed to initialize cache at /home/agent/.cache/uv`, opening `CACHEDIR.TAG` failed with read-only filesystem error30. No code failure is inferred from those attempts.
2. Retried with `UV_CACHE_DIR=/tmp/bac-pop-step-uv-cache uv run --no-sync`: scoped Ruff exited0 (`All checks passed!`); scoped Black exited1, requesting only the generator-expression line collapse in the new test. Its diff was inspected before root authorized that formatting correction. POP and the existing parent test were already unchanged under Black.
3. After the authorized formatting correction, reran both scoped checks with the same writable cache and `--no-sync`, using all three exact paths above. Ruff exited0 (`All checks passed!`); Black exited0 (`3 files would be left unchanged.`).

These are scoped lint/format results, not application test results or broad static acceptance. Root runtime capture, fresh independent review, unchanged original behavioral gates and separate parent/constructor/restore prerequisites remain pending. No readiness change, active-parent completion claim, copied authority, compatibility adapter or acceptance waiver is introduced.
