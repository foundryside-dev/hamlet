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
        VFSProfileCompiler().compile_profile([declaration], {"energy": "float"}, cross_scope=())


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
    compiled = VFSProfileCompiler().compile_profile(declarations, cross_scope=())
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
    compiled = compiler.compile_profile(profile, cross_scope=())
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
    compiled = compiler.compile_profile(profile, bar_schema={"energy": "float"}, cross_scope=())
    assert compiled.variables[0].name == "avg_energy"


def test_agent_static_dependency_proves_a_batched_output():
    """An agent static is per-agent storage, so an expression over it alone is agent-shaped
    (the deleted eager evaluator rebuilt it from its scalar literal and had to refuse this)."""
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
    compiled = VFSProfileCompiler().compile_profile(declarations, cross_scope=())
    assert compiled.dependencies["computed"] == ("source",)


def _declaration(identifier: str, *, scope: str, expression: str | None = None, type: str = "scalar", **extra) -> VariableDeclaration:
    payload = {
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "id": identifier,
        "scope": scope,
        "type": type,
        "lifetime": "episode",
        "semantic_type": "custom",
        "exposed_to": [],
        "initial_value": False if type == "bool" else 0.0,
        **extra,
    }
    if expression is not None:
        payload["expression"] = expression
    return VariableDeclaration(**payload)


def test_agent_expression_reads_globals_by_bare_name_without_a_dependency_edge():
    """V7: every global id is a scalar input of the agent profile, like `tick`, never an edge."""
    globals_ = [_declaration("day_phase", scope="global", expression="tick"), _declaration("scale", scope="global")]
    agents = [
        _declaration("is_night", scope="agent", type="bool", expression="day_phase > 0.5 and bar.energy < 1.0"),
        _declaration("scaled", scope="agent", expression="bar.energy * scale"),
    ]
    compiled = VFSProfileCompiler().compile_profile(agents, {"energy": "float"}, cross_scope=globals_)
    assert {var.name for var in compiled.variables} == {"is_night", "scaled"}
    assert compiled.dependencies == {"is_night": (), "scaled": ()}
    assert compiled.variables[0].ast is not None


def test_agent_expression_over_a_global_alone_is_still_batch_shaped_at_compile():
    """A global-only agent expression has no agent axis; the shape proof refuses it as before."""
    with pytest.raises(TypeCheckError, match="expression shape is scalar, expected agent"):
        VFSProfileCompiler().compile_profile(
            [_declaration("flag", scope="agent", type="bool", expression="day_phase > 0.5")],
            {"energy": "float"},
            cross_scope=[_declaration("day_phase", scope="global", expression="tick")],
        )


def test_agent_expression_over_a_global_tensor_refuses_at_compile():
    """A global tensor is admitted with its declared type, so arithmetic over it refuses at type check."""
    with pytest.raises(TypeCheckError, match="incompatible types float and tensor1d"):
        VFSProfileCompiler().compile_profile(
            [_declaration("heat", scope="agent", expression="bar.energy * grid")],
            {"energy": "float"},
            cross_scope=[_declaration("grid", scope="global", type="tensor1d", shape=[2], initial_value=[0.0, 0.0])],
        )


def test_global_expression_reading_agent_state_refuses_as_scope_widening():
    with pytest.raises(
        TypeCheckError,
        match=r"Variable 'gb' is global-scope but its expression reads agent-scope variable\(s\) \['public_state'\]",
    ):
        VFSProfileCompiler().compile_profile(
            [_declaration("gb", scope="global", expression="public_state * 2.0")],
            {"energy": "float"},
            cross_scope=[_declaration("public_state", scope="agent")],
        )


def test_cross_scope_roster_must_be_the_other_scope():
    with pytest.raises(ValueError, match="cross_scope for a agent profile holds global declarations only"):
        VFSProfileCompiler().compile_profile(
            [_declaration("a", scope="agent")],
            cross_scope=[_declaration("b", scope="agent")],
        )
