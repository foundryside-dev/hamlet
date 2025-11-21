# [TEST-22] VFS Smoke Test Config Pack

**Priority:** P2 (Minor)
**Category:** Testing
**Status:** MISSING
**Effort:** 2 hours

## Description

Missing dedicated VFS smoke test config pack at `configs/test/vfs_smoke/`. VFS system is tested extensively via curriculum level configs (L0-L3) and unit tests, but no minimal smoke test config specifically designed for fast VFS validation. Smoke test would enable quick VFS sanity checks without running full curriculum configs.

## Current State

**Existing VFS test coverage:**
- ✅ 298 VFS unit tests (expression evaluation, registry, profiles, observation)
- ✅ VFS tested in curriculum configs (L0-L3 all use VFS profiles)
- ✅ Integration tests use L0_0_minimal for VFS validation

**Missing:**
- ❌ Dedicated `configs/test/vfs_smoke/` config pack
- ❌ Minimal smoke test config (fastest possible VFS validation)
- ❌ Config pack specifically designed for VFS feature testing

**Why smoke test config is useful:**
- Fast validation: Minimal config compiles and runs in seconds
- CI integration: Quick VFS sanity check in pull requests
- Developer workflow: Fast feedback during VFS development
- Feature testing: Isolate VFS testing from curriculum complexity

## Required Implementation

### 1. Create VFS Smoke Test Config Pack (1-2 hours)

**Directory:** `configs/test/vfs_smoke/`

**Files:**
```
configs/test/vfs_smoke/
├── substrate.yaml          # Minimal substrate (3×3 grid)
├── bars.yaml               # Single bar (energy)
├── cascades.yaml           # Empty cascades
├── affordances.yaml        # Single affordance (food)
├── cues.yaml               # Minimal cues
├── training.yaml           # Fast training (10 episodes)
├── enabled_actions.yaml    # Minimal actions
├── vfs_profiles.yaml       # VFS profiles (this is the focus)
├── drive_as_code.yaml      # Minimal reward
└── variables_reference.yaml # VFS variable reference
```

**Focus: vfs_profiles.yaml (comprehensive VFS feature coverage):**
```yaml
version: "1.0"

# Test global profile
global_profile:
  variables:
    # Scalar types
    global_int:
      type: int
      default: 42
      normalization:
        mode: "min_max"
        range: [0, 100]
      access_control:
        readers: [agent, engine]
        writers: [engine]

    global_float:
      type: float
      default: 0.5
      normalization:
        mode: "z_score"
        mean: 0.5
        std_dev: 0.1
      access_control:
        readers: [agent, engine]
        writers: [engine, bac]

    global_bool:
      type: bool
      default: false
      access_control:
        readers: [agent, engine]
        writers: [engine]

    # Expression variable
    derived_value:
      type: float
      expression: "vfs:global_int * 2.0 + vfs:global_float"
      access_control:
        readers: [agent, engine]
        writers: []  # Computed, not writable

# Test agent profile
agent_profiles:
  test_agent:
    variables:
      # Private variable (not in observations)
      agent_private:
        type: int
        default: 0
        access_control:
          readers: [engine]
          writers: [actions]

      # Observable variable
      agent_observable:
        type: float
        default: 1.0
        normalization:
          mode: "min_max"
          range: [0, 10]
        access_control:
          readers: [agent, engine]
          writers: [actions, bac]

      # Vector type
      agent_position:
        type: vector3
        default: [0.0, 0.0, 0.0]
        normalization:
          mode: "min_max"
          range: [[0, 3], [0, 3], [0, 1]]  # 3×3 grid, z=0
        access_control:
          readers: [agent, engine]
          writers: [engine]

      # Expression with bar reference
      normalized_energy:
        type: float
        expression: "bar:energy * 100.0"
        access_control:
          readers: [agent, engine]
          writers: []

# Test item profile
item_profiles:
  test_item:
    variables:
      item_quality:
        type: float
        default: 1.0
        normalization:
          mode: "min_max"
          range: [0, 2]
        access_control:
          readers: [agent, engine]
          writers: [actions]

      item_stack:
        type: int
        default: 1
        normalization:
          mode: "min_max"
          range: [1, 99]
        access_control:
          readers: [agent, engine]
          writers: [actions, engine]
```

**Other config files (minimal):**

**substrate.yaml:**
```yaml
type: grid
dimensions: 2
grid_size: [3, 3]
boundary_mode: clamp
distance_metric: manhattan
encoding:
  mode: relative
```

**bars.yaml:**
```yaml
energy:
  display_name: "Energy"
  initial_value: 1.0
  min_value: 0.0
  max_value: 1.0
  decay_rate: 0.01
  critically_low_threshold: 0.2
  low_threshold: 0.4
  high_threshold: 0.8
```

**training.yaml:**
```yaml
use_double_dqn: false
gamma: 0.99
epsilon_start: 1.0
epsilon_end: 0.1
epsilon_decay_steps: 1000
replay_buffer_size: 1000
batch_size: 32
min_replay_size: 100
learning_rate: 0.001
target_network_update_frequency: 100
gradient_clip_max_norm: 10.0
num_episodes: 10  # Fast smoke test
max_episode_length: 100
log_frequency: 10
checkpoint_frequency: 10
tensorboard_log_dir: "runs/vfs_smoke"
```

### 2. Smoke Test Script (30 minutes)

**File:** `tests/test_townlet/integration/test_vfs_smoke.py` (new)

**Integration test using smoke config:**
```python
import pytest
from townlet.universe.compiler import UniverseCompiler
from townlet.environment.vectorized_env import VectorizedHamletEnv


def test_vfs_smoke_config_compiles():
    """Test VFS smoke config compiles successfully."""
    config_dir = "configs/test/vfs_smoke"
    compiled = UniverseCompiler.compile(config_dir)

    # Validate VFS profiles compiled
    assert compiled.compiled_vfs_profiles is not None
    assert compiled.compiled_vfs_profiles.global_profile is not None
    assert "test_agent" in compiled.compiled_vfs_profiles.agent_profiles
    assert "test_item" in compiled.compiled_vfs_profiles.item_profiles


def test_vfs_smoke_environment_creates():
    """Test environment creates with VFS smoke config."""
    config_dir = "configs/test/vfs_smoke"
    compiled = UniverseCompiler.compile(config_dir)

    env = VectorizedHamletEnv(
        compiled_universe=compiled,
        num_agents=16,  # Small batch for smoke test
        device="cpu"
    )

    # Validate VFS registry initialized
    assert env.vfs_registry is not None
    assert env.vfs_registry.has_scope("global")
    assert env.vfs_registry.has_scope("agent")


def test_vfs_smoke_episode_runs():
    """Test full episode runs with VFS smoke config."""
    config_dir = "configs/test/vfs_smoke"
    compiled = UniverseCompiler.compile(config_dir)

    env = VectorizedHamletEnv(compiled_universe=compiled, num_agents=16, device="cpu")

    obs = env.reset()
    for step in range(100):
        actions = env.action_space.sample()  # Random actions
        obs, rewards, dones, infos = env.step(actions)

        # Validate VFS observations present
        assert obs.shape[1] > 0  # Non-empty observations
        assert not torch.isnan(obs).any()  # No NaN values

    # Smoke test passed


def test_vfs_smoke_all_variable_types():
    """Test all VFS variable types work in smoke config."""
    config_dir = "configs/test/vfs_smoke"
    compiled = UniverseCompiler.compile(config_dir)
    env = VectorizedHamletEnv(compiled_universe=compiled, num_agents=16, device="cpu")

    env.reset()

    # Test reading all variable types
    global_int = env.vfs_registry.get("global", 0, "global_int")
    assert global_int == 42

    global_float = env.vfs_registry.get("global", 0, "global_float")
    assert abs(global_float - 0.5) < 0.01

    global_bool = env.vfs_registry.get("global", 0, "global_bool")
    assert global_bool == False

    agent_observable = env.vfs_registry.get("agent", 0, "agent_observable")
    assert agent_observable == 1.0

    # Test derived variable (expression)
    derived = env.vfs_registry.get("global", 0, "derived_value")
    expected = 42 * 2.0 + 0.5  # global_int * 2 + global_float
    assert abs(derived - expected) < 0.01


def test_vfs_smoke_benchmark():
    """Benchmark VFS smoke config compilation and execution."""
    import time

    config_dir = "configs/test/vfs_smoke"

    # Benchmark compilation
    start = time.time()
    compiled = UniverseCompiler.compile(config_dir)
    compile_time = time.time() - start
    print(f"VFS smoke compilation: {compile_time:.3f}s")
    assert compile_time < 1.0  # Should compile in <1 second

    # Benchmark environment creation
    start = time.time()
    env = VectorizedHamletEnv(compiled_universe=compiled, num_agents=16, device="cpu")
    create_time = time.time() - start
    print(f"VFS smoke env creation: {create_time:.3f}s")
    assert create_time < 2.0  # Should create in <2 seconds

    # Benchmark episode
    start = time.time()
    env.reset()
    for step in range(100):
        actions = env.action_space.sample()
        env.step(actions)
    episode_time = time.time() - start
    print(f"VFS smoke episode (100 steps): {episode_time:.3f}s")
    assert episode_time < 5.0  # Should run 100 steps in <5 seconds
```

### 3. Documentation (30 minutes)

**Update:** `docs/config-schemas/variables.md`

**Add section:**
```markdown
## VFS Smoke Test Config

For quick VFS validation during development, use the smoke test config:

\```bash
# Compile smoke test config
python -m townlet.compiler compile configs/test/vfs_smoke

# Run smoke test
uv run pytest tests/test_townlet/integration/test_vfs_smoke.py

# Run with benchmark
uv run pytest tests/test_townlet/integration/test_vfs_smoke.py -v
\```

The smoke test config covers all VFS features:
- Global, agent, and item profiles
- All scalar types (int, float, bool, string)
- Vector types (vector3)
- Expression variables
- All normalization modes
- All access control patterns

Use smoke test for:
- Quick VFS sanity checks
- CI validation (fast feedback)
- VFS feature development
- Regression detection
```

## Acceptance Criteria

- [ ] `configs/test/vfs_smoke/` directory created
- [ ] All required config files present (substrate, bars, vfs_profiles, etc.)
- [ ] vfs_profiles.yaml covers all VFS features (types, scopes, expressions, normalization, access control)
- [ ] Smoke config compiles successfully
- [ ] Smoke config runs 10 episodes successfully
- [ ] Integration test `test_vfs_smoke.py` validates compilation, environment creation, episode execution
- [ ] Benchmark test shows smoke config compiles in <1s, runs episode in <5s
- [ ] Documentation updated with smoke test usage
- [ ] CI can use smoke test for fast VFS validation

## Evidence

**Source Report:** gap-report-final.md (lines 71-94), gap-report-testing-docs.md
**Existing test coverage:** 298 VFS unit tests, VFS tested in L0-L3 configs

## Implementation Notes

**Why P2 (not P1/P0):** VFS system is already extensively tested (298 unit tests + integration tests via L0-L3 configs). Smoke test config is convenience feature for faster development feedback, not critical for merge.

**Smoke Test Purpose:**
1. **Fast validation:** Compile + run in <10 seconds (vs L0_0_minimal ~30 seconds)
2. **Feature coverage:** Test all VFS features in one minimal config
3. **CI integration:** Quick VFS sanity check in pull requests
4. **Developer workflow:** Instant feedback during VFS development

**Design Principles:**
- **Minimal:** 3×3 grid, 1 bar, 10 episodes (fast)
- **Comprehensive:** Covers all VFS features (types, scopes, expressions, normalization)
- **Focused:** Isolates VFS testing from curriculum complexity
- **Benchmarked:** Performance targets for compilation and execution

**VFS Feature Coverage:**
- ✅ Global profile (shared state)
- ✅ Agent profile (per-agent state)
- ✅ Item profile (per-item state)
- ✅ All scalar types (int, float, bool, string)
- ✅ Vector type (vector3)
- ✅ Expression variables (computed from other variables)
- ✅ All normalization modes (min_max, z_score)
- ✅ All access control patterns (readers/writers)
- ✅ Private variables (not in observations)
- ✅ Observable variables (in observations)

**Comparison to L0_0_minimal:**
- L0_0_minimal: Full curriculum config (8 bars, cascades, affordances, training)
- vfs_smoke: Minimal config (1 bar, no cascades, 1 affordance, fast training)
- L0_0_minimal: ~30s compilation + episode
- vfs_smoke: ~10s compilation + episode (3× faster)

**CI Integration:**
```yaml
# .github/workflows/vfs-smoke-test.yml
name: VFS Smoke Test

on: [pull_request]

jobs:
  vfs-smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run VFS smoke test
        run: uv run pytest tests/test_townlet/integration/test_vfs_smoke.py -v
```

## References

- Config location: `configs/test/vfs_smoke/` (to be created)
- Test file: `tests/test_townlet/integration/test_vfs_smoke.py` (to be created)
- Documentation: `docs/config-schemas/variables.md` (add smoke test section)
- Related: L0_0_minimal (similar minimal config but curriculum-focused, not VFS-focused)
