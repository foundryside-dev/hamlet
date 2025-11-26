#!/usr/bin/env python3
"""Validate config packs by invoking the CLI compiler."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIGS_ROOT = REPO_ROOT / "configs"
# Excluded directories:
# - `templates`: Template config files, not actual experiments
# - `aspatial_test`: Trimmed pack for unit tests that violates Stage 4 assumptions
# - `reference_config`: Documentation only, not a runnable experiment
EXCLUDED_DIRS = {"templates", "aspatial_test", "reference_config"}

# Packs that are expected to fail validation (negative test fixtures). We assert
# they do fail; a successful validation here means a regression in error handling.
EXPECTED_FAIL_DIRS = {"vfs_circular_dependency", "vfs_type_mismatch", "vfs_undefined_var"}


def iter_config_dirs(base: Path) -> list[Path]:
    """Recursively find all v2.1 experiment directories (containing experiment.yaml)."""
    dirs: list[Path] = []

    def scan_dir(path: Path) -> None:
        """Recursively scan for experiment directories."""
        for entry in sorted(path.iterdir()):
            if not entry.is_dir() or entry.name in EXCLUDED_DIRS:
                continue

            # v2.1 experiment directories contain experiment.yaml
            if (entry / "experiment.yaml").exists():
                dirs.append(entry)
            else:
                # Recurse into subdirectories to find nested experiment packs
                # (e.g., configs/test/action_space/grid2d/)
                scan_dir(entry)

    scan_dir(base)
    return dirs


def run_cli_validate(config_dir: Path, expect_failure: bool = False) -> None:
    cmd = [sys.executable, "-m", "townlet.universe", "validate", str(config_dir)]
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    if expect_failure:
        if result.returncode == 0:
            raise RuntimeError(f"Expected validation to fail for {config_dir}, but it succeeded")
    else:
        result.check_returncode()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate config packs via python -m townlet.universe validate")
    parser.add_argument("config", nargs="?", help="Optional single config directory to validate")
    args = parser.parse_args()

    if args.config:
        config_dirs = [Path(args.config).resolve()]
    else:
        config_dirs = iter_config_dirs(CONFIGS_ROOT)

    if not config_dirs:
        print("No config packs found for validation", file=sys.stderr)
        return 1

    for config_dir in config_dirs:
        try:
            display_path = config_dir.relative_to(REPO_ROOT)
        except ValueError:
            display_path = config_dir
        expect_fail = config_dir.name in EXPECTED_FAIL_DIRS
        print(f"🔧 Validating {display_path} via CLI ...", end="")
        if expect_fail:
            print(" (expected failure fixture)")
        else:
            print()
        run_cli_validate(config_dir, expect_failure=expect_fail)

    print("✅ Universe compiler CLI validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
