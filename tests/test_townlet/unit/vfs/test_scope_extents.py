"""Config-in/behaviour-out tests for scope extents (hamlet-9e1ae3b7a2).

No scope takes an authored extent, so the variables declaration has no `extents`
block at all (VFS WP15):
- Affordance-scope rows have no authored extent: the level's affordance count is
  the authority (VFS WP6, findings F4).
- The zone and group scopes were deleted in VFS WP2, the message scope in VFS WP15.
  An `extents` block, empty or not, is an unknown key that refuses at parse.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch
import yaml

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError

PRIMARY_LEVEL = "L0_test"

AFFORDANCE_VARIABLE = {
    "readable_by": ["engine", "agent"],
    "writable_by": ["engine"],
    "id": "occupied_by_test",
    "scope": "affordance",
    "type": "agent_ref",
    "lifetime": "tick",
    "semantic_type": "custom",
    "initial_value": None,
    "exposed_to": [],
    "description": "Current claimant for each affordance row",
}


def _add_variable(pack: Path, declaration: dict[str, object]) -> None:
    ref_path = pack / "variables.yaml"
    data = yaml.safe_load(ref_path.read_text())
    data["variables"]["declarations"].append(declaration)
    ref_path.write_text(yaml.safe_dump(data))


@pytest.mark.parametrize("scope", ["zone", "group"])
def test_deleted_zone_and_group_scopes_refuse(temp_config_pack: Path, scope: str) -> None:
    """zone/group storage had no publisher and no write path; a declaration of either refuses."""
    declaration = dict(AFFORDANCE_VARIABLE, id=f"{scope}_state", scope=scope, type="scalar", initial_value=0.0)
    _add_variable(temp_config_pack, declaration)

    with pytest.raises(CompilationError, match=f"{scope}_state|scope"):
        UniverseCompiler().compile(temp_config_pack, primary_level=PRIMARY_LEVEL, use_cache=False)


@pytest.mark.parametrize(
    "extents",
    [{}, {"num_zones": 2}, {"num_groups": 2}, {"num_affordances": 2}, {"num_message_slots": 2}],
    ids=["empty", "num_zones", "num_groups", "num_affordances", "num_message_slots"],
)
def test_extents_block_refuses_at_parse_with_its_location(temp_config_pack: Path, extents: dict[str, int]) -> None:
    """The extents block is deleted: an old pack declaring one, even empty, fails loudly."""
    ref_path = temp_config_pack / "variables.yaml"
    data = yaml.safe_load(ref_path.read_text())
    data["variables"]["extents"] = extents
    ref_path.write_text(yaml.safe_dump(data))

    with pytest.raises(CompilationError) as excinfo:
        UniverseCompiler().compile(temp_config_pack, primary_level=PRIMARY_LEVEL, use_cache=False)
    message = str(excinfo.value)
    assert "Stage 1" in message and "extents" in message
    assert f"{ref_path}:" in message


def test_affordance_scope_rows_come_from_the_level(temp_config_pack: Path) -> None:
    """findings_vfs F4: an affordance-scope variable needs no authored extent; its
    registry rows are the level's affordance count, the one authority, in every world (S1)."""
    _add_variable(temp_config_pack, AFFORDANCE_VARIABLE)

    universe = UniverseCompiler().compile(temp_config_pack, primary_level=PRIMARY_LEVEL, use_cache=False)
    env = VectorizedHamletEnv.from_universe(
        universe,
        level_name=PRIMARY_LEVEL,
        num_agents=2,
        device=torch.device("cpu"),
    )

    rows = env.vfs_registry.get(AFFORDANCE_VARIABLE["id"], reader="engine")
    assert rows.shape == (2, universe.metadata.affordance_count)
