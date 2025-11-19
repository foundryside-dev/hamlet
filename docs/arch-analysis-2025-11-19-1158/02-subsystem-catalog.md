# Subsystem Catalog: HAMLET Townlet

**Analysis Date**: 2025-11-19
**Scope**: All 12 subsystems in `src/townlet/`
**Analyst**: Claude Code
**Total LOC**: 28,314 lines across 104 Python files

---

## 1. Universe Compiler

**Location**: `src/townlet/universe/`
**Confidence**: HIGH

### Responsibility
The Universe Compiler is the architectural keystone of HAMLET, transforming hierarchical v2.1 YAML configurations into immutable `CompiledUniverse` artifacts through a 7-stage pipeline. It serves as the central integration point, resolving symbols, cross-validating configurations, and producing cached binary artifacts (`.compiled/universe.msgpack`) that feed all runtime subsystems.

### Key Components

1. **compiler.py** (3,100 LOC) - Main UniverseCompiler class orchestrating 7-stage pipeline (parse → symbol table → resolve → cross-validate → metadata → optimization → emit)
2. **symbol_table.py** - Name resolution, ID allocation for bars/affordances/actions, ensures global vocabulary consistency across curriculum levels
3. **compiled.py** - CompiledUniverse immutable artifact container with provenance tracking (config_hash, brain_hash, drive_hash)
4. **optimization.py** - Performance optimizations (tensor preallocation sizing, vocabulary deduplication)
5. **dto/** - Data transfer objects (ObservationSpec, MeterMetadata, AffordanceMetadata, ActionMetadata, UniverseMetadata)
6. **adapters/vfs_adapter.py** - VFS integration adapter converting VariableDef specs to ObservationFields
7. **errors.py** - Compilation error types (SymbolNotFoundError, CircularDependencyError, ValidationError)

### Dependencies

**Inbound** (who depends on this subsystem):
- **Vectorized Environment** → loads CompiledUniverse artifact at initialization
- **Population Manager** → passes compiled metadata to environment factory
- **Demo Runner** → invokes compiler for config validation before training
- **CLI tools** → `python -m townlet.compiler {compile,inspect,validate}`

**Outbound** (what this subsystem depends on):
- **Configuration System** → imports all Pydantic DTOs for v2.1 hierarchical config validation
- **VFS** → uses VFSAdapter to integrate variable definitions into observation specs
- **Substrate** → imports SubstrateConfig for validation

**External**:
- **PyYAML** - YAML parsing
- **Pydantic** - Schema validation
- **msgpack** - Binary serialization of compiled artifacts
- **hashlib** - SHA256 hashing for provenance (config_hash, drive_hash, brain_hash)

### Architectural Patterns

- **Pipeline Pattern**: 7-stage sequential compilation (parse → symbol table → resolve → cross-validate → metadata → optimization → emit)
- **Memento Pattern**: CompiledUniverse captures complete configuration snapshot with provenance tracking
- **Adapter Pattern**: VFSAdapter converts between VFS schemas and compiler DTOs
- **Builder Pattern**: Incremental construction of symbol table and metadata structures
- **Registry Pattern**: Symbol table acts as centralized ID registry for bars/affordances/actions

### Key Abstractions

- **SymbolTable**: Global name-to-ID mapping ensuring consistent vocabulary across curriculum levels
- **CompiledUniverse**: Immutable artifact containing all metadata, observation specs, and provenance hashes
- **CompilationStage**: (Implicit) Each stage is a distinct transformation phase

### Notable Design Decisions

1. **Multi-Level Compilation** - Single compile produces metadata for all curriculum levels (L0-L3), enabling checkpoint transfer across levels
2. **Immutable Artifacts** - CompiledUniverse is read-only after creation, cached to disk for reproducibility
3. **Provenance Tracking** - SHA256 hashes (config_hash, drive_hash, brain_hash) prevent checkpoint mismatches
4. **Symbol Table Centralization** - All ID allocation happens in compiler, ensures consistent action/bar/affordance IDs

### Integration Points

- **Compile-time**: CLI `python -m townlet.compiler compile <config>` produces `.compiled/universe.msgpack`
- **Runtime**: VectorizedHamletEnv.__init__() loads CompiledUniverse artifact, Population passes it to env factory
- **CI/CD**: GitHub Actions runs `validate` command on all config packs for lint-style validation

### Code Quality Observations

- **Strengths**: Clear stage separation, comprehensive error handling, extensive logging, provenance tracking
- **Concerns**: compiler.py is 3,100 LOC (potential for further modularization), some stages have complex nested logic

---

## 2. Configuration System

**Location**: `src/townlet/config/`
**Confidence**: HIGH

### Responsibility
Pydantic-based schema validation layer enforcing the "no-defaults principle" for v2.1 hierarchical configuration. Validates all YAML inputs (training, bars, affordances, drive-as-code, brain, curriculum) and ensures all behavioral parameters are explicitly specified. Acts as the type system contract between YAML configs and the Universe Compiler.

### Key Components

1. **drive_as_code.py** (681 LOC) - DAC reward function specifications (extrinsic, intrinsic, shaping, modifiers)
2. **training_v2_config.py** - Training hyperparameters (batch_size, episodes, replay_buffer_capacity)
3. **bars_v2_config.py** - Meter definitions (name, bounds, depletion_rate, starting_value)
4. **affordances_v2_config.py** - Interaction definitions (name, delta_bars, enabled status)
5. **curriculum_config.py** - Difficulty progression configuration (strategy, stages, thresholds)
6. **stratum_config.py** - Substrate configuration (Grid2D/3D/ND, Continuous, Aspatial)

**Note**: BrainConfig (726 LOC) is located in `agent/brain_config.py`, not this subsystem.

### Dependencies

**Inbound**:
- **Universe Compiler** → imports all config DTOs for validation during compilation
- **Demo Runner** → loads config DTOs to pass to compiler
- **CLI tools** → validation scripts use DTOs for schema checking

**Outbound**:
- **Substrate** → imports SubstrateConfig (note: actual substrate configs may be in substrate/config.py)
- **VFS** → VariableReferenceConfig integration

**External**:
- **Pydantic 2.0+** - Schema validation, DTOs, field validation
- **PyYAML** - YAML parsing (implicitly through loader)

### Architectural Patterns

- **Data Transfer Object (DTO)**: All configs are Pydantic models for validation and serialization
- **No-Defaults Principle**: Required fields with no default values enforce explicit configuration
- **Schema Validation**: Pydantic validators enforce constraints (positive values, valid enums, cross-field validation)

### Key Abstractions

- **BaseModel** (Pydantic): All config classes inherit from Pydantic BaseModel
- **Config Hierarchy**: Experiment → Stratum → Environment → Levels → (Curriculum, Bars, Affordances, Training, Variables)

### Notable Design Decisions

1. **No-Defaults Principle** - All behavioral parameters required, no hidden defaults (prevents non-reproducible configs)
2. **Breaking Changes Encouraged** - Pre-release status allows aggressive schema evolution without backwards compatibility
3. **Hierarchical v2.1 Structure** - Multi-level configs (experiment, stratum, levels) replace old single-file configs
4. **DAC Integration** - Reward functions fully declarative (replaced 583 LOC of hardcoded Python strategies)

### Integration Points

- **Compile-time**: Universe Compiler instantiates config DTOs from YAML, validates schemas
- **Runtime**: Compiled artifacts contain validated config data, not the DTOs themselves

### Code Quality Observations

- **Strengths**: Comprehensive Pydantic validation, clear schema definitions, extensive docstrings
- **Concerns**: 19 separate config files (could benefit from schema organization), some validators have complex nested logic

---

## 3. Vectorized Environment

**Location**: `src/townlet/environment/`
**Confidence**: HIGH

### Responsibility
GPU-native batched RL environment implementing the Gymnasium interface. Manages [num_agents, ...] tensor operations for meters (resources), affordances (interactions), rewards (via DACEngine), temporal mechanics, and action resolution. Consumes CompiledUniverse artifacts and provides the core RL loop (step, reset, render).

### Key Components

1. **vectorized_env.py** (1,839 LOC) - VectorizedHamletEnv main class, Gymnasium interface implementation
2. **dac_engine.py** (968 LOC) - DACEngine reward computation from DAC YAML specs (extrinsic + intrinsic + shaping)
3. **affordance_engine.py** (551 LOC) - AffordanceEngine handles interaction resolution (delta_bars application, success tracking)
4. **meter_dynamics.py** - MeterDynamics manages bar depletion, restoration, bounds enforcement
5. **action_builder.py** - ActionSpaceBuilder composes substrate actions + custom actions into global vocabulary
6. **temporal_utils.py** - TimeManager handles day/night cycles, temporal state (L3 curriculum)
7. **pomdp_builder.py** - POMDP observation window construction (5×5 local vision for L2)

### Dependencies

**Inbound**:
- **Population Manager** → calls env.step(actions), env.reset() for training loop
- **Demo Runner** → instantiates environment for training sessions
- **Recording** → captures environment state for episode playback

**Outbound**:
- **Universe Compiler** → loads CompiledUniverse artifact at __init__()
- **Substrate** → delegates positioning, movement, distance calculations to substrate instance
- **VFS** → uses VariableRegistry for state storage and access control
- **Curriculum** → receives CurriculumDecision objects specifying depletion rates, active meters

**External**:
- **PyTorch** - GPU tensor operations ([num_agents, ...] batching)
- **Gymnasium** - RL environment interface (spaces, step, reset, render)
- **NumPy** - Compatibility layer for non-tensor operations

### Architectural Patterns

- **Facade Pattern**: VectorizedHamletEnv orchestrates DACEngine, AffordanceEngine, MeterDynamics, Substrate
- **Strategy Pattern**: Configurable reward computation (DACEngine), action resolution (AffordanceEngine)
- **Delegation Pattern**: Substrate handles all positioning logic, environment handles game logic

### Key Abstractions

- **Gymnasium.Env**: Standard RL environment interface (observation_space, action_space, step, reset, render)
- **CompiledUniverse**: Immutable configuration artifact consumed at initialization
- **TensorBatch**: All state maintained as PyTorch tensors with batch dimension [num_agents, ...]

### Notable Design Decisions

1. **GPU-Native Vectorization** - All state as PyTorch tensors, minimizes CPU/GPU transfers
2. **DAC Reward Computation** - Declarative reward functions (extrinsic + intrinsic × modifiers + shaping)
3. **Dual Reward Tracking** - Separate extrinsic/intrinsic reward throughout pipeline (pedagogical transparency)
4. **Substrate Delegation** - Environment delegates all positioning to substrate (clean separation of concerns)
5. **POMDP Support** - 5×5 vision window construction for partial observability (L2 curriculum)

### Integration Points

- **Compile-time**: Loads `.compiled/universe.msgpack` artifact at __init__()
- **Runtime**: Population drives step() loop, DACEngine computes rewards each step, AffordanceEngine resolves interactions

### Code Quality Observations

- **Strengths**: Clean facade orchestration, comprehensive tensor batching, clear separation of concerns (meters vs. affordances vs. rewards)
- **Concerns**: vectorized_env.py is 1,839 LOC (could split into smaller modules), some methods have deep nesting

---

## 4. Substrate System

**Location**: `src/townlet/substrate/`
**Confidence**: HIGH

### Responsibility
Spatial abstraction layer defining position representation, movement mechanics, distance metrics, and observation encoding. Supports multiple substrate types (Grid2D/3D/ND, Continuous2D/3D/ND, Aspatial) with configurable boundary modes (clamp, wrap, bounce, sticky) and distance metrics (manhattan, euclidean, chebyshev). Enables teaching spatial concepts separately from RL concepts.

### Key Components

1. **base.py** - Abstract SpatialSubstrate interface defining position(), move(), distance(), get_bounds()
2. **grid2d.py** (605 LOC) - Grid2DSubstrate discrete 2D grid with configurable boundary modes
3. **grid3d.py** (620 LOC) - Grid3DSubstrate discrete 3D grid
4. **gridnd.py** (537 LOC) - GridNDSubstrate N-dimensional discrete grid (4D-100D)
5. **continuous.py** (766 LOC) - Continuous2D/Continuous3D substrates with smooth positioning
6. **continuousnd.py** (504 LOC) - ContinuousNDSubstrate N-dimensional continuous spaces
7. **aspatial.py** - AspatialSubstrate pure state machine (no positioning, reveals meters as fundamental)
8. **factory.py** - SubstrateFactory creates substrate instances from StratumConfig

**Note**: SubstrateConfig is defined in `config/stratum_config.py`, not in this subsystem.

### Dependencies

**Inbound**:
- **Vectorized Environment** → delegates position(), move(), distance() calls to substrate instance
- **Universe Compiler** → validates SubstrateConfig during compilation
- **POMDP Builder** → queries substrate for local observation windows (vision_range)

**Outbound**:
- None (substrate is self-contained abstraction)

**External**:
- **PyTorch** - Tensor operations for batched position updates
- **NumPy** - Compatibility for non-tensor geometry

### Architectural Patterns

- **Strategy Pattern**: Multiple substrate implementations (Grid2D, Continuous, Aspatial) sharing common interface
- **Factory Pattern**: SubstrateFactory instantiates correct substrate based on config
- **Template Method**: Base class defines interface, subclasses implement specific mechanics

### Key Abstractions

- **SpatialSubstrate**: Abstract interface for position/movement/distance operations
- **BoundaryMode**: Enum (clamp, wrap, bounce, sticky) configuring edge behavior
- **DistanceMetric**: Enum (manhattan, euclidean, chebyshev) configuring distance calculations
- **ObservationEncoding**: Enum (relative, scaled, absolute) configuring observation normalization

### Notable Design Decisions

1. **Aspatial Substrate** - Proves positioning optional, pedagogically reveals meters as "true universe"
2. **Observation Encoding Modes** - relative (normalized [0,1]), scaled ([0, grid_size]), absolute (raw) for different learning scenarios
3. **Constant Observation Dim** - Grid2D produces same obs_dim regardless of grid size (enables transfer learning)
4. **Boundary Mode Diversity** - Wrap (toroidal), bounce (elastic), sticky (L-shaped corners) for varied movement mechanics
5. **N-Dimensional Support** - GridND/ContinuousND support 4D-100D spaces (extreme dimensionality for research)

### Integration Points

- **Compile-time**: Universe Compiler validates SubstrateConfig, determines observation_dim
- **Runtime**: Environment delegates all position/movement operations to substrate instance

### Code Quality Observations

- **Strengths**: Clean abstraction, comprehensive boundary mode implementations, extensive distance metric support
- **Concerns**: Some substrate implementations have duplicated logic (refactor opportunity for shared utilities)

---

## 5. Agent Networks

**Location**: `src/townlet/agent/`
**Confidence**: HIGH

### Responsibility
Neural network architectures for Q-learning. Implements SimpleQNetwork (MLP, ~26K params) for full observability and RecurrentSpatialQNetwork (CNN+LSTM, ~650K params) for partial observability (POMDP). Includes factories for networks, optimizers, and loss functions, enabling configuration-driven instantiation.

### Key Components

1. **networks.py** (539 LOC) - SimpleQNetwork (MLP) and RecurrentSpatialQNetwork (CNN+LSTM) implementations
2. **network_factory.py** - NetworkFactory creates Q-networks from BrainConfig
3. **optimizer_factory.py** - OptimizerFactory creates optimizers (Adam, RMSprop) from config
4. **loss_factory.py** - LossFactory creates loss functions (Huber, MSE) from config
5. **brain_config.py** (726 LOC) - BrainConfig Pydantic DTOs (network architecture, optimizer, loss, Q-learning params)

### Dependencies

**Inbound**:
- **Population Manager** → instantiates Q-networks via NetworkFactory, calls forward() for action selection
- **Universe Compiler** → validates BrainConfig during compilation
- **Training Infrastructure** → loads network state_dict from checkpoints

**Outbound**:
- None (agent is self-contained, depends only on PyTorch)

**External**:
- **PyTorch** - Neural network modules (nn.Linear, nn.LSTM, nn.Conv2d), optimizers, loss functions

### Architectural Patterns

- **Factory Pattern**: NetworkFactory, OptimizerFactory, LossFactory for configuration-driven instantiation
- **Strategy Pattern**: Multiple network architectures (SimpleQNetwork, RecurrentSpatialQNetwork) sharing common interface

### Key Abstractions

- **QNetwork**: (Implicit) Common interface for forward(obs, hidden_state=None) → (q_values, new_hidden_state)
- **BrainConfig**: Configuration DTO specifying network architecture, optimizer, loss, Q-learning hyperparameters

### Notable Design Decisions

1. **Dual Architectures** - SimpleQNetwork (MLP) for full observability, RecurrentSpatialQNetwork (CNN+LSTM) for POMDP
2. **LSTM Hidden State Management** - Resets at episode start, persists during rollout, resets per transition in batch training
3. **Gradient Clipping** - max_norm=10.0 prevents exploding gradients (critical for LSTM)
4. **Checkpoint Transfer** - All Grid2D configs use 29→8 architecture (enables checkpoint transfer across curriculum levels)
5. **Compact Encoders** - Vision (5×5 window → 128), Position (x,y → 32), Meters (8 → 32) → LSTM (192→256)

### Integration Points

- **Compile-time**: Universe Compiler validates BrainConfig, determines network architecture
- **Runtime**: Population instantiates networks via factory, calls forward() for action selection, backward() for gradient updates

### Code Quality Observations

- **Strengths**: Clean architecture separation, comprehensive factory pattern, well-documented forward() methods
- **Concerns**: brain_config.py is 726 LOC (could split network config from optimizer/loss config)

---

## 6. Population Manager

**Location**: `src/townlet/population/`
**Confidence**: HIGH

### Responsibility
Coordinates multi-agent training with shared curriculum and exploration strategies. Orchestrates Q-networks (online and target), replay buffers, training loops, gradient updates, and checkpoint management. Implements DQN and Double DQN algorithms with configurable target network update frequency.

### Key Components

1. **vectorized.py** (1,094 LOC) - VectorizedPopulation main class orchestrating training loop
2. **base.py** - Abstract Population interface
3. **runtime_registry.py** - RuntimeAgentRegistry tracks agent metadata (birth step, lifetime survival, curriculum level)
4. **factory.py** - PopulationFactory creates population instances from config

### Dependencies

**Inbound**:
- **Demo Runner** → instantiates population, calls train_step() for multi-day training sessions
- **Recording** → queries population for agent states, Q-values for episode capture

**Outbound**:
- **Vectorized Environment** → calls env.step(actions), env.reset() for training loop
- **Agent Networks** → instantiates Q-networks via NetworkFactory, calls forward() for action selection
- **Training Infrastructure** → uses ReplayBuffer for experience storage, Checkpoint utilities for save/load
- **Exploration** → uses exploration strategies (RND, epsilon-greedy) for action selection
- **Curriculum** → receives CurriculumDecision objects specifying environment difficulty

**External**:
- **PyTorch** - Gradient computation, optimizer.step(), network.state_dict() for checkpointing
- **NumPy** - Compatibility for non-tensor operations

### Architectural Patterns

- **Facade Pattern**: VectorizedPopulation orchestrates environment, networks, replay buffer, exploration, curriculum
- **Memento Pattern**: Checkpoints capture complete training state (networks, optimizer, replay buffer, curriculum stage)
- **Observer Pattern**: TensorBoard logging, episode database tracking

### Key Abstractions

- **Population**: Abstract interface for train_step(), save_checkpoint(), load_checkpoint()
- **RuntimeAgentRegistry**: Tracks per-agent metadata across training

### Notable Design Decisions

1. **DQN Algorithm Variants** - Vanilla DQN (max over target network) vs. Double DQN (argmax online, evaluate target)
2. **Target Network Updates** - Configurable frequency (e.g., every 1000 steps) for stability
3. **Shared Curriculum** - All agents in population share same curriculum stage (not individual progression)
4. **Batched Training** - Single backward() pass computes gradients for entire batch (GPU efficiency)
5. **Exploration Integration** - Population delegates action selection to exploration strategies (RND, epsilon-greedy)

### Integration Points

- **Compile-time**: Loads CompiledUniverse metadata for environment factory
- **Runtime**: Drives env.step() loop, trains Q-networks via replay buffer, saves checkpoints to disk

### Code Quality Observations

- **Strengths**: Clean orchestration of all training components, comprehensive checkpoint management
- **Concerns**: vectorized.py is 1,094 LOC (could split training loop from checkpoint management), some methods have deep nesting

---

## 7. Exploration Strategies

**Location**: `src/townlet/exploration/`
**Confidence**: HIGH

### Responsibility
Implements exploration algorithms for intrinsic motivation and action selection. Includes RND (Random Network Distillation), ICM (Intrinsic Curiosity Module), adaptive intrinsic (performance-based annealing), and epsilon-greedy. Enables pedagogical comparison of exploration techniques.

### Key Components

1. **rnd.py** - RND (Random Network Distillation) for novelty-seeking exploration
2. **adaptive_intrinsic.py** - AdaptiveIntrinsic with performance-based annealing (suppresses intrinsic after threshold survival)
3. **epsilon_greedy.py** - EpsilonGreedy action selection with linear annealing
4. **action_selection.py** - Action selection utilities (epsilon-greedy, greedy, random)
5. **base.py** - Abstract ExplorationStrategy interface
6. **factory.py** - ExplorationFactory creates exploration strategies from config

### Dependencies

**Inbound**:
- **Population Manager** → uses exploration strategies for action selection
- **Vectorized Environment** → intrinsic rewards added to extrinsic rewards

**Outbound**:
- **Training Infrastructure** → imports BatchedAgentState from training.state for agent tracking

**Note**: RND defines its own `RNDNetwork` class (doesn't depend on agent/). AdaptiveIntrinsic uses internal variance tracking (doesn't depend on curriculum/).

**External**:
- **PyTorch** - Neural networks for RND/ICM, tensor operations for intrinsic reward computation

### Architectural Patterns

- **Strategy Pattern**: Multiple exploration implementations (RND, ICM, Adaptive, Epsilon-Greedy) sharing common interface
- **Factory Pattern**: ExplorationFactory instantiates correct strategy based on config
- **Observer Pattern**: Exploration strategies track agent performance for annealing decisions

### Key Abstractions

- **ExplorationStrategy**: Abstract interface for select_action(), compute_intrinsic_reward()
- **IntrinsicRewardModule**: (Implicit) Common interface for RND/ICM novelty computation

### Notable Design Decisions

1. **RND for Novelty** - Random network prediction error as proxy for state novelty
2. **Adaptive Annealing** - Intrinsic weight suppression after mean survival >50 steps (prevents "Low Energy Delirium")
3. **Crisis Suppression** - DAC modifiers can suppress intrinsic rewards during resource crises (pedagogical)
4. **Epsilon Linear Annealing** - Epsilon decays from 1.0 → 0.1 over training (exploration → exploitation)

### Integration Points

- **Compile-time**: Universe Compiler validates exploration config
- **Runtime**: Population calls exploration.select_action() each step, DACEngine adds intrinsic rewards

### Code Quality Observations

- **Strengths**: Clean strategy pattern implementation, well-documented exploration algorithms
- **Concerns**: Some overlap between RND and ICM implementations (shared feature extraction logic)

---

## 8. Curriculum System

**Location**: `src/townlet/curriculum/`
**Confidence**: HIGH

### Responsibility
Controls environment difficulty progression based on agent performance. Implements Static curriculum (fixed stages with step thresholds) and Adversarial curriculum (adaptive challenge). Returns CurriculumDecision objects specifying depletion rates, active meters, and reward mode.

### Key Components

1. **adversarial.py** (531 LOC) - AdversarialCurriculum adaptive difficulty based on agent survival
2. **static.py** - StaticCurriculum fixed progression through predefined stages
3. **base.py** - Abstract Curriculum interface
4. **factory.py** - CurriculumFactory creates curriculum instances from config
5. **decision.py** - CurriculumDecision DTO specifying environment difficulty

### Dependencies

**Inbound**:
- **Population Manager** → queries curriculum for current stage, passes agent performance metrics
- **Vectorized Environment** → applies CurriculumDecision (depletion rates, active meters) each step

**Outbound**:
- None (curriculum is self-contained decision logic)

**External**:
- None (pure Python logic)

### Architectural Patterns

- **Strategy Pattern**: Multiple curriculum implementations (Static, Adversarial) sharing common interface
- **Factory Pattern**: CurriculumFactory instantiates correct curriculum based on config
- **Decision Object Pattern**: CurriculumDecision encapsulates all difficulty parameters

### Key Abstractions

- **Curriculum**: Abstract interface for update_stage(), get_current_decision()
- **CurriculumDecision**: DTO specifying depletion_rates, active_meters, reward_mode

### Notable Design Decisions

1. **Performance-Based Progression** - Adversarial curriculum increases difficulty when mean survival exceeds threshold
2. **Multi-Meter Activation** - Curriculum stages control which meters are active (L0: energy only, L1: all meters)
3. **Depletion Rate Scaling** - Early stages have slow depletion (extended survival), later stages faster (challenge)
4. **Pedagogical Staging** - L0 (credit assignment) → L0.5 (multi-resource) → L1 (full) → L2 (POMDP) → L3 (temporal)

### Integration Points

- **Compile-time**: Universe Compiler validates curriculum config, multi-level compilation
- **Runtime**: Population queries curriculum each update_stage(), Environment applies CurriculumDecision each step

### Code Quality Observations

- **Strengths**: Clean decision object pattern, well-documented stage progression logic
- **Concerns**: Adversarial curriculum threshold logic could be more configurable (currently hardcoded thresholds)

---

## 9. Training Infrastructure

**Location**: `src/townlet/training/`
**Confidence**: HIGH

### Responsibility
Experience replay buffers (vanilla, sequential for LSTM, prioritized), checkpointing utilities, training state management, and TensorBoard logging. Provides core training infrastructure shared across all population implementations.

### Key Components

1. **replay_buffer.py** - ReplayBuffer standard experience replay (random sampling)
2. **sequential_replay_buffer.py** - SequentialReplayBuffer LSTM-compatible buffer (maintains episode coherence)
3. **prioritized_replay_buffer.py** - PrioritizedReplayBuffer with TD-error prioritization
4. **checkpoint_utils.py** - save_checkpoint(), load_checkpoint(), validate_checkpoint() utilities
5. **state.py** - TrainingState DTO (step, episode, curriculum_stage, epsilon)
6. **tensorboard_logger.py** - TensorBoardLogger metrics logging (rewards, survival, Q-values, loss)

### Dependencies

**Inbound**:
- **Population Manager** → uses replay buffers for experience storage, checkpoint utilities for save/load
- **Demo Runner** → uses checkpoint utilities for multi-day training sessions

**Outbound**:
- **Agent Networks** → checkpoints store network state_dict
- **Curriculum** → checkpoints store curriculum stage

**External**:
- **PyTorch** - state_dict() serialization for networks and optimizers
- **TensorBoard** - SummaryWriter for metrics logging
- **NumPy** - Replay buffer storage (numpy arrays for efficiency)

### Architectural Patterns

- **Memento Pattern**: Checkpoints capture complete training state for reproducibility
- **Observer Pattern**: TensorBoard logging tracks training metrics
- **Strategy Pattern**: Multiple replay buffer implementations (vanilla, sequential, prioritized)

### Key Abstractions

- **ReplayBuffer**: Abstract interface for add(), sample()
- **Checkpoint**: (Implicit) Dictionary containing networks, optimizer, replay_buffer, training_state

### Notable Design Decisions

1. **Sequential Buffer for LSTM** - Maintains episode coherence (required for recurrent networks)
2. **Checkpoint Provenance** - config_hash, drive_hash, brain_hash prevent checkpoint mismatches
3. **TensorBoard Integration** - Comprehensive metrics (extrinsic, intrinsic, total reward, survival, Q-values, loss)
4. **Lazy Loading** - Checkpoints can be loaded without replay buffer (for inference)

### Integration Points

- **Compile-time**: None (infrastructure is runtime-only)
- **Runtime**: Population adds experiences to buffer, samples batches for training, saves/loads checkpoints

### Code Quality Observations

- **Strengths**: Clean checkpoint management, comprehensive TensorBoard logging, well-documented replay buffer variants
- **Concerns**: Some duplication between replay buffer implementations (shared sampling logic)

---

## 10. VFS (Variable & Feature System)

**Location**: `src/townlet/vfs/`
**Confidence**: HIGH

### Responsibility
Declarative state space configuration system defining variables (global, agent, agent_private scopes), observation fields, normalization specs, and access control. Compiles `variables_reference.yaml` into observation specs and runtime registries. Integrated into production (TASK-002C complete per CLAUDE.md).

### Key Components

1. **schema.py** - Pydantic schemas (VariableDef, ObservationField, NormalizationSpec, WriteSpec)
2. **registry.py** - VariableRegistry runtime storage with GPU tensors, access control enforcement
3. **observation_builder.py** - ObservationBuilder compile-time spec generation, dimension validation
4. **__init__.py** - Public API exports

### Dependencies

**Inbound**:
- **Universe Compiler** → uses VFSAdapter to integrate VariableDef specs into ObservationFields
- **Vectorized Environment** → uses VariableRegistry for state storage and access control

**Outbound**:
- None (VFS is self-contained, depends only on PyTorch/Pydantic)

**External**:
- **PyTorch** - GPU tensor storage in VariableRegistry
- **Pydantic** - Schema validation for VariableDef, ObservationField

### Architectural Patterns

- **Registry Pattern**: VariableRegistry centralized state storage with access control
- **Builder Pattern**: ObservationBuilder constructs observation specs from variable definitions
- **Adapter Pattern**: VFSAdapter converts VariableDef to ObservationField for compiler integration

### Key Abstractions

- **VariableDef**: Declarative variable definition (name, scope, readers, writers, normalization)
- **ObservationField**: Observation spec with dimensions, normalization, and source variables
- **VariableRegistry**: Runtime storage with GPU tensors and access control

### Notable Design Decisions

1. **Three Scopes** - global (shared), agent (per-agent), agent_private (hidden state)
2. **Access Control** - Readers (agent, engine, acs, bac), Writers (engine, actions, bac)
3. **Breaking Change** - All config packs MUST include `variables_reference.yaml` (enforced by compiler)
4. **GPU Tensor Storage** - VariableRegistry stores all state as PyTorch tensors for GPU efficiency

### Integration Points

- **Compile-time**: Universe Compiler uses VFSAdapter to convert VariableDef → ObservationField
- **Runtime**: Environment uses VariableRegistry for state storage, observation construction

### Code Quality Observations

- **Strengths**: Clean access control design, comprehensive schema validation, clear scope separation
- **Concerns**: VFS integration required breaking changes across all config packs (migration complexity)

---

## 11. Demo & Orchestration

**Location**: `src/townlet/demo/`
**Confidence**: MEDIUM

### Responsibility
Training orchestration (DemoRunner), live inference server (WebSocket), unified server (training + inference), and SQLite database for episode tracking. Provides high-level orchestration of multi-day training sessions and real-time visualization.

### Key Components

1. **runner.py** (958 LOC) - DemoRunner multi-day training orchestration with checkpoint management
2. **live_inference.py** (1,213 LOC) - LiveInferenceServer WebSocket server for real-time visualization
3. **unified_server.py** (532 LOC) - UnifiedServer integrated training + inference in single process
4. **database.py** (407 LOC) - EpisodeDatabase SQLite tracking for episode metadata, agent stats
5. **__main__.py** - CLI entry points

### Dependencies

**Inbound**:
- **scripts/run_demo.py** → instantiates UnifiedServer for training + live inference
- **Frontend** → connects to WebSocket server for real-time visualization

**Outbound**:
- **Universe Compiler** → invokes compiler to produce CompiledUniverse
- **Population Manager** → orchestrates multi-day training via train_step() calls
- **Recording** → triggers episode recordings based on criteria

**External**:
- **WebSockets** - Real-time communication with frontend (Vue.js)
- **SQLite** - Episode database for tracking metadata
- **FastAPI/Uvicorn** - REST API server (optional)

### Architectural Patterns

- **Facade Pattern**: DemoRunner orchestrates compiler, population, recording, database
- **Observer Pattern**: WebSocket server broadcasts environment state to connected clients
- **Context Manager Pattern**: DemoRunner uses context manager for resource cleanup

### Key Abstractions

- **DemoRunner**: High-level training orchestration with checkpoint management
- **LiveInferenceServer**: WebSocket server for real-time visualization
- **EpisodeDatabase**: SQLite database for episode tracking

### Notable Design Decisions

1. **Multi-Day Training** - DemoRunner manages checkpoint save/load across training sessions
2. **Unified Server** - Training + inference in single process (convenient for development)
3. **Context Manager Pattern** - DemoRunner __enter__/__exit__ for resource cleanup (DB connections, TensorBoard writers)
4. **WebSocket Broadcasting** - Server broadcasts state at configurable speed (0.2s default, 10,000 total episodes)

### Integration Points

- **Compile-time**: DemoRunner invokes Universe Compiler if .compiled/ missing
- **Runtime**: Orchestrates population training, broadcasts to WebSocket clients, logs to database

### Code Quality Observations

- **Strengths**: Clean orchestration pattern, comprehensive checkpoint management, real-time visualization support
- **Concerns**: Overlapping responsibilities (runner.py, unified_server.py, live_inference.py could be better separated), some methods have deep nesting

---

## 12. Recording System

**Location**: `src/townlet/recording/`
**Confidence**: MEDIUM

### Responsibility
Episode recording to compressed binary format (msgpack + lz4), replay playback, video export to MP4 (via matplotlib + ffmpeg), and recording criteria (interesting episodes). Optional extra dependency for episode analysis and presentation.

### Key Components

1. **recorder.py** - EpisodeRecorder captures environment state to compressed binary
2. **replay.py** - EpisodeReplay playback from recordings
3. **video_export.py** - VideoExporter MP4 generation via matplotlib + ffmpeg
4. **video_renderer.py** - VideoRenderer frame rendering (matplotlib)
5. **criteria.py** - RecordingCriteria triggers (high reward, long survival, low survival)
6. **data_structures.py** - Recording data formats (EpisodeData, FrameData)
7. **__main__.py** - CLI entry point (`python -m townlet.recording {export,batch}`)

### Dependencies

**Inbound**:
- **Demo Runner** → triggers recordings based on criteria
- **CLI tools** → export/batch commands for MP4 generation

**Outbound**:
- **Vectorized Environment** → queries environment state for frame capture
- **Population** → queries Q-values for episode visualization

**External**:
- **msgpack** - Binary serialization
- **lz4** - Compression
- **matplotlib** - Frame rendering
- **ffmpeg-python** - Video export (optional extra)
- **Pillow** - Image manipulation (optional extra)

### Architectural Patterns

- **Memento Pattern**: EpisodeRecorder captures complete episode state for replay
- **Observer Pattern**: Recording criteria observe training progress for trigger decisions
- **Command Pattern**: CLI commands (export, batch) for video generation

### Key Abstractions

- **EpisodeRecorder**: Captures environment state to binary format
- **EpisodeReplay**: Replays episodes from recordings
- **RecordingCriteria**: Decision logic for which episodes to record

### Notable Design Decisions

1. **Optional Extra** - Recording is `[recording]` extra in pyproject.toml (not required for training)
2. **Compressed Binary** - msgpack + lz4 for efficient storage (episodes can be long)
3. **Interesting Episodes** - Criteria trigger recordings for pedagogically valuable episodes (high reward, long survival, early failures)
4. **MP4 Export** - Matplotlib + ffmpeg pipeline for presentation-ready videos

### Integration Points

- **Compile-time**: None (recording is runtime-only)
- **Runtime**: Demo triggers recordings, CLI exports to MP4 post-training

### Code Quality Observations

- **Strengths**: Clean memento pattern implementation, comprehensive recording criteria
- **Concerns**: Optional extra status suggests lower integration priority, some overlap with demo/ subsystem (episode tracking)

---

## Summary: Subsystem Dependencies Graph

```
┌──────────────────────┐
│ Configuration System │ (DTOs)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐      ┌──────────────────────┐
│  Universe Compiler   │◄─────┤        VFS           │
└──────────┬───────────┘      └──────────────────────┘
           │
           ▼
┌──────────────────────┐
│ Vectorized Environ.  │◄─────┐
└──────────┬───────────┘      │
           │                  │
           ▼                  │
┌──────────────────────┐      │
│  Population Manager  │──────┘
└──────────┬───────────┘
           │
    ┌──────┴──────┬────────────────┬──────────────────┬──────────────────┐
    │             │                │                  │                  │
    ▼             ▼                ▼                  ▼                  ▼
┌────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐  ┌───────────┐
│ Agent  │  │ Substrate  │  │ Training   │  │   Exploration  │  │Curriculum │
│Networks│  │            │  │Infrastructure│  │                │  │           │
└────────┘  └────────────┘  └────────────┘  └────────────────┘  └───────────┘
                                                                       │
                                                                       ▼
                                                              ┌──────────────┐
                                                              │     Demo     │
                                                              └──────┬───────┘
                                                                     │
                                                                     ▼
                                                              ┌──────────────┐
                                                              │  Recording   │
                                                              └──────────────┘
```

**Critical Path**: Config System → Universe Compiler → VFS → Vectorized Environment → Population Manager

**Core Abstractions**: Agent Networks, Substrate, Training Infrastructure, Exploration, Curriculum

**Orchestration Layer**: Demo & Orchestration, Recording System

---

**End of Subsystem Catalog**

**Next Phase**: Architecture Diagram Generation (C4 diagrams)
