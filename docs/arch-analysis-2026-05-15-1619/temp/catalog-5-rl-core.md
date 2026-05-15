## RL Core (agent + population + training + exploration)

**Location:** `src/townlet/agent/`, `src/townlet/population/`, `src/townlet/training/`, `src/townlet/exploration/`

**Responsibility:** Coordinate batched DQN training (vanilla/double) with intrinsic exploration (RND, adaptive), manage GPU-resident replay buffers, and orchestrate vectorized population dynamics.

**Internal Structure:**
- `agent/` — Q-network architectures and factories (networks, losses, optimizers)
- `population/` — VectorizedPopulation (batched training loop), AgentRuntimeRegistry (per-agent state)
- `training/` — TrainingState, ReplayBuffer, sequential/prioritized variants
- `exploration/` — RND, epsilon-greedy, adaptive intrinsic weighting

---

### Agent / Networks

**Networks** (`networks.py`):
- `SimpleQNetwork` — MLP [obs_dim → hidden_dim → hidden_dim → action_dim], LayerNorm at each hidden layer
- `RecurrentSpatialQNetwork` — LSTM-based POMDP agent: vision CNN (25-dim local window → 128), position encoder (conditional on position_dim), meter encoder (8 meters → 32), affordance encoder (15 types + none → 32), temporal encoder (4 features → 16), LSTM (224-dim input → 256 hidden), Q-head (256 → 128 → action_dim). Handles episode-boundary hidden-state resets via `reset_hidden_state()`.
- `DuelingQNetwork` — Dueling decomposition (Wang et al. 2016): shared feature extraction → value stream (V) + advantage stream (A), aggregation via Q = V + (A - mean(A))
- `StructuredQNetwork` — Group encoders for semantic observation groups (spatial, bars, affordances, temporal, custom), drives inductive bias vs. SimpleQNetwork

**Factories** (`network_factory.py`, `loss_factory.py`, `optimizer_factory.py`):
- **NetworkFactory**: `build_feedforward()` (MLP from config), `build_recurrent()` (RecurrentSpatialQNetwork from config)
- **LossFactory**: MSE, Huber (configurable delta), SmoothL1 — all driven by BrainConfig
- **OptimizerFactory**: Adam/AdamW with betas, eps, weight decay + optional LR scheduler (StepLR, ExponentialLR, CosineAnnealingLR)
- **Factory Pattern Discipline**: All parameters explicitly specified via config DTOs (FeedforwardConfig, RecurrentConfig, LossConfig, OptimizerConfig) — **no defaults, no BAC** (per PDR-002)

---

### Population

**VectorizedPopulation** (`vectorized.py`):
- **Batched Architecture**: All `num_agents` agents share a single Q-network (not one-per-agent). Tensors vectorized: [batch_size, ...] for observations, actions, rewards, etc.
- **Runtime Registry** (`AgentRuntimeRegistry`): Per-agent tensors for curriculum_stage, survival_time, epsilon, intrinsic_weight. Provides JSON-safe snapshots (`AgentTelemetrySnapshot`) for inference/telemetry.
- **Replay Buffer Wiring**: Recurrent agents use SequentialReplayBuffer (episode-level storage); feedforward agents use ReplayBuffer or PrioritizedReplayBuffer (config-driven, TASK-005 Phase 3). PER not yet supported for recurrent (raises NotImplementedError).
- **Target Network**: Separate target network (frozen in eval mode), updated every `target_update_frequency` steps. Vanilla DQN vs Double DQN driven by `brain_config.q_learning.use_double_dqn`.
- **Episode Container**: Tracks per-agent transitions during rollout (obs, action, reward, next_obs, done); batched push to replay buffer every `train_frequency` steps.

**Population Manager Protocol** (`base.py`):
- Abstract interface: `step_population()` (GPU hot path) and `get_checkpoint()` (cold path)
- Responsible for action selection, environment stepping, reward aggregation, buffer updates, network training

---

### Training

**TrainingState** (`state.py`):
- **RewardTensor DTO**: Hot-path composition semantics — explicit separation of total reward (always present) from optional extrinsic/intrinsic/shaping components. `is_composed=True` for DAC-composed rewards (production), `is_composed=False` for legacy component-based rewards. Eliminates misleading "zeros in intrinsic" pattern (CRIT-07).
- **Batched State**: Episode step counters, survival times, curriculum decisions, depletion multiplier (curriculum difficulty)
- **Other DTOs**: PopulationCheckpoint (network weights, curriculum states, metrics), CurriculumDecision (stage decision payload)

**Replay Buffer** (`replay_buffer.py`, `sequential_replay_buffer.py`, `prioritized_replay_buffer.py`):
- **Standard ReplayBuffer**: Circular [capacity] buffer storing (obs, action, reward_total, next_obs, done). GPU-resident. Detects full wrap via `has_wrapped` flag (for HIGH-04 serialization).
- **SequentialReplayBuffer**: Stores episode-level sequences [batch_size, seq_len, obs_dim] for LSTM training. Maintains episode boundaries.
- **PrioritizedReplayBuffer**: Alpha-based priority weighting (TASK-005 Phase 3). Beta annealing from `brain_config.replay.priority_beta_annealing`. Pydantic validator ensures PER params present when prioritized=True.
- **Reward Composition**: Buffers store pre-composed totals from RewardTensor (not separate extrinsic/intrinsic splits). DAC handles composition upstream.

---

### Exploration

**RND** (`rnd.py`):
- **RNDExploration**: Random Network Distillation — target network (frozen), predictor network (trained). Prediction error = novelty signal. Active mask support for padding dimension masking.
- **Running Mean/Std**: Welford's online algorithm for numerical stability (OpenAI/CleanRL pattern)
- **RNDNetwork**: 3-layer MLP [obs_dim → 256 → 128 → embed_dim], architecture mirrors SimpleQNetwork for consistency

**Adaptive Intrinsic** (`adaptive_intrinsic.py`):
- **Composition**: Contains RNDExploration instance; wraps intrinsic reward computation with variance-based annealing
- **Annealing Logic**: Tracks survival time history (window=100 episodes). When variance drops below `variance_threshold` (config: 100.0, increased from 10.0 to prevent premature annealing per comment) AND survival time > `min_survival_fraction * max_episode_length` (prevents "stable failure"), decay intrinsic weight by `decay_rate` (default 0.99)
- **Weight Floor**: `min_intrinsic_weight` (default 0.0)
- **Action Masking**: Epsilon-greedy delegation with optional action validity masks [batch, num_actions]

**Epsilon-Greedy** (`epsilon_greedy.py`):
- **Vanilla Baseline**: Epsilon probability random, 1-epsilon probability argmax. No intrinsic motivation (returns zero tensor).
- **Decay Schedule**: Exponential `epsilon *= epsilon_decay` per episode, floor at `epsilon_min`
- **Action Masking**: Supported via `action_selection.py` shared utility

**Action Selection Utility** (`action_selection.py`):
- `epsilon_greedy_action_selection()` — vectorized [batch, num_actions] → [batch] actions, with optional action masking (boundary constraints)

---

### Q-Learning Variants

**Double DQN vs Vanilla DQN**:
- **Plumbing**: `brain_config.q_learning.use_double_dqn` boolean flag
- **Feedforward Path** (lines ~900): Double DQN selects actions via online network, evaluates via target network
- **Recurrent Path** (lines 780-809): Double DQN unrolls online network to select next_actions per timestep, then evaluates with target network (two separate unrolls to maintain hidden state). Vanilla DQN uses only target network for both.
- **Target Network Update**: Standard Bellman with gamma discount, no next-state Q-values for terminal states (dones tensor masks)

---

### Dependencies

**Inbound**:
- `src/townlet/demo/runner.py` — DemoRunner instantiates VectorizedPopulation, checkpoint loading
- `scripts/run_demo.py` — Entry point, config loading, training loop orchestration

**Outbound**:
- `environment/vectorized_env.py` — VectorizedHamletEnv interface (observation_spec, step, attach_runtime_registry, set_exploration_module)
- `curriculum/` — CurriculumManager for difficulty progression
- `config/brain_config.py`, `config/training_v2_config.py` — Pydantic config DTOs
- `torch` — PyTorch (networks, optimization, tensor ops)

---

### Patterns Observed

- **Factory Pattern**: NetworkFactory, LossFactory, OptimizerFactory all follow declarative config-driven architecture (no hardcoded defaults)
- **Vectorized Batch Operations**: All Q-learning updates operate on [batch, ...] tensors on GPU — no per-agent loops
- **DTO Composition for Rewards**: RewardTensor separates composition intent (is_composed flag) from component storage
- **Episode-Boundary State Management**: LSTM hidden state reset at episode start (reset_hidden_state) — cascaded to all recurrent agents in batch
- **Cold/Hot Path Separation**: Checkpoint loading (Pydantic, disk I/O) vs. training loop (GPU tensors, no validation)

---

### Concerns

1. **Gradient Clipping Configuration** (max_grad_norm=10.0): Currently config-driven via `TrainingLoopConfig.max_grad_norm`. Plumbed into VectorizedPopulation.__init__, applied during `_train_on_batch()`. Confirm applied to optimizer before step() — not a concern, standard practice.

2. **Adaptive Annealing Threshold** (variance_threshold=100.0): Increased from 10.0 per comment in adaptive_intrinsic.py line 29 to prevent premature annealing. Config-driven, not hardcoded. Ensure this threshold sensible across curriculum difficulty ranges (L0 vs L3). Consider sensitivity analysis if survival variance patterns change.

3. **LSTM Hidden-State Episode Resets**: Reset occurs via `reset_hidden_state(batch_size, device)` at episode boundaries. Verify this is called on BOTH q_network and target_network in recurrent path (lines 778, 783). Code appears correct — reset happens before each sequence unroll.

4. **PER Beta Annealing Not Fully Integrated**: TASK-005 Phase 3 partial implementation. PrioritizedReplayBuffer accepts `priority_beta_annealing` config, but unclear if annealing schedule is actually applied during sampling. Check `sample()` method implementation.

5. **Double DQN Hidden-State Synchronization** (Recurrent Path): Lines 783-790 reset online network, then unroll twice (once for action selection, once for evaluation). Verify hidden state doesn't diverge between these two unrolls — should be fine (independent LSTM forward passes), but check if temporal coupling between selections matters for correctness.

6. **Active Mask in RND**: RNDNetwork registers `active_mask` buffer (line 91). Verify this mask is actually applied in forward pass — code shows initialization but not application. Low priority (masking padding dims), but could silently include noise if mask unused.

---

### Confidence

**HIGH** — All four packages tightly integrated, well-documented with PDR/TASK labels. Factories enforce no-defaults discipline (PDR-002). Population vectorization is clear (shared single Q-network). Exploration composition (RND → AdaptiveIntrinsic) is compositional and testable. Q-learning paths (vanilla vs Double) plumbed into config. Minor hygiene issues flagged (PER beta annealing, active mask application) but no structural bugs detected. Code aligns with CLAUDE.md pedagogical goals (interesting failures like "Low Energy Delirium" are encouraged, not bugs).
