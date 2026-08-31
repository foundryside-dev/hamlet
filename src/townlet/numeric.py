"""Numeric representation boundaries shared by compiler and runtime code."""

from __future__ import annotations

import math
import struct


def require_float32(value: float, *, field: str) -> float:
    """Return the exact float32 value, refusing values with no runtime meaning."""
    try:
        authored = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} must be finite and representable as float32, got {value!r}") from exc

    if not math.isfinite(authored):
        raise ValueError(f"{field} must be finite and representable as float32, got {value!r}")

    try:
        encoded = struct.pack(">f", authored)
    except OverflowError as exc:
        raise ValueError(f"{field} must be finite and representable as float32, got {value!r}") from exc

    runtime_value = float(struct.unpack(">f", encoded)[0])
    if not math.isfinite(runtime_value):
        raise ValueError(f"{field} must be finite and representable as float32, got {value!r}")
    if authored != 0.0 and runtime_value == 0.0:
        raise ValueError(f"{field} must not underflow to zero in float32, got {value!r}")

    return runtime_value


__all__ = ["require_float32"]
