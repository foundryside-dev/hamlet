# 04 — Final Architecture Report: Townlet

**Date:** 2026-05-16
**Repository:** `/home/john/hamlet`
**Primary package:** `townlet` (0.1.0 alpha)
**Scope:** Whole-repository architecture analysis, derived **from source only** (per user
directive — documentation is stale and not used as authoritative evidence).
**Method:** Eight parallel `codebase-explorer` subagents → consolidated catalog → independent
validator gate → diagrams + quality + security in parallel → this synthesis.

---

## Executive summary

Townlet is a **GPU-native vectorized Deep RL training framework** built around a declarative
"universe compiler" pattern: every aspect of an environment (variables, observation spec,
substrate, affordances, effects, items, reward function, curriculum) is described in YAML, type-
checked by Pydantic v2, compiled into a frozen `CompiledUniverse` DTO at startup, and then
executed against torch tensors in a 16-stage tick loop. A web UI streams live training state to a
Vue dashboard over WebSocket at 5 Hz.

**State of the codebase.** Disciplined in architecture, **incomplete in follow-through**.

- ✅ **Architecture is coherent.** Eight subsystems with clear responsibilities, internally
  consistent dependency graph (no cycles), declarative-data-driven design, comprehensive Pydantic
  DTO surface, sound checkpoint provenance (four-hash compatibility pipeline).
- ✅ **Tooling is configured.** Ruff + Black + mypy + pytest + coverage + pre-commit + 4 GitHub
  Actions workflows + custom `no_defaults_lint` AST walker.
- ⚠️ **Discipline is half-applied.** ~15 dead-code / orphan items remaining despite an explicit
  "zero-backwards-compat" rule in CLAUDE.md and AGENTS.md.
- ⚠️ **Documentation is rotting.** 12 specific CLAUDE.md drifts confirmed (e.g., wrong config
  layout, wrong file names, missing exploration files, missing `frontend/package.json`).
  The test README has now been rebaselined to measured counts and a **19%** local coverage
  artifact, but the wider doc set remains stale.
- ⚠️ **One real security issue.** Demo loads checkpoints with `weights_only=False` and
  `verify_checkpoint_digest(..., required=False)` — RCE via tampered checkpoint under the
  service user.

The user's instinct to **recreate the documentation set** is correct. This analysis is the
source-of-truth foundation for that recreation.

---

## 1. What Townlet is

### 1.1 Purpose

A pedagogical Deep RL platform. The stated mission (`pyproject.toml`,
`CONTRIBUTING.md`): "trick students into learning graduate-level RL by making them think they're
just playing The Sims." The framework deliberately produces "interesting failures" (reward
hacking) as teaching artefacts.

### 1.2 What it does at runtime

```
Operator                                          Vue Frontend (browser)
   │ scripts/run_demo.py                                  │
   ▼                                                      ▼ ws://host:8766/ws
┌─────────────────────────────────────┐         ┌─────────────────────┐
│ UnifiedServer (one process)         │ <─poll──┤ LiveInferenceServer │
│ ┌──── training thread ─────────┐    │  fs     │ (FastAPI, uvicorn)  │
│ │ DemoRunner.run               │    │ ckpt    │ + LiveInferenceWorker│
│ │   loop:                      │    │ ─────►  │   5 Hz broadcast    │
│ │     VectorizedPopulation     │    │         └─────────────────────┘
│ │       .step_population()     │    │
│ │         → VectorizedHamletEnv│    │
│ │            .step()           │    │
│ │              (16 stages,     │    │
│ │               GPU tensors)   │    │
│ │     checkpoint every N eps   │    │
│ └──────────────────────────────┘    │
└─────────────────────────────────────┘
                              │ records
                              ▼
                  runs/<level>/<run>/{checkpoints/, episodes/, telemetry/}
```

### 1.3 What it does at startup

```
configs/<pack>/                                     CompiledUniverse
    ├── stratum.yaml                                  ├── primary_level metadata
    ├── environment.yaml                              ├── compiled VFS (8 VTC programs)
    ├── actions.yaml                                  ├── compiled EffectCatalog
    ├── brain.yaml                                    ├── action metadata
    ├── items.yaml             ┌──────────────┐       ├── observation spec
    ├── effects.yaml        ──►│  UAC         │──►    ├── 7+ provenance hashes
    ├── vfs_profiles.yaml      │  (9 stages)  │       │   (config, drive, brain, vfs,
    └── levels/<L>/            └──────────────┘       │    actions, effects, transition_graph)
        ├── curriculum.yaml      Pydantic → SymbolTable │
        ├── bars.yaml            → validators        ──┘
        ├── affordances.yaml     → compilers           │ frozen, content-addressed
        ├── drive.yaml           → emit/cache          ▼
        └── training.yaml                          VectorizedHamletEnv
                                                      DACEngine
                                                      VectorizedPopulation
```

---

## 2. Architectural shape

### 2.1 Eight subsystems

| ID | Subsystem | LOC | Role | Pattern |
|----|-----------|----:|------|---------|
| SG1 | Universe Compiler | 5,750 | YAML → frozen `CompiledUniverse` | Pipeline + visitor over symbol table |
| SG2 | VFS | 7,080 | Declarative state + access control + tick-time transitions | Compiled-rule registry + TorchScript kernels |
| SG3 | Config DTOs | 4,728 | Pydantic v2 schema for every YAML | One file per logical schema |
| SG4 | Environment & DAC | 5,041 | Tick loop + reward engine | Vectorised env wrapper over compiled artefacts |
| SG5 | Substrate & World DSL | 6,831 | Spatial topologies + expression language | ABC+factory (substrate); parser/AST/eval (DSL) |
| SG6 | RL Training Stack | 6,427 | Networks, replay, exploration, curriculum, population | Strategy + factory; Double DQN supported |
| SG7 | Effects & Items | 4,480 | 10-command state-mutation DSL + tensor-backed inventory | Compile-pre-parse, runtime execute |
| SG8 | Demo / Recording / Frontend | ~14,800 | UnifiedServer + WebSocket + Vue dashboard | 2-thread server, filesystem-as-IPC, Pinia store |

(Full per-subsystem detail in `02-subsystem-catalog.md`; per-file detail in `temp/sg{1..8}-*.md`.)

### 2.2 Layering

```
┌── data (declarative) ───────────────────────────────────┐
│ configs/<pack>/   ← YAML; one pack per experiment       │
└────────────┬────────────────────────────────────────────┘
             │ Pydantic v2
             ▼
┌── DTOs (SG3) ───────────────────────────────────────────┐
│ 142 BaseModels, extra="forbid", no shared base         │
└────────────┬────────────────────────────────────────────┘
             │ aggregate
             ▼
┌── Compile-time (SG1) ───────────────────────────────────┐
│ RawConfigsV21 → 9-stage pipeline → CompiledUniverse     │
│ Validators: feasibility / limits / semantics / references│
│ Sub-compilers: VFS / Actions / Effects / Observation /  │
│                Metadata / Optimization / Cues(orphan)   │
└────────────┬────────────────────────────────────────────┘
             │ frozen dataclass with 7+ provenance hashes
             ▼
┌── Runtime (SG2, SG4, SG5 substrate, SG7) ───────────────┐
│ VectorizedHamletEnv.step() — 16 stages, torch tensors   │
│   1.  action_executor → action writes (VTC)             │
│   2.  passive depletion (VTC)                           │
│   3.  threshold cascades (VTC)                          │
│   4.  effects tick (SG7)                                │
│   5.  VFS evaluator → profile expressions               │
│   6.  terminal conditions (VTC)                         │
│   7-9. counter / item lifecycle / retirement            │
│  10.  VTCRewardProgram(reward_backend=DACEngine)        │
│  11-16. temporal incr / observation assembly / info     │
└────────────┬────────────────────────────────────────────┘
             │ batched transitions
             ▼
┌── Training (SG6) ───────────────────────────────────────┐
│ VectorizedPopulation.step_population()                  │
│   Q-network forward → replay store → loss → optim.step  │
│   Curriculum advance/retreat, exploration ε decay       │
│ Periodic checkpoint with 4-hash compatibility metadata  │
└────────────┬────────────────────────────────────────────┘
             │ checkpoint_ep*.pt (filesystem IPC)
             ▼
┌── Demo & Frontend (SG8) ────────────────────────────────┐
│ LiveInferenceServer polls newest checkpoint, runs       │
│ inference loop, broadcasts state_update frames at 5 Hz  │
│ over ws://:8766/ws to Vue/Pinia frontend.               │
└─────────────────────────────────────────────────────────┘
```

**Leaf utilities.** SG5 (world expression DSL) is the lingua franca — used by SG1 compilers, SG2
profile evaluator, SG7 effects compiler, SG7 items conditions. SG3 (config DTOs) is the input
contract for everything.

**Single point of orchestration.** `VectorizedHamletEnv.step()` is the only place all four
runtime subsystems collaborate (SG2 + SG4 + SG7 + indirectly SG5 evaluator). Diagram 3 in
`03-diagrams.md` visualises this.

### 2.3 Design principles in evidence

1. **Declarative everything.** Variables, rewards, effects, action writes are YAML. The
   substantive Python code is the compiler, the runtime, and the training loop — domain logic
   lives in data.
2. **Compile once, run hot.** Heavyweight work (parsing, type-checking, dependency-DAG building,
   AST baking) happens at startup; the tick loop is closed-form torch ops over baked structures.
3. **Provenance over backwards-compat.** Every compile produces **twelve** SHA-256 hashes
   (`compiled.py:55-87`): `observation_schema_hash`, `variable_schema_hash`, `action_schema_hash`,
   `transition_graph_hash`, `vfs_hash`, `drive_hash`, `brain_hash`, `experiment_hash`,
   `stratum_hash`, `environment_hash`, `actions_hash`, `items_hash`. Two checkpoints produced
   from different YAML resume only if their relevant hashes match. This is the project's
   alternative to runtime backwards-compatibility.
4. **GPU-native by intent.** Tensors throughout VFS, VTC programs, observation builder, reward
   engine. The tick loop *should* be branch-free over agents.
5. **Pedagogical "interesting failures".** Per AGENTS.md and CLAUDE.md: reward hacking and
   curriculum mismatches are features, not bugs.

### 2.4 Where the principles are violated (in the code)

These are the structural debts. All sourced from the validated catalog (§11) and the quality
assessment (§4).

- **Compile-time / runtime mixing.** `universe/compiler.py` calls `SubstrateFactory.build()`
  during compilation — pushing runtime construction into the compile pipeline (catalog §11.5).
- **Per-agent Python loops in nominally GPU paths.** Six confirmed sites violate "GPU-native by
  intent" (catalog §11.3 + `dac_engine.py:572-577, 747-751`, `affordance_engine.py:538-555`,
  `action_executor.py:73-134`, `vectorized_env.py:954-969`, `grid2d.py:581-598`,
  `vfs/vtc.py` `VTCInteractionProgressProgram.apply`).
- **Two coexisting DAC compilation paths.** `dac_engine.py:196` (DAC v2 schema) vs
  `dac_engine.py:230` (legacy `agent.yaml` schema). One should die per the
  zero-backwards-compat rule.
- **Frozen DTO mutated in place.** `VFSCompiler.compile_item_spawn_conditions` mutates
  `rule.when_ast` (catalog §1, §11.2).

---

## 3. State of the codebase (cross-cutting health)

### 3.1 Test corpus and coverage

| Signal | Value | Source |
|--------|-------|--------|
| Tests collected | 2,895 (2,862 selected by default) | `uv run pytest --collect-only -q tests/test_townlet --no-cov` |
| Test functions (`def test_...`) | 2,762 | quality §3 |
| Test files | 284 under `tests/test_townlet/` | `find tests/test_townlet -type f -name 'test_*.py'` |
| Test LOC | 77,265 (170% of src) | discovery |
| Coverage (actual) | **19% line / 36 branches** | `.coverage` artefact, quality §3 |
| Coverage recorded by `tests/test_townlet/README.md` | **19% line coverage**, explicitly qualified as a local artifact | README rebaseline |
| `pytest-benchmark` referenced? | Yes, but **not installed** in `pyproject.toml` / `uv.lock` | quality §3 |
| Markers in use? | 18 uses of `slow/gpu/integration/e2e` across 2,762 tests | quality §3 |

**Interpretation.** The test count is healthy (2,895 collected tests). The coverage figure is
dramatically lower than advertised. The test corpus is **broad but shallow** — many small unit
tests over the easily-testable surface, with performance and integration paths effectively
unmeasured (the performance directory imports a missing dependency).

### 3.2 Tooling status

| Tool | Configured | Enforced |
|------|------------|----------|
| ruff (`E,F,I,N,W,UP`) | `pyproject.toml` | Pre-commit ✓, CI ✓ |
| black (line 140) | `pyproject.toml` | Pre-commit ✓, CI ✓ |
| mypy | `pyproject.toml` | CI ✓ — but `disallow_untyped_defs = false` ("tighten later" comment, 6 months stale) |
| pytest + coverage | `pyproject.toml` | CI ✓ — but no `--cov-fail-under` |
| `hypothesis` | dev dep | Used in `tests/test_townlet/properties/` |
| `vulture` | dev dep | **Never invoked** anywhere (zero pre-commit/CI/script callers) |
| Custom `no_defaults_lint` | `scripts/no_defaults_lint.py` | Pre-commit hook |
| `pytest-benchmark` | Imported by tests | **Not declared** in `pyproject.toml` |
| Security linter (`bandit`, ruff `S`) | None | None |

(Quality §2 has the full table with line references.)

### 3.3 Documentation health

- 499 markdown files in `docs/`.
- 12 specific drifts confirmed against CLAUDE.md (catalog §10).
- `tests/test_townlet/README.md` has been rebaselined to measured test counts and the local
  coverage artifact.
- `CHANGELOG.md` has been rebaselined to `0.1.0`: the 2025-11-05 section is now an alpha
  worklog, not a separate release declaration.
- Four `DEPENDENCY_ANALYSIS_*.{txt,md}` files at repo root are **tracked** and **stale** from a
  prior ad-hoc audit.

**Diagnosis.** Documentation is generated faster than it is curated. The discipline gap is
maintenance, not authorship.

### 3.4 Dead / orphan code (zero-backwards-compat violations)

Confirmed by validator and quality agent. Severity per quality §4:

| Severity | Item | Effort to fix |
|---:|------|---|
| P1 | `VTCSocialResidueProgram` — compiled but never executed | M (regenerates VFS hash) |
| P1 | `agent_config.py` (362 LOC) legacy parallel of `brain_config.py` + `drive_as_code.py` | L (audit + delete) |
| P1 | DAC dual compilation path (`dac_engine.py:230`) | L (audit + delete one branch) |
| P1 | Tracked `DEPENDENCY_ANALYSIS_*` quartet | S (delete + .gitignore) |
| P2 | `CuesCompiler` instantiated, never read | S |
| P2 | `StructuredQNetwork` implemented + tested, unreachable via factory | S |
| P2 | `capability_config.py`, `affordance_masking.py` orphans | S |
| P2 | `Switch` and `Reduce` AST nodes — unparseable, unimplemented | S |
| P2 | `EffectScope.ITEM` and `EffectScope.AFFORDANCE` populated but never iterated | M |
| P2 | `scripts/migrate_affordances_to_effects.py` one-shot | S |
| P3 | `UnifiedServer._start_frontend()` defined, never called | S |
| P3 | `RecordingCriteria` ignored (only periodic honoured) | S |
| P3 | `flask` + `flask-cors` + duplicate `msgpack`/`lz4` + `cloudpickle` + `gitpython` in pyproject, unused in src | S |

Quality §4 estimates **~15-28 engineer-hours** clears 70% of P1+P2.

### 3.5 Latent bugs (silent correctness risks)

| Risk | Symptom | Fix priority |
|------|---------|--------------|
| Adversarial curriculum tensors not in `get_checkpoint_state()` | Resume silently loses `agent_stages` etc. | P1 |
| `decay_epsilon()` called from `demo/runner.py:933` only, not `VectorizedPopulation` | Layering inconsistency (validator confirmed it IS called) | P2 |
| `PerformanceTracker.update_step(rewards, dones)` misnamed (param holds step counts) | Confusing call site | P2 |
| `decisions[0].depletion_multiplier` only — never per-agent | Curriculum difficulty is global, design seemingly intends per-agent | P1 |
| `_max_tensor_elements` assigned twice in registry | Hidden override risk | P3 |
| `ASTNode.line`/`column` never populated by parser | Misleading error positions | P2 |
| `ACTION_ICONS` has 5 entries for 8-16-action vocabulary | Frontend gaps | P2 |
| `aggregation` extrinsic hardcoded to `min` despite 4-mode docstring | Feature gap, not a bug — but matches the project's "interesting failures" only if intentional | P2 |
| RecurrentSpatialQNetwork LSTM input dim 240, not 192 (per CLAUDE.md) | Doc drift, not code bug | doc fix |

### 3.6 Performance discipline

**Six confirmed GPU-discipline leaks** in nominally GPU-native paths:
`affordance_engine.py:538-555`, `action_executor.py:73-134`, `vectorized_env.py:954-969 +
1346-1371`, `dac_engine.py:572-577 + 747-751`, `grid2d.py:581-598`, `vfs/vtc.py`
`VTCInteractionProgressProgram.apply`.

**Performance test infrastructure exists** at `tests/test_townlet/performance/` but **silently
skips** because `pytest-benchmark` is referenced but not declared. There is no shipped profiling
baseline.

### 3.7 Security posture

(Full detail: `07-security-surface.md`.)

| ID | Finding | Severity |
|----|---------|----------|
| **SEC-01** | `safe_torch_load(..., weights_only=False)` + `verify_checkpoint_digest(..., required=False)` at every demo checkpoint-loading site (`live_inference.py:444`, `runner.py:185`, `runner.py:342`). **RCE via tampered checkpoint** under service user. | **High** |
| SEC-02 | uvicorn binds `0.0.0.0` without auth (`live_inference.py:1231`, `unified_server.py:416`) | Medium |
| SEC-03 | `deploy/townlet-demo.service` lacks all hardening directives (`NoNewPrivileges`, `PrivateTmp`, `ProtectSystem`) | Medium |
| SEC-04 | Service runs only training; switching to `run_demo.py` silently exposes `0.0.0.0:8766` | Medium |
| Various | Supply chain (cloudpickle, gitpython, flask×2 declared but unused; torch<2.12 upper pin) | Low-Medium |

**Confirmed clean:** YAML is `safe_load` throughout (except a `SafeLoader` subclass for source-mapping — verified safe). World DSL is a closed pyparsing grammar with no `eval`/`exec` escape. No `shell=True`, no `os.system`, no PII.

**Posture.** This is a localhost-only pedagogical tool with a real RCE path if a hostile checkpoint
ever reaches the loader. Acceptable on a single-user workstation; **not deployable** to a shared
cluster or hosted environment without SEC-01 fixed first.

---

## 4. Recommendations (prioritised for document recreation)

The user's stated goal is **recreating the document set**. This list is ordered to maximise the
value of that recreation, with code fixes interleaved where doc accuracy depends on them.

### P0 — block the doc recreation until done

1. **Test README coverage claim: done.** `tests/test_townlet/README.md` now records 2,895
   collected tests, 2,862 default-selected tests, 284 test files, and the 19% local coverage
   artifact with its caveat.
2. **Fix SEC-01 if any non-self-distributed checkpoints are ever loaded.** Set
   `verify_checkpoint_digest(..., required=True)` and audit `weights_only=False` callers.
   (S — 1 h once decision is made)
3. **Version baseline: done.** Use `0.1.0`. `pyproject.toml:3` already declares `0.1.0`, and
   the 2025-11-05 changelog section has been recast as a `0.1.0` alpha worklog.

### P1 — must inform the new docs

4. **Recreate `CLAUDE.md` configuration section** to use `configs/<pack>/levels/<level>/`
   (catalog §10 rows 2-5, SG3 evidence). Eliminate the flat-layout claim.
5. **Recreate the universe-compiler doc** with the **actual 9 stages**, not the legacy "seven
   stages" claim. Use the §4 diagram in `03-diagrams.md` as the canonical visualisation. Resolve
   the three internal numbering schemes in `pipeline.py`. (M)
6. **Document VTC programs accurately.** 9 program classes, of which **8 are wired at runtime**
   (validator-confirmed); `VTCSocialResidueProgram` is unwired. Either wire it or delete it
   before naming it in docs. (M — 4-6 h to delete + regenerate VFS hash; L to wire properly)
7. **Recreate `docs/config-schemas/`** to reflect the hierarchical v2.1 layout. The current
   per-file schema docs are obsolete (SG3 §4).
8. **Recreate the exploration strategies doc.** CLAUDE.md names files that don't exist
   (`icm.py`, `count_based.py`, `adaptive_rnd.py`). Document the actual three strategies
   (`epsilon_greedy.py`, `rnd.py`, `adaptive_intrinsic.py`) and the inheritance shape. (M)
9. **Recreate the runtime tick walkthrough** using the 16-stage flow from catalog §4 and
   Diagram 3. The `step()` is the single most important code path; it deserves a dedicated
   document. (M)
10. **Add a `drive_hash` provenance doc.** Where is each hash computed; what it covers; how
    checkpoint compatibility is decided. (S-M)

### P1 — code cleanups that simplify the docs

11. **Delete tracked stale artefacts**: `DEPENDENCY_ANALYSIS_*.{txt,md}` (4 files),
    legacy `agent_config.py`, `capability_config.py`, `affordance_masking.py`, dead `CuesCompiler`,
    dead `StructuredQNetwork` (or wire it). (S total)
12. **Delete the legacy DAC compilation path** in `dac_engine.py:230`. Maintain only the DAC v2
    schema. Update `drive.yaml` documentation to match. (L)
13. **Remove unused pyproject deps**: `flask`, `flask-cors`, `cloudpickle`, `gitpython`,
    duplicate `msgpack` and `lz4`. (S)
14. **Wire or remove `pytest-benchmark`.** Either add to dev deps and run perf tests in CI, or
    delete the conftest that imports it. (S)
15. **Recreate `frontend/package.json`** so `npm run dev` is reproducible. (S — once stack
    confirmed from `vite.config.js` and store/component imports.)

### P2 — quality-of-life

16. Wire `vulture` into pre-commit OR remove from dev deps.
17. Set `--cov-fail-under` in pyproject.
18. Tighten mypy: `disallow_untyped_defs = true` for new code, audit old.
19. Add `ruff` selection `B` (bugbear) and consider `S` (bandit) or wire bandit/safety into CI.
20. Centralise the three observation encodings (relative/scaled/absolute) across substrates —
    they are duplicated per-substrate today (catalog §5A).
21. Vectorise the six confirmed GPU-discipline leaks OR amend the "GPU-native" marketing to
    acknowledge mixed-mode hot paths.

### P3 — nice-to-have

22. Document the world expression DSL grammar formally (currently exists only in
    `parser.py:55-236` and `temp/sg5-substrate-world.md`).
23. Add line/column population to `ASTNode` for proper error reporting.
24. Wire `EffectScope.ITEM` and `EffectScope.AFFORDANCE` buckets OR delete them.

---

## 5. The document recreation plan

Suggested target document set, with this analysis as input. Each doc gets a one-line scope and a
pointer to the evidence here.

| New doc | Scope | Primary source |
|---------|-------|-----|
| `docs/ARCHITECTURE.md` | One-page system overview | This report §1-2 + `03-diagrams.md` Diagram 1-2 |
| `docs/RUNTIME-TICK.md` | The 16-stage `step()` walkthrough | `02-subsystem-catalog.md` §4 + Diagram 3 |
| `docs/UNIVERSE-COMPILER.md` | The 9-stage compile pipeline | `temp/sg1-universe.md` + Diagram 4 |
| `docs/VFS.md` | Variable & Feature System + VTC programs | `temp/sg2-vfs.md` |
| `docs/CONFIG-PACKS.md` | Hierarchical layout, DTO map, no-defaults rule | `temp/sg3-config.md` |
| `docs/REWARD-DAC.md` | DAC schema and engine (only the v2 path post-cleanup) | `temp/sg4-environment.md` |
| `docs/EXPRESSION-DSL.md` | DSL grammar, AST, 48 built-ins | `temp/sg5-substrate-world.md` Part B |
| `docs/SUBSTRATES.md` | ABC + factory + 9 concrete substrates | `temp/sg5-substrate-world.md` Part A |
| `docs/EFFECTS-AND-ITEMS.md` | 10-command DSL + inventory | `temp/sg7-effects-items.md` |
| `docs/RL-TRAINING.md` | Networks, replay, exploration, curriculum, population | `temp/sg6-training.md` |
| `docs/CHECKPOINT-PROVENANCE.md` | 4-hash compatibility pipeline | `temp/sg6-training.md` checkpoint_utils + SG1 evidence |
| `docs/DEMO-AND-FRONTEND.md` | UnifiedServer + WebSocket protocol + Vue store | `temp/sg8-demo-recording-frontend.md` + Diagram 5 |
| `docs/SECURITY.md` (replace) | Updated threat model & posture | `07-security-surface.md` |
| `docs/QUALITY-AND-TOOLING.md` | Tooling stack, test culture, coverage policy | `05-quality-assessment.md` |
| `docs/GLOSSARY.md` | VFS, VTC, UAC, DAC, MAC (?), DTO, ACL, the curriculum levels | This report (terms in §1-2) |

Old documents to **retire** (not migrate; verbatim copy preserves the drift):
- The "seven-stage" universe compiler description.
- Any doc using the flat `configs/<level>/` layout.
- Any doc referencing `reward_strategy.py`, `icm.py`, `count_based.py`, `adaptive_rnd.py`.
- Test-corpus stats older than the current `.coverage` artefact.

---

## 6. Confidence and limitations

**Confidence per phase:**
- Discovery / topology: **High** (verified)
- Per-subsystem catalogs: **High** for all 8 (subagent self-assessment + validator gate)
- Cross-subsystem dependency matrix: **High** (validator spot-checked 4 edges)
- Diagrams: **High** (built on the validated catalog with explicit validation hooks)
- Quality assessment: **High** (every claim cited; two of my brief's assumptions corrected by the agent)
- Security: **High** for the narrow inbound surface; **Medium** for supply chain depth (deps not audited beyond pyproject)

**Known limitations:**
1. Tests not analysed for **what** they cover, only **that** they exist. The 19% coverage figure
   is from the local `.coverage` artefact and was not regenerated under this analysis.
2. `runs/` contents not inspected — actual checkpoint shapes not validated against the catalogued
   provenance pipeline.
3. `docs/` (499 markdown files) deliberately **not used** as source per the user's directive;
   doc-vs-code drift was sampled, not exhaustively catalogued.
4. The DAC engine's 11 shaping bonuses and 9 extrinsic strategies were enumerated by name but
   their individual semantics were not deeply verified — SG4 walked the structure, not every body.
5. Performance baseline does not exist; the six GPU-discipline leaks are flagged but not
   quantified against an alternative implementation.

**Where to start a recreated doc set with the highest confidence:**
- Diagrams 1, 2, 4 in `03-diagrams.md` — all derived from validated facts and source code.
- `02-subsystem-catalog.md` §1-8 — these survived a dedicated validator gate.
- The 12-row documentation drift catalog (§10) — every row independently verified by the validator.

---

## 7. Workspace artefact index

| File | Purpose |
|------|---------|
| `00-coordination.md` | Strategy, scope, execution log |
| `01-discovery-findings.md` | Holistic discovery from source only |
| `02-subsystem-catalog.md` | The validated 8-subsystem catalog + cross-cutting concerns |
| `03-diagrams.md` | Five C4 / sequence diagrams in Mermaid |
| `04-final-report.md` | This document |
| `05-quality-assessment.md` | Toolchain, hygiene, test culture, doc decay |
| `07-security-surface.md` | Threat model, STRIDE, supply chain, deployment posture |
| `temp/sg1-universe.md` | Universe compiler evidence |
| `temp/sg2-vfs.md` | VFS evidence |
| `temp/sg3-config.md` | Config DTO evidence |
| `temp/sg4-environment.md` | Environment & DAC evidence |
| `temp/sg5-substrate-world.md` | Substrate + World DSL evidence |
| `temp/sg6-training.md` | RL training stack evidence |
| `temp/sg7-effects-items.md` | Effects + Items evidence |
| `temp/sg8-demo-recording-frontend.md` | Demo + Recording + Frontend evidence |
| `temp/validation-catalog.md` | Independent validator's gate report |

**Intentionally absent.** `06-architect-handover.md` is not produced. Option A
(Full Analysis) does not require it; the final report §5 already provides the doc-recreation
plan that an architect handover would otherwise carry.

**Cleanup recommendation for `temp/`.** Once the new document set in §5 is built and the
per-subsystem `docs/*.md` files have absorbed the relevant evidence with proper citations, the
`temp/` directory can be deleted in a single `rm -rf` — or preserved as `docs/arch-analysis-
2026-05-16-1200/temp/` for audit. There is no ongoing reason to retain it.
