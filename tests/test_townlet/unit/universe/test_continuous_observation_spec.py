"""Tests for continuous substrate observation spec generation."""

from tests.test_townlet.helpers.config_builder import mutate_stratum_yaml, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


def test_continuous1d_relative_encoding_adds_position_velocity_fields(tmp_path):
    """Continuous1D with relative encoding should add 1D position and velocity fields."""
    # Create minimal config pack using helper
    config_dir = prepare_config_dir(tmp_path, name="continuous1d_test")

    # Modify stratum.yaml to use continuous substrate
    def set_continuous_substrate(data):
        data["stratum"]["substrate"] = {
            "type": "continuous",
            "continuous": {
                "dimensions": 1,
                "bounds": [[0.0, 10.0]],
                "boundary": "clamp",
                "movement_delta": 0.5,
                "interaction_radius": 1.0,
                "distance_metric": "euclidean",
                "observation_encoding": "relative",
                "action_discretization": {"num_directions": 8, "num_magnitudes": 3},
            },
        }
        data["stratum"]["vision_support"] = "global"
        data["stratum"]["temporal_support"] = "disabled"

    mutate_stratum_yaml(config_dir, set_continuous_substrate)

    # Compile the config
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, use_cache=False)

    # Verify observation spec has position and velocity fields
    field_names = {f.name for f in compiled.observation_spec.fields}

    assert "obs_position" in field_names, f"Continuous1D should have obs_position field. " f"Found fields: {field_names}"
    assert "obs_velocity" in field_names, f"Continuous1D should have obs_velocity field. " f"Found fields: {field_names}"

    # Verify dimensions (relative encoding: 1D)
    pos_field = next(f for f in compiled.observation_spec.fields if f.name == "obs_position")
    vel_field = next(f for f in compiled.observation_spec.fields if f.name == "obs_velocity")

    assert pos_field.dims == 1, f"Continuous1D relative encoding should have 1D position, got {pos_field.dims}"
    assert vel_field.dims == 1, f"Continuous1D should have 1D velocity, got {vel_field.dims}"

    # Verify start/end indices are correct
    assert pos_field.start_index == 0, f"Position should start at 0, got {pos_field.start_index}"
    assert pos_field.end_index == 1, f"Position should end at 1, got {pos_field.end_index}"
    assert vel_field.start_index == 1, f"Velocity should start at 1, got {vel_field.start_index}"
    assert vel_field.end_index == 2, f"Velocity should end at 2, got {vel_field.end_index}"


def test_continuous1d_scaled_encoding_doubles_position_dims(tmp_path):
    """Continuous1D with scaled encoding should have 2D position (normalized + range)."""
    # Create minimal config pack using helper
    config_dir = prepare_config_dir(tmp_path, name="continuous1d_scaled")

    # Modify stratum.yaml to use continuous substrate with scaled encoding
    def set_continuous_substrate_scaled(data):
        data["stratum"]["substrate"] = {
            "type": "continuous",
            "continuous": {
                "dimensions": 1,
                "bounds": [[0.0, 10.0]],
                "boundary": "clamp",
                "movement_delta": 0.5,
                "interaction_radius": 1.0,
                "distance_metric": "euclidean",
                "observation_encoding": "scaled",  # <- KEY DIFFERENCE
                "action_discretization": {"num_directions": 8, "num_magnitudes": 3},
            },
        }
        data["stratum"]["vision_support"] = "global"
        data["stratum"]["temporal_support"] = "disabled"

    mutate_stratum_yaml(config_dir, set_continuous_substrate_scaled)

    # Compile
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, use_cache=False)

    # Verify dimensions (scaled encoding: position=2, velocity=1)
    pos_field = next(f for f in compiled.observation_spec.fields if f.name == "obs_position")
    vel_field = next(f for f in compiled.observation_spec.fields if f.name == "obs_velocity")

    assert pos_field.dims == 2, f"Continuous1D scaled encoding should have 2D position (normalized + range), " f"got {pos_field.dims}"
    assert vel_field.dims == 1, f"Velocity should remain 1D (native dimensionality), got {vel_field.dims}"

    # Verify start/end indices are correct
    assert pos_field.start_index == 0, f"Position should start at 0, got {pos_field.start_index}"
    assert pos_field.end_index == 2, f"Position should end at 2, got {pos_field.end_index}"
    assert vel_field.start_index == 2, f"Velocity should start at 2, got {vel_field.start_index}"
    assert vel_field.end_index == 3, f"Velocity should end at 3, got {vel_field.end_index}"


def test_continuousnd_4d_relative_encoding(tmp_path):
    """ContinuousND 4D should have 4D position and velocity fields."""
    # Create minimal config pack using helper
    config_dir = prepare_config_dir(tmp_path, name="continuousnd_4d")

    # Modify stratum.yaml to use 4D continuousnd substrate
    def set_continuousnd_4d_substrate(data):
        data["stratum"]["substrate"] = {
            "type": "continuousnd",
            "continuous": {
                "dimensions": 4,
                "bounds": [[0.0, 10.0], [0.0, 10.0], [0.0, 10.0], [0.0, 10.0]],
                "boundary": "clamp",
                "movement_delta": 0.5,
                "interaction_radius": 1.0,
                "distance_metric": "euclidean",
                "observation_encoding": "relative",
                "action_discretization": {"num_directions": 8, "num_magnitudes": 3},
            },
        }
        data["stratum"]["vision_support"] = "global"
        data["stratum"]["temporal_support"] = "disabled"

    mutate_stratum_yaml(config_dir, set_continuousnd_4d_substrate)

    # Compile
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, use_cache=False)

    # Verify 4D observations
    pos_field = next(f for f in compiled.observation_spec.fields if f.name == "obs_position")
    vel_field = next(f for f in compiled.observation_spec.fields if f.name == "obs_velocity")

    assert pos_field.dims == 4, f"ContinuousND 4D should have 4D position, got {pos_field.dims}"
    assert vel_field.dims == 4, f"ContinuousND 4D should have 4D velocity, got {vel_field.dims}"

    # Verify start/end indices are correct
    assert pos_field.start_index == 0, f"Position should start at 0, got {pos_field.start_index}"
    assert pos_field.end_index == 4, f"Position should end at 4, got {pos_field.end_index}"
    assert vel_field.start_index == 4, f"Velocity should start at 4, got {vel_field.start_index}"
    assert vel_field.end_index == 8, f"Velocity should end at 8, got {vel_field.end_index}"
