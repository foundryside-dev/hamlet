"""Required and scoped declarations are enforced independently of filenames."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from townlet.universe.compiler import UniverseCompiler
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationError


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    source = Path("configs/test/model_config")
    root = tmp_path / "scoping_pack"
    shutil.copytree(source, root)
    # Establish that every failure below isolates the intended declaration change.
    UniverseCompiler().compile(root, primary_level="L0_test", use_cache=False)
    return root


def test_missing_required_vfs_declaration_rejected(config_dir: Path) -> None:
    """The required VFS declaration cannot disappear from a valid pack."""
    (config_dir / "vfs_profiles.yaml").unlink()

    with pytest.raises(CompilationError) as caught:
        UniverseCompiler().compile(config_dir, primary_level="L0_test", use_cache=False)

    assert len(caught.value.issues) == 1, str(caught.value)
    issue = caught.value.issues[0]
    assert issue.code == ErrorCode.DECLARATION_MISSING
    assert issue.message == "Missing required vfs_profiles declaration"
    assert issue.location == f"{config_dir}:1"


def test_item_free_pack_supports_absent_optional_item_catalog(config_dir: Path) -> None:
    """No item catalog is needed to construct a deliberately item-free world."""
    (config_dir / "items.yaml").unlink()

    compiled = UniverseCompiler().compile(config_dir, primary_level="L0_test", use_cache=False)

    assert compiled.items_catalog is None
    env = compiled.create_environment(level_name="L0_test", num_agents=1, device="cpu")
    observation = env.reset()
    assert observation.shape == (1, env.observation_dim)
    assert env.item_manager is None


@pytest.mark.parametrize("family", ["vfs_profiles", "effects", "items"])
def test_level_scoped_shared_declarations_rejected(config_dir: Path, family: str) -> None:
    """Complete shared catalogs remain pack scoped in arbitrarily named documents."""
    level_dir = config_dir / "levels" / "L0_test" / "catalogs"
    level_dir.mkdir()
    misplaced_path = level_dir / "shared.yml"
    shutil.copyfile(config_dir / f"{family}.yaml", misplaced_path)

    with pytest.raises(CompilationError) as caught:
        UniverseCompiler().compile(config_dir, primary_level="L0_test", use_cache=False)

    assert len(caught.value.issues) == 1, str(caught.value)
    issue = caught.value.issues[0]
    assert issue.code == ErrorCode.DECLARATION_SCOPE
    assert f"{family} declaration is not allowed at level scope" in issue.message
    assert issue.location == f"{misplaced_path}:1"
