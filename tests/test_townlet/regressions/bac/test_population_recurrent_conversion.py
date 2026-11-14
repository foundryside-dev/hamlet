"""Real POP replay conversion before ENV binds the nine component owners."""

from __future__ import annotations

import copy
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.test_townlet.regressions.bac.test_parent_intrinsic_handoff import IDS, equal, make_parent
from townlet.training.sequential_replay_buffer import SequentialReplayBuffer
from townlet.universe.compiler import UniverseCompiler


@pytest.fixture
def recurrent_packs(tmp_path: Path) -> tuple[Any, Any]:
    source = Path("configs/test/bac_remediation/recurrent")
    destination = tmp_path / "recurrent_per"
    shutil.copytree(source, destination)  # Authored configuration data only.
    brain_path = destination / "brain.yaml"
    brain = yaml.safe_load(brain_path.read_text())
    brain["replay"].update(prioritized=True, priority_alpha=0.6, priority_beta=0.4, priority_beta_annealing=True)
    brain_path.write_text(yaml.safe_dump(brain, sort_keys=False))
    return (
        UniverseCompiler().compile(source, primary_level="L0_0_minimal", use_cache=False),
        UniverseCompiler().compile(destination, primary_level="L0_0_minimal", use_cache=False),
    )


def test_nonpristine_captured_uniform_to_per_preserves_rows_and_masks(recurrent_packs: tuple[Any, Any]) -> None:
    """Missing ordinary-operation lineage must not break POP's actual conversion branch."""
    uniform, prioritized = recurrent_packs
    source = make_parent(uniform)
    source.enter()
    for _ in range(3):
        source.population.step_population(source.env)
    source.complete()
    source_replay = source.population.replay_buffer
    captured = copy.deepcopy(source_replay.serialize())
    assert captured["format_version"] == 6
    assert captured["num_transitions"] == 3 * len(IDS)
    assert all(episode["legality_recorded"].all() for episode in captured["episodes"])
    assert all(episode["next_action_masks"].shape[1] == source.population.action_dim for episode in captured["episodes"])

    target = make_parent(prioritized)
    pop = target.population
    assert target.boundary is None
    installed = SequentialReplayBuffer.for_replay(
        source_replay.capacity,
        source_replay.device,
        options=source_replay.replay_options,
        action_dim=source_replay.action_dim,
        legality_mode=source_replay.legality_mode,
    )
    prepared = installed.prepare_serialized(captured, expected_obs_dim=pop.current_obs.shape[1], lineage=None)
    installed.load_prepared(prepared, lineage=None)
    equal(installed.serialize(), captured)
    # This target has never bound ENV roles. Its ordinary replay is supplied before
    # binding; no already-bound owner or restore credential is replaced.
    pop.replay_buffer = installed
    pop._bind_training()

    converted = pop.replay_buffer
    assert converted is not installed
    assert converted.retained_transitions == 3 * len(IDS)
    after = converted.serialize()
    assert after["format_version"] == 7
    for field in ("episodes", "num_transitions", "action_dim", "legality_mode", "replay_options", "historical_archives"):
        equal(after[field], captured[field])
    assert after["priority_state"]["initialization"] == {
        "kind": "captured6_active_adapter",
        "source_replay_kind": "sequential",
        "source_format_version": 6,
    }
    equal(installed.serialize(), captured)
    equal(source_replay.serialize(), captured)
    assert converted.readiness(pop._replay_request()).ready
    # Conversion is idempotent; the converted owner is the one actually bound.
    pop._bind_training()
    assert pop.replay_buffer is converted
    target.bind()
    assert target.env.world_phase == "fresh-bound"


@pytest.mark.parametrize("with_transport", (False, True), ids=("archives-only", "transport-and-archives"))
def test_inspection_conversion_preserves_archives_without_training_historical_rows(
    recurrent_packs: tuple[Any, Any], with_transport: bool
) -> None:
    """Both real inspection branches must carry historical rows only as archives."""
    uniform, prioritized = recurrent_packs
    source = make_parent(uniform)
    source.enter()
    for _ in range(3):
        source.population.step_population(source.env)
    source.complete()
    source_replay = source.population.replay_buffer
    captured = copy.deepcopy(source_replay.serialize())
    required = ("observations", "actions", "rewards", "dones", "next_observations")
    optional = ("rewards_extrinsic", "rewards_intrinsic", "rewards_shaping")
    rows = [
        {key: episode[key].clone() for key in required + optional if episode.get(key) is not None} for episode in captured["episodes"][:2]
    ]
    assert len(rows) == 2
    # Public historical writer deliberately has no captured successor legality.
    # Its real serialized transport becomes an authentic inspection archive.
    old = SequentialReplayBuffer(source_replay.capacity, source_replay.device)
    old.store_episode(rows[0])
    original = copy.deepcopy(old.serialize())
    assert original["format_version"] == 5 and original["num_transitions"] > 0
    inspected = SequentialReplayBuffer(source_replay.capacity, source_replay.device)
    inspected.load_from_serialized(original, lineage=None)
    if with_transport:
        inspected.store_episode(rows[0])
        inspected.store_episode(rows[1])
    before = copy.deepcopy(inspected.serialize())
    assert before["inspection_kind"] == "sequential_replay_inspection"
    assert bool(before["legacy_transport"]["num_transitions"]) is with_transport
    assert len(inspected.historical_archives) == 1

    target = make_parent(prioritized)
    pop = target.population
    assert target.boundary is None
    pop.replay_buffer = inspected
    pop._bind_training()
    converted = pop.replay_buffer
    assert converted is not inspected
    after = converted.serialize()
    assert after["format_version"] == 7
    assert after["legality_mode"] == "captured"
    assert after["num_transitions"] == converted.retained_transitions == 0
    assert after["episodes"] == []
    assert not converted.readiness(pop._replay_request()).ready
    archives = converted.historical_archives
    expected = ([before["legacy_transport"]] if with_transport else []) + [original]
    assert len(archives) == len(expected)
    assert len({archive.source_digest for archive in archives}) == len(expected)
    for archive, transport in zip(archives, expected, strict=True):
        equal(archive.original_state, transport)
        assert archive.archived_row_count == transport["num_transitions"]
    assert archives[-1].source_digest == inspected.historical_archives[0].source_digest
    equal(inspected.serialize(), before)
    equal(source_replay.serialize(), captured)
    target.bind()
    assert target.env.world_phase == "fresh-bound"
