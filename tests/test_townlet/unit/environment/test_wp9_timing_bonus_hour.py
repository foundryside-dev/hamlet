"""DAC `timing_bonus` on a real environment: it runs, and it reads the hour the action was taken at.

The reward calculator used to hand DAC `env.time_of_day` as a Python int, so any drive with a
`timing_bonus` crashed on its first step (unit tests passed a tensor). Under the WP9 clock the
observation shows instant k+1 after a step, while the reward reads instant k, the hour the
rewarded action was gated at.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import torch
import yaml

from townlet.universe.compiler import UniverseCompiler

REPO = Path(__file__).resolve().parents[4]
LEVEL = "L3_temporal_mechanics"
BONUS = 1.0


def _env(tmp_path: Path, *, timing_bonus: bool):
    pack = tmp_path / ("bonus" if timing_bonus else "base")
    shutil.copytree(REPO / "configs" / "default_curriculum", pack, ignore=shutil.ignore_patterns(".compiled"))
    if timing_bonus:
        drive_path = pack / "levels" / LEVEL / "drive.yaml"
        drive = yaml.safe_load(drive_path.read_text())
        drive["drive"]["shaping"].append(
            {
                "type": "timing_bonus",
                "weight": BONUS,
                "time_ranges": [{"start_hour": 9, "end_hour": 9, "affordance": "WORK", "multiplier": 1.0}],
            }
        )
        drive_path.write_text(yaml.safe_dump(drive, sort_keys=False))
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL)
    return universe.create_environment(num_agents=1, level_name=LEVEL, device="cpu")


def _shaping_per_step(env) -> list[tuple[int, float]]:
    """(hour the action was taken at, shaping reward) for INTERACT on WORK at hours 8..10."""
    actions = {action.name: index for index, action in enumerate(env.action_space.actions)}
    torch.manual_seed(0)
    env.reset()
    out = []
    for _ in range(11):
        acted_hour = env.time_of_day
        action = actions["WAIT"]
        if acted_hour in (8, 9, 10):
            env.positions[0] = env.affordances["WORK"].to(env.positions.dtype)
            for meter in ("energy", "mood"):
                env.meters[0, env.meter_name_to_index[meter]] = 1.0
            action = actions["INTERACT"]
        _obs, _reward, _done, info = env.step(torch.tensor([action], device=env.device))
        out.append((acted_hour, float(info["reward_components"]["shaping"][0])))
    return out


def test_timing_bonus_steps_and_rewards_the_acted_hour(tmp_path):
    base = _shaping_per_step(_env(tmp_path, timing_bonus=False))
    with_bonus = _shaping_per_step(_env(tmp_path, timing_bonus=True))
    assert [hour for hour, _ in base] == [hour for hour, _ in with_bonus] == list(range(11))
    deltas = {hour: round(bonus - plain, 6) for (hour, plain), (_, bonus) in zip(base, with_bonus, strict=True)}
    # WORK succeeds at 9 and 10 (opens 9..17), but the window is hour 9 only: the bonus lands
    # on the step whose action was taken at hour 9, though its observation already shows 10.
    assert deltas[9] == BONUS
    assert all(delta == 0.0 for hour, delta in deltas.items() if hour != 9)
