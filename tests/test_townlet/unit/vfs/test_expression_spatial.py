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


def test_distance_and_in_range_static_affordance():
    profile = _profile('distance_to_affordance("Fridge")', name="dist")
    evaluator = VFSEvaluator(mode=EvaluationMode.EAGER)

    agent_pos = torch.tensor([[0.0, 0.0], [2.0, 0.0]])
    affordances = {"Fridge": torch.tensor([1.0, 0.0])}

    res = evaluator.evaluate_global_profile(
        profile,
        bars={},
        vfs_state={},
        device=torch.device("cpu"),
        agent_positions=agent_pos,
        affordance_positions=affordances,
    )

    assert torch.allclose(res["dist"], torch.tensor([1.0, 1.0]))

    profile_range = _profile('in_range("Fridge", 1.0)', name="in_range")
    res_range = evaluator.evaluate_global_profile(
        profile_range,
        bars={},
        vfs_state={},
        device=torch.device("cpu"),
        agent_positions=agent_pos,
        affordance_positions=affordances,
    )
    assert torch.equal(res_range["in_range"], torch.tensor([True, True]))


def test_direction_and_metric_euclidean():
    profile = _profile('direction_to_affordance("Target")', name="dir")
    evaluator = VFSEvaluator(mode=EvaluationMode.EAGER)

    agent_pos = torch.tensor([[0.0, 0.0], [2.0, 0.0]])
    affordances = {"Target": torch.tensor([2.0, 0.0])}

    res = evaluator.evaluate_global_profile(
        profile,
        bars={},
        vfs_state={},
        device=torch.device("cpu"),
        agent_positions=agent_pos,
        affordance_positions=affordances,
    )

    assert torch.allclose(res["dir"], torch.tensor([[1.0, 0.0], [0.0, 0.0]]))

    profile_euclid = _profile('distance_to_affordance("Target", "euclidean")', name="dist_e")
    res_e = evaluator.evaluate_global_profile(
        profile_euclid,
        bars={},
        vfs_state={},
        device=torch.device("cpu"),
        agent_positions=agent_pos,
        affordance_positions=affordances,
    )
    assert torch.allclose(res_e["dist_e"], torch.tensor([2.0, 0.0]))


def test_empty_affordance_returns_inf_false_zero_dir():
    evaluator = VFSEvaluator(mode=EvaluationMode.EAGER)
    agent_pos = torch.tensor([[0.0, 0.0]])

    dist_profile = _profile('distance_to_affordance("None")', name="dist")
    res_d = evaluator.evaluate_global_profile(
        dist_profile,
        bars={},
        vfs_state={},
        device=torch.device("cpu"),
        agent_positions=agent_pos,
        affordance_positions={},
    )
    assert torch.isinf(res_d["dist"]).all()

    dir_profile = _profile('direction_to_affordance("None")', name="dir")
    res_dir = evaluator.evaluate_global_profile(
        dir_profile,
        bars={},
        vfs_state={},
        device=torch.device("cpu"),
        agent_positions=agent_pos,
        affordance_positions={},
    )
    assert torch.allclose(res_dir["dir"], torch.zeros_like(agent_pos))


def test_invalid_metric_raises():
    evaluator = VFSEvaluator(mode=EvaluationMode.EAGER)
    agent_pos = torch.tensor([[0.0, 0.0]])
    affordances = {"Fridge": torch.tensor([0.0, 0.0])}

    profile = _profile('distance_to_affordance("Fridge", "chebyshev")', name="dist")
    try:
        evaluator.evaluate_global_profile(
            profile,
            bars={},
            vfs_state={},
            device=torch.device("cpu"),
            agent_positions=agent_pos,
            affordance_positions=affordances,
        )
    except ValueError:
        return
    assert False, "Expected ValueError for invalid metric"
