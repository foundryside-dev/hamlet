"""Config-in/behaviour-out tests for message/affordance scope extents (hamlet-9e1ae3b7a2).

These tests pin the extent contract from both ends:
- Declaring a message/affordance-scoped variable WITHOUT its extent fails loudly
  at compile time (not at env construction).
- Declaring the extent in variables.yaml `extents:` reaches the runtime
  registry, so the scope actually works end-to-end.

The zone and group scopes (and their num_zones/num_groups extents) were deleted in
VFS WP2: storage with no publisher and no write path. Declaring either now refuses.
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

SCOPED_VARIABLE = {
    "message": {
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "id": "message_payload",
        "scope": "message",
        "type": "vecNf",
        "lifetime": "tick",
        "semantic_type": "custom",
        "initial_value": [0.0, 0.0, 0.0],
        "exposed_to": [],
        "dims": 3,
        "description": "Recent message buffer payload",
    },
    "affordance": {
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
    },
}

EXTENT_NAME = {
    "message": "num_message_slots",
    "affordance": "num_affordances",
}


def _add_scoped_variable(pack: Path, scope: str, extents: dict[str, int] | None) -> None:
    """Append a scoped variable (and optionally an extents block) to the pack's variables.yaml."""
    ref_path = pack / "variables.yaml"
    data = yaml.safe_load(ref_path.read_text())
    data["variables"]["declarations"].append(SCOPED_VARIABLE[scope])
    if extents is not None:
        data["variables"]["extents"] = extents
    ref_path.write_text(yaml.safe_dump(data))


@pytest.mark.parametrize("scope", ["message", "affordance"])
def test_scoped_variable_without_extent_fails_at_compile(temp_config_pack: Path, scope: str) -> None:
    """A message/affordance-scoped variable with no declared extent must be rejected
    at compile time, naming both the variable and the missing extent — never a green
    compile followed by a crash at env construction (the Trial K shape)."""
    _add_scoped_variable(temp_config_pack, scope, extents=None)

    with pytest.raises(CompilationError) as excinfo:
        UniverseCompiler().compile(temp_config_pack, primary_level=PRIMARY_LEVEL, use_cache=False)

    message = str(excinfo.value)
    assert SCOPED_VARIABLE[scope]["id"] in message
    assert EXTENT_NAME[scope] in message


@pytest.mark.parametrize(
    ("scope", "extents"),
    [
        ("message", {"num_message_slots": 3}),
    ],
)
def test_scoped_variable_with_extent_reaches_runtime(temp_config_pack: Path, scope: str, extents: dict[str, int]) -> None:
    """With the extent declared, the pack compiles AND the env constructs, and the
    registry allocates storage with the declared extent."""
    _add_scoped_variable(temp_config_pack, scope, extents=extents)

    universe = UniverseCompiler().compile(temp_config_pack, primary_level=PRIMARY_LEVEL, use_cache=False)

    extent_name, extent_value = next(iter(extents.items()))
    assert getattr(universe.metadata, extent_name) == extent_value

    env = VectorizedHamletEnv.from_universe(
        universe,
        level_name=PRIMARY_LEVEL,
        num_agents=2,
        device=torch.device("cpu"),
    )

    assert getattr(env.vfs_registry, extent_name) == extent_value
    value = env.vfs_registry.get(SCOPED_VARIABLE[scope]["id"], reader="engine")
    # Message scope allocates [num_agents, num_message_slots, ...]
    assert value.shape[0] == 2
    assert value.shape[1] == extent_value


def test_extent_of_zero_is_rejected(temp_config_pack: Path) -> None:
    """An explicit zero extent is a declaration that means nothing — reject it."""
    _add_scoped_variable(temp_config_pack, "message", extents={"num_message_slots": 0})

    with pytest.raises(CompilationError):
        UniverseCompiler().compile(temp_config_pack, primary_level=PRIMARY_LEVEL, use_cache=False)


def test_extents_without_scoped_variables_are_allowed(temp_config_pack: Path) -> None:
    """Declaring extents with no matching-scope variables is harmless sizing metadata."""
    ref_path = temp_config_pack / "variables.yaml"
    data = yaml.safe_load(ref_path.read_text())
    data["variables"]["extents"] = {"num_message_slots": 4}
    ref_path.write_text(yaml.safe_dump(data))

    universe = UniverseCompiler().compile(temp_config_pack, primary_level=PRIMARY_LEVEL, use_cache=False)
    assert universe.metadata.num_message_slots == 4


@pytest.mark.parametrize("scope", ["zone", "group"])
def test_deleted_zone_and_group_scopes_refuse(temp_config_pack: Path, scope: str) -> None:
    """zone/group storage had no publisher and no write path; a declaration of either refuses."""
    declaration = dict(SCOPED_VARIABLE["message"], id=f"{scope}_state", scope=scope, type="scalar", initial_value=0.0)
    del declaration["dims"]
    ref_path = temp_config_pack / "variables.yaml"
    data = yaml.safe_load(ref_path.read_text())
    data["variables"]["declarations"].append(declaration)
    ref_path.write_text(yaml.safe_dump(data))

    with pytest.raises(CompilationError, match=f"{scope}_state|scope"):
        UniverseCompiler().compile(temp_config_pack, primary_level=PRIMARY_LEVEL, use_cache=False)


@pytest.mark.parametrize("extent", ["num_zones", "num_groups"])
def test_deleted_zone_and_group_extents_refuse(temp_config_pack: Path, extent: str) -> None:
    """The deleted extents are unknown keys, not inert metadata."""
    ref_path = temp_config_pack / "variables.yaml"
    data = yaml.safe_load(ref_path.read_text())
    data["variables"]["extents"] = {extent: 2}
    ref_path.write_text(yaml.safe_dump(data))

    with pytest.raises(CompilationError, match=extent):
        UniverseCompiler().compile(temp_config_pack, primary_level=PRIMARY_LEVEL, use_cache=False)
