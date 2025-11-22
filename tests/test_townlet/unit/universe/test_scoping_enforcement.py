from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError


def _write_minimal_experiment(root: Path) -> None:
    """Create a minimal valid experiment layout (without levels)."""
    (root / "experiment.yaml").write_text("version: 2.1\nname: test\n")
    (root / "stratum.yaml").write_text("version: 2.1\nsubstrate:\n  type: grid\n  grid:\n    width: 1\n    height: 1\n")
    (root / "environment.yaml").write_text(
        "version: 2.1\n" "meters: []\n" "affordances: []\n" "cascade_graph: []\n" "modulation_graph: []\n" "variables: []\n"
    )
    (root / "actions.yaml").write_text("version: 2.1\ncustom_actions: []\n")
    (root / "agent.yaml").write_text("version: 2.1\n")
    levels_dir = root / "levels" / "L1"
    levels_dir.mkdir(parents=True)
    (levels_dir / "curriculum.yaml").write_text("version: 2.1\ncurriculum:\n  active_temporal: false\n  active_vision: global\n")
    (levels_dir / "bars.yaml").write_text("version: 2.1\nmeters: []\ncascades: []\n")
    (levels_dir / "affordances.yaml").write_text("version: 2.1\naffordances: []\nmodulations: []\n")
    (levels_dir / "training.yaml").write_text("version: 2.1\npopulation:\n  size: 1\n")


def test_missing_experiment_files_rejected():
    """Compiler should fail when shared experiment-level catalogs are missing."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_minimal_experiment(root)
        # Do NOT create vfs_profiles/effects/items
        compiler = UniverseCompiler()
        with pytest.raises(CompilationError, match="Missing required experiment-level file"):
            compiler.compile(root)


def test_level_scoped_shared_files_rejected():
    """Compiler should fail when shared catalogs appear under a level."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_minimal_experiment(root)
        # Provide required experiment-level files
        (root / "vfs_profiles.yaml").write_text("version: 2.1\nglobal_profile: {}\nitem_profiles: []\n")
        (root / "effects.yaml").write_text("version: 2.1\neffects: []\n")
        (root / "items.yaml").write_text("version: 2.1\nitems: []\n")
        # Add forbidden level-scoped copies
        level_dir = root / "levels" / "L1"
        (level_dir / "vfs_profiles.yaml").write_text("version: 2.1\n")
        (level_dir / "effects.yaml").write_text("version: 2.1\n")
        (level_dir / "items.yaml").write_text("version: 2.1\n")

        compiler = UniverseCompiler()
        with pytest.raises(CompilationError, match="SCOPING_FORBIDDEN_LEVEL_FILE"):
            compiler.compile(root)
