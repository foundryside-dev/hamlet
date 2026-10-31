"""The type checker and the evaluator agree for every registered expression function.

For each ``FUNCTION_SPECS`` entry, one expression with a per-agent argument is parsed,
type-checked and evaluated on a batch-3 context. The declared return type must name the
evaluated dtype, and the result must keep the batch axis: ``[3]`` for a scalar-typed
result, ``[3, D]`` for a vector-typed one. A function without a row here fails the
coverage test, so a new function cannot ship without proving the contract.

The context is the enriched one (temporal history, step counter, positions): what a
function needs from its context is a separate contract (``FunctionSpec.requires``).
"""

from __future__ import annotations

import pytest
import torch

from townlet.world.expression.ast_nodes import OperatorType
from townlet.world.expression.context import ExecutionContext
from townlet.world.expression.evaluator import Evaluator
from townlet.world.expression.functions import FUNCTION_SPECS, VectorTypes
from townlet.world.expression.history import TemporalHistory
from townlet.world.expression.parser import ExpressionParser
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError

BATCH = 3

SCHEMA = {
    "bar.f": "float",
    "bar.g": "float",
    "bar.i": "int",
    "bar.j": "int",
    "bar.b": "bool",
    "vfs.pos": "vec2f",
    "vfs.ipos": "vec2i",
    "vfs.goal": "vec2f",
    "vfs.home": "vec2f",
    "vfs.v3": "vec3f",
    "vfs.n": "vecNf",
    "vfs.sites": "tensor2d",
    "vfs.started": "int",
}

# One expression per registered function. Every row carries a per-agent argument so the
# shape half of the contract is exercised, not just the dtype half.
CASES: dict[str, str] = {
    # Math
    "max": "max(bar.f, bar.g)",
    "min": "min(bar.i, 2)",
    "abs": "abs(bar.f - 0.5)",
    "clamp": "clamp(bar.f, 0.2, 0.8)",
    "clamp01": "clamp01(bar.i)",
    "sigmoid": "sigmoid(bar.i)",
    "tanh": "tanh(bar.f)",
    "smoothstep": "smoothstep(0.0, 1.0, bar.f)",
    "threshold": "threshold(bar.f, 0.2, 0.8)",
    # Statistics
    "mean": "mean(bar.i, bar.i)",
    "variance": "variance(bar.f, bar.g)",
    "sum": "sum(bar.i, bar.i)",
    "product": "product(bar.i, 2)",
    "min_all": "min_all(bar.f, 0.5)",
    "max_all": "max_all(bar.i, bar.i)",
    "argmin": "argmin(bar.f, bar.g)",
    "argmax": "argmax(bar.f, 0.5)",
    "count_where": "count_where(bar.b, true)",
    # Logic and masks
    "all": "all(bar.b, bar.b)",
    "any": "any(bar.b, true)",
    "where": "where(bar.b, bar.f, bar.g)",
    "masked_add": "masked_add(bar.f, 1.0, bar.b)",
    "masked_set": "masked_set(bar.f, 1.0, bar.b)",
    "gather": "gather(vfs.n, bar.i - 1)",
    "scatter": "scatter(vfs.n, bar.i - 1, bar.g)",
    "one_hot": "one_hot(bar.i - 1, 3)",
    # Sampling
    "normal_dist": "normal_dist(bar.f, 0.1)",
    "uniform": "uniform(bar.f, 1.0)",
    "perlin_noise": "perlin_noise(bar.f, bar.g)",
    "simplex_noise": "simplex_noise(bar.f, bar.g, 3)",
    # Temporal
    "time_in_window": "time_in_window(bar.i, 1, 3)",
    "phase_sin": "phase_sin(bar.i, 24.0)",
    "phase_cos": "phase_cos(bar.i, 24)",
    "elapsed_ticks": "elapsed_ticks(vfs.started)",
    "lag": "lag(bar.f, 1)",
    "delta": "delta(bar.f)",
    "moving_average": "moving_average(bar.i, 2)",
    "ema": "ema(bar.f, 0.5)",
    "rate_of_change": "rate_of_change(bar.f, 1)",
    "rising_edge": "rising_edge(bar.b)",
    "falling_edge": "falling_edge(bar.b)",
    # Spatial
    "distance": "distance(vfs.pos, vfs.goal)",
    "manhattan_distance": "manhattan_distance(vfs.pos, vfs.home)",
    "within_radius": "within_radius(vfs.pos, vfs.goal, 0.5)",
    "nearest": "nearest(vfs.pos, vfs.sites)",
    "normalize": "normalize(vfs.pos)",
    # Affordance
    "distance_to_affordance": 'distance_to_affordance("WORK")',
    "in_range": 'in_range("WORK", 2.0)',
    "direction_to_affordance": 'direction_to_affordance("WORK")',
}

# A second expression for every function whose declared type depends on its argument
# types: the arguments mix int and float (or an int literal against a float input) so the
# promotion rule is exercised, not just the homogeneous case. A function whose return type
# is fixed has no row here.
MIXED_CASES: dict[str, str] = {
    "max": "max(bar.i, bar.f)",
    "min": "min(bar.i, 0.5)",
    "abs": "abs(bar.i)",
    "clamp": "clamp(bar.i, 0.2, 0.8)",
    "min_all": "min_all(bar.i, bar.f)",
    "max_all": "max_all(bar.i, 0.5)",
    "where": "where(bar.b, bar.i, 0.5)",
    "masked_add": "masked_add(bar.i, 0.5, bar.b)",
    "masked_set": "masked_set(bar.i, 0.5, bar.b)",
    "gather": "gather(vfs.ipos, bar.j % 2)",
    "scatter": "scatter(vfs.pos, bar.j % 2, bar.i)",
    "lag": "lag(bar.i, 1)",
    "delta": "delta(bar.i)",
    "normalize": "normalize(vfs.ipos)",
}

POS = torch.tensor([[0.0, 0.0], [1.0, 1.0], [3.0, 4.0]])
IPOS = torch.tensor([[0, 0], [1, 1], [3, 4]])
GOAL = torch.tensor([[0.0, 4.0], [1.0, 1.0], [0.0, 0.0]])
# `home` and `sites` are globals: one row per world (S1), here the same in every world.
HOME = torch.tensor([2.0, 2.0]).expand(BATCH, 2).clone()
SITES = torch.tensor([[0.0, 1.0], [2.0, 3.0], [10.0, 10.0]]).expand(BATCH, 3, 2).clone()


def make_context() -> ExecutionContext:
    bars = {
        "f": torch.tensor([0.1, 0.5, 0.9]),
        "g": torch.tensor([0.3, 0.3, 0.3]),
        "i": torch.tensor([1, 2, 3]),
        "j": torch.tensor([3, 1, 2]),
        "b": torch.tensor([True, False, True]),
    }
    vfs = {
        "pos": POS.clone(),
        "ipos": IPOS.clone(),
        "goal": GOAL.clone(),
        "home": HOME.clone(),
        "v3": torch.zeros(BATCH, 3),
        "n": torch.zeros(BATCH, 5),
        "sites": SITES.clone(),
        "started": torch.tensor([3, 7, 9]),
    }
    history = TemporalHistory({"bar.f": 4, "bar.b": 4, "bar.i": 4}, torch.device("cpu"))
    history.push("bar.f", torch.zeros(BATCH))
    history.push("bar.b", torch.zeros(BATCH, dtype=torch.bool))
    history.push("bar.i", torch.zeros(BATCH, dtype=torch.long))
    return ExecutionContext(
        bars=bars,
        vfs=vfs,
        affordances={},
        temporal={},
        affordance_positions={"WORK": torch.tensor([2.0, 2.0])},
        agent_positions=POS.clone(),
        vfs_types={
            "pos": "vec2f",
            "ipos": "vec2i",
            "goal": "vec2f",
            "home": "vec2f",
            "v3": "vec3f",
            "n": "vecNf",
            "sites": "tensor2d",
            "started": "scalar",
        },
        num_agents=BATCH,
        history=history,
        step=7,
    )


def dtype_class(value: torch.Tensor) -> str:
    if value.dtype == torch.bool:
        return "bool"
    if value.is_floating_point():
        return "float"
    return "int"


def declared_class(declared: str) -> str:
    if declared in {"int", "float", "bool"}:
        return declared
    if declared in VectorTypes:
        return "int" if declared.endswith("i") else "float"
    raise AssertionError(f"unexpected declared type {declared!r}")


def check_and_evaluate(expression: str) -> tuple[str, torch.Tensor]:
    ast = ExpressionParser().parse(expression)
    declared = TypeChecker(SCHEMA).check(ast)
    value = Evaluator(make_context()).evaluate(ast)
    return declared, value


def test_cases_cover_every_registered_function() -> None:
    assert set(CASES) == set(FUNCTION_SPECS), {
        "missing a case": sorted(set(FUNCTION_SPECS) - set(CASES)),
        "case for an unregistered function": sorted(set(CASES) - set(FUNCTION_SPECS)),
    }
    assert set(MIXED_CASES) <= set(FUNCTION_SPECS), sorted(set(MIXED_CASES) - set(FUNCTION_SPECS))


def test_mixed_cases_cover_every_argument_dependent_return_type() -> None:
    """A function whose declared type varies with its argument types needs a mixed row.

    Probe: the same spec with all-int and all-float arguments; when the two declared
    types differ the return type is argument-dependent.
    """
    argument_dependent = set()
    for name, spec in FUNCTION_SPECS.items():
        if spec.max_args == 0:
            continue
        arity = spec.min_args if spec.min_args > 0 else 1
        try:
            all_int = spec.return_type(["int"] * arity)
            all_float = spec.return_type(["float"] * arity)
        except IndexError:
            continue
        if all_int != all_float:
            argument_dependent.add(name)
    assert argument_dependent <= set(MIXED_CASES), sorted(argument_dependent - set(MIXED_CASES))


@pytest.mark.parametrize("name", sorted(FUNCTION_SPECS))
def test_declared_type_matches_evaluated_dtype_and_batch_shape(name: str) -> None:
    _assert_agreement(CASES[name])


@pytest.mark.parametrize("name", sorted(MIXED_CASES))
def test_declared_type_matches_evaluated_dtype_with_mixed_argument_types(name: str) -> None:
    _assert_agreement(MIXED_CASES[name])


def _assert_agreement(expression: str) -> None:
    declared, value = check_and_evaluate(expression)
    assert isinstance(value, torch.Tensor), f"{expression} evaluated to {type(value).__name__}"
    assert dtype_class(value) == declared_class(declared), f"{expression}: declared {declared}, evaluated {value.dtype}"
    if declared in VectorTypes:
        assert value.dim() == 2 and value.shape[0] == BATCH, f"{expression}: declared {declared}, shape {tuple(value.shape)}"
        if declared.startswith("vec2"):
            assert value.shape[1] == 2
    else:
        assert tuple(value.shape) == (BATCH,), f"{expression}: declared {declared}, shape {tuple(value.shape)}"


def test_mean_of_ints_promotes_to_float() -> None:
    declared, value = check_and_evaluate("mean(bar.i, 2)")
    assert declared == "float"
    assert torch.allclose(value, torch.tensor([1.5, 2.0, 2.5]))


def test_stacked_functions_broadcast_a_literal_against_per_agent_inputs() -> None:
    for expression, expected in (
        ("sum(bar.i, 1)", torch.tensor([2.0, 3.0, 4.0])),
        ("product(bar.i, 2)", torch.tensor([2.0, 4.0, 6.0])),
        ("max_all(bar.i, 2)", torch.tensor([2, 2, 3])),
        ("count_where(bar.b, true)", torch.tensor([2, 1, 2])),
    ):
        _declared, value = check_and_evaluate(expression)
        assert torch.equal(value, expected), expression


@pytest.mark.parametrize(
    "op,left,right,expected",
    [
        (OperatorType.ADD, "int", "int", "int"),
        (OperatorType.SUB, "int", "float", "float"),
        (OperatorType.MUL, "float", "int", "float"),
        (OperatorType.DIV, "int", "int", "float"),
        (OperatorType.DIV, "float", "int", "float"),
        (OperatorType.MOD, "int", "int", "int"),
        (OperatorType.POW, "int", "int", "int"),
        (OperatorType.POW, "float", "float", "float"),
    ],
)
def test_arithmetic_operators_declare_the_evaluated_dtype(op: OperatorType, left: str, right: str, expected: str) -> None:
    operand = {"int": "bar.i", "float": "bar.f"}
    declared, value = check_and_evaluate(f"{operand[left]} {op.value} {operand[right]}")
    assert declared == expected
    assert dtype_class(value) == expected


def test_integer_division_is_real_division() -> None:
    declared, value = check_and_evaluate("bar.i / 2")
    assert declared == "float"
    assert torch.allclose(value, torch.tensor([0.5, 1.0, 1.5]))


def test_distance_functions_reduce_the_vector_axis_only() -> None:
    assert torch.allclose(check_and_evaluate("distance(vfs.pos, vfs.goal)")[1], torch.tensor([4.0, 0.0, 5.0]))
    assert torch.allclose(check_and_evaluate('distance(vfs.pos, vfs.goal, "manhattan")')[1], torch.tensor([4.0, 0.0, 7.0]))
    assert torch.allclose(check_and_evaluate("manhattan_distance(vfs.pos, vfs.goal)")[1], torch.tensor([4.0, 0.0, 7.0]))
    assert torch.equal(check_and_evaluate("within_radius(vfs.pos, vfs.goal, 4.5)")[1], torch.tensor([True, True, False]))
    assert torch.equal(check_and_evaluate("nearest(vfs.pos, vfs.sites)")[1], torch.tensor([0, 0, 1]))


def test_distance_against_a_global_vector_is_per_agent_and_between_globals_is_per_world() -> None:
    per_agent = check_and_evaluate("manhattan_distance(vfs.pos, vfs.home)")[1]
    assert torch.allclose(per_agent, torch.tensor([4.0, 2.0, 3.0]))
    per_world = check_and_evaluate("distance(vfs.home, vfs.home)")[1]
    assert torch.equal(per_world, torch.zeros(BATCH))


def test_masked_functions_promote_an_int_value_against_a_float_argument() -> None:
    """Reviewer probe: `masked_add(bar.i, 0.5, bar.b)` typed float but evaluated int64 and truncated 0.5 to 0."""
    declared, value = check_and_evaluate("masked_add(bar.i, 0.5, bar.b)")
    assert declared == "float"
    assert torch.allclose(value, torch.tensor([1.5, 2.0, 3.5]))
    declared, value = check_and_evaluate("masked_set(bar.i, 0.5, bar.b)")
    assert declared == "float"
    assert torch.allclose(value, torch.tensor([0.5, 2.0, 0.5]))
    # A 0-dim float literal against a batched int64 tensor promotes to float under torch's rules.
    assert torch.promote_types(torch.int64, torch.tensor(0.5).dtype) == torch.float32


def test_masked_functions_keep_an_int_value_against_an_int_argument() -> None:
    declared, value = check_and_evaluate("masked_add(bar.i, 1, bar.b)")
    assert declared == "int"
    assert torch.equal(value, torch.tensor([2, 2, 4]))


def test_distance_between_int_and_float_vectors_is_measured_in_float_and_symmetric() -> None:
    """Reviewer probe: `distance(vfs.ipos, vfs.goal)` truncated the float vector to int, giving [0, 0, 5]."""
    euclid = check_and_evaluate("distance(vfs.ipos, vfs.goal)")[1]
    assert torch.allclose(euclid, torch.tensor([4.0, 0.0, 5.0]))
    swapped = check_and_evaluate("distance(vfs.goal, vfs.ipos)")[1]
    assert torch.equal(euclid, swapped)
    goal_half = torch.tensor([[0.5, 0.5], [1.5, 1.5], [0.0, 0.0]])
    assert torch.allclose(_distance_values("distance(vfs.ipos, vfs.goal)", goal_half), torch.tensor([0.70710678, 0.70710678, 5.0]))
    assert torch.allclose(_distance_values("manhattan_distance(vfs.ipos, vfs.goal)", goal_half), torch.tensor([1.0, 1.0, 7.0]))
    assert torch.allclose(_distance_values("manhattan_distance(vfs.goal, vfs.ipos)", goal_half), torch.tensor([1.0, 1.0, 7.0]))
    assert torch.equal(_distance_values("within_radius(vfs.ipos, vfs.goal, 1)", goal_half), torch.tensor([True, True, False]))


def _distance_values(expression: str, goal: torch.Tensor) -> torch.Tensor:
    ast = ExpressionParser().parse(expression)
    TypeChecker(SCHEMA).check(ast)
    context = make_context()
    context.vfs["goal"] = goal
    return Evaluator(context).evaluate(ast)


def test_nearest_measures_int_points_against_float_candidates_in_float() -> None:
    context = make_context()
    context.vfs["sites"] = torch.tensor([[0.9, 0.9], [1.9, 1.9]]).expand(BATCH, 2, 2).clone()
    ast = ExpressionParser().parse("nearest(vfs.ipos, vfs.sites)")
    TypeChecker(SCHEMA).check(ast)
    # ipos row (1,1) is 0.14 from (0.9,0.9); truncating the candidates to (0,0)/(1,1) would pick row 1.
    assert torch.equal(Evaluator(context).evaluate(ast), torch.tensor([0, 0, 1]))


@pytest.mark.parametrize(
    "expression",
    [
        "distance(vfs.pos, vfs.v3)",
        "manhattan_distance(vfs.pos, vfs.v3)",
        "within_radius(vfs.pos, vfs.v3, 1.0)",
    ],
)
def test_vectors_of_different_static_widths_are_refused_at_type_check(expression: str) -> None:
    """Reviewer probe: vec2f against vec3f type-checked and crashed at the first evaluation."""
    ast = ExpressionParser().parse(expression)
    with pytest.raises(TypeCheckError, match="requires vectors of one width"):
        TypeChecker(SCHEMA).check(ast)


@pytest.mark.parametrize("candidates", ["vfs.pos", "vfs.v3", "vfs.n"])
def test_nearest_refuses_vector_candidates_at_type_check(candidates: str) -> None:
    """S1: a vector variable's rows are the batch's worlds, so they are never one world's candidates."""
    ast = ExpressionParser().parse(f"nearest(vfs.pos, {candidates})")
    with pytest.raises(TypeCheckError, match="must be a tensor2d of candidate rows"):
        TypeChecker(SCHEMA).check(ast)


def test_nearest_refuses_candidates_without_the_points_world_axis_at_evaluation() -> None:
    context = make_context()
    context.vfs["sites"] = torch.tensor([[0.9, 0.9], [1.9, 1.9], [5.0, 5.0]])  # [K, D]: no per-world axis
    ast = ExpressionParser().parse("nearest(vfs.pos, vfs.sites)")
    TypeChecker(SCHEMA).check(ast)
    with pytest.raises(ValueError, match="candidates are per world"):
        Evaluator(context).evaluate(ast)


@pytest.mark.parametrize(
    "expression",
    [
        "distance(vfs.pos, vfs.n)",
        "manhattan_distance(vfs.n, vfs.pos)",
        "within_radius(vfs.pos, vfs.n, 1.0)",
        "nearest(vfs.n, vfs.sites)",
    ],
)
def test_a_vecn_width_mismatch_is_a_named_error_at_evaluation(expression: str) -> None:
    """A vecN* type carries no width, so the mismatch surfaces when the function runs, naming it."""
    ast = ExpressionParser().parse(expression)
    TypeChecker(SCHEMA).check(ast)
    name = expression.split("(")[0]
    with pytest.raises(ValueError, match=rf"Function '{name}' requires vectors of one width, got widths"):
        Evaluator(make_context()).evaluate(ast)


def test_a_result_built_only_from_literals_has_no_batch_axis() -> None:
    declared, value = check_and_evaluate("one_hot(2, 3)")
    assert declared == "vecNf"
    assert torch.equal(value, torch.tensor([0.0, 0.0, 1.0]))
    declared, value = check_and_evaluate("one_hot(bar.i - 1, 3)")
    assert declared == "vecNf"
    assert tuple(value.shape) == (BATCH, 3)


def test_normalize_returns_a_unit_vector_per_agent() -> None:
    declared, value = check_and_evaluate("normalize(vfs.pos)")
    assert declared == "vec2f"
    assert torch.allclose(value, torch.tensor([[0.0, 0.0], [0.70710678, 0.70710678], [0.6, 0.8]]))


@pytest.mark.parametrize(
    "expression",
    [
        "distance(bar.f, bar.g)",
        "manhattan_distance(bar.f, 1.0)",
        "within_radius(bar.f, bar.g, 0.5)",
        "nearest(bar.f, vfs.sites)",
        "normalize(bar.f)",
    ],
)
def test_distance_functions_refuse_scalar_arguments_at_type_check(expression: str) -> None:
    ast = ExpressionParser().parse(expression)
    with pytest.raises(TypeCheckError, match="must be a vector variable"):
        TypeChecker(SCHEMA).check(ast)


def test_distance_between_scalars_points_at_abs() -> None:
    ast = ExpressionParser().parse("distance(bar.f, bar.g)")
    with pytest.raises(TypeCheckError, match=r"abs\(a - b\)"):
        TypeChecker(SCHEMA).check(ast)


def test_every_spec_carries_documentation_metadata() -> None:
    for spec in FUNCTION_SPECS.values():
        assert spec.signature.startswith(spec.name + "("), spec.name
        assert spec.summary.endswith("."), spec.name
        assert spec.returns, spec.name
