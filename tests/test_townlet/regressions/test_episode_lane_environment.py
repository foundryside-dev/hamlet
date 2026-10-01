"""Environment eligibility and retirement must agree with authored lane endings."""

from pathlib import Path

import pytest
import torch

from tests.test_townlet.regressions.fixtures.episode_lanes import (
    UNEQUAL_ENDINGS,
    action_ids,
    compile_authored_environment,
    copy_authored_config,
    observe_environment_steps,
)


@pytest.mark.parametrize("end_ticks", [(2, 5), (5, 2), (2,), (2, 2)])
def test_authored_endings_freeze_counts_and_publish_owned_events(tmp_path: Path, end_ticks: tuple[int, ...]) -> None:
    config = copy_authored_config(tmp_path / "pack", lifespan=20, num_agents=len(end_ticks))
    env = compile_authored_environment(config, num_agents=len(end_ticks))
    for episode in range(2):
        env.reset()
        assert env.step_counts.tolist() == [0] * len(end_ticks)
        assert env.dones.tolist() == [False] * len(end_ticks)
        assert env.global_tick == 0
        assert env.meters[:, env.meter_name_to_index["energy"]].tolist() == [1.0] * len(end_ticks)
        with observe_environment_steps(env) as ticks:
            for tick in range(1, max(end_ticks) + 1):
                names = ["END_LANE" if tick == ending else "WAIT" for ending in end_ticks]
                env.step(action_ids(env, names))
        independent_counts = torch.stack([item.active_before for item in ticks]).sum(dim=0).tolist()
        observed_counts = ticks[-1].info["step_counts"].tolist()
        print(f"episode={episode} endings={end_ticks} independent={independent_counts} reported={observed_counts}")
        assert independent_counts == list(end_ticks)
        assert observed_counts == list(end_ticks)
        assert sum(int(item.active_before.sum()) for item in ticks) == sum(end_ticks)
        assert [item.world_tick for item in ticks] == list(range(1, max(end_ticks) + 1))
        assert torch.stack([item.new_done for item in ticks]).sum(dim=0).tolist() == [1] * len(end_ticks)
        for tick, item in enumerate(ticks, start=1):
            for name in ("active_on_entry", "newly_terminal", "newly_retired"):
                event = item.info[name]
                assert event.dtype == torch.bool
                assert event.shape == (len(end_ticks),)
                assert event.device == env.device
            assert torch.equal(item.info["active_on_entry"], item.active_before)
            assert torch.equal(item.info["newly_terminal"], item.new_done)
            assert not item.info["newly_retired"].any()
            assert item.info["step_counts"].tolist() == [min(tick, ending) for ending in end_ticks]
        # Published events must own their tensors; later environment mutation cannot alter them.
        _, _, _, info = env.step(action_ids(env, ["WAIT"] * len(end_ticks)))
        env.dones.zero_()
        env.step_counts.zero_()
        assert not info["active_on_entry"].any()
        assert not info["newly_terminal"].any()
        assert not info["newly_retired"].any()
        assert info["step_counts"].tolist() == list(end_ticks)


def test_death_wins_lifespan_coincidence_and_sticky_dead_rows_receive_no_bonus(tmp_path: Path) -> None:
    config = copy_authored_config(tmp_path / "pack", lifespan=5, num_agents=2)
    env = compile_authored_environment(config, num_agents=2)
    env.reset()
    with observe_environment_steps(env) as ticks:
        for names in UNEQUAL_ENDINGS:
            env.step(action_ids(env, names))
        env.step(action_ids(env, ("WAIT", "WAIT")))
    assert ticks[4].rewards.tolist() == [0.0, 0.0]
    assert ticks[5].rewards.tolist() == [0.0, 0.0]
    assert all(not item.info["newly_retired"].any() for item in ticks)
    assert ticks[-1].info["step_counts"].tolist() == [2, 5]


def test_healthy_retirement_preserves_live_reward_and_components_once(tmp_path: Path) -> None:
    config = copy_authored_config(tmp_path / "pack", lifespan=5, num_agents=2)
    env = compile_authored_environment(config, num_agents=2)
    env.reset()
    with observe_environment_steps(env) as ticks:
        for _ in range(6):
            env.step(action_ids(env, ("WAIT", "WAIT")))
    retirement = ticks[4]
    components = retirement.info["reward_components"]
    assert torch.allclose(retirement.rewards, components["extrinsic"] + components["intrinsic"] + components["shaping"])
    assert (retirement.rewards > 1.0).all()
    assert retirement.info["newly_retired"].tolist() == [True, True]
    assert retirement.info["newly_terminal"].tolist() == [True, True]
    assert ticks[5].rewards.tolist() == [0.0, 0.0]
    assert not ticks[5].info["newly_retired"].any()
    assert ticks[5].info["step_counts"].tolist() == [5, 5]
