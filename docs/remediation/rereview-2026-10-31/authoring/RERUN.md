# Re-review rerun — lens `authoring` at `f3a6d115` (green call)

Detached worktree `scratchpad/rereview/authoring/wt2` (removed at the end), CPU, `REVIEW_WT=wt2
PYTHONPATH=wt2/src` with `/home/john/hamlet/.venv/bin/python`. `/home/john/hamlet` untouched; no
`git stash`. Same probes as the first pass (`probes/harness.py` now takes `REVIEW_WT`), plus
`probes/d_docs2.py` (line-agnostic doc splice at the new line numbers; every YAML block of the five
docs, including bare `expression:` / `value:` / `condition:` fragments wrapped in the context the
doc states). Logs: `probes/out2_mechanics.log`, `out2_mechanics2.log`, `out2_items.log`,
`out2_matrix.log`, `out2_docs.log`, `out2_closure.log`, `lint2.txt`.

## 5. VERDICT: GREEN, with one P2 I ask the coordinator to weigh (A9, below)

Every blocking item from `559dd0f9` is closed or moved:
- A1 closed (rules on meters step; four VFS.md examples step; the meter is clamped).
- A2 closed (random draws in expressions, rules and action writes; per world; same-seed A/A bitwise;
  seed 8 differs).
- A3 closed (position and vector functions in expressions, rules and action writes; `elapsed_ticks`
  deleted; the exposed `distance_to_affordance` is correct in the first observation).
- A4 closed as a refusal (`[AFFORDANCE_OPENING_HOURS_DAY_PERIOD]` at the affordance's `file:line`).
- A5/A6: I accept the UaC scope call. The action-mask gap's lowering target is a VTC phase, but the
  authored surface (an `actions.yaml` predicate) and the consumer (`ActionMaskBuilder`) are action
  -space; neither is a VFS or compiler contract that is claimed and does not hold.

The one thing I would not want to go unrecorded is **A9** (pre-existing at both SHAs, found by the
new fragment-level doc splice): the expression parser refuses any `if` whose condition starts
with `(`. By the letter of the bar it is a P2 (a documented expression form and a doc example
refuse), it is in `world/expression/` (in scope), and the refusal text does not name the cause.
Against it: the workaround is trivial (drop the outer parenthesis or write `if not not (...)`),
nothing mis-evaluates, and it has nothing to do with the sprint's contracts. My call: GREEN with
A9 filed as the first P2 of the next phase; if the coordinator reads the bar strictly, it is the
only blocking item.

## 1. Findings rerun (A1–A8) and new

| id | at 559dd0f9 | at f3a6d115 | evidence |
|---|---|---|---|
| A1 rule on a meter crashes at step | P1 | **closed** | `r1`: `energy_base_depletion` at `apply_passive_depletion` steps, energy 1.0→0.985 (= passive 0.01 + rule 0.005); `r2` `low_health_hits_mood` steps; `m1` night hunger: dsat −0.058 at night, −0.008 by day; `m13` doom≥3 zeroes health → `done=[True,True]` on tick 4; VFS.md:1485/:1500/:1735 step. Bars commit path: `vfs/transition_schedule.py:111-118,129-149` (`_split_vfs_and_bars`, `_clamp_written_meters`). |
| A2 no random draw in VFS | P2 gap | **closed** | `m7`: rule `overwrite uniform(0.0, 3.0)` with `condition: tick % 4 == 0` → three worlds `[2.081, 0.618, 2.806]` for ticks 1-4, `[0.548, 0.451, 2.315]` for 5-8; variables.md:395 `weather` expression steps; same-seed A/A identical, seed 8 differs, worlds differ. Matrix: `uniform`/`normal_dist` REFUSED→OK in gexpr, aexpr, rule_g, rule_a, action (10 cells). |
| A3 shape allow-list strands functions | P2 gap | **closed** | Matrix REFUSED→OK: `gather`, `distance_to_affordance`, `in_range`, `distance`, `within_radius` in aexpr/rule_a/action (14 cells); extra cells `manhattan_distance`, `nearest(vecv, t2d)`, `within_radius` OK in all three; vector-returning `normalize`/`direction_to_affordance`/`scatter` refuse into a scalar target with "declared as scalar but expression returns vec2f" (correct); `elapsed_ticks()` → `Unknown function`. `m8`: `distance_to_affordance("EAT")` and `min(... "EAT", ... "COOK")` compile; first observation after `reset()` carries `0.3125 = 5/16` with registry 5.0 for an agent at (2,0) and EAT at (2,5) (manhattan 5; agent 1 at (7,2) → 8). 101 → 125 OK cells of 245. |
| A4 opening hours vs period ≠ 24 | P2 | **closed (refusal)** | `m10`: `[AFFORDANCE_OPENING_HOURS_DAY_PERIOD] levels/L3_temporal_mechanics/affordances.yaml:9 - Affordance 'EAT' declares opening_hours, but level ... has a day clock period of 48; opening hours currently require a 24-tick day period` (`universe/validation/semantics.py:401-419`). The four 24-sites remain (`functions.py:678`, `token_spec.py:391`, `affordance_identity.py`, `affordances_v2_config.py:44`) behind that refusal — §7 design item, not a defect now. |
| A5 affordance closed by a variable | P2 gap | **UaC** | `m9`: every spelling still `extra_forbidden` (expected; moved by scope call). |
| A6 action masked by a condition | P2 gap | **UaC** | `m3b`: no predicate field (expected; moved). |
| A7 doc drift | P3 | **closed** | see §3: every block parses, compiles and steps except the ones the doc itself labels incomplete or bad, and A9. |
| A8 refusals without a fix | P3 | **closed** for the ones I listed | shape: "Variable 'ax' is agent-scope but its expression 'lag(tick, 1)' reads no per-agent state ... Declare 'ax' with scope: global, or read agent state (an agent variable, a meter 'bar.<m>', a position function)"; rule shape: "expression 'gstat * ascalar' is agent-shaped, but its target 'gtarget' has declared scope 'global', which admits scalar-shaped values"; spawn predicate: "calls 'uniform', which needs a random stream on the context, which an item spawn predicate does not carry. Declare the quantity as a global or agent expression variable and read it by name." The A1 runtime KeyError is gone with A1. Not re-audited: `variables_config.py:93/:101/:104`, `vtc.py` vocabulary refusals, `token_spec.py:1125`. |
| no-defaults / name branches / shims | P3 | **unchanged** | see §4. |

### A9 (NEW, P2 by the bar, pre-existing) — `if (` never parses
- claim: any `if` whose condition begins with an open parenthesis fails at parse with
  `Expected end of text, found 'then'`: `if (bar.energy < 0.2) then 1.0 else 0.0`,
  `if (bar.energy < 0.2) and (bar.health < 0.2) then ...`, `if (a + b) * c > 1.0 then ...`.
  `if not (…) then`, `if a and b then`, and `(a) and (b)` outside an `if` all parse.
- cause: `primary_base = constant | function_call | if_expression | path_or_variable`
  (`world/expression/parser.py:145`) tries `function_call = identifier + "(" + …`
  (`:109`) before `if_expression` (`:135-137`), and `identifier` does not exclude keywords, so
  `if (…)` is consumed as a call to a function named `if` and the `then` is left over. Identical
  at `559dd0f9` (`probes/parser_old.py`).
- where it bites the docs: expressions.md:968 ("Bad — hard to read", but it is meant to be a
  valid expression, and the doc's best-practice 1 at :850-860 says to parenthesise) refuses in an
  interaction with `[EFFECT-COMPILE] affordances.yaml:50 ... Expected end of text, found 'then'`
  — located, but the message does not say "the parenthesis after `if`".
- fix shape: exclude `EXPRESSION_KEYWORDS` from `identifier` (or order `if_expression` before
  `function_call`); one parser test with a parenthesised condition.
- repro: `PYTHONPATH=wt2/src python -c "from townlet.world.expression.parser import ExpressionParser as P; P().parse('if (bar.energy < 0.2) then 1.0 else 0.0')"`.

### Other observations (P3, not blocking)
- `uniform`/`normal_dist` are now **refused** in an item spawn predicate (`out2_items.log`; at
  `559dd0f9` they were admitted). The refusal is located and names the fix (declare an expression
  variable), and variables.md's consumer table says spawn predicates read variables and meters, so
  this is consistent; note it as an intentional narrowing so nobody files it as a regression.
- `expressions.md:975` and `:1025` are fragments the doc labels "complete required fields shown in
  variables.md"; as written they refuse (`id`/`scope`/… missing). Fine as labelled.
- `expressions.md:956` "Bad — type mismatch (int vs float)" refuses as the doc says it should.

## 2. Designer-mechanics table at f3a6d115

| mechanic | 559dd0f9 | f3a6d115 | evidence |
|---|---|---|---|
| hunger decays faster at night | GAP (A1) | **EXPRESSIBLE** | global `is_night` expr + rule on `bar.satiation` gated `condition: is_night` → −0.058/tick at night vs −0.008 by day (`m1`) |
| ticks since the agent last ate | EXPRESSIBLE | EXPRESSIBLE | `m2c`: 1,2 → 0 on the +energy write → 1 → 0; variables.md:446 steps |
| cooldown on an action | AWKWARD / GAP (mask) | AWKWARD / **UaC** (mask) | `m3` gated writes fire at ticks 1 and 4 only; no predicate field (`m3b`) |
| resource regenerates toward a cap | EXPRESSIBLE | EXPRESSIBLE | `m4` 0.3,0.6,0.9,1.0,1.0 with clamp; asymptotic form too |
| reward on a rising edge | EXPRESSIBLE | EXPRESSIBLE | `m5/m5b` reward 5.97 on the edge tick only |
| variable persists across episodes | EXPRESSIBLE | EXPRESSIBLE | `m6` 3.0 before and after `reset()` |
| per-world global weather every K ticks | AWKWARD (deterministic) / GAP (random) | **EXPRESSIBLE** | `m7` rule form; variables.md:395 expression form `where(tick % 4 == 0, uniform(0.0, 3.0), lag(weather, 1))` exposed; per world, per seed |
| observation "distance to nearest food" | GAP (A3) | **EXPRESSIBLE** | `m8`; first observation 5/16 for manhattan 5; `min(distance_to_affordance("EAT"), distance_to_affordance("COOK"))` compiles |
| affordance closed by a variable | GAP (A5) | GAP → **UaC** | `m9` |
| opening hours keyed to a declared period ≠ 24 | GAP (wrong silently) | **refused at compile** (located) | `m10`; the full fix is §7 of STATUS.md |
| item state decays while held | AWKWARD (effects) | AWKWARD (effects) | `m_items.py m11c`: apple `on_pickup: [{spawn_effect: food_decay, target: self, intensity: 1.0}]` → held apple condition 96, 94, 92, 90 over four ticks, rerun inline at f3a6d115 (the scripted `m11c` writes `target: item`, a harness bug, and refuses; `target: self` is the working form). VFS route refuses by design (`m11a/m11b`) |
| action masked unless a condition holds | GAP | GAP → **UaC** | `m3b` |
| terminal condition on a variable | GAP (A1) | **EXPRESSIBLE-BUT-AWKWARD** | `m13`: rule `doom >= 3.0 → overwrite bar.health 0.0` → `done` on tick 4 (through a lethal meter; no `terminal_when` on a variable) |
| private variable drives a reward | EXPRESSIBLE | EXPRESSIBLE | `m14b` reward gap 1,2,3; no obs row; agent read refused |
| moving average of a meter exposed | EXPRESSIBLE | EXPRESSIBLE | `m15` obs row tracks `moving_average(bar.energy, 4)` |

Score: 11 EXPRESSIBLE (one of them awkward), 2 AWKWARD (held-item decay via effects; cooldown
without a mask), 1 refused-by-design (non-24 opening hours), 2 moved to UaC. No GAP left in VFS or
compiler scope.

## 3. Doc examples at f3a6d115 (`probes/d_docs2.py`, 86 splices)

- **variables.md**: `:8` day_phase (whole declaration) OK; `:395` weather OK (exposed, per world);
  `:446` time_since_last_sleep OK.
- **declarations.md**: `:106` period_of → 24 on L3 OK (`:62` is the transport illustration, not run).
- **transition_rules.md**: `:46` OK once the illustrative names are declared (as its caveat says);
  public_reputation 0.5 → 0.05 after three ticks.
- **expressions.md**: `:214` is_critical OK (as a whole `variables:` document it refuses only because
  my splice replaced the pack roster that L3's `period_of: day_phase` needs — appended, it steps);
  `:236` regeneration effect as effects.yaml OK; `:265` spawn rule with `when` OK (items_smoke,
  `is_winter` declared); `:701` is_night/is_crisis/motivation OK; `:755`+`:769` in_crisis +
  `vfs_variable` shaping OK; `:995` OK; `:975`/`:1025` refuse as labelled-incomplete; every bare
  `expression:` line at `:599/:612/:632/:646/:658/:678/:690/:789/:932/:956/:1063/:1075` compiles
  and steps in the scope the doc comment states (global for `is_night`/`tick`-only, agent for
  `bar.*`), the one "Bad — type mismatch" (`:956`) refusing as documented; `:606` effect locals
  `intensity`/`duration_remaining` OK in an agent effect; every `value:` line at
  `:620/:740/:780/:944/:986/:1032` OK in an interaction or agent effect; `:670` `item.durability > 0`
  OK in a medkit `on_use` `if`. **Fails: `:968`** (A9, `if (` parse).
- **VFS.md**: `:290/:344/:534/:680/:931/:986/:1096/:1318/:1485/:1500/:1517/:1636/:1735/:1758/:1778/
  :1828/:2052/:2504/:2577` all compile and step with the documented effect (job_is_open true at
  tick 10; CALL_AMBULANCE `occupied_by[DOCTOR] = [0, -1]`; rules on meters now move energy/mood).
  `:1959` refuses and is marked "not authorable" (expected). `:2493` (presentation label) and
  `:2709` (versioning sketch) are not variable declarations and were not run.

## 4. Principle violations at f3a6d115

- **No-defaults.** `scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt
  --ratchet .defaults-ratchet` → clean, 617 whitelisted, at the ceiling. Whitelist unchanged since
  `559dd0f9` (ratchet 618 → 617); every whitelisted path resolves on disk. Empty-whitelist run over
  `config/`, `vfs/`, `universe/`, `world/expression/`: 241 sites. New in the remediated files:
  `vfs/random_draws.py` none; `vfs/evaluator.py:108 .get(..., default)` and `:39-40`,
  `profiles.py:274/307/364/516`, `vtc.py:2429-2440,2493` (`.get` defaults on the raw-mapping rule
  branch, previously adjudicated dead), `schema_hashes.py:377/415` (function parameter defaults),
  `symbol_table.py:32-38` (dataclass `default_factory`) — engine-internal, none authorable. The
  YAML-reachable behavioural defaults I listed under A7 are unchanged and still under blanket
  waivers: `config/drive_as_code.py:573-576, 605-610, 193-205` and `config/items_config.py:266-267,
  313-314, 340-362`. `actions_config.py:48-58` (`source_affordance`, `writes`) and
  `items_config.py:134 exclusive` (required) are fine.
- **Name branches (PDR-0045).** Grep for the eight `default_curriculum` meter names over the in
  -scope dirs → docstrings and `>>>` examples only. The only domain constant is still the 24-tick
  day (`functions.py:678`, `token_spec.py:391`, `vtc.py:3450` always-open window `(0, 24)`,
  `affordances_v2_config.py:44`), now guarded by `semantics.py:401-419`; `random_draws.py:46
  _UNIFORM_BITS = 24` is a mantissa width, not a day.
- **Backcompat shims.** None new: `namespace.py:243-244 _LEGACY_*` still refusal-text only;
  `hasattr` only at `compiler.py:706-709` (YAML error marks); `compilers/actions.py:201 "BACKWARD"`
  is a label-preset direction name. Old artifacts refuse on the schema version.

## Closure rows rerun (`out2_closure.log`)
V1/V2/V3/V4/V5/V7/V8/V9/V12/V13/V14, C1/C3/C4/C5/C7 all still CLOSED with the same evidence as
the first pass (C7's refusal now cites `display.yaml:3`). C8 feedforward twins compile; the
`token_set` cell in `c_closure.py` is my brain-vocabulary mistake (the hand-written probe with
`architecture: {type: token_set, ...}` refused `[TOKEN-IDENTITY]` in the first pass and was not
re-run).

## Not covered
The full test suite (another lens); COMPILER.md; runtime registry/checkpoint; CUDA; effects
semantics beyond the one held-item probe; a re-audit of every refusal message outside the ones
named above.
