# Task: Generate C4 Architecture Diagrams

## Context
- **Workspace**: `docs/arch-analysis-2025-11-19-1158/`
- **Read**: `01-discovery-findings.md`, `02-subsystem-catalog.md`
- **Write to**: `03-diagrams.md`
- **Diagram format**: PlantUML (C4-PlantUML notation)

## Objective

Generate C4 architecture diagrams using PlantUML notation to visualize the HAMLET Townlet architecture at multiple levels. Use data from discovery findings and subsystem catalog to create accurate, comprehensive diagrams.

## Diagrams to Generate

### 1. Context Diagram (Level 1)
- **Purpose**: Show HAMLET system in its environment
- **Elements**:
  - **HAMLET Townlet System** (central box)
  - **External Systems**: User (researcher/student), Configuration Files (YAML), Checkpoint Storage, Frontend (Vue.js), TensorBoard, MLflow
- **Relationships**: Show data flows (configs → system, system → checkpoints, system → frontend)

### 2. Container Diagram (Level 2)
- **Purpose**: Show major subsystems within HAMLET
- **Elements**: All 12 subsystems from catalog
  - Universe Compiler
  - Configuration System
  - Vectorized Environment
  - Substrate System
  - Agent Networks
  - Population Manager
  - Exploration Strategies
  - Curriculum System
  - Training Infrastructure
  - VFS
  - Demo & Orchestration
  - Recording System
- **Relationships**: Show dependencies from catalog (use subsystem dependency graph)
- **Technology labels**: Python, PyTorch, Pydantic, etc.

### 3. Component Diagrams (Level 3)

Generate component diagrams for the **3 most critical subsystems**:

**A) Universe Compiler**
- Components: compiler.py, symbol_table.py, compiled.py, optimization.py, dto/, adapters/vfs_adapter.py, errors.py
- Show 7-stage pipeline flow: parse → symbol table → resolve → cross-validate → metadata → optimization → emit

**B) Vectorized Environment**
- Components: vectorized_env.py, dac_engine.py, affordance_engine.py, meter_dynamics.py, action_builder.py, temporal_utils.py, pomdp_builder.py
- Show facade orchestration pattern

**C) Population Manager**
- Components: vectorized.py, base.py, runtime_registry.py, factory.py
- Show interactions with Environment, Agent Networks, Training Infrastructure

## Expected Output

Write `03-diagrams.md` with the following structure:

```markdown
# Architecture Diagrams: HAMLET Townlet

**Analysis Date**: 2025-11-19
**Notation**: C4-PlantUML
**Analyst**: Claude Code

---

## Diagram Legend

**C4 Model Levels**:
- **Level 1 (Context)**: System in environment, external dependencies
- **Level 2 (Container)**: Major subsystems within system
- **Level 3 (Component)**: Internal structure of critical subsystems

**PlantUML Notation**:
- `Person()`: External user/actor
- `System()`: External system
- `Container()`: Major subsystem/component
- `Component()`: Internal module/file
- `Rel()`: Relationship/dependency

---

## 1. Context Diagram (Level 1)

### Purpose
Shows HAMLET Townlet system in its operational environment, including external systems and users.

### Diagram

\```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml

LAYOUT_WITH_LEGEND()

title Context Diagram: HAMLET Townlet System

Person(researcher, "Researcher/Student", "Configures experiments, trains agents, analyzes results")

System(hamlet, "HAMLET Townlet", "Pedagogical Deep RL environment for multi-resource survival learning")

System_Ext(configs, "YAML Configurations", "Hierarchical v2.1 config packs defining universes, curriculum levels")
System_Ext(checkpoints, "Checkpoint Storage", "Persisted network weights, training state, replay buffers")
System_Ext(frontend, "Vue.js Frontend", "Real-time visualization of agent behavior, meters, grid")
System_Ext(tensorboard, "TensorBoard", "Metrics dashboard (rewards, survival, loss)")
System_Ext(mlflow, "MLflow", "Experiment tracking (optional)")

Rel(researcher, hamlet, "Runs experiments")
Rel(researcher, configs, "Authors/modifies")
Rel(configs, hamlet, "Loaded by Universe Compiler")
Rel(hamlet, checkpoints, "Saves/loads")
Rel(hamlet, frontend, "Broadcasts state via WebSocket")
Rel(hamlet, tensorboard, "Logs metrics")
Rel(hamlet, mlflow, "Tracks experiments (optional)")
Rel(researcher, frontend, "Views visualization")
Rel(researcher, tensorboard, "Views metrics")

@enduml
\```

---

## 2. Container Diagram (Level 2)

### Purpose
Shows the 12 major subsystems within HAMLET Townlet and their dependencies.

### Diagram

[Include full PlantUML diagram here]

---

## 3. Component Diagrams (Level 3)

### 3.1 Universe Compiler

[Include diagram showing 7-stage pipeline]

### 3.2 Vectorized Environment

[Include diagram showing facade pattern]

### 3.3 Population Manager

[Include diagram showing training loop orchestration]

---

## Diagram Notes

[Any clarifications, simplifications, or assumptions made in diagrams]
```

## Validation Criteria

- [ ] All diagrams use valid C4-PlantUML syntax
- [ ] Context diagram includes all external systems
- [ ] Container diagram includes all 12 subsystems
- [ ] Dependencies match subsystem catalog (bidirectional consistency)
- [ ] Component diagrams for 3 critical subsystems
- [ ] Technology labels included (Python, PyTorch, etc.)
- [ ] Clear diagram purposes documented
- [ ] Diagram notes section present

## Notes

- **Use C4-PlantUML**: Standard C4 notation for architectural diagrams
- **Leverage catalog**: Dependencies, components, patterns all documented in 02-subsystem-catalog.md
- **Simplify when needed**: Diagrams should be readable, not exhaustive (e.g., don't show every file)
- **Consistent naming**: Use exact subsystem names from catalog
- **Bidirectional arrows**: If A→B in catalog, show in diagram
