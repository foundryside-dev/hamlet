"""WP16 (F13): `persistent` VFS state survives demo checkpoint resume.

The spec says `persistent` retains state across episode resets and promises exact
checkpoint resume. A season, a reputation or a market price driven by a transition rule
must therefore come back from a checkpoint with exactly the value it was saved at, under
the identity gate, and only after that gate has passed.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import torch
import yaml

from tests.test_townlet.regressions.fixtures.episode_lanes import LEVEL_NAME, compile_authored_environment, copy_authored_config
from townlet.curriculum.static import StaticCurriculum
from townlet.demo.runner import DemoRunner
from townlet.exploration.adaptive_intrinsic import AdaptiveIntrinsicExploration
from townlet.population.vectorized import VectorizedPopulation

NUM_AGENTS = 2
LIFESPAN = 4
PERSISTENT = ("season", "standing")
EPISODE = "episode_count"


def _variable(var_id: str, *, scope: str, lifetime: str, initial_value: float) -> dict[str, object]:
    return {
        "id": var_id,
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "scope": scope,
        "type": "scalar",
        "lifetime": lifetime,
        "semantic_type": "custom",
        "exposed_to": [],
        "initial_value": initial_value,
    }


def _advance(var_id: str, expression: str) -> dict[str, object]:
    return {
        "variable_id": var_id,
        "effect": "advance",
        "expression": expression,
        "composition": "additive_delta",
        "condition": None,
        "clamp": [0.0, 1000.0],
    }


def _author_pack(destination: Path, *, season_initial: float = 0.0) -> Path:
    """The episode-lanes pack plus a persistent global, a persistent agent variable and an
    episode-lifetime control, all advanced once per tick by one transition rule."""
    pack = copy_authored_config(destination, lifespan=LIFESPAN, num_agents=NUM_AGENTS)
    variables_path = pack / "variables.yaml"
    payload = yaml.safe_load(variables_path.read_text())
    payload["variables"]["declarations"] += [
        _variable("season", scope="global", lifetime="persistent", initial_value=season_initial),
        _variable("standing", scope="agent", lifetime="persistent", initial_value=0.0),
        _variable(EPISODE, scope="global", lifetime="episode", initial_value=0.0),
    ]
    variables_path.write_text(yaml.safe_dump(payload, sort_keys=False))
    rules = {
        "version": "1.0",
        "transition_rules": [
            {
                "id": "advance_world",
                "phase": "apply_transition_rules",
                "condition": None,
                "writes": [
                    _advance("season", "1.0"),
                    _advance(EPISODE, "1.0"),
                    # Agent-shaped, so the per-agent rows genuinely differ from one another.
                    _advance("standing", "0.25 + bar.energy * 0.0"),
                ],
            }
        ],
    }
    (pack / "transition_rules.yaml").write_text(yaml.safe_dump(rules, sort_keys=False))
    return pack


def _population(pack: Path) -> VectorizedPopulation:
    env = compile_authored_environment(pack, num_agents=NUM_AGENTS)
    exploration = AdaptiveIntrinsicExploration(obs_dim=env.observation_dim, rnd_training_batch_size=128, device=torch.device("cpu"))
    population = VectorizedPopulation(
        env=env,
        curriculum=StaticCurriculum(1.0),
        exploration=exploration,
        agent_ids=[f"lane-{index}" for index in range(NUM_AGENTS)],
        device=torch.device("cpu"),
        brain_config=env.universe.brain,
        obs_dim=env.observation_dim,
        action_dim=env.action_dim,
        train_frequency=1,
        batch_size=128,
        sequence_length=1,
        max_grad_norm=1.0,
        tb_logger=None,
        max_episodes=100,
        max_steps_per_episode=LIFESPAN,
    )
    population.reset()
    return population


def _runner(pack: Path, tmp_path: Path, name: str, population: VectorizedPopulation) -> DemoRunner:
    runner = DemoRunner(
        config_dir=pack,
        db_path=tmp_path / f"{name}.db",
        checkpoint_dir=tmp_path / "checkpoints",
        max_episodes=1,
        level_name=LEVEL_NAME,
    )
    runner.population = population
    runner.env = population.env
    runner.curriculum = population.curriculum
    runner.exploration = population.exploration
    return runner


def _values(population: VectorizedPopulation) -> dict[str, torch.Tensor]:
    registry = population.env.vfs_registry
    return {var_id: registry.get(var_id, reader="engine") for var_id in (*PERSISTENT, EPISODE)}


def _run_across_resets(population: VectorizedPopulation, ticks: int) -> int:
    """Real training steps; returns how many episode resets the run crossed."""
    resets = 0
    for _ in range(ticks):
        if bool(population.episode_completed.all()):
            population.reset()
            resets += 1
        population.step_population(population.env)
    return resets


def _trained_checkpoint(tmp_path: Path) -> tuple[Path, dict[str, torch.Tensor]]:
    pack = _author_pack(tmp_path / "pack")
    population = _population(pack)
    ticks = 3 * LIFESPAN + 1
    assert _run_across_resets(population, ticks) >= 2
    saved = _values(population)
    # Persistent state accumulated across every episode; the episode control did not.
    # `season` is a global: one row per world (S1), each advanced while its own lane is
    # active, so it tracks that lane's `standing` exactly and the rows may differ.
    assert saved["season"].shape == (NUM_AGENTS,)
    assert torch.equal(saved["season"], saved["standing"] * 4.0)
    # Rules skip a lane on the tick it ends; each world still holds more than one episode.
    assert bool((saved["standing"] > 0.25 * LIFESPAN).all())
    assert bool((saved[EPISODE] < ticks).all())
    with _runner(pack, tmp_path, "first", population) as runner:
        runner.save_checkpoint()
    return pack, saved


def test_persistent_state_survives_resume_exactly_and_episode_state_is_not_restored(tmp_path: Path) -> None:
    pack, saved = _trained_checkpoint(tmp_path)
    (checkpoint_path,) = (tmp_path / "checkpoints").glob("checkpoint_ep*.pt")
    payload = torch.load(checkpoint_path, weights_only=False)
    # Exactly the persistent lifetime is saved; tick and episode lifetimes (the engine
    # `tick` among them) are re-initialized by every reset and are not resume state.
    assert set(payload["vfs_persistent_state"]) == set(PERSISTENT)

    resumed = _population(pack)
    # A value the resuming run holds in its episode-lifetime variable before the load.
    registry = resumed.env.vfs_registry
    registry.set_engine_value(EPISODE, torch.full_like(registry.get(EPISODE, reader="engine"), 42.0))
    fresh_episode_count = _values(resumed)[EPISODE]
    assert not torch.equal(fresh_episode_count, saved[EPISODE])
    with _runner(pack, tmp_path, "second", resumed) as runner:
        assert runner.load_checkpoint() == 0
    restored = _values(resumed)
    for var_id in PERSISTENT:
        assert torch.equal(restored[var_id], saved[var_id]), var_id
    # The episode-lifetime variable keeps the resuming run's own value, not the saved one.
    assert torch.equal(restored[EPISODE], fresh_episode_count)

    # The runner's resume policy starts a fresh episode; persistent state survives it and
    # continues from the saved value.
    resumed.reset()
    after_reset = _values(resumed)
    for var_id in PERSISTENT:
        assert torch.equal(after_reset[var_id], saved[var_id]), var_id
    assert bool((after_reset[EPISODE] == 0.0).all())
    resumed.step_population(resumed.env)
    assert torch.equal(_values(resumed)["season"], saved["season"] + 1.0)


def test_a_mismatched_pack_is_refused_before_any_state_is_applied(tmp_path: Path) -> None:
    _trained_checkpoint(tmp_path)
    other_pack = _author_pack(tmp_path / "other", season_initial=5.0)
    other = _population(other_pack)
    registry = other.env.vfs_registry
    before = registry.persistent_state()
    with _runner(other_pack, tmp_path, "other", other) as runner:
        with (
            patch.object(registry, "validate_persistent_state", wraps=registry.validate_persistent_state) as validate,
            patch.object(registry, "restore_persistent_state", wraps=registry.restore_persistent_state) as restore,
        ):
            with pytest.raises(ValueError, match="vfs_hash mismatch"):
                runner.load_checkpoint()
            validate.assert_not_called()
            restore.assert_not_called()
    after = registry.persistent_state()
    assert set(after) == set(before)
    assert all(torch.equal(after[var_id], before[var_id]) for var_id in before)
    assert after["season"].tolist() == [5.0] * NUM_AGENTS


def _server(pack: Path, checkpoint_dir: Path):
    from townlet.demo.live_inference import LiveInferenceServer

    server = LiveInferenceServer(
        checkpoint_dir=checkpoint_dir,
        level_name=LEVEL_NAME,
        port=8799,
        step_delay=0.0,
        total_episodes=1,
        config_dir=pack,
    )
    server._initialize_components()
    return server


@pytest.mark.asyncio
async def test_serving_a_checkpoint_restores_its_persistent_world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Live inference serves the policy in the persistent world state it was trained into."""
    pack = _author_pack(tmp_path / "pack")
    monkeypatch.chdir(tmp_path)  # the server opens a q-value log in CWD
    checkpoint_dir = tmp_path / "checkpoints"

    producer = _server(pack, checkpoint_dir)
    env = producer.env
    wait = torch.full((NUM_AGENTS,), env.action_dim - 1, dtype=torch.long, device=env.device)
    for _ in range(3):  # three episodes of two ticks each
        env.reset()
        env.step(wait)
        env.step(wait)
    saved = {var_id: env.vfs_registry.get(var_id, reader="engine") for var_id in PERSISTENT}
    assert bool((saved["season"] > 2.0).all())  # more than any single two-tick episode can hold
    with DemoRunner(
        config_dir=pack, db_path=tmp_path / "producer.db", checkpoint_dir=checkpoint_dir, max_episodes=1, level_name=LEVEL_NAME
    ) as runner:
        runner.population = producer.population
        runner.env = env
        runner.curriculum = producer.curriculum
        runner.exploration = producer.exploration
        runner.save_checkpoint()

    server = _server(pack, checkpoint_dir)
    registry = server.env.vfs_registry
    assert bool((registry.get("season", reader="engine") == 0.0).all())
    assert await server._check_and_load_checkpoint() is True
    for var_id in PERSISTENT:
        assert torch.equal(registry.get(var_id, reader="engine"), saved[var_id]), var_id
    server.env.reset()
    assert torch.equal(registry.get("season", reader="engine"), saved["season"])
