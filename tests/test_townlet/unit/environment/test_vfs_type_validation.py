"""Tests for VFS type validation in vectorized environment."""

import pytest

from townlet.environment.vectorized_env import _VALID_VFS_TYPES, _normalize_vfs_type


class TestNormalizeVfsType:
    """Tests for _normalize_vfs_type helper function."""

    def test_normalizes_int_to_scalar(self):
        """'int' should be normalized to 'scalar'."""
        assert _normalize_vfs_type("int", "test_var") == "scalar"

    def test_normalizes_float_to_scalar(self):
        """'float' should be normalized to 'scalar'."""
        assert _normalize_vfs_type("float", "test_var") == "scalar"

    def test_preserves_scalar(self):
        """'scalar' should pass through unchanged."""
        assert _normalize_vfs_type("scalar", "test_var") == "scalar"

    def test_preserves_bool(self):
        """'bool' should pass through unchanged."""
        assert _normalize_vfs_type("bool", "test_var") == "bool"

    def test_preserves_tensor_types(self):
        """Tensor types should pass through unchanged."""
        assert _normalize_vfs_type("tensor1d", "test_var") == "tensor1d"
        assert _normalize_vfs_type("tensor2d", "test_var") == "tensor2d"
        assert _normalize_vfs_type("tensor3d", "test_var") == "tensor3d"
        assert _normalize_vfs_type("tensorNd", "test_var") == "tensorNd"

    def test_preserves_reference_types(self):
        """Reference types should pass through unchanged."""
        assert _normalize_vfs_type("agent_ref", "test_var") == "agent_ref"
        assert _normalize_vfs_type("item_ref", "test_var") == "item_ref"

    def test_rejects_invalid_type_with_clear_error(self):
        """Invalid types should raise ValueError with helpful message."""
        with pytest.raises(ValueError) as excinfo:
            _normalize_vfs_type("scaler", "motivation")  # Common typo

        error_msg = str(excinfo.value)
        assert "scaler" in error_msg  # Shows the bad type
        assert "motivation" in error_msg  # Shows which variable
        assert "Valid types" in error_msg  # Shows valid options

    def test_rejects_unknown_type(self):
        """Unknown types should raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported VFS variable type"):
            _normalize_vfs_type("integer", "count")

    def test_rejects_empty_string(self):
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported VFS variable type"):
            _normalize_vfs_type("", "test_var")

    def test_valid_types_constant_complete(self):
        """_VALID_VFS_TYPES should contain all expected types."""
        expected = {"scalar", "bool", "tensor1d", "tensor2d", "tensor3d", "tensorNd", "agent_ref", "item_ref"}
        assert _VALID_VFS_TYPES == expected
