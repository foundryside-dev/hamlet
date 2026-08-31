#!/usr/bin/env python3
"""M4 equal-step L2 token feedforward/recurrent engineering check.

The frozen denominator is ``docs/product/baselines/2026-08-l2-preraster``.
Every candidate cell uses representative seed 45 and that baseline run's exact
summed-live-agent transition budget. Seed 45 is the shortest and lowest-scoring
member of the frozen cohort, so it is the strictest cheap deterministic engineering
check. A vector environment step is indivisible: if its live lanes would exceed the
remaining budget, training stops before that step and records the shortfall. A run
is budget-compliant when that conservative shortfall is at most ``num_agents - 1``;
exact equality is reported separately.

Brain widths are never synthesized here. ``--brain-template`` is a required,
complete ``brain.yaml`` whose architecture and aggregator must match the cell.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import math
import platform
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import torch
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PACK = REPO_ROOT / "configs" / "default_curriculum"
LEVEL = "L2_partial_observability"
MAX_STEPS_PER_EPISODE = 1000

sys.path.insert(0, str(REPO_ROOT / "src"))

from townlet.determinism import seed_all  # noqa: E402

ARCHITECTURES = ("token_feedforward", "token_recurrent")
AGGREGATORS = ("mean", "attention")
REPRESENTATIVE_SEED = 45
SEEDS = (REPRESENTATIVE_SEED,)
BASELINE_ENV_STEP_BUDGETS = {
    42: 3_322_056,
    43: 3_112_832,
    44: 3_314_536,
    45: 2_278_640,
    46: 2_286_816,
}
BASELINE_SEED_MEANS = {
    42: 98.9975,
    43: 98.9975,
    44: 98.985,
    45: 98.83,
    46: 99.91125,
}
BASELINE_IQM = 98.99333333333334
ACCEPTANCE_THRESHOLD = 79.19466666666668
BUDGET_STOP_RULE = "stop_before_vector_step"


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()


def require_clean_acceptance_inputs() -> dict[str, str]:
    """Return committed protocol identities or refuse any dirty acceptance input."""
    dirty = _git(
        "status",
        "--porcelain",
        "--untracked-files=all",
        "--",
        "src/townlet",
        "scripts/l2_token_regression.py",
        "configs/benchmarks/l2_token_regression",
    )
    if dirty:
        raise SystemExit(f"acceptance inputs are dirty — commit the engine, harness, and M4 templates before running:\n{dirty}")
    return {
        "git_sha": _git("rev-parse", "HEAD"),
        "src_tree": _git("rev-parse", "HEAD:src/townlet"),
        "harness_blob": _git("rev-parse", "HEAD:scripts/l2_token_regression.py"),
        "brain_templates_tree": _git("rev-parse", "HEAD:configs/benchmarks/l2_token_regression"),
    }


def validate_brain_template(path: Path, *, architecture: str, aggregator: str) -> dict[str, Any]:
    """Validate a complete caller-supplied brain template against its matrix cell."""
    if architecture not in ARCHITECTURES:
        raise ValueError(f"unknown architecture {architecture!r}; expected one of {ARCHITECTURES}")
    if aggregator not in AGGREGATORS:
        raise ValueError(f"unknown aggregator {aggregator!r}; expected one of {AGGREGATORS}")
    if not path.is_file():
        raise FileNotFoundError(path)
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict) or not isinstance(raw.get("architecture"), dict):
        raise ValueError(f"{path} must contain an architecture mapping")
    architecture_block = cast(dict[str, Any], raw["architecture"])
    expected_type = "token_set" if architecture == "token_feedforward" else "recurrent"
    actual_type = architecture_block.get("type")
    if actual_type != expected_type:
        raise ValueError(f"{architecture} requires architecture.type {expected_type!r}; template declares {actual_type!r}")
    typed_block = architecture_block.get(expected_type)
    if not isinstance(typed_block, dict) or not isinstance(typed_block.get("aggregator"), dict):
        raise ValueError(f"{path} architecture.{expected_type}.aggregator must be declared")
    actual_aggregator = typed_block["aggregator"].get("type")
    if actual_aggregator != aggregator:
        raise ValueError(f"aggregator mismatch: cell requires {aggregator!r}; template declares {actual_aggregator!r}")
    return raw


def run_directory(run_root: Path, architecture: str, aggregator: str, seed: int) -> Path:
    return run_root / f"{architecture}-{aggregator}" / f"seed_{seed}"


def _pin_run_root(run_root: Path, *, identity: dict[str, str]) -> None:
    run_root.mkdir(parents=True, exist_ok=True)
    pin_path = run_root / "PIN"
    if pin_path.exists():
        pinned = json.loads(pin_path.read_text())
        if pinned != identity:
            raise SystemExit(
                "run root is pinned to different acceptance inputs — all M4 cells must share the exact "
                "engine tree, harness blob, and committed template tree"
            )
    else:
        pin_path.write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n")


def _rewrite_seed(pack: Path, seed: int) -> str:
    config_path = pack / "levels" / LEVEL / "training.yaml"
    old_lines = config_path.read_text().splitlines(keepends=True)
    new_lines: list[str] = []
    hits = 0
    for line in old_lines:
        if line.lstrip().startswith("seed:"):
            indent = line[: len(line) - len(line.lstrip())]
            new_lines.append(f"{indent}seed: {seed}\n")
            hits += 1
        else:
            new_lines.append(line)
    if hits != 1:
        raise ValueError(f"expected exactly one seed line in {config_path}, found {hits}")
    config_path.write_text("".join(new_lines))
    relative = config_path.relative_to(pack)
    return "".join(difflib.unified_diff(old_lines, new_lines, fromfile=f"a/{relative}", tofile=f"b/{relative}"))


def _install_brain_template(pack: Path, template: Path) -> str:
    destination = pack / "levels" / LEVEL / "brain.yaml"
    destination.parent.mkdir(parents=True, exist_ok=True)
    new_lines = template.read_text().splitlines(keepends=True)
    destination.write_text("".join(new_lines))
    relative = destination.relative_to(pack)
    return "".join(difflib.unified_diff([], new_lines, fromfile="/dev/null", tofile=f"b/{relative}"))


def _hardware_metadata() -> dict[str, Any]:
    devices = []
    if torch.cuda.is_available():
        for index in range(torch.cuda.device_count()):
            properties = torch.cuda.get_device_properties(index)
            devices.append({"index": index, "name": properties.name, "total_memory_bytes": properties.total_memory})
    return {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "platform": platform.platform(),
        "cuda_visible_devices": devices,
    }


def validate_resume_run(
    run_dir: Path,
    *,
    identity: dict[str, str],
    brain_template: Path,
    architecture: str,
    aggregator: str,
    seed: int,
    budget: int,
) -> dict[str, Any]:
    """Validate that an existing run is the exact unfinished cohort member requested."""
    meta_path = run_dir / "meta.json"
    if not meta_path.is_file() or not (run_dir / "pack").is_dir():
        raise FileNotFoundError(f"resume requires the existing run metadata and pack: {meta_path}, {run_dir / 'pack'}")
    if (run_dir / "greedy_eval.json").exists():
        raise ValueError(f"{run_dir} already has greedy_eval.json and is not an unfinished training run")
    if not any((run_dir / "checkpoints").glob("checkpoint_ep*.pt")):
        raise FileNotFoundError(f"resume requires a checkpoint under {run_dir / 'checkpoints'}")

    metadata = json.loads(meta_path.read_text())
    expected: dict[str, Any] = {
        "format": "l2-token-regression-1",
        "architecture": architecture,
        "aggregator": aggregator,
        "seed": seed,
        "level": LEVEL,
        "requested_live_agent_steps": budget,
        "budget_stop_rule": BUDGET_STOP_RULE,
        **identity,
        "brain_template_sha256": hashlib.sha256(brain_template.read_bytes()).hexdigest(),
    }
    for key, value in expected.items():
        if metadata.get(key) != value:
            raise ValueError(f"{meta_path}: {key}={metadata.get(key)!r}, expected {value!r}")
    return cast(dict[str, Any], metadata)


def prepare_run(
    *, run_root: Path, brain_template: Path, architecture: str, aggregator: str, seed: int, budget: int, resume: bool = False
) -> tuple[Path, dict[str, Any]]:
    if seed not in SEEDS:
        raise ValueError(f"seed must be one of {SEEDS}")
    expected_budget = BASELINE_ENV_STEP_BUDGETS[seed]
    if budget != expected_budget:
        raise ValueError(f"seed {seed} requires the frozen budget {expected_budget}; got {budget}")
    validate_brain_template(brain_template, architecture=architecture, aggregator=aggregator)
    identity = require_clean_acceptance_inputs()
    _pin_run_root(run_root, identity=identity)
    run_dir = run_directory(run_root, architecture, aggregator, seed)
    if run_dir.exists():
        if not resume:
            raise FileExistsError(f"{run_dir} already exists — pass --resume for a validated continuation")
        return run_dir, validate_resume_run(
            run_dir,
            identity=identity,
            brain_template=brain_template,
            architecture=architecture,
            aggregator=aggregator,
            seed=seed,
            budget=budget,
        )
    if resume:
        raise FileNotFoundError(f"{run_dir} does not exist — --resume never creates a new run")
    run_dir.mkdir(parents=True)
    pack = run_dir / "pack"
    shutil.copytree(PACK, pack)
    shutil.rmtree(pack / ".compiled", ignore_errors=True)
    seed_diff = _rewrite_seed(pack, seed)
    brain_diff = _install_brain_template(pack, brain_template)
    (run_dir / "pack.diff").write_text(seed_diff + brain_diff)
    template_bytes = brain_template.read_bytes()
    metadata: dict[str, Any] = {
        "format": "l2-token-regression-1",
        "architecture": architecture,
        "aggregator": aggregator,
        "seed": seed,
        "level": LEVEL,
        "requested_live_agent_steps": budget,
        "budget_stop_rule": BUDGET_STOP_RULE,
        **identity,
        "brain_template": str(brain_template.resolve()),
        "brain_template_sha256": hashlib.sha256(template_bytes).hexdigest(),
        "hardware": _hardware_metadata(),
    }
    (run_dir / "meta.json").write_text(json.dumps(metadata, indent=2, sort_keys=True))
    return run_dir, metadata


def runtime_model_metadata(runner: Any) -> dict[str, int | str | None]:
    """Capture the instantiated network and compiler-owned identity surfaces."""
    if runner.population is None:
        raise RuntimeError("population must be initialized before capturing model metadata")
    level = runner.compiled.get_level(runner.level_name)
    return {
        "parameter_count": sum(parameter.numel() for parameter in runner.population.q_network.parameters()),
        "compiled_brain_hash": runner.compiled.brain_hash,
        "compiled_pack_brain_hash": runner.compiled.pack_brain_hash,
        "compiled_token_type_schema_hash": level.token_type_schema_hash,
        "compiled_token_layout_hash": level.layout_hash,
        "compiled_observation_schema_hash": level.observation_schema_hash,
    }


def normalized_train_command(args: argparse.Namespace) -> list[str]:
    command = [
        "uv",
        "run",
        "python",
        str(REPO_ROOT / "scripts" / "l2_token_regression.py"),
        "train",
        "--architecture",
        args.architecture,
        "--aggregator",
        args.aggregator,
        "--brain-template",
        str(Path(args.brain_template).resolve()),
        "--seed",
        str(args.seed),
        "--env-step-budget",
        str(args.env_step_budget),
        "--run-root",
        str(Path(args.run_root).resolve()),
    ]
    if args.resume:
        command.append("--resume")
    return command


def begin_training_attempt(metadata: dict[str, Any], args: argparse.Namespace, *, argv: list[str], started_at: str) -> dict[str, Any]:
    """Append one auditable training attempt while preserving the cohort start."""
    command = normalized_train_command(args)
    attempt = {
        "started_at": started_at,
        "finished_at": None,
        "duration_seconds": None,
        "resume": bool(args.resume),
        "argv": list(argv),
        "normalized_command": command,
    }
    metadata.setdefault("training_started_at", started_at)
    metadata.setdefault("training_attempts", []).append(attempt)
    metadata["train_argv"] = list(argv)
    metadata["normalized_train_command"] = command
    return attempt


def finish_training_attempt(
    metadata: dict[str, Any],
    attempt: dict[str, Any],
    *,
    finished_at: str,
    duration_seconds: float,
    completed: bool,
) -> None:
    attempt["finished_at"] = finished_at
    attempt["duration_seconds"] = duration_seconds
    metadata["duration_seconds"] = float(metadata.get("duration_seconds", 0.0)) + duration_seconds
    if completed:
        metadata["training_finished_at"] = finished_at
    else:
        metadata.pop("training_finished_at", None)


def require_budget_complete_for_eval(metadata: dict[str, Any], run_dir: Path) -> None:
    requested = metadata.get("requested_live_agent_steps")
    realized = metadata.get("realized_live_agent_steps")
    if (
        not isinstance(requested, int)
        or isinstance(requested, bool)
        or not isinstance(realized, int)
        or isinstance(realized, bool)
        or not 0 <= requested - realized <= 7
    ):
        raise SystemExit(f"{run_dir} is not budget-complete; resume training first (requested={requested}, realized={realized})")


def cmd_train(args: argparse.Namespace) -> None:
    run_dir, metadata = prepare_run(
        run_root=Path(args.run_root),
        brain_template=Path(args.brain_template),
        architecture=args.architecture,
        aggregator=args.aggregator,
        seed=args.seed,
        budget=args.env_step_budget,
        resume=args.resume,
    )
    from townlet.demo.runner import DemoRunner

    started_at = datetime.now(UTC).isoformat()
    started_clock = time.monotonic()
    attempt = begin_training_attempt(metadata, args, argv=list(sys.argv), started_at=started_at)
    (run_dir / "meta.json").write_text(json.dumps(metadata, indent=2, sort_keys=True))
    completed = False
    try:
        with DemoRunner(
            config_dir=run_dir / "pack",
            db_path=run_dir / "demo.db",
            checkpoint_dir=run_dir / "checkpoints",
            max_episodes=None,
            level_name=LEVEL,
            max_environment_steps=args.env_step_budget,
        ) as runner:
            runner.run()
            metadata.update(runtime_model_metadata(runner))
            realized = runner.completed_live_agent_steps
            shortfall = args.env_step_budget - realized
            completed = 0 <= shortfall <= runner.population.num_agents - 1
            metadata.update(
                {
                    "realized_live_agent_steps": realized,
                    "budget_shortfall": shortfall,
                    "budget_exact": shortfall == 0,
                    "budget_compliant": completed,
                    "completed_episodes": runner.current_episode,
                }
            )
    finally:
        finish_training_attempt(
            metadata,
            attempt,
            finished_at=datetime.now(UTC).isoformat(),
            duration_seconds=time.monotonic() - started_clock,
            completed=completed,
        )
        (run_dir / "meta.json").write_text(json.dumps(metadata, indent=2, sort_keys=True))

    # The frozen artifact includes the per-episode curve and cumulative all-agent
    # transition accounting. Reuse its exact extractor rather than fork the metric.
    from scripts.l2_baseline import cmd_curves

    cmd_curves(argparse.Namespace(run_dir=str(run_dir)))
    print(
        f"[l2_token_regression] {args.architecture}/{args.aggregator} seed {args.seed}: "
        f"{realized}/{args.env_step_budget} live-agent steps -> {run_dir}"
    )


def cmd_eval(args: argparse.Namespace) -> None:
    from townlet.demo.runner import DemoRunner

    run_dir = Path(args.run_dir)
    metadata = json.loads((run_dir / "meta.json").read_text())
    require_budget_complete_for_eval(metadata, run_dir)
    if (run_dir / "greedy_eval.json").exists():
        raise FileExistsError(f"{run_dir / 'greedy_eval.json'} already exists — refusing to overwrite evaluation evidence")
    with DemoRunner(
        config_dir=run_dir / "pack",
        db_path=run_dir / "demo.db",
        checkpoint_dir=run_dir / "checkpoints",
        max_episodes=None,
        level_name=LEVEL,
    ) as runner:
        runner.should_shutdown = True
        runner.run()
        env = runner.env
        population = runner.population
        assert env is not None and population is not None
        if runner.current_episode == 0:
            raise SystemExit(f"no checkpoint restored from {run_dir / 'checkpoints'}")
        network = population.q_network
        network.eval()
        seed_all(args.eval_seed)
        num_agents = env.num_agents
        episodes: list[dict[str, int | list[int]]] = []
        for episode in range(args.episodes):
            observations = env.reset()
            alive = torch.ones(num_agents, dtype=torch.bool)
            hidden = network.initial_hidden(num_agents, env.device) if population.is_recurrent else None
            steps = torch.zeros(num_agents, dtype=torch.long)
            for _ in range(MAX_STEPS_PER_EPISODE):
                with torch.no_grad():
                    if population.is_recurrent:
                        assert hidden is not None
                        q_sequence, hidden = network(observations.unsqueeze(1), hidden)
                        q_values = q_sequence[:, 0, :]
                    else:
                        q_values = network(observations)
                action_masks = env.get_action_masks()
                if action_masks.dtype != torch.bool:
                    action_masks = action_masks > 0.5
                actions = q_values.masked_fill(~action_masks, float("-inf")).argmax(dim=-1)
                observations, _rewards, dones, _info = env.step(actions)
                steps += alive.long()
                alive &= ~dones.detach().cpu().bool()
                if not alive.any():
                    break
            episodes.append({"episode": episode, "survival_steps": steps.tolist()})

        flat = [step for episode in episodes for step in cast(list[int], episode["survival_steps"])]
        result = {
            "run_dir": str(run_dir),
            "checkpoint_episode": runner.current_episode,
            "train_seed": metadata["seed"],
            "architecture": metadata["architecture"],
            "aggregator": metadata["aggregator"],
            "eval_seed": args.eval_seed,
            "eval_episodes": args.episodes,
            "num_agents": num_agents,
            "episode_cap": MAX_STEPS_PER_EPISODE,
            "protocol": (
                "greedy: argmax over action-masked Q, epsilon 0, no learning; recurrent hidden state "
                "starts at zero per episode and threads across its steps; survival = env.step calls an "
                "agent was alive entering, capped; agents stay dead until the batch episode ends"
            ),
            "mean_survival": sum(flat) / len(flat),
            "median_survival": sorted(flat)[len(flat) // 2],
            "episodes": episodes,
        }
    output = run_dir / "greedy_eval.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(f"[l2_token_regression] greedy eval mean={result['mean_survival']:.6f} median={result['median_survival']} -> {output}")


def _read_seed_result(run_root: Path, architecture: str, aggregator: str, seed: int) -> dict[str, Any]:
    run_dir = run_directory(run_root, architecture, aggregator, seed)
    meta_path = run_dir / "meta.json"
    eval_path = run_dir / "greedy_eval.json"
    if not meta_path.is_file() or not eval_path.is_file():
        raise FileNotFoundError(f"missing M4 artifacts for {architecture}-{aggregator}/seed_{seed}: {meta_path}, {eval_path}")
    metadata = json.loads(meta_path.read_text())
    evaluation = json.loads(eval_path.read_text())
    expected = {
        "architecture": architecture,
        "aggregator": aggregator,
        "seed": seed,
        "requested_live_agent_steps": BASELINE_ENV_STEP_BUDGETS[seed],
        "budget_stop_rule": BUDGET_STOP_RULE,
    }
    for key, value in expected.items():
        if metadata.get(key) != value:
            raise ValueError(f"{meta_path}: {key}={metadata.get(key)!r}, expected {value!r}")
    if evaluation.get("train_seed") != seed or evaluation.get("eval_seed") != 12345:
        raise ValueError(f"{eval_path}: seed contract mismatch")
    if evaluation.get("eval_episodes") != 100 or evaluation.get("num_agents") != 8 or evaluation.get("episode_cap") != 1000:
        raise ValueError(f"{eval_path}: greedy evaluation protocol mismatch")
    mean = evaluation.get("mean_survival")
    if not isinstance(mean, (int, float)) or isinstance(mean, bool) or not math.isfinite(mean):
        raise ValueError(f"{eval_path}: mean_survival must be finite")
    episodes = evaluation.get("episodes")
    if not isinstance(episodes, list) or len(episodes) != 100:
        raise ValueError(f"{eval_path}: episodes must contain the 100 raw evaluation episodes")
    raw_steps: list[int] = []
    for episode_index, episode in enumerate(episodes):
        if not isinstance(episode, dict) or episode.get("episode") != episode_index:
            raise ValueError(f"{eval_path}: episodes[{episode_index}] has an invalid episode index")
        survival_steps = episode.get("survival_steps")
        if not isinstance(survival_steps, list) or len(survival_steps) != 8:
            raise ValueError(f"{eval_path}: episodes[{episode_index}].survival_steps must contain eight agents")
        if any(not isinstance(step, int) or isinstance(step, bool) or not 0 <= step <= MAX_STEPS_PER_EPISODE for step in survival_steps):
            raise ValueError(f"{eval_path}: episodes[{episode_index}].survival_steps contains an invalid value")
        raw_steps.extend(cast(list[int], survival_steps))
    raw_mean = sum(raw_steps) / len(raw_steps)
    if float(mean) != raw_mean:
        raise ValueError(f"{eval_path}: mean_survival={mean!r} does not match raw episodes mean {raw_mean!r}")
    realized = metadata.get("realized_live_agent_steps")
    if not isinstance(realized, int) or isinstance(realized, bool):
        raise ValueError(f"{meta_path}: realized_live_agent_steps must be an integer")
    parameter_count = metadata.get("parameter_count")
    if not isinstance(parameter_count, int) or isinstance(parameter_count, bool) or parameter_count <= 0:
        raise ValueError(f"{meta_path}: parameter_count must be a positive integer")
    identity_keys = (
        "git_sha",
        "src_tree",
        "harness_blob",
        "brain_templates_tree",
        "brain_template_sha256",
        "compiled_brain_hash",
        "compiled_pack_brain_hash",
        "compiled_token_type_schema_hash",
        "compiled_token_layout_hash",
        "compiled_observation_schema_hash",
    )
    for key in identity_keys:
        if not isinstance(metadata.get(key), str) or not metadata[key]:
            raise ValueError(f"{meta_path}: {key} must be a non-empty string")
    shortfall = BASELINE_ENV_STEP_BUDGETS[seed] - realized
    # No partial vector steps: at eight agents, a compliant conservative stop
    # can leave at most seven transitions unused and can never overshoot.
    budget_compliant = 0 <= shortfall <= 7
    return {
        "seed": seed,
        "requested_live_agent_steps": metadata["requested_live_agent_steps"],
        "realized_live_agent_steps": realized,
        "budget_shortfall": shortfall,
        "budget_exact": shortfall == 0,
        "budget_compliant": budget_compliant,
        "mean_survival": float(mean),
        "parameter_count": parameter_count,
        **{key: metadata[key] for key in identity_keys},
        "run_dir": str(run_dir),
    }


def _one_identity(rows: list[dict[str, Any]], key: str, *, context: str) -> Any:
    values = {row[key] for row in rows}
    if len(values) != 1:
        raise ValueError(f"{key} differs across {context}: {sorted(values, key=repr)!r}")
    return next(iter(values))


def summarize_results(run_root: Path) -> dict[str, Any]:
    cells: list[dict[str, Any]] = []
    for architecture in ARCHITECTURES:
        for aggregator in AGGREGATORS:
            seeds = [_read_seed_result(run_root, architecture, aggregator, seed) for seed in SEEDS]
            score = seeds[0]["mean_survival"]
            score_passed = score >= ACCEPTANCE_THRESHOLD
            budget_exact = all(row["budget_exact"] for row in seeds)
            budget_compliant = all(row["budget_compliant"] for row in seeds)
            model_identity_keys = (
                "parameter_count",
                "brain_template_sha256",
                "compiled_brain_hash",
                "compiled_token_type_schema_hash",
                "compiled_token_layout_hash",
                "compiled_observation_schema_hash",
            )
            model_identity = {key: _one_identity(seeds, key, context=f"{architecture}/{aggregator} seeds") for key in model_identity_keys}
            cells.append(
                {
                    "architecture": architecture,
                    "aggregator": aggregator,
                    "seeds": seeds,
                    "greedy_mean_survival": score,
                    "score_passed": score_passed,
                    "budget_exact": budget_exact,
                    "budget_compliant": budget_compliant,
                    "passed": score_passed and budget_compliant,
                    "model_identity": model_identity,
                }
            )
    all_seed_rows = [seed for cell in cells for seed in cell["seeds"]]
    cohort_identity_keys = (
        "git_sha",
        "src_tree",
        "harness_blob",
        "brain_templates_tree",
        "compiled_pack_brain_hash",
        "compiled_token_type_schema_hash",
        "compiled_token_layout_hash",
        "compiled_observation_schema_hash",
    )
    cohort_identity = {key: _one_identity(all_seed_rows, key, context="the M4 cohort") for key in cohort_identity_keys}
    return {
        "format": "l2-token-engineering-summary-1",
        "representative_seed": REPRESENTATIVE_SEED,
        "baseline_seed_means": BASELINE_SEED_MEANS,
        "baseline_iqm": BASELINE_IQM,
        "acceptance_threshold": ACCEPTANCE_THRESHOLD,
        "budget_stop_rule": BUDGET_STOP_RULE,
        "cohort_identity": cohort_identity,
        "cells": cells,
        "all_cells_passed": all(cell["passed"] for cell in cells),
    }


def cmd_summarize(args: argparse.Namespace) -> None:
    result = summarize_results(Path(args.run_root))
    output = Path(args.output) if args.output else Path(args.run_root) / "summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))
    print(f"[l2_token_regression] summary -> {output}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    train = subparsers.add_parser("train", help="train one exact-budget M4 cell/seed")
    train.add_argument("--architecture", required=True, choices=ARCHITECTURES)
    train.add_argument("--aggregator", required=True, choices=AGGREGATORS)
    train.add_argument("--brain-template", required=True)
    train.add_argument("--seed", required=True, type=int, choices=SEEDS)
    train.add_argument("--env-step-budget", required=True, type=int)
    train.add_argument("--run-root", default="runs/l2_token_regression")
    train.add_argument("--resume", action="store_true", help="continue the exact matching unfinished run from its latest checkpoint")
    train.set_defaults(function=cmd_train)

    evaluate = subparsers.add_parser("eval", help="run the frozen greedy protocol")
    evaluate.add_argument("--run-dir", required=True)
    evaluate.add_argument("--episodes", type=int, default=100)
    evaluate.add_argument("--eval-seed", type=int, default=12345)
    evaluate.set_defaults(function=cmd_eval)

    summarize = subparsers.add_parser("summarize", help="summarize the four representative-seed engineering cells")
    summarize.add_argument("--run-root", default="runs/l2_token_regression")
    summarize.add_argument("--output")
    summarize.set_defaults(function=cmd_summarize)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.function(args)


if __name__ == "__main__":
    main()
