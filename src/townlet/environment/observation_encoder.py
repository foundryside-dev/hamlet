"""Observation encoding for :class:`VectorizedHamletEnv`."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import TYPE_CHECKING, cast

import torch

from townlet.vfs.observation_builder import VFSObservationSpec, build_vfs_observation

if TYPE_CHECKING:
    from townlet.environment.vectorized_env import VectorizedHamletEnv


class ObservationEncoder:
    """Build runtime observation tensors from the environment state."""

    def __init__(self, env: VectorizedHamletEnv) -> None:
        self._env = env

    def _get_observations(self) -> torch.Tensor:
        """Construct observation vector using compiled observation spec."""
        env = self._env
        obs_fields = env.observation_spec.fields
        outputs: list[torch.Tensor] = []
        self._sync_position_observation_to_vfs()

        def _ensure_observation_field_shape(field_name: str, value: torch.Tensor, dims: int) -> torch.Tensor:
            if value.dim() == 1:
                value = value.unsqueeze(1)
            expected_shape = (env.num_agents, dims)
            if value.dim() != 2 or tuple(value.shape) != expected_shape:
                raise ValueError(f"Observation field '{field_name}' produced shape {tuple(value.shape)}, expected {expected_shape}.")
            return value

        for field in obs_fields:
            name = field.name
            dims = field.dims

            if name == "obs_grid_encoding":
                if env.partial_observability:
                    value = torch.zeros((env.num_agents, dims), device=env.device)
                else:
                    if hasattr(env.substrate, "_encode_full_grid"):
                        grid_encoding = env.substrate._encode_full_grid(env.positions, env.affordances)
                    else:
                        grid_encoding = env.substrate.encode_observation(env.positions, env.affordances)
                    value = grid_encoding
            elif name == "obs_local_window":
                if not env.partial_observability:
                    value = torch.zeros((env.num_agents, dims), device=env.device)
                else:
                    local_window = env.substrate.encode_partial_observation(
                        env.positions,
                        env.affordances,
                        vision_range=env.vision_radius,
                    )
                    value = local_window
            elif name == "obs_position":
                value = self._build_vfs_agent_observation_field(name, dims)
            elif name == "obs_velocity":
                vel = env._encode_velocity_observation()
                if vel is None:
                    value = torch.zeros((env.num_agents, dims), device=env.device)
                else:
                    value = vel
            elif name == "obs_meters":
                value = env.meters
            elif name in {"obs_affordance_at_position", "obs_affordances"}:
                value = env._build_affordance_encoding(dims)
            elif name == "obs_effects":
                value = env._build_effects_observation(dims)
            elif name == "obs_temporal":
                if not env.temporal_support_enabled or not env.enable_temporal_mechanics:
                    value = torch.zeros((env.num_agents, dims), device=env.device)
                else:
                    time_of_day = env.time_of_day
                    day_length = float(env.day_length)
                    time_angle = (time_of_day / day_length) * 2 * math.pi
                    time_sin = torch.tensor(math.sin(time_angle), device=env.device)
                    time_cos = torch.tensor(math.cos(time_angle), device=env.device)
                    day_progress = float(time_of_day) / day_length
                    night_threshold = day_length * 0.25
                    if time_of_day < night_threshold or time_of_day >= (day_length - night_threshold):
                        is_night = 1.0
                    else:
                        is_night = 0.0

                    value = torch.zeros((env.num_agents, dims), device=env.device)
                    if dims > 0:
                        value[:, 0] = time_sin
                    if dims > 1:
                        value[:, 1] = time_cos
                    if dims > 2:
                        value[:, 2] = day_progress
                    if dims > 3:
                        value[:, 3] = is_night
            elif name == "obs_vfs":
                if env.vfs_observation_spec is not None:
                    agent_item_inventory = None
                    if env.item_inventory is not None:
                        agent_item_inventory = env.item_inventory.slots

                    value = build_vfs_observation(
                        registry=env.vfs_registry,
                        spec=env.vfs_observation_spec,
                        batch_size=env.num_agents,
                        agent_item_inventory=agent_item_inventory,
                    )
                else:
                    value = torch.zeros((env.num_agents, dims), device=env.device)
            else:
                if name not in env.vfs_registry._definitions:
                    raise ValueError(f"Observation field '{name}' not found in VFS variables (no defaults allowed).")
                val = env.vfs_registry.get(name, reader="engine")
                if val.dim() > 1:
                    value = val
                else:
                    value = val.unsqueeze(1)

            outputs.append(_ensure_observation_field_shape(name, value, dims))

        observations = torch.cat(outputs, dim=1)

        activity = getattr(env, "observation_activity", None)
        if activity is not None and activity.active_mask:
            if len(activity.active_mask) != observations.shape[1]:
                raise ValueError(
                    "ObservationActivity mask length does not match observation_dim.\n"
                    f"  mask_len={len(activity.active_mask)}, obs_dim={observations.shape[1]}"
                )
            mask = torch.tensor(activity.active_mask, device=env.device, dtype=observations.dtype)
            observations = observations * mask.unsqueeze(0)

        return observations

    def _build_vfs_agent_observation_field(self, field_name: str, dims: int) -> torch.Tensor:
        """Build a single agent-scoped observation field from VFS registry state."""
        env = self._env
        if field_name not in env.vfs_registry.variables:
            raise ValueError(f"Observation field '{field_name}' is not backed by a VFS variable.")

        spec = VFSObservationSpec(
            global_vfs_dim=0,
            agent_vfs_dim=dims,
            item_vfs_dim=0,
            agent_vars=(field_name,),
            agent_active_mask=tuple(True for _ in range(dims)),
        )
        return build_vfs_observation(
            registry=env.vfs_registry,
            spec=spec,
            batch_size=env.num_agents,
        )

    def _sync_position_observation_to_vfs(self) -> None:
        """Publish the current substrate position observation into VFS state."""
        env = self._env
        has_position_field = any(field.name == "obs_position" for field in env.observation_spec.fields)
        if not has_position_field:
            return
        if "obs_position" not in env.vfs_registry.variables:
            raise ValueError("Observation field 'obs_position' is present but no matching VFS variable exists.")

        position = self._encode_position_observation()
        if position is None:
            raise ValueError("Observation field 'obs_position' is present but the substrate does not expose position features.")
        env.vfs_registry.set("obs_position", position.to(device=env.device, dtype=torch.float32), writer="engine")

    def _build_affordance_encoding(self, dims: int) -> torch.Tensor:
        """Build one-hot encoding of current affordance under each agent."""
        env = self._env
        num_types = env.num_affordance_types
        total_dims = num_types + 1

        affordance_encoding = torch.zeros(env.num_agents, total_dims, device=env.device)

        for affordance_idx, affordance_name in enumerate(env.affordance_names):
            if affordance_name in env.affordances:
                affordance_pos = env.affordances[affordance_name]
                on_affordance = env.substrate.is_on_position(env.positions, affordance_pos)
                if on_affordance.any():
                    affordance_encoding[on_affordance, affordance_idx] = 1.0

        row_sums = affordance_encoding.sum(dim=1)
        none_mask = row_sums == 0
        affordance_encoding[none_mask, num_types] = 1.0

        if dims != total_dims:
            raise ValueError(f"Observation field 'obs_affordances' expected {dims} dims, but affordance encoding produced {total_dims}.")
        return affordance_encoding

    def _encode_position_observation(self) -> torch.Tensor | None:
        """Encode agent position using substrate-native semantics."""
        env = self._env
        if getattr(env.substrate, "position_dim", 0) == 0:
            return None

        encode_fn = Callable[[torch.Tensor, dict[str, torch.Tensor]], torch.Tensor]

        encoder = getattr(env.substrate, "_encode_position_features", None)
        if callable(encoder):
            typed_encoder = cast(encode_fn, encoder)
            return typed_encoder(env.positions, env.affordances)

        public_encoder = getattr(env.substrate, "encode_position_features", None)
        if callable(public_encoder):
            typed_public = cast(encode_fn, public_encoder)
            return typed_public(env.positions, env.affordances)

        encode_observation = getattr(env.substrate, "encode_observation", None)
        if callable(encode_observation):
            typed_encode_obs = cast(encode_fn, encode_observation)
            return typed_encode_obs(env.positions, env.affordances)

        normalizer = getattr(env.substrate, "normalize_positions", None)
        if callable(normalizer):
            typed_normalizer = cast(Callable[[torch.Tensor], torch.Tensor], normalizer)
            return typed_normalizer(env.positions)

        return None
