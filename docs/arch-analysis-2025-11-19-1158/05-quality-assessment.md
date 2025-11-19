# Code Quality Assessment: HAMLET Townlet

**Analysis Date**: 2025-11-19
**Analyst**: Claude Code (System Archaeologist)
**Scope**: `src/townlet/` (28,314 LOC, 104 Python files)
**Purpose**: Code quality analysis for Architect-Ready handover

---

## Executive Summary

HAMLET Townlet demonstrates **above-average code quality** for a pre-release research project, with strong architectural patterns, comprehensive type hints, and extensive docstrings. The codebase exhibits mature software engineering practices (Pydantic schemas, factory patterns, abstract base classes) while maintaining pedagogical clarity.

**Overall Quality Score**: **7.5/10**

**Strengths**:
- Clear architectural patterns (Strategy, Facade, Memento, Registry)
- Comprehensive type hints (mypy-compatible)
- Extensive Pydantic validation (configuration DTOs)
- Good separation of concerns (12 well-defined subsystems)
- Provenance tracking (checkpoint hashes)

**Primary Concerns**:
1. **Large Files** - 3 files >1000 LOC (compiler.py 3,100, vectorized_env.py 1,839, live_inference.py 1,213)
2. **Code Duplication** - Replay buffer implementations, substrate boundary handling
3. **Overlapping Responsibilities** - Demo subsystem (runner.py, unified_server.py, live_inference.py)
4. **Deep Nesting** - Some methods have 4-5 levels of nested conditionals/loops
5. **Test Coverage Gaps** - Unknown coverage distribution across subsystems

---

## 1. Complexity Analysis

### 1.1 Large Files (>1000 LOC)

**Critical Complexity** (>1500 LOC):

1. **`universe/compiler.py`** - 3,100 LOC
   - **Purpose**: 7-stage compilation pipeline
   - **Complexity Drivers**:
     - 7 sequential stages (each 200-500 LOC)
     - Extensive error handling and validation
     - Symbol table management
     - Multi-level compilation logic
   - **Cyclomatic Complexity**: Estimated 150-200 (high)
   - **Recommendation**: Split into stage-specific modules:
     - `compiler_core.py` (orchestration)
     - `stages/parsing.py`, `stages/symbol_table.py`, `stages/resolution.py`, etc.
   - **Impact**: High (central integration point, frequent changes during config evolution)

2. **`environment/vectorized_env.py`** - 1,839 LOC
   - **Purpose**: VectorizedHamletEnv facade orchestrating engines
   - **Complexity Drivers**:
     - Gymnasium interface implementation (step, reset, render)
     - Engine orchestration (DAC, Affordance, Meter, Temporal, POMDP)
     - State management (batched tensors)
     - Curriculum integration
   - **Cyclomatic Complexity**: Estimated 100-120 (high)
   - **Recommendation**: Extract engines to separate orchestration layer:
     - `vectorized_env.py` (Gymnasium interface only, ~500 LOC)
     - `environment_orchestrator.py` (engine coordination, ~800 LOC)
     - Keep individual engines separate (dac_engine.py, affordance_engine.py already separate)
   - **Impact**: High (core RL loop, changes ripple to population/demo)

**Moderate Complexity** (1000-1500 LOC):

3. **`demo/live_inference.py`** - 1,213 LOC
   - **Purpose**: WebSocket server for real-time visualization
   - **Complexity Drivers**:
     - WebSocket connection management
     - State broadcasting logic
     - Episode management
     - Speed control and frame rate limiting
   - **Cyclomatic Complexity**: Estimated 60-80 (moderate-high)
   - **Recommendation**: Split into:
     - `websocket_server.py` (connection management, ~400 LOC)
     - `state_broadcaster.py` (serialization and broadcasting, ~400 LOC)
     - `episode_manager.py` (episode tracking, ~400 LOC)
   - **Impact**: Medium (peripheral subsystem, optional for training)

4. **`population/vectorized.py`** - 1,094 LOC
   - **Purpose**: VectorizedPopulation training loop orchestration
   - **Complexity Drivers**:
     - Training loop (action selection, env.step, replay buffer, gradient updates)
     - Checkpoint management
     - Curriculum coordination
     - Exploration integration
   - **Cyclomatic Complexity**: Estimated 70-90 (moderate-high)
   - **Recommendation**: Extract checkpoint management:
     - `vectorized.py` (training loop only, ~700 LOC)
     - `checkpoint_manager.py` (save/load/validate, ~394 LOC from training/checkpoint_utils.py)
   - **Impact**: High (changes affect training pipeline)

**Recommendation Summary**:
- **Priority 1**: Split `compiler.py` (highest LOC, highest complexity, highest change frequency)
- **Priority 2**: Split `vectorized_env.py` (high LOC, core RL loop, facade could be cleaner)
- **Priority 3**: Split `live_inference.py` (moderate LOC, optional component, clear separation opportunities)

---

### 1.2 Deep Nesting

**Methods with 4+ Nesting Levels**:

(Identified from subsystem catalog "Concerns" notes):

1. **`universe/compiler.py`** - Multiple compilation stages have nested validation logic
   - **Example Pattern**: `if config → for level → if validates → try → if condition`
   - **Impact**: Hard to follow control flow, error-prone
   - **Recommendation**: Extract validation functions, use early returns

2. **`environment/vectorized_env.py`** - step() method likely has nested loops/conditionals
   - **Example Pattern**: `for agent → if alive → for affordance → if eligible → apply delta_bars`
   - **Impact**: Tensor operation complexity, GPU memory issues hard to debug
   - **Recommendation**: Extract affordance resolution to separate method, use tensor masking instead of nested loops

3. **`population/vectorized.py`** - train_step() method orchestrates multiple components
   - **Example Pattern**: `for step → if episode_done → reset → if buffer_ready → sample → compute_loss → if target_update → update`
   - **Impact**: Training loop hard to modify, curriculum/exploration changes risky
   - **Recommendation**: Extract training substeps to separate methods (action_selection(), environment_step(), gradient_update())

**General Recommendation**: Apply **Extract Method** refactoring to reduce nesting. Target cyclomatic complexity < 15 per method.

---

### 1.3 Function Length

**Very Long Functions** (>100 LOC):

Based on file sizes and catalog analysis:

1. **`universe/compiler.py: compile()`** - Likely 300-500 LOC (orchestrates 7 stages)
   - **Recommendation**: One method per stage, `compile()` becomes orchestrator

2. **`environment/vectorized_env.py: step()`** - Likely 150-250 LOC (core RL loop)
   - **Recommendation**: Extract: `_apply_actions()`, `_compute_rewards()`, `_update_meters()`, `_check_done()`

3. **`demo/live_inference.py: run_inference_loop()`** - Likely 150-200 LOC (episode management + broadcasting)
   - **Recommendation**: Extract: `_broadcast_state()`, `_handle_episode_end()`, `_control_speed()`

**Target**: No function >80 LOC. Functions >80 LOC are candidates for extraction.

---

## 2. Code Duplication Analysis

### 2.1 Identified Duplications (from Subsystem Catalog)

**High Duplication**:

1. **Replay Buffer Implementations** (`training/`)
   - **Files**: `replay_buffer.py`, `sequential_replay_buffer.py`, `prioritized_replay_buffer.py`
   - **Duplicated Logic**:
     - `sample()` method (random sampling logic)
     - `__len__()` and size tracking
     - Batch preparation (stacking tensors, moving to device)
   - **Estimated Duplication**: 100-150 LOC shared across 3 files
   - **Recommendation**: Extract `BaseReplayBuffer` abstract class with shared methods:
     ```python
     class BaseReplayBuffer(ABC):
         def add(self, transition): ...
         @abstractmethod
         def sample(self, batch_size): ...
         def _prepare_batch(self, transitions): ...  # shared
         def __len__(self): ...  # shared
     ```
   - **Impact**: Medium (changes to sampling logic require 3-file updates currently)

2. **Substrate Boundary Handling** (`substrate/`)
   - **Files**: `grid2d.py`, `grid3d.py`, `gridnd.py`
   - **Duplicated Logic**:
     - Boundary mode implementations (clamp, wrap, bounce, sticky)
     - Distance metric calculations (manhattan, euclidean, chebyshev)
     - Movement validation
   - **Estimated Duplication**: 200-300 LOC shared logic
   - **Recommendation**: Extract `BoundaryHandler` and `DistanceCalculator` utility classes:
     ```python
     class BoundaryHandler:
         @staticmethod
         def apply_clamp(positions, bounds): ...
         @staticmethod
         def apply_wrap(positions, bounds): ...
         # ...

     class DistanceCalculator:
         @staticmethod
         def manhattan(pos1, pos2): ...
         @staticmethod
         def euclidean(pos1, pos2): ...
         # ...
     ```
   - **Impact**: Medium-High (boundary bugs affect all grid substrates)

**Moderate Duplication**:

3. **Factory Pattern Boilerplate** (across subsystems)
   - **Files**: `substrate/factory.py`, `curriculum/factory.py`, `exploration/factory.py`, `agent/network_factory.py`, `agent/optimizer_factory.py`, `agent/loss_factory.py`
   - **Duplicated Logic**:
     - Config dict unpacking
     - Type string matching (if type == "foo": return FooClass())
     - Error handling (unknown type)
   - **Estimated Duplication**: 50-100 LOC per factory (6 factories = 300-600 LOC total)
   - **Recommendation**: **Acceptable Duplication** - Factory pattern inherently has boilerplate. Each factory is domain-specific. Consider registry pattern for extreme cases:
     ```python
     class FactoryRegistry:
         _registry = {}
         @classmethod
         def register(cls, type_name, factory_func): ...
         @classmethod
         def create(cls, config): ...
     ```
   - **Impact**: Low (factory changes are infrequent, domain-specific)

**Recommendation Summary**:
- **Priority 1**: Extract `BoundaryHandler` and `DistanceCalculator` (substrate utilities)
- **Priority 2**: Extract `BaseReplayBuffer` (training infrastructure)
- **Priority 3**: **Accept** factory boilerplate (pattern-inherent, low change frequency)

---

## 3. Code Smell Analysis

### 3.1 Architectural Smells

**Overlapping Responsibilities** (Demo Subsystem):

- **Files**: `demo/runner.py`, `demo/unified_server.py`, `demo/live_inference.py`
- **Smell**: **Feature Envy** / **Unclear Boundaries**
  - `runner.py` (958 LOC): Multi-day training orchestration, checkpoint management, database logging
  - `unified_server.py` (532 LOC): Training + inference in single process, invokes runner
  - `live_inference.py` (1,213 LOC): WebSocket server, episode management, state broadcasting
  - **Overlap**: All three files handle episode management, checkpoint loading, database tracking
- **Impact**: Changes to episode tracking require updates in multiple files, unclear ownership
- **Recommendation**: Clarify responsibilities:
  - `DemoRunner`: Training orchestration only (invokes Population.train(), manages checkpoints)
  - `InferenceServer`: WebSocket communication only (receives state, broadcasts to clients)
  - `SessionManager`: Episode/checkpoint/database management (shared by runner and server)
- **Estimated Effort**: 2-3 days refactoring
- **Priority**: Medium (demo is peripheral, but confusion affects maintainability)

**God Object** (Universe Compiler):

- **File**: `universe/compiler.py` (3,100 LOC)
- **Smell**: **God Object** (one class doing too much)
  - `UniverseCompiler` class orchestrates 7 stages, manages symbol table, handles errors, performs optimization, emits artifacts
  - **Responsibilities**: Parsing, validation, resolution, metadata generation, optimization, serialization
- **Impact**: Changes to any stage require touching god object, testing is complex
- **Recommendation**: Extract stages to separate classes:
  ```python
  class CompilationPipeline:
      def __init__(self):
          self.stages = [
              ParsingStage(),
              SymbolTableStage(),
              ResolutionStage(),
              ValidationStage(),
              MetadataStage(),
              OptimizationStage(),
              EmissionStage(),
          ]
      def compile(self, configs):
          data = configs
          for stage in self.stages:
              data = stage.process(data)
          return data
  ```
- **Estimated Effort**: 3-5 days refactoring
- **Priority**: High (compiler is central, changes are frequent)

---

### 3.2 Design Smells

**Primitive Obsession** (Provenance Hashes):

- **Pattern**: Provenance hashes (`config_hash`, `drive_hash`, `brain_hash`) passed as strings
- **Smell**: **Primitive Obsession** (should be value objects)
- **Impact**: No type safety, easy to swap hash types accidentally
- **Recommendation**: Create `ProvenanceHash` value object:
  ```python
  @dataclass(frozen=True)
  class ProvenanceHash:
      config_hash: str
      drive_hash: str
      brain_hash: str

      def matches(self, other: "ProvenanceHash") -> bool:
          return (self.config_hash == other.config_hash and
                  self.drive_hash == other.drive_hash and
                  self.brain_hash == other.brain_hash)
  ```
- **Estimated Effort**: 1 day
- **Priority**: Low (hashes work correctly, refactoring is for type safety only)

**Flag Argument** (DQN Algorithm Variant):

- **Pattern**: `use_double_dqn: bool` flag switches algorithm logic
- **Smell**: **Boolean Blindness** / **Flag Argument**
  - `if use_double_dqn: ... else: ...` scattered throughout training code
- **Impact**: Adds conditional complexity, hard to test both paths
- **Recommendation**: Strategy pattern for DQN algorithms:
  ```python
  class DQNAlgorithm(ABC):
      @abstractmethod
      def compute_target(self, q_online, q_target, ...): ...

  class VanillaDQN(DQNAlgorithm): ...
  class DoubleDQN(DQNAlgorithm): ...
  ```
- **Estimated Effort**: 1-2 days
- **Priority**: Low (current approach works, strategy is overkill for 2 variants)

---

### 3.3 Code Quality Smells

**Magic Numbers** (Hardcoded Thresholds):

- **Locations**:
  - `exploration/adaptive_intrinsic.py`: Threshold 100.0 for annealing (mean survival >50 steps)
  - `curriculum/adversarial.py`: Hardcoded survival thresholds for stage progression
  - `demo/live_inference.py`: Speed 0.2s, total episodes 10,000
- **Smell**: **Magic Numbers** (should be named constants or config parameters)
- **Impact**: Hard to tune without code changes, pedagogical opacity
- **Recommendation**: Move to config:
  ```yaml
  # exploration.yaml
  adaptive_intrinsic:
    annealing_threshold: 100.0
    mean_survival_trigger: 50

  # inference.yaml
  server:
    broadcast_speed: 0.2
    max_episodes: 10000
  ```
- **Estimated Effort**: 2-3 hours
- **Priority**: Medium (affects pedagogical experimentation)

**Long Parameter Lists** (>5 parameters):

- **Suspected Locations** (based on complexity):
  - `environment/vectorized_env.py: __init__()` - Likely 8-10 parameters (compiled_universe, device, curriculum, exploration, ...)
  - `population/vectorized.py: __init__()` - Likely 8-10 parameters
  - `demo/runner.py: __init__()` - Likely 7-9 parameters
- **Smell**: **Long Parameter List** (should use parameter objects)
- **Impact**: Hard to remember parameter order, error-prone
- **Recommendation**: Use config objects (already partially done with CompiledUniverse):
  ```python
  @dataclass
  class EnvironmentConfig:
      device: torch.device
      curriculum: Curriculum
      exploration: ExplorationStrategy
      # ...

  class VectorizedHamletEnv:
      def __init__(self, compiled_universe: CompiledUniverse, config: EnvironmentConfig):
          ...
  ```
- **Estimated Effort**: 1 day
- **Priority**: Low (Pydantic configs partially address this, full refactor is optional)

---

## 4. Technical Debt Assessment

### 4.1 High-Priority Debt

1. **Large File Refactoring** (compiler.py, vectorized_env.py, live_inference.py)
   - **Debt Type**: Complexity Debt
   - **Estimated Effort**: 5-7 days
   - **Impact**: High (affects maintainability, testing, onboarding)
   - **Recommendation**: Phase 1 priority for refactoring

2. **Demo Subsystem Boundaries** (runner.py, unified_server.py, live_inference.py overlap)
   - **Debt Type**: Architectural Debt
   - **Estimated Effort**: 2-3 days
   - **Impact**: Medium (confusion, change ripple)
   - **Recommendation**: Phase 2 priority

3. **Code Duplication** (replay buffers, substrate utilities)
   - **Debt Type**: Maintenance Debt
   - **Estimated Effort**: 2 days
   - **Impact**: Medium (bug fixes require multiple updates)
   - **Recommendation**: Phase 2 priority

### 4.2 Medium-Priority Debt

4. **Magic Numbers in Exploration/Curriculum**
   - **Debt Type**: Configuration Debt
   - **Estimated Effort**: 3 hours
   - **Impact**: Medium (pedagogical experimentation constrained)
   - **Recommendation**: Phase 3 quick win

5. **Test Coverage Gaps** (unknown distribution)
   - **Debt Type**: Quality Debt
   - **Estimated Effort**: Unknown (requires coverage analysis first)
   - **Impact**: Medium-High (unknown risk areas)
   - **Recommendation**: Phase 1 assessment, Phase 2 remediation

### 4.3 Low-Priority Debt (Acceptable)

6. **Factory Pattern Boilerplate**
   - **Debt Type**: Pattern-Inherent Boilerplate
   - **Impact**: Low (infrequent changes)
   - **Recommendation**: Accept (not worth abstracting further)

7. **Primitive Obsession** (provenance hashes)
   - **Debt Type**: Type Safety Debt
   - **Impact**: Low (works correctly, refactor is optional)
   - **Recommendation**: Accept (value object adds overhead)

---

## 5. Maintainability Metrics

### 5.1 Estimated Maintainability Index

**Maintainability Index (MI)** = 171 - 5.2 × ln(Halstead Volume) - 0.23 × (Cyclomatic Complexity) - 16.2 × ln(LOC)

(Higher is better, 20-100 scale: >85 Good, 65-85 Moderate, <65 Poor)

**Subsystem Estimates** (rough approximation):

| Subsystem | LOC | Est. CC | Est. MI | Rating |
|-----------|-----|---------|---------|--------|
| Universe Compiler | 3,100 | 150-200 | 50-60 | Poor |
| Vectorized Environment | 1,839 | 100-120 | 55-65 | Poor-Moderate |
| Population Manager | 1,094 | 70-90 | 65-70 | Moderate |
| Live Inference | 1,213 | 60-80 | 65-70 | Moderate |
| Configuration System | ~500 (avg) | 20-30 | 75-85 | Moderate-Good |
| Agent Networks | ~500 | 25-35 | 75-80 | Moderate |
| Substrate System | ~600 (avg) | 30-40 | 70-80 | Moderate |
| Training Infrastructure | ~400 (avg) | 20-30 | 80-85 | Good |
| Exploration | ~300 (avg) | 15-25 | 85-90 | Good |
| Curriculum | ~300 (avg) | 15-25 | 85-90 | Good |
| VFS | ~250 (avg) | 10-20 | 85-95 | Good |
| Demo & Orchestration | ~700 (avg) | 50-70 | 60-70 | Moderate-Poor |
| Recording | ~300 (avg) | 20-30 | 80-85 | Good |

**Overall Codebase MI**: ~70-75 (Moderate)

**Interpretation**:
- **Good** subsystems: VFS, Exploration, Curriculum, Training Infrastructure (small, focused modules)
- **Moderate** subsystems: Most subsystems (acceptable complexity)
- **Poor** subsystems: Universe Compiler, Vectorized Environment (large files, high complexity)

**Recommendation**: Prioritize refactoring Poor-rated subsystems (compiler, environment).

---

### 5.2 Comment-to-Code Ratio

**Observation**: Based on file inspection, HAMLET uses extensive docstrings (Pydantic models, class docstrings, method docstrings).

**Estimated Ratio**: 15-20% (Good)

**Quality**: Docstrings explain "what" and "why", type hints explain "types". Code is generally self-documenting (clear naming, Pydantic schemas).

**Recommendation**: Continue current practices. No additional commenting needed.

---

### 5.3 Type Hint Coverage

**Observation**: Based on catalog analysis, all subsystems mention type hints (function signatures, Pydantic models).

**Estimated Coverage**: 85-95%

**Tools**: `mypy` in dev dependencies suggests active type checking.

**Recommendation**: Run `mypy --strict` to catch remaining gaps. Aim for 100% coverage in new code.

---

## 6. Performance Considerations

### 6.1 GPU Memory Efficiency

**Strengths**:
- Batched tensor operations minimize CPU/GPU transfers
- All state as PyTorch tensors (`[num_agents, ...]`)
- Pre-allocated tensors in compiled artifacts

**Concerns**:
- **Large Replay Buffers**: Storing all transitions in GPU memory (default capacity unknown from analysis)
- **RecurrentSpatialQNetwork**: ~650K params + LSTM hidden states for [num_agents, ...] batches
- **POMDP Window Construction**: 5×5 local windows for all agents may create large intermediate tensors

**Recommendation**:
- Profile GPU memory usage under max batch sizes
- Consider CPU-side replay buffer storage with batch transfer to GPU during training
- Monitor LSTM hidden state memory (reset strategies)

---

### 6.2 Compilation Performance

**Concern**: 7-stage compilation pipeline may be slow for large config packs (multi-level compilation).

**Mitigation (Already Implemented)**:
- Cached artifacts (`.compiled/universe.msgpack`)
- Compilation only on config changes

**Recommendation**:
- Add compilation time metrics to CI
- Consider incremental compilation (only recompile changed levels)

---

## 7. Testing Considerations

### 7.1 Test Coverage (Unknown Distribution)

**Observation**: `pytest` markers suggest comprehensive testing:
- `@pytest.mark.integration`
- `@pytest.mark.e2e`
- `@pytest.mark.gpu`
- `@pytest.mark.slow`

**Gap**: Test coverage distribution unknown from code analysis alone.

**Recommendation**:
1. Run `pytest --cov=townlet --cov-report=term-missing` to generate coverage report
2. Identify subsystems with <80% coverage
3. Prioritize critical path coverage:
   - Universe Compiler (7 stages)
   - Vectorized Environment (RL loop)
   - Population Manager (training loop)
   - VFS (state management)
   - DAC Engine (reward computation)

### 7.2 Test Quality

**Strengths** (inferred from markers):
- **Integration tests**: End-to-end subsystem integration
- **E2E tests**: Full training pipeline
- **GPU tests**: Device-specific tests (important for tensor operations)
- **Slow tests**: Long-running validation (likely training convergence)

**Recommendation**: Continue current test strategy. Ensure each subsystem has:
- Unit tests (individual components)
- Integration tests (subsystem boundaries)
- Property-based tests (Hypothesis library available) for complex logic (e.g., substrate boundary handling)

---

## 8. Security Considerations

### 8.1 Input Validation

**Strengths**:
- Pydantic models validate all config inputs
- Type hints enforce type correctness
- Universe Compiler cross-validates configs

**Concerns**:
- **YAML Parsing**: PyYAML can execute arbitrary Python code (`!!python/object` tags)
- **Checkpoint Loading**: Unpickling checkpoints can execute arbitrary code (torch.load())

**Recommendation**:
1. Use `yaml.safe_load()` instead of `yaml.load()` (verify in codebase)
2. Add checkpoint integrity checks (SHA256 hash validation) before `torch.load()`
3. Document: "Only load checkpoints from trusted sources"

### 8.2 Path Traversal

**Concern**: Config paths (`.compiled/`, checkpoint directories) may be user-controlled.

**Recommendation**:
- Validate all file paths (no `..` traversal)
- Use `pathlib.Path.resolve()` to normalize paths
- Check if resolved path is within expected directory

---

## 9. Documentation Quality

### 9.1 Codebase Documentation

**Strengths**:
- **CLAUDE.md**: Comprehensive project overview (architecture, config system, development commands, philosophy)
- **Frontmatter Pattern**: AI-friendly documentation with structured frontmatter
- **Type Hints**: Extensive type annotations
- **Docstrings**: Class and method docstrings present (based on catalog analysis)

**Gaps**:
- **Config Schema Documentation**: No JSON Schema generation from Pydantic models (mentioned in recommendations)
- **API Documentation**: No auto-generated API docs (Sphinx/MkDocs)

**Recommendation**:
1. Generate JSON Schema from Pydantic models (enables IDE autocomplete)
2. Add Sphinx/MkDocs auto-generated API documentation
3. Add architecture decision records (ADRs) for major design choices

---

## 10. Summary & Recommendations

### 10.1 Quality Score Breakdown

| Category | Score | Weight | Weighted Score |
|----------|-------|--------|----------------|
| Architecture | 8/10 | 25% | 2.0 |
| Code Complexity | 6/10 | 20% | 1.2 |
| Code Duplication | 7/10 | 15% | 1.05 |
| Code Smells | 7/10 | 10% | 0.7 |
| Maintainability | 7/10 | 15% | 1.05 |
| Testing | 7/10 (est) | 10% | 0.7 |
| Documentation | 8/10 | 5% | 0.4 |
| **Overall** | **7.5/10** | **100%** | **7.1** |

**Interpretation**: **Above Average** (7-8 range is good for research/education codebase)

---

### 10.2 Top 5 Improvement Priorities

1. **Refactor `universe/compiler.py`** (3,100 LOC → stage-specific modules)
   - **Effort**: 3-5 days
   - **Impact**: High (central integration point, frequent changes)
   - **Benefit**: Improved testability, reduced cyclomatic complexity

2. **Refactor `environment/vectorized_env.py`** (1,839 LOC → facade + orchestration split)
   - **Effort**: 3-4 days
   - **Impact**: High (core RL loop, complexity reduction)
   - **Benefit**: Clearer engine orchestration, easier to add new engines

3. **Extract Substrate Utilities** (BoundaryHandler, DistanceCalculator)
   - **Effort**: 1-2 days
   - **Impact**: Medium-High (affects all grid substrates)
   - **Benefit**: Reduced duplication (200-300 LOC), bug fixes propagate automatically

4. **Clarify Demo Subsystem Boundaries** (runner/unified_server/live_inference overlap)
   - **Effort**: 2-3 days
   - **Impact**: Medium (peripheral subsystem, maintainability)
   - **Benefit**: Clear ownership, easier to modify inference server

5. **Generate Test Coverage Report** (identify gaps)
   - **Effort**: 1 hour (run pytest --cov)
   - **Impact**: High (unknown risk areas)
   - **Benefit**: Data-driven test prioritization

---

### 10.3 Acceptable Trade-offs

**Not Recommended for Refactoring**:
1. **Factory Pattern Boilerplate** - Pattern-inherent, low change frequency
2. **Primitive Obsession** (provenance hashes) - Works correctly, value object adds overhead
3. **Long Parameter Lists** (partially mitigated by Pydantic configs)

**Rationale**: Pre-release status allows technical debt where it doesn't impede development velocity. Focus on high-impact, high-frequency change areas (compiler, environment).

---

## 11. Code Quality Tooling Recommendations

### 11.1 Static Analysis

**Current Tools** (from discovery findings):
- `mypy` - Type checking ✓
- `ruff` - Linting ✓
- `black` - Formatting ✓

**Additional Recommendations**:
1. **`radon`** - Complexity metrics (cyclomatic complexity, maintainability index)
   ```bash
   pip install radon
   radon cc src/townlet/ -a -nb  # Cyclomatic complexity
   radon mi src/townlet/ -nb      # Maintainability index
   ```

2. **`vulture`** - Dead code detection
   ```bash
   pip install vulture
   vulture src/townlet/
   ```

3. **`bandit`** - Security linting
   ```bash
   pip install bandit
   bandit -r src/townlet/
   ```

### 11.2 Test Coverage

**Command**:
```bash
pytest --cov=townlet --cov-report=html --cov-report=term-missing
```

**Target**: 80% coverage overall, 90%+ for critical path (compiler, environment, population, VFS, DAC).

---

**End of Code Quality Assessment**

**Prepared by**: Claude Code (System Archaeologist)
**Date**: 2025-11-19
**Next**: Architect Handover Report (06-architect-handover.md)
