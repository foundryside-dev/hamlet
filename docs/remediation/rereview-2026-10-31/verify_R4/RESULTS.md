# verify_R4: adversarial verification of f3a6d115 (repair package R4, fix/vfs-compiler-remediation-2)

Setup:
- Detached worktree `verify_R4/wt` at f3a6d115 with its own `.venv` (`uv sync --extra dev --extra recording`);
  `townlet.__file__` asserted under `wt/src` by every probe. Second worktree `verify_R4/wt_base` at 636192e0 for
  the AST and behaviour differentials, run with wt's venv and `WT=`/argv repointing, import path asserted.
- CPU only (`CUDA_VISIBLE_DEVICES=`). Probes in `verify_R4/probes/` (the R3 harness copied as `harness.py`/`r3pack.py`;
  the R3 verifier's own probes copied as `r3_*.py`); scratch packs under `probes/packs_wt`, `probes/work_*`.
- /home/john/hamlet untouched; no `git stash`. Both worktrees were clean (`git status --short` empty) and are removed at the end.
- No fixes made.

## DEFECTS (severity per rereview-2026-10-31/BRIEF.md; no P1, no P2 found)

### P3 — EXPRESSION-AFFORDANCE-UNDEPLOYED ignores declaration scope: a level-scoped expression is refused for another level's deployment
- `universe/validation/semantics.py:282` loops every level of the pack for every expression, including the ones
  from `levels/<L>/affordances` (`:241` collects them by prefix). An interaction `value:` in L1's own `affordances.yaml`
  naming EAT is refused because L0_0 does not deploy EAT, although that interaction can only run in L1.
- Repro (`probes/p6_refusals.py`, "L1 interaction names EAT (level-scoped), L0_0 does not deploy EAT"): default_curriculum,
  SLEEP on_start `bar.mood + 0.0 * distance_to_affordance("EAT")` in L1, EAT removed from L0_0's `enabled_affordances` →
  `[EXPRESSION-AFFORDANCE-UNDEPLOYED] levels/L1_full_observability/affordances.yaml:51`. With all levels deploying EAT it compiles and runs.
- The STATUS §5.3 design call covers pack-scope variables ("bites a curriculum whose early levels deploy fewer affordances");
  `expressions.md:496` states it for every position-function expression ("one a level does not deploy, refuses at compile at the
  expression's line"), so the behaviour is doc-consistent; for level-scoped families it is still an over-refusal the design call
  did not weigh. No shipped pack is affected (all levels deploy all 14).

### P3 — prose is scanned as an expression: a description that parses is refused
- `semantics.py:241` feeds every string leaf of every declaration (descriptions, labels included) to the parser; a leaf that
  parses and contains a position function with a string literal is checked like an expression.
- Repro (`p6_refusals.py`): custom action REST `description: distance_to_affordance("NOPE")` → `[EXPRESSION-AFFORDANCE-UNKNOWN] actions.yaml:10`;
  a variable `description: in_range("NOPE", 1.0)` → the same code at `variables.yaml:37`. Unlikely in practice; a false refusal nonetheless.

### P3 — residual compile-accepts / reset-crashes in the V7 class (narrower than before; the literal cases are now refused)
- `gather(v2, 1 + 1)`, `gather(v2, 2 + 3)` (constant index, not folded; `semantics.py:301` takes a literal only),
  `gather(direction_to_affordance("EAT"), 7)` and `distance(v3, direction_to_affordance("EAT"))` (computed argument of a
  statically known width, `semantics.py:292` takes bare variables only) all compile and raise `ValueError` at reset
  (`Function 'gather' index is outside the element axis [0, 2)` / `requires vectors of one width, got widths 3 and 2`).
- Repro: `p6_refusals.py` "EXPRESSION-VECTOR-WIDTH / EXPRESSION-INDEX-RANGE" block. `docs/config-schemas/expressions.md:484` (as of
  this commit) promises compile refusal only for "two declared variables of different dims or shape" and "a literal gather/scatter
  index", and says "a width only an expression produces is checked at run time, and a mismatch there raises an error naming the
  function" — which is what happens. Documented behaviour, so P3 (the R3 verifier's classification), not a broken contract.

### P3 (known, STATUS §7.4) — placement draws from torch's global RNG; layout and spawn depend on N
- `environment/vectorized_env.py:1679,1683,1691,1696,1700` (`generator=None`, `randperm`, `randint`). `p3_place.py`: same seed, the
  14-affordance layout differs between N=2 and N=5 (the constructor's `initialize_positions(num_agents)` at `:782/:788` consumes
  N-dependent global RNG before reset), world 0/1 spawn differs, and reset advances the global RNG state. `_sample_free_cells`
  re-draws only clashing rows, so world w's spawn also depends on the other worlds' clashes. Same-seed A/A is identical.

### P3 (known, out of lens: effects) — a bar written by an effect is out of bounds in-tick and rules read it raw
- `p4_clamp.py` last block: effect on_tick `modify bar.satiation value: bar.satiation - 5.0` on default_curriculum; a rule at
  `apply_transition_rules` doing `bar.mood += bar.satiation * 0.01` moves mood by **-0.044** (reads -4.0) and **-0.054** the next
  tick (reads -5.0); satiation is 0.0 after `clamp_and_validate`. D3 closed this for action writes and rules
  (`vfs/transition_schedule.py:_clamp_written_meters`); the effects executor's `modify` (`effects/executor.py:170`) is the same exposure
  through a different door. BRIEF scope excludes effects; listed, not counted.

### P3 nits
- `uniform(5.0, 2.0)` is admitted and draws from (2, 5]; `normal_dist(0.0, -2.0)` is admitted (sign flipped). Docs say `[low, high)`.
  `world/expression/functions.py:644,655`. Neither refused at compile.
- `if(x)then(1.0)else(2.0)` (no spaces) fails loudly with "Expected end of text, found 'then'" because `if(` is read as a call.
  Pre-existing; loud, not a misread.
- DemoRunner (pre-existing, runner, out of lens): the final checkpoint is saved after `current_episode += 1`
  (`demo/runner.py:953` then `:971`), so a resume (`:505`, loaded+1) skips one runner episode index. The env's draw counter is
  consistent (verified below), but a 3-episode run resumed to 5 runs 4 episodes.
- Draw-site identity, for the record (`p2_sites.py`): a rule's draws are keyed `rule:<id>:<write index>`, so swapping a rule's writes,
  inserting a non-random write before a random one, or renaming the rule re-rolls that rule's draws, and every such edit moves
  `transition_graph_hash` and `vfs_hash` (covered). Reordering rules, adding an unrelated rule, and renaming a write's *target*
  variable change nothing. Expression variables are keyed `var:<id>`, so renaming one re-rolls it (`variable_schema_hash`,
  `variables_hash`, `vfs_hash` move).

## AREAS

### 1. Prior repros: HOLDS
`p1_r12_rerun.py`, `r3_*.py` (the R3 verifier's own probes, unmodified apart from the harness path).
- D1: `true_count`, `truex`, `falsey`, `notable`, `nothing`, `not_x`, … all parse as one identifier; e2e `if notable then 7 else 3`
  with `able` and `notable` both declared gives **7.0**; `true_count + 1.0` = 2.0.
- D2: EAT `[99,2]` / `[2,2,2]` under randomize compiles, runs randomized at n=2 **and n=51** (`randomize` stays True); shipped
  `static_epistemic_access` builds at n=61 and n=2. The fallback is gone.
- D3: every `m_oob`/`m_oob2` row now gives dhealth -0.0090 / denergy -0.0160 / dmood -0.00400 (the clamped values).
- D4: `[LOAD_ERROR] stratum.yaml:11 … interaction_radius (20.0) exceeds the span of bounds[0] (10.0)`; the `ContinuousConfig`
  DTO refuses a rank-4 radius 20 the same way.
- P3s: gridnd rank 9 and 100 refuse at the DTO (`stratum.yaml:7`, "4 to 8 (MAX_POSITION_RANK …)"); `DAC-REF-001` at `drive.yaml:5`
  (the `bar:` line) and `CLOCK_REFERENCE` at `curriculum.yaml:13` (the `period_of` line); persistent `effect_ref`/`affordance_ref`/`item_ref`
  refuse at the declaration, `agent_ref` compiles; moving an effect to `aa_more_effects.yaml` no longer moves `effects_hash`;
  the stale docstring is gone.
- V1: every `p_aff.py` expression runs at N=3 and N=14 with `world0(N) == world0(N=1)` and no row-constant leak; `p_aff_cond.py` likewise.
- V2: `p_refconst4.py` refuses under all 16 global seeds (compile admission is deterministic).
- V3: `p_order_hash.py` and `p_unrelated.py`: declaration reorder, file move, unrelated random agent/global/rule — nothing re-rolls.
- V4/V5: `tensor1d` zeros-mode `gather` runs (0.0); vector `==`/`!=`/`>` refuse at `[VFS-PROFILE-COMPILE]`.
- V6: typo and undeployed names refuse `[EXPRESSION-AFFORDANCE-UNKNOWN]` / `[-UNDEPLOYED]` at the declaration line.
- V7: `p_seed.py`: env X (seed 1) episode 2 now equals solo seed-1 episode 2 after constructing env Y (seed 2); `initial_seed`
  unchanged by construct/reset/step. `p_reginit.py`: `random_uniform` initializers and spawn still N-dependent (known §7.4).
- `p_diff.py` (items_smoke, N=2/4/7, 64 steps): 0 diffs in worlds 1..N-1, A/A identical, effects sampled, items spawned.

### 2. Counter-based randomness: HOLDS
`p2_stats.py`, `p2_sites.py`, `p2_resume.py`, `p9_misc.py`.
- Kernel vs `reference_uniform`: exact at (seed, episode, tick, site, ordinal, world, element) samples including seed -1, 2^63,
  tick 2^40, ordinal 2, element 7.
- 1e6 uniform: mean 0.50024, var 0.083318, min 4.2e-7, max 0.99999982, all in [0,1); 100-bin χ² = 77 (df 99). 1e6 normal (Box–Muller):
  mean 0.00056, var 1.00029, skew 0.0007, kurtosis 3.0022, 71 values with |x|>4 (expect ~63), all finite.
- Correlations (1000 ticks × 1000 worlds, then 1e5): adjacent ticks -0.00005, adjacent worlds -0.00056, t vs t+37 +0.00003,
  adjacent elements -0.0015, two draws in one expression -0.0035, episode 1 vs 2 +0.008, sites var:a vs var:b +0.003 (1e5),
  seed 1 vs 2 -0.002 (1e5). All within noise.
- Repeats: 262144 values over 4096 worlds × 64 ticks → 2087 repeats vs 2048 expected from the 2^24 grid; every value is an exact
  multiple of 2^-24; no two world rows identical over 64 ticks.
- Edge cases: `uniform(3,3)` = 3; `normal_dist(0,0)` = 0; ±1e30 and 1e-45 ranges finite; ticks 0 … 2^63-1, 2^63, 2^64-1 all match the
  reference (tick and seed alias mod 2^64, as the spec says); episodes up to 2^64+5 fine; seed 0, -1, -2^63, 2^64-1 map to the
  masked state and reproduce; `restore` refuses a negative, bool, float or missing field; 100000 resets fine; `_shr` is a logical
  shift on negative int64. 1000 draws × 256 worlds in 0.06 s (vs the Python-loop generators of R3).
- Sites: see the P3 note above. The rule-level condition is one shared site: with `condition: uniform() < 0.5` and two writes,
  c1 == c2 in 2560/2560 rows (fired 1268); with each write also carrying its own random condition, "exactly one fired" is
  23/2560 (the two writes' own 1% conditions), i.e. the rule-level draw is still shared and the write-level ones independent.
  Two draws in one expression: `uniform() - uniform()` std 0.401 (0.408 expected), never 0.
- Global RNG: `torch.get_rng_state()` unchanged over 5 steps of a drawing pack; `manual_seed(999)` after construction changes no draw.
- Resume (`p2_resume.py`, real `DemoRunner.run()` on a default_curriculum L1 copy, N=2, 6 steps/episode, random global + agent
  expression + random rule, `VectorizedHamletEnv.step` wrapped to log draws): run A 5 episodes; run B 3 episodes (checkpoints at
  runner episodes 0, 2 and the final one); run C resumes B's directory to 5. C's rows equal A's at every (env episode, tick):
  6 compared, 0 mismatches; B's rows are a prefix of A's. `live_inference.py:475` restores before its first `reset()` (`:654`).
  Mid-episode save: the only other save path is the `finally` save after a shutdown that breaks the step loop; it carries the
  episode counter already incremented (the runner nit above), the draw contract itself holds.
- S1 (`p9_misc.py`, default_curriculum, N ∈ {2,5}, 40 steps, global/agent/affordance-target/action-write draws plus an effect
  `sample`, world 0 teleported+INTERACTing at t=5 and killed at t=15): 0 diffs in worlds 1..N-1, A/A identical, world 0 differs
  at 35/40 ticks, effect sampled at 35 ticks; world-0 draws (g_rand, aff_v, aff_w) equal at N=1 vs N=5.
- Affordance-target shape through arithmetic: `uniform(0.0, bar.energy)`, `uniform() + a_rand`, `normal_dist(bar.energy, 0.1)` on an
  affordance target refuse at compile (`[VTC-WRITE-TYPE]`); `uniform() * g_rand` runs world-local at N=3 and N=14.
- `claim_if_free agent_id` with `condition: uniform() < 0.5` compiles and claims per world.
- Engine-defect guards (R3 area 3a, re-verified at this SHA; `p9c_guards.py`, `p9d_guard_profile.py`): action writes and transition
  rules run with `draws=None` on a drawing pack raise "Engine defect: … ran without the instant's draws"; draws for 2 worlds on 3
  agents raise "ran with draws for 2 worlds, not 3"; a global profile with a drawing variable marked raises "sample, but the profile
  was evaluated without the instant's draws"; `DrawStream` with shape `(3,)` or `()` for 2 worlds, and a `(5,)` or `(2,14)` argument in
  a `(2,)` context, raise. None consumes the global RNG. A `(14,)` argument in a `(2,14)` context is admitted by broadcasting (an
  affordance-axis-only tensor; nothing in VFS produces one and the compile proof refuses `[W]` operands there) — noted, not a defect.

### 3. Per-world placement (D2): HOLDS (known P3 above)
`p3_place.py`, `p3_place_b.py`.
- L1, N=64, 100 resets: 0 duplicated affordance cells, 0 agents on an affordance, 100 distinct layouts, in bounds.
- Boundary with the 14-affordance vocabulary: 3×5 (15 cells) and 1×15 compile and run 30 resets at N=50 clean; 2×7 and 1×14
  (14 cells) refuse `[GRID_CAPACITY_EXCEEDED] levels/<each level>/training.yaml:23` (the `randomize_affordances` key). The
  check counts **deployed** affordances (2×2 with 14 declared / 2 deployed compiles and runs). Compile capacity equals
  `substrate.get_capacity()` on the cubic (192) and gridnd (625) packs. Bypassing the compile (capacity 12 < 15) raises the
  runtime guard.
- Randomize false: all 14 positions equal the declared ones. (An agent may spawn on a declared affordance under randomize false —
  pre-existing, `vectorized_env.py:788`; noted, not new.)
- Same seed, same N: layout and spawns identical. N-dependence and global RNG: the known P3.

### 4. Meter clamp at commit (D3): HOLDS (effects path noted)
`p4_clamp.py`, `p4_clamp_b.py`.
- A rule `+5` / overwrite 7 / `-5` on satiation at every one of the 13 phases before `clamp_and_validate`, and an action write `±5`
  at every one of the 9 action phases: satiation ends at 1.0-depletion or 0.0, and health/energy show only the clamped cascade
  (dhealth -0.0090/-0.0050). No raw value leaks.
- Composition in one phase is clamped once: two rules `-1.5` and `+0.8` (two rules, or two writes of one rule) give 0.292
  (= 1.0 - 0.7 - 0.008), not 0.8. An action `+5` then a rule reading `bar.satiation` in the same phase reads **1.0** (dmood +0.006
  with mood started at 0.5), not 5.3 and not the phase-entry value.
- Asymmetric bounds: money +2e6 → 999999, -5e6 → 0, overwrite -3 → 0. Satiation re-bounded to [0.2, 1] lethal_min: rule -0.95 →
  0.2000 and `done`; overwrite 0.25 → 0.242, alive.
- Lethal: health := 0, -= 5, -= 1.0 at ingest_actions / passive_depletion / threshold_cascades / transition_rules all end the
  episode that tick; an action write -5 kills both worlds; `agent_id == 1` kills world 1 only.
- Effects: see the known P3.

### 5. Keyword parsing (D1): HOLDS
`p5_kw.py`.
- Every keyword as prefix, suffix, with digits and underscores (`notable cannot untrue band door motif iffy heathen elsewhere
  truest falsehood andy orb then_x x_if true1 not2 if1 _not ifx notnot andand oror true_false elseif thenelse truefalse nottrue`)
  is one identifier; `notable and not able or orbit`, `not notable`, `not not able`, `if iffy then thenx else elsewhere`,
  `truex or true`, nested if/then/else, `a and(b)`, `(a)and(b)`, tabs, `-notable`, `not -able`, `x.notable`, `bar.not_energy` all
  parse as intended. `a andb`, `then1.0`, `else2.0`, `elsex` fail loudly.
- Shipped packs: every string leaf of every YAML under `configs/` (5413 leaves, 5038 parse) parsed at f3a6d115 and at 636192e0 with
  each tree's own parser; canonical ASTs (line/column stripped) are identical for all 5413.

### 6. New compile refusals: HOLDS (three P3s above)
`p6_refusals.py`.
- ASPATIAL (aspatial_test): variable, nested call, `in_range`, rule write, effect `on_tick value`, interaction `on_start value` all
  refuse at their own line.
- UNKNOWN (default_curriculum): variable, nested in where/max, `direction_to_affordance` under gather, `in_range`, inlined chain,
  lower-case `"eat"`, rule write, rule condition, action write, action write condition, effect value, interaction value all refuse
  at their own line; an item spawn `when:` refuses earlier (`[ITEM-SPAWN-CONDITION]`, the expression-variable route).
- UNDEPLOYED: a pack variable naming EAT refuses when L0_0 or L1 does not deploy it (compiling L1), as the design call says;
  `gridnd_4d_pack` (`enabled_affordances: []`) refuses. Level-scoped sources: the P3 above.
- VECTOR-WIDTH: `distance(v2, v3)`, `distance(v2, gv3)` (global), `manhattan_distance(t13, vn4)`, `within_radius`, `nearest`, and the
  same in a rule, refuse. INDEX-RANGE: `gather(v2, 5|-1|2)`, `gather(t13, 3)`, `gather(vn4, 4)`, `scatter(v2, 5, …)`, and in a rule,
  refuse; `gather(v2, 1)` runs; `gather(v2, 5.0)` refuses on type. Residuals: the P3 above.

### 7. Behaviour preservation vs 636192e0: HOLDS
`p7_preserve.py`, run from both trees with the same venv (N=4, seed 42, 48 scripted steps; per-tick hashes of obs, meters,
positions, every registry variable, reward, done; plus every `*_hash`, the layout, the action list and the global RNG state).
- As shipped: model_pack L0_demo, items_smoke, effects_smoke, trial_k_cold bitwise identical at every tick, same layout, same RNG
  state; the only hashes that move are `u.effects_hash` on items_smoke and effects_smoke (the id sort, as the commit says).
  default_curriculum L1 and L3 (randomize true) differ from tick 0 with a different layout — the expected placement change.
- With `randomize_affordances: false` forced in the copies: L1 and L3 are bitwise identical too, no hash moves.

### 8. Gates in the worktree: HOLDS
- `CUDA_VISIBLE_DEVICES= uv run pytest tests -q --no-cov -p no:cacheprovider`: `5523 passed, 15 skipped, 1 deselected, 13 warnings
  in 1108.53s`, exit 0 (`verify_R4/pytest_full.log`).
- `no_defaults_lint --ratchet`: clean, 617 whitelisted, "at the ceiling"; `.defaults-ratchet` = 617. ruff clean; black 638 unchanged;
  `validate_compiler_cli.py` passes.
- `token_type_schema_hash` on every level of every pack (fresh copies, no cache): 33 of 36 compile, all `de093a6e9f59924e`; the 3
  refusals are the negative fixtures `vfs_circular_dependency`, `vfs_type_mismatch`, `vfs_undefined_var`, as at baseline.

## Not covered
- CUDA (the kernel's `_shr`/int64 wrap was checked on CPU only).
- `r3_p_defect.py` as written no longer runs (`vfs_random_streams` is gone); its intent is covered by `p9c_guards.py` / `p9d_guard_profile.py`.
- mypy (not rerun; the Lint job runs it in CI).
- Effects/items generators' resume (known not checkpointed, §7.4).
