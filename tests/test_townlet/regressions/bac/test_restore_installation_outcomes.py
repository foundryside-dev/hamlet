"""Actual BANK/runtime install observations, not runner or all-child qualification.

The completion-poison test must run alone in a fresh pytest process. It poisons
the real process domain deliberately; no private singleton or recovery is used.
"""

from __future__ import annotations

import copy
import gc
import shutil
import threading
import weakref
from pathlib import Path

import numpy as np
import pytest
import torch
import yaml

from townlet.config.bac_options import BaCOptions, resolve_bac_options
from townlet.config.brain_config import apply_training_overrides
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.exploration_policy import ExplorationRuntime, build_exploration, resolve_exploration_policy
from townlet.config.world_roster import WorldRosterDeclaration
from townlet.curriculum.factory import build_curriculum
from townlet.environment.vectorized_env import WorldReceiptIssuer
from townlet.exploration.rng_custody import process_rng_domain
from townlet.exploration.scoped_curiosity import CuriosityBank
from townlet.exploration.world_curiosity_state import WorldCuriosityDescriptor
from townlet.population.vectorized import VectorizedPopulation
from townlet.universe.compiler import UniverseCompiler

IDS = ("outcome-A", "outcome-B", "outcome-C", "outcome-D", "outcome-E", "outcome-F", "outcome-G", "outcome-H")


@pytest.fixture(scope="module")
def compiled(tmp_path_factory):
    source = Path("configs/test/bac_remediation/feedforward")
    pack = tmp_path_factory.mktemp("install-outcomes") / "pack"
    shutil.copytree(source, pack, ignore=shutil.ignore_patterns(".compiled"))
    path = pack / "levels/L0_0_minimal/training.yaml"
    document = yaml.safe_load(path.read_text())
    training = document["training"]
    training["replay_buffer"].update(capacity=64, batch_size=2, min_size=2)
    training["training_loop"].update(max_episodes=2, max_steps_per_episode=20)
    training["intrinsic"]["rnd"]["feature_dim"] = 8
    path.write_text(yaml.safe_dump(document, sort_keys=False))
    return UniverseCompiler().compile(pack, primary_level="L0_0_minimal", use_cache=False)


def owners(compiled, scope="shared"):
    """Fresh production owners with genuine POP cadence validators; no controller."""
    selected = compiled.get_level(compiled.metadata.primary_level)
    effective = compiled.effective_run
    device = torch.device("cpu")
    env = compiled.create_environment(
        num_agents=len(IDS),
        level_name=compiled.metadata.primary_level,
        device=device,
        world_roster=WorldRosterDeclaration(IDS),
        training_seed=selected.training.seed,
        lane_world_ids=IDS,
    )
    curriculum = build_curriculum(
        effective.training,
        curriculum_options=effective.options.curriculum,
        static_policy=effective.static_policy,
        device=device,
    )
    curriculum.initialize_population(len(IDS))
    resolved = resolve_bac_options(selected.training.bac_options, training=selected.training)
    options = resolved.options.model_dump(exclude_none=True)
    options["curiosity_scope"] = {
        "scope": scope,
        "seed_policy": "legacy_shared_v1" if scope == "shared" else "world_id_derived_v1",
    }
    drive = selected.drive.intrinsic.model_dump()
    drive["strategy"] = "rnd"
    policy = resolve_exploration_policy(
        IntrinsicStrategyConfig.model_validate(drive), selected.training, BaCOptions.model_validate(options)
    )
    descriptor = WorldCuriosityDescriptor.from_policy(
        policy,
        world_ids=IDS,
        observation_dim=selected.token_spec.total_dims,
        action_dim=selected.action_metadata.total_actions,
        training_seed=selected.training.seed,
    )
    holder = {}

    def issuer(bank):
        holder["bank"] = bank
        return WorldReceiptIssuer(owner=bank)

    def committed(**kwargs):
        return holder["population"].validate_committed_batch(**kwargs)

    def cadence(**kwargs):
        return holder["population"].validate_parent_cadence(**kwargs)

    reports = []
    runtime = build_exploration(
        policy=policy,
        descriptor=descriptor,
        device=device,
        validate_accepted_episode=env.validate_accepted_episode,
        issuer_factory=issuer,
        report_allocation=reports.append,
        validate_committed_batch=committed,
        validate_parent_cadence=cadence,
    )
    population = VectorizedPopulation.for_training(
        env=env,
        curriculum=curriculum,
        exploration=runtime,
        agent_ids=list(IDS),
        device=device,
        brain_config=apply_training_overrides(compiled.brain, selected.training),
        obs_dim=selected.token_spec.total_dims,
        action_dim=selected.action_metadata.total_actions,
        train_frequency=1,
        batch_size=2,
        sequence_length=8,
        max_grad_norm=10.0,
        tb_logger=None,
        max_episodes=2,
        max_steps_per_episode=20,
        replay_options=resolved.options.replay,
        min_transitions=2,
        replay_rng=np.random.Generator(np.random.PCG64(selected.training.seed)),
        replay_origin="authored",
        beta_vector_tick_horizon=40,
        beta_horizon_origin="authored two episodes of twenty vector ticks",
        current_vector_tick=0,
    )
    holder["population"] = population
    return runtime, holder["bank"], population


def prepare(owner):
    state = owner.checkpoint_state()
    return owner.prepare_restore(state=state, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)


def result_is(outcome, **expected):
    result = outcome.read()
    for name, value in expected.items():
        assert getattr(result, name) == value, name
    return result


@pytest.mark.parametrize("kind", ("bank", "runtime"))
@pytest.mark.parametrize("scope", ("shared", "per_world"))
def test_actual_install_result_survives_consumption_and_read_is_not_an_operation(compiled, monkeypatch, kind, scope):
    runtime, bank, population = owners(compiled, scope)
    owner = bank if kind == "bank" else runtime
    prepared = prepare(owner)
    outcome = owner.restore_installation_outcome(prepared=prepared)
    result_is(outcome, status="pending", call_entered=False, operation_entered=False, returned_normally=False)
    domain = process_rng_domain()
    with monkeypatch.context() as patch:
        patch.setattr(domain, "admission", lambda **kwargs: pytest.fail("observation opened RNG admission"))
        assert owner.restore_installation_outcome(prepared=prepared) is outcome
        assert outcome.read().status == "pending"
    owner.install_restore(prepared=prepared)
    final = result_is(
        outcome,
        status="sealed",
        call_entered=True,
        operation_entered=True,
        handle_consumed=True,
        bank_publication="complete",
        runtime_publication="not_applicable" if kind == "bank" else "complete",
        completion="succeeded",
        returned_normally=True,
        runtime_handle_consumed=kind == "runtime",
    )
    assert population.exploration is runtime
    with pytest.raises((ValueError, RuntimeError)):
        owner.restore_installation_outcome(prepared=prepared)
    with monkeypatch.context() as patch:
        patch.setattr(domain, "admission", lambda **kwargs: pytest.fail("sealed result opened RNG admission"))
        assert outcome.read() is final
    with pytest.raises((AttributeError, TypeError)):
        final.status = "pending"


@pytest.mark.parametrize("kind", ("bank", "runtime"))
def test_guard_refusal_seals_first_attempt_but_preserves_lawful_standalone_retry(compiled, kind):
    runtime, bank, _ = owners(compiled)
    owner = bank if kind == "bank" else runtime
    prepared = prepare(owner)
    outcome = owner.restore_installation_outcome(prepared=prepared)
    with owner.retain_parent_custody():
        with pytest.raises(RuntimeError):
            owner.install_restore(prepared=prepared)
    first = result_is(
        outcome,
        status="sealed",
        call_entered=True,
        operation_entered=False,
        handle_consumed=False,
        bank_publication="none",
        completion="not_entered",
        returned_normally=False,
        runtime_handle_consumed=False,
    )
    owner.install_restore(prepared=prepared)
    assert outcome.read() is first
    assert bank._publications == 1
    with pytest.raises((ValueError, RuntimeError)):
        owner.restore_installation_outcome(prepared=prepared)


def test_genuine_intervening_operation_reports_consumed_no_publication(compiled):
    _, bank, _ = owners(compiled)
    prepared = prepare(bank)
    outcome = bank.restore_installation_outcome(prepared=prepared)
    bank.checkpoint_state()  # A real operation invalidates currentness, even without learning.
    with pytest.raises((ValueError, RuntimeError)):
        bank.install_restore(prepared=prepared)
    result_is(
        outcome,
        status="sealed",
        call_entered=True,
        operation_entered=True,
        handle_consumed=True,
        bank_publication="none",
        completion="succeeded",
        returned_normally=False,
    )
    assert bank._publications == 0


@pytest.mark.parametrize("after_assignment", (False, True))
def test_dictionary_publication_fault_is_never_certified_no_publication(compiled, monkeypatch, after_assignment):
    _, bank, _ = owners(compiled)
    prepared = prepare(bank)
    outcome = bank.restore_installation_outcome(prepared=prepared)
    original = bank.__dict__

    def interrupted(self, name, value):
        if self is bank and name == "__dict__":
            if after_assignment:
                object.__setattr__(self, name, value)
            raise RuntimeError("injected actual dictionary assignment failure")
        object.__setattr__(self, name, value)

    monkeypatch.setattr(CuriosityBank, "__setattr__", interrupted)
    with pytest.raises(RuntimeError, match="actual dictionary assignment"):
        bank.install_restore(prepared=prepared)
    result_is(
        outcome,
        status="sealed",
        operation_entered=True,
        handle_consumed=True,
        bank_publication="uncertain",
        completion="succeeded",
        returned_normally=False,
    )
    assert (bank.__dict__ is original) is (not after_assignment)
    assert bank._publications == int(after_assignment)


def test_runtime_suffix_fault_preserves_actual_successful_bank_outcome(compiled, monkeypatch):
    runtime, bank, _ = owners(compiled)
    prepared = prepare(runtime)
    outcome = runtime.restore_installation_outcome(prepared=prepared)

    def interrupted(self, name, value):
        if self is runtime and name == "_state":
            raise RuntimeError("injected actual selector publication failure")
        object.__setattr__(self, name, value)

    monkeypatch.setattr(ExplorationRuntime, "__setattr__", interrupted)
    with pytest.raises(RuntimeError, match="actual selector publication"):
        runtime.install_restore(prepared=prepared)
    result_is(
        outcome,
        status="sealed",
        operation_entered=True,
        handle_consumed=True,
        bank_publication="complete",
        runtime_publication="uncertain",
        completion="succeeded",
        returned_normally=False,
        runtime_handle_consumed=False,
    )
    assert bank._publications == 1 and not bank._completion_uncertain


def test_observation_identity_thread_and_weak_lifetime(compiled):
    _, bank, _ = owners(compiled)
    prepared = prepare(bank)
    outcome = bank.restore_installation_outcome(prepared=prepared)
    with pytest.raises((TypeError, ValueError)):
        copy.copy(outcome)
    errors = []

    def foreign_thread(observation):
        try:
            observation.read()
        except (ValueError, RuntimeError) as error:
            errors.append(error)

    thread = threading.Thread(target=foreign_thread, args=(outcome,))
    thread.start()
    thread.join()
    assert len(errors) == 1 and outcome.read().status == "pending"
    bank.install_restore(prepared=prepared)
    reference = weakref.ref(outcome)
    errors.clear()  # Caught thread tracebacks are test-owned strong references.
    del outcome, prepared, thread
    gc.collect()
    assert reference() is None


def test_bank_completion_failure_retains_published_outcome_poison(compiled, monkeypatch):
    """Run this node alone: real failed completion poisons its fresh process."""
    _, bank, _ = owners(compiled)
    prepared = prepare(bank)
    outcome = bank.restore_installation_outcome(prepared=prepared)
    domain = process_rng_domain()

    def failed_completion(devices):
        raise RuntimeError("injected genuine invocation completion failure")

    monkeypatch.setattr(domain, "_complete", failed_completion)
    with pytest.raises(BaseException, match="genuine invocation completion"):
        bank.install_restore(prepared=prepared)
    final = result_is(
        outcome,
        status="sealed",
        operation_entered=True,
        handle_consumed=True,
        bank_publication="complete",
        completion="failed",
        returned_normally=False,
    )
    assert bank._completion_uncertain and bank._publications == 1
    monkeypatch.setattr(domain, "admission", lambda **kwargs: pytest.fail("post-poison result opened admission"))
    assert outcome.read() is final
