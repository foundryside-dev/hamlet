"""Strict semantic helpers for v2.1 universe compilation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import fields
from pathlib import Path
from typing import Any

from townlet.environment.substrate_action_validator import SubstrateActionValidator
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationErrorCollector
from townlet.universe.raw_configs_v21 import RawConfigsV21
from townlet.universe.source_map import SourceMap, locate
from townlet.universe.stages import CompilationStage
from townlet.universe.validation.feasibility import grid_capacity_for_substrate
from townlet.world.expression import ASTNode, Constant, FunctionCall, OperatorType, UnaryOp, Variable
from townlet.world.expression.functions import FUNCTION_SPECS, REQUIRES_POSITIONS
from townlet.world.expression.parser import ExpressionParser


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


def grid_axis_sizes(substrate: Any) -> tuple[int, ...] | None:
    """Per-axis cell counts of a discrete grid substrate config; None for any other substrate."""
    if substrate.type == "grid" and substrate.grid is not None:
        grid = substrate.grid
        return (grid.width, grid.height) if grid.depth is None else (grid.width, grid.height, grid.depth)
    if substrate.type == "gridnd" and substrate.gridnd is not None:
        return tuple(int(size) for size in substrate.gridnd.dimension_sizes)
    return None


def _validate_item_placements(
    raw: RawConfigsV21,
    experiment_dir: Path,
    source_map: SourceMap | None,
    errors: CompilationErrorCollector,
) -> None:
    """Item placement modes against the substrate they place on.

    `random` asks the substrate's own position initialization and works everywhere.
    `fixed`, `grid` and `scripted` name grid cells, so they need a discrete grid (any
    rank), and every authored cell must have the grid's rank and lie inside it.
    """
    substrate = raw.stratum.stratum.substrate
    axes = grid_axis_sizes(substrate)
    for level_name, level in raw.levels.items():
        if level.items_appearance is None:
            continue
        declaration = f"levels/{level_name}/items_appearance"
        location = locate(source_map, declaration, str(experiment_dir / "levels" / level_name / "items_appearance"))
        for rule in level.items_appearance.items:
            placement = rule.placement
            if placement is None or placement.mode == "random":
                continue
            if axes is None:
                errors.add(
                    f"Item '{rule.item_type}' uses placement mode '{placement.mode}', which names grid cells, but the "
                    f"substrate is '{substrate.type}'. Use placement mode 'random' (the substrate's own position "
                    "initialization) or a grid substrate.",
                    code=ErrorCode.ITEM_PLACEMENT_SUBSTRATE,
                    location=location,
                )
                continue
            cells: list[tuple[Any, ...]] = []
            if placement.mode == "fixed":
                cells = [tuple(cell) for cell in placement.fixed_positions or []]
            elif placement.mode == "scripted":
                # An event without a position list has no cell (rank 0) and refuses below.
                positions = [event.get("position") for event in placement.script or []]
                cells = [tuple(position) if isinstance(position, list | tuple) else () for position in positions]
            for cell in cells:
                in_grid = len(cell) == len(axes) and all(
                    isinstance(c, int) and not isinstance(c, bool) and 0 <= c < size for c, size in zip(cell, axes, strict=True)
                )
                if not in_grid:
                    errors.add(
                        f"Item '{rule.item_type}' {placement.mode} placement cell {list(cell)} is not a cell of the "
                        f"{'x'.join(str(size) for size in axes)} grid (a cell has {len(axes)} integer coordinates, "
                        "each in [0, size)).",
                        code=ErrorCode.ITEM_PLACEMENT_SUBSTRATE,
                        location=location,
                    )


def _validate_item_arena_profiles(raw: RawConfigsV21, source_map: SourceMap | None, errors: CompilationErrorCollector) -> None:
    """An item arena needs an item profile to store its rows in.

    The registry refuses `max_items > 0` with no item profiles at environment construction
    (`vfs/registry.py`); the two declarations are both visible here, so the refusal is
    located at the arena size instead.
    """
    items = raw.items
    if items is None:
        return
    if (items.max_items_in_world > 0 or items.max_items_per_agent > 0) and not raw.variables.item_profiles:
        errors.add(
            f"The item catalog declares an item arena (max_items_in_world={items.max_items_in_world}, "
            f"max_items_per_agent={items.max_items_per_agent}) but variables.item_profiles is empty; item rows have no "
            "profile to store their state in. Declare at least one item profile, or set both arena sizes to 0.",
            code=ErrorCode.ITEM_ARENA_PROFILE_MISSING,
            location=locate(source_map, "items:max_items_in_world", locate(source_map, "items")),
        )


_POSITION_FUNCTIONS = frozenset(name for name, spec in FUNCTION_SPECS.items() if REQUIRES_POSITIONS in spec.requires)
_SAME_WIDTH_FUNCTIONS = frozenset({"distance", "manhattan_distance", "within_radius", "nearest"})
"""The functions whose first two arguments must be vectors of one width (`_ensure_same_vector_width`)."""
_ELEMENT_INDEX_FUNCTIONS = frozenset({"gather", "scatter"})


def _string_leaves(value: Any, path: str) -> Iterable[tuple[str, str]]:
    """Every string in a dumped declaration, with its source-map key path (``a.b[0].c``)."""
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, Mapping):
        for key, child in value.items():
            yield from _string_leaves(child, f"{path}.{key}" if path else str(key))
    elif isinstance(value, list | tuple):
        for index, child in enumerate(value):
            yield from _string_leaves(child, f"{path}[{index}]")


def _calls(node: Any) -> Iterable[FunctionCall]:
    """Every function call in an expression AST."""
    if isinstance(node, FunctionCall):
        yield node
    if isinstance(node, ASTNode):
        for ast_field in fields(node):
            yield from _calls(getattr(node, ast_field.name))
    elif isinstance(node, list | tuple):
        for item in node:
            yield from _calls(item)


def _literal_int(node: ASTNode) -> int | None:
    if isinstance(node, Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, UnaryOp) and node.op == OperatorType.SUB:
        inner = _literal_int(node.operand)
        if inner is not None:
            return -inner
    return None


def _declared_widths(raw: RawConfigsV21) -> dict[str, int]:
    """The element width of every registry variable with elements, from its declaration."""
    widths: dict[str, int] = {}
    for declaration in raw.variables.declarations:
        if declaration.profile is not None:
            continue
        kind = declaration.type
        if kind in {"vec2f", "vec2i"}:
            widths[declaration.id] = 2
        elif kind in {"vec3f", "vec3i"}:
            widths[declaration.id] = 3
        elif kind in {"vecNf", "vecNi"} and declaration.dims is not None:
            widths[declaration.id] = declaration.dims
        elif kind.startswith("tensor") and declaration.shape:
            widths[declaration.id] = declaration.shape[-1]
    return widths


def _expression_documents(raw: RawConfigsV21) -> list[tuple[str, Any]]:
    """Every authored declaration that may hold an expression, as ``(source-map prefix, dumped payload)``."""
    documents: list[tuple[str, Any]] = [("variables", raw.variables.model_dump(mode="python", by_alias=True))]
    documents.append(("actions", raw.actions.model_dump(mode="python", by_alias=True)["actions"]))
    for prefix, model in (("effects", raw.effects), ("items", raw.items)):
        if model is not None:
            documents.append((prefix, model.model_dump(mode="python", by_alias=True)))
    for name, level in raw.levels.items():
        documents.append((f"levels/{name}/affordances", level.affordances.model_dump(mode="python", by_alias=True)))
    return documents


def _validate_expression_static_facts(raw: RawConfigsV21, source_map: SourceMap | None, errors: CompilationErrorCollector) -> None:
    """Refuse, at the expression's own line, what an expression's literals make wrong before it runs.

    - A position function (``distance_to_affordance``, ``in_range``, ``direction_to_affordance``,
      found from ``FUNCTION_SPECS`` by ``requires`` positions) on an aspatial substrate, which has
      no positions: the call would yield a constant.
    - A position function naming an affordance the pack does not declare (a typo), or one a level
      does not deploy (``training.enabled_affordances``): it has no position there, so the call
      would read infinity, false or a zero vector, and an exposed one crashes the observation.
    - Two vectors of declared, different widths given to a same-width function (``distance``,
      ``manhattan_distance``, ``within_radius``, ``nearest``).
    - A literal ``gather``/``scatter`` index outside its vector's declared width.

    Every declaration that may hold an expression is scanned (variable expressions, action writes,
    transition rules, effect and interaction pipelines); prose (a description) does not parse as
    an expression and is skipped.
    """
    aspatial = raw.stratum.stratum.substrate.type == "aspatial"
    declared_affordances = {affordance.name for level in raw.levels.values() for affordance in level.affordances.affordances}
    deployed = {name: set(level.training.enabled_affordances) for name, level in raw.levels.items()}
    widths = _declared_widths(raw)
    parser = ExpressionParser()

    documents = _expression_documents(raw)
    located: list[tuple[str, str, str]] = []  # (key, fallback key, text)
    for prefix, payload in documents:
        for path, text in _string_leaves(payload, ""):
            located.append((f"{prefix}:{path}", prefix, text))
    for rule in raw.transition_rules:
        rule_key = f"transition_rules:{rule.get('id')}"
        for path, text in _string_leaves(dict(rule), ""):
            located.append((rule_key, "transition_rules", text))

    for key, fallback_key, text in located:
        if "(" not in text:
            continue
        try:
            ast = parser.parse(text)
        except Exception:  # noqa: BLE001 - prose (a description) is not an expression; nothing to refuse
            continue
        location = locate(source_map, key, locate(source_map, fallback_key, str(raw.experiment_dir / fallback_key.split(":")[0])))
        for call in _calls(ast):
            name = call.function_name
            arguments = call.arguments
            if name in _POSITION_FUNCTIONS:
                if aspatial:
                    errors.add(
                        f"{key} calls '{name}', which needs agent and affordance positions, but the substrate is aspatial: "
                        "it has no positions, so the call would yield a constant. Remove the position read, or declare "
                        "a spatial substrate.",
                        code=ErrorCode.EXPRESSION_POSITION_ASPATIAL,
                        location=location,
                    )
                    continue
                if not arguments:
                    continue
                target = arguments[0]
                if not isinstance(target, Constant) or not isinstance(target.value, str):
                    continue
                if target.value not in declared_affordances:
                    errors.add(
                        f"{key} calls {name}(\"{target.value}\"), but no affordance is named '{target.value}'. "
                        f"Declared affordances: {sorted(declared_affordances)}.",
                        code=ErrorCode.EXPRESSION_AFFORDANCE_UNKNOWN,
                        location=location,
                    )
                    continue
                for level_name, enabled in sorted(deployed.items()):
                    if target.value not in enabled:
                        errors.add(
                            f"{key} calls {name}(\"{target.value}\"), but level '{level_name}' does not deploy "
                            f"'{target.value}' (training.enabled_affordances), so it has no position there and the call "
                            "would read infinity, false or a zero vector. Deploy it in every level, or read a deployed one.",
                            code=ErrorCode.EXPRESSION_AFFORDANCE_UNDEPLOYED,
                            location=location,
                        )
            elif name in _SAME_WIDTH_FUNCTIONS and len(arguments) >= 2:
                left, right = (widths.get(arg.name) if isinstance(arg, Variable) else None for arg in arguments[:2])
                if left is not None and right is not None and left != right:
                    errors.add(
                        f"{key} calls {name}() on vectors of declared widths {left} and {right}; '{name}' needs one width.",
                        code=ErrorCode.EXPRESSION_VECTOR_WIDTH,
                        location=location,
                    )
            elif name in _ELEMENT_INDEX_FUNCTIONS and len(arguments) >= 2 and isinstance(arguments[0], Variable):
                width = widths.get(arguments[0].name)
                index = _literal_int(arguments[1])
                if width is not None and index is not None and not 0 <= index < width:
                    errors.add(
                        f"{key} calls {name}({arguments[0].name}, {index}), but '{arguments[0].name}' has declared width "
                        f"{width}: an index is 0 to {width - 1}.",
                        code=ErrorCode.EXPRESSION_INDEX_RANGE,
                        location=location,
                    )


def _validate_affordance_deployments(
    raw: RawConfigsV21,
    experiment_dir: Path,
    source_map: SourceMap | None,
    errors: CompilationErrorCollector,
) -> None:
    """Deployment against the placement mode, and fixed positions against the substrate.

    With `training.randomize_affordances: false` the runtime places every deployed
    affordance at its declared `deployment.positions[0]` (`vectorized_env._position_to_tensor`),
    refusing a rank mismatch and a missing position only there, and never checking bounds
    at all (a cell outside the grid is placed where no agent can reach it). Each of those is
    a fact of the pack, so each is refused here at the line that declares it: every
    deployed affordance must be `fixed`, and every fixed position the level declares must be
    a position of the substrate. With `randomize_affordances: true` the runtime samples
    positions and reads none of the declared ones, so nothing is checked.
    """
    substrate = raw.stratum.stratum.substrate
    axes = grid_axis_sizes(substrate)
    bounds: list[tuple[float, float]] | None = None
    if substrate.type in {"continuous", "continuousnd"} and substrate.continuous is not None:
        bounds = list(substrate.continuous.bounds)
    if axes is not None:
        rank: int | None = len(axes)
        extent = "x".join(str(size) for size in axes)
    elif bounds is not None:
        rank = len(bounds)
        extent = "x".join(f"[{low}, {high}]" for low, high in bounds)
    else:
        rank = None
        extent = "aspatial"
    for level_name, level in raw.levels.items():
        if level.training.randomize_affordances:
            continue
        fallback = str(experiment_dir / "levels" / level_name / "affordances")
        deployed = set(level.training.enabled_affordances)
        for index, affordance in enumerate(level.affordances.affordances):
            deployment = affordance.deployment
            key = f"levels/{level_name}/affordances:affordances[{index}].deployment"
            if rank is not None and affordance.name in deployed and deployment.type != "fixed":
                errors.add(
                    f"Affordance '{affordance.name}' has deployment.type='{deployment.type}' but level '{level_name}' declares "
                    "training.randomize_affordances: false, so the runtime needs an explicit position for it. "
                    "Declare deployment.type: fixed with positions, or set randomize_affordances: true.",
                    code=ErrorCode.AFFORDANCE_POSITION_REQUIRED,
                    location=locate(source_map, f"{key}.type", locate(source_map, key, fallback)),
                )
            if deployment.type != "fixed":
                continue
            positions_location = locate(source_map, f"{key}.positions", locate(source_map, key, fallback))
            if rank is None:
                errors.add(
                    f"Affordance '{affordance.name}' declares fixed positions, but the substrate is aspatial and has no "
                    "positions. Use deployment.type: random.",
                    code=ErrorCode.AFFORDANCE_POSITION_SUBSTRATE,
                    location=positions_location,
                )
                continue
            for position in deployment.positions:
                if len(position) != rank:
                    errors.add(
                        f"Affordance '{affordance.name}' fixed position {list(position)} has {len(position)} coordinate(s), "
                        f"but the {substrate.type} substrate has rank {rank} ({extent}).",
                        code=ErrorCode.AFFORDANCE_POSITION_SUBSTRATE,
                        location=positions_location,
                    )
                    continue
                if axes is not None:
                    inside = all(0 <= coordinate < size for coordinate, size in zip(position, axes, strict=True))
                else:
                    assert bounds is not None
                    inside = all(low <= coordinate <= high for coordinate, (low, high) in zip(position, bounds, strict=True))
                if not inside:
                    errors.add(
                        f"Affordance '{affordance.name}' fixed position {list(position)} lies outside the {substrate.type} "
                        f"substrate ({extent}); it would be placed where no agent can reach it.",
                        code=ErrorCode.AFFORDANCE_POSITION_SUBSTRATE,
                        location=positions_location,
                    )


def _validate_opening_hours_day_period(
    raw: RawConfigsV21,
    experiment_dir: Path,
    source_map: SourceMap | None,
    errors: CompilationErrorCollector,
) -> None:
    """Opening hours are authored on a 24-hour clock; refuse them on any other active day period.

    The affordance gate compiles `time_in_window` over hours 0-23 and the affordance token
    carries one open-hour lane per hour of a 24-tick day (`OPENING_HOURS_FEATURES`), so a
    level whose resolved day clock period is not 24 would read its schedule against the
    wrong clock. The gate only runs with active temporal mechanics, and an inactive level
    declares no period, so only active levels are checked.
    """
    temporal_supported = raw.stratum.stratum.temporal_support == "enabled"
    for level_name, level in raw.levels.items():
        curriculum = level.curriculum.curriculum
        day_length = curriculum.day_length
        if not (temporal_supported and curriculum.active_temporal) or day_length is None or day_length == 24:
            continue
        fallback = str(experiment_dir / "levels" / level_name / "affordances")
        for index, affordance in enumerate(level.affordances.affordances):
            if not affordance.opening_hours.enabled:
                continue
            key = f"levels/{level_name}/affordances:affordances[{index}].opening_hours"
            errors.add(
                f"Affordance '{affordance.name}' declares opening_hours, but level '{level_name}' has a day clock period of "
                f"{day_length}; opening hours currently require a 24-tick day period.",
                code=ErrorCode.AFFORDANCE_OPENING_HOURS_DAY_PERIOD,
                location=locate(source_map, key, locate(source_map, f"levels/{level_name}/affordances:{affordance.name}", fallback)),
            )


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
    _validate_item_placements(raw, experiment_dir, source_map, errors)
    _validate_item_arena_profiles(raw, source_map, errors)
    _validate_affordance_deployments(raw, experiment_dir, source_map, errors)
    _validate_expression_static_facts(raw, source_map, errors)
    _validate_opening_hours_day_period(raw, experiment_dir, source_map, errors)

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
                    if isinstance(modify, str) and modify.startswith("bar."):
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

        # Under S1 the batch is N independent single-agent worlds sharing one affordance layout:
        # random placement needs one world to hold its deployed affordances plus its one agent,
        # whatever the population size. That is a fact of the pack, so it refuses here rather
        # than at runtime (which used to fall back, silently, to declared positions).
        if grid_capacity is not None and level.training.randomize_affordances:
            deployed_count = len(normalized_enabled)
            required_slots = deployed_count + 1
            if required_slots > grid_capacity:
                training_fallback = str(level_dir / "training")
                errors.add(
                    f"Grid capacity exceeded: level '{level_name}' randomizes {deployed_count} deployed affordance(s) plus one "
                    f"agent per world ({required_slots} distinct cells), but the substrate has {grid_capacity} cell(s). "
                    "Enlarge the substrate, deploy fewer affordances, or set randomize_affordances: false with fixed positions.",
                    code=ErrorCode.GRID_CAPACITY_EXCEEDED,
                    location=locate(
                        source_map,
                        f"levels/{level_name}/training:randomize_affordances",
                        locate(source_map, f"levels/{level_name}/training", training_fallback),
                    ),
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
