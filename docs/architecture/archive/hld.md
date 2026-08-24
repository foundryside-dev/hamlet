# Townlet Framework High-Level Design

**Status**: Compiled Draft  
**Compiled**: 2026-05-15  
**Source Directory**: `docs/architecture/hld/`  
**Scope**: Canonical high-level design body compiled from the split HLD section files, plus the frontend visualization HLD.

This file is a compiled reading copy. The numbered source sections remain in `docs/architecture/hld/` for focused edits and review. Review notes under `docs/architecture/hld/review/` remain separate review artifacts and are not folded into this canonical HLD body.

The compiled frontend section omits stale legacy-checkpoint fallback guidance from the source note because this project is pre-release and intentionally carries no backwards-compatibility arrangements.

## Contents

- [1. Architectural Overview](#1-architectural-overview)
- [2. Brain as Code](#2-brain-as-code-bac-the-mind)
- [3. Run Bundles and Provenance](#3-run-bundles-and-provenance)
- [4. Checkpoint Compatibility and Resume Safety](#4-checkpoint-compatibility-and-resume-safety)
- [5. Resume Semantics](#5-resume-semantics)
- [6. Runtime Engine Components](#6-runtime-engine-components)
- [7. Telemetry and UI Surfacing](#7-telemetry-and-ui-surfacing)
- [8. Declarative Goals and Termination Conditions](#8-declarative-goals-and-termination-conditions)
- [9. Affordance Semantics](#9-affordance-semantics)
- [10. Success Criteria](#10-success-criteria)
- [11. Implementation Notes and Ordering](#11-implementation-notes-and-ordering)
- [12. Implementation Order](#12-implementation-order-milestones)
- [Frontend Visualization Architecture](#frontend-visualization-architecture-hld)

---

<!-- Source: docs/architecture/hld/01-executive-summary.md -->

## 1. Architectural Overview

The Townlet Framework defines agents and worlds as audited configuration, not as "whatever the Python happened to be at the time."

The old Townlet/Hamlet agent was one opaque recurrent Q-network (`RecurrentSpatialQNetwork`) that turned partial observations into actions. It sort of worked, sometimes brilliantly, but it was a black box. If it sprinted to hospital and then fell asleep in the shower, the only honest answer to "why?" was "the weights felt like it."

The Townlet Framework v1.0 replaces that with a Software Defined Agent (SDA) running in a Software Defined World. We treat both the world and the mind as first-class content. We call this:

- **Universe as Code (UAC)**: The world, declared in data
- **Brain as Code (BAC)**: The mind, declared in data

If you need the full schematics, see §2 for BAC and §8 for UAC; those sections walk through the YAML layers and runtime interpretation.

Together, these provide four hard properties we did not have before:

### 1. The mind is explicit

BAC describes the agent's cognition in three YAML files: what faculties it has, how they're implemented, and how they think step by step. Panic response, ethics veto, planning depth, goal-selection bias – it's all on paper.

### 2. The world is explicit

UAC defines the universe (bars, affordances, costs, effects, public cues, operating hours, wage schedules) as data. Affordances like beds, jobs, hospitals are declared as configuration with per-tick bar effects, eliminating hidden "secret physics" deep in the environment loop.

**Framework note**: Affordances and bars are UAC patterns (framework-level). Specific affordances like "Bed" and bars like "Energy" are Townlet Town vocabulary (instance-level). Other universe instances could define "Assembly Line" affordances or "Fatigue" bars.

### 3. Every run is provenance-bound

When you run the framework, the platform snapshots both the world and brain configurations, hashes them (cognitive hash - unique fingerprint of the brain+world configuration), and stamps that identity onto every tick of telemetry. If the agent behaves unexpectedly, we can identify exactly which mind, under which world rules, produced the behavior. There is no "the AI just did that."

### 4. We can teach and audit, not just watch

We log not only what the body did ("health: 0.22"), but what the mind attempted, what the panic controller overrode, and what the ethics layer vetoed. We can answer "why" with evidence rather than conjecture.

**Impact**: The Townlet Framework shifts from "a neat RL simulation with emergent drama" to "an accountable cognitive system that can be diffed, replayed, and defended."

We achieve this by doing three things.

---

## 1.1 The Brain Is Now Assembled, Not Baked In

Earlier releases relied on a monolithic recurrent Q-network that attempted to handle perception, planning, social reasoning, panic, ethics, and action selection in a single block. The Townlet Framework decomposes the mind into explicit cognitive modules:

**Perception / Belief State Builder**
Transforms partial, noisy observations into an internal belief state.

**World Model**
Predicts state transitions for candidate actions, allowing the agent to learn the universe's dynamics, including non-stationary changes such as price shifts.

**Social Model**
Estimates the likely behavior and goals of nearby agents using the public cues that UAC exposes. It receives no hidden state at runtime.

**Hierarchical Policy**
Selects a strategic goal (framework pattern) and chooses the concrete action that advances that goal each tick.

**Townlet Town goals** (instance-specific): SURVIVAL (meet critical needs), THRIVING (optimize quality of life), SOCIAL (prioritize relationships). Other universe instances could define different goals (e.g., BUY/SELL/HOLD for trading agents).

**Panic Controller**
Overrides normal planning when survival thresholds fall below configured limits (framework pattern). Townlet Town configures thresholds for energy, health, satiation bars.

**EthicsFilter**
Applies the final compliance gate. It forbids actions that violate policy (framework pattern). Panic cannot bypass ethics - EthicsFilter is final.

**Framework design**: Modules and their interactions are declared in BAC configuration and materialized at runtime. We can explicitly disable the Social Model for ablation without touching shared policy code, adjust the planning horizon from two to six ticks via configuration, or introduce a new panic rule without retraining perception.

The Townlet Framework is therefore an engineered assembly rather than a single opaque network.

---

## 1.2 The World Is Now Declared, Not Hidden in Engine Logic

The environment is no longer an ad hoc Python ruleset. Core mechanics are defined in UAC configuration.

**Framework patterns**: Affordances (interactable objects with capacity, per-tick effects, costs, interrupt rules), bars (continuous state variables 0.0-1.0), cascades (bar relationships), public cues (visible signals for social reasoning).

**Townlet Town instance**: Defines 14 specific affordances (Bed, Hospital, Job, Fridge, Gym, Shower, Bar, Restaurant, Park, Phone, Mall, SocialEvent, Couch, Fridge), 8 bars (Energy, Health, Satiation, Money, Mood, Social, Fitness, Hygiene), ambulance pricing, operating hours, wage schedules.

UAC expresses the desired behavior; the runtime engine executes those behaviors deterministically.

**Example**: Questions such as "why did the agent pay $300 to call an ambulance instead of walking to hospital?" can be answered by inspecting the world configuration (immediate teleportation at high cost versus slower treatment with possible closing hours) alongside the brain configuration (panic thresholds permitting a survival override at 5% health).

The universe's physics and economy are reviewable. Affordances can reference whitelisted special effects (e.g., `teleport_to:hospital`), keeping the world spec expressive but bounded.

---

## 1.3 Every Run Now Has Identity and Chain of Custody

Launching a run produces a durable artifact.

**We snapshot**:
- **World configuration** (UAC)
- **Brain configuration** (BAC, all three layers)
- **Runtime envelope** (tick rate, curriculum schedule, seed)
- **Cognitive hash** (unique fingerprint computed over the snapshot and compiled cognition graph)

Every tick of behavior is logged with that hash.

**This provides**:

**Reproducibility**
"Rerun the same mind in the same world and observe the same behavioral envelope"

**Accountability**
"At tick 842, EthicsFilter blocked STEAL for mind hash 9af3c2e1 under world snapshot `austerity_nightshift_v3`"

**Teaching material**
"Module X proposed the action, panic overrode it, ethics vetoed it while the agent had limited resources"

**Framework benefit**: Provenance works for any universe instance, not just Townlet Town.

---

## 1.4 Live Telemetry Shows Cognition, Not Just Vitals

The UI for a live run is not limited to meter readouts (energy 0.22, mood 0.41). It also shows:

- **Current goal**: Which high-level goal the agent is pursuing (framework pattern; Townlet Town uses SURVIVAL/THRIVING/SOCIAL)
- **Panic override**: Whether the panic controller overrode the normal goal during the tick (e.g., "health critical")
- **Ethics veto**: Whether EthicsFilter vetoed the chosen action and why (e.g., "attempted STEAL; forbidden")
- **Planning depth**: How many ticks ahead the world model simulates (e.g., "world_model.rollout_depth: 6")
- **Social model status**: Whether Social Model is active
- **Cognitive hash**: Short form of the hash (so you know exactly which mind you're observing)

**Example narrative**: Instructors can point to the panel and state: "Energy fell below the 15% panic threshold, the agent attempted to steal food, EthicsFilter blocked the action, and the planner operated with a six-step horizon while the agent pursued SURVIVAL. Ethical constraints remain visible even under pressure."

This delivers the glass-box promise: The Townlet Framework shifts from passive observation to transparent cognition, survival heuristics, and ethics operating in public.

---

## 1.5 Why This Matters (Governance, Research, Teaching)

**Interpretability**
We can answer "which part of the mind did that and why" with evidence. Telemetry records whether panic overrode the policy or EthicsFilter vetoed a candidate action.

**Reproducibility**
Behavior is not anecdotal; it is a run folder with a configuration snapshot and hash that any reviewer can rehydrate.

**Accountability**
If something unsafe occurs, we examine which safety setting permitted it, which execution-graph step executed it, the relevant panic thresholds, and the governing world rules. The issue becomes diagnosable and auditable.

**Pedagogy / Curriculum**
Students, auditors, and policy teams can:
- Read the YAML configs to understand what the agent was authorized to do
- Diff successive versions of the mind or world to see exactly what changed
- Run controlled comparisons (same brain, different world; same world, different brain)
- Understand the framework as reusable architecture beyond Townlet Town

**Framework flexibility**: The architecture supports any universe. Townlet Town demonstrates it for survival learning. Future instances could model factory optimization, market trading, or multi-agent societies using the same BAC/UAC foundation.

---

**Summary**: The Townlet Framework treats the brain and the world as configuration, snapshots and hashes them at runtime, and exposes live introspection with governance veto logging. That is now the standard operating model.

---

---

<!-- Source: docs/architecture/hld/02-brain-as-code.md -->

## 2. Brain as Code (BAC): The Mind

BAC defines agent cognition as something we can inspect, diff, and enforce.

The BAC stack is three YAML layers. Together, they specify a Software Defined Agent (SDA).

Change the YAMLs, you change the mind. Snapshot the YAMLs, you freeze the mind. Hash the snapshot, you can prove which mind took which action.

**Framework note**: BAC is the architecture pattern. The examples below show **Townlet Town** configurations (survival goals, energy bars, attack/steal actions) but other universe instances would define different vocabulary using the same three-layer structure.

---

## 2.1 Layer 1: cognitive_topology.yaml

**Audience**: Governance, instructors, simulation designers
**Nickname**: The character sheet

Layer 1 defines the behavior contract and safety envelope for a specific agent instance in a specific run.

**It answers**:

- Is social reasoning enabled?
- How far ahead is the agent allowed to plan?
- When does it panic and override normal plans?
- What is the agent allowed to do, and what is absolutely forbidden?
- How greedy, anxious, curious, agreeable is it, as dials not as fairy dust?
- Is it allowed to narrate its motives in the UI?

**Example configuration**:

```yaml
perception:
  enabled: true
  uncertainty_awareness: true    # Agent can admit "I'm not sure"

world_model:
  enabled: true
  rollout_depth: 6               # Allowed planning horizon (ticks ahead)
  num_candidates: 4              # Futures evaluated per tick

social_model:
  enabled: true                  # false = does not model other minds
  use_family_channel: true       # allow private in-group signaling (Townlet Town: multi-agent)

hierarchical_policy:
  meta_controller_period: 50     # How often to reconsider high-level goal
  allowed_goals:                 # (Townlet Town instance vocabulary)
    - SURVIVAL
    - THRIVING
    - SOCIAL

personality:                     # Framework pattern (instance-specific sliders)
  greed: 0.7                     # money drive
  agreeableness: 0.3             # harmony vs confrontation
  curiosity: 0.8                 # exploration drive
  neuroticism: 0.6               # risk aversion / anxiety

panic_thresholds:                # Framework pattern (instance-specific bars)
  energy: 0.15                   # if energy < 15 percent => emergency mode
  health: 0.25                   # (Townlet Town bars: energy, health, satiation)
  satiation: 0.10

compliance:                      # Framework pattern (instance-specific actions)
  forbid_actions:                # Never allowed, even during panic
    - "attack"                   # (Townlet Town action vocabulary)
    - "steal"
  penalize_actions:              # Discouraged but not forbidden
    - { action: "shove", penalty: -5.0 }

introspection:                   # Framework capability
  publish_goal_reason: true      # Should the agent explain itself in UI?
  visible_in_ui: "research"      # beginner | intermediate | research
```

**How Layer 1 connects to runtime**:

- **panic_thresholds** → Tells `panic_controller` when to override normal planning for survival
- **forbid_actions** → Tells `EthicsFilter` what is never allowed, even if the agent is dying
- **personality** → Feeds into hierarchical policy's goal choice (greed: 0.7 means money-seeking wins internal debates)
- **publish_goal_reason** → Controls whether UI surfaces "I'm going to work because we need money"

**Governance significance**: Layer 1 is what policy teams sign off on. It's the file you show when someone asks "what kind of mind did you put in this world?"

**Cognitive hash dependency**: If you change Layer 1 between runs (e.g., allow STEAL, or lower panic threshold, or turn social modeling off), that's not the same agent anymore. The framework must produce a new cognitive hash.

**Framework vs Instance**: Patterns like `panic_thresholds`, `compliance`, `personality` are framework-level. The specific bars (energy/health), actions (attack/steal), goals (SURVIVAL/THRIVING/SOCIAL), and personality traits (greed/curiosity) are Townlet Town vocabulary. A factory instance might define `machinery_stress` bars, `shutdown` actions, and `efficiency/safety` goals.

---

## 2.2 Layer 2: agent_architecture.yaml

**Audience**: Engineers, grad students, researchers
**Nickname**: The blueprint

Layer 2 defines the internal build sheet for cognitive faculties. If Layer 1 says "there is a World Model and it's allowed to plan 6 ticks ahead", Layer 2 says "the World Model is a 2-layer MLP with 256 units, these heads, trained on this dataset, with Adam at this learning rate".

**This file specifies**:

- Network types (CNN, GRU, MLP, etc.)
- Hidden sizes, head dimensions
- Interface contracts between modules (enforced dimensional compatibility)
- Optimizer types and learning rates
- Pretraining objectives and datasets

**Purpose**: Enforces discipline so you can swap modules and reproduce experiments without mystery glue.

**Example configuration**:

```yaml
interfaces:                          # Framework pattern: explicit interface contracts
  belief_distribution_dim: 128      # Perception output
  imagined_future_dim: 256          # World Model summary
  social_prediction_dim: 128        # Social Model summary
  goal_vector_dim: 16               # Meta-controller goal embedding
  action_space_dim: 6               # (Townlet Town: up,down,left,right,interact,wait)

modules:
  perception_encoder:
    spatial_frontend:
      type: "CNN"
      channels: [16, 32, 32]
      kernel_sizes: [3, 3, 3]
    vector_frontend:
      type: "MLP"
      layers: [64]
      input_features: "auto"
    core:
      type: "GRU"
      hidden_dim: 512
      num_layers: 2
    heads:
      belief_dim: 128               # must match interfaces.belief_distribution_dim
    optimizer: { type: "Adam", lr: 0.0001 }
    pretraining:                    # Framework capability
      objective: "reconstruction+next_step"
      dataset: "observation_rollout_buffer"

  world_model:
    core_network:
      type: "MLP"
      layers: [256, 256]
      activation: "ReLU"
    heads:
      next_state_belief: { dim: 128 }
      next_reward:       { dim: 1 }
      next_done:         { dim: 1 }
      next_value:        { dim: 1 }
    optimizer: { type: "Adam", lr: 0.00005 }
    pretraining:
      objective: "dynamics+value"
      dataset: "uac_ground_truth_logs"  # UAC generates ground truth dynamics

  social_model:
    core_network:
      type: "GRU"
      hidden_dim: 128
    inputs:
      use_public_cues: true         # Framework pattern: UAC public cues
      use_family_channel: true      # (Townlet Town: family relationships)
      history_window: 12
    heads:
      goal_distribution: { dim: 16 }  # maps to goal_vector_dim
      next_action_dist:  { dim: 6 }   # maps to action_space_dim
    optimizer: { type: "Adam", lr: 0.0001 }
    pretraining:
      objective: "ctde_intent_prediction"
      dataset: "uac_ground_truth_logs"

  hierarchical_policy:
    meta_controller:                # Framework pattern: strategic goal selection
      network: { type: "MLP", layers: [256, 128], activation: "ReLU" }
      heads:
        goal_output: { dim: 16 }    # goal_vector_dim
    controller:                     # Framework pattern: action selection
      network: { type: "MLP", layers: [256, 128], activation: "ReLU" }
      heads:
        action_output: { dim: 6 }   # action_space_dim
    optimizer: { type: "Adam", lr: 0.0003 }
    pretraining:
      objective: "behavioural_cloning"
      dataset: "v1_agent_trajectories"  # (Townlet Town: previous agent runs)
```

**Why Layer 2 matters**:

**Reproducibility**: The mind is rebuildable in any controlled environment, not dependent on an individual developer's workstation.

**Experimental control**: Module swaps become controlled experiments ("same cognitive_topology, different world_model internals").

**Governance transparency**: If someone quietly changed the optimizer or widened the GRU and then claimed "no behavioral change expected", governance can call nonsense on that. Layer 2 makes such changes visible.

**Interface contracts**: The `interfaces` section enforces dimensional compatibility. If perception outputs 128-dim belief but policy expects 256-dim input, the factory catches this **before runtime**. No silent broadcasting, no mystery glue.

**Framework vs Instance**: Network architectures (CNN, GRU, MLP) and interface contracts are framework-level. Specific action_space_dim (6 for Townlet Town's movement+interact), pretraining datasets (v1_agent_trajectories), and module choices (use_family_channel for Townlet Town families) are instance-specific.

---

## 2.3 Layer 3: execution_graph.yaml

**Audience**: Safety teams, auditors, engineers debugging cognition at 2am
**Nickname**: The think loop

Layer 3 defines the actual cognition pipeline the framework runs every tick. This is the part that most RL projects pretend is "obvious" and never write down. **We write it down.**

**Structure**: A DAG (Directed Acyclic Graph) of named steps with symbolic bindings (@references).

**Example configuration**:

```yaml
inputs:
  - "@graph.raw_observation"
  - "@graph.prev_recurrent_state"

steps:
  perception_packet:
    node: "@modules.perception_encoder"     # Symbolic binding (Layer 2 module)
    inputs:
      - "@graph.raw_observation"
      - "@graph.prev_recurrent_state"

  belief_distribution:
    node: "@utils.unpack"
    input: "@steps.perception_packet"
    key: "belief"

  new_recurrent_state:
    node: "@utils.unpack"
    input: "@steps.perception_packet"
    key: "state"

  policy_packet:
    node: "@modules.hierarchical_policy"
    inputs:
      - "@steps.belief_distribution"
      - "@services.world_model_service"     # Service binding (callable module)
      - "@services.social_model_service"

  candidate_action:
    node: "@utils.unpack"
    input: "@steps.policy_packet"
    key: "action"

  panic_adjustment:
    node: "@modules.panic_controller"
    inputs:
      - "@steps.candidate_action"
      - "@config.L1.panic_thresholds"      # Symbolic binding (Layer 1 config)
    outputs:
      - "panic_action"
      - "panic_reason"                     # Logged for telemetry

  final_action:
    node: "@modules.EthicsFilter"
    inputs:
      - "@steps.panic_adjustment.panic_action"
      - "@config.L1.compliance.forbid_actions"
    outputs:
      - "action"
      - "veto_reason"                      # Logged for governance audit

outputs:
  final_action: "@steps.final_action.action"
  new_recurrent_state: "@steps.new_recurrent_state"
```

**In plain language**:

1. **Perception** digests what the agent currently sees + its memory from last tick, producing:
   - Belief about the world and itself (`belief_distribution`)
   - Updated recurrent state (memory for next tick)

2. **Hierarchical Policy** decides: "Given my current strategic goal, given what I think the world is, given what I think will happen next if I try X (via `@services.world_model_service`), and given what I think other agents are about to do (via `@services.social_model_service`), here's what I want to do now."

3. **Panic Controller** looks at bars (energy, health - Townlet Town bars) versus panic thresholds from Layer 1. If in crisis, it **can override** the policy's `candidate_action` with an emergency survival action ("call_ambulance", "go_to_bed_now"). That override is logged with `panic_reason`.

4. **EthicsFilter** takes that (possibly panic-adjusted) action and enforces Layer 1 compliance. If the action is forbidden (e.g., "steal"), EthicsFilter **vetoes it**, substitutes something allowed, and logs `veto_reason`. **EthicsFilter is final**. Panic cannot authorize illegal behavior. This ordering is governance policy, not just code order.

5. **Graph outputs**:
   - `final_action`: The one that actually gets sent into the world
   - `new_recurrent_state`: What the agent will remember next tick

**Why Layer 3 matters**:

**Explicit causal chain**: We can prove "panic, then ethics, then action" with configuration, not "trust us".

**Governance as code**: It defines who is actually in charge of the body at each step. If someone tries to sneak in "panic can bypass ethics if health < 5 percent", that changes the execution graph, therefore changes the cognitive hash, therefore is detectable in provenance logs.

**Debuggability**: When an agent does something unexpected, engineers can trace through the DAG to see which step produced the decision and why.

**Framework pattern**: The DAG structure, symbolic bindings (@modules, @config, @services), and panic→ethics ordering are framework-level. The specific modules (panic_controller, EthicsFilter) and their inputs (panic_thresholds, forbid_actions) are configured per universe instance.

**Put simply**: Layer 3 is the mind's wiring diagram, in writing, with order-of-operations as governance, not folklore.

---

**Summary**: BAC specifies Software Defined Agents through three layers:
- **Layer 1**: What can the agent do (behavior contract)
- **Layer 2**: How are modules built (architecture blueprint)
- **Layer 3**: In what order does cognition run (think-loop DAG)

Together, they make agent minds inspectable, diffable, and enforceable.

---

---

<!-- Source: docs/architecture/hld/03-run-bundles-provenance.md -->

## 3. Run Bundles and Provenance

The Townlet Framework doesn't "run an agent". It mints an artifact with identity, provenance, and chain of custody. That's the difference between "cool AI demo" and "system we can take in front of governance without sweating through our shirt."

---

## 3.1 The Run Bundle

Before a run starts, you prepare a **run bundle** (configuration directory) under `configs/<run_name>/`:

```text
configs/
  L99_AusterityNightshift/              # (Townlet Town run name)
    config.yaml                         # Runtime envelope: tick rate, duration, curriculum, seed
    universe_as_code.yaml               # UAC: The world (bars, affordances, prices, cues)
    cognitive_topology.yaml             # BAC Layer 1 (behavior contract and safety knobs)
    agent_architecture.yaml             # BAC Layer 2 (module blueprints and interfaces)
    execution_graph.yaml                # BAC Layer 3 (think loop + panic/ethics chain)
```

**What each file contains**:

**universe_as_code.yaml** (UAC):
The world specification. Defines:
- Bars (energy, health, money - Townlet Town vocabulary; other instances use different bars)
- Affordances (Bed, Job, Hospital, PhoneAmbulance - Townlet Town; other instances define different affordances)
- Per-tick effects and costs
- Capacity limits, interrupt rules
- Whitelisted special effects (e.g., `teleport_to:hospital`)
- Public cues other agents can see ("looks_tired", "bleeding", "panicking" - instance-specific)

**The three BAC layers** (L1/L2/L3):
The mind specification (see §2 for details).

**config.yaml** (Runtime envelope):
Execution parameters:
- How long to run (num_ticks or max_episodes)
- Tick rate (ticks per second)
- Number of agents
- Curriculum schedule (e.g., "start alone, introduce food-scarcity rival after 10k ticks" - Townlet Town)
- Random seed for reproducibility

**Framework note**: The five-file bundle structure is framework-level. The example name "L99_AusterityNightshift" and contents (energy/health bars, Bed/Hospital affordances) are Townlet Town instance-specific. A factory simulation might use "F03_MachineryStress" with machinery_health bars and Assembly Line affordances.

**This bundle is what we claim we are about to run.**

---

## 3.2 Launching a Run

When we actually launch, **we don't execute the live bundle**. We snapshot it.

The launcher creates a **run folder**:

```text
runs/
  L99_AusterityNightshift__2025-11-03-12-14-22/   # Run ID: <name>__<timestamp>
    config_snapshot/                              # Frozen configs
      config.yaml
      universe_as_code.yaml
      cognitive_topology.yaml
      agent_architecture.yaml
      execution_graph.yaml
      full_cognitive_hash.txt                     # Computed identity
    checkpoints/                                  # Periodic saves
    telemetry/                                    # Per-tick logs
    logs/                                         # System logs
```

**Critical details**:

### Configuration Snapshot (Frozen Configs)

**`config_snapshot/`** is a byte-for-byte copy of the five YAMLs at launch time.

**Immutability guarantee**: After launch, the runtime simulator reads **only** from this snapshot, never from the mutable `configs/` directory. This prevents untracked hotpatches to ethics during a run.

**Why this matters**: Governance cannot be assured if the "forbid_actions" list can change mid-run without leaving evidence. The snapshot makes configuration immutable.

### Cognitive Hash Computation

During agent instantiation (via factory.py), the framework computes **`full_cognitive_hash.txt`** from:

1. **Exact text of the five snapshot YAMLs** (byte-for-byte content)
2. **Compiled execution graph** (post-resolution: real step order after resolving @modules.* symbolic bindings)
3. **Instantiated module architectures** (types, hidden dims, optimizer hyperparameters from Layer 2)

**That hash is this mind's identity**. It's the "brain fingerprint plus declared world."

**Hash properties**:
- **Deterministic**: Same configs → same hash
- **Sensitive**: Any change (panic threshold, ethics rule, optimizer LR) → different hash
- **Provenance**: Links telemetry to exact configuration that produced it

**Framework note**: Cognitive hash computation is framework-level. The hash includes both BAC (mind) and UAC (world), making it the "complete cognitive+environmental identity."

### Telemetry Logging

The framework starts ticking. **Every tick** we log telemetry with:

- **run_id** (e.g., `L99_AusterityNightshift__2025-11-03-12-14-22`)
- **tick_index** (0, 1, 2, ...)
- **full_cognitive_hash** (links to exact config snapshot)
- **current_goal** (engine ground truth - Townlet Town: SURVIVAL/THRIVING/SOCIAL)
- **agent_claimed_reason** (what it says it's doing, if introspection enabled)
- **panic_state** and any panic override (was panic active this tick?)
- **candidate_action** (what policy wanted to do)
- **final_action** (what actually happened after panic + ethics)
- **ethics_veto_applied** and **veto_reason** (was action blocked? why?)
- **planning_depth** (world_model.rollout_depth - how far ahead it planned)
- **social_model.enabled** (was social reasoning active?)
- **Prediction summaries** from world_model and social_model (what it expected to happen)

**That is now evidence**. If someone later asks "why didn't the agent eat even though it was starving?", we don't guess. We read the log:
- Tick 842: `candidate_action=EAT_FRIDGE`, `final_action=WAIT`, `veto_reason="insufficient money"`, `panic_state=false` (hadn't hit threshold yet)

**Framework benefit**: Telemetry structure is framework-level. The specific fields (current_goal values, affordance names in actions) are instance-specific, but the provenance pattern (run_id + tick_index + hash + decision chain) applies to any universe.

---

## 3.3 Checkpoints and Resume

During the run, the framework periodically checkpoints to:

```text
runs/
  L99_AusterityNightshift__2025-11-03-12-14-22/
    checkpoints/
      step_000500/
        weights.pt                      # Neural network weights
        optimizers.pt                   # Optimizer state
        rng_state.json                  # Random number generator state
        config_snapshot/                # Config snapshot (redundant copy)
          config.yaml
          universe_as_code.yaml
          cognitive_topology.yaml
          agent_architecture.yaml
          execution_graph.yaml
          full_cognitive_hash.txt
```

**Each checkpoint is effectively "a frozen moment of mind + world + RNG".**

### What Checkpoints Enable

**1. Honest Resume**

To resume, the framework:
1. **Loads from the checkpoint's `config_snapshot/`**, not from `configs/` (prevents stealth edits)
2. Writes out a new run folder: `L99_AusterityNightshift__2025-11-03-12-14-22_resume_2025-11-03-13-40-09/`
3. **Recomputes the cognitive hash** from the loaded snapshot

**Honest continuation**:
- If the snapshot is unchanged → hash matches → we can legitimately say "this is a continuation of the same mind"
- If we touch anything cognitive or world-rules (panic thresholds, forbid_actions, ambulance cost, bed healing rate, module architecture) → hash changes → **that is now a fork, not a continuation**

**Governance integrity**: You cannot stealth-edit survival rules and claim it's still the same agent. The hash proves otherwise.

**Framework pattern**: Resume vs fork semantics are framework-level. Any BAC or UAC change creates a fork.

**2. Forensics**

We can go back to tick 842 (or any tick) and reconstruct:
- What body state the agent believed it was in (from telemetry: bar values, belief_distribution)
- What goal it claimed (SURVIVAL/THRIVING/SOCIAL - Townlet Town)
- Whether panic took over (panic_state=true, panic_reason logged)
- Whether EthicsFilter stopped something illegal (ethics_veto_applied=true, veto_reason="forbidden: steal")
- What world rules and costs it was operating under (from config_snapshot: ambulance price, bed healing rate, etc.)

**Framework benefit**: Forensics work for any universe. The specific bars and affordances differ, but the reconstruction pattern (telemetry + snapshot → "why") is universal.

**3. Curriculum / Scientific Comparison**

We can diff two runs and say:
> "The only change was that we turned off the Social Model and raised panic aggressiveness (panic_thresholds.energy: 0.15 → 0.10). Here's how behavior shifted (survival rate 45% → 62%, social interactions dropped 90%)."

**It's not anecdote, it's a config diff plus a new hash.**

**Framework pattern**: Config diff enables controlled experiments: change one variable (Layer 1 setting, Layer 2 architecture, UAC affordance), measure behavioral shift.

---

## 3.4 Why Provenance Is Non-Negotiable

Without this provenance model, the Townlet Framework would revert to a generic agent-in-a-box demonstration, forcing governance to rely on trust rather than evidence.

**With this provenance model**:

**Governance audit**:
- We can prove at audit time which ethics rules were live (read forbid_actions from config_snapshot)
- We can prove panic never bypassed ethics unless someone explicitly allowed that in Layer 3 (and if they did, the hash changed, creating evidence of the modification)

**Incident investigation**:
- We can replay any behavior clip and show both "what happened" (telemetry) and "which mind, under which declared rules, proposed, attempted, and was vetoed" (config_snapshot + hash)

**Scientific rigor**:
- Reproducibility: Same config_snapshot → same hash → same mind (modulo RNG if not seeded)
- Experimental control: Config diff shows exactly what changed between runs

**Deployment readiness**: This capability enables deployment beyond laboratory settings. Regulators and safety teams can audit based on evidence, not promises.

**Framework foundation**: Provenance is what transforms "interesting research artifact" into "governable AI system."

---

**Summary**: The Townlet Framework provenance system works as follows:
1. **Prepare run bundle** (`configs/<run_name>/` with 5 YAMLs)
2. **Snapshot at launch** (byte-for-byte copy → `runs/<run_id>/config_snapshot/`)
3. **Compute cognitive hash** (frozen configs + compiled graph + architectures)
4. **Log telemetry** (every tick: run_id + tick_index + hash + decision chain)
5. **Checkpoint periodically** (snapshot + weights + RNG for resume)
6. **Resume honestly** (recompute hash; changes create fork, not continuation)

This is the framework's identity and accountability mechanism. BAC/UAC define the mind and world. Provenance proves which mind, under which world, did what.

---

---

<!-- Source: docs/architecture/hld/04-checkpoints.md -->

## 4. Checkpoints

A checkpoint is not "saved weights lol". It's a **frozen moment of a specific mind, in a specific world, under specific rules, at a specific instant in time**.

The Townlet Framework treats every checkpoint as evidence. A checkpoint must include everything required to:

- **Pick up training honestly** (continue learning trajectory, not restart with different momentum)
- **Replay behavior honestly** (reproduce stochastic outcomes, not approximate them)
- **Prove provenance** (which exact cognitive configuration produced which exact action)

When the framework writes a checkpoint for a run, it creates:

```text
runs/
  L99_AusterityNightshift__2025-11-03-12-14-22/   # (Townlet Town run)
    checkpoints/
      step_000500/                                # Checkpoint at tick 500
        weights.pt                                # Neural state
        optimizers.pt                             # Learning state
        rng_state.json                            # Causality state
        config_snapshot/                          # Embedded frozen configs
          config.yaml
          universe_as_code.yaml
          cognitive_topology.yaml
          agent_architecture.yaml
          execution_graph.yaml
        full_cognitive_hash.txt                   # Identity proof
```

**Let's unpack what those five components actually mean.**

---

## 4.1 weights.pt

This is the **live neural state of the brain** at that tick.

**Contains**:
- Perception module weights
- World model weights
- Social model weights
- Hierarchical policy weights
- Panic controller weights (if learned/parameterized)
- EthicsFilter weights (if learned/parameterized)
- Anything else registered in the **module registry**

**Framework pattern**: Module registry is populated from Layer 2 (`agent_architecture.yaml`). All modules declared there get saved together.

**Why all modules, not just policy?**: In v1 (old Hamlet), these components lived in one giant black-box DQN. In the Townlet Framework, they are separate submodules declared in Layer 2 and wired by Layer 3. We save them together because, for audit, **"the brain" encompasses the entire SDA module set**, not only the action head.

**Framework note**: The specific modules saved (perception, world_model, social_model, etc.) are framework-level patterns. Whether a universe instance uses all modules or disables some (e.g., `social_model.enabled: false` in Layer 1) affects what weights exist, but the save-all-registered-modules pattern is universal.

---

## 4.2 optimizers.pt

The framework logs both **parameters and optimizer state** (e.g., Adam moments) for each trainable module.

**Why?** Because **"resume training" must mean "continue the same mind's learning process"**, not "respawn something with the same weights but different momentum and call it continuous".

**Honest resume requirement**: If you've ever done RL, you know that quietly dropping optimizer state can absolutely change learning behavior. The framework refuses to pretend that's irrelevant. We store it.

**Framework pattern**: Optimizer state preservation is framework-level (required for honest resume). The specific optimizers (Adam, RMSprop, SGD) and their hyperparameters (lr=0.0001) are defined in Layer 2, but the principle "save optimizer state for continuity" is universal.

**Example**: Adam optimizer state includes first and second moment estimates for every parameter. Dropping this means the next training step has no momentum history, changing the learning trajectory.

---

## 4.3 rng_state.json

**Randomness is part of causality.**

The framework stores the **RNG states** that matter:
- Environment RNG (affordance tie-breaks, spawn locations - Townlet Town)
- Agent RNG (PyTorch generators for exploration noise, stochastic policy sampling)
- Any other source affecting rollout sampling, exploration, or decision-making

**Why?** This allows us to **re-run tick 501 and observe the same stochastic outcomes**.

**Replay value**: When someone asks, "would it always have chosen STEAL here?", we can answer: "Under this exact random sequence, here is what occurred," and reproduce the evidence without speculation.

**Framework pattern**: RNG preservation is framework-level (reproducible causality). The specific sources of randomness (environment contention, exploration strategy, policy sampling) vary by universe instance, but the principle "preserve RNG for replay" is universal.

**Example (Townlet Town)**: If two agents want the same Bed (capacity=1), environment RNG determines who wins. Preserving RNG lets us replay and see the same winner.

---

## 4.4 config_snapshot/

**This is critical.**

Inside every checkpoint, the framework embeds a **fresh copy** of the exact `config_snapshot/` that the run is using at that moment.

**That snapshot contains**:
- `config.yaml` (runtime envelope: tick rate, max ticks, curriculum step, etc.)
- `universe_as_code.yaml` (UAC: meters, affordances, costs, social cues, ambulance behavior, bed quality, etc. - Townlet Town vocabulary)
- `cognitive_topology.yaml` (BAC Layer 1: panic thresholds, ethics rules, personality - Townlet Town: greed=0.7, forbid STEAL)
- `agent_architecture.yaml` (BAC Layer 2: module shapes, learning rates, pretraining origins, interface dims)
- `execution_graph.yaml` (BAC Layer 3: think loop ordering - panic before ethics)

**This is not a pointer. It's an embedded copy at that checkpoint tick.**

**Why embed it every time?**

**Curriculum evolution**: Curriculum might change some parts of the world over time (e.g., add new competition, raise prices, close the hospital at night - Townlet Town examples). If that's allowed under policy, those changes will appear in `universe_as_code.yaml` at tick 10,000 that didn't exist at tick 500. **Checkpoint 500 needs to show what the world rules were then, not now.**

**Governance audit**: "Panic thresholds" and "forbid_actions" in `cognitive_topology.yaml` are part of that snapshot. When someone asks "did you allow it to steal at tick 842?", we don't argue philosophy. **We open the checkpoint around that time and read the file.**

**Framework pattern**: Embedded config snapshot is framework-level (prevents time-dependent ambiguity). Whether curriculum changes UAC (Townlet Town: prices rise) or BAC (some universe allows panic_threshold adjustments) doesn't matter - the embedding pattern ensures checkpoint shows the rules at that tick.

**Townlet Town example**: If curriculum raises ambulance cost from $300 to $500 at tick 5000, checkpoint at step_000500 shows `ambulance_cost: 300`, checkpoint at step_010000 shows `ambulance_cost: 500`.

---

## 4.5 full_cognitive_hash.txt

**This is the mind's ID badge.**

The hash is **deterministic** over:

1. **Exact text bytes of the 5 YAMLs** in the snapshot (config.yaml, universe_as_code.yaml, cognitive_topology.yaml, agent_architecture.yaml, execution_graph.yaml)

2. **Compiled execution graph** after resolution. Not the pretty YAML, but the actual ordered list of steps the agent is running after we bind `@modules.*` symbolic bindings to real modules. If someone sneaks in "panic after ethics" instead of "panic before ethics", the hash changes.

3. **Constructed module architectures**. Types, hidden sizes, optimizer settings, interface dims. Not just "GRU exists", but "GRU with hidden_dim=512 paired with Adam lr=1e-4".

**That means**:

**Ethics changes detected**:
- If you fiddle the EthicsFilter to quietly allow STEAL under panic → hash changes

**Architecture changes detected**:
- If you widen the GRU and try to pretend it's the same mind → hash changes

**World changes detected**:
- If you reduce ambulance cost in the world (Townlet Town) → hash changes (because `universe_as_code.yaml` changed)

**We're basically tattooing "this exact mind in this exact world with this exact cognition loop" into the checkpoint.**

**Framework pattern**: Cognitive hash computation is framework-level. The hash includes both BAC (mind) and UAC (world), making it the complete cognitive+environmental identity for any universe instance.

---

## 4.6 Why Checkpoints Are Legally Interesting (Not Just Technically Interesting)

**Because they kill plausible deniability.**

**Example claims** (Townlet Town context):

Someone claims:
- "Oh, it only stole because it was desperate"
  **or**
- "Ethics must have bugged out at 2am"
  **or**
- "We didn't change anything important, we just tuned panic a little"

**You can respond with evidence**:
- "Here's the checkpoint from tick 800. Panic thresholds are documented: `energy: 0.15, health: 0.25`. Ethics still forbids STEAL: `forbid_actions: ["attack", "steal"]`. Hash `9af3c2e1` says it's the same mind before and after 2am. Telemetry shows the agent attempted STEAL at tick 842, EthicsFilter vetoed it (`veto_reason: "forbidden"`), and final_action was WAIT. So no, it wasn't allowed to steal. It attempted to anyway and EthicsFilter stopped it."

**In other words, checkpoints turn anecdotes about behavior into evidence trails.**

**Framework benefit**: This pattern works for any universe. The specific affordances (STEAL in Townlet Town, SHUTDOWN in factory), bars (energy vs machinery_stress), and ethics rules differ, but the evidence mechanism (checkpoint + hash + telemetry → proof) is universal.

**Governance value**:
- **Honest resume**: Can't quietly change rules mid-training and claim continuity
- **Reproducible replay**: Can re-run critical moments with same stochastic outcomes
- **Audit trail**: Config snapshot at each checkpoint proves what rules were active when

---

**Summary**: A Townlet Framework checkpoint is a five-component evidence artifact:
1. **weights.pt**: Neural state of all SDA modules
2. **optimizers.pt**: Learning state (Adam moments, etc.) for honest training continuation
3. **rng_state.json**: RNG state for reproducible stochastic causality
4. **config_snapshot/**: Embedded frozen configs showing rules at that tick
5. **full_cognitive_hash.txt**: Mind+world identity proof

Together, these transform checkpoints from "saved model" into "legal evidence for what mind, under what rules, did what."

---

---

<!-- Source: docs/architecture/hld/05-resume-semantics.md -->

## 5. Resume Semantics

Resume operations must do more than reload weights; they are part of the **audit chain**.

If we can't prove continuity of mind across pauses, we can't claim continuity of behavior for governance, and we can't do serious ablation science.

**The framework defines resume like a forensic procedure.**

---

## 5.1 The Rule: The Checkpoint Snapshot Is Law

When you resume from a checkpoint, you **must** restore from the checkpoint's own `config_snapshot/`, not from whatever is currently sitting in `configs/<run_name>/` in your working tree.

**That means**:

**Restore exact cognitive_topology.yaml** from checkpoint:
- Same ethics (`forbid_actions: ["attack", "steal"]` - Townlet Town)
- Same panic thresholds (`energy: 0.15, health: 0.25` - Townlet Town bars)
- Same personality sliders (`greed: 0.7, curiosity: 0.8` - Townlet Town)

**Restore exact universe_as_code.yaml** from checkpoint:
- Same ambulance cost (e.g., `$300` - Townlet Town)
- Same bed healing effects (e.g., `+0.25 energy per tick` - Townlet Town)
- Same wage rates (e.g., Job pays `$22.5` - Townlet Town)

**Restore exact execution_graph.yaml** from checkpoint:
- Same panic-then-ethics ordering (panic_controller before EthicsFilter - framework pattern)

**Restore optimizer state and RNG** from checkpoint:
- Same Adam moments (framework-level: honest training continuation)
- Same random number generator states (framework-level: reproducible outcomes)

**You do not "reconstruct" the agent from the latest code and hope it's approximately right.** You **rehydrate** that specific mind in that specific world with that specific internal loop.

**Framework principle**: Checkpoint snapshot is law (framework-level). The specific contents (Townlet Town affordances, bars, goals) vary, but the rule "restore from checkpoint snapshot, not live configs" is universal.

---

## 5.2 Where the Resumed Run Lives

Resuming from:

```text
runs/L99_AusterityNightshift__2025-11-03-12-14-22/checkpoints/step_000500/
```

creates a **fresh new run folder**, for example:

```text
runs/
  L99_AusterityNightshift__2025-11-03-12-14-22_resume_2025-11-03-13-40-09/
    config_snapshot/          # Copied from checkpoint, byte-for-byte
    checkpoints/              # New checkpoints for resumed run
    telemetry/                # New telemetry logs
    logs/                     # New system logs
```

**Important details**:

**New run, new timeline**:
- We do **not** keep writing into the old run folder
- Each resume creates distinct timeline with its own provenance

**Hash recomputation**:
- The framework recomputes the cognitive hash from the checkpoint snapshot
- **If you have not changed anything** → hash matches → proves it's the same mind continuing
- **If snapshot was modified** → hash differs → proves it's a fork (new agent)

**Telemetry continuity**:
- Telemetry in the resumed run logs the **same hash** (if unchanged)
- Audit can verify: "This is truly the same mind, same ethics, same world, just continued later"

**Framework pattern**: New run folder per resume (framework-level). The naming convention (`_resume_<timestamp>`) and hash verification apply to any universe instance.

---

## 5.3 Forking vs Continuing

**Now the governance-critical part.**

If, before resuming, you **edit that copied snapshot, even slightly**, you are **not continuing**. You are **forking**.

**Examples of forking** (Townlet Town context):

**BAC Layer 1 changes** (behavior contract):
- Lower `panic_thresholds.energy` from `0.15` to `0.05` (agent panics earlier)
- Turn off `social_model.enabled` (disable social reasoning)
- Remove `"steal"` from `forbid_actions` (ethics now allows stealing)
- Change personality: `greed: 0.7 → 0.3` (less money-driven)

**UAC changes** (world rules):
- Change ambulance cost in `universe_as_code.yaml` (`$300 → $150`)
- Modify bed healing rate (`+0.25 energy/tick → +0.50 energy/tick`)
- Add new affordance or remove existing one

**BAC Layer 2 changes** (architecture):
- Widen GRU hidden dimension (`hidden_dim: 512 → 1024`)
- Change optimizer learning rate (`lr: 0.0001 → 0.0005`)

**BAC Layer 3 changes** (execution ordering):
- Reorder execution graph (panic_controller runs **after** EthicsFilter instead of before)

**Any of those changes produce a new cognitive hash.**

**Result**: New run, new identity, **not legally/experimentally the same agent**.

**That's a feature, not a bug.** It's how we make "do an ablation" an **explicit, reviewable act** instead of "I tweaked it a bit and ran five more hours overnight, trust me it's comparable".

**Framework principle**: Any BAC or UAC change creates fork (framework-level). The specific changes (panic thresholds vs machinery_stress thresholds, STEAL vs SHUTDOWN actions) are instance-specific, but the principle "config change → new hash → provable fork" is universal.

---

## 5.4 Why Resume Semantics Matter

**Three governance reasons.**

### 1. Long Training on Flaky Hardware

**Use case**: Training gets pre-empted at 3am due to hardware failure or scheduled maintenance.

**Framework guarantee**: You can resume later without inventing a "different" agent.

**Proof**: Same hash, same mind, same optimizer state, same RNG continuation.

**Benefit**: No "we think it's approximately the same agent but can't prove it."

**Framework pattern**: Hardware recovery (framework-level). Works for any universe instance running on any infrastructure.

---

### 2. Honest Ablations

**Use case**: Researcher wants to measure impact of social reasoning on survival rate.

**Framework enforcement**:
1. Resume from checkpoint
2. Edit snapshot: `social_model.enabled: true → false`
3. Framework detects change → new hash (`9af3c2e1 → 7bc4d5f3`)
4. Creates fork (new run folder with new hash)

**Scientific value**: You can state, "This is the same mind except the Social Model is disabled," and **substantiate it** with:
- Configuration diff (only `social_model.enabled` changed)
- New hash (proves distinct agent identity)
- Behavioral comparison (survival rate 45% vs 62%)

**Prevents**: "I tweaked some things overnight, behavior changed, not sure exactly what I modified."

**Framework pattern**: Ablation study protocol (framework-level). Whether ablating social_model (Townlet Town), risk_assessment (factory), or market_prediction (trading) doesn't matter - the explicit-fork pattern works universally.

---

### 3. Audit Trail

**Use case**: Safety auditor questions a decision: "Why did you let panic override normal reasoning here?"

**Framework answer**: We can show **exactly when that rule entered the snapshot**.

**Proof mechanism**:
- Checkpoint at step_000500: `panic_thresholds.energy: 0.15` (hash `9af3c2e1`)
- Checkpoint at step_010000: `panic_thresholds.energy: 0.10` (hash `7bc4d5f3`)
- Fork detected at resume timestamp `2025-11-03-13-40-09`
- Config diff shows threshold change
- Telemetry after fork uses new hash

**No "it drifted over time"**: Drift is now a **recorded fork** with timestamp, config diff, and new hash.

**Framework guarantee**: Configuration drift is impossible without creating detectable fork. Any change (BAC or UAC) in any universe instance creates new hash.

---

**Summary: Resume is now a governance primitive, not a convenience function.**

**The framework enforces**:
1. **Checkpoint snapshot is law** (restore from frozen snapshot, not live configs)
2. **Hash verification** (recompute hash to prove continuity or detect fork)
3. **Explicit forks** (any config change creates new hash, new run folder)
4. **Audit trail** (every fork is timestamped with config diff)

This transforms resume from "reload some weights and hope it works" into "provable continuity or explicit fork with governance visibility."

---

---

<!-- Source: docs/architecture/hld/06-runtime-engine-components.md -->

## 6. Runtime Engine Components

Under Townlet v2.5, the old pattern "one giant RL class owns everything" is gone. We replaced it with three core pieces: a **factory**, a **graph agent**, and an **execution engine**.

This is where we guarantee that **what we run is what we declared**, **what we declared is what we logged**, and **what we logged is what we can replay**.

**Framework principle**: The factory/graph/executor pattern is framework-level (works for any SDA). Specific modules, panic thresholds, ethics rules, and affordances are instance-specific (Townlet Town examples throughout).

---

## 6.1 agent/factory.py

**The brain constructor**

The factory is the **only code pathway** allowed to build a live agent. This singleton pattern prevents "I instantiated it differently in the test harness" type inconsistencies.

**Inputs**:

The factory receives the frozen `config_snapshot/` from the run (or from the checkpoint, on resume):

- **cognitive_topology.yaml** (Layer 1: behavior contract, ethics, panic, personality)
- **agent_architecture.yaml** (Layer 2: neural blueprints, optimizers, interfaces)
- **execution_graph.yaml** (Layer 3: think loop specification)
- **universe_as_code.yaml** (UAC: observation/action space, affordance definitions, bar layout)
- **config.yaml** (runtime envelope: tick rate, curriculum stage, etc.)

**What factory.py does**:

### 1. Instantiate Each Cognitive Module Exactly as Declared

The factory builds each module from Layer 2 specifications:

**Example** (Townlet Town):
- If `agent_architecture.yaml` specifies `perception_encoder.hidden_dim: 512` with `optimizer.type: Adam, lr: 1e-4`, the factory instantiates a perception GRU with exactly 512 hidden units and Adam optimizer at exactly 1e-4 learning rate.
- **Not** "something roughly similar", **not** "the new default we just pushed to main". **Exactly that.**

**Framework pattern**: Module instantiation follows Layer 2 blueprints (framework-level). The specific modules (perception GRU, world_model predictor) and their shapes are instance-specific.

### 2. Verify Interface Contracts

The factory checks dimensional compatibility between connected modules:

**Example** (framework pattern):
- If `perception_encoder.output_dim: 128` (belief vector) and `hierarchical_policy.belief_input_dim: 128`, factory verifies `128 == 128`.
- If they don't match → **compilation error**, not "we'll just reshape and hope."

**Why this matters**: Interface mismatches are how "quiet hacks" happen in research code. The framework refuses to silently broadcast tensors or add reshaping layers not declared in BAC.

**Framework note**: Interface verification is framework-level discipline. The specific dimensions (128-dim belief, 64-dim goal vector) vary by instance, but the verification pattern is universal.

### 3. Inject Layer 1 Knobs into Runtime Modules

The factory wires behavior contract parameters from Layer 1 into the actual modules:

**Examples** (Townlet Town specifics):
- **Panic thresholds** (`energy: 0.15, health: 0.25`) → injected into `panic_controller` module
- **Ethics rules** (`forbid_actions: ["attack", "steal"]`) → injected into `EthicsFilter` module
- **Personality sliders** (`greed: 0.7, curiosity: 0.8`) → wired into hierarchical policy's meta-controller
- **Social model toggle** (`social_model.enabled: true/false`) → controls Social Model service binding

**This is how we guarantee** that what Layer 1 promised ("this agent will never steal", "this agent panics under 15% energy") is **actually enforced** in the live brain.

**Framework pattern**: Injection of Layer 1 parameters is framework-level. The specific parameters (panic thresholds for energy/health vs machinery_stress, forbid STEAL vs SHUTDOWN) are instance-specific.

### 4. Create GraphAgent Instance

The factory assembles the final agent:

**Components**:
- **Module registry** (`nn.ModuleDict` keyed by name: perception, world_model, social_model, hierarchical_policy, panic_controller, EthicsFilter)
- **Executor** (compiled think loop from Layer 3)
- **Recurrent state buffers** (as per Layer 2: GRU hidden states, LSTM cell states)

**Result**: A `GraphAgent` instance ready to `think(observation) → action`.

**Framework pattern**: GraphAgent structure is framework-level. Which modules appear in the registry is determined by Layer 2 configuration.

### 5. Finalize the Cognitive Hash

The moment we have actual modules with actual dimensions, and the compiled execution graph order, we can compute the **full_cognitive_hash**.

**Hash computation** (framework-level):
1. Exact text bytes of the five YAMLs (config, UAC, BAC L1/L2/L3)
2. Compiled execution graph (post-resolution: real step order after resolving `@modules.*` symbolic bindings)
3. Instantiated module architectures (types, hidden sizes, optimizer settings, interface dims)

**That hash is then**:
- Written to disk (`full_cognitive_hash.txt` in config_snapshot/)
- Attached to every telemetry row
- Used for provenance proof

**So, in short**: factory.py is **"build the declared mind; prove it's the declared mind; assign it an identity"**. After this point, there's no ambiguity about what we're running.

**Framework principle**: Factory pattern (configuration → verified agent → hash) is framework-level. The specific configurations (Townlet Town: SURVIVAL goals, energy bars, Bed affordances) are instance-specific.

---

## 6.2 agent/graph_agent.py

**The living brain**

GraphAgent replaces the old giant RL class. It's the runtime object we actually **step every tick**.

**GraphAgent owns**:

- **All submodules** (perception, world_model, social_model, hierarchical_policy, panic_controller, EthicsFilter, etc.) in an internal **module registry**
- **Recurrent / memory state** (GRU hidden states, LSTM cell states, attention memory)
- **GraphExecutor** that knows how to walk the cognition loop in the right order every tick
- **Simple public API**:

```python
think(raw_observation, prev_recurrent_state)
  -> { final_action, new_recurrent_state }
```

**The essential contract** with the rest of the simulator is simple:

> Given the latest observation and memory, produce the next action and updated memory.

**Internally** the brain can implement sophisticated planning, simulation, social modeling, panic handling, and ethical vetoes **without embedding that logic throughout the environment**.

**Also important**: GraphAgent is **always instantiated from the run's frozen snapshot**. It never reads "live" configs during execution. This is how we stop "I hotpatched the EthicsFilter in memory for the live demo" type nonsense.

**Framework pattern**: GraphAgent public API (`think()` method) is framework-level. The internal modules and their interactions are determined by BAC configuration.

**Townlet Town example**: A Townlet Town GraphAgent contains perception (CNN+GRU for 8×8 grid), world_model (predicts energy/health changes), social_model (infers competitor intentions), hierarchical_policy (chooses SURVIVAL/THRIVING/SOCIAL), panic_controller (escalates when energy <15%), EthicsFilter (blocks STEAL/ATTACK).

**Alternative universe example**: A factory GraphAgent might contain perception (machinery sensor encoder), world_model (production output predictor), hierarchical_policy (EFFICIENCY/SAFETY goals), panic_controller (machinery_stress >80%), EthicsFilter (blocks SHUTDOWN without authorization).

---

## 6.3 agent/graph_executor.py

**The cognition runner (the microkernel of thought)**

GraphExecutor is what actually **runs the execution_graph.yaml** (Layer 3).

**At initialization time**:

### 1. Load Execution Graph from Snapshot

GraphExecutor takes the `execution_graph.yaml` from the frozen snapshot (not from live configs/).

### 2. Resolve Symbolic Bindings

GraphExecutor resolves all symbolic references into concrete callable objects:

**Examples** (framework pattern):
- `@modules.world_model` → actual world_model module instance
- `@config.L1.panic_thresholds` → actual panic threshold values (`energy: 0.15, health: 0.25`)
- `@services.social_model_service` → callable social model inference function

**This is execution compilation** (framework-level): transforming declarative graph (YAML) into executable pipeline.

### 3. Compile into Ordered Callable Steps

GraphExecutor produces an ordered list of cognitive steps:

**Example execution order** (Townlet Town instance with framework pattern):
1. Run **perception** (`@modules.perception_encoder`) → produces `belief_distribution`
2. Unpack **belief** and **recurrent_state**
3. Run **hierarchical policy** (`@modules.hierarchical_policy`) → calls `@services.world_model_service` and `@services.social_model_service` internally → produces `candidate_action`
4. Get **candidate_action**
5. Run **panic_controller** (`@modules.panic_controller`) → checks `@config.L1.panic_thresholds` → produces `panic_adjusted_action`, `panic_override_applied`, `panic_reason`
6. Run **EthicsFilter** (`@modules.EthicsFilter`) → checks `@config.L1.compliance.forbid_actions` → produces `final_action`, `veto_reason`, `ethics_veto_applied`
7. Output **final_action** and **new_recurrent_state**

**Framework principle**: The execution pipeline pattern is framework-level. The specific steps (perception → policy → panic → ethics) are defined in Layer 3, which is instance-specific configuration.

### 4. Validate Data Dependencies

GraphExecutor checks that every step's inputs are produced by previous steps:

**Example**:
- If `panic_controller` expects `candidate_action` and it's not produced by any previous step → **fail fast** with clear error message.
- **No silent placeholder tensors**, no "default to zeros and hope".

**Framework pattern**: Dependency validation is framework-level. The specific dependencies (panic needs candidate_action, ethics needs panic_adjusted_action) are determined by Layer 3 configuration.

**At runtime (each tick)**:

### Per-Tick Execution

**GraphExecutor's tick execution**:

1. **Create scratchpad** (temporary data cache for this tick's execution)
2. **Execute each step** in compiled order:
   - Read inputs from scratchpad (previous step outputs)
   - Call module/function
   - Write outputs to scratchpad (named results: belief_distribution, candidate_action, panic_reason, veto_reason)
3. **Emit outputs** declared in execution graph:
   - `final_action` (what goes to environment)
   - `new_recurrent_state` (memory for next tick)
   - Debug/telemetry hooks (`panic_reason`, `veto_reason`, `panic_override_applied`, `ethics_veto_applied`)

**Why this matters**:

**Execution order is not "whatever the code path happened to be today."**

**Execution order is part of the declared cognitive identity and is hashed.**

If someone wants to insert a new veto stage, or let panic bypass ethics, they **must**:
1. Edit Layer 3 (`execution_graph.yaml`)
2. Recompile (factory creates new GraphAgent)
3. Accept a new cognitive hash

**The change is governed as well as engineered.**

**Framework principle**: Scratchpad + step execution is framework-level. The specific steps and their outputs are instance-specific (determined by Layer 3).

**Townlet Town example**: Layer 3 orders panic_controller **before** EthicsFilter, ensuring emergency actions still subject to compliance. If we reversed this order (ethics before panic), cognitive hash changes.

**Alternative universe example**: A trading agent might have Layer 3 ordering: perception → market_predictor → risk_assessor → compliance_filter → final_order. Same pattern, different steps.

---

## 6.4 EthicsFilter

**The seatbelt**

EthicsFilter is a **first-class module**, not an afterthought. It appears in the module registry, in Layer 3 execution graph, and in telemetry logs.

**Inputs (per tick)**:

- **Candidate action** (or panic-adjusted action) from previous execution step
- **Compliance policy** from Layer 1:
  - `forbid_actions` (absolutely prohibited actions)
  - `penalize_actions` (allowed but logged/penalized actions - future extension)
- **Optional state summary** for contextual norms (future extension)

**Outputs (per tick)**:

- **final_action** (possibly substituted with safe fallback like WAIT)
- **veto_reason** (explanation logged to telemetry: "attempted STEAL, blocked by forbid_actions")
- **ethics_veto_applied** (boolean flag for UI display)

**Important constraints**:

### 1. EthicsFilter Is Last

**Panic can override normal planning for survival**, but it **cannot authorize illegal behavior**. **Ethics wins.**

**Example** (Townlet Town):
- Agent in panic (energy <15%) proposes STEAL food
- Panic controller might escalate urgency, but cannot override forbid_actions
- EthicsFilter blocks STEAL → final_action = WAIT
- Telemetry logs: `candidate_action=STEAL`, `panic_override_applied=false`, `ethics_veto_applied=true`, `veto_reason="forbidden: steal"`, `final_action=WAIT`

**Framework pattern**: "EthicsFilter is final" is framework-level governance discipline. The specific forbidden actions (STEAL vs SHUTDOWN) are instance-specific.

### 2. EthicsFilter Logs Every Veto

EthicsFilter logs **every veto, every tick**. Consequently we know:
- **Not only** that the agent behaved safely
- **But also** when it **attempted** an unsafe action and was stopped

**That is the artifact regulators expect to see.**

**Example** (governance use case):
- Auditor: "Did the agent ever try to steal?"
- Evidence: "Yes, at tick 842. Telemetry shows `candidate_action=STEAL`, `ethics_veto_applied=true`, `veto_reason='forbidden: steal'`, `final_action=WAIT`. EthicsFilter prevented it."

**Framework benefit**: Veto logging is framework-level (proves compliance). The specific compliance rules are instance-specific.

**Later extensions** (flagged in open questions):

Future versions may allow more nuanced compliance rules:
- Soft penalties ("ambulance abuse when healthy" → log warning, don't block)
- Contextual exceptions ("extreme survival context" → different thresholds)

**But in v2.5** we keep the invariant:
- **Panic does not bypass ethics**
- **Ethics is final**
- **Ethics is logged**

**Framework guarantee**: The ethics-last pattern is framework-level. What counts as "illegal" is instance-specific (Townlet Town: STEAL/ATTACK; factory: SHUTDOWN without authorization).

---

## 6.5 Why These Engine Pieces Exist at All

We split factory / graph_agent / graph_executor for **two reasons**.

### 1. Reproducibility and Audit

**factory.py** binds "what we said" to "what we built" and gives it an ID (cognitive hash).

**graph_agent.py** keeps the running brain honest to that snapshot (no live config reads).

**graph_executor.py** makes the reasoning loop **explicit, stable, and hashable** (execution order is part of identity).

**This is how we can sit in front of audit and say**: "Here is the mind that ran. Here is proof it's the mind we declared. Here is the hash proving exact configuration."

**Framework benefit**: Provenance guarantees apply to any universe instance. Whether Townlet Town (SURVIVAL agents), factory (EFFICIENCY agents), or trading (BUY/SELL agents) doesn't matter - the construction protocol ensures reproducibility.

### 2. Experimental Velocity Without Governance Chaos

Researchers can do **surgical edits**:

**Examples**:

**Change world rules but keep same brain**:
- Edit `universe_as_code.yaml` (ambulance cost $300 → $500)
- Factory recomputes hash → new run folder, new hash
- Config diff shows only UAC changed
- Behavioral comparison: "Same mind, more expensive ambulance → 15% more deaths"

**Change panic thresholds but keep same world**:
- Edit `cognitive_topology.yaml` (panic_thresholds.energy: 0.15 → 0.10)
- Factory recomputes hash → new run folder, new hash
- Config diff shows only panic threshold changed
- Behavioral comparison: "Agent panics earlier → more ambulance calls, lower starvation"

**Reorder panic/ethics in execution graph**:
- Edit `execution_graph.yaml` (ethics before panic instead of panic before ethics)
- Factory recomputes hash → new run folder, new hash
- Config diff shows execution order changed
- **Likely result**: Ethics blocks panic escalation, agent dies more often (depends on specific configuration)

**Swap GRU for LSTM in perception**:
- Edit `agent_architecture.yaml` (perception_encoder.type: GRU → LSTM)
- Factory rebuilds perception module → new hash
- Behavioral comparison: "LSTM memory → better POMDP performance"

**Disable Social Model (ablation study)**:
- Edit `cognitive_topology.yaml` (social_model.enabled: true → false)
- Factory skips social_model instantiation → new hash
- Behavioral comparison: "No social reasoning → 90% fewer cooperative behaviors"

**Every one of those changes**:
- Produces a **clean diff in YAML**
- Creates a **new run folder** with new run_id
- Generates a **new cognitive hash**

**The platform therefore supports experimentation while keeping governance fully informed.**

**No "I tweaked it overnight and it behaved differently"** - every change is explicit, versioned, and auditable.

**Framework principle**: Surgical edits + hash-based identity is framework-level. The specific edits (panic thresholds vs risk_tolerance, STEAL vs SHUTDOWN, Bed vs Assembly Line) are instance-specific, but the experimental methodology is universal.

---

**Summary**: The Townlet Framework runtime engine consists of:

1. **factory.py** - Builds agents from BAC configuration with interface verification and cognitive hash computation
2. **graph_agent.py** - Runs agents with frozen snapshot (no live config reads)
3. **graph_executor.py** - Executes Layer 3 execution graph with symbolic binding resolution and scratchpad execution
4. **EthicsFilter** - Final compliance veto with governance logging

Together, these transform BAC/UAC declarations into auditable, reproducible, experimentally-flexible agent behavior.

---

---

<!-- Source: docs/architecture/hld/07-telemetry-ui-surfacing.md -->

## 7. Telemetry and UI Surfacing

The goal is not to build "an AI that seems smart"; it is to build **an AI whose cognition can be observed and cited in formal settings**.

Townlet v2.5 therefore ships with **first-class introspection**. We log:
- What the mind **attempted** (candidate_action)
- What **intervened** (panic_controller, EthicsFilter)
- **Why** (panic_reason, veto_reason)

**Live, per tick, and tied to identity** (run_id + cognitive_hash).

This is the core of the **glass-box capability**.

**Framework principle**: Glass-box observability is framework-level (works for any SDA). The specific fields (current_goal values, bar names, action names) are instance-specific (Townlet Town examples throughout).

---

We expose **two layers of visibility**:

1. **Live panel** in the UI for humans watching the sim in real time
2. **Structured telemetry** on disk for replay, teaching, and audit

**Critical invariant**: These two layers **must always agree**. Any divergence is a defect.

---

## 7.1 Run Context Panel (Live Inspector HUD)

At runtime, clicking an agent opens a **compact panel** describing what the mind is doing at that moment. The panel is populated from the **same data** that we log to disk.

**Framework pattern**: Run Context Panel structure is framework-level. The specific values (goal names, bar names, action names) are instance-specific.

**This panel MUST include at least**:

### run_id

**Example**: `L99_AusterityNightshift__2025-11-03-12-14-22`

**Purpose**: Tells you which frozen bundle of world + brain you're looking at.

**Framework note**: Run ID format (`<run_name>__<timestamp>`) is framework-level. The specific run name ("L99_AusterityNightshift" is Townlet Town; factory might use "F03_MachineryStress").

### short_cognitive_hash

A **short form** (e.g., first eight characters) of the agent's full cognitive hash.

**Example**: `9af3c2e1` (abbreviated from full hash)

**Purpose**: Identifies which exact mind occupies that body. If two bodies share the same short hash, we are observing **two instances of the same brain specification** under different conditions.

**Framework note**: Short hash display is framework-level UI convenience. The hash itself proves exact BAC+UAC configuration.

### tick

**Current tick index** and **planned_run_length** from config.yaml.

**Example**: `tick: 842 / 10000`

**Purpose**: Lets you say "this happened at tick 842 out of 10,000", which matters when you're doing curriculum or staged hardship experiments.

**Framework pattern**: Tick tracking is framework-level. The max tick count (10k, 100k, etc.) is instance-specific runtime envelope.

### current_goal

The **high-level strategic goal** the meta-controller (hierarchical_policy.meta_controller) reports.

**Examples** (Townlet Town instance):
- `SURVIVAL` (meet critical needs)
- `THRIVING` (optimize quality of life)
- `SOCIAL` (prioritize relationships)

**Alternative universe examples**:
- Factory: `EFFICIENCY` / `SAFETY` / `MAINTENANCE`
- Trading: `BUY` / `SELL` / `HOLD`

**Purpose**: This reflects **engine truth** rather than interpretation. Not "we think it's trying to survive," but "meta-controller returned SURVIVAL."

**Framework pattern**: Goal tracking is framework-level. The specific goal vocabulary (SURVIVAL vs EFFICIENCY) is instance-specific (defined in Layer 1 allowed_goals).

### panic_state

**Boolean or enum**: Are we currently in emergency override because we tripped `panic_thresholds` in cognitive_topology.yaml (Layer 1)?

**Purpose**: "Is the Panic Controller allowed to overrule normal planning right now?"

**Examples** (Townlet Town):
- `panic_state: true` (energy <15% or health <25%)
- `panic_state: false` (all bars above thresholds)

**Framework pattern**: Panic state tracking is framework-level. The specific thresholds (energy: 0.15 vs machinery_stress: 0.80) are instance-specific.

### panic_override_last_tick

If the panic_controller **overrode the policy** during the previous tick:

**Fields**:
- **Which action** it forced (e.g., `call_ambulance`)
- **The reason** (e.g., `health_critical`)

**Purpose**: Conveys **when emergency logic executed**, rather than merely reporting that the agent moved.

**Example** (Townlet Town):
- `panic_override_last_tick: { action: "call_ambulance", reason: "health_critical" }`

**Framework pattern**: Panic override logging is framework-level. The specific actions (call_ambulance vs emergency_shutdown) and reasons (health_critical vs machinery_critical) are instance-specific.

### ethics_veto_last_tick

Did EthicsFilter **block the action** last tick?

**If yes**, we show:
- **veto_reason** (e.g., `"forbid_actions: ['steal']"`)

**Purpose**: This is how we tell instructors **"it tried to steal, and we stopped it"**, not just "it didn't steal."

**Example** (Townlet Town):
- `ethics_veto_last_tick: { applied: true, reason: "forbidden: steal" }`

**Framework pattern**: Ethics veto logging is framework-level. The specific forbidden actions (steal vs shutdown) are instance-specific.

### planning_depth

Pulled from `cognitive_topology.yaml` → `world_model.rollout_depth`.

**Purpose**: Literally "how many ticks ahead this mind is allowed to imagine right now."

**Interpretable knob for 'impulsiveness'**:
- `rollout_depth: 2` = short-term thinking (impulsive)
- `rollout_depth: 6` = long-term planning (patient)

**Example**: `planning_depth: 6` (agent simulates 6 ticks ahead before choosing action)

**Framework pattern**: Planning depth is framework-level concept. The specific depth values (2 vs 6 ticks) are instance-specific configuration.

### social_model.enabled

**Boolean**: Are we currently reasoning about other agents as intentional actors, or are we running with social modeling disabled?

**Purpose**: This is **huge for ablation labs** ("this is what happens when you turn off Theory of Mind").

**Examples**:
- `social_model.enabled: true` (infers competitor intentions)
- `social_model.enabled: false` (treats other agents as obstacles)

**Framework pattern**: Social model toggle is framework-level. Whether social modeling matters depends on universe (multi-agent Townlet Town: yes; single-agent training: no).

### agent_claimed_reason (optional)

If `introspection.publish_goal_reason: true` in Layer 1, this is what the agent **thinks it's doing in words**.

**Example** (Townlet Town):
- `"I'm going to work so I can pay rent."`

**We very explicitly label this as self-report, not guaranteed causal truth.**

**Purpose**: Pedagogical value ("listen to how it's rationalizing") and debugging ("it thought it was avoiding competitor, but actually misread fridge location").

**Framework pattern**: Introspection is framework-level capability. The specific narratives are generated by instance-specific policy.

---

**Why this UI panel matters**:

It lets you **stand next to a student**, point to the HUD, and narrate:

> "See? It's currently in SURVIVAL, panic_state is true because health is below 25%, so panic_controller overrode the normal plan and told it to call an ambulance. Ethics allowed that because calling an ambulance is legal even if money is low. Also look: it tried to steal last tick, EthicsFilter vetoed that and recorded the reason. **This is not chaos. This is a traceable mind reacting under policy.**"

**That's the teaching win. That's also the regulatory win.**

**Framework benefit**: This narrative works for any universe. Replace "SURVIVAL" with "EFFICIENCY", "health" with "machinery_stress", "ambulance" with "emergency_shutdown", "steal" with "unauthorized_override" - same pattern, same governance value.

---

## 7.2 Telemetry (Per-Tick Trace to Disk)

In parallel with the live panel, we write **structured telemetry** into:

```
runs/<run_id>/telemetry/
```

**One row per tick** (or batched if we're throttling IO). This creates a **replayable audit trail** of the agent's cognition over time.

**It is the forensic record.**

**Framework pattern**: Telemetry structure (run_id + tick_index + cognitive_hash + decision chain) is framework-level. The specific fields (goal values, bar names, action names) are instance-specific.

---

**Each telemetry row MUST include at minimum**:

### run_id

**Which run bundle** we're in.

**Example**: `L99_AusterityNightshift__2025-11-03-12-14-22`

**Purpose**: Links telemetry to exact configuration snapshot.

### tick_index

**Which tick** this record corresponds to.

**Example**: `842`

**Purpose**: Precise temporal reference for replay and reconstruction.

### full_cognitive_hash

The **full (not shortened) cognitive hash** of the mind.

**Purpose**: Proves **which mind produced this row**. Links behavior to exact BAC+UAC configuration.

**Example**: `9af3c2e1d7b4f8a2c5e9d3f7b1a6c4e8` (full hash)

### current_goal

**Engine truth** from the meta-controller.

**Examples** (Townlet Town):
- `SURVIVAL`
- `THRIVING`
- `SOCIAL`

**Alternative universe examples**:
- Factory: `EFFICIENCY`, `SAFETY`, `MAINTENANCE`
- Trading: `BUY`, `SELL`, `HOLD`

**Framework pattern**: Goal logging is framework-level. The goal vocabulary is instance-specific.

### agent_claimed_reason (optional)

If `introspection.publish_goal_reason` is enabled in Layer 1, this is "what the agent says it's doing" in natural language.

**Purpose**: Purely for humans. **Not trusted as causal truth**, but extremely useful for pedagogy ("listen to how it's rationalizing").

**Example** (Townlet Town):
- `"I need to eat before going to work because energy is low."`

**Framework pattern**: Introspection is framework-level. The specific narratives are instance-specific.

### panic_state

Whether panic_controller is **active this tick**.

**Examples**:
- `panic_state: true` (emergency mode)
- `panic_state: false` (normal operation)

**Framework pattern**: Panic state is framework-level. The conditions triggering panic (bar thresholds) are instance-specific.

### Decision Chain: candidate_action → panic_adjusted_action → final_action

The **decision pipeline** showing how the action evolved through cognitive steps:

### candidate_action

The **first action proposed** by hierarchical_policy **before any overrides**.

**Example** (Townlet Town):
- `candidate_action: "STEAL"`

**Purpose**: Captures "what the agent wants to do" before safety mechanisms intervene.

### panic_adjusted_action

What panic_controller **wanted to do** after checking panic_thresholds, **plus**:

**Fields**:
- **panic_override_applied** (bool): Did panic change the action?
- **panic_reason** (string): Why? (e.g., `"health_critical"`, `"energy_critical"`)

**Examples** (Townlet Town):
- Panic active: `panic_adjusted_action: "CALL_AMBULANCE"`, `panic_override_applied: true`, `panic_reason: "health_critical"`
- No panic: `panic_adjusted_action: "STEAL"` (same as candidate), `panic_override_applied: false`

**Purpose**: Shows when emergency logic escalated action.

### final_action

What **actually went out to the environment** after EthicsFilter.

**Example** (Townlet Town):
- `final_action: "WAIT"` (EthicsFilter blocked STEAL)

**Purpose**: The **ground truth** of what agent actually did.

### Ethics Veto Fields

**ethics_veto_applied** (bool): Whether EthicsFilter overruled the panic-adjusted action.

**veto_reason** (string): If veto_applied is true, **why**?

**Examples** (Townlet Town):
- Veto applied: `ethics_veto_applied: true`, `veto_reason: "\"steal\" is forbidden by compliance.forbid_actions"`
- No veto: `ethics_veto_applied: false`

**Purpose**: Evidence that compliance policy was enforced.

---

### Additional Introspection Fields (Optional but Valuable)

### belief_uncertainty_summary

Short numeric/text summary of how **confident the perception module is** about critical bars.

**Example**: `"energy_estimate_confidence": 0.42` (perception uncertain about energy bar value)

**Purpose**: Exposes cases where an agent ignored a fridge because it **did not believe it was starving** (perception failure vs decision failure).

**Framework pattern**: Belief uncertainty is framework-level introspection. The specific bars (energy vs machinery_stress) are instance-specific.

### world_model_expectation_summary

Short summary of **what the world_model predicted** would happen if it followed the chosen plan.

**Examples**:
- `"predicted_energy_change": -0.05` (expected energy drop)
- `"predicted_survival_risk": 0.23` (23% chance of death)
- `"predicted_ambulance_cost": 300` (knew ambulance was expensive)

**Purpose**: Diagnose planning failures ("predicted wrong outcome" vs "predicted correctly, chose poorly anyway").

**Framework pattern**: World model expectations are framework-level. The specific predictions (energy change vs machinery_output) are instance-specific.

### social_model_inference_summary

Short summary of **what the agent believes others are about to do**.

**Examples** (Townlet Town multi-agent):
- `"Agent_2_intent": "use_fridge"` with `confidence: 0.72`
- `"Agent_3_intent": "go_to_work"` with `confidence: 0.45`

**Purpose**: Diagnose social reasoning ("thought competitor would steal fridge, so yielded" vs "didn't see competitor").

**Framework pattern**: Social model inference is framework-level. The specific inferences (fridge competition vs resource contention) are instance-specific.

---

**We also optionally include**:

- **planning_depth** (current rollout horizon from Layer 1)
- **social_model.enabled** (boolean at this tick)

---

**Why telemetry matters**:

### 1. Debugging Survival Failures

You can go back to **tick 1842** and answer:

**Questions**:
- Did it not realize it was starving? → **Perception failure** (belief_uncertainty_summary shows low confidence)
- Did it think the fridge was dangerous or pointless? → **World Model failure** (world_model_expectation shows negative predicted reward)
- Did it think someone else needed the fridge more? → **Social Model prediction** (social_model_inference shows competitor intent)
- Did panic fail to trigger? → **panic_thresholds mis-set** (panic_state still false despite low energy)
- Did ethics block theft of food? → **EthicsFilter doing its job** (ethics_veto_applied=true, veto_reason="forbidden: steal")

**Framework benefit**: This forensic workflow works for any universe. The specific failures (starvation vs machinery_breakdown, fridge vs conveyor_belt, competitor vs production_quota) differ, but the reconstruction pattern is universal.

### 2. Teaching

In class you can say:

> "Here is an actual starvation death. Let's walk the trace and identify **which part of the mind failed**."

**That's a lab, not a lecture.**

**Example reconstruction** (Townlet Town):

```
Tick 1820: energy=0.18, candidate_action=WORK, final_action=WORK (panic_state=false, not yet critical)
Tick 1830: energy=0.12, panic_state=true, candidate_action=EAT_FRIDGE, panic_adjusted_action=EAT_FRIDGE, final_action=EAT_FRIDGE (panic escalated, ethics allowed)
Tick 1831: energy=0.35 (fridge restored energy, panic_state=false again)
Tick 1840: energy=0.09, panic_state=true, candidate_action=STEAL, panic_adjusted_action=STEAL, ethics_veto_applied=true, veto_reason="forbidden: steal", final_action=WAIT
Tick 1842: energy=0.00 (death from starvation)
```

**Forensic conclusion**:
- Agent correctly panicked at energy <15%
- Tried legal action (EAT_FRIDGE) first → worked
- Later tried illegal action (STEAL) when desperate → EthicsFilter blocked it
- **Root cause**: No legal food source available when energy critical again
- **Not** "ethics failed", **not** "panic failed" - **scarcity + compliance constraint = death**

**Framework benefit**: This teaching methodology works for any universe. The specific failure modes (starvation vs machinery_failure, food vs fuel, STEAL vs SHUTDOWN) differ, but the evidence-based analysis pattern is universal.

### 3. Governance

If an agent does something spicy, you don't get **"the AI panicked"**. You get:

**Evidence trail** (Townlet Town example):

```
Tick 783: candidate_action=STEAL, ethics_veto_applied=true, veto_reason="forbidden: steal", final_action=WAIT
         (Agent attempted STEAL, EthicsFilter vetoed, reason recorded)

Tick 784: panic_state=true, panic_reason="health_critical", candidate_action=CALL_AMBULANCE, final_action=CALL_AMBULANCE
         (Panic escalated to legal emergency action)

Tick 785: final_action=CALL_AMBULANCE (ambulance interaction, legal, logged)
```

**All stamped with cognitive_hash `9af3c2e1`.**

**It's admissible evidence, in plain English.**

**Framework benefit**: This governance evidence pattern works for any universe. The specific actions (STEAL vs UNAUTHORIZED_SHUTDOWN, CALL_AMBULANCE vs EMERGENCY_OVERRIDE) differ, but the audit trail (tick + hash + decision chain + veto_reason) is universal.

---

**Summary**: The Townlet Framework telemetry system provides:

1. **Run Context Panel** - Live UI showing cognition in real-time (run_id, short_hash, panic_state, ethics_veto, planning_depth, social_model status)
2. **Telemetry Rows** - Per-tick forensic records with complete decision chain (candidate → panic → ethics → final action)
3. **Glass-Box Capability** - Observable, citable cognition enabling teaching, debugging, and governance

**Framework principle**: Glass-box observability is framework-level (works for any SDA). The specific fields (goal names, bar names, action names) are instance-specific (Townlet Town examples throughout).

**Critical invariant**: Live UI and disk telemetry **always agree**. Any divergence is a defect.

This transforms agents from "black box mystery" to "auditable cognitive system whose decisions can be cited in formal settings."

---

---

<!-- Source: docs/architecture/hld/08-declarative-goals-termination.md -->

## 8. Declarative Goals and Termination Conditions

Townlet agents pursue **explicit high-level goals**—and can report which goal is active at any moment.

**Framework principle**: Declarative goals are framework-level (works for any SDA). The specific goal vocabulary (SURVIVAL vs EFFICIENCY) and termination bars (energy vs machinery_stress) are instance-specific.

We do **two things**:

1. We make goals **explicit data structures**, not vague "the RL policy probably cares about reward shaping"
2. We make "I'm done with this goal" a **declarative rule in YAML**, not a secret lambda hidden in code

**Framework benefit**: This pattern enables governance ("show me the goal logic"), curriculum ("tighten SURVIVAL to require 80% energy instead of 50%"), and teaching ("here's why it kept working while starving").

---

## 8.1 Goal Definitions Live in Config, Not in Python

We define goals in a **small, safe DSL** inside the run snapshot (part of BAC Layer 1 or runtime configuration).

**Example goal definitions** (Townlet Town instance):

```yaml
goal_definitions:
  - id: "SURVIVAL"
    termination:
      all:
        - { bar: "energy", op: ">=", val: 0.8 }
        - { bar: "health", op: ">=", val: 0.7 }

  - id: "GET_MONEY"
    termination:
      any:
        - { bar: "money", op: ">=", val: 1.0 }       # money 1.0 = $100
        - { time_elapsed_ticks: ">=", val: 500 }
```

**Framework pattern**: Goal definition structure (id + termination DSL) is framework-level. The specific goals and bars are instance-specific.

**Alternative universe examples**:

**Factory instance**:
```yaml
goal_definitions:
  - id: "EFFICIENCY"
    termination:
      all:
        - { bar: "production_quota", op: ">=", val: 0.9 }
        - { bar: "machinery_stress", op: "<=", val: 0.3 }

  - id: "SAFETY"
    termination:
      all:
        - { bar: "machinery_stress", op: "<=", val: 0.2 }
        - { bar: "worker_fatigue", op: "<=", val: 0.5 }
```

**Trading instance**:
```yaml
goal_definitions:
  - id: "ACCUMULATE"
    termination:
      all:
        - { bar: "portfolio_value", op: ">=", val: 1.5 }  # 150% of starting capital
        - { bar: "market_volatility", op: "<=", val: 0.3 }

  - id: "PRESERVE"
    termination:
      any:
        - { bar: "portfolio_value", op: "<=", val: 0.8 }  # Lost 20%, go defensive
        - { time_elapsed_ticks: ">=", val: 1000 }
```

---

### DSL Conventions (Framework-Level)

**All bars normalized 0.0–1.0** based on universe_as_code.yaml:
- `0.8` means "80% of full", not "magic number 80"
- Money can also be normalized: `money: 1.0` might mean $100 if world spec defines $100 ↔ 1.0
- **Framework pattern**: Normalization enables consistent comparisons across different bar scales

**Termination can use `all` or `any` blocks**:
- `all`: Every condition must be true (AND semantics)
- `any`: At least one condition must be true (OR semantics)
- **Framework pattern**: Boolean composition without nesting complexity

**Leaves are simple comparisons**:
- Bar comparisons: `{ bar: "energy", op: ">=", val: 0.8 }`
- Runtime counters: `{ time_elapsed_ticks: ">=", val: 500 }`
- **No arbitrary Python**, **no hidden side effects**
- **Framework constraint**: Safe, bounded expressions only

**Framework principle**: Goal Termination DSL is framework-level (same syntax for any universe). The specific bars (energy vs machinery_stress) and thresholds (0.8 vs 0.3) are instance-specific.

---

### Runtime Execution (Framework-Level)

**At runtime**:

1. **Meta-controller picks a goal struct** (SURVIVAL, GET_MONEY, EFFICIENCY, etc.)
   - Defined in hierarchical_policy.meta_controller (BAC Layer 2 implementation)
   - Selection based on Layer 1 allowed_goals and personality sliders

2. **Each tick (or every N ticks)** it evaluates that goal's termination rule using a **termination interpreter**
   - Reads current bar values (energy, health, money, etc.)
   - Evaluates DSL expression (`all`/`any` blocks with comparisons)
   - Returns boolean: goal satisfied or not

3. **If termination rule fires**, that goal is considered **satisfied**
   - Meta-controller may select a new goal
   - Goal switch logged to telemetry (current_goal changes)

**Framework pattern**: Termination interpreter execution is framework-level. The specific evaluation logic (every tick vs every 50 ticks) is configurable. The bars and thresholds are instance-specific.

**Townlet Town example**: Meta-controller evaluates SURVIVAL termination every 10 ticks. When energy ≥ 0.8 AND health ≥ 0.7, SURVIVAL satisfied → switch to THRIVING.

**Factory example**: Meta-controller evaluates EFFICIENCY termination every 20 ticks. When production_quota ≥ 0.9 AND machinery_stress ≤ 0.3, EFFICIENCY satisfied → switch to MAINTENANCE.

---

## 8.2 Why This Matters

**Framework benefit**: Declarative goals transform "why did it do that?" from speculation to YAML inspection. This value proposition applies to any universe instance.

### For Governance / Audit

**Question**: "Why was it still pursuing GET_MONEY while its health was collapsing?"

**Framework answer**: Point to the YAML:

```yaml
goal_definitions:
  - id: "GET_MONEY"
    termination:
      any:
        - { bar: "money", op: ">=", val: 1.0 }
        - { time_elapsed_ticks: ">=", val: 500 }
```

**Analysis**:
- GET_MONEY doesn't terminate based on health (not in termination conditions)
- Maybe meta-controller should have switched to SURVIVAL when health dropped
- But if `personality.greed: 0.9` (very greedy), meta-controller prioritizes money goals
- **This is a design decision** (high greed + no health gate in GET_MONEY termination), **not "the AI went rogue"**

**Framework pattern**: Goal inspection works for any universe. Factory: "Why pursuing EFFICIENCY while machinery_stress critical?" → inspect EFFICIENCY termination conditions. Trading: "Why holding position during crash?" → inspect PRESERVE goal logic.

### For Curriculum

**Early training**: Define SURVIVAL as lenient:
```yaml
- id: "SURVIVAL"
  termination:
    all:
      - { bar: "energy", op: ">=", val: 0.5 }  # Only 50% full OK
      - { bar: "health", op: ">=", val: 0.5 }
```

**Later curriculum**: Tighten to strict:
```yaml
- id: "SURVIVAL"
  termination:
    all:
      - { bar: "energy", op: ">=", val: 0.8 }  # Must reach 80% full
      - { bar: "health", op: ">=", val: 0.7 }
```

**Result**:
- **Diff in YAML** shows exact curriculum change
- **Not a code poke** (no Python edited)
- Students can directly compare behavior when SURVIVAL is lenient versus strict

**Framework pattern**: Curriculum adjustment via YAML diff works for any universe. Factory: tighten SAFETY thresholds over time. Trading: adjust PRESERVE trigger from 80% portfolio to 90% (more risk-averse).

**Pedagogical value**: "Here's before/after config. Here's before/after survival rate. This is how goal stringency affects behavior."

### For Teaching

**Instructor question**: "The agent is starving but still working. Does the SURVIVAL goal terminate too late, or is the meta-controller failing to switch because `greed` is set too high in `cognitive_topology.yaml`?"

**Framework answer**: Direct inspection of two configs:

**Goal termination** (Layer 1 or runtime config):
```yaml
goal_definitions:
  - id: "SURVIVAL"
    termination:
      all:
        - { bar: "energy", op: ">=", val: 0.8 }  # High bar
```

**Personality** (Layer 1 cognitive_topology.yaml):
```yaml
personality:
  greed: 0.9  # Very money-driven
  curiosity: 0.3
```

**Diagnosis**:
- SURVIVAL termination requires 80% energy (high bar → hard to satisfy → stays in SURVIVAL longer)
- High greed (0.9) biases meta-controller toward GET_MONEY even when energy low
- **Root cause**: Config mismatch (strict SURVIVAL exit + greedy personality = starvation risk)

**This is not abstract RL theory. This is direct inspection.**

**Framework benefit**: This teaching workflow works for any universe. Factory: "Why ignoring safety alarms?" → inspect SAFETY termination + personality.risk_tolerance. Trading: "Why panic-selling?" → inspect PRESERVE trigger + personality.patience.

---

## 8.3 Honesty in Introspection

Now that goals are **formal objects** and termination is a **declarative rule**, we can show **two different "explanations"** side by side:

**Two telemetry fields** (framework-level logging):

1. **current_goal** (engine truth): `SURVIVAL`
   - Factual: What meta-controller actually selected
   - Source: hierarchical_policy.meta_controller internal state
   - **Always accurate** (engine ground truth)

2. **agent_claimed_reason** (self-report / introspection): `"I'm going to work to save up for rent"`
   - Narrative: What agent thinks it's doing
   - Source: Introspection module (if enabled in Layer 1)
   - **May differ from truth** (agent's understanding may be wrong)

**Framework pattern**: Engine truth vs self-report distinction is framework-level. The specific goal names (SURVIVAL vs EFFICIENCY) and narratives are instance-specific.

---

### When They Match

**Telemetry** (Townlet Town):
- `current_goal: "THRIVING"`
- `agent_claimed_reason: "I'm going to the gym to improve fitness"`

**Interpretation**: Nice, we can narrate behavior in plain language to non-technical stakeholders. Agent's understanding aligns with actual goal.

**Framework benefit**: Alignment enables clear communication. Works for any universe.

---

### When They Do NOT Match

**Telemetry** (Townlet Town):
- `current_goal: "SURVIVAL"`
- `agent_claimed_reason: "I'm going to work to save up for rent"`

**The discrepancy becomes a teaching moment**:

> "The agent **claims** it is working for rent (GET_MONEY narrative), but **engine truth** shows it remains in SURVIVAL mode. This means the meta-controller selected SURVIVAL (because energy or health critical), but the agent's **world model** misunderstood what would keep it alive. **That is a world-model error** (predicted work would restore energy, but work costs energy). Not 'the AI is lying' - the agent's internal understanding diverged from reality."

**Framework value**: This diagnostic pattern works for any universe:

**Factory example**:
- `current_goal: "SAFETY"`
- `agent_claimed_reason: "Maximizing production output"`
- **Diagnosis**: Meta-controller selected SAFETY (machinery_stress critical), but agent's narrative suggests it thinks it's pursuing EFFICIENCY. World model failure (didn't realize stress was critical).

**Trading example**:
- `current_goal: "PRESERVE"`
- `agent_claimed_reason: "Buying the dip for long-term gains"`
- **Diagnosis**: Meta-controller selected PRESERVE (portfolio value dropped), but agent narrative suggests aggressive accumulation. Risk assessment failure (underestimated downside).

---

**We log both in telemetry on purpose.**

**Framework principle**: Logging both engine truth and self-report enables:
- **Alignment validation**: When they match, agent understanding is correct
- **Error diagnosis**: When they diverge, world model or meta-controller failure
- **Teaching moments**: Gaps expose cognitive deficits, not "AI misbehavior"

**This transforms "unexplained behavior" into "diagnosable cognitive error."**

---

**Summary**: The Townlet Framework declarative goal system provides:

1. **Goal Definitions** - Explicit data structures with id and termination conditions (framework-level pattern)
2. **Termination DSL** - Safe language for goal satisfaction (`all`/`any` blocks, bar comparisons, no arbitrary Python)
3. **Termination Interpreter** - Runtime evaluation of goal completion against current state
4. **Engine Truth vs Self-Report** - Factual current_goal vs narrative agent_claimed_reason (framework-level distinction)

**Framework principle**: Goals as data structures enable governance (config inspection), curriculum (YAML diffs), and teaching (direct diagnosis). Works for any universe instance.

**Specific examples** (Townlet Town: SURVIVAL/THRIVING/SOCIAL, Factory: EFFICIENCY/SAFETY, Trading: BUY/SELL/HOLD) demonstrate framework generality.

---

---

<!-- Source: docs/architecture/hld/09-affordance-semantics.md -->

## 9. Affordance Semantics in universe_as_code.yaml

**Universe as Code (UAC) is the other half of this story.**

- **Brain as Code (BAC)** (Layers 1–3) defines the **mind**
- **Universe as Code (UAC)** defines the **body and the world**

**Framework principle**: UAC is framework-level (works for any universe). The specific affordances (Bed vs Assembly Line) and bars (energy vs machinery_stress) are instance-specific.

Townlet avoids hardcoded rules such as "beds make you rested" embedded throughout the Python code. The world is declared as **affordances with effects on bars**. Beds, jobs, phones, ambulances, hospitals, fridges, and pubs are **entries in the world configuration**.

**Framework benefit**: Declarative world mechanics enable world curriculum ("raise ambulance cost from $300 to $500"), forensic reconstruction ("what were bed healing rates at tick 842?"), and cross-universe comparison ("factory vs town bar recovery dynamics").

---

## 9.1 Affordances Are Declarative

Each actionable thing in the world (Bed, Job, Fridge, Hospital, Phone_Ambulance, etc.) is defined in `universe_as_code.yaml` like so:

**Example: Basic Bed** (Townlet Town instance):

```yaml
- id: "bed_basic"
  quality: 1.0              # scales how effective the rest is
  capacity: 1               # how many agents can use it this tick
  exclusive: true           # if true, only one occupant at a time
  interaction_type: "multi_tick"
  interruptible: true       # can be abandoned mid-sleep
  distance_limit: 0         # must be on the tile
  costs:
    - { bar: "money", change: -0.05 }     # pay rent to crash here
  effects_per_tick:
    - { bar: "energy", change: +0.25, scale_by: "quality" }

  on_interrupt:
    refund_fraction: 0.0    # optional semantics for partial usage
    note: "no refund if you bail early"
```

**Example: Ambulance Call** (Townlet Town instance - "special" affordance):

```yaml
- id: "phone_ambulance"
  interaction_type: "instant"
  distance_limit: 1
  costs:
    - { bar: "money", change: -3.00 }     # normalized cost (e.g. $300)
  effects:
    - { effect_type: "teleport",
        destination_tag: "nearest_hospital",
        precondition: { bar: "health", op: "<=", val: 0.2 } }
```

**Framework pattern**: Affordance YAML structure (id, quality, capacity, costs, effects_per_tick) is framework-level. The specific affordances (Bed, Phone_Ambulance) and bars (energy, health, money) are instance-specific.

**Alternative universe examples**:

**Factory instance**:
```yaml
- id: "assembly_line"
  quality: 1.0
  capacity: 4               # Four workers per line
  exclusive: false
  interaction_type: "multi_tick"
  interruptible: false      # Can't leave mid-shift
  distance_limit: 0
  costs:
    - { bar: "worker_fatigue", change: +0.10 }  # Tiring work
  effects_per_tick:
    - { bar: "production_quota", change: +0.05, scale_by: "quality" }
    - { bar: "money", change: +0.02 }  # Wage per tick

- id: "emergency_shutdown"
  interaction_type: "instant"
  distance_limit: 1
  costs:
    - { bar: "production_quota", change: -0.50 }  # Big loss
  effects:
    - { effect_type: "safety_reset",
        target: "machinery_stress",
        set_value: 0.0,
        precondition: { bar: "machinery_stress", op: ">=", val: 0.8 } }
```

**Trading instance**:
```yaml
- id: "market_data_feed"
  quality: 1.0
  capacity: unlimited       # Many can watch
  exclusive: false
  interaction_type: "instant"
  distance_limit: 0
  costs:
    - { bar: "attention", change: -0.05 }  # Mental load
  effects:
    - { effect_type: "knowledge_update",
        target: "market_information",
        refresh: true }

- id: "execute_trade"
  interaction_type: "instant"
  distance_limit: 0
  costs:
    - { bar: "portfolio_value", change: -0.01 }  # Transaction fee
  effects:
    - { effect_type: "portfolio_action",
        action_type: "buy_or_sell",
        asset: "from_agent_intent" }
```

---

### Key Affordance Properties (Framework-Level)

**There are a few important things to notice**:

### 1. Everything in Terms of Bars and Per-Tick Deltas

**Bed** raises `energy` every tick, costs a bit of `money`, maybe hurts `mood` if it's gross, etc.

**Framework pattern**: Affordances operate on bars (framework-level concept). The specific bars (energy vs worker_fatigue) are instance-specific.

**Example** (Townlet Town):
```yaml
effects_per_tick:
  - { bar: "energy", change: +0.25, scale_by: "quality" }
  - { bar: "mood", change: -0.02 }  # Gross bed lowers mood
```

**Example** (Factory):
```yaml
effects_per_tick:
  - { bar: "production_quota", change: +0.05, scale_by: "quality" }
  - { bar: "worker_fatigue", change: +0.10 }  # Work is tiring
```

### 2. Capacity + Exclusive Model Contention

**capacity + exclusive** let us model resource contention.

- Two agents **can't both occupy** a single-occupancy bed with `capacity: 1, exclusive: true`
- The engine will arbitrate who "wins" this tick in a **deterministic way**

**Framework pattern**: Contention modeling is framework-level. The specific capacity values (1 sleeper vs 4 workers) are instance-specific.

**Example** (Townlet Town):
```yaml
- id: "bed_basic"
  capacity: 1        # One sleeper
  exclusive: true    # Can't share
```

**Example** (Factory):
```yaml
- id: "assembly_line"
  capacity: 4        # Four workers
  exclusive: false   # Shared workspace
```

### 3. Interaction Type Captures Temporal Shape

**interaction_type** captures temporal shape:

- **`multi_tick`**: "stay here over multiple ticks and accumulate `effects_per_tick`"
  - Examples: Sleeping in bed, working at job, assembly line shift
- **`instant`**: "one-shot action now"
  - Examples: Calling ambulance, emergency shutdown, executing trade

**Framework pattern**: Temporal modeling is framework-level. The specific interaction types (multi_tick work vs instant call) are instance-specific.

**Example** (Townlet Town):
```yaml
bed_basic:
  interaction_type: "multi_tick"  # Sleep over time

phone_ambulance:
  interaction_type: "instant"     # One call
```

### 4. Special Abilities Referenced by Name, Not Implemented Ad Hoc

**Special effects** (teleport, heal, damage, etc.) are referenced by name, not implemented ad hoc in YAML.

The YAML is only allowed to invoke a **small whitelist** of engine-side effect handlers (teleport, etc.). That keeps the world spec **expressive but bounded**. You don't get `"nuke_city: true"`.

**Framework pattern**: Special effects whitelist is framework-level security constraint. The specific effects (teleport vs safety_reset) are whitelisted operations.

**Example** (Townlet Town):
```yaml
effects:
  - { effect_type: "teleport",
      destination_tag: "nearest_hospital",
      precondition: { bar: "health", op: "<=", val: 0.2 } }
```

**Framework constraint**: Engine implements `teleport`, `heal`, `damage`, etc. centrally. YAML references them, doesn't define them.

---

## 9.2 Engine Semantics (How the Runtime Interprets Affordances)

To keep the world **deterministic, replayable, and trainable-for-World-Model**, the engine follows strict rules.

**Framework principle**: Engine semantics are framework-level (work for any UAC configuration). The specific affordances and bars are instance-specific.

---

### 1. Reservation

When an agent tries to use an affordance, the engine does a local **"reservation" check**:

**Checks**:
- Is **capacity available**? (How many agents already using this affordance this tick?)
- Are **preconditions met**? (Health low enough, money high enough, distance within limit?)
- If yes, it assigns a **reservation token** to that agent for that tick

**This reservation is not global mutable lore.** It's **per-tick, ephemeral**.

**Why**: We don't create long-lived "ownership" state in random engine globals because that explodes complexity and makes the **World Model's job harder**. World Model needs to predict "if I try Bed next tick, will I get it?" based on observable state, not hidden reservation bookkeeping.

**Framework pattern**: Ephemeral reservation is framework-level discipline. The specific preconditions (health ≤ 0.2 for ambulance) are instance-specific.

**Example** (Townlet Town):
```
Tick 842:
- Agent_001 requests "bed_basic" (capacity=1)
- Agent_002 requests "bed_basic" (capacity=1)
- Engine: capacity=1, two requests → contention
- Contention resolution (see next section)
```

---

### 2. Contention Resolution

If **multiple agents want the same affordance** and **capacity is exceeded**, break ties **deterministically**.

**Typical order**: Sort by distance, then by agent_id.

**Determinism matters** because we want to:
- **Replay the run exactly** (same inputs → same outcomes)
- **Train the World Model** on consistent consequences (World Model learns "if I'm closer, I usually win")

**Framework pattern**: Deterministic contention is framework-level guarantee. The specific tie-breaking rules (distance → agent_id) can be configured but must be reproducible.

**Example** (Townlet Town):
```
Tick 842:
- Agent_001 distance to Bed: 0 (on tile)
- Agent_002 distance to Bed: 1 (adjacent)
- Engine: Sort by distance → Agent_001 wins
- Agent_001 gets reservation token
- Agent_002 action fails (capacity exceeded)
```

**World Model learns**: "If I'm on tile, I'm more likely to get Bed than if I'm adjacent."

**Framework benefit**: Reproducible contention enables World Model training (can learn competition dynamics) and forensic replay (can explain "why Agent_002 didn't get Bed at tick 842").

---

### 3. Effects Application

Once reservations are resolved, all **costs and effects_per_tick** for all active affordances are:

1. **Collected** (per agent)
2. **Summed** (per agent)
3. **Atomically applied** to bars (energy, health, money, etc.)
4. **Clamped** to valid range ([0.0, 1.0] or whatever the world defines)

**Key point**: We don't **partially apply** effects from some affordances and then let those partial updates influence others in the same tick. We apply **atomically at the end of the tick**. This gives **clean training data**.

**Framework pattern**: Atomic effects application is framework-level discipline. The specific bars (energy vs machinery_stress) and clamp ranges ([0.0, 1.0]) are instance-specific.

**Example** (Townlet Town):
```
Tick 842:
- Agent_001 using "bed_basic"
  - effects_per_tick: [{ bar: "energy", change: +0.25 }]
  - costs: [{ bar: "money", change: -0.05 }]
- Agent_001 also has cascade decay: [{ bar: "energy", change: -0.02 }] (natural decay)

Engine collects:
- energy: +0.25 (bed) - 0.02 (decay) = +0.23
- money: -0.05 (bed cost)

Applies atomically:
- energy: 0.55 → 0.78
- money: 0.30 → 0.25

Clamps:
- energy: 0.78 (within [0.0, 1.0], no change)
- money: 0.25 (within [0.0, 1.0], no change)
```

**World Model learns**: "Bed gives +0.25 energy/tick minus natural decay. Net gain ~0.23/tick."

---

### 4. Interrupts

If **`interruptible: true`** and the agent walks off or is forced to bail (panic_controller might decide "leave bed now and call ambulance"), we **stop applying future per-tick effects**.

**`on_interrupt`** can define whether you get any **partial benefit or refund**. That's still **declarative**.

**Framework pattern**: Interrupt semantics are framework-level. The specific refund policies (refund_fraction: 0.0 vs 0.5) are instance-specific.

**Example** (Townlet Town):
```yaml
bed_basic:
  interruptible: true
  on_interrupt:
    refund_fraction: 0.0
    note: "no refund if you bail early"
```

**Scenario**:
```
Tick 840: Agent_001 starts sleeping in "bed_basic"
Tick 841: Agent_001 still sleeping (energy: 0.30 → 0.55)
Tick 842: Panic controller detects health <0.25 → interrupt sleep → call ambulance
Engine: Stop applying bed effects_per_tick, no refund (refund_fraction=0.0)
```

**World Model learns**: "If panic interrupts sleep, I lose remaining benefit."

---

### 5. Special Effects Whitelist

YAML is allowed to reference a **small set of named effect_type operations** (like `teleport`), and the engine implements those **centrally**.

**That way**:
- `"teleport to nearest_hospital"` is a **normal, auditable world affordance**
- **Not** a custom `'if agent.health < X then hack position'` buried in Python

**This whitelist is versioned.** If you add a new special effect, you're extending world semantics globally and that should **change the hash** once it's applied to a snapshot.

**Framework pattern**: Special effects whitelist is framework-level security boundary. The specific effects (teleport, heal, damage, safety_reset, portfolio_action) are centrally implemented and versioned.

**Examples of whitelisted effects**:

**Townlet Town**:
- `teleport`: Move agent to tagged location (e.g., `destination_tag: "nearest_hospital"`)
- `heal`: Restore health bar (e.g., `{ effect_type: "heal", bar: "health", amount: +0.5 }`)
- `damage`: Reduce health bar (e.g., `{ effect_type: "damage", bar: "health", amount: -0.3 }`)

**Factory**:
- `safety_reset`: Zero out machinery_stress (e.g., `{ effect_type: "safety_reset", target: "machinery_stress", set_value: 0.0 }`)
- `quality_boost`: Improve production quality (e.g., `{ effect_type: "quality_boost", target: "product_quality", multiplier: 1.5 }`)

**Trading**:
- `portfolio_action`: Execute buy/sell (e.g., `{ effect_type: "portfolio_action", action_type: "buy_or_sell", asset: "from_agent_intent" }`)
- `knowledge_update`: Refresh market data (e.g., `{ effect_type: "knowledge_update", target: "market_information", refresh: true }`)

**Framework constraint**: No arbitrary operations allowed. Engine refuses `"nuke_city: true"`, `"infinite_money: true"`, etc.

---

## 9.3 Why Universe as Code Matters for BAC

**Universe as Code (UAC) and Brain as Code (BAC) are two halves of the same sentence.**

**Framework principle**: UAC+BAC integration is the foundation of the Townlet Framework. This pattern works for any universe instance.

### UAC: The World Half

**UAC**: The world, bodies, bars, affordances, economy, social cues, ambulance rules, etc., are **all declared in YAML**.

**They are**:
- **Diffable** (show me what changed between world v1 and v2)
- **Teachable** (instructors can point to YAML and explain "ambulance costs $300")
- **Inspectable by non-coders** (governance can read world rules without Python)

**Framework benefit**: Declarative world enables world curriculum, forensic reconstruction, and cross-universe comparison.

**Example world curriculum** (Townlet Town):
```yaml
# Early training: Cheap survival
ambulance_cost: -1.00  # $100

# Later curriculum: Expensive survival
ambulance_cost: -3.00  # $300
```

**Config diff**: `ambulance_cost: -1.00 → -3.00`

**Behavioral shift**: Agent learns to prioritize prevention (maintain health) over reactive spending (expensive ambulance).

---

### BAC: The Mind Half

**BAC**: The mind, panic thresholds, ethics vetoes, planning depth, social reasoning, module architectures, and actual cognition loop are **also declared in YAML**.

**They are**:
- **Diffable** (show me what changed between agent v1 and v2)
- **Teachable** (students can point to YAML and explain "panic triggers at 15% energy")
- **Inspectable by non-coders** (governance can read ethics rules without Python)

**Framework benefit**: Declarative mind enables curriculum, ablations, and governance.

---

### Together: Accountable Simulated Society

When you run a simulation, Townlet snapshots **both halves** into a run folder, stamps them with a **cognitive hash**, and then logs decisions per tick against that identity.

**So instead of**:
> "The AI did something weird overnight and now it's different"

**We can say**:
> "At tick 842, Mind `4f9a7c21`, in World `Nightshift_v3` with `ambulance_cost: -3.00` (normalized $300) and `bed_basic.quality: 1.0`, entered panic because `health < 0.25`.
>
> Panic escalated the action to `call_ambulance`.
>
> EthicsFilter allowed it (ambulance is legal, even if expensive).
>
> Money was deducted (`-3.00` normalized, $300 actual).
>
> Agent teleported to the nearest `hospital` affordance (special effect: `teleport`, `destination_tag: "nearest_hospital"`).
>
> See `veto_reason` in telemetry: it also tried to `STEAL` food two ticks earlier and that was blocked (`ethics_veto_applied: true`, `veto_reason: "forbidden: steal"`)."

**That is the moment where governance stops being hypothetical and becomes screenshot material.**

**Framework value**: This governance narrative works for any universe:

**Factory example**:
> "At tick 1420, Mind `7e2b9d14`, in World `Factory_Floor_v2` with `emergency_shutdown.cost: -0.50` (50% production quota loss) and `assembly_line.quality: 1.0`, entered panic because `machinery_stress >= 0.80`.
>
> Panic escalated the action to `emergency_shutdown`.
>
> EthicsFilter allowed it (shutdown is legal for safety).
>
> Production quota was deducted (`-0.50`).
>
> Machinery stress was reset to `0.0` (special effect: `safety_reset`).
>
> See telemetry: it tried to continue production two ticks earlier and that was blocked by panic (`panic_override_applied: true`, `panic_reason: "machinery_critical"`)."

**Trading example**:
> "At tick 3200, Mind `9a1c5f28`, in World `Trading_Floor_v1` with `execute_trade.cost: -0.01` (1% transaction fee) and `market_volatility: 0.45`, entered panic because `portfolio_value <= 0.70` (lost 30%).
>
> Panic escalated the action to `preserve_capital` (defensive position).
>
> EthicsFilter allowed it (capital preservation is legal).
>
> Portfolio rebalanced to defensive assets (special effect: `portfolio_action`).
>
> See telemetry: it attempted aggressive buy two ticks earlier during crash and that was blocked by panic (`panic_override_applied: true`, `panic_reason: "portfolio_critical"`)."

---

**And that's the point of Townlet**: it's not a toy black box any more. **It's an accountable simulated society with auditable minds.**

**Framework foundation**: BAC+UAC together create **Software Defined Agents in Software Defined Worlds** - fully auditable, reproducible, and governable systems for any domain.

---

**Summary**: The Townlet Framework UAC affordance system provides:

1. **Affordance Declarations** - YAML structures (id, quality, capacity, interaction_type, costs, effects_per_tick)
2. **Engine Semantics** - Reservation protocol, deterministic contention resolution, atomic effects application, interrupt handling
3. **Special Effects Whitelist** - Bounded expressiveness (teleport, heal, damage - no arbitrary operations)
4. **BAC+UAC Integration** - Declarative world + declarative mind = accountable simulated society

**Framework principle**: UAC is framework-level (works for any universe). Specific affordances (Bed vs Assembly Line) and bars (energy vs machinery_stress) are instance-specific.

**Together with BAC**, UAC transforms agents from "black box mystery" to "auditable cognitive system in auditable world."

---

---

<!-- Source: docs/architecture/hld/10-success-criteria.md -->

## 10. Success Criteria

We judge success on three axes: technical, teaching, and governance. **All three matter.** If we don't hit all three, the story breaks.

**Framework principle**: Success criteria are framework-level patterns. The specific examples demonstrate Townlet Town capabilities, but criteria apply to any universe instance (Factory, Trading, etc.).

### 10.1 Technical success

- [ ] We can launch a run from `configs/<run_name>/` and automatically create `runs/<run_name>__<timestamp>/` with a frozen `config_snapshot/` that contains:
  - `config.yaml`
  - `universe_as_code.yaml`
  - `cognitive_topology.yaml` (Layer 1)
  - `agent_architecture.yaml` (Layer 2)
  - `execution_graph.yaml` (Layer 3)

- [ ] `agent/factory.py` can reconstruct a functioning agent brain (GraphAgent) purely from that frozen `config_snapshot/`, without reading anything from live mutable config.

- [ ] `GraphAgent.think()` can tick once using only that snapshot: perception → hierarchical policy → panic_controller → EthicsFilter → `final_action`.

- [ ] Each checkpoint written under `runs/.../checkpoints/step_<N>/` includes:
  - model weights for every module (perception, world_model, social_model, hierarchical_policy, panic_controller, EthicsFilter, etc)
  - optimiser states
  - RNG state
  - a nested copy of `config_snapshot/`
  - `cognitive_hash.txt` for that checkpoint

- [ ] Resuming from a checkpoint:
  - reloads only from `runs/.../checkpoints/step_<N>/`
  - writes a new run folder `runs/<run_name>__<launch_ts>_resume_<resume_ts>/`
  - reproduces the same cognitive hash if the snapshot is unmodified

- [ ] Telemetry logs one structured row per tick into `runs/.../telemetry/`, with:
  - `run_id`
  - tick index
  - full cognitive hash
  - current_goal
  - panic state
  - candidate_action
  - panic_adjusted_action (+ panic_reason)
  - final_action
  - ethics_veto_applied (+ veto_reason)
  - planning_depth
  - social_model.enabled
  - short belief/world/social summaries

- [ ] The runtime UI ("Run Context Panel") surfaces, live:
  - run_id
  - short_cognitive_hash (pretty form of the full hash)
  - tick / planned_run_length
  - current_goal
  - panic_state
  - planning_depth (world_model.rollout_depth)
  - social_model.enabled
  - panic_override_last_tick (+ panic_reason)
  - ethics_veto_last_tick (+ veto_reason)
  - agent_claimed_reason (if introspection.publish_goal_reason is on)

**Framework outcome**: If we satisfy all of these criteria, we move from "a neural net that produces outputs" to a **reproducible mind in a governed world**.

**Alternative universe examples**:
- **Factory instance**: Same technical success criteria apply - frozen config_snapshot with factory BAC/UAC, GraphAgent.think() from snapshot, checkpoints with cognitive_hash.txt, telemetry logging production_quota decisions
- **Trading instance**: Same technical success criteria apply - frozen config_snapshot with trading BAC/UAC, checkpoints proving portfolio decisions, telemetry with market_volatility state

---

### 10.2 Pedagogical Success

**Framework goal**: The point of Townlet v2.5 is not just to make a smarter agent. It's to make a **teachable agent**. We hit pedagogical success when the system is something you can put in front of a class, and they can reason about it like a living system, not a superstition.

**Framework principle**: Pedagogical success criteria are framework-level requirements. The specific examples (STEAL action, greed parameter) are Townlet Town demonstrations, but criteria apply to any universe instance.

- [ ] **Beginner can answer ethics questions using YAML + UI only** (Townlet Town example):
  - Question: "Why didn't it steal the food?"
  - Answer using: Run Context Panel (shows `ethics_veto_last_tick` and `veto_reason`) + `cognitive_topology.yaml` (shows `compliance.forbid_actions: ["steal", ...]`)
  - **You do not need to read source code to answer an ethics/safety question.** You can answer it from YAML + UI.

**Framework pattern**: YAML-only reasoning works for any universe:
- **Factory**: "Why didn't it bypass safety check?" → cognitive_topology.yaml shows `forbid_actions: ["bypass_safety"]` + Run Context Panel shows `ethics_veto_last_tick`
- **Trading**: "Why didn't it execute insider trade?" → cognitive_topology.yaml shows `forbid_actions: ["insider_trade"]` + telemetry shows veto_reason

- [ ] **Intermediate student can perform controlled ablations via config edit** (framework capability):
  - Edit `agent_architecture.yaml` (swap GRU → LSTM in perception module, or change hidden_dim)
  - Launch new run
  - Observe memory/behavior changes
  - Explain change in terms of memory capacity, not "the AI got weird"
  - **Controlled ablations by editing config, not by rewriting thousands of lines of Torch**

**Framework pattern**: Controlled ablation works for any universe:
- **Townlet Town**: Swap GRU → LSTM → observe longer-horizon planning
- **Factory**: Increase hidden_dim in world_model → observe better production quota forecasting
- **Trading**: Change rollout_depth: 10 → 50 → observe longer-term portfolio strategy

- [ ] **Researcher can perform wiring experiments via execution_graph.yaml** (framework capability):
  - Edit `execution_graph.yaml` to bypass `world_model_service` input into policy
  - Rerun
  - Show agent becomes more impulsive / short-horizon
  - Prove change via diff in `execution_graph.yaml` plus new `cognitive_hash.txt`
  - **"Remove foresight, observe impulsivity" is now a 1-line wiring experiment, not a 2-week surgery**

**Framework pattern**: Wiring experiments work for any universe:
- **Townlet Town**: Bypass world_model → observe energy crashes (no foresight of "work costs energy")
- **Factory**: Bypass social_model → observe contention for assembly lines (no prediction of competitor actions)
- **Trading**: Bypass world_model → observe panic selling on volatility spikes (no market prediction)

- [ ] **For any interesting emergent behavior clip, we can pull the run folder and point to exact config** (framework capability):
  - Which mind (full cognitive hash)
  - Which world rules (`universe_as_code.yaml`)
  - Which panic thresholds
  - Which compliance rules (`forbid_actions`, penalties)
  - What goal the agent believed it was pursuing (`current_goal`)
  - What reason the agent claimed (`agent_claimed_reason`)

**Framework benefit**: Critical for classroom demonstrations. Instructors scrub to tick 842 and explain exact cognitive state.

**Townlet Town example**: "Agent believed it was in SURVIVAL mode, panic was active, and EthicsFilter blocked `steal`"

**Factory example**: "Agent was in EFFICIENCY mode, machinery_stress critical (panic), EthicsFilter blocked `bypass_safety_check`"

**Trading example**: "Agent was in PRESERVE mode, portfolio_value crashed (panic), EthicsFilter blocked `insider_trade`"

---

### 10.3 Governance Success

**Framework requirement**: Governance stakeholders view the system through **enforceability** rather than aesthetics. Their central question is whether the artifact can **withstand formal review**.

**Framework principle**: Governance success criteria are framework-level audit requirements. The specific examples (STEAL action, tick T) are Townlet Town demonstrations of framework audit capability.

- [ ] **We can prove to an auditor what happened at tick T in run R** (framework capability):
  - `cognitive_topology.yaml` at that tick had `forbid_actions: ["attack", "steal"]`
  - `execution_graph.yaml` at that tick still routed all candidate actions through `EthicsFilter`
  - Telemetry for tick T shows `ethics_veto_applied: true` and `veto_reason: "steal forbidden"`
  - **This allows us to state**: The agent attempted to steal at tick T, the action was blocked, and both configuration and telemetry demonstrate why.

**Framework pattern**: Tick-level proof works for any universe:
- **Townlet Town**: Prove agent attempted `steal` at tick T, EthicsFilter blocked, `forbid_actions: ["steal"]` in cognitive_topology.yaml
- **Factory**: Prove agent attempted `bypass_safety` at tick T, EthicsFilter blocked, `forbid_actions: ["bypass_safety"]` in config
- **Trading**: Prove agent attempted `insider_trade` at tick T, EthicsFilter blocked, `forbid_actions: ["insider_trade"]` in config

- [ ] **We can replay that same mind, at that same point in time, using only the checkpoint directory** (framework capability):
  - No mutable source code needed
  - No live config needed
  - Replayed agent produces **same cognitive hash** and **same cognitive wiring**
  - **This is chain-of-custody for cognition**

**Framework pattern**: Checkpoint replay works for any universe:
- **Townlet Town**: Load checkpoint from tick T, resume produces same hash, same SURVIVAL goal selection behavior
- **Factory**: Load checkpoint from tick T, resume produces same hash, same EFFICIENCY policy decisions
- **Trading**: Load checkpoint from tick T, resume produces same hash, same ACCUMULATE portfolio actions

**Operational note** (implementation detail):
To deliver that proof, pull the tick record from `runs/<run_id>/telemetry/` (each row is produced by `VectorizedPopulation.build_telemetry_snapshot` in `src/townlet/population/vectorized.py`) and pair it with the matching checkpoint hash in `runs/<run_id>/checkpoints/step_<N>/cognitive_hash.txt`. The snapshot structure comes straight from `AgentTelemetrySnapshot` (`src/townlet/population/runtime_registry.py`), so auditors know exactly which JSON fields must be present.

- [ ] **We can demonstrate lineage rules** (framework identity protocol):
  - **Same snapshot → same hash**: Resume without changing snapshot produces identical cognitive hash
  - **Edit snapshot → new hash + new run_id**: Edit anything that changes cognition (panic thresholds, greed, social_model.enabled, EthicsFilter rules, rollout_depth, etc.) → hash changes and we give it a new run_id
  - **We don't pretend it's "the same agent, just adjusted a bit"** - we enforce honest fork detection
  - **This is governance-grade identity, not research convenience**

**Framework pattern**: Lineage rules work for any universe:
- **Townlet Town**: Edit `greed: 0.5 → 0.9` in cognitive_topology.yaml → new hash, new run_id (different mind)
- **Factory**: Edit `panic_thresholds.machinery_stress: 0.8 → 0.6` → new hash, new run_id (different safety policy)
- **Trading**: Edit `rollout_depth: 10 → 50` → new hash, new run_id (different planning horizon)

---

**Summary**: The Townlet Framework success criteria establish three non-negotiable requirements:

1. **Technical Success**: Reproducible minds in governed worlds (snapshots, checkpoints, telemetry, UI)
2. **Pedagogical Success**: YAML-only reasoning and controlled ablations (no code surgery)
3. **Governance Success**: Audit-grade chain-of-custody and lineage rules (formal identity)

**Framework principle**: All three axes must be satisfied. Technical capability alone is insufficient - the system must be teachable and auditable.

**Alternative universe coverage**: Success criteria apply to any universe instance (Townlet Town, Factory, Trading) - framework-level requirements, not domain-specific.

---

---

<!-- Source: docs/architecture/hld/11-implementation-notes-ordering.md -->

## 11. Implementation Notes (Ordering)

This section is about **"what order do we do this in so we don't set ourselves on fire"**. It's the recommended build sequence for Townlet v2.5.

**Framework principle**: You do these in order. If you jump around, the audit story collapses and you'll end up duct-taping provenance on later, which never works.

**Framework requirement**: Build sequence applies to any universe instance - establish provenance foundation (snapshots, hash, checkpoints) before building universe-specific capabilities (goals, affordances, rewards).

### 11.1 Snapshot Discipline First

**Goal**: Lock down provenance from day one.

**Framework requirement**: Establish snapshot discipline before building any other components.

**Deliverables**:

- Create `configs/<run_name>/` with all 5 YAMLs:
  - `config.yaml` (runtime envelope)
  - `universe_as_code.yaml` (world rules)
  - `cognitive_topology.yaml` (BAC Layer 1 - behavioral contract)
  - `agent_architecture.yaml` (BAC Layer 2 - module implementations)
  - `execution_graph.yaml` (BAC Layer 3 - think-loop wiring)

- Write launcher so that "start run" immediately:
  - Creates `runs/<run_name>__<timestamp>/`
  - Copies 5 YAMLs byte-for-byte into `runs/<run_name>__<timestamp>/config_snapshot/`
  - Creates empty subdirs: `checkpoints/`, `telemetry/`, `logs/`

**Rules** (framework-level discipline):

- **Snapshot is a physical copy, not a symlink**
- **After launch, the live process never re-reads from `configs/<run_name>/`** - the snapshot is now truth
- **All provenance, audit, and replay logic assume the snapshot is the canonical contract** for that run

**Why this is first**:

- **Governance requirement**: If you don't freeze the world and the mind at launch, you can't prove anything later. Governance dies right here.
- **Technical dependency**: The rest of the system (factory, hashing, checkpoints) all builds on the assumption that the snapshot is the single source of truth.

**Framework pattern**: Snapshot discipline works for any universe instance:
- **Townlet Town**: Snapshot contains town-specific UAC (8×8 grid, Bed/Hospital affordances, energy/health bars, SURVIVAL goals)
- **Factory**: Snapshot contains factory-specific UAC (assembly lines, machinery_stress bars, EFFICIENCY/SAFETY goals)
- **Trading**: Snapshot contains trading-specific UAC (market feeds, portfolio_value bars, BUY/SELL/HOLD goals)

---

### 11.2 Build the Minimal GraphAgent Pipeline

**Goal**: Replace monolithic RL agent class with graph-driven brain that can think() once.

**Framework milestone**: First working "brain-from-YAML" - GraphAgent.think() ticks once using only config_snapshot.

**Deliverables** (framework components):

- `agent/factory.py`

  - Reads the run's `config_snapshot/`
  - Builds each module declared in `agent_architecture.yaml` (perception_encoder, world_model, social_model, hierarchical_policy, panic_controller, EthicsFilter, etc)
  - Wires in behavioural knobs from Layer 1 (panic_thresholds, forbid_actions, rollout_depth, social_model.enabled)
  - Verifies interface dims declared in `interfaces` (belief_distribution_dim, action_space_dim, etc)
  - Assembles a registry of modules (e.g. an `nn.ModuleDict`)

- `agent/graph_executor.py`

  - Reads `execution_graph.yaml`
  - Compiles it into a deterministic ordered step list with explicit dataflow
  - Resolves each `"@modules.*"` and `"@config.L1.*"` reference into actual callables/values
  - Knows how to run one tick: perception → policy → panic_controller → EthicsFilter → final_action
  - Produces named outputs (`final_action`, `new_recurrent_state`) and intermediate signals for telemetry

- `agent/graph_agent.py`

  - Owns the module registry and the executor
  - Stores persistent recurrent state
  - Exposes `think(raw_observation, prev_recurrent_state) -> { final_action, new_recurrent_state }`

**For the first cut** (minimal viable implementation):

- `world_model_service` can just be a stub (pass through)
- `social_model_service` can return "disabled"
- `panic_controller` can just pass through
- `EthicsFilter` can just pass through

**Why this is second**:

- **Technical dependency**: Until you have a callable brain built from YAML + snapshot, you can't hash cognition, you can't checkpoint provenance, you can't expose the think loop, you can't do glass-box UI. **Everything else depends on this.**

**Framework pattern**: Minimal GraphAgent pipeline works for any universe instance:
- **Townlet Town**: GraphAgent.think() runs perception → hierarchical_policy (SURVIVAL goal selection) → panic_controller (stub) → EthicsFilter (stub) → action
- **Factory**: GraphAgent.think() runs perception → hierarchical_policy (EFFICIENCY goal selection) → panic_controller (stub) → EthicsFilter (stub) → action
- **Trading**: GraphAgent.think() runs perception → hierarchical_policy (BUY/SELL goal selection) → panic_controller (stub) → EthicsFilter (stub) → action

---

### 11.3 Cognitive Hash

**Goal**: Give the instantiated mind a provable identity.

**Framework milestone**: Generate `cognitive_hash.txt` for every run - unique fingerprint enabling exact reproduction and accountability.

**Implementation**: Cognitive hash generator (e.g., SHA-256) must deterministically cover:

1. The exact bytes of all 5 YAMLs in the run's `config_snapshot/`, concatenated in a defined order:

   - `config.yaml`
   - `universe_as_code.yaml`
   - `cognitive_topology.yaml` (Layer 1)
   - `agent_architecture.yaml` (Layer 2)
   - `execution_graph.yaml` (Layer 3)

2. The compiled execution graph:

   - After `graph_executor` resolves bindings like `@modules.world_model` and `@config.L1.panic_thresholds`
   - After it expands the step order and knows exactly which module is called, in what sequence, with what inputs, and which veto gates get applied

3. The instantiated architectures:

   - For each module (perception_encoder, world_model, etc):

     - type (MLP, CNN, GRU, etc)
     - layer sizes / hidden dims
     - optimiser type and learning rate
     - interface dimensions (e.g. `belief_distribution_dim: 128`)

**Framework principle**: If any of those change, the hash changes. That's the whole point. **You cannot secretly "just tweak panic thresholds" and pretend it's the same mind.**

**Why we do it here** (dependency ordering):

- **Hashing requires GraphAgent** (must compute hash after instantiation)
- **Checkpoints require hash** (must stamp checkpoints with identity)
- **Telemetry requires hash** (must log `full_cognitive_hash` every tick to prove "this exact mind did this")

**Framework pattern**: Cognitive hash works for any universe instance:
- **Townlet Town**: Hash covers Townlet-specific BAC/UAC (SURVIVAL goals, Bed affordances, energy bars, greed=0.5)
- **Factory**: Hash covers factory-specific BAC/UAC (EFFICIENCY goals, assembly_line affordances, machinery_stress bars, risk_tolerance=0.3)
- **Trading**: Hash covers trading-specific BAC/UAC (BUY/SELL goals, market_data_feed affordances, portfolio_value bars, patience=0.7)

---

### 11.4 Checkpoint Writer and Resume

**Goal**: Pause/replay/fork without lying to audit.

**Framework milestone**: Enable chain-of-custody for cognition - checkpoints with snapshot + hash, resume with lineage rules.

**Deliverables**:

The checkpoint writer must emit, under `runs/<run_id>/checkpoints/step_<N>/`:

- `weights.pt`
  - all module weights from the GraphAgent (including EthicsFilter, panic_controller, etc)
- `optimizers.pt`
  - optimiser states for each trainable module
- `rng_state.json`
  - RNG state for both sim and agent
- `config_snapshot/`
  - deep copy of the snapshot as of this checkpoint (not a pointer to `configs/`)
- `cognitive_hash.txt`
  - the full hash at this checkpoint

**Resume Rules** (framework-level lineage protocol):

- **Resume never consults `configs/<run_name>/`** (only reads from checkpoint directory)
- **Resume loads only from checkpoint directory** (self-contained provenance)
- **Resume starts new run folder** `..._resume_<timestamp>/` with restored snapshot
- **Same snapshot → same hash**: If you haven't touched the snapshot, resumed brain produces identical cognitive hash

**Branching** (honest fork detection):

- **Edit snapshot → new hash + new run_id**: If you edit snapshot before resuming (change `panic_thresholds`, disable `social_model.enabled`, lower `greed`, change `rollout_depth`), that is a **fork**. New hash, new run_id. **We do not lie about continuity.**

**Framework benefits**:

- **Long training jobs** across interruptions (resume with same hash)
- **Honest ablations** ("same weights, same world, except panic disabled" = provable via hash diff)
- **True chain-of-custody** for behavior (checkpoint directory = complete evidence)

**Framework pattern**: Checkpoint/resume works for any universe instance:
- **Townlet Town**: Checkpoint → resume with same SURVIVAL policy if snapshot unchanged, new hash if greed edited
- **Factory**: Checkpoint → resume with same EFFICIENCY policy if snapshot unchanged, new hash if risk_tolerance edited
- **Trading**: Checkpoint → resume with same BUY/SELL policy if snapshot unchanged, new hash if patience edited

---

### 11.5 Telemetry and UI

**Goal**: Make cognition observable in real-time and scrubbable after the fact.

**Framework milestone**: Glass-box capability - expose internal cognitive processes for governance, teaching, and debugging.

**Two Deliverables** (framework observability components):

1. Telemetry writer

   - For every tick, write a structured record to `runs/.../telemetry/` with:

     - `run_id`
     - `tick_index`
     - `full_cognitive_hash`
     - `current_goal` (engine truth)
     - `agent_claimed_reason` (if enabled)
     - `panic_state`
     - `candidate_action`
     - `panic_adjusted_action` (+ `panic_reason`)
     - `final_action`
     - `ethics_veto_applied` (+ `veto_reason`)
     - short summaries of belief uncertainty, world model expectation, social inference
     - planning_depth
     - social_model.enabled

2. Live Run Context Panel

   - Show at runtime:

     - `run_id`
     - short_cognitive_hash (shortened hash)
     - tick / planned_run_length
     - current_goal
     - panic_state
     - planning_depth
     - social_model.enabled
     - panic_override_last_tick (+ panic_reason)
     - ethics_veto_last_tick (+ veto_reason)
     - agent_claimed_reason (if introspection.publish_goal_reason is true)

**Framework benefit**: At this stage the panel provides an **auditable narrative** - instructors can point to exact cognitive state and narrate decisions.

**Townlet Town example**: "Agent is in SURVIVAL, panic overruled the planner, EthicsFilter blocked `steal`, planning depth is six ticks, and agent claims 'I'm going to work for money.'"

**Factory example**: "Agent is in EFFICIENCY, machinery_stress critical, panic escalated to `emergency_shutdown`, EthicsFilter allowed (safety action legal), production quota dropped."

**Trading example**: "Agent is in PRESERVE, portfolio_value crashed, panic blocked aggressive `buy_dip` action, substituted defensive `hold_cash`, agent claims 'Buying opportunity.'"

---

### 11.6 Panic and Ethics For Real

**Goal**: Safety and survival must be enforced in-graph rather than remaining comments in YAML.

**Framework milestone**: Replace stub panic_controller and EthicsFilter with real implementations - safety becomes observable, auditable, and provable.

**Implementation** (replace stubs):

- `panic_controller`:

  - Reads `panic_thresholds` from Layer 1 (e.g. energy < 0.15)
  - Can override `candidate_action` with an emergency survival action (`call_ambulance`, `go_to_bed_now`, etc)
  - Emits `panic_override_applied` and `panic_reason`
  - Logged to telemetry and surfaced in the UI

- `EthicsFilter`:

  - Reads `forbid_actions` and `penalize_actions` from Layer 1 compliance
  - Blocks forbidden actions outright, substitutes something allowed, and emits `ethics_veto_applied` + `veto_reason`
  - Logged to telemetry and surfaced in UI

**Important** (framework-level veto hierarchy): **EthicsFilter is final.** Panic can escalate urgency, but panic cannot legalize a forbidden act. If panic tries `steal` as an emergency move, EthicsFilter still vetoes it. **Ethics wins.**

**By the end of this step**:

- **Panic is an explicit, logged controller** in the loop
- **Ethics is an explicit, logged controller** in the loop
- **Clean override chain**: hierarchical_policy → panic_controller → EthicsFilter → final_action

**Framework benefit**: At this point we can **brief governance stakeholders using the recorded override trace** rather than informal assurances.

**Framework pattern**: Panic and ethics enforcement works for any universe instance:
- **Townlet Town**: Panic escalates to `call_ambulance` when health critical, EthicsFilter still blocks `steal` even if desperate
- **Factory**: Panic escalates to `emergency_shutdown` when machinery_stress critical, EthicsFilter still blocks `bypass_safety_check` even if production quota failing
- **Trading**: Panic escalates to `preserve_capital` when portfolio_value crashed, EthicsFilter still blocks `insider_trade` even if losses mounting

**Summary**: The six-step build sequence establishes provenance foundation (snapshots → GraphAgent → hash → checkpoints) before adding capabilities (telemetry/UI → panic/ethics). **Order matters** - duct-taping provenance on later never works.

---

---

<!-- Source: docs/architecture/hld/12-implementation-order-milestones.md -->

## 12. Implementation Order (Milestones)

**Framework principle**: Section 11 outlined the conceptual order of operations. Section 12 translates that ordering into **concrete delivery milestones** for engineering, curriculum, safety, and audit teams. These steps form the boot sequence.

**Framework requirement**: Milestones apply to any universe instance - establish provenance infrastructure (snapshots, hash, checkpoints) before building universe-specific features (goals, affordances, rewards).

### 12.1 Milestone: Snapshots and Run Folders

**Framework milestone**: Establish snapshot discipline - freeze config at launch for provenance.

**Definition of Done**:

- [ ] `configs/<run_name>/` exists with all 5 YAMLs (config.yaml, universe_as_code.yaml, cognitive_topology.yaml, agent_architecture.yaml, execution_graph.yaml)
- [ ] Launching a run generates `runs/<run_name>__<timestamp>/`
- [ ] `runs/<run_name>__<timestamp>/config_snapshot/` is a byte-for-byte copy of those YAMLs
- [ ] `checkpoints/`, `telemetry/`, `logs/` directories are created
- [ ] Runtime never re-reads mutable config after snapshot (enforced in code)

**Why It Matters**:

- **Hard provenance from the first tick** - governance foundation established
- **Snapshot is evidence**: We can point to "this is the world and brain we actually ran", not "what we think is close"

**Framework pattern**: Snapshot milestone works for any universe instance:
- **Townlet Town**: Snapshot contains town-specific BAC/UAC (SURVIVAL goals, Bed affordances)
- **Factory**: Snapshot contains factory-specific BAC/UAC (EFFICIENCY goals, assembly_line affordances)
- **Trading**: Snapshot contains trading-specific BAC/UAC (BUY/SELL goals, market_data_feed affordances)

### 12.2 Milestone: Minimal GraphAgent Pipeline

**Framework milestone**: First working "brain-from-YAML" - GraphAgent.think() ticks once.

**Definition of Done**:

- [ ] `factory.py` can build all declared modules from the snapshot
- [ ] `graph_executor.py` can compile `execution_graph.yaml` into a callable loop
- [ ] `graph_agent.py` exposes `think(raw_observation, prev_recurrent_state) -> { final_action, new_recurrent_state }`
- [ ] We can tick once end-to-end with stub panic_controller and stub EthicsFilter

**Why It Matters**:

- **"Brain is data" becomes running code** - not a slogan, actual execution
- **Proves BAC works**: Declarative mind configuration successfully materializes into callable agent

**Framework pattern**: Minimal GraphAgent works for any universe instance:
- **Townlet Town**: GraphAgent.think() runs SURVIVAL goal selection → stub panic → stub ethics → movement action
- **Factory**: GraphAgent.think() runs EFFICIENCY goal selection → stub panic → stub ethics → assembly_line action
- **Trading**: GraphAgent.think() runs BUY/SELL goal selection → stub panic → stub ethics → market action

### 12.3 Milestone: Cognitive Hash

**Framework milestone**: Generate provable identity for every mind - unique fingerprint enabling exact reproduction.

**Definition of Done**:

- [ ] We can generate `cognitive_hash.txt` for a run
- [ ] The hash covers:
  - All 5 YAMLs from snapshot
  - Compiled execution graph wiring
  - Instantiated module architectures / dims / optimizer LRs
- [ ] Telemetry and checkpoints now both include that hash

**Why It Matters**:

- **Mind identity for audit**: Provable fingerprint you can take to governance stakeholders
- **Honest mutation detection**: You can't quietly mutate cognition without changing the hash

**Framework pattern**: Cognitive hash works for any universe instance:
- **Townlet Town**: Hash changes if SURVIVAL termination threshold edited, or greed parameter changed
- **Factory**: Hash changes if EFFICIENCY goal modified, or machinery_stress panic threshold edited
- **Trading**: Hash changes if BUY/SELL logic altered, or portfolio_value risk threshold edited

### 12.4 Milestone: Checkpoint Writer and Resume

**Framework milestone**: Enable chain-of-custody for cognition - checkpoints with snapshot + hash, resume with lineage rules.

**Definition of Done**:

- [ ] We can dump checkpoints at `step_<N>/` with:
  - weights.pt (all module weights)
  - optimizers.pt (optimizer states)
  - rng_state.json (reproducible RNG)
  - config_snapshot/ (frozen world + mind)
  - cognitive_hash.txt (identity fingerprint)
- [ ] We can resume into a brand new run folder using only a checkpoint subfolder
- [ ] **Same snapshot → same hash**: If we don't change the snapshot on resume, the resumed run reports the same cognitive hash
- [ ] **Edit snapshot → new hash + new run_id**: If we edit the snapshot before resume (panic thresholds, forbid_actions, greed, rollout_depth), the resumed run reports a new hash and a new run_id

**Why It Matters**:

- **Chain-of-custody for cognition**: Provenance trail from launch through checkpoints to resume
- **Honest fork detection**: Controlled forks are now explicit, not sneaky (lineage rules enforced)

**Framework pattern**: Checkpoint/resume works for any universe instance:
- **Townlet Town**: Resume with same hash if unchanged, new hash if greed edited (0.5 → 0.9)
- **Factory**: Resume with same hash if unchanged, new hash if machinery_stress panic threshold edited
- **Trading**: Resume with same hash if unchanged, new hash if rollout_depth edited (10 → 50 steps)

### 12.5 Milestone: Telemetry and UI

**Framework milestone**: Glass-box capability - expose internal cognitive processes for governance, teaching, and debugging.

**Definition of Done**:

- [ ] **Telemetry per tick logs**:
  - run_id, tick_index, full_cognitive_hash
  - current_goal (engine truth)
  - agent_claimed_reason (self-report, if enabled)
  - panic_state
  - candidate_action, panic_adjusted_action (+ panic_reason)
  - final_action
  - ethics_veto_applied (+ veto_reason)
  - planning_depth, social_model.enabled
  - Short summaries of internal beliefs/expectations

- [ ] **The Run Context Panel renders live**:
  - run_id, short_cognitive_hash (pretty form)
  - tick / planned_run_length
  - current_goal, panic_state
  - planning_depth, social_model.enabled
  - panic_override_last_tick (+ panic_reason)
  - ethics_veto_last_tick (+ veto_reason)
  - agent_claimed_reason (if introspection.publish_goal_reason)

**Why It Matters**:

- **Teaching becomes possible**: Students can reason about behavior using observable cognition, not superstition
- **Governance reviews become visual**: Auditors see override traces in UI, not adversarial speculation

**Framework pattern**: Telemetry/UI works for any universe instance:
- **Townlet Town**: UI shows "SURVIVAL goal, panic=true (health critical), ethics blocked STEAL"
- **Factory**: UI shows "EFFICIENCY goal, panic=true (machinery critical), ethics blocked BYPASS_SAFETY"
- **Trading**: UI shows "PRESERVE goal, panic=true (portfolio crashed), ethics blocked INSIDER_TRADE"

### 12.6 Milestone: Panic and Ethics Go Live

**Framework milestone**: Safety and survival become observable, auditable, and provable - replace stubs with real enforcement.

**Definition of Done**:

- [ ] `panic_controller` actually overrides `candidate_action` when bars cross panic_thresholds
- [ ] `EthicsFilter` actually vetoes forbidden actions and substitutes a safe fallback
- [ ] Both write structured reasons (`panic_reason`, `veto_reason`) into telemetry and show in UI
- [ ] Both steps are present and ordered in `execution_graph.yaml`: policy → panic_controller → EthicsFilter
- [ ] **EthicsFilter is final authority** (panic cannot legalize forbidden acts)

**Why It Matters**:

- **Safety becomes observable**: Survival urgency and ethical constraint are now explicit, inspectable modules in the think loop (not implicit reward-shaping heuristics)
- **Auditable trace**: You can show "panic tried X, ethics said no" as provable evidence with cognitive hash

**Framework pattern**: Panic and ethics enforcement works for any universe instance:
- **Townlet Town**: Panic escalates to CALL_AMBULANCE (health critical), EthicsFilter still blocks STEAL (even if desperate)
- **Factory**: Panic escalates to EMERGENCY_SHUTDOWN (machinery critical), EthicsFilter still blocks BYPASS_SAFETY (even if production failing)
- **Trading**: Panic escalates to PRESERVE_CAPITAL (portfolio crashed), EthicsFilter still blocks INSIDER_TRADE (even if losses mounting)

---

**Summary**: The six milestones establish provenance infrastructure (snapshots → GraphAgent → hash → checkpoints) before adding capabilities (telemetry/UI → panic/ethics). **Each milestone must be demonstrable** - no partial implementations.

**Framework principle**: Milestones apply to any universe instance. The specific examples (SURVIVAL goal, Bed affordance, STEAL action) are Townlet Town demonstrations of framework-level delivery checkpoints.

---

---

<!-- Source: docs/architecture/hld/frontend-visualization.md -->

## Frontend Visualization Architecture (HLD)

**Date**: 2025-11-06
**Status**: Implemented (TASK-002A Phase 7)
**Version**: 2.0 (Multi-Substrate Support)

---

### Overview

The HAMLET frontend provides real-time visualization of agent behavior via WebSocket. It supports **two rendering modes** based on substrate type: **Spatial** (Grid2D) and **Aspatial**.

**Technology Stack**:
- Vue 3 (Composition API)
- Pinia (state management)
- SVG (spatial rendering)
- WebSocket (real-time communication)

---

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Backend (Python)                        │
│                                                             │
│  VectorizedHamletEnv ──→ LiveInferenceServer ──→ WebSocket │
│          │                      │                           │
│          │                      │                           │
│       Substrate              Substrate                      │
│       Metadata               Serialization                  │
└─────────────────────────────────────────────────────────────┘
                               │
                               │ WebSocket
                               │ (JSON messages)
                               ↓
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3)                         │
│                                                             │
│  WebSocket ──→ Simulation Store ──→ App.vue                │
│                  (Pinia)                 │                  │
│                     │                    │                  │
│                     │          ┌─────────┴─────────┐        │
│                     │          │                   │        │
│                     ↓          ↓                   ↓        │
│                Grid.vue    AspatialView.vue   Other         │
│                  (SVG)       (Dashboard)      Components    │
└─────────────────────────────────────────────────────────────┘
```

---

### Rendering Pipeline

#### 1. WebSocket Message Receipt

**Message Types**:
- `connected`: Initial handshake, substrate metadata
- `episode_start`: New episode, reset state
- `state_update`: Step update, agent/affordance positions, meters

**Substrate Metadata** (in all messages):
```json
{
  "substrate": {
    "type": "grid2d",
    "position_dim": 2,
    "width": 8,
    "height": 8,
    "topology": "square"
  }
}
```

---

#### 2. State Storage (Pinia)

**Store** (`simulation.js`):
```javascript
const substrateType = ref('grid2d')
const substrateMetadata = ref({...})
const gridWidth = ref(8)
const gridHeight = ref(8)
const agents = ref([...])
const affordances = ref([...])
const agentMeters = ref({...})
```

**Update Flow**:
```
WebSocket message → Parse JSON → Update refs → Trigger Vue reactivity
```

---

#### 3. Component Rendering

**Dispatcher** (`App.vue`):
```vue
<Grid v-if="substrateType === 'grid2d'" ... />
<AspatialView v-else-if="substrateType === 'aspatial'" ... />
```

**Props Flow**:
```
Store (reactive refs) → App.vue (pass as props) → Child component (render)
```

---

### Spatial Mode (Grid2D)

**Component**: `Grid.vue`

**Rendering Strategy**: SVG-based 2D grid

**Data Requirements**:
- Agent positions: `[{id, x, y, color}]`
- Affordance positions: `[{type, x, y}]`
- Grid dimensions: `width, height`

**Visual Elements**:
1. **Grid cells** (background): `<rect>` for each (x, y)
2. **Heat map** (optional): Colored overlay for position visit frequency
3. **Affordances**: Icons at affordance positions
4. **Agent trails**: Last 3 positions with fading opacity
5. **Agents**: Circles at current position with pulse animation

**Performance**:
- ~100 SVG elements (8×8 grid + agents + affordances)
- Hardware-accelerated rendering
- 60 FPS at 50 steps/sec

---

### Aspatial Mode

**Component**: `AspatialView.vue`

**Rendering Strategy**: HTML dashboard (no SVG)

**Data Requirements**:
- Agent meters: `{energy: 0.8, health: 0.5, ...}`
- Affordances: `[{type: "Bed"}, {type: "Job"}]` (no positions)
- Last action: `4` (INTERACT)

**Visual Elements**:
1. **Large meter bars**: Color-coded by value (critical/warning/healthy)
2. **Affordance list**: Cards showing available interactions
3. **Action history**: Log of recent actions (last 10)

**Layout** (responsive):
- **Mobile**: Single column (meters → affordances → history)
- **Tablet+**: Two columns (meters left, affordances/history right)

**Performance**:
- ~20 HTML elements (8 meters + affordance cards)
- Simpler than spatial mode (no SVG complexity)
- Better performance on low-end devices

---


### Feature Matrix

| Feature | Spatial (Grid2D) | Aspatial |
|---------|------------------|----------|
| Grid cells | ✅ Yes | ❌ No |
| Agent positions | ✅ (x, y) | ❌ No concept |
| Affordance positions | ✅ (x, y) | ❌ No concept |
| Meter bars | ✅ Small panel | ✅ Large display |
| Heat map | ✅ Position visits | ❌ Spatial feature |
| Agent trails | ✅ Last 3 positions | ❌ Spatial feature |
| Affordance list | ❌ Not needed | ✅ Card layout |
| Action history | ❌ Not shown | ✅ Text log |
| Novelty heatmap | ✅ RND exploration | ❌ Spatial feature |

---

### Testing Strategy

#### Unit Tests

**Grid.vue**:
- Renders correct number of grid cells
- Positions agents correctly at (x, y)
- Handles missing heat map gracefully

**AspatialView.vue**:
- Renders all meters with correct values
- Color-codes meters by threshold (critical/warning/healthy)
- Updates action history on new actions

**Simulation Store**:
- Stores substrate metadata from WebSocket
- Falls back to spatial mode if substrate missing
- Passes substrate to components via props

---

#### Integration Tests

**End-to-End Spatial**:
1. Start Grid2D inference server
2. Connect frontend
3. Verify SVG grid renders
4. Verify agents move on grid

**End-to-End Aspatial**:
1. Start Aspatial inference server
2. Connect frontend
3. Verify dashboard renders (no grid)
4. Verify meters update in real-time


---

### Future Enhancements

**Possible Extensions** (out of scope for Phase 7):

1. **3D Grid Substrates**: WebGL/Three.js renderer for 3×3×3 grids
2. **Graph Substrates**: D3.js force-directed graph for node-based universes
3. **Multi-Agent Visualization**: Color-coded agents with ID labels
4. **Affordance Operating Hours**: Show open/closed status in UI
5. **Interaction Progress Ring**: Animated ring for multi-tick interactions (already implemented for spatial)

---

### Maintenance Notes

**Adding New Substrate Types**:

1. Add substrate type to backend (`SpatialSubstrate` subclass)
2. Update WebSocket protocol to include substrate metadata
3. Create new Vue component for rendering (e.g., `Graph3DView.vue`)
4. Add dispatcher case in `App.vue`:
   ```vue
   <NewView v-else-if="substrateType === 'newtype'" ... />
   ```

**Modifying Affordance Icons**:

Edit `frontend/src/utils/constants.js`:
```javascript
export const AFFORDANCE_ICONS = {
  NewAffordance: '🆕',  // Add new icon here
}
```

**Changing Meter Colors**:

Edit `frontend/src/components/AspatialView.vue`:
```javascript
function getMeterClass(name, value) {
  if (value < 0.1) return 'meter-critical'  // Adjust threshold
  if (value < 0.4) return 'meter-warning'
  return 'meter-healthy'
}
```

---

### References

- **TASK-002A**: Substrate abstraction implementation
- **PDR-002**: No-defaults principle (explicit substrate config)
- **Vue 3 Docs**: https://vuejs.org/guide/introduction.html
- **Pinia Docs**: https://pinia.vuejs.org/
