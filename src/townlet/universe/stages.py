"""Authoritative stage vocabulary for the universe compile pipeline."""

from __future__ import annotations

from enum import Enum


class CompilationStage(Enum):
    """The compile pipeline's stages, in execution order.

    This enum is the single authority on stage numbering. Log markers,
    error ``stage`` labels, and ``UniverseCompiler`` method names all cite
    it; do not hand-write "Stage N" strings anywhere else.
    """

    PREFLIGHT = (0, "Preflight validation")
    PARSE = (1, "Parse v2.1 configs")
    LIMITS = (2, "Enforce safety limits")
    SEMANTICS = (3, "Cross-validate semantics")
    SYMBOLS = (4, "Build symbol table")
    RESOLVE = (5, "Resolve references")
    SHARED = (6, "Enrich shared schemas and effects")
    LEVELS = (7, "Compile levels and optimization data")
    EMIT = (8, "Emit compiled universe")

    def __init__(self, number: int, description: str) -> None:
        self.number = number
        self.description = description

    @property
    def label(self) -> str:
        """Canonical "Stage N: description" string for logs and diagnostics."""
        return f"Stage {self.number}: {self.description}"
