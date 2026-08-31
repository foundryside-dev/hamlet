"""Guards against reintroducing a whole fixed-width observation ABI."""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import torch

from townlet.agent.network_factory import NetworkFactory
from townlet.config.brain_config import FeedforwardConfig, SetAggregatorConfig, TokenSetConfig
from townlet.curriculum.static import StaticCurriculum
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
from townlet.population.vectorized import VectorizedPopulation
from townlet.training.replay_buffer import ReplayBuffer
from townlet.training.state import RewardTensor
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/default_curriculum")
LEVEL = "L1_full_observability"
CPU = torch.device("cpu")
SOURCE_ROOT = Path("src/townlet")
FIXED_NAMES = frozenset({"fixed_total_dims", "fixed_row_layout"})
ALLOWED_FIXED_REFERENCES = Counter(
    {
        ("universe/dto/token_spec.py", "definition", "fixed_total_dims"): 1,
        ("universe/dto/token_spec.py", "definition", "fixed_row_layout"): 1,
        ("universe/__main__.py", "attribute", "fixed_total_dims"): 2,
    }
)
FORBIDDEN_WHOLE_OBSERVATION_CALLABLES = frozenset(
    {
        "expand",
        "expand_observation",
        "expand_full_observation",
        "reconstruct",
        "reconstruct_observation",
        "reconstruct_full_observation",
    }
)


def _production_fixed_references() -> Counter[tuple[str, str, str]]:
    references: Counter[tuple[str, str, str]] = Counter()
    for path in SOURCE_ROOT.rglob("*.py"):
        relative = path.relative_to(SOURCE_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in FIXED_NAMES:
                references[(relative, "definition", node.name)] += 1
            elif isinstance(node, ast.Attribute) and node.attr in FIXED_NAMES:
                references[(relative, "attribute", node.attr)] += 1
            elif isinstance(node, ast.Name) and node.id in FIXED_NAMES:
                references[(relative, "name", node.id)] += 1
    return references


def _assert_no_whole_observation_callable(label: str, obj: object) -> None:
    exposed = sorted(name for name in FORBIDDEN_WHOLE_OBSERVATION_CALLABLES if callable(getattr(obj, name, None)))
    assert exposed == [], f"{label} exposes forbidden whole-observation callables: {exposed}"


def _guard_allocator(
    name: str,
    allocator: Callable[..., torch.Tensor],
    fixed_width: int,
) -> Callable[..., torch.Tensor]:
    def guarded(*args: Any, **kwargs: Any) -> torch.Tensor:
        result = allocator(*args, **kwargs)
        if result.ndim > 0 and result.shape[-1] == fixed_width:
            pytest.fail(f"torch.{name} allocated a forbidden whole fixed observation tensor: {tuple(result.shape)}")
        return result

    return guarded


def test_fixed_shape_names_are_limited_to_artifact_definitions_and_cli_reporting() -> None:
    assert _production_fixed_references() == ALLOWED_FIXED_REFERENCES


def test_vertical_runtime_has_no_whole_fixed_observation_surface_or_allocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initial = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)
    fixed_width = initial.get_level(LEVEL).token_spec.fixed_total_dims
    assert fixed_width == 4090

    for name in ("zeros", "full", "zeros_like"):
        allocator = getattr(torch, name)
        monkeypatch.setattr(torch, name, _guard_allocator(name, allocator, fixed_width))

    universe = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)
    env = VectorizedHamletEnv(universe=universe, level_name=LEVEL, num_agents=4, device=CPU)
    observations = env.reset()
    wait = torch.full((4,), env.action_ids["WAIT"], dtype=torch.long, device=CPU)
    next_observations, rewards, dones, _ = env.step(wait)

    replay = ReplayBuffer(capacity=8, device=CPU)
    replay.push(
        observations,
        wait,
        RewardTensor(total=rewards),
        next_observations,
        dones,
    )
    sampled = replay.sample(4)

    flat_network = NetworkFactory.build_feedforward(
        FeedforwardConfig(hidden_layers=[16], activation="relu", dropout=0.0, layer_norm=False),
        obs_dim=env.observation_dim,
        action_dim=env.action_dim,
    )
    token_network = NetworkFactory.build_token_set(
        TokenSetConfig(
            token_embed_dim=16,
            aggregator=SetAggregatorConfig(type="mean"),
            q_head_hidden_dim=16,
        ),
        action_dim=env.action_dim,
        token_spec=env.token_spec,
    )
    assert flat_network(sampled["observations"]).shape == (4, env.action_dim)
    assert token_network(sampled["observations"]).shape == (4, env.action_dim)

    curriculum = StaticCurriculum(difficulty_level=0.5)
    curriculum.initialize_population(4)
    population = VectorizedPopulation(
        env=env,
        curriculum=curriculum,
        exploration=EpsilonGreedyExploration(epsilon=0.1, epsilon_min=0.1, epsilon_decay=1.0),
        agent_ids=[f"agent_{index}" for index in range(4)],
        device=CPU,
        obs_dim=env.observation_dim,
        brain_config=universe.brain,
        action_dim=env.action_dim,
        train_frequency=1,
        batch_size=4,
        sequence_length=1,
        max_grad_norm=1.0,
        vision_window_size=1,
    )

    objects = {
        "compiled universe": universe,
        "environment": env,
        "encoder": env._observation_encoder,
        "replay": replay,
        "population": population,
        "flat network": flat_network,
        "token network": token_network,
    }
    for label, obj in objects.items():
        _assert_no_whole_observation_callable(label, obj)

    assert observations.shape == next_observations.shape == (4, env.token_spec.total_dims)
    assert sampled["observations"].shape == (4, env.token_spec.total_dims)
