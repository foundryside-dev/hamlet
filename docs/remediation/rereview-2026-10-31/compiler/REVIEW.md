# Re-review, lens `compiler` (universe compiler as a product) at 559dd0f9

Worktree: `scratchpad/rereview/compiler/wt` (detached at 559dd0f9, `uv sync --extra dev --extra recording`). Probes: `rereview/compiler/probes/`. Scratch packs: `rereview/compiler/packs/`. /home/john/hamlet untouched.
`R` below means `wt/.venv/bin/python probes/repro.py <src-pack> <level> <work-dir> <file> <old> <new>`, run from `wt/`. It copies the pack, applies the literal edit, compiles with `use_cache=False`, builds a 2-world CPU env and steps it.

## Gate (all at 559dd0f9, in the worktree)
- `CUDA_VISIBLE_DEVICES= uv run pytest tests -q --no-cov -p no:cacheprovider` -> `=== 5317 passed, 17 skipped, 1 deselected, 15 warnings in 1057.07s (0:17:37) ===`, EXIT 0
- `ruff check .` -> `All checks passed!` (exit 0)
- `black --check src tests scripts` -> `645 files would be left unchanged.` (exit 0)
- `mypy src/townlet` -> `Success: no issues found in 179 source files` (exit 0)
- `no_defaults_lint.py ... --ratchet` -> `No defaults detected. Clean.` / `(618 violation(s) whitelisted)` / `Ratchet: 618 whitelisted violation(s), at the ceiling.` (exit 0)
- `scripts/validate_compiler_cli.py` -> `✅ Universe compiler CLI validation passed` (exit 0)
- `scripts/gen_expression_functions_doc.py --check` -> `docs/config-schemas/expressions.md is current (49 functions)` (exit 0)

## VERDICT: NOT GREEN
There are seven P2 items, listed below as N1 to N7. N4 could be argued up to P1.

## New findings (most severe first)

### N1 P2: the compile accepts packs that the runtime refuses at env construction (four shapes)
Each of these compiles cleanly, then `create_environment` raises.
- a. A custom action named `''`. `config/actions_config.py:45` `name: str` has no `min_length`, but the runtime `ActionConfig` has one. Crash at `environment/vectorized_env.py:520` -> pydantic `main.py:263` ValidationError. Repro: `R configs/static_epistemic_access L0_simple w actions.yaml "  - name: ADVANCE" "  - name: ''"` (also `probes/emptyname.py`). The fuzzer found it independently in two packs.
- b. An item arena above zero with `variables.item_profiles: []`. Crash at `vfs/registry.py:697`, "Item VFS requested (max_items>0) but no item_profiles were provided." Repro: `R configs/static_epistemic_access L0_simple w items.yaml "max_items_in_world: 0" "max_items_in_world: 1"`. The fuzzer hit it six times across three packs.
- c. An affordance fixed-position rank that differs from the substrate's. Crash at `vectorized_env.py:478`. Repro: `R configs/test/effects_smoke L0_effects w levels/L0_effects/affordances.yaml "      - - 2\n        - 2" "      - - 2\n        - 2\n        - 2"`.
- d. `randomize_affordances: false` with `deployment.type: random`. Crash at `vectorized_env.py:458`. Repro: `R configs/static_epistemic_access L0_simple w levels/L0_simple/training.yaml "randomize_affordances: true" "randomize_affordances: false"`. This overlaps the known UaC follow-up about fixed positions.
- Related: a fixed position out of bounds, e.g. `[99, 2]` on a 5×5 grid, is accepted silently. The affordance is placed at `[99, 2]` and can never be reached (`probes/pos99.py`).
- Cause: `compilers/optimization.py:117` sets every `affordance_position_map` entry to `None`. Positions are only validated at runtime in `vectorized_env._position_to_tensor`.

### N2 P2: substrate-construction refusals escape the compiler as bare `ValueError`
These carry no code and no file:line. The CLI turns them into `UNCLASSIFIED_REFUSAL <pack>:1`.
- `gridnd.dimension_sizes: [5]` or `[5,5,5]` -> `substrate/gridnd.py:62`.
- `type: continuousnd` with 1 dimension -> `substrate/continuousnd.py:73`.
- `type: continuous` with `dimensions: 4` -> `substrate/factory.py:118`.
- The DTOs (`config/stratum_config.py:56-72, 98-131`) do not encode these rank rules. Stage 7 (`compiler.py:400`, inside `build_action_space_metadata`) does not wrap substrate-factory errors.
- Repro: `R configs/test/gridnd_4d_pack L0_test w stratum.yaml "dimension_sizes: [5, 5, 5, 5]" "dimension_sizes: [5]"`.

### N3 P2: a custom action named after a substrate action is silently dropped, along with its writes
- Where: `compilers/actions.py:111` `if custom.name in substrate_names: continue`.
- Rename ADVANCE (which has two writes) to `UP` in static_epistemic_access. It compiles. `UP` is the substrate movement action with `writes: ()`, `action_write_program: []`, and `public_state` stays at 0 after three `UP` steps (`probes/upwrites.py`).
- `INTERACT` is refused, but only as a bare `ValueError` with no code or location (`compilers/actions.py:110`). `GET`, `USE_SLOT_n` and `DROP_SLOT_n` are refused the same way (N2 class).

### N4 P2 (arguably P1): continuous `bounds: [-.inf, .inf]` compiles and every position and observation is NaN
- Repro: `R configs/test/action_space/continuous1d <level> w stratum.yaml "- [0.0, 10.0]" "- [-.inf, .inf]"`. After reset, `env.positions` is `[[nan],[nan]]` and `isnan(obs).any()` is True.
- `ContinuousConfig.bounds: list[tuple[float, float]]` (`config/stratum_config.py:102`) needs finite values (`allow_inf_nan=False`).
- It is silent corruption reachable from an authored pack, so it can be argued P1. It sits in the authoring DTO, but the strata phase may also own it.

### N5 P2: effect dynamics and level `items_appearance` are outside every checkpoint-gated hash
- `probes/gate_e2e.py` stamps a checkpoint from items_smoke with `attach_universe_metadata`, then runs `assert_checkpoint_identity`:
  - effect `wear_and_tear` changed from `1.0*intensity` to `50.0*intensity` -> **ACCEPTED**;
  - appearance changed to apple `spawn_count 3->9` and `period 100->5` -> **ACCEPTED**;
  - control: an item `on_use` edit -> refused on `items_hash`.
- `probes/hash_matrix_items.py`: effect body edits, `spawn_count`, `period` and a coin `spawn_count 0->2` move only `config_hash`. Effect `duration` moves `observation_schema_hash` and `vfs_hash`, through the token payload only.
- None of the six pack hashes covers the `effects` family, and no level hash covers `items_appearance` (`compiler.py:225-235, 511-515`).
- The README (`README.md:306-311`) lists only the hashes that exist, so this is a coverage gap, not a broken claim. It has the same shape as original F2/C2, which was rated P1 ("silent acceptance"). The fix is cheap: hash movement is free.

### N6 P2: the literals `true` and `false` can be declared as variable ids, and expressions read the literal, not the variable
- Declare a global bool `true` (initial `false`) and `probe: 'if true then 7.0 else 3.0'`. It compiles, the AST holds `Constant True`, and after a step the registry has `true=[False,False]` but `probe=[7.,7.]`.
- `RESERVED_NAMES` (`world/expression/references.py`) covers engine names but not literals.
- In the same family, ids that can never be referenced are declarable: `'a b'`, `1x`, `x-y`, `énergie`, `and`. `VariableDeclaration.id` is `str` with only `min_length=1` (`config/variables_config.py:45`). The refusal only comes at the first expression that uses the id, and it is a misleading parse error such as "found '+'" for `énergie` (`probes/varid.py`). Literals that silently shadow are P2. Unreferenceable ids are P3.

### N7 P3 (limit gap): `max_active_effects` has no upper bound
- `effects.yaml` `item: 1000000` in items_smoke -> compiled in 21.6 s, `total_dims=78,000,162`, 3.86 GB RSS (`probes/huge.py`). A runtime env at that width would OOM.
- Every other capacity has a `MAX_*` in `validation/limits.py`, or `le=` in its DTO (`max_items_in_world le=1000`).

### N8 P3: artifact bytes are not deterministic across processes
- Only two things differ:
  - `metadata.compiled_at`, which is inherent, so byte identity can never hold;
  - `vfs_evaluation_marks` serialized as `list(set)` unsorted (`compiled.py:~410`), so the order follows PYTHONHASHSEED. Repro: L5_multi_agent and vfs_dependency_chain across seeds 1-6 (`probes/det.py`, `detcmp.py`).
- The runtime consumes the marks as a set, so there is no behavioural effect. Use `sorted(v)`.

### N9 P3: hash false moves (classifying the known text-vs-AST follow-up)
- `affordances_hash` moves when an `on_start` value is respaced (`bar.energy + 0.8` vs `bar.energy+0.8`) and when a `costs` mapping is reordered. `items_hash` moves when a hook value is respaced.
- Cause: the `_compute_pydantic_hash` text dump (`compiler.py:636-642`) hashes source text and keeps dict insertion order.
- `initial_value 2.0 -> 2` still moves `variables_hash`, `variable_schema_hash` and `vfs_hash`.
- Classification: P3. These are false moves only: no semantic edit failed to move, and hash movement is free. A false move only causes an unneeded resume refusal.
- Null edits that correctly do not move: comments, key reorder inside a variable, flow vs block lists, role-list order, expression respacing and parens (variables, rules), splitting or moving variable fragments, `drive.yaml -> mechanics/rewards.yml`, multi-document merge, and rule `clamp [0.0,4.0] -> [0,4]`.

### N10 P3: missing codes and smaller diagnostics
- `symbol_table.py:36-70` (seven duplicate-* sites) and `compiler.py:627` (cache write) raise `CompilationError` with `code=None`. A duplicate custom action is located (`actions.yaml:9`) but uncoded. `custom_actions` is not in `_is_named_collection` (`declarations.py`), so discovery never reports both origins.
- `.YAML` and `.YML` uppercase files are silently ignored by discovery and by `config_hash` (`declarations.py:75`, `suffix in {".yaml",".yml"}`). A bogus `extra.YAML` compiles.
- A file directly at `levels/x.yaml` is treated as pack scope. `declarations.md:15` covers only "outside levels/" and "under levels/<id>/".
- Emacs lock files (`.#bars.yaml`, a broken symlink) make every compile refuse with `DECLARATION_SCOPE`.
- `inspect <artifact> --primary-level OTHER` exits 0. It does print a STALE warning that names the mismatch.
- The provenance digest covers townlet `.py` files plus python, torch and pydantic versions. Other dependencies (pyyaml, msgpack, numpy) are not covered.
- On load, `delay_commands` comes back as `[]` vs `None` and `torch_version` as `str` vs `TorchVersion`. Every reader uses `or []`, so this is harmless.

## What held (evidence)
- **Round trip.** For 10 packs or levels (default_curriculum L2 and L3, items_smoke, effects_smoke, aspatial_test, gridnd_4d, L5_multi_agent, SEA, trial_k_cold, token_set_smoke L1_attention), a cache-served `compile()` deep-equals the fresh one at every field, except the two benign type differences under N10. A 3-agent, 40-step env trace (obs, reward, done) is bitwise equal from fresh and cache-loaded artifacts (`probes/roundtrip.py`).
- **Cache.** Discovery runs before the cache fast-path, so an added empty level directory refuses on both paths. Path, content and provenance changes are detected, and so is an mtime-only edit. An uppercase `.YAML` file is ignored by both paths (N10).
- **CLI.** No traceback in 14 cases: missing dir, unknown level, inspect without a level, missing artifact, garbage msgpack, a stale artifact (exit 0 plus a STALE warning, including through the artifact path), a duplicate declaration, non-UTF-8 bytes (`YAML_SYNTAX_ERROR`), an unreadable file (`UNCLASSIFIED_REFUSAL`), and a broken symlink. Exit codes are right. `inspect` reports freshness and emits `token_rows`.
- **Fuzzing.** About 2,250 mutated packs across 6 bases (`probes/fuzz.py` with 750 type-breaking mutations, `fuzz2.py` with 1,500 type-preserving ones; logs in `fuzz_*.log`). Results: 833 compiled and stepped 4 ticks, the rest refused, 1 BARE (N2), 2 UNLOCATED (both the duplicate-action case, N10) and 10 RUNTIME (all N1 shapes). No KeyError, AttributeError or TypeError escaped a stage.
- **Discovery scope.** `stratum` at level scope and `bars` at pack scope are both refused with `DECLARATION_SCOPE` at file:line. A duplicate drive in a nested `sub/d.yaml` gives `DECLARATION_COLLISION` with both origins. YAML merge-key and anchor misuse is refused with a location.

## Known-item classification
- PHASEA "`initial_value: 2` vs `2.0` false move": P3, still open (confirmed in N9).
- PHASEA "`from_dict` ignores unknown keys": P3, still open (`to_dict()` plus a bogus top-level key and a bogus level key -> accepted).
- PHASEA "items_hash / affordances_hash hash source text": P3, still open (N9).
- PHASEA "deployment.type fixed positions ignored": UaC, reproduced as N1d (crash at env build). It belongs to UaC, and the compile-side check is part of N1.
- PHASEA "identity: effects with identical payload alias": design or owner decision. P3 for this lens.
- PHASEA "VF F9 lag + order-free hash": closed. The `canonical_expression_schema` docstring reasons it through, and the dependency set rather than the order is hashed.
- B4 "VFS profile refusals located at variables.yaml:1": closed. A type-mismatched expression is refused at `variables.yaml:55`, the `- id: scaled_public` line.
- RESULTS_repair P1 "switch with non-empty case/default body crashes": closed. An effect `switch` with a `cases[0].do` and a `default` body compiles and steps 6 ticks.
- RESULTS_repair P2 "undeclared vfs_profile unlocated": closed. Refused at `items.yaml:22`, naming the declared profiles.
- PHASEA "`ActionSpaceBuilder.get_enabled_actions` zero callers" and "stale docstrings": P3, not re-checked.

## Original-review closure (compiler lens)
| id | status | evidence |
|---|---|---|
| C1 items_appearance not serialized | CLOSED | `compiled.py:454/557`; items_smoke cache-load deep-equal; env traces equal |
| C2 pack hashes stamped, never compared | CLOSED | `checkpoint_utils.py:60-76, 357` `PACK_HASH_KEYS`; item `on_use` edit refused on `items_hash`. Sibling gap: N5 |
| C3 catalog nullified at arena 0 | CLOSED | `raw_configs_v21.py:180` nullifies only when there are no item types and both arena sizes are 0; `per_agent: 0, world: 10` compiles and spawns 8 items over 2 worlds |
| C4 dead required DTO fields | CLOSED except the DAC seam | `curriculum_levels`, cues, category, evaluation/checkpointing: 0 hits; `capability_config.py` deleted. `IntrinsicConfig.rnd_config/icm_config/count_config/adaptive_config` remain (`drive_as_code.py:241-244`), P3, DAC seam |
| C5 RecordingConfig extra=allow | CLOSED | no `extra="allow"` in `src/townlet` |
| C6 metadata.py "money" branch | CLOSED | no money/cost/critical in `compilers/metadata.py` |
| C7 presentation filename reader | CLOSED | `_resolve_presentation` (`compiler.py:279`); the artifact carries presentation; no `presentation.yaml` reader in src |
| C8 no discriminator for identical variables | SUPERSEDED | S3 ruling: the identity check is gated on the brain (CLAUDE.md) |
| C9 inspect JSON lacks layout | CLOSED | `__main__.py` `_token_layout_payload` gives `token_rows` with `filler_ref` and offsets |
| C10 CLI tracebacks | CLOSED | `ValueError`/`OSError` go to `UNCLASSIFIED_REFUSAL`; 0 tracebacks in 14 cases. Residual: N2 lands there unlocated |
| C11 cache path- and cwd-blind, inspect not fresh | CLOSED | `experiment_dir` and source digest in provenance (`compiler.py:676-723`); git sha from the package root; inspect reports freshness |
| C12 effects DTO defaults | OPEN P3 | `effects_config.py:125, 130, 137, 154` (`intensity`, `quantity`, `else_`, `delay_do` defaults) remain. They are structural |
| C13 residue | CLOSED | `EFFECT_OBSERVATION_SLOTS`, `vfs_profiles_smoke`, `validate_substrate_configs.py` and the seven dead whitelist files are all gone |
| C14 wall-clock asserts in the default selection | CLOSED | `perf` marker, excluded by default (`pyproject.toml:131`) |

## Not covered
GPU paths. Perf tests (excluded). Any training run. Checkpoint save and load beyond `assert_checkpoint_identity`. `MAX_CACHE_FILE_SIZE` overflow. Symlinks inside the pack beyond the broken-link case. YAML bombs. Concurrent compiles writing the same `.compiled`. Other dependency-version drift. `compile` against a read-only pack directory. Multi-level packs where non-primary levels differ structurally (meter vocabulary is enforced equal, so not reachable). The `docs/architecture/COMPILER.md` text against source, beyond grep.
