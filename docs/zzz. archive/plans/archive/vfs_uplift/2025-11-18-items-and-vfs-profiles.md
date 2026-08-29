# Items & VFS Profiles – Implementation Plan (Config v2.1)

**Status:** Draft
**Owner:** Config / Environment / VFS
**Related:** `vfs/schema.py`, `environment/vectorized_env.py`, `universe/compiler.py`, `configs/reference_config/reference-config-v2.1-complete.yaml`, `configs/reference_config/VARIABLE_SUBSYSTEM.md`, `docs/vfs-integration-guide.md`

---

## 0. Preconditions

Before starting this work, the following should be true:

- The codebase is green: all existing tests pass (including action space / metadata tests in `tests/test_townlet/unit/environment/test_action_space.py`).
- Legacy config paths are removed and all runtime flows use the v2.1 configuration system (no v1 adapters, no hamletconfig).
- Remaining behavioral defaults that violate the no-defaults principle (e.g., loss and replay PER knobs) are either removed or surfaced as explicit config requirements.
- The current VFS implementation is stable and documented as Phase 1 (static variables only), with VARIABLE_SUBSYSTEM.md and `docs/vfs-integration-guide.md` reflecting that expressions are *design targets*, not yet executable.

These preconditions reduce the risk that items/VFS extensions interact with unstable behaviour or legacy code paths.

---

## 1. Goals & Non‑Goals

### 1.1 Goals

- Introduce **Items** as first‑class, fully declarative entities in the v2.1 config stack:
  - Spawned in the world (random / fixed) with schedules, cooldowns, counts, priorities, and conditions.
  - Can be held by agents (inventory) and interacted with (pickup/use/drop, custom verbs).
  - Can affect bars, VFS, cascades, affordances, and environment state when interacted with.
  - Have visual metadata (emoji/icon, labels, tags).
- Generalize the **VFS** from “one global state” to **VFS profiles**:
  - Global VFS profiles (world‑level).
  - Agent VFS profiles (per‑agent copies of a shared profile catalog).
  - Item VFS profiles (per‑item copies of shared profiles).
- Extend **DynObs / observation building** to include:
  - Global VFS fields.
  - Agent VFS fields.
  - VFS fields for items an agent holds (and potentially nearby items).
- Keep all behavior **config‑driven**:
  - No new implicit defaults for behavioral knobs (spawn rates, limits, effects).
  - Clear config errors at compile time where possible.

### 1.2 Non‑Goals (for this plan)

- No changes to model architectures, training hyperparameters, or PER.
- No visual UI / frontend design for items (only metadata hooks).
- No new physics/simulation systems beyond what’s needed to track items and their VFS state.

---

## 2. Conceptual Model

### 2.1 Global vs Object State

- **Global State**
  - Global bars (e.g., time of day, weather).
  - Global VFS profiles (e.g., `is_night`, `lighting_level`, `ambient_noise`).
  - Global affordances (doors, hazards) and “environment” objects.
  - Global items (placed in the world; many may later be better expressed as affordances, and should generally only be used for single‑shot, affordance‑like events such as a Pac‑Man fruit).

- **Object State = Collection of VFS Profiles**
  - Each entity (global, agent, item) has a collection of VFS profiles.
  - Each **VFS profile** defines one logical variable or function, including:
    - Its update rule (dependencies on bars, other VFS profiles, affordances, configuration).
    - Its observation mapping (shape, exposure, masking).
  - Profiles are grouped by **scope**:
    - `global` – shared by all agents & items.
    - `agent` – replicated per agent (same schema, different value per agent).
    - `item` – replicated per item instance (same schema, different value per item).

### 2.2 Items

Items are:

- Placeable objects:
  - At fixed coordinates or random positions under constraints.
  - With timing: start times, durations, cooldowns, max concurrent / total instances.
  - With conditions: only spawn if certain VFS predicates or item/affordance conditions hold.
- Holdable by agents:
  - Agents maintain an inventory of item instances.
  - Items can be exclusive (single holder) or shared (e.g., environmental objects treated as “items”).
- Behaviour carriers:
  - Each item type is associated with one or more **item VFS profiles**.
  - Interactions (pick up, use, drop) reference VFS profiles to define their effects:
    - On bars (energy, mood, etc.).
    - On agent VFS (e.g., `is_carrying_heavy_load`).
    - On item VFS (e.g., durability, charges).
    - On global VFS (e.g., `global_noise_level`).
    - On affordances (e.g., unlocking doors).

---

## 3. Config Surface – New Files & Sections

**Observation-shape vs masking rule**

- If a setting can change the **shape** of the observation vector (`obs_dim`), it must live at the **experiment level** (shared across all curriculum levels).
  - Examples: adding/removing item types that introduce new VFS profiles with observations, changing substrate type, changing meter vocabulary.
- If a setting only changes **values or masking** (which slots are active vs inactive) without changing `obs_dim`, it should live at the **curriculum/level level**.
  - Examples: enabling/disabling items via spawn rules, turning specific fields on/off via curriculum masks, per-level inventory limits.

The items/VFS configuration below follows this rule: catalogs and profile definitions are experiment-level; appearance, spawn, and masking are level/curriculum-level.

### 3.1 New Config Files

1. **`items.yaml` (experiment‑scoped catalog)**
   Location (shared across all curriculum levels):
   - `configs/<experiment>/items.yaml`

   Purpose:
   - Declare global item *types* (the catalog) and their VFS bindings.
   - Define intrinsic properties and interactions that are the same across levels.
   - This file does **not** control whether or where items appear; it only defines what items *are*.

2. **`items.yaml` (level‑scoped appearance)**
   Location (per curriculum level / level directory):
   - `configs/<experiment>/levels/<level_name>/items.yaml`

   Purpose:
   - Declare item *appearance state* for that level:
     - Inventory configuration (e.g., `max_items_per_agent`).
     - Spawn rules, lifecycle constraints, conditions, and priorities.
   - References item types by ID from the experiment‑level catalog.

3. **`vfs_profiles.yaml` (experiment‑scoped)**
   Location (shared across levels):
   - `configs/<experiment>/vfs_profiles.yaml`

   Purpose:
   - Declare reusable VFS profile definitions (global/agent/item).
   - Each profile specifies its dependencies, update rule, and observation wiring.

> NOTE: If we want a single entry point, we can embed `vfs_profiles` into `environment.yaml`. This plan assumes a separate file for clarity, but is compatible with a merged design.

### 3.2 `items.yaml` Schemas (Conceptual)

We split items configuration into:
- An experiment‑level **catalog** of item types.
- Per‑level **appearance state** describing which items appear and how.

**1. Experiment‑level catalog (`configs/<experiment>/items.yaml`)**

```yaml
# Global item catalog (shared across all curriculum levels)
items:
  version: "1.0"

  item_types:
    - id: umbrella
      name: "Umbrella"
      icon: "☂️"
      tags: ["weather", "protection"]
      vfs_profiles: ["item_wetness_resistance"]   # references into vfs_profiles.yaml
      interactions:
        pickup:
          effects: [...]   # bars/VFS/affordances/environment references
        use:
          effects: [...]
        drop:
          effects: [...]
        # Optional item-scoped custom commands:
        # - local_commands: Commands available when the item is present in the agent's local space
        #   (e.g., on the same tile or within interaction radius in continuous substrates).
        # - inventory_commands: Commands available only while the item is held in the agent's wallet.
        #
        # Example:
        #   local_commands:
        #     - name: OPEN_UMBRELLA
        #       description: "Open umbrella when standing next to it"
        #       effects: { ... }
        #   inventory_commands:
        #     - name: USE_UMBRELLA
        #       description: "Use umbrella while holding it"
        #       effects: { ... }
```

**2. Level‑scoped appearance (`configs/<experiment>/levels/<level_name>/items.yaml`)**

```yaml
# Per-level appearance state (curriculum-level control)
items:
  version: "1.0"

  inventory:
    max_items_per_agent: 3   # REQUIRED: explicit inventory capacity (no implicit caps)

  spawn_rules:
    - type_id: umbrella       # refers to catalog entry
      placement:
        mode: "random"        # random | fixed | grid | scripted
        positions: []         # required for fixed/scripted
      schedule:
        kind: "time_window"   # time_window | poisson | normal | once
        params: {...}
      limits:
        max_simultaneous: 3
        max_total: 10
      lifecycle:
        duration_steps: 50
        cooldown_steps: 20
      priority: 10
      conditions:
        - when: "vfs:is_raining"  # reference into global VFS
          equals: true
```

Key ideas:

- **Experiment‑level `items.yaml`** defines the **item catalog**:
  - `item_types` describe intrinsic properties, interactions, VFS bindings, and item‑scoped commands.
  - This catalog is shared by all curriculum levels.
- **Level‑scoped `items.yaml`** defines **appearance state**:
  - `spawn_rules` describe *instances* behaviour at the level (where, when, how many).
  - `inventory.max_items_per_agent` defines a hard cap on how many items each agent can hold; environment must enforce this (no implicit inventory limits).
- Items may also declare **item-scoped custom commands** via `interactions.local_commands` and `interactions.inventory_commands`:
  - Local commands are included in the global action vocabulary but are only enabled/masked when the agent is in range of a dropped item.
  - Inventory commands are only enabled/masked for agents currently holding that item in their wallet.
  - These commands are derived from item metadata, not manually defined in `actions.yaml`.
- No defaults for behavioral numbers (duration, cooldown, max counts, priorities).

### 3.3 `vfs_profiles.yaml` Schema (Conceptual)

Top‑level:

```yaml
vfs_profiles:
  version: "1.0"

  global:
    - id: is_night
      expression: "time_of_day >= 20 || time_of_day < 6"   # FUTURE: expression DSL (BAC Phase 2+)
      deps:
        bars: ["time"]
        vfs: []
      observation:
        exposed_to: ["agent"]
        shape: []
        semantic_type: "temporal"

  agent:
    - id: is_heavily_loaded
      expression: "inventory_weight > 0.8"                  # FUTURE: expression DSL (BAC Phase 2+)
      deps:
        vfs: ["inventory_weight"]
      observation:
        exposed_to: ["agent"]
        shape: []
        semantic_type: "custom"

  item:
    - id: durability
      initial_value: 1.0
      update_on:
        interaction: "durability - 0.1"                     # FUTURE: expression DSL (BAC Phase 2+)
      observation:
        exposed_to: ["agent"]
        shape: []
        semantic_type: "custom"
```

Key ideas:

- Profiles are grouped by **scope**: `global`, `agent`, `item`.
- Each profile defines:
  - **ID**: stable across experiment.
  - **Dependencies**: bars, other VFS, possibly affordances.
  - **Update rule**: expressed via a DSL (see VARIABLE_SUBSYSTEM.md) and compiled by BAC in a future phase; in early phases, these fields are treated as design-time metadata only.
  - **Observation mapping**: shape, semantic type, exposure.
- This should align structurally with `src/townlet/vfs/schema.py` but add scoping and profile IDs.

---

## 4. DTO & Compiler Changes

### 4.1 New DTOs

Add DTO modules under `src/townlet/config/`:

1. `items_config.py`
   - `InventoryConfig` (e.g., `max_items_per_agent`)
   - `ItemInteractionEffectConfig`
   - `ItemTypeConfig`
   - `ItemSpawnPlacementConfig`
   - `ItemSpawnScheduleConfig`
   - `ItemSpawnLimitsConfig`
   - `ItemSpawnConditionConfig`
   - `ItemSpawnRuleConfig`
   - `ItemsConfig` (root)

2. `vfs_profiles_config.py`
   - `VFSProfileObservationConfig`
   - `VFSProfileDepsConfig`
   - `VFSProfileConfig` (common base)
   - `GlobalVFSProfileConfig`
   - `AgentVFSProfileConfig`
   - `ItemVFSProfileConfig`
   - `VFSProfilesConfig` (root with `global`, `agent`, `item` lists)

All DTOs:

- Use `ConfigDict(extra="forbid")`.
- Enforce “no defaults” for behavioral values (durations, limits, schedule parameters).
- Use validators to enforce:
  - Non‑empty `deps` where required.
  - Valid ranges (e.g., probabilities ∈ (0, 1]).
  - That references (`vfs_profiles` on items, `when` conditions) actually point to existing profile IDs.

### 4.2 UniverseCompiler Integration

Update `src/townlet/universe/compiler.py`:

1. **New load stages**
   - When building `RawConfigsV21`:
     - Load `VFSProfilesConfig` once per experiment (from `vfs_profiles.yaml`).
     - Load the experiment‑level item catalog (`ItemsCatalogConfig`) from `items.yaml`.
     - For each level:
       - Load level‑scoped `ItemsConfig` from `levels/<level>/items.yaml` (appearance state: inventory + spawn rules).
       - Validate that all `spawn_rules.type_id` entries reference known catalog item IDs.

2. **CompiledUniverse extensions**
   - Update `src/townlet/universe/compiled.py`:
     - New fields on `CompiledUniverse`:
       - `vfs_profile_catalog`: structured collection of global/agent/item profile definitions.
       - `item_catalog`: map of `item_type_id -> CompiledItemType` (from experiment-level `items.yaml`).
       - `item_spawn_plans`: per level, list of compiled spawn rules (from level-scoped `items.yaml`).
     - Ensure all new fields are included in hashing / provenance where appropriate.

3. **Validation & errors**
   - Compiler should fail fast with clear errors when:
     - `items.yaml` references unknown `vfs_profiles` IDs.
     - `vfs_profiles.yaml` missing required fields or has invalid dependencies.
     - Spawn rules reference unknown `item_type_id`s.
   - Use the existing `format_validation_error` helpers to keep error messages consistent.

---

## 5. Runtime / Environment Changes

### 5.1 Item Runtime Model

Add item modeling to `src/townlet/environment/vectorized_env.py` and/or a dedicated module:

- **ItemInstance** (internal dataclass/struct)
  - `id: int`
  - `type_id: str`
  - `position` (grid/continuous/aspatial representation)
  - `holder_agent_id: int | None`
  - `spawn_step: int`
  - `expire_step: int | None`
  - `cooldown_until_step: int | None`
  - Link to item VFS state indices in the global state tensors.

- **ItemManager**
  - Maintains:
    - Pool of `ItemInstance`s.
    - Spawn scheduler (per `item_spawn_plans`).
    - Cooldown & lifetime enforcement.
  - Exposes methods:
    - `step(global_state, agent_states, vfs_state, rng)`
    - `pickup(agent_id, item_id)`
    - `drop(agent_id, item_id)`
    - `use(agent_id, item_id)`

### 5.2 Inventory Integration

Extend agent state in `VectorizedHamletEnv`:

- Read `max_items_per_agent` from config (e.g., `ItemsConfig.inventory`) and treat it as the hard cap on inventory size for all agents in that level.
- Add a per‑agent **wallet** structure when `max_items_per_agent > 0`:
  - A fixed‑size array of item instance IDs per agent (backed by a mask when slots are empty).
  - Alternatively, a ragged structure internal to ItemManager plus a view for observation building.

- Update environment:
  - On interaction with an item:
    - Modify bars / VFS via configured `effects`.
    - Modify item VFS profiles (e.g., decrement durability).
    - Enforce `max_items_per_agent` on pickup; attempts to exceed the cap must either be disallowed or follow an explicit, config‑driven replacement policy (no silent overflows).
    - Respect max stacks / exclusivity rules (if introduced later).
  - When `max_items_per_agent > 0`, the action vocabulary must always include **GET** and **DROP** commands:
    - These are **automatically generated core actions**, analogous to directional movement commands.
    - They are not optional custom actions; the compiler/runtime should derive and inject them whenever items are enabled (items > 0).
    - When no items are present for a level (`max_items_per_agent == 0` and no spawn rules), GET/DROP are omitted from the action vocabulary.

  - Similarly, when there is at least one affordance configured for a level, the core **INTERACT** command must be automatically included:
    - INTERACT should be treated like movement and GET/DROP: a required core action whose presence is implied by affordance usage.
    - If there are zero affordances in a level, INTERACT should not be included in the action vocabulary.
    - For **continuous substrates**, INTERACT must use an explicit interaction range:
      * At minimum, this range is provided by the substrate config (e.g., `interaction_radius` on continuous substrates).
      * Future item-specific/interact-style commands may introduce per-command range overrides, but there must never be an implicit, hard-coded distance for interactions in continuous space.

---

## 6. VFS Engine & DynObs Changes

### 6.1 VFS Engine Extensions

Current VFS schema (in `vfs/schema.py`) describes variables and observation fields for Phase 1 (static variables only; expressions rejected at load time). We need to:

1. Introduce profile scope and IDs:
   - Extend `VariableDef` or add a profile wrapper:
     - `profile_id: str`
     - `scope: Literal["global", "agent", "item"]`
   - Keep `VariableDef` semantics but allow grouping by `(scope, profile_id)`.

2. Adjust VFS evaluation (BAC-aware, Phase 2+):
   - Evaluation loop becomes:
     - Evaluate global profiles once per step.
     - For each agent, evaluate agent profiles using:
       - Global bars & VFS as inputs.
       - Agent’s own bars/VFS.
     - For each item, evaluate item profiles using:
       - Global bars & VFS.
       - Item’s own VFS and possibly associated affordances.
   - Ensure ordering respects declared dependencies; when the expression DSL is introduced (see VARIABLE_SUBSYSTEM.md and `docs/vfs-integration-guide.md`), dependency graphs will be compiled by BAC and executed in topological order.

3. Serialization:
   - Include item VFS state in checkpoint archives (alongside global and agent VFS).
   - Ensure that reloading reproduces item inventories and VFS values exactly.

### 6.2 DynObs / Observation Building

Extend observation building (wherever the structured obs is composed) to:

- Include **global VFS** fields according to their `ObservationField`/profile config.
- Include **agent VFS** fields.
- Include **item VFS** fields for:
  - Items currently held by the agent.
  - Optionally: items within an observable spatial neighborhood (future work; keep out of initial scope).
- Respect existing masks:
  - Items not held and not in range should be masked via `curriculum_active`/similar fields, consistent with QUICK‑05 structured masking.

We will likely need:

- A mapping from profile IDs to a fixed observation index layout:
  - Immutable per compiled universe (so obs_dim is stable).
  - Uses masks to indicate which slots are active per agent / per step.

### 6.3 Observation Management Modes

To support different workflows around observation size and curriculum reuse, introduce three observation management modes (configured at the **experiment level**, since they affect obs_dim semantics):

1. **`full_auto`**
   - System derives obs layout from config:
     - Includes all configured profiles and variables.
     - Uses masking to handle presence/absence where possible, but may drop fields entirely when they are not declared in a given experiment config.
   - Goal: easiest path for users; system manages obs size and masking automatically.

2. **`max_compact`**
   - System always **drops** inactive/unused fields rather than padding and masking.
   - Obs_dim is minimized for the current experiment/level, but:
     - Different curricula may have different obs_dims.
     - The user is responsible for managing networks/checkpoints across curricula (no guarantee of dimension compatibility).
   - Goal: smallest possible observation vectors; ideal for one-off experiments or where per-level networks are acceptable.

3. **`full_manual`**
   - User specifies the full obs layout explicitly:
     - For example, indices 0–27 = stratum, 28–31 = time, 32 = affordance_indicator, 33 = health_bar, etc.
     - Each index (or slice) is bound to a specific variable, profile, or preset.
   - System:
     - Enforces this mapping and requires that all referenced variables/profiles exist.
     - Uses masking values (not dimension changes) to indicate inactivity.
   - Goal: maximum control and stability for advanced users; obs_dim is fixed by design across curricula.

Mode selection:
- Is an experiment-level decision (features that change obs_dim must be experiment-scoped).
- Curriculum-level configs can still control **masking** and activation, but not the base obs shape in `full_manual` and must follow the chosen mode’s semantics in `full_auto`/`max_compact`.

---

## 7. Reference Config & Documentation Updates

### 7.1 Reference Config

Update `configs/reference_config/reference-config-v2.1-complete.yaml`:

- Add new **Section** for `vfs_profiles.yaml`:
  - Document global/agent/item profile examples.
  - Show how profiles feed into obs and how they depend on bars/VFS.
- Add new **Section** for `items.yaml`:
  - Provide at least one example item type and spawn rule.
  - Document each field and its semantics (especially limits and schedules).

### 7.2 Schema Docs

Add or extend docs under `docs/config-schemas/`:

- `items.md` – schema and examples for `items.yaml`.
- `vfs-profiles.md` – schema and examples for `vfs_profiles.yaml`.

Highlight:

- “No defaults” policy for behavioral parameters.
- Relationship between profiles and observation masking.
- How items, bars, VFS, cascades, and affordances interact.

---

## 8. Phasing & Risk Retirement Strategy

### 8.1 Risk & Complexity Overview

- **Phase 1 (schemas + compiler)** – low–medium complexity, low runtime risk.
  - Main risk: locking in an awkward schema/file layout or over‑designing the first version.
  - Mitigation: keep behaviour‑free (metadata only), tighten scope to minimal DTOs and references.
- **Phase 2 (VFS engine + DynObs)** – high complexity, medium–high risk.
  - Cross‑cuts VFS evaluation, dependency ordering, obs layout, and masking.
  - Risks: obs_dim mismatches, incorrect VFS values, subtle masking bugs.
- **Phase 3 (items runtime + inventory)** – high complexity, medium risk.
  - Introduces new stateful systems (ItemManager, inventories, item VFS state).
  - Risks: state drift between items, inventories, VFS slots, and observations.
- **Phase 4 (advanced scheduling/conditions)** – medium complexity, low–medium incremental risk.
  - Risks: combinatorial interactions between schedules and conditions; mitigated by strong validation.

### 8.2 Risk Reduction Activities

1. **Tighten Phase 1 scope**
   - Limit `items.yaml` and `vfs_profiles.yaml` to structural metadata and wiring (IDs, scope, obs mapping) with no executable expressions initially.
   - Defer expression evaluation semantics to Phase 2+.

2. **Feature flagging**
   - Add a feature flag in compiled metadata (e.g., `features.items_enabled: bool`).
   - Gate all new runtime paths in environment/VFS/dynobs on this flag so schema/metadata changes can land without affecting existing runs.

3. **Dedicated test config pack**
   - Create `configs/test/items_smoke/` with:
     - A single item type (e.g., `umbrella`) with simple spawn rules.
     - One global, one agent, and one item VFS profile.
   - Use this pack for focused unit/integration tests of compiler, VFS, and environment wiring.

4. **Metadata‑driven obs tests**
   - Add tests that derive expected obs layout and masks directly from compiled metadata and assert:
     - `env.action_dim` / `env.obs_dim` matches compiled counts.
     - Activating/deactivating items affects masks only, not raw dimensions.

5. **Constrained VFS evaluation semantics**
   - In early phases, support only simple, hard‑coded update patterns (e.g., linear transforms, threshold checks) rather than a full expression DSL.
   - Accept expression fields in config but either validate them as “not supported yet” or treat them as metadata until the DSL is implemented.

6. **Hard validation & guardrails**
   - Compiler:
     - Enforce reasonable limits on item types, spawn rules, and profile counts.
     - Fail fast on unresolved references (`vfs_profiles`, `item_type_id`, `when` conditions).
   - Runtime:
     - Assertions around inventory size vs `max_items_per_agent`, and VFS index bounds.

7. **Structural vs behavioural PR separation**
   - Land changes in small steps:
     - (a) DTOs + compiler + metadata only.
     - (b) VFS catalog + metadata tests.
     - (c) ItemManager + inventories behind feature flag.
     - (d) DynObs + masking + items_smoke tests.

8. **Instrumentation for debugging**
   - Behind a debug flag, log:
     - Item spawns/despawns and inventory changes.
     - Counts of active items per type and per agent.
     - Summaries of VFS profile evaluation (per scope).

### Phase 1 – Schema & Compiler Only

- Implement DTOs and compiler wiring (`ItemsConfig`, `VFSProfilesConfig`).
- Update `CompiledUniverse` to carry new metadata.
- Update reference config + schema docs.
- No runtime / environment changes yet.

**Risk retired:** configuration drift between design and code for items/VFS profiles; we gain compile‑time validation and a stable schema.

### Phase 2 – VFS Engine & DynObs

- Extend VFS engine to handle scoped profiles (global/agent/item).
- Extend observation builder to include new VFS fields with masking.
- Provide tests that:
  - Verify evaluation ordering and dependency handling.
  - Confirm obs_dim and masks match compiled metadata.

**Risk retired:** mismatch between VFS design and observed agent inputs; all VFS‑driven behavior is visible and validated.

### Phase 3 – Items Runtime & Inventory

- Implement ItemManager, item instances, and inventory integration.
- Wire item interactions into the environment (pickup/use/drop).
- Connect item VFS profiles to item lifecycle (durability, timers, etc.).

**Risk retired:** items existing only “on paper” in config; agents can now interact with them, and their VFS effects are observable.

### Phase 4 – Advanced Scheduling & Conditions (Optional)

- Add richer scheduling (Poisson, normal distributions, scripted sequences).
- Implement complex spawn conditions referencing VFS, bars, and affordances.
- Tighten validation and add regression tests for scheduling logic.

**Risk retired:** ad‑hoc or “magic” item behaviours; all spawn/placement behaviour becomes declarative and testable.

---

## 9. Open Design Questions (to resolve before coding)

1. **File layout**
   - Separate `vfs_profiles.yaml` vs embedding into `environment.yaml`?
   - Separate `items.yaml` per level vs level block inside a single `items.yaml`?

2. **Expression language for VFS profiles**
   - How much of a DSL do we support in Phase 1?
   - Do we reuse existing expression fields in `vfs/schema.py`, or introduce a higher‑level profile‑oriented abstraction first?

3. **Observation budget**
   - How many item slots per agent should be represented explicitly in obs?
   - How do we handle items beyond that slot count (truncate, summarize, ignore)?

4. **Interaction granularity**
   - Do we model item interactions as:
     - New custom actions (e.g., `USE_ITEM_slot0`), or
     - Parameterized interactions with arguments (current code prefers fixed vocab)?

5. **Performance considerations**
   - Max reasonable counts for items / profiles per level.
   - Whether we need batching/compaction strategies for item VFS state to avoid large sparse tensors.

These decisions will determine some DTO field shapes and runtime data structures and should be settled (or at least constrained) before implementation begins.
