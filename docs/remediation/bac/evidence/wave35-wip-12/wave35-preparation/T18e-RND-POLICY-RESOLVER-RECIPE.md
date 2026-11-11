# Current resolved RND configuration recipe

2026-11-11. Root verified source-only metadata for the complete 1456-line tests/test_townlet/regressions/bac/test_pw_scope_conversion.py, SHA256672a1441520b69cfda5045220a29d2abf891afa7fbad8d461c5e22c91adab893 before/after, then inspected its public policy builder at78–106 and its import declarations. Whole-body cost is1456, not the29-line excerpt. This is an executed-call-site/public configuration recipe, not an independent audit of the unopened resolver implementation. The consuming core agent should read this prose only, not that sixth body.

Actual public symbols/import origins:

- BaCOptions from townlet.config.bac_options
- IntrinsicStrategyConfig from townlet.config.drive_as_code
- TrainingV2Config from townlet.config.training_v2_config
- resolve_exploration_policy from townlet.config.exploration_policy

The genuine selected level is compiled.get_level('L0_test'). Build the drive by taking level.drive.intrinsic.model_dump(), replacing strategy with 'rnd', and validating with IntrinsicStrategyConfig.model_validate. Deep-copy level.training.model_dump(), apply the explicit data edits below, then validate it with TrainingV2Config.model_validate.

| Training data location | Explicit value/edit |
|---|---|
|replay_buffer.batch_size|2|
|intrinsic.rnd.feature_dim|4|
|intrinsic.rnd.learning_rate|0.001|
|intrinsic.initial_weight|0.4|
|intrinsic.survival_window|10|
|intrinsic.min_survival_fraction|0.01|
|intrinsic.annealing.min_weight|0.01|
|intrinsic.annealing.threshold|100.0|
|intrinsic.annealing.decay_rate|0.9|
|training_loop.max_steps_per_episode|20|

Build actual BaCOptions with model_validate over explicit authored options: curiosity_scope.scope='per_world' and curiosity_scope.seed_policy='world_id_derived_v1' for private; the corresponding shared pair is scope='shared', seed_policy='legacy_shared_v1'. The latter is the current supported shared policy name, not a compatibility fallback. provider_parameter_source='training'. rnd.service_mode='paced_fifo', rnd.max_updates_per_tick=1, rnd.max_pending_rows=4, rnd.overflow_policy='drop_oldest'. The source recipe also explicitly supplies providers.count_based={quantization_width:0.125,max_entries:4} and providers.icm={feature_dim:4,hidden_dim:8,learning_rate:0.001,inverse_weight:0.8,forward_weight:0.2,training_batch_size:2,max_pending_transitions:4}; those are authored option data, not extra model implementations.

The observed genuine public resolver call is positional resolve_exploration_policy(validated_drive, validated_training, validated_options). Use that call rather than guessing keyword spellings or constructing a fake namespace. The result is the real resolved policy consumed by the already-owned provider_factory.make_backend. Obtain D/A from actual selected.token_spec.total_dims and selected.action_metadata.total_actions, and pass that actual policy/dimension/binding consistently to WorldCuriosityDescriptor.from_policy and the factory according to their owned source. No copied Rig/controller is needed, and no import of the test policy helper is required.

These settings give the selected RND profile batch2, feature4, LR0.001, capacity4, one update per service tick and drop_oldest. They do not by themselves create training history: the witness must still admit actual rows and execute genuine service/Adam work. Current source code and production R0 admission remain unchanged; no runtime was run for this capsule.
