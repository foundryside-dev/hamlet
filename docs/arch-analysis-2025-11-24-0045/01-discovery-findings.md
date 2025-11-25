# Discovery Findings - Townlet Architecture

**Analysis Date**: 2025-11-24 00:45
**Codebase**: HAMLET Townlet System (Post-Refactor)
**Source Root**: `src/townlet/`

## Executive Summary

Townlet is a **GPU-native vectorized Deep Reinforcement Learning environment** for pedagogical research. The system implements a pedagogical curriculum where agents learn to survive by managing competing needs (energy, health, mood, etc.) in spatial and aspatial environments. Architecture emphasizes **declarative configuration**, **compile-time validation**, and **runtime performance** through GPU-accelerated batch operations.

**Key Architectural Characteristics**:
- **Compiler-driven configuration system** (Universe Action Compiler - UAC)
- **GPU-native vectorized training** (PyTorch-based)
- **Modular substrate system** (Grid2D, Grid3D, GridND, Continuous, Aspatial)
- **Declarative reward functions** (Drive As Code - DAC)
- **Variable & Feature System** (VFS) for state management
- **Expression language** for runtime computations

**Scale**: ~150+ Python modules across 16 major subsystems, ~10K+ LOC

## Technology Stack

### Core Dependencies
- **Python 3.13** - Language runtime
- **PyTorch 2.9+** - GPU-native tensor operations, neural networks
- **Gymnasium 1.0+** - RL environment interface standard
- **Pydantic 2.0+** - Configuration validation (no-defaults principle)
- **PyParsing 3.1+** - Expression language parsing

### Infrastructure
- **FastAPI + WebSockets** - Inference server, live visualization
- **TensorFlow 2.20+** - TensorBoard logging integration
- **MLflow 2.9+** - Experiment tracking
- **NumPy/Pandas** - Data manipulation
- **Rich** - CLI formatting

### Development Tools
- **pytest** - Testing framework (unit, integration, E2E)
- **black/ruff** - Code formatting and linting
- **mypy** - Static type checking

## Directory Structure

```
src/townlet/
├── agent/              # Neural network architectures
├── compiler/           # CLI tool for universe compilation
├── config/             # Configuration DTOs (Pydantic)
├── curriculum/         # Training curriculum strategies
├── demo/               # Training runner, inference server
├── effects/            # Effect system (compiler, executor)
├── environment/        # Vectorized environment, affordances, DAC
├── exploration/        # Exploration strategies (RND, epsilon-greedy)
├── items/              # Item system (inventory, instances)
├── population/         # Population-based training
├── recording/          # Episode recording and replay
├── substrate/          # Spatial substrates (Grid2D, Continuous, etc.)
├── training/           # Training state, replay buffers
├── universe/           # Universe compiler (7-stage pipeline)
├── vfs/                # Variable & Feature System
└── world/              # Expression language (parser, evaluator)
```

## Entry Points

### Primary Entry Point
**`scripts/run_demo.py`** - Unified demo server
- Loads hierarchical YAML configs (`configs/default_curriculum/levels/<level>/`)
- Instantiates `UnifiedServer` from `townlet.demo.unified_server`
- Coordinates training, inference, and visualization
- Usage: `python run_demo.py --config configs/default_curriculum --level L1_full_observability --episodes 10000`

### CLI Tools
**`python -m townlet.universe`** - Universe compiler CLI
- Commands: `compile`, `inspect`, `validate`
- Compiles YAML configs → optimized runtime artifacts
- Integrated into CI via `.github/workflows/config-validation.yml`

**`python -m townlet.recording`** - Episode recording/replay
- Recording and playback of training episodes
- Video export functionality

## Subsystem Identification

**16 major subsystems identified** (4-12 expected, 16 indicates high modularity):

### Core Training Loop (4 subsystems)
1. **environment** - Vectorized environment execution
2. **population** - Population-based training logic
3. **agent** - Neural network architectures
4. **training** - Training state, replay buffers, checkpoints

### Configuration & Compilation (3 subsystems)
5. **config** - Configuration DTOs (no-defaults principle)
6. **universe** - Universe compiler (7-stage pipeline)
7. **compiler** - CLI interface for compilation

### State & Computation (3 subsystems)
8. **vfs** - Variable & Feature System (state management)
9. **world** - Expression language (runtime computations)
10. **substrate** - Spatial/aspatial substrates

### Game Mechanics (2 subsystems)
11. **effects** - Effect system (cascades, triggers)
12. **items** - Item system (inventory, pickups)

### Auxiliary Systems (4 subsystems)
13. **curriculum** - Training curriculum strategies
14. **exploration** - Exploration strategies (RND, ICM)
15. **demo** - Demo runner, inference server
16. **recording** - Episode recording and replay

## Architectural Patterns Observed

### 1. Compiler-Driven Configuration
- **Pattern**: YAML configs → validation → compilation → optimized runtime artifacts
- **Rationale**: Catch errors at compile-time, not training-time
- **Implementation**: Universe compiler (7-stage pipeline)

### 2. No-Defaults Principle
- **Pattern**: All behavioral parameters must be explicit in configs
- **Rationale**: Hidden defaults create non-reproducible configs
- **Implementation**: Pydantic DTOs with required fields

### 3. GPU-Native Vectorization
- **Pattern**: Batch operations on GPU tensors, minimize CPU-GPU transfers
- **Rationale**: Performance for population-based training
- **Implementation**: PyTorch tensors throughout, vectorized environment

### 4. Declarative Reward Functions (DAC)
- **Pattern**: Reward logic in YAML, compiled to computation graphs
- **Rationale**: A/B test reward structures without code changes
- **Implementation**: `drive_as_code.yaml` → DACEngine

### 5. Pluggable Substrate System
- **Pattern**: Abstract substrate interface, multiple implementations
- **Rationale**: Support diverse spatial/aspatial environments
- **Implementation**: Grid2D, Grid3D, GridND, Continuous, Aspatial

### 6. Expression Language for Runtime Flexibility
- **Pattern**: Declarative expressions in configs, runtime evaluation
- **Rationale**: Dynamic computations without hardcoded logic
- **Implementation**: PyParsing-based expression language in `world/`

## Key Design Decisions

### 1. Pre-Release Breaking Changes Strategy
**Decision**: Zero backwards compatibility - delete old code immediately
**Rationale**: Pre-release with zero users → clean breaks free
**Evidence**: `src/hamlet/` marked obsolete, VFS integration required, DAC mandatory

### 2. Curriculum-Based Pedagogy
**Decision**: Progressive levels (L0 → L3) with increasing complexity
**Rationale**: "Trick students into learning graduate-level RL"
**Evidence**: 5 curriculum levels in `configs/default_curriculum/levels/`

### 3. Fixed Affordance Vocabulary
**Decision**: All levels observe same 14 affordances (even if not deployed)
**Rationale**: Enables checkpoint transfer learning across levels
**Evidence**: Global action vocabulary in `configs/global_actions.yaml`

### 4. Separation of Substrate and Game Mechanics
**Decision**: Substrate (spatial) vs Effects/Items (game logic)
**Rationale**: Reuse spatial logic across different game mechanics
**Evidence**: Separate subsystems for substrate, effects, items

## Dependencies & Integration Points

### External Dependencies
- **Gymnasium** - RL environment interface (population → environment)
- **PyTorch** - Neural networks (agent), tensors (everywhere)
- **FastAPI/WebSockets** - Inference server (demo → frontend)
- **Pydantic** - Config validation (config → all subsystems)

### Internal Dependencies (High-Level)
- **universe → vfs, world, effects, items** - Compiler depends on state systems
- **environment → substrate, vfs, effects, items** - Environment orchestrates mechanics
- **population → agent, training** - Population manages networks and training
- **demo → population, environment, universe** - Demo coordinates training

## Configuration Structure

Hierarchical YAML configs per curriculum level:
```
configs/default_curriculum/levels/<level>/
├── substrate.yaml       # Spatial substrate (grid size, topology)
├── bars.yaml            # Meter definitions (energy, health, etc.)
├── affordances.yaml     # Interaction definitions
├── effects.yaml         # Effect definitions
├── items.yaml           # Item definitions
├── drive_as_code.yaml   # Reward function specification (REQUIRED)
├── training.yaml        # Hyperparameters
├── curriculum.yaml      # Curriculum strategy
└── variables_reference.yaml  # VFS configuration (REQUIRED)
```

**Breaking Change**: `variables_reference.yaml` and `drive_as_code.yaml` are REQUIRED for all config packs post-refactor.

## Complexity Assessment

**Overall Complexity**: HIGH
- 16 subsystems (high modularity)
- Compiler pipeline (7 stages)
- Expression language (parser, type checker, evaluator)
- GPU-native vectorization (performance-critical)
- Multiple substrate types (5 implementations)

**Coupling Assessment**: MEDIUM
- Clear subsystem boundaries
- Well-defined interfaces (Pydantic DTOs)
- Some tight coupling: universe ↔ vfs/world, environment ↔ substrate

**Documentation Quality**: HIGH
- Comprehensive CLAUDE.md with architecture overview
- Config schema docs in `docs/config-schemas/`
- Implementation plans in `docs/plans/`

## Orchestration Strategy Recommendation

**Recommendation**: PARALLEL analysis with 4 parallel groups

**Reasoning**:
1. **16 subsystems** - Too many for efficient sequential analysis
2. **Loose coupling** - Most subsystems have clear boundaries
3. **Time efficiency** - Estimated 3-4 hours solo → 1-2 hours parallel
4. **Clear groups** - Natural grouping by architectural layer

**Proposed Groups**:
- **Group 1**: Core Training (environment, population, agent, training) - 4 subsystems
- **Group 2**: Configuration (config, universe, compiler) - 3 subsystems
- **Group 3**: State Systems (vfs, world, substrate) - 3 subsystems
- **Group 4**: Game Mechanics (effects, items) - 2 subsystems
- **Group 5**: Auxiliary (curriculum, exploration, demo, recording) - 4 subsystems

**Subagent Allocation**: 5 parallel subagents, one per group

## Next Steps

1. **Update coordination log** with parallel strategy decision
2. **Create task specifications** for 5 subagent groups
3. **Spawn parallel subagents** for subsystem catalog generation
4. **Validation gate** after catalog completion
5. **Proceed to diagram generation**

## Confidence Level

**MEDIUM-HIGH**: Comprehensive directory scan, entry point analysis, and technology stack review completed. Subsystem boundaries clear from file organization. Some uncertainty about internal dependencies (will be resolved in detailed analysis).
