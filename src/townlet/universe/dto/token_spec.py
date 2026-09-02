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
from typing import TYPE_CHECKING, Final, Literal, get_args

from townlet.config.affordances_v2_config import AffordanceParamConfig
from townlet.config.effects_config import EffectScope, ReapplyPolicy
from townlet.config.interaction_type import InteractionType
from townlet.effects.affordance_identity import (
    AFFORDANCE_LIFECYCLE_STAGES,
    AFFORDANCE_WRITE_SOURCES,
    AFFORDANCE_WRITE_TARGETS,
    SPAWN_EFFECT_TARGETS,
    AffordanceMeterWrite,
    extract_affordance_meter_writes,
    opening_hours_signature,
)
from townlet.numeric import require_float32
from townlet.vfs.schema import NormalizationSpec, VariableDef, VariableScope
from townlet.vfs.semantic_type import SemanticType

if TYPE_CHECKING:
    from townlet.config.affordances_v2_config import AffordancesV2Config
    from townlet.config.environment_config import EnvironmentConfig
    from townlet.config.items_config import ItemsCatalogConfig
    from townlet.effects.catalog import EffectCatalog
    from townlet.universe.compiled import CompiledVFSProfiles
    from townlet.vfs.profiles import CompiledVariable

# --------------------------------------------------------------------------- engine constants

#: Position payloads pad to this rank, with a rank feature (spec §1). A substrate of rank > 8
#: is refused at compile time; raising the constant is a superseding PDR (breaks checkpoints).
MAX_POSITION_RANK: Final[int] = 8

#: Value sub-block width. Scalar kinds use lane 0; ``cyclical_sin_cos`` lands sin/cos in lanes
#: 0–1 of ONE token (spec §1 width rule). A width-used feature accompanies the lanes.
VALUE_BLOCK_WIDTH: Final[int] = 2

#: Affordance effect summary capacity measured from the executable fleet census. Canonical
#: ordering retains all five admitted entries; more than five refuses instead of truncating.
EFFECT_SUMMARY_K: Final[int] = 5

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

ENCODING_VERSION: Final[str] = "token-1.1"
TOKEN_TRANSPORT_VERSION: Final[str] = "compact-1"

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

#: The meter surface is deliberately narrower than the general VFS vocabulary: every
#: member is bounded and fits VALUE_BLOCK_WIDTH (PDR-0134).
METER_NORMALIZATION_KIND_VOCABULARY: Final[tuple[str, ...]] = (
    "minmax",
    "log_scaled",
    "cyclical_sin_cos",
    "binary",
)

#: Meter declared-parameter signature (spec §1 "identity = declared payload, applied
#: recursively"): what an affordance effect entry carries for its TARGET, and what the meter
#: token carries for itself. Built from bars.yaml + range_type declared parameters, no
#: names. Every feature is bounded into [-1, 1] (spec §1 boundedness, applied to anything entering a
#: payload): initial as position within the declared range, rates as range-relative
#: fractions per tick saturated by x/(1+x), the range itself as a saturated log.
METER_SIGNATURE_FEATURES: Final[tuple[str, ...]] = (
    (
        "initial",
        "lethal_min",
        "lethal_max",
        "passive_depletion",
        "move_depletion",
        "interact_depletion",
        "natural_recovery",
        "range",
    )
    + tuple(f"normalization_kind_{kind}" for kind in METER_NORMALIZATION_KIND_VOCABULARY)
    + (
        "normalization_min",
        "normalization_max",
        "normalization_scale",
    )
)
METER_SIGNATURE_WIDTH: Final[int] = len(METER_SIGNATURE_FEATURES)

#: Effect static payload (declared identity of an `EffectDefinitionConfig`): scope one-hot,
#: declared duration (saturated log), and reapply-policy one-hot. Spawn intensity is live
#: instance state and therefore belongs in the dynamic effect-token payload.
EFFECT_STATIC_FEATURES: Final[tuple[str, ...]] = (
    tuple(f"scope_{s}" for s in EFFECT_SCOPE_VOCABULARY) + ("duration",) + tuple(f"reapply_{p}" for p in REAPPLY_POLICY_VOCABULARY)
)


def saturate(x: float) -> float:
    """Bounded, monotone, scale-free map of a non-negative magnitude into [0, 1): x / (1 + x)."""
    if not math.isfinite(x):
        raise ValueError(f"saturate expects a finite magnitude, got {x}")
    if x < 0:
        raise ValueError(f"saturate expects a non-negative magnitude, got {x}")
    return x / (1.0 + x)


def saturate_signed(x: float) -> float:
    """Signed saturation into (−1, 1): sign(x) · |x| / (1 + |x|)."""
    return math.copysign(saturate(abs(x)), x) if x != 0 else 0.0


def _float32_tuple(values: Iterable[float], *, field: str) -> tuple[float, ...]:
    """Canonicalize a complete model-facing feature vector to its runtime dtype."""
    return tuple(require_float32(value, field=f"{field} feature {index}") for index, value in enumerate(values))


def _float32_range(low: float, high: float, *, field: str, logarithmic: bool) -> tuple[float, float, float]:
    """Validate the arithmetic a float32 normalizer performs over an authored range."""
    low32 = require_float32(low, field=f"{field}.min")
    high32 = require_float32(high, field=f"{field}.max")
    if not low32 < high32:
        raise ValueError(
            f"{field} bounds must remain strictly ordered in float32, got authored ({low!r}, {high!r}) "
            f"and runtime ({low32!r}, {high32!r})"
        )
    span32 = require_float32(high32 - low32, field=f"{field} float32 span")
    require_float32(1.0 / span32, field=f"{field} float32 reciprocal span")
    if logarithmic:
        log_span32 = require_float32(math.log1p(span32), field=f"{field} float32 log1p span")
        require_float32(1.0 / log_span32, field=f"{field} float32 reciprocal log1p span")
    return low32, high32, span32


def _normalization_values(value: float | list[float] | None) -> list[float]:
    if value is None:
        return []
    return [float(item) for item in value] if isinstance(value, list) else [float(value)]


def _require_normalization_float32(var_id: str, spec: NormalizationSpec) -> None:
    """Refuse exposure parameters whose float32 execution changes their semantics."""
    if spec.kind in _RANGE_KINDS:
        lows = _normalization_values(spec.min)
        highs = _normalization_values(spec.max)
        if len(lows) == 1 and len(highs) > 1:
            lows *= len(highs)
        if len(highs) == 1 and len(lows) > 1:
            highs *= len(lows)
        if len(lows) != len(highs):
            raise ValueError(f"Variable '{var_id}': normalization bounds are not broadcast-compatible")
        for index, (low, high) in enumerate(zip(lows, highs, strict=True)):
            _float32_range(
                low,
                high,
                field=f"Variable '{var_id}' normalization[{index}]",
                logarithmic=spec.kind == "log_scaled",
            )
    elif spec.kind == "cyclical_sin_cos":
        assert spec.period is not None
        period32 = require_float32(spec.period, field=f"Variable '{var_id}' cyclical period")
        require_float32(2.0 * math.pi / period32, field=f"Variable '{var_id}' cyclical float32 factor")
    elif spec.kind == "binary":
        assert spec.threshold is not None
        require_float32(spec.threshold, field=f"Variable '{var_id}' binary threshold")


def position_features(prefix: str, *, with_rank: bool) -> tuple[str, ...]:
    """Position block feature names: MAX_POSITION_RANK coordinates (+ rank feature)."""
    names = tuple(f"{prefix}_{i}" for i in range(MAX_POSITION_RANK))
    if with_rank:
        return names + (f"{prefix}_rank",)
    return names


def element_coordinate_block(shape: tuple[int, ...], element_index: int) -> tuple[float, ...]:
    """Return one variable element's padded row-major coordinates and normalized rank."""
    if len(shape) > MAX_POSITION_RANK:
        raise ValueError(f"Variable element rank {len(shape)} exceeds MAX_POSITION_RANK={MAX_POSITION_RANK}")
    element_count = 1
    if shape:
        element_count = math.prod(shape)
    if isinstance(element_index, bool) or not isinstance(element_index, int) or not 0 <= element_index < element_count:
        raise ValueError(f"element_index must be an integer within [0, {element_count}), got {element_index!r}")
    coords = [0.0] * MAX_POSITION_RANK
    if shape:
        stride = element_count
        for axis, dim in enumerate(shape):
            if isinstance(dim, bool) or not isinstance(dim, int) or dim <= 0:
                raise ValueError(f"Variable shape dimensions must be positive integers, got {shape!r}")
            stride //= dim
            axis_index = (element_index // stride) % dim
            coords[axis] = axis_index / max(dim - 1, 1)
    return _float32_tuple((*coords, len(shape) / MAX_POSITION_RANK), field="variable element coordinate block")


VALUE_BLOCK_FEATURES: Final[tuple[str, ...]] = tuple(f"value_{i}" for i in range(VALUE_BLOCK_WIDTH)) + ("value_width_used",)


def _effect_summary_features() -> tuple[str, ...]:
    out: list[str] = []
    for k in range(EFFECT_SUMMARY_K):
        out.append(f"effect_{k}_form")
        out.extend(f"effect_{k}_stage_{stage}" for stage in AFFORDANCE_LIFECYCLE_STAGES)
        out.extend(f"effect_{k}_source_{source}" for source in AFFORDANCE_WRITE_SOURCES)
        out.extend(f"effect_{k}_write_target_{target}" for target in AFFORDANCE_WRITE_TARGETS)
        out.extend(f"effect_{k}_{feature}" for feature in SPAWN_EFFECT_IDENTITY_FEATURES)
        out.append(f"effect_{k}_magnitude")
        out.append(f"effect_{k}_sign")
        out.extend(f"effect_{k}_target_{f}" for f in METER_SIGNATURE_FEATURES)
    return tuple(out)


AFFORDANCE_DURATION_FEATURES: Final[tuple[str, ...]] = ("duration_applicable", "duration_ticks")
OPENING_HOURS_FEATURES: Final[tuple[str, ...]] = tuple(f"open_hour_{hour}" for hour in range(24))
SPAWN_EFFECT_IDENTITY_FEATURES: Final[tuple[str, ...]] = (
    tuple(f"spawn_target_{target}" for target in SPAWN_EFFECT_TARGETS)
    + ("spawn_intensity", "spawn_duration")
    + tuple(f"spawn_scope_{scope}" for scope in EFFECT_SCOPE_VOCABULARY)
    + tuple(f"spawn_reapply_{policy}" for policy in REAPPLY_POLICY_VOCABULARY)
    + ("spawn_observable",)
)
AFFORDANCE_EFFECT_MAGNITUDE_OFFSET: Final[int] = (
    1
    + len(AFFORDANCE_LIFECYCLE_STAGES)
    + len(AFFORDANCE_WRITE_SOURCES)
    + len(AFFORDANCE_WRITE_TARGETS)
    + len(SPAWN_EFFECT_IDENTITY_FEATURES)
)
AFFORDANCE_EFFECT_METER_OFFSET: Final[int] = AFFORDANCE_EFFECT_MAGNITUDE_OFFSET + 2
AFFORDANCE_EFFECT_ENTRY_WIDTH: Final[int] = AFFORDANCE_EFFECT_METER_OFFSET + METER_SIGNATURE_WIDTH


#: Immutable affordance identity stored on each compiled slot: interaction type,
#: duration, exact opening-hours behavior, recursively declared meter-effect targets,
#: and declared effect count. Positions and visibility are dynamic and excluded.
AFFORDANCE_SIGNATURE_WIDTH: Final[int] = (
    len(INTERACTION_TYPE_VOCABULARY) + len(AFFORDANCE_DURATION_FEATURES) + len(OPENING_HOURS_FEATURES) + len(_effect_summary_features()) + 1
)

#: Per-type payload schema: feature names in order. Presence is NOT a payload feature — it
#: leads every serialized row (spec §1 "presence is explicit"). Width is fixed per type across
#: all universes (spec §1 first invariant); entity variation goes into token count.
PAYLOAD_SCHEMAS: Final[Mapping[str, tuple[str, ...]]] = {
    "self": position_features("position", with_rank=True) + position_features("velocity", with_rank=False),
    "meter": VALUE_BLOCK_FEATURES + METER_SIGNATURE_FEATURES,
    "affordance": (
        tuple(f"interaction_type_{t}" for t in INTERACTION_TYPE_VOCABULARY)
        + AFFORDANCE_DURATION_FEATURES
        + OPENING_HOURS_FEATURES
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
    "effect": EFFECT_STATIC_FEATURES + ("remaining_fraction", "live_intensity", "owner_slot", "owner_slot_applicable"),
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
    normalization: NormalizationSpec
    initial: float
    min: float
    max: float
    lethal_min: bool
    lethal_max: bool
    passive_depletion: float
    move_depletion: float
    interact_depletion: float
    natural_recovery: float

    def __post_init__(self) -> None:
        authored_values = {
            "initial": self.initial,
            "min": self.min,
            "max": self.max,
            "passive_depletion": self.passive_depletion,
            "move_depletion": self.move_depletion,
            "interact_depletion": self.interact_depletion,
            "natural_recovery": self.natural_recovery,
        }
        for field_name, value in (
            ("initial", self.initial),
            ("min", self.min),
            ("max", self.max),
            ("passive_depletion", self.passive_depletion),
            ("move_depletion", self.move_depletion),
            ("interact_depletion", self.interact_depletion),
            ("natural_recovery", self.natural_recovery),
        ):
            runtime_value = require_float32(value, field=f"Meter '{self.name}' {field_name}")
            object.__setattr__(self, field_name, runtime_value)

        minimum, maximum, _span = _float32_range(
            authored_values["min"],
            authored_values["max"],
            field=f"Meter '{self.name}' bounds",
            logarithmic=False,
        )
        initial = self.initial
        if not minimum <= initial <= maximum:
            raise ValueError(f"Meter '{self.name}' initial must lie within its float32 bounds [{minimum}, {maximum}], got {initial}")
        if authored_values["min"] < authored_values["initial"] < authored_values["max"] and not minimum < initial < maximum:
            raise ValueError(
                f"Meter '{self.name}' initial is strictly interior in the authored declaration but collapses "
                f"to a bound in float32: {authored_values['initial']!r} -> {initial!r}"
            )

        spec = require_exposure_normalization(f"meter:{self.name}", self.normalization)
        if spec.kind not in METER_NORMALIZATION_KIND_VOCABULARY:
            raise ValueError(
                f"Meter '{self.name}': normalization kind {spec.kind!r} is not in the bounded "
                f"two-lane meter vocabulary {METER_NORMALIZATION_KIND_VOCABULARY}"
            )
        if spec.kind in _RANGE_KINDS:
            if not isinstance(spec.min, float) or not isinstance(spec.max, float):
                raise ValueError(f"Meter '{self.name}': range normalization bounds must be scalar floats")
            normalized_min, normalized_max, _normalization_span = _float32_range(
                spec.min,
                spec.max,
                field=f"Meter '{self.name}' normalization",
                logarithmic=spec.kind == "log_scaled",
            )
            if normalized_min != self.min or normalized_max != self.max:
                raise ValueError(
                    f"Meter '{self.name}': normalization bounds ({spec.min}, {spec.max}) do not match "
                    f"the declared bars bounds ({self.min}, {self.max})"
                )
        elif spec.kind == "cyclical_sin_cos":
            assert spec.period is not None
            period32 = require_float32(spec.period, field=f"Meter '{self.name}' cyclical period")
            require_float32(2.0 * math.pi / period32, field=f"Meter '{self.name}' cyclical float32 factor")
        elif spec.kind == "binary":
            assert spec.threshold is not None
            require_float32(spec.threshold, field=f"Meter '{self.name}' binary threshold")


@dataclass(frozen=True)
class EffectDeclaration:
    """An effects.yaml effect's declared parameters — the inputs to `effect_static_payload`."""

    id: str
    scope: str
    duration: int
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
    """One compiled slot bound to exactly one filler in declaration order."""

    slot_index: int
    filler_kind: FillerKind
    filler_ref: str

    def __post_init__(self) -> None:
        if self.slot_index < 0:
            raise ValueError(f"SlotBinding slot_index must be >= 0, got {self.slot_index}")
        if self.filler_kind not in get_args(FillerKind):
            raise ValueError(f"SlotBinding filler_kind must be static|dynamic, got {self.filler_kind!r}")
        if not self.filler_ref:
            raise ValueError("SlotBinding filler_ref must name the declaration it is bound to")


@dataclass(frozen=True)
class TokenContext:
    """One named effect-catalog row and its complete fixed payload."""

    context_ref: str
    fixed_payload: tuple[float, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "fixed_payload", tuple(self.fixed_payload))


def _canonical_fixed_payload(type_name: str, payload: Sequence[float], *, field: str) -> tuple[float, ...]:
    expected_width = len(PAYLOAD_SCHEMAS[type_name])
    if len(payload) != expected_width:
        raise ValueError(f"{field} has {len(payload)} features, expected {expected_width}")
    canonical: list[float] = []
    for feature_index, feature in enumerate(payload):
        if isinstance(feature, bool) or not isinstance(feature, int | float):
            raise ValueError(f"{field} feature {feature_index} must be a finite float, got {feature!r}")
        value = float(feature)
        if not math.isfinite(value):
            raise ValueError(f"{field} feature {feature_index} must be finite, got {feature!r}")
        if not -1.0 <= value <= 1.0:
            raise ValueError(f"{field} feature {feature_index} must be within [-1, 1], got {feature!r}")
        canonical.append(require_float32(value, field=f"{field} feature {feature_index}"))
    return tuple(canonical)


@dataclass(frozen=True)
class TokenTypeSchema:
    """One token type in a compiled universe: its (engine-constant) payload schema, compiled
    capacity, slot bindings, and census count."""

    type_name: str
    payload_features: tuple[str, ...]
    capacity: int
    slot_bindings: tuple[SlotBinding, ...]
    slot_context_payloads: tuple[tuple[float, ...], ...]
    effect_catalog_contexts: tuple[TokenContext, ...]

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
        object.__setattr__(self, "slot_context_payloads", tuple(tuple(payload) for payload in self.slot_context_payloads))
        object.__setattr__(self, "effect_catalog_contexts", tuple(self.effect_catalog_contexts))
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
        if self.type_name == "effect":
            if self.slot_context_payloads:
                raise ValueError("Token type 'effect': slot_context_payloads must be empty; effect identity comes from the catalog")
            refs = [context.context_ref for context in self.effect_catalog_contexts]
            if any(not ref for ref in refs):
                raise ValueError("Token type 'effect': effect catalog context_ref must be nonempty")
            if len(set(refs)) != len(refs):
                raise ValueError(f"Token type 'effect': effect catalog context_ref values must be unique, got {refs!r}")
            canonical_contexts = tuple(
                TokenContext(
                    context_ref=context.context_ref,
                    fixed_payload=_canonical_fixed_payload(
                        self.type_name,
                        context.fixed_payload,
                        field=f"Token type 'effect' catalog context {context.context_ref!r} fixed_payload",
                    ),
                )
                for context in self.effect_catalog_contexts
            )
            object.__setattr__(self, "effect_catalog_contexts", canonical_contexts)
        else:
            if self.effect_catalog_contexts:
                raise ValueError(f"Token type {self.type_name!r}: effect_catalog_contexts must be empty")
            if len(self.slot_context_payloads) != self.capacity:
                raise ValueError(
                    f"Token type {self.type_name!r}: capacity {self.capacity} but "
                    f"{len(self.slot_context_payloads)} slot context payloads"
                )
            object.__setattr__(
                self,
                "slot_context_payloads",
                tuple(
                    _canonical_fixed_payload(
                        self.type_name,
                        payload,
                        field=f"Token type {self.type_name!r} slot {slot_index} context payload",
                    )
                    for slot_index, payload in enumerate(self.slot_context_payloads)
                ),
            )

    @property
    def payload_width(self) -> int:
        return len(self.payload_features)

    @property
    def fixed_row_width(self) -> int:
        """Presence plus the complete projected payload consumed by the network."""
        return 1 + self.payload_width

    @property
    def census(self) -> int:
        return len(self.slot_bindings)


def build_token_type(
    type_name: str,
    slot_bindings: Sequence[SlotBinding],
    *,
    slot_context_payloads: Sequence[Sequence[float]],
    effect_catalog_contexts: Sequence[TokenContext],
) -> TokenTypeSchema:
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
        slot_context_payloads=tuple(tuple(payload) for payload in slot_context_payloads),
        effect_catalog_contexts=tuple(effect_catalog_contexts),
    )


@dataclass(frozen=True)
class CompactTokenTypeLayout:
    """Immutable compact and fixed-row metadata for one token type."""

    type_name: str
    start: int
    end: int
    capacity: int
    compact_row_width: int
    fixed_row_width: int
    dynamic_features: tuple[str, ...]
    fixed_scatter_indices: tuple[int | None, ...]


@dataclass(frozen=True)
class CompactTokenLayout:
    """Derived metadata for the sole compact env/replay transport."""

    types: tuple[CompactTokenTypeLayout, ...]
    dynamic_total_dims: int

    def get_type(self, type_name: str) -> CompactTokenTypeLayout | None:
        for token_type in self.types:
            if token_type.type_name == type_name:
                return token_type
        return None


@dataclass(frozen=True)
class TokenSpec:
    """The compiler's token artifact (spec §2): type schemas in engine-canonical roster order.

    Serialization is compact dynamic state. The fixed projected rows exist only for the
    network boundary and are described separately by ``fixed_*`` derivations.
    """

    types: tuple[TokenTypeSchema, ...]
    position_rank: int
    transport_version: str
    encoding_version: str = ENCODING_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "types", tuple(self.types))
        if self.encoding_version != ENCODING_VERSION:
            raise ValueError(
                f"TokenSpec encoding_version must be the engine's exact current version "
                f"{ENCODING_VERSION!r}, got {self.encoding_version!r}"
            )
        if isinstance(self.position_rank, bool) or not isinstance(self.position_rank, int):
            raise ValueError(f"TokenSpec position_rank must be an integer, got {self.position_rank!r}")
        if not 0 <= self.position_rank <= MAX_POSITION_RANK:
            raise ValueError(f"TokenSpec position_rank must be within [0, {MAX_POSITION_RANK}], got {self.position_rank}")
        if self.transport_version != TOKEN_TRANSPORT_VERSION:
            raise ValueError(
                f"TokenSpec transport_version must be the engine's exact current version "
                f"{TOKEN_TRANSPORT_VERSION!r}, got {self.transport_version!r}"
            )
        names = [t.type_name for t in self.types]
        if len(set(names)) != len(names):
            raise ValueError(f"TokenSpec has duplicate token types: {names}")
        order = [TOKEN_TYPE_ROSTER.index(n) for n in names]
        if order != sorted(order):
            raise ValueError(f"TokenSpec types must follow engine roster order {TOKEN_TYPE_ROSTER}; got {names}")

    @property
    def total_dims(self) -> int:
        return self.compact_layout().dynamic_total_dims

    @property
    def fixed_total_dims(self) -> int:
        return sum(t.capacity * t.fixed_row_width for t in self.types)

    @property
    def census(self) -> dict[str, int]:
        return {t.type_name: t.census for t in self.types}

    def get_type(self, type_name: str) -> TokenTypeSchema | None:
        for t in self.types:
            if t.type_name == type_name:
                return t
        return None

    def row_layout(self) -> tuple[tuple[str, int, int, int], ...]:
        """Compact (type_name, slot_index, start, end) rows in transport order."""
        layout = self.compact_layout()
        rows: list[tuple[str, int, int, int]] = []
        offset = 0
        for t in self.types:
            type_layout = layout.get_type(t.type_name)
            assert type_layout is not None
            for binding in t.slot_bindings:
                rows.append(
                    (
                        t.type_name,
                        binding.slot_index,
                        offset,
                        offset + type_layout.compact_row_width,
                    )
                )
                offset += type_layout.compact_row_width
        return tuple(rows)

    def fixed_row_layout(self) -> tuple[tuple[str, int, int, int], ...]:
        """Fixed projected rows consumed only at the network boundary."""
        rows: list[tuple[str, int, int, int]] = []
        offset = 0
        for token_type in self.types:
            for binding in token_type.slot_bindings:
                rows.append(
                    (
                        token_type.type_name,
                        binding.slot_index,
                        offset,
                        offset + token_type.fixed_row_width,
                    )
                )
                offset += token_type.fixed_row_width
        return tuple(rows)

    def compact_layout(self) -> CompactTokenLayout:
        """Derive compact lane order, offsets, widths, and fixed-row scatter metadata."""
        rank = self.position_rank
        position = tuple(f"position_{index}" for index in range(rank))
        velocity = tuple(f"velocity_{index}" for index in range(rank))
        egocentric = tuple(f"egocentric_{index}" for index in range(rank))
        dynamic_features: dict[str, tuple[str, ...]] = {
            "self": ("presence",) + position + velocity,
            "meter": ("presence", "value_0", "value_1"),
            "affordance": ("presence",) + position + egocentric,
            "agent": ("presence",) + position + egocentric,
            "item": ("presence",) + position + egocentric + ("carried", "owner_slot", "owner_slot_applicable"),
            "effect": (
                "presence",
                "context_index",
                "remaining_fraction",
                "live_intensity",
                "owner_slot",
                "owner_slot_applicable",
            ),
            "variable_element": ("presence", "value_0", "value_1"),
        }
        type_layouts: list[CompactTokenTypeLayout] = []
        offset = 0
        for token_type in self.types:
            type_name = token_type.type_name
            features = dynamic_features[type_name]
            indices: list[int | None] = []
            for feature in features:
                if feature == "presence":
                    indices.append(0)
                elif feature == "context_index":
                    indices.append(None)
                else:
                    indices.append(1 + PAYLOAD_SCHEMAS[type_name].index(feature))
            end = offset + token_type.capacity * len(features)
            type_layouts.append(
                CompactTokenTypeLayout(
                    type_name=type_name,
                    start=offset,
                    end=end,
                    capacity=token_type.capacity,
                    compact_row_width=len(features),
                    fixed_row_width=token_type.fixed_row_width,
                    dynamic_features=features,
                    fixed_scatter_indices=tuple(indices),
                )
            )
            offset = end
        return CompactTokenLayout(
            types=tuple(type_layouts),
            dynamic_total_dims=offset,
        )


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
    _require_normalization_float32(var_id, spec)
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
            return require_float32(value[0], field=where)
        if len(value) != element_count:
            raise ValueError(
                f"{where} lists {len(value)} values but the variable has {element_count} elements; "
                "declare one value per element (row-major over the shape) or a single scalar"
            )
        return require_float32(value[element_index], field=where)
    return require_float32(value, field=where)


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


def _element_default(default: object, element_index: int, element_count: int, *, where: str) -> float:
    """The declared initial of one element, flattened row-major; scalars broadcast."""
    if default is None:
        return 0.0
    flat = list(_flatten(default))
    if len(flat) == element_count:
        return require_float32(flat[element_index], field=where)
    if len(flat) == 1:
        return require_float32(flat[0], field=where)
    raise ValueError(f"Declared default has {len(flat)} elements but the variable has {element_count}")


def normalize_declared_scalar(value: float, spec: NormalizationSpec, *, element_index: int, element_count: int) -> float:
    """Apply a bounded normalization kind to one declared scalar (the descriptor's 'normalized
    declared initial'). For cyclical_sin_cos the descriptor carries the phase fraction, not the
    sin/cos pair — the pair is the value block's job."""
    value = require_float32(value, field="declared initial")
    kind = spec.kind
    if kind == "minmax" or kind == "log_scaled":
        lo = _element_param(spec.min, element_index, element_count=element_count, where="normalization.min")
        hi = _element_param(spec.max, element_index, element_count=element_count, where="normalization.max")
        assert lo is not None and hi is not None
        v = min(max(value, lo), hi) if spec.clip else value
        if kind == "minmax":
            normalized = (v - lo) / (hi - lo)
        else:
            normalized = math.log1p(v - lo) / math.log1p(hi - lo)
        return require_float32(normalized, field="normalized declared initial")
    if kind == "cyclical_sin_cos":
        assert spec.period is not None
        period = require_float32(spec.period, field="normalization.period")
        return require_float32((value % period) / period, field="normalized declared initial")
    if kind == "binary":
        assert spec.threshold is not None
        threshold = require_float32(spec.threshold, field="normalization.threshold")
        return 1.0 if value > threshold else 0.0
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
    bounded = (
        0.0 if lo is None else saturate_signed(lo),
        0.0 if hi is None else saturate_signed(hi),
        0.0 if clip is None else clip,
        0.0 if scale is None else saturate_signed(float(scale)),
    )
    return _float32_tuple(bounded + (1.0 if absent else 0.0,), field="normalization descriptor")


def describe_variable(var: ExposedVariable, *, element_index: int, owner_capacity: int | None) -> tuple[float, ...]:
    """The variable-descriptor block for one element (spec §1): fixed-width, name-free, built
    from the declaration. Width == DESCRIPTOR_BLOCK_WIDTH."""
    spec = require_exposure_normalization(var.id, var.normalization)
    if var.owner_slot is not None:
        if owner_capacity is None or owner_capacity <= 0:
            raise ValueError(f"Variable '{var.id}' carries owner_slot {var.owner_slot} but no owner capacity was given")
        if not 0 <= var.owner_slot < owner_capacity:
            raise ValueError(f"Variable '{var.id}' owner_slot {var.owner_slot} must be within compiled capacity {owner_capacity}")
        owner = (var.owner_slot / owner_capacity, 1.0)
    else:
        owner = (0.0, 0.0)
    count = var.element_count
    declared = _element_default(var.default, element_index, count, where=f"Variable '{var.id}' default")
    initial = normalize_declared_scalar(declared, spec, element_index=element_index, element_count=count)
    block = (
        _one_hot(SCOPE_VOCABULARY, var.scope)
        + _one_hot(SEMANTIC_TYPE_VOCABULARY, var.semantic_type)
        + _one_hot(NORMALIZATION_KIND_VOCABULARY, spec.kind)
        + normalization_param_vector(spec, element_index=element_index, element_count=count)
        + _one_hot(DTYPE_VOCABULARY, _VARIABLE_TYPE_DTYPE[var.type])
        + _one_hot(LIFETIME_VOCABULARY, var.lifetime)
        + (initial, saturate(math.log1p(var.element_count)))
        + owner
    )
    assert len(block) == DESCRIPTOR_BLOCK_WIDTH
    bounded_block = _float32_tuple(block, field=f"Variable '{var.id}' descriptor")
    if any(not -1.0 <= feature <= 1.0 for feature in bounded_block):
        raise ValueError(f"Variable '{var.id}' descriptor features must all be within [-1, 1]")
    return bounded_block


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
    into [-1, 1]: the initial as its position within [min, max]; each declared rate (meter units
    per tick) as a fraction of the declared range, saturated by x/(1+x) so a money-scale rate
    cannot blow up the token; the range itself as a saturated log1p. Absolute normalization
    bounds/scale deliberately carry the declared units, while the behavioral-rate portion is
    scale-free."""
    span = meter.max - meter.min
    if span <= 0:
        raise ValueError(f"Meter '{meter.name}': bounds must satisfy min < max")
    initial = min(max((meter.initial - meter.min) / span, 0.0), 1.0)
    spec = meter.normalization
    if spec.kind in _RANGE_KINDS:
        assert isinstance(spec.min, float) and isinstance(spec.max, float)
        normalization_min = saturate_signed(spec.min)
        normalization_max = saturate_signed(spec.max)
    else:
        normalization_min = 0.0
        normalization_max = 0.0
    if spec.kind == "cyclical_sin_cos":
        assert spec.period is not None
        normalization_scale = saturate(spec.period)
    elif spec.kind == "binary":
        assert spec.threshold is not None
        normalization_scale = saturate_signed(spec.threshold)
    else:
        normalization_scale = 0.0
    signature = (
        initial,
        1.0 if meter.lethal_min else 0.0,
        1.0 if meter.lethal_max else 0.0,
        saturate_signed(meter.passive_depletion / span),
        saturate_signed(meter.move_depletion / span),
        saturate_signed(meter.interact_depletion / span),
        saturate_signed(meter.natural_recovery / span),
        saturate(math.log1p(span)),
        *_one_hot(METER_NORMALIZATION_KIND_VOCABULARY, spec.kind),
        normalization_min,
        normalization_max,
        normalization_scale,
    )
    assert len(signature) == METER_SIGNATURE_WIDTH
    return _float32_tuple(signature, field=f"Meter '{meter.name}' static signature")


def affordance_signature(
    *,
    affordance: AffordanceParamConfig,
    effect_deltas: Sequence[AffordanceMeterWrite],
    meters: Mapping[str, MeterDeclaration],
) -> tuple[float, ...]:
    """Immutable compiled identity for one affordance slot."""
    name = affordance.name
    interaction_type = str(affordance.interaction_type)
    if interaction_type not in INTERACTION_TYPE_VOCABULARY:
        raise ValueError(f"Affordance {name!r}: interaction_type {interaction_type!r} is not in " f"{INTERACTION_TYPE_VOCABULARY}")
    duration_applicable = affordance.duration_ticks is not None
    if affordance.duration_ticks is not None:
        duration = saturate(float(affordance.duration_ticks))
    else:
        duration = 0.0
    signature = (
        *_one_hot(INTERACTION_TYPE_VOCABULARY, interaction_type),
        float(duration_applicable),
        duration,
        *opening_hours_signature(affordance.opening_hours),
        *effect_summary(effect_deltas, meters),
        saturate(float(len(effect_deltas))),
    )
    assert len(signature) == AFFORDANCE_SIGNATURE_WIDTH
    return _float32_tuple(signature, field=f"Affordance {name!r} static signature")


def effect_static_payload(effect: EffectDeclaration) -> tuple[float, ...]:
    """An effect's declared-identity features (len(EFFECT_STATIC_FEATURES) wide, all bounded):
    scope one-hot, saturated log1p(duration), and reapply-policy one-hot. The runtime
    appends remaining fraction, live spawn intensity, and owner coordinates."""
    return _float32_tuple(
        _one_hot(EFFECT_SCOPE_VOCABULARY, effect.scope)
        + (saturate(math.log1p(effect.duration)),)
        + _one_hot(REAPPLY_POLICY_VOCABULARY, effect.reapply_policy),
        field=f"Effect '{effect.id}' static payload",
    )


def effect_summary(deltas: Sequence[AffordanceMeterWrite], meters: Mapping[str, MeterDeclaration]) -> tuple[float, ...]:
    """Encode the fixed-K affordance write summary.

    Unknown magnitudes rank first in stable declaration order. Every known magnitude
    follows in descending target-relative order, stable for ties. More than K reachable
    writes refuse: silently omitting behavior would alias distinct affordances.
    """
    if len(deltas) > EFFECT_SUMMARY_K:
        raise ValueError(
            f"Affordance declares {len(deltas)} reachable meter writes; EFFECT_SUMMARY_K={EFFECT_SUMMARY_K} "
            "permits at most that many without aliasing behavior"
        )
    unknown_entries: list[tuple[AffordanceMeterWrite, float, float, MeterDeclaration]] = []
    known_entries: list[tuple[AffordanceMeterWrite, float, float, MeterDeclaration]] = []
    for write in deltas:
        meter = meters.get(write.meter_name)
        if meter is None:
            raise ValueError(f"Effect targets meter '{write.meter_name}' which is not declared")
        if write.delta is None:
            magnitude = 0.0
            sign = 0.0
        else:
            if not math.isfinite(write.delta):
                raise ValueError(f"Effect delta targeting meter '{write.meter_name}' must be finite, got {write.delta}")
            magnitude = min(abs(write.delta) / (meter.max - meter.min), 1.0)
            if write.delta != 0:
                sign = math.copysign(1.0, write.delta)
            else:
                sign = 0.0
        entry = (write, magnitude, sign, meter)
        if write.delta is None:
            unknown_entries.append(entry)
        else:
            known_entries.append(entry)
    known_entries.sort(key=lambda entry: entry[1], reverse=True)
    ranked = unknown_entries + known_entries
    out: list[float] = []
    for k in range(EFFECT_SUMMARY_K):
        if k < len(ranked):
            write, magnitude, sign, meter = ranked[k]
            spawned = write.spawned_effect
            if spawned is not None:
                spawn_identity = (
                    *_one_hot(SPAWN_EFFECT_TARGETS, spawned.target),
                    saturate_signed(spawned.intensity),
                    saturate(math.log1p(spawned.duration)),
                    *_one_hot(EFFECT_SCOPE_VOCABULARY, spawned.scope),
                    *_one_hot(REAPPLY_POLICY_VOCABULARY, spawned.reapply_policy),
                    float(spawned.observable),
                )
            else:
                spawn_identity = (0.0,) * len(SPAWN_EFFECT_IDENTITY_FEATURES)
            out.extend(
                (
                    float(write.form),
                    *_one_hot(AFFORDANCE_LIFECYCLE_STAGES, write.stage),
                    *_one_hot(AFFORDANCE_WRITE_SOURCES, write.source),
                    *_one_hot(AFFORDANCE_WRITE_TARGETS, write.target),
                    *spawn_identity,
                    magnitude,
                    sign,
                    *meter_signature(meter),
                )
            )
        else:
            out.extend((0.0,) * AFFORDANCE_EFFECT_ENTRY_WIDTH)
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


# --------------------------------------------------------------------------- canonical slot bindings


def variable_element_bindings(
    environment: EnvironmentConfig,
    compiled_vfs_profiles: CompiledVFSProfiles | None,
    vfs_variables: tuple[VariableDef, ...],
    *,
    item_capacity_value: int = 0,
) -> tuple[SlotBinding, ...]:
    """Derive variable-element bindings in registry declaration order."""
    bindings, _contexts = _variable_element_artifacts(
        environment, compiled_vfs_profiles, vfs_variables, item_capacity_value=item_capacity_value
    )
    return bindings


#: `ItemVFSVariableConfig.type` uses its own vocabulary. It is congruent with
#: `VariableDef`'s dtype-bearing members except for plain "float" (spelled "scalar" on
#: `VariableDef`) and plain "int" (`VariableDef` has no scalar-int member at all — only
#: typed references and integer vectors resolve to dtype "int"); a plain-int item
#: variable therefore has no token dtype landing yet and is refused explicitly below.
_ITEM_VAR_TYPE_TO_TOKEN_TYPE: Final[Mapping[str, str]] = {
    "float": "scalar",
    "bool": "bool",
    "vec2i": "vec2i",
    "vec3i": "vec3i",
    "agent_ref": "agent_ref",
    "item_ref": "item_ref",
    "affordance_ref": "affordance_ref",
    "effect_ref": "effect_ref",
}
#: Item-profile state has no authored `semantic_type` — `ItemVFSVariableConfig`
#: deliberately carries none (PDR-0075/0066: a per-variable observation group could
#: reach nothing for item-scoped state). Every exposed item variable lands in the
#: engine's own bucket; `scope` ("item") and `owner_slot` already distinguish it from
#: every other exposed variable, so an authored group is not needed to avoid collision.
_ITEM_PROFILE_SEMANTIC_TYPE: Final[str] = "custom"
#: Item-profile state has no authored `lifetime` either — item instances (and their
#: VFS rows) never survive `env.reset()`, so "episode" is the only member that matches
#: reality.
_ITEM_PROFILE_LIFETIME: Final[str] = "episode"


def _variable_element_artifacts(
    environment: EnvironmentConfig,
    compiled_vfs_profiles: CompiledVFSProfiles | None,
    vfs_variables: tuple[VariableDef, ...],
    *,
    item_capacity_value: int = 0,
) -> tuple[tuple[SlotBinding, ...], tuple[tuple[float, ...], ...]]:
    """Derive variable bindings and their complete fixed payloads in one pass."""
    env_semantic = {var.name: str(var.semantic_type) for var in environment.environment.variables}

    exposed_profile: dict[str, str] = {}
    exposed_item_vars: list[tuple[str, CompiledVariable]] = []  # (id "<profile>.<var>", declaration)
    if compiled_vfs_profiles is not None:
        for profile in (compiled_vfs_profiles.global_profile, compiled_vfs_profiles.agent_profile):
            if profile is None:
                continue
            for compiled_var in profile.variables:
                if compiled_var.exposed_to:
                    exposed_profile[str(compiled_var.name)] = str(compiled_var.semantic_type)
        for profile_name, item_profile in (compiled_vfs_profiles.item_profiles or {}).items():
            for compiled_var in item_profile.variables:
                if compiled_var.exposed_to:
                    exposed_item_vars.append((f"{profile_name}.{compiled_var.name}", compiled_var))

    if exposed_item_vars and item_capacity_value <= 0:
        names = ", ".join(var_id for var_id, _ in exposed_item_vars)
        raise ValueError(
            f"Item-profile variable(s) {names} declare exposed_to, but this universe's compiled `item` token "
            "capacity is 0 (no items.yaml, or max_items_in_world + max_items_per_agent × agents_per_world sums "
            "to 0) — there is no item-arena slot for an exposed item variable to bind against."
        )

    bindings: list[SlotBinding] = []
    contexts: list[tuple[float, ...]] = []
    bound: list[ExposedVariable] = []

    def emit(exposed: ExposedVariable, *, owner_capacity: int | None) -> None:
        bound.append(exposed)
        descriptor_blocks = tuple(
            describe_variable(exposed, element_index=i, owner_capacity=owner_capacity) for i in range(exposed.element_count)
        )
        assert exposed.normalization is not None
        width_used = value_block_width_used(exposed.normalization) / VALUE_BLOCK_WIDTH
        for element_index, descriptor_block in enumerate(descriptor_blocks):
            if exposed.owner_slot is not None:
                filler_ref = f"{exposed.id}[{exposed.owner_slot}]"
            elif exposed.element_count == 1:
                filler_ref = exposed.id
            else:
                filler_ref = f"{exposed.id}[{element_index}]"
            bindings.append(
                SlotBinding(
                    slot_index=len(bindings),
                    filler_kind="static",
                    filler_ref=filler_ref,
                )
            )
            payload = [0.0] * len(PAYLOAD_SCHEMAS["variable_element"])
            coordinates = element_coordinate_block(exposed.shape, element_index)
            position_start = PAYLOAD_SCHEMAS["variable_element"].index("position_0")
            descriptor_start = PAYLOAD_SCHEMAS["variable_element"].index(DESCRIPTOR_BLOCK_FEATURES[0])
            payload[position_start : position_start + MAX_POSITION_RANK + 1] = coordinates
            payload[PAYLOAD_SCHEMAS["variable_element"].index("value_width_used")] = width_used
            payload[descriptor_start : descriptor_start + DESCRIPTOR_BLOCK_WIDTH] = descriptor_block
            contexts.append(_float32_tuple(payload, field=f"Variable '{exposed.id}' fixed payload"))

    for var_def in vfs_variables:
        var_id = var_def.id
        if var_id in env_semantic:
            semantic_type = env_semantic[var_id]
        elif var_id in exposed_profile:
            semantic_type = exposed_profile[var_id]
        elif var_def.exposed_to:
            raise ValueError(
                f"Variable '{var_id}' (variables_reference.yaml overlay) declares exposed_to, but overlay "
                "statics have no semantic_type surface and cannot bind variable_element slots yet. "
                "Declare the variable in vfs_profiles.yaml to expose it."
            )
        else:
            continue

        if var_def.initial_value_mode is not None or var_def.initial_value_params is not None:
            raise ValueError(
                f"Exposed variable '{var_id}' reached variable_element binding with "
                f"initial_value_mode={var_def.initial_value_mode!r} and initial_value_params={var_def.initial_value_params!r}; "
                "the compiler must lower initialization to one explicit declared default"
            )
        if var_def.default is None:
            raise ValueError(
                f"Exposed variable '{var_id}' must have one explicit declared default before variable_element binding; got default=None"
            )

        if isinstance(var_def.scope, VariableScope):
            scope = var_def.scope.value
        else:
            scope = str(var_def.scope)
        if var_def.shape:
            shape = tuple(var_def.shape)
        elif var_def.dims is not None and var_def.dims > 1:
            shape = (int(var_def.dims),)
        else:
            shape = ()
        emit(
            ExposedVariable(
                var_id,
                scope,
                semantic_type,
                var_def.type,
                var_def.lifetime,
                var_def.default,
                shape,
                var_def.normalization,
            ),
            owner_capacity=None,
        )

    for var_id, item_var in exposed_item_vars:
        mapped_type = _ITEM_VAR_TYPE_TO_TOKEN_TYPE.get(item_var.type)
        if mapped_type is None:
            raise ValueError(
                f"Item-profile variable '{var_id}' declares type {item_var.type!r}, which has no token "
                "dtype landing yet — expose a float, bool, vec2i/vec3i, or *_ref item variable instead."
            )
        for owner_slot in range(item_capacity_value):
            emit(
                ExposedVariable(
                    var_id,
                    "item",
                    _ITEM_PROFILE_SEMANTIC_TYPE,
                    mapped_type,
                    _ITEM_PROFILE_LIFETIME,
                    item_var.initial_value,
                    (),
                    item_var.normalization,
                    owner_slot=owner_slot,
                ),
                owner_capacity=item_capacity_value,
            )

    check_indistinguishability(bound, owner_capacity=item_capacity_value or None)
    return tuple(bindings), tuple(contexts)


def effect_slot_refs(
    *,
    max_active_effects: Mapping[str, int] | None,
    declared_agents_per_world: int | None,
    item_capacity_value: int,
    affordance_capacity_value: int,
) -> tuple[str, ...]:
    """Derive the exact scope-blocked effect slot references."""
    if max_active_effects is None:
        return ()
    denominators = {
        "global": 1,
        "agent": _agents_per_world(declared_agents_per_world),
        "item": item_capacity_value,
        "affordance": affordance_capacity_value,
    }
    refs: list[str] = []
    for scope in EFFECT_SCOPE_VOCABULARY:
        block = max_active_effects[scope] * denominators[scope]
        refs.extend(f"effect:{scope}:{i}" for i in range(block))
    return tuple(refs)


def canonical_token_bindings(
    *,
    meter_declarations: tuple[MeterDeclaration, ...],
    affordances: AffordancesV2Config,
    items_catalog: ItemsCatalogConfig | None,
    compiled_effect_catalog: EffectCatalog | None,
    environment: EnvironmentConfig,
    compiled_vfs_profiles: CompiledVFSProfiles | None,
    vfs_variables: tuple[VariableDef, ...],
) -> tuple[tuple[TokenType, tuple[SlotBinding, ...]], ...]:
    """Derive every token type's complete slot bindings from persisted authorities.

    This is the single compiler/loader boundary for token capacity, binding order,
    references, and static signatures. It never reads an existing ``TokenSpec``.
    """
    meter_names = [meter.name for meter in meter_declarations]
    if len(set(meter_names)) != len(meter_names):
        raise ValueError("meter declarations contain duplicate names; meter token identity must be unique")
    meter_bindings = tuple(
        SlotBinding(
            slot_index=index,
            filler_kind="static",
            filler_ref=meter.name,
        )
        for index, meter in enumerate(meter_declarations)
    )

    affordance_names = [affordance.name for affordance in affordances.affordances]
    if len(set(affordance_names)) != len(affordance_names):
        raise ValueError("affordances.yaml declares duplicate names; affordance token identity must be unique")
    affordance_bindings = tuple(
        SlotBinding(
            slot_index=index,
            filler_kind="static",
            filler_ref=affordance.name,
        )
        for index, affordance in enumerate(affordances.affordances)
    )

    if items_catalog is None:
        item_capacity_value = 0
    else:
        item_capacity_value = item_capacity(
            max_items_in_world=items_catalog.max_items_in_world,
            max_items_per_agent=items_catalog.max_items_per_agent,
            declared_agents_per_world=None,
        )
    item_bindings = tuple(
        SlotBinding(slot_index=index, filler_kind="dynamic", filler_ref=f"item:{index}") for index in range(item_capacity_value)
    )

    if compiled_effect_catalog is not None:
        declared_effect_count = len(compiled_effect_catalog.effects)
        max_active_effects = compiled_effect_catalog.max_active_effects
    else:
        declared_effect_count = 0
        max_active_effects = None
    expected_effect_capacity = effect_capacity(
        max_active_effects=max_active_effects,
        declared_effect_count=declared_effect_count,
        declared_agents_per_world=None,
        item_capacity_value=item_capacity_value,
        affordance_capacity_value=len(affordance_bindings),
    )
    effect_refs = effect_slot_refs(
        max_active_effects=max_active_effects if declared_effect_count else None,
        declared_agents_per_world=None,
        item_capacity_value=item_capacity_value,
        affordance_capacity_value=len(affordance_bindings),
    )
    if len(effect_refs) != expected_effect_capacity:
        raise ValueError(
            "Effect token slot layout disagrees with its declared capacity; canonical effect derivations must "
            "consume the same persisted budget and denominators"
        )
    effect_bindings = tuple(SlotBinding(slot_index=index, filler_kind="dynamic", filler_ref=ref) for index, ref in enumerate(effect_refs))

    by_type: Mapping[TokenType, tuple[SlotBinding, ...]] = {
        "self": (SlotBinding(slot_index=0, filler_kind="static", filler_ref="self"),),
        "meter": meter_bindings,
        "affordance": affordance_bindings,
        "agent": (),
        "item": item_bindings,
        "effect": effect_bindings,
        "variable_element": variable_element_bindings(
            environment, compiled_vfs_profiles, vfs_variables, item_capacity_value=item_capacity_value
        ),
    }
    return tuple((type_name, by_type[type_name]) for type_name in TOKEN_TYPE_ROSTER)


def _fixed_payload(type_name: str, values: Mapping[str, float]) -> tuple[float, ...]:
    payload = [0.0] * len(PAYLOAD_SCHEMAS[type_name])
    for feature, value in values.items():
        payload[PAYLOAD_SCHEMAS[type_name].index(feature)] = value
    return _float32_tuple(payload, field=f"Token type {type_name!r} fixed payload")


def canonical_token_contexts(
    *,
    position_rank: int,
    meter_declarations: tuple[MeterDeclaration, ...],
    affordances: AffordancesV2Config,
    items_catalog: ItemsCatalogConfig | None,
    compiled_effect_catalog: EffectCatalog | None,
    environment: EnvironmentConfig,
    compiled_vfs_profiles: CompiledVFSProfiles | None,
    vfs_variables: tuple[VariableDef, ...],
) -> tuple[tuple[TokenType, tuple[tuple[float, ...], ...], tuple[TokenContext, ...]], ...]:
    """Derive each type's immutable fixed payload table from persisted declarations."""
    rank = require_position_rank(position_rank, substrate_type="compiled TokenSpec")
    rank_value = rank / MAX_POSITION_RANK
    rank_context = {"position_rank": rank_value}

    meter_contexts = tuple(
        _fixed_payload(
            "meter",
            {
                "value_width_used": value_block_width_used(meter.normalization) / VALUE_BLOCK_WIDTH,
                **dict(zip(METER_SIGNATURE_FEATURES, meter_signature(meter), strict=True)),
            },
        )
        for meter in meter_declarations
    )

    meters_by_name = {meter.name: meter for meter in meter_declarations}
    affordance_static_features = (
        tuple(f"interaction_type_{member}" for member in INTERACTION_TYPE_VOCABULARY)
        + AFFORDANCE_DURATION_FEATURES
        + OPENING_HOURS_FEATURES
        + _effect_summary_features()
        + ("effect_count",)
    )
    affordance_contexts = tuple(
        _fixed_payload(
            "affordance",
            rank_context
            | dict(
                zip(
                    affordance_static_features,
                    affordance_signature(
                        affordance=affordance,
                        effect_deltas=extract_affordance_meter_writes(affordance, effect_catalog=compiled_effect_catalog),
                        meters=meters_by_name,
                    ),
                    strict=True,
                )
            ),
        )
        for affordance in affordances.affordances
    )

    if items_catalog is None:
        item_capacity_value = 0
    else:
        item_capacity_value = item_capacity(
            max_items_in_world=items_catalog.max_items_in_world,
            max_items_per_agent=items_catalog.max_items_per_agent,
            declared_agents_per_world=None,
        )
    item_contexts = tuple(_fixed_payload("item", rank_context) for _ in range(item_capacity_value))

    _variable_bindings, variable_contexts = _variable_element_artifacts(
        environment, compiled_vfs_profiles, vfs_variables, item_capacity_value=item_capacity_value
    )

    effect_contexts: tuple[TokenContext, ...] = ()
    if compiled_effect_catalog is not None:
        if len(compiled_effect_catalog.effects) > 2**24:
            raise ValueError("Effect catalog has more than 2**24 entries; float32 context indices would not remain exact")
        name_to_id = compiled_effect_catalog.effect_name_to_id
        if name_to_id is None:
            name_to_id = {}
        ordered_effects = sorted(compiled_effect_catalog.effects.values(), key=lambda effect: name_to_id[effect.id])
        effect_contexts = tuple(
            TokenContext(
                context_ref=f"effect:{effect.id}",
                fixed_payload=_fixed_payload(
                    "effect",
                    dict(
                        zip(
                            EFFECT_STATIC_FEATURES,
                            effect_static_payload(
                                EffectDeclaration(
                                    id=effect.id,
                                    scope=effect.scope,
                                    duration=effect.duration,
                                    reapply_policy=effect.reapply_policy,
                                )
                            ),
                            strict=True,
                        )
                    ),
                ),
            )
            for effect in ordered_effects
        )

    by_type: Mapping[TokenType, tuple[tuple[tuple[float, ...], ...], tuple[TokenContext, ...]]] = {
        "self": ((_fixed_payload("self", rank_context),), ()),
        "meter": (meter_contexts, ()),
        "affordance": (affordance_contexts, ()),
        "agent": ((), ()),
        "item": (item_contexts, ()),
        "effect": ((), effect_contexts),
        "variable_element": (variable_contexts, ()),
    }
    return tuple((type_name, *by_type[type_name]) for type_name in TOKEN_TYPE_ROSTER)


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
    "AFFORDANCE_DURATION_FEATURES",
    "AFFORDANCE_EFFECT_ENTRY_WIDTH",
    "AFFORDANCE_EFFECT_MAGNITUDE_OFFSET",
    "AFFORDANCE_EFFECT_METER_OFFSET",
    "AFFORDANCE_SIGNATURE_WIDTH",
    "DESCRIPTOR_BLOCK_FEATURES",
    "DESCRIPTOR_BLOCK_WIDTH",
    "DTYPE_FLAG_WIDTH",
    "EFFECT_STATIC_FEATURES",
    "EFFECT_SUMMARY_K",
    "ENCODING_VERSION",
    "LIFETIME_ONE_HOT_WIDTH",
    "MAX_POSITION_RANK",
    "MEAN_CENSUS_ADVISORY",
    "METER_NORMALIZATION_KIND_VOCABULARY",
    "METER_SIGNATURE_FEATURES",
    "METER_SIGNATURE_WIDTH",
    "NORMALIZATION_KIND_ONE_HOT_WIDTH",
    "NORMALIZATION_PARAM_VECTOR_WIDTH",
    "OWNER_SLOT_COORDINATE_WIDTH",
    "OPENING_HOURS_FEATURES",
    "PAYLOAD_SCHEMAS",
    "REAPPLY_POLICY_VOCABULARY",
    "RESERVED_TOKEN_TYPE_NAMES",
    "SPAWN_EFFECT_IDENTITY_FEATURES",
    "SCOPE_ONE_HOT_WIDTH",
    "SEMANTIC_TYPE_ONE_HOT_WIDTH",
    "TOKEN_TYPE_FILLER_KIND",
    "TOKEN_TYPE_ROSTER",
    "TOKEN_TRANSPORT_VERSION",
    "VALUE_BLOCK_WIDTH",
    "VARIABLE_TYPE_VOCABULARY",
    "CompactTokenLayout",
    "CompactTokenTypeLayout",
    "EffectDeclaration",
    "ExposedVariable",
    "MeterDeclaration",
    "SlotBinding",
    "TokenContext",
    "TokenSpec",
    "TokenType",
    "TokenTypeSchema",
    "affordance_capacity",
    "affordance_signature",
    "agent_capacity",
    "build_token_type",
    "canonical_token_bindings",
    "canonical_token_contexts",
    "check_indistinguishability",
    "describe_variable",
    "effect_capacity",
    "effect_slot_refs",
    "effect_static_payload",
    "effect_summary",
    "element_coordinate_block",
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
    "variable_element_bindings",
]
