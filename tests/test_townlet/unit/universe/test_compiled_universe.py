"""Tests for CompiledUniverse Stage 7 artifact."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import msgpack  # type: ignore[import]
import pytest

from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.dto.token_spec import MAX_POSITION_RANK


@pytest.fixture(scope="module")
def compiled_payload() -> dict[str, Any]:
    compiled = UniverseCompiler().compile(Path("configs/default_curriculum"), primary_level="L0_0_minimal")
    return compiled.to_dict()


def _primary_token_spec(payload: dict[str, Any]) -> dict[str, Any]:
    primary_level = payload["metadata"]["primary_level"]
    return payload["all_levels"][primary_level]["token_spec"]


def _token_type(payload: dict[str, Any], type_name: str) -> dict[str, Any]:
    return next(entry for entry in _primary_token_spec(payload)["types"] if entry["type_name"] == type_name)


def test_compiler_returns_compiled_universe() -> None:
    compiler = UniverseCompiler()
    compiled = compiler.compile(Path("configs/default_curriculum"), primary_level="L0_0_minimal")

    assert isinstance(compiled, CompiledUniverse)
    # v2.1: universe_name comes from experiment.yaml metadata.name
    assert compiled.metadata.universe_name == "Complete Reference Example"
    assert compiled.get_level(compiled.metadata.primary_level).token_spec.total_dims == compiled.metadata.observation_dim


def test_compiled_universe_is_frozen() -> None:
    compiler = UniverseCompiler()
    compiled = compiler.compile(Path("configs/default_curriculum"), primary_level="L0_0_minimal")

    try:
        compiled.metadata = None  # type: ignore[attr-defined]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("CompiledUniverse should be frozen")


@pytest.mark.parametrize(
    "case",
    (
        "token_spec_unknown",
        "token_type_unknown",
        "slot_binding_unknown",
        "slot_binding_legacy_static_signature",
        "effect_context_unknown",
    ),
)
def test_compiled_token_artifact_rejects_unknown_and_legacy_keys(compiled_payload: dict[str, Any], case: str) -> None:
    payload = deepcopy(compiled_payload)
    token_spec = _primary_token_spec(payload)
    token_type = _token_type(payload, "self")
    binding = token_type["slot_bindings"][0]

    if case == "token_spec_unknown":
        token_spec["unknown"] = "must refuse"
    elif case == "token_type_unknown":
        token_type["unknown"] = "must refuse"
    elif case == "slot_binding_unknown":
        binding.pop("static_signature", None)
        binding["unknown"] = "must refuse"
    elif case == "slot_binding_legacy_static_signature":
        binding["static_signature"] = None
    else:
        effect_type = _token_type(payload, "effect")
        effect_type["effect_catalog_contexts"] = [
            {
                "context_ref": "effect:test",
                "fixed_payload": [0.0] * len(effect_type["payload_features"]),
                "unknown": "must refuse",
            }
        ]

    with pytest.raises(ValueError, match="token|Token|cache"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize(
    ("case", "value"),
    (
        ("position_rank", True),
        ("position_rank", -1),
        ("position_rank", MAX_POSITION_RANK + 1),
        ("position_rank", "2"),
        ("transport_version", "full-payload-legacy"),
        ("missing_transport_version", None),
    ),
)
def test_compiled_token_artifact_rejects_invalid_rank_and_transport_version(
    compiled_payload: dict[str, Any], case: str, value: object
) -> None:
    payload = deepcopy(compiled_payload)
    token_spec = _primary_token_spec(payload)
    token_spec.setdefault("position_rank", 2)
    token_spec.setdefault("transport_version", "compact-1")

    if case == "missing_transport_version":
        token_spec.pop("transport_version", None)
    else:
        token_spec[case] = value

    with pytest.raises(ValueError, match="position_rank|transport_version"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize(
    "case",
    (
        "non_effect_context_count",
        "effect_slot_contexts",
        "non_effect_catalog_contexts",
        "malformed_width",
        "nonfinite_payload",
        "out_of_bounds_payload",
        "empty_effect_ref",
        "duplicate_effect_ref",
    ),
)
def test_compiled_token_artifact_rejects_invalid_context_tables(compiled_payload: dict[str, Any], case: str) -> None:
    payload = deepcopy(compiled_payload)
    self_type = _token_type(payload, "self")
    effect_type = _token_type(payload, "effect")
    self_width = len(self_type["payload_features"])
    effect_width = len(effect_type["payload_features"])
    self_type["slot_context_payloads"] = [[0.0] * self_width]
    self_type["effect_catalog_contexts"] = []
    effect_type["slot_context_payloads"] = []
    effect_type["effect_catalog_contexts"] = []

    if case == "non_effect_context_count":
        self_type["slot_context_payloads"] = []
    elif case == "effect_slot_contexts":
        effect_type["slot_context_payloads"] = [[0.0] * effect_width]
    elif case == "non_effect_catalog_contexts":
        self_type["effect_catalog_contexts"] = [{"context_ref": "wrong", "fixed_payload": [0.0] * self_width}]
    elif case == "malformed_width":
        self_type["slot_context_payloads"] = [[0.0] * (self_width - 1)]
    elif case == "nonfinite_payload":
        self_type["slot_context_payloads"][0][0] = float("nan")
    elif case == "out_of_bounds_payload":
        self_type["slot_context_payloads"][0][0] = 1.0001
    elif case == "empty_effect_ref":
        effect_type["effect_catalog_contexts"] = [{"context_ref": "", "fixed_payload": [0.0] * effect_width}]
    else:
        context = {"context_ref": "effect:duplicate", "fixed_payload": [0.0] * effect_width}
        effect_type["effect_catalog_contexts"] = [context, deepcopy(context)]

    with pytest.raises(ValueError, match="context|payload|effect"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize("load_mode", ("from_dict", "msgpack_cache"))
def test_schema_version_refuses_before_invalid_token_payload(compiled_payload: dict[str, Any], tmp_path: Path, load_mode: str) -> None:
    payload = deepcopy(compiled_payload)
    payload["compiled_schema_version"] = "1.25"
    _primary_token_spec(payload).pop("types")

    with pytest.raises(ValueError, match="schema mismatch"):
        if load_mode == "from_dict":
            CompiledUniverse.from_dict(payload)
        else:
            cache_path = tmp_path / "old-1.25.msgpack"
            cache_path.write_bytes(msgpack.packb(payload, use_bin_type=True))
            CompiledUniverse.load_from_cache(cache_path)
