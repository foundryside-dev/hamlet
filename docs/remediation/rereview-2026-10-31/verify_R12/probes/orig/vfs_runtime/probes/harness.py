"""Probe harness: clone the static_epistemic_access witness, patch, compile, build env."""

from __future__ import annotations

import shutil
import sys
import traceback
from pathlib import Path

import torch
import yaml

REPO = Path("/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/verify_R12/wt")
BASE = REPO / "configs" / "static_epistemic_access"
PACKS = Path(__file__).resolve().parent / "packs"
PACKS.mkdir(exist_ok=True)

sys.path.insert(0, str(REPO / "src"))


def load_yaml(path: Path):
    with open(path) as fh:
        return yaml.safe_load(fh)


def dump_yaml(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        yaml.safe_dump(payload, fh, sort_keys=False)


def make_pack(name: str, *, variables=None, actions=None, affordances=None, extra_files=None, base: Path = BASE) -> Path:
    """Copy the base pack; `variables` / `actions` / `affordances` are callables that mutate the loaded YAML."""
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
    if affordances is not None:
        path = dest / "levels" / "L0_simple" / "affordances.yaml"
        payload = load_yaml(path)
        affordances(payload["affordances"])
        dump_yaml(path, payload)
    for rel, payload in (extra_files or {}).items():
        dump_yaml(dest / rel, payload)
    return dest


def compile_pack(path: Path, level: str = "L0_simple"):
    from townlet.universe.compiler import UniverseCompiler

    return UniverseCompiler().compile(path, primary_level=level)


def build_env(universe, num_agents: int = 2, level: str = "L0_simple"):
    from townlet.environment.vectorized_env import VectorizedHamletEnv

    env = VectorizedHamletEnv.from_universe(universe, level_name=level, num_agents=num_agents, device="cpu")
    env.reset()
    return env


def action_index(env, name: str) -> int:
    for idx, action in enumerate(env.action_space.actions):
        if action.name == name:
            return idx
    raise KeyError(f"{name} not in {[a.name for a in env.action_space.actions]}")


def decl(id, scope="agent", type="scalar", lifetime="episode", semantic_type="custom", readable=("engine", "agent"),
         writable=("engine",), exposed=(), initial_value=0.0, **extra):
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


def write(variable_id, expression, phase="apply_completion_bonuses", composition="additive_delta", condition=None,
          priority=0, clamp=None, telemetry_label=None):
    return {
        "variable_id": variable_id,
        "expression": expression,
        "condition": condition,
        "composition": composition,
        "phase": phase,
        "priority": priority,
        "clamp": clamp,
        "telemetry_label": telemetry_label or f"w_{variable_id}",
    }


MINMAX = {"kind": "minmax", "min": 0.0, "max": 10.0, "clip": True}


def probe(label):
    """Decorator: run a probe, print PASS/FAIL header and traceback on exception."""

    def wrap(fn):
        def run(*a, **k):
            print(f"\n===== {label} =====")
            try:
                return fn(*a, **k)
            except Exception as exc:  # noqa: BLE001
                print(f"EXC {type(exc).__name__}: {str(exc)[:1500]}")
                if "--tb" in sys.argv:
                    traceback.print_exc()
                return exc

        return run

    return wrap


def reg(env, name):
    return env.vfs_registry.get(name, reader="engine")


def step(env, action_name=None, actions=None):
    if actions is None:
        actions = torch.full((env.num_agents,), action_index(env, action_name), dtype=torch.long)
    return env.step(actions)


def make_pack_from(name: str, base: Path, mutate=None) -> Path:
    """Copy any base pack to PACKS/name; `mutate(dest)` edits files in place."""
    dest = PACKS / name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(base, dest, ignore=shutil.ignore_patterns(".compiled"))
    if mutate is not None:
        mutate(dest)
    return dest


def edit_yaml(path: Path, fn):
    payload = load_yaml(path)
    fn(payload)
    dump_yaml(path, payload)


def ve_rows(env, obs, agent=None):
    """Map variable_element filler_ref -> compact row values (agent row `agent`, or all agents)."""
    spec = env.token_spec
    vt = spec.get_type("variable_element")
    out = {}
    for (ttype, slot, start, end) in spec.row_layout():
        if ttype != "variable_element":
            continue
        ref = vt.slot_bindings[slot].filler_ref
        if agent is None:
            out[ref] = [[round(v, 4) for v in obs[a, start:end].tolist()] for a in range(obs.shape[0])]
        else:
            out[ref] = [round(v, 4) for v in obs[agent, start:end].tolist()]
    return out


def type_rows(env, obs, type_name, agent=0):
    spec = env.token_spec
    out = []
    for (ttype, slot, start, end) in spec.row_layout():
        if ttype == type_name:
            out.append((slot, [round(v, 4) for v in obs[agent, start:end].tolist()]))
    return out
