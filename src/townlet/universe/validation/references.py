"""Symbol registration and reference-resolution passes."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from townlet.config.drive_as_code import DriveAsCodeConfig
from townlet.universe.errors import CompilationError, CompilationErrorCollector, CompilationMessage
from townlet.universe.pipeline import ResolvedConfigBundle
from townlet.universe.raw_configs_v21 import RawConfigsV21
from townlet.universe.symbol_table import UniverseSymbolTable


def build_symbol_table(raw: RawConfigsV21) -> UniverseSymbolTable:
    """Collect all named v2.1 entities into a symbol table."""
    errors = CompilationErrorCollector(stage="Stage 2: Symbol Table")
    table = UniverseSymbolTable()

    def _register(register_fn, payload) -> None:
        try:
            register_fn(payload)
        except CompilationError as exc:
            errors.extend(exc.issues)

    env = raw.environment.environment
    for meter in getattr(env, "meters", []) or []:
        _register(table.register_meter, meter)

    for cascade in getattr(env, "cascade_graph", []) or []:
        _register(table.register_cascade, cascade)

    for affordance in getattr(env, "affordances", []) or []:
        _register(table.register_affordance, affordance)

    for variable in getattr(env, "variables", []) or []:
        _register(table.register_variable, variable)

    for action in getattr(raw.actions.actions, "custom_actions", []) or []:
        _register(table.register_action, action)

    if raw.items is not None:
        for item in getattr(raw.items, "item_types", []) or []:
            _register(table.register_item, item)

    errors.check_and_raise(stage_label="Stage 2: Symbol Table")
    return table


def resolve_references(
    raw: RawConfigsV21,
    symbol_table: UniverseSymbolTable,
    experiment_dir: Path,
    *,
    validate_dac_references: Callable[[DriveAsCodeConfig, UniverseSymbolTable, CompilationErrorCollector], None] | None = None,
) -> ResolvedConfigBundle:
    """Resolve and validate symbolic references between loaded config DTOs."""
    errors = CompilationErrorCollector(stage="Stage 3: Reference Resolution")

    meter_names = set(symbol_table.meters.keys())
    affordance_names = set(symbol_table.affordances_by_name.keys())
    variable_ids = set(symbol_table.variables.keys())
    item_ids = set(symbol_table.items.keys())

    for level_name, level in raw.levels.items():
        level_dir = experiment_dir / "levels" / level_name

        for cascade in getattr(level.bars, "cascades", []) or []:
            if cascade.source not in meter_names:
                errors.add(
                    CompilationMessage(
                        code="UAC-RES-CASCADE",
                        message=f"Cascade references unknown source meter '{cascade.source}'.",
                        location=str(level_dir / "bars.yaml"),
                    )
                )
            if cascade.target not in meter_names:
                errors.add(
                    CompilationMessage(
                        code="UAC-RES-CASCADE",
                        message=f"Cascade references unknown target meter '{cascade.target}'.",
                        location=str(level_dir / "bars.yaml"),
                    )
                )

        enabled_affordances = getattr(level.training, "enabled_affordances", None)
        if enabled_affordances is not None:
            requested = {str(name) for name in enabled_affordances}
            unknown = requested - affordance_names
            if unknown:
                errors.add(
                    CompilationMessage(
                        code="UAC-RES-AFF",
                        message=f"training.enabled_affordances contains unknown entries: {sorted(unknown)}",
                        location=str(level_dir / "training.yaml"),
                    )
                )

        for affordance in getattr(level.affordances, "affordances", []) or []:
            invalid_costs = [meter for meter in affordance.costs.keys() if meter not in meter_names]
            if invalid_costs:
                errors.add(
                    CompilationMessage(
                        code="UAC-RES-AFF",
                        message=f"Affordance '{affordance.name}' references unknown meters in costs: {sorted(invalid_costs)}",
                        location=str(level_dir / "affordances.yaml"),
                    )
                )

            for stage_commands in (affordance.interactions or {}).values():
                for cmd in stage_commands:
                    modify_target = getattr(cmd, "modify", None)
                    if isinstance(modify_target, str) and modify_target.startswith("target.bar."):
                        meter_name = modify_target.split(".")[-1]
                        if meter_name not in meter_names:
                            errors.add(
                                CompilationMessage(
                                    code="UAC-RES-AFF",
                                    message=f"Affordance '{affordance.name}' interaction references unknown meter '{meter_name}'.",
                                    location=str(level_dir / "affordances.yaml"),
                                )
                            )
                    if isinstance(modify_target, str):
                        vfs_prefixes = ("vfs.", "target.vfs.", "self.vfs.")
                        if modify_target.startswith(vfs_prefixes):
                            var_name = modify_target.split(".")[-1]
                            if var_name not in variable_ids:
                                errors.add(
                                    CompilationMessage(
                                        code="UAC-RES-VFS",
                                        message=f"Affordance '{affordance.name}' interaction uses unknown VFS variable '{var_name}'.",
                                        location=str(level_dir / "affordances.yaml"),
                                    )
                                )

        if level.items_appearance is not None:
            for rule in level.items_appearance.items:
                if rule.item_type not in item_ids:
                    errors.add(
                        CompilationMessage(
                            code="UAC-RES-ITEM",
                            message=f"Item appearance references unknown item_type '{rule.item_type}'.",
                            location=str(level_dir / "items.yaml"),
                        )
                    )

    if validate_dac_references is not None:
        for level in raw.levels.values():
            if getattr(level, "drive", None):
                validate_dac_references(level.drive, symbol_table, errors)

    errors.check_and_raise(stage_label="Stage 3: Reference Resolution")
    return ResolvedConfigBundle(raw=raw, symbol_table=symbol_table)
