"""ENV component proofs; cooperative population custody is not actual POP learning.

Breaks targeted: publishing before ready, accepting lookalike capabilities, reopening
retired lanes, performing physics/provider work during retirement, and leaking a
partly published decision. Real Q/Adam/replay/curriculum owners are constructed;
declared component closure uses real sinks, without claiming POP learning/replay.
"""

from __future__ import annotations

import copy
import random
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch

from townlet.agent.network_factory import NetworkFactory
from townlet.agent.optimizer_factory import OptimizerFactory
from townlet.config.bac_options import resolve_bac_options
from townlet.config.brain_config import apply_training_overrides
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.exploration_policy import build_exploration, resolve_exploration_policy
from townlet.config.training_v2_config import TrainingV2Config
from townlet.config.world_roster import WorldRosterDeclaration
from townlet.curriculum.factory import build_curriculum
from townlet.environment.vectorized_env import WorldReceiptIssuer
from townlet.exploration.world_curiosity_state import WorldCuriosityDescriptor
from townlet.training.clock_ledger import ClockLedger, PreparedVectorStep
from townlet.training.episode import EpisodeCompletion, LaneOutcome, freeze_lane_outcome
from townlet.training.replay_buffer import ReplayBuffer
from townlet.universe.compiler import UniverseCompiler

IDS = ("component-A", "component-B")
SEED = 42


def equal(left: Any, right: Any) -> None:
    """Exact owned witness comparison; never recompute an expected production value."""
    if isinstance(left, torch.Tensor):
        assert isinstance(right, torch.Tensor)
        assert (left.dtype, left.device, left.shape) == (right.dtype, right.device, right.shape)
        assert torch.equal(left, right)
    elif isinstance(left, np.ndarray):
        np.testing.assert_array_equal(left, right)
    elif isinstance(left, Mapping):
        assert left.keys() == right.keys()
        for key in left:
            equal(left[key], right[key])
    elif isinstance(left, (tuple, list)):
        assert type(left) is type(right) and len(left) == len(right)
        for first, second in zip(left, right, strict=True):
            equal(first, second)
    else:
        assert type(left) is type(right) and left == right


def owned(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        return value.detach().clone()
    if isinstance(value, Mapping):
        return {key: owned(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(owned(item) for item in value)
    if isinstance(value, list):
        return [owned(item) for item in value]
    return copy.deepcopy(value)


@pytest.fixture(scope="module")
def compiled() -> Any:
    return UniverseCompiler().compile(Path("configs/test/token_set_smoke"), primary_level="L0_test", use_cache=False)


class ComponentPopulation:
    """Actual registered component owner with retained issued decision/step custody.

    Unsupported commit/native requests fail closed. Canonical component boundary
    commitments own a component ClockLedger, not production POP history.
    """

    def __init__(self, compiled: Any):
        self.device = torch.device("cpu")
        selected = compiled.get_level(compiled.metadata.primary_level)
        authored = selected.training.model_dump()
        authored["population"]["size"] = len(IDS)
        authored["seed"] = SEED
        training = TrainingV2Config.model_validate(authored)
        options = resolve_bac_options(training.bac_options, training=training).options
        self.env = compiled.create_environment(
            num_agents=len(IDS),
            level_name=compiled.metadata.primary_level,
            device=self.device,
            world_roster=WorldRosterDeclaration(IDS),
            training_seed=SEED,
            lane_world_ids=IDS,
        )
        brain = apply_training_overrides(compiled.brain, training)
        assert brain.architecture.token_set is not None
        self.q = NetworkFactory.build_token_set(
            config=brain.architecture.token_set, action_dim=self.env.action_dim, token_spec=self.env.token_spec
        ).to(self.device)
        self.optimizer, self.scheduler = OptimizerFactory.build(config=brain.optimizer, parameters=self.q.parameters())
        self.replay = ReplayBuffer(capacity=brain.replay.capacity, device=self.device)
        effective = compiled.effective_run
        self.curriculum = build_curriculum(
            training, curriculum_options=effective.options.curriculum, static_policy=effective.static_policy, device=self.device
        )
        self.curriculum.initialize_population(len(IDS))
        self.curriculum_issuer = WorldReceiptIssuer(owner=self.curriculum)
        policy = resolve_exploration_policy(
            drive_intrinsic=IntrinsicStrategyConfig(strategy="none", base_weight=0.0, apply_modifiers=[]),
            training=training,
            options=options,
        )
        self.policy = policy
        descriptor = WorldCuriosityDescriptor.from_policy(
            policy,
            world_ids=IDS,
            observation_dim=self.env.observation_dim,
            action_dim=self.env.action_dim,
            training_seed=SEED,
        )
        self.reports: list[Any] = []
        self.bank: Any = None
        self.bank_issuer: Any = None
        self.runtime = build_exploration(
            policy=policy,
            descriptor=descriptor,
            device=self.device,
            validate_accepted_episode=self.env.validate_accepted_episode,
            issuer_factory=self.capture_bank,
            report_allocation=self.reports.append,
            validate_committed_batch=self.validate_committed_batch,
            validate_parent_cadence=self.validate_parent_cadence,
        )
        assert self.bank is not None and self.bank is not self.runtime
        self.issuer = WorldReceiptIssuer(owner=self)
        self.completion_request: Any = None
        self.committed_batches: dict[int, Any] = {}
        self.current_epsilons = self.runtime.epsilon_tensor(batch_size=len(IDS), device=self.device)
        self.ledger = ClockLedger()
        self.revision = 0
        self.intent: Any = None
        self.ready: Any = None
        self.participation: Any = None
        self.activation: Any = None
        self.retired: tuple[str, ...] | None = None
        self.current_obs: Any = None
        self.completed = torch.zeros(len(IDS), dtype=torch.bool)
        self.step_registry: dict[int, dict[str, Any]] = {}
        self.step_started = False
        self.env.set_exploration_runtime(exploration=self.runtime, claim_vector_step=self.claim_vector_step)
        self.roles = {
            "population": self,
            "curiosity": self.bank,
            "curriculum": self.curriculum,
            "exploration": self,  # Real component coordinator owns its child commit journal.
            "network": self.q,
            "optimizer": self.optimizer,
            "scheduler": self if self.scheduler is None else self.scheduler,
            "replay": self.replay,
            "selection": self,  # Owns actual diagnostic epsilon telemetry supplied below.
        }
        self.authority = self.env.bind_boundary_authority(owner=self, role_owners=self.roles)
        release = self.authority.bootstrap(first_batch_episode=0)
        self.env.install_boundary_release(release)
        self.reservation = self.env.prepare_episode(batch_episode=0, release=release)
        self.env.validate_episode_reservation(self.reservation)
        self.reset = self.env.reset(reservation=self.reservation)
        self.accepted = self.reset.accepted
        self.current_obs = self.reset.observation

    def capture_bank(self, bank: Any) -> Any:
        if self.bank is not None:
            raise ValueError("component permits exactly one actual BANK construction")
        self.bank = bank
        self.bank_issuer = WorldReceiptIssuer(owner=bank)
        return self.bank_issuer

    def validate_committed_batch(self, *, batch_episode: Any, outcomes: Any) -> None:
        request = self.completion_request
        content = tuple((item.payload.hex(), item.fingerprint) for item in map(freeze_lane_outcome, outcomes))
        if request is None or request != (self.accepted, batch_episode, content):
            raise ValueError("ENV component does not own this canonical completion request")

    def validate_parent_cadence(self, *, cadence: Any, mode: Any, accepted: Any, parent_restore: Any) -> None:
        raise ValueError("ENV component does not install parent-native cadence")

    def request(self, retired: tuple[str, ...]) -> Any:
        if self.activation is not None or self.step_started:
            raise ValueError("component decision window is closed")
        if self.intent is not None:
            if retired != self.retired:
                raise ValueError("component decision request changed")
            return self.intent
        self.retired = retired
        self.intent = self.issuer.issue(
            kind="initial_participation_intent",
            payload={
                "accepted": self.accepted,
                "world_ids": IDS,
                "retired_world_ids": retired,
                "population_revision": self.revision,
            },
        )
        return self.intent

    def stage_ready(self, prepared: Any) -> Any:
        if self.ready is not None:
            if self.ready.prepared is not prepared:
                raise ValueError("component already staged a different preparation")
            return self.ready
        if prepared.accepted is not self.accepted or prepared.intent is not self.intent:
            raise ValueError("component requires its actual retained decision")
        observation, masks, retired = prepared.observation, prepared.action_masks, prepared.retired_world_ids
        assert retired == self.retired
        equal(observation, self.current_obs)
        assert observation.shape == (len(IDS), self.env.observation_dim) and observation.dtype == torch.float32
        assert masks.shape == (len(IDS), self.env.action_dim) and masks.dtype == torch.bool
        assert observation.device == masks.device == self.device
        candidate_completed = torch.tensor([world in retired for world in IDS], dtype=torch.bool)
        assert not bool(masks[candidate_completed].any())
        assert bool(masks[~candidate_completed].any(dim=1).all())
        self.candidate = (observation, masks, candidate_completed, self.revision + 1)
        self.ready = self.issuer.issue(
            kind="initial_participation_ready",
            payload={"accepted": self.accepted, "intent": self.intent, "prepared": prepared, "population_revision": self.revision},
        )
        return self.ready

    def publish(self, prepared: Any) -> Any:
        self.stage_ready(prepared)
        observation, masks, completed, next_revision = self.candidate
        result = self.env.commit_initial_participation(prepared=prepared, population_ready=self.ready)
        # Assignment-only paired suffix: no property read, validation or issuance.
        self.current_obs = observation
        self.current_masks = masks
        self.completed = completed
        self.revision = next_revision
        self.participation = result
        self.intent = None
        self.ready = None
        return result

    def activate(self) -> Any:
        try:
            self.activation = self.issuer.issue(kind="activation", payload={"accepted": self.accepted})
            curiosity = self.runtime.begin_episode(accepted=self.accepted)
            return self.env.activate_episode(accepted=self.accepted, population_receipt=self.activation, curiosity_receipt=curiosity)
        except BaseException:
            self.activation = None
            self.env.abandon_episode(accepted=self.accepted, reason="runtime_failure")
            raise

    def prepare_step(self, actions: torch.Tensor) -> Any:
        if self.participation is not None:
            self.env.validate_initial_participation(accepted=self.accepted, participation=self.participation, predecessor=self.current_obs)
        candidate = {
            "accepted": self.accepted,
            "world_ids": IDS,
            "predecessor": self.current_obs.clone(),
            "actions": actions.clone(),
            "active_on_entry": ~self.completed.clone(),
        }
        equal(candidate["active_on_entry"], ~self.env.dones)
        handle = PreparedVectorStep()
        self.step_registry[id(handle)] = {"handle": handle, "candidate": candidate, "tick": self.ledger.vector_ticks + 1, "claimed": False}
        return handle

    def claim_vector_step(self, *, prepared: Any, **candidate: Any) -> int:
        record = self.step_registry.get(id(prepared))
        if record is None or record["handle"] is not prepared or record["claimed"]:
            raise ValueError("component step was not issued or has already executed")
        original = record["candidate"]
        if candidate["accepted"] is not self.accepted or candidate["accepted"] is not original["accepted"]:
            raise ValueError("component step token changed")
        if candidate["world_ids"] != IDS:
            raise ValueError("component step binding changed")
        for name in ("predecessor", "actions", "active_on_entry"):
            value, expected = candidate[name], original[name]
            if (value.dtype, value.device, value.shape) != (expected.dtype, expected.device, expected.shape) or not torch.equal(
                value, expected
            ):
                raise ValueError("component step content changed")
        if self.participation is not None:
            self.env.validate_initial_participation(accepted=self.accepted, participation=self.participation, predecessor=self.current_obs)
        record["claimed"] = True
        self.step_started = True
        return record["tick"]

    def step(self) -> Any:
        actions = torch.full((len(IDS),), self.env.action_ids["WAIT"], dtype=torch.long)
        prepared = self.prepare_step(actions)
        observations, rewards, dones, info = self.env.step(actions, vector_step=prepared)
        handoff = info["intrinsic_transition"]
        receipts = self.runtime.admit_and_service(context=handoff.context, stamp=handoff.stamp, accepted=handoff.accepted)
        self.ledger = self.ledger.advance(vector_ticks=1, eligible_transitions=int(info["active_on_entry"].sum()))
        self.current_obs = observations.detach().clone()
        self.completed = dones.detach().clone()
        info["component_selection_epsilons"] = self.current_epsilons
        return observations, rewards, dones, info, receipts

    def prepare_empty_episode_evidence(self, *, accepted: Any) -> Any:
        if accepted is not self.accepted or self.activation is None or self.step_started:
            raise ValueError("component empty proof needs actual activated zero-event custody")
        if not bool(self.completed.all()) or bool(self.env.step_counts.any()) or self.ledger.vector_ticks:
            raise ValueError("component has genuine participating work")
        return self.issuer.issue(kind="empty_episode", payload={"accepted": accepted, "participated_world_ids": (), "events": ()})


def witness(rig: ComponentPopulation) -> dict[str, Any]:
    """Available physical/RNG witnesses; safe even after quarantine (no exporter)."""
    env = rig.env
    return {
        "physical": owned(
            {name: getattr(env, name) for name in ("positions", "_velocity", "meters", "dones", "step_counts", "intrinsic_weights")}
        ),
        "tick_hour": (env.global_tick, env.time_of_day),
        "vfs": owned(env._current_vfs_state()),
        "history": owned((env._last_affordances, env._affordance_streaks, env._affordances_seen, env._unique_affordances_count)),
        "interactions": owned((env.interaction_progress, env.last_interaction_affordance, env.last_interaction_position)),
        "reward_cache": owned(env._last_reward_components),
        "q": owned(rig.q.state_dict()),
        "optimizer": owned(rig.optimizer.state_dict()),
        "ledger": rig.ledger,
        "rng": (torch.get_rng_state().clone(), random.getstate(), owned(np.random.get_state())),
    }


def assert_unchanged(rig: ComponentPopulation, before: dict[str, Any]) -> None:
    equal(witness(rig), before)


def component_state(rig: ComponentPopulation) -> dict[str, Any]:
    """Qualified exports outside decision/restore custody; baseline owns aliases."""
    return owned(
        {
            "replay": rig.replay.serialize(),
            "retained": rig.replay.retained_transitions,
            "curriculum": rig.curriculum.checkpoint_state(),
            "scheduler": None if rig.scheduler is None else rig.scheduler.state_dict(),
        }
    )


def prepare(rig: ComponentPopulation, retired: tuple[str, ...] = (IDS[1],)) -> Any:
    intent = rig.request(retired)
    return rig.env.prepare_initial_participation(accepted=rig.accepted, intent=intent)


def activated(compiled: Any, retired: tuple[str, ...] = (IDS[1],)) -> ComponentPopulation:
    rig = ComponentPopulation(compiled)
    rig.publish(prepare(rig, retired))
    rig.activate()
    return rig


def test_genuine_reset_prepares_retirement_without_publication(compiled: Any) -> None:
    """Causal RED: current ENV lacks prepare after all genuine prerequisites succeed."""
    rig = ComponentPopulation(compiled)
    assert rig.env.world_phase == "active-awaiting-activation"
    assert rig.env.world_ids == IDS and rig.accepted is rig.reset.accepted
    assert not bool(rig.env.dones.any()) and not bool(rig.env.step_counts.any())
    assert rig.activation is None and rig.ledger == ClockLedger()
    before = witness(rig)
    intent = rig.request((IDS[1],))
    prepared = rig.env.prepare_initial_participation(accepted=rig.accepted, intent=intent)
    assert prepared.kind == "prepared_initial_participation"
    assert prepared.accepted is rig.accepted and prepared.intent is intent
    assert prepared.retired_world_ids == (IDS[1],)
    assert prepared.observation.shape == (len(IDS), rig.env.observation_dim)
    assert prepared.action_masks.shape == (len(IDS), rig.env.action_dim)
    assert prepared.observation.dtype == torch.float32 and prepared.action_masks.dtype == torch.bool
    equal(prepared.observation, rig.reset.observation)
    assert bool(prepared.action_masks[0].any()) and not bool(prepared.action_masks[1].any())
    assert rig.env.prepare_initial_participation(accepted=rig.accepted, intent=intent) is prepared
    assert rig.activation is None
    assert_unchanged(rig, before)


@pytest.mark.parametrize("retired,expected", [((), [False, False]), ((IDS[1],), [False, True]), (IDS, [True, True])])
def test_commit_publishes_owned_geometry_without_physics(compiled: Any, retired: tuple[str, ...], expected: list[bool]) -> None:
    """Missing/overbroad publication or leaked public readings corrupts this boundary."""
    rig = ComponentPopulation(compiled)
    runtime_before = rig.runtime.checkpoint_state()
    components_before = component_state(rig)
    assert components_before["retained"] == 0
    legal = rig.env.get_action_masks().clone()
    before = witness(rig)
    prepared = prepare(rig, retired)
    prepared.observation.add_(100)
    prepared.action_masks.logical_not_()
    result = rig.publish(prepared)
    assert result.kind == "initial_participation" and result.accepted is rig.accepted
    assert result.retired_world_ids == retired
    equal(result.observation, rig.reset.observation)
    equal(rig.env.dones, torch.tensor(expected))
    expected_mask = legal.clone()
    expected_mask[torch.tensor(expected)] = False
    equal(result.action_masks, expected_mask)
    equal(rig.current_masks, expected_mask)
    result.action_masks.fill_(True)
    result.observation.fill_(99)
    equal(result.action_masks, expected_mask)
    equal(result.observation, rig.reset.observation)
    after = witness(rig)
    before["physical"]["dones"] = torch.tensor(expected)
    equal(after, before)
    equal(rig.runtime.checkpoint_state(), runtime_before)
    equal(component_state(rig), components_before)
    assert rig.env.world_phase == "active-awaiting-activation" and rig.activation is None


def test_first_real_transition_uses_sealed_activity_and_one_service(compiled: Any, monkeypatch: Any) -> None:
    """A late retirement or synthetic second reward/service changes real handoff counts."""
    rig = activated(compiled)
    calls: dict[str, list[Any]] = {"reward": [], "service": []}
    reward, service = rig.runtime.reward, rig.runtime.admit_and_service

    def observed_reward(**kwargs: Any) -> Any:
        result = reward(**kwargs)
        calls["reward"].append((kwargs, result))
        return result

    def observed_service(**kwargs: Any) -> Any:
        result = service(**kwargs)
        calls["service"].append((kwargs, result))
        return result

    monkeypatch.setattr(rig.runtime, "reward", observed_reward)
    monkeypatch.setattr(rig.runtime, "admit_and_service", observed_service)
    predecessor = rig.current_obs.clone()
    _, rewards, dones, info, receipts = rig.step()
    handoff = info["intrinsic_transition"]
    assert len(calls["reward"]) == len(calls["service"]) == 1
    equal(handoff.context.predecessor, predecessor)
    equal(handoff.context.active_on_entry, torch.tensor([True, False]))
    equal(info["step_counts"], torch.tensor([1, 0]))
    assert rig.env.global_tick == 1 and rig.ledger.vector_ticks == rig.ledger.eligible_transitions == 1
    assert bool(dones[1]) and float(rewards[1]) == 0.0
    assert not bool(info["successor_action_masks"][1].any())
    for kwargs in (calls["reward"][0][0], calls["service"][0][0]):
        assert kwargs["context"] is handoff.context and kwargs["stamp"] is handoff.stamp and kwargs["accepted"] is rig.accepted
    assert receipts is calls["service"][0][1]
    rig.env.validate_initial_participation(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)


def test_no_retirement_preserves_ordinary_active_transition(compiled: Any) -> None:
    rig = activated(compiled, ())
    _, _, _, info, _ = rig.step()
    equal(info["active_on_entry"], torch.tensor([True, True]))
    equal(info["step_counts"], torch.tensor([1, 1]))
    assert rig.ledger.vector_ticks == 1 and rig.ledger.eligible_transitions == 2


@pytest.mark.parametrize("with_participation", [True, False])
def test_real_claim_validates_current_owned_reading_once_before_publication(
    compiled: Any, monkeypatch: Any, with_participation: bool
) -> None:
    claim = ComponentPopulation.claim_vector_step
    claim_calls, validations = [], []
    in_claim = False

    def observed_claim(owner: ComponentPopulation, *, prepared: Any, **candidate: Any) -> int:
        nonlocal in_claim
        assert not in_claim
        claim_calls.append(prepared)
        in_claim = True
        try:
            return claim(owner, prepared=prepared, **candidate)
        finally:
            in_claim = False

    monkeypatch.setattr(ComponentPopulation, "claim_vector_step", observed_claim)
    rig = ComponentPopulation(compiled)
    if with_participation:
        rig.publish(prepare(rig))
    rig.activate()
    predecessor = rig.current_obs
    validate = rig.env.validate_initial_participation

    def observed_validation(**kwargs: Any) -> Any:
        assert kwargs["accepted"] is rig.accepted and kwargs["participation"] is rig.participation
        assert kwargs["predecessor"] is predecessor
        assert not rig.step_started and not any(record["claimed"] for record in rig.step_registry.values())
        validations.append(in_claim)
        return validate(**kwargs)

    monkeypatch.setattr(rig.env, "validate_initial_participation", observed_validation)
    _, _, _, info, _ = rig.step()
    assert len(claim_calls) == 1 and rig.step_registry[id(claim_calls[0])]["claimed"] and rig.step_started
    assert validations == ([False, True] if with_participation else [])
    assert not in_claim and rig.env.world_phase == "active"
    expected = torch.tensor([True, not with_participation])
    equal(info["active_on_entry"], expected)
    equal(info["step_counts"], expected.long())
    assert rig.ledger.vector_ticks == 1 and rig.ledger.eligible_transitions == int(expected.sum())


def test_validator_accepts_later_genuine_active_lane_terminal(compiled: Any) -> None:
    """Comparing all future dones to the initial seal would reject lawful A retirement."""
    rig = ComponentPopulation(compiled)
    rig.env.agent_lifespan = 1  # Explicit genuine ENV lifespan, not pre-step inactivity.
    rig.publish(prepare(rig))
    rig.activate()
    _, _, dones, info, _ = rig.step()
    equal(dones, torch.tensor([True, True]))
    equal(info["newly_retired"], torch.tensor([True, False]))
    equal(info["step_counts"], torch.tensor([1, 0]))
    rig.env.validate_initial_participation(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)


def test_separate_all_inactive_ordinary_step_contract_is_preserved(compiled: Any) -> None:
    """This ordinary API control is separate from zero-tick empty abandonment."""
    rig = activated(compiled, IDS)
    _, rewards, _, info, _ = rig.step()
    equal(info["active_on_entry"], torch.tensor([False, False]))
    equal(info["step_counts"], torch.tensor([0, 0]))
    equal(rewards, torch.zeros(len(IDS)))
    assert rig.env.global_tick == 1 and rig.ledger.vector_ticks == 1 and rig.ledger.eligible_transitions == 0


def test_direct_ordinary_activation_remains_available_without_decision(compiled: Any) -> None:
    """An additive participation API must not make direct all-active activation fail."""
    rig = ComponentPopulation(compiled)
    rig.activate()
    equal(rig.env.dones, torch.tensor([False, False]))
    assert rig.env.world_phase == "active"
    intent = rig.issuer.issue(
        kind="initial_participation_intent",
        payload={"accepted": rig.accepted, "world_ids": IDS, "retired_world_ids": (), "population_revision": 0},
    )
    before = witness(rig)
    with pytest.raises(ValueError):
        rig.env.prepare_initial_participation(accepted=rig.accepted, intent=intent)
    assert_unchanged(rig, before)


def test_whole_retirement_uses_real_empty_abandonment(compiled: Any) -> None:
    rig = activated(compiled, IDS)
    before = witness(rig)
    epsilon_before = rig.runtime.epsilon
    assert not bool(rig.env.get_action_masks().any())
    abandonment = rig.env.abandon_episode(accepted=rig.accepted, reason="empty_participation")
    assert abandonment.reason == "empty_participation" and rig.env.world_phase == "quarantined"
    assert rig.env.global_tick == 0 and rig.ledger == ClockLedger() and not rig.step_registry
    assert_unchanged(rig, before)
    assert rig.runtime.epsilon == epsilon_before  # Do not export native state after quarantine.
    with pytest.raises(ValueError):
        rig.env.step(torch.zeros(len(IDS), dtype=torch.long), vector_step=PreparedVectorStep())
    with pytest.raises(ValueError):
        rig.env.vfs_random_state()


def test_missing_real_empty_proof_refuses_without_release(compiled: Any, monkeypatch: Any) -> None:
    rig = activated(compiled, IDS)

    def refuse(*, accepted: Any) -> Any:
        raise ValueError("component owner cannot attest this empty request")

    monkeypatch.setattr(rig, "prepare_empty_episode_evidence", refuse)
    before = witness(rig)
    with pytest.raises(ValueError):
        rig.env.abandon_episode(accepted=rig.accepted, reason="empty_participation")
    assert rig.env.world_phase == "active"
    assert_unchanged(rig, before)


@pytest.mark.parametrize("retired", [[IDS[1]], (IDS[1], IDS[1]), (IDS[1], IDS[0]), ("unknown",), ("",), (True,)])
def test_invalid_retirement_ids_refuse_before_publication(compiled: Any, retired: Any) -> None:
    rig = ComponentPopulation(compiled)
    intent = rig.request(retired)
    before = witness(rig)
    with pytest.raises(ValueError):
        rig.env.prepare_initial_participation(accepted=rig.accepted, intent=intent)
    assert rig.env.world_phase == "active-awaiting-activation"
    assert_unchanged(rig, before)


@pytest.mark.parametrize(
    "damage", ["copy_token", "copy_intent", "foreign_issuer", "wrong_kind", "extra_key", "bool_revision", "wrong_order"]
)
def test_intent_identity_and_exact_content_are_required(compiled: Any, damage: str) -> None:
    rig = ComponentPopulation(compiled)
    intent = rig.request((IDS[1],))
    accepted = rig.accepted
    fields = intent.payload
    if damage == "copy_token":
        accepted = replace(accepted)
    elif damage == "copy_intent":
        intent = replace(intent)
    elif damage == "foreign_issuer":
        intent = WorldReceiptIssuer(owner=rig.q).issue(kind=intent.kind, payload=fields)
    elif damage == "wrong_kind":
        intent = rig.issuer.issue(kind="activation", payload=fields)
    else:
        if damage == "extra_key":
            fields["extra"] = True
        elif damage == "bool_revision":
            fields["population_revision"] = True
        else:
            fields["world_ids"] = tuple(reversed(IDS))
        intent = rig.issuer.issue(kind="initial_participation_intent", payload=fields)
    before = witness(rig)
    with pytest.raises(ValueError):
        rig.env.prepare_initial_participation(accepted=accepted, intent=intent)
    assert_unchanged(rig, before)


@pytest.mark.parametrize("damage", ["copy_prepared", "copy_ready", "wrong_prepared", "revision", "foreign_owner"])
def test_pure_commit_refusal_retains_exact_preparation(compiled: Any, damage: str) -> None:
    rig = ComponentPopulation(compiled)
    prepared = prepare(rig)
    ready = rig.stage_ready(prepared)
    request = prepared
    if damage == "copy_prepared":
        request = replace(prepared)
    elif damage == "copy_ready":
        ready = replace(ready)
    else:
        fields = ready.payload
        if damage == "wrong_prepared":
            fields["prepared"] = replace(prepared)
        elif damage == "revision":
            fields["population_revision"] += 1
        issuer = WorldReceiptIssuer(owner=rig.q) if damage == "foreign_owner" else rig.issuer
        ready = issuer.issue(kind="initial_participation_ready", payload=fields)
    before = witness(rig)
    with pytest.raises(ValueError):
        rig.env.commit_initial_participation(prepared=request, population_ready=ready)
    assert_unchanged(rig, before)
    assert rig.env.prepare_initial_participation(accepted=rig.accepted, intent=rig.intent) is prepared
    rig.publish(prepared)
    equal(rig.env.dones, torch.tensor([False, True]))


def test_changed_intent_and_second_commit_cannot_replace_decision(compiled: Any) -> None:
    rig = ComponentPopulation(compiled)
    prepared = prepare(rig)
    ready = rig.stage_ready(prepared)
    another = rig.issuer.issue(kind=rig.intent.kind, payload=rig.intent.payload)
    with pytest.raises(ValueError):
        rig.env.prepare_initial_participation(accepted=rig.accepted, intent=another)
    rig.publish(prepared)
    before = witness(rig)
    with pytest.raises(ValueError):
        rig.env.commit_initial_participation(prepared=prepared, population_ready=ready)
    assert_unchanged(rig, before)


@pytest.mark.parametrize("field", ["dones", "step_counts", "positions", "meters", "_velocity"])
def test_prepublication_physical_tamper_quarantines(compiled: Any, field: str) -> None:
    rig = ComponentPopulation(compiled)
    prepared = prepare(rig)
    ready = rig.stage_ready(prepared)
    tensor = getattr(rig.env, field)
    if field == "dones":
        tensor[0] = True
    else:
        tensor.reshape(-1)[0] += 1
    before = witness(rig)
    with pytest.raises(ValueError):
        rig.env.commit_initial_participation(prepared=prepared, population_ready=ready)
    assert rig.env.world_phase == "quarantined"
    assert_unchanged(rig, before)


@pytest.mark.parametrize("field", ["dones", "step_counts", "positions", "meters", "_velocity"])
def test_active_validator_rejects_tamper_before_any_transition(compiled: Any, field: str) -> None:
    rig = activated(compiled)
    tensor = getattr(rig.env, field)
    if field == "dones":
        tensor[1] = False
    else:
        tensor.reshape(-1)[0] += 1
    before = witness(rig)
    with pytest.raises(ValueError):
        rig.env.validate_initial_participation(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
    assert_unchanged(rig, before)
    assert not rig.step_registry and rig.ledger == ClockLedger()


@pytest.mark.parametrize("damage", ["copy_result", "foreign_result", "copy_token", "changed_predecessor"])
def test_active_validator_requires_private_predecessor_and_issued_result(compiled: Any, damage: str) -> None:
    rig = activated(compiled)
    participation, accepted, predecessor = rig.participation, rig.accepted, rig.current_obs.clone()
    if damage == "copy_result":
        participation = replace(participation)
    elif damage == "foreign_result":
        participation = activated(compiled).participation
    elif damage == "copy_token":
        accepted = replace(accepted)
    else:
        predecessor.add_(0.25)
    before = witness(rig)
    with pytest.raises(ValueError):
        rig.env.validate_initial_participation(accepted=accepted, participation=participation, predecessor=predecessor)
    assert_unchanged(rig, before)


def test_duplicate_reset_preserves_seal_and_activation_closes_window(compiled: Any) -> None:
    rig = activated(compiled)
    before = witness(rig)
    assert rig.env.reset(reservation=rig.reservation) is rig.reset
    equal(rig.env.dones, torch.tensor([False, True]))
    equal(rig.env.get_action_masks(), rig.participation.action_masks)
    intent = rig.issuer.issue(
        kind="initial_participation_intent",
        payload={"accepted": rig.accepted, "world_ids": IDS, "retired_world_ids": (), "population_revision": rig.revision},
    )
    with pytest.raises(ValueError):
        rig.env.prepare_initial_participation(accepted=rig.accepted, intent=intent)
    assert_unchanged(rig, before)


def test_pending_decision_refuses_duplicate_reset_reentry(compiled: Any, monkeypatch: Any) -> None:
    rig = ComponentPopulation(compiled)
    build = rig.env.action_mask_builder.build
    refused: list[bool] = []

    def read_with_reentry(**kwargs: Any) -> Any:
        with pytest.raises(ValueError):
            rig.env.reset(reservation=rig.reservation)
        refused.append(True)
        return build(**kwargs)

    monkeypatch.setattr(rig.env.action_mask_builder, "build", read_with_reentry)
    before = witness(rig)
    prepared = prepare(rig)
    assert refused == [True]
    assert_unchanged(rig, before)
    rig.publish(prepared)
    assert refused == [True]  # No deferred mask callback after the publication cut.


def test_live_empty_candidate_mask_refuses_before_publication(compiled: Any, monkeypatch: Any) -> None:
    rig = ComponentPopulation(compiled)
    build = rig.env.action_mask_builder.build

    def no_live_actions(**kwargs: Any) -> Any:
        mask = build(**kwargs)
        mask[0] = False
        return mask

    monkeypatch.setattr(rig.env.action_mask_builder, "build", no_live_actions)
    before = witness(rig)
    with pytest.raises(ValueError):
        prepare(rig)
    assert_unchanged(rig, before)
    assert not bool(rig.env.dones.any())


def test_mask_callback_physical_mutation_is_not_blessed_as_fresh(compiled: Any, monkeypatch: Any) -> None:
    rig = ComponentPopulation(compiled)
    build = rig.env.action_mask_builder.build

    def mutate_while_reading(**kwargs: Any) -> Any:
        mask = build(**kwargs)
        rig.env.meters[0, 0] += 1
        return mask

    monkeypatch.setattr(rig.env.action_mask_builder, "build", mutate_while_reading)
    rng_before = torch.get_rng_state().clone()
    with pytest.raises(ValueError):
        prepare(rig)
    assert rig.env.world_phase == "quarantined"
    assert not bool(rig.env.dones.any()) and not bool(rig.env.step_counts.any())
    equal(torch.get_rng_state(), rng_before)


def test_prepublication_allocation_failure_invalidates_old_handle(compiled: Any, monkeypatch: Any) -> None:
    rig = ComponentPopulation(compiled)
    prepared = prepare(rig)
    ready = rig.stage_ready(prepared)
    record = rig.env._record

    def fail_result(kind: str, payload: Any) -> Any:
        if kind == "initial_participation":
            raise MemoryError("controlled result allocation failure before status publication")
        return record(kind, payload)

    before = witness(rig)
    with monkeypatch.context() as patch:
        patch.setattr(rig.env, "_record", fail_result)
        with pytest.raises(MemoryError):
            rig.env.commit_initial_participation(prepared=prepared, population_ready=ready)
    assert_unchanged(rig, before)
    with pytest.raises(ValueError):
        rig.env.commit_initial_participation(prepared=prepared, population_ready=ready)
    fresh = rig.env.prepare_initial_participation(accepted=rig.accepted, intent=rig.intent)
    assert fresh is not prepared
    rig.ready = None  # Low-level component abandons its invalidated ready custody.
    rig.publish(fresh)


def test_exception_after_status_publication_quarantines_without_rollback(compiled: Any, monkeypatch: Any) -> None:
    rig = ComponentPopulation(compiled)
    prepared = prepare(rig)
    ready = rig.stage_ready(prepared)
    original_setattr = type(rig.env).__setattr__
    fired: list[bool] = []

    def publish_then_fail(env: Any, name: str, value: Any) -> None:
        original_setattr(env, name, value)
        if env is rig.env and name == "dones" and bool(value[1]) and not fired:
            fired.append(True)
            raise RuntimeError("controlled interruption immediately after actual status assignment")

    with monkeypatch.context() as patch:
        patch.setattr(type(rig.env), "__setattr__", publish_then_fail)
        with pytest.raises(RuntimeError):
            rig.env.commit_initial_participation(prepared=prepared, population_ready=ready)
    assert fired == [True] and bool(rig.env.dones[1])
    assert rig.env.world_phase == "quarantined" and rig.activation is None
    assert rig.env.global_tick == 0 and not bool(rig.env.step_counts.any())
    with pytest.raises(ValueError):
        rig.env.commit_initial_participation(prepared=prepared, population_ready=ready)
    with pytest.raises(ValueError):
        rig.env.vfs_random_state()


def test_postpublication_activation_failure_quarantines(compiled: Any, monkeypatch: Any) -> None:
    rig = ComponentPopulation(compiled)
    rig.publish(prepare(rig))
    issue = rig.issuer.issue

    def fail_activation(*, kind: str, payload: Any) -> Any:
        if kind == "activation":
            raise MemoryError("controlled separate activation allocation failure")
        return issue(kind=kind, payload=payload)

    monkeypatch.setattr(rig.issuer, "issue", fail_activation)
    with pytest.raises(MemoryError):
        rig.activate()
    assert rig.env.world_phase == "quarantined" and rig.activation is None
    equal(rig.env.dones, torch.tensor([False, True]))
    assert rig.ledger == ClockLedger()


def test_prepared_capability_cannot_cross_receiver_or_restore_phase(compiled: Any) -> None:
    source, destination = ComponentPopulation(compiled), ComponentPopulation(compiled)
    prepared = prepare(source)
    ready = source.stage_ready(prepared)
    before = witness(destination)
    with pytest.raises(ValueError):
        destination.env.commit_initial_participation(prepared=prepared, population_ready=ready)
    with pytest.raises(ValueError):
        destination.env.prepare_world_restore(
            kind="INITIAL",
            state={},  # Deliberately invalid data, never presented as a genuine native snapshot.
            world_roster=WorldRosterDeclaration(IDS),
            destination_world_ids=IDS,
            semantic_execution_identity=destination.env.semantic_execution_identity,
        )
    assert destination.env.world_phase == "active-awaiting-activation"
    assert_unchanged(destination, before)


def test_constructed_step_is_not_an_authority_after_retirement(compiled: Any) -> None:
    rig = activated(compiled)
    before = witness(rig)
    with pytest.raises(ValueError):
        rig.env.step(torch.zeros(len(IDS), dtype=torch.long), vector_step=PreparedVectorStep())
    assert_unchanged(rig, before)


@pytest.mark.parametrize("with_participation", [True, False])
def test_claim_cleanup_cannot_resume_physics(compiled: Any, monkeypatch: Any, with_participation: bool) -> None:
    """A real once-claim followed by public cleanup must stop before ENV's write cut."""
    claim = ComponentPopulation.claim_vector_step
    abandonments: list[Any] = []

    def claim_then_abandon(owner: ComponentPopulation, *, prepared: Any, **candidate: Any) -> int:
        tick = claim(owner, prepared=prepared, **candidate)
        abandonments.append(owner.env.abandon_episode(accepted=owner.accepted, reason="runtime_failure"))
        return tick

    # Construction binds this real owner callback once; no late ENV callback rebinding.
    monkeypatch.setattr(ComponentPopulation, "claim_vector_step", claim_then_abandon)
    rig = ComponentPopulation(compiled)
    if with_participation:
        rig.publish(prepare(rig))
    rig.activate()
    calls: list[str] = []
    reset_tick = rig.env.vfs_registry.reset_tick_scoped
    execute = rig.env._action_executor._execute_actions
    reward, service = rig.runtime.reward, rig.runtime.admit_and_service

    def observed_reset() -> Any:
        calls.append("registry")
        return reset_tick()

    def observed_execute(actions: Any) -> Any:
        calls.append("physics")
        return execute(actions)

    def observed_reward(**kwargs: Any) -> Any:
        calls.append("reward")
        return reward(**kwargs)

    def observed_service(**kwargs: Any) -> Any:
        calls.append("service")
        return service(**kwargs)

    monkeypatch.setattr(rig.env.vfs_registry, "reset_tick_scoped", observed_reset)
    monkeypatch.setattr(rig.env._action_executor, "_execute_actions", observed_execute)
    monkeypatch.setattr(rig.runtime, "reward", observed_reward)
    monkeypatch.setattr(rig.runtime, "admit_and_service", observed_service)
    actions = torch.full((len(IDS),), rig.env.action_ids["WAIT"], dtype=torch.long)
    prepared = rig.prepare_step(actions)
    before, revision = witness(rig), rig.env._world_revision
    with pytest.raises(ValueError):
        rig.env.step(actions, vector_step=prepared)
    assert rig.step_registry[id(prepared)]["claimed"] and rig.step_started
    assert len(abandonments) == 1 and abandonments[0].accepted is rig.accepted
    assert rig.env.world_phase == "quarantined"
    assert rig.env._world_revision == revision
    assert calls == []
    assert_unchanged(rig, before)


def observe_refused_encoder_cleanup(rig: ComponentPopulation, monkeypatch: Any) -> dict[str, Any]:
    """Observe real nested refusal separately from actual cleanup after guard unwind."""
    encode = rig.env._encode_observations
    abandon, record = rig.env.abandon_episode, rig.env._record
    probe: dict[str, Any] = {"encode": encode, "events": [], "attempts": [], "refused": [], "abandonments": [], "records": []}

    def observed_record(kind: str, payload: Any) -> Any:
        probe["records"].append(kind)
        return record(kind, payload)

    def observed_abandon(*, accepted: Any, reason: str) -> Any:
        probe["attempts"].append((accepted, reason, rig.activation))
        try:
            result = abandon(accepted=accepted, reason=reason)
        except ValueError as error:
            probe["refused"].append(error)
            raise
        probe["abandonments"].append(result)
        return result

    def encode_then_attempt_cleanup() -> Any:
        probe["events"].append("entered")
        encode()  # Preserve genuine outer observation work before the rejected cleanup.
        probe["events"].append("encoded")
        before = witness(rig)
        phase, revision, records = rig.env.world_phase, rig.env._world_revision, tuple(probe["records"])
        probe["events"].append("attempted")
        try:
            rig.env.abandon_episode(accepted=rig.accepted, reason="runtime_failure")
        except ValueError as error:
            assert probe["refused"][-1] is error
            assert rig.env.world_phase == phase and rig.env._world_revision == revision
            assert tuple(probe["records"]) == records
            assert_unchanged(rig, before)
            probe["events"].append("refused")
            raise
        raise AssertionError("nested encoder cleanup unexpectedly completed")

    monkeypatch.setattr(rig.env, "_record", observed_record)
    monkeypatch.setattr(rig.env, "abandon_episode", observed_abandon)
    monkeypatch.setattr(rig.env, "_encode_observations", encode_then_attempt_cleanup)
    return probe


def test_observation_cleanup_cannot_return_healthy_validation(compiled: Any, monkeypatch: Any) -> None:
    """An escaping observation fault denies validation; genuine later cleanup stays durable."""
    rig = activated(compiled)
    probe = observe_refused_encoder_cleanup(rig, monkeypatch)
    before, revision = witness(rig), rig.env._world_revision
    with pytest.raises(ValueError) as failure:
        rig.env.validate_initial_participation(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
    assert probe["events"] == ["entered", "encoded", "attempted", "refused"]
    assert probe["refused"] == [failure.value] and len(probe["attempts"]) == 1 and probe["abandonments"] == []
    monkeypatch.setattr(rig.env, "_encode_observations", probe["encode"])
    cleanup = rig.env.abandon_episode(accepted=rig.accepted, reason="runtime_failure")
    abandonments = probe["abandonments"]
    assert len(abandonments) == 1 and abandonments[0].reason == "runtime_failure"
    assert abandonments[0] is cleanup and cleanup.accepted is rig.accepted and len(probe["attempts"]) == 2
    with pytest.raises(ValueError):
        rig.env.validate_initial_participation(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
    assert rig.env.world_phase == "quarantined" and rig.env._world_revision == revision
    assert_unchanged(rig, before)


def test_observation_cleanup_cannot_activate_quarantined_episode(compiled: Any, monkeypatch: Any) -> None:
    rig = ComponentPopulation(compiled)
    rig.publish(prepare(rig))
    probe = observe_refused_encoder_cleanup(rig, monkeypatch)
    begin, curiosity = rig.runtime.begin_episode, []

    def observed_begin(**kwargs: Any) -> Any:
        result = begin(**kwargs)
        curiosity.append(result)
        return result

    monkeypatch.setattr(rig.runtime, "begin_episode", observed_begin)
    before, revision = witness(rig), rig.env._world_revision
    with pytest.raises(ValueError) as failure:
        rig.activate()
    assert probe["events"] == ["entered", "encoded", "attempted", "refused"]
    assert probe["refused"] == [failure.value] and len(probe["attempts"]) == 2
    abandonments = probe["abandonments"]  # Actual ComponentPopulation.activate cleanup after ENV unwound.
    assert len(abandonments) == 1 and abandonments[0].accepted is rig.accepted
    assert abandonments[0].reason == "runtime_failure"
    retained_activation = probe["attempts"][0][2]
    assert retained_activation is not None and probe["attempts"][1][2] is None and len(curiosity) == 1
    monkeypatch.setattr(rig.env, "_encode_observations", probe["encode"])
    with pytest.raises(ValueError):
        rig.env.activate_episode(accepted=rig.accepted, population_receipt=retained_activation, curiosity_receipt=curiosity[0])
    assert rig.env.world_phase == "quarantined" and rig.env._world_revision == revision
    assert rig.activation is None
    assert_unchanged(rig, before)


def test_reading_validator_accepts_genuine_committed_preactivation(compiled: Any) -> None:
    """Q1 causal RED reaches the absent reading API after genuine reset/decision commit."""
    rig = ComponentPopulation(compiled)
    rig.publish(prepare(rig))
    assert rig.env.world_phase == "active-awaiting-activation" and rig.activation is None
    before, revision = witness(rig), rig.env._world_revision
    assert (
        rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
        is None
    )
    assert rig.env.world_phase == "active-awaiting-activation" and rig.env._world_revision == revision
    assert_unchanged(rig, before)
    with pytest.raises(ValueError):
        rig.env.validate_initial_participation(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
    with pytest.raises(ValueError):
        rig.env.step(torch.zeros(len(IDS), dtype=torch.long), vector_step=PreparedVectorStep())


@pytest.mark.parametrize("damage", ["copy_result", "foreign_result", "copy_token", "mutated_record", "predecessor"])
def test_reading_validator_authenticates_current_private_reading(compiled: Any, damage: str) -> None:
    rig = activated(compiled)
    participation, accepted, predecessor = rig.participation, rig.accepted, rig.current_obs.clone()
    if damage == "copy_result":
        participation = replace(participation)
    elif damage == "foreign_result":
        participation = activated(compiled).participation
    elif damage == "copy_token":
        accepted = replace(accepted)
    elif damage == "mutated_record":
        fields = participation.payload
        fields["observation"].add_(1)
        participation = replace(participation, _payload=fields)
    else:
        predecessor.add_(0.25)
    before, revision = witness(rig), rig.env._world_revision
    with pytest.raises(ValueError):
        rig.env.validate_initial_participation_reading(accepted=accepted, participation=participation, predecessor=predecessor)
    assert rig.env._world_revision == revision
    assert_unchanged(rig, before)


@pytest.mark.parametrize("field", ["positions", "meters", "dones", "step_counts"])
def test_reading_validator_rejects_public_physical_tamper(compiled: Any, field: str) -> None:
    rig = activated(compiled)
    value = getattr(rig.env, field)
    if field == "dones":
        value[1] = False
    else:
        value.reshape(-1)[0] += 1
    before, revision = witness(rig), rig.env._world_revision
    with pytest.raises(ValueError):
        rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
    assert rig.env.world_phase == "quarantined" and rig.env._world_revision == revision
    assert_unchanged(rig, before)


def test_reading_validator_cleanup_is_durable(compiled: Any, monkeypatch: Any) -> None:
    rig = activated(compiled)
    probe = observe_refused_encoder_cleanup(rig, monkeypatch)
    before, revision = witness(rig), rig.env._world_revision
    with pytest.raises(ValueError) as failure:
        rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
    assert probe["events"] == ["entered", "encoded", "attempted", "refused"]
    assert probe["refused"] == [failure.value] and len(probe["attempts"]) == 1 and probe["abandonments"] == []
    monkeypatch.setattr(rig.env, "_encode_observations", probe["encode"])
    cleanup = rig.env.abandon_episode(accepted=rig.accepted, reason="runtime_failure")
    abandonments = probe["abandonments"]
    assert len(abandonments) == 1 and abandonments[0].accepted is rig.accepted
    assert abandonments[0] is cleanup and cleanup.reason == "runtime_failure" and len(probe["attempts"]) == 2
    for _ in range(2):
        with pytest.raises(ValueError):
            rig.env.validate_initial_participation_reading(
                accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs
            )
    assert rig.env.world_phase == "quarantined" and rig.env._world_revision == revision
    assert_unchanged(rig, before)


def test_pending_decision_cannot_be_used_as_reading_authority(compiled: Any) -> None:
    rig = ComponentPopulation(compiled)
    prepared = prepare(rig)
    before = witness(rig)
    with pytest.raises(ValueError):
        rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=prepared, predecessor=rig.current_obs)
    assert_unchanged(rig, before)
    rig.publish(prepared)  # A pure refused query must not consume the actual pending decision.
    equal(rig.env.dones, torch.tensor([False, True]))


def test_failed_episode_cannot_use_retained_reading_authority(compiled: Any) -> None:
    rig = activated(compiled)
    rig.env.abandon_episode(accepted=rig.accepted, reason="runtime_failure")
    before = witness(rig)
    with pytest.raises(ValueError):
        rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
    assert rig.env.world_phase == "quarantined"
    assert_unchanged(rig, before)


def test_activation_in_progress_refuses_recursive_reading(compiled: Any, monkeypatch: Any) -> None:
    """The readable preactivation phase must not bypass actual activation's busy fence."""
    rig = ComponentPopulation(compiled)
    rig.publish(prepare(rig))
    encode = rig.env._encode_observations
    refused: list[bool] = []

    def encode_with_query() -> Any:
        observation = encode()
        with pytest.raises(ValueError):
            rig.env.validate_initial_participation_reading(
                accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs
            )
        refused.append(True)
        return observation

    monkeypatch.setattr(rig.env, "_encode_observations", encode_with_query)
    before, revision = witness(rig), rig.env._world_revision
    rig.activate()
    assert refused == [True] and rig.env.world_phase == "active"
    assert rig.env._world_revision == revision
    assert_unchanged(rig, before)


def reading_phase(compiled: Any, phase: str) -> ComponentPopulation:
    """Earn completed phases through a declared one-step component cap and real sinks."""
    rig = ComponentPopulation(compiled)
    rig.publish(prepare(rig))
    if phase == "active-awaiting-activation":
        return rig
    rig.activate()
    if phase == "active":
        return rig
    observations, rewards, _, info, _ = rig.step()
    equal(rig.env.step_counts, torch.tensor([1, 0]))
    event = LaneOutcome(
        outcome=EpisodeCompletion(
            agent_idx=0,
            reason="cap",
            survival_time=1,
            final_observation=observations[0].detach().cpu().clone(),
            final_meters=rig.env.meters[0].detach().cpu().clone(),
        ),
        batch_episode=rig.accepted.batch_episode,
        planned_horizon=1,
        reward_total=float(rewards[0]),
        reward_extrinsic=float(info["reward_components"]["extrinsic"][0]),
        reward_intrinsic=float(info["reward_components"]["intrinsic"][0]),
        reward_shaping=float(info["reward_components"]["shaping"][0]),
        policy_entropy=0.0,  # The real component control always chooses WAIT, not a Q policy.
        world_id=IDS[0],
        world_episode_seq=rig.accepted.world_episode_seqs[0],
    )
    outcomes = (event,)
    content = tuple((item.payload.hex(), item.fingerprint) for item in map(freeze_lane_outcome, outcomes))
    key = rig.accepted.batch_episode
    rig.completion_before = owned(rig.runtime.checkpoint_state())
    curriculum = rig.curriculum.prepare_episode_outcomes(outcomes)
    bank = rig.runtime.prepare_completion(
        accepted=rig.accepted, boundary_key=key, completion_content=content, outcomes=outcomes, participated_world_ids=(IDS[0],)
    )
    close = rig.env.prepare_episode_close(
        accepted=rig.accepted,
        boundary_key=key,
        completion_content=content,
        participated_world_ids=(IDS[0],),
        dispositions=bank.prepared_receipt,
    )
    rig.env.freeze_episode_close(close)
    rig.close_context = (curriculum, bank, close, outcomes, content, key)
    if phase == "boundary-pending":
        return rig
    return finish_reading_close(rig, phase)


def finish_reading_close(rig: ComponentPopulation, phase: str) -> ComponentPopulation:
    curriculum, bank, close, outcomes, content, key = rig.close_context
    rig.curriculum.commit_prepared_episode_outcomes(curriculum)
    retirement = rig.runtime.commit_completion(prepared=bank)
    rig.completion_request = (rig.accepted, key, content)
    rig.runtime.commit_batch_episode(batch_episode=key, outcomes=outcomes)
    original_before = rig.completion_before["selector"]["epsilon"]
    expected_after = max(rig.policy.epsilon_end, original_before * rig.policy.epsilon_decay)
    published = rig.runtime.checkpoint_state()  # BANK completion is committed; no pending export.
    assert rig.runtime.epsilon == expected_after
    equal(
        published["selector"],
        {
            "epsilon": expected_after,
            "epsilon_min": rig.policy.epsilon_end,
            "epsilon_decay": rig.policy.epsilon_decay,
        },
    )
    equal(
        published["cadence"]["last_committed"],
        {
            "batch_episode": key,
            "completion_content": content,
            "epsilon_before": original_before,
            "epsilon_after": expected_after,
        },
    )
    rig.runtime.commit_batch_episode(batch_episode=key, outcomes=outcomes)  # Exact supported retry, not another completion.
    equal(rig.runtime.checkpoint_state(), published)
    rig.committed_batches[key] = content
    rig.completed = torch.ones_like(rig.completed)  # Genuine declared component cap finalized A; B was already retired.
    rig.ledger = rig.ledger.advance(completed_batch_episodes=1)
    rig.current_epsilons = rig.runtime.epsilon_tensor(batch_size=len(IDS), device=rig.device)
    equal(rig.current_epsilons, torch.full((len(IDS),), rig.runtime.epsilon, dtype=torch.float32))
    closure = rig.env.close_episode(close, dispositions=retirement)
    assert dict(retirement.dispositions)[IDS[1]] == "retired_nonparticipating"
    if phase == "closed-awaiting-release":
        return rig
    fields = {"accepted": rig.accepted, "boundary_key": key, "completion_content": content}
    effects = rig.issuer.issue(
        kind="boundary_effects",
        payload={
            "batch_episode": key,
            "accepted_identity": rig.accepted,
            "completion_content": content,
            "retirement_receipt": retirement,
            "curriculum_receipt": rig.curriculum_issuer.issue(kind="curriculum_receipt", payload=fields),
            **{
                name: rig.issuer.issue(kind=name, payload=fields)
                for name in ("exploration_receipt", "population_commit_receipt", "epsilon_install_receipt", "selection_sync_receipt")
            },
        },
    )
    rig.release = rig.authority.completed(closure=closure, effects=effects)
    rig.env.install_boundary_release(rig.release)
    assert phase == "released-completed"
    return rig


@pytest.mark.parametrize("phase", ["active-awaiting-activation", "active", "closed-awaiting-release", "released-completed"])
def test_reading_validator_preserves_each_genuine_healthy_phase(compiled: Any, monkeypatch: Any, phase: str) -> None:
    claim, claim_calls = ComponentPopulation.claim_vector_step, []

    def observed_claim(owner: ComponentPopulation, *, prepared: Any, **candidate: Any) -> int:
        claim_calls.append(prepared)
        return claim(owner, prepared=prepared, **candidate)

    monkeypatch.setattr(ComponentPopulation, "claim_vector_step", observed_claim)
    rig = reading_phase(compiled, phase)
    claim_calls.clear()  # Earned closed phases used their genuine claim before this reading boundary.
    assert rig.env.world_phase == phase
    components_before, runtime_before = component_state(rig), rig.runtime.checkpoint_state()
    before, revision = witness(rig), rig.env._world_revision

    def forbidden_mask(**kwargs: Any) -> Any:
        raise AssertionError("a pure reading must not recompute action masks")

    monkeypatch.setattr(rig.env.action_mask_builder, "build", forbidden_mask)
    rig.participation.observation.add_(100)
    rig.participation.action_masks.fill_(True)
    for _ in range(2):
        assert (
            rig.env.validate_initial_participation_reading(
                accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs
            )
            is None
        )
    assert rig.env.world_phase == phase and rig.env._world_revision == revision
    assert_unchanged(rig, before)
    equal(component_state(rig), components_before)
    equal(rig.runtime.checkpoint_state(), runtime_before)
    if phase != "active":
        with pytest.raises(ValueError):
            rig.env.validate_initial_participation(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
        with pytest.raises(ValueError):
            rig.env.step(torch.zeros(len(IDS), dtype=torch.long), vector_step=PreparedVectorStep())
    assert claim_calls == []


def test_frozen_close_refuses_reading_without_consuming_sink_handles(compiled: Any) -> None:
    rig = reading_phase(compiled, "boundary-pending")
    original_context = rig.close_context
    before = witness(rig)
    with pytest.raises(ValueError):
        rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
    assert rig.env.world_phase == "boundary-pending"
    assert_unchanged(rig, before)
    finish_reading_close(rig, "released-completed")
    assert rig.close_context is original_context and rig.env.world_phase == "released-completed"
    assert rig.ledger.completed_batch_episodes == 1
    assert rig.committed_batches == {original_context[5]: original_context[4]}


def test_new_genuine_reset_invalidates_prior_reading_identity(compiled: Any) -> None:
    rig = reading_phase(compiled, "released-completed")
    old_participation, old_accepted = rig.participation, rig.accepted
    reservation = rig.env.prepare_episode(batch_episode=rig.release.next_batch_episode, release=rig.release)
    reset = rig.env.reset(reservation=reservation)
    rig.reservation, rig.reset, rig.accepted, rig.current_obs = reservation, reset, reset.accepted, reset.observation
    rig.participation = rig.activation = None
    rig.retired = None
    rig.step_started = False
    rig.publish(prepare(rig))
    assert rig.accepted is not old_accepted and rig.accepted.world_episode_seqs == (2, 2)
    before = witness(rig)
    with pytest.raises(ValueError):
        rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=old_participation, predecessor=rig.current_obs)
    rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
    assert_unchanged(rig, before)
    rig.activate()
    _, _, _, info, _ = rig.step()
    equal(info["component_selection_epsilons"], rig.runtime.epsilon_tensor(batch_size=len(IDS), device=rig.device))


@pytest.mark.parametrize("damage", ["dtype", "width", "nonfinite"])
def test_reading_validator_requires_actual_finite_observation_geometry(compiled: Any, damage: str) -> None:
    rig = activated(compiled)
    predecessor = rig.current_obs.clone()
    if damage == "dtype":
        predecessor = predecessor.to(torch.float64)
    elif damage == "width":
        predecessor = predecessor[:, :-1]
    else:
        predecessor[0, 0] = float("nan")
    before, revision = witness(rig), rig.env._world_revision
    with pytest.raises(ValueError):
        rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=rig.participation, predecessor=predecessor)
    assert rig.env._world_revision == revision and rig.env.world_phase == "active"
    assert_unchanged(rig, before)
