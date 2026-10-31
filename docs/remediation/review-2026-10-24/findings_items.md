# Findings — items (Universe-as-Code part B: items, affordances, meters/bars, rewards/DAC)

Reviewer: items seam. Date: 2026-10-24. All reproductions run against `fix/episode-lane-accounting`
HEAD (a44b470f) with `use_cache=False` unless the finding is about the cache. Scripts live in
`/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/items/` (`h.py` harness; `p1_items_obs.py`, `p2_on_drop.py`,
`p3_dto_refusals.py`, `p4_zero_aff.py`, `p5_natural.py`, `p6_spawn_item_pos.py`, `p7_dead_agent.py`,
`p8_two_aff.py`, `p9_multitick.py`, `p10_gridnd_items.py`, `p11_l3.py`, `p12_misc.py`, `p13_more.py`,
`dac_formula.py`). Pack copies used by the probes are under `.../items/packs/<name>/` (whole-pack
copies of `configs/test/items_smoke`, `configs/reference/model_pack`, `configs/test/gridnd_4d_pack`).

## Backlog adjudication

| id | disposition | evidence (file:line, command, 1-line output) |
|---|---|---|
| hamlet-17a7f03bc9 (broken tool vs empty hand both 0.0) | **STILL LIVE** (the filed scenario is a *held* tool) | `p1_items_obs.py`: item-arena `variable_element` row for `medical.durability` reads `presence=1 value=0.000` when a world-resident medkit's durability is written to 0.0, and `presence=0` when no item occupies the slot — absence IS a presence feature now (`token_publishers.py:1060-1073`). But after `GET` of the (exclusive) medkit the same row reads `presence=0 value=0.000` because `lift_item` removes it from `active_items` (see 4b931faaf4). Output: `after GET (held, durability 0): item row presence=0 carried=0 | durability ve presence=0 value=0.000`. A held broken tool and an empty hand still observe identically. The mechanism that would close it (presence bit per item-arena slot) exists and works for world-resident items; it is defeated by 4b931faaf4. |
| hamlet-1b9af9088c (spawn_item unreachable end-to-end) | **STILL LIVE** | (1) `config/effects_config.py:99` `position: str \| None` — `CommandConfig(spawn_item="apple", position=[1,2])` → `Input should be a valid string` (`p3_dto_refusals.py`). (2) No production context carries `agent_positions`: `affordance_engine.py:477-487`, `items/action_handlers.py:108-119`, `vectorized_env.py:1092-1097` (`effect_manager.tick(...)` without `agent_positions`). `p6_spawn_item_pos.py` (items_smoke copy, `energy_station.on_start: [spawn_item: apple, position: target]`, INTERACT): `position=target: ValueError: agent_positions and target_index required for position 'target'`; `position=self: ValueError: agent_positions and self_index required`; `position` omitted: `ValueError: Invalid position: None` (compiles, dies at first INTERACT). (3) `items/manager.py:271-282` `random` strategy still hardcodes `(dx, dy)`. Bonus: `docs/config-schemas/items.md:449` teaches `position: "target.position"`, which is refused at compile (`TypeCheckError Path 'target.position' not found in schema`). |
| hamlet-266a0a41f0 (interaction progress unobservable, undeclarable) | **STILL LIVE** | `p11_l3.py` on `default_curriculum/L3_temporal_mechanics`: `vfs vars with 'progress': []`, `token filler refs mentioning progress: []`; `interaction_progress` has no VFS variable and no token binding (only `env.interaction_progress`, `vectorized_env.py:339`). `uv run pytest tests/test_townlet/integration/test_temporal_mechanics.py -k progress` → `4 passed` (the test that asserts NOT observable still passes). Still latent in shipped packs: `multi_tick affordances in L3: []`. |
| hamlet-45f501e15b (`max_items_per_agent: 0` nullifies catalog) | **STILL LIVE** | `universe/raw_configs_v21.py:169-170` `if items is not None and (items.max_items_in_world == 0 or items.max_items_per_agent == 0): items = None`. `p3_dto_refusals.py` (items_smoke copy, `max_items_per_agent: 0`): compile fails with the misleading downstream error `[UAC-RES-ITEM] .../levels/L0_smoke/items.yaml:3 - Item appearance references unknown item_type 'apple'` (and medkit, coin). Silent half (`p14_final.py`, same copy minus `levels/L0_smoke/items.yaml`): compile still refuses, but only because items_smoke exposes `medical.durability` and the token builder then reports `compiled item token capacity is 0 (no item catalog declaration, ...)` — a misleading message for a pack that DOES declare a catalog; a pack with no exposed item variable would compile with `items_catalog=None`, no error. |
| hamlet-4b931faaf4 (held exclusive items invisible to item token) | **STILL LIVE** | `vectorized_env.py:891` builds `ItemSlotBatch` from `manager.get_all_items()` = `active_items` only (`items/manager.py:592-594`); `lift_item` (`manager.py:427`) pops exclusive items into `held_items`, which has no observation reader. `p1_items_obs.py`: medkit row `presence=1` before GET → `presence=0 carried=0` after GET; `active [0,1,2] held [3]`. Asymmetry confirmed in `p13_more.py`: with `exclusive: false` the medkit stays in `active_items` and reads `presence [1,1] carried [1,0]` after GET. So `carried` only ever works for shared items. |
| hamlet-559cc74246 (item tokens carry no declared identity) | **STILL LIVE** | `universe/dto/token_spec.py:1697` `item_contexts = tuple(_fixed_payload("item", rank_context) for _ in range(item_capacity_value))` — every item slot gets the identical static payload. `p1_items_obs.py`: `static slot ctx payload identical across slots: True`; apple vs coin spawned on the same cell → `non-position lanes equal: True [1.0, 0.0, 0.0, 0.0]`; apple vs medkit also equal. The only discriminator is the item-arena `variable_element` slot for an *exposed* profile variable (medkit's `durability`); apple/coin (no exposed vars) are byte-identical. README's "item identities are profile-qualified" describes the symbol inventory, not the token. |
| hamlet-628e202bf7 (item `on_drop` inert) | **STILL LIVE** | `items/action_handlers.py:346-384` `handle_drop_slot_action` never calls `_execute_interaction(..., "on_drop")`; the only call sites are `:184` (`on_pickup`) and `:227` (`on_use`). `p2_on_drop.py` (items_smoke copy, medkit `on_drop: modify target.bar.money +0.5`, `on_pickup +0.1`): `after GET: 0.1`, `after USE: 0.1`, `after DROP (on_drop +0.5 expected): 0.1`. `configs/trial_k_cold` still compiles (`trial_k_cold compiled OK`), so the original record remains reproducible. `docs/config-schemas/items.md:653` ("DROP_SLOT_N … Executes `on_drop` Effects") is false. |
| hamlet-6b24c0bd83 (capability vocabulary dead) | **STILL LIVE** | `grep -rn "capability_config\|CapabilityConfig" src/townlet` → zero hits outside `config/capability_config.py`. `AffordanceParamConfig(..., capabilities=[{type: cooldown, cooldown_ticks: 5}])` → `Extra inputs are not permitted` (`p3_dto_refusals.py`). Whitelisted whole-file at `.defaults-whitelist.txt:120`. Same shape, new instance: `config/affordance_masking.py` (`BarConstraint`, `ModeConfig.hours`) also has zero importers (see F12). |
| hamlet-787aaa29f1 (list-typed item variable crashes at spawn) | **FIXED** | `p3_dto_refusals.py` (items_smoke copy, `freshness: type vec2f`, both `exposed_to: []` and `[agent]`): `Stage 1: Parse ... Item variable 'freshness' type has no supported scalar item-arena storage` — refused at parse, never reaches `spawn_item`. Width disagreement cannot arise (item-state slots are scalar, `token_publishers.py:994-999`). |
| hamlet-bf42ac60b5 (item-slot obs raw/unnormalized) | **FIXED** | `p1_items_obs.py`: `durability=3.0 → ve value=0.030`, `100 → 1.000` under the declared `minmax 0..100` (`CompiledValueNormalizer`, `token_publishers.py:1065-1067`). Exposure without a normalization is refused at compile (`require_exposure_normalization`). |
| hamlet-d45331a367 (`recovery.natural` required, consumed nowhere) | **STILL LIVE, with a twist** | `grep -rn "recover" src/townlet/vfs/vtc.py` → no hits; the only consumer is the meter token identity payload (`universe/compilers/observation.py:150`, `token_spec.py:1154`). `p5_natural.py` (items_smoke copy, health `initial 0.5, passive 0.0, recovery.natural 0.05`): `health over 9 idle ticks: [0.5]*9`; meanwhile `meter slot ctx natural_recovery lane: [0.0, 0.0476, 0.0]` — the dead parameter is published to the network as part of the meter's identity and participates in the indistinguishability refusal. `docs/config-schemas/bars.md:97` ("`recovery.natural` — Recovery per tick") actively lies. |
| hamlet-6c49488b22 (item fixed placement 2-D only) | **STILL LIVE, and broader** | `config/items_config.py:298` `fixed_positions: list[tuple[int, int]]`; `SpawnPlacementConfig(mode="fixed", fixed_positions=[(1,2,3)])` → `Tuple should have at most 2 items after validation, not 3`. Broader (F2): on GridND/continuous/aspatial NO placement mode spawns anything, because `vectorized_env.py:823-841` only derives `grid_size` from `substrate.width/height` (GridND exposes `dimension_sizes`, `substrate/gridnd.py:90`). `grid` mode (`manager.py:675-686`) and `random` spawn_item (`manager.py:271-282`) are also 2-D literals. |
| hamlet-fba3d5aa3c (zero-affordance pack crashes at first observation) | **FIXED** | `p4_zero_aff.py` (items_smoke copy with `environment.affordances: []`, level `affordances: []`, `enabled_affordances: []`, no shaping): `compiled+reset+step OK; census {... 'affordance': 0 ...} obs torch.Size([2, 469])`; INTERACT stays in the action space (id 4) and is masked `[False, False]`. The engine/publisher tolerate capacity 0 (`AffordanceTokenPublisher.publish` returns at `capacity == 0`, `token_publishers.py:509`). A shaping bonus naming a missing affordance is refused at compile (`DAC-REF-006/007`). |

## New findings (ranked, most severe first)

### F1. Compiled-universe cache drops every level's `items_appearance`: a cached run spawns no items at all
- severity: P1 (silent data loss; second and later runs of any items pack differ from the first)
- where: `src/townlet/universe/compiled.py:340-470` (`to_dict`/`from_dict` serialize `items_catalog` and `items_hash` but never `LevelMetadata.items_appearance`); consumer `vectorized_env.py:820`.
- failure scenario: compile `configs/test/items_smoke` once (writes `.compiled/universe-L0_smoke.msgpack`), compile again with the default `use_cache=True` → `level.items_appearance is None` → `reset()` skips `spawn_initial_items` → zero items in the world; GET is permanently masked. Training/inference after the first compile runs an item-less universe with the same `config_hash`.
- reproduction: `rm -rf configs/test/items_smoke/.compiled`, then compile twice in one process (transcript) →
  ```
  fresh  items_appearance: [('apple', 3, ...), ('medkit', 1, ...), ('coin', 0, ...)]
  fresh  spawned: [('apple', (3, 4)), ('apple', (2, 3)), ('apple', (2, 3)), ('medkit', (1, 1))]
  cached items_appearance: None
  cached spawned: []
  ```
- note: serialize `items_appearance` (and its compiled `when_ast`) in the level payload, or refuse to cache a universe whose levels carry it.

### F2. Item spawning is silently inert on every non-Grid2D/Grid3D substrate (GridND, continuous, aspatial)
- severity: P1 (declared level `items:` rules validate, compile, and never execute)
- where: `vectorized_env.py:823-841` (`grid_size` only from `hasattr(substrate,"width") and hasattr(substrate,"height")`; else `spawn_initial_items` is never called); also `items/manager.py:675-686` (`grid` placement `pos = (x, y)`), `:271-282` (`random` spawn_item 2-D), `config/items_config.py:298`.
- failure scenario: gridnd pack with an items catalog and a level `items.yaml` (`rock`, `spawn_count: 2`, `placement: random`) → `reset()` → no items, no error.
- reproduction: `p12_misc.py` → `gridnd: items_appearance rules 1 spawned after reset: []`; `p10_gridnd_items.py` → `GridNDSubstrate has width/height: False`, `AspatialSubstrate has width/height: False` (both packs ship an items catalog).
- note: derive `grid_size` from the substrate contract (`dimension_sizes`/extents) or refuse items_appearance on substrates the spawner cannot place on.

### F3. DAC modifiers, bar bonuses and thresholds are evaluated on RAW meters while their vocabulary is `[0,1]`-normalized — `trial002_money_log_gdp`'s `money_crisis` can never fire
- severity: P1 (shipped pack's declared reward logic is inert; silent)
- where: `environment/reward_calculator.py:46` passes `env.meters` (raw, declared bounds); `dac_engine.py:115-142` compares against ranges that `drive_as_code.py:85-109` forces to cover exactly `[0.0, 1.0]`; same for `BarBonusConfig.center le=1`, `efficiency_bonus.threshold le=1`, `economic_efficiency.min_balance le=1`, `state_achievement.min_value le=1`, `crisis_avoidance`. `dac_engine.py:863` docstring claims "normalized meter values".
- failure scenario: trial002 money bounds `[1.0, 1e6]`, `money_crisis` ranges `[0,0.2)→0.0, [0.2,1]→1.0` on `intrinsic.apply_modifiers`. Any money value ≥ 1.0 (i.e. every legal value) lands in the last range → multiplier 1.0 always; the "critical" range is unreachable.
- reproduction: `p13_more.py` →
  ```
  money raw=1.0   (minmax-normalized 0.00e+00): intrinsic_weight [1.0, 1.0]
  money raw=5.0   (minmax-normalized 4.00e-06): intrinsic_weight [1.0, 1.0]
  money bounds 1.0 1000000.0  intrinsic.apply_modifiers ['energy_crisis','health_crisis','money_crisis','food_crisis']
  ```
  Formula itself verified correct on a hand-computed 2-agent batch (see Refuted).
- note: either feed DAC the declared normalization (the same spec the meter token uses) or validate modifier/bonus ranges against each bar's declared bounds.

### F4. `base_reward: 0.0` / `base: 0.0` silently become 1.0 (and an omitted `base_reward` is a hidden default of 1.0)
- severity: P1 (wrong reward value from an explicitly authored config)
- where: `dac_engine.py:160` `base = getattr(strategy, "base", None) or 1.0` (multiplicative) and `:188` `base_reward = getattr(strategy, "base_reward", None) or 1.0` (constant_base); `config/drive_as_code.py:193,198` default both to `None`.
- failure scenario: `extrinsic: {type: constant_base_with_shaped_bonus, base_reward: 0.0, bar_bonuses: []}` → every live agent gets extrinsic 1.0 per tick. `multiplicative` with `base: 0.0` → product of bars (base treated as 1.0).
- reproduction: `dac_formula.py` (engine built directly) → `base_reward 0.0 -> extrinsic [1.0, 1.0] (expected [0,0])`; `multiplicative base 0.0 -> extrinsic [0.3, 0.8] (expected [0,0])`. Through the full compiler (`p14_final.py`, items_smoke copies, `env.step`): `base_reward: 0.0: compiled; extrinsic [1.0, 1.0]` and `base_reward deleted: compiled; extrinsic [1.0, 1.0]` — neither the DTO nor `universe/validation` refuses the omission. `docs/config-schemas/drive_as_code.md:41,266` claim "all fields required (no defaults)".
- note: make `base`/`base_reward` required per strategy and drop the `or`.

### F5. `completion_bonus` pays on every tick of a multi-tick interaction, not on completion; the compiled VTC completion-bonus rules are never evaluated
- severity: P1 (reward semantics differ from the declared vocabulary; duration-scaled over-payment)
- where: `action_executor.py:264-270` adds every in-progress agent to `successful_interactions`; `vectorized_env.py:1417` stores it as `_last_affordances`; `dac_engine.py:502-523` pays when `last_action_affordance == affordance`. `vfs/vtc.py:2714-2731` compiles `CompiledVTCInteractionCompletionBonus` (`affordance.<name>.completed`, phase `apply_completion_bonuses`), but nothing evaluates `completion_bonus_rules` (`grep -n completion_bonus_rules src/townlet/vfs/vtc.py` → field `:1285` and compile `:2681-2743` only; `transition_schedule.py` has no executor; they are only hashed in `schema_hashes.py:93`). The runtime `completion_mask` is derived inside `VTCInteractionProgressProgram.apply` from the *progress* rule's `duration_ticks` (`vtc.py:1346-1348`) and correctly drives `on_completion` effects (`action_executor.py:282`); the DAC bonus simply does not read it.
- failure scenario: model_pack `SLEEP` (`multi_tick`, `duration_ticks: 3`) with `completion_bonus weight 0.1 affordance SLEEP` → 0.1 at progress 1, 2 and at completion, i.e. 3× per completed interaction and also for interactions that are later abandoned.
- reproduction: `p9_multitick.py` (ii) → `tick 0: progress=1 shaping=0.1`, `tick 1: progress=2 shaping=0.1`, `tick 2: progress=0 shaping=0.1`, `tick 3: progress=1 shaping=0.1` …
- note: gate the bonus on `progress_result.completion_mask` (or execute the compiled completion rule) instead of "interacted this tick".

### F6. Opening hours and `timing_bonus` hardcode a 24-tick day; with any other `day_length` windows wrap mid-day
- severity: P1 when `day_length != 24` (affordances open/closed at the wrong times); invisible on shipped packs (all resolve to 24)
- where: `world/expression/functions.py:730-731` `period = 24.0; hour = time_value % 24`, fed `temporal.time_of_day = global_tick % day_length` (`vectorized_env.py:1221`; gate expression `vtc.py:2971-2975`); `config/drive_as_code.py:453-454` `TimeRange.start_hour/end_hour le=23`; `config/affordances_v2_config.py:403-404` `0..23` / `1..28`.
- failure scenario: `day_length: 48`, SLEEP `opening_hours 6–18` → open at time-of-day 30 and 40 (second "day" inside the day), closed at 20 and 47.
- reproduction: `p9_multitick.py` (iii) model_pack copy → `day_length 48 {3: False, 10: True, 20: False, 30: True, 40: True, 47: False}`.
- note: the window period must come from the declared clock (`period_of`), not an engine literal.

### F7. Dead agents still execute item actions and movement (only INTERACT is dones-gated)
- severity: P2 (a terminated agent mutates shared world state: removes items from the world for live agents, pays movement cost)
- where: `action_executor.py:81-84` (movement, no dones filter), `:116-188` (GET/USE/DROP/custom item loops, no dones filter) vs `:200-201` (INTERACT uses `interact_intent & ~dones`). `step()` relies on callers honouring `get_action_masks()`, which the env itself does not enforce.
- failure scenario: `env.dones[0]=True`; agent 0 is fed GET on a medkit cell → item lifted out of the world into a dead agent's inventory; fed UP → position changes and energy debited.
- reproduction: `p7_dead_agent.py` → `dead agent mask all False: True`; `dead agent GET: inventory [3,-1,-1] held [3]`; `dead agent UP: pos [2,2] -> [2,1] energy 1.0 -> 0.97`; `dead agent INTERACT ... energy 0.5 -> 0.49` (not executed; the 0.01 is passive depletion).
- note: apply the same `~dones` gate to movement and item dispatch.

### F8. Two affordances on one cell both fire on a single INTERACT, and tracking records only the last
- severity: P2 (double application; streak/completion/diversity tracking lies)
- where: `action_executor.py:317-343` loops every affordance and applies each whose position matches; `successful_interactions[agent] = name` overwrites; no compile-time refusal of overlapping `deployment.positions`.
- reproduction: `p8_two_aff.py` (items_smoke copy, `energy_station` and `health_station` both at `[1,1]`) → `compiled; after one INTERACT energy 0.74 health 0.8 successful_interactions {0: 'health_station'}` (both +0.3 effects applied; one interact debit).
- note: refuse overlapping fixed positions at compile, or make INTERACT target one affordance.

### F9. `approach_reward` is Euclidean regardless of the substrate's declared distance metric
- severity: P2 (reward disagrees with the declared world geometry; wrap/toroidal ignored too)
- where: `dac_engine.py:484` `torch.norm(agent_positions - target_pos, dim=1)`; `affordance_positions` are raw grid coordinates (`vectorized_env.py:1377-1390`).
- reproduction: `p12_misc.py` on items_smoke (`distance_metric: manhattan`), agent (4,4), target (1,1), `max_distance 5` → `approach bonus 0.1515` (manhattan distance 6 should give 0; Euclidean 4.24 gives 0.15). On aspatial (`p14_final.py`, `configs/aspatial_test`, positions `[N,0]`): `approach_reward(Bed) -> shaping [1.0, 1.0]` — norm over zero dims is 0, so the full bonus is paid every tick and the compiler does not refuse `approach_reward` on an aspatial universe.
- note: route through `substrate.distance()`.

### F10. A hard-coded `+1.0` retirement reward is added outside `drive.yaml`
- severity: P3 (undeclared, but oracle-preserved: pinned by `tests/test_townlet/unit/environment/test_vectorized_env.py:485 test_step_retirement_bonus`; the term still has no `drive.yaml` spelling)
- where: `vectorized_env.py:1196-1203` `bonus = newly_retired.to(...)`; `rewards += bonus; components["extrinsic"] += bonus`.
- reproduction: `p12_misc.py` on items_smoke (`max_steps_per_episode: 100`, `base_reward 0.01`) → `tick 99 newly_retired [True, True] reward [1.01, 1.01] extrinsic [1.01, 1.01]`. Not registered in `docs/oracle/known-divergences.md` (grep `lifespan|newly_retired|retirement` → only lifecycle-status prose).
- note: either declare it (a `retirement_bonus` shaping type) or drop it.

### F11. `opening_hours.enabled: true` on a level without active temporal mechanics compiles and is silently ignored
- severity: P2 (declared schedule inert)
- where: `vectorized_env.py:493-494` `if not self.enable_temporal_mechanics: return True`; no cross-validation (the compiler refuses `multi_tick` in this situation — `MULTI_TICK_REQUIRES_TEMPORAL` — but not opening hours).
- reproduction: `p13_more.py` (items_smoke copy, `temporal_support: disabled`, `energy_station.opening_hours: enabled, 6–18`) → `compiled; _is_affordance_open: True`.
- same shape, DAC side: a `timing_bonus` shaping on a non-temporal level compiles and always pays 0 because `reward_calculator.py:39-40` only passes `current_hour` when temporal is active and `dac_engine.py:673` returns zeros without it. `p14_final.py` (items_smoke copy, all-hours window on `energy_station`, INTERACT succeeds) → `succ {0: 'energy_station'} shaping [0.0, 0.0]`.

### F12. Dead declared vocabulary in the seam's DTOs (accepted-but-inert, or required-but-unconsumed)
- severity: P2
- where / evidence (all by grep over `src/townlet`, see transcript):
  - `config/affordance_masking.py` (`BarConstraint`, `ModeConfig.hours/effects`): zero importers (same shape as 6b24c0bd83; vulture lines 11-15).
  - `config/drive_as_code.py:236-244` `IntrinsicStrategyConfig.strategy` and `rnd_config/icm_config/count_config/adaptive_config`: only `base_weight` and `apply_modifiers` are read (`dac_engine.py:915,920`). The runtime exploration module is built from `training.yaml: intrinsic.*` (`demo/runner.py:420,513`), so `drive.yaml`'s `adaptive_config` on L1 (`README.md:198-203`) is dead and `strategy: none` does not turn RND off. README admits "unfinished integration"; the DTO does not.
  - `ExtrinsicStrategyConfig.variable` (`drive_as_code.py:202`): never read — `vfs_variable` uses `variable_bonuses` only. `dac_formula.py`: `vfs_variable with variable: only -> extrinsic [0.0, 0.0]`. Cross-strategy fields are silently ignored: `multiplicative + bar_bonuses(scale 100) -> extrinsic [0.3, 0.8]`.
  - `CompositionConfig.normalize/clip` inert (README admits); `log_components/log_modifiers` are stored (`dac_engine.py:90-91`) and read by nobody.
  - `TriggerCondition` (`drive_as_code.py:247`): zero consumers. `VFSVariableBonusConfig` and `VfsVariableConfig` both carry `type: "vfs_variable"` in the `ShapingBonusConfig` union (`:575,:582`).
  - `ExtrinsicStrategyConfig` docstring (`:164-166`) promises `aggregation op ∈ {min,max,mean,product}` and `hybrid` "weighted combination of multiple strategies"; engine implements min only (`dac_engine.py:349-363`) and a renamed constant_base (`:409-447`). `drive_as_code.md:494` is honest; the DTO is not.
  - `config/environment_config.py:314` `AffordanceDefinition.category` and `:357` `cues: list[CueConfig]` are REQUIRED and consumed by nothing in `src/townlet` (`grep -rn "cues\b|\.category\b"` → no hits outside the DTO).
  - `affordances_v2_config.py:537-553`: `on_early_exit`/`on_failure` are accepted stage names but every non-empty use is refused (`reachable_stages`), and nothing executes them (`affordance_engine.py` compiles them, no call site) — vocabulary that can only ever be written as `[]`. Every shipped `affordances.yaml` carries the two empty keys.
  - `items/instance.py:27` `spawn_tick`, `inventory.py:131,135` `is_full/count_items`, `affordance_engine.py:374,387` `get_affordance_action_map/get_num_affordances`: no callers (vulture confirmed).
  - `ItemsCatalogConfig.from_yaml` / `EnvironmentConfig.from_yaml` / `ActionsConfig.from_yaml`: filename readers CLAUDE.md says are deleted; only tests and docstrings call them (`tests/test_townlet/unit/items/test_item_lifecycle.py:12` etc.).

### F13. Item token `owner_slot` / `owner_slot_applicable` lanes have no producer
- severity: P2 (declared observation feature always zero)
- where: `vectorized_env.py:906` `owner_slot = torch.full((K,), -1)`; publisher `token_publishers.py:654-659` therefore always writes 0/0.
- reproduction: `p1_items_obs.py` → `owner_slot batch: [-1, -1, -1, -1, -1]`; rows show `owner_slot=0.00 owner_appl=0` before and after GET.

### F14. `spawn_initial_items` counts refused spawns toward `max_total`
- severity: P3 (latent under-spawn when `max_total` is combined with a capacity/cooldown refusal)
- where: `items/manager.py:865-871` increments `current_total` without checking `spawn_item`'s `None` return (compare `process_respawns` `:964-967`, which checks).
- reproduction: `p12_misc.py` (items_smoke copy, `max_items_in_world: 2`) → `spawned ['apple','apple'] rule_spawn_counts {'rule_0_apple': 3, 'rule_1_medkit': 1, ...}`.

### F15. Random item placement ignores occupancy; `GET` and the GET mask pick "first found" at a cell
- severity: P3
- where: `items/manager.py:659-663` (`random` placement, no `_position_occupied` check; `spawn_item` `:393-396` happily indexes several items per cell); `action_handlers.py:163-167`, `action_mask_builder.py:450-454` (first match wins; the agent cannot choose).
- reproduction: fresh compile of items_smoke → `spawned: [... ('apple', (2, 3)), ('apple', (2, 3)) ...]`; `p12_misc.py` drop onto an apple cell → `items at (2, 0): ['apple', 'medkit'] position_index {0, 3}`.

### F16. Whitelist residue and hidden defaults the blanket entries hide
- severity: P3
- `.defaults-whitelist.txt:49` whitelists `src/townlet/environment/affordance_config.py`, which does not exist. Lines 50-51, 133, 189, 241 blanket-whitelist `affordance_engine.py`, `vectorized_env.py`, `dac_engine.py`, `items/manager.py`, `action_executor.py`; sites they hide: `vectorized_env.py:141` (`getattr(metadata,"ticks_per_day",0) or 0`), `:152,159-160,267` (`getattr(..., {})`/`""`), `:1013-1025` (`hasattr(self,"_velocity")`), `:1038,1388,1443,1453,1463` (`hasattr` guards on attributes `__init__` always sets), `affordance_engine.py:102-103` (`or NullEffectManager()` / `or NullItemManager()`), `dac_engine.py:160,188,222,251,...` (`or 1.0`/`or 0.0`, see F4), `items/manager.py:527,656,852,866,955` (`getattr(rule, ...)` defaults on a typed DTO), `items_config.py:134` (`exclusive` default True), `:246,293` (`schedule.type` default `periodic`, `placement.mode` default `random`), `drive_as_code.py:633-638` (`version`, `modifiers`, `shaping`, `composition` defaults).
- `token_publishers.py:186` docstring still cites the deleted `vfs/observation_builder.apply_normalization` (residuals list).

## Refuted

Claims tested that did NOT reproduce (commands in the scripts named):
- **DAC composition formula** (`dac_formula.py`): hand-computed 2-agent batch — modifier `m` on `b0` (`[0,0.5)→0`, `[0.5,1]→1`), `constant_base 0.01 + 0.5·b0`, intrinsic `0.1×raw×Πm`, `efficiency_bonus 2.0 @ b0≥0.7`, meters `b0=[0.3,0.8]` → `total [0.16, 2.51]` = expected; with `dones=[F,T]` → `[0.16, 0.0]`; weights `[0.0, 1.0]`. `total = extrinsic + intrinsic·base_weight·Πmodifiers + shaping` holds exactly.
- **Zero-affordance pack crashes at first observation** (fba3d5aa3c): compiled, reset and stepped fine (`p4_zero_aff.py`).
- **List-typed item variable crashes at spawn** (787aaa29f1): refused at parse (`p3_dto_refusals.py`).
- **Item-slot observation unnormalized** (bf42ac60b5): `3.0 → 0.030` (`p1_items_obs.py`).
- **multi_tick affordance on a non-temporal level crashes at INTERACT**: compiler refuses with `[MULTI_TICK_REQUIRES_TEMPORAL]` (`p9_multitick.py` (i)).
- **Same-tick GET race on one exclusive item**: sequential dispatch, first agent wins cleanly: `slots [[3,-1,-1],[-1,-1,-1]] holders {0}` (`p12_misc.py`).
- **Item/inventory state leaks across reset**: after `reset()` inventories are `-1`, `held_items` empty, `item_vfs` rows re-initialised to profile defaults (`[100.0]…`), `respawn_timers`/`cooldown_until` empty, instance ids restart at 0 before respawn (`p12_misc.py`).
- **Multi-tick progress survives movement**: UP after 2 ticks resets progress to 0; re-entering restarts at 1 (`p9_multitick.py` (ii-b)).
- **Shaping bonus naming an undeclared affordance silently returns zeros**: refused at compile `DAC-REF-006` / `DAC-REF-007` (`p4_zero_aff.py`).
- **Money crushed to [0,1]** (CLAUDE.md "Economic balance"): trial002 money (`bounds [1,1e6]`, `initial 1000`) survives `reset()` + `step(WAIT)` at `1000.0` (`p14_final.py`); the declared bounds are honoured by every clamp. F3 is about DAC *reading* the raw value, not clamping it.
- **"Fixed affordance vocabulary across levels"** (CLAUDE.md): `md5sum configs/default_curriculum/levels/*/affordances.yaml` → all five `923ed2abe0809d10f8d491f4126d8c06`. Holds.
- **Dead agent INTERACT executes**: it does not (`p7_dead_agent.py`); only movement and item actions leak.
- **Opening-hours window spelling 22→28 (overnight)** parses and wraps correctly via `time_in_window` modulo; the defect (F6) is the period, not the wrap.
- **`.compiled` cache mislabel / fingerprint**: fingerprint logic works; the loss in F1 is in serialization, not cache validation.
- **Executable meter-name branches in the reward path** (CLAUDE.md "never branch on a variable's name"): all `meter_literals.txt` hits in my files are docstrings/examples; `dac_engine._get_bar_index` is map-driven and `money_bar` is the declared role binding. None found.

## Coverage

Read fully: `items/manager.py`, `items/action_handlers.py`, `items/inventory.py`, `items/instance.py`, `environment/affordance_engine.py`, `environment/dac_engine.py`, `environment/reward_calculator.py`, `environment/action_executor.py`, `environment/action_mask_builder.py`, `environment/token_publishers.py`, `environment/vectorized_env.py`, `config/items_config.py`, `config/affordances_v2_config.py`, `config/bars_v2_config.py`, `config/drive_as_code.py`, `config/affordance_masking.py`, `config/actions_config.py`, `config/environment_config.py`, `environment/action_config.py`, `config/capability_config.py`, `config/interaction_type.py`, `docs/config-schemas/affordances.md`, `docs/config-schemas/bars.md`, README "Rewards", the items_smoke pack, `.defaults-whitelist.txt`/vulture/meter_literals/residual hits for these files.

Skimmed (targeted sections only): `vfs/vtc.py` (gate program, interaction-progress/completion compile, reward program, opening-hours expression), `vfs/transition_schedule.py` (phase dispatch), `universe/dto/token_spec.py` (item/meter payload regions), `universe/compiled.py` (serialization), `universe/raw_configs_v21.py` (items gate), `universe/compilers/actions.py` (item action creation), `environment/observation_encoder.py` (publisher wiring), `world/expression/functions.py` (`time_in_window`), `docs/config-schemas/items.md` and `drive_as_code.md` (grep for load-bearing claims), trial002 and model_pack drive/bars/affordances.

Read, no defect found: action ordering within one step (Layer-2 e) — `action_executor.py` runs movement → velocity writes → movement debit → GET → USE → DROP → custom item verbs → INTERACT debit + interactions, all on post-movement positions, then `step()` runs the VTC action-write phases; the only ordering issue found is the dones asymmetry (F7).

Not reached: VTC occupancy/capacity claims (`claim_if_free` / `capacity_claim`, `actions_config.py:74`) — not exercised at runtime; `effects/` internals beyond the executor's position branch; `ItemManager` scripted/poisson/normal schedules at runtime (read only — note `despawn_item:533-542` sets a `normal` respawn timer to an absolute sample without a `current_tick+1` floor, unlike `process_respawns:943`); `VTCModulationProgram` numeric behaviour; the `configs/test/action_masking`, `model_config_4meter/_12meter` and `configs/simple` packs (not exercised); custom item verbs (`local_commands`/`inventory_commands`) at runtime; CUDA device behaviour (CPU only, per brief).
