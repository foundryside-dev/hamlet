"""time_of_day is a derivation of global_tick — one temporal pipeline."""

from __future__ import annotations

import inspect
from pathlib import Path

import torch

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler
import townlet.environment.vectorized_env as vec_mod


def test_no_independent_time_of_day_increment_remains():
    src = inspect.getsource(vec_mod)
    assert "self.time_of_day + 1" not in src  # the second bookkeeping is gone


def test_time_of_day_equals_tick_mod_day_length_on_temporal_pack(tmp_path):
    # L3 is the shipped temporal level; compile the real pack read-only.
    u = UniverseCompiler().compile(Path("configs/default_curriculum"), primary_level="L3_temporal_mechanics")
    env = u.create_environment(num_agents=2, level_name="L3_temporal_mechanics", device="cpu")
    env.reset()
    day = int(env.day_length)
    for k in range(1, 2 * day + 2):
        env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))
        assert env.time_of_day == env.global_tick % day == k % day


def test_time_of_day_is_zero_without_temporal_mechanics(tmp_path):
    u = UniverseCompiler().compile(prepare_config_dir(tmp_path), primary_level=PRIMARY_LEVEL_NAME)
    env = u.create_environment(num_agents=1, level_name=PRIMARY_LEVEL_NAME, device="cpu")
    env.reset()
    env.step(torch.zeros(1, dtype=torch.long, device=env.device))
    assert env.time_of_day == 0
