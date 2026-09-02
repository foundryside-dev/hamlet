"""Focused tests for the public-metadata compiler boundary."""

from __future__ import annotations

import pytest

from townlet.config.affordances_v2_config import AffordanceParamConfig, AffordancesV2Config
from townlet.universe.compilers.metadata import MetadataCompiler


def _metadata_compiler() -> MetadataCompiler:
    return MetadataCompiler(
        schema_version="test",
        compiler_version="test",
        compute_config_mtime=lambda _path: 0.0,
        build_cache_fingerprint=lambda _path: ("hash", "provenance"),
        get_git_sha=lambda: "sha",
    )


def _affordances_with_costs(costs: dict[str, float]) -> AffordancesV2Config:
    affordance = AffordanceParamConfig.model_construct(name="REST", costs=costs)
    return AffordancesV2Config.model_construct(affordances=[affordance])


@pytest.mark.parametrize(("costs", "expected"), (({}, 0.0), ({"energy": 0.25}, 0.0), ({"money": 2.5}, 2.5)))
def test_affordance_metadata_uses_money_key_or_explicit_semantic_zero(costs: dict[str, float], expected: float) -> None:
    metadata = _metadata_compiler().build_affordance_metadata(_affordances_with_costs(costs))

    assert metadata.affordances[0].cost == expected


def test_affordance_metadata_has_no_fallback_for_missing_canonical_costs() -> None:
    affordance = AffordanceParamConfig.model_construct(name="REST")
    del affordance.costs
    config = AffordancesV2Config.model_construct(affordances=[affordance])

    with pytest.raises(AttributeError, match="costs"):
        _metadata_compiler().build_affordance_metadata(config)
