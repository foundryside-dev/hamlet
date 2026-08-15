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

## Baselines (CPU, L0_0_minimal: 3×3 grid, 1 affordance)

Numbers are mean call time captured by `pytest-benchmark` on
`project-recovery` HEAD. The ratio to the `n=1` row shows scale behaviour;
flat ratios indicate a vectorised path, steeply growing ratios indicate a
per-agent Python loop hiding in the implementation.

**Caveat: this baseline varies `num_agents` only.** Grid size and affordance
count are pinned to the L0_0_minimal config (3×3, 1 affordance). To cover
the grid-size axis the done_definition names, see the multi-config sweep
in `TestEnvironmentStepBenchmarks::test_env_step_scales_with_grid` below.

### env.step (whole-tick)

| num_agents | mean    | vs n=1 | notes |
|------------|---------|--------|-------|
| 1          | 1.37 ms | 1.00x  | baseline |
| 4          | 1.38 ms | 1.02x  | nearly flat — most env.step work is constant-time orchestration |
| 16         | 1.40 ms | 1.04x  | |
| 64         | 1.48 ms | 1.10x  | sub-linear growth; per-agent overhead is small at n≤64 |

### ActionMaskBuilder.build

| num_agents | mean    | vs n=1 |
|------------|---------|--------|
| 1          | 151 µs  | 1.00x  |
| 4          | 189 µs  | 1.25x  |
| 16         | 242 µs  | 1.60x  |
| 64         | 460 µs  | **3.05x** |

**Material super-linear growth.** The per-affordance `is_on_position` loop
and the per-slot inventory loops in `build()` are the most visible per-agent
Python work in the env hot path. Even with only 1 affordance on this config,
the n=64 row is 3× the n=1 row — a sweep against an affordance-heavy config
will compound this further.

### VTC passive depletion (`env._apply_vtc_passive_depletion`)

| num_agents | mean    | vs n=1 |
|------------|---------|--------|
| 1          | 143 µs  | 1.00x  |
| 4          | 152 µs  | 1.06x  |
| 16         | 155 µs  | 1.08x  |
| 64         | 155 µs  | 1.08x  |

Flat — already vectorised over the batch dimension.

### VTC threshold cascades (`env._apply_vtc_threshold_cascades`)

| num_agents | mean    | vs n=1 |
|------------|---------|--------|
| 1          | 168 µs  | 1.00x  |
| 4          | 177 µs  | 1.05x  |
| 16         | 182 µs  | 1.08x  |
| 64         | 183 µs  | 1.09x  |

Flat across scale; cascades dominate constant overhead but the cost does not
grow meaningfully with population size.

### VTCInteractionProgressProgram.apply (isolated)

Measured against `L0_5_dual_resource` with an empty interaction batch
(measures pure dispatch overhead per agent, no work per agent):

| num_agents | mean    | vs n=1 |
|------------|---------|--------|
| 1          | 10 µs   | 1.00x  |
| 4          | 18 µs   | 1.78x  |
| 16         | 48 µs   | **4.64x** |
| 64         | 171 µs  | **16.61x** |

**Worst-measured per-agent growth in the runtime.** The 16x growth at n=64
is observed with *no actual interactions in flight* — the entire cost is
the per-agent Python loop at `vtc.py:1257`. Any interactive workload makes
this worse. Top vectorisation candidate.

### Reward calculation (`_reward_calculator._calculate_shaped_rewards`)

| num_agents | mean    | vs n=1 |
|------------|---------|--------|
| 1          | 80 µs   | 1.00x  |
| 4          | 82 µs   | 1.02x  |
| 16         | 87 µs   | 1.08x  |
| 64         | 89 µs   | 1.11x  |

Effectively constant per call regardless of population. The DACEngine
compiled functions are already vectorised; **not a hot-path candidate** at
current scale.

## Ranked vectorisation candidates

| Rank | Candidate | Evidence | Status |
|------|-----------|----------|--------|
| 1 | **`VTCInteractionProgressProgram.apply`** (`vfs/vtc.py:1218`) | **16.6x at n=64** with empty interaction batch — measured | Replace the per-agent loop at vtc.py:1257 with a vectorised path. Highest-leverage change in the runtime. |
| 2 | **`ActionMaskBuilder.build` per-affordance / per-slot loops** (`environment/action_mask_builder.py`) | 3.05x at n=64 with only 1 affordance — measured | Likely amplifies on affordance-heavy configs; benchmark on `L1_full_observability` (14 affordances) before optimising to size the win. |
| 3 | `affordance_engine.py` per-agent resolution | Indirect signal via rank-2 growth — not measured in isolation | Add benchmark before optimising. |
| 4 | `action_executor.py` per-agent dispatch | `env.step` whole-tick cost is sub-linear (1.10x at n=64); not visibly bottlenecked | Re-evaluate if env.step starts growing super-linearly. |
| 5 | DACEngine reward paths | 1.11x at n=64 — already flat | No action. |

## Open coverage gaps

The current benchmarks cover the `num_agents` axis well. The done_definition
also names `grid_size` and `affordance_count` as required baseline
dimensions. Coverage gaps that future work should close:

- **Grid-size / affordance-count sweep:** the L0_0_minimal 3×3 baseline (1
  affordance) masks costs that grow with affordance count. A parameterised
  sweep against `default_curriculum/L1_full_observability` (8×8, 14
  affordances) would expose the per-affordance loop inside ActionMaskBuilder
  more accurately. Tracked but deferred to keep this baseline
  reproducible-quickly.
- **`affordance_engine.py` isolated benchmark:** currently inferred from
  ActionMaskBuilder growth, not measured directly.
- **`action_executor._execute_actions` isolated benchmark:** rank-4 today,
  unmeasured.

These gaps are tracked alongside the milestone follow-ups.

## Rules of the road

- **No optimisation merged without benchmark evidence.** Adding
  `--benchmark-compare` output to a PR description is the minimum standard.
  Enforcement is currently honour-system; a CI gate is a future hardening
  item.
- **Every new benchmark must call `_record_scale_axes`** so the comparison
  captures dimensions, not just timing.
- **Add a benchmark for a hot path before vectorising it**, even if only a
  single-agent baseline. The vectorisation is the diff; without the baseline
  there is nothing to diff against.
