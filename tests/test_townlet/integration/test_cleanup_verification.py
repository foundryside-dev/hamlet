"""Runtime consumes compiled products rather than reading authoring transports."""

from pathlib import Path

import pytest


@pytest.mark.parametrize("transport", ["variables.yaml", "effects.yaml"])
def test_environment_does_not_read_authoring_transport(transport):
    source = Path("src/townlet/environment/vectorized_env.py").read_text()
    assert transport not in source


def test_environment_does_not_rebuild_effect_catalog():
    source = Path("src/townlet/environment/vectorized_env.py").read_text()
    assert "EffectCatalog.from_config" not in source
