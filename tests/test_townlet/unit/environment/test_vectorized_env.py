"""Unit tests for VectorizedHamletEnv (environment/vectorized_env.py).

This test suite focuses on testing individual methods of VectorizedHamletEnv
with mocked dependencies to achieve 70%+ coverage.

Test Coverage Plan (Sprint 15):
- Phase 15A: Initialization & Setup (__init__, reset, _build_movement_deltas)
- Phase 15B: Core Loop (step, _execute_actions, _get_observations, get_action_masks)
- Phase 15C: Interactions & Rewards (_handle_interactions, _calculate_shaped_rewards)
- Phase 15D: Checkpointing (get/set_affordance_positions, randomize_affordance_positions)

Testing Strategy:
- Mock heavy dependencies (SubstrateFactory, AffordanceEngine, etc.)
- Use real tensors for state (positions, meters)
- Focus on logic paths, not tensor operations
- Use builders.py for test data construction
"""

from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

import pytest
import torch
import yaml

import townlet.environment.action_executor as action_executor_module
import townlet.environment.env_factory as env_factory_module
import townlet.environment.observation_encoder as observation_encoder_module
import townlet.environment.reward_calculator as reward_calculator_module
import townlet.environment.vectorized_env as vectorized_env_module
from townlet.environment.env_factory import (
    _build_bar_index_map,
    _resolve_deployable_affordances,
)
from townlet.universe.compiled import CompiledVFSProfiles
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.dto import MeterInfo, MeterMetadata
from townlet.universe.errors import CompilationError
from townlet.vfs.profiles import CompiledGlobalProfile, CompiledVariable
from townlet.vfs.schema import WriteSpec

DEFAULT_CURRICULUM_LEVELS = (
    "L0_0_minimal",
    "L0_5_dual_resource",
    "L1_full_observability",
    "L2_partial_observability",
    "L3_temporal_mechanics",
)

# =============================================================================
# AFFORDANCE FILTERING HELPERS
# =============================================================================


def test_environment_runtime_modules_own_extracted_clusters():
    """R-1 ownership guard: vectorized_env delegates the extracted method clusters."""
    env_source = Path(vectorized_env_module.__file__).read_text()

    expected_module_methods = {
        action_executor_module: [
            "def _execute_actions",
            "def _handle_interactions",
            "def _handle_instant_interactions",
        ],
        observation_encoder_module: [
            "def _get_observations",
            "def _build_affordance_encoding",
            "def _encode_position_observation",
        ],
        reward_calculator_module: ["def _calculate_shaped_rewards"],
        env_factory_module: ["def from_universe"],
    }
    for module, method_markers in expected_module_methods.items():
        source = Path(module.__file__).read_text()
        for marker in method_markers:
            assert marker in source

    delegated_implementation_markers = [
        "movement_actions =",
        "build_vfs_observation(",
        "dac_engine.calculate_rewards(",
        "return env_cls(",
    ]
    for marker in delegated_implementation_markers:
        assert marker not in env_source


def _with_runtime_action_write(universe, level_name: str, action_name: str, write: WriteSpec):
    """Return a compiled universe whose named runtime action carries one VFS write."""
    return _with_runtime_action_surface(universe, level_name, action_name, writes=(write,), disable_vfs_profiles=True)


def _with_runtime_action_surface(
    universe,
    level_name: str,
    action_name: str,
    *,
    costs: dict[str, float] | None = None,
    effects: dict[str, float] | None = None,
    writes: tuple[WriteSpec, ...] = (),
    disable_vfs_profiles: bool = False,
):
    """Return a compiled universe with patched runtime action effects/writes for equivalence tests."""
    level = universe.get_level(level_name)
    patched_actions = []
    found = False
    for action in level.runtime_action_space.actions:
        if action.name == action_name:
            patched_actions.append(
                replace(
                    action,
                    costs=costs if costs is not None else action.costs,
                    effects=effects if effects is not None else action.effects,
                    writes=tuple(write.model_dump(mode="json") for write in writes),
                )
            )
            found = True
        else:
            patched_actions.append(action)
    if not found:
        raise AssertionError(f"Test action '{action_name}' was not present in runtime action space")

    runtime_action_space = replace(level.runtime_action_space, actions=tuple(patched_actions))
    patched_level = replace(level, runtime_action_space=runtime_action_space)
    all_levels = dict(universe.all_levels or {})
    all_levels[level_name] = patched_level
    return replace(
        universe,
        runtime_action_space=runtime_action_space,
        all_levels=all_levels,
        compiled_vfs_profiles=None if disable_vfs_profiles else universe.compiled_vfs_profiles,
        vfs_observation_spec=None if disable_vfs_profiles else universe.vfs_observation_spec,
        vfs_observation_marks=None if disable_vfs_profiles else universe.vfs_observation_marks,
    )


def test_build_bar_index_map():
    """Test bar index map construction from universe metadata."""
    # Create mock metadata with 3 bars
    # MeterInfo.name is the bar ID (lowercase)
    meter_metadata = MeterMetadata(
        meters=(
            MeterInfo(name="energy", index=0, critical=True, initial_value=1.0, observable=True),
            MeterInfo(name="health", index=1, critical=True, initial_value=1.0, observable=True),
            MeterInfo(name="satiation", index=2, critical=False, initial_value=0.8, observable=True),
        )
    )

    bar_map = _build_bar_index_map(meter_metadata)

    assert bar_map == {"energy": 0, "health": 1, "satiation": 2}
    assert len(bar_map) == 3


class TestResolveDeployableAffordances:
    def test_supports_enabled_ids_and_names(self):
        all_names = ["Bed", "Doctor", "FastFood"]
        name_to_id = {"Bed": "0", "Doctor": "5", "FastFood": "4"}
        enabled = ["5", "FastFood"]

        result = _resolve_deployable_affordances(all_names, enabled, name_to_id)

        assert result == ["Doctor", "FastFood"]


# =============================================================================
# PHASE 15A: INITIALIZATION & SETUP
# =============================================================================


class TestVectorizedHamletEnvInitialization:
    """Test VectorizedHamletEnv.__init__ with various configurations."""

    def test_init_requires_stratum_yaml(self, config_pack_factory):
        """Should raise CompilationError if stratum.yaml is missing (v2.1 experiment root)."""
        config_pack = config_pack_factory(name="missing_stratum")
        (config_pack / "stratum.yaml").unlink()

        with pytest.raises(CompilationError, match="stratum.yaml.*not found"):
            UniverseCompiler().compile(config_pack, primary_level="L0_test")

    def test_init_raises_if_config_pack_not_found(self, compile_universe):
        """Should raise CompilationError if config pack directory doesn't exist."""
        with pytest.raises(CompilationError, match="Config directory does not exist"):
            compile_universe(Path("/nonexistent/path"))

    def test_env_defaults_to_test_config_pack(self, cpu_env_factory, test_config_pack_path: Path):
        """Env factory defaults to configs/test pack (compiled path)."""

        env = cpu_env_factory()
        assert Path(env.config_pack_path).resolve() == test_config_pack_path.resolve()

    def test_init_creates_substrate_from_config(self, cpu_env_factory):
        """Should load substrate.yaml and create substrate via factory."""
        env = cpu_env_factory(num_agents=2)

        # Verify substrate was created
        assert env.substrate is not None
        assert hasattr(env.substrate, "position_dim")

    def test_init_loads_affordances_from_config(self, cpu_env_factory):
        """Should load affordances.yaml and create affordance engine."""
        env = cpu_env_factory()

        # Verify affordance engine was created
        assert env.affordance_engine is not None
        assert hasattr(env.affordance_engine, "affordances")

    def test_init_initializes_state_tensors(self, cpu_env_factory):
        """Should initialize positions, meters, lifetimes, and dones tensors."""
        num_agents = 3
        env = cpu_env_factory(num_agents=num_agents)
        env.reset()

        # Verify state tensors exist with correct shapes
        assert env.positions.shape == (num_agents, env.substrate.position_dim)
        assert env.meters.shape == (num_agents, env.meter_count)
        assert env.dones.shape == (num_agents,)

        # Verify tensors are on correct device
        assert env.positions.device == env.device
        assert env.meters.device == env.device

    def test_init_sets_device_correctly(self, env_factory):
        """Should set device to CPU by default or use provided device."""
        env_cpu = env_factory(device_override="cpu")
        assert env_cpu.device == torch.device("cpu")

        env_explicit = env_factory(device_override=torch.device("cpu"))
        assert env_explicit.device == torch.device("cpu")


class TestVectorizedHamletEnvReset:
    """Test VectorizedHamletEnv.reset() method."""

    def test_reset_returns_observations(self, cpu_env_factory):
        env = cpu_env_factory(num_agents=2)
        obs = env.reset()
        assert isinstance(obs, torch.Tensor)
        assert obs.shape == (env.num_agents, env.observation_dim)

    def test_reset_initializes_meters_from_config(self, cpu_env_factory):
        env = cpu_env_factory(num_agents=2)
        env.reset()
        assert torch.all(env.meters >= 0.0)
        assert torch.all(env.meters <= 1.0)
        assert torch.all(env.meters[0] == env.meters[1])

    def test_reset_clears_dones_flag(self, cpu_env_factory):
        env = cpu_env_factory(num_agents=2)
        env.dones = torch.ones(2, dtype=torch.bool)
        env.reset()
        assert torch.all(~env.dones)

    def test_reset_initializes_step_counts(self, cpu_env_factory):
        env = cpu_env_factory(num_agents=2)
        env.step_counts = torch.tensor([10, 20])
        env.reset()
        assert torch.all(env.step_counts == 0)

    def test_reset_randomizes_agent_positions(self, cpu_env_factory):
        env = cpu_env_factory(num_agents=5)
        env.reset()
        assert torch.all(env.positions >= 0)
        assert torch.all(env.positions < env.grid_size)

    def test_reset_temporal_mechanics_initializes_time(self, env_factory, cpu_device):
        env = env_factory(
            config_dir=Path("configs/default_curriculum"),
            level_name="L3_temporal_mechanics",
            num_agents=1,
            device_override=cpu_device,
        )
        env.reset()
        assert env.enable_temporal_mechanics is True
        assert env.time_of_day == 0


class TestBuildMovementDeltas:
    """Test VectorizedHamletEnv._build_movement_deltas() method."""

    def test_build_movement_deltas_creates_tensor(self, cpu_env_factory):
        """Should create movement deltas tensor from substrate actions."""

        env = cpu_env_factory()

        deltas = env._build_movement_deltas()

        # Should return tensor with shape [action_dim, position_dim]
        assert isinstance(deltas, torch.Tensor)
        assert deltas.shape[0] == env.action_dim
        assert deltas.shape[1] == env.substrate.position_dim

    def test_build_movement_deltas_correct_values_grid2d(self, cpu_env_factory):
        """Should create correct deltas for Grid2D substrate (UP, DOWN, LEFT, RIGHT)."""

        env = cpu_env_factory()

        deltas = env._build_movement_deltas()

        # For Grid2D, movement actions should have non-zero deltas
        # Non-movement actions (INTERACT, WAIT, REST, MEDITATE) should have zero deltas
        # Check that at least some actions have non-zero deltas
        has_nonzero = torch.any(deltas != 0, dim=1)
        assert torch.any(has_nonzero).item(), "Should have some non-zero movement deltas"


# =============================================================================
# PLACEHOLDER: PHASE 15B, 15C, 15D tests will be added incrementally
# =============================================================================


# =============================================================================
# PHASE 15B: CORE LOOP (step, _execute_actions, _get_observations, get_action_masks)
# =============================================================================


class TestVectorizedHamletEnvStep:
    """Test VectorizedHamletEnv.step() method."""

    def test_step_returns_correct_types(self, cpu_env_factory):
        env = cpu_env_factory(num_agents=2)
        env.reset()

        actions = torch.full((2,), 5, device=env.device, dtype=torch.long)
        obs, rewards, dones, info = env.step(actions)

        assert isinstance(obs, torch.Tensor)
        assert isinstance(rewards, torch.Tensor)
        assert isinstance(dones, torch.Tensor)
        assert isinstance(info, dict)

    def test_step_returns_correct_shapes(self, cpu_env_factory):
        env = cpu_env_factory(num_agents=3)
        env.reset()

        actions = torch.full((3,), 5, device=env.device, dtype=torch.long)
        obs, rewards, dones, _ = env.step(actions)

        assert obs.shape == (3, env.observation_dim)
        assert rewards.shape == (3,)
        assert dones.shape == (3,)

    def test_step_increments_step_counts(self, cpu_env_factory):
        env = cpu_env_factory(num_agents=2)
        env.reset()

        initial_counts = env.step_counts.clone()
        actions = torch.full((2,), 5, device=env.device, dtype=torch.long)
        env.step(actions)

        assert torch.all(env.step_counts == initial_counts + 1)

    def test_step_depletes_meters(self, cpu_env_factory):
        env = cpu_env_factory(num_agents=2)
        env.reset()

        initial_meters = env.meters.clone()
        actions = torch.full((2,), 5, device=env.device, dtype=torch.long)
        env.step(actions)

        assert not torch.allclose(env.meters, initial_meters)

    def test_step_executes_compiled_vfs_action_writes(self, compile_universe, test_config_pack_path, cpu_device):
        universe = compile_universe(test_config_pack_path)
        write = WriteSpec(
            variable_id="deficit_energy",
            expression="0.25",
            condition=None,
            composition="additive_delta",
            phase="apply_action_effects",
            priority=0,
            clamp=(0.0, 1.0),
            telemetry_label="wait_deficit_energy",
        )
        universe = _with_runtime_action_write(universe, "L0_test", "WAIT", write)
        env = vectorized_env_module.VectorizedHamletEnv.from_universe(
            universe,
            level_name="L0_test",
            num_agents=2,
            device=cpu_device,
        )
        env.reset()

        before = env.vfs_registry.get("deficit_energy", reader="engine").clone()
        actions = torch.tensor([env.action_ids["WAIT"], env.action_ids["REST"]], device=env.device)
        env.step(actions)
        after = env.vfs_registry.get("deficit_energy", reader="engine")

        assert torch.allclose(after, torch.tensor([before[0] + 0.25, before[1]], device=env.device))

    def test_vtc_action_effects_apply_all_curriculum_levels(self, compile_universe, cpu_device):
        write = WriteSpec(
            variable_id="energy",
            expression="0.13",
            condition=None,
            composition="additive_delta",
            phase="apply_action_effects",
            priority=0,
            clamp=(0.0, 1.0),
            telemetry_label="rest_energy_gain",
        )

        for level_name in DEFAULT_CURRICULUM_LEVELS:
            universe = compile_universe(Path("configs/default_curriculum"), primary_level=level_name)
            vtc_universe = _with_runtime_action_surface(
                universe,
                level_name,
                "REST",
                writes=(write,),
            )
            control_env = vectorized_env_module.VectorizedHamletEnv.from_universe(
                universe,
                level_name=level_name,
                num_agents=3,
                device=cpu_device,
            )
            vtc_env = vectorized_env_module.VectorizedHamletEnv.from_universe(
                vtc_universe,
                level_name=level_name,
                num_agents=3,
                device=cpu_device,
            )

            torch.manual_seed(17)
            control_env.reset()
            torch.manual_seed(17)
            vtc_env.reset()
            vtc_env.positions = control_env.positions.clone()
            vtc_env.meters = control_env.meters.clone()
            vtc_env.dones = control_env.dones.clone()
            vtc_env.step_counts = control_env.step_counts.clone()
            vtc_env.global_tick = control_env.global_tick
            vtc_env.time_of_day = control_env.time_of_day

            energy_idx = control_env.meter_name_to_index["energy"]
            control_env.meters[:, energy_idx] = 0.5
            vtc_env.meters[:, energy_idx] = 0.5

            actions = torch.full((control_env.num_agents,), control_env.action_ids["REST"], dtype=torch.long, device=control_env.device)
            assert torch.equal(control_env.get_action_masks(), vtc_env.get_action_masks())

            _, control_rewards, control_dones, _ = control_env.step(actions)
            _, vtc_rewards, vtc_dones, _ = vtc_env.step(actions)

            energy_delta = vtc_env.meters[:, energy_idx] - control_env.meters[:, energy_idx]
            assert torch.allclose(energy_delta, torch.full_like(energy_delta, 0.13), atol=1e-6), level_name
            assert torch.all(torch.isfinite(control_rewards)).item(), level_name
            assert torch.all(torch.isfinite(vtc_rewards)).item(), level_name
            assert torch.equal(control_dones, vtc_dones), level_name
            assert torch.equal(control_env.get_action_masks(), vtc_env.get_action_masks()), level_name

    def test_step_increments_time_of_day(self, custom_env_builder):
        # Use temporal-enabled level to ensure mechanics are active
        env = custom_env_builder(
            source_pack=Path("configs/default_curriculum"),
            level_name="L3_temporal_mechanics",
            overrides=None,
        )
        env.reset()

        wait_action_idx = env.action_ids["WAIT"]
        actions = torch.tensor([wait_action_idx], device=env.device)
        env.step(actions)
        assert env.time_of_day == 1

        env.time_of_day = 23
        env.step(actions)
        assert env.time_of_day == 0

    def test_step_retirement_bonus(self, custom_env_builder):
        env = custom_env_builder(
            overrides={"training_loop": {"max_steps_per_episode": 5}},
        )
        env.agent_lifespan = 5
        env.reset()

        wait_action_idx = env.action_ids["WAIT"]
        actions = torch.tensor([wait_action_idx], device=env.device)
        for _ in range(4):
            _, _, dones, _ = env.step(actions)
            assert not dones[0]

        _, rewards, dones, _ = env.step(actions)
        assert dones[0]
        assert rewards[0].item() >= 1.0

    def test_step_info_contains_metadata(self, cpu_env_factory):
        env = cpu_env_factory(num_agents=2)
        env.reset()

        actions = torch.full((2,), 5, device=env.device, dtype=torch.long)
        _, _, _, info = env.step(actions)

        assert set(info.keys()) >= {"step_counts", "positions", "successful_interactions"}
        assert isinstance(info["step_counts"], torch.Tensor)
        assert isinstance(info["positions"], torch.Tensor)
        assert isinstance(info["successful_interactions"], dict)

    def test_step_info_contains_reward_components(self, cpu_env_factory):
        """Test that info dict contains reward_components and intrinsic_weight."""
        env = cpu_env_factory(num_agents=2)
        env.reset()

        actions = torch.full((2,), 5, device=env.device, dtype=torch.long)
        _, _, _, info = env.step(actions)

        # Verify reward_components is present and is a dict
        assert "reward_components" in info
        assert isinstance(info["reward_components"], dict)

        # Verify expected component keys
        components = info["reward_components"]
        assert "extrinsic" in components
        assert "intrinsic" in components
        assert "shaping" in components

        # Verify each component is a tensor with correct shape
        assert isinstance(components["extrinsic"], torch.Tensor)
        assert isinstance(components["intrinsic"], torch.Tensor)
        assert isinstance(components["shaping"], torch.Tensor)
        assert components["extrinsic"].shape == (2,)
        assert components["intrinsic"].shape == (2,)
        assert components["shaping"].shape == (2,)

        # Verify intrinsic_weight is present and is a tensor
        assert "intrinsic_weight" in info
        assert isinstance(info["intrinsic_weight"], torch.Tensor)
        assert info["intrinsic_weight"].shape == (2,)

    def test_step_threads_vfs_affordance_and_temporal_context(self, custom_env_builder, monkeypatch):
        """Runtime VFS evaluation should receive current affordance and temporal state."""
        env = custom_env_builder(overrides={"environment": {"enable_temporal_mechanics": True}})
        env.reset()
        env.time_of_day = 10
        env.global_tick = 7

        profile = CompiledGlobalProfile(
            variables=[
                CompiledVariable(
                    name="context_probe",
                    type="bool",
                    exposed_to=("agent",),
                    semantic_type="custom",
                    initial_value=True,
                    result_type="bool",
                )
            ],
            dependencies={"context_probe": tuple()},
        )
        env.universe = replace(
            env.universe,
            compiled_vfs_profiles=CompiledVFSProfiles(
                evaluation_mode="mark_and_sweep",
                debug_logging=False,
                global_profile=profile,
                item_profiles={},
            ),
        )
        env.vfs_observation_marks = {"global": {"context_probe"}}

        captured_context: dict[str, object] = {}

        def capture_evaluation(**kwargs):
            captured_context.update(kwargs)
            return {}

        assert env.vfs_evaluator is not None
        monkeypatch.setattr(env.vfs_evaluator, "evaluate_global_profile", capture_evaluation)

        env.step(torch.zeros(env.num_agents, dtype=torch.long))

        assert set(captured_context["affordances"]) == set(env.affordances)
        first_affordance = env.affordance_names[0]
        affordance_state = captured_context["affordances"][first_affordance]
        assert torch.equal(affordance_state["available"], torch.tensor(env._is_affordance_open(first_affordance), device=env.device))

        temporal = captured_context["temporal"]
        assert torch.equal(temporal["tick"], torch.tensor(7, device=env.device))
        assert torch.equal(temporal["time_of_day"], torch.tensor(10.0, device=env.device))
        assert torch.equal(temporal["day_progress"], torch.tensor(10.0 / float(env.day_length), device=env.device))
        assert torch.equal(temporal["is_night"], torch.tensor(False, device=env.device))


class TestExecuteActions:
    """Test VectorizedHamletEnv._execute_actions() method."""

    def test_execute_actions_movement(self, cpu_env_factory):
        """Should update agent positions for movement actions."""

        env = cpu_env_factory()
        env.reset()

        # Place agent away from borders so the UP action can't clamp back into the
        # same cell, which previously made this test randomly fail when the
        # sampled spawn started on y=0.
        env.positions[0] = torch.tensor([3, 3], device=env.device, dtype=env.positions.dtype)

        initial_position = env.positions[0].clone()

        # Execute UP action (action 0 for Grid2D)
        up_idx = env.action_ids["UP"]
        actions = torch.tensor([up_idx], device=env.device)
        env._execute_actions(actions)

        # Position should change
        assert not torch.all(env.positions[0] == initial_position).item()

    def test_execute_actions_wait_preserves_position(self, cpu_env_factory):
        """Should not change position for WAIT action."""
        env = cpu_env_factory()
        env.reset()

        initial_position = env.positions[0].clone()

        # Execute WAIT action using runtime index
        wait_action_idx = env.action_ids["WAIT"]
        actions = torch.tensor([wait_action_idx], device=env.device)
        env._execute_actions(actions)

        # Position should not change
        assert torch.all(env.positions[0] == initial_position).item()

    def test_execute_actions_interact_preserves_position(self, cpu_env_factory):
        """Should not change position for INTERACT action."""
        env = cpu_env_factory()
        env.reset()

        initial_position = env.positions[0].clone()

        # Execute INTERACT action using runtime index
        interact_idx = env.action_ids.get("INTERACT")
        if interact_idx is not None:
            actions = torch.tensor([interact_idx], device=env.device)
            env._execute_actions(actions)

        # Position should not change
        assert torch.all(env.positions[0] == initial_position).item()

    def test_execute_actions_returns_interaction_dict(self, cpu_env_factory):
        """Should return dict mapping agent indices to affordance names for successful interactions."""
        env = cpu_env_factory(num_agents=2)
        env.reset()

        actions = torch.tensor([4, 5], device=env.device)  # INTERACT, WAIT
        result = env._execute_actions(actions)

        assert isinstance(result, dict)


class TestGetObservations:
    """Test VectorizedHamletEnv._get_observations() method."""

    def test_get_observations_returns_tensor(self, cpu_env_factory):
        env = cpu_env_factory(num_agents=2)
        env.reset()

        obs = env._get_observations()

        assert obs.shape == (2, env.observation_dim)

    def test_get_observations_full_observability_shape(self, cpu_env_factory):
        env = cpu_env_factory(num_agents=3)
        env.reset()
        obs = env._get_observations()
        assert obs.shape == (3, env.observation_dim)
        assert env.partial_observability is False

    def test_get_observations_pomdp_shape(self, custom_env_builder):
        env = custom_env_builder(
            num_agents=2,
            source_pack=Path("configs/default_curriculum"),
            level_name="L2_partial_observability",
        )
        env.reset()
        obs = env._get_observations()
        assert env.partial_observability is True
        assert obs.shape == (2, env.observation_dim)

    def test_get_observations_contains_meters(self, cpu_env_factory):
        env = cpu_env_factory()
        env.reset()
        obs = env._get_observations()
        assert torch.all(obs[:, -4:] >= -1.0)

    def test_get_observations_uses_substrate_position_encoder(self, cpu_env_factory, monkeypatch):
        env = cpu_env_factory(num_agents=2)
        env.reset()

        expected = torch.full((env.num_agents, env.substrate.position_dim), 0.42, device=env.device)

        def fake_encoder(positions, affordances):
            return expected

        def fail_normalize(_):
            raise AssertionError("normalize_positions should not be called when encoder exists")

        monkeypatch.setattr(env.substrate, "_encode_position_features", fake_encoder)
        monkeypatch.setattr(env.substrate, "normalize_positions", fail_normalize, raising=False)

        encoded = env._encode_position_observation()
        assert torch.allclose(encoded, expected)

    def test_get_observations_falls_back_to_encode_observation(self, cpu_env_factory, monkeypatch):
        env = cpu_env_factory()
        env.reset()

        expected = torch.full((env.num_agents, env.substrate.position_dim), 0.25, device=env.device)

        def fake_encode_observation(positions, affordances):
            return expected

        def fail_normalize(_):
            raise AssertionError("normalize_positions fallback should not trigger when encode_observation exists")

        monkeypatch.setattr(env.substrate, "_encode_position_features", None, raising=False)
        monkeypatch.setattr(env.substrate, "encode_position_features", None, raising=False)
        monkeypatch.setattr(env.substrate, "encode_observation", fake_encode_observation)
        monkeypatch.setattr(env.substrate, "normalize_positions", fail_normalize, raising=False)

        encoded = env._encode_position_observation()
        assert torch.allclose(encoded, expected)

    def test_get_observations_handles_agent_private_scope(self, cpu_env_factory):
        env = cpu_env_factory(num_agents=2)
        env.reset()

        env.vfs_registry.variables["deficit_energy"].scope = "agent_private"
        obs = env._get_observations()
        assert obs.shape[0] == env.num_agents


class TestGetActionMasks:
    """Test VectorizedHamletEnv.get_action_masks() method."""

    def test_get_action_masks_returns_tensor(self, cpu_env_factory):
        env = cpu_env_factory(num_agents=2)
        env.reset()
        masks = env.get_action_masks()
        assert masks.dtype == torch.bool

    def test_get_action_masks_correct_shape(self, cpu_env_factory):
        env = cpu_env_factory(num_agents=3)
        env.reset()
        masks = env.get_action_masks()
        assert masks.shape == (3, env.action_dim)

    def test_get_action_masks_some_actions_available(self, cpu_env_factory):
        env = cpu_env_factory()
        env.reset()
        masks = env.get_action_masks()
        assert torch.any(masks)
        assert masks.shape == (1, env.action_dim)

    def test_get_action_masks_temporal_mechanics_masks_closed_affordances(self, custom_env_builder):
        env = custom_env_builder(
            overrides={"environment": {"enable_temporal_mechanics": True}},
        )
        env.reset()

        bar_pos = env.affordances.get("Bar")
        if bar_pos is None:
            pytest.skip("Test config missing 'Bar' affordance")

        env.positions[0] = bar_pos.clone()

        env.time_of_day = 10  # Bar closed mid-morning
        closed_masks = env.get_action_masks()
        interact_idx = env.action_ids["INTERACT"]
        assert not closed_masks[0, interact_idx]

        env.time_of_day = 20  # Bar open in evening
        open_masks = env.get_action_masks()
        assert open_masks[0, interact_idx]

    def test_get_action_masks_respect_training_enabled_actions(self, custom_env_builder):
        env = custom_env_builder(
            overrides={"enabled_actions": {"custom": ["INTERACT", "WAIT"]}},
            num_agents=2,
        )
        env.reset()

        masks = env.get_action_masks()
        disabled_ids = [action.id for action in env.action_space.get_disabled_actions()]
        assert disabled_ids, "Expected at least one disabled action from enabled_actions override"

        for disabled_id in disabled_ids:
            assert torch.all(~masks[:, disabled_id]), f"Action {disabled_id} should be masked for all agents"


# =============================================================================
# PLACEHOLDER: PHASE 15C, 15D tests will be added incrementally
# =============================================================================


# =============================================================================
# PHASE 15C: INTERACTIONS & REWARDS
# =============================================================================


class TestHandleInteractions:
    """Test VectorizedHamletEnv._handle_interactions() and _handle_interactions_legacy()."""

    def test_handle_interactions_legacy_when_temporal_disabled(self, cpu_env_factory):
        """Should use legacy instant interactions when temporal mechanics disabled."""
        env = cpu_env_factory()
        env.reset()

        # Create interact mask
        interact_mask = torch.tensor([True])

        # Should return dict (may be empty if no affordance at position)
        result = env._handle_interactions(interact_mask)
        assert isinstance(result, dict)

    def test_handle_interactions_multi_tick_when_temporal_enabled(self, custom_env_builder):
        """Should use multi-tick interactions when temporal mechanics enabled."""
        env = custom_env_builder(overrides={"environment": {"enable_temporal_mechanics": True}})
        env.reset()

        # Multi-tick mode should initialize progress tracking
        assert hasattr(env, "interaction_progress")
        assert hasattr(env, "last_interaction_affordance")
        assert hasattr(env, "last_interaction_position")

    def test_handle_interactions_returns_empty_when_no_interact(self, cpu_env_factory):
        """Should return empty dict when no agents interact."""
        env = cpu_env_factory(num_agents=2)
        env.reset()

        # No agents interacting
        interact_mask = torch.tensor([False, False])

        result = env._handle_interactions(interact_mask)
        assert result == {}


class TestCalculateShapedRewards:
    """Test VectorizedHamletEnv._calculate_shaped_rewards()."""

    def test_calculate_shaped_rewards_returns_tensor(self, cpu_env_factory):
        """Should return rewards tensor."""
        env = cpu_env_factory(num_agents=2)
        env.reset()

        rewards = env._calculate_shaped_rewards()

        assert isinstance(rewards, torch.Tensor)
        assert rewards.shape == (2,)

    def test_calculate_shaped_rewards_uses_meter_values(self, cpu_env_factory):
        """Should calculate rewards based on current meter values."""
        env = cpu_env_factory()
        env.reset()

        # Get initial reward
        initial_reward = env._calculate_shaped_rewards()

        # Modify meters (reduce energy)
        energy_idx = next(m.index for m in env.level.meter_metadata.meters if m.name == "energy")
        env.meters[0, energy_idx] = 0.1

        # Reward should change
        new_reward = env._calculate_shaped_rewards()
        # Rewards are based on meter states, so they should differ
        assert initial_reward.item() != new_reward.item()

    def test_calculate_shaped_rewards_returns_finite_values(self, cpu_env_factory):
        """Should return finite reward values (no NaN or inf)."""
        env = cpu_env_factory(num_agents=3)
        env.reset()

        rewards = env._calculate_shaped_rewards()

        assert torch.all(torch.isfinite(rewards)).item()


class TestCustomActionExecution:
    """Test custom actions after VTC owns action meter effects."""

    def test_execute_actions_does_not_apply_legacy_runtime_costs_or_effects(self, compile_universe, cpu_device):
        universe = compile_universe(Path("configs/default_curriculum"), primary_level="L0_0_minimal")
        universe = _with_runtime_action_surface(
            universe,
            "L0_0_minimal",
            "REST",
            costs={"mood": 0.1},
            effects={"energy": 0.2},
            writes=(),
        )
        env = vectorized_env_module.VectorizedHamletEnv.from_universe(
            universe,
            level_name="L0_0_minimal",
            num_agents=2,
            device=cpu_device,
        )
        env.reset()
        env.meters.fill_(0.5)

        before = env.meters.clone()
        actions = torch.full((env.num_agents,), env.action_ids["REST"], dtype=torch.long, device=env.device)
        env._execute_actions(actions)

        assert torch.allclose(env.meters, before)

    def test_action_id_lookup_returns_int_or_none(self, cpu_env_factory):
        """action_ids lookup returns int for valid actions, None otherwise."""
        env = cpu_env_factory()
        env.reset()

        rest_idx = env.action_ids.get("REST")
        assert rest_idx is None or isinstance(rest_idx, int)

        invalid_idx = env.action_ids.get("NONEXISTENT_ACTION")
        assert invalid_idx is None


# =============================================================================
# PHASE 15D: CHECKPOINTING
# =============================================================================


class TestGetAffordancePositions:
    """Test VectorizedHamletEnv.get_affordance_positions()."""

    def test_get_affordance_positions_returns_dict(self, cpu_env_factory):
        """Should return dict with positions, ordering, and position_dim."""
        env = cpu_env_factory()
        env.reset()

        positions = env.get_affordance_positions()

        assert isinstance(positions, dict)
        assert "positions" in positions
        assert "ordering" in positions
        assert "position_dim" in positions

    def test_get_affordance_positions_has_correct_position_dim(self, cpu_env_factory):
        """Should include position_dim matching substrate."""
        env = cpu_env_factory()
        env.reset()

        checkpoint_data = env.get_affordance_positions()

        # Grid2D should have position_dim = 2
        assert checkpoint_data["position_dim"] == 2

    def test_get_affordance_positions_includes_all_affordances(self, cpu_env_factory):
        """Should include all affordances in positions dict."""
        env = cpu_env_factory()
        env.reset()

        checkpoint_data = env.get_affordance_positions()

        # Should have same affordances
        assert set(checkpoint_data["positions"].keys()) == set(env.affordances.keys())

    def test_get_affordance_positions_converts_to_lists(self, cpu_env_factory):
        """Should convert tensor positions to lists."""
        env = cpu_env_factory()
        env.reset()

        checkpoint_data = env.get_affordance_positions()

        # All positions should be lists
        for name, pos in checkpoint_data["positions"].items():
            assert isinstance(pos, list)


class TestSetAffordancePositions:
    """Test VectorizedHamletEnv.set_affordance_positions()."""

    def test_set_affordance_positions_updates_affordances(self, cpu_env_factory):
        """Should update affordance positions from checkpoint data."""
        env = cpu_env_factory()
        env.reset()

        # Get current positions
        original_checkpoint = env.get_affordance_positions()

        # Randomize positions
        env.randomize_affordance_positions()

        # Restore from checkpoint
        env.set_affordance_positions(original_checkpoint)

        # Positions should match original
        restored_checkpoint = env.get_affordance_positions()
        assert restored_checkpoint["positions"] == original_checkpoint["positions"]

    def test_set_affordance_positions_validates_position_dim(self, cpu_env_factory):
        """Should validate position_dim matches substrate."""
        env = cpu_env_factory()
        env.reset()

        # Create invalid checkpoint with wrong position_dim
        invalid_checkpoint = {
            "positions": {},
            "ordering": [],
            "position_dim": 3,  # Wrong! Should be 2 for Grid2D
        }

        with pytest.raises(ValueError, match="position_dim mismatch"):
            env.set_affordance_positions(invalid_checkpoint)


class TestRandomizeAffordancePositions:
    """Test VectorizedHamletEnv.randomize_affordance_positions()."""

    def test_randomize_affordance_positions_changes_positions(self, cpu_env_factory):
        """Should change affordance positions."""
        env = cpu_env_factory()
        env.reset()

        # Get current positions
        original_positions = env.get_affordance_positions()

        # Randomize
        env.randomize_affordance_positions()

        # Get new positions
        new_positions = env.get_affordance_positions()

        # At least some positions should change
        # (with 8x8 grid, very unlikely all stay the same)
        assert original_positions["positions"] != new_positions["positions"]

    def test_randomize_affordance_positions_maintains_affordance_count(self, cpu_env_factory):
        """Should keep same number of affordances."""
        env = cpu_env_factory()
        env.reset()

        original_count = len(env.affordances)

        env.randomize_affordance_positions()

        assert len(env.affordances) == original_count

    def test_randomize_affordance_positions_stays_in_bounds(self, cpu_env_factory):
        """Should keep all positions within grid bounds."""
        env = cpu_env_factory()
        grid_size = env.grid_size
        env.reset()

        env.randomize_affordance_positions()

        # All positions should be within [0, grid_size)
        for affordance_pos in env.affordances.values():
            assert torch.all(affordance_pos >= 0).item()
            assert torch.all(affordance_pos < grid_size).item()

    def test_static_affordance_positions_respected_when_randomization_disabled(
        self,
        tmp_path,
        test_config_pack_path: Path,
        env_factory,
        cpu_device,
    ):
        target = tmp_path / "static_positions_pack"
        shutil.copytree(test_config_pack_path, target)

        level_dir = target / "levels" / "L0_test"
        training_path = level_dir / "training.yaml"
        training_data = yaml.safe_load(training_path.read_text())
        training_block = training_data.setdefault("training", {})
        training_block["randomize_affordances"] = False
        training_block["enabled_affordances"] = ["EAT", "SLEEP"]
        training_path.write_text(yaml.safe_dump(training_data, sort_keys=False))

        env = env_factory(config_dir=target, num_agents=1, device_override=cpu_device)
        env.reset()

        assert env.randomize_affordances is False
        initial_positions = {name: pos.clone() for name, pos in env.affordances.items()}

        # Subsequent calls to randomize should no-op when disabled
        env.randomize_affordance_positions()
        for name, pos in initial_positions.items():
            assert torch.allclose(pos, env.affordances.get(name))


# =============================================================================
# END OF SPRINT 15 TESTS
# =============================================================================
