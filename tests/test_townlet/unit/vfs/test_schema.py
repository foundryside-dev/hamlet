"""Test VFS schema definitions (Cycle 1 - TDD RED phase).

This module tests Pydantic schemas for the Variable & Feature System (VFS).
All tests should FAIL initially (RED), then pass after implementation (GREEN).
"""

import pytest
from pydantic import ValidationError


class TestVariableDef:
    """Test VariableDef schema validation."""

    def test_scalar_variable_valid(self):
        """Scalar variable with all required fields."""
        from townlet.vfs.schema import VariableDef

        var = VariableDef(
            id="energy",
            scope="agent",
            type="scalar",
            lifetime="episode",
            readable_by=["agent", "engine"],
            writable_by=["engine"],
            default=1.0,
        )

        assert var.id == "energy"
        assert var.scope == "agent"
        assert var.type == "scalar"
        assert var.lifetime == "episode"
        assert var.readable_by == ["agent", "engine"]
        assert var.writable_by == ["engine"]
        assert var.default == 1.0

    def test_vecNf_variable_valid(self):  # noqa: N802
        """N-dimensional float vector with dims specified."""
        from townlet.vfs.schema import VariableDef

        var = VariableDef(
            id="position",
            scope="agent",
            type="vecNf",
            dims=2,
            lifetime="episode",
            readable_by=["agent"],
            writable_by=["engine"],
            default=[0.0, 0.0],
        )

        assert var.type == "vecNf"
        assert var.dims == 2
        assert var.default == [0.0, 0.0]

    def test_vecNi_variable_valid(self):  # noqa: N802
        """N-dimensional int vector with dims specified."""
        from townlet.vfs.schema import VariableDef

        var = VariableDef(
            id="grid_pos",
            scope="agent",
            type="vecNi",
            dims=2,
            lifetime="episode",
            readable_by=["agent"],
            writable_by=["engine"],
            default=[0, 0],
        )

        assert var.type == "vecNi"
        assert var.dims == 2

    def test_bool_variable_valid(self):
        """Boolean variable."""
        from townlet.vfs.schema import VariableDef

        var = VariableDef(
            id="is_tired",
            scope="agent",
            type="bool",
            lifetime="tick",
            readable_by=["agent"],
            writable_by=["engine"],
            default=False,
        )

        assert var.type == "bool"
        assert var.default is False

    def test_global_scope_valid(self):
        """Global scope variable (single value for all agents)."""
        from townlet.vfs.schema import VariableDef

        var = VariableDef(
            id="time_sin",
            scope="global",
            type="scalar",
            lifetime="tick",
            readable_by=["agent"],
            writable_by=["engine"],
            default=0.0,
        )

        assert var.scope == "global"

    def test_agent_private_scope_valid(self):
        """Agent-private scope (not observable by other agents)."""
        from townlet.vfs.schema import VariableDef

        var = VariableDef(
            id="home_position",
            scope="agent_private",
            type="vecNf",
            dims=2,
            lifetime="episode",
            readable_by=["agent"],  # Owner agent only
            writable_by=["engine"],
            default=[0.0, 0.0],
        )

        assert var.scope == "agent_private"

    def test_invalid_scope_rejected(self):
        """Invalid scope should raise ValidationError."""
        from townlet.vfs.schema import VariableDef

        with pytest.raises(ValidationError):
            VariableDef(
                id="test",
                scope="invalid_scope",
                type="scalar",
                lifetime="episode",
                readable_by=["agent"],
                writable_by=["engine"],
                default=0.0,
            )

    def test_invalid_type_rejected(self):
        """Invalid type should raise ValidationError."""
        from townlet.vfs.schema import VariableDef

        with pytest.raises(ValidationError):
            VariableDef(
                id="test",
                scope="agent",
                type="invalid_type",
                lifetime="episode",
                readable_by=["agent"],
                writable_by=["engine"],
                default=0.0,
            )

    def test_vecNf_without_dims_rejected(self):  # noqa: N802
        """vecNf type requires dims field."""
        from townlet.vfs.schema import VariableDef

        with pytest.raises(ValidationError, match="requires 'dims' field"):
            VariableDef(
                id="test",
                scope="agent",
                type="vecNf",
                # Missing dims!
                lifetime="episode",
                readable_by=["agent"],
                writable_by=["engine"],
                default=[0.0],
            )

    def test_scalar_with_dims_rejected(self):
        """scalar type should not have dims field."""
        from townlet.vfs.schema import VariableDef

        with pytest.raises(ValidationError, match="scalar.*dims"):
            VariableDef(
                id="test",
                scope="agent",
                type="scalar",
                dims=1,  # Should not be present!
                lifetime="episode",
                readable_by=["agent"],
                writable_by=["engine"],
                default=0.0,
            )


class TestNormalizationSpec:
    """Test NormalizationSpec schema validation."""

    def test_minmax_scalar_valid(self):
        """MinMax normalization with scalar bounds."""
        from townlet.vfs.schema import NormalizationSpec

        norm = NormalizationSpec(
            kind="minmax",
            min=0.0,
            max=1.0,
            clip=False,
        )

        assert norm.kind == "minmax"
        assert norm.min == 0.0
        assert norm.max == 1.0

    def test_minmax_vector_valid(self):
        """MinMax normalization with vector bounds."""
        from townlet.vfs.schema import NormalizationSpec

        norm = NormalizationSpec(
            kind="minmax",
            min=[0.0, 0.0],
            max=[7.0, 7.0],
            clip=False,
        )

        assert norm.kind == "minmax"
        assert norm.min == [0.0, 0.0]
        assert norm.max == [7.0, 7.0]

    def test_zscore_scalar_valid(self):
        """Z-score normalization with scalar parameters."""
        from townlet.vfs.schema import NormalizationSpec

        norm = NormalizationSpec(
            kind="zscore",
            mean=0.5,
            std=0.2,
        )

        assert norm.kind == "zscore"
        assert norm.mean == 0.5
        assert norm.std == 0.2

    def test_zscore_vector_valid(self):
        """Z-score normalization with vector parameters."""
        from townlet.vfs.schema import NormalizationSpec

        norm = NormalizationSpec(
            kind="zscore",
            mean=[0.5, 0.5],
            std=[0.2, 0.2],
        )

        assert norm.kind == "zscore"
        assert norm.mean == [0.5, 0.5]
        assert norm.std == [0.2, 0.2]

    def test_full_normalization_vocabulary_is_reachable_and_closed(self):
        """Every kind constructs with its required parameters, and the set is
        exactly the nine that exist.

        It was ten until `clipped_log_scaled` was folded into `log_scaled` +
        `clip=True` (hamlet-fba56feca5): clamping became a parameter, so a
        separate clamping member would have been two names for one behaviour.
        Enumerating the closed set here means adding a kind without meaning to
        fails, which is what PDR-0047 asks a closed vocabulary to guarantee.
        """
        from typing import get_args

        from townlet.vfs.schema import NormalizationSpec

        constructed = {
            "none": NormalizationSpec(kind="none"),
            "minmax": NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=False),
            "zscore": NormalizationSpec(kind="zscore", mean=0.5, std=0.2),
            "cyclical_sin_cos": NormalizationSpec(kind="cyclical_sin_cos", period=24.0),
            "one_hot": NormalizationSpec(kind="one_hot", categories=4),
            "binary": NormalizationSpec(kind="binary", threshold=0.5),
            "log_scaled": NormalizationSpec(kind="log_scaled", min=0.0, max=100.0, clip=False),
            "rank_scaled": NormalizationSpec(kind="rank_scaled"),
            "masked_value": NormalizationSpec(kind="masked_value", mask_value=-1.0, fill_value=0.0),
        }
        declared = set(get_args(NormalizationSpec.model_fields["kind"].annotation))

        assert set(constructed) == declared
        assert "clipped_log_scaled" not in declared
        assert all(spec.kind == kind for kind, spec in constructed.items())

    def test_minmax_without_min_rejected(self):
        """MinMax normalization requires min field."""
        from townlet.vfs.schema import NormalizationSpec

        with pytest.raises(ValidationError, match="requires 'min' parameter"):
            NormalizationSpec(
                kind="minmax",
                max=1.0,
                clip=False,
                # Missing min!
            )

    def test_zscore_without_mean_rejected(self):
        """Z-score normalization requires mean field."""
        from townlet.vfs.schema import NormalizationSpec

        with pytest.raises(ValidationError, match="requires 'mean' parameter"):
            NormalizationSpec(
                kind="zscore",
                std=0.2,
                # Missing mean!
            )

    def test_cyclical_sin_cos_requires_positive_period(self):
        """Cyclical normalization requires an explicit positive period."""
        from townlet.vfs.schema import NormalizationSpec

        with pytest.raises(ValidationError, match="positive 'period'"):
            NormalizationSpec(kind="cyclical_sin_cos", period=0.0)

    def test_one_hot_requires_at_least_two_categories(self):
        """One-hot normalization requires a useful category count."""
        from townlet.vfs.schema import NormalizationSpec

        with pytest.raises(ValidationError, match="at least 2 categories"):
            NormalizationSpec(kind="one_hot", categories=1)

    def test_binary_requires_threshold(self):
        """Binary normalization requires an explicit threshold."""
        from townlet.vfs.schema import NormalizationSpec

        with pytest.raises(ValidationError, match="requires 'threshold'"):
            NormalizationSpec(kind="binary")

    def test_log_scaled_requires_ordered_bounds(self):
        """Log-scaled normalization requires min < max."""
        from townlet.vfs.schema import NormalizationSpec

        with pytest.raises(ValidationError, match="requires 'min' < 'max'"):
            NormalizationSpec(kind="log_scaled", min=10.0, max=10.0, clip=False)

    def test_masked_value_requires_mask_and_fill(self):
        """Masked-value normalization requires both mask and fill values."""
        from townlet.vfs.schema import NormalizationSpec

        with pytest.raises(ValidationError, match="requires 'mask_value'"):
            NormalizationSpec(kind="masked_value", fill_value=0.0)


class TestObservationField:
    """Test ObservationField schema validation."""

    def test_scalar_observation_valid(self):
        """Scalar observation field (shape=[])."""
        from townlet.vfs.schema import ObservationField

        obs = ObservationField(
            id="obs_energy",
            source_variable="energy",
            exposed_to=["agent"],
            shape=[],
            semantic_type="custom",
        )

        assert obs.id == "obs_energy"
        assert obs.source_variable == "energy"
        assert obs.exposed_to == ["agent"]
        assert obs.shape == []

    def test_vector_observation_valid(self):
        """Vector observation field (shape=[N])."""
        from townlet.vfs.schema import ObservationField

        obs = ObservationField(
            id="obs_position",
            source_variable="position",
            exposed_to=["agent"],
            shape=[2],
            semantic_type="custom",
        )

        assert obs.shape == [2]

    def test_observation_with_normalization_valid(self):
        """Observation field with normalization spec."""
        from townlet.vfs.schema import NormalizationSpec, ObservationField

        obs = ObservationField(
            id="obs_energy",
            source_variable="energy",
            exposed_to=["agent"],
            shape=[],
            semantic_type="custom",
            normalization=NormalizationSpec(
                kind="minmax",
                min=0.0,
                max=1.0,
                clip=False,
            ),
        )

        assert obs.normalization is not None
        assert obs.normalization.kind == "minmax"

    def test_observation_without_normalization_valid(self):
        """Observation field without normalization (None)."""
        from townlet.vfs.schema import ObservationField

        obs = ObservationField(
            id="obs_money",
            source_variable="money",
            exposed_to=["agent"],
            shape=[],
            semantic_type="custom",
            normalization=None,
        )

        assert obs.normalization is None


class TestWriteSpec:
    """Test WriteSpec schema validation."""

    def test_write_spec_full_v11_contract_valid(self):
        """Write specification carries v1.1 conflict, phase, clamp, and telemetry metadata."""
        from townlet.vfs.schema import WriteSpec

        write = WriteSpec(
            variable_id="energy",
            expression="energy - 0.005",
            condition="agent_mask & action_is_move",
            composition="additive_delta",
            phase="action_costs",
            priority=10,
            clamp=[0.0, 1.0],
            telemetry_label="movement_energy_cost",
        )

        assert write.variable_id == "energy"
        assert write.expression == "energy - 0.005"
        assert write.condition == "agent_mask & action_is_move"
        assert write.composition == "additive_delta"
        assert write.phase == "action_costs"
        assert write.priority == 10
        assert write.clamp == (0.0, 1.0)
        assert write.telemetry_label == "movement_energy_cost"

    def test_write_spec_accepts_explicit_no_condition_or_clamp(self):
        """Optional condition and clamp are explicit fields, not hidden defaults."""
        from townlet.vfs.schema import WriteSpec

        write = WriteSpec(
            variable_id="money",
            expression="money + 10.0",
            condition=None,
            composition="overwrite",
            phase="action_effects",
            priority=0,
            clamp=None,
            telemetry_label="wage_credit",
        )

        assert write.expression == "money + 10.0"
        assert write.condition is None
        assert write.clamp is None

    def test_write_spec_requires_explicit_v11_metadata(self):
        """Old variable_id/expression-only writes fail loudly instead of remaining valid."""
        from townlet.vfs.schema import WriteSpec

        with pytest.raises(ValidationError) as exc_info:
            WriteSpec(
                variable_id="energy",
                expression="-0.005",
            )

        missing_fields = {error["loc"][0] for error in exc_info.value.errors() if error["type"] == "missing"}
        assert missing_fields == {
            "condition",
            "composition",
            "phase",
            "priority",
            "clamp",
            "telemetry_label",
        }

    def test_write_spec_empty_variable_id_rejected(self):
        """Empty variable_id should be rejected."""
        from townlet.vfs.schema import WriteSpec

        with pytest.raises(ValidationError):
            WriteSpec(
                variable_id="",  # Empty!
                expression="-0.005",
                condition=None,
                composition="additive_delta",
                phase="action_costs",
                priority=10,
                clamp=[0.0, 1.0],
                telemetry_label="movement_energy_cost",
            )

    def test_write_spec_empty_expression_rejected(self):
        """Empty expression should be rejected."""
        from townlet.vfs.schema import WriteSpec

        with pytest.raises(ValidationError):
            WriteSpec(
                variable_id="energy",
                expression="",  # Empty!
                condition=None,
                composition="additive_delta",
                phase="action_costs",
                priority=10,
                clamp=[0.0, 1.0],
                telemetry_label="movement_energy_cost",
            )

    def test_write_spec_rejects_unknown_composition_mode(self):
        """Composition mode is a closed vocabulary from the VFS transition spec."""
        from townlet.vfs.schema import WriteSpec

        with pytest.raises(ValidationError):
            WriteSpec(
                variable_id="energy",
                expression="-0.005",
                condition=None,
                composition="merge_somehow",
                phase="action_costs",
                priority=10,
                clamp=[0.0, 1.0],
                telemetry_label="movement_energy_cost",
            )

    def test_write_spec_rejects_negative_priority(self):
        """Priority is an explicit non-negative ordering key within a phase."""
        from townlet.vfs.schema import WriteSpec

        with pytest.raises(ValidationError):
            WriteSpec(
                variable_id="energy",
                expression="-0.005",
                condition=None,
                composition="additive_delta",
                phase="action_costs",
                priority=-1,
                clamp=[0.0, 1.0],
                telemetry_label="movement_energy_cost",
            )

    def test_write_spec_rejects_inverted_clamp_bounds(self):
        """Clamp bounds must be ordered low-to-high when present."""
        from townlet.vfs.schema import WriteSpec

        with pytest.raises(ValidationError):
            WriteSpec(
                variable_id="energy",
                expression="-0.005",
                condition=None,
                composition="additive_delta",
                phase="action_costs",
                priority=10,
                clamp=[1.0, 0.0],
                telemetry_label="movement_energy_cost",
            )
