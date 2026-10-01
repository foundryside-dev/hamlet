"""Checked static policy access and immutable runtime policy snapshots."""

from __future__ import annotations

import pytest
import torch

from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef


def _variable(identifier: str, scope: str, readers: list[str], writers: list[str]) -> VariableDef:
    return VariableDef(
        id=identifier,
        scope=scope,
        type="scalar",
        lifetime="episode",
        default=2.0,
        readable_by=readers,
        writable_by=writers,
    )


@pytest.mark.parametrize("scope,accessor", [("global", "get_global"), ("agent", "get_agent")])
def test_convenience_accessors_enforce_actor_and_clone(scope: str, accessor: str) -> None:
    registry = VariableRegistry([_variable("hidden", scope, ["engine"], ["engine"])], 2, torch.device("cpu"))
    method = getattr(registry, accessor)
    with pytest.raises(PermissionError, match="agent.*hidden|hidden.*agent"):
        method("hidden", reader="agent")
    with pytest.raises(PermissionError, match="unknown|Unknown"):
        method("hidden", reader="bogus")
    with pytest.raises(TypeError):
        method("hidden")
    value = method("hidden", reader="engine")
    value.fill_(99.0)
    assert torch.all(registry.get("hidden", reader="engine") == 2.0)


def test_mutating_source_policy_cannot_change_runtime_authority() -> None:
    variable = _variable("public", "agent", ["engine", "agent"], ["engine"])
    registry = VariableRegistry([variable], 2, torch.device("cpu"))
    variable.readable_by.clear()
    variable.writable_by.clear()
    registry.variables["public"].readable_by.clear()
    registry.variables["public"].writable_by.clear()
    assert torch.all(registry.get("public", reader="agent") == 2.0)
    registry.set("public", torch.full((2,), 3.0), writer="engine")
    assert torch.all(registry.get_agent("public", reader="engine") == 3.0)


def test_mutated_unknown_policy_is_rejected_before_storage_allocation() -> None:
    variable = _variable("invalid", "global", ["engine"], ["engine"])
    variable.readable_by.append("acs")
    with pytest.raises(ValueError, match="read|role|actor"):
        VariableRegistry([variable], 2, torch.device("cpu"))


@pytest.mark.parametrize("method", ["set", "set_engine_value"])
def test_same_value_write_denies_without_mutation(method: str) -> None:
    registry = VariableRegistry([_variable("constant", "agent", ["engine"], [])], 2, torch.device("cpu"))
    before = registry.get("constant", reader="engine")
    kwargs = {"writer": "engine"} if method == "set" else {}
    with pytest.raises(PermissionError, match="constant"):
        getattr(registry, method)("constant", before.clone(), **kwargs)
    assert torch.equal(before, registry.get("constant", reader="engine"))
    registry.reset_tick_scoped()
    registry.reset_episode_scoped()
    assert torch.equal(before, registry.get("constant", reader="engine"))


def test_dynamic_add_snapshots_new_policy_and_cannot_replace_old_policy() -> None:
    variable = _variable("new", "agent", ["engine"], ["engine"])
    registry = VariableRegistry([], 2, torch.device("cpu"), dynamic_variable_mode=True)
    registry.add_variable(variable, network_shape_effect="shape_stable_internal")
    variable.readable_by.append("agent")
    with pytest.raises(PermissionError, match="agent"):
        registry.get("new", reader="agent")
    with pytest.raises(ValueError, match="already exists"):
        registry.add_variable(variable, network_shape_effect="shape_stable_internal")


def _items() -> VariableRegistry:
    from townlet.vfs.profiles import CompiledItemProfile, CompiledVariable

    profiles = {}
    for name, readers, writers in [("public", ("engine", "agent"), ("engine",)), ("hidden", ("engine",), ())]:
        variable = CompiledVariable(
            name="value", type="float", exposed_to=(), lifetime="episode", readable_by=readers, writable_by=writers, initial_value=2.0
        )
        profiles[name] = CompiledItemProfile(profile_name=name, variables=[variable])
    return VariableRegistry([], 2, torch.device("cpu"), max_items=2, item_profiles=profiles)


def test_item_policies_are_qualified_and_denials_preserve_storage() -> None:
    registry = _items()
    registry.register_item_instance(0, "public")
    registry.register_item_instance(1, "hidden")
    registry.write_item("public", "value", 4.0, 0, writer="engine")
    assert registry.read_item("public", "value", 0, reader="agent") == 4.0
    assert registry.item_vfs is not None
    before = registry.item_vfs.clone()
    with pytest.raises(PermissionError, match="hidden"):
        registry.read_item("hidden", "value", 1, reader="agent")
    with pytest.raises(PermissionError, match="hidden"):
        registry.write_item("hidden", "value", 0.0, 1, writer="engine")
    with pytest.raises(PermissionError, match="profile|hidden"):
        registry.read_item("public", "value", 1, reader="agent")
    assert torch.equal(before, registry.item_vfs)
    with pytest.raises(PermissionError, match="unknown|Unknown"):
        registry.read_item("public", "value", 0, reader="bogus")
    with pytest.raises(TypeError):
        registry.read_item("public", "value", 0)
    with pytest.raises(TypeError):
        registry.write_item("public", "value", 4.0, 0)


def test_item_policy_mutation_cannot_change_access_authority() -> None:
    registry = _items()
    registry.register_item_instance(0, "public")
    variable = registry.item_profiles["public"].variables[0]
    variable.readable_by = ("engine",)
    variable.writable_by = ()
    registry.write_item("public", "value", 3.0, 0, writer="engine")
    assert registry.read_item("public", "value", 0, reader="agent") == 3.0


def test_unregistered_item_row_cannot_borrow_public_profile() -> None:
    registry = _items()
    registry.register_item_instance(0, "hidden")
    assert registry.item_vfs is not None
    registry.item_vfs[0, 0] = 47.0
    registry.unregister_item_instance(0)
    before = registry.item_vfs.clone()
    with pytest.raises(PermissionError, match="profile"):
        registry.read_item("public", "value", 0, reader="agent")
    with pytest.raises(PermissionError, match="profile"):
        registry.write_item("public", "value", 1.0, 0, writer="engine")
    assert torch.equal(before, registry.item_vfs)
