"""Observation encoding for :class:`VectorizedHamletEnv`."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import TYPE_CHECKING, cast

import torch

from townlet.universe.compilers.observation import meter_name_from_observation_field
from townlet.vfs.observation_builder import VFSObservationSpec, apply_normalization, build_vfs_observation
from townlet.vfs.schema import NormalizationSpec

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
        self._sync_observation_primitives_to_vfs()

        for field in obs_fields:
            value = self._build_observation_field_from_vfs(field.name, field.dims)
            outputs.append(self._ensure_agent_observation_shape(field.name, value, field.dims))

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

    def _build_observation_field_from_vfs(self, field_name: str, dims: int) -> torch.Tensor:
        """Build one compiled observation field from VFS state."""
        env = self._env
        if field_name != "obs_vfs":
            return self._build_vfs_agent_observation_field(field_name, dims)

        if env.vfs_observation_spec is None:
            raise ValueError("Observation field 'obs_vfs' is present but no compiled VFS observation spec exists.")

        agent_item_inventory = None
        if env.item_inventory is not None:
            agent_item_inventory = env.item_inventory.slots

        return build_vfs_observation(
            registry=env.vfs_registry,
            spec=env.vfs_observation_spec,
            batch_size=env.num_agents,
            agent_item_inventory=agent_item_inventory,
        )

    def _build_vfs_agent_observation_field(self, field_name: str, dims: int) -> torch.Tensor:
        """Build a single agent-scoped observation field from VFS registry state."""
        env = self._env
        vfs_field = self._compiled_vfs_observation_field(field_name)
        source_variable = vfs_field.source_variable
        if source_variable not in env.vfs_registry.variables:
            raise ValueError(f"Observation field '{field_name}' is not backed by a VFS variable.")

        # SOURCE width, not observed width. The registry is read at the width the variable
        # actually stores; the declared normalizer may then WIDEN it (cyclical_sin_cos -> 2,
        # one_hot -> categories), and `_apply_declared_normalization` below is what checks the
        # result against the field's declared dims.
        #
        # This used to assert `shape_dims == dims` and read at `dims`. That equality is only
        # true for width-preserving kinds, so it fired before `apply_normalization` ever ran —
        # which is one of the reasons the widening kinds were unreachable in practice as well
        # as unauthorable (hamlet-3d3039f340).
        source_dims = 1
        for shape_dim in vfs_field.shape:
            source_dims *= shape_dim

        spec = VFSObservationSpec(
            global_vfs_dim=0,
            agent_vfs_dim=source_dims,
            item_vfs_dim=0,
            agent_vars=(source_variable,),
            agent_active_mask=tuple(True for _ in range(source_dims)),
        )
        raw = build_vfs_observation(
            registry=env.vfs_registry,
            spec=spec,
            batch_size=env.num_agents,
        )
        return self._apply_declared_normalization(field_name, raw, vfs_field.normalization, dims)

    def _apply_declared_normalization(
        self,
        field_name: str,
        value: torch.Tensor,
        normalization: NormalizationSpec | None,
        dims: int,
    ) -> torch.Tensor:
        """Apply a field's DECLARED normalization spec, if it declares one.

        Until WS-1(e) nothing applied these specs: `apply_normalization` implements the
        whole VFS normalization ABI, the specs are compiled and hashed into
        `observation_schema_hash`, and the `obs_meters` field description has always read
        "meter values (normalized)" — but no production code path ever called it. The
        declaration is now what drives the observation.
        """
        if normalization is None:
            return value
        normalized = apply_normalization(value, normalization)
        if normalized.shape[-1] != dims:
            raise ValueError(
                "Declared normalization changed an observation field's width.\n"
                f"  Field: {field_name}\n"
                f"  Normalization kind: {normalization.kind}\n"
                f"  Declared dims: {dims}, produced: {normalized.shape[-1]}\n"
                "  Rule: the compiled observation layout is fixed; a dimension-changing "
                "normalizer (cyclical_sin_cos, one_hot) must be reflected in the field's dims."
            )
        return normalized

    def _compiled_vfs_observation_field(self, field_name: str):
        """Return the compiler-emitted VFS observation field for an observation id."""
        for field in self._env.universe.vfs_observation_fields:
            if field.id == field_name:
                return field
        raise ValueError(f"Observation field '{field_name}' is missing from compiled VFS observation fields.")

    def _ensure_agent_observation_shape(self, field_name: str, value: torch.Tensor, dims: int) -> torch.Tensor:
        """Normalize and validate one agent-scoped observation field."""
        env = self._env
        if value.dim() == 1:
            value = value.unsqueeze(1)
        expected_shape = (env.num_agents, dims)
        if value.dim() != 2 or tuple(value.shape) != expected_shape:
            raise ValueError(f"Observation field '{field_name}' produced shape {tuple(value.shape)}, expected {expected_shape}.")
        return value

    def _set_observation_variable(self, field_name: str, value: torch.Tensor, dims: int) -> None:
        """Validate an observation primitive and publish it to the VFS registry."""
        env = self._env
        value = value.to(device=env.device, dtype=torch.float32)
        shaped = self._ensure_agent_observation_shape(field_name, value, dims)
        registry_value = shaped
        if dims == 1:
            registry_value = shaped[:, 0]
        env.vfs_registry.set(field_name, registry_value, writer="engine")

    def _sync_observation_primitives_to_vfs(self) -> None:
        """Publish system observation primitives into VFS state before assembly."""
        self._sync_grid_observation_to_vfs()
        self._sync_local_window_observation_to_vfs()
        self._sync_position_observation_to_vfs()
        self._sync_velocity_observation_to_vfs()
        self._sync_meter_observation_to_vfs()
        self._sync_affordance_observation_to_vfs()
        self._sync_effect_observation_to_vfs()
        self._sync_temporal_observation_to_vfs()

    def _sync_grid_observation_to_vfs(self) -> None:
        """Publish current global grid observation into VFS state."""
        env = self._env
        grid_field = next((field for field in env.observation_spec.fields if field.name == "obs_grid_encoding"), None)
        if grid_field is None:
            return
        if "obs_grid_encoding" not in env.vfs_registry.variables:
            raise ValueError("Observation field 'obs_grid_encoding' is present but no matching VFS variable exists.")

        if env.partial_observability:
            grid_encoding = torch.zeros((env.num_agents, grid_field.dims), device=env.device)
        elif hasattr(env.substrate, "_encode_full_grid"):
            grid_encoding = env.substrate._encode_full_grid(env.positions, env.affordances)
        else:
            grid_encoding = env.substrate.encode_observation(env.positions, env.affordances)

        self._set_observation_variable("obs_grid_encoding", grid_encoding, grid_field.dims)

    def _sync_local_window_observation_to_vfs(self) -> None:
        """Publish current local-window observation into VFS state."""
        env = self._env
        local_field = next((field for field in env.observation_spec.fields if field.name == "obs_local_window"), None)
        if local_field is None:
            return
        if "obs_local_window" not in env.vfs_registry.variables:
            raise ValueError("Observation field 'obs_local_window' is present but no matching VFS variable exists.")

        if not env.partial_observability:
            local_window = torch.zeros((env.num_agents, local_field.dims), device=env.device)
        else:
            local_window = env.substrate.encode_partial_observation(
                env.positions,
                env.affordances,
                vision_range=env.vision_radius,
            )

        self._set_observation_variable("obs_local_window", local_window, local_field.dims)

    def _sync_velocity_observation_to_vfs(self) -> None:
        """Publish current velocity observation into VFS state."""
        env = self._env
        velocity_field = next((field for field in env.observation_spec.fields if field.name == "obs_velocity"), None)
        if velocity_field is None:
            return
        if "obs_velocity" not in env.vfs_registry.variables:
            raise ValueError("Observation field 'obs_velocity' is present but no matching VFS variable exists.")

        velocity = env._encode_velocity_observation()
        if velocity is None:
            velocity = torch.zeros((env.num_agents, velocity_field.dims), device=env.device)

        self._set_observation_variable("obs_velocity", velocity, velocity_field.dims)

    def _sync_position_observation_to_vfs(self) -> None:
        """Publish the current substrate position observation into VFS state."""
        env = self._env
        has_position_field = any(field.name == "obs_position" for field in env.observation_spec.fields)
        if not has_position_field:
            return
        if "obs_position" not in env.vfs_registry.variables:
            raise ValueError("Observation field 'obs_position' is present but no matching VFS variable exists.")

        position = env._encode_position_observation()
        if position is None:
            raise ValueError("Observation field 'obs_position' is present but the substrate does not expose position features.")
        position_field = env.observation_spec.get_field_by_name("obs_position")
        self._set_observation_variable("obs_position", position, position_field.dims)

    def _sync_meter_observation_to_vfs(self) -> None:
        """Publish each meter's current value into its own VFS source variable.

        `env.meters` is the STATE tensor and stays `[num_agents, meter_count]` — one column
        per meter, unchanged by this cut. What changed is the destination: one 1-wide VFS
        variable per meter instead of a single block variable, because a block cannot carry
        a per-meter normalization kind (hamlet-3d3039f340).

        The meter -> column mapping comes from compiled metadata, never from parsing a field
        name back into a meter name. The observation ORDER comes from the compiled fields.
        Those are the same order by construction (both are environment.yaml declaration
        order), and this asserts it rather than assuming it.
        """
        env = self._env
        meter_fields = [field for field in env.observation_spec.fields if field.semantic_type == "bars"]
        if not meter_fields:
            return

        name_to_column = env.meter_name_to_index
        if tuple(env.meters.shape) != (env.num_agents, len(name_to_column)):
            raise ValueError(
                f"Meter state tensor shape {tuple(env.meters.shape)} does not match "
                f"({env.num_agents}, {len(name_to_column)}) — one column per declared meter."
            )

        meter_values = env.meters.to(device=env.device, dtype=torch.float32)
        for field in meter_fields:
            meter_name = meter_name_from_observation_field(field.name)
            column = name_to_column.get(meter_name)
            if column is None:
                raise ValueError(
                    f"Observation field '{field.name}' names meter '{meter_name}', which has no " "column in the compiled meter metadata."
                )
            if field.name not in env.vfs_registry.variables:
                raise ValueError(f"Observation field '{field.name}' is present but no matching VFS variable exists.")
            # 1-D column view: the SOURCE is a scalar per agent. A widening normalizer
            # (cyclical_sin_cos, one_hot) expands it downstream, at observation build time.
            env.vfs_registry.set(field.name, meter_values[:, column], writer="engine")

    def _sync_affordance_observation_to_vfs(self) -> None:
        """Publish current affordance-at-position observation into VFS state."""
        env = self._env
        for field in env.observation_spec.fields:
            if field.name not in {"obs_affordance_at_position", "obs_affordances"}:
                continue
            if field.name not in env.vfs_registry.variables:
                raise ValueError(f"Observation field '{field.name}' is present but no matching VFS variable exists.")

            affordance = self._build_affordance_encoding(field.dims)
            env.vfs_registry.set(field.name, affordance.to(device=env.device, dtype=torch.float32), writer="engine")

    def _sync_effect_observation_to_vfs(self) -> None:
        """Publish current effect observation into VFS state."""
        env = self._env
        effects_field = next((field for field in env.observation_spec.fields if field.name == "obs_effects"), None)
        if effects_field is None:
            return
        if "obs_effects" not in env.vfs_registry.variables:
            raise ValueError("Observation field 'obs_effects' is present but no matching VFS variable exists.")

        effects = env._build_effects_observation(effects_field.dims)
        self._set_observation_variable("obs_effects", effects, effects_field.dims)

    def _sync_temporal_observation_to_vfs(self) -> None:
        """Publish current temporal observation into VFS state."""
        env = self._env
        temporal_field = next((field for field in env.observation_spec.fields if field.name == "obs_temporal"), None)
        if temporal_field is None:
            return
        if "obs_temporal" not in env.vfs_registry.variables:
            raise ValueError("Observation field 'obs_temporal' is present but no matching VFS variable exists.")

        temporal = self._build_temporal_observation(temporal_field.dims)
        self._set_observation_variable("obs_temporal", temporal, temporal_field.dims)

    def _build_temporal_observation(self, dims: int) -> torch.Tensor:
        """Build the runtime temporal observation vector."""
        env = self._env
        if dims != 4:
            raise ValueError(f"Observation field 'obs_temporal' expected 4 dims, got {dims}.")

        value = torch.zeros((env.num_agents, dims), device=env.device)
        if not env.temporal_support_enabled or not env.enable_temporal_mechanics:
            return value

        time_of_day = env.time_of_day
        day_length = float(env.day_length)
        time_angle = (time_of_day / day_length) * 2 * math.pi
        day_progress = float(time_of_day) / day_length
        night_threshold = day_length * 0.25
        is_before_night_threshold = time_of_day < night_threshold
        is_after_night_threshold = time_of_day >= (day_length - night_threshold)
        if is_before_night_threshold:
            is_night = True
        elif is_after_night_threshold:
            is_night = True
        else:
            is_night = False

        value[:, 0] = math.sin(time_angle)
        value[:, 1] = math.cos(time_angle)
        value[:, 2] = day_progress
        value[:, 3] = float(is_night)
        return value

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
