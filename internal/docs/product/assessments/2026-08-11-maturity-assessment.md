# Townlet Maturity Assessment — 2026-08-11

> Produced by workflow run `wf_4ca82820-274` (12 agents, 3 macro lenses + 8 subsystem
> assessments + synthesis; ~583 tool calls). Commissioned by `PDR-0002`; dispositions adopted
> in `PDR-0004`. Source-verified throughout; `docs/` treated as untrusted evidence.
> Evidence detail (per-subsystem findings, inert-field lists, authorability gaps) is in the
> run journal: `.claude/projects/.../subagents/workflows/wf_4ca82820-274/journal.jsonl`.


Scope: `src/townlet/` (45,274 LOC Python across 14 packages), `configs/`, `frontend/`, `docs/`.
Evidence basis: three macro sweeps (declared-vs-live field audit, bug-corpus freshness verification, spec/doc truth audit) and eight subsystem assessments, all source-verified. `docs/` treated as untrusted throughout.

---

## 1. Macro verdict

Townlet is a working GPU-native DRL engine with a half-connected declarative front end. The engine half is real: a universe compiles end-to-end (`configs/default_curriculum`, 5 levels, ~1.0s cold, cached warm), emits a frozen provenance-stamped artifact, drives a tick loop whose observation vector is assembled purely by iterating the compiled spec (`observation_encoder.py:24-45`), and trains a feedforward DQN whose network, optimizer, LR schedule, loss and replay configuration are all genuinely read from `brain.yaml` (`network_factory.py:50-69`, `optimizer_factory.py:55-162`, `loss_factory.py:192-204`). Against the thesis, "Universe as Code" is roughly two-thirds delivered — bars, passive depletion, threshold cascades, terminal conditions, affordances, the full DAC reward surface (9 extrinsic strategies, 11 shaping bonuses, all implemented, not stubbed), and the effects/items command language all compile from YAML and demonstrably move numbers at runtime. "Brain as Code" is delivered at layer 1 and declared-only at layer 2. The bug volume is genuinely low for a codebase this size and this neglected; the owner's read is correct.

The single biggest structural issue is not any individual defect: it is that **the declarative surface and the runtime were built by separate passes with no test binding them, and every inert field ships set to its no-op value, so the config lies silently and the author cannot tell.** Across eight subsystems I count ~40 distinct schema fields that validate, are documented, and drive nothing — `composition.normalize`/`clip` (`dac_engine.py:949` composes with no tanh and no clamp), `recovery.natural` (shipped at `0.001` in L1 with zero readers), `replay_buffer.min_size` (two cross-field validators, real gate hardcoded at `vectorized.py:758`), the entire `adversarial:` block present in every shipped level and read by nobody (`curriculum/factory.py:132-137`), the whole recurrent encoder specification (`network_factory.py:99-103` says so in its own docstring), `recording.enabled` (spawns a writer thread and writes zero files), `effects.yaml` `scope:` (`executor.py:222` hardcodes `EffectScope.AGENT`), and `EffectsConfig` lacking `extra="forbid"` such that `configs/reference/model_pack/effects.yaml` silently compiles to an empty catalog. Every one of these survived because there is not a single test in the repository that takes a YAML file, changes a value, and asserts the runtime behaviour changed. That absence is the mechanism, and it is the one thing worth fixing structurally rather than case by case. The single biggest asset is the **compiled-universe pipeline with real provenance**: an 8-stage compiler (`compiler.py:148-221`) that emits a frozen msgpack artifact keyed on config hash + compiler version + git SHA + python/torch/pydantic versions (`compiler.py:655-680`), schema-version-checked on load (`compiled.py:583-587`), with an architectural test that mechanically prevents compilation logic migrating back into the orchestrator. That is a better build cache than most production systems have, and it is the correct spine for "the config is the experiment." Separately from the structural finding — and more urgent than it — two live correctness defects mean artifacts are being corrupted today: the compile cache is not keyed on `primary_level` (`compiler.py:595-598` returns a single `universe.msgpack` per pack), so a checkpoint can carry the wrong level's provenance (`checkpoint_utils.py:34-42`); and the recurrent path trains a memoryless network, because `forward()` never mutates `self.hidden_state` and the training loop never threads it (`networks.py:271-272`, `vectorized.py:777-828`). Fix both before any declarative expansion. Inert config changes what to plan; these two change what to do first.

---

## 2. The disposition table

| Subsystem | Disposition | One-line reason | Keep above all |
|---|---|---|---|
| SG1 universe-compiler | **REPAIR** | Pipeline works and is well-decomposed; one proven silent data bug (cache not keyed on `primary_level`, `compiler.py:595-598`) plus a dead parallel `OptimizationData` path | Provenance composition + cache-fingerprint discipline (`compiler.py:655-680`, `compiled.py:583-587`) |
| SG2 vfs / VTC | **REPAIR** | Runtime state layer is mature and enforced; the flagship authoring surfaces (action writes, `transition_rules.yaml`) have no YAML path — `compilers/actions.py:205` hardcodes `writes=()` | `VTCTransitionRunner` + phase schedule (`transition_schedule.py:35-200`); `schema_hashes.py` in full |
| SG3 config-dto | **REPAIR** | Validation craftsmanship is above codebase average; the failure is the join to runtime, not the schemas | Conditional discriminated unions (`brain_config.py:240-451`), `compute_brain_hash`, `apply_training_overrides` |
| SG4 environment / DAC | **REPAIR** | Most finished subsystem; all 20 DAC strategy types real, but composition inert, custom actions are structural no-ops, and the live interaction path is a weaker duplicate of a dead sibling | Spec-driven `_get_observations` + fail-loud shape guard (`observation_encoder.py:24-45,101-109`) |
| SG5 substrate / world | **REPAIR** | `world/expression` is among the best code in the repo; `substrate/` has the right ABC but ~half its declared config matrix crashes at `env.reset()` | `FUNCTION_SPECS` single-registry design (`functions.py:262-266`); `SpatialSubstrate` ABC |
| SG6 training-stack | **REPAIR** | Feedforward path is declarative end-to-end and works; recurrent path contains a proven silent training-correctness bug and both headline capabilities are unreachable from any shipped config | The three replay buffers (~1,250 LOC) and `checkpoint_utils.attach_universe_metadata` |
| SG7 effects / items | **REPAIR** | Pure-YAML effect chain proven working by execution; ~half the declared surface (scopes, `on_drop`, spawn rules) is inert | `CommandCompiler` type checker + AST baker + compile-time PARALLEL write-conflict detection (`compiler.py:314-352`) |
| SG8 demo / recording / frontend | **REPAIR, with embedded DELETE** | Demo/inference half is live and substrate-agnostic; recording/replay slice is unreachable at three independent points and 9 months stale — delete it; frontend is unbuildable (`frontend/package.json` absent, `.gitignore:94` = `*.json`) | `demo/database.py` in full; substrate-agnostic broadcast (`live_inference.py:911-956`) |

**Downgrades on adversarial review: none.** Every subsystem landed on REPAIR, and in three cases the assessor explicitly argued down from a harsher verdict and recorded why: SG5 and SG6 rejected REBUILD (the architecture is right; specific wires were never connected), SG6 and SG8 rejected RESPEC (a proven correctness bug outranks spec absence — you cannot spec your way out of an LSTM that does not learn). SG8 is the only mixed verdict: REPAIR for demo + frontend, DELETE for `src/townlet/recording/` (~1,150 LOC plus ~2,600 lines of tests constraining code no user can reach). Two further scoped deletions were argued inside REPAIR verdicts: SG1's `OptimizationData` end-to-end, and SG6's dead architectures (`SimpleQNetwork`, `StructuredQNetwork`, `RewardTensor.from_components`, `AdversarialCurriculum.from_yaml`).

Uniform REPAIR is a real signal, not a hedge: no subsystem's *design* was found wrong for the thesis. What is wrong is enumerable in every case, which is REPAIR's definition.

---

## 3. Systemic patterns

Ranked by threat to the authoring thesis.

### P1 — Declared-but-inert config (the defining defect class)

**What it is.** A YAML field exists, validates, is documented, and does not drive runtime behaviour. This is the worst possible failure for a declarative product because the author has no signal. It is worse than an absent feature.

**Where it shows up.** Every subsystem. Highest-consequence instances, all source-verified:

- `drive.composition.normalize` / `.clip` — declared `drive_as_code.py:602-603`, engine reads only the two sibling logging flags (`dac_engine.py:90-91`), composition is `total_reward = extrinsic + intrinsic + shaping_total` (`dac_engine.py:949`), returned unchanged at `:963`. Docs certify it live (`docs/config-schemas/drive_as_code.md:250-251`).
- `bars.meters[].recovery.natural` — required field (`bars_v2_config.py:44-49,91`), **shipped at a non-zero value** (`configs/default_curriculum/levels/L1_full_observability/bars.yaml:28-29`), zero readers outside its own schema file. The sibling `depletion` is fully live via `vtc.py:2354`.
- `training.training_loop.checkpointing.{interval,keep_last}` and `evaluation.*` — required, `gt=0`-validated (`training_v2_config.py:194-220`), configs declare 5000 while the runner uses a hardcoded 100-episode constant. `grep -rn "unlink|rmtree|keep_last" src/townlet scripts/` returns exactly one line: the schema declaration.
- `curriculum.adversarial.*` — the full 8-field block (`training_v2_config.py:235-284`) present in every shipped level's `training.yaml:78-90`, consumed by nothing (`curriculum/factory.py:132-137`).
- `replay_buffer.min_size` — two cross-field validators (`training_v2_config.py:109-123`); real gate is `16 if is_recurrent else batch_size` (`vectorized.py:757-760`). An author setting `min_size: 10000` gets warmup at 32.
- `brain.architecture.recurrent.*` — six required sub-specs under `extra="forbid"`; factory reads exactly `config.lstm.hidden_size` (`network_factory.py:117`) and says so in its own docstring at `:99-103`. `RecurrentSpatialQNetwork` hardcodes the CNN, all three encoders, `num_layers=1` and the Q-head (`networks.py:117-172`).
- `effects.yaml` `scope:` — `executor.py:222` hardcodes `scope=EffectScope.AGENT` with the comment "scope hardcoded to AGENT for now". Item- and affordance-scoped effects additionally never tick, never expire, and leak (`manager.py:367-397`).
- `recording.enabled: true` — spawns a writer thread, logs success, writes zero files, because only the `periodic` criterion is evaluated (`recorder.py:242-263`) and `RecordingCriteria` has zero production callers (`criteria.py:13`).
- `stratum.yaml` `observation_encoding: scaled`, `topology: cubic` + `active_vision: partial`, and `width != height` — all three compile and then **crash** at `env.reset()`; `type: grid3d` has no factory branch at all (`stratum_config.py:167`, `factory.py:152`).

**The corollary that explains the invisibility.** In nearly every case the inert field ships set to its no-op value: every `drive.yaml` sets `normalize: false` / `clip: null`; no config declares `writes:`; all six shipped brains are `type: feedforward`; every level sets `curriculum.strategy: static`. The drift is invisible precisely because nothing exercises it.

**The corollary that makes it worse — validation theater.** The schemas enforce cross-field invariants on fields nothing consumes, which manufactures false confidence. `min_size` gets two model validators; `CNNEncoderConfig` runs positive-value and layer-length-consistency validators on numbers that are discarded (`brain_config.py:58-86`); `curriculum_levels` is required and documented as ordered while ordering actually comes from `sorted(levels_dir.iterdir())` (`raw_configs_v21.py:240-250`). The stricter the validation, the more strongly an author infers the field matters.

**What closing it takes.** Two rules, both mechanical: (a) every schema field must appear at a **non-default** value in at least one config pack, and a test must assert its behavioural effect; (b) any field that fails (a) after one pass gets deleted, not documented. Under the zero-backcompat contract deletion is free. This single pair of rules would have caught roughly 30 of the ~40 instances above.

### P2 — Runtime-first construction with no authoring path

**What it is.** A complete, tested runtime capability whose only inputs are Python literals. Distinct from P1: here the runtime works, and the *config vocabulary* is missing.

**Where.** The VTC action-write ABI is the flagship case: `WriteSpec` is genuinely consumed (`vtc.py:409-441`), with an 11-mode composition dispatch at `vtc.py:523-558`, reaching the environment at `vectorized_env.py:282,492-493` — but `grep -rln "writes:" configs/` is **empty**, `WriteSpec(` is constructed only in `tests/`, and `compilers/actions.py:199-205` hardcodes `reads=(), writes=(), effects={}` for every compiled action. Same shape: the affordance occupancy/capacity-claim engine (`vtc.py:2176-2192`) with no production caller while `configs/L5_multi_agent/variables_reference.yaml:14-23` declares `occupied_by` that nothing writes; `transition_rules.yaml`, the sole VTC authoring file, parses only `social_residue` (`raw_configs_v21.py:217-227`) and appears in zero packs; `capability_config.py:1-112`, a fully-validated six-type module with zero importers repo-wide.

**What closing it takes.** For each declarative subsystem, one end-to-end test that authors the feature in YAML and asserts the behaviour. `tests/test_townlet/integration/test_vtc_transition_schedule_runtime.py` already is exactly this template — it writes a `transition_rules.yaml`, steps the env, asserts a variable moved 0.5→0.6, asserts hashes diverge, and asserts `vectorized_env.py` contains no domain tokens. Replicate that file's shape per surface.

### P3 — Testing tests the schema, never the wiring

**What it is.** The mechanism behind P1 and P2. No test in `tests/test_townlet/unit/config/` or `tests/unit/agent/test_brain_config.py` imports a single runtime consumer — 139 tests assert only that Pydantic accepts/rejects YAML shapes. All 53 DAC tests build the config in Python (`test_dac_engine.py:57-71`), never from a `drive.yaml`. All effects tests hand-build `CommandNode` objects, skipping the parser and compiler. Coverage is inverted in SG8: 96-100% on production-unreachable recording code, 30-33% on the code that runs, zero on the WebSocket protocol that has actually broken 11 ways. And 12k lines of training tests pass while the LSTM does not learn.

**What closing it takes.** A test *category*, not more tests: config-in → observable-behaviour-out, one per declarative surface, using the real compiler and real env.

### P4 — Inertness tracks recency, not quality

The oldest subsystems are fully live: feedforward network construction, VTC passive depletion, VFS access control (`registry.py:512-579` with real `PermissionError` raises and negative tests), dueling/set-encoder builders. The newest layers are declared-only: recurrent brain encoders, `capability_config.py`, items placement/schedule migration, effects scopes. This is a **disposition signal**: the cut line runs along the newest work, not through the codebase. The owner's instinct to keep the good parts is empirically correct.

### P5 — One unabsorbed migration invalidated the entire doc corpus

The v2.1 migration renamed `substrate.yaml`→`stratum.yaml`, `agent.yaml`→`brain.yaml`, `drive_as_code.yaml`→`drive.yaml`, deleted `cascades.yaml`/`cues.yaml`/`global_actions.yaml`, and moved packs under `<experiment>/levels/<level>/`. Source absorbed it completely (`preflight.py:105-149`, `raw_configs_v21.py:200-280`). Docs absorbed none of it — including `CLAUDE.md` and `README.md`, both of which have today's mtime and are wrong about layout, filenames, required files, stage count and observation dimensions. Every README quickstart command targets a path that does not exist and omits the required `--level`. `docs/architecture/archive/UNIVERSE-COMPILER.md` names seven `_stage_N_*` methods, none of which exist. `docs/config-schemas/drive_as_code.md` is 1437 lines documenting a filename and root key that do not exist. **Recency does not imply truth in this repo**; the one fully correct authoring document is `configs/reference/model_pack/README.md` (27 lines, May, outside `docs/`, unlinked from anywhere, and its single command is missing `--primary-level`). Error strings drift too — `validation/references.py:76-213` points authors at `drive_as_code.yaml`, and `vfs/schema.py:543` raises "required but not found" for a file `preflight.py:117-119` lists as optional. Already tracked as `hamlet-7a52a63e0b`.

**What closing it takes.** One coordinated pass, not 20 fixes — plus regenerating schema docs from the *consuming code path* rather than the Pydantic model, or they will keep certifying inert fields.

### P6 — Two unreconciled records of truth

`docs/bugs/` holds 60 files: 26 enhancement wishlist, 2 audits, 2 templates, 30 actual defect notes. Of 25 verified, 12 (48%) no longer describe reality. Meanwhile the *source* is littered with fix markers — `HIGH-02:`, `MED-05:`, `CRIT-07:`, `HIGH-09: Removed…`, `BUG-22 FIX:` — while the corresponding markdown still reads `Status: open`. The 2025-11-26 training audit fixed BUG-01/02/11 and CRIT-07, all four verified in source, and none were moved to `closed/`. The codebase knows what was fixed; the documentation does not. Any agent trusting `docs/bugs/` will re-litigate settled work.

**What closing it takes.** Delete the corpus; migrate the ~10 still-real items into filigree; stop maintaining a markdown backlog alongside a tracker.

### P7 — Domain semantics hardcoded in Python

For a product whose thesis is that the world is data, these are contract breaches: affordance affordability is keyed to a bar **literally named `money`** (`vectorized_env.py:628`, `affordance_engine.py:374-377`); curriculum stages are a Python literal with six Sims-specific meter names that do not match the shipped 8-meter `bars.yaml` (`adversarial.py:28-64`), with `CurriculumDecision.active_meters` capped at `max_length=6` (`state.py:178-185`) — a hard wall against any author whose universe differs; the retirement bonus is a `+1.0` magic constant outside the reward spec (`vectorized_env.py:1086`); adding a substrate topology is documented by the project's own doc as a four-step Python edit (`docs/architecture/substrate-system.md:107-129`).

### P8 — No-defaults erosion, concentrated in the newest schemas

`grep -c 'Field(default'`: `drive_as_code.py` 20, `brain_config.py` 15, `effects_config.py` 10, `training_v2_config.py` 7. CLAUDE.md classifies implicit defaults as a contract violation. Note the compounding: both confirmed-inert DAC fields (`normalize`, `clip`) carry defaults — an inert field with a default is invisible twice, since the author never types it and never sees it fail. Three DTOs also omit `extra="forbid"` (`effects_config.py:214,250`, `vfs_config.py:8`), and `EffectsConfig` defaulting `effect_definitions=[]` is what makes a wrong root key compile to an empty catalog instead of erroring.

---

## 4. The authorability ledger

This is the distance between promise and reality: what a person with a game-mechanic idea must still write Python for. Sizing is relative work, not schedule.

### SG2 VFS / VTC — the largest concentration
| Gap | Size |
|---|---|
| Action-conditioned state writes ("action X mutates variable Y by expression E, composed as claim_if_free / capacity_claim / priority_write, in phase P") — runtime complete, no YAML path (`compilers/actions.py:205`) | **M** (wire the compiler; runtime exists) |
| Affordance occupancy / capacity claiming (one agent per bed, N per job) — engine exists (`vtc.py:2176-2192`), no caller | **M** |
| Group-, zone- and message-scoped variables — the L5/L6 curriculum targets; env never supplies extents (`registry.py:464-482`, `vectorized_env.py:599-606`) | **L** |
| Choosing observation normalization (minmax/zscore/cyclical/one-hot/log/rank/masked) — required, cross-validated, never touches a tensor | **M** (or **S** if deleted) |
| Restricting who may write a derived VFS variable — compiler overwrites declared ACLs (`compilers/vfs.py:277-290`) | **S** |
| Declarative VTC transition rules beyond `social_residue` | **M** |

### SG4 Environment / DAC
| Gap | Size |
|---|---|
| Give a custom action *any* effect — cost, meter change, teleport. A declared REST/MEDITATE is structurally a no-op (`actions_config.py:38-43` → `compilers/actions.py:199-205` → `action_executor.py:20-158`) | **M** |
| Use a currency bar not named `money` | **S** |
| Set the episode-completion (retirement) reward | **S** |
| Normalize or clip the composed reward | **S** |
| Choose the aggregation operator, or compose sub-strategies with `hybrid` (both self-declared stubs, `dac_engine.py:347-377,408-448`) | **M** |
| Non-clamp boundary modes actually affecting the action mask (`action_mask_builder.py:130-179`; the abstract hook `get_valid_neighbors` exists and is never called) | **M** |
| Multi-tick affordances / opening hours without also enabling the day/night cycle | **S** |

### SG6 Training stack
| Gap | Size |
|---|---|
| Define curriculum stages — which meters active, what depletion, when to advance. Currently `STAGE_CONFIGS` Python literal | **L** (needs a real `stages.yaml` contract keyed to the universe's own bars) |
| Author a universe with >6 meters and still express a curriculum (`max_length=6`) | **S** inside the above |
| Choose an exploration strategy — `drive.intrinsic.strategy` has 5 Literals; `AdaptiveIntrinsicExploration` is hardcoded (`demo/runner.py:436`) and 2 of 5 have no implementation | **M** |
| Per-level network architecture (feedforward L0-L1, recurrent L2-L3) — `brain.yaml` resolves once at pack root (`raw_configs_v21.py:136`) | **M** |
| Configure recurrent geometry (CNN channels/kernels, encoder widths, LSTM depth, dropout, Q-head) | **M** (or **S** to delete the block) |
| Control when training begins relative to buffer fill | **S** |

### SG7 Effects / Items
| Gap | Size |
|---|---|
| Attach an effect to an item, an affordance, or the world (`executor.py:222` hardcodes AGENT; item/affordance effects never tick) | **M** |
| Area-of-effect (`for_each: nearby_agents` is a guaranteed runtime crash from YAML) | **M** |
| Spawn N items, or at computed coordinates, or with non-default initial VFS state | **M** |
| Effect intensity as an expression; duration override at spawn site | **S** |
| Consume/despawn an entity from a command; toggle affordance availability | **S** |
| `on_drop` behaviour (compiled, never called) | **S** |

### SG5 Substrate / world
| Gap | Size |
|---|---|
| A rectangular (non-square) world — compiles, rejected at `vectorized_env.py:178-180` | **S** (fix or add a schema validator) |
| `observation_encoding: scaled`, and `cubic` + `partial` vision — compile then crash; **three of the four crashes collapse to one change**: `compilers/observation.py:64-150` re-derives dims from `substrate.type` strings instead of asking the substrate instance, which it already does correctly for continuous at `:148-149` | **S** |
| A new topology (hex, simplex, BCC, graph) or substrate family from YAML | **L** (arguably out of scope; the doc is honest that this is a Python edit) |
| switch/case or fold/reduce in a config expression (`Switch`/`Reduce` AST nodes are unparseable) | **M**, or **S** to delete |

### SG3 Config DTO / SG1 Compiler
| Gap | Size |
|---|---|
| Checkpoint cadence and retention; periodic evaluation | **S** |
| Natural meter recovery / regeneration | **S** |
| Affordance interaction semantics: cooldowns, meter gates, prerequisites, probabilistic success, skill scaling. `capability_config.py:1-112` declares all six types with zero importers repo-wide — but it is not a head start: deleting it (WS-2) costs nothing, and the feature remains an unbuilt **L** either way | **L** |
| Curriculum ordering and membership actually honouring `experiment.curriculum_levels` | **S** |
| A schema for six of eleven files an author must write (`stratum`, `environment`, `experiment`, `actions`, `bars`, `curriculum`) — contracts exist only as Pydantic models | **M** (doc work, tracked in `hamlet-7a52a63e0b`) |

### SG8 Demo / frontend
| Gap | Size |
|---|---|
| Build or run the frontend at all from a clean checkout (`frontend/package.json` absent; `.gitignore:94` = `*.json`) | **S**, and blocking |
| Give a new affordance a display icon — `cues.yaml` schema exists, `CuesCompiler` is instantiated (`compiler.py:68`) and never invoked | **M** |
| Surface any new value in the UI; label actions for a non-cardinal vocabulary | **M** |
| Visualize a substrate other than Grid2D or Aspatial | **L** |
| Record anything other than every-Nth-episode | delete instead |

**Ledger summary.** Roughly 12 Small, 16 Medium, 5 Large. The Larges are the honest scope statements: curriculum-as-code, affordance capabilities, multi-agent scopes, new substrate families, and non-grid visualization. Everything else is wiring.

---

## 5. What is genuinely good

Evidence-backed, worth preserving verbatim through any recovery program.

**The compiler's provenance and artifact discipline.** `_compute_provenance_id` hashes config hash + compiler version + git SHA + python/torch/pydantic versions, and cache validity requires the whole thing to match (`compiler.py:655-680`, checked at `:127-134`). `COMPILED_SCHEMA_VERSION` is checked on every cache load with an actionable message (`compiled.py:583-587`), backed by `REQUIRED_COMPILED_UNIVERSE_FIELDS` (`compiled.py:53-90`) and ~30 parametrized tests that pop each field and assert the load fails. This is what makes a 40-field artifact safe to evolve.

**`world/expression` and the `FUNCTION_SPECS` single registry** (`functions.py:262-266`). Both the evaluator (`evaluator.py:100-107`) and the type checker (`type_checker.py:360-364`) read the same `FunctionSpec` bundling name, arity, return-type rule, argument validator and eval fn. It is structurally impossible to add a function to one and forget the other. 49 functions, ~15 consumers across effects/items/vfs/vtc/universe-compilers, 95% parser coverage, with a strict-float regex at `parser.py:69-73` carrying a comment explaining the real bug it fixes. This is the best engineering in the repo and the pattern the rest of the declarative surface should copy.

**The observation ABI.** `observation_encoder.py:24-45` builds the entire observation vector by iterating the compiled `ObservationSpec` and reading each field from the VFS registry — no hardcoded field list, no positional assumptions — with `_ensure_agent_observation_shape` (`:101-109`) raising on any spec/tensor mismatch rather than padding. The hardcoded-observation era is genuinely gone, and that fail-loud guard is the only reason SG5's three dimension bugs are crashes rather than silent tensor corruption feeding training. Do not soften it while repairing the compiler.

**VFS access control and provenance hashing.** `registry.py:484-580` enforces read ACLs, write ACLs, `agent_private` masking and a deliberately narrowed engine writeback path with real `PermissionError` raises, shape/dtype validation, and genuine negative tests. `schema_hashes.py:1-270` composes canonical, sorted, JSON-stable variable/observation/action/transition-graph hashes into one `vfs_hash` — the backbone that makes checkpoints and universes reproducible.

**`VTCTransitionRunner` + phase schedule** (`transition_schedule.py:35-200`). Passive depletion, threshold cascades, terminal conditions, state residue and action writes all commit through one phase-filtered runner with immutable context dataclasses, clone-on-entry semantics, and a hard error for any state key that is neither a bar nor a VFS variable (`:265-278`).

**The effects command compiler** (`effects/compiler.py`, 411 lines). Full type checking against a real schema, AST baked onto the node so the executor never parses at runtime, compile-time PARALLEL write-conflict detection that recurses through nested blocks (`:314-352`), and an explicit, well-messaged refusal to support nested `for_each` (`:246-267`). Refusing a feature loudly beats shipping it half-working. The bounded-resource discipline throughout (`MAX_CASCADE_DEPTH`, `MAX_COLLECTION_SIZE`, `MAX_DELAY_TICKS`) means effects can cascade without hanging training.

**The three replay buffers** (~1,250 LOC): batch-size-exceeds-capacity guard (`replay_buffer.py:83-87`), per-tensor shape validation on store (`sequential_replay_buffer.py:141-165`), O(1) deque eviction, length-weighted episode sampling for uniform transition sampling (`:226-232`), versioned serialize/load with explicit legacy rejection (`:327-333`). Backed by ~3,300 lines of genuinely constraining tests.

**Brain-as-Code layer 1.** `OptimizerFactory` (`optimizer_factory.py:23-162`) consumes every declared field across 4 optimizers and 4 schedules with assert guards documenting the Pydantic invariants they rely on; `LossFactory` (`loss_factory.py:176-204`) is small and total over its Literal; `build_feedforward`/`build_dueling` (`network_factory.py:50-70,165-178`) consume everything including layer_norm/dropout ordering and per-stream activations. `compute_brain_hash` (`brain_config.py:534-552`) and `apply_training_overrides` (`:562-596`, non-mutating, enumerated) are exactly right. The conditional discriminated unions — required-iff-selected *and* must-be-absent-otherwise — are the no-defaults principle done correctly.

**`checkpoint_utils.attach_universe_metadata`** (`training/checkpoint_utils.py:22-42`): records `config_hash`, `observation_schema_hash`, `drive_hash`, `brain_hash`, `vfs_hash` and per-field observation UUIDs. Real provenance for a declarative product.

**Architectural-invariant tests.** `test_domain_compiler_modules_own_their_implementation` asserts by source inspection that compilation logic has not migrated back into `compiler.py`; `test_vtc_transition_schedule_runtime.py:85-98` asserts `vectorized_env.py` contains no domain tokens ("trust", "reputation", "faction", "institution"). Rare and worth keeping verbatim — these mechanically defend the declarative boundary.

**Fail-loud config errors as documentation.** `AffordanceEngine._get_meter_idx` (`affordance_engine.py:473-489`) raises with the offending name, the context, and the sorted list of valid options. `_vfs_domain_compilation_error` (`compiler.py:250-267`) translates domain exceptions into located, coded diagnostics. `CompilationErrorCollector` aggregates so authors get every broken reference in one pass. `compile()` refuses to guess `primary_level` (`compiler.py:94-95`). `AdversarialCurriculum` checkpoint strictness (`adversarial.py:455-506`) names missing fields with a regenerate instruction and explains in its docstring which past silent-reset bug motivated it.

**Also worth naming:** `demo/database.py` in full (88% covered, 15 real tests, context-manager lifecycle); substrate-agnostic broadcast (`live_inference.py:911-956,184-244`) — change the substrate in YAML and the UI payload adapts; `AspatialSubstrate` as a first-class substrate rather than a degenerate grid; the four boundary modes implemented per-substrate and fully vectorized; the DAC closure-factory pattern (eleven explicit factories deliberately avoiding the late-binding loop closure bug); `epsilon_greedy_action_selection` handling the all-actions-invalid row instead of a NaN argmax; item identity preservation across pickup/drop with per-instance state surviving.

---

## 6. Recovery shape

Work streams and their dependencies. No dates, no estimates, no sequencing beyond must-precede-because.

*Tracker state verified this pass:* `filigree list-issues` shows 5 open tasks + 1 active milestone + 1 planning release. Three open items already map onto streams below and should be treated as their seeds, not duplicates: `hamlet-d892e161c0` "Restore Vue/Vite frontend package metadata" (WS-0), `hamlet-c8c316ba03` "Add golden tick, phase ordering, hash boundary, and checkpoint safety tests" (WS-3), `hamlet-7a52a63e0b` "Replace stale architecture and workflow docs with source-derived facts" (WS-5). The active milestone `hamlet-7a932c4e40` "Wire Architecture Gaps From 2026-05-16 Architecture Report" is the existing container for WS-4-shaped work.

**WS-0 — Unblock and stop the bleeding.** Write `frontend/package.json` **and** fix `.gitignore:94`'s blanket `*.json` (fixing the symptom alone reproduces the bug on the next write — `hamlet-d892e161c0` as written targets only the manifest). Delete `docs/bugs/` after migrating the ~10 verified-still-real items into filigree. *Must precede nothing technically, but must precede any doc work, because the stale corpus will cause re-litigation of settled fixes.*

**WS-1 — Correctness defects that silently corrupt data.** Four items, independent of each other and of everything else: (a) key the compile cache on `primary_level` — `_cache_artifact_path` (`compiler.py:595-598`) returns a single `universe.msgpack` per pack, so requesting a different level returns the wrong artifact, and that artifact is what stamps checkpoint provenance (`checkpoint_utils.py:34-42`); (b) fix the LSTM training unroll — `forward()` does not mutate `self.hidden_state` and the training loop never threads it, so every training timestep sees zeros (`vectorized.py:777-828`, `networks.py:271-272,290`); (c) stop treating the last index of every sampled subsequence as terminal (`vectorized.py:817-819,837-839`); (d) delete the live-but-weaker `apply_interaction` and route to `apply_instant_interaction`, which already has the meter clamp, generic affordability check and type validation (`affordance_engine.py:396-450` vs `:154-211`). **This stream must precede WS-4 (declarative expansion)**: expanding the authoring surface on top of a training loop that does not learn, or a cache that returns the wrong universe, compounds the damage. It must also precede any RESPEC work — you cannot freeze a contract around a broken loop.

**WS-2 — Zero-backcompat deletion.** Cheap, mandated, and it shrinks WS-3 and WS-5, which is why it precedes both: `src/townlet/recording/` end-to-end (~1,150 LOC + ~2,600 test lines, unreachable at three points, 9 months stale — salvage the async-queue design and the msgpack+LZ4 versioned envelope on paper); `OptimizationData` end-to-end *after* confirming the VTC cascade/modulation compilers reject unknown meter and affordance names so the author-facing validation at `compilers/optimization.py:49-89` is not lost; `capability_config.py`, `affordance_masking.py`, `source_map.py`, `world/types/primitive.py`, `StructuredQNetwork`, `SimpleQNetwork`, `RewardTensor.from_components`, `AdversarialCurriculum.from_yaml`, `ActionSpaceBuilder` (loads a `global_actions.yaml` that no longer exists) and their tests; `is_dueling`/`is_set_encoder`; items `spawn_position`/`spawn_interval`; `Switch`/`Reduce` AST nodes; `get_valid_neighbors` (unless WS-4 uses it for boundary-aware masking — decide there first); the eight orphaned Vue components.

**WS-3 — The wiring test harness.** One config-in → behaviour-out test per declarative surface, using the real compiler and real env. Templates already exist and should be copied rather than invented: `test_vtc_transition_schedule_runtime.py:47-98` and `integration/test_items_integration.py` (asserts real numeric bar deltas). Plus the two mechanical rules: every schema field must appear non-default in at least one pack, and every enumerated value of every `stratum.yaml` field must compile *and build an env*. **This must precede WS-4** — it is the acceptance criterion for WS-4, and without it the next declarative feature will land inert exactly like the last six did. It is also the cheapest way to enumerate what is left: run the rules and the inert set falls out mechanically rather than by hand-tracing.

**WS-4 — Close the authoring surface (the product work).** Governed by the ledger in §4. Two independent sub-streams: *wire it* and *delete it*, decided per field — never "leave it declared." Highest-leverage items, because each unlocks a category rather than a knob: populate `RuntimeAction.reads/writes` from config (unlocks the whole 11-mode composition engine that already exists); pass the catalog's compiled scope into `spawn_effect` and tick item/affordance effects (unlocks three of four effect scopes); delegate substrate observation dims to the substrate instance in `compilers/observation.py:64-150` (fixes three of four substrate crashes in one change); give custom actions a real behavioural surface; add `extra="forbid"` and required `effect_definitions` to `EffectsConfig` (converts the worst failure mode from silent to loud). **Depends on WS-1 and WS-3.**

**WS-5 — Doc and spec truth.** Already scoped as `hamlet-7a52a63e0b`. One coordinated pass driven by the single unabsorbed v2.1 migration, not 20 independent fixes. Must include: the seven missing schema references (`stratum`, `environment`, `experiment`, `actions`, `bars`, `curriculum`, `drive`); promoting `configs/reference/model_pack/README.md` and `docs/guides/world-compiler-guide.md` into a real authoring guide; deleting the aspirational-never-built set (`UNIVERSE_AS_CODE.md`'s four non-existent subsystems, `BRAIN_AS_CODE.md`'s cognitive-module graph, HLD 03/05/08/09) — the repo's own zero-BC rule applies to docs; a `docs/` layout where the directory name encodes authority; and the compiler's user-facing error strings, which for a declarative product are the most-read spec of all. **Two hard prerequisites**: the compiler's stage numbering must be made coherent first — it has three mutually inconsistent systems in one file (`compiler.py:100-225`: eight `_log_stage` calls, two unlogged Stage-0 passes, inline comments labelled 1/1b/1c/2/3/5/6/7, methods named `_stage_5/6/7` while logging 6/7/8) and no doc can be truthful until it is. And WS-4 must be far enough along that schema docs are generated from consuming code paths, not from Pydantic models — otherwise the rewrite re-certifies the inert fields.

**Ordering summary.** WS-0 and WS-1 have no prerequisites and no dependency on each other. WS-2 precedes WS-3 and WS-5. WS-3 gates WS-4. WS-5 trails WS-4 and is gated on the stage-numbering fix. The only genuinely sequential constraint is WS-1 → WS-3 → WS-4; everything else is parallelizable.

---

## 7. What this assessment could not establish

**Not verified by execution.** Most findings are source-traced, not run. The exceptions — which *were* executed — are: `configs/default_curriculum` compiling in ~1.0s with a working warm cache; the observation/action dims (`observation_dim=124`, `action_count=15`) that contradict CLAUDE.md's 29→8 claim; the three substrate configs that crash at `env.reset()`; the LSTM zero-hidden-state demonstration (identical observations → identical Q-values under the training-loop unroll, differing under a correct one); the pure-YAML effects chain (`effects.yaml` → item `on_use` → agent effect → `on_tick` bar delta of +0.04 per `env.step`); and `configs/reference/model_pack/effects.yaml` compiling to `n_defs=0`. Everything else — including the cache/primary_level bug's downstream impact on checkpoint provenance — is inferred from source and would benefit from a runtime confirmation.

**Not established: whether anything trains well.** This is a maturity assessment of the *substrate*, not of learning outcomes. No claim is made about whether agents learn, whether the curriculum progresses, whether reward hacking still emerges pedagogically, or what the LSTM fix does to L2/L3 results. The recurrent path is unexercised by any shipped pack, so its behaviour post-fix is unknown.

**Not established: performance.** No profiling was run. Two known-cost items are flagged but unquantified: observations are encoded twice per step (`reward_calculator.py:23-24` then `vectorized_env.py:1105`), with the intrinsic-reward encoding using a pre-advance `time_of_day`; and the hot path depends on TorchScript JIT fusion (`vtc_kernels.py`) with no fallback, where a toolchain fault takes down 37 subsystem tests. Whether either matters at training scale is unmeasured.

**Tracker state.** Verified directly (`filigree list-issues`): 5 open tasks, 1 active milestone, 1 planning release, and `hamlet-7a52a63e0b` confirmed open. What was *not* verified is the claim that ~10 still-real items from `docs/bugs/` should be migrated in — that is a judgement carried up from the freshness lens, and the per-note mapping to filigree issues has not been done. Nor was it checked whether the open issues' bodies already cover the defects I attribute to them beyond their titles.

**Partial coverage.** Of 30 defect notes in `docs/bugs/`, 25 were verified (83%); five were not. `docs/config-schemas/{effects,items,expressions,vfs-profiles,affordances,training,enabled_actions}.md` were assessed for pack-context staleness but not field-by-field verified against their DTOs — only `brain.md` and `training.md` were. The 176 plans and 119 bug files were not individually read. The 322-field sweep was mechanical (grep-based), so a field consumed via `**model_dump()` splat or dynamic `getattr` on a computed name could have been misclassified as inert — I hand-checked this for DAC (`dac_engine.py` uses explicit `getattr` on strategy objects, never a splat) but not for every subsystem.

**Absence-of-evidence verdicts, flagged as lower confidence.** BUG-37 (no compile-time VFS standard-variable contract) rests on not finding a check across `preflight.py`, `validation/references.py` and `validation/semantics.py` — a named check elsewhere in the compiler would overturn it. Similarly, `recovery.natural` is asserted to have *no reader*, not that no regeneration exists anywhere; if health regen occurs it is via DAC/effects/cascades, not that field.

**Frontend not run.** With `package.json` absent, nothing in `frontend/` was built or executed. The 11 WebSocket protocol drift instances are a static diff between `live_inference.py:506-1148` and `stores/simulation.js:253-601`; which of them matter in practice is unverified. Component liveness (19 wired / 8 orphaned) is import-graph analysis only.

**Test-suite health.** 2942 tests collect. The full suite was not run to green, and no coverage gate exists despite AGENTS.md claiming ≥70%. Coverage figures cited per-subsystem are from targeted `pytest --cov` runs, not a whole-repo measurement. Note also that `src/townlet/` is 45,274 LOC, not the ~37k in the brief — a ~20% underestimate that does not change any conclusion but is worth correcting.

**Out of scope by instruction.** No sequencing, forecasting, or effort estimation — that is `/axiom-program-management`'s. The ledger's S/M/L sizing is relative work only and should not be read as duration.