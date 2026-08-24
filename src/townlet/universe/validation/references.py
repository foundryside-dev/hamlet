"""Symbol registration and reference-resolution passes."""

from __future__ import annotations

from pathlib import Path

from townlet.config.drive_as_code import DriveAsCodeConfig
from townlet.universe.errors import CompilationError, CompilationErrorCollector, CompilationMessage
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

    if raw.vfs_profiles is not None:
        profile_configs = [
            raw.vfs_profiles.global_profile,
            raw.vfs_profiles.agent_profile,
            *(raw.vfs_profiles.item_profiles or []),
        ]
        for profile in profile_configs:
            if profile is None:
                continue
            for variable in getattr(profile, "variables", []) or []:
                _register(table.register_profile_vfs_variable, variable)

    for action in getattr(raw.actions.actions, "custom_actions", []) or []:
        _register(table.register_action, action)

    if raw.items is not None:
        for item in getattr(raw.items, "item_types", []) or []:
            _register(table.register_item, item)

    errors.check_and_raise(stage_label="Stage 2: Symbol Table")
    return table


def validate_dac_references(
    dac_config: DriveAsCodeConfig,
    symbol_table: UniverseSymbolTable,
    errors: CompilationErrorCollector,
) -> None:
    """Validate DAC references to bars, variables, and affordances."""
    for mod_name, mod_config in dac_config.modifiers.items():
        bar_ref = getattr(mod_config, "bar", None)
        variable_ref = getattr(mod_config, "variable", None)
        if bar_ref:
            if bar_ref not in symbol_table.meters:
                errors.add(
                    CompilationMessage(
                        code="DAC-REF-001",
                        message=f"Modifier '{mod_name}' references undefined bar: {bar_ref}",
                        location=f"drive_as_code.yaml:modifiers.{mod_name}",
                    )
                )
        elif variable_ref:
            if variable_ref not in symbol_table.vfs_variables:
                errors.add(
                    CompilationMessage(
                        code="DAC-REF-002",
                        message=f"Modifier '{mod_name}' references undefined VFS variable: {variable_ref}",
                        location=f"drive_as_code.yaml:modifiers.{mod_name}",
                    )
                )

    extrinsic_bars = getattr(dac_config.extrinsic, "bars", None)
    if extrinsic_bars:
        for bar in extrinsic_bars:
            if bar not in symbol_table.meters:
                errors.add(
                    CompilationMessage(
                        code="DAC-REF-003",
                        message=f"Extrinsic strategy references undefined bar: {bar}",
                        location="drive_as_code.yaml:extrinsic.bars",
                    )
                )

    for idx, bonus in enumerate(getattr(dac_config.extrinsic, "bar_bonuses", []) or []):
        bonus_bar = getattr(bonus, "bar", None)
        if bonus_bar and bonus_bar not in symbol_table.meters:
            errors.add(
                CompilationMessage(
                    code="DAC-REF-004",
                    message=f"Extrinsic bar bonus references undefined bar: {bonus_bar}",
                    location=f"drive_as_code.yaml:extrinsic.bar_bonuses[{idx}]",
                )
            )

    for idx, var_bonus in enumerate(getattr(dac_config.extrinsic, "variable_bonuses", []) or []):
        var_ref = getattr(var_bonus, "variable", None)
        if var_ref and var_ref not in symbol_table.vfs_variables:
            errors.add(
                CompilationMessage(
                    code="DAC-REF-005",
                    message=f"Extrinsic variable bonus references undefined VFS variable: {var_ref}",
                    location=f"drive_as_code.yaml:extrinsic.variable_bonuses[{idx}]",
                )
            )

    for idx, shaping in enumerate(dac_config.shaping):
        if shaping.type == "approach_reward":
            target_aff = getattr(shaping, "target_affordance", None) or getattr(shaping, "target", None)
            if target_aff and target_aff not in symbol_table.affordances:
                errors.add(
                    CompilationMessage(
                        code="DAC-REF-006",
                        message=f"Shaping bonus references undefined affordance: {target_aff}",
                        location=f"drive_as_code.yaml:shaping[{idx}]",
                    )
                )
        elif shaping.type == "completion_bonus":
            aff_ref = getattr(shaping, "affordance", None)
            if aff_ref and aff_ref not in symbol_table.affordances:
                errors.add(
                    CompilationMessage(
                        code="DAC-REF-007",
                        message=f"Shaping bonus (completion_bonus) references undefined affordance: {aff_ref}",
                        location=f"drive_as_code.yaml:shaping[{idx}]",
                    )
                )
        elif shaping.type == "streak_bonus":
            aff_ref = getattr(shaping, "affordance", None)
            if aff_ref and aff_ref not in symbol_table.affordances:
                errors.add(
                    CompilationMessage(
                        code="DAC-REF-008",
                        message=f"Shaping bonus (streak_bonus) references undefined affordance: {aff_ref}",
                        location=f"drive_as_code.yaml:shaping[{idx}]",
                    )
                )
        elif shaping.type == "timing_bonus":
            for time_range_idx, time_range in enumerate(shaping.time_ranges):
                aff_ref = getattr(time_range, "affordance", None)
                if aff_ref and aff_ref not in symbol_table.affordances:
                    errors.add(
                        CompilationMessage(
                            code="DAC-REF-009",
                            message=f"Shaping bonus (timing_bonus) references undefined affordance: {aff_ref}",
                            location=f"drive_as_code.yaml:shaping[{idx}].time_ranges[{time_range_idx}]",
                        )
                    )
        elif shaping.type == "efficiency_bonus":
            bar_ref = getattr(shaping, "bar", None)
            if bar_ref and bar_ref not in symbol_table.meters:
                errors.add(
                    CompilationMessage(
                        code="DAC-REF-010",
                        message=f"Shaping bonus (efficiency_bonus) references undefined bar: {bar_ref}",
                        location=f"drive_as_code.yaml:shaping[{idx}]",
                    )
                )
        elif shaping.type == "crisis_avoidance":
            bar_ref = getattr(shaping, "bar", None)
            if bar_ref and bar_ref not in symbol_table.meters:
                errors.add(
                    CompilationMessage(
                        code="DAC-REF-011",
                        message=f"Shaping bonus (crisis_avoidance) references undefined bar: {bar_ref}",
                        location=f"drive_as_code.yaml:shaping[{idx}]",
                    )
                )
        elif shaping.type == "economic_efficiency":
            money_bar = getattr(shaping, "money_bar", None)
            if money_bar and money_bar not in symbol_table.meters:
                errors.add(
                    CompilationMessage(
                        code="DAC-REF-012",
                        message=f"Shaping bonus (economic_efficiency) references undefined bar: {money_bar}",
                        location=f"drive_as_code.yaml:shaping[{idx}]",
                    )
                )
        elif shaping.type == "balance_bonus":
            for bar in getattr(shaping, "bars", []) or []:
                if bar and bar not in symbol_table.meters:
                    errors.add(
                        CompilationMessage(
                            code="DAC-REF-013",
                            message=f"Shaping bonus (balance_bonus) references undefined bar: {bar}",
                            location=f"drive_as_code.yaml:shaping[{idx}]",
                        )
                    )
        elif shaping.type == "state_achievement":
            for condition_idx, condition in enumerate(getattr(shaping, "conditions", []) or []):
                condition_bar = getattr(condition, "bar", None)
                if condition_bar and condition_bar not in symbol_table.meters:
                    errors.add(
                        CompilationMessage(
                            code="DAC-REF-014",
                            message=f"Shaping bonus (state_achievement) references undefined bar: {condition_bar}",
                            location=f"drive_as_code.yaml:shaping[{idx}].conditions[{condition_idx}]",
                        )
                    )
        elif shaping.type == "vfs_variable":
            var_ref = getattr(shaping, "variable", None)
            if var_ref and var_ref not in symbol_table.vfs_variables:
                errors.add(
                    CompilationMessage(
                        code="DAC-REF-015",
                        message=f"Shaping bonus (vfs_variable) references undefined VFS variable: {var_ref}",
                        location=f"drive_as_code.yaml:shaping[{idx}]",
                    )
                )


def resolve_references(
    raw: RawConfigsV21,
    symbol_table: UniverseSymbolTable,
    experiment_dir: Path,
) -> None:
    """Resolve and validate symbolic references between loaded config DTOs."""
    errors = CompilationErrorCollector(stage="Stage 3: Reference Resolution")

    meter_names = set(symbol_table.meters.keys())
    vfs_variable_ids = set(symbol_table.vfs_variables.keys())
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

        for affordance in getattr(level.affordances, "affordances", []) or []:
            for stage_commands in (affordance.interactions or {}).values():
                for cmd in stage_commands:
                    modify_target = getattr(cmd, "modify", None)
                    if isinstance(modify_target, str):
                        vfs_prefixes = ("vfs.", "target.vfs.", "self.vfs.")
                        if modify_target.startswith(vfs_prefixes):
                            var_name = modify_target.split(".")[-1]
                            if var_name not in vfs_variable_ids:
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

    for level in raw.levels.values():
        if getattr(level, "drive", None):
            validate_dac_references(level.drive, symbol_table, errors)

    errors.check_and_raise(stage_label="Stage 3: Reference Resolution")
