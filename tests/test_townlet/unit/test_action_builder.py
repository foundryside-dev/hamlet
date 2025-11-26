"""Tests for ActionSpaceBuilder and ComposedActionSpace."""

from pathlib import Path

import pytest
import torch
import yaml

from townlet.environment.action_builder import ComposedActionSpace
from townlet.environment.action_config import ActionConfig

GLOBAL_ACTIONS_PATH = Path("configs/global_actions.yaml")


def _load_global_custom_actions(path: Path | None = None) -> list[dict]:
    """Load custom actions from a global_actions.yaml (empty list if missing)."""
    path = path or GLOBAL_ACTIONS_PATH
    if not path.exists():
        return []
    with path.open() as f:
        data = yaml.safe_load(f) or {}
    return data.get("custom_actions", [])


@pytest.fixture
def global_actions_file(tmp_path: Path) -> Path:
    """Temporary global_actions.yaml containing REST and MEDITATE."""
    path = tmp_path / "global_actions.yaml"
    path.write_text(
        """
version: "1.0"
custom_actions:
  - name: "REST"
    type: "passive"
    costs: {energy: -0.002}
    effects: {}
  - name: "MEDITATE"
    type: "passive"
    costs: {}
    effects: {mood: 0.02}
"""
    )
    return path


def make_action(id: int, name: str, type: str, **overrides) -> ActionConfig:
    """Factory for creating ActionConfig in tests with explicit defaults.

    Centralizes ActionConfig creation so when fields change, we only update here.
    """
    defaults = {
        "id": id,
        "name": name,
        "type": type,
        "delta": None,
        "teleport_to": None,
        "costs": {},
        "effects": {},
        "enabled": True,
        "description": None,
        "icon": None,
        "source": "substrate",
        "source_affordance": None,
    }
    defaults.update(overrides)
    return ActionConfig(**defaults)


def test_composed_action_space_basic():
    """ComposedActionSpace should track actions and metadata."""
    actions = [
        make_action(0, "UP", "movement", delta=[0, -1]),
        make_action(1, "DOWN", "movement", delta=[0, 1]),
        make_action(2, "REST", "passive", source="custom"),
    ]

    space = ComposedActionSpace(
        actions=actions,
        substrate_action_count=2,
        custom_action_count=1,
        affordance_action_count=0,
        enabled_action_names=None,
    )

    assert space.action_dim == 3
    assert space.substrate_action_count == 2
    assert space.custom_action_count == 1


def test_composed_action_space_get_by_id():
    """Should retrieve action by ID."""
    actions = [
        make_action(0, "UP", "movement", delta=[0, -1]),
        make_action(1, "REST", "passive", source="custom"),
    ]

    space = ComposedActionSpace(
        actions=actions,
        substrate_action_count=1,
        custom_action_count=1,
        affordance_action_count=0,
        enabled_action_names=None,
    )

    assert space.get_action_by_id(0).name == "UP"
    assert space.get_action_by_id(1).name == "REST"


def test_composed_action_space_get_by_name():
    """Should retrieve action by name."""
    actions = [
        make_action(0, "UP", "movement", delta=[0, -1]),
        make_action(1, "REST", "passive", source="custom"),
    ]

    space = ComposedActionSpace(
        actions=actions,
        substrate_action_count=1,
        custom_action_count=1,
        affordance_action_count=0,
        enabled_action_names=None,
    )

    assert space.get_action_by_name("UP").id == 0
    assert space.get_action_by_name("REST").id == 1


def test_composed_action_space_enabled_count():
    """Should count enabled vs disabled actions."""
    actions = [
        make_action(0, "UP", "movement", delta=[0, -1]),
        make_action(1, "DOWN", "movement", delta=[0, 1]),
        make_action(2, "REST", "passive", source="custom"),
        make_action(3, "MEDITATE", "passive", enabled=False, source="custom"),  # Disabled
    ]

    space = ComposedActionSpace(
        actions=actions,
        substrate_action_count=2,
        custom_action_count=2,
        affordance_action_count=0,
        enabled_action_names={"UP", "DOWN", "REST"},  # MEDITATE not enabled
    )

    assert space.action_dim == 4  # Total actions (including disabled)
    assert space.enabled_action_count == 3  # Only enabled ones


def test_composed_action_space_get_base_mask():
    """Should generate action mask with disabled actions masked out."""
    actions = [
        make_action(0, "UP", "movement", delta=[0, -1]),
        make_action(1, "DOWN", "movement", delta=[0, 1]),
        make_action(2, "REST", "passive", source="custom"),
        make_action(3, "MEDITATE", "passive", enabled=False, source="custom"),  # Disabled
    ]

    space = ComposedActionSpace(
        actions=actions,
        substrate_action_count=2,
        custom_action_count=2,
        affordance_action_count=0,
        enabled_action_names=None,
    )

    mask = space.get_base_action_mask(num_agents=2, device=torch.device("cpu"))

    # Shape: [2 agents, 4 actions]
    assert mask.shape == (2, 4)

    # Actions 0, 1, 2 enabled (True)
    assert mask[0, 0]
    assert mask[0, 1]
    assert mask[0, 2]

    # Action 3 disabled (False)
    assert not mask[0, 3]
    assert not mask[1, 3]  # Disabled for all agents


def test_action_space_builder_substrate_only():
    """Builder with no custom actions should return substrate actions only."""
    from townlet.environment.action_builder import ActionSpaceBuilder
    from townlet.substrate.grid2d import Grid2DSubstrate

    substrate = Grid2DSubstrate(width=8, height=8, boundary="clamp", distance_metric="manhattan")

    # No global_actions.yaml
    builder = ActionSpaceBuilder(
        substrate=substrate,
        global_actions_path=Path("/nonexistent/global_actions.yaml"),
        enabled_action_names=None,
    )

    space = builder.build()

    assert space.action_dim == substrate.action_space_size  # Grid2D substrate actions only
    assert space.substrate_action_count == substrate.action_space_size
    assert space.custom_action_count == 0


def test_action_space_builder_with_custom_actions(tmp_path):
    """Builder with custom actions should compose substrate + custom."""
    from townlet.environment.action_builder import ActionSpaceBuilder
    from townlet.substrate.grid2d import Grid2DSubstrate

    # Create temporary global_actions.yaml
    global_actions_yaml = tmp_path / "global_actions.yaml"
    global_actions_yaml.write_text(
        """
version: "1.0"
description: "Global custom actions"

custom_actions:
  - name: "REST"
    type: "passive"
    costs: {energy: -0.002}
    effects: {}
  - name: "MEDITATE"
    type: "passive"
    costs: {mood: 0.02}
    effects: {}
"""
    )

    substrate = Grid2DSubstrate(width=8, height=8, boundary="clamp", distance_metric="manhattan")

    builder = ActionSpaceBuilder(
        substrate=substrate,
        global_actions_path=global_actions_yaml,
        enabled_action_names=None,
    )

    space = builder.build()

    # 9 substrate (with diagonals) + 2 custom = 11 actions
    assert space.action_dim == substrate.action_space_size + 2
    assert space.substrate_action_count == substrate.action_space_size
    assert space.custom_action_count == 2

    # Substrate actions come first (IDs 0-5)
    assert space.get_action_by_id(0).name == "UP"
    assert space.get_action_by_id(0).source == "substrate"

    # Custom actions come after substrate block
    first_custom_id = substrate.action_space_size
    assert space.get_action_by_id(first_custom_id).name == "REST"
    assert space.get_action_by_id(first_custom_id).source == "custom"
    assert space.get_action_by_id(first_custom_id + 1).name == "MEDITATE"
    assert space.get_action_by_id(first_custom_id + 1).source == "custom"


def test_action_space_builder_with_enabled_actions(tmp_path):
    """Builder should mark disabled actions as enabled=False."""
    from townlet.environment.action_builder import ActionSpaceBuilder
    from townlet.substrate.grid2d import Grid2DSubstrate

    global_actions_yaml = tmp_path / "global_actions.yaml"
    global_actions_yaml.write_text(
        """
version: "1.0"
custom_actions:
  - name: "REST"
    type: "passive"
    costs: {}
    effects: {}
  - name: "MEDITATE"
    type: "passive"
    costs: {}
    effects: {}
"""
    )

    substrate = Grid2DSubstrate(width=8, height=8, boundary="clamp", distance_metric="manhattan")

    # Only enable UP, DOWN, REST (disable others)
    builder = ActionSpaceBuilder(
        substrate=substrate,
        global_actions_path=global_actions_yaml,
        enabled_action_names=["UP", "DOWN", "REST"],
    )

    space = builder.build()

    # All 11 actions defined (9 substrate + 2 custom)
    assert space.action_dim == substrate.action_space_size + 2

    # UP, DOWN, REST enabled
    assert space.get_action_by_name("UP").enabled
    assert space.get_action_by_name("DOWN").enabled
    assert space.get_action_by_name("REST").enabled

    # All other substrate + custom actions disabled
    assert not space.get_action_by_name("LEFT").enabled
    assert not space.get_action_by_name("RIGHT").enabled
    assert not space.get_action_by_name("UP_LEFT").enabled
    assert not space.get_action_by_name("UP_RIGHT").enabled
    assert not space.get_action_by_name("DOWN_LEFT").enabled
    assert not space.get_action_by_name("DOWN_RIGHT").enabled
    assert not space.get_action_by_name("INTERACT").enabled
    assert not space.get_action_by_name("MEDITATE").enabled

    # Enabled count = 3
    assert space.enabled_action_count == 3


def test_empty_enabled_list_disables_all():
    """Empty enabled_action_names list should disable all actions."""
    from townlet.environment.action_builder import ActionSpaceBuilder
    from townlet.substrate.grid2d import Grid2DSubstrate

    substrate = Grid2DSubstrate(width=8, height=8, boundary="clamp", distance_metric="manhattan")

    # Empty list = explicitly disable all actions
    builder = ActionSpaceBuilder(
        substrate=substrate,
        global_actions_path=Path("/nonexistent/global_actions.yaml"),
        enabled_action_names=[],  # Empty list (disable all)
    )

    space = builder.build()

    # All substrate actions exist
    assert space.action_dim == substrate.action_space_size

    # But ZERO actions enabled
    assert space.enabled_action_count == 0

    # Verify all actions disabled
    for action in space.actions:
        assert not action.enabled


def test_load_global_actions_yaml(global_actions_file: Path):
    """Should load global_actions.yaml successfully."""
    from townlet.environment.action_builder import ActionSpaceBuilder
    from townlet.substrate.grid2d import Grid2DSubstrate

    substrate = Grid2DSubstrate(width=8, height=8, boundary="clamp", distance_metric="manhattan")

    builder = ActionSpaceBuilder(
        substrate=substrate,
        global_actions_path=global_actions_file,
        enabled_action_names=None,
    )

    space = builder.build()

    custom_actions = _load_global_custom_actions(global_actions_file)
    expected_substrate = substrate.action_space_size
    expected_custom = len(custom_actions)

    assert space.action_dim == expected_substrate + expected_custom
    assert space.substrate_action_count == expected_substrate
    assert space.custom_action_count == expected_custom


def test_global_actions_has_rest_and_meditate(global_actions_file: Path):
    """Global actions should include REST and MEDITATE (temp file)."""
    from townlet.environment.action_builder import ActionSpaceBuilder
    from townlet.substrate.grid2d import Grid2DSubstrate

    substrate = Grid2DSubstrate(width=8, height=8, boundary="clamp", distance_metric="manhattan")

    builder = ActionSpaceBuilder(
        substrate=substrate,
        global_actions_path=global_actions_file,
        enabled_action_names=None,
    )

    space = builder.build()

    custom_names = {entry["name"] for entry in _load_global_custom_actions(global_actions_file)}
    required = {"REST", "MEDITATE"}
    assert required.issubset(custom_names)

    # Should have REST and MEDITATE
    rest = space.get_action_by_name("REST")
    assert rest.type == "passive"
    assert rest.costs.get("energy", 0) < 0  # Negative cost (restoration)

    meditate = space.get_action_by_name("MEDITATE")
    assert meditate.type == "passive"
    assert meditate.effects.get("mood", 0) > 0  # Positive effect (restoration)


def test_global_actions_yaml_actions_present(global_actions_file: Path):
    """Custom actions from YAML should appear in built action space."""
    from townlet.environment.action_builder import ActionSpaceBuilder
    from townlet.substrate.grid2d import Grid2DSubstrate

    substrate = Grid2DSubstrate(width=8, height=8, boundary="clamp", distance_metric="manhattan")

    builder = ActionSpaceBuilder(
        substrate=substrate,
        global_actions_path=global_actions_file,
        enabled_action_names=None,
    )

    space = builder.build()

    custom_entries = _load_global_custom_actions(global_actions_file)
    expected_names = {entry["name"] for entry in custom_entries}
    space_custom_names = {action.name for action in space.actions if action.source == "custom"}

    assert space_custom_names == expected_names

    # Validate that numeric properties defined in YAML propagate to the action configs
    for entry in custom_entries:
        action = space.get_action_by_name(entry["name"])
        if "delta" in entry:
            assert action.delta == entry["delta"]
        if "teleport_to" in entry:
            assert action.teleport_to == entry["teleport_to"]
        if "costs" in entry:
            for meter, amount in entry["costs"].items():
                assert action.costs.get(meter) == amount
        if "effects" in entry:
            for meter, amount in entry["effects"].items():
                assert action.effects.get(meter) == amount
