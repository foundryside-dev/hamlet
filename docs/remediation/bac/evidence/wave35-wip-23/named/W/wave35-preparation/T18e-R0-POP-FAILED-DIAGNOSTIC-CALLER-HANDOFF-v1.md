# POP failed-diagnostic caller handoff v1

2026-11-14. Implemented only after root released the caller baton following R127 producer30PASS, fresh diagnostic-completion1PASS and independent12 thread/fork probes with custody. Those are root-reported producer results, not executions performed by this writer. Caller APP bytes are now frozen for root's causal pace case and final combined selection.

No application imports/tests/collection, Git operations, branches, worktrees or extra implementation-body reads. Only POP and the existing parent-handoff test changed. Source-owned plan `T18e-R0-POP-FAILED-DIAGNOSTIC-CALLER-PLAN-v1.md`, SHA256 `cccf82e759fadf2163f81d9be236044328af1848882ab03f24eeac9ee17f189c`.

## Exact delta

POP grows6 lines. The existing failed guard retains a local boolean from `_failed_step and _has_failed_step_diagnostic()`, then preserves the original failed-but-unproven refusal. The exploration dictionary value invokes `_checkpoint_exploration_state(*, failed_diagnostic: bool)` at its original evaluation position. That helper uses an explicit `if` to return the real producer failure diagnostic for the proven failed route, otherwise the existing healthy checkpoint. It catches nothing and has no default, ternary, healthy fallback, cache or subset representation. The twelve outer fields and their child-evaluation order remain unchanged. The public smaller checkpoint DTO, retained failure proof and healthy restore refusal are unchanged.

Parent test grows41 lines, confined to the existing pace branch. A transparent real diagnostic observer retains an owned copy; the public POP export must call it once and preserve its entire result. New checks require all twelve literal outer fields, exact version/schema/reasons, current counters/full ledger, actual Q/target/optimizer/replay state, supported absent scheduler and genuine fresh-receiver universe metadata. Every original progress/nonreexecution assertion and exact fresh receiver `Failed or in-progress` rejection remains. A final injected diagnostic-capture exception must propagate by object identity, preventing healthy fallback or stale substitution. No other test changes.

Ordinary `diff -u` against the authorized before snapshots verified these exact deltas; no Git was used. The dictionary remains at the same source location relative to Q/optimizer/scheduler/total_steps and universe/target/training/replay capture.

## Frozen whole-body custody

| Body | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/population/vectorized.py` | 3169 | `4cc490995fe34b17499030ec91de7bd1e4f19533a60fdb6338a92064a5c684e3` |
| `tests/test_townlet/regressions/bac/test_parent_intrinsic_handoff.py` | 832 | `8806af864533a94517e6f75ff87ef9b67a74d30cf2fc570736e0494e724b5e4d` |
| `tests/test_townlet/regressions/bac/test_population_standalone_step_cleanup.py` | 102 | `d59505029082a518f888bdc5937a6e23fbb56aac1681d2ce901e504ed6b37509` |
| `tests/test_townlet/regressions/bac/test_initial_participation_population.py` | 775 | `0db498e53d21f62f98ea53d6cf801476a1cac73b29a4710760a68d269dc78566` |

Total4878/four, growth47 lines from4831. The retained reviewer's attributed115-line fifth body gives4993/five. No further body capacity is claimed.

Before mutation, specifically authorized immutable snapshots were created and rehashed:

- `T18e-R0-POP-DIAGNOSTIC-CALLER-BEFORE-v1.py.txt`:3163, SHA256 `ea05fddb584cc7836e663e2aa2cada3c4dca1fcbc08584e030efa1816ac4bf38`.
- `T18e-R0-PARENT-DIAGNOSTIC-CALLER-BEFORE-v1.py.txt`:791, SHA256 `2621285b5d259be7f4bf8eb5e7b2ae1d2eb29c867923a7e2aa043c9e6246f7ef`.

Opaque producer handoff remains `../evidence-management/parent-c1/failed-diagnostic-implementation-v1/handoff.json`, SHA256 `a9993a98f523664765235eec9498f3b42aca67802bc864b62678b26325e90452`. No producer body was reopened.

## Scoped checks and retained failed attempts

All checker invocations used `UV_CACHE_DIR=/tmp/bac-pop-step-uv-cache uv run --no-sync` and only the two changed paths. Initial Ruff passed. Initial multi-file `black --check --diff` aborted in its multiprocessing SyncManager with sandbox `PermissionError: [Errno 1] Operation not permitted` on socket setup; it did not certify formatting. The shell also ran `wc` afterward and returned0, so no separate Black exit code was retained for that aborted attempt; this is explicitly not a pass.

Per-file Black avoided that environmental failure. POP exited0. Parent initially exited1 showing only new expected-field-set/tuple formatting. The new assertion was represented with an equivalent explicit literal-name string set to retain the hard whole-body budget, tuples were formatted one per line, and the observer list received an explicit type annotation. All original assertions were untouched.

Final scoped Ruff on both changed files exited0 (`All checks passed!`). Final per-file Black exited0 for POP and0 for parent (`1 file would be left unchanged.` each); POP did not change after its successful check. No application runtime/defaults/mypy/global-static result is claimed by this writer. Previous failed R124 evidence and pending wider gates remain preserved.

Root next executes `test_parent_intrinsic_handoff.py::test_partial_failure_records_reached_cut_and_refuses_reexecution[pace-advanced-1]`, then the complete23 POP and98 C1 final selection at one sealed candidate, with independent review. This caller repair preserves observation of actual failed state; it grants no healthy resume, active-parent integration, constructor/restore closure or broader programme acceptance.
