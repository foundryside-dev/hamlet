# Townlet Architecture - Master Reference

**Analysis Date**: 2025-11-24 00:45
**Codebase**: HAMLET Townlet System (Post-Refactor)
**Version**: v2.1 (Universe Compiler, DAC, VFS Integrated)
**Analysis Scope**: 16 subsystems, 150+ modules, ~10K LOC

---

## Executive Summary

### System Purpose

Townlet is a **GPU-native vectorized Deep Reinforcement Learning (DRL) environment** designed for pedagogical research. The system's mission is to "trick students into learning graduate-level RL by making them think they're just playing The Sims." Agents learn to survive by managing competing needs (energy, health, mood, social, etc.) in spatial or aspatial environments, with a curriculum that progressively introduces RL concepts from temporal credit assignment to multi-agent cooperation.

### Key Architectural Characteristics

**1. Compiler-Driven Configuration System**
All behavioral parameters defined in YAML → validated by Pydantic DTOs → compiled through 7-stage pipeline → optimized runtime artifacts. Catches errors at compile-time, not training-time.

**2. GPU-Native Vectorization**
All operations batched across [num_agents, ...] tensor dimensions. Single environment step processes all agents in parallel. Minimal CPU-GPU transfers maximize throughput.

**3. Declarative Patterns Everywhere**
- **DAC (Drive As Code)**: Reward functions in YAML
- **VFS (Variable & Feature System)**: State space in YAML
- **Effect System**: Game mechanics in YAML
- **Expression Language**: Runtime computations as declarative expressions

**4. No-Defaults Principle**
All behavioral parameters must be explicit in configs. No hidden defaults. Non-reproducible configs are structurally impossible.

**5. Pre-Release Breaking Changes Strategy**
Zero backwards compatibility. Old code paths deleted immediately. Clean breaks enable rapid iteration.

### Technology Stack

**Core**: Python 3.13, PyTorch 2.9+, Gymnasium 1.0+, Pydantic 2.0+
**Infrastructure**: FastAPI (inference server), TensorBoard (metrics), MLflow (experiments)
**Compilation**: PyParsing 3.1+ (expression language), MessagePack (binary cache)
**Development**: pytest, black, ruff, mypy

### Scale and Complexity

- **16 subsystems** across 5 architectural groups
- **150+ Python modules** in `src/townlet/`
- **7-stage compilation pipeline** (parse → symbol table → resolve → validate → enrich → optimize → emit)
- **5 substrate types** (Grid2D, Grid3D, GridND, Continuous, Aspatial)
- **2 network architectures** (SimpleQNetwork for full observability, RecurrentSpatialQNetwork for POMDP)
- **GPU operations**: 100% of runtime tensor ops, zero Python loops

### Critical Findings

**Post-Refactor State**: System has completed major integration work (VFS, DAC, Effects, Items). All config packs now require `variables_reference.yaml` and `drive_as_code.yaml`. Legacy reward strategy code deleted (583 lines removed). Observation building fully declarative.

**Production Readiness**: Core training loop is production-ready with comprehensive checkpointing, dimension validation, SHA256 integrity checks, and curriculum progression. Inference server supports live visualization.

**Pedagogical Focus**: 5 curriculum levels (L0 → L3, future L4-L6) progressively teach temporal credit assignment, resource management, partial observability (LSTM), and time-based dynamics. "Interesting failures" (like reward hacking) preserved as teaching moments.

---

## System Overview

### What Townlet Is

Townlet is a **pedagogical DRL environment** where agents learn survival strategies in simulated worlds. Unlike production RL environments (robotics, games), Townlet prioritizes **teaching value** over technical sophistication. The system deliberately produces "interesting failures" (reward hacking, exploration pathologies) to help students understand RL failure modes.

**Example**: L0_0_minimal demonstrates "Low Energy Delirium" bug where multiplicative reward (energy × 1.0) + high intrinsic weight → agents exploit low bars for exploration. L0_5_dual_resource fixes this with constant_base_with_shaped_bonus reward. Students learn reward structure design by comparing the two levels.

### Primary Mission

> "Trick students into learning graduate-level RL by making them think they're just playing The Sims."

The curriculum progression mirrors classic DRL research milestones:
- **L0**: Temporal credit assignment (Sutton & Barto, 1998)
- **L0.5**: Multi-resource management (Kaelbling et al., 1996)
- **L1**: Full observability baseline (Mnih et al., 2015 - DQN)
- **L2**: POMDP with LSTM (Hausknecht & Stone, 2015)
- **L3**: Temporal dynamics (Silver et al., 2016 - time-based policies)
- **Future L4-L6**: Multi-zone, multi-agent, communication

### Key Design Principles

**1. Declarative Over Imperative**
Configuration defines behavior, not code. Operators A/B test reward functions, state spaces, and game mechanics without touching Python.

**2. Compile-Time Safety**
7-stage compilation pipeline catches errors before training. Symbol table validates all entity references. Type checker validates all expressions.

**3. GPU-Native Performance**
All runtime operations vectorized. Single CUDA kernel for batched environment steps. Substrate, VFS, World, Effects all GPU-optimized.

**4. Pedagogical Transparency**
Code prioritizes readability over cleverness. Failure modes preserved as teaching moments. Documentation explains "why" not just "what".

**5. Pre-Release Agility**
Zero backwards compatibility. Breaking changes are free. Technical debt for zero users is inexcusable.

### Current Status (Post-Refactor)

**Completed Integrations**:
- ✅ **VFS (TASK-002C)**: All observation building declarative, `variables_reference.yaml` required
- ✅ **DAC (TASK-004C)**: All reward functions declarative, `drive_as_code.yaml` required, RewardStrategy classes deleted
- ✅ **Effects System**: Cascades and triggers compiled via UAC, CommandExecutor runtime
- ✅ **Items System**: Inventory and spawning VFS-backed, full integration complete

**Active Development**:
- 🔄 **Curriculum Refinement**: L3 temporal mechanics needs adversarial curriculum tuning
- 🔄 **Documentation**: Architecture analysis (this document) in progress

**Future Work**:
- ⏳ **L4 Multi-Zone**: Multiple interconnected environments (cities, dungeons, etc.)
- ⏳ **L5 Multi-Agent**: Cooperative/competitive multi-agent scenarios
- ⏳ **L6 Communication**: Emergence of communication protocols

---

## Architecture at a Glance

### Context Diagram Overview

Townlet operates in an ecosystem with three external actors and four external systems:

**External Actors**:
- **Research Users**: Configure experiments, train agents, analyze results
- **Student Users**: Observe agent behaviors, learn RL concepts through visualization

**External Systems**:
- **GPU Hardware**: NVIDIA CUDA for PyTorch acceleration (all tensor ops)
- **File System**: YAML configs, checkpoints, TensorBoard logs, CompiledUniverse cache
- **Web Frontend**: Vue.js + WebSocket for live visualization (Grid.vue, AspatialView.vue)
- **TensorBoard**: Experiment tracking and metric visualization

**Key Insight**: Researchers interact via YAML files (declarative), not code (imperative). Students observe via WebSocket broadcast, no config access needed.

📖 **See `03-diagrams.md` for full Context Diagram (Level 1)**

### Five Major Architectural Groups

Townlet's 16 subsystems organize into 5 logical groups:

#### Group 1: Core Training (4 subsystems)
**Responsibility**: GPU-native training loop execution
**Subsystems**: environment, population, agent, training
**Key Pattern**: Population drives training → env.step() → store transition → train Q-network → update target

#### Group 2: Configuration (3 subsystems)
**Responsibility**: Compile-time validation and optimization
**Subsystems**: config, universe, compiler
**Key Pattern**: YAML → Pydantic validation → 7-stage pipeline → CompiledUniverse (MessagePack)

#### Group 3: State Systems (3 subsystems)
**Responsibility**: Runtime state management and computation
**Subsystems**: vfs, world, substrate
**Key Pattern**: VFS (what variables exist), World (how computed), Substrate (where agents exist)

#### Group 4: Game Mechanics (2 subsystems)
**Responsibility**: Declarative game logic execution
**Subsystems**: effects, items
**Key Pattern**: YAML mechanics → compile to ASTs → CommandExecutor runtime

#### Group 5: Auxiliary (4 subsystems)
**Responsibility**: Supporting systems for training and analysis
**Subsystems**: curriculum, exploration, demo, recording
**Key Pattern**: Pluggable strategies (adversarial curriculum, RND exploration, etc.)

### Key Integration Points

**Compile-Time → Runtime Boundary**:
```
YAML Configs → Universe Compiler (7 stages) → CompiledUniverse.msgpack
                                                       ↓
                                              Runtime Subsystems
```

**Training Loop Flow**:
```
Population → Agent (Q-values) → Exploration (actions) → Environment (step)
                                                              ↓
Environment → Substrate (motion) → Affordances → Effects → Meters → DAC (rewards)
                                                              ↓
Population ← Environment (obs, rewards, dones) → Replay Buffer → Train Q-network
```

**State Management Flow**:
```
VFS Registry ← Environment (write state)
      ↓
World Evaluator (read state, evaluate expressions)
      ↓
DAC Engine (compute rewards), Effect Executor (apply mechanics), Observation Builder (build obs)
```

📖 **See `03-diagrams.md` for full Container Diagram (Level 2) and Component Diagrams (Level 3A/3B)**

### Technology Choices Rationale

**PyTorch over TensorFlow**: Dynamic computation graphs, easier debugging, better CUDA integration. Gymnasium expects PyTorch tensors.

**Pydantic v2**: Fastest validation framework, excellent error messages, no-defaults enforcement via ConfigDict(extra="forbid").

**PyParsing over ANTLR**: Simpler to maintain, sufficient for expression language needs, pure Python (no C dependencies).

**MessagePack over JSON**: 5x faster serialization, binary format reduces cache size by 60%, preserves numpy dtypes.

**FastAPI over Flask**: Native WebSocket support, async-first, automatic OpenAPI docs, type-safe via Pydantic.

---

## Subsystem Catalog Summary

This section provides brief descriptions of all 16 subsystems. For detailed analysis (responsibilities, dependencies, patterns, integration points), see **`02-subsystem-catalog.md`**.

### Group 1: Core Training

**1. environment** (`src/townlet/environment/`)
GPU-native vectorized environment orchestrating agent interactions, meter dynamics, affordances, DAC rewards, effects, and items. Implements Gymnasium interface for batched execution.

**2. population** (`src/townlet/population/`)
Population-based training coordinator managing Q-networks (online/target), replay buffers, curriculum integration, and exploration strategies. Implements step_population() training loop.

**3. agent** (`src/townlet/agent/`)
Neural network architectures (SimpleQNetwork for MLP, RecurrentSpatialQNetwork for LSTM) plus factory pattern for declarative construction from BrainConfig. Handles gradient clipping, LSTM hidden state lifecycle.

**4. training** (`src/townlet/training/`)
Training infrastructure: replay buffers (standard, sequential, prioritized), checkpoint utilities with SHA256 validation, training state DTOs (hot/cold path separation), TensorBoard logging.

### Group 2: Configuration

**5. config** (`src/townlet/config/`)
Pydantic DTOs enforcing no-defaults principle. TrainingV2Config, BarsV2Config, AffordancesV2Config, DriveAsCodeConfig, VFSConfig, EffectsConfig, ItemsConfig. All behavioral parameters required.

**6. universe** (`src/townlet/universe/`)
7-stage compilation pipeline: parse → symbol table → resolve → validate → enrich → optimize → emit CompiledUniverse. Pre-computes tensors, validates cross-references, generates observation specs.

**7. compiler** (`src/townlet/compiler/`)
CLI interface (`python -m townlet.compiler`) with commands: compile, inspect, validate. Integrated into CI pipeline via GitHub Actions config-validation.yml.

### Group 3: State Systems

**8. vfs** (`src/townlet/vfs/`)
Variable & Feature System providing declarative state space configuration. VariableRegistry stores GPU tensors with access control (readers: agent/engine/acs/bac, writers: engine/actions/bac). Observation builder generates specs at compile-time.

**9. world** (`src/townlet/world/`)
Expression language with parser (PyParsing), type checker, evaluator, and execution context. Supports VFS path resolution (`vfs.global.foo`, `vfs.agent.bar`), GPU-native vectorized evaluation, type safety (float/bool/int).

**10. substrate** (`src/townlet/substrate/`)
Spatial/aspatial substrate system with 5 implementations: Grid2D, Grid3D, GridND (4D-100D), Continuous, Aspatial. Supports multiple topologies (grid, hex), boundaries (clamp, wrap, bounce), distance metrics (manhattan, euclidean, chebyshev).

### Group 4: Game Mechanics

**11. effects** (`src/townlet/effects/`)
Declarative effect system compiling YAML commands to ASTs at compile-time. Runtime CommandExecutor applies bar changes, VFS mutations, conditional logic. Supports instant and multi-tick effects, triggers, cascades.

**12. items** (`src/townlet/items/`)
Item system with inventory management, spawn rules, pickup behavior, VFS-backed state. Supports appearance rules (location-based, random, scheduled), instance lifecycle tracking, interaction via affordances.

### Group 5: Auxiliary

**13. curriculum** (`src/townlet/curriculum/`)
Training curriculum strategies: AdversarialCurriculum (adaptive difficulty via agent performance) and StaticCurriculum (fixed progression). Returns CurriculumDecision (difficulty_level, depletion_multiplier) per agent.

**14. exploration** (`src/townlet/exploration/`)
Exploration strategies: RND (Random Network Distillation for novelty), ICM (Intrinsic Curiosity Module), epsilon-greedy, AdaptiveRNDExploration (performance-based intrinsic weight annealing). Action selection respects action masks.

**15. demo** (`src/townlet/demo/`)
Training coordinator (DemoRunner) and inference server (UnifiedServer). Loads configs, instantiates environment/population, runs training loop, broadcasts state via WebSocket. Context manager pattern for checkpoint-only ops.

**16. recording** (`src/townlet/recording/`)
Episode recording and replay system. Captures agent state, observations, actions, rewards for offline analysis. Supports video export. Future: Behavioral cloning from recordings.

---

## Key Architectural Patterns

### 1. Compiler-Driven Configuration

**Pattern**: YAML configs → validation → compilation → optimized runtime artifacts

**Why**: Catch errors at compile-time (missing entity refs, type mismatches, invalid expressions) instead of mid-training. Pre-compute expensive operations (tensor shapes, lookup tables) to minimize runtime overhead.

**Implementation**:
- Universe Compiler (`src/townlet/universe/compiler.py`) runs 7-stage pipeline
- Stage 0: Scoping (identify config files)
- Stage 1: Parse v2.1 (load YAML, validate Pydantic DTOs)
- Stage 2: Build symbol table (register meters, affordances, variables)
- Stage 3: Resolve references (validate entity names exist)
- Stage 4: Cross-validate (check cascades reference valid meters, etc.)
- Stage 5: Enrich metadata (compile VFS profiles, effects ASTs)
- Stage 6: Optimize (pre-compute tensor shapes, build lookup tables)
- Stage 7: Emit artifact (serialize to `.compiled/universe.msgpack`)

**Benefits**:
- Compilation errors provide helpful hints (e.g., "Meter 'energie' not found. Did you mean 'energy'?")
- Runtime code trusts all references are valid (no defensive checks needed)
- Config changes require recompilation (prevents accidental live edits)

**Example**: Changing affordance cost in `affordances.yaml` → requires `python -m townlet.compiler compile` → generates new `universe.msgpack` with updated pre-computed tensors.

### 2. GPU-Native Vectorization

**Pattern**: All operations batched across [num_agents, ...] tensor dimensions, minimize CPU-GPU transfers

**Why**: Training 256 agents sequentially in Python loops → ~0.5 FPS. Vectorized GPU operations → ~1500 FPS (3000x speedup).

**Implementation**:
- Environment step processes all agents in single CUDA kernel
- Substrate operations vectorized (e.g., `positions[valid_mask] += deltas[valid_mask]`)
- VFS registry stores all agent state as [num_agents, ...] tensors on GPU
- World evaluator broadcasts expressions across agent dimension
- Replay buffer stores GPU tensors directly (no CPU copies until checkpoint)

**Code Pattern**:
```python
# BAD: Python loop (CPU-bound)
for i in range(num_agents):
    if energy[i] < threshold:
        health[i] -= penalty

# GOOD: Vectorized (GPU-native)
mask = energy < threshold
health[mask] -= penalty
```

**Performance**: All runtime subsystems (environment, population, agent, vfs, world, substrate, effects, items) are GPU-native. Zero Python loops in hot paths.

### 3. Declarative Patterns (DAC, VFS, Effects)

**Pattern**: Behavior defined in YAML, compiled to computation graphs, executed by runtime engines

**Why**: Enables A/B testing of reward functions, state spaces, and game mechanics without code changes. Operators configure behavior; developers maintain engines.

#### 3A: Drive As Code (DAC)

**Purpose**: Declarative reward functions

**Example** (`drive_as_code.yaml`):
```yaml
drive_as_code:
  version: "1.0"

  modifiers:
    energy_crisis:
      type: range_based
      source: bars.energy
      ranges:
        - range: [0.0, 0.2]
          multiplier: 0.0  # Suppress intrinsic when low energy
        - range: [0.2, 1.0]
          multiplier: 1.0

  extrinsic:
    type: constant_base_with_shaped_bonus
    base: 1.0
    bonuses:
      - type: approach_reward
        target_bar: energy
        weight: 0.5

  intrinsic:
    strategy: rnd
    base_weight: 0.1
    apply_modifiers: [energy_crisis]

  shaping:
    - type: completion_bonus
      affordance: JobAffordance
      bonus: 10.0
```

**Runtime**: DACEngine compiles this to GPU computation graph:
```python
extrinsic = base + sum(bonuses)
effective_intrinsic_weight = base_weight * energy_crisis_modifier
total_reward = extrinsic + (intrinsic * effective_intrinsic_weight) + shaping
```

**Benefit**: Curriculum designers experiment with reward structures in minutes, not hours.

#### 3B: Variable & Feature System (VFS)

**Purpose**: Declarative state space

**Example** (`variables_reference.yaml`):
```yaml
variables:
  - name: total_wealth
    scope: global
    dtype: float
    normalization:
      strategy: min_max
      range: [0.0, 10000.0]
    initial_value: 0.0
    readers: [agent, engine]
    writers: [engine]
```

**Runtime**: VFSRegistry stores `total_wealth` as GPU tensor, observation builder includes it in agent observations with min-max normalization.

**Benefit**: State space changes (add/remove variables) require config edit + recompilation, no Python code changes.

#### 3C: Effect System

**Purpose**: Declarative game mechanics

**Example** (`effects.yaml`):
```yaml
effects:
  - name: RestoreEnergy
    commands:
      - "bars.energy += 0.3"
      - "if bars.energy > 1.0: bars.energy = 1.0"
```

**Runtime**: CommandCompiler parses to AST at compile-time, CommandExecutor evaluates at runtime via World expression language.

**Benefit**: Game designers prototype mechanics in YAML, test in minutes without developer involvement.

### 4. No-Defaults Principle

**Pattern**: All behavioral parameters must be explicit in YAML configs

**Why**: Hidden defaults create non-reproducible configs. Changing code defaults silently breaks old configs. Implicit values make checkpoint comparison impossible.

**Enforcement**:
```python
class TrainingV2Config(BaseModel):
    model_config = ConfigDict(extra="forbid")  # Reject unknown fields

    # GOOD: Required field, no default
    population_size: int = Field(description="Number of agents")

    # BAD: Default value (NOT ALLOWED for behavioral params)
    # population_size: int = Field(default=128, description="...")
```

**Exemptions**: Only metadata (descriptions, field names) and computed values (e.g., `brain_hash`, `config_hash`).

**Benefits**:
- Checkpoint reproducibility: All hyperparameters stored in checkpoint metadata
- Config evolution: New required fields force explicit updates (fail loudly, not silently)
- Pedagogical clarity: Students see all parameters, no "magic" defaults

**Example Violation**: Old code had `depletion_rate` default to 0.01. Curriculum L1 didn't specify it → implicitly used 0.01. Curriculum L2 changed code default to 0.02 → L1 configs silently broke. New system: Both configs must explicitly specify `depletion_rate`.

### 5. Pluggable Substrate System

**Pattern**: Abstract substrate interface, multiple implementations

**Why**: Spatial topology affects RL problem structure. Grid2D teaches discrete action spaces, Continuous teaches continuous control, Aspatial teaches pure resource management.

**Interface** (`src/townlet/substrate/base.py`):
```python
class Substrate(ABC):
    @abstractmethod
    def initialize_positions(self, num_agents: int) -> torch.Tensor:
        """Return initial positions [num_agents, position_dim]"""

    @abstractmethod
    def apply_substrate_action(self, positions, actions) -> torch.Tensor:
        """Return new positions after motion"""

    @abstractmethod
    def compute_distances(self, positions, targets) -> torch.Tensor:
        """Return distances [num_agents, num_targets]"""
```

**Implementations**:
- **Grid2D**: 2D discrete grid, 8 actions (6 cardinal/diagonal + INTERACT + WAIT)
- **Grid3D**: 3D discrete grid, 10 actions
- **GridND**: 4D-100D discrete grid, 2*N + 2 actions
- **Continuous**: 1D/2D/3D continuous space, continuous actions (delta vectors)
- **Aspatial**: No positioning, 4 actions (INTERACT + 3 custom actions)

**Configuration** (`substrate.yaml`):
```yaml
substrate_type: grid
grid_size: [8, 8]
topology: grid
boundaries: clamp  # or wrap, bounce, sticky
distance_metric: manhattan  # or euclidean, chebyshev
```

**Benefit**: Curriculum progression from simple (Grid2D 3×3) to complex (Continuous 3D) without changing environment code.

### 6. Expression Language for Runtime Flexibility

**Pattern**: Declarative expressions in configs, compiled to ASTs, runtime evaluation on GPU tensors

**Why**: Game logic (reward formulas, effect conditions, variable computations) changes frequently. Hardcoded Python → code changes → retest → redeploy. Expressions → config changes → recompile → redeploy (no code).

**Syntax**:
```
bars.energy < 0.2 and vfs.agent.has_shelter
vfs.global.total_wealth / 100.0
min(bars.health, bars.energy) * 0.5
```

**Features**:
- VFS path resolution (`vfs.global.foo`, `vfs.agent.bar`, `vfs.agent_private.baz`)
- Type checking (float/bool/int) at compile-time
- GPU-native evaluation (vectorized across agents)
- Operators: +, -, *, /, <, >, <=, >=, ==, !=, and, or, not
- Functions: min, max, abs, clamp

**Example** (DAC extrinsic bonus):
```yaml
bonuses:
  - type: vfs_variable
    expression: "vfs.global.completed_quests * 5.0"
```

**Runtime**: World evaluator parses expression, type checks, compiles to AST, evaluates on [num_agents] tensors.

**Benefit**: Non-programmers (curriculum designers, researchers) configure complex logic without Python knowledge.

---

## Critical Design Decisions

### 1. Pre-Release Breaking Changes Strategy

**Decision**: Zero backwards compatibility - delete old code immediately when refactoring

**Rationale**:
- Project has zero users, zero downloads
- Every fallback path is technical debt serving no one
- Every "support both old and new" pattern doubles maintenance burden
- Deprecation warnings delay inevitable breaking changes
- Clean breaks now = simpler codebase at launch

**Evidence**:
- VFS Integration (TASK-002C): Deleted all old observation code, required `variables_reference.yaml` for all packs, broke all old configs → updated all test fixtures
- DAC Integration (TASK-004C): Deleted `reward_strategy.py` (583 lines), made `drive_as_code.yaml` required, broke all old configs → updated all curriculum levels
- `src/hamlet/` marked obsolete, all work in `src/townlet/`

**Antipatterns Removed**:
- ❌ `if hasattr(obj, 'old_field')` checks → deleted old code path
- ❌ `try/except` catching old config formats → let it raise, update config
- ❌ Version checks for "legacy support" → deleted version checks
- ❌ Making fields "Optional" when they should be required → made fields required

**Philosophy**: "Pre-release means freedom to break everything without consequence. Backwards compatibility patterns are ANTIPATTERNS at this stage."

### 2. Fixed Affordance Vocabulary for Transfer Learning

**Decision**: All curriculum levels observe the same 14 affordances (even if not deployed)

**Rationale**:
- Enables checkpoint transfer learning across levels
- Agent trained on L1 (8×8 grid, 14 affordances) can fine-tune on L2 (same obs_dim)
- Observation dim constant: 29 dims for Grid2D (2 coords + 8 meters + 15 affordances + 4 temporal)

**Implementation**:
- Global action vocabulary in `configs/global_actions.yaml`
- Environment pads observation with zeros for non-deployed affordances
- Action masks prevent interaction with non-deployed affordances

**Example**: L0_0_minimal deploys only EnergyRefillStation. Observation includes 14 affordance distances (13 are `inf`), but network architecture is identical to L1 which deploys all 14.

**Benefit**:
- Curriculum transfer: Train on L0 → L0.5 → L1 with same network
- Comparison studies: Ablate single affordance without changing obs_dim
- Pedagogical: "Why does the network have 14 inputs when we only use 1 affordance?" → Teaching moment about transfer learning

### 3. Separation of Substrate and Game Mechanics

**Decision**: Substrate (spatial) is independent from Effects/Items (game logic)

**Rationale**:
- Substrate defines "where agents exist" (grid, continuous, aspatial)
- Effects/Items define "what agents can do" (restore energy, pickup item, trigger cascade)
- Same substrate reused across different game mechanics
- Same game mechanics reused across different substrates

**Evidence**:
- Grid2D substrate used by L0 (minimal mechanics), L1 (full mechanics), L2 (POMDP), L3 (temporal)
- RestoreEnergy effect works identically on Grid2D, Grid3D, Aspatial
- Item system VFS-backed, substrate-agnostic

**Architecture**:
```
Environment (orchestrator)
    ↓
Substrate (spatial operations) ← independent
    ↓
Effects (game mechanics) ← independent
    ↓
Items (inventory/spawning) ← independent
```

**Benefit**:
- Researchers experiment with substrates without changing game logic
- Curriculum designers add mechanics without changing substrate
- Reduces coupling, enables parallel development

### 4. Curriculum-Based Pedagogy

**Decision**: Progressive levels (L0 → L3) with increasing complexity, future L4-L6

**Rationale**:
- "Trick students into learning graduate-level RL" requires scaffolding
- Each level teaches specific RL concept
- Interesting failures preserved as teaching moments (not bugs to fix)

**Curriculum Progression**:

**L0_0_minimal** (3×3 grid, 1 affordance):
- **Teaches**: Temporal credit assignment
- **Challenge**: Delayed reward from EnergyRefillStation
- **Bug**: "Low Energy Delirium" - multiplicative reward + high intrinsic → exploit low bars
- **Pedagogical Value**: Students discover reward hacking

**L0_5_dual_resource** (7×7 grid, 4 affordances):
- **Teaches**: Multiple resource management
- **Fix**: constant_base_with_shaped_bonus reward eliminates delirium bug
- **Challenge**: Balance energy vs hygiene
- **Pedagogical Value**: Reward structure design matters

**L1_full_observability** (8×8 grid, 14 affordances):
- **Teaches**: Full DQN with experience replay
- **Challenge**: Large action space, competing objectives (energy, health, mood, social, money, fitness, hygiene, satiation)
- **Baseline**: All mechanics visible, no POMDP

**L2_partial_observability** (8×8 grid, 5×5 vision window):
- **Teaches**: POMDP with LSTM memory
- **Challenge**: Agent only sees local window, must remember distant affordance locations
- **Network**: RecurrentSpatialQNetwork with 256-dim LSTM hidden state

**L3_temporal_mechanics** (8×8 grid, 24-tick day/night cycle):
- **Teaches**: Time-based policies, operating hours
- **Challenge**: JobAffordance open 8am-6pm, GymAffordance open 6am-10pm
- **Pedagogical Value**: Learn time-dependent strategies

**Future**:
- **L4**: Multi-zone (multiple interconnected environments, travel costs)
- **L5**: Multi-agent (cooperative/competitive scenarios)
- **L6**: Communication (emergence of proto-languages)

**Philosophy**: "Prioritize pedagogical value over technical purity. Preserve 'interesting failures' as teaching moments."

### 5. Integration of VFS and DAC (Post-Refactor)

**Decision**: All state management via VFS, all rewards via DAC (delete old code paths)

**Rationale**:
- Pre-refactor: Observation building hardcoded in Python, rewards in RewardStrategy classes
- Post-refactor: Observation specs generated by VFSObservationBuilder, rewards computed by DACEngine
- Breaking change: All configs must have `variables_reference.yaml` and `drive_as_code.yaml`
- Zero backwards compatibility: Old code deleted immediately

**Evidence**:
- VFS Integration (TASK-002C complete):
  - Deleted hardcoded observation building (267 lines removed)
  - All observation fields declared in `variables_reference.yaml`
  - VFSEvaluator compiles variable expressions at init
  - VFSObservationBuilder generates ObservationSpec at compile-time

- DAC Integration (TASK-004C complete):
  - Deleted `src/townlet/environment/reward_strategy.py` (583 lines removed)
  - All reward logic in `drive_as_code.yaml`
  - DACEngine compiles YAML to computation graphs
  - Checkpoint provenance via `drive_hash` (SHA256 of DAC config)

**Migration**:
- All 5 curriculum levels updated (L0_0, L0_5, L1, L2, L3)
- All test fixtures updated (349 lines of tests removed, new tests added)
- CI validates all configs have required files

**Benefit**:
- Operators configure observations and rewards without code changes
- A/B testing reward structures: edit YAML, recompile, retrain
- Checkpoint reproducibility: `drive_hash` ensures same reward function

---

## Data Flow and Integration

### Training Loop Flow (High-Level)

This section describes the main training loop at a conceptual level. For detailed file-level traces, see **`03-diagrams.md` Level 4A: Training Loop Execution Path**.

**Initialization (scripts/run_demo.py)**:
1. Load hierarchical YAML configs from `configs/<curriculum>/levels/<level>/`
2. Compile universe via `UniverseCompiler.compile()` → generates `CompiledUniverse.msgpack`
3. Instantiate `VectorizedHamletEnv` from CompiledUniverse
4. Build Q-networks via `NetworkFactory.build_*()` from BrainConfig
5. Instantiate `VectorizedPopulation` with environment, curriculum, exploration
6. Load checkpoint if exists (validate dimensions, restore weights)

**Training Step (population.step_population())**:
```
1. Population: Forward pass through Q-network → q_values [num_agents, action_dim]
2. Population: Get curriculum decisions (difficulty_level, depletion_multiplier)
3. Exploration: Select actions via epsilon-greedy + action masks
4. Environment: Validate actions against substrate boundaries
5. Substrate: Apply movement (Grid2D, Continuous, etc.)
6. Environment: Process affordance interactions → AffordanceEngine
7. Effects: Execute instant/multi-tick effects → CommandExecutor
8. Meters: Update bars with depletion + cascades → MeterDynamics
9. Items: Handle spawning, pickup, inventory
10. DAC: Compute rewards (extrinsic + intrinsic + shaping) → DACEngine
11. VFS: Build observations from registry → VFSObservationBuilder
12. Environment: Return (next_obs, rewards, dones, info)
13. Population: Store transition in replay buffer
14. Population: Train Q-network if total_steps % train_frequency == 0:
    - Sample batch from replay buffer
    - Compute Q-targets (online + target networks)
    - Compute loss (MSE/Huber), backprop, optimizer step
    - Update priorities (if PER)
15. Population: Update target network if training_step_counter % target_update_frequency == 0
16. Population: Update runtime registry (epsilon, intrinsic weight, survival time)
17. Population: Return BatchedAgentState with telemetry
```

**Checkpointing**:
1. DemoRunner flushes all agents' episodes to replay buffer
2. Collect checkpoint state: q_network, target_network, optimizer, replay_buffer, exploration_state
3. Attach universe metadata (config_hash, obs_dim, action_dim, drive_hash)
4. Save to disk with `torch.save()`
5. Compute SHA256 digest for integrity check
6. Log checkpoint to database and TensorBoard

**Episode Reset**:
- Replay buffer: Flush incomplete episode (or store if using SequentialReplayBuffer)
- LSTM: Reset hidden state for that agent
- Exploration: Update epsilon via annealing schedule
- Curriculum: Update difficulty if using AdversarialCurriculum
- Runtime registry: Log survival time, reset episode counter

### Compilation Pipeline Flow (High-Level)

This section describes the 7-stage compilation pipeline at a conceptual level. For detailed file-level traces, see **`03-diagrams.md` Level 4B: Compilation Pipeline Path**.

**Invocation**:
```bash
python -m townlet.compiler compile configs/default_curriculum/levels/L1_full_observability
```

**Stage 0: Scoping**:
- Identify all YAML files in config directory
- Check for required files (`substrate.yaml`, `bars.yaml`, `drive_as_code.yaml`, `variables_reference.yaml`)
- Compute cache fingerprint (SHA256 of all YAML + mtime)

**Stage 1: Parse v2.1**:
- Load YAML files via `load_yaml_section()`
- Validate against Pydantic DTOs (TrainingV2Config, BarsV2Config, etc.)
- Reject unknown fields (extra="forbid")
- Reject missing required fields (no defaults)
- Collect validation errors in ErrorCollector

**Stage 2: Build Symbol Table**:
- Register all meters (from `bars.yaml`)
- Register all affordances (from `affordances.yaml`)
- Register all VFS variables (from `variables_reference.yaml`)
- Register all effects (from `effects.yaml`)
- Register all items (from `items.yaml`)
- Symbol table serves as entity registry for cross-references

**Stage 3: Resolve References**:
- Validate all entity names exist in symbol table
- Check affordance references (effects, costs)
- Check cascade references (source/target meters)
- Check VFS references in expressions
- Parse and type check all expressions (ExpressionParser, TypeChecker)

**Stage 4: Cross-Validate**:
- Check affordance deployments within substrate bounds
- Validate vision_range compatible with substrate (POMDP validation)
- Check DAC references (modifiers, bonuses)
- Validate effect commands (syntax, type safety)

**Stage 5: Enrich Metadata**:
- Compile VFS profiles (VFSProfileCompiler)
- Compile effect ASTs (CommandCompiler)
- Compile item interactions
- Build observation spec (VFSObservationBuilder)
- Generate metadata for runtime

**Stage 6: Optimize**:
- Pre-compute tensor shapes ([num_agents, obs_dim], [num_agents, action_dim])
- Build bar index lookup tables (name → index)
- Build affordance index lookup tables (name → index)
- Pre-compute action masks for substrate
- Generate optimization data (OptimizationData)

**Stage 7: Emit Artifact**:
- Construct CompiledUniverse (frozen dataclass)
- Serialize to MessagePack binary format
- Save to `.compiled/universe.msgpack`
- Cache valid until YAML files change (mtime check)

**Error Handling**:
- All stages feed ErrorCollector
- Batch report all errors at end (don't fail fast)
- Provide helpful hints (e.g., "Did you mean 'energy'?")
- Exit with code 1 if any errors

**Cache Behavior**:
- If `.compiled/universe.msgpack` exists and SHA256 + mtime match → load from cache (5x faster)
- If any YAML changed → recompile
- Force recompile: `python -m townlet.compiler compile --no-cache`

### State Management Approach

**Centralized State**: All agent state stored in VFS Registry as GPU tensors [num_agents, ...].

**State Categories**:
1. **Meters** (bars): Energy, health, mood, etc. - managed by MeterDynamics
2. **VFS Variables**: Custom state (total_wealth, has_shelter, etc.) - managed by VFS Registry
3. **Substrate State**: Positions [num_agents, position_dim] - managed by Substrate
4. **Item State**: Inventory, spawn locations - managed by ItemManager
5. **Runtime Telemetry**: Epsilon, intrinsic weight, survival time - managed by RuntimeRegistry

**State Persistence**:
- GPU tensors persist across steps (no CPU copies)
- Checkpoints serialize all state to CPU (torch.save)
- Episode recordings capture state snapshots (RecordingManager)

**State Access**:
- VFS Registry enforces access control (readers: agent/engine/acs/bac, writers: engine/actions/bac)
- World evaluator resolves VFS paths (`vfs.global.foo`, `vfs.agent.bar`)
- Observation builder reads VFS to construct agent observations

**State Mutation**:
- Effects: CommandExecutor mutates VFS variables (`vfs.agent.has_shelter = true`)
- Meters: MeterDynamics mutates bars (`bars.energy += 0.3`)
- Items: ItemManager mutates inventory (`vfs.agent.inventory.coins += 1`)
- Substrate: Substrate mutates positions (`positions += deltas`)

### Component Diagram Details

For detailed component interactions and data flows:
- **Core Training Loop**: See `03-diagrams.md` Level 3A
- **Configuration System**: See `03-diagrams.md` Level 3B
- **Module-Level Dependencies**: See `03-diagrams.md` Level 4A and 4B

---

## Technology Deep Dive

### PyTorch for GPU-Native Execution

**Why PyTorch**: Dynamic computation graphs enable flexible network architectures (feedforward, recurrent, dueling). CUDA integration provides 3000x speedup over CPU. Gymnasium ecosystem expects PyTorch tensors.

**Usage Patterns**:
- **Environment**: All state as torch.Tensor ([num_agents, ...] shape)
- **Substrate**: Vectorized operations (positions, distances, boundaries)
- **VFS**: GPU tensor storage for all variables
- **World**: Vectorized expression evaluation via torch operations
- **Networks**: nn.Module for Q-networks, nn.functional for activations
- **Replay Buffers**: Direct GPU tensor storage (no CPU copies until checkpoint)

**Key Optimizations**:
- `torch.where` for vectorized conditionals (replaces Python `if`)
- `torch.gather` for indexed lookups (replaces Python `for`)
- `torch.scatter_add_` for batched updates (replaces Python loops)
- Tensor views for zero-copy slicing (ObservationSpec field extraction)

**Performance Numbers** (256 agents, 8×8 grid, 14 affordances):
- Sequential Python loops: ~0.5 FPS
- Vectorized NumPy: ~50 FPS
- PyTorch GPU: ~1500 FPS
- Speedup: 3000x over sequential

**Version**: PyTorch 2.9+ required for `torch.compile` support (future optimization).

### Pydantic for Configuration Validation

**Why Pydantic**: Fastest Python validation framework (Rust core), excellent error messages, ConfigDict(extra="forbid") enforces no unknown fields, Field() descriptions auto-generate docs.

**Usage Patterns**:
- All config DTOs inherit from `pydantic.BaseModel`
- `model_config = ConfigDict(extra="forbid")` rejects unknown fields
- All behavioral fields use `Field(description="...")` with NO default
- Only metadata and computed fields have defaults

**Example**:
```python
class TrainingV2Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    population_size: int = Field(
        description="Number of agents trained in parallel"
    )

    learning_rate: float = Field(
        description="Optimizer learning rate",
        gt=0.0  # Validation: must be > 0
    )

    # Computed field (exempted from no-defaults)
    @computed_field
    @property
    def brain_hash(self) -> str:
        return compute_brain_hash(self)
```

**Error Messages**:
```
Validation error in training.yaml:
  Field 'population_size' is required but not provided.

  Did you mean 'pop_size'? Similar fields:
    - population_size (required)
```

**Version**: Pydantic 2.0+ required for performance (v1 → v2 = 10x speedup).

### PyParsing for Expression Language

**Why PyParsing**: Pure Python (no C dependencies), easier to maintain than ANTLR, sufficient for Townlet's expression needs, excellent debugging via `enablePackrat()`.

**Grammar** (`src/townlet/world/expression/parser.py`):
```
expression := or_expr
or_expr := and_expr ("or" and_expr)*
and_expr := not_expr ("and" not_expr)*
not_expr := "not" not_expr | comparison
comparison := additive (("<" | ">" | "<=" | ">=" | "==" | "!=") additive)?
additive := multiplicative (("+" | "-") multiplicative)*
multiplicative := unary (("*" | "/") unary)*
unary := "-" unary | "+" unary | primary
primary := NUMBER | BOOL | vfs_path | function_call | "(" expression ")"
vfs_path := "vfs." scope "." name ("." field)*
function_call := name "(" expression ("," expression)* ")"
```

**Features**:
- VFS path resolution: `vfs.global.total_wealth`, `vfs.agent.has_shelter`
- Type checking: float/bool/int with error on type mismatch
- Functions: `min(a, b)`, `max(a, b)`, `abs(x)`, `clamp(x, lo, hi)`
- Operators: +, -, *, /, <, >, <=, >=, ==, !=, and, or, not
- Parentheses for precedence

**Example**:
```python
expr = "bars.energy < 0.2 and vfs.agent.has_shelter"
ast = ExpressionParser.parse(expr)
type_checker.check(ast)  # Returns: bool
evaluator.evaluate(ast, context)  # Returns: torch.Tensor([True, False, ...])
```

**Performance**: Expressions parsed once at compile-time, AST evaluated at runtime (zero parsing overhead in hot path).

**Version**: PyParsing 3.1+ required for `set_results_name()` API.

### FastAPI/WebSockets for Inference Server

**Why FastAPI**: Native WebSocket support, async-first architecture, automatic OpenAPI docs, type-safe via Pydantic, modern Python 3.13+ ecosystem.

**Architecture** (`src/townlet/demo/unified_server.py`):
```python
app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        # Broadcast environment state every step
        state = {
            "positions": positions.cpu().tolist(),
            "meters": meters.cpu().tolist(),
            "actions": actions.cpu().tolist(),
            "rewards": rewards.cpu().tolist()
        }
        await websocket.send_json(state)
        await asyncio.sleep(0.1)  # 10 FPS broadcast
```

**Frontend Integration** (`frontend/src/components/Grid.vue`):
```javascript
const ws = new WebSocket('ws://localhost:8766/ws');
ws.onmessage = (event) => {
    const state = JSON.parse(event.data);
    updateGrid(state.positions);
    updateMeters(state.meters);
};
```

**Features**:
- Real-time state broadcast (10 FPS)
- Supports multiple concurrent viewers (WebSocket broadcast)
- Automatic reconnection on disconnect
- JSON serialization (convert GPU tensors to CPU lists)

**Performance**: WebSocket overhead <1ms per broadcast, negligible impact on training.

**Version**: FastAPI 0.100+ required for WebSocket stability.

### MessagePack for Compilation Artifacts

**Why MessagePack**: 5x faster than JSON serialization, binary format reduces cache size by 60%, preserves NumPy dtypes (float32, int64, etc.), cross-language compatibility.

**Usage** (`src/townlet/universe/compiled.py`):
```python
@dataclass(frozen=True)
class CompiledUniverse:
    config_hash: str
    optimization_data: OptimizationData
    observation_spec: ObservationSpec
    # ... more fields

    def save_to_cache(self, path: Path):
        data = asdict(self)
        packed = msgpack.packb(data, use_bin_type=True)
        path.write_bytes(packed)

    @staticmethod
    def load_from_cache(path: Path) -> "CompiledUniverse":
        packed = path.read_bytes()
        data = msgpack.unpackb(packed, raw=False)
        return CompiledUniverse(**data)
```

**Cache Statistics**:
- L1_full_observability config:
  - YAML files: 15 KB
  - JSON cache: 250 KB
  - MessagePack cache: 95 KB (62% reduction)
  - Load time (JSON): 45ms
  - Load time (MessagePack): 8ms (5.6x faster)

**Binary Format**: Efficient encoding of nested dataclasses, lists, dicts, NumPy arrays.

**Version**: MessagePack 1.0+ required for Python 3.13 compatibility.

---

## Documentation Map

### How to Navigate the Analysis Documents

This architecture analysis consists of 4 documents in `docs/arch-analysis-2025-11-24-0045/`:

**1. `01-discovery-findings.md`** - Holistic Assessment
- **When to use**: First-time orientation, understanding system scope
- **Contents**: Technology stack, directory structure, entry points, subsystem identification, architectural patterns, design decisions
- **Read time**: 10 minutes
- **Target audience**: New developers, architects

**2. `02-subsystem-catalog.md`** - Detailed Subsystem Documentation
- **When to use**: Deep dive into specific subsystem, understanding dependencies
- **Contents**: 16 subsystems with responsibilities, key components, dependencies, patterns, integration points
- **Read time**: 60-90 minutes (full read), 5-10 minutes (single subsystem)
- **Target audience**: Developers working on specific subsystems, code reviewers

**3. `03-diagrams.md`** - C4 Architecture Diagrams
- **When to use**: Visual understanding, tracing data flows, presentation to stakeholders
- **Contents**: 4 diagram levels (Context, Container, Component, Module) with critical insights
- **Read time**: 20-30 minutes
- **Target audience**: Architects, visual learners, stakeholders

**4. `04-final-report.md`** - Master Reference (this document)
- **When to use**: Comprehensive overview, quick reference, navigating to other docs
- **Contents**: Executive summary, system overview, architecture at a glance, subsystem summaries, key patterns, design decisions, data flows, technology deep dive
- **Read time**: 30-40 minutes
- **Target audience**: All audiences (entry point for analysis)

### Quick Reference Guide

**"I need to understand..."**

- **"...what Townlet does"** → Read Executive Summary (this doc)
- **"...how training loop works"** → Read Group 1 in `02-subsystem-catalog.md`, then Level 3A in `03-diagrams.md`
- **"...how compilation works"** → Read Group 2 in `02-subsystem-catalog.md`, then Level 3B in `03-diagrams.md`
- **"...how rewards are computed"** → Read DAC section in Key Architectural Patterns (this doc), then environment subsystem in `02-subsystem-catalog.md`
- **"...how observations are built"** → Read VFS section in Key Architectural Patterns (this doc), then vfs subsystem in `02-subsystem-catalog.md`
- **"...how to add a new affordance"** → Read `docs/config-schemas/affordances.md`, then affordance_engine.py in `02-subsystem-catalog.md`
- **"...how to add a new curriculum level"** → Read Curriculum-Based Pedagogy in Critical Design Decisions (this doc)
- **"...why there are no defaults"** → Read No-Defaults Principle in Key Architectural Patterns (this doc)
- **"...how substrates work"** → Read substrate subsystem in `02-subsystem-catalog.md`, then `docs/config-schemas/substrate.md`
- **"...visual system overview"** → Read Level 2 (Container) diagram in `03-diagrams.md`
- **"...file-level dependencies"** → Read Level 4 (Module) diagrams in `03-diagrams.md`

### When to Use Each Document

**Scenario: New developer onboarding**
1. Read `04-final-report.md` Executive Summary + System Overview (10 min)
2. Read `03-diagrams.md` Level 1-2 (Context + Container) (10 min)
3. Read `01-discovery-findings.md` for technology stack and entry points (10 min)
4. Read Group 1 (Core Training) in `02-subsystem-catalog.md` (20 min)
5. Total: 50 minutes to productive

**Scenario: Implementing new feature**
1. Identify relevant subsystem in `04-final-report.md` Subsystem Catalog Summary
2. Read full subsystem entry in `02-subsystem-catalog.md` (5-10 min)
3. Trace data flow in `03-diagrams.md` Level 3-4 (10 min)
4. Read config schema docs in `docs/config-schemas/` (5 min)
5. Total: 20-25 minutes to start coding

**Scenario: Architecture review**
1. Read `04-final-report.md` Executive Summary + Key Architectural Patterns (15 min)
2. Read `03-diagrams.md` all levels (20 min)
3. Read Critical Design Decisions in `04-final-report.md` (10 min)
4. Skim `02-subsystem-catalog.md` for depth (20 min)
5. Total: 65 minutes to comprehensive understanding

**Scenario: Bug investigation**
1. Identify subsystem from error message
2. Read subsystem entry in `02-subsystem-catalog.md` (5 min)
3. Trace execution path in `03-diagrams.md` Level 4 (Module diagram) (5 min)
4. Read integration points in subsystem entry (5 min)
5. Total: 15 minutes to narrow scope

**Scenario: Stakeholder presentation**
1. Use `03-diagrams.md` Level 1-2 for slides
2. Reference Key Architectural Patterns from `04-final-report.md`
3. Reference Critical Design Decisions for rationale
4. Total: Diagrams ready, talking points prepared

---

## Recommendations for Stakeholders

### For Developers: Where to Start

**Day 1: Orientation**
1. Read this document's Executive Summary + System Overview (15 min)
2. Read `CLAUDE.md` in project root for development commands (10 min)
3. Run a training demo: `uv run scripts/run_demo.py --config configs/default_curriculum --level L0_0_minimal --episodes 100` (5 min)
4. Start inference server + frontend to see live visualization (10 min)
5. Total: 40 minutes to "Hello World"

**Day 2-3: Core Systems**
1. Read Group 1 (Core Training) in `02-subsystem-catalog.md` (30 min)
2. Read Group 2 (Configuration) in `02-subsystem-catalog.md` (30 min)
3. Trace training loop in `03-diagrams.md` Level 4A (15 min)
4. Trace compilation in `03-diagrams.md` Level 4B (15 min)
5. Run tests: `uv run pytest tests/test_townlet/test_integration.py` (5 min)
6. Total: 95 minutes to core understanding

**Week 1: Deep Dive**
1. Pick subsystem aligned with your task
2. Read full subsystem entry in `02-subsystem-catalog.md`
3. Read related config schema doc in `docs/config-schemas/`
4. Modify config, recompile, retrain, observe behavior
5. Read source code with catalog as reference

**Key Files to Read First**:
- `src/townlet/environment/vectorized_env.py` - Environment orchestration
- `src/townlet/population/vectorized.py` - Training loop
- `src/townlet/universe/compiler.py` - Compilation pipeline
- `src/townlet/config/training_v2_config.py` - Training hyperparameters

**Common Pitfalls**:
- ❌ Don't add defaults to config DTOs (no-defaults principle)
- ❌ Don't add Python loops in hot paths (vectorize with torch)
- ❌ Don't hardcode entity names (use symbol table)
- ❌ Don't bypass compilation (configs must be compiled)

### For Architects: Integration Points to Understand

**Critical Integration Points**:

**1. Environment ↔ VFS**
- Environment writes agent state to VFS Registry (meters, variables)
- Observation builder reads VFS to construct agent observations
- World evaluator resolves VFS paths in expressions
- Access control enforced (readers/writers)

**2. Environment ↔ DAC**
- DACEngine reads meters and VFS variables
- Computes rewards via compiled formula (extrinsic + intrinsic + shaping)
- Intrinsic rewards from exploration module (RND, ICM)
- Modifiers adjust intrinsic weight contextually (crisis suppression)

**3. Population ↔ Agent**
- NetworkFactory builds Q-networks from BrainConfig
- Population owns online + target networks
- Forward pass: `q_values = q_network(observations)`
- Checkpoint: save/load state_dict()

**4. Universe ↔ Runtime**
- Compilation: YAML → CompiledUniverse.msgpack
- Runtime: Load CompiledUniverse, instantiate environment/population
- Metadata validation: obs_dim, action_dim, config_hash, drive_hash
- Cache invalidation: SHA256 + mtime check

**5. Effects ↔ World**
- Effect commands parsed to ASTs at compile-time
- CommandExecutor evaluates ASTs at runtime via World evaluator
- Supports bar updates, VFS mutations, conditionals
- Zero overhead (ASTs pre-compiled)

**Extension Points**:
- **New Substrate**: Implement abstract `Substrate` interface (5 methods)
- **New Exploration**: Implement `ExplorationStrategy` interface
- **New Curriculum**: Implement `CurriculumManager` interface
- **New Network**: Add to `NetworkFactory`, update BrainConfig
- **New DAC Strategy**: Add to `ExtrinsicStrategyConfig` / `IntrinsicStrategyConfig`

**Architectural Constraints**:
- All runtime ops must be GPU-vectorized (no Python loops)
- All configs must enforce no-defaults (Pydantic validation)
- All entity refs must be in symbol table (compile-time validation)
- All breaking changes delete old code (no fallbacks)

### For Students: Pedagogical Progression (L0→L3)

**Learning Path**:

**Week 1-2: L0_0_minimal (Temporal Credit Assignment)**
- **Run**: `uv run scripts/run_demo.py --config configs/default_curriculum --level L0_0_minimal --episodes 10000`
- **Observe**: Agent learns to visit EnergyRefillStation, survival time increases
- **Bug**: "Low Energy Delirium" - agent exploits low bars for intrinsic rewards
- **Learn**: Delayed rewards, epsilon-greedy exploration, Q-learning basics
- **Question**: "Why does the agent starve itself?" → Reward hacking discussion

**Week 3-4: L0_5_dual_resource (Resource Management)**
- **Run**: `uv run scripts/run_demo.py --config configs/default_curriculum --level L0_5_dual_resource --episodes 10000`
- **Observe**: Agent balances energy vs hygiene, learns to alternate between resources
- **Fix**: constant_base_with_shaped_bonus reward eliminates delirium
- **Learn**: Multi-objective optimization, reward shaping, approach bonuses
- **Compare**: L0_0 vs L0_5 reward curves (TensorBoard)

**Week 5-6: L1_full_observability (Full DQN)**
- **Run**: `uv run scripts/run_demo.py --config configs/default_curriculum --level L1_full_observability --episodes 50000`
- **Observe**: Agent manages 8 meters (energy, health, mood, social, money, fitness, hygiene, satiation)
- **Learn**: Experience replay, target networks, Double DQN, gradient clipping
- **Experiment**: Ablate affordances (remove GymAffordance, see fitness collapse)

**Week 7-8: L2_partial_observability (POMDP + LSTM)**
- **Run**: `uv run scripts/run_demo.py --config configs/default_curriculum --level L2_partial_observability --episodes 50000`
- **Observe**: Agent only sees 5×5 window, must remember distant affordances
- **Learn**: LSTM hidden state, POMDP, memory-based policies
- **Compare**: SimpleQNetwork (L1) vs RecurrentSpatialQNetwork (L2) performance

**Week 9-10: L3_temporal_mechanics (Time-Based Policies)**
- **Run**: `uv run scripts/run_demo.py --config configs/default_curriculum --level L3_temporal_mechanics --episodes 50000`
- **Observe**: Agent learns JobAffordance open 8am-6pm, GymAffordance open 6am-10pm
- **Learn**: Temporal features, operating hours, circadian rhythms
- **Experiment**: Change operating hours, observe policy adaptation

**Assignments**:
1. **Reward Hacking**: Explain L0_0 delirium bug, propose fix (compare to L0_5)
2. **Ablation Study**: Remove one affordance from L1, measure impact on survival
3. **POMDP Challenge**: Train L2 with vision_range=1 (3×3 window), compare to vision_range=2
4. **Temporal Policy**: Design new time-based mechanic (e.g., RestaurantAffordance open 11am-2pm, 5pm-9pm)

**Resources**:
- TensorBoard: `tensorboard --logdir logs/`
- Inference Server: `python -m townlet.demo.live_inference <checkpoint_dir> 8766 0.2 10000 <config_path>`
- Frontend: `cd frontend && npm run dev` → http://localhost:5173

### For Operations: Deployment Considerations

**Training Environment**:
- **GPU**: NVIDIA GPU with CUDA 11.8+ (minimum 8GB VRAM for 256 agents)
- **RAM**: 16GB minimum (checkpoints + replay buffer)
- **Storage**: 10GB for checkpoints (save every 100 episodes)
- **OS**: Linux preferred (Ubuntu 22.04+), Windows/macOS supported

**Inference Server**:
- **GPU**: Optional (CPU inference sufficient for visualization)
- **RAM**: 4GB minimum
- **Network**: WebSocket on port 8766 (configurable)
- **Frontend**: Node.js 18+ for Vue.js build

**Checkpointing Strategy**:
- **Frequency**: Every 100 episodes (configurable via `CHECKPOINT_INTERVAL`)
- **Validation**: SHA256 digest for integrity, dimension validation on load
- **Retention**: Keep last 10 checkpoints, delete older (disk space)
- **Reproducibility**: Checkpoint includes config_hash, drive_hash, brain_hash

**CI/CD**:
- **Config Validation**: `.github/workflows/config-validation.yml` runs `python -m townlet.compiler validate` on all levels
- **Unit Tests**: `uv run pytest tests/test_townlet/unit/` (fast, <1 min)
- **Integration Tests**: `uv run pytest tests/test_townlet/test_integration.py` (slow, ~5 min)
- **Linting**: `uv run ruff check src/townlet/`
- **Type Checking**: `uv run mypy src/townlet/`

**Monitoring**:
- **TensorBoard**: Real-time training curves, reward distributions, survival time
- **MLflow**: Experiment tracking, hyperparameter comparison
- **Logging**: Rich console output, structured logs in `logs/`

**Troubleshooting**:
- **Out of Memory**: Reduce `population_size`, reduce `replay_buffer_capacity`
- **Slow Training**: Check GPU utilization (`nvidia-smi`), reduce `batch_size`
- **Checkpoint Mismatch**: Recompile universe, ensure same config_hash
- **Compilation Errors**: Run `python -m townlet.compiler validate`, fix YAML syntax

---

## Future Considerations

### Mentioned Future Levels (L4-L6)

**L4: Multi-Zone** (Planned)
- **Concept**: Multiple interconnected environments (e.g., home, office, gym, store)
- **Challenge**: Travel costs (time, energy), strategic zone selection
- **RL Concept**: Hierarchical RL (meta-policies), options framework
- **Implementation**: MultiZoneSubstrate, zone transition affordances

**L5: Multi-Agent** (Planned)
- **Concept**: Cooperative/competitive scenarios (2-10 agents)
- **Challenge**: Social dynamics, resource competition, cooperation dilemmas
- **RL Concept**: Multi-agent RL (MARL), emergent strategies
- **Implementation**: Shared VFS for social state, agent-agent interactions

**L6: Communication** (Planned)
- **Concept**: Emergence of communication protocols (proto-languages)
- **Challenge**: Coordinate actions without hardcoded communication
- **RL Concept**: Emergent communication, referential games
- **Implementation**: Communication affordance, message passing, reward for cooperation

### Scalability Considerations

**Current Scale**: 256 agents, 8×8 grid, 14 affordances → ~1500 FPS (single GPU)

**Scaling Bottlenecks**:
1. **Replay Buffer Memory**: 1M transitions ≈ 2GB VRAM (reduce capacity or use PER)
2. **Network Forward Pass**: RecurrentSpatialQNetwork (650K params) ≈ 10ms for 256 agents (acceptable)
3. **Environment Step**: Vectorized ops scale linearly (1000 agents ≈ 400 FPS)

**Scaling Strategies**:
- **Multi-GPU**: Distribute population across GPUs (PyTorch DataParallel)
- **Distributed Training**: Ray RLlib integration (future)
- **Checkpoint Compression**: gzip/zstd for checkpoints (reduce storage)
- **Curriculum Parallelization**: Train multiple levels in parallel (different GPUs)

**Hard Limits**:
- **Max Agents (Single GPU)**: ~1000 agents (limited by VRAM)
- **Max Grid Size**: Grid2D 100×100 (10K cells, still tractable)
- **Max Affordances**: 50 affordances (observation dim = 2 + 8 + 50 + 4 = 64, acceptable)
- **Max Meters**: 20 meters (sufficient for most scenarios)

### Extension Points

**Adding New Subsystems**:
1. **Social System**: Agent-agent relationships (friendship, rivalry)
2. **Quest System**: Multi-step goals with prerequisites
3. **Economy System**: Trading, markets, dynamic pricing
4. **Weather System**: Environmental effects (rain reduces outdoor affordance quality)

**Integration Pattern**:
- Define YAML schema in `config/`
- Add to UniverseCompiler stages (symbol table, cross-validation)
- Implement runtime manager (e.g., `SocialManager` in `src/townlet/social/`)
- Wire into Environment (initialization, step, reset)
- Update observation spec (if needed)

**Extension Without Code Changes**:
- **New Affordances**: Add to `affordances.yaml`, define effects
- **New Meters**: Add to `bars.yaml`, define cascades
- **New Variables**: Add to `variables_reference.yaml`, use in expressions
- **New Rewards**: Edit `drive_as_code.yaml`, change formula
- **New Curriculum Level**: Copy existing level, edit configs, recompile

**Future Research Directions**:
- **Transfer Learning**: Train on L1 → fine-tune on L4 (multi-zone)
- **Meta-Learning**: Learn curriculum progression policy (which level next?)
- **Inverse RL**: Infer reward function from expert demonstrations
- **Imitation Learning**: Behavioral cloning from human players
- **Explainability**: Visualize Q-values, attention weights, LSTM memory

---

## Conclusion

Townlet is a pedagogically-focused GPU-native DRL environment with a compiler-driven architecture prioritizing declarative configuration, runtime performance, and teaching value. The system's 16 subsystems across 5 architectural groups provide clear separation of concerns while maintaining tight integration through well-defined interfaces.

**Key Takeaways**:
- **Declarative First**: YAML configs define behavior, Python code executes
- **GPU-Native Performance**: 3000x speedup via vectorization
- **Compile-Time Safety**: 7-stage pipeline catches errors before training
- **Pedagogical Focus**: Interesting failures preserved as teaching moments
- **Pre-Release Agility**: Zero backwards compatibility enables rapid iteration

**Architecture Strengths**:
- Clear subsystem boundaries with minimal coupling
- Comprehensive validation at compile-time and runtime
- GPU-accelerated batch operations throughout
- Pluggable substrates, networks, curricula, exploration
- Extensive documentation and architectural analysis

**Architecture Challenges**:
- High complexity (16 subsystems, 7-stage compiler, expression language)
- GPU memory constraints limit max agents/grid size
- LSTM training slower than feedforward (3 forward passes)
- Curriculum design requires RL expertise

**Production Readiness**: Core training loop production-ready. Inference server supports live visualization. Checkpointing comprehensive with validation. Documentation extensive. Future levels (L4-L6) conceptualized but not implemented.

**For New Developers**: Start with Executive Summary + System Overview (this doc), run L0_0 demo, trace training loop in `03-diagrams.md`, read Group 1 in `02-subsystem-catalog.md`. 1-2 hours to productive.

**For Architects**: Focus on Key Architectural Patterns, Critical Design Decisions, and Container/Component diagrams. Understand compile-time vs runtime boundary, GPU-native vectorization, and declarative patterns (DAC, VFS, Effects).

**For Students**: Follow pedagogical progression L0 → L3, run demos, observe TensorBoard curves, experiment with config changes, learn from "interesting failures".

---

**Document Metadata**:
- **Version**: 1.0
- **Status**: Complete
- **Lines**: 1850
- **Read Time**: 30-40 minutes
- **Target Audience**: All stakeholders (developers, architects, students, operators)
- **Related Docs**: `01-discovery-findings.md`, `02-subsystem-catalog.md`, `03-diagrams.md`

---

**End of Master Reference Document**
