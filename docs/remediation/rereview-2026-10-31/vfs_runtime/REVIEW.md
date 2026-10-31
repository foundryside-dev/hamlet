# Re-review — lens `vfs_runtime` (VFS runtime correctness and isolation) — 559dd0f9

Worktree: `rereview/vfs_runtime/wt` (detached at 559dd0f9, removed at the end). Interpreter: `/home/john/hamlet/.venv/bin/python`
with `PYTHONPATH=wt/src` (`townlet.__file__` confirmed under wt/src), `CUDA_VISIBLE_DEVICES=` (CPU). /home/john/hamlet untouched, no `git stash`.
Probes: `probes/` (harness.py = B4 harness repointed; common.py = pack builders; p_writes / p_isolation / p_dying / p_reset_ckpt /
p_access / p_misc / p_claim). Logs: `out/*.log`, differential snapshots `out/iso_*.pt`. Packs built under `probes/packs/` from
`configs/static_epistemic_access` (SEA) and `configs/test/items_smoke`.

## VERDICT: NOT GREEN

Blocking (all three reachable from an authored pack; each fits both bar definitions — P1 "a crash reachable from an authored pack" and
P2 "a compile that accepts what the runtime can't serve" — filed under the more specific P2, not under-called):

- **N1 (P2, crash at step)** — bool (and reference) item-profile state is served to pipelines as float32, so any boolean operator over
  `item.<bool>` compiles and crashes at step.
- **N2 (P2, crash at step)** — an action write into a vector/tensor-typed agent variable with an agent-shaped expression compiles and crashes
  at step; the same rule broadcasts.
- **N3 (P2, crash at step, mis-attributed)** — `clamp` on a reference target compiles; at step the clamp rewrites the row index and the
  registry reports it as "Engine defect".
- N4 was downgraded to **P3** after checking the indirection routes (see below): null test and release are authorable through a global
  sentinel / a global bool; only the identity test ("is this claim mine") is unauthorable, and under S1 that question is moot.

Everything else held: world isolation (A/B differential at N=2/4/5, every registry variable, meters, obs, effects), bitwise determinism
(A/A), N=1 ≡ N>1 on world 0 up to RNG-stream-size effects, dead-world freezing, reset ordering, persistent save/restore, access policy on
every authored write path, the closed phase graph.

## 1. New findings (most severe first)

### N1 — P2 — bool/ref item state crosses the float32 item arena untyped; `not item.flag` / `item.flag and …` crash at step
- Claim: `VariableDeclaration` admits `bool`, `agent_ref`, `item_ref` item-profile state (`config/variables_config.py:92`), the type checker
  types `item.flag` as `bool`, but `effects/context.py:215-224` (`read_item_state`) hands the evaluator `torch.as_tensor(registry.read_item(...))`
  = a float32 0-d tensor (the arena is float32, `vfs/registry.py:718-722`, `:829`, `:856`). `not` → `TypeError: ~ (operator.invert) is only
  implemented on integer and Boolean-type tensors`; `and` → `NotImplementedError: "bitwise_and_cpu" not implemented for 'Float'`. A bare
  `if: item.flag` happens to work (float truthiness), so the failure is operator-dependent.
- Repro: `probes/p_access.py a2` (`out/p_access.log`): items_smoke + food-profile `flag: bool`; apple `on_use: [{if: "not item.flag", then: [modify item.flag value: not item.flag], else: []}]`
  compiles; GET then USE_SLOT_0 → TypeError. Variant `if: "item.flag and item.owner == nullref"` → NotImplementedError.
- Where: `src/townlet/effects/context.py:215-224`; fix: cast each item-state read to `storage_dtype(registry.get_item_variable_type(profile, name))`
  (bool/long) when building `item_state`, or refuse non-scalar item types at the declaration until the arena is typed.
- Related (P3): an `agent_ref` item variable stores `-1.0`; `item.owner == nullref` (ref vs ref) compiles and compares float with long — works by
  coincidence of torch promotion, not by contract.

### N2 — P2 — action write into a `vecNf`/`tensor1d` agent target with an agent-shaped expression compiles, crashes at step; rules broadcast
- Claim: `admitted_write_result_types("vecNf")` is `{int, float}` (`vfs/storage_dtype.py:901-908`) and the action-write shape proof admits
  `agent` for any agent-scoped target (`vfs/vtc.py:2338`, `_AGENT_ROW_SHAPES`; `namespace.shapes(..., payload_for_vectors=False)`), so
  `vec <- av` / `vec <- bar.energy` compiles. `VTCActionWriteProgram._coerce_expression_tensor` (`vfs/vtc.py:1037-1055`) accepts a 0-d value
  (broadcast) or an exact-shape value only → `ValueError: Expression for VTC action write 'w_vec' produced shape (3,), expected (3, 3)`.
  `VTCTransitionRuleProgram._coerce_tensor_to_target` (`vfs/vtc.py:1859-1892`) pads and broadcasts the same value, so a rule with the same
  expression runs (`[[2,2,2],[2,2,2],[2,2,2]]`). Literals work on both. (`vec[0]` and `vec` as a write *value* are refused at compile.)
- Repro: `probes/p_writes.py w1` (`out/p_writes.log` lines 5-17).
- Fix shape: either refuse at compile (vector/tensor target + non-scalar-shaped expression in an action write) or broadcast as the rule program does.

### N3 — P2 — `clamp` on an `agent_ref`/`item_ref` target compiles; at step the registry refuses the clamped row as an "Engine defect"
- Claim: neither `WriteSpec` (`vfs/schema.py:313-315,331-336`), `TransitionRuleWriteConfig` nor `_write_type_refusal` (`vfs/vtc.py:581-637`,
  which does gate *composition* for references) refuses `clamp` on a reference target. `_clamp_in_dtype` (`vfs/vtc.py:687-697`) clamps the
  row index: `aref <- -1 overwrite clamp [0, 10]` stores 0 in every world; `aref <- agent_id clamp [0, 0.5]` stores 0 in every world; then
  `VariableRegistry._validate_world_refs` (`vfs/registry.py:475-507`) raises `RuntimeError: Engine defect: agent_ref 'aref' in world 1 names agent 0 …`.
  An authoring error is reported as an engine bug, without `file:line`. `clamp` on a bool target also compiles: `flag <- true clamp [0, 0]`
  silently stores `False` (`probes/p_claim2.py c3`) — a clamp "bounds a value" has no meaning on a bool and rewrites it.
- Repro: `probes/p_writes.py w2` (`out/p_writes.log` lines 22-27), `probes/p_claim2.py c3`.
- Fix: refuse `clamp` on reference and bool targets next to the composition gate in `_write_type_refusal`.

### N4 — P3 (ergonomics; latent spec gap for agents-per-world > 1) — references are write-only with respect to identity
- What refuses: `aref == -1`, `aref < 0`, `aref == agent_id`, `where(aref == -1, …)` in rules, action writes, effects, item hooks and profile
  expressions (`Comparison operator == requires compatible operands, got agent_ref and int`, `world/expression/type_checker.py:277`); in
  pipelines a reference cannot be written from `-1` or `agent_id` (`agent_id` is not in INTERACTION_PIPELINE/EFFECT_PIPELINE,
  `vfs/namespace.py:212-230`; an int literal → "expected agent_ref, got int"); an action write cannot release an affordance row
  (`vfs/vtc.py:2373-2414`); an agent-shaped condition cannot gate an affordance-row rule (`_RULE_ADMITTED_SHAPES`, `vfs/vtc.py:2364-2368`).
- What is authorable (`probes/p_claim2.py c2`, `out/p_claim2.log`): **null test** via a global sentinel (`nullref: global agent_ref, null`;
  rule `condition: occ == nullref` compiles and counts free rows per world); **release** via a global bool written by the interaction
  (`rel: global bool, tick lifetime`; SLEEP `on_start: modify rel value true`; rule `occ <- -1 overwrite, condition: rel`): only world 1's
  row released after world 1's INTERACT. So "claim / is it free / release when done" is three hops and two helper variables, not Python.
- Residual: the **identity** test is unauthorable — `occ == agent_id` refuses on type, `occ == me` (an agent-scoped ref set from `agent_id`)
  refuses on shape (`affordance` vs `agent`), and an agent's identity cannot be lifted into global scope (agent→global refused). Under S1 a
  world has one agent, so "is this claim mine" ≡ "is it claimed"; the gap becomes real only when agents-per-world becomes declarable.
  Suggested: admit `-1` as a null literal in ref comparisons (the write side already does), and document the sentinel/bool pattern.
- Repro: `probes/p_access.py a3`, `probes/p_claim.py`, `probes/p_claim2.py`.

### N5 — P3 — a rule scheduled at `evaluate_terminal_conditions` is seen by expressions one tick late
- `step()` evaluates profiles (3.7) before `evaluate_terminal_conditions` (4), so `g += 1` there gives `(g, g2=g*2)` = `(1,0),(2,2),(3,4)`;
  at every other phase expressions see this tick's write (`(1,2),(2,4),(3,6)`). variables.md:245-247 ("an expression always reads this tick's
  writes … transition rules") is wrong for that one phase; the phase list at :204-218 is right. Either document or refuse rules after the
  evaluation point. `probes/p_writes.py w5`.

### N6 — P3 — exposure composes through expressions: an exposed expression over engine-only inputs reaches the observation
- `ex2: hidden_score * immutable_scale` (both `readable_by: [engine]`) with `exposed_to: [agent]` compiles and publishes `0.1` (= 1.0/10) in
  the token row (`probes/p_writes.py w4`). The variables themselves never reach the observation (VFS.md:595, CLAUDE.md hold literally), but
  `readable_by` is not propagated through expressions. By design or not, it is undocumented; either state it in variables.md or refuse
  exposing an expression whose transitive inputs are not agent-readable.

### N7 — P3 — dead-world expressions shift once after death, then freeze; tick-derived ones keep moving
- After an agent dies, its world's history ring stops but expressions re-evaluate against the post-commit cursor, so `lag(av,2)+delta(bar.energy)`
  went `-0.48 → 1.0` on the step after death and then held; `gexp: g*2 + tick` keeps advancing with the engine `tick`; the dead world's
  observation changes every step (reward 0). variables.md:328 ("keep evaluating, over that frozen history") covers it; the one-step shift is the
  surprising part. `probes/p_dying.py d1`.

### N8 — P3 — a persistent `item_ref`/`agent_ref` survives `reset()` and points at the re-populated row
- `held: item_ref, lifetime: persistent` keeps `[3, 16]` across `reset()`; row 3 is re-spawned by the next episode (same profile here, any
  profile in general). The DTO refuses persistent *item-scope* variables but not a persistent reference *into* the episode-lifetime arena.
  `probes/p_misc.py m3`. Refuse `item_ref` with `lifetime: persistent`, or document the dangling semantics.

### N9 — P3 — bool compositions are silently boolean algebra; `composition: clamp` with `clamp: null` is overwrite
- `flag <- true` with `additive_delta` = OR, `multiplicative_modifier`/`min` = AND, `max` = OR (`probes/p_writes.py w2`). Defined by torch, not
  by the authoring contract. `composition: clamp, clamp: null` compiles and behaves as overwrite (`w6`). Refuse or document both.

### N10 — P3 — doc drift found on the way
- `docs/architecture/VFS.md:272, :1097` still describe `VFSEvaluator` "mark-and-sweep or eager mode"; `eager` was deleted (no `evaluation_mode`
  field on `VariablesConfig`).
- `docs/config-schemas/variables.md:382` names `get_global`, `get_agent` accessors that `vfs/registry.py` does not have.
- Phase-entry snapshot semantics (a priority-0 write is not visible to a priority-1 read in the same phase; two additive rules on one target
  compose; a rule reading the target sees the entry value — `probes/p_misc.py m2`) are still undocumented (B3 follow-up #44).
- Division by zero in an exposed expression (`public_state / zero`) compiles and raises at the first publish (`CompiledValueNormalizer received
  non-finite live values`, `token_publishers.py:234-238`): loud and data-dependent; worth one sentence in variables.md.

## 2. What held (evidence)

- **Isolation**: `probes/p_isolation.py` pack (global/agent/affordance rules incl. `priority_write` and `clamp`, agent + global effects with
  `sample` and `intensity`, `lag/delta/ema/moving_average/rising_edge`, lag-self accumulator, `random_uniform` tick-lifetime and
  `random_normal` episode-lifetime tensors, `agent_ref <- agent_id`, bool toggle, tick-lifetime action write, persistent accumulator, exposed
  expressions). World-0 perturbed (every action id, INTERACT→e1 spawn, global effect spawns) vs unperturbed, 40 steps + reset + 4 steps, at
  N=2, 4 (= affordance count), 5: **NO DIVERGENCE in worlds 1..N-1** on obs, reward, done, meters, positions, every registry variable, effects;
  global RNG stream identical. `out/iso_*.pt`, `compare2.py`.
- **Determinism**: same seed, two runs, N=4: bitwise identical on every world and every key (`compare2.py … all`).
- **N=1 vs N=4**: world 0 identical on every registry variable except the random initializers (RNG stream length) and positions (random placement);
  meters identical every step.
- **Dying agent** (`p_dying.py`): on the dying step every write still applies (entry mask); afterwards the world's globals, affordance rows,
  agent variables, meters and effects writes are frozen (a live global effect in the dead world keeps counting ticks and writes nothing —
  follow-up #28 closed); live worlds unaffected.
- **Reset ordering** (`p_reset_ckpt.py r1/r3`): instant 0 evaluates persistent expressions from carried values (`pacc: lag(pacc,1)+1` continues
  6 → 7), `tick` is 0 in every row, tick-lifetime writes are visible in that step's observation and reset before the next; episode random
  initializers redraw per reset and hold within an episode; tick-lifetime ones redraw per step; a reset after partial deaths clears dones and
  re-seeds history; two resets in a row are fine.
- **Persistent save/restore** (`r2`): snapshot = exactly the persistent ids (incl. SEA's `immutable_scale`), dtype-preserving (bool, int64 refs,
  float32 vectors); restore then `reset()` evaluates `pexp` from the restored value; a cross-world ref or an N-mismatched snapshot is refused
  before any write.
- **Access policy** (`p_access.py a1`): engine-only read by `agent`, write to `writable_by: []` by engine, any write by `agent` → PermissionError;
  effect `modify`, effect `sample store_in`, `for_each all_agents` body, transition rule, action write, interaction `modify`, item hook
  (`medical:locked`) on a `writable_by: []` target all refuse at compile `[UAC-STATIC-WRITE]` with `file:line`; `exposed_to` without read
  access refuses at the declaration (registry and item variables). Item-state publisher binds via `authorize_item_read(reader="agent")` +
  `exposed_to` and publishes each world's own rows only.
- **Phase graph** (`p_writes.py w5`): a rule at any of the 14 phases applies; action writes after `apply_completion_bonuses` and unknown phases
  refuse at compile with the actions/rules `file:line`. Variable id = meter name refuses `[SYMBOL_METER_COLLISION]` at both declaration lines.
- **Rule ordering** (`p_misc.py m2`): rule priority = declaration order (later rule wins on overwrite and priority_write), as transition_rules.md says.
- **Hashes** (`p_misc.py m1`): hidden tensor shape, `initial_value_mode` and literal `initial_value` all move `level.vfs_hash` (V12 closed).
- **for_each all_agents** in agent and global effects writes the effect's world only (`p_misc.py m4`).
- **Type gate on pipelines**: effect `modify`/`sample` into bool/ref/scalar is strictly typed (int literal into scalar refused; float into
  bool refused; uniform into bool/agent_ref refused); VTC writes admit int→float32 widening only; conditions must be bool.
- Targeted tests at the worktree: `pytest tests/test_townlet/unit/vfs tests/test_townlet/unit/environment -k "vtc or vfs or registry or
  history or transition or publisher or token"` → 735 passed.

## 3. Known-item classification (PHASEA_FOLLOWUPS.md + B3/B4 records), my lens only

| item | class | why |
|---|---|---|
| #3 `initial_value: 2` vs `2.0` moves hash | P3 | compiler lens; not re-tested |
| #7 F9/WP14 hash ignores evaluation order | closed | B3 H5 (fwd vs reversed authoring → identical traces); M1 shows the hash covers shape/initializer |
| #8 `day_phase` episode lifetime, no persistent example | P3 | doc/example only |
| #20 visibility mask computed twice | P3 | perf |
| #22 one ItemManager shared by all worlds | closed (items pass) | `ItemManager.worlds[w]` per world; `item_row_world`; item rows per world in A/B differential (B4) — not re-probed here |
| #24 torch global RNG not checkpointed | out of scope | training loop; noted that `_reset_lifetimes` random draws and placement ride that stream |
| #25 S1 remainder (global/affordance effects shared store, for_each crosses worlds) | closed | effects keyed by world (`effects/manager.py:305-312`); D2 global effect in world 2 only; M4 for_each world-local |
| #28 effect tick without write mask (dead agent advances global) | closed | `step()` passes `live=active_on_entry`; D2: dead world's global effect writes nothing |
| #32 phase rename | closed | `apply_transition_rules` in graph; `social_residue`/`residue_targets` 0 hits |
| #33 `_target_spellings` duplicate | P3 | compiler lens |
| #34 effects/spawn predicates read tick-lifetime expression vars from storage | closed | B4 I3/H3 refusals; `inline_expression_reads` (`namespace.py:580-600`) |
| #36 spawn predicate history op | closed | B4 |
| #37 two history-operator lists | closed | `TEMPORAL_FUNCTIONS` derived (`functions.py`), `vfs/history.py` imports it |
| #38 profile refusals unlocated | closed | B4 F1; my w4a/w6a refusals cite the declaration line |
| B3 #43 `_run_state_residue` names | closed | 0 hits |
| B3 #44 phase-entry snapshot undocumented | P3 OPEN | N10; semantics verified (M2) |
| B3 #45 budget-0 effect scope silent refusal | P3 | effects |
| B4r #49 "effect closes an affordance" capability gap | spec gap, effects/UaC scope | not VFS; listed for the owner |
| B4 #54 affordance_identity self/all lanes zero | P3 | compiler lens |
| B4 #55 DAC role fields not through resolver | P3 | DAC reads with `reader="engine"` via `registry.get` (`dac_engine.py:120,205`) — checked, no bypass |
| B4 #56 `_LEGACY_*` table | P3 | refusal text only (`namespace.py:453-467`) |
| B4 #57 agent-shaped into global/affordance refuses | P3 (feeds N4) | conservative under S1; forces the global-sentinel / global-bool indirection |
| docs sweep #60 spatial functions refused in profiles | P2 spec gap (known) | "distance to nearest food" as an observed feature is unauthorable; VFS scope |
| docs sweep #61 `time_in_window` 24-tick constant | P2 (known) | `functions.py:628` hardcodes 24; the declared clock period is ignored — hidden behavioural constant (no-defaults) |
| B4r P1 switch body crash | closed at 559dd0f9 | commit subject "typed switch cases"; compiler lens verifies |
| B4r P2 undeclared item profile unlocated | closed at 559dd0f9 | commit subject "located item-profile refusal" |
| B4r P3 `self`/`target` not reserved | closed | `RESERVED_NAMES` includes `ENTITY_NAMES` (`references.py:66`) |
| B4 P2 `additive_delta` into a ref | closed | `_write_type_refusal` composition gate (`vtc.py:594-599`); **but `clamp` escaped the same gate → N3** |
| B4 P3 claim_if_free needs source_affordance | closed/by design | custom actions may declare `source_affordance` (`actions_config.py:48`); works (`p_claim.py`) |

## 4. Original-review closure (findings_vfs.md / gaps_vfs.md)

| id | status | evidence |
|---|---|---|
| hamlet-3381043d2e action writes | CLOSED | SEA ADVANCE writes run in every probe |
| hamlet-4597fd5d04 / 5f99e89865 | CLOSED | lifetimes honoured (R1); `configs/simple` residual gone (grep 0) |
| hamlet-0268336cd1 reset/global lifetime | CLOSED | R1: tick/episode reset, persistent kept |
| hamlet-83a043a9b9 agent_private | SUPERSEDED | scope deleted (S1); privacy = `readable_by`/`exposed_to`, enforced (A1) |
| hamlet-0071c78ee9 observable | CLOSED | no such key; marks derived |
| hamlet-8c354c90bb initial_value_mode | CLOSED | DTO field; eye/random validated (`variables_config.py:121-147`) |
| hamlet-b5cd718368 vector vocab | CLOSED | one `VariableType`; vecNf/tensor allocate (W1, R2) |
| hamlet-c6c6c241c5 / F8 / V7 agent expr reads global | CLOSED | `AGENT_EXPRESSION` admits GLOBAL (`namespace.py:185-193`); `ag: gexp + av + public_state` runs |
| hamlet-de52c40c03 item expressions | CLOSED | refused loudly (`profiles.py:481-488`) |
| hamlet-f2a37a8c8a | CLOSED | item state via `read_item`/`write_item` with roles |
| hamlet-f54b887148 / F2 / V2 shape-coincidence masking | CLOSED | `_action_write_scope_refusal` (`vtc.py:2373-2414`) + shape proof; W1 N=2 vs 3 identical logic; **payload twin is N2** |
| hamlet-8b5af63108 tensorNd | CLOSED | DTO type; doc gap not re-checked |
| hamlet-2ca2cb373f / F7 / V11 dtype coercion | CLOSED on registry/VTC/effects (`to_storage_dtype`, strict effect types); **item arena residual is N1** |
| hamlet-b9a3bcbde2 / V8 bare `vfs.X` batch write | CLOSED | spelling refused; pipeline writes land in their world (M4, B4 C1) |
| hamlet-cb0ccdaa98 cascades→VFS | CLOSED | `transition_rules` family |
| hamlet-cebe51077a / F1 / V1 phases never executed | CLOSED | graph = the 14 executed phases (`transition_graph.py:14-30`); W5 rule at every phase applies; action writes past `apply_completion_bonuses` refuse |
| hamlet-02bd5a3eaa / V9 zone | SUPERSEDED | scope deleted (S1) |
| F3 / V3 eager | CLOSED by deletion | no `evaluation_mode`; VFS.md:272/1097 still mention it (N10) |
| F4 / V4 extents.num_affordances | CLOSED by deletion | no `extents` on `VariablesConfig` |
| F5 / V5 meter-name variable | CLOSED | `[SYMBOL_METER_COLLISION]` at both lines (W6) |
| F6 / V6 reward program compiled never run | CLOSED | no reward program in `VTCTransitionSchedule`; `compile_vtc_bounds_clamps` 0 refs |
| F9 / V12 hash ignores shape/init | CLOSED | M1 |
| F10 / V10 unreachable modes, dead fns, semantic_type | CLOSED except `semantic_type` | `pair_storage_mode`/`dynamic_variable_mode` gone; `evaluate_all`, `run_phase`, `passive_rate_for`, `duration_for`, `compile_vtc_bounds_clamps`, `_apply_vtc_action_writes` 0 hits; `semantic_type` still required and consumed only at exposure/hash (`token_spec.py`) — P3 OPEN |
| F11 / V13 random init frozen | CLOSED | R1: redraw per reset / per step |
| F12 / V15 residues | CLOSED | docstring/whitelist/configs/simple hits 0; VFS.md §6 corrected (:588-597); new drift in N10 |
| F13 / V14 expressions one tick late | CLOSED | expressions evaluated after `clamp_and_validate` (W5); residual one-phase case is N5 |

## 5. Not covered
- CUDA device paths (CPU only). Items gameplay beyond the hook/arena reads above; item respawn predicates (B4 I3b covered them). The
  full test suite (another reviewer). Checkpoint save/restore through `DemoRunner` end to end (registry-level roundtrip only; B3 r_resume
  covered the runner). `capacity_claim`. Interaction `delay` paths. The `effect_ref`/`affordance_ref` types (no write path exercised).
  Token POMDP masking of `variable_element` (non-spatial, unaffected by construction; not probed).
