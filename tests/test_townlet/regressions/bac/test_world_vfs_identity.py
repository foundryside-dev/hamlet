"""Direct VFS identity proofs using genuine ENV/component transition owners.

World-only native attestations do not load learner children or qualify ambient
spawn/layout RNG, parent checkpoint installation or simulator independence.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pytest
import torch

from townlet.config.world_roster import WorldRosterDeclaration
from townlet.environment.vectorized_env import WorldReceiptIssuer
from townlet.universe.compiler import UniverseCompiler

DOMAIN = "townlet.simulator.vfs.world-draw.v1"
ROLES = ("population", "curiosity", "curriculum", "exploration", "network", "optimizer", "scheduler", "replay", "selection")
CLOCK_UNITS = (
    "vector_ticks",
    "eligible_transitions",
    "optimizer_updates",
    "completed_batch_episodes",
    "predictor_admitted_rows",
    "predictor_consumed_minibatches",
    "predictor_dropped_rows",
)


def assert_nested_equal(actual, expected):
    if isinstance(expected, torch.Tensor):
        assert (actual.shape, actual.dtype, actual.device) == (expected.shape, expected.dtype, expected.device)
        assert torch.equal(actual, expected)
    elif isinstance(expected, dict):
        assert actual.keys() == expected.keys()
        for key in expected:
            assert_nested_equal(actual[key], expected[key])
    elif isinstance(expected, (list, tuple)):
        assert type(actual) is type(expected) and len(actual) == len(expected)
        for value, reference in zip(actual, expected, strict=True):
            assert_nested_equal(value, reference)
    else:
        assert type(actual) is type(expected) and actual == expected


@pytest.fixture(scope="module")
def compiled():
    return UniverseCompiler().compile(Path("configs/test/token_set_smoke"), primary_level="L0_test", use_cache=False)


class LocalProducerOwners:
    """VFS's own component custody, independent of production POP/native load."""

    def __init__(self, compiled: Any, env: Any, roster: WorldRosterDeclaration, seed: int):
        from townlet.agent.network_factory import NetworkFactory
        from townlet.agent.optimizer_factory import OptimizerFactory
        from townlet.config.bac_options import resolve_bac_options
        from townlet.config.brain_config import apply_training_overrides
        from townlet.config.drive_as_code import IntrinsicStrategyConfig
        from townlet.config.exploration_policy import build_exploration, resolve_exploration_policy
        from townlet.config.training_v2_config import TrainingV2Config
        from townlet.curriculum.factory import build_curriculum
        from townlet.exploration.world_curiosity_state import WorldCuriosityDescriptor
        from townlet.training.clock_ledger import ClockLedger
        from townlet.training.replay_buffer import ReplayBuffer

        self.env, self.roster = env, roster
        data = compiled.get_level(env.level_name).training.model_dump()
        data["population"]["size"], data["seed"] = env.num_agents, seed
        training = TrainingV2Config.model_validate(data)
        options = resolve_bac_options(training.bac_options, training=training).options
        brain = apply_training_overrides(compiled.brain, training)
        assert brain.architecture.token_set is not None
        self.network = NetworkFactory.build_token_set(
            config=brain.architecture.token_set, action_dim=env.action_dim, token_spec=env.token_spec
        ).to(env.device)
        self.optimizer, self.scheduler = OptimizerFactory.build(config=brain.optimizer, parameters=self.network.parameters())
        self.replay = ReplayBuffer(capacity=brain.replay.capacity, device=env.device)
        self.curriculum = build_curriculum(
            training,
            curriculum_options=compiled.effective_run.options.curriculum,
            static_policy=compiled.effective_run.static_policy,
            device=env.device,
        )
        self.curriculum.initialize_population(env.num_agents)
        self.policy = resolve_exploration_policy(
            drive_intrinsic=IntrinsicStrategyConfig(strategy="none", base_weight=0.0, apply_modifiers=[]),
            training=training,
            options=options,
        )
        descriptor = WorldCuriosityDescriptor.from_policy(
            self.policy, world_ids=env.world_ids, observation_dim=env.observation_dim, action_dim=env.action_dim, training_seed=seed
        )
        self.bank = self.bank_issuer = None
        self.reports, self.committed = [], {}
        self.commit_request = None
        self.component_commitment = None
        self.runtime = build_exploration(
            policy=self.policy,
            descriptor=descriptor,
            device=env.device,
            validate_accepted_episode=env.validate_accepted_episode,
            issuer_factory=self.capture_bank,
            report_allocation=self.reports.append,
            validate_committed_batch=self.validate_commit,
            validate_parent_cadence=self.validate_parent_cadence,
        )
        assert self.bank is not None and self.bank is not self.runtime
        self.parent = WorldReceiptIssuer(owner=self)
        actual_owners = {
            "population": self,
            "curiosity": self.bank,
            "curriculum": self.curriculum,
            "exploration": self.runtime,
            "network": self.network,
            "optimizer": self.optimizer,
            "scheduler": self if self.scheduler is None else self.scheduler,
            "replay": self.replay,
            "selection": self.runtime,
        }
        # Declared initial cooperative issuer custody for the real owners.
        # No runtime effect producer is inferred from issuer_factory(BANK).
        self.roles = {role: WorldReceiptIssuer(owner=owner) for role, owner in actual_owners.items()}
        self.roles["population"], self.roles["curiosity"] = self.parent, self.bank_issuer
        self.ledger, self.revision = ClockLedger(), 0
        self.registry, self.pending = {}, None
        self.accepted = self.participation = self.activation = None
        self.restore_context = None
        self.current_epsilons = self.runtime.epsilon_tensor(batch_size=env.num_agents, device=env.device)
        self.control_horizon = 1  # Declared before reset: deterministic legal-argmax cap.
        env.set_exploration_runtime(exploration=self.runtime, claim_vector_step=self.claim)
        self.authority = env.bind_boundary_authority(owner=self, role_owners=actual_owners)

    def capture_bank(self, bank):
        if self.bank is not None:
            raise ValueError("VFS controller already owns a BANK")
        self.bank, self.bank_issuer = bank, WorldReceiptIssuer(owner=bank)
        return self.bank_issuer

    def validate_commit(self, *, batch_episode, outcomes):
        from townlet.training.episode import freeze_lane_outcome

        content = tuple((item.payload.hex(), item.fingerprint) for item in map(freeze_lane_outcome, outcomes))
        request = self.commit_request
        if request is None or request[0] is not self.accepted or request[1:] != (batch_episode, content):
            raise ValueError("VFS component has no matching canonical commitment")
        self.env.validate_accepted_episode(accepted=request[0])

    def validate_parent_cadence(self, *, cadence, mode, accepted, parent_restore):
        from townlet.training.clock_ledger import ClockLedger

        context = self.restore_context
        if context is None or mode != context["mode"] or accepted is not None or parent_restore is not context["prepared"]:
            raise ValueError("VFS runtime continuation requires actual retained ENV preparation")
        component = context["component"]
        if type(component) is not dict or set(component) != {"schema", "last_committed", "ledger"}:
            raise ValueError("VFS continuation requires its exact portable record")
        if component["schema"] != "world-component-continuation-v1":
            raise ValueError("unknown VFS component continuation schema")
        units = component["ledger"]
        if type(units) is not dict or set(units) != set(CLOCK_UNITS):
            raise ValueError("VFS continuation requires all seven clock units")
        earned_ledger = ClockLedger(**units)
        if type(context["ledger"]) is not ClockLedger or context["ledger"] != earned_ledger:
            raise ValueError("supplied ledger differs from recorded VFS component work")
        last = component["last_committed"]
        state = parent_restore.state
        if mode == "initial":
            if state["kind"] != "INITIAL" or last is not None or earned_ledger != ClockLedger():
                raise ValueError("INITIAL VFS continuation requires genuine zero component history")
            expected = None
        else:
            if (
                state["kind"] != "COMPLETED"
                or type(last) is not dict
                or set(last) != {"batch_episode", "completion_content", "epsilon_before", "epsilon_after"}
            ):
                raise ValueError("COMPLETED VFS continuation requires its earned canonical commitment")
            closed = state["last_closed_episode"]
            if type(last["batch_episode"]) is not int or last["batch_episode"] != state["completed_boundary_key"]:
                raise ValueError("VFS commitment differs from prepared parent boundary")
            content = last["completion_content"]
            if (
                type(content) is not list
                or not content
                or any(
                    type(pair) is not list or len(pair) != 2 or any(type(value) is not str or not value for value in pair)
                    for pair in content
                )
            ):
                raise ValueError("VFS commitment requires full ordered canonical content")
            canonical = tuple(tuple(pair) for pair in content)
            if last["batch_episode"] != closed["batch_episode"] or canonical != tuple(map(tuple, closed["completion_content"])):
                raise ValueError("VFS commitment differs from actual prepared closure")
            if earned_ledger.completed_batch_episodes == 0 or any(
                type(last[name]) not in (int, float) for name in ("epsilon_before", "epsilon_after")
            ):
                raise ValueError("VFS commitment has no earned completion or schedule")
            expected = {**last, "completion_content": canonical}
        if cadence != {"schema": "parent-global-epsilon-cadence-v1", "last_committed": expected}:
            raise ValueError("runtime cadence differs from earned VFS component commitment")

    def component_state(self):
        """Separate portable journal from genuine source commits and clock work."""
        return {
            "schema": "world-component-continuation-v1",
            "last_committed": copy.deepcopy(self.component_commitment),
            "ledger": {unit: getattr(self.ledger, unit) for unit in CLOCK_UNITS},
        }

    def validate_parent_restore(self, *, prepared, curiosity_state):
        context = self.restore_context
        if context is None or prepared is not context["prepared"]:
            raise ValueError("VFS BANK continuation has no genuine parent custody")
        assert_nested_equal(curiosity_state, context["runtime"]["bank"])
        context["release"] = self.authority.restored(restore=prepared, boundary=context["boundary"])

    def adopt(self, reservation, result, *, retired_world_ids):
        self.reservation, self.result, self.accepted = reservation, result, result.accepted
        observation = result.observation
        self.episode_horizon = self.control_horizon
        self.activation, self.participation = None, None
        self.rewards = {
            name: torch.zeros(self.env.num_agents, device=self.env.device) for name in ("total", "extrinsic", "intrinsic", "shaping")
        }
        self.intent = self.parent.issue(
            kind="initial_participation_intent",
            payload={
                "accepted": self.accepted,
                "world_ids": self.accepted.world_ids,
                "retired_world_ids": retired_world_ids,
                "population_revision": self.revision,
            },
        )
        prepared = self.env.prepare_initial_participation(accepted=self.accepted, intent=self.intent)
        candidate_obs, candidate_masks = prepared.observation, prepared.action_masks
        assert torch.equal(candidate_obs, observation)
        assert candidate_obs.shape == (self.env.num_agents, self.env.observation_dim) and candidate_obs.dtype == torch.float32
        assert candidate_masks.shape == (self.env.num_agents, self.env.action_dim) and candidate_masks.dtype == torch.bool
        assert candidate_obs.device == candidate_masks.device == self.env.device
        completed = torch.tensor([wid in retired_world_ids for wid in self.accepted.world_ids], dtype=torch.bool, device=self.env.device)
        assert not bool(candidate_masks[completed].any()) and bool(candidate_masks[~completed].any(dim=1).all())
        private_obs, counts = candidate_obs.detach().clone(), self.env.step_counts.detach().clone()
        next_revision = self.revision + 1
        self.ready = self.parent.issue(
            kind="initial_participation_ready",
            payload={
                "accepted": self.accepted,
                "intent": self.intent,
                "prepared": prepared,
                "population_revision": self.revision,
            },
        )
        decision = self.env.commit_initial_participation(prepared=prepared, population_ready=self.ready)
        # Assignment-only paired publication suffix.
        self.current_obs = candidate_obs
        self.current_masks = candidate_masks
        self.completed = completed
        self.previous = private_obs
        self.counts = counts
        self.revision = next_revision
        self.participation = decision
        self.intent = None
        self.ready = None
        self.activate()

    def activate(self):
        try:
            self.activation = self.parent.issue(kind="activation", payload={"accepted": self.accepted})
            curiosity = self.runtime.begin_episode(accepted=self.accepted)
            self.env.validate_initial_participation_reading(
                accepted=self.accepted, participation=self.participation, predecessor=self.previous
            )
            assert torch.equal(self.current_obs, self.previous)
            assert torch.equal(self.counts, self.env.step_counts) and torch.equal(self.completed, self.env.dones)
            self.env.activate_episode(accepted=self.accepted, population_receipt=self.activation, curiosity_receipt=curiosity)
            assert torch.equal(self.current_obs, self.previous)
            assert torch.equal(self.counts, self.env.step_counts)
        except BaseException:
            self.activation = None
            self.env.abandon_episode(accepted=self.accepted, reason="runtime_failure")
            raise

    def validate_reading(self):
        self.env.validate_initial_participation(accepted=self.accepted, participation=self.participation, predecessor=self.previous)
        if not torch.equal(self.current_obs, self.previous) or not torch.equal(self.completed, self.env.dones):
            raise ValueError("VFS component's owned predecessor/activity changed")
        if not torch.equal(self.counts, self.env.step_counts):
            raise ValueError("VFS component's eligible counts changed")

    def issue_step(self, actions):
        from townlet.training.clock_ledger import PreparedVectorStep

        self.validate_reading()
        if self.pending is not None:
            raise ValueError("VFS controller already owns a pending step")
        assert actions.shape == (self.env.num_agents,) and actions.dtype == torch.long and actions.device == self.env.device
        assert bool(((actions >= 0) & (actions < self.env.action_dim)).all())
        handle = PreparedVectorStep()
        self.registry[id(handle)] = {
            "handle": handle,
            "accepted": self.accepted,
            "world_ids": self.accepted.world_ids,
            "predecessor": self.previous.clone(),
            "actions": actions.detach().clone(),
            "active_on_entry": ~self.completed.clone(),
            "tick": self.ledger.vector_ticks + 1,
            "stage": "prepared",
        }
        self.pending = handle
        return handle

    def claim(self, *, prepared, accepted, world_ids, predecessor, actions, active_on_entry):
        self.validate_reading()
        record = self.registry.get(id(prepared))
        if record is None or prepared is not record["handle"] or prepared is not self.pending or record["stage"] != "prepared":
            raise ValueError("VFS step is unissued, foreign or consumed")
        if accepted is not self.accepted or accepted is not record["accepted"] or world_ids != record["world_ids"]:
            raise ValueError("VFS step identity changed")
        if record["tick"] != self.ledger.vector_ticks + 1:
            raise ValueError("VFS step lifetime clock changed")
        for name, value in (("predecessor", predecessor), ("actions", actions), ("active_on_entry", active_on_entry)):
            original = record[name]
            if (value.shape, value.dtype, value.device) != (original.shape, original.dtype, original.device) or not torch.equal(
                value, original
            ):
                raise ValueError("VFS step bytes changed")
        record["stage"] = "executing"
        return record["tick"]

    def step(self, actions):
        from townlet.training.state import RewardTensor

        handle = self.issue_step(actions)
        predecessor = self.previous.clone()
        try:
            observation, reward, dones, info = self.env.step(actions, vector_step=handle)
            active, components = info["active_on_entry"], info["reward_components"]
            counts = self.counts + active.to(torch.long)
            assert torch.equal(info["step_counts"], counts)
            self.ledger = self.ledger.advance(vector_ticks=1, eligible_transitions=int(active.sum()))
            if bool(active.any()):
                self.replay.push_recorded(
                    predecessor[active],
                    actions[active],
                    RewardTensor.from_dac(
                        reward[active],
                        extrinsic=components["extrinsic"][active],
                        intrinsic=components["intrinsic"][active],
                        shaping=components["shaping"][active],
                    ),
                    observation[active],
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
            self.current_obs, self.previous = observation.detach().clone(), observation.detach().clone()
            self.current_masks, self.completed = info["successor_action_masks"].detach().clone(), dones.detach().clone()
            self.counts = counts
            self.rewards["total"] += reward
            for name in ("extrinsic", "intrinsic", "shaping"):
                self.rewards[name] += components[name]
            self.registry[id(handle)]["stage"], self.pending = "completed", None
            info["component_selection_epsilons"] = self.current_epsilons
            return observation, reward, dones, info, receipts
        except BaseException:
            self.env.abandon_episode(accepted=self.accepted, reason="runtime_failure")
            raise

    def prepare_empty_episode_evidence(self, *, accepted):
        if accepted is not self.accepted or self.activation is None or self.pending is not None:
            raise ValueError("VFS empty proof lacks activated owner custody")
        if (
            not bool(self.completed.all())
            or bool(self.counts.any())
            or any(record["accepted"] is accepted for record in self.registry.values())
        ):
            raise ValueError("VFS component has actual vector work")
        return self.parent.issue(kind="empty_episode", payload={"accepted": accepted, "participated_world_ids": (), "events": ()})


def bound(compiled, ids, lanes, seed=731):
    roster = WorldRosterDeclaration.from_dict({"schema": "world-roster-v1", "world_ids": list(ids)})
    env = compiled.create_environment(
        num_agents=len(lanes), level_name="L0_test", device="cpu", world_roster=roster, training_seed=seed, lane_world_ids=lanes
    )
    return LocalProducerOwners(compiled, env, roster, seed)


def bootstrap(owners):
    release = owners.authority.bootstrap(first_batch_episode=0)
    owners.env.install_boundary_release(release)
    return release


def accept(owners, release, *, retired_world_ids):
    env = owners.env
    reservation = env.prepare_episode(batch_episode=release.next_batch_episode, release=release)
    result = env.reset(reservation=reservation)
    try:
        owners.adopt(reservation, result, retired_world_ids=retired_world_ids)
    except BaseException:
        owners.activation = None
        env.abandon_episode(accepted=result.accepted, reason="runtime_failure")
        raise
    return reservation, result


def legal_actions(env):
    masks = env.get_action_masks()
    assert masks.any(dim=1).all()
    return masks.to(torch.int64).argmax(dim=1)


def domain_draw(env):
    return env._vfs_draws().stream("bac.identity.probe", (env.num_agents, 16)).uniform("uniform", torch.tensor(0.0))


@pytest.mark.parametrize("other_lanes", [("target-b", "target-a"), ("spectator", "target-a", "target-b")])
def test_current_env_same_ids_survive_lane_reversal_and_leading_spectator(compiled, other_lanes):
    """Causal RED: row-keyed draws change target-a when it moves away from row zero."""
    left = bound(compiled, ("target-a", "target-b"), ("target-a", "target-b"))
    right = bound(compiled, other_lanes, other_lanes)
    for owners in (left, right):
        _, reset = accept(owners, bootstrap(owners), retired_world_ids=())
        assert reset.accepted.world_episode_seqs == (1,) * owners.env.num_agents
        assert owners.env.world_phase == "active"
    before = domain_draw(left.env)
    reordered = domain_draw(right.env)
    for world_id in left.env.world_ids:
        assert torch.equal(before[left.env.world_ids.index(world_id)], reordered[right.env.world_ids.index(world_id)]), world_id
    # The same property survives actual accepted/activated ENV rollout.
    left.step(legal_actions(left.env))
    right.step(legal_actions(right.env))
    assert left.env.global_tick == right.env.global_tick == 1
    after, reordered_after = domain_draw(left.env), domain_draw(right.env)
    for world_id in left.env.world_ids:
        assert torch.equal(after[left.env.world_ids.index(world_id)], reordered_after[right.env.world_ids.index(world_id)]), world_id


def test_other_world_action_does_not_shift_target_domain(compiled):
    left = bound(compiled, ("other", "target"), ("other", "target"))
    right = bound(compiled, ("other", "target"), ("other", "target"))
    for owners in (left, right):
        accept(owners, bootstrap(owners), retired_world_ids=())
    # Align only the target action input. No whole-simulator observation equality is claimed.
    common = left.env.get_action_masks()[1] & right.env.get_action_masks()[1]
    assert common.any()
    target_action = int(common.to(torch.int64).argmax())
    a, b = legal_actions(left.env), legal_actions(right.env)
    alternatives = right.env.get_action_masks()[0].nonzero().flatten()
    alternatives = alternatives[alternatives != a[0]]
    assert alternatives.numel() > 0
    b[0] = alternatives[0]
    a[1] = b[1] = target_action
    left.step(a)
    right.step(b)
    assert torch.equal(domain_draw(left.env)[1], domain_draw(right.env)[1])


def context(seed, ids, sequences):
    # Deferred deliberately: first RED must reach current row-key behavior, not import failure.
    from townlet.vfs.random_draws import VFSWorldContext

    return VFSWorldContext(training_seed=seed, world_ids=ids, world_episode_seqs=sequences)


def producer(seed, ids, sequences):
    from townlet.vfs.random_draws import VFSRandomness

    return VFSRandomness(context=context(seed, ids, sequences))


def expected_uniform(seed, world_id, sequence, tick, site, ordinal, element):
    """Independent scalar executable specification; uses no production hash helpers."""
    mask = 2**64 - 1

    def mix(value):
        value = (value + 0x9E3779B97F4A7C15) & mask
        value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & mask
        value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & mask
        return value ^ (value >> 31)

    encoded = json.dumps([DOMAIN, seed, world_id, sequence], ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    base = int.from_bytes(hashlib.blake2b(encoded, digest_size=8).digest(), "little")
    label = int.from_bytes(hashlib.blake2b(site.encode("utf-8"), digest_size=8).digest(), "little")
    key = mix(mix(mix(base ^ tick) ^ label) ^ ordinal)
    return (mix(key ^ element) >> 40) / 2**24


@pytest.mark.parametrize(
    "device_name", ["cpu", pytest.param("cuda", marks=pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA unavailable"))]
)
@pytest.mark.parametrize("shape,argument_shape", [((2,), ()), ((2, 3), ()), ((2, 3), (2, 3)), ((2, 1), (2, 4))])
def test_vectorized_uniform_normal_shapes_match_independent_domain_spec(device_name, shape, argument_shape):
    from townlet.vfs.random_draws import reference_uniform

    device = torch.device(device_name)
    ids, sequences, seed, tick = ("a:雪", " a:雪 "), (2, 11), 2**80 + 91, 7
    draws = producer(seed, ids, sequences).instant(tick=tick, device=device)
    like = torch.zeros(argument_shape, device=device)
    stream = draws.stream("test.site", shape)
    actual = stream.uniform("uniform", like)
    normal = stream.normal("normal_dist", like)
    result_shape = tuple(torch.broadcast_shapes(shape, argument_shape))
    elements = math.prod(result_shape[1:])
    expected = torch.tensor(
        [
            [expected_uniform(seed, wid, seq, tick, "test.site", 0, element) for element in range(elements)]
            for wid, seq in zip(ids, sequences)
        ],
        dtype=torch.float32,
        device=device,
    ).reshape(result_shape)
    assert actual.shape == normal.shape == result_shape
    assert actual.dtype == normal.dtype == torch.float32
    assert actual.device == normal.device == device
    assert torch.equal(actual, expected)
    expected_normal = []
    for wid, seq in zip(ids, sequences):
        row = []
        for element in range(elements):
            u1 = 1 - expected_uniform(seed, wid, seq, tick, "test.site", 1, 2 * element)
            u2 = expected_uniform(seed, wid, seq, tick, "test.site", 1, 2 * element + 1)
            row.append(math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2))
        expected_normal.append(row)
    torch.testing.assert_close(normal, torch.tensor(expected_normal, device=device).reshape(result_shape), rtol=1e-6, atol=1e-6)
    assert torch.isfinite(normal).all()
    assert ((actual >= 0) & (actual < 1)).all()
    assert reference_uniform(
        training_seed=seed, world_id=ids[1], world_episode_seq=11, tick=tick, site="test.site", ordinal=0, element=0
    ) == expected_uniform(seed, ids[1], 11, tick, "test.site", 0, 0)


def test_unequal_context_sequences_preserve_target_and_shared_prefix():
    first = producer(71, ("other", "target"), (1, 9)).instant(tick=3, device=torch.device("cpu"))
    changed = producer(71, ("other", "target"), (100, 9)).instant(tick=3, device=torch.device("cpu"))
    draw_a = first.stream("site", (2, 32)).uniform("uniform", torch.tensor(0.0))
    draw_b = changed.stream("site", (2, 32)).uniform("uniform", torch.tensor(0.0))
    assert torch.equal(draw_a[1], draw_b[1])
    assert not torch.equal(draw_a[0], draw_b[0])
    for instant in (first, changed):
        a = instant.stream_with_shared_prefix("write.a", (2, 32), shared_site="rule", shared_draws=1)
        b = instant.stream_with_shared_prefix("write.b", (2, 32), shared_site="rule", shared_draws=1)
        assert torch.equal(a.uniform("uniform", torch.tensor(0.0)), b.uniform("uniform", torch.tensor(0.0)))
        tail = a.uniform("uniform", torch.tensor(0.0))
        ordinary = instant.stream("write.a", (2, 32)).uniform("uniform", torch.tensor(0.0))
        assert torch.equal(tail, ordinary)
        assert not torch.equal(tail, b.uniform("uniform", torch.tensor(0.0)))


def test_locked_normative_vectors_and_seed_id_sequence_tick_site_ordinal_inputs():
    from townlet.vfs.random_draws import reference_uniform

    # Locked by root from the approved scalar specification before production edits.
    # Keep these literal data here; no runtime dependency on ignored handoff JSON.
    vectors = (
        (0, "target-a", 0, 0, "vfs.reference", 0, (14222929, 2176863, 2314024, 2910008)),
        (
            731,
            "target-a",
            1,
            1,
            "bac.identity.probe",
            0,
            (
                16680306,
                3999839,
                8338086,
                10240450,
                5803577,
                14828653,
                5886397,
                3077549,
                8241551,
                11996649,
                15302141,
                5075517,
                6067964,
                14402929,
                3246540,
                3149326,
            ),
        ),
        (1208925819614629174706267, " a:雪 ", 11, 7, "u", 2, (12260248, 12197302, 14462603, 6327938)),
        (1208925819614629174706267, "a:雪", 2, 7, "u", 0, (259688, 675176, 14603466, 9899782)),
    )
    # Validate every oracle vector before reaching the old reference API's causal RED.
    for seed, wid, seq, tick, site, ordinal, expected_bits24 in vectors:
        for element, bits24 in enumerate(expected_bits24):
            assert expected_uniform(seed, wid, seq, tick, site, ordinal, element) == bits24 / 2**24
    for seed, wid, seq, tick, site, ordinal, expected_bits24 in vectors:
        for element, bits24 in enumerate(expected_bits24):
            assert (
                reference_uniform(
                    training_seed=seed,
                    world_id=wid,
                    world_episode_seq=seq,
                    tick=tick,
                    site=site,
                    ordinal=ordinal,
                    element=element,
                )
                == bits24 / 2**24
            )
    for seed, wid, seq, tick, site, ordinal, expected_bits24 in vectors:
        stream = producer(seed, (wid,), (seq,)).instant(tick=tick, device=torch.device("cpu")).stream(site, (1, len(expected_bits24)))
        for _ in range(ordinal):
            stream.uniform("uniform", torch.tensor(0.0))
        actual = stream.uniform("uniform", torch.tensor(0.0))
        expected = torch.tensor([[bits24 / 2**24 for bits24 in expected_bits24]], dtype=torch.float32)
        assert torch.equal(actual, expected)

    values = []
    for seed, wid, seq, tick, site, ordinal in (
        (3, "target", 4, 5, "s", 0),
        (3 + 2**64, "target", 4, 5, "s", 0),
        (3, "target ", 4, 5, "s", 0),
        (3, "target", 6, 5, "s", 0),
        (3, "target", 4, 6, "s", 0),
        (3, "target", 4, 5, "s.other", 0),
        (3, "target", 4, 5, "s", 1),
    ):
        stream = producer(seed, (wid,), (seq,)).instant(tick=tick, device=torch.device("cpu")).stream(site, (1, 16))
        for _ in range(ordinal):
            stream.uniform("uniform", torch.tensor(0.0))
        actual = stream.uniform("uniform", torch.tensor(0.0))
        expected = torch.tensor([[expected_uniform(seed, wid, seq, tick, site, ordinal, e) for e in range(16)]])
        assert torch.equal(actual, expected)
        values.append(actual)
    assert all(not torch.equal(values[0], other) for other in values[1:])


def test_reset_projects_reservation_before_evaluation_and_retry_never_resamples(compiled, monkeypatch):
    owners = bound(compiled, ("a", "b"), ("b", "a"))
    env = owners.env
    release = bootstrap(owners)
    before, rng = env.vfs_random_state(), torch.get_rng_state().clone()
    reservation = env.prepare_episode(batch_episode=0, release=release)
    assert env.prepare_episode(batch_episode=0, release=release).world_episode_seqs == (1, 1)
    assert env.vfs_random_state() == before
    assert torch.equal(torch.get_rng_state(), rng)
    observed = []
    real_evaluate = env._evaluate_vfs_profiles

    def observe():
        if env.world_phase != "resetting":
            return real_evaluate()
        assert env.world_phase == "resetting"
        assert dict(env.accepted_episode_seqs) == {"b": 0, "a": 0}
        observed.append(env.vfs_randomness.state())
        with pytest.raises(ValueError):
            env.vfs_random_state()
        return real_evaluate()

    monkeypatch.setattr(env, "_evaluate_vfs_profiles", observe)
    result = env.reset(reservation=reservation)
    assert len(observed) == 1
    assert observed[0]["world_ids"] == ["b", "a"]
    assert observed[0]["world_episode_seqs"] == [1, 1]
    assert tuple(observed[0]["world_episode_seqs"]) == result.accepted.world_episode_seqs
    owners.adopt(reservation, result, retired_world_ids=())
    for after_step in (False, True):
        if after_step:
            owners.step(legal_actions(env))
        state, tick, rng = env.vfs_random_state(), env.global_tick, torch.get_rng_state().clone()
        assert env.reset(reservation=reservation) is result
        assert env.vfs_random_state() == state
        assert env.global_tick == tick
        assert torch.equal(torch.get_rng_state(), rng)
    assert dict(env.accepted_episode_seqs) == {"a": 1, "b": 1}


def test_late_reset_failure_quarantines_candidate_without_accepting(compiled, monkeypatch):
    owners = bound(compiled, ("a", "b"), ("a", "b"))
    env = owners.env
    release = bootstrap(owners)
    reservation = env.prepare_episode(batch_episode=0, release=release)
    real_evaluate = env._evaluate_vfs_profiles
    observed = []

    def fail_late():
        real_evaluate()
        observed.append(domain_draw(env))
        raise RuntimeError("owned late-reset fault")

    monkeypatch.setattr(env, "_evaluate_vfs_profiles", fail_late)
    with pytest.raises(RuntimeError, match="owned late-reset fault"):
        env.reset(reservation=reservation)
    assert len(observed) == 1
    assert env.world_phase == "quarantined"
    assert dict(env.accepted_episode_seqs) == {"a": 0, "b": 0}
    with pytest.raises(ValueError):
        env.vfs_random_state()
    with pytest.raises(ValueError):
        env.reset(reservation=reservation)


@pytest.mark.parametrize(
    "field,value",
    [
        ("training_seed", True),
        ("training_seed", 4.0),
        ("training_seed", -1),
        ("world_ids", ["a", "a"]),
        ("world_ids", ["a", ""]),
        ("world_ids", ["a", 9]),
        ("world_episode_seqs", [0, True]),
        ("world_episode_seqs", [0, 1.0]),
        ("world_episode_seqs", [0, -1]),
        ("world_episode_seqs", [0]),
        ("world_episode_seqs", [0, 9]),
        ("schema", "old"),
        ("domain", "curiosity"),
    ],
)
def test_vfs_deep_validation_refuses_before_mutation(field, value):
    from townlet.vfs.random_draws import VFSRandomness

    draws = producer(4, ("a", "b"), (0, 1))
    expected = context(4, ("a", "b"), (0, 1))
    before = draws.state()
    broken = copy.deepcopy(before)
    broken[field] = value
    rng = torch.get_rng_state().clone()
    with pytest.raises((ValueError, TypeError)):
        VFSRandomness.validate_state(broken, expected=expected)
    assert draws.state() == before
    assert torch.equal(torch.get_rng_state(), rng)


def test_native_context_owns_storage_and_refuses_old_scalar_payload():
    from townlet.vfs.random_draws import VFSRandomness

    draws = producer(4, ("a", "b"), (0, 1))
    expected = context(4, ("a", "b"), (0, 1))
    state = draws.state()
    validated = VFSRandomness.validate_state(state, expected=expected)
    state["world_ids"][1] = "changed"
    state["world_episode_seqs"][1] = 99
    assert validated.world_ids == ("a", "b")
    assert validated.world_episode_seqs == (0, 1)
    assert draws.state()["world_episode_seqs"] == [0, 1]
    for broken in ({"seed": 4, "episode": 1}, {**draws.state(), "extra": 1}):
        with pytest.raises((ValueError, TypeError)):
            VFSRandomness.validate_state(broken, expected=expected)


def initial_snapshot(owners, release):
    identity = {
        "semantic_execution_identity": owners.env.semantic_execution_identity,
        "bootstrap_first_batch": release.next_batch_episode,
        "world_binding": owners.env.world_ids,
    }
    states = {
        "population": {"component_vector_ticks": owners.ledger.vector_ticks, "accepted": owners.accepted},
        "curriculum": copy.deepcopy(owners.curriculum.checkpoint_state()),
        "exploration": copy.deepcopy(owners.runtime.checkpoint_state()),
        "network": copy.deepcopy(owners.network.state_dict()),
        "optimizer": copy.deepcopy(owners.optimizer.state_dict()),
        "scheduler": {"state": None if owners.scheduler is None else copy.deepcopy(owners.scheduler.state_dict())},
        "replay": copy.deepcopy(owners.replay.serialize()),
        "selection": {"epsilon": owners.runtime.epsilon, "diagnostic": owners.current_epsilons.clone()},
    }
    children = {
        role: owners.roles[role].issue(kind="initial_owner", payload={**identity, "role": role, "state": states[role]})
        for role in ROLES
        if role != "curiosity"
    }
    initial = owners.authority.prepare_initial_snapshot(
        release=release, owners=owners.parent.issue(kind="initial_owners", payload={**identity, **children})
    )
    owners.saved_runtime = copy.deepcopy(states["exploration"])
    owners.saved_ledger = owners.ledger
    owners.saved_component = owners.component_state()
    return owners.env.checkpoint_world_state(kind="INITIAL", release=release, retained_binding_batches=(), initial=initial)


def completed_snapshot(owners, accepted):
    from townlet.training.episode import EpisodeCompletion, LaneOutcome, freeze_lane_outcome

    env = owners.env
    assert not bool(owners.completed.all())  # Whole-empty is abandonment, never a completion step.
    masks = env.get_action_masks()
    assert bool(masks[~owners.completed].any(dim=1).all()) and not bool(masks[owners.completed].any())
    owners.step(masks.to(torch.long).argmax(dim=1))
    participants = tuple(wid for row, wid in enumerate(env.world_ids) if int(env.step_counts[row]) > 0)
    assert accepted is owners.accepted and participants
    assert bool((owners.counts <= owners.episode_horizon).all())
    outcomes = tuple(
        LaneOutcome(
            outcome=EpisodeCompletion(
                agent_idx=row,
                reason="cap",
                survival_time=int(owners.counts[row]),
                final_observation=owners.current_obs[row].detach().cpu().clone(),
                final_meters=env.meters[row].detach().cpu().clone(),
            ),
            batch_episode=accepted.batch_episode,
            planned_horizon=owners.episode_horizon,
            reward_total=float(owners.rewards["total"][row]),
            reward_extrinsic=float(owners.rewards["extrinsic"][row]),
            reward_intrinsic=float(owners.rewards["intrinsic"][row]),
            reward_shaping=float(owners.rewards["shaping"][row]),
            policy_entropy=0.0,
            world_id=wid,
            world_episode_seq=accepted.world_episode_seqs[row],
        )
        for row, wid in enumerate(accepted.world_ids)
        if wid in participants
    )
    # Genuine deterministic legal-argmax policy has entropy0; no Q learning claim.
    content = tuple((item.payload.hex(), item.fingerprint) for item in map(freeze_lane_outcome, outcomes))
    before = owners.runtime.epsilon
    curriculum = owners.curriculum.prepare_episode_outcomes(outcomes)
    bank = owners.runtime.prepare_completion(
        accepted=accepted,
        boundary_key=accepted.batch_episode,
        completion_content=content,
        outcomes=outcomes,
        participated_world_ids=participants,
    )
    prepared = env.prepare_episode_close(
        accepted=accepted,
        boundary_key=accepted.batch_episode,
        completion_content=content,
        participated_world_ids=participants,
        dispositions=bank.prepared_receipt,
    )
    request = (accepted, accepted.batch_episode, content)
    env.freeze_episode_close(prepared)
    owners.curriculum.commit_prepared_episode_outcomes(curriculum)
    committed = owners.runtime.commit_completion(prepared=bank)
    owners.commit_request = request
    owners.runtime.commit_batch_episode(batch_episode=accepted.batch_episode, outcomes=outcomes)
    after = max(owners.policy.epsilon_end, before * owners.policy.epsilon_decay)
    published = owners.runtime.checkpoint_state()
    assert owners.runtime.epsilon == published["selector"]["epsilon"] == after
    assert published["cadence"]["last_committed"] == {
        "batch_episode": accepted.batch_episode,
        "completion_content": content,
        "epsilon_before": before,
        "epsilon_after": after,
    }
    owners.runtime.commit_batch_episode(batch_episode=accepted.batch_episode, outcomes=outcomes)
    assert_nested_equal(owners.runtime.checkpoint_state(), published)
    owners.current_epsilons = owners.runtime.epsilon_tensor(batch_size=env.num_agents, device=env.device)
    assert torch.equal(owners.current_epsilons, torch.full((env.num_agents,), after, dtype=torch.float32, device=env.device))
    owners.committed[accepted.batch_episode] = content
    owners.ledger = owners.ledger.advance(completed_batch_episodes=1)
    owners.component_commitment = {
        "batch_episode": accepted.batch_episode,
        "completion_content": [list(pair) for pair in request[2]],
        "epsilon_before": before,
        "epsilon_after": after,
    }
    closure = env.close_episode(prepared, dispositions=committed)
    child_payload = {"accepted": accepted, "boundary_key": accepted.batch_episode, "completion_content": content}
    child_roles = {
        "curriculum_receipt": "curriculum",
        "exploration_receipt": "exploration",
        "population_commit_receipt": "population",
        "epsilon_install_receipt": "exploration",
        "selection_sync_receipt": "selection",
    }
    effects = owners.parent.issue(
        kind="boundary_effects",
        payload={
            "batch_episode": accepted.batch_episode,
            "accepted_identity": accepted,
            "completion_content": content,
            "retirement_receipt": committed,
            **{name: owners.roles[role].issue(kind=name, payload=child_payload) for name, role in child_roles.items()},
        },
    )
    release = owners.authority.completed(closure=closure, effects=effects)
    env.install_boundary_release(release)
    owners.saved_runtime = copy.deepcopy(published)
    owners.saved_ledger = owners.ledger
    owners.saved_component = owners.component_state()
    owners.release = release
    return env.checkpoint_world_state(kind="COMPLETED", release=release, retained_binding_batches=tuple(owners.committed), initial=None)


def prepare_restore(owners, state, *, runtime_state, component_ledger, component_state):
    prepared = owners.env.prepare_world_restore(
        kind=state["kind"],
        state=state,
        world_roster=owners.roster,
        destination_world_ids=owners.env.world_ids,
        semantic_execution_identity=owners.env.semantic_execution_identity,
    )
    owners.restore_context = {
        "prepared": prepared,
        "mode": "initial" if state["kind"] == "INITIAL" else "completed_boundary",
        "runtime": copy.deepcopy(runtime_state),
        "ledger": component_ledger,
        "component": copy.deepcopy(component_state),
        "release": None,
    }
    return prepared


def install_restore(owners, prepared):
    receipt = owners.parent.issue(
        kind="restored_boundary", payload={"kind": prepared.state["kind"], "state": prepared.state, "prepared": prepared}
    )
    context = owners.restore_context
    if context is None or context["prepared"] is not prepared:
        raise ValueError("VFS restore requires its exact retained runtime/world pairing")
    context["boundary"] = receipt
    # Actual runtime/BANK continuation only. Other component children are fresh;
    # this remains explicitly short of all-child T26/full-parent installation.
    child = owners.runtime.prepare_restore(
        state=context["runtime"],
        mode=context["mode"],
        accepted=None,
        parent_restore=prepared,
        validate_parent_restore=owners.validate_parent_restore,
    )
    owners.runtime.install_restore(prepared=child)
    owners.ledger = context["ledger"]
    owners.component_commitment = context["component"]["last_committed"]
    owners.current_epsilons = owners.runtime.epsilon_tensor(batch_size=owners.env.num_agents, device=owners.env.device)
    release = context["release"]
    assert release is not None
    installed = owners.env.install_world_restore(prepared=prepared, release=release)
    assert owners.env.install_world_restore(prepared=prepared, release=release) is installed
    return installed


@pytest.mark.parametrize("kind", ["INITIAL", "COMPLETED"])
def test_native_roundtrip_projects_destination_and_preserves_history(compiled, kind):
    source = bound(compiled, ("a", "b"), ("a", "b"))
    release = bootstrap(source)
    if kind == "INITIAL":
        state = initial_snapshot(source, release)
        sequence = 0
    else:
        _, result = accept(source, release, retired_world_ids=())
        state = completed_snapshot(source, result.accepted)
        sequence = 1
    assert state["schema"] == "world-lifecycle-v4"
    assert state["vfs_random_context"]["world_episode_seqs"] == [sequence, sequence]
    destination = bound(compiled, ("a", "b"), ("b", "a"))
    before = destination.env.vfs_random_state()
    prepared = prepare_restore(
        destination,
        state,
        runtime_state=source.saved_runtime,
        component_ledger=source.saved_ledger,
        component_state=json.loads(json.dumps(source.saved_component)),
    )
    assert destination.env.vfs_random_state() == before
    # Prepared restore data must remain portable, not embed a producer/dataclass/capability.
    json.dumps(prepared.payload)
    # Accessor copies and input mutations must not change the portable prepared payload.
    state["vfs_random_context"]["world_episode_seqs"][1] = 999
    exposed = prepared.state
    exposed["vfs_random_context"]["world_ids"][1] = "tampered"
    assert prepared.state["vfs_random_context"]["world_ids"] == ["a", "b"]
    assert prepared.state["vfs_random_context"]["world_episode_seqs"] == [sequence, sequence]
    rng = torch.get_rng_state().clone()
    installed = install_restore(destination, prepared)
    assert torch.equal(torch.get_rng_state(), rng)
    assert destination.env.vfs_random_state()["world_ids"] == ["b", "a"]
    assert destination.env.vfs_random_state()["world_episode_seqs"] == [sequence, sequence]
    assert dict(destination.env.accepted_episode_seqs) == {"a": sequence, "b": sequence}
    if kind == "COMPLETED":
        again = destination.env.checkpoint_world_state(kind=kind, release=installed, retained_binding_batches=(0,), initial=None)
        assert again["accepted_bindings"] == prepared.state["accepted_bindings"]
        assert again["saved_lane_binding"] == prepared.state["saved_lane_binding"]
        assert again["vfs_random_context"]["world_ids"] == ["b", "a"]
        # Validate a second-generation snapshot where historical and producer lanes differ.
        second = bound(compiled, ("a", "b"), ("a", "b"))
        install_restore(
            second,
            prepare_restore(
                second,
                again,
                runtime_state=destination.runtime.checkpoint_state(),
                component_ledger=destination.ledger,
                component_state=json.loads(json.dumps(destination.component_state())),
            ),
        )
        assert second.env.vfs_random_state()["world_ids"] == ["a", "b"]
    _, result = accept(destination, installed, retired_world_ids=())
    assert result.accepted.world_episode_seqs == (sequence + 1, sequence + 1)


@pytest.mark.parametrize("kind", ["INITIAL", "COMPLETED"])
@pytest.mark.parametrize(
    "field,value",
    [
        ("training_seed", 732),
        ("world_ids", ["a", "intruder"]),
        ("world_ids", ["b", "a"]),
        ("world_episode_seqs", [1, True]),
        ("world_episode_seqs", [0, 19]),
        ("domain", "curiosity"),
    ],
)
def test_native_deep_child_refusal_is_pure_including_initial(compiled, kind, field, value):
    source = bound(compiled, ("a", "b"), ("a", "b"))
    release = bootstrap(source)
    if kind == "INITIAL":
        state = initial_snapshot(source, release)
    else:
        _, result = accept(source, release, retired_world_ids=())
        state = completed_snapshot(source, result.accepted)
    state["vfs_random_context"][field] = value
    destination = bound(compiled, ("a", "b"), ("b", "a"))
    env = destination.env
    before = (env.world_phase, dict(env.accepted_episode_seqs), env.vfs_random_state(), env.global_tick)
    rng = torch.get_rng_state().clone()
    with pytest.raises((ValueError, TypeError)):
        prepare_restore(
            destination,
            state,
            runtime_state=source.saved_runtime,
            component_ledger=source.saved_ledger,
            component_state=source.saved_component,
        )
    assert (env.world_phase, dict(env.accepted_episode_seqs), env.vfs_random_state(), env.global_tick) == before
    assert torch.equal(torch.get_rng_state(), rng)


def test_standalone_restore_cannot_install_contradictory_cursors(compiled):
    owners = bound(compiled, ("a", "b"), ("a", "b"))
    bootstrap(owners)
    env = owners.env
    before = env.vfs_random_state()
    broken = copy.deepcopy(before)
    broken["world_episode_seqs"][1] = 1
    rng = torch.get_rng_state().clone()
    with pytest.raises((ValueError, TypeError)):
        env.restore_vfs_random_state(broken)
    assert env.vfs_random_state() == before
    assert dict(env.accepted_episode_seqs) == {"a": 0, "b": 0}
    assert torch.equal(torch.get_rng_state(), rng)
    env.restore_vfs_random_state(before)
    assert env.vfs_random_state() == before


def test_component_vfs_mixed_then_all_active_two_real_boundaries(compiled):
    """Real BANK disposition/sequence and lifetime cadence survive a new accepted cycle."""
    owners = bound(compiled, ("a", "b"), ("b", "a"))
    release = bootstrap(owners)
    for batch, retired, transitions in ((0, ("b",), 1), (1, (), 3)):
        _, result = accept(owners, release, retired_world_ids=retired)
        assert result.accepted.world_episode_seqs == (batch + 1, batch + 1)
        assert owners.env.global_tick == 0 and owners.ledger.vector_ticks == batch
        assert torch.equal(
            owners.current_epsilons, owners.runtime.epsilon_tensor(batch_size=owners.env.num_agents, device=owners.env.device)
        )
        state = completed_snapshot(owners, result.accepted)
        assert owners.env.global_tick == 1 and owners.ledger.vector_ticks == batch + 1
        assert owners.ledger.eligible_transitions == transitions == owners.replay.retained_transitions
        assert owners.ledger.completed_batch_episodes == batch + 1
        assert tuple(state["last_closed_episode"]["participated_world_ids"]) == tuple(wid for wid in ("b", "a") if wid not in retired)
        assert state["vfs_random_context"]["world_episode_seqs"] == [batch + 1, batch + 1]
        assert len(state["accepted_bindings"]) == batch + 1
        release = owners.release
    assert owners.env.prepare_episode(batch_episode=release.next_batch_episode, release=release).world_episode_seqs == (3, 3)


@pytest.mark.parametrize(
    "damage", ["initial_cadence", "earlier_cadence", "zero_ledger", "earlier_ledger", "same_count_ledger", "initial_nonzero_ledger"]
)
def test_native_restore_rejects_unearned_cadence_or_ledger_before_publication(compiled, monkeypatch, damage):
    """Genuine world/BANK pairing cannot bless an unrelated global cadence or lifetime ledger."""
    source = bound(compiled, ("a", "b"), ("a", "b"))
    release = bootstrap(source)
    initial = initial_snapshot(source, release)
    initial_runtime, zero_ledger = copy.deepcopy(source.saved_runtime), source.saved_ledger
    initial_component = copy.deepcopy(source.saved_component)
    captures = []
    for retired in (("b",), ()):
        _, result = accept(source, release, retired_world_ids=retired)
        state = completed_snapshot(source, result.accepted)
        captures.append((state, copy.deepcopy(source.saved_runtime), source.saved_ledger, copy.deepcopy(source.saved_component)))
        release = source.release
    earlier, latest = captures
    assert earlier[2].vector_ticks == 1 and earlier[2].eligible_transitions == 1
    assert latest[2].vector_ticks == 2 and latest[2].eligible_transitions == 3
    assert latest[1]["cadence"]["last_committed"]["batch_episode"] == 1
    assert_nested_equal(latest[1]["cadence"]["last_committed"]["completion_content"], source.committed[1])
    state, runtime_state, ledger, component = (
        (initial, initial_runtime, zero_ledger, initial_component) if damage == "initial_nonzero_ledger" else latest
    )
    component = json.loads(json.dumps(component))
    healthy = bound(compiled, ("a", "b"), ("b", "a"))
    prepared = prepare_restore(healthy, state, runtime_state=runtime_state, component_ledger=ledger, component_state=component)
    json.dumps(prepared.payload)
    installed = install_restore(healthy, prepared)
    continued = healthy.runtime.checkpoint_state()
    for field in ("selector", "cadence"):
        assert_nested_equal(continued[field], runtime_state[field])
    assert healthy.ledger == ledger
    _, next_reset = accept(healthy, installed, retired_world_ids=())
    assert next_reset.accepted.world_episode_seqs == ((1, 1) if state["kind"] == "INITIAL" else (3, 3))
    candidate = copy.deepcopy(runtime_state)
    if damage in ("initial_cadence", "earlier_cadence"):
        old_runtime = initial_runtime if damage == "initial_cadence" else earlier[1]
        for field in ("selector", "cadence"):
            candidate[field] = copy.deepcopy(old_runtime[field])
        assert_nested_equal(candidate["bank"], latest[1]["bank"])
        assert candidate["cadence"] != latest[1]["cadence"]
    elif damage == "zero_ledger":
        ledger = zero_ledger
    elif damage == "earlier_ledger":
        ledger = earlier[2]
    elif damage == "same_count_ledger":
        other = bound(compiled, ("a", "b"), ("a", "b"))
        other.control_horizon = 2
        other_release = bootstrap(other)
        for batch in (0, 1):
            _, result = accept(other, other_release, retired_world_ids=())
            if batch == 0:
                other.step(legal_actions(other.env))
            completed_snapshot(other, result.accepted)
            other_release = other.release
        ledger = other.saved_ledger
        assert ledger.completed_batch_episodes == latest[2].completed_batch_episodes
        assert ledger.vector_ticks != latest[2].vector_ticks and ledger.eligible_transitions != latest[2].eligible_transitions
    else:
        ledger = latest[2]
    destination = bound(compiled, ("a", "b"), ("b", "a"))
    env = destination.env
    before = {
        "phase": env.world_phase,
        "cursors": dict(env.accepted_episode_seqs),
        "physical": {name: getattr(env, name).clone() for name in ("positions", "meters", "dones", "step_counts")},
        "ledger": destination.ledger,
    }
    preparations, installations = [], []
    prepare_world = env.prepare_world_restore
    install_child, install_world = destination.runtime.install_restore, env.install_world_restore

    def observed_prepare(**kwargs):
        actual = prepare_world(**kwargs)
        preparations.append(actual)
        return actual

    def observed_child(**kwargs):
        installations.append("runtime/BANK")
        return install_child(**kwargs)

    def observed_world(**kwargs):
        installations.append("world")
        return install_world(**kwargs)

    monkeypatch.setattr(env, "prepare_world_restore", observed_prepare)
    monkeypatch.setattr(destination.runtime, "install_restore", observed_child)
    monkeypatch.setattr(env, "install_world_restore", observed_world)
    try:
        with pytest.raises(ValueError):
            prepared = prepare_restore(destination, state, runtime_state=candidate, component_ledger=ledger, component_state=component)
            json.dumps(prepared.payload)
            install_restore(destination, prepared)
    finally:
        assert len(preparations) == 1, "negative must reach genuine ENV restore preparation"
        assert installations == [], "mismatched continuation must refuse before runtime/BANK or world installation"
        assert destination.ledger is before["ledger"]
        assert env.world_phase == before["phase"]
        assert dict(env.accepted_episode_seqs) == before["cursors"]
        for name, original in before["physical"].items():
            assert_nested_equal(getattr(env, name), original)
