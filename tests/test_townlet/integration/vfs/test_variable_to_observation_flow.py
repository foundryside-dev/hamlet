"""Integration coverage for the VFS variable-to-observation path."""

import torch

from townlet.config.vfs_profiles_config import (
    AgentVFSProfileConfig,
    AgentVFSVariableConfig,
    GlobalVFSProfileConfig,
    GlobalVFSVariableConfig,
    ItemVFSProfileConfig,
    ItemVFSVariableConfig,
)
from townlet.vfs.observation_builder import VFSObservationSpec, build_vfs_observation
from townlet.vfs.profiles import VFSProfileCompiler
from townlet.vfs.registry import VariableRegistry, VFSRegistryProtocol
from townlet.vfs.schema import VariableDef


def test_variable_registry_values_flow_into_agent_observation() -> None:
    """Global, agent, and item VFS values should survive the full observation join."""
    device = torch.device("cpu")
    runtime_variables = [
        VariableDef(
            id="weather",
            scope="global",
            type="scalar",
            lifetime="episode",
            readable_by=["agent", "engine"],
            writable_by=["engine"],
            exposed_to=["agent"],
            default=0.25,
        ),
        VariableDef(
            id="stamina",
            scope="agent",
            type="scalar",
            lifetime="episode",
            readable_by=["agent", "engine"],
            writable_by=["engine"],
            exposed_to=["agent"],
            default=1.0,
        ),
    ]
    global_profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(semantic_type="custom", name="weather", type="float", initial_value=0.25, exposed_to=["agent"]),
        ]
    )
    agent_profile = AgentVFSProfileConfig(
        variables=[
            AgentVFSVariableConfig(semantic_type="custom", name="stamina", type="float", initial_value=1.0, exposed_to=["agent"]),
        ]
    )
    item_profile = ItemVFSProfileConfig(
        profile_name="ration",
        variables=[
            ItemVFSVariableConfig(name="nutrition", type="float", initial_value=0.75, exposed_to=["agent"]),
            ItemVFSVariableConfig(name="internal_decay", type="float", initial_value=0.1, exposed_to=["engine"]),
        ],
    )
    compiled_item_profile = VFSProfileCompiler().compile_item_profile(item_profile, bar_schema={})
    registry = VariableRegistry(
        variables=runtime_variables,
        num_agents=2,
        device=device,
        max_items=2,
        item_profiles={"ration": compiled_item_profile},
    )
    assert isinstance(registry, VFSRegistryProtocol)

    registry.set("weather", torch.tensor(0.5), writer="engine")
    registry.set("stamina", torch.tensor([0.9, 0.4]), writer="engine")
    registry.register_item_instance(0, "ration")
    registry.write_item("ration", "nutrition", 0.75, vfs_index=0)
    registry.write_item("ration", "internal_decay", 0.25, vfs_index=0)

    spec = VFSObservationSpec.from_profiles(
        global_profile=global_profile,
        agent_profile=agent_profile,
        item_profiles=[item_profile],
    )
    observation = build_vfs_observation(
        registry,
        spec,
        batch_size=2,
        agent_item_inventory=torch.tensor([[0, -1, -1], [-1, -1, -1]], dtype=torch.long),
    )

    assert observation.shape == (2, 5)
    assert torch.allclose(
        observation,
        torch.tensor(
            [
                [0.5, 0.9, 0.75, 0.0, 0.0],
                [0.5, 0.4, 0.0, 0.0, 0.0],
            ],
            dtype=torch.float32,
        ),
    )
