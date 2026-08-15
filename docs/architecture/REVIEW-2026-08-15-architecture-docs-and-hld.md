# Architecture documentation review — 2026-08-15

**Scope.** Every file in `docs/architecture/` except `archive/`. The 12 top-level documents were
read directly; `hld/01–12` + `hld/frontend-visualization.md` and the 13-section `hld/review/`
audit were reviewed by a 14-agent workflow, whose findings were spot-checked against source
before inclusion here. `hld.md` was not read separately — it is a compiled reading copy of the
`hld/` sources (49 `##` headings vs 131 across the split files; the difference is per-file
frontmatter — AI-Friendly Summary, Document Scope, Keywords — dropped during compilation, plus
the legacy-checkpoint guidance its own header says it omits). The `hld/` sources are therefore
the superset and were the ones reviewed.

**Ground rule.** Nothing below is stated as implemented unless someone looked at `src/townlet/`
or `configs/` and saw it. Document claims are treated as design intent, never as facts about the
running system. Items where verification was not possible are labelled **unverified**.

---

## 1. The headline

`docs/architecture/` describes, in detail and with an approving tone, a system that was largely
not built — and it does so without a single "historical" or "superseded" banner anywhere.

The single largest block of it — Brain as Code: three cognitive YAML layers, `factory.py` /
`graph_agent.py` / `graph_executor.py`, `EthicsFilter`, `panic_controller`, the cognitive hash,
the five-file run bundle, `config_snapshot/` provenance, the glass-box telemetry schema — has
**zero footprint in `src/townlet/`**. Not partial, not renamed: zero grep hits for
`execution_graph`, `cognitive_topology`, `agent_architecture` in either `src/` or `configs/`.
`BRAIN_AS_CODE.md` and `hld/02-brain-as-code.md` both carry the header *"Status: Approved for
Implementation."*

That is roughly 3,500 lines of the ~12,600 in scope, plus most of `hld/03`, `04`, `05`, `06`,
`07`, `10`, `11`, `12`, plus the sections of the review audit written to govern it. The
governance story the project tells about itself rests entirely on this apparatus.

Meanwhile the subsystems that *do* exist and are under active development —
`src/townlet/oracle/` (the WS-7 freeze/oracle infrastructure), the strangler/divergence method
the last several commits are built around, `src/townlet/items/`, `src/townlet/effects/` —
appear in **no document under `docs/architecture/`**. (They are covered elsewhere: `README.md`
and `docs/oracle/ORACLE.md` describe the strangler rewrite and the pinned oracle accurately.
The gap is specifically that `docs/architecture/` has not been updated to know about them.)

**The framing authority is `README.md`, not this directory.** README states the pivot in one
line — *"from game as experience to writing a game as experience"* — names authoring as the
point, and correctly demotes the survival world in `configs/default_curriculum` to "the first-class
demonstration of that idea, not the product itself." It is also honest about status (pre-release,
mid-strangler, CI never run on this branch). Where `docs/architecture/` disagrees with README,
README is right and `docs/architecture/` is the document to fix.

The two VFS documents (May 2026) are the exception and the model: source-mapped, dimension-literal-free,
with an explicit "current boundaries" section.

**This is not an indictment of the design.** Per the project owner, the corpus documents a
deliberate pivot to a higher level of abstraction; the documentation simply never landed before
the project went on hold. The problem is therefore narrow and fixable: the documents assert
*completion* they never had. Every finding below should be read as "intent, mislabelled as
record" rather than "wrong design" — see §5.

---

## 2. Top-level documents

### 2.1 Vintage

Only `vfs.md` (2026-05-15) and `vfs-current-implementation.md` (2026-05-16) postdate 2025-11.
Everything else predates the recovery branch by 6–9 months.

### 2.2 Verified doc-vs-code gaps

Checked directly on branch `project-recovery`, 2026-08-15:

| doc claim | reality |
|---|---|
| `cues.yaml` is a first-class UAC input (COMPILER_ARCHITECTURE §2, §5; COMPILER_HAMLETCONFIG_INTEGRATION; `hld/review/review-06` entire) | No `cues.yaml` file exists — cues moved *inline* into `environment.yaml`, and are authored in **24 packs including `configs/default_curriculum`**. But see §4.4 item 4: they are authored in a schema the compiler does not accept, and `CuesCompiler` is instantiated at `universe/compiler.py:69` and never called. |
| `cascades.yaml` defines cross-meter dynamics; `CascadeEngine` applies them (UNIVERSE_AS_CODE §4, §12) | No `cascades.yaml` anywhere; no `CascadeEngine` in `src/townlet`. Threshold cascades now compile through VTC. |
| `reward_model` computes end-of-life score (UNIVERSE_AS_CODE §2) | No such module. DAC/`drive.yaml` owns reward. |
| `VectorizedTownletEnv` is the runtime class (UNIVERSE_AS_CODE, ~6 references incl. code snippets) | Class is `VectorizedHamletEnv`. The named class does not exist. |
| `substrate.yaml` (every doc showing a pack layout) | Real packs use `stratum.yaml`. `substrate.yaml` survives only in `configs/test/items_smoke/`. |
| `variables_reference.yaml` is REQUIRED in all packs (CLAUDE.md) | Not present in `configs/default_curriculum/`. `vfs.md` correctly says it is optional and `vfs_profiles.yaml` is the required file. **CLAUDE.md is the stale document here.** |
| Social-residue rules come from experiment-level `transition_rules.yaml` (vfs-current-implementation) | No `transition_rules.yaml` anywhere in `configs/`. The compiler, its phase, and its contribution to `transition_graph_hash` are real machinery with nothing to compile. |
| `clamp_and_validate` phase enforces bounds (implied by vfs-current-implementation's phase graph) | Phase is declared and empty; bounds are hardcoded in 7 places (filigree `hamlet-f46e2b381a`). The doc is right about the graph, misleading about what it does. |

### 2.3 Doc-vs-doc contradictions

These are wrong *before* you compare them to code — the documents disagree with each other.

1. **Two incompatible affordance sets.** UNIVERSE_AS_CODE §5 ships 15 named affordances
   (bed, luxury_bed, shower, home_meal, fast_food, job, labor, gym, bar, park, recreation,
   therapist, doctor, hospital, call_ambulance). GLOSSARY lists a *different* 14 (…Restaurant,
   Phone, Mall, SocialEvent, Couch, Fridge). About eight names overlap. COMPILER_ARCHITECTURE
   §3.2 hardcodes `dims=15` for the one-hot. CLAUDE.md says 14.
2. **Three incompatible observation-dimension tables.** COMPILER_ARCHITECTURE: L1=29, L2=54.
   `vfs.md` §2.3: L0_0=38, L0_5=78, L1=93, L2=54, L3=93 — labelled *"Validated"*. CLAUDE.md says
   every such literal is wrong by ~4× and only the compiled artifact is authoritative. (A status
   agent reading the artifact reported 124 for the real 8×8 grid; treat that as one reading, not
   a new literal to write down.) Two of the three tables assert numbers as fact; at most one can
   be right.
3. **Three incompatible curricula.** TRAINING_LEVELS defines L1–L6. TOWNLET_CURRICULUM_V4
   defines L0–L8 with different content at every number. GLOSSARY defines L0/L0.5/L1/L2/L3.
   `hld/review/review-04` uses L0–L8. "L1" means three different things across four documents,
   and GLOSSARY flags only the *BAC-layer-vs-level* ambiguity, not this one.
4. **Money is normalised vs money is not.** UNIVERSE_AS_CODE is emphatic — all values in [0,1],
   money 1.0 ≈ $100, clamped every tick, loader rejects any other range. `hld/08` repeats it as
   an absolute framework rule. `hld/09`'s own worked example costs an ambulance `-3.00` against
   that bar. Per CLAUDE.md, WS-1(e) (2026-08-12) *removed* six hardcoded [0,1] clamps precisely
   because they crushed WORK's payout, and `money.bounds.max` is 999999.0. The UAC document's
   central numeric invariant is the bug that was fixed.
5. **"Exactly eight bars, indices 0–7, a ninth is rejected"** (UNIVERSE_AS_CODE §9) versus VFS,
   where bars are ordinary variables and the whole point is a software-defined need set
   (`vfs.md` §15: "bars are variables, not the whole ontology"). Opposite claims about the same
   ABI, both presented as current.
6. **Two provenance schemes, never reconciled.** BRAIN_AS_CODE hashes *concatenated raw YAML
   text* (so a comment change forks the run). VFS hashes *structure* (`variable_schema_hash`,
   `observation_schema_hash`, `action_schema_hash`, `transition_graph_hash`, `vfs_hash`). No
   document says which won, or how `cognitive_hash` relates to `vfs_hash` / `drive_hash` /
   `brain_hash`.

### 2.4 Design weaknesses independent of staleness

- **COMPILER_ARCHITECTURE §9.2 makes "existing config packs work without modification" a
  success criterion.** CLAUDE.md's first rule is zero backwards compatibility. The document's
  own acceptance gate is now a project anti-pattern. Same for `frontend-visualization.md`'s
  "Backward Compatibility" section.
- **COMPILER_ARCHITECTURE treats reward as a hypothetical future extension** (§7.1 "Adding
  RewardCompiler… make reward.yaml optional with sensible defaults"). DAC shipped as a
  *required* per-level `drive.yaml` with a hard `drive_hash`. The doc's extensibility example
  is the thing that got built, built the opposite way.
- **BRAIN_AS_CODE §13.1 leaves ethics-vs-panic ambiguous by its own admission** ("leaving the
  rule ambiguous creates governance risk") and ships anyway. This is the same item the HLD
  review raises as BLOCKER 1.
- **TOWNLET_CURRICULUM_V4.md is a chat transcript filed as architecture** — opens "Here is the
  fleshed-out curriculum… This is a fantastic pedagogical roadmap", has a header typo
  ("fLevel 2"), specifies 5×5 grids against a pack whose grid is fixed 8×8 pack-wide. Its
  *content* is nonetheless the clearest statement of pedagogical intent in the repo, which is
  exactly why it deserves rewriting as a real spec (filigree `hamlet-e979f2ba37`).
- **TRAINING_LEVELS.md is unrunnable as written** — every config path
  (`configs/level_1_full_observability.yaml`) is a flat file that does not exist; it invokes
  `scripts/start_training_run.py`. Its "✅ Implemented" ticks are the most actively misleading
  claims in the directory.
- **ROADMAP.md is a different project** — "Phase 3 Complete", next action "execute multi-day
  demo", POMDP as future work, decision log stops 2025-10-30.
- **substrate-system.md is the only small, honest top-level doc.** One fix needed
  (`substrate.yaml` → `stratum.yaml`) and it stands.

---

## 3. The HLD (`docs/architecture/hld/`)

### 3.1 What it commits to

1. BAC replaces the monolithic Q-network with three YAML layers fully specifying cognition.
2. **EthicsFilter is the final, unbypassable gate**: `hierarchical_policy → panic_controller →
   EthicsFilter`; panic escalates, never overrides ethics.
3. A single **cognitive hash** over frozen config + compiled execution graph + instantiated
   architectures is the complete identity of "this mind in this world", stamped on every tick.
4. The **frozen `config_snapshot/` is the only runtime read source** — never live `configs/` —
   specifically to block mid-run hotpatching of ethics rules.
5. Checkpoints are self-contained five-component artifacts sufficient for exact stochastic resume.
6. **Resume always forks** on any snapshot edit — new run folder, new hash, no silent drift.
7. Goals and termination are a bounded declarative DSL (`all`/`any` over bars and elapsed ticks).
8. Affordances are declarative bar-effect contracts with ephemeral per-tick reservation and
   deterministic contention tie-break.
9. **Live UI and disk telemetry must always agree** — divergence is defined as a defect.
10. **Foundation-first build order**: snapshot → agent → hash → checkpoint *before* telemetry and
    ethics. Provenance is explicitly declared non-retrofittable.
11. Three-axis, all-or-nothing acceptance: technical + pedagogical + governance together.

Commitments 1–6 and 9–11 have no implementation. 7 and 8 have partial analogues in DAC and VTC
that do not match the documented shapes.

### 3.2 Where the HLD is weak — worst first

**High**

- **The whole 5-file provenance apparatus (03, 04, 05, 06, 10–12) describes something with zero
  code footprint, and no document flags it as historical.** The real pack layout shares no
  filename with `configs/<run_name>/`'s five YAMLs.
- **EthicsFilter-last is asserted as an absolute invariant and contradicted as a reconfigurable
  knob in the same document.** `hld/06` §6.4 says panic can never bypass ethics. §6.5, under
  "Experimental Velocity Without Governance Chaos", lists as a routine researcher edit
  (verified verbatim, `06-runtime-engine-components.md:396–460`):

  > **Reorder panic/ethics in execution graph**:
  > - Edit `execution_graph.yaml` (ethics before panic instead of panic before ethics)
  > - Factory recomputes hash → new run folder, new hash
  > - **Likely result**: Ethics blocks panic escalation, agent dies more often

  It is offered alongside "swap GRU for LSTM" as an ordinary ablation, with a casual behavioural
  prediction and no mention that it inverts the document's own safety invariant. A safety
  invariant that the same document lists as a one-line config experiment is not an invariant —
  it is a default. Decide which it is; if it is an invariant, the graph validator must reject
  the ordering.
- **Cognitive hash scope is self-contradictory.** `hld/01` §1.3's snapshot list implies one
  combined hash; the same section's accountability example treats "mind hash" and "world
  snapshot id" as two identifiers. And the hash's second input — "the compiled cognition
  graph" — is never defined: no compiler, no compilation stage, no canonicalisation, no digest
  length. Every governance claim rests on an artifact that is never specified.
- **The checkpoint directory tree is drawn two contradictory ways** between `hld/03` §3.3 and
  `hld/04`. `full_cognitive_hash.txt` is inside `config_snapshot/` in one and a sibling in the
  other. An engineer implementing from these builds the wrong thing either way.
- **Snapshot immutability is asserted and then contradicted in the same doc set.** `hld/03`
  §3.2 guarantees the runtime reads only frozen launch-time config; `hld/04` §4.4's
  curriculum-evolution example has `universe_as_code.yaml` legitimately differing between
  checkpoints *within one run*. Either the snapshot is not immutable or curriculum mutates
  through an unspecified side channel.
- **`hld/08`'s "all bars normalized 0.0–1.0"** is falsified by `hld/09`'s own worked example and
  independently by `money.bounds.max: 999999.0`.
- **`hld/09`'s affordance reservation model contradicts its own examples twice**: "ephemeral,
  per-tick, no persistent ownership state" is incompatible with the multi-tick sleep example
  spanning ticks 840–842; and `bed_basic` is declared `distance_limit: 0` while the canonical
  contention example has a contender at distance 1 — ineligible under the affordance's own
  definition three sections earlier.

**Medium**

- EthicsFilter's veto *fallback* action is never specified — the one detail governance review
  would ask for first.
- `compliance.penalize_actions` is declared in Layer 1 and never wired into the execution graph.
- `meta_controller_period: 50` is irreconcilable with a DAG that runs every step every tick.
- "UI and disk always agree" is asserted by fiat alongside undefined IO batching with no
  crash-mid-batch story; telemetry write-path ownership is never assigned (executor vs logger
  vs env loop) — exactly the dual-writer gap that produces the divergence being ruled out.
- `action_space_dim: 6` contradicts the real 8-action Grid2D vocabulary.
- `@modules.*` vs `@services.*_service` binding namespaces are used inconsistently, unexplained.
- Recurring Factory/Trading-universe framing across 10/11/12 is unfalsifiable padding — neither
  exists anywhere in the repo.

---

## 4. Outstanding actions from `hld/review/`

The 13-section review (2025-11) yielded **72 discrete actions**; **71 were status-checked
against source** (one produced no verdict). Result: **46 OUTSTANDING, 12 PARTIAL, 14
DONE/OBSOLETE**, with several near-duplicates merged.

Note on the OBSOLETE bucket: nine items were marked obsolete *because the components they would
govern (EthicsFilter, panic_controller, `cognitive_topology.yaml`, social_model_service) do not
exist*. Under the revival framing in §5 those are **not obsolete — they are pending**, and
should be re-read as acceptance criteria for building BAC rather than as closed.

### 4.1 Titled blockers — all seven still OUTSTANDING, none tracked

| id | area | evidence |
|---|---|---|
| ethicsfilter-deterministic-controller | governance | Zero hits for EthicsFilter/panic anywhere; no execution graph to wire into |
| ethicsfilter-docs-and-tests | governance | Docs still say "Approved for Implementation"; no ethics test exists |
| checkpoint-signing-key-management | provenance | No key loading anywhere; the HMAC signing it serves doesn't exist |
| curriculum-fork-vs-pressure-rule | curriculum | See §4.2 — confirmed live |
| world-fork-validation-test | curriculum | No `world_config_hash` emitted to test against |
| world-config-hash-observation | observation | Zero hits; the VFS global-scope pattern exists to build it on |
| fix-order-and-week1-plan | process | No epic encodes the review's fix order |

Five of the seven are moot unless BAC is actually built. Two — the curriculum fork rule and
`world_config_hash` — are live and cheap.

### 4.2 The one finding I'd act on this week

**`AdversarialCurriculum` mutates world physics at runtime, from hardcoded Python, with no
config, no hash, and no fork gate.** Verified directly:

- `src/townlet/curriculum/adversarial.py` defines `STAGE_CONFIGS` as a **module-level Python
  constant**: five stages, each carrying `active_meters`, `depletion_multiplier`, and
  `reward_mode`.
- `depletion_multiplier` reaches the environment at
  `src/townlet/population/vectorized.py:738` → `envs.step(actions, depletion_multiplier)`.

So depletion rate — world physics — changes mid-run by stage, sourced from Python constants that
no config pack can express and no hash covers. That is simultaneously:
- the governance hazard the review flagged (world-rule mutation that should force a fork),
- a direct contradiction of the "physics are data" thesis every UAC document opens with,
- and a live blind spot in checkpoint provenance: two checkpoints from the same run can have
  had different physics with identical hashes.

Related: `reward_mode: 'shaped'|'sparse'` is still carried in `StageConfig` and regex-validated
in `training/state.py:187`, but I found no consumer in the reward path — DAC/`drive.yaml` owns
reward now. Looks like vestigial surface from the deleted RewardStrategy era; worth confirming
before deletion.

### 4.3 Corrections to the workflow's own verdicts

Three verdicts did not survive spot-checking and are corrected here:

- ❌ *"No capacity/occupancy concept in the affordance engine at all."* **Wrong as stated.**
  `claim_if_free` and `capacity_claim` compositions exist in `src/townlet/vfs/vtc.py`
  (lines 526–571), including affordance-scoped claim variants. The *legacy affordance engine*
  has none — the capability moved to VTC. Two agents in the same run gave contradictory answers
  on this; VTC is the correct one.
- ❌ *"`_persist_config_snapshot()` writes the copy but **training** still reads live
  `configs/`."* **Misattributed.** The snapshot writer lives only in
  `src/townlet/demo/unified_server.py`; it is not in the training path at all, and nothing
  anywhere reads a snapshot back. Corrected framing in §4.4 item 2.
- ❌ *"Cues schema and validator exist but are never invoked; no shipped `cues.yaml` anywhere."*
  **True but badly misleading.** Cues *are* authored — inline in `environment.yaml` across 24
  packs including `default_curriculum` — in a schema the validator would reject. The right
  conclusion is the opposite of "delete it". Corrected in §4.4 item 4.

Also flagged **unverified** by the workflow itself and left that way: `frontend-visualization.md`'s
`"type": "grid2d"` wire-protocol literal, and whether checkpoint security docs exist.

### 4.4 Untracked work worth filing

Highest value first, blockers excluded (they need the BAC go/no-go decision first):

1. Gate `AdversarialCurriculum`'s world-rule mutations behind a fork/hash rule — closes two
   review actions at once (`curriculum-fork-vs-pressure-rule`, `curriculum-pressure-vs-world-fork-enforcement`).
2. `config_snapshot/` has a writer and no reader. Corrected from the workflow's framing after
   direct check: the string appears in exactly one module, `src/townlet/demo/unified_server.py`
   (`_persist_config_snapshot` at :97, called at :136). It is **not in the training path at
   all**, and no code anywhere loads a snapshot back. So the `hld/03` provenance guarantee —
   "the runtime reads only the frozen snapshot" — is not weakly enforced; it is unimplemented,
   and the one place that writes a snapshot is the demo/inference server.
3. Add `world_config_hash` as a global-scope VFS variable — unblocks the fork-detection test.
4. **Cues exist in three mutually incompatible forms.** Verified directly:
   - **Authored**: a `cues:` block inside `environment.yaml` in 24 packs, including
     `configs/default_curriculum/environment.yaml` — shape is
     `name` / `trigger{bar,threshold,direction}` / `display{icon,color,message}`, i.e.
     presentation cues.
   - **In code**: `config/cues.py` + `universe/cues_compiler.py` expect a *different* shape
     (`cue_id`, `condition.meter`, simple vs compound cues), with symbol-table registration at
     `symbol_table.py:81-83`. `CuesCompiler` is instantiated at `compiler.py:69` and the
     attribute is never read again.
   - **In the docs**: behavioural Theory-of-Mind cues (`observable_effects`,
     `movement_speed_modifier`, `limping`) matching neither of the above.

   Nothing consumes cues at runtime in any form. This is not "documented but unshipped" — it is
   authored content in the shipped curriculum pack that no code path reads, against a validator
   that would reject its schema if it were ever called. Pick one shape, wire the compiler call,
   or delete two of the three. **Do not simply delete the code** — the declarations exist.
5. Decide affordance capacity/occupancy semantics at the *engine* level now that VTC has the
   primitive (`hamlet-7391dc697a` covers contention but not the semantics).
6. Instrument graduation criteria (retirement rate, navigation success, coordination gain) —
   zero instrumentation exists for any curriculum level, so no level's success criteria can be
   evaluated.
7. Fix `hld/review/review-05`'s obs-dim formulas (assume a 5×5 grid that does not exist) and its
   `vision_range` unit assumption (it is a normalized [0,1] fraction, not a cell radius).

Explicitly **not** worth filing yet — all blocked on absent foundations: population-genetics
dynasty/polygamy/arranged-marriage configs, family lifecycle state machine, child inheritance
modes, cue-transparency research configs, L4–L8 graduation validation, truthfulness-index metric.

Already tracked and correctly so: `hamlet-e979f2ba37` (curriculum authoring),
`hamlet-0d0115383e` (per-level architecture), `hamlet-ae6601e463` (hashes),
`hamlet-7391dc697a` (contention), `hamlet-d5cb2dd4e7` (checkpoint digest),
`hamlet-0dd4ac24d9` (presentation), `hamlet-15050f280a` (retirement mechanics),
`hamlet-ad2773718a` (UAC foundations).

---

## 5. Recommendation

**Framing (from the project owner, 2026-08-15):** these documents are a deliberate pivot to a
higher level of abstraction. The pivot was real and intended; the documentation never landed
before the project went on hold, and the work is now being revived. **VFS, Universe as Code, the
substrate system, Brain as Code and the generic compiler are the way forward** — the project has
evolved from a DRL tech demo into *a rapid DRL experimentation framework for game designers*.

Three consequences for how this review should be read:

1. **The corpus is the product spec, not legacy.** Nothing here recommends retiring it.
2. **The authoring surface is the product.** Every finding where behaviour can only be expressed
   in Python is therefore a product defect, not a tidiness issue — §4.2 (`STAGE_CONFIGS`
   hardcoding depletion rates) is the clearest example, and it is worse under this framing than
   under a governance framing, because a designer cannot author around it.
3. **"Townlet Town" is a sample game, not the deliverable.** GLOSSARY's framework/instance
   boundary is the right instinct and should be enforced harder: several documents still
   describe instance content (14-vs-15 affordances, the 8-bar ABI, the town map) as if it were
   framework. Under a designer-facing framework those are *example pack* content, and freezing
   them into the framework is the thing that will bite.

That changes the disposition materially. The gap is **not** "docs describe a road not taken" —
it is **"intent that never got built, still asserting it was."** Which means:

- Do **not** archive the BAC/UAC design corpus. It is the specification of where the project is
  going, and it is the only written record of that intent.
- **Do** strip the false completion signal. `BRAIN_AS_CODE.md` and `hld/02` say *"Status:
  Approved for Implementation"*; `hld/10` lists success criteria as if they gate a build in
  progress; `TRAINING_LEVELS.md` carries "✅ Implemented" ticks against config paths that do not
  exist. That is what makes the corpus dangerous rather than merely aspirational — a reader
  (human or agent) cannot tell intent from record, and CLAUDE.md's own stale entries show the
  cost compounding.

So the disposition is **status-correction, not retirement**:

- **Banner as `Status: Design intent — not yet implemented`, with a dated "as-built delta"
  section:** `BRAIN_AS_CODE.md`, `COMPILER_ARCHITECTURE.md`, `hld/02`–`hld/06`,
  `hld/10`–`hld/12`. The delta names what landed (compile-once immutable artifacts, provenance
  hashing, the declarative world, VFS/VTC as the transition layer) and what did not (the three
  cognitive layers, `EthicsFilter`, `panic_controller`, the five-YAML run bundle, the cognitive
  hash). Keep the design prose intact — it is the target.
- **Same banner, plus reconciliation against VFS:** `UNIVERSE_AS_CODE.md`. Its world model
  ([0,1] money, eight fixed bars, `cascades.yaml`, `CascadeEngine`, `VectorizedTownletEnv`) has
  been superseded *by a later part of the same pivot*, not abandoned — VFS/VTC is where those
  concepts went. Say so explicitly; the successor is already documented.
- **Archive:** `ROADMAP.md`, `TRAINING_LEVELS.md` — these are pre-pivot, not unlanded pivot.
  They describe the phase-based project the abstraction pivot replaced.
- **Convert the review's blockers from "moot" to backlog.** §4.1 reads them as mostly moot
  *because* BAC does not exist. Under revival that inverts: five of the seven are the acceptance
  criteria for building BAC, and they should be filed against the BAC epic rather than dropped.
- **Correct in place:** `substrate-system.md` (`stratum.yaml`), `GLOSSARY.md` (affordance list,
  level vocabulary, version header), `COMPILER_HAMLETCONFIG_INTEGRATION.md` (cues, flat pack
  paths), `hld/08` (money bounds), `hld/09` (reservation model, `distance_limit`), `hld/10`
  §10.3 (real symbols annotated with fabricated field names — the most misleading citation in
  the set).
- **Rewrite as intent, clearly labelled:** `TOWNLET_CURRICULUM_V4.md`.
- **Keep as current:** `vfs.md`, `vfs-current-implementation.md`, `substrate-system.md`.
- **Annotate:** `hld/review/*` with current filigree status — roughly a third of it is already
  tracked or resolved, so it reads as a larger open backlog than it is.
- **Write what's missing:** nothing in `docs/architecture/` describes `src/townlet/oracle/`,
  the strangler/divergence method, `items/`, or `effects/`. The architecture the project is
  *currently building* is undocumented.

Filigree `hamlet-7a52a63e0b` ("Replace stale architecture and workflow docs with source-derived
facts") is the issue this belongs to; it is P1 and ready.

---

*Method: 12 top-level docs read directly; `hld/` and `hld/review/` reviewed by 14 Sonnet agents
(1.1M tokens, 248 tool calls, ~17 min) across read → status-check → synthesise phases, with all
status verdicts required to cite file paths and symbols. Every claim carried forward into this
document was then spot-verified by hand: the BAC zero-footprint headline, the `config_snapshot`
write/read paths, the `hld/06` §6.5 reorder example (quoted verbatim), the `hld/09`
`distance_limit`/`-3.00` declarations, the cues declarations across 24 packs, and the
`AdversarialCurriculum` → `envs.step(actions, depletion_multiplier)` trace. Three relayed
findings did not survive that check and were corrected (§4.3, §4.4 items 2 and 4). Raw workflow
output:
`/tmp/claude-1000/-home-john-hamlet/5b2c3c08-ebdd-4476-b500-d5f308e52dd8/scratchpad/hld-review-report.md`.*
