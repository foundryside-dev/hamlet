# Findings — effects

Seam: Universe-as-Code part A — `src/townlet/effects/`, `src/townlet/world/expression/`,
`src/townlet/config/effects_config.py`, `src/townlet/universe/compilers/effects.py`, the effect
call sites in `environment/vectorized_env.py` and `EffectTokenPublisher`.
All scripts: `/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/effects/`
(`repro_d766.py`, `repro_d766_agent.py`, `func_sweep.py`, `dto_probes.py`, `history_probe.py`,
`probe_a.py` … `probe_f.py`; derived packs under `variants/`, built from `configs/test/effects_smoke`
by `packlib.py`). Run from `/home/john/hamlet` with `uv run python <script>`.
Baseline: `pytest tests/test_townlet/unit/effects tests/test_townlet/unit/world tests/test_townlet/unit/vfs/test_expression_*.py` → 428 passed, 2 skipped.

## Backlog adjudication

| id | disposition | evidence (file:line, command, 1-line output) |
|---|---|---|
| hamlet-d76684f549 | **STILL LIVE** (P1, scope-independent) | `environment/vectorized_env.py:801-807` — `reset()` only calls `effect_manager.reset_scheduler()` and cancels agent-scoped *scheduled* items; no `EffectManager` store (`global_effects`/`agent_effects`/`item_effects`/`affordance_effects`, `manager.py:96-99`) is ever cleared — `EffectManager` has no `reset()` method at all (only `reset_scheduler`, `manager.py:425`), so the defect is a missing method plus a missing call. `uv run python scratchpad/effects/repro_d766.py` (trial002, exactly the bug's recipe): `after INTERACT money: [2000.0, 2000.0]` → `effects before reset: [('business_cycle','global',1)]` → `after reset money: [1000.0, 1000.0]` / `effects after reset: [('business_cycle','global',1)]` → `after WAIT money: [2258.819, 2258.819]` / `elapsed_ticks 2`. Agent-scoped variant `repro_d766_agent.py` (effects_smoke `energy_regen` on agent 1): `before reset: [('energy_regen','agent',1,1,19)]` / `after reset: [('energy_regen','agent',1,1,19)]` — same leak, same counters. `README.md:412` honestly lists "effects reset" as incomplete; the bug is not hidden by docs, just unfixed. |
| hamlet-4cd664a955 | **FIXED** (commit `c6c6b524`) | `executor.py:276-294` no longer passes a scope; `manager.py:196` `scope = EffectScope(effect_def.scope)` derives it from the catalog. The d766 repro above shows trial002's `scope: global` effect land in `global_effects` (`('business_cycle', 'global', …)`), and `manager.tick` ticks `global_effects` first (`manager.py:459`). Pinned by `tests/.../test_spawn_effect.py::test_spawn_effect_definition_scope_is_runtime_authority`. Residue: `configs/trial_k_cold/effects.yaml:16-19` still carries the "global is unreachable, pinned to slot 0" workaround comment (stale, harmless). |
| hamlet-a737e444c0 | **STILL LIVE** (P1, both halves; worse than filed) | **Time:** the effects schema is built from `variables.declarations` only (`universe/compilers/effects.py:35-39`); the engine `tick` variable is injected by the VFS compiler (`universe/compilers/vfs.py:38,78`) and never reaches the effects schema. `probe_a.py` C / `probe_c.py` C2: `temporal.tick`, `vfs.tick` and bare `tick` **all refuse at compile** — `Effect 't' failed to compile: Reference traversal requires schema entry for 'vfs.tick'`. `probe_e.py`: `default_curriculum` L3 `effects_schema` keys containing "tick" = `['elapsed_ticks']` only. So the effects.md banner's "✅ correct working form: the bare `tick` variable" is **false for effects**. **Position:** `probe_a.py` D: `distance_to_affordance("FOOD")` and `in_range("FOOD", 2.0)` compile, then `RuntimeError: Spatial operators require agent_positions on the execution context` at the first tick — `_make_eval_context` never passes `agent_positions`/`affordance_positions` (`executor.py:800-815`), `_lifecycle_context` for on_tick/on_despawn passes none (`manager.py:568-575, 600-608`), and `vectorized_env.py:1092-1097` calls `effect_manager.tick(...)` **without** `agent_positions` although `manager.tick` accepts it (`manager.py:436`). `target.position` refuses at compile. |
| hamlet-b3a30b82ef | **FIXED in part / OBSOLETE framing; residual is a NEW finding (F7)** | The "opposite entities" framing is obsolete: `manager.py:290-325 _lifecycle_context` now sets **both** `self_index` and `target_index` to the attached entity for agent/item effects. `probe_b.py` N1: agent-scoped effect `modify: target.vfs.score` on agent 1 → `[0.0, 1.0, 0.0]` — one agent's variable, no KeyError (the filed failure). N3: bare `vfs.score` still writes the whole batch `[1.0,1.0,1.0]` (that is hamlet-b9a3bcbde2, not mine). N2: `self.vfs.score` on an agent variable still refuses at compile (`Path 'self.vfs.score' not found in schema`) because `compilers/effects.py:41-45` emits `self.vfs.*` only for item profiles — so `self.` and `target.` are now the *same* entity in effects, with `self.vfs` unspellable; see F7. |
| hamlet-88578e629e | **FIXED** (DTO side); doc now lies the other way (F12) | `config/effects_config.py:86, 230, 266` — all three DTOs carry `ConfigDict(extra="forbid")`; `observable: bool = Field(...)` is required (`:242`). `dto_probes.py`: `[observable omitted] REFUSED ValidationError`. Residual behavioural defaults: `version: Literal["1.0"] = "1.0"` (`:268`) and `effect_definitions = []` (`:269`) — DTO-policy, handed to the compiler reviewer. |
| hamlet-7eadeb214c | **STILL LIVE** as a doc defect; the shipped `for_each` has real holes (F4, F5, F6) | `probe_a.py` B2: `for_each: all_agents` with `target.bar.health - 0.1` works end-to-end (`[0.9, 0.9, 0.9]`). But: `as: a` is dead (B1, compile refusal `Variable 'a' not found in schema`); `nearby_agents` is unreachable from YAML (B3: `ValueError: radius required`, and `radius` is not a `CommandConfig` field → `dto_probes.py` `[for_each radius] REFUSED`); `active_effects` iterates the attached agent's own index once per active effect (B4: agent 1 with 2 effects got `-0.2`). `docs/config-schemas/effects.md:903-983` still says the collections are "(future)" and teaches `as:` as working. |
| hamlet-8f2e13c5a9 | **STILL LIVE** as a doc defect; recount confirmed; sweep found engine bugs (F3, F8, F9, F10) | `func_sweep.py`: `FUNCTION_SPECS count: 49`, every entry parsed, type-checked and evaluated on a batch-3 context (table in Coverage). 48/49 evaluate on their declared inputs under the *enriched* context (11 of them crash under the effects context — the 7 history ops, `elapsed_ticks()`, and the 3 affordance-spatial ops; see F9); **`mean(int,int)` crashes** (`mean(): could not infer output dtype … Got: Long`). `docs/config-schemas/expressions.md:309-316, 407-415, 965-977` still carry the "planned" labels and the `if … then "healthy" else "injured"` example (`:347`) type-checks but crashes (`torch.where` on str). |

## New findings (ranked, most severe first)

### F1. `modify: bar.X value: <scalar>` rebinds the bar to a stride-0 broadcast view; the next indexed write in the same tick silently lands on every agent
- severity: P1 (silent data corruption)
- where: `effects/executor.py:230-231` (`result.expand_as(original)`), `effects/context.py:279` (`self.bars[bar_name] = value` rebinds instead of `copy_`), `effects/context.py:227-229` (`original[self.target_index] = value` in-place on the view)
- failure scenario: effect A `modify: bar.health value: "0.3"` (scalar → expanded view, `stride (0,)`), effect B on agent 1 `modify: target.bar.health value: target.bar.health + 0.1` in the same tick → all agents become 0.4. Any `bar.X` scalar modify followed by any `target.bar.X` / `self.bar.X` / for_each write to the same bar.
- reproduction: `uv run python scratchpad/effects/probe_d.py` → `after scalar modify: bars.x = [0.3,0.3,0.3] stride: (0,) is_contiguous: False` / `after target.bar.x += 0.1 on agent 1 only: [0.4, 0.4, 0.4]`. End-to-end in `probe_b.py` I: `health after tick: [0.4, 0.4]` (agent 0 should be 0.3).
- note: `set_path("bar.*")` should `copy_` into the existing tensor (or `expand_as(...).clone()`).

### F2. The `if` *command* reduces a per-agent condition with `.any()` and runs the branch for every agent
- severity: P1 (wrong behaviour)
- where: `effects/executor.py:464-469`; the `switch` command does the same batch reduce at `executor.py:598-602` (`comp.any()` selects the case for every agent)
- failure scenario: `if: "bar.health < 0.5" then: [modify bar.energy …]` with one low agent applies the penalty to all agents; the expression-form `if C then A else B` is element-wise (`evaluator.py:128`), so the same keyword has two semantics.
- reproduction: `probe_b.py` F → `health: [1.0, 0.1, 1.0] energy (only agent 1 low; expect only agent 1 -0.5): [0.49, 0.49, 0.49]`.
- note: scoped forms (`target.bar.*` in agent-scoped effects) evaluate to a scalar and are safe; the bare `bar.*` vocabulary the docs teach is not.

### F3. `mean()` type-checks as float but crashes on int inputs; three other functions return a dtype that disagrees with the type checker
- severity: P1 for `mean` (compile-clean → runtime crash); P2 for the rest
- where: `world/expression/functions.py:409-420` (`mean`), `:435-459` (`sum`/`product` declare float, return int64 on int args), `:355-366` (`clamp01` declares `_return_numeric` → int, returns float), `type_checker.py:280-282` (`/` declares int for int operands, evaluates float)
- failure scenario: `modify: bar.health value: "bar.health * mean(1, 2)"` compiles and crashes at the first tick. `elapsed_ticks` is schema'd `float` (`compilers/effects.py:27`) but injected as int64 (`executor.py:752`): `modify: vfs.score value: "elapsed_ticks"` on a float variable compiles then raises `ValueError: Value for 'score' has dtype torch.int64, expected torch.float32`.
- reproduction: `probe_c.py` O2 → `compiled OK` then `RuntimeError: mean(): could not infer output dtype … Got: Long`; `probe_d.py` V → `ValueError: Value for 'score' has dtype torch.int64, expected torch.float32`; `func_sweep.py` rows `sum | declared float | int (3,)`, `product | float | int (3,)`, `clamp01 | int | float (3,)`; `probe_c.py`: `'42 / 10': declared=int value=float32 4.2`.

### F4. `for_each … as: <name>` is accepted, parsed, stored, and never bound — the iterator is unreachable from any body expression
- severity: P2 (declared field with no consumer; doc teaches it)
- where: `config/effects_config.py:108` (`as_`), `effects/parser.py:101` (→ `CommandNode.iterator`), `executor.py:557-561` (`iterator_value` set on the child context), `executor.py:719-815` (`_make_eval_context` never injects it; only REDUCE binds `reduce_iterator`/`acc` at `:650-658`)
- failure scenario: `for_each: all_agents, as: a, do: [modify target.bar.health value: "… * a"]` → compile refusal naming `a` as an unknown variable.
- reproduction: `probe_a.py` B1 → `Effect 'fe' failed to compile: Variable 'a' not found in schema. Available variables: ['intensity', 'elapsed_ticks', …]`. `effects.md:903-983` says "Iterator Variable: Available inside do commands".
- note: either bind `iterator_value` into the eval context under `node.iterator` (and add it to the schema at compile time), or delete `as`.

### F5. `nearby_agents` resolver is unreachable from YAML: `radius` exists on `CommandNode` but not on `CommandConfig`, and positions are never threaded anyway
- severity: P2 (dead declared vocabulary; `effects.md:939` teaches `nearby_agents(radius=2)`)
- where: `effects/schema.py:80` (`radius`), `effects/parser.py:97-103` (never sets it), `config/effects_config.py:69-133` (no `radius`, `extra="forbid"`), `effects/collections.py:20-33`; same for `spawn_item` `quantity`/`initial_state` (`schema.py:59-60`, preflight machinery at `executor.py:178-183`, no DTO field)
- reproduction: `dto_probes.py` → `[for_each radius] REFUSED ValidationError`, `[spawn_item quantity] REFUSED`, `[spawn_item initial_state] REFUSED`; `probe_a.py` B3 → compiles, spawns, then `ValueError: radius required for 'nearby_agents' collection`; with `radius` forced on the compiled node (`probe_c.py` B3b) → `ValueError: agent_positions required for 'nearby_agents' collection` (env never passes positions into `manager.tick`, see a737e444c0). The resolver also uses `torch.norm` (Euclidean, no wrap) regardless of the substrate's declared metric (`collections.py:30`).

### F6. `for_each: active_effects` iterates the attached agent's own index once per active effect
- severity: P2 (declared collection with nonsense semantics)
- where: `effects/collections.py:48-54` returns `[eff.target_entity_id …]`, i.e. `self_index` repeated N times; the body's `target.*` then hits the same agent N times.
- reproduction: `probe_a.py` B4 → agent 1 with 2 active effects and body `target.bar.health - 0.1` → `[1.0, 0.8, 1.0]`.

### F7. In an effect, `self.` and `target.` are now the same entity, `self.vfs.X` is unspellable for agent variables, and `affordance`-scoped effects address an *agent* row
- severity: P2
- where: `manager.py:305-313` (`self_index = target_index = entity_id`), `compilers/effects.py:38-45` (`self.vfs.*` emitted only for item profiles), `manager.py:339-345` (affordance scope keyed by `str(entity_id)`), `_lifecycle_context` sets `target_index=entity_id` for `affordance` and `global` scopes too
- failure scenario: an affordance-scoped effect's `target.bar.health` writes agent `entity_id`; a global effect's `target.bar.*` writes agent 0. No path from any effect to "this affordance" (`effects.md:217-250` promises `target.availability`, `target.position`).
- reproduction: `probe_b.py` K → affordance-scoped effect on "affordance 1": `health per agent: [1.0, 0.9, 1.0]`; K2 → global effect `target.bar.health`: `[0.9, 1.0, 1.0]`; N2 → `Path 'self.vfs.score' not found in schema`.

### F8. Spatial distance functions refuse their intended vector inputs and collapse the batch axis on scalar inputs
- severity: P2 (vocabulary that cannot produce a per-agent value)
- where: `functions.py:979-1006` (`.sum(dim=-1)` over a `[batch]` tensor), `:36-38` `_ensure_all_numeric` admits only `int`/`float`
- failure scenario: `distance(vfs.position, vfs.position)` on `vec2f` → compile refusal; `distance(bar.energy, bar.health)` → one scalar for the whole batch, then broadcast to every agent by `modify`. `within_radius(...)` likewise returns a single bool; `nearest` returns shape `(1,)`.
- reproduction: `probe_e.py` AA → `Function 'distance' requires numeric args, got ['vec2f', 'vec2f']`; AB → `[0.89999, 0.89999, 0.89999]` with agent 0's energy zeroed (batch collapsed); `func_sweep.py` rows `distance | float ()`, `manhattan_distance | float ()`, `within_radius | bool ()`, `nearest | int (1,)`, `normalize | float (2, 3)`, `one_hot | float (3, 3)`.

### F9. Temporal operators compile inside effects and always crash at runtime; `elapsed_ticks()` as a function likewise
- severity: P2 (compile-clean, runtime crash)
- where: `executor.py:44, 815` (`ExprExecutionContext(... temporal={})`, no `history`, no `step`); `functions.py:194-203 _require_history`, `:762-766`
- reproduction: `probe_d.py` Z → `compiled OK (lag in effect)` then `RuntimeError: Temporal operators require a TemporalHistory on the execution context`; `func_sweep.py` bare-context column: `lag/delta/ema/moving_average/rate_of_change/rising_edge/falling_edge` all `ERR RuntimeError`, `elapsed_ticks() → requires context.step`. Only `vfs/evaluator.py:161-170` threads history/step/positions, so the whole temporal and affordance-spatial families are VFS-profile-only, and the effects compiler does not refuse them.

### F10. `time_in_window` hardcodes a 24-tick day; the pack's declared clock period is ignored
- severity: P2 ("engine knows the game": `day_length` is authored per pack, CLAUDE.md)
- where: `functions.py:731` `period = torch.tensor(24.0, …)`
- reproduction: `probe_d.py` X → `time_in_window(tick=25, 1, 3)` = `True` regardless of any declared day length.

### F11. A registry variable named `intensity` (or `elapsed_ticks`, `duration_remaining`) silently shadows the effect's own lifecycle scalar
- severity: P2 (silent wrong value)
- where: `executor.py:749-773` — effect scalars are written into `vfs_dict` first, then every registry variable is written over them by id.
- reproduction: `probe_d.py` U → variable `intensity = 5.0`, spawn intensity 1.0, `bar.health - 0.1 * intensity` → `[0.5, 0.5]` (expected 0.9).

### F12. `effects.md` lies about the DTO in both directions (fields that are refused, fields that are required)
- severity: P2 (doc actively contradicts behaviour; `extra="forbid"` makes it a refusal)
- where: `docs/config-schemas/effects.md:286-314` documents an effect-level `intensity` field; `:433-436` says `observable` is optional (default true); `:259-284` says `duration: 1` means "only on_spawn executes"; `:691-700` says `spawn_effect` `target`/`intensity` are optional with defaults; `:625-660` lists `temporal.*`, `sqrt`, `sin`, `cos`, and a Python-form ternary.
- reproduction: `dto_probes.py` → `[effect intensity field] REFUSED ValidationError`, `[observable omitted] REFUSED`; `config/effects_config.py:168-172` requires `target` and `intensity`; `probe_c.py` S → duration-1 effect: `after spawn: [1.0,1.0]` → `after 1 tick: [0.7, 0.7] active: 0` (on_tick fired once).

### F13. `switch` cases are untyped dicts: a typo'd `do` key compiles to an empty case
- severity: P2 (defeats `extra="forbid"` — the exact No-Defaults hole the DTO fix closed elsewhere)
- where: `config/effects_config.py:113` `cases: list[dict[str, Any]]`; `effects/parser.py:111` `case.get("do") or []`
- reproduction: `probe_d.py` Y → case `{when: "1", doo: [modify bar.health 0.0]}` compiles; health unchanged `[1.0, 1.0]`.

### F14. An `observable: true` effect in a scope whose `max_active_effects` budget is 0 compiles, spawns, and is silently absent from the observation; non-observable effects never count against the budget
- severity: P2 (misleading declaration)
- where: `vectorized_env.py:950-953` (`if not slots: continue`), `:949` only iterates observable effects; `config/effects_config.py:270-278` describes the budget as "concurrently active effects"
- reproduction: `probe_c.py` R2 → `global budget 0`, observable global effect: `compiled OK; effect census: 0 active: 1`; `probe_b.py` G2 → 3 stacked `observable: false` effects against `agent: 2`: `step OK` (G1 with `observable: true` correctly raises `TokenCapacityError … 3 live instance(s) but compiled capacity is 2`).

### F15. Two affordances identical in every declared parameter (including deployment position) compile; the indistinguishability check covers only variables
- severity: P2 (CLAUDE.md: "two entities identical in every declared parameter are refused at compile time")
- where: `universe/dto/token_spec.py:1099-1110 check_indistinguishability` is called once, for exposed variables (`:1520`); `effects/affordance_identity.py` builds the affordance signature from interaction type, duration, opening hours and meter writes (`token_spec.py:1181-1189`), never compared across affordances. Two effects differing only in `id` also compile (`probe_c.py` T); the effect token tells them apart only via the catalog ordinal (`context_index` lane), a name-derived index.
- reproduction: `probe_f.py` AC2 → BED and FOOD with identical interactions and identical position: `compiled OK`. (Shared with the compiler reviewer; reported here because `affordance_identity.py` is in this seam.)

### F16. Two effects writing the same bar in one tick: earliest-spawned wins, undocumented
- severity: P3 (order dependence)
- where: `manager.py:483` iterates `reversed(effects.copy())`, so the most recently spawned effect runs first and the oldest writes last.
- reproduction: `probe_b.py` H → `a` (sets 0.3) spawned before `b` (sets 0.7): `health after tick: [0.3, 0.3]`.

### F17. `lag(x, 0)` returns the value from `window` ticks ago, not the current value
- severity: P3
- where: `history.py:89-95` — `target = (idx - 0) % window` is the slot about to be overwritten (oldest), and `valid = warm >= 0` is always true.
- reproduction: `history_probe.py` → window 3, values 1,2,4,8,16: `step 3 cur=8.0: … lag0=1.0`, `step 4 cur=16.0: … lag0=2.0`.

### F18. `uniform()` / `normal_dist()` with no (or scalar) arguments draw one value shared by every agent
- severity: P3 (latent; undocumented semantics)
- where: `functions.py:678-699` (`torch.rand(())` when no args; `rand_like(ts[0])` follows the first arg's shape, which is `()` for literals)
- reproduction: `probe_b.py` Q → `modify: bar.health value: "uniform(0.0, 1.0)"` on 4 agents: `[0.2089, 0.2089, 0.2089, 0.2089]`.

### F19. Dead executable surface and swallowed exceptions in the seam (vulture confirmed)
- severity: P3
- where: never called in `src/`: `manager.py:615 _build_context`, `manager.py:655 cancel_effect`, `collections.py:65 register_collection_resolver`, `functions.py:110 _eval_stack_numeric`, `type_checker.py:214/224/232 _lookup_ref_type/_fallback_target_lookup/_fallback_item_lookup`; never read: `ActiveEffect.effect_index` and `EffectCatalog.effect_id_to_name` (the publisher orders by `token_spec.effect_catalog_contexts`, `vectorized_env.py:931-938`), `ExecutionContext.iterator_value` (F4), `ScheduledItem.due_tick`, `ActiveEffect.spawn_step`. `effects/parser.py:87-92` wraps the resolver import in `except Exception: collection_resolvers = {}` — an import failure would silently turn `all_agents` into an expression and surface as "Variable 'all_agents' not found". `token_publishers.py:186` docstring cites the deleted `vfs/observation_builder.apply_normalization` (residuals.txt:94).
- `.defaults-whitelist.txt:173-185, 194-197` blanket `:*` every file in this seam; `scripts/no_defaults_lint.py --whitelist /dev/null` on them reports **87** hidden defaults, including executable ones: `executor.py:744 getattr(self, "device", cpu)` on an object that never has `device`, `context.py:148 affordance_overrides.get(aff_name, True)`, `executor.py:343 quantity or 1`, `executor.py:730 effect or context.effect`.

### F20. `simplex_noise` is `perlin_noise` under another name
- severity: P3 (declared vocabulary whose name promises a different algorithm)
- where: `functions.py:303-318` — `eval_fn` is byte-identical to `perlin_noise` (`:285-300`), both call `_perlin_2d`.
- reproduction: read-only; `func_sweep.py` evaluates both to `float (3,)` with the same kernel.

## Refuted

- **README "nested refusal rolls back immediately" (PR #44) holds.** `probe_d.py` W: outer `on_spawn` writes `bar.health - 0.5` then spawns inner; inner writes `bar.energy - 0.5` then a write denied by an injected `PermissionError` on `authorize_write` → `PermissionError propagated`, `health/energy after denied cascade: [1.0,1.0] [1.0,1.0] active effects: 0 next_instance_id: 0`. `admission.py` snapshot restores bars, stores, ids.
- **"Known denied authored targets refuse at compilation" (README:156) holds for effects, including inside `delay … do`.** `probe_a.py` A1/A2/A3: `writable_by: []` variable written from `on_tick`, from `on_spawn` after a bar write, and from a delayed block → `[UAC-STATIC-WRITE] … Variable 'locked' denies engine write required by effects:ro:on_spawn[1].delay_do[0]`. The runtime "delay carve-out" in `_preflight_command` is therefore unreachable for static targets.
- **`do:` alias collision between `for_each` and `delay`** — both fields receive the list, nothing breaks (`dto_probes.py` `[for_each do] OK`, `[delay do] OK`). `delay_do:` as a YAML key is also accepted (populate_by_name) — cosmetic.
- **Effect token presence/payload is cleared after despawn.** `probe_b.py` G3: tick 1 row `[1.0, 0.0, 0.5, 0.5, 0.0, 0.0]`, after despawn `[0.0, 0.0, 0.0, 0.0, 0.0, 0.0]` (`token_publishers.py:731-736`, and `_effect_slot_batch` returns `None` → publisher early-return leaves the pre-zeroed row).
- **Capacity overflow is loud for observable effects.** `probe_b.py` G1 → `TokenCapacityError: Token type 'effect' overflow at publish time: 3 live instance(s) but compiled capacity is 2 (source: effect_manager scope 'agent')`.
- **Scalar `modify: bar.X` does write back to `env.meters`** (`probe_b.py` I2 → `[0.3, 0.3]`); the corruption in F1 needs a second indexed write.
- **`for_each: all_agents` + `target.bar.*` works end-to-end** (`probe_a.py` B2), and **`target.vfs.X` from an agent-scoped effect addresses one agent** (`probe_b.py` N1) — the KeyError in b3a30b82ef no longer reproduces.
- **Temporal history ordering is correct under the VFS evaluator's evaluate-then-push order** (`history_probe.py`): `lag(1)` = previous value, `lag(3)` at step 3 = `vals[0]`, `moving_average(2)` = mean of current and previous, `rising_edge`/`falling_edge` fire on the transition tick only. Only `lag(…, 0)` is wrong (F17).
- **`scope: global` reaches `EffectManager.global_effects`** (see 4cd664a955).
- **`spawn_effect: target: "agent"` (the effects.md for_each example)** is refused at compile, not silently accepted: DTO accepts the string, parser leaves `target=None`, type checker refuses `Variable 'agent' not found` — loud.
- **`bar.i / 0`, `bar.health / 0.0`** evaluate to `inf` (no crash, no clamp) — consistent with torch; `bar.i % 0` raises `ZeroDivisionError`. Not reported as a defect.
- **The "authorize loops without evaluating selection" fix (45ba42bb)** — I found no path that evaluates a collection before authorizing: `_preflight_command` uses a placeholder child for non-inventory collections, `_execute_for_each` resolves then preflights every body before the first mutation. Pinned by `test_command_preflight_selection.py`.
- **meter_literals.txt entries in this seam** (`type_checker.py:60/68`, `ast_nodes.py:127/159`, `expression/context.py:23`) are all docstrings/comments — no executable branch on a meter name.

## Coverage

- **Read fully:** `effects/executor.py`, `manager.py`, `context.py`, `admission.py`, `compiler.py`, `catalog.py`, `collections.py`, `scheduler.py`, `schema.py`, `parser.py`, `affordance_identity.py`; `config/effects_config.py`; `universe/compilers/effects.py`; `world/expression/functions.py`, `context.py`, `evaluator.py`, `history.py`, `type_checker.py`, `parser.py`; `vectorized_env.py` effect call sites (init 190-220, reset 780-830, step 1040-1110, 1195-1225, `_effect_slot_batch`/`_observable_effects_for_world` 916-1001); `EffectTokenPublisher` (`token_publishers.py:318-360, 665-736`); `docs/config-schemas/effects.md` banner, field reference §scope/duration/intensity/observable, command language §modify/if/for_each; `expressions.md` banner, roadmap, functions, future sections; README effect claims (150-165, 412).
- **Skimmed:** `world/expression/ast_nodes.py`, `world/types/primitive.py`, `vfs/evaluator.py` (only the context-construction and history push sites), `items_config.py` command validation, `token_spec.py` affordance signature / indistinguishability entry points, the effects test file names and `test_command_preflight_selection.py`.
- **Executed:** 49/49 `FUNCTION_SPECS` entries (bare and enriched contexts; sweep table is the output of `func_sweep.py`, summarised in F3/F8/F9); 40 pack-variant / executor-level probes; both backlog reproductions.
- **Not reached:** item-scoped effects end-to-end (`item_effects`, `self.vfs` on items, `inventory_items` collection) beyond the existing tests; `sample`/`reduce`/`parallel`/`switch` command runtime semantics beyond the switch typo probe; CUDA device propagation; `perlin_noise` numeric correctness against a reference (only shape/dtype checked); the `_execute_scheduled_items` context derivation for global/affordance-scoped delayed work; `ActionConfig`/affordance interaction compilation (compiler reviewer's seam) except as needed for F15.
