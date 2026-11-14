"""ENV-only restore currentness; portable fixtures confer no native owner proof.

These tests construct the production compiled ENV and its genuine prepared-world
records. Authored portable snapshots exercise ENV parsing/currentness, not POP,
BANK, runner checkpoint production, or continued-learning acceptance.
"""

from __future__ import annotations

import copy
import gc
import threading
import weakref
from pathlib import Path

import pytest
import torch

from townlet.config.world_roster import WorldRecord, WorldRosterDeclaration, world_binding
from townlet.environment import parent_custody, vectorized_env
from townlet.universe.compiler import UniverseCompiler

ROLES = ("population", "curiosity", "curriculum", "exploration", "network", "optimizer", "scheduler", "replay", "selection")
WORLD_IDS = ("component-A", "component-B")


@pytest.fixture(scope="module")
def compiled():
    return UniverseCompiler().compile(Path("configs/test/token_set_smoke"), primary_level="L0_test", use_cache=False)


def receiver(compiled, *, manual=False):
    roster = WorldRosterDeclaration(WORLD_IDS)
    env = compiled.create_environment(
        num_agents=2,
        level_name=compiled.metadata.primary_level,
        device=torch.device("cpu"),
        world_roster=roster,
        training_seed=42,
        lane_world_ids=WORLD_IDS,
    )
    # These owners only exercise ENV role identity. No native-owner state or
    # successful learner/controller receipt is fabricated by this fixture.
    roles = {role: object() for role in ROLES}
    authority = env.bind_boundary_authority(owner=object(), role_owners=roles)
    if manual:
        env.bind_manual_execution(population_owner=roles["population"])
    return env, roster, authority


def prepare(env, roster, state):
    return env.prepare_world_restore(
        kind=state["kind"],
        state=state,
        world_roster=roster,
        destination_world_ids=WORLD_IDS,
        semantic_execution_identity=env.semantic_execution_identity,
    )


def forbidden(*args, **kwargs):
    raise AssertionError("pure currentness entered an effectful or payload-reading path")


def snapshot(env, roster, kind):
    """Lawful parser inputs; deliberately not a native controller checkpoint."""
    context = env.vfs_random_state()
    state = {
        "schema": "world-lifecycle-v4",
        "kind": kind,
        "next_batch_episode": 0,
        "world_roster": roster.to_dict(),
        "manifest_digest": roster.manifest_digest,
        "roster_semantic_identity": roster.semantic_identity,
        "training_seed": 42,
        "execution_identity": env.semantic_execution_identity,
        "saved_lane_binding": None,
        "destination_lane_binding": world_binding(WORLD_IDS),
        "accepted_episode_seqs": dict.fromkeys(WORLD_IDS, 0),
        "last_closed_episode": None,
        "completed_boundary_key": None,
        "accepted_bindings": [],
        "vfs_random_context": context,
    }
    if kind == "COMPLETED":
        context["world_episode_seqs"] = [1, 1]
        state.update(
            next_batch_episode=1,
            saved_lane_binding=world_binding(WORLD_IDS),
            accepted_episode_seqs=dict.fromkeys(WORLD_IDS, 1),
            last_closed_episode={
                "batch_episode": 0,
                "world_ids": list(WORLD_IDS),
                "world_episode_seqs": [1, 1],
                "completion_content": {"nested": [torch.tensor([3.0]), {"event": "component-owned-content"}]},
                "participated_world_ids": list(WORLD_IDS),
            },
            completed_boundary_key=0,
            accepted_bindings=[{"batch_episode": 0, "world_ids": list(WORLD_IDS), "world_episode_seqs": [1, 1]}],
        )
    return state


@pytest.mark.parametrize("kind", ["INITIAL", "COMPLETED"])
@pytest.mark.parametrize("manual", [False, True])
@pytest.mark.parametrize("bootstrap", [False, True])
def test_pure_prepared_check_preserves_multiple_records_and_issued_bootstrap(compiled, kind, manual, bootstrap):
    env, roster, authority = receiver(compiled, manual=manual)
    issued = authority.bootstrap(first_batch_episode=0) if bootstrap else None
    state = snapshot(env, roster, kind)
    if kind == "COMPLETED" and issued is not None:
        state["last_closed_episode"]["completion_content"]["opaque"] = issued
    first, second = prepare(env, roster, state), prepare(env, roster, state)
    assert first is not second
    public_copy = first.payload
    public_copy["state"]["accepted_episode_seqs"][WORLD_IDS[0]] = 999
    if kind == "COMPLETED":
        public_copy["state"]["last_closed_episode"]["completion_content"]["nested"][0].fill_(999)
    with env.retain_parent_custody() as scope:
        assert scope.validate_prepared_restore(prepared=first) is None
        assert scope.validate_prepared_restore(prepared=second) is None
    assert env.world_phase == "fresh-bound"
    assert env._world_bootstrap is issued
    assert first.state["accepted_episode_seqs"][WORLD_IDS[0]] == (0 if kind == "INITIAL" else 1)
    if kind == "COMPLETED":
        assert first.state["last_closed_episode"]["completion_content"]["nested"][0].item() == 3.0


@pytest.mark.parametrize("changed", [False, True])
def test_prepared_check_never_reads_payload_or_enters_device_or_admission_work(compiled, monkeypatch, changed):
    env, roster, authority = receiver(compiled)
    prepared = prepare(env, roster, snapshot(env, roster, "COMPLETED"))
    rng = torch.get_rng_state().clone()
    before = (env._world_phase, env._world_generation, len(env._world_records), env._participation_failed)
    with env.retain_parent_custody() as scope:
        with monkeypatch.context() as patch:
            patch.setattr(WorldRecord, "payload", property(forbidden))
            patch.setattr(WorldRecord, "__getattr__", forbidden)
            patch.setattr(torch, "equal", forbidden)
            patch.setattr(vectorized_env, "same_value", forbidden)
            patch.setattr(vectorized_env.VFSRandomness, "state", forbidden)
            patch.setattr(vectorized_env.VFSRandomness, "validate_state", forbidden)
            patch.setattr(parent_custody, "process_rng_domain", forbidden)
            patch.setattr(env, "_require_phase", forbidden)
            patch.setattr(env, "_valid_record", forbidden)
            patch.setattr(env, "_check_committed_participation", forbidden)
            patch.setattr(authority, "_bound_env", forbidden)
            if changed:
                patch.setattr(env, "_world_revision", 1)
                with pytest.raises(ValueError):
                    scope.validate_prepared_restore(prepared=prepared)
            else:
                assert scope.validate_prepared_restore(prepared=prepared) is None
    assert before == (env._world_phase, env._world_generation, len(env._world_records), env._participation_failed)
    assert torch.equal(rng, torch.get_rng_state())


@pytest.mark.parametrize(
    "name,value",
    [
        ("_world_phase", "bootstrap-ready"),
        ("_world_generation", 1),
        ("_world_generation", False),
        ("_world_revision", 1),
        ("_world_revision", False),
        ("_world_seed", 43),
        ("_world_roster", WorldRosterDeclaration(WORLD_IDS)),
        ("_world_identity", "different-semantic-identity"),
        ("_world_ids", tuple(reversed(WORLD_IDS))),
        ("_world_cursors", {WORLD_IDS[0]: 0, WORLD_IDS[1]: 1}),
        ("_world_cursors", {WORLD_IDS[0]: False, WORLD_IDS[1]: 0}),
        ("_world_bindings", {0: {}}),
        ("_world_equal", {"unexpected": object()}),
        ("_participation_busy", True),
        ("_participation_failed", True),
        ("_exploration_bound", True),
        *[
            (name, object())
            for name in (
                "_world_accepted",
                "_world_reset",
                "_world_reservation",
                "_world_release",
                "_world_closure",
                "_world_frozen",
                "_world_consumers",
                "_world_restored",
                "_world_vfs_pending",
                "_world_last_closed",
                "_world_saved_binding",
                "_participation_pending",
                "_participation_committed",
                "_participation_reset_state",
                "_manual_close_prepared",
            )
        ],
    ],
)
def test_changed_receiving_metadata_refuses_without_poisoning_valid_preparation(compiled, monkeypatch, name, value):
    env, roster, _ = receiver(compiled)
    prepared = prepare(env, roster, snapshot(env, roster, "INITIAL"))
    with env.retain_parent_custody() as scope:
        with monkeypatch.context() as patch:
            patch.setattr(env, name, value)
            with pytest.raises(ValueError):
                scope.validate_prepared_restore(prepared=prepared)
        assert scope.validate_prepared_restore(prepared=prepared) is None
    assert env.world_phase == "fresh-bound"
    assert not env._participation_failed


@pytest.mark.parametrize(
    "field,value",
    [
        ("_tick", 1),
        ("_busy", True),
        ("_failed", True),
        ("_pending", object()),
        ("_accepted", object()),
        ("_state", {}),
        ("_stage", "completed"),
        ("_failure", ("failed", 1, None)),
    ],
)
def test_manual_receiving_session_must_remain_genuinely_quiescent(compiled, monkeypatch, field, value):
    env, roster, _ = receiver(compiled, manual=True)
    prepared = prepare(env, roster, snapshot(env, roster, "INITIAL"))
    with env.retain_parent_custody() as scope:
        with monkeypatch.context() as patch:
            patch.setattr(env._manual_session, field, value)
            with pytest.raises(ValueError):
                scope.validate_prepared_restore(prepared=prepared)
        assert scope.validate_prepared_restore(prepared=prepared) is None


def test_copied_foreign_and_replaced_payload_preparations_have_no_authority(compiled, monkeypatch):
    env, roster, _ = receiver(compiled)
    other, other_roster, _ = receiver(compiled)
    prepared = prepare(env, roster, snapshot(env, roster, "INITIAL"))
    foreign = prepare(other, other_roster, snapshot(other, other_roster, "INITIAL"))
    forged = WorldRecord(prepared.kind, env, prepared._generation, prepared._payload)
    with env.retain_parent_custody() as scope:
        for value in (foreign, forged, copy.copy(prepared), object()):
            with pytest.raises(ValueError):
                scope.validate_prepared_restore(prepared=value)
        original = prepared._payload
        try:
            object.__setattr__(prepared, "_payload", dict(original))
            with pytest.raises(ValueError):
                scope.validate_prepared_restore(prepared=prepared)
        finally:
            object.__setattr__(prepared, "_payload", original)
        assert scope.validate_prepared_restore(prepared=prepared) is None


def test_expired_foreign_thread_and_operation_bound_scopes_refuse(compiled, monkeypatch):
    env, roster, _ = receiver(compiled)
    prepared = prepare(env, roster, snapshot(env, roster, "INITIAL"))
    failures = []
    with env.retain_parent_custody() as scope:

        def foreign_thread():
            try:
                scope.validate_prepared_restore(prepared=prepared)
            except BaseException as error:
                failures.append(error)

        thread = threading.Thread(target=foreign_thread)
        thread.start()
        thread.join(timeout=5)
        assert not thread.is_alive(), "foreign-thread rejection must precede lock acquisition"
        assert len(failures) == 1 and isinstance(failures[0], ValueError)
        with monkeypatch.context() as patch:
            patch.setattr(scope, "_operation", object())
            with pytest.raises(ValueError):
                scope.validate_prepared_restore(prepared=prepared)
        with monkeypatch.context() as patch:
            patch.setattr(scope, "_pid", -1)
            with pytest.raises(ValueError):
                scope.validate_prepared_restore(prepared=prepared)
        for field, value in (("active", (object(), threading.current_thread())), ("reverse", {})):
            with monkeypatch.context() as patch:
                patch.setattr(env._env_custody, field, value)
                with pytest.raises(ValueError):
                    scope.validate_prepared_restore(prepared=prepared)
        assert scope.validate_prepared_restore(prepared=prepared) is None
    with pytest.raises(ValueError):
        scope.validate_prepared_restore(prepared=prepared)


def test_seal_does_not_keep_abandoned_world_preparation_alive(compiled):
    env, roster, _ = receiver(compiled)
    prepared = prepare(env, roster, snapshot(env, roster, "COMPLETED"))
    with env.retain_parent_custody() as scope:
        scope.validate_prepared_restore(prepared=prepared)
    reference = weakref.ref(prepared)
    key = id(prepared)
    del prepared
    gc.collect()
    assert reference() is None
    assert key not in env._world_records
