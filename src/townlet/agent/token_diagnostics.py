"""Training-dynamical diagnostics riding the token net (token-obs spec §3b / §6).

The structural suite passes green while training quietly degrades without these —
they are RECORDED METRICS, computed against a live `TokenSetQNetwork` and the
compiled `TokenSpec`, for the training loop to log every diagnostic interval
(the Task-10 cut wires `token_diagnostic_metrics` beside the existing TensorBoard
metrics; nothing here runs in the live step path this task).

What lands here (unit 3 Task 9):

- per-type encoder gradient norms (dead rare-type encoders are invisible in a
  whole-network norm);
- the cold-token injection hook (bounded Q-perturbation when a never-seen token
  toggles present);
- presence-flip counting between s and s' + conditioning of any per-sample signal
  on it (TD-error and intrinsic reward vs presence-flip count — §3b's named risk:
  RND novelty becoming a visibility-churn detector);
- pooled-embedding norm and online-vs-target cosine drift.

The probe EXPERIMENTS (flat-vs-token A/B, mean-vs-attention learning probe,
slot-swap decode) are unit-4/5 scope per spec §6 — deliberately not here.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import torch
import torch.nn as nn

from townlet.agent.networks import TokenSetQNetwork

if TYPE_CHECKING:
    from townlet.universe.dto.token_spec import TokenSpec

__all__ = [
    "cold_token_injection",
    "condition_on_presence_flips",
    "online_target_cosine",
    "per_type_encoder_grad_norms",
    "pooled_embedding_norm",
    "presence_flip_count",
    "token_diagnostic_metrics",
]


def per_type_encoder_grad_norms(network: TokenSetQNetwork) -> dict[str, float]:
    """L2 gradient norm per token type (projection weight + bias + type embedding).

    Call AFTER ``backward()``: a type whose norm sits at exactly 0.0 across steps is
    a dead encoder (rare-type starvation — §6). Parameters with no grad count 0.
    """
    norms: dict[str, float] = {}
    for type_name in network.token_type_names:
        encoder = network.encoders[type_name]
        assert isinstance(encoder, nn.Linear)
        total = 0.0
        for parameter in (encoder.weight, encoder.bias, network.type_embeddings[type_name]):
            if parameter.grad is not None:
                total += float(parameter.grad.detach().pow(2).sum())
        norms[type_name] = math.sqrt(total)
    return norms


def presence_flip_count(token_spec: TokenSpec, obs_before: torch.Tensor, obs_after: torch.Tensor) -> torch.Tensor:
    """Per-sample count of token rows whose presence bit flips between s and s'.

    Presence flips are the large discontinuous jumps §3b names: this count is the
    conditioning variable for both the TD-error and the intrinsic-reward diagnostics.
    """
    if obs_before.shape != obs_after.shape:
        raise ValueError(f"observation shapes differ: {tuple(obs_before.shape)} vs {tuple(obs_after.shape)}")
    presence_columns = torch.tensor([start for _name, _slot, start, _end in token_spec.row_layout()], device=obs_before.device)
    before = obs_before.index_select(1, presence_columns) > 0.5
    after = obs_after.index_select(1, presence_columns) > 0.5
    return (before ^ after).sum(dim=1)


def condition_on_presence_flips(values: torch.Tensor, flips: torch.Tensor) -> dict[int, float]:
    """Mean of a per-sample signal conditioned on presence-flip count.

    One shape serves both §3b diagnostics: pass TD errors for the TD-error
    distribution, intrinsic rewards for the visibility-churn pump check
    (the PDR-0016 shape, measured once already in this repo).
    """
    if values.shape != flips.shape:
        raise ValueError(f"values and flips must align per sample: {tuple(values.shape)} vs {tuple(flips.shape)}")
    out: dict[int, float] = {}
    for flip_count in torch.unique(flips):
        mask = flips == flip_count
        out[int(flip_count)] = float(values[mask].mean())
    return out


def cold_token_injection(
    network: TokenSetQNetwork,
    token_spec: TokenSpec,
    obs: torch.Tensor,
    *,
    type_name: str,
    slot_index: int,
    payload: torch.Tensor | None = None,
) -> float:
    """The cold-token injection hook (§6): toggle one token present and measure the
    Q-perturbation.

    Returns max |ΔQ| over the batch and actions when the named slot flips from its
    state in ``obs`` to present-with-``payload`` (zeros when omitted — the coldest
    payload). An unbounded response to a never-seen token is the failure this hook
    exists to see; the bound itself is a training-time observation, not asserted.
    """
    if type_name not in network.token_type_names:
        raise ValueError(f"type {type_name!r} is not in the network roster {network.token_type_names}")
    for name, slot, start, end in token_spec.row_layout():
        if name == type_name and slot == slot_index:
            with torch.no_grad():
                baseline = network(obs)
                injected = obs.clone()
                injected[:, start] = 1.0
                width = end - start - 1
                if payload is None:
                    injected[:, start + 1 : end] = 0.0
                else:
                    if payload.shape[-1] != width:
                        raise ValueError(f"payload width {payload.shape[-1]} != slot payload width {width}")
                    injected[:, start + 1 : end] = payload.to(dtype=injected.dtype)
                perturbed = network(injected)
            return float((perturbed - baseline).abs().max())
    raise ValueError(f"slot {type_name}[{slot_index}] is not in the TokenSpec layout")


def pooled_embedding_norm(network: TokenSetQNetwork, obs: torch.Tensor) -> float:
    """Mean L2 norm of the pooled set embedding over the batch."""
    with torch.no_grad():
        return float(network.pooled_embedding(obs).norm(dim=-1).mean())


def online_target_cosine(online: TokenSetQNetwork, target: TokenSetQNetwork, obs: torch.Tensor) -> float:
    """Mean cosine similarity between online and target pooled embeddings.

    Drift toward 0 (or negative) between target syncs is representation churn the
    Q-head must chase; recorded, not gated.
    """
    with torch.no_grad():
        online_pooled = online.pooled_embedding(obs)
        target_pooled = target.pooled_embedding(obs)
        return float(torch.nn.functional.cosine_similarity(online_pooled, target_pooled, dim=-1, eps=1e-8).mean())


def token_diagnostic_metrics(
    *,
    online: TokenSetQNetwork,
    target: TokenSetQNetwork,
    token_spec: TokenSpec,
    obs: torch.Tensor,
    next_obs: torch.Tensor,
    td_errors: torch.Tensor | None = None,
    intrinsic_rewards: torch.Tensor | None = None,
) -> dict[str, float]:
    """One flat metric dict per diagnostic interval — the recording surface the
    Task-10 training loop logs (grad norms are read from the online net's CURRENT
    grads, so call after ``backward()`` and before ``zero_grad()``)."""
    metrics: dict[str, float] = {}
    for type_name, norm in per_type_encoder_grad_norms(online).items():
        metrics[f"TokenNet/GradNorm/{type_name}"] = norm
    flips = presence_flip_count(token_spec, obs, next_obs)
    metrics["TokenNet/PresenceFlips_Mean"] = float(flips.to(dtype=torch.float32).mean())
    metrics["TokenNet/PooledNorm"] = pooled_embedding_norm(online, obs)
    metrics["TokenNet/OnlineTargetCosine"] = online_target_cosine(online, target, obs)
    if td_errors is not None:
        for flip_count, mean_value in condition_on_presence_flips(td_errors, flips).items():
            metrics[f"TokenNet/TDError_At{flip_count}Flips"] = mean_value
    if intrinsic_rewards is not None:
        for flip_count, mean_value in condition_on_presence_flips(intrinsic_rewards, flips).items():
            metrics[f"TokenNet/Intrinsic_At{flip_count}Flips"] = mean_value
    return metrics
