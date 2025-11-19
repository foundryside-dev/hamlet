# Architecture Diagrams: HAMLET Townlet

**Analysis Date**: 2025-11-19
**Notation**: C4-PlantUML
**Analyst**: Claude Code
**Source**: Discovery findings + Subsystem catalog

---

## Diagram Legend

**C4 Model Levels**:
- **Level 1 (Context)**: System in environment, external dependencies
- **Level 2 (Container)**: Major subsystems within system
- **Level 3 (Component)**: Internal structure of critical subsystems

**PlantUML Notation**:
- `Person()`: External user/actor
- `System()`: HAMLET Townlet system
- `System_Ext()`: External system
- `Container()`: Major subsystem/component
- `Component()`: Internal module/file
- `Rel()`: Relationship/dependency (solid line)
- `Rel_D()`: Dependency (dashed line)

---

## 1. Context Diagram (Level 1)

### Purpose
Shows HAMLET Townlet system in its operational environment, including external systems, users, and data flows. Illustrates the system's position within the pedagogical RL research workflow.

### Diagram

```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml

LAYOUT_WITH_LEGEND()

title Context Diagram: HAMLET Townlet System

Person(researcher, "Researcher/Student", "Configures experiments, trains agents, analyzes emergent behaviors")

System(hamlet, "HAMLET Townlet", "Pedagogical Deep RL environment: GPU-native vectorized training for multi-resource survival learning")

System_Ext(configs, "YAML Configurations", "Hierarchical v2.1 config packs (experiment, stratum, environment, levels)")
System_Ext(checkpoints, "Checkpoint Storage", "Persisted network weights, training state, replay buffers, provenance hashes")
System_Ext(frontend, "Vue.js Frontend", "Real-time visualization: grid, agents, meters, affordances, novelty heatmap")
System_Ext(tensorboard, "TensorBoard", "Metrics dashboard: rewards (extrinsic/intrinsic/total), survival, Q-values, loss")
System_Ext(mlflow, "MLflow", "Experiment tracking and hyperparameter management (optional)")
System_Ext(recordings, "Episode Recordings", "Compressed binary episodes (msgpack+lz4) for replay and MP4 export")

Rel(researcher, hamlet, "Runs experiments via CLI/scripts")
Rel(researcher, configs, "Authors/modifies config packs")
Rel(configs, hamlet, "Loaded & compiled by Universe Compiler")
Rel(hamlet, checkpoints, "Saves/loads (with drive_hash/brain_hash/config_hash provenance)")
Rel(hamlet, frontend, "Broadcasts agent state via WebSocket (port 8766)")
Rel(hamlet, tensorboard, "Logs metrics via TensorFlow SummaryWriter")
Rel(hamlet, mlflow, "Tracks experiments (optional)")
Rel(hamlet, recordings, "Captures interesting episodes (high reward, long survival)")
Rel(researcher, frontend, "Views real-time visualization")
Rel(researcher, tensorboard, "Views training metrics")
Rel(researcher, recordings, "Replays/exports episodes to MP4")

note right of hamlet
  **Technologies**
  - Python 3.13
  - PyTorch 2.9+
  - Gymnasium 1.0+
  - Pydantic 2.0+
  - PyYAML 6.0+
end note

@enduml
```

**Key Insights**:
- **Declarative Configuration**: All behavior defined in YAML, compiled into immutable artifacts
- **Provenance Tracking**: Checkpoints tagged with hashes preventing mismatches
- **Real-time Visualization**: WebSocket enables pedagogical observation of emergent behaviors
- **Dual Experiment Tracking**: TensorBoard (training) + MLflow (experimental)

---

## 2. Container Diagram (Level 2)

### Purpose
Shows the 12 major subsystems within HAMLET Townlet and their dependencies. Illustrates the compiler-driven architecture where Universe Compiler acts as the central integration point.

### Diagram

```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml

LAYOUT_WITH_LEGEND()

title Container Diagram: HAMLET Townlet Subsystems

System_Boundary(hamlet, "HAMLET Townlet System") {
    Container(config, "Configuration System", "Python, Pydantic 2.0+", "Validates v2.1 hierarchical configs, enforces no-defaults principle")

    Container(compiler, "Universe Compiler", "Python, PyYAML, msgpack", "7-stage pipeline: parse → symbol table → resolve → cross-validate → metadata → optimization → emit")

    Container(vfs, "VFS (Variable & Feature System)", "Python, Pydantic, PyTorch", "Declarative state space configuration, variable registry with GPU tensors")

    Container(environment, "Vectorized Environment", "Python, PyTorch, Gymnasium", "GPU-native batched RL environment: meters, affordances, rewards, temporal mechanics")

    Container(substrate, "Substrate System", "Python, PyTorch", "Spatial abstraction: Grid2D/3D/ND, Continuous, Aspatial")

    Container(agent, "Agent Networks", "Python, PyTorch", "SimpleQNetwork (MLP), RecurrentSpatialQNetwork (CNN+LSTM)")

    Container(population, "Population Manager", "Python, PyTorch", "Training loop orchestration: Q-networks, replay buffers, curriculum, exploration")

    Container(exploration, "Exploration Strategies", "Python, PyTorch", "RND, ICM, adaptive intrinsic, epsilon-greedy")

    Container(curriculum, "Curriculum System", "Python", "Static and adversarial difficulty progression")

    Container(training, "Training Infrastructure", "Python, PyTorch, NumPy", "Replay buffers, checkpointing, TensorBoard logging")

    Container(demo, "Demo & Orchestration", "Python, WebSockets, SQLite", "DemoRunner, live inference server, episode database")

    Container(recording, "Recording System", "Python, msgpack, lz4", "Episode capture, replay, MP4 export (optional)")
}

System_Ext(yaml_configs, "YAML Configs", "Hierarchical v2.1 config packs")
System_Ext(compiled_artifacts, "Compiled Artifacts", ".compiled/universe.msgpack")
System_Ext(checkpoint_storage, "Checkpoint Storage", "Network weights, training state")
System_Ext(frontend, "Vue.js Frontend", "Real-time visualization")

' Configuration flow
Rel(yaml_configs, config, "Loaded as Pydantic DTOs")
Rel(config, compiler, "DTOs validated during compilation")
Rel(vfs, compiler, "VFSAdapter integrates variable definitions")
Rel(compiler, compiled_artifacts, "Emits immutable artifacts (cached)")

' Runtime flow
Rel(compiled_artifacts, environment, "Loaded at initialization")
Rel(compiler, environment, "Provides CompiledUniverse")
Rel(environment, substrate, "Delegates position/movement operations")
Rel(environment, population, "step() returns obs/rewards/done")
Rel(environment, vfs, "Uses VariableRegistry for state storage")
Rel(population, agent, "Instantiates Q-networks via factory")
Rel(population, training, "Uses replay buffers, saves checkpoints")
Rel(population, exploration, "Delegates action selection")
Rel(population, curriculum, "Receives CurriculumDecision")
Rel(population, demo, "Orchestrated by DemoRunner")
Rel(demo, frontend, "Broadcasts state via WebSocket")
Rel(demo, recording, "Triggers episode captures")
Rel(training, checkpoint_storage, "Saves/loads checkpoints")

note right of compiler
  **Critical Path**
  Config → Compiler → VFS →
  Environment → Population
end note

note bottom of exploration
  **Strategy Pattern**
  Multiple implementations
  (RND, ICM, Adaptive)
end note

note bottom of substrate
  **Abstraction Layer**
  Grid2D/3D/ND,
  Continuous, Aspatial
end note

@enduml
```

**Architectural Patterns**:
- **Pipeline**: Universe Compiler 7-stage transformation
- **Facade**: VectorizedEnvironment orchestrates DAC, Affordance, Meter, Substrate engines
- **Strategy**: Exploration, Curriculum, Substrate have multiple implementations
- **Factory**: Network, Optimizer, Loss, Substrate, Curriculum factories
- **Memento**: Checkpoints, Compiled artifacts, Recordings
- **Registry**: Symbol Table, Variable Registry
- **Observer**: TensorBoard, WebSocket, Database

**Critical Path**: Configuration System → Universe Compiler → VFS → Vectorized Environment → Population Manager

---

## 3. Component Diagrams (Level 3)

### 3.1 Universe Compiler - 7-Stage Pipeline

### Purpose
Shows the internal structure of the Universe Compiler, emphasizing the 7-stage pipeline that transforms hierarchical YAML configs into immutable `CompiledUniverse` artifacts.

### Diagram

```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

title Component Diagram: Universe Compiler (7-Stage Pipeline)

Container_Boundary(compiler, "Universe Compiler") {
    Component(compiler_main, "compiler.py", "Python (3,100 LOC)", "UniverseCompiler class orchestrating 7-stage pipeline")

    Component(symbol_table, "symbol_table.py", "Python", "Name resolution, ID allocation for bars/affordances/actions")

    Component(compiled, "compiled.py", "Python", "CompiledUniverse immutable artifact with provenance (config_hash, drive_hash, brain_hash)")

    Component(optimization, "optimization.py", "Python", "Performance optimizations: tensor preallocation, vocabulary deduplication")

    Component(dto, "dto/", "Python, Pydantic", "ObservationSpec, MeterMetadata, AffordanceMetadata, ActionMetadata, UniverseMetadata")

    Component(vfs_adapter, "adapters/vfs_adapter.py", "Python", "VFSAdapter: converts VariableDef → ObservationField")

    Component(errors, "errors.py", "Python", "SymbolNotFoundError, CircularDependencyError, ValidationError")

    Component(cues_compiler, "cues_compiler.py", "Python", "Cue metadata compilation (UI hints)")

    Component(source_map, "source_map.py", "Python", "Source location tracking for error reporting")
}

System_Ext(config_system, "Configuration System", "Pydantic DTOs")
System_Ext(vfs_system, "VFS", "Variable definitions")
System_Ext(artifact_cache, ".compiled/universe.msgpack", "Cached artifacts")

Rel(config_system, compiler_main, "Loads config DTOs")
Rel(compiler_main, symbol_table, "Stage 2: Build symbol table")
Rel(symbol_table, symbol_table, "Allocates IDs for bars/affordances/actions")
Rel(compiler_main, vfs_adapter, "Stage 3: Integrate VFS variables")
Rel(vfs_system, vfs_adapter, "Provides VariableDef specs")
Rel(vfs_adapter, dto, "Produces ObservationFields")
Rel(compiler_main, optimization, "Stage 6: Optimize metadata")
Rel(compiler_main, compiled, "Stage 7: Emit CompiledUniverse")
Rel(compiled, artifact_cache, "Serialize to msgpack (cached)")
Rel(compiler_main, errors, "Raises on validation failures")
Rel(compiler_main, cues_compiler, "Compiles UI metadata")
Rel(compiler_main, source_map, "Tracks source locations for errors")

note right of compiler_main
  **7-Stage Pipeline**
  1. Parse YAML configs
  2. Build symbol table
  3. Resolve references
  4. Cross-validate
  5. Generate metadata
  6. Optimize
  7. Emit artifact
end note

note left of symbol_table
  **Global Vocabulary**
  Ensures consistent IDs
  across curriculum levels
end note

note bottom of compiled
  **Provenance Tracking**
  - config_hash (SHA256)
  - drive_hash (DAC config)
  - brain_hash (network arch)
end note

@enduml
```

**Key Insights**:
- **Sequential Pipeline**: Each stage transforms data, outputs feed next stage
- **Symbol Table Centralization**: All ID allocation happens here (ensures consistency)
- **Immutable Output**: CompiledUniverse is read-only, cached to disk
- **Provenance Hashes**: Prevents checkpoint mismatches (critical for reproducibility)

---

### 3.2 Vectorized Environment - Facade Pattern

### Purpose
Shows the internal structure of VectorizedEnvironment, emphasizing the facade pattern orchestrating multiple engines (DAC, Affordance, Meter, Temporal) and delegation to Substrate.

### Diagram

```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

title Component Diagram: Vectorized Environment (Facade Pattern)

Container_Boundary(environment, "Vectorized Environment") {
    Component(vectorized_env, "vectorized_env.py", "Python, PyTorch (1,839 LOC)", "VectorizedHamletEnv: Gymnasium interface, orchestrates engines")

    Component(dac_engine, "dac_engine.py", "Python, PyTorch (968 LOC)", "DACEngine: computes rewards from DAC specs (extrinsic + intrinsic + shaping)")

    Component(affordance_engine, "affordance_engine.py", "Python (551 LOC)", "AffordanceEngine: handles interaction resolution (delta_bars, success tracking)")

    Component(meter_dynamics, "meter_dynamics.py", "Python, PyTorch", "MeterDynamics: bar depletion, restoration, bounds enforcement")

    Component(action_builder, "action_builder.py", "Python", "ActionSpaceBuilder: composes substrate actions + custom actions")

    Component(temporal_utils, "temporal_utils.py", "Python", "TimeManager: day/night cycles, temporal state (L3)")

    Component(pomdp_builder, "pomdp_builder.py", "Python", "POMDP observation window (5×5 local vision for L2)")
}

System_Ext(compiled_universe, "CompiledUniverse", "Immutable config artifact")
System_Ext(substrate, "Substrate System", "Spatial abstraction")
System_Ext(vfs_registry, "VFS VariableRegistry", "GPU tensor storage")
System_Ext(population, "Population Manager", "Training loop")

Rel(compiled_universe, vectorized_env, "Loaded at __init__()")
Rel(vectorized_env, dac_engine, "Delegates reward computation")
Rel(vectorized_env, affordance_engine, "Delegates interaction resolution")
Rel(vectorized_env, meter_dynamics, "Delegates bar updates")
Rel(vectorized_env, action_builder, "Delegates action space composition")
Rel(vectorized_env, temporal_utils, "Queries time-based state (L3)")
Rel(vectorized_env, pomdp_builder, "Builds local observation window (L2)")
Rel(vectorized_env, substrate, "Delegates position/movement operations")
Rel(vectorized_env, vfs_registry, "Reads/writes variables")
Rel(population, vectorized_env, "Calls step(actions) → (obs, rewards, done)")

note right of vectorized_env
  **Facade Orchestration**
  Coordinates:
  - DAC (rewards)
  - Affordance (interactions)
  - Meter (resources)
  - Temporal (time)
  - Substrate (position)
  - VFS (state)
end note

note left of dac_engine
  **Declarative Rewards**
  extrinsic +
  (intrinsic × modifiers) +
  shaping
end note

note bottom of affordance_engine
  **Interaction Resolution**
  Applies delta_bars,
  tracks success,
  respects enabled status
end note

@enduml
```

**Key Insights**:
- **Facade Pattern**: VectorizedEnvironment provides simple Gymnasium interface, delegates complexity to specialized engines
- **Declarative Rewards**: DACEngine executes YAML-defined reward functions (no hardcoded strategies)
- **GPU-Native**: All state as PyTorch tensors with batch dimension [num_agents, ...]
- **Curriculum Integration**: Meter dynamics use CurriculumDecision (depletion rates, active meters)

---

### 3.3 Population Manager - Training Loop Orchestration

### Purpose
Shows the internal structure of Population Manager, emphasizing its role as the central orchestrator of the training loop, coordinating environment, networks, replay buffers, curriculum, and exploration.

### Diagram

```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

title Component Diagram: Population Manager (Training Loop)

Container_Boundary(population, "Population Manager") {
    Component(vectorized_pop, "vectorized.py", "Python, PyTorch (1,094 LOC)", "VectorizedPopulation: orchestrates training loop, manages Q-networks")

    Component(base, "base.py", "Python", "Abstract Population interface")

    Component(runtime_registry, "runtime_registry.py", "Python", "RuntimeAgentRegistry: tracks agent metadata (birth step, lifetime, level)")

    Component(factory, "factory.py", "Python", "PopulationFactory: creates population instances from config")
}

System_Ext(environment, "Vectorized Environment", "RL environment")
System_Ext(agent_networks, "Agent Networks", "Q-networks")
System_Ext(training_infra, "Training Infrastructure", "Replay buffers, checkpoints")
System_Ext(exploration, "Exploration Strategies", "RND, epsilon-greedy")
System_Ext(curriculum, "Curriculum System", "Difficulty progression")
System_Ext(demo, "Demo & Orchestration", "DemoRunner")

Rel(demo, factory, "Creates population instance")
Rel(factory, vectorized_pop, "Instantiates VectorizedPopulation")
Rel(vectorized_pop, environment, "Calls env.step(actions) → (obs, rewards, done)")
Rel(vectorized_pop, agent_networks, "Instantiates online + target Q-networks")
Rel(agent_networks, vectorized_pop, "forward(obs) → q_values")
Rel(vectorized_pop, training_infra, "Adds experiences to replay buffer")
Rel(training_infra, vectorized_pop, "Samples batches for training")
Rel(vectorized_pop, exploration, "Delegates action selection (epsilon-greedy, RND)")
Rel(vectorized_pop, curriculum, "Queries current CurriculumDecision")
Rel(curriculum, vectorized_pop, "Returns depletion rates, active meters")
Rel(vectorized_pop, runtime_registry, "Tracks per-agent metadata")
Rel(vectorized_pop, training_infra, "Saves/loads checkpoints")

note right of vectorized_pop
  **Training Loop**
  1. Select actions (explore)
  2. env.step(actions)
  3. Store in replay buffer
  4. Sample batch
  5. Compute loss (DQN/DoubleDQN)
  6. Backpropagate gradients
  7. Update target network
  8. Log metrics
  9. Save checkpoint
end note

note left of agent_networks
  **DQN Algorithms**
  - Vanilla DQN: max Q_target
  - Double DQN: argmax Q_online,
    evaluate Q_target
end note

note bottom of runtime_registry
  **Per-Agent Tracking**
  - Birth step
  - Lifetime survival
  - Curriculum level
end note

@enduml
```

**Key Insights**:
- **Central Orchestrator**: Population manages all training loop components
- **DQN Variants**: Configurable Vanilla DQN vs. Double DQN (reduces Q-value overestimation)
- **Target Network Updates**: Configurable frequency (e.g., every 1000 steps)
- **Batched Training**: Single backward() pass for entire batch (GPU efficiency)

---

## 4. Dependency Summary Graph

### Simplified Critical Path Visualization

```
YAML Configs
    ↓
Configuration System (Pydantic DTOs)
    ↓
Universe Compiler (7-stage pipeline)
    ↓ (+ VFS integration)
CompiledUniverse artifact (.compiled/universe.msgpack)
    ↓
Vectorized Environment (Gymnasium, GPU-native)
    ↓ (delegates to)
    ├─→ Substrate (position/movement)
    ├─→ DACEngine (rewards)
    ├─→ AffordanceEngine (interactions)
    └─→ MeterDynamics (resources)
    ↓
Population Manager (training loop)
    ↓ (coordinates)
    ├─→ Agent Networks (Q-networks)
    ├─→ Exploration (RND, epsilon-greedy)
    ├─→ Curriculum (difficulty progression)
    └─→ Training Infrastructure (buffers, checkpoints)
    ↓
Demo & Orchestration (multi-day training)
    ↓ (outputs)
    ├─→ Checkpoints (network weights + provenance)
    ├─→ TensorBoard (metrics)
    ├─→ WebSocket (frontend visualization)
    └─→ Recordings (episode capture)
```

---

## Diagram Notes

### Simplifications Made

1. **Not All Files Shown**: Component diagrams show key files (7-15 per subsystem), not all files
2. **External Dependencies Grouped**: PyTorch, Pydantic, PyYAML mentioned at subsystem level, not per-component
3. **Bidirectional Relationships**: Some relationships shown unidirectional for clarity (e.g., Environment ↔ Population shown as Population → Environment)
4. **Inheritance Not Shown**: Base classes (SpatialSubstrate, Population, ExplorationStrategy) implied by "Strategy Pattern" notes

### Assumptions

1. **C4-PlantUML Availability**: Diagrams assume access to C4-PlantUML stdlib (https://github.com/plantuml-stdlib/C4-PlantUML)
2. **PlantUML Rendering**: Diagrams require PlantUML renderer (VSCode extension, online editor, etc.)
3. **Technology Labels**: Based on pyproject.toml and import statements (not runtime inspection)

### Future Diagram Opportunities

1. **Data Flow Diagram**: Show tensor shapes and transformations ([num_agents, obs_dim] → [num_agents, action_dim])
2. **State Machine Diagram**: Curriculum stage transitions (L0 → L0.5 → L1 → L2 → L3)
3. **Sequence Diagram**: Training loop step-by-step (select_action → env.step → replay.add → train)
4. **Class Diagram**: Detailed inheritance hierarchies (SpatialSubstrate subclasses, ExplorationStrategy subclasses)

---

**End of Architecture Diagrams**

**Next Phase**: Final Architecture Report (synthesis of findings, catalog, diagrams)
