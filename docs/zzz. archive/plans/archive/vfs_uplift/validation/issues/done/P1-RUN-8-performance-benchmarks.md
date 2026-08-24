# [RUN-8] Performance Benchmarks (<5% Overhead)

**Priority:** P1 (Important)
**Category:** Runtime / Testing
**Status:** PARTIAL
**Effort:** 1 day

## Description

VFS uplift adds new runtime overhead (VFS evaluation, expression evaluation, item VFS tracking, effects execution). Target is <5% overhead in environment step loop compared to baseline. Performance benchmark infrastructure exists (pytest-benchmark) but no formal validation that overhead target is met.

## Current State

**Infrastructure exists:**
- ✅ pytest-benchmark installed and configured
- ✅ Performance test patterns established
- ✅ Efficient implementation patterns used throughout:
  - GPU tensors for vectorized operations
  - Mark-and-sweep evaluation (EAGER mode currently, LAZY once VFS-6 complete)
  - Cached compiled ASTs (no runtime parsing)
  - Zero runtime YAML loading (all configs compiled at startup)

**Missing:**
- ❌ No formal baseline vs VFS-enabled comparison
- ❌ No documented overhead characteristics
- ❌ No CI performance regression detection
- ❌ No profiling data showing hotspots

**Current assumption:** Overhead likely <1% based on efficient patterns, but not formally verified.

## Required Implementation

### 1. Baseline Performance Tests (2-3 hours)

**File:** `tests/test_townlet/performance/test_baseline_performance.py` (new)

**Tests:**
```python
import pytest

@pytest.mark.benchmark(group="environment-step")
def test_baseline_environment_step(benchmark, minimal_config):
    """Benchmark environment step without VFS/items/effects."""
    env = create_baseline_environment(minimal_config)  # No VFS features

    def step():
        env.step(actions)

    result = benchmark(step)
    # Record baseline: ~X ms per step

@pytest.mark.benchmark(group="environment-step")
def test_vfs_enabled_environment_step(benchmark, vfs_config):
    """Benchmark environment step with full VFS uplift features."""
    env = create_vfs_environment(vfs_config)  # VFS + items + effects

    def step():
        env.step(actions)

    result = benchmark(step)
    # Compare to baseline: should be <5% overhead
```

**Configurations:**
- Baseline: L0_0_minimal without VFS/items/effects (pure bars + affordances)
- VFS-enabled: L1_full_observability with VFS + items + effects

### 2. Component-Level Benchmarks (3-4 hours)

**File:** `tests/test_townlet/performance/test_vfs_performance.py` (new)

**Test VFS evaluation overhead:**
```python
@pytest.mark.benchmark(group="vfs-evaluation")
def test_vfs_evaluation_overhead(benchmark, vfs_registry, global_profile):
    """Benchmark VFS expression evaluation."""
    context = build_evaluation_context()

    def evaluate():
        VFSEvaluator.evaluate_global_profile(
            profile=global_profile,
            registry=vfs_registry,
            context=context,
            mode=EvaluationMode.EAGER
        )

    result = benchmark(evaluate)
    # Target: <0.1ms for 50 variables with simple expressions
```

**Test item VFS tracking:**
```python
@pytest.mark.benchmark(group="item-vfs")
def test_item_vfs_observation_overhead(benchmark, item_manager):
    """Benchmark item VFS observation building."""

    def build_obs():
        obs = item_manager.build_item_vfs_observations()

    result = benchmark(build_obs)
    # Target: <0.1ms for 100 items
```

**Test effects execution:**
```python
@pytest.mark.benchmark(group="effects")
def test_effects_execution_overhead(benchmark, effect_manager, execution_context):
    """Benchmark effects execution per tick."""

    def tick():
        effect_manager.tick(execution_context)

    result = benchmark(tick)
    # Target: <0.2ms for 50 active effects
```

### 3. Profiling and Hotspot Analysis (2-3 hours)

**Tool:** cProfile or py-spy

**Generate profiling data:**
```bash
# Profile full training run
python -m cProfile -o profile.stats scripts/run_demo.py --config configs/L1_full_observability

# Analyze hotspots
python -m pstats profile.stats
> sort cumulative
> stats 20
```

**Document hotspots:**
- Which functions take most time in step loop?
- VFS evaluation overhead breakdown (parsing, context building, evaluation)
- Item management overhead (spawn, update, VFS tracking)
- Effects execution overhead (catalog lookup, command execution, reapply policies)

### 4. Performance Documentation (2-3 hours)

**File:** `docs/performance/vfs-uplift-overhead.md` (new)

**Contents:**
- Benchmark results table (baseline vs VFS-enabled)
- Overhead breakdown by component (VFS, items, effects)
- Profiling hotspots and optimization opportunities
- Performance characteristics at different scales:
  - Small: 10 VFS vars, 10 items, 5 effects
  - Medium: 50 VFS vars, 100 items, 50 effects
  - Large: 200 VFS vars, 1000 items, 500 effects
- CI performance regression thresholds

### 5. CI Integration (1-2 hours)

**File:** `.github/workflows/performance-tests.yml` (new)

**Workflow:**
```yaml
name: Performance Tests

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run benchmarks
        run: uv run pytest tests/test_townlet/performance/ --benchmark-only --benchmark-json=output.json
      - name: Check regression
        run: python scripts/check_performance_regression.py output.json
```

**Regression detection:**
- Compare against baseline (stored in repo)
- Flag if overhead exceeds 5% threshold
- Post comment on PR with benchmark results

## Acceptance Criteria

- [ ] Baseline performance tests for environment step loop
- [ ] VFS-enabled performance tests for environment step loop
- [ ] Component-level benchmarks for VFS, items, effects
- [ ] Overhead calculation: (VFS_time - baseline_time) / baseline_time < 0.05
- [ ] Profiling data generated and analyzed
- [ ] Hotspot documentation with optimization opportunities
- [ ] Performance documentation in `docs/performance/`
- [ ] CI workflow for performance regression detection
- [ ] Benchmark results table in documentation
- [ ] Verified <5% overhead target is met (or document exceptions)

## Evidence

**Source Report:** gap-report-final.md (lines 55-68, 452-455), gap-report-runtime.md
**Infrastructure:** pytest-benchmark in `pyproject.toml`
**Efficient Patterns:** Mark-and-sweep (evaluator.py), GPU tensors (vectorized_env.py), compiled catalogs (compiler.py)

## Implementation Notes

**Why P1 (not P0):** Functional correctness validated. This is about verifying performance characteristics, not fixing a bug. Based on efficient patterns used, overhead likely <1%, well under 5% target.

**Performance Target Justification:**
- <5% overhead is acceptable for pedagogical environment
- VFS uplift adds significant functionality (declarative state, expression language, items, effects)
- Trade-off: Slight performance cost for massive flexibility gain

**Expected Results (based on implementation patterns):**
- VFS evaluation (EAGER): ~0.5-1% overhead (50 variables, simple expressions)
- VFS evaluation (LAZY, once VFS-6 complete): ~0.2-0.5% overhead (mark-and-sweep optimization)
- Item VFS tracking: ~0.3-0.5% overhead (100 items, GPU tensors)
- Effects execution: ~0.5-1% overhead (50 active effects, compiled commands)
- **Total estimated: 1.5-3% overhead** (well under 5% target)

**Optimization Opportunities (if overhead exceeds target):**
1. **VFS Evaluation:**
   - Complete VFS-6 (mark-and-sweep LAZY mode) → reduces overhead by 50%
   - Cache expression results for constant expressions
   - Vectorize expression evaluation for batch processing

2. **Item VFS:**
   - Use sparse tensors for item storage (most slots empty)
   - Batch item updates (don't iterate per-item)

3. **Effects:**
   - Skip empty effect slots (early-exit if no active effects)
   - Compile effect commands to GPU kernels (advanced optimization)

**Benchmark Configuration:**
- Batch size: 512 (typical training batch)
- Grid size: 8×8 (L1 config)
- VFS variables: 50 (global + agent profiles)
- Items: 100 (moderate spawn rate)
- Effects: 50 (realistic active effect count)
- Episode length: 1000 ticks (measure sustained overhead)

**Profiling Tools:**
- cProfile: CPU profiling (function-level timing)
- py-spy: Low-overhead sampling profiler (captures live runs)
- torch.profiler: GPU profiling (if GPU overhead suspected)

## References

- Baseline test: `tests/test_townlet/performance/test_baseline_performance.py` (to be created)
- VFS benchmarks: `tests/test_townlet/performance/test_vfs_performance.py` (to be created)
- Documentation: `docs/performance/vfs-uplift-overhead.md` (to be created)
- CI workflow: `.github/workflows/performance-tests.yml` (to be created)
- Related: VFS-6 (mark-and-sweep optimization for LAZY mode)
