"""Execution context for expression evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import torch

from townlet.world.expression.history import TemporalHistory
from townlet.world.expression.references import ReferenceKind, parse_reference

if TYPE_CHECKING:
    from townlet.vfs.random_draws import DrawStream


@dataclass
class ExecutionContext:
    """Runtime context for expression evaluation.

    A read resolves through the one reference grammar
    (``townlet.world.expression.references``), the same grammar the compiler's
    ``townlet.vfs.namespace.Namespace`` resolves spellings by, so the type checker can
    never admit a spelling this context does not serve:

    - a bare name reads ``vfs``: registry variables, engine names (``tick``,
      ``agent_id``) and pipeline-local names (``intensity``), as the consumer built it;
    - ``bar.<m>`` reads ``bars``;
    - ``item.<x>`` reads ``item_state``, the state of the item the context is bound to
      (None when it is bound to none).

    ``temporal`` is the engine's internal namespace for the programs it generates
    itself (operating-hour gates, meter depletion); no authored context admits it.
    """

    bars: dict[str, torch.Tensor]
    vfs: dict[str, torch.Tensor]
    temporal: dict[str, torch.Tensor]
    item_state: dict[str, torch.Tensor] | None = None
    affordance_positions: dict[str, torch.Tensor] | None = None
    agent_positions: torch.Tensor | None = None
    device: torch.device = torch.device("cpu")
    history: TemporalHistory | None = None
    # Where sampling functions draw from (S1: one world's draws never shift another's).
    # A VFS context (one profile variable, one action write, one transition-rule write)
    # carries ``draws``, the owner's counter-based draw sites (``townlet.vfs.random_draws``):
    # each value a pure function of seed, episode, tick, site, world and element. A command
    # pipeline is bound to one world and carries that world's generator as ``rng``. Neither
    # set means torch's global stream, which only direct engine or test callers build.
    rng: torch.Generator | None = None
    draws: DrawStream | None = None

    def get(self, path: str) -> torch.Tensor:
        """The value ``path`` names; KeyError when it is no spelling this context serves."""
        segments = path.split(".")
        if len(segments) == 2 and segments[0] == "temporal" and segments[1] in self.temporal:
            return self.temporal[segments[1]]
        reference = parse_reference(path)
        if reference is None:
            raise KeyError(f"'{path}' is not a reference spelling (a bare name, 'bar.<meter>' or 'item.<name>')")
        if reference.kind == ReferenceKind.METER:
            if reference.name in self.bars:
                return self.bars[reference.name]
        elif reference.kind == ReferenceKind.ITEM:
            if self.item_state is None:
                raise KeyError(f"'{path}' reads item state, but this context is bound to no item")
            if reference.name in self.item_state:
                return self.item_state[reference.name]
        elif reference.name in self.vfs:
            return self.vfs[reference.name]
        raise KeyError(f"Path '{path}' not found in execution context")
