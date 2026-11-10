"""Actual ENV identity authentication; local owner receipts do not qualify BANK.

The prerequisite deliberately never looks up the proposed public method. These
tests reuse the charged real compiler/lifecycle fixture, including nine explicit
local roles, without claiming real provider, replay, runner or bank integration.
"""

from __future__ import annotations

import random
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from tests.test_townlet.regressions.bac.test_world_episode_identity import (
    IDS,
    SEED,
    _env,
    _Run,
    _same,
    _state,
)
from tests.test_townlet.regressions.bac.test_world_episode_identity import (
    compiled as compiled,
)
from townlet.config.world_roster import WorldAcceptedEpisode, WorldRosterDeclaration
from townlet.environment.vectorized_env import VectorizedHamletEnv


def _snapshot(env):
    numpy_state = np.random.get_state()
    return {
        "env": _state(env),
        "semantic_identity": env.semantic_execution_identity,
        "python_rng": random.getstate(),
        "numpy_rng": (numpy_state[0], numpy_state[1].tolist(), *numpy_state[2:]),
    }


def _quarantined_snapshot(env):
    """Observable witnesses; quarantine deliberately forbids native VFS export."""
    numpy_state = np.random.get_state()
    return {
        "phase": env.world_phase,
        "ids": env.world_ids,
        "cursors": dict(env.accepted_episode_seqs),
        "positions": env.positions.clone(),
        "meters": env.meters.clone(),
        "dones": env.dones.clone(),
        "steps": env.step_counts.clone(),
        "tick": env.global_tick,
        "semantic_identity": env.semantic_execution_identity,
        "torch_rng": torch.get_rng_state().clone(),
        "python_rng": random.getstate(),
        "numpy_rng": (numpy_state[0], numpy_state[1].tolist(), *numpy_state[2:]),
    }


def _validator(env):
    method = getattr(env, "validate_accepted_episode", None)
    assert callable(method), "actual ENV must expose public validate_accepted_episode"
    return method


def _pure_validation(env, accepted):
    method = _validator(env)
    before = _snapshot(env)
    assert method(accepted=accepted) is None
    assert method(accepted=accepted) is None
    _same(before, _snapshot(env))


def _pure_refusal(env, accepted):
    method = _validator(env)
    before = _snapshot(env)
    with pytest.raises(ValueError):
        method(accepted=accepted)
    _same(before, _snapshot(env))


def test_actual_env_lifecycle_prerequisite_without_public_validator(compiled):
    """Independent fixture control: genuine INITIAL, acceptance and next entry."""
    run = _Run(_env(compiled))
    initial = run.initial()
    assert initial["kind"] == "INITIAL"
    assert initial["accepted_bindings"] == []
    assert initial["accepted_episode_seqs"] == dict.fromkeys(IDS, 0)
    reservation = run.env.prepare_episode(batch_episode=1, release=run.release)
    run.env.validate_episode_reservation(reservation)
    receipt = run.env.reset(reservation=reservation)
    first = receipt.accepted
    assert isinstance(first, WorldAcceptedEpisode)
    assert first.world_ids == IDS and first.world_episode_seqs == (1, 1)
    assert first.batch_episode == 1
    assert run.env.world_phase == "active-awaiting-activation"
    assert receipt.observation is not None
    run.accepted = first
    run.env.activate_episode(
        accepted=first,
        population_receipt=run.population.activation(first),
        curiosity_receipt=run.bank.activation(first),
    )
    run.step()
    assert bool((run.env.step_counts > 0).all())
    _, closure, dispositions = run.close(1)
    assert run.env.world_phase == "closed-awaiting-release"
    run.release_closed(1, closure, dispositions)
    assert run.env.world_phase == "released-completed"
    second = run.reset(2)[1].accepted
    assert second is not first
    assert second.world_ids == IDS and second.world_episode_seqs == (2, 2)
    assert dict(run.env.accepted_episode_seqs) == dict.fromkeys(IDS, 2)


def test_public_authentication_accepts_real_token_repeatedly_without_reset(compiled):
    run = _Run(_env(compiled))
    accepted = run.reset(1)[1].accepted
    _pure_validation(run.env, accepted)
    run.step()
    _pure_validation(run.env, accepted)


@pytest.mark.parametrize("kind", ["copy", "constructed", "duck", "none", "changed_case", "changed_unicode"])
def test_public_authentication_refuses_unissued_identity_purely(compiled, kind):
    run = _Run(_env(compiled))
    accepted = run.reset(1)[1].accepted
    if kind == "copy":
        candidate = replace(accepted)
    elif kind == "constructed":
        candidate = WorldAcceptedEpisode(accepted.world_ids, accepted.world_episode_seqs, accepted.batch_episode, object(), 1)
    elif kind == "duck":
        candidate = SimpleNamespace(
            world_ids=accepted.world_ids, world_episode_seqs=accepted.world_episode_seqs, batch_episode=accepted.batch_episode
        )
    elif kind == "changed_case":
        candidate = replace(accepted, world_ids=(IDS[0].upper(), IDS[1]))
    elif kind == "changed_unicode":
        candidate = replace(accepted, world_ids=("é", "e\u0301"))
    else:
        candidate = None
    _pure_refusal(run.env, candidate)
    _pure_validation(run.env, accepted)


def test_public_authentication_refuses_foreign_env_with_same_public_identity(compiled):
    run = _Run(_env(compiled))
    foreign = _Run(_env(compiled))
    accepted = run.reset(1)[1].accepted
    other = foreign.reset(1)[1].accepted
    assert accepted.world_ids == other.world_ids
    assert accepted.world_episode_seqs == other.world_episode_seqs
    assert accepted.batch_episode == other.batch_episode
    assert run.env.semantic_execution_identity == foreign.env.semantic_execution_identity
    foreign_before = _snapshot(foreign.env)
    _pure_refusal(run.env, other)
    _same(foreign_before, _snapshot(foreign.env))
    _pure_validation(run.env, accepted)


def test_public_authentication_refuses_stale_token_after_valid_boundary_and_fresh_reset(compiled):
    run = _Run(_env(compiled))
    old = run.reset(1)[1].accepted
    run.step()
    _, closure, dispositions = run.close(1)
    run.release_closed(1, closure, dispositions)
    current = run.reset(2)[1].accepted
    assert current.world_episode_seqs == (2, 2)
    _pure_refusal(run.env, old)
    _pure_validation(run.env, current)


@pytest.mark.parametrize("ids", [("Case", "case"), ("é", "e\u0301")])
def test_public_authentication_preserves_exact_case_and_unicode_ids(compiled, ids):
    env = VectorizedHamletEnv(
        universe=compiled,
        level_name="L0_test",
        num_agents=2,
        device="cpu",
        world_roster=WorldRosterDeclaration.from_dict({"schema": "world-roster-v1", "world_ids": list(ids)}),
        training_seed=SEED,
        lane_world_ids=ids,
    )
    run = _Run(env)
    accepted = run.reset(1)[1].accepted
    _pure_validation(env, accepted)
    assert accepted.world_ids == ids
    assert env.world_ids == ids
    assert dict(env.accepted_episode_seqs) == dict.fromkeys(ids, 1)
    _pure_refusal(env, replace(accepted, world_ids=tuple(reversed(ids))))


def test_initial_has_no_accepted_token_to_authenticate(compiled):
    run = _Run(_env(compiled))
    assert run.initial()["accepted_bindings"] == []
    _pure_refusal(run.env, None)
    _pure_refusal(run.env, WorldAcceptedEpisode(IDS, (0, 0), 1, object(), 0))
    assert run.initial()["accepted_episode_seqs"] == dict.fromkeys(IDS, 0)


def test_public_authentication_requires_explicit_keyword_argument(compiled):
    run = _Run(_env(compiled))
    accepted = run.reset(1)[1].accepted
    method = _validator(run.env)
    before = _snapshot(run.env)
    with pytest.raises(TypeError):
        method()
    with pytest.raises(TypeError):
        method(accepted)
    _same(before, _snapshot(run.env))


def test_identity_authentication_does_not_activate_or_release_phase_permissions(compiled):
    run = _Run(_env(compiled))
    reservation = run.env.prepare_episode(batch_episode=1, release=run.release)
    receipt = run.env.reset(reservation=reservation)
    accepted = receipt.accepted
    _pure_validation(run.env, accepted)
    before = _snapshot(run.env)
    with pytest.raises(ValueError):
        run.env.step(torch.zeros(2, dtype=torch.long), depletion_multiplier=1.0)
    _same(before, _snapshot(run.env))
    run.accepted = accepted
    run.env.activate_episode(
        accepted=accepted,
        population_receipt=run.population.activation(accepted),
        curiosity_receipt=run.bank.activation(accepted),
    )
    _pure_validation(run.env, accepted)
    run.step()
    _, closure, dispositions = run.close(1)
    _pure_validation(run.env, accepted)
    before = _snapshot(run.env)
    with pytest.raises(ValueError):
        run.env.step(torch.zeros(2, dtype=torch.long), depletion_multiplier=1.0)
    with pytest.raises(ValueError):
        run.env.prepare_episode(batch_episode=2, release=run.release)
    with pytest.raises(ValueError):
        run.completed((1,))
    _same(before, _snapshot(run.env))
    run.release_closed(1, closure, dispositions)
    _pure_validation(run.env, accepted)


def test_identity_authentication_keeps_quarantine_and_physics_refusal(compiled):
    run = _Run(_env(compiled))
    accepted = run.reset(1)[1].accepted
    run.env.abandon_episode(accepted=accepted, reason="runtime_failure")
    assert run.env.world_phase == "quarantined"
    method = _validator(run.env)
    before = _quarantined_snapshot(run.env)
    for _ in range(2):
        with pytest.raises(ValueError):
            run.env.vfs_random_state()
        with pytest.raises(ValueError):
            run.env.step(torch.zeros(2, dtype=torch.long), depletion_multiplier=1.0)
        with pytest.raises(ValueError):
            run.initial()
        _same(before, _quarantined_snapshot(run.env))
        assert method(accepted=accepted) is None
        _same(before, _quarantined_snapshot(run.env))
    with pytest.raises(ValueError):
        run.env.vfs_random_state()
    with pytest.raises(ValueError):
        run.env.step(torch.zeros(2, dtype=torch.long), depletion_multiplier=1.0)
    with pytest.raises(ValueError):
        run.initial()
    _same(before, _quarantined_snapshot(run.env))
