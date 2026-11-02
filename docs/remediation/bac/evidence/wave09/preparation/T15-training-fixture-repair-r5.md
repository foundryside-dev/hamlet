# T15 training fixture repair r5

2026-11-02 in existing `/workspace/hamlet`. Root explicitly confirmed failed full70539 actually CLOSED and custody verified before source-write clearance: root-attributed1FAIL6222PASS14SKIP15warnings1395.93wall, exit2. No runtime result was produced by this worker.

Only `tests/test_townlet/integration/test_training_loop.py` changed. The three flat learning cases now request `config_pack_factory`, author private copied YAML min16/batch16 through one in-file helper, and pass that copied pack to the existing CPU environment factory before compilation. The recurrent masked-loss case extends its existing copied-YAML modifier with min4/batch4. All four assert the compiled declaration has exactly those values. Canonical/shared config, compiled runtime fields and production replay admission remain untouched.

Actual positive `training_step_counter` is additionally required in the10-episode, Q-value and masked-loss cases. The target cadence case retains its positive-counter assertion and additionally requires at least10 successful optimizer updates, ensuring its original target-weight-change assertion runs. This means10 optimizer updates, not10 target copies. All original weight allclose atol1e-6, Q-change >0.01, epsilon, survival, replay, finite-metric and target assertions remain. The10episodes/50cap,100 target ticks,20*30 Q-value budget and30*30 recurrent budget remain unchanged. The other four selection/boundary/epsilon/storage cases are unchanged.

## Exact source custody

Same five complete implementation/test/helper sources:3649 lines before,3672 after. No sixth source or executable probe was opened. Training-loop source grew618 to641 lines; before SHA256 `890093ce4ff87a0a543b07cd3b4a1a456d02c53d8012286d3834a5a23e67d75b`.

| Source | Final lines | Final SHA256 |
| --- | ---: | --- |
| `src/townlet/population/vectorized.py` | 2146 | `9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a` |
| `tests/test_townlet/regressions/test_episode_lane_sinks.py` | 304 | `29b8fd697fd11e55c6d0a28de2ecba119f933d3cb8276d36f6502e35bbf0e79b` |
| `tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py` | 424 | `1bd025f4fd8c1a18f25235ed94718e68826a8c301386906d8a09ccd85710cc1f` |
| `tests/test_townlet/regressions/fixtures/episode_lanes.py` | 157 | `9de34aa9764fe2cef766aace4e6ebd391543621fa90def16b5614292e476ec7f` |
| `tests/test_townlet/integration/test_training_loop.py` | 641 | `207500289444d904f33d1961164fec493433a3f1514562ff541ce5fced11c722` |

All four prior source hashes, including the qualified sink fix, remain unchanged. Complete owned diff was inspected. Owned checks both exited0:

```text
.venv/bin/black --check tests/test_townlet/integration/test_training_loop.py
# 1 file would be left unchanged
.venv/bin/ruff check tests/test_townlet/integration/test_training_loop.py
# All checks passed!
```

## Root-owned four affected nodes

These spellings derive directly from the unchanged class/test names; no collection or runtime was run here:

```text
tests/test_townlet/integration/test_training_loop.py::TestMultiEpisodeTraining::test_train_10_episodes_with_learning_progression
tests/test_townlet/integration/test_training_loop.py::TestMaskedLossIntegration::test_masked_loss_during_training
tests/test_townlet/integration/test_training_loop.py::TestMultiEpisodeTraining::test_target_network_updates_at_frequency
tests/test_townlet/integration/test_training_loop.py::TestMultiEpisodeTraining::test_q_values_improve_over_time
```

Root will execute the four affected cases, then all8 module cases, with exact candidate/import custody before any replacement full run. Fresh independent review remains root-owned. Readiness and original numerical assertions may still expose actual failures; Black/Ruff success is not learning acceptance. No budgets, thresholds or assertions should be weakened to make those future runs pass.

Only the named training-loop source and this requested ignored report were written. No project imports/runtime, pytest/collection, new probes, branch/worktree/source copy/deletion, subdelegation, index/tracker/commit/publication or runtime-controller operation occurred. All14 existing worktrees and the finite66tasks/22lenses/54requirements remain preserved. Return stationary.
