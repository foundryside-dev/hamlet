"""Action-domain compiler boundary."""

from __future__ import annotations

import torch

from townlet.config.actions_config import ActionsConfig
from townlet.config.affordances_v2_config import AffordancesV2Config
from townlet.config.items_config import ItemsCatalogConfig, build_item_command_action_name
from townlet.config.stratum_config import StratumConfig
from townlet.config.training_v2_config import TrainingV2Config
from townlet.environment.action_config import ActionConfig
from townlet.environment.action_labels import PRESET_LABELS, CanonicalAction
from townlet.substrate.factory import SubstrateFactory
from townlet.universe.dto import ActionMetadata, ActionSpaceMetadata, RuntimeAction, RuntimeActionSpace


class ActionCompiler:
    """Compile runtime action metadata."""

    def build_action_space_metadata(
        self,
        stratum: StratumConfig,
        actions: ActionsConfig,
        training: TrainingV2Config,
        affordances: AffordancesV2Config,
        items: ItemsCatalogConfig | None,
        action_label_overrides: dict[int, str] | None,
    ) -> ActionSpaceMetadata:
        """Build action space metadata using substrate actions + custom actions."""
        entries: list[ActionMetadata] = []
        next_id = 0

        def _add(
            name: str,
            action_type: str,
            source: str,
            enabled: bool,
            movement_delta: tuple[float, ...] | None = None,
            description: str = "",
            source_affordance: str | None = None,
            writes: tuple[dict, ...] = (),
        ) -> None:
            nonlocal next_id
            entries.append(
                ActionMetadata(
                    id=next_id,
                    name=name,
                    type=action_type,  # type: ignore[arg-type]
                    enabled=enabled,
                    source=source,  # type: ignore[arg-type]
                    costs={},
                    description=description,
                    movement_delta=movement_delta,
                    source_affordance=source_affordance,
                    writes=writes,
                )
            )
            next_id += 1

        substrate_actions_cfg = actions.actions.substrate_actions
        allow_interact = len(affordances.affordances) > 0
        substrate_actions: list[ActionConfig] = []
        substrate_names: set[str] = set()

        allowed_names_raw = training.enabled_actions.custom if training.enabled_actions else None
        custom_action_names = {custom.name for custom in actions.actions.custom_actions}
        apply_global_filter = False
        if allowed_names_raw is not None:
            apply_global_filter = any(name not in custom_action_names for name in allowed_names_raw)
        allowed_names = set(allowed_names_raw) if allowed_names_raw is not None else None

        if substrate_actions_cfg.inherit:
            substrate = SubstrateFactory.build(stratum.stratum.substrate, torch.device("cpu"))
            substrate_actions = substrate.get_default_actions()
            substrate_names = {a.name for a in substrate_actions}
            for action in substrate_actions:
                enabled = True
                if apply_global_filter and allowed_names is not None:
                    enabled = action.name in allowed_names
                if action.name == "INTERACT" and not allow_interact:
                    enabled = False
                movement_delta: tuple[float, ...] | None = None
                if action.type == "movement" and action.delta is not None:
                    movement_delta = tuple(float(d) for d in action.delta)
                _add(
                    action.name,
                    action.type,
                    "substrate",
                    enabled,
                    movement_delta=movement_delta,
                    description=action.description or "",
                )

        reserved_names: set[str] = {"INTERACT"}
        if items is not None:
            reserved_names.add("GET")
            for slot_idx in range(items.max_items_per_agent):
                reserved_names.add(f"USE_SLOT_{slot_idx}")
                reserved_names.add(f"DROP_SLOT_{slot_idx}")
            for item in items.item_types:
                for item_cmd in item.interactions.local_commands:
                    reserved_names.add(build_item_command_action_name(item.id, item_cmd.name, "local"))
                for item_cmd in item.interactions.inventory_commands:
                    reserved_names.add(build_item_command_action_name(item.id, item_cmd.name, "inventory"))

        enabled_custom = set(allowed_names) if allowed_names is not None else set()
        for custom in actions.actions.custom_actions:
            if custom.name in reserved_names:
                raise ValueError(f"Action name '{custom.name}' is reserved for system actions and cannot be overridden")
            if custom.name in substrate_names:
                continue
            action_type = "passive" if custom.name == "WAIT" else "interaction"
            if apply_global_filter and allowed_names is not None:
                enabled = custom.name in allowed_names
            else:
                enabled = custom.enabled_by_default or custom.name in enabled_custom
            _add(
                custom.name,
                action_type,
                "custom",
                enabled,
                description=custom.description or "",
                source_affordance=custom.source_affordance,
                writes=tuple(write.model_dump() for write in custom.writes),
            )

        if items is not None and items.max_items_per_agent > 0 and items.max_items_in_world > 0:
            get_enabled = True
            if apply_global_filter and allowed_names is not None:
                get_enabled = "GET" in allowed_names
            _add("GET", "interaction", "item", get_enabled)
            for slot_idx in range(items.max_items_per_agent):
                use_enabled = True
                drop_enabled = True
                if apply_global_filter and allowed_names is not None:
                    use_enabled = f"USE_SLOT_{slot_idx}" in allowed_names
                    drop_enabled = f"DROP_SLOT_{slot_idx}" in allowed_names
                _add(f"USE_SLOT_{slot_idx}", "interaction", "item", use_enabled)
                _add(f"DROP_SLOT_{slot_idx}", "interaction", "item", drop_enabled)
            for item in items.item_types:
                for item_cmd in item.interactions.local_commands:
                    name = build_item_command_action_name(item.id, item_cmd.name, "local")
                    enabled = True
                    if apply_global_filter and allowed_names is not None:
                        enabled = name in allowed_names
                    _add(name, "interaction", "item", enabled)
                for item_cmd in item.interactions.inventory_commands:
                    name = build_item_command_action_name(item.id, item_cmd.name, "inventory")
                    enabled = True
                    if apply_global_filter and allowed_names is not None:
                        enabled = name in allowed_names
                    _add(name, "interaction", "item", enabled)

        label_config = actions.actions.labels
        label_preset = label_config.preset

        preset_label_map: dict[str, str] = {}
        if label_preset and label_preset in PRESET_LABELS:
            preset_labels_obj = PRESET_LABELS[label_preset]
            for canonical_idx, label in preset_labels_obj.labels.items():
                canonical_name = CanonicalAction(canonical_idx).name
                if canonical_name == "MOVE_X_NEGATIVE":
                    preset_label_map["LEFT"] = label
                elif canonical_name == "MOVE_X_POSITIVE":
                    preset_label_map["RIGHT"] = label
                elif canonical_name == "MOVE_Y_NEGATIVE":
                    preset_label_map["DOWN"] = label
                elif canonical_name == "MOVE_Y_POSITIVE":
                    preset_label_map["UP"] = label
                elif canonical_name == "MOVE_Z_POSITIVE":
                    preset_label_map["FORWARD"] = label
                elif canonical_name == "MOVE_Z_NEGATIVE":
                    preset_label_map["BACKWARD"] = label
                elif canonical_name == "INTERACT":
                    preset_label_map["INTERACT"] = label
                elif canonical_name == "WAIT":
                    preset_label_map["WAIT"] = label

        complete_labels: dict[int, str] = {}
        label_description = PRESET_LABELS[label_preset].description if label_preset and label_preset in PRESET_LABELS else "Custom labels"
        label_domain = PRESET_LABELS[label_preset].domain if label_preset and label_preset in PRESET_LABELS else "custom"

        for entry in entries:
            if action_label_overrides and entry.id in action_label_overrides:
                complete_labels[entry.id] = action_label_overrides[entry.id]
            elif entry.name in preset_label_map:
                complete_labels[entry.id] = preset_label_map[entry.name]
            else:
                complete_labels[entry.id] = entry.name

        return ActionSpaceMetadata(
            total_actions=len(entries),
            actions=tuple(entries),
            labels=complete_labels,
            label_description=label_description,
            label_domain=label_domain,
        )

    def build_runtime_action_space(self, action_metadata: ActionSpaceMetadata) -> RuntimeActionSpace:
        """Build the runtime action-space artifact from compiled metadata."""
        runtime_actions = tuple(
            RuntimeAction(
                id=action.id,
                name=action.name,
                type=action.type,
                enabled=action.enabled,
                source=action.source,
                costs=dict(action.costs),
                effects={},
                delta=action.movement_delta,
                teleport_to=None,
                description=action.description or None,
                icon=None,
                source_affordance=action.source_affordance,
                reads=(),
                writes=action.writes,
            )
            for action in sorted(action_metadata.actions, key=lambda entry: entry.id)
        )
        substrate_action_count = sum(1 for action in runtime_actions if action.source == "substrate")
        return RuntimeActionSpace(
            actions=runtime_actions,
            substrate_action_count=substrate_action_count,
            custom_action_count=len(runtime_actions) - substrate_action_count,
            affordance_action_count=0,
            enabled_action_names=None,
        )
