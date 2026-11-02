# T15 artifact fixture repair r4

2026-11-02, existing `/workspace/hamlet`. Root explicitly reported runtime91551 actually CLOSED before authorizing this repair: failed/interrupted result 1 setup ERROR, 3536 PASS, 11 SKIP, 13 warnings, 870.28 wall seconds. These are root-attributed results, not this worker's execution. No new full success is claimed.

Only `tests/test_townlet/regressions/test_episode_lane_sinks.py` was edited, solely its local `run_lane_runner` selector. Actual eligibility derives from `~env.dones & ~population.episode_completed`; on normal production learner entry those agree because POP refuses a live already-completed lane. Ascending eligible original-world indices project the complete compiled two-world action schedule. Q/state observation assertions now require K; selected actions require K; actual supplied masks must exist and have exact `(K,A)` shape. Legality indexes these masks with K-local row indices. Finite-Q checks, compiled action IDs and original END_LANE/WAIT timing remain. No masks, reward data, terminal bits, world transitions or inactive transport actions are invented.

The reviewed diff is 11 additions/4 removals, net seven lines. No artifact source modification was needed. Original ENV execution and independent full-N Q/curriculum/action transport, eligible ledgers, survival, completion snapshots, budgets/caps, queue, TensorBoard, file/index/SQL, playback, exports and all corruption assertions remain untouched. The common helper and all other audited source bytes remain unchanged. There is no assertion deletion, skip/xfail, relaxed budget/minimum or production change.

## Exact bounded source custody

Exactly the same four complete sources were read: 3024 lines before, 3031 after. No fifth source, conftest, project import, runtime, pytest/collection or executable probe was used.

| Source | Lines after | SHA256 after |
| --- | ---: | --- |
| `src/townlet/population/vectorized.py` | 2146 | `9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a` |
| `tests/test_townlet/regressions/test_episode_lane_sinks.py` | 304 | `29b8fd697fd11e55c6d0a28de2ecba119f933d3cb8276d36f6502e35bbf0e79b` |
| `tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py` | 424 | `1bd025f4fd8c1a18f25235ed94718e68826a8c301386906d8a09ccd85710cc1f` |
| `tests/test_townlet/regressions/fixtures/episode_lanes.py` | 157 | `9de34aa9764fe2cef766aace4e6ebd391543621fa90def16b5614292e476ec7f` |

Before sinks hash: `7e4aa29416b3fcfd01470ba143d3eec43172d66cff9aa4120ef6e28b245dcd8a`. All three other hashes equal the audit. Only owned Black/Ruff checks executed, both exit0:

```text
.venv/bin/black --check tests/test_townlet/regressions/test_episode_lane_sinks.py
# 1 file would be left unchanged
.venv/bin/ruff check tests/test_townlet/regressions/test_episode_lane_sinks.py
# All checks passed!
```

## Root-owned focused20 qualification

Run the previously failed artifact first through the existing exact-identity/import harness:

```text
tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py::test_ordinary_two_episode_files_index_sql_and_tb_match_actual_eligible_ledger
```

Then both entire modules, nine sink and eleven artifact cases, before any new full attempt. The following node spellings follow the unchanged source parameterizations; they have not been collection-verified by this worker:

```text
tests/test_townlet/regressions/test_episode_lane_sinks.py::test_ordinary_runner_db_tb_curriculum_and_snapshots_match_two_episode_ledger[end_ticks0]
tests/test_townlet/regressions/test_episode_lane_sinks.py::test_ordinary_runner_db_tb_curriculum_and_snapshots_match_two_episode_ledger[end_ticks1]
tests/test_townlet/regressions/test_episode_lane_sinks.py::test_real_dac_db_and_tb_publish_effective_components_and_zero_terminal_frame
tests/test_townlet/regressions/test_episode_lane_sinks.py::test_budget_six_retains_terminal_and_once_only_survivor_truncation
tests/test_townlet/regressions/test_episode_lane_sinks.py::test_caller_cap_keeps_authored_terminal_and_live_bootstrap[end_ticks0]
tests/test_townlet/regressions/test_episode_lane_sinks.py::test_caller_cap_keeps_authored_terminal_and_live_bootstrap[end_ticks1]
tests/test_townlet/regressions/test_episode_lane_sinks.py::test_indivisible_zero_work_budget_publishes_no_episode
tests/test_townlet/regressions/test_episode_lane_sinks.py::test_runner_publishes_owned_completion_meters_after_live_storage_changes
tests/test_townlet/regressions/test_episode_lane_sinks.py::test_caller_cap_completes_lanes_before_curriculum_publication
tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py::test_ordinary_two_episode_files_index_sql_and_tb_match_actual_eligible_ledger
tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py::test_actual_replay_manager_and_observer_seek_back_reset_and_episode_reload
tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py::test_both_real_exporters_use_same_run_and_actual_fourteen_transition_metadata
tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py::test_copied_real_artifact_corruption_is_refused_or_detected_against_ledger[schema]
tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py::test_copied_real_artifact_corruption_is_refused_or_detected_against_ledger[reason]
tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py::test_copied_real_artifact_corruption_is_refused_or_detected_against_ledger[missing_component]
tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py::test_copied_real_artifact_corruption_is_refused_or_detected_against_ledger[nan]
tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py::test_copied_real_artifact_corruption_is_refused_or_detected_against_ledger[sum]
tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py::test_copied_real_artifact_corruption_is_refused_or_detected_against_ledger[phantom]
tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py::test_copied_real_artifact_corruption_is_refused_or_detected_against_ledger[consistent_phantom]
tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py::test_copied_real_artifact_corruption_is_refused_or_detected_against_ledger[raw_intrinsic]
```

Only the named existing sink source and this ignored report were written. No branch/worktree/source copy/deletion, subdelegation, index/tracker/commit/publication or runtime-controller operation occurred. All fourteen worktrees and programme66 tasks/22 lenses/54 requirements remain preserved. Return stationary; root owns execution and integration.
