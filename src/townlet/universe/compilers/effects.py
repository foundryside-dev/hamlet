"""Effects-domain compiler boundary."""

from __future__ import annotations

from pathlib import Path

import yaml

from townlet.config.effects_config import EffectsConfig
from townlet.effects.catalog import EffectCatalog


class EffectsCompiler:
    """Compile effects catalogs against the active schema."""

    def compile_catalog(
        self,
        experiment_dir: Path,
        schema: dict[str, str],
        *,
        time_enabled: bool,
    ) -> EffectCatalog | None:
        """Load and compile effects catalog from experiment directory."""
        effects_path = experiment_dir / "effects.yaml"

        if not effects_path.exists():
            return None

        effects_data = yaml.safe_load(effects_path.read_text())
        effects_config = EffectsConfig(**effects_data)

        return EffectCatalog.from_config(effects_config, schema=schema, time_enabled=time_enabled)
