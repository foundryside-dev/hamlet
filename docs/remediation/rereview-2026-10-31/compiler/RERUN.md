# Green-call rerun, lens `compiler`, at f3a6d115

Worktree: `scratchpad/rereview/compiler/wt2` (detached at f3a6d115). I pointed the same probes from the first pass (`rereview/compiler/probes/`) at it. Scratch packs are in `packs/*2*`. /home/john/hamlet was not touched.
`R` means `probes/repro.py <pack> <level> <work> <file> <old> <new>`. It compiles with `use_cache=False`, builds a 2-world CPU env and steps it 6 ticks.

## Gate
- pytest: `=== 5523 passed, 15 skipped, 1 deselected, 13 warnings in 1128.12s (0:18:48) ===`, EXIT 0
- `ruff check .` -> `All checks passed!` (exit 0)
- `black --check src tests scripts` -> `654 files would be left unchanged.` (exit 0)
- `mypy src/townlet` -> `Success: no issues found in 180 source files` (exit 0)
- `no_defaults_lint ... --ratchet` -> `No defaults detected. Clean.` / `(617 violation(s) whitelisted)` / `Ratchet: 617 whitelisted violation(s), at the ceiling.` (exit 0)
- `validate_compiler_cli.py` -> `✅ Universe compiler CLI validation passed` (exit 0)
- `gen_expression_functions_doc.py --check` -> `docs/config-schemas/expressions.md is current (48 functions)` (exit 0). It was 49 at 559dd0f9: `elapsed_ticks` was removed, which is the B4 "one history-operator list" follow-up. Not a regression.
- token_type_schema_hash (`probes/tts_all.py`, every level of every pack under `configs/`): **33 compilable levels, all `de093a6e9f59924e`**. The 3 that refuse are the negative fixtures (`vfs_circular_dependency`, `vfs_type_mismatch`, `vfs_undefined_var`), each with `VFS-PROFILE-COMPILE`. `total_dims` ranges from 19 to 474.

## VERDICT: NOT GREEN (narrowly)
Every finding from the first pass (N1–N6) holds. Two new P2s remain under the bar's wording "compile accepts what the runtime can't serve". Both have one-line DTO fixes:
- **R1**: `experiment_name: ''` compiles, then env construction refuses. This is pre-existing (identical at 559dd0f9); my first fuzz missed it.
- **R2**: continuous `bounds` that are finite but outside the float32 range compile, then crash at the first step.

If the coordinator rules R2 too contrived to count, R1 alone still blocks under the bar as written.

## New findings
### R1 P2 (by precedent: N1a's shape, which was ruled P2 and fixed): an empty `experiment.experiment_name` compiles, then env construction raises
- `config/experiment_config.py:33`: `experiment_name: str` has no `min_length`. The runtime refuses at `environment/vectorized_env.py:172` ("Missing mandatory experiment_name").
- Repro: `R configs/static_epistemic_access L0_simple w experiment.yaml "experiment_name: Static Epistemic Access" "experiment_name: ''"` -> `COMPILED`, then `RUNTIME ValueError @vectorized_env.py:172`.
- Found by the fresh-seed fuzz runs 33, 35 and 36 (5 hits). Same class as the old N1a.

### R2 P2 (contrived): continuous bounds beyond float32 compile and crash at step
- `bounds: [[0.0, 1.0e39]]` (also `[-1e308, 1e308]`) -> `COMPILED`, then `RuntimeError @substrate/continuous.py:164: value cannot be converted to type float without overflow`.
- `[0, 1e30]` runs.
- The new finite check in `ContinuousConfig.validate_bounds` admits values the float32 position dtype cannot hold. Bound them by `torch.finfo(float32).max`.

### R3 P3 (UaC route, pre-existing): continuous affordance positions are integers only
- `config/affordances_v2_config.py:81`: `positions: list[list[int]]`. On a continuous substrate, `- - 5.5` is refused with "Input should be a valid integer".
- So an affordance at a non-integer coordinate cannot be authored. It is affordance deployment, so UaC, not VFS or compiler.

### R4 P3: a negative effect budget is located at `effects.yaml:1`, not at the `max_active_effects` line (`LOAD_ERROR`).

## The first-pass findings at f3a6d115
| id | status | evidence |
|---|---|---|
| N1a empty custom action name | CLOSED | `actions.yaml:9 - Invalid actions declaration (custom_actions[1].name): String should have at least 1 character` |
| N1b item arena with no profiles | CLOSED | `ITEM-ARENA-PROFILE-MISSING items.yaml:5` |
| N1c position rank | CLOSED | `affordances.yaml:11 - Affordance 'BED' fixed position [2, 2, 2] has 3 coordinate(s), but the grid substrate has rank 2 (5x5)` |
| N1d random + randomize false | CLOSED | `AFFORDANCE-POSITION-REQUIRED`, one issue per affordance at its own line (11/35/54/76) |
| N1 out-of-bounds or negative position | CLOSED | `[99,2]` and `[-1,2]` refused on grid; gridnd `1x1x1x1` refused per affordance; continuous `[50]`/`[-3]` refused, `[10]` (edge) admitted; aspatial fixed positions refused |
| N2 substrate rank as bare ValueError | CLOSED | gridnd `[5]`/`[5,5,5]`, continuousnd 1-D, continuous 4-D and `interaction_radius` > span are all `LOAD_ERROR stratum.yaml:<line>` from the DTO. 0 BARE in 3,450 fuzz cases |
| N3 custom action shadowing a substrate or engine name | CLOSED | `UP` and `INTERACT` -> `ACTION-NAME-RESERVED actions.yaml:9`; `GET` refused on the items pack; a duplicate `WAIT` gives `DECLARATION_COLLISION` with both origins. `GET`/`USE_SLOT_0` are admitted where no item actions exist (no collision) |
| N4 infinite or NaN bounds | CLOSED | `[-inf, inf]` and `[nan, 10]` refused at `stratum.yaml:5`; `movement_delta: .inf` refused. Residual R2 |
| N5 effects and items_appearance outside identity | CLOSED | `gate_e2e.py`: effect body edit -> REFUSED `effects_hash`; appearance edit -> REFUSED `items_appearance_hash`; control `items_hash` refused |
| N6 literal or non-identifier ids | CLOSED | `true`/`false`/`and`/`a b`/`1x`/`x-y`/`énergie`/`bar.energy`/`item.x` refused with the identifier grammar, item scope included. `kwvar.py`: `True`, `notable`, `true_count`, `false_alarm`, `order`, `iffy`, `thenx`, `elsewhere`, `android`, `not_`, `ifx` declared as global bools: both `if X` and `if not X` read the variable (D1 keyword-prefix repair verified) |
| N7 `max_active_effects` unbounded | OPEN P3 | `item: 1000000` still compiles (21.8 s, 78,000,162 dims, 3.86 GB); negative values now refused |
| N8 artifact bytes vary by process | CLOSED | L5_multi_agent and vfs_dependency_chain over PYTHONHASHSEED 1–4: only `compiled_at` differs |
| N9 hash false moves | OPEN P3 (unchanged) | `affordances_hash` moves on respacing and on `costs` order; `items_hash` on hook respacing; `initial_value 2.0->2` and effect `1.0->1` move by design (canonical AST keeps the constant type) |
| N10 codes and diagnostics | CLOSED except the provenance item | `symbol_table` -> `SYMBOL_DUPLICATE`; cache write -> `CACHE_WRITE_FAILED`; `.YAML` refused (`DECLARATION_SCOPE`, "must use a lowercase .yaml or .yml suffix"); `levels/x.yaml` refused; dotfiles, including `.#bars.yaml`, skipped as documented (`declarations.md:17-19`); `inspect --primary-level OTHER` -> `ARTIFACT_LOAD_REFUSED` exit 1. Still open (P3): provenance ignores pyyaml/msgpack/numpy versions; `delay_commands` None vs `[]` on load |

## Changes that are not regressions
- `inspect --primary-level OTHER` went from exit 0 plus a warning to a coded exit-1 `ARTIFACT_LOAD_REFUSED`.
- The gridnd DTO now says "4 to 8" dimensions, which closes the STATUS P3 about ranks 4–100 vs `MAX_POSITION_RANK=8`.
- Dotfiles are skipped by rule (`declarations.md:17-19`), so the Emacs-lock case now passes.
- Position functions naming an undeployed affordance are refused at compile (design call R4).

## Sweeps rerun
- **Hash null edits and semantic edits.**
  - Run on SEA plus a transition rule (`hash_matrix_sea.py`) and on items_smoke (`hash_matrix_items.py`). `effects_hash` and `items_appearance_hash` were added to the harness.
  - Every semantic edit moves a hash, and the new hashes move on exactly their own families: effect body, duration, reapply policy, observable and budget; spawn count, period, and rule order.
  - Null edits hold: comments, an effect fragment moved to an earlier-sorting file (`effects_hash` sorts by id; the old D-P3 is fixed), an appearance moved to `levels/L0_smoke/sub/spawn.yml`, effect respacing, variable fragment moves, drive rename, multi-document files.
  - The false moves are as listed under N9.
- **Cache round trip.** 11 packs or levels, continuous1d included. A cache-served compile deep-equals the fresh one, apart from `torch_version` str/TorchVersion and `delay_commands` None/`[]`. The 3-agent, 40-step trace is bitwise equal on all 11.
  - Staleness: an added empty level dir or a `README.md`-only level dir is refused on both paths. `.YAML` is refused on both. A key reorder with mtime set back is served (P3, content-equal).
- **Per-world placement.** A 2×2 grid with 4 random affordances -> `GRID_CAPACITY_EXCEEDED`. A 1×5 grid compiles, and runs with `num_agents` 1, 61 and 200 (D2 repair holds).
- **CLI.** 17 cases, 0 tracebacks, exit codes correct. `inspect` reports FRESH, then STALE after an edit, through both the pack dir and the artifact path. A mismatched `--primary-level` is now a coded exit-1 refusal.
- **Fuzzer, same seeds and bases as the first pass.**
  - Bases: items_smoke, SEA, aspatial_test, gridnd_4d and effects_smoke (750 type-breaking + 1,250 type-preserving cases), plus default_curriculum L3 (250).
  - Plus fresh seeds 31–36, 200 each (items_smoke, SEA, continuous1d ×2, gridnd_4d, trial_k_cold).
  - Total 3,450 cases: 1,424 compiled and stepped 4 ticks, and 2,021 refused, every refusal coded and located.
  - 0 BARE and 0 UNLOCATED. The base packs are byte-identical between the two SHAs (`git diff --stat 559dd0f9 f3a6d115` on the six bases is empty), so the same-seed comparison holds. At 559dd0f9 the same seeds gave 1 BARE, 2 UNLOCATED and 10 RUNTIME.
  - 5 RUNTIME, all R1 (`experiment_name: ''`, fresh seeds 33/35/36). The same-seed runs are clean.
- **Not rerun:** the first-pass `marks.py` survey (superseded by N8), and the `unicode`/`varid` cases beyond those listed.

## Not covered
GPU paths. Perf tests. Training runs. Checkpoint save/load beyond `assert_checkpoint_identity`. R3/R4 random-draw determinism and checkpoint version 9 (vfs_runtime lens). YAML bombs. Concurrent cache writers. `MAX_CACHE_FILE_SIZE` overflow.
