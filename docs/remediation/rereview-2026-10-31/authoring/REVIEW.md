# Re-review — lens `authoring` (docs vs DTOs vs behaviour, designer mechanics, principle violations)

Commit `559dd0f9`, detached worktree `scratchpad/rereview/authoring/wt`, CPU, `PYTHONPATH=wt/src`
with `/home/john/hamlet/.venv/bin/python` (`townlet.__file__` confirmed under `wt/src`). Every probe
copies `configs/default_curriculum` (or `configs/test/items_smoke`) into `probes/packs/<name>`, patches
YAML, compiles with `UniverseCompiler().compile(path, primary_level=..., use_cache=False)`, builds
`VectorizedHamletEnv.from_universe(...)` and steps. Probes: `probes/harness.py`, `m_mechanics.py`,
`m_mechanics2.py`, `m_items.py`, `f_matrix.py`, `d_docs.py`, `c_closure.py`; logs `probes/out_*.log`.
`/home/john/hamlet` untouched; no `git stash`; worktree removed at the end.

## 1. VERDICT: NOT GREEN

Blocking:

- **A1 (P1)** a transition rule whose `variable_id` is a meter (`bar.<m>`) compiles and crashes on the
  first `env.step` with a bare `KeyError` and no `file:line`. Every doc under test advertises the form;
  four VFS.md examples die this way.
- **A2 (P2, spec gap in VFS scope)** VFS state cannot hold a random draw: `uniform`/`normal_dist` are
  refused in variable expressions, transition rules and action writes (admitted only in effects,
  interactions and spawn predicates). "A per-world global weather that changes every K ticks" is not
  authorable; the only workaround is deterministic noise that is identical across worlds.
- **A3 (P2, spec gap in VFS scope, the known spatial item plus its vector twin)** the profile shape
  prover's allow-list (`vfs/profiles.py:377-441` (`pointwise` at `:420`)) excludes the position functions AND every vector
  function (`distance`, `within_radius`, `gather`, `normalize`), so a declared `vec2f` variable can be
  consumed by nothing in VFS; "distance to nearest food" is not an observable feature.
- **A4 (P2, known, classified)** opening hours against a declared clock period other than 24: the
  gate, the token lanes, the identity and the DTO all hardcode 24, nothing refuses the mismatch, and
  the affordance is open at the wrong hours.

- **A5 (P2, known, classified)** an affordance closed by a variable has no spelling (the availability
  store was deleted at 2e0d1622 because nothing authored reached it); the follow-up list itself
  calls it a capability gap in VFS/compiler scope.
- **A6 (P2, spec gap)** an action masked unless a variable condition holds has no spelling
  (`CustomActionConfig` has no predicate field); the lowering target already exists as the VTC phase
  `compute_action_legality_masks`, so I count it in compiler scope. If the owner rules action
  legality out of scope it drops to the "later phase" list without changing the verdict.

Everything else is P3 or closed. The registry/doc agreement tests
(`tests/test_townlet/unit/world/expression/test_function_registry_agreement.py`,
`test_expression_functions_doc.py`) pass at this SHA (106 passed), so the return-type column of
`expressions.md` holds; what does not hold is *where* a function may be called (A2/A3).

## 2. NEW findings (most severe first)

### A1. P1 — transition rule on a meter: compile green, `KeyError` at step 1, no location
- claim: `transition_rules[].writes[].variable_id: bar.<meter>` is resolved at compile to the bare
  meter name with a `meter=True` target (`vtc.py:453-461`, `vtc_write_targets`), the rule compiles,
  and `VTCTransitionRuleProgram._compute_phase_effects` raises
  `KeyError("VTC transition rule targets unknown VFS variable 'energy'")` because it looks the target
  up in the VFS phase snapshot only (`src/townlet/vfs/vtc.py:1683-1684`). Even if that check were
  bypassed, `_run_transition_rules` returns VFS values only (`vfs/transition_schedule.py:167-184`) and
  `run_phases` never folds a rule's result into `bars_state`, so there is no commit path for a meter
  write from a rule at all.
- documented as supported: `docs/config-schemas/variables.md:343` ("a meter | `bar.<name>` |
  everywhere, including an action write's or rule's `variable_id`"), `transition_rules.md:63-64`,
  and the VFS.md examples at `:1441` (`energy_base_depletion`), `:1456`, `:1691`
  (`low_health_hits_mood`). The pinning test
  `tests/test_townlet/unit/config/test_vfs_doc_transition_rule_examples.py:55-70` compiles the
  blocks against a mock target map and never steps.
- repro: `probes/m_mechanics2.py r1 r2` → `compiled rule targets: [('energy_base_depletion',
  'energy', 'apply_passive_depletion')]` then `STEP CRASH: KeyError "VTC transition rule targets
  unknown VFS variable 'energy'"`; `m_mechanics.py m1 m13` (night-hunger on `bar.satiation`,
  variable-driven death via `bar.health`) and `d_docs.py` (VFS.md:1441, :1456, :1691) all die the
  same way. Action writes to `bar.energy` work (`r3`, VFS.md:1052/:1274 stepped), so the gap is the
  rule program only.
- history: pre-existing, not a regression of the one-spelling cut — `vtc_write_targets` has carried
  `meter=True` targets since `adb76a71` (2026-10-24, sprint phase A; present at 76a3060e, `vtc.py:493`), and no shipped pack or
  test ever stepped a rule with a meter target.
- fix shape: either give `VTCTransitionRuleProgram.apply` a bars commit path (evaluate meter targets
  against `bars_state`, return `next_bars`, have `run_phases` fold it and `clamp_and_validate` run
  after) or refuse `bar.` targets in `compile_vtc_transition_rules` with the write's `file:line` and
  correct the three docs. Either way it needs a stepping test.

### A2. P2 — no random draw can reach VFS state (spec gap, `vfs/profiles.py:420-437` + the rule/action shape prover)
- claim: `uniform(...)` and `normal_dist(...)` are refused with "Expression function 'uniform' has no
  qualified variable output shape" in a global/agent variable expression, a transition-rule
  expression (`[VTC-WRITE-TYPE] ... has no provable shape`) and an action write; they are admitted in
  effect pipelines, interaction pipelines and item spawn predicates (`f_matrix.py`, `m_items.py
  spawn`). `perlin_noise(tick, 0.0, seed)` is admitted everywhere, but it is a function of `tick`
  alone, so it draws the same value in every world.
- consequence for a designer: the brief's "per-world global weather that changes every K ticks"
  compiles only as a deterministic schedule (`m7b`: `((tick - tick % 4) / 4) % 3` works); the random
  version refuses (`m7`), and no VFS mechanic can carry per-world randomness (loot rolls, random
  decay, stochastic events) without an effect-pipeline detour that still cannot write a global.
- the effects route is no escape: an effect can read a global, write a meter and call `uniform`, but
  effects spawn only from an interaction or another effect — there is no episode-start / autonomous
  spawn surface (`docs/config-schemas/effects.md:326` "no `on_reset` hook, so an effect cannot be
  declared live at tick 0"; `effects/manager.py:571`). A world process must wait for an agent to
  interact with something.
- fix shape (VFS scope): add `uniform`/`normal_dist` to the `pointwise` set in `_shape`
  (`profiles.py:420`) with result shape = first argument's shape (and say in `expressions.md` that a
  literal first argument is one draw per batch; pass a per-world value such as `weather * 0.0` for
  per-world draws). Rules and action writes share the prover via `_write_shape_refusal`
  (`vtc.py:2094`, `:2507`) so one edit covers all three.

### A3. P2 — the shape prover's allow-list strands twelve registered functions (position AND vector), and one function is callable from nowhere
- claim: `_shape` (`profiles.py:415-441`) proves shape only for a hand-listed `pointwise`/`stacked`
  set; every other registered function refuses "has no qualified variable output shape". Measured
  over 35 expressions × 7 contexts (`out_matrix.log`): refused in variable expressions, rules and
  action writes but admitted in effects/interactions — `distance_to_affordance`, `in_range`,
  `distance`, `manhattan_distance`, `within_radius`, `gather`, `uniform`, `normal_dist` (A2) — all
  scalar/bool-returning. `normalize`, `direction_to_affordance`, `scatter`, `one_hot` return vectors
  and refuse everywhere a scalar target is written (expected); `nearest(vecv, t2d)` and
  `gather(t2d, 0)` refuse in every context including effects (extra cells, 24 compiles, in
  `out_matrix_extra` below). The evaluator already receives agent and affordance
  positions for both profiles (`vectorized_env.py:1225-1227, 1248-1250`), so the spatial half is
  purely the prover (known item, classified P2 below).
- vector twin (new): `vec2f`/`vecNf` variables are declarable and exposable, yet
  `distance(vecv, vecv)` and `within_radius(vecv, vecv, 1.0)` refuse in an agent expression
  (`f_matrix.py aexpr`), so a declared vector variable can be read by no expression, rule or action
  write — only by an effect or interaction. "Distance to a remembered home position as an
  observation" is unauthorable.
- `elapsed_ticks()` (new, P3 inside this finding): registered (`functions.py:1326-1332`,
  `requires=(REQUIRES_STEP,)`), documented without caveat (`expressions.md:417`), and admitted by
  **no** authoring context: profiles refuse it in `_shape`, and no `ReadContext` in `vfs/namespace.py`
  carries `REQUIRES_STEP` (effects/interactions carry positions only; rules/spawn carry nothing).
  Delete it or admit it.
- fix shape: derive the shape rule from the registry instead of a hand list — a scalar-returning
  function of per-agent arguments is agent-shaped, of scalars scalar; position functions are agent
  -shaped (and therefore refuse in a global expression by the existing widening rule).

### A4. P2 (known item, classified; new sub-sites) — opening hours ignore a declared clock period
- claim: with `day_phase.normalization.period: 48` and `day_length: {period_of: day_phase}`, the
  level resolves `day_length=48` and `_clock_hour = tick % 48` (`vectorized_env.py:505-507`), but the
  compiled gate is `time_in_window(temporal.time_of_day, s, e)` (`vfs/vtc.py:3222-3226`) whose
  evaluator hardcodes a 24-tick period (`world/expression/functions.py:626-628`), so EAT declared
  open 2..6 is open at ticks 2-5 **and 26-29** (`m_mechanics2.py m10`: `ticks where EAT is open:
  [2, 3, 4, 5, 26, 27, 28, 29, 50, 51]`). Nothing refuses the mismatch.
- the other 24-sites, none of which can represent hour 24..47: the affordance token payload
  `OPENING_HOURS_FEATURES = open_hour_0..23` (`universe/dto/token_spec.py:390`), the identity
  signature `opening_hours_signature` with `% 24` (`effects/affordance_identity.py:162-184`), and
  `OpeningHoursWindow.end: le=28` (`config/affordances_v2_config.py:44`; `start: 30` refuses at load,
  `m10b`). So a 48-hour day cannot even declare a window after hour 28.
- severity call: wrong behaviour from an authored pack, but only when a pack declares a non-24
  period, and `declarations.md:119` says the clock reference "does not redesign time units". P2: the
  compiler should at least refuse `period != 24` while these constants exist. Known-item id: the
  docs-sweep "time_in_window hardcodes a 24-tick day" line in PHASEA_FOLLOWUPS.

### A5. P3 — doc examples that do not parse as written, or author a grammar that no longer exists
All in the trusted tier (`docs/config-schemas/`) unless noted. Verified by `d_docs.py` (every YAML
block spliced into a scratch pack, compiled and stepped):
- `expressions.md:189-202` (`is_critical`) and `:647-677` (`is_night`/`is_crisis`/`motivation`) omit
  `readable_by`/`writable_by` → `[LOAD_ERROR] ... Field required`. Completed, they compile and step.
- `expressions.md:206-218` (`effects_catalog:` with `type: if / path / operation`) and `:222-226`
  (`spawn_rules:`) are pre-Cut-A grammars → `[DECLARATION_UNKNOWN]`. `:912-921` keys entries by
  `name:` → `declarations[1].id: Field required`. `:81-84` names `duration` and `slot_index` as
  context variables; the effect locals are `intensity`, `elapsed_ticks`, `duration_remaining`
  (`references.py:51`). `:25-26` says DAC reads expressions "(future)" while `variable_bonuses` /
  `vfs_variable` consume VFS variables today (M5, M14 below).
- `VFS.md:927-938` (§9.1 "Current strategy") shows `normalization: null` on an exposed variable and
  fragments without scope/type; `:960-972` (§9.2) uses `source_variable:`. Both refuse at the DTO;
  neither section is marked design-era (contrast §16.2, which is).
- `VFS.md:1441`, `:1456`, `:1691` are the A1 crash examples.
- Everything else under test holds: `variables.md:8` (whole declaration), `:313` (`time_since_*`,
  and `configs/L5_multi_agent/variables.yaml:35` does carry it), `declarations.md:96` (`period_of`
  → 24 on L3), `transition_rules.md:46` (steps once the illustrative names are declared, as its
  caveat says), VFS.md `:290/:343/:531/:677/:1052/:1274/:1473/:1592/:1712/:1730/:2002/:2454/:2525`
  all compile and step with the documented effect (`job_is_open` true for ticks 9-17; CALL_AMBULANCE
  claims DOCTOR's row in world 0 only: `occupied_by[0][13] = 0`, world 1 untouched).

### A6. P3 — refusals that do not name the fix
- `vfs/profiles.py:396, 401, 441, 448, 451` — "has no qualified variable/expression output shape" /
  "vector/tensor payloads is not supported": says what was refused, never what to write (declare the
  quantity elsewhere? which functions are admitted?). This is the message behind A2/A3 and M8.
- `vfs/vtc.py:1684` — the A1 runtime `KeyError`: no code, no `file:line`, no fix.
- `config/variables_config.py:93` ("type has no supported scalar item-arena storage"), `:101` ("scope
  has no supported observation publisher"), `:104` ("requires float32 storage; type 'x' is
  unsupported") — name the rule, not the alternative (declare scalar/bool; drop `exposed_to`).
- `profiles.py:342-347` ("expression shape is scalar, expected agent for agent scope") — the common
  case is an agent variable over `tick` only (`time_in_window(tick,2,6)` in an agent expression
  refuses); the message should say "declare it `scope: global`".
- `vtc.py:2908` ("Unsupported VTC modulation type"), `:3020-3023` (duration), `token_spec.py:1125`
  ("not an exposure-admitted kind") — vocabulary refusals without the vocabulary.
- `[ITEM-SPAWN-CONDITION]` for `distance_to_affordance` in a spawn `when` — says the predicate "has
  no agent/affordance positions" without saying a spawn predicate reads globals/agent vars/meters
  only (text in `out_items.log`).

### A7. P3 — no-defaults: behavioural defaults reachable from YAML hidden by blanket waivers
`scripts/no_defaults_lint.py` over `config/`, `vfs/`, `universe/`, `world/expression/` with an
empty whitelist (`scratchpad/empty_wl.txt`) lists 150 sites; the YAML-reachable behavioural ones,
all under `*` waivers in `.defaults-whitelist.txt`:
- `config/drive_as_code.py:605-610` `DriveAsCodeConfig.version default "1.0"`, `modifiers default
  {}`, `shaping default []`, `composition default_factory` → `CompositionConfig` (`:573-576`)
  `normalize=False`, `clip=None`, `log_components=True`, `log_modifiers=True`; `:193-205`
  `ExtrinsicStrategyConfig.bar_bonuses/variable_bonuses/apply_modifiers default []`, `base_reward`,
  `base`, `variable default None`. A `drive.yaml` with no `composition:` block compiles with
  `normalize: false` silently (the shipped packs happen to write it).
- `config/items_config.py:266-267` `SpawnScheduleConfig.type default "periodic"`, `:313-314`
  `SpawnPlacementConfig.mode default "random"`, `:340-362` `placement/schedule/max_total/when
  default None` — an appearance rule with no `schedule:` silently becomes periodic/random.
- Whitelist hygiene: every path in `.defaults-whitelist.txt` resolves on disk (checked by script);
  the ratchet ceiling is 618. The original C13 list of seven deleted files is gone (closed).
- Closed on this surface: `items_config.py:134 exclusive` is now `Field(...)` required (known item
  closed); `TransitionRuleWriteConfig.phase/priority/telemetry_label` defaults are computed values
  (documented as such); `actions_config.py:55 writes default_factory=list` means "no writes"
  (acceptable); `effects_config.py:316 max_active_effects default None` is validated required when
  effects exist (`:340-345`).

### A8. P3 — PDR-0045 / shims (nothing new; inventory)
- No branch on a meter or variable *name* in scope: `grep` for the eight `default_curriculum` meter
  names over `vfs/`, `universe/`, `world/expression/`, `config/`, the three env files → docstrings
  and `>>>` examples only. `compilers/metadata.py` no longer mentions `money` (C6 closed).
- Branches on declared parameters, which is the rule: clock detection
  (`universe/declarations.py:525-531`: `semantic_type == "temporal"` ∧ `expression == "tick"` ∧
  cyclical normalization), reserved engine names (`references.py:60`).
- The 24-tick day is the one domain constant baked into the engine (A4 sites). `action_executor.py`
  `velocity_x` branches are the known strata item.
- Backwards-compatibility: none found beyond the `_LEGACY_*` tables in `vfs/namespace.py:236-237`
  that feed refusal text only (known, acceptable). `hasattr` in scope only at `compiler.py:654-657`
  (YAML error marks). Old artifacts refuse on `COMPILED_SCHEMA_VERSION`.

## 2b. Designer mechanics table

| mechanic | class | evidence / fragment | gap (Python edit, scope) |
|---|---|---|---|
| hunger decays faster at night | **GAP (A1)** — the natural form crashes | global `is_night: tick % 24 >= 18 or tick % 24 < 6` + rule `condition: is_night`, `variable_id: bar.satiation`, `expression: "-0.05"` → compiles, `KeyError` at step (`m1`). No VFS escape: the meter cannot be touched per tick from VFS except by an action write, and an agent effect that writes `bar.satiation` under `if: is_night` needs an interaction to spawn it (no autonomous spawn, see A2) | rule program bars commit path (`vtc.py:1617-1700`, `transition_schedule.py:167-184`); VFS scope |
| ticks since the agent last ate | **EXPRESSIBLE** | `initial_value: -1.0`, `expression: where(delta(bar.satiation) > 0.0, 0.0, lag(ticks_since_ate, 1) + 1.0)` (variables.md:313 pattern); `m2c`: counts 1,2 → 0 on a +energy action write → 1 → 0 | — |
| cooldown on an action | **EXPRESSIBLE-BUT-AWKWARD** (effect half) / **GAP** (mask half) | `last_strike` agent var `initial_value: -100.0`; action writes `hit += 1` and `last_strike <- tick` (overwrite) both with `condition: tick - last_strike >= 3.0` → fires at ticks 1 and 4 only (`m3`). The action is still selectable, costs its costs and consumes the turn; `CustomActionConfig` has no precondition field (`m3b`: `enabled_when`/`precondition`/`condition`/`available_when`/`mask` all `extra_forbidden`) | an authored legality predicate lowered into the existing `compute_action_legality_masks` phase and `ActionMaskBuilder`; action-space/compiler scope |
| resource regenerates toward a cap | **EXPRESSIBLE** | rule `additive_delta 0.3, clamp [0,1]` → 0.3, 0.6, 0.9, 1.0, 1.0; or `additive_delta 0.5 * (1.0 - mana2)` asymptotic (`m4`) | — |
| reward on a rising edge | **EXPRESSIBLE** | `low_energy: bar.energy < 0.95` (bool), `rose: rising_edge(low_energy)` (bool), `drive.extrinsic.variable_bonuses: [{variable: rose, weight: 5.0}]` → reward 0.97 … 5.97 on the edge tick only, 0.96 after (`m5`, `m5b`) | — |
| variable persists across episodes | **EXPRESSIBLE** | `lifetime: persistent` global counted by a rule: 3.0 before and after `reset()` (`m6`) | — |
| per-world global weather every K ticks | **EXPRESSIBLE-BUT-AWKWARD** (deterministic) / **GAP** (random, A2) | deterministic: global expression `((tick - tick % 4) / 4) % 3` → 0,0,0,1,1,1,1,2 (`m7b`). Random: rule `overwrite uniform(0.0, 3.0)` with `condition: tick % 4 == 0` refuses `[VTC-WRITE-TYPE] ... no provable shape` (`m7`) | admit `uniform`/`normal_dist` in `_shape` (`profiles.py:420`); VFS scope |
| observation "distance to nearest food" | **GAP** (known; A3) | `expression: distance_to_affordance("EAT")` on an exposed agent scalar → `[VFS-PROFILE-COMPILE] ... has no qualified variable output shape` (`m8`); same for `min(distance_to_affordance("EAT"), distance_to_affordance("COOK"))` and `in_range` | admit position functions as agent-shaped in `_shape`; the evaluator already has the positions (`vectorized_env.py:1225`); VFS scope |
| affordance closed by a variable | **GAP** (known; availability store deleted at 2e0d1622) | every spelling tried (`availability`, `available_when`, `condition`, `enabled_when`, bar-constraint list) → `[LEVEL_LOAD_ERROR] extra_forbidden` (`m9`); `config/affordance_masking.py BarConstraint` has no consumer | a declared affordance-scoped bool read by `is_affordance_open`; VFS/compiler scope per the follow-up note |
| opening hours keyed to a declared period ≠ 24 | **GAP** (A4) | period 48 compiles; EAT 2..6 open at 26..29 too (`m10`); `end > 28` refuses (`m10b`) | thread `day_length` into the gate (`vtc.py:3224`), `time_in_window` (`functions.py:628`), `OPENING_HOURS_FEATURES` (`token_spec.py:390`), identity (`affordance_identity.py:171`), DTO (`affordances_v2_config.py:44`) — or refuse `period != 24`; VTC/compiler scope |
| item state decays while held | **EXPRESSIBLE-BUT-AWKWARD** (effects route) / **GAP** (VFS route, by design) | items_smoke: apple `on_pickup: [{spawn_effect: food_decay, target: self, intensity: 1.0}]` with the catalog's item-scoped `food_decay` → held apple `condition` 100 → 96, 94, 92, 90 (`m_items.py`). VFS: rule on `freshness` refuses (`names no variable, meter or item state a transition write or rule can read`), item expression refuses (`expression execution supports global and agent scopes only`) — both documented (`variables.md:170`) | none required; note the per-profile intersection rule and that a catalog entry + `max_active_effects.item` budget is needed |
| action masked unless a variable condition holds | **GAP** | see cooldown mask half | same |
| terminal condition on a variable | **GAP (A1)** — the only workaround crashes | no declared terminal surface beyond `bars.yaml lethal_min/max` (`compile_vtc_terminal_conditions`, `vtc.py:3034-3135`); the workaround rule `doom >= 3.0 → overwrite bar.health 0.0` is the A1 crash (`m13`) | after A1 is fixed the workaround is EXPRESSIBLE-BUT-AWKWARD; a declared `terminal_when` on a variable is a bars/VTC change |
| private variable driving a reward | **EXPRESSIBLE** | `readable_by: [engine]`, `exposed_to: []`, written by an action, read by `variable_bonuses` → reward gap 1.0, 2.0, 3.0 between the praying and waiting agent; no `variable_element` row for it; `registry.get(..., reader="agent")` → `PermissionError` (`m14b`) | — |
| moving average of a meter as an observation | **EXPRESSIBLE** | `expression: moving_average(bar.energy, 4)`, `exposed_to: [agent]`, minmax → obs row `[1.0, 0.9975, 0.0]` tracks the registry value (`m15`) | — |

## 3. Known-item classification (authoring-relevant lines of PHASEA_FOLLOWUPS and the B3/B4 records)

- spatial functions refused in variable expressions (docs sweep) — **P2**, open; A3 above; the contradiction with `namespace.py` carrying positions is real (`_EVERY_REQUIREMENT` on both profile contexts).
- `time_in_window` hardcodes 24 — **P2**, open; A4 with its three sibling sites.
- "an effect that closes an affordance" capability gap — **P2** (spec gap in scope, unauthorable); open.
- VFS.md §11.6/§12.3/§14.3 `reads:` examples — **closed**: no `reads:` key in any extracted block; every `transition_rules` block compiles.
- Hash false move `2` vs `2.0` — P3, not re-tested.
- `self`/`target` reserved — **closed**: `RESERVED_NAMES` includes `ENTITY_NAMES` (`references.py:60`).
- DAC role fields bypass the resolver — P3; `variable_bonuses` reads by bare id (works, M5/M14).
- `_LEGACY_*` table feeds refusal text only — P3, acceptable.
- `items_config.py exclusive` hidden default — **closed** (`Field(...)`, `items_config.py:134`).
- Budget-0 effect scope silently refuses spawns — P3, not re-tested.
- B4 "semantics to document: phase-entry snapshot" — P3 doc; variables.md:245-247 now describes the end-of-step evaluation; the within-phase snapshot rule is still undocumented.
- B4 `aref <- aref2` dead form — not re-tested (B4 repair record says fixed).
- `CompiledUniverse.from_dict` ignores unknown keys — P3, not re-tested.
- Not classified here (outside this lens): the UaC fixed-deployment item, the identity/effect-slot aliasing item, the items-per-world/ItemManager items, the B2c effect-store leaks, the torch-RNG checkpoint item, `velocity_x`, the B3 import-order and rename items, `affordance_identity` self/all lanes, and the hash false-move items.

## 4. Original-review closure (authoring-relevant rows)

| id | status | evidence |
|---|---|---|
| V1 phases never executed / crash | **CLOSED** | action write at `apply_transition_rules`/`apply_passive_depletion` → `[UAC-STATIC-WRITE] ... runs without the tick's actions`; at `compute_rewards`/`emit_telemetry`/unknown → `not a transition phase`; rule at `compute_rewards`/`emit_telemetry`/`apply_modulations` → refused (`c_closure.py`) |
| V2 agent-axis inference | **CLOSED** | action write to global → `targets variable 'g', declared scope 'global' ... must be a ...`; to affordance without claim → refused |
| V3 `evaluation_mode: eager` | **CLOSED** | key refused `extra_forbidden`; `variables.md:179-183` |
| V4 `extents` | **CLOSED** | key refused |
| V5 variable id == meter | **CLOSED** | `[SYMBOL_METER_COLLISION] variables.yaml:25 ... collides with the meter 'energy' declared at ...` |
| V6 reward_component_program | not re-checked (VFS.md §17 says deleted 2026-10-24) |
| V7 agent expression reads global | **CLOSED** | `a: g * bar.energy` = 1.98 |
| V8 bare `vfs.X` write | **CLOSED** | `vfs.x` and `self.vfs.x` refuse naming `x` |
| V9 zone | **CLOSED** | scope vocabulary is the four |
| V12 hash ignores shape/initializer | **CLOSED** | `vfs_hash` 9b7ababc / ca473c2c / d2eea99f for [2,2] zeros, [4,4] zeros, [2,2] ones |
| V13 random init frozen | **CLOSED** | two resets draw differently |
| V14 expression sees rule write a tick late | **CLOSED** | `gc` 1,2,3 with `g2 = gc*2` 2,4,6 same tick |
| V15 residue (whitelist dead files, VFS.md §6 claims) | **CLOSED** (files) / **SUPERSEDED** (§6 text is dated) |
| C1 items_appearance lost on cache | **CLOSED** | `to_dict`/`from_dict` round-trip keeps it (`items_smoke`) |
| C3 catalog nullified on 0 | **CLOSED** | `max_items_per_agent: 0` compiles with the catalog; `raw_configs_v21.py:170` now requires empty `item_types` too |
| C4 dead required fields | **CLOSED** for `curriculum_levels` (bogus level → `[LOAD_ERROR] experiment.yaml:7`); others not re-checked |
| C5 RecordingConfig extra=allow | **CLOSED** | `extra_forbidden` |
| C6 `"money"` branch | **CLOSED** | no `money` in `compilers/metadata.py` |
| C7 presentation by filename | **CLOSED** | `display.yaml` with `NO_SUCH_METER` → `[LOAD_ERROR] display.yaml:4`; `CompiledUniverse.presentation` carried (`compiled.py:235-237`) |
| C8 identity discriminator | **SUPERSEDED** by the brain-gated rule: twins compile under `feedforward`, refuse `[TOKEN-IDENTITY]` under `token_set` |
| C9 inspect json row layout | **CLOSED** by reading (`__main__.py:163-185` joins `row_layout()` and bindings); not executed |
| C12 effects DTO defaults | **OPEN (P3)** — `effects_config.py:119-159` structural `None`/`[]` defaults remain (one command kind per node) |
| C13 whitelist residue | **CLOSED** (every whitelisted path exists) |
| V10/V11/C2/C10/C11/C14 | out of this lens (runtime/registry/cache/CLI/perf) — not re-checked |

## 5. Not covered
- `COMPILER.md` claims (another lens); registry runtime API and checkpoint resume; CUDA.
- The full `expressions.md` function table beyond the 35-expression matrix (the generated table is
  registry-pinned by test; I checked admission per context, not every signature).
- Item-arena publisher behaviour for held items; effects-engine semantics beyond the one decay probe.
- The pytest suite (another reviewer); I ran only the two expression registry/doc agreement tests (106 passed).
- I did not re-verify the B3/B4 "HOLDS" claims that are outside authoring (differential, resume).

## Appendix: out_matrix_extra (24 compiles, vector/spatial cells added after the main matrix)
```
aexpr/rule_a/action: manhattan_distance(vecv, vecv), normalize(vecv), nearest(vecv, t2d),
                     direction_to_affordance("EAT"), scatter(vecv, 0, 1.0), gather(t2d, 0)  -> all REFUSED
effect:              manhattan_distance OK; the other five REFUSED (vector/int result into a float target,
                     or nearest/gather(t2d) type refusals)
```
