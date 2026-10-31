# SG6 — RL Training Stack

**Locations:** `src/townlet/agent/`, `src/townlet/population/`, `src/townlet/training/`, `src/townlet/exploration/`, `src/townlet/curriculum/`
**Actual LOC and file counts (from `wc -l` and `ls`):**

| Subsystem    | Files (.py)                                                                                                                | LOC  |
| ------------ | -------------------------------------------------------------------------------------------------------------------------- | ---- |
| `agent/`     | `networks.py` (654), `network_factory.py` (225), `optimizer_factory.py` (162), `loss_factory.py` (42), `__init__.py` (1)   | 1084 |
| `population/`| `vectorized.py` (1201), `runtime_registry.py` (~135), `base.py` (~70), `__init__.py` (1)                                   | ~1407|
| `training/`  | `replay_buffer.py` (448), `prioritized_replay_buffer.py` (444), `sequential_replay_buffer.py` (358), `tensorboard_logger.py` (432), `checkpoint_utils.py` (260), `state.py` (285), `__init__.py` (1) | 2228 |
| `exploration/` | `rnd.py` (343), `adaptive_intrinsic.py` (228), `base.py` (118), `epsilon_greedy.py` (118), `action_selection.py` (93), `__init__.py` (1) | 901 |
| `curriculum/`| `adversarial.py` (531), `static.py` (126), `base.py` (81), `factory.py` (70), `__init__.py` (1)                            | 809  |

**Confidence:** High for `agent/`, `population/` (entry points + full `step_population` read), `exploration/` (all files), `curriculum/` (all files), and the front-half of each replay buffer. Medium for the deeper serialization tails of the replay buffers (`stats`, `serialize`, `load_from_serialized`), `checkpoint_utils.py` after line 200, and `tensorboard_logger.py` (method names surveyed but bodies unread).

**Prompt-vs-reality reconciliation.** Several items in the SG6 brief disagree with what is in the tree as of `project-recovery` HEAD. The brief talks about `exploration/icm.py`, `exploration/count_based.py`, and `exploration/adaptive_rnd.py`; none exist on disk. `agent/` is 5 files (not 5 source modules; `__init__.py` is a 1-line docstring stub). `population/` has 4 files, not 3 (a `runtime_registry.py` and a small `base.py` accompany `vectorized.py`). `training/` has 7 files, including a `prioritized_replay_buffer.py` and a separate `sequential_replay_buffer.py` that aren't in the brief's narrative. I describe what is actually there.

## Overall responsibility

The five subsystems are the off-policy Q-learning training loop. The orchestrator is `VectorizedPopulation.step_population`
(`src/townlet/population/vectorized.py:606`). Each tick it: (1) gets Q-values from the online network; (2) asks the curriculum
manager for batch decisions (with Q-values when the curriculum is `AdversarialCurriculum`); (3) calls the exploration strategy
for action selection under action masks; (4) steps the environment (rewards are already DAC-composed by the environment); (5)
stores the transition (`ReplayBuffer` / `PrioritizedReplayBuffer` for feed-forward; `SequentialReplayBuffer` for recurrent); (6)
trains the RND predictor if the strategy is novelty-based; (7) on `train_frequency` ticks samples a batch and does a DQN or
Double-DQN target step (`vectorized.py:760` … `987`); (8) periodically syncs the target network and steps the LR scheduler; (9)
resets per-agent hidden state on dones; (10) returns a `BatchedAgentState`.

Two things to keep clear about responsibility boundaries:

- **Reward composition lives in DAC inside the environment, not here.** `step_population` *receives* a fully composed total
  reward tensor from `envs.step(...)` and *re-stores* the components for provenance (`vectorized.py:692–712`). The "intrinsic
  reward" that exploration strategies compute is recomputed here purely for logging — `update_stats=False` at
  `vectorized.py:700`. Comments throughout call this out ("DAC engine already includes intrinsic in the rewards tensor",
  `vectorized.py:696`, `:1008`).
- **No `ExplorationStrategy.update()` is called from the training loop.** Despite the ABC at
  `exploration/base.py:75`, the actual training path bypasses `update()` and calls `rnd.update_predictor()` directly when
  the strategy is `RNDExploration | AdaptiveIntrinsicExploration` (`vectorized.py:744–752`).

---

## Subsystem 1: `agent/`

### Files

- `networks.py` (654 LOC) — 4 nn.Module classes
- `network_factory.py` (225 LOC) — `NetworkFactory` with 4 static builders + `_get_activation`
- `optimizer_factory.py` (162 LOC) — `OptimizerFactory` (Adam / AdamW / SGD / RMSprop) + LR schedulers (constant / step_decay / cosine / exponential)
- `loss_factory.py` (42 LOC) — `LossFactory` (mse / huber / smooth_l1)
- `__init__.py` — 1-line docstring; not a public-API curator

### Networks

**`SimpleQNetwork(obs_dim, action_dim, hidden_dim)`** (`networks.py:14`).
A 3-Linear MLP `obs → h → h → action` with `LayerNorm` + `ReLU` between layers. `forward(x) → q_values` (`networks.py:41`).
No dropout. Tagged "PDR-002" — all dims explicit, no defaults.

**`RecurrentSpatialQNetwork(action_dim, window_size, position_dim, num_meters, num_affordance_types, enable_temporal_features, hidden_dim, observation_spec=None, temporal_embed_dim=16)`** (`networks.py:53`).
Architecture:
- Vision encoder: `Conv2d(1→16, 3×3) → ReLU → Conv2d(16→32, 3×3) → ReLU → Flatten → Linear(32·W·W, 128) → LayerNorm → ReLU` (`networks.py:117–126`).
- Position encoder: `Linear(position_dim, 32) → ReLU`, or `None` if `position_dim == 0` (aspatial) (`networks.py:129–139`).
- Meter encoder: `Linear(num_meters, 32) → ReLU` (`networks.py:142`).
- Affordance encoder: `Linear(num_affordance_types + 1, 32) → ReLU` (the `+1` is a "none" slot) (`networks.py:154`).
- Temporal encoder: `Linear(4, temporal_embed_dim=16) → ReLU` (`networks.py:148`). The 4 is `self.temporal_dims = 4` — "Fixed v2.1 temporal feature count" (`networks.py:110`).
- LSTM: `nn.LSTM(input=128+pos+32+32+16, hidden=hidden_dim, num_layers=1, batch_first=True)` (`networks.py:159–162`). With Grid2D and temporal features, input is `128 + 32 + 32 + 32 + 16 = 240` (note: the docstring at line 62 claims `224` and `192`; both are stale relative to the temporal-encoder addition).
- Output: `LayerNorm(hidden) → Linear(hidden, 128) → LayerNorm → ReLU → Linear(128, action_dim)`.

`forward(obs, hidden=None) → (q_values, new_hidden)` (`networks.py:207`). It is **mandatory** that the network was constructed with an `ObservationSpec`; otherwise forward raises (`networks.py:228–229`: `"ObservationSpec-driven slicing is required in v2.1; legacy positional layout is no longer supported."`). The spec is consulted at construction to set 5 slice objects (`_grid_slice`, `_position_slice`, `_meters_slice`, `_affordance_slice`, `_temporal_slice`, `networks.py:186–205`) which then drive runtime slicing.

Hidden-state management is exposed via three methods (`networks.py:292–318`): `reset_hidden_state(batch_size, device)`, `set_hidden_state((h, c))`, `get_hidden_state()`. The population class is the sole owner of when these get called.

**`DuelingQNetwork(obs_dim, action_dim, shared_dims, value_dims, advantage_dims, activation, value_activation, advantage_activation, dropout, layer_norm)`** (`networks.py:321`).
Standard Wang-et-al. dueling decomposition: shared trunk → value head (scalar) and advantage head (action_dim), recombined as `V + (A - mean(A))` (`networks.py:425`). Activation is configurable per stream.

**`SetEncoderQNetwork(obs_dim, action_dim, token_slice, token_shape, token_embed_dim, base_hidden_dim, q_head_hidden_dim)`** (`networks.py:443`).
Permutation-invariant mean pooling over a fixed-capacity token region of the flat observation. Reshapes a slice of `obs` into `[B, max_tokens, token_dim]`, encodes per-token with `Linear → LayerNorm → ReLU`, masks "empty" rows (sum-of-abs == 0), mean-pools, concatenates with the non-token base encoding, and feeds the result through a 2-layer Q-head (`networks.py:516–536`).

**`StructuredQNetwork(obs_dim, action_dim, observation_activity, group_embed_dim=32, q_head_hidden_dim=128)`** (`networks.py:558`).
Builds one encoder per semantic group from `observation_activity.group_slices` (e.g. spatial / bars / affordances / temporal /
custom), each `Linear → LayerNorm → ReLU` to `group_embed_dim`. Concatenates and feeds a 2-layer Q-head. **Important and possibly load-bearing:** `StructuredQNetwork` is defined and tested (`tests/test_townlet/unit/agent/test_structured_qnetwork.py`) but `NetworkFactory` has no `build_structured` method — the factory supports `feedforward`, `recurrent`, `dueling`, and `set_encoder` only (`network_factory.py:23–206`). `VectorizedPopulation._build_network` matches the factory's coverage and would raise on an unsupported `architecture.type` (`vectorized.py:395`). So `StructuredQNetwork` is **dead from the perspective of the training loop** until someone wires it in.

### Patterns

- **Double DQN support.** Honoured in `population/vectorized.py` only — see Subsystem 2.
- **Target network handling.** Built unconditionally for every architecture by mirroring the online `_build_network` call (`vectorized.py:161`), `load_state_dict` from online once at init, then set to `.eval()` (`vectorized.py:164–165`). Periodically synced inside `step_population` (see below).
- **LSTM state management.** Handled in three places: (a) construction-time spec slicing (`networks.py:186`), (b) per-step rollout — `recurrent_network.set_hidden_state(new_hidden)` after forward (`vectorized.py:645`), (c) per-training-batch — reset to zeros at the start of each sequence sweep (`vectorized.py:777`, `:789`, `:794`), and (d) per-episode-end — `_reset_hidden_state(agent_idx)` zeros only that agent's slice of `(h, c)` (`vectorized.py:428–442`).
- **PDR-002 ("no defaults") discipline.** Comments throughout assert no hidden defaults. Optimizer/loss factories use `assert ... is not None` to crash-loudly on schema gaps (`optimizer_factory.py:57–58`, `loss_factory.py:35`).

### Dependencies

- **Inbound:** `population/vectorized.py` (instantiates networks via `NetworkFactory`, builds optimizers and loss via factories — `vectorized.py:18–21`).
- **Outbound:** `torch.nn`, `torch.optim`, `torch.optim.lr_scheduler`, and Pydantic config models in `townlet.config.brain_config` (`network_factory.py:13–14`, `optimizer_factory.py:17`, `loss_factory.py:8`). Recurrent and set-encoder builders also import the universe DTOs `ObservationSpec` / `ObservationActivity` for slice metadata (`networks.py:11`, `network_factory.py:17`).

---

## Subsystem 2: `population/`

### Files

- `vectorized.py` (1201 LOC) — `VectorizedPopulation`
- `runtime_registry.py` (135 LOC) — `AgentTelemetrySnapshot` (dataclass) + `AgentRuntimeRegistry`
- `base.py` (70 LOC) — `PopulationManager` ABC with two abstract methods (`step_population`, `get_checkpoint`)
- `__init__.py` — empty docstring

### `VectorizedPopulation`

Constructor (`vectorized.py:50–252`) takes the env, a `CurriculumManager`, an `ExplorationStrategy`, agent ids, device,
`BrainConfig`, plus four required scalars (`train_frequency`, `batch_size`, `sequence_length`, `max_grad_norm`, `action_dim`,
`vision_window_size`). `brain_config is None` raises with a "no legacy fallback" message at line 93. `observation_spec` must
exist on the env or it raises at line 102.

Per-tick `step_population(envs)` (`vectorized.py:606–1029`) does:

1. **Device sanity** (`:620–637`). Refuses to step if `current_obs.device` ≠ `self.device`. Treats `cuda` and `cuda:0` as equal.
2. **Forward pass on online network** (`:640–647`). Recurrent path also calls `set_hidden_state(new_hidden)` so the recurrent rollout carries memory across env steps.
3. **Construct a transient `BatchedAgentState`** to hand to curriculum (`:650–659`).
4. **Curriculum decisions** (`:662–674`). Calls `get_batch_decisions_with_qvalues(temp_state, agent_ids, q_values)` if the curriculum implements it (the adversarial curriculum does), else `get_batch_decisions(...)`. This is the type-test that lets `StaticCurriculum` ignore Q-values entirely.
5. **Sync curriculum metrics to the runtime registry** (`:677`, `_sync_curriculum_metrics` at `:461`). Difficulty `[0,1]` is mapped to a 1–5 discrete stage via `_difficulty_to_stage` (`:482`).
6. **Action masking** from `envs.get_action_masks()` (`:680`).
7. **Action selection** via `self.exploration.select_actions(q_values, temp_state, action_masks)` (`:683`).
8. **Env step** with the *first* curriculum agent's `depletion_multiplier` as a scalar (`:686–693`). N.B. only `decisions[0].depletion_multiplier` is used — this is a single global knob, not per-agent.
9. **Intrinsic logging** (`:698–700`). `compute_intrinsic_rewards(self.current_obs, update_stats=False)` for RND-family strategies. Stats are **not** updated here (comment at `:697`: "stats updated in env during reward calc").
10. **Replay-buffer push** (`:703–741`). DAC components are pulled from `info["reward_components"]` and packed into a `RewardTensor.from_dac(...)`. Feed-forward path calls `self.replay_buffer.push(...)`. Recurrent path appends to a per-agent `current_episodes[i]` dict (full episode is flushed via `_store_episode_and_reset` when `done` fires, `:1003–1004`).
11. **RND predictor training** (`:744–752`). Adds observations to `rnd.obs_buffer`, calls `rnd.update_predictor()` (no-op until the buffer hits `training_batch_size`).
12. **Q-network training** (`:755–991`), gated by `self.total_steps % train_frequency == 0` and a min-buffer check (`16` for recurrent, `batch_size` for feed-forward).
13. **Episode-end housekeeping** (`:999–1005`). For agents whose `done == True`, calls `_finalize_episode(idx, survival_time)`, which records survival, lets `AdaptiveIntrinsicExploration` consider annealing, syncs telemetry, zeros the episode step counter, and zeros that agent's LSTM hidden slice.

### Q-learning variants — where the `use_double_dqn` flag is honoured

- Read once at construction from `brain_config.q_learning.use_double_dqn` (`vectorized.py:121`).
- Honoured twice:
  - **Feed-forward path** (`vectorized.py:917–927`). If `use_double_dqn`: `next_actions = self.q_network(next_obs).argmax(1)`; `q_next = self.target_network(next_obs).gather(1, next_actions.unsqueeze(1)).squeeze()`. Else `q_next = self.target_network(next_obs).max(1)[0]`.
  - **Recurrent path** (`vectorized.py:791–841`). If `use_double_dqn`: three passes through the sequence — one to collect `q_pred` from the online net (already done in pass 1), one to get *next-action* argmaxes from the online net at each `t`, one to get Q-values from the target net at each `t`; then `q_next = q_values_list[t+1].gather(1, next_action_list[t+1].unsqueeze(1)).squeeze()`. The CLAUDE.md claim "3 forward passes for recurrent vs 2" is correct.
- The flag is **also persisted in the checkpoint indirectly** — `brain_config` is part of the universe config, so its hash flows through `brain_hash` (see `training/checkpoint_utils.py:41`, `:111–120`).

### Target-network sync, scheduler, gradient clipping

- Target sync (`vectorized.py:893–894`, `:986–987`): `training_step_counter % target_update_frequency == 0` → `target.load_state_dict(online.state_dict())`. Counter is **per training event**, not per env step (it increments only inside the trainable branch).
- Gradient clip: `torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), max_norm=self.max_grad_norm)` for both paths (`:881`, `:958`). `max_grad_norm` is required.
- LR scheduler stepped after each optimizer step when present (`:885`, `:962`).

### Detailed walk: the feed-forward DQN training step

When `total_steps % train_frequency == 0` and the buffer has at least `batch_size` transitions:

1. **Sample.** Either uniform (`ReplayBuffer.sample`, `:911`) or prioritised (`PrioritizedReplayBuffer.sample`, `:906`).
   In the PER case, IS weights and integer indices come back in the batch dict. In the uniform case, `weights` is
   constructed locally as a tensor of ones (`:912`).
2. **Online Q-prediction.** `q_pred = self.q_network(batch["observations"]).gather(1, batch["actions"].unsqueeze(1)).squeeze()` (`:915`). The gather narrows the `[batch, action_dim]` output to the action that was actually taken.
3. **Target Q.** Either Double-DQN or vanilla, gated by `self.use_double_dqn` (`:919–925`). The vanilla path takes
   `q_next = self.target_network(next_obs).max(1)[0]`; the Double-DQN path uses the *online* network to choose actions
   and the *target* network to evaluate them. In both branches the discount uses `~batch["dones"]` so that terminal
   transitions zero out the bootstrapped value.
4. **TD-error.** `td_errors = (q_pred - q_target).abs()` (`:930`). Used both for PER priority updates and as a logged
   training metric.
5. **Loss.** Two paths:
   - PER: per-sample loss via `F.{mse,huber,smooth_l1}_loss(..., reduction='none')`, then `loss = (weights * per_sample_loss).mean()` (`:936–944`).
   - Non-PER: `loss = self.loss_fn(q_pred, q_target)` using the configured loss module (`:947`).
6. **Backprop.** `optimizer.zero_grad()` → `loss.backward()` → `clip_grad_norm_(parameters, max_norm)` → `optimizer.step()` (`:956–959`).
7. **LR schedule.** `scheduler.step()` if present (`:962`).
8. **Priority update.** PER only: `per_buffer.update_priorities(indices, td_errors)` (`:967`), then `anneal_beta(...)` if
   the buffer is configured for it and `max_episodes`/`max_steps_per_episode` are both provided (`:970–982`).
9. **Target sync.** `training_step_counter += 1`; if it's a multiple of `target_update_frequency`,
   `target_network.load_state_dict(q_network.state_dict())` (`:986–987`).
10. **Histogram log.** `_log_network_histograms()` every 100 training steps (`:989`).

### Detailed walk: the recurrent DQN training step

Similar in shape but with several differences forced by the LSTM:

1. **Sample sequences.** `sequential_buffer.sample_sequences(batch_size, seq_len)` returns observations, actions, rewards,
   dones, and a validity mask, all stacked into `[batch_size, seq_len, ...]` tensors (`:766–769`).
2. **Online pass.** Reset hidden state to zeros for the batch (`:777`). Iterate `t in range(seq_len)`, calling
   `recurrent_network(batch["observations"][:, t, :])` each step (the LSTM updates its hidden state implicitly inside
   the network — note the network's `forward` does **not** use the implicit `self.hidden_state` here because the
   population reset it explicitly first; instead each call returns `(q, new_hidden)` and the population discards the
   returned hidden in this path since `forward` re-reads `self.hidden_state` on each call via
   `set_hidden_state`... actually no, looking at the code at `vectorized.py:780–783` more carefully: the loop ignores
   the returned hidden state — `q_values, _ = recurrent_network(...)`. Hidden state advancement therefore depends on
   the network's *internal* state propagation. Inspection of `networks.py:271–278` shows the network falls back to
   `self.hidden_state` when no hidden is passed, so the unrolled hidden state is being threaded through implicitly
   via the instance attribute. That's a subtle point.) Gather Q for the action taken at each `t` into a list.
3. **Target pass.** Same loop, but with the target network. The hidden-state plumbing is *also* via instance attribute
   (`:789` resets it). For Double-DQN, an additional online pass collects argmax actions per step (`:793–801`), then a
   target-net pass collects Q-values per step (`:803–807`), and the targets are computed by gathering the target's Q
   at the next step under the online net's chosen action (`:810–820`). For vanilla DQN, one pass through the target
   net suffices and `q_next = q_values_list[t+1].max(1)[0]` (`:823–841`).
4. **Loss with masking.** `losses = F.{huber,smooth_l1,mse}_loss(q_pred_all, q_target_all, reduction='none', ...)`
   over `[batch, seq_len]`. The post-terminal mask from the replay buffer is applied: `masked_loss = (losses * mask).sum() / mask.sum().clamp_min(1)` (`:863–865`). The `.clamp_min(1)` is a defensive guard against an all-masked batch
   (which shouldn't happen in practice but would otherwise NaN the loss).
5. **Backprop + clip + step + scheduler** identical to feed-forward (`:879–886`).
6. **Hidden state cleanup.** Reset the network's hidden state back to the *episode* batch size after training, because
   the training pass mutated it to the `batch_size` from the sampled sequences (`:897–898`). This is the single most
   subtle line in the file; without it, the next env-step rollout would crash on a hidden-state shape mismatch.

### PER specifics

- PER + recurrent raises `NotImplementedError` at construction (`vectorized.py:215`).
- PER path uses per-sample loss with `reduction='none'` weighted by IS weights (`:933–944`).
- Priorities updated with `|TD-error|` from `(q_pred - q_target).abs()` (`:929`, `:967`).
- Beta annealing requires `max_episodes` and `max_steps_per_episode` to be plumbed through; otherwise warns once via `_per_beta_warning_logged` (`:974–982`).

### Checkpointing

`get_checkpoint_state()` (`vectorized.py:1085–1131`) returns a dict with `version=2`, online + target weights, optimizer / scheduler state, total_steps, exploration state, universe metadata block (meter_count, meter_names, version, obs_dim, action_dim), and replay buffer `serialize()`. `load_checkpoint_state()` (`:1133–1201`) validates `universe_metadata`, refuses meter-count mismatch (`:1158`), warns on obs_dim mismatch, then restores everything. `PopulationCheckpoint` (the Pydantic DTO from `training/state.py:191`) is a much thinner thing — `get_checkpoint()` (`:1068`) returns it for telemetry but does **not** include weights. Two distinct checkpoint paths exist; the heavy one is `get_checkpoint_state`.

### `AgentRuntimeRegistry`

A small class (`runtime_registry.py:40`) that owns 4 GPU tensors of length `num_agents`: `_survival_time`, `_curriculum_stage`, `_epsilon`, `_intrinsic_weight`. It exposes tensor and scalar accessors plus `set_*` mutators. Snapshots into `AgentTelemetrySnapshot` (dataclass at `:18`) for JSON-safe egress. Crucially, the environment receives this registry via `self.env.attach_runtime_registry(self.runtime_registry)` (`vectorized.py:128`) so the reward-side code can read curriculum stage / intrinsic weight at reward-compose time.

### Dependencies

- **Inbound:** Top-level training driver (presumed `scripts/run_demo.py` per CLAUDE.md). Out of SG6 scope.
- **Outbound:** `agent/{networks,network_factory,loss_factory,optimizer_factory}` (lines `:18–21`), `config.brain_config.BrainConfig` (`:22`), `curriculum.base.CurriculumManager` (`:23`), `exploration/{action_selection,adaptive_intrinsic,base,rnd}` (`:24–27`), `training/{replay_buffer,sequential_replay_buffer,state}` plus a local import of `PrioritizedReplayBuffer` (`:30–32`, `:196`), and an `if TYPE_CHECKING` reference to `environment.vectorized_env.VectorizedHamletEnv` (`:35`).
- Population is the **only** subsystem in SG6 that touches all the others. It's the integration node.

---

## Subsystem 3: `training/`

### Files

- `state.py` (285) — `EnvInfoDict` TypedDict, `RewardTensor`, `CurriculumDecision` (Pydantic), `PopulationCheckpoint` (Pydantic), `BatchedAgentState`.
- `replay_buffer.py` (448) — `ReplayBuffer` (uniform circular FIFO)
- `prioritized_replay_buffer.py` (444) — `PrioritizedReplayBuffer` (Schaul et al. 2016)
- `sequential_replay_buffer.py` (358) — `SequentialReplayBuffer` (episode-keyed for LSTM)
- `tensorboard_logger.py` (432) — `TensorBoardLogger` with `log_episode`, `log_training_step`, `log_meters`, `log_network_stats`, `log_affordance_usage`, `log_modifier_effects`, `log_reward_components`, `log_hyperparameters`, plus `__enter__/__exit__` (only method names verified; bodies unread).
- `checkpoint_utils.py` (260) — hash-validation and `safe_torch_load`.
- `__init__.py` — empty.

### Replay buffer (uniform, `ReplayBuffer`)

- **Capacity:** scalar, fixed at construction; storage tensors lazily allocated on first `push` once `obs_dim` is known (`replay_buffer.py:97–106`).
- **Push:** vectorised slice-write with wrap-around handling; rejects `batch_size > capacity` to prevent corruption (`:78–83`); validates that all batch dims match (`:85–95`).
- **Push accepts a `RewardTensor`**, not raw `rewards` (`:61`). It stores `rewards.total` plus optional component channels (`rewards_extrinsic`, `rewards_intrinsic`, `rewards_shaping`) so DAC provenance survives a round-trip.
- **Sample:** `torch.randperm(self.size, device=self.device)[:batch_size]` — **without replacement** (`:207`). Returns a dict with an all-True `mask` (for parity with the sequential buffer's API) (`:218–225`).
- **No prioritisation.** Uniform sampling.

### Prioritized replay buffer

- Constructor takes `alpha`, `beta`, `beta_annealing`, plus `capacity` and `device` (`prioritized_replay_buffer.py:26`).
- Priorities live in a `numpy.float32` array of size `capacity` (`:61`).
- **Sampling is O(n)** via `np.random.choice` with `replace=False` (`:177`). Comment at line 149 calls this out as future work (segment tree).
- **Push assigns max priority** to new entries (`:141`). `update_priorities` writes `|td_error| + 1e-6` per index (`:206–223`).
- **Beta annealing** is exponential interpolation from `beta_initial` to 1.0 over `total_steps` (`:225–238`). Caller (population) is responsible for invoking `anneal_beta(total_steps, current_step)` each training step.
- Distinct fields `rewards_extrinsic`, `rewards_intrinsic`, `rewards_shaping` again preserved for DAC provenance, mirroring the uniform buffer (`:96–98`).

### Sequential replay buffer (LSTM)

- Stores complete *episodes* in a `collections.deque` (`sequential_replay_buffer.py:60`). Evicts oldest episodes when `num_transitions > capacity` (`:174–177`).
- Episode dict requires `observations`, `actions`, `rewards`, `dones`; optional `rewards_extrinsic`, `rewards_intrinsic`, `rewards_shaping`. Rejects zero-length episodes; validates tensor shapes and lengths (`:128–165`).
- `sample_sequences(batch_size, seq_len)` (`:179–274`): filters to episodes with `len ≥ seq_len`, **weights episode selection by length so transition sampling is approximately uniform** (`:228–232`), picks a random valid `start_idx`, and slices. Constructs a `mask` that goes False after the first terminal in the sub-sequence to enable post-terminal loss masking (`:248–260`).
- Raises a friendly error with episode-length stats and a hint to use a `non_training_recurrent_population` fixture when there is no episode long enough (`:209–221`).

### Training state DTOs (`state.py`)

- **`RewardTensor`** (`state.py:38`) — `__slots__`-based hot-path container with `total`, optional `extrinsic`, `intrinsic`, `shaping`, and `is_composed`. Class-method constructors `from_dac` (used by the population, `:86`) and `from_components` (legacy; used by tests). Has `.to(device)`, `.cpu()`, `.batch_size`.
- **`BatchedAgentState`** (`state.py:210`) — `__slots__` for `observations, actions, rewards, dones, epsilons, intrinsic_rewards, survival_times, device, info`. No validation in `__init__` ("hot path"). HIGH-09 comment notes the `curriculum_difficulties` field was deleted as dead.
- **`CurriculumDecision`** (`state.py:167`) — Pydantic, frozen. `difficulty_level ∈ [0,1]`, `active_meters` list (length 1–6 per `MED-12`), `depletion_multiplier > 0 and ≤ 10`, `reward_mode ∈ {shaped, sparse}`, `reason` non-empty string.
- **`PopulationCheckpoint`** (`state.py:191`) — Pydantic, frozen. Holds generation, num_agents (1–1000), agent_ids, curriculum_states, exploration_states, pareto_frontier, metrics_summary. Crucially **does not** carry network weights; the heavy "checkpoint state" dict comes out of `VectorizedPopulation.get_checkpoint_state()` instead.

### Checkpoint utilities

`attach_universe_metadata` (`checkpoint_utils.py:22`) attaches: `config_hash`, `observation_dim`, `action_dim`, `meter_count`,
`observation_field_uuids`, `observation_schema_hash`, `drive_hash`, `brain_hash`, `vfs_hash`.

`assert_checkpoint_dimensions` (`:68`) enforces — and **raises** — when any of these mismatch:
- `observation_dim`, `action_dim`
- `observation_field_uuids` in order (`:92` — "comparison is order-sensitive by design")
- `drive_hash` (DAC reward function identity) (`:98–109`)
- `brain_hash` (network architecture identity) (`:111–120`)

`assert_checkpoint_vfs_hash` (`:123`) handles the explicit `--force-new-vfs` branch fork. `_compute_sha256` /
`persist_checkpoint_digest` / `verify_checkpoint_digest` provide a sidecar `.sha256` integrity check (`:150–196`). The
file ends with a `safe_torch_load` helper (line 199+, not read in full).

### Replay-buffer serialisation (the part the architecture analysis can't see at a glance)

The uniform `ReplayBuffer.serialize` (`replay_buffer.py:295–369`) is doing more than a `state_dict()`:

- **Format version 3 is required on load**; legacy formats (`version < 3`) are rejected with an explicit `ValueError`, in keeping with the project's "zero backwards compatibility" stance (`replay_buffer.py:384–388`).
- **Wrap-aware reordering.** When `has_wrapped` is true (`:185–186`), it concatenates `[position:]` onto `[:position]` *before* moving to CPU, so the deserialised buffer is in temporal order with `position = size`. The receiver re-sets `has_wrapped = (loaded_size == self.capacity)` (`:409`), preserving FIFO eviction semantics on the next push.
- **All six reward channels are persisted** (`total`, `extrinsic`, `intrinsic`, `shaping` × not, oh wait — total + extrinsic + intrinsic + shaping). All four are mirrored alongside `observations`, `actions`, `next_observations`, `dones`.
- **`obs_dim` is validated on load** against the live buffer if it was already lazily allocated, refusing the load with a clear message if dims diverged (`:415–419`).
- **Capacity downgrade is rejected**, not silently truncated (`:399–403`).

`PrioritizedReplayBuffer.serialize` / `load_from_serialized` (`prioritized_replay_buffer.py:314–444`, not all read) mirror the same shape but additionally persist `priorities`, `max_priority`, `alpha`, `beta`, `beta_initial`, and `beta_annealing` — those last three so a checkpoint resumes with the *same annealing trajectory*, not a re-randomised one.

The sequential buffer's serialisation is episode-by-episode (deque of dicts of tensors), not a single flat tensor (`sequential_replay_buffer.py:276+`).

### TensorBoardLogger surface

Read only the surface (constructor and method list). It's a `SummaryWriter` wrapper with seven log domains:

- `log_episode(episode, survival_time, total_reward, extrinsic_reward, intrinsic_reward, ...)` — per-episode scalars.
- `log_multi_agent_episode(episode, agents: list[dict])` — batched form.
- `log_curriculum_transitions(episode, events: list[dict])` — consumes the structured transition events written by `AdversarialCurriculum._record_transition_event`.
- `log_training_step(step, td_error, q_values, ...)` — per-train-tick scalars; called via `log_custom_metric` from inside the population.
- `log_meters(...)` — meter dynamics.
- `log_network_stats(...)` / `log_affordance_usage(...)` / `log_custom_action_usage(...)`.
- `log_modifier_effects(...)` / `log_reward_components(...)` — DAC-side observability hooks; the population uses `log_custom_metric` directly at `vectorized.py:323–333` rather than these.
- `log_hyperparameters(hparams, metrics)`.

Constructor knobs: `flush_every` (episodes), `log_gradients` (off by default), `log_histograms` (on by default). The population gates histogram logging behind its own `if self.tb_logger is not None and self.total_steps % 100 != 0: return` (`vectorized.py:295`) — independent of the logger's own `log_histograms` flag.

### What is persisted across episodes / checkpointed

| State                                        | Persisted across episodes? | In checkpoint? |
| -------------------------------------------- | -------------------------- | -------------- |
| Q-network weights                             | yes                        | yes (`q_network`)
| Target network weights                        | yes                        | yes (`target_network`)
| Optimizer state                               | yes                        | yes
| LR scheduler state                            | yes                        | yes
| `total_steps`, `training_step_counter`        | yes                        | yes
| Replay buffer contents                        | yes                        | yes (`serialize()`)
| Exploration state (RND nets, ε, RMS stats)    | yes                        | yes (`exploration_state`)
| Curriculum tracker (agent_stages, etc.)       | yes                        | yes via `exploration_states` slot? No — actually returned through `PopulationCheckpoint.curriculum_states`. The big `get_checkpoint_state` dict does *not* include curriculum tracker tensors. **(Concern.)**
| LSTM hidden state                             | yes within a rollout, reset on episode end | no
| `current_obs`                                 | yes                        | no — relies on reset on resume
| Episode buffers (`current_episodes`)          | within rollout only        | no

### Dependencies

- **Inbound:** `population/vectorized.py` (the sole consumer of the replay buffers and `BatchedAgentState`).
- **Outbound:** `torch`, `numpy`, Pydantic. `checkpoint_utils.py` imports `townlet.universe.compiled.CompiledUniverse`.

---

## Subsystem 4: `exploration/`

### Strategies

- **`epsilon_greedy.py` — `EpsilonGreedyExploration`** (`118` LOC). Holds three scalars (`epsilon`, `epsilon_decay`, `epsilon_min`); `select_actions` delegates to the shared `epsilon_greedy_action_selection` (`epsilon_greedy.py:60`). `compute_intrinsic_rewards` returns a zero tensor (`:80`). `update` is a no-op. `decay_epsilon` does `max(min, ε·decay)` and is called per *episode* (not per step), but **no caller in the SG6 codebase actually invokes `decay_epsilon()`** — `_get_current_epsilon_value` reads `self.exploration.epsilon` directly (`vectorized.py:447–453`) and `sync_exploration_metrics` writes the same scalar to all per-agent registry slots. So the schedule is read but not driven from this subsystem. (Possible concern — see below.)

- **`rnd.py` — `RNDExploration`** (`343` LOC) and `RNDNetwork`. `RNDNetwork` (`:68`) is `Linear(obs_dim, 256) → ReLU → Linear(256, 128) → ReLU → Linear(128, embed_dim=128)` with an `active_mask` buffer that zeroes "padding" observation dims so RND can ignore unused VFS slots. `compute_intrinsic_rewards` (`:192`): MSE between fixed and predictor embeddings, optionally `reward_rms.update(...)`, then **divided by `sqrt(reward_rms.var) + 1e-8`** to normalise (`:219`). The novelty signal is recomputed at training time for *logging only* in the SG6 path (see Subsystem 2). Predictor training: maintains a list-based `obs_buffer`, kicks off a step when `len ≥ training_batch_size` (`:242–269`), uses `F.mse_loss(predicted, target.detach())` and `torch.optim.Adam`. `RunningMeanStd` (`:17`) is a Welford-style running statistics tracker used to normalise novelty.

- **`adaptive_intrinsic.py` — `AdaptiveIntrinsicExploration`** (`228` LOC). Composes (not inherits) an `RNDExploration` instance (`:61`). Adds an annealing loop: per-episode-end (`update_on_episode_end(survival_time)`, `:134`) appends to `survival_history`, prunes to `survival_window`, and calls `should_anneal()`. The annealing predicate is **conjunctive**: `variance < variance_threshold AND mean_survival > min_survival_for_annealing`, where `min_survival_for_annealing = int(min_survival_fraction × max_episode_length)` (`:79`, `:180`). Anneal step is `weight = max(weight × decay_rate, min_weight)` (`:182–185`). `get_intrinsic_weight()` (`:187`) is the read-side that population calls.

- **`base.py` — `ExplorationStrategy`** (`118` LOC). Five abstract methods: `select_actions`, `compute_intrinsic_rewards`, `update`, `checkpoint_state`, `load_state`. All current strategies implement them, but the runtime path bypasses `update()` and calls `rnd.update_predictor()` directly (see cross-cutting).

- **`action_selection.py`** (`93` LOC). One pure function: `epsilon_greedy_action_selection(q_values, epsilons, action_masks)`. Handles three subtle cases that show up in the codebase: (1) BUG-23 — rows where every action is masked invalid, falls back to argmax over unmasked Q (`:46–62`); (2) vectorised valid-action sampling via `torch.multinomial` instead of a Python loop (`:65–77`); (3) per-agent epsilons via `torch.rand(batch) < epsilons` (`:88`).

### Detailed walk: what `step_population` actually invokes on each strategy

For all three strategies, per env step, the population calls exactly two methods on the strategy: `select_actions` (always)
and `compute_intrinsic_rewards` (conditional on `isinstance(..., RNDExploration | AdaptiveIntrinsicExploration)`). It does
**not** call `update` (the ABC declares it but the population uses `rnd.update_predictor()` directly instead — see cross-
cutting). It calls `update_on_episode_end` *only* on `AdaptiveIntrinsicExploration` (gated by `isinstance`, `:512–513`).

For `EpsilonGreedyExploration`:
- `select_actions` → `epsilon_greedy_action_selection(q_values, agent_states.epsilons, action_masks)`. The per-agent
  `epsilons` come from `agent_states`, which is the transient state object populated at `vectorized.py:650–659` with
  `self.current_epsilons`. `self.current_epsilons` is a `torch.full((num_agents,), <scalar ε from strategy>, ...)` written
  by `sync_exploration_metrics` (`:488–506`). So even though each agent could in principle have its own ε, the present
  driver writes a single global scalar across the batch.
- `compute_intrinsic_rewards` returns zeros; the population's `isinstance` gate at `:699` makes sure this method isn't
  even called for the plain ε-greedy strategy.

For `RNDExploration`:
- `select_actions` is the same shared function as the ε-greedy strategy. The two strategies are interchangeable for the
  *action* side.
- `compute_intrinsic_rewards` returns `mse_per_sample / (sqrt(reward_rms.var) + 1e-8)` (`rnd.py:219`). The population calls
  this with `update_stats=False` because the env's DAC engine already did the in-loop stats update during reward
  composition (see comment at `vectorized.py:697`). This is fragile — there are now two call sites of `RNDExploration`
  novelty per step (env's reward composition and population's logging), and only the env's is supposed to update stats.
- The predictor is trained from `update_predictor()` invoked at `vectorized.py:750`. Stats updates and predictor updates
  are decoupled — predictor sees `obs_buffer`, RMS sees the in-flight MSE per sample.

For `AdaptiveIntrinsicExploration`:
- All three of the methods above delegate to the wrapped `RNDExploration` (`adaptive_intrinsic.py:103`, `:124`, `:132`).
- The unique surface is `update_on_episode_end(survival_time)` (`:134`) and `get_intrinsic_weight()` (`:187`). The
  population calls the former in `_finalize_episode` (`vectorized.py:512–513`) and the latter in
  `_get_current_intrinsic_weight_value` (`:455–458`). The intrinsic weight scalar is written into the runtime registry
  per-agent (identical across agents in current code) so the env can pick it up during reward composition.
- Crucial: `compute_intrinsic_rewards` at `adaptive_intrinsic.py:105–124` deliberately does **not** multiply by
  `current_intrinsic_weight`. The docstring at `:112` calls this out — "Weight is applied in replay buffer sampling, NOT
  here. This prevents double-weighting bug." In the post-DAC world, "replay buffer sampling" is no longer where the
  weight is applied; the env's DAC engine applies it. The docstring is now misleading but the behaviour is correct (the
  weight is applied exactly once, in the env).

### Common interface

Yes: `ExplorationStrategy` (ABC at `base.py:16`) with 5 abstract methods listed above. `EpsilonGreedyExploration`, `RNDExploration`, and `AdaptiveIntrinsicExploration` all implement it; `AdaptiveIntrinsicExploration` reuses `RNDExploration` by composition. The population code does `isinstance(self.exploration, RNDExploration | AdaptiveIntrinsicExploration)` to decide whether to update an RND predictor (`vectorized.py:699`, `:744`) — i.e. the interface is informally widened by `isinstance` checks for RND-family novelty support.

### Dependencies

- **Inbound:** `population/vectorized.py` (constructs and drives the strategy; type-tests RND-vs-non-RND).
- **Outbound:** `torch`, `numpy`, `townlet.training.state.BatchedAgentState`. No environment dependency — exploration sees only `q_values`, `agent_states`, and `action_masks` on the action path, and `observations` on the novelty path.

---

## Subsystem 5: `curriculum/`

### Strategies

- **`static.py` — `StaticCurriculum`** (`126` LOC). Returns the same `CurriculumDecision` to every agent every call. Stores `difficulty_level`, `reward_mode`, `active_meters`, `depletion_multiplier` (`:42–45`). Maintains a tiny `_StaticTracker` (`:117`) purely so the population's logging path can read `tracker.agent_stages` without special-casing.

- **`adversarial.py` — `AdversarialCurriculum`** (`531` LOC). The substantive curriculum.
  - **5 hard-coded stages** (`STAGE_CONFIGS` at `:28`): stage 1 (energy+hygiene, 0.2× depletion, shaped) → stage 4 (all 6 meters, 1.0× depletion, shaped) → stage 5 (all meters, 1.0×, **sparse rewards**, "graduation"). The `active_meters` and `depletion_multiplier` per stage are wired here, not in YAML.
  - **`PerformanceTracker`** (`:67`) owns 7 per-agent tensors: `episode_rewards`, `episode_steps`, `prev_avg_reward`, `last_survival_rate`, `agent_stages`, `steps_at_stage`, `episodes_at_stage`. `update_step(rewards, dones)` is called from `VectorizedPopulation.update_curriculum_tracker` (`vectorized.py:1049–1052`). Note the docstring at `adversarial.py:88` flags that **the "rewards" parameter is actually survival-step counts**, not rewards — caller-side abuse.
  - **Advance criteria** (`_should_advance`, `:239`): `stage < 5` and `steps_at_stage ≥ min_steps_at_stage` and `survival_rate > 0.7` and `learning_progress > 0` and `entropy < 0.5`.
  - **Retreat criteria** (`_should_retreat`, `:267`): `stage > 1` and `steps_at_stage ≥ min_steps_at_stage` and (`survival_rate < 0.3` OR `learning_progress < 0`). Retreat takes priority over advance (`:322`).
  - **Entropy from Q-values** (`_calculate_action_entropy`, `:428`): softmax over Q, then `-Σ p log p`, normalised by `log(num_actions)`. Returned in `[0,1]`.
  - **Mapping stage→difficulty_level** (`:358–369`): base `(stage-1)/4.0`, then linearly remapped into the optional `[difficulty_min, difficulty_max]` band from `TrainingV2Config.curriculum.adversarial`.
  - **Telemetry**: every transition pushes a structured dict to `self.transition_events` (`:399`) with `agent_id`, `from_stage`, `to_stage`, `reason`, `survival_rate`, `learning_progress`, `entropy`, `steps_at_stage`.
  - **YAML loader** (`from_yaml` at `:194`). Still present, but `factory.build_curriculum` (`factory.py:22`) is the v2.1 path and `from_yaml` is unused by SG6's call chain.

### Detailed walk: the adversarial step

Per env step:

1. `step_population` constructs the transient `BatchedAgentState` and forwards Q-values into
   `get_batch_decisions_with_qvalues` (`vectorized.py:664–668`, `adversarial.py:294`).
2. Inside, `_calculate_action_entropy` (`:428`) softmaxes Q over actions, computes Shannon entropy, normalises by
   `log(num_actions)` to put it in `[0,1]`.
3. For each agent index `i`:
   - `_should_retreat(i)` is checked first (`:322`). If true, `agent_stages[i] -= 1`, `steps_at_stage[i] = 0`,
     `episodes_at_stage[i] = 0`, and `prev_avg_reward[i]` is updated to the current agent's running average.
   - Otherwise `_should_advance(i, entropy)` is checked (`:331`). Same shape of updates, in the other direction.
   - The current stage's hardcoded `STAGE_CONFIGS[stage-1]` is read for `active_meters`, `depletion_multiplier`, `reward_mode`.
   - Difficulty is mapped `(stage-1)/4.0` → optional `[min, max]` band.
   - A `CurriculumDecision` is constructed.
   - If a transition fired, a structured event dict is appended to `transition_events`.

Two important facts about the call surface:

- The "rewards" parameter to `PerformanceTracker.update_step` is *survival step counts*, not rewards (docstring at
  `adversarial.py:88`). The caller in `vectorized.py:1049–1052` does `tracker.update_step(rewards, dones)` after passing
  what should be `env.step_counts.clone()` — needs a runtime check to confirm.
- `update_step` runs every env step, not every episode. It does its own per-step bookkeeping (incrementing
  `episode_steps`, `steps_at_stage`) and a per-done baseline update.

### Common interface

`CurriculumManager` ABC at `base.py:14`. Three abstract methods: `get_batch_decisions`, `checkpoint_state`, `load_state`. The
adversarial curriculum **also** exposes `get_batch_decisions_with_qvalues` (not on the ABC, see `adversarial.py:294`).
Population calls the wider method if available via `hasattr(self.curriculum, "get_batch_decisions_with_qvalues")`
(`vectorized.py:662`) — a duck-typed extension point.

`base.py` exposes an optional `initialize_population(num_agents)` hook with a no-op default (`base.py:22–28`); `AdversarialCurriculum` overrides it to build a `PerformanceTracker` (`adversarial.py:222–225`), and `StaticCurriculum` overrides it to set up its `_StaticTracker` (`static.py:50–54`).

`factory.py` selects between the two implementations based on `TrainingV2Config.curriculum.strategy ∈ {"static", "adversarial"}` (`factory.py:48–70`). Anything else raises.

### Dependencies

- **Inbound:** `population/vectorized.py` constructs whichever curriculum the factory returns and calls into it once per step (decision) and once per env step (`update_curriculum_tracker`, `vectorized.py:1049`).
- **Outbound:** `torch`, `yaml` (in `adversarial.from_yaml` only), `pydantic`, `townlet.training.state.{BatchedAgentState, CurriculumDecision}`, and `townlet.config.training_v2_config.TrainingV2Config` (factory only).

---

## Cross-cutting observations

**Composition (who calls whom).** The flow is:

```
scripts/run_demo.py
  └── VectorizedPopulation                       (population/vectorized.py:42)
        ├── env: VectorizedHamletEnv             (out of SG6 scope)
        ├── curriculum: CurriculumManager        (built by curriculum.factory.build_curriculum)
        │     └── PerformanceTracker             (adversarial only)
        ├── exploration: ExplorationStrategy     (Eps / RND / AdaptiveIntrinsic)
        │     └── RNDExploration                 (owned by composition in Adaptive)
        ├── q_network, target_network            (built via agent.NetworkFactory)
        ├── optimizer, scheduler                 (built via agent.OptimizerFactory)
        ├── loss_fn                              (built via agent.LossFactory)
        ├── replay_buffer:
        │     ReplayBuffer                       (feed-forward, prioritized=False)
        │     | PrioritizedReplayBuffer          (feed-forward, prioritized=True)
        │     | SequentialReplayBuffer           (recurrent — PER not supported)
        ├── tb_logger: TensorBoardLogger | None
        └── runtime_registry: AgentRuntimeRegistry  (attached to env so reward code can read it)
```

The orchestrator of the training loop is exclusively `VectorizedPopulation.step_population` — no other module in SG6 calls
out into multiple subsystems at once. There is no separate "Trainer" / "Learner" class. The env owns reward composition
(DAC); the population owns Q-learning. Curriculum and exploration are pure callables consulted by the population.

**Where the `is_recurrent` branch lives.** It is *only* in `population/vectorized.py` (`:151`, `:170–175`, `:207–218`, `:258–260`, `:400`, `:430–433`, `:641–647`, `:721–730`, `:758`, `:763–898`, `:1003–1004`). The recurrent network's hidden-state lifecycle (per-rollout vs per-batch vs per-episode resets) is owned by the population class, not the network class — the network only provides primitive `get/set/reset_hidden_state`.

**Reward composition is provenance, not active math, in this layer.** The DAC engine in the environment composes
`extrinsic + (intrinsic × weight × modifiers) + shaping` *before* anything in SG6 sees a number. Replay buffers, episode
containers, and the `RewardTensor` DTO all carry the components alongside the composed total purely for logging /
TensorBoard / debugging. Subsystem 2's `_log_reward_components` (`vectorized.py:302–333`) is the lone consumer of those
component channels.

**Exploration↔curriculum coupling is one-directional.** Exploration never reads curriculum state; curriculum sometimes
reads Q-values (entropy) but never reads exploration state. The coupling site is `_finalize_episode` (`vectorized.py:508–519`),
which calls `AdaptiveIntrinsicExploration.update_on_episode_end(survival_time)` after the curriculum-driven stage logic has
already happened.

**The "runtime registry" is the back-channel.** `AgentRuntimeRegistry` (`population/runtime_registry.py:40`) is the place
where survival time, curriculum stage, epsilon, and intrinsic weight live as GPU tensors of shape `[num_agents]`. It is
attached to the env at construction time (`vectorized.py:128`). Reward-side code in the env can read these tensors *while
composing rewards* without having to reach back into the population. The registry is what closes the loop from
"curriculum decides stage" → "stage shapes reward" without forcing a strict callback through the population. It is
read by the population from `_get_current_*` methods (`vectorized.py:447–459`) and written by `_sync_curriculum_metrics`
(`:461`) and `sync_exploration_metrics` (`:488`).

**Action masking pipeline.** Action masks come from `envs.get_action_masks()` (`vectorized.py:680`). The population does
not own masking logic; it just forwards the mask into the exploration strategy's `select_actions`. The shared utility
in `action_selection.epsilon_greedy_action_selection` handles all corner cases (all-invalid rows, vectorised valid sampling)
in one place — so all three strategies that use ε-greedy on top of Q-values share consistent masking semantics.

**Where action_dim is sourced.** `action_dim` is passed into `VectorizedPopulation.__init__` as an explicit argument
(`vectorized.py:63`, `:124`). The brain's `q_network` and `target_network` both honour it. The checkpoint records it
under `universe_metadata.action_dim` (`:1120`). `assert_checkpoint_dimensions` cross-checks against
`universe.metadata.action_count` (`checkpoint_utils.py:82–84`), giving a hard refusal when an action vocabulary changes
between training and resume. This is the mechanism that supports CLAUDE.md's "global vocabulary enables checkpoint
transfer" claim — the size of the action head is part of the checkpoint identity, and the universe-compiler-side action
vocabulary is identity-checked on resume.

**DAC vs Q-learning rewards: one-way street.** The environment's DAC engine produces a single composed total per agent
per step. SG6 stores that total plus its components for *provenance* (training and TensorBoard), but Q-learning targets
are built only from the composed total (`vectorized.py:927` / `:816` / `:836`). There is no mechanism in SG6 to retrain
on a different reward composition without rerunning the env. This is intentional — the `drive_hash` check
(`checkpoint_utils.py:99–109`) explicitly forbids resuming a checkpoint against a different DAC config.

**Hot-path performance budget.** A best-effort list of every CPU↔GPU sync that happens per env step in `step_population`:
- `info["q_values"] = [q_values[i].cpu().tolist() for i in range(self.num_agents)]` (`:1015`) — per-agent CPU tolist.
- Recurrent episode append `obs[i].cpu(), actions[i].cpu(), rewards[i].cpu(), ...` (`:723–730`) — per-agent CPU clone, six tensors each.
- RND obs buffer append `self.current_obs[i].cpu()` (`:748`) — per-agent CPU clone.
- Within training (every `train_frequency` step): TD-error and Q-mean `.item()` calls into `last_td_error` / `last_loss` / `last_q_values_mean` (`:951–953`).

The recurrent path's per-step `.cpu()` calls for episode storage are the largest cost; they happen *every* step (not gated
by `train_frequency`). For `num_agents` modest (1–8) this is acceptable. The feed-forward path is much cheaner because
the replay-buffer push stays on-device end-to-end (`replay_buffer.py:118–177`).

---

## Concerns (per file, prioritised by impact)

**`agent/networks.py`**
- `StructuredQNetwork` (`:558`) is implemented and tested (`tests/test_townlet/unit/agent/test_structured_qnetwork.py`) but no factory builder exists and `_build_network` in the population class would reject `architecture.type == "structured"` (`vectorized.py:395`). Either the network is dead code or the factory is incomplete.
- `RecurrentSpatialQNetwork` docstring at `:62` ("224", "192") is out of date — the actual LSTM input dim with temporal features is `128 + position(32) + meters(32) + affordance(32) + temporal(16) = 240`.
- The `try/except Exception: self._use_observation_spec = False` at `networks.py:204–205` is a defensive swallow that contradicts the strict raise at `:228`. If the spec parse fails silently at construction, the forward call will raise opaquely on first inference. Suggest reraising in `__init__`.

**`agent/network_factory.py`**
- `build_recurrent` (`:72`) acknowledges in its docstring (`:99–104`) that `RecurrentSpatialQNetwork` is **not** fully config-driven — only `lstm.hidden_size` is honoured; CNN, position, meter, affordance, temporal, and Q-head dims are all hardcoded inside the network class. The BAC contract is half-finished.
- `enable_temporal_features=False` is hardwired at `:131` with comment "Will be determined by environment" — and indeed, `vectorized.py:170–175` mutates this attribute on the network *after* construction. This is a leaky abstraction that future refactors will trip over.

**`population/vectorized.py`**
- Only `decisions[0].depletion_multiplier` is passed to the env (`:686–693`). With per-agent curriculum advancement, agents on different stages still share one global env difficulty knob. Either intentional (all agents share one env config) or a latent bug; comment says "Extract curriculum difficulty multiplier" with no per-agent context.
- `update_curriculum_tracker` (`:1049–1052`) passes `rewards` but the tracker treats it as `survival_steps` (see `adversarial.py:88` "rewards here are actually survival_steps, not rewards"). This parameter-name lie is a maintenance hazard.
- `get_checkpoint()` (`:1068`) returns curriculum state under `curriculum_states={"global": ...}` but the heavy `get_checkpoint_state()` (`:1085`) does **not** include curriculum state at all. Two checkpoint surfaces with non-overlapping coverage of curriculum tracker tensors. On `load_checkpoint_state` (`:1133`), the adversarial curriculum's `agent_stages`, `steps_at_stage`, etc. will not be restored unless the caller separately threads `PopulationCheckpoint` through. This is a real bug surface for resume-from-checkpoint with adversarial curriculum.
- Line 1015: `info["q_values"] = [q_values[i].cpu().tolist() for i in range(self.num_agents)]` does a CPU sync every step purely to record Q-values into the info dict for downstream telemetry. Acceptable, but worth knowing it is in the hot path.
- The dual-path `replay_buffer: ReplayBuffer | SequentialReplayBuffer | PrioritizedReplayBuffer` union forces nine `# type: ignore` comments and four `cast()`s. A small Protocol would clean this up.

**`training/replay_buffer.py` / `prioritized_replay_buffer.py`**
- Comment in `replay_buffer.py:79` calls out the buffer-corruption guard but does not validate that `batch_size > 0`. A zero-batch push would no-op but advance `position` by zero, which is fine; still worth an explicit check for symmetry with the PER buffer (`prioritized_replay_buffer.py:161`).
- PER `sample` is O(n) (`prioritized_replay_buffer.py:170–177`). For typical replay capacities (~1M) this is the dominant cost of training. The TODO at `:149` is correct: a sum-tree is needed for scale.

**`training/sequential_replay_buffer.py`**
- Length-weighted episode sampling at `:228–232` is correct in expectation but uses `random.choices` per sequence (Python-level) — not GPU-accelerated. Acceptable because this is the `train_frequency`-gated path, but it does serialise CPU↔GPU more than the feed-forward path.

**`exploration/epsilon_greedy.py` / `rnd.py` / `adaptive_intrinsic.py`**
- `EpsilonGreedyExploration.decay_epsilon()` (`epsilon_greedy.py:92`) and `RNDExploration.decay_epsilon()` (`rnd.py:302`) are never called by the population. The population reads `self.exploration.epsilon` (`vectorized.py:447–453`) but never schedules a decay. So the configured `epsilon_decay`/`epsilon_min` knobs are inert unless something *outside* SG6 calls `decay_epsilon()`. **(High-impact concern if true; warrants a grep over the wider repo to confirm.)**
- `RNDExploration.update_predictor()` (`rnd.py:242`) drops samples *past* `training_batch_size` only after the first batch is consumed; the buffer is a flat Python list, so insertion is O(1) but `obs_buffer = obs_buffer[batch:]` (`:257`) is O(n) and reallocates the list each train tick. A `collections.deque(maxlen=...)` would be more honest.
- `AdaptiveIntrinsicExploration.load_state` (`adaptive_intrinsic.py:213`) restores `min_survival_for_annealing` from the product of two restored fields (`:227`), but the comparison at runtime is `mean_survival > self.min_survival_for_annealing` (`:180`). If the user changes `max_episode_length` between runs but the checkpoint pins the old `min_survival_fraction × old_max`, the annealing threshold will be the *checkpoint's* number, not the live config's. Whether this is desired or not is a design question.

**`curriculum/adversarial.py`**
- "rewards" parameter actually carries step counts (`:88`). Rename or document at the caller side too.
- `STAGE_CONFIGS` (`:28`) is a module-level Python constant. The set of active meters per stage is impossible to override from YAML — `configure_from_training` (`:168`) only adjusts thresholds and the difficulty band. So "stage 3 adds money" is hardwired regardless of the substrate's actual meters.
- Retreat-on-negative-learning-progress (`:289–292`) uses an unsmoothed `current_avg - prev_avg`. With noisy short episodes this can trigger spurious retreats unless `min_steps_at_stage` is conservative.
- `load_state` (`:466`) assumes `initialize_population` was called first and **does not** raise if `episodes_at_stage` is missing from the state dict (it isn't in `checkpoint_state` at all — `:453–464`). Resume will silently reset all `episodes_at_stage` to zero.

**`curriculum/static.py`**
- `active_meters` default at `:44` is the legacy 6-meter set. With VFS-driven configurable meter sets this risks falling out of step with the actual universe; suggest defaulting to "all meters from substrate" via the factory.

**Test inventory in full (filenames only, per brief).**

```
tests/test_townlet/unit/agent/
  test_brain_config.py
  test_loss_factory.py
  test_network_factory.py
  test_network_selection.py
  test_networks.py
  test_optimizer_factory.py
  test_set_encoder_qnetwork.py
  test_structured_qnetwork.py

tests/test_townlet/unit/population/
  test_action_selection.py
  test_double_dqn_algorithm.py
  test_recurrent_training.py
  test_runtime_registry.py
  test_vectorized_population.py

tests/test_townlet/unit/training/
  test_checkpoint_utils.py
  test_prioritized_replay_buffer.py
  test_prioritized_replay_buffer_components.py
  test_replay_buffer_components.py
  test_replay_buffers.py
  test_sequential_replay_buffer.py
  test_state.py
  test_tensorboard_logger.py

tests/test_townlet/unit/exploration/
  test_epsilon_greedy_selection.py
  test_exploration_strategies.py
  test_rnd_masking.py
  test_rnd_normalization.py
  test_rnd_stats_update_timing.py

tests/test_townlet/unit/curriculum/
  test_curriculums.py
```

The agent and training subsystems are heavily tested. Population has a dedicated double-DQN test (which is reassuring
given the multiple branches in `step_population`), plus a recurrent-training test (which exercises the heaviest code
path in the entire SG6 surface). Exploration is unusually well-tested *for what it does* — three test files
specifically about RND masking, normalisation, and the timing of stats updates speaks to historical pain in exactly
the area I flagged at `vectorized.py:697` (two consumers of `compute_intrinsic_rewards` with different `update_stats`
needs). Curriculum is the thinnest: a single file for what is the most stateful, branching code in SG6
(`adversarial.py` is 531 LOC with 28 methods/functions).

**Test coverage signals.** The test inventory looks proportionate to the code:
- agent: 7 test files (covers networks, factories, brain config, set-encoder, structured) — supports above concern that `StructuredQNetwork` is exercised even though it isn't reachable through the factory.
- population: 5 test files including `test_double_dqn_algorithm.py` and `test_recurrent_training.py`.
- training: 8 test files including separate component-level files for each replay buffer.
- exploration: 5 test files specifically covering `rnd_masking`, `rnd_normalization`, `rnd_stats_update_timing`, `epsilon_greedy_selection`.
- curriculum: 1 test file (`test_curriculums.py`). **Light** given that `adversarial.py` is 531 LOC with non-trivial control flow (advance/retreat priority, transition events, difficulty mapping). Worth a deeper look outside SG6's scope.

No legacy/deprecated symbols visible in the SG6 surface; the file headers carry "CRIT-07", "POP-XXX", "PDR-002" tags that look like recent invariant-tightening, not deprecation cruft.

---

## A note on `__init__.py` files

All five subsystems' `__init__.py` files are 1-line docstring stubs:

```
src/townlet/agent/__init__.py:        "Agent networks for townlet."
src/townlet/population/__init__.py:   "Townlet: GPU-native sparse reward system."
src/townlet/training/__init__.py:     "Townlet: GPU-native sparse reward system."
src/townlet/exploration/__init__.py:  "Townlet: GPU-native sparse reward system."
src/townlet/curriculum/__init__.py:   "Townlet: GPU-native sparse reward system."
```

None of them curates a public API via `__all__` or re-exports. Consumers must import from the concrete module (e.g.
`from townlet.training.replay_buffer import ReplayBuffer`, not `from townlet.training import ReplayBuffer`). The
`vectorized.py` import block at lines 18–32 is the de-facto consumer-facing surface, and it imports the concrete files
in exactly that pattern. Whether to formalise public APIs in `__init__.py` is a style call; the current convention is
"there is no public API, only modules".

## Open questions

1. **Who, if anyone, calls `decay_epsilon()` on the exploration strategies?** Nothing in SG6 does. If nothing outside SG6 does either, the entire epsilon schedule is dead and current effective epsilon equals `epsilon_start` for the whole run. (Needs a `grep -rn "decay_epsilon\|\.epsilon_decay\b" src/townlet` outside this scope.)
2. **Where is `update_curriculum_tracker` actually called from?** Defined at `vectorized.py:1049` but I did not see it invoked inside `step_population`. If the driver script doesn't call it, the adversarial curriculum's `PerformanceTracker` never advances `steps_at_stage` or `episodes_at_stage` and stage advancement is effectively frozen. (SG6 scope can't answer this; needs SG of demo/driver.)
3. **What guarantees a `dones`-true transition makes it into the recurrent replay buffer with the terminal step included?** The episode flush at `_store_episode_and_reset` (`:398`) runs *before* `_finalize_episode`, but the per-step append at `:723–730` happens before the env's `dones` are observed in the same step. I think the terminal step is included because the append uses pre-step `current_obs` and post-step `actions`/`rewards`/`dones`, but a unit-test trace would settle it.
4. **Curriculum checkpointing.** Does `PopulationCheckpoint.curriculum_states` actually round-trip the per-agent stage tensors? The Pydantic field allows `dict[str, dict[str, Any]]` (`state.py:204`), and adversarial's `checkpoint_state` returns CPU tensors (`adversarial.py:458–464`), but tensors are not JSON-safe. Either there is a torch-aware serialisation step downstream (out of scope) or this is broken on serialisation.
5. **`max_episode_length` for `AdaptiveIntrinsicExploration`.** The default of 500 (`adaptive_intrinsic.py:31`) hardcodes a number that arguably should always come from the curriculum/env. Is the factory that builds this strategy plumbing the env's real max-steps in, or is the default leaking?
