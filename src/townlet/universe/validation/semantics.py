"""Strict semantic helpers for v2.1 universe compilation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def select_primary_level(levels: Mapping[str, Any], requested: str | None) -> str:
    """Resolve the primary level, rejecting unknown explicit names."""
    if requested is None:
        return sorted(levels.keys())[0]
    if requested not in levels:
        raise ValueError(f"Primary level '{requested}' not found. Available: {list(levels.keys())}")
    return requested
