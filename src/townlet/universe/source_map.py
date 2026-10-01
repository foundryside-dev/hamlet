"""Source provenance keyed by declaration family, scope and entity identity."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path

_TRAILING_SEGMENT = re.compile(r"(\.[A-Za-z_0-9]+|\[\d+\])$")


def variable_location_key(profile: str | None, identifier: str) -> str:
    """Encode canonical variable identity without ambiguous name separators."""
    return f"variables:{json.dumps((profile, identifier), separators=(',', ':'))}"


class SourceMap:
    """Lightweight registry of config keys to file/line metadata."""

    def __init__(self) -> None:
        self._locations: dict[str, tuple[str, int | None]] = {}

    def record(self, key: str, file_path: Path, line: int | None) -> None:
        self._locations[key] = (str(file_path), line)

    def lookup(self, location: str) -> str | None:
        """Return a formatted `path:line` string for a location key if tracked.

        Falls back through progressively shorter keys: first colon-delimited
        prefixes (``file:id:section`` -> ``file:id``), then trailing ``.attr``
        / ``[idx]`` segments (``file:shaping[0].time_ranges[1]`` ->
        ``file:shaping[0]``).
        """

        parts = location.split(":")
        if len(parts) <= 1:
            return self._format(location)

        for end in range(len(parts), 0, -1):
            candidate = ":".join(parts[:end])
            while True:
                formatted = self._format(candidate)
                if formatted:
                    return formatted
                trimmed = _TRAILING_SEGMENT.sub("", candidate)
                if trimmed == candidate:
                    break
                candidate = trimmed
        return None

    def _format(self, key: str) -> str | None:
        if key not in self._locations:
            return None
        path, line = self._locations[key]
        if line is None:
            return path
        return f"{path}:{line}"

    def bulk_record(self, entries: Iterable[tuple[str, Path, int | None]]) -> None:
        for key, path, line in entries:
            self.record(key, path, line)


def locate(source_map: SourceMap | None, key: str, fallback: str | None = None) -> str:
    """Resolve ``key`` to ``path:line`` where tracked, else the fallback (or the key)."""

    if source_map is not None:
        located = source_map.lookup(key)
        if located is not None:
            return located
    return fallback if fallback is not None else key
