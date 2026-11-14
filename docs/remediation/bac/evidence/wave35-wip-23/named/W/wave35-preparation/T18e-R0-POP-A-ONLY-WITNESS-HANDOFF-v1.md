# A-only standalone replay witness correction v1

2026-11-14. Narrow root APP baton after R124. Only `tests/test_townlet/regressions/bac/test_initial_participation_population.py` changed: line301's genuine standalone replay sample witness now passes explicit `lineage=None`, with Black-compatible line wrapping. All assertions are unchanged. No POP/runtime/BANK/other test changes, application imports/tests, Git operations, branches or worktrees. This prose records the handoff; root owns exact targeted runtime capture.

Root reported R124's actual selection as21PASS/2FAIL of23, plus the overlapping original control1PASS. Eight focused cleanup and ten handoff cases passed. The A-only case had already reached two genuine steps and one optimizer update before its own omitted-lineage witness failed. The other failed pace diagnostic exposes the separately required failed-step exporter capability. The root preservation ruling in `T18e-FAILED-STEP-DIAGNOSTIC-PRESERVATION.md` remains controlling; this correction does not weaken that assertion, repair the producer diagnostic gap or qualify the full selection. Root also reported scoped Ruff/Black/defaults600PASS and mypy12FAIL; none is relabeled by this handoff.

Before editing, verified the initial-participation body773 SHA256 `9186a953f79cd8b4cf2a4fea47c6ff24197ae53764b6d2e6fa33267f78000bd5` and preserved identical bytes in the specifically authorized inert snapshot `T18e-R0-POP-A-ONLY-WITNESS-BEFORE-v1.py.txt`. Ordinary `diff -u` against that snapshot shows exactly the explicit keyword addition and its wrapping.

Frozen after-source:

| Body | Lines | SHA256 |
| --- | ---: | --- |
| POP vectorized.py | 3163 | `ea05fddb584cc7836e663e2aa2cada3c4dca1fcbc08584e030efa1816ac4bf38` |
| test_parent_intrinsic_handoff.py | 791 | `2621285b5d259be7f4bf8eb5e7b2ae1d2eb29c867923a7e2aa043c9e6246f7ef` |
| test_population_standalone_step_cleanup.py | 102 | `d59505029082a518f888bdc5937a6e23fbb56aac1681d2ce901e504ed6b37509` |
| test_initial_participation_population.py | 775 | `0db498e53d21f62f98ea53d6cf801476a1cac73b29a4710760a68d269dc78566` |

Whole-file budget4831/four, under5000; the other three bodies retain their previous seals. No extra helper/producer body was opened.

Executed only scoped static commands on the changed initial-participation path, each with `UV_CACHE_DIR=/tmp/bac-pop-step-uv-cache uv run --no-sync`: `ruff check` exit0 (`All checks passed!`), `black --check` exit0 (`1 file would be left unchanged.`). No application runtime was executed by this writer.

Root's next exact node is `tests/test_townlet/regressions/bac/test_initial_participation_population.py::test_actual_a_learning_replay_private_b_and_next_cycle`. Broad23 repetition remains deferred until the separate diagnostic prerequisite is repaired and reviewed. No acceptance or missing-interface waiver follows from this one-witness change.
