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
import math
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
import torch
import yaml
from pydantic import ValidationError

from townlet.environment.action_executor import ActionExecutor
from townlet.environment.affordance_engine import AffordanceEngine
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.compilers.observation import meter_observation_field_name
from townlet.vfs import vtc
from townlet.vfs.observation_builder import apply_normalization

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
    env.positions[:] = torch.tensor(env.affordances[affordance], device=env.device, dtype=env.positions.dtype)


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


def test_each_meter_declares_its_own_normalization_sourced_from_its_own_bounds() -> None:
    """Every meter carries its OWN spec, and the bounds half still comes from bars.yaml.

    This asserted one block spec whose `min`/`max` were parallel LISTS. Per-meter
    parameters were therefore always expressible; per-meter KIND was not, which is the
    whole of hamlet-3d3039f340. Now each meter has its own spec, and PDR-0016's coupling
    — the declaration that ceilings the runtime also scales the observation — is asserted
    meter by meter.
    """
    universe = UniverseCompiler().compile(SOURCE_PACK, primary_level=L1, use_cache=False)
    level = universe.get_level(L1)

    declared = {meter.name: meter.bounds for meter in level.bars.meters}
    specs = {f.id: f.normalization for f in universe.vfs_observation_fields}
    bars_fields = [f for f in universe.observation_spec.fields if f.semantic_type == "bars"]
    assert len(bars_fields) == len(declared), "one observation field per declared meter"

    for field in bars_fields:
        meter_name = field.feature_ref  # the compiled field NAMES its meter; nothing parses it (unit 4)
        assert meter_name is not None and field.feature == "meter"
        spec = specs[field.name]
        assert spec is not None, f"{field.name} must declare a normalization"
        assert spec.kind == "minmax", "default_curriculum declares minmax for every meter"
        # Scalars now, not list entries: the spec belongs to ONE meter.
        assert spec.min == declared[meter_name].min
        assert spec.max == declared[meter_name].max


def test_obs_meters_observation_is_scaled_by_declared_bounds(tmp_path: Path) -> None:
    """A meter's observation is its value over its DECLARED ceiling, not its raw value.

    Before this unit nothing normalized anything, so money entered the 124-dim
    observation raw while the other 123 features sat in [0, 1].
    """
    env = _env(_pack(tmp_path, L1), L1)
    money_idx = env.meter_name_to_index["money"]
    energy_idx = env.meter_name_to_index["energy"]
    money_max = next(m.bounds.max for m in env.universe.get_level(L1).bars.meters if m.name == "money")

    env.meters[:, money_idx] = 22.5
    env.meters[:, energy_idx] = 0.5

    obs = env._get_observations()[0]
    money_field = env.observation_spec.get_field_by_name(meter_observation_field_name("money"))
    energy_field = env.observation_spec.get_field_by_name(meter_observation_field_name("energy"))
    observed = {"money": obs[money_field.start_index], "energy": obs[energy_field.start_index]}

    assert observed["money"].item() == pytest.approx(22.5 / money_max, rel=1e-6)
    # A unit-interval meter is unchanged by minmax over [0, 1] — the normalization is
    # per-meter, not a single global divisor.
    assert observed["energy"].item() == pytest.approx(0.5, abs=1e-6)


def test_every_declared_normalization_reaches_the_observation(tmp_path: Path) -> None:
    """The VFS normalization ABI has production callers, for EVERY field that declares one.

    `apply_normalization` was fully implemented, tested and hashed into
    `observation_schema_hash` with ZERO production callers. This pins that every field
    declaring a spec now has it applied, so the surface cannot go inert again silently.

    Every field is first driven OFF its identity point, without which this test cannot
    cash that promise. At reset every declared spec happens to be an identity map —
    `minmax` over [0, 1] is the identity for the seven unit-interval meters, money is
    0.0, and the four environment-declared variables are permanently 0.0 because nothing
    writes them (`hamlet-dc8f887cd5`). A version of this test that observed the reset
    state passed with the whole normalization half reverted.
    """
    env = _env(_pack(tmp_path, L1), L1)

    declared = {f.id: f.normalization for f in env.universe.vfs_observation_fields if f.normalization is not None}
    money_field_name = meter_observation_field_name("money")
    assert money_field_name in declared, "every meter must be among the normalized fields"

    # Drive every normalized field off its identity point. The money meter via its value
    # (the only non-unit ceiling in any shipped pack); the rest by writing the registry
    # directly, since they have no production writer to do it for us.
    env.meters[:, env.meter_name_to_index["money"]] = 22.5
    off_identity = {money_field_name}
    for field_id, spec in declared.items():
        if field_id == money_field_name or field_id not in env.vfs_registry.variables:
            continue
        maximum = spec.max if isinstance(spec.max, float) else None
        if spec.kind != "minmax" or maximum is None or maximum == 1.0:
            continue
        current = env.vfs_registry.get(field_id, reader="engine")
        env.vfs_registry.set(field_id, torch.full_like(current, maximum / 2.0), writer="engine")
        off_identity.add(field_id)

    assert len(off_identity) >= 2, f"only {off_identity} could be driven off identity — the test would not discriminate"

    obs = env._get_observations()
    checked = 0
    for field in env.observation_spec.fields:
        normalization = declared.get(field.name)
        if normalization is None:
            continue
        raw = env.vfs_registry.get(field.name, reader="engine")
        if raw.dim() == 1:
            raw = raw.unsqueeze(1)
        expected = apply_normalization(raw, normalization)
        actual = obs[:, field.start_index : field.end_index]
        assert torch.allclose(expected, actual, atol=1e-6), f"{field.name} is not normalized as declared"
        if field.name in off_identity:
            # Vacuity guard: prove this field's spec is NOT the identity here, so the
            # assertion above actually discriminated.
            assert not torch.allclose(raw, actual, atol=1e-6), f"{field.name} normalization is an identity map — assertion was vacuous"
            checked += 1

    assert checked >= 2, f"only {checked} field(s) discriminated; this test cannot detect the surface going inert"


def test_dimension_changing_normalization_is_rejected_only_when_it_disagrees_with_dims(tmp_path: Path) -> None:
    """A widening normalizer is legal — the field must simply DECLARE the width it produces.

    This test used to read "a normalizer that changes a field's width must fail loudly",
    which conflated two things: producing a different width than the SOURCE (fine, and now
    authorable) versus producing a different width than the field DECLARES (a defect). The
    first is what `cyclical_sin_cos` and `one_hot` are for; only the second is an error.

    Both halves are pinned, because dropping the mismatch guard while making widening legal
    would let a wrong-width normalizer corrupt the observation layout silently.
    """
    from townlet.vfs.schema import NormalizationSpec

    env = _env(_pack(tmp_path, L1), L1)
    encoder = env._observation_encoder
    source = torch.zeros((env.num_agents, 1))
    widening = NormalizationSpec(kind="cyclical_sin_cos", period=24.0)

    # Declared 2, produces 2: accepted.
    widened = encoder._apply_declared_normalization("obs_meter_test", source, widening, 2)
    assert widened.shape == (env.num_agents, 2)

    # Declared 1, produces 2: still a defect, still loud.
    with pytest.raises(ValueError, match="changed an observation field's width"):
        encoder._apply_declared_normalization("obs_meter_test", source, widening, 1)


# --------------------------------------------------------------------------------------
# Per-meter normalization kinds (hamlet-3d3039f340, PDR-0054)
# --------------------------------------------------------------------------------------


def test_a_meter_can_declare_a_log_family_and_it_reaches_the_observation() -> None:
    """ACCEPTANCE LEG 2, verbatim from hamlet-3d3039f340.

    The ticket measured that `money` with bounds [1, 1e6] under a linear normalizer
    observes 0.000999 at money=1000 — the whole operating range 1..100,000 crushed into
    [0, 0.0999], leaving the agent effectively blind to money. It required that after the
    fix the compiled spec reports `log_scaled` and the observed value at money=1000 is
    0.5.

    Leg 1 (the pack compiles with zero src/ diff) is how the defect arose in the first
    place: `variables_reference.yaml` accepted exactly this declaration, validated it,
    compiled green, and discarded it. So this asserts the OBSERVED VALUE, not the schema.
    """
    pack = Path("configs/trial002_money_log_gdp")
    universe = UniverseCompiler().compile(pack, primary_level="L0_simple", use_cache=False)

    spec = next(f.normalization for f in universe.vfs_observation_fields if f.id == meter_observation_field_name("money"))
    assert spec is not None and spec.kind == "log_scaled", "money must compile to the declared log family"

    observed = {value: apply_normalization(torch.tensor([value]), spec).item() for value in (1.0, 10.0, 1000.0, 100000.0, 1000000.0)}
    assert observed[1000.0] == pytest.approx(0.5, abs=1e-6), "the ticket's headline number"
    # The rest of the ticket's table, so a partial regression cannot pass on one point.
    assert observed[1.0] == pytest.approx(0.0, abs=1e-6)
    assert observed[10.0] == pytest.approx(1.0 / 6.0, abs=1e-6)
    assert observed[100000.0] == pytest.approx(5.0 / 6.0, abs=1e-6)
    assert observed[1000000.0] == pytest.approx(1.0, abs=1e-6)

    # And the defect it replaces: linear scaling would have crushed it to ~0.001.
    assert observed[1000.0] > 100 * (1000.0 / 1000000.0)


def test_a_widening_meter_kind_grows_the_observation_by_exactly_its_extra_dims(tmp_path: Path) -> None:
    """The width couplings are genuinely broken, not merely bypassed.

    Before this cut the observed bars width was pinned to the meter COUNT in three places
    (the meter-encoder Linear, its zero fallback, and the encoder's source-shape assert),
    so a widening kind could not be used even though `apply_normalization` implemented it.
    Declaring `cyclical_sin_cos` on one meter must now widen the observation by exactly
    one dimension, end to end — compiled spec, bars group slice, and the real observation
    tensor.
    """
    baseline = UniverseCompiler().compile(SOURCE_PACK, primary_level=L1, use_cache=False)
    baseline_dims = baseline.observation_spec.total_dims
    baseline_bars = baseline.observation_activity.group_slices["bars"]

    pack = _pack(tmp_path, L1)
    env_yaml = pack / "environment.yaml"
    data = yaml.safe_load(env_yaml.read_text())
    for meter in data["environment"]["meters"]:
        if meter["name"] == "mood":
            meter["range_type"] = {"kind": "cyclical_sin_cos", "period": 24.0}
    env_yaml.write_text(yaml.safe_dump(data))

    widened = UniverseCompiler().compile(pack, primary_level=L1, use_cache=False)

    assert widened.observation_spec.total_dims == baseline_dims + 1
    bars = widened.observation_activity.group_slices["bars"]
    assert (bars.stop - bars.start) == (baseline_bars.stop - baseline_bars.start) + 1

    mood_field = widened.observation_spec.get_field_by_name(meter_observation_field_name("mood"))
    assert mood_field.dims == 2, "sin and cos"

    # The SOURCE stays one scalar — the extra dimension is produced by the normalizer at
    # observation time, not stored. Conflating these is what made the kind unreachable.
    source = next(f for f in widened.vfs_observation_fields if f.id == mood_field.name)
    assert source.shape == [1]

    # End to end: the real observation is (sin, cos) of the meter's value.
    env = _env(pack, L1)
    env.meters[:, env.meter_name_to_index["mood"]] = 6.0
    obs = env._get_observations()[0, mood_field.start_index : mood_field.end_index]
    angle = 6.0 * (2.0 * math.pi / 24.0)
    assert obs[0].item() == pytest.approx(math.sin(angle), abs=1e-5)
    assert obs[1].item() == pytest.approx(math.cos(angle), abs=1e-5)


def test_a_meter_observation_id_that_collides_is_a_compile_error(tmp_path: Path) -> None:
    """The namespacing prefix is asserted, not trusted.

    A bare meter name as a variable id is unusable twice over: the VTC merges bars and VFS
    variables into one evaluation namespace and raises at RUNTIME on the first bar write,
    and `build_vfs_variables` SKIPS a field shadowed by a declared variable, silently
    producing an observation field with no backing variable. Both are found at compile
    time, with the meter named.
    """
    pack = _pack(tmp_path, L1)
    env_yaml = pack / "environment.yaml"
    data = yaml.safe_load(env_yaml.read_text())
    data["environment"]["variables"].append(
        {
            "name": meter_observation_field_name("energy"),
            "type": "scalar",
            "dims": 1,
            "scope": "agent",
            "description": "A variable that shadows a meter's observation id",
            "semantic_type": "custom",
            "normalization": {"method": "normalize", "range": [0.0, 1.0], "clip": False},
        }
    )
    env_yaml.write_text(yaml.safe_dump(data))

    with pytest.raises(Exception, match="collides with a declared environment variable"):
        UniverseCompiler().compile(pack, primary_level=L1, use_cache=False)


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


def test_semantic_groups_must_be_contiguous() -> None:
    """group_slices is the name-blind way to address a block, and W6 sizes a network layer
    from it — so a group that spans foreign dimensions produces a wrong TENSOR SHAPE, far
    from its cause. build_activity records a group's start on first sighting and its end on
    every sighting, so interleaving was previously silent."""
    from townlet.universe.compilers.observation import ObservationCompiler
    from townlet.universe.dto import ObservationField, ObservationSpec

    def _field(name: str, start: int, semantic: str) -> ObservationField:
        return ObservationField(
            uuid=None,
            name=name,
            type="scalar",
            dims=1,
            start_index=start,
            end_index=start + 1,
            scope="agent",
            description=name,
            semantic_type=semantic,
            feature="meter" if semantic == "bars" else "variable",
            feature_ref=name if semantic == "bars" else None,
        )

    interleaved = ObservationSpec.from_fields([_field("a", 0, "bars"), _field("b", 1, "spatial"), _field("c", 2, "bars")])
    with pytest.raises(ValueError, match="not contiguous"):
        ObservationCompiler().build_activity(interleaved)

    contiguous = ObservationSpec.from_fields([_field("a", 0, "bars"), _field("c", 1, "bars"), _field("b", 2, "spatial")])
    activity = ObservationCompiler().build_activity(contiguous)
    assert activity.group_slices["bars"] == slice(0, 2)


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


def test_one_hot_over_an_unindexable_bar_range_is_a_compile_error(tmp_path: Path) -> None:
    """A one_hot meter whose bar can hold an out-of-range index must fail at COMPILE time.

    Found by review: declaring `categories: 5` on a bar bounded [1, 1e6] compiled green and
    then died on the first observation build with "one_hot normalization received category
    index outside configured range" — naming no meter, no value and no file. A bar that only
    reaches the invalid region later would have failed mid-training.
    """
    pack = _pack(tmp_path, L1)
    env_yaml = pack / "environment.yaml"
    data = yaml.safe_load(env_yaml.read_text())
    for meter in data["environment"]["meters"]:
        if meter["name"] == "money":
            meter["range_type"] = {"kind": "one_hot", "categories": 5}
    env_yaml.write_text(yaml.safe_dump(data))

    with pytest.raises(Exception, match="not a valid index range"):
        UniverseCompiler().compile(pack, primary_level=L1, use_cache=False)


def test_a_normalizer_failure_at_runtime_names_the_field(tmp_path: Path) -> None:
    """`apply_normalization` is field-agnostic, so its messages name the KIND and never the
    field. With one field per meter that leaves an author nothing to act on, so the encoder
    re-raises with the field name attached."""
    from townlet.vfs.schema import NormalizationSpec

    env = _env(_pack(tmp_path, L1), L1)
    encoder = env._observation_encoder

    with pytest.raises(ValueError, match="obs_meter_money"):
        encoder._apply_declared_normalization(
            "obs_meter_money",
            torch.full((env.num_agents, 1), 99.0),
            NormalizationSpec(kind="one_hot", categories=4),
            4,
        )
