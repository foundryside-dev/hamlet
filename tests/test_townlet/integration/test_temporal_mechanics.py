# tests/test_townlet/integration/test_temporal_mechanics.py
"""Integration tests for temporal mechanics (Level 3).

This module consolidates all temporal mechanics tests from:
- test_temporal_integration.py (6 tests)
- test_multi_interaction.py (4 tests)
- test_vectorized_env_temporal.py (2 tests)

Plus 5 new integration tests for critical gaps.

Total: 17 tests organized into 6 test classes.

TEST ORGANIZATION:
------------------
1. TestTimeProgression (3 tests)
   - Full 24-hour cycle wrapping
   - Time progression through 24 ticks
   - Observation dimensions with temporal features (sin/cos time + progress)

2. TestOperatingHours (3 tests)
   - Job masking after 6pm (closed hours)
   - Bar wraparound hours (6pm-4am across midnight)
   - 24-hour affordances (Bed, Hospital always available)

3. TestMultiTickInteractions (6 tests)
   - Progressive benefit accumulation (linear 75%)
   - Completion bonus (25% on final tick)
   - Multi-tick Job completion (4 ticks with money gain)
   - Money charged per tick (not on completion)
   - Interaction progress in observations (0.0-1.0)
   - Completion bonus timing (only on final tick)

4. TestEarlyExitMechanics (2 tests)
   - Early exit from interaction (keep linear benefits)
   - Early exit progress verification

5. TestMultiAgentTemporal (1 test)
   - Multi-agent independent temporal states

6. TestTemporalIntegrations (3 tests)
   - Temporal mechanics disabled fallback (legacy mode)
   - Temporal mechanics with adversarial curriculum
   - Temporal state recording (time_of_day, interaction_progress)

IMPLEMENTATION STATUS (corrected 2026-08-16, hamlet-a0832f9004):
----------------------------------------------------------------
This block previously read "ALL TESTS PASSING (17/17)". That was false, and it was
false invisibly: every test here is `slow`-marked and `pyproject.toml` puts
`-m "not slow"` in the default pytest addopts, so no gate ran them.

PASSING (7): time progression, operating hours on WORK, the always-open SLEEP
affordance, temporal observation features, and the disabled-temporal fallback.

FAILING (10), all for one reason: they were written against a pack whose
affordances were Bed / Job / Bar / Hospital, with multi-tick interactions and a
wraparound (6pm-4am) schedule. The shipped pack ships SLEEP / WORK / ENTERTAINMENT /
DOCTOR, every affordance is `interaction_type: instant`, and no schedule crosses
midnight. Both engine capabilities ARE implemented (multi_tick + duration_ticks in
affordances_v2_config.py; wraparound at world/expression/functions.py:740-743) and
these tests are their ONLY coverage, so they are being repaired against a
purpose-authored test pack rather than deleted. Do NOT re-point them at an
always-open instant affordance to make them green: that passes vacuously while
exercising none of the behaviour named in the test.

"""

from pathlib import Path

import pytest
import torch

pytestmark = pytest.mark.slow


def _interact_idx(env) -> int:
    """Resolve the INTERACT action index from the compiled action vocabulary.

    The index is NOT a constant: the vocabulary is composed from the substrate's
    movement actions plus the pack's custom actions, so it moves whenever either
    changes. These tests previously hardcoded 4, which is UP_LEFT on an 8-way
    Grid2D — the assertions were reading a diagonal move and tracking whether it
    happened to be in bounds.
    """
    return env.action_mask_builder.action_ids["INTERACT"]


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

    def test_bar_wraparound_hours(self, temporal_env):
        """Verify Bar operating hours wrap around midnight (6pm-4am).

        New test: Validates wraparound logic for late-night affordances.
        """
        env = temporal_env

        env.reset()

        # Use actual Bar position (randomized on reset)
        assert "Bar" in env.affordances, "Bar affordance not deployed in test config"
        env.positions[0] = env.affordances["Bar"]
        env.meters[0, 3] = 1.0  # $100 money

        # 8pm: Bar open (operating hours: 18-28, i.e., 6pm-4am)
        env.time_of_day = 20
        masks = env.get_action_masks()
        assert masks[0, _interact_idx(env)]  # INTERACT allowed

        # 2am: Bar still open (wraparound)
        env.time_of_day = 2
        masks = env.get_action_masks()
        assert masks[0, _interact_idx(env)]  # INTERACT allowed

        # 5am: Bar closed
        env.time_of_day = 5
        masks = env.get_action_masks()
        assert not masks[0, _interact_idx(env)]  # INTERACT blocked

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

    def test_progressive_benefit_accumulation(self, temporal_env):
        """Verify linear benefits accumulate per tick.

        Migrated from: test_multi_interaction.py::test_progressive_benefit_accumulation
        """
        env = temporal_env

        env.reset()

        # Use actual Bed position (randomized on reset)
        assert "Bed" in env.affordances, "Bed affordance not deployed in test config"
        env.meters[0, 0] = 0.3  # Start at 30% energy to avoid clamping
        env.positions[0] = env.affordances["Bed"]

        initial_energy = env.meters[0, 0].item()

        # Bed config: 5 ticks, +7.5% energy per tick (linear)
        # But also -0.5% depletion per tick
        # Net per tick: +7.0%
        # First INTERACT
        env.step(torch.tensor([4], device=env.device))

        energy_after_1 = env.meters[0, 0].item()
        # Expected: +0.075 (benefit) - 0.005 (depletion) + cascading ~= +0.070
        assert abs((energy_after_1 - initial_energy) - 0.070) < 0.01

        # Second INTERACT
        env.step(torch.tensor([4], device=env.device))

        energy_after_2 = env.meters[0, 0].item()
        assert abs((energy_after_2 - initial_energy) - 0.140) < 0.02

    def test_completion_bonus(self, temporal_env):
        """Verify 25% bonus on full completion.

        Migrated from: test_multi_interaction.py::test_completion_bonus
        """
        env = temporal_env

        env.reset()

        # Use actual Bed position (randomized on reset)
        assert "Bed" in env.affordances, "Bed affordance not deployed in test config"
        env.meters[0, 0] = 0.3  # Start at 30% energy
        env.meters[0, 6] = 0.7  # Start at 70% health (to see bonus)
        env.positions[0] = env.affordances["Bed"]

        initial_energy = env.meters[0, 0].item()
        initial_health = env.meters[0, 6].item()

        # Complete all 5 ticks
        for _ in range(5):
            env.step(torch.tensor([4], device=env.device))

        final_energy = env.meters[0, 0].item()
        final_health = env.meters[0, 6].item()

        # Total energy: 5 × 7.5% (linear) + 12.5% (completion) = 50%
        # Minus 5 × 0.5% depletion = -2.5%
        # Net: ~47.5%, but cascading effects apply
        # Check that energy increased significantly (at least 40%)
        assert (final_energy - initial_energy) > 0.40

        # Health bonus only on completion: +2%
        # (cascading effects from energy/satiation also apply)
        assert (final_health - initial_health) > 0.015

    def test_multi_tick_job_completion(self, temporal_env):
        """Verify Job completion over 4 ticks with money gain.

        Migrated from: test_temporal_integration.py::test_multi_tick_job_completion
        """
        env = temporal_env

        env.reset()

        # Use actual Job position (randomized on reset)
        assert "Job" in env.affordances, "Job affordance not deployed in test config"
        env.positions[0] = env.affordances["Job"]
        env.meters[0, 3] = 0.5  # Start with $50
        env.time_of_day = 10  # 10am (Job open 8-18)

        initial_money = env.meters[0, 3].item()

        # Complete 4 ticks of Job
        for i in range(4):
            env.step(torch.tensor([4], device=env.device))  # INTERACT
            # Progress: 1, 2, 3, then 0 (completes on 4th)
            if i < 3:
                assert env.interaction_progress[0] == (i + 1)
            else:
                assert env.interaction_progress[0] == 0  # Completed

        final_money = env.meters[0, 3].item()

        # Job pays: 4 × $5.625 (linear) + $5.625 (completion) = $28.125 total
        # Normalized: +0.28125
        assert (final_money - initial_money) > 0.25  # At least 25% gain

    def test_money_charged_per_tick(self, temporal_env):
        """Verify cost charged each tick, not on completion.

        Migrated from: test_multi_interaction.py::test_money_charged_per_tick
        """
        env = temporal_env

        env.reset()

        # Use actual Bed position (randomized on reset)
        assert "Bed" in env.affordances, "Bed affordance not deployed in test config"
        env.positions[0] = env.affordances["Bed"]
        env.meters[0, 3] = 0.50  # Start with $50

        # Bed costs $1/tick = 0.01 normalized
        env.step(torch.tensor([4], device=env.device))

        money_after_1 = env.meters[0, 3].item()
        assert abs(money_after_1 - 0.49) < 0.001  # $50 - $1 = $49

        env.step(torch.tensor([4], device=env.device))

        money_after_2 = env.meters[0, 3].item()
        assert abs(money_after_2 - 0.48) < 0.001  # $49 - $1 = $48

    def test_interaction_progress_in_observations(self, temporal_env):
        """Verify interaction progress (0.0-1.0) appears in observations.

        New test: Validates that agents can observe their own progress.
        """
        env = temporal_env

        obs = env.reset()

        # Use actual Bed position (randomized on reset)
        assert "Bed" in env.affordances, "Bed affordance not deployed in test config"
        env.positions[0] = env.affordances["Bed"]
        env.meters[0, 0] = 0.3  # Low energy

        # Initial observation: no progress (interaction_progress at -2, lifetime at -1)
        progress_feature = obs[0, -2].cpu().item()
        assert progress_feature == 0.0

        # After 1 tick: progress = 1 (raw) / 10.0 (normalization) = 0.1
        obs, _, _, _ = env.step(torch.tensor([4], device=env.device))
        progress_feature = obs[0, -2].cpu().item()
        assert progress_feature == pytest.approx(0.1, abs=0.01)

        # After 2 ticks: progress = 2 / 10.0 = 0.2
        obs, _, _, _ = env.step(torch.tensor([4], device=env.device))
        progress_feature = obs[0, -2].cpu().item()
        assert progress_feature == pytest.approx(0.2, abs=0.01)

        # After 3 ticks: progress = 3 / 10.0 = 0.3
        obs, _, _, _ = env.step(torch.tensor([4], device=env.device))
        progress_feature = obs[0, -2].cpu().item()
        assert progress_feature == pytest.approx(0.3, abs=0.01)

    def test_completion_bonus_timing(self, temporal_env):
        """Verify completion bonus applied ONLY on final tick.

        New test: Validates that completion bonus doesn't leak into linear ticks.
        """
        env = temporal_env

        env.reset()

        # Use actual Job position (randomized on reset)
        assert "Job" in env.affordances, "Job affordance not deployed in test config"
        env.positions[0] = env.affordances["Job"]
        env.meters[0, 3] = 0.5  # Start with $50
        env.time_of_day = 10  # 10am (Job open)

        # Track money after each tick
        money_values = [0.5]  # Initial

        # Job: 4 ticks, $5.625/tick (linear) + $5.625 bonus (completion)
        for i in range(4):
            env.step(torch.tensor([4], device=env.device))
            money_values.append(env.meters[0, 3].item())

        # Verify linear accumulation
        # Tick 1: $50 + $5.625 = $55.625 (normalized: 0.55625)
        assert money_values[1] == pytest.approx(0.55625, abs=0.001)

        # Tick 2: $55.625 + $5.625 = $61.25 (normalized: 0.6125)
        assert money_values[2] == pytest.approx(0.6125, abs=0.001)

        # Tick 3: $61.25 + $5.625 = $66.875 (normalized: 0.66875)
        assert money_values[3] == pytest.approx(0.66875, abs=0.001)

        # Tick 4: $66.875 + $5.625 (linear) + $5.625 (bonus) = $78.125
        # Normalized: 0.78125
        assert money_values[4] == pytest.approx(0.78125, abs=0.001)

        # Verify completion bonus magnitude
        bonus_tick_gain = money_values[4] - money_values[3]
        linear_tick_gain = money_values[1] - money_values[0]

        # Completion tick should be ~2x linear tick (linear + bonus)
        assert bonus_tick_gain > (linear_tick_gain * 1.9)


# =============================================================================
# TEST CLASS 4: EARLY EXIT MECHANICS
# =============================================================================


class TestEarlyExitMechanics:
    """Early exit from multi-tick interactions."""

    def test_early_exit_from_interaction(self, temporal_env):
        """Verify agent can exit early and keep linear benefits.

        Migrated from: test_temporal_integration.py::test_early_exit_from_interaction
        """
        env = temporal_env

        env.reset()

        # Use actual Bed position (randomized on reset)
        assert "Bed" in env.affordances, "Bed affordance not deployed in test config"
        env.meters[0, 0] = 0.3  # Low energy
        env.positions[0] = env.affordances["Bed"]

        initial_energy = env.meters[0, 0].item()

        # Do 2 ticks of Bed (requires 5 for completion)
        env.step(torch.tensor([4], device=env.device))
        env.step(torch.tensor([4], device=env.device))
        assert env.interaction_progress[0] == 2

        energy_after_2 = env.meters[0, 0].item()

        # Move away - early exit from interaction
        # Progress tracking state persists until next interaction (implicit reset)
        env.step(torch.tensor([0], device=env.device))  # UP

        # Key behavior: Energy should have increased from 2 ticks (no completion bonus)
        # Each Bed tick gives ~7% energy, so 2 ticks ≈ 14%
        assert (energy_after_2 - initial_energy) > 0.1

        # Verify no completion bonus was applied (would give extra 25%)
        # With completion bonus, gain would be ~21%, without it's ~14%
        assert (energy_after_2 - initial_energy) < 0.18

    def test_early_exit_keeps_progress(self, temporal_env):
        """Verify agent keeps linear benefits if exiting early.

        Migrated from: test_multi_interaction.py::test_early_exit_keeps_progress
        """
        env = temporal_env

        env.reset()

        # Use actual Bed position (randomized on reset)
        assert "Bed" in env.affordances, "Bed affordance not deployed in test config"
        env.meters[0, 0] = 0.3  # Start at 30% energy
        env.positions[0] = env.affordances["Bed"]

        initial_energy = env.meters[0, 0].item()

        # Do 3 ticks, then move away
        for _ in range(3):
            env.step(torch.tensor([4], device=env.device))

        energy_after_3 = env.meters[0, 0].item()

        # Move away (UP action)
        env.step(torch.tensor([0], device=env.device))

        # Energy should be at approximately 3 × 7% = 21% gain
        # (3 ticks of benefit minus depletion, no completion bonus)
        assert abs((energy_after_3 - initial_energy) - 0.21) < 0.03


# =============================================================================
# TEST CLASS 5: MULTI-AGENT TEMPORAL
# =============================================================================


class TestMultiAgentTemporal:
    """Multi-agent temporal mechanics with independent states."""

    def test_multi_agent_temporal_interactions(self, cpu_device, cpu_env_factory):
        """Verify 3 agents with independent temporal states.

        New test: Validates that each agent has independent interaction progress.
        """
        env = cpu_env_factory(config_dir=Path("configs/default_curriculum"), level_name="L3_temporal_mechanics", num_agents=3)

        env.reset()

        # Use actual affordance positions (randomized on reset)
        assert "Bed" in env.affordances, "Bed affordance not deployed in test config"
        assert "Job" in env.affordances, "Job affordance not deployed in test config"

        # Agent 0: On Bed (5 ticks), do 2 ticks
        env.positions[0] = env.affordances["Bed"]
        env.meters[0, 0] = 0.3  # Low energy

        # Agent 1: On Job (4 ticks), do 3 ticks
        env.positions[1] = env.affordances["Job"]
        env.meters[1, 3] = 0.5  # $50
        env.time_of_day = 10  # Job open

        # Agent 2: Not interacting (move to empty position)
        env.positions[2] = torch.tensor([3, 3], device=env.device)

        # Execute 3 steps
        for i in range(3):
            # Agent 0: INTERACT only first 2 ticks, then move away
            agent0_action = 4 if i < 2 else 0  # INTERACT for i=0,1, then UP
            actions = torch.tensor(
                [
                    agent0_action,  # Agent 0: INTERACT twice, then UP
                    4,  # Agent 1: INTERACT (Job) all 3 times
                    0,  # Agent 2: UP (no interaction)
                ],
                device=env.device,
            )

            obs, _, _, _ = env.step(actions)

            # Verify individual progress
            if i < 2:
                # Agent 0: Should show progress on Bed
                assert env.interaction_progress[0] == (i + 1)
                # Progress normalized by /10.0, not by tick count
                assert obs[0, -2] == pytest.approx((i + 1) / 10.0, abs=0.01)

            # Agent 1: Should show progress on Job
            assert env.interaction_progress[1] == (i + 1)
            # Progress normalized by /10.0, not by tick count
            assert obs[1, -2] == pytest.approx((i + 1) / 10.0, abs=0.01)

            # Agent 2: Should show no progress
            assert env.interaction_progress[2] == 0
            assert obs[2, -2] == 0.0

        # Final verification - agents have independent interaction states
        # Agent 0: Moved away after 2 interactions (progress behavior tested above)
        # Agent 1: Completed 3 interactions
        assert env.interaction_progress[1] == 3  # Job progress
        # Agent 2: Never interacted
        assert env.interaction_progress[2] == 0  # No progress


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
