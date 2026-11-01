"""Detached DQN targets using only recorded successor legality."""

import math

import torch
from torch import Tensor

from townlet.training.replay_contract import validate_successor_masks


def _q_tensor(name: str, value: Tensor, reference: Tensor) -> None:
    if not isinstance(value, Tensor) or not value.is_floating_point():
        raise ValueError(f"{name} must be a floating tensor")
    if value.shape != reference.shape or value.device != reference.device or value.dtype != reference.dtype:
        raise ValueError(f"{name} shape/dtype/device must match q_target")


@torch.no_grad()
def legal_bootstrap(q_online: Tensor | None, q_target: Tensor, legal: Tensor, bootstrap: Tensor, *, double_dqn: bool) -> Tensor:
    """Return legal successor values, with exact zero on non-bootstrap rows.

    Arbitrary leading dimensions are preserved. Non-bootstrap rows are excluded
    before max/argmax; unused terminal and illegal outputs may be nonfinite.
    Double DQN selects with online Q and evaluates that action with target Q.
    """
    if not isinstance(q_target, Tensor) or not q_target.is_floating_point() or q_target.ndim < 1 or q_target.shape[-1] < 1:
        raise ValueError("q_target shape must be [...,A], A>0, with floating dtype")
    if type(double_dqn) is not bool:
        raise ValueError("double_dqn must be bool")
    if not isinstance(bootstrap, Tensor) or bootstrap.dtype != torch.bool:
        raise ValueError("bootstrap must be a bool tensor")
    if bootstrap.shape != q_target.shape[:-1] or bootstrap.device != q_target.device:
        raise ValueError("bootstrap shape/device must match q_target leading dimensions")
    validate_successor_masks(legal, ~bootstrap, action_dim=q_target.shape[-1])
    if legal.device != q_target.device:
        raise ValueError("legal device must match q_target")
    if double_dqn:
        if q_online is None:
            raise ValueError("Double DQN requires q_online")
        _q_tensor("q_online", q_online, q_target)
    result = torch.zeros_like(bootstrap, dtype=q_target.dtype)
    if not bootstrap.any():
        return result
    mask, target = legal[bootstrap], q_target[bootstrap]
    selector = target
    if double_dqn and q_online is not None:
        selector = q_online[bootstrap]
    if not torch.isfinite(selector[mask]).all():
        raise ValueError("bootstrapped legal selection Q values must be finite")
    choice = selector.masked_fill(~mask, -torch.inf).argmax(dim=-1, keepdim=True)
    values = target.gather(-1, choice).squeeze(-1)
    if not torch.isfinite(values).all():
        raise ValueError("bootstrapped selected target Q values must be finite")
    result[bootstrap] = values
    return result


@torch.no_grad()
def legal_td_target(
    rewards: Tensor, dones: Tensor, q_online: Tensor | None, q_target: Tensor, legal: Tensor, *, gamma: float, double_dqn: bool
) -> Tensor:
    """Canonical reward plus discounted legal value; gamma=0 never reads Q.

    This operates on real transitions. Recurrent callers exclude padding using
    lengths, independently of their loss-mask/anchor selection.
    """
    if isinstance(gamma, bool) or not isinstance(gamma, (int, float)) or not math.isfinite(gamma) or not 0 <= gamma <= 1:
        raise ValueError("gamma must be finite in [0,1]")
    if not isinstance(rewards, Tensor) or not rewards.is_floating_point() or not torch.isfinite(rewards).all():
        raise ValueError("rewards must be finite floating values")
    if not isinstance(q_target, Tensor) or q_target.ndim < 1:
        raise ValueError("q_target shape must be [...,A]")
    validate_successor_masks(legal, dones, action_dim=q_target.shape[-1])
    if rewards.shape != dones.shape or rewards.device != q_target.device or rewards.dtype != q_target.dtype:
        raise ValueError("rewards shape/dtype/device must match real transition Q rows")
    values = legal_bootstrap(q_online, q_target, legal, (~dones) & (gamma != 0), double_dqn=double_dqn)
    result = rewards + gamma * values
    if not torch.isfinite(result).all():
        raise ValueError("Bellman targets must be finite")
    return result
