# R3 verifier record — commit `636192e0` (fix/vfs-compiler-remediation-2)

Isolated worktree `verify_R3/wt` at `636192e0` (and `verify_R3/wt_base` at `39825727` for the deltas);
`townlet.__file__` confirmed inside the worktree. Probes in `verify_R3/probes/` (harness = the authoring
lens's `harness.py`, repointed via `WT=`). Nothing in `/home/john/hamlet` was edited. No fixes made.

## Defects (severity per `rereview-2026-10-31/BRIEF.md`)

### V1 — P1: a draw on an affordance-scope target, combined with an affordance operand, leaks across worlds (or crashes)
- Repro (`p_aff.py`, default_curriculum, 14 affordances): rule `aff_v := uniform() * aff_w` (both
  affordance scope). Compiles. N=3: `RuntimeError: size of tensor a (3) must match ... (14)` at step.
  **N=14: runs silently and every world's row is `[d_0 … d_13]`, all worlds' draws**
  (`world0(N=14) == world0(N=1): False`, `w0 == w1`). Same for `uniform(0.0, aff_w)`,
  `where(aff_w > 0.5, uniform(), 0.0)`, `normal_dist(0.0, aff_w)`, and the rule **condition**
  `uniform() < aff_w` (`p_aff_cond.py`: N=14 all world rows identical; N=3 crash).
- Cause: `world/expression/functions.py:622-644` `_draw` returns `[W]` for a 0-d `like`;
  `vfs/profiles.py:389-396` `expression_shape` proves a draw as `scalar` (`draw_axis="scalar"`),
  which joins with `affordance`; `vfs/vtc.py:1804` `_world_column_view` only unsqueezes named
  global `world_columns`, so the bare `[W]` draw broadcasts against `[W, A]` on the trailing axis.
- Not affected: `uniform()` alone (spread per world, correct), `uniform(aff_w)`, `normal_dist(aff_w, 0.1)`
  (draw shaped by the affordance argument, correct and world-local).
- R3-introduced (draws were refused in rules before).

### V2 — P2: `vfs/vtc.py:654-655, 683-685, 698-699` evaluates a draw at compile time from torch's global RNG
- `_constant_value` treats "no `read_paths`" as "constant"; with draws admitted that is false.
  `ExecutionContext(bars={}, vfs={}, temporal={})` has no streams, so `_draw` falls through to the
  global generator (the claim "a VFS draw never falls through" fails here).
- Direct: `_constant_value(where(uniform() < 0.5, -1, 0))` under `manual_seed(0..9)` →
  `[-1, 0, 0, -1, 0, 0, 0, 0, 0, 0]`; compiling consumes the global RNG (control pack does not).
- **Compile admission is nondeterministic** (`p_refconst4.py`, items_smoke, agent_ref target,
  `max(-1, where(uniform() < 0.5, -1, 0))`): global seeds 0..15 →
  `REF REF REF OK REF REF REF REF REF REF OK OK OK OK REF OK`. An admitted pack then writes 0 into
  every world's `agent_ref`; the registry backstop catches it at step (`vfs/registry.py:504`,
  "Engine defect: agent_ref 'aref' in world 1 names agent 0"), so the outcome is a crash, not silent
  corruption. A compile after `seed_all` also shifts the run's global stream.
  (On default_curriculum the check runs ~8 times per compile, so admission is rare but possible.)

### V3 — P2: random-draw order is keyed by declaration order, which no identity hash covers
- One stream per world is shared by every draw site, consumed in evaluation order; profile order is
  `nx.topological_sort` generation-then-insertion order (`vfs/profiles.py:154`), i.e. declaration order.
- `p_order_hash.py`: moving declaration `a_two` from `variables.yaml` to `aaa/early.yaml` (a pure
  transport change) moves **no hash** (all 23 `*_hash` fields on universe and level equal) and
  **changes `a_two`'s trajectory**. Reversing declaration order: same (no hash moves, `a_two` changes).
- `p_unrelated.py`: an unrelated non-random variable, global, or static: no change (holds). An
  unrelated **random** agent var, global var, or random rule re-rolls **every** other draw
  (g_rand, a_two, g_target, a_target all change), including the global profile (shared stream).
- So two packs identical by every checkpoint identity hash produce different trajectories, and a
  designer A/B adding one random mechanic re-rolls all the others. Suggested fix shape: derive the
  generator per (world, draw-site identity), not per world.

### V4 — P2: an expression reading a `tensor1d` initialised by `initial_value_mode` crashes at reset
- `p_shapes.py` / `t_t1.py`: `t1: tensor1d, shape [3], initial_value_mode: zeros`; agent expression
  `gather(t1, 0)` compiles; reset raises `RuntimeError: Could not infer dtype of NoneType` at
  `vfs/evaluator.py:153` (`torch.tensor(var.initial_value)` with `None` for the static dependency).
  With a literal `initial_value` it works. `expressions.md:447` documents `gather` over tensor1d.
- Newly reachable: tensor/vector reads were labelled `payload` and refused in variable expressions before R3.

### V5 — P2: vector equality in a bool expression variable compiles and is refused at step
- `t_t1.py`: agent bool `x: vecv == vecv` (or `!=`) compiles; reset raises
  `Agent-profile variable 'x' evaluated to shape (2, 2), expected (2,)` (`vectorized_env.py:1377`).
  The type checker says `bool`, the shape proof (no more `payload` label, `vfs/namespace.py` `shapes`)
  says `agent`, the evaluator returns `[W, 2]`. Other vector-through-pointwise cases
  (`vecv + 1.0`, `abs`, `sum`, `mean`, `clamp`, `count_where`, `argmax`, `perlin_noise`, `uniform(vecv)`,
  `where(flag, vecv, vecv)`, `vecv > 0.5`) are refused by the type checker (holds). R3-introduced.

### V6 — P2: an unknown affordance name in a position function is never refused
- `p_undeployed.py`: `distance_to_affordance("NOPE")` compiles; exposed → reset crashes
  (`CompiledValueNormalizer received non-finite live values`); unexposed → silent `inf`.
  An affordance declared but not in `enabled_affordances` behaves the same (documented as infinity,
  `expressions.md:501`), and `in_range` silently reads false. The typo case is statically knowable;
  the undeployed-and-exposed case is a guaranteed reset crash, also statically knowable
  (`gridnd_4d_pack` ships `enabled_affordances: []`). Newly reachable in observations via A3.

### V7 — P3s
- **Seeds are read lazily, process-global.** `vfs/random_streams.py:51` reads `torch.initial_seed()`
  at each episode's first draw. `p_seed.py`: env X (seed 1) constructed, env Y `seed_all(2)`, then X's
  episode 2 equals solo-seed-**2** episode 2, not seed 1. Same pattern in `effects/manager.py:319`
  and `items/manager.py:298-303`. Single-env runners are unaffected. Two same-seed envs at the same
  episode produce identical streams (by construction).
- **Docstring claim false.** `random_streams.py:12-13` (and `variables.md` "Random draws") say a
  resumed run re-derives streams from "the episode counter it restarts at"; the counter is
  per-env and starts at 0 (nothing restores it), so a resume replays episode 1's streams. Not
  checkpointed is the known follow-up; the wording is wrong.
- **`random_*` initializers and spawn positions ride the global stream** (`vfs/registry.py:639,643`;
  `vectorized_env.py:1681` randperm; `substrate.initialize_positions(generator=None)`): world w's values
  depend on N (`p_reginit.py`: world 0's `random_uniform` init differs at N=2 vs N=4). Documented in
  the registry docstring and registered (STATUS §7.4, checkpoint angle only); the N-dependence is
  not registered. The world-0 differential still holds.
- **vecN width mismatch** (`distance(vni, vni4)`, `distance(vecv, vni)`) and **literal out-of-range
  `gather(vecv, 5)` / `gather(vecv, -1)`** compile and raise at reset. Width is documented as a
  run-time check (`expressions.md:484`), but a declared `dims:` and a literal index are static.
- **Done worlds keep drawing.** Expression variables in a done world keep re-evaluating and drawing
  (the observation changes each step) while rules, writes and history freeze. That is consistent with
  vfs_runtime N7 / variables.md:328 and keeps stream position independent of death. No isolation
  impact.
- **Perf** (`p_perf.py`, CPU): N=64: 807 steps/s without draws → 723 with 1 agent draw → 539 with
  4 draw sites; N=256: 693 → 523 → 290. Per draw site, one `torch.rand` per world in a Python loop
  plus a stack (`functions.py:644`). Not pathological on CPU. On CUDA that is one kernel launch per
  world per draw site, so it will scale badly at large N.
- `respawn mid-episode`: there is no per-world mid-episode respawn in this env (a done world waits for
  `env.reset()`); covered as "episode-2 reset" instead.

## Areas

| # | Area | Verdict | Evidence |
|---|---|---|---|
| 1a | World-0 differential, N ∈ {2,4,7}, 64 steps + reset + 6 steps; random global/agent expressions, two-draw expression, double read, random rule, random action write, effect `sample` + effect `uniform`, periodic item spawns gated on a random var, world 0 teleported/INTERACTing/killed at t=20 | **HOLDS** | `p_diff.py`: 0 diffs in worlds 1..N-1 (obs, reward, done, meters, pos, every registry var, items, effects); A/A bitwise; effects sampled (sv nonzero) and items spawned |
| 1b | N-independence | **HOLDS** | `p_seed.py`: worlds 0..3 equal at N=4 vs N=8; world 0 equal at N=1 vs N=8 |
| 1c | Dead world | **HOLDS** (P3 note) | `p_dead.py`: streams keep advancing; rules and writes frozen; no effect on others |
| 1d | Two draws in one expression, the same variable read twice | **HOLDS** | `a_two` deterministic (A/A); `a_read2 == 2*a_rand` |
| 1e | Random expression read by a rule: stored, not inlined | **HOLDS** | `a_seen(t) == a_rand(t-1)` for 10 steps; tick-lifetime random read by a rule refuses |
| 1f | Unrelated declarations | **FAILS** (V3) | non-random additions are neutral; random additions and declaration order re-roll draws with no hash movement |
| 1g | Affordance-scope targets | **FAILS** (V1) | |
| 2 | Global RNG reachable from authored config | **FAILS narrowly** (V2) | VFS: `vtc.py:685` compile-time (V2), `registry.py:639,643` initializers (documented, P3). Env/positions: `vectorized_env.py:1681`, substrate `initialize_positions(generator=None)` (pre-existing). Effects: `executor.py:388` tick-seeded fallback only for a world-less context; 14-affordance interaction probe consumed no global RNG (`p_interact_rng.py`). Items: spawn predicate path gone (`SpawnPredicateReads.context` carries no rng; `uniform`/`normal_dist` refuse); schedules use `world_rngs`. Training (not authored): replay buffers, epsilon-greedy, oracle driver. Runtime step: no global RNG consumed (rollouts and guards checked) |
| 3a | Engine-defect guards | **HOLDS** | `p_defect.py`: None, 2-for-3 and 4-for-3 streams each raise "Engine defect", no global consumption |
| 3b | Episode re-derivation | **HOLDS** | ep2 ≠ ep1, ep2 reproducible |
| 3c | Two envs in one process | **P3** (V7) | lazy process-global seed |
| 4a | f_matrix delta | **HOLDS** | 24 newly admitted, 0 newly refused (exact list matches the claim); `elapsed_ticks` refused everywhere |
| 4b | Newly admitted cell values | **HOLDS** | spatial: hand-checked vs positions (manhattan/euclid/in_range); vector: distance 5.0, manhattan 7.0, gather, within_radius in expr/rule/action; draws: N=2048/4096 distributions (uniform range/mean, normal mean 0.004 std 1.000) |
| 4c | Derived shape rules | **FAILS** (V4, V5; V7 P3s) | nested, `where` mixed, global-vector-in-agent (refused, correct message), broadcast stats (`mean(bar.energy, gstat)`, `variance(..., gstat, 1.0)`, `argmax`, `count_where`) hand-checked, matching; position functions in `lag`/`ema` refuse naming the route; via a named variable they work |
| 5 | First observation (WP9) | **HOLDS** | `p_spatial.py`: grid2d randomize T/F, L2 POMDP, gridnd 4d, continuous1d: reset / step / episode-2 reset all equal the hand computation; aspatial yields 0 (known) |
| 6 | Spawn predicates | **HOLDS** | `uniform`/`normal_dist`/position function refused with the expression-variable route; random global and agent vars admitted; 76/0 spawn decisions match the own world's value at reset and retry |
| 7 | Behaviour preservation vs `39825727` | **HOLDS** | `p_preserve.py`: default_curriculum L1/L2/L3, model_pack, items_smoke, effects_smoke, trial_k_cold: 0 of 23 hashes moved; 48-step rollout (obs, reward, done, meters) bitwise equal; global RNG state equal |
| 8 | Perf | **P3** | see V7 |
| 9 | Gates in worktree | **HOLDS** | pytest: 5438 passed, 17 skipped, 1 deselected (20m23s, exit 0); no_defaults: clean, ratchet 618 at ceiling; token_type_schema_hash `de093a6e9f59924e…` on 33/33 compilable levels (3 refusals are the negative fixtures `vfs_circular_dependency`, `vfs_type_mismatch`, `vfs_undefined_var`, as at baseline) |
| — | Rules/writes refuse position functions naming the route | **HOLDS** | `[VTC-WRITE-TYPE] ... Declare the quantity as a global or agent expression variable and read it by name.` |
| — | `elapsed_ticks()` deleted | **HOLDS** | no hits in src/docs/configs/scripts; `REQUIRES_STEP`/`context.step` gone |
| — | Docs weather example | **HOLDS** | re-rolls at ticks 0, 4, 8 per world, holds between |
