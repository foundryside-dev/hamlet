"""Declared costs — all of them — gate the live interaction.

WS-1(d). Before the fix the executor read a single hardcoded ``money`` meter index
via ``get_affordance_cost()``, so an affordance declaring an ``energy`` or ``mood``
cost was affordable to an agent who could not pay it. Everything but money was
declared, validated, documented, and ignored at runtime.

Two further defects fell out of the same code path:

* ``get_affordance_cost()``'s docstring promised a *"Normalized cost [0, 1] where
  1.0 = $100"* and in fact returned the raw declared amount.
* ``apply_instant_interaction`` had ``check_affordability: bool = False`` — the
  safe behaviour was opt-in, and every production caller left it off.

Affordability is now a precondition: the executor gates on ``can_afford`` and the
engine *raises* rather than silently narrowing the mask. Narrowing would let the
caller record a completed interaction the engine had declined.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import torch
import yaml

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/default_curriculum")
LEVEL = "L0_0_minimal"


def _pack(tmp_path: Path, name: str, *, sleep_energy_cost: float | None = None) -> Path:
    target = tmp_path / name
    shutil.copytree(PACK, target)
    shutil.rmtree(target / ".compiled", ignore_errors=True)

    if sleep_energy_cost is not None:
        path = target / "levels" / LEVEL / "affordances.yaml"
        doc = yaml.safe_load(path.read_text())
        entries = doc["affordances"]["affordances"]
        sleep = next(a for a in entries if a["name"] == "SLEEP")
        sleep["costs"] = {"energy": sleep_energy_cost}
        path.write_text(yaml.safe_dump(doc, sort_keys=False))

    return target


def _env(pack: Path, num_agents: int = 2) -> VectorizedHamletEnv:
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    env = VectorizedHamletEnv(universe=universe, level_name=LEVEL, num_agents=num_agents, device=torch.device("cpu"))
    env.reset()
    return env


def _park_everyone_on(env: VectorizedHamletEnv, affordance: str) -> None:
    position = env.affordances[affordance]
    for agent in range(env.num_agents):
        env.positions[agent] = position.clone().to(env.positions.dtype)


def _interact_action_id(env: VectorizedHamletEnv) -> int:
    labels = env.get_action_label_names()
    return next(idx for idx, name in labels.items() if name == "INTERACT")


def _seed_all_meters(env: VectorizedHamletEnv, value: float) -> None:
    """Seed EVERY meter, deliberately.

    Load-bearing, and previously unstated in the plan: under the pack's shipped
    ``initial: 1.0`` the variant gate sees ``0.95 >= 0.9`` on the first step, the
    interaction completes, and the discriminating assertion below fails at step 1
    for the wrong reason.
    """
    env.meters[:, :] = value


@pytest.mark.parametrize(
    ("sleep_energy_cost", "expect_interaction"),
    [(0.0, True), (0.9, False)],
)
def test_declared_non_money_costs_gate_the_live_interaction(tmp_path: Path, sleep_energy_cost: float, expect_interaction: bool) -> None:
    """One YAML value decides whether the interaction happens at all.

    ``SLEEP.costs`` moves from ``{energy: 0.0}`` to ``{energy: 0.9}``. Nothing else
    differs. Before the fix both arms behave identically, because the gate only ever
    consulted ``money`` and SLEEP declares no money cost.

    ``successful_interactions == {}`` is the discriminating assertion: a fix that
    only narrows the mask *inside* the engine still records the interaction.
    """
    pack = _pack(tmp_path, f"sleep{sleep_energy_cost}", sleep_energy_cost=sleep_energy_cost)
    env = _env(pack)
    _seed_all_meters(env, 0.5)
    _park_everyone_on(env, "SLEEP")

    actions = torch.full((env.num_agents,), _interact_action_id(env), dtype=torch.long)
    _, _, _, info = env.step(actions)

    recorded = info["successful_interactions"]
    if expect_interaction:
        assert recorded, "baseline arm: SLEEP costs nothing, so the interaction must complete"
    else:
        assert recorded == {}, (
            f"variant arm: SLEEP declares energy 0.9 and every agent holds 0.5, so no interaction "
            f"should be recorded — got {recorded}. A fix that narrows the mask inside the engine "
            "but leaves the executor's bookkeeping alone produces exactly this failure."
        )


def test_engine_exposes_no_optin_affordability_guard() -> None:
    """Structural pin: the opt-in guard and the money-only helpers are gone.

    ``current_tick``'s missing default is the ONLY thing standing between a dropped
    keyword and a silent regression — it seeds the effect command RNG and anchors
    the scheduler, so defaulting it to 0 changes behaviour without raising.
    """
    import inspect

    from townlet.environment.affordance_engine import AffordanceEngine

    assert not hasattr(
        AffordanceEngine, "apply_interaction"
    ), "apply_interaction was the weaker duplicate path; it must be deleted, not aliased"
    assert not hasattr(
        AffordanceEngine, "get_affordance_cost"
    ), "get_affordance_cost returned only the money component, and lied about normalizing it"
    assert not hasattr(AffordanceEngine, "_check_affordability"), "the private helper is now the public can_afford"
    assert hasattr(AffordanceEngine, "can_afford")

    signature = inspect.signature(AffordanceEngine.apply_instant_interaction)
    assert "check_affordability" not in signature.parameters, "affordability is a precondition, never an option"
    assert (
        signature.parameters["current_tick"].default is inspect.Parameter.empty
    ), "current_tick must have NO default — a silent 0 breaks the effect RNG seed and the scheduler anchor"


def test_engine_refuses_agents_that_cannot_pay(tmp_path: Path) -> None:
    """The engine asserts the precondition rather than trusting the caller."""
    pack = _pack(tmp_path, "refuse", sleep_energy_cost=0.9)
    env = _env(pack)
    _seed_all_meters(env, 0.5)

    with pytest.raises(ValueError, match="cannot pay"):
        env.affordance_engine.apply_instant_interaction(
            meters=env.meters,
            affordance_name="SLEEP",
            agent_mask=torch.ones(env.num_agents, dtype=torch.bool),
            current_tick=0,
        )


def test_multi_tick_without_temporal_mechanics_is_rejected_at_compile_time(tmp_path: Path) -> None:
    """A multi-tick interaction with no tick schedule can never complete.

    Config error, so the compiler refuses it rather than leaving a runtime puzzle.
    """
    pack = _pack(tmp_path, "multitick")
    path = pack / "levels" / LEVEL / "affordances.yaml"
    doc = yaml.safe_load(path.read_text())
    sleep = next(a for a in doc["affordances"]["affordances"] if a["name"] == "SLEEP")
    sleep["interaction_type"] = "multi_tick"
    sleep["duration_ticks"] = 3
    path.write_text(yaml.safe_dump(doc, sort_keys=False))

    with pytest.raises(Exception, match="MULTI_TICK_REQUIRES_TEMPORAL|multi_tick"):
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def test_instant_interaction_type_compiles_without_temporal_mechanics(tmp_path: Path) -> None:
    """Sibling control: only multi-tick interactions require temporal mechanics."""
    pack = _pack(tmp_path, "instant")
    path = pack / "levels" / LEVEL / "affordances.yaml"
    doc = yaml.safe_load(path.read_text())
    sleep = next(a for a in doc["affordances"]["affordances"] if a["name"] == "SLEEP")
    sleep["interaction_type"] = "instant"
    sleep.pop("duration_ticks", None)
    path.write_text(yaml.safe_dump(doc, sort_keys=False))

    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    assert universe.metadata.primary_level == LEVEL
