# T15 training fixture independent review r5

2026-11-02. Continued independent review in existing `/workspace/hamlet`, adding only the authorized training-loop integration source to the previous four-source scope. Frozen manifest: HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`, candidate tree `f71c52fad680a74da1b90cc7470455fc90f4fa3f`. Static review only; no r5 runtime qualification is claimed.

## Exact source inventory

Five complete implementation/test/helper sources, 3672 lines. SHA256/counts independently measured and match the supplied r5 manifest/repair record. The four previously reviewed sources remain byte-identical. Read the new audit and repair prose, bounded diff and source-verified constructor supplier prose; canonical model-config training YAML was read as DATA. No sixth config-builder/environment fixture/conftest/other source was opened.

| Source | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/population/vectorized.py` | 2146 | `9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a` |
| `tests/test_townlet/regressions/test_episode_lane_sinks.py` | 304 | `29b8fd697fd11e55c6d0a28de2ecba119f933d3cb8276d36f6502e35bbf0e79b` |
| `tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py` | 424 | `1bd025f4fd8c1a18f25235ed94718e68826a8c301386906d8a09ccd85710cc1f` |
| `tests/test_townlet/regressions/fixtures/episode_lanes.py` | 157 | `9de34aa9764fe2cef766aace4e6ebd391543621fa90def16b5614292e476ec7f` |
| `tests/test_townlet/integration/test_training_loop.py` | 641 | `207500289444d904f33d1961164fec493433a3f1514562ff541ce5fced11c722` |

## Findings and severity

No actionable correctness or quality finding in the r5 fixture repair. Accept statically, pending real execution of the four affected cases and all eight module cases. This is existing T15 consumer preservation, not a new task/lens or scope waiver.

Canonical model-config YAML still declares replay minimum1000/batch32. The failed ten-episode fixture could produce at most500 one-agent transitions (10 episodes times50), below minimum1000 regardless of network/replay capacity. The previously inspected POP path reads the compiled training minimum, asks readiness before sampling and increments `training_step_counter` only after real backward/optimizer execution. Consequently unchanged weights at the old budget are consistent with honored admission, not evidence that this repair must lower production warmup.

The new `_learning_config_pack` helper modifies the copied training YAML before `cpu_env_factory(config_dir=...)` compiles it. Its factory/name/batch inputs are explicit; each flat case uses its own named pack and declares min16/batch16. The recurrent case extends its existing copied-pack modifier with min4/batch4 before compilation. All four assert those exact values on `env.level.training.replay_buffer`. The source-verified supplier prose establishes that the CPU factory follows the real compiler/ENV route and `config_pack_factory` supplies a prepared copy path; this review does not reopen excluded supplier implementations. There is no write to canonical YAML, compiled carrier mutation, production-source change, replacement sampler, synthetic transition or fabricated optimizer counter in the repair.

## Preservation and refuted concerns

- The ten-episode case retains ten episodes, cap50, frequency4, batch16, original brain, genuine replay/storage/step checks and weight-change predicate with `atol=1e-6`. Positive optimizer progress is added, not substituted for weight movement. Survival episode count remains ten.
- The target case retains100 actual vector ticks with resets, frequency4 and target cadence10. Requiring at least10 real optimizer updates makes its pre-existing conditional target-change assertion unavoidable. The original weight tolerance remains. This demonstrates reaching a target-copy opportunity and changed target weights; it does not newly establish an exact per-update cadence trace, which was not added or claimed by this repair.
- The Q-value case retains20 episodes at cap30, epsilon decay, original network evaluations and mean/std change threshold `>0.01`. Positive optimizer progress prevents initialized non-None metrics or different reset observations alone from satisfying the test. The preserved statistic remains a change check, not proof of improved policy performance or same-observation causal attribution.
- The recurrent case retains30 episodes at cap30, sequence8, batch4, frequency4, original brain, lifespan1000 and existing curriculum modifier. Genuine episode/cap completion supplies captured replay through unchanged POP. Positive optimizer progress means zero initialized loss/TD metrics can no longer stand in for actual learning. Minimum4 does not bypass sampleable-unit readiness; missing selected sampler support or insufficient real captured sequences must still fail execution. Finite metric and completed-episode predicates remain. This consumer test does not alone prove every masked-gradient property described in its historical docstring.
- The four action-selection/boundary/epsilon/replay-storage cases are untouched and continue using their original factory calls. No learner minimum is globally lowered. All original budgets, numerical predicates and survival/epsilon/target/loss assertions remain; there are no skips, xfails or deletions to hide a runtime failure.

The retained independent artifact1 PASS was executed by this reviewer at r4, with actual exit0 and original source/import/thread identity. Root additionally reports artifact20 PASS. Their four source hashes remain unchanged here; no fresh r5 artifact execution is claimed.

## Runtime owed and custody

Root reports fullreplacementR1 actually failed with1FAIL6222PASS14SKIP and was gracefully stopped under its own controller custody before this source repair. That failed full result must remain preserved; neither this static acceptance nor earlier artifact success converts it to full qualification. Black/Ruff success is attributed to the repair report and was not rerun by this reviewer.

Execute the exact four affected nodes through the existing frozen candidate/import harness, then all eight module tests before another full attempt. The exact previously failed case is `tests/test_townlet/integration/test_training_loop.py::TestMultiEpisodeTraining::test_train_10_episodes_with_learning_progression`. The other affected nodes are `TestMaskedLossIntegration::test_masked_loss_during_training`, `TestMultiEpisodeTraining::test_target_network_updates_at_frequency` and `TestMultiEpisodeTraining::test_q_values_improve_over_time` in that same module. Assert actual job results and learning progress; do not relax budgets, readiness or numerical checks if execution reveals another failure.

No runtime/project import/collection/compiler/linter/probe, source edit, helper creation, index/tracker/commit mutation, checkout/worktree/source copy/deletion, cancellation or subdelegation occurred. Only this requested ignored report was written. Existing worktrees and finite programme remain untouched. Reviewer stationary pending root collection and any explicit independent-runtime clearance.
