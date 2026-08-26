"""Pipeline-level tests for UniverseCompiler staging."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import pytest
import yaml

from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError


def _copy_experiment(tmp_path: Path) -> Path:
    source = Path("configs/test/model_config")
    dest = tmp_path / source.name
    shutil.copytree(source, dest)
    return dest


def test_stage_markers_emit_in_order(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Compiler should emit the stage markers in order."""
    config_dir = _copy_experiment(tmp_path)
    compiler = UniverseCompiler()

    caplog.set_level(logging.INFO, logger="townlet.universe.compiler")
    compiler.compile(config_dir, primary_level="L0_test", use_cache=False)

    markers = [
        record.message for record in caplog.records if record.name == "townlet.universe.compiler" and record.message.startswith("Stage ")
    ]

    assert markers == [
        "Stage 1: Parse v2.1 configs",
        "Stage 2: Enforce safety limits",
        "Stage 3: Cross-validate semantics",
        "Stage 4: Build symbol table",
        "Stage 5: Resolve references",
        "Stage 6: Enrich shared schemas and effects",
        "Stage 7: Compile levels and optimization data",
        "Stage 8: Emit compiled universe",
    ]


def test_stage3_resolves_invalid_affordance_reference(tmp_path: Path) -> None:
    """Unknown item references in level spawn rules should fail during Stage 3 resolution."""
    config_dir = _copy_experiment(tmp_path)
    items_path = config_dir / "levels" / "L0_test" / "items.yaml"
    items_payload = {
        "version": "1.0",
        "items": [
            {
                "item_type": "ghost_item",
                "spawn_count": 1,
            }
        ],
    }
    items_path.write_text(yaml.safe_dump(items_payload))

    compiler = UniverseCompiler()
    with pytest.raises(CompilationError) as excinfo:
        compiler.compile(config_dir, primary_level="L0_test", use_cache=False)

    assert "Stage 5: Resolve references" in str(excinfo.value)
    assert "ghost_item" in str(excinfo.value)


def test_compile_requires_explicit_primary_level(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)

    with pytest.raises(ValueError, match="requires an explicit primary_level"):
        UniverseCompiler().compile(config_dir, use_cache=False)


def test_compile_rejects_level_directory_input(tmp_path: Path) -> None:
    config_dir = _copy_experiment(tmp_path)
    level_dir = config_dir / "levels" / "L0_test"

    with pytest.raises(CompilationError, match="Cannot validate level directory directly"):
        UniverseCompiler().compile(level_dir, primary_level="L0_test", use_cache=False)






