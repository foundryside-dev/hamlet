# SG3 — Configuration DTO Layer

**Location:** `src/townlet/config/` (4,728 LOC, 22 files)
**Confidence:** High for the loaded v2.1 surface and pack layout (cross-checked
against `src/townlet/universe/raw_configs_v21.py` and an actual pack at
`configs/default_curriculum/`). Medium on `agent_config.py` — its classes are
exported via `__init__.py` but I found only one runtime consumer
(`environment/dac_engine.py` importing `DriveConfig`); the rest of the file
duplicates classes that live (canonically) in `brain_config.py` and
`drive_as_code.py`. See Concerns.

## Responsibility

This package is the YAML→runtime boundary. Every operator-authored knob in a
v2.1 config pack is parsed into a Pydantic v2 `BaseModel` here before it is
allowed to influence any compiler, environment, or training code. One file per
logical schema; each file owns the load function for the YAML it gates. The
package is consumed almost exclusively through two surfaces: (a) the v2.1
package loader `townlet.universe.raw_configs_v21.RawConfigsV21.from_experiment_dir`,
which loads the whole pack into one frozen dataclass; and (b) the single
public loader `load_training_v2_config(config_dir)` (re-exported from
`townlet.config`), used by `scripts/run_demo.py:23` to obtain a level's
`TrainingV2Config` for the demo server. The package has no submodule init
files beyond `__init__.py`; everything is flat.

## DTO catalog

Grouped by concern. File paths are `src/townlet/config/<file>`; classes named
`*ConfigRoot` are the body of a YAML file's top-level key.

### Pack-shape DTOs (experiment-level, one per shared YAML)

- **`experiment_config.py` (75 LOC)** — Wraps `experiment.yaml`.
  `ExperimentConfig:49` → `experiment` → `ExperimentConfigRoot:33` with
  `version`, `experiment_name`, `metadata: ExperimentMetadata:21`, and
  `curriculum_levels: list[str]` (the ordered level directory names under
  `levels/`). All fields required (`...`). Loader: `from_yaml(path)` classmethod.

- **`stratum_config.py` (243 LOC)** — Wraps `stratum.yaml`; defines the
  substrate type and observation layout strategy.
  `StratumConfig:217` → `StratumConfigRoot:202` carrying:
  - `substrate: SubstrateConfig:164` — discriminated by `type` ∈ {`grid`,
    `grid3d`, `gridnd`, `continuous`, `continuousnd`, `aspatial`}; a
    `model_validator` enforces that exactly the matching block
    (`GridConfig:44` / `GridNDConfig:79` / `ContinuousConfig:122` /
    `AspatialConfig:158`) is present and others are `None`.
  - `vision_support: Literal["global","partial","both","none"]`,
    `temporal_support: Literal["enabled","disabled"]`,
    `observation_mode: ObservationModeConfig:22` (`full_auto` /
    `max_compact` / `full_manual`).
  - `ContinuousConfig` requires an `ActionDiscretizationConfig:99` block
    (`num_directions ∈ [8,32]`, `num_magnitudes ∈ [3,7]`).

- **`environment_config.py` (178 LOC)** — Wraps `environment.yaml`; the global
  vocabulary that all curriculum levels share.
  `EnvironmentConfig:152` → `EnvironmentConfigRoot:138` carrying lists of
  `MeterConfig:22`, `CascadeConfig:38` (the cascade graph),
  `ModulationConfig:48` (the modulation graph), `AffordanceDefinition:58`
  (the canonical name registry), `VariableConfig:95` (VFS variable specs with
  embedded `NormalizationConfig:73`), and `CueConfig:128` (UI cue triggers).
  Per-level *behavior* is **not** here — only names, descriptions, types,
  and graph edges.

- **`actions_config.py` (85 LOC)** — Wraps `actions.yaml`. Note the docstring
  at `:1`: this is the **parse-time** DTO; runtime action wiring lives in
  `townlet.environment.action_config`. Owns `SubstrateActionsConfig:32`
  (inherit?), `CustomActionConfig:38` (name/description/enabled_by_default
  per custom action), and `ActionLabelsConfig:46`
  (preset ∈ {`gaming`,`6dof`,`cardinal`,`math`}). Uses a local
  `StrictBaseModel:26` instead of base.py.

- **`brain_config.py` (596 LOC)** — Wraps `brain.yaml`. The neural-network
  spec. `BrainConfig:465` owns: `architecture: Literal["feedforward",
  "recurrent","dueling","set_encoder"]` plus the corresponding sub-DTO —
  `FeedforwardConfig:18`, `RecurrentConfig:134` (which composes
  `CNNEncoderConfig:38` + four `MLPEncoderConfig:90` blocks + `LSTMConfig:116`),
  `DuelingConfig:176`, `SetEncoderConfig:206`. Optimizer/loss live in
  `OptimizerConfig:255` (per-type optional fields with model-validator
  cross-checks), `ScheduleConfig:219`, `LossConfig:330`, `ReplayConfig:390`,
  and a top-level `QLearningConfig:455`. Also owns two utilities:
  `compute_brain_hash(config) → sha256` at `:534` (for checkpoint provenance)
  and `apply_training_overrides(brain, training)` at `:562` (lets per-level
  `training.yaml` override gamma / learning_rate / target_update_frequency
  / use_double_dqn from `brain.yaml`).

- **`items_config.py` (396 LOC)** — Wraps both `items.yaml` (experiment-level
  catalog) and per-level `items.yaml` overlays. `ItemsCatalogConfig:221`
  holds a list of `ItemTypeConfig:138` (id, vfs_profile reference,
  `ItemInteractionsConfig:77` of Effects-syntax commands, optional
  duration/cooldown). Spawn rules live in `SpawnScheduleConfig:266` and
  `SpawnPlacementConfig:313`. `ItemsAppearanceConfig:386` (with
  `ItemAppearanceRuleConfig:340`) is the per-level overlay. The free function
  `build_item_command_action_name(item_id, command_name, scope)` at `:72`
  produces a stable action-space name for custom item verbs.

- **`effects_config.py` (267 LOC)** — Wraps `effects.yaml`. Two
  `StrEnum`s (`ReapplyPolicy:19`, `EffectScope:43`) with case-insensitive
  `_missing_` hooks. `EffectsConfig:250` is a list of
  `EffectDefinitionConfig:214` (id, scope, duration, intensity,
  reapply_policy, observable, plus four command-pipeline lifecycle hooks
  `on_spawn` / `on_tick` / `on_despawn` / `on_interrupt`). `CommandConfig:67`
  is the universal command unit (modify / spawn_effect / spawn_item / if /
  for_each / switch / reduce / parallel / delay / sample) reused from
  affordances and items.

- **`vfs_profiles_config.py` (349 LOC)** — Wraps `vfs_profiles.yaml`. Three
  parallel hierarchies for the three VFS scopes:
  `GlobalVFSVariableConfig:20` + `GlobalVFSProfileConfig:95`,
  `AgentVFSVariableConfig:128` + `AgentVFSProfileConfig:205`,
  `ItemVFSVariableConfig:238` + `ItemVFSProfileConfig:286`, gathered under
  `VFSProfilesConfig:321`. Each variable schema enforces *exactly one*
  initialiser via `validate_value_xor_expression` (initial_value / mode /
  expression), with tensor types requiring matching `shape`. Note: the
  three variable schemas duplicate almost identical logic — they differ
  mainly by allowed `type` literals and ref-type kinds. The agent and item
  variants populate optional `id`/`exposed_to` metadata defaults in a
  `model_validator` (a no-defaults exception, but on metadata only — see
  No-defaults section).

- **`vfs_config.py` (19 LOC)** — A thin wrapper:
  `VariablesReferenceConfig` parses the experiment-level optional
  `variables_reference.yaml` and rejects item-scoped variables (those must
  live in `vfs_profiles.yaml`). The actual `VariableDef` schema is imported
  from `townlet.vfs.schema`.

- **`cues.py` (128 LOC)** — Standalone loader for `cues.yaml`. Owns
  `SimpleCueConfig:28`, `CompoundCueConfig:43`, `VisualCueConfig:67` (range
  validated to lie within `[0,1]`), and `CuesConfig:85` with `simple_cues`,
  `compound_cues`, `visual_cues`. The narrative-metadata fields
  (`derived_cues`, `behavioral_cues`, `cue_reliability`, `training_strategy`,
  `teaching_value`, `game_design_insights`, `implementation_phases`,
  `future_extensions`, `current_status`, `next_steps`) are typed
  `dict[str, Any] | None` and look like operator-authored documentation —
  no validators touch them. Free loader: `load_cues_config(cues_path):113`.

### Per-level DTOs (one per file under `levels/<L>/`)

- **`curriculum_config.py` (81 LOC)** — Wraps each level's `curriculum.yaml`.
  `CurriculumConfig:55` → `CurriculumConfigRoot:24` with
  `active_vision: Literal["global","partial"]`, `vision_range: float`
  (`[0.0,1.0]`), `active_temporal: bool`, and a conditionally-required
  `day_length: int | None` enforced by `validate_day_length:36` (required
  iff `active_temporal=true`, else must be null).

- **`curriculum.py` (13 LOC)** — Thin re-export of `CurriculumConfig` plus a
  `load_curriculum_config(config_dir)` helper that just builds the path and
  defers to `CurriculumConfig.from_yaml`. The split exists only so
  `__init__.py` can expose both name styles.

- **`bars_v2_config.py` (218 LOC)** — Wraps each level's `bars.yaml`.
  `BarsV2Config:140` (version `Literal["1.0"]`) carries:
  - `meters: list[MeterConfig:70]` — each meter has
    `MeterDepletionConfig:34` (`passive`/`move`/`interact` drains),
    `MeterRecoveryConfig:44` (`natural`), `MeterBoundsConfig:52`
    (`min`/`max`/`lethal_min`/`lethal_max`), and an `initial` value
    constrained to lie within bounds.
  - `cascades: list[CascadeParamConfig:106]` — `(source, target, threshold,
    strength)` with a self-cascade ban. The README convention "strength = 0.0
    to explicitly disable a cascade" is enforced as a docstring, not a
    validator.
  - Field validators forbid duplicate meter names and duplicate
    `(source,target)` cascade pairs.

- **`affordances_v2_config.py` (280 LOC)** — Wraps each level's
  `affordances.yaml`. `AffordancesV2Config:223` carries:
  - `affordances: list[AffordanceParamConfig:95]` — name (must match the
    experiment-level registry), `costs` / `costs_per_tick` (affordability
    gates), `interactions: dict[stage, list[CommandConfig]]` (Effects-syntax
    outcomes, validated against the stage whitelist `on_start` / `per_tick`
    / `on_completion` / `on_early_exit` / `on_failure`), optional
    `interaction_type` ∈ {`instant`,`multi_tick`,`dual`} with conditional
    `duration_ticks`, `OpeningHoursConfig:55` (enabled+schedule), and
    `DeploymentConfig:76` (fixed positions / random / procedural).
  - `modulations: list[ModulationParamConfig:187]` — `(bar, affordances[],
    type=linear_multiplier, threshold, min_multiplier)`.
  - `CommandConfig` is imported from `effects_config` — the unified Effects
    syntax bridge.

- **`training_v2_config.py` (442 LOC)** — Wraps each level's `training.yaml`.
  Top-level `TrainingV2Config:337` is composed of fourteen sub-DTOs:
  `PopulationConfig:54` (size), `EnabledActionsConfig:62` (curriculum-level
  enables of custom actions with `enabled_by_default=false`),
  `QLearningConfig:85` (the four per-level overrides applied by
  `apply_training_overrides`), `ReplayBufferConfig:99` (with two
  model-validators: `min_size ≤ capacity` and `batch_size ≤ min_size`),
  `ExplorationConfig:129` (`epsilon_start ≥ epsilon_end`), `IntrinsicConfig:169`
  composing `RNDConfig:150` and `AnnealingConfig:159`, `TrainingLoopConfig:212`
  carrying nested `EvaluationConfig:194` and `CheckpointingConfig:203`,
  `CurriculumStrategyConfig:287` (`static` | `adversarial` discriminated
  union with `AdversarialCurriculumConfig:235` — has 4 stage advancement /
  retreat thresholds and a `survival_retreat < survival_advance` invariant).
  Two file-level sibling sections are also represented:
  `RunMetadataConfig:308` and `RecordingConfig:325`. The loader at `:393`
  parses YAML, lifts the file-level `run_metadata` / `recording` siblings
  into the same payload as `training`, then constructs the DTO. Notable:
  `enabled_affordances: list[str]` lives directly on `TrainingV2Config`
  (not on its own sub-DTO).

- **`drive_as_code.py` (681 LOC)** — Wraps each level's `drive.yaml` (note
  the file is named `drive.yaml`, not `drive_as_code.yaml` as CLAUDE.md
  states — see Concerns). `DriveAsCodeConfig:608` carries:
  - `modifiers: dict[str, ModifierConfig:51]` — each modifier sources from
    a `bar` xor `variable` and contains `ranges: list[RangeConfig:21]`,
    validated to cover `[0.0, 1.0]` exactly (no gaps, no overlaps) by
    `validate_ranges_coverage:87`.
  - `extrinsic: ExtrinsicStrategyConfig:155` — nine-way `type` literal
    (`multiplicative` / `constant_base_with_shaped_bonus` / `additive_unweighted` /
    `weighted_sum` / `polynomial` / `threshold_based` / `aggregation` /
    `vfs_variable` / `hybrid`); each strategy reads different optional
    fields (bars / base_reward / bar_bonuses / variable / etc.) — no
    cross-validator enforces which fields a given strategy needs.
  - `intrinsic: IntrinsicStrategyConfig:209` — five-way `strategy` literal,
    `base_weight`, `apply_modifiers`, plus four optional
    `dict[str, Any]`-typed config blobs for each strategy variant.
  - `shaping: list[ShapingBonusConfig]` — discriminated union of 12 bonus
    DTOs (`ApproachRewardConfig:276`, `CompletionBonusConfig:298`,
    `EfficiencyBonusConfig:318`, `StateAchievementConfig:353`,
    `VFSVariableBonusConfig:376`, `StreakBonusConfig:396`,
    `DiversityBonusConfig:418`, `TimingBonusConfig:460`,
    `EconomicEfficiencyConfig:482`, `BalanceBonusConfig:504`,
    `CrisisAvoidanceConfig:526`, `VfsVariableConfig:549`), each tagged by a
    `type` literal.
  - `composition: CompositionConfig:587` — `normalize` / `clip` /
    `log_components` / `log_modifiers`. **All four fields have defaults**
    on this DTO (see Concerns).
  - A `model_validator` at `:641` cross-checks that every modifier name
    referenced by `extrinsic.apply_modifiers` or
    `intrinsic.apply_modifiers` is defined in the `modifiers` map.

### Auxiliary DTOs (referenced by other DTOs, not files-of-their-own)

- **`capability_config.py` (112 LOC)** — Six discriminated `*Capability`
  classes (`MultiTickCapability`, `CooldownCapability`,
  `MeterGatedCapability`, `SkillScalingCapability`,
  `ProbabilisticCapability`, `PrerequisiteCapability`) and a union alias
  `CapabilityConfig`. Not referenced by `__init__.py` or by any v2.1 loader
  I could find — see Concerns.
- **`affordance_masking.py` (47 LOC)** — `BarConstraint` and `ModeConfig`
  for hour-of-day availability. Same observation: not wired into the v2.1
  load path.
- **`exploration.py` (23 LOC)** — A standalone single-section loader that
  reads `training.yaml:training.exploration` and constructs the
  `ExplorationConfig` *re-exported from `training_v2_config`*. Convenience
  shim for callers that only want exploration.

### Public entry-points

| File | Free loader | Wraps |
|------|------------|-------|
| `training_v2_config.py` | `load_training_v2_config(config_dir)` | `training.yaml` |
| `bars_v2_config.py` | `load_bars_v2_config(config_dir)` | `bars.yaml` |
| `affordances_v2_config.py` | `load_affordances_v2_config(config_dir)` | `affordances.yaml` |
| `curriculum.py` | `load_curriculum_config(config_dir)` | `curriculum.yaml` |
| `brain_config.py` | `load_brain_config(config_dir)` | `brain.yaml` |
| `drive_as_code.py` | `load_drive_as_code_config(config_dir)` | `drive.yaml` |
| `cues.py` | `load_cues_config(cues_path)` | `cues.yaml` (path, not dir) |
| `exploration.py` | `load_exploration_config(config_dir)` | section of `training.yaml` |
| `experiment_config.py` | `ExperimentConfig.from_yaml(path)` | `experiment.yaml` |
| `stratum_config.py` | `StratumConfig.from_yaml(path)` | `stratum.yaml` |
| `environment_config.py` | `EnvironmentConfig.from_yaml(path)` | `environment.yaml` |
| `actions_config.py` | `ActionsConfig.from_yaml(path)` | `actions.yaml` |
| `curriculum_config.py` | `CurriculumConfig.from_yaml(path)` | `curriculum.yaml` |

`base.py:14 load_yaml_section(config_dir, filename, section)` is the shared
"open YAML, fetch top-level key" helper used by every `load_*_config`. Most
of these loaders wrap pydantic `ValidationError` in `base.py:55
format_validation_error(error, context)` which produces a banner message
ending in "All parameters must be explicitly specified (no-defaults
principle)" with a pointer to `configs/templates/`.

## No-defaults enforcement

The CLAUDE.md "No-Defaults Principle" claim is **partially supported by the
code and not enforced at the config layer alone**. Three layers are at play:

1. **Pydantic field-level**: 142 of the configs' BaseModel classes use
   `ConfigDict(extra="forbid")` (counted by `grep -c` of the source). Two
   files use `extra="allow"` (`training_v2_config.py:328`
   `RecordingConfig` — for forward-compatible recorder backends — and
   `agent_config.py:22,96` `PerceptionConfig`/`ShapingConfig` — both
   placeholder schemas for not-yet-finalised systems).
2. **Required fields**: The hierarchical-pack DTOs
   (`StratumConfigRoot`, `EnvironmentConfigRoot`, `ActionsConfigRoot`,
   `BarsV2Config`, `AffordancesV2Config`, `TrainingV2Config`,
   `BrainConfig`, etc.) declare every field with `Field(...)` /
   `Field(description=...)` and no `default=`, so missing keys raise
   `ValidationError`. The model_validators piled on top
   (`ReplayBufferConfig.validate_min_size_le_capacity`,
   `ExplorationConfig.validate_epsilon_start_ge_end`,
   `MeterConfig.validate_initial_in_bounds`,
   `AdversarialCurriculumConfig.validate_retreat_lt_advance`,
   etc.) enforce relational invariants between fields.
3. **Project-wide structural lint**: `scripts/no_defaults_lint.py` is an AST
   walker that flags `default=` / `default_factory=` and Python function
   parameter defaults across `src/townlet/`. It is whitelist-driven; the
   intent is to forbid hidden defaults in non-config code too. This is the
   global side of the "no defaults" policy; the DTO layer is the local side.

`base.py` does **not** provide a custom BaseModel or strict-by-default base —
each file repeats `model_config = ConfigDict(extra="forbid")` on every class.
`actions_config.py:26` defines its own `StrictBaseModel` and uses it as a
parent, but no other file does. Refactoring these into a shared base is a
clean-up opportunity.

**Caveats on "no defaults"**:

- `affordances_v2_config.py:62 OpeningHoursConfig.schedule = default_factory=list`
  — defaulted, but guarded by a validator that rejects empty lists when
  `enabled=true`.
- `vfs_profiles_config.py:115,225 default_metadata` model-validators
  populate empty `id` and `exposed_to` fields on agent/global VFS variables
  after parsing — a deliberate defaulting on metadata.
- `drive_as_code.py:602-605 CompositionConfig` — `normalize`, `clip`,
  `log_components`, `log_modifiers` all carry hardcoded defaults
  (`False`, `None`, `True`, `True`). This is the largest concrete
  no-defaults violation I found, and it sits on a hot reward-system DTO.
- `drive_as_code.py:634,635,638,639 DriveAsCodeConfig` — `version`,
  `modifiers`, `shaping`, `composition` all carry defaults. So a
  `drive.yaml` containing only `extrinsic:` and `intrinsic:` will validate
  silently.

## Config pack actual layout

The actual on-disk shape of `configs/default_curriculum/` (what the v2.1
loader expects, per `universe/raw_configs_v21.py`):

```
configs/default_curriculum/
├── experiment.yaml              → ExperimentConfig
├── stratum.yaml                 → StratumConfig
├── environment.yaml             → EnvironmentConfig
├── actions.yaml                 → ActionsConfig
├── brain.yaml                   → BrainConfig (loaded via load_brain_config)
├── effects.yaml                 → EffectsConfig (optional)
├── items.yaml                   → ItemsCatalogConfig (optional)
├── vfs_profiles.yaml            → VFSProfilesConfig (optional)
├── variables_reference.yaml     → tuple[VariableDef, ...] (optional)
└── levels/
    ├── L0_0_minimal/
    ├── L0_5_dual_resource/
    ├── L1_full_observability/
    ├── L2_partial_observability/
    └── L3_temporal_mechanics/
        ├── curriculum.yaml      → CurriculumConfig
        ├── bars.yaml            → BarsV2Config
        ├── affordances.yaml     → AffordancesV2Config
        ├── drive.yaml           → DriveAsCodeConfig   (NB: file is drive.yaml,
        │                          parsed key is `drive:`)
        ├── training.yaml        → TrainingV2Config + run_metadata + recording
        └── items.yaml           → ItemsAppearanceConfig (optional per-level)
```

I verified this by listing all five level directories — every one contains
exactly the same five files (`curriculum.yaml`, `bars.yaml`,
`affordances.yaml`, `drive.yaml`, `training.yaml`). The L1 level has no
per-level `items.yaml`, matching the optional treatment in the loader at
`raw_configs_v21.py:247-251`.

`configs/reference/model_pack/` mirrors the same layout and exists as a
"complete reference example" — `configs/reference/config-complete.yaml` is
a single-file flattened variant (separate from the loader path).

## Versioning

Only three DTO files carry a `_v2` filename suffix —
`bars_v2_config.py`, `affordances_v2_config.py`, `training_v2_config.py` —
and their internal `version` field is the literal string `"1.0"`. The
suffix encodes the **pack-layout version** (the hierarchical v2.1 shape),
not the schema version of the file itself. Notes:

- `__init__.py:25` declares `CONFIG_SCHEMA_VERSION = "2.1.0"` — the pack
  version, separate from each DTO's `version` literal.
- `curriculum_config.py`, `environment_config.py`, `experiment_config.py`,
  `stratum_config.py`, `actions_config.py` have **no** `_v2` suffix but are
  v2.1-native (they only exist for the hierarchical pack — see
  `__init__.py:5-6` "Legacy training.yaml and flat bars/cascades/affordances
  loaders are not re-exported"). They are *implicitly* v2 schemas.
- `cues.py` and `drive_as_code.py` are also unsuffixed but only exist in
  v2.1 form.
- `version` is a `Literal["1.0"]` in `BarsV2Config`, `AffordancesV2Config`,
  `TrainingV2Config`, and `ItemsCatalogConfig` (so a typo to `"1.1"` will
  hard-fail). In `EnvironmentConfigRoot`, `StratumConfigRoot`,
  `CurriculumConfigRoot`, `ExperimentConfigRoot`, `ActionsConfigRoot`, and
  `AgentConfigRoot`, `version` is a free-form `str`. `CuesConfig.version`
  is `Field(min_length=1)`. `DriveAsCodeConfig.version` is `str` with a
  `"1.0"` default.

There is no `_v1` sibling for any of these files; this is consistent with
the pre-release "delete legacy code" stance.

## Public API surface

`townlet.config.__init__` re-exports (and nothing else):

```
CONFIG_SCHEMA_VERSION = "2.1.0"

# DTO classes
ExperimentConfig, StratumConfig, EnvironmentConfig, ActionsConfig,
AgentConfig, BarsV2Config, AffordancesV2Config, CurriculumConfig,
TrainingV2Config

# Free loaders
load_bars_v2_config, load_affordances_v2_config,
load_curriculum_config, load_training_v2_config
```

`__init__.py:5-6` explicitly states "Legacy training.yaml and flat
bars/cascades/affordances loaders are not re-exported" — a deliberate
narrowing of the surface. Note that `BrainConfig`, `DriveAsCodeConfig`,
`EffectsConfig`, `ItemsCatalogConfig`, `VFSProfilesConfig`, and `CuesConfig`
are **not** exposed via `__init__.py` — they are imported directly by
`townlet.universe.raw_configs_v21` and friends, which is the production
load path. The exported surface is the "shallow consumer" API; the deep
consumer is the v2.1 raw-config aggregator.

`scripts/run_demo.py:23` imports `load_training_v2_config` directly from
`townlet.config.training_v2_config` — the only non-aggregator entry point.
The rest of the universe compiler reaches into modules by full path.

## Dependencies

**Inbound** (modules outside `src/townlet/config/` that import from it):

- `townlet/universe/raw_configs_v21.py` — imports every public DTO; the
  aggregator that produces `RawConfigsV21`. This is the single
  most-coupled consumer.
- `townlet/universe/compilers/{metadata,optimization,vfs,actions,effects}.py`
  — each compiler stage pulls the specific DTOs it needs
  (`BarsV2Config`, `AffordancesV2Config`, `EnvironmentConfig`,
  `StratumConfig`, `ActionsConfig`, `ItemsCatalogConfig`, `EffectsConfig`,
  `VFSProfilesConfig`, `VariableConfig`).
- `townlet/universe/{compiler.py,symbol_table.py,cues_compiler.py,
  validation/references.py,loaders/preflight.py}` — assorted cross-cutters.
- `townlet/substrate/factory.py` — imports `SubstrateConfig` from
  `stratum_config.py`.
- `townlet/agent/{loss_factory,optimizer_factory,network_factory}.py` —
  import `LossConfig`, `OptimizerConfig`, `ScheduleConfig`, `DuelingConfig`,
  `FeedforwardConfig`, `RecurrentConfig`, `SetEncoderConfig` from
  `brain_config.py`.
- `townlet/population/vectorized.py` — `BrainConfig`.
- `townlet/curriculum/factory.py` — `TrainingV2Config`.
- `townlet/items/manager.py`, `townlet/effects/{schema,catalog,manager,
  parser,executor}.py` — `ItemsCatalogConfig`, `ItemsAppearanceConfig`,
  `EffectScope`, `EffectsConfig`, `CommandConfig`.
- `townlet/environment/dac_engine.py` — `DriveConfig` from
  `agent_config.py` (the only inbound link to `agent_config.py` I found).
- `townlet/demo/{runner,unified_server}.py` — `compute_brain_hash`,
  `apply_training_overrides`, `TrainingV2Config`, `load_training_v2_config`.
- `scripts/run_demo.py` — `load_training_v2_config`.

**Outbound** (third-party / inner-townlet dependencies):

- `pydantic` (v2 — uses `BaseModel`, `ConfigDict(extra=...)`,
  `field_validator`, `model_validator`, `ValidationError`, `Field`).
- `pyyaml` (every `from_yaml` / `load_*_config`).
- Within townlet: `townlet.vfs.schema` (`VariableDef`, `VariableScope`,
  `load_variables_reference_config`) is imported by `vfs_config.py`.
  `vfs_config.py` is the only config module that crosses into another
  townlet package — the rest of the config tree is otherwise self-contained.

## Patterns observed

- **One DTO file per YAML, one classmethod loader per file.** The convention
  is `<Section>Config` for the top-level wrapper, `<Section>ConfigRoot` for
  the body of the parsed key, and free `load_<section>_config(config_dir)`
  for the by-directory loader. The `from_yaml(path)` classmethod and the
  free `load_*` function coexist; the free loader is preferred (it uses
  `base.py.load_yaml_section` for nicer errors).
- **Discriminated unions on a `type: Literal[...]` field, plus a
  `model_validator(mode="after")` that asserts the matching sub-block is
  present.** Used in `SubstrateConfig`, `BrainConfig` architecture,
  `ExtrinsicStrategyConfig` (partially — see Concerns), the capability and
  effects systems.
- **Cross-field invariants via `model_validator(mode="after")`.** Replay
  buffer ordering, exploration ordering, cascade self-link ban, modifier
  reference resolution, schedule-type required-fields, opening-hours non-empty
  when enabled — these are routinely encoded as named validators with
  descriptive error messages.
- **Helpful errors over cryptic ones.** `base.py.format_validation_error`
  reformats `ValidationError` into an "❌ <context> VALIDATION FAILED"
  banner and routes operators to `configs/templates/`. Almost every free
  loader wraps the pydantic exception in a `ValueError` via this helper.
- **Effects-command reuse.** `CommandConfig` from `effects_config.py` is
  embedded in `affordances_v2_config.py:128` (as
  `dict[stage, list[CommandConfig]]`), in `items_config.py:171`, and in
  `effects_config.py` itself — a single command grammar shared across
  three subsystems.
- **`extra="forbid"` ubiquity.** With two exceptions, every BaseModel
  forbids unrecognised keys. This means a typo in a YAML field name fails
  loudly.
- **Provenance hashes co-located with DTOs.** `compute_brain_hash` lives in
  `brain_config.py` rather than in checkpoint code, because the canonical
  serialisation is a property of the DTO. The DAC equivalent (`drive_hash`,
  documented in CLAUDE.md) doesn't appear to live in `drive_as_code.py` —
  it's presumably computed elsewhere.

## Concerns

- **`agent_config.py` (362 LOC) duplicates schemas that exist canonically
  elsewhere and is barely used.** It re-defines its own
  `FeedforwardConfig`, `RecurrentConfig`, `LSTMConfig`, `OptimizerConfig`,
  `QLearningConfig`, `BrainConfig`, `LossConfig` (parallel to
  `brain_config.py`) and `ExtrinsicConfig`, `IntrinsicConfig`,
  `AnnealingConfig`, `CompositionConfig`, `DriveConfig` (parallel to
  `drive_as_code.py`). The only inbound consumer I found in `src/townlet/`
  is `environment/dac_engine.py` which imports `DriveConfig`. `AgentConfig`
  itself is exported by `__init__.py:15` but I could not find a runtime
  loader that produces one (no `agent.yaml` exists in `default_curriculum`).
  This looks like a v1 / pre-split scaffold that the v2.1 brain/drive
  refactor left orphaned. Per the pre-release "delete legacy" rule, this
  file (or large portions of it) is a candidate for deletion.

- **`capability_config.py` and `affordance_masking.py` appear orphaned.**
  Neither module is imported by anything in `src/townlet/` outside the
  config package (`grep -rn "capability_config\|affordance_masking"
  src/townlet/` returns only the file definitions). The v2.1 affordance
  flow handles `interaction_type`, `duration_ticks`, `opening_hours`, and
  `costs` directly on `AffordanceParamConfig`. These two files look like
  prior-iteration designs that were superseded.

- **`drive_as_code.CompositionConfig` carries hardcoded defaults** on all
  four of its fields (`normalize=False`, `clip=None`,
  `log_components=True`, `log_modifiers=True`). Per CLAUDE.md "make fields
  required, update all configs with explicit values", these defaults are
  antipatterns — and `drive.yaml` is hot-path config. Same critique for
  `DriveAsCodeConfig.version`, `.modifiers`, `.shaping`, and `.composition`,
  all of which have defaults.

- **`ExtrinsicStrategyConfig` is a `type` literal with nine variants but
  no validator enforces the per-variant required fields.** Every per-variant
  field (`base_reward`, `bar_bonuses`, `variable_bonuses`, `base`, `bars`,
  `variable`) is optional with a default, so e.g. `{type:
  "vfs_variable"}` without a `variable` will pydantic-validate cleanly and
  blow up downstream. This is the typical motivation for a Pydantic v2
  discriminated union; consider refactoring into nine sub-DTOs tagged by
  `type`, mirroring how `ShapingBonusConfig` is already done.

- **`IntrinsicStrategyConfig`'s strategy-specific configs are
  `dict[str, Any] | None`** (`rnd_config`, `icm_config`, `count_config`,
  `adaptive_config` at `drive_as_code.py:242-245`). Untyped dicts in a
  no-defaults regime defeat the purpose; these should be typed sub-DTOs.

- **CLAUDE.md is stale on three concrete claims.** (1) It states "All config
  packs **MUST** include `variables_reference.yaml`" — but
  `raw_configs_v21.py:202-211` treats this file as optional, and the actual
  `configs/default_curriculum/` does not contain one. (2) It states "DAC
  reward specification (REQUIRED)" with filename `drive_as_code.yaml` — but
  the actual filename is `drive.yaml` (parsed key `drive:`). (3) It refers
  to `configs/<level>/` flat packs (no `levels/` subdirectory) which no
  longer exist. The hierarchical layout (`<pack>/levels/<level>/`) is
  current. Recommend updating CLAUDE.md.

- **Two near-identical `ExplorationConfig`s.** One in
  `training_v2_config.py:129` (the v2.1 canonical) and one re-exported by
  `exploration.py:5`. The shim exists for callers who only want exploration;
  it does its own YAML loading via `load_yaml_section`. Acceptable, but the
  duplication-by-re-export is easy to misread; a single import path would
  be cleaner.

- **`vfs_profiles_config.py`'s three variable schemas are 90% copy-paste**
  (`GlobalVFSVariableConfig`, `AgentVFSVariableConfig`,
  `ItemVFSVariableConfig` share `validate_value_xor_expression` and
  `validate_tensor_shape` verbatim). Extract to a mixin or shared base.

- **`base.py` is named "Base configuration utilities" but provides no base
  class** — only two free helpers. Either the file should host a
  `StrictBaseModel` (and `actions_config.py:26`'s local one should be
  moved) or it should be renamed (`yaml_utils.py`?). The current name
  implies a class hierarchy that doesn't exist.

- **Test coverage uneven.** `tests/test_townlet/unit/config/` contains
  ten test files covering `base`, `affordance_masking`, `config_pack_factory`,
  `cues`, `curriculum`, `drive_as_code`, `environment`, `exploration`,
  `stratum`, `training_v2`, `vfs_profiles`. Conspicuously **missing**:
  `bars_v2_config`, `affordances_v2_config`, `brain_config`,
  `experiment_config`, `actions_config`, `items_config`, `effects_config`,
  `agent_config`, `capability_config`, `vfs_config`. The two largest DTO
  files (`drive_as_code.py` 681 LOC, `brain_config.py` 596 LOC) — only
  `drive_as_code` is covered.

## Open questions

- Where is `drive_hash` actually computed? CLAUDE.md states it lives at
  checkpoint time but `drive_as_code.py` provides no equivalent of
  `compute_brain_hash`. Worth tracing through `environment/dac_engine.py`
  or the checkpoint code (out of scope for this subsystem).
- `RecordingConfig` uses `extra="allow"` — is this for a recorder plugin
  system that's not yet implemented, or is it accumulating unstructured
  knobs? The optional fields (`output_dir`, `max_queue_size`, `compression`,
  `criteria`) suggest the latter.
- `cues.py` describes its file as "theory-of-mind signals" and carries
  ten Any-typed narrative-metadata fields. Are these meant to migrate into
  proper schemas, or are they intentionally schemaless documentation
  embedded in YAML?
- The `BrainConfig.architecture` literal includes `"set_encoder"` (via
  `SetEncoderConfig`) but I didn't trace whether any current curriculum
  pack uses it. If not, candidate for deletion.
