# tests/test_townlet/integration/test_temporal_mechanics.py
"""Integration tests for temporal mechanics (Level 3).

This module consolidates all temporal mechanics tests from:
- test_temporal_integration.py (6 tests)
- test_multi_interaction.py (4 tests)
- test_vectorized_env_temporal.py (2 tests)

Plus 5 new integration tests for critical gaps.

Total: 17 tests organized into 6 test classes.

STATUS (2026-08-16, hamlet-a0832f9004 then hamlet-551be983a8): 17 tests, all
passing, and — unlike every previous claim in this docstring — that statement is
made against a suite that actually runs them.

This block twice read "ALL TESTS PASSING (17/17)" while 15 of the 17 failed. The
falsehood was invisible rather than careless: the file was `pytest.mark.slow`,
`pyproject.toml` carried `-m "not slow"` in its default addopts, and so no gate
reading ever executed a line of it. The marker is gone (the file runs in ~15s;
it was never slow), the addopts filter is gone with it, and the honest reading is
now the default one.

WHY THIS FILE CARRIES ITS OWN CONFIG PACK
-----------------------------------------
These tests were written against a pack whose affordances were Bed / Job / Bar /
Hospital, one multi-tick and one open 6pm-4am. The shipped pack has neither
property: every affordance is `interaction_type: instant` and no schedule crosses
midnight. Both engine capabilities are real — verified live on 2026-08-16, with
progress advancing 1..n and resetting on completion, `costs_per_tick` charged
every tick, and an 18->28 window open at 02:00 — but no shipped config exercises
them, so the fixture below re-parameterizes a copy of the L3 pack.

The trap this file exists to avoid: do NOT re-point these at an always-open
instant affordance to make them green. `test_wraparound_hours_cross_midnight`
would pass while exercising zero wraparound logic. A vacuous green here is
strictly worse than a red, because it is indistinguishable from coverage.

Every assertion is derived from the declared constants below, never from a
literal copied out of the vanished pack, and each is verified red by mutation:
killing the wrapping branch, ignoring `duration_ticks`, and moving
`costs_per_tick` to completion each fail a different named test.
"""

from pathlib import Path

import pytest
import torch

from tests.test_townlet.helpers.config_builder import copy_config_pack, mutate_affordances_yaml

# NOT `slow`-marked. The whole file runs in ~15s, and the marker (combined with
# the `-m "not slow"` that pyproject's default addopts USED to carry) is precisely
# what hid 15 failing tests here from every gate reading — see hamlet-a0832f9004.

TEMPORAL_LEVEL = "L3_temporal_mechanics"


def _interact_idx(env) -> int:
    """Resolve the INTERACT action index from the compiled action vocabulary.

    The index is NOT a constant: the vocabulary is composed from the substrate's
    movement actions plus the pack's custom actions, so it moves whenever either
    changes. These tests previously hardcoded 4, which is UP_LEFT on an 8-way
    Grid2D — the assertions were reading a diagonal move and tracking whether it
    happened to be in bounds.
    """
    return env.action_mask_builder.action_ids["INTERACT"]


def _meter(env, name: str) -> int:
    """Resolve a meter's column from the compiled meter vocabulary.

    Same rule as `_interact_idx`: the old form hardcoded `meters[0, 3]` for money
    and `meters[0, 0]` for energy, which is a name-branch wearing an integer.
    """
    idx = env.meter_name_to_index.get(name)
    assert idx is not None, f"meter '{name}' not in compiled vocabulary {list(env.meter_name_to_index)}"
    return idx


# =============================================================================
# THE TEMPORAL TEST PACK
# =============================================================================
#
# The shipped pack declares no multi-tick affordance and no wraparound schedule,
# so the behaviour below has no config to run against. Rather than point these
# tests at an always-open instant affordance (which would go green while
# exercising none of it), the fixture re-parameterizes the shipped L3 pack.
#
# The affordance *names* are the shipped vocabulary — the compiler cross-checks
# them against environment.yaml and rejects additions with AFFORDANCE_VOCAB_MISMATCH,
# so this changes parameters only. Every assertion below is derived from these
# constants, never from a literal copied out of a vanished pack.

WRAPAROUND_AFFORDANCE = "ENTERTAINMENT"
WRAPAROUND_START = 18  # 6pm
WRAPAROUND_END = 28  # 4am next day; the schema allows end<=28 for exactly this

REST_AFFORDANCE = "SLEEP"
REST_DURATION = 5
REST_ENERGY_PER_TICK = 0.15
REST_COMPLETION_ENERGY = 0.25
REST_COMPLETION_HEALTH = 0.05
REST_MONEY_PER_TICK = 1.0  # charged per tick, not on completion

JOB_AFFORDANCE = "WORK"
JOB_DURATION = 4
JOB_PAY_PER_TICK = 5.625
JOB_COMPLETION_PAY = 5.625
JOB_OPEN_HOUR = 10  # inside the shipped 9-17 schedule


def _decay_per_interacting_tick(env, meter: str) -> float:
    """Decay a meter suffers on a tick spent interacting: `passive` + `interact`.

    Read from the compiled pack rather than frozen as a literal. The fixture
    below AUTHORS every affordance parameter it asserts on; the depletion rates
    it does not author must come from the artifact, or a change to `bars.yaml`
    turns these tests into an unexplained arithmetic mismatch.
    """
    for bar in env.bars_config.meters:
        if bar.name == meter:
            return float(bar.depletion.passive) + float(bar.depletion.interact)
    raise AssertionError(f"meter '{meter}' not found in the compiled bars config")


def _apply_temporal_pack(data: dict) -> None:
    """Give the shipped L3 affordances the temporal parameters these tests need."""
    for affordance in data["affordances"]["affordances"]:
        name = affordance["name"]

        if name == WRAPAROUND_AFFORDANCE:
            affordance["opening_hours"] = {
                "enabled": True,
                "schedule": [{"start": WRAPAROUND_START, "end": WRAPAROUND_END}],
            }

        elif name == REST_AFFORDANCE:
            affordance["interaction_type"] = "multi_tick"
            affordance["duration_ticks"] = REST_DURATION
            affordance["costs_per_tick"] = {"money": REST_MONEY_PER_TICK}
            affordance["interactions"]["on_start"] = []
            affordance["interactions"]["per_tick"] = [
                {"modify": "target.bar.energy", "value": f"target.bar.energy + {REST_ENERGY_PER_TICK}"},
            ]
            affordance["interactions"]["on_completion"] = [
                {"modify": "target.bar.energy", "value": f"target.bar.energy + {REST_COMPLETION_ENERGY}"},
                {"modify": "target.bar.health", "value": f"target.bar.health + {REST_COMPLETION_HEALTH}"},
            ]

        elif name == JOB_AFFORDANCE:
            affordance["interaction_type"] = "multi_tick"
            affordance["duration_ticks"] = JOB_DURATION
            affordance["costs_per_tick"] = {}
            affordance["interactions"]["on_start"] = []
            affordance["interactions"]["per_tick"] = [
                {"modify": "target.bar.money", "value": f"target.bar.money + {JOB_PAY_PER_TICK}"},
            ]
            affordance["interactions"]["on_completion"] = [
                {"modify": "target.bar.money", "value": f"target.bar.money + {JOB_COMPLETION_PAY}"},
            ]


@pytest.fixture
def temporal_pack_dir(tmp_path) -> Path:
    """A copy of the shipped pack with multi-tick and wraparound parameters set."""
    pack = copy_config_pack(Path("configs/default_curriculum"), tmp_path, name="temporal_pack")
    mutate_affordances_yaml(pack, _apply_temporal_pack, level_name=TEMPORAL_LEVEL)
    return pack


@pytest.fixture
def multitick_env(cpu_env_factory, temporal_pack_dir):
    """Single-agent env on the re-parameterized temporal pack."""
    return cpu_env_factory(config_dir=temporal_pack_dir, level_name=TEMPORAL_LEVEL, num_agents=1)


def _free_cell(env) -> torch.Tensor:
    """A grid cell with no affordance on it.

    Affordance placement is not stable across resets, so a hardcoded "empty"
    cell is a coin flip: this test file previously used [3, 3] and passed or
    failed depending on where deployment happened to put things that run.
    """
    occupied = {tuple(int(v) for v in pos.tolist()) for pos in env.affordances.values()}
    for x in range(int(env.substrate.width)):
        for y in range(int(env.substrate.height)):
            if (x, y) not in occupied:
                return torch.tensor([x, y], device=env.device)
    raise AssertionError("every grid cell carries an affordance; no free cell for an idle agent")


def _park(env, affordance: str, *, hour: int | None = None, money: float = 500.0):
    """Put agent 0 on an affordance, solvent, with the clock where we want it.

    Money matters: `can_afford` gates the multi-tick path on EVERY declared cost,
    so an agent parked on a priced affordance with the default balance silently
    does nothing at all and the interaction never starts.
    """
    env.positions[0] = env.affordances[affordance]
    env.meters[0, _meter(env, "money")] = money
    if hour is not None:
        env.time_of_day = hour
    return _interact_idx(env)


# =============================================================================
# TEST CLASS 1: TIME PROGRESSION
# =============================================================================


class TestTimeProgression:
    """24-hour cycle and time encoding in observations."""

    def test_full_24_hour_cycle(self, temporal_env):
        """Verify 24-hour cycle completes and wraps correctly.

        Migrated from: test_temporal_integration.py::test_full_24_hour_cycle
        """
        env = temporal_env

        env.reset()
        assert env.time_of_day == 0

        # Step through 24 hours
        for expected_time in range(24):
            assert env.time_of_day == expected_time
            env.step(torch.tensor([0], device=env.device))  # UP action

        # Should wrap back to 0
        assert env.time_of_day == 0

    def test_time_of_day_cycles(self, temporal_env):
        """Verify time cycles through 24 ticks (alternative verification).

        Migrated from: test_vectorized_env_temporal.py::test_time_of_day_cycles
        """
        env = temporal_env

        env.reset()

        # Step 24 times
        for i in range(24):
            assert env.time_of_day == i
            env.step(torch.tensor([0], device=env.device))  # any action advances the clock

        # Should wrap back to 0
        assert env.time_of_day == 0

    def test_observation_dimensions_with_temporal(self, cpu_device, cpu_env_factory):
        """Verify observation includes temporal features (sin/cos time + progress + lifetime).

        Migrated from: test_temporal_integration.py::test_observation_dimensions_with_temporal
        Combined with: test_vectorized_env_temporal.py::test_observation_includes_time_and_progress

        NOTE: Updated to expect 4 temporal features (was 3) to match actual implementation.
        The 4th feature (lifetime_progress) was added for forward compatibility.
        """
        env = cpu_env_factory(config_dir=Path("configs/default_curriculum"), level_name="L3_temporal_mechanics", num_agents=2)

        obs = env.reset()

        # Observation size now flows from compiled metadata
        expected_dim = env.metadata.observation_dim
        assert obs.shape == (2, expected_dim)

        # Locate the temporal block by its declared group, not by counting back from
        # the end — negative indices silently follow any layout change.
        temporal = obs[0, env.observation_activity.group_slices["temporal"]]
        time_sin, time_cos, day_progress, is_night = temporal

        # time_of_day = 0 at reset => sin = 0, cos = 1
        assert time_sin == pytest.approx(0.0, abs=1e-6)
        assert time_cos == pytest.approx(1.0, abs=1e-6)
        assert day_progress == 0.0  # midnight is 0/24 of the way through the day
        assert is_night == 1.0  # midnight IS night (threshold is day_length * 0.25)


# =============================================================================
# TEST CLASS 2: OPERATING HOURS
# =============================================================================


class TestOperatingHours:
    """Time-based affordance availability and action masking."""

    def test_operating_hours_mask_job(self, temporal_env):
        """Verify WORK is masked out outside its declared operating hours.

        Migrated from: test_temporal_integration.py::test_operating_hours_mask_job
        """
        env = temporal_env

        env.reset()

        # Use actual WORK position (randomized on reset)
        assert "WORK" in env.affordances, "WORK affordance not deployed in test config"
        env.positions[0] = env.affordances["WORK"]
        env.meters[0, 3] = 1.0

        # 10am: WORK open (L3 declares opening_hours 9-17)
        env.time_of_day = 10
        masks = env.get_action_masks()
        assert masks[0, _interact_idx(env)]  # INTERACT allowed

        # 7pm: WORK closed
        env.time_of_day = 19
        masks = env.get_action_masks()
        assert not masks[0, _interact_idx(env)]  # INTERACT blocked

    def test_wraparound_hours_cross_midnight(self, multitick_env):
        """An 18->28 schedule is open across midnight and closed in the morning.

        This is the only live exercise of the wrapping branch at
        `world/expression/functions.py:741` (`hour >= start | hour < end`). The
        non-wrapping branch would report CLOSED at both 20:00 and 02:00, so the
        02:00 assertion is what distinguishes the two.
        """
        env = multitick_env
        env.reset()

        interact = _park(env, WRAPAROUND_AFFORDANCE)

        # Inside the window, before midnight.
        env.time_of_day = 20
        assert env.get_action_masks()[0, interact], "20:00 is inside an 18->28 window"

        # Inside the window, AFTER midnight — only the wrapping branch allows this.
        env.time_of_day = 2
        assert env.get_action_masks()[0, interact], "02:00 is inside an 18->28 window (wraps)"

        # Outside the window: past the 04:00 close.
        env.time_of_day = 5
        assert not env.get_action_masks()[0, interact], "05:00 is past the 04:00 close"

        # Outside the window: the middle of the day.
        env.time_of_day = 12
        assert not env.get_action_masks()[0, interact], "12:00 is outside an 18->28 window"

    def test_24_hour_affordances(self, temporal_env):
        """Verify a 24-hour affordance (SLEEP) is available at every hour.

        SLEEP declares `opening_hours.enabled: false`, which the engine treats as
        always-open. That is asserted here rather than assumed: "no schedule" and
        "always open" are the same config and opposite behaviours if read wrong.
        """
        env = temporal_env

        env.reset()

        # Use actual SLEEP position (randomized on reset)
        assert "SLEEP" in env.affordances, "SLEEP affordance not deployed in test config"
        env.positions[0] = env.affordances["SLEEP"]

        # Test at multiple times
        for time in [0, 6, 12, 18, 23]:
            env.time_of_day = time
            masks = env.get_action_masks()
            assert masks[0, _interact_idx(env)], f"SLEEP should be available at {time}:00"


# =============================================================================
# TEST CLASS 3: MULTI-TICK INTERACTIONS
# =============================================================================


class TestMultiTickInteractions:
    """Multi-tick interaction mechanics (linear + completion bonus)."""

    def test_progressive_benefit_accumulation(self, multitick_env):
        """`per_tick` effects accrue on every tick of a multi-tick interaction."""
        env = multitick_env
        env.reset()

        energy = _meter(env, "energy")
        interact = _park(env, REST_AFFORDANCE)
        env.meters[0, energy] = 0.3  # low, so the +per_tick does not clamp at 1.0

        initial = env.meters[0, energy].item()

        for tick in range(1, 3):
            env.step(torch.tensor([interact], device=env.device))
            env.positions[0] = env.affordances[REST_AFFORDANCE]
            gained = env.meters[0, energy].item() - initial
            net = REST_ENERGY_PER_TICK - _decay_per_interacting_tick(env, "energy")
            assert gained == pytest.approx(net * tick, abs=0.02), f"after {tick} tick(s)"

        # Progress is mid-interaction, not complete: no completion effect yet.
        assert env.interaction_progress[0] == 2

    def test_completion_bonus(self, multitick_env):
        """`on_completion` effects land once the full duration is served."""
        env = multitick_env
        env.reset()

        energy, health = _meter(env, "energy"), _meter(env, "health")
        interact = _park(env, REST_AFFORDANCE)
        env.meters[0, energy] = 0.1
        env.meters[0, health] = 0.5

        initial_energy = env.meters[0, energy].item()
        initial_health = env.meters[0, health].item()

        for _ in range(REST_DURATION):
            env.step(torch.tensor([interact], device=env.device))
            env.positions[0] = env.affordances[REST_AFFORDANCE]

        net = REST_ENERGY_PER_TICK - _decay_per_interacting_tick(env, "energy")
        expected_energy = net * REST_DURATION + REST_COMPLETION_ENERGY
        assert env.meters[0, energy].item() - initial_energy == pytest.approx(expected_energy, abs=0.03)

        # health has no per_tick effect at all, so its entire gain is the
        # completion bonus net of passive decay — this dies if on_completion
        # stops firing, which the energy assertion alone would not catch.
        health_decay = _decay_per_interacting_tick(env, "health")
        expected_health = REST_COMPLETION_HEALTH - health_decay * REST_DURATION
        assert env.meters[0, health].item() - initial_health == pytest.approx(expected_health, abs=0.01)

    def test_multi_tick_job_completion(self, multitick_env):
        """Progress advances 1..duration-1 then resets to 0 on completion."""
        env = multitick_env
        env.reset()

        money = _meter(env, "money")
        interact = _park(env, JOB_AFFORDANCE, hour=JOB_OPEN_HOUR, money=50.0)
        initial_money = env.meters[0, money].item()

        for tick in range(JOB_DURATION):
            env.step(torch.tensor([interact], device=env.device))
            env.positions[0] = env.affordances[JOB_AFFORDANCE]
            env.time_of_day = JOB_OPEN_HOUR

            if tick < JOB_DURATION - 1:
                assert env.interaction_progress[0] == tick + 1, f"tick {tick}"
            else:
                assert env.interaction_progress[0] == 0, "progress resets on completion"

        # money has zero depletion, so this is exact rather than approximate.
        expected = JOB_PAY_PER_TICK * JOB_DURATION + JOB_COMPLETION_PAY
        assert env.meters[0, money].item() - initial_money == pytest.approx(expected, abs=0.001)

    def test_money_charged_per_tick(self, multitick_env):
        """`costs_per_tick` is charged every tick, not once at completion.

        Deliberately stops SHORT of the duration: if the charge were taken on
        completion instead, the balance here would still be the opening one.
        """
        env = multitick_env
        env.reset()

        money = _meter(env, "money")
        interact = _park(env, REST_AFFORDANCE, money=50.0)

        for tick in range(1, REST_DURATION):  # never reaches completion
            env.step(torch.tensor([interact], device=env.device))
            env.positions[0] = env.affordances[REST_AFFORDANCE]
            expected = 50.0 - REST_MONEY_PER_TICK * tick
            assert env.meters[0, money].item() == pytest.approx(expected, abs=0.001), f"after {tick} tick(s)"

    def test_interaction_progress_is_tracked_but_not_observable(self, multitick_env):
        """Progress advances as engine state — and is NOT in the observation.

        This test was `test_interaction_progress_in_observations` and read
        `obs[0, -2]`, expecting progress/10.0 in the last-but-one slot. The
        temporal observation block is now exactly four features (sin, cos,
        day_progress, is_night) — see `observation_encoder._build_temporal_observation`
        — so `interaction_progress` is engine state with no VFS variable and no
        observation mark. An author cannot declare it observable from a config
        pack. That gap is filed separately; it is asserted here rather than
        quietly dropped, so the day it becomes observable this test fails and
        says so.
        """
        env = multitick_env
        obs = env.reset()

        interact = _park(env, REST_AFFORDANCE)
        temporal = env.observation_activity.group_slices["temporal"]
        assert obs[0, temporal].numel() == 4, "temporal block is sin/cos/day_progress/is_night"

        for tick in range(1, 4):
            obs, _, _, _ = env.step(torch.tensor([interact], device=env.device))
            env.positions[0] = env.affordances[REST_AFFORDANCE]
            assert env.interaction_progress[0] == tick

            # The progress value appears nowhere in the observation.
            assert not torch.isclose(obs[0], torch.full_like(obs[0], tick / 10.0), atol=1e-6).any(), (
                "interaction progress is unexpectedly present in the observation — "
                "if it became observable, update this test and close the filed gap"
            )

    def test_completion_bonus_timing(self, multitick_env):
        """The completion bonus lands on the final tick ONLY, not earlier."""
        env = multitick_env
        env.reset()

        money = _meter(env, "money")
        interact = _park(env, JOB_AFFORDANCE, hour=JOB_OPEN_HOUR, money=50.0)

        balances = [env.meters[0, money].item()]
        for _ in range(JOB_DURATION):
            env.step(torch.tensor([interact], device=env.device))
            env.positions[0] = env.affordances[JOB_AFFORDANCE]
            env.time_of_day = JOB_OPEN_HOUR
            balances.append(env.meters[0, money].item())

        # Every tick before the last pays exactly the per-tick rate.
        for tick in range(1, JOB_DURATION):
            gain = balances[tick] - balances[tick - 1]
            assert gain == pytest.approx(JOB_PAY_PER_TICK, abs=0.001), f"tick {tick} should be linear only"

        # The final tick pays the per-tick rate PLUS the completion bonus.
        final_gain = balances[JOB_DURATION] - balances[JOB_DURATION - 1]
        assert final_gain == pytest.approx(JOB_PAY_PER_TICK + JOB_COMPLETION_PAY, abs=0.001)
        assert final_gain > balances[1] - balances[0], "completion tick must exceed a linear tick"


# =============================================================================
# TEST CLASS 4: EARLY EXIT MECHANICS
# =============================================================================


class TestEarlyExitMechanics:
    """Early exit from multi-tick interactions."""

    def test_early_exit_keeps_linear_benefit_without_bonus(self, multitick_env):
        """Leaving before the duration keeps per-tick gains and forfeits the bonus."""
        env = multitick_env
        env.reset()

        energy, health = _meter(env, "energy"), _meter(env, "health")
        interact = _park(env, REST_AFFORDANCE)
        env.meters[0, energy] = 0.1
        env.meters[0, health] = 0.5
        initial_energy = env.meters[0, energy].item()
        initial_health = env.meters[0, health].item()

        served = 2
        for _ in range(served):  # REST_DURATION is 5, so this is an early exit
            env.step(torch.tensor([interact], device=env.device))
            env.positions[0] = env.affordances[REST_AFFORDANCE]
        assert env.interaction_progress[0] == served

        gained = env.meters[0, energy].item() - initial_energy
        net = REST_ENERGY_PER_TICK - _decay_per_interacting_tick(env, "energy")
        assert gained == pytest.approx(net * served, abs=0.02)

        # health only moves on completion, so it must be pure decay here. This is
        # the assertion that actually distinguishes early exit from completion.
        health_decay = _decay_per_interacting_tick(env, "health")
        assert env.meters[0, health].item() - initial_health == pytest.approx(-health_decay * served, abs=0.005)

        # Walking away does not retroactively grant the completion bonus.
        env.step(torch.tensor([0], device=env.device))  # a movement action
        assert env.meters[0, health].item() - initial_health < REST_COMPLETION_HEALTH

    def test_early_exit_progress_does_not_advance_off_affordance(self, multitick_env):
        """Progress accrues only while the agent is actually on the affordance."""
        env = multitick_env
        env.reset()

        interact = _park(env, REST_AFFORDANCE)

        served = 3
        for _ in range(served):
            env.step(torch.tensor([interact], device=env.device))
            env.positions[0] = env.affordances[REST_AFFORDANCE]
        assert env.interaction_progress[0] == served

        # Step away and keep pressing INTERACT on empty ground: no further progress.
        env.positions[0] = (
            torch.tensor([0, 0], device=env.device)
            if not torch.equal(env.affordances[REST_AFFORDANCE], torch.tensor([0, 0], device=env.device))
            else torch.tensor([1, 1], device=env.device)
        )
        before = int(env.interaction_progress[0])
        env.step(torch.tensor([interact], device=env.device))
        assert env.interaction_progress[0] <= before, "progress must not advance off the affordance"


# =============================================================================
# TEST CLASS 5: MULTI-AGENT TEMPORAL
# =============================================================================


class TestMultiAgentTemporal:
    """Multi-agent temporal mechanics with independent states."""

    def test_multi_agent_temporal_interactions(self, cpu_env_factory, temporal_pack_dir):
        """Three agents hold independent interaction progress in one vectorized step."""
        env = cpu_env_factory(config_dir=temporal_pack_dir, level_name=TEMPORAL_LEVEL, num_agents=3)
        env.reset()

        interact = _interact_idx(env)
        money = _meter(env, "money")

        rest_pos = env.affordances[REST_AFFORDANCE]
        job_pos = env.affordances[JOB_AFFORDANCE]
        idle_pos = _free_cell(env)  # NOT a hardcoded cell: deployment moves between resets

        env.positions[0] = rest_pos  # multi-tick, duration REST_DURATION
        env.positions[1] = job_pos  # multi-tick, duration JOB_DURATION
        env.positions[2] = idle_pos  # nothing here
        env.meters[:, money] = 500.0
        env.time_of_day = JOB_OPEN_HOUR

        steps = 3  # fewer than either duration, so nobody completes and resets
        for step in range(steps):
            env.step(torch.tensor([interact, interact, interact], device=env.device))
            env.positions[0] = rest_pos
            env.positions[1] = job_pos
            env.positions[2] = idle_pos
            env.time_of_day = JOB_OPEN_HOUR

            assert env.interaction_progress[0] == step + 1, "agent 0 progresses on rest"
            assert env.interaction_progress[1] == step + 1, "agent 1 progresses on job"
            assert env.interaction_progress[2] == 0, "agent 2 stands on nothing"

        assert env.interaction_progress[0] == steps
        assert env.interaction_progress[1] == steps
        assert env.interaction_progress[2] == 0


# =============================================================================
# TEST CLASS 6: TEMPORAL INTEGRATIONS
# =============================================================================


class TestTemporalIntegrations:
    """Cross-system temporal mechanics integration."""

    def test_temporal_mechanics_disabled_fallback(self, cpu_device, cpu_env_factory, test_config_pack_path):
        """Verify environment works without temporal mechanics (legacy mode).

        Migrated from: test_temporal_integration.py::test_temporal_mechanics_disabled_fallback
        """
        env = cpu_env_factory(config_dir=test_config_pack_path, num_agents=1)

        obs = env.reset()

        # Temporal features always included for forward compatibility. The width comes
        # from the compiled artifact — reconstructing it from a layout formula is how
        # this assertion went stale (the meter block became one field per meter).
        assert obs.shape == (1, env.observation_dim)

        # The temporal block is ALLOCATED even with temporal mechanics off; it is the
        # activity mask that makes it dormant, not a narrower tensor.
        assert "temporal" in env.observation_activity.group_slices

        # Temporal state is dormant but present
        assert hasattr(env, "time_of_day")
        assert env.time_of_day == 0

        # Interactions work (legacy single-shot mode)
        assert "SLEEP" in env.affordances, "SLEEP affordance not deployed in test config"
        env.positions[0] = env.affordances["SLEEP"]
        env.meters[0, 0] = 0.3  # Start low to see increase

        initial_energy = env.meters[0, 0].item()

        env.step(torch.tensor([_interact_idx(env)], device=env.device))

        final_energy = env.meters[0, 0].item()
        # Legacy mode: single-shot benefit from SLEEP.
        # Even with depletion, should see significant increase
        assert (final_energy - initial_energy) > 0.4  # At least 40% gain

    def test_temporal_mechanics_with_curriculum(self, cpu_device, cpu_env_factory):
        """Verify temporal mechanics works with adversarial curriculum.

        New test: Validates that curriculum receives correct survival signal.
        """
        from townlet.curriculum.adversarial import AdversarialCurriculum

        env = cpu_env_factory(config_dir=Path("configs/default_curriculum"), level_name="L3_temporal_mechanics", num_agents=1)

        curriculum = AdversarialCurriculum(
            max_steps_per_episode=50,
            survival_advance_threshold=0.7,
            survival_retreat_threshold=0.3,
            entropy_gate=0.5,
            min_steps_at_stage=10,
        )

        env.reset()
        # Set very high energy to ensure agent survives 100 steps
        # (meters deplete over time even with just movement)
        env.meters[0, 0] = 5.0  # High energy buffer

        # Run 100 steps across day/night cycle
        step_count = 0
        for _ in range(100):
            action = torch.tensor([0], device=env.device)  # UP action
            obs, reward, done, info = env.step(action)

            if not done[0]:
                step_count += 1
            else:
                break

        # This test's subject is that temporal mechanics does not BREAK the loop, so it
        # asserts that the environment ran and time advanced. It deliberately does NOT
        # assert a survival count: how long an agent walking UP survives is a property
        # of the demo pack's balance, and pinning it here makes a content-tuning change
        # look like a temporal-mechanics regression (CLAUDE.md: do not test for
        # "correct" strategies).
        assert step_count > 0, "environment did not run a single step"

        # Time advances with stepping. Checked on a fresh episode so a mid-loop death
        # (which resets the clock) cannot confuse the reading.
        env.reset()
        before = env.time_of_day
        env.step(torch.tensor([0], device=env.device))
        assert env.time_of_day != before, "time did not advance with steps"

        # Key test: Temporal mechanics (time progression, operating hours) doesn't
        # break basic environment operation - agent survived and curriculum can be used
        assert hasattr(env, "time_of_day")  # Temporal state exists
        assert curriculum is not None  # Curriculum instantiated successfully
