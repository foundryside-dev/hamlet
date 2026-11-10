"""Real composer scale controls; ENV retirement and runtime admission are separate."""

import pytest
import torch

from townlet.config.drive_as_code import (
    CompositionConfig,
    DriveAsCodeConfig,
    EfficiencyBonusConfig,
    ExtrinsicStrategyConfig,
    IntrinsicStrategyConfig,
    ModifierConfig,
    RangeConfig,
)
from townlet.environment.dac_engine import DACEngine
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.vtc import VTCRewardProgram


def _engine(base: float, modifier: float) -> DACEngine:
    device = torch.device("cpu")
    config = DriveAsCodeConfig(
        version="1.0",
        modifiers={"double": ModifierConfig(bar="energy", ranges=[RangeConfig(name="all", min=0.0, max=1.0, multiplier=modifier)])},
        extrinsic=ExtrinsicStrategyConfig(
            type="constant_base_with_shaped_bonus",
            base_reward=1.0,
            bars=[],
            bar_bonuses=[],
            variable_bonuses=[],
            apply_modifiers=[],
        ),
        intrinsic=IntrinsicStrategyConfig(strategy="rnd", base_weight=base, apply_modifiers=["double"]),
        shaping=[EfficiencyBonusConfig(type="efficiency_bonus", weight=0.1, bar="energy", threshold=0.7)],
        composition=CompositionConfig(normalize=False, clip=None, log_components=True, log_modifiers=True),
    )
    registry = VariableRegistry(variables=[], num_agents=2, device=device, items_per_world=0, item_profiles=None, num_affordances=0)
    return DACEngine(dac_config=config, vfs_registry=registry, device=device, num_agents=2, bar_index_map={"energy": 0})


def _inputs() -> dict[str, torch.Tensor]:
    return {
        "step_counts": torch.tensor([1, 1], dtype=torch.long),
        "dones": torch.tensor([False, False]),
        "meters": torch.tensor([[0.8], [0.8]], dtype=torch.float32),
        "intrinsic_raw": torch.tensor([2.0, 2.0], dtype=torch.float32),
        "runtime_intrinsic_scale": torch.tensor([0.5, 0.25], dtype=torch.float32),
    }


# Breaks caught: ignored/doubled scale, folded drive base, bypassed compiled modifier,
# or scale incorrectly applied to real extrinsic/shaping. Expectations are hand-derived.
@pytest.mark.parametrize(
    ("raw", "scale", "base", "modifier", "want_intrinsic", "want_total", "want_raw_base"),
    [
        (2.0, 0.5, 0.25, 2.0, 0.5, 1.6, 0.5),
        (2.0, 0.0, 0.25, 2.0, 0.0, 1.1, 0.5),
        (2.0, 1.0, 0.25, 2.0, 1.0, 2.1, 0.5),
        (2.0, 0.5, 0.5, 2.0, 1.0, 2.1, 1.0),
        (2.0, 0.5, 0.25, 1.0, 0.25, 1.35, 0.5),
        (1.0, 0.5, 0.25, 2.0, 0.25, 1.35, 0.25),
    ],
)
def test_real_vtc_dac_composes_independent_factors(raw, scale, base, modifier, want_intrinsic, want_total, want_raw_base):
    inputs = _inputs()
    inputs["intrinsic_raw"].fill_(raw)
    inputs["runtime_intrinsic_scale"].fill_(scale)
    total, weights, components = VTCRewardProgram().apply(reward_backend=_engine(base, modifier), reward_context={}, **inputs)

    torch.testing.assert_close(total, torch.full((2,), want_total))
    torch.testing.assert_close(weights, torch.full((2,), modifier))
    torch.testing.assert_close(components["extrinsic"], torch.ones(2))
    torch.testing.assert_close(components["shaping"], torch.full((2,), 0.1))
    torch.testing.assert_close(components["intrinsic"], torch.full((2,), want_intrinsic))
    torch.testing.assert_close(components["intrinsic_raw"], torch.full((2,), want_raw_base))
    torch.testing.assert_close(components["provider_intrinsic_raw"], torch.full((2,), raw))
    torch.testing.assert_close(components["runtime_intrinsic_scale"], torch.full((2,), scale))


# Breaks caught: using one scalar/mean scale for the population or masking provenance
# as though a DAC done flag established ENV retirement/inactive-entry behavior.
@pytest.mark.parametrize("terminal", [False, True])
def test_full_population_scale_and_terminal_diagnostics(terminal):
    inputs = _inputs()
    inputs["runtime_intrinsic_scale"] = torch.tensor([0.5, 0.0])
    inputs["dones"][1] = terminal
    total, weights, components = VTCRewardProgram().apply(reward_backend=_engine(0.25, 2.0), reward_context={}, **inputs)

    torch.testing.assert_close(total, torch.tensor([1.6, 0.0 if terminal else 1.1]))
    torch.testing.assert_close(components["intrinsic"], torch.tensor([0.5, 0.0]))
    torch.testing.assert_close(components["extrinsic"], torch.tensor([1.0, 0.0 if terminal else 1.0]))
    torch.testing.assert_close(components["shaping"], torch.tensor([0.1, 0.0 if terminal else 0.1]))
    torch.testing.assert_close(weights, torch.tensor([2.0, 2.0]))
    torch.testing.assert_close(components["intrinsic_raw"], torch.tensor([0.5, 0.5]))
    torch.testing.assert_close(components["provider_intrinsic_raw"], torch.tensor([2.0, 2.0]))
    torch.testing.assert_close(components["runtime_intrinsic_scale"], torch.tensor([0.5, 0.0]))


def test_done_masks_nonzero_intrinsic_without_erasing_diagnostics():
    inputs = _inputs()
    inputs["dones"][1] = True
    total, weights, components = VTCRewardProgram().apply(reward_backend=_engine(0.25, 2.0), reward_context={}, **inputs)

    torch.testing.assert_close(total, torch.tensor([1.6, 0.0]))
    torch.testing.assert_close(components["intrinsic"], torch.tensor([0.5, 0.0]))
    torch.testing.assert_close(components["runtime_intrinsic_scale"], torch.tensor([0.5, 0.25]))
    torch.testing.assert_close(components["provider_intrinsic_raw"], torch.tensor([2.0, 2.0]))
    torch.testing.assert_close(components["intrinsic_raw"], torch.tensor([0.5, 0.5]))
    torch.testing.assert_close(weights, torch.tensor([2.0, 2.0]))


# Break caught: restoring an implicit old-caller default instead of requiring scale.
@pytest.mark.parametrize("entry", ["vtc", "dac"])
def test_scale_is_required_at_both_composer_entries(entry):
    inputs = _inputs()
    del inputs["runtime_intrinsic_scale"]
    engine = _engine(0.25, 2.0)
    with pytest.raises(TypeError, match="runtime_intrinsic_scale"):
        if entry == "vtc":
            VTCRewardProgram().apply(reward_backend=engine, reward_context={}, **inputs)
        else:
            engine.calculate_rewards(**inputs)


# Breaks caught: broadcasting malformed scale, coercion, nonfinite/negative acceptance,
# or computing on the wrong device. Meta supplies a CPU-host-independent mismatch.
@pytest.mark.parametrize(
    ("scale", "error"),
    [
        pytest.param(0.5, TypeError, id="python-scalar"),
        pytest.param([0.5, 0.5], TypeError, id="python-list"),
        pytest.param(None, TypeError, id="none"),
        pytest.param(torch.tensor(0.5), ValueError, id="rank-zero"),
        pytest.param(torch.tensor([0.5]), ValueError, id="short"),
        pytest.param(torch.tensor([0.5, 0.5, 0.5]), ValueError, id="long"),
        pytest.param(torch.tensor([[0.5], [0.5]]), ValueError, id="rank-two"),
        pytest.param(torch.ones(2, dtype=torch.float64), TypeError, id="float64"),
        pytest.param(torch.ones(2, dtype=torch.int64), TypeError, id="integer"),
        pytest.param(torch.ones(2, dtype=torch.bool), TypeError, id="bool"),
        pytest.param(torch.tensor([float("nan"), 0.5]), ValueError, id="nan"),
        pytest.param(torch.tensor([0.5, float("inf")]), ValueError, id="positive-infinity"),
        pytest.param(torch.tensor([float("-inf"), 0.5]), ValueError, id="negative-infinity"),
        pytest.param(torch.tensor([0.5, -0.01]), ValueError, id="negative"),
        pytest.param(torch.empty(2, device="meta"), RuntimeError, id="wrong-device"),
    ],
)
def test_dac_rejects_malformed_runtime_scale(scale, error):
    inputs = _inputs()
    inputs["runtime_intrinsic_scale"] = scale
    with pytest.raises(error, match="runtime_intrinsic_scale"):
        _engine(0.25, 2.0).calculate_rewards(**inputs)


# Breaks caught: input mutation, borrowed provenance storage, or aliased diagnostics
# that let caller/observer writes change another component or the canonical reward.
@pytest.mark.parametrize("provenance", ["provider_intrinsic_raw", "runtime_intrinsic_scale"])
def test_inputs_and_provenance_components_have_owned_storage(provenance):
    inputs = _inputs()
    before = {name: value.clone() for name, value in inputs.items()}
    total, weights, components = VTCRewardProgram().apply(reward_backend=_engine(0.25, 2.0), reward_context={}, **inputs)
    outputs = {"total": total, "weights": weights, **components}
    saved = {name: value.clone() for name, value in outputs.items()}
    for name, value in inputs.items():
        torch.testing.assert_close(value, before[name])

    inputs["intrinsic_raw"].fill_(31.0)
    inputs["runtime_intrinsic_scale"].fill_(37.0)
    for name, value in outputs.items():
        torch.testing.assert_close(value, saved[name])

    components[provenance].fill_(99.0)
    torch.testing.assert_close(inputs["intrinsic_raw"], torch.full((2,), 31.0))
    torch.testing.assert_close(inputs["runtime_intrinsic_scale"], torch.full((2,), 37.0))
    for name, value in outputs.items():
        if name != provenance:
            torch.testing.assert_close(value, saved[name])


# Breaks caught: detached snapshots used in composition, in-place edits to leaves,
# scale applied twice, or terminal masking that leaks intrinsic gradients.
def test_runtime_scaling_preserves_autograd_and_terminal_mask():
    inputs = _inputs()
    inputs["intrinsic_raw"] = torch.tensor([2.0, 4.0], requires_grad=True)
    inputs["runtime_intrinsic_scale"] = torch.tensor([0.5, 0.25], requires_grad=True)
    inputs["dones"][1] = True
    total, _, components = VTCRewardProgram().apply(reward_backend=_engine(0.25, 2.0), reward_context={}, **inputs)
    total.sum().backward()

    torch.testing.assert_close(total, torch.tensor([1.6, 0.0]))
    torch.testing.assert_close(inputs["intrinsic_raw"].grad, torch.tensor([0.25, 0.0]))
    torch.testing.assert_close(inputs["runtime_intrinsic_scale"].grad, torch.tensor([1.0, 0.0]))
    torch.testing.assert_close(inputs["intrinsic_raw"], torch.tensor([2.0, 4.0]))
    torch.testing.assert_close(inputs["runtime_intrinsic_scale"], torch.tensor([0.5, 0.25]))
    assert components["provider_intrinsic_raw"].requires_grad
    assert components["runtime_intrinsic_scale"].requires_grad
