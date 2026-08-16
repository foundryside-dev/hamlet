"""The ONE closed vocabulary of observation semantic types (PDR-0047, DIV-005).

A compiled observation field carries exactly one of these. The value is load-bearing three
ways: it is concatenated into the field's provenance UUID, it is mirrored into the VFS
observation field that feeds `observation_schema_hash`, and it names the field's slice in
`observation_activity.group_slices` — how structured encoders (and the meter block's
consumers) address a run of dimensions without knowing any field's name.

Every place that declares, emits, or stores a semantic type references THIS module. Before it
existed there were three disagreeing vocabularies (five schema classes, the compiler's
hardcoded literals, and a name-inferring adapter) and no authority; the compiler emitted
`"effects"`, which no schema permitted, and nothing caught it because the DTO field was
`str | None` (hamlet-2fe1c34ebb).

Members, and who assigns them (PDR-0047 rule 3 — the compiler emits only from this set):

- `spatial`    — substrate-derived position / grid / window blocks. Compiler-assigned.
- `bars`       — THE METER BLOCK. Compiler-assigned to meter fields only. Reserved: the
                 runtime publishes meter columns into every bars-group field and the meter
                 encoder is sized from the group, so an authored variable may not join it.
- `affordance` — the affordance-at-position block. Compiler-assigned.
- `effects`    — the observable-effects block. Compiler-assigned. Admitted to the vocabulary
                 by DIV-005 as a deliberate extension (PDR-0016): it is a real compiled block
                 with its own group slice, and folding it into `custom` would destroy the
                 grouping the structured encoders exist to use.
- `temporal`   — the compiler's temporal-features block, and any authored variable the author
                 declares temporal (an agent clock, say).
- `custom`     — authored variables with no other grouping. Never a default: an author writes it.

`SEMANTIC_GROUP_ORDER` is the fixed layout order of the groups in the observation vector. The
compiler stable-partitions its field list by it, which is what lets an author choose ANY
member for a variable without breaking group contiguity — and which is the identity on every
shipped pack's layout, because the compiler already emitted its blocks in this order.
"""

from __future__ import annotations

from typing import Final, Literal, get_args

SemanticType = Literal["bars", "spatial", "affordance", "effects", "temporal", "custom"]

SEMANTIC_TYPES: Final[frozenset[str]] = frozenset(get_args(SemanticType))

# Layout order of groups in the observation vector. Matches the order the compiler emits
# its own blocks; pinned by test against default_curriculum's measured layout.
SEMANTIC_GROUP_ORDER: Final[tuple[str, ...]] = ("spatial", "bars", "affordance", "effects", "custom", "temporal")

# The one member an AUTHORED variable may not declare — see `bars` above.
METER_BLOCK_SEMANTIC: Final[str] = "bars"


def require_semantic_type(value: object, *, where: str) -> str:
    """Return `value` if it is a vocabulary member; raise with the rule otherwise.

    Used at the compiled DTO boundary so the compiler is held to the same closed set an
    author is — a `str` field would let an off-vocabulary literal through silently.
    """
    if not isinstance(value, str) or value not in SEMANTIC_TYPES:
        raise ValueError(
            f"{where}: semantic_type {value!r} is not in the closed vocabulary "
            f"{sorted(SEMANTIC_TYPES)}. The set is defined once, in townlet.vfs.semantic_type; "
            "extending it is a decision (PDR-0016), not a literal at a call site."
        )
    return value


__all__ = [
    "METER_BLOCK_SEMANTIC",
    "SEMANTIC_GROUP_ORDER",
    "SEMANTIC_TYPES",
    "SemanticType",
    "require_semantic_type",
]
