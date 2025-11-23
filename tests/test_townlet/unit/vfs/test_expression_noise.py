import torch

from townlet.vfs.evaluator import EvaluationMode, VFSEvaluator
from townlet.vfs.profiles import CompiledGlobalProfile, CompiledVariable
from townlet.world.expression import ExpressionParser


def _profile(expr: str, name: str = "var") -> CompiledGlobalProfile:
    ast = ExpressionParser().parse(expr)
    var = CompiledVariable(
        name=name,
        type="float",
        exposed_to=("agent",),
        semantic_type="custom",
        expression=expr,
        ast=ast,
    )
    return CompiledGlobalProfile(variables=[var], dependencies={name: ()})


def test_perlin_seed_determinism():
    profile = _profile("perlin_noise(bar.x, bar.y, 42)", name="noise")
    evaluator = VFSEvaluator(mode=EvaluationMode.EAGER)
    bars = {"x": torch.tensor([0.1, 0.5]), "y": torch.tensor([0.2, 0.6])}
    out1 = evaluator.evaluate_global_profile(
        profile,
        bars,
        {},
        device=torch.device("cpu"),
        agent_positions=None,
        affordance_positions={},
    )
    out2 = evaluator.evaluate_global_profile(
        profile,
        bars,
        {},
        device=torch.device("cpu"),
        agent_positions=None,
        affordance_positions={},
    )
    assert torch.allclose(out1["noise"], out2["noise"])


def test_perlin_smoothness_neighbors_close():
    profile = _profile("perlin_noise(bar.x, bar.y, 0)", name="noise")
    evaluator = VFSEvaluator(mode=EvaluationMode.EAGER)
    base = torch.tensor([0.0, 0.0])
    delta = torch.tensor([0.05, 0.05])
    bars_a = {"x": base[:1], "y": base[:1]}
    bars_b = {"x": delta[:1], "y": delta[:1]}
    n_a = evaluator.evaluate_global_profile(
        profile,
        bars_a,
        {},
        device=torch.device("cpu"),
        agent_positions=None,
        affordance_positions={},
    )["noise"]
    n_b = evaluator.evaluate_global_profile(
        profile,
        bars_b,
        {},
        device=torch.device("cpu"),
        agent_positions=None,
        affordance_positions={},
    )["noise"]
    assert torch.abs(n_a - n_b) < 0.5


def test_simplex_aliases_perlin():
    perlin_profile = _profile("perlin_noise(bar.x, bar.y, 7)", name="p")
    simplex_profile = _profile("simplex_noise(bar.x, bar.y, 7)", name="s")
    evaluator = VFSEvaluator(mode=EvaluationMode.EAGER)
    bars = {"x": torch.tensor([0.3]), "y": torch.tensor([0.9])}
    p = evaluator.evaluate_global_profile(
        perlin_profile,
        bars,
        {},
        device=torch.device("cpu"),
        agent_positions=None,
        affordance_positions={},
    )["p"]
    s = evaluator.evaluate_global_profile(
        simplex_profile,
        bars,
        {},
        device=torch.device("cpu"),
        agent_positions=None,
        affordance_positions={},
    )["s"]
    assert torch.allclose(p, s)
