import torch

from townlet.world.expression.ast_nodes import Constant, FunctionCall
from townlet.world.expression.context import ExecutionContext
from townlet.world.expression.evaluator import Evaluator
from townlet.world.expression.functions import FUNCTION_SPECS
from townlet.world.expression.parser import ExpressionParser
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError


class DummyContext:
    device = torch.device("cpu")

    def get(self, name: str):
        raise KeyError(name)


def _eval(func: str, *consts: float | bool) -> torch.Tensor:
    args = [Constant(value=v) for v in consts]
    node = FunctionCall(function_name=func, arguments=args)
    return Evaluator(DummyContext()).evaluate(node)


def _eval_expr(expr: str, vfs: dict[str, torch.Tensor], step: int | None) -> torch.Tensor:
    ast = ExpressionParser().parse(expr)
    context = ExecutionContext(
        bars={},
        vfs=vfs,
        affordances={},
        temporal={},
        device=torch.device("cpu"),
        step=step,
    )
    return Evaluator(context).evaluate(ast)


def test_numeric_functions_produce_float():
    assert torch.allclose(_eval("sigmoid", 0.0), torch.tensor(0.5))
    assert torch.allclose(_eval("tanh", 0.0), torch.tensor(0.0))
    assert torch.allclose(_eval("smoothstep", 0.0, 1.0, 0.5), torch.tensor(0.5), atol=1e-6)
    assert torch.allclose(_eval("clamp01", 2.0), torch.tensor(1.0))
    assert torch.allclose(_eval("mean", 1.0, 3.0), torch.tensor(2.0))
    assert torch.allclose(_eval("variance", 1.0, 3.0), torch.tensor(1.0))
    assert torch.allclose(_eval("sum", 1.0, 2.0, 3.0), torch.tensor(6.0))
    assert torch.allclose(_eval("product", 2.0, 3.0), torch.tensor(6.0))
    assert torch.allclose(_eval("min_all", 2.0, -1.0), torch.tensor(-1.0))
    assert torch.allclose(_eval("max_all", 2.0, -1.0), torch.tensor(2.0))


def test_normalize_and_arg_functions():
    norm = _eval("normalize", 1.0, 1.0, 2.0)
    assert torch.allclose(torch.sum(torch.abs(norm)), torch.tensor(1.0), atol=1e-6)

    assert _eval("argmin", 3.0, 1.0, 2.0).item() == 1
    assert _eval("argmax", 3.0, 1.0, 2.0).item() == 0


def test_count_where_and_threshold():
    count = _eval("count_where", True, False, True)
    assert count.item() == 2

    thr_low = _eval("threshold", 0.1, 0.15, 0.25)
    thr_high = _eval("threshold", 0.3, 0.15, 0.25)
    assert thr_low.item() is False
    assert thr_high.item() is True


def test_typechecker_unknown_function_raises():
    tc = TypeChecker(schema={"x": "float"})
    bad_call = FunctionCall(function_name="not_a_function", arguments=[Constant(value=1.0)])
    try:
        tc.visit_function_call(bad_call)
        assert False, "expected TypeCheckError"
    except TypeCheckError:
        pass


def test_typechecker_validates_signatures():
    tc = TypeChecker(schema={"x": "float", "y": "bool"})
    ok_call = FunctionCall(function_name="sigmoid", arguments=[Constant(value=1.0)])
    assert tc.visit_function_call(ok_call) == "float"

    bad = FunctionCall(function_name="count_where", arguments=[Constant(value=1.0)])
    try:
        tc.visit_function_call(bad)
        assert False, "expected TypeCheckError for non-bool arg"
    except TypeCheckError:
        pass


def test_registry_has_do_now_functions():
    expected = {
        "sigmoid",
        "tanh",
        "smoothstep",
        "clamp01",
        "mean",
        "variance",
        "sum",
        "product",
        "normalize",
        "min_all",
        "max_all",
        "count_where",
        "argmin",
        "argmax",
        "normal_dist",
        "uniform",
        "threshold",
    }
    assert expected.issubset(set(FUNCTION_SPECS.keys()))


def test_registry_has_vtc_recommended_operator_catalogue():
    expected = {
        "all",
        "any",
        "where",
        "masked_add",
        "masked_set",
        "gather",
        "scatter",
        "one_hot",
        "distance",
        "manhattan_distance",
        "within_radius",
        "nearest",
        "time_in_window",
        "phase_sin",
        "phase_cos",
        "elapsed_ticks",
    }
    assert expected.issubset(set(FUNCTION_SPECS.keys()))


def test_mask_tensor_operator_catalogue_evaluates_with_parser():
    vfs = {
        "value": torch.tensor([1.0, 2.0, 3.0]),
        "mask": torch.tensor([True, False, True]),
        "idx": torch.tensor([2, 0]),
        "base": torch.zeros(3),
        "updates": torch.tensor([9.0, 8.0]),
    }

    assert torch.allclose(_eval_expr("where(mask, value + 1.0, value - 1.0)", vfs, None), torch.tensor([2.0, 1.0, 4.0]))
    assert torch.allclose(_eval_expr("masked_add(value, 0.5, mask)", vfs, None), torch.tensor([1.5, 2.0, 3.5]))
    assert torch.allclose(_eval_expr("masked_set(value, 0.0, mask)", vfs, None), torch.tensor([0.0, 2.0, 0.0]))
    assert torch.equal(_eval_expr("all(mask, value > 0.0)", vfs, None), torch.tensor([True, False, True]))
    assert torch.equal(_eval_expr("any(mask, value < 2.0)", vfs, None), torch.tensor([True, False, True]))
    assert torch.allclose(_eval_expr("gather(value, idx)", vfs, None), torch.tensor([3.0, 1.0]))
    assert torch.allclose(_eval_expr("scatter(base, idx, updates)", vfs, None), torch.tensor([8.0, 0.0, 9.0]))
    assert torch.equal(
        _eval_expr("one_hot(idx, 3)", vfs, None),
        torch.tensor([[0.0, 0.0, 1.0], [1.0, 0.0, 0.0]]),
    )


def test_spatial_operator_catalogue_evaluates_batched_positions():
    vfs = {
        "positions": torch.tensor([[0.0, 0.0], [3.0, 4.0]]),
        "targets": torch.tensor([[0.0, 4.0], [0.0, 0.0]]),
        "candidates": torch.tensor([[0.0, 1.0], [2.0, 2.0], [10.0, 10.0]]),
    }

    assert torch.allclose(_eval_expr("distance(positions, targets)", vfs, None), torch.tensor([4.0, 5.0]))
    assert torch.allclose(_eval_expr("manhattan_distance(positions, targets)", vfs, None), torch.tensor([4.0, 7.0]))
    assert torch.equal(_eval_expr("within_radius(positions, targets, 4.5)", vfs, None), torch.tensor([True, False]))
    assert torch.equal(_eval_expr("nearest(positions, candidates)", vfs, None), torch.tensor([0, 1]))


def test_temporal_operator_catalogue_evaluates_windows_and_phases():
    vfs = {
        "time": torch.tensor([22.0, 10.0]),
        "phase": torch.tensor([6.0, 12.0]),
        "started": torch.tensor([5, 10]),
        "now": torch.tensor([8, 12]),
    }

    assert torch.equal(_eval_expr("time_in_window(time, 21, 6)", vfs, None), torch.tensor([True, False]))
    assert torch.equal(_eval_expr("time_in_window(time, 9, 17)", vfs, None), torch.tensor([False, True]))
    assert torch.allclose(_eval_expr("phase_sin(phase, 24)", vfs, None), torch.tensor([1.0, 0.0]), atol=1e-6)
    assert torch.allclose(_eval_expr("phase_cos(phase, 24)", vfs, None), torch.tensor([0.0, -1.0]), atol=1e-6)
    assert torch.equal(_eval_expr("elapsed_ticks(started)", vfs, 9), torch.tensor([4, 0]))
    assert torch.equal(_eval_expr("elapsed_ticks(started, now)", vfs, None), torch.tensor([3, 2]))


def test_typechecker_accepts_vtc_recommended_operator_signatures():
    parser = ExpressionParser()
    checker = TypeChecker(
        schema={
            "flag": "bool",
            "value": "float",
            "time": "float",
            "position": "float",
            "target": "float",
            "candidates": "float",
            "idx": "int",
        }
    )

    assert checker.check(parser.parse("where(flag, value, 0.0)")) == "float"
    assert checker.check(parser.parse("masked_add(value, 1.0, flag)")) == "float"
    assert checker.check(parser.parse("one_hot(idx, 3)")) == "float"
    assert checker.check(parser.parse("nearest(position, candidates)")) == "int"
    assert checker.check(parser.parse("time_in_window(time, 9, 17)")) == "bool"
