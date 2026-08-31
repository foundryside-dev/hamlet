#!/usr/bin/env python3
"""Reproducible CPU benchmark for compact token observation encoding."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

import torch

from townlet.determinism import seed_all
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler


def _positive(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _non_negative(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--level", required=True)
    parser.add_argument("--agents", type=_positive, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--warmup", type=_non_negative, required=True)
    parser.add_argument("--iterations", type=_positive, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _reset_if_terminal(env: VectorizedHamletEnv, dones: torch.Tensor) -> None:
    if bool(dones.any()):
        env.reset()


def main() -> int:
    args = _parse_args()
    torch.set_num_threads(1)
    seed_all(args.seed)

    device = torch.device("cpu")
    universe = UniverseCompiler().compile(args.config, primary_level=args.level, use_cache=False)
    env = VectorizedHamletEnv(
        universe=universe,
        level_name=args.level,
        num_agents=args.agents,
        device=device,
    )
    env.reset()
    wait_actions = torch.full(
        (args.agents,),
        env.action_ids["WAIT"],
        dtype=torch.long,
        device=device,
    )

    for _ in range(args.warmup):
        _, _, dones, _ = env.step(wait_actions)
        _reset_if_terminal(env, dones)

    observation_samples: list[int] = []
    for _ in range(args.iterations):
        started = time.perf_counter_ns()
        env._get_observations()
        observation_samples.append(time.perf_counter_ns() - started)

    step_samples: list[int] = []
    for _ in range(args.iterations):
        started = time.perf_counter_ns()
        _, _, dones, _ = env.step(wait_actions)
        step_samples.append(time.perf_counter_ns() - started)
        _reset_if_terminal(env, dones)

    median_observation_ns = statistics.median(observation_samples)
    median_step_ns = statistics.median(step_samples)
    encoding_ratio = median_observation_ns / median_step_ns
    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "agents": args.agents,
        "commit": _git("rev-parse", "HEAD"),
        "config": str(args.config),
        "cpu": platform.processor() or platform.machine(),
        "denominator": median_step_ns,
        "dirty": bool(_git("status", "--porcelain")),
        "encoding_ratio": encoding_ratio,
        "iterations": args.iterations,
        "level": args.level,
        "median_observation_ns": median_observation_ns,
        "median_step_ns": median_step_ns,
        "numerator": median_observation_ns,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "seed": args.seed,
        "thread_count": torch.get_num_threads(),
        "torch_version": torch.__version__,
        "warmup": args.warmup,
    }
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    output.write_text(f"{rendered}\n", encoding="utf-8")
    sys.stdout.write(f"{rendered}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
