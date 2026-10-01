"""Integration tests for VFS runtime evaluation."""

import shutil
from pathlib import Path
from unittest.mock import patch

import torch
import yaml

from townlet.universe.compiler import UniverseCompiler
from townlet.vfs.evaluator import VFSEvaluator


def test_vfs_expressions_evaluated_at_runtime():
    """VFS expressions should be evaluated during environment step."""
    # Setup: Compile universe with VFS profiles
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "effects_smoke"

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_effects", use_cache=False)

    # Create environment
    env = compiled.create_environment(
        num_agents=4,
        level_name="L0_effects",
        device=torch.device("cpu"),
    )

    # Exercise: Step environment
    env.reset()
    obs, rewards, dones, info = env.step(torch.zeros(4, dtype=torch.long))

    # Verify: VFS variables should be in registry and updated
    # (day_count should increment each step if expression is "day_count + 1")
    assert hasattr(env, "vfs_registry")
    # Check that global VFS variables exist
    assert "day_count" in env.vfs_registry._storage or "day_count" in env.vfs_registry.variables


def test_mark_and_sweep_evaluates_unexposed_authored_expressions(tmp_path):
    """Expressions execute because they are state, independently of observation exposure."""
    config_dir = tmp_path / "world"
    shutil.copytree("configs/test/effects_smoke", config_dir)
    variables_path = config_dir / "variables.yaml"
    variables = yaml.safe_load(variables_path.read_text())
    day_count = next(variable for variable in variables["variables"]["declarations"] if variable["id"] == "day_count")
    day_count["expression"] = "tick"
    assert day_count["exposed_to"] == []
    variables_path.write_text(yaml.safe_dump(variables))

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_effects", use_cache=False)

    # Track which variables are evaluated
    evaluated_vars = []
    original_evaluate = VFSEvaluator.evaluate_global_profile

    def track_evaluation(self, profile, bars, vfs_state, marks=None, device=None, **kwargs):
        """Track which variables are evaluated."""
        result = original_evaluate(self, profile, bars, vfs_state, marks, device, **kwargs)
        if profile is compiled.compiled_vfs_profiles.global_profile:
            evaluated_vars.extend(result.keys())
        return result

    with patch.object(VFSEvaluator, "evaluate_global_profile", track_evaluation):
        # Create environment (default mode is mark-and-sweep)
        env = compiled.create_environment(
            num_agents=4,
            level_name="L0_effects",
            device=torch.device("cpu"),
        )

        # Exercise: Step environment
        env.reset()
        evaluated_vars.clear()  # Clear any evaluation from reset
        env.step(torch.zeros(4, dtype=torch.long))

    assert compiled.vfs_evaluation_marks is not None
    assert compiled.vfs_evaluation_marks["global"] == {"day_count"}
    assert set(evaluated_vars) == {"day_count"}


def test_eager_mode_evaluates_all_vars():
    """Eager mode should evaluate all VFS variables."""
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "vfs_dependency_chain"

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_deps", use_cache=False)

    evaluated_vars = []
    original_evaluate = VFSEvaluator.evaluate_global_profile

    def track_evaluation(self, profile, bars, vfs_state, marks=None, device=None, **kwargs):
        """Track which variables are evaluated."""
        result = original_evaluate(self, profile, bars, vfs_state, marks, device, **kwargs)
        if profile is compiled.compiled_vfs_profiles.global_profile:
            evaluated_vars.extend(result.keys())
        return result

    with patch.object(VFSEvaluator, "evaluate_global_profile", track_evaluation):
        env = compiled.create_environment(
            num_agents=4,
            level_name="L0_deps",
            device=torch.device("cpu"),
        )

        env.reset()
        evaluated_vars.clear()
        env.step(torch.zeros(4, dtype=torch.long))

    assert compiled.compiled_vfs_profiles is not None
    assert compiled.compiled_vfs_profiles.evaluation_mode == "eager"
    assert compiled.compiled_vfs_profiles.global_profile is not None
    all_vars = {var.name for var in compiled.compiled_vfs_profiles.global_profile.variables}
    assert set(evaluated_vars) == all_vars, f"Expected all vars {all_vars}, got {set(evaluated_vars)}"


def test_vfs_expression_dependency_chain():
    """VFS variables with complex dependency chains should evaluate correctly.

    Tests:
    - Multi-level dependencies (a → b → c)
    - Expression reuse across variables
    - Eager evaluation includes static inputs as well as derived variables
    """
    # Setup: Use vfs_dependency_chain which has dependency chains
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "vfs_dependency_chain"

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_deps", use_cache=False)

    # Create environment
    env = compiled.create_environment(
        num_agents=4,
        level_name="L0_deps",
        device=torch.device("cpu"),
    )

    # Exercise: Reset and step environment
    env.reset()
    obs, rewards, dones, info = env.step(torch.zeros(4, dtype=torch.long))

    # Verify: Registry exists and has variables
    assert hasattr(env, "vfs_registry")

    # Verify values: a = 10 (initial_value), b = a + 5 = 15, c = b * 2 = 30
    assert "a" in env.vfs_registry._storage, "Variable 'a' not found in registry"
    assert "b" in env.vfs_registry._storage, "Variable 'b' not found in registry"
    assert "c" in env.vfs_registry._storage, "Variable 'c' not found in registry"

    a_value = env.vfs_registry._storage["a"]
    b_value = env.vfs_registry._storage["b"]
    c_value = env.vfs_registry._storage["c"]

    # Global VFS variables are scalar tensors (shape [])
    assert a_value.item() == 10.0, f"Expected a=10.0, got {a_value.item()}"
    assert b_value.item() == 15.0, f"Expected b=15.0, got {b_value.item()}"
    assert c_value.item() == 30.0, f"Expected c=30.0, got {c_value.item()}"


def test_vfs_expressions_access_bars():
    """VFS expressions should be able to read bar values.

    Tests:
    - VFS variable depends on bar.energy
    - Bar values change during step
    - VFS expression reflects updated bar values
    """
    # Setup: Use config with VFS var that reads bar.energy
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "vfs_bar_access"

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_bars", use_cache=False)

    # Create environment
    env = compiled.create_environment(
        num_agents=4,
        level_name="L0_bars",
        device=torch.device("cpu"),
    )

    # Exercise: Reset environment
    env.reset()

    # Verify registry exists
    assert hasattr(env, "vfs_registry")
    assert "low_energy_flag" in env.vfs_registry._storage, "Variable 'low_energy_flag' not found in registry"

    # Test 1: Set energy to high value (0.8 > 0.3)
    # Manually set bars (simulating high energy)
    energy_idx = env.meter_name_to_index["energy"]
    env.meters[:, energy_idx] = torch.tensor([0.8, 0.8, 0.8, 0.8], device=env.device)
    env.step(torch.zeros(4, dtype=torch.long))

    # Verify: low_energy_flag should be False (energy > 0.3)
    low_energy_flag = env.vfs_registry._storage["low_energy_flag"]
    assert low_energy_flag.dtype == torch.bool, f"Expected bool type, got {low_energy_flag.dtype}"
    # low_energy_flag is agent-scoped (hamlet-d970ef83f0 / token-obs unit 3 Task 5b — a
    # bar.energy-derived expression is inherently per-agent, so the variable is declared
    # agent scope, not global). [num_agents] is the DECLARED shape here, not a bypass.
    # low_energy_flag = bar.energy < 0.3 -> [0.8, 0.8, 0.8, 0.8] < 0.3 -> [False, False, False, False]
    assert low_energy_flag.shape == (4,), f"Expected shape [4], got {low_energy_flag.shape}"
    assert torch.all(~low_energy_flag), f"Expected all False when energy=0.8, got {low_energy_flag}"

    # Test 2: Set energy to low value (0.2 < 0.3)
    env.meters[:, energy_idx] = torch.tensor([0.2, 0.2, 0.2, 0.2], device=env.device)
    env.step(torch.zeros(4, dtype=torch.long))

    # Verify: low_energy_flag should be True (energy < 0.3)
    low_energy_flag = env.vfs_registry._storage["low_energy_flag"]
    assert torch.all(low_energy_flag), f"Expected all True when energy=0.2, got {low_energy_flag}"

    # Test 3: Mixed energy values
    env.meters[:, energy_idx] = torch.tensor([0.1, 0.5, 0.2, 0.9], device=env.device)
    env.step(torch.zeros(4, dtype=torch.long))

    # Verify: low_energy_flag should match per-agent energy levels
    low_energy_flag = env.vfs_registry._storage["low_energy_flag"]
    expected = torch.tensor([True, False, True, False])  # [0.1<0.3, 0.5<0.3, 0.2<0.3, 0.9<0.3]
    assert torch.equal(low_energy_flag, expected), f"Expected {expected} when energy=[0.1,0.5,0.2,0.9], got {low_energy_flag}"
