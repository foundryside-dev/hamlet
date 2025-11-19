# Final Architecture Report: HAMLET Townlet

**Analysis Date**: 2025-11-19
**Analyst**: Claude Code (System Archaeologist)
**Deliverable**: Architect-Ready Analysis
**Codebase**: `src/townlet/` (28,314 LOC, 104 Python files, 12 subsystems)

---

## Executive Summary

HAMLET Townlet is a **pedagogical Deep Reinforcement Learning environment** implementing a compiler-driven, GPU-native vectorized training system. The project's mission is to "trick students into learning graduate-level RL by making them think they're just playing The Sims" through multi-resource survival scenarios that produce pedagogically valuable emergent behaviors.

**Key Architectural Characteristics**:
1. **Declarative Configuration Over Code** - All behavioral parameters defined in hierarchical v2.1 YAML configs, enforcing "no-defaults principle"
2. **GPU-Native Vectorization** - All state as PyTorch tensors with batch dimension [num_agents, ...], minimizing CPU/GPU transfers
3. **Compiler-Driven Integration** - 7-stage Universe Compiler transforms YAML into immutable `CompiledUniverse` artifacts
4. **Pedagogical Abstraction Layers** - Substrate (spatial), Curriculum (difficulty), Exploration (intrinsic motivation) demonstrate RL concepts separately
5. **Pre-Release Agility** - Zero users, zero backwards compatibility constraints, aggressive refactoring encouraged

**Project Status**: Pre-release with recent major integrations (VFS TASK-002C complete, DAC runtime integration complete, config v2.1 hierarchical structure).

---

## Architecture Overview

### System Context

HAMLET Townlet operates within a pedagogical research workflow:
- **Inputs**: Hierarchical v2.1 YAML configuration packs (experiment, stratum, environment, levels)
- **Processing**: Universe Compiler → VectorizedEnvironment → Population training loop
- **Outputs**: Trained checkpoints (with provenance hashes), TensorBoard metrics, real-time WebSocket visualization, episode recordings

**External Dependencies**:
- PyTorch 2.9+ (deep learning, GPU tensors)
- Gymnasium 1.0+ (RL environment interface)
- Pydantic 2.0+ (schema validation)
- PyYAML 6.0+ (config parsing)
- WebSockets (live visualization)
- TensorFlow (TensorBoard only, not training)

### Subsystem Inventory

**12 Major Subsystems**:

1. **Universe Compiler** (3,100 LOC) - 7-stage pipeline: parse → symbol table → resolve → cross-validate → metadata → optimization → emit
2. **Configuration System** (18 Pydantic DTOs) - Validates hierarchical configs, enforces no-defaults principle
3. **Vectorized Environment** (1,839 LOC) - GPU-native batched RL environment (Gymnasium interface)
4. **Substrate System** (6 implementations) - Spatial abstraction (Grid2D/3D/ND, Continuous, Aspatial)
5. **Agent Networks** (2 architectures) - SimpleQNetwork (MLP, ~26K params), RecurrentSpatialQNetwork (CNN+LSTM, ~650K params)
6. **Population Manager** (1,094 LOC) - Training loop orchestration, DQN/Double DQN algorithms
7. **Exploration Strategies** (4 implementations) - RND, ICM, adaptive intrinsic, epsilon-greedy
8. **Curriculum System** (2 strategies) - Static and adversarial difficulty progression
9. **Training Infrastructure** (3 buffer types) - Replay buffers, checkpointing, TensorBoard logging
10. **VFS (Variable & Feature System)** - Declarative state space configuration, GPU tensor registry
11. **Demo & Orchestration** - DemoRunner, WebSocket server, SQLite episode database
12. **Recording System** (optional) - Episode capture (msgpack+lz4), MP4 export

---

## Architectural Patterns

### Primary Patterns

1. **Pipeline Pattern** (Universe Compiler)
   - 7 sequential stages transforming YAML → CompiledUniverse
   - Each stage outputs feed next stage
   - Immutable output artifact cached to disk

2. **Facade Pattern** (Vectorized Environment)
   - VectorizedHamletEnv orchestrates: DACEngine, AffordanceEngine, MeterDynamics, Temporal, Substrate, VFS
   - Provides simple Gymnasium interface (step, reset, render)
   - Delegates complexity to specialized engines

3. **Strategy Pattern** (Exploration, Curriculum, Substrate)
   - Multiple implementations sharing common interface
   - Exploration: RND, ICM, Adaptive, Epsilon-Greedy
   - Curriculum: Static, Adversarial
   - Substrate: Grid2D/3D/ND, Continuous, Aspatial

4. **Factory Pattern** (Pervasive)
   - NetworkFactory, OptimizerFactory, LossFactory, SubstrateFactory, CurriculumFactory, ExplorationFactory
   - Enables configuration-driven instantiation

5. **Memento Pattern** (Checkpoints, Compiled Artifacts, Recordings)
   - CompiledUniverse: Immutable config snapshot with provenance (config_hash, drive_hash, brain_hash)
   - Checkpoints: Networks, optimizer, replay buffer, training state
   - Recordings: Compressed episode state for replay

6. **Registry Pattern** (Symbol Table, Variable Registry)
   - Symbol Table: Global name-to-ID mapping for bars/affordances/actions
   - Variable Registry: GPU tensor storage with access control

7. **Observer Pattern** (TensorBoard, WebSocket, Database)
   - TensorBoard: Logs metrics (rewards, survival, Q-values, loss)
   - WebSocket: Broadcasts environment state to frontend
   - Database: Tracks episode metadata

---

## Critical Path: Data Flow

```
1. Configuration Loading
   YAML configs → Pydantic DTOs (Configuration System)

2. Compilation
   DTOs → Universe Compiler (7 stages) → CompiledUniverse artifact (.compiled/universe.msgpack)
   + VFS integration (variables_reference.yaml → ObservationSpec)

3. Environment Initialization
   CompiledUniverse → VectorizedHamletEnv.__init__()
   - Instantiates DACEngine (reward computation)
   - Instantiates AffordanceEngine (interaction resolution)
   - Instantiates Substrate (position/movement)
   - Loads VFS VariableRegistry (state storage)

4. Population Initialization
   CompiledUniverse metadata → VectorizedPopulation.__init__()
   - Instantiates Q-networks (online + target) via NetworkFactory
   - Instantiates ReplayBuffer (vanilla/sequential/prioritized)
   - Instantiates Exploration strategy (RND/epsilon-greedy/etc.)
   - Instantiates Curriculum (static/adversarial)

5. Training Loop
   For each step:
     a. Population.select_action() → (actions)
     b. Environment.step(actions) → (observations, rewards, dones)
     c. ReplayBuffer.add(transition)
     d. ReplayBuffer.sample(batch_size) → (batch)
     e. Population.train_on_batch(batch) → (loss, gradients)
     f. Optimizer.step() → (updated Q-network)
     g. Update target network (if step % target_update_frequency == 0)
     h. TensorBoard.log_metrics(rewards, loss, survival, Q-values)
     i. Curriculum.update_stage(performance) → (CurriculumDecision)

6. Checkpointing
   Population.save_checkpoint() → Disk
   - Networks (online, target)
   - Optimizer state
   - Replay buffer
   - Training state (step, episode, curriculum_stage)
   - Provenance hashes (drive_hash, brain_hash, config_hash)

7. Visualization (Parallel)
   LiveInferenceServer broadcasts via WebSocket:
   - Agent positions (from Substrate)
   - Meter values (from MeterDynamics)
   - Affordance locations
   - Novelty heatmap (from RND)
   - Action history
```

---

## Notable Design Decisions

### 1. Declarative Configuration (Drive As Code)

**Decision**: Reward functions fully declarative in `drive_as_code.yaml` (extrinsic + intrinsic + shaping + modifiers)

**Rationale**:
- Enables A/B testing without code changes
- Pedagogical transparency (students see reward structure directly)
- Replaced 583 LOC of hardcoded Python reward strategies

**Trade-offs**:
- More complex config schema
- Requires DAC engine runtime (968 LOC)
- **Benefit**: Reproducibility, config-driven experimentation

### 2. No-Defaults Principle

**Decision**: All behavioral parameters required in configs (no hidden defaults)

**Rationale**:
- Prevents non-reproducible configs (changing code defaults silently breaks old configs)
- Pre-release status allows aggressive schema evolution
- Forces explicit thinking about hyperparameters

**Trade-offs**:
- Verbose config files
- Higher barrier to entry
- **Benefit**: Perfect reproducibility, no surprising implicit behavior

### 3. GPU-Native Vectorization

**Decision**: All state as PyTorch tensors with batch dimension [num_agents, ...]

**Rationale**:
- Minimizes CPU/GPU transfers (major performance bottleneck)
- Enables batched operations (single forward/backward pass for entire population)
- Leverages PyTorch ecosystem

**Trade-offs**:
- Increased memory usage (all agents in memory simultaneously)
- Debugging complexity (tensor shapes, device placement)
- **Benefit**: ~10-100x speedup over sequential CPU implementation

### 4. Multi-Level Compilation

**Decision**: Single compile produces metadata for all curriculum levels (L0-L3)

**Rationale**:
- Ensures consistent global vocabulary (action/bar/affordance IDs)
- Enables checkpoint transfer across curriculum levels
- Reduces compilation overhead

**Trade-offs**:
- Compilation time proportional to number of levels
- Unused level metadata in memory
- **Benefit**: Curriculum progression without recompilation

### 5. Aspatial Substrate

**Decision**: Provide pure state machine substrate (no positioning)

**Rationale**:
- Pedagogical: Demonstrates positioning is optional, meters are "true universe"
- Simplest baseline for testing (no movement complexity)
- Enables non-spatial RL research

**Trade-offs**:
- Additional substrate implementation to maintain
- **Benefit**: Reveals fundamental RL concepts (meters, affordances, rewards) without spatial distraction

### 6. LSTM for POMDP

**Decision**: RecurrentSpatialQNetwork (CNN+LSTM, ~650K params) for partial observability (5×5 vision window)

**Rationale**:
- POMDP (partial observability) requires memory
- CNN extracts spatial features from local window
- LSTM maintains hidden state across timesteps
- Pedagogical: Demonstrates recurrent architectures for POMDPs

**Trade-offs**:
- 25x more parameters than SimpleQNetwork (~26K)
- Sequential replay buffer required (maintains episode coherence)
- 3 forward passes for Double DQN (online prediction, online selection, target evaluation)
- **Benefit**: Handles partial observability, teaches LSTM usage in RL

### 7. Checkpoint Provenance

**Decision**: SHA256 hashes (config_hash, drive_hash, brain_hash) stored in checkpoints

**Rationale**:
- Prevents accidental checkpoint mismatches (loading checkpoint with different config/DAC/network)
- Reproducibility (know exact config that produced checkpoint)
- Pre-release agility (configs change frequently)

**Trade-offs**:
- Checkpoints incompatible with config changes (must retrain)
- **Benefit**: Perfect reproducibility, prevents subtle bugs from config drift

---

## Integration Points

### Compile-Time Integration

**Universe Compiler** acts as central integration point:
- Loads Configuration System Pydantic DTOs
- Integrates VFS via VFSAdapter (VariableDef → ObservationField)
- Validates Substrate configs
- Produces CompiledUniverse artifact (cached to `.compiled/universe.msgpack`)

### Runtime Integration

**VectorizedEnvironment** consumes CompiledUniverse:
- Loads metadata (observation_dim, action_dim, bars, affordances)
- Instantiates DACEngine from DAC config
- Instantiates AffordanceEngine from affordance metadata
- Instantiates Substrate from stratum config
- Loads VFS VariableRegistry from variable definitions

**Population** coordinates training:
- Instantiates Q-networks from BrainConfig
- Drives Environment.step() loop
- Uses Training Infrastructure (replay buffers, checkpoints)
- Coordinates Exploration, Curriculum

**Demo** orchestrates multi-day training:
- Invokes Universe Compiler (if .compiled/ missing)
- Instantiates Population
- Manages checkpoint save/load across sessions
- Broadcasts to WebSocket for live visualization
- Logs to SQLite database

---

## Technology Stack Summary

### Core Technologies
- **Python 3.13** - Primary language
- **PyTorch 2.9+** - Deep learning, GPU tensors, gradient computation
- **Gymnasium 1.0+** - RL environment interface
- **Pydantic 2.0+** - Schema validation, DTOs
- **PyYAML 6.0+** - Hierarchical config parsing

### Infrastructure
- **msgpack** - Binary serialization (compiled artifacts)
- **lz4** - Compression (episode recordings)
- **WebSockets** - Real-time visualization
- **SQLite** - Episode database
- **TensorFlow** - TensorBoard logging only (not training)
- **MLflow** - Experiment tracking (optional)

### Development Tools
- **pytest** - Testing (integration, e2e, gpu, slow markers)
- **black** - Code formatting
- **ruff** - Linting
- **mypy** - Type checking
- **uv** - Package manager (modern pip replacement)

---

## Code Quality Observations (High-Level)

**Strengths**:
1. **Clear Separation of Concerns** - Config, compiler, environment, training well-separated
2. **Comprehensive Abstractions** - Strategy pattern enables pedagogical comparison (exploration, curriculum, substrate)
3. **Provenance Tracking** - Hashes ensure reproducibility
4. **Extensive Documentation** - Docstrings, type hints, comprehensive CLAUDE.md

**Areas for Improvement**:
1. **Large Files** - compiler.py (3,100 LOC), vectorized_env.py (1,839 LOC), live_inference.py (1,213 LOC) could be split
2. **Overlapping Responsibilities** - demo/ subsystem has multiple orchestration files (runner.py, unified_server.py, live_inference.py)
3. **Code Duplication** - Some replay buffer implementations share logic, some substrate implementations have duplicated boundary handling

**Note**: Detailed code quality assessment provided in separate document (05-quality-assessment.md).

---

## Recommendations for Improvement

### Architectural Improvements

1. **Modularize Large Files**
   - Split `compiler.py` (3,100 LOC) into stage-specific modules
   - Split `vectorized_env.py` (1,839 LOC) into environment core + engine orchestration
   - Split `live_inference.py` (1,213 LOC) into server + state broadcasting

2. **Clarify Demo Subsystem Boundaries**
   - Consolidate runner.py, unified_server.py, live_inference.py responsibilities
   - Consider: DemoRunner (orchestration), InferenceServer (WebSocket), SessionManager (checkpoint/database)

3. **Extract Shared Utilities**
   - Replay buffer shared sampling logic
   - Substrate shared boundary handling logic

### Configuration Improvements

4. **Config Schema Documentation**
   - Generate JSON Schema from Pydantic models
   - Provide autocomplete support for YAML editors

5. **Config Validation CLI**
   - `python -m townlet.compiler validate <config>` already exists
   - Enhance with warnings (not just errors) for suboptimal configs

### Testing & Observability

6. **Test Coverage Analysis**
   - Identify subsystems with weak test coverage
   - Priority: Universe Compiler, VFS, DAC Engine (critical path)

7. **Observability Enhancements**
   - Add structured logging (JSON logs for programmatic analysis)
   - Add performance profiling hooks (torch.profiler integration)

**Note**: Detailed improvement roadmap provided in architect handover report (06-architect-handover.md).

---

## Appendix: Document Index

This architecture analysis consists of the following documents:

1. **00-coordination.md** - Analysis plan, execution log, deliverable selection
2. **01-discovery-findings.md** - Holistic assessment, subsystem inventory, technology stack
3. **02-subsystem-catalog.md** - Detailed analysis of all 12 subsystems (responsibility, components, dependencies, patterns)
4. **03-diagrams.md** - C4 architecture diagrams (Context, Container, 3 Component diagrams in PlantUML)
5. **04-final-report.md** - This document (executive summary and synthesis)
6. **05-quality-assessment.md** - Code quality analysis (complexity, duplication, smells, technical debt) - MANDATORY for Architect-Ready
7. **06-architect-handover.md** - Architect handover report (improvement recommendations, prioritization) - MANDATORY for Architect-Ready

**Validation Reports** (in `temp/`):
- `validation-01-discovery.md` - Gate 1 (APPROVED)
- `validation-02-catalog.md` - Gate 2 (APPROVED after 3 warnings fixed)
- `validation-03-diagrams-self.md` - Gate 3 (APPROVED, systematic self-validation)

---

## Conclusion

HAMLET Townlet demonstrates a well-architected pedagogical RL system with strong separation of concerns, comprehensive abstractions, and a compiler-driven declarative configuration approach. The architecture prioritizes pedagogical clarity (demonstrating RL concepts separately), reproducibility (provenance tracking), and performance (GPU-native vectorization).

The pre-release status enables aggressive architectural evolution without backwards compatibility constraints, as evidenced by recent major integrations (VFS, DAC, config v2.1). The codebase is production-ready for research/education use cases, with clear improvement opportunities documented in the code quality assessment and architect handover reports.

**Next Steps**: See `06-architect-handover.md` for prioritized improvement roadmap and architectural recommendations.

---

**End of Final Architecture Report**

**Prepared by**: Claude Code (System Archaeologist)
**Date**: 2025-11-19
**Status**: Ready for code quality assessment and architect handover
