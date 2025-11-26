"""Integration tests for live inference WebSocket protocol."""

import pytest

from townlet.demo.live_inference import LiveInferenceServer

LEVEL_NAME = "L0_test"


@pytest.mark.asyncio
async def test_build_substrate_metadata_grid2d(tmp_path, test_config_pack_path):
    """Test _build_substrate_metadata returns correct metadata for Grid2D."""
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()

    # Use a writable copy so we can adjust agent loss if schemas change
    import shutil

    from tests.test_townlet.helpers.config_builder import mutate_brain_yaml, mutate_training_yaml

    config_copy = tmp_path / "config_pack"
    shutil.copytree(test_config_pack_path, config_copy)
    # Ensure agent loss is schema-compliant
    mutate_brain_yaml(config_copy, lambda brain: brain.update({"loss": {"type": "huber", "huber_delta": 1.0}}))

    def _set_adversarial(training_data: dict) -> None:
        training_section = training_data.get("training", {}) or {}
        curriculum_cfg = training_section.get("curriculum", {}) or {}
        curriculum_cfg["strategy"] = "adversarial"
        training_section["curriculum"] = curriculum_cfg
        training_data["training"] = training_section

    mutate_training_yaml(config_copy, _set_adversarial)

    server = LiveInferenceServer(
        checkpoint_dir=checkpoint_dir,
        port=8767,  # Different port to avoid conflicts
        step_delay=0.01,
        total_episodes=100,
        config_dir=config_copy,
        level_name=LEVEL_NAME,
    )

    # Initialize components (creates environment with substrate)
    await server.startup()

    try:
        # Test substrate metadata extraction
        metadata = server._build_substrate_metadata()

        # Verify Grid2D metadata
        assert "type" in metadata, "Substrate metadata should include type"
        assert "position_dim" in metadata, "Substrate metadata should include position_dim"

        # Grid2D should have these fields
        assert metadata["type"] == "grid2d", "Test config uses Grid2D substrate"
        assert metadata["position_dim"] == 2, "Grid2D has position_dim=2"
        assert "width" in metadata, "Grid2D should include width"
        assert "height" in metadata, "Grid2D should include height"
        assert "topology" in metadata, "Grid2D should include topology"

        # Verify values are sensible
        assert isinstance(metadata["width"], int)
        assert isinstance(metadata["height"], int)
        assert metadata["width"] > 0
        assert metadata["height"] > 0

    finally:
        await server.shutdown()


@pytest.mark.asyncio
async def test_build_substrate_metadata_before_env_created(tmp_path, test_config_pack_path):
    """Test _build_substrate_metadata returns safe defaults when env is None."""
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()

    server = LiveInferenceServer(
        checkpoint_dir=checkpoint_dir,
        port=8768,
        step_delay=0.01,
        total_episodes=100,
        config_dir=test_config_pack_path,
        level_name=LEVEL_NAME,
    )

    # Don't call startup() - env should be None
    metadata = server._build_substrate_metadata()

    # Should return safe defaults
    assert metadata["type"] == "unknown"
    assert metadata["position_dim"] == 0
