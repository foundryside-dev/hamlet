"""Test VFS VariableRegistry (Cycle 2 - TDD RED phase).

This module tests the Variable Registry which manages runtime storage of VFS variables
with access control and scope semantics.

Scope patterns:
- global: Single value (shape [] or [dims])
- agent: Per-agent values (shape [num_agents] or [num_agents, dims])
- agent_private: Per-agent private values (shape [num_agents] or [num_agents, dims])
"""

import pytest
import torch


class TestRegistryInitialization:
    """Test VariableRegistry initialization with different scopes."""

    def test_registry_creation_empty(self):
        """Create empty registry with no variables."""
        from townlet.vfs.registry import VariableRegistry

        registry = VariableRegistry(
            variables=[],
            num_agents=4,
            device=torch.device("cpu"),
        )

        assert registry.num_agents == 4
        assert registry.device == torch.device("cpu")

    def test_registry_implements_observation_protocol(self):
        """Both registry implementations must satisfy the observation builder contract."""
        from townlet.vfs.registry import ScopedVariableRegistry, VariableRegistry, VFSRegistryProtocol

        registry = VariableRegistry(
            variables=[],
            num_agents=4,
            device=torch.device("cpu"),
        )
        scoped_registry = ScopedVariableRegistry(device=torch.device("cpu"))

        assert isinstance(registry, VFSRegistryProtocol)
        assert isinstance(scoped_registry, VFSRegistryProtocol)

    def test_engine_write_path_enforces_declared_shape_and_permissions(self):
        """Engine writeback has a public registry method; it enforces the declared element
        shape (hamlet-d970ef83f0 — a global scalar can no longer legally hold a per-agent
        batch) and still enforces writable_by."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        writable = VariableDef(
            id="low_energy_flag",
            scope="global",
            type="bool",
            lifetime="tick",
            readable_by=["engine"],
            writable_by=["engine"],
            default=False,
        )
        protected = VariableDef(
            id="action_owned",
            scope="global",
            type="scalar",
            lifetime="tick",
            readable_by=["engine"],
            writable_by=["actions"],
            default=0.0,
        )
        registry = VariableRegistry(
            variables=[writable, protected],
            num_agents=4,
            device=torch.device("cpu"),
        )

        # A batched write to a declared-global scalar now raises instead of silently
        # corrupting storage shape.
        with pytest.raises(ValueError, match="shape"):
            registry.set_engine_value("low_energy_flag", torch.tensor([True, False, True, False]))

        # A correctly (declared-)shaped write still succeeds.
        registry.set_engine_value("low_energy_flag", torch.tensor(True))
        value = registry.get_global("low_energy_flag")
        assert value.shape == ()
        assert value.dtype == torch.bool
        assert bool(value.item()) is True

        with pytest.raises(PermissionError, match="engine"):
            registry.set_engine_value("action_owned", torch.tensor([1.0, 2.0]))

    def test_lifetime_reset_methods_restore_tick_and_episode_defaults(self):
        """Variable lifetime declarations must have runtime reset semantics."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="tick_flag",
                scope="global",
                type="bool",
                lifetime="tick",
                readable_by=["engine"],
                writable_by=["engine"],
                default=False,
            ),
            VariableDef(
                id="episode_score",
                scope="agent",
                type="scalar",
                lifetime="episode",
                readable_by=["engine"],
                writable_by=["engine"],
                default=1.0,
            ),
            VariableDef(
                id="persistent_counter",
                scope="global",
                type="scalar",
                lifetime="persistent",
                readable_by=["engine"],
                writable_by=["engine"],
                default=5.0,
            ),
        ]
        registry = VariableRegistry(variables=variables, num_agents=2, device=torch.device("cpu"))
        # tick_flag is global-scoped: a scalar write, not a per-agent batch
        # (hamlet-d970ef83f0 — set_engine_value enforces the declared shape).
        registry.set_engine_value("tick_flag", torch.tensor(True))
        registry.set("episode_score", torch.tensor([7.0, 8.0]), writer="engine")
        registry.set("persistent_counter", torch.tensor(9.0), writer="engine")

        registry.reset_tick_scoped()

        assert registry.get_global("tick_flag").item() is False
        assert torch.equal(registry.get_agent("episode_score"), torch.tensor([7.0, 8.0]))
        assert registry.get_global("persistent_counter").item() == 9.0

        registry.reset_episode_scoped()

        assert registry.get_global("tick_flag").item() is False
        assert torch.equal(registry.get_agent("episode_score"), torch.tensor([1.0, 1.0]))
        assert registry.get_global("persistent_counter").item() == 9.0

    def test_generic_read_write_api_removed_from_variable_registry(self):
        """Item VFS callers should use read_item/write_item instead of partial wrappers."""
        from townlet.vfs.registry import VariableRegistry

        assert not hasattr(VariableRegistry, "read")
        assert not hasattr(VariableRegistry, "write")

    def test_registry_with_global_scalar(self):
        """Initialize registry with global scalar variable."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="time_sin",
                scope="global",
                type="scalar",
                lifetime="tick",
                readable_by=["agent", "engine"],
                writable_by=["engine"],
                default=0.0,
            )
        ]

        registry = VariableRegistry(
            variables=variables,
            num_agents=4,
            device=torch.device("cpu"),
        )

        # Global scalar: shape []
        value = registry.get("time_sin", reader="engine")
        assert value.shape == torch.Size([])
        assert value.item() == 0.0

    def test_registry_with_agent_scalar(self):
        """Initialize registry with agent-scoped scalar variable."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="energy",
                scope="agent",
                type="scalar",
                lifetime="episode",
                readable_by=["agent", "engine"],
                writable_by=["engine"],
                default=1.0,
            )
        ]

        registry = VariableRegistry(
            variables=variables,
            num_agents=4,
            device=torch.device("cpu"),
        )

        # Agent scalar: shape [num_agents]
        value = registry.get("energy", reader="engine")
        assert value.shape == torch.Size([4])
        assert torch.all(value == 1.0)

    def test_registry_with_agent_vector(self):
        """Initialize registry with agent-scoped vector variable."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="position",
                scope="agent",
                type="vecNf",
                dims=2,
                lifetime="episode",
                readable_by=["agent"],
                writable_by=["engine"],
                default=[0.0, 0.0],
            )
        ]

        registry = VariableRegistry(
            variables=variables,
            num_agents=4,
            device=torch.device("cpu"),
        )

        # Agent vector: shape [num_agents, dims]
        value = registry.get("position", reader="agent")
        assert value.shape == torch.Size([4, 2])
        assert torch.all(value == 0.0)

    def test_registry_with_agent_private_vector(self):
        """Initialize registry with agent_private scoped vector variable."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="home_position",
                scope="agent_private",
                type="vecNf",
                dims=2,
                lifetime="episode",
                readable_by=["agent", "engine"],
                writable_by=["engine"],
                default=[5.0, 5.0],
            )
        ]

        registry = VariableRegistry(
            variables=variables,
            num_agents=4,
            device=torch.device("cpu"),
        )

        # Agent_private vector: shape [num_agents, dims]
        value = registry.get("home_position", reader="engine")
        assert value.shape == torch.Size([4, 2])
        assert torch.all(value == 5.0)

    def test_registry_with_mixed_scopes(self):
        """Initialize registry with multiple variables of different scopes."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="time_sin",
                scope="global",
                type="scalar",
                lifetime="tick",
                readable_by=["agent", "engine"],
                writable_by=["engine"],
                default=0.0,
            ),
            VariableDef(
                id="energy",
                scope="agent",
                type="scalar",
                lifetime="episode",
                readable_by=["agent", "engine"],
                writable_by=["engine"],
                default=1.0,
            ),
            VariableDef(
                id="home_pos",
                scope="agent_private",
                type="vecNf",
                dims=2,
                lifetime="episode",
                readable_by=["agent", "engine"],
                writable_by=["engine"],
                default=[0.0, 0.0],
            ),
        ]

        registry = VariableRegistry(
            variables=variables,
            num_agents=4,
            device=torch.device("cpu"),
        )

        # Verify all three scopes initialized correctly
        time_sin = registry.get("time_sin", reader="engine")
        assert time_sin.shape == torch.Size([])

        energy = registry.get("energy", reader="engine")
        assert energy.shape == torch.Size([4])

        home_pos = registry.get("home_pos", reader="engine")
        assert home_pos.shape == torch.Size([4, 2])

    def test_duplicate_variable_ids_raise_error(self):
        """Duplicate variable identifiers are rejected at construction time."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="energy",
                scope="agent",
                type="scalar",
                lifetime="episode",
                readable_by=["agent"],
                writable_by=["engine"],
                default=1.0,
            ),
            VariableDef(
                id="energy",  # Duplicate on purpose
                scope="agent",
                type="scalar",
                lifetime="episode",
                readable_by=["agent"],
                writable_by=["engine"],
                default=0.5,
            ),
        ]

        with pytest.raises(ValueError, match="Duplicate variable id 'energy'"):
            VariableRegistry(variables=variables, num_agents=2, device=torch.device("cpu"))

    def test_global_scalar_dtype_is_float32(self):
        """Global scalar tensors are initialized with float32 dtype for consistency."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="time_sin",
                scope="global",
                type="scalar",
                lifetime="tick",
                readable_by=["engine"],
                writable_by=["engine"],
                default=0,  # Int default should still yield float tensor
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=1, device=torch.device("cpu"))
        value = registry.get("time_sin", reader="engine")

        assert value.dtype == torch.float32
        assert value.shape == torch.Size([])

    def test_missing_dims_for_vec_variables_raise_value_error(self):
        """vecNi/vecNf variables without dims raise a descriptive error."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        bad_variable = VariableDef.model_construct(
            id="grid",
            scope="agent",
            type="vecNf",
            dims=None,
            lifetime="episode",
            readable_by=["agent"],
            writable_by=["engine"],
            default=[0.0, 0.0],
        )

        with pytest.raises(ValueError, match="must have dims field defined"):
            VariableRegistry(variables=[bad_variable], num_agents=2, device=torch.device("cpu"))


class TestRegistryAccessControl:
    """Test access control enforcement (readable_by/writable_by)."""

    def test_read_allowed(self):
        """Read variable when reader is in readable_by list."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="energy",
                scope="agent",
                type="scalar",
                lifetime="episode",
                readable_by=["agent", "engine"],
                writable_by=["engine"],
                default=1.0,
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=4, device=torch.device("cpu"))

        # Both agent and engine can read
        value = registry.get("energy", reader="agent")
        assert value is not None

        value = registry.get("energy", reader="engine")
        assert value is not None

    def test_read_denied(self):
        """Read variable when reader is NOT in readable_by list."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="energy",
                scope="agent",
                type="scalar",
                lifetime="episode",
                readable_by=["agent"],  # Only agent can read
                writable_by=["engine"],
                default=1.0,
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=4, device=torch.device("cpu"))

        # acs cannot read (not in readable_by)
        with pytest.raises(PermissionError, match="acs.*not allowed to read.*energy"):
            registry.get("energy", reader="acs")

    def test_agent_cannot_read_agent_private(self):
        """Agents should not directly read agent_private variables."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="secret",
                scope="agent_private",
                type="scalar",
                lifetime="episode",
                readable_by=["agent", "engine"],
                writable_by=["engine"],
                default=0.5,
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=3, device=torch.device("cpu"))

        with pytest.raises(PermissionError, match="agent_private"):
            registry.get("secret", reader="agent")

    def test_engine_can_read_agent_private(self):
        """Privileged readers (engine) can access full agent_private tensors."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="secret",
                scope="agent_private",
                type="scalar",
                lifetime="episode",
                readable_by=["agent", "engine"],
                writable_by=["engine"],
                default=0.5,
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=3, device=torch.device("cpu"))

        value = registry.get("secret", reader="engine")
        assert torch.all(value == 0.5)

    def test_write_allowed(self):
        """Write variable when writer is in writable_by list."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="energy",
                scope="agent",
                type="scalar",
                lifetime="episode",
                readable_by=["agent"],
                writable_by=["engine"],
                default=1.0,
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=4, device=torch.device("cpu"))

        # Engine can write
        new_value = torch.full((4,), 0.5, device=torch.device("cpu"))
        registry.set("energy", new_value, writer="engine")

        # Verify written
        value = registry.get("energy", reader="agent")
        assert torch.all(value == 0.5)

    def test_write_denied(self):
        """Write variable when writer is NOT in writable_by list."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="energy",
                scope="agent",
                type="scalar",
                lifetime="episode",
                readable_by=["agent"],
                writable_by=["engine"],  # Only engine can write
                default=1.0,
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=4, device=torch.device("cpu"))

        # agent cannot write (not in writable_by)
        new_value = torch.full((4,), 0.5, device=torch.device("cpu"))
        with pytest.raises(PermissionError, match="agent.*not allowed to write.*energy"):
            registry.set("energy", new_value, writer="agent")


class TestRegistryGetSet:
    """Test get/set operations."""

    def test_get_nonexistent_variable(self):
        """Get non-existent variable should raise KeyError."""
        from townlet.vfs.registry import VariableRegistry

        registry = VariableRegistry(variables=[], num_agents=4, device=torch.device("cpu"))

        with pytest.raises(KeyError, match="nonexistent"):
            registry.get("nonexistent", reader="engine")

    def test_set_nonexistent_variable(self):
        """Set non-existent variable should raise KeyError."""
        from townlet.vfs.registry import VariableRegistry

        registry = VariableRegistry(variables=[], num_agents=4, device=torch.device("cpu"))

        with pytest.raises(KeyError, match="nonexistent"):
            registry.set("nonexistent", torch.tensor([1.0]), writer="engine")

    def test_set_scalar_updates_value(self):
        """Set scalar variable updates its value."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="energy",
                scope="agent",
                type="scalar",
                lifetime="episode",
                readable_by=["agent"],
                writable_by=["engine"],
                default=1.0,
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=4, device=torch.device("cpu"))

        # Initial value
        value = registry.get("energy", reader="agent")
        assert torch.all(value == 1.0)

        # Update
        new_value = torch.tensor([0.9, 0.8, 0.7, 0.6], device=torch.device("cpu"))
        registry.set("energy", new_value, writer="engine")

        # Verify update
        value = registry.get("energy", reader="agent")
        assert torch.allclose(value, new_value)

    def test_set_vector_updates_value(self):
        """Set vector variable updates its value."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="position",
                scope="agent",
                type="vecNf",
                dims=2,
                lifetime="episode",
                readable_by=["agent"],
                writable_by=["engine"],
                default=[0.0, 0.0],
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=4, device=torch.device("cpu"))

        # Update positions
        new_positions = torch.tensor(
            [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]],
            device=torch.device("cpu"),
        )
        registry.set("position", new_positions, writer="engine")

        # Verify update
        value = registry.get("position", reader="agent")
        assert torch.allclose(value, new_positions)

    def test_get_returns_clone_for_readers(self):
        """Readers should receive a clone they cannot mutate in-place."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="energy",
                scope="agent",
                type="scalar",
                lifetime="episode",
                readable_by=["agent", "engine"],
                writable_by=["engine"],
                default=1.0,
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=2, device=torch.device("cpu"))

        view = registry.get("energy", reader="agent")
        view.fill_(0.0)

        fresh = registry.get("energy", reader="agent")
        assert torch.all(fresh == 1.0)

    def test_set_validates_shape(self):
        """Setting wrong-shaped tensors should raise ValueError."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="position",
                scope="agent",
                type="vecNf",
                dims=2,
                lifetime="episode",
                readable_by=["agent"],
                writable_by=["engine"],
                default=[0.0, 0.0],
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=2, device=torch.device("cpu"))

        wrong_shape = torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        with pytest.raises(ValueError, match="shape"):
            registry.set("position", wrong_shape, writer="engine")

    def test_set_validates_dtype(self):
        """Setting tensors with wrong dtype should raise ValueError."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="energy",
                scope="agent",
                type="scalar",
                lifetime="episode",
                readable_by=["agent"],
                writable_by=["engine"],
                default=1.0,
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=2, device=torch.device("cpu"))

        wrong_dtype = torch.ones(2, dtype=torch.int64)
        with pytest.raises(ValueError, match="dtype"):
            registry.set("energy", wrong_dtype, writer="engine")

    def test_set_global_scalar_updates_single_value(self):
        """Set global scalar variable (single value)."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="time_sin",
                scope="global",
                type="scalar",
                lifetime="tick",
                readable_by=["agent"],
                writable_by=["engine"],
                default=0.0,
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=4, device=torch.device("cpu"))

        # Update global scalar
        new_value = torch.tensor(0.707, device=torch.device("cpu"))
        registry.set("time_sin", new_value, writer="engine")

        # Verify update
        value = registry.get("time_sin", reader="agent")
        assert value.item() == pytest.approx(0.707)


class TestRegistryScopeSemantics:
    """Test scope-specific tensor shape semantics."""

    def test_global_scalar_shape(self):
        """Global scalar has shape []."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="global_var",
                scope="global",
                type="scalar",
                lifetime="tick",
                readable_by=["agent"],
                writable_by=["engine"],
                default=1.0,
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=10, device=torch.device("cpu"))

        value = registry.get("global_var", reader="agent")
        assert value.shape == torch.Size([])  # Single value, no agent dimension

    def test_global_vector_shape(self):
        """Global vector has shape [dims]."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="global_vec",
                scope="global",
                type="vecNf",
                dims=3,
                lifetime="tick",
                readable_by=["agent"],
                writable_by=["engine"],
                default=[1.0, 2.0, 3.0],
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=10, device=torch.device("cpu"))

        value = registry.get("global_vec", reader="agent")
        assert value.shape == torch.Size([3])  # [dims], no agent dimension

    def test_agent_scalar_shape(self):
        """Agent scalar has shape [num_agents]."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="agent_var",
                scope="agent",
                type="scalar",
                lifetime="episode",
                readable_by=["agent"],
                writable_by=["engine"],
                default=1.0,
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=10, device=torch.device("cpu"))

        value = registry.get("agent_var", reader="agent")
        assert value.shape == torch.Size([10])  # [num_agents]

    def test_agent_vector_shape(self):
        """Agent vector has shape [num_agents, dims]."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="agent_vec",
                scope="agent",
                type="vecNf",
                dims=2,
                lifetime="episode",
                readable_by=["agent"],
                writable_by=["engine"],
                default=[0.0, 0.0],
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=10, device=torch.device("cpu"))

        value = registry.get("agent_vec", reader="agent")
        assert value.shape == torch.Size([10, 2])  # [num_agents, dims]

    def test_agent_private_scalar_shape(self):
        """Agent_private scalar has shape [num_agents]."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="private_var",
                scope="agent_private",
                type="scalar",
                lifetime="episode",
                readable_by=["agent", "engine"],
                writable_by=["engine"],
                default=1.0,
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=10, device=torch.device("cpu"))

        value = registry.get("private_var", reader="engine")
        assert value.shape == torch.Size([10])  # [num_agents]

    def test_agent_private_vector_shape(self):
        """Agent_private vector has shape [num_agents, dims]."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="private_vec",
                scope="agent_private",
                type="vecNf",
                dims=2,
                lifetime="episode",
                readable_by=["agent", "engine"],
                writable_by=["engine"],
                default=[0.0, 0.0],
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=10, device=torch.device("cpu"))

        value = registry.get("private_vec", reader="engine")
        assert value.shape == torch.Size([10, 2])  # [num_agents, dims]


class TestRegistryRelationalScopes:
    """Test L5 relational and world-structure scope storage."""

    def test_variable_scope_enum_includes_l5_storage_scopes(self):
        """The schema should accept the L5 storage scopes as first-class enum values."""
        from townlet.vfs.schema import VariableScope

        assert VariableScope.PAIR == "pair"
        assert VariableScope.GROUP == "group"
        assert VariableScope.AFFORDANCE == "affordance"
        assert VariableScope.ZONE == "zone"

    def test_registry_initializes_pair_group_affordance_and_zone_scalars(self):
        """Dense scope prefixes should match the declared world extents."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="trust",
                scope="pair",
                type="scalar",
                lifetime="episode",
                readable_by=["engine"],
                writable_by=["engine"],
                default=0.25,
            ),
            VariableDef(
                id="group_norm_strength",
                scope="group",
                type="scalar",
                lifetime="episode",
                readable_by=["engine"],
                writable_by=["engine"],
                default=0.5,
            ),
            VariableDef(
                id="occupied_by",
                scope="affordance",
                type="agent_ref",
                lifetime="episode",
                readable_by=["engine"],
                writable_by=["engine"],
                default=None,
            ),
            VariableDef(
                id="zone_danger",
                scope="zone",
                type="scalar",
                lifetime="episode",
                readable_by=["engine"],
                writable_by=["engine"],
                default=0.0,
            ),
        ]

        registry = VariableRegistry(
            variables=variables,
            num_agents=3,
            num_groups=2,
            num_affordances=4,
            num_zones=5,
            device=torch.device("cpu"),
        )

        assert registry.get("trust", reader="engine").shape == torch.Size([3, 3])
        assert torch.all(registry.get("trust", reader="engine") == 0.25)
        assert registry.get("group_norm_strength", reader="engine").shape == torch.Size([2])
        assert registry.get("occupied_by", reader="engine").shape == torch.Size([4])
        assert torch.all(registry.get("occupied_by", reader="engine") == -1)
        assert registry.get("zone_danger", reader="engine").shape == torch.Size([5])

    def test_registry_prefixes_vectors_and_tensors_with_relational_scopes(self):
        """Vector and tensor storage should add the scope dimensions before payload dimensions."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="relative_offset",
                scope="pair",
                type="vecNf",
                dims=2,
                lifetime="episode",
                readable_by=["engine"],
                writable_by=["engine"],
                default=[0.0, 1.0],
            ),
            VariableDef(
                id="affordance_slots",
                scope="affordance",
                type="tensor2d",
                shape=[2, 3],
                lifetime="episode",
                readable_by=["engine"],
                writable_by=["engine"],
                default=None,
            ),
        ]

        registry = VariableRegistry(
            variables=variables,
            num_agents=4,
            num_affordances=6,
            device=torch.device("cpu"),
        )

        assert registry.get("relative_offset", reader="engine").shape == torch.Size([4, 4, 2])
        assert registry.get("affordance_slots", reader="engine").shape == torch.Size([6, 2, 3])

    def test_registry_requires_explicit_extent_for_non_agent_relational_scope(self):
        """Missing world extents should fail loudly instead of allocating ambiguous storage."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variable = VariableDef(
            id="group_norm_strength",
            scope="group",
            type="scalar",
            lifetime="episode",
            readable_by=["engine"],
            writable_by=["engine"],
            default=0.5,
        )

        with pytest.raises(ValueError, match="num_groups.*positive"):
            VariableRegistry(variables=[variable], num_agents=3, device=torch.device("cpu"))


class TestRegistrySparsePairScopes:
    """Test sparse pair-scope storage for neighbourhood-limited relationships."""

    def _trust_variable(self):
        from townlet.vfs.schema import VariableDef

        return VariableDef(
            id="trust",
            scope="pair",
            type="scalar",
            lifetime="episode",
            readable_by=["engine"],
            writable_by=["engine"],
            default=0.0,
        )

    def test_sparse_pair_scope_allocates_edge_rows_not_dense_matrix(self):
        """Sparse pair variables should allocate active relationship rows instead of N x N storage."""
        from townlet.vfs.registry import VariableRegistry

        registry = VariableRegistry(
            variables=[self._trust_variable()],
            num_agents=1000,
            pair_storage_mode="sparse",
            pair_edges=[(0, 1), (1, 2)],
            device=torch.device("cpu"),
        )

        assert registry.get("trust", reader="engine").shape == torch.Size([2])
        assert torch.equal(registry.get_pair_edges(), torch.tensor([[0, 1], [1, 2]]))
        mask = registry.get_pair_mask()
        assert mask.shape == torch.Size([1000, 1000])
        assert mask[0, 1]
        assert mask[1, 2]
        assert mask.sum().item() == 2

    def test_sparse_pair_scope_requires_explicit_pair_edges(self):
        """Sparse mode should fail loudly instead of silently falling back to dense storage."""
        from townlet.vfs.registry import VariableRegistry

        with pytest.raises(ValueError, match="pair_edges"):
            VariableRegistry(
                variables=[self._trust_variable()],
                num_agents=3,
                pair_storage_mode="sparse",
                device=torch.device("cpu"),
            )

    def test_sparse_pair_scope_rejects_invalid_pair_edges(self):
        """Neighbourhood edges must be directed in-range agent index pairs."""
        from townlet.vfs.registry import VariableRegistry

        with pytest.raises(ValueError, match="out of range"):
            VariableRegistry(
                variables=[self._trust_variable()],
                num_agents=3,
                pair_storage_mode="sparse",
                pair_edges=[(0, 3)],
                device=torch.device("cpu"),
            )

        with pytest.raises(ValueError, match="duplicate"):
            VariableRegistry(
                variables=[self._trust_variable()],
                num_agents=3,
                pair_storage_mode="sparse",
                pair_edges=[(0, 1), (0, 1)],
                device=torch.device("cpu"),
            )

    def test_sparse_pair_scope_rejects_dense_pair_writes(self):
        """Sparse pair storage should only accept one row per active relationship."""
        from townlet.vfs.registry import VariableRegistry

        registry = VariableRegistry(
            variables=[self._trust_variable()],
            num_agents=3,
            pair_storage_mode="sparse",
            pair_edges=[(0, 1), (1, 2)],
            device=torch.device("cpu"),
        )

        with pytest.raises(ValueError, match=r"expected \(2,\)"):
            registry.set("trust", torch.zeros((3, 3)), writer="engine")

        with pytest.raises(ValueError, match=r"expected \(2,\)"):
            registry.set_engine_value("trust", torch.zeros((3, 3)))

    def test_sparse_pair_scope_can_materialize_dense_debug_view(self):
        """Sparse relationship values can be expanded into a dense read-only view for diagnostics."""
        from townlet.vfs.registry import VariableRegistry

        registry = VariableRegistry(
            variables=[self._trust_variable()],
            num_agents=3,
            pair_storage_mode="sparse",
            pair_edges=[(0, 1), (1, 2)],
            device=torch.device("cpu"),
        )
        registry.set("trust", torch.tensor([0.25, 0.75]), writer="engine")

        dense = registry.materialize_pair_dense("trust", reader="engine", fill_value=-1.0)

        assert torch.equal(
            dense,
            torch.tensor(
                [
                    [-1.0, 0.25, -1.0],
                    [-1.0, -1.0, 0.75],
                    [-1.0, -1.0, -1.0],
                ]
            ),
        )


class TestRegistryVariablesProperty:
    """Test the public variables property for introspection."""

    def test_variables_property_exposes_definitions(self):
        """Registry.variables property exposes variable definitions."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="energy",
                scope="agent",
                type="scalar",
                lifetime="episode",
                readable_by=["agent"],
                writable_by=["engine"],
                default=1.0,
            ),
            VariableDef(
                id="position",
                scope="agent",
                type="vecNf",
                dims=2,
                lifetime="episode",
                readable_by=["agent"],
                writable_by=["engine"],
                default=[0.0, 0.0],
            ),
        ]

        registry = VariableRegistry(variables=variables, num_agents=4, device=torch.device("cpu"))

        # Variables property should expose definitions dict
        assert "energy" in registry.variables
        assert "position" in registry.variables
        assert len(registry.variables) == 2

    def test_variables_property_returns_dict(self):
        """Registry.variables returns dictionary mapping IDs to definitions."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="energy",
                scope="agent",
                type="scalar",
                lifetime="episode",
                readable_by=["agent"],
                writable_by=["engine"],
                default=1.0,
            ),
        ]

        registry = VariableRegistry(variables=variables, num_agents=4, device=torch.device("cpu"))

        # Check type and structure
        assert isinstance(registry.variables, dict)
        assert registry.variables["energy"].id == "energy"
        assert registry.variables["energy"].scope == "agent"
        assert registry.variables["energy"].type == "scalar"

    def test_variables_property_empty_registry(self):
        """Registry.variables works with empty registry."""
        from townlet.vfs.registry import VariableRegistry

        registry = VariableRegistry(variables=[], num_agents=4, device=torch.device("cpu"))

        assert isinstance(registry.variables, dict)
        assert len(registry.variables) == 0
