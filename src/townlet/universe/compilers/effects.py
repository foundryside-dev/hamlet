"""Effects-domain compiler boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from townlet.effects.catalog import EffectCatalog


class _EffectsDelegate(Protocol):
    def _compile_effects_catalog(
        self,
        experiment_dir: Path,
        schema: dict[str, str],
        *,
        time_enabled: bool,
    ) -> EffectCatalog | None: ...


class EffectsCompiler:
    """Compile effects catalogs against the active schema."""

    def __init__(self, delegate: _EffectsDelegate) -> None:
        self._delegate = delegate

    def compile_catalog(
        self,
        experiment_dir: Path,
        schema: dict[str, str],
        *,
        time_enabled: bool,
    ) -> EffectCatalog | None:
        return self._delegate._compile_effects_catalog(experiment_dir, schema, time_enabled=time_enabled)
