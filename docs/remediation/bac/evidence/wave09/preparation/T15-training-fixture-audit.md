# T15 training fixture causal audit

2026-11-02, existing `/workspace/hamlet`; root-reported HEAD75bc8e43/current source treef4032499. Root's failed full70539 remains under root custody pending actual closure. This worker made no source edits or runtime calls. Only this requested ignored audit is written.

## Exact five-source inventory

The prior four sources plus the one authorized integration source total3649 lines. No sixth implementation/config-helper/conftest source was opened. Source-verified constructor supplier and checkpoint fixture audit prose were consumed without following implementation links. Canonical model-config training YAML was read as authored DATA.

| Source | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/population/vectorized.py` | 2146 | `9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a` |
| `tests/test_townlet/regressions/test_episode_lane_sinks.py` | 304 | `29b8fd697fd11e55c6d0a28de2ecba119f933d3cb8276d36f6502e35bbf0e79b` |
| `tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py` | 424 | `1bd025f4fd8c1a18f25235ed94718e68826a8c301386906d8a09ccd85710cc1f` |
| `tests/test_townlet/regressions/fixtures/episode_lanes.py` | 157 | `9de34aa9764fe2cef766aace4e6ebd391543621fa90def16b5614292e476ec7f` |
| `tests/test_townlet/integration/test_training_loop.py` | 618 | `890093ce4ff87a0a543b07cd3b4a1a456d02c53d8012286d3834a5a23e67d75b` |

## Actual cause and inputs

The failing `TestMultiEpisodeTraining::test_train_10_episodes_with_learning_progression` calls `cpu_env_factory(num_agents=1)` without a configuration override. Verified supplier prose establishes the real compiler/ENV route selecting canonical `configs/test/model_config/levels/L0_test/training.yaml`. Its authored DATA declares min_size1000, batch32, training capacity100000, seed42 and episode lifespan1000. The separately passed `minimal_brain_config` supplies actual population feedforward replay capacity10000, Adam0.001 and nonprioritized replay. Population batch16 and frequency4 are explicit in the test. Capacity, warmup and batch have distinct roles; the brain does not override the selected training minimum.

POP `_compiled_replay_setup` reads actual `env.level.training.replay_buffer.min_size`. `_learn` asks readiness before sampling/optimizer execution. The test collects at most10*50=500 one-agent transitions, with early terminal breaks reducing that bound. It cannot reach min1000. Unchanged initial/final weights are therefore expected under the accepted production contract. Root's observed failure is consistent with those inspected inputs and admission path. Lowering production warmup, mutating a compiled carrier after construction, reinterpreting batch16 as an implicit minimum, increasing episodes/caps or weakening allclose tolerance would conceal the fixture mismatch.

## Other learning consumers in the same file

| Case | Existing real transition budget | Causal consequence |
| --- | --- | --- |
| `test_train_10_episodes_with_learning_progression` | at most500 | Weight-change assertion cannot execute real learning at min1000. |
| `test_target_network_updates_at_frequency` | exactly100 ticks across resets | Existing optimizer>0 assertion must fail at min1000. Its target-change branch requires10 optimizer steps, so merely retaining a conditional can miss cadence evidence. |
| `test_q_values_improve_over_time` | at most20*30=600 | Claimed trained Q-value difference may reflect different reset observations; zero optimizer progress remains possible, and initialized non-None metrics do not prove learning. Preserve its numerical >0.01 predicate and add genuine optimizer progress. |
| `test_masked_loss_during_training` | at most30*30=900 | Existing copied pack modifier only sets lifespan1000, leaving inherited warmup. Recurrent passed-brain capacity5000 is adequate but cannot cure warmup. `total_steps>0` and finite initialized loss0/TD0 cannot prove its stated actual-training purpose. |

The remaining action-mask, boundary, epsilon-decay and replay-accumulation cases assert selection/environment/exploration/storage behavior, not parameter/optimizer progression. Their canonical authored warmup remains appropriate and needs no repair. No unrelated random-action assertions or storage-capacity descriptive cleanup is proposed.

## Minimal proposed owned repair after root clearance

Only edit `tests/test_townlet/integration/test_training_loop.py`:

1. For the three flat learning cases above, request the existing `config_pack_factory` fixture and create a private copied pack with an explicit YAML modifier setting `training.replay_buffer.min_size=16` and `batch_size=16`. Pass that copied `config_dir` to the existing `cpu_env_factory` before compilation. A small in-file helper taking explicit factory/name/batch inputs may share the identical modifier. Each case receives its own copied pack. Preserve passed minimal brain and all population controls.
2. Extend the existing recurrent masked-loss copied-pack modifier to author `min_size=4,batch_size=4`, matching its existing population batch4. Preserve recurrent brain, sequence8, frequency4,30 episodes,30-step loop, lifespan1000 and curriculum changes. Captured real episodes and actual readiness must still supply sampleable units; no fabricated replay/masks or lower production threshold is allowed. If that retained budget cannot yield the selected recurrent sampleability, root must expose the actual failure rather than assume progress.
3. Explicitly assert compiled training minimum/batch values agree with each case's intended authored controls. Keep all existing survival, epsilon, replay, finite-metric and numerical weight/Q predicates. Require positive actual `training_step_counter` in the10-episode, Q-value and masked-loss cases. In target-update test require at least10 real optimizer steps so its existing target-change assertion necessarily executes. Do not change10 episodes/50 cap,100 target ticks,20*30 Q budget or30*30 recurrent budget.

This is fixture authoring through an existing verified copying factory, not editing canonical/shared YAML or compiled runtime fields. No canonical config, fixture helper, POP, provider, source hash outside the owned training-loop file or previously repaired sink selector should change.

## Root-owned qualification

After actual full closure and write clearance, root should execute the exact failed10-episode node first, then all eight tests in this integration module using its existing identity/import harness. Explicitly observe the four actual-learning cases' optimizer assertions and preserve original tolerances/budgets. Existing epsilon-only and storage-only tests retain canonical min1000, establishing that the explicit copied lower minimum is scoped. Owned Black/Ruff and complete diff review precede root runtime; no green claim follows from static coherence. Broader gates and new full attempt remain root-owned.

No project imports, pytest/collection, executable probe, compiler, linter, branch/worktree/source copy/deletion, subdelegation, index/tracker/commit/publication or runtime-controller operation occurred in this audit. Existing14 worktrees and finite66tasks/22lenses/54requirements remain preserved. Stationary awaiting explicit root clearance.
