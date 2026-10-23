"""Compiled authored lanes with controlled selection and real brain forwards."""

from __future__ import annotations

import shutil
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import patch

import torch
import yaml

from townlet.config.brain_config import apply_training_overrides
from townlet.curriculum.static import StaticCurriculum
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.exploration.base import ExplorationStrategy
from townlet.population.vectorized import VectorizedPopulation
from townlet.training.state import BatchedAgentState
from townlet.universe.compiler import UniverseCompiler

EPISODE_LANE_CONFIG = Path(__file__).resolve().parents[4] / "configs/test/episode_lanes"
LEVEL_NAME = "L0_test"
UNEQUAL_ENDINGS = (
    ("WAIT", "WAIT"),
    ("END_LANE", "WAIT"),
    ("WAIT", "WAIT"),
    ("WAIT", "WAIT"),
    ("WAIT", "END_LANE"),
)


def copy_authored_config(destination: Path, *, lifespan: int, num_agents: int) -> Path:
    """Copy the whole authored pack and declare test-specific training controls."""
    shutil.copytree(EPISODE_LANE_CONFIG, destination)
    training_path = destination / "levels" / LEVEL_NAME / "training.yaml"
    payload = yaml.safe_load(training_path.read_text())
    payload["training"]["population"]["size"] = num_agents
    payload["training"]["training_loop"]["max_steps_per_episode"] = lifespan
    training_path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return destination


def compile_authored_environment(config_dir: Path, *, num_agents: int) -> VectorizedHamletEnv:
    """Compile supported YAML without cache or runtime state injection."""
    universe = UniverseCompiler().compile(config_dir, primary_level=LEVEL_NAME, use_cache=False)
    return VectorizedHamletEnv(universe=universe, level_name=LEVEL_NAME, num_agents=num_agents, device="cpu")


def build_authored_population(config_dir: Path, *, num_agents: int, exploration: ExplorationStrategy) -> VectorizedPopulation:
    """Build the normal population using the compiled brain and training overrides."""
    env = compile_authored_environment(config_dir, num_agents=num_agents)
    training = env.level.training
    curriculum = StaticCurriculum(
        difficulty_level=0.5,
        reward_mode="shaped",
        active_meters=["energy", "health", "satiation", "money", "mood", "social"],
        depletion_multiplier=1.0,
    )
    curriculum.initialize_population(num_agents)
    population = VectorizedPopulation(
        env=env,
        curriculum=curriculum,
        exploration=exploration,
        agent_ids=[f"authored-lane-{i}" for i in range(num_agents)],
        device=env.device,
        brain_config=apply_training_overrides(env.universe.brain, training),
        obs_dim=env.observation_dim,
        train_frequency=training.training_loop.train_frequency,
        batch_size=training.replay_buffer.batch_size,
        sequence_length=training.training_loop.sequence_length,
        max_grad_norm=training.training_loop.max_grad_norm,
        action_dim=env.action_dim,
        tb_logger=None,
        max_episodes=training.training_loop.max_episodes,
        max_steps_per_episode=training.training_loop.max_steps_per_episode,
    )
    population.reset()
    return population


def action_ids(env: VectorizedHamletEnv, names: Sequence[str]) -> torch.Tensor:
    """Resolve names from the compiled action space, never fixed numeric IDs."""
    return torch.tensor([env.action_ids[name] for name in names], dtype=torch.long, device=env.device)


@dataclass
class SelectionWitness:
    """Copies of actual network outputs and selected authored actions."""

    q_values: list[torch.Tensor] = field(default_factory=list)
    actions: list[torch.Tensor] = field(default_factory=list)


@contextmanager
def controlled_action_schedule(
    exploration: ExplorationStrategy, env: VectorizedHamletEnv, schedule: Sequence[Sequence[str]]
) -> Iterator[SelectionWitness]:
    """Control only selection; population still calls the real network/exploration."""
    witness = SelectionWitness()
    stream = iter(schedule)

    def select(q_values: torch.Tensor, agent_states: BatchedAgentState, action_masks: torch.Tensor | None) -> torch.Tensor:
        assert q_values.shape == (env.num_agents, env.action_dim)
        assert torch.isfinite(q_values).all()
        assert agent_states.observations.shape[0] == env.num_agents
        actions = action_ids(env, next(stream))
        assert actions.shape == (env.num_agents,)
        assert action_masks is not None
        active = ~env.dones
        assert action_masks[torch.arange(env.num_agents, device=env.device), actions][active].all()
        witness.q_values.append(q_values.detach().clone())
        witness.actions.append(actions.clone())
        return actions

    with patch.object(exploration, "select_actions", side_effect=select):
        yield witness


@dataclass
class LaneTick:
    """Independent pre/post sticky-done evidence and actual published readings."""

    active_before: torch.Tensor
    new_done: torch.Tensor
    actions: torch.Tensor
    rewards: torch.Tensor
    dones: torch.Tensor
    info: dict
    world_tick: int


@contextmanager
def observe_environment_steps(env: VectorizedHamletEnv) -> Iterator[list[LaneTick]]:
    """Collect owned readings without replacing environment transition execution."""
    ticks: list[LaneTick] = []
    original_step = env.step

    def step(actions: torch.Tensor, depletion_multiplier: float = 1.0):
        previous = env.dones.clone()
        result = original_step(actions, depletion_multiplier)
        _, rewards, dones, info = result
        snapshot = {
            key: {name: value.clone() for name, value in item.items()} if isinstance(item, dict) else item.clone()
            for key, item in info.items()
            if isinstance(item, torch.Tensor) or key == "reward_components"
        }
        ticks.append(LaneTick(~previous, ~previous & dones, actions.clone(), rewards.clone(), dones.clone(), snapshot, env.global_tick))
        return result

    with patch.object(env, "step", side_effect=step):
        yield ticks
