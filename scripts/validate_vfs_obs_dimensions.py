#!/usr/bin/env python3
"""Validate obs_dim calculations for Items & VFS Profiles (Phase 1 limits).

This script validates that Phase 1 design decisions result in acceptable
obs_dim growth across all curriculum levels.

Purpose:
- Prove Phase 1 limits (max 20 global, 20 agent, 3 items × 5 profiles) are safe
- Calculate worst-case obs_dim for each curriculum level
- Validate against network architecture constraints (MLP input size)
- Generate report for team presentation

Usage:
    python scripts/validate_vfs_obs_dimensions.py

Expected Output:
    ✓ All curriculum levels within safe obs_dim range (<200 dims)
    ✓ Phase 1 limits prevent obs_dim explosion
    ✓ Checkpoint transfer remains viable
"""

from dataclasses import dataclass


@dataclass
class VFSProfileLimits:
    """Phase 1 VFS profile limits (from design decisions)."""

    max_global_profiles: int = 20
    max_agent_profiles: int = 20
    max_item_profiles: int = 5  # Per item type
    max_items_per_agent: int = 3


@dataclass
class ObsDimBreakdown:
    """Observation dimension breakdown."""

    # Baseline (no VFS/Items)
    baseline_dims: int

    # VFS contributions
    global_vfs_dims: int
    agent_vfs_dims: int
    item_vfs_dims: int
    total_vfs_dims: int

    # Final total
    total_dims: int

    # Metadata
    level_name: str

    def __str__(self) -> str:
        """Human-readable breakdown."""
        return f"""
Level: {self.level_name}
  Baseline (no VFS/Items):     {self.baseline_dims:3d} dims

  VFS Additions:
    Global VFS:                +{self.global_vfs_dims:3d} dims
    Agent VFS:                 +{self.agent_vfs_dims:3d} dims
    Item VFS (3 slots):        +{self.item_vfs_dims:3d} dims
    ─────────────────────────────────────
    Total VFS contribution:    +{self.total_vfs_dims:3d} dims

  Final obs_dim:                {self.total_dims:3d} dims
  Growth: {self.total_dims - self.baseline_dims:+3d} dims ({(self.total_dims / self.baseline_dims - 1) * 100:+.1f}%)
"""


# Current curriculum level obs_dims (Phase 0 baseline - NO VFS/Items)
# Source: vfs-integration-guide.md and test validation
BASELINE_OBS_DIMS = {
    "L0_0_minimal": 38,
    "L0_5_dual_resource": 78,
    "L1_full_observability": 93,
    "L2_partial_observability": 54,  # POMDP with local window
    "L3_temporal_mechanics": 93,
}


def calculate_vfs_dims(
    num_global_profiles: int,
    num_agent_profiles: int,
    num_item_profiles: int,
    max_items_per_agent: int,
) -> tuple[int, int, int, int]:
    """Calculate VFS contribution to obs_dim.

    Args:
        num_global_profiles: Number of global VFS profiles
        num_agent_profiles: Number of agent VFS profiles
        num_item_profiles: Number of item VFS profiles (per item type)
        max_items_per_agent: Number of item slots per agent

    Returns:
        (global_dims, agent_dims, item_dims, total_vfs_dims)

    Phase 1 Assumptions:
    - All VFS profiles are scalar (1 dim each)
    - Item profiles replicated across ALL item slots (fixed layout)
    - Empty slots masked with 0.0 (not removed from obs)
    """
    # Phase 1: All profiles are scalar
    global_dims = num_global_profiles * 1
    agent_dims = num_agent_profiles * 1

    # Item VFS: ALL item profiles appear in EACH slot
    # (Even if different item types have different profiles,
    #  we reserve space for union of all profiles per slot)
    item_dims = num_item_profiles * max_items_per_agent

    total_vfs_dims = global_dims + agent_dims + item_dims

    return global_dims, agent_dims, item_dims, total_vfs_dims


def calculate_obs_dim_with_vfs(
    level_name: str,
    baseline_dim: int,
    num_global_profiles: int,
    num_agent_profiles: int,
    num_item_profiles: int,
    max_items_per_agent: int,
) -> ObsDimBreakdown:
    """Calculate total obs_dim with VFS profiles and items."""
    global_dims, agent_dims, item_dims, total_vfs_dims = calculate_vfs_dims(
        num_global_profiles,
        num_agent_profiles,
        num_item_profiles,
        max_items_per_agent,
    )

    total_dims = baseline_dim + total_vfs_dims

    return ObsDimBreakdown(
        baseline_dims=baseline_dim,
        global_vfs_dims=global_dims,
        agent_vfs_dims=agent_dims,
        item_vfs_dims=item_dims,
        total_vfs_dims=total_vfs_dims,
        total_dims=total_dims,
        level_name=level_name,
    )


def validate_phase1_worst_case():
    """Validate worst-case scenario with Phase 1 limits."""
    print("=" * 70)
    print("PHASE 1 WORST-CASE ANALYSIS")
    print("=" * 70)

    limits = VFSProfileLimits()

    print("\nPhase 1 Limits (from design decisions):")
    print(f"  max_global_profiles:     {limits.max_global_profiles}")
    print(f"  max_agent_profiles:      {limits.max_agent_profiles}")
    print(f"  max_item_profiles:       {limits.max_item_profiles} (per item type)")
    print(f"  max_items_per_agent:     {limits.max_items_per_agent}")

    print("\nWorst-case VFS contribution:")
    g, a, i, total = calculate_vfs_dims(
        limits.max_global_profiles,
        limits.max_agent_profiles,
        limits.max_item_profiles,
        limits.max_items_per_agent,
    )
    print(f"  Global VFS:   {g:3d} dims  ({limits.max_global_profiles} profiles × 1 dim)")
    print(f"  Agent VFS:    {a:3d} dims  ({limits.max_agent_profiles} profiles × 1 dim)")
    print(f"  Item VFS:     {i:3d} dims  ({limits.max_item_profiles} profiles × {limits.max_items_per_agent} slots)")
    print("  ─────────────────────────")
    print(f"  Total:        {total:3d} dims")

    print("\n" + "=" * 70)
    print("CURRICULUM LEVEL IMPACT (Worst-Case)")
    print("=" * 70)

    results = []
    for level_name, baseline_dim in BASELINE_OBS_DIMS.items():
        breakdown = calculate_obs_dim_with_vfs(
            level_name,
            baseline_dim,
            limits.max_global_profiles,
            limits.max_agent_profiles,
            limits.max_item_profiles,
            limits.max_items_per_agent,
        )
        results.append(breakdown)
        print(breakdown)

    # Validation checks
    print("=" * 70)
    print("VALIDATION CHECKS")
    print("=" * 70)

    max_safe_obs_dim = 200  # MLP architecture constraint

    all_safe = True
    for breakdown in results:
        if breakdown.total_dims > max_safe_obs_dim:
            print(f"❌ {breakdown.level_name}: {breakdown.total_dims} dims > {max_safe_obs_dim} (TOO LARGE)")
            all_safe = False
        else:
            print(f"✓ {breakdown.level_name}: {breakdown.total_dims} dims < {max_safe_obs_dim} (SAFE)")

    if all_safe:
        print("\n✓ ALL LEVELS SAFE: Phase 1 limits prevent obs_dim explosion")
    else:
        print("\n❌ SOME LEVELS UNSAFE: Reduce Phase 1 limits")

    return all_safe


def validate_realistic_scenario():
    """Validate realistic scenario (not worst-case)."""
    print("\n" + "=" * 70)
    print("REALISTIC SCENARIO ANALYSIS")
    print("=" * 70)

    # Realistic: 5 global, 5 agent, 2 item profiles
    print("\nRealistic VFS usage:")
    print("  global_profiles:         5  (e.g., is_night, ambient_noise, weather)")
    print("  agent_profiles:          5  (e.g., is_tired, is_hungry, stress_level)")
    print("  item_profiles:           2  (e.g., durability, uses_remaining)")
    print("  max_items_per_agent:     3")

    g, a, i, total = calculate_vfs_dims(5, 5, 2, 3)
    print("\nRealistic VFS contribution:")
    print(f"  Global VFS:   {g:3d} dims")
    print(f"  Agent VFS:    {a:3d} dims")
    print(f"  Item VFS:     {i:3d} dims")
    print("  ─────────────────────────")
    print(f"  Total:        {total:3d} dims")

    print("\n" + "=" * 70)
    print("CURRICULUM LEVEL IMPACT (Realistic)")
    print("=" * 70)

    for level_name, baseline_dim in BASELINE_OBS_DIMS.items():
        breakdown = calculate_obs_dim_with_vfs(level_name, baseline_dim, 5, 5, 2, 3)
        growth_pct = (breakdown.total_dims / breakdown.baseline_dims - 1) * 100
        print(f"{level_name:25s}: {baseline_dim:3d} → {breakdown.total_dims:3d} (+{breakdown.total_vfs_dims:2d}, +{growth_pct:.1f}%)")


def validate_minimal_scenario():
    """Validate minimal items-only scenario (no VFS profiles)."""
    print("\n" + "=" * 70)
    print("MINIMAL SCENARIO (Items Only, No VFS Profiles)")
    print("=" * 70)

    # Items only: 0 global, 0 agent, 2 item profiles
    print("\nMinimal configuration:")
    print("  global_profiles:         0")
    print("  agent_profiles:          0")
    print("  item_profiles:           2  (durability, uses)")
    print("  max_items_per_agent:     3")

    g, a, i, total = calculate_vfs_dims(0, 0, 2, 3)
    print("\nMinimal VFS contribution:")
    print(f"  Global VFS:   {g:3d} dims")
    print(f"  Agent VFS:    {a:3d} dims")
    print(f"  Item VFS:     {i:3d} dims")
    print("  ─────────────────────────")
    print(f"  Total:        {total:3d} dims")

    print("\n" + "=" * 70)
    print("CURRICULUM LEVEL IMPACT (Minimal)")
    print("=" * 70)

    for level_name, baseline_dim in BASELINE_OBS_DIMS.items():
        breakdown = calculate_obs_dim_with_vfs(level_name, baseline_dim, 0, 0, 2, 3)
        growth_pct = (breakdown.total_dims / breakdown.baseline_dims - 1) * 100
        print(f"{level_name:25s}: {baseline_dim:3d} → {breakdown.total_dims:3d} (+{breakdown.total_vfs_dims:2d}, +{growth_pct:.1f}%)")


def generate_summary_report():
    """Generate executive summary for team presentation."""
    print("\n" + "=" * 70)
    print("EXECUTIVE SUMMARY")
    print("=" * 70)

    limits = VFSProfileLimits()

    # Calculate worst-case totals for cleaner f-string
    worst_case_vfs_dims = limits.max_global_profiles + limits.max_agent_profiles + (limits.max_item_profiles * limits.max_items_per_agent)
    worst_case_total = 93 + worst_case_vfs_dims
    worst_case_pct = (worst_case_total / 93 - 1) * 100

    print(f"""
Phase 1 Design Decisions:
- Max global VFS profiles:  {limits.max_global_profiles}
- Max agent VFS profiles:   {limits.max_agent_profiles}
- Max item profiles:        {limits.max_item_profiles} (per item type)
- Max items per agent:      {limits.max_items_per_agent}

Worst-Case obs_dim Growth:
- VFS contribution: +{worst_case_vfs_dims} dims
- Largest level (L1/L3): 93 → {worst_case_total} dims ({worst_case_pct:.1f}% increase)

Realistic obs_dim Growth:
- VFS contribution: +16 dims (5 global + 5 agent + 6 item)
- Largest level (L1/L3): 93 → 109 dims (+17% increase)

Checkpoint Compatibility:
- obs_dim remains FIXED for given config (no runtime changes)
- Empty item slots masked with 0.0 (not removed from obs)
- Checkpoint transfer works across levels with same VFS/Items config

Network Architecture Impact:
- Current MLP: obs_dim → 256 → 128 → action_dim
- Worst-case L1: 148 dims → 256 (still comfortable)
- No architecture changes needed

Conclusion:
✓ Phase 1 limits are SAFE and CONSERVATIVE
✓ Realistic usage has minimal impact (+17%)
✓ Worst-case is manageable (+59%)
✓ No network architecture changes needed
""")


def main():
    """Run all validation checks."""
    print("\n" + "=" * 70)
    print("VFS & ITEMS OBSERVATION DIMENSION VALIDATION")
    print("Phase 1 Limits Analysis")
    print("=" * 70)

    # Run validations
    worst_case_safe = validate_phase1_worst_case()
    validate_realistic_scenario()
    validate_minimal_scenario()
    generate_summary_report()

    # Exit code
    if worst_case_safe:
        print("\n✓ VALIDATION PASSED: Phase 1 limits are safe")
        return 0
    else:
        print("\n❌ VALIDATION FAILED: Phase 1 limits too high")
        return 1


if __name__ == "__main__":
    exit(main())
