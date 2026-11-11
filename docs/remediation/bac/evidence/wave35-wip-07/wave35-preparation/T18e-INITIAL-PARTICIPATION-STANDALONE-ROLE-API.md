# Real standalone role construction: owned POP call-site API

READONLY fixture capsule. Existing exact-five context remains POP2612/RP1299/clock48/state263/parenttest777=4999; metadata rechecked before rereads, unchanged hashes as INITIAL-PARTICIPATION-POP-OWNER-FACTS. Only this ignored file written. No factory/network/replay/curriculum/ENV/helper sixth body, source/test edit, import/probe/reflection/runtime/test/git/index/branch/worktree/source copy. These are exact actual caller APIs, not a factory-implementation audit or copied helper body.

## Constructor-binding constraint

POP `_initialize`320 calls `env.set_exploration_runtime(exploration=exploration,claim_vector_step=self.claim_vector_step)` before its actual Q construction. `for_training` always reaches that initialization. Thus constructing POP consumes ENV's once-only setter for the actual POP callback. A later component controller cannot replace it, even with the same runtime; role registration does not change callback custody. Do not construct POP merely to obtain roles and then bypass its claim/activation with another controller.

Two honest choices: use actual POP as registered population with its own genuine reset/claim and coordinated new participation consumer (currently missing), or construct the real components independently through the calls below and register an explicitly limited component controller as population. The latter proves actual ENV/component ownership, not actual POP/Q-learning/replay/curriculum E2E. Normal nine roles remain required; no reduced profile or dummy model/buffer is proposed.

## Inputs already supplied by public compiled fixture facts

Parent `make_parent`142 uses selected=`compiled.get_level(compiled.metadata.primary_level)`, effective=`compiled.effective_run`, actual selected TokenSpec width D and actual action_metadata.total_actions A; actual explicit device/roster/seed/ordered IDs. It calls `apply_training_overrides(compiled.brain,selected.training)` from `townlet.config.brain_config` for the effective real BrainConfig. No selected.brain or invented geometry. Actual smoke architecture is token_set with mean pooling/Adam/nonprioritized replay; use its real typed config. These factories need no POP instance. Keep actual declared N, ENV/descriptor/IDs and curriculum initialization consistent; unchanged parent smoke recipe uses N8. A separately authored two-world fixture must explicitly preserve that consistency, not silently reuse an eight-row initialized manager.

## Real Q/target/optimizer/loss calls

Public imports actually used at POP24–27: `LossFactory` from townlet.agent.loss_factory; `NetworkFactory` from townlet.agent.network_factory; `OptimizerFactory` from townlet.agent.optimizer_factory. Actual `_build_network`1266–1315 dispatches:

| Actual architecture | Actual callable and exact keyword names |
|---|---|
|token_set|`NetworkFactory.build_token_set(config=brain.architecture.token_set,action_dim=A,token_spec=env.token_spec)`|
|recurrent|`NetworkFactory.build_recurrent(config=brain.architecture.recurrent,action_dim=A,token_spec=env.token_spec)`|
|feedforward|`NetworkFactory.build_feedforward(config=brain.architecture.feedforward,obs_dim=D,action_dim=A)`|
|dueling|`NetworkFactory.build_dueling(config=brain.architecture.dueling,obs_dim=D,action_dim=A)`|

Pass the actual selected non-None typed subconfig; do not fabricate a namespace or substitute another architecture. Actual POP calls the selected builder twice and `.to(device)` on each returned real nn.Module, then `target.load_state_dict(q.state_dict())` and `target.eval()` (POP335–351). A component fixture can retain those actual objects. If it only needs the registered network owner, that is the actual online Q object, not a fake class; it must not claim a learner executed merely because construction succeeded.

Actual POP356 call: `optimizer,scheduler = OptimizerFactory.build(config=brain.optimizer,parameters=q.parameters())`. This directly associates the returned real optimizer with the actual online Q Parameters; do not detach/deepcopy the optimizer independently. Request real Adam through the genuine selected optimizer config (smoke type adam), not a handwritten optimizer stand-in. Scheduler comes from this returned pair; the source treats it as optional. Do not invent a scheduler object when None. Optional loss: `LossFactory.build(config=brain.loss)` (POP362). No direct Adam or scheduler constructor kwargs beyond this factory call are established here.

## Real replay construction

Imports already used by POP: ReplayBuffer from townlet.training.replay_buffer; PrioritizedReplayBuffer from townlet.training.prioritized_replay_buffer; SequentialReplayBuffer from townlet.training.sequential_replay_buffer. POP `_initialize`383–409 and `_new_replay`489–524 supply:

| Selected kind | Actual public call |
|---|---|
|Flat uniform (actual smoke)|`ReplayBuffer(capacity=brain.replay.capacity,device=device)`|
|Flat PER|`PrioritizedReplayBuffer(capacity=brain.replay.capacity,alpha=brain.replay.priority_alpha,beta=brain.replay.priority_beta,beta_annealing=brain.replay.priority_beta_annealing,device=device)`|
|Qualified flat PER sampler|On the actual PER object: `configure_sampling(sampling_mode=options.sampling_mode,rng=actual_numpy_generator,origin=explicit_origin)`; parent passes these by required keywords.|
|Recurrent uniform|`SequentialReplayBuffer.for_replay(capacity,device,options=options,action_dim=A,legality_mode='captured')`|
|Recurrent PER|`SequentialReplayBuffer.for_prioritized_replay(capacity,device,options=options,action_dim=A,legality_mode='captured',alpha=alpha,beta=beta,beta_annealing=annealing,beta_vector_tick_horizon=horizon,current_vector_tick=tick,rng=actual_numpy_generator,origin=explicit_origin)`|

Options are actual fully resolved ReplayOptions, obtained at the parent call site through `resolve_bac_options(selected.training.bac_options,training=selected.training).options.replay`. For PER all configured alpha/beta/annealing values must exist. Parent for_training supplies explicit actual NumPy Generator, origin, vector-tick horizon and current tick; no hidden seed/default belongs in a standalone constructor. Current flat uniform needs only actual capacity/device and adopts real successor legality on genuine push_recorded; merely constructing it is not replay admission or learning. Retirement must leave the real buffer unchanged. No factory body was opened and no unsupported convenience factory is invented.

## Real curriculum and runtime calls

Parent test153–161 imports `build_curriculum` from townlet.curriculum.factory and calls `build_curriculum(effective.training,curriculum_options=effective.options.curriculum,static_policy=effective.static_policy,device=device)`, then `curriculum.initialize_population(N)`. This is the source-backed standalone real-manager recipe. **No HybridCurriculum constructor/import appears in the owned POP/RP/state/parent fixture.** Do not guess a class alias or its kwargs. If a literal HybridCurriculum class is mandatory, its owner must qualify it; the actual selected factory route above does not require POP and avoids that unknown.

Actual selected policy is either the already-qualified `policy(compiled,family,scope,'paced_fifo')` return alone (not Rig/service), or the parent's validated actual drive/training/BaCOptions resolver route. Import `build_exploration` and `resolve_exploration_policy` from townlet.config.exploration_policy; WorldCuriosityDescriptor from townlet.exploration.world_curiosity_state. Parent172–209 calls `WorldCuriosityDescriptor.from_policy(selected_policy,world_ids=ids,observation_dim=D,action_dim=A,training_seed=selected.training.seed)` and `build_exploration(policy=selected_policy,descriptor=descriptor,device=device,validate_accepted_episode=env.validate_accepted_episode,issuer_factory=issuer_factory,report_allocation=reports.append,validate_committed_batch=actual_owner_validator,validate_parent_cadence=actual_owner_cadence_validator)`.

The real issuer_factory receives actual BANK, retains it for curiosity registration and returns actual `WorldReceiptIssuer(owner=bank)` (public import from townlet.environment.vectorized_env). Runtime facade is a different object. The two parent callbacks must validate the actual cooperative owner's retained genuine request/outcome/cadence state; presence of no-op lambdas is not authority. No mutable-child accessor or fake policy/descriptor/provider is needed. Constructor/model RNG use occurs before the retirement before/after witness; do not count legitimate initialization as a retirement effect or secretly alter selected RNG recipes.

## Normal nine-role template and ordering

With independently built real components, register population=the actual cooperative controller; curiosity=captured actual BANK; curriculum=real initialized manager; exploration=actual runtime; network=actual online Q; optimizer=its actual factory optimizer; replay=actual selected buffer; selection=actual runtime selector owner. Scheduler role is the actual returned scheduler when present. If the genuine selected factory returns None, the actual coordinating population/controller owns that explicit absence, as actual parent fixture binds POP for that role; no DummyScheduler or fabricated optimizer work is needed. Roles may coincide under the existing world contract. Retain actual issuer objects and attest only operations that really occurred, never absent native/all-child state.

Construct ENV without POP, construct these actual components/controller/runtime, then invoke ENV's once-only runtime setter with the real runtime and the cooperative controller's honest issued-step/once-claim callback **before** binding world roles. Bind all nine actual roles, bootstrap and use genuine reservation/reset/activation. New initial participation must use the proposed actual owner protocol before activation, not a direct dones write. That protocol is not yet an existing public producer. A component registry/controller must be explicitly labelled as such; it cannot issue a handle claiming actual POP custody or manufacture native output/receipts to satisfy assertions.

If the desired test requires actual POP current_obs/completed/ledger/replay/optimizer behavior, use actual POP and its constructor-bound callback unchanged. The present missing POP participation consumer cannot be bypassed by rebinding; root must stage coherent actual ENV+POP implementation/tests. Independent real components are sufficient for a truthful ENV component test, not a substitute for required C real POP learning/A-only replay/B nonparticipation, full D stable native restore, E/F/B1 or whole-programme acceptance. These are finite constructor facts; no recursive purity audit or new capability-reducing profile is required.
