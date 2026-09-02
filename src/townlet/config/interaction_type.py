"""The ONE closed vocabulary of affordance interaction types (PDR-0047, hamlet-45b35cfee5).

An affordance's `interaction_type` is a behavioural parameter: it selects whether an INTERACT
completes in one tick or accumulates progress over `duration_ticks`. It is
REQUIRED in `affordances.yaml` — there is no runtime coalesce to `instant` any more (that
was a hidden default on a behavioural parameter, and its description said so out loud).

Before this module the field had TWO vocabularies: the authoring DTO permitted
`instant | multi_tick | dual` and a dead runtime module also admitted `continuous`, which
the VTC rejects and nothing else implements. `continuous` was never real; the module that
named it had zero importers and is deleted.

Every place that declares, checks, or stores an interaction type references this module.
"""

from __future__ import annotations

from typing import Final, Literal, get_args

InteractionType = Literal["instant", "multi_tick"]

INTERACTION_TYPES: Final[frozenset[str]] = frozenset(get_args(InteractionType))

# The members that accumulate progress and therefore REQUIRE `duration_ticks`.
PROGRESS_INTERACTION_TYPES: Final[frozenset[str]] = frozenset({"multi_tick"})

__all__ = ["INTERACTION_TYPES", "PROGRESS_INTERACTION_TYPES", "InteractionType"]
