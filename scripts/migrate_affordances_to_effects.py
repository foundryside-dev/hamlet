"""Migrate affordances.yaml from effects dict to Effects commands.

Usage:
    python scripts/migrate_affordances_to_effects.py configs/default_curriculum/levels/L0_0_minimal
    python scripts/migrate_affordances_to_effects.py --all  # Migrate all levels
"""

import argparse
from pathlib import Path

import yaml


def migrate_affordance(affordance: dict) -> dict:
    """Migrate single affordance from effects dict to interactions commands.

    Supports three input formats:
    1. Simple effects dict → interactions.on_start (costs PRESERVED)
    2. effect_pipeline → interactions (all stages)
    3. Multi-tick affordances (costs_per_tick PRESERVED)

    NOTE: costs and costs_per_tick fields are PRESERVED as affordability gates.
    Only effects/effect_pipeline are migrated to interactions.
    """
    # If already has interactions, skip
    if "interactions" in affordance:
        return affordance

    interactions = {
        "on_start": [],
        "per_tick": [],
        "on_completion": [],
        "on_early_exit": [],
        "on_failure": [],
    }

    # PATH 1: Migrate effect_pipeline (if present)
    if "effect_pipeline" in affordance:
        pipeline = affordance["effect_pipeline"]
        for stage in ["on_start", "per_tick", "on_completion", "on_early_exit", "on_failure"]:
            for effect in pipeline.get(stage, []):
                interactions[stage].append(
                    {
                        "modify": f"target.bar.{effect['meter']}",
                        "value": f"target.bar.{effect['meter']} + {effect['amount']}",
                    }
                )

        affordance.pop("effect_pipeline")

    # PATH 2: Migrate simple effects dict (on_start only)
    else:
        effects = affordance.get("effects", {})

        # Convert effects to modify commands (on_start)
        for meter, amount in effects.items():
            interactions["on_start"].append(
                {
                    "modify": f"target.bar.{meter}",
                    "value": f"target.bar.{meter} + {amount}",
                }
            )

        # Remove effects field (migrated to interactions)
        affordance.pop("effects", None)

        # PRESERVE costs and costs_per_tick fields (affordability gates)
        # These are NOT migrated - they remain as separate pre-check mechanism

    # Add interactions
    affordance["interactions"] = interactions

    return affordance


def migrate_file(config_path: Path, dry_run: bool = False) -> None:
    """Migrate affordances.yaml file."""
    affordances_file = config_path / "affordances.yaml"

    if not affordances_file.exists():
        print(f"❌ Not found: {affordances_file}")
        return

    print(f"📝 Migrating: {affordances_file}")

    # Load YAML
    with open(affordances_file) as f:
        data = yaml.safe_load(f)

    # Migrate each affordance
    affordances = data["affordances"]["affordances"]
    for i, aff in enumerate(affordances):
        affordances[i] = migrate_affordance(aff)

    # Save (or show) result
    if dry_run:
        print(yaml.dump(data, default_flow_style=False, sort_keys=False))
    else:
        with open(affordances_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        print(f"✅ Migrated: {affordances_file}")


def main():
    parser = argparse.ArgumentParser(description="Migrate affordances to Effects commands")
    parser.add_argument("path", nargs="?", help="Path to config level directory")
    parser.add_argument("--all", action="store_true", help="Migrate all curriculum levels")
    parser.add_argument("--dry-run", action="store_true", help="Show output without writing")

    args = parser.parse_args()

    if args.all:
        levels_dir = Path("configs/default_curriculum/levels")
        for level_dir in sorted(levels_dir.iterdir()):
            if level_dir.is_dir():
                migrate_file(level_dir, dry_run=args.dry_run)
    elif args.path:
        migrate_file(Path(args.path), dry_run=args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
