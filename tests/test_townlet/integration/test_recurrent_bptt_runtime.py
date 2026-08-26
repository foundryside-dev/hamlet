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

from townlet.agent.network_factory import NetworkFactory
from townlet.agent.networks import RecurrentSpatialQNetwork
from townlet.demo.runner import DemoRunner
from townlet.population.vectorized import VectorizedPopulation

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
    # Do not inherit the source pack's compile cache (WS-1(a): cache keying is itself defective).
    shutil.rmtree(target / ".compiled", ignore_errors=True)

    brain = yaml.safe_load((target / "brain.yaml").read_text())
    brain["architecture"] = architecture
    (target / "brain.yaml").write_text(yaml.safe_dump(brain, sort_keys=False))

    training_path = target / "levels" / LEVEL_NAME / "training.yaml"
    training = yaml.safe_load(training_path.read_text())
    block = training["training"]
    block["population"]["size"] = 8
    # Explicit: the expected unroll length below depends on the DQN variant.
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
def test_training_unroll_threads_hidden_state_for_configured_sequence_length(tmp_path: Path, monkeypatch, sequence_length: int) -> None:
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


def test_initial_hidden_is_zero_and_forward_requires_hidden(pomdp_env) -> None:
    """Post-WS-1(b) network API: the network owns no hidden state.

    `initial_hidden(batch_size, device)` is the only factory, and `forward`
    demands the hidden state explicitly - a one-argument call must fail at
    argument binding, so no caller can silently fall back to stale or zero
    memory.

    The input-block slices come from the compiled TokenSpec's contiguous per-type
    serialization; they are required parameters, and this construction previously
    omitted them and survived only by never reaching a forward pass.
    """
    blocks = NetworkFactory.token_block_slices(pomdp_env.token_spec)
    network = RecurrentSpatialQNetwork(
        action_dim=pomdp_env.action_dim,
        window_size=1,
        position_dim=blocks["self"].stop - blocks["self"].start,
        bars_dim=blocks["meter"].stop - blocks["meter"].start,
        num_affordance_types=(blocks["affordance"].stop - blocks["affordance"].start) - 1,
        enable_temporal_features=False,
        hidden_dim=64,
        meters_slice=blocks["meter"],
        affordance_slice=blocks["affordance"],
        position_slice=blocks["self"],
    )

    hidden = network.initial_hidden(4, torch.device("cpu"))
    h, c = hidden
    assert h.shape == (network.lstm.num_layers, 4, 64)
    assert c.shape == (network.lstm.num_layers, 4, 64)
    assert not h.any() and not c.any(), "initial hidden state must be all zeros"

    with pytest.raises(TypeError):
        network(torch.zeros(2, pomdp_env.observation_dim))  # hidden is required, not optional


def test_the_input_block_slices_are_required_at_construction(pomdp_env) -> None:
    """The slices are mandatory at BINDING, not discovered on the first forward pass.

    They used to default to None, so a network built without them constructed happily,
    moved to a device, and only then raised inside `forward()` — potentially
    mid-training. A parameter the object cannot function without is not optional
    (No-Defaults Principle); the failure now lands at the authoring mistake instead of
    arbitrarily far downstream. `grid_slice` is the ONE exception and stays optional:
    "no spatial window" is a real universe, and a token observation is always one.
    """
    blocks = NetworkFactory.token_block_slices(pomdp_env.token_spec)
    kwargs = {
        "action_dim": pomdp_env.action_dim,
        "window_size": 1,
        "position_dim": blocks["self"].stop - blocks["self"].start,
        "bars_dim": blocks["meter"].stop - blocks["meter"].start,
        "num_affordance_types": (blocks["affordance"].stop - blocks["affordance"].start) - 1,
        "enable_temporal_features": False,
        "hidden_dim": 64,
        "meters_slice": blocks["meter"],
        "affordance_slice": blocks["affordance"],
    }

    for omitted in ("meters_slice", "affordance_slice"):
        missing = {k: v for k, v in kwargs.items() if k != omitted}
        with pytest.raises(TypeError):
            RecurrentSpatialQNetwork(**missing)

    # grid_slice omitted: constructs, and the vision encoder reads zeros.
    RecurrentSpatialQNetwork(**kwargs)


def test_training_update_does_not_clobber_rollout_hidden_state(tmp_path: Path, monkeypatch) -> None:
    """A training update must not zero the LSTM memory of a mid-episode agent."""
    lstm_calls: list[tuple[int, torch.Tensor]] = []
    original_init = RecurrentSpatialQNetwork.__init__

    def instrumented_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)

        def pre_hook(module, inputs):
            hx = inputs[1]
            h = hx[0]
            lstm_calls.append((int(inputs[0].shape[0]), (h.abs().sum(dim=(0, 2)) == 0).clone()))

        self.lstm.register_forward_pre_hook(pre_hook)

    monkeypatch.setattr(RecurrentSpatialQNetwork, "__init__", instrumented_init)

    observed: list[tuple[torch.Tensor, torch.Tensor]] = []
    original_step = VectorizedPopulation.step_population

    def instrumented_step(self, envs):
        start = len(lstm_calls)
        counts_before = self.episode_step_counts.clone()
        result = original_step(self, envs)
        for batch, zero_mask in lstm_calls[start:]:
            if batch == self.num_agents:
                observed.append((counts_before, zero_mask))
        return result

    monkeypatch.setattr(VectorizedPopulation, "step_population", instrumented_step)

    pack = _make_pack(tmp_path, "clobber", architecture=RECURRENT_ARCHITECTURE, sequence_length=8)
    with DemoRunner(
        config_dir=pack,
        db_path=tmp_path / "clobber.sqlite",
        checkpoint_dir=tmp_path / "clobber-ckpt",
        level_name=LEVEL_NAME,
    ) as runner:
        runner.run()
        population = runner.population

    assert population.last_training_step > 0, "training never ran"
    mid_episode = [(c, z) for c, z in observed if bool((c > 0).any())]
    assert mid_episode, "no mid-episode rollout forward observed"

    violations = [(int(c.max()), int(z.sum())) for c, z in mid_episode if bool((z & (c > 0)).any())]
    assert not violations, (
        f"{len(violations)}/{len(mid_episode)} mid-episode rollout forwards fed the LSTM a hidden state of exactly zero "
        "for an agent whose episode was already in progress: rollout memory is being destroyed mid-episode "
        "(training clobbers the hidden state)"
    )
