# Additive BaC options (schema version bac-options-v1)

This package declares portable, immutable, finite-only options. Declaration loading and
resolution do not by themselves establish runtime qualification. T15 consumes resolved replay
policies through explicit or compiled-adapter population learning; [STATUS.md](STATUS.md)
records qualification and remaining T16 runner propagation. Consumer ownership remains effective
configuration/roles T03, encoders T17, replay T08–T16, exploration T18a–d, curriculum T20–T22,
checkpoints T24–T26 and evaluation T27.
Current compile/cache transport retains the authored training block and encoder
block. `resolve_bac_options(training.bac_options, training=training)` returns
`ResolvedBaCOptions(schema_version, options, provenance)`; serialize this receipt
with `model_dump(mode="json")`. Persisting that resolved receipt in the effective
run/checkpoint is later work. Parsing a mode is not operational qualification.

Author `training.bac_options` inside the existing wrapped training declaration.
Every old required field remains required. Missing additive fields (or null)
mean unspecified, never a local constructor default. The central resolver fills
only unspecified fields; an explicit override changes only its named field and
any documented dependent derivation. Unknown keys, geometry overrides, invalid
literals, nonfinite numbers, boolean strings, and invalid ranges refuse.
Existing architecture/optimizer/schedule presets remain validated and retained.
The five training overrides and complete level-brain replacement are unchanged.
Existing hash APIs are not redefined here; old identity adaptation belongs to
T03a. New fields can affect ordinary DTO serialization and authored hashes.

## Versioned old-document resolution

Each leaf has an immutable provenance entry with field, origin and reason.
Explicit values record `authored`; omissions record `bac-options-v1` and the
literal resolution or dependency. N is training population size; B is training
replay batch size. For resolved `curiosity_scope.scope: per_world`, omission-derived pending
capacities use local cardinality1 instead of N; explicit overrides remain authored and shared
values remain unchanged (`config/bac_options.py:172–190,255–257`). This resolver behavior does
not qualify private runtime isolation or X02. This table is the sole behavioral resolution
policy; consumers must use a resolved object rather than invent constructor defaults.

| Option | Omitted value | Unit / selected role |
|---|---|---|
| replay.sampling_mode | successive_without_replacement | Prioritized draw law; alternative independent_with_replacement |
| replay.uniform_sequence_adapter | legacy_episode_length_with_replacement | Nonprioritized recurrent law; alternative uniform_windows_with_replacement |
| replay.sequence_mode | fixed_full | Real sequence windows; alternative adaptive_prefix |
| replay.retention_mode | whole_episode | Recurrent retention; alternative transition_tail |
| replay.sequence_objective | window_mean | Loss unit; alternative anchor_transition |
| replay.priority_reduction | max_abs | Sequence priority reduction; alternative mean_abs |
| rnd.service_mode | paced_fifo | Predictor service; alternative occupancy_fifo |
| rnd.max_updates_per_tick | 1 | Ordinary predictor minibatches per vector tick in paced mode; inactive preset in occupancy mode |
| rnd.max_pending_rows | max(2*N, B) | Predictor rows; at least B; bounded-service upgrade |
| rnd.overflow_policy | service_before_admit | Lossless mandatory service; alternatives drop_oldest/drop_newest count dropped rows |
| curriculum.commit_mode | completion | Lane outcome commitment; alternative legacy_step |
| curriculum.difficulty_mode | stage_band | Direct stage band; alternative rate_limited |
| serving.policy_mode | greedy_eval | Evaluation network mode; alternative mc_dropout |
| checkpoint.save_initial | false | Initial checkpoint request |
| checkpoint.save_final | true | Committed final checkpoint request |
| provider_parameter_source | training | RND/adaptive parameter ownership; alternative drive |
| providers.count_based.quantization_width | 1/16 | Positive numeric bin width |
| providers.count_based.max_entries | training.replay_buffer.capacity | Positive finite-memory table entries |
| providers.icm.feature_dim | training.intrinsic.rnd.feature_dim | Feature width |
| providers.icm.hidden_dim | 2 * resolved providers.icm.feature_dim | Hidden width |
| providers.icm.learning_rate | training.intrinsic.rnd.learning_rate | Positive optimizer learning rate |
| providers.icm.inverse_weight / forward_weight | 0.8 / 0.2 | Nonnegative inverse/forward objective weights |
| providers.icm.training_batch_size | B | Complete transitions per predictor update |
| providers.icm.max_pending_transitions | max(2*N, resolved ICM batch size) | Complete FIFO transitions, at least one ICM batch |
| evaluation.seed | training.seed | Viewer seed |
| evaluation.episode_cap | training.training_loop.max_steps_per_episode | Eligible episode cap; historical 500 remains explicit |
| evaluation.epsilon | training.exploration.epsilon_end | Viewer exploration probability [0,1] |
| evaluation.curriculum_state_policy | fresh | Viewer curriculum state; alternative retain_compatible |
| evaluation.reward_metric | extrinsic | Display/score component; alternatives intrinsic, shaping, total |

Evaluation policy mode uses `serving.policy_mode`; world and policy identities
are compiler-derived. T27 must construct the EvaluationRunView and record viewer
overrides; this table does not yet alter serving behavior.

## Encoder declaration and preservation

Under `architecture.token_set` or `architecture.recurrent`, `token_encoder`
accepts `{mode: linear}` (no hidden width) or `{mode: interaction_mlp,
hidden_width: <positive integer>}`. `config.bac_options.TokenEncoderOptions` is the portable declaration.
`resolve_token_encoder` returns the immutable
selection and its origin. Omission resolves to linear with a bac-options-v1
receipt. The new field is schema-only until T17 consumes it. Mean and attention
remain selectable; linear mean retains its known descriptor/value association
limitation. Zero-width flat-network constant policies remain valid. Token
rosters, capacities, observation widths and action geometry stay compiler-owned.

## Provider precedence and truthful roles

The drive continues to select all five accepted strategies: none, rnd,
adaptive_rnd, count_based and icm. This block does not introduce a competing
strategy selector. Explicit typed count/ICM values override the same recognized
raw-drive key, which overrides recorded derived values. The T02 resolver records
schema defaults and typed selections only; **T18a still owes raw-drive precedence,
located same-precedence conflict diagnostics, and final provider field roles**.
In particular, its output alone must not be used to distinguish an explicit
value from a derived one; retain the provenance and authored block.

RND/adaptive dictionary values remain presets unless provider_parameter_source
is drive; training owns those knobs by default. Nonselected typed provider values
and nonselected/unknown raw drive keys remain losslessly retained authoring,
with inactive-key roles supplied by T18a. Count/ICM typed options are active only
for their selected provider. Training annealing/survival parameters are active
only for adaptive_rnd; other providers retain them as inactive presets. None has
zero raw novelty. Zero intrinsic scale remains accepted. Actual provider dispatch,
reward scaling and service implementation are later work, not established by
these schema tests.

Replay warmup counts retained eligible transitions; backend readiness separately checks actual
row/window support for the selected law. Authored `min_size` is positive and no greater than
capacity; explicit `VectorizedPopulation.for_training` accepts a nonnegative threshold. Batch
size may exceed warmup, and replacement laws can draw more units than their positive support.
Successive laws require sufficient distinct sampleable units; recurrent transition occupancy
alone does not establish window cardinality. The population logs changed unready diagnostics
(`config/training_v2_config.py:102`, `population/vectorized.py:654,715`).

Other conditional roles: replay sampling applies to PER; the uniform adapter
applies to nonprioritized recurrent sampling; sequence/objective/retention and
sequence reduction are recurrent settings, retained presets elsewhere. Predictor
service is relevant to RND/adaptive and ICM, with count/none zero predictor work.
`stage_band` retains adaptation_rate as inactive preset; rate_limited is the
planned active consumer. Nonselected architecture/optimizer/schedule blocks are
validated inactive presets, not erased.

K02: accepted stage graphs, active-meter and reward-mode labels remain retained;
their richer mechanics are unqualified, not forbidden. K04: recording criteria
remain losslessly retained; periodic selection is the existing operational path,
other criteria are unqualified. No new option claims to implement either surface.

The four complete packs under `configs/test/bac_remediation` exercise every new
literal, both aggregators and encoders, with options-only examples in `options/`.
Tests compile copies with the public UniverseCompiler, exercise compiled DTO and
msgpack cache round-trips, and rename declarations without changing resolutions.
These are authoring/transport checks, not whole-BAC runtime qualification.
