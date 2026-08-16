"""Test ObservationField schema extensions for semantic grouping."""

import pytest
from pydantic import ValidationError

from townlet.vfs.schema import ObservationField
from townlet.vfs.semantic_type import SEMANTIC_TYPES


class TestSemanticTypeField:
    def test_semantic_type_is_required(self):
        """semantic_type is part of the field's identity (observation_schema_hash) and names its
        group slice, so it is never defaulted (PDR-0047; it used to default to 'custom')."""
        with pytest.raises(ValidationError) as exc_info:
            ObservationField(
                id="test_field",
                source_variable="test_var",
                exposed_to=["agent"],
                shape=[1],
                normalization=None,
            )
        assert "semantic_type" in str(exc_info.value).lower()

    def test_semantic_type_accepts_every_member_of_the_one_vocabulary(self):
        for semantic_type in sorted(SEMANTIC_TYPES):
            field = ObservationField(
                id=f"test_{semantic_type}",
                source_variable="test_var",
                exposed_to=["agent"],
                shape=[1],
                normalization=None,
                semantic_type=semantic_type,
            )
            assert field.semantic_type == semantic_type

    def test_semantic_type_rejects_invalid_values(self):
        """semantic_type should reject values not in the closed vocabulary."""
        with pytest.raises(ValidationError) as exc_info:
            ObservationField(
                id="test_field",
                source_variable="test_var",
                exposed_to=["agent"],
                shape=[1],
                normalization=None,
                semantic_type="invalid_type",  # Not in the vocabulary
            )

        error = str(exc_info.value)
        assert "semantic_type" in error.lower()


class TestCurriculumActiveField:
    def test_curriculum_active_defaults_to_true(self):
        """curriculum_active should default to True if not specified."""
        field = ObservationField(
            id="test_field",
            source_variable="test_var",
            exposed_to=["agent"],
            shape=[1],
            normalization=None,
            semantic_type="custom",
        )
        assert field.curriculum_active is True

    def test_curriculum_active_accepts_false(self):
        """curriculum_active should accept False (for padding dims)."""
        field = ObservationField(
            id="test_field",
            source_variable="test_var",
            exposed_to=["agent"],
            shape=[1],
            normalization=None,
            semantic_type="custom",
            curriculum_active=False,
        )
        assert field.curriculum_active is False

    def test_curriculum_active_accepts_bool_like_values(self):
        """curriculum_active should coerce bool-like values (Pydantic behavior)."""
        # Pydantic coerces strings like "yes", "true", "1" to bool
        field = ObservationField(
            id="test_field",
            source_variable="test_var",
            exposed_to=["agent"],
            shape=[1],
            normalization=None,
            semantic_type="custom",
            curriculum_active="yes",  # Coerced to True
        )
        assert field.curriculum_active is True
