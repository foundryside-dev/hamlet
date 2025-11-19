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
            GlobalVFSVariableConfig(name="day_count", type="int", initial_value=0),
            GlobalVFSVariableConfig(name="tick", type="int", initial_value=0),
        ]
    )

    compiler = VFSProfileCompiler()
    graph = compiler.build_dependency_graph(profile.variables)

    # No dependencies = no edges
    assert len(graph.edges) == 0
    assert set(graph.nodes) == {"day_count", "tick"}


def test_build_dependency_graph_with_deps():
    """Variables with expression dependencies have edges."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(name="tick", type="int", initial_value=0),
            GlobalVFSVariableConfig(name="is_night", type="bool", expression="tick % 24 >= 18"),
        ]
    )

    compiler = VFSProfileCompiler()
    graph = compiler.build_dependency_graph(profile.variables)

    # is_night depends on tick
    assert ("tick", "is_night") in graph.edges


def test_build_dependency_graph_nested_deps():
    """Nested dependencies create transitive edges."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(name="a", type="int", initial_value=1),
            GlobalVFSVariableConfig(name="b", type="int", expression="a + 1"),
            GlobalVFSVariableConfig(name="c", type="int", expression="b + 1"),
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
            GlobalVFSVariableConfig(name="target", type="agent_ref", initial_value=0),
            # Expression uses PathAccess: target.bar.energy (should extract "target" as dependency)
            GlobalVFSVariableConfig(name="is_low", type="bool", expression="target.bar.energy < 0.2"),
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
            GlobalVFSVariableConfig(name="a", type="int", expression="b + 1"),
            GlobalVFSVariableConfig(name="b", type="int", expression="a + 1"),
        ]
    )

    compiler = VFSProfileCompiler()

    with pytest.raises(CircularDependencyError, match="cycle"):
        compiler.topological_sort(profile.variables)


def test_detect_circular_dependency_complex():
    """Detect complex circular dependency (a -> b -> c -> a)."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(name="a", type="int", expression="c + 1"),
            GlobalVFSVariableConfig(name="b", type="int", expression="a + 1"),
            GlobalVFSVariableConfig(name="c", type="int", expression="b + 1"),
        ]
    )

    compiler = VFSProfileCompiler()

    with pytest.raises(CircularDependencyError, match="cycle"):
        compiler.topological_sort(profile.variables)


def test_topological_sort_no_deps():
    """Topological sort with no dependencies."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(name="a", type="int", initial_value=1),
            GlobalVFSVariableConfig(name="b", type="int", initial_value=2),
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
            GlobalVFSVariableConfig(name="c", type="int", expression="b + 1"),
            GlobalVFSVariableConfig(name="a", type="int", initial_value=1),
            GlobalVFSVariableConfig(name="b", type="int", expression="a + 1"),
        ]
    )

    compiler = VFSProfileCompiler()
    sorted_vars = compiler.topological_sort(profile.variables)

    # Should be ordered: a, b, c
    names = [v.name for v in sorted_vars]
    assert names == ["a", "b", "c"]
