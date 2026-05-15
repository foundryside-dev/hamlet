"""Round-trip serialization tests for compiler metadata DTOs."""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Mapping
from dataclasses import FrozenInstanceError, is_dataclass
from pathlib import Path

import msgpack  # type: ignore[import]
import pytest
import torch

from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.dto import (
    ActionMetadata,
    ActionSpaceMetadata,
    AffordanceInfo,
    AffordanceMetadata,
    MeterInfo,
    MeterMetadata,
    ObservationField,
    ObservationSpec,
    UniverseMetadata,
)


def _to_plain(obj):
    if is_dataclass(obj):
        return {f.name: _to_plain(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, Mapping):
        return {k: _to_plain(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_to_plain(v) for v in obj]
    return obj


def test_universe_metadata_round_trip() -> None:
    """UniverseMetadata and related DTOs should survive JSON round-trip."""
    config_dir = Path("configs/test/model_config")
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_test", use_cache=False)

    metadata = compiled.metadata
    observation_spec = compiled.observation_spec
    action_meta = compiled.action_space_metadata
    meter_meta = compiled.meter_metadata
    affordance_meta = compiled.affordance_metadata

    def _round_trip(dataclass_obj, factory):
        payload = json.loads(json.dumps(_to_plain(dataclass_obj)))
        return factory(payload)

    def _meta_factory(payload: dict) -> UniverseMetadata:
        payload["meter_names"] = tuple(payload["meter_names"])
        payload["meter_name_to_index"] = payload["meter_name_to_index"]
        payload["affordance_ids"] = tuple(payload["affordance_ids"])
        payload["affordance_id_to_index"] = payload["affordance_id_to_index"]
        return UniverseMetadata(**payload)

    def _obs_spec_factory(payload: dict) -> ObservationSpec:
        obs_fields = tuple(ObservationField(**field) for field in payload["fields"])
        return ObservationSpec(total_dims=payload["total_dims"], fields=obs_fields, encoding_version=payload["encoding_version"])

    def _action_meta_factory(payload: dict) -> ActionSpaceMetadata:
        actions = tuple(ActionMetadata(**action) for action in payload["actions"])
        labels_raw = payload.get("labels", {})
        labels = {int(k): v for k, v in labels_raw.items()}
        return ActionSpaceMetadata(
            total_actions=payload["total_actions"],
            actions=actions,
            labels=labels,
            label_description=payload.get("label_description"),
            label_domain=payload.get("label_domain"),
        )

    def _meter_meta_factory(payload: dict) -> MeterMetadata:
        meters = tuple(MeterInfo(**meter) for meter in payload["meters"])
        return MeterMetadata(meters=meters)

    def _affordance_meta_factory(payload: dict) -> AffordanceMetadata:
        affordances = tuple(AffordanceInfo(**aff) for aff in payload["affordances"])
        return AffordanceMetadata(affordances=affordances)

    reconstructed_metadata = _round_trip(metadata, _meta_factory)
    reconstructed_obs = _round_trip(observation_spec, _obs_spec_factory)
    reconstructed_action_meta = _round_trip(action_meta, _action_meta_factory)
    reconstructed_meter_meta = _round_trip(meter_meta, _meter_meta_factory)
    reconstructed_affordance_meta = _round_trip(affordance_meta, _affordance_meta_factory)

    assert reconstructed_metadata == metadata
    assert reconstructed_obs == observation_spec
    assert reconstructed_action_meta == action_meta
    assert reconstructed_meter_meta == meter_meta
    assert reconstructed_affordance_meta == affordance_meta


def test_compiled_universe_msgpack_round_trip(tmp_path: Path) -> None:
    compiler = UniverseCompiler()
    compiled = compiler.compile(Path("configs/test/model_config"), primary_level="L0_test")

    artifact_path = tmp_path / "compiled.msgpack"
    compiled.save_to_cache(artifact_path)
    reconstructed = CompiledUniverse.load_from_cache(artifact_path)

    assert reconstructed.observation_activity.active_dim_count > 0
    assert reconstructed.observation_activity == compiled.observation_activity
    assert reconstructed.metadata == compiled.metadata
    assert reconstructed.observation_spec == compiled.observation_spec
    assert reconstructed.action_space_metadata == compiled.action_space_metadata
    assert reconstructed.meter_metadata == compiled.meter_metadata
    assert reconstructed.affordance_metadata == compiled.affordance_metadata
    assert "base_depletions" not in compiled.to_dict()["optimization_data_raw"]
    assert torch.equal(
        reconstructed.optimization_data.action_mask_table,
        compiled.optimization_data.action_mask_table,
    )
    with pytest.raises(FrozenInstanceError):
        reconstructed.metadata = None  # type: ignore[attr-defined]


def test_compiled_universe_schema_version_guard(tmp_path: Path) -> None:
    compiler = UniverseCompiler()
    compiled = compiler.compile(Path("configs/test/model_config"), primary_level="L0_test", use_cache=False)
    artifact_path = tmp_path / "compiled.msgpack"
    compiled.save_to_cache(artifact_path)

    # Fresh artifact should load normally
    loaded = CompiledUniverse.load_from_cache(artifact_path)
    assert loaded.metadata == compiled.metadata

    # Tamper with schema version to simulate stale cache
    payload = msgpack.unpackb(artifact_path.read_bytes(), raw=False, strict_map_key=False)
    payload["compiled_schema_version"] = "0.0-test"
    tampered_path = tmp_path / "tampered.msgpack"
    tampered_path.write_bytes(msgpack.packb(payload, use_bin_type=True))

    with pytest.raises(ValueError, match="schema mismatch"):
        CompiledUniverse.load_from_cache(tampered_path)


def test_compiled_universe_requires_schema_version(tmp_path: Path) -> None:
    compiler = UniverseCompiler()
    compiled = compiler.compile(Path("configs/test/model_config"), primary_level="L0_test", use_cache=False)
    payload = compiled.to_dict()
    payload.pop("compiled_schema_version")
    missing_version_path = tmp_path / "missing-schema-version.msgpack"
    missing_version_path.write_bytes(msgpack.packb(payload, use_bin_type=True))

    with pytest.raises(ValueError, match="missing required field 'compiled_schema_version'"):
        CompiledUniverse.load_from_cache(missing_version_path)
