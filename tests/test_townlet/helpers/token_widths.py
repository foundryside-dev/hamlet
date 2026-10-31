"""Derived token-width expectations shared by the width-pinning tests.

The fixed (full-context) width of a universe is its census applied to the engine's per-type
payload schemas: every type's rows are ``presence + payload``, and the payload width is the
length of ``PAYLOAD_SCHEMAS[type]``, itself composed from the declaration vocabularies. Tests
pin the census literally (what a pack declares) and derive the width from it here, so a
vocabulary change moves every pin at once instead of leaving stale literals behind. One
literal pin of the shipped ``default_curriculum`` width remains, in
``unit/universe/test_token_emission.py``, so vocabulary drift is loud exactly once.
"""

from __future__ import annotations

from collections.abc import Mapping

from townlet.universe.dto.token_spec import PAYLOAD_SCHEMAS


def fixed_width_for(census: Mapping[str, int]) -> int:
    """``fixed_total_dims`` implied by a census: Σ capacity × (1 presence + payload width)."""
    return sum(capacity * (1 + len(PAYLOAD_SCHEMAS[type_name])) for type_name, capacity in census.items())
