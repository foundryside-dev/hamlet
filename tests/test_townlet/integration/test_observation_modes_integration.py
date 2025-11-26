from pathlib import Path

from tests.test_townlet.helpers.config_builder import mutate_stratum_yaml, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


def test_max_compact_drops_masked_fields(tmp_path: Path):
    config_dir = prepare_config_dir(tmp_path, name="obs_compact")
    compiler = UniverseCompiler()

    baseline = compiler.compile(config_dir, use_cache=False)
    baseline_fields = baseline.observation_spec.fields
    masked = [f for f in baseline_fields if "MASKED" in (f.description or "")]
    assert masked, "Fixture should produce at least one masked observation field to test compaction."
    unmasked = [f for f in baseline_fields if "MASKED" not in (f.description or "")]
    expected_dims = sum(f.dims for f in unmasked)

    mutate_stratum_yaml(
        config_dir,
        lambda data: data["stratum"].update({"observation_mode": {"mode": "max_compact"}}),
    )

    compact = compiler.compile(config_dir, use_cache=False)
    assert [f.name for f in compact.observation_spec.fields] == [f.name for f in unmasked]
    assert compact.observation_spec.total_dims == expected_dims


def test_full_manual_selects_subset(tmp_path: Path):
    config_dir = prepare_config_dir(tmp_path, name="obs_manual")
    compiler = UniverseCompiler()

    baseline = compiler.compile(config_dir, use_cache=False)
    baseline_fields = list(baseline.observation_spec.fields)
    assert len(baseline_fields) >= 2, "Fixture should expose multiple observation fields."

    includes = [baseline_fields[0].name, baseline_fields[1].name]
    expected_dims = sum(f.dims for f in baseline_fields if f.name in includes)

    mutate_stratum_yaml(
        config_dir,
        lambda data: data["stratum"].update({"observation_mode": {"mode": "full_manual", "include_fields": includes}}),
    )

    manual = compiler.compile(config_dir, use_cache=False)
    assert [f.name for f in manual.observation_spec.fields] == includes
    assert manual.observation_spec.total_dims == expected_dims
