"""Unit tests for checkpoint validation, action labels, and error handling.

This module covers edge cases not exercised by integration tests:
- Legacy checkpoint detection (missing position_dim)
- Position dimension mismatch validation
- Action labels flowing from compiler metadata (custom + preset) rather than runtime file loading
"""

import shutil
from pathlib import Path

import pytest
import yaml

from tests.test_townlet.utils import builders
from tests.test_townlet.utils.builders import make_vectorized_env_from_pack


@pytest.fixture(autouse=True)
def invalidate_compiled_cache(test_config_pack_path):
    """Force recompilation so action labels from the compiler are present."""
    pack_path = Path(test_config_pack_path).resolve()
    compiled_artifact = pack_path / ".compiled" / "universe.msgpack"
    builders._UNIVERSE_CACHE.pop(pack_path, None)
    if compiled_artifact.exists():
        compiled_artifact.unlink()


class TestCheckpointValidation:
    """Test checkpoint validation and error handling."""

    def test_legacy_checkpoint_rejected_missing_position_dim(self, cpu_device, test_config_pack_path):
        """Should reject legacy checkpoints missing position_dim field.

        This tests the breaking change in Phase 4 where position_dim became
        required in checkpoint format. Legacy checkpoints should be rejected
        with a clear error message.

        Coverage target: lines 878-891 (legacy checkpoint detection)
        """
        env = make_vectorized_env_from_pack(
            test_config_pack_path,
            level_name="L0_test",
            num_agents=1,
            device=cpu_device,
        )

        # Create legacy checkpoint data by removing position_dim from a valid payload
        legacy_checkpoint = env.get_affordance_positions()
        legacy_checkpoint.pop("position_dim", None)

        # Should raise ValueError with helpful message
        with pytest.raises(ValueError) as exc_info:
            env.set_affordance_positions(legacy_checkpoint)

        # Verify error message provides clear guidance
        error_msg = str(exc_info.value)
        assert "position_dim" in error_msg.lower(), "Error should mention missing field"
        assert "no longer supported" in error_msg.lower(), "Error should indicate format is obsolete"
        assert "delete" in error_msg.lower() or "retrain" in error_msg.lower(), "Error should provide remediation steps"

    def test_checkpoint_position_dim_mismatch_rejected(self, cpu_device, test_config_pack_path):
        """Should reject checkpoints with incompatible position dimensions.

        If checkpoint was saved from a 2D substrate but loaded into a 3D substrate,
        the position dimensions won't match and load should fail.

        Coverage target: lines 893-899 (dimension mismatch validation)
        """
        # Create 2D environment
        env_2d = make_vectorized_env_from_pack(
            test_config_pack_path,
            level_name="L0_test",
            num_agents=1,
            device=cpu_device,
        )

        # Create checkpoint with wrong position_dim (pretend it came from 3D substrate)
        checkpoint_3d = env_2d.get_affordance_positions()
        checkpoint_3d["position_dim"] = env_2d.substrate.position_dim + 1
        checkpoint_3d["positions"] = {name: coords + [0] for name, coords in checkpoint_3d["positions"].items()}

        # Should raise ValueError about dimension mismatch
        with pytest.raises(ValueError) as exc_info:
            env_2d.set_affordance_positions(checkpoint_3d)

        error_msg = str(exc_info.value)
        assert "position_dim mismatch" in error_msg.lower(), "Error should mention dimension mismatch"
        assert "3" in error_msg, "Error should mention checkpoint dimension (3D)"
        assert "2" in error_msg, "Error should mention substrate dimension (2D)"

    def test_checkpoint_loads_with_correct_position_dim(self, cpu_device, test_config_pack_path):
        """Should successfully load checkpoint with matching position_dim.

        This is the happy path - verifies that validation passes when dimensions match.

        Coverage target: lines 901-910 (successful checkpoint loading)
        """
        env = make_vectorized_env_from_pack(
            test_config_pack_path,
            level_name="L0_test",
            num_agents=1,
            device=cpu_device,
        )

        # Create valid checkpoint using runtime-generated payload
        valid_checkpoint = env.get_affordance_positions()

        # Should load successfully (no exception)
        env.set_affordance_positions(valid_checkpoint)

        # Verify positions were loaded
        for name, expected in valid_checkpoint["positions"].items():
            assert name in env.affordances
            assert env.affordances[name].tolist() == expected


class TestActionLabelLoading:
    """Test action labels provided via compiler metadata."""

    def test_custom_action_labels_from_config(self, cpu_device, tmp_path):
        """Should propagate custom action labels through compiler metadata.

        Users can supply `action_labels.yaml`; the compiler should embed those
        labels into ActionSpaceMetadata and VectorizedHamletEnv should reflect
        them at runtime.
        """
        config_dir = tmp_path / "custom_labels_config"
        # Use model_config as v2.1-compatible base pack.
        shutil.copytree(Path("configs/test/model_config"), config_dir)

        action_labels_config = {
            "custom": {
                0: "PORT",  # Custom name for LEFT
                1: "STARBOARD",  # Custom name for RIGHT
                2: "AFT",  # Custom name for DOWN
                3: "FORE",  # Custom name for UP
                4: "INTERACT",
                5: "WAIT",
            }
        }
        with open(config_dir / "action_labels.yaml", "w") as f:
            yaml.safe_dump(action_labels_config, f, sort_keys=False)

        env = make_vectorized_env_from_pack(
            config_dir,
            num_agents=1,
            device=cpu_device,
        )

        # Labels should be present in compiler metadata and exposed on the env.
        compiled_labels = env.universe.action_space_metadata.labels
        assert env.action_labels is not None  # Rehydrated ActionLabels wrapper
        assert env.action_labels.labels == compiled_labels  # runtime view mirrors compiler metadata
        label_values = list(compiled_labels.values())
        assert "PORT" in label_values, "Custom label 'PORT' should be loaded"
        assert "STARBOARD" in label_values, "Custom label 'STARBOARD' should be loaded"
        assert "AFT" in label_values, "Custom label 'AFT' should be loaded"
        assert "FORE" in label_values, "Custom label 'FORE' should be loaded"

    def test_default_action_labels_when_no_config(self, cpu_device, test_config_pack_path):
        """Should use default 'gaming' preset when no action_labels.yaml exists."""
        # test_config_pack_path doesn't have action_labels.yaml, so should use default
        env = make_vectorized_env_from_pack(
            test_config_pack_path,
            num_agents=1,
            device=cpu_device,
        )

        # Verify default labels are embedded via compiler metadata and match runtime view
        compiled_labels = env.universe.action_space_metadata.labels
        assert env.action_labels is not None
        assert env.action_labels.labels == compiled_labels
        # Default preset should cover canonical movement + meta actions (custom actions may extend the set)
        base_labels = {"UP", "DOWN", "LEFT", "RIGHT", "INTERACT", "WAIT"}
        assert base_labels.issubset(set(compiled_labels.values()))


class TestAffordancePositionSerialization:
    """Test affordance position serialization edge cases."""

    def test_aspatial_affordance_positions_empty_list(self, cpu_device):
        """Aspatial substrates should serialize affordance positions as empty lists.

        When substrate has position_dim=0 (aspatial), affordance positions should
        be empty lists in the checkpoint.

        Coverage target: lines 854-857 (aspatial position handling)
        """
        repo_root = Path(__file__).parent.parent.parent.parent.parent
        aspatial_config_path = repo_root / "configs" / "aspatial_test"

        # Skip test if aspatial config doesn't exist
        if not aspatial_config_path.exists():
            pytest.skip("Aspatial test config not found")

        # Use aspatial config directly - no parameter injection needed
        # Config packs are atomic artifacts (no individual file overrides)
        env = make_vectorized_env_from_pack(
            aspatial_config_path,
            num_agents=1,
            device=cpu_device,
        )

        env.reset()

        # Get affordance positions
        checkpoint_data = env.get_affordance_positions()

        # Verify position_dim is 0
        assert checkpoint_data["position_dim"] == 0, "Aspatial substrate should have position_dim=0"

        # Verify all affordance positions are empty lists
        for name, pos in checkpoint_data["positions"].items():
            assert pos == [], f"Aspatial affordance {name} should have empty position list, got {pos}"
