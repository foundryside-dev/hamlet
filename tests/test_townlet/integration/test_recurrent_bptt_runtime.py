"""Config-in/behaviour-out pins for token-native recurrent training."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import torch
import yaml

from townlet.agent.networks import RecurrentTokenQNetwork
from townlet.demo.runner import DemoRunner
from townlet.population.vectorized import VectorizedPopulation

LEVEL_NAME = "L2_partial_observability"
MAX_EPISODES = 24

RECURRENT_ARCHITECTURE = {
    "type": "recurrent",
    "recurrent": {
        "token_embed_dim": 32,
        "aggregator": {"type": "mean"},
        "lstm": {"hidden_size": 64, "num_layers": 1, "dropout": 0.0},
        "q_head_hidden_dim": 64,
    },
}


def _make_pack(tmp_path: Path, name: str, *, sequence_length: int) -> Path:
    target = tmp_path / name
    shutil.copytree(Path("configs") / "default_curriculum", target)
    shutil.rmtree(target / ".compiled", ignore_errors=True)

    brain_path = target / "brain.yaml"
    brain = yaml.safe_load(brain_path.read_text())
    brain["architecture"] = RECURRENT_ARCHITECTURE
    brain_path.write_text(yaml.safe_dump(brain, sort_keys=False))

    training_path = target / "levels" / LEVEL_NAME / "training.yaml"
    training = yaml.safe_load(training_path.read_text())
    block = training["training"]
    block["population"]["size"] = 8
    block["q_learning"]["use_double_dqn"] = True
    block["replay_buffer"]["batch_size"] = 12
    block["replay_buffer"]["min_size"] = 16
    loop = block["training_loop"]
    loop["max_episodes"] = MAX_EPISODES
    loop["max_steps_per_episode"] = 40
    loop["train_frequency"] = 4
    loop["sequence_length"] = sequence_length
    training_path.write_text(yaml.safe_dump(training, sort_keys=False))
    return target


def _run(pack: Path, output: Path) -> VectorizedPopulation:
    with DemoRunner(
        config_dir=pack,
        db_path=output.with_suffix(".sqlite"),
        checkpoint_dir=output,
        level_name=LEVEL_NAME,
    ) as runner:
        runner.run()
        return runner.population


def test_recurrent_brain_yaml_trains_the_recurrent_weight_matrix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Real configured training must backpropagate into LSTM recurrence."""
    gradients: list[float] = []
    original_init = RecurrentTokenQNetwork.__init__

    def instrumented_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.lstm.weight_hh_l0.register_hook(lambda gradient: gradients.append(float(gradient.abs().max())))

    monkeypatch.setattr(RecurrentTokenQNetwork, "__init__", instrumented_init)
    population = _run(_make_pack(tmp_path, "gradient", sequence_length=8), tmp_path / "gradient-output")

    assert population.is_recurrent
    assert isinstance(population.q_network, RecurrentTokenQNetwork)
    assert gradients, "no real training backward pass reached the LSTM"
    assert all(gradient > 0.0 for gradient in gradients), "a recurrent training update produced an exactly-zero recurrent gradient"


@pytest.mark.parametrize("sequence_length", [2, 8])
def test_training_passes_the_configured_sequence_in_one_network_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sequence_length: int,
) -> None:
    """The authored BPTT length reaches the network as one sequence tensor."""
    calls: list[tuple[int, int, bool]] = []
    original_forward = RecurrentTokenQNetwork.forward

    def instrumented_forward(self, observations, hidden):
        calls.append((int(observations.shape[0]), int(observations.shape[1]), torch.is_grad_enabled()))
        return original_forward(self, observations, hidden)

    monkeypatch.setattr(RecurrentTokenQNetwork, "forward", instrumented_forward)
    population = _run(
        _make_pack(tmp_path, f"sequence-{sequence_length}", sequence_length=sequence_length),
        tmp_path / f"sequence-{sequence_length}-output",
    )

    assert population.sequence_length == sequence_length
    gradient_training_calls = [call for call in calls if call[0] == population.batch_size and call[2]]
    assert gradient_training_calls, "training never called the recurrent network with gradients enabled"
    assert {call[1] for call in gradient_training_calls} == {sequence_length}


def test_training_does_not_clobber_mid_episode_rollout_memory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Zero-start replay unrolls must not overwrite population-owned rollout state."""
    lstm_calls: list[tuple[int, int, torch.Tensor]] = []
    original_init = RecurrentTokenQNetwork.__init__

    def instrumented_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)

        def record_hidden(_module, inputs):
            sequence, hidden = inputs
            zero_mask = hidden[0].abs().sum(dim=(0, 2)) == 0
            lstm_calls.append((int(sequence.shape[0]), int(sequence.shape[1]), zero_mask.clone()))

        self.lstm.register_forward_pre_hook(record_hidden)

    monkeypatch.setattr(RecurrentTokenQNetwork, "__init__", instrumented_init)

    observed: list[tuple[torch.Tensor, torch.Tensor]] = []
    original_step = VectorizedPopulation.step_population

    def instrumented_step(self, env):
        start = len(lstm_calls)
        counts_before = self.episode_step_counts.clone()
        result = original_step(self, env)
        for batch_size, sequence_length, zero_mask in lstm_calls[start:]:
            if batch_size == self.num_agents and sequence_length == 1:
                observed.append((counts_before, zero_mask))
        return result

    monkeypatch.setattr(VectorizedPopulation, "step_population", instrumented_step)
    population = _run(_make_pack(tmp_path, "rollout-memory", sequence_length=8), tmp_path / "rollout-memory-output")

    assert population.last_training_step > 0, "training never ran"
    mid_episode = [(counts, zeros) for counts, zeros in observed if bool((counts > 0).any())]
    assert mid_episode, "no mid-episode rollout forward was observed"
    assert not any(bool((zeros & (counts > 0)).any()) for counts, zeros in mid_episode)
