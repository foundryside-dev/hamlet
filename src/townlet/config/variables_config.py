"""One explicit authoring contract for world-state variables."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, model_validator

from townlet.vfs.access_policy import validate_static_access
from townlet.vfs.schema import NormalizationSpec, VariableScope, VFSScopeExtents
from townlet.vfs.semantic_type import SemanticType

VariableType = Literal[
    "scalar",
    "bool",
    "vec2i",
    "vec3i",
    "vec2f",
    "vec3f",
    "vecNi",
    "vecNf",
    "agent_ref",
    "item_ref",
    "affordance_ref",
    "effect_ref",
    "tensor1d",
    "tensor2d",
    "tensor3d",
    "tensorNd",
    "message_token",
]
VariableLifetime = Literal["tick", "episode", "persistent"]
_REFERENCE_TYPES = frozenset({"agent_ref", "item_ref", "affordance_ref", "effect_ref"})
_TENSOR_TYPES = frozenset({"tensor1d", "tensor2d", "tensor3d", "tensorNd"})
_FIXED_VECTOR_WIDTHS = {"vec2i": 2, "vec3i": 3, "vec2f": 2, "vec3f": 3}


class VariableDeclaration(BaseModel):
    """Authored state semantics, independent of file and compiler subsystem."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    scope: VariableScope
    type: VariableType
    lifetime: VariableLifetime
    semantic_type: SemanticType
    readable_by: list[Literal["engine", "agent"]]
    writable_by: list[Literal["engine"]]
    exposed_to: list[Literal["agent"]]
    profile: str | None = None
    dims: StrictInt | None = None
    shape: list[StrictInt] | None = None
    initial_value: Any = None
    initial_value_mode: Literal["zeros", "ones", "eye", "random_normal", "random_uniform"] | None = None
    initial_value_params: dict[str, Any] | None = None
    expression: str | None = None
    normalization: NormalizationSpec | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_contract(self) -> VariableDeclaration:
        validate_static_access(self.id, self.readable_by, self.writable_by, self.exposed_to)
        if "[" in self.id or "]" in self.id:
            raise ValueError(f"Variable '{self.id}' cannot contain slot-index delimiters")
        has_literal = "initial_value" in self.model_fields_set
        has_mode = self.initial_value_mode is not None
        if has_literal == has_mode:
            raise ValueError(f"Variable '{self.id}' must declare exactly one initial_value or initial_value_mode")
        if self.initial_value_params is not None and not has_mode:
            raise ValueError(f"Variable '{self.id}' initial_value_params requires initial_value_mode")
        if self.expression is not None:
            if self.scope not in {VariableScope.GLOBAL, VariableScope.AGENT}:
                raise ValueError(f"Variable '{self.id}' expression execution supports global and agent scopes only")
            if has_mode:
                raise ValueError(f"Variable '{self.id}' expression requires literal initial_value, not initial_value_mode")
        if self.scope == VariableScope.ITEM:
            if not self.profile or "." in self.profile or "[" in self.profile or "]" in self.profile:
                raise ValueError(f"Item variable '{self.id}' requires a simple declared profile identifier")
            if "." in self.id:
                raise ValueError(f"Item variable '{self.id}' cannot contain profile separators")
            if self.type not in {"scalar", "bool", *_REFERENCE_TYPES}:
                raise ValueError(f"Item variable '{self.id}' type has no supported scalar item-arena storage")
            if self.lifetime != "episode":
                raise ValueError(f"Item variable '{self.id}' lifetime must be episode")
        elif self.profile is not None:
            raise ValueError(f"Variable '{self.id}' profile is only meaningful for item scope")
        if bool(self.exposed_to) != (self.normalization is not None):
            raise ValueError(f"Variable '{self.id}' normalization is required exactly when exposed_to is nonempty")
        if self.exposed_to and self.scope not in {VariableScope.GLOBAL, VariableScope.AGENT, VariableScope.ITEM}:
            raise ValueError(f"Variable '{self.id}' scope has no supported observation publisher")
        if self.exposed_to and self.scope != VariableScope.ITEM and self.type in {"bool", "vec2i", "vec3i", "vecNi", *_REFERENCE_TYPES}:
            raise ValueError(
                f"Variable '{self.id}' registry observation publisher requires float32 storage; type '{self.type}' is unsupported"
            )
        if self.type in _TENSOR_TYPES:
            if not self.shape or any(isinstance(axis, bool) or axis <= 0 for axis in self.shape):
                raise ValueError(f"Variable '{self.id}' tensor requires a positive shape")
            ranks = {"tensor1d": 1, "tensor2d": 2, "tensor3d": 3}
            if self.type in ranks and len(self.shape) != ranks[self.type]:
                raise ValueError(f"Variable '{self.id}' tensor shape has the wrong rank")
            if self.dims is not None:
                raise ValueError(f"Variable '{self.id}' tensor uses shape, not dims")
        elif self.shape is not None:
            raise ValueError(f"Variable '{self.id}' shape is only meaningful for tensor types")
        if self.type in {"vecNi", "vecNf", "message_token"}:
            if self.dims is None or self.dims <= 0:
                raise ValueError(f"Variable '{self.id}' requires dims")
        elif self.dims is not None:
            raise ValueError(f"Variable '{self.id}' does not use dims")
        if has_mode:
            if self.type not in _TENSOR_TYPES:
                raise ValueError(f"Variable '{self.id}' initial_value_mode requires tensor storage")
            assert self.shape is not None
            if self.initial_value_mode == "eye" and (len(self.shape) != 2 or self.shape[0] != self.shape[1]):
                raise ValueError(f"Variable '{self.id}' eye initialization requires square 2D shape")
            if self.initial_value_mode in {"random_normal", "random_uniform"}:
                if self.exposed_to:
                    raise ValueError(f"Variable '{self.id}' random initialization has no exact exposed initial value")
                if self.initial_value_mode == "random_normal":
                    required = {"mean", "std"}
                else:
                    required = {"low", "high"}
                if set(self.initial_value_params or {}) != required:
                    raise ValueError(f"Variable '{self.id}' random initializer requires explicit {sorted(required)} parameters")
                assert self.initial_value_params is not None
                if any(
                    isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value)
                    for value in self.initial_value_params.values()
                ):
                    raise ValueError(f"Variable '{self.id}' random initializer parameters must be finite numbers")
                if self.initial_value_mode == "random_normal" and self.initial_value_params["std"] < 0:
                    raise ValueError(f"Variable '{self.id}' random initializer std must be nonnegative")
                if self.initial_value_mode == "random_uniform" and self.initial_value_params["low"] > self.initial_value_params["high"]:
                    raise ValueError(f"Variable '{self.id}' random initializer requires low <= high")
            elif self.initial_value_params is not None:
                raise ValueError(f"Variable '{self.id}' deterministic initialization accepts no initial_value_params")
        else:
            self._validate_literal()
        return self

    def _validate_literal(self) -> None:
        value = self.initial_value
        if value is None:
            if self.type not in _REFERENCE_TYPES:
                raise ValueError(f"Variable '{self.id}' null initial_value is only valid for an unbound reference")
            return
        if self.type == "bool":
            if not isinstance(value, bool):
                raise ValueError(f"Variable '{self.id}' bool initial_value must be boolean")
            return
        if self.type == "scalar" or self.type in _REFERENCE_TYPES:
            if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
                raise ValueError(f"Variable '{self.id}' initial_value must be a finite number")
            if self.type in _REFERENCE_TYPES and (int(value) != value or value < -1):
                raise ValueError(f"Variable '{self.id}' reference initial_value must be an integer >= -1 or null")
            return
        if self.type in _TENSOR_TYPES:
            assert self.shape is not None
            expected = self.shape
        else:
            if self.type in _FIXED_VECTOR_WIDTHS:
                vector_width: int | None = _FIXED_VECTOR_WIDTHS[self.type]
            else:
                vector_width = self.dims
            assert vector_width is not None
            expected = [vector_width]

        def check_shape(payload: Any, axes: list[int]) -> None:
            if not axes:
                if isinstance(payload, bool) or not isinstance(payload, int | float) or not math.isfinite(payload):
                    raise ValueError(f"Variable '{self.id}' initial_value contains a nonfinite or nonnumeric element")
                if self.type in {"vec2i", "vec3i", "vecNi"} and int(payload) != payload:
                    raise ValueError(f"Variable '{self.id}' integer vector initial_value contains a noninteger element")
                return
            if not isinstance(payload, list) or len(payload) != axes[0]:
                raise ValueError(f"Variable '{self.id}' initial_value must match its declared shape")
            for child in payload:
                check_shape(child, axes[1:])

        assert expected is not None
        check_shape(value, expected)


class VariablesConfig(BaseModel):
    """Canonical pack variable roster, evaluation settings and named item schemas."""

    model_config = ConfigDict(extra="forbid")
    version: Literal["1.0"]
    evaluation_mode: Literal["mark_and_sweep", "eager"]
    debug_logging: bool
    extents: VFSScopeExtents
    item_profiles: list[str]
    declarations: list[VariableDeclaration]

    @model_validator(mode="after")
    def validate_roster(self) -> VariablesConfig:
        if len(set(self.item_profiles)) != len(self.item_profiles):
            raise ValueError("Duplicate item profile identifiers")
        if any(not name or "." in name or "[" in name or "]" in name for name in self.item_profiles):
            raise ValueError("Item profile identifiers must be nonempty and contain no element separators")
        seen: set[tuple[str | None, str]] = set()
        extent_fields = {
            VariableScope.ZONE: "num_zones",
            VariableScope.GROUP: "num_groups",
            VariableScope.MESSAGE: "num_message_slots",
            VariableScope.AFFORDANCE: "num_affordances",
        }
        for variable in self.declarations:
            if self.evaluation_mode == "eager" and variable.scope in {VariableScope.GLOBAL, VariableScope.AGENT}:
                if variable.initial_value is None:
                    raise ValueError(
                        f"Variable '{variable.id}' eager evaluation requires a literal non-null initial value; "
                        "null references and initializer modes are supported by mark_and_sweep storage only"
                    )
            identity = (variable.profile if variable.scope == VariableScope.ITEM else None, variable.id)
            if identity in seen:
                raise ValueError(f"Duplicate variable identifier {identity}")
            seen.add(identity)
            if variable.id == "tick" and variable.scope != VariableScope.ITEM:
                raise ValueError("Variable id 'tick' is reserved for the engine-written step counter")
            if variable.scope == VariableScope.ITEM and variable.profile not in self.item_profiles:
                raise ValueError(f"Variable '{variable.id}' uses unknown item profile '{variable.profile}'")
            field = extent_fields.get(variable.scope)
            if field is not None and getattr(self.extents, field) is None:
                raise ValueError(f"Variable '{variable.id}' scope requires explicit '{field}' extent")
        return self

    def for_scope(self, scope: VariableScope) -> tuple[VariableDeclaration, ...]:
        return tuple(variable for variable in self.declarations if variable.scope == scope)

    def for_item_profile(self, profile: str) -> tuple[VariableDeclaration, ...]:
        return tuple(variable for variable in self.declarations if variable.scope == VariableScope.ITEM and variable.profile == profile)
