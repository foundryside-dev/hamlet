"""hamlet-df3a96bbac: expressions evaluate on the shipped default shape —
mark_and_sweep with canonical variable declarations."""

from __future__ import annotations

import pytest
import torch
import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError


def _make_env(tmp_path, profile_payload, num_agents=2):
    config_dir = prepare_config_dir(tmp_path)
    (config_dir / "variables.yaml").write_text(yaml.safe_dump(profile_payload))
    u = UniverseCompiler().compile(config_dir, primary_level=PRIMARY_LEVEL_NAME)
    env = u.create_environment(num_agents=num_agents, level_name=PRIMARY_LEVEL_NAME, device="cpu")
    env.reset()
    return env


_PROFILES = {
    "variables": {
        "version": "1.0",
        "item_profiles": ["default_item"],
        "declarations": [
            {
                "readable_by": ["engine", "agent"],
                "writable_by": ["engine"],
                "id": "stash",
                "scope": "global",
                "type": "scalar",
                "lifetime": "persistent",
                "semantic_type": "custom",
                "initial_value": 1.0,
                "exposed_to": [],
            },
            {
                "readable_by": ["engine", "agent"],
                "writable_by": ["engine"],
                "id": "tick_echo",
                "scope": "global",
                "type": "scalar",
                "lifetime": "persistent",
                "semantic_type": "custom",
                "initial_value": 0.0,
                "exposed_to": [],
                "expression": "tick * 2.0",
            },
        ],
    }
}


def _global_value(env, name) -> float:
    return float(env.vfs_registry.get(name, reader="engine").reshape(-1)[0])


def test_global_expression_advances_under_mark_and_sweep_default(tmp_path):
    env = _make_env(tmp_path, _PROFILES)
    for _ in range(3):
        env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))
    # The value MOVED, which is the whole ticket; pin the exact phase relation: the
    # evaluator runs after the clock advance, at the instant the observation describes.
    assert _global_value(env, "tick_echo") == 2.0 * env.global_tick


def test_static_survives_engine_write_unclobbered(tmp_path):
    env = _make_env(tmp_path, _PROFILES)
    env.vfs_registry.set_engine_value("stash", torch.tensor(7.0))
    env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))
    assert _global_value(env, "stash") == 7.0  # statics are storage, never re-evaluated


_DEPENDENCY_PROFILES = {
    "variables": {
        "version": "1.0",
        "item_profiles": ["default_item"],
        "declarations": [
            {
                "readable_by": ["engine", "agent"],
                "writable_by": ["engine"],
                "id": "base",
                "scope": "global",
                "type": "scalar",
                "lifetime": "persistent",
                "semantic_type": "custom",
                "initial_value": 1.0,
                "exposed_to": [],
            },
            {
                "readable_by": ["engine", "agent"],
                "writable_by": ["engine"],
                "id": "derived",
                "scope": "global",
                "type": "scalar",
                "lifetime": "persistent",
                "semantic_type": "custom",
                "initial_value": 0.0,
                "exposed_to": [],
                "expression": "base + 1.0",
            },
        ],
    }
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


# --- Task 6 (hamlet-5d74335111): agent-profile evaluation gets the second call site ---

_AGENT_PROFILES = {
    "variables": {
        "version": "1.0",
        "item_profiles": ["default_item"],
        "declarations": [
            {
                "readable_by": ["engine", "agent"],
                "writable_by": ["engine"],
                "id": "wealth_static",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "semantic_type": "custom",
                "initial_value": 1.0,
                "exposed_to": [],
            },
            {
                "readable_by": ["engine", "agent"],
                "writable_by": ["engine"],
                "id": "low_energy",
                "scope": "agent",
                "type": "bool",
                "lifetime": "episode",
                "semantic_type": "custom",
                "initial_value": False,
                "exposed_to": [],
                "expression": "bar.energy < 2.0",
            },
        ],
    }
}


def test_agent_expression_evaluates_per_agent(tmp_path):
    env = _make_env(tmp_path, _AGENT_PROFILES)
    env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))
    value = env.vfs_registry.get("low_energy", reader="engine")
    assert value.shape[0] == env.num_agents
    # bars are normalized [0,1] in this engine, so energy < 2.0 is true for every agent —
    # the assertion is that the expression RAN and wrote per-agent, not its economics:
    assert bool(value.reshape(-1).all())


def test_agent_static_is_never_clobbered(tmp_path):
    env = _make_env(tmp_path, _AGENT_PROFILES)
    env.vfs_registry.set_engine_value("wealth_static", torch.full((env.num_agents,), 9.0))
    env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))
    assert float(env.vfs_registry.get("wealth_static", reader="engine").reshape(-1)[0]) == 9.0


_AGENT_DEPENDENCY_PROFILES = {
    "variables": {
        "version": "1.0",
        "item_profiles": ["default_item"],
        "declarations": [
            {
                "readable_by": ["engine", "agent"],
                "writable_by": ["engine"],
                "id": "base",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "semantic_type": "custom",
                "initial_value": 1.0,
                "exposed_to": [],
            },
            {
                "readable_by": ["engine", "agent"],
                "writable_by": ["engine"],
                "id": "derived",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "semantic_type": "custom",
                "initial_value": 0.0,
                "exposed_to": [],
                "expression": "base + 1.0",
            },
        ],
    }
}


def test_agent_static_dependency_of_marked_expression_is_not_clobbered_by_write_back(tmp_path):
    """Agent-scope mirror of the global regression above (Task 5 fix-round amendment
    obligation 2): `base` is a static dependency of the marked expression `derived` —
    the evaluator's dependency chase re-emits `base` at its compile-time initial value
    in `result`, and reusing evaluate_global_profile means the agent write-back loop
    must apply the SAME expression-only filter or it clobbers the engine-written
    per-agent `base` with that scalar initial on every step.
    """
    env = _make_env(tmp_path, _AGENT_DEPENDENCY_PROFILES)
    engine_base = torch.tensor([10.0, 20.0][: env.num_agents])
    env.vfs_registry.set_engine_value("base", engine_base)
    env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))
    base_value = env.vfs_registry.get("base", reader="engine").reshape(-1)
    derived_value = env.vfs_registry.get("derived", reader="engine").reshape(-1)
    assert torch.allclose(base_value, engine_base)  # static write-back skipped, not clobbered to 1.0
    assert torch.allclose(derived_value, engine_base + 1.0)  # evaluated FROM the engine-written base


_AGENT_SCALAR_EXPRESSION_PROFILES = {
    "variables": {
        "version": "1.0",
        "item_profiles": ["default_item"],
        "declarations": [
            {
                "readable_by": ["engine", "agent"],
                "writable_by": ["engine"],
                "id": "scalar_expr",
                "scope": "agent",
                "type": "scalar",
                "lifetime": "episode",
                "semantic_type": "custom",
                "initial_value": 0.0,
                "exposed_to": [],
                "expression": "tick * 2.0",
            }
        ],
    }
}


def test_agent_expression_wrong_shape_raises_naming_variable_and_shapes(tmp_path):
    with pytest.raises(CompilationError, match="scalar_expr.*shape"):
        _make_env(tmp_path, _AGENT_SCALAR_EXPRESSION_PROFILES)


# --- review-2026-10-24 F3: statics are storage. The deleted eager evaluator rebuilt
# expression context from each static's declared literal, so an expression over an
# engine-written static was permanently stale. Mark-and-sweep is the only path. ---

_STATIC_INPUT_PROFILES = {
    "variables": {
        "version": "1.0",
        "item_profiles": ["default_item"],
        "declarations": [
            {
                "readable_by": ["engine", "agent"],
                "writable_by": ["engine"],
                "id": "stash",
                "scope": "global",
                "type": "scalar",
                "lifetime": "persistent",
                "semantic_type": "custom",
                "initial_value": 1.0,
                "exposed_to": [],
            },
            {
                "readable_by": ["engine", "agent"],
                "writable_by": ["engine"],
                "id": "stash_twice",
                "scope": "global",
                "type": "scalar",
                "lifetime": "persistent",
                "semantic_type": "custom",
                "initial_value": 0.0,
                "exposed_to": [],
                "expression": "stash * 2.0",
            },
        ],
    }
}


def test_static_survives_engine_write_and_feeds_dependents_its_runtime_value(tmp_path):
    """The write-back filter keeps an engine-written static unclobbered, and the expression
    that depends on it reads the written value, never the declared literal 1.0."""
    env = _make_env(tmp_path, _STATIC_INPUT_PROFILES)
    env.vfs_registry.set_engine_value("stash", torch.tensor(7.0))
    env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))
    assert _global_value(env, "stash") == 7.0
    assert _global_value(env, "stash_twice") == 14.0
