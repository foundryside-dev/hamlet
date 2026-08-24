"""YAML source map: file/line provenance for compiler diagnostics.

``build_pack_source_map`` parses a pack's YAML files with a line-annotating
loader (a PARALLEL load — the ``__line__`` keys it injects would violate the
DTOs' ``extra="forbid"`` if fed to them) and records pack-relative keys like
``levels/L1/drive.yaml:modifiers.energy_crisis``. Raise sites look keys up via
``SourceMap.lookup`` and fall back to their current file-level location when
the key is untracked.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

import yaml


class _LineNumberLoader(yaml.SafeLoader):
    """PyYAML loader that annotates mappings with their starting line numbers."""


def _construct_mapping(loader: _LineNumberLoader, node: yaml.nodes.MappingNode, deep: bool = False):
    mapping = yaml.SafeLoader.construct_mapping(loader, node, deep)
    mapping["__line__"] = node.start_mark.line + 1
    return mapping


_LineNumberLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)

# One trailing ``.segment`` or ``[index]`` of a location key, for suffix trimming.
_TRAILING_SEGMENT = re.compile(r"(\.[A-Za-z_0-9]+|\[\d+\])$")


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


def _load_yaml(file_path: Path):
    with open(file_path, encoding="utf-8") as handle:
        return yaml.load(handle, Loader=_LineNumberLoader)


def _record_named_entries(
    source_map: SourceMap,
    rel: str,
    file_path: Path,
    entries: object,
    *,
    id_keys: tuple[str, ...] = ("name", "id"),
) -> None:
    if not isinstance(entries, list):
        return
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        line = entry.get("__line__")
        for id_key in id_keys:
            identifier = entry.get(id_key)
            if identifier:
                source_map.record(f"{rel}:{identifier}", file_path, line)


def _record_drive(source_map: SourceMap, rel: str, file_path: Path) -> None:
    doc = _load_yaml(file_path)
    drive = doc.get("drive") if isinstance(doc, dict) else None
    if not isinstance(drive, dict):
        return
    modifiers = drive.get("modifiers")
    if isinstance(modifiers, dict):
        for name, cfg in modifiers.items():
            if isinstance(cfg, dict):
                source_map.record(f"{rel}:modifiers.{name}", file_path, cfg.get("__line__"))
    extrinsic = drive.get("extrinsic")
    if isinstance(extrinsic, dict):
        source_map.record(f"{rel}:extrinsic", file_path, extrinsic.get("__line__"))
        for list_key in ("bar_bonuses", "variable_bonuses"):
            entries = extrinsic.get(list_key)
            if isinstance(entries, list):
                for idx, entry in enumerate(entries):
                    if isinstance(entry, dict):
                        source_map.record(f"{rel}:extrinsic.{list_key}[{idx}]", file_path, entry.get("__line__"))
    shaping = drive.get("shaping")
    if isinstance(shaping, list):
        for idx, entry in enumerate(shaping):
            if isinstance(entry, dict):
                source_map.record(f"{rel}:shaping[{idx}]", file_path, entry.get("__line__"))


def _record_cascades(source_map: SourceMap, rel: str, file_path: Path, cascades: object) -> None:
    if not isinstance(cascades, list):
        return
    for entry in cascades:
        if not isinstance(entry, dict):
            continue
        source = entry.get("source")
        target = entry.get("target")
        if source and target:
            source_map.record(f"{rel}:{source}->{target}", file_path, entry.get("__line__"))


def build_pack_source_map(experiment_dir: Path) -> SourceMap:
    """Build the file:line map for a pack's high-value declaration surfaces.

    Tracked today: environment.yaml variables, vfs_profiles.yaml profile
    variables, and per level the affordance entries, bars cascades, and
    drive.yaml modifiers / extrinsic bonuses / shaping entries. Parse failures
    are ignored — provenance is best-effort enrichment, never a gate.
    """

    experiment_dir = Path(experiment_dir)
    source_map = SourceMap()

    env_path = experiment_dir / "environment.yaml"
    if env_path.exists():
        try:
            doc = _load_yaml(env_path)
            env = doc.get("environment") if isinstance(doc, dict) else None
            if isinstance(env, dict):
                _record_named_entries(source_map, "environment.yaml", env_path, env.get("variables"))
        except yaml.YAMLError:
            pass

    profiles_path = experiment_dir / "vfs_profiles.yaml"
    if profiles_path.exists():
        try:
            doc = _load_yaml(profiles_path)
            if isinstance(doc, dict):
                profiles = [doc.get("global_profile"), doc.get("agent_profile")]
                item_profiles = doc.get("item_profiles")
                if isinstance(item_profiles, list):
                    profiles.extend(item_profiles)
                for profile in profiles:
                    if isinstance(profile, dict):
                        _record_named_entries(source_map, "vfs_profiles.yaml", profiles_path, profile.get("variables"))
        except yaml.YAMLError:
            pass

    levels_dir = experiment_dir / "levels"
    if not levels_dir.is_dir():
        return source_map
    for level_dir in sorted(p for p in levels_dir.iterdir() if p.is_dir()):
        rel_level = f"levels/{level_dir.name}"

        aff_path = level_dir / "affordances.yaml"
        if aff_path.exists():
            try:
                doc = _load_yaml(aff_path)
                outer = doc.get("affordances") if isinstance(doc, dict) else None
                if isinstance(outer, dict):
                    _record_named_entries(source_map, f"{rel_level}/affordances.yaml", aff_path, outer.get("affordances"))
            except yaml.YAMLError:
                pass

        bars_path = level_dir / "bars.yaml"
        if bars_path.exists():
            try:
                doc = _load_yaml(bars_path)
                outer = doc.get("bars") if isinstance(doc, dict) else None
                if isinstance(outer, dict):
                    _record_cascades(source_map, f"{rel_level}/bars.yaml", bars_path, outer.get("cascades"))
            except yaml.YAMLError:
                pass

        drive_path = level_dir / "drive.yaml"
        if drive_path.exists():
            try:
                _record_drive(source_map, f"{rel_level}/drive.yaml", drive_path)
            except yaml.YAMLError:
                pass

    return source_map
