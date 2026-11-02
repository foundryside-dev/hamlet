# T15 lane supplier repair r1

Stationary authoring handoff; runtime qualification remains owed to root. No project imports, pytest, or product runtime executed by this owner.

## Scope and census

Read exactly five repository instruction/implementation/test/helper files (3375 source lines before edit, 3382 after edit; below 5 files/5000 lines). No sixth dependency, conftest, learning test source, or probe was opened. Failure JSON is supplied qualification data, not an additional implementation source.

| File | Before lines | SHA-256 read |
| --- | ---: | --- |
| AGENTS.md | 79 | 184c48c8f99d106870802bd72d4e7fe79baad11ac72234fa47e9bb493c3b9238 |
| CLAUDE.md | 605 | a65cd6db26d75dce767d1b23f83be01206f09905d2e40073d6767d67740db4a3 |
| src/townlet/population/vectorized.py | 2128 | e1accf8f6b0d9b884d37931facadcb030505552bdbe2d29d1733ee19fb021b02 |
| tests/test_townlet/regressions/test_episode_lane_population.py | 406 | 74b7245dd73b64c9aad409050c98aaa72887420e9020dfe325512efc13ddb3c1 |
| tests/test_townlet/regressions/fixtures/episode_lanes.py | 157 | 9de34aa9764fe2cef766aace4e6ebd391543621fa90def16b5614292e476ec7f |

Modified only tests/test_townlet/regressions/test_episode_lane_population.py, plus this requested ignored report. Final owned source: 413 lines, SHA-256 5c306090ecdf7ec50c699ffb48913376a40fd12e58feb682bfc1ceb514ecd4f8. Diff: 10 additions/3 removals. AST census before/after: five test functions, 61 Assert nodes; parameterization unchanged (29 cases: 3 replay totals, 12 eligible ledger, 12 explicit cut, 1 distinct reason, 1 recurrent).

No branches, worktrees, copies of the source checkout, deletions, staging, commits, subdelegation, production minimum changes, shipped config changes, or original artifact edits. Existing 14 worktrees preserved. The factory continues copying the authored pack into each test destination as before.

## Causal evidence and changes

R0 qualification context supplied by root: HEAD 75bc, tree f4ae7e65c2f2a1ffc944c19342490b8f48d6c9bf, B03 42 failures/125 passes. All 11 unique failures in the owned source stop at the common helper's obsolete full-N q_values assertion, episode_lanes.py:105. The failure directory contains 22 matching records, with controller/worker copies of each unique nodeid. The common helper correction is a separate owner's work and was read at its now stationary 157-line version; this owner did not edit it.

1. Added keyword-only replay_min_size: int | None = None to make_lane_population. A non-None value edits training.replay_buffer.min_size in the copied pack's levels/LEVEL_NAME/training.yaml before compilation. LEVEL_NAME is imported from the already-authorized helper. None performs no extra YAML read/write and preserves authored behavior. No existing caller in the owned source changes its minimum. Root owns intended explicit minimum selection for the actual-learning tests, including the 63-row run.
2. Corrected the recurrent test's selection comparison to reference_q[active, 0], since selection receives K eligible provider rows. The curriculum still receives full-N real forward Q values and remains compared exactly against reference_q[:, 0]. Entropy calculation and dead-row nonzero evidence now use that full-N curriculum observer instead of the K-row selection observer. No assertion was removed or weakened into a permissive capability check.

## Retained controls

Real authored WAIT/END_LANE actions and normal environment stepping; compiled action IDs and masks through the shared helper; independent eligible predecessor/action/reward/next-observation/done ledgers and all DAC reward components; two-episode reset and cumulative survival/terminal counts; standard/PER/sequential replay totals and sequence coordinates/content; exact completion reasons, survival and exploration history; completed-population refusal; reset-before-mutation snapshot equality; explicit cap/budget/shutdown/checkpoint flush closure and idempotence; owned final observation/meter snapshots; nonterminal cut replay dones; authored death versus healthy retirement; recurrent full-N real forward/curriculum Q equality, entropy, curriculum decisions/stages, active hidden carry, dead hidden zeroing, surviving selected action, hidden evolution and real dead-row forward evidence.

Constructor/inspection replay behavior remains untouched; no maskless row is declared trainable. The owned source had no stale replay-instance patch to migrate. The helper retains its full authored action witness while returning only K selected rows; inactive transport action values are production-owned.

## Static verification and runtime owed

Passed (exit 0):

- .venv/bin/black --check tests/test_townlet/regressions/test_episode_lane_population.py
- .venv/bin/ruff check tests/test_townlet/regressions/test_episode_lane_population.py
- git diff --check -- tests/test_townlet/regressions/test_episode_lane_population.py
- Standard-library AST parse/census of before/after source (61 asserts, five tests each).

No runtime success is claimed. Once all writers are stationary, root owes exact collection and causal qualification of the 29 owned cases with the stationary common helper, independent review, and the separately owned learning cases exercising an explicitly authored replay minimum. Root should verify both omitted/None authored-min preservation and the explicit copied-YAML minimum through compilation as part of integration qualification. Real product failures must remain visible.
