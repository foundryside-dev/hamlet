"""Tests for VFS expression evaluation integration."""

import pytest

from townlet.config.vfs_profiles_config import (
    GlobalVFSProfileConfig,
    GlobalVFSVariableConfig,
)
from townlet.vfs.profiles import CircularDependencyError, VFSProfileCompiler


def test_build_dependency_graph_no_deps():
    """Variables with no dependencies have no edges."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(semantic_type="custom", name="day_count", type="int", initial_value=0),
            GlobalVFSVariableConfig(semantic_type="custom", name="tick", type="int", initial_value=0),
        ]
    )

    compiler = VFSProfileCompiler()
    graph = compiler.build_dependency_graph(profile.variables)

    # No dependencies = no edges
    assert len(graph.edges) == 0
    assert set(graph.nodes) == {"day_count", "tick"}


def test_build_dependency_graph_with_deps():
    """Variables with expression dependencies have edges.

    Uses ``hour`` rather than ``tick`` as the dependency: ``tick`` is now the reserved
    engine-written VFS global (token-obs design ruling 6) and is ambient in profile
    expressions — it never becomes an in-profile dependency edge, which would defeat the
    point of this test. See test_engine_tick_variable.py for tick-specific coverage.
    """
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(semantic_type="custom", name="hour", type="int", initial_value=0),
            GlobalVFSVariableConfig(semantic_type="custom", name="is_night", type="bool", expression="hour % 24 >= 18"),
        ]
    )

    compiler = VFSProfileCompiler()
    graph = compiler.build_dependency_graph(profile.variables)

    # is_night depends on hour
    assert ("hour", "is_night") in graph.edges


def test_build_dependency_graph_nested_deps():
    """Nested dependencies create transitive edges."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(semantic_type="custom", name="a", type="int", initial_value=1),
            GlobalVFSVariableConfig(semantic_type="custom", name="b", type="int", expression="a + 1"),
            GlobalVFSVariableConfig(semantic_type="custom", name="c", type="int", expression="b + 1"),
        ]
    )

    compiler = VFSProfileCompiler()
    graph = compiler.build_dependency_graph(profile.variables)

    # a -> b -> c
    assert ("a", "b") in graph.edges
    assert ("b", "c") in graph.edges


def test_build_dependency_graph_with_path_deps():
    """Variables with PathAccess dependencies (e.g., target.bar.energy) extract root namespace."""
    profile = GlobalVFSProfileConfig(
        variables=[
            # Simulate a variable named "target" that would be accessed via PathAccess
            GlobalVFSVariableConfig(semantic_type="custom", name="target", type="agent_ref", initial_value=0),
            # Expression uses PathAccess: target.bar.energy (should extract "target" as dependency)
            GlobalVFSVariableConfig(semantic_type="custom", name="is_low", type="bool", expression="target.bar.energy < 0.2"),
        ]
    )

    compiler = VFSProfileCompiler()
    graph = compiler.build_dependency_graph(profile.variables)

    # is_low depends on target (root namespace from target.bar.energy)
    assert ("target", "is_low") in graph.edges
    assert len(graph.edges) == 1  # Only one dependency


def test_detect_circular_dependency_simple():
    """Detect simple circular dependency (a -> b -> a)."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(semantic_type="custom", name="a", type="int", expression="b + 1"),
            GlobalVFSVariableConfig(semantic_type="custom", name="b", type="int", expression="a + 1"),
        ]
    )

    compiler = VFSProfileCompiler()

    with pytest.raises(CircularDependencyError, match="cycle"):
        compiler.topological_sort(profile.variables)


def test_detect_circular_dependency_complex():
    """Detect complex circular dependency (a -> b -> c -> a)."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(semantic_type="custom", name="a", type="int", expression="c + 1"),
            GlobalVFSVariableConfig(semantic_type="custom", name="b", type="int", expression="a + 1"),
            GlobalVFSVariableConfig(semantic_type="custom", name="c", type="int", expression="b + 1"),
        ]
    )

    compiler = VFSProfileCompiler()

    with pytest.raises(CircularDependencyError, match="cycle"):
        compiler.topological_sort(profile.variables)


def test_topological_sort_no_deps():
    """Topological sort with no dependencies."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(semantic_type="custom", name="a", type="int", initial_value=1),
            GlobalVFSVariableConfig(semantic_type="custom", name="b", type="int", initial_value=2),
        ]
    )

    compiler = VFSProfileCompiler()
    sorted_vars = compiler.topological_sort(profile.variables)

    # Both have no deps, order doesn't matter (but should be deterministic)
    assert len(sorted_vars) == 2


def test_topological_sort_linear_deps():
    """Topological sort with linear dependencies (a -> b -> c)."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(semantic_type="custom", name="c", type="int", expression="b + 1"),
            GlobalVFSVariableConfig(semantic_type="custom", name="a", type="int", initial_value=1),
            GlobalVFSVariableConfig(semantic_type="custom", name="b", type="int", expression="a + 1"),
        ]
    )

    compiler = VFSProfileCompiler()
    sorted_vars = compiler.topological_sort(profile.variables)

    # Should be ordered: a, b, c
    names = [v.name for v in sorted_vars]
    assert names == ["a", "b", "c"]


def test_compile_variable_with_expression():
    """Compiler parses and type-checks expressions."""
    var = GlobalVFSVariableConfig(semantic_type="custom", name="is_night", type="bool", expression="tick % 24 >= 18")

    compiler = VFSProfileCompiler()
    schema = {"tick": "int"}  # Available variables

    compiled = compiler.compile_variable(var, schema)

    assert compiled.name == "is_night"
    assert compiled.ast is not None  # Parsed AST
    assert compiled.result_type == "bool"


def test_compile_variable_with_initial_value():
    """Compiler handles static initial values (no expression)."""
    var = GlobalVFSVariableConfig(semantic_type="custom", name="day_count", type="int", initial_value=0)

    compiler = VFSProfileCompiler()
    schema = {}

    compiled = compiler.compile_variable(var, schema)

    assert compiled.name == "day_count"
    assert compiled.ast is None  # No expression
    assert compiled.initial_value == 0


def test_compile_variable_type_mismatch():
    """Compiler catches type mismatches."""
    from townlet.world.expression.type_checker import TypeCheckError

    var = GlobalVFSVariableConfig(semantic_type="custom", name="invalid", type="bool", expression="tick + 1")  # Returns int, not bool

    compiler = VFSProfileCompiler()
    schema = {"tick": "int"}

    with pytest.raises(TypeCheckError, match="bool"):
        compiler.compile_variable(var, schema)


def test_compile_global_profile():
    """Compiler compiles global profile with dependency ordering."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(semantic_type="custom", name="c", type="int", expression="b + 1"),
            GlobalVFSVariableConfig(semantic_type="custom", name="a", type="int", initial_value=1),
            GlobalVFSVariableConfig(semantic_type="custom", name="b", type="int", expression="a + 1"),
        ]
    )

    compiler = VFSProfileCompiler()
    compiled = compiler.compile_global_profile(profile)

    # Variables sorted in dependency order
    assert [v.name for v in compiled.variables] == ["a", "b", "c"]

    # All variables compiled
    assert all(v.ast is not None or v.initial_value is not None for v in compiled.variables)


def test_compile_global_profile_with_bars():
    """Compiler includes bars in schema for expressions."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(
                semantic_type="custom",
                name="avg_energy",
                type="float",
                expression="bar.energy",  # Reference to bar
            ),
        ]
    )

    compiler = VFSProfileCompiler()
    # Should not raise (bar.energy is valid path)
    compiled = compiler.compile_global_profile(profile, bar_schema={"energy": "float"})

    assert compiled.variables[0].name == "avg_energy"
