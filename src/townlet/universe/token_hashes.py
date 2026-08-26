"""Canonical TokenSpec hash helpers (token-obs spec §5).

Home of the three token-observation identity hashes:

- ``token_type_schema_hash`` — the TRANSFER contract (per-type payload schemas);
- ``layout_hash`` — the FLAT-NET contract (capacities, slot bindings, total_dims);
- ``observation_schema_hash`` — REDEFINED at the unit-3 cut over the TokenSpec
  type-schema + slot-binding CONTENT (spec §5): it occupies slot 2 of the unchanged
  four-term ``compute_vfs_hash`` composition (vfs/schema_hashes.py), so ``vfs_hash``
  moves everywhere at the cut as a consequence — DIV-008's registered movement.

These lived in ``vfs/schema_hashes.py`` while the token path ran alongside the old
observation path; the move here resolves that module's vfs → universe layering
inversion (task-7 review M3, ruled "revisit at Task 10 with the swap").
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from townlet.universe.dto.token_spec import TOKEN_TYPE_FILLER_KIND, TokenSpec

__all__ = [
    "canonical_observation_schema",
    "canonical_token_layout",
    "canonical_token_type_schema",
    "compute_observation_schema_hash",
    "compute_token_layout_hash",
    "compute_token_type_schema_hash",
]


def canonical_token_type_schema(spec: TokenSpec) -> dict[str, Any]:
    """The type-schema payload of a TokenSpec — the TRANSFER contract (token-obs spec §5).

    Two universes whose type schemas hash equal can exchange per-type encoder weights
    (ModuleDict keys). Deliberately EXCLUDES capacities and slot bindings: entity variation
    goes into token count, never payload width (spec §1 first invariant), so a pack with 8
    meters and a pack with 3 share this hash. The engine constants that shape payloads
    (MAX_POSITION_RANK, VALUE_BLOCK_WIDTH, EFFECT_SUMMARY_K, every vocabulary one-hot) are
    covered through the payload FEATURE NAMES, which spell them out member by member —
    an enum member added anywhere in the descriptor block moves this hash.
    """
    return {
        "encoding_version": spec.encoding_version,
        "types": [
            {
                "type_name": t.type_name,
                "filler_kind": TOKEN_TYPE_FILLER_KIND[t.type_name],
                "payload_features": list(t.payload_features),
            }
            for t in spec.types
        ],
    }


def compute_token_type_schema_hash(spec: TokenSpec) -> str:
    """SHA-256 of the canonical token type-schema payload (transfer contract)."""
    return _hash_payload(canonical_token_type_schema(spec))


def canonical_token_layout(spec: TokenSpec) -> dict[str, Any]:
    """The serialization-layout payload of a TokenSpec — the FLAT-NET contract (spec §5).

    Strictly stronger than the type-schema payload: it adds capacities, slot-binding order
    and identity (which filler owns which slot — a flat reader's dims are positional, so a
    re-bound slot changes what a dim MEANS even at equal width), and `total_dims`.
    Deliberately EXCLUDES `SlotBinding.static_signature`: that is slot CONTENT (what the
    descriptor block will publish), not layout — a re-declared initial value moves what the
    net sees, not where (PDR-0033 narrowness; pinned by test).
    """
    return {
        "encoding_version": spec.encoding_version,
        "total_dims": spec.total_dims,
        "types": [
            {
                "type_name": t.type_name,
                "payload_features": list(t.payload_features),
                "capacity": t.capacity,
                "slot_bindings": [
                    {
                        "slot_index": binding.slot_index,
                        "filler_kind": binding.filler_kind,
                        "filler_ref": binding.filler_ref,
                    }
                    for binding in t.slot_bindings
                ],
            }
            for t in spec.types
        ],
    }


def compute_token_layout_hash(spec: TokenSpec) -> str:
    """SHA-256 of the canonical token layout payload (flat-net contract)."""
    return _hash_payload(canonical_token_layout(spec))


def canonical_observation_schema(spec: TokenSpec) -> dict[str, Any]:
    """The observation-schema payload — type schema + slot-binding CONTENT (spec §5).

    The strongest of the three: the layout payload plus each slot's compiled
    ``static_signature`` (the descriptor-block content the runtime will publish for that
    slot). Two universes equal under this hash produce identically-shaped AND
    identically-annotated observations; a re-declared initial value or normalization
    parameter moves this hash without moving ``layout_hash``.
    """
    layout = canonical_token_layout(spec)
    for type_entry, token_type in zip(layout["types"], spec.types, strict=True):
        for binding_entry, binding in zip(type_entry["slot_bindings"], token_type.slot_bindings, strict=True):
            binding_entry["static_signature"] = None if binding.static_signature is None else [float(x) for x in binding.static_signature]
    return layout


def compute_observation_schema_hash(spec: TokenSpec) -> str:
    """SHA-256 of the canonical observation-schema payload (type schema + slot content).

    This is the value that enters slot 2 of ``compute_vfs_hash``'s four-term composition
    — the composition itself is structurally untouched (DIV-008's contract).
    """
    return _hash_payload(canonical_observation_schema(spec))


def _hash_payload(payload: Any) -> str:
    canonical_json = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
