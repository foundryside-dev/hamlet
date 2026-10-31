# verify_R12: adversarial verification of 39825727 (fix/vfs-compiler-remediation-2)

Setup:
- Detached worktree `verify_R12/wt` at 39825727, with its own `.venv` from `uv sync --extra dev --extra recording`. `townlet.__file__` resolves under `wt/src`.
- Second worktree `verify_R12/wt_base` at 559dd0f9, for the differentials. It runs with wt's venv and `PYTHONPATH=wt_base/src`, and each run asserts the import path.
- Everything ran on CPU (`CUDA_VISIBLE_DEVICES=`).
- Probes are in `verify_R12/probes/`, scratch packs in `verify_R12/work/`.
- I did not touch /home/john/hamlet and did not use `git stash`.

## DEFECTS (most severe first)

### D1 P1: variable ids that start with a keyword pass the new grammar, and the lexer misreads them
- **Claim:** "Variable ids follow the expression identifier grammar, derived from the parser."
- **What happens:** `is_identifier` (`world/expression/references.py:572-579`) admits any `[A-Za-z_]\w*` that is not exactly a keyword. The parser matches three keywords with `Literal`, not `Keyword`: `true` and `false` at `parser.py:61-62`, which are tried before the identifier, and the prefix unary `not`. Only those three prefixes misparse. `iffy`, `if_open`, `thenx`, `elsewhere`, `orbit`, `order`, `android` and `and_x` all parse as plain variables:
  - `notable`, `nothing` and `not_x` parse as `UnaryOp(NOT, Variable('able'/'hing'/'_x'))`. This is silent.
  - `true_count`, `truex`, `falsey` and `false_alarm` fail with "Expected end of text, found '_'". This is loud but misleading.
- **Repro:** `probes/refusals/r_ids.py`. Declare agent bools `able: true` and `notable: true`, and `probe: if notable then 7.0 else 3.0`. The pack compiles, and `probe` is **3.0** in every world when it should be 7.0.
  - With `notable` alone: `[VFS-PROFILE-COMPILE] ... 'able' names no variable`.
  - With `true_count + 1.0`: `does not parse: Expected end of text, found '_'`.
- **Trigger:** the silent misread needs both `able` and `notable` declared. With `notable` alone the refusal is loud but misleading.
- **Fix shape:** use pyparsing `Keyword` (or `Literal + ~Word(IDENTIFIER_BODY_CHARS)`) for `true`, `false` and `not`. Making `is_identifier` refuse keyword prefixes would be the wrong fix, because `order` and `android` are legal today.
- **History:** the parser bug predates this commit, but the commit says it closed the N6 class ("expressions read the literal, not the variable"), and this case is that class.
- **Probe output:** `probes/parser_ids.py`.

### D2 P2: `randomize_affordances: true` is not position-free at runtime, so skipping the position checks there loses refusals
- **What happens:** `_validate_affordance_deployments` (`universe/validation/semantics.py`, `if level.training.randomize_affordances: continue`) skips every position check under randomize true. The runtime, however, falls back to the declared positions when `len(affordances) + num_agents > substrate capacity`. That fallback is `randomize_affordance_positions`, `environment/vectorized_env.py:1630-1650`: it sets `self.randomize_affordances = False` and then `_apply_configured_affordance_positions`. `num_agents` is a runtime argument, so the compiler cannot know whether the fallback will fire.
- **Repro:** `probes/rand_fallback.py`.
  - default_curriculum L1, EAT `[2,2]` changed to `[99,2]`: it compiles, and with `num_agents=2` the positions are randomized. With `num_agents=51` the run prints `env.randomize_affordances now False` and EAT is placed at **[99, 2]**, off the 8×8 grid, silently.
  - Same pack with `[2,2,2]` at `num_agents=51`: `RUNTIME ValueError: Affordance 'EAT' position has 3 dims but substrate requires 2`.
  - Shipped `configs/static_epistemic_access` at `num_agents=61`: `RUNTIME ValueError: Affordance 'SLEEP' requires explicit position when randomize_affordances is disabled`. This is N1d reached through the back door.
- **Root cause:** the fallback's capacity test sums `num_agents` across independent worlds, as if they shared one grid (under S1 each world holds one agent), and then silently flips to configured positions.
- **Fix shapes:** check fixed positions whatever `randomize_affordances` says (cheap, and it keeps the `type: random` skip), or delete the fallback (the principled fix under S1).

### D3 P2: a meter rule before `clamp_and_validate` lets an out-of-bounds meter drive the cascades in the same tick
- **What happens:** the new meter-rule commit path (`vfs/transition_schedule.py:174-187`) leaves the meter unclamped until `clamp_and_validate`, which is what the docs promise. But `VTCThresholdCascadeProgram.apply` reads the source bar raw (`vfs/vtc.py:~1176-1179`). So a rule at `apply_passive_depletion` that overshoots changes this tick's cascade magnitude.
- **Repro:** `probes/meters/m_oob.py`, rule `bar.satiation += -5.0` at `apply_passive_depletion` with `clamp: null`, 1 step:

  | setup | satiation | Δhealth | Δenergy |
  |---|---|---|---|
  | this rule | 0.0 after clamp | **-0.0624** | **-0.0962** |
  | same rule with `clamp: [0,1]`, or an overwrite to 0.0 | 0.0 | -0.0090 | -0.0160 |

  The same rule at `ingest_actions` does not leak, because the passive-depletion program clamps.
- **Second repro** (`probes/meters/m_oob2.py`): a rule at `apply_threshold_cascades` sets `bar.satiation += -5`, and a later rule at `apply_transition_rules` adds `bar.satiation*0.01` to mood. Δmood is -0.04408 without a clamp and -0.00400 with `clamp [0,1]`. I did not probe the effects path (`effects.tick`), but it reads the same bars.
- **Why it matters:** action writes cannot reach that phase, so meter rules opened this exposure.
- **Fix shape:** the depletion and cascade programs clamp each write to the meter's declared bounds (`_required_clamp`). Either clamp a `bar.` rule target to its declared bounds at commit, or document the in-tick leak.
- **Doc gap:** "the meter is then held to its declared bounds at clamp_and_validate" (`variables.md:276-282`, `transition_rules.md:64-66`) does not mention the in-tick leak.

### D4 P2: a substrate-constructor refusal still escapes uncoded and unlocated, in stage 3
- **What happens:** continuous `interaction_radius` larger than a bound's span raises `ValueError` at `substrate/continuous.py:79`; `continuousnd.py:99` has the same check. The path is `universe/validation/semantics.py:327` → `SubstrateActionValidator` → `SubstrateFactory.build`. It is not stage 7, so the new wrapper never sees it.
- **Result:** the compiler raises `BARE ValueError`, and the CLI reports `[UNCLASSIFIED_REFUSAL] <pack>:1` with exit 1.
- **Repro:** `rp.py configs/test/action_space/continuous1d <lvl> w stratum.yaml "interaction_radius: 1.0" "interaction_radius: 20.0"`.
- **Status:** this is the original N2 class. The rank rules moved to the DTOs, but this rule did not.

### P3s
- **Rank DTO bound versus the real cap.** The DTO messages say gridnd and continuousnd "has 4 to 100" dimensions (`config/stratum_config.py:66-69, 82-87, 118-122`). The token spec caps rank at `MAX_POSITION_RANK=8`, so ranks 9-100 pass the DTO and refuse with `[TOKEN-SPEC] @stratum.yaml:1`. The DTO advertises a range that never compiles.
- **`_record_sources` reorder: 2 of 22 sampled refusals now point one line up, at the parent key.** These DAC and clock lookups locate the parent mapping key, not the leaf. They were exact at 559dd0f9 only because the offending field happened to be the first child, so this is a key-granularity nit, not a regression in the recorder:
  - `DAC-REF-001`, modifier `bar: nosuch`: `drive.yaml:5` becomes `:4` (`energy_crisis:`).
  - `CLOCK_REFERENCE`, `period_of: nosuch`: `L3/curriculum.yaml:13` becomes `:12` (`day_length:`).
  - Three moved to a neutral or better key (opening_hours, bounds, normalization). The other 17 are unchanged. Script: `probes/loc_cmp.sh`, `loc_cmp2.sh`.
- **`effects_hash` is order-sensitive in merged fragments.** Moving `food_decay` into `aa_more_effects.yaml` moves it, because the sorted-path merge order changes; moving it into `zz_*.yaml` does not. A literal `1.0` becoming `1` also moves it. Definition order is not semantic: the catalog sorts effect ids (`effects/catalog.py:76`), and token encoding uses that sorted order. So the order move is a false move. Int against float is a type difference in the DSL. Script: `probes/hashes/h_matrix.py`.
- **Stale docstring.** `training/checkpoint_utils.py:473-476` (`assert_checkpoint_identity`) still says "four per-level content hashes" and "six pack-scope content hashes".
- **Known gap, confirmed.** `lifetime: persistent` compiles on `effect_ref` and `affordance_ref`, in agent and global scope. `item_ref` refuses.
- **Undocumented same-phase order.** In one phase, action writes commit before rules, and a rule reads the action's result (rule overwrite 0.2 beats action overwrite 0.5; `bar.satiation*0.5` after an action set of 0.5 gives 0.25). The variables.md snapshot paragraph says rules and action writes read their phase-entry snapshots "separately". It never states the order.
- **Doc sweep (fork, `probes/docs_sweep.py`, log `work/docs_sweep.log`).** Every A1/A5 block named in the commit now loads and steps. Leftovers:
  - `variables.md:370` `time_since_last_sleep` is presented as "one declaration" but lacks required fields.
  - `expressions.md:980` is not valid YAML.
  - VFS.md:1754/1772/2044/2567 read undeclared names and are not marked illustrative.
  - `expressions.md:585/785` still name a `duration` effect local, and `:729/:1066` still call DAC "(future)".
- **Latent.** `LEVEL-COMPILE-REFUSED` is located at a directory (`levels/<name>:1`), not a file. I found no reachable trigger. `__main__.py:215` uses `assert` for a runtime invariant.

## AREAS

### 1. Original repros: HOLDS
Every original repro now refuses with a code and file:line, or runs correctly. D1 and D4 are new variants in the N6 and N2 classes; they are reported under areas 4 and 3.
- **Compiler lens:**
  - N1a: `[LOAD_ERROR] actions.yaml:9`.
  - N1b: `[ITEM-ARENA-PROFILE-MISSING] items.yaml:5`.
  - N1c: `[AFFORDANCE-POSITION-SUBSTRATE] affordances.yaml:11`.
  - N1d: `[AFFORDANCE-POSITION-REQUIRED]` at each `type: random` line (11/35/54/76).
  - Out-of-bounds `[99,2]`: `[AFFORDANCE-POSITION-SUBSTRATE] :11`.
  - N2: `[LOAD_ERROR] stratum.yaml:7` for gridnd 1 and 3, and `stratum.yaml:3` for continuous 4.
  - N3: `[ACTION-NAME-RESERVED] actions.yaml:9`.
  - N4: `[LOAD_ERROR] stratum.yaml:5` (finite bounds).
  - gate_e2e: effect body edit refused on `effects_hash`, appearance edit on `items_appearance_hash`, control edit on `items_hash`.
  - N6: `true`/`false`/`and`/'a b'/`1x`/`x-y`/`énergie`/`bar.energy`/`item.x` refuse at the declaration. `True` and `abs` compile and are read as variables, which is correct.
  - N10: duplicate custom action gives `DECLARATION_COLLISION` with both origins; `.YAML`/`.Yml` and `levels/x.yaml` give `DECLARATION_SCOPE`; dotfiles, dot dirs (pack, levels/, inside a level, `.git`) and an emacs lock symlink are ignored; a cache write failure gives `[CACHE_WRITE_FAILED]` with exit 1; inspect against a mismatched level gives `[ARTIFACT_LOAD_REFUSED]` with exit 1.
- **Authoring lens:**
  - r1: energy 0.985. r2: mood 0.986.
  - m1: night decay. m13: dies at tick 4, the tick doom reaches 3.
  - m10: `[AFFORDANCE_OPENING_HOURS_DAY_PERIOD] affordances.yaml:9`.
  - d_docs is re-keyed by content (fork); all A1/A5 checks hold.
- **Runtime lens:**
  - a2 `not item.flag`: runs.
  - w1: every per-row read into vec/tensor refuses with `[VTC-WRITE-TYPE]` in both programs; literals run.
  - w2 and c3: clamp on bool and on refs refuses.
  - w5: the documented one-tick lag at `evaluate_terminal_conditions` remains.
  - m3: persistent `item_ref` refuses `[LOAD_ERROR]`.

### 2. Rules on meters: HOLDS, except D3
- **Night hunger** (`probes/meters/m_rules.py a`, 4 worlds, 60 steps): exact float32 match to the hand model `s -= 0.008; if night(k): s -= 0.05; clamp`, with max abs error 0.0. The rule at instant k reads `is_night(k)`, as the clock contract says.
- **Dead world:** satiation is frozen after death and the live worlds keep moving.
- **Priority:** in the same phase the action write commits first and the rule overrides or composes on top.
- **Bounds and clamps:**
  - +0.5 clamps to 1.0.
  - overwrite 7 with rule clamp [0,5] at `clamp_and_validate` gives 1.0.
  - rule clamp [0,0.3] gives 0.3.
  - money 2e6 gives 999999.
  - min/max/multiplicative/priority_write/clamp compositions behave correctly.
  - `claim_if_free` on a meter refuses at the DTO.
- **Lethal:** a rule zeroing health ends the episode that tick at each of six phases. Additive -1.5 clamps to 0 and is lethal. A per-world kill (`agent_id == 1`) ends world 1 only.
- **Every phase:** 13 phases give exactly control minus 0.1. `evaluate_terminal_conditions` refuses `[UAC-STATIC-WRITE] transition_rules.yaml:3`.
- **Differential** (`m_diff.py`): world 0 perturbed against unperturbed at N=4 and N=5 over 64 steps, with meter rules at four phases plus agent and global VFS writes. Worlds 1..N-1 show no divergence.

### 3. New refusals: HOLDS
- **Vector targets** (`probes/refusals/r_vec.py`, all 10 types × action/rule × 13 expressions, 224 cases):
  - Constants run: a literal, `1.0+2.0`, `where(true,..)`, `if true then..`, `max(1.0,2.0)`, an inlined constant expression var (`kconst`, `kconst2 = kconst+1`).
  - Per-row reads refuse with `[VTC-WRITE-TYPE]` (element-payload): `av`, `gv`, `tick`, `agent_id`, `bar.energy`, `where(ib,..)`.
  - Int types refuse float reads on type.
  - A global vec2f target behaves the same.
  - No runtime errors.
- **Clamp** (`r_clamp.py`): bool and all four ref types refuse in both programs, as do `composition: clamp` on a bool and a global bool. `clamp: null` runs.
- **Persistent refs:** `item_ref` refuses; `effect_ref` and `affordance_ref` compile (known gap, confirmed).
- **Item-state cast** (`r_items.py`): bool and all ref types in item profiles, with null initial values. `not`, `and`, `or`, `==`, `!=`, `where`, `switch`, a mixed `bar.energy > 0.5 and not item.flag`, and ref reads and writes all compile and step with correct results.

### 4. Compiler refusals: FAILS (D2, D4)
- **Positions:** see D2.
- **Ranks** (all refusals located):
  - gridnd: 3 refuses at the DTO; 4 and 8 compile; 9, 13 and 100 refuse `[TOKEN-SPEC] stratum.yaml:1`; 101 refuses at the DTO.
  - continuous: 1-3 compile; 4 refuses at the DTO.
  - continuousnd: 3 refuses at the DTO; 4 and 8 compile; 9 and 100 hit TOKEN-SPEC; 101 refuses at the DTO.
- **Action-name reservation** (`probes/actnames.py`): every substrate movement name on grid2d (diagonals on and off), grid3d, gridnd, continuous 1D/2D/3D, continuousnd and aspatial, plus INTERACT, refuses `[ACTION-NAME-RESERVED] actions.yaml:<line>`.
  - GET, USE_SLOT_n and DROP_SLOT_n refuse only where items exist; `USE_SLOT_9` beyond the slot count is admitted.
  - WAIT is admitted as a custom action on grid2d, continuous and aspatial, and refused on gridnd and continuousnd, where it is a substrate action.
- **Identifiers:** `_x`, `x_`, `X1`, `__`, `x1_y2`, `True` and `NOT` compile and read correctly; unicode refuses, and so does each of the 8 parser keywords. Keyword prefixes are D1.

### 5. effects_hash and items_appearance_hash: HOLDS (P3 false moves)
- **Semantic edits move the right hash** (`probes/hashes/h_matrix.py`):
  - `effects_hash`: effect body, operator, duration, reapply_policy, observable, budget, scope, nested `spawn_effect` intensity, id rename, definition order.
  - `items_appearance_hash`: spawn_count, period, schedule type, placement, `when`, max_total, rule order.
- **Null edits that do not move:** comments, respacing, redundant parens, quoting, key reorder, budget key reorder, flow list, file move, and a split that keeps the merge order.
- **Checkpoint identity** (`h_ckpt.py`):
  - A missing key refuses by name.
  - None against a digest refuses for both hashes.
  - Format 7 refuses in `assert_checkpoint_identity` and in `validate_demo_checkpoint_payload`.
  - A 1.39 artifact makes the cache path recompile (rewritten to 1.40); `from_dict(1.39)` refuses; a 1.40 artifact without `effects_hash` refuses.

### 6. Opening-hours day period: HOLDS
- Period 24 compiles.
- Periods 48 and 12 refuse at each `opening_hours:` line (L3 lines 9, 59, 287).
- A literal day_length of 48 with no clock variable refuses; 24 compiles.
- L1 (inactive) with period 48 and EAT hours enabled compiles, and `_is_affordance_open` is True on all 30 ticks; `enable_temporal_mechanics` is False, so the gate never runs.

### 7. Discovery changes: HOLDS (P3 location regressions)
- See area 1, N10.
- Locations sampled across stages 1, 3, 5 and 6, DAC and clock: 22 refusals at 559dd0f9 against 39825727. Two got worse, which are listed in the P3s.

### 8. Behaviour preservation: HOLDS
- The fork ran `probes/diff8/` with N=4, 64 steps, the same seed and a scripted action sequence.
- Packs: default_curriculum L1 and L3, reference/model_pack L0_demo, items_smoke, effects_smoke, trial_k_cold L0_cold, trial002 L0_simple.
- Obs, reward, dones, meters, positions, every registry variable and `item_vfs` are bitwise identical at every tick. Action-name lists are equal.
- Limit: no shipped pack has a meter rule, so these traces do not exercise the new path. Area 2 covers it.

### 9. Gates in the worktree: HOLDS
- `CUDA_VISIBLE_DEVICES= uv run pytest tests -q --no-cov -p no:cacheprovider`: `5415 passed, 17 skipped, 1 deselected, 15 warnings in 1052.04s`, EXIT 0.
- `no_defaults_lint --ratchet`: `No defaults detected. Clean. (618 violation(s) whitelisted) Ratchet: 618 ... at the ceiling.`
- ruff, black (648 unchanged), mypy (179 files, success), `validate_compiler_cli.py` and `gen_expression_functions_doc.py --check`: all clean.
- `token_type_schema_hash` (`probes/tts_hash.py`, every level of every pack, fresh copy, no cache): 33 of 36 levels compile at both SHAs, the same set, all `de093a6e9f59924e`. The other 3 are the same refusal fixtures at both SHAs.
