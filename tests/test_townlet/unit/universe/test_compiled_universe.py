"""Tests for CompiledUniverse Stage 7 artifact."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler


def test_compiler_returns_compiled_universe() -> None:
    compiler = UniverseCompiler()
    compiled = compiler.compile(Path("configs/default_curriculum"), primary_level="L0_0_minimal")

    assert isinstance(compiled, CompiledUniverse)
    # v2.1: universe_name comes from experiment.yaml metadata.name
    assert compiled.metadata.universe_name == "Complete Reference Example"
    assert compiled.token_spec.total_dims == compiled.metadata.observation_dim


def test_compiled_universe_is_frozen() -> None:
    compiler = UniverseCompiler()
    compiled = compiler.compile(Path("configs/default_curriculum"), primary_level="L0_0_minimal")

    try:
        compiled.metadata = None  # type: ignore[attr-defined]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("CompiledUniverse should be frozen")
