"""Per-scope registry arenas (token-obs unit 3, Task 8 — the Global Constraints storage decision).

The registry gains item_vfs-style consolidated arenas for the `global` and `agent`
scopes: one `[rows, elements]` float32 tensor per scope with a compiled index map, where
`rows` is 1 (global) or num_agents (agent). Float32-typed variables of those scopes are
STORED as views into the arena, so every write (set / set_engine_value / lifetime reset)
lands in the arena without any sync step, and the token registry publisher reads one slab
per scope — this is what lets the publisher's fills be batched (never per-variable Python
loops) and what retires the clone-per-read at the Task-10 swap (hamlet-c7084169f7).

`agent_private` is excluded from the arenas BY CONSTRUCTION — the arenas exist to feed
observation, and the publisher (environment/token_publishers.py) is the enforcement
point for the hamlet-83a043a9b9 boundary.
"""

import pytest
import torch

from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef

DEVICE = torch.device("cpu")


def _var(
    name: str,
    *,
    scope: str = "global",
    type: str = "scalar",
    default=0.0,
    dims: int | None = None,
    shape: list[int] | None = None,
    lifetime: str = "persistent",
) -> VariableDef:
    return VariableDef(
        id=name,
        scope=scope,
        type=type,
        dims=dims,
        shape=shape,
        lifetime=lifetime,
        readable_by=["agent", "engine"],
        writable_by=["engine"],
        default=default,
        description=f"test {name}",
    )


@pytest.fixture
def registry() -> VariableRegistry:
    return VariableRegistry(
        variables=[
            _var("g_scalar", default=0.25),
            _var("g_vec", type="vecNf", dims=3, default=[1.0, 2.0, 3.0]),
            _var("a_scalar", scope="agent", default=0.5, lifetime="episode"),
            _var("a_vec", scope="agent", type="vecNf", dims=2, default=[0.1, 0.2]),
            _var("p_scalar", scope="agent_private", default=9.0),
            _var("g_ref", type="item_ref", default=None),
            _var("g_bool", type="bool", default=True),
            _var("t_scalar", default=0.0, lifetime="tick"),
        ],
        num_agents=3,
        device=DEVICE,
    )


class TestArenaLayout:
    def test_both_scopes_always_present(self, registry):
        assert set(registry.scope_arenas.keys()) == {"global", "agent"}

    def test_global_arena_shape_and_index(self, registry):
        arena = registry.scope_arenas["global"]
        # g_scalar (1) + g_vec (3) + t_scalar (1); ref and bool dtypes stay standalone.
        assert arena.tensor.shape == (1, 5)
        assert arena.tensor.dtype == torch.float32
        assert arena.index["g_scalar"] == (0, 1)
        assert arena.index["g_vec"] == (1, 3)
        assert arena.index["t_scalar"] == (4, 1)
        assert "g_ref" not in arena.index
        assert "g_bool" not in arena.index

    def test_agent_arena_shape_and_index(self, registry):
        arena = registry.scope_arenas["agent"]
        assert arena.tensor.shape == (3, 3)  # a_scalar (1) + a_vec (2), rows = num_agents
        assert arena.index["a_scalar"] == (0, 1)
        assert arena.index["a_vec"] == (1, 2)

    def test_agent_private_never_in_any_arena(self, registry):
        # The arenas feed observation; agent_private is excluded by construction
        # (hamlet-83a043a9b9 — the publisher is the enforcement point).
        for arena in registry.scope_arenas.values():
            assert "p_scalar" not in arena.index

    def test_initial_values_land_in_arena(self, registry):
        assert registry.scope_arenas["global"].tensor[0].tolist() == [0.25, 1.0, 2.0, 3.0, 0.0]
        for row in registry.scope_arenas["agent"].tensor.tolist():
            assert row == pytest.approx([0.5, 0.1, 0.2])


class TestWritesLandInArena:
    def test_set_writes_through_to_arena(self, registry):
        registry.set("g_scalar", torch.tensor(0.75), writer="engine")
        assert registry.scope_arenas["global"].tensor[0, 0].item() == 0.75

    def test_set_engine_value_writes_through(self, registry):
        registry.set_engine_value("a_vec", torch.tensor([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]))
        assert registry.scope_arenas["agent"].tensor[:, 1:3].tolist() == [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]

    def test_reads_are_unchanged_by_the_arena(self, registry):
        registry.set("a_scalar", torch.tensor([0.1, 0.2, 0.3]), writer="engine")
        assert registry.get("a_scalar", reader="engine").tolist() == pytest.approx([0.1, 0.2, 0.3])
        assert registry.get_agent("a_scalar").tolist() == pytest.approx([0.1, 0.2, 0.3])

    def test_get_still_returns_a_clone_not_an_arena_view(self, registry):
        value = registry.get_global("g_scalar")
        value.fill_(123.0)
        assert registry.scope_arenas["global"].tensor[0, 0].item() == 0.25

    def test_lifetime_reset_restores_arena_values(self, registry):
        registry.set("t_scalar", torch.tensor(7.0), writer="engine")
        registry.set("a_scalar", torch.tensor([9.0, 9.0, 9.0]), writer="engine")
        registry.reset_tick_scoped()
        assert registry.scope_arenas["global"].tensor[0, 4].item() == 0.0  # tick lifetime restored
        assert registry.scope_arenas["agent"].tensor[:, 0].tolist() == [9.0, 9.0, 9.0]  # episode untouched
        registry.reset_episode_scoped()
        assert registry.scope_arenas["agent"].tensor[:, 0].tolist() == [0.5, 0.5, 0.5]

    def test_shape_and_dtype_refusals_unchanged(self, registry):
        with pytest.raises(ValueError, match="shape"):
            registry.set("g_scalar", torch.tensor([1.0, 2.0]), writer="engine")
        with pytest.raises(PermissionError):
            registry.set("g_scalar", torch.tensor(1.0), writer="agent")


class TestNonArenaVariablesUnchanged:
    def test_ref_and_bool_storage_dtypes(self, registry):
        assert registry.get("g_ref", reader="engine").dtype == torch.long
        assert registry.get("g_bool", reader="engine").dtype == torch.bool

    def test_agent_private_reads_still_work_for_privileged_readers(self, registry):
        assert registry.get("p_scalar", reader="engine").tolist() == [9.0, 9.0, 9.0]


class TestDynamicVariableMode:
    def test_dynamic_added_variables_stay_out_of_the_arena(self):
        registry = VariableRegistry(
            variables=[_var("g_scalar", default=0.0)],
            num_agents=2,
            device=DEVICE,
            dynamic_variable_mode=True,
        )
        registry.add_variable(_var("late", default=1.0), network_shape_effect="shape_stable_internal")
        assert "late" not in registry.scope_arenas["global"].index
        assert registry.get("late", reader="engine").item() == 1.0

    def test_removing_an_arena_backed_variable_drops_its_index_entry(self):
        registry = VariableRegistry(
            variables=[_var("g_scalar", default=0.0)],
            num_agents=2,
            device=DEVICE,
            dynamic_variable_mode=True,
        )
        registry.remove_variable("g_scalar", network_shape_effect="shape_stable_internal")
        assert "g_scalar" not in registry.scope_arenas["global"].index
