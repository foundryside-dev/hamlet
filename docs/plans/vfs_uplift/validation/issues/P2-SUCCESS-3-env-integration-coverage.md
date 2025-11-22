# P2-SUCCESS-3: Environment Integration Test Coverage at 4%

**Priority:** P2 (Minor - Test Coverage Gap)
**Category:** Success Criteria (Testing)
**Estimated Effort:** 6-8 hours
**Status:** Open
**Created:** 2025-11-22

---

## Problem Description

The vectorized environment module (`src/townlet/environment/vectorized_env.py`) has only 4% test coverage, below the 60% target for integration modules.

**Current Coverage:**
```
src/townlet/environment/vectorized_env.py    4%    (very low)
```

**Gap Analysis:**
- Integration tests exist (372 tests, 2480% of target!)
- Unit coverage for `vectorized_env.py` specifically is low
- Most code paths exercised by integration tests but not measured by unit coverage

**Impact:**
- Hard to identify which environment methods lack testing
- Regression risk if integration tests don't cover edge cases
- **Low priority:** Integration tests validate end-to-end behavior

**Evidence:**
- Agent 9 (Success Criteria) report, section SUCCESS-3
- Coverage report from `uv run pytest --cov`

---

## How to Fix

### Step 1: Run Coverage for vectorized_env.py (30 minutes)

Generate detailed coverage report:

```bash
# Run all tests with coverage for vectorized_env.py
UV_CACHE_DIR=.uv-cache uv run pytest \
  --cov=townlet.environment.vectorized_env \
  --cov-report=term-missing \
  --cov-report=html \
  tests/

# Open htmlcov/index.html to see line-by-line coverage
```

**Identify uncovered methods:**
- Which step() paths not tested?
- Which reset() edge cases not covered?
- Which observation building methods untested?
- Which reward calculation paths uncovered?

### Step 2: Add Unit Tests for Uncovered Paths (3 hours)

**File:** `tests/test_townlet/unit/environment/test_vectorized_env_coverage.py` (NEW)

Focus on methods not covered by integration tests:

```python
"""Unit tests to increase vectorized_env.py coverage."""

import pytest
import torch
from townlet.environment.vectorized_env import VectorizedHamletEnv


class TestEnvironmentInitialization:
    """Test environment construction edge cases."""

    def test_init_with_minimal_config(self):
        """Verify env initializes with minimal valid config."""
        config = create_minimal_config()
        env = VectorizedHamletEnv(config, n_envs=4)

        assert env.n_envs == 4
        assert env.observation_space is not None
        assert env.action_space is not None

    def test_init_with_vfs_enabled(self):
        """Verify VFS registry initialized when vfs_profiles present."""
        config = create_config_with_vfs()
        env = VectorizedHamletEnv(config, n_envs=2)

        assert env.vfs_registry is not None
        assert env.vfs_registry.global_vfs.shape[0] == 2  # n_envs

    def test_init_with_effects_enabled(self):
        """Verify effect manager initialized when effects catalog present."""
        config = create_config_with_effects()
        env = VectorizedHamletEnv(config, n_envs=2)

        assert env.effect_manager is not None

    def test_init_with_items_enabled(self):
        """Verify item manager initialized when items catalog present."""
        config = create_config_with_items()
        env = VectorizedHamletEnv(config, n_envs=2)

        assert env.item_manager is not None
        assert env.item_manager.max_items > 0


class TestStepMethod:
    """Test environment step() method edge cases."""

    def test_step_with_invalid_action_masked(self):
        """Verify invalid actions (masked) result in no-op."""
        env = create_env()
        obs, _ = env.reset()

        # Action 7 is masked (invalid)
        action = torch.tensor([7, 7, 7, 7])  # All invalid

        obs_before = obs.clone()
        obs_after, reward, done, truncated, info = env.step(action)

        # Agent position should not change (no-op for invalid action)
        # This tests action masking enforcement

    def test_step_with_vfs_evaluation(self):
        """Verify VFS variables evaluated during step."""
        config = create_config_with_vfs()
        env = VectorizedHamletEnv(config, n_envs=2)
        obs, _ = env.reset()

        # Modify global VFS
        env.vfs_registry.global_vfs[0, time_idx] = 0.5

        # Step should evaluate VFS expressions
        action = torch.tensor([0, 0])  # Valid action
        obs, reward, done, truncated, info = env.step(action)

        # Check VFS appears in observation
        # (exact index depends on observation config)

    def test_step_with_effect_execution(self):
        """Verify effects executed during step."""
        config = create_config_with_effects()
        env = VectorizedHamletEnv(config, n_envs=1)
        obs, _ = env.reset()

        # Spawn effect
        env.effect_manager.spawn_effect("test_effect", agent_id=0, env_id=0)

        # Step should execute effect
        action = torch.tensor([0])
        obs, reward, done, truncated, info = env.step(action)

        # Verify effect was executed (check bar modification)

    def test_step_with_item_interactions(self):
        """Verify item actions (GET/USE/DROP) work during step."""
        config = create_config_with_items()
        env = VectorizedHamletEnv(config, n_envs=1)
        obs, _ = env.reset()

        # Spawn item at agent location
        env.item_manager.spawn_item("test_item", position=(0, 0), env_id=0)

        # Execute GET action
        get_action_id = env.action_to_id["GET"]
        action = torch.tensor([get_action_id])
        obs, reward, done, truncated, info = env.step(action)

        # Verify item in inventory
        assert env.item_manager.get_agent_inventory(agent_id=0, env_id=0)


class TestResetMethod:
    """Test environment reset() method edge cases."""

    def test_reset_clears_vfs_state(self):
        """Verify VFS registry reset to defaults."""
        config = create_config_with_vfs()
        env = VectorizedHamletEnv(config, n_envs=2)

        # Modify VFS
        env.vfs_registry.agent_vfs[0, 0, gold_idx] = 999.0

        # Reset should restore defaults
        obs, info = env.reset()

        gold_value = env.vfs_registry.agent_vfs[0, 0, gold_idx]
        assert gold_value == 0.0  # Default value

    def test_reset_clears_effects(self):
        """Verify active effects cleared on reset."""
        config = create_config_with_effects()
        env = VectorizedHamletEnv(config, n_envs=1)
        obs, _ = env.reset()

        # Spawn effect
        env.effect_manager.spawn_effect("test_effect", agent_id=0, env_id=0)
        assert len(env.effect_manager.active_effects) > 0

        # Reset should clear effects
        obs, info = env.reset()
        assert len(env.effect_manager.active_effects) == 0

    def test_reset_clears_items(self):
        """Verify items despawned on reset."""
        config = create_config_with_items()
        env = VectorizedHamletEnv(config, n_envs=1)
        obs, _ = env.reset()

        # Spawn item
        env.item_manager.spawn_item("test_item", position=(0, 0), env_id=0)
        assert env.item_manager.get_item_count() > 0

        # Reset should despawn items
        obs, info = env.reset()
        # Note: Items may respawn based on spawn rules, check initial spawn count


class TestObservationBuilding:
    """Test observation construction."""

    def test_build_observation_without_vfs(self):
        """Verify observation built correctly without VFS."""
        config = create_minimal_config()
        env = VectorizedHamletEnv(config, n_envs=2)
        obs, _ = env.reset()

        # Check observation shape
        assert obs.shape == (2, env.obs_dim)

    def test_build_observation_with_vfs(self):
        """Verify VFS variables included in observation."""
        config = create_config_with_vfs()
        env = VectorizedHamletEnv(config, n_envs=2)
        obs, _ = env.reset()

        # Observation should include VFS dims
        expected_dims = (
            env.substrate.position_dim +
            env.n_bars +
            env.vfs_obs_dim +  # VFS contribution
            env.affordance_obs_dim +
            env.temporal_obs_dim
        )
        assert obs.shape[1] == expected_dims

    def test_build_observation_with_items(self):
        """Verify item VFS included in observation."""
        config = create_config_with_items()
        env = VectorizedHamletEnv(config, n_envs=1)
        obs, _ = env.reset()

        # Spawn item
        env.item_manager.spawn_item("test_item", position=(0, 0), env_id=0)

        # Build observation
        obs, _, _, _, _ = env.step(torch.tensor([0]))  # WAIT action

        # Item VFS should be non-zero in observation
        # (exact index depends on observation config)


class TestRewardCalculation:
    """Test reward computation paths."""

    def test_reward_with_dac_engine(self):
        """Verify DAC engine computes rewards."""
        config = create_config_with_dac()
        env = VectorizedHamletEnv(config, n_envs=2)
        obs, _ = env.reset()

        action = torch.tensor([0, 0])  # WAIT
        obs, reward, done, truncated, info = env.step(action)

        # Reward should be computed (non-zero for non-trivial config)
        assert reward.shape == (2,)

    def test_reward_with_intrinsic(self):
        """Verify intrinsic reward (RND) added to total."""
        config = create_config_with_intrinsic()
        env = VectorizedHamletEnv(config, n_envs=1)
        obs, _ = env.reset()

        action = torch.tensor([0])
        obs, reward, done, truncated, info = env.step(action)

        # info should contain intrinsic reward breakdown
        assert 'intrinsic_reward' in info

    def test_reward_logging(self):
        """Verify reward components logged in info dict."""
        config = create_config_with_logging()
        env = VectorizedHamletEnv(config, n_envs=1)
        obs, _ = env.reset()

        action = torch.tensor([0])
        obs, reward, done, truncated, info = env.step(action)

        # Check info contains reward breakdown
        assert 'extrinsic_reward' in info
        assert 'total_reward' in info


class TestDoneAndTruncation:
    """Test episode termination conditions."""

    def test_done_on_death(self):
        """Verify episode terminates when agent dies."""
        config = create_config_with_death_condition()
        env = VectorizedHamletEnv(config, n_envs=1)
        obs, _ = env.reset()

        # Set health to 0 (death)
        env.bars[0, 0, health_idx] = 0.0

        action = torch.tensor([0])
        obs, reward, done, truncated, info = env.step(action)

        # Should be done
        assert done[0] == True

    def test_truncated_on_max_steps(self):
        """Verify episode truncates at max_steps."""
        config = create_config_with_max_steps(10)
        env = VectorizedHamletEnv(config, n_envs=1)
        obs, _ = env.reset()

        # Step 10 times
        for _ in range(10):
            action = torch.tensor([0])
            obs, reward, done, truncated, info = env.step(action)

        # Should be truncated
        assert truncated[0] == True
```

### Step 3: Add Tests for Error Handling (2 hours)

Test exception paths and error handling:

```python
class TestErrorHandling:
    """Test error handling in vectorized_env."""

    def test_invalid_action_out_of_bounds(self):
        """Verify out-of-bounds actions handled gracefully."""
        env = create_env()
        obs, _ = env.reset()

        # Action index exceeds action_space
        invalid_action = torch.tensor([999])

        # Should either: (1) raise error, or (2) clamp to valid range
        # Verify behavior matches design

    def test_missing_vfs_profiles_raises_error(self):
        """Verify environment fails if VFS config missing but required."""
        config = create_config_missing_vfs()

        with pytest.raises(ConfigurationError, match="vfs_profiles"):
            env = VectorizedHamletEnv(config, n_envs=1)

    def test_mismatched_batch_size_raises_error(self):
        """Verify action batch size must match n_envs."""
        env = VectorizedHamletEnv(create_config(), n_envs=4)
        obs, _ = env.reset()

        # Wrong batch size
        action = torch.tensor([0, 0])  # Only 2 actions for 4 envs

        with pytest.raises(ValueError, match="batch size"):
            env.step(action)
```

### Step 4: Verify Coverage Improvement (30 minutes)

Re-run coverage:

```bash
UV_CACHE_DIR=.uv-cache uv run pytest \
  --cov=townlet.environment.vectorized_env \
  --cov-report=term-missing \
  tests/

# Target: 60%+ coverage (up from 4%)
```

---

## Acceptance Criteria

- [ ] Environment integration coverage increases from 4% to ≥60%
- [ ] All major step() paths tested
- [ ] All reset() edge cases tested
- [ ] Observation building tested (with/without VFS, effects, items)
- [ ] Reward calculation tested (extrinsic, intrinsic, DAC)
- [ ] Termination conditions tested (done, truncated)
- [ ] Error handling tested (invalid actions, missing config)
- [ ] VFS/effects/items integration tested at env level

---

## Files to Create

1. `tests/test_townlet/unit/environment/test_vectorized_env_coverage.py` (NEW) - Unit tests

---

## Related Issues

- Related: P2-SUCCESS-2 (VFS evaluator coverage)
- Related: P1-RUN-12 (integration test failures)
- Blocks: None (test coverage gap)

---

## Notes

- **Low priority:** 372 integration tests validate end-to-end behavior
- **Coverage paradox:** Integration tests exercise code but don't count toward unit coverage
- **Strategy:** Write focused unit tests for uncovered branches in vectorized_env.py
- **Alternative:** Could refactor integration tests to run with `--cov=townlet.environment.vectorized_env`
- Consider if 60% is appropriate target given strong integration coverage
- Focus on edge cases NOT covered by integration tests (error paths, boundary conditions)
