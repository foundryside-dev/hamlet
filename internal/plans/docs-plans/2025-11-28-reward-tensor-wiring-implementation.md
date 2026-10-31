# RewardTensor Component Wiring - Implementation Plan

> 📌 **Recovered from archive 2026-08-26 — a COMPLETED plan, retained only as test provenance.**
>
> This is a historical implementation plan, not current intent and not a description of shipped
> behaviour. It is out of the archive for one reason: live test files cite this exact path to
> explain which plan task they implement, and those citations must resolve.
>
> Read it as provenance for those tests. For what the system actually does now, use
> `README.md` and the HLD set in `docs/architecture/`.


**Date**: 2025-11-28
**Design Document**: `docs/zzz. archive/plans/2025-11-28-reward-tensor-wiring-design.md`
**Status**: Ready for implementation
**Estimated Tasks**: 9

---

## Overview

This plan implements the wiring to populate RewardTensor's component fields (extrinsic, intrinsic, shaping) which currently exist but are never populated. The implementation follows the data flow: DAC → env → population → buffer/tensorboard.

---

## Task 1: Add intrinsic_raw to DACEngine component output

**File**: `src/townlet/environment/dac_engine.py`
**Lines**: 1001-1007

**Current code** (line 1001-1007):
```python
# 5. Build components dict for logging
components = {
    "extrinsic": extrinsic,
    "intrinsic": intrinsic,
    "shaping": shaping_total,
}

return total_reward, intrinsic_weight, components
```

**New code**:
```python
# 5. Build components dict for logging
# intrinsic_raw: before modifier application (base_weight applied, not modifiers)
# intrinsic: after modifier application (base_weight × modifiers × raw)
intrinsic_raw_weighted = intrinsic_raw_copy * base_weight  # base_weight already applied at line 972

components = {
    "extrinsic": extrinsic,
    "intrinsic": intrinsic,
    "intrinsic_raw": intrinsic_raw_weighted,  # Before modifiers, after base_weight
    "shaping": shaping_total,
}

return total_reward, intrinsic_weight, components
```

**Why**: We need `intrinsic_raw` (before modifiers) to log to TensorBoard so users can compare raw novelty vs suppressed novelty.

**Verification**:
```bash
uv run pytest tests/test_townlet/unit/environment/test_dac_engine.py -k "components" -v
```

---

## Task 2: Add components to info dict in vectorized_env.step()

**File**: `src/townlet/environment/vectorized_env.py`
**Lines**: 1726-1732

**Current code** (line 1726-1732):
```python
info = {
    "step_counts": self.step_counts.clone(),
    "positions": self.positions.clone(),
    "successful_interactions": successful_interactions,  # {agent_idx: affordance_name}
}

return observations, rewards, self.dones, info
```

**New code**:
```python
info = {
    "step_counts": self.step_counts.clone(),
    "positions": self.positions.clone(),
    "successful_interactions": successful_interactions,  # {agent_idx: affordance_name}
    "reward_components": self._last_reward_components,  # DAC breakdown
    "intrinsic_weight": self.intrinsic_weights,  # Effective modifier weight
}

return observations, rewards, self.dones, info
```

**Context**: `self._last_reward_components` is already set at line 2123:
```python
self._last_reward_components = components
```

And `self.intrinsic_weights` is set at line 2120:
```python
self.intrinsic_weights = intrinsic_weights
```

**Why**: Population needs access to components via info dict (Gym-like API preserved).

**Verification**:
```bash
uv run pytest tests/test_townlet/integration/test_dac_integration.py -v
```

---

## Task 3: Extract components in VectorizedPopulation._training_step()

**File**: `src/townlet/population/vectorized.py`
**Lines**: 639-669

**Current code** (line 648-669):
```python
# 7. Store transition in replay buffer
# CRIT-07: Use RewardTensor to store DAC-composed total rewards
reward_tensor = RewardTensor.from_dac(total=rewards)

if self.is_recurrent:
    # For recurrent networks: accumulate episodes
    for i in range(self.num_agents):
        self.current_episodes[i]["observations"].append(self.current_obs[i].cpu())
        self.current_episodes[i]["actions"].append(actions[i].cpu())
        self.current_episodes[i]["rewards"].append(rewards[i].cpu())  # CRIT-07: DAC-composed total
        self.current_episodes[i]["dones"].append(dones[i].cpu())
else:
    # For feedforward networks: store individual transitions
    self.replay_buffer.push(
        observations=self.current_obs,
        actions=actions,
        rewards=reward_tensor,  # CRIT-07: RewardTensor with DAC-composed total
        next_observations=next_obs,
        dones=dones,
    )
```

**New code**:
```python
# 7. Store transition in replay buffer
# Extract DAC components from info dict for provenance tracking
components = info.get("reward_components", {})
intrinsic_weight = info.get("intrinsic_weight")

reward_tensor = RewardTensor.from_dac(
    total=rewards,
    extrinsic=components.get("extrinsic"),
    intrinsic=components.get("intrinsic"),
    shaping=components.get("shaping"),
)

# Log components to TensorBoard (episode-level aggregation)
if self.tensorboard_logger is not None and components:
    self._log_reward_components(
        components=components,
        intrinsic_weight=intrinsic_weight,
    )

if self.is_recurrent:
    # For recurrent networks: accumulate episodes with components
    for i in range(self.num_agents):
        self.current_episodes[i]["observations"].append(self.current_obs[i].cpu())
        self.current_episodes[i]["actions"].append(actions[i].cpu())
        self.current_episodes[i]["rewards"].append(rewards[i].cpu())
        self.current_episodes[i]["rewards_extrinsic"].append(components["extrinsic"][i].cpu())
        self.current_episodes[i]["rewards_intrinsic"].append(components["intrinsic"][i].cpu())
        self.current_episodes[i]["rewards_shaping"].append(components["shaping"][i].cpu())
        self.current_episodes[i]["dones"].append(dones[i].cpu())
else:
    # For feedforward networks: store individual transitions
    self.replay_buffer.push(
        observations=self.current_obs,
        actions=actions,
        rewards=reward_tensor,
        next_observations=next_obs,
        dones=dones,
    )
```

**Also add helper method** after `_training_step()`:
```python
def _log_reward_components(
    self,
    components: dict[str, torch.Tensor],
    intrinsic_weight: torch.Tensor | None,
) -> None:
    """Log reward component means to TensorBoard."""
    if self.tensorboard_logger is None:
        return

    step = self.total_steps

    # Log mean values across all agents
    self.tensorboard_logger.log_custom_metric(
        "Rewards/Extrinsic_Mean", components["extrinsic"].mean().item(), step
    )
    self.tensorboard_logger.log_custom_metric(
        "Rewards/Intrinsic_Mean", components["intrinsic"].mean().item(), step
    )
    self.tensorboard_logger.log_custom_metric(
        "Rewards/Shaping_Mean", components["shaping"].mean().item(), step
    )

    # Log intrinsic_raw if available (before modifiers)
    if "intrinsic_raw" in components:
        self.tensorboard_logger.log_custom_metric(
            "Rewards/Intrinsic_Raw_Mean", components["intrinsic_raw"].mean().item(), step
        )

    # Log effective intrinsic weight
    if intrinsic_weight is not None:
        self.tensorboard_logger.log_custom_metric(
            "Rewards/Intrinsic_Weight_Mean", intrinsic_weight.mean().item(), step
        )
```

**Why**: Central extraction point for components; logs to TensorBoard for debugging.

**Verification**:
```bash
uv run pytest tests/test_townlet/unit/population/test_vectorized_population.py -k "reward" -v
```

---

## Task 4: Update ReplayBuffer to store components

**File**: `src/townlet/training/replay_buffer.py`

### 4a. Add storage tensors (after line 52)

**Current** (line 48-52):
```python
# Storage tensors (initialized on first push)
self.observations: torch.Tensor | None = None
self.actions: torch.Tensor | None = None
self.rewards: torch.Tensor | None = None  # CRIT-07: Single total rewards field
self.next_observations: torch.Tensor | None = None
self.dones: torch.Tensor | None = None
```

**New**:
```python
# Storage tensors (initialized on first push)
self.observations: torch.Tensor | None = None
self.actions: torch.Tensor | None = None
self.rewards: torch.Tensor | None = None  # Total reward
self.rewards_extrinsic: torch.Tensor | None = None  # DAC extrinsic component
self.rewards_intrinsic: torch.Tensor | None = None  # DAC intrinsic component (after modifiers)
self.rewards_shaping: torch.Tensor | None = None    # DAC shaping component
self.next_observations: torch.Tensor | None = None
self.dones: torch.Tensor | None = None
```

### 4b. Update push() to store components (line 94-100)

**Current** (line 94-100):
```python
if self.observations is None:
    self.observations = torch.zeros(self.capacity, obs_dim, device=self.device)
    self.actions = torch.zeros(self.capacity, dtype=torch.long, device=self.device)
    self.rewards = torch.zeros(self.capacity, device=self.device)
    self.next_observations = torch.zeros(self.capacity, obs_dim, device=self.device)
    self.dones = torch.zeros(self.capacity, dtype=torch.bool, device=self.device)
```

**New**:
```python
if self.observations is None:
    self.observations = torch.zeros(self.capacity, obs_dim, device=self.device)
    self.actions = torch.zeros(self.capacity, dtype=torch.long, device=self.device)
    self.rewards = torch.zeros(self.capacity, device=self.device)
    self.rewards_extrinsic = torch.zeros(self.capacity, device=self.device)
    self.rewards_intrinsic = torch.zeros(self.capacity, device=self.device)
    self.rewards_shaping = torch.zeros(self.capacity, device=self.device)
    self.next_observations = torch.zeros(self.capacity, obs_dim, device=self.device)
    self.dones = torch.zeros(self.capacity, dtype=torch.bool, device=self.device)
```

### 4c. Store component values in push() (after line 126)

After storing `self.rewards[indices] = reward_totals` (line 126), add:
```python
# Store components if available
if rewards.extrinsic is not None:
    self.rewards_extrinsic[indices] = rewards.extrinsic.to(self.device)
if rewards.intrinsic is not None:
    self.rewards_intrinsic[indices] = rewards.intrinsic.to(self.device)
if rewards.shaping is not None:
    self.rewards_shaping[indices] = rewards.shaping.to(self.device)
```

### 4d. Update serialize() format_version to 3 and add components (line 268-314)

Update `format_version` to 3 and add component tensors to serialization.

### 4e. Update load_from_serialized() to require version 3

Change version check from `< 2` to `< 3` and load component tensors.

### 4f. Update clear() and stats()

Add clearing and stats for new component tensors.

**Verification**:
```bash
uv run pytest tests/test_townlet/unit/training/test_replay_buffer.py -v
```

---

## Task 5: Update PrioritizedReplayBuffer similarly

**File**: `src/townlet/training/prioritized_replay_buffer.py`

Same pattern as Task 4:
- Add `rewards_extrinsic`, `rewards_intrinsic`, `rewards_shaping` storage (after line 55)
- Initialize in push() allocation block (line 89-94)
- Store components in push() loop (after line 119)
- Update serialize() to format_version 3, add components (line 288-338)
- Update load_from_serialized() version check to 3 (line 353)
- Update clear() to reset component tensors (line 231-246)
- Update stats() to include component memory (line 248-286)

**Verification**:
```bash
uv run pytest tests/test_townlet/unit/training/test_prioritized_replay_buffer.py -v
```

---

## Task 6: Update SequentialReplayBuffer for components

**File**: `src/townlet/training/sequential_replay_buffer.py`

### 6a. Update store_episode() validation (line 121)

**Current**:
```python
required_keys = {"observations", "actions", "rewards", "dones"}
```

**New**:
```python
required_keys = {"observations", "actions", "rewards", "dones"}
optional_component_keys = {"rewards_extrinsic", "rewards_intrinsic", "rewards_shaping"}
```

### 6b. Update serialize() format_version to 3 and add component keys

In the episode serialization loop (line 276-283), add component keys:
```python
serialized_episode = {
    "observations": episode["observations"].cpu(),
    "actions": episode["actions"].cpu(),
    "rewards": episode["rewards"].cpu(),
    "dones": episode["dones"].cpu(),
}
# Add components if present
for key in ["rewards_extrinsic", "rewards_intrinsic", "rewards_shaping"]:
    if key in episode:
        serialized_episode[key] = episode[key].cpu()
```

### 6c. Update load_from_serialized() version check to 3

Change version check from `< 2` to `< 3`.

**Verification**:
```bash
uv run pytest tests/test_townlet/unit/training/test_sequential_replay_buffer.py -v
```

---

## Task 7: Add log_reward_components() to TensorBoardLogger

**File**: `src/townlet/training/tensorboard_logger.py`

Add new method after `log_modifier_effects()` (after line 345):

```python
def log_reward_components(
    self,
    step: int,
    total: float,
    extrinsic: float,
    intrinsic: float,
    shaping: float,
    intrinsic_raw: float | None = None,
    intrinsic_weight: float | None = None,
    agent_id: str = "agent_0",
) -> None:
    """Log reward component breakdown for analysis.

    Logs each DAC reward component to enable debugging of reward composition.
    Useful for diagnosing reward hacking, modifier effectiveness, and
    intrinsic/extrinsic balance.

    Args:
        step: Global training step (x-axis)
        total: Total composed reward
        extrinsic: Extrinsic (environment) reward component
        intrinsic: Intrinsic (exploration) reward after modifiers
        shaping: Shaping bonus component
        intrinsic_raw: Intrinsic before modifiers (optional)
        intrinsic_weight: Effective intrinsic weight after modifiers (optional)
        agent_id: Agent identifier (defaults to "agent_0" if empty)
    """
    agent_id = agent_id or "agent_0"
    prefix = f"{agent_id}/" if agent_id else ""

    self.writer.add_scalar(f"{prefix}Rewards/Total", total, step)
    self.writer.add_scalar(f"{prefix}Rewards/Extrinsic", extrinsic, step)
    self.writer.add_scalar(f"{prefix}Rewards/Intrinsic", intrinsic, step)
    self.writer.add_scalar(f"{prefix}Rewards/Shaping", shaping, step)

    if intrinsic_raw is not None:
        self.writer.add_scalar(f"{prefix}Rewards/Intrinsic_Raw", intrinsic_raw, step)

    if intrinsic_weight is not None:
        self.writer.add_scalar(f"{prefix}Rewards/Intrinsic_Weight", intrinsic_weight, step)
```

**Verification**:
```bash
uv run pytest tests/test_townlet/unit/training/test_tensorboard_logger.py -v
```

---

## Task 8: Update current_episodes initialization in VectorizedPopulation

**File**: `src/townlet/population/vectorized.py`

Find where `current_episodes` is initialized (search for `current_episodes`) and add component keys:

```python
self.current_episodes[i] = {
    "observations": [],
    "actions": [],
    "rewards": [],
    "rewards_extrinsic": [],  # NEW
    "rewards_intrinsic": [],  # NEW
    "rewards_shaping": [],    # NEW
    "dones": [],
}
```

Also update episode completion handler (where episodes are stored to buffer) to include components.

**Verification**:
```bash
uv run pytest tests/test_townlet/unit/population/test_vectorized_population.py -k "recurrent" -v
```

---

## Task 9: Add integration test for component flow

**File**: `tests/test_townlet/integration/test_reward_component_flow.py` (NEW)

```python
"""Integration test for RewardTensor component wiring."""

import torch
import pytest
from pathlib import Path

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.population.vectorized import VectorizedPopulation
from townlet.training.state import RewardTensor


@pytest.fixture
def minimal_config(tmp_path: Path):
    """Create minimal config for testing component flow."""
    # Use L0_0_minimal config
    return Path("configs/L0_0_minimal")


class TestRewardComponentFlow:
    """Verify components flow from DAC to buffer."""

    def test_dac_returns_components(self, minimal_config):
        """DACEngine.calculate_rewards returns component dict."""
        env = VectorizedHamletEnv.from_config_dir(
            config_dir=minimal_config,
            num_envs=1,
            device=torch.device("cpu"),
        )

        # Step to trigger DAC
        actions = torch.zeros(1, dtype=torch.long)
        obs, rewards, dones, info = env.step(actions)

        assert "reward_components" in info
        components = info["reward_components"]
        assert "extrinsic" in components
        assert "intrinsic" in components
        assert "shaping" in components

        env.close()

    def test_components_in_info_dict(self, minimal_config):
        """step() returns components in info dict."""
        env = VectorizedHamletEnv.from_config_dir(
            config_dir=minimal_config,
            num_envs=1,
            device=torch.device("cpu"),
        )

        obs, rewards, dones, info = env.step(torch.zeros(1, dtype=torch.long))

        assert "reward_components" in info
        assert "intrinsic_weight" in info

        env.close()

    def test_replay_buffer_stores_components(self, minimal_config, tmp_path):
        """Replay buffer stores component tensors."""
        from townlet.training.replay_buffer import ReplayBuffer

        buffer = ReplayBuffer(capacity=100, device=torch.device("cpu"))

        # Create RewardTensor with components
        reward_tensor = RewardTensor.from_dac(
            total=torch.tensor([1.0]),
            extrinsic=torch.tensor([0.5]),
            intrinsic=torch.tensor([0.3]),
            shaping=torch.tensor([0.2]),
        )

        buffer.push(
            observations=torch.randn(1, 29),
            actions=torch.zeros(1, dtype=torch.long),
            rewards=reward_tensor,
            next_observations=torch.randn(1, 29),
            dones=torch.zeros(1, dtype=torch.bool),
        )

        assert buffer.rewards_extrinsic is not None
        assert buffer.rewards_intrinsic is not None
        assert buffer.rewards_shaping is not None
        assert buffer.rewards_extrinsic[0].item() == pytest.approx(0.5)

    def test_checkpoint_format_version_3(self, minimal_config):
        """Serialized buffer has format_version 3."""
        from townlet.training.replay_buffer import ReplayBuffer

        buffer = ReplayBuffer(capacity=100, device=torch.device("cpu"))

        reward_tensor = RewardTensor.from_dac(
            total=torch.tensor([1.0]),
            extrinsic=torch.tensor([0.5]),
            intrinsic=torch.tensor([0.3]),
            shaping=torch.tensor([0.2]),
        )

        buffer.push(
            observations=torch.randn(1, 29),
            actions=torch.zeros(1, dtype=torch.long),
            rewards=reward_tensor,
            next_observations=torch.randn(1, 29),
            dones=torch.zeros(1, dtype=torch.bool),
        )

        serialized = buffer.serialize()
        assert serialized["format_version"] == 3
        assert "rewards_extrinsic" in serialized
        assert "rewards_intrinsic" in serialized
        assert "rewards_shaping" in serialized

    def test_load_rejects_old_format(self):
        """Loading format_version < 3 raises ValueError."""
        from townlet.training.replay_buffer import ReplayBuffer

        buffer = ReplayBuffer(capacity=100, device=torch.device("cpu"))

        old_format = {
            "format_version": 2,
            "size": 0,
            "position": 0,
            "capacity": 100,
            "observations": None,
            "actions": None,
            "rewards": None,
            "next_observations": None,
            "dones": None,
        }

        with pytest.raises(ValueError, match="format_version < 3"):
            buffer.load_from_serialized(old_format)
```

**Verification**:
```bash
uv run pytest tests/test_townlet/integration/test_reward_component_flow.py -v
```

---

## Implementation Order

1. **Task 1**: DACEngine intrinsic_raw (foundation)
2. **Task 2**: vectorized_env info dict (pass-through)
3. **Task 7**: TensorBoardLogger method (can be done in parallel)
4. **Task 4**: ReplayBuffer storage (core)
5. **Task 5**: PrioritizedReplayBuffer (same pattern)
6. **Task 6**: SequentialReplayBuffer (same pattern)
7. **Task 3**: VectorizedPopulation extraction (connects all pieces)
8. **Task 8**: current_episodes initialization (recurrent support)
9. **Task 9**: Integration tests (verification)

---

## Full Test Suite Verification

After all tasks:
```bash
uv run pytest tests/test_townlet/ --ignore=tests/test_townlet/performance -q
```

Expected: All tests pass, format_version 3 enforced.

---

## Rollback Plan

If issues arise:
1. Revert format_version to 2
2. Remove component tensor storage
3. Keep components in info dict but don't consume them

Components are additive - old functionality remains intact.
