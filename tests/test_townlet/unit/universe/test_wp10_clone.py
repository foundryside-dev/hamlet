"""`CompiledUniverse.clone()` works on a freshly compiled universe (WP10 follow-up).

Before this, `clone()` raised `TypeError: cannot pickle 'mappingproxy' object` on any universe
that had not first been round-tripped through `to_dict`/`from_dict`: `UniverseMetadata` and
the action products install read-only `MappingProxyType` views that `copy.deepcopy` cannot
reconstruct. The existing clone test worked around it by cloning a deserialized artifact.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from townlet.universe.compiler import UniverseCompiler


def test_clone_of_a_freshly_compiled_universe_is_a_deep_equal_copy() -> None:
    universe = UniverseCompiler().compile(Path("configs/static_epistemic_access"), primary_level="L0_simple", use_cache=False)
    cloned = universe.clone()

    assert cloned is not universe
    assert cloned.metadata == universe.metadata and cloned.metadata is not universe.metadata
    assert dict(cloned.metadata.meter_name_to_index) == dict(universe.metadata.meter_name_to_index)
    assert cloned.variables_hash == universe.variables_hash
    level, original = cloned.get_level("L0_simple"), universe.get_level("L0_simple")
    assert level is not original
    assert level.vfs_hash == original.vfs_hash
    assert level.runtime_action_space == original.runtime_action_space
    assert level.action_metadata == original.action_metadata
    assert level.token_spec == original.token_spec
    # The round trip is byte-identical, so the clone is the same artifact.
    assert cloned.to_dict() == universe.to_dict()


def test_universe_metadata_deepcopies_with_its_read_only_views() -> None:
    universe = UniverseCompiler().compile(Path("configs/static_epistemic_access"), primary_level="L0_simple", use_cache=False)
    copied = deepcopy(universe.metadata)
    assert copied == universe.metadata
    assert type(copied.meter_name_to_index).__name__ == "mappingproxy"
