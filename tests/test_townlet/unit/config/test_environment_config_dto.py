"""Tests for EnvironmentConfig DTO (v2.1 environment.yaml)."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from townlet.config.environment_config import EnvironmentConfig


class TestEnvironmentConfigLoading:
    """Test loading EnvironmentConfig from real v2.1 YAML."""

    def test_load_from_model_config_environment_yaml(self):
        """Load environment.yaml from the canonical model_config pack."""
        env_path = Path("configs/test/model_config/environment.yaml")
        assert env_path.exists(), f"environment.yaml not found at {env_path}"

        config = EnvironmentConfig.from_yaml(env_path)
        root = config.environment

        # Basic shape checks
        assert root.version == "1.0"
        assert len(root.meters) == 8
        assert len(root.cascade_graph) > 0
        assert len(root.modulation_graph) > 0
        assert len(root.affordances) >= 1
        assert len(root.variables) >= 1
        assert len(root.cues) >= 1

        # Meters and affordances match expected vocabulary
        meter_names = {m.name for m in root.meters}
        assert {"energy", "health", "satiation", "hygiene", "money", "fitness", "mood", "social"} <= meter_names

        affordance_names = {a.name for a in root.affordances}
        assert {"EAT", "SLEEP", "WORK"}.issubset(affordance_names)

        # At least one cascade and modulation edge references valid meters/affordances
        cascade = next(c for c in root.cascade_graph if c.source == "satiation" and c.target == "health")
        assert "hunger" in cascade.description.lower()

        modulation = next(m for m in root.modulation_graph if m.bar == "energy")
        assert "WORK" in {a.upper() for a in modulation.affordances}

    def test_environment_config_bars_and_variables_are_consistent(self):
        """Meters in environment.yaml should align with VFS variables."""
        env_path = Path("configs/default_curriculum/environment.yaml")
        assert env_path.exists(), f"environment.yaml not found at {env_path}"

        config = EnvironmentConfig.from_yaml(env_path)
        root = config.environment

        meter_names = {m.name for m in root.meters}
        variable_names = {v.name for v in root.variables}

        # All meter-backed variables should have corresponding meters
        assert "deficit_energy" in variable_names
        assert "deficit_satiation" in variable_names
        assert "time_since_last_eat" in variable_names
        assert "time_since_last_sleep" in variable_names

        # Simple consistency check: variables must reference valid meter concepts
        assert "energy" in meter_names
        assert "satiation" in meter_names

    def test_environment_config_rejects_extra_meter_fields(self, tmp_path: Path):
        """Extra fields in meter definitions should be rejected (extra=forbid)."""
        env_yaml = tmp_path / "environment.yaml"
        env_yaml.write_text("""
environment:
  version: "1.0"
  meters:
    - name: energy
      description: "Energy"
      range_type: normalized
      extra_field: "not allowed"
  cascade_graph: []
  modulation_graph: []
  affordances: []
  variables: []
  cues: []
""")

        with pytest.raises(ValidationError):
            EnvironmentConfig.from_yaml(env_yaml)

    def test_variable_normalization_range_requires_two_values(self, tmp_path: Path):
        """Normalization.range must contain exactly two values [min, max]."""
        env_yaml = tmp_path / "environment.yaml"
        env_yaml.write_text("""
environment:
  version: "1.0"
  meters:
    - name: energy
      description: "Energy"
      range_type: normalized
  cascade_graph: []
  modulation_graph: []
  affordances: []
  variables:
    - name: deficit_energy
      type: scalar
      dims: 1
      scope: agent
      description: "How far below target energy"
      normalization:
        method: normalize
        range: [0.0]
  cues: []
""")

        with pytest.raises(ValidationError):
            EnvironmentConfig.from_yaml(env_yaml)


# --- hamlet-1dba1910c0: the normalization vocabulary must be honest ----------
#
# `clip` and `normalize` used to be four-member siblings that compiled to
# byte-identical minmax specs, and `minmax` is (v-min)/(max-min) — pure
# rescaling. So `method: clip` promised clamping and delivered none: an author
# declaring clip on [0,1] and feeding 7.0 got 7.0 back. `none` was in the
# approved vocabulary and rejected unconditionally by the compiler. Both are
# the ambiguity PDR-0047 rule 1 forbids: a closed vocabulary whose members must
# be distinct and must do what their names say.


def test_removed_vocabulary_members_are_rejected() -> None:
    """`clip` and `none` are gone from the authoring vocabulary, and the error
    names what IS allowed — an author who wrote either must be told, not
    silently given rescaling under a clamping name."""
    from townlet.config.environment_config import NormalizationConfig

    for dead in ("clip", "none"):
        with pytest.raises(ValidationError) as excinfo:
            NormalizationConfig(method=dead, range=[0.0, 1.0])
        message = str(excinfo.value)
        assert "normalize" in message and "standardize" in message


def test_every_surviving_member_compiles_to_a_distinct_spec() -> None:
    """The point of the removal: two names must never mean one behaviour."""
    from townlet.config.environment_config import NormalizationConfig
    from townlet.universe.compilers.observation import ObservationCompiler

    convert = ObservationCompiler._convert_normalization
    specs = {
        "normalize": convert("v", NormalizationConfig(method="normalize", range=[0.0, 1.0], clip=False)),
        "standardize": convert("v", NormalizationConfig(method="standardize", range=[0.0, 1.0], mean=0.5, std=0.25)),
    }
    assert specs["normalize"].kind != specs["standardize"].kind
    assert len({s.kind for s in specs.values()}) == len(specs)


def test_normalize_rescales_and_clamps_only_when_the_author_says_so() -> None:
    """REPLACED, not relaxed — as its predecessor instructed.

    The old test pinned that `normalize` lets out-of-range values through and
    said: *"if this assertion ever starts failing because values ARE clamped,
    the vocabulary gained a member and this test must be replaced rather than
    relaxed."* It gained a PARAMETER instead (`hamlet-fba56feca5`), so both
    halves are now pinned: the un-clamped behaviour is unchanged, and clamping
    is reachable — the thing the `clip` member falsely promised and never did.
    """
    import torch

    from townlet.config.environment_config import NormalizationConfig
    from townlet.universe.compilers.observation import ObservationCompiler
    from townlet.vfs.observation_builder import apply_normalization

    values = torch.tensor([-5.0, 0.0, 0.5, 1.0, 7.0])

    loose = ObservationCompiler._convert_normalization("v", NormalizationConfig(method="normalize", range=[0.0, 1.0], clip=False))
    assert apply_normalization(values, loose).tolist() == [-5.0, 0.0, 0.5, 1.0, 7.0]

    clamped = ObservationCompiler._convert_normalization("v", NormalizationConfig(method="normalize", range=[0.0, 1.0], clip=True))
    assert apply_normalization(values, clamped).tolist() == [0.0, 0.0, 0.5, 1.0, 1.0]


def test_clip_must_be_declared_and_only_where_it_applies() -> None:
    """No-Defaults, both directions: omitting `clip` on `normalize` is a compile
    error rather than a silent false, and offering it to `standardize` — which
    has no range to clamp against — is rejected rather than ignored.
    """
    from townlet.config.environment_config import NormalizationConfig

    with pytest.raises(ValidationError, match="requires an explicit 'clip'"):
        NormalizationConfig(method="normalize", range=[0.0, 1.0])

    with pytest.raises(ValidationError, match="does not accept 'clip'"):
        NormalizationConfig(method="standardize", range=[0.0, 1.0], mean=0.5, std=0.2, clip=True)


def test_the_deleted_clamping_member_stays_deleted() -> None:
    """`clipped_log_scaled` clamped AND log-scaled — the only clamping member,
    so a plain clamp was unreachable. With `clip` a parameter, keeping it would
    be PDR-0053 shape #3 (two members, one behaviour) authored by hand while
    cleaning up that very shape. `log_scaled` + `clip=True` is exactly what it
    did, and the pair below pins that equivalence.
    """
    import torch

    from townlet.vfs.observation_builder import apply_normalization
    from townlet.vfs.schema import NormalizationSpec

    with pytest.raises(ValidationError):
        NormalizationSpec(kind="clipped_log_scaled", min=0.0, max=99.0, clip=True)

    out = apply_normalization(
        torch.tensor([-10.0, 999.0]),
        NormalizationSpec(kind="log_scaled", min=0.0, max=99.0, clip=True),
    )
    assert out.tolist() == [0.0, 1.0]
