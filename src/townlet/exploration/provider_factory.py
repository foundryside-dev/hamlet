"""Construct actual curiosity backends independently of scope routing and cadence."""

from __future__ import annotations

import torch

from townlet.config.bac_options import RNDOptions
from townlet.config.exploration_policy import ResolvedExplorationPolicy
from townlet.exploration.adaptive_intrinsic import AdaptiveIntrinsicExploration
from townlet.exploration.base import ExplorationStrategy
from townlet.exploration.count_based import CountExploration
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
from townlet.exploration.icm import ICMExploration
from townlet.exploration.rnd import RNDExploration
from townlet.exploration.world_curiosity_state import WorldCuriosityDescriptor, WorldRNGState


def _validated_policy(policy: ResolvedExplorationPolicy) -> ResolvedExplorationPolicy:
    if not isinstance(policy, ResolvedExplorationPolicy):
        raise ValueError("factory requires an actual resolved exploration policy")
    return ResolvedExplorationPolicy.from_dict(policy.to_dict())


def make_policy_selector(policy: ResolvedExplorationPolicy) -> EpsilonGreedyExploration:
    """Return a fresh global epsilon selector; consumers own its completion cadence."""
    policy = _validated_policy(policy)
    return EpsilonGreedyExploration(epsilon=policy.epsilon_start, epsilon_decay=policy.epsilon_decay, epsilon_min=policy.epsilon_end)


def make_backend(
    policy: ResolvedExplorationPolicy,
    *,
    world_id: str | None,
    obs_dim: int,
    action_dim: int,
    device: torch.device | str,
    rng: WorldRNGState | None,
    descriptor: WorldCuriosityDescriptor | None,
) -> ExplorationStrategy:
    """Validate explicit ownership before constructing the selected real provider.

    Private callers pass the actual candidate received by OwnedWorldBackend.construct.
    Binding validation supports that candidate's active model_init custody; lifecycle
    snapshot/restore operations remain outside this callback. Shared ownership inputs
    must all be explicit None. The factory never selects a seed or services a queue.
    """
    policy = _validated_policy(policy)
    if type(obs_dim) is not int or obs_dim < 0:
        raise ValueError("factory observation dimension must be a nonnegative exact integer")
    if policy.strategy != "none" and obs_dim == 0:
        raise ValueError("selected curiosity provider requires a positive observation dimension")
    if type(action_dim) is not int or action_dim <= 0:
        raise ValueError("factory action dimension must be a positive exact integer")
    selected_device = torch.device(device)
    if selected_device.type not in {"cpu", "cuda"}:
        raise ValueError("factory requires a CPU or CUDA destination")
    if selected_device.type == "cuda" and selected_device.index is None:
        raise ValueError("factory CUDA destination requires an explicit device index")
    cuda_devices: tuple[int, ...] = ()
    if selected_device.type == "cuda":
        assert selected_device.index is not None
        cuda_devices = (selected_device.index,)

    if policy.curiosity_scope == "shared":
        if world_id is not None or rng is not None or descriptor is not None:
            raise ValueError("shared construction requires explicit absent world, RNG and descriptor ownership")
        if policy.service_clock_unit != "vector_tick":
            raise ValueError("shared construction requires the vector_tick service clock")
    else:
        if not isinstance(descriptor, WorldCuriosityDescriptor) or not isinstance(rng, WorldRNGState):
            raise ValueError("private construction requires an actual descriptor and world RNG owner")
        if type(world_id) is not str or not world_id or world_id not in descriptor.world_ids:
            raise ValueError("private construction requires an exact declared world ID")
        if policy.service_clock_unit != "world_eligible_admission":
            raise ValueError("private construction requires the world_eligible_admission service clock")
        checked_descriptor = WorldCuriosityDescriptor.from_dict(descriptor.to_dict())
        expected_descriptor = WorldCuriosityDescriptor.from_policy(
            policy,
            world_ids=checked_descriptor.world_ids,
            observation_dim=obs_dim,
            action_dim=action_dim,
            training_seed=checked_descriptor.training_seed,
        )
        if checked_descriptor.to_dict() != expected_descriptor.to_dict():
            raise ValueError("factory descriptor disagrees with selected policy or geometry")
        rng.validate_binding(descriptor=expected_descriptor, world_id=world_id, cuda_devices=cuda_devices)

    if policy.strategy == "none":
        return make_policy_selector(policy)
    parameters = policy.provider_parameters
    if policy.strategy == "count_based":
        return CountExploration(
            policy, quantization_width=parameters["quantization_width"], max_entries=parameters["max_entries"], device=selected_device
        )
    if policy.strategy == "icm":
        return ICMExploration(
            policy,
            obs_dim=obs_dim,
            action_dim=action_dim,
            feature_dim=parameters["feature_dim"],
            hidden_dim=parameters["hidden_dim"],
            learning_rate=parameters["learning_rate"],
            inverse_weight=parameters["inverse_weight"],
            forward_weight=parameters["forward_weight"],
            training_batch_size=parameters["training_batch_size"],
            max_pending_transitions=parameters["max_pending_transitions"],
            device=selected_device,
            rng=rng,
            service_clock_unit=policy.service_clock_unit,
        )

    options = RNDOptions(
        service_mode=policy.service_mode,
        max_updates_per_tick=policy.max_updates_per_tick,
        max_pending_rows=policy.max_pending_rows,
        overflow_policy=policy.overflow_policy,
    )
    backend: RNDExploration | AdaptiveIntrinsicExploration
    if policy.strategy == "rnd":
        backend = RNDExploration(
            obs_dim=obs_dim,
            embed_dim=policy.rnd_feature_dim,
            learning_rate=policy.rnd_learning_rate,
            training_batch_size=policy.predictor_batch_size,
            epsilon_start=policy.epsilon_start,
            epsilon_min=policy.epsilon_end,
            epsilon_decay=policy.epsilon_decay,
            device=selected_device,
            rng=rng,
            service_clock_unit=policy.service_clock_unit,
        )
    else:
        backend = AdaptiveIntrinsicExploration(
            obs_dim=obs_dim,
            embed_dim=policy.rnd_feature_dim,
            rnd_learning_rate=policy.rnd_learning_rate,
            rnd_training_batch_size=policy.predictor_batch_size,
            initial_intrinsic_weight=policy.initial_intrinsic_weight,
            min_intrinsic_weight=policy.min_intrinsic_weight,
            variance_threshold=policy.variance_threshold,
            min_survival_fraction=policy.min_survival_fraction,
            max_episode_length=policy.max_episode_length,
            survival_window=policy.survival_window,
            decay_rate=policy.decay_rate,
            epsilon_start=policy.epsilon_start,
            epsilon_min=policy.epsilon_end,
            epsilon_decay=policy.epsilon_decay,
            device=selected_device,
            rng=rng,
            service_clock_unit=policy.service_clock_unit,
        )
    backend.configure_service(options)
    return backend
