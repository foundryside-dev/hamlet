# T15 artifact fixture independent review r4

2026-11-02. Independent static source/specification and quality review in existing `/workspace/hamlet`. Frozen HEAD independently read as `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`; supplied r4 manifest names candidate tree `f4032499a9800e8a8398b812a8dcc7ebfe9c4974`. No full qualification claim is made.

## Scope and identity

Read AGENTS.md and CLAUDE.md, the supplied artifact causal audit and r4 repair report, candidate manifest, bounded artifact diff, and exactly these four whole implementation/test/helper sources (3031 lines). SHA256 and line counts were independently measured from the working files and match the manifest and repair report.

| Source | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/population/vectorized.py` | 2146 | `9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a` |
| `tests/test_townlet/regressions/test_episode_lane_sinks.py` | 304 | `29b8fd697fd11e55c6d0a28de2ecba119f933d3cb8276d36f6502e35bbf0e79b` |
| `tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py` | 424 | `1bd025f4fd8c1a18f25235ed94718e68826a8c301386906d8a09ccd85710cc1f` |
| `tests/test_townlet/regressions/fixtures/episode_lanes.py` | 157 | `9de34aa9764fe2cef766aace4e6ebd391543621fa90def16b5614292e476ec7f` |

No fifth runner/recorder/database/TensorBoard/conftest/probe source was opened. The manifest's other filenames and digests were treated as identity data, not implementation review. No runtime, project import, collection, test, compiler, checkout, branch/worktree/source copy/deletion, index, commit, tracker mutation or subdelegation occurred. Only this ignored report is written.

## Findings and severity

No actionable correctness or quality finding in the r4 repair. Static review accepts the narrow causal change, subject to the executable evidence below. This acceptance does not newly qualify the larger T15 implementation or claim independent review of excluded sink implementations.

The sink-selector hunk contains 11 additions and four removals, confined to `run_lane_runner.reset.select` (lines 67–83). Its predecessor demanded two provider rows and returned two actions after one world had finished. Production `_select_eligible` instead supplies K rows. The repaired selector computes actual ascending original-world indices from `~env.dones & ~population.episode_completed`, checks finite `(K,A)` Q values and K observation rows, resolves the complete two-world authored schedule through compiled action IDs, then selects its K original-world entries. The actual supplied mask must exist and have `(K,A)` geometry; legality uses K-local `arange(K)` paired with the projected actions.

For `(2,5)`, tick 3 maps original world 1 to local row 0 and selects its WAIT; tick 5 selects its END_LANE. For `(5,2)`, tick 3 retains original world 0 at local row 0 and selects its WAIT; tick 5 selects its END_LANE. The completed world's schedule entry is never mistaken for the survivor's. The existing two parameterized world orders exercise these distinct mappings. On production learner entry, the intersection agrees with `active_on_entry`: `step_population` refuses any live already-completed lane before provider invocation. The selector runs before ENV transition and completion mutation, so it observes the same entry state.

## Refuted concerns and retained evidence

- **Production masking or narrowed network/curriculum execution:** `_rollout_q` still forwards the real full-N current observations and retains the full output in `last_selected_q_values`. `step_population` supplies full-N state/Q to curriculum, obtains full-N ENV masks, and only `_select_eligible` projects the provider view. It assigns returned K actions back into an N action tensor. Full-N ENV execution and published Q information remain intact. The fixture introduces no fabricated mask or additional brain forward.
- **Authored schedule substituted for observed transport:** the ENV wrapper calls `original_step` and records the actual N actions, pre-step active bits, terminal/done bits, observations, meters, rewards, reward components and weights. The repaired schedule controls eligible selection only. Inactive transport continues to be production-owned; the common helper's schedule witness is not evidence of inactive applied actions.
- **Assertion weakening:** the obsolete full-N provider assumption is replaced with K geometry, explicit mask presence/shape and local legality assertions. Finite-Q checking remains. State observation row count is checked; this helper does not independently establish numeric equality of every projected state/Q/epsilon row, which remains a separate provider/learner qualification concern. No assertion removal from artifact consumers, skip, xfail, threshold relaxation, budget/minimum change or generated fake artifact is introduced.
- **Lifecycle and sink evidence lost:** the unchanged sink cases retain both survivor orders, two episodes/reset, exact 5 vector ticks and 7 live transitions per episode, survival/custom-action metrics, final owned completion observations/meters, curriculum publication, effective DAC components and zero terminal reward frame. Budget six, cap three, exactly-once flush, zero-work indivisible budget, completion-storage aliasing and completion-before-curriculum controls remain.
- **Artifact corruption hidden:** the unchanged module uses ordinary runner cleanup, real queue acceptance/dequeue identity and order, empty queue and writer buffer, terminated writer thread, four frames/two markers/two files/two SQL recording rows and fourteen realized eligible transitions. Queued metadata/frames must equal persisted payloads; sizes/index/SQL/TensorBoard and per-world reward ledgers remain checked. Real replay/observer seek, reset and reload and both export paths remain covered. All eight corruption variants remain, including independent semantic rejection of structurally consistent phantom transitions and raw-intrinsic substitution; original-file digest preservation remains asserted.

The source hashes show production POP, common fixture and artifact module unchanged from the supplied prior audit. The parent reports broader main/consumer qualified scopes byte-identical; this bounded reviewer does not re-open those scopes or treat their qualification as newly established here. No new task, lens, scope waiver or reduction of the finite programme is proposed.

## Runtime still owed

Root reports the prior full gate ended with one setup ERROR, 3536 PASS and 11 SKIP at the obsolete selector, followed by graceful closure of its own controller and successful custody checks. Those are attributed prior results, not this reviewer's execution and not r4 success.

The exact previously failed node must first execute through the existing candidate-identity/import harness:

`tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py::test_ordinary_two_episode_files_index_sql_and_tb_match_actual_eligible_ledger`

Then execute both complete sink and artifact modules (nine plus eleven cases), preserving artifact evidence through `EPISODE_LANE_ARTIFACT_EVIDENCE_DIR`, before the replacement full gate. These runs must establish actual cleanup, queue/persistence/SQL/TensorBoard/playback/export/corruption outcomes on the frozen repaired candidate. Black/Ruff success is attributed to the repair report; this review did not rerun executable tools. Broader B03/G2/BAC/final qualification remains root-owned. Any new failure requires causal triage rather than modifying evidence assertions by assumption.

Reviewer remains stationary pending root collection and explicit runtime clearance. The exact failed artifact node above is my selected independent existing-harness execution case if root assigns free CPU and the approved harness invocation; no additional probe/helper is requested.
