"""Cleanup verification tests for VFS uplift runtime integration."""

import subprocess


def test_no_runtime_variables_reference_yaml_loading():
    """Verify no runtime loading of variables_reference.yaml for item vars."""
    # Grep check: src/townlet/environment/vectorized_env.py
    result = subprocess.run(
        [
            "grep",
            "-n",
            "variables_reference.yaml",
            "src/townlet/environment/vectorized_env.py",
        ],
        capture_output=True,
        text=True,
    )

    # Should find no matches (or only comments)
    assert (
        result.returncode != 0 or "variables_reference.yaml" not in result.stdout
    ), f"Found runtime variables_reference.yaml loading:\n{result.stdout}"


def test_no_runtime_effects_yaml_loading():
    """Verify no runtime loading of effects.yaml."""
    result = subprocess.run(
        [
            "grep",
            "-n",
            "effects.yaml",
            "src/townlet/environment/vectorized_env.py",
        ],
        capture_output=True,
        text=True,
    )

    # Should find no matches (or only comments)
    assert result.returncode != 0 or "effects_path.*read_text" not in result.stdout, f"Found runtime effects.yaml loading:\n{result.stdout}"


def test_no_runtime_effect_catalog_rebuild():
    """Verify no runtime EffectCatalog.from_config() calls."""
    result = subprocess.run(
        [
            "grep",
            "-n",
            "EffectCatalog.from_config",
            "src/townlet/environment/vectorized_env.py",
        ],
        capture_output=True,
        text=True,
    )

    # Should find no matches
    assert result.returncode != 0, f"Found runtime EffectCatalog rebuild:\n{result.stdout}"


def test_no_runtime_vfs_profile_loading():
    """Verify no runtime loading of vfs_profiles.yaml."""
    result = subprocess.run(
        [
            "grep",
            "-n",
            "vfs_profiles.yaml",
            "src/townlet/environment/vectorized_env.py",
        ],
        capture_output=True,
        text=True,
    )

    # Should find no matches (or only comments)
    assert (
        result.returncode != 0 or "vfs_profiles_path.*read_text" not in result.stdout
    ), f"Found runtime vfs_profiles.yaml loading:\n{result.stdout}"
