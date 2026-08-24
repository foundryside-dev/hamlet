"""Config-in/behaviour-out tests for zone/group/message scope extents (hamlet-9e1ae3b7a2).

Trial K showed a zone-scoped variable VALIDATES and COMPILES, then hard-crashes at
env construction because nothing wires num_zones/num_groups/num_message_slots into
VariableRegistry and no config surface exists to declare them.

These tests pin the fix from both ends:
- Declaring a zone/group/message-scoped variable WITHOUT its extent fails loudly
  at compile time (not at env construction).
- Declaring the extent in variables_reference.yaml `extents:` reaches the runtime
  registry, so the scope actually works end-to-end.
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
    "zone": {
        "id": "zone_temp_offset",
        "scope": "zone",
        "type": "scalar",
        "default": 0.0,
        "lifetime": "persistent",
        "readable_by": ["agent", "engine"],
        "writable_by": ["engine"],
        "description": "Per-zone temperature offset",
    },
    "group": {
        "id": "group_cohesion",
        "scope": "group",
        "type": "scalar",
        "default": 0.5,
        "lifetime": "persistent",
        "readable_by": ["agent", "engine"],
        "writable_by": ["engine"],
        "description": "Per-group cohesion",
    },
    "message": {
        "id": "message_payload",
        "scope": "message",
        "type": "vecNf",
        "dims": 3,
        "default": [0.0, 0.0, 0.0],
        "lifetime": "tick",
        "readable_by": ["agent", "engine"],
        "writable_by": ["engine"],
        "description": "Recent message buffer payload",
    },
    "affordance": {
        "id": "occupied_by_test",
        "scope": "affordance",
        "type": "agent_ref",
        "lifetime": "tick",
        "readable_by": ["engine", "vtc"],
        "writable_by": ["engine", "vtc"],
        "default": None,
        "observable": False,
        "description": "Current claimant for each affordance row",
    },
}

EXTENT_NAME = {
    "zone": "num_zones",
    "group": "num_groups",
    "message": "num_message_slots",
    "affordance": "num_affordances",
}


def _add_scoped_variable(pack: Path, scope: str, extents: dict[str, int] | None) -> None:
    """Append a scoped variable (and optionally an extents block) to the pack's variables_reference.yaml."""
    ref_path = pack / "variables_reference.yaml"
    data = yaml.safe_load(ref_path.read_text())
    data["variables"].append(SCOPED_VARIABLE[scope])
    if extents is not None:
        data["extents"] = extents
    ref_path.write_text(yaml.safe_dump(data))


@pytest.mark.parametrize("scope", ["zone", "group", "message", "affordance"])
def test_scoped_variable_without_extent_fails_at_compile(temp_config_pack: Path, scope: str) -> None:
    """A zone/group/message-scoped variable with no declared extent must be rejected
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
        ("zone", {"num_zones": 4}),
        ("group", {"num_groups": 2}),
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
    if scope == "message":
        # Message scope allocates [num_agents, num_message_slots, ...]
        assert value.shape[0] == 2
        assert value.shape[1] == extent_value
    else:
        assert value.shape[0] == extent_value


def test_extent_of_zero_is_rejected(temp_config_pack: Path) -> None:
    """An explicit zero extent is a declaration that means nothing — reject it."""
    _add_scoped_variable(temp_config_pack, "zone", extents={"num_zones": 0})

    with pytest.raises(CompilationError):
        UniverseCompiler().compile(temp_config_pack, primary_level=PRIMARY_LEVEL, use_cache=False)


def test_extents_without_scoped_variables_are_allowed(temp_config_pack: Path) -> None:
    """Declaring extents with no matching-scope variables is harmless sizing metadata."""
    ref_path = temp_config_pack / "variables_reference.yaml"
    data = yaml.safe_load(ref_path.read_text())
    data["extents"] = {"num_zones": 4}
    ref_path.write_text(yaml.safe_dump(data))

    universe = UniverseCompiler().compile(temp_config_pack, primary_level=PRIMARY_LEVEL, use_cache=False)
    assert universe.metadata.num_zones == 4
