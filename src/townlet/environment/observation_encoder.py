"""Observation encoding for :class:`VectorizedHamletEnv`."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, cast

import torch

from townlet.environment.token_publishers import TokenPublishContext, TokenTypePublisher
from townlet.universe.dto import ObservationField
from townlet.universe.dto.observation_feature import VARIABLE_FEATURE
from townlet.universe.dto.token_spec import TokenSpec
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
        """Build one compiled observation field from VFS state.

        Every field is read the SAME way (PDR-0075): the compiled VFS mirror names the
        field's source variable, the registry's declaration of that variable says which
        scope it lives in, and the value is read from that scope and normalized as declared.
        Compiler features (grid, meters, affordances, effects, temporal, item slots) reach here
        too — their sync step has already published them into engine-written registry
        variables — so there is no per-field name branch. This used to special-case a field
        called `obs_vfs` and build it directly from the compiled profile spec, which is the
        name-branch shape PDR-0045 forbids.
        """
        env = self._env
        vfs_field = self._compiled_vfs_observation_field(field_name)
        source_variable = vfs_field.source_variable
        declared = env.vfs_registry.variables.get(source_variable)
        if declared is None:
            raise ValueError(f"Observation field '{field_name}' is not backed by a VFS variable.")

        # SOURCE width, not observed width. The registry is read at the width the variable
        # actually stores; the declared normalizer may then WIDEN it (cyclical_sin_cos -> 2,
        # one_hot -> categories), and `_apply_declared_normalization` below is what checks the
        # result against the field's declared dims.
        source_dims = 1
        for shape_dim in vfs_field.shape:
            source_dims *= shape_dim

        if declared.scope == "global":
            spec = VFSObservationSpec(
                global_vfs_dim=source_dims,
                agent_vfs_dim=0,
                item_vfs_dim=0,
                global_vars=(source_variable,),
                global_active_mask=tuple(True for _ in range(source_dims)),
            )
        elif declared.scope in ("agent", "agent_private"):
            spec = VFSObservationSpec(
                global_vfs_dim=0,
                agent_vfs_dim=source_dims,
                item_vfs_dim=0,
                agent_vars=(source_variable,),
                agent_active_mask=tuple(True for _ in range(source_dims)),
            )
        else:
            raise ValueError(
                "Observation field is backed by a variable in a scope the encoder cannot read directly.\n"
                f"  Field: {field_name}\n"
                f"  Source variable: {source_variable} (scope {declared.scope!r})\n"
                "  Rule: an observation field reads a global or agent variable; other scopes are "
                "observed through a compiler feature (e.g. item slots), never as a bare field."
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
        try:
            normalized = apply_normalization(value, normalization)
        except ValueError as exc:
            # `apply_normalization` is field-agnostic by design, so its messages name the
            # KIND and never the field. At one field that was tolerable; with one field per
            # meter, "one_hot normalization received category index outside configured range"
            # gives an author nothing to act on. Re-raise with the field, so the error points
            # at a line in their environment.yaml.
            raise ValueError(
                f"Declared normalization failed for observation field '{field_name}'.\n"
                f"  Normalization kind: {normalization.kind}\n"
                f"  Underlying error: {exc}"
            ) from exc
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
        """Publish every engine-filled observation feature into VFS state before assembly.

        Dispatch is on the compiled field's declared FEATURE (`townlet.universe.dto.
        observation_feature`), never on its name: the name is the registry variable the value
        is published under — data that flows through — and nothing here compares it to a
        literal. This used to be nine steps each looking a field up by a hardcoded
        `obs_<x>` string, which is the PDR-0045 shape unit 3 removed for `obs_vfs` and this
        unit removes for its siblings. A `variable` field is registry-owned state and is not
        published; a feature this table does not know is a defect, not a skip.
        """
        for field in self._env.observation_spec.fields:
            if field.feature == VARIABLE_FEATURE:
                continue
            publish = self._FEATURE_PUBLISHERS.get(field.feature)
            if publish is None:
                raise ValueError(
                    f"Observation field '{field.name}' declares feature {field.feature!r}, which the "
                    "runtime has no publisher for.\n"
                    "  Rule: every engine-published member of townlet.universe.dto.observation_feature "
                    "has one entry in ObservationEncoder._FEATURE_PUBLISHERS."
                )
            publish(self, field)

    def _require_registry_variable(self, field: ObservationField) -> None:
        env = self._env
        if field.name not in env.vfs_registry.variables:
            raise ValueError(f"Observation field '{field.name}' ({field.feature}) is present but no matching VFS variable exists.")

    def _publish_item_slots(self, field: ObservationField) -> None:
        """The item-slot feature — the exposed item-profile variables of the item in each of
        the agent's slots (PDR-0075) — is present exactly when the compiled VFS observation
        spec has item width."""
        env = self._env
        if env.vfs_observation_spec is None:
            raise ValueError(f"Observation field '{field.name}' (item_slots) is present but no compiled VFS observation spec exists.")
        self._require_registry_variable(field)

        full = env.vfs_observation_spec
        item_spec = VFSObservationSpec(
            global_vfs_dim=0,
            agent_vfs_dim=0,
            item_vfs_dim=full.item_vfs_dim,
            item_profile_vars=full.item_profile_vars,
            item_vars_per_slot=full.item_vars_per_slot,
            item_active_mask=full.item_active_mask,
            max_items_per_agent=full.max_items_per_agent,
            max_item_profiles=full.max_item_profiles,
            max_tensor_elements=full.max_tensor_elements,
        )
        agent_item_inventory = None
        if env.item_inventory is not None:
            agent_item_inventory = env.item_inventory.slots
        item_obs = build_vfs_observation(
            registry=env.vfs_registry,
            spec=item_spec,
            batch_size=env.num_agents,
            agent_item_inventory=agent_item_inventory,
        )
        self._set_observation_variable(field.name, item_obs, field.dims)

    def _publish_grid_encoding(self, field: ObservationField) -> None:
        """The substrate's global grid encoding; zeros while partial observability is active."""
        env = self._env
        self._require_registry_variable(field)
        if env.partial_observability:
            grid_encoding = torch.zeros((env.num_agents, field.dims), device=env.device)
        elif hasattr(env.substrate, "_encode_full_grid"):
            grid_encoding = env.substrate._encode_full_grid(env.positions, env.affordances)
        else:
            grid_encoding = env.substrate.encode_observation(env.positions, env.affordances)
        self._set_observation_variable(field.name, grid_encoding, field.dims)

    def _publish_local_window(self, field: ObservationField) -> None:
        """The substrate's partial-vision window; zeros while full observability is active."""
        env = self._env
        self._require_registry_variable(field)
        if not env.partial_observability:
            local_window = torch.zeros((env.num_agents, field.dims), device=env.device)
        else:
            local_window = env.substrate.encode_partial_observation(
                env.positions,
                env.affordances,
                vision_range=env.vision_radius,
            )
        self._set_observation_variable(field.name, local_window, field.dims)

    def _publish_velocity(self, field: ObservationField) -> None:
        env = self._env
        self._require_registry_variable(field)
        velocity = env._encode_velocity_observation()
        if velocity is None:
            velocity = torch.zeros((env.num_agents, field.dims), device=env.device)
        self._set_observation_variable(field.name, velocity, field.dims)

    def _publish_position(self, field: ObservationField) -> None:
        env = self._env
        self._require_registry_variable(field)
        position = env._encode_position_observation()
        if position is None:
            raise ValueError(f"Observation field '{field.name}' (position) is present but the substrate does not expose position features.")
        self._set_observation_variable(field.name, position, field.dims)

    def _publish_meter(self, field: ObservationField) -> None:
        """Publish one meter's current value into the field's own VFS source variable.

        `env.meters` is the STATE tensor and stays `[num_agents, meter_count]` — one column
        per meter. The destination is one 1-wide VFS variable per meter, because a block
        cannot carry a per-meter normalization kind (hamlet-3d3039f340). Which column is the
        field's `feature_ref` — the meter's name, stamped by the compiler — looked up in the
        compiled meter metadata; nothing parses the meter's name back out of the field's name.
        """
        env = self._env
        name_to_column = env.meter_name_to_index
        if tuple(env.meters.shape) != (env.num_agents, len(name_to_column)):
            raise ValueError(
                f"Meter state tensor shape {tuple(env.meters.shape)} does not match "
                f"({env.num_agents}, {len(name_to_column)}) — one column per declared meter."
            )
        meter_name = field.feature_ref
        if meter_name is None:
            # The DTO refuses a meter field without a referent at construction; this is the
            # runtime restating the invariant it relies on rather than trusting it silently.
            raise ValueError(f"Observation field '{field.name}' is a meter feature but names no meter.")
        column = name_to_column.get(meter_name)
        if column is None:
            raise ValueError(
                f"Observation field '{field.name}' names meter {meter_name!r}, which has no column in the compiled meter metadata."
            )
        self._require_registry_variable(field)
        # 1-D column view: the SOURCE is a scalar per agent. A widening normalizer
        # (cyclical_sin_cos, one_hot) expands it downstream, at observation build time.
        env.vfs_registry.set(field.name, env.meters.to(device=env.device, dtype=torch.float32)[:, column], writer="engine")

    def _publish_affordance_at_position(self, field: ObservationField) -> None:
        env = self._env
        self._require_registry_variable(field)
        affordance = self._build_affordance_encoding(field.dims)
        env.vfs_registry.set(field.name, affordance.to(device=env.device, dtype=torch.float32), writer="engine")

    def _publish_effects(self, field: ObservationField) -> None:
        env = self._env
        self._require_registry_variable(field)
        effects = env._build_effects_observation(field.dims)
        self._set_observation_variable(field.name, effects, field.dims)

    def _publish_temporal(self, field: ObservationField) -> None:
        self._require_registry_variable(field)
        temporal = self._build_temporal_observation(field.dims)
        self._set_observation_variable(field.name, temporal, field.dims)

    # One publisher per engine-published member of the feature vocabulary. `variable` is
    # deliberately absent: the registry owns it. Keyed by the vocabulary's own literals so
    # that adding a member without a publisher fails at the first observation with the rule,
    # not silently.
    _FEATURE_PUBLISHERS: dict[str, Callable[[ObservationEncoder, ObservationField], None]] = {
        "grid_encoding": _publish_grid_encoding,
        "local_window": _publish_local_window,
        "position": _publish_position,
        "velocity": _publish_velocity,
        "meter": _publish_meter,
        "affordance_at_position": _publish_affordance_at_position,
        "effects": _publish_effects,
        "temporal": _publish_temporal,
        "item_slots": _publish_item_slots,
    }

    def _build_temporal_observation(self, dims: int) -> torch.Tensor:
        """Build the runtime temporal observation vector."""
        env = self._env
        if dims != 4:
            raise ValueError(f"Temporal observation feature expected 4 dims, got {dims}.")

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
            raise ValueError(f"Affordance-at-position feature expected {dims} dims, but the affordance encoding produced {total_dims}.")
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


class TokenObservationEncoder:
    """Token-observation assembly (token-obs unit 3, Task 8 — ALONGSIDE the old path).

    Dispatches one publisher per token type (PDR-0076: dispatch on type, never a name
    to match) over the compiled TokenSpec's serialization layout. `variable_element`
    carries TWO publishers — registry-arena and item-arena (spec §3).

    NOT wired into the live step path: `ObservationEncoder._get_observations` above
    remains the environment's observation until the Task-10 swap, which calls
    :meth:`encode` at the existing end-of-step observation point (the one sync point
    after all VTC/effects/evaluator writes of the tick).
    """

    def __init__(self, spec: TokenSpec, publishers: Sequence[TokenTypePublisher], device: torch.device) -> None:
        self._spec = spec
        self._device = device
        self._publishers: dict[str, list[TokenTypePublisher]] = {}
        for publisher in publishers:
            if spec.get_type(publisher.type_name) is None:
                raise ValueError(
                    f"Publisher for token type {publisher.type_name!r} has no type in the compiled TokenSpec "
                    f"(types: {[t.type_name for t in spec.types]})"
                )
            self._publishers.setdefault(publisher.type_name, []).append(publisher)
        for token_type in spec.types:
            if token_type.capacity > 0 and token_type.type_name not in self._publishers:
                raise ValueError(
                    f"Token type {token_type.type_name!r} has capacity {token_type.capacity} but no publisher.\n"
                    "  Rule: one publisher per token type (PDR-0076) — a type with slots and no filler is a "
                    "lying observation, not a skip."
                )
        # Cross-publisher slot disjointness (review Minor-6): where one type carries
        # several publishers (variable_element), their slot sets must be disjoint —
        # an overlapping compiled artifact is a bug that must refuse loudly, never
        # resolve as silent last-writer-wins.
        for type_name, type_publishers in self._publishers.items():
            if len(type_publishers) < 2:
                continue
            claimed_by: dict[int, str] = {}
            overlaps: dict[int, tuple[str, str]] = {}
            for publisher in type_publishers:
                claimed = getattr(publisher, "claimed_slots", None)
                if claimed is None:
                    continue
                name = type(publisher).__name__
                for slot in claimed:
                    if slot in claimed_by:
                        overlaps[slot] = (claimed_by[slot], name)
                    else:
                        claimed_by[slot] = name
            if overlaps:
                detail = "; ".join(f"slot {slot}: {a} and {b}" for slot, (a, b) in sorted(overlaps.items()))
                raise ValueError(
                    f"Token type {type_name!r}: overlapping slot claims across publishers — {detail}.\n"
                    "  Rule: cross-publisher slot sets must be disjoint; an overlapping compiled binding is "
                    "an artifact bug and must be loud, never last-writer-wins."
                )

    def encode(self, batch_size: int, ctx: TokenPublishContext) -> torch.Tensor:
        """Build one tick's token observation, `[batch_size, total_dims]` float32.

        The output tensor is allocated PER TICK (spec §6: stored observations are
        cloned or per-tick allocated — nothing here can alias a previous tick, pinned
        by the replay-aliasing test). Each type's rows are addressed through a
        `.view()` of the flat slice — raises on copy, never `.reshape()`.
        """
        observation = torch.zeros((batch_size, self._spec.total_dims), dtype=torch.float32, device=self._device)
        offset = 0
        for token_type in self._spec.types:
            width = token_type.capacity * token_type.row_width
            if token_type.capacity > 0:
                rows = observation[:, offset : offset + width].view(batch_size, token_type.capacity, token_type.row_width)
                for publisher in self._publishers.get(token_type.type_name, []):
                    publisher.publish(rows, ctx)
            offset += width
        return observation
