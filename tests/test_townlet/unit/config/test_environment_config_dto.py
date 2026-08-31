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

    def test_default_curriculum_declares_no_writerless_variables(self):
        """The shipped pack must not declare observation variables nothing writes.

        deficit_energy / deficit_satiation / time_since_last_eat /
        time_since_last_sleep were declared with no runtime writer, so agents
        observed frozen zeros in slots the ABI claimed were live
        (hamlet-dc8f887cd5). Deleted per zero-backwards-compat; a declaration
        may return only together with the authoring surface that drives it.
        """
        env_path = Path("configs/default_curriculum/environment.yaml")
        assert env_path.exists(), f"environment.yaml not found at {env_path}"

        config = EnvironmentConfig.from_yaml(env_path)
        root = config.environment

        variable_names = {v.name for v in root.variables}
        assert variable_names == set(), f"writerless variables declared: {variable_names}"

        meter_names = {m.name for m in root.meters}
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
      range_type:
        kind: minmax
        clip: true
      extra_field: "not allowed"
  cascade_graph: []
  modulation_graph: []
  affordances: []
  variables: []
  cues: []
""")

        with pytest.raises(ValidationError):
            EnvironmentConfig.from_yaml(env_yaml)


def test_meter_range_type_is_exactly_the_bounded_two_lane_vocabulary() -> None:
    """The token ABI is fixed at two bounded value lanes; the meter DTO must not
    continue accepting declarations that cannot truthfully enter that ABI."""
    from townlet.config.environment_config import MeterConfig

    admitted = (
        {"kind": "minmax", "clip": True},
        {"kind": "log_scaled", "clip": True},
        {"kind": "cyclical_sin_cos", "period": 24.0},
        {"kind": "binary", "threshold": 0.5},
    )
    assert [MeterConfig(name="m", description="d", range_type=spec).range_type.kind for spec in admitted] == [
        "minmax",
        "log_scaled",
        "cyclical_sin_cos",
        "binary",
    ]

    for deleted in (
        {"kind": "none"},
        {"kind": "zscore", "mean": 0.0, "std": 1.0},
        {"kind": "one_hot", "categories": 4},
        {"kind": "rank_scaled"},
        {"kind": "masked_value", "mask_value": -1.0, "fill_value": 0.0},
    ):
        with pytest.raises(ValidationError):
            MeterConfig(name="m", description="d", range_type=deleted)

    for unclipped in ("minmax", "log_scaled"):
        with pytest.raises(ValidationError):
            MeterConfig(name="m", description="d", range_type={"kind": unclipped, "clip": False})


@pytest.mark.parametrize(
    "range_type",
    (
        {"kind": "binary", "threshold": float("nan")},
        {"kind": "binary", "threshold": float("inf")},
        {"kind": "cyclical_sin_cos", "period": float("inf")},
    ),
)
def test_meter_range_type_rejects_non_finite_parameters(range_type: dict[str, object]) -> None:
    from townlet.config.environment_config import MeterConfig

    with pytest.raises(ValidationError):
        MeterConfig(name="m", description="d", range_type=range_type)


def test_variable_normalization_range_requires_two_values(tmp_path: Path):
    """Normalization.range must contain exactly two values [min, max]."""
    env_yaml = tmp_path / "environment.yaml"
    env_yaml.write_text("""
environment:
  version: "1.0"
  meters:
    - name: energy
      description: "Energy"
      range_type:
        kind: minmax
        clip: true
  cascade_graph: []
  modulation_graph: []
  affordances: []
  variables:
    - name: deficit_energy
      type: scalar
      dims: 1
      scope: agent
      description: "How far below target energy"
      semantic_type: custom
      normalization:
        method: normalize
        clip: true
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


def _normalizer(spec):
    """One-element `CompiledValueNormalizer` — the live normalization ABI since the cut."""
    import torch

    from townlet.environment.token_publishers import CompiledValueNormalizer

    return CompiledValueNormalizer([("v", spec, 0, 1)], torch.device("cpu"))


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

    # The compiler's job is to carry the author's `clip` through into the VFS spec
    # UNCHANGED. What clamps is the live normalizer (`CompiledValueNormalizer`), and
    # since the unit-3 cut it only ever sees clip: true — boundedness is certified at
    # exposure, so an unclipped minmax refuses before it can reach a token.
    loose = ObservationCompiler._convert_normalization("v", NormalizationConfig(method="normalize", range=[0.0, 1.0], clip=False))
    assert loose.kind == "minmax" and loose.clip is False
    clamped = ObservationCompiler._convert_normalization("v", NormalizationConfig(method="normalize", range=[0.0, 1.0], clip=True))
    assert clamped.kind == "minmax" and clamped.clip is True

    normalizer = _normalizer(clamped)
    values = torch.tensor([[-5.0], [0.0], [0.5], [1.0], [7.0]])
    assert normalizer.apply(values)[:, 0, 0].tolist() == [0.0, 0.0, 0.5, 1.0, 1.0]


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

    from townlet.vfs.schema import NormalizationSpec

    with pytest.raises(ValidationError):
        NormalizationSpec(kind="clipped_log_scaled", min=0.0, max=99.0, clip=True)

    normalizer = _normalizer(NormalizationSpec(kind="log_scaled", min=0.0, max=99.0, clip=True))
    out = normalizer.apply(torch.tensor([[-10.0], [999.0]]))[:, 0, 0]
    assert out.tolist() == [0.0, 1.0]
