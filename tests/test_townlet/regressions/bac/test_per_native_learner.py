"""Two ordinary public learner updates must survive finite, large DAC rewards.

The high-alpha1 case qualifies C01 only after its real first update succeeds.
Compiler admission, reward bounds and liveness are explicit prerequisites; an
earlier failure is not evidence of the replay normalization defect. This uses
the shipped global-NumPy/physical-index learner adapter, not captured replay.
"""

from __future__ import annotations

import hashlib
import json
import math
import warnings
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
import yaml

from townlet.config.brain_config import apply_training_overrides
from townlet.curriculum.factory import build_curriculum
from townlet.demo.runner import DemoRunner
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
from townlet.population.vectorized import VectorizedPopulation
from townlet.training.prioritized_replay_buffer import PrioritizedReplayBuffer

CPU = torch.device("cpu")
LEVEL = "L1_full_observability"


def _authored_pack(destination: Path, *, base: float, alpha: float) -> tuple[Path, str]:
    """Copy YAML DATA only; public loading/compilation performs all validation."""
    source = Path(__file__).resolve().parents[4] / "configs" / "default_curriculum"
    for original in sorted(source.rglob("*")):
        relative = original.relative_to(source)
        if original.suffix not in {".yaml", ".yml"} or ".compiled" in relative.parts:
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(original.read_text())
    brain_path = destination / "brain.yaml"
    brain = yaml.safe_load(brain_path.read_text())
    assert brain["architecture"]["type"] == "feedforward"
    assert brain["architecture"]["feedforward"]["dropout"] == 0.0
    brain["optimizer"]["learning_rate"] = 0.0001
    brain["loss"] = {"type": "huber", "huber_delta": 0.25}
    brain["q_learning"].update(gamma=0.0, target_update_frequency=1000)
    brain["replay"].update(capacity=2, prioritized=True, priority_alpha=alpha, priority_beta=1.0, priority_beta_annealing=False)
    brain_path.write_text(yaml.safe_dump(brain, sort_keys=False))
    training_path = destination / "levels" / LEVEL / "training.yaml"
    training_document = yaml.safe_load(training_path.read_text())
    training = training_document["training"]
    training["population"]["size"] = 2
    training["q_learning"].update(gamma=0.0, learning_rate=0.0001, target_update_frequency=1000)
    training["replay_buffer"].update(capacity=2, batch_size=2, min_size=2)
    training["training_loop"].update(max_episodes=1, max_steps_per_episode=20, train_frequency=1, sequence_length=1, max_grad_norm=10.0)
    training_path.write_text(yaml.safe_dump(training_document, sort_keys=False))
    drive_path = destination / "levels" / LEVEL / "drive.yaml"
    drive_document = yaml.safe_load(drive_path.read_text())
    drive = drive_document["drive"]
    assert drive["extrinsic"]["type"] == "constant_base_with_shaped_bonus"
    drive["extrinsic"].update(base_reward=base, bar_bonuses=[], variable_bonuses=[], apply_modifiers=[])
    drive["composition"].update(normalize=False, clip=None)
    drive_path.write_text(yaml.safe_dump(drive_document, sort_keys=False))
    digest = hashlib.sha256()
    for path in sorted(destination.rglob("*.yaml")):
        digest.update(str(path.relative_to(destination)).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return destination, digest.hexdigest()


def _report(record_property: Callable[[str, Any], None], name: str, evidence: dict[str, Any]) -> None:
    encoded = json.dumps(evidence, sort_keys=True)
    record_property(name, encoded)
    print(f"T13 {name}: {encoded}")


def _observe_update(
    population: VectorizedPopulation,
    env: VectorizedHamletEnv,
    *,
    tick: int,
    base: float,
    alpha: float,
    record_property: Callable[[str, Any], None],
) -> None:
    observations = population.current_obs.detach().clone()
    masks = env.get_action_masks().detach().clone()
    assert torch.isfinite(observations).all(), "prerequisite: finite public observations"
    assert not env.dones.any(), "prerequisite: both ordinary lanes must enter this tick live"
    assert masks.shape == (2, env.action_dim) and masks.any(dim=1).all()
    before = {name: value.detach().clone() for name, value in population.q_network.named_parameters()}
    assert before and all(torch.isfinite(value).all() for value in before.values())
    before_max = max(float(value.abs().max()) for value in before.values())
    assert before_max <= 1e6
    with torch.no_grad():
        q_before = population.q_network(observations).detach().clone()
    assert q_before.shape == (2, env.action_dim)
    assert torch.isfinite(q_before).all() and q_before.abs().max() <= 1e6
    assert torch.count_nonzero(q_before) > 0, "prerequisite: nontrivial real network forward"
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        try:
            state = population.step_population(env)
        except Exception as error:
            error.add_note(
                f"T13 ordinary tick {tick}; completed learner updates={population.training_step_counter}; "
                f"base={base}, alpha={alpha}. Earlier admission/runtime errors do not establish C01."
            )
            raise
        finally:
            _report(record_property, f"tick_{tick}_warnings", {"warnings": [str(item.message) for item in observed]})
    metrics = population.get_training_metrics()
    assert population.training_step_counter == tick and metrics["training_step"] == tick
    assert math.isfinite(metrics["loss"]), "prerequisite: the actual Huber learner loss must remain finite"
    after = dict(population.q_network.named_parameters())
    assert all(torch.isfinite(value).all() for value in after.values())
    changed = sum(not torch.equal(before[name], value.detach()) for name, value in after.items())
    assert changed > 0, "real optimizer must change parameters"
    after_max = max(float(value.detach().abs().max()) for value in after.values())
    assert after_max <= 1e6
    optimizer_state = population.optimizer.state_dict()["state"]
    assert optimizer_state, "real Adam optimizer must own updated moments"
    for values in optimizer_state.values():
        assert float(values["step"].item()) == tick
        assert all(torch.isfinite(value).all() for value in values.values() if isinstance(value, torch.Tensor))
    with torch.no_grad():
        q_after = population.q_network(observations)
    assert torch.isfinite(q_after).all() and not torch.equal(q_before, q_after)
    assert state.info["active_on_entry"].all(), "prerequisite: this update must contain both real lanes"
    assert masks.gather(1, state.actions[:, None]).all(), "ordinary selected actions must have been legal"
    torch.testing.assert_close(q_before, torch.tensor(state.info["q_values"], dtype=q_before.dtype, device=CPU), rtol=0.0, atol=0.0)
    rows = population.replay_buffer.serialize()
    assert rows["size_current"] == 2 and rows["capacity"] == 2
    assert rows["alpha"] == alpha and rows["beta"] == 1.0 and not rows["beta_annealing"]
    torch.testing.assert_close(rows["observations"], observations, rtol=0.0, atol=0.0)
    torch.testing.assert_close(rows["next_observations"], state.observations, rtol=0.0, atol=0.0)
    assert torch.equal(rows["actions"], state.actions) and torch.equal(rows["dones"], state.dones)
    assert torch.equal(rows["rewards"], state.rewards)
    assert torch.isfinite(state.observations).all() and torch.isfinite(state.rewards).all()
    component_evidence = {}
    for name in ("extrinsic", "intrinsic", "shaping"):
        actual = state.info["reward_components"][name]
        assert torch.isfinite(actual).all()
        assert torch.equal(rows[f"rewards_{name}"], actual)
        assert rows[f"rewards_{name}_present"].all()
        if name != "extrinsic":
            assert actual.abs().max() <= 1e6, "prerequisite: other ordinary DAC components stay small"
        component_evidence[name] = actual.tolist()
    intrinsic_weight = state.info["intrinsic_weight"]
    assert intrinsic_weight is None or torch.isfinite(intrinsic_weight).all()
    selected_q = q_before.gather(1, rows["actions"][:, None]).squeeze(1).double().numpy()
    # Gamma is zero in both admitted declarations, so this independent TD bound
    # needs neither the learner's bootstrap implementation nor post-update Q.
    td = np.abs(rows["rewards"].double().numpy() - selected_q)
    priorities = rows["priorities"][:2].astype(np.float64)
    assert np.isfinite(td).all() and np.isfinite(priorities).all() and (priorities > 0).all()
    np.testing.assert_allclose(priorities, td + 1e-6, rtol=2e-6, atol=1e-6)
    scores = priorities**alpha
    probabilities = scores / scores.sum(dtype=np.float64)
    assert np.isfinite(probabilities).all() and (probabilities > 0).all()
    assert probabilities.sum() == pytest.approx(1.0)
    if base > 1e38:
        assert ((state.rewards.double() >= 1.9e38) & (state.rewards.double() <= 2.1e38)).all()
        assert ((td >= 1.9e38) & (td <= 2.1e38)).all()
        assert priorities.sum(dtype=np.float64) > np.finfo(np.float32).max
        np.testing.assert_allclose(probabilities, [0.5, 0.5], rtol=0.0, atol=1e-6)
    _report(
        record_property,
        f"tick_{tick}_actual_update",
        {
            "updates": population.training_step_counter,
            "loss": metrics["loss"],
            "mean_td_logging": str(metrics["td_error"]),
            "pre_q_abs_max": float(q_before.abs().max()),
            "parameter_abs_max_before": before_max,
            "parameter_abs_max_after": after_max,
            "changed_parameter_tensors": changed,
            "adam_steps": sorted({float(values["step"].item()) for values in optimizer_state.values()}),
            "actions": state.actions.tolist(),
            "dones": state.dones.tolist(),
            "dac_totals": state.rewards.tolist(),
            "dac_components": component_evidence,
            "intrinsic_weight": None if intrinsic_weight is None else intrinsic_weight.tolist(),
            "pre_optimizer_td": td.tolist(),
            "priorities": priorities.tolist(),
            "float64_priority_sum": float(priorities.sum(dtype=np.float64)),
            "float64_probabilities": probabilities.tolist(),
        },
    )
    assert tick == 2 or not state.dones.any(), "prerequisite: two live ticks; report an early terminal boundary before qualifying C01"


@pytest.mark.parametrize(
    ("base", "alpha"),
    [(1.0, 1.0), (2e38, 0.0), (2e38, 1.0)],
    ids=["modest-alpha1-control", "large-alpha0-control", "large-alpha1-c01"],
)
def test_public_learner_two_finite_priority_updates(
    tmp_path: Path, record_property: Callable[[str, Any], None], base: float, alpha: float
) -> None:
    """Catch float32 priority normalization failure after genuine learner TD updates."""
    pack, data_hash = _authored_pack(tmp_path / "pack", base=base, alpha=alpha)
    _report(record_property, "authored_data", {"base": base, "alpha": alpha, "yaml_sha256": data_hash, "capacity": 2})
    numpy_state = np.random.get_state()
    try:
        np.random.seed(731)
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(731)
            with DemoRunner(
                config_dir=pack,
                db_path=tmp_path / "learner.db",
                checkpoint_dir=tmp_path / "checkpoints",
                max_episodes=1,
                level_name=LEVEL,
            ) as runner:
                training = runner.training_config
                loop = training.training_loop
                brain = apply_training_overrides(runner.brain_config, training)
                assert brain.architecture.type == "feedforward" and brain.replay.prioritized
                assert brain.replay.capacity == training.replay_buffer.capacity == 2
                assert training.replay_buffer.batch_size == training.replay_buffer.min_size == 2
                assert brain.replay.priority_alpha == alpha and brain.replay.priority_beta == 1.0
                assert brain.replay.priority_beta_annealing is False
                assert runner.brain_config.q_learning.gamma == training.q_learning.gamma == brain.q_learning.gamma == 0.0
                assert brain.loss.type == "huber" and brain.loss.huber_delta == 0.25
                assert brain.optimizer.learning_rate == 0.0001
                assert loop.max_grad_norm == 10.0 and loop.train_frequency == loop.sequence_length == 1
                assert loop.max_steps_per_episode == 20
                _report(
                    record_property,
                    "admitted_config",
                    {"brain": brain.model_dump(mode="json"), "training": training.model_dump(mode="json")},
                )
                env = VectorizedHamletEnv.from_universe(runner.compiled, level_name=runner.level_name, num_agents=2, device=CPU)
                curriculum = build_curriculum(training, max_steps_per_episode=loop.max_steps_per_episode, device=CPU)
                curriculum.initialize_population(2)
                exploration = EpsilonGreedyExploration(epsilon=0.5, epsilon_decay=0.99, epsilon_min=0.1)
                population = VectorizedPopulation(
                    env=env,
                    curriculum=curriculum,
                    exploration=exploration,
                    agent_ids=["agent_0", "agent_1"],
                    device=CPU,
                    obs_dim=env.observation_dim,
                    brain_config=brain,
                    train_frequency=loop.train_frequency,
                    batch_size=training.replay_buffer.batch_size,
                    sequence_length=loop.sequence_length,
                    max_grad_norm=loop.max_grad_norm,
                    action_dim=env.action_dim,
                    max_episodes=1,
                    max_steps_per_episode=loop.max_steps_per_episode,
                )
                runner.env, runner.curriculum, runner.exploration, runner.population = env, curriculum, exploration, population
                assert isinstance(population.replay_buffer, PrioritizedReplayBuffer) and population.use_per and not population.is_recurrent
                assert isinstance(population.optimizer, torch.optim.Adam)
                assert population.gamma == 0.0 and population.loss_delta == 0.25
                assert population.training_step_counter == 0 and not population.optimizer.state_dict()["state"]
                population.reset()
                for tick in (1, 2):
                    _observe_update(population, env, tick=tick, base=base, alpha=alpha, record_property=record_property)
    finally:
        np.random.set_state(numpy_state)
