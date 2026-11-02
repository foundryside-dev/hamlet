# T15 checkpoint consumer fixture audit

Static read-only source investigation at HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`, root-reported frozen candidate tree `929bc8952a2e797871d15376e2ef61a8aec73ca5`. Root explicitly permits this ignored audit while its runtimes remain active; no tracked source edits or runtime/import/pytest/collection occurred. Read AGENTS.md and CLAUDE.md; root's finite task restrictions govern. No branches, worktrees, copies, deletion, index, commits or delegation.

## Exact complete source inventory

Exactly five complete implementation/test files, 4525 lines:

| File | Lines | SHA256 |
|---|---:|---|
| src/townlet/population/vectorized.py | 2146 | 9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a |
| tests/test_townlet/integration/test_checkpointing.py | 1665 | c7044acb8e7f247511c80e8ab792a14040fff7eb646ee99f27bc96ab262cdf34 |
| tests/test_townlet/_fixtures/environment.py | 460 | 21bd79b1736efd53fdacb76ca6a6f4abaf3917340204aef74994ba20b6af745c |
| tests/test_townlet/_fixtures/config.py | 145 | f25801c31ddb8354cc8b63a25fa145b518a65c05b275d19f558cf6f4e3f04fb8 |
| tests/test_townlet/_fixtures/brain_configs.py | 109 | aac8397902f8f038bee0c3da913c1a6b3930478d70c8a82156898231605cc9f4 |

No helper, conftest, environment implementation, replay-buffer implementation or runner implementation was opened. Consumed source-verified prose T15-constructor-fixture-suppliers.md, T15-constructor-factory-bridge.md and T15-sequence-serialization-api.md from this directory. Additional non-source data read: canonical model-config training YAML and two root failure-controller JSON artifacts.

## Confirmed fixture inputs and failure

Config fixture64–74 returns repository `configs/test/model_config`; compile fixture109–145 compiles its sole level without on-disk cache. Environment fixture131–177 passes that compiled universe through the actual VectorizedHamletEnv classmethod, selecting the only available level and forcing CPU only in the CPU wrapper. No training override is supplied by the failing test. The separate constructor bridge/supplier prose confirms this retains the real selected `env.level.training`.

Authored DATA `configs/test/model_config/levels/L0_test/training.yaml`, SHA256 `be51560e5c6f8f98444bdeef83eb66b6834bbdf6bd9789eeb33b016cd92a7485`, declares replay min_size1000, batch32, training replay capacity100000, seed42 and episode limit1000. Passed minimal_brain_config is separately authored at brain_configs17–59: feedforward, Adam learning_rate0.001, replay capacity10000 and prioritized false. Runtime capacity comes from that passed brain (POP397), not training capacity100000. Test TRAIN_KWARGS39 uses batch32, frequency1, sequence1, max_grad_norm1.0. These distinct roles must remain unchanged.

Root failure data `failure-controller-7b2caf923c210d83.json` identifies TestCheckpointRoundTrip::test_checkpoint_roundtrip_training_resumption, failure1135 weights_changed False, candidate tree above, and passed-brain capacity10000. Test1084 collects only100 real one-agent ticks and continues50 at1090. POP527 uses the actual selected training min_size1000; POP715–725 checks actual replay readiness before sampling; optimizer.step763 and training_step_counter764 occur only after readiness. The helper43–48 correctly resets completed batches, admitting real transitions only. Thus this fixture never reaches declared retained warmup; weight equality alone would not establish that cause without the inspected admission/input path.

Independent ownership confounder: POP1449/1450/1462 return network/optimizer/target state_dict views. Test1087 captures these without ownership then continues source training. Once warmup is fixed, this could silently turn the purported checkpoint tensors into later source state while its integer counter remains the earlier value. A fixture-owned deepcopy or actual serialization is necessary. Do not change public checkpoint producer semantics for this consumer repair.

## Proposed narrow training-resumption repair (awaiting source write clearance)

Collect `max(env.level.training.replay_buffer.min_size, pop1.batch_size)` actual transitions with existing one-agent helper, bounded by asserted passed-brain/public buffer capacity. Assert retained occupancy meets declared warmup and positive training_step_counter. Deepcopy get_checkpoint_state before continuing source. Continue the existing50 ticks and prove source optimizer counter and parameter changes against the owned checkpoint. Load that owned state, verify restored counters and checkpoint weights, reset under existing fresh-episode policy, continue50 ticks, and require resumed optimizer counter advancement plus existing allclose-atol1e-6 weight-change and architecture assertions. Rename fixed100/150 labels to checkpoint/continued state. No warmup lowering, batch-as-min substitution, xfail, dropped assertion or weaker tolerance.

## Second current producer fixture failure

Root `failure-controller-22994d666182b190.json` reports recurrent current-checkpoint test163: actual action_dim8, expected None. POP595–645 binds training before rollout; a pristine recurrent constructor is replaced with configured captured replay. POP954 stores captured episodes on checkpoint finalization. The test's just-produced checkpoint expectations163–185 incorrectly demand old maskless format5; restored expectations213–285 incorrectly demand archive-only reset.

Root-confirmed public contract (prose only): uniform captured sequential serialization is exact format6, carries geometry/action_dim, legality_mode captured, resolved six-leaf replay_options, episode/transition identity counters and historical_archives. Captured episodes include next_action_masks bool[rows,A], legality_recorded bool[rows], transition_ids int64, episode_id/original_length/start_offset, in addition to original row fields. Current6 source/restored learner state should be equal and active retained rows remain2, len(buffer)2 episodes, despite fresh rollout reset. Compare actual source geometry/options and descriptors rather than guessing defaults. New captured state must not become historical merely because rollout restarts.

Future repair remains confined to this test file: replace stale new-producer5/inspection assertions with exact captured6 geometry/options/legal masks/identity and source-restored equality; prove sampleable captured continuation using an actual request with persisted resolved options. Retain checkpoint completion once, survival-history idempotence, pending rollout exclusions, fresh completion/episode/env counts, false nonterminal dones, hidden reset, source bytes immutability and producer state immutability. Genuine historical maskless5 archival guarantee remains protected in separate root-owned fixtures/tests; do not alter it. Buffer implementation was not read.

## Custody and disposition

Ignored destination verified with git check-ignore. Source writes remain blocked until root reports all runtimes closed and grants clearance. This audit is investigation/proposal, not runtime acceptance. Root owns exact identity, execution and broader gates. Return stationary after receipt delivery.
