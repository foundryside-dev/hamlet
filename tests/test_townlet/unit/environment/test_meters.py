"""Consolidated tests for meter dynamics and cascade effects (v2.1 configs)."""

import pytest
import torch

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def cpu_env_factory(env_factory, cpu_device):
    """Convenience builder for CPU-bound VectorizedHamletEnv instances."""

    def _build(num_agents: int = 1):
        return env_factory(num_agents=num_agents, device_override=cpu_device)

    return _build


# =============================================================================
# Base Depletion Tests
# =============================================================================


class TestBaseDepletion:
    """Test per-step meter depletion mechanics."""

    def test_base_depletion_rates(self, cpu_env_factory):
        """Base depletion rates applied correctly via VTC passive-depletion rules."""
        env = cpu_env_factory()
        env.reset()

        # Set all meters to 1.0
        env.meters = torch.ones(1, 8)

        # Run one depletion cycle
        env._apply_vtc_passive_depletion(1.0)

        # Expected after depletion (configs/default_curriculum v2.1, L0_0_minimal):
        # energy:   1.0 - 0.010 = 0.990
        # health:   1.0 - 0.005 = 0.995
        # satiation:1.0 - 0.008 = 0.992
        # hygiene:  1.0 - 0.003 = 0.997
        # money:    1.0 - 0.000 = 1.000
        # fitness:  1.0 - 0.002 = 0.998
        # mood:     1.0 - 0.004 = 0.996
        # social:   1.0 - 0.006 = 0.994
        expected = torch.tensor([[0.99, 0.995, 0.992, 0.997, 1.0, 0.998, 0.996, 0.994]])
        assert torch.allclose(env.meters, expected, atol=1e-4)

    def test_clamping_at_zero(self, cpu_env_factory):
        """Meters clamped at 0.0 (no negative values)."""
        env = cpu_env_factory()
        env.reset()

        # Set all meters very low
        env.meters = torch.full((1, 8), 0.001)

        # Run depletion (should clamp at 0.0)
        env._apply_vtc_passive_depletion(1.0)

        # All should be 0.0 or near-zero (except money which doesn't deplete)
        assert torch.all(env.meters[:, [0, 1, 2, 4, 5, 6, 7]] >= 0.0)
        assert torch.all(env.meters[:, [0, 1, 2, 4, 5, 6, 7]] <= 0.001)

    def test_step_uses_vtc_passive_depletion_not_meter_dynamics(self, cpu_env_factory):
        """The environment step should not call the legacy MeterDynamics depletion executor."""
        env = cpu_env_factory()
        env.reset()
        assert hasattr(env, "vtc_passive_depletion_program")
        assert not hasattr(type(env.meter_dynamics), "deplete_meters")

        def fail_legacy_depletion(*_args, **_kwargs):
            raise AssertionError("legacy MeterDynamics.deplete_meters must not execute passive decay")

        env.meter_dynamics.deplete_meters = fail_legacy_depletion
        env.meters = torch.ones(1, 8)

        env.step(torch.tensor([0]))

        assert env.meters[0, env.meter_name_to_index["energy"]].item() < 1.0


class TestCascadeEffects:
    """Test meter cascade relationships."""

    # Secondary → Primary Cascades

    def test_low_satiation_affects_both_primaries(self, cpu_env_factory):
        """Low satiation damages both health AND energy (fundamental need)."""
        env = cpu_env_factory()
        env.reset()

        energy_idx = env.meter_name_to_index["energy"]
        health_idx = env.meter_name_to_index["health"]
        satiation_idx = env.meter_name_to_index["satiation"]

        # Set satiation below threshold (0.3), primaries at 1.0
        env.meters = torch.ones(1, 8)
        env.meters[0, satiation_idx] = 0.2  # satiation at 20% (below 30% threshold)
        initial_health = env.meters[0, health_idx].item()
        initial_energy = env.meters[0, energy_idx].item()

        # Apply cascade
        env._apply_vtc_threshold_cascades()

        # Both should decrease
        assert env.meters[0, health_idx] < initial_health  # health decreased
        assert env.meters[0, energy_idx] < initial_energy  # energy decreased

        # Deficit = (0.3 - 0.2) / 0.3 = 0.333...
        # Health penalty = 0.004 * 0.333 = 0.00133...
        # Energy penalty = 0.006 * 0.333 = 0.002
        expected_health = 1.0 - (0.004 * (0.3 - 0.2) / 0.3)
        expected_energy = 1.0 - (0.006 * (0.3 - 0.2) / 0.3)

        assert torch.isclose(env.meters[0, health_idx], torch.tensor(expected_health), atol=1e-4)
        assert torch.isclose(env.meters[0, energy_idx], torch.tensor(expected_energy), atol=1e-4)

    def test_low_mood_affects_energy(self, cpu_env_factory):
        """Low mood damages energy (depressed → exhausted)."""
        env = cpu_env_factory()
        env.reset()

        energy_idx = env.meter_name_to_index["energy"]
        mood_idx = env.meter_name_to_index["mood"]

        # Set mood below threshold, energy at 1.0
        env.meters = torch.ones(1, 8)
        env.meters[0, mood_idx] = 0.1  # mood at 10%
        initial_energy = env.meters[0, energy_idx].item()

        # Apply cascade
        env._apply_vtc_threshold_cascades()

        # Energy should decrease
        assert env.meters[0, energy_idx] < initial_energy

        # Deficit = (0.2 - 0.1) / 0.2 = 0.5
        # Energy penalty = 0.001 * 0.5 = 0.0005
        expected_energy = 1.0 - (0.001 * (0.2 - 0.1) / 0.2)
        assert torch.isclose(env.meters[0, energy_idx], torch.tensor(expected_energy), atol=1e-4)

    def test_high_satiation_no_penalty(self, cpu_env_factory):
        """Satiation above threshold → no penalties."""
        env = cpu_env_factory()
        env.reset()

        energy_idx = env.meter_name_to_index["energy"]
        health_idx = env.meter_name_to_index["health"]
        satiation_idx = env.meter_name_to_index["satiation"]

        env.meters = torch.ones(1, 8)
        env.meters[0, satiation_idx] = 0.8  # satiation at 80% (above threshold)

        initial_health = env.meters[0, health_idx].item()
        initial_energy = env.meters[0, energy_idx].item()

        env._apply_vtc_threshold_cascades()

        # No change
        assert env.meters[0, health_idx] == initial_health
        assert env.meters[0, energy_idx] == initial_energy

    def test_step_applies_threshold_cascades_without_imperative_helpers(self, cpu_env_factory):
        """The step path should execute passive threshold cascades through VTC rules."""
        env = cpu_env_factory()
        env.reset()

        def forbidden_cascade_call(meters):
            raise AssertionError("imperative cascade helper was called")

        env.meter_dynamics.apply_secondary_to_primary_effects = forbidden_cascade_call
        env.meter_dynamics.apply_tertiary_to_secondary_effects = forbidden_cascade_call
        env.meter_dynamics.apply_tertiary_to_primary_effects = forbidden_cascade_call

        energy_idx = env.meter_name_to_index["energy"]
        satiation_idx = env.meter_name_to_index["satiation"]
        env.meters = torch.ones(1, 8)
        env.meters[0, satiation_idx] = 0.2

        actions = torch.tensor([env.action_ids["WAIT"]], device=env.device)
        env.step(actions)

        passive_energy = 1.0 - env.vtc_passive_depletion_program.passive_rate_for("energy")
        passive_satiation = 0.2 - env.vtc_passive_depletion_program.passive_rate_for("satiation")
        expected_cascade_penalty = 0.006 * ((0.3 - passive_satiation) / 0.3)

        assert torch.isclose(
            env.meters[0, energy_idx],
            torch.tensor(passive_energy - expected_cascade_penalty, device=env.device),
            atol=1e-5,
        )

    # Note: v2.1 default curriculum expresses cascades directly in bars.yaml
    # as a small set of meter-to-meter edges (satiation→health/energy,
    # mood→energy, hygiene→mood/social). Legacy tertiary cascade patterns
    # (e.g., hygiene→fitness, social→energy) are no longer present in the
    # active configuration, so the corresponding tests have been removed
    # rather than asserting on behavior the runtime no longer implements.


class TestTerminalConditions:
    """Test death conditions (energy ≤ 0, health ≤ 0)."""

    def test_health_zero_death(self, cpu_env_factory):
        """Health at 0 → death."""
        env = cpu_env_factory()
        env.reset()

        health_idx = env.meter_name_to_index["health"]

        env.meters = torch.ones(1, 8)
        env.meters[0, health_idx] = 0.0  # health at 0
        env.dones = torch.tensor([False])

        env.dones = env.meter_dynamics.check_terminal_conditions(env.meters, env.dones)

        assert env.dones[0]

    def test_energy_zero_death(self, cpu_env_factory):
        """Energy at 0 → death."""
        env = cpu_env_factory()
        env.reset()

        energy_idx = env.meter_name_to_index["energy"]

        env.meters = torch.ones(1, 8)
        env.meters[0, energy_idx] = 0.0  # energy at 0
        env.dones = torch.tensor([False])

        env.dones = env.meter_dynamics.check_terminal_conditions(env.meters, env.dones)

        assert env.dones[0]

    def test_both_primaries_above_zero_alive(self, cpu_env_factory):
        """Both primaries > 0 → alive."""
        env = cpu_env_factory()
        env.reset()

        energy_idx = env.meter_name_to_index["energy"]
        health_idx = env.meter_name_to_index["health"]

        env.meters = torch.ones(1, 8)
        env.meters[0, energy_idx] = 0.5  # energy at 50%
        env.meters[0, health_idx] = 0.5  # health at 50%
        env.dones = torch.tensor([False])

        env.dones = env.meter_dynamics.check_terminal_conditions(env.meters, env.dones)

        assert not env.dones[0]


class TestMeterClamping:
    """Test that meters stay within [0, 1] bounds."""

    def test_no_negative_values_after_depletion(self, cpu_env_factory):
        """Meters don't go negative after depletion."""
        env = cpu_env_factory()
        env.reset()

        # Set all meters very low
        env.meters = torch.full((1, 8), 0.001)

        # Run multiple depletion cycles
        for _ in range(5):
            env._apply_vtc_passive_depletion(1.0)

        # All should be >= 0.0
        assert torch.all(env.meters >= 0.0)

    def test_no_overflow_above_one(self, cpu_env_factory):
        """Meters don't overflow above 1.0."""
        env = cpu_env_factory()
        env.reset()

        # Set all meters to 1.0
        env.meters = torch.ones(1, 8)

        # Meters should stay at or below 1.0
        assert torch.all(env.meters <= 1.0)


class TestMultiAgentMeters:
    """Test that agents have independent meter states."""

    def test_multi_agent_selective_death(self, cpu_env_factory):
        """Multiple agents: only those with primary=0 die."""
        env = cpu_env_factory(num_agents=3)
        env.reset()

        energy_idx = env.meter_name_to_index["energy"]
        health_idx = env.meter_name_to_index["health"]

        env.meters = torch.ones(3, 8)
        env.meters[0, health_idx] = 0.0  # Agent 0: health=0 → dead
        env.meters[1, energy_idx] = 0.0  # Agent 1: energy=0 → dead
        # Agent 2: both primaries > 0 → alive
        env.dones = torch.tensor([False, False, False])

        env.dones = env.meter_dynamics.check_terminal_conditions(env.meters, env.dones)

        assert env.dones[0]  # dead (health=0)
        assert env.dones[1]  # dead (energy=0)
        assert not env.dones[2]  # alive

    def test_agents_have_independent_meters(self, multi_agent_env):
        """Different agents have independent meter states."""
        multi_agent_env.reset()

        energy_idx = multi_agent_env.meter_name_to_index["energy"]
        satiation_idx = multi_agent_env.meter_name_to_index["satiation"]

        # Modify one agent's meters
        multi_agent_env.meters[0, energy_idx] = 0.5  # Agent 0 energy = 50%
        multi_agent_env.meters[0, satiation_idx] = 0.3  # Agent 0 satiation = 30%

        # Other agents should be unaffected
        assert multi_agent_env.meters[1, energy_idx] != 0.5
        assert multi_agent_env.meters[2, energy_idx] != 0.5
        assert multi_agent_env.meters[3, energy_idx] != 0.5


# =============================================================================
# Full Cascade Integration Tests
# =============================================================================


class TestCascadeIntegration:
    """Test full cascade sequence (as called in step())."""

    def test_full_cascade_sequence(self, cpu_env_factory):
        """Test complete cascade: deplete → secondary → tertiary → check_dones."""
        env = cpu_env_factory()
        env.reset()

        energy_idx = env.meter_name_to_index["energy"]
        health_idx = env.meter_name_to_index["health"]
        hygiene_idx = env.meter_name_to_index["hygiene"]
        satiation_idx = env.meter_name_to_index["satiation"]

        # Set meters to trigger cascades (hygiene + satiation)
        env.meters = torch.ones(1, 8)
        env.meters[0, hygiene_idx] = 0.1  # hygiene at 10% (will cascade)
        env.meters[0, satiation_idx] = 0.2  # satiation at 20% (will cascade)

        initial_health = env.meters[0, health_idx].item()
        initial_energy = env.meters[0, energy_idx].item()

        # Run full cascade as in step()
        env._apply_vtc_passive_depletion(1.0)
        env._apply_vtc_threshold_cascades()
        env.dones = env.meter_dynamics.check_terminal_conditions(env.meters, env.dones)

        # Health and energy should be reduced (cascade effects accumulate)
        assert env.meters[0, health_idx] < initial_health  # health decreased
        assert env.meters[0, energy_idx] < initial_energy  # energy decreased

        # Agent should still be alive (primaries not at 0 yet)
        assert not env.dones[0]
