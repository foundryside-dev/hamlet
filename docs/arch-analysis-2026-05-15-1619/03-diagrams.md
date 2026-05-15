# Architecture Diagrams

Mermaid diagrams at three C4 levels: **System Context**, **Container** (subsystems), and **Component** (universe pipeline detail). All diagrams reflect the post-reorganization state of `src/townlet/` as observed in this analysis.

---

## 1. System Context (C4 Level 1)

The boundary between Townlet and its operator-facing surfaces.

```mermaid
graph TB
    Operator[/"Operator / Researcher<br/>(student running curriculum)"/]
    Configs[("YAML Config Packs<br/>configs/{level}/")]
    Checkpoints[("Checkpoints<br/>+ TensorBoard<br/>+ SQLite DB")]
    Frontend[/"Vue Frontend<br/>(Grid.vue / AspatialView.vue)"/]
    Townlet["Townlet<br/><br/>Pedagogical Deep-RL Environment<br/>(GPU-vectorized DQN + DAC + VFS)"]

    Operator -->|"run_demo.py / unified_server"| Townlet
    Configs -->|"v2.1 hierarchical YAML"| Townlet
    Townlet -->|"writes checkpoints + metrics"| Checkpoints
    Townlet -->|"WebSocket telemetry (port 8766)<br/>JSON snapshots"| Frontend
    Frontend -->|"observer"| Operator
```

---

## 2. Container Diagram (C4 Level 2 — Subsystems)

The 6 logical subsystems and the data they exchange. Arrows show direction of dependency / data flow at runtime.

```mermaid
graph LR
    subgraph Config["Config Layer"]
        CFG["⚙️ Configuration / DTO Layer<br/><br/>22 Pydantic v2 modules<br/>(src/townlet/config/)"]
    end

    subgraph Compile["Compile Time"]
        UCP["📦 Declarative Compilation Pipeline<br/><br/>universe/ + vfs/ + effects/<br/>7-stage UAC compiler"]
    end

    subgraph Runtime["Runtime"]
        ENV["🌐 Environment Runtime &amp; DAC<br/><br/>VectorizedHamletEnv<br/>DACEngine<br/>(src/townlet/environment/)"]
        PHYS["🗺️ Physical Layer<br/><br/>substrate/ + world/ + items/<br/>Grid2D/3D/ND, Continuous, Aspatial"]
        RL["🧠 RL Core<br/><br/>agent/ + population/<br/>training/ + exploration/<br/>DQN, RND, replay buffers"]
    end

    subgraph Orch["Orchestration / Periphery"]
        ORCH["🎬 Orchestration<br/><br/>curriculum/ + recording/ + demo/<br/>UnifiedServer, LiveInferenceServer"]
    end

    External1[("YAML configs<br/>configs/*/")]
    External2[("Cache<br/>.universe-cache/<br/>(msgpack)")]
    External3[("Checkpoints +<br/>TensorBoard +<br/>SQLite DB +<br/>episode recordings")]
    External4[("Vue Frontend<br/>via WebSocket")]

    External1 --> CFG
    CFG -->|"strictly-typed DTOs"| UCP
    UCP -->|"writes / reads"| External2
    UCP -->|"CompiledUniverse<br/>(immutable)"| ENV
    UCP -->|"CompiledUniverse"| ORCH
    PHYS -->|"SpatialSubstrate,<br/>Expression Evaluator,<br/>Inventory"| ENV
    PHYS -->|"world.expression"| UCP
    RL -->|"actions"| ENV
    ENV -->|"observations, rewards"| RL
    ORCH -->|"curriculum decisions"| RL
    ORCH -->|"records via async queue"| External3
    ORCH -->|"telemetry"| External4

    classDef compile fill:#e1f5ff,stroke:#0288d1,color:#000
    classDef runtime fill:#fff3e0,stroke:#f57c00,color:#000
    classDef orch fill:#f3e5f5,stroke:#8e24aa,color:#000
    classDef config fill:#e8f5e9,stroke:#388e3c,color:#000
    class UCP compile
    class ENV,PHYS,RL runtime
    class ORCH orch
    class CFG config
```

---

## 3. Component Diagram — UAC Compilation Pipeline (C4 Level 3)

The seven-stage compiler internal flow with handoff DTOs.

```mermaid
graph TD
    YAML[/"YAML configs<br/>experiment + level packs"/] --> Preflight
    Preflight["Stage 0: Preflight<br/>(loaders/preflight.py)<br/>YAML syntax + scoping"]
    Preflight --> Load
    Load["Stage 1: Load v2.1<br/>(loaders/v21.py +<br/>RawConfigsV21)"]
    Load -->|"LoadedConfigBundle"| Limits
    Limits["Stage 2: Limits<br/>(validation/limits.py)<br/>cache/profile/array bounds"]
    Limits --> Semantics
    Semantics["Stage 3: Semantics<br/>(validation/semantics.py +<br/>feasibility.py)<br/>cascade cycles, primary level"]
    Semantics --> Symbols
    Symbols["Stage 4: Symbol Table<br/>(symbol_table.py)<br/>register named entities"]
    Symbols --> Refs
    Refs["Stage 5: References<br/>(validation/references.py)<br/>resolve DAC + effect refs"]
    Refs -->|"ResolvedConfigBundle"| Shared
    Shared["Stage 6: Shared Artifacts"]

    subgraph "Domain Compilers"
        VFSC["compilers/vfs.py<br/>→ CompiledVFSProfiles"]
        EFFC["compilers/effects.py<br/>→ EffectCatalog +<br/>expression schema"]
        ACTC["compilers/actions.py"]
        OBSC["compilers/observation.py"]
        OPTC["compilers/optimization.py"]
        METC["compilers/metadata.py"]
        VFSAD["adapters/vfs_adapter.py<br/>ObservationField → ObservationSpec"]
    end

    Shared --> VFSC
    Shared --> EFFC
    VFSC --> Levels
    EFFC --> Levels
    Levels["Stage 7: Per-Level<br/>(compilers/*.py)"]
    Levels --> ACTC
    Levels --> OBSC
    Levels --> OPTC
    Levels --> METC
    Levels --> VFSAD
    ACTC -->|"CompiledLevelBundle"| Emit
    OBSC --> Emit
    OPTC --> Emit
    METC --> Emit
    VFSAD --> Emit
    Emit["Stage 8: Emit + Cache<br/>(compiled.py)<br/>msgpack serialise +<br/>config_hash + provenance_id"]
    Emit -->|"CompiledUniverse"| Cache[("Cache file")]
    Emit -->|"CompiledUniverse"| Runtime[/"Runtime consumers<br/>(vectorized_env,<br/>affordance_engine,<br/>training)"/]

    classDef stage fill:#e3f2fd,stroke:#1976d2,color:#000
    classDef compiler fill:#fff8e1,stroke:#fbc02d,color:#000
    class Preflight,Load,Limits,Semantics,Symbols,Refs,Shared,Levels,Emit stage
    class VFSC,EFFC,ACTC,OBSC,OPTC,METC,VFSAD compiler
```

---

## 4. Component Diagram — Runtime Tick (C4 Level 3)

One step of `VectorizedHamletEnv` showing the order of operations and which subsystems participate.

```mermaid
sequenceDiagram
    participant Pop as VectorizedPopulation<br/>(RL Core)
    participant Env as VectorizedHamletEnv<br/>(Environment Runtime)
    participant Sub as Substrate<br/>(Physical Layer)
    participant MD as MeterDynamics
    participant EM as EffectManager<br/>(Effects)
    participant VFS as VFSEvaluator
    participant IM as ItemManager
    participant DAC as DACEngine

    Pop->>Env: step(actions)
    Env->>Sub: validate + apply position delta
    Env->>EM: interaction → spawn affordance Effects
    Env->>MD: deplete_meters (base × curriculum)
    Env->>MD: cascade(secondary → primary)<br/>cascade(tertiary → secondary)<br/>cascade(tertiary → primary)
    Env->>EM: effect_manager.tick()
    EM->>VFS: write effect-modified bars
    Env->>VFS: evaluate global profile
    Env->>MD: check_terminal_conditions
    Env->>IM: item_manager.tick() + respawns
    Env->>DAC: calculate_rewards(state)
    DAC-->>Env: RewardTensor (extrinsic + intrinsic + shaping)
    Env->>Env: time_of_day = (t+1) % day_length
    Env-->>Pop: observations, rewards, done
```

---

## 5. Component Diagram — Demo/Orchestration Topology

How `UnifiedServer` glues training, inference and the frontend together.

```mermaid
graph LR
    OP[/"Operator"/]
    OP -->|"./run_demo.py"| US

    subgraph "UnifiedServer process"
        US["UnifiedServer<br/>(demo/unified_server.py)<br/>SIGINT/SIGTERM coordinator"]
        TrainThread[/"Training thread<br/>DemoRunner.run()"/]
        InfThread[/"Inference thread<br/>LiveInferenceServer<br/>(FastAPI + WebSocket :8766)"/]
        FrontProc[/"Frontend subprocess<br/>npm run dev"/]

        US --> TrainThread
        US --> InfThread
        US --> FrontProc
    end

    TrainThread -->|"checkpoint files<br/>every 100 episodes"| FS[("Filesystem<br/>checkpoints/")]
    InfThread -->|"polls + hot-load"| FS
    TrainThread -->|"async queue"| RecWriter[/"RecordingWriter<br/>daemon thread"/]
    RecWriter --> DB[("SQLite WAL<br/>+ msgpack/lz4 files")]
    InfThread --> DB
    InfThread -->|"WebSocket frames"| Vue[/"Vue frontend<br/>:5173"/]
    FrontProc --> Vue
    Vue --> OP

    classDef server fill:#e8eaf6,stroke:#3949ab,color:#000
    classDef io fill:#fce4ec,stroke:#c2185b,color:#000
    class US,TrainThread,InfThread,FrontProc server
    class FS,DB,Vue io
```

---

## 6. Dependency Graph — Subsystem Coupling

Cycle-detection / layering view. Arrows = "depends on at import time" between top-level subsystems.

```mermaid
graph TD
    CFG["config/"]
    UNI["universe/<br/>(+ compilers, dto, loaders,<br/>validation, adapters)"]
    VFS["vfs/"]
    EFF["effects/"]
    SUB["substrate/"]
    WLD["world/"]
    ITM["items/"]
    ENV["environment/"]
    AGT["agent/"]
    POP["population/"]
    TRN["training/"]
    EXP["exploration/"]
    CUR["curriculum/"]
    REC["recording/"]
    DEM["demo/"]

    UNI --> CFG
    UNI --> WLD
    UNI --> VFS
    UNI --> EFF
    VFS --> WLD
    EFF --> WLD

    ENV --> UNI
    ENV --> CFG
    ENV --> SUB
    ENV --> WLD
    ENV --> VFS
    ENV --> EFF
    ENV --> ITM
    ITM --> EFF
    ITM --> WLD

    AGT --> CFG
    POP --> AGT
    POP --> ENV
    POP --> TRN
    POP --> EXP
    POP --> CUR
    TRN --> CFG
    EXP --> CFG

    REC --> POP
    DEM --> POP
    DEM --> ENV
    DEM --> UNI
    DEM --> REC
    DEM --> CUR

    classDef compile fill:#e1f5ff,stroke:#0288d1,color:#000
    classDef runtime fill:#fff3e0,stroke:#f57c00,color:#000
    classDef rl fill:#f3e5f5,stroke:#8e24aa,color:#000
    classDef orch fill:#fce4ec,stroke:#c2185b,color:#000
    classDef phys fill:#e0f2f1,stroke:#00796b,color:#000
    classDef base fill:#e8f5e9,stroke:#388e3c,color:#000

    class CFG base
    class UNI,VFS,EFF compile
    class SUB,WLD,ITM phys
    class ENV runtime
    class AGT,POP,TRN,EXP rl
    class CUR,REC,DEM orch
```

**Observations on the dependency graph:**

- **No cycles** detected at the top-level. The compilation pipeline (`universe/`, `vfs/`, `effects/`) sits on top of `config/` and `world/`, and is consumed by `environment/`, but does not depend on it.
- **`environment/` is the runtime hub** — six inbound subsystem edges from the RL core / orchestration layer, eight outbound to compile-time and physical-layer subsystems.
- **`world/` is shared by both compile and runtime sides** — the expression evaluator is used by `universe/` at compile time (type-check) and by `effects/` runtime executor for evaluation. This is a deliberate seam, not a leak.
- **`demo/` is the broadest consumer** — depends on `population/`, `environment/`, `universe/`, `recording/`, `curriculum/`. Appropriate for an orchestrator.

---

## Notes

- All diagrams use the post-reorganization state of `src/townlet/` (619-line `compiler.py`, modular `compilers/`, `dto/`, `loaders/`, `validation/`, `adapters/`).
- Mermaid syntax is GitHub-flavoured; renders directly in GitHub-style markdown viewers.
- For a deeper component view of `vectorized_env.py` (2,200 lines, the next decomposition target), see Subsystem 3 in [02-subsystem-catalog.md](02-subsystem-catalog.md), which sketches the proposed split into `action_executor.py`, `observation_encoder.py`, `env_factory.py`, and `reward_calculator.py`.
