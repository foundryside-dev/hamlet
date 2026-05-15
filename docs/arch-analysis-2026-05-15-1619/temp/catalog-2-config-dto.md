## Configuration / DTO Layer

**Location:** `src/townlet/config/`

**Responsibility:** Provide strictly-typed Pydantic DTOs for all hierarchical v2.1 YAML configuration files, enforcing explicit specification of every behavioral parameter at load-time.

**Key Components:** (22 modules total)

### v2.1 Hierarchical Configuration (Primary)
- `experiment_config.py` — Experiment-level orchestration (metadata, curriculum level sequence)
- `stratum_config.py` — Substrate & temporal capability declarations per level
- `environment_config.py` — Global meter/cascade/modulation/affordance registry
- `agent_config.py` — Perception, drive (reward), and brain (network architecture) configs
- `actions_config.py` — Substrate & custom action definitions, label presets
- `bars_v2_config.py` — Per-level meter configurations (initial, depletion, recovery, bounds)
- `affordances_v2_config.py` — Per-level affordance parameters & modulations
- `training_v2_config.py` — Per-level training orchestration (population, Q-learning, replay, exploration, curriculum strategy)
- `curriculum_config.py` — Per-level vision mode, temporal settings, curriculum overrides

### Supporting Configurations
- `drive_as_code.py` — Declarative DAC reward function schemas (extrinsic, intrinsic, shaping)
- `effects_config.py` — Effect pipeline definitions (commands, reapply policies, lifecycle)
- `items_config.py` — Item catalog, appearance, spawn conditions, effects
- `vfs_profiles_config.py` — VFS variable observation profiles & normalization
- `vfs_config.py` — VFS variable registry
- `brain_config.py` — Neural network architecture (feedforward, recurrent, dueling, loss)
- `capability_config.py` — VFS capability declarations
- `cues.py` — Internal meter state → observable cue mappings
- `affordance_masking.py` — Affordance visibility masking metadata
- `exploration.py` — Loader for ExplorationConfig (RND, annealing, epsilon-greedy)

### Base Infrastructure
- `base.py` — YAML loading and validation error formatting utilities
- `__init__.py` — v2.1 public API (no legacy re-exports)

**No-Defaults Discipline:**

The package enforces strict "no implicit defaults" via three mechanisms:

1. **Pydantic Field Requirements:** All behavioral fields use `Field(...)` (ellipsis) to mark required fields. Optional fields explicitly use `Field(default=None)` or `default_factory=list/dict` with documented intent.
   - Example (required): `version: str = Field(..., description="Config schema version")`
   - Example (optional): `costs: dict[str, float] | None = Field(default=None, description="Optional per-step meter costs")`

2. **StrictBaseModel:** All config classes inherit from `BaseModel` with `ConfigDict(extra="forbid")` to reject unexpected YAML keys.

3. **Validators & Model Post-Validators:** Each DTO includes `@field_validator` and `@model_validator(mode="after")` rules that reject invalid or incomplete configurations at parse time.
   - Example: `OpeningHoursConfig.validate_schedule_required_when_enabled()` ensures schedule is non-empty when enabled=true
   - Example: `MeterBoundsConfig.validate_bounds_order()` ensures min < max
   - Example: `EffectDefinitionConfig.parse_command_dicts()` converts dicts to typed CommandConfig objects

4. **Lint Enforcement:** `scripts/no_defaults_lint.py` catches function defaults, logical-OR defaults, and framework calls with implicit defaults at CI-time.

**Antipatterns Found:**

1. **effects_config.py (observable field):** `observable: bool = Field(default=True)` — should this be required? The no-defaults discipline suggests effects _must_ declare observability intent.
   - Line 245 violates the explicit-intent principle if the YAML can omit observability. Consider `Field(...)` instead.

2. **effects_config.py (optional command lists):** Lines 248–251 define lifecycle command pipelines with `default=[]` (empty list). This is acceptable for optional features (empty command = no-op), but the distinction between "omitted" and "explicitly empty" is blurred in YAML. Consider documenting whether omission is equivalent to `[]`.

3. **drive_as_code.py (logging flags):** Lines 602–605 define `log_components`, `log_modifiers` with `default=True/False`. These are behavioral; explicit YAML declaration is preferred over implicit defaults.

4. **effects_config.py & drive_as_code.py (version field defaults):** `version: Literal["1.0"] = Field(default="1.0")` — version string should be required to prevent silent schema mismatches on schema bumps. Recommend `Field(...)` to force explicit declaration.

**Versioning:**

- **v2.1 Primary:** `bars_v2_config.py`, `affordances_v2_config.py`, `training_v2_config.py` — modern full-spec configs
- **v2.1 Complete Hierarchy:** All experiment/stratum/environment/agent/actions/curriculum configs are v2.1 (no v1 stragglers)
- **DAC is Content, Not Version:** `drive_as_code.py` defines DAC syntax but is version-agnostic; DAC configs carry their own `version` field
- **No v1 Burden:** The config layer exposes no v1 compatibility shims. The UniverseCompiler boundary enforces v2.1 strict-schema entry point.

**Dependencies:**

**Inbound:** Configuration consumed by:
- `UniverseCompiler.compile()` via `load_v21_configs()` loader
- `RawConfigsV21.__post_init__()` type assembly
- Domain compilers: `ActionCompiler`, `EffectsCompiler`, `MetadataCompiler`, `VFSCompiler`, `OptimizationCompiler`
- Runtime: `VectorizedHamletEnv` and `ItemManager` consume compiled artifacts derived from these DTOs

**Outbound:** 
- Pydantic v2 `BaseModel`
- PyYAML for loading
- Internal cross-imports: `affordances_v2_config` imports `CommandConfig` from `effects_config`; `training_v2_config` imports from `base`

**Patterns Observed:**

1. **One DTO per YAML:** Each major config file (experiment.yaml, environment.yaml, training.yaml, etc.) has a corresponding DTO module, with classes wrapping top-level keys and nested structures.

2. **Pydantic v2 Style:** All classes explicitly use `model_config = ConfigDict(extra="forbid")` for strictness. Required fields use `Field(...)` (ellipsis literal). Validators are `@field_validator` and `@model_validator(mode="after")`.

3. **from_yaml() Classmethod:** Load-friendly pattern; most config classes provide a `@classmethod from_yaml(path: Path)` that handles YAML parsing and instantiation in one call.

4. **Error Context Preservation:** `base.py` provides `format_validation_error()` to transform cryptic Pydantic errors into actionable messages that guide operators to the correct YAML template.

5. **Conditional Validation:** Advanced validators like `ModifierConfig.validate_source()` enforce "exactly one of" constraints and cross-field dependencies at the DTO layer, not later.

**Concerns:**

1. **Observable Field Antipattern (effects_config.py:245):** Implicit `default=True` for observability violates explicit-intent discipline. High-risk for silent incorrect behavior if YAML author forgets observability declaration.

2. **Version Field Defaults (effects_config.py:267, drive_as_code.py:634):** Hard-coded version defaults (`default="1.0"`) risk silent schema mismatches when schemas evolve. Should be required fields.

3. **Empty Lifecycle Commands (effects_config.py:248–251):** Whether `on_spawn: []` (empty) is equivalent to omission is unclear. YAML may allow omission, but DTOs show empty list as default. Document or enforce required empty arrays in YAML.

4. **DAC is Self-Contained:** `drive_as_code.py` is feature-complete for DAC syntax but is large (670+ lines) and may benefit from submodule organization (RangeConfig, ModifierConfig, strategies all in one file).

5. **No V1 Legacy Visible:** The codebase has successfully eliminated v1 stragglers from the config layer; all imports in `__init__.py` are v2.1. However, confirm that old experiment directories cannot silently load as v2.1.

**Confidence:** **High**

Evidence:
- All 22 files reviewed and cross-checked against commit 92979107 (recent dead-default cleanup)
- `__init__.py` explicitly omits legacy loaders
- `base.py` and `format_validation_error()` demonstrate intentional error-first design
- Pydantic v2 `Field(...)` pattern is consistent across modules
- Field validators and model validators are comprehensive and tested
- Recent plan (docs/plans/2026-05-15-compiler-cleanup-modernization.md) confirms Stage 1 owns strict DTO loading
- No-defaults lint script (scripts/no_defaults_lint.py) is active and integrated into CI
