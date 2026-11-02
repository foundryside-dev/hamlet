# T15 existing fixture audit — bounded read-only source inspection

Prepared 2026-11-02 in existing `/workspace/hamlet` at HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`. Root attributes the frozen runtime candidate tree `f4ae7e65c2f2a1ffc944c19342490b8f48d6c9bf`. This worker did not create that tree, execute runtime, or inspect production implementation. Root explicitly allowed this ignored report while retaining the source/test/index/tracked write barrier until all current runtimes close.

## Exact complete source inventory

Five whole implementation/test/helper files, **3300 lines total**, below the hard five-file/5000-line ceiling. No sixth implementation, conftest, runner, POP, SB, RB, provider, imported fixture or compiler source was opened. Imports shown in these files were read as text only.

| Source | Lines | SHA256 |
|---|---:|---|
| `tests/test_townlet/unit/population/test_vectorized_population.py` | 1884 | `9e0b50095cd29470afc92d42a740a800e34c731aea12abfa96a7d60d89b1015c` |
| `tests/test_townlet/unit/population/test_recurrent_training.py` | 564 | `e288d03c24b98e6bd4aff86c617a933dfba0ac233821967d5db00dc301ff7e01` |
| `tests/test_townlet/unit/population/test_double_dqn_algorithm.py` | 324 | `b9b12150109541ed53f75fc692661c305f075b616827bac4c37a83afbe859e5a` |
| `tests/test_townlet/unit/population/test_action_selection.py` | 375 | `81ffc9ef6390f2a64471f3e9daf3ea77c751d1bc0e97ff6cbd5b03eede65b2b1` |
| `tests/test_townlet/regressions/fixtures/episode_lanes.py` | 153 | `b22601ae6cac1c78fe86f3e23b717c831905df9c39850daa24b406ae4e6f5c33` |

Read root AGENTS/CLAUDE and supplied prose `T15-constructor-unit-consumers.md`, `T15-interface-proposal-r1.md`, `T15-implementation-r0.md`, `T15-sequence-serialization-api.md`, `T15-flat-contracts.md`. Producer facts below are attributed to that prose and root's dispatch, not inferred from uninspected production source. Skills using-superpowers (dispatched-subagent stop) and cloud-environment-runtime were read. No network work was needed.

## Observed causal failures and exact bounded fixes

Read the six controller failure JSON DATA artifacts under `/workspace/bac-review-2026-11-01/qualification/wave09-b03-r0/B03-owners/`. These are actual root runtime evidence at the attributed tree, not this worker's execution. Three failures are in scope:

1. `integration/test_authored_episode_lanes.py::test_authored_pack_compiles` and `::test_authored_population_survival_reports_the_seven_actual_transitions` fail at helper line105. Actual provider Q/mask tensors have one eligible row after the first world ends; the helper asserts full N=2. The attributed provider contract now selects strict eligible K rows with aligned state, per-row epsilon and masks, then scatters full-N transport actions to env.step. The full-N helper assumption is obsolete, not evidence that production must restore inactive selector calls.

   After root clears writes, derive ascending eligible world indices from the real entry `~env.dones`, require Q shape `(K,A)` and state observation count K, retain finite-Q assertions, resolve the next authored **full-N** schedule through existing `action_ids`, retain its full-N shape assertion, select its K eligible actions by those indices, require mask shape `(K,A)` and retain every eligible-action legality assertion with K indices. Return only the selected K actions. Preserve authored world identity/order, exact schedule progression and no added random draw. Preserve full authored action schedule in witness actions, with actual provider Q outputs in witness q_values. `observe_environment_steps` remains unchanged and still observes actual original env.step with full-N transport/actions, sticky done and rewards. Preserve all seven actual transition and lifecycle expectations; no production edit or inactive selector restoration.

2. `unit/population/test_recurrent_training.py::TestEpisodeBuffering::test_store_episode_and_reset_adds_to_buffer` fails because its five manually fabricated rows omit the newly required collector lists. The runtime stacks empty `episode["next_action_masks"]`. Root/prose establish collectors now include the previous eight keys plus list bool[A] successor masks and list scalar bool recorded flags; complete fragments use `store_captured_episode`, once, with aligned stacks.

   After root clears writes, label this isolated random/manual collector data explicitly synthetic. For each of its five rows, construct a restrictive synthetic bool[A] successor mask with one permitted successor action and append it to `next_action_masks`; append scalar bool True to `legality_recorded`. Keep those additions aligned with all original row lists/device/dtype. These are declared synthetic unit inputs, not recovered historical ENV evidence or fabricated all-legal constrained history. Preserve every original assertion (successful store, empty reset collector, positive replay occupancy); strengthen aligned reset checks if useful. Do not change `_store_episode_and_reset`, fabricate production masks, weaken validation or archive unknown rows as active qualified data.

The other three failure DATA records are recurrent-bootstrap parameterizations reporting no optimizer updates. Their test implementations are outside this five-file context; this worker does not diagnose them or propose a production workaround. Root owns their separate bounded investigation.

## Explicit limitations and untouched roles

`TestRecurrentTraining::test_recurrent_training_path_via_step_population` seeds twenty maskless ten-row episodes through legacy `store_episode`, cites the obsolete sixteen-episode premise, and asserts only `is_recurrent` after one step. Under approved History A that maskless content is archival, not qualified learner rows. This smoke is **not acceptance evidence of actual learning**. Root explicitly limits this repair to the observed K/N and missing-collector-list failures; no new training programme or unobserved fixture rewrite is introduced. T15's independently owned actual-update/prefix controls supply learning proof. The scheduler save/load test likewise only proves restoration equality unless independently shown to advance. Neither weak smoke justifies lowering authored retained warmup, bypassing readiness or training on maskless history.

VP raw checkpoint/plain-push inspection, DD manual target calculations and flag tests, action-selection tests, empty collector, real rollout flush, hidden-state resets and adaptive completion retain their existing roles. No observed failure here calls for editing the three other audited unit modules. No skip, xfail, deletion, renamed public method, removed capability or reduced assertion is proposed.

## Custody

During this audit only this ignored prose report was written, after root explicitly allowed prose. No source/test, index, tracked metadata, branch, checkout, worktree, source copy, deletion, tracker, subagent, commit or publication action occurred. All fourteen existing worktrees remain preserved. No project import, pytest/collection, compiler, linter or runtime was executed. Entry tracked status showed only four pre-existing staged T15/schema paths. Source/test edits remain blocked pending root's explicit runtime-closed clearance. This report is a static causal fixture audit and proposed repair, not GREEN or release approval.
