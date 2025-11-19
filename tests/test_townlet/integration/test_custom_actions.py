"""Integration tests for custom actions (REST, MEDITATE)."""

import pytest
import torch

from tests.test_townlet.helpers.config_builder import prepare_config_dir


def _enable_rest_and_meditate(data: dict) -> None:
    """Ensure both REST and MEDITATE are explicitly enabled in training.yaml."""
    enabled = data["training"].setdefault("enabled_actions", {})
    enabled["custom"] = ["REST", "MEDITATE"]


@pytest.fixture
def custom_actions_pack(tmp_path):
    """Temporary config pack with REST and MEDITATE enabled."""
    pack_dir = prepare_config_dir(tmp_path, modifier=_enable_rest_and_meditate, name="custom_actions_pack")
    return pack_dir


def test_rest_action_is_enabled(cpu_env_factory, custom_actions_pack):
    """REST should be present and enabled in the action space."""
    env = cpu_env_factory(config_dir=custom_actions_pack, num_agents=1)
    env.reset()

    rest = env.action_space.get_action_by_name("REST")
    assert rest.enabled, "REST should be enabled when listed in training.enabled_actions.custom"

    mask = env.action_space.get_base_action_mask(env.num_agents, env.device)
    assert mask[0, rest.id], "REST should be available in the base action mask"

    # Stepping with REST should not violate meter bounds
    env.meters.fill_(0.5)
    env.step(torch.tensor([rest.id], device=env.device))
    assert torch.all((env.meters >= 0.0) & (env.meters <= 1.0))


def test_meditate_action_is_enabled(cpu_env_factory, custom_actions_pack):
    """MEDITATE should be present and enabled in the action space."""
    env = cpu_env_factory(config_dir=custom_actions_pack, num_agents=1)
    env.reset()

    meditate = env.action_space.get_action_by_name("MEDITATE")
    assert meditate.enabled, "MEDITATE should be enabled when listed in training.enabled_actions.custom"

    mask = env.action_space.get_base_action_mask(env.num_agents, env.device)
    assert mask[0, meditate.id], "MEDITATE should be available in the base action mask"

    env.meters.fill_(0.4)
    env.step(torch.tensor([meditate.id], device=env.device))
    assert torch.all((env.meters >= 0.0) & (env.meters <= 1.0))


def test_rest_action_respects_dynamic_meter_lookup(cpu_env_factory, custom_actions_pack):
    """REST should be resolved via meter names rather than fixed indices."""
    env = cpu_env_factory(config_dir=custom_actions_pack, num_agents=1)
    env.reset()

    rest = env.action_space.get_action_by_name("REST")
    mood_idx = env.meter_name_to_index.get("mood")
    assert mood_idx is not None, "mood meter must be present in config"

    env.step(torch.tensor([rest.id], device=env.device))
    after = env.meters

    # No NaNs and clamp respected
    assert torch.all(torch.isfinite(after))
    assert torch.all((after >= 0.0) & (after <= 1.0))
