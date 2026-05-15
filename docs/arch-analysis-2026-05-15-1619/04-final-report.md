# HAMLET / Townlet — Architecture Analysis: Final Report

**Date:** 2026-05-15
**Branch:** `project-recovery`
**Scope:** `src/townlet/` (152 files, ~40K LOC) + `scripts/` + `tests/test_townlet/` (305 files) + `configs/` + `pyproject.toml`. Excluded: obsolete `src/hamlet/`, the Vue `frontend/` (referenced only as a downstream WebSocket consumer).
**Workspace:** `docs/arch-analysis-2026-05-15-1619/`

## Companion documents

- [`00-coordination.md`](00-coordination.md) — analysis plan and execution log
- [`01-discovery-findings.md`](01-discovery-findings.md) — holistic discovery
- [`02-subsystem-catalog.md`](02-subsystem-catalog.md) — 6 subsystem entries
- [`03-diagrams.md`](03-diagrams.md) — 6 Mermaid diagrams (C4 context/container/component, sequence, topology, dependency graph)
- [`temp/validation-catalog.md`](temp/validation-catalog.md) — independent validation pass on the catalog (verdict: PASS-WITH-NOTES; the two specific errors it surfaced are corrected in §2)

---

## Executive Summary

Townlet is a pedagogical Deep-RL training environment that compiles declarative YAML experiment packs into immutable `CompiledUniverse` artifacts and executes them through a vectorised GPU-native runtime. The architecture is sound, the recent compiler-cleanup pass is **largely complete and visible in the tree**, and the codebase honours its pre-release "no backwards compatibility" discipline with only a handful of antipattern violations remaining at the Pydantic layer.

The single most consequential architectural debt has migrated: the 4,431-line `universe/compiler.py` monolith that drove the prior `arch-analysis-2026-05-15-compiler-cleanup/` pass is now a 656-line orchestration shell delegating to typed stage modules in `compilers/`, `dto/`, `loaders/`, `validation/`, and `adapters/`. **The next clear refactor target is `environment/vectorized_env.py` (2,200 lines)** — the runtime hub now occupies the structural position the compiler used to. A concrete four-way decomposition is laid out in [§4 Recommendations](#4-recommendations).

Eight findings warrant attention; none are critical (P0), three are high-priority (P1), the rest are documentation, hygiene, or minor structural drift.

---

## 1. Architectural Picture

### 1.1 Subsystem topology

Six logical subsystems map cleanly onto the directory structure (see [§02 catalog](02-subsystem-catalog.md) and [`03-diagrams.md`](03-diagrams.md)):

| # | Subsystem | LOC | Role | Confidence |
|---|-----------|-----|------|------------|
| 1 | **Declarative Compilation Pipeline** (universe + vfs + effects) | ~11K | YAML → CompiledUniverse; seven-stage UAC pipeline; pre-compiled effect ASTs | High |
| 2 | **Configuration / DTO Layer** (config/) | ~4.7K | 22 Pydantic v2 modules enforcing strict v2.1 schema; no-defaults discipline | High |
| 3 | **Environment Runtime & DAC** (environment/) | ~5.3K | VectorizedHamletEnv (2,200-line hub) + DACEngine reward computation graph | High |
| 4 | **Physical Layer** (substrate + world + items) | ~8K | 8 substrate types; expression evaluator; inventory + item lifecycle | High |
| 5 | **RL Core** (agent + population + training + exploration) | ~5.4K | DQN/Double DQN, RND/adaptive intrinsic, vectorized population | High |
| 6 | **Orchestration & Periphery** (curriculum + recording + demo) | ~5.6K | Curriculum strategies; async recording; UnifiedServer + LiveInferenceServer | High |

### 1.2 Coupling

- **No subsystem cycles** at the import-graph level ([§03 diagram 6](03-diagrams.md#6-dependency-graph--subsystem-coupling)).
- **`environment/` is the runtime hub** — 6 inbound subsystem edges, 8 outbound to compile-time and physical-layer subsystems.
- **`world/expression` is a shared seam** used by both `universe/` (compile-time type-check) and `effects/` (runtime evaluation). This is deliberate, not a leak.
- **`config/` is the foundation layer** — every subsystem reads from it; nothing writes back.

### 1.3 Pipeline shape

The seven-stage UAC compilation pipeline ([§03 diagram 3](03-diagrams.md#3-component-diagram--uac-compilation-pipeline-c4-level-3)) uses **explicit typed stage handoffs** (`LoadedConfigBundle → ResolvedConfigBundle → SharedCompilerArtifacts → CompiledLevelBundle → CompiledArtifactBundle` in `universe/pipeline.py`). This is one of the strongest architectural signals in the codebase: every stage's input/output is a named dataclass, and the pipeline is logged, numbered, and cache-fingerprinted.

The runtime tick ([§03 diagram 4](03-diagrams.md#4-component-diagram--runtime-tick-c4-level-3)) follows a clean 11-step sequence: action validation → meter dynamics → cascades → effects → VFS evaluation → terminal checks → item lifecycle → retirement → DAC reward → temporal increment → observation build. The vectorisation is consistent — no per-agent for-loops in the hot path.

---

## 2. Findings

Findings are prioritised by **structural impact** × **likelihood of biting** in a production-pedagogy scenario.

### P1 — High priority

#### F-1. `environment/vectorized_env.py` is the next obvious decomposition target (2,200 lines, 38 methods)

The runtime hub now occupies the structural position the universe compiler held three months ago. The catalog ([§02 Subsystem 3](02-subsystem-catalog.md#3-environment-runtime--dac-reward-engine)) identifies concrete split lines. **Recommendation in §4.**

#### F-2. `NullItemManager` consolidation is incomplete

CLAUDE.md and code comments claim `ENV-009` consolidated duplicate `NullItemManager` implementations into `environment/null_managers.py`. The validator confirmed the class is still defined in **three places**:

- `environment/null_managers.py:15` (the intended canonical location)
- `effects/manager.py:23`
- `effects/context.py:21`

This is the kind of silent drift the no-backcompat rule was supposed to eliminate. **Recommendation in §4.**

#### F-3. Four no-defaults antipatterns in the config layer

The pre-release "no defaults" discipline is enforced by `scripts/no_defaults_lint.py` and the Pydantic `Field(...)` convention, but four specific instances slip through:

| Site | Issue |
|------|-------|
| `config/effects_config.py:245` | `observable: bool = Field(default=True, ...)` — observability is behavioural and should be required. |
| `config/effects_config.py:248–251` | Lifecycle command lists (`on_spawn` / `on_tick` / `on_despawn` / `on_interrupt`) all default to `[]`. YAML omission vs. explicit empty list is undocumented. |
| `config/effects_config.py:267` | `version: Literal["1.0"] = Field(default="1.0")` — should be required. |
| `config/drive_as_code.py:634` | `version: str = Field(default="1.0", ...)` — **worse**: the annotation is bare `str`, so any string validates. Silent schema-drift risk is materially higher than the Literal-typed sites. |

#### F-4. `drive_as_code.py` is ~670 lines and overloaded

Same module holds `RangeConfig`, `ModifierConfig`, all extrinsic strategies, all shaping bonuses, and DAC composition. As the system has grown it has become the single largest DTO module. Candidate for the same submodule split the universe compiler just received. Lower urgency than F-1 but the same shape of problem.

### P2 — Medium priority

#### F-5. `DACEngine` dual-schema branching is fragile

`environment/dac_engine.py:110–135, 196, 231, 243, 257` uses `hasattr` / `getattr` to detect whether it received a `DriveConfig` (legacy `agent_config` schema) or a `DriveAsCodeConfig` (`drive_as_code` schema). It works, but it is the kind of seam that breaks silently when either schema evolves. A strongly-typed union (`DriveConfig | DriveAsCodeConfig`) with explicit `match` arms would be safer.

#### F-6. POMDP × substrate compatibility is silently coerced

The substrate × POMDP matrix has documentation/code drift:

- `AspatialSubstrate.get_default_actions()` (`substrate/aspatial.py:141–162`) returns `[INTERACT]` only — missing `WAIT` despite the base-class docstring at `substrate/base.py:92`.
- POMDP is rejected for `Grid3D` (vision_range > 2), `Continuous*`, and `GridND` (N≥4) at `environment/vectorized_env.py:258–308`.
- Configuration accepts `observation_encoding ∈ {relative, scaled, absolute}` but `vectorized_env.py:306` silently coerces to `relative` for POMDP without raising.

The silent coercion violates the no-defaults / fail-loudly contract for behavioural parameters.

#### F-7. `effects/scheduler.py` class is named `Scheduler`, not `EffectScheduler`

Catalog naming slip caught by the validator. Worth noting because almost every other class in `effects/` carries a domain prefix (`CommandNode`, `CommandParser`, `CommandCompiler`, `CommandExecutor`, `CompiledEffect`, `EffectCatalog`, `EffectManager`, `ActiveEffect`). A bare `Scheduler` reads as suspiciously generic in a package shared with `EffectManager` — consider renaming for consistency.

### P3 — Low priority / informational

#### F-8. CLAUDE.md is stale on curriculum naming

CLAUDE.md still describes config packs as `L0_0_minimal`, `L0_5_dual_resource`, `L1_full_observability`, `L2_partial_observability`, `L3_temporal_mechanics`. The actual `configs/` directory contains `aspatial_test/`, `default_curriculum/`, `reference/`, `simple/`, `test/`. Pure documentation drift; no code impact.

#### Lesser citation slips (already corrected in the catalog)

- `compiled.py:68–69` → actually `92–93` for the `agent_profile`/`item_profiles` TODOs.
- `compiler.py:85` → actually `86–87` for the explicit-primary-level raise.
- Line counts: `compiler.py` 619 → 656, `compiled.py` 965 → 995 (both grew between the subagent snapshot and the report; the architectural claim "down from 4,431" is still true).

---

## 3. Cross-Subsystem Themes

### 3.1 The compiler refactor playbook works

The universe-compiler reorganization is a worked example for the codebase:

- **Before:** 4,431-line `compiler.py` monolith with embedded validation, parsing, metadata, and emission.
- **After:** 656-line orchestration shell; stage modules in `compilers/`; typed handoffs in `pipeline.py`; validation phases split four ways; loaders, DTOs, adapters each in their own sub-package.

The same shape of refactor applies to `vectorized_env.py` and (with less urgency) `drive_as_code.py`. The team has the muscle memory.

### 3.2 The "no defaults" discipline mostly works

The lint script + Pydantic `Field(...)` convention + commit `92979107` (which removed dead defensive defaults at the experiment-root boundary) demonstrate the team takes this seriously. The four remaining antipatterns (F-3) are isolated to `effects_config.py` and `drive_as_code.py`, and one of them (`drive_as_code.py:634`) is a strictly *worse* violation than its neighbours because the type annotation is un-Literal'd `str`.

### 3.3 The runtime is GPU-native and consistent

Vectorisation is honoured throughout the hot path: meter dynamics, DAC reward, RND novelty, replay buffers, population step, exploration action selection — all operate on `[batch, ...]` tensors with no per-agent for-loops. The null-object pattern (`NullItemManager`) is the right shape for optional subsystems; only the consolidation is incomplete (F-2).

### 3.4 The pedagogical mission shapes what counts as a "bug"

CLAUDE.md is explicit: some "interesting failures" (Low Energy Delirium reward-hacking, sparse-reward catastrophes) are teaching moments and should be preserved, not patched. This analysis honours that — none of F-1 through F-8 are pedagogical-emergence issues; all are structural / hygiene findings.

---

## 4. Recommendations

Ordered by impact × ease.

### R-1. Decompose `vectorized_env.py` along the boundaries already implicit in its method clusters

Concrete split (from [§02 Subsystem 3 Concerns](02-subsystem-catalog.md#3-environment-runtime--dac-reward-engine)):

| New module | Methods to extract |
|------------|-------------------|
| `environment/action_executor.py` | `_execute_actions()`, `_handle_interactions()`, `_handle_instant_interactions()` |
| `environment/observation_encoder.py` | `_get_observations()`, `_build_affordance_encoding()`, `_encode_position_observation()` |
| `environment/reward_calculator.py` | `_calculate_shaped_rewards()` (façade over DACEngine) |
| `environment/env_factory.py` | `from_universe()` + initialisation helpers |

`VectorizedHamletEnv` becomes a step-orchestrator delegating to these four modules — same architectural shape as `universe/compiler.py` post-cleanup. Tests already in `tests/test_townlet/unit/environment/` provide a regression safety net.

### R-2. Finish `NullItemManager` consolidation

Delete the duplicates in `effects/manager.py:23` and `effects/context.py:21`; import from `environment/null_managers.py` instead. Verify no circular import. Re-run any test that exercises the null path.

### R-3. Tighten the four `Field(default=...)` antipatterns

Change to `Field(...)` (required) in:

- `effects_config.py:245` (`observable`)
- `effects_config.py:248–251` (lifecycle command lists; if YAML omission must remain valid, document it explicitly in the DTO docstring)
- `effects_config.py:267` (`version`)
- `drive_as_code.py:634` (`version`; also tighten annotation to `Literal["1.0"]` to catch future-version configs at load)

Update the affected config packs to specify these fields explicitly. Update `scripts/no_defaults_lint.py` to catch this class of `Field(default=...)` going forward (the lint script appears to catch function-default and logical-OR-default patterns but not Pydantic-Field-defaults).

### R-4. Replace `DACEngine` hasattr/getattr with a tagged union

Define `DriveSpec = DriveConfig | DriveAsCodeConfig` (or a discriminated `Annotated[..., Field(discriminator="kind")]`), then drive selection by `match`/`isinstance` instead of attribute probing. Eliminates `dac_engine.py:110–135, 196, 231, 243, 257`.

### R-5. Make POMDP × substrate compatibility loud

- Either implement `WAIT` in `AspatialSubstrate.get_default_actions()`, or update the base-class docstring to remove the contract.
- `vectorized_env.py:306`: raise `ValueError` on POMDP + non-`relative` encoding instead of silently coercing.
- Add an explicit POMDP-compatibility matrix to `docs/` (or a test in `tests/test_townlet/unit/environment/test_pomdp_validation.py`) so the supported envelope is discoverable.

### R-6. Refresh CLAUDE.md curriculum naming (doc only)

Replace the `L0_0_minimal` ... `L3_temporal_mechanics` block with the actual current pack list (`aspatial_test`, `default_curriculum`, `reference`, `simple`, `test`).

### R-7. Optional: split `drive_as_code.py` along its natural seams

If/when `drive_as_code.py` reaches ~1,000 lines, split into `range.py`, `modifier.py`, `extrinsic.py`, `intrinsic.py`, `shaping.py`, `composition.py` — one DTO family per file. The pattern is identical to the universe-compilers split.

---

## 5. Pre-existing tracker signals

The catalog cites multiple internal labels (`PDR-002`, `TASK-005 Phase 3`, `ENV-007`, `ENV-009`, `HIGH-01`, `HIGH-02`, `HIGH-04`, `CRIT-07`, `JANK-09`). Without access to the issue tracker the meanings are inferred from inline comments; spot-check before scheduling work that these IDs map to the current Filigree issue set. The 3 ready-to-work issues in `filigree session-context` at session start were:

- P1 `hamlet-74197422b3` — torch 2.12 + triton 3.7 segfault inside pytest (validated by `pyproject.toml` upper-bound pin)
- P1 `hamlet-5ab2f7c7c5` — refine compiler boundary and level metadata contracts (overlaps with R-1 fallout if the new boundaries change runtime artefact shapes)
- P4 `hamlet-b454c1b75a` — release: Future

`hamlet-5ab2f7c7c5` should be cross-referenced against R-1 when planning the next refactor.

---

## 6. Confidence and Limitations

**High-confidence findings:** subsystem boundaries, dependency graph, the `vectorized_env.py` decomposition recommendation, the four `Field(default=...)` antipatterns, the `NullItemManager` triplication, the AspatialSubstrate WAIT bug, the universe compiler's post-reorganization state. All cross-checked by an independent validation pass.

**Medium confidence:** DAC engine internal data flow (read but not exhaustively traced); RL core hyperparameter sensitivity (variance_threshold=100.0, max_grad_norm=10.0 — config-driven but not benchmark-evaluated here); curriculum advance/retreat metric thresholds (data-driven but not validated against historical experiment outcomes).

**Out of scope:** Vue frontend (`frontend/`), full test-suite analysis (305 test files; only the directory layout was inspected), `mlflow` / `tensorboard` integration details, GPU performance profiling, multi-agent or multi-zone (L5/L6) extensions referenced as "Future" in CLAUDE.md.

**Validation:** [`temp/validation-catalog.md`](temp/validation-catalog.md) verdict was `PASS-WITH-NOTES`. The two factually wrong concerns it surfaced (`semantics.py` fallback that doesn't exist; RND active_mask that *is* applied) have been corrected in [`02-subsystem-catalog.md`](02-subsystem-catalog.md).
