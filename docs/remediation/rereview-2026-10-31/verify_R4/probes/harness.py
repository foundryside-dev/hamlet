"""Authoring-lens harness: clone default_curriculum at 559dd0f9 (worktree), patch, compile, step."""

from __future__ import annotations

import os
import shutil
import sys
import traceback
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

HERE = Path(__file__).resolve().parent
WT = Path(os.environ.get("WT", str(HERE.parent / "wt"))).resolve()
assert (WT / "src" / "townlet").is_dir(), WT
sys.path.insert(0, str(WT / "src"))

import torch  # noqa: E402
import yaml  # noqa: E402

BASE = WT / "configs" / "default_curriculum"
LEVEL = "L1_full_observability"
PACKS = HERE / ("packs_" + WT.name)
PACKS.mkdir(exist_ok=True)


def load_yaml(path: Path):
    with open(path) as fh:
        return yaml.safe_load(fh)


def dump_yaml(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        yaml.safe_dump(payload, fh, sort_keys=False)


def make_pack(
    name: str,
    *,
    variables=None,
    actions=None,
    affordances=None,
    curriculum=None,
    bars=None,
    drive=None,
    rules=None,
    effects=None,
    extra_files=None,
    base: Path = BASE,
    level: str = LEVEL,
) -> Path:
    """Copy the base pack; callables mutate the loaded YAML payload (inner mapping); `rules` is a
    list of transition rules written to a pack-root transition_rules.yaml."""
    dest = PACKS / name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(base, dest, ignore=shutil.ignore_patterns(".compiled"))
    if variables is not None:
        payload = load_yaml(dest / "variables.yaml")
        variables(payload["variables"])
        dump_yaml(dest / "variables.yaml", payload)
    if actions is not None:
        payload = load_yaml(dest / "actions.yaml")
        actions(payload["actions"])
        dump_yaml(dest / "actions.yaml", payload)
    if effects is not None:
        payload = load_yaml(dest / "effects.yaml")
        effects(payload)
        dump_yaml(dest / "effects.yaml", payload)
    lvl = dest / "levels" / level
    if affordances is not None:
        payload = load_yaml(lvl / "affordances.yaml")
        affordances(payload["affordances"])
        dump_yaml(lvl / "affordances.yaml", payload)
    if curriculum is not None:
        payload = load_yaml(lvl / "curriculum.yaml")
        curriculum(payload["curriculum"])
        dump_yaml(lvl / "curriculum.yaml", payload)
    if bars is not None:
        payload = load_yaml(lvl / "bars.yaml")
        bars(payload["bars"])
        dump_yaml(lvl / "bars.yaml", payload)
    if drive is not None:
        payload = load_yaml(lvl / "drive.yaml")
        drive(payload["drive"])
        dump_yaml(lvl / "drive.yaml", payload)
    if rules is not None:
        dump_yaml(dest / "transition_rules.yaml", {"version": "1.0", "transition_rules": rules})
    for rel, payload in (extra_files or {}).items():
        dump_yaml(dest / rel, payload)
    return dest


def compile_pack(path: Path, level: str = LEVEL):
    from townlet.universe.compiler import UniverseCompiler

    return UniverseCompiler().compile(path, primary_level=level, use_cache=False)


def try_compile(path: Path, level: str = LEVEL):
    """Return (universe, None) or (None, 'ExcType: message')."""
    try:
        return compile_pack(path, level), None
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"


def build_env(universe, num_agents: int = 2, level: str = LEVEL):
    from townlet.environment.vectorized_env import VectorizedHamletEnv

    env = VectorizedHamletEnv.from_universe(universe, level_name=level, num_agents=num_agents, device="cpu")
    env.reset()
    return env


def action_index(env, name: str) -> int:
    for idx, action in enumerate(env.action_space.actions):
        if action.name == name:
            return idx
    raise KeyError(f"{name} not in {[a.name for a in env.action_space.actions]}")


def step(env, names):
    """Step with one action name per agent (or one name for all)."""
    n = env.num_agents
    if isinstance(names, str):
        names = [names] * n
    acts = torch.tensor([action_index(env, nm) for nm in names], dtype=torch.long)
    return env.step(acts)


def reg(env, name):
    return env.vfs_registry.get(name, reader="engine")


def meter(env, name):
    return env.meters[:, env.meter_name_to_index[name]]


def decl(
    id,
    scope="agent",
    type="scalar",
    lifetime="episode",
    semantic_type="custom",
    readable=("engine", "agent"),
    writable=("engine",),
    exposed=(),
    initial_value=0.0,
    **extra,
):
    d = {
        "id": id,
        "scope": scope,
        "type": type,
        "lifetime": lifetime,
        "semantic_type": semantic_type,
        "readable_by": list(readable),
        "writable_by": list(writable),
        "exposed_to": list(exposed),
    }
    if "initial_value_mode" not in extra:
        d["initial_value"] = initial_value
    d.update(extra)
    return d


def write(
    variable_id,
    expression,
    phase="apply_completion_bonuses",
    composition="additive_delta",
    condition=None,
    priority=0,
    clamp=None,
    telemetry_label=None,
):
    return {
        "variable_id": variable_id,
        "expression": expression,
        "condition": condition,
        "composition": composition,
        "phase": phase,
        "priority": priority,
        "clamp": clamp,
        "telemetry_label": telemetry_label or f"w_{variable_id.replace('.', '_')}",
    }


def rule(id, writes, phase="apply_transition_rules", condition=None):
    return {"id": id, "phase": phase, "condition": condition, "writes": writes}


def rwrite(variable_id, expression, composition="additive_delta", condition=None, clamp=None, effect=None):
    return {
        "variable_id": variable_id,
        "expression": expression,
        "composition": composition,
        "condition": condition,
        "clamp": clamp,
        "effect": effect,
    }


def add_action(actions_payload, name, writes, source_affordance=None, description="probe"):
    entry = {"name": name, "description": description, "enabled_by_default": True, "writes": writes}
    if source_affordance is not None:
        entry["source_affordance"] = source_affordance
    actions_payload["custom_actions"].append(entry)


MINMAX = {"kind": "minmax", "min": 0.0, "max": 10.0, "clip": True}
MINMAX01 = {"kind": "minmax", "min": 0.0, "max": 1.0, "clip": True}


def probe(label):
    def wrap(fn):
        def run(*a, **k):
            print(f"\n===== {label} =====", flush=True)
            try:
                return fn(*a, **k)
            except Exception:  # noqa: BLE001
                print("EXCEPTION:")
                traceback.print_exc()
                return None

        return run

    return wrap


def short(msg: str, n: int = 400) -> str:
    return msg if len(msg) <= n else msg[:n] + "..."
