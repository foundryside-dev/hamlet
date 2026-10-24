"""The closed vocabulary of variable semantic types.

Every variable declares one. Two readers consume it:

- the token spec (`universe/dto/token_spec.py`): an exposed variable's descriptor block
  carries a one-hot over this vocabulary, so the one-hot width — and with it
  `token_type_schema_hash` — is `len(get_args(SemanticType))`;
- the clock detector (`universe/declarations.py`): a global `temporal` variable whose
  expression is `tick` with a cyclical normalization is the pack's clock.

Members:

- `temporal` — clock and time-derived state.
- `custom`   — every other authored variable. Never a default: an author writes it.

The vocabulary used to carry `bars`, `spatial`, `affordance` and `effects`, the group names of
the deleted grouped observation vector. No pack declared them and nothing assigned them;
they were deleted (VFS WP6). A declaration that still names one fails validation.
"""

from __future__ import annotations

from typing import Literal

SemanticType = Literal["temporal", "custom"]

__all__ = ["SemanticType"]
