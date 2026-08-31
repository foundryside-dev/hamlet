#!/usr/bin/env python3
"""L2 pre-raster baseline harness (token-obs unit 3, hamlet-fa6bb6da4a).

Freezes the shipped-L2 feedforward training baseline BEFORE the token cut kills the
raster observation path (spec §6 unit 3). Reversal trigger 1 reads this baseline
forever: token networks must reach >= 80% of its final greedy survival within the
same env-step budget (seed-level IQM).

Phase-0 constraint: src/townlet/ is FROZEN. This script only drives shipped code.
The greedy evaluation it performs does not exist in the engine — the `evaluation:`
training.yaml block is declared-but-inert (zero runtime consumers, verified
2026-08-24) — so the measurement lives here, outside the engine.

Subcommands:
  train  --seed N --episodes E [--run-root runs/l2_baseline]
         Copy configs/default_curriculum with ONLY the L2 seed rewritten; run
         DemoRunner headlessly to E episodes. Refuses on a dirty src/townlet or a
         HEAD that differs from an existing run-root pin.
  eval   --run-dir <dir> [--episodes 100] [--eval-seed 12345]
         Greedy rollouts (argmax over masked Q, epsilon 0) from the run's latest
         checkpoint. Writes <run-dir>/greedy_eval.json.
  curves --run-dir <dir>
         Per-episode survival series (slot 0, from the run DB) plus cumulative
         per-agent env-step accounting (all agents, from TensorBoard events).
         Writes <run-dir>/curves.csv.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACK = REPO_ROOT / "configs" / "default_curriculum"
LEVEL = "L2_partial_observability"
MAX_STEPS_PER_EPISODE = 1000  # shipped L2 training_loop.max_steps_per_episode

sys.path.insert(0, str(REPO_ROOT / "src"))


# ---------------------------------------------------------------------------
# Pure functions (unit-tested in tests/test_townlet/unit/scripts/)
# ---------------------------------------------------------------------------


def rewrite_seed(pack_src: Path, pack_dst: Path, seed: int, level: str = LEVEL) -> str:
    """Copy a config pack, rewriting exactly the one `seed:` line of the level's
    training.yaml. Returns the unified diff of that file. Raises ValueError unless
    exactly one seed line was found (a silent zero-rewrite would freeze the wrong
    baseline)."""
    shutil.copytree(pack_src, pack_dst)
    cfg = pack_dst / "levels" / level / "training.yaml"
    old_lines = cfg.read_text().splitlines(keepends=True)
    seed_re = re.compile(r"^(\s*)seed:\s*\S+\s*$")
    new_lines: list[str] = []
    hits = 0
    for line in old_lines:
        m = seed_re.match(line)
        if m:
            hits += 1
            new_lines.append(f"{m.group(1)}seed: {seed}\n")
        else:
            new_lines.append(line)
    if hits != 1:
        raise ValueError(f"expected exactly one seed line in {cfg}, found {hits}")
    cfg.write_text("".join(new_lines))
    rel = str(cfg.relative_to(pack_dst))
    return "".join(difflib.unified_diff(old_lines, new_lines, fromfile=f"a/{rel}", tofile=f"b/{rel}"))


def iqm(values: list[float] | list[int]) -> float:
    """Interquartile mean: mean of the middle 50% (drop floor(n/4) from each tail).
    For n < 4 a quartile cannot be shed from each side; falls back to the mean."""
    xs = sorted(float(v) for v in values)
    n = len(xs)
    if n == 0:
        raise ValueError("iqm of empty sequence")
    if n < 4:
        return sum(xs) / n
    q = n // 4
    mid = xs[q : n - q]
    return sum(mid) / len(mid)


# ---------------------------------------------------------------------------
# train
# ---------------------------------------------------------------------------


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()


def cmd_train(args: argparse.Namespace) -> None:
    dirty = _git("status", "--porcelain", "src/townlet")
    if dirty:
        raise SystemExit(f"src/townlet is dirty — the baseline must run on committed code:\n{dirty}")
    head = _git("rev-parse", "HEAD")
    # The invariant is the ENGINE tree, not the commit: docs/test/plan commits
    # between seed launches are harmless; a moved src/townlet is not.
    src_tree = _git("rev-parse", "HEAD:src/townlet")

    run_root = Path(args.run_root)
    run_root.mkdir(parents=True, exist_ok=True)
    pin_file = run_root / "PIN"
    if pin_file.exists():
        pinned = pin_file.read_text().split()[0]
        if pinned != src_tree:
            raise SystemExit(
                f"run-root pinned to src/townlet tree {pinned[:12]} but HEAD carries {src_tree[:12]} — all seeds must share one engine tree"
            )
    else:
        pin_file.write_text(f"{src_tree} src-tree (head-at-first-seed {head})\n")

    run_dir = run_root / f"seed_{args.seed}"
    if run_dir.exists():
        raise SystemExit(f"{run_dir} already exists — refusing to overwrite a baseline run")
    run_dir.mkdir(parents=True)

    diff = rewrite_seed(PACK, run_dir / "pack", seed=args.seed)
    (run_dir / "pack.diff").write_text(diff)
    (run_dir / "meta.json").write_text(json.dumps({"seed": args.seed, "episodes": args.episodes, "pin": head, "level": LEVEL}, indent=2))

    from townlet.demo.runner import DemoRunner

    with DemoRunner(
        config_dir=run_dir / "pack",
        db_path=run_dir / "demo.db",
        checkpoint_dir=run_dir / "checkpoints",
        max_episodes=args.episodes,
        level_name=LEVEL,
    ) as runner:
        runner.run()
    print(f"[l2_baseline] seed {args.seed}: trained to {args.episodes} episodes in {run_dir}")


# ---------------------------------------------------------------------------
# eval
# ---------------------------------------------------------------------------


def cmd_eval(args: argparse.Namespace) -> None:
    import torch

    from townlet.demo.runner import DemoRunner
    from townlet.determinism import seed_all

    run_dir = Path(args.run_dir)
    meta = json.loads((run_dir / "meta.json").read_text())

    with DemoRunner(
        config_dir=run_dir / "pack",
        db_path=run_dir / "demo.db",
        checkpoint_dir=run_dir / "checkpoints",
        max_episodes=meta["episodes"],
        level_name=LEVEL,
    ) as runner:
        # run() builds env/population, load_checkpoint() restores the trained
        # weights, and the pre-loop shutdown check returns before any training
        # step — the shipped early-exit, not a private API.
        runner.should_shutdown = True
        runner.run()
        env = runner.env
        population = runner.population
        assert env is not None and population is not None
        if runner.current_episode == 0:
            raise SystemExit(f"no checkpoint restored from {run_dir / 'checkpoints'}")

        q_network = population.q_network
        q_network.eval()
        seed_all(args.eval_seed)

        num_agents = env.num_agents
        episodes: list[dict[str, int | list[int]]] = []
        for ep in range(args.episodes):
            obs = env.reset()
            alive = torch.ones(num_agents, dtype=torch.bool)
            steps = torch.zeros(num_agents, dtype=torch.long)
            for _t in range(MAX_STEPS_PER_EPISODE):
                with torch.no_grad():
                    q = q_network(obs)
                masks = env.get_action_masks()
                if masks.dtype != torch.bool:
                    masks = masks > 0.5
                q = q.masked_fill(~masks, float("-inf"))
                actions = q.argmax(dim=-1)
                obs, _rewards, dones, _info = env.step(actions)
                steps += alive.long()
                alive &= ~dones.detach().cpu().bool()
                if not alive.any():
                    break
            episodes.append({"episode": ep, "survival_steps": steps.tolist()})

        flat: list[int] = []
        for e in episodes:
            ss = e["survival_steps"]
            assert isinstance(ss, list)
            flat.extend(ss)
        result = {
            "run_dir": str(run_dir),
            "checkpoint_episode": runner.current_episode,
            "train_seed": meta["seed"],
            "eval_seed": args.eval_seed,
            "eval_episodes": args.episodes,
            "num_agents": num_agents,
            "episode_cap": MAX_STEPS_PER_EPISODE,
            "protocol": (
                "greedy: argmax over action-masked Q, epsilon 0, no learning; "
                "survival = env.step calls an agent was alive entering, capped; "
                "agents stay dead until the batch episode ends"
            ),
            "mean_survival": sum(flat) / len(flat),
            "median_survival": sorted(flat)[len(flat) // 2],
            "episodes": episodes,
        }
    out = run_dir / "greedy_eval.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"[l2_baseline] greedy eval: mean {result['mean_survival']:.1f} median {result['median_survival']} -> {out}")


# ---------------------------------------------------------------------------
# curves
# ---------------------------------------------------------------------------


def cmd_curves(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    conn = sqlite3.connect(run_dir / "demo.db")
    try:
        rows = conn.execute("SELECT episode_id, survival_time, epsilon, intrinsic_weight FROM episodes ORDER BY episode_id").fetchall()
    finally:
        conn.close()

    # Per-agent env-step accounting from TensorBoard events (the DB records slot 0
    # only). Tag layout: <agent_id>/Episode/Survival_Time per log_episode.
    per_episode_all_agents: dict[int, int] = {}
    try:
        from tensorboard.backend.event_processing.event_accumulator import (  # type: ignore[import-untyped]
            EventAccumulator,
        )

        # DemoRunner's layout rule: <run>/checkpoints under a runs/-rooted tree puts
        # TensorBoard at the checkpoint dir's SIBLING, <run>/tensorboard.
        tb_dir = run_dir / "tensorboard"
        if not tb_dir.exists():
            tb_dir = run_dir / "checkpoints" / "tensorboard"
        acc = EventAccumulator(str(tb_dir), size_guidance={"scalars": 0})
        acc.Reload()
        survival_tags = [t for t in acc.Tags().get("scalars", []) if t.endswith("Survival_Time")]
        for tag in survival_tags:
            for ev in acc.Scalars(tag):
                per_episode_all_agents[ev.step] = per_episode_all_agents.get(ev.step, 0) + int(ev.value)
    except Exception as exc:  # noqa: BLE001 — accounting degrades, curve stays
        print(f"[l2_baseline] WARNING: env-step accounting unavailable ({exc}); total_env_steps column will be empty")

    out = run_dir / "curves.csv"
    cumulative = 0
    with out.open("w") as f:
        f.write("episode,survival_steps_agent0,epsilon,intrinsic_weight,env_steps_all_agents,total_env_steps_cumulative\n")
        for episode_id, survival, epsilon, iw in rows:
            all_agents = per_episode_all_agents.get(episode_id, 0)
            cumulative += all_agents
            f.write(f"{episode_id},{survival},{epsilon:.6f},{iw:.6f},{all_agents},{cumulative if all_agents else ''}\n")
    print(f"[l2_baseline] curves: {len(rows)} episodes, {cumulative} total per-agent env steps -> {out}")


# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_train = sub.add_parser("train", help="train one baseline seed headlessly")
    p_train.add_argument("--seed", type=int, required=True)
    p_train.add_argument("--episodes", type=int, required=True)
    p_train.add_argument("--run-root", type=str, default="runs/l2_baseline")
    p_train.set_defaults(fn=cmd_train)

    p_eval = sub.add_parser("eval", help="greedy evaluation from the run's latest checkpoint")
    p_eval.add_argument("--run-dir", type=str, required=True)
    p_eval.add_argument("--episodes", type=int, default=100)
    p_eval.add_argument("--eval-seed", type=int, default=12345)
    p_eval.set_defaults(fn=cmd_eval)

    p_curves = sub.add_parser("curves", help="extract per-episode curves + env-step accounting")
    p_curves.add_argument("--run-dir", type=str, required=True)
    p_curves.set_defaults(fn=cmd_curves)

    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
