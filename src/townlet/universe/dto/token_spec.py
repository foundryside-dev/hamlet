"""TokenSpec — the compiled token-observation artifact and its pure derivations.

Spec: docs/superpowers/specs/2026-08-22-token-observation-representation-design.md §§1–2
(token type system, TokenSpec artifact, capacity table, serialization). This module is the
ONE definition of the engine constants and payload schemas the token path dispatches on —
same discipline as `observation_feature.py`: a new token type is a new roster member plus a
new publisher, never a name to match.

What lives here (unit 3, Task 6): the frozen artifact dataclasses, the engine constants,
the per-type payload schemas (feature names in order — widths fall out of enum sizes, not
literals), the descriptor block, and the pure derivations the compiler consumes at emission
(Task 7): capacities per §2's table, the exposure refusals (boundedness / width rules /
`rank_scaled`), the compile-time indistinguishability check, the rank gate, and the
`{type: mean}` census advisory. Nothing here reads a config file or a compiled universe;
every input is a declaration-derived value the caller hands over.

Widths that are DERIVED from closed vocabularies, never written as literals:

- scope one-hot          = ``len(VariableScope)``                      (vfs/schema.py)
- semantic-type one-hot  = ``len(SEMANTIC_TYPES)``                     (vfs/semantic_type.py)
- normalization one-hot  = size of ``NormalizationSpec.kind``'s Literal (vfs/schema.py)
- interaction_type       = size of ``InteractionType``                 (config/interaction_type.py)
- effect scope one-hot   = ``len(EffectScope)``                        (config/effects_config.py)

`DESCRIPTOR_BLOCK_WIDTH` is pinned by a single test so any drift in those enums is loud.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Final, Literal, get_args

from townlet.config.effects_config import EffectScope, ReapplyPolicy
from townlet.config.interaction_type import InteractionType
from townlet.vfs.schema import NormalizationSpec, VariableDef, VariableScope
from townlet.vfs.semantic_type import SemanticType

# --------------------------------------------------------------------------- engine constants

#: Position payloads pad to this rank, with a rank feature (spec §1). A substrate of rank > 8
#: is refused at compile time; raising the constant is a superseding PDR (breaks checkpoints).
MAX_POSITION_RANK: Final[int] = 8

#: Value sub-block width. Scalar kinds use lane 0; ``cyclical_sin_cos`` lands sin/cos in lanes
#: 0–1 of ONE token (spec §1 width rule). A width-used feature accompanies the lanes.
VALUE_BLOCK_WIDTH: Final[int] = 2

#: Affordance effect summary: the k largest declared deltas by normalized magnitude (spec §1).
EFFECT_SUMMARY_K: Final[int] = 4

#: Compiling ``{type: mean}`` against a census where any one type exceeds this many tokens
#: emits a loud compile-time advisory (spec §2, "token census").
MEAN_CENSUS_ADVISORY: Final[int] = 64

TokenType = Literal["self", "meter", "affordance", "agent", "item", "effect", "variable_element"]

#: The seven live token types in engine-canonical order (spec §1 table). Serialization rows
#: concatenate in this order; the order is part of the layout hash.
TOKEN_TYPE_ROSTER: Final[tuple[TokenType, ...]] = get_args(TokenType)

#: Reserved names (spec §1): intent only, NOT settled shapes. They refuse instantiation.
RESERVED_TOKEN_TYPE_NAMES: Final[frozenset[str]] = frozenset({"relation", "message", "group"})

#: Which filler kind each live type takes (spec §3 "presence ownership"): a `static` slot is
#: bound to its filler at compile time; a `dynamic` slot is assigned at runtime and toggles
#: presence. `static` does NOT mean "always present": the §3 visibility filter still zeroes
#: presence (and payload) of any spatial token out of range under partial observability.
FillerKind = Literal["static", "dynamic"]
TOKEN_TYPE_FILLER_KIND: Final[Mapping[str, FillerKind]] = {
    "self": "static",
    "meter": "static",
    "affordance": "static",
    "agent": "dynamic",
    "item": "dynamic",
    "effect": "dynamic",
    "variable_element": "static",
}

ENCODING_VERSION: Final[str] = "token-1.0"

# --------------------------------------------------------------------------- vocabularies (read, not written)

SCOPE_VOCABULARY: Final[tuple[str, ...]] = tuple(member.value for member in VariableScope)
SEMANTIC_TYPE_VOCABULARY: Final[tuple[str, ...]] = get_args(SemanticType)
NORMALIZATION_KIND_VOCABULARY: Final[tuple[str, ...]] = get_args(NormalizationSpec.model_fields["kind"].annotation)
INTERACTION_TYPE_VOCABULARY: Final[tuple[str, ...]] = get_args(InteractionType)
EFFECT_SCOPE_VOCABULARY: Final[tuple[str, ...]] = tuple(member.value for member in EffectScope)
REAPPLY_POLICY_VOCABULARY: Final[tuple[str, ...]] = tuple(member.value for member in ReapplyPolicy)
LIFETIME_VOCABULARY: Final[tuple[str, ...]] = get_args(VariableDef.model_fields["lifetime"].annotation)
VARIABLE_TYPE_VOCABULARY: Final[tuple[str, ...]] = get_args(VariableDef.model_fields["type"].annotation)
DTYPE_VOCABULARY: Final[tuple[str, ...]] = ("float", "int", "bool")

#: VariableDef.type -> dtype flag. References and message tokens are integer ids. Pinned by
#: test to cover exactly VARIABLE_TYPE_VOCABULARY, so a new VariableDef type is loud here.
_VARIABLE_TYPE_DTYPE: Final[Mapping[str, str]] = {
    "scalar": "float",
    "vec2f": "float",
    "vec3f": "float",
    "vecNf": "float",
    "tensor1d": "float",
    "tensor2d": "float",
    "tensor3d": "float",
    "tensorNd": "float",
    "vec2i": "int",
    "vec3i": "int",
    "vecNi": "int",
    "agent_ref": "int",
    "item_ref": "int",
    "affordance_ref": "int",
    "effect_ref": "int",
    "message_token": "int",
    "bool": "bool",
}

# --------------------------------------------------------------------------- descriptor block widths

SCOPE_ONE_HOT_WIDTH: Final[int] = len(SCOPE_VOCABULARY)
SEMANTIC_TYPE_ONE_HOT_WIDTH: Final[int] = len(SEMANTIC_TYPE_VOCABULARY)
NORMALIZATION_KIND_ONE_HOT_WIDTH: Final[int] = len(NORMALIZATION_KIND_VOCABULARY)
#: Canonical parameter vector: fixed slots (min, max, clip-flag, scale) + one params-absent
#: flag. "scale" is the kind's single magnitude parameter: `period` for cyclical_sin_cos,
#: `threshold` for binary. Absent slots read 0 and the flag reads 1 when any slot is absent;
#: the kind one-hot already says which slots a kind declares, so absence is never ambiguous.
NORMALIZATION_PARAM_SLOTS: Final[tuple[str, ...]] = ("min", "max", "clip", "scale")
NORMALIZATION_PARAM_VECTOR_WIDTH: Final[int] = len(NORMALIZATION_PARAM_SLOTS) + 1
DTYPE_FLAG_WIDTH: Final[int] = len(DTYPE_VOCABULARY)
LIFETIME_ONE_HOT_WIDTH: Final[int] = len(LIFETIME_VOCABULARY)
DECLARED_INITIAL_WIDTH: Final[int] = 1
ELEMENT_COUNT_WIDTH: Final[int] = 1
#: (normalized owner slot, applicable flag) — item-profile state carries its owner slot.
OWNER_SLOT_COORDINATE_WIDTH: Final[int] = 2

DESCRIPTOR_BLOCK_FEATURES: Final[tuple[str, ...]] = (
    tuple(f"scope_{s}" for s in SCOPE_VOCABULARY)
    + tuple(f"semantic_{s}" for s in SEMANTIC_TYPE_VOCABULARY)
    + tuple(f"norm_kind_{k}" for k in NORMALIZATION_KIND_VOCABULARY)
    + tuple(f"norm_param_{p}" for p in NORMALIZATION_PARAM_SLOTS)
    + ("norm_param_absent",)
    + tuple(f"dtype_{d}" for d in DTYPE_VOCABULARY)
    + tuple(f"lifetime_{lt}" for lt in LIFETIME_VOCABULARY)
    + ("declared_initial", "log_element_count", "owner_slot", "owner_slot_applicable")
)
DESCRIPTOR_BLOCK_WIDTH: Final[int] = len(DESCRIPTOR_BLOCK_FEATURES)

# --------------------------------------------------------------------------- payload schemas

#: Meter declared-parameter signature (spec §1 "identity = declared payload, applied
#: recursively"): what an affordance effect entry carries for its TARGET, and what the meter
#: token carries for itself. Built from bars.yaml's declared parameters, no names. Every
#: feature is bounded into [0, 1] (spec §1 boundedness, applied to anything entering a
#: payload): initial as position within the declared range, rates as range-relative
#: fractions per tick saturated by x/(1+x), the range itself as a saturated log.
METER_SIGNATURE_FEATURES: Final[tuple[str, ...]] = (
    "initial",
    "lethal_min",
    "lethal_max",
    "passive_depletion",
    "move_depletion",
    "interact_depletion",
    "natural_recovery",
    "range",
)
METER_SIGNATURE_WIDTH: Final[int] = len(METER_SIGNATURE_FEATURES)

#: Effect static payload (declared identity of an `EffectDefinitionConfig`): scope one-hot,
#: declared intensity (signed, saturated), declared duration (saturated log), reapply-policy
#: one-hot. Two declared effects differing in any declared parameter are distinguishable.
EFFECT_STATIC_FEATURES: Final[tuple[str, ...]] = (
    tuple(f"scope_{s}" for s in EFFECT_SCOPE_VOCABULARY)
    + ("intensity", "duration")
    + tuple(f"reapply_{p}" for p in REAPPLY_POLICY_VOCABULARY)
)


def saturate(x: float) -> float:
    """Bounded, monotone, scale-free map of a non-negative magnitude into [0, 1): x / (1 + x)."""
    if x < 0:
        raise ValueError(f"saturate expects a non-negative magnitude, got {x}")
    return x / (1.0 + x)


def saturate_signed(x: float) -> float:
    """Signed saturation into (−1, 1): sign(x) · |x| / (1 + |x|)."""
    return math.copysign(saturate(abs(x)), x) if x != 0 else 0.0


def position_features(prefix: str, *, with_rank: bool) -> tuple[str, ...]:
    """Position block feature names: MAX_POSITION_RANK coordinates (+ rank feature)."""
    names = tuple(f"{prefix}_{i}" for i in range(MAX_POSITION_RANK))
    return names + (f"{prefix}_rank",) if with_rank else names


VALUE_BLOCK_FEATURES: Final[tuple[str, ...]] = tuple(f"value_{i}" for i in range(VALUE_BLOCK_WIDTH)) + ("value_width_used",)


def _effect_summary_features() -> tuple[str, ...]:
    out: list[str] = []
    for k in range(EFFECT_SUMMARY_K):
        out.append(f"effect_{k}_present")
        out.append(f"effect_{k}_magnitude")
        out.append(f"effect_{k}_sign")
        out.extend(f"effect_{k}_target_{f}" for f in METER_SIGNATURE_FEATURES)
    return tuple(out)


#: Per-type payload schema: feature names in order. Presence is NOT a payload feature — it
#: leads every serialized row (spec §1 "presence is explicit"). Width is fixed per type across
#: all universes (spec §1 first invariant); entity variation goes into token count.
PAYLOAD_SCHEMAS: Final[Mapping[str, tuple[str, ...]]] = {
    "self": position_features("position", with_rank=True) + position_features("velocity", with_rank=False),
    "meter": VALUE_BLOCK_FEATURES + METER_SIGNATURE_FEATURES,
    "affordance": (
        tuple(f"interaction_type_{t}" for t in INTERACTION_TYPE_VOCABULARY)
        + position_features("position", with_rank=True)
        + position_features("egocentric", with_rank=False)
        + _effect_summary_features()
        + ("effect_count",)
    ),
    "agent": position_features("position", with_rank=True) + position_features("egocentric", with_rank=False),
    "item": (
        position_features("position", with_rank=True)
        + position_features("egocentric", with_rank=False)
        + ("carried", "owner_slot", "owner_slot_applicable")
    ),
    "effect": EFFECT_STATIC_FEATURES + ("remaining_fraction", "owner_slot", "owner_slot_applicable"),
    "variable_element": position_features("position", with_rank=True) + VALUE_BLOCK_FEATURES + DESCRIPTOR_BLOCK_FEATURES,
}

# --------------------------------------------------------------------------- declaration inputs


@dataclass(frozen=True)
class ExposedVariable:
    """A variable declaration as the token derivations see it (declaration-derived, name-free
    apart from `id`, which is used only to NAME declarations in error messages).

    Task 7 builds these from `VariableDef` + the field's semantic type; nothing here reads a
    `VariableDef` directly so the derivations stay testable against synthetic declarations.
    """

    id: str
    scope: str
    semantic_type: str
    type: str
    lifetime: str
    default: object
    shape: tuple[int, ...]
    normalization: NormalizationSpec | None
    owner_slot: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "shape", tuple(self.shape))
        if self.scope not in SCOPE_VOCABULARY:
            raise ValueError(f"Variable '{self.id}': scope {self.scope!r} is not a VariableScope member {SCOPE_VOCABULARY}")
        if self.semantic_type not in SEMANTIC_TYPE_VOCABULARY:
            raise ValueError(f"Variable '{self.id}': semantic_type {self.semantic_type!r} is not in {SEMANTIC_TYPE_VOCABULARY}")
        if self.type not in _VARIABLE_TYPE_DTYPE:
            raise ValueError(f"Variable '{self.id}': type {self.type!r} is not a VariableDef type")
        if self.lifetime not in LIFETIME_VOCABULARY:
            raise ValueError(f"Variable '{self.id}': lifetime {self.lifetime!r} is not in {LIFETIME_VOCABULARY}")

    @property
    def element_count(self) -> int:
        """Tensor-shaped variables tokenize per element; scalars are the rank-0 case."""
        return math.prod(self.shape) if self.shape else 1

    @property
    def rank(self) -> int:
        return len(self.shape)


@dataclass(frozen=True)
class MeterDeclaration:
    """A bars.yaml meter's declared parameters — the inputs to `meter_signature`."""

    name: str
    initial: float
    min: float
    max: float
    lethal_min: bool
    lethal_max: bool
    passive_depletion: float
    move_depletion: float
    interact_depletion: float
    natural_recovery: float


@dataclass(frozen=True)
class EffectDeclaration:
    """An effects.yaml effect's declared parameters — the inputs to `effect_static_payload`."""

    id: str
    scope: str
    duration: int
    intensity: float
    reapply_policy: str

    def __post_init__(self) -> None:
        if self.scope not in EFFECT_SCOPE_VOCABULARY:
            raise ValueError(f"Effect '{self.id}': scope {self.scope!r} is not an EffectScope member {EFFECT_SCOPE_VOCABULARY}")
        if self.reapply_policy not in REAPPLY_POLICY_VOCABULARY:
            raise ValueError(f"Effect '{self.id}': reapply_policy {self.reapply_policy!r} is not in {REAPPLY_POLICY_VOCABULARY}")
        if self.duration <= 0:
            raise ValueError(f"Effect '{self.id}': duration must be > 0 ticks")


# --------------------------------------------------------------------------- artifact


@dataclass(frozen=True)
class SlotBinding:
    """One compiled slot: bound at compile time to its filler (spec §2). Binding order is
    declaration order, stable, and hashed. `static_signature` is carried for
    `variable_element` slots so the artifact records what the indistinguishability check saw.
    """

    slot_index: int
    filler_kind: FillerKind
    filler_ref: str
    # The DESCRIPTOR BLOCK for this slot: DESCRIPTOR_BLOCK_WIDTH floats, or None where the
    # type has no static content. Typed concretely (it was `tuple[object, ...]`, which
    # forced a cast at every consumer and hid the width contract).
    static_signature: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        if self.slot_index < 0:
            raise ValueError(f"SlotBinding slot_index must be >= 0, got {self.slot_index}")
        if self.filler_kind not in get_args(FillerKind):
            raise ValueError(f"SlotBinding filler_kind must be static|dynamic, got {self.filler_kind!r}")
        if not self.filler_ref:
            raise ValueError("SlotBinding filler_ref must name the declaration it is bound to")


@dataclass(frozen=True)
class TokenTypeSchema:
    """One token type in a compiled universe: its (engine-constant) payload schema, compiled
    capacity, slot bindings, and census count."""

    type_name: str
    payload_features: tuple[str, ...]
    capacity: int
    slot_bindings: tuple[SlotBinding, ...]

    def __post_init__(self) -> None:
        if self.type_name in RESERVED_TOKEN_TYPE_NAMES:
            raise ValueError(
                f"Token type {self.type_name!r} is a reserved name (spec §1): intent only, not a settled "
                "shape. It refuses instantiation until its own unit lands it."
            )
        if self.type_name not in TOKEN_TYPE_ROSTER:
            raise ValueError(f"Token type {self.type_name!r} is not in the closed roster {TOKEN_TYPE_ROSTER}")
        object.__setattr__(self, "payload_features", tuple(self.payload_features))
        object.__setattr__(self, "slot_bindings", tuple(self.slot_bindings))
        expected = PAYLOAD_SCHEMAS[self.type_name]
        if self.payload_features != expected:
            raise ValueError(
                f"Token type {self.type_name!r}: payload schema does not match the engine constant "
                f"(got {len(self.payload_features)} features, engine defines {len(expected)}). Payload "
                "width is fixed per type across all universes (spec §1)."
            )
        if self.capacity < 0:
            raise ValueError(f"Token type {self.type_name!r}: capacity must be >= 0")
        if len(self.slot_bindings) != self.capacity:
            raise ValueError(f"Token type {self.type_name!r}: capacity {self.capacity} but {len(self.slot_bindings)} slot bindings")
        for expected_index, binding in enumerate(self.slot_bindings):
            if binding.slot_index != expected_index:
                raise ValueError(
                    f"Token type {self.type_name!r}: slot_index {binding.slot_index} at position {expected_index}; "
                    "bindings must be dense from 0 in declaration order"
                )
            if binding.filler_kind != TOKEN_TYPE_FILLER_KIND[self.type_name]:
                raise ValueError(
                    f"Token type {self.type_name!r}: slot {binding.slot_index} is {binding.filler_kind!r} but the "
                    f"type's filler kind is {TOKEN_TYPE_FILLER_KIND[self.type_name]!r}"
                )

    @property
    def payload_width(self) -> int:
        return len(self.payload_features)

    @property
    def row_width(self) -> int:
        """Presence + payload."""
        return 1 + self.payload_width

    @property
    def census(self) -> int:
        return len(self.slot_bindings)


def build_token_type(type_name: str, slot_bindings: Sequence[SlotBinding]) -> TokenTypeSchema:
    """Construct a type schema from its bindings; the payload schema is the engine constant."""
    if type_name in RESERVED_TOKEN_TYPE_NAMES:
        raise ValueError(
            f"Token type {type_name!r} is a reserved name (spec §1): intent only, not a settled shape. "
            "It refuses instantiation until its own unit lands it."
        )
    if type_name not in PAYLOAD_SCHEMAS:
        raise ValueError(f"Token type {type_name!r} is not in the closed roster {TOKEN_TYPE_ROSTER}")
    return TokenTypeSchema(
        type_name=type_name,
        payload_features=PAYLOAD_SCHEMAS[type_name],
        capacity=len(slot_bindings),
        slot_bindings=tuple(slot_bindings),
    )


@dataclass(frozen=True)
class TokenSpec:
    """The compiler's token artifact (spec §2): type schemas in engine-canonical roster order.

    Serialization = the flat view: rows concatenate type-then-slot, presence leading each row,
    ``total_dims = Σ_type N_type × (1 + payload_width_type)``.
    """

    types: tuple[TokenTypeSchema, ...]
    encoding_version: str = ENCODING_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "types", tuple(self.types))
        names = [t.type_name for t in self.types]
        if len(set(names)) != len(names):
            raise ValueError(f"TokenSpec has duplicate token types: {names}")
        order = [TOKEN_TYPE_ROSTER.index(n) for n in names]
        if order != sorted(order):
            raise ValueError(f"TokenSpec types must follow engine roster order {TOKEN_TYPE_ROSTER}; got {names}")

    @property
    def total_dims(self) -> int:
        return sum(t.capacity * t.row_width for t in self.types)

    @property
    def census(self) -> dict[str, int]:
        return {t.type_name: t.census for t in self.types}

    def get_type(self, type_name: str) -> TokenTypeSchema | None:
        for t in self.types:
            if t.type_name == type_name:
                return t
        return None

    def row_layout(self) -> tuple[tuple[str, int, int, int], ...]:
        """(type_name, slot_index, start, end) per row in serialization order; presence at `start`."""
        rows: list[tuple[str, int, int, int]] = []
        offset = 0
        for t in self.types:
            for binding in t.slot_bindings:
                rows.append((t.type_name, binding.slot_index, offset, offset + t.row_width))
                offset += t.row_width
        return tuple(rows)


# --------------------------------------------------------------------------- exposure rules


#: Kinds that certify boundedness by themselves (spec §1 "boundedness is certified at exposure").
_BOUNDED_KINDS: Final[frozenset[str]] = frozenset({"cyclical_sin_cos", "binary"})
#: Range kinds: bounded only with ``clip: true``.
_RANGE_KINDS: Final[frozenset[str]] = frozenset({"minmax", "log_scaled"})


def require_exposure_normalization(var_id: str, spec: NormalizationSpec | None) -> NormalizationSpec:
    """The exposure refusals, in one place (spec §1 width + boundedness rules; Task 5f ruling).

    - normalization is REQUIRED at exposure (spec §2 "normalization authority");
    - ``one_hot`` is refused on tokenized variables (width-changing; author a clipped minmax
      index instead — its declared range rides in the descriptor block);
    - ``rank_scaled`` is refused at exposure (hamlet-6a6e104523: it ranks across dim 0 = the
      batch = causally independent worlds — non-Markov, constant-zero on globals);
    - ``none`` / ``zscore`` / bare ``masked_value`` / unclipped range kinds are unbounded.
    """
    if spec is None:
        raise ValueError(
            f"Variable '{var_id}' is exposed but declares no normalization.\n"
            "  Rule: normalization is required at exposure (spec §2, normalization authority) — the "
            "normalization that feeds a token value is declared on the variable being exposed."
        )
    kind = spec.kind
    if kind == "one_hot":
        raise ValueError(
            f"Variable '{var_id}' exposes with normalization kind 'one_hot'.\n"
            f"  Rule: one_hot is refused on tokenized variables — it widens 1→C and cannot fit the "
            f"fixed {VALUE_BLOCK_WIDTH}-wide value block (spec §1 width rule). Expose the category as a "
            "clipped minmax index over [0, C-1]; the declared range then rides in the descriptor "
            "block's min/max slots (there is no separate categories-count feature)."
        )
    if kind == "rank_scaled":
        raise ValueError(
            f"Variable '{var_id}' exposes with normalization kind 'rank_scaled'.\n"
            "  Rule: rank_scaled is refused at profile-variable exposure (hamlet-6a6e104523): it ranks "
            "across dim 0 = the batch = causally independent worlds, so the observation depends on "
            "other worlds' state and reads constant-zero on globals / single-agent batches."
        )
    bounded = kind in _BOUNDED_KINDS or (kind in _RANGE_KINDS and spec.clip is True)
    if not bounded:
        raise ValueError(
            f"Variable '{var_id}' exposes with normalization kind '{kind}'"
            f"{' (clip: false)' if kind in _RANGE_KINDS else ''}.\n"
            "  Rule: a value feature entering a token must come from a bounded normalization kind "
            f"({sorted(_BOUNDED_KINDS)}) or a range kind ({sorted(_RANGE_KINDS)}) with clip: true "
            "(spec §1, boundedness is certified at exposure). Unbounded values saturate LayerNorm "
            "and read as perpetual novelty to RND (PDR-0016)."
        )
    return spec


def value_block_width_used(spec: NormalizationSpec) -> int:
    """Lanes of the value block a kind fills: cyclical_sin_cos uses both, every other kind lane 0."""
    return 2 if spec.kind == "cyclical_sin_cos" else 1


def require_position_rank(rank: int, *, substrate_type: str) -> int:
    """Refuse a substrate whose position rank exceeds MAX_POSITION_RANK (spec §1)."""
    if rank < 0:
        raise ValueError(f"Substrate '{substrate_type}' reports negative position rank {rank}")
    if rank > MAX_POSITION_RANK:
        raise ValueError(
            f"Substrate '{substrate_type}' has position rank {rank} > MAX_POSITION_RANK = {MAX_POSITION_RANK}.\n"
            "  Rule: position payloads pad to the engine constant MAX_POSITION_RANK (spec §1). This is a "
            "deliberate capability contraction for GridND's 4–100D range; raising the constant breaks "
            "every checkpoint and is a superseding PDR, not a config change."
        )
    return rank


# --------------------------------------------------------------------------- descriptor block derivation


def _one_hot(vocabulary: Sequence[str], member: str) -> tuple[float, ...]:
    return tuple(1.0 if v == member else 0.0 for v in vocabulary)


def _element_param(value: float | list[float] | None, element_index: int, *, element_count: int, where: str) -> float | None:
    """One element's normalization parameter: scalars broadcast; a list must have exactly one
    entry per element (a per-axis list against a multi-axis shape is a named refusal)."""
    if value is None:
        return None
    if isinstance(value, list):
        if len(value) == 1:
            return float(value[0])
        if len(value) != element_count:
            raise ValueError(
                f"{where} lists {len(value)} values but the variable has {element_count} elements; "
                "declare one value per element (row-major over the shape) or a single scalar"
            )
        return float(value[element_index])
    return float(value)


def _flatten(value: object) -> Iterator[float]:
    if isinstance(value, bool):
        yield 1.0 if value else 0.0
    elif isinstance(value, int | float):
        yield float(value)
    elif isinstance(value, list | tuple):
        for item in value:
            yield from _flatten(item)
    else:
        raise ValueError(f"Declared default contains a non-numeric entry {value!r}")


def _element_default(default: object, element_index: int, element_count: int) -> float:
    """The declared initial of one element, flattened row-major; scalars broadcast."""
    if default is None:
        return 0.0
    flat = list(_flatten(default))
    if len(flat) == element_count:
        return flat[element_index]
    if len(flat) == 1:
        return flat[0]
    raise ValueError(f"Declared default has {len(flat)} elements but the variable has {element_count}")


def normalize_declared_scalar(value: float, spec: NormalizationSpec, *, element_index: int, element_count: int) -> float:
    """Apply a bounded normalization kind to one declared scalar (the descriptor's 'normalized
    declared initial'). For cyclical_sin_cos the descriptor carries the phase fraction, not the
    sin/cos pair — the pair is the value block's job."""
    kind = spec.kind
    if kind == "minmax" or kind == "log_scaled":
        lo = _element_param(spec.min, element_index, element_count=element_count, where="normalization.min")
        hi = _element_param(spec.max, element_index, element_count=element_count, where="normalization.max")
        assert lo is not None and hi is not None
        v = min(max(value, lo), hi) if spec.clip else value
        if kind == "minmax":
            return (v - lo) / (hi - lo)
        return math.log1p(v - lo) / math.log1p(hi - lo)
    if kind == "cyclical_sin_cos":
        assert spec.period is not None
        return (value % spec.period) / spec.period
    if kind == "binary":
        assert spec.threshold is not None
        return 1.0 if value >= spec.threshold else 0.0
    raise ValueError(f"normalize_declared_scalar: kind {kind!r} is not an exposure-admitted kind")


def normalization_param_vector(spec: NormalizationSpec, *, element_index: int, element_count: int) -> tuple[float, ...]:
    """Canonical (min, max, clip, scale, params_absent) for the descriptor block."""
    lo = _element_param(spec.min, element_index, element_count=element_count, where="normalization.min")
    hi = _element_param(spec.max, element_index, element_count=element_count, where="normalization.max")
    clip = None if spec.clip is None else (1.0 if spec.clip else 0.0)
    scale: float | None
    if spec.kind == "cyclical_sin_cos":
        scale = spec.period
    elif spec.kind == "binary":
        scale = spec.threshold
    elif spec.kind == "one_hot":
        scale = None if spec.categories is None else float(spec.categories)
    elif spec.kind == "zscore":
        scale = _element_param(spec.std, element_index, element_count=element_count, where="normalization.std")
    elif spec.kind == "masked_value":
        scale = spec.fill_value
    else:
        scale = None
    slots = (lo, hi, clip, scale)
    absent = any(s is None for s in slots)
    return tuple(0.0 if s is None else float(s) for s in slots) + (1.0 if absent else 0.0,)


def describe_variable(var: ExposedVariable, *, element_index: int, owner_capacity: int | None) -> tuple[float, ...]:
    """The variable-descriptor block for one element (spec §1): fixed-width, name-free, built
    from the declaration. Width == DESCRIPTOR_BLOCK_WIDTH."""
    spec = require_exposure_normalization(var.id, var.normalization)
    if var.owner_slot is not None:
        if owner_capacity is None or owner_capacity <= 0:
            raise ValueError(f"Variable '{var.id}' carries owner_slot {var.owner_slot} but no owner capacity was given")
        owner = (var.owner_slot / owner_capacity, 1.0)
    else:
        owner = (0.0, 0.0)
    count = var.element_count
    declared = _element_default(var.default, element_index, count)
    initial = normalize_declared_scalar(declared, spec, element_index=element_index, element_count=count)
    block = (
        _one_hot(SCOPE_VOCABULARY, var.scope)
        + _one_hot(SEMANTIC_TYPE_VOCABULARY, var.semantic_type)
        + _one_hot(NORMALIZATION_KIND_VOCABULARY, spec.kind)
        + normalization_param_vector(spec, element_index=element_index, element_count=count)
        + _one_hot(DTYPE_VOCABULARY, _VARIABLE_TYPE_DTYPE[var.type])
        + _one_hot(LIFETIME_VOCABULARY, var.lifetime)
        + (initial, math.log1p(var.element_count))
        + owner
    )
    assert len(block) == DESCRIPTOR_BLOCK_WIDTH
    return block


def static_payload_signature(var: ExposedVariable, *, owner_capacity: int | None) -> tuple[object, ...]:
    """Everything static about a variable's tokens: the descriptor block per element plus the
    coordinate space (scope, shape). Two exposed variables with equal signatures are
    indistinguishable under permutation-invariant pooling (spec §1)."""
    blocks = tuple(describe_variable(var, element_index=i, owner_capacity=owner_capacity) for i in range(var.element_count))
    return (var.scope, var.shape, blocks)


def check_indistinguishability(variables: Iterable[ExposedVariable], *, owner_capacity: int | None) -> None:
    """Compile-time indistinguishability check (spec §1): identical static signature → error
    naming both declarations and demanding a distinguishing declared parameter."""
    seen: dict[tuple[object, ...], str] = {}
    for var in variables:
        sig = static_payload_signature(var, owner_capacity=owner_capacity)
        other = seen.get(sig)
        if other is not None:
            raise ValueError(
                f"Variables '{other}' and '{var.id}' are indistinguishable: identical static payload "
                "signature (descriptor block + coordinate space).\n"
                "  Rule: under permutation-invariant pooling two such tokens alias for every weight "
                "setting (spec §1). Add a distinguishing DECLARED parameter to one of them — a different "
                "semantic_type, lifetime, normalization range, or declared initial value."
            )
        seen[sig] = var.id


# --------------------------------------------------------------------------- meter / affordance payload math


def meter_signature(meter: MeterDeclaration) -> tuple[float, ...]:
    """A meter's declared-parameter features (METER_SIGNATURE_WIDTH wide), every one bounded
    into [0, 1]: the initial as its position within [min, max]; each declared rate (meter units
    per tick) as a fraction of the declared range, saturated by x/(1+x) so a money-scale rate
    cannot blow up the token; the range itself as a saturated log1p. Every feature but `range`
    is scale-free: a meter re-declared in different units gives the same signature except for
    `range`, which deliberately carries the declared span (it is what tells a 0–1 meter from a
    0–999999 one)."""
    span = meter.max - meter.min
    if span <= 0:
        raise ValueError(f"Meter '{meter.name}': bounds must satisfy min < max")
    initial = min(max((meter.initial - meter.min) / span, 0.0), 1.0)
    return (
        initial,
        1.0 if meter.lethal_min else 0.0,
        1.0 if meter.lethal_max else 0.0,
        saturate(abs(meter.passive_depletion) / span),
        saturate(abs(meter.move_depletion) / span),
        saturate(abs(meter.interact_depletion) / span),
        saturate(abs(meter.natural_recovery) / span),
        saturate(math.log1p(span)),
    )


def effect_static_payload(effect: EffectDeclaration) -> tuple[float, ...]:
    """An effect's declared-identity features (len(EFFECT_STATIC_FEATURES) wide, all bounded):
    scope one-hot, signed-saturated intensity, saturated log1p(duration), reapply-policy one-hot.
    The runtime appends remaining_fraction and the owner coordinate at publish time."""
    return (
        _one_hot(EFFECT_SCOPE_VOCABULARY, effect.scope)
        + (saturate_signed(effect.intensity), saturate(math.log1p(effect.duration)))
        + _one_hot(REAPPLY_POLICY_VOCABULARY, effect.reapply_policy)
    )


def effect_summary(deltas: Mapping[str, float], meters: Mapping[str, MeterDeclaration]) -> tuple[float, ...]:
    """The affordance effect summary (spec §1): the K largest declared deltas by NORMALIZED
    magnitude — |delta| relative to the TARGET meter's declared range, so a +22.5 delta on a
    0–999999 meter and a +0.3 delta on a 0–1 meter rank on comparable footing (2.25e-5 vs 0.3) —
    each (present, magnitude, sign, target signature); fewer than K → absent-marked. Returns the
    EFFECT_SUMMARY_K × (3 + METER_SIGNATURE_WIDTH) block; the count feature is appended by the
    caller from `len(deltas)`."""
    ranked: list[tuple[float, float, MeterDeclaration]] = []
    for target, delta in deltas.items():
        meter = meters.get(target)
        if meter is None:
            raise ValueError(f"Effect targets meter '{target}' which is not declared")
        magnitude = min(abs(delta) / (meter.max - meter.min), 1.0)
        ranked.append((magnitude, math.copysign(1.0, delta) if delta != 0 else 0.0, meter))
    ranked.sort(key=lambda r: r[0], reverse=True)
    out: list[float] = []
    for k in range(EFFECT_SUMMARY_K):
        if k < len(ranked):
            magnitude, sign, meter = ranked[k]
            out.extend((1.0, magnitude, sign, *meter_signature(meter)))
        else:
            out.extend((0.0,) * (3 + METER_SIGNATURE_WIDTH))
    return tuple(out)


# --------------------------------------------------------------------------- capacity (spec §2 table)


def self_capacity() -> int:
    return 1


def meter_capacity(meters: Sequence[MeterDeclaration]) -> int:
    """Count of declared meters (bars.yaml)."""
    return len(meters)


def affordance_capacity(*, affordance_count: int) -> int:
    """Count of affordance instances — the runtime count from `metadata.affordance_count`
    (affordances.yaml); the extents `num_affordances` declaration is presence-checked and inert."""
    if affordance_count < 0:
        raise ValueError("affordance_count must be >= 0")
    return affordance_count


def _agents_per_world(declared_agents_per_world: int | None) -> int:
    """`num_agents` is a batch of independent worlds, never a shared-world population (Global
    Constraints). Absent a declared shared-world count, one agent occupies each world."""
    if declared_agents_per_world is None:
        return 1
    if declared_agents_per_world < 1:
        raise ValueError(f"declared agents-per-world must be >= 1, got {declared_agents_per_world}")
    return declared_agents_per_world


def agent_capacity(*, declared_agents_per_world: int | None) -> int:
    """Declared agents-per-world − 1; 0 where no shared-world declaration exists (the type is
    then structurally absent — every shipped pack today)."""
    return _agents_per_world(declared_agents_per_world) - 1


def item_capacity(*, max_items_in_world: int, max_items_per_agent: int, declared_agents_per_world: int | None) -> int:
    """`max_items_in_world + max_items_per_agent × agents_per_world` (items.yaml, required fields)."""
    if max_items_in_world < 0 or max_items_per_agent < 0:
        raise ValueError("item capacities must be >= 0")
    return max_items_in_world + max_items_per_agent * _agents_per_world(declared_agents_per_world)


def effect_capacity(
    *,
    max_active_effects: Mapping[str, int] | None,
    declared_effect_count: int,
    declared_agents_per_world: int | None,
    item_capacity_value: int,
    affordance_capacity_value: int,
) -> int:
    """Σ over EffectScope of declared per-scope budget × that scope's denominator (world = 1,
    agents-per-world, item capacity, affordance capacity). The budget is REQUIRED (No-Defaults)
    whenever any effect is declared; with no effects declared the capacity is 0."""
    if declared_effect_count < 0:
        raise ValueError("declared_effect_count must be >= 0")
    if declared_effect_count == 0:
        return 0
    if max_active_effects is None:
        raise ValueError(
            f"effects.yaml declares {declared_effect_count} effect(s) but no `max_active_effects` budget.\n"
            "  Rule: effect token capacity derives from a per-scope declared budget "
            f"(max_active_effects: {{{', '.join(f'{s}: N' for s in EFFECT_SCOPE_VOCABULARY)}}}), "
            "required if any effects are declared (spec §2 capacity table, No-Defaults)."
        )
    denominators = {
        "global": 1,
        "agent": _agents_per_world(declared_agents_per_world),
        "item": item_capacity_value,
        "affordance": affordance_capacity_value,
    }
    missing = [s for s in EFFECT_SCOPE_VOCABULARY if s not in max_active_effects]
    unknown = [s for s in max_active_effects if s not in EFFECT_SCOPE_VOCABULARY]
    if missing or unknown:
        raise ValueError(
            f"max_active_effects must declare exactly the EffectScope members {EFFECT_SCOPE_VOCABULARY}; "
            f"missing {missing}, unknown {unknown}"
        )
    total = 0
    for scope in EFFECT_SCOPE_VOCABULARY:
        budget = max_active_effects[scope]
        if budget < 0:
            raise ValueError(f"max_active_effects.{scope} must be >= 0")
        total += budget * denominators[scope]
    return total


def variable_element_capacity(variables: Iterable[ExposedVariable]) -> int:
    """Σ element counts of explicitly exposed variables. Each variable is checked against the
    exposure rules so a refused kind never sizes a capacity.

    `agent_private` is NOT refused here by ruling (Task 6 review M1): the spec §2 table places
    that exclusion in the publisher's filter before slot binding. LANDED (Task 8):
    `environment/token_publishers.py::RegistryVariableElementPublisher` refuses an
    agent_private-bound slot at construction, and the registry's scope arenas exclude
    agent_private by construction — pinned by test (agent_private never lands in any
    agent's rows; the hamlet-83a043a9b9 boundary by mechanism)."""
    total = 0
    for var in variables:
        require_exposure_normalization(var.id, var.normalization)
        total += var.element_count
    return total


# --------------------------------------------------------------------------- census advisory


def mean_census_advisory(spec: TokenSpec, *, aggregator: str) -> str | None:
    """Spec §2: compiling ``{type: mean}`` against a census where any single type exceeds
    MEAN_CENSUS_ADVISORY tokens returns a loud advisory naming the counts; None otherwise."""
    if aggregator != "mean":
        return None
    over = {name: count for name, count in spec.census.items() if count > MEAN_CENSUS_ADVISORY}
    if not over:
        return None
    counts = ", ".join(f"{name}={count}" for name, count in over.items())
    return (
        f"Token census advisory: aggregator 'mean' with type count(s) above {MEAN_CENSUS_ADVISORY} — {counts}. "
        "Mean pooling dilutes each token's contribution as the set grows; past this regime prefer "
        "`{type: attention}` (spec §4 regime guidance). Full census: " + ", ".join(f"{name}={count}" for name, count in spec.census.items())
    )


__all__ = [
    "DESCRIPTOR_BLOCK_FEATURES",
    "DESCRIPTOR_BLOCK_WIDTH",
    "DTYPE_FLAG_WIDTH",
    "EFFECT_STATIC_FEATURES",
    "EFFECT_SUMMARY_K",
    "ENCODING_VERSION",
    "LIFETIME_ONE_HOT_WIDTH",
    "MAX_POSITION_RANK",
    "MEAN_CENSUS_ADVISORY",
    "METER_SIGNATURE_FEATURES",
    "METER_SIGNATURE_WIDTH",
    "NORMALIZATION_KIND_ONE_HOT_WIDTH",
    "NORMALIZATION_PARAM_VECTOR_WIDTH",
    "OWNER_SLOT_COORDINATE_WIDTH",
    "PAYLOAD_SCHEMAS",
    "REAPPLY_POLICY_VOCABULARY",
    "RESERVED_TOKEN_TYPE_NAMES",
    "SCOPE_ONE_HOT_WIDTH",
    "SEMANTIC_TYPE_ONE_HOT_WIDTH",
    "TOKEN_TYPE_FILLER_KIND",
    "TOKEN_TYPE_ROSTER",
    "VALUE_BLOCK_WIDTH",
    "VARIABLE_TYPE_VOCABULARY",
    "EffectDeclaration",
    "ExposedVariable",
    "MeterDeclaration",
    "SlotBinding",
    "TokenSpec",
    "TokenType",
    "TokenTypeSchema",
    "affordance_capacity",
    "agent_capacity",
    "build_token_type",
    "check_indistinguishability",
    "describe_variable",
    "effect_capacity",
    "effect_static_payload",
    "effect_summary",
    "item_capacity",
    "mean_census_advisory",
    "meter_capacity",
    "meter_signature",
    "normalization_param_vector",
    "normalize_declared_scalar",
    "position_features",
    "require_exposure_normalization",
    "require_position_rank",
    "saturate",
    "saturate_signed",
    "self_capacity",
    "static_payload_signature",
    "value_block_width_used",
    "variable_element_capacity",
]
