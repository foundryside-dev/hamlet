"""Config-in/behaviour-out pins for token-native recurrent training."""

from __future__ import annotations

import shutil
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

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
    captured = {}
    original_initialize = VectorizedPopulation._initialize

    def initialize(self, *args, **kwargs):
        original_initialize(self, *args, **kwargs)
        captured["population"] = self
        captured["before"] = [parameter.detach().clone() for parameter in self.q_network.parameters()]
        captured["steps"] = stack.enter_context(patch.object(self.optimizer, "step", wraps=self.optimizer.step))

    with ExitStack() as stack:
        stack.enter_context(patch.object(VectorizedPopulation, "_initialize", new=initialize))
        runner = stack.enter_context(
            DemoRunner(
                config_dir=pack,
                db_path=output.with_suffix(".sqlite"),
                checkpoint_dir=output,
                level_name=LEVEL_NAME,
            )
        )
        runner.run()
        population = captured["population"]
        steps = captured["steps"]
        assert steps.call_count > 0, "configured run performed no real optimizer update"
        assert steps.call_count == population.training_step_counter
        assert any(
            not torch.equal(old, current) for old, current in zip(captured["before"], population.q_network.parameters(), strict=True)
        )
        return population


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
def test_training_keeps_the_configured_sequence_graph_connected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sequence_length: int,
) -> None:
    """Detaching a real prefix must sever the measured final-to-earlier derivative."""
    requests = []
    sampled_lengths = []
    original_request = VectorizedPopulation._replay_request

    def request(self):
        result = original_request(self)
        assert result.sequence_length == sequence_length
        requests.append(result)
        return result

    full_horizon_rows = []
    original_predictions = VectorizedPopulation._recurrent_predictions

    def predictions(self, batch):
        assert batch.observations.shape[1] <= sequence_length
        assert bool((batch.lengths <= sequence_length).all())
        sampled_lengths.append(batch.lengths.detach().clone())
        initial_hidden_ids = set()
        first_prefixes = []
        original_hidden = self.q_network.initial_hidden

        def initial_hidden(*args, **kwargs):
            hidden = original_hidden(*args, **kwargs)
            initial_hidden_ids.add(id(hidden[0]))
            return hidden

        def forward_hook(_module, inputs, output):
            # Identify the FIRST real prefix by the actual initial-hidden object,
            # never by a zero-value heuristic or a later connected timestep.
            if torch.is_grad_enabled() and id(inputs[1][0]) in initial_hidden_ids:
                initial_hidden_ids.remove(id(inputs[1][0]))
                first_prefixes.append((inputs[0].detach().clone(), output[1][0]))

        hook = self.q_network.register_forward_hook(forward_hook)
        try:
            with patch.object(self.q_network, "initial_hidden", new=initial_hidden):
                result = original_predictions(self, batch)
        finally:
            hook.remove()
        values, _, _ = result
        full_rows = torch.nonzero(batch.lengths == sequence_length, as_tuple=False).flatten()
        if len(full_rows):
            first_observations = batch.observations[full_rows, :1]
            first_hidden = [hidden for observations, hidden in first_prefixes if torch.equal(observations, first_observations)]
            assert first_hidden, "actual full-length group had no observed first real prefix"
            for row in full_rows.tolist():
                assert bool(batch.loss_mask[row, sequence_length - 1]), "final full-length prediction was not selected for the loss"
                derivatives = torch.autograd.grad(values[row, sequence_length - 1], first_hidden, retain_graph=True, allow_unused=True)
                connected = [gradient for gradient in derivatives if gradient is not None and bool((gradient != 0).any())]
                assert len(connected) == 1, "final selected prediction lost its FIRST real prefix across the configured horizon"
                assert torch.isfinite(connected[0]).all(), "full-horizon derivative is nonfinite"
                full_horizon_rows.append((self.training_step_counter, row, sequence_length))
        return result

    monkeypatch.setattr(VectorizedPopulation, "_replay_request", request)
    monkeypatch.setattr(VectorizedPopulation, "_recurrent_predictions", predictions)
    population = _run(
        _make_pack(tmp_path, f"sequence-{sequence_length}", sequence_length=sequence_length),
        tmp_path / f"sequence-{sequence_length}-output",
    )

    assert population.sequence_length == sequence_length
    assert requests and sampled_lengths, "no real recurrent training batch was observed"
    assert any(bool((lengths == sequence_length).any()) for lengths in sampled_lengths), "authored BPTT length was never sampled"
    assert full_horizon_rows, "no actual full-length update proved its first-to-final recurrent gradient"


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

    observed: list[tuple[torch.Tensor, torch.Tensor, torch.Tensor]] = []
    original_step = VectorizedPopulation.step_population

    def instrumented_step(self, env):
        start = len(lstm_calls)
        counts_before = self.episode_step_counts.clone()
        active_before = (~env.dones).clone()
        result = original_step(self, env)
        for batch_size, sequence_length, zero_mask in lstm_calls[start:]:
            if batch_size == self.num_agents and sequence_length == 1:
                observed.append((counts_before, active_before, zero_mask))
        return result

    monkeypatch.setattr(VectorizedPopulation, "step_population", instrumented_step)
    population = _run(_make_pack(tmp_path, "rollout-memory", sequence_length=8), tmp_path / "rollout-memory-output")

    assert population.last_training_step > 0, "training never ran"
    mid_episode = [(counts, active, zeros) for counts, active, zeros in observed if bool(((counts > 0) & active).any())]
    assert mid_episode, "no mid-episode rollout forward was observed"
    assert not any(bool((zeros & (counts > 0) & active).any()) for counts, active, zeros in mid_episode)
    # Completed lanes retain their survival count and clear their hidden state.
    # They are no longer mid-episode forwards, even while another lane is live.
    completed = [(counts, active, zeros) for counts, active, zeros in observed if bool(((counts > 0) & ~active).any())]
    assert completed, "no completed lane was observed alongside a live lane"
    assert all(bool(zeros[(counts > 0) & ~active].all()) for counts, active, zeros in completed)
