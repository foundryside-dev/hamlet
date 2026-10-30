"""VFS WP12 (spawn half), finding F6: one declaration owns what a spawn predicate reads.

`SpawnPredicateReads` derives the compile-time schema and the runtime context from the
same registry roster through the same scope rule. Every reproduction in
review-2026-10-24/vfs_round2/r13*.py either works end to end or is refused at compile
time with the rule's `file:line`; none compiles and then raises at reset or step.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import torch
import yaml

from townlet.items.manager import SpawnPredicateReads
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.compilers.vfs import VFSCompiler
from townlet.universe.declarations import DeclarationStore
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationError
from townlet.universe.raw_configs_v21 import RawConfigsV21
from townlet.world.expression import ExpressionParser

BASE = Path(__file__).resolve().parents[4] / "configs" / "test" / "items_smoke"
LEVEL = "L0_smoke"
APPLES_AT_RESET = 3  # items_smoke L0_smoke: apple spawn_count


def _global(identifier: str, *, initial: float = 0.0, expression: str | None = None, lifetime: str = "episode") -> dict:
    declaration = {
        "id": identifier,
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "scope": "global",
        "type": "scalar",
        "lifetime": lifetime,
        "semantic_type": "custom",
        "exposed_to": [],
        "initial_value": initial,
    }
    if expression is not None:
        declaration["expression"] = expression
    return declaration


def _pack(tmp_path: Path, when: str, extra_variables: tuple[dict, ...] = (), *, temporal: bool = False) -> Path:
    pack = tmp_path / "pack"
    shutil.copytree(BASE, pack, ignore=shutil.ignore_patterns(".compiled"))
    variables_path = pack / "variables.yaml"
    variables = yaml.safe_load(variables_path.read_text())
    variables["variables"]["declarations"].extend(extra_variables)
    variables_path.write_text(yaml.safe_dump(variables, sort_keys=False))
    items_path = pack / "levels" / LEVEL / "items.yaml"
    items = yaml.safe_load(items_path.read_text())
    for rule in items["items"]:
        if rule["item_type"] == "apple":
            rule["when"] = when
    items_path.write_text(yaml.safe_dump(items, sort_keys=False))
    if temporal:
        stratum_path = pack / "stratum.yaml"
        stratum = yaml.safe_load(stratum_path.read_text())
        stratum["stratum"]["temporal_support"] = "enabled"
        stratum_path.write_text(yaml.safe_dump(stratum, sort_keys=False))
        curriculum_path = pack / "levels" / LEVEL / "curriculum.yaml"
        curriculum = yaml.safe_load(curriculum_path.read_text())
        curriculum["curriculum"].update({"active_temporal": True, "day_length": 24})
        curriculum_path.write_text(yaml.safe_dump(curriculum, sort_keys=False))
    return pack


def _when_location(pack: Path) -> str:
    items_path = pack / "levels" / LEVEL / "items.yaml"
    line = next(number for number, text in enumerate(items_path.read_text().splitlines(), start=1) if text.strip().startswith("when:"))
    return f"{items_path}:{line}"


def _apples_after_reset(pack: Path) -> int:
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL)
    env = universe.create_environment(num_agents=1, level_name=LEVEL, device="cpu")
    env.reset()
    return sum(1 for item in env.item_manager.items_in_world(0) if item.item_type == "apple")


SEASON = _global("season", initial=1.0)


@pytest.mark.parametrize(
    ("when", "extra", "temporal"),
    [
        pytest.param("env.has_food", (), False, id="r13-env-prefix-agent-bool"),
        pytest.param("env.season > 0.5", (SEASON,), False, id="r13-env-prefix-global"),
        pytest.param("season > 0.5", (SEASON,), False, id="r13-bare-global"),
        pytest.param("energy > 0.5", (), False, id="r13-bare-meter"),
        pytest.param("agent.vfs.has_food", (), False, id="agent-vfs-prefix"),
        pytest.param("temporal.is_night", (), True, id="r13b-is-night"),
        pytest.param("temporal.time_of_day < 12.0", (), True, id="r13b-time-of-day"),
        pytest.param("temporal.tick > 5", (), True, id="temporal-tick"),
        pytest.param("vfs.freshness > 0.5", (), False, id="item-scope-variable"),
    ],
)
def test_unserved_read_refuses_at_compile_with_file_line(tmp_path, when, extra, temporal):
    pack = _pack(tmp_path, when, extra, temporal=temporal)
    with pytest.raises(CompilationError) as excinfo:
        UniverseCompiler().compile(pack, primary_level=LEVEL)
    (issue,) = excinfo.value.issues
    assert issue.code == ErrorCode.ITEM_SPAWN_CONDITION
    assert issue.location == _when_location(pack)
    assert "does not serve" in issue.message
    assert "apple" in issue.message


def test_non_bool_predicate_refuses_with_file_line(tmp_path):
    pack = _pack(tmp_path, "vfs.season + 1.0", (SEASON,))
    with pytest.raises(CompilationError) as excinfo:
        UniverseCompiler().compile(pack, primary_level=LEVEL)
    (issue,) = excinfo.value.issues
    assert issue.code == ErrorCode.ITEM_SPAWN_CONDITION
    assert issue.location == _when_location(pack)
    assert "must return bool" in issue.message


@pytest.mark.parametrize(
    ("when", "extra", "expected"),
    [
        pytest.param("vfs.season > 0.5", (SEASON,), APPLES_AT_RESET, id="r13-vfs-global-true"),
        pytest.param("vfs.season < 0.5", (SEASON,), 0, id="r13-vfs-global-false"),
        pytest.param("bar.energy > 0.5", (), APPLES_AT_RESET, id="meter"),
        pytest.param("not vfs.has_food", (), APPLES_AT_RESET, id="agent-scope-variable"),
        pytest.param("vfs.tick < 1.0", (), APPLES_AT_RESET, id="engine-clock"),
    ],
)
def test_served_reads_work_end_to_end(tmp_path, when, extra, expected):
    assert _apples_after_reset(_pack(tmp_path, when, extra)) == expected


def test_spawn_predicate_reads_expression_value_evaluated_at_reset(tmp_path):
    """r13's `vfs.season > 0.5` with season an expression: the declared literal (0.0)
    would gate the spawn shut; the evaluated value (tick + 1 = 1.0 at instant 0) opens it."""
    season = _global("season", initial=0.0, expression="tick + 1.0")
    assert _apples_after_reset(_pack(tmp_path, "vfs.season > 0.5", (season,))) == APPLES_AT_RESET


def test_compile_schema_and_runtime_context_cannot_drift(tmp_path):
    """Every name the compiler admits resolves in the runtime context, and vice versa."""
    pack = _pack(tmp_path, "vfs.season > 0.5", (SEASON,))
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL)
    env = universe.create_environment(num_agents=2, level_name=LEVEL, device="cpu")
    env.reset()

    raw = RawConfigsV21.from_declarations(DeclarationStore.discover(pack))
    schema = SpawnPredicateReads.schema(
        meter_names=env.meter_name_to_index,
        variables=VFSCompiler().build_runtime_variables(raw.variables),
    )
    context = SpawnPredicateReads.context(bars=env.bars, registry=env.vfs_registry, device=env.device)
    served = {SpawnPredicateReads.bar_path(name) for name in context.bars} | {
        SpawnPredicateReads.variable_path(identifier) for identifier in context.vfs
    }
    assert set(schema) == served
    for path in schema:
        context.get(path)  # no KeyError
    assert SpawnPredicateReads.variable_path("tick") in schema


def test_reads_lists_every_name_in_source_order():
    ast = ExpressionParser().parse("(bar.energy < 0.4) and vfs.danger >= 3 or not season")
    assert SpawnPredicateReads.reads(ast) == ["bar.energy", "vfs.danger", "season"]


def test_agent_scope_read_decides_per_world(tmp_path):
    """S1: each world's spawn follows its own agent's value; there is no all-worlds reduction."""
    pack = _pack(tmp_path, "bar.energy > 0.5")
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL)
    env = universe.create_environment(num_agents=2, level_name=LEVEL, device="cpu")
    env.reset()
    rule = next(rule for rule in env.level.items_appearance.items if rule.item_type == "apple")
    bars = {name: tensor.clone() for name, tensor in env.bars.items()}
    bars["energy"] = torch.tensor([0.9, 0.1])
    assert env.item_manager._should_spawn_rule(rule, bars=bars) == [True, False]
    bars["energy"] = torch.tensor([0.9, 0.6])
    assert env.item_manager._should_spawn_rule(rule, bars=bars) == [True, True]


def test_rejected_initial_spawn_retries_on_its_declared_period(tmp_path):
    """A predicate false at reset arms the respawn timer, so the rule retries every period;
    it fires on the first period boundary after the predicate turns true (tick 7 -> tick 10)."""
    bloom = _global("bloom", initial=0.0, expression="tick >= 7.0")
    bloom["type"] = "bool"
    bloom["initial_value"] = False
    pack = _pack(tmp_path, "vfs.bloom", (bloom,))
    items_path = pack / "levels" / LEVEL / "items.yaml"
    items = yaml.safe_load(items_path.read_text())
    for rule in items["items"]:
        if rule["item_type"] == "apple":
            rule["schedule"] = {"type": "periodic", "period": 5}
    items_path.write_text(yaml.safe_dump(items, sort_keys=False))

    universe = UniverseCompiler().compile(pack, primary_level=LEVEL)
    env = universe.create_environment(num_agents=1, level_name=LEVEL, device="cpu")
    env.reset()
    wait = next(i for i, action in enumerate(env.action_space.actions) if action.name == "WAIT")
    apples_by_tick = {0: sum(1 for item in env.item_manager.items_in_world(0) if item.item_type == "apple")}
    for _ in range(12):
        env.step(torch.tensor([wait], device=env.device))
        apples_by_tick[env.global_tick] = sum(1 for item in env.item_manager.items_in_world(0) if item.item_type == "apple")
    assert all(apples_by_tick[tick] == 0 for tick in range(10))  # rejected at 0 and 5; true from 7
    assert apples_by_tick[10] == 1
