"""Capture real lifecycle paths and compare a complete, exact coordinate contract.

The producer is deliberately external to the selected source tree. It does not
import fixture helpers or candidate packages into a preserved parent process.
Controlled recipes disable RND; learner/predictor qualification is separate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ReadingKey = tuple[str, str, int, int, str]
RECIPES = ("authored-two-five", "passive-two-five", "death-at-lifespan", "healthy-retirement", "two-episodes-reset", "budget-six")
FIELDS = frozenset(
    {
        "actions",
        "observations",
        "meters",
        "dones",
        "rewards",
        "step_counts",
        "global_tick",
        "time_of_day",
        "ledger_active",
        "ledger_terminal",
        "ledger_counts",
        "ledger_terminal_counts",
        "ledger_live_transitions",
        "active_on_entry",
        "newly_terminal",
        "newly_retired",
        "extrinsic",
        "intrinsic",
        "shaping",
        "intrinsic_weight",
        "initial_energy",
        "reset_observations",
        "reset_meters",
        "reset_dones",
        "reset_counts",
        "reset_global_tick",
        "population_counts",
        "population_completed",
        "population_total_steps",
        "population_training_steps",
        "completion_reason",
        "completion_survival",
        "completion_observation",
        "completion_meters",
        "reset_population_counts",
        "reset_population_completed",
        "reset_completion_reason",
        "reset_completion_survival",
        "runner_live_transitions",
        "runner_budget_reached",
        "runner_budget_shortfall",
        "runner_episode_count",
        "selected_q_values",
        "replay_size",
        "admitted_observation",
        "eligible_observation",
    }
)
COORDINATES = frozenset({"value", "present", "dtype", "shape", "sha256"})
TICK_TENSORS = {
    "actions": True,
    "observations": True,
    "meters": True,
    "dones": True,
    "rewards": True,
    "step_counts": False,
    "ledger_active": False,
    "ledger_terminal": False,
    "ledger_counts": False,
    "ledger_terminal_counts": False,
    "active_on_entry": False,
    "newly_terminal": False,
    "newly_retired": False,
    "intrinsic_weight": True,
    "extrinsic": True,
    "intrinsic": True,
    "shaping": True,
}


def expected_inventory(recipe: str) -> set[ReadingKey]:
    result: set[ReadingKey] = set()

    def scalar(field: str, tick: int, agent: int, coordinate: str) -> None:
        result.add((recipe, field, tick, agent, coordinate))

    def tensor(field: str, tick: int, hashed: bool) -> None:
        for coordinate in ("present", "dtype", "shape"):
            scalar(field, tick, -1, coordinate)
        for agent in range(2):
            scalar(field, tick, agent, "value")
            if hashed:
                scalar(field, tick, agent, "sha256")

    population = recipe in {"authored-two-five", "two-episodes-reset", "budget-six"}
    episodes = 2 if recipe == "two-episodes-reset" else 1
    for episode in range(episodes + 1):
        offset = episode * 100
        for field in ("reset_observations", "reset_meters", "reset_dones", "reset_counts"):
            tensor(field, offset, True)
        scalar("reset_global_tick", offset, -1, "value")
        tensor("initial_energy", offset, False)
        if population:
            for field in ("reset_population_counts", "reset_population_completed"):
                tensor(field, offset, False)
            for agent in range(2):
                for field in ("reset_completion_reason", "reset_completion_survival"):
                    scalar(field, offset, agent, "value")
        if episode == episodes:
            continue
        for tick in range(1, 5 if recipe == "budget-six" else 6):
            for field, hashed in TICK_TENSORS.items():
                tensor(field, offset + tick, hashed)
            for field in ("global_tick", "time_of_day", "ledger_live_transitions"):
                scalar(field, offset + tick, -1, "value")
            for agent in range(2):
                scalar("eligible_observation", offset + tick, agent, "value")
                if population:
                    scalar("admitted_observation", offset + tick, agent, "value")
            if population:
                tensor("selected_q_values", offset + tick, True)
        if population:
            ticks = [*range(1, 5), 99] if recipe == "budget-six" else range(1, 6)
            for tick in ticks:
                for field in ("population_counts", "population_completed"):
                    tensor(field, offset + tick, False)
                for field in ("population_total_steps", "population_training_steps", "replay_size"):
                    scalar(field, offset + tick, -1, "value")
                for agent in range(2):
                    for field in ("completion_reason", "completion_survival", "completion_observation", "completion_meters"):
                        scalar(field, offset + tick, agent, "value")
    if recipe == "budget-six":
        for field in ("runner_live_transitions", "runner_budget_reached", "runner_budget_shortfall", "runner_episode_count"):
            scalar(field, 99, -1, "value")
    return result


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def validate_value(value: Any) -> None:
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float and math.isfinite(value):
        return
    if type(value) is list:
        for child in value:
            validate_value(child)
        return
    raise ValueError("Readings require finite, JSON-native typed values")


def validate_key(value: Any) -> ReadingKey:
    if not isinstance(value, (list, tuple)) or len(value) != 5:
        raise ValueError("Reading identity requires recipe, field, tick, agent, coordinate")
    recipe, field, tick, agent, coordinate = value
    if recipe not in RECIPES or field not in FIELDS or coordinate not in COORDINATES:
        raise ValueError(f"Unknown reading identity: {value}")
    if type(tick) is not int or tick < 0 or type(agent) is not int or agent < -1:
        raise ValueError(f"Invalid reading tick/agent: {value}")
    return (recipe, field, tick, agent, coordinate)


def reading_index(readings: list[dict[str, Any]]) -> dict[ReadingKey, Any]:
    result: dict[ReadingKey, Any] = {}
    for row in readings:
        if not isinstance(row, dict) or set(row) != {"key", "value"}:
            raise ValueError("Malformed reading")
        key = validate_key(row["key"])
        if key in result:
            raise ValueError(f"Duplicate reading: {key}")
        validate_value(row["value"])
        result[key] = row["value"]
    return result


def equal(old: Any, new: Any) -> bool:
    # Canonical JSON alone would conflate a few native scalar types; check all
    # nested types as well as values, including bool/int and float/int.
    if type(old) is not type(new):
        return False
    if isinstance(old, list):
        return len(old) == len(new) and all(equal(a, b) for a, b in zip(old, new, strict=True))
    return old == new


def compare_exact(
    before: Mapping[ReadingKey, Any], after: Mapping[ReadingKey, Any], intended: Sequence[tuple[ReadingKey, Any, Any]]
) -> None:
    declarations = {}
    for key, old, new in intended:
        validate_key(key)
        validate_value(old)
        validate_value(new)
        if key in declarations:
            raise ValueError(f"Duplicate intended difference: {key}")
        if equal(old, new):
            # Type errors in a changed reading remain visible even if its
            # declaration attempts to permit an unchanged int value.
            if key in before and key in after and type(before[key]) is not type(after[key]):
                raise ValueError(f"Reading type changed: {key}")
            raise ValueError(f"Unused intended difference: {key}")
        declarations[key] = (old, new)
    if before.keys() != after.keys():
        raise ValueError("Coordinate inventory changed (dropped or unknown reading)")
    changed = {}
    for key in before:
        validate_key(key)
        validate_value(before[key])
        validate_value(after[key])
        if not equal(before[key], after[key]):
            changed[key] = (before[key], after[key])
    if changed.keys() != declarations.keys():
        raise ValueError("Observed differences do not match the exact declaration set")
    for key, (old, new) in changed.items():
        expected_old, expected_new = declarations[key]
        if type(old) is not type(expected_old) or type(new) is not type(expected_new):
            raise ValueError(f"Reading type changed: {key}")
        if not equal(old, expected_old) or not equal(new, expected_new):
            raise ValueError(f"Unexpected exact values: {key}")


def strict_json(text: str) -> Any:
    def pairs(entries: list[tuple[str, Any]]) -> dict:
        result = {}
        for name, value in entries:
            if name in result:
                raise ValueError(f"Duplicate JSON property: {name}")
            result[name] = value
        return result

    def bad_constant(value: str) -> None:
        raise ValueError(f"Nonfinite JSON constant: {value}")

    return json.loads(text, object_pairs_hook=pairs, parse_constant=bad_constant)


def load_expected(path: Path) -> dict[str, Any]:
    text = path.read_text()
    blocks = re.findall(r"^```json[ \t]*\n(.*?)^```[ \t]*$", text, flags=re.MULTILINE | re.DOTALL)
    if len(blocks) != 1 or len(re.findall(r"^```json\b", text, flags=re.MULTILINE)) != 1:
        raise ValueError("Expected manifest requires exactly one fenced JSON payload")
    value = strict_json(blocks[0])
    if not isinstance(value, dict) or set(value) != {"schema", "before_revision", "after_revision", "changes"}:
        raise ValueError("Malformed expected manifest")
    if value["schema"] != "episode-lanes.expected.v1" or not re.fullmatch(r"[0-9a-f]{40}", value["before_revision"]):
        raise ValueError("Expected manifest schema/full parent revision required")
    if value["after_revision"] is not None and not re.fullmatch(r"[0-9a-f]{40}", value["after_revision"]):
        raise ValueError("Invalid optional candidate revision")
    if not isinstance(value["changes"], list):
        raise ValueError("Expected changes must be a list")
    seen = set()
    for row in value["changes"]:
        if not isinstance(row, dict) or set(row) != {"key", "before", "after"}:
            raise ValueError("Expected changes require exact key/before/after")
        key = validate_key(row["key"])
        if key in seen:
            raise ValueError(f"Duplicate intended difference: {key}")
        seen.add(key)
        validate_value(row["before"])
        validate_value(row["after"])
        if equal(row["before"], row["after"]):
            raise ValueError(f"Unused intended difference: {key}")
    return value


def semantic_errors(index: Mapping[ReadingKey, Any], recipe: str) -> list[str]:
    """Reconstruct the entry ledger and candidate contract from actual readings.

    Neither producer verdicts nor candidate counts provide the event oracle.
    Captured sticky dones, episode reset boundaries and the declared recipe do.
    """
    errors = []

    def read(field: str, tick: int, agent: int, coordinate: str = "value") -> Any:
        return index[(recipe, field, tick, agent, coordinate)]

    def require(field: str, tick: int, agent: int, expected: Any, coordinate: str = "value") -> None:
        if not equal(read(field, tick, agent, coordinate), expected):
            errors.append(f"{field}/{tick}/{agent}/{coordinate}: required {expected!r}")

    def f32(value: float) -> float:
        return struct.unpack("f", struct.pack("f", value))[0]

    population = recipe in {"authored-two-five", "two-episodes-reset", "budget-six"}
    episodes = 2 if recipe == "two-episodes-reset" else 1
    replay_rows = 0
    for episode in range(episodes + 1):
        offset = episode * 100
        for agent in range(2):
            require("reset_counts", offset, agent, 0)
            require("reset_dones", offset, agent, False)
            if population:
                require("reset_population_counts", offset, agent, 0)
                require("reset_population_completed", offset, agent, False)
                require("reset_completion_reason", offset, agent, None)
                require("reset_completion_survival", offset, agent, None)
        require("reset_global_tick", offset, -1, 0)
        if episode == episodes:
            continue
        counts = [0, 0]
        terminal_counts = [0, 0]
        previous_done = [False, False]
        completions: list[tuple[int, str] | None] = [None, None]
        live_transitions = 0
        limit = 4 if recipe == "budget-six" else 5
        for step in range(1, limit + 1):
            tick = offset + step
            require("global_tick", tick, -1, step)
            for field in ("active_on_entry", "newly_terminal", "newly_retired"):
                require(field, tick, -1, True, "present")
                require(field, tick, -1, "torch.bool", "dtype")
                require(field, tick, -1, [2], "shape")
            for agent in range(2):
                active = not previous_done[agent]
                done = read("dones", tick, agent)
                if type(done) is not bool or previous_done[agent] and not done:
                    errors.append(f"dones/{tick}/{agent}: invalid sticky terminal state")
                newly = active and bool(done)
                counts[agent] += int(active)
                terminal_counts[agent] += int(newly)
                live_transitions += int(active)
                replay_rows += int(active)
                retired = recipe == "healthy-retirement" and step == 5
                for field, expected in (
                    ("ledger_active", active),
                    ("ledger_terminal", newly),
                    ("ledger_counts", counts[agent]),
                    ("ledger_terminal_counts", terminal_counts[agent]),
                    ("step_counts", counts[agent]),
                    ("active_on_entry", active),
                    ("newly_terminal", newly),
                    ("newly_retired", retired),
                ):
                    require(field, tick, agent, expected)
                reward = read("rewards", tick, agent)
                components = [read(field, tick, agent) for field in ("extrinsic", "intrinsic", "shaping")]
                # Retirement preserves the original total while accounting the
                # bonus in extrinsic. Reassociation of float32 additions can
                # move the recomposed sum by one ULP; exact coordinates still
                # compare without tolerance in compare_exact.
                if not math.isclose(reward, f32(f32(components[0] + components[1]) + components[2]), rel_tol=1e-5, abs_tol=1e-6):
                    errors.append(f"rewards/{tick}/{agent}: canonical component sum differs")
                if not active:
                    for field in ("rewards", "extrinsic", "intrinsic", "shaping", "intrinsic_weight"):
                        require(field, tick, agent, 0.0)
                    require("eligible_observation", tick, agent, None)
                elif read("eligible_observation", tick, agent) is None:
                    errors.append(f"eligible_observation/{tick}/{agent}: terminal/live entry row missing")
                if newly:
                    completions[agent] = (tick, "retirement" if retired else "authored_terminal")
                if population:
                    require("admitted_observation", tick, agent, read("eligible_observation", tick, agent))
                    require("population_counts", tick, agent, counts[agent])
                    require("population_completed", tick, agent, bool(done))
                    completion = completions[agent]
                    require("completion_reason", tick, agent, completion[1] if completion is not None else None)
                    require("completion_survival", tick, agent, counts[agent] if completion is not None else None)
                    for field, snapshot in (("completion_observation", "observations"), ("completion_meters", "meters")):
                        require(field, tick, agent, read(snapshot, completion[0], agent, "sha256") if completion is not None else None)
                previous_done[agent] = bool(done)
            require("ledger_live_transitions", tick, -1, live_transitions)
            if population:
                require("replay_size", tick, -1, replay_rows)
        expected_counts = [5, 5] if recipe == "healthy-retirement" else [2, limit]
        if counts != expected_counts or terminal_counts != ([1, 0] if recipe == "budget-six" else [1, 1]):
            errors.append(f"episode {episode}: independent authored event enumeration differs")
        if recipe == "budget-six":
            for agent in range(2):
                completion = completions[agent]
                final_tick = completion[0] if completion is not None else offset + limit
                require("population_counts", 99, agent, counts[agent])
                require("population_completed", 99, agent, True)
                require("completion_reason", 99, agent, completion[1] if completion is not None else "budget")
                require("completion_survival", 99, agent, counts[agent])
                for field, snapshot in (("completion_observation", "observations"), ("completion_meters", "meters")):
                    require(field, 99, agent, read(snapshot, final_tick, agent, "sha256"))
            for field, expected in (
                ("runner_live_transitions", 6),
                ("runner_budget_reached", True),
                ("runner_budget_shortfall", 0),
                ("runner_episode_count", 1),
            ):
                require(field, 99, -1, expected)
    return errors


def validate_capture(value: dict[str, Any]) -> dict[ReadingKey, Any]:
    if (
        not isinstance(value, dict)
        or set(value) != {"schema", "manifest", "readings", "contract"}
        or value["schema"] != "episode-lanes.capture.v1"
    ):
        raise ValueError("Malformed capture schema")
    manifest = value["manifest"]
    required = {
        "source_root",
        "revision",
        "source_sha256",
        "source_stamp",
        "imported_modules",
        "config_sha256",
        "config_inventory",
        "instrument_sha256",
        "recipe",
        "recipe_version",
        "seed",
        "device",
        "actions",
        "action_sha256",
        "measured_fields",
    }
    if set(manifest) != required:
        raise ValueError("Malformed source/config/recipe manifest")
    if manifest["recipe"] not in RECIPES or manifest["recipe_version"] != 1 or manifest["seed"] != 42 or manifest["device"] != "cpu":
        raise ValueError("Unknown recipe version/seed/device")
    if not re.fullmatch(r"[0-9a-f]{40}", manifest["revision"]):
        raise ValueError("Capture requires a full revision")
    for name in ("source_sha256", "config_sha256", "instrument_sha256", "action_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", manifest[name]):
            raise ValueError(f"Invalid digest: {name}")
    if manifest["source_stamp"] != {"revision": manifest["revision"], "source_sha256": manifest["source_sha256"]}:
        raise ValueError("Stale source stamp")
    source_path = Path(manifest["source_root"]) / "src" / "townlet"
    if not Path(manifest["source_root"]).is_absolute() or not manifest["imported_modules"]:
        raise ValueError("Absolute source/import identity required")
    for module, path in manifest["imported_modules"].items():
        if module != "townlet" and not module.startswith("townlet."):
            raise ValueError("Unknown imported module")
        if not Path(path).is_absolute() or not Path(path).is_relative_to(source_path):
            raise ValueError(f"Wrong imported source root: {path}")
    if "townlet" not in manifest["imported_modules"]:
        raise ValueError("Missing townlet import identity")
    if digest(canonical(manifest["config_inventory"])) != manifest["config_sha256"]:
        raise ValueError("Configuration byte inventory digest differs")
    if digest(canonical(manifest["actions"])) != manifest["action_sha256"]:
        raise ValueError("Recorded action digest differs")
    indexed = reading_index(value["readings"])
    if not indexed or any(key[0] != manifest["recipe"] for key in indexed):
        raise ValueError("Reading recipe differs from manifest")
    if indexed.keys() != expected_inventory(manifest["recipe"]):
        raise ValueError("Recipe coordinate inventory missing, dropped or unknown readings")
    fields = sorted({key[1] for key in indexed})
    if fields != sorted(manifest["measured_fields"]) or len(fields) != len(manifest["measured_fields"]):
        raise ValueError("Measured field inventory differs")
    if set(value["contract"]) != {"qualified", "errors"} or type(value["contract"]["qualified"]) is not bool:
        raise ValueError("Malformed independent contract result")
    if not isinstance(value["contract"]["errors"], list) or value["contract"]["qualified"] != (not value["contract"]["errors"]):
        raise ValueError("Inconsistent independent contract result")
    errors = semantic_errors(indexed, manifest["recipe"])
    if value["contract"] != {"qualified": not errors, "errors": errors}:
        raise ValueError("Forged or stale independent contract result")
    return indexed


def source_identity(root: Path) -> dict[str, str]:
    dirty = git(
        root, "status", "--porcelain", "--untracked-files=all", "--", "src", "configs", "scripts", "tests", "pyproject.toml", "uv.lock"
    )
    if dirty:
        raise ValueError(f"Dirty execution-bearing source: {dirty}")
    inventory = {
        name: digest((root / name).read_bytes()) for name in git(root, "ls-files", "--", "src", "pyproject.toml", "uv.lock").splitlines()
    }
    return {"revision": git(root, "rev-parse", "HEAD"), "source_sha256": digest(canonical(inventory))}


def config_inventory(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): digest(path.read_bytes()) for path in sorted(root.rglob("*.yaml")) if path.is_file()}


class Collector:
    def __init__(self, recipe: str):
        self.recipe = recipe
        self.readings: list[dict[str, Any]] = []
        self.errors: list[str] = []
        self.actions: list[list[int]] = []
        self.episode = 0

    def scalar(self, field: str, tick: int, agent: int, value: Any, coordinate: str) -> None:
        self.readings.append({"key": [self.recipe, field, self.episode * 100 + tick, agent, coordinate], "value": value})

    def tensor(self, field: str, tick: int, value: Any, *, num_agents: int, hashed: bool) -> None:
        self.scalar(field, tick, -1, value is not None, "present")
        self.scalar(field, tick, -1, str(value.dtype) if value is not None else None, "dtype")
        self.scalar(field, tick, -1, list(value.shape) if value is not None else None, "shape")
        for agent in range(num_agents):
            row = value[agent].detach().cpu().contiguous() if value is not None else None
            self.scalar(field, tick, agent, row.tolist() if row is not None else None, "value")
            if hashed:
                self.scalar(field, tick, agent, digest(row.numpy().tobytes()) if row is not None else None, "sha256")

    def reset(self, env: Any, population: Any) -> None:
        n = env.num_agents
        for field, value in (
            ("reset_observations", env._get_observations()),
            ("reset_meters", env.meters),
            ("reset_dones", env.dones),
            ("reset_counts", env.step_counts),
        ):
            self.tensor(field, 0, value, num_agents=n, hashed=True)
        self.scalar("reset_global_tick", 0, -1, env.global_tick, "value")
        self.tensor("initial_energy", 0, env.meters[:, env.meter_name_to_index["energy"]], num_agents=n, hashed=False)
        if population is not None:
            self.tensor("reset_population_counts", 0, population.episode_step_counts, num_agents=n, hashed=False)
            self.tensor("reset_population_completed", 0, getattr(population, "episode_completed", None), num_agents=n, hashed=False)
            completions = getattr(population, "episode_completions", None)
            for agent in range(n):
                completion = completions[agent] if completions is not None else None
                self.scalar("reset_completion_reason", 0, agent, completion.reason if completion is not None else None, "value")
                self.scalar("reset_completion_survival", 0, agent, completion.survival_time if completion is not None else None, "value")


def run_producer(args: argparse.Namespace) -> dict[str, Any]:
    # Imports occur only after the isolated process pins sys.path explicitly.
    import torch
    import yaml

    import townlet
    from townlet.curriculum.static import StaticCurriculum
    from townlet.determinism import seed_all
    from townlet.environment.vectorized_env import VectorizedHamletEnv
    from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
    from townlet.population.vectorized import VectorizedPopulation
    from townlet.universe.compiler import UniverseCompiler

    root = args.source_root.resolve()
    stamp = source_identity(root)
    original_inventory = config_inventory(args.config_root)
    collector = Collector(args.recipe)
    seed_all(42)
    torch.set_num_threads(1)
    with tempfile.TemporaryDirectory(prefix="episode-lane-producer-") as temporary:
        pack = Path(temporary) / "config"
        shutil.copytree(args.config_root, pack, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        level_dirs = sorted((pack / "levels").iterdir())
        if len(level_dirs) != 1 or not level_dirs[0].is_dir():
            raise ValueError("Lifecycle config requires exactly one primary level")
        level_name = level_dirs[0].name
        training_path = level_dirs[0] / "training.yaml"
        config = yaml.safe_load(training_path.read_text())
        training = config["training"]
        training["population"]["size"] = 2
        training["training_loop"]["max_steps_per_episode"] = (
            5 if args.recipe in {"passive-two-five", "death-at-lifespan", "healthy-retirement"} else 10
        )
        training["training_loop"]["max_episodes"] = 2 if args.recipe == "two-episodes-reset" else 1
        training["replay_buffer"]["batch_size"] = 128
        config["recording"] = {"enabled": False}
        training_path.write_text(yaml.safe_dump(config, sort_keys=False))
        effective_inventory = config_inventory(pack)
        config_identity = {"authored": original_inventory, "effective": effective_inventory}
        universe = UniverseCompiler().compile(pack, primary_level=level_name, use_cache=False)
        env = VectorizedHamletEnv(universe=universe, level_name=level_name, num_agents=2, device=torch.device("cpu"))
        wait = env.action_space.get_action_by_name("WAIT").id
        end = env.action_space.get_action_by_name("END_LANE").id
        schedule = [[wait, wait], [end, wait], [wait, wait], [wait, wait], [wait, end]]
        if args.recipe in {"passive-two-five", "healthy-retirement"}:
            schedule = [[wait, wait]] * 5
        population = None
        exploration = EpsilonGreedyExploration(epsilon=0.0, epsilon_decay=1.0, epsilon_min=0.0)
        if args.recipe in {"authored-two-five", "two-episodes-reset", "budget-six"}:
            population = VectorizedPopulation(
                env=env,
                curriculum=StaticCurriculum(difficulty_level=1.0),
                exploration=exploration,
                agent_ids=["early", "late"],
                device=torch.device("cpu"),
                brain_config=universe.brain,
                obs_dim=env.observation_dim,
                train_frequency=1,
                batch_size=128,
                sequence_length=1,
                max_grad_norm=1.0,
                action_dim=env.action_dim,
            )

        def select(q_values: Any, agent_states: Any, action_masks: Any) -> Any:
            collector.tensor("selected_q_values", env.global_tick + 1, q_values, num_agents=2, hashed=True)
            actions = torch.tensor(schedule[env.global_tick], dtype=torch.long, device=env.device)
            active = ~env.dones
            if not bool(action_masks[torch.arange(2), actions][active].all()):
                raise ValueError("Scripted live action violates compiled action mask")
            return actions

        exploration.select_actions = select
        episodes = 2 if args.recipe == "two-episodes-reset" else 1

        def episode_reset() -> None:
            if population is None:
                env.reset()
            else:
                population.reset()
            if args.recipe == "passive-two-five":
                # Explicit controlled fixture from the retained oracle recipe;
                # the authored witness never injects meters.
                env.meters[:, env.meter_name_to_index["energy"]] = torch.tensor([0.015, 0.045])
            collector.reset(env, population)

        live_counts = torch.zeros(2, dtype=torch.long)
        terminal_counts = torch.zeros(2, dtype=torch.long)
        live_transitions = 0
        last_observation = None
        original_step = env.step

        def measured_step(actions: Any, depletion_multiplier: float = 1.0) -> Any:
            nonlocal live_transitions, last_observation
            before = env.dones.clone()
            predecessor = population.current_obs.clone() if population is not None else env._get_observations().clone()
            result = original_step(actions, depletion_multiplier)
            observations, rewards, dones, info = result
            last_observation = observations
            tick = env.global_tick
            active = ~before
            newly = active & dones
            live_counts.add_(active.long())
            terminal_counts.add_(newly.long())
            live_transitions += int(active.sum().item())
            collector.actions.append(actions.tolist())
            for field, value, hashed in (
                ("actions", actions, True),
                ("observations", observations, True),
                ("meters", env.meters, True),
                ("dones", dones, True),
                ("rewards", rewards, True),
                ("step_counts", info["step_counts"], False),
                ("ledger_active", active, False),
                ("ledger_terminal", newly, False),
                ("ledger_counts", live_counts, False),
                ("ledger_terminal_counts", terminal_counts, False),
                ("active_on_entry", info.get("active_on_entry"), False),
                ("newly_terminal", info.get("newly_terminal"), False),
                ("newly_retired", info.get("newly_retired"), False),
                ("intrinsic_weight", info["intrinsic_weight"], True),
            ):
                collector.tensor(field, tick, value, num_agents=2, hashed=hashed)
            for field in ("extrinsic", "intrinsic", "shaping"):
                collector.tensor(field, tick, info["reward_components"][field], num_agents=2, hashed=True)
            for agent in range(2):
                collector.scalar(
                    "eligible_observation",
                    tick,
                    agent,
                    digest(predecessor[agent].numpy().tobytes()) if bool(active[agent]) else None,
                    "value",
                )
            collector.scalar("global_tick", tick, -1, env.global_tick, "value")
            collector.scalar("time_of_day", tick, -1, env.time_of_day, "value")
            collector.scalar("ledger_live_transitions", tick, -1, live_transitions, "value")
            if not torch.equal(env.step_counts, live_counts):
                collector.errors.append(f"episode {collector.episode} tick {tick}: runtime counts differ from independent entry ledger")
            for field, expected in (("active_on_entry", active), ("newly_terminal", newly)):
                if (
                    field not in info
                    or info[field].dtype != torch.bool
                    or info[field].shape != (2,)
                    or not torch.equal(info[field], expected)
                ):
                    collector.errors.append(f"episode {collector.episode} tick {tick}: required {field} absent or inconsistent")
            retired = info.get("newly_retired")
            expected_retired = (
                torch.ones(2, dtype=torch.bool) if args.recipe == "healthy-retirement" and tick == 5 else torch.zeros(2, dtype=torch.bool)
            )
            if retired is None or retired.dtype != torch.bool or retired.shape != (2,) or not torch.equal(retired, expected_retired):
                collector.errors.append(f"episode {collector.episode} tick {tick}: required newly_retired absent or malformed")
            if not torch.equal(
                rewards,
                info["reward_components"]["extrinsic"] + info["reward_components"]["intrinsic"] + info["reward_components"]["shaping"],
            ):
                collector.errors.append(f"episode {collector.episode} tick {tick}: total reward differs from canonical component sum")
            if (
                bool((rewards[~active] != 0).any())
                or any(bool((value[~active] != 0).any()) for value in info["reward_components"].values())
                or bool((info["intrinsic_weight"][~active] != 0).any())
            ):
                collector.errors.append(f"episode {collector.episode} tick {tick}: completed lane retains reward contribution")
            return result

        env.step = measured_step

        replay_rows: dict[int, str] = {}

        def observe_replay(real_population: Any) -> None:
            original_push = real_population.replay_buffer.push

            def push(*arguments: Any, **keywords: Any) -> Any:
                observed = keywords["observations"] if "observations" in keywords else arguments[0]
                before = real_population.current_obs
                identities = [digest(row.detach().cpu().contiguous().numpy().tobytes()) for row in before]
                incoming = [digest(row.detach().cpu().contiguous().numpy().tobytes()) for row in observed]
                for identity in set(incoming):
                    candidates = [agent for agent, candidate in enumerate(identities) if candidate == identity]
                    if len(candidates) > incoming.count(identity):
                        raise ValueError("Replay row identity ambiguous between independently eligible/phantom lanes")
                unused = set(range(2))
                for identity in incoming:
                    matched = [agent for agent in sorted(unused) if identities[agent] == identity]
                    if not matched:
                        raise ValueError("Replay admitted an unknown predecessor row")
                    agent = matched[0]
                    replay_rows[agent] = identity
                    unused.remove(agent)
                return original_push(*arguments, **keywords)

            real_population.replay_buffer.push = push

        if population is not None:
            observe_replay(population)

        def population_readings(tick: int) -> None:
            if population is None:
                return
            if tick != 99:
                for agent in range(2):
                    collector.scalar("admitted_observation", tick, agent, replay_rows.get(agent), "value")
                replay_rows.clear()
            collector.tensor("population_counts", tick, population.episode_step_counts, num_agents=2, hashed=False)
            collector.tensor("population_completed", tick, getattr(population, "episode_completed", None), num_agents=2, hashed=False)
            collector.scalar("population_total_steps", tick, -1, population.total_steps, "value")
            collector.scalar("population_training_steps", tick, -1, population.training_step_counter, "value")
            collector.scalar("replay_size", tick, -1, len(population.replay_buffer), "value")
            completions = getattr(population, "episode_completions", None)
            if not torch.equal(population.episode_step_counts, live_counts):
                collector.errors.append(f"episode {collector.episode} tick {tick}: population counts differ from independent entry ledger")
            for agent in range(2):
                completion = completions[agent] if completions is not None else None
                if bool(env.dones[agent]) and (completion is None or completion.survival_time != int(live_counts[agent])):
                    collector.errors.append(
                        f"episode {collector.episode} tick {tick}: required once-only completion absent or inconsistent"
                    )
                for field, value in (
                    ("completion_reason", completion.reason if completion is not None else None),
                    ("completion_survival", completion.survival_time if completion is not None else None),
                    ("completion_observation", digest(completion.final_observation.numpy().tobytes()) if completion is not None else None),
                    ("completion_meters", digest(completion.final_meters.numpy().tobytes()) if completion is not None else None),
                ):
                    collector.scalar(field, tick, agent, value, "value")

        if args.recipe == "budget-six":
            from unittest.mock import patch

            from townlet.demo.runner import DemoRunner

            # Real runner owns budget decision, population steps and completion.
            # Construct normally from supported bytes, then explicitly select
            # the controlled no-intrinsic exploration through its existing seam.
            original_population_reset = VectorizedPopulation.reset
            original_population_step = VectorizedPopulation.step_population

            def runner_reset(real_population: Any) -> None:
                nonlocal env, population, original_step
                env = real_population.env
                population = real_population
                original_population_reset(real_population)
                observe_replay(real_population)
                original_step = env.step
                env.step = measured_step
                collector.reset(env, population)

            def runner_step(real_population: Any, real_env: Any) -> Any:
                result = original_population_step(real_population, real_env)
                population_readings(real_env.global_tick)
                return result

            with (
                patch("townlet.demo.runner.AdaptiveIntrinsicExploration", side_effect=lambda **kwargs: exploration),
                patch.object(VectorizedPopulation, "reset", runner_reset),
                patch.object(VectorizedPopulation, "step_population", runner_step),
                DemoRunner(
                    config_dir=pack,
                    db_path=Path(temporary) / "demo.db",
                    checkpoint_dir=Path(temporary) / "checkpoints",
                    max_episodes=1,
                    level_name=level_name,
                    max_environment_steps=6,
                ) as runner,
            ):
                runner.run()
                population_readings(99)
                for field, value in (
                    ("runner_live_transitions", runner.completed_live_agent_steps),
                    ("runner_budget_reached", runner.environment_step_budget_reached),
                    ("runner_budget_shortfall", runner.environment_step_budget_shortfall),
                    ("runner_episode_count", runner.current_episode),
                ):
                    collector.scalar(field, 99, -1, value, "value")
                if live_counts.tolist() != [2, 4] or terminal_counts.tolist() != [1, 0] or live_transitions != 6 or env.global_tick != 4:
                    raise ValueError("Real runner did not produce independently enumerated budget-six stop")
                collector.episode = 1
                original_population_reset(population)
                collector.reset(env, population)
        else:
            for episode in range(episodes):
                collector.episode = episode
                live_counts.zero_()
                terminal_counts.zero_()
                live_transitions = 0
                episode_reset()
                for tick in range(1, 6):
                    if population is None:
                        env.step(torch.tensor(schedule[tick - 1], dtype=torch.long))
                    else:
                        population.step_population(env)
                    population_readings(tick)
                expected = [5, 5] if args.recipe == "healthy-retirement" else [2, 5]
                if live_counts.tolist() != expected or terminal_counts.tolist() != [1, 1]:
                    raise ValueError(f"Independent authored event contract failed: {live_counts.tolist()}, {terminal_counts.tolist()}")
                if last_observation is None:
                    raise ValueError("No observed production transitions")
            collector.episode = episodes
            episode_reset()

        imported = {
            name: str(Path(module.__file__).resolve())
            for name, module in sys.modules.items()
            if (name == "townlet" or name.startswith("townlet.")) and getattr(module, "__file__", None)
        }
        assert Path(townlet.__file__).resolve().is_relative_to(root / "src" / "townlet")
        if stamp != source_identity(root) or original_inventory != config_inventory(args.config_root):
            raise ValueError("Source/config changed during capture")
        manifest = {
            "source_root": str(root),
            **stamp,
            "source_stamp": stamp,
            "imported_modules": imported,
            "config_inventory": config_identity,
            "config_sha256": digest(canonical(config_identity)),
            "instrument_sha256": digest(Path(__file__).read_bytes()),
            "recipe": args.recipe,
            "recipe_version": 1,
            "seed": 42,
            "device": "cpu",
            "actions": collector.actions,
            "action_sha256": digest(canonical(collector.actions)),
            "measured_fields": sorted({row["key"][1] for row in collector.readings}),
        }
        result = {
            "schema": "episode-lanes.capture.v1",
            "manifest": manifest,
            "readings": collector.readings,
            "contract": {"qualified": not collector.errors, "errors": collector.errors},
        }
        errors = semantic_errors(reading_index(collector.readings), args.recipe)
        result["contract"] = {"qualified": not errors, "errors": errors}
        return result


def capture_command(args: argparse.Namespace) -> None:
    args.source_root = args.source_root.resolve()
    args.config_root = args.config_root.resolve()
    source_identity(args.source_root)
    args.output.mkdir(parents=True, exist_ok=False)
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(args.source_root / "src")
    environment["PYTHONSAFEPATH"] = "1"
    environment["CUDA_VISIBLE_DEVICES"] = ""
    command = [
        sys.executable,
        "-P",
        str(Path(__file__).resolve()),
        "_produce",
        "--source-root",
        str(args.source_root),
        "--config-root",
        str(args.config_root),
        "--recipe",
        args.recipe,
        "--output",
        str(args.output.resolve()),
    ]
    with (args.output / "stdout.log").open("w") as stdout, (args.output / "stderr.log").open("w") as stderr:
        result = subprocess.run(command, cwd=args.source_root, env=environment, stdout=stdout, stderr=stderr)
    (args.output / "command.json").write_text(
        json.dumps({"command": command, "exit_status": result.returncode, "pythonpath": environment["PYTHONPATH"]}, indent=2) + "\n"
    )
    if result.returncode:
        raise ValueError(f"Producer failed ({result.returncode}); see {args.output / 'stderr.log'}")
    value = strict_json((args.output / "capture.json").read_text())
    validate_capture(value)
    print(
        json.dumps(
            {
                "recipe": args.recipe,
                "revision": value["manifest"]["revision"],
                "readings": len(value["readings"]),
                "contract": value["contract"],
                "output": str(args.output),
            }
        )
    )


def compare_command(args: argparse.Namespace) -> bool:
    before = strict_json((args.before / "capture.json").read_text())
    after = strict_json((args.after / "capture.json").read_text())
    old, new = validate_capture(before), validate_capture(after)
    expected = load_expected(args.expected)
    errors = []
    for field in (
        "config_sha256",
        "config_inventory",
        "instrument_sha256",
        "recipe",
        "recipe_version",
        "seed",
        "device",
        "actions",
        "action_sha256",
        "measured_fields",
    ):
        if before["manifest"][field] != after["manifest"][field]:
            errors.append(f"Input/recipe identity differs: {field}")
    if before["manifest"]["revision"] != expected["before_revision"]:
        errors.append("Parent revision differs from preregistration")
    if expected["after_revision"] is not None and after["manifest"]["revision"] != expected["after_revision"]:
        errors.append("Candidate revision differs from expected")
    candidate_root = Path(after["manifest"]["source_root"])
    for label, capture in (("Parent", before), ("Candidate", after)):
        if source_identity(Path(capture["manifest"]["source_root"])) != capture["manifest"]["source_stamp"]:
            errors.append(f"{label} source stamp is stale")
    if git(candidate_root, "rev-parse", f"{expected['before_revision']}^{{commit}}") != expected["before_revision"]:
        errors.append("Parent revision is unavailable")
    ancestry = subprocess.run(
        ["git", "-C", str(candidate_root), "merge-base", "--is-ancestor", expected["before_revision"], after["manifest"]["revision"]],
        check=False,
    )
    if ancestry.returncode:
        errors.append("Parent revision is not a candidate ancestor")
    try:
        compare_exact(
            old,
            new,
            [
                (validate_key(row["key"]), row["before"], row["after"])
                for row in expected["changes"]
                if row["key"][0] == before["manifest"]["recipe"]
            ],
        )
    except ValueError as error:
        errors.append(str(error))
    if not after["contract"]["qualified"]:
        errors.extend(after["contract"]["errors"])
    changed = [
        {"key": list(key), "before": old.get(key), "after": new.get(key)}
        for key in sorted(old.keys() | new.keys())
        if key not in old or key not in new or not equal(old[key], new[key])
    ]
    output = {
        "schema": "episode-lanes.comparison.v1",
        "qualified": not errors,
        "changed": changed,
        "errors": errors,
        "before_manifest": before["manifest"],
        "after_manifest": after["manifest"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"qualified": not errors, "changes": len(changed), "errors": errors}))
    return not errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("capture", "_produce"):
        child = subparsers.add_parser(command)
        child.add_argument("--source-root", type=Path, required=True)
        child.add_argument("--config-root", type=Path, required=True)
        child.add_argument("--recipe", choices=RECIPES, required=True)
        child.add_argument("--output", type=Path, required=True)
    compare = subparsers.add_parser("compare")
    for name in ("before", "after", "expected", "output"):
        compare.add_argument(f"--{name}", type=Path, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "_produce":
        sys.path.insert(0, str(args.source_root.resolve() / "src"))
        value = run_producer(args)
        validate_capture(value)
        (args.output / "capture.json").write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    elif args.command == "capture":
        capture_command(args)
    elif not compare_command(args):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
