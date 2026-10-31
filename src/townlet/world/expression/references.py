"""The one grammar of a state reference in an expression (VFS round-2 S5).

Every consumer of the expression language (a variable expression, an action write, a
transition rule, an effect or interaction pipeline, an item spawn predicate) spells a
reference to state one way:

- ``x``: a registry variable, read in this world by its declared scope (S1: a global is
  this world's value, an agent variable is this world's agent's row, an affordance
  variable is this world's per-affordance row). An engine-provided name (``tick``,
  ``agent_id``) or a pipeline-local name (``intensity``) is also bare.
- ``bar.m``: a meter of this world's agent.
- ``item.x``: the state of the item the context is bound to (an item interaction, an
  item-scoped effect, an inventory loop). It is the only qualifier, because an item is
  the only second entity a context can have: under S1 a world has one agent.

The grammar is shared by compile time (``townlet.vfs.namespace.Namespace``, which
resolves a spelling against the symbol table and refuses every other spelling with the
canonical one named) and run time (every ``ExecutionContext.get``), so a spelling the
type checker admits is a spelling the runtime serves.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

__all__ = [
    "EFFECT_LOCALS",
    "ENGINE_AGENT_ID",
    "ENGINE_TICK",
    "ENTITY_NAMES",
    "ENTITY_SELF",
    "ENTITY_TARGET",
    "ITEM_ROOT",
    "METER_ROOT",
    "RESERVED_NAMES",
    "Reference",
    "ReferenceKind",
    "parse_reference",
]

METER_ROOT = "bar"
ITEM_ROOT = "item"

ENGINE_TICK = "tick"
"""The engine step counter, readable by bare name in every context and written by the engine only."""

ENGINE_AGENT_ID = "agent_id"
"""The acting agent's row, served to transition writes and rules."""

EFFECT_LOCALS: dict[str, str] = {"intensity": "float", "elapsed_ticks": "float", "duration_remaining": "float"}
"""The names an active effect binds while its pipeline runs, with their expression types."""

ENTITY_SELF = "self"
ENTITY_TARGET = "target"
ENTITY_NAMES: frozenset[str] = frozenset({ENTITY_SELF, ENTITY_TARGET})
"""The two entities a pipeline context binds, named by a ``spawn_effect`` target, a ``spawn_item``
position and the item-state read qualifier (``self.<x>``, ``target.<x>``)."""

RESERVED_NAMES: frozenset[str] = frozenset({ENGINE_TICK, ENGINE_AGENT_ID, *EFFECT_LOCALS, *ENTITY_NAMES})
"""Every bare name the engine or a pipeline binds, and the two entity names. A registry variable may
not take one: its bare spelling would name two things (``VariableDeclaration`` refuses it at the
declaration line)."""


class ReferenceKind(StrEnum):
    """What a canonical spelling names, read off its shape."""

    NAME = "name"
    METER = "meter"
    ITEM = "item"


@dataclass(frozen=True)
class Reference:
    """One canonical reference: its kind and the bare name it qualifies."""

    kind: ReferenceKind
    name: str

    @property
    def spelling(self) -> str:
        if self.kind == ReferenceKind.METER:
            return f"{METER_ROOT}.{self.name}"
        if self.kind == ReferenceKind.ITEM:
            return f"{ITEM_ROOT}.{self.name}"
        return self.name


def parse_reference(path: str) -> Reference | None:
    """The reference ``path`` spells, or None when it is not a canonical spelling."""
    segments = path.split(".")
    if any(not segment for segment in segments):
        return None
    if len(segments) == 1:
        return Reference(ReferenceKind.NAME, segments[0])
    if len(segments) == 2 and segments[0] == METER_ROOT:
        return Reference(ReferenceKind.METER, segments[1])
    if len(segments) == 2 and segments[0] == ITEM_ROOT:
        return Reference(ReferenceKind.ITEM, segments[1])
    return None
