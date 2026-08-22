"""hamlet-bc0a5deeff: item-profile expressions have no evaluator — refuse at compile."""

from __future__ import annotations

import pytest

from townlet.config.vfs_profiles_config import ItemVFSProfileConfig
from townlet.vfs.profiles import VFSProfileCompiler


def test_item_profile_expression_refuses_at_compile():
    profile = ItemVFSProfileConfig(
        profile_name="p",
        variables=[{"name": "rot", "type": "float", "expression": "1.0"}],
    )
    with pytest.raises(ValueError, match="hamlet-bc0a5deeff"):
        VFSProfileCompiler().compile_item_profile(profile, bar_schema={})
