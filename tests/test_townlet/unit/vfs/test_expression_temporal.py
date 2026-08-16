import torch

from townlet.vfs.evaluator import EvaluationMode, VFSEvaluator
from townlet.vfs.history import collect_history_requirements
from townlet.vfs.profiles import CompiledGlobalProfile, CompiledVariable
from townlet.world.expression import ExpressionParser


def _profile(expr: str, name: str = "var", type_: str = "float") -> CompiledGlobalProfile:
    ast = ExpressionParser().parse(expr)
    var = CompiledVariable(
        name=name,
        type=type_,
        exposed_to=("agent",),
        expression=expr,
        ast=ast,
    )
    return CompiledGlobalProfile(variables=[var], dependencies={name: ()})


def test_delta_warm_and_delta_values():
    profile = _profile("delta(bar.energy)", name="energy_delta")
    history_spec = collect_history_requirements(profile)
    evaluator = VFSEvaluator(mode=EvaluationMode.EAGER, history_spec=history_spec)

    bars0 = {"energy": torch.tensor([1.0, 2.0])}
    res0 = evaluator.evaluate_global_profile(profile, bars0, {}, device=torch.device("cpu"), step=0)
    assert torch.allclose(res0["energy_delta"], torch.zeros_like(bars0["energy"]))

    bars1 = {"energy": torch.tensor([2.5, 1.0])}
    res1 = evaluator.evaluate_global_profile(profile, bars1, {}, device=torch.device("cpu"), step=1)
    expected = torch.tensor([1.5, -1.0])
    assert torch.allclose(res1["energy_delta"], expected)


def test_moving_average_window_and_warmup():
    profile = _profile("moving_average(bar.energy, 2)", name="energy_ma")
    history_spec = collect_history_requirements(profile)
    evaluator = VFSEvaluator(mode=EvaluationMode.EAGER, history_spec=history_spec)

    bars0 = {"energy": torch.tensor([1.0, 1.0])}
    res0 = evaluator.evaluate_global_profile(profile, bars0, {}, device=torch.device("cpu"), step=0)
    assert torch.allclose(res0["energy_ma"], torch.tensor([1.0, 1.0]))

    bars1 = {"energy": torch.tensor([3.0, 1.0])}
    res1 = evaluator.evaluate_global_profile(profile, bars1, {}, device=torch.device("cpu"), step=1)
    assert torch.allclose(res1["energy_ma"], torch.tensor([2.0, 1.0]))


def test_rate_of_change_promotes_to_float_with_int_inputs():
    profile = _profile("rate_of_change(bar.steps, 1)", name="roc")
    history_spec = collect_history_requirements(profile)
    evaluator = VFSEvaluator(mode=EvaluationMode.EAGER, history_spec=history_spec)

    bars0 = {"steps": torch.tensor([0, 10], dtype=torch.int64)}
    evaluator.evaluate_global_profile(profile, bars0, {}, device=torch.device("cpu"), step=0)

    bars1 = {"steps": torch.tensor([5, 12], dtype=torch.int64)}
    res1 = evaluator.evaluate_global_profile(profile, bars1, {}, device=torch.device("cpu"), step=1)
    assert res1["roc"].dtype == torch.float32
    assert torch.allclose(res1["roc"], torch.tensor([5.0, 2.0]))


def test_rising_edge_bool_history():
    profile = _profile("rising_edge(bar.flag)", name="flag_edge", type_="bool")
    history_spec = collect_history_requirements(profile)
    evaluator = VFSEvaluator(mode=EvaluationMode.EAGER, history_spec=history_spec)

    bars0 = {"flag": torch.tensor([False, False])}
    res0 = evaluator.evaluate_global_profile(profile, bars0, {}, device=torch.device("cpu"), step=0)
    assert torch.equal(res0["flag_edge"], torch.tensor([False, False]))

    bars1 = {"flag": torch.tensor([True, False])}
    res1 = evaluator.evaluate_global_profile(profile, bars1, {}, device=torch.device("cpu"), step=1)
    assert torch.equal(res1["flag_edge"], torch.tensor([True, False]))


def test_history_spec_collects_windows():
    profile = _profile("moving_average(bar.energy, 3) + delta(bar.energy)", name="combo")
    history_spec = collect_history_requirements(profile)
    assert history_spec["bar.energy"] == 3
