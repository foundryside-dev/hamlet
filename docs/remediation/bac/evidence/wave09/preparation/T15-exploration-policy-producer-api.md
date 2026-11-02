# T15 genuine exploration-policy producer API

Bounded static handoff, 2026-11-01, observed HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`. No project imports/runtime/tests or tracked edits. The prior four-file context is extended by the explicitly authorized fifth source, `config/exploration_policy.py` (768 lines): **five whole files / 3162 charged lines**, no sixth source/helper/test.

## Exact public producers

`from townlet.config.effective_run import resolve_effective_run` — EF154–161:

```text
resolve_effective_run(base: BrainConfig, training: TrainingV2Config, *,
    primary_level: str, origins: Mapping[str, str],
    drive_intrinsic: IntrinsicStrategyConfig) -> EffectiveRunConfig
```

`from townlet.config.exploration_policy import resolve_exploration_policy` — RP455–457:

```text
resolve_exploration_policy(drive_intrinsic: IntrinsicStrategyConfig,
    training: TrainingV2Config, options: BaCOptions) -> ResolvedExplorationPolicy
```

All three RP arguments are required; there is no keyword-only separator. EF174–177 supplies `BaCOptions()` when `training.bac_options is None`, otherwise the actual authored `training.bac_options`, then calls `resolve_exploration_policy(drive_intrinsic, training, authored)`. Use authored options for this producer, not an invented resolved payload.

**Drive selects strategy**: RP463–464 reads `drive_intrinsic.strategy`; RP24–25 permits exactly `none`, `rnd`, `adaptive_rnd`, `count_based`, `icm`. `BaCOptions.providers.count_based/icm` supplies typed parameter overrides, not the selector (OP90–99,138–149; RP628–679). Precedence is typed selected overrides > raw selected drive block > versioned derivation. RP757–768 constructs the genuine immutable `ResolvedExplorationPolicy`, including roles, authoring, units and service/scope metadata. Do not fabricate its many `from_dict` fields.

## Existing runner access and complete fixture call

RR111–115 already obtains `runner.effective_run = runner.resolved_launch.effective`. **For a pack authored with the desired drive intrinsic strategy, the complete policy accessor is `runner.effective_run.exploration`.** The runner does not call either producer itself.

There is **no compiled-level drive accessor used by RR**. Its `compiled.get_level(...)` calls are RR160 and RR398; no `.drive` or `drive_intrinsic` access occurs anywhere in RR's 1001 lines. Claiming `level.drive.intrinsic` or another guessed compiled path from this inventory would invent an interface. No sixth compiled DTO/source was opened.

There is an actual source-verified typed drive reconstruction route: EF148 calls `IntrinsicStrategyConfig.model_validate(policy.authored_parameters['drive_intrinsic'])`; import path is `townlet.config.drive_as_code` (EF14; RP21). RP475–477 captures the real drive's `model_dump()` in that field. This permits a fixture to resolve a genuine policy without guessing a compiled accessor:

```python
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.effective_run import resolve_effective_run

original = runner.effective_run
# Fixture-local explicit authoring choice; use "icm" for the ICM case.
drive_payload = dict(original.exploration.authored_parameters["drive_intrinsic"])
drive_payload["strategy"] = "count_based"
drive_intrinsic = IntrinsicStrategyConfig.model_validate(drive_payload)
view = resolve_effective_run(
    original.base_brain,
    original.training,
    primary_level=original.primary_level,
    origins=original.origins,
    drive_intrinsic=drive_intrinsic,
)
policy = view.exploration
```

Every required argument above comes from the actual existing view or the validated explicit fixture choice; none is a placeholder. This creates typed fixture-local authoring and a genuine resolver result; it does not rewrite the compiled universe or prove the original pack compiled with that changed strategy. For authored production-path evidence, select the strategy in the actual drive declaration before compilation and take the runner accessor directly.

To call RP directly instead of building a view, import `resolve_exploration_policy` above and `BaCOptions` from `townlet.config.bac_options`, set `training = original.training`, set `options = training.bac_options` if present otherwise `BaCOptions()`, then call **`resolve_exploration_policy(drive_intrinsic, training, options)`**. EF is preferable when the fixture also needs canonical replay options/effective brain. Existing training carries its real authored provider overrides in either route. No Count/ICM constructor signature was re-inspected here.

## Source identity and custody

Paths are relative to `/workspace/hamlet/src/townlet/`; all five files are charged whole even where read selectively.

| Alias/path | Lines | SHA256 |
|---|---:|---|
| RR `demo/runner.py` | 1001 | `94842641bdce645fdd90d188d5bbdf6e09e7f4c071d15756202e173acd47c15d` |
| EF `config/effective_run.py` | 365 | `9ff2c4e8cc538160abe7188c7a2192b3ee740464d1b0681790e569685d49882c` |
| OP `config/bac_options.py` | 294 | `10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916` |
| WS `exploration/world_curiosity_state.py` | 734 | `8b242ef58af2840c069db3d599606ba4760eea675e6be5bf00d8eb89c23b5b82` |
| RP `config/exploration_policy.py` | 768 | `af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c` |

The only write is this ignored report (`.git/info/exclude:7`, `/.superpowers/`). The active author's untracked learner test was observed only through `git status`, not opened or changed. No source/tests/index/branch/worktree/sourcecopies/subagent/runtime operation was performed. Final source hashes/counts and ignore status are checked before returning stationary; root retains integration and qualification custody.
