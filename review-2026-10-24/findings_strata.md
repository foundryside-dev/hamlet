# Findings — strata

Reviewer seam: substrates (`src/townlet/substrate/`), `config/stratum_config.py`,
`config/curriculum_config.py`, env consumers (`vectorized_env.py` position/affordance paths,
`action_mask_builder.py`, `action_executor.py`, `action_labels.py`, spatial parts of
`token_publishers.py`), `universe/compilers/actions.py`, `environment/substrate_action_validator.py`.
All scripts: `/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/strata/`
(run from `/home/john/hamlet` with `PYTHONPATH=src uv run python <script> <scratch-dir>`).
Branch `fix/episode-lane-accounting`, CPU only, 2026-10-24.

## Backlog adjudication

| id | disposition | evidence (file:line, command, 1-line output) |
|---|---|---|
| hamlet-6c49488b22 | STILL LIVE | `s9_items_nd.py`: `SpawnPlacementConfig(mode="fixed", fixed_positions=[[1,0,0,0]])` → `Tuple should have at most 2 items after validation, not 4` (`config/items_config.py:298`). Worse than filed: the same trial_k_cold item declarations on a scratch 7×7×7×7 gridnd AND on a 7×7×2 cubic pack compile, construct and reset with `active_items == {}` while the 7×7 control spawns `{0: (1, 0)}` — the item-appearance path is silently skipped off Grid2D/Grid3D (see F4 for the full rank-2 inventory). |
| hamlet-1b9af9088c | OBSOLETE (for my clause) / deferred | The clause "DTOs refuse coordinate positions" is about `config/effects_config.py:99` `position: str \| None  # Expression for position` — a `spawn_item` command *expression* string, not a substrate position type. No substrate DTO is involved: `DeploymentConfig.positions: list[list[int]]` (`affordances_v2_config.py:81`) accepts any rank and `_position_to_tensor` (`vectorized_env.py:454-487`) only checks `numel`. Whether the expression surface now reaches the executor is the effects/items reviewers' call; not re-adjudicated here. |

## New findings (ranked, most severe first)

### F1. Action masking forbids every edge-crossing move regardless of `boundary`, so `wrap` and `bounce` are declared surfaces no masked policy can ever reach
- severity: P1 (declared mechanic silently neutralised; the `boundary_wrap` differential pack cannot exercise wrap)
- where: `src/townlet/environment/action_mask_builder.py:140-170` (duck-types on `width`/`height`, never reads `self.substrate.boundary`); `grid2d.py:107-110` implements the wrap the mask hides.
- failure scenario: `configs/differential/boundary_wrap` (8×8, `boundary: wrap`). Agent at (0,0): LEFT/UP/UP_LEFT/UP_RIGHT/DOWN_LEFT are masked False, exactly as on `clamp`. `substrate.apply_movement` for the same LEFT returns (7,0). Every consumer of `get_action_masks()` (`population/vectorized.py:642,682,778`, `demo/live_inference.py:800`) never sees the torus. Same code path masks `bounce` (reflection unreachable) and `sticky` (harmless no-op). Grid3D is hit identically (same `width`/`height`/`depth` duck typing, lines 171-188).
- reproduction: `s2_wrap_mask.py`
  ```
  substrate.boundary = wrap
  agent0 at [0, 0] masked-out: ['UP', 'LEFT', 'UP_LEFT', 'UP_RIGHT', 'DOWN_LEFT', 'INTERACT', 'GET', 'USE_SLOT_0', 'DROP_SLOT_0']
  agent1 at [7, 7] masked-out: ['DOWN', 'RIGHT', 'UP_RIGHT', 'DOWN_LEFT', 'DOWN_RIGHT', 'GET', 'USE_SLOT_0', 'DROP_SLOT_0']
  apply_movement LEFT from (0,0) under wrap gives: [[7, 0]]
  positions after forced LEFT step from (0,0): [[7, 0], [7, 0]]  velocity: [[7.0, 0.0], [7.0, 0.0]]
  ```
- note: gate the boundary mask on `substrate.boundary == "clamp"` (or ask the substrate for a blocked-moves predicate); note GridND/continuous get no boundary mask at all (F13), so the families already disagree.

### F2. Continuous2D movement is scaled by `movement_delta` twice (quarter-step instead of half-step)
- severity: P1 (wrong behaviour; every 2-D continuous universe moves `movement_delta²·magnitude` per step)
- where: `src/townlet/substrate/continuous.py:548-549` bakes `movement_delta` into each `MOVE_i_j` delta; `continuous.py:157` (`apply_movement`) multiplies the incoming delta by `movement_delta` again. 1D (`:409`) and 3D (`:641` ff.) emit unit deltas and are scaled once. `vectorized_env._build_movement_deltas` (`:691-716`) copies the declared delta verbatim, so the double scaling reaches the env.
- failure scenario: `movement_delta: 0.5`, magnitude-1.0 east action → displacement 0.25; with `movement_delta: 2.0` the agent moves 4.0 per step.
- reproduction: `s1_continuous2d_double_scale.py`
  ```
  MOVE_0_2 declared delta: [0.5, 0.0]
  2D displacement for magnitude-1.0 east step (expected 0.5): [[0.25, 0.0]]
  1D RIGHT delta [1] displacement: [[0.5]]
  3D RIGHT delta [1, 0, 0] displacement: [[0.5, 0.0, 0.0]]
  ```
- note: emit unit-magnitude direction vectors in `_generate_discretized_actions` like 1D/3D do. No shipped pack is continuous-2D, so nothing in `configs/` currently witnesses this.

### F3. Capacity fallback in `randomize_affordance_positions` silently flips the pack to configured placement — and crashes `reset()` when the pack has no fixed positions to fall back on
- severity: P1 (silent mode switch; `ValueError` on first reset for a valid random-deployment pack)
- where: `src/townlet/environment/vectorized_env.py:1571-1621` (sets `self.randomize_affordances = False`, returns `None`, logs a warning); `__init__` `:366-369` discards the `None` and never calls `_apply_configured_affordance_positions()`; `reset()` `:752-760` then takes the configured branch; `_position_to_tensor` `:461` raises when deployment is `random`.
- failure scenario: (a) `default_curriculum` L1 with `num_agents=60` (14 + 60 > 64): a pack that declared `randomize_affordances: true` runs on the fixed layout, with every affordance at the origin between `__init__` and the first `reset()`. (b) scratch `configs/test/action_space/grid2d` with `deployment.type: random`, `randomize_affordances: true`, `num_agents=70`: `reset()` raises "requires explicit position when randomize_affordances is disabled" — the pack never disabled it. The comment at `:1606` ("RawConfigsV21 already emits a warning") is false: `grep -n capacity src/townlet/universe/raw_configs_v21.py` → no hits.
- reproduction: `s3_capacity_fallback.py`, `s3b_capacity_random.py`
  ```
  training.randomize_affordances = True
  after __init__: randomize_affordances = False
  after __init__: affordance positions: {'EAT': [0, 0], 'SLEEP': [0, 0], ... 'DOCTOR': [0, 0]}
  after reset #1: {'EAT': [2, 2], 'SLEEP': [0, 0], 'WORK': [4, 4], 'SHOWER': [1, 1]} ...
  ---
  deployment types: {'Bed': 'random', 'Job': 'random'} | 8x8 grid
  after __init__: randomize_affordances = False  affordances: {'Bed': [0, 0], 'Job': [0, 0]}
  reset raised: ValueError - Affordance 'Bed' requires explicit position when randomize_affordances is disabled.
  ```
- note: refuse at construction (`agents + affordances > capacity` is a config fact) instead of downgrading a declared mode.

### F4. Items never spawn on any substrate other than Grid2D/Grid3D — silently; and every item-placement path is typed or coded for rank 2 (position-typing side of hamlet-6c49488b22)
- severity: P1 (declared `items_appearance` silently produces nothing on gridnd/continuous/aspatial; `fixed`/`scripted` placement refuses rank ≠ 2 even on cubic)
- where (rank-2 inventory):
  - `vectorized_env.py:824-840` — `grid_size` only built when `hasattr(substrate,"width") and hasattr(substrate,"height")`; otherwise `spawn_initial_items` is skipped with no diagnostic (GridND has `dimension_sizes`, continuous has `bounds`).
  - `config/items_config.py:298` `fixed_positions: list[tuple[int, int]]`; `:311` script `position: (x,y)`.
  - `items/manager.py:277-279` `find_spawn_location` jitters `(dx, dy)` only; `:678-680` and `:752-755` `mode: grid` loops over `grid_size[0]`, `grid_size[1]` only (3-D cubic gets 2-tuples that `_in_bounds` `:291` rejects by length → nothing placed).
  - `action_mask_builder.py:102-106` compares `item.position == tuple(positions[i].tolist())` — int tuple vs float coordinates on continuous substrates could never be equal (code-read inference, not reproduced: nothing spawns there in the first place, so the comparison is never reached today).
  - `vectorized_env.py:466-467` dead axial `{"q","r"}` branch: no DTO (`DeploymentConfig.positions: list[list[int]]`) can deliver a dict.
- failure scenario: trial_k_cold's coat (`mode: fixed`, `fixed_positions: [[1,0]]`, `spawn_count: 1`) on a 7×7×7×7 gridnd or a 7×7×2 cubic scratch pack: compile OK, reset OK, `active_items == {}`.
- reproduction: `s9_items_nd.py`
  ```
  [grid_control] compile+reset OK; active_items after reset: {0: (1, 0)} | items_appearance declared: [('coat', 1, 'fixed', [(1, 0)])]
  [gridnd] compile+reset OK; active_items after reset: {} | items_appearance declared: [('coat', 1, 'fixed', [(1, 0)])]
  [cubic] compile+reset OK; active_items after reset: {} | items_appearance declared: [('coat', 1, 'fixed', [(1, 0)])]
  SpawnPlacementConfig refuses 4-D fixed_positions: ['fixed_positions.0', '  Tuple should have at most 2 items ... not 4 ...']
  ```
  (cubic: `fixed_positions` is a 2-tuple on a 3-D substrate; `_in_bounds` length check drops it silently.)
- note: type positions as `list[list[int|float]]` validated against `substrate.position_dim`, and ask the substrate for extents instead of `hasattr(width)`.

### F5. Fixed affordance positions are never bounds-checked at compile or construction time; an off-grid affordance compiles, is unreachable, and emits normalized coordinates > 1
- severity: P2 (misleading acceptance; observation contract `[0,1]` broken; the checkpoint path *does* refuse the same coordinates)
- where: `vectorized_env.py:454-487` `_position_to_tensor` (checks `numel` only); no bounds validator in `src/townlet/universe/` (grep `deployment.positions|out of bounds|within.*bounds` → none). Contrast `validate_affordance_positions` `:1509-1565`, which refuses `normalized ∉ [0,1]` — but only for checkpoints.
- failure scenario: scratch copy of `configs/differential/div003_rect` (8×6) with `EAT` at `[7, 7]`.
- reproduction: `s8_fixed_oob.py`
  ```
  compile OK on 8x6 grid with affordance EAT at [7,7] (y=7 >= height 6)
  normalize_positions([7,7]) = [[1.0, 1.399999976158142]]
  reachable from any in-bounds cell: False
  obs finite: True obs max: 1.399999976158142
  validate_affordance_positions (checkpoint path) refuses: Affordance 'EAT' coordinates are outside the current substrate bounds
  ```
- note: run the existing checkpoint validator's bounds check over `deployment.positions` at cross-validate.

### F6. A custom `WAIT` is silently dropped — including its `writes` — on substrates that emit WAIT themselves (GridND, ContinuousND)
- severity: P2 (declared vocabulary with no runtime consumer, no diagnostic)
- where: `src/townlet/universe/compilers/actions.py:111-112` (`if custom.name in substrate_names: continue`); `gridnd.py:280-295` and `continuousnd.py` emit `WAIT`; Grid2D/Grid3D/Continuous1-3D/Aspatial do not (`grid2d.py:287` "WAIT is custom-only via actions.yaml"). Two families, two vocabularies.
- failure scenario: gridnd_4d_pack + `custom_actions: [WAIT with writes: [{variable_id: energy, expression: '0.5', …}]]` → compiled WAIT is `source=substrate`, `writes=()`.
- reproduction: `s6_custom_wait_dropped.py`
  ```
  declared custom WAIT with a write to energy
  WAIT entries after compile: [(9, 'substrate', 'passive', ())]
  any diagnostics? (compile succeeded silently)
  ```
- note: either no substrate emits WAIT (it is passive, not spatial) or a name collision is a refusal like the `reserved_names` one two lines below.

### F7. `action_discretization` is required for every continuous substrate but consumed only by Continuous2D (dead required config on 1D, 3D, ND)
- severity: P2 (no-defaults forces authors to write config that nothing reads)
- where: `config/stratum_config.py:107-113` (`action_discretization: ActionDiscretizationConfig = Field(...)` required); `substrate/factory.py:85,99,115` passes it to 1D/2D/3D; only `Continuous2DSubstrate._generate_discretized_actions` (`continuous.py:495`) reads it; `factory.py:127-133` does not even pass it to `ContinuousNDSubstrate`.
- failure scenario: `configs/test/action_space/continuous1d` declares `num_directions: 8, num_magnitudes: 3`; compiled substrate actions are `[LEFT, RIGHT, INTERACT]`.
- reproduction: `s1_continuous2d_double_scale.py` / `s5_action_order.py`
  ```
  1D action names: ['LEFT', 'RIGHT', 'INTERACT'] (action_discretization 8x3 declared, consumed?)
  3D action names: ['UP', 'DOWN', 'LEFT', 'RIGHT', 'UP_Z', 'DOWN_Z', 'INTERACT']
  configs/test/action_space/continuous1d: n=7 substrate_count=3 ... substrate default names: ['LEFT', 'RIGHT', 'INTERACT']
  ```
- note: make the field conditional on `dimensions == 2` (or honour it in every family).

### F8. The `self` token's velocity lane is unbounded: −7 on a wrap seam, raw world units on continuous
- severity: P2 (observation payload violates its own "bounded" contract; the sibling position/egocentric lanes are in [0,1]/[−1,1])
- where: `action_executor.py:32` (`velocity = positions − old_positions`, unnormalized); `token_publishers.py:346` declares `velocities: [N, D] velocity features (bounded, caller's contract)` and `:413-414` writes it verbatim.
- failure scenario: boundary_wrap, agent at x=7 moves RIGHT → x=0, velocity −7 lands in the observation; continuous1d (bounds [0,10], `movement_delta 0.5`) publishes 0.5 next to a normalized position 0.55.
- reproduction: `s4_velocity.py`, `s4b_velocity_continuous.py`
  ```
  wrap grid: pos after RIGHT from x=7: [[0, 3]] velocity: [[-7.0, 0.0]]
  self token row: [1.0, 0.0, 0.4285714328289032, -7.0, 0.0]
  continuous1d self token row (presence, pos..., vel...): [1.0, 0.550000011920929, 0.5]
  ```
- note: compute velocity as `substrate.egocentric_delta(old, new)` (shortest path, same denominator).

### F9. `vision_support: none` is an unusable vocabulary item; `active_vision: local` is a residual the DTO can never produce
- severity: P2 (declared enum member with no admissible level)
- where: `config/stratum_config.py:186` admits `"none"`; `universe/validation/semantics.py:112-125` rejects `global` unless `{global, both}` and `partial` unless `{partial, both}`, and `CurriculumConfigRoot.active_vision` (`curriculum_config.py:28`) only allows those two — so every level under `none` fails `VISION_INCOMPATIBLE`. `semantics.py:107` still canonicalises `"local"`.
- reproduction: `s7_vision_none.py`
  ```
  vision_support: none -> CompilationError Stage 3: Cross-validate semantics failed:
    - [VISION_INCOMPATIBLE] .../levels/L0/curriculum.yaml:1 - Invalid vision configuration: curriculum.active_vision='global' requires stratum.vision_support in ['global','both'].
  ```
- note: delete `"none"` and the `"local"` branch.

### F10. The canonical ordering contract (`INTERACT` at `[-2]`, `WAIT` at `[-1]`) is false after composition and STRATA.md §5 claims downstream code relies on it
- severity: P2 (doc actively lies about behaviour; the substrate families disagree with each other on WAIT; aspatial does not emit `[INTERACT, WAIT]`)
- where: `substrate/base.py:119-141` and `docs/architecture/STRATA.md` §5 ("Downstream systems identify meta-actions by position… Aspatial… `[INTERACT, WAIT]` only (`aspatial.py:159-165`)"); composition in `compilers/actions.py:73-153` appends custom then item actions after the substrate block. No runtime consumer indexes by position (`grep actions\[-2\]` → base.py docstring only; executor uses `action_ids.get("INTERACT")`), so the code is consistent and only the contract text is wrong.
- reproduction: `s5_action_order.py`
  ```
  configs/default_curriculum: ... '8:INTERACT(s)', '9:WAIT(c)', '10:REST(c)', '11:MEDITATE(c)', '12:GET(i)', '13:USE_SLOT_0(i)', '14:DROP_SLOT_0(i)']  [-2] = USE_SLOT_0  [-1] = DROP_SLOT_0
  configs/test/gridnd_4d_pack: ... '8:INTERACT(s)', '9:WAIT(s)', '10:GET(i)' ...   substrate default names: [..., 'INTERACT', 'WAIT']
  configs/aspatial_test: substrate default names: ['INTERACT']
  ```
- note: rewrite the contract as "movement block then INTERACT within the substrate-sourced prefix; WAIT is custom" — or make it true.

### F11. Engine branches on the variable names `velocity_x/y/z/magnitude`, reading the registry's private `_definitions`; nothing declares or documents them
- severity: P2 (CLAUDE.md "never branch on a variable's name"; capability with no documented authoring reach)
- where: `src/townlet/environment/action_executor.py:35-46`.
- evidence: `grep -rn "velocity_x\|velocity_y\|velocity_magnitude" configs/ docs/config-schemas/` → 0 hits; `src/townlet` outside the executor → 0 hits. An author who happens to declare an agent variable called `velocity_x` gets engine writes; one who calls it `speed_x` gets nothing.
- note: expose velocity through a declared semantic type / engine-write binding, not a magic id.

### F12. `SubstrateActionValidator` validates the substrate's own defaults against itself; STRATA.md §5 says it checks "alignment between the two halves"
- severity: P3 (tautological refusal; dead `hex` branch)
- where: `environment/substrate_action_validator.py:31-32` builds `substrate_impl.get_default_actions()` and never reads `actions.actions` (the `ActionsConfig` it demands); `:45-46` `topology == "hex"` cannot occur (`GridConfig.topology: Literal["square","cubic"]`). With `substrate_actions.inherit: false` the compiled space has no movement and no INTERACT yet the validator still passes (it does not look at `inherit`).
- note: validate the *compiled* action metadata or delete the class.

### F13. Boundary masking exists only for substrates with `width`/`height`: GridND and Continuous* agents may bump walls (and pay movement cost) while Grid2D/Grid3D agents may not
- severity: P3 (family inconsistency; no doc states either rule)
- where: `action_mask_builder.py:140-142` duck typing.
- reproduction: `s11_masks_labels.py`
  ```
  == GridND: no boundary masking at all (clamp bump allowed, movement cost charged)
    at origin masked-out: ['INTERACT', 'GET', 'USE_SLOT_0', 'DROP_SLOT_0']
    after DIM0_NEG bump at origin: pos [[0, 0, 0, 0]]  meter delta [-0.009999990463256836, 0.0, 0.0]
  ```

### F14. `math` and `cardinal` label presets label the `UP` action (delta `[0, −1]`) as `Y_POS` / `NORTH`
- severity: P3 (label lies about the sign of the delta it names; `CanonicalAction` comments say MOVE_Y_POSITIVE = "up")
- where: `compilers/actions.py:167-170` maps `MOVE_Y_NEGATIVE→"DOWN"`, `MOVE_Y_POSITIVE→"UP"`; `grid2d.py:171` `UP` is `delta=[0,-1]`.
- reproduction: `s11_masks_labels.py`
  ```
  math: [('UP', (0.0, -1.0), 'Y_POS'), ('DOWN', (0.0, 1.0), 'Y_NEG'), ...]
  ```
  Also: `FORWARD`/`BACKWARD` preset entries (`:171-174`) never match any substrate name (Grid3D emits `UP_Z`/`DOWN_Z`), GridND/Continuous2D names get no preset label at all, and `action_labels.get_labels()`/`_filter_labels_for_substrate` (which assumes `D0_NEG..DN_NEG, D0_POS..` ordering that GridND does not emit) has zero callers in `src/`.

### F15. Grid2D `bounce` has no safety clamp (Grid3D/GridND do): a 1-wide axis reflects out of bounds
- severity: P3 (latent; DTO permits `width: 1`)
- where: `grid2d.py:112-127` vs `grid3d.py:118` / `gridnd.py:166`.
- reproduction: `s10_refutations.py` — `Grid2D 1x1 bounce: x=0 step +1 -> [[-1, 0]]`; `GridND 1^4 bounce: step +1 -> [[0, 0, 0, 0]]`.

### F16. An agent can be masked into zero legal actions when no custom WAIT is declared
- severity: P3 (edge: 1×1 grid or no-movement corner with no affordance underfoot; shipped packs all declare WAIT)
- where: `action_mask_builder.py` has no "at least one action" guarantee; Grid2D/3D/continuous substrates emit no WAIT (F6/F10).
- reproduction: `s11_masks_labels.py` — `legal: ['WAIT']` on a 1×1 clamp grid; `without custom WAIT legal count: 0`.

### F17. `.defaults-whitelist.txt` `src/townlet/substrate/**:*` (and `stratum_config.py:*`, `action_executor.py:*`, `vectorized_env.py:*`) — what it hides
- severity: P3
- Lint run without the whitelist (`scripts/no_defaults_lint.py --whitelist /dev/null src/townlet/substrate …`, 17 violations): constructor defaults unreachable from YAML — `grid2d.py:45-46` (`topology="square"`, `enable_diagonals=True`), `grid3d.py:49-51` (`distance_metric="manhattan"`, `topology`, `enable_diagonals=True`), `gridnd.py:41-42`, `continuousnd.py:52` (`distance_metric="euclidean"`); `continuous.py:143` `names.get(self.dimensions, {})`; the wrap-ternaries (`grid2d.py:398,406` etc.) are harmless. Not flagged by the lint but behaviour-bearing: `continuous.py:516-517` `.get()` on the discretization dict; `continuous.py:527-529` hardcoded `base_energy_cost = 0.005` etc. (dead meter-cost literals — computed and discarded, `:554-556`); `_encode_velocity_observation` `vectorized_env.py:1003-1023` `hasattr/getattr` guards; `action_mask_builder.py:140,173` `getattr/hasattr` duck typing (F1/F13); `reset()` `:824-830` `hasattr(width)` (F4); `vectorized_env.py:141` `getattr(self.metadata, "ticks_per_day", 0) or 0`. `config/stratum_config.py` itself has only `depth: int | None = None` (validator-enforced) — the whitelist line is unneeded there.

### F18. vulture entries in the seam — adjudication
- `_encode_scaled` / `_encode_absolute` in all five spatial substrates: dead, 0 callers in src and tests — stranded remnant of the deleted `observation_encoding` selector (PDR-0143). Delete.
- `get_valid_neighbors` (base + all families), `supports_enumerable_positions`, `coordinate_semantics`, `action_space_size`: 0 src callers (tests only). `grid2d.get_valid_neighbors` also ignores `enable_diagonals` and `grid3d/gridnd` build CPU tensors without a device — harmless only because dead.
- `action_labels.get_label/get_action_count/get_labels`: 0 src callers; `_filter_labels_for_substrate`'s N≥4 scheme disagrees with GridND's emitted order (F14).
- `config/*: model_config` / validators: false positives (pydantic).
- `token_publishers.py:_layout` ×8: stored, never read — cosmetic.

### F19. `GridNDConfig`/`ContinuousConfig` rank limits live in the substrate constructors, not the DTOs (loud but late, non-UAC error)
- severity: P3
- `s13_config_vs_runtime.py`: `gridnd` with 2 dims, `continuous` with 5 dims, `continuousnd` with 2 dims all pass the DTO and fail only in `SubstrateFactory.build` with a bare `ValueError` (no error code / location). The DTO docstring says "N>=4 recommended" while the runtime says required.

## Refuted

- (c) Radius uses the LONGEST axis with the `max(1, …)` floor exactly as documented: `Grid2DSubstrate(8,6)._token_vision_radius(0.3) == 2` (shorter axis would give 1); `vision_range 0.0 → 1`; 1×1 grid → 1. Cubic POMDP end-to-end (`s12b_pomdp.py`, div003_cubic_partial, radius 2): affordance presence is 1 at manhattan 1–2 and 0 at ≥3. `s10_refutations.py`, `s12b_pomdp.py`.
- (b) Wrap shortest-path deltas correct at both edges for even (8) and odd (7) spans: `[-1, -4, 1]` and `[-1, 3, 1]`, all `|d| ≤ span/2`; `visible()` symmetric A→B vs B→A; egocentric within [−1, 1]. Tie on even span goes negative as `base.py:21-23` pins. `s10_refutations.py`.
- (d) Same per-axis denominator for normalized positions and egocentric deltas: grids `span−1` (`[7,5]` on 8×6 → `[1,1]` both ways), continuous `extent`; 1-wide axis `max(…,1)` safe (no NaN). Continuous egocentric under wrap from −5 to +5 on extent 10 is 0 (same point on the torus) — correct by construction. `s10_refutations.py`.
- (a) Every family × boundary × metric (×diagonals for grids) constructs with no silent fallback: 12 combos × Grid2D/Grid3D/GridND/Continuous2D; all four boundary branches exist in every family (`grid2d.py:102-135`, `grid3d.py`, `gridnd.py:147-171`, `continuous.py:163-193`, `continuousnd.py:188-218`). `s10_refutations.py`.
- (h) Bounce reflection sign and sticky semantics correct where reachable: Grid2D/3D x=0 step −1 → 1, x=7 step +1 → 6; Continuous 9.8+0.5 → 9.7, 0.2−0.5 → 0.3; sticky holds 9.8; grid sticky/clamp are per-axis (a diagonal at a corner moves along the free axis — identical to clamp, so no observable difference). `s10_refutations.py`.
- (e) Movement deltas generated in a deterministic order matching the names for Grid2D (diag), Grid3D (diag + Z), GridND (DIMi_NEG, DIMi_POS interleaved), and `_build_movement_deltas` keys them by compiled id. `s10_refutations.py`, `s5_action_order.py`.
- (g) Rectangular grid x/y: on div003_rect (8×6) 40 random masked steps keep positions within `lo=[0,0] hi=[7,5]`; `normalize_positions([7,5]) == [1,1]`; corner masks are per-axis from the substrate's own `width`/`height` (`action_mask_builder.py:143-146`). `s12_e2e.py`.
- (f) No live agent ever receives an all-False mask row over 40 random masked ticks on div003_rect, aspatial_test, gridnd_4d_pack, continuous1d (the all-False rows observed were exactly the `dones` rows, by design). `s12b_pomdp.py`.
- (i) Aspatial tolerates every env position path: compile, construct, reset, 40 masked steps, finite 19-dim obs, `visible()` all-true and `egocentric_delta()` width 0 (`aspatial.py:65-71`). `s12_e2e.py`.
- POMDP does not reshape the tensor: default_curriculum L1 vs L2 `total_dims 118 == 118`, `layout_hash` equal. Transfer contract holds across families: `token_type_schema_hash == 8ad2b59b502a905b` on default_curriculum (2-D), div003_cubic_partial (3-D), gridnd_4d_pack (4-D), continuous1d and aspatial_test (dims 118/152/78/27/19, five distinct `layout_hash`es) — only the `428982ef…` literal in CLAUDE.md is stale. Both hashes are compared at checkpoint load (`training/checkpoint_utils.py:189-194`, `:211-217`).
- `stratum.vision_support` capability check is real (`semantics.py:105-125`, `VISION_INCOMPATIBLE`), and `temporal_support` is consumed (`vectorized_env.py:123`). `s7_vision_none.py` shows the refusal firing.
- Checkpoint `validate_affordance_positions` does bounds-check (F5 output), including rect grids and integer-compat for grids.
- Device (j): substrates allocate every tensor on the caller's `positions.device` / passed `device`; the factory's `device` arg is unused by design (`factory.py:27-32`). Nothing to refute on CPU; no CPU/CUDA mismatch surfaced across the six packs stepped.
- Existing suite: `tests/test_townlet/unit/substrate`, `unit/universe/test_action_space_composition.py`, `integration/test_substrate_observation_seam.py` → 327 passed, 5 skipped (`scratchpad/strata/pytest_substrate.txt`). None of those tests covers F1–F8 (they test substrates in isolation or without masks).
- Residuals file: no hits in my files except `token_publishers.py:186` (a docstring citing the deleted `vfs/observation_builder.apply_normalization` ABI — stale comment, not a code path) and the `compiled_vfs_profiles` references in `vectorized_env.py` (live attribute, not the deleted authoring surface). `meter_literals.txt`: no hits in my files.

## Coverage

- Read fully: all nine `src/townlet/substrate/*.py`; `config/stratum_config.py`; `config/curriculum_config.py`; `environment/action_mask_builder.py`; `environment/action_executor.py`; `environment/action_labels.py`; `environment/substrate_action_validator.py`; `universe/compilers/actions.py`; `vectorized_env.py` lines 73-375, 375-520, 520-720, 743-880, 995-1060, 1460-1664; `token_publishers.py` self/affordance publishers (380-420, 495-550) and the spatial call sites of agent/item publishers; `universe/validation/semantics.py:95-170`; `universe/validation/feasibility.py`; STRATA.md §5 and §7; `docs/manual/pomdp_compatibility_matrix.md`; README "Spatial configuration"; every listed pack's `stratum.yaml` / `curriculum.yaml` / `actions.yaml`.
- Skimmed: `items/manager.py` (only the placement/grid_size lines), `items_config.py:290-320`, `raw_configs_v21.py:115-150`, `compilers/metadata.py:100-125`, `demo/live_inference.py:218-232`, `action_builder.py:76-94`, the test file listing (names only).
- Not reached: `environment/env_factory.py`; the rest of `token_publishers.py` (meter/effect/variable publishers); `universe/dto/token_spec.py`; checkpoint position round-trip (`training/checkpoint_utils.py`); the frontend's consumption of substrate metadata; `tests/test_townlet/properties/test_substrate_nd.py`. CUDA not exercised (brief says CPU). No continuous-2D or continuousND pack ships, so F2 and the ND half of F7 were shown at substrate level, not through a compiled pack.
- Adjacent, for the observation reviewer: `vectorized_env.py:410` always passes `agent_slots=None`, so `AgentTokenPublisher` (`token_publishers.py:576`) never populates other-agent spatial tokens — not owned here.
- Adjacent, for the training reviewer: `compilers/actions.py:66-71` `apply_global_filter` is only engaged when `enabled_actions.custom` names a non-custom action, so a list of only custom names cannot disable substrate actions — not tested here.
