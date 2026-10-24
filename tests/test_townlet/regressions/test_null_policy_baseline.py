"""Null-policy survival floors on ``configs/default_curriculum`` L1.

The project's only prior learning evidence (M4) reported greedy survival of 99 ticks,
which is exactly what a WAIT-only policy achieves on this pack. These floors turn that
comparison into a regression test: any future "learning result" on L1 must beat the
WAIT-only line to be called one, and the scripted sleeper marks the next rung.

The WAIT-only figure is not hard-coded. It is forward-integrated in pure Python from the
compiled pack's declared passive dynamics (per-meter passive depletion, threshold
cascades, lethal bounds) and then checked against the engine. On the shipped pack this
is 99: energy alone would reach its lethal bound on tick 100, but the declared
satiation -> energy cascade starts biting once satiation drops below its threshold and
takes the last 0.01 one tick early.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest
import torch

from townlet.config.affordances_v2_config import AffordanceParamConfig
from townlet.config.bars_v2_config import BarsV2Config
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler

CONFIG_DIR = Path(__file__).resolve().parents[3] / "configs" / "default_curriculum"
LEVEL = "L1_full_observability"
NUM_LANES = 4
DEVICE = torch.device("cpu")


@pytest.fixture(scope="module")
def universe() -> CompiledUniverse:
    return UniverseCompiler().compile(CONFIG_DIR, primary_level=LEVEL)


def predict_idle_survival(bars: BarsV2Config) -> tuple[int, str]:
    """Forward-integrate the declared passive dynamics for an agent that never acts.

    Mirrors the engine's per-tick order (passive depletion, then declared cascades in
    authored order, then lethal-bound checks) using only declared parameters. Returns
    the tick on which the first lethal bound is reached and the meter that reached it.
    The engine counts that lethal tick as a survived step, so this is the ``step_counts``
    value a WAIT-only lane reports.
    """
    values = {meter.name: meter.initial for meter in bars.meters}
    bounds = {meter.name: meter.bounds for meter in bars.meters}
    lethal = [meter for meter in bars.meters if meter.bounds.lethal_min or meter.bounds.lethal_max]
    assert lethal, "pack declares no lethal bound; an idle agent would never die"
    for tick in range(1, 1_000_000):
        for meter in bars.meters:
            values[meter.name] = min(max(values[meter.name] - meter.depletion.passive, meter.bounds.min), meter.bounds.max)
        for cascade in bars.cascades:
            source = values[cascade.source]
            if cascade.threshold != 0.0 and source < cascade.threshold:
                delta = -cascade.strength * (cascade.threshold - source) / cascade.threshold
                target = bounds[cascade.target]
                values[cascade.target] = min(max(values[cascade.target] + delta, target.min), target.max)
        for meter in lethal:
            if meter.bounds.lethal_min and values[meter.name] <= meter.bounds.min:
                return tick, meter.name
            if meter.bounds.lethal_max and values[meter.name] >= meter.bounds.max:
                return tick, meter.name
    raise AssertionError("idle agent did not reach a lethal bound within a million ticks")


def restoring_affordance(affordances: Sequence[AffordanceParamConfig], meter_name: str) -> str:
    """The one affordance whose ``on_start`` interactions write the lethal meter's bar."""
    candidates = [
        affordance.name
        for affordance in affordances
        if any(
            command.modify is not None and command.modify.endswith(f".bar.{meter_name}") for command in affordance.interactions["on_start"]
        )
    ]
    assert len(candidates) == 1, f"expected exactly one affordance writing bar {meter_name!r} on start, found {candidates}"
    return candidates[0]


def make_env(universe: CompiledUniverse) -> VectorizedHamletEnv:
    torch.manual_seed(0)
    env = VectorizedHamletEnv.from_universe(universe, level_name=LEVEL, num_agents=NUM_LANES, device=DEVICE)
    env.reset()
    return env


def run_episode(env: VectorizedHamletEnv, choose, max_steps: int) -> list[int]:
    """Step ``env`` with ``choose(env) -> actions`` until every lane is done; return per-lane survival."""
    for _ in range(max_steps):
        _, _, dones, _ = env.step(choose(env))
        if bool(dones.all()):
            break
    assert bool(env.dones.all()), "episode did not terminate on every lane"
    return env.step_counts.tolist()


def wait_policy(env: VectorizedHamletEnv) -> torch.Tensor:
    wait_id = env.action_space.get_action_by_name("WAIT").id
    return torch.full((env.num_agents,), wait_id, dtype=torch.long, device=env.device)


def random_policy(env: VectorizedHamletEnv) -> torch.Tensor:
    """Uniform over the legal action mask; finished lanes WAIT."""
    wait_id = env.action_space.get_action_by_name("WAIT").id
    mask = env.get_action_masks().float()
    mask[env.dones] = 0.0
    mask[env.dones, wait_id] = 1.0
    return torch.multinomial(mask, 1).squeeze(1)


def make_sleeper_policy(env: VectorizedHamletEnv, meter_name: str, affordance_name: str, threshold: float):
    """Walk to the nearest restoring affordance and INTERACT once the lethal meter is low."""
    wait_id = env.action_space.get_action_by_name("WAIT").id
    interact_id = env.action_space.get_action_by_name("INTERACT").id
    moves = [
        (action.id, torch.tensor(action.delta, dtype=torch.long))
        for action in env.action_space.actions
        if action.type == "movement" and action.delta is not None
    ]
    meter_idx = env.meter_name_to_index[meter_name]

    def choose(env: VectorizedHamletEnv) -> torch.Tensor:
        actions = torch.full((env.num_agents,), wait_id, dtype=torch.long, device=env.device)
        targets = env.affordances[affordance_name].reshape(-1, env.substrate.position_dim).to(torch.long)
        positions = env.positions.to(torch.long)
        level = env.meters[:, meter_idx]
        for lane in range(env.num_agents):
            if bool(env.dones[lane]) or float(level[lane]) >= threshold:
                continue
            offsets = targets - positions[lane]
            nearest = offsets[offsets.abs().sum(dim=1).argmin()]
            if int(nearest.abs().sum()) == 0:
                actions[lane] = interact_id
                continue
            step = torch.sign(nearest)
            for action_id, delta in moves:
                if torch.equal(delta, step):
                    actions[lane] = action_id
                    break
        return actions

    return choose


def test_idle_survival_is_derived_from_declared_dynamics(universe: CompiledUniverse) -> None:
    """WAIT-only lanes die on exactly the tick the declared passive dynamics predict."""
    level = universe.get_level(LEVEL)
    predicted, lethal_meter = predict_idle_survival(level.bars)
    env = make_env(universe)
    survival = run_episode(env, wait_policy, level.training.training_loop.max_steps_per_episode)
    print(f"idle: predicted={predicted} via {lethal_meter}, observed={survival}")
    assert survival == [predicted] * NUM_LANES
    # Shipped pack: 99 (energy, with the satiation -> energy cascade taking the last tick).
    assert (
        float(env.meters[0, env.meter_name_to_index[lethal_meter]]) <= level.bars.meters[env.meter_name_to_index[lethal_meter]].bounds.min
    )


def test_uniform_random_dies_before_idle(universe: CompiledUniverse) -> None:
    """Acting at random costs movement energy and dies strictly before standing still."""
    level = universe.get_level(LEVEL)
    predicted, _ = predict_idle_survival(level.bars)
    env = make_env(universe)
    survival = run_episode(env, random_policy, level.training.training_loop.max_steps_per_episode)
    print(f"random: observed={survival} idle={predicted}")
    assert max(survival) < predicted


def test_scripted_sleeper_outlives_idle(universe: CompiledUniverse) -> None:
    """A scripted walk-to-the-restorer policy beats the idle floor on every lane.

    This is the simplest skill the pack rewards; a trained policy that does not beat the
    idle line has not learned it.
    """
    level = universe.get_level(LEVEL)
    predicted, lethal_meter = predict_idle_survival(level.bars)
    restorer = restoring_affordance(level.affordances.affordances, lethal_meter)
    env = make_env(universe)
    # Start walking while there is still enough of the lethal meter to cross the whole
    # substrate (one move plus one passive tick per cell) and press INTERACT once.
    meter = next(m for m in level.bars.meters if m.name == lethal_meter)
    grid = universe.stratum.stratum.substrate.grid
    assert grid is not None, "the sleeper's walking budget is derived from a grid substrate"
    span = (grid.width - 1) + (grid.height - 1)
    threshold = span * (meter.depletion.passive + meter.depletion.move) + meter.depletion.interact + meter.depletion.passive
    assert threshold < meter.initial, "the sleeper would need to walk before the episode starts"
    sleeper = make_sleeper_policy(env, lethal_meter, restorer, threshold)
    survival = run_episode(env, sleeper, level.training.training_loop.max_steps_per_episode)
    print(f"sleeper via {restorer} at {lethal_meter} < {threshold:.3f}: observed={survival} idle={predicted}")
    assert min(survival) > predicted
