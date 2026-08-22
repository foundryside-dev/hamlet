"""hamlet-df3a96bbac: expressions evaluate on the shipped default shape —
mark_and_sweep, no variables_reference.yaml."""

from __future__ import annotations

import torch
import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


def _make_env(tmp_path, profile_payload, num_agents=2):
    config_dir = prepare_config_dir(tmp_path)
    (config_dir / "vfs_profiles.yaml").write_text(yaml.safe_dump(profile_payload))
    ref = config_dir / "variables_reference.yaml"
    if ref.exists():
        ref.unlink()  # the shipped-default shape: NO overlay file
    u = UniverseCompiler().compile(config_dir, primary_level=PRIMARY_LEVEL_NAME)
    env = u.create_environment(num_agents=num_agents, level_name=PRIMARY_LEVEL_NAME, device="cpu")
    env.reset()
    return env


_PROFILES = {
    "version": "1.0", "evaluation_mode": "mark_and_sweep", "debug_logging": False,
    "global_profile": {"variables": [
        {"semantic_type": "custom", "name": "stash", "type": "float", "initial_value": 1.0},
        {"semantic_type": "custom", "name": "tick_echo", "type": "float", "expression": "tick * 2.0"},
    ]},
    "agent_profile": None,
    "item_profiles": [{"profile_name": "default_item", "variables": []}],
}


def _global_value(env, name) -> float:
    return float(env.vfs_registry.get(name, reader="engine").reshape(-1)[0])


def test_global_expression_advances_under_mark_and_sweep_default(tmp_path):
    env = _make_env(tmp_path, _PROFILES)
    for _ in range(3):
        env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))
    # evaluator ran at tick k-1 on the last step (pre-increment) — the value MOVED,
    # which is the whole ticket; pin the exact phase relation:
    assert _global_value(env, "tick_echo") == 2.0 * (env.global_tick - 1)


def test_static_survives_engine_write_unclobbered(tmp_path):
    env = _make_env(tmp_path, _PROFILES)
    env.vfs_registry.set_engine_value("stash", torch.tensor(7.0))
    env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))
    assert _global_value(env, "stash") == 7.0  # statics are storage, never re-evaluated


_DEPENDENCY_PROFILES = {
    "version": "1.0", "evaluation_mode": "mark_and_sweep", "debug_logging": False,
    "global_profile": {"variables": [
        {"semantic_type": "custom", "name": "base", "type": "float", "initial_value": 1.0},
        {"semantic_type": "custom", "name": "derived", "type": "float", "expression": "base + 1.0"},
    ]},
    "agent_profile": None,
    "item_profiles": [{"profile_name": "default_item", "variables": []}],
}


def test_static_dependency_of_marked_expression_is_not_clobbered_by_write_back(tmp_path):
    """hamlet-df3a96bbac regression: only `derived` is marked (expression, exposed_to
    defaults to ["agent"]); `base` is a static dependency the evaluator chases via
    add_with_deps and re-emits at its INITIAL value. The write-back loop must skip
    that re-emitted static rather than clobber an engine write with it — while still
    letting the dependency chase feed the evaluation of `derived` itself.
    """
    env = _make_env(tmp_path, _DEPENDENCY_PROFILES)
    env.vfs_registry.set_engine_value("base", torch.tensor(99.0))
    env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))
    assert _global_value(env, "base") == 99.0  # static write-back skipped, not clobbered to 1.0
    assert _global_value(env, "derived") == 100.0  # evaluated FROM the engine-written base
