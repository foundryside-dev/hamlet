# Current curriculum policy developer contract

This contract describes the bounded T21 producer at candidate tree b7a8c6778ef1dc61e0865c8136ad073eafcfb255 and the accepted CurriculumDecision producer-domain repair. It does not declare integrated BAC release. Root reports239 joint passes (64 factory/175 T20), four local guards passing at default count601, independent T21 selection48 passes/16 deselected and independent DTO selection23 passes/41 deselected, each with custody checks. These are received execution results; no runtime was executed to write this document.

## Resolve portable options and the actual static roster separately

`townlet.config.bac_options.resolve_bac_options(options, *, training)` remains the pure options resolver. It requires no world roster and returns `ResolvedBaCOptions` with `schema_version='bac-options-v2'`, fully resolved `options`, and per-field `provenance`. Authored `None` is an absence marker resolved at this owner. Curriculum omissions become `commit_mode='completion'` and `difficulty_mode='stage_band'`. Explicit `legacy_step` and unknown selectors refuse; no compatibility selector remains.

`resolve_static_baseline_policy(*, declared_meter_names: tuple[str, ...])` is the sole owner of the immutable named fixed policy. It returns `StaticBaselinePolicy` with these exact fields:

```python
{
    "policy_id": "static-baseline-v1",
    "difficulty_level": 0.5,
    "reward_mode": "shaped",
    "depletion_multiplier": 1.0,
    "active_meters": ("custom_reserve", "thermal_budget"),
}
```

The example names are illustrative caller-supplied declarations, not built-in meter names. Production callers supply the actual declared meter names in declaration order. Names must be strings, nonblank and unique; `()` is a valid explicitly supplied empty roster. Lists are not accepted by this strict Python resolution API. No inferred domain-name list or manufactured empty roster substitutes for missing caller transport.

The baseline is resolved-only; it adds no authored static knobs to `BaCOptions` or `TrainingV2Config`. The model forbids extra fields, nonfinite numbers and changed named-baseline constants. Existing programmatic `StaticCurriculum` accepts supported custom fixed parameters independently of this baseline.

## Construct the current manager explicitly

Given an existing validated `training: TrainingV2Config`, actual `declared_meter_names: tuple[str, ...]`, and explicit device, the direct route is:

```python
from townlet.config.bac_options import resolve_bac_options, resolve_static_baseline_policy
from townlet.curriculum.factory import build_curriculum

resolved = resolve_bac_options(training.bac_options, training=training)
static_policy = resolve_static_baseline_policy(declared_meter_names=declared_meter_names)
assert resolved.options.curriculum is not None
curriculum = build_curriculum(
    training,
    curriculum_options=resolved.options.curriculum,
    static_policy=static_policy,
    device=device,
)
curriculum.initialize_population(training.population.size)
```

Actual factory signature:

```python
build_curriculum(
    training: TrainingV2Config,
    *,
    curriculum_options: CurriculumOptions,
    static_policy: StaticBaselinePolicy,
    device: torch.device,
) -> CurriculumManager
```

Both mode fields must already be resolved, including when static is selected. The factory never resolves omissions. It has no `max_steps_per_episode` argument or `configure_from_training` path. It returns an uninitialized manager; the caller initializes its actual population once.

Static construction passes completion mode, fixed difficulty/reward/depletion and a copied meter list. Adversarial construction passes completion/difficulty modes, adaptation rate, min/max difficulty, survival advance/retreat thresholds, entropy gate, minimum stage dwell and device directly from the resolved modes and selected training block.

Difficulty modes remain `stage_band` and `rate_limited`. Completed survival means `survival_time/planned_horizon`; stage dwell counts eligible transitions. `rate_limited` bounds difficulty movement per eligible transition, while stage-band keeps adaptation rate inactive. Authored training rates remain strictly positive; the separately accepted T20 programmatic zero-rate capability is unchanged. Singleton difficulty bounds remain supported.

## Effective configuration and current serialization

The effective resolver requires the actual roster explicitly:

```python
resolve_effective_run(
    base: BrainConfig,
    training: TrainingV2Config,
    *,
    primary_level: str,
    origins: Mapping[str, str],
    drive_intrinsic: IntrinsicStrategyConfig,
    declared_meter_names: tuple[str, ...],
) -> EffectiveRunConfig
```

It calls the canonical baseline resolver and carries `effective.static_policy` alongside `effective.options` and `effective.training`. The factory handoff from an already resolved effective object is:

```python
assert effective.options.curriculum is not None
curriculum = build_curriculum(
    effective.training,
    curriculum_options=effective.options.curriculum,
    static_policy=effective.static_policy,
    device=device,
)
curriculum.initialize_population(effective.training.population.size)
```

`EffectiveRunConfig.to_dict()` includes required `static_policy`. `from_dict()` explicitly decodes a portable JSON meter list to the typed tuple, validates the fixed declaration, reconstructs the current effective policy and compares the complete canonical payload. Missing declaration, altered roles/identity and obsolete missing-scope payloads refuse. EF no longer contains the old shared-scope payload acceptance branch. Current curriculum native state remains T20 version2; these option/effective version changes do not renumber that state.

Self-consistency validation does not authenticate a serialized roster against a separately loaded world. Parent restore consumers must compare expected actual effective/world identity before installation.

## Field activity and hash meaning

Completion mode is an active explicit or derived omitted contract marker for both strategies. Difficulty mode and adversarial presets are inactive under static. Under adversarial stage-band, adaptation rate is inactive; under rate-limited it participates in selected execution identity. Inactive presets remain in authored training and its hash.

When static is selected, policy ID, difficulty and depletion are derived from the named baseline. `reward_mode` and `active_meters` remain **unqualified application metadata**. Their presence in a decision does not establish reward switching or meter gating in environment mechanics. Depletion is a finite nonnegative scalar policy output; its transport is established here, while all-lane physics application belongs to the later dynamics/pipeline owners.

The execution identity hashes this canonical content:

```python
{
    "schema": "effective-run-v2",
    "fields": active,
    "exploration": exploration.policy_identity,
    "static_policy": static_policy.model_dump(),  # only when static is selected
}
```

The complete selected static declaration is deliberately bound as policy context, including metadata whose mechanics remain unqualified. Actual meter names and order therefore change the selected static execution hash. Under adversarial, the static declaration remains serialized as an inactive preset and is excluded from that selected identity projection. This does not establish broader adversarial world binding.

Authored training hash remains SHA256 of the full training model JSON. Existing authored identity retains its brain/exploration-authored expression. `primary_level` is serialized but is not an independent field of the execution hash expression above; no claim that it alone authenticates a compiled world is made.

## Accepted zero/arbitrary-roster DTO producer domain

The independently accepted CurriculumDecision repair matches actual static producer output: empty and seven-name meter lists are accepted without a six-name enumeration or length cap. Semantic roster validation/membership remains with the owner possessing the declared roster; the DTO cannot authenticate world membership by itself. Static copies meter lists at construction and into each decision.

Depletion outputs accept finite nonnegative scalar numbers, including tested `0.0`, `0.37` and `12.0`. Negative, nonfinite, boolean and list-shaped constructor inputs refuse. The DTO retains strict finite numeric validation; the reported malformed-input tests exercised constructor refusal, not direct malformed DTO validation. Difficulty remains in `[0,1]`; supported reward labels remain `shaped|sparse`.

A supported custom static constructor example is:

```python
StaticCurriculum(
    commit_mode="completion",
    difficulty_level=0.8,
    reward_mode="sparse",
    active_meters=["operator_defined"],
    depletion_multiplier=0.0,
)
```

This is a programmatic current policy, not an override of `static-baseline-v1`. Arbitrary new reward labels are not a supported feature.

## Open compiled integration

The supplied compiler API is `UniverseCompiler().compile(Path(pack), primary_level='L0_test', use_cache=False)`, with `compiled.effective_run` as the transport. Required roster maintenance at the compiler producer remains the forthcoming separate serial slice. It is not yet a working compiled-route witness; root reports the remaining global type error at `compiled.py:389`. No compiled example here claims execution success.

Actual compiler/caller maintenance, a real compiled factory witness, current outer validators, all-lane dynamics, world identity and remaining integration/full-suite/native/learning/restart/E2E/final BAC acceptance gates remain open. This document was written only as ignored developer-contract prose during the source/index freeze; no code, tests, tracked documentation, runtime or Git actions were performed.
