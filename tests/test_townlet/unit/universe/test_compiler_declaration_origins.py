"""Compiler-domain refusals retain discovery origins after transport relocation."""

from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from townlet.universe.compiler import UniverseCompiler
from townlet.universe.compilers.metadata import MetadataCompiler
from townlet.universe.compilers.optimization import OptimizationCompiler
from townlet.universe.errors import CompilationError
from townlet.universe.raw_configs_v21 import RawConfigsV21


@pytest.fixture
def relocated_pack(tmp_path: Path) -> Path:
    pack = tmp_path / "pack"
    shutil.copytree(Path("configs/test/model_config"), pack)
    for original, relocated in (
        ("experiment.yaml", "definitions/project.yml"),
        ("levels/L0_test/curriculum.yaml", "levels/L0_test/scene/timing.yml"),
        ("levels/L0_test/bars.yaml", "levels/L0_test/mechanics/resources.yml"),
        ("levels/L0_test/affordances.yaml", "levels/L0_test/mechanics/opportunities.yml"),
    ):
        target = pack / relocated
        target.parent.mkdir(parents=True, exist_ok=True)
        (pack / original).rename(target)
    return pack


def _metadata_compiler() -> MetadataCompiler:
    return MetadataCompiler(
        schema_version="test",
        compiler_version="test",
        compute_config_mtime=lambda _: 0.0,
        build_cache_fingerprint=lambda _: ("transport", "provenance"),
        get_git_sha=lambda: "test",
    )


@pytest.mark.parametrize("failure", ["version", "day_length"])
def test_metadata_refusals_name_relocated_declaration(relocated_pack: Path, failure: str) -> None:
    raw = RawConfigsV21.from_experiment_dir(relocated_pack)
    compiled = UniverseCompiler().compile(relocated_pack, primary_level="L0_test", use_cache=False)
    level = compiled.get_level("L0_test")
    assert raw.source_map is not None
    if failure == "version":
        raw.experiment.experiment.version = ""
        key = "experiment:version"
        expected_code = "UAC-META-VERSION"
    else:
        level.curriculum.curriculum.active_temporal = True
        level.curriculum.curriculum.day_length = None
        key = "levels/L0_test/curriculum:day_length"
        expected_code = "UAC-META-DAY-LENGTH"

    with pytest.raises(CompilationError) as raised:
        _metadata_compiler().build_universe_metadata(
            raw,
            level,
            experiment_dir=relocated_pack,
            config_hash="transport",
            config_mtime=0.0,
        )

    issue = raised.value.issues[0]
    assert issue.code == expected_code
    assert issue.location == raw.source_map.lookup(key)
    assert issue.location is not None and issue.location.rsplit(":", 1)[-1].isdigit()
    assert ".yaml" not in issue.message


@pytest.mark.parametrize("failure", ["cascade", "modulation_bar", "modulation_affordance"])
def test_optimization_refusals_name_relocated_entry(relocated_pack: Path, failure: str) -> None:
    raw = RawConfigsV21.from_experiment_dir(relocated_pack)
    compiled = UniverseCompiler().compile(relocated_pack, primary_level="L0_test", use_cache=False)
    level = compiled.get_level("L0_test")
    assert raw.source_map is not None
    meter_metadata = level.meter_metadata
    affordance_metadata = level.affordance_metadata
    if failure == "cascade":
        cascade = level.bars.cascades[0]
        key = f"levels/L0_test/bars:{cascade.source}->{cascade.target}"
        meter_metadata = replace(meter_metadata, meters=tuple(m for m in meter_metadata.meters if m.name != cascade.source))
        expected_code = "UAC-OPT-CASCADE"
    else:
        modulation = level.affordances.modulations[0]
        key = "levels/L0_test/affordances:modulations[0]"
        if failure == "modulation_bar":
            meter_metadata = replace(meter_metadata, meters=tuple(m for m in meter_metadata.meters if m.name != modulation.bar))
            level.bars.cascades.clear()
        else:
            target = modulation.affordances[0]
            affordance_metadata = replace(
                affordance_metadata, affordances=tuple(a for a in affordance_metadata.affordances if a.name != target)
            )
        expected_code = "UAC-OPT-MODULATION"

    with pytest.raises(CompilationError) as raised:
        OptimizationCompiler().build_optimization_data(
            level.bars,
            level.affordances,
            meter_metadata,
            affordance_metadata,
            level.action_metadata,
            source_map=raw.source_map,
            level_name="L0_test",
        )

    issue = raised.value.issues[0]
    assert issue.code == expected_code
    assert issue.location == raw.source_map.lookup(key)
    assert issue.location is not None and issue.location.rsplit(":", 1)[-1].isdigit()
    assert ".yaml" not in issue.message
