"""Raw config loader for Config v2.1 hierarchical structure."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from townlet.config.actions_config import ActionsConfig
from townlet.config.affordances_v2_config import AffordancesV2Config, load_affordances_v2_config
from townlet.config.bars_v2_config import BarsV2Config, load_bars_v2_config
from townlet.config.brain_config import BrainConfig, load_brain_config
from townlet.config.curriculum_config import CurriculumConfig
from townlet.config.drive_as_code import DriveAsCodeConfig
from townlet.config.environment_config import EnvironmentConfig
from townlet.config.experiment_config import ExperimentConfig
from townlet.config.items_config import ItemsAppearanceConfig, ItemsCatalogConfig
from townlet.config.stratum_config import StratumConfig
from townlet.config.training_v2_config import TrainingV2Config, load_training_v2_config
from townlet.universe.errors import CompilationErrorCollector

# Security limits (mirrors compiler.py, kept local to avoid circular imports)
MAX_METERS = 100
MAX_AFFORDANCES = 100
MAX_CASCADES = 500
MAX_ACTIONS = 300
MAX_VARIABLES = 200
MAX_GRID_CELLS = 10_000  # 100×100 maximum (DoS protection)
MAX_ITEM_TYPES = 200
MAX_VFS_PROFILES = 200
MAX_SPAWN_RULES_PER_ITEM = 200

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CurriculumLevel:
    """All curriculum-level configs for a single level."""

    name: str
    curriculum: CurriculumConfig
    bars: BarsV2Config
    affordances: AffordancesV2Config
    drive: DriveAsCodeConfig
    training: TrainingV2Config
    items_appearance: ItemsAppearanceConfig | None = None

    @property
    def level_dir(self) -> str:
        """Directory name for this level."""
        return self.name


@dataclass(frozen=True)
class RawConfigsV21:
    """Container for all v2.1 hierarchical config DTOs."""

    # Experiment-level configs (shared vocabulary and metadata)
    experiment: ExperimentConfig
    stratum: StratumConfig
    environment: EnvironmentConfig
    actions: ActionsConfig
    brain: BrainConfig

    # Curriculum levels (per-level parameters)
    levels: dict[str, CurriculumLevel]

    # Provenance
    experiment_dir: Path

    # Optional experiment-level configs
    items: ItemsCatalogConfig | None = None

    def __post_init__(self) -> None:
        """Validate v2.1 invariants across all curriculum levels."""
        if not self.levels:
            raise ValueError(f"No curriculum levels found in {self.experiment_dir}")

        env_meter_names = {meter.name for meter in self.environment.environment.meters}
        env_affordance_names = {aff.name for aff in self.environment.environment.affordances}

        # ------------------------------------------------------------------
        # Global security limits (per-environment counts)
        # ------------------------------------------------------------------
        env_cascades = getattr(self.environment.environment, "cascade_graph", [])
        env_variables = getattr(self.environment.environment, "variables", []) or []

        checks = [
            (len(env_meter_names), MAX_METERS, "environment.yaml", "meters"),
            (len(env_affordance_names), MAX_AFFORDANCES, "environment.yaml", "affordances"),
            (len(env_cascades), MAX_CASCADES, "environment.yaml", "cascade_graph"),
            (len(self.actions.actions.custom_actions), MAX_ACTIONS, "actions.yaml", "actions"),
            (len(env_variables), MAX_VARIABLES, "environment.yaml", "variables"),
        ]

        for count, limit, filename, label in checks:
            if count > limit:
                raise ValueError(
                    f"Too many {label}: found {count} (max {limit}).\n"
                    f"  Experiment: {self.experiment_dir}\n"
                    f"  File: {filename}\n"
                    "This may indicate config injection, duplication, or an unsafe configuration size."
                )

        if self.items is not None:
            item_count = len(self.items.item_types)
            if item_count > MAX_ITEM_TYPES:
                raise ValueError(
                    "items.yaml item_types exceeds safety limit for v2.1 configs.\n"
                    f"  Experiment: {self.experiment_dir}\n"
                    f"  Item types: {item_count} (max {MAX_ITEM_TYPES})\n"
                    "Reduce catalog size; oversized catalogs are rejected."
                )

        # ------------------------------------------------------------------
        # Cascade invariants (environment.yaml cascade_graph vs bars.yaml)
        # ------------------------------------------------------------------
        env_edges = {(c.source, c.target) for c in env_cascades}

        # Validate that cascade sources/targets reference existing meters
        for edge in env_cascades:
            cascade_problems: list[str] = []
            if edge.source not in env_meter_names:
                cascade_problems.append(f"unknown source meter '{edge.source}'")
            if edge.target not in env_meter_names:
                cascade_problems.append(f"unknown target meter '{edge.target}'")
            if cascade_problems:
                raise ValueError(
                    "Invalid cascade_graph entry in environment.yaml.\n"
                    f"  Experiment: {self.experiment_dir}\n"
                    f"  Edge: ({edge.source} -> {edge.target})\n"
                    f"  Problem: {', '.join(cascade_problems)}\n"
                    f"  Valid meters: {sorted(env_meter_names)}\n"
                    "\nAll cascade_graph entries must reference meters declared in environment.yaml meters."
                )

        # Detect cycles in environment cascade graph (structural)
        cascade_graph: dict[str, list[str]] = {}
        for edge in env_cascades:
            cascade_graph.setdefault(edge.source, []).append(edge.target)

        def _detect_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
            cycles: list[list[str]] = []
            visited: set[str] = set()
            stack: set[str] = set()

            def dfs(node: str, path: list[str]) -> None:
                visited.add(node)
                stack.add(node)
                path.append(node)
                for neighbor in graph.get(node, []):
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

        cycles = _detect_cycles(cascade_graph)
        if cycles:
            formatted = ", ".join(" → ".join(c + [c[0]]) for c in cycles)
            raise ValueError(
                "Cascade circularity detected in environment.yaml cascade_graph.\n"
                f"  Experiment: {self.experiment_dir}\n"
                f"  Cycles: {formatted}\n"
                "\nFix cascade_graph in environment.yaml so it is acyclic."
            )

        # ------------------------------------------------------------------
        # Modulation invariants (environment.yaml modulation_graph vs affordances.yaml)
        # ------------------------------------------------------------------
        env_mods = getattr(self.environment.environment, "modulation_graph", [])

        # Validate that modulation_graph references existing bars and affordances
        for mod in env_mods:
            modulation_problems: list[str] = []
            if mod.bar not in env_meter_names:
                modulation_problems.append(f"unknown bar '{mod.bar}'")
            invalid_affs = [name for name in mod.affordances if name not in env_affordance_names]
            if invalid_affs:
                modulation_problems.append(f"unknown affordances {sorted(invalid_affs)}")
            if modulation_problems:
                raise ValueError(
                    "Invalid modulation_graph entry in environment.yaml.\n"
                    f"  Experiment: {self.experiment_dir}\n"
                    f"  Entry: (bar={mod.bar}, affordances={sorted(mod.affordances)})\n"
                    f"  Problem: {', '.join(modulation_problems)}\n"
                    f"  Valid meters: {sorted(env_meter_names)}\n"
                    f"  Valid affordances: {sorted(env_affordance_names)}\n"
                    "\nAll modulation_graph entries must reference meters and affordances declared in environment.yaml."
                )

        env_mod_pairs = {(m.bar, tuple(sorted(m.affordances))) for m in env_mods}

        # ------------------------------------------------------------------
        # Per-level invariants: vocabulary, capacity, cascades, modulations
        # ------------------------------------------------------------------

        substrate = self.stratum.stratum.substrate
        grid_capacity: int | None = None
        grid_config = getattr(substrate, "grid", None)
        if getattr(substrate, "type", None) == "grid" and grid_config is not None:
            # 2D (square) or 3D (cubic) grid
            width = grid_config.width
            height = grid_config.height
            depth = getattr(grid_config, "depth", None)
            if grid_config.topology == "cubic" and depth is not None:
                grid_capacity = width * height * depth
            else:
                grid_capacity = width * height
            if grid_capacity > MAX_GRID_CELLS:
                raise ValueError(
                    "Grid size exceeds safety limit for v2.1 configs.\n"
                    f"  Experiment: {self.experiment_dir}\n"
                    f"  Dimensions: {width}×{height}"
                    f"{'×' + str(depth) if depth is not None and grid_config.topology == 'cubic' else ''}"
                    f" = {grid_capacity} cells (max {MAX_GRID_CELLS})\n"
                    "\nReduce grid dimensions in stratum.yaml to avoid excessive observation/state sizes."
                )
        gridnd_config = getattr(substrate, "gridnd", None)
        if getattr(substrate, "type", None) == "gridnd" and gridnd_config is not None:
            # N-dimensional grid: product of all dimension sizes
            grid_capacity = 1
            for size in gridnd_config.dimension_sizes:
                grid_capacity *= size
            if grid_capacity > MAX_GRID_CELLS:
                dims_str = "×".join(str(s) for s in gridnd_config.dimension_sizes)
                raise ValueError(
                    "GridND size exceeds safety limit for v2.1 configs.\n"
                    f"  Experiment: {self.experiment_dir}\n"
                    f"  Dimensions: {dims_str} = {grid_capacity} cells (max {MAX_GRID_CELLS})\n"
                    "\nReduce dimension_sizes in stratum.yaml to avoid excessive observation/state sizes."
                )

        for level_name, level in self.levels.items():
            level_meter_names = {meter.name for meter in level.bars.meters}
            level_affordance_names = {aff.name for aff in level.affordances.affordances}

            if level.items_appearance is not None:
                per_item_rule_counts: dict[str, int] = {}
                for rule in level.items_appearance.items:
                    per_item_rule_counts[rule.item_type] = per_item_rule_counts.get(rule.item_type, 0) + 1
                    if per_item_rule_counts[rule.item_type] > MAX_SPAWN_RULES_PER_ITEM:
                        raise ValueError(
                            "items.yaml spawn rules exceed safety limit for a single item type.\n"
                            f"  Experiment: {self.experiment_dir}\n"
                            f"  Level: {level_name}\n"
                            f"  Item type: {rule.item_type}\n"
                            f"  Rules: {per_item_rule_counts[rule.item_type]} (max {MAX_SPAWN_RULES_PER_ITEM})\n"
                            "Reduce spawn rules per item to avoid unbounded spawn scheduling."
                        )

            # Vocabulary consistency
            if level_meter_names != env_meter_names:
                missing = env_meter_names - level_meter_names
                extra = level_meter_names - env_meter_names
                raise ValueError(
                    "Meter vocabulary mismatch between environment.yaml and levels "
                    f"bars.yaml for level '{level_name}'.\n"
                    f"  Experiment: {self.experiment_dir}\n"
                    f"  Expected (from environment.yaml): {sorted(env_meter_names)}\n"
                    f"  Actual (from levels/{level_name}/bars.yaml): {sorted(level_meter_names)}\n"
                    f"  Missing: {sorted(missing) if missing else 'none'}\n"
                    f"  Extra: {sorted(extra) if extra else 'none'}\n"
                    "\nAll levels must have identical meter vocabulary to environment.yaml."
                )

            if level_affordance_names != env_affordance_names:
                missing = env_affordance_names - level_affordance_names
                extra = level_affordance_names - env_affordance_names
                raise ValueError(
                    "Affordance vocabulary mismatch between environment.yaml and levels "
                    f"affordances.yaml for level '{level_name}'.\n"
                    f"  Experiment: {self.experiment_dir}\n"
                    f"  Expected (from environment.yaml): {sorted(env_affordance_names)}\n"
                    f"  Actual (from levels/{level_name}/affordances.yaml): {sorted(level_affordance_names)}\n"
                    f"  Missing: {sorted(missing) if missing else 'none'}\n"
                    f"  Extra: {sorted(extra) if extra else 'none'}\n"
                    "\nAll levels must have identical affordance vocabulary to environment.yaml."
                )

            # Cascade coverage per level
            level_edges = {(c.source, c.target) for c in level.bars.cascades}
            missing_edges = env_edges - level_edges
            extra_edges = level_edges - env_edges
            if missing_edges:
                raise ValueError(
                    f"Missing cascade entries in levels/{level_name}/bars.yaml.\n"
                    f"  Experiment: {self.experiment_dir}\n"
                    f"  Level: {level_name}\n"
                    f"  Missing cascades (must match environment.yaml cascade_graph): {sorted(missing_edges)}\n"
                    "\nAll cascades from environment.yaml cascade_graph MUST be present in each level's bars.yaml "
                    "(set strength: 0.0 to disable, do not omit)."
                )
            if extra_edges:
                raise ValueError(
                    f"Extra cascades found in levels/{level_name}/bars.yaml.\n"
                    f"  Experiment: {self.experiment_dir}\n"
                    f"  Level: {level_name}\n"
                    f"  Extra cascades (not in environment.yaml cascade_graph): {sorted(extra_edges)}\n"
                    "\nbars.yaml cascades must exactly match the structure declared in environment.yaml cascade_graph."
                )

            # Modulation coverage per level
            level_mod_pairs = {(m.bar, tuple(sorted(m.affordances))) for m in level.affordances.modulations}
            missing_mods = env_mod_pairs - level_mod_pairs
            extra_mods = level_mod_pairs - env_mod_pairs
            if missing_mods:
                raise ValueError(
                    f"Missing modulation entries in levels/{level_name}/affordances.yaml.\n"
                    f"  Experiment: {self.experiment_dir}\n"
                    f"  Level: {level_name}\n"
                    f"  Missing modulations (must match environment.yaml modulation_graph): {sorted(missing_mods)}\n"
                    "\naffordances.yaml modulations must implement every relationship declared in "
                    "environment.yaml modulation_graph."
                )

            # Affordance costs meter references must be valid
            for aff in level.affordances.affordances:
                invalid_cost_meters = [name for name in aff.costs.keys() if name not in env_meter_names]

                # Extract meter names from interactions (Effects commands)
                # Effects commands use paths like "target.bar.{meter_name}"
                invalid_interaction_meters = []
                for stage_commands in aff.interactions.values():
                    for cmd in stage_commands:
                        # Extract meter name from modify path (e.g., "target.bar.energy" -> "energy")
                        modify = getattr(cmd, "modify", None)
                        if isinstance(modify, str) and modify.startswith("target.bar."):
                            meter_name = modify.split(".")[-1]
                            if meter_name not in env_meter_names:
                                invalid_interaction_meters.append(meter_name)

                if invalid_cost_meters or invalid_interaction_meters:
                    affordance_problems: list[str] = []
                    if invalid_cost_meters:
                        affordance_problems.append(f"costs: {sorted(invalid_cost_meters)}")
                    if invalid_interaction_meters:
                        affordance_problems.append(f"interactions: {sorted(set(invalid_interaction_meters))}")
                    raise ValueError(
                        "Affordance references unknown meters in costs/interactions.\n"
                        f"  Experiment: {self.experiment_dir}\n"
                        f"  Level: {level_name}\n"
                        f"  Affordance: {aff.name}\n"
                        f"  Invalid meter names: {', '.join(affordance_problems)}\n"
                        f"  Valid meters (from environment.yaml): {sorted(env_meter_names)}\n"
                        "\nAll meter keys in costs/effects must match meters declared in environment.yaml."
                    )
            if extra_mods:
                raise ValueError(
                    f"Extra modulation entries found in levels/{level_name}/affordances.yaml.\n"
                    f"  Experiment: {self.experiment_dir}\n"
                    f"  Level: {level_name}\n"
                    f"  Extra modulations (not in environment.yaml modulation_graph): {sorted(extra_mods)}\n"
                    "\naffordances.yaml modulations must not introduce new bar→affordance relationships "
                    "beyond environment.yaml modulation_graph."
                )

            # Validate curriculum-level enabled_affordances against environment vocabulary
            enabled_affordances = getattr(level.training, "enabled_affordances", None)
            normalized_enabled = env_affordance_names
            if enabled_affordances is not None:
                normalized_enabled = {str(name) for name in enabled_affordances}
                invalid = normalized_enabled - env_affordance_names
                if invalid:
                    raise ValueError(
                        "Invalid enabled_affordances in training.yaml.\n"
                        f"  Experiment: {self.experiment_dir}\n"
                        f"  Level: {level_name}\n"
                        f"  Invalid entries: {sorted(invalid)}\n"
                        f"  Valid affordances (from environment.yaml): {sorted(env_affordance_names)}\n"
                        "\nAll entries in training.enabled_affordances must match affordance names "
                        "declared in environment.yaml."
                    )

            # Capacity check for grid substrates: hard error if deployed affordances + agents exceed grid capacity.
            # NOTE: This check must be INSIDE the loop to validate ALL levels, not just the last one.
            if grid_capacity is not None:
                deployed_count = len(normalized_enabled)
                population_size = getattr(level.training.population, "size", 0)
                required_slots = deployed_count + population_size
                if required_slots > grid_capacity:
                    raise ValueError(
                        "Grid capacity exceeded for level configuration.\n"
                        f"  Experiment: {self.experiment_dir}\n"
                        f"  Level: {level_name}\n"
                        f"  Capacity (cells): {grid_capacity}\n"
                        f"  Agents: {population_size}\n"
                        f"  Affordances deployed: {deployed_count}\n"
                        f"  Required slots: {required_slots}\n"
                        "\nReduce population size or enabled affordances, or increase grid dimensions."
                    )

    @classmethod
    def from_experiment_dir(cls, experiment_dir: Path) -> RawConfigsV21:
        """
        Load all configs from a v2.1 experiment directory.

        Expected structure:
            experiment_dir/
              experiment.yaml
              stratum.yaml
              environment.yaml
              actions.yaml
              agent.yaml
              levels/
                <level_name>/
                  curriculum.yaml
                  bars.yaml
                  affordances.yaml
                  training.yaml
        """

        experiment_dir = Path(experiment_dir).resolve()
        errors = CompilationErrorCollector(stage="Stage 1: Load v2.1 Configs")

        # Shared experiment-level configs
        experiment = stratum = environment = actions = brain = items = None
        shared_specs = [
            ("experiment.yaml", ExperimentConfig, "experiment"),
            ("stratum.yaml", StratumConfig, "stratum"),
            ("environment.yaml", EnvironmentConfig, "environment"),
            ("actions.yaml", ActionsConfig, "actions"),
        ]

        for filename, loader_cls, label in shared_specs:
            path = experiment_dir / filename
            try:
                loaded = loader_cls.from_yaml(path)  # type: ignore[attr-defined]
            except Exception as exc:  # noqa: BLE001 - we want to aggregate anything
                errors.add(
                    f"Failed to load {label} from {filename}: {exc}",
                    code="LOAD_ERROR",
                    location=str(path),
                )
                continue

            if label == "experiment":
                experiment = loaded
            elif label == "stratum":
                stratum = loaded
            elif label == "environment":
                environment = loaded
            elif label == "actions":
                actions = loaded

        # Load brain.yaml
        brain_path = experiment_dir / "brain.yaml"
        try:
            brain = load_brain_config(experiment_dir)
        except Exception as exc:
            errors.add(
                f"Failed to load brain from brain.yaml: {exc}",
                code="LOAD_ERROR",
                location=str(brain_path),
            )

        # Load items.yaml (optional)
        items_path = experiment_dir / "items.yaml"
        if items_path.exists():
            try:
                loaded_items = ItemsCatalogConfig.from_yaml(items_path)
                # Treat zero-capacity catalogs as disabled to remove item actions/obs.
                if loaded_items.max_items_in_world == 0 or loaded_items.max_items_per_agent == 0:
                    items = None
                else:
                    items = loaded_items
            except Exception as exc:  # noqa: BLE001
                errors.add(
                    f"Failed to load items from items.yaml: {exc}",
                    code="LOAD_ERROR",
                    location=str(items_path),
                )

        # If any shared config failed, surface now.
        if errors.errors:
            errors.check_and_raise()

        # Curriculum levels
        levels_dir = experiment_dir / "levels"
        if not levels_dir.exists():
            errors.add(
                f"Missing levels/ directory under {experiment_dir}",
                code="MISSING_LEVELS_DIR",
                location=str(levels_dir),
            )
            errors.check_and_raise()

        levels: dict[str, CurriculumLevel] = {}
        for level_dir in sorted(levels_dir.iterdir()):
            if not level_dir.is_dir():
                continue

            level_name = level_dir.name
            try:
                curriculum = CurriculumConfig.from_yaml(level_dir / "curriculum.yaml")
                bars = load_bars_v2_config(level_dir)
                affordances = load_affordances_v2_config(level_dir)
                training = load_training_v2_config(level_dir)

                # Load drive.yaml
                drive_path = level_dir / "drive.yaml"
                import yaml

                with open(drive_path) as f:
                    drive_data = yaml.safe_load(f)
                drive = DriveAsCodeConfig(**drive_data["drive"])

                # Load level-specific items.yaml if exists
                items_appearance = None
                level_items_path = level_dir / "items.yaml"
                if level_items_path.exists():
                    import yaml

                    with open(level_items_path) as f:
                        items_data = yaml.safe_load(f)
                    items_appearance = ItemsAppearanceConfig(**items_data)

                levels[level_name] = CurriculumLevel(
                    name=level_name,
                    curriculum=curriculum,
                    bars=bars,
                    affordances=affordances,
                    drive=drive,
                    training=training,
                    items_appearance=items_appearance,
                )
            except Exception as exc:  # noqa: BLE001
                errors.add(
                    f"Failed to load level '{level_name}': {exc}",
                    code="LEVEL_LOAD_ERROR",
                    location=str(level_dir),
                )

        if not levels:
            errors.add(
                f"No curriculum levels found in {levels_dir}",
                code="NO_CURRICULUM_LEVELS",
                location=str(levels_dir),
            )

        errors.check_and_raise()

        return cls(
            experiment=experiment,  # type: ignore[arg-type]
            stratum=stratum,  # type: ignore[arg-type]
            environment=environment,  # type: ignore[arg-type]
            actions=actions,  # type: ignore[arg-type]
            brain=brain,  # type: ignore[arg-type]
            items=items,
            levels=levels,
            experiment_dir=experiment_dir,
        )
