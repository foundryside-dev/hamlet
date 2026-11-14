"""The current runner artifact must bind one explicit native boundary."""

import pytest
import torch

from townlet.training import checkpoint_utils
from townlet.vfs.random_draws import VFSRandomness, VFSWorldContext


def boundary():
    context = VFSWorldContext(training_seed=42, world_ids=("native-world",), world_episode_seqs=(0,))
    return {
        "kind": "INITIAL",
        "world_state": {"kind": "INITIAL", "vfs_random_context": VFSRandomness(context=context).state()},
        "rng_state": {"schema": "native-rng-v1", "torch_cpu": torch.get_rng_state(), "torch_cuda": {}},
    }


def test_current_artifact_requires_native_boundary_field():
    assert "native_boundary" in checkpoint_utils.DEMO_CHECKPOINT_KEYS
    assert checkpoint_utils.CHECKPOINT_FORMAT_VERSION == 10


def test_native_boundary_outer_validation_is_observational():
    state = boundary()
    before = torch.get_rng_state().clone()
    checkpoint_utils.validate_demo_native_boundary(
        {"native_boundary": state, "vfs_random_state": state["world_state"]["vfs_random_context"]}, cuda_devices=()
    )
    assert torch.equal(before, torch.get_rng_state())


@pytest.mark.parametrize("damage", ["missing", "extra", "kind", "world_kind", "rng_profile"])
def test_native_boundary_refuses_inconsistent_transport(damage):
    state = boundary()
    outer_vfs = state["world_state"]["vfs_random_context"]
    if damage == "missing":
        del state["world_state"]
    elif damage == "extra":
        state["invented"] = True
    elif damage == "kind":
        state["kind"] = "ACTIVE"
    elif damage == "world_kind":
        state["world_state"]["kind"] = "COMPLETED"
    else:
        state["rng_state"]["torch_cuda"] = {0: torch.get_rng_state()}
    with pytest.raises(ValueError):
        checkpoint_utils.validate_demo_native_boundary({"native_boundary": state, "vfs_random_state": outer_vfs}, cuda_devices=())


def test_runtime_fields_accept_current_world_vfs_state():
    from townlet.vfs.random_draws import VFSRandomness, VFSWorldContext

    context = VFSWorldContext(training_seed=42, world_ids=("native-world",), world_episode_seqs=(3,))
    payload = {
        "substrate_metadata": {"position_dim": 2, "substrate_type": "Grid2DSubstrate"},
        "agent_ids": ["agent_0"],
        "epsilon": 0.25,
        "completed_live_agent_steps": 123,
        "vfs_persistent_state": {},
        "vfs_random_state": VFSRandomness(context=context).state(),
    }
    checkpoint_utils.validate_demo_checkpoint_runtime_fields(payload, position_dim=2, substrate_type="Grid2DSubstrate", num_agents=1)


def test_native_boundary_refuses_conflicting_outer_vfs_state():
    from townlet.vfs.random_draws import VFSRandomness, VFSWorldContext

    current = VFSRandomness(context=VFSWorldContext(training_seed=42, world_ids=("native-world",), world_episode_seqs=(0,))).state()
    wrong = VFSRandomness(context=VFSWorldContext(training_seed=42, world_ids=("native-world",), world_episode_seqs=(1,))).state()
    state = boundary()
    state["world_state"]["vfs_random_context"] = current
    with pytest.raises(ValueError):
        checkpoint_utils.validate_demo_native_boundary({"native_boundary": state, "vfs_random_state": wrong}, cuda_devices=())
