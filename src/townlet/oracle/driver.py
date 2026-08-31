"""The injected trace producer for the differential harness.

SELF-CONTAINED BY RULE: this file is executed by file path in BOTH sides'
interpreters — including the frozen oracle worktree, where townlet.oracle does
not exist. It may import stdlib, numpy, torch, and townlet modules present at
the oracle tag ONLY. It must never reference the oracle module (pinned by
test_driver_source_is_self_contained).

The trace file it writes is format_version 4, matching trace_io.py exactly
(keys: obs, rewards, dones, actions, meta; meta carries params, hashes,
code_root, pack_root, and action_source). trace_io.py cannot be imported here
(same rule), so the two modules' TRACE_FORMAT_VERSION constants and meta shape
are kept in sync by hand — see FIX 5, WS-7 fix wave 2. The pairing is pinned by
the Task 5 integration test.

--pack-root exists because the oracle pins CODE and must also pin its INPUTS
(hamlet-2090c9f16d). Every pack DTO is extra="forbid", so a key added to a
live pack makes the frozen oracle reject it at Stage 1 and every cell crashes
for a schema reason rather than yielding a verdict. Each side therefore
resolves the SAME logical --pack against its OWN root. --pack stays logical
because it is part of RunParams, which compare_traces requires to be equal
across sides; the resolved root is recorded beside code_root instead, where
it is reported but never compared.

Recipe mirrors tests/test_townlet/integration/test_determinism.py::_trace_hash,
the recipe whose determinism is verified CPU + CUDA at the tag (PDR-0030).
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sys
import traceback
from pathlib import Path

import numpy as np
import torch

import townlet
from townlet.determinism import seed_all
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

TRACE_FORMAT_VERSION = 4


def collect_provenance_hashes(universe: object, level_metadata: object) -> dict[str, str | None]:
    """Collect shared and selected-level ``*_hash`` provenance fields.

    Reflection rather than a hardcoded list lets each side report its own hash
    surface. The selected level is authoritative for per-level hashes; shared
    experiment hashes remain on the outer compiled universe.
    """
    shared_hashes = {
        field.name: getattr(universe, field.name)
        for field in dataclasses.fields(universe)  # type: ignore[arg-type]
        if field.name.endswith("_hash")
    }
    selected_level_hashes = {
        field.name: getattr(level_metadata, field.name)
        for field in dataclasses.fields(level_metadata)  # type: ignore[arg-type]
        if field.name.endswith("_hash")
    }
    return shared_hashes | selected_level_hashes


def run_trace(
    *,
    pack: str,
    pack_root: str,
    level: str,
    num_agents: int,
    steps: int,
    seed: int,
    device: str,
    out: Path,
    actions_path: Path | None = None,
) -> None:
    """Produce one differential-harness trace.

    actions_path: None IS the declared seeded-random mode (actions are drawn
    from torch.randint each step) — it is not a fallback for a missing file.
    Passing a path selects scripted mode: the npz at that path must hold an
    integer "actions" array of shape (steps, num_agents) with every value in
    [0, env.action_dim), and those actions are stepped verbatim in order.
    seed_all(seed) still runs in scripted mode — env internals may consume
    RNG independently of the action draw.
    """
    # `pack` is LOGICAL (part of RunParams, compared across sides); `pack_root`
    # is this side's resolution root and is reported, never compared.
    resolved_pack = (Path(pack_root) / pack).resolve()
    universe = UniverseCompiler().compile(resolved_pack, primary_level=level, use_cache=False)
    level_metadata = universe.get_level(level)
    seed_all(seed)
    env = VectorizedHamletEnv(universe=universe, level_name=level, num_agents=num_agents, device=torch.device(device))

    scripted: np.ndarray | None = None
    if actions_path is not None:
        with np.load(actions_path, allow_pickle=False) as data:
            if "actions" not in data:
                raise ValueError(f"actions file {actions_path} has no 'actions' array")
            scripted = np.asarray(data["actions"])
        if scripted.shape != (steps, num_agents):
            raise ValueError(f"actions shape {scripted.shape} != declared (steps={steps}, num_agents={num_agents})")
        if not np.issubdtype(scripted.dtype, np.integer):
            raise ValueError(f"actions dtype {scripted.dtype} is not integer")
        if scripted.min() < 0 or scripted.max() >= env.action_dim:
            raise ValueError(
                f"actions contain values outside [0, action_dim={env.action_dim}): " f"min={int(scripted.min())}, max={int(scripted.max())}"
            )

    obs = env.reset()
    obs_frames = [obs.cpu().numpy().copy()]
    reward_frames: list[np.ndarray] = []
    done_frames: list[np.ndarray] = []
    action_frames: list[np.ndarray] = []
    for t in range(steps):
        if scripted is None:
            # Actions drawn on CPU so the stream is device-independent, then
            # moved to the env device — same as the verified determinism recipe.
            actions = torch.randint(0, env.action_dim, (env.num_agents,)).to(env.device)
        else:
            actions = torch.from_numpy(scripted[t].astype(np.int64)).to(env.device)
        action_frames.append(actions.cpu().numpy().astype(np.int64).copy())
        obs, rewards, dones, _ = env.step(actions)
        obs_frames.append(obs.cpu().numpy().copy())
        reward_frames.append(rewards.cpu().numpy().copy())
        done_frames.append(dones.cpu().numpy().copy())

    meta = {
        "format_version": TRACE_FORMAT_VERSION,
        "params": {
            "pack": pack,
            "level": level,
            "num_agents": num_agents,
            "steps": steps,
            "seed": seed,
            "device": device,
        },
        "hashes": collect_provenance_hashes(universe, level_metadata),
        # The resolved src root this process actually imported townlet from —
        # derived from the imported package itself, NOT from __file__ of this
        # driver script (which is the same injected new-tree file on both
        # sides regardless of which PYTHONPATH was set). Lets the harness
        # detect a PYTHONPATH injection that silently failed to take effect
        # (FIX 5): if it did, both sides would import the same working-tree
        # townlet and every cell would trivially — and falsely — AGREE.
        "code_root": str(Path(townlet.__file__).resolve().parent.parent),
        # The pack root this side actually read its config from. Sibling of
        # code_root and, like it, excluded from compare_traces: the two sides
        # resolve different roots BY DESIGN once a pack-schema divergence is
        # declared. Recorded so the choice is never silent.
        "pack_root": str(Path(pack_root).resolve()),
        "action_source": (
            "seeded-random" if scripted is None else "scripted:" + hashlib.sha256(scripted.astype(np.int64).tobytes()).hexdigest()[:16]
        ),
    }
    np.savez_compressed(
        out,
        obs=np.stack(obs_frames).astype(np.float32),
        rewards=np.stack(reward_frames).astype(np.float32),
        dones=np.stack(done_frames).astype(bool),
        actions=np.stack(action_frames).astype(np.int64),
        meta=np.array(json.dumps(meta)),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Produce one differential-harness trace.")
    parser.add_argument("--pack", required=True, help="logical pack path, resolved against --pack-root")
    parser.add_argument("--pack-root", required=True, help="this side's config root (the oracle side reads frozen fixtures)")
    parser.add_argument("--level", required=True)
    parser.add_argument("--num-agents", type=int, required=True)
    parser.add_argument("--steps", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--device", required=True, choices=("cpu", "cuda"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--actions", type=Path, default=None, help="npz with an 'actions' array to replay verbatim (scripted mode)")
    args = parser.parse_args(argv)
    try:
        run_trace(
            pack=args.pack,
            pack_root=args.pack_root,
            level=args.level,
            num_agents=args.num_agents,
            steps=args.steps,
            seed=args.seed,
            device=args.device,
            out=args.out,
            actions_path=args.actions,
        )
    except Exception:  # noqa: BLE001 — boundary: full traceback to stderr, nonzero exit
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
