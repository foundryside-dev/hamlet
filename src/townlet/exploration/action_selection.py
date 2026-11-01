"""
Shared action selection utilities for exploration strategies.

This module contains common action selection logic used across multiple
exploration strategies to avoid duplication.
"""

import torch


def epsilon_greedy_action_selection(
    q_values: torch.Tensor,  # [batch, num_actions]
    epsilons: torch.Tensor,  # [batch] per-agent epsilon values
    action_masks: torch.Tensor | None = None,  # [batch, num_actions] bool
) -> torch.Tensor:
    """
    Select actions using epsilon-greedy strategy with action masking.

    Legacy transport adapter: empty mask rows retain unmasked greedy output.
    This API has no producer eligibility and cannot diagnose live-empty rows.
    Producers with eligibility must use epsilon_greedy_action_selection_eligible.

    This is a shared utility used by multiple exploration strategies:
    - EpsilonGreedyExploration
    - RNDExploration
    - AdaptiveIntrinsicExploration
    - VectorizedPopulation (for inference)

    Args:
        q_values: Q-values for each action [batch, num_actions]
        epsilons: Per-agent exploration rates [batch] (0.0 = greedy, 1.0 = random)
        action_masks: Optional validity masks [batch, num_actions] bool (True = valid)

    Returns:
        actions: [batch] selected action indices (long)

    Example:
        >>> q_values = torch.randn(4, 6)  # 4 agents, 6 actions
        >>> epsilons = torch.tensor([0.1, 0.5, 0.0, 1.0])
        >>> action_masks = torch.ones(4, 6, dtype=torch.bool)
        >>> actions = epsilon_greedy_action_selection(q_values, epsilons, action_masks)
        >>> actions.shape
        torch.Size([4])
    """
    batch_size, num_actions = q_values.shape
    device = q_values.device

    # Apply action masking to Q-values if provided
    if action_masks is not None:
        # Detect rows with no valid actions (all False) - BUG-23
        valid_count = action_masks.sum(dim=1)  # [batch]
        all_invalid = valid_count == 0  # [batch] bool

        masked_q_values = q_values.clone()
        masked_q_values[~action_masks] = float("-inf")
    else:
        masked_q_values = q_values
        all_invalid = None

    # Greedy actions (argmax of masked Q-values)
    greedy_actions = torch.argmax(masked_q_values, dim=1)

    # For rows with all invalid actions, use argmax of unmasked Q-values (BUG-23)
    if all_invalid is not None and all_invalid.any():
        unmasked_greedy = torch.argmax(q_values, dim=1)
        greedy_actions = torch.where(all_invalid, unmasked_greedy, greedy_actions)

    # Random actions (sample only from valid actions)
    if action_masks is not None:
        # Empty legacy rows are transport only, never part of the sampler.
        assert all_invalid is not None
        valid_rows = ~all_invalid
        random_actions = greedy_actions.clone()
        if valid_rows.any():
            probs = action_masks[valid_rows].float()
            probs = probs / probs.sum(dim=1, keepdim=True)
            random_actions[valid_rows] = torch.multinomial(probs, num_samples=1).squeeze(1)
    else:
        # No masking: sample uniformly from all actions
        random_actions = torch.randint(0, num_actions, (batch_size,), device=device)

    # Epsilon mask: True = explore (random), False = exploit (greedy)
    explore_mask = torch.rand(batch_size, device=device) < epsilons

    # Select based on mask
    actions = torch.where(explore_mask, random_actions, greedy_actions)

    return actions


def epsilon_greedy_action_selection_eligible(
    q_values: torch.Tensor,
    epsilons: torch.Tensor,
    action_masks: torch.Tensor | None,
    *,
    eligible: torch.Tensor,
) -> torch.Tensor:
    """Select only producer-declared eligible rows, rejecting live-empty legality.

    ``eligible`` is actual active membership, never inferred from mask contents.
    Inactive rows return unmasked greedy indices solely for transport and consume
    no random draws. Explicit ``action_masks=None`` permits all actions.
    """
    if not isinstance(eligible, torch.Tensor) or eligible.dtype != torch.bool:
        raise ValueError("eligible must be a bool tensor")
    if eligible.shape != q_values.shape[:1] or eligible.device != q_values.device:
        raise ValueError("eligible shape/device must match q_values rows")
    if action_masks is not None:
        if action_masks.dtype != torch.bool or action_masks.shape != q_values.shape or action_masks.device != q_values.device:
            raise ValueError("action_masks must be bool with q_values shape/device")
        if (eligible & ~action_masks.any(dim=1)).any():
            raise ValueError("eligible rows have no legal actions")
    actions = q_values.argmax(dim=1)
    if eligible.any():
        if action_masks is None:
            masks = None
        else:
            masks = action_masks[eligible]
        actions[eligible] = epsilon_greedy_action_selection(q_values[eligible], epsilons[eligible], masks)
    return actions
