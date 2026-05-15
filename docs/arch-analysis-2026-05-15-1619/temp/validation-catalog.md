# Validation Report: 02-subsystem-catalog.md

## Verdict: PASS-WITH-NOTES

## Methodology

For each of the 6 subsystem entries, I verified (a) every line-count claim with `wc -l`, (b) at least 2 named-symbol claims per subsystem with `grep`/`Read`, and (c) every concern that cites a specific file:line. Tools: Read, Bash (wc, grep, ls). All checks read-only.

The architectural picture the catalog paints is faithful to the code. The discrepancies are line-number drift (compiler.py / compiled.py have grown since the catalog was drafted), one off-by-many line citation for `agent_profile/item_profiles`, one factually wrong "concern" about RND active_mask, and a couple of minor symbol-name misses. None of these invalidate the subsystem boundaries, dependency graph, or the headline observations.

## Line-count audit

| File | Claimed | Actual | Match |
|------|---------|--------|-------|
| universe/compiler.py | 619 | 656 | ⚠️  +37 |
| environment/vectorized_env.py | 2200 | 2200 | ✅ |
| environment/dac_engine.py | 1012 | 1012 | ✅ |
| universe/compiled.py | 965 | 995 | ⚠️  +30 |
| environment/affordance_engine.py | 625 | 625 | ✅ |
| environment/meter_dynamics.py | 221 | 221 | ✅ |
| environment/temporal_utils.py | 78 | 78 | ✅ |
| environment/null_managers.py | 67 | 67 | ✅ |

`compiler.py` and `compiled.py` have grown since the catalog was drafted (likely between the subagent's snapshot and synthesis). Architectural claim — "compiler.py is down from ~4,431 lines" — still holds; the picture isn't materially different at 656 vs 619.

## Specific-line claims audit

| Cited location | Claim | Reality | Verdict |
|---|---|---|---|
| `compiled.py:68–69` | `agent_profile`, `item_profiles` marked `Any` with TODOs | Lines 68–69 are `compiled_effect_catalog`, `effects_schema`. Actual `agent_profile: Any \| None` and `item_profiles: dict[str, Any] \| None` with `# TODO` markers live at lines **92–93**. | ⚠️  Content correct, line number wrong |
| `semantics.py:15–21` | Falls back to `sorted(levels.keys())[0]` when `primary_level` is None | `select_primary_level` raises `ValueError` on None (line 18); no `sorted(...)` fallback present. Catalog's own follow-up note ("compiler.py:85 does enforce it") is correct in spirit — `compiler.py:86–87` raises ValueError. | ❌ The cited fallback never existed at semantics.py:15–21 |
| `compiler.py:85` | "enforces explicit primary level" | The raise lives at **lines 86–87**, not 85. | ⚠️  Off by one |
| `effects_config.py:245` | `observable: bool = Field(default=True, ...)` | Line 245 is exactly `observable: bool = Field(default=True, description="Visible in agent observations")`. | ✅ |
| `effects_config.py:248–251` | Lifecycle command lists default to `[]` | Lines 248–251 are `on_spawn/on_tick/on_despawn/on_interrupt = Field(default=[], ...)`. | ✅ |
| `effects_config.py:267` | `version: Literal["1.0"] = Field(default="1.0")` | Confirmed at line 267. | ✅ |
| `drive_as_code.py:602–605` | `log_components`, `log_modifiers` defaulted to True/False | Lines 602–605: `normalize: default=False`, `clip: default=None`, `log_components: default=True`, `log_modifiers: default=True`. Both `log_*` default to `True`, not "True/False" as catalog says — minor wording slip. | ⚠️  Both default True |
| `drive_as_code.py:634` | `version: Literal["1.0"] = Field(default="1.0")` | Line 634 is `version: str = Field(default="1.0", ...)`. Annotation is `str`, **not** `Literal["1.0"]` (so the silent-schema-drift risk is actually worse than catalog states). | ⚠️  Annotation differs; concern still valid |
| `dac_engine.py:110–135` | hasattr/getattr for dual schemas | Confirmed: `hasattr(config, "bar")`, `getattr(config, "bar", None)`, etc. at exactly those lines. | ✅ |
| `vectorized_env.py:702` | `action_mask_table.shape[1] == 0` temporal check | Line 702 is exactly that condition with the cited fallback message. | ✅ |
| `items/instance.py:23` | `position: tuple[int,...] \| tuple[float,...]` dual typing | Exact match at line 23. | ✅ |
| `substrate/aspatial.py:141–162` | `get_default_actions()` returns `[INTERACT]` not `[INTERACT, WAIT]` | Confirmed: lines 141–162 return a single-element list `[INTERACT]`. Base-class docstring (`base.py:92`) says "Aspatial substrates have NO movement actions, only `[INTERACT, WAIT]`". Catalog says docstring is at line 92 — it's actually at line 92. | ✅ |
| `rnd.py:91` (RNDNetwork) | `active_mask` buffer registered but **not visibly applied** in forward pass | Line 91 registers the buffer. Lines 102–106 of `forward()` apply it: `masked_x = x * active_mask`. The mask IS applied. | ❌ Concern is wrong |

## Findings

### Subsystem 1: Declarative Compilation Pipeline

- ✅ Verified: `universe/compiler.py` is 656 lines (still small enough that the "down from 4,431" claim holds); `universe/compiled.py` exists with `REQUIRED_COMPILED_UNIVERSE_FIELDS`; `effects/schema.py:CommandNode`, `effects/compiler.py:CommandCompiler`, `effects/executor.py:CommandExecutor`, `effects/catalog.py:CompiledEffect`/`EffectCatalog`, `effects/parser.py:CommandParser` all exist as named.
- ⚠️  Notes:
  - Line 619 → 656 drift on `compiler.py`; 965 → 995 on `compiled.py`.
  - `compiled.py:68–69` cite is wrong — `agent_profile`/`item_profiles` are at lines 92–93 (content correct).
  - `compiler.py:85` cite is off-by-one (raise is at 86–87).
  - `effects/scheduler.py` defines class **`Scheduler`** (line 21) plus `ScheduledItem`, not `EffectScheduler` as the catalog calls it.
  - `NullItemManager` is defined in **three** places: `environment/null_managers.py:15`, `effects/manager.py:23`, and `effects/context.py:21`. Catalog says "Consolidates duplicates (ENV-009)" — consolidation is incomplete.
- ❌ Errors:
  - **Concern #2 misreads semantics.py:15–21.** The function raises `ValueError` on `None`; there is no `sorted(levels.keys())[0]` fallback. The "Status: safe" conclusion happens to be right, but the diagnostic path is fictional.

### Subsystem 2: Configuration / DTO Layer

- ✅ Verified: all four cited `Field(default=...)` antipatterns (`effects_config.py:245,248–251,267`; `drive_as_code.py:602–605,634`) match the source byte-for-byte.
- ⚠️  Notes:
  - Catalog says "22 modules total" — actual count in `src/townlet/config/` is **21** `.py` files plus `__init__.py` (22 if you count `__init__.py`). Catalog also omits `curriculum.py` from its enumeration (it lists `curriculum_config.py` only).
  - `drive_as_code.py:634` annotation is `str`, not `Literal["1.0"]` (the version-drift risk is worse than catalog states).
  - "log_components, log_modifiers defaulted to True/False" — both default to `True`.
- ❌ Errors: none material.

### Subsystem 3: Environment Runtime & DAC Reward Engine

- ✅ Verified: `vectorized_env.py` is exactly 2,200 lines; `VectorizedHamletEnv` at line 102; `DACEngine` at `dac_engine.py:28`; `dac_engine.py:110–135` hasattr/getattr branching confirmed; `action_mask_table.shape[1] == 0` check at line 702 confirmed; `meter_dynamics.py` and `temporal_utils.py` at exact claimed sizes; `is_affordance_open(time_of_day, operating_hours)` confirmed at `temporal_utils.py:11`; `NullItemManager.spawn_item` raises confirmed at `null_managers.py:41`.
- ⚠️  Notes:
  - Catalog asserts "No residue of RewardStrategy". `grep -rn "RewardStrategy" src/townlet/` returns no class hits; only a comment in `replay_buffer.py` mentions the legacy pattern by name. Effectively true.
- ❌ Errors: none.

### Subsystem 4: Physical Layer

- ✅ Verified: 8 substrate types as enumerated; `AspatialSubstrate.get_default_actions()` lines 141–162 return only `[INTERACT]`, missing `WAIT`, contradicting `base.py:92` docstring — exactly as claimed; `ItemInstance.position` dual-typed at `items/instance.py:23`; POMDP rejection logic for Aspatial/Continuous/4+D/Grid3D vision_range and the silent `observation_encoding=relative` coercion all live at `vectorized_env.py:258–308`.
- ⚠️  Notes: none material.
- ❌ Errors: none.

### Subsystem 5: RL Core

- ✅ Verified: `SimpleQNetwork`, `RecurrentSpatialQNetwork`, `DuelingQNetwork`, `StructuredQNetwork` all at `agent/networks.py` (lines 14, 53, 321, 443); `NetworkFactory` at `network_factory.py:20`; `RewardTensor` at `training/state.py:38`; `CurriculumDecision` at line 167; `PopulationCheckpoint` at line 191; `RNDExploration` at `rnd.py:109`; `active_mask` buffer registered at `rnd.py:91`.
- ⚠️  Notes:
  - `agent/` directory does not contain a separate `losses` or `optimizers` module — `loss_factory.py` and `optimizer_factory.py` exist (catalog says so). No drift; just noting the catalog's "(networks, losses, optimizers)" phrasing in the structure line refers to factories.
- ❌ Errors:
  - **Concern #6** says the RND `active_mask` "application in forward pass is not visibly applied — verify." It IS applied: `rnd.py:104–105` does `masked_x = x * active_mask`. This concern is incorrect.

### Subsystem 6: Orchestration & Periphery

- ✅ Verified: `CurriculumManager` ABC at `curriculum/base.py:14`; `AdversarialCurriculum` at `adversarial.py:126`; `PerformanceTracker` at `adversarial.py:67`; `StaticCurriculum` in `static.py`; `EpisodeRecorder` and `RecordingWriter` at `recording/recorder.py:22,163`; `RecordedStep`/`EpisodeMetadata`/`EpisodeEndMarker` at `data_structures.py:49,76,102`; `DemoRunner` at `demo/runner.py:37`; `LiveInferenceServer` at `live_inference.py:73`; `UnifiedServer` at `unified_server.py:32`; `DemoDatabase` at `database.py:8`.
- ⚠️  Notes: none material.
- ❌ Errors: none.

## Verdict justification

**PASS-WITH-NOTES.** The catalog's architectural picture is faithful: subsystem boundaries, dependency directions, file-size hot-spots, the "no-defaults" violations, the AspatialSubstrate WAIT bug, the dual-schema hasattr/getattr seam in DACEngine, and the substrate × POMDP coercion are all backed by the source. Line counts are correct except for `compiler.py` (619 → 656) and `compiled.py` (965 → 995), which have grown since the subagent's snapshot but still support the "down from 4,431" narrative.

Two specific concerns are factually wrong and should be corrected in any downstream use:

1. **Subsystem 1, Concern #2** — `semantics.py:15–21` does **not** fall back to `sorted(levels.keys())[0]`; it raises `ValueError`. The "Status: safe" conclusion is right but for the wrong reason.
2. **Subsystem 5, Concern #6** — `RNDNetwork.forward()` **does** apply `active_mask` (line 105). The concern's "verify" prompt has been satisfied; the answer is "applied correctly".

Three secondary cleanups for the catalog (non-blocking):

- The `compiled.py:68–69` line citation for `agent_profile`/`item_profiles` should be **lines 92–93**.
- `effects/scheduler.py` defines `Scheduler`, not `EffectScheduler`.
- `NullItemManager` is duplicated across `environment/null_managers.py`, `effects/manager.py`, and `effects/context.py` — the "(ENV-009) consolidation" claim is incomplete.

None of these change the cross-subsystem summary or the prioritisation of `vectorized_env.py` as the next refactor target.
