"""Tests for RND intrinsic reward normalization.

This test file demonstrates that RND raw MSE values need normalization
to be comparable in magnitude to extrinsic rewards.
"""

import torch

from townlet.exploration.rnd import RNDExploration


class TestRNDNormalization:
    """Test that RND intrinsic rewards are normalized properly."""

    def test_intrinsic_rewards_are_stable_order_of_magnitude(self):
        """Test that intrinsic rewards are stable and not exploding.

        EXP-01: Updated test to verify the variance collapse fix. The fix prevents
        intrinsic rewards from exploding (10-100x) when early MSE values are small.
        Now intrinsic rewards should be stable around the actual MSE magnitude.
        """
        obs_dim = 29
        embed_dim = 128
        device = torch.device("cpu")

        rnd = RNDExploration(
            obs_dim=obs_dim,
            embed_dim=embed_dim,
            device=device,
        )

        # Generate 100 random observations
        observations = torch.randn(100, obs_dim, device=device)

        # Compute intrinsic rewards with statistics update enabled
        intrinsic_rewards = rnd.compute_intrinsic_rewards(observations, update_stats=True)

        # MSE values are typically in 0.01-0.1 range for untrained networks
        mean_intrinsic = intrinsic_rewards.mean().item()
        std_intrinsic = intrinsic_rewards.std().item()

        print("\\nNormalized MSE statistics:")
        print(f"  Mean: {mean_intrinsic:.6f}")
        print(f"  Std:  {std_intrinsic:.6f}")
        print(f"  Min:  {intrinsic_rewards.min().item():.6f}")
        print(f"  Max:  {intrinsic_rewards.max().item():.6f}")

        # EXP-01: After fix, intrinsic rewards should be stable (not exploding)
        # Typical MSE is 0.01-0.1, normalized by sqrt(1.0) ≈ same range
        # Key check: rewards are NOT artificially inflated (< 1.0)
        assert mean_intrinsic < 1.0, (
            f"Intrinsic reward ({mean_intrinsic:.6f}) is too large. "
            f"EXP-01 fix should prevent variance collapse causing reward explosion."
        )

        # Also check rewards are positive and non-zero
        assert mean_intrinsic > 0.001, (
            f"Intrinsic reward ({mean_intrinsic:.6f}) is too small. " f"RND should produce measurable novelty signal."
        )

    def test_normalized_rewards_are_stable_after_warmup(self):
        """Test that normalized intrinsic rewards remain stable after warmup.

        EXP-01: Updated test to verify stability fix. With the variance collapse fix,
        normalized rewards are stable and bounded, not necessarily unit variance.
        The key property is that rewards don't explode as the predictor learns.
        """
        obs_dim = 29
        embed_dim = 128
        device = torch.device("cpu")

        rnd = RNDExploration(
            obs_dim=obs_dim,
            embed_dim=embed_dim,
            device=device,
        )

        # Warmup: collect statistics over 1000 observations
        for _ in range(10):
            observations = torch.randn(100, obs_dim, device=device)
            _ = rnd.compute_intrinsic_rewards(observations, update_stats=True)  # Warm up statistics

            # Simulate training: update predictor
            batch = {"observations": observations}
            rnd.update(batch)

        # After warmup, compute rewards on new batch
        test_observations = torch.randn(100, obs_dim, device=device)
        normalized_rewards = rnd.compute_intrinsic_rewards(test_observations)

        mean = normalized_rewards.mean().item()
        variance = normalized_rewards.var().item()

        print("\\nNormalized reward statistics after warmup:")
        print(f"  Mean: {mean:.6f}")
        print(f"  Variance: {variance:.6f}")
        print(f"  Std: {normalized_rewards.std().item():.6f}")

        # EXP-01: After warmup + predictor learning, MSE should decrease (predictor learns)
        # Key check: rewards are stable and bounded, not exploding
        assert mean < 1.0, f"Mean reward ({mean:.6f}) should not explode"
        assert mean > 0, f"Mean reward ({mean:.6f}) should be positive"
        # Variance can be very small if predictor learns well (reduces prediction error)
        assert variance < 10.0, f"Variance ({variance:.6f}) should be bounded"

    def test_normalization_is_persistent_across_checkpoints(self):
        """Test that normalization statistics are saved/loaded correctly."""
        obs_dim = 29
        embed_dim = 128
        device = torch.device("cpu")

        # Create RND and warmup
        rnd1 = RNDExploration(obs_dim=obs_dim, embed_dim=embed_dim, device=device)

        for _ in range(5):
            observations = torch.randn(100, obs_dim, device=device)
            rnd1.compute_intrinsic_rewards(observations, update_stats=True)
            rnd1.update({"observations": observations})

        # Save checkpoint
        checkpoint = rnd1.checkpoint_state()

        # Create new RND and load checkpoint
        rnd2 = RNDExploration(obs_dim=obs_dim, embed_dim=embed_dim, device=device)
        rnd2.load_state(checkpoint)

        # Compute rewards on same observations
        test_obs = torch.randn(50, obs_dim, device=device)
        rewards1 = rnd1.compute_intrinsic_rewards(test_obs)
        rewards2 = rnd2.compute_intrinsic_rewards(test_obs)

        # Rewards should be identical (normalization stats preserved)
        # THIS ASSERTION SHOULD FAIL IF checkpoint_state/load_state don't include norm stats
        torch.testing.assert_close(rewards1, rewards2, rtol=1e-5, atol=1e-5, msg="Normalized rewards should match after checkpoint load")


class TestAdaptiveIntrinsicDoubleWeighting:
    """Test that AdaptiveIntrinsicExploration doesn't apply weight twice."""

    def test_adaptive_applies_weight_only_once(self):
        """Demonstrate double-weighting bug in AdaptiveIntrinsicExploration.

        This test SHOULD FAIL initially, showing weight is applied twice.
        After fix, weight should only be applied once (in replay buffer).
        """
        from townlet.exploration.adaptive_intrinsic import AdaptiveIntrinsicExploration

        obs_dim = 29
        embed_dim = 128
        device = torch.device("cpu")

        adaptive = AdaptiveIntrinsicExploration(
            obs_dim=obs_dim,
            embed_dim=embed_dim,
            initial_intrinsic_weight=0.7,
            device=device,
        )

        observations = torch.randn(10, obs_dim, device=device)

        # Get rewards from adaptive
        adaptive_rewards = adaptive.compute_intrinsic_rewards(observations)

        # Reset RND statistics to same state
        # EXP-01: Use initial_count=100 to match new RunningMeanStd default
        adaptive.rnd.reward_rms.mean = 0.0
        adaptive.rnd.reward_rms.var = 1.0
        adaptive.rnd.reward_rms.count = 100.0

        # Get raw RND rewards (should be same because adaptive doesn't apply weight)
        raw_rnd_rewards = adaptive.rnd.compute_intrinsic_rewards(observations)

        current_weight = adaptive.get_intrinsic_weight()
        assert current_weight == 0.7, "Weight should be 0.7"

        # BUG: Before fix, adaptive_rewards would be raw_rnd * 0.7
        # FIX: After fix, adaptive_rewards should equal raw_rnd (weight applied in replay buffer)

        # THIS ASSERTION SHOULD FAIL BEFORE FIX (showing double weighting)
        torch.testing.assert_close(
            adaptive_rewards,
            raw_rnd_rewards,
            rtol=0.1,
            atol=0.1,
            msg="Adaptive should return raw RND rewards (weight applied in replay buffer)",
        )


class TestActiveMaskValidation:
    """Test active_mask validation (EXP-09)."""

    def test_active_mask_length_mismatch_raises_error(self):
        """Test that active_mask length must match obs_dim."""
        import pytest

        with pytest.raises(ValueError, match="active_mask length.*must match obs_dim"):
            RNDExploration(
                obs_dim=29,
                active_mask=(True, False, True),  # Only 3 elements, not 29
            )

    def test_active_mask_warns_when_over_50_percent_masked(self):
        """Test that warning is raised when >50% of dimensions are masked.

        EXP-09: Masking too many dimensions may harm transfer learning by
        destroying spatial information needed for curriculum progression.
        """
        import warnings

        obs_dim = 10
        # 6 masked, 4 active = 60% masked
        mask = (True, True, True, True, False, False, False, False, False, False)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            RNDExploration(obs_dim=obs_dim, active_mask=mask)

            # Should have exactly one warning
            assert len(w) == 1
            assert "60%" in str(w[0].message)
            assert "transfer learning" in str(w[0].message)

    def test_active_mask_no_warning_under_50_percent_masked(self):
        """Test that no warning when <=50% of dimensions are masked."""
        import warnings

        obs_dim = 10
        # 5 masked, 5 active = exactly 50% masked (not >50%)
        mask = (True, True, True, True, True, False, False, False, False, False)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            RNDExploration(obs_dim=obs_dim, active_mask=mask)

            # Should have no warnings
            assert len(w) == 0

    def test_no_active_mask_no_warning(self):
        """Test that no warning when active_mask is None."""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            RNDExploration(obs_dim=29, active_mask=None)

            # Should have no warnings
            assert len(w) == 0
