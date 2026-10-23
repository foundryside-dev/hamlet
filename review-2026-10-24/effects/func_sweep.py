"""Evaluate every FUNCTION_SPECS entry through parser -> type checker -> evaluator on a batch-3 context."""
import torch, traceback
from townlet.world.expression.functions import FUNCTION_SPECS
from townlet.world.expression.parser import ExpressionParser
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError
from townlet.world.expression.evaluator import Evaluator
from townlet.world.expression.context import ExecutionContext
from townlet.world.expression.history import TemporalHistory

print("FUNCTION_SPECS count:", len(FUNCTION_SPECS))
print(sorted(FUNCTION_SPECS))
schema = {"bar.f": "float", "bar.i": "int", "bar.b": "bool", "bar.g": "float"}
B = 3
def ctx(rich):
    bars = {"f": torch.tensor([0.1, 0.5, 0.9]), "g": torch.tensor([0.3, 0.3, 0.3]), "i": torch.tensor([1, 2, 3]), "b": torch.tensor([True, False, True])}
    c = ExecutionContext(bars=bars, vfs={}, affordances={"WORK": {"position": torch.tensor([2.0, 2.0])}}, temporal={})
    if rich:
        c.history = TemporalHistory({"bar.f": 4, "bar.b": 4, "bar.i": 4}, torch.device("cpu"))
        c.history.push("bar.f", torch.tensor([0.0, 0.0, 0.0]))
        c.history.push("bar.b", torch.tensor([False, False, False]))
        c.history.push("bar.i", torch.tensor([0, 0, 0]))
        c.agent_positions = torch.tensor([[0.0, 0.0], [1.0, 1.0], [3.0, 4.0]])
        c.affordance_positions = {"WORK": torch.tensor([2.0, 2.0])}
        c.step = 7
    return c

cases = {
 "max": "max(bar.f, bar.g)", "min": "min(bar.f, bar.g)", "abs": "abs(bar.f - 0.5)", "clamp": "clamp(bar.f, 0.2, 0.8)",
 "clamp01": "clamp01(bar.i)", "sigmoid": "sigmoid(bar.f)", "tanh": "tanh(bar.f)", "smoothstep": "smoothstep(0.0, 1.0, bar.f)",
 "mean": "mean(bar.i, bar.i)", "variance": "variance(bar.f, bar.g)", "sum": "sum(bar.i, bar.i)", "product": "product(bar.i, bar.i)",
 "normalize": "normalize(bar.f, bar.g)", "min_all": "min_all(bar.f, bar.g)", "max_all": "max_all(bar.f, bar.g)",
 "count_where": "count_where(bar.b, bar.b)", "argmin": "argmin(bar.f, bar.g)", "argmax": "argmax(bar.f, bar.g)",
 "threshold": "threshold(bar.f, 0.2, 0.8)", "all": "all(bar.b, bar.b)", "any": "any(bar.b, bar.b)",
 "where": "where(bar.b, bar.f, bar.g)", "masked_add": "masked_add(bar.f, 1.0, bar.b)", "masked_set": "masked_set(bar.f, 1.0, bar.b)",
 "gather": "gather(bar.f, bar.i - 1)", "scatter": "scatter(bar.f, bar.i - 1, bar.g)", "one_hot": "one_hot(bar.i - 1, 3)",
 "normal_dist": "normal_dist(bar.f, 0.1)", "uniform": "uniform(0.0, 1.0)", "perlin_noise": "perlin_noise(bar.f, bar.g)",
 "simplex_noise": "simplex_noise(bar.f, bar.g, 3)", "time_in_window": "time_in_window(bar.i, 1, 3)",
 "phase_sin": "phase_sin(bar.i, 24.0)", "phase_cos": "phase_cos(bar.i, 24)", "elapsed_ticks": "elapsed_ticks()",
 "lag": "lag(bar.f, 1)", "delta": "delta(bar.f)", "moving_average": "moving_average(bar.f, 2)", "ema": "ema(bar.f, 0.5)",
 "rate_of_change": "rate_of_change(bar.f, 1)", "rising_edge": "rising_edge(bar.b)", "falling_edge": "falling_edge(bar.b)",
 "distance": "distance(bar.f, bar.g)", "manhattan_distance": "manhattan_distance(bar.f, bar.g)",
 "within_radius": "within_radius(bar.f, bar.g, 0.5)", "nearest": "nearest(bar.f, bar.g)",
 "distance_to_affordance": 'distance_to_affordance("WORK")', "in_range": 'in_range("WORK", 2.0)',
 "direction_to_affordance": 'direction_to_affordance("WORK")',
}
missing = set(FUNCTION_SPECS) - set(cases)
print("uncovered specs:", missing)
parser = ExpressionParser(); tc = TypeChecker(schema)
def dtclass(t):
    if not isinstance(t, torch.Tensor): return type(t).__name__
    if t.dtype == torch.bool: return "bool"
    if t.is_floating_point(): return "float"
    return "int"
rows = []
for name in sorted(FUNCTION_SPECS):
    expr = cases[name]
    try:
        ast = parser.parse(expr); declared = tc.check(ast)
    except Exception as e:
        rows.append((name, expr, "TYPECHECK-FAIL", repr(e)[:90], "", "")); continue
    out = {}
    for rich in (False, True):
        try:
            v = Evaluator(ctx(rich)).evaluate(ast)
            out[rich] = f"{dtclass(v)} {tuple(v.shape) if isinstance(v, torch.Tensor) else ''}"
        except Exception as e:
            out[rich] = f"ERR {type(e).__name__}: {str(e)[:70]}"
    rows.append((name, expr, declared, out[False], out[True]))
for r in rows:
    print(" | ".join(str(x) for x in r))
