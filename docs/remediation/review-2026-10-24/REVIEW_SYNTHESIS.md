# Townlet review pass — VFS, compiler, strata, Universe-as-Code (2026-10-24)

Source reviewed: `fix/episode-lane-accounting` at `a44b470f`, CPU. Five parallel reviewers, one
per seam; every finding carries a reproduction script under this scratchpad. I independently
re-ran the reproductions for each P1 marked ✔ below. Per-seam detail, including the Refuted and
Coverage sections, is in `findings_{vfs,compiler,strata,effects,items}.md` beside this file.

Nothing under the repo was modified. Compiles rewrote git-ignored `.compiled` caches only.

## 1. P1 findings, ranked (wrong behaviour, crash, or silent data loss)

Ordered roughly by blast radius. "✔" = I reproduced it myself; "R" = reviewer-reproduced only.

| # | seam | finding | where | ✔ |
|---|---|---|---|---|
| 1 | compiler | Cache-served `CompiledUniverse` drops every level's `items_appearance`. `to_dict`/`from_dict` never carry it. DemoRunner and live_inference compile with cache on, so the second run of any items pack trains in an item-less world. | `universe/compiled.py:380-410, 458-492` | ✔ |
| 2 | effects | Effects survive `env.reset()`: instances and `elapsed_ticks` carry into the next episode (backlog hamlet-d76684f549, still live). `reset()` only resets the scheduler; `EffectManager` has no reset. | `environment/vectorized_env.py:801-807`, `effects/manager.py:425` | ✔ |
| 3 | vfs | Four graph phases are never executed by `step()`: `apply_modulations`, `compute_rewards`, `emit_observation_features`, `emit_telemetry`. Writes and transition rules scheduled there compile green and never apply. Five more phases compile green and crash on step 1 for action writes. | `environment/vectorized_env.py:1074-1176`, `vfs/transition_schedule.py:117-135` | ✔ |
| 4 | effects | `modify: bar.X value: <scalar>` rebinds the bar to a stride-0 `expand_as` view; the next indexed write in the same tick lands on every agent. | `effects/executor.py:230-231`, `effects/context.py:279` | ✔ |
| 5 | effects | The `if` and `switch` *commands* reduce a per-agent condition with `.any()` and run the branch for all agents. The expression-form `if` is element-wise, so one keyword has two semantics. | `effects/executor.py:464-469, 598-602` | ✔ |
| 6 | vfs | `evaluation_mode: eager` evaluates expressions against each static's compile-time literal. An expression over an engine-written global is wrong forever. The mode is a required authored enum member. | `vfs/evaluator.py:184-200` | ✔ |
| 7 | vfs | VTC action writes decide "agent axis" by `target.shape[0] == num_agents`. A global/zone/group tensor whose extent happens to equal `num_agents` is silently masked per agent; any other extent crashes; a global scalar target compiles then crashes. Whether a pack runs depends on a training hyperparameter. | `vfs/vtc.py:954-962` | ✔ (source) |
| 8 | strata | Action masking forbids every edge-crossing move regardless of `boundary`. `wrap` and `bounce` are declared surfaces no masked policy can reach; the `boundary_wrap` differential pack cannot exercise wrap. | `environment/action_mask_builder.py:140-170` | ✔ |
| 9 | compiler | Stratum `boundary` and `distance_metric` edits move only `stratum_hash`, which nobody compares. A clamp-world checkpoint resumes on a wrap world and is accepted. Concrete half of backlog hamlet-2dde1015fe. | `universe/compiler.py:204`, `training/checkpoint_utils.py:139-341` | ✔ |
| 10 | items | DAC modifiers, bar bonuses and thresholds compare RAW meters against a vocabulary the DTO forces into `[0,1]`. Shipped `trial002_money_log_gdp` `money_crisis` (bounds 1..1e6) can never fire. | `environment/reward_calculator.py:46`, `dac_engine.py:115-142`, `config/drive_as_code.py:85-109` | ✔ |
| 11 | items | `base_reward: 0.0` / `base: 0.0` become 1.0 via `… or 1.0`; an omitted `base_reward` compiles and pays 1.0. Hidden default in a no-defaults engine. | `environment/dac_engine.py:160, 188` | ✔ (source) |
| 12 | items | `completion_bonus` pays every tick of a multi-tick interaction, not on completion. The compiled VTC completion-bonus rules are hashed and never evaluated. | `action_executor.py:264-270`, `dac_engine.py:502-523`, `vfs/vtc.py:2681-2743` | ✔ |
| 13 | strata | Continuous2D scales movement by `movement_delta` twice (baked into action deltas, applied again in `apply_movement`). 1D and 3D scale once. | `substrate/continuous.py:157, 548-549` | ✔ |
| 14 | strata | `randomize_affordance_positions` capacity fallback silently sets `randomize_affordances=False`; `__init__` discards the None so every affordance sits at the origin until reset; a random-deployment pack with no fixed positions raises on reset. Live on default_curriculum L1 at 60 agents. | `environment/vectorized_env.py:1571-1621` | ✔ |
| 15 | strata / items | Items never spawn on any substrate but Grid2D/Grid3D. `reset()` derives grid size only from `width`/`height`; every placement DTO and manager path is rank 2 (backlog hamlet-6c49488b22, still live and broader). | `vectorized_env.py:823-841`, `config/items_config.py:298, 311`, `items/manager.py:277-279, 678-680, 752-755` | ✔ (DTO) |
| 16 | effects / items | `time_in_window`, opening hours and `timing_bonus` hardcode a 24-tick day; the pack's declared clock period is ignored. "Engine knows the game." | `world/expression/functions.py` (`time_in_window`), affordance hours path | R |
| 17 | effects | Effects cannot read position or time: `tick` in any spelling refuses at compile; spatial functions compile then crash because positions are never threaded (backlog hamlet-a737e444c0, still live, worse than filed). | `universe/compilers/effects.py:35-39`, `effects/executor.py:800-815`, `vectorized_env.py:1092` | R |
| 18 | effects | `mean()` type-checks float and crashes on int inputs at the first tick; `sum`/`product`/`clamp01`/`/` and `elapsed_ticks` return dtypes that disagree with the type checker (one is a runtime ValueError on write). | `world/expression/functions.py:355-459`, `type_checker.py:280-282`, `compilers/effects.py:27` | R |

## 2. P2 findings, grouped (dead or unreachable declared surface, misleading refusals, docs that lie)

The reviewers' brief asked for one pattern: declared vocabulary with no consumer, runtime
capability with no authoring reach, or two vocabularies that disagree. It is everywhere.

**Required-but-consumed-by-nobody config** (no-defaults forces authors to write dead YAML, and bogus values compile):
`experiment.curriculum_levels` and `experiment.metadata.*`; `environment.cues` and `CueConfig`;
`AffordanceDefinition.category`/`.description`; `training_loop.evaluation.*` and `.checkpointing.*`;
`IntrinsicConfig.{rnd,icm,count,adaptive}_config` and `TriggerCondition`; the whole
`config/capability_config.py` module and the `affordance_masking.py` vocabulary; `variables.extents.num_affordances`
(runtime uses the level's count); `action_discretization` on 1D/3D/ND continuous; `bars.yaml recovery.natural`
(backlog hamlet-d45331a367, still live, now also moves `layout_hash`); `on_early_exit`/`on_failure` only ever `[]`;
`for_each … as:` never bound; `nearby_agents`/`radius`/`spawn_item quantity`/`initial_state` on the AST but not the DTO.

**Runtime capability with no authoring reach:** `reward_component_program` compiled, hashed, never run;
`zone` scope has storage but no consumer (backlog hamlet-02bd5a3eaa); sparse-pair and dynamic-variable
registry modes unreachable; item token `owner_slot` lanes have no producer; `active_effects` for_each iterates
self N times; `vision_support: none` admits no level; `active_vision: local` cannot be produced by the DTO.

**Two vocabularies disagree / silent acceptance:** item catalog nullified when `max_items_per_agent == 0` OR
`max_items_in_world == 0`, then refused with a misleading message (backlog hamlet-45f501e15b, still live);
`RecordingConfig` is the only `extra="allow"` DTO and typo keys enter `training_hash`; `presentation` is
content-discovered at compile but fixed-filename at runtime; a custom `WAIT` with writes is silently dropped
on GridND/ContinuousND; `switch` cases are untyped dicts so a typo'd `do` compiles to an empty case; a VFS id
equal to a meter name compiles and is caught only inside VTC apply; `variable_schema_hash` ignores tensor
shape and initializer; an agent-scope expression cannot read any global (including the pack clock); a
registry variable named `intensity`/`elapsed_ticks` shadows the effect lifecycle scalar; two affordances
identical in every parameter compile (indistinguishability check covers variables only, backlog
hamlet-2aca57c0f0 still has no escape hatch); fixed affordance positions are never bounds-checked (off-grid
affordance compiles, normalized coordinate > 1 reaches the observation); the `self` token velocity lane is
unbounded (−7 on a wrap seam).

**Engine knows the game (PDR-0045 name branches):** `compilers/metadata.py:72` `costs["money"]` feeding a dead
field; `action_executor.py:35-46` branches on `velocity_x/y/z/magnitude` via the registry's private
`_definitions`; `curriculum/adversarial.py` and `curriculum/static.py` hardcode the eight life-sim meters
(backlog hamlet-310e336786, out of the four seams, still live); the 24-tick day above.

**Runtime semantics nobody declared:** dead agents still move and GET/USE/DROP (only INTERACT is dones-gated);
two affordances on one cell both fire per INTERACT; `approach_reward` is Euclidean regardless of declared
metric and pays in full on aspatial; opening hours and `timing_bonus` silently inert on non-temporal levels;
in an effect `self.` and `target.` are now the same entity and `self.vfs.X` is unspellable; an `observable`
effect in a zero-budget scope silently vanishes from the observation; GridND/continuous get no boundary
masking at all while grids do; `INTERACT at [-2], WAIT at [-1]` is false after composition and STRATA.md §5
says code relies on it (no code does); `math`/`cardinal` label presets call UP (delta `[0,-1]`) `Y_POS`/`NORTH`.

**Docs that actively lie** (only listed because they contradict behaviour): `effects.md` (effect-level
`intensity` refused, `observable` required not optional, `duration: 1` semantics, `nearby_agents`, `for_each`
"future"), `bars.md` `recovery.natural` "per tick", `items.md` `on_drop` executes, `drive_as_code.md` "all
fields required", `expressions.md` function inventory, `STRATA.md` §5 ordering contract, `variables.md`
eager-mode clause.

P3s (latent, residue, whitelist and vulture adjudications, `lag(x,0)`, `simplex_noise` is Perlin, Grid2D
`bounce` lacks the clamp 3D/ND have, random initializers reset to the same draw, one-tick lag of expressions
behind transition rules, CLI refusals as tracebacks, path-blind cache identity) are in the per-seam files.

## 3. Backlog disposition — all 45 triage bugs

| disposition | count |
|---|---|
| STILL LIVE | 22 |
| FIXED | 16 |
| OBSOLETE (surface deleted; concern checked on the replacement) | 7 |

**STILL LIVE (22):** 02bd5a3eaa zone scope · 17a7f03bc9 held tool vs empty hand · 1b9af9088c spawn_item unreachable
· 266a0a41f0 interaction progress unobservable · 2aca57c0f0 indistinguishability escape hatch · 2dde1015fe dead
hashes (sharpened to #9 above) · 310e336786 AdversarialCurriculum meters · 45f501e15b max_items_per_agent 0 ·
4b931faaf4 held items invisible · 53bce4af41 inspect json offsets (narrowed: census/hashes now present,
row_layout still not) · 559cc74246 item token identity · 628e202bf7 on_drop inert · 6b24c0bd83 capability vocab
dead · 6c49488b22 item placement 2-D (broader: no spawn off Grid2D/3D) · 7eadeb214c for_each doc (and for_each
has real holes) · 8f2e13c5a9 expressions doc (and the sweep found engine bugs) · a737e444c0 effects can't read
position/time (worse than filed) · b9a3bcbde2 bare vfs.X write fans out · cebe51077a closed phase set (worse:
#3 above) · d45331a367 recovery.natural inert · d76684f549 effects survive reset · f9090ec3e8 wall-clock asserts
(a second one in test_vtc_kernels.py).

**FIXED (16):** 0268336cd1 · 2ca2cb373f (shape; dtype still coerced, P3) · 3381043d2e (ADVANCE witness writes end
to end) · 4cd664a955 · 787aaa29f1 · 83a043a9b9 · 88578e629e · 8b5af63108 (works; doc gap remains) · b3a30b82ef
(partly; residual self/target identity is a new P2) · b5cd718368 · bf42ac60b5 · cb0ccdaa98 (via transition_rules;
cascades themselves still refuse VFS targets) · de52c40c03 · df2b972c49 · f54b887148 (write-side twin is #7
above) · fba3d5aa3c.

**OBSOLETE (7):** 0071c78ee9 · 4597fd5d04 · 5f99e89865 · 8c354c90bb · c6c6c241c5 (surviving half: agent expressions
cannot read globals, P2) · f278b8691f · f2a37a8c8a.

Nothing was written to filigree. Closing the 16 fixed and 7 obsolete entries is a one-liner per id on the
CLI once you nod; the MCP server is down.

## 4. What was refuted (worth knowing it holds)

Each reviewer recorded 10–12 non-reproductions with commands. The ones that matter: the README's static-access
claims hold (policy snapshot immutable and used by publishers; `writable_by: []` enforced; denied writes refuse at
compile including inside `delay … do`); nested effect refusal rolls back fully; cache invalidation on nested,
deleted and mtime-backdated files recompiles; duplicate/missing/unknown declarations refuse with `file:line`;
`period_of` resolves to 24 and a literal duplicate refuses; msgpack round trip preserves every hash and field
except `items_appearance`; `token_type_schema_hash` is identical across 2-D/3-D/4-D/continuous/aspatial (the
CLAUDE.md literal `428982ef` is merely stale, current value `8ad2b59b502a905b`); POMDP keeps `total_dims` and
`layout_hash`; wrap shortest-path deltas and the radius formula are correct; the DAC total formula is exact on a
hand-computed batch; reset fully clears items, inventories and item VFS; same-tick GET race is clean.

## 5. Coverage limits

Not reached by anyone: `environment/env_factory.py`, the meter/variable publishers' internals, checkpoint
position round-trip, CUDA, `population/`, `demo/`, `recording/`, `training/` beyond the checkpoint gate. The
expression function sweep covered all 49 `FUNCTION_SPECS` entries through parser → type checker → evaluator on a
batch of three. Existing suites in scope were run as baselines and are green (vfs 318, substrate 327, effects 428).
