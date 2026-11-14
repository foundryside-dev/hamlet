"""Genuine ENV/BANK composition controls, not POP/native-runner qualification.

The component owner compares its actual captured BANK state and records its real
world-install journal. Other role identities confer no native-owner attestation.
"""

from __future__ import annotations

from copy import copy
from pathlib import Path
from threading import Thread
from typing import Any

import numpy as np
import pytest
import torch

from townlet.config.world_roster import WorldRosterDeclaration, world_binding
from townlet.environment.vectorized_env import WorldReceiptIssuer
from townlet.exploration.scoped_curiosity import CuriosityBank
from townlet.exploration.world_curiosity_state import WorldCuriosityDescriptor
from townlet.universe.compiler import UniverseCompiler

IDS = ("restore-A", "restore-B")
ROLES = ("population", "curiosity", "curriculum", "exploration", "network", "optimizer", "scheduler", "replay", "selection")


def equal(left: Any, right: Any) -> None:
    if isinstance(left, torch.Tensor):
        assert isinstance(right, torch.Tensor) and left.dtype == right.dtype and left.device == right.device
        assert torch.equal(left, right)
    elif isinstance(left, np.ndarray):
        assert isinstance(right, np.ndarray) and left.dtype == right.dtype and left.shape == right.shape
        assert np.array_equal(left, right)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            equal(left[key], right[key])
    elif isinstance(left, (tuple, list)):
        assert type(left) is type(right) and len(left) == len(right)
        for a, b in zip(left, right):
            equal(a, b)
    else:
        assert left == right


@pytest.fixture(scope="module")
def compiled():
    return UniverseCompiler().compile(Path("configs/test/token_set_smoke"), primary_level="L0_test", use_cache=False)


class Component:
    def __init__(self, compiled, manual: bool):
        selected = compiled.get_level(compiled.metadata.primary_level)
        self.roster = WorldRosterDeclaration(IDS)
        training = compiled.effective_run.training
        self.env = compiled.create_environment(
            num_agents=2,
            level_name=compiled.metadata.primary_level,
            device=torch.device("cpu"),
            world_roster=self.roster,
            training_seed=training.seed,
            lane_world_ids=IDS,
        )
        policy = compiled.effective_run.exploration
        descriptor = WorldCuriosityDescriptor.from_policy(
            policy,
            world_ids=IDS,
            observation_dim=selected.token_spec.total_dims,
            action_dim=selected.action_metadata.total_actions,
            training_seed=training.seed,
        )
        self.allocations = []
        self.bank = CuriosityBank(
            policy=policy,
            descriptor=descriptor,
            device=torch.device("cpu"),
            validate_accepted_episode=self.env.validate_accepted_episode,
            issuer_factory=lambda bank: WorldReceiptIssuer(owner=bank),
            report_allocation=self.allocations.append,
        )
        roles = {role: object() for role in ROLES}
        roles["curiosity"] = self.bank
        self.native_owner = roles["population"]
        self.active_attempt = None
        self.foreign_env = None
        self.authority = self.env.bind_boundary_authority(owner=self, role_owners=roles)
        self.manual = self.env.bind_manual_execution(population_owner=roles["population"]) if manual else None
        self.bank_state = self.bank.checkpoint_state()
        self.world_state = {
            "schema": "world-lifecycle-v4",
            "kind": "INITIAL",
            "next_batch_episode": 0,
            "world_roster": self.roster.to_dict(),
            "manifest_digest": self.roster.manifest_digest,
            "roster_semantic_identity": self.roster.semantic_identity,
            "training_seed": training.seed,
            "execution_identity": self.env.semantic_execution_identity,
            "saved_lane_binding": None,
            "destination_lane_binding": world_binding(IDS),
            "accepted_episode_seqs": dict.fromkeys(IDS, 0),
            "last_closed_episode": None,
            "completed_boundary_key": None,
            "accepted_bindings": [],
            "vfs_random_context": self.env.vfs_random_state(),
        }
        self.prepared = self.prepare_world()
        self.comparisons = []
        self.journal = []
        self.issuer = WorldReceiptIssuer(owner=self)

    def prepare_world(self):
        return self.env.prepare_world_restore(
            kind="INITIAL",
            state=self.world_state,
            world_roster=self.roster,
            destination_world_ids=IDS,
            semantic_execution_identity=self.env.semantic_execution_identity,
        )

    def compare(self, *, prepared, curiosity_state):
        assert prepared is self.prepared
        equal(prepared.state, self.world_state)
        equal(curiosity_state, self.bank_state)
        self.comparisons.append(prepared)

    def finalize(self, *, restored):
        from townlet.environment.restore_attempt import validate_restore_finalizer

        validate_restore_finalizer(attempt=self.active_attempt, owner=self.native_owner, restored=restored)
        validate_restore_finalizer(attempt=self.active_attempt, owner=self.native_owner, restored=restored)
        validate_restore_finalizer(attempt=self.active_attempt, owner=self.env, restored=restored)
        with pytest.raises(ValueError):
            validate_restore_finalizer(attempt=self.active_attempt, owner=self.foreign_env, restored=restored)
        assert self.env.world_phase == "bootstrap-ready"
        assert restored.next_batch_episode == self.world_state["next_batch_episode"]
        assert dict(self.env.accepted_episode_seqs) == self.world_state["accepted_episode_seqs"]
        self.journal.append(restored)

    def boundary(self):
        # This is a component's actual matching world/BANK proof only, not an
        # attestation that the identity-only network/replay role slots were loaded.
        return self.issuer.issue(
            kind="restored_boundary",
            payload={
                "kind": "INITIAL",
                "state": self.world_state,
                "prepared": self.prepared,
            },
        )

    def attempt(self):
        return self.authority.restore_bank_attempt(
            prepared=self.prepared,
            bank=self.bank,
            validate_parent_restore=self.compare,
            finalize_component=self.finalize,
        )


@pytest.mark.parametrize("manual", (False, True))
def test_real_bank_install_and_component_journal(compiled, manual):
    from townlet.environment.restore_attempt import validate_restore_finalizer

    rig = Component(compiled, manual)
    rig.foreign_env = Component(compiled, False).env
    with rig.attempt() as attempt:
        rig.active_attempt = attempt
        attempt.prepare_child(state=rig.bank_state, mode="initial")
        assert len(rig.comparisons) == 3
        attempt.issue_release(boundary=rig.boundary())
        attempt.install_child()
        assert len(rig.comparisons) == 4
        attempt.install_world()
        for owner in (rig.native_owner, rig.env):
            with pytest.raises(ValueError):
                validate_restore_finalizer(attempt=attempt, owner=owner, restored=rig.env._world_release)
        release = attempt.finish()
        for owner in (rig.native_owner, rig.env):
            with pytest.raises(ValueError):
                validate_restore_finalizer(attempt=attempt, owner=owner, restored=release)
        attempt.abort()  # COMPLETE must not become revoked by later cleanup.
    assert rig.journal == [release]
    assert rig.env.world_phase == "bootstrap-ready"
    equal(rig.bank.checkpoint_state(), rig.bank_state)
    assert rig.env.accepted_binding_batches() == ()
    reservation = rig.env.prepare_episode(batch_episode=release.next_batch_episode, release=release)
    rig.env.reset(reservation=reservation)
    with pytest.raises(ValueError):
        rig.env.accepted_binding_batches()


def test_history_export_requires_an_installed_boundary(compiled):
    rig = Component(compiled, True)
    with pytest.raises(ValueError):
        rig.env.accepted_binding_batches()


def test_early_exit_revokes_only_selected_preparation(compiled):
    rig = Component(compiled, True)
    other = rig.prepare_world()
    with rig.attempt():
        with pytest.raises(ValueError):
            rig.authority.restored(restore=rig.prepared, boundary=rig.boundary())
    assert rig.env.world_phase == "fresh-bound"
    with rig.env.retain_parent_custody() as scope:
        with pytest.raises(ValueError):
            scope.validate_prepared_restore(prepared=rig.prepared)
        scope.validate_prepared_restore(prepared=other)
    assert not rig.comparisons and not rig.journal
    equal(rig.bank.checkpoint_state(), rig.bank_state)


def test_attempt_cannot_be_copied_borrowed_or_reused(compiled):
    rig = Component(compiled, False)
    errors = []
    with rig.attempt() as attempt:
        with pytest.raises(TypeError):
            copy(attempt)

        def foreign():
            try:
                attempt.prepare_child(state=rig.bank_state, mode="initial")
            except BaseException as error:
                errors.append(error)

        thread = Thread(target=foreign)
        thread.start()
        thread.join(timeout=5)
        assert not thread.is_alive() and len(errors) == 1 and isinstance(errors[0], ValueError)
        with pytest.raises(ValueError):
            with rig.attempt():
                pytest.fail("nested attempt entered")
    with pytest.raises(ValueError):
        attempt.prepare_child(state=rig.bank_state, mode="initial")


@pytest.mark.parametrize("cut", ("world", "finalizer"))
def test_actual_child_publication_then_failure_fences_receiver(compiled, monkeypatch, cut):
    rig = Component(compiled, True)
    marker = RuntimeError("actual downstream cut")

    def fail(**kwargs):
        raise marker

    if cut == "finalizer":
        rig.finalize = fail
    with pytest.raises(RuntimeError) as failure:
        with rig.attempt() as attempt:
            attempt.prepare_child(state=rig.bank_state, mode="initial")
            attempt.issue_release(boundary=rig.boundary())
            attempt.install_child()
            if cut == "world":
                monkeypatch.setattr(rig.env, "install_world_restore", fail)
            attempt.install_world()
            attempt.finish()
    assert failure.value is marker
    assert rig.env._world_restore_terminal is True
    for action in (
        rig.env.get_action_masks,
        rig.env.get_affordance_positions,
        rig.env.vfs_random_state,
        rig.env.accepted_binding_batches,
        rig.prepare_world,
    ):
        with pytest.raises(ValueError):
            action()
    with pytest.raises(ValueError):
        rig.manual.step(accepted=None, actions=torch.zeros(2, dtype=torch.int64), depletion_multiplier=1.0)
    assert not rig.journal


@pytest.mark.parametrize("request_kind", ("damaged_state", "missing_private_initialization"))
def test_caught_preparation_error_cannot_continue(compiled, request_kind):
    rig = Component(compiled, False)
    damaged = dict(rig.bank_state, schema="invalid-current-schema")
    with rig.attempt() as attempt:
        with pytest.raises((TypeError, ValueError)):
            if request_kind == "damaged_state":
                attempt.prepare_child(state=damaged, mode="initial")
            else:
                attempt.prepare_private_initialization(state=rig.bank_state, initialization=None)
        with pytest.raises(ValueError):
            attempt.prepare_child(state=rig.bank_state, mode="initial")
        with pytest.raises(ValueError):
            attempt.issue_release(boundary=rig.boundary())
    assert not rig.journal


@pytest.mark.parametrize("operation", ("prepare", "install"))
def test_native_layout_rejects_unissued_parent_and_handle(compiled, operation):
    rig = Component(compiled, False)
    before = rig.env.get_affordance_positions()
    with pytest.raises(ValueError):
        if operation == "prepare":
            rig.env.prepare_native_layout(before, parent_plan=object())
        else:
            rig.env.install_native_layout(prepared=object(), parent_plan=object(), attempt=object(), restored=object())
    equal(rig.env.get_affordance_positions(), before)
