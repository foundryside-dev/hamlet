"""Harness for items-seam probes."""
from __future__ import annotations
import shutil, sys
from pathlib import Path
import torch
import yaml

REPO = Path("/home/john/hamlet")
SCR = Path("/tmp/claude-1000/-home-john-hamlet/7674c716-85c3-47ef-9259-6ef1cc884b42/scratchpad/items")
PACKS = SCR / "packs"
sys.path.insert(0, str(REPO / "src"))

from townlet.universe.compiler import UniverseCompiler  # noqa: E402
from townlet.environment.vectorized_env import VectorizedHamletEnv  # noqa: E402


def compile(pack_dir, level, num_agents=2):
    u = UniverseCompiler().compile(Path(pack_dir), primary_level=level, use_cache=False)
    env = VectorizedHamletEnv.from_universe(u, level_name=level, num_agents=num_agents, device="cpu")
    return u, env


def copy_pack(src, name, edits=None):
    """Copy pack to scratch; edits: {relpath: callable(dict)->dict}."""
    dst = PACKS / name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(REPO / src, dst, ignore=shutil.ignore_patterns(".compiled"))
    for rel, fn in (edits or {}).items():
        p = dst / rel
        data = yaml.safe_load(p.read_text())
        data = fn(data) or data
        p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    return dst


def layout(env):
    return env.token_spec.row_layout()


def rows(env, type_name, obs=None):
    """Return dict slot -> tensor [N, width] of rows for a token type."""
    if obs is None:
        obs = env._get_observations()
    out = {}
    for row in layout(env):
        t, slot, start, end = row[0], row[1], row[2], row[3]
        if t == type_name:
            out[slot] = obs[:, start:end]
    return out


def place(env, agent, xy):
    env.positions[agent] = torch.tensor(xy, dtype=env.positions.dtype)


def aid(env, name):
    return env.action_space.get_action_by_name(name).id


def act(env, names):
    actions = torch.tensor([aid(env, n) for n in names], dtype=torch.long)
    return env.step(actions)


def dyn_features(env, type_name):
    spec = env.token_spec
    tt = spec.get_type(type_name)
    return tt
