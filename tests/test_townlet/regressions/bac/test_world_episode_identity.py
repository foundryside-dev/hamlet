"""Real ENV/component lifecycle; world-only native attestations stay limited.

Independent real owners and canonical replay/service do not qualify production
POP learning, all-child T25/T26 installation or simulator independence. _Sink is
restricted to deliberately bad/interface-unit evidence, never positive closure.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

IDS = ("orchard-west", "river-house")
SEED = 479
CLOCK_UNITS = (
    "vector_ticks",
    "eligible_transitions",
    "optimizer_updates",
    "completed_batch_episodes",
    "predictor_admitted_rows",
    "predictor_consumed_minibatches",
    "predictor_dropped_rows",
)


@pytest.fixture(scope="module")
def compiled():
    from townlet.universe.compiler import UniverseCompiler

    result = UniverseCompiler().compile(
        Path(__file__).resolve().parents[4] / "configs/test/token_set_smoke",
        primary_level="L0_test",
        use_cache=False,
    )
    assert result.to_dict()["compiled_schema_version"] == "1.42"
    return result


def _roster(ids=IDS):
    from townlet.config.world_roster import WorldRosterDeclaration

    return WorldRosterDeclaration.from_dict({"schema": "world-roster-v1", "world_ids": list(ids)})


def _env(compiled, order=IDS):
    from townlet.environment.vectorized_env import VectorizedHamletEnv

    return VectorizedHamletEnv(
        universe=compiled,
        level_name="L0_test",
        num_agents=2,
        device="cpu",
        world_roster=_roster(),
        training_seed=SEED,
        lane_world_ids=order,
    )


def _baseline_inputs(compiled):
    from townlet.config.drive_as_code import IntrinsicStrategyConfig
    from townlet.config.training_v2_config import TrainingV2Config

    selected = compiled.get_level("L0_test")
    drive = selected.drive.intrinsic.model_dump()
    drive.update(strategy="none", base_weight=0.0, apply_modifiers=[])
    return {
        "drive_intrinsic": IntrinsicStrategyConfig.model_validate(drive),
        "training_input": TrainingV2Config.model_validate(selected.training.model_dump()),
    }


def _selected_inputs(compiled, *, family, scope):
    from townlet.config.bac_options import BaCOptions
    from townlet.config.drive_as_code import IntrinsicStrategyConfig
    from townlet.config.training_v2_config import TrainingV2Config

    selected = compiled.get_level("L0_test")
    drive = selected.drive.intrinsic.model_dump()
    drive.update(strategy=family, base_weight=0.0 if family == "none" else 0.4, apply_modifiers=[])
    training = selected.training.model_dump()
    training["replay_buffer"]["batch_size"] = 2
    training["intrinsic"]["rnd"].update(feature_dim=4, learning_rate=0.001)
    training["intrinsic"].update(initial_weight=0.4, survival_window=10, min_survival_fraction=0.01)
    training["intrinsic"]["annealing"].update(min_weight=0.01, threshold=100.0, decay_rate=0.9)
    training["training_loop"]["max_steps_per_episode"] = 20
    options = {
        "curiosity_scope": {"scope": scope, "seed_policy": "legacy_shared_v1" if scope == "shared" else "world_id_derived_v1"},
        "provider_parameter_source": "training",
        "rnd": {"service_mode": "paced_fifo", "max_updates_per_tick": 1, "max_pending_rows": 4, "overflow_policy": "drop_oldest"},
        "providers": {
            "count_based": {"quantization_width": 0.125, "max_entries": 4},
            "icm": {
                "feature_dim": 4,
                "hidden_dim": 8,
                "learning_rate": 0.001,
                "inverse_weight": 0.8,
                "forward_weight": 0.2,
                "training_batch_size": 2,
                "max_pending_transitions": 4,
            },
        },
    }
    training["bac_options"] = BaCOptions.model_validate(options).model_dump()
    return {
        "drive_intrinsic": IntrinsicStrategyConfig.model_validate(drive),
        "training_input": TrainingV2Config.model_validate(training),
    }


def _same(left, right):
    if isinstance(left, torch.Tensor):
        assert isinstance(right, torch.Tensor)
        assert left.dtype == right.dtype and left.device == right.device
        assert left.shape == right.shape and torch.equal(left, right)
    elif isinstance(left, np.ndarray):
        assert type(left) is type(right) and left.dtype == right.dtype
        assert left.shape == right.shape and np.array_equal(left, right)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            _same(left[key], right[key])
    elif isinstance(left, (tuple, list)):
        assert type(left) is type(right) and len(left) == len(right)
        for first, second in zip(left, right, strict=True):
            _same(first, second)
    else:
        assert type(left) is type(right) and left == right


def _state(env):
    """Observable identity plus real mutable simulator/RNG witnesses."""
    return {
        "phase": env.world_phase,
        "ids": env.world_ids,
        "cursors": dict(env.accepted_episode_seqs),
        "positions": env.positions.clone(),
        "meters": env.meters.clone(),
        "dones": env.dones.clone(),
        "steps": env.step_counts.clone(),
        "tick": env.global_tick,
        "vfs": deepcopy(env.vfs_random_state()),
        "rng": torch.get_rng_state().clone(),
    }


def _unissued_step():
    from townlet.training.clock_ledger import PreparedVectorStep

    return PreparedVectorStep()


class _Sink:
    """Cooperative local owner; only issuer-sealed evidence is accepted by ENV.

    This is not a fake implementation of POP canonical outcome validation.
    Its event content is deliberately an opaque interface fixture.
    """

    def __init__(self):
        from townlet.environment.vectorized_env import WorldReceiptIssuer

        self.issuer = WorldReceiptIssuer(owner=self)
        self.accepted = None
        self.participants = ()
        self.records = {}
        self.initial_weight = torch.tensor([0.25, -0.75])

    def receipt(self, receipt_kind, **payload):
        return self.issuer.issue(kind=receipt_kind, payload=payload)

    def prepare_empty_episode_evidence(self, *, accepted):
        if accepted is not self.accepted or self.participants:
            raise ValueError("not an empty accepted episode")
        return self.receipt("empty_episode", accepted=accepted, participated_world_ids=(), events=())

    def activation(self, accepted):
        self.accepted = accepted
        return self.receipt("activation", accepted=accepted)


class _Run:
    def __init__(self, env, bootstrap=True, *, drive_intrinsic, training_input):
        from townlet.agent.network_factory import NetworkFactory
        from townlet.agent.optimizer_factory import OptimizerFactory
        from townlet.config.bac_options import resolve_bac_options
        from townlet.config.brain_config import apply_training_overrides
        from townlet.config.drive_as_code import IntrinsicStrategyConfig
        from townlet.config.exploration_policy import build_exploration, resolve_exploration_policy
        from townlet.config.training_v2_config import TrainingV2Config
        from townlet.curriculum.factory import build_curriculum
        from townlet.environment.vectorized_env import WorldReceiptIssuer
        from townlet.exploration.world_curiosity_state import WorldCuriosityDescriptor
        from townlet.training.clock_ledger import ClockLedger
        from townlet.training.replay_buffer import ReplayBuffer

        self.env = env
        self.boundary = self.population = self
        assert isinstance(drive_intrinsic, IntrinsicStrategyConfig)
        assert isinstance(training_input, TrainingV2Config)
        authored = training_input.model_dump()
        authored["population"]["size"] = env.num_agents
        authored["seed"] = env.vfs_random_state()["training_seed"]
        training = TrainingV2Config.model_validate(authored)
        options = resolve_bac_options(training.bac_options, training=training).options
        brain = apply_training_overrides(env.universe.brain, training)
        assert brain.architecture.token_set is not None
        self.q = NetworkFactory.build_token_set(
            config=brain.architecture.token_set, action_dim=env.action_dim, token_spec=env.token_spec
        ).to(env.device)
        self.optimizer, self.scheduler = OptimizerFactory.build(config=brain.optimizer, parameters=self.q.parameters())
        self.replay_capacity = brain.replay.capacity
        self.replay = ReplayBuffer(capacity=self.replay_capacity, device=env.device)
        effective = env.universe.effective_run
        self.curriculum = build_curriculum(
            training, curriculum_options=effective.options.curriculum, static_policy=effective.static_policy, device=env.device
        )
        self.curriculum.initialize_population(env.num_agents)
        self.policy = resolve_exploration_policy(
            drive_intrinsic=drive_intrinsic,
            training=training,
            options=options,
        )
        descriptor = WorldCuriosityDescriptor.from_policy(
            self.policy,
            world_ids=env.world_ids,
            observation_dim=env.observation_dim,
            action_dim=env.action_dim,
            training_seed=training.seed,
        )
        self.bank = self.bank_issuer = None
        self.reports = []
        self.completion_request = None
        self.committed_batches = {}
        self.component_commitment = None
        self.runtime = build_exploration(
            policy=self.policy,
            descriptor=descriptor,
            device=env.device,
            validate_accepted_episode=env.validate_accepted_episode,
            issuer_factory=self.capture_bank,
            report_allocation=self.reports.append,
            validate_committed_batch=self.validate_committed_batch,
            validate_parent_cadence=self.validate_parent_cadence,
        )
        assert self.bank is not None and self.bank is not self.runtime
        self.issuer = WorldReceiptIssuer(owner=self)
        self.roles = {
            "population": self,
            "curiosity": self.bank,
            "curriculum": self.curriculum,
            "exploration": self.runtime,
            "network": self.q,
            "optimizer": self.optimizer,
            "scheduler": self if self.scheduler is None else self.scheduler,
            "replay": self.replay,
            "selection": self.runtime,
        }
        # Explicit cooperative fixture custody, established BEFORE role binding.
        # These are not facade-produced effects; BANK's issuer is BANK-only.
        self.role_issuers = {
            name: self.bank_issuer if name == "curiosity" else WorldReceiptIssuer(owner=owner) for name, owner in self.roles.items()
        }
        self.role_issuers["population"] = self.issuer
        self.ledger = ClockLedger()
        self.revision = 0
        self.step_registry = {}
        self.pending_step = None
        self.step_started = False
        self.current_epsilons = self.runtime.epsilon_tensor(batch_size=env.num_agents, device=env.device)
        self.release = None
        self.accepted = None
        self.events = {}
        self.outcomes = {}
        self.close_contexts = {}
        self.activation_receipt = self.participation = None
        self.restore_context = None
        self.control_horizon = 1  # Declared deterministic component cap, before any reset/step.
        env.set_exploration_runtime(exploration=self.runtime, claim_vector_step=self.claim_vector_step)
        self.authority = env.bind_boundary_authority(owner=self, role_owners=self.roles)
        if bootstrap:
            self.release = env.install_boundary_release(self.authority.bootstrap(first_batch_episode=1))

    def capture_bank(self, bank):
        from townlet.environment.vectorized_env import WorldReceiptIssuer

        if self.bank is not None:
            raise ValueError("one actual BANK per component controller")
        self.bank = bank
        self.bank_issuer = WorldReceiptIssuer(owner=bank)
        return self.bank_issuer

    def receipt(self, receipt_kind, **payload):
        return self.issuer.issue(kind=receipt_kind, payload=payload)

    def role_receipt(self, owner_role, receipt_kind, **payload):
        if owner_role == "population":
            return self.receipt(receipt_kind, **payload)
        return self.role_issuers[owner_role].issue(kind=receipt_kind, payload=payload)

    def validate_committed_batch(self, *, batch_episode, outcomes):
        from townlet.training.episode import freeze_lane_outcome

        content = tuple((item.payload.hex(), item.fingerprint) for item in map(freeze_lane_outcome, outcomes))
        request = self.completion_request
        if request is None or request[0] is not self.accepted or request[1:] != (batch_episode, content):
            raise ValueError("component does not own this complete canonical request")
        self.env.validate_accepted_episode(accepted=request[0])

    def validate_parent_cadence(self, *, cadence, mode, accepted, parent_restore):
        from townlet.training.clock_ledger import ClockLedger

        context = self.restore_context
        if context is None or parent_restore is not context["prepared"] or accepted is not None or mode != context["mode"]:
            raise ValueError("component runtime restore requires its genuine retained ENV preparation")
        component = context["component"]
        if type(component) is not dict or set(component) != {"schema", "last_committed", "ledger"}:
            raise ValueError("component continuation requires its exact portable record")
        if component["schema"] != "world-component-continuation-v1":
            raise ValueError("unknown component continuation schema")
        units = component["ledger"]
        if type(units) is not dict or set(units) != set(CLOCK_UNITS):
            raise ValueError("component continuation requires all seven clock units")
        earned_ledger = ClockLedger(**units)
        if type(context["ledger"]) is not ClockLedger or context["ledger"] != earned_ledger:
            raise ValueError("supplied ledger differs from recorded component work")
        last = component["last_committed"]
        state = parent_restore.state
        if mode == "initial":
            if state["kind"] != "INITIAL" or last is not None or earned_ledger != ClockLedger():
                raise ValueError("INITIAL continuation requires genuine zero component history")
            expected = None
        else:
            if (
                state["kind"] != "COMPLETED"
                or type(last) is not dict
                or set(last) != {"batch_episode", "completion_content", "epsilon_before", "epsilon_after"}
            ):
                raise ValueError("COMPLETED continuation requires its earned canonical commitment")
            closed = state["last_closed_episode"]
            if type(last["batch_episode"]) is not int or last["batch_episode"] != state["completed_boundary_key"]:
                raise ValueError("component commitment differs from prepared parent boundary")
            content = last["completion_content"]
            if (
                type(content) is not list
                or not content
                or any(
                    type(pair) is not list or len(pair) != 2 or any(type(value) is not str or not value for value in pair)
                    for pair in content
                )
            ):
                raise ValueError("component commitment requires full ordered canonical content")
            canonical = tuple(tuple(pair) for pair in content)
            if last["batch_episode"] != closed["batch_episode"] or canonical != tuple(map(tuple, closed["completion_content"])):
                raise ValueError("component commitment differs from actual prepared closure")
            if earned_ledger.completed_batch_episodes == 0 or any(
                type(last[name]) not in (int, float) for name in ("epsilon_before", "epsilon_after")
            ):
                raise ValueError("component commitment has no earned completion or schedule")
            expected = {**last, "completion_content": canonical}
        if cadence != {"schema": "parent-global-epsilon-cadence-v1", "last_committed": expected}:
            raise ValueError("runtime cadence differs from earned component commitment")

    def component_state(self):
        """Portable source journal, earned independently of runtime checkpoint input."""
        return {
            "schema": "world-component-continuation-v1",
            "last_committed": deepcopy(self.component_commitment),
            "ledger": {unit: getattr(self.ledger, unit) for unit in CLOCK_UNITS},
        }

    def validate_parent_restore(self, *, prepared, curiosity_state):
        context = self.restore_context
        if context is None or prepared is not context["prepared"]:
            raise ValueError("component BANK restore has no actual parent preparation")
        _same(curiosity_state, context["runtime"]["bank"])
        context["release"] = self.authority.restored(restore=prepared, boundary=context["boundary"])

    def adopt_reset(self, reservation, reset, *, retired_world_ids):
        if reset.accepted is self.accepted:
            if reservation is not self.reservation or retired_world_ids != self.retired:
                raise ValueError("changed component reset retry")
            self.check_current()
            return
        self.reservation, self.reset_record, self.accepted = reservation, reset, reset.accepted
        self.current_obs = reset.observation
        self.counts = self.env.step_counts.detach().clone()
        self.completed_lanes = self.env.dones.detach().clone()
        self._reading = self.current_obs.detach().clone()
        self._counts = self.counts.clone()
        self.activation_receipt = self.participation = None
        self.pending_step = None
        self.step_started = False
        self.retired = retired_world_ids
        self.episode_horizon = self.control_horizon
        self.reward_totals = {
            name: torch.zeros(self.env.num_agents, device=self.env.device) for name in ("total", "extrinsic", "intrinsic", "shaping")
        }
        intent = self.receipt(
            "initial_participation_intent",
            accepted=self.accepted,
            world_ids=self.accepted.world_ids,
            retired_world_ids=retired_world_ids,
            population_revision=self.revision,
        )
        self.intent = intent
        prepared = self.env.prepare_initial_participation(accepted=self.accepted, intent=intent)
        observation, masks = prepared.observation, prepared.action_masks
        _same(observation, self.current_obs)
        assert observation.shape == (self.env.num_agents, self.env.observation_dim)
        assert observation.dtype == torch.float32 and observation.device == self.env.device
        assert masks.shape == (self.env.num_agents, self.env.action_dim) and masks.dtype == torch.bool
        assert masks.device == self.env.device
        completed = torch.tensor([wid in retired_world_ids for wid in self.accepted.world_ids], dtype=torch.bool, device=self.env.device)
        assert not bool(masks[completed].any()) and bool(masks[~completed].any(dim=1).all())
        reading, counts, next_revision = observation.detach().clone(), self.counts.clone(), self.revision + 1
        ready = self.receipt(
            "initial_participation_ready", accepted=self.accepted, intent=intent, prepared=prepared, population_revision=self.revision
        )
        self.ready = ready
        participation = self.env.commit_initial_participation(prepared=prepared, population_ready=ready)
        # Paired suffix: preallocated reference assignments only.
        self.current_obs = observation
        self.current_masks = masks
        self.completed_lanes = completed
        self._reading = reading
        self._counts = counts
        self.revision = next_revision
        self.participation = participation
        self.intent = None
        self.ready = None

    def activation(self, accepted):
        if accepted is not self.accepted or self.participation is None:
            raise ValueError("activation requires this actual completed reset decision")
        if self.activation_receipt is None:
            self.activation_receipt = self.receipt("activation", accepted=accepted)
        return self.activation_receipt

    def activate(self):
        try:
            population = self.activation(self.accepted)
            curiosity = self.runtime.begin_episode(accepted=self.accepted)
            self.env.validate_initial_participation_reading(
                accepted=self.accepted, participation=self.participation, predecessor=self._reading
            )
            _same(self.current_obs, self._reading)
            _same(self.counts, self._counts)
            _same(self.env.step_counts, self._counts)
            _same(self.completed_lanes, self.env.dones)
            activation = self.env.activate_episode(accepted=self.accepted, population_receipt=population, curiosity_receipt=curiosity)
            _same(self.current_obs, self._reading)
            _same(self.counts, self._counts)
            return activation
        except BaseException:
            self.activation_receipt = None
            self.env.abandon_episode(accepted=self.accepted, reason="runtime_failure")
            raise

    def reset(self, batch, *, retired_world_ids):
        reservation = self.env.prepare_episode(batch_episode=batch, release=self.release)
        self.env.validate_episode_reservation(reservation)
        reset = self.env.reset(reservation=reservation)
        try:
            self.adopt_reset(reservation, reset, retired_world_ids=retired_world_ids)
            self.activate()
        except BaseException:
            self.activation_receipt = None
            self.env.abandon_episode(accepted=reset.accepted, reason="runtime_failure")
            raise
        return reservation, reset

    def check_current(self):
        if self.accepted is not self.reset_record.accepted:
            raise ValueError("component accepted custody changed")
        self.env.validate_initial_participation(accepted=self.accepted, participation=self.participation, predecessor=self._reading)
        _same(self.current_obs, self._reading)
        _same(self.counts, self._counts)
        _same(self.env.step_counts, self._counts)
        _same(self.completed_lanes, self.env.dones)

    def prepare_step(self, actions):
        from townlet.training.clock_ledger import PreparedVectorStep

        self.check_current()
        assert actions.dtype == torch.long and actions.device == self.env.device and actions.shape == (self.env.num_agents,)
        assert bool(((actions >= 0) & (actions < self.env.action_dim)).all())
        candidate = {
            "accepted": self.accepted,
            "world_ids": self.accepted.world_ids,
            "predecessor": self._reading.clone(),
            "actions": actions.detach().clone(),
            "active_on_entry": ~self.completed_lanes.clone(),
        }
        if self.pending_step is not None:
            record = self.step_registry[id(self.pending_step)]
            if record["stage"] != "prepared":
                raise ValueError("component step is already executing")
            for name, value in candidate.items():
                if name == "accepted":
                    assert value is record["candidate"][name]
                else:
                    _same(value, record["candidate"][name])
            return self.pending_step
        handle = PreparedVectorStep()
        self.step_registry[id(handle)] = {
            "handle": handle,
            "candidate": candidate,
            "tick": self.ledger.vector_ticks + 1,
            "stage": "prepared",
        }
        self.pending_step = handle
        return handle

    def claim_vector_step(self, *, prepared, accepted, world_ids, predecessor, actions, active_on_entry):
        self.check_current()
        record = self.step_registry.get(id(prepared))
        if record is None or record["handle"] is not prepared or prepared is not self.pending_step or record["stage"] != "prepared":
            raise ValueError("component step must be genuinely issued and single use")
        candidate = record["candidate"]
        if accepted is not self.accepted or accepted is not candidate["accepted"] or world_ids != self.accepted.world_ids:
            raise ValueError("component step accepted identity/binding changed")
        if record["tick"] != self.ledger.vector_ticks + 1:
            raise ValueError("component lifetime tick changed")
        for name, value in (("predecessor", predecessor), ("actions", actions), ("active_on_entry", active_on_entry)):
            expected = candidate[name]
            if (value.dtype, value.device, value.shape) != (expected.dtype, expected.device, expected.shape) or not torch.equal(
                value, expected
            ):
                raise ValueError("component issued step content changed")
        record["stage"] = "executing"
        self.step_started = True
        return record["tick"]

    def step(self):
        from townlet.training.state import RewardTensor

        self.check_current()
        masks = self.env.get_action_masks()
        assert bool(masks[~self.completed_lanes].any(dim=1).all())
        actions = masks.to(torch.int64).argmax(dim=1)
        prepared = self.prepare_step(actions)
        predecessor = self._reading.clone()
        try:
            observations, rewards, dones, info = self.env.step(actions, vector_step=prepared)
            active = info["active_on_entry"]
            expected_counts = self._counts + active.to(torch.long)
            _same(info["step_counts"], expected_counts)
            self.ledger = self.ledger.advance(vector_ticks=1, eligible_transitions=int(active.sum()))
            components = info["reward_components"]
            if bool(active.any()):
                self.replay.push_recorded(
                    predecessor[active],
                    actions[active],
                    RewardTensor.from_dac(
                        rewards[active],
                        extrinsic=components["extrinsic"][active],
                        intrinsic=components["intrinsic"][active],
                        shaping=components["shaping"][active],
                    ),
                    observations[active],
                    dones[active],
                    info["successor_action_masks"][active],
                )
            handoff = info["intrinsic_transition"]
            receipts = self.runtime.admit_and_service(context=handoff.context, stamp=handoff.stamp, accepted=handoff.accepted)
            self.ledger = self.ledger.advance(
                predictor_admitted_rows=sum(item.admitted_rows for item in receipts),
                predictor_consumed_minibatches=sum(item.optimizer_updates for item in receipts),
                predictor_dropped_rows=sum(item.dropped_rows for item in receipts),
            )
            self.current_obs = observations.detach().clone()
            self.current_masks = info["successor_action_masks"].detach().clone()
            self.completed_lanes = dones.detach().clone()
            self.counts = expected_counts
            self._reading = self.current_obs.clone()
            self._counts = expected_counts.clone()
            self.reward_totals["total"] += rewards
            for name in ("extrinsic", "intrinsic", "shaping"):
                self.reward_totals[name] += components[name]
            self.step_registry[id(prepared)]["stage"] = "completed"
            self.pending_step = None
            self.last_transition = (predecessor, actions.clone(), observations.detach().clone(), rewards.detach().clone(), info)
            self.last_service = receipts
            info["component_selection_epsilons"] = self.current_epsilons
            return observations, rewards, dones, info, receipts
        except BaseException:
            self.env.abandon_episode(accepted=self.accepted, reason="runtime_failure")
            raise

    def prepare_empty_episode_evidence(self, *, accepted):
        if accepted is not self.accepted or self.activation_receipt is None or self.step_started:
            raise ValueError("component empty evidence requires actual zero-event activated custody")
        if not bool(self.completed_lanes.all()) or bool(self.env.step_counts.any()) or self.pending_step is not None:
            raise ValueError("component has participating work")
        return self.receipt("empty_episode", accepted=accepted, participated_world_ids=(), events=())

    def observed_outcomes(self, batch, participants):
        from townlet.training.episode import EpisodeCompletion, LaneOutcome, freeze_lane_outcome

        self.check_current()
        actual = tuple(wid for row, wid in enumerate(self.accepted.world_ids) if int(self._counts[row]) > 0)
        if batch != self.accepted.batch_episode or participants != actual or not actual or self.pending_step is not None:
            raise ValueError("component completion must match genuine positive participation")
        if bool((self._counts > self.episode_horizon).any()):
            raise ValueError("component exceeded its declared control horizon")
        outcomes = tuple(
            LaneOutcome(
                outcome=EpisodeCompletion(
                    agent_idx=row,
                    reason="cap",
                    survival_time=int(self._counts[row]),
                    final_observation=self.current_obs[row].detach().cpu().clone(),
                    final_meters=self.env.meters[row].detach().cpu().clone(),
                ),
                batch_episode=batch,
                planned_horizon=self.episode_horizon,
                reward_total=float(self.reward_totals["total"][row]),
                reward_extrinsic=float(self.reward_totals["extrinsic"][row]),
                reward_intrinsic=float(self.reward_totals["intrinsic"][row]),
                reward_shaping=float(self.reward_totals["shaping"][row]),
                policy_entropy=0.0,
                world_id=wid,
                world_episode_seq=self.accepted.world_episode_seqs[row],
            )
            for row, wid in enumerate(self.accepted.world_ids)
            if wid in actual
        )
        # The controller's actual deterministic legal-argmax policy ends at this
        # declared positive control cap; entropy0 is not Q-policy telemetry.
        content = tuple((item.payload.hex(), item.fingerprint) for item in map(freeze_lane_outcome, outcomes))
        return outcomes, content

    def prepare_close(self, batch, participants):
        outcomes, content = self.observed_outcomes(batch, participants)
        self.events[batch] = content
        self.outcomes[batch] = outcomes
        before = deepcopy(self.runtime.checkpoint_state())
        curriculum = self.curriculum.prepare_episode_outcomes(outcomes)
        bank = self.runtime.prepare_completion(
            accepted=self.accepted, boundary_key=batch, completion_content=content, outcomes=outcomes, participated_world_ids=participants
        )
        close = self.env.prepare_episode_close(
            accepted=self.accepted,
            boundary_key=batch,
            completion_content=content,
            participated_world_ids=participants,
            dispositions=bank.prepared_receipt,
        )
        context = {
            "curriculum": curriculum,
            "bank": bank,
            "close": close,
            "outcomes": outcomes,
            "before": before,
            "request": (self.accepted, batch, content),
            "committed": False,
            "dispositions": None,
        }
        self.close_contexts[batch] = context
        return close

    def close(self, batch, participants):
        if batch not in self.close_contexts:
            self.prepare_close(batch, participants)
        context = self.close_contexts[batch]
        if context["request"][0] is not self.accepted or participants != tuple(item.world_id for item in context["outcomes"]):
            raise ValueError("component close retry changed identity or participants")
        prepared = context["close"]
        self.env.freeze_episode_close(prepared)
        if not context["committed"]:
            self.curriculum.commit_prepared_episode_outcomes(context["curriculum"])
            context["dispositions"] = self.runtime.commit_completion(prepared=context["bank"])
            self.completion_request = context["request"]
            self.runtime.commit_batch_episode(batch_episode=batch, outcomes=context["outcomes"])
            before = context["before"]["selector"]["epsilon"]
            after = max(self.policy.epsilon_end, before * self.policy.epsilon_decay)
            published = self.runtime.checkpoint_state()
            assert self.runtime.epsilon == published["selector"]["epsilon"] == after
            _same(
                published["cadence"]["last_committed"],
                {
                    "batch_episode": batch,
                    "completion_content": self.events[batch],
                    "epsilon_before": before,
                    "epsilon_after": after,
                },
            )
            self.runtime.commit_batch_episode(batch_episode=batch, outcomes=context["outcomes"])
            _same(self.runtime.checkpoint_state(), published)
            self.current_epsilons = self.runtime.epsilon_tensor(batch_size=self.env.num_agents, device=self.env.device)
            _same(self.current_epsilons, torch.full((self.env.num_agents,), after, dtype=torch.float32, device=self.env.device))
            self.committed_batches[batch] = self.events[batch]
            self.ledger = self.ledger.advance(completed_batch_episodes=1)
            self.component_commitment = {
                "batch_episode": batch,
                "completion_content": [list(pair) for pair in context["request"][2]],
                "epsilon_before": before,
                "epsilon_after": after,
            }
            context["committed"] = True
        receipt = context["dispositions"]
        closure = self.env.close_episode(prepared, dispositions=receipt)
        return prepared, closure, receipt

    def release_closed(self, batch, closure, dispositions):
        context = self.close_contexts[batch]
        if not context["committed"] or dispositions is not context["dispositions"] or dispositions is not closure.dispositions:
            raise ValueError("release requires actual completed component effects and BANK identity")
        fields = {
            name: self.role_receipt(role, name, accepted=self.accepted, boundary_key=batch, completion_content=self.events[batch])
            for name, role in (
                ("curriculum_receipt", "curriculum"),
                ("exploration_receipt", "exploration"),
                ("population_commit_receipt", "population"),
                ("epsilon_install_receipt", "exploration"),
                ("selection_sync_receipt", "selection"),
            )
        }
        effects = self.boundary.receipt(
            "boundary_effects",
            batch_episode=batch,
            accepted_identity=self.accepted,
            completion_content=self.events[batch],
            retirement_receipt=dispositions,
            **fields,
        )
        release = self.authority.completed(closure=closure, effects=effects)
        self.release = self.env.install_boundary_release(release)
        return effects

    def initial(self):
        states = {
            "population": {"component_vector_ticks": self.ledger.vector_ticks, "accepted": self.accepted},
            "curriculum": deepcopy(self.curriculum.checkpoint_state()),
            "exploration": deepcopy(self.runtime.checkpoint_state()),
            "network": deepcopy(self.q.state_dict()),
            "optimizer": deepcopy(self.optimizer.state_dict()),
            "scheduler": {"state": None if self.scheduler is None else deepcopy(self.scheduler.state_dict())},
            "replay": deepcopy(self.replay.serialize()),
            "selection": {"epsilon": self.runtime.epsilon, "diagnostic": self.current_epsilons.clone()},
        }
        owner_fields = {
            name: self.role_receipt(
                name,
                "initial_owner",
                state=states[name],
                role=name,
                semantic_execution_identity=self.env.semantic_execution_identity,
                bootstrap_first_batch=1,
                world_binding=self.env.world_ids,
            )
            for name in ("population", "curriculum", "exploration", "network", "optimizer", "scheduler", "replay", "selection")
        }
        owners = self.boundary.receipt(
            "initial_owners",
            semantic_execution_identity=self.env.semantic_execution_identity,
            bootstrap_first_batch=1,
            world_binding=self.env.world_ids,
            **owner_fields,
        )
        proof = self.authority.prepare_initial_snapshot(release=self.release, owners=owners)
        return self.env.checkpoint_world_state(
            kind="INITIAL",
            release=self.release,
            retained_binding_batches=(),
            initial=proof,
        )

    def completed(self, references):
        return self.env.checkpoint_world_state(
            kind="COMPLETED",
            release=self.release,
            retained_binding_batches=references,
            initial=None,
        )


def _restore(compiled, state, order, *, runtime_state, component_ledger, component_state, drive_intrinsic, training_input):
    run = _Run(_env(compiled, order), bootstrap=False, drive_intrinsic=drive_intrinsic, training_input=training_input)
    prepared = run.env.prepare_world_restore(
        kind=state["kind"],
        state=state,
        world_roster=_roster(),
        destination_world_ids=order,
        semantic_execution_identity=run.env.semantic_execution_identity,
    )
    # Only the actual runtime/BANK child and supplied real component ledger are
    # continued. Q/replay/curriculum remain newly initialized: no full D/T26 claim.
    boundary = run.boundary.receipt("restored_boundary", kind=state["kind"], state=deepcopy(state), prepared=prepared)
    mode = "initial" if state["kind"] == "INITIAL" else "completed_boundary"
    run.restore_context = {
        "prepared": prepared,
        "boundary": boundary,
        "mode": mode,
        "runtime": deepcopy(runtime_state),
        "component": deepcopy(component_state),
        "ledger": component_ledger,
        "release": None,
    }
    child = run.runtime.prepare_restore(
        state=runtime_state, mode=mode, accepted=None, parent_restore=prepared, validate_parent_restore=run.validate_parent_restore
    )
    run.runtime.install_restore(prepared=child)
    run.ledger = component_ledger
    run.component_commitment = run.restore_context["component"]["last_committed"]
    run.current_epsilons = run.runtime.epsilon_tensor(batch_size=run.env.num_agents, device=run.env.device)
    release = run.restore_context["release"]
    assert release is not None
    run.release = run.env.install_world_restore(prepared=prepared, release=release)
    assert run.env.install_world_restore(prepared=prepared, release=release) is run.release
    return run


def test_declared_roster_owned_exact_serialization():
    from townlet.config.world_roster import WorldRosterDeclaration

    payload = {"schema": "world-roster-v1", "world_ids": list(IDS)}
    roster = WorldRosterDeclaration.from_dict(payload)
    payload["world_ids"].reverse()
    assert roster.world_ids == IDS
    exported = roster.to_dict()
    exported["world_ids"].clear()
    assert roster.to_dict() == {"schema": "world-roster-v1", "world_ids": list(IDS)}
    with pytest.raises((AttributeError, TypeError)):
        roster.world_ids = tuple(reversed(IDS))


@pytest.mark.parametrize("ids", [[], [""], ["x", "x"], [True, "x"], "not-an-array"])
def test_roster_invalid_ids_refuse(ids):
    from townlet.config.world_roster import WorldRosterDeclaration

    with pytest.raises((TypeError, ValueError)):
        WorldRosterDeclaration.from_dict({"schema": "world-roster-v1", "world_ids": ids})


@pytest.mark.parametrize("change", ["missing", "old_schema", "extra"])
def test_roster_exact_schema(change):
    from townlet.config.world_roster import WorldRosterDeclaration

    payload = {"schema": "world-roster-v1", "world_ids": list(IDS)}
    if change == "missing":
        del payload["world_ids"]
    elif change == "old_schema":
        payload["schema"] = "world-roster-v0"
    else:
        payload["row_names"] = list(IDS)
    with pytest.raises((TypeError, ValueError)):
        WorldRosterDeclaration.from_dict(payload)


@pytest.mark.parametrize("order", [(IDS[0],), (IDS[0], IDS[0]), (IDS[0], "foreign")])
def test_invalid_binding_precedes_constructor_randomness(compiled, monkeypatch, order):
    from townlet.environment.vectorized_env import VectorizedHamletEnv

    def forbidden(*args, **kwargs):
        pytest.fail("invalid constructor binding reached random layout")

    monkeypatch.setattr(VectorizedHamletEnv, "randomize_affordance_positions", forbidden)
    before = torch.get_rng_state().clone()
    with pytest.raises((TypeError, ValueError)):
        _env(compiled, order)
    assert torch.equal(before, torch.get_rng_state())


def test_real_env_requires_explicit_roster_seed_binding(compiled):
    from townlet.environment.vectorized_env import VectorizedHamletEnv

    with pytest.raises(TypeError):
        VectorizedHamletEnv(universe=compiled, level_name="L0_test", num_agents=2, device="cpu")
    env = _env(compiled)
    assert env.world_ids == IDS
    assert dict(env.accepted_episode_seqs) == dict.fromkeys(IDS, 0)


def test_reservation_and_failed_preflight_are_pure(compiled):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    before = _state(run.env)
    first = run.env.prepare_episode(batch_episode=1, release=run.release)
    second = run.env.prepare_episode(batch_episode=1, release=run.release)
    assert first.world_ids == second.world_ids == IDS
    assert first.world_episode_seqs == second.world_episode_seqs == (1, 1)
    foreign = _Run(_env(compiled), **_baseline_inputs(compiled))
    foreign_reservation = foreign.env.prepare_episode(batch_episode=1, release=foreign.release)
    before = _state(run.env)
    with pytest.raises(ValueError):
        run.env.validate_episode_reservation(foreign_reservation)
    _same(before, _state(run.env))
    run.env.validate_episode_reservation(first)
    _same(before, _state(run.env))


def test_authority_bootstrap_binding_and_consumption(compiled):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    assert run.env.bind_boundary_authority(owner=run.boundary, role_owners=run.roles) is run.authority
    before = _state(run.env)
    with pytest.raises(ValueError):
        run.env.bind_boundary_authority(owner=_Sink(), role_owners=run.roles)
    _same(before, _state(run.env))
    reservation, reset = run.reset(1, retired_world_ids=())
    assert reset.accepted.world_episode_seqs == (1, 1)
    with pytest.raises(ValueError):
        run.authority.bootstrap(first_batch_episode=1)
    with pytest.raises(ValueError):
        run.env.prepare_episode(batch_episode=2, release=run.release)
    assert run.env.reset(reservation=reservation) is reset


def test_reset_retry_after_rollout_owns_original_observation(compiled, monkeypatch):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    calls = []
    original = run.env._get_observations

    def observed():
        calls.append(1)
        return original()

    monkeypatch.setattr(run.env, "_get_observations", observed)
    reservation, receipt = run.reset(1, retired_world_ids=())
    initial = receipt.observation.clone()
    receipt.observation.fill_(1234)
    _same(initial, receipt.observation)
    run.step()
    before = _state(run.env)
    count = len(calls)
    assert run.env.reset(reservation=reservation) is receipt
    assert len(calls) == count
    _same(before, _state(run.env))
    _same(initial, receipt.observation)


def test_activation_requires_owned_matching_receipts(compiled):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    reservation = run.env.prepare_episode(batch_episode=1, release=run.release)
    reset = run.env.reset(reservation=reservation)
    accepted = reset.accepted
    run.adopt_reset(reservation, reset, retired_world_ids=())
    before = _state(run.env)
    with pytest.raises((TypeError, ValueError)):
        run.env.activate_episode(
            accepted=accepted,
            population_receipt=SimpleNamespace(accepted=accepted),
            curiosity_receipt=run.runtime.begin_episode(accepted=accepted),
        )
    _same(before, _state(run.env))
    population = run.population.activation(accepted)
    curiosity = run.runtime.begin_episode(accepted=accepted)
    activation = run.env.activate_episode(accepted=accepted, population_receipt=population, curiosity_receipt=curiosity)
    assert run.env.activate_episode(accepted=accepted, population_receipt=population, curiosity_receipt=curiosity) is activation


def test_late_reset_failure_quarantines_without_false_rollback(compiled, monkeypatch):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    reservation = run.env.prepare_episode(batch_episode=1, release=run.release)

    def fail_late():
        raise RuntimeError("injected late encoding failure")

    monkeypatch.setattr(run.env, "_get_observations", fail_late)
    with pytest.raises(RuntimeError, match="late encoding"):
        run.env.reset(reservation=reservation)
    assert run.env.world_phase == "quarantined"
    assert dict(run.env.accepted_episode_seqs) == dict.fromkeys(IDS, 0)
    with pytest.raises((ValueError, RuntimeError)):
        run.env.reset(reservation=reservation)
    with pytest.raises((ValueError, RuntimeError)):
        run.env.step(torch.zeros(2, dtype=torch.long), vector_step=_unissued_step())
    with pytest.raises((ValueError, RuntimeError)):
        run.initial()
    # No assertion of simulator or RNG rollback: reconstruction is the recovery.
    fresh = _Run(_env(compiled), **_baseline_inputs(compiled))
    assert fresh.reset(1, retired_world_ids=())[1].accepted.world_episode_seqs == (1, 1)


def test_close_alone_blocks_save_next_release_is_save_independent(compiled):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    run.reset(1, retired_world_ids=())
    run.step()
    prepared, closure, dispositions = run.close(1, run.env.world_ids)
    before = _state(run.env)
    assert run.env.close_episode(prepared, dispositions=dispositions) is closure
    _same(before, _state(run.env))
    with pytest.raises(ValueError):
        run.completed((1,))
    with pytest.raises(ValueError):
        run.env.prepare_episode(batch_episode=2, release=run.release)
    run.release_closed(1, closure, dispositions)
    assert run.env.install_boundary_release(run.release) is run.release
    # No checkpoint call between release and the next successful reset.
    assert run.reset(2, retired_world_ids=())[1].accepted.world_episode_seqs == (2, 2)


def test_wrong_release_and_changed_disposition_are_pure(compiled):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    foreign = _Run(_env(compiled), **_baseline_inputs(compiled))
    before = _state(run.env)
    with pytest.raises(ValueError):
        run.env.install_boundary_release(foreign.release)
    _same(before, _state(run.env))
    run.reset(1, retired_world_ids=(IDS[1],))
    run.step()
    prepared, closure, dispositions = run.close(1, (IDS[0],))
    before = _state(run.env)
    forged = replace(run.role_receipt("curiosity", "prepared_dispositions", **dispositions.payload))
    with pytest.raises((TypeError, ValueError)):
        run.env.prepare_episode_close(
            accepted=run.accepted,
            boundary_key=1,
            completion_content=run.events[1],
            participated_world_ids=(IDS[0],),
            dispositions=forged,
        )
    _same(before, _state(run.env))
    assert run.env.close_episode(prepared, dispositions=dispositions) is closure


def test_empty_abandon_is_not_completion_or_initial(compiled):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    run.reset(1, retired_world_ids=IDS)
    abandoned = run.env.abandon_episode(accepted=run.accepted, reason="empty_participation")
    assert run.env.abandon_episode(accepted=run.accepted, reason="empty_participation") is abandoned
    assert run.env.world_phase == "quarantined"
    assert dict(run.env.accepted_episode_seqs) == dict.fromkeys(IDS, 1)
    with pytest.raises(ValueError):
        run.completed(())
    with pytest.raises(ValueError):
        run.initial()
    with pytest.raises(ValueError):
        run.env.prepare_episode(batch_episode=2, release=run.release)


def test_participating_episode_cannot_claim_empty_abandon(compiled):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    run.reset(1, retired_world_ids=(IDS[1],))
    run.step()
    before = _state(run.env)
    with pytest.raises(ValueError):
        run.env.abandon_episode(accepted=run.accepted, reason="empty_participation")
    _same(before, _state(run.env))


def test_initial_snapshot_repeat_restore_and_first_real_reset(compiled):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    before = _state(run.env)
    state = run.initial()
    _same(state, run.initial())
    _same(before, _state(run.env))
    assert state["schema"] == "world-lifecycle-v4" and state["kind"] == "INITIAL"
    assert state["vfs_random_context"] == {
        "schema": "vfs-world-random-v1",
        "domain": "townlet.simulator.vfs.world-draw.v1",
        "training_seed": SEED,
        "world_ids": list(IDS),
        "world_episode_seqs": [0, 0],
    }
    assert state["accepted_bindings"] == []
    assert state["last_closed_episode"] is None and state["completed_boundary_key"] is None
    assert state["saved_lane_binding"] is None
    assert state["accepted_episode_seqs"] == dict.fromkeys(IDS, 0)
    restored = _restore(
        compiled,
        state,
        tuple(reversed(IDS)),
        runtime_state=run.runtime.checkpoint_state(),
        component_ledger=run.ledger,
        component_state=run.component_state(),
        **_baseline_inputs(compiled),
    )
    assert restored.env.world_phase == "bootstrap-ready"
    assert restored.reset(1, retired_world_ids=())[1].accepted.world_episode_seqs == (1, 1)
    with pytest.raises(ValueError):
        restored.initial()
    restored.step()
    _, closure, dispositions = restored.close(1, restored.env.world_ids)
    restored.release_closed(1, closure, dispositions)
    assert restored.completed((1,))["kind"] == "COMPLETED"


@pytest.mark.parametrize(
    "field,value",
    [
        ("kind", "UNKNOWN"),
        ("schema", "world-lifecycle-v2"),
        ("completed_boundary_key", 0),
        ("last_closed_episode", {}),
        ("accepted_episode_seqs", {IDS[0]: 0, IDS[1]: 1}),
        ("next_batch_episode", True),
    ],
)
def test_malformed_initial_restore_is_pure(compiled, field, value):
    state = _Run(_env(compiled), **_baseline_inputs(compiled)).initial()
    state[field] = value
    target = _Run(_env(compiled), bootstrap=False, **_baseline_inputs(compiled))
    before = _state(target.env)
    with pytest.raises((TypeError, ValueError)):
        target.env.prepare_world_restore(
            kind="INITIAL",
            state=state,
            world_roster=_roster(),
            destination_world_ids=IDS,
            semantic_execution_identity=target.env.semantic_execution_identity,
        )
    _same(before, _state(target.env))
    if field == "schema":
        state["schema"] = "world-lifecycle-v3"
        with pytest.raises((TypeError, ValueError)):
            target.env.prepare_world_restore(
                kind="INITIAL",
                state=state,
                world_roster=_roster(),
                destination_world_ids=IDS,
                semantic_execution_identity=target.env.semantic_execution_identity,
            )
        _same(before, _state(target.env))


def test_initial_restore_over_live_boundary_refuses(compiled):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    state = run.initial()
    run.reset(1, retired_world_ids=())
    before = _state(run.env)
    with pytest.raises(ValueError):
        run.env.prepare_world_restore(
            kind="INITIAL",
            state=state,
            world_roster=_roster(),
            destination_world_ids=IDS,
            semantic_execution_identity=run.env.semantic_execution_identity,
        )
    _same(before, _state(run.env))


def test_two_boundaries_two_reorders_keep_historical_binding_verbatim(compiled):
    first = _Run(_env(compiled), **_baseline_inputs(compiled))
    first.reset(1, retired_world_ids=())
    first.step()
    _, closure, dispositions = first.close(1, first.env.world_ids)
    first.release_closed(1, closure, dispositions)
    saved1 = first.completed((1,))
    old_outcomes = deepcopy(first.outcomes[1])
    second = _restore(
        compiled,
        saved1,
        tuple(reversed(IDS)),
        runtime_state=first.runtime.checkpoint_state(),
        component_ledger=first.ledger,
        component_state=first.component_state(),
        **_baseline_inputs(compiled),
    )
    assert dict(second.env.accepted_episode_seqs) == dict.fromkeys(IDS, 1)
    assert second.reset(2, retired_world_ids=(IDS[1],))[1].accepted.world_ids == tuple(reversed(IDS))
    second.step()
    _, closure, dispositions = second.close(2, (IDS[0],))
    second.release_closed(2, closure, dispositions)
    saved2 = second.completed((1, 2))
    assert saved2["vfs_random_context"]["training_seed"] == SEED
    assert saved2["vfs_random_context"]["world_ids"] == list(reversed(IDS))
    assert saved2["vfs_random_context"]["world_episode_seqs"] == [2, 2]
    assert saved2["accepted_bindings"] == [
        {"batch_episode": 1, "world_ids": list(IDS), "world_episode_seqs": [1, 1]},
        {"batch_episode": 2, "world_ids": list(reversed(IDS)), "world_episode_seqs": [2, 2]},
    ]
    third = _restore(
        compiled,
        saved2,
        IDS,
        runtime_state=second.runtime.checkpoint_state(),
        component_ledger=second.ledger,
        component_state=second.component_state(),
        **_baseline_inputs(compiled),
    )
    restored_bindings = third.completed((1, 2))["accepted_bindings"]
    _same(saved2["accepted_bindings"], restored_bindings)
    by_batch = {binding["batch_episode"]: binding for binding in restored_bindings}
    for event in old_outcomes + second.outcomes[2]:
        assert by_batch[event.batch_episode]["world_ids"][event.outcome.agent_idx] == event.world_id
        assert by_batch[event.batch_episode]["world_episode_seqs"][event.outcome.agent_idx] == event.world_episode_seq
    next_receipt = third.reset(3, retired_world_ids=())[1].accepted
    assert next_receipt.world_ids == IDS and next_receipt.world_episode_seqs == (3, 3)
    # No unequal-cursor fixture is passed off as reachable native history.


@pytest.mark.parametrize("damage", ["missing_latest", "duplicate_batch", "wrong_latest", "foreign_world", "bool_sequence"])
def test_completed_binding_corruption_refuses_before_install(compiled, damage):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    for batch in (1, 2):
        run.reset(batch, retired_world_ids=())
        run.step()
        _, closure, dispositions = run.close(batch, run.env.world_ids)
        run.release_closed(batch, closure, dispositions)
    state = run.completed((1, 2))
    if damage == "missing_latest":
        state["accepted_bindings"].pop()
    elif damage == "duplicate_batch":
        state["accepted_bindings"].append(deepcopy(state["accepted_bindings"][0]))
    elif damage == "wrong_latest":
        state["accepted_bindings"][-1]["world_ids"].reverse()
    elif damage == "foreign_world":
        state["accepted_bindings"][0]["world_ids"][0] = "foreign"
    else:
        state["accepted_bindings"][0]["world_episode_seqs"][1] = True
    target = _Run(_env(compiled), bootstrap=False, **_baseline_inputs(compiled))
    before = _state(target.env)
    with pytest.raises((ValueError, TypeError)):
        target.env.prepare_world_restore(
            kind="COMPLETED",
            state=state,
            world_roster=_roster(),
            destination_world_ids=IDS,
            semantic_execution_identity=target.env.semantic_execution_identity,
        )
    _same(before, _state(target.env))


def test_step_before_activation_and_changed_reservation_refuse(compiled):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    reservation = run.env.prepare_episode(batch_episode=1, release=run.release)
    run.env.reset(reservation=reservation)
    before = _state(run.env)
    with pytest.raises(ValueError):
        run.env.step(torch.zeros(2, dtype=torch.long), vector_step=_unissued_step())
    with pytest.raises(ValueError):
        run.env.reset(reservation=replace(reservation, world_episode_seqs=(2, 2)))
    _same(before, _state(run.env))


def test_empty_close_and_unknown_history_reference_refuse(compiled):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    run.reset(1, retired_world_ids=())
    before = _state(run.env)
    with pytest.raises(ValueError):
        run.close(1, ())
    _same(before, _state(run.env))
    run.step()
    _, closure, dispositions = run.close(1, run.env.world_ids)
    run.release_closed(1, closure, dispositions)
    before = _state(run.env)
    with pytest.raises(ValueError):
        run.completed((1, 12))
    _same(before, _state(run.env))


def test_initial_schema_exact_and_snapshot_isolation(compiled):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    state = run.initial()
    assert set(state) == {
        "schema",
        "kind",
        "next_batch_episode",
        "world_roster",
        "manifest_digest",
        "roster_semantic_identity",
        "training_seed",
        "execution_identity",
        "saved_lane_binding",
        "destination_lane_binding",
        "accepted_episode_seqs",
        "last_closed_episode",
        "completed_boundary_key",
        "accepted_bindings",
        "vfs_random_context",
    }
    state["world_roster"]["world_ids"].clear()
    state["accepted_episode_seqs"][IDS[0]] = 99
    state["vfs_random_context"]["world_ids"].clear()
    state["vfs_random_context"]["world_episode_seqs"][0] = 99
    assert run.initial()["world_roster"]["world_ids"] == list(IDS)
    assert run.initial()["accepted_episode_seqs"] == dict.fromkeys(IDS, 0)
    assert run.initial()["vfs_random_context"]["world_ids"] == list(IDS)
    assert run.initial()["vfs_random_context"]["world_episode_seqs"] == [0, 0]


@pytest.mark.parametrize("mode", ["wrong_kind", "extra_key", "changed_manifest", "wrong_seed", "unknown_member"])
def test_restore_identity_and_kind_mismatch_refuse(compiled, mode):
    state = _Run(_env(compiled), **_baseline_inputs(compiled)).initial()
    target = _Run(_env(compiled), bootstrap=False, **_baseline_inputs(compiled))
    kind, order = "INITIAL", IDS
    if mode == "wrong_kind":
        kind = "COMPLETED"
    elif mode == "extra_key":
        state["legacy_episode"] = 0
    elif mode == "changed_manifest":
        state["world_roster"]["world_ids"].reverse()
    elif mode == "wrong_seed":
        state["training_seed"] += 1
    else:
        order = (IDS[0], "foreign")
    before = _state(target.env)
    with pytest.raises((ValueError, TypeError)):
        target.env.prepare_world_restore(
            kind=kind,
            state=state,
            world_roster=_roster(),
            destination_world_ids=order,
            semantic_execution_identity=target.env.semantic_execution_identity,
        )
    _same(before, _state(target.env))


def test_foreign_boundary_effect_receipt_cannot_release(compiled):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    run.reset(1, retired_world_ids=())
    run.step()
    _, closure, dispositions = run.close(1, run.env.world_ids)
    foreign = _Sink().receipt(
        "boundary_effects",
        batch_episode=1,
        accepted_identity=run.accepted,
        completion_content=run.events[1],
        retirement_receipt=dispositions,
    )
    before = _state(run.env)
    with pytest.raises((ValueError, TypeError)):
        run.authority.completed(closure=closure, effects=foreign)
    with pytest.raises(ValueError):
        run.initial()
    _same(before, _state(run.env))


@pytest.mark.parametrize(
    "field,value", [("batch_episode", True), ("batch_episode", 1.0), ("world_episode_seqs", [True, 1]), ("world_episode_seqs", [1.0, 1])]
)
def test_last_closure_numeric_alias_refuses(compiled, field, value):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    run.reset(1, retired_world_ids=())
    run.step()
    _, closure, dispositions = run.close(1, run.env.world_ids)
    run.release_closed(1, closure, dispositions)
    state = run.completed((1,))
    state["last_closed_episode"][field] = value
    target = _Run(_env(compiled), bootstrap=False, **_baseline_inputs(compiled))
    before = _state(target.env)
    with pytest.raises(ValueError):
        target.env.prepare_world_restore(
            kind="COMPLETED",
            state=state,
            world_roster=_roster(),
            destination_world_ids=IDS,
            semantic_execution_identity=target.env.semantic_execution_identity,
        )
    _same(before, _state(target.env))


@pytest.mark.parametrize("damage", ["foreign_effect", "wrong_content", "foreign_initial"])
def test_bound_outer_proof_rejects_wrong_child(compiled, monkeypatch, damage):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    issuer = run.boundary if damage == "foreign_initial" else run.population
    original = issuer.receipt
    foreign = _Sink()

    def altered(kind, **payload):
        if kind == "population_commit_receipt":
            if damage == "foreign_effect":
                return foreign.receipt(kind, **payload)
            if damage == "wrong_content":
                payload["completion_content"] = (("changed-same-boundary",),)
        if kind == "initial_owner" and damage == "foreign_initial":
            return foreign.receipt(kind, **payload)
        return original(kind, **payload)

    monkeypatch.setattr(issuer, "receipt", altered)
    if damage == "foreign_initial":
        before = _state(run.env)
        with pytest.raises(ValueError):
            run.initial()
    else:
        run.reset(1, retired_world_ids=())
        run.step()
        _, closure, dispositions = run.close(1, run.env.world_ids)
        before = _state(run.env)
        with pytest.raises(ValueError):
            run.release_closed(1, closure, dispositions)
    _same(before, _state(run.env))


def test_prepared_close_refuses_intervening_rollout(compiled):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    run.control_horizon = 2  # Genuine further A rollout is within the declared cap.
    run.reset(1, retired_world_ids=(IDS[1],))
    run.step()
    content = ((1, 0, IDS[0], 1, "interface-stale-preparation"),)
    # This negative isolates ENV's revision pin. A real BANK preparation blocks
    # further stepping; this local issuer-unit evidence cannot settle/release.
    dispositions = run.role_receipt(
        "curiosity",
        "prepared_dispositions",
        accepted=run.accepted,
        boundary_key=1,
        completion_content=content,
        participated_world_ids=(IDS[0],),
        dispositions=((IDS[0], "completed"), (IDS[1], "retired_nonparticipating")),
    )
    prepared = run.env.prepare_episode_close(
        accepted=run.accepted, boundary_key=1, completion_content=content, participated_world_ids=(IDS[0],), dispositions=dispositions
    )
    run.step()
    assert run.env.step_counts.tolist() == [2, 0]
    before = _state(run.env)
    with pytest.raises(ValueError):
        run.env.freeze_episode_close(prepared)
    _same(before, _state(run.env))


def test_closure_installed_before_acknowledgement_retries_once(compiled, monkeypatch):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    run.reset(1, retired_world_ids=())
    run.step()
    original = run.env.close_episode
    captured = []

    def interrupted(prepared, **kwargs):
        assert run.env.world_phase == "boundary-pending"
        frozen = _state(run.env)
        with pytest.raises(ValueError):
            run.env.step(torch.zeros(2, dtype=torch.long), vector_step=_unissued_step())
        assert run.env.freeze_episode_close(prepared) is prepared
        _same(frozen, _state(run.env))
        closure = original(prepared, **kwargs)
        captured.append((prepared, kwargs, closure))
        raise RuntimeError("after closure installation")

    monkeypatch.setattr(run.env, "close_episode", interrupted)
    with pytest.raises(RuntimeError, match="after closure installation"):
        run.close(1, run.env.world_ids)
    prepared, kwargs, closure = captured[0]
    before = _state(run.env)
    assert run.env.freeze_episode_close(prepared) is prepared
    assert original(prepared, **kwargs) is closure
    _same(before, _state(run.env))
    assert run.env.world_phase == "closed-awaiting-release"
    run.release_closed(1, closure, closure.dispositions)
    assert run.reset(2, retired_world_ids=())[1].accepted.world_episode_seqs == (2, 2)


def test_component_two_cycles_capture_replay_then_single_service_and_earned_effects(compiled, monkeypatch):
    """Missing replay, duplicate reward/service, toy effects or episode-clock reuse fail here."""
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    assert run.roles["network"] is run.q and run.roles["optimizer"] is run.optimizer
    assert run.roles["replay"] is run.replay and run.roles["curriculum"] is run.curriculum
    assert run.roles["curiosity"] is run.bank and run.bank_issuer.owner is run.bank
    assert run.roles["exploration"] is run.roles["selection"] is run.runtime
    assert set(run.roles) == set("population curiosity curriculum exploration network optimizer scheduler replay selection".split())
    calls = []
    reward, push, service = run.runtime.reward, run.replay.push_recorded, run.runtime.admit_and_service

    def observed_reward(**kwargs):
        result = reward(**kwargs)
        calls.append(("reward", kwargs))
        return result

    def observed_push(observations, actions, rewards, next_observations, dones, next_action_masks):
        result = push(observations, actions, rewards, next_observations, dones, next_action_masks)
        calls.append(
            (
                "replay",
                (observations.clone(), actions.clone(), rewards, next_observations.clone(), dones.clone(), next_action_masks.clone()),
            )
        )
        return result

    def observed_service(**kwargs):
        assert calls[-1][0] == "replay"
        result = service(**kwargs)
        calls.append(("service", kwargs))
        return result

    monkeypatch.setattr(run.runtime, "reward", observed_reward)
    monkeypatch.setattr(run.replay, "push_recorded", observed_push)
    monkeypatch.setattr(run.runtime, "admit_and_service", observed_service)
    for batch, retired, eligible_total in ((1, (IDS[1],), 1), (2, (), 3)):
        reservation, reset = run.reset(batch, retired_world_ids=retired)
        assert reset.accepted.world_episode_seqs == (batch, batch)
        assert run.env.global_tick == 0 and run.ledger.vector_ticks == batch - 1
        predecessor = run.current_obs.clone()
        observation, total, dones, info, _ = run.step()
        active = info["active_on_entry"]
        _same(active, torch.tensor([wid not in retired for wid in IDS]))
        _same(info["step_counts"], active.to(torch.long))
        assert run.env.global_tick == 1 and run.ledger.vector_ticks == batch
        assert run.ledger.eligible_transitions == eligible_total == run.replay.retained_transitions
        assert run.ledger.optimizer_updates == 0  # Real optimizer constructed; no invented learner update.
        _same(info["component_selection_epsilons"], run.runtime.epsilon_tensor(batch_size=run.env.num_agents, device=run.env.device))
        assert [name for name, _ in calls[-3:]] == ["reward", "replay", "service"]
        reward_call, captured, service_call = (item[1] for item in calls[-3:])
        handoff = info["intrinsic_transition"]
        for forwarded in (reward_call, service_call):
            assert forwarded["context"] is handoff.context and forwarded["stamp"] is handoff.stamp
            assert forwarded["accepted"] is reset.accepted
        assert handoff.context.vector_tick == batch
        _same(captured[0], predecessor[active])
        _same(captured[2].total, total[active])
        for name in ("extrinsic", "intrinsic", "shaping"):
            _same(getattr(captured[2], name), info["reward_components"][name][active])
        _same(captured[3], observation[active])
        _same(captured[4], dones[active])
        _same(captured[5], info["successor_action_masks"][active])
        assert run.env.reset(reservation=reservation) is reset
        participants = tuple(wid for wid in IDS if wid not in retired)
        before = run.runtime.epsilon
        _, closure, dispositions = run.close(batch, participants)
        assert tuple(item.world_id for item in run.outcomes[batch]) == participants
        assert dict(dispositions.dispositions) == {wid: "retired_nonparticipating" if wid in retired else "completed" for wid in IDS}
        assert run.runtime.epsilon == max(run.policy.epsilon_end, before * run.policy.epsilon_decay)
        effects = run.release_closed(batch, closure, dispositions)
        assert effects.payload["retirement_receipt"] is closure.dispositions
        assert run.ledger.completed_batch_episodes == batch and len(calls) == batch * 3
    assert run.completed((1, 2))["accepted_bindings"][-1]["world_episode_seqs"] == [2, 2]
    assert set(run.committed_batches) == {1, 2}


@pytest.mark.parametrize("damage", ["constructed", "copied", "foreign", "changed_actions", "reused"])
def test_component_step_registry_authenticates_identity_content_and_single_use(compiled, damage):
    from copy import copy

    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    run.reset(1, retired_world_ids=(IDS[1],))
    actions = run.env.get_action_masks().to(torch.long).argmax(dim=1)
    issued = run.prepare_step(actions)
    assert run.prepare_step(actions.clone()) is issued
    candidate = issued
    if damage == "constructed":
        candidate = _unissued_step()
    elif damage == "copied":
        candidate = copy(issued)
    elif damage == "foreign":
        other = _Run(_env(compiled), **_baseline_inputs(compiled))
        other.reset(1, retired_world_ids=(IDS[1],))
        candidate = other.prepare_step(actions)
    elif damage == "changed_actions":
        actions = (actions + 1) % run.env.action_dim
    else:
        run.step()
    before, ledger, replay = _state(run.env), run.ledger, deepcopy(run.replay.serialize())
    with pytest.raises(ValueError):
        run.env.step(actions, vector_step=candidate)
    _same(before, _state(run.env))
    assert run.ledger == ledger
    _same(run.replay.serialize(), replay)


def test_component_all_inactive_ordinary_step_is_separate_from_empty_abandonment(compiled):
    run = _Run(_env(compiled), **_baseline_inputs(compiled))
    run.reset(1, retired_world_ids=IDS)
    _, rewards, _, info, _ = run.step()
    _same(rewards, torch.zeros(2))
    _same(info["active_on_entry"], torch.tensor([False, False]))
    _same(info["step_counts"], torch.zeros(2, dtype=torch.long))
    assert run.env.global_tick == run.ledger.vector_ticks == 1
    assert run.ledger.eligible_transitions == run.replay.retained_transitions == 0
    assert run.env.world_phase == "active" and not run.outcomes and not run.committed_batches


@pytest.mark.parametrize(
    "damage", ["initial_cadence", "earlier_cadence", "zero_ledger", "earlier_ledger", "same_count_ledger", "initial_nonzero_ledger"]
)
def test_component_restore_rejects_unearned_cadence_or_ledger_before_publication(compiled, monkeypatch, damage):
    """A real matching BANK/world cannot authorize lost global work or wrong clock units."""
    source = _Run(_env(compiled), **_baseline_inputs(compiled))
    initial = source.initial()
    initial_runtime, zero_ledger = deepcopy(source.runtime.checkpoint_state()), source.ledger
    initial_component = source.component_state()
    captures = []
    for batch, retired in ((1, (IDS[1],)), (2, ())):
        source.reset(batch, retired_world_ids=retired)
        source.step()
        participants = tuple(wid for wid in IDS if wid not in retired)
        _, closure, dispositions = source.close(batch, participants)
        source.release_closed(batch, closure, dispositions)
        captures.append(
            (
                source.completed(tuple(range(1, batch + 1))),
                deepcopy(source.runtime.checkpoint_state()),
                source.ledger,
                source.component_state(),
            )
        )
    earlier, latest = captures
    assert earlier[2].vector_ticks == 1 and earlier[2].eligible_transitions == 1
    assert latest[2].vector_ticks == 2 and latest[2].eligible_transitions == 3
    assert latest[1]["cadence"]["last_committed"]["batch_episode"] == 2
    _same(latest[1]["cadence"]["last_committed"]["completion_content"], source.events[2])
    state, runtime_state, ledger, component = (
        (initial, initial_runtime, zero_ledger, initial_component) if damage == "initial_nonzero_ledger" else latest
    )
    # A real JSON transport proves this record does not depend on source objects.
    import json

    component = json.loads(json.dumps(component))
    # Earn the healthy native prepare/install and next-reset route before the
    # negative. Only separately supplied cadence/selector or ledger will change.
    healthy = _restore(
        compiled,
        state,
        tuple(reversed(IDS)),
        runtime_state=runtime_state,
        component_ledger=ledger,
        component_state=component,
        **_baseline_inputs(compiled),
    )
    continued = healthy.runtime.checkpoint_state()
    for field in ("selector", "cadence"):
        _same(continued[field], runtime_state[field])
    assert healthy.ledger == ledger
    next_batch = state["next_batch_episode"]
    expected_sequences = (1, 1) if state["kind"] == "INITIAL" else (3, 3)
    assert healthy.reset(next_batch, retired_world_ids=())[1].accepted.world_episode_seqs == expected_sequences
    candidate = deepcopy(runtime_state)
    if damage in ("initial_cadence", "earlier_cadence"):
        old_runtime = initial_runtime if damage == "initial_cadence" else earlier[1]
        for field in ("selector", "cadence"):
            candidate[field] = deepcopy(old_runtime[field])
        _same(candidate["bank"], latest[1]["bank"])
        assert candidate["cadence"] != latest[1]["cadence"]
    elif damage == "zero_ledger":
        ledger = zero_ledger
    elif damage == "earlier_ledger":
        ledger = earlier[2]
    elif damage == "same_count_ledger":
        other = _Run(_env(compiled), **_baseline_inputs(compiled))
        other.control_horizon = 2
        for batch in (1, 2):
            other.reset(batch, retired_world_ids=())
            other.step()
            if batch == 1:
                other.step()
            _, closure, dispositions = other.close(batch, IDS)
            other.release_closed(batch, closure, dispositions)
        ledger = other.ledger
        assert ledger.completed_batch_episodes == latest[2].completed_batch_episodes
        assert ledger.vector_ticks != latest[2].vector_ticks and ledger.eligible_transitions != latest[2].eligible_transitions
    else:
        ledger = latest[2]
    targets, preparations, installations = [], [], []
    original_init = _Run.__init__

    def observed_init(run, env, bootstrap=True, *, drive_intrinsic, training_input):
        original_init(run, env, bootstrap=bootstrap, drive_intrinsic=drive_intrinsic, training_input=training_input)
        targets.append((run, _state(env), run.ledger))
        prepare_world = env.prepare_world_restore
        install_child, install_world = run.runtime.install_restore, env.install_world_restore

        def observed_prepare(**kwargs):
            prepared = prepare_world(**kwargs)
            preparations.append(prepared)
            return prepared

        def observed_child(**kwargs):
            installations.append("runtime/BANK")
            return install_child(**kwargs)

        def observed_world(**kwargs):
            installations.append("world")
            return install_world(**kwargs)

        monkeypatch.setattr(env, "prepare_world_restore", observed_prepare)
        monkeypatch.setattr(run.runtime, "install_restore", observed_child)
        monkeypatch.setattr(env, "install_world_restore", observed_world)

    monkeypatch.setattr(_Run, "__init__", observed_init)
    try:
        with pytest.raises(ValueError):
            _restore(
                compiled,
                state,
                tuple(reversed(IDS)),
                runtime_state=candidate,
                component_ledger=ledger,
                component_state=component,
                **_baseline_inputs(compiled),
            )
    finally:
        assert len(targets) == len(preparations) == 1, "negative must reach genuine ENV restore preparation"
        assert installations == [], "mismatched continuation must refuse before runtime/BANK or world installation"
        target, before, original_ledger = targets[0]
        assert target.ledger is original_ledger
        assert target.env.world_phase == before["phase"]
        assert dict(target.env.accepted_episode_seqs) == before["cursors"]
        for name in ("positions", "meters", "dones"):
            _same(getattr(target.env, name), before[name])
        _same(target.env.step_counts, before["steps"])
