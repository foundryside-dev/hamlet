"""Test VFS VariableRegistry (Cycle 2 - TDD RED phase).

This module tests the Variable Registry which manages runtime storage of VFS variables
with access control and scope semantics.

Scope patterns:
- global: One value per world (shape [num_worlds] or [num_worlds, dims]; S1: num_worlds == num_agents)
- agent: Per-agent values (shape [num_agents] or [num_agents, dims])
- affordance: Per-affordance values in each world (shape [num_worlds, num_affordances, ...])
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

    def test_engine_write_path_enforces_declared_shape_and_permissions(self):
        """Engine writeback has a public registry method; it enforces the declared element
        shape (a global scalar holds exactly one value per world) and still enforces
        writable_by."""
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
            writable_by=[],
            default=0.0,
        )
        registry = VariableRegistry(
            variables=[writable, protected],
            num_agents=4,
            device=torch.device("cpu"),
        )

        # A world-invariant 0-d write to a per-world global raises instead of broadcasting.
        with pytest.raises(ValueError, match="shape"):
            registry.set_engine_value("low_energy_flag", torch.tensor(True))

        # One value per world succeeds.
        registry.set_engine_value("low_energy_flag", torch.tensor([True, False, True, False]))
        value = registry.get("low_energy_flag", reader="engine")
        assert value.shape == (4,)
        assert value.dtype == torch.bool
        assert value.tolist() == [True, False, True, False]

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
        # Globals are per world: one value per world (S1).
        registry.set_engine_value("tick_flag", torch.tensor([True, True]))
        registry.set("episode_score", torch.tensor([7.0, 8.0]), writer="engine")
        registry.set("persistent_counter", torch.tensor([9.0, 4.0]), writer="engine")

        registry.reset_tick_scoped()

        assert registry.get("tick_flag", reader="engine").tolist() == [False, False]
        assert torch.equal(registry.get("episode_score", reader="engine"), torch.tensor([7.0, 8.0]))
        assert registry.get("persistent_counter", reader="engine").tolist() == [9.0, 4.0]

        registry.reset_episode_scoped()

        assert registry.get("tick_flag", reader="engine").tolist() == [False, False]
        assert torch.equal(registry.get("episode_score", reader="engine"), torch.tensor([1.0, 1.0]))
        assert registry.get("persistent_counter", reader="engine").tolist() == [9.0, 4.0]

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

        # Global scalar: one value per world, shape [num_worlds]
        value = registry.get("time_sin", reader="engine")
        assert value.shape == torch.Size([4])
        assert torch.all(value == 0.0)

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
                readable_by=["agent", "engine"],
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
                scope="agent",
                type="vecNf",
                dims=2,
                lifetime="episode",
                readable_by=["engine"],
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
        assert time_sin.shape == torch.Size([4])

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
                readable_by=["agent", "engine"],
                writable_by=["engine"],
                default=1.0,
            ),
            VariableDef(
                id="energy",  # Duplicate on purpose
                scope="agent",
                type="scalar",
                lifetime="episode",
                readable_by=["agent", "engine"],
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
        assert value.shape == torch.Size([1])

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
            readable_by=["engine", "agent"],
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
                readable_by=["agent", "engine"],  # Finite engine/agent readers
                writable_by=["engine"],
                default=1.0,
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=4, device=torch.device("cpu"))

        # acs cannot read (not in readable_by)
        with pytest.raises(PermissionError, match="Unknown actor.*acs.*read"):
            registry.get("energy", reader="acs")

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
                readable_by=["agent", "engine"],
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
                readable_by=["agent", "engine"],
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
                readable_by=["agent", "engine"],
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
                readable_by=["agent", "engine"],
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
                readable_by=["agent", "engine"],
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
                readable_by=["agent", "engine"],
                writable_by=["engine"],
                default=1.0,
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=2, device=torch.device("cpu"))

        wrong_dtype = torch.ones(2, dtype=torch.int64)
        with pytest.raises(ValueError, match="dtype"):
            registry.set("energy", wrong_dtype, writer="engine")

    def test_set_global_scalar_updates_single_value(self):
        """Set a global scalar: one value per world, each world its own."""
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

        registry = VariableRegistry(variables=variables, num_agents=4, device=torch.device("cpu"))

        # Update world 2's row only
        new_value = torch.tensor([0.0, 0.0, 0.707, 0.0], device=torch.device("cpu"))
        registry.set("time_sin", new_value, writer="engine")

        # Verify update
        value = registry.get("time_sin", reader="agent")
        assert value.tolist() == pytest.approx([0.0, 0.0, 0.707, 0.0])


class TestRegistryScopeSemantics:
    """Test scope-specific tensor shape semantics."""

    def test_global_scalar_shape(self):
        """Global scalar has shape [num_worlds]."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="global_var",
                scope="global",
                type="scalar",
                lifetime="tick",
                readable_by=["agent", "engine"],
                writable_by=["engine"],
                default=1.0,
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=10, device=torch.device("cpu"))

        value = registry.get("global_var", reader="agent")
        assert value.shape == torch.Size([10])  # One value per world (S1: one world per agent)

    def test_global_vector_shape(self):
        """Global vector has shape [num_worlds, dims]."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="global_vec",
                scope="global",
                type="vecNf",
                dims=3,
                lifetime="tick",
                readable_by=["agent", "engine"],
                writable_by=["engine"],
                default=[1.0, 2.0, 3.0],
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=10, device=torch.device("cpu"))

        value = registry.get("global_vec", reader="agent")
        assert value.shape == torch.Size([10, 3])  # [num_worlds, dims]
        assert torch.equal(value[7], torch.tensor([1.0, 2.0, 3.0]))

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
                readable_by=["agent", "engine"],
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
                readable_by=["agent", "engine"],
                writable_by=["engine"],
                default=[0.0, 0.0],
            )
        ]

        registry = VariableRegistry(variables=variables, num_agents=10, device=torch.device("cpu"))

        value = registry.get("agent_vec", reader="agent")
        assert value.shape == torch.Size([10, 2])  # [num_agents, dims]


class TestRegistryWorldStructureScopes:
    """Test world-structure scope storage."""

    def test_variable_scope_enum_has_no_zone_group_pair_message_or_agent_private(self):
        """zone/group (VFS WP2) and pair/message/agent_private (VFS WP15) are deleted."""
        from townlet.vfs.schema import VariableScope

        assert {scope.value for scope in VariableScope} == {"global", "agent", "item", "affordance"}

    def test_registry_initializes_affordance_scalars(self):
        """Dense scope prefixes should match the declared world extents."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="occupied_by",
                scope="affordance",
                type="agent_ref",
                lifetime="episode",
                readable_by=["engine"],
                writable_by=["engine"],
                default=None,
            ),
        ]

        registry = VariableRegistry(
            variables=variables,
            num_agents=3,
            num_affordances=4,
            device=torch.device("cpu"),
        )

        assert registry.get("occupied_by", reader="engine").shape == torch.Size([3, 4])
        assert torch.all(registry.get("occupied_by", reader="engine") == -1)

    def test_registry_prefixes_vectors_and_tensors_with_scope_dimensions(self):
        """Vector and tensor storage should add the scope dimensions before payload dimensions."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variables = [
            VariableDef(
                id="relative_offset",
                scope="agent",
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

        assert registry.get("relative_offset", reader="engine").shape == torch.Size([4, 2])
        assert registry.get("affordance_slots", reader="engine").shape == torch.Size([4, 6, 2, 3])

    def test_registry_requires_explicit_extent_for_non_agent_relational_scope(self):
        """Missing world extents should fail loudly instead of allocating ambiguous storage."""
        from townlet.vfs.registry import VariableRegistry
        from townlet.vfs.schema import VariableDef

        variable = VariableDef(
            id="occupied_by",
            scope="affordance",
            type="scalar",
            lifetime="episode",
            readable_by=["engine"],
            writable_by=["engine"],
            default=-1.0,
        )

        with pytest.raises(ValueError, match="num_affordances.*positive"):
            VariableRegistry(variables=[variable], num_agents=3, device=torch.device("cpu"))


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
                readable_by=["agent", "engine"],
                writable_by=["engine"],
                default=1.0,
            ),
            VariableDef(
                id="position",
                scope="agent",
                type="vecNf",
                dims=2,
                lifetime="episode",
                readable_by=["agent", "engine"],
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
                readable_by=["agent", "engine"],
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
