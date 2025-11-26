# Subsystem Catalog - Townlet Architecture

**Analysis Date**: 2025-11-24 00:45
**Total Subsystems**: 16 across 5 architectural groups

---

## Group 1: Core Training

**Purpose**: Core training loop components - environment execution, population management, neural networks, and training infrastructure

**Subsystems**: environment, population, agent, training

### Subsystem 1: environment

**Name**: environment
**Location**: src/townlet/environment/
**Primary Responsibility**: GPU-native vectorized environment execution orchestrating all agent interactions, meter dynamics, affordances, rewards (DAC), and game mechanics (effects/items) in batch mode.

#### Key Components

- **vectorized_env.py** (`VectorizedHamletEnv`): Main environment class implementing Gymnasium-style interface for batched execution. Orchestrates substrate, meters, affordances, DAC, VFS, effects, and items. Manages [num_agents, ...] tensor operations on GPU.

- **affordance_engine.py** (`AffordanceEngine`): Config-driven affordance interaction processor. Pre-compiles Effects commands at startup, processes instant/multi-tick interactions, handles operating hours and affordability. Maps affordance names to indices for tensor operations.

- **dac_engine.py** (`DACEngine`): Drive As Code reward computation engine. Compiles declarative YAML specs into GPU-native computation graphs. Implements formula: `total_reward = extrinsic + (intrinsic * effective_intrinsic_weight) + shaping`. Uses torch.where for efficient modifier evaluation.

- **meter_dynamics.py** (`MeterDynamics`): Meter update logic including depletion, cascades, and effects. All operations vectorized across agents. Handles meter relationships (e.g., low energy depletes health).

- **action_builder.py** (`ComposedActionSpace`): Combines substrate actions (MOVE, INTERACT) with custom actions (REST, MEDITATE) into unified action vocabulary. Validates action masks against substrate boundaries.

- **action_config.py** (`ActionConfig`, `ActionSpaceConfig`): Configuration DTOs for action space metadata, labels, and enabled actions. Ensures global action vocabulary for checkpoint transfer.

- **temporal_utils.py**: Time-of-day utilities for affordance opening hours, temporal mechanics (day/night cycle), and temporal feature encoding.

#### Dependencies

**Inbound** (who depends on this):
- population (VectorizedPopulation calls env.step(), env.reset())
- demo (DemoRunner instantiates environment)
- recording (episode recorder observes environment state)

**Outbound** (this depends on):
- substrate (Grid2D/Grid3D/Continuous/Aspatial for spatial operations)
- vfs (VariableRegistry for state management, observation building)
- effects (EffectManager for cascade execution)
- items (ItemManager for inventory and spawning)
- universe (CompiledUniverse for all configuration)
- world (expression evaluation via VFSEvaluator)

**External libraries**:
- PyTorch (GPU tensors, batch operations)
- NumPy (occasional CPU array conversions)

#### Patterns & Design Decisions

**GPU-Native Vectorization**: All operations batched [num_agents, ...] to minimize CPU-GPU transfers. Single step() call processes all agents in parallel.

**Compiler-Driven Configuration**: Environment reads all behavioral parameters from CompiledUniverse. No hardcoded defaults (no-defaults principle). Recompilation required for config changes.

**Modular Game Mechanics**: Affordances, effects, and items are pluggable subsystems. AffordanceEngine pre-compiles Effects commands at startup for performance. ItemManager handles inventory/spawning independently.

**DAC Integration**: DACEngine computes rewards declaratively from YAML. Intrinsic rewards modulated by crisis suppression modifiers (e.g., disable exploration when energy low). Formula: `total_reward = extrinsic + (intrinsic * base_weight * modifiers) + shaping`.

**POMDP Support**: When partial observability enabled, renders local vision window (5×5 for vision_range=2) around agent position. Validates substrate compatibility (Grid2D/Grid3D only, not continuous/aspatial).

**Performance Optimization**: Pre-computes bar index maps, affordance lookups, and Effects commands at initialization. Runtime operations are pure tensor math.

#### Integration Points

**Training Loop Integration**:
1. Population calls `env.reset()` → returns initial observations [num_agents, obs_dim]
2. Population calls `env.step(actions, depletion_multiplier)` → returns (next_obs, rewards, dones, info)
3. Environment internally: validates actions → updates substrate positions → processes affordances → updates meters → computes rewards (DAC) → applies effects → handles items → returns results
4. Population stores transitions in replay buffer and trains Q-network

**Key Interfaces**:
- `reset() -> torch.Tensor`: Initialize all agents, return observations
- `step(actions, depletion_multiplier) -> (obs, rewards, dones, info)`: Execute actions, return transitions
- `get_action_masks() -> torch.Tensor`: Return valid actions per agent [num_agents, action_dim]
- `attach_runtime_registry(registry)`: Wire AgentRuntimeRegistry for telemetry
- `set_exploration_module(exploration)`: Wire exploration strategy for intrinsic rewards

**Data Flow**:
- IN: actions [num_agents], curriculum depletion multiplier (float)
- PROCESS: substrate motion → affordance interactions → meter updates → DAC rewards → effects → items
- OUT: observations [num_agents, obs_dim], rewards [num_agents], dones [num_agents], info (dict with telemetry)

#### Confidence Level

**HIGH**: VectorizedHamletEnv is well-documented with clear initialization from CompiledUniverse. All subsystem integrations (DAC, affordances, effects, items, VFS) are visible in __init__ and step(). Code is production-ready with GPU optimizations and extensive validation.

Evidence: Complete source review of vectorized_env.py (300 lines analyzed), affordance_engine.py, dac_engine.py, meter_dynamics.py. Clear integration with population via Gymnasium-style interface.

---

### Subsystem 2: population

**Name**: population
**Location**: src/townlet/population/
**Primary Responsibility**: Population-based training orchestration - manages Q-networks (online/target), replay buffers, training loops, curriculum integration, and exploration strategies for batched agents.

#### Key Components

- **vectorized.py** (`VectorizedPopulation`): Core population manager coordinating num_agents parallel agents. Owns Q-networks (online + target), optimizer, replay buffer, and training state. Implements step_population() training loop: action selection → env.step() → replay buffer storage → Q-network training → target network updates.

- **base.py** (`PopulationManager`): Abstract base class defining population interface. Specifies contracts for reset(), step_population(), checkpoint management.

- **runtime_registry.py** (`AgentRuntimeRegistry`): Per-agent runtime telemetry storage (epsilon, intrinsic weight, survival time, curriculum stage). Provides GPU tensors for fast reads, CPU snapshots for logging. Single source of truth for agent metrics.

#### Dependencies

**Inbound** (who depends on this):
- demo (DemoRunner instantiates and calls population.step_population())
- checkpoint_utils (saves/loads population state)

**Outbound** (this depends on):
- agent (NetworkFactory for Q-network construction, networks module for forward passes)
- training (ReplayBuffer/SequentialReplayBuffer/PrioritizedReplayBuffer for experience storage)
- environment (VectorizedHamletEnv for step() and reset())
- curriculum (CurriculumManager for difficulty decisions)
- exploration (ExplorationStrategy for action selection, RNDExploration for intrinsic rewards)
- universe (CompiledUniverse for action_dim, observation metadata)

**External libraries**:
- PyTorch (nn.Module for networks, optimizer, loss functions)
- NumPy (checkpoint serialization)

#### Patterns & Design Decisions

**Brain As Code (BAC)**: All network architecture, optimizer, loss function, and replay buffer parameters come from `brain.yaml` (BrainConfig). No hardcoded defaults. NetworkFactory builds networks declaratively.

**Dual Network Architecture**: Online Q-network (training) + target network (stable Q-targets). Target synced every `target_update_frequency` steps. Prevents moving target problem in Q-learning.

**Double DQN Support**: Configurable via `brain.yaml: use_double_dqn`. When enabled, decouples action selection (online network) from evaluation (target network) to reduce Q-value overestimation.

**Replay Buffer Variants**:
- Feedforward: `ReplayBuffer` (standard) or `PrioritizedReplayBuffer` (PER with importance sampling)
- Recurrent: `SequentialReplayBuffer` (episode sequences for LSTM training)
- PER not yet supported for recurrent (raises NotImplementedError)

**LSTM Hidden State Management**: RecurrentSpatialQNetwork maintains hidden state across episode rollout. Resets at episode start, persists during step(), resets per agent on done. Separate hidden state for training (batch sequences).

**Gradient Clipping**: max_norm=10.0 prevents exploding gradients in recurrent networks.

**Telemetry Sync**: runtime_registry synced every step with epsilon, intrinsic weight, curriculum stage. Provides live metrics for inference server.

#### Integration Points

**Training Loop Flow**:
1. `reset()`: Initialize environment, reset Q-network hidden state (if recurrent)
2. `step_population(env)`:
   - Get Q-values from online network
   - Get curriculum decisions (difficulty, depletion_multiplier)
   - Select actions via exploration strategy (epsilon-greedy + action masking)
   - Call `env.step(actions, depletion_multiplier)`
   - Store transition in replay buffer
   - Train Q-network if `total_steps % train_frequency == 0` and buffer has enough samples
   - Update target network if `training_step_counter % target_update_frequency == 0`
   - Handle episode resets (flush episodes for recurrent, update exploration)
3. Return `BatchedAgentState` with observations, actions, rewards, dones

**Checkpoint Interface**:
- `get_checkpoint_state() -> dict`: Complete state (q_network, target_network, optimizer, scheduler, replay_buffer, exploration_state, universe_metadata)
- `load_checkpoint_state(checkpoint)`: Restore from checkpoint with universe compatibility validation

**Curriculum Integration**:
- Receives `CurriculumDecision` (difficulty_level, depletion_multiplier) per agent
- Passes depletion_multiplier to `env.step()` for dynamic meter depletion
- Syncs curriculum stage to runtime_registry for telemetry

**Exploration Integration**:
- Wires exploration module to environment via `env.set_exploration_module()`
- Calls `exploration.select_actions(q_values, state, action_masks)` for action selection
- Computes intrinsic rewards via `exploration.compute_intrinsic_rewards()` for logging (DAC already included intrinsic in rewards)

#### Confidence Level

**HIGH**: VectorizedPopulation is the central training coordinator with clear responsibilities. Complete source review (1095 lines) shows all integrations: network construction (NetworkFactory), training loop (Q-learning with replay buffer), curriculum (CurriculumManager), exploration (ExplorationStrategy), checkpointing. Production-ready with robust error handling and universe metadata validation.

Evidence: Full source analysis of vectorized.py, runtime_registry.py, base.py. Clear contracts with environment (Gymnasium interface), agent (network factory), training (replay buffers).

---

### Subsystem 3: agent

**Name**: agent
**Location**: src/townlet/agent/
**Primary Responsibility**: Neural network architectures for Q-learning, including feedforward (MLP), recurrent (LSTM), and dueling networks, plus factory pattern for declarative network construction from configuration.

#### Key Components

- **networks.py**: Core Q-network architectures:
  - `SimpleQNetwork`: Feedforward MLP with LayerNorm (obs_dim → 256 → 128 → action_dim)
  - `RecurrentSpatialQNetwork`: LSTM-based network for POMDP with vision encoder (CNN), position encoder, meter encoder, affordance encoder, and temporal encoder. LSTM hidden state managed across episodes.
  - `DuelingQNetwork`: Dueling architecture with value/advantage decomposition (Wang et al. 2016)
  - `StructuredQNetwork`: Group-based encoders for semantic observation groups (spatial, bars, affordances, temporal)

- **network_factory.py** (`NetworkFactory`): Factory for building Q-networks from BrainConfig. Static methods: `build_feedforward()`, `build_recurrent()`, `build_dueling()`. Enables declarative network construction from YAML.

- **brain_config.py** (`BrainConfig`): Pydantic DTO for network configuration (architecture, optimizer, loss, Q-learning params, replay buffer settings). Enforces no-defaults principle. Computes brain_hash for checkpoint provenance.

- **optimizer_factory.py** (`OptimizerFactory`): Builds PyTorch optimizers (Adam, SGD, RMSprop) from config. Supports optional learning rate schedulers (StepLR, ExponentialLR, CosineAnnealing).

- **loss_factory.py** (`LossFactory`): Builds loss functions (MSE, Huber, SmoothL1) from config. Huber loss requires delta parameter.

#### Dependencies

**Inbound** (who depends on this):
- population (VectorizedPopulation instantiates networks via NetworkFactory, calls forward(), optimizer.step())
- training (checkpoint_utils saves/loads network weights)

**Outbound** (this depends on):
- universe (ObservationSpec for recurrent network slicing)
- vfs (observation activity for structured networks)

**External libraries**:
- PyTorch (nn.Module, nn.Linear, nn.LSTM, nn.Conv2d, optimizers, loss functions)

#### Patterns & Design Decisions

**Factory Pattern**: NetworkFactory centralizes network construction. Future-proofs for Software Defined Agents (SDA) where architecture comes entirely from config.

**No-Defaults Principle**: All architecture parameters (hidden_dim, layers, activation, dropout) must be explicit in BrainConfig. No fallback defaults.

**LSTM Hidden State Lifecycle**:
- Reset at episode start: `reset_hidden_state(batch_size, device)`
- Persist during episode: `forward()` returns (q_values, new_hidden), caller updates via `set_hidden_state()`
- Reset per agent on done: `hidden_state[:, agent_idx, :] = 0.0`
- Reset for training: batch of sequences gets fresh hidden state

**Observation Slicing for LSTM**: RecurrentSpatialQNetwork uses ObservationSpec for field extraction (v2.1 pipeline). Legacy positional slicing removed. Fields: obs_local_window, obs_position, obs_meters, obs_affordances, obs_temporal.

**Dueling Architecture**: Separate value stream V(s) and advantage stream A(s,a). Q(s,a) = V(s) + (A(s,a) - mean(A)). Mean subtraction ensures identifiability.

**Brain Hash Provenance**: compute_brain_hash() generates SHA256 of BrainConfig for checkpoint validation. Prevents loading checkpoints trained with different network architectures.

#### Integration Points

**Population Integration**:
1. Population constructs networks via `NetworkFactory.build_*()` from BrainConfig
2. Forward pass: `q_values = q_network(observations)` (feedforward) or `q_values, hidden = q_network(observations)` (recurrent)
3. Training: compute loss, backprop, optimizer.step(), clip gradients
4. Checkpoint: save/load q_network.state_dict(), target_network.state_dict(), optimizer.state_dict()

**Network Construction Flow**:
```
BrainConfig (YAML) → NetworkFactory → Q-network (nn.Module)
                   ↓
            OptimizerFactory → optimizer
                   ↓
              LossFactory → loss_fn
```

**Recurrent Forward Pass**:
```
obs [batch, obs_dim]
  ↓ slice via ObservationSpec
grid, position, meters, affordances, temporal
  ↓ encode
vision_features (CNN), position_features (MLP), meter_features, affordance_features, temporal_features
  ↓ concatenate
combined [batch, 1, lstm_input_dim]
  ↓ LSTM
lstm_out [batch, hidden_dim]
  ↓ LayerNorm + MLP
q_values [batch, action_dim]
```

#### Confidence Level

**HIGH**: All network architectures are production-ready with clear responsibilities. NetworkFactory provides clean abstraction for declarative construction. BrainConfig enforces no-defaults principle. LSTM hidden state management is well-documented with lifecycle comments.

Evidence: Complete source review of networks.py (540 lines), network_factory.py, brain_config.py. Clear integration with population via forward() and checkpoint state_dict().

---

### Subsystem 4: training

**Name**: training
**Location**: src/townlet/training/
**Primary Responsibility**: Training infrastructure including replay buffers (standard, sequential, prioritized), checkpoint utilities, training state DTOs, and TensorBoard logging.

#### Key Components

- **replay_buffer.py** (`ReplayBuffer`): Circular buffer for feedforward DQN. Stores (obs, action, reward_extrinsic, reward_intrinsic, next_obs, done) transitions. Samples random mini-batches with combined rewards. Vectorized push/sample operations.

- **sequential_replay_buffer.py** (`SequentialReplayBuffer`): Episode buffer for recurrent networks. Stores full episodes as sequences. Samples contiguous subsequences for LSTM training with post-terminal masking.

- **prioritized_replay_buffer.py** (`PrioritizedReplayBuffer`): Prioritized experience replay with importance sampling weights. Uses TD error for priority updates. Beta annealing for bias correction.

- **checkpoint_utils.py**: Checkpoint security and validation:
  - `attach_universe_metadata()`: Add config_hash, obs_dim, action_dim, drive_hash to checkpoint
  - `assert_checkpoint_dimensions()`: Validate dimension compatibility
  - `config_hash_warning()`: Warn on universe mismatch
  - `persist_checkpoint_digest()`: Compute SHA256 for checkpoints
  - `verify_checkpoint_digest()`: Validate checkpoint integrity
  - `safe_torch_load()`: Load checkpoints with weights_only safety guard

- **state.py**: Training state DTOs:
  - `CurriculumDecision` (cold path, Pydantic): Immutable curriculum configuration (difficulty_level, depletion_multiplier, reward_mode)
  - `PopulationCheckpoint` (cold path, Pydantic): Serializable population state for checkpointing
  - `BatchedAgentState` (hot path, slots): GPU tensors for training loop (observations, actions, rewards, dones, epsilons)

- **tensorboard_logger.py** (`TensorBoardLogger`): TensorBoard integration for metrics logging (scalars, histograms, distributions). Flush control for real-time monitoring.

#### Dependencies

**Inbound** (who depends on this):
- population (uses replay buffers for experience storage, checkpoint_utils for save/load)
- demo (DemoRunner uses checkpoint_utils and TensorBoard logger)

**Outbound** (this depends on):
- universe (CompiledUniverse for metadata validation)

**External libraries**:
- PyTorch (tensor storage, state_dict serialization)
- NumPy (checkpoint serialization of scalars)
- TensorFlow (TensorBoard writer)

#### Patterns & Design Decisions

**Dual Reward Storage**: Replay buffers store extrinsic and intrinsic rewards separately. Combine at sample time with configurable intrinsic_weight. Enables dynamic intrinsic weight annealing.

**Post-Terminal Masking**: SequentialReplayBuffer applies mask to prevent gradients from post-terminal garbage in LSTM training. Loss computed only on valid timesteps.

**Prioritized Replay (PER)**:
- Alpha controls priority exponent (0 = uniform, 1 = full prioritization)
- Beta controls importance sampling (starts <1, anneals to 1)
- TD error magnitude determines priority
- Not yet supported for recurrent networks

**Checkpoint Provenance**: Checkpoints include universe_metadata (config_hash, obs_dim, action_dim, meter_count, drive_hash) for compatibility validation. Prevents loading checkpoints trained on different universes.

**Hot/Cold Path Separation**: BatchedAgentState (hot path) uses slots and GPU tensors for performance. CurriculumDecision/PopulationCheckpoint (cold path) use Pydantic for validation and serialization.

**Checkpoint Security**: SHA256 digests detect tampering/corruption. weights_only=True prevents arbitrary code execution from untrusted checkpoints. Numpy type allowlisting for PyTorch 2.6+ compatibility.

#### Integration Points

**Population Training Loop**:
1. Population calls `replay_buffer.push(obs, actions, rewards_extrinsic, rewards_intrinsic, next_obs, dones)`
2. When `total_steps % train_frequency == 0`:
   - Feedforward: `batch = replay_buffer.sample(batch_size, intrinsic_weight)` (standard or PER)
   - Recurrent: `batch = sequential_buffer.sample_sequences(batch_size, seq_len, intrinsic_weight)`
3. Compute loss, backprop, update Q-network
4. PER: `prioritized_buffer.update_priorities(indices, td_errors)`

**Checkpoint Flow**:
1. DemoRunner calls `population.get_checkpoint_state()` → dict with q_network, optimizer, replay_buffer, exploration_state
2. `attach_universe_metadata(checkpoint, universe)` → add config_hash, dimensions
3. `torch.save(checkpoint, path)` → serialize to disk
4. `persist_checkpoint_digest(path)` → compute SHA256
5. Load: `verify_checkpoint_digest(path)` → validate integrity
6. `safe_torch_load(path)` → load with security checks
7. `assert_checkpoint_dimensions(checkpoint, universe)` → validate compatibility
8. `population.load_checkpoint_state(checkpoint)` → restore state

**Replay Buffer Serialization**:
- `serialize() -> dict`: Extract transitions to CPU for checkpointing
- `load_from_serialized(state)`: Restore from checkpoint, move to device

#### Confidence Level

**HIGH**: Replay buffers are well-documented with clear contracts for push/sample/serialize. Checkpoint utilities provide comprehensive validation and security. State DTOs follow hot/cold path separation pattern. TensorBoard integration is straightforward.

Evidence: Complete source review of replay_buffer.py (273 lines), sequential_replay_buffer.py, prioritized_replay_buffer.py, checkpoint_utils.py (165 lines), state.py (138 lines). Clear integration with population via push/sample/checkpoint interfaces.

---

## Training Loop Flow Summary

The 4 Core Training subsystems integrate as follows:

**Initialization (DemoRunner)**:
1. Compile universe from YAML configs
2. Instantiate environment from CompiledUniverse
3. Build networks via NetworkFactory from BrainConfig
4. Instantiate population with environment, curriculum, exploration
5. Load checkpoint if exists (validate dimensions, restore state)

**Training Step (population.step_population)**:
1. **Agent**: Q-network forward pass → q_values [num_agents, action_dim]
2. **Population**: Get curriculum decisions (difficulty, depletion_multiplier)
3. **Population**: Select actions via exploration + action masks
4. **Environment**: Process actions → update substrate → affordances → meters → DAC → effects → items
5. **Environment**: Return (next_obs, rewards, dones, info)
6. **Training**: Store transitions in replay buffer
7. **Agent**: Train Q-network if `total_steps % train_frequency == 0`:
   - Sample batch from replay buffer
   - Compute Q-targets (online + target networks)
   - Compute loss (MSE/Huber/SmoothL1)
   - Backprop, clip gradients, optimizer step
   - Update priorities (if PER)
8. **Agent**: Update target network if `training_step_counter % target_update_frequency == 0`
9. **Population**: Return BatchedAgentState with telemetry

**Checkpointing (DemoRunner)**:
1. Flush all agents' episodes to replay buffer
2. Collect checkpoint state: q_network, target_network, optimizer, replay_buffer, exploration_state
3. Add universe_metadata for validation
4. Save to disk with SHA256 digest
5. Log to database and TensorBoard

**Critical Questions Answered**:
- **Training loop flow**: population.step_population() → env.step() → replay buffer → train Q-network → update target
- **Environment-population relationship**: Population owns environment, calls step() and reset(), wires exploration module and runtime registry
- **Agent network management**: NetworkFactory instantiates from BrainConfig, population owns online + target networks, syncs via state_dict()
- **Checkpoint triggers**: DemoRunner saves every CHECKPOINT_INTERVAL (100) episodes, flushes replay buffer first

---

## Group 2: Configuration

**Purpose**: Configuration validation and compilation - YAML config DTOs, universe compiler pipeline, and CLI tools

**Subsystems**: config, universe, compiler

### Subsystem 1: config

**Location**: `src/townlet/config/`

**Primary Responsibility**: Pydantic-based configuration DTOs (Data Transfer Objects) that enforce the no-defaults principle for all behavioral parameters in YAML config files.

#### Key Components

- `base.py`: Core utilities for YAML loading and validation error formatting
  - `load_yaml_section()`: Loads and validates YAML sections with helpful error messages
  - `format_validation_error()`: Transforms Pydantic errors into actionable messages

- `training_v2_config.py`: Training hyperparameters DTO (curriculum-level)
  - `TrainingV2Config`: Population size, Q-learning params, replay buffer, exploration, intrinsic strategies
  - All fields required (no defaults) with Pydantic validation

- `bars_v2_config.py`: Meter (bars) and cascade parameters DTO (curriculum-level)
  - `BarsV2Config`: Meter depletion/recovery rates, bounds, lethality
  - `CascadeParamConfig`: Meter relationship parameters (threshold, strength)

- `affordances_v2_config.py`: Affordance parameters DTO (curriculum-level)
  - `AffordancesV2Config`: Affordance costs, effects, deployment positions
  - `AffordanceParamConfig`: Per-affordance configuration

- `environment_config.py`: Environment-level vocabulary DTO (experiment-wide)
  - `EnvironmentConfig`: Meters, cascades, affordances, VFS variables registry
  - Defines canonical names and metadata for all entities

- `stratum_config.py`: Substrate configuration DTO (experiment-wide)
  - `StratumConfig`: Grid topology, observation modes, temporal support
  - `SubstrateConfig`: Grid dimensions, boundaries, distance metrics

- `agent_config.py`: Neural network configuration DTO (experiment-wide)
  - `AgentConfig`: Network architecture, brain type (feedforward/recurrent), drive specification

- `actions_config.py`: Action space configuration DTO (experiment-wide)
  - `ActionsConfig`: Substrate actions, custom actions, action labels

- `drive_as_code.py`: DAC (Drive As Code) reward function DTOs
  - `DriveAsCodeConfig`: Declarative reward specifications (modifiers, extrinsic, intrinsic, shaping)
  - `ModifierConfig`: Range-based multipliers for contextual reward adjustment
  - `ExtrinsicStrategyConfig`: Base reward strategies (multiplicative, additive, etc.)
  - `IntrinsicStrategyConfig`: Exploration drives (RND, ICM, count-based, etc.)

- `vfs_config.py`: VFS (Variable & Feature System) configuration DTOs
  - Variable definitions, observation fields, normalization specs

- `effects_config.py`: Effect system configuration DTOs
  - Effect definitions, triggers, cascades

- `items_config.py`: Item system configuration DTOs
  - Item types, appearances, spawn rules, pickup behavior

- `__init__.py`: Exposes v2.1 configuration entrypoints
  - `CONFIG_SCHEMA_VERSION = "2.1.0"`
  - Re-exports all major config classes

#### Dependencies

**Inbound** (who depends on config):
- `universe` - Compiler loads and validates all config DTOs
- `environment` - Runtime uses compiled configs
- `population` - Training uses training configs
- `demo` - Demo server loads configs

**Outbound** (config depends on):
- **External**: `pydantic` (v2.0+) - DTO validation framework
- **External**: `pyyaml` - YAML parsing

**Internal**: None (config is a foundational layer with no internal dependencies)

#### Patterns & Design Decisions

**1. No-Defaults Principle** (CRITICAL):
- **Pattern**: All behavioral parameters must be explicitly specified in YAML
- **Enforcement**: Pydantic models use `Field()` with no `default` values for behavioral fields
- **Rationale**: Hidden defaults create non-reproducible configs; changing code defaults silently breaks old configs
- **Implementation**:
  - `model_config = ConfigDict(extra="forbid")` - Reject unknown fields
  - Required fields have no `default=` parameter
  - Only metadata (descriptions) and computed values are exempted
- **Example**:
  ```python
  class QLearningConfig(BaseModel):
      model_config = ConfigDict(extra="forbid")

      use_double_dqn: bool = Field(description="Enable Double DQN")  # REQUIRED
      gamma: float = Field(gt=0.0, le=1.0, description="Discount factor")  # REQUIRED
      learning_rate: float = Field(gt=0.0, description="Learning rate")  # REQUIRED
  ```

**2. Hierarchical Config Structure** (v2.1):
- **Pattern**: Experiment-level (shared) configs + curriculum-level (per-level) configs
- **Structure**:
  ```
  experiment_dir/
  ├── experiment.yaml     # Experiment metadata
  ├── stratum.yaml        # Substrate configuration
  ├── environment.yaml    # Vocabulary (meters, affordances, cascades)
  ├── actions.yaml        # Action space
  ├── agent.yaml          # Neural network
  ├── effects.yaml        # Effect catalog (optional)
  ├── items.yaml          # Item catalog (optional)
  ├── vfs_profiles.yaml   # VFS profiles (optional)
  └── levels/
      └── L1_full_observability/
          ├── curriculum.yaml   # Curriculum strategy
          ├── bars.yaml         # Meter parameters
          ├── affordances.yaml  # Affordance parameters
          └── training.yaml     # Training hyperparameters
  ```

**3. Validation-Rich DTOs**:
- **Pattern**: Pydantic validators enforce semantic constraints at parse time
- **Examples**:
  - `@model_validator`: Cross-field validation (e.g., `min_size <= capacity`)
  - `@field_validator`: Single-field validation (e.g., unique action names)
  - `Field(gt=0.0, le=1.0)`: Numeric constraints

**4. Helpful Error Messages**:
- **Pattern**: Transform cryptic Pydantic errors into actionable messages
- **Implementation**: `format_validation_error()` in `base.py`
- **Output**: References to template configs, explicit missing fields

**5. Breaking Changes Strategy**:
- **Pattern**: Pre-release → zero backwards compatibility → delete old code immediately
- **Evidence**: All configs must use v2.1 schema; no fallbacks for old formats

#### Integration Points

**YAML → DTO Pipeline**:
1. Operator writes YAML config files in hierarchical structure
2. `base.load_yaml_section()` reads YAML files
3. Pydantic DTOs validate structure and constraints
4. Compiler receives validated DTOs for Stage 1 processing
5. Runtime receives compiled artifacts (no direct YAML parsing)

**Config Schema Evolution**:
- `CONFIG_SCHEMA_VERSION = "2.1.0"` tracks breaking changes
- No migration paths - configs must be updated to latest schema
- Templates in `configs/templates/` provide reference implementations

**CLI Validation**:
- `python -m townlet.universe validate <config_dir>` - Validates DTOs without compiling
- Pydantic errors surfaced with helpful context

#### Confidence Level

**HIGH**:
- Clear file structure with comprehensive Pydantic models
- No-defaults principle explicitly documented in docstrings
- All major config types identified and analyzed
- Validation patterns consistent across all DTOs
- Integration points well-defined (YAML → DTO → Compiler)

---

### Subsystem 2: universe

**Location**: `src/townlet/universe/`

**Primary Responsibility**: Seven-stage compiler pipeline that transforms validated config DTOs into optimized, immutable `CompiledUniverse` artifacts with multi-level curriculum support.

#### Key Components

- `compiler.py`: Main compiler implementation with 7-stage pipeline
  - `UniverseCompiler`: Entry point for compilation
  - Stage 0: Scoping preflight (validate file structure)
  - Stage 1: Parse v2.1 configs (load DTOs)
  - Stage 2: Build symbol table (register all entities)
  - Stage 3: Resolve references (validate symbolic references)
  - Stage 4: Cross-validate semantics (validate relationships)
  - Stage 5: Enrich shared schemas (VFS profiles, effects, expression types)
  - Stage 6: Compile levels + optimization (per-level metadata, optimization data)
  - Stage 7: Emit artifact + cache (serialize to MessagePack)

- `symbol_table.py`: Symbol registry for cross-stage validation
  - `UniverseSymbolTable`: Stores registered entities (meters, affordances, actions, variables, cascades, cues, items)
  - Provides lookup methods with helpful error messages
  - Prevents duplicate registrations

- `compiled.py`: Immutable compiled artifact representation
  - `CompiledUniverse`: Frozen dataclass with all compiled metadata and optimization data
  - `CompiledVFSProfiles`: Compiled VFS profiles (global, agent, item)
  - `save_to_cache()`: Serialize to MessagePack (`.compiled/universe.msgpack`)
  - `load_from_cache()`: Deserialize with schema version validation

- `optimization.py`: Pre-computed runtime optimization data
  - `OptimizationData`: GPU tensors and lookup tables for fast runtime execution
  - `base_depletions`: Pre-computed meter depletion rates
  - `cascade_data`: Pre-compiled cascade relationships
  - `action_mask_table`: Temporal action availability (24-hour cycle)
  - `affordance_position_map`: Pre-computed affordance positions

- `raw_configs_v21.py`: Raw config loader for hierarchical v2.1 structure
  - `RawConfigsV21`: Container for all v2.1 DTOs
  - `CurriculumLevel`: Per-level config bundle (bars, affordances, curriculum, training)
  - Security limits enforcement (MAX_METERS, MAX_AFFORDANCES, etc.)
  - Cascade cycle detection

- `errors.py`: Compilation error handling
  - `CompilationError`: Structured error with stage, errors, hints, warnings
  - `CompilationErrorCollector`: Accumulates errors before raising
  - `CompilationMessage`: Structured diagnostic with code and location

- `cues_compiler.py`: UI cues compilation (metadata only)
  - Compiles UI hints and tooltips for frontend visualization

- `source_map.py`: Source location tracking for error reporting
  - Maps compiled elements back to source YAML locations

- `dto.py`: Metadata DTOs for compiled artifacts (not shown but referenced)
  - `UniverseMetadata`, `ObservationSpec`, `ActionSpaceMetadata`, etc.

#### Dependencies

**Inbound** (who depends on universe):
- `compiler` - CLI tool invokes `UniverseCompiler.compile()`
- `demo` - Demo server loads `CompiledUniverse` artifacts
- `environment` - Runtime uses compiled metadata and optimization data
- `population` - Training uses compiled observation specs

**Outbound** (universe depends on):
- `config` - Loads all Pydantic DTOs (experiment, stratum, environment, bars, affordances, training, etc.)
- `vfs` - Compiles VFS profiles, validates VFS expressions
- `world` - Type checks expressions, validates temporal history
- `effects` - Compiles effect catalog
- `items` - Compiles item catalog
- `substrate` - Validates substrate configurations

**External**:
- `pydantic` - DTO validation
- `pyyaml` - YAML parsing
- `msgpack` - Serialization/deserialization
- `torch` - GPU tensor optimization data

#### Patterns & Design Decisions

**1. Seven-Stage Compiler Pipeline**:
- **Stage 0**: Scoping preflight
  - Validates file structure (required files, forbidden files)
  - Ensures `vfs_profiles.yaml` and `items.yaml` at experiment root (not in levels)
  - Fast-fail before heavy parsing

- **Stage 1**: Parse v2.1 configs
  - Loads all YAML files via Pydantic DTOs
  - Hierarchical structure: experiment-level + per-level
  - Returns `RawConfigsV21` container

- **Stage 2**: Build symbol table
  - Registers all named entities (meters, affordances, actions, variables, cascades, cues, items)
  - Detects duplicate names early
  - Provides lookup API for later stages

- **Stage 3**: Resolve references
  - Validates symbolic references (e.g., cascade source/target, affordance modulation)
  - Checks VFS variable references in expressions
  - Validates DAC references to bars and variables
  - Type-checks expressions against symbol table

- **Stage 4**: Cross-validate semantics
  - Validates relationships between entities
  - Ensures vocabulary consistency across curriculum levels
  - Detects cascade cycles
  - Validates temporal mechanics (if enabled)

- **Stage 5**: Enrich shared schemas
  - Compiles VFS profiles (global, agent, item)
  - Compiles effect catalog (optional)
  - Builds expression type schema for runtime validation
  - Computes VFS history requirements

- **Stage 6**: Compile levels + optimization
  - Generates per-level metadata (observation specs, action spaces)
  - Pre-computes optimization data (GPU tensors, lookup tables)
  - Builds action mask tables for temporal mechanics
  - Computes affordance position maps

- **Stage 7**: Emit artifact + cache
  - Serializes `CompiledUniverse` to MessagePack
  - Writes to `.compiled/universe.msgpack`
  - Includes provenance (config hash, mtime, drive_hash)
  - Schema version checking for cache invalidation

**2. Cache-First Compilation**:
- **Pattern**: Check cache fingerprint before recompiling
- **Implementation**:
  - Compute config hash (SHA256 of all YAML files)
  - Compute config mtime (latest modification time)
  - Compare against cached artifact metadata
  - Skip compilation if cache valid
- **Performance**: ~500ms cold compile → ~50ms cache hit

**3. Security Limits** (DoS Protection):
- **Pattern**: Hard limits on config size to prevent resource exhaustion
- **Limits**:
  - `MAX_METERS = 100`
  - `MAX_AFFORDANCES = 100`
  - `MAX_CASCADES = 500`
  - `MAX_ACTIONS = 300`
  - `MAX_VARIABLES = 200`
  - `MAX_GRID_CELLS = 10000` (100×100 grid)
  - `MAX_CACHE_FILE_SIZE = 10MB`
  - `MAX_ITEM_TYPES = 200`
  - `MAX_VFS_PROFILES = 200`
- **Enforcement**: Checked in Stage 0 and `RawConfigsV21.__post_init__()`

**4. Multi-Level Curriculum Support**:
- **Pattern**: Single compilation produces artifacts for all curriculum levels
- **Primary Level**: One level selected as primary (determines top-level metadata)
- **All Levels**: Dictionary of per-level metadata for runtime level switching
- **Vocabulary Consistency**: All levels must share same meters and affordances

**5. Provenance Tracking**:
- **Pattern**: Track config hash and drive_hash for reproducibility
- **config_hash**: SHA256 of all YAML files (for cache invalidation)
- **drive_hash**: SHA256 of DAC config (for checkpoint compatibility)
- **mtime**: Latest modification time across all configs

**6. Immutable Artifacts**:
- **Pattern**: `CompiledUniverse` is a frozen dataclass
- **Rationale**: Prevents accidental mutation, enables safe sharing across threads
- **Implementation**: `@dataclass(frozen=True)`

#### Integration Points

**Config → Compiled Artifact Pipeline**:
```
YAML Configs
    ↓ (load_yaml_section)
Pydantic DTOs
    ↓ (Stage 1)
RawConfigsV21
    ↓ (Stages 2-6)
CompiledUniverse
    ↓ (Stage 7)
.compiled/universe.msgpack
    ↓ (load_from_cache)
Runtime Execution
```

**Compilation Artifacts**:
1. **Primary Output**: `config_dir/.compiled/universe.msgpack`
   - Binary MessagePack format
   - Schema version: `COMPILED_SCHEMA_VERSION = "1.2"`
   - Contains all metadata, optimization data, and per-level configs

2. **Metadata**:
   - `UniverseMetadata`: Universe name, substrate type, observation dim, action count
   - `ObservationSpec`: Observation field definitions and dimensions
   - `ActionSpaceMetadata`: Action vocabulary and labels
   - `MeterMetadata`: Meter names, indices, types
   - `AffordanceMetadata`: Affordance names, indices, categories

3. **Optimization Data**:
   - `base_depletions`: Torch tensor of meter depletion rates
   - `cascade_data`: Pre-compiled cascade relationships
   - `action_mask_table`: 24×N boolean tensor for temporal availability
   - `affordance_position_map`: Pre-computed positions per affordance

4. **Per-Level Artifacts** (Multi-Level Support):
   - Each level has its own observation spec, metadata, and optimization data
   - Enables runtime switching between curriculum levels without recompilation

**CLI Integration**:
- `python -m townlet.universe compile <config_dir>` - Compile with caching
- `python -m townlet.universe compile --no-cache` - Force recompile
- `python -m townlet.universe validate <config_dir>` - Lint-style check (no cache)
- `python -m townlet.universe inspect <artifact>` - Inspect compiled artifact

**CI/CD Integration**:
- `.github/workflows/config-validation.yml` - Validates all config packs in CI
- Catches compilation errors before merge

#### Confidence Level

**HIGH**:
- Complete 7-stage pipeline identified and documented
- All key components located and analyzed
- Artifact structure well-defined (MessagePack with schema versioning)
- Security limits and validation patterns clear
- Integration points from YAML to runtime execution mapped
- Cache strategy and provenance tracking understood

---

### Subsystem 3: compiler

**Location**: `src/townlet/compiler/`

**Primary Responsibility**: CLI tool for invoking the Universe compiler with commands for compilation, inspection, and validation.

#### Key Components

- `__main__.py`: CLI entry point (`python -m townlet.universe`)
  - `main()`: Argument parsing and command dispatch
  - `_build_parser()`: Argparse configuration for subcommands
  - `_cmd_compile()`: Compile command implementation
  - `_cmd_inspect()`: Inspect command implementation
  - `_cmd_validate()`: Validate command implementation

- `__init__.py`: Package marker (minimal)

**Commands**:

1. **compile**: Compile a config pack and optionally cache the artifact
   - Args: `config_dir`, `--no-cache`
   - Output: Compilation summary (metadata, elapsed time, cache path)
   - Cache: Writes to `config_dir/.compiled/universe.msgpack`

2. **inspect**: Inspect a compiled universe artifact
   - Args: `artifact`, `--format {table,json}`
   - Auto-resolves: `config_dir` → `config_dir/.compiled/universe.msgpack`
   - Output: Metadata summary (universe name, substrate, counts, hash, timestamp)

3. **validate**: Run compilation without touching the cache (lint-style check)
   - Args: `config_dir`
   - Output: Validation success/failure (no cache writes)
   - Use case: CI/CD, pre-commit hooks

#### Dependencies

**Inbound** (who depends on compiler):
- **CI/CD**: `.github/workflows/config-validation.yml` - Validates all config packs
- **Developers**: Manual invocation for config debugging
- **Build Systems**: Pre-compilation of config packs before deployment

**Outbound** (compiler depends on):
- `universe` - `UniverseCompiler.compile()` for core compilation logic
- `universe.compiled` - `CompiledUniverse.load_from_cache()` for inspection

**External**:
- `argparse` - CLI argument parsing
- `json` - JSON output for inspect command

#### Patterns & Design Decisions

**1. Subcommand CLI Pattern**:
- **Pattern**: Single entry point with multiple subcommands (Git-style)
- **Implementation**: `argparse` with `subparsers`
- **Benefits**: Consistent interface, discoverable commands, built-in help

**2. Developer-Friendly Error Messages**:
- **Pattern**: Surface compilation errors with helpful context
- **Implementation**: Catch `CompilationError`, print to stderr, exit with non-zero
- **Example**:
  ```
  Compilation failed: Stage 2: Symbol Table failed:
    - Duplicate meter 'energy' detected.
  ```

**3. Auto-Resolve Artifact Paths**:
- **Pattern**: Inspect command accepts either config dir or artifact path
- **Implementation**: `if artifact_path.is_dir(): artifact_path = artifact_path / ".compiled" / "universe.msgpack"`
- **Benefits**: Less typing, better UX

**4. Performance Metrics**:
- **Pattern**: Report compilation time for performance monitoring
- **Implementation**: `time.perf_counter()` before/after compilation
- **Output**: `Compilation succeeded in 142.3 ms`

**5. Cache Control**:
- **Pattern**: Explicit `--no-cache` flag for forcing recompilation
- **Rationale**: Default behavior uses cache; override for debugging or CI
- **Implementation**: `compile(config_dir, use_cache=not args.no_cache)`

**6. Format Options**:
- **Pattern**: Inspect command supports table (human) and JSON (machine) formats
- **Rationale**: Table for terminal debugging, JSON for scripting/automation
- **Implementation**: `--format {table,json}` flag

#### Integration Points

**How CLI Invokes Compiler**:
```python
# compile command
compiler = UniverseCompiler()
compiled = compiler.compile(config_dir, use_cache=True)
_print_summary(compiled.metadata)
```

**How Inspect Loads Artifacts**:
```python
# inspect command
compiled = CompiledUniverse.load_from_cache(artifact_path)
print(json.dumps(metadata_to_dict(compiled.metadata), indent=2))
```

**How Validate Works**:
```python
# validate command
compiler = UniverseCompiler()
compiler.compile(config_dir, use_cache=False)  # No cache I/O
print("Validation succeeded")
```

**CI/CD Integration**:
```yaml
# .github/workflows/config-validation.yml
- name: Validate configs
  run: |
    for config in configs/*/; do
      python -m townlet.universe validate "$config"
    done
```

**Pre-Commit Hook Usage**:
```bash
# Pre-commit hook (conceptual)
python -m townlet.universe validate configs/L1_full_observability
```

**Artifact Inspection**:
```bash
# Human-readable summary
python -m townlet.universe inspect configs/L1_full_observability

# Machine-readable JSON
python -m townlet.universe inspect configs/L1_full_observability --format json | jq '.metadata.observation_dim'
```

#### Confidence Level

**HIGH**:
- Simple, well-defined CLI tool with 3 commands
- All commands implemented and documented
- Clear invocation patterns for compilation, inspection, validation
- Integration points with CI/CD and development workflows understood
- CLI architecture follows standard patterns (argparse, subcommands, error handling)

---

## Group 3: State Systems

**Purpose**: State management and computation - Variable & Feature System, expression language, and spatial substrates

**Subsystems**: vfs, world, substrate

### Subsystem 1: vfs (Variable & Feature System)

**Location**: `src/townlet/vfs/`

**Primary Responsibility**: Declarative state space configuration providing runtime storage, access control, and observation spec generation for all environment variables.

#### Key Components

- **`schema.py`** (397 lines): Pydantic schemas for VFS configuration
  - `VariableDef`: Variable definition with scope, type, lifetime, access control
  - `VariableScope`: Enum for global/agent/agent_private/item scopes
  - `NormalizationSpec`: Observation normalization (minmax, zscore)
  - `ObservationField`: Observation field mapping with semantic types
  - `WriteSpec`: Action write specification for variable updates
  - Type system: scalar, vec2i/vec3i/vec2f/vec3f, vecNi/vecNf, bool, agent_ref, item_ref, tensor1d/2d/3d/Nd

- **`registry.py`** (823 lines): Runtime storage with GPU tensors and access control
  - `VariableRegistry`: Primary storage for global/agent/agent_private variables
  - `ScopedVariableRegistry`: Simplified three-scope storage (global, agent, item)
  - Tensor storage: `_storage` dict mapping variable IDs to PyTorch tensors
  - Access control enforcement: `get(var_id, reader)`, `set(var_id, value, writer)`
  - Item VFS storage: Profile-based item variables with `item_vfs` tensor [max_items, max_profile_vars]

- **`observation_builder.py`** (311 lines): Compile-time observation spec generation
  - `VFSObservationSpec`: Dimension specification (global_vfs_dim, agent_vfs_dim, item_vfs_dim)
  - `build_vfs_observation()`: Constructs observation tensor from registry state
  - Handles variable ordering, normalization, and item inventory masking
  - Fixed vocabulary: max_items_per_agent=3, max_item_profiles=5 for transfer learning

- **`evaluator.py`** (212 lines): VFS expression evaluator with mark-and-sweep optimization
  - `VFSEvaluator`: Evaluates VFS expressions using compiled profiles
  - `EvaluationMode`: MARK_AND_SWEEP (observed variables only) vs EAGER (all variables)
  - `evaluate_global_profile()`: Evaluates variables in topological dependency order
  - Temporal history support via `TemporalHistory` integration

- **`profiles.py`** (~400 lines estimated): VFS profile compilation
  - `VFSProfileCompiler`: Compiles YAML profiles with expression parsing and type checking
  - `CompiledVariable`: Compiled variable with parsed AST and inferred types
  - `CompiledGlobalProfile`, `CompiledItemProfile`: Compiled profile containers
  - Dependency graph construction using NetworkX for topological sorting

- **`history.py`**: Temporal history tracking for time-series expressions

#### Dependencies

**Inbound** (who depends on vfs):
- `environment`: Uses `VariableRegistry` for runtime state storage, `VFSObservationSpec` for obs_dim calculation
- `universe`: Compiler loads `VariableDef` from configs, validates schemas
- `world`: Expression evaluator accesses VFS state via `ExecutionContext.vfs`
- `effects`: Effect system reads/writes VFS variables during effect execution
- `items`: Item system uses item-scoped VFS profiles

**Outbound** (vfs depends on):
- `world.expression`: Uses expression parser, type checker, evaluator, AST nodes
- `config.vfs_profiles_config`: Pydantic configs for VFS profiles (GlobalVFSProfileConfig, etc.)
- **PyTorch**: GPU tensors for all storage (`torch.Tensor`)
- **Pydantic**: Schema validation for `VariableDef`, `ObservationField`
- **NetworkX**: Dependency graph construction for topological sorting
- **PyYAML**: Loading `variables_reference.yaml` configs

#### Patterns & Design Decisions

**1. No-Defaults Principle Enforcement**
- All variables require explicit `default` values in configs
- Prevents silent fallbacks and ensures reproducibility
- Enforced at schema validation time (Pydantic)

**2. Scope-Based Access Control**
- Three scopes: `global` (shared singleton), `agent` (per-agent batch tensor), `agent_private` (hidden from observations)
- Access control: `readable_by`, `writable_by` fields specify which systems can access
- Permissions checked at runtime: `get(var_id, reader="agent")` raises `PermissionError` if denied

**3. Mark-and-Sweep Evaluation**
- Only evaluate variables marked as `observable=True` to save computation
- Dependency tracking: Evaluates dependencies of observed variables recursively
- Falls back to EAGER mode (evaluate all) for debugging via `HAMLET_DEBUG_VFS` env var

**4. Profile-Based Item Storage**
- Item variables stored in unified `item_vfs` tensor: [max_items, max_profile_vars]
- Profile-agnostic layout: All profiles share same tensor, unused slots masked
- Mapping: `item_profile_map[profile_name][var_name] -> tensor_index`
- Enables heterogeneous item types (food, medical, tools) with different variable sets

**5. Tensor Type Safety**
- Each variable tracks `_expected_shapes` and `_expected_dtypes` at initialization
- Runtime validation on `set()`: Checks shape and dtype match expected
- Prevents silent shape mismatches that cause GPU errors

**6. Observation Dimension Stability**
- Fixed vocabulary approach: `max_items_per_agent=3`, `max_item_profiles=5`
- Guarantees constant `obs_dim` across curriculum levels for transfer learning
- Padding for inactive profiles/items maintains dimensionality

#### Integration Points

**1. VFS → Environment**
- Environment calls `registry.get("energy", reader="engine")` to read bar values
- Environment calls `registry.set("position", new_pos, writer="engine")` after movement
- Observation builder invoked at each step: `build_vfs_observation(registry, spec, batch_size, inventory)`

**2. VFS → Compiler**
- Compiler stage: Parse → Validate → Compile → Emit
- `load_variables_reference_config()` loads and validates YAML
- `VFSProfileCompiler` compiles expressions into ASTs with dependency tracking
- Compiled profiles stored in `compiled_universe` for runtime use

**3. VFS → Expression Language**
- VFS state injected into `ExecutionContext.vfs` dict
- Expressions reference variables: `vfs.energy`, `self.vfs.motivation`, `target.vfs.health`
- Type information via `vfs_types` dict: `{"target": "agent_ref"}` enables reference traversal
- Reference chains: `target.vfs.home_position` → resolve `target` (agent_ref) → traverse to agent's VFS

**4. Variable Scopes and Storage Layout**

| Scope | Storage Shape | Example | Access Pattern |
|-------|---------------|---------|----------------|
| `global` | `[]` (scalar) or `[dims]` (vector) | `time_of_day: tensor(12.5)` | Singleton, broadcast to batch in observations |
| `agent` | `[num_agents]` or `[num_agents, dims]` | `energy: tensor([1.0, 0.8, 0.9, 1.0])` | Per-agent, observable by all |
| `agent_private` | `[num_agents]` or `[num_agents, dims]` | `home_position: tensor([[3,4], [2,1], ...])` | Per-agent, hidden from agent observations |
| `item` | `[max_items, max_profile_vars]` | `item_vfs[5, 2] = 0.8` (nutrition for item 5) | Profile-based, indexed by `vfs_index` |

**5. Access Control Matrix**

| Reader/Writer | global | agent | agent_private | item |
|---------------|--------|-------|---------------|------|
| `agent` (read) | ✅ | ✅ | ❌ (hidden) | ✅ |
| `engine` (read/write) | ✅ | ✅ | ✅ | ✅ |
| `acs` (read) | ✅ | ✅ | ✅ | ✅ |
| `bac` (read/write) | ✅ | ✅ | ✅ | ✅ |
| `actions` (write) | ❌ | ✅ | ❌ | ✅ |

**6. Expression DSL Pipeline**
```
YAML Config → Parser → AST → Type Checker → Evaluator → Tensor Result
"bar.energy + 0.1" → BinaryOp(PathAccess("bar.energy"), ADD, Constant(0.1)) → "float" → tensor([...])
```

#### Confidence Level

**HIGH** - Complete understanding of:
- Schema definitions and Pydantic validation structure
- Runtime storage layout and tensor shapes for all scopes
- Access control enforcement mechanisms
- Observation building pipeline and dimension calculation
- Profile compilation with expression parsing and dependency resolution
- Integration with environment, compiler, and expression language

Evidence: Read 1,800+ lines across 7 VFS files, including complete `schema.py`, `registry.py`, `observation_builder.py`, `evaluator.py`, and partial `profiles.py`. Examined test files and config examples. VFS is production-ready with comprehensive documentation.

---

### Subsystem 2: world (Expression Language)

**Location**: `src/townlet/world/`

**Primary Responsibility**: Declarative expression language providing runtime computations for VFS variables, effects, and reward functions with GPU-native evaluation.

#### Key Components

- **`expression/parser.py`** (300+ lines): PyParsing-based expression parser
  - `ExpressionParser`: Converts expression strings to AST nodes
  - Grammar: Literals (int, float, bool, string), operators (arithmetic, logical, comparison), function calls, if-then-else, path access, index access
  - Operator precedence: POW (highest) → MUL/DIV/MOD → ADD/SUB → comparisons → logical (lowest)
  - Packrat parsing enabled for performance
  - Keywords: `true`, `false`, `and`, `or`, `not`, `if`, `then`, `else`

- **`expression/ast_nodes.py`** (150+ lines): Abstract syntax tree node definitions
  - `ASTNode`: Base class with Visitor pattern support
  - Node types: `Constant`, `Variable`, `PathAccess`, `BinaryOp`, `UnaryOp`, `FunctionCall`, `IfThenElse`, `IndexAccess`
  - `OperatorType`: Enum for operators (ADD, SUB, MUL, DIV, MOD, POW, AND, OR, NOT, EQ, NEQ, GT, LT, GTE, LTE)
  - `ASTVisitor`: Interface for traversal (Evaluator, TypeChecker, Printer)

- **`expression/evaluator.py`** (146 lines): GPU-native expression evaluation
  - `Evaluator`: ASTVisitor implementation that executes AST on PyTorch tensors
  - `visit_constant()`: Converts Python literals to `torch.Tensor`
  - `visit_variable()`: Resolves from `ExecutionContext`
  - `visit_binary_op()`: Tensor arithmetic (`+`, `-`, `*`, `/`, `%`, `**`), logical (`&`, `|`), comparison (`==`, `!=`, `<`, `>`)
  - `visit_if_then_else()`: Vectorized conditionals via `torch.where(condition, true_branch, false_branch)`
  - `visit_index_access()`: Dynamic tensor indexing (`inventory[slot_index]`)
  - Function dispatch to `FUNCTION_SPECS` registry

- **`expression/type_checker.py`** (350+ lines estimated): Static type checking before evaluation
  - `TypeChecker`: ASTVisitor for bottom-up type inference
  - Type system: `int`, `float`, `bool`, `str`, `agent_ref`, `item_ref`
  - Schema lookup: Variables and paths resolved from `schema` dict
  - Type rules: `int + int → int`, `int + float → float`, `float / int → float`
  - Reference traversal: `target.vfs.health` resolves `target` type (`agent_ref`), then traverses to agent's VFS
  - Raises `TypeCheckError` on violations (e.g., `"hello" + 5`)

- **`expression/context.py`** (300+ lines estimated): Execution context for evaluation
  - `ExecutionContext`: Runtime state container
    - `bars`: Meter values (e.g., `{"energy": tensor([batch])}`)
    - `vfs`: VFS variable state (e.g., `{"position": tensor([[x,y], ...])}`)
    - `affordances`: Affordance positions/states
    - `temporal`: Time-based values (tick count, day/night)
    - `agent_positions`, `affordance_positions`: Spatial data
    - `item_vfs`, `item_profile_map`: Item VFS storage and mappings
    - `history`: Temporal history for time-series expressions
  - `get(path)`: Resolves dotted paths to tensors
    - `"bar.energy"` → bars dict
    - `"vfs.position"` → vfs dict (agent scope)
    - `"global.vfs.time_sin"` → vfs dict (global scope)
    - `"self.bar.health"`, `"target.vfs.motivation"` → agent reference resolution
  - Reference chain resolution: `target.vfs.home_position` → `get("target")` (returns agent_ref tensor) → index into VFS

- **`expression/functions.py`** (400+ lines estimated): Built-in function registry
  - `FunctionSpec`: Function specification (name, args, return type, validation, eval_fn)
  - `FUNCTION_SPECS`: Shared registry for type checker and evaluator
  - Math: `min`, `max`, `abs`, `sqrt`, `sin`, `cos`, `exp`, `log`, `clamp`, `pow`
  - Logical: `any`, `all`
  - Aggregation: `sum`, `mean`, `count`
  - Temporal: `lag`, `moving_avg`, `rate_of_change` (require `TemporalHistory`)
  - Distance: `distance` (spatial distance between positions)
  - Type-specific: `floor`, `ceil`, `round` (float → int conversions)

- **`expression/history.py`**: Temporal history for time-series expressions
  - `TemporalHistory`: Ring buffer for historical values
  - `push(key, value)`: Store timestamped tensor
  - `get(key, steps_back)`: Retrieve value from N steps ago
  - Used by `lag()`, `moving_avg()`, `rate_of_change()` functions

- **`types/primitive.py`**: Primitive type definitions for type system

#### Dependencies

**Inbound** (who depends on world):
- `vfs`: VFS evaluator uses expression parser, type checker, evaluator for variable expressions
- `effects`: Effect compiler parses effect expressions for conditions and magnitude
- `environment.dac_engine`: DAC reward functions use expressions for dynamic reward computation
- `universe`: Compiler validates all expressions during compilation stage

**Outbound** (world depends on):
- **PyTorch**: All evaluation produces `torch.Tensor` results
- **PyParsing**: Grammar-based expression parsing
- No internal Townlet dependencies (world is low-level infrastructure)

#### Patterns & Design Decisions

**1. GPU-Native Evaluation**
- All operations return PyTorch tensors, not Python scalars
- Vectorized conditionals: `if energy < 0.2 then 1 else 0` → `torch.where(energy < 0.2, 1, 0)`
- Batch operations: Single expression evaluates across all agents simultaneously
- No Python loops over batch dimension (GPU parallelism)

**2. Visitor Pattern for AST Traversal**
- `ASTNode.accept(visitor)` delegates to visitor's `visit_*()` method
- Multiple visitors: `Evaluator` (execution), `TypeChecker` (validation), future: `Printer` (pretty-printing)
- Clean separation: Node structure vs traversal logic
- Easy to add new operations: Add visitor method, no node changes

**3. Unified Function Registry**
- `FUNCTION_SPECS` shared by type checker and evaluator
- Single source of truth for function signatures and implementations
- Type checker validates signatures: `max(int, int) → int`, `max(float, float) → float`
- Evaluator dispatches: `max(args, context) → torch.max(torch.stack(args))`
- Prevents signature drift between checker and evaluator

**4. Context-Based Evaluation**
- `ExecutionContext` encapsulates all runtime state (bars, vfs, temporal, spatial)
- No global state: Multiple evaluators can run concurrently with different contexts
- Testability: Easy to construct mock contexts for unit tests
- Isolation: Evaluation doesn't mutate context (reads only, except for function side effects)

**5. Type Safety Before Evaluation**
- Parse → Type Check → Evaluate pipeline
- Compiler catches type errors at config validation time, not runtime
- Schema-driven type checking: All variables and paths have declared types
- Prevents runtime GPU errors from shape mismatches

**6. Strict Float/Int Distinction**
- Parser uses strict regex: `1.0` → float, `1` → int
- Prevents `"42"` from parsing as float (breaks array indexing)
- Type promotions: `int + float → float`, `int * int → int`
- Index access requires int: `inventory[slot_index]` validates `slot_index` is int type

#### Integration Points

**1. Expression → VFS Evaluation Pipeline**
```
Config: "if bar.energy < 0.2 then bar.energy * 2.0 else bar.energy * 1.1"
  ↓ Parser
AST: IfThenElse(
       condition=BinaryOp(PathAccess("bar.energy"), LT, Constant(0.2)),
       true_branch=BinaryOp(PathAccess("bar.energy"), MUL, Constant(2.0)),
       false_branch=BinaryOp(PathAccess("bar.energy"), MUL, Constant(1.1))
     )
  ↓ Type Checker (schema: {"bar.energy": "float"})
Type: "float"
  ↓ Evaluator (context: {bars: {"energy": tensor([0.1, 0.5, 0.9])}})
Result: tensor([0.2, 0.55, 0.99])  # Vectorized over batch
```

**2. Path Resolution in ExecutionContext**

| Path | Resolution | Example Tensor |
|------|------------|----------------|
| `bar.energy` | `context.bars["energy"]` | `tensor([1.0, 0.8, 0.9])` [batch] |
| `vfs.position` | `context.vfs["position"]` | `tensor([[3,4], [2,1], [5,6]])` [batch, 2] |
| `global.vfs.time_sin` | `context.vfs["time_sin"]` | `tensor(0.707)` [] (singleton) |
| `self.bar.health` | `context.bars["health"][self_indices]` | `tensor([1.0, 0.9, 0.8])` (indexed) |
| `target.vfs.motivation` | `context.vfs["target"]` → agent_ref → index into `vfs["motivation"]` | Dynamic indexing |

**3. Reference Traversal**
- `target` variable has type `agent_ref` (stored in `vfs_types` dict)
- Expression: `target.vfs.health`
  1. Resolve `target`: `context.vfs["target"]` → `tensor([2, 0, 3])` (agent indices)
  2. Validate indices: Check `-1 < indices < num_agents`
  3. Resolve `health`: `context.vfs["health"][indices]` → Gather health values for target agents
- Enables agent-to-agent interactions: "Heal target if target.bar.health < 0.5"

**4. Temporal History Integration**
- VFS evaluator creates `TemporalHistory` if `history_spec` provided
- `history_spec`: `{"bar.energy": 10, "vfs.position": 5}` (store last N timesteps)
- Expressions: `lag(bar.energy, 2)` → energy from 2 steps ago
- `moving_avg(vfs.position, 5)` → Average position over last 5 steps
- Use case: Velocity estimation, momentum-based effects, rate-of-change triggers

**5. Function Evaluation Example: `distance`**
```python
# Expression: "distance(self.vfs.position, target.vfs.position)"
# Context: agent_positions = [[1,2], [3,4]], target = [1, 0] (agent 1 looking at agent 0)
def eval_distance(args, context, ast_args):
    pos1 = args[0]  # self.vfs.position → [[3,4]] (agent 1)
    pos2 = args[1]  # target.vfs.position → [[1,2]] (agent 0)
    return torch.norm(pos1 - pos2, dim=-1)  # Euclidean distance
# Result: tensor([2.828]) (distance from [3,4] to [1,2])
```

**6. Vectorized Conditionals**
```python
# Expression: "if bar.energy < 0.5 then -0.1 else 0.0"
# Bars: energy = [0.2, 0.6, 0.9]
condition = torch.tensor([True, False, False])
true_branch = torch.tensor([-0.1, -0.1, -0.1])
false_branch = torch.tensor([0.0, 0.0, 0.0])
result = torch.where(condition, true_branch, false_branch)
# Result: [-0.1, 0.0, 0.0] (only first agent gets penalty)
```

#### Confidence Level

**HIGH** - Complete understanding of:
- Parser grammar and AST construction (read 200+ lines of grammar rules)
- AST node types and Visitor pattern implementation
- Evaluator tensor operations for all node types
- Type checker schema-based validation and type inference rules
- ExecutionContext path resolution and reference traversal
- Function registry architecture and integration with type checker
- Temporal history for time-series expressions

Evidence: Read 800+ lines across parser, AST nodes, evaluator, type checker, context, and functions. Examined integration with VFS evaluator and DAC engine. Expression language is production-ready, GPU-optimized, and type-safe.

---

### Subsystem 3: substrate (Spatial Substrates)

**Location**: `src/townlet/substrate/`

**Primary Responsibility**: Abstract spatial substrate system providing pluggable implementations for agent positioning, movement, distance computation, and observation encoding.

#### Key Components

- **`base.py`** (400+ lines): Abstract interface for all substrates
  - `SpatialSubstrate`: ABC defining substrate contract
  - **Properties**:
    - `position_dim`: Dimensionality (0=aspatial, 2=2D, 3=3D, N=N-dimensional)
    - `position_dtype`: Tensor dtype (`torch.long` for grids, `torch.float32` for continuous)
    - `action_space_size`: Number of discrete actions (substrate-specific)
  - **Abstract methods**:
    - `get_default_actions()`: Returns substrate's action space (movement + INTERACT + WAIT)
    - `initialize_positions(num_agents, device)`: Random initial positions
    - `apply_movement(positions, deltas)`: Movement with boundary handling
    - `compute_distance(pos1, pos2)`: Distance metric (Manhattan, Euclidean, Chebyshev)
    - `encode_observation(positions, affordances)`: Position encoding for observations
    - `get_observation_dim()`: Observation dimensionality
    - `normalize_positions(positions)`: Normalize to [0,1] (relative encoding)
  - **Canonical action ordering contract**: Movement actions → INTERACT → WAIT (enables meta-action identification by position)

- **`grid2d.py`** (300+ lines): 2D square grid substrate
  - Coordinate system: `[x, y]` where x=column, y=row, origin=(0,0) at top-left
  - Boundaries: `clamp` (hard walls), `wrap` (toroidal), `bounce` (elastic), `sticky` (stay in place)
  - Distance metrics: `manhattan` (L1), `euclidean` (L2), `chebyshev` (L∞)
  - Observation encoding: `relative` (normalized [0,1]), `scaled` (grid dimensions), `absolute` (raw coordinates)
  - Diagonals: 8 actions if enabled (UP, DOWN, LEFT, RIGHT, UP_LEFT, UP_RIGHT, DOWN_LEFT, DOWN_RIGHT), else 4
  - Action space: [movements, INTERACT, WAIT] (8-10 actions total)

- **`grid3d.py`** (400+ lines): 3D cubic grid substrate
  - Coordinate system: `[x, y, z]` (3D Cartesian)
  - Same boundaries and distance metrics as Grid2D
  - Additional actions: `UP_Z`, `DOWN_Z` (vertical movement)
  - Action space: [movements (10), INTERACT, WAIT] (12 actions total)
  - POMDP support: `vision_range <= 2` (3D window size explodes for large ranges)

- **`gridnd.py`** (500+ lines): N-dimensional hypergrid substrate
  - Coordinate system: `[d0, d1, ..., dN]` (arbitrary dimensions 4-100)
  - Action space: `[DIM0_NEG, DIM0_POS, DIM1_NEG, DIM1_POS, ..., INTERACT, WAIT]` (2N+2 actions)
  - Example: 7D grid → 16 actions (14 movement + INTERACT + WAIT)
  - POMDP: **Not supported** (N≥4 window too large for memory)
  - Use case: High-dimensional optimization problems, abstract state spaces

- **`continuous.py`** (600+ lines): 1D/2D/3D continuous substrates
  - `Continuous1DSubstrate`, `Continuous2DSubstrate`, `Continuous3DSubstrate`
  - Coordinate system: Float coordinates with configurable bounds (e.g., [-10.0, 10.0])
  - Position dtype: `torch.float32` (enables sub-cell precision)
  - Movement: `movement_delta` parameter (e.g., 0.1 per step)
  - Action discretization: Fixed directions (8 for 2D: N, NE, E, SE, S, SW, W, NW)
  - Observation encoding: Relative (normalized), scaled, or absolute
  - Interaction radius: Distance threshold for affordance interaction

- **`continuousnd.py`** (400+ lines): N-dimensional continuous substrate
  - Arbitrary dimensions (4-100) with float coordinates
  - Action space: 2N directions (positive/negative along each axis)
  - Use case: High-dimensional continuous control (physics simulation, robotics)

- **`aspatial.py`** (150+ lines): No spatial substrate (pure state machine)
  - `position_dim = 0`: No positioning concept
  - Action space: `[INTERACT, WAIT]` (2 actions, no movement)
  - Distance: Always 0 (no spatial meaning)
  - Observation: Empty tensor `[batch, 0]`
  - Philosophy: "Meters (bars) are the true universe; positioning is optional overlay"
  - Use case: Abstract planning, resource management without navigation

- **`factory.py`** (153 lines): Substrate factory for instantiation
  - `SubstrateFactory.build(config, device)`: Creates substrate from Pydantic config
  - Maps `SubstrateConfig.type` to concrete implementations:
    - `"grid"` + `topology="square"` → `Grid2DSubstrate`
    - `"grid"` + `topology="cubic"` → `Grid3DSubstrate`
    - `"continuous"` + `dimensions=2` → `Continuous2DSubstrate`
    - `"gridnd"` → `GridNDSubstrate`
    - `"continuousnd"` → `ContinuousNDSubstrate`
    - `"aspatial"` → `AspatialSubstrate`

#### Dependencies

**Inbound** (who depends on substrate):
- `environment`: Uses substrate for position initialization, movement application, distance computation, observation encoding
- `universe`: Compiler validates substrate configs, computes `action_space_size`
- `config.stratum_config`: `SubstrateConfig` Pydantic DTOs consumed by factory
- `demo`: Inference server queries substrate type for frontend rendering mode (spatial vs aspatial)

**Outbound** (substrate depends on):
- **PyTorch**: All position tensors, movement, distance ops
- `environment.action_config`: `ActionConfig` DTOs for `get_default_actions()`
- `environment.affordance_layout`: `iter_affordance_positions()` for affordance placement
- No dependencies on vfs, world, or other high-level subsystems (substrate is low-level infrastructure)

#### Patterns & Design Decisions

**1. Conceptual Agnosticism**
- Don't assume 2D, Euclidean, or grid-based
- Support: 1D-100D, discrete/continuous, spatial/aspatial
- Design principle: "The meters are the universe, positioning is optional"
- Aspatial substrate proves positioning is not fundamental

**2. Pluggable Substrate System**
- Abstract base class defines contract
- Environment is substrate-agnostic: Calls abstract methods, doesn't inspect concrete type
- Factory pattern: Configuration-driven instantiation
- Transfer learning: Fixed observation vocabulary across substrates (where possible)

**3. Canonical Action Ordering**
- All substrates emit actions in same order: [movements, INTERACT, WAIT]
- `actions[-2]` always INTERACT, `actions[-1]` always WAIT
- Downstream systems identify meta-actions by position, not name
- Aspatial exception: No movements, only `[INTERACT, WAIT]`

**4. Boundary Mode Diversity**
- **Clamp**: Hard walls (current HAMLET behavior)
- **Wrap**: Toroidal (Pac-Man style, infinite loop)
- **Bounce**: Elastic reflection (billiards)
- **Sticky**: Agents stick to walls (no movement when out of bounds)
- Each mode has different pedagogical value (learning boundaries, wraparound navigation)

**5. Distance Metric Configurability**
- **Manhattan** (L1): |x1-x2| + |y1-y2| (grid distance, 4-connectivity)
- **Euclidean** (L2): sqrt((x1-x2)² + (y1-y2)²) (straight-line distance)
- **Chebyshev** (L∞): max(|x1-x2|, |y1-y2|) (king's move chess, 8-connectivity)
- Affects affordance proximity, reward shaping, strategic planning

**6. Observation Encoding Modes**
- **Relative** (default): Normalized [0,1] coordinates (best for transfer learning, required for POMDP)
- **Scaled**: Coordinates scaled to grid dimensions [0, grid_size] (value range conveys grid size)
- **Absolute**: Raw unnormalized coordinates (for physical simulation)
- All modes produce **identical obs_dim** (just value range changes, not dimensions)

**7. Type Safety via position_dtype**
- Grids: `torch.long` (integer coordinates)
- Continuous: `torch.float32` (float coordinates)
- Prevents dtype mismatches: `apply_movement()` casts deltas to correct type
- Enables mixed substrate types without GPU dtype errors

#### Integration Points

**1. Substrate → Environment Integration**
```python
# Environment initialization
substrate = SubstrateFactory.build(substrate_config, device)
positions = substrate.initialize_positions(num_agents, device)

# Each step
movement_deltas = action_to_delta[actions]  # [batch, position_dim]
new_positions = substrate.apply_movement(positions, movement_deltas)

# Distance computation
distances = substrate.compute_distance(agent_positions, affordance_position)
within_range = distances < interaction_radius

# Observation encoding
position_obs = substrate.encode_observation(positions, affordances)
# Concatenated with bars, meters, affordances → full observation
```

**2. Substrate → Action Space**
- Substrate provides default actions: `substrate.get_default_actions()`
- `ActionSpaceBuilder` merges with custom actions from `enabled_actions.yaml`
- Global vocabulary ensures transfer learning: All levels see same action space
- Curriculum: L0 might only enable 2 affordances, L1 enables all 14, but action space remains fixed

**3. Substrate → Observation Dimensions**

| Substrate | position_dim | obs_dim (from substrate) | Example Shape |
|-----------|--------------|--------------------------|---------------|
| Grid2D (8×8, relative) | 2 | 2 (normalized position) | [batch, 2] |
| Grid3D (8×8×3, relative) | 3 | 3 (normalized position) | [batch, 3] |
| GridND (7D, 5×5×5×5×5×5×5) | 7 | 7 (normalized position) | [batch, 7] |
| Continuous2D | 2 | 2 (normalized position) | [batch, 2] |
| Aspatial | 0 | 0 (no position) | [batch, 0] |

Total `obs_dim` = `substrate.get_observation_dim()` + bars + meters + affordances + temporal

**4. Substrate-Specific Behaviors**

**Grid2D: Diagonal Movement**
- `enable_diagonals=True`: 8 actions (4 cardinal + 4 diagonal)
- `enable_diagonals=False`: 4 actions (cardinal only)
- Diagonal cost: Same as cardinal (Euclidean distance would be √2, but discrete grid treats as 1)

**Continuous: Discretized Actions**
- Continuous space with discrete action set (8 directions for 2D)
- Each action: `position += direction_vector * movement_delta`
- `movement_delta`: Step size (e.g., 0.1 → 10 steps to cross unit square)
- Enables RL algorithms designed for discrete actions (DQN) on continuous substrates

**Aspatial: No Movement**
- Position tensor: `[batch, 0]` (empty, but preserves batch dimension)
- `apply_movement()`: No-op (returns unchanged positions)
- `compute_distance()`: Always 0 (no spatial meaning)
- Affordances: "Everywhere and nowhere" (interaction doesn't require proximity)

**5. POMDP Support Validation**

| Substrate | POMDP Support | Rationale |
|-----------|---------------|-----------|
| Grid2D | ✅ (vision_range ≤ 10) | 5×5 window = 25 cells (manageable) |
| Grid3D | ✅ (vision_range ≤ 2) | 5×5×5 window = 125 cells (large, but GPU-feasible) |
| GridND (N≥4) | ❌ | N-dimensional window explodes (5^N cells for vision_range=2) |
| Continuous | ✅ | Continuous window (filter by radius, not discrete cells) |
| Aspatial | ✅ (special case) | No position → no partial observability (always fully observable) |

**6. Substrate Factory Pattern**
```python
# Config: substrate.yaml
substrate:
  type: grid
  grid:
    width: 8
    height: 8
    topology: square
    boundary: clamp
    distance_metric: manhattan
    observation_encoding: relative
    diagonals: true

# Factory instantiation
config = load_substrate_config(Path("substrate.yaml"))
substrate = SubstrateFactory.build(config, device=torch.device("cuda"))
# Returns: Grid2DSubstrate(8, 8, clamp, manhattan, relative, square, diagonals=True)
```

#### Confidence Level

**HIGH** - Complete understanding of:
- Abstract substrate interface and contract (read entire `base.py`)
- Grid2D implementation with boundaries, distance metrics, observation encoding (read 150+ lines)
- Substrate factory instantiation logic (read entire `factory.py`)
- Aspatial substrate philosophy and implementation (read entire file)
- Action space canonical ordering and meta-action identification
- Observation encoding modes and dimension stability
- POMDP support validation logic
- Integration with environment, action space builder, compiler

Evidence: Read 1,500+ lines across 8 substrate files (base, grid2d, grid3d, gridnd, continuous, continuousnd, aspatial, factory). Examined config schemas and integration tests. Substrate system is production-ready, pedagogically diverse, and transfer learning-friendly.

---

## Summary: Group 3 State Systems

**Total Lines of Code**: ~8,300 lines across 3 subsystems

**Key Architectural Insight**: State Systems form the **declarative runtime foundation** of Townlet:
- **VFS**: Declarative state space (what variables exist, who can access them)
- **World**: Declarative computations (how variables are derived from expressions)
- **Substrate**: Declarative space (where agents exist, how they move)

All three subsystems emphasize:
1. **Configuration-driven behavior**: YAML configs → compiled artifacts → runtime execution
2. **GPU-native operations**: PyTorch tensors throughout, no CPU loops
3. **Type safety**: Pydantic validation (VFS), static type checking (world), dtype enforcement (substrate)
4. **Pluggability**: Abstract interfaces (SpatialSubstrate), factory patterns (SubstrateFactory), registry patterns (FUNCTION_SPECS)

**Cross-Subsystem Integration**:
- VFS expressions evaluated via world.expression language
- Substrate positions stored in VFS variables (agent scope)
- Expression context accesses both VFS state and substrate spatial data
- All three subsystems orchestrated by `environment.VectorizedHamletEnv`

**Production Readiness**: All three subsystems are **production-ready** with comprehensive test coverage, documentation, and real-world usage in curriculum levels L0-L3.


---

## Group 4: Game Mechanics

**Purpose**: Game logic systems - effect system and item system for agent interactions

**Subsystems**: effects, items

### Subsystem 1: effects

**Location**: `src/townlet/effects/`

**Primary Responsibility**: Declarative effect system with compile-time validation and runtime execution. Effects are temporal state modifications (buffs/debuffs, cascades, triggers) defined in YAML and compiled into GPU-native command pipelines. Provides a domain-specific language for game mechanics without hardcoded Python logic.

#### Key Components

- `schema.py`: AST node types and effect definitions
  - `CommandType` enum: 12 command types (MODIFY, SPAWN_EFFECT, SPAWN_ITEM, SAMPLE, IF, FOR_EACH, SWITCH, REDUCE, PARALLEL, DELAY, TRIGGER_CASCADE)
  - `CommandNode` dataclass: AST representation with pre-compiled expression ASTs for runtime performance
  - `EffectDefinition`: Lightweight effect metadata for tests/benchmarks

- `parser.py`: YAML config → AST transformation
  - `CommandParser`: Parses `CommandConfig` DTOs to `CommandNode` AST
  - Handles nested structures (if/then/else, for_each loops, switch/case)
  - No validation at this stage (pure parsing)

- `compiler.py`: AST validation with expression type checking
  - `CommandCompiler`: Validates commands against type schema (e.g., `{"target.bar.energy": "float"}`)
  - Pre-compiles expression ASTs using `ExpressionParser` and `TypeChecker` from world subsystem
  - Enforces constraints: nested for_each prohibited, delay requires time_enabled, parallel branches must have disjoint writes
  - Stores compiled ASTs in `CommandNode` for zero-cost runtime evaluation

- `executor.py`: Runtime command execution engine
  - `CommandExecutor`: Executes pre-compiled `CommandNode` commands against `ExecutionContext`
  - NEVER parses expressions at runtime (all ASTs pre-compiled by compiler)
  - Handles target/self prefix resolution via `_TargetAwareExecutionContext`
  - Implements all 12 command types with GPU tensor operations
  - Cascade depth tracking (MAX_CASCADE_DEPTH=10) to prevent infinite spawn loops

- `manager.py`: Effect lifecycle management
  - `EffectManager`: Manages active effects across all scopes (global, agent, item, affordance)
  - `ActiveEffect` dataclass: Runtime effect instance with intensity, duration, elapsed_ticks
  - Reapply policies: RENEW (reset duration), MERGE (accumulate intensity), REPLACE (cancel old), STACK (create new instance)
  - Executes on_spawn, on_tick, on_despawn, on_interrupt hooks via CommandExecutor
  - Integrates with scheduler for delayed commands

- `scheduler.py`: Tick-aligned command scheduler
  - `Scheduler`: Tick-based scheduler for DELAY commands
  - `ScheduledItem` dataclass: Commands + due_tick + scope/entity_id
  - Caps: MAX_DELAY_TICKS=1000, MAX_SCHEDULED_ITEMS=10000
  - Cancellation support for scope/entity cleanup

- `catalog.py`: Effect catalog compilation
  - `EffectCatalog`: Maps effect IDs to `CompiledEffect` definitions
  - `CompiledEffect`: Pre-compiled effect with validated command pipelines
  - `from_config()` factory: Parses + compiles effects from `EffectsConfig`
  - Deterministic effect indexing for observation encoding

- `context.py`: Execution context for command evaluation
  - `ExecutionContext`: Runtime state for command execution (bars, vfs_registry, self_index, target_index, effect, spawn_depth, agent_positions, scheduler, etc.)
  - Path resolution: `bar.*`, `vfs.*`, `target.*`, `self.*`, `affordance.*.available`
  - Item-scoped VFS routing when `self_is_item=True`
  - Context copying for nested command execution (if/for_each)

- `collections.py`: Collection resolvers for for_each commands
  - `COLLECTION_RESOLVERS`: Registry of named collections (all_agents, nearby_agents, inventory_items, active_effects)
  - `resolve_collection()`: Resolves collection name to list of indices
  - MAX_COLLECTION_SIZE=256 cap to prevent performance issues

#### Dependencies

**Inbound** (who depends on this subsystem):
- `environment` - Executes affordance effects, item interaction effects, meter cascades
- `items` - Item interactions compile to effect commands (on_pickup, on_use, on_drop)
- `universe` - Compiles effect definitions from YAML configs

**Outbound** (this subsystem depends on):
- `world` - Expression language (parser, type checker, evaluator) for command expressions
- `vfs` - Variable registry for state access/mutation in commands
- `config` - `EffectsConfig`, `CommandConfig` DTOs for schema validation

**External libraries**:
- PyTorch - Tensor operations, GPU execution
- Pydantic - Configuration validation (via config subsystem)

#### Patterns & Design Decisions

**Pattern 1: Compiler-Driven Validation**
- YAML → Parser (AST) → Compiler (type checking + AST pre-compilation) → Runtime (zero-cost execution)
- Rationale: Catch errors at compile-time, not training-time
- Performance: Pre-compiled ASTs eliminate runtime parsing overhead

**Pattern 2: Pre-Compiled Expression ASTs**
- CommandCompiler stores compiled expression ASTs in CommandNode fields (e.g., `value_ast`, `condition_ast`)
- CommandExecutor NEVER parses expressions (only evaluates pre-compiled ASTs)
- Rationale: Eliminate parsing overhead in hot path (effects execute every tick)

**Pattern 3: Scoped Effect Storage**
- Effects stored by scope (global, agent, item, affordance)
- Rationale: Fast lookup without scanning all effects
- Trade-off: More complex storage management

**Pattern 4: Reapply Policies**
- RENEW: Reset duration (for short buffs)
- MERGE: Accumulate intensity (for stacking effects)
- REPLACE: Cancel old, create new (for conflicting buffs)
- STACK: Allow multiple instances (for periodic triggers)
- Rationale: Different game mechanics need different reapply semantics

**Pattern 5: Cascade Depth Tracking**
- spawn_effect increments `spawn_depth` to prevent infinite spawn loops
- MAX_CASCADE_DEPTH=10 prevents stack overflow
- Rationale: Effects can spawn effects (e.g., poison spawns damage effect)

**Pattern 6: Tick-Aligned Scheduling**
- Scheduler stores commands by due_tick for O(1) retrieval
- Rationale: Deterministic timing for delayed effects (e.g., "heal after 5 ticks")

#### Integration Points

**Effect Lifecycle**:
1. **Definition** (compile-time): YAML → Parser → Compiler → EffectCatalog
2. **Spawn** (runtime): EffectManager.spawn_effect() → on_spawn commands → ActiveEffect created
3. **Tick** (runtime): EffectManager.tick() → on_tick commands → duration decremented
4. **Despawn** (runtime): duration_remaining ≤ 0 → on_despawn commands → effect removed
5. **Interrupt** (runtime): Manual cancel or reapply policy → on_interrupt commands

**Command Execution Flow**:
1. CommandExecutor.execute() receives CommandNode + ExecutionContext
2. Dispatcher routes by CommandType (MODIFY, IF, FOR_EACH, etc.)
3. Evaluator.evaluate() runs pre-compiled AST against context
4. Result mutates context state (bars, vfs, spawn effects/items)

**Integration with VFS**:
- Effects read/write VFS variables via `context.vfs_registry`
- Supports agent-scoped (`vfs.motivation`), item-scoped (`self.vfs.durability`), and global (`vfs.day_count`) variables
- VFS reference traversal: `vfs.ally_ref.bar.health` (follow agent_ref to read ally's health)

**Integration with Items**:
- Effects can spawn items via SPAWN_ITEM command
- Items can trigger effects via on_pickup/on_use/on_drop hooks
- For_each can iterate over inventory_items collection

**Integration with Environment**:
- Affordance interactions execute effects (e.g., "eat food" → modify bar.energy)
- Meter cascades implemented as effects (e.g., low energy → reduce fitness)
- Effects update bars tensor in-place (environment reads mutated state)

#### Confidence Level

**HIGH**: Complete source code analysis of all 9 modules. Effect system is well-documented with clear separation between compile-time (parser, compiler, catalog) and runtime (executor, manager, scheduler). Integration points with VFS, items, and environment are explicit. The pre-compiled AST pattern is a key performance optimization.

---

### Subsystem 2: items

**Location**: `src/townlet/items/`

**Primary Responsibility**: World object system with VFS-backed state, inventory mechanics, and effect-based interactions. Items are physical objects with position, durability/state, and custom verbs (pickup, use, drop, custom commands). Supports exclusive (single-holder) and shared (multi-holder) items.

#### Key Components

- `instance.py`: Runtime item representation
  - `ItemInstance` dataclass: Runtime instance with position, vfs_index, vfs_profile, spawn_tick, duration_total, duration_remaining, holder_agent_ids
  - `tick()`: Decrements duration_remaining (item aging/spoiling)
  - `is_expired()`: Check if item should despawn
  - Exclusive vs shared semantics: exclusive items leave world when picked up, shared items stay in place

- `manager.py`: Item lifecycle and spawning
  - `ItemManager`: Central manager for all items in world
  - `CompiledItemType`: Item type with pre-compiled effect commands (on_pickup, on_use, on_drop, local_commands, inventory_commands)
  - Compiles item interactions using `CommandCompiler` from effects subsystem
  - VFS slot allocation: Fixed-size pool (max_items) with free slot tracking
  - Cooldown tracking: Prevents spam spawning (item_type → next_spawn_tick)
  - Appearance config: Periodic respawning with placement strategies (random, fixed, grid, scripted)
  - Spawn schedules: periodic, poisson, normal, time_window, scripted
  - Item registries: `active_items` (on grid), `held_items` (in inventories)

- `inventory.py`: Agent inventory storage
  - `InventoryState`: GPU tensor-based inventory ([batch, max_items_per_agent] of instance IDs)
  - Slots storage: -1 = empty, ≥0 = instance_id
  - Item metadata: dict[instance_id → ItemInstance] for lookup
  - `add_item()`: DENY_PICKUP policy if full (no automatic dropping)
  - `remove_item()`: Clear slot, update holder_agent_ids
  - `has_item()`: Check if agent already holds instance (prevent duplicates)

- `action_handlers.py`: Item action execution
  - `ItemActionHandler`: Handles GET, USE_SLOT_N, DROP_SLOT_N actions
  - `_execute_interaction()`: Executes effect commands for item interactions
  - ExecutionContext mapping: `target` = agent performing action, `self` = item (can access `self.vfs.durability`)
  - Custom verb dispatch: local (item at agent position) vs inventory (item in agent inventory)
  - Action masking: `compute_custom_action_masks()` disables unavailable custom verbs

#### Dependencies

**Inbound** (who depends on this subsystem):
- `environment` - Handles item actions (GET, USE_SLOT_N, DROP_SLOT_N, custom verbs)
- `effects` - Effects can spawn items via SPAWN_ITEM command
- `universe` - Compiles item catalog from items.yaml

**Outbound** (this subsystem depends on):
- `effects` - Item interactions compile to effect commands (CommandCompiler, CommandExecutor)
- `vfs` - Item state stored in item-scoped VFS (e.g., durability, spoilage)
- `config` - `ItemsCatalogConfig`, `ItemTypeConfig` DTOs

**External libraries**:
- PyTorch - Tensor storage for inventory slots
- Pydantic - Configuration validation

#### Patterns & Design Decisions

**Pattern 1: VFS-Backed Item State**
- Each item has a `vfs_index` into `item_vfs` tensor ([max_items, num_item_vars])
- Item state (durability, spoilage, power) stored in VFS, not ItemInstance
- Rationale: GPU-native state management, uniform access pattern
- VFS profiles: Each item type references a vfs_profile (e.g., "food_stats", "weapon_stats")

**Pattern 2: Exclusive vs Shared Items**
- Exclusive items: Single holder, leave world when picked up (e.g., sword)
- Shared items: Multiple holders, stay in world when picked up (e.g., bonfire)
- Rationale: Support both "pickup" and "use in place" mechanics
- Implementation: `exclusive` boolean + `holder_agent_ids` set

**Pattern 3: Fixed-Size VFS Slot Pool**
- Pre-allocate max_items VFS slots at environment creation
- Track free slots with `vfs_free_slots` set
- Rationale: Avoid dynamic memory allocation during training (GPU compatibility)
- Trade-off: Hard cap on max_items, but predictable memory usage

**Pattern 4: Effect-Based Interactions**
- Item interactions compile to effect commands (MODIFY, SPAWN_EFFECT, etc.)
- Rationale: Reuse effect system's expression language, no hardcoded Python logic
- Example: Apple on_use → `[{modify: "bar.energy", value: "bar.energy + 0.2"}]`

**Pattern 5: Dual Item Registry**
- `active_items`: Items on grid (spatially positioned)
- `held_items`: Items in inventories (no position, but still tick)
- Rationale: Items continue to age/spoil when held (held apple still rots)

**Pattern 6: Appearance Config with Scheduling**
- Spawn rules: count, max_total, placement (random/fixed/grid/scripted), schedule (periodic/poisson/normal/time_window/scripted)
- Respawn timers: Track per-item-type respawn tick
- Rationale: Declarative item spawning without hardcoded spawn logic

**Pattern 7: Custom Verb System**
- Items define custom commands (e.g., "sharpen" for sword, "read" for book)
- Action naming: `item_type__command_name__scope` (e.g., "sword__sharpen__inventory")
- Scope: `local` (item at agent position) vs `inventory` (item in agent inventory)
- Rationale: Extensible interaction system without hardcoding verbs

#### Integration Points

**Item Lifecycle**:
1. **Definition** (compile-time): YAML → ItemManager compiles with CommandCompiler → CompiledItemType
2. **Spawn** (runtime): ItemManager.spawn_item() → allocate VFS slot → initialize VFS state → ItemInstance created
3. **Pickup** (runtime): GET action → add_item() → lift_item() (if exclusive) → on_pickup effects
4. **Use** (runtime): USE_SLOT_N action → on_use effects (item stays in inventory)
5. **Drop** (runtime): DROP_SLOT_N action → remove_item() → place_item() → on_drop effects
6. **Tick** (runtime): ItemManager.tick() → item.tick() (age/spoil) → despawn if expired
7. **Despawn** (runtime): despawn_item() → free VFS slot → set respawn timer

**Inventory Integration**:
- InventoryState stores instance IDs in GPU tensor ([batch, max_items_per_agent])
- ItemActionHandler reads inventory slots to find items for USE_SLOT_N actions
- DENY_PICKUP policy: add_item() returns False if inventory full

**VFS Integration**:
- Item state stored in `item_vfs` tensor ([max_items, num_item_vars])
- VFS profiles define item-scoped variables (e.g., "food_stats" → durability, spoilage)
- Item effects access item state via `self.vfs.durability` (where `self` = item)
- Agent effects access item state via `vfs.item_ref.vfs.durability` (VFS reference traversal)

**Effect Integration**:
- Item interactions (on_pickup, on_use, on_drop, custom commands) compile to effect commands
- ItemActionHandler executes commands via CommandExecutor
- ExecutionContext: `target` = agent, `self` = item (enables `target.bar.energy` and `self.vfs.durability`)
- Effects can spawn items via SPAWN_ITEM command (e.g., "eat apple" → spawn "apple core")

**Action Space Integration**:
- Base actions: GET (pickup), USE_SLOT_N (use item in slot N), DROP_SLOT_N (drop item from slot N)
- Custom actions: Dynamic action space based on compiled item types (e.g., "sword__sharpen__inventory")
- Action masking: Disable unavailable custom verbs (e.g., mask "sharpen" if no sword in inventory)

**Environment Integration**:
- Environment calls ItemManager.tick() every step (item aging)
- Environment calls ItemManager.process_respawns() every step (respawn expired items)
- ItemActionHandler.handle_*_action() called from environment when agent performs item action

#### Confidence Level

**HIGH**: Complete source code analysis of all 4 modules. Item system is well-integrated with effects (all interactions compile to effect commands) and VFS (item state stored in item-scoped VFS). The exclusive/shared item pattern is unique and well-implemented. Appearance config with scheduling provides flexible spawning mechanics.

---

## Summary: Game Mechanics Group

**Total Subsystems**: 2 (effects, items)

**Key Insights**:
1. **Effect System = DSL for Game Mechanics**: Effects provide a declarative domain-specific language (12 command types) for defining game mechanics without hardcoded Python logic. All interactions (affordances, items, cascades) compile to effect commands.

2. **Pre-Compiled AST Performance**: CommandCompiler pre-compiles expression ASTs at config load time, eliminating parsing overhead in the hot path (effects execute every tick). This is a critical performance optimization.

3. **Items Built on Effects**: Item interactions (on_pickup, on_use, on_drop, custom verbs) compile to effect commands. This creates a unified execution model: all game mechanics flow through the effect executor.

4. **VFS-Backed Item State**: Item state (durability, spoilage, power) stored in VFS, not ItemInstance. This provides GPU-native state management and uniform access patterns.

5. **Lifecycle Hooks**: Both effects and items provide lifecycle hooks (on_spawn/on_pickup, on_tick, on_despawn/on_drop, on_interrupt). This enables complex temporal behaviors (e.g., poison effect that spawns damage effect every 3 ticks).

6. **Scoped Storage**: Effects and items use scoped storage (global, agent, item, affordance) for fast O(1) lookups without scanning all entities.

**Architectural Pattern**: Effects = Computation Engine, Items = Stateful Objects. Effects define "what happens" (modify meters, spawn entities, trigger cascades), items define "what exists" (physical objects with position and state). Both integrate via the ExecutionContext/CommandExecutor abstraction.

**Integration Complexity**: MEDIUM-HIGH. Effects and items are tightly coupled (items compile to effects), but both have clear interfaces (EffectCatalog, ItemManager) that environment/universe consume. The ExecutionContext abstraction provides clean separation between "what to execute" (CommandNode) and "runtime state" (bars, vfs, positions).

---

## Group 5: Auxiliary Systems

**Purpose**: Supporting systems for training - curriculum strategies, exploration mechanisms, demo infrastructure, and recording tools

**Subsystems**: curriculum, exploration, demo, recording

### Subsystem 1: curriculum

**Location**: `src/townlet/curriculum/`

**Primary Responsibility**: Manages training difficulty progression through adaptive curriculum strategies that adjust environment complexity based on agent performance metrics (survival rate, learning progress, policy convergence).

#### Key Components

- `base.py`: `CurriculumManager` abstract base class defining the curriculum interface with methods for batch decisions, checkpointing, and state restoration
- `static.py`: `StaticCurriculum` - trivial implementation that returns fixed difficulty for all agents (baseline/testing)
- `adversarial.py`: `AdversarialCurriculum` - auto-tuning curriculum with 5-stage progression (Stage 1: 2 meters @ 20% depletion → Stage 5: 6 meters @ 100% + sparse rewards). Uses `PerformanceTracker` for GPU-based per-agent metrics tracking
- `factory.py`: `build_curriculum()` - factory function that selects curriculum implementation based on TrainingV2Config strategy field

#### Dependencies

**Inbound**:
- `population` - calls `get_batch_decisions()` to determine environment configuration per episode
- `demo.runner` - instantiates curriculum via factory, saves/loads curriculum state in checkpoints

**Outbound**:
- `training.state` - uses `BatchedAgentState`, `CurriculumDecision` DTOs
- `config.training_v2_config` - reads TrainingV2Config for curriculum parameters

**External libraries**: PyTorch (GPU tensors for performance tracking), PyYAML (config loading)

#### Patterns & Design Decisions

**5-Stage Adversarial Progression**: AdversarialCurriculum implements fixed 5-stage progression with hardcoded configurations (STAGE_CONFIGS list). Each stage adds complexity:
- Stage 1: energy + hygiene only, 20% depletion, shaped rewards
- Stage 2: add satiation, 50% depletion
- Stage 3: add money, 80% depletion
- Stage 4: all 6 meters, 100% depletion
- Stage 5: sparse rewards (graduation milestone)

**Multi-Signal Advancement**: Agents advance when ALL three conditions met:
1. High survival rate (>70%)
2. Positive learning progress (reward improvement)
3. Low entropy (<0.5) - converged policy

**Retreat Mechanism**: Agents retreat when struggling (survival <30% OR negative learning). Prevents agents from being stuck at too-hard difficulty.

**GPU-Native Performance Tracking**: `PerformanceTracker` uses PyTorch tensors for all metrics (episode_rewards, episode_steps, agent_stages) to minimize CPU-GPU transfers.

**Difficulty Mapping**: v2.1 configuration allows mapping internal stage (1-5) to external difficulty_level ∈ [min_difficulty, max_difficulty] without changing advancement logic.

#### Integration Points

**Curriculum affects training difficulty**:
- Returns `CurriculumDecision` with active_meters list, depletion_multiplier, reward_mode per agent
- Environment reads decisions to configure meter depletion rates and reward strategy
- Called once per episode (not per step) to minimize overhead

**Stage Transition Events**:
- Records transition telemetry with metrics (survival_rate, learning_progress, entropy, steps_at_stage)
- TensorBoard logger consumes transition_events for visualization
- Console logs curriculum transitions with emoji markers

**Checkpointing**:
- `checkpoint_state()` saves agent_stages, episode_rewards, prev_avg_reward, steps_at_stage
- `load_state()` restores curriculum progression from checkpoint
- Enables resume from arbitrary curriculum stage

#### Confidence Level

**HIGH** - Well-documented code with clear abstractions. AdversarialCurriculum is the production implementation with comprehensive stage logic. StaticCurriculum serves as baseline. Factory pattern enables clean configuration-driven selection. Stage configurations are hardcoded constants (STAGE_CONFIGS), which is pedagogically intentional but not configurable. Performance tracking is GPU-native and properly batched.

---

### Subsystem 2: exploration

**Location**: `src/townlet/exploration/`

**Primary Responsibility**: Controls exploration-exploitation tradeoff through action selection strategies and intrinsic motivation rewards. Implements Random Network Distillation (RND) for novelty-seeking behavior and adaptive annealing based on performance variance.

#### Key Components

- `base.py`: `ExplorationStrategy` abstract base class defining interface for action selection, intrinsic reward computation, and network updates
- `rnd.py`: `RNDExploration` - Random Network Distillation with fixed random network and trainable predictor. High prediction error = novel state. Uses `RunningMeanStd` for reward normalization
- `adaptive_intrinsic.py`: `AdaptiveIntrinsicExploration` - wraps RNDExploration and adds variance-based annealing. Reduces intrinsic weight when agent demonstrates consistent performance (low survival variance + high mean survival)
- `epsilon_greedy.py`: `EpsilonGreedyExploration` - simple baseline with no intrinsic rewards, just epsilon-greedy action selection
- `action_selection.py`: `epsilon_greedy_action_selection()` - shared GPU-vectorized action selection utility with action masking support (handles invalid actions at boundaries)

#### Dependencies

**Inbound**:
- `population` - calls `select_actions()` every step, `compute_intrinsic_rewards()` for novelty bonuses, `update()` for RND training
- `demo.runner` - instantiates exploration strategy, saves/loads exploration state in checkpoints

**Outbound**:
- `training.state` - uses `BatchedAgentState` for per-agent epsilon values
- `agent.networks` - RNDNetwork architecture matches SimpleQNetwork (256→128→embed_dim) for consistency

**External libraries**:
- PyTorch (neural networks, GPU operations)
- NumPy (RunningMeanStd statistics)

#### Patterns & Design Decisions

**Random Network Distillation (RND)**:
- Fixed network: randomly initialized, frozen (provides stable target)
- Predictor network: trained to match fixed network via MSE loss
- Prediction error = novelty signal (high error for novel states, low for familiar)
- Normalized by running std to bring intrinsic rewards to comparable magnitude with extrinsic

**Observation Masking**:
- RNDNetwork supports `active_mask` to zero out padding dimensions
- Prevents padding from affecting novelty computation (critical for variable-dim observations)
- Mask moves with network to device (registered as buffer)

**Adaptive Annealing**:
- Tracks survival time variance over sliding window (default: 100 episodes)
- Reduces intrinsic weight when: (1) low variance (<threshold) AND (2) high mean survival (>40% of max_steps)
- Defensive: prevents annealing on "consistently failing" agents (low variance + low survival)
- Uses exponential decay (weight *= decay_rate, floor at min_weight)

**Shared Action Selection**:
- `epsilon_greedy_action_selection()` is GPU-vectorized utility used by all strategies
- Per-agent epsilon values (BatchedAgentState.epsilons) enable different exploration rates
- Action masking: uses multinomial sampling for valid actions only, falls back to greedy for invalid rows
- Vectorized implementation is 10-100x faster than Python loop

**Composability**:
- AdaptiveIntrinsicExploration wraps RNDExploration via composition (not inheritance)
- Delegates action selection and RND computation to inner instance
- Adds annealing logic on top without duplicating RND code

#### Integration Points

**Action Selection (Hot Path)**:
- Called every step for all agents
- Uses per-agent epsilon from BatchedAgentState (enables diverse exploration across population)
- Respects action masks for boundary constraints (invalid actions at grid edges)

**Intrinsic Rewards**:
- `compute_intrinsic_rewards()` returns unweighted novelty values
- Weight application happens once in replay buffer sampling (prevents double-weighting bug)
- Optional `update_stats` flag controls when to update RunningMeanStd (only during training rollouts)

**RND Training**:
- Accumulates observations in buffer
- Trains predictor when buffer reaches batch_size (128 by default)
- Gradient step minimizes MSE between predictor and fixed network outputs
- Training is NOT on hot path (happens during replay buffer sampling)

**Epsilon Decay**:
- `decay_epsilon()` called once per episode by population
- Exponential schedule: epsilon *= epsilon_decay (typical: 0.995 = ~1% decay)
- Floor at epsilon_min (prevents pure greedy, maintains minimal exploration)

**Novelty Visualization**:
- `get_novelty_map()` generates novelty heatmap for all grid positions
- Used by frontend to visualize RND exploration focus
- Only applicable for Grid2D substrates

#### Confidence Level

**HIGH** - Well-structured exploration subsystem with clear separation of concerns. RND implementation follows standard practices (OpenAI/CleanRL). Adaptive annealing logic is defensive against premature convergence. Action selection is properly vectorized and handles edge cases (invalid actions, all-invalid rows). Observation masking is critical for variable-dim support. The only complexity is the composition pattern for AdaptiveIntrinsicExploration, which is well-executed.

---

### Subsystem 3: demo

**Location**: `src/townlet/demo/`

**Primary Responsibility**: Orchestrates multi-day training runs with checkpointing, live inference visualization, and database persistence. Coordinates training thread, inference server, and frontend in unified demo experience.

#### Key Components

- `runner.py`: `DemoRunner` - main training orchestrator that manages environment, population, curriculum, exploration, checkpointing, database, and TensorBoard logging. Implements context manager for resource cleanup
- `unified_server.py`: `UnifiedServer` - coordinates training thread, inference thread (FastAPI/WebSocket), and frontend subprocess (npm run dev). Handles graceful shutdown and config snapshot persistence
- `live_inference.py`: `LiveInferenceServer` - FastAPI WebSocket server that loads latest checkpoint and runs step-by-step inference at human-watchable speed. Supports both inference and replay modes
- `database.py`: `DemoDatabase` - SQLite database wrapper with WAL mode for concurrent access. Stores episode metrics, affordance visits, position heatmaps, system state, and episode recordings

#### Dependencies

**Inbound**:
- Entry point: `scripts/run_demo.py` instantiates UnifiedServer
- Inference clients: frontend connects via WebSocket on port 8766

**Outbound**:
- `environment` - creates VectorizedHamletEnv from compiled universe
- `population` - creates VectorizedPopulation, calls step_population()
- `agent` - derives BrainConfig from agent.yaml + training.yaml
- `curriculum` - builds curriculum via factory
- `exploration` - instantiates AdaptiveIntrinsicExploration
- `universe.compiler` - compiles hierarchical YAML configs
- `training.checkpoint_utils` - safe loading, digest verification, metadata attachment
- `training.tensorboard_logger` - TensorBoard metric logging
- `recording` - optional EpisodeRecorder for episode capture

**External libraries**:
- FastAPI + uvicorn (inference WebSocket server)
- SQLite3 (database persistence)
- TensorFlow/TensorBoard (metric logging)
- PyTorch (checkpoint save/load)

#### Patterns & Design Decisions

**Context Manager for Resource Cleanup**:
- DemoRunner implements `__enter__` and `__exit__` for automatic cleanup
- Properly closes database, TensorBoard writer, and episode recorder
- Safe for checkpoint operations without running full training (critical for inference server)

**Unified Server Architecture**:
- Training runs in background thread (non-daemon, explicit join)
- Inference runs in separate thread (daemon, dies with main)
- Frontend runs as subprocess (Vue dev server)
- Graceful shutdown coordination via shutdown_requested flag and threading.Lock

**Checkpoint Version Control**:
- Version 3 checkpoints include substrate_metadata for validation
- Pre-flight compatibility check detects old checkpoints and fails fast
- Breaking changes enforced via version check (no backwards compatibility)

**Brain As Code (TASK-005)**:
- Derives BrainConfig from agent.yaml (base) + training.yaml (overrides)
- Computes brain_hash (SHA256) for checkpoint provenance
- Network architecture, optimizer, Q-learning params all declaratively configured

**Three-Phase Checkpoint State**:
1. **Phase 2**: Full population state (q_network, optimizer, replay_buffer)
2. **Phase 3**: Curriculum state (agent_stages, performance_trackers)
3. **Phase 4**: Affordance layout (grid positions for resume)

**Episode Flushing for Recurrent Networks**:
- Flushes surviving agents at max_steps (P1.2 fix for memory leak)
- Critical for agents that survive full episode without terminal state
- Loops over all agents (not just agent 0) for multi-agent support

**Generalization Test at Episode 5000**:
- Automatically randomizes affordance positions
- Stores old/new positions in database for provenance
- Tests spatial generalization (position-invariant policies)

**Metric Decomposition**:
- Tracks total_reward (combined), extrinsic_reward (pure), intrinsic_reward (unweighted)
- Separates for analysis: `extrinsic = total - (intrinsic * weight)`
- Logs all three to TensorBoard and database

**Config Snapshot Persistence**:
- UnifiedServer copies entire config pack to run directory
- Ensures reproducibility even if source configs change
- Stored alongside checkpoints and logs

#### Integration Points

**Training Loop Coordination**:
- DemoRunner.run() is main training entry point
- Compiles universe → creates environment → builds population → loads checkpoint → training loop
- Checkpoints every 100 episodes, heartbeat logs every 10, detailed summary every 50

**Inference Server Communication**:
- WebSocket broadcasts state updates to frontend on port 8766
- Payload schema: TELEMETRY_SCHEMA_VERSION = "1.0.0"
- Includes agent positions, meters, actions, Q-values, epsilon, curriculum stage
- Supports both inference mode (live network) and replay mode (recorded episodes)

**Database Schema**:
- `episodes`: survival_time, rewards (total/extrinsic/intrinsic), curriculum_stage, epsilon
- `affordance_visits`: from_affordance → to_affordance transitions (NEW in this codebase)
- `position_heatmap`: (x, y) visit counts + novelty values (for RND visualization)
- `system_state`: key-value store for training status, last checkpoint path
- `episode_recordings`: metadata for recorded episodes (file path, size, recording reason)

**TensorBoard Logging**:
- Phase 1: Multi-agent episode metrics (survival, rewards, stage, epsilon)
- Phase 2: Training metrics (TD error, loss) when training occurs
- Phase 3: Meter dynamics (final meter values) and affordance usage
- Phase 4: Hyperparameters + final metrics (at training completion)
- Curriculum transitions logged with telemetry

**Shutdown Handling**:
- Signal handlers (SIGTERM, SIGINT) set should_shutdown flag
- Checked every 10 steps in training loop for fast Ctrl+C response
- Graceful shutdown: saves final checkpoint, closes all resources

#### Confidence Level

**HIGH** - DemoRunner is the production training orchestrator with comprehensive state management. UnifiedServer coordinates three concurrent components (training, inference, frontend) with proper shutdown handling. LiveInferenceServer supports both inference and replay modes with WebSocket streaming. Database schema is well-designed for multi-day training analytics. Context manager pattern ensures proper resource cleanup. Checkpoint versioning prevents silent failures from breaking changes. The only complexity is the multi-threaded coordination, which is well-implemented with explicit synchronization.

---

### Subsystem 4: recording

**Location**: `src/townlet/recording/`

**Primary Responsibility**: Non-blocking capture of episode trajectories to disk for offline analysis and replay. Uses async queue + background writer thread to avoid blocking training loop. Supports criteria-based recording (only save interesting episodes).

#### Key Components

- `recorder.py`: `EpisodeRecorder` - main interface with bounded queue (default: 1000 items). `RecordingWriter` runs in background thread to pull items, buffer steps, evaluate criteria, and write msgpack files
- `replay.py`: `ReplayManager` - loads recorded episodes from disk, decompresses LZ4, and provides step-by-step playback control
- `data_structures.py`: `RecordedStep` (frozen dataclass ~100-150 bytes), `EpisodeMetadata` (summary stats), `EpisodeEndMarker` (queue sentinel)
- `criteria.py`: Recording criteria evaluation (milestone survival, curriculum transitions, high rewards, diverse affordance usage)
- `video_export.py`, `video_renderer.py`: Video export functionality (not analyzed in detail)

#### Dependencies

**Inbound**:
- `demo.runner` - instantiates EpisodeRecorder if recording enabled, calls record_step() every step
- `demo.live_inference` - uses ReplayManager for replay mode

**Outbound**:
- `demo.database` - queries recording metadata, inserts episode_recordings table entries
- `curriculum` - queries stage info for recording criteria (e.g., stage transitions)

**External libraries**:
- msgpack (efficient binary serialization)
- lz4.frame (fast compression, ~3-5x size reduction)
- Python threading + queue (background writer)

#### Patterns & Design Decisions

**Non-Blocking Recording**:
- Bounded queue (Queue.put_nowait()) drops frames when full (graceful degradation)
- Training loop never blocks on I/O
- Clones tensors to CPU immediately (cheap), defers compression/serialization to writer thread

**Frozen Dataclasses with Slots**:
- `RecordedStep` uses `frozen=True, slots=True` for minimal memory footprint
- Tuples instead of lists for immutability and msgpack efficiency
- ~100-150 bytes per step (500 steps = ~75KB before compression)

**Episode Boundary Markers**:
- `EpisodeEndMarker` is queue sentinel that triggers criteria evaluation
- Writer buffers steps until marker received
- Enables step accumulation without premature file writes

**Criteria-Based Recording**:
- Only saves episodes meeting criteria (milestone survival, transitions, high rewards, diverse affordances)
- Prevents disk bloat from recording every episode
- Configurable via `recording.criteria` in training.yaml

**Compression Pipeline**:
- msgpack serialization (efficient binary format)
- LZ4 compression (fast, ~3-5x size reduction)
- File naming: `episode_{id:06d}.msgpack.lz4`

**Positional Flexibility**:
- `RecordedStep.position` is tuple of variable length: (x, y) for 2D, (x, y, z) for 3D, () for aspatial
- Handles any substrate dimensionality without schema changes

**Temporal Mechanics Support**:
- Optional fields: time_of_day, interaction_progress (Level 2.5+ features)
- Backwards compatible with episodes lacking temporal data

#### Integration Points

**Training Loop Recording**:
- DemoRunner calls `record_step()` every step with positions, meters, action, rewards, Q-values, epsilon, action_masks
- Calls `finish_episode()` at episode end with EpisodeMetadata
- Only records agent 0 (single-agent recording for now)

**Replay Playback**:
- ReplayManager.load_episode() decompresses and deserializes episode
- Provides step-by-step control: get_current_step(), next_step(), seek()
- LiveInferenceServer uses ReplayManager for replay mode

**Database Integration**:
- Writer inserts episode_recordings table entry with file_path, metadata, recording_reason
- Database queries enable filtering by stage, reward, survival time
- Frontend can query database to list available recordings

**Recording Criteria**:
- Milestone survival: first episode to reach threshold (e.g., 100, 200, 300 steps)
- Curriculum transitions: record episodes where stage changes
- High rewards: top 5% of episodes by total_reward
- Diverse affordance usage: episodes using ≥X unique affordances

**Shutdown Handling**:
- `shutdown()` drains queue and joins writer thread (10s timeout)
- Ensures buffered episodes written before process exit

#### Integration Points (Recording Workflow)

**Step Recording (Hot Path)**:
```python
recorder.record_step(
    step=step,
    positions=env.positions[0],  # Agent 0
    meters=env.meters[0],
    action=action,
    reward=extrinsic_only,
    intrinsic_reward=intrinsic,
    done=done,
    q_values=q_values,
    epsilon=epsilon,
    action_masks=action_masks,
    time_of_day=time_of_day,
    interaction_progress=interaction_progress,
)
```

**Episode Completion**:
```python
metadata = EpisodeMetadata(
    episode_id=episode_id,
    survival_steps=survival,
    total_reward=reward,
    extrinsic_reward=extrinsic,
    intrinsic_reward=intrinsic,
    curriculum_stage=stage,
    epsilon=epsilon,
    intrinsic_weight=weight,
    timestamp=timestamp,
    affordance_layout=layout,
    affordance_visits=visits,
    custom_action_uses=uses,
)
recorder.finish_episode(metadata)
```

#### Confidence Level

**MEDIUM-HIGH** - Well-designed recording subsystem with proper separation of concerns (recorder vs writer thread). Non-blocking queue pattern prevents training loop interference. Frozen dataclasses with slots minimize memory overhead. Criteria-based recording prevents disk bloat. Compression pipeline is efficient (msgpack + LZ4). ReplayManager provides clean playback interface. The only uncertainty is the criteria evaluation logic (not fully analyzed), but the infrastructure is solid. Recording is optional (configurable), so failures don't impact core training.




---

## Cross-Subsystem Dependencies

**Major Dependency Flows**:

- **universe → vfs, world, effects, items**: Compiler depends on all state and mechanics systems for validation and compilation
- **environment → substrate, vfs, effects, items, affordances**: Environment orchestrates all mechanics systems
- **population → environment, agent, training, exploration, curriculum**: Population coordinates the entire training loop
- **demo → population, environment, universe**: Demo runner manages training execution
- **All subsystems → config**: Configuration DTOs provide foundation for all subsystems

**Critical Integration Points**:

1. **Training Loop Core**: population → environment → substrate
2. **State Management**: environment → vfs → effects/items
3. **Compilation Pipeline**: universe → vfs/world → effects/items
4. **Exploration Integration**: exploration → environment (via wiring)
5. **Network Management**: agent → population (ownership and synchronization)

**Architectural Layers** (bottom-up):

1. **Foundation**: config, substrate
2. **State & Computation**: vfs, world
3. **Game Mechanics**: effects, items
4. **Execution**: environment
5. **Training**: agent, training, exploration, curriculum
6. **Orchestration**: population, demo
7. **Compilation**: universe, compiler
8. **Recording**: recording (optional)
