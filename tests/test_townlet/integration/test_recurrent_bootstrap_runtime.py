"""Config-in / behaviour-out pinning test for recurrent (LSTM) Q-target bootstrapping.

Pins WS-1 defect (c): the last index of every sampled subsequence was treated as
terminal, so `gamma` had no effect on the boundary target and every mid-episode
window boundary lost its bootstrap term.

The test only ever edits YAML in a copied config pack and then runs the product's
own entry point (DemoRunner). Nothing is stubbed; the loss/sample interceptors are
record-only.

Written against the token-native recurrent network API. The network takes a
REQUIRED `hidden` argument and owns no mutable hidden state,
so every recomputation below threads hidden state explicitly.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import torch
import yaml

from townlet.agent.networks import RecurrentTokenQNetwork
from townlet.demo.runner import DemoRunner
from townlet.population.vectorized import VectorizedPopulation
from townlet.training.replay_buffer import ReplayBuffer
from townlet.training.sequential_replay_buffer import SequentialReplayBuffer

PACK = Path("configs") / "test" / "model_config"
LEVEL = "L0_test"

RECURRENT_BRAIN = """
version: "1.0"
description: "Recurrent brain (LSTM) for bootstrap pinning test"
architecture:
  type: recurrent
  recurrent:
    token_embed_dim: 32
    aggregator:
      type: mean
    lstm:
      hidden_size: 64
      num_layers: 1
      dropout: 0.0
    q_head_hidden_dim: 64
optimizer:
  type: adam
  learning_rate: 0.0003
  adam_beta1: 0.9
  adam_beta2: 0.999
  adam_eps: 1.0e-8
  weight_decay: 0.0
  schedule:
    type: constant
loss:
  type: huber
  huber_delta: 1.0
q_learning:
  gamma: {gamma}
  use_double_dqn: {double}
  target_update_frequency: 100000
replay:
  capacity: 5000
  prioritized: false
"""


def _make_pack(
    tmp_path: Path,
    name: str,
    *,
    recurrent: bool,
    gamma: float,
    double: bool = True,
    seq_len: int = 8,
) -> Path:
    """Copy the shipped test pack and change ONLY YAML values."""
    dest = tmp_path / name
    shutil.copytree(PACK, dest)
    # A copied compiler cache would make every YAML edit below inert.
    shutil.rmtree(dest / ".compiled", ignore_errors=True)

    if recurrent:
        (dest / "brain.yaml").write_text(RECURRENT_BRAIN.format(gamma=gamma, double=str(double).lower()))

    level = dest / "levels" / LEVEL

    curriculum = yaml.safe_load((level / "curriculum.yaml").read_text())
    curriculum["curriculum"]["active_vision"] = "partial" if recurrent else "global"
    curriculum["curriculum"]["vision_range"] = 0.5
    (level / "curriculum.yaml").write_text(yaml.safe_dump(curriculum, sort_keys=False))

    training = yaml.safe_load((level / "training.yaml").read_text())
    block = training["training"]
    # apply_training_overrides() lets the level file win over brain.yaml: set both.
    block["q_learning"]["gamma"] = gamma
    block["q_learning"]["use_double_dqn"] = double
    block["q_learning"]["target_update_frequency"] = 100000
    block["population"]["size"] = 4
    block["replay_buffer"]["batch_size"] = 8
    block["replay_buffer"]["min_size"] = 8
    loop = block["training_loop"]
    loop["sequence_length"] = seq_len
    loop["max_steps_per_episode"] = 30
    loop["train_frequency"] = 4
    loop["max_episodes"] = 12
    loop["checkpointing"]["interval"] = 1_000_000
    (level / "training.yaml").write_text(yaml.safe_dump(training, sort_keys=False))
    return dest


def _unroll(network, observations: torch.Tensor, device) -> tuple[torch.Tensor, tuple[torch.Tensor, torch.Tensor]]:
    """Independent re-implementation of the training unroll (post-b explicit-hidden API).

    Returns (q_values_at_last_step, hidden_after_last_step).
    """
    batch_size = observations.shape[0]
    hidden = network.initial_hidden(batch_size, device)
    q_values, hidden = network(observations, hidden)
    return q_values[:, -1, :], hidden


def _closed_form_boundary_target(
    population,
    batch: dict[str, torch.Tensor],
    gamma: float,
    *,
    boundary_hidden: str = "threaded",
) -> torch.Tensor:
    """r_T + gamma * Q_target(s', a*) recomputed independently of the training code.

    `boundary_hidden` selects WHICH hidden state conditions the successor forward:
      - "threaded": the hidden state after unrolling the window - the only choice
        consistent with the interior arm, which evaluates Q(o_{t+1} | h_t).
      - "crossed": online/target hidden trajectories exchanged (negative control).
      - "zero": a fresh zero hidden state - the plausible-but-wrong implementation.
        Used only as a negative control to prove the "threaded" assertion has teeth.

    Online and target hidden states are computed by two INDEPENDENT unrolls: the
    networks have different weights, so their hidden trajectories differ and must
    not be crossed.
    """
    online = population.q_network
    target_net = population.target_network
    expected = []
    for row, length in enumerate(batch["lengths"].tolist()):
        observations = batch["observations"][row : row + 1, :length]
        successor = batch["next_observations"][row : row + 1, length - 1 : length]
        with torch.no_grad():
            _, target_hidden = _unroll(target_net, observations, population.device)
            _, online_hidden = _unroll(online, observations, population.device)
            if boundary_hidden == "zero":
                target_hidden = target_net.initial_hidden(1, population.device)
                online_hidden = online.initial_hidden(1, population.device)
            elif boundary_hidden == "crossed":
                target_hidden, online_hidden = online_hidden, target_hidden
            target_values, _ = target_net(successor, target_hidden)
            legal = batch["next_action_masks"][row, length - 1]
            reward = batch["rewards"][row, length - 1]
            if bool(batch["dones"][row, length - 1]) or gamma == 0.0:
                expected.append(reward)
                continue
            assert bool(legal.any()), "nonterminal successor has no captured legal action"
            if population.use_double_dqn:
                online_values, _ = online(successor, online_hidden)
                action = online_values[0, 0].masked_fill(~legal, -torch.inf).argmax()
                value = target_values[0, 0, action]
            else:
                value = target_values[0, 0].masked_fill(~legal, -torch.inf).max()
            expected.append(reward + gamma * value)
    return torch.stack(expected)


def _boundary(batch, values):
    rows = torch.arange(len(batch["lengths"]), device=values.device)
    return values[rows, batch["lengths"] - 1]


def _run(pack: Path, out: Path, monkeypatch: pytest.MonkeyPatch, *, episodes: int = 12, gammas: tuple[float, ...] = ()):
    """Run the real training entry point.

    Returns (population, updates) where each update is
    (batch, q_target, expectations). `expectations` maps gamma -> closed-form
    boundary target, plus the key "zero" for the zero-hidden negative control.
    The closed forms are evaluated *at the moment of the update*: computing them
    afterwards would use post-training weights and prove nothing.
    """
    import townlet.population.vectorized as vec_mod

    captured: dict[str, object] = {}
    batches: list[dict[str, torch.Tensor]] = []
    targets: list[torch.Tensor] = []
    expectations: list[dict[object, torch.Tensor]] = []

    original_init = VectorizedPopulation._initialize

    def init_spy(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        captured["population"] = self
        captured["optimizer_steps"] = 0
        captured["initial_parameters"] = [parameter.detach().clone() for parameter in self.q_network.parameters()]
        original_step = self.optimizer.step

        def optimizer_step(*step_args, **step_kwargs):
            result = original_step(*step_args, **step_kwargs)
            captured["optimizer_steps"] += 1
            return result

        monkeypatch.setattr(self.optimizer, "step", optimizer_step)

    monkeypatch.setattr(VectorizedPopulation, "_initialize", init_spy)

    original_sample = SequentialReplayBuffer.sample_batch

    def sample_spy(self, request):
        batch = original_sample(self, request)
        batches.append(
            {
                key: getattr(batch, key).detach().clone()
                for key in ("observations", "actions", "rewards", "dones", "next_observations", "next_action_masks", "lengths", "loss_mask")
            }
        )
        return batch

    monkeypatch.setattr(SequentialReplayBuffer, "sample_batch", sample_spy)

    class LossSpy:
        """Record-only proxy: forwards every call to torch.nn.functional untouched."""

        def __init__(self, real):
            self._real = real

        def __getattr__(self, name):
            func = getattr(self._real, name)
            if name not in ("huber_loss", "smooth_l1_loss", "mse_loss"):
                return func

            def wrapped(pred, target, *args, **kwargs):
                if batches and len(targets) < len(batches):
                    full_target = torch.zeros_like(batches[-1]["rewards"])
                    full_target[batches[-1]["loss_mask"]] = target.detach()
                    targets.append(full_target)
                    population = captured["population"]
                    batch = batches[-1]
                    if gammas and "next_observations" in batch:
                        exp: dict[object, torch.Tensor] = {
                            gamma: _closed_form_boundary_target(population, batch, gamma) for gamma in gammas
                        }
                        exp["zero"] = _closed_form_boundary_target(population, batch, gammas[0], boundary_hidden="zero")
                        exp["crossed"] = _closed_form_boundary_target(population, batch, gammas[0], boundary_hidden="crossed")
                        expectations.append(exp)
                    else:
                        expectations.append({})
                return func(pred, target, *args, **kwargs)

            return wrapped

    monkeypatch.setattr(vec_mod, "F", LossSpy(vec_mod.F))

    runner = DemoRunner(
        config_dir=pack,
        db_path=out / "demo.db",
        checkpoint_dir=out / "checkpoints",
        max_episodes=episodes,
        level_name=LEVEL,
    )
    runner.run()

    population = captured["population"]
    if batches:
        assert captured["optimizer_steps"] == len(batches) == population.training_step_counter
        assert any(
            not torch.equal(before, after)
            for before, after in zip(captured["initial_parameters"], population.q_network.parameters(), strict=True)
        ), "real optimizer updates did not change online parameters"
    return population, list(zip(batches, targets, expectations, strict=True))


def test_recurrent_architecture_is_selected_by_brain_yaml(tmp_path, monkeypatch):
    """architecture.type in brain.yaml must change the runtime, not just the config."""
    recurrent_pack = _make_pack(tmp_path, "recurrent", recurrent=True, gamma=0.99)
    feedforward_pack = _make_pack(tmp_path, "feedforward", recurrent=False, gamma=0.99)

    recurrent_pop, _ = _run(recurrent_pack, tmp_path / "out-recurrent", monkeypatch, episodes=4)
    assert recurrent_pop.is_recurrent is True
    assert isinstance(recurrent_pop.q_network, RecurrentTokenQNetwork)
    assert isinstance(recurrent_pop.replay_buffer, SequentialReplayBuffer)

    feedforward_pop, _ = _run(feedforward_pack, tmp_path / "out-feedforward", monkeypatch, episodes=4)
    assert feedforward_pop.is_recurrent is False
    assert not isinstance(feedforward_pop.q_network, RecurrentTokenQNetwork)
    assert isinstance(feedforward_pop.replay_buffer, ReplayBuffer)


@pytest.mark.parametrize(
    "gamma, other_gamma, double",
    [(0.99, 0.5, True), (0.5, 0.99, True), (0.99, 0.5, False)],
)
def test_subsequence_boundary_bootstraps_with_gamma_from_yaml(tmp_path, monkeypatch, gamma, other_gamma, double):
    """Mid-episode window boundaries must bootstrap with the gamma written in YAML.

    Four things are pinned at once:
      1. the boundary transition of a sampled subsequence is NOT treated as terminal;
      2. the successor used is next_observations[:, -1] and the discount is the
         configured one - the same run checked against the other gamma must not match;
      3. the successor is evaluated under the hidden state accumulated over the window,
         not a fresh zero hidden state (the "zero" negative control must NOT match);
      4. both use_double_dqn branches are covered.
    """
    name = f"bootstrap-{gamma}-{double}"
    pack = _make_pack(tmp_path, name, recurrent=True, gamma=gamma, double=double)
    population, updates = _run(pack, tmp_path / "out", monkeypatch, gammas=(gamma, other_gamma))

    assert updates, "no recurrent training update happened - test would pass vacuously"
    assert population.gamma == pytest.approx(gamma), "gamma did not reach the runtime"
    assert population.use_double_dqn is double, "use_double_dqn did not reach the runtime"

    non_terminal = 0
    collapsed = 0
    for batch, q_target, _ in updates:
        # Only each row's final real objective coordinate is a window boundary.
        alive = (~_boundary(batch, batch["dones"])) & _boundary(batch, batch["loss_mask"])
        non_terminal += int(alive.sum())
        collapsed += int((torch.eq(_boundary(batch, q_target), _boundary(batch, batch["rewards"])) & alive).sum())

    assert non_terminal > 0, "every sampled window ended on a real terminal - inconclusive"
    assert collapsed == 0, (
        f"{collapsed}/{non_terminal} mid-episode window boundaries lost their bootstrap term "
        "(q_target == reward at the last index of the sampled subsequence)"
    )

    max_deviation = 0.0
    min_other_gap = float("inf")
    min_zero_gap = float("inf")
    max_cross_gap = 0.0
    for batch, q_target, expectations in updates:
        assert "next_observations" in batch, "sampled sequences must carry the successor observation"
        alive = (~_boundary(batch, batch["dones"])) & _boundary(batch, batch["loss_mask"])
        boundary = _boundary(batch, q_target)
        expected = expectations[gamma]
        wrong_gamma = expectations[other_gamma]
        wrong_hidden = expectations["zero"]
        wrong_cross = expectations["crossed"]
        max_deviation = max(max_deviation, float((boundary - expected).abs().max()))
        if bool(alive.any()):
            min_other_gap = min(min_other_gap, float((expected[alive] - wrong_gamma[alive]).abs().max()))
            max_cross_gap = max(max_cross_gap, float((expected[alive] - wrong_cross[alive]).abs().max()))
            min_zero_gap = min(min_zero_gap, float((expected[alive] - wrong_hidden[alive]).abs().max()))

    # Pins WHICH successor and WHICH hidden state the bootstrap uses, not merely that
    # some non-zero value was added.
    assert max_deviation < 1e-5, f"boundary target deviates from r + gamma * Q(s', a*) by {max_deviation}"
    assert min_other_gap > 1e-6, "closed forms for the two gammas are indistinguishable - assertion is vacuous"
    assert min_zero_gap > 1e-6, (
        "threaded-hidden and zero-hidden closed forms are indistinguishable - the " "hidden-state half of the assertion is vacuous"
    )
    assert max_cross_gap > 1e-6, "own-hidden and crossed-hidden targets are indistinguishable"
    print(f"[measured] max_deviation={max_deviation:.3e} min_other_gap={min_other_gap:.3e} min_zero_gap={min_zero_gap:.3e}")
