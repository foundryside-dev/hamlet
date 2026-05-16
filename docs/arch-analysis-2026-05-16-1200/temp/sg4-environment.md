# SG4 — Environment & DAC

**Location:** `src/townlet/environment/` (5,041 LOC, 15 files)
**Confidence:** High — read all 15 modules in full or in detail, walked the `step()` tick loop with citations, cross-checked claims against git history (`git show --stat 4d694d73`, `git show --stat bfde7c8a`), grep-verified the absence of `reward_strategy` references in `src/` and `configs/`, and traced inbound/outbound dependencies. The one source-vs-doc discrepancy (line-count of the deleted file) is reported below.

## Responsibility

This subsystem is the runtime that everything else simulates *through*. It contains:

- **`VectorizedHamletEnv`** (`vectorized_env.py:63-1559`) — the GPU-native, batched, Gym-style environment. It owns the per-agent tensors (`positions`, `meters`, `dones`, `step_counts`, `intrinsic_weights`, `_velocity`, `interaction_progress`), the substrate, the affordance engine, the DAC engine, the VFS registry, the item manager, the effect manager, and a battery of compiled VTC (variable-typed compute) programs. Every training tick passes through `step()`.
- **`DACEngine`** (`dac_engine.py:28-1012`) — the runtime reward engine. It consumes the compiled `DriveConfig` / `DriveAsCodeConfig` from the universe and produces `total = extrinsic + intrinsic·w_eff + shaping` on GPU.
- **The action stack** — composes a global substrate + custom action vocabulary, builds masks per tick, executes actions (movement, INTERACT, item GET/USE/DROP, custom verbs).
- **The affordance stack** — config-driven instant/multi-tick interaction engine that drives the Effects DSL and modulates meter changes.
- **The observation encoder** — assembles per-tick observation tensors by syncing primitives into VFS and reading back through the compiled VFS observation spec.

The environment is the *one* class that wires substrates, items, effects, VFS, affordances, DAC, and curriculum together. Everything else either drives it (`population/`, `demo/`, `training/`) or is consumed by it.

## Tick loop walkthrough

Entry point: `VectorizedHamletEnv.step(actions, depletion_multiplier=1.0)` at `vectorized_env.py:1084-1218`.

```
0. Snapshot prev_dones; reset tick-scoped VFS slots                     vectorized_env.py:1102-1103
       prev_dones = self.dones.clone()
       self.vfs_registry.reset_tick_scoped()

1. Execute actions                                                       vectorized_env.py:1105
       successful_interactions = self._action_executor._execute_actions(actions)
       (action_executor.py:20-158)
       1a. Split actions into substrate (< substrate_action_count) vs custom    action_executor.py:23-30
       1b. For substrate actions: apply movement deltas via env.substrate.apply_movement()
       1c. Compute and store velocity = positions - old_positions; publish
           velocity_{x,y,z,magnitude} to VFS if those vars exist          action_executor.py:32-46
       1d. Deduct per-bar `depletion.move` from movers                    action_executor.py:48-60
       1e. If item_handler present: dispatch GET / USE_SLOT_* / DROP_SLOT_* /
           handler.custom_action_specs verbs (REST, MEDITATE, ...)        action_executor.py:62-134
       1f. INTERACT mask:                                                 action_executor.py:136-156
            - Deduct `depletion.interact` from interactors
            - Call _handle_interactions(interact_mask)
              -> if temporal disabled OR no multi-tick affordances:
                    _handle_instant_interactions: substrate.is_on_position
                    check, affordability check (money_idx >= cost),
                    affordance_engine.apply_interaction()                action_executor.py:253-289
              -> else: walks each affordance, splits instant vs multi-tick,
                    advances vtc_interaction_progress_program, applies
                    apply_vtc_multi_tick_effects() per tick-group        action_executor.py:160-234
       1g. _update_affordance_tracking writes _last_affordances /
           _affordance_streaks / _unique_affordances_count               vectorized_env.py:1328-1371

2. Apply compiled VTC action-writes (VFS transition writes for the chosen
   action ids) - active_mask excludes already-dead agents                vectorized_env.py:1106, 1224-1241

3. Passive depletion via compiled VTC program                            vectorized_env.py:1109, 1243-1256
       program.apply(bars_state=..., depletion_multiplier=...)

4. Passive threshold cascades (e.g., low energy -> health damage)        vectorized_env.py:1112, 1258-1270

5. Effects tick (active effects from EffectManager)                      vectorized_env.py:1114-1130
       - Build bars dict (views into self.meters)
       - effect_manager.tick(bars, vfs_registry, current_step=global_tick,
                              item_manager)
       - Sync bars dict back into self.meters

6. VFS evaluator pass (global profile)                                   vectorized_env.py:1132-1166
       vfs_evaluator.evaluate_global_profile(
           profile, bars, vfs_state, marks, device, step=global_tick,
           affordances=_build_vfs_affordance_context(),
           temporal=_build_vfs_temporal_context(),
           agent_positions, affordance_positions, vfs_types,
           num_agents, item_vfs, item_profile_map,
           item_index_to_profile,
       )
       Writes results back via vfs_registry.set_engine_value(...)

7. Apply compiled VTC terminal conditions                                vectorized_env.py:1169, 1272-1283
       self.dones |= terminal_program.apply(bars_state, ...)

8. step_counts += 1; global_tick += 1                                    vectorized_env.py:1172-1173

9. Item lifecycle:                                                       vectorized_env.py:1177-1184
       item_manager.tick(global_tick)            # age/despawn
       item_manager.process_respawns(global_tick, bars=, temporal=)

10. Retirement check: step_counts >= agent_lifespan                      vectorized_env.py:1188

11. Reward computation                                                   vectorized_env.py:1191
        rewards = self._reward_calculator._calculate_shaped_rewards()
        (reward_calculator.py:19-53)
        - Pull intrinsic_raw from env.exploration_module
          (if set; else zeros)                                            reward_calculator.py:22-26
        - Build kwargs dict with agent_positions, affordance_positions,
          last_action_affordance, affordance_streak, unique_affordances_used,
          current_hour (if temporal)                                      reward_calculator.py:28-39
        - Hand off to env.vtc_reward_program.apply(
              reward_backend=env.dac_engine,
              step_counts, dones, meters, intrinsic_raw,
              reward_context=kwargs)                                      reward_calculator.py:41-48
          (the VTC reward program is the compile-time wrapper that calls
           DACEngine.calculate_rewards)
        - Store intrinsic_weights and _last_reward_components on env

12. Retirement bonus (+1.0) applied to retired agents; dones |= retired  vectorized_env.py:1192-1193

13. Cancel any pending agent-scoped scheduled effects for newly-dead     vectorized_env.py:1196-1200
    agents (effect_manager.cancel_scheduled_for_entity)

14. Advance time_of_day if temporal enabled                              vectorized_env.py:1203-1206

15. Build observations via ObservationEncoder                            vectorized_env.py:1208
        observation_encoder._get_observations() (observation_encoder.py:23-46)
        1. _sync_observation_primitives_to_vfs():
           grid, local_window, position, velocity, meters,
           affordance_at_position, effects, temporal -> VFS               observation_encoder.py:122-282
        2. For each field in env.observation_spec.fields:
           _build_observation_field_from_vfs(field.name, field.dims)
           -> obs_vfs uses build_vfs_observation(registry, vfs_observation_spec, ...)
           -> agent-scoped fields read directly from VFS variable
        3. torch.cat(outputs, dim=1) -> [num_agents, observation_dim]
        4. Apply observation_activity.active_mask if set

16. Return (observations, rewards, dones, info)                          vectorized_env.py:1210-1218
        info contains: step_counts, positions, successful_interactions,
                       reward_components (DAC breakdown), intrinsic_weight
```

Key invariants enforced in `step()`:

- **Single source of truth for time.** `global_tick` is independent of `step_counts[0]` to fix HIGH-01 (`vectorized_env.py:435`, comments at `1124, 1152, 1173, 1178, 1183`). Items, effects, and VFS evaluator all consume `global_tick`.
- **VFS reset cadence.** `reset_tick_scoped()` runs at top of step; `reset_episode_scoped()` runs only in `reset()` (`vectorized_env.py:763`).
- **Dead agents zero-out.** DAC explicitly `torch.where(dones, 0, reward)` for extrinsic, intrinsic, and shaping (`dac_engine.py:185, 225, 263, 290, 321, 356, 390, 422, 451, 491, 986, 995`). Action masks also force-disable all actions for dead agents (`vectorized_env.py:1079-1080`).

## DAC engine

`DACEngine` (`dac_engine.py:28-1012`) is constructed at `vectorized_env.py:325-331` with `dac_config=self.level.drive` (the per-level `DriveConfig`/`DriveAsCodeConfig` already materialized by the universe compiler), the shared `VariableRegistry`, the device, `num_agents`, and a `bar_index_map` (bar_name -> index into the `meters` tensor) built from `universe.meter_metadata` (`env_factory.py:30-32`, called at `vectorized_env.py:322`).

**Construction-time compilation** (`dac_engine.py:73-83`):
- `_compile_modifiers()` (`dac_engine.py:85-152`): for each entry in `dac_config.modifiers`, builds a closure that reads from a bar or VFS variable (DAC schema uses `bar`/`variable` fields; agent-config schema uses a single `source` string and resolves it against `bar_index_map`), then walks `ranges` sorted by `min` using a chain of `torch.where(in_range, r.multiplier, fallback)` to produce a per-agent multiplier.
- `_compile_extrinsic()` (`dac_engine.py:154-501`): a giant `if/elif` matching `strategy.type` to one of nine concrete computation closures. All nine close over the strategy and capture either bar IDs or variable IDs:
   - `multiplicative` (line 162): `base * prod(bars)`
   - `constant_base_with_shaped_bonus` (line 191): two sub-shapes — DAC schema (`base_reward + Σ bar_bonuses + Σ variable_bonuses`) at line 196 and agent.yaml schema (`base + Σ weight*transform(bar)` with `transform ∈ {linear, quadratic, exponential}`) at line 230
   - `additive_unweighted` (line 268): `base + Σ bars`
   - `weighted_sum` (line 296): `base + Σ scale*bar`
   - `polynomial` (line 327): `base + Σ scale*bar^center` with `torch.clamp(min=0)` to dodge NaN on fractional exponents of negatives (`dac_engine.py:344`, comment "CRIT-01")
   - `threshold_based` (line 362): `base + Σ (bar≥center ? scale : 0)`
   - `aggregation` (line 396): `base + min(bars)` (hardcoded to `min`; the docstring at line 397 acknowledges this is simplified)
   - `vfs_variable` (line 428): `base + Σ weight*vfs[var]`
   - `hybrid` (line 457): per-bonus, `scale*bar` if `|center|<1e-6` else `scale*(bar-center)`
- `_compile_shaping()` (`dac_engine.py:503-886`): builds a `list[Callable]` for the 11 supported shaping types (`approach_reward`, `completion_bonus`, `efficiency_bonus`, `state_achievement`, `streak_bonus`, `diversity_bonus`, `timing_bonus`, `economic_efficiency`, `balance_bonus`, `crisis_avoidance`, `vfs_variable`). Each closure factory captures its config and returns a `compute_*(**kwargs)` that pulls what it needs from `kwargs` (positions, last affordance, streaks, hour, meters, etc.).

**Runtime path: `calculate_rewards`** (`dac_engine.py:904-1012`):
1. Device-consistency check across `meters`, `intrinsic_raw`, `dones` with a tolerant `cuda` vs `cuda:0` comparator (`dac_engine.py:940-962`).
2. `extrinsic = extrinsic_fn(meters, dones)` (line 965).
3. `intrinsic_weight` starts at `ones(num_agents)`; for each modifier name listed in `intrinsic.apply_modifiers`, multiply in `modifier_fn(meters)`. `intrinsic = intrinsic_raw * base_weight * intrinsic_weight`, then zero out dead agents (lines 971-986).
4. `shaping_total = Σ shaping_fn(meters, dones, **kwargs)`, zero out dead agents (lines 989-995).
5. Return `(extrinsic + intrinsic + shaping_total, intrinsic_weight, components_dict)` where the components dict has `extrinsic`, `intrinsic` (post-modifier), `intrinsic_raw` (post base-weight, pre-modifier), and `shaping` (lines 1003-1012).

**The "compiled" path is purely Python-closure-based, not torch.jit.** The GPU-nativeness comes from operating on `torch.Tensor` for all per-agent quantities (multipliers, bonuses, etc.) rather than from a compiled graph. The only string-comparison hot spot is `completion_bonus` / `timing_bonus`, which loops `[1.0 if aff == target else 0.0 for aff in last_action_affordance]` and turns it into a tensor (`dac_engine.py:572-577, 747-751`).

**Drive hash provenance.** DAC engine itself does *not* produce `drive_hash`. The universe compiler computes `drive_hash = self._compute_pydantic_hash(level.drive)` at `townlet/universe/compiler.py:416` and stores it on `CompiledUniverse` (`townlet/universe/compiled.py:160, 195, 286, 340, 356`). At checkpoint save it is copied from the universe to the checkpoint dict (`townlet/training/checkpoint_utils.py:40`), and on load the saved hash is compared against the current universe's hash; mismatch raises (`checkpoint_utils.py:98-107`).

## Items & effects integration (per-tick)

Several action and lifecycle hooks weave items and effects through the env. Specifically:

- **Items appearance** is handled in `reset()` (`vectorized_env.py:798-820`) and per-tick in `step()` (`vectorized_env.py:1177-1184`). `item_manager.tick(global_tick)` ages items and despawns expired ones; `item_manager.process_respawns(global_tick, bars, temporal)` triggers periodic respawning. Both calls use the *new* global_tick after increment (line 1180-1184).
- **Item actions** (GET/USE/DROP) are dispatched per agent inside `_execute_actions` (`action_executor.py:62-134`). Each action loops `for agent_idx in torch.where(mask)[0]` and calls a specific handler that consumes `meters` and `current_tick`. The handler signature includes `meters=env.meters` because items can directly modify bars (`action_executor.py:78, 99, 134`).
- **Item-driven custom verbs** are registered by `item_handler.custom_action_specs` (`action_executor.py:120`). The exact set is items-dependent and not enumerated here — that's SG7's contract.
- **Item action masks** are computed by `item_handler.compute_custom_action_masks(action_space, action_masks, positions)` (`vectorized_env.py:994`). The handler mutates the action_masks tensor in place.
- **Effect manager tick** is between cascades and terminal checks (`vectorized_env.py:1120-1126`). Bars are passed by reference (`bars_dict = {name: meters[:, idx] for ...}`); the effect manager mutates them in place and the env syncs them back (`vectorized_env.py:1128-1130`). The effect manager is also passed `item_manager` (line 1125) so effects can act on items.
- **Newly-dead-agent cleanup** (`vectorized_env.py:1196-1200`): after rewards are computed, any agent that became done in this step has its scheduled (delayed) effects cancelled via `effect_manager.cancel_scheduled_for_entity(scope="agent", entity_id=int(idx))`.

Result: the per-tick contract between env, items, and effects is bidirectional — bars and VFS are shared mutable state, and lifecycle hooks fire deterministically in a specific order (action → depletion → cascades → effects → VFS → terminal → counters → items → reward).

## Action stack

The composable action stack is **substrate actions + custom actions (+ future affordance actions)**. The runtime no longer builds it itself — the universe compiler emits a `RuntimeActionSpace` (with `actions`, `substrate_action_count`, `custom_action_count`, `affordance_action_count`, `enabled_action_names`) which the env rehydrates into a `ComposedActionSpace` at `vectorized_env.py:404-674`.

- **`action_config.py:20-97`** — `ActionConfig` Pydantic model. Required fields with no defaults: `id`, `name`, `type ∈ {movement, interaction, passive, transaction}`, `costs` (dict), `effects` (dict), `delta`, `teleport_to`, `enabled`, `description`, `icon`, `source ∈ {substrate, custom, affordance, item}`, `source_affordance`. VFS hooks: `reads: list[str]` and `writes: list[WriteSpec]` (compiled into the `VTCActionWriteProgram`). `validate_movement_actions` (line 89) enforces that movement actions have `delta` or `teleport_to`, and that non-movement actions do not.
- **`action_builder.py:12-99`** — `ComposedActionSpace`. Keeps the full action list (including disabled ones, so `action_dim` is constant across curriculum levels for checkpoint transfer; comment at lines 15-18 and `action_dim` property at 41-46) plus counts and an `enabled_action_names` set. Helper accessors: `get_action_by_id`, `get_action_by_name`, `get_enabled_actions`, `get_substrate_actions`, `get_custom_actions`, `get_base_action_mask`.
- **`action_builder.py:101-229`** — `ActionSpaceBuilder`. The *legacy* runtime builder that reads `substrate.get_default_actions()` and `global_actions.yaml`. The env's hot path no longer uses this (compiler emits a `RuntimeActionSpace`), but it survives for tooling and tests. `_load_global_custom_actions` (lines 181-229) enforces explicit `custom_actions` key in YAML and refuses to silently default optional fields ("NO DEFAULTS" comments at lines 184, 196, 213, 226).
- **`action_executor.py:14-289`** — already walked in the tick-loop section. Handles substrate movement, velocity write-back to VFS, GET/USE/DROP item verbs, custom verbs registered by `item_handler.custom_action_specs`, INTERACT dispatch (instant vs multi-tick via `vtc_interaction_progress_program`), and per-affordance affordability check using `env.money_idx`.
- **`action_labels.py:23-359`** — Configurable user-facing action labels mapped onto canonical action indices (`CanonicalAction` IntEnum at lines 23-55). Four presets at `PRESET_LABELS` (lines 100-166): `gaming` (UP/DOWN/LEFT/RIGHT), `6dof` (SWAY/HEAVE/SURGE), `cardinal` (NORTH/SOUTH/EAST/WEST), `math` (X_NEG/X_POS/...). `get_labels()` builds label sets for substrate dim (lines 169 onwards). Pedagogical value: the same canonical actions can be relabelled per domain.
- **`substrate_action_validator.py:21-110`** — `SubstrateActionValidator`. Compile-time-ish sanity check: `square` grid must define deltas `{(0,-1),(0,1),(-1,0),(1,0)}`; `cubic` requires the 6 axis-aligned 3D deltas; `hex` requires 6 axial deltas; `aspatial` rejects any movement actions; warns if no INTERACT action exists in the global vocabulary. Used by the compiler / validator path; not the runtime hot loop.

**Custom actions in practice.** CLAUDE.md claims `REST` (energy recovery) and `MEDITATE` (mood boost) are the custom actions. Verified: `configs/default_curriculum/actions.yaml` declares both as `enabled_by_default: false` custom actions (only config in repo containing those names). `REST` description: "Passive energy recovery (slower than SLEEP)". `MEDITATE` description: "Passive mood boost (slower than MEDITATE affordance)" — note the affordance shares the name, which is mildly confusing.

## Affordance stack

- **`affordance_config.py:18-155`** — Pydantic schemas. `AffordanceEffect`, `AffordanceCost`, `AffordanceConfig` (with `interaction_type ∈ {instant, multi_tick, continuous, dual}`, `duration_ticks` validation, `operating_hours [open, close]` validation, multi-format `position` validation at lines 102-126), and `AffordanceConfigCollection`. **Note:** this module is described as a "runtime DTO"; the *parse-time* schemas live in `townlet.config.affordances_v2_config` and the compiler emits the runtime objects. The env operates on `level.affordances.affordances` (a tuple of `AffordanceParamConfig` from the compiler — see `vectorized_env.py:482-483`) rather than directly on `AffordanceConfig`. Several methods in `AffordanceEngine` use `hasattr(aff, "interactions")` to distinguish the v2 form (`affordance_engine.py:106`).
- **`affordance_engine.py:46-573`** — The runtime affordance processor.
  - At init (`affordance_engine.py:55-126`): captures `meter_name_to_idx`, modulation program, VFS registry, command executor, effect manager, item manager, affordance overrides. If both `command_executor` and `effects_schema` are present, walks each affordance's `interactions` dict and compiles the five lifecycle stages (`on_start`, `per_tick`, `on_completion`, `on_early_exit`, `on_failure`) via the Effects parser+compiler into a `CompiledAffordance` (`affordance_engine.py:36-44`) stored in `compiled_affordances[name]`.
  - `apply_instant_interaction` (line 154) — costs, modulation multiplier, on_start effects, clamp to [0,1].
  - `apply_vtc_multi_tick_effects` (line 234) — per-tick costs, per_tick effects, then `on_completion` effects gated by `completion_mask`. Takes `current_tick` (the VTC-selected tick number, 0..duration-1) as input from `_advance_vtc_interaction_progress` in the action executor.
  - `apply_interaction` (line 396) — used by the instant-mode path in `_handle_instant_interactions`; applies costs then on_start commands.
  - `_compute_affordance_multiplier` (line 213) — defers to `vtc_modulation_program.compute_affordance_multiplier(affordance_name, bars_state, agent_mask)` when present; returns 1.0 where active, 0.0 elsewhere when absent.
  - `_execute_affordance_effects` (line 491) — the Effects-DSL execution kernel. Builds an `ExecutionContext` per agent (per-target loop over `torch.where(agent_mask)[0]`, lines 538-555), executes compiled commands against shared bar views, then scales the delta by the modulation multiplier (lines 562-563). **This is the only per-agent Python loop in the affordance hot path.**
  - `_check_affordability` (line 314), `_iter_costs`/`_cost_fields` (450-471) handle dict-style vs DTO-style cost entries — DTO compatibility shims.
  - `NullEffectManager` (line 568) — fallback used when no `effect_manager` is provided (only `spawn_effect` raises; other methods are absent and would AttributeError if called).
- **`affordance_layout.py:1-73`** — `AffordancePositionProvider` Protocol and `iter_affordance_positions` adapter. Lets observation builders iterate over affordance positions regardless of whether the underlying container is a dict, a list, a `(name, position)` iterable, or a custom provider. Skips zero-numel tensors (aspatial). The env stores affordances as `dict[str, torch.Tensor]` (`vectorized_env.py:400`).

**Interaction with items (SG7) and VFS (SG2).** The affordance engine is constructed with handles to both `vfs_registry` and `item_manager` (`vectorized_env.py:482-494`). At each `_execute_affordance_effects` call, the `ExecutionContext` carries `vfs_registry`, `item_manager`, `effect_manager`, `scheduler`, `current_tick`, and `affordance_overrides` (`affordance_engine.py:542-552`). The compiled Effects commands therefore can read/write VFS variables, schedule delayed effects, spawn/despawn items, and toggle affordance availability — all from declarative interaction definitions in the YAML.

## Env construction sequence (`__init__`)

`VectorizedHamletEnv.__init__` at `vectorized_env.py:73-529` is large enough to warrant a step-by-step trace:

1. **Device + level resolution** (`vectorized_env.py:95-110`): require explicit `device`, resolve `level = universe.get_level(level_name)`, capture facades `_action_executor`, `_observation_encoder`, `_reward_calculator`.
2. **Curriculum/training extraction** (`vectorized_env.py:112-145`): pull `training_cfg`, `randomize_affordances`, `partial_observability` (derived from `active_vision != "global"`), `vision_range`, `enabled_affordances` (must be explicit), `temporal_support_enabled`, `temporal_active`, `enable_temporal_mechanics` (the AND of those two), `day_length` (required when temporal active), `agent_lifespan`.
3. **Substrate build** (`vectorized_env.py:149-151`): `SubstrateFactory.build(stratum.substrate, device)`.
4. **Action labels rehydrate** (`vectorized_env.py:153-164`): from compiled metadata. Raises if missing.
5. **Experiment + observation metadata** (`vectorized_env.py:166-180`): experiment_name required; observation_activity + level-specific `observation_spec`.
6. **Grid size resolution** (`vectorized_env.py:182-191`): from substrate width/height if available, else from compiled metadata. Square-only invariant enforced.
7. **Vision/POMDP feasibility** (`vectorized_env.py:193-272`): `vision_radius` from `ceil(vision_range * grid_size/2)` with hard cap of 50 to prevent OOM. Five `raise ValueError` guards for unsupported POMDP combinations: aspatial substrates, continuous substrates, 4D+ substrates, 3D windows > 125 cells, and non-`relative` observation encoding under POMDP.
8. **VFS wiring** (`vectorized_env.py:277-314`): `vfs_variables` from universe, `VariableRegistry` built with item profiles + affordance count + num_agents + device, `VFSObservationSpec` from `compiled_vfs_profiles`, `VFSEvaluator` constructed if profiles present.
9. **Meter index map + DAC engine** (`vectorized_env.py:317-331`): build `bar_index_map`, instantiate `DACEngine`.
10. **Effects manager** (`vectorized_env.py:335-360`): lazy-import `EffectManager`, attach to `compiled_effect_catalog`. If catalog is None (minimal config), `effect_manager = None`. `effects_schema` is required from the universe.
11. **Bars config + initial values** (`vectorized_env.py:363-370`): `initial_meter_values` tensor precomputed.
12. **Affordance position resolution** (`vectorized_env.py:374-402`): resolve which affordances are deployable using `env_factory._resolve_deployable_affordances`. Build position dicts from both config and optimization data.
13. **Action space rehydrate** (`vectorized_env.py:404-407`): from `level.runtime_action_space`. `action_ids` provides name→id lookup.
14. **Movement deltas tensor** (`vectorized_env.py:408, 676-700`): build `[action_dim, position_dim]` zero tensor; fill where actions have `type == "movement"` and a `delta` field.
15. **VTC program compilation** (`vectorized_env.py:409-418`): eight compiled programs — `action_writes`, `affordance_gates`, `interaction_progress`, `terminal_conditions`, `passive_depletions`, `modulations`, `threshold_cascades`, `reward_components`. All construct-once at env init.
16. **State tensor allocation** (`vectorized_env.py:420-438`): see table above.
17. **Items wiring** (`vectorized_env.py:439-477`): if `universe.items_catalog` exists, instantiate `ItemManager`, `InventoryState`, `ItemActionHandler`. The items system requires `compiled_vfs_profiles.item_profiles` — raises if missing. The handler is wired with command executor + VFS registry + meter_name_to_index + effect_manager + affordance_overrides.
18. **Affordance engine** (`vectorized_env.py:479-494`): instantiate with affordance tuple, num_agents, device, meter_index, modulation program, VFS registry, effects schema, command executor, effect_manager, item_manager (or `NullItemManager`), affordance_overrides.
19. **Exploration placeholder** (`vectorized_env.py:497`): `exploration_module = None`; set externally by population.
20. **Temporal state init** (`vectorized_env.py:500-511`): interaction_progress, last_interaction_affordance/position, time_of_day. Zero-out interaction_progress if temporal disabled.
21. **Affordance history** (`vectorized_env.py:513-521`): `_last_affordances`, `_affordance_streaks`, `_unique_affordances_count`, `_affordances_seen`.
22. **Initial affordance placement** (`vectorized_env.py:523-529`): either `randomize_affordance_positions()` or `_apply_configured_affordance_positions()`.

Six post-init injection points exist:
- `attach_runtime_registry(registry)` (`vectorized_env.py:531-533`)
- `set_exploration_module(exploration)` (`vectorized_env.py:535-545`)
- `set_affordance_positions(checkpoint_data)` (`vectorized_env.py:1431-1468`) for checkpoint restore
- `affordance_overrides` mutated by Effects DSL (shared dict between env, affordance_engine, effect_manager, item_handler)
- `vfs_registry` mutated by all writers
- `meters` mutated by every consumer

## Action masking detail

`get_action_masks` (`vectorized_env.py:917-1082`) builds the action mask in a precise order, each layer overlaying the previous:

1. **Base mask** (line 931): `ComposedActionSpace.get_base_action_mask(num_agents, device)`. Disabled actions are `False` for all agents.
2. **Item-specific masks** (lines 937-994):
   - GET masked when inventory full (any slot != -1).
   - GET masked when no item at agent position. **Per-agent Python loop with set comprehension over `item_manager.active_items.values()`** (lines 953-969) — O(N · num_items).
   - USE_SLOT_i / DROP_SLOT_i masked when slot is empty.
   - Custom item verbs (local/inventory): defer to `item_handler.compute_custom_action_masks`.
3. **Boundary masks** (lines 996-1029): for discrete grid substrates with position_dim >= 2, detect agents at top/bottom/left/right edges using `positions[:, 1] == 0` etc. Then resolve direction action IDs by inspecting `_movement_deltas[:, axis]` sign — `up_action_ids = torch.nonzero(deltas[:, 1] < 0)`. This is the only metadata-driven boundary masking; the comment "no hardcoded names" at line 1005 is accurate.
4. **3D Z-axis masks** (lines 1031-1050): if position_dim == 3 and substrate has `.depth`, mask Z-axis movement at floor/ceiling.
5. **INTERACT masking** (lines 1052-1073): INTERACT is valid only if the agent stands on an open affordance. Walks every affordance, checks operating hours via `_is_affordance_open(name)` (which respects `affordance_overrides`), then `substrate.is_on_position(positions, affordance_pos)`. `base_interact_mask` is preserved so config-disabled INTERACT stays disabled.
6. **Dead-agent override** (lines 1079-1080): `action_masks[dones] = False`. This is the LAST step and overrides every earlier check. The comment at line 1075 makes the ordering invariant explicit.

The complexity bound is `O(num_agents · num_affordances)` for the INTERACT step (per-affordance `is_on_position` check on the full agent batch) plus `O(num_agents · num_items)` for the GET-at-position check. Both can dominate at scale.

## Test landscape

`tests/test_townlet/unit/environment/` contains 27 test files (filenames only, not opened):

```
test_action_config_extension.py        test_meters.py
test_action_labels.py                  test_movement_deltas.py
test_action_masking.py                 test_movement_mask_bug.py
test_action_space.py                   test_observations.py
test_affordance_engine.py              test_pomdp_validation.py
test_affordances.py                    test_reward_calculator.py
test_checkpoint_validation.py          test_vectorized_env_level_metadata.py
test_compiled_effects_usage.py         test_vectorized_env.py
test_dac_engine.py                     test_vectorized_env_runtime.py
test_effect_observation.py             test_vfs_integration.py
test_engine_dynamic_sizing.py          test_vfs_type_validation.py
test_env_observation_activity.py       test_vision_bounds.py
test_gridnd_action_support.py
test_item_delay_tick.py
test_load_global_actions.py
```

Observations from file inventory alone:

- **No `test_reward_strategies.py`** — consistent with the claimed deletion of 349 lines under commit `bfde7c8a`.
- **`test_dac_engine.py`** exists as the canonical DAC test surface, alongside the smaller `test_reward_calculator.py` for the facade.
- **`test_affordance_engine.py` and `test_affordances.py`** both exist — likely a unit-vs-integration split or legacy carryover.
- **`test_action_*` files** are split across action_config, action_labels, action_masking, action_space — one per concern, suggesting the action stack is the most tested area of the subsystem.
- **POMDP, vision bounds, and grid-N-D action support** each have dedicated test files, matching the strong validation logic visible in `vectorized_env.py:218-272` and `action_labels._filter_labels_for_substrate`.

## Verify or refute (from CLAUDE.md)

1. **`reward_strategy.py` deleted.** **Confirmed.** `find src -name 'reward_strategy*'` returns nothing. Git: commit `4d694d73 refactor(dac): delete obsolete reward_strategy.py`. However the message states `Deleted: src/townlet/environment/reward_strategy.py (234 lines)` and `git show --stat 4d694d73` shows `1 file changed, 234 deletions(-)`. **CLAUDE.md claims "583 lines removed", which is incorrect** — the deletion was 234 lines.
2. **All reward strategy classes gone from environment/.** **Confirmed.** `grep -rn "RewardStrategy" src/townlet` returns no hits in any `*.py`. The DAC engine is the sole reward producer. `reward_calculator.py` is a 53-line thin facade that pulls intrinsic from `exploration_module`, builds the reward kwargs, and delegates to `env.vtc_reward_program.apply(reward_backend=env.dac_engine, ...)`.
3. **Old reward strategy tests deleted (claimed 349 lines removed).** **Confirmed.** Commit `bfde7c8a test(dac): remove obsolete reward strategy tests` shows `tests/test_townlet/unit/environment/test_reward_strategies.py | 349 ---------------------`. The 349 figure matches exactly. The current test directory contains no `test_reward_strategies.py`; only `test_reward_calculator.py` remains.

## Observation encoder (extra detail)

`ObservationEncoder` (`observation_encoder.py:17-335`) builds the observation tensor in two passes:

**Pass 1: `_sync_observation_primitives_to_vfs()`** (lines 122-131) calls eight helpers, one per primitive field:

- `_sync_grid_observation_to_vfs` (line 133): if there is an `obs_grid_encoding` field, calls `env.substrate._encode_full_grid(positions, affordances)` (or `encode_observation`) and writes into VFS variable `obs_grid_encoding`. In partial-observability mode, writes zeros — the global grid is hidden.
- `_sync_local_window_observation_to_vfs` (line 151): inverse of the above. If POMDP, calls `env.substrate.encode_partial_observation(positions, affordances, vision_range=env.vision_radius)`. Otherwise zeros.
- `_sync_position_observation_to_vfs` (line 186): delegates to `env._encode_position_observation()` which in turn searches the substrate for `_encode_position_features`, `encode_position_features`, `encode_observation`, or `normalize_positions` in that order (`observation_encoder.py:307-335`). Raises if substrate has position_dim > 0 but no encoder.
- `_sync_velocity_observation_to_vfs` (line 171): writes `env._velocity` (set in action executor) into the `obs_velocity` VFS variable.
- `_sync_meter_observation_to_vfs` (line 201): special-cased — writes `env.meters` directly into VFS without going through `_set_observation_variable` (so no `_ensure_agent_observation_shape` guard).
- `_sync_affordance_observation_to_vfs` (line 218): builds a one-hot encoding plus a "no-affordance" slot (`num_affordance_types + 1` dims, line 288); for each affordance, marks agents standing on it via `substrate.is_on_position`. The fallback "none" slot fires when no row sum is 1.
- `_sync_effect_observation_to_vfs` (line 230): builds an `effect_observation_slots * 3` tensor (effect_index, time-remaining-fraction, active-flag) per agent, via `env._build_effects_observation` (`vectorized_env.py:861-886`). The 3-channel layout (index, remaining/total, 1.0) is hardcoded.
- `_sync_temporal_observation_to_vfs` (line 242): 4-dim tensor with `[sin(2π·t/T), cos(2π·t/T), day_progress, is_night]` (lines 254-282). Hard-asserts `dims == 4` at line 257.

**Pass 2: `_get_observations` body** (lines 24-46): walks `env.observation_spec.fields` and for each calls `_build_observation_field_from_vfs`. The `obs_vfs` field is the catch-all that reads through `build_vfs_observation(registry, vfs_observation_spec, batch_size=num_agents, agent_item_inventory=...)`. Other fields are agent-scoped VFS variables and use a synthetic `VFSObservationSpec` with a single `agent_var` (lines 68-93). All field outputs are passed through `_ensure_agent_observation_shape` which insists on `(num_agents, dims)` and raises otherwise (line 109). Final step: `torch.cat(outputs, dim=1)` then optional element-wise mask multiply by `observation_activity.active_mask` (lines 36-44).

**Implication:** there is no observation tensor that exists outside of the VFS pipeline. Anything an agent can see has been published to a named variable. This makes the observation surface introspectable, but also means observation latency is proportional to the number of VFS sync helpers plus the number of registered fields.

## Action labels (extra detail)

`action_labels.get_labels(preset, custom_labels, substrate_position_dim)` (`action_labels.py:169-261`) is the public construction API. It is *not* called from `vectorized_env.py` at runtime — the env rehydrates labels from `level.action_metadata.labels` (a compile-time map) at `vectorized_env.py:160-164`. `get_labels` and `_filter_labels_for_substrate` (`action_labels.py:264-359`) are used during compilation (`townlet/universe/compilers/actions.py:13`).

The remapping behaviour is non-obvious: `_filter_labels_for_substrate` reindexes labels per substrate dimensionality:

- 0D aspatial: 2 actions (INTERACT=0, WAIT=1), the canonical IntEnum is *not* respected — INTERACT lives at index 0 here, not 4.
- 1D: 4 actions; INTERACT moves from canonical 4 to slot 2.
- 2D: 6 actions; `_filter` swaps the canonical Y-axis ordering — slot 0 becomes `MOVE_Y_POSITIVE` (UP) and slot 1 becomes `MOVE_Y_NEGATIVE` (DOWN), reversing the IntEnum order.
- 3D: 8 actions with the same Y-swap.
- N≥4: generated `D{i}_NEG` / `D{i}_POS` labels at slots `0..N-1` and `N..2N-1`, with INTERACT at `2N` and WAIT at `2N+1`. Presets are *ignored* for N≥4 because "no canonical 4D directions" exist (comment at line 329).

This per-dim remapping is the canonical source of the "action_dim varies by substrate" rule that `ComposedActionSpace.action_dim` then preserves *across curriculum levels at fixed dim* for checkpoint transfer.

## Public API surface

`src/townlet/environment/__init__.py` is one line: `"""Townlet: GPU-native sparse reward system."""`. There are no re-exports. Consumers import concrete modules directly:

- `townlet.environment.vectorized_env.VectorizedHamletEnv` (the primary export, via classmethod `from_universe`)
- `townlet.environment.dac_engine.DACEngine` (constructed inside the env; not imported externally)
- `townlet.environment.action_config.ActionConfig`, `ActionSpaceConfig`, `load_global_actions_config`
- `townlet.environment.action_builder.ComposedActionSpace`, `ActionSpaceBuilder`
- `townlet.environment.action_labels.ActionLabels`, `CanonicalAction`, `PRESET_LABELS`, `get_labels`
- `townlet.environment.affordance_config.AffordanceConfig`, `AffordanceEffect`, `AffordanceCost`, `AffordanceConfigCollection`
- `townlet.environment.affordance_engine.AffordanceEngine`, `CompiledAffordance`, `NullEffectManager`
- `townlet.environment.affordance_layout.iter_affordance_positions`, `AffordancePositionProvider`
- `townlet.environment.substrate_action_validator.SubstrateActionValidator`, `ValidationResult`
- `townlet.environment.observation_encoder.ObservationEncoder`
- `townlet.environment.reward_calculator.RewardCalculator`
- `townlet.environment.null_managers.NullItemManager`
- `townlet.environment.env_factory.from_universe`

The lack of `__all__` and `__init__` re-exports means every consumer pins to a concrete submodule path; refactoring file layout will ripple. (Concern below.)

## Dependencies

**Inbound** (who imports `townlet.environment.*` — `grep -rl "VectorizedHamletEnv" src/townlet` plus follow-up search):

- `townlet.population.base`, `townlet.population.vectorized` — `VectorizedPopulation` constructs and drives the env, sets `env.exploration_module`, attaches runtime registry.
- `townlet.demo.runner`, `townlet.demo.live_inference` — demo/visualization harnesses.
- `townlet.universe.compiled` — back-reference for typing.
- `townlet.universe.compilers.actions` — imports `PRESET_LABELS, CanonicalAction` from `action_labels` to materialize compiled action labels.
- Tests in `tests/test_townlet/unit/environment/` and `tests/test_townlet/integration/` (`test_vectorized_env*`, `test_dac_engine`, `test_affordance_engine`, etc.).

**Outbound** (`grep "^from townlet" src/townlet/environment/*.py`):

- `townlet.config.actions_config` — parse-time DTOs (`ActionsConfig`, `ActionsConfigRoot`)
- `townlet.config.agent_config.DriveConfig`
- `townlet.config.drive_as_code.DriveAsCodeConfig`
- `townlet.config.effects_config.CommandConfig`
- `townlet.config.stratum_config.SubstrateConfig`
- `townlet.effects.{compiler,executor,parser,schema}` — `CommandCompiler`, `CommandExecutor`, `ExecutionContext`, `CommandParser`, `CommandNode`. Also from inside `__init__` of `vectorized_env`: `townlet.effects.manager.EffectManager` (lazy import at `vectorized_env.py:335-336`).
- `townlet.items` — `InventoryState`, `ItemActionHandler`, `ItemManager`
- `townlet.substrate.{base,continuous,factory}` — `SpatialSubstrate`, `ContinuousSubstrate`, `SubstrateFactory`
- `townlet.universe.dto` — `MeterMetadata`, `RuntimeActionSpace`
- `townlet.vfs.{evaluator,observation_builder,registry,schema,vtc}` — `VFSEvaluator`, `EvaluationMode`, `VFSObservationSpec`, `build_vfs_observation`, `VariableRegistry`, `WriteSpec`, and the eight `VTC*Program`s plus their `compile_vtc_*` builders. The compiled VTC programs are: `action_writes`, `affordance_gates`, `interaction_progress`, `modulations`, `passive_depletions`, `reward_components`, `terminal_conditions`, `threshold_cascades`.

The env's outbound surface spans **six subsystems**: config, effects, items, substrate, universe, vfs. This is the central wiring layer.

## Reset path (`reset()`)

`VectorizedHamletEnv.reset()` (`vectorized_env.py:728-822`) is a separate worker from `step()`:

1. **Affordance/agent positions** (lines 736-747): if `randomize_affordances`, sample affordance + agent positions *together* (the BUG-15 fix at lines 1470-1559 — sample both classes from the same call to ensure no collisions). Otherwise call `_apply_configured_affordance_positions()` and spawn agents independently (potential collision; flagged as a TODO at line 746).
2. **Velocity reset** (lines 749-754): zeros.
3. **Meters** (line 757): broadcast `initial_meter_values` over `num_agents` and `.clone()`.
4. **Dones, step_counts, global_tick, intrinsic_weights** (lines 759-762): reset to defaults.
5. **VFS episode-scoped reset** (line 763): `vfs_registry.reset_episode_scoped()`. Important — `step()` resets only tick-scoped state; episode-scoped state lives across ticks within an episode.
6. **Temporal reset** (lines 766-770): zero `time_of_day`, `interaction_progress`, `last_interaction_affordance`, `last_interaction_position`.
7. **Affordance history reset** (lines 772-776).
8. **`affordance_overrides.clear()`** (line 778). Episode-scoped — operator/affordance toggles from Effects DSL do not persist.
9. **Effect manager reset** (lines 780-786): `reset_scheduler(current_tick=0)`, plus a defensive `cancel_scheduled_for_entity` per agent in case reset is called mid-episode.
10. **VFS evaluator reset** (lines 788-790): clears temporal history (`vfs_evaluator.reset()`) so temporal VFS ops don't leak across episodes.
11. **Item state reset** (lines 793-796): `item_manager.reset_state()`, `item_inventory.reset()`.
12. **Initial item spawn** (lines 798-820): if items present and `level.items_appearance` is configured, call `item_manager.spawn_initial_items(...)` with the substrate grid_size. Only works for grid substrates (lines 803-809); silently skips for continuous/aspatial. The temporal context tensor is only passed when temporal mechanics are enabled.
13. **Return** (line 822): observations from `_observation_encoder._get_observations()`.

Observations:
- The "reset is hard-coded for grid substrates when items exist" branch at lines 803-820 means items + continuous substrates silently skip initial spawning. A `warnings.warn` or an explicit raise would be safer.
- The reset does *not* reset `_last_reward_components` — stale DAC component tensors from the previous episode persist on `env` until the first `step()` overwrites them. Not a correctness bug because they're info-only, but a possible source of confusion in tests.

## DAC strategy reference (line citations)

Modifier compilation: `_compile_modifiers` `dac_engine.py:85-152`. Source resolution handles two schemas — `ModifierConfig` with `bar`/`variable` fields (DAC), and `RangeMultiplierModifier` with a single `source` string (agent-config). Range evaluation uses sorted ranges and reverse-walked `torch.where(in_range, multiplier, fallback)` starting from the last range as the default (lines 138-145).

Extrinsic strategies (`_compile_extrinsic`, `dac_engine.py:154-501`):

| Type                                   | Line | Formula                                                |
|----------------------------------------|------|--------------------------------------------------------|
| `multiplicative`                       | 162  | `base * prod(meters[bars])`                            |
| `constant_base_with_shaped_bonus` (DAC)| 191  | `base_reward + Σ scale·(bar-center) + Σ weight·vfs[v]` |
| `constant_base_with_shaped_bonus` (agent.yaml) | 230 | `base + Σ weight·transform(bar)` where `transform ∈ {linear, quadratic, exponential}` |
| `additive_unweighted`                  | 268  | `base + Σ meters[bars]`                                |
| `weighted_sum`                         | 296  | `base + Σ scale·meters[bar]`                           |
| `polynomial`                           | 327  | `base + Σ scale·clamp(meters[bar],min=0)^center`       |
| `threshold_based`                      | 362  | `base + Σ (meters[bar]≥center ? scale : 0)`            |
| `aggregation`                          | 396  | `base + min(meters[bars])` (hardcoded min)             |
| `vfs_variable`                         | 428  | `base + Σ weight·vfs[var]`                             |
| `hybrid`                               | 457  | per bonus: `scale·bar` if `|center|<1e-6` else `scale·(bar-center)` |

Shaping bonuses (`_compile_shaping`, `dac_engine.py:503-886`):

| Type                  | Line | Key kwargs                                                      |
|-----------------------|------|-----------------------------------------------------------------|
| `approach_reward`     | 512  | `agent_positions`, `affordance_positions`                       |
| `completion_bonus`    | 549  | `last_action_affordance` (list[str\|None])                      |
| `efficiency_bonus`    | 585  | `meters`                                                        |
| `state_achievement`   | 617  | `meters` (multi-condition AND)                                  |
| `streak_bonus`        | 658  | `affordance_streak: dict[str, [N] long]`                        |
| `diversity_bonus`     | 691  | `unique_affordances_used: [N] long`                             |
| `timing_bonus`        | 716  | `current_hour`, `last_action_affordance` (wraps midnight)       |
| `economic_efficiency` | 765  | `meters` (uses money bar)                                       |
| `balance_bonus`       | 797  | `meters` (imbalance = max-min across listed bars)               |
| `crisis_avoidance`    | 831  | `meters` (strictly-above threshold)                             |
| `vfs_variable`        | 863  | reads `vfs_registry[variable]`; raises if missing               |

Every shaping closure zero-initializes a `[N]` tensor and returns it when its required kwarg is missing, except `vfs_variable` which intentionally lets `KeyError` propagate (line 873).

Composition path: `extrinsic + intrinsic·base_weight·(prod of intrinsic.apply_modifiers) + Σ shaping` (`dac_engine.py:965-998`). The intrinsic weight chain is *separate* from any modifier chains applied inside the extrinsic strategy itself — extrinsic strategies can each `apply_modifiers` individually (lines 178, 219, 257, 283, 313, 348, 382, 414, 443, 483).

## Patterns observed

- **GPU-native vectorisation, with caveats.** All per-tick state (`positions`, `meters`, `dones`, `step_counts`, `interaction_progress`, `_velocity`, `intrinsic_weights`) is `torch.Tensor` on `self.device`. Bar/effect updates, VTC programs, action masks (mostly), DAC extrinsic/intrinsic, and most shaping bonuses are tensor-vectorized via `torch.where`. **However, several hot paths fall back to per-agent Python loops:**
  - `_execute_affordance_effects` loops `for agent_idx in torch.where(agent_mask)[0]:` and executes Effects commands one agent at a time (`affordance_engine.py:538-555`).
  - `action_executor` dispatches GET/USE/DROP and custom item verbs via per-agent `for agent_idx in torch.where(...)[0]:` (`action_executor.py:73-134`).
  - `get_action_masks` walks every active item to check item-at-position (`vectorized_env.py:954-969`) and walks every agent's effect slots (`_build_effects_observation`, `vectorized_env.py:878-885`).
  - `_update_affordance_tracking` is a per-agent Python loop because affordance names are strings (`vectorized_env.py:1346-1371`).
  - DAC `completion_bonus` and `timing_bonus` build a tensor from a Python list comprehension over `last_action_affordance` strings (`dac_engine.py:572-577, 747-751`).
  These costs scale linearly with `num_agents` and dominate for small batches; they are the obvious profiling targets if throughput becomes a bottleneck.
- **Compile-once, execute-many.** Every static reward/affordance/transition rule is compiled to a `VTC*Program` or a captured Python closure at env construction (`vectorized_env.py:409-418` for the eight VTC programs; `dac_engine.py:73-83` for DAC compilation). Runtime hot-loop is then plain tensor algebra plus dispatch. This is the "compiled graph" architecture the docs describe — Python-closure compilation, not torch.jit.
- **Facade + delegate split.** `VectorizedHamletEnv` retains thin facade methods (`_get_observations`, `_calculate_shaped_rewards`, `_execute_actions`, `_handle_interactions`, `_handle_instant_interactions`, etc. at `vectorized_env.py:853-1311`) that delegate to `ObservationEncoder`/`ActionExecutor`/`RewardCalculator`. The facades exist so that test code and previously-built callers don't break; the real work lives in the dedicated classes.
- **Null-object pattern, but inconsistent.** `NullItemManager` (in `null_managers.py`) is a proper null object — `spawn_item` raises, lifecycle methods no-op. `NullEffectManager` (defined inside `affordance_engine.py:568-572`) only stubs `spawn_effect` and would `AttributeError` on any other method (e.g., `tick`, `cancel_scheduled_for_entity`). The two null implementations live in different modules and have different completeness; the `affordance_engine.py` placement is awkward.
- **No-defaults enforcement.** The codebase consistently raises `ValueError` rather than supplying defaults when a config value is missing (examples: `vectorized_env.py:96` for `device`, `121-123` for `enabled_affordances`, `132-136` for `day_length`, `156-157` for compiled action labels, `170-176` for `experiment_name`, `218-262` for POMDP feasibility, `359` for `effects_schema`). Matches the project's "no defaults" rule.
- **Effects-DSL as scripting layer for affordances.** The affordance engine compiles per-lifecycle-stage Effects programs (parsed by `CommandParser`, compiled by `CommandCompiler`, executed by `CommandExecutor`). The bar dict is shared by reference, so commands mutate meters in place. Effects can also spawn delayed work via the scheduler, spawn items, and gate VFS writes.
- **VFS-as-bus.** Observation primitives (grid, local window, position, velocity, meters, affordance, effects, temporal) are *published into the VFS registry* before observation assembly (`observation_encoder.py:122-282`). This means VFS expressions can reference observation values, and the same registry that backs reward variables also backs observation tensors. The pattern keeps observation/reward/transition logic uniformly addressable, but it does mean the registry is the single source of truth for nearly every tensor in the system.

## Compiled VTC programs (eight)

Compiled at env construction (`vectorized_env.py:409-418`) from level-scoped sources:

| Program                             | Source                                           | Tick-loop callsite                      |
|-------------------------------------|--------------------------------------------------|-----------------------------------------|
| `VTCActionWriteProgram`             | `action_space.actions` (writes field)            | `_apply_vtc_action_writes` (line 1224)  |
| `VTCAffordanceGateProgram`          | `level.affordances.affordances`                  | `_is_affordance_open` (line 612)        |
| `VTCInteractionProgressProgram`     | `level.affordances.affordances`                  | `_advance_vtc_interaction_progress` (action_executor.py:239) |
| `VTCTerminalConditionProgram`       | `bars_config.meters`                             | `_apply_vtc_terminal_conditions` (line 1272) |
| `VTCPassiveDepletionProgram`        | `bars_config.meters`                             | `_apply_vtc_passive_depletion` (line 1243)   |
| `VTCModulationProgram`              | `level.affordances.modulations`                  | `affordance_engine._compute_affordance_multiplier` |
| `VTCThresholdCascadeProgram`        | `bars_config.cascades`                           | `_apply_vtc_threshold_cascades` (line 1258)  |
| `VTCRewardProgram`                  | `level.drive`                                    | `reward_calculator._calculate_shaped_rewards` |

Each program is the compile-time representation of one rule family. `step()` invokes seven of the eight per tick (`VTCInteractionProgressProgram` only fires when multi-tick affordances are active and an INTERACT happened or progression is pending — `action_executor.py:153-156`). Most program `.apply()` methods consume `bars_state` and `active_mask` and return a partial dict of updates; the env applies them back to `self.meters` or `self.vfs_registry` via `_set_vtc_bar_value`/`set_engine_value`.

The single-program-per-rule-family split means a new rule family (e.g., a future "energy regeneration" rule) would require a new VTC program, a new compiler emit step, and a new env construction line. The pattern is regular but not flexible to runtime extension.

## Schema-shape adapters (compatibility shims)

The runtime carries a number of small adapter functions that smooth over the parse-time DTOs vs runtime DTOs split:

- `env_factory._normalize_vfs_type` (`env_factory.py:20-27`) — maps `int|float` → `scalar`, validates against the canonical set `{scalar, bool, tensor1d, tensor2d, tensor3d, tensorNd, agent_ref, item_ref}`.
- `env_factory._build_bar_index_map` (`env_factory.py:30-32`) — flattens `MeterMetadata` to `dict[name, index]`.
- `env_factory._resolve_deployable_affordances` (`env_factory.py:35-53`) — accepts either affordance *names* or *ids* in the enabled list.
- `affordance_engine._iter_costs` / `_cost_fields` (`affordance_engine.py:450-471`) — handles three different cost representations (Pydantic models with `.meter`/`.amount`, dict with `meter`/`amount` keys, single-entry dict).
- `affordance_engine._get_meter_idx` (`affordance_engine.py:473-489`) — explicit-error wrapper around `meter_name_to_idx` lookup with context-aware error messages.
- `vectorized_env._build_action_space_from_runtime_artifact` (`vectorized_env.py:645-674`) — rebuilds `ComposedActionSpace` and `ActionConfig` objects from the compiler's `RuntimeActionSpace`. Casts `WriteSpec` entries.
- `vectorized_env._position_to_tensor` (`vectorized_env.py:568-599`) — accepts tensor / dict `{q, r}` / list / tuple / scalar Number; validates dim against `substrate.position_dim`.

The runtime appears to have absorbed multiple historical schema generations. Each adapter is justified individually, but the cumulative result is that "the env can consume *almost any* config shape" — useful for transition periods, but at odds with the project's stated "no defaults / break things" rule. A future cleanup pass could collapse most of these by requiring the universe compiler to emit a single canonical runtime shape.

## Concerns

- **Per-agent Python loops in hot paths.** Listed under Patterns. For 1-16 agents these are invisible; for 256+ they dominate. `affordance_engine.py:538-555`, `action_executor.py:73-134, 92-99, 110-118, 127-134`, `vectorized_env.py:954-969, 878-885, 1346-1371`. None of them are clearly batched.
- **CLAUDE.md line-count claim is wrong.** "Old System ... `src/townlet/environment/reward_strategy.py` → DELETED (583 lines removed)" (CLAUDE.md). Actual deletion was 234 lines (git commit `4d694d73`). Test deletion of 349 lines is correct. Worth fixing the doc; it's the kind of number people quote.
- **Reward `reward_calculator.py:41-48` indirection.** The reward path is `RewardCalculator → env.vtc_reward_program.apply(reward_backend=env.dac_engine, ...)`. The DACEngine is no longer called directly by the calculator — there's a VTC program wrapper. This is documented nowhere in `dac_engine.py` and obscures the contract. A `dac_engine.calculate_rewards(...)` call would be clearer; the VTC wrapper appears to add little here.
- **`AffordanceConfig` in `affordance_config.py` is largely vestigial.** The runtime engine (`affordance_engine.py`) operates on the v2.1 `AffordanceParamConfig` produced by the universe compiler and uses `hasattr(aff, "interactions")` to detect the schema (`affordance_engine.py:106`). Pure runtime callers don't materialize `AffordanceConfig`. The two-schema reality is not flagged in either module's docstring beyond a single comment line. Future readers will be confused.
- **`NullEffectManager` is incomplete and mis-located.** Lives at the bottom of `affordance_engine.py:568-572`, only stubs `spawn_effect`, and would `AttributeError` on `tick`, `scheduler`, `cancel_scheduled_for_entity`, etc. — all of which `ExecutionContext` may dereference. The `affordance_engine.py` constructor uses `effect_manager or NullEffectManager()` (line 90), so when an env is constructed without an effect manager and an affordance triggers a non-`spawn_effect` Effects command, the failure will look like an AttributeError rather than the explicit RuntimeError that `NullItemManager` would give. Either move it to `null_managers.py` and complete it, or always require a real `EffectManager`.
- **`VectorizedHamletEnv.__init__` is 460 lines (vectorized_env.py:73-529).** It does substrate construction, action-space rehydration, VFS registry construction, VFS evaluator wiring, DAC engine wiring, effects construction, items construction, affordance engine construction, VTC compilation, state-tensor allocation, and affordance-position layout. Nothing wrong functionally, but it's one of the largest constructors in the codebase and any change ripples. An architecture-quality pass would suggest extracting subsystem builders.
- **`__init__.py` exports nothing.** Every consumer pins to a concrete file path. Renaming a file (e.g., splitting `dac_engine.py`) breaks every import site. A curated public surface in `townlet/environment/__init__.py` would help.
- **`get_action_masks` is 165+ lines** (`vectorized_env.py:917-1082`) and grew organically — substrate-dim checks (2D, 3D, NDim), item-aware GET/USE/DROP masking, INTERACT-on-affordance masking, dead-agent override. Hard to test in isolation; not split out into `ActionExecutor` even though most of its logic is action-shaped.
- **`enable_temporal_mechanics` gating sprawls across files.** It's checked in `vectorized_env.py` (reset, step, build VFS temporal context), `action_executor.py` (`_handle_interactions` switching between instant and multi-tick), `observation_encoder.py` (`_build_temporal_observation`). The cross-cutting flag is correctly threaded but is a likely site for subtle bugs when adding new temporal-aware code.

## State tensors owned by the env

For reference (all initialized at `vectorized_env.py:421-437` and re-initialized at `reset()`):

| Tensor                                | Shape                              | Dtype                            | Purpose                                                |
|---------------------------------------|------------------------------------|----------------------------------|--------------------------------------------------------|
| `positions`                           | `[N, position_dim]`                | `substrate.position_dtype`        | Agent locations                                        |
| `_velocity`                           | `[N, position_dim]`                | `float32`                        | Per-step delta position                                |
| `meters`                              | `[N, meter_count]`                 | `float32`                        | Normalized [0,1] bar values                            |
| `dones`                               | `[N]`                              | `bool`                           | Terminal flag                                          |
| `step_counts`                         | `[N]`                              | `long`                           | Per-agent step counter                                 |
| `global_tick`                         | scalar `int`                       | —                                | Independent of step_counts[0]                          |
| `intrinsic_weights`                   | `[N]`                              | `float32`                        | Effective intrinsic weight after modifiers             |
| `interaction_progress`                | `[N]`                              | `long`                           | Multi-tick interaction progress                        |
| `last_interaction_position`           | `[N, position_dim]`                | `position_dtype`                 | Where last multi-tick interaction started              |
| `_unique_affordances_count`           | `[N]`                              | `long`                           | DAC shaping diversity input                            |
| `_affordance_streaks` (dict)          | `{name: [N] long}`                 | —                                | DAC shaping streak input, lazily allocated             |

Python-side state:
- `last_interaction_affordance: list[str | None]` length `N`
- `_last_affordances: list[str | None]` length `N`
- `_affordances_seen: list[set[str]]` length `N`
- `_last_reward_components: dict[str, torch.Tensor]` (last computed DAC components)
- `affordance_overrides: dict[str, bool]` (runtime affordance availability toggle, mutated by Effects DSL)
- `affordances: dict[str, torch.Tensor]` (name → position tensor)

## Selected hot-path code paths

A few concrete code paths worth quoting verbatim for downstream review.

**Action mask boundary masking is metadata-driven (vectorized_env.py:1005-1029):**

```python
# Mask invalid movements using movement deltas (metadata-driven, no hardcoded names)
deltas = self._movement_deltas
up_action_ids    = torch.nonzero(deltas[:, 1] < 0, as_tuple=False).squeeze(1)
down_action_ids  = torch.nonzero(deltas[:, 1] > 0, as_tuple=False).squeeze(1)
left_action_ids  = torch.nonzero(deltas[:, 0] < 0, as_tuple=False).squeeze(1)
right_action_ids = torch.nonzero(deltas[:, 0] > 0, as_tuple=False).squeeze(1)
```

This is the canonical pattern for "find the action IDs by their declared movement deltas, not by name". It is the reason the codebase can support arbitrary `D{i}_NEG/D{i}_POS` action naming in N-D substrates.

**Modifier evaluation uses reverse-walked nested `torch.where` (dac_engine.py:138-145):**

```python
ranges = sorted(config.ranges, key=lambda r: r.min)
multiplier = torch.full_like(source_value, ranges[-1].multiplier, dtype=torch.float32)
for r in reversed(ranges[:-1]):
    condition = (source_value >= r.min) & (source_value < r.max)
    multiplier = torch.where(condition, r.multiplier, multiplier)
```

This is the canonical "GPU lookup table" idiom in the codebase. It implies modifiers are *interval lookups* over a single bar/variable, not arbitrary predicates. Multi-source modifiers would require a different shape.

**Reward routing through VTC wrapper (reward_calculator.py:41-48):**

```python
total_rewards, intrinsic_weights, components = env.vtc_reward_program.apply(
    reward_backend=env.dac_engine,
    step_counts=env.step_counts,
    dones=env.dones,
    meters=env.meters,
    intrinsic_raw=intrinsic_raw,
    reward_context=kwargs,
)
```

The reward path is mediated by a VTC program rather than a direct DAC engine call. This is a recent architectural decision (the VTC program is compiled at `vectorized_env.py:418`). The DAC engine is now a "backend" passed in as an argument, suggesting future reward backends may exist.

## Cross-cutting facade methods

`VectorizedHamletEnv` exposes a number of methods that exist purely as façades — they forward to the dedicated executor / encoder / calculator. They are retained because external callers (tests, demo runners, population) pinned to the older signatures during the extraction. Catalog:

| Facade                                                | Forwards to                                                       |
|-------------------------------------------------------|-------------------------------------------------------------------|
| `_get_observations` (`vectorized_env.py:853`)         | `_observation_encoder._get_observations()`                        |
| `_build_affordance_encoding` (line 857)               | `_observation_encoder._build_affordance_encoding(dims)`           |
| `_encode_position_observation` (line 888)             | `_observation_encoder._encode_position_observation()`             |
| `_execute_actions` (line 1220)                        | `_action_executor._execute_actions(actions)`                      |
| `_handle_interactions` (line 1301)                    | `_action_executor._handle_interactions(mask)`                     |
| `_handle_instant_interactions` (line 1305)            | `_action_executor._handle_instant_interactions(mask)`             |
| `_calculate_shaped_rewards` (line 1309)               | `_reward_calculator._calculate_shaped_rewards()`                  |
| `_build_effects_observation` (line 861)               | self-contained; reads `effect_manager.get_observable_agent_effects` |
| `_encode_velocity_observation` (line 892)             | self-contained; returns `_velocity`                               |

`_build_effects_observation` and `_encode_velocity_observation` survived extraction because they read env-owned tensors (`effect_observation_slots`, `_velocity`). Future refactors could push them into the observation encoder.

## Open questions

- The `aggregation` extrinsic strategy is hardcoded to `min` (`dac_engine.py:411`) despite the docstring suggesting `min/max/mean/product`. Is the missing `operation` field intentional, or is this an incomplete implementation? If intentional, the docstring lies; if not, this is a feature gap.
- `agent.yaml` vs `drive_as_code.yaml` config shapes: DAC has two code paths in `_compile_extrinsic` for `constant_base_with_shaped_bonus` (`dac_engine.py:196` vs `230`) and the modifier compilation special-cases `RangeMultiplierModifier.source` vs `ModifierConfig.bar/variable`. Which schema is canonical going forward? The pre-release "delete the old" rule suggests one should die.
- The "GPU-native" claim is partially aspirational: the affordance Effects execution and item action dispatch are per-agent Python loops. Is the project intentionally accepting this cost (because affordances are sparse events), or is batched Effects execution planned?
- `set_affordance_positions` (`vectorized_env.py:1431`) is the only callsite that requires checkpoint `position_dim`; `get_affordance_positions` (`vectorized_env.py:1403`) produces it. Are old checkpoints fully purged, or does this branch still get exercised?
- `reward_calculator.py` routes through `env.vtc_reward_program.apply(reward_backend=env.dac_engine, ...)`. What does `VTCRewardProgram` add over a direct `DACEngine.calculate_rewards` call? (Answer is in SG2's territory but matters for SG4's contract.)
