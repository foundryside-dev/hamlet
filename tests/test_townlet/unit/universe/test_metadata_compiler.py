"""Focused tests for the public-metadata compiler boundary.

The metadata DTOs carry only facts the compiler derives from declarations. The deleted
``AffordanceInfo.cost`` was filled by branching on a meter literally named ``money``
(PDR-0045); ``category``/``description``/``position``/``enabled`` and
``MeterInfo.critical``/``observable`` were constants. None had a reader.
"""

from __future__ import annotations

import dataclasses

import pytest

from townlet.config.affordances_v2_config import AffordanceParamConfig, AffordancesV2Config
from townlet.config.bars_v2_config import BarsV2Config
from townlet.config.bars_v2_config import MeterConfig as BarMeterConfig
from townlet.config.environment_config import EnvironmentConfig, EnvironmentConfigRoot
from townlet.config.environment_config import MeterConfig as EnvMeterConfig
from townlet.universe.compilers.metadata import MetadataCompiler
from townlet.universe.dto import AffordanceInfo, MeterInfo


def _metadata_compiler() -> MetadataCompiler:
    return MetadataCompiler(
        schema_version="test",
        compiler_version="test",
        compute_config_mtime=lambda _path: 0.0,
        build_cache_fingerprint=lambda _path: ("hash", "provenance"),
        get_git_sha=lambda: "sha",
    )


def _affordances(*named_costs: tuple[str, dict[str, float]]) -> AffordancesV2Config:
    return AffordancesV2Config.model_construct(
        affordances=[AffordanceParamConfig.model_construct(name=name, costs=costs) for name, costs in named_costs]
    )


def test_metadata_dtos_carry_no_constant_or_name_derived_fields() -> None:
    assert [f.name for f in dataclasses.fields(AffordanceInfo)] == ["id", "name"]
    assert [f.name for f in dataclasses.fields(MeterInfo)] == ["name", "index", "initial_value", "description"]


def test_affordance_metadata_is_declaration_ordered_identity() -> None:
    metadata = _metadata_compiler().build_affordance_metadata(_affordances(("REST", {}), ("WORK", {"energy": 0.1})))

    assert metadata.affordances == (AffordanceInfo(id="REST", name="REST"), AffordanceInfo(id="WORK", name="WORK"))


def test_affordance_metadata_does_not_depend_on_what_the_currency_meter_is_called() -> None:
    compiler = _metadata_compiler()

    as_money = compiler.build_affordance_metadata(_affordances(("EAT", {"money": 2.5})))
    as_credits = compiler.build_affordance_metadata(_affordances(("EAT", {"credits": 2.5})))

    assert as_money == as_credits


def _environment(*names: str) -> EnvironmentConfig:
    meters = [EnvMeterConfig.model_construct(name=name, description=f"{name} meter") for name in names]
    return EnvironmentConfig.model_construct(environment=EnvironmentConfigRoot.model_construct(meters=meters))


def _bars(**initials: float) -> BarsV2Config:
    return BarsV2Config.model_construct(meters=[BarMeterConfig.model_construct(name=n, initial=v) for n, v in initials.items()])


def test_meter_metadata_takes_initial_value_from_the_declared_bar() -> None:
    metadata = _metadata_compiler().build_meter_metadata(_environment("energy", "health"), _bars(health=0.5, energy=0.9))

    assert metadata.meters == (
        MeterInfo(name="energy", index=0, initial_value=0.9, description="energy meter"),
        MeterInfo(name="health", index=1, initial_value=0.5, description="health meter"),
    )


def test_meter_metadata_has_no_silent_initial_fallback() -> None:
    with pytest.raises(KeyError, match="health"):
        _metadata_compiler().build_meter_metadata(_environment("energy", "health"), _bars(energy=0.9))
