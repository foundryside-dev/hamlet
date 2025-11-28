# RewardTensor Component Wiring Design

**Date**: 2025-11-28
**Status**: Approved
**Author**: Claude + Human collaboration

## Summary

Wire up RewardTensor to actually populate and use reward component fields (extrinsic, intrinsic, shaping) that currently exist but are never populated. This enables reward decomposition analysis for debugging and pedagogy.

## Motivation

RewardTensor was introduced as scaffolding for explicit reward composition semantics, but components are never populated - only `total` is used. For HAMLET's pedagogical mission, being able to answer "why did the agent do X?" requires seeing reward breakdown.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Component flow | Via `info` dict in `step()` | Preserves Gym-like API |
| Component usage | TensorBoard + replay buffer storage | Full provenance for debugging |
| Buffer storage | Separate tensors per component | Explicit, self-documenting |
| Checkpoint versioning | Bump to v3, reject old | Zero backwards compatibility (CLAUDE.md) |

## Data Flow

```
DACEngine.calculate_rewards()
    │
    ▼
(total, weights, {extrinsic, intrinsic, shaping})
    │
    ▼
vectorized_env.step()
    │
    ├──► returns: (obs, rewards, dones, info)
    │                              │
    │              info["reward_components"] = {
    │                  "extrinsic": tensor,
    │                  "intrinsic": tensor,      # after modifiers
    │                  "intrinsic_raw": tensor,  # before modifiers
    │                  "intrinsic_weight": tensor,
    │                  "shaping": tensor
    │              }
    ▼
VectorizedPopulation._training_step()
    │
    ├──► RewardTensor.from_dac(total, extrinsic, intrinsic, shaping)
    │
    ├──► replay_buffer.push(rewards=reward_tensor)
    │         └──► stores: total, extrinsic, intrinsic, shaping
    │
    └──► tensorboard_logger.log_reward_components(reward_tensor)
```

## Components Tracked

| Field | Source | Store in Buffer | Log to TB |
|-------|--------|-----------------|-----------|
| `total` | DAC output | Yes | Yes |
| `extrinsic` | DAC extrinsic_fn | Yes | Yes |
| `intrinsic` | After modifiers | Yes | Yes |
| `intrinsic_raw` | Before modifiers | No (derivable) | Yes |
| `intrinsic_weight` | Effective modifier | No (derivable) | Yes |
| `shaping` | DAC shaping sum | Yes | Yes |

## Files to Modify

| File | Change |
|------|--------|
| `src/townlet/environment/vectorized_env.py` | Add components to `info` dict in `step()` |
| `src/townlet/population/vectorized.py` | Extract components from `info`, pass to `RewardTensor.from_dac()` |
| `src/townlet/training/replay_buffer.py` | Add component tensor storage, bump format_version to 3 |
| `src/townlet/training/prioritized_replay_buffer.py` | Same as above |
| `src/townlet/training/sequential_replay_buffer.py` | Store components in episode dict |
| `src/townlet/training/tensorboard_logger.py` | Add `log_reward_components()` method |

## TensorBoard Metrics

```python
# Core components
rewards/total
rewards/extrinsic
rewards/intrinsic          # After modifiers
rewards/intrinsic_raw      # Before modifiers
rewards/shaping

# Modifier insight
rewards/intrinsic_weight   # Effective weight after all modifiers (0.0-1.0)
```

## Checkpoint Format

```python
# format_version 3
{
    "format_version": 3,
    "rewards": tensor,           # total (existing, renamed internally)
    "rewards_extrinsic": tensor, # NEW
    "rewards_intrinsic": tensor, # NEW
    "rewards_shaping": tensor,   # NEW
    ...
}
```

Loading format_version < 3 raises `ValueError` with clear migration message.

## Test Updates

1. Update fixtures that create RewardTensor to include components
2. Add tests for component storage/retrieval in all replay buffer types
3. Add tests for TensorBoard logging of components
4. Add integration test verifying components flow from DAC to buffer

## Pedagogical Value

- Students can see "agent is exploring" when intrinsic spikes
- Can diagnose reward hacking by seeing which component dominates
- Can tune intrinsic weight by observing balance over training
- Can verify modifier suppression by comparing `intrinsic_raw` vs `intrinsic`
