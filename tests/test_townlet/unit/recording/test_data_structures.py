"""
Tests for recording data structures.

Test serialization/deserialization roundtrips for episode recording data.
"""

from dataclasses import asdict

import msgpack


class TestRecordedStep:
    """Test RecordedStep serialization and deserialization."""

    def test_basic_step_serialization_roundtrip(self):
        """RecordedStep should serialize to msgpack and deserialize losslessly."""
        from townlet.recording.data_structures import RecordedStep, deserialize_step

        # Create a basic step
        step = RecordedStep(
            step=42,
            position=(3, 5),
            meters=(1.0, 0.9, 0.8, 0.5, 0.7, 0.6, 0.95, 0.85),
            action=4,  # INTERACT
            reward=1.0,
            intrinsic_reward=0.15,
            done=False,
            q_values=None,
            time_of_day=None,
            interaction_progress=None,
            extrinsic_reward=0.85,
            shaping_reward=0.0,
        )

        # Serialize to msgpack
        serialized = msgpack.packb(asdict(step), use_bin_type=True)

        # Deserialize
        deserialized_dict = msgpack.unpackb(serialized, raw=False)
        deserialized_step = deserialize_step(deserialized_dict)

        # Verify roundtrip
        assert deserialized_step == step
        assert deserialized_step.step == 42
        assert deserialized_step.position == (3, 5)
        assert deserialized_step.meters == (1.0, 0.9, 0.8, 0.5, 0.7, 0.6, 0.95, 0.85)
        assert deserialized_step.action == 4
        assert deserialized_step.reward == 1.0
        assert deserialized_step.intrinsic_reward == 0.15
        assert deserialized_step.done is False
        assert deserialized_step.q_values is None

    def test_step_with_q_values_serialization(self):
        """RecordedStep with Q-values should serialize correctly."""
        from townlet.recording.data_structures import RecordedStep, deserialize_step

        step = RecordedStep(
            step=10,
            position=(0, 0),
            meters=(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
            action=2,  # LEFT
            reward=0.8,
            intrinsic_reward=0.05,
            done=False,
            q_values=(0.8, 0.7, 0.9, 0.6, 1.2, 0.5),
            time_of_day=None,
            interaction_progress=None,
            extrinsic_reward=0.75,
            shaping_reward=0.0,
        )

        # Serialize and deserialize
        serialized = msgpack.packb(asdict(step), use_bin_type=True)
        deserialized_dict = msgpack.unpackb(serialized, raw=False)
        deserialized_step = deserialize_step(deserialized_dict)

        # Verify Q-values preserved
        assert deserialized_step.q_values == (0.8, 0.7, 0.9, 0.6, 1.2, 0.5)

    def test_step_with_temporal_mechanics_serialization(self):
        """RecordedStep with temporal fields should serialize correctly."""
        from townlet.recording.data_structures import RecordedStep

        step = RecordedStep(
            step=100,
            position=(4, 4),
            meters=(0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3),
            action=4,  # INTERACT
            reward=0.5,
            intrinsic_reward=0.1,
            done=False,
            q_values=None,
            time_of_day=12,  # Noon
            interaction_progress=0.33,  # 1/3 through interaction
            extrinsic_reward=0.4,
            shaping_reward=0.0,
        )

        # Serialize and deserialize
        serialized = msgpack.packb(asdict(step), use_bin_type=True)
        deserialized_dict = msgpack.unpackb(serialized, raw=False)
        deserialized_step = RecordedStep(**deserialized_dict)

        # Verify temporal fields preserved
        assert deserialized_step.time_of_day == 12
        assert deserialized_step.interaction_progress == 0.33

    def test_terminal_step_serialization(self):
        """Terminal step (done=True) should serialize correctly."""
        from townlet.recording.data_structures import RecordedStep

        step = RecordedStep(
            step=487,
            position=(7, 7),
            meters=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),  # Dead
            action=3,  # Last action before death
            reward=0.0,
            intrinsic_reward=0.0,
            done=True,
            q_values=None,
            time_of_day=None,
            interaction_progress=None,
            extrinsic_reward=0.0,
            shaping_reward=0.0,
        )

        # Serialize and deserialize
        serialized = msgpack.packb(asdict(step), use_bin_type=True)
        deserialized_dict = msgpack.unpackb(serialized, raw=False)
        deserialized_step = RecordedStep(**deserialized_dict)

        # Verify done flag preserved
        assert deserialized_step.done is True
        assert deserialized_step.reward == 0.0


class TestEpisodeMetadata:
    """Test EpisodeMetadata serialization and deserialization."""

    def test_basic_metadata_serialization_roundtrip(self):
        """EpisodeMetadata should serialize to msgpack and deserialize losslessly."""
        from townlet.recording.data_structures import EpisodeMetadata, deserialize_metadata

        metadata = EpisodeMetadata(
            episode_id=12345,
            survival_steps=487,
            total_reward=423.7,
            extrinsic_reward=410.2,
            intrinsic_reward=13.5,
            curriculum_stage=3,
            epsilon=0.15,
            intrinsic_weight=0.3,
            timestamp=1699123456.78,
            affordance_layout={"Bed": (2, 3), "Hospital": (5, 1)},
            affordance_visits={"Bed": 15, "Hospital": 2},
            custom_action_uses={},
            completion_reason="authored_terminal",
            shaping_reward=0.0,
        )

        # Serialize to msgpack
        serialized = msgpack.packb(asdict(metadata), use_bin_type=True)

        # Deserialize
        deserialized_dict = msgpack.unpackb(serialized, raw=False)
        deserialized_metadata = deserialize_metadata(deserialized_dict)

        # Verify roundtrip
        assert deserialized_metadata == metadata
        assert deserialized_metadata.episode_id == 12345
        assert deserialized_metadata.survival_steps == 487
        assert deserialized_metadata.total_reward == 423.7
        assert deserialized_metadata.curriculum_stage == 3
        assert deserialized_metadata.affordance_layout == {"Bed": (2, 3), "Hospital": (5, 1)}
        assert deserialized_metadata.affordance_visits == {"Bed": 15, "Hospital": 2}

    def test_metadata_with_no_affordance_visits(self):
        """Metadata with empty affordance visits should serialize correctly."""
        from townlet.recording.data_structures import EpisodeMetadata

        metadata = EpisodeMetadata(
            episode_id=1,
            survival_steps=10,
            total_reward=10.0,
            extrinsic_reward=10.0,
            intrinsic_reward=0.0,
            curriculum_stage=1,
            epsilon=1.0,
            intrinsic_weight=1.0,
            timestamp=1699123456.78,
            affordance_layout={"Bed": (2, 3)},
            affordance_visits={},  # No visits
            custom_action_uses={},  # No custom actions used
            completion_reason="authored_terminal",
            shaping_reward=0.0,
        )

        # Serialize and deserialize
        serialized = msgpack.packb(asdict(metadata), use_bin_type=True)
        deserialized_dict = msgpack.unpackb(serialized, raw=False)
        deserialized_metadata = EpisodeMetadata(**deserialized_dict)

        # Verify empty dict preserved
        assert deserialized_metadata.affordance_visits == {}


class TestEpisodeEndMarker:
    """Test EpisodeEndMarker creation."""

    def test_episode_end_marker_creation(self):
        """EpisodeEndMarker should wrap metadata."""
        from townlet.recording.data_structures import EpisodeEndMarker, EpisodeMetadata

        metadata = EpisodeMetadata(
            episode_id=100,
            survival_steps=200,
            total_reward=150.0,
            extrinsic_reward=145.0,
            intrinsic_reward=5.0,
            curriculum_stage=2,
            epsilon=0.5,
            intrinsic_weight=0.5,
            timestamp=1699123456.78,
            affordance_layout={"Bed": (2, 3)},
            affordance_visits={"Bed": 5},
            custom_action_uses={},
            completion_reason="authored_terminal",
            shaping_reward=0.0,
        )

        marker = EpisodeEndMarker(metadata=metadata)

        # Verify marker wraps metadata
        assert marker.metadata == metadata
        assert marker.metadata.episode_id == 100


class TestRequiredArtifactContract:
    """New fields are constructor requirements, not compatibility defaults."""

    def test_metadata_reason_and_shaping_are_required(self):
        from dataclasses import MISSING, fields

        from townlet.recording.data_structures import EpisodeMetadata

        declared = {field.name: field for field in fields(EpisodeMetadata)}
        for name in ("completion_reason", "shaping_reward"):
            assert name in declared, f"EpisodeMetadata requires {name}"
            assert declared[name].default is MISSING
            assert declared[name].default_factory is MISSING

    def test_step_extrinsic_and_shaping_are_required(self):
        from dataclasses import MISSING, fields

        from townlet.recording.data_structures import RecordedStep

        declared = {field.name: field for field in fields(RecordedStep)}
        for name in ("extrinsic_reward", "shaping_reward"):
            assert name in declared, f"RecordedStep requires {name}"
            assert declared[name].default is MISSING
            assert declared[name].default_factory is MISSING

    def test_recorder_component_arguments_are_required(self):
        from inspect import Parameter, signature

        from townlet.recording.recorder import EpisodeRecorder

        declared = signature(EpisodeRecorder.record_step).parameters
        for name in ("extrinsic_reward", "shaping_reward"):
            assert name in declared, f"record_step requires {name}"
            assert declared[name].default is Parameter.empty

    def test_recording_format_has_one_current_constant(self):
        from townlet.recording import data_structures

        assert getattr(data_structures, "RECORDING_FORMAT_VERSION", None) == 2

    def test_current_dtos_roundtrip_flat_positions_and_canonical_rewards(self):
        from tests.test_townlet.utils.builders import make_test_recording_payload
        from townlet.recording.data_structures import deserialize_metadata, deserialize_step

        payload = make_test_recording_payload(episode_id=7, completion_reason="authored_terminal")
        metadata = deserialize_metadata(payload["metadata"])
        step = deserialize_step(payload["steps"][0])
        assert metadata.completion_reason == "authored_terminal"
        assert metadata.shaping_reward == 0.2
        assert metadata.affordance_layout == {"Bed": (2, 3)}
        assert step.reward == 1.0
        assert step.extrinsic_reward == 0.5
        assert step.intrinsic_reward == 0.3
        assert step.shaping_reward == 0.2
