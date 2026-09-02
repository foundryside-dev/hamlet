"""WS-1(e): declared `bars.*.bounds` drive the runtime AND the observation.

Config-in/behaviour-out pins for task 3a (`PDR-0014`, `PDR-0015`, `PDR-0016`).

Before this unit, `bars.*.bounds` was declared in every pack and read by no runtime
site: six hardcoded `[0.0, 1.0]` clamps contradicted it every tick, so L1's
`money.bounds.max: 999999.0` was crushed to `1.0` and six of seven money affordances
were permanently unaffordable. The declared VFS observation normalization was inert in
the same way — `apply_normalization` implemented the whole ABI, was hashed into
`observation_schema_hash`, and had zero production callers, while the compiled
`obs_meters` field description read "meter values (normalized)".

The two are one feature: `bounds.max` is exactly the range a `minmax` normalizer needs
(`PDR-0016`). These tests pin both halves together.

Every literal here was MEASURED, not derived. Note that passive depletion runs AFTER
the interaction within a step, so a ceiling of 0.5 with `passive: 0.01` reads back
0.490000, not 0.500000 — see `PDR-0015`/§0.2 of the plan, where three of the four
originally-specified red baselines were wrong for exactly this reason.

**Only `bounds.max` is pinned, and that is not an omission.** All 108 declared floors
across all 25 packs are `0.0` — identical to the floor the old hardcoded clamp used —
so wiring `bounds.min` and hardcoding `0.0` are numerically indistinguishable on every
shipped pack. The difference is not expressible as behaviour by any config that exists,
so there is no honest test for it. Do not read the absence of a floor test as the
wiring being half-done.
"""

from __future__ import annotations

import inspect
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
import torch
import yaml
from pydantic import ValidationError

from townlet.agent.token_input import TokenInputAssembler
from townlet.environment.action_executor import ActionExecutor
from townlet.environment.affordance_engine import AffordanceEngine
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler
from townlet.vfs import vtc

SOURCE_PACK = Path("configs/default_curriculum")
L0 = "L0_0_minimal"
L1 = "L1_full_observability"


def _pack(tmp_path: Path, level: str, mutator: Callable[[dict], None] | None = None) -> Path:
    """Copy the shipped pack into tmp_path, optionally editing one level's bars.yaml.

    Every `.compiled` artifact is removed: cache validity keys on config hash +
    provenance, and provenance uses `git rev-parse HEAD` rather than dirty state, so a
    stale artifact would be judged valid and report the OLD hash (§0.2 correction 10).
    """
    dest = tmp_path / "pack"
    shutil.copytree(SOURCE_PACK, dest)
    for compiled in dest.rglob(".compiled"):
        shutil.rmtree(compiled, ignore_errors=True)
    for artifact in dest.rglob("*.msgpack"):
        artifact.unlink()

    if mutator is not None:
        bars_path = dest / "levels" / level / "bars.yaml"
        data = yaml.safe_load(bars_path.read_text())
        mutator(data)
        bars_path.write_text(yaml.safe_dump(data, sort_keys=False))
    return dest


def _env(pack: Path, level: str, num_agents: int = 1) -> VectorizedHamletEnv:
    universe = UniverseCompiler().compile(pack, primary_level=level, use_cache=False)
    env = VectorizedHamletEnv(universe=universe, level_name=level, num_agents=num_agents, device=torch.device("cpu"))
    env.reset()
    return env


def _meter(data: dict, name: str) -> dict:
    for meter in data["bars"]["meters"]:
        if meter["name"] == name:
            return meter
    raise AssertionError(f"{name} not declared in bars.yaml")


def _action(env: VectorizedHamletEnv, name: str) -> int:
    return next(idx for idx, label in env.get_action_label_names().items() if label == name)


def _park_on(env: VectorizedHamletEnv, affordance: str) -> None:
    env.positions[:] = env.affordances[affordance].to(device=env.device, dtype=env.positions.dtype)


def _set_meter_range_type(pack: Path, meter_name: str, range_type: dict[str, object]) -> None:
    environment_path = pack / "environment.yaml"
    data = yaml.safe_load(environment_path.read_text())
    meter = next(meter for meter in data["environment"]["meters"] if meter["name"] == meter_name)
    meter["range_type"] = range_type
    environment_path.write_text(yaml.safe_dump(data, sort_keys=False))


def _expanded_meter_row(env: VectorizedHamletEnv, observation: torch.Tensor, meter_name: str) -> torch.Tensor:
    schema = env.token_spec.get_type("meter")
    layout = env.token_spec.compact_layout().get_type("meter")
    assert schema is not None and layout is not None
    binding = next(binding for binding in schema.slot_bindings if binding.filler_ref == meter_name)
    dynamic_rows = observation[:, layout.start : layout.end].view(observation.shape[0], schema.capacity, layout.compact_row_width)
    return TokenInputAssembler(env.token_spec).expand_type("meter", dynamic_rows)[0, binding.slot_index]


def _fixed_meter_feature(env: VectorizedHamletEnv, row: torch.Tensor, feature: str) -> float:
    schema = env.token_spec.get_type("meter")
    assert schema is not None
    return row[1 + schema.payload_features.index(feature)].item()


# --------------------------------------------------------------------------------------
# The bounds half
# --------------------------------------------------------------------------------------


def test_authored_bounds_max_ceilings_the_meter(tmp_path: Path) -> None:
    """A declared ceiling below 1.0 is enforced. Red before this unit: 0.990000."""

    def lower_energy_ceiling(data: dict) -> None:
        energy = _meter(data, "energy")
        # `initial` must stay inside the declared bounds or MeterConfig rejects the pack.
        energy["initial"] = 0.4
        energy["bounds"]["max"] = 0.5
        # lethal_max stays false: bounds already drive lethal terminal conditions, and
        # terminal conditions evaluate AFTER passive depletion, so a true here kills the
        # agent on the RED leg (energy 0.99 >= 0.5) and masks the assertion entirely.
        energy["bounds"]["lethal_max"] = False

    env = _env(_pack(tmp_path, L0, lower_energy_ceiling), L0)
    energy_idx = env.meter_name_to_index["energy"]

    _park_on(env, "SLEEP")
    env.step(torch.tensor([_action(env, "INTERACT")]))

    # 0.5 ceiling minus one 0.01 passive tick. NOT 0.5 — that is the value at the engine
    # boundary if you bypass env.step, which is what PDR-0014 originally specified.
    assert env.meters[0, energy_idx].item() == pytest.approx(0.49, abs=1e-6)


def test_authored_bounds_max_above_one_survives_the_passive_depletion_tick(tmp_path: Path) -> None:
    """A ceiling ABOVE 1.0 is honoured — invisible to an unwired (0.0, 1.0) clamp.

    Red before this unit: 0.990000 / 0.980000 / 0.970000.
    """

    def raise_energy_ceiling(data: dict) -> None:
        energy = _meter(data, "energy")
        energy["initial"] = 1.0
        energy["bounds"]["max"] = 2.0
        energy["bounds"]["lethal_max"] = False

    env = _env(_pack(tmp_path, L0, raise_energy_ceiling), L0)
    energy_idx = env.meter_name_to_index["energy"]

    _park_on(env, "SLEEP")
    env.step(torch.tensor([_action(env, "INTERACT")]))
    after_interact = env.meters[0, energy_idx].item()

    # SLEEP restores energy; with the ceiling raised the value must be free to exceed 1.0.
    assert after_interact > 1.0, f"ceiling of 2.0 not honoured: energy is {after_interact}"

    wait = _action(env, "WAIT")
    env.step(torch.tensor([wait]))
    env.step(torch.tensor([wait]))
    assert env.meters[0, energy_idx].item() == pytest.approx(after_interact - 0.02, abs=1e-6)


def test_threshold_cascade_respects_authored_bounds_max(tmp_path: Path) -> None:
    """The cascade compiler emits its TARGET's declared bounds.

    This is the sole regression guard for that change: no cascade in any of the 25
    shipped packs targets a non-unit meter, so the B1+B2 transition_graph_hash equals
    the B1-only hash on every real pack (§0.2 correction 4). Only a synthetic
    non-unit ceiling discriminates the two.
    """

    def raise_energy_ceiling(data: dict) -> None:
        energy = _meter(data, "energy")
        energy["initial"] = 1.0
        energy["bounds"]["max"] = 2.0
        energy["bounds"]["lethal_max"] = False

    env = _env(_pack(tmp_path, L0, raise_energy_ceiling), L0)
    energy_idx = env.meter_name_to_index["energy"]
    satiation_idx = env.meter_name_to_index["satiation"]

    # Fire the declared satiation->energy cascade (threshold 0.3, strength 0.006) with
    # energy already above the old hardcoded 1.0 ceiling.
    env.meters[0, energy_idx] = 1.8
    env.meters[0, satiation_idx] = 0.1
    env.step(torch.tensor([_action(env, "WAIT")]))

    # 1.8 - 0.01 passive - 0.004 cascade. Measured: unpatched 1.000000, B1-only 1.000000.
    assert env.meters[0, energy_idx].item() == pytest.approx(1.78584, abs=1e-5)


def test_shipped_economy_is_solvent(tmp_path: Path) -> None:
    """Stock L1, no YAML edit: money survives, and the declared economy is affordable.

    Red before this unit: money reads 1.000000 after one tick, and six of seven money
    affordances are permanently unaffordable.
    """
    env = _env(_pack(tmp_path, L1), L1)
    money_idx = env.meter_name_to_index["money"]

    env.meters[:, money_idx] = 22.5
    env.step(torch.tensor([_action(env, "WAIT")]))
    assert env.meters[0, money_idx].item() == pytest.approx(22.5, abs=1e-4)

    # The movement arm pins the ActionExecutor movement clamp, which the WAIT arm cannot
    # see: WAIT takes neither the movement nor the interaction path.
    env.meters[:, money_idx] = 22.5
    env.step(torch.tensor([_action(env, "UP")]))
    assert env.meters[0, money_idx].item() == pytest.approx(22.5, abs=1e-4)

    env.meters[:, money_idx] = 22.5
    for affordance, cost in (("EAT", 5.0), ("SHOWER", 1.0), ("LAUNDRY", 2.0), ("COOK", 3.0), ("ENTERTAINMENT", 5.0), ("DOCTOR", 20.0)):
        affordable = env.affordance_engine.can_afford(affordance, env.meters, cost_mode="instant")
        assert bool(affordable[0].item()), f"{affordance} (${cost}) unaffordable at $22.50"


def test_modulation_multiplier_clamp_is_not_a_meter_bound() -> None:
    """B3: the modulation clamp bounds a MULTIPLIER, not a meter — it stays [0, 1].

    Green on production code both before and after this unit. It exists so a later
    reader does not "harmonise" the last remaining (0.0, 1.0) literal in vtc.py onto
    the declared meter bounds.
    """
    universe = UniverseCompiler().compile(SOURCE_PACK, primary_level=L1, use_cache=False)
    level = universe.get_level(L1)
    program = vtc.compile_vtc_modulations(level.affordances.modulations)

    assert program.rules, "no modulation rules compiled — this test would be vacuous"
    for rule in program.rules:
        assert rule.clamp == (0.0, 1.0)
        assert rule.variable_id.startswith("affordance.")


def test_no_hardcoded_meter_bounds_remain() -> None:
    """The only guard against a partial fix that looks green.

    Four of the six sites could be wired while the two that actually bind are missed —
    which is what `PDR-0014`'s original site list would have done (`PDR-0015`).
    """
    for func in (
        AffordanceEngine.apply_instant_interaction,
        AffordanceEngine.apply_vtc_multi_tick_effects,
        ActionExecutor._execute_actions,
        vtc.compile_vtc_passive_depletions_with_phase_graph,
        vtc.compile_vtc_threshold_cascades_with_phase_graph,
    ):
        source = inspect.getsource(func)
        assert "0.0, 1.0" not in source, f"{func.__qualname__} still hardcodes a meter bound"


def test_meter_without_declared_bounds_is_fatal() -> None:
    """No hidden defaults: a cascade whose target declares no bounds must raise.

    Unreachable from any config pack — `validation/semantics.py` and
    `compilers/optimization.py` both reject it earlier — so this is pinned against a
    synthetic rule list rather than a pack (§0.2 correction 11).
    """
    with pytest.raises(ValueError, match="no declared bounds"):
        vtc.compile_vtc_threshold_cascades(
            [{"source": "satiation", "target": "energy", "threshold": 0.3, "strength": 0.006}],
            [{"name": "satiation", "depletion": {"passive": 0.0}, "bounds": {"min": 0.0, "max": 1.0}}],
        )


# --------------------------------------------------------------------------------------
# The normalization half (PDR-0016)
# --------------------------------------------------------------------------------------


def test_range_type_changes_the_live_meter_token_value_and_identity(tmp_path: Path) -> None:
    """Config-in/behavior-out pin for PDR-0134 and hamlet-1e335e0363.

    Before the repair both packs emitted the same bars-derived minmax value and the
    token carried no declaration identity at all.
    """
    linear_pack = _pack(tmp_path / "linear", L1)
    log_pack = _pack(tmp_path / "log", L1)
    _set_meter_range_type(linear_pack, "money", {"kind": "minmax", "clip": True})
    _set_meter_range_type(log_pack, "money", {"kind": "log_scaled", "clip": True})
    linear = _env(linear_pack, L1)
    logarithmic = _env(log_pack, L1)

    for env in (linear, logarithmic):
        env.meters[0, env.meter_name_to_index["money"]] = 1000.0

    linear_observation = linear._get_observations()
    log_observation = logarithmic._get_observations()
    linear_row = _expanded_meter_row(linear, linear_observation, "money")
    log_row = _expanded_meter_row(logarithmic, log_observation, "money")
    linear_value = _fixed_meter_feature(linear, linear_row, "value_0")
    log_value = _fixed_meter_feature(logarithmic, log_row, "value_0")

    assert linear_value == pytest.approx(1000.0 / 999999.0)
    assert log_value == pytest.approx(torch.log1p(torch.tensor(1000.0)).item() / torch.log1p(torch.tensor(999999.0)).item())
    assert log_value != pytest.approx(linear_value)
    assert linear.level.layout_hash == logarithmic.level.layout_hash
    assert linear.level.observation_schema_hash != logarithmic.level.observation_schema_hash
    assert linear.level.vfs_hash != logarithmic.level.vfs_hash
    linear_affordances = linear.token_spec.get_type("affordance")
    log_affordances = logarithmic.token_spec.get_type("affordance")
    assert linear_affordances is not None and log_affordances is not None
    assert any(
        left != right
        for left, right in zip(
            linear_affordances.slot_context_payloads,
            log_affordances.slot_context_payloads,
            strict=True,
        )
    )
    assert _fixed_meter_feature(linear, linear_row, "normalization_kind_minmax") == 1.0
    assert _fixed_meter_feature(linear, linear_row, "normalization_kind_log_scaled") == 0.0
    assert _fixed_meter_feature(logarithmic, log_row, "normalization_kind_minmax") == 0.0
    assert _fixed_meter_feature(logarithmic, log_row, "normalization_kind_log_scaled") == 1.0


# --------------------------------------------------------------------------------------
# Per-meter normalization kinds (hamlet-3d3039f340, PDR-0054)
# --------------------------------------------------------------------------------------


def test_an_underspecified_meter_type_is_a_compile_error(tmp_path: Path) -> None:
    """PDR-0052's ruling, at the meter: 'there is no such thing as unspecified here'.

    Each member of the range_type vocabulary fully determines its own required parameters,
    and omitting one fails at parse time rather than being defaulted. Pinned for the two
    shapes that matter: a member missing its parameter, and a parameter belonging to a
    DIFFERENT member.
    """
    from townlet.config.environment_config import MeterConfig

    with pytest.raises(ValidationError):
        MeterConfig(name="m", description="d", range_type={"kind": "minmax"})  # no clip
    with pytest.raises(ValidationError):
        MeterConfig(name="m", description="d", range_type={"kind": "cyclical_sin_cos"})  # no period
    with pytest.raises(ValidationError):
        MeterConfig(name="m", description="d", range_type={"kind": "minmax", "clip": True, "period": 24.0})
    with pytest.raises(ValidationError):
        MeterConfig(name="m", description="d", range_type={"kind": "normalized"})  # deleted member


def test_the_reference_config_meters_parse_against_the_current_schema() -> None:
    """`configs/reference/config-complete.yaml` calls itself the authoritative reference and
    is reachable by no gate.

    `scripts/validate_compiler_cli.py` only descends directories containing an
    `experiment.yaml`, so a loose reference YAML is never validated — and the per-meter cut
    initially left one meter on the deleted `unbounded` member because the migration matched
    a bare value and that line carried a trailing comment. An author copying the block got a
    parse error from a file whose whole job is to be copied.

    This pins the meters block specifically, not the whole file: the file is a documentation
    artifact with deliberate omissions elsewhere.
    """
    import yaml as _yaml

    from townlet.config.environment_config import MeterConfig

    reference = Path("configs/reference/config-complete.yaml")
    data = _yaml.safe_load(reference.read_text())
    meters = data["environment"]["meters"]
    assert meters, "the reference config must declare meters"

    for raw in meters:
        parsed = MeterConfig(**raw)
        assert parsed.range_type.kind, f"{parsed.name} must declare a range_type kind"


# --------------------------------------------------------------------------------------
# The clamp_and_validate phase (hamlet-f46e2b381a — the architecture half)
# --------------------------------------------------------------------------------------


def test_clamp_and_validate_carries_compiled_bounds_rules(tmp_path: Path) -> None:
    """The declared-but-empty phase is real: one bounds rule per declared meter.

    Red before this unit: `clamp_and_validate` appeared exactly once in the codebase, as
    a string in DEFAULT_TRANSITION_PHASES, with no rule family ever assigned to it.
    """
    universe = UniverseCompiler().compile(_pack(tmp_path, L1), primary_level=L1, use_cache=False)
    schedule = universe.get_level(L1).transition_schedule

    bounds_rules = {rule.variable_id: rule for rule in schedule.bounds_clamp_program.rules}
    passive_rules = {rule.variable_id: rule for rule in schedule.passive_depletion_program.rules}

    # Same source of truth: every declared meter gets a bounds rule, with the same
    # declared bounds the passive-depletion per-write clamp already carries.
    assert set(bounds_rules) == set(passive_rules)
    for name, rule in bounds_rules.items():
        assert rule.phase == "clamp_and_validate"
        assert rule.clamp == passive_rules[name].clamp

    # The bound that made this a P1: money's declared ceiling, not a hardcoded 1.0.
    assert bounds_rules["money"].clamp == (0.0, 999999.0)


def test_meter_pushed_out_of_bounds_after_cascades_is_clamped_before_terminal_reads(tmp_path: Path) -> None:
    """Closes the live hole: the effect-manager tick runs AFTER passive depletion and
    cascades, and its `bar.*` writes are raw — nothing between it and terminal
    conditions, rewards, or the observation enforced declared bounds. The
    clamp_and_validate phase runs exactly in that slot (see the step loop's
    `phases_between("apply_threshold_cascades", "evaluate_terminal_conditions")`).

    Red before this unit: the meter stays at 5.0 through the phase range.
    """
    env = _env(_pack(tmp_path, L0), L0)
    energy_idx = env.meter_name_to_index["energy"]

    # Simulate a post-cascade write (e.g. a ticking effect's `modify: bar.energy`).
    env.meters[0, energy_idx] = 5.0

    env._run_vtc_transition_phases(
        env.vtc_transition_runner.phases_between("apply_threshold_cascades", "evaluate_terminal_conditions"),
        active_mask=torch.logical_not(env.dones),
    )

    assert env.meters[0, energy_idx].item() == pytest.approx(1.0)
