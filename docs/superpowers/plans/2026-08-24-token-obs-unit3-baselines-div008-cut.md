# Token-Obs Unit 3 — Baselines, DIV-008, then the Cut: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze the shipped-L2 pre-raster training baseline (≥5 seeds — unrepeatable
after the cut), register DIV-008, then replace the fixed-width superset+mask observation
ABI with the TokenSpec as one atomic knockdown, adjudicated per-stream against the pinned
oracle: **tokens change what agents see, never what the world does.**

**Architecture:** Three phases in strict order. Phase 0 (src/townlet **frozen**): a
standalone baseline harness trains the shipped L2 feedforward configuration headlessly at
5 seeds, measures final greedy survival (the measurement does not exist today — the
`evaluation:` config block is declared-but-inert, verified 2026-08-24), and commits the
frozen record that reversal trigger 1 reads forever. Phase 1: the unit-1/unit-2
carry-forward batch lands on the harness, the matrix re-confirms exit 0 in both modes,
and the DIV-008 register entry is written — record-then-bind, entry before cut. Phase 2:
the cut — new machinery (TokenSpec, publishers, token_set network) is built green
alongside the old path, then one swap task severs the old wiring and repairs the suite,
then adjudication binds DIV-008 with movers measured (never guessed), runs the matrix in
both modes, and moves the docs at gate-2 standard.

**Tech Stack:** Python 3.12, torch, pytest, uv. No new dependencies. Two RTX 4060 Ti
16GB GPUs available for Phase 0.

**Spec:** `docs/superpowers/specs/2026-08-22-token-observation-representation-design.md`
(§§1–5 are the design; §6 unit 3 is this plan's mandate; the Reversal-triggers and
Verify-at-implementation sections travel with every task). Tracker: `hamlet-fa6bb6da4a`
(in progress, assignee `claude-fable` — all filigree ops use `--actor claude-fable`; do
not re-claim). Discharge tickets riding this unit: `hamlet-b8ad2ffcd6`,
`hamlet-d97b4d6b4a`, `hamlet-d970ef83f0`, `hamlet-88578e629e`, `hamlet-0ddc83e377`,
`hamlet-6a6e104523`, `hamlet-702ae15f82` (preflight half), `hamlet-81942565ff` (mirror
half), `hamlet-c7084169f7` (clone-audit half). Carry-forward batches: tracker comments
234 and 242 on `hamlet-fa6bb6da4a`.

## Plan staging (stated up front, not discovered)

Phase 0 and Phase 1 tasks are written at full step fidelity below. Phase 2 tasks are
written at **contract fidelity** — exact files, interfaces, refusal shapes, named tests,
verification commands — and each is **expanded to step fidelity immediately before its
execution**, against the then-current tree. This is the spec's own ordering, not
deferral: §2 mandates that capacity, the worked width table, and trigger 3's arithmetic
are computed **only after explicit exposure lands** (Task 5), so later tasks' literal
code depends on earlier tasks' outputs by design. The expansion appends to this file;
each expansion is committed with its task.

## Global Constraints

- **Phase 0 freezes `src/townlet/`.** The baseline measures the shipped code; not one
  line under `src/townlet/` moves until Task 3. The harness lives in `scripts/` and
  writes artifacts under `docs/product/baselines/` and `runs/` (gitignored except the
  frozen record).
- **Record-then-bind (`PDR-0037`/`PDR-0033`):** the DIV-008 entry is written before the
  cut; its declared hash fields are finalized by **measurement** (DIV-009's worktree
  method) at binding, never guessed. Narrowness both directions: a declared non-mover →
  `REGISTERED_DIVERGENCE_ABSENT`; an undeclared mover → red.
- **The adjudication criterion (spec §5):** under **scripted** actions,
  `actions`/`rewards`/`dones` and state evolution stay **byte-exact** across the cut;
  the `obs` stream diverges **as registered** (unit-1's `RegisteredStreamDivergence`).
  Verified fact this rests on: no fixture pack declares `exposed_to` anywhere
  (grep 2026-08-24, zero hits) — post-cut, fixture profile variables become unexposed,
  compiles succeed, no fixture edit is needed (fixtures are frozen; never touch
  `.oracle/` or `oracle_fixtures/`).
- **`num_agents` is a batch size, not a shared-world population.** Today's
  `VectorizedHamletEnv(num_agents=N)` means N **independent** worlds (tests pass 2/4
  routinely). The `agent` token type's capacity derives from a *declared shared-world
  count*; **no shipped pack declares one, so `agent` capacity is 0 everywhere and the
  type is structurally absent** (spec §2). The overflow refusal must key on the declared
  count, never on `num_agents` — otherwise every existing test breaks. Admitted
  authoring surface #4 (the declared count field) is deferred to the first shared-world
  pack; recorded, not built here.
- **No green half-state inside the swap (spec §6.3):** Tasks 6–9 build new machinery
  green alongside the old path (new files; suite stays green). Task 10 severs the old
  wiring and lands green at its end. Pushes happen only at green task boundaries.
- **No-tech-debt (`PDR-0012`/`PDR-0013`):** wire-or-delete; every finding this unit
  surfaces gets a named discharge vehicle in-flight; nothing parks.
- **Implementation constraints (spec §6, verbatim, inherited by every Phase-2 task):**
  publisher write targets use `.view()` (raises on copy), never `.reshape()`; stored
  observations are `.clone()`d or per-tick allocated; attention uses explicit QKV +
  `F.scaled_dot_product_attention`; masks are bool; no LayerNorm/Linear over
  concatenated set width anywhere in the token path; registry publisher fills are
  batched per scope via the arena (never per-variable Python loops); item-arena reads
  never hold cross-tick views.
- **Storage decision (assigned to this plan by spec §3): per-scope arenas.** The
  registry publisher is built item_vfs-style — a per-scope `[capacity, elements]` arena
  with a compiled index map, batched fills, `.view()` writes — for global and agent
  scopes. Rationale: the in-tree template exists (`item_vfs` arena + index map), both
  `variable_element` fill paths then share one code shape, and it retires the
  per-variable Python loop + clone-per-read that `hamlet-c7084169f7` measured. The
  index-map-only alternative was considered and rejected: it leaves per-variable write
  granularity in place, which is the measured cost.
- Test invocation: `UV_CACHE_DIR=.uv-cache uv run pytest <path> -v`. Type gate:
  `UV_CACHE_DIR=.uv-cache uv run mypy src/townlet`. Matrix:
  `UV_CACHE_DIR=.uv-cache uv run python -m townlet.oracle.harness matrix` (plain and
  `--scripted`), exit 0 required at every green boundary.
- Commit style per task, `feat(obs)|feat(oracle)|feat(vfs)|test|docs: … (hamlet-fa6bb6da4a)`;
  matrix runs recorded by run id in commit messages that adjudicate.
- Float32 note (spec verify-at-implementation): tick counters are exact to 2^24;
  persistent-lifetime counters remain `hamlet-0268336cd1`'s question — the publisher
  carries the cast-policy comment, nothing more.

---

## Phase 0 — Freeze the L2 baseline (src/townlet FROZEN)

### Task 1: Baseline harness — headless seed runs + the greedy evaluator that does not exist

The spec's trigger 1 reads "final greedy survival" against this baseline forever.
**Verified 2026-08-24: no greedy evaluation exists** — `EvaluationConfig`
(`training_v2_config.py:194`, `interval`/`num_episodes`) has zero runtime consumers;
the training loop never evaluates. The harness therefore builds the measurement as a
standalone script; whether the inert config block wires into the training loop or dies
is WS-4-routed authoring-surface work, **not** this unit's.

**Files:**
- Create: `scripts/l2_baseline.py` (single file, three subcommands)
- Create: `tests/test_townlet/unit/scripts/test_l2_baseline.py` (pure-function tests
  only — pack rewriting and IQM; no training in tests)
- Filigree: file the inert-`EvaluationConfig` finding as a new bug ticket, routed WS-4
  (`recovery:WS-4` label), discharge vehicle stated as "wire into the training loop or
  delete the block; the unit-3 baseline harness is the interim measurement"; comment the
  ticket id into `hamlet-fa6bb6da4a`.

**Interfaces (produces):**
- `l2_baseline.py train --seed N --episodes E --run-root runs/l2_baseline/` — copies
  `configs/default_curriculum` to a scratch pack with **only** the
  `levels/L2_partial_observability/training.yaml` `seed:` line rewritten to N, then runs
  `DemoRunner(config_dir=<scratch>, db_path=<run>/demo.db, checkpoint_dir=<run>/checkpoints,
  max_episodes=E, level_name="L2_partial_observability").run()` headlessly. Records the
  scratch-pack diff (must be exactly one line) into the run dir.
- `l2_baseline.py eval --run-dir <run> --episodes 100 --device cuda` — loads the final
  checkpoint via the DemoRunner **context-manager** pattern (CLAUDE.md), builds a fresh
  env from the same scratch pack, runs greedy rollouts (`argmax` over
  `population.q_network` Q-values, epsilon 0, no learning), and writes
  `<run>/greedy_eval.json`: per-episode survival steps per agent slot, mean, median,
  episode cap (1000), eval seed.
- `l2_baseline.py curves --run-dir <run>` — reads the run's `demo.db` (schema in
  `src/townlet/demo/database.py` — read it, do not guess) and writes
  `<run>/curves.csv`: `episode, survival_steps, total_env_steps_cumulative` (survival
  per episode; cumulative env-step counter is the trigger-1 budget denominator).
- `iqm(values: list[float]) -> float` — interquartile mean, pure function, exported for
  Task 2's record and reused by unit 4's comparison.

- [ ] **Step 1: Write the failing tests** — `test_rewrite_seed_changes_exactly_one_line`
  (copy a minimal pack fixture, rewrite seed, assert unified diff has exactly one `- seed:`/`+ seed:`
  pair), `test_iqm_drops_tails` (`iqm([0,0,10,10,10,10,100,100]) == 10.0`),
  `test_iqm_small_n_falls_back_to_mean` (n < 4 → mean, documented).
- [ ] **Step 2: Run to verify failure** (`ModuleNotFoundError` / `AttributeError`).
- [ ] **Step 3: Implement `scripts/l2_baseline.py`** — argparse three subcommands as
  contracted; `train` refuses to run if `git status --porcelain src/townlet` is
  non-empty or HEAD differs from the pin recorded in an existing run-root (all seeds
  must share one tree).
- [ ] **Step 4: Tests pass; mypy clean on the script**
  (`uv run mypy scripts/l2_baseline.py`).
- [ ] **Step 5: Calibration run** — `train --seed 42 --episodes 300` on one GPU, timed.
  Record episodes/hour and env-steps/hour from `curves`. **Budget decision rule:**
  `E = min(50_000, largest multiple of 1_000 such that 5 seeds complete within ~12 h
  wall across both GPUs)`, floor 5_000. Record the chosen E and the arithmetic in the
  Task 2 record. Sanity-check `eval` end-to-end on the calibration checkpoint.
- [ ] **Step 6: File the inert-EvaluationConfig ticket; commit**
  (`feat(baseline): headless L2 baseline harness — train/eval/curves (hamlet-fa6bb6da4a)`).

### Task 2: Execute and freeze the baseline (operator-driven, not subagent)

Five seeds — **42, 43, 44, 45, 46** — at the Task-1 budget E, split across the two
GPUs, run in background; then greedy eval (100 episodes each), curves extracted, and the
frozen record committed. This task is driven by the standing agent (long wall-clock
background jobs), not dispatched to a subagent.

**Files:**
- Create: `docs/product/baselines/2026-08-l2-preraster/record.md` — the frozen record:
  git pin (must be the Task-1 commit), config identity (pack path + compiled
  `config_hash` from the artifact), seeds, episode budget E, realized total env steps
  per seed, final greedy survival per seed (mean + median of 100 greedy episodes),
  **seed-level IQM of final greedy survival** (the trigger-1 number), curve plateau
  status stated honestly (plateaued or still climbing at E — trigger 1 compares at
  equal budget either way), eval protocol (greedy argmax, 100 episodes, cap 1000,
  eval seed), and the exact reproduction commands.
- Create: `docs/product/baselines/2026-08-l2-preraster/seed_<N>_curves.csv` (×5) and
  `seed_<N>_greedy_eval.json` (×5) — committed; checkpoints stay in `runs/`
  (uncommitted; sha256 of each final checkpoint recorded in `record.md`).

- [ ] **Step 1:** Launch 5 training runs (background, 2–3 per GPU via
  `CUDA_VISIBLE_DEVICES`), monitor to completion.
- [ ] **Step 2:** `eval` + `curves` per seed; assemble `record.md`; compute IQM.
- [ ] **Step 3:** Self-check the record against trigger 1's wording — every quantity it
  reads (final greedy survival, env-step budget, seed-level IQM) must be present and
  unambiguous. A future reader must be able to run the token-side comparison without
  interpreting anything.
- [ ] **Step 4:** Commit the record
  (`docs(baseline): freeze L2 pre-raster baseline, 5 seeds (hamlet-fa6bb6da4a)`); push;
  comment the record path + IQM onto `hamlet-fa6bb6da4a`.

## Phase 1 — Harness carry-forwards and the DIV-008 entry

### Task 3: The comment-234/242 harness batch, then a clean pre-cut matrix baseline

The unit-1 and unit-2 reviews named six cheap harness items to land "in the same unit
that registers DIV-008". They land **before** the entry so the pre-cut exit-0 baseline
is read on the final harness.

**Files:**
- Modify: `src/townlet/oracle/trace_io.py` — (a) single-source `_TRACE_STREAMS` (it is
  defined here; `matrix.py` already imports it — remove any remaining hand-synced
  stream tuple elsewhere in the oracle package, grep `("obs", "actions", "rewards",
  "dones")`); (b) restore the `mismatched` diff dict in the
  `REGISTERED_DIVERGENCE_ABSENT` hash detail (comment-242 item 1).
- Modify: `src/townlet/oracle/harness.py` — `_ADJUDICATION_NOTE` "ALL EITHER" wording
  fix (comment-234 item 4).
- Modify: `docs/oracle/known-divergences.md` — "Adding an entry" gains one sentence on
  narrow-to-disjoint (DIV-009 style) vs overlap (DIV-010 style) (comment-242 item 5).
- Test: `tests/test_townlet/unit/oracle/test_compare.py` — three asserts from
  comment 234: `register_refs == ()` on the stale-stream test; a distinct-refs
  composition test (hash DIV-X + stream DIV-Y → two refs — branch currently untested);
  a `diff_entries` value assert.

- [ ] Steps: failing tests → implement → suite green → **matrix exit 0 in BOTH modes**
  (plain + `--scripted`), run ids recorded → commit
  (`test(oracle): unit-3 harness carry-forward batch (hamlet-fa6bb6da4a)`).

### Task 4: Write the DIV-008 register entry (entry now, binding at Task 11)

**Files:**
- Modify: `docs/oracle/known-divergences.md` — replace the DIV-008 reservation note
  with the entry.

**Entry content (drafted here; declared movers finalized by measurement at Task 11):**
- **What diverges:** the `obs` stream, on every cell (`RegisteredStreamDivergence`,
  stream-scoped — unit 1's third shape, built for exactly this entry), plus the
  provenance hashes the cut moves — expected `observation_schema_hash` (redefined over
  the TokenSpec) and `vfs_hash` (slot-2 composition consequence, spec §5); whether
  `variable_schema_hash` moves (VariableDef loses its inert `normalization` field)
  is **measured at binding, not asserted here**.
- **What must NOT diverge (the criterion):** under scripted actions,
  `actions`/`rewards`/`dones` byte-exact on every cell. Tokens change what agents see,
  never what the world does.
- **Env-internal-RNG caveat (comment-234 item 3, verbatim requirement):** scripted mode
  removes the action-draw RNG coupling; if `env.step` ever starts consuming global RNG,
  old/new decorrelate env-internally even under identical actions — failure direction
  is red, never false green, but a future env change must not be misread as a token-cut
  defect.
- **Fixture-exposure note:** fixture packs declare no `exposed_to` (verified, zero
  hits); post-cut their profile variables are unexposed by the explicit-exposure rule,
  which is part of the registered observation divergence, not a separate defect.
- [ ] Steps: write entry → `pytest tests/test_townlet/unit/oracle/ -v` green (the
  register parser must accept it; binding absent so no cell flips) → commit
  (`feat(oracle): DIV-008 entry recorded — record-then-bind (hamlet-fa6bb6da4a)`).

## Phase 2 — The cut (contract fidelity; each task expanded to step fidelity at execution)

### Task 5: Authoring-surface prerequisites — every compile-time rule, packs updated

All compile-time; no runtime behavior moves yet; suite stays green.

**Files:** `src/townlet/config/vfs_profiles_config.py`,
`src/townlet/config/effects_config.py`, `src/townlet/vfs/schema.py`,
`src/townlet/vfs/registry.py`, `src/townlet/universe/validation/`, shipped packs under
`configs/` (mechanical exposure/normalization edits), tests beside each.

**Contracts:**
1. **Explicit exposure (`hamlet-d97b4d6b4a`):** delete the three default-injection
   validators (`vfs_profiles_config.py:127-128, 238-239, 325-326` shape). Empty
   `exposed_to` = unexposed. Every shipped pack that relies on the fail-open default
   gets the explicit line it meant; packs that meant "unexposed" get nothing. Census
   first, edits recorded per pack in the task report.
2. **Normalization at exposure (`hamlet-b8ad2ffcd6`):** exposed profile variables gain
   a **required** `normalization` field; unexposed need none. Boundedness certification
   (spec §1): exposing under `none`/`zscore`/unclipped `minmax`/bare `masked_value` is
   a compile refusal naming the rule; `one_hot` on tokenized variables refuses;
   `cyclical_sin_cos` is legal (lands both lanes in Task 6). `rank_scaled`
   (`hamlet-6a6e104523`) is restricted or refused on the same surface — decision at
   expansion, with that ticket's evidence in hand.
3. **Effects DTOs (`hamlet-88578e629e`):** `ConfigDict(extra="forbid")` on every
   effects DTO; `max_active_effects: {global, agent, item, affordance}` required in
   `effects.yaml` **iff** any effects are declared (No-Defaults); shipped packs
   declaring effects gain the block.
4. **`set_engine_value` shape close (`hamlet-d970ef83f0`):** `registry.py:567` refuses
   a tensor whose shape contradicts the variable's declared element shape (a global
   scalar can no longer legally hold `[B]`). Fix every caller the refusal flushes out.
5. **Write-backs loud (`hamlet-0ddc83e377`):** VTC/evaluator write-backs raise on
   unknown ids instead of silently dropping.
6. **Widened scope DTO (spec §2 "DTO consequence"):** the observation-field scope
   Literal widens to carry all nine `VariableScope` members; the §2 scope table's
   refusals (affordance/pair/group/zone/message exposure → compile error naming the
   table) are implemented and table-tested per row.
7. **Extents preflight two-liner (`hamlet-702ae15f82`, preflight half).**

**Tests:** per-rule refusal tests naming the error text; a scope-table test
parameterized over all nine rows; pack-census test — every shipped pack compiles
post-edit. Tickets 1–5's closures commented with mechanism evidence.

### Task 6: TokenSpec — the compiled artifact and its math

**Files:** create `src/townlet/universe/dto/token_spec.py`; modify
`src/townlet/universe/compilers/observation.py` (emission arrives Task 7; this task
builds the artifact + pure derivations), tests under
`tests/test_townlet/unit/universe/`.

**Contracts (all from spec §§1–2, exact):** type roster (7 live types, canonical
engine order; 3 reserved names refuse); per-type payload schema embedded (feature
names, order, normalization refs); `MAX_POSITION_RANK = 8` (rank > 8 pack refuses
loudly); `VALUE_BLOCK_WIDTH = 2` + width-used feature; the variable-descriptor block
(scope one-hot 9, semantic_type one-hot 6, normalization kind one-hot 9 + canonical
parameter vector absent-marked, dtype flag 3, lifetime one-hot 3, normalized declared
initial, log-scaled element count, owner/slot coordinate) — **exact widths fixed here
and recorded in the artifact**; capacity table per spec §2 (agent capacity 0 absent a
shared-world declaration; item = `max_items_in_world + max_items_per_agent ×
agents_per_world`; effect = per-scope declared budgets × denominators);
compile-time indistinguishability check (identical static payload signature + coordinate
space → compile error naming both declarations); token census + the `{type: mean}`
>64-tokens advisory; serialization layout `total_dims = Σ N_t × (1 + W_t)`, presence
leading each row; affordance payload (interaction_type one-hot, absolute + egocentric
position, effect summary k=4 by normalized magnitude with target-signature recursion,
count feature). Worked width table for `default_curriculum` L1 computed and recorded
(the spec's §2 estimate is superseded by this measurement).

**Tests:** indistinguishability refusal + one-distinguishing-parameter compiles;
width rules (`cyclical_sin_cos` one token both lanes; `one_hot` refusal); capacity
arithmetic per type against a fixture pack; census counts; serialization width equals
the sum formula; rank-9 substrate refusal.

### Task 7: Compiler emission, hashes, and the `.compiled` schema

**Files:** `src/townlet/universe/compilers/observation.py`,
`src/townlet/universe/compilers/vfs.py`, `src/townlet/universe/compiled.py`,
`src/townlet/universe/dto/universe_metadata.py`, the `.compiled`
serializer/loaders, tests beside each.

**Contracts:** the pipeline's product is the TokenSpec (ObservationSpec ceases to be
emitted — its type is deleted in Task 10 with its last consumer);
`observation_schema_hash` is redefined over TokenSpec type-schema + slot-binding
content; **`vfs_hash` keeps name and meaning — the TokenSpec-derived hash occupies slot
2 of the same four-term composition** (spec §5, ruled); the VFS `ObservationField`
mirror and `VFSObservationSpec` lose their producer (deletion completes in Task 10;
`hamlet-81942565ff`'s in-engine fallback dies with it — the capacity table replaces
it); `apply_normalization` kernels survive and move to the publisher path;
`COMPILED_SCHEMA_VERSION` bumps; stale artifacts refuse loudly; `inspect` prints the
token census. Engine-minted publisher variables enumerated here (spec §5's inventory
item). Comment-242 item 4 (evaluator comment: statics also enter `vars_to_eval` via
`history_spec` — name the second path) lands with the vfs.py touch.

### Task 8: Runtime publishers and the visibility filter

**Files:** create `src/townlet/environment/token_publishers.py` (one module, one
publisher per type); modify `src/townlet/vfs/registry.py` (per-scope arenas);
`src/townlet/environment/observation encoder` (new token encoder alongside the old —
swap is Task 10), tests under `tests/test_townlet/unit/environment/`.

**Contracts:** one publisher per token type, dispatching on type (`PDR-0076`
discipline); `variable_element` filled by two publishers — registry publisher over the
new **per-scope arenas** (Global Constraints decision) and the item-arena publisher
with owner/slot coordinates; the publisher is the **`agent_private` enforcement point**
(filtered before slot binding, pinned by test — the `hamlet-83a043a9b9` boundary by
mechanism); presence ownership (static 1 / dynamic toggles, unique-slot writes);
overflow **raises at publish time** naming type, capacity, source; visibility filter
via substrate `visible(self_pos, entity_pos, vision_range)` under declared metric +
boundary mode, wrap-aware; egocentric features at publish time (shortest-path under
wrap); publishers run at the existing end-of-step observation point; **fills are
batched per scope — the per-variable loop and clone-per-read die**
(`hamlet-c7084169f7`: record a before/after step-time + clone count on
`set_encoder_smoke`, the clone-audit half of that ticket).
Comment-242 items 3 (reset-path tick write clobber: reorder or comment) and 2 (hoist
the static-merge/refusal block out of the `compiled_vfs_profiles is not None` gate)
land with the step-path rewrite. Float32 cast-policy comment on the tick publisher.

**Tests:** per-type wiring test (declare → that token row moves); presence
legitimately-zero ≠ absent; overflow at capacity+1 raises; visibility per substrate ×
boundary mode; egocentric wrap; `agent_private` never lands in any agent's rows;
replay aliasing (two consecutive stored ticks differ).

### Task 9: The token_set network, flat view, checkpoint gates, transfer

**Files:** `src/townlet/agent/networks.py` (new `TokenSetQNetwork`),
`src/townlet/agent/network_factory.py`, `src/townlet/config/brain_config.py`
(`architecture.type: token_set` + `token_embed_dim` + the `PDR-0112` aggregator block
verbatim), `src/townlet/training/checkpoint_utils.py`,
`src/townlet/exploration/` (RND), tests beside each.

**Contracts:** per-type projection encoders in an **`nn.ModuleDict` keyed by token
type name**; learned per-type embedding added post-projection; one mixed pooled set;
aggregator `{type: mean} | {type: attention, num_heads: N}` (required, No-Defaults);
Q-head. Masking: output-side masking guarantees **exact-zero contribution and
exact-zero gradient** for absent tokens per aggregator type, pinned by test; all-empty
unmask guard survives. Checkpoint gates **replaced**: token nets gate on the TokenSpec
**type-schema hash** (payload-schema contents, `MAX_POSITION_RANK`,
`VALUE_BLOCK_WIDTH`); flat nets gate on the **layout hash**;
`observation_field_uuids` dies with its producer; roster mismatch at cross-universe
load is loud (intersection load, both directions reported, payload-schema mismatch
refuses); cross-universe load resets optimizer, re-copies target, resets RND. RND: the
activity-mask constructor contract is **deleted, not defaulted**; RND consumes the
flat serialization. Transfer-contract test: two disjoint-vocabulary fixture universes;
train-step on one; weights load by type and forward cleanly on the other.
Permutation invariance re-pinned on the **mixed-type** set. Flat-view forward passes
for `feedforward`/`dueling` + layout-hash gate test. Training-dynamical diagnostics
that ride the net (per-type encoder grad norms, cold-token injection hook points) land
here as recorded metrics; the probe *experiments* (flat-vs-token A/B, mean-vs-attention
learning probe, slot-swap decode) are unit-4/5 scope per spec §6 and are named in the
task report as such.

### Task 10: The swap — sever, repair, green

**Files:** `src/townlet/environment/vectorized_env.py` (+ its observation encoder
module), deletions of the now-unproduced: `ObservationSpec`/`ObservationField`
(universe DTO), `ObservationActivity` + `curriculum_active`, raster/window encoders,
the temporal observation block, `vfs/observation_builder.py` spec/mirror halves,
`brain_config` recurrent/dueling wiring kept (flat view), `set_encoder` architecture
replaced by `token_set` in `set_encoder_smoke` (full pack migration is unit 5; this
pack moves now because its architecture dies with `SetEncoderQNetwork` only in unit
6 — at this task it switches to `token_set` to stay a live exerciser), every
`total_dims` consumer re-pointed at the serialization width.

**Contracts:** old path severed in one task; suite repaired to green **within** the
task; mypy clean; the full deletion sweep (dead networks, `ScopedVariableRegistry`,
`dynamic_needs.py`) stays **unit 6** — this task deletes only what the swap orphans
in-place (wire-or-delete, no dual-carry, no dead re-exports). Comment-242 item 6
(extract the duplicated global/agent evaluation+write-back block) executes during this
rewrite. POMDP levels: same TokenSpec + radius filter; L2/L3 run token-flat until
unit 4 (they run feedforward today — census). No `grid_encoding`, `local_window`,
`temporal`, `affordance_at_position` field survives anywhere in `src/townlet/`.

### Task 11: Adjudication, DIV-008 binding, docs — the unit lands

**Contracts:**
1. **Measure the movers** (DIV-009 worktree method) old-tree vs new-tree per cell;
   finalize DIV-008's declared hash fields to exactly the measured set; bind the cells
   (composed with DIV-006/009/010 refs where they stand).
2. **Matrix, both modes:** scripted mode is the criterion — `actions`/`rewards`/`dones`
   byte-exact on every cell, `obs` `DIVERGED_AS_REGISTERED`; plain mode recorded
   beside it. Exit 0 both modes, run ids into the commit and the register entry.
3. **RND distribution comparison (spec §3b):** intrinsic-reward distribution on
   identical states pre/post cut, measured and recorded (an artifact under
   `docs/product/baselines/2026-08-l2-preraster/` beside the curves it complements).
4. **Docs at gate-2 standard:** CLAUDE.md (superset+mask teaching → TokenSpec;
   "ask the compiled artifact" survives, allocated-vs-active dies),
   `docs/config-schemas/` (vfs-profiles exposure+normalization, effects
   `max_active_effects`, brain `token_set`), README observation claims, memory file
   `observation-is-a-superset-with-an-activity-mask.md` superseded.
5. **Tracker:** discharge-vehicle tickets closed with mechanism evidence
   (`hamlet-b8ad2ffcd6`, `-d97b4d6b4a`, `-d970ef83f0`, `-88578e629e`, `-0ddc83e377`,
   `-6a6e104523` per its Task-5 decision, `-702ae15f82` preflight half,
   `-81942565ff`, `-83a043a9b9` observation half, `-bf42ac60b5` observation half,
   `-c7084169f7` audit half); unit-3 completion comment on `hamlet-fa6bb6da4a`;
   PDR at checkpoint.

---

## Self-review (run at write time)

- **Spec coverage:** §6.3's three clauses → Tasks 1–2 (baselines), 4+11 (DIV-008
  record-then-bind), 5–10 (the cut's enumerated contents: TokenSpec ✓ T6, publishers ✓
  T8, widened scope DTO ✓ T5, explicit exposed_to ✓ T5, required normalization ✓ T5,
  set_engine_value ✓ T5, checkpoint gates ✓ T9, `.compiled` schema ✓ T7, token-native
  net + flat view ✓ T9). §1 invariants → T6/T8 tests. §2 tables → T5/T6. §3 → T8.
  §3b → T9 (RND contract) + T11 (measurement). §4 → T9. §5 → T7 (hashes) + T4/T11
  (oracle). Test-strategy structural list → distributed T5–T10; training-dynamical
  probes explicitly split unit 3 (instrumentation) vs units 4/5 (experiments).
  Carry-forward comments 234/242: items 1,5 → T3; 3 → T4; 4 → T7; 2,3(step),6 → T8/T10;
  asserts → T3. Verify-at-implementation: vtc.py ✓ (zero hits, verified 2026-08-24),
  network callers ✓ (factory/dispatch only), shared-world home ✓ (deferred, capacity 0,
  Global Constraints), widths → T6, float32 → T8 comment.
- **Placeholder scan:** Phase 2 tasks are contract-fidelity by declared design (see
  "Plan staging"), with the expansion gate mandatory before execution — not TBDs.
- **Type consistency:** `TokenSpec` (T6) consumed by T7/T8/T9 under that name;
  `token_publishers.py` (T8) consumed by T10's encoder swap; `iqm` (T1) consumed by
  T2 and unit 4.

---

## Phase 2 re-sequencing addendum + Task 5 expansion (2026-08-24, pre-execution pass)

Recon (full dossier in the SDD workspace) settled the verify-at-implementation items
and **falsified one boundary in the original Task 5**: three of its items change
compiled output or refuse frozen fixture packs, so they cannot land pre-cut without
turning the matrix red on divergences DIV-008 does not yet bind. They move INTO the
cut. The others are verified behavior-neutral for every shipped and fixture pack and
stay in Task 5.

### What moves out of Task 5, and where

1. **Explicit exposure (delete the `["agent"]` default-injection)** → the cut
   (Task 10's adjudicated batch). Deleting the injection changes which variables are
   observed the moment it lands: 31 shipped profile variables, exactly ONE explicit
   `exposed_to` in the fleet (`trial_f_durability/vfs_profiles.yaml:22`), and the
   fixture packs (`items_smoke`, `effects_smoke`) rely on the injection for their
   observed profile variables — pre-cut deletion diverges the obs stream un-registered.
   Shipped-pack edits (adding the explicit `exposed_to` each author meant, or dropping
   exposure) land in the same cut window.
2. **Required `normalization` at exposure (+ boundedness/one_hot refusals on that
   surface)** → the cut. The requirement is exposure-keyed, so it is vacuous for
   fixtures only AFTER the injection dies — the two must land together.
3. **Required `max_active_effects` in effects.yaml** → the cut, with a Task 11
   consequence: `effects_smoke` is a FROZEN fixture that declares effects and cannot
   gain the block, so its new-side compile refuses — an honest `NEW_SIDE_ERROR`, not
   adjudicable by DIV-008 (which binds stream/hash divergence, not refusal).
   **Task 11 therefore includes the decision point: if any fixture cell refuses on
   required-field grounds, execute an oracle move-forward (the `PDR-0074` precedent —
   evidence re-earned at the new commit, fixtures re-frozen from the updated test
   packs, register entries re-stamped, matrix returned to AGREE).** This is recorded
   here so Task 11 walks into it deliberately, not surprised.

### Task 5 (re-scoped): behavior-neutral compile hardening — verified against the fleet

Everything below is verified neutral: zero shipped/fixture pack exercises the refused
or newly-guarded path (dossier, 2026-08-24). The matrix in both modes is the proof
obligation and runs at task end; ANY non-baseline verdict is a stop-and-report.

**5a. Effects DTOs get `extra="forbid"`** (`hamlet-88578e629e`):
`EffectDefinitionConfig` (effects_config.py:214) and `EffectsConfig` (:250) gain
`model_config = ConfigDict(extra="forbid")` (matching `CommandConfig:84`). Preflight:
grep every shipped AND fixture effects.yaml for keys outside the DTO fields before
landing; a stray key found is a pack bug fixed in the same commit (configs/ only —
a fixture stray key is a stop-and-report). The `observable=True` behavioral default
and `default=[]` idioms are recorded in the ticket but NOT changed here — removing a
default changes pack requirements, which is cut-scoped. The ticket stays open until
the cut finishes it; comment the partial discharge.

**5b. `set_engine_value` shape guard** (`hamlet-d970ef83f0`): registry.py:567-587
gains `value.shape != self._expected_shapes[variable_id] → ValueError` for ALL
variables (today only sparse-pair is checked; :583-586). Risk pre-checked at
implementation: run the full suite + matrix — any caller relying on the bypass is a
latent corruption this guard exposes; fix the caller in the same task if it is
engine code, stop-and-report if a fixture pack's runtime exercises it. Related
standing bug `hamlet-f54b887148` (global [B]-shaped tensor hard-fails) — read it
before implementing; if the guard's landing resolves or reshapes that ticket,
comment it.

**5c. Write-back unknown-id loudness** (`hamlet-0ddc83e377`): the three silent-drop
sites are all in vectorized_env.py (`_commit_vtc_transition_state` :1258-1260;
global-profile write-back :1094-1097; agent-profile write-back :1129-1131, whose
comment already defers to this unit). Unknown id → raise KeyError naming the id and
the write source. vtc.py and evaluator.py are already loud (dossier) — no change
there. Neutral because nothing currently hits the drop paths (the suite+matrix
prove it).

**5d. Widened scope DTO + scope-table refusals** (spec §2 table): the universe-layer
closed set lives at exactly three sites — `universe/dto/observation_spec.py:66`
(`Literal["global","agent","agent_private"]`), `universe/compilers/vfs.py:286`
(2-member), `universe/compilers/observation.py:403` (cast). Widen the DTO field to
the nine `VariableScope` members; implement the §2 table refusals so a variable of
scope affordance/pair/group/zone/message DECLARING EXPOSURE fails compile naming the
table (currently unreachable from any pack — vfs_profiles has only global/agent/item
blocks and variables_reference marks are half-dead per `hamlet-33e520cebd` — hence
neutral). `agent_private` stays representable in the DTO; its publisher filter is
Task 8. Table-test all nine rows.

**5e. Extents preflight two-liner** (`hamlet-702ae15f82` preflight half): add
`VariableScope.AFFORDANCE: "num_affordances"` to `_SCOPE_EXTENT_FIELD`
(vfs/schema.py:593-597). Crash window today: zero-affordance packs only.

**5f. `rank_scaled` ruling** (`hamlet-6a6e104523`): REFUSED at profile-variable
exposure (joins the §1 boundedness/one_hot refusal list — it is [0,1]-bounded but
ranks `dim=0` across causally-independent worlds and silently degenerates to
constant zero at batch 1; observation_builder.py:93-103). Zero shipped usages, so
refusal is neutral. Meter/`range_type` usage is NOT touched — a different surface
with its own record (`PDR-0057` executed it); the ticket gets the split ruling as a
comment. The kind is not deleted from the vocabulary while the meter surface
legitimately carries it.

**Task 5 sequencing gate (from the session ledger, binding):** no `src/townlet/` or
`configs/` edit until every baseline seed is TRAINED and GREEDY-EVALED (train copies
the pack at launch; eval runs on the current engine tree). The baseline record's
commit is the gate that opens this task.

**Tests:** one refusal test per rule naming the error text (5a stray key, 5b shape,
5c unknown id, 5d each refused scope row, 5f rank_scaled exposure); the nine-row
scope table test; full suite green; matrix exit 0 both modes with baseline verdict
composition unchanged.

### Consequential edits to later task contracts (supersede the original text where they conflict)

- **Task 10 (the swap)** additionally lands: the exposure-injection deletion + fleet
  `exposed_to` edits; required normalization at exposure + its refusal set (incl.
  one_hot, unbounded kinds, rank_scaled from 5f); required `max_active_effects` +
  the capacity denominators consuming it. These adjudicate under DIV-008 with
  everything else in the atomic knockdown.
- **Task 11 (adjudication)** additionally owns: the fixture-refusal decision point
  (oracle move-forward per `PDR-0074` if any fixture cell NEW_SIDE_ERRORs on
  required fields — expected: `effects_smoke` only), and re-verifying the DIV-008
  entry's fixture-exposure note against what actually happened.
