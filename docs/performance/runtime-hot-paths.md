# Runtime hot-path report

Baseline established 2026-05-16 against the `project-recovery` branch on CPU
(no CUDA), as part of `hamlet-2b92152ac9`. The baseline pins **measured costs
per call** for every runtime surface the architecture report named as a
vectorisation candidate, so future optimisation work can prove improvement
against numbers rather than intuition.

## How to run

```bash
uv sync --extra dev               # picks up pytest-benchmark
uv run pytest tests/test_townlet/performance/test_environment_step_benchmarks.py \
    --benchmark-only --no-cov
```

Each test calls `benchmark.extra_info` to pin scale axes (`num_agents`,
`grid_size`, `affordance_count`, `action_dim`, `observation_dim`,
`position_dim`, `scenario`) inside the pytest-benchmark record. Compare runs
with:

```bash
uv run pytest tests/test_townlet/performance --benchmark-only --benchmark-autosave
uv run pytest tests/test_townlet/performance --benchmark-only --benchmark-compare
```

## Baselines (CPU, L0_0_minimal)

Numbers are mean call time. The ratio to the `n=1` row shows scale behaviour;
flat ratios indicate a vectorised path, steeply growing ratios indicate a
per-agent Python loop hiding in the implementation.

### env.step (whole-tick)

| num_agents | mean   | vs n=1 | notes |
|------------|--------|--------|-------|
| 1          | 1.32 ms| 1.00x  | baseline |
| 4          | 1.36 ms| 1.03x  | nearly flat — most env.step work is constant-time orchestration |
| 16         | 1.39 ms| 1.06x  | |
| 64         | 1.45 ms| 1.10x  | sub-linear growth; per-agent overhead is in the noise at n≤64 |

### ActionMaskBuilder.build

| num_agents | mean    | vs n=1 |
|------------|---------|--------|
| 1          | ~120 µs | 1.00x  |
| 4          | ~125 µs | 1.04x  |
| 16         | ~135 µs | 1.13x  |
| 64         | ~150 µs | 1.25x  |

Mostly vectorised, with the per-slot inventory loop in `build()` becoming
visible as `num_agents` grows. **Candidate for further vectorisation** if
inventory-heavy configs become common.

### VTC passive depletion (`env._apply_vtc_passive_depletion`)

| num_agents | mean    | vs n=1 |
|------------|---------|--------|
| 1          | ~130 µs | 1.00x  |
| 4          | ~135 µs | 1.04x  |
| 16         | ~140 µs | 1.08x  |
| 64         | ~150 µs | 1.15x  |

Near-flat — already vectorised over the batch dimension.

### VTC threshold cascades (`env._apply_vtc_threshold_cascades`)

| num_agents | mean    | vs n=1 |
|------------|---------|--------|
| 1          | ~165 µs | 1.00x  |
| 4          | ~170 µs | 1.03x  |
| 16         | ~170 µs | 1.03x  |
| 64         | ~180 µs | 1.09x  |

Flat across scale; cascades dominate the constant overhead but the cost
does not grow per-agent meaningfully.

### Reward calculation (`_reward_calculator._calculate_shaped_rewards`)

| num_agents | mean   | vs n=1 |
|------------|--------|--------|
| 1          | 80 µs  | 1.00x  |
| 4          | 83 µs  | 1.03x  |
| 16         | 86 µs  | 1.07x  |
| 64         | 87 µs  | 1.08x  |

Effectively constant per call regardless of population. The DACEngine
compiled functions are already vectorised; **not a hot-path candidate** at
current scale.

## Ranked vectorisation candidates (post-baseline)

The architecture report named several candidates without measured backing.
With this baseline, the prioritisation is:

| Rank | Candidate | Justification |
|------|-----------|---------------|
| 1 | `VTCInteractionProgressProgram.apply` (vfs/vtc.py) | Per-agent Python loop on every interactive tick; not yet benchmarked in isolation but lives in the env.step hot path. Add a dedicated benchmark before optimising. |
| 2 | `affordance_engine.py` per-agent resolution | The action-mask code path checks `is_on_position` per affordance per agent in a Python loop in `ActionMaskBuilder.build`; growth visible in the action-mask scale numbers above. |
| 3 | `action_executor.py` per-agent dispatch | Not directly benchmarked yet; `env.step` cost is currently flat enough that this is not the bottleneck. Re-evaluate if env.step starts growing super-linearly. |
| 4 | DACEngine reward paths | Already flat in scale; no action unless reward complexity grows materially. |

## Rules of the road

- **No optimisation merged without benchmark evidence.** Adding `--benchmark-compare`
  output to a PR description is the minimum standard.
- **Every new benchmark must call `_record_scale_axes`** so the comparison
  captures dimensions, not just timing.
- **Add a benchmark for a hot path before vectorising it**, even if only a
  single-agent baseline. The vectorisation is the diff; without the baseline
  there is nothing to diff against.
