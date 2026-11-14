# Actual runner replay-profile construction capsule

Read-only implementation inspection for the profile acceptance owner. No production/test edits, execution, imports, Git, branches/worktrees or executable copies. This new prose capsule is the only write. Inventory remains exactly POP3571 SHA256 `ee3aa7d0d37f07fae221217fd4b5fb24f873ad39371eb06954f7b719301bc2c8` and runner1356 SHA256 `4f05e0eec706c4b64efc0b7adc3ebd7117446f0d17e419648a1ed812e1158018`: two whole bodies/4927 lines. No DTO, network, replay implementation or test body was opened. Root reports R170 seven real runner cases and119 native components passing; those results do not establish these additional selected replay profiles.

## Authoring that reaches actual construction

Runner uses `effective_run.effective_brain`, not an unmodified raw brain after launch/authoring overrides, and `effective_run.options.replay`, not a replacement fixture sampler. Effective training supplies seed, population size, replay batch/minimum and loop settings. Profile tests must assert these effective values so an override cannot silently undo the intended profile.

| Intended profile | Effective brain selection | Actual selected constructor before binding |
| --- | --- | --- |
| Prioritized flat | `architecture.type` is nonrecurrent (feedforward, dueling or token_set); `replay.prioritized=True`; authored capacity, nonnull priority_alpha, priority_beta and priority_beta_annealing | `PrioritizedReplayBuffer(...)` then `configure_sampling(sampling_mode=resolved_options.sampling_mode, rng=owned_rng, origin='authored')` |
| Uniform recurrent | `architecture.type='recurrent'` and its required `architecture.recurrent` block; `replay.prioritized=False`; authored capacity | `SequentialReplayBuffer.for_replay(capacity, device, options=resolved_options, action_dim=actual_action_dim, legality_mode='captured')` |
| Prioritized recurrent | Same actual recurrent architecture; `replay.prioritized=True` with nonnull priority_alpha/beta/beta_annealing | `SequentialReplayBuffer.for_prioritized_replay(..., options, actual action_dim, legality_mode='captured', alpha, beta, beta_annealing, beta_vector_tick_horizon, current_vector_tick, rng, origin)` |

The recurrent Q-network is constructed through `NetworkFactory.build_recurrent(config=architecture.recurrent, action_dim=actual_action_dim, token_spec=env.token_spec)`. It is not a generic flat-observation LSTM substitution. Exact authored recurrent-block fields and child-supported sampling/sequence enum values are outside these two inspected bodies; the acceptance owner must use its actual schema/child-source supplier or an existing valid authored configuration. This capsule does not invent YAML values.

`_ReplaySetup.create` clones the resolved ReplayOptions and requires every one of its six fields nonnull. The inspected consumer explicitly uses sampling_mode, sequence_mode and sequence_objective; it does not enumerate the remaining three field names. Keep the complete real resolver output. POP passes batch_size from effective training.replay_buffer.batch_size, min_transitions from min_size, sequence_length/train_frequency/max_grad_norm from the authored training_loop. Uniform flat hardcodes its own actual transition request; recurrent and PER requests use selected resolved policy. Do not carry that flat shortcut into a recurrent test.

## Ordering and reproducible horizon

`DemoRunner.run` calls `VectorizedPopulation.for_training(...)` with the selected effective brain/options, a real NumPy Generator(PCG64(training.seed)), origin='authored', current_vector_tick=0, and beta horizon `runner.max_episodes * training_loop.max_steps_per_episode` with its actual origin string. The factory creates a nonnull `_ReplaySetup` with preserve_global=False. `_initialize` calls `_new_replay` immediately and records `_bound_replay` as that selected live object. Only afterward does runner initialize curriculum and bind ENV's actual nine role owners, including the already-selected replay object.

Therefore normal runner construction needs no post-binding replay swap or `_bind_training` conversion to select any of these profiles. Do not monkeypatch `population.replay_buffer` after ENV binding to manufacture coverage. The older base-constructor/inspection transport adaptation path is separate; its six missing explicit lineage arguments are already reported and do not establish a blocker for the genuine for_training path.

Keep source and receiving authored beta-horizon inputs unchanged. To exercise continued learning, use an earlier real completed checkpoint within the same authored run horizon, rather than extending max_episodes on the receiving runner and silently changing a prioritized-recurrent continuation contract. Actual sequential priority validation relates current_vector_tick to restored POP total_steps and horizon to the selected setup. Native installation must retain real sampler RNG, priorities and clock; reconstructing an initial seeded sampler is not continuation. Ambient Torch RNG restoration remains a separate last child.

## Obtaining an actual recurrent update

Recurrent rows accumulate in POP's per-lane episode containers. `_store_episode_and_reset` stores the real complete captured episode with successor masks and legality provenance on finalization. The vector-step path calls `_learn` before finalizing newly terminal lanes; externally stopped surviving lanes are flushed later by runner's completion choreography. Consequently a first just-completed episode need not have produced a recurrent learner update. Configure enough real completed history and subsequent eligible steps for readiness, batch size, sequence length/objective and train_frequency. Require actual `training_step_counter`/optimizer history advancement; do not infer learning from completed episode count or stored fragments alone.

A meaningful profile witness retains the existing real route: selected production construction → actual steps/learning → written current native artifact → genuinely fresh runner with the same authored profile → next real learner update. Check selected actual replay class/policy and native sampler/priority/episode data where the producer contract supports it; component object counts are not acceptance.

## Current limits and blockers

- Root reports PER/sequential native stage/install owners are authoring or running their dedicated RED cases during the current freeze. Their final public implementation/qualification must precede claiming successful profile restore. Runner invokes the real required stage/install methods unconditionally; there is no fallback dispatcher.
- Exact child enum combinations, recurrent model DTO fields, sampler/native publication guarantees and historical archive policy require their actual owners. This two-body supplier cannot certify them.
- Native artifacts now require strict POP version8 and real optimizer_parameter_updates. Build fresh current artifacts; do not seed old schema fixtures with invented trained counts.
- Existing pending initialized-history/provider-ledger/hardware/global gates retain their status. The newly selected profile tests do not waive those obligations or automatically qualify CUDA.

Production remains untouched under the R171 freeze. Root owns execution and source-exact acceptance.
