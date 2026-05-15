## Environment Runtime & DAC Reward Engine

**Location:** `src/townlet/environment/`

**Responsibility:** Vectorized batched GPU-native runtime that executes action-step-observation loops for all agents in parallel, applying meter dynamics, effects, and DAC-based reward computation.

**Key Components:**

- **`vectorized_env.py`** (2200 lines) — Central orchestrator. `VectorizedHamletEnv` class manages the full tick lifecycle: action validation, meter depletion, cascading effects, VFS evaluation, terminal conditions, effect scheduling, meter recovery from Effects, retirement checks, and DAC reward calculation. Contains 38 methods spanning initialization (with CompiledUniverse consumption), reset, step, observation building, and affordance position/mask management. Largest single file in codebase; primary refactoring candidate.

- **`dac_engine.py`** (1012 lines) — DAC compiler→runtime bridge. `DACEngine` takes compiled DAC YAML specs (via DriveConfig or DriveAsCodeConfig) and builds GPU-native reward computation graphs. Compiles modifiers into torch.where-based range lookups, extrinsic strategies (multiplicative/constant_base variants), and shaping bonuses. Formula: `reward = extrinsic + (intrinsic_raw × base_weight × modifier1 × modifier2...) + shaping`. Returns components dict for logging. Handles dual config schema compatibility (drive_as_code + agent_config).

- **`action_builder.py` + `action_config.py` + `action_labels.py` + `substrate_action_validator.py`** — Action assembly & validation chain. `ComposedActionSpace` maintains complete action list (substrate + custom + affordance) with disabled actions masked but still assigned IDs (critical: action_dim same across curriculum levels). `SubstrateActionValidator` ensures substrate↔action compatibility (e.g., Grid2D requires 4-way movement deltas). ActionLabels rehydrates from compiler-emitted metadata.

- **`affordance_config.py` + `affordance_engine.py` + `affordance_layout.py`** — Affordance subsystem. `AffordanceEngine` (625 lines) processes instant and multi-tick affordance interactions using Effects system, handles operating hours (delegating to `temporal_utils.is_affordance_open()`), and applies affordability checks. Converts affordance specs into CompiledAffordance (on_start/per_tick/on_completion/etc.). Layout manages spatial positioning of affordance instances.

- **`meter_dynamics.py`** (221 lines) — Tensor-driven meter updates. Applies passive base depletions (curriculum-modulated), cascade rules (secondary→primary, tertiary→secondary, tertiary→primary), modulation multipliers, and terminal condition checks. Pre-computes cascade/modulation tables at init for GPU performance. Handles vectorized [num_agents, meter_count] tensors.

- **`temporal_utils.py`** (78 lines) — **Single source of truth** for affordance operating hours. Canonical `is_affordance_open(time_of_day, operating_hours)` centralizes wraparound logic (supports [8,18], [18,28], [22,6], [0,24] notations uniformly via modulo arithmetic). Extracted from UniverseCompiler._is_open() to fix JANK-09 (3 prior implementations with inconsistencies).

- **`null_managers.py`** (67 lines) — Null-object pattern for optional subsystems. `NullItemManager` provides no-op tick/process_respawns when items disabled, raises RuntimeError on spawn_item. Consolidates duplicate implementations (ENV-009).

**Runtime Flow (One Tick):**

1. **Action Execution** → `_execute_actions()`: Movement (substrate delta application), interaction (instant or multi-tick affordance), wait action. Validates affordance availability via temporal masks.
2. **Meter Depletion** → `meter_dynamics.deplete_meters()`: Base passive decay × curriculum multiplier.
3. **Cascading** → Three cascade passes (secondary→primary, tertiary→secondary, tertiary→primary).
4. **Effects Tick** → `effect_manager.tick()`: Active Effects modify bars; results synced back to meters.
5. **VFS Evaluation** → Global profile evaluation; updated values written to `vfs_registry._storage`.
6. **Terminal Checks** → `meter_dynamics.check_terminal_conditions()`: Are any agents dead?
7. **Item Lifecycle** → `item_manager.tick()` (age/despawn), `process_respawns()`.
8. **Retirement** → Agents reaching max_steps_per_episode marked done + bonus +1.0 reward.
9. **DAC Reward** → `dac_engine.calculate_rewards()`: extrinsic, intrinsic×modifiers, shaping.
10. **Temporal Increment** → `time_of_day = (time_of_day + 1) % day_length` if temporal_mechanics enabled.
11. **Observation** → `_get_observations()`: Build [num_agents, obs_dim] from meters, VFS, positions, affordances, effects.

**DAC Engine Internals:**

- **Modifier Compilation** (`_compile_modifiers()`): Converts YAML range definitions into GPU-optimized functions. Uses `torch.where()` for branch prediction. Supports bar indices (from `bar_index_map`) and VFS variables (resolved at init).
- **Extrinsic Paths**: multiplicative (base × bar1 × bar2 × ... × modifiers), constant_base_with_shaped_bonus (with bar/variable bonuses). Dual-schema (drive_as_code vs agent_config) via hasattr/getattr for config detection.
- **Intrinsic Modulation**: `intrinsic = intrinsic_raw × base_weight × (modifier1 × modifier2 × ...)`. Modifiers are chained multipliers (range-based or VFS-sourced).
- **Shaping**: Placeholder reward bonuses (not yet deeply used).
- **Device Validation** (ENV-007): Ensures all tensors match DACEngine device; raises RuntimeError on mismatch.

**Dependencies:**

- **Inbound** (callers): 
  - `population/base.py` → `VectorizedHamletEnv.from_universe()`
  - `population/vectorized.py` → `VectorizedHamletEnv`
  - `demo/runner.py`, `demo/live_inference.py` → `VectorizedHamletEnv`
  
- **Outbound** (consumed):
  - `universe.compiled` → `CompiledUniverse` (meter_metadata, compiled_vfs_profiles, action_space, affordances, effects_schema)
  - `substrate.*` → Substrate implementations (Grid2D, Grid3D, Continuous, Aspatial)
  - `vfs.registry` → `VariableRegistry` (read/write during step)
  - `vfs.evaluator` → `VFSEvaluator` (global profile evaluation)
  - `vfs.observation_builder` → Observation spec construction
  - `effects.executor` → `CommandExecutor`, `EffectManager`
  - `items` → `ItemManager` (spawning, lifecycle)
  - `config.drive_as_code` → DriveAsCodeConfig (DAC YAML)
  - `config.agent_config` → DriveConfig, bonus specs

**Patterns Observed:**

- **Vectorization throughout**: All operations on [num_agents, ...] shaped tensors; zero for-loops over agents in hot path.
- **Null-object pattern**: `NullItemManager`, `null_effect_manager` for optional subsystems; fail-fast on misuse.
- **Config schema dual-path**: DACEngine supports both drive_as_code.ExtrinsicStrategyConfig and agent_config.ExtrinsicConfig via hasattr/getattr branching.
- **Metadata-driven runtime**: Action space, affordance positions, temporal masks, observation specs all materialized from CompiledUniverse artifacts at init.
- **Closure-based compiled functions**: Modifiers, extrinsic, shaping compiled into lambdas capturing config at init time.

**Concerns:**

1. **vectorized_env.py size (2200 lines)** — Natural decomposition candidates:
   - **Action execution & affordance interaction** → dedicated `action_executor.py` (take `_execute_actions()` + `_handle_interactions()` + `_handle_instant_interactions()`)
   - **Observation encoding** → dedicated `observation_encoder.py` (take `_get_observations()`, `_build_affordance_encoding()`, `_encode_position_observation()`, etc.)
   - **Initialization & configuration** → dedicated `env_factory.py` or expand `from_universe()` pattern
   - **Reward & metric calculation** → dedicated `reward_calculator.py` (take `_calculate_shaped_rewards()`)

2. **Config rehydration from CompiledUniverse**: Seen at lines 190–199, 717–746 (rehydrating ActionLabels, ActionConfigs from runtime artifacts). Not an immediate antipattern (artifacts are thin DTOs), but watch for recursive unpacking of nested config structures.

3. **hasattr/getattr for dual schemas** (dac_engine.py:110–135): DACEngine accepts both DriveConfig and DriveAsCodeConfig; uses hasattr/getattr to detect which schema. Works but fragile; strongly-typed schema union would be cleaner. Same at lines 196, 231, 243, 257.

4. **No residue of RewardStrategy**: Confirmed — zero mentions of RewardStrategy class. DAC is sole reward path; clean deletion.

5. **Temporal mask table initialization**: `action_mask_table.shape[1] == 0` check (line 702) suggests optional temporal metadata. Ensure compiler always populates when temporal_mechanics enabled.

6. **try/except minimized**: Found none in hot paths. Good hygiene.

**Confidence:** **High**

- Codebase is well-instrumented with comments (ENV-007, HIGH-01, HIGH-02, JANK-09 references).
- Clear separation of concerns: meter dynamics, DAC reward, affordance interactions, effects, VFS evaluation.
- No RewardStrategy legacy; DAC is cohesive and complete.
- Decomposition roadmap for vectorized_env.py is concrete and low-risk.
- Unit tests likely exist (not inspected here) validate core tick flow.
