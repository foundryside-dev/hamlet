"""Regression tests for level-specific action/affordance metadata wiring.

These tests ensure the vectorized environment respects per-level action
metadata (enabled_actions) and aligns temporal affordance masks with the
level's affordance ordering rather than the primary level's vocabulary.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler


def _build_two_level_pack(tmp_path: Path, config_pack_factory) -> Path:
    """Create a two-level config pack with diverging action/affordance metadata.

    L0_test: template as-is (only REST enabled, canonical affordance order)
    L1_alt:  REST + MEDITATE enabled; affordance list reversed to change mask order
    """

    pack_dir = config_pack_factory(name="two_level_pack")

    # Ensure REST/MEDITATE are present in the action vocabulary so enabling works.
    actions_path = pack_dir / "actions.yaml"
    actions_data = yaml.safe_load(actions_path.read_text())
    custom_actions = actions_data["actions"].setdefault("custom_actions", [])
    existing = {action["name"] for action in custom_actions}

    def _add_action(name: str, description: str):
        if name in existing:
            return
        custom_actions.append(
            {
                "name": name,
                "description": description,
                "enabled_by_default": False,
            }
        )
        existing.add(name)

    _add_action("REST", "Passive energy recovery (test)")
    _add_action("MEDITATE", "Passive mood/health recovery (test)")
    actions_path.write_text(yaml.safe_dump(actions_data, sort_keys=False))

    # Extend experiment curriculum_levels with a second level.
    experiment_path = pack_dir / "experiment.yaml"
    experiment_data = yaml.safe_load(experiment_path.read_text())
    levels = experiment_data["experiment"].get("curriculum_levels", [])
    levels.append("L1_alt")
    experiment_data["experiment"]["curriculum_levels"] = levels
    experiment_path.write_text(yaml.safe_dump(experiment_data, sort_keys=False))

    # Clone L0_test → L1_alt.
    src_level = pack_dir / "levels" / "L0_test"
    dest_level = pack_dir / "levels" / "L1_alt"
    shutil.copytree(src_level, dest_level)

    # Enable an extra custom action (MEDITATE) in L1_alt.
    training_path = dest_level / "training.yaml"
    training_data = yaml.safe_load(training_path.read_text())
    enabled_actions = training_data.get("training", {}).get("enabled_actions", {}) or {}
    custom_actions = enabled_actions.get("custom", [])
    if "MEDITATE" not in custom_actions:
        custom_actions.append("MEDITATE")
    enabled_actions["custom"] = custom_actions
    training_data.setdefault("training", {})["enabled_actions"] = enabled_actions
    training_path.write_text(yaml.safe_dump(training_data, sort_keys=False))

    # Reverse affordance order in L1_alt to force a different mask column layout.
    affordances_path = dest_level / "affordances.yaml"
    affordances_data = yaml.safe_load(affordances_path.read_text())
    affordance_list = affordances_data["affordances"].get("affordances", [])
    affordances_data["affordances"]["affordances"] = list(reversed(affordance_list))
    affordances_path.write_text(yaml.safe_dump(affordances_data, sort_keys=False))

    # Turn on temporal mechanics for L1_alt so temporal masks are exercised.
    curriculum_path = dest_level / "curriculum.yaml"
    curriculum_data = yaml.safe_load(curriculum_path.read_text())
    curriculum_data.setdefault("curriculum", {})["active_temporal"] = True
    curriculum_data["curriculum"]["day_length"] = 4
    curriculum_path.write_text(yaml.safe_dump(curriculum_data, sort_keys=False))

    return pack_dir


def _compile_two_level_pack(tmp_path: Path, config_pack_factory, compile_universe) -> CompiledUniverse:
    pack_dir = _build_two_level_pack(tmp_path, config_pack_factory)
    return compile_universe(pack_dir, primary_level="L0_test")


def test_level_action_metadata_respected(tmp_path, config_pack_factory, compile_universe, cpu_device):
    """MEDITATE should be disabled in L0_test but enabled in L1_alt via level metadata."""

    compiled = _compile_two_level_pack(tmp_path, config_pack_factory, compile_universe)

    env_l0 = compiled.create_environment(num_agents=1, level_name="L0_test", device=cpu_device)
    env_l1 = compiled.create_environment(num_agents=1, level_name="L1_alt", device=cpu_device)

    meditate_id = env_l1.action_space.get_action_by_name("MEDITATE").id

    base_mask_l0 = env_l0.action_space.get_base_action_mask(num_agents=1, device=env_l0.device)
    base_mask_l1 = env_l1.action_space.get_base_action_mask(num_agents=1, device=env_l1.device)

    assert base_mask_l0.shape == base_mask_l1.shape
    assert not base_mask_l0[0, meditate_id], "L0_test should keep MEDITATE disabled"
    assert base_mask_l1[0, meditate_id], "L1_alt should enable MEDITATE via level action metadata"


def test_affordance_gate_program_uses_selected_level_order(tmp_path, config_pack_factory, compile_universe, cpu_device):
    """Temporal gates must compile from the selected level, not the primary level."""

    compiled = _compile_two_level_pack(tmp_path, config_pack_factory, compile_universe)
    level0 = compiled.get_level("L0_test")
    level1 = compiled.get_level("L1_alt")

    level0_affordances = [aff.name for aff in level0.affordances.affordances]
    level1_affordances = [aff.name for aff in level1.affordances.affordances]
    assert level0_affordances != level1_affordances  # Sanity: order actually differs

    env = compiled.create_environment(num_agents=1, level_name="L1_alt", device=cpu_device)
    gate_targets = [rule.target_affordance_id for rule in env.vtc_affordance_gate_program.rules]

    assert not hasattr(env, "action_mask_table")
    assert gate_targets == level1_affordances


def test_environment_metadata_matches_selected_non_primary_level(tmp_path, cpu_device):
    pack_dir = tmp_path / "default_curriculum"
    shutil.copytree(Path("configs/default_curriculum"), pack_dir)
    stratum_path = pack_dir / "stratum.yaml"
    stratum_data = yaml.safe_load(stratum_path.read_text())
    stratum_path.write_text(yaml.safe_dump(stratum_data, sort_keys=False))

    compiled = UniverseCompiler().compile(
        pack_dir,
        primary_level="L1_full_observability",
        use_cache=False,
    )

    env = compiled.create_environment(num_agents=1, level_name="L2_partial_observability", device=cpu_device)

    # The env's metadata is the SELECTED level's, not the compiled primary's. Observation
    # width is deliberately NOT the discriminator any more: one pack has one TokenSpec, and
    # POMDP changes the visibility radius, never the layout (token-obs spec §3). The
    # per-level curriculum is what actually differs.
    assert env.metadata.primary_level == "L2_partial_observability"
    assert compiled.metadata.primary_level == "L1_full_observability"
    assert env.token_spec.total_dims == compiled.metadata.observation_dim
    assert env.metadata.observation_dim == env.token_spec.total_dims
    assert env.partial_observability
    assert env.metadata.action_count == env.level.action_metadata.total_actions
