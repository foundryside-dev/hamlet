"""Tests for VFS expression evaluation integration."""

import pytest

from townlet.config.variables_config import VariableDeclaration
from townlet.vfs.profiles import CircularDependencyError, VFSProfileCompiler
from townlet.world.expression.type_checker import TypeCheckError


@pytest.mark.parametrize("scope,expression", [("agent", "3.0"), ("global", "bar.energy"), ("global", "mean(bar.energy)")])
def test_expression_result_must_match_runtime_scope_shape(scope, expression):
    declaration = VariableDeclaration(
        readable_by=["engine", "agent"],
        writable_by=["engine"],
        id="computed",
        scope=scope,
        type="scalar",
        lifetime="episode",
        semantic_type="custom",
        exposed_to=[],
        initial_value=0.0,
        expression=expression,
    )
    with pytest.raises(TypeCheckError, match="shape"):
        VFSProfileCompiler().compile_profile([declaration], {"energy": "float"}, evaluation_mode="mark_and_sweep")


def test_agent_expression_static_dependency_retains_batched_shape():
    declarations = [
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            id="source",
            scope="agent",
            type="scalar",
            lifetime="episode",
            semantic_type="custom",
            exposed_to=[],
            initial_value=2.0,
        ),
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            id="computed",
            scope="agent",
            type="scalar",
            lifetime="episode",
            semantic_type="custom",
            exposed_to=[],
            initial_value=0.0,
            expression="source + 1.0",
        ),
    ]
    compiled = VFSProfileCompiler().compile_profile(declarations, evaluation_mode="mark_and_sweep")
    assert compiled.variables[-1].name == "computed"


def test_build_dependency_graph_no_deps():
    """Variables with no dependencies have no edges."""
    profile = [
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="day_count",
            type="scalar",
            initial_value=0,
            scope="global",
            lifetime="persistent",
            exposed_to=[],
        ),
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="tick",
            type="scalar",
            initial_value=0,
            scope="global",
            lifetime="persistent",
            exposed_to=[],
        ),
    ]
    compiler = VFSProfileCompiler()
    graph = compiler.build_dependency_graph(profile)
    assert len(graph.edges) == 0
    assert set(graph.nodes) == {"day_count", "tick"}


def test_build_dependency_graph_with_deps():
    """Variables with expression dependencies have edges.

    Uses ``hour`` rather than ``tick`` as the dependency: ``tick`` is now the reserved
    engine-written VFS global (token-obs design ruling 6) and is ambient in profile
    expressions — it never becomes an in-profile dependency edge, which would defeat the
    point of this test. See test_engine_tick_variable.py for tick-specific coverage.
    """
    profile = [
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="hour",
            type="scalar",
            initial_value=0,
            scope="global",
            lifetime="persistent",
            exposed_to=[],
        ),
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="is_night",
            type="bool",
            expression="hour % 24 >= 18",
            scope="global",
            lifetime="persistent",
            exposed_to=[],
            initial_value=False,
        ),
    ]
    compiler = VFSProfileCompiler()
    graph = compiler.build_dependency_graph(profile)
    assert ("hour", "is_night") in graph.edges


def test_build_dependency_graph_nested_deps():
    """Nested dependencies create transitive edges."""
    profile = [
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="a",
            type="scalar",
            initial_value=1,
            scope="global",
            lifetime="persistent",
            exposed_to=[],
        ),
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="b",
            type="scalar",
            expression="a + 1",
            scope="global",
            lifetime="persistent",
            exposed_to=[],
            initial_value=0.0,
        ),
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="c",
            type="scalar",
            expression="b + 1",
            scope="global",
            lifetime="persistent",
            exposed_to=[],
            initial_value=0.0,
        ),
    ]
    compiler = VFSProfileCompiler()
    graph = compiler.build_dependency_graph(profile)
    assert ("a", "b") in graph.edges
    assert ("b", "c") in graph.edges


def test_build_dependency_graph_with_path_deps():
    """Variables with PathAccess dependencies (e.g., target.bar.energy) extract root namespace."""
    profile = [
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="target",
            type="agent_ref",
            initial_value=0,
            scope="global",
            lifetime="persistent",
            exposed_to=[],
        ),
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="is_low",
            type="bool",
            expression="target.bar.energy < 0.2",
            scope="global",
            lifetime="persistent",
            exposed_to=[],
            initial_value=False,
        ),
    ]
    compiler = VFSProfileCompiler()
    graph = compiler.build_dependency_graph(profile)
    assert ("target", "is_low") in graph.edges
    assert len(graph.edges) == 1


def test_detect_circular_dependency_simple():
    """Detect simple circular dependency (a -> b -> a)."""
    profile = [
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="a",
            type="scalar",
            expression="b + 1",
            scope="global",
            lifetime="persistent",
            exposed_to=[],
            initial_value=0.0,
        ),
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="b",
            type="scalar",
            expression="a + 1",
            scope="global",
            lifetime="persistent",
            exposed_to=[],
            initial_value=0.0,
        ),
    ]
    compiler = VFSProfileCompiler()
    with pytest.raises(CircularDependencyError, match="cycle"):
        compiler.topological_sort(profile)


def test_detect_circular_dependency_complex():
    """Detect complex circular dependency (a -> b -> c -> a)."""
    profile = [
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="a",
            type="scalar",
            expression="c + 1",
            scope="global",
            lifetime="persistent",
            exposed_to=[],
            initial_value=0.0,
        ),
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="b",
            type="scalar",
            expression="a + 1",
            scope="global",
            lifetime="persistent",
            exposed_to=[],
            initial_value=0.0,
        ),
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="c",
            type="scalar",
            expression="b + 1",
            scope="global",
            lifetime="persistent",
            exposed_to=[],
            initial_value=0.0,
        ),
    ]
    compiler = VFSProfileCompiler()
    with pytest.raises(CircularDependencyError, match="cycle"):
        compiler.topological_sort(profile)


def test_topological_sort_no_deps():
    """Topological sort with no dependencies."""
    profile = [
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="a",
            type="scalar",
            initial_value=1,
            scope="global",
            lifetime="persistent",
            exposed_to=[],
        ),
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="b",
            type="scalar",
            initial_value=2,
            scope="global",
            lifetime="persistent",
            exposed_to=[],
        ),
    ]
    compiler = VFSProfileCompiler()
    sorted_vars = compiler.topological_sort(profile)
    assert len(sorted_vars) == 2


def test_topological_sort_linear_deps():
    """Topological sort with linear dependencies (a -> b -> c)."""
    profile = [
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="c",
            type="scalar",
            expression="b + 1",
            scope="global",
            lifetime="persistent",
            exposed_to=[],
            initial_value=0.0,
        ),
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="a",
            type="scalar",
            initial_value=1,
            scope="global",
            lifetime="persistent",
            exposed_to=[],
        ),
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="b",
            type="scalar",
            expression="a + 1",
            scope="global",
            lifetime="persistent",
            exposed_to=[],
            initial_value=0.0,
        ),
    ]
    compiler = VFSProfileCompiler()
    sorted_vars = compiler.topological_sort(profile)
    names = [v.id for v in sorted_vars]
    assert names == ["a", "b", "c"]


def test_compile_variable_with_expression():
    """Compiler parses and type-checks expressions."""
    var = VariableDeclaration(
        readable_by=["engine", "agent"],
        writable_by=["engine"],
        semantic_type="custom",
        id="is_night",
        type="bool",
        expression="tick % 24 >= 18",
        scope="global",
        lifetime="persistent",
        exposed_to=[],
        initial_value=False,
    )
    compiler = VFSProfileCompiler()
    schema = {"tick": "int"}
    compiled = compiler.compile_variable(var, schema)
    assert compiled.name == "is_night"
    assert compiled.ast is not None
    assert compiled.result_type == "bool"


def test_compile_variable_with_initial_value():
    """Compiler handles static initial values (no expression)."""
    var = VariableDeclaration(
        readable_by=["engine", "agent"],
        writable_by=["engine"],
        semantic_type="custom",
        id="day_count",
        type="scalar",
        initial_value=0,
        scope="global",
        lifetime="persistent",
        exposed_to=[],
    )
    compiler = VFSProfileCompiler()
    schema = {}
    compiled = compiler.compile_variable(var, schema)
    assert compiled.name == "day_count"
    assert compiled.ast is None
    assert compiled.initial_value == 0


def test_compile_variable_type_mismatch():
    """Compiler catches type mismatches."""
    from townlet.world.expression.type_checker import TypeCheckError

    var = VariableDeclaration(
        readable_by=["engine", "agent"],
        writable_by=["engine"],
        semantic_type="custom",
        id="invalid",
        type="bool",
        expression="tick + 1",
        scope="global",
        lifetime="persistent",
        exposed_to=[],
        initial_value=False,
    )
    compiler = VFSProfileCompiler()
    schema = {"tick": "int"}
    with pytest.raises(TypeCheckError, match="bool"):
        compiler.compile_variable(var, schema)


def test_compile_global_profile():
    """Compiler compiles global profile with dependency ordering."""
    profile = [
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="c",
            type="scalar",
            expression="b + 1",
            scope="global",
            lifetime="persistent",
            exposed_to=[],
            initial_value=0.0,
        ),
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="a",
            type="scalar",
            initial_value=1,
            scope="global",
            lifetime="persistent",
            exposed_to=[],
        ),
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="b",
            type="scalar",
            expression="a + 1",
            scope="global",
            lifetime="persistent",
            exposed_to=[],
            initial_value=0.0,
        ),
    ]
    compiler = VFSProfileCompiler()
    compiled = compiler.compile_profile(profile, evaluation_mode="mark_and_sweep")
    assert [v.name for v in compiled.variables] == ["a", "b", "c"]
    assert all(v.ast is not None or v.initial_value is not None for v in compiled.variables)


def test_compile_agent_profile_with_bars():
    """Compiler includes bars in schema for expressions."""
    profile = [
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            semantic_type="custom",
            id="avg_energy",
            type="scalar",
            expression="bar.energy",
            scope="agent",
            lifetime="persistent",
            exposed_to=[],
            initial_value=0.0,
        )
    ]
    compiler = VFSProfileCompiler()
    compiled = compiler.compile_profile(profile, bar_schema={"energy": "float"}, evaluation_mode="mark_and_sweep")
    assert compiled.variables[0].name == "avg_energy"


def test_eager_agent_static_dependency_refuses_the_scalar_reinitialization_shape():
    declarations = [
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            id="source",
            scope="agent",
            type="scalar",
            lifetime="episode",
            semantic_type="custom",
            exposed_to=[],
            initial_value=2.0,
        ),
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            id="computed",
            scope="agent",
            type="scalar",
            lifetime="episode",
            semantic_type="custom",
            exposed_to=[],
            initial_value=0.0,
            expression="source + 1.0",
        ),
    ]
    with pytest.raises(TypeCheckError, match="shape"):
        VFSProfileCompiler().compile_profile(declarations, evaluation_mode="eager")
