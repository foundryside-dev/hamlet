import torch

from townlet.world.expression.ast_nodes import Constant, FunctionCall
from townlet.world.expression.evaluator import Evaluator
from townlet.world.expression.functions import FUNCTION_SPECS
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError


class DummyContext:
    device = torch.device("cpu")

    def get(self, name: str):
        raise KeyError(name)


def _eval(func: str, *consts: float | bool) -> torch.Tensor:
    args = [Constant(value=v) for v in consts]
    node = FunctionCall(function_name=func, arguments=args)
    return Evaluator(DummyContext()).evaluate(node)


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
