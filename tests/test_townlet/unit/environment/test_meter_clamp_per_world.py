"""One world's action never clamps another world's meters (owner ruling S1; verify_B2c L1).

The movement-cost, interaction-cost and interaction-effect clamps ran `torch.clamp` over
every row whenever any agent moved or interacted. A meter another world had pushed past
its bound (an unclamped item write) was therefore clamped before passive depletion in one
run and after it in another, depending only on what world 0 did.

The rule now: a meter write made by an agent's own action is clamped in that agent's row
at once; every world's meters are clamped at `clamp_and_validate` each step.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from townlet.determinism import seed_all
from townlet.universe.compiler import UniverseCompiler

WITNESS = Path(__file__).resolve().parents[4] / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"


@pytest.fixture(scope="module")
def universe():
    return UniverseCompiler().compile(WITNESS, primary_level=LEVEL, use_cache=False)


def _world1_energy_after(universe, world0_action: str) -> tuple[float, torch.Tensor]:
    seed_all(3)
    env = universe.create_environment(num_agents=2, level_name=LEVEL, device="cpu")
    seed_all(3)
    env.reset()
    energy = env.meter_name_to_index["energy"]
    env.meters[1, energy] = 1.2  # world 1 past its bound, as an unclamped item write leaves it
    action = {a.name: i for i, a in enumerate(env.action_space.actions)}
    obs, _, _, _ = env.step(torch.tensor([action[world0_action], action["WAIT"]]))
    return float(env.meters[1, energy]), obs[1].clone()


@pytest.mark.parametrize("world0_action", ["INTERACT", "UP"])
def test_world0s_action_does_not_clamp_world1(universe, world0_action: str) -> None:
    quiet = _world1_energy_after(universe, "WAIT")
    active = _world1_energy_after(universe, world0_action)
    assert quiet[0] == active[0] == 1.0  # depleted 1.2 -> 1.19, then clamped once at clamp_and_validate
    assert torch.equal(quiet[1], active[1])


def test_an_agents_own_cost_is_clamped_in_its_row_at_once(universe) -> None:
    from townlet.environment.action_executor import clamp_rows

    meters = torch.tensor([[1.5, -0.5], [1.5, -0.5]])
    out = clamp_rows(meters, torch.tensor([True, False]), torch.tensor([0.0, 0.0]), torch.tensor([1.0, 1.0]))
    assert out.tolist() == [[1.0, 0.0], [1.5, -0.5]]
