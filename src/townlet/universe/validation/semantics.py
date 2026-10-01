"""Strict semantic helpers for v2.1 universe compilation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from townlet.environment.substrate_action_validator import SubstrateActionValidator
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationErrorCollector
from townlet.universe.raw_configs_v21 import RawConfigsV21
from townlet.universe.source_map import SourceMap, locate
from townlet.universe.stages import CompilationStage
from townlet.universe.validation.feasibility import grid_capacity_for_substrate


def select_primary_level(levels: Mapping[str, Any], requested: str | None) -> str:
    """Resolve the primary level, rejecting unknown explicit names."""
    if requested is None:
        raise ValueError("select_primary_level requires an explicit primary_level; implicit level selection is not allowed.")
    if requested not in levels:
        raise ValueError(f"Primary level '{requested}' not found. Available: {list(levels.keys())}")
    return requested


def _detect_cycles(graph: Mapping[str, Iterable[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    visited: set[str] = set()
    stack: set[str] = set()

    def dfs(node: str, path: list[str]) -> None:
        visited.add(node)
        stack.add(node)
        path.append(node)
        if node in graph:
            neighbors = graph[node]
        else:
            neighbors = ()
        for neighbor in neighbors:
            if neighbor not in visited:
                dfs(neighbor, path.copy())
            elif neighbor in stack:
                try:
                    start = path.index(neighbor)
                    cycles.append(path[start:])
                except ValueError:
                    cycles.append([neighbor])
        stack.remove(node)

    for node in graph:
        if node not in visited:
            dfs(node, [])

    return cycles


def validate_v21_semantics(raw: RawConfigsV21, experiment_dir: Path, source_map: SourceMap | None) -> None:
    """Validate v2.1 semantic constraints after typed config loading.

    ``source_map`` upgrades declaration identities to their actual file:line
    origins. Filesystem discovery and scope validation belong to the frontend.
    """
    errors = CompilationErrorCollector(stage=CompilationStage.SEMANTICS.label)

    temporal_supported = raw.stratum.stratum.temporal_support == "enabled"
    for level_name, level in raw.levels.items():
        day_length = level.curriculum.curriculum.day_length
        if temporal_supported and level.curriculum.curriculum.active_temporal:
            if day_length is None or day_length <= 0:
                errors.add(
                    "curriculum.day_length must be >0 when temporal_support is enabled and active_temporal=true.",
                    code=ErrorCode.TEMPORAL_DAY_LENGTH_MISSING,
                    location=locate(
                        source_map, f"levels/{level_name}/curriculum", str(experiment_dir / "levels" / level_name / "curriculum")
                    ),
                )

    # A multi_tick affordance needs a tick schedule to progress through. Without
    # active temporal mechanics its interaction can be started and never completes,
    # which is a config error the compiler should refuse rather than a runtime
    # behaviour to debug. The closed vocabulary has no hybrid fallback: every
    # multi_tick declaration requires active temporal mechanics.
    for level_name, level in raw.levels.items():
        temporal_active = temporal_supported and level.curriculum.curriculum.active_temporal
        if temporal_active:
            continue
        for affordance in level.affordances.affordances:
            if affordance.interaction_type == "multi_tick":
                errors.add(
                    (
                        f"Affordance '{affordance.name}' is interaction_type: multi_tick, but level "
                        f"'{level_name}' has no active temporal mechanics "
                        "(stratum.temporal_support='enabled' and curriculum.active_temporal=true). "
                        "A multi-tick interaction cannot progress without a tick schedule."
                    ),
                    code=ErrorCode.MULTI_TICK_REQUIRES_TEMPORAL,
                    location=locate(
                        source_map,
                        f"levels/{level_name}/affordances:{affordance.name}",
                        str(experiment_dir / "levels" / level_name / "affordances"),
                    ),
                )

    vision_support = raw.stratum.stratum.vision_support
    for level_name, level in raw.levels.items():
        active = level.curriculum.curriculum.active_vision
        if active in {"local", "partial"}:
            active_canon = "partial"
        else:
            active_canon = "global"
        if active_canon == "global" and vision_support not in {"global", "both"}:
            errors.add(
                "Invalid vision configuration: curriculum.active_vision='global' requires stratum.vision_support in ['global','both'].",
                code=ErrorCode.VISION_INCOMPATIBLE,
                location=locate(source_map, f"levels/{level_name}/curriculum", str(experiment_dir / "levels" / level_name / "curriculum")),
            )
        if active_canon == "partial" and vision_support not in {"partial", "both"}:
            errors.add(
                (
                    "Invalid vision configuration: curriculum.active_vision=partial/local "
                    "requires stratum.vision_support in ['partial','both']."
                ),
                code=ErrorCode.VISION_INCOMPATIBLE,
                location=locate(source_map, f"levels/{level_name}/curriculum", str(experiment_dir / "levels" / level_name / "curriculum")),
            )

    substrate = raw.stratum.stratum.substrate

    validator = SubstrateActionValidator(substrate, raw.actions)
    validation_result = validator.validate()
    for err in validation_result.errors:
        errors.add(
            err,
            code=ErrorCode.SUBSTRATE_ACTION_INCOMPATIBLE,
            location=locate(source_map, "actions", str(experiment_dir / "actions")),
        )
    for warn in validation_result.warnings:
        errors.add(
            warn,
            code=ErrorCode.SUBSTRATE_ACTION_WARNING_AS_ERROR,
            location=locate(source_map, "actions", str(experiment_dir / "actions")),
        )

    if substrate.type in {"continuous", "continuousnd"}:
        continuous_cfg = getattr(substrate, "continuous", None)
        if continuous_cfg is None or getattr(continuous_cfg, "interaction_radius", None) is None:
            errors.add(
                "Continuous substrates require an explicit interaction_radius; no defaults are applied.",
                code=ErrorCode.INTERACTION_RADIUS_MISSING,
                location=locate(source_map, "stratum", str(experiment_dir / "stratum")),
            )

    environment_location = locate(source_map, "environment", str(experiment_dir / "environment"))
    env_meter_names = {m.name for m in raw.environment.environment.meters}
    env_affordance_names = {a.name for a in raw.environment.environment.affordances}
    env_mod_pairs = {(m.bar, tuple(sorted(m.affordances))) for m in raw.environment.environment.modulation_graph}
    env_edges = {(c.source, c.target) for c in raw.environment.environment.cascade_graph}

    for mod in raw.environment.environment.modulation_graph:
        invalid_affordances = [name for name in mod.affordances if name not in env_affordance_names]
        if mod.bar not in env_meter_names or invalid_affordances:
            errors.add(
                (
                    "environment modulation_graph references unknown bars or affordances: "
                    f"bar={mod.bar}, affordances={sorted(mod.affordances)}"
                ),
                code=ErrorCode.MODULATION_INVALID_REFERENCE,
                location=locate(source_map, "environment", str(experiment_dir / "environment")),
            )

    for edge in env_edges:
        if edge[0] not in env_meter_names or edge[1] not in env_meter_names:
            errors.add(
                f"environment cascade_graph references unknown meters: {edge}",
                code=ErrorCode.CASCADE_INVALID_METER,
                location=locate(source_map, "environment", str(experiment_dir / "environment")),
            )

    cascade_graph: dict[str, list[str]] = {}
    for edge_source, edge_target in env_edges:
        if edge_source not in cascade_graph:
            cascade_graph[edge_source] = []
        cascade_graph[edge_source].append(edge_target)
    for cycle in _detect_cycles(cascade_graph):
        formatted = " -> ".join(cycle + [cycle[0]])
        errors.add(
            f"environment cascade_graph contains circular cascade: {formatted}",
            code=ErrorCode.CASCADE_CYCLE,
            location=locate(source_map, "environment", str(experiment_dir / "environment")),
        )

    grid_capacity = grid_capacity_for_substrate(substrate)

    for level_name, level in raw.levels.items():
        level_dir = experiment_dir / "levels" / level_name

        level_meter_names = {meter.name for meter in level.bars.meters}
        level_affordance_names = {aff.name for aff in level.affordances.affordances}

        if level_meter_names != env_meter_names:
            missing = env_meter_names - level_meter_names
            extra = level_meter_names - env_meter_names
            errors.add(
                f"Meter vocabulary mismatch with environment declaration at {environment_location}.",
                code=ErrorCode.METER_VOCAB_MISMATCH,
                location=locate(source_map, f"levels/{level_name}/bars", str(level_dir / "bars")),
            )
            if missing:
                errors.add_hint(f"Missing meters: {sorted(missing)}")
            if extra:
                errors.add_hint(f"Unexpected meters: {sorted(extra)}")

        if level_affordance_names != env_affordance_names:
            missing = env_affordance_names - level_affordance_names
            extra = level_affordance_names - env_affordance_names
            errors.add(
                f"Affordance vocabulary mismatch with environment declaration at {environment_location}.",
                code=ErrorCode.AFFORDANCE_VOCAB_MISMATCH,
                location=locate(source_map, f"levels/{level_name}/affordances", str(level_dir / "affordances")),
            )
            if missing:
                errors.add_hint(f"Missing affordances: {sorted(missing)}")
            if extra:
                errors.add_hint(f"Unexpected affordances: {sorted(extra)}")

        level_edges = {(c.source, c.target) for c in level.bars.cascades}
        missing_edges = env_edges - level_edges
        extra_edges = level_edges - env_edges
        if missing_edges:
            errors.add(
                f"Missing cascades (must match environment cascade_graph at {environment_location}): {sorted(missing_edges)}",
                code=ErrorCode.CASCADE_MISSING,
                location=locate(source_map, f"levels/{level_name}/bars", str(level_dir / "bars")),
            )
        if extra_edges:
            errors.add(
                f"Extra cascades not declared in environment cascade_graph at {environment_location}: {sorted(extra_edges)}",
                code=ErrorCode.CASCADE_EXTRA,
                location=locate(source_map, f"levels/{level_name}/bars", str(level_dir / "bars")),
            )

        level_mod_pairs = {(m.bar, tuple(sorted(m.affordances))) for m in level.affordances.modulations}
        missing_mods = env_mod_pairs - level_mod_pairs
        extra_mods = level_mod_pairs - env_mod_pairs
        if missing_mods:
            errors.add(
                f"Missing modulations (must match environment modulation_graph at {environment_location}): {sorted(missing_mods)}",
                code=ErrorCode.MODULATION_MISSING,
                location=locate(source_map, f"levels/{level_name}/affordances", str(level_dir / "affordances")),
            )
        if extra_mods:
            errors.add(
                f"Extra modulations not declared in environment modulation_graph at {environment_location}: {sorted(extra_mods)}",
                code=ErrorCode.MODULATION_EXTRA,
                location=locate(source_map, f"levels/{level_name}/affordances", str(level_dir / "affordances")),
            )

        for aff in level.affordances.affordances:
            if getattr(aff, "opening_hours", None) is None:
                errors.add(
                    f"Affordance '{aff.name}' missing opening_hours.",
                    code=ErrorCode.AFFORDANCE_OPENING_HOURS_MISSING,
                    location=locate(source_map, f"levels/{level_name}/affordances:{aff.name}", str(level_dir / "affordances")),
                )
            deployment = getattr(aff, "deployment", None)
            if deployment is not None and getattr(deployment, "type", None) == "fixed" and not deployment.positions:
                errors.add(
                    f"Affordance '{aff.name}' has deployment.type='fixed' but no positions specified.",
                    code=ErrorCode.AFFORDANCE_DEPLOYMENT_POSITIONS_MISSING,
                    location=locate(source_map, f"levels/{level_name}/affordances:{aff.name}", str(level_dir / "affordances")),
                )
            invalid_cost_meters = [name for name in aff.costs.keys() if name not in env_meter_names]

            invalid_interaction_meters = []
            for stage_commands in aff.interactions.values():
                for cmd in stage_commands:
                    modify = getattr(cmd, "modify", None)
                    if isinstance(modify, str) and modify.startswith("target.bar."):
                        meter_name = modify.split(".")[-1]
                        if meter_name not in env_meter_names:
                            invalid_interaction_meters.append(meter_name)

            if invalid_cost_meters or invalid_interaction_meters:
                errors.add(
                    f"Affordance '{aff.name}' references unknown meters in costs/interactions.",
                    code=ErrorCode.AFFORDANCE_INVALID_METER,
                    location=locate(source_map, f"levels/{level_name}/affordances:{aff.name}", str(level_dir / "affordances")),
                )

        normalized_enabled = set(level.training.enabled_affordances)
        invalid_enabled = normalized_enabled - env_affordance_names
        if invalid_enabled:
            errors.add(
                f"Invalid enabled_affordances in training: unknown entries {sorted(invalid_enabled)}",
                code=ErrorCode.ENABLED_AFFORDANCES_INVALID,
                location=locate(source_map, f"levels/{level_name}/training", str(level_dir / "training")),
            )

        if grid_capacity is not None:
            deployed_count = len(normalized_enabled)
            population_size = level.training.population.size
            required_slots = deployed_count + population_size
            if required_slots > grid_capacity:
                errors.add(
                    f"Grid capacity exceeded: {required_slots} entities (agents + affordances) vs grid capacity {grid_capacity}.",
                    code=ErrorCode.GRID_CAPACITY_EXCEEDED,
                    location=locate(source_map, f"levels/{level_name}/training", str(level_dir / "training")),
                )

    for level_name, level in raw.levels.items():
        level_path = experiment_dir / "levels" / level_name / "drive"
        drive = getattr(level, "drive", None)

        if drive is None:
            errors.add(
                f"drive is required for level {level_name}.",
                code=ErrorCode.LEVEL_DRIVE_MISSING,
                location=locate(source_map, f"levels/{level_name}/drive", str(level_path)),
            )
            continue

        if getattr(drive, "extrinsic", None) is None:
            errors.add(
                f"drive.extrinsic is required for level {level_name}.",
                code=ErrorCode.LEVEL_DRIVE_EXTRINSIC_MISSING,
                location=locate(source_map, f"levels/{level_name}/drive", str(level_path)),
            )

        if getattr(drive, "intrinsic", None) is None:
            errors.add(
                f"drive.intrinsic is required for level {level_name}.",
                code=ErrorCode.LEVEL_DRIVE_INTRINSIC_MISSING,
                location=locate(source_map, f"levels/{level_name}/drive", str(level_path)),
            )

    errors.check_and_raise()
