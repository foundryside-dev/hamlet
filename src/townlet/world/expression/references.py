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

__all__ = ["ITEM_ROOT", "METER_ROOT", "Reference", "ReferenceKind", "parse_reference"]

METER_ROOT = "bar"
ITEM_ROOT = "item"


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
