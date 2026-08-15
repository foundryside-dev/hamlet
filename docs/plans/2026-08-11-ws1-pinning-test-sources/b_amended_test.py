"""Config-in / behaviour-out pins for recurrent (LSTM) training.

These tests take a YAML config pack, change values in it, and assert that the
RUNTIME behaviour of training changes accordingly:

  * brain.yaml  architecture.type: recurrent   -> the LSTM recurrent weight
    matrix (weight_hh_l0) must receive gradient from real training updates.
  * training.yaml training_loop.sequence_length -> the number of timesteps that
    backpropagation-through-time actually reaches must equal that value.
  * a training update must not destroy the rollout hidden state mid-episode.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import torch
import yaml

from townlet.agent.networks import RecurrentSpatialQNetwork
from townlet.demo.runner import DemoRunner

LEVEL_NAME = "L2_partial_observability"
MAX_EPISODES = 24

RECURRENT_ARCHITECTURE = {
    "type": "recurrent",
    "recurrent": {
        "vision_encoder": {"channels": [16, 32], "kernel_sizes": [3, 3], "strides": [1, 1], "padding": [1, 1], "activation": "relu"},
        "position_encoder": {"hidden_sizes": [32], "activation": "relu"},
        "meter_encoder": {"hidden_sizes": [32], "activation": "relu"},
        "affordance_encoder": {"hidden_sizes": [32], "activation": "relu"},
        "lstm": {"hidden_size": 256, "num_layers": 1, "dropout": 0.0},
        "q_head": {"hidden_sizes": [128], "activation": "relu"},
    },
}


def _make_pack(tmp_path: Path, name: str, *, architecture: dict, sequence_length: int) -> Path:
    target = tmp_path / name
    shutil.copytree(Path("configs") / "default_curriculum", target)

    brain = yaml.safe_load((target / "brain.yaml").read_text())
    brain["architecture"] = architecture
    (target / "brain.yaml").write_text(yaml.safe_dump(brain, sort_keys=False))

    training_path = target / "levels" / LEVEL_NAME / "training.yaml"
    training = yaml.safe_load(training_path.read_text())
    block = training["training"]
    block["population"]["size"] = 8
    block["replay_buffer"]["batch_size"] = 12
    block["replay_buffer"]["min_size"] = 16
    # Explicit: the expected unroll length below depends on the DQN variant.
    block["q_learning"]["use_double_dqn"] = True
    loop = block["training_loop"]
    loop["max_episodes"] = MAX_EPISODES
    loop["max_steps_per_episode"] = 40
    loop["train_frequency"] = 4
    loop["sequence_length"] = sequence_length
    training_path.write_text(yaml.safe_dump(training, sort_keys=False))
    return target


def _run(pack: Path, tmp_path: Path):
    with DemoRunner(
        config_dir=pack,
        db_path=tmp_path / f"{pack.name}.sqlite",
        checkpoint_dir=tmp_path / f"{pack.name}-ckpt",
        level_name=LEVEL_NAME,
    ) as runner:
        runner.run()
        return runner.population


def test_recurrent_brain_yaml_trains_the_recurrent_weight_matrix(tmp_path: Path, monkeypatch) -> None:
    """architecture.type: recurrent must make weight_hh_l0 receive real gradient."""
    grads: list[float] = []
    original_init = RecurrentSpatialQNetwork.__init__

    def instrumented(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.lstm.weight_hh_l0.register_hook(lambda g: grads.append(float(g.abs().max())))

    monkeypatch.setattr(RecurrentSpatialQNetwork, "__init__", instrumented)

    pack = _make_pack(tmp_path, "recurrent", architecture=RECURRENT_ARCHITECTURE, sequence_length=8)
    population = _run(pack, tmp_path)

    assert population.is_recurrent
    assert isinstance(population.q_network, RecurrentSpatialQNetwork)
    assert grads, "no backward pass reached the LSTM: training never ran"
    zero_grad_updates = [g for g in grads if g == 0.0]
    assert not zero_grad_updates, (
        f"{len(zero_grad_updates)}/{len(grads)} training updates gave lstm.weight_hh_l0 exactly zero gradient: "
        "the recurrent weights are frozen at initialisation (hidden state is not threaded through the unroll)"
    )


@pytest.mark.parametrize("sequence_length", [2, 8])
def test_training_unroll_threads_hidden_state_for_configured_sequence_length(
    tmp_path: Path, monkeypatch, sequence_length: int
) -> None:
    """training_loop.sequence_length is the length of the threaded BPTT unroll.

    Instruments the real network's forward() during a real DemoRunner run and inspects
    what the real training block passed in: a threaded unroll shows runs of exactly
    `sequence_length` consecutive training forwards where each call receives the hidden
    state returned by the previous one.
    """
    calls: list[dict] = []
    original_forward = RecurrentSpatialQNetwork.forward

    def instrumented(self, obs, hidden=None):
        q_values, new_hidden = original_forward(self, obs, hidden)
        calls.append(
            {
                "batch": int(obs.shape[0]),
                "h_in": None if hidden is None else hidden[0].detach().clone(),
                "h_out": new_hidden[0].detach().clone(),
            }
        )
        return q_values, new_hidden

    monkeypatch.setattr(RecurrentSpatialQNetwork, "forward", instrumented)

    pack = _make_pack(tmp_path, f"seq{sequence_length}", architecture=RECURRENT_ARCHITECTURE, sequence_length=sequence_length)
    population = _run(pack, tmp_path)
    assert population.sequence_length == sequence_length

    # Replay batch size (12) is deliberately different from population size (8) so training
    # forwards and rollout forwards are separable by batch dimension alone.
    training_calls = [c for c in calls if c["batch"] == population.batch_size]
    assert training_calls, "training never ran"

    runs: list[int] = []
    for index, call in enumerate(training_calls):
        starts_new_run = call["h_in"] is None or not bool(call["h_in"].any())
        if starts_new_run:
            runs.append(1)
            continue
        assert runs, "threaded training forward with no preceding run start"
        previous = training_calls[index - 1]
        assert torch.equal(call["h_in"], previous["h_out"]), "training forward did not receive the previous timestep's hidden state"
        runs[-1] += 1

    # +1 = the window-boundary successor forward added by WS-1(c): after unrolling the
    # window the successor state next_observations[:, -1] is evaluated under the hidden
    # state the unroll ended on, which extends the threaded run by exactly one call.
    expected_run_length = sequence_length + 1
    assert set(runs) == {expected_run_length}, (
        f"threaded training unrolls had lengths {sorted(set(runs))}, expected exactly "
        f"{expected_run_length} = training_loop.sequence_length ({sequence_length}) from "
        "training.yaml + 1 boundary-successor forward"
    )


def test_training_update_does_not_clobber_rollout_hidden_state(tmp_path: Path, monkeypatch) -> None:
    """A training update must leave the rollout LSTM memory intact."""
    from townlet.population.vectorized import VectorizedPopulation

    norms_when_training_fired: list[float] = []
    original_step = VectorizedPopulation.step_population

    def instrumented(self, envs):
        result = original_step(self, envs)
        trained_this_step = self.last_training_step == self.total_steps
        if trained_this_step and not bool(result.dones.any()):
            norms_when_training_fired.append(float(self.rollout_hidden[0].norm()))
        return result

    monkeypatch.setattr(VectorizedPopulation, "step_population", instrumented)

    pack = _make_pack(tmp_path, "clobber", architecture=RECURRENT_ARCHITECTURE, sequence_length=8)
    _run(pack, tmp_path)

    assert norms_when_training_fired, "no mid-episode training update was observed"
    zeroed = [n for n in norms_when_training_fired if n == 0.0]
    assert not zeroed, (
        f"{len(zeroed)}/{len(norms_when_training_fired)} mid-episode training updates left the rollout hidden "
        "state at exactly zero: training is clobbering rollout memory"
    )
