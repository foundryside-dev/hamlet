"""Real standalone POP failures preserve their cause and quarantine both owners."""

from __future__ import annotations

from typing import Any

import pytest
import torch

from tests.test_townlet.regressions.bac.test_parent_intrinsic_handoff import IDS, assert_failed, make_parent
from tests.test_townlet.regressions.bac.test_parent_intrinsic_handoff import compiled as compiled


@pytest.mark.parametrize("scope", ("shared", "per_world"))
@pytest.mark.parametrize("cleanup_raises", (False, True), ids=("cleanup-ok", "cleanup-raises"))
@pytest.mark.parametrize("seam", ("physics", "sample"))
def test_standalone_failure_quarantines_without_replacing_cause(
    compiled: Any, monkeypatch: Any, scope: str, cleanup_raises: bool, seam: str
) -> None:
    """Catch missing sample lineage, rejected quarantine reasons, and lost primary errors."""
    rig = make_parent(compiled, "rnd", scope)
    rig.enter()
    rig.runtime.checkpoint_state()  # Establish healthy public access before the failure.
    pop, accepted = rig.population, rig.record.accepted
    primary = RuntimeError(f"injected standalone failure after actual {seam}")
    secondary = RuntimeError("injected after actual runtime and BANK quarantine")
    before_parameters = tuple(parameter.detach().clone() for parameter in pop.q_network.parameters())
    physical_calls: list[None] = []
    sampled: list[Any] = []
    sample_lineages: list[Any] = []
    cleanup_calls: list[tuple[str, Any, str]] = []
    completed_cleanup: list[str] = []
    physical_step = rig.env.step
    sample = pop.replay_buffer.sample_batch
    quarantine = rig.runtime.quarantine_episode
    abandon = rig.env.abandon_episode

    def physical_step_then_fail(*args: Any, **kwargs: Any) -> Any:
        physical_calls.append(None)
        result = physical_step(*args, **kwargs)
        if seam == "physics":
            raise primary
        return result

    def sample_then_fail(request: Any, *, lineage: Any) -> Any:
        sample_lineages.append(lineage)
        assert lineage is None
        sampled.append(sample(request, lineage=lineage))
        raise primary

    def quarantine_then_maybe_fail(*, accepted: Any, reason: str) -> None:
        cleanup_calls.append(("runtime", accepted, reason))
        quarantine(accepted=accepted, reason=reason)
        completed_cleanup.append("runtime")
        if cleanup_raises:
            raise secondary

    def observe_abandon(*, accepted: Any, reason: str) -> Any:
        cleanup_calls.append(("env", accepted, reason))
        result = abandon(accepted=accepted, reason=reason)
        completed_cleanup.append("env")
        return result

    monkeypatch.setattr(rig.env, "step", physical_step_then_fail)
    monkeypatch.setattr(pop.replay_buffer, "sample_batch", sample_then_fail)
    monkeypatch.setattr(rig.runtime, "quarantine_episode", quarantine_then_maybe_fail)
    monkeypatch.setattr(rig.env, "abandon_episode", observe_abandon)

    with pytest.raises(Exception) as raised:
        pop.step_population(rig.env)
    assert raised.value is primary
    assert len(physical_calls) == rig.env.global_tick == 1
    assert [owner for owner, _, _ in cleanup_calls] == ["runtime", "env"]
    assert all(token is accepted and reason == "runtime_failure" for _, token, reason in cleanup_calls)
    assert completed_cleanup == ["runtime", "env"]
    notes = getattr(primary, "__notes__", [])
    if cleanup_raises:
        assert len(notes) == 1 and repr(secondary) in notes[0]
    else:
        assert not notes

    if seam == "sample":
        assert sample_lineages == [None] and len(sampled) == 1
        assert sampled[0].rewards.shape == (2,)
        assert pop.replay_buffer.retained_transitions == len(IDS)
        assert_failed(rig, "advanced", 1)
    else:
        assert not sample_lineages and not sampled
        assert pop.replay_buffer.retained_transitions == 0
        assert_failed(rig, "executing", 0)
    assert pop.training_step_counter == pop.clock_ledger.optimizer_updates == 0
    assert all(
        torch.equal(parameter.detach(), before) for parameter, before in zip(pop.q_network.parameters(), before_parameters, strict=True)
    )
    assert rig.env.world_phase == "quarantined"
    with pytest.raises(RuntimeError):
        rig.runtime.checkpoint_state()
    with pytest.raises(RuntimeError):
        pop.step_population(rig.env)
    assert len(physical_calls) == 1
    assert len(cleanup_calls) == 2
    assert_failed(rig, "advanced" if seam == "sample" else "executing", 1 if seam == "sample" else 0)
