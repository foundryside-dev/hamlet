"""Compiler safety limits for config-pack validation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from townlet.universe.errors import CompilationErrorCollector
from townlet.universe.stages import CompilationStage
from townlet.universe.validation.feasibility import grid_capacity_for_substrate

if TYPE_CHECKING:
    from townlet.universe.raw_configs_v21 import RawConfigsV21

MAX_METERS = 100
MAX_AFFORDANCES = 100
MAX_CASCADES = 500
MAX_ACTIONS = 300
MAX_VARIABLES = 200
MAX_GRID_CELLS = 10_000
MAX_CACHE_FILE_SIZE = 10 * 1024 * 1024
EFFECT_OBSERVATION_SLOTS = 8
MAX_ITEM_TYPES = 200
MAX_VFS_PROFILES = 200
MAX_SPAWN_RULES_PER_ITEM = 200


def validate_v21_limits(raw: RawConfigsV21, experiment_dir: Path) -> None:
    """Validate hard config-pack size and resource limits over loaded DTOs."""
    errors = CompilationErrorCollector(stage=CompilationStage.LIMITS.label)
    experiment_dir = Path(experiment_dir)

    env_meter_names = {meter.name for meter in raw.environment.environment.meters}
    env_affordance_names = {aff.name for aff in raw.environment.environment.affordances}
    env_cascades = raw.environment.environment.cascade_graph
    env_variables = raw.environment.environment.variables

    checks = [
        (len(env_meter_names), MAX_METERS, "environment.yaml", "meters"),
        (len(env_affordance_names), MAX_AFFORDANCES, "environment.yaml", "affordances"),
        (len(env_cascades), MAX_CASCADES, "environment.yaml", "cascade_graph"),
        (len(raw.actions.actions.custom_actions), MAX_ACTIONS, "actions.yaml", "actions"),
        (len(env_variables), MAX_VARIABLES, "environment.yaml", "variables"),
    ]

    for count, limit, filename, label in checks:
        if count > limit:
            errors.add(
                (
                    f"Too many {label}: found {count} (max {limit}). "
                    "This may indicate config injection, duplication, or an unsafe configuration size."
                ),
                code="CONFIG_LIMIT_EXCEEDED",
                location=str(experiment_dir / filename),
            )

    if raw.items is not None:
        item_count = len(raw.items.item_types)
        if item_count > MAX_ITEM_TYPES:
            errors.add(
                f"items.yaml item_types exceeds safety limit for v2.1 configs: found {item_count} (max {MAX_ITEM_TYPES}).",
                code="ITEM_TYPES_LIMIT_EXCEEDED",
                location=str(experiment_dir / "items.yaml"),
            )

    grid_capacity = grid_capacity_for_substrate(raw.stratum.stratum.substrate)
    if grid_capacity is not None and grid_capacity > MAX_GRID_CELLS:
        errors.add(
            f"Substrate grid size exceeds safety limit for v2.1 configs: {grid_capacity} cells (max {MAX_GRID_CELLS}).",
            code="GRID_SIZE_LIMIT_EXCEEDED",
            location=str(experiment_dir / "stratum.yaml"),
        )

    for level_name, level in raw.levels.items():
        if level.items_appearance is None:
            continue

        per_item_rule_counts: dict[str, int] = {}
        for rule in level.items_appearance.items:
            per_item_rule_counts[rule.item_type] = per_item_rule_counts.get(rule.item_type, 0) + 1
            if per_item_rule_counts[rule.item_type] > MAX_SPAWN_RULES_PER_ITEM:
                errors.add(
                    (
                        "items.yaml spawn rules exceed safety limit for a single item type: "
                        f"{rule.item_type} has {per_item_rule_counts[rule.item_type]} rules "
                        f"(max {MAX_SPAWN_RULES_PER_ITEM})."
                    ),
                    code="SPAWN_RULE_LIMIT_EXCEEDED",
                    location=str(experiment_dir / "levels" / level_name / "items.yaml"),
                )

    errors.check_and_raise()
