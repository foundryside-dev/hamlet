# Findings — VFS, round 2 (2026-10-24, after WP1–WP8 landed)

Reviewer seam: the VFS contract one layer below round 1 — reset/evaluation identity, observation publication under POMDP, scope semantics under the batched runtime, hash provenance, expression reachability, and the authoring surface itself. All probes are CPU-only, run as `cd /home/john/hamlet && uv run python review-2026-10-24/vfs_round2/<script>.py`; each script has a `.log` beside it with the verbatim output quoted below. Scratch packs are clones under `review-2026-10-24/vfs_round2/packs/`, built by `vfs_round2/harness.py` (round 1's harness plus `ve_rows`/`type_rows`, which map compact observation rows back to their slot `filler_ref`). Base pack is `configs/static_epistemic_access` (the "witness") unless stated. Nothing round 1 reported, or that WP1–WP8 fixed, is repeated here.

## Executive summary

1. **The shipped clock is wrong twice in every L3 episode.** `day_phase` (`expression: tick`) is published one tick behind the `time_of_day` that gates opening hours, and the first observation after `reset()` carries the *previous episode's* last hour (`default_curriculum/L3`: reset obs hour 5.0 while `time_of_day` is 0) — F1, F2.
2. `reset()` never evaluates expressions: every expression variable shows its literal (episode/tick lifetime) or stale value (persistent) in the first observation of every episode (F1).
3. Under `active_vision: partial`, item-state `variable_element` rows stay present with live values when the item token itself is hidden — a POMDP leak (F3).
4. `num_agents` is a batch of independent worlds (agent token capacity is always 0), yet `global` storage is one slab for the whole batch: one world's SLEEP raised another world's observation and reward (F4, S1).
5. Expression text enters no checkpoint-gated hash: tripling a rewarded expression moved **no** hash while reward went 2.0 → 6.0 (F5).
6. The compiler type-checks writes but does not shape-prove them: pair/message reads in action writes, agent-shaped values into global rule targets, and spawn conditions spelled `env.X`, bare meter or `temporal.*` all compile green and crash at step or reset (F6).
7. `message` scope is write-only to the sender's own buffer and has no reader; `pair` writes from agent values land on the column axis including the diagonal (F7, F8).
8. The temporal-history pipeline (`lag`, `delta`, `ema`, …, `vfs_history_spec`) is dead by construction: the shape proof refuses every temporal function (F9).
9. Spec problems: `agent_private` can do strictly less than `agent` + `readable_by: [engine]`; the identity rule refuses hunger/thirst-style pairs unless the author perturbs behaviour; one variable has five spellings across consumers (S2, S3, S5).
10. Counts: **14 findings (5 P1, 8 P2, 1 P3) and 10 spec problems.** Fix S1 first: deciding what `global` means under a batch of worlds is the only spec decision here that changes what a policy learns.

## F-table (implementation against spec)

| id | sev | gap | defect site | script |
|---|---|---|---|---|
| F1 | P1 | `reset()` evaluates no expression; first obs of every episode shows the literal (or, for persistent, last episode's value) | `environment/vectorized_env.py:736-830` (sole `_evaluate_vfs_profiles` call is `:1101` in `step`) | `r1_reset_expression.py`, `r2_shipped_clock.py` |
| F2 | P1 | The registry `tick` (and every clock derived from it) is published one tick behind engine time; the observed hour lags the hour that gates affordances | `vectorized_env.py:1057` (tick written before increment at `:1109`; `time_of_day` set after it at `:1149`) | `r1_reset_expression.py`, `r2_shipped_clock.py` |
| F3 | P1 | Item-state `variable_element` rows ignore the visibility filter under `active_vision: partial` | `environment/token_publishers.py:1030-1073` (`ItemArenaVariableElementPublisher.publish`) | `r3_item_state_vision_leak.py` |
| F4 | P1 | `global` storage is shared by a batch the token model treats as independent worlds; per-world events write it and every world observes and is rewarded on it | `vfs/registry.py:350-353` (global prefix `()`), `token_publishers.py:893` (`arenas["global"].tensor[0]` broadcast to all worlds), `universe/dto/token_spec.py:1294-1307` (agents_per_world always 1) | `r12_global_cross_world.py` |
| F5 | P1 | Expression text is in no checkpoint-gated hash; a changed reward-feeding expression resumes silently | `universe/compilers/vfs.py:83-107` (expression never reaches `VariableDef`), `vfs/schema_hashes.py:160-180`, `training/checkpoint_utils.py:69` (no variables pack hash) | `r8_hash_coverage.py` |
| F6 | P2 | Writes and spawn conditions are type-checked, not shape-proved or context-checked: three families compile green and crash at runtime | `vfs/vtc.py:426-441`, `:941-947`, `:1785-1791`; `universe/compilers/vfs.py:204-211` vs `items/manager.py:604-616`, `vectorized_env.py:823` | `r4_…`, `r6_…`, `r13_…`, `r13b_…` |
| F7 | P2 | A pair target receiving an agent-shaped value writes it down the column (the *other* agent), diagonal included; no declared direction | `vfs/vtc.py:1773-1776` | `r6_rules_pair_global.py` |
| F8 | P2 | `message` `append_event`: the sender appends to its own row; payload 0 is "free"; a nonzero initial value makes every append vanish; a full buffer drops silently; nothing can read the buffer | `vfs/vtc.py:806-827`, `:860-864` | `r5_message_scope.py` |
| F9 | P2 | Temporal operators are refused by the shape proof, so `vfs_history_spec`, `collect_history_requirements`, `TemporalHistory` and the evaluator's history push are dead by construction | `vfs/profiles.py:417-434`; `universe/compiler.py:299-301`; `vfs/evaluator.py:25-71`; `universe/compiled.py:208` | `r9_history_operators.py` |
| F10 | P2 | A `tick`-lifetime expression variable is never visible to any transition write (always its reset literal); variables.md:158-159 says writes see the previous tick's value | `vectorized_env.py:1060` (`reset_tick_scoped` before action phases) | `r11_lifetime_expression.py` (a) |
| F11 | P2 | Action writes and transition rules targeting an expression-owned variable compile and are silently overwritten at evaluation | `vfs/vtc.py:2176` (`_action_write_scope_refusal`), `:1928-1945` (rule target check) — neither consults expression ownership | `r11_lifetime_expression.py` (b) |
| F12 | P2 | Token-spec refusals (e.g. indistinguishability) escape the compiler as a bare `ValueError` with no code, stage or `file:line` | `universe/compiler.py:376` → `compilers/observation.py:77` → `dto/token_spec.py:1107` | `r10_indistinguishable.py` |
| F13 | P2 | `persistent` VFS state is not checkpointed; resume restarts it at initial values (the affordance layout, by contrast, is restored) | `demo/runner.py:277-292` (payload), `:349-365` (load) | `r15_persistent_not_checkpointed.log` |
| F14 | P3 | Residue: L5 exposes two never-written variables (constant tokens) and allocates pair/affordance state nothing writes; engine computes an unreachable `temporal.is_night` with a hidden "first/last quarter" constant; doc scope tables contradict | `configs/L5_multi_agent/variables.yaml`; `vectorized_env.py:513-528`; `CLAUDE.md:289`, `docs/architecture/VFS.md` §5.1/§5.2 | `r16_L5_inert.py` |

## S-table (spec against product)

| id | problem | smallest fix |
|---|---|---|
| S1 | The spec never says whether the `num_agents` batch is one shared world or N worlds; `global`, `pair`, `message` and items assume shared, the token spec assumes independent | Rule it explicitly. Either give `global` a per-world axis (and refuse `pair`/`message` until agents_per_world > 1 is declarable), or declare agents-per-world and make the agent token real |
| S2 | `agent_private` does strictly less than `agent` + `readable_by: [engine]` (it cannot be a reward input or an expression input) and silently overrides a declared `readable_by: [engine, agent]` | Delete the scope (privacy is already `readable_by`/`exposed_to`), or give it every `agent` consumer and refuse `agent` in its `readable_by` |
| S3 | The identity rule refuses two exposed variables with equal declared parameters (hunger/thirst), even for flat brains; the only escape is to change behaviour (initial 0.001) | Apply the refusal only to permutation-invariant brains, and let declared dynamics (write deltas, rule rates) enter the descriptor as meters' rates do |
| S4 | A named derived quantity (expression variable) cannot be a same-tick input to a write: one-tick lag always, never for `tick` lifetime. Authors must inline the predicate | Macro-expand expression variables into write/condition ASTs at compile, or evaluate profiles before the action phases too |
| S5 | One variable, five spellings across five consumers; two spawn spellings compile and crash | One resolver and schema builder shared by every consumer; one spelling |
| S6 | `message` has no communication semantics: no recipient, no sender metadata, no reader, but a required extent | Delete it (as zone/group were), or define delivery to an addressed recipient's row plus a reader |
| S7 | `pair` has no way to address a specific pair from an event and no reader; under S1's independent worlds, pairs span worlds | Delete until a partner binding (`other.`) and a reader exist, or define both |
| S8 | Transition rules: `reads` is required and never checked (it can name nothing real); `kind` is a three-valued label with no behaviour; the family is named `social_residue` for what is the general per-tick VFS dynamic | Derive reads from the ASTs; delete `kind`; rename the family |
| S9 | A "time since event" or accumulator mechanic needs three declarations in three families (variable, transition rule, affordance effect); L5's `time_since_last_sleep` shows the intent, unwired | Admit `lag(x, 1)` with lag-only self-edges allowed, so `where(event, 0, lag(t, 1) + 1)` is one declaration (needs F9) |
| S10 | Docs contradict each other on scope count, sparse pairs, the lag rule and `persistent` | Correct in the WP that touches each |

---

## Findings

### F1. `reset()` evaluates no expression variable — the first observation of every episode is wrong
- **severity:** P1. The policy acts on the first observation of every episode, and the value there is not what the expression computes.
- **where:** `VectorizedHamletEnv.reset` (`vectorized_env.py:736-830`) calls `reset_episode_scoped()` (`:771`) and writes `tick` (`:777`) but never calls `_evaluate_vfs_profiles` (only call site: `step`, `:1101`). Episode- and tick-lifetime expression variables therefore publish their declared literal. Persistent ones publish whatever the last step of the previous episode computed.
- **spec:** variables.md: "Expressions are evaluated once per tick, after every transition phase … so an expression always reads this tick's writes". `reset()` produces an observation without that evaluation.
- **reproduction** (`r1_reset_expression.py`: witness plus agent `e_energy: bar.energy * 2.0` exposed, global `g_persist_tick: tick` persistent, `g_episode_tick: tick` episode):
  ```
  reset#1: … e_energy reg=[0.0, 0.0] (true 2*energy=[2.0, 2.0]) g_persist_tick=0 …
     obs rows (presence,lane0,lane1): e_energy=[1.0, 0.0, 0.0] …
  step5:  … g_persist_tick=4 g_episode_tick=4 …
  reset#2: … e_energy reg=[0.0, 0.0] (true 2*energy=[2.0, 2.0]) g_persist_tick=4 g_episode_tick=0
     obs rows: e_energy=[1.0, 0.0, 0.0] g_persist_tick=[1.0, 0.04, 0.0] …
  reset#2+step1: … g_persist_tick=0 …
  ```
  On the shipped pack (`r2_shipped_clock.py`, `default_curriculum` L3, `day_phase` is `lifetime: persistent`, `expression: tick`):
  ```
  step30: obs day_phase hour=5.0 time_of_day(gates opening hours)=6 global_tick=30
  reset#2: obs day_phase hour=5.0 registry day_phase=29 time_of_day=0
  reset#2+step1: obs day_phase hour=0.0 time_of_day=1
  ```
  Episode lengths vary, so in every L3 episode after the first, the first observed hour is the previous episode's final hour mod 24. To the policy that is noise. Then the clock jumps.
- **fix:** call `_evaluate_vfs_profiles()` at the end of `reset()`, after the tick write and item spawn and before `_get_observations()`. With F2 fixed as well, `day_phase` no longer needs `lifetime: persistent` to look right.

### F2. The VFS `tick` (and so `day_phase`) is one tick behind the engine clock that gates affordances
- **severity:** P1. In the same observation, the clock token says hour *k−1* while the next action is gated at hour *k*.
- **where:** `step()` writes `tick ← global_tick` at `vectorized_env.py:1057`, evaluates expressions at `:1101`, increments `global_tick` at `:1109`, and derives `time_of_day = global_tick % day_length` at `:1149`. The observation is built at `:1151` and carries the pre-increment tick. `_is_affordance_open` (`:496`) gates the next step's interactions with `time_of_day`, the post-increment value.
- **reproduction:** `r1_reset_expression.py`. `tick_mirror: tick + 1.0` equals `global_tick` exactly:
  ```
  reset#1: global_tick=0 registry tick=0 … tick_mirror=0
  step1:   global_tick=1 registry tick=0 … tick_mirror=1
  step2:   global_tick=2 registry tick=1 … tick_mirror=2
  ```
  `r2_shipped_clock.py` (L3, decoding the `day_phase` sin/cos lanes back to an hour):
  ```
  reset: obs day_phase hour=0.0 … time_of_day=0
  step1: obs day_phase hour=0.0 time_of_day(gates opening hours)=1
  step2: obs day_phase hour=1.0 time_of_day(gates opening hours)=2
  ```
  The reset observation and the first post-step observation carry the same hour. A shop that opens at hour 8 is open when the token reads 7.
- **fix:** decide what `tick` means and make every clock agree. The smallest change: write `tick` after the increment and before evaluation, or evaluate after `:1109`, so the observation describes the state the next action is taken in. `token-obs ruling 6` ("one temporal primitive") is violated today: there are two primitives, one tick apart.

### F3. Item-state rows leak through the visibility filter
- **severity:** P1. Under partial observability, the policy sees that an item exists in a given slot, and its state, while the item token itself is hidden.
- **where:** `ItemArenaVariableElementPublisher.publish` (`token_publishers.py:1030-1073`) sets presence from `live & profile-match` only. It never consults `ctx.vision_range` or `substrate.visible()`. `ItemTokenPublisher.publish` (`:632-662`) does, and zeroes the item token's presence and payload. CLAUDE.md and token-obs §3: out-of-range spatial tokens have presence and payload zeroed.
- **reproduction:** `r3_item_state_vision_leak.py` (`configs/test/items_smoke` with `active_vision: partial`, `vision_range: 0.2`, radius 1; medkit exposes `medical.durability`):
  ```
  trial0: agent@[4, 4] medkit@[2, 3] manhattan=3 (radius 1) | item token slot3 presence=0.0 | medical.durability[3] row=[1.0, 1.0, 0.0]
  trial2: agent@[1, 4] medkit@[4, 0] manhattan=7 (radius 1) | item token slot3 presence=0.0 | medical.durability[3] row=[1.0, 1.0, 0.0]
  trial3: agent@[1, 2] medkit@[1, 3] manhattan=1 (radius 1) | item token slot3 presence=1.0 | medical.durability[3] row=[1.0, 1.0, 0.0]
  ```
- **fix:** have the publisher compute visibility the way the item token does (positions from `ctx.item_slots`, `visible | carried`), and AND it into `mine_live`. The two publishers should share one per-slot visibility mask.

### F4. `global` state couples worlds the observation model treats as independent
- **severity:** P1. A policy is rewarded for, and observes, events in a world it is not in.
- **where:** the token spec fixes agents-per-world at 1 (`token_spec.py:1294-1307`, `declared_agents_per_world=None` at every call, `:1583-1695`), so agent capacity is 0 and each batch row is its own world (token-obs spec: "`default_curriculum`'s population of 8 is 8 *independent* worlds"). But `global` storage has prefix shape `()` (`registry.py:350-353`), and the registry publisher broadcasts `arenas["global"].tensor[0]` to every world (`token_publishers.py:893`). Effects write globals from a per-agent interaction context (`vfs.X` in an affordance effect). The reward reads the shared value for every world.
- **reproduction:** `r12_global_cross_world.py` (global `visits`, exposed and rewarded at weight 1; SLEEP `on_start` adds `vfs.visits + 1`; agent 0 on SLEEP, agent 1 on an empty cell):
  ```
  token census: {'self': 1, 'meter': 4, 'affordance': 4, 'agent': 0, …}  (agent capacity 0 => each batch row is its own world)
  after [INTERACT, WAIT]: successful_interactions={0: 'SLEEP'} visits=1.0
     visits token row  agent0=[1.0, 0.1, 0.0]  agent1=[1.0, 0.1, 0.0]
     reward            agent0=1.000   agent1=1.000  (agent1 did nothing in its own world)
  ```
- **note:** the engine-written `tick` is legitimately batch-uniform, because all worlds step in lockstep. The defect is authored globals written by per-world events. Round 1 called a global effect counting both interactions "at least defensible"; under the independent-worlds framing it is cross-world reward leakage. The fix depends on S1.

### F5. Expression text is invisible to every checkpoint-gated hash
- **severity:** P1. An exact resume accepts a checkpoint trained under a different reward or dynamics, and the policy keeps learning against the changed world.
- **where:** `VFSCompiler._variable_to_definition` (`compilers/vfs.py:83-107`) never copies `expression` into `VariableDef`, so `_canonical_variable_entry` (`schema_hashes.py:160-180`) cannot hash it. The expression lives only in `CompiledVFSProfiles`, which no hash reads. `semantic_type` is likewise absent. `PACK_HASH_KEYS` (`checkpoint_utils.py:69`) hashes experiment/stratum/environment/actions/items, but not the pack-scope `variables` declaration.
- **reproduction:** `r8_hash_coverage.py` stamps every checkpoint identity key with `attach_universe_metadata` and diffs:
  ```
  hidden_expression_text             moved: NOTHING (checkpoint resumes silently)
  hidden_semantic_type               moved: NOTHING (checkpoint resumes silently)
  hidden_initial_value               moved: ['vfs_hash']
  exposed_norm_kind_minmax_to_log    moved: ['observation_schema_hash', 'vfs_hash']
  exposed+rewarded expression x1 -> x3: hashes moved: NOTHING; reward after 2x ADVANCE: [2.0] vs [6.0]; bonus [2.0] vs [6.0]
  ```
- **fix:** add a canonical profile hash (per scope: variable id, expression source, declared type, dependency order) and fold it into `variable_schema_hash` or `vfs_hash`. Do not add an `expression` field to `VariableDef` just to hash it. Consider a `variables_hash` beside the five pack hashes.

### F6. Type-checked but not shape-proved: three families compile green and crash at runtime
- **severity:** P2 (refusal missing). These are the same class as round 1's F1/F2, on the read side.
- **where and reproduction:**
  - **Action writes reading non-agent-row state.** `_write_expression_schema` (`vtc.py:426-441`) admits every registry variable by bare name with no shape. `_coerce_expression_tensor` (`:941-947`) refuses at step. `r4_write_expression_shape.py`:
    ```
    --- pair_read (num_agents=2)     compile: OK   runtime: ValueError: … produced shape (2, 2), expected (2,)
    --- message_read (num_agents=3)  compile: OK   runtime: ValueError: … produced shape (3, 3), expected (3,)
    ```
    (Global tensors are correctly refused by type: see Refutations.)
  - **Agent-shaped value into a global rule target.** `_coerce_tensor_to_target` (`vtc.py:1785-1791`). `r6_rules_pair_global.py`:
    ```
    --- global_agent_value (num_agents=3)   compile: OK
       runtime: ValueError: Expression for VTC social residue 'social_residue:g:gsum' produced shape (3,), expected broadcastable to ()
    ```
  - **Item spawn conditions.** `_build_spawn_condition_schema` (`compilers/vfs.py:204-211`) admits bare meter names, `env.X`, `vfs.X`, `agent.vfs.X` and `temporal.{time_of_day,day_progress,is_night}`. The runtime context (`items/manager.py:604-616`) serves bare variable ids under `vfs`, bars, and `temporal.tick` only (`vectorized_env.py:823`). `r13_spawn_condition_namespaces.py`, `r13b_spawn_temporal.py`:
    ```
    --- env_prefix_agent_bool: when: 'env.has_food'   compile: OK  runtime: KeyError: "Path 'env.has_food' not found in execution context"
    --- bar_bare: when: 'energy > 0.5'                compile: OK  runtime: KeyError: "Path 'energy' not found in execution context"
    --- vfs_prefix_global: when: 'vfs.season > 0.5'   compile: OK  reset OK: apples spawned = 3
    --- is_night: when: 'temporal.is_night'            compile: OK  runtime: KeyError: "Path 'temporal.is_night' not found in execution context"
    ```
- **fix:** give write and rule expressions the `_expression_shape` proof profiles already have, with shapes keyed by scope: agent-row, pair, message-row, scalar. Refuse any result that does not match the target scope. Build the spawn schema from the runtime context's actual keys, or the reverse; one function should own both.

### F7. Pair targets take agent-shaped values down the column, diagonal included
- **severity:** P2. The value is silently attributed to an axis the author never chose.
- **where:** `vtc.py:1773-1776` reshapes an agent-shaped value to `(1, N)` for a pair target, so `trust[i, j] += value[j]`. The DTO docstring (`transition_rules_config.py:31-33`) promises "symmetric active-agent" masking but says nothing about axis. `L5_multi_agent` declares `trust` as "Directed trust from one agent to another". If rows are "from", agent i's own quantity lands in every *other* agent's row toward i, and on `trust[i, i]`.
- **reproduction:** `r6_rules_pair_global.py` (energies set to 0.9/0.5/0.1, rule `trust += bar.energy`):
  ```
  after 1 step: trust = [[0.89, 0.49, 0.09], [0.89, 0.49, 0.09], [0.89, 0.49, 0.09]]
  ```
- **fix:** refuse agent-shaped values into pair targets until the DSL can name the axis (S7). At minimum, declare the axis in the spec and exclude the diagonal.

### F8. `message` `append_event` is a silent, self-addressed, unreadable log
- **severity:** P2. A declared scope and a composition reach no consumer, and three authorable cases drop writes silently.
- **where:** `_apply_append_event` (`vtc.py:806-827`) writes the acting agent's own row at the first "free" slot and `continue`s when none is free. `_event_slot_free_mask` (`:860-864`) defines free as `value == 0`. No observation publisher accepts message scope, profile expressions cannot name it, rewards refuse it (`references.py:104`), and an action write that reads it crashes (F6).
- **reproduction:** `r5_message_scope.py` (3 slots; agent 0 ADVANCE, agent 1 WAIT):
  ```
  --- append_basic          step1: inbox = [[1.0, 0.0, 0.0], [0.0, 0.0, 0.0]] … step4: [[1.0, 1.0, 1.0], [0.0, 0.0, 0.0]]   (4th append dropped; agent 1 never receives)
  --- append_zero_payload   step2: inbox = [[0.0, 0.0, 0.0], …]       (payload 0 indistinguishable from empty)
  --- append_sentinel_init  step2: inbox = [[-1.0, -1.0, -1.0], …]    (initial_value -1 => every slot 'occupied'; every append vanishes)
  --- agent_expr_reads_inbox      REFUSED … Variable 'inbox' not found in schema
  ```
- **fix:** S6 decides whether the scope survives. If it does, "free" needs a declared sentinel, overflow needs a declared policy (refuse, ring, or drop with telemetry), and delivery needs an addressee.

### F9. The temporal-history pipeline is dead by construction
- **severity:** P2. Unreachable feature, plus a compiled artifact field that can never be non-empty.
- **where:** `_expression_shape`'s qualified function lists (`profiles.py:417-434`) omit every member of `history.TEMPORAL_FUNCTIONS` (`lag`, `delta`, `moving_average`, `ema`, `rate_of_change`, `rising_edge`, `falling_edge`). Every profile expression using one is refused. So `collect_history_requirements` (`compiler.py:299-301`) always returns `{}`, `CompiledUniverse.vfs_history_spec` (`compiled.py:208`) is always None, and `VFSEvaluator`'s `TemporalHistory` and `_push_history` (`evaluator.py:25-71`) never allocate. Even if the operators were admitted, `collect_history_requirements` reads only the global profile, so an agent-scope `lag(bar.energy, 1)` would have no buffer.
- **reproduction:** `r9_history_operators.py`:
  ```
  --- agent_lag_bar       REFUSED … Expression function 'lag' has no qualified variable output shape
  --- global_ema_tick     REFUSED … Expression function 'ema' has no qualified variable output shape
  --- global_rising_edge  REFUSED … Expression function 'rising_edge' has no qualified variable output shape
  ```
- **fix:** either delete the pipeline (`vfs/history.py`, the evaluator's history members, the artifact field, the DSL's temporal functions), or admit the operators as pointwise and collect requirements from both profiles. S9 argues for admitting them.

### F10. A `tick`-lifetime expression variable is never visible to a transition write
- **severity:** P2. A spec promise is false for one lifetime, and the variable is silently constant as far as writes can see.
- **where:** `step()` resets tick-lifetime state (`vectorized_env.py:1060`) before the action phases (`:1063`), and expressions evaluate only at `:1101`. A write condition reading a tick-lifetime expression always sees the literal. variables.md:158-159: "an action write or transition rule that reads an expression variable sees the value computed at the end of the previous tick."
- **reproduction:** `r11_lifetime_expression.py` (a). `rich` is `bar.money > 0.1` (money is 0.50 throughout, so always true):
  ```
  step1: money=0.50 rich(after eval)=[True] hits via tick-lifetime cond=[0.0] via episode-lifetime cond=[0.0]
  step3: money=0.50 rich(after eval)=[True] hits via tick-lifetime cond=[0.0] via episode-lifetime cond=[2.0]
  ```
  The episode-lifetime miss at step 1 is F1.
- **fix:** refuse a transition-write read of a tick-lifetime expression variable at compile, or adopt S4.

### F11. Writes to an expression-owned variable compile and are silently discarded
- **severity:** P2 (refusal missing).
- **where:** `_action_write_scope_refusal` (`vtc.py:2176`) and the rule target check (`vtc.py:1928-1945`) check scope and type, never whether the target carries an `expression`. Profile evaluation (`vectorized_env.py:1101`) then overwrites whatever was written. Expression variables must declare `writable_by: [engine]`, so the static write check cannot catch this either.
- **reproduction:** `r11_lifetime_expression.py` (b):
  ```
  compile: OK (no refusal for writes to an expression-owned variable)
  after ADVANCE: public_state=[1.0] derived=[2.0] (action wrote 100, rule wrote derived+50; both discarded)
  ```
- **fix:** at compile, refuse any action write, rule write or effect write whose target has an expression, citing both origins.

### F12. Token-spec refusals reach the author as bare `ValueError`s without provenance
- **severity:** P2 (wrong message shape: no error code, no stage, no `file:line`, unlike every other compile refusal).
- **where:** `_stage_7_compile_levels` calls `build_token_spec` (`compiler.py:376` → `compilers/observation.py:77`) outside the stage's error collection, so `check_indistinguishability`'s `ValueError` (`token_spec.py:1107`) propagates raw.
- **reproduction:** `r10_indistinguishable.py`:
  ```
  REFUSED ValueError: Variables 'hunger' and 'thirst' are indistinguishable: identical static payload signature …
  ```
  Compare `r4`'s `CompilationError: Stage 7 … [VTC-WRITE-TYPE] …/actions.yaml:9 - …`.
- **fix:** wrap the token-spec build in the stage collector and locate variable-named refusals at their declaration.

### F13. `persistent` VFS state does not survive checkpoint resume
- **severity:** P2. "Persistent" world state (a season, a reputation, a market price driven by rules) silently restarts mid-run.
- **where:** the demo checkpoint payload (`demo/runner.py:277-292`) holds population, curriculum and affordance layout, but no registry state. `load_checkpoint` restores the affordance layout (`:361-365`) and nothing from the registry. Evidence: `r15_persistent_not_checkpointed.log` (`grep vfs_registry|_storage|persistent` over runner, population and checkpoint_utils returns no hits).
- **spec:** variables.md:50, "`persistent` retains state across episode resets"; README/variables.md "exact checkpoint resume".
- **fix:** serialize persistent-lifetime registry storage (and `global_tick` if S1/F2 keep it) into the checkpoint, and restore it under the existing `vfs_hash` gate. Or state in variables.md that resume resets `persistent`.

### F14. Residue
- **severity:** P3.
- `configs/L5_multi_agent/variables.yaml`: `deficit_energy` and `time_since_last_sleep` are exposed, `lifetime: tick`, and written by nothing: two constant-zero tokens in every observation. `trust` (pair) and `occupied_by` (affordance) are written by nothing. `r16_L5_inert.py`:
  ```
  census {…, 'variable_element': 2}
  {'deficit_energy': [1.0, 0.0, 0.0], 'time_since_last_sleep': [1.0, 0.0, 0.0]}
  trust [[0.5, 0.5], [0.5, 0.5]] occupied_by [-1, -1, -1, -1]
  ```
  This is round 1's `configs/simple` shape, still present in L5. `deficit_energy` is now expressible as `expression: max(0.0, 0.5 - bar.energy)`.
- `_build_vfs_temporal_context` (`vectorized_env.py:513-528`) computes `is_night` with an engine constant (night = first and last 25% of the day), a game fact hardcoded in the engine. It is passed to the profile evaluator, but no profile expression can name `temporal.*` (schema refuses it), and the spawn path that advertises it is not given it (F6). Delete it.
- Docs: `CLAUDE.md:289` and `VFS.md` §5.1 list nine scopes, including `group`/`zone`, which WP2 deleted. VFS.md §5.2 says "Sparse pair storage is available" two paragraphs after §5.1 says it was deleted in WP6.

---

## Spec problems

### S1. What is `global` when `num_agents` is a batch of worlds? (fix this first)
- **What the designer writes:** a global `town_reputation`, raised by an affordance effect when any agent works.
- **What happens:** with N "independent" worlds (agent capacity 0), every world's reward and observation move when any world's agent works (F4). `pair` (N×N) and `message` assume agents share a world. The token spec assumes they don't. Items are world-shared too (one `ItemManager`, `vectorized_env.py:868-873`).
- **Smallest change:** state the ruling in variables.md. Option A (independent worlds, the token-spec reading): `global` storage gains a per-world leading axis of 1 per row, so effects write their own world's row; `pair`/`message` refuse until agents-per-world > 1 is declarable. Option B (one shared world): declare agents-per-world, give the agent token its capacity, and make the token spec's "independent worlds" sentence false on purpose. This is the only S item that changes what a policy learns.

### S2. `agent_private` is a dominated scope
- **What the designer writes:** VFS.md §5.1's own example, a per-agent `hidden_reward` with `scope: agent_private`.
- **What happens** (`r7_agent_private.py`):
  ```
  --- private_as_reward                       REFUSED … 'agent_private/scalar' has no ordinary reward reduction
  --- agent_engine_only_as_reward             compile: OK
  --- private_in_agent_expression             REFUSED … Variable 'hidden_reward' not found in schema
  --- agent_engine_only_in_agent_expression   compile: OK
  --- private_declared_agent_readable         compile: OK
     registry.get(reader=agent): PermissionError … ; compiled policy readable_by = ('engine', 'agent')
  ```
  `agent` with `readable_by: [engine]`, `exposed_to: []` gives the same privacy and keeps every consumer. `agent_private` adds a second, silent override of the declared role list (`registry.py:645`).
- **Smallest change:** delete `agent_private`. Privacy is fully expressed by `readable_by`/`exposed_to`. If kept, refuse `agent` in its `readable_by` at parse and admit it wherever `agent` is admitted.

### S3. The identity rule refuses legitimate designs and offers only a behavioural escape
- **What the designer writes:** `hunger` and `thirst`, both agent scalars, minmax 0–1, initial 0, driven by different writes or expressions.
- **What happens:** refused (`r10_indistinguishable.py`); the descriptor block (`token_spec.py:1059-1088`) carries scope, semantic type (two values), normalization, dtype, lifetime and initial, but nothing about dynamics. The suggested escape works only by changing behaviour (`perturbed_initial` compiles with `initial_value: 0.001`). The refusal fires for the witness's `dueling` flat brain, which distinguishes inputs by slot position.
- **Smallest change:** gate the refusal on a permutation-invariant brain (`token_set`/recurrent token encoders). Longer term, let declared dynamics enter the descriptor (bounded write deltas, rule rates), as meter signatures already carry depletion rates.

### S4. Named derived quantities cannot be same-tick inputs
- **What the designer writes:** `rich: bar.money > 0.1`, then ADVANCE's write with `condition: rich`.
- **What happens:** the condition reads last tick's `rich` (episode lifetime), or never sees it (tick lifetime, F10). The designer must inline `bar.money > 0.1` into every write, which defeats naming it.
- **Smallest change:** at compile, substitute expression variables into write/condition ASTs (they are pure functions of state), or evaluate the profiles once before the action phases as well as after. Either makes the lag rule in variables.md unnecessary.

### S5. One variable, five spellings
| consumer | spellings accepted |
|---|---|
| profile expression | `x`, `bar.m`, `tick` (`vfs.x` refused) |
| action write / rule | `x`, `vfs.x`, `self.vfs.x`, `target.vfs.x`, `m`, `bar.m`, `self.bar.m`, `target.bar.m`, `agent_id` |
| effect | `vfs.x`, `global.vfs.x`, `target.vfs.x`, `target.bar.m` |
| item spawn condition | `vfs.x`, `agent.vfs.x`; `env.x`, `m`, `temporal.*` compile and crash (F6) |
| DAC | `variable: x` |

**Smallest change:** one schema builder fed by the symbol table, used by every consumer's type checker and every runtime context, and one documented spelling per scope.

### S6. `message` is storage without communication
The scope requires an extent (`num_message_slots`) and admits `append_event`, but there is no addressee (the sender appends to itself), no sender identity, no age, no reader of any kind, and the "free" sentinel is hardwired to 0 (F8). This is the zone/group shape WP2 deleted. **Smallest change:** delete `message` scope and `append_event` until communication is designed, or define addressed delivery (a declared recipient expression) plus a `variable_element` publisher with a slot coordinate.

### S7. `pair` cannot express a pairwise event
No DSL binding names "the other agent" of a pair, so a pair variable can receive only a scalar, another pair variable, or an agent vector forced onto the column axis (F7). Nothing reads it except other rules. Under S1 option A, pairs span worlds. **Smallest change:** delete with `message`, or add a partner binding (`other.bar.m`, `other.vfs.x`) in pair-target rule contexts plus an exposure contract.

### S8. Transition rules: required-but-inert fields and a misleading family name
`reads` is required (`vtc.py:2008-2011`) and only hashed and serialized; `r6` compiles and runs `reads: [no_such_variable]` with an expression reading `immutable_scale` (result `gsum = 0.5`). `kind` ∈ {`social_residue`, `visibility_effect`, `institutional_rule`} changes only the derived telemetry label (`r6`: all three give `gsum = 1.0`). The family is named `social_residue`, but it is the general declarative per-tick VFS dynamic (round 1 used it for tensor decay). Separately, `ActionConfig.reads` defaults to `[]` and is equally inert (`action_config.py:78-81`). **Smallest change:** derive `reads` from the ASTs and delete the field; delete `kind`; rename the family `dynamics` (or `transition_rules`).

### S9. Accumulators and "time since" need three families
To count ticks since the agent last slept, a designer needs a persistent or episode variable (variables declaration), a `+1` rule (a transition-rules file with id, kind, phase, reads, condition, clamp, effect), and a reset-to-zero affordance effect. Self-reference is refused as a cycle, and history operators are refused (F9). L5's `time_since_last_sleep` is the shipped evidence of intent, still unwired. **Smallest change:** once F9 admits the operators, allow `lag`-only self-edges in the dependency graph, so `where(<event>, 0.0, lag(t_since, 1) + 1.0)` is one declaration.

### S10. Doc contradictions
- Scope count: `CLAUDE.md:289` and VFS.md §5.1 say nine; variables.md says seven.
- VFS.md §5.2 says sparse pairs are available; §5.1 says they were deleted.
- variables.md:158-159 states the lag rule, which is false for `tick` lifetime (F10).
- variables.md:50 does not say whether `persistent` survives resume (F13).

---

## Refutations (tested, held)

- **Global/vector/tensor reads into scalar writes are refused by type at compile:** `r4` `global_tensor_read` → `[VTC-WRITE-TYPE] … assigns a tensor1d expression 'gvec' to 'public_state'`, and the condition variant is refused too. The f54b887148 shape is closed on the read side for tensors (it survives for pair/message: F6).
- **The `vfs.x` spawn spelling works end to end:** `r13` `vfs.season > 0.5` → 3 apples; `< 0.5` → 0.
- **`agent_private` reads are refused even when `readable_by` declares `agent`** (`r7`). Enforcement holds; the problem is the contradiction (S2).
- **`kind` has no hidden behavioural branch:** `r6`, all three kinds give identical writes.
- **Done agents:** transition-rule writes are masked by `active_on_entry`. In `r14a`, `age` stops at 1.0 for the dead agent while the live one reaches 3.0, and the dead agent's reward is 0.0. Expressions keep evaluating, but over frozen inputs.
- **Empty roster:** `declarations: []` compiles and steps. The registry holds only `tick`, `variable_element` capacity is 0, `total_dims` is 37 (`r14b`).
- **WP7 holds:** changing a hidden `initial_value` moves `vfs_hash`; changing an exposed normalization kind moves `observation_schema_hash` and `vfs_hash` (`r8`).
- **Cyclical normalization is exact:** decoding the `day_phase` sin/cos lanes in `r2` recovers integer hours with period 24.
- **WP5 holds:** the witness's agent `scaled_public: public_state * immutable_scale` (agent reads global) compiles and tracks in every probe.
- **Item-state slots publish presence 0 for a dead slot** (round 1); only the visibility filter is missing (F3).

## Proposed work packages (continuing from vfs.md WP8)

| WP | content | closes | size |
|---|---|---|---|
| WP9 | Clock and reset truth: evaluate profiles at the end of `reset()`; write `tick` post-increment (or evaluate after the increment) so `tick`, `day_phase` and `time_of_day` agree in every observation. Acceptance: `r1`, `r2` show equal hours at reset and every step | F1, F2 | S |
| WP10 | Profile identity into `vfs_hash` (expression source, type, order, `semantic_type`); add `variables_hash` to the pack hashes. Acceptance: `r8` moves a hash on every line | F5 | S |
| WP11 | One per-slot visibility mask shared by the item and item-state publishers. Acceptance: `r3` shows state presence 0 whenever item presence is 0 | F3 | S |
| WP12 | Shape-proved writes: scope-keyed shapes in write and rule type checking; refuse writes to expression-owned targets; one spawn schema derived from the runtime context; wrap token-spec errors in stage diagnostics; refuse agent-shaped values into pair targets pending S7. Acceptance: `r4`, `r6`, `r11b`, `r13`, `r13b`, `r10` refuse at compile with `file:line` | F6, F7, F11, F12 | M |
| WP13 | Rule S1, then implement it: per-world `global` axis, or declared agents-per-world. Acceptance: `r12` shows agent 1 unaffected (option A) or an agent token present (option B) | F4, S1 | M–L |
| WP14 | History: admit temporal operators as pointwise, collect from both profiles, allow `lag`-only self-edges; or delete the pipeline. Acceptance: `r9` compiles and tracks, or `vfs_history_spec` is gone | F9, S9 | M |
| WP15 | Scope surface: delete `agent_private`, `message` and `pair` (or give each a reader and an addressing rule); clean the L5 pack. Acceptance: `r5`, `r7`, `r16` | F8, F14 (L5), S2, S6, S7 | M |
| WP16 | Persist `persistent`-lifetime registry state in checkpoints, under the `vfs_hash` gate | F13 | S |
| WP17 | Spec text: identity rule gated on brain type (S3); one-spelling resolver (S5); transition-rule `reads`/`kind`/name (S8); inline expression variables into writes (S4); doc corrections (S10); delete `temporal.is_night` | S3, S4, S5, S8, S10, F14 | M |

**Ordering:** WP9 → WP10 → WP11 are small, independent and policy-relevant, so do them first. Take WP13's *decision* before WP15, because deleting or keeping `pair`/`message` depends on it. WP12 precedes WP14, because admitting temporal operators adds shapes the proof must cover.

## Coverage

- **Read:** `vfs/profiles.py`, `vfs/evaluator.py`, `vfs/history.py`, `vfs/schema_hashes.py`, `config/variables_config.py`, `config/transition_rules_config.py`, `universe/compilers/vfs.py`; `vfs/registry.py` (constructor, shapes, writes, resets); `vfs/vtc.py` (write schema, action-write coercion and composition, append_event, social-residue compile and coercion); `token_publishers.py` (normalizer, registry and item-arena variable publishers, item publisher); `token_spec.py` (`_variable_element_artifacts`, descriptor, indistinguishability); `vectorized_env.py` (`reset`, `step`, profile evaluation, temporal context); `items/manager.py` spawn evaluation; `training/checkpoint_utils.py` stamp; `demo/runner.py` save/load; `references.py` reward-variable check.
- **Not reached:** affordance `claim_if_free`/`capacity_claim` occupancy at runtime (deliberately skipped: round 1 and WP2 cover the scope rule); effects-side item-profile writes; CUDA paths; seeded determinism of random initializers (WP7 landed it).
- **Side effect:** `r16` compiled `configs/L5_multi_agent` in place, which refreshed its gitignored `.compiled/universe-L5_multi_agent.msgpack` (the cache was stale at schema 1.26). No tracked file changed.
