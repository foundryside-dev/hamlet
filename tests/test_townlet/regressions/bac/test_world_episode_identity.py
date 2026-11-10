"""Real ENV producer tests; sealed local sink receipts are interface evidence only.

Compilation uses the accepted current1.42 public receipt. The sinks below do not
qualify real POP/PW05/T25/T26, provider learning, VFS or simulator independence.
New production imports stay inside helpers so the preimplementation RED collects.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

IDS = ("orchard-west", "river-house")
SEED = 479


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


def _same(left, right):
    if isinstance(left, torch.Tensor):
        assert isinstance(right, torch.Tensor)
        assert left.dtype == right.dtype and left.device == right.device
        assert left.shape == right.shape and torch.equal(left, right)
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
    def __init__(self, env, bootstrap=True):
        self.env = env
        self.boundary = _Sink()
        self.population = _Sink()
        self.bank = _Sink()
        self.roles = dict.fromkeys(
            "population curiosity curriculum exploration network optimizer scheduler replay selection".split(), self.boundary
        )
        self.roles.update(population=self.population, curiosity=self.bank)
        self.authority = env.bind_boundary_authority(owner=self.boundary, role_owners=self.roles)
        self.release = None
        self.accepted = None
        self.events = {}
        if bootstrap:
            self.release = env.install_boundary_release(self.authority.bootstrap(first_batch_episode=1))

    def reset(self, batch):
        reservation = self.env.prepare_episode(batch_episode=batch, release=self.release)
        self.env.validate_episode_reservation(reservation)
        reset = self.env.reset(reservation=reservation)
        self.accepted = reset.accepted
        self.env.activate_episode(
            accepted=reset.accepted,
            population_receipt=self.population.activation(reset.accepted),
            curiosity_receipt=self.bank.activation(reset.accepted),
        )
        return reservation, reset

    def step(self, participants=IDS):
        # Control actual active-on-entry lanes; no fabricated simulator steps.
        for index, world_id in enumerate(self.env.world_ids):
            self.env.dones[index] = world_id not in participants
        masks = self.env.get_action_masks()
        actions = masks.to(torch.int64).argmax(dim=1)
        self.env.step(actions, depletion_multiplier=1.0)
        self.population.participants = tuple(participants)
        self.bank.participants = tuple(participants)

    def close(self, batch, participants=IDS):
        # Actual ENV participation; opaque fixture content is not an EP envelope.
        content = tuple(
            (batch, index, world_id, self.accepted.world_episode_seqs[index], "interface-outcome")
            for index, world_id in enumerate(self.accepted.world_ids)
            if world_id in participants
        )
        self.events[batch] = content
        dispositions = tuple(
            (world_id, "completed" if world_id in participants else "retired_nonparticipating") for world_id in self.accepted.world_ids
        )
        receipt = self.bank.receipt(
            "prepared_dispositions",
            accepted=self.accepted,
            boundary_key=batch,
            completion_content=content,
            participated_world_ids=tuple(participants),
            dispositions=dispositions,
        )
        prepared = self.env.prepare_episode_close(
            accepted=self.accepted,
            boundary_key=batch,
            completion_content=content,
            participated_world_ids=tuple(participants),
            dispositions=receipt,
        )
        self.env.freeze_episode_close(prepared)
        receipt = self.bank.receipt("dispositions", **receipt.payload)
        closure = self.env.close_episode(prepared, dispositions=receipt)
        self.bank.records[batch] = dispositions
        return prepared, closure, receipt

    def release_closed(self, batch, closure, dispositions):
        fields = {
            name: (self.population if name == "population_commit_receipt" else self.boundary).receipt(
                name, accepted=self.accepted, boundary_key=batch, completion_content=self.events[batch]
            )
            for name in (
                "curriculum_receipt",
                "exploration_receipt",
                "population_commit_receipt",
                "epsilon_install_receipt",
                "selection_sync_receipt",
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
        owner_fields = {
            name: self.roles[name].receipt(
                "initial_owner",
                state={"weights": self.boundary.initial_weight.clone()},
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


def _restore(compiled, state, order):
    run = _Run(_env(compiled, order), bootstrap=False)
    prepared = run.env.prepare_world_restore(
        kind=state["kind"],
        state=state,
        world_roster=_roster(),
        destination_world_ids=order,
        semantic_execution_identity=run.env.semantic_execution_identity,
    )
    # T25/T26 joint validation is a labeled sealed interface attestation here.
    boundary = run.boundary.receipt("restored_boundary", kind=state["kind"], state=deepcopy(state), prepared=prepared)
    release = run.authority.restored(restore=prepared, boundary=boundary)
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
    run = _Run(_env(compiled))
    before = _state(run.env)
    first = run.env.prepare_episode(batch_episode=1, release=run.release)
    second = run.env.prepare_episode(batch_episode=1, release=run.release)
    assert first.world_ids == second.world_ids == IDS
    assert first.world_episode_seqs == second.world_episode_seqs == (1, 1)
    foreign = _Run(_env(compiled))
    foreign_reservation = foreign.env.prepare_episode(batch_episode=1, release=foreign.release)
    before = _state(run.env)
    with pytest.raises(ValueError):
        run.env.validate_episode_reservation(foreign_reservation)
    _same(before, _state(run.env))
    run.env.validate_episode_reservation(first)
    _same(before, _state(run.env))


def test_authority_bootstrap_binding_and_consumption(compiled):
    run = _Run(_env(compiled))
    assert run.env.bind_boundary_authority(owner=run.boundary, role_owners=run.roles) is run.authority
    before = _state(run.env)
    with pytest.raises(ValueError):
        run.env.bind_boundary_authority(owner=_Sink(), role_owners=run.roles)
    _same(before, _state(run.env))
    reservation, reset = run.reset(1)
    assert reset.accepted.world_episode_seqs == (1, 1)
    with pytest.raises(ValueError):
        run.authority.bootstrap(first_batch_episode=1)
    with pytest.raises(ValueError):
        run.env.prepare_episode(batch_episode=2, release=run.release)
    assert run.env.reset(reservation=reservation) is reset


def test_reset_retry_after_rollout_owns_original_observation(compiled, monkeypatch):
    run = _Run(_env(compiled))
    calls = []
    original = run.env._get_observations

    def observed():
        calls.append(1)
        return original()

    monkeypatch.setattr(run.env, "_get_observations", observed)
    reservation, receipt = run.reset(1)
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
    run = _Run(_env(compiled))
    reservation = run.env.prepare_episode(batch_episode=1, release=run.release)
    accepted = run.env.reset(reservation=reservation).accepted
    before = _state(run.env)
    with pytest.raises((TypeError, ValueError)):
        run.env.activate_episode(
            accepted=accepted,
            population_receipt=SimpleNamespace(accepted=accepted),
            curiosity_receipt=run.bank.activation(accepted),
        )
    _same(before, _state(run.env))
    population = run.population.activation(accepted)
    curiosity = run.bank.activation(accepted)
    activation = run.env.activate_episode(accepted=accepted, population_receipt=population, curiosity_receipt=curiosity)
    assert run.env.activate_episode(accepted=accepted, population_receipt=population, curiosity_receipt=curiosity) is activation


def test_late_reset_failure_quarantines_without_false_rollback(compiled, monkeypatch):
    run = _Run(_env(compiled))
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
        run.env.step(torch.zeros(2, dtype=torch.long), depletion_multiplier=1.0)
    with pytest.raises((ValueError, RuntimeError)):
        run.initial()
    # No assertion of simulator or RNG rollback: reconstruction is the recovery.
    fresh = _Run(_env(compiled))
    assert fresh.reset(1)[1].accepted.world_episode_seqs == (1, 1)


def test_close_alone_blocks_save_next_release_is_save_independent(compiled):
    run = _Run(_env(compiled))
    run.reset(1)
    run.step()
    prepared, closure, dispositions = run.close(1)
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
    assert run.reset(2)[1].accepted.world_episode_seqs == (2, 2)


def test_wrong_release_and_changed_disposition_are_pure(compiled):
    run = _Run(_env(compiled))
    foreign = _Run(_env(compiled))
    before = _state(run.env)
    with pytest.raises(ValueError):
        run.env.install_boundary_release(foreign.release)
    _same(before, _state(run.env))
    run.reset(1)
    run.step((IDS[0],))
    prepared, closure, dispositions = run.close(1, (IDS[0],))
    before = _state(run.env)
    forged = replace(run.bank.receipt("prepared_dispositions", **dispositions.payload))
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
    run = _Run(_env(compiled))
    run.reset(1)
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
    run = _Run(_env(compiled))
    run.reset(1)
    run.step((IDS[0],))
    before = _state(run.env)
    with pytest.raises(ValueError):
        run.env.abandon_episode(accepted=run.accepted, reason="empty_participation")
    _same(before, _state(run.env))


def test_initial_snapshot_repeat_restore_and_first_real_reset(compiled):
    run = _Run(_env(compiled))
    before = _state(run.env)
    state = run.initial()
    _same(state, run.initial())
    _same(before, _state(run.env))
    assert state["schema"] == "world-lifecycle-v3" and state["kind"] == "INITIAL"
    assert state["accepted_bindings"] == []
    assert state["last_closed_episode"] is None and state["completed_boundary_key"] is None
    assert state["saved_lane_binding"] is None
    assert state["accepted_episode_seqs"] == dict.fromkeys(IDS, 0)
    restored = _restore(compiled, state, tuple(reversed(IDS)))
    assert restored.env.world_phase == "bootstrap-ready"
    assert restored.reset(1)[1].accepted.world_episode_seqs == (1, 1)
    with pytest.raises(ValueError):
        restored.initial()
    restored.step()
    _, closure, dispositions = restored.close(1)
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
    state = _Run(_env(compiled)).initial()
    state[field] = value
    target = _Run(_env(compiled), bootstrap=False)
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


def test_initial_restore_over_live_boundary_refuses(compiled):
    run = _Run(_env(compiled))
    state = run.initial()
    run.reset(1)
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
    first = _Run(_env(compiled))
    first.reset(1)
    first.step()
    _, closure, dispositions = first.close(1)
    first.release_closed(1, closure, dispositions)
    saved1 = first.completed((1,))
    old_content = deepcopy(first.events[1])
    second = _restore(compiled, saved1, tuple(reversed(IDS)))
    assert dict(second.env.accepted_episode_seqs) == dict.fromkeys(IDS, 1)
    assert second.reset(2)[1].accepted.world_ids == tuple(reversed(IDS))
    second.step((IDS[0],))
    _, closure, dispositions = second.close(2, (IDS[0],))
    second.release_closed(2, closure, dispositions)
    saved2 = second.completed((1, 2))
    assert saved2["accepted_bindings"] == [
        {"batch_episode": 1, "world_ids": list(IDS), "world_episode_seqs": [1, 1]},
        {"batch_episode": 2, "world_ids": list(reversed(IDS)), "world_episode_seqs": [2, 2]},
    ]
    third = _restore(compiled, saved2, IDS)
    restored_bindings = third.completed((1, 2))["accepted_bindings"]
    _same(saved2["accepted_bindings"], restored_bindings)
    by_batch = {binding["batch_episode"]: binding for binding in restored_bindings}
    for batch, index, world_id, sequence, _ in old_content + second.events[2]:
        assert by_batch[batch]["world_ids"][index] == world_id
        assert by_batch[batch]["world_episode_seqs"][index] == sequence
    next_receipt = third.reset(3)[1].accepted
    assert next_receipt.world_ids == IDS and next_receipt.world_episode_seqs == (3, 3)
    # No unequal-cursor fixture is passed off as reachable native history.


@pytest.mark.parametrize("damage", ["missing_latest", "duplicate_batch", "wrong_latest", "foreign_world", "bool_sequence"])
def test_completed_binding_corruption_refuses_before_install(compiled, damage):
    run = _Run(_env(compiled))
    for batch in (1, 2):
        run.reset(batch)
        run.step()
        _, closure, dispositions = run.close(batch)
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
    target = _Run(_env(compiled), bootstrap=False)
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
    run = _Run(_env(compiled))
    reservation = run.env.prepare_episode(batch_episode=1, release=run.release)
    run.env.reset(reservation=reservation)
    before = _state(run.env)
    with pytest.raises(ValueError):
        run.env.step(torch.zeros(2, dtype=torch.long), depletion_multiplier=1.0)
    with pytest.raises(ValueError):
        run.env.reset(reservation=replace(reservation, world_episode_seqs=(2, 2)))
    _same(before, _state(run.env))


def test_empty_close_and_unknown_history_reference_refuse(compiled):
    run = _Run(_env(compiled))
    run.reset(1)
    before = _state(run.env)
    with pytest.raises(ValueError):
        run.close(1, ())
    _same(before, _state(run.env))
    run.step()
    _, closure, dispositions = run.close(1)
    run.release_closed(1, closure, dispositions)
    before = _state(run.env)
    with pytest.raises(ValueError):
        run.completed((1, 12))
    _same(before, _state(run.env))


def test_initial_schema_exact_and_snapshot_isolation(compiled):
    run = _Run(_env(compiled))
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
    }
    state["world_roster"]["world_ids"].clear()
    state["accepted_episode_seqs"][IDS[0]] = 99
    assert run.initial()["world_roster"]["world_ids"] == list(IDS)
    assert run.initial()["accepted_episode_seqs"] == dict.fromkeys(IDS, 0)


@pytest.mark.parametrize("mode", ["wrong_kind", "extra_key", "changed_manifest", "wrong_seed", "unknown_member"])
def test_restore_identity_and_kind_mismatch_refuse(compiled, mode):
    state = _Run(_env(compiled)).initial()
    target = _Run(_env(compiled), bootstrap=False)
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
    run = _Run(_env(compiled))
    run.reset(1)
    run.step()
    _, closure, dispositions = run.close(1)
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
    run = _Run(_env(compiled))
    run.reset(1)
    run.step()
    _, closure, dispositions = run.close(1)
    run.release_closed(1, closure, dispositions)
    state = run.completed((1,))
    state["last_closed_episode"][field] = value
    target = _Run(_env(compiled), bootstrap=False)
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
    run = _Run(_env(compiled))
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
        run.reset(1)
        run.step()
        _, closure, dispositions = run.close(1)
        before = _state(run.env)
        with pytest.raises(ValueError):
            run.release_closed(1, closure, dispositions)
    _same(before, _state(run.env))


def test_prepared_close_refuses_intervening_rollout(compiled):
    run = _Run(_env(compiled))
    run.reset(1)
    run.step((IDS[0],))
    content = ((1, 0, IDS[0], 1, "interface-outcome"),)
    dispositions = run.bank.receipt(
        "prepared_dispositions",
        accepted=run.accepted,
        boundary_key=1,
        completion_content=content,
        participated_world_ids=(IDS[0],),
        dispositions=((IDS[0], "completed"), (IDS[1], "retired_nonparticipating")),
    )
    prepared = run.env.prepare_episode_close(
        accepted=run.accepted,
        boundary_key=1,
        completion_content=content,
        participated_world_ids=(IDS[0],),
        dispositions=dispositions,
    )
    run.step(IDS)
    before = _state(run.env)
    with pytest.raises(ValueError):
        run.env.freeze_episode_close(prepared)
    _same(before, _state(run.env))


def test_closure_installed_before_acknowledgement_retries_once(compiled, monkeypatch):
    run = _Run(_env(compiled))
    run.reset(1)
    run.step()
    original = run.env.close_episode
    captured = []

    def interrupted(prepared, **kwargs):
        assert run.env.world_phase == "boundary-pending"
        frozen = _state(run.env)
        with pytest.raises(ValueError):
            run.env.step(torch.zeros(2, dtype=torch.long), depletion_multiplier=1.0)
        assert run.env.freeze_episode_close(prepared) is prepared
        _same(frozen, _state(run.env))
        closure = original(prepared, **kwargs)
        captured.append((prepared, kwargs, closure))
        raise RuntimeError("after closure installation")

    monkeypatch.setattr(run.env, "close_episode", interrupted)
    with pytest.raises(RuntimeError, match="after closure installation"):
        run.close(1)
    prepared, kwargs, closure = captured[0]
    before = _state(run.env)
    assert run.env.freeze_episode_close(prepared) is prepared
    assert original(prepared, **kwargs) is closure
    _same(before, _state(run.env))
    assert run.env.world_phase == "closed-awaiting-release"
    run.release_closed(1, closure, closure.dispositions)
    assert run.reset(2)[1].accepted.world_episode_seqs == (2, 2)
