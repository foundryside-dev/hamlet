"""Action-domain compiler boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from townlet.config.actions_config import ActionsConfig
from townlet.config.affordances_v2_config import AffordancesV2Config
from townlet.config.items_config import ItemsCatalogConfig
from townlet.config.stratum_config import StratumConfig
from townlet.config.training_v2_config import TrainingV2Config
from townlet.universe.dto import ActionSpaceMetadata


class _ActionDelegate(Protocol):
    def _build_action_space_metadata(
        self,
        stratum: StratumConfig,
        actions: ActionsConfig,
        training: TrainingV2Config,
        affordances: AffordancesV2Config,
        items: ItemsCatalogConfig | None,
        config_pack_path: Path,
    ) -> ActionSpaceMetadata: ...


class ActionCompiler:
    """Compile runtime action metadata."""

    def __init__(self, delegate: _ActionDelegate) -> None:
        self._delegate = delegate

    def build_action_space_metadata(
        self,
        stratum: StratumConfig,
        actions: ActionsConfig,
        training: TrainingV2Config,
        affordances: AffordancesV2Config,
        items: ItemsCatalogConfig | None,
        config_pack_path: Path,
    ) -> ActionSpaceMetadata:
        return self._delegate._build_action_space_metadata(stratum, actions, training, affordances, items, config_pack_path)
