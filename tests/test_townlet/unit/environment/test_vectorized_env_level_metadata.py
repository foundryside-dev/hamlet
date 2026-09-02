"""Regression tests for level-specific action/affordance metadata wiring.

These tests ensure the vectorized environment respects per-level action
metadata (enabled_actions) and aligns temporal affordance masks with the
level's affordance ordering rather than the primary level's vocabulary.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from townlet.agent.networks import TokenSetQNetwork
from townlet.config.brain_config import ArchitectureConfig, SetAggregatorConfig, TokenSetConfig
from townlet.population.vectorized import VectorizedPopulation
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.token_hashes import compute_token_layout_hash


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

    # Change compiler-owned meter identity without changing its shape.
    bars_path = dest_level / "bars.yaml"
    bars_data = yaml.safe_load(bars_path.read_text())
    bars_data["bars"]["meters"][0]["initial"] = 0.5
    bars_path.write_text(yaml.safe_dump(bars_data, sort_keys=False))

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


def test_selected_non_primary_level_carries_its_own_meter_runtime_declarations(
    tmp_path,
    config_pack_factory,
    compile_universe,
    cpu_device,
):
    compiled = _compile_two_level_pack(tmp_path, config_pack_factory, compile_universe)
    primary = compiled.get_level("L0_test")
    selected = compiled.get_level("L1_alt")
    env = compiled.create_environment(num_agents=1, level_name="L1_alt", device=cpu_device)

    assert primary.token_spec.total_dims == selected.token_spec.total_dims
    assert primary.meter_declarations != selected.meter_declarations
    assert env.level.meter_declarations is selected.meter_declarations


def test_dac_bar_indices_come_from_selected_non_primary_level(
    tmp_path,
    config_pack_factory,
    compile_universe,
    cpu_device,
):
    compiled = _compile_two_level_pack(tmp_path, config_pack_factory, compile_universe)
    selected = compiled.get_level("L1_alt")
    env = compiled.create_environment(num_agents=1, level_name="L1_alt", device=cpu_device)

    expected = {meter.name: meter.index for meter in selected.meter_metadata.meters}
    assert env.dac_engine.bar_index_map == expected


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
    # width is deliberately NOT the discriminator any more: level specs share one layout,
    # and POMDP changes the visibility radius rather than the layout (token-obs spec §3).
    # Static declaration identity can still differ, so the encoder must use the selected
    # level's TokenSpec rather than the universe's primary-level alias.
    assert env.metadata.primary_level == "L2_partial_observability"
    assert compiled.metadata.primary_level == "L1_full_observability"
    assert env.token_spec.total_dims == compiled.metadata.observation_dim
    assert env.metadata.observation_dim == env.token_spec.total_dims
    assert env._observation_encoder._spec is env.level.token_spec
    assert env._observation_encoder._spec is not compiled.get_level(compiled.metadata.primary_level).token_spec
    assert env.partial_observability
    assert env.metadata.action_count == env.level.action_metadata.total_actions


def test_token_set_population_builds_from_selected_non_primary_level(
    tmp_path,
    config_pack_factory,
    compile_universe,
    adversarial_curriculum,
    epsilon_greedy_exploration,
    cpu_device,
):
    """The token network must bind the selected level's positional layout."""

    compiled = _compile_two_level_pack(tmp_path, config_pack_factory, compile_universe)
    env = compiled.create_environment(num_agents=1, level_name="L1_alt", device=cpu_device)
    brain = compiled.brain.model_copy(
        update={
            "architecture": ArchitectureConfig(
                type="token_set",
                token_set=TokenSetConfig(
                    token_embed_dim=16,
                    q_head_hidden_dim=32,
                    aggregator=SetAggregatorConfig(type="mean"),
                ),
            )
        }
    )

    assert env.token_spec is env.level.token_spec
    primary_spec = compiled.get_level(compiled.metadata.primary_level).token_spec
    assert env.token_spec is not primary_spec
    assert compute_token_layout_hash(env.token_spec) != compute_token_layout_hash(primary_spec)

    population = VectorizedPopulation(
        env=env,
        curriculum=adversarial_curriculum,
        exploration=epsilon_greedy_exploration,
        agent_ids=["agent_0"],
        device=cpu_device,
        brain_config=brain,
        obs_dim=env.observation_dim,
        train_frequency=1,
        batch_size=1,
        sequence_length=1,
        max_grad_norm=10.0,
        action_dim=env.action_dim,
    )

    assert population.token_spec is env.token_spec
    assert isinstance(population.q_network, TokenSetQNetwork)
    assert population.q_network.obs_dim == env.token_spec.total_dims
