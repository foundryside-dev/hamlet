"""WP17 S5 (review-2026-10-24 VFS round 2): one variable, one spelling, one resolver.

Before this change every consumer of the expression language had its own namespace:
a profile expression read ``x``, an action write ``x``/``vfs.x``/``self.vfs.x``/
``target.vfs.x`` and a meter as ``m``/``bar.m``/``self.bar.m``/``target.bar.m``, an
effect ``vfs.x``/``global.vfs.x``/``target.vfs.x``, a spawn predicate ``vfs.x``. Under
S1 a world has one agent, so those qualifiers carried no information.

Now there is one grammar (``townlet.world.expression.references``) and one resolver
(``townlet.vfs.namespace.Namespace``) that every type checker and every runtime
context uses:

- ``x``: a registry variable, read in this world by its declared scope (and the
  engine names ``tick`` and ``agent_id``, and an effect's locals);
- ``bar.m``: a meter of this world's agent;
- ``item.x``: the state of the item the context is bound to.

Every other spelling refuses at compile, naming the one to write, at ``file:line``.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest
import torch
import yaml

from tests.test_townlet._fixtures.command_namespace import command_compiler
from townlet.config.effects_config import CommandConfig
from townlet.effects.context import ExecutionContext as EffectContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.parser import CommandParser
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.items.manager import SpawnPredicateReads
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
from townlet.vfs.namespace import (
    AGENT_EXPRESSION,
    ANY_ITEM,
    EFFECT_PIPELINE,
    GLOBAL_EXPRESSION,
    INTERACTION_PIPELINE,
    SPAWN_PREDICATE,
    TRANSITION_WRITE,
    ItemBinding,
    Namespace,
    ReadContext,
    SymbolKind,
)
from townlet.vfs.schema import VariableScope
from townlet.vfs.transition_graph import DEFAULT_TRANSITION_PHASES
from townlet.world.expression import read_paths
from townlet.world.expression.context import ExecutionContext
from townlet.world.expression.evaluator import Evaluator
from townlet.world.expression.functions import FUNCTION_SPECS, REQUIRES_HISTORY, TEMPORAL_FUNCTIONS
from townlet.world.expression.type_checker import TypeCheckError

CONFIGS = Path(__file__).resolve().parents[4] / "configs"
WITNESS = CONFIGS / "static_epistemic_access"
LEVEL = "L0_simple"
ITEMS = CONFIGS / "test" / "items_smoke"
ITEMS_LEVEL = "L0_smoke"
LATE_PHASE = "apply_completion_bonuses"


# -- pack harness ----------------------------------------------------------------------


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _dump(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def _decl(var_id: str, *, scope: str = "agent", type: str = "scalar", lifetime: str = "episode", **extra: object) -> dict:
    declaration: dict[str, object] = {
        "id": var_id,
        "scope": scope,
        "type": type,
        "lifetime": lifetime,
        "semantic_type": "custom",
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "exposed_to": [],
        "initial_value": False if type == "bool" else (-1 if type.endswith("_ref") else 0.0),
    }
    declaration.update(extra)
    return declaration


def _write(variable_id: str, expression: str, *, condition: str | None = None, composition: str = "additive_delta") -> dict:
    return {
        "variable_id": variable_id,
        "expression": expression,
        "condition": condition,
        "composition": composition,
        "phase": LATE_PHASE,
        "priority": 0,
        "clamp": None,
        "telemetry_label": "w",
    }


def _rule(variable_id: str, expression: str, *, composition: str = "additive_delta") -> dict:
    return {
        "id": "r",
        "phase": "apply_transition_rules",
        "condition": None,
        "writes": [
            {
                "variable_id": variable_id,
                "expression": expression,
                "composition": composition,
                "condition": None,
                "clamp": None,
                "effect": None,
            }
        ],
    }


def _pack(
    tmp_path: Path,
    *,
    declarations: list[dict] = (),  # type: ignore[assignment]
    writes: list[dict] | None = None,
    rules: list[dict] | None = None,
    name: str = "pack",
) -> Path:
    pack = tmp_path / name
    shutil.copytree(WITNESS, pack, ignore=shutil.ignore_patterns(".compiled"))
    variables = _yaml(pack / "variables.yaml")
    variables["variables"]["declarations"] += list(declarations)
    _dump(pack / "variables.yaml", variables)
    if writes is not None:
        actions = _yaml(pack / "actions.yaml")
        advance = next(action for action in actions["actions"]["custom_actions"] if action["name"] == "ADVANCE")
        advance["writes"] = writes
        _dump(pack / "actions.yaml", actions)
    if rules is not None:
        _dump(pack / "transition_rules.yaml", {"version": "1.0", "transition_rules": rules})
    return pack


def _compile(pack: Path, level: str = LEVEL) -> CompiledUniverse:
    return UniverseCompiler().compile(pack, primary_level=level, use_cache=False)


def _env(universe: CompiledUniverse, level: str = LEVEL, num_agents: int = 2) -> VectorizedHamletEnv:
    env = VectorizedHamletEnv.from_universe(universe, level_name=level, num_agents=num_agents, device="cpu")
    env.reset()
    return env


def _advance(env: VectorizedHamletEnv) -> None:
    index = next(i for i, action in enumerate(env.action_space.actions) if action.name == "ADVANCE")
    env.step(torch.full((env.num_agents,), index, dtype=torch.long))


def _read(env: VectorizedHamletEnv, name: str) -> list:
    return env.vfs_registry.get(name, reader="engine").tolist()


def _meter(env: VectorizedHamletEnv, name: str) -> list:
    return env.meters[:, env.meter_name_to_index[name]].tolist()


def _refused(pack: Path, *needles: str, level: str = LEVEL) -> str:
    with pytest.raises(CompilationError) as caught:
        _compile(pack, level)
    message = str(caught.value)
    for needle in needles:
        assert needle in message, message
    return message


# -- the resolver ----------------------------------------------------------------------

NAMESPACE = Namespace(
    variables=[("g", VariableScope.GLOBAL, "scalar"), ("a", VariableScope.AGENT, "scalar"), ("seat", VariableScope.AFFORDANCE, "scalar")],
    meters=["energy"],
    item_profiles={"medical": {"durability": "scalar"}},
)

#: (context, old spelling, the one canonical spelling the refusal names)
OLD_SPELLINGS: list[tuple[ReadContext, str, str]] = [
    (AGENT_EXPRESSION, "vfs.a", "a"),
    (AGENT_EXPRESSION, "energy", "bar.energy"),
    (TRANSITION_WRITE, "vfs.a", "a"),
    (TRANSITION_WRITE, "self.vfs.a", "a"),
    (TRANSITION_WRITE, "target.vfs.a", "a"),
    (TRANSITION_WRITE, "energy", "bar.energy"),
    (TRANSITION_WRITE, "self.bar.energy", "bar.energy"),
    (TRANSITION_WRITE, "target.bar.energy", "bar.energy"),
    (EFFECT_PIPELINE, "vfs.g", "g"),
    (EFFECT_PIPELINE, "global.vfs.g", "g"),
    (EFFECT_PIPELINE, "target.vfs.a", "a"),
    (EFFECT_PIPELINE, "target.bar.energy", "bar.energy"),
    (EFFECT_PIPELINE.with_item(ANY_ITEM), "self.vfs.durability", "item.durability"),
    (EFFECT_PIPELINE.with_item(ANY_ITEM), "target.vfs.durability", "item.durability"),
    (INTERACTION_PIPELINE.with_item(ItemBinding.of_profile("medical")), "self.vfs.durability", "item.durability"),
    (SPAWN_PREDICATE, "vfs.tick", "tick"),
    (SPAWN_PREDICATE, "vfs.g", "g"),
    (SPAWN_PREDICATE, "agent.vfs.a", "a"),
]


@pytest.mark.parametrize(("context", "old", "canonical"), OLD_SPELLINGS, ids=[f"{c.label}:{o}" for c, o, _ in OLD_SPELLINGS])
def test_every_old_spelling_refuses_naming_the_canonical_one(context: ReadContext, old: str, canonical: str) -> None:
    message = NAMESPACE.refusal(old, context)
    assert message is not None
    assert f"write '{canonical}'" in message
    assert NAMESPACE.refusal(canonical, context) is None


@pytest.mark.parametrize(
    ("context", "spelling", "kind", "name"),
    [
        (AGENT_EXPRESSION, "a", SymbolKind.VARIABLE, "a"),
        (AGENT_EXPRESSION, "g", SymbolKind.VARIABLE, "g"),
        (AGENT_EXPRESSION, "tick", SymbolKind.ENGINE, "tick"),
        (AGENT_EXPRESSION, "bar.energy", SymbolKind.METER, "energy"),
        (TRANSITION_WRITE, "seat", SymbolKind.VARIABLE, "seat"),
        (TRANSITION_WRITE, "agent_id", SymbolKind.ENGINE, "agent_id"),
        (EFFECT_PIPELINE, "intensity", SymbolKind.LOCAL, "intensity"),
        (EFFECT_PIPELINE.with_item(ANY_ITEM), "item.durability", SymbolKind.ITEM_STATE, "durability"),
        (SPAWN_PREDICATE, "tick", SymbolKind.ENGINE, "tick"),
    ],
)
def test_canonical_spellings_resolve(context: ReadContext, spelling: str, kind: SymbolKind, name: str) -> None:
    symbol = NAMESPACE.resolve(spelling, context)
    assert (symbol.kind, symbol.name) == (kind, name)


@pytest.mark.parametrize(
    ("context", "spelling", "needle"),
    [
        (EFFECT_PIPELINE, "item.durability", "bound to no item"),
        (INTERACTION_PIPELINE, "intensity", "names no variable"),
        (SPAWN_PREDICATE, "agent_id", "names no variable"),
        (GLOBAL_EXPRESSION, "a", "declared scope 'agent'"),
        (EFFECT_PIPELINE, "seat", "declared scope 'affordance'"),
        (SPAWN_PREDICATE, "env.hour", "is not a reference"),
        (SPAWN_PREDICATE, "temporal.time_of_day", "is not a reference"),
    ],
)
def test_a_qualifier_or_name_the_context_does_not_have_refuses(context: ReadContext, spelling: str, needle: str) -> None:
    message = NAMESPACE.refusal(spelling, context)
    assert message is not None and needle in message, message


def test_schema_and_runtime_cannot_drift_every_spelling_the_schema_admits_the_runtime_serves() -> None:
    """The structural no-drift proof for the shared ``world.expression`` runtime context.

    Every spelling each context's schema admits is read through the runtime
    ``ExecutionContext`` built the way the consumers build it (bare names in ``vfs``,
    meters in ``bars``, item state in ``item_state``), and every old spelling the
    resolver refuses is refused by the runtime too. Both sides parse the same grammar,
    so neither can admit what the other does not.
    """
    item_context = EFFECT_PIPELINE.with_item(ANY_ITEM)
    for context in (AGENT_EXPRESSION, GLOBAL_EXPRESSION, TRANSITION_WRITE, SPAWN_PREDICATE, INTERACTION_PIPELINE, item_context):
        entries = NAMESPACE.entries(context)
        runtime = ExecutionContext(
            bars={symbol.name: torch.tensor([1.0]) for symbol in entries.values() if symbol.kind == SymbolKind.METER},
            vfs={
                symbol.name: torch.tensor([2.0])
                for symbol in entries.values()
                if symbol.kind in {SymbolKind.VARIABLE, SymbolKind.ENGINE, SymbolKind.LOCAL}
            },
            temporal={},
            item_state={symbol.name: torch.tensor(3.0) for symbol in entries.values() if symbol.kind == SymbolKind.ITEM_STATE},
        )
        for spelling in entries:
            runtime.get(spelling)
    runtime = ExecutionContext(bars={"energy": torch.tensor([1.0])}, vfs={"a": torch.tensor([2.0])}, temporal={})
    for _, old, _ in OLD_SPELLINGS:
        if "." in old:
            with pytest.raises(KeyError):
                runtime.get(old)


# -- profile expressions ---------------------------------------------------------------


def test_profile_expression_canonical_spelling_computes(tmp_path: Path) -> None:
    pack = _pack(tmp_path, declarations=[_decl("double_energy", expression="bar.energy * 2.0 + tick * 0.0")])
    env = _env(_compile(pack))
    assert _read(env, "double_energy") == [2.0 * value for value in _meter(env, "energy")]


def test_profile_expression_old_spelling_refuses_at_the_declaration(tmp_path: Path) -> None:
    pack = _pack(tmp_path, declarations=[_decl("doubled", expression="vfs.hidden_score * 2.0")])
    message = _refused(pack, "write 'hidden_score'")
    line = next(number for number, text in enumerate((pack / "variables.yaml").read_text().splitlines(), 1) if "id: doubled" in text)
    assert f"variables.yaml:{line}" in message  # follow-up 5: the variable's line, not variables.yaml:1


def test_profile_cycle_is_located_at_a_variable_on_it(tmp_path: Path) -> None:
    pack = _pack(tmp_path, declarations=[_decl("p", expression="q + 1.0"), _decl("q", expression="p + 1.0")])
    message = _refused(pack, "Circular dependency")
    assert not re.search(r"variables\.yaml:1\b", message), message


# -- action writes and transition rules ------------------------------------------------


def test_action_write_canonical_spellings_write_the_right_storage(tmp_path: Path) -> None:
    pack = _pack(
        tmp_path,
        declarations=[_decl("acc")],
        writes=[_write("acc", "bar.energy + hidden_score"), _write("bar.money", "-0.25")],
    )
    env = _env(_compile(pack))
    energy = _meter(env, "energy")
    hidden = _read(env, "hidden_score")
    money = _meter(env, "money")
    _advance(env)
    assert _read(env, "acc") == pytest.approx([e + h for e, h in zip(energy, hidden, strict=True)])
    assert _meter(env, "money") == pytest.approx([m - 0.25 for m in money])


@pytest.mark.parametrize(
    ("target", "expression", "canonical"),
    [
        ("hidden_score", "vfs.public_state", "public_state"),
        ("hidden_score", "self.vfs.public_state", "public_state"),
        ("hidden_score", "target.vfs.public_state", "public_state"),
        ("hidden_score", "energy", "bar.energy"),
        ("hidden_score", "self.bar.energy", "bar.energy"),
        ("hidden_score", "target.bar.energy", "bar.energy"),
        ("energy", "1.0", "bar.energy"),
    ],
)
def test_action_write_old_spelling_refuses_at_file_line(tmp_path: Path, target: str, expression: str, canonical: str) -> None:
    pack = _pack(tmp_path, writes=[_write(target, expression)])
    message = _refused(pack, f"write '{canonical}'")
    assert "actions.yaml:" in message


def test_transition_rule_canonical_and_old_spellings(tmp_path: Path) -> None:
    pack = _pack(tmp_path, declarations=[_decl("acc")], rules=[_rule("acc", "bar.energy")], name="ok")
    env = _env(_compile(pack))
    energy = _meter(env, "energy")
    _advance(env)
    assert _read(env, "acc") == pytest.approx(energy, abs=0.2)  # passive depletion may run before the rule phase
    pack = _pack(tmp_path, declarations=[_decl("acc")], rules=[_rule("acc", "target.bar.energy")], name="old")
    assert "transition_rules.yaml:" in _refused(pack, "write 'bar.energy'")
    pack = _pack(tmp_path, declarations=[_decl("acc")], rules=[_rule("energy", "1.0")], name="old_target")
    _refused(pack, "write 'bar.energy'")


# -- command pipelines -----------------------------------------------------------------


def _affordance_pack(tmp_path: Path, modify: str, value: str) -> Path:
    pack = _pack(tmp_path, declarations=[_decl("acc")])
    affordances = _yaml(pack / "levels" / LEVEL / "affordances.yaml")
    affordances["affordances"]["affordances"][0]["interactions"]["on_start"] = [{"modify": modify, "value": value}]
    _dump(pack / "levels" / LEVEL / "affordances.yaml", affordances)
    return pack


@pytest.mark.parametrize(
    ("modify", "value", "canonical"),
    [
        ("target.bar.energy", "bar.energy + 0.1", "bar.energy"),
        ("bar.energy", "target.bar.energy + 0.1", "bar.energy"),
        ("target.vfs.acc", "1.0", "acc"),
        ("acc", "vfs.acc + 1.0", "acc"),
    ],
)
def test_affordance_interaction_old_spelling_refuses_at_compile_with_file_line(
    tmp_path: Path, modify: str, value: str, canonical: str
) -> None:
    message = _refused(_affordance_pack(tmp_path, modify, value), f"write '{canonical}'")
    assert "affordances.yaml:" in message


def test_affordance_interaction_reading_an_effect_local_refuses(tmp_path: Path) -> None:
    """An interaction has no active effect, so `intensity` (which compiled before and raised at step) refuses."""
    _refused(_affordance_pack(tmp_path, "acc", "intensity"), "'intensity' names no variable")


def _items_pack(tmp_path: Path, on_use: list[dict], *, spawn_when: str | None = None, declarations: list[dict] = ()) -> Path:  # type: ignore[assignment]
    pack = tmp_path / "items"
    shutil.copytree(ITEMS, pack, ignore=shutil.ignore_patterns(".compiled"))
    items = _yaml(pack / "items.yaml")
    medkit = next(item for item in items["items"]["item_types"] if item["id"] == "medkit")
    medkit["interactions"]["on_use"] = on_use
    _dump(pack / "items.yaml", items)
    if declarations:
        variables = _yaml(pack / "variables.yaml")
        variables["variables"]["declarations"] += list(declarations)
        _dump(pack / "variables.yaml", variables)
    if spawn_when is not None:
        appearance = _yaml(pack / "levels" / ITEMS_LEVEL / "items.yaml")
        appearance["items"][0]["when"] = spawn_when
        _dump(pack / "levels" / ITEMS_LEVEL / "items.yaml", appearance)
    return pack


def test_item_hook_old_item_spelling_refuses_at_compile(tmp_path: Path) -> None:
    pack = _items_pack(tmp_path, [{"modify": "self.vfs.durability", "value": "self.vfs.durability - 10"}])
    message = _refused(pack, "write 'item.durability'", level=ITEMS_LEVEL)
    assert "items.yaml:" in message


def test_item_hook_canonical_spellings_write_the_item_and_the_agent(tmp_path: Path) -> None:
    """Run the compiled hook through the real command executor against the environment's registry."""
    pack = _items_pack(
        tmp_path,
        [
            {"modify": "item.durability", "value": "item.durability - 10"},
            {"modify": "bar.health", "value": "bar.health + 0.25"},
            {"modify": "has_food", "value": "true"},
        ],
    )
    universe = _compile(pack, ITEMS_LEVEL)
    env = _env(universe, ITEMS_LEVEL)
    compiled = next(item for item in env.item_manager.compiled_item_types if item.id == "medkit")
    registry = env.vfs_registry
    row = next(
        index
        for index, profile in registry.item_vfs_index_to_profile.items()
        if profile == "medical" and index // registry.items_per_world == 1
    )
    before = registry.read_item("medical", "durability", row, reader="engine")
    health = _meter(env, "health")
    bars = {name: env.meters[:, idx] for name, idx in env.meter_name_to_index.items()}
    context = EffectContext(bars=bars, vfs_registry=registry, self_index=row, target_index=1, self_is_item=True)
    for command in compiled.compiled_on_use:
        CommandExecutor().execute(command, context)
    assert registry.read_item("medical", "durability", row, reader="engine") == pytest.approx(float(before) - 10.0)
    assert _meter(env, "health")[1] == pytest.approx(health[1] + 0.25)
    assert _meter(env, "health")[0] == pytest.approx(health[0])  # world 0 untouched (S1)
    assert _read(env, "has_food") == [False, True]


def test_effect_old_spellings_refuse_and_canonical_compile() -> None:
    compiler = command_compiler({"g": "float", "a": "float", "bar.energy": "float"}, scopes={"g": "global"})
    parser = CommandParser()
    compiler.compile_commands(parser.parse_commands([CommandConfig(modify="a", value="g + bar.energy * intensity")]))
    for modify, value, canonical in (("vfs.a", "1.0", "a"), ("a", "global.vfs.g", "g"), ("target.bar.energy", "1.0", "bar.energy")):
        with pytest.raises(TypeCheckError, match=re.escape(f"write '{canonical}'")):
            compiler.compile_commands(parser.parse_commands([CommandConfig(modify=modify, value=value)]))
    item_compiler = command_compiler({"item.charge": "float"}, item=True)
    item_compiler.compile_commands(parser.parse_commands([CommandConfig(modify="item.charge", value="item.charge - 1.0")]))
    with pytest.raises(TypeCheckError, match=re.escape("write 'item.charge'")):
        item_compiler.compile_commands(parser.parse_commands([CommandConfig(modify="self.vfs.charge", value="1.0")]))
    with pytest.raises(TypeCheckError, match="bound to no item"):
        command_compiler({"item.charge": "float"}).compile_commands(
            parser.parse_commands([CommandConfig(modify="item.charge", value="1.0")])
        )


def test_effect_runtime_reads_and_writes_this_worlds_rows(tmp_path: Path) -> None:
    """A global-scoped effect bound to world 1 reads and writes world 1's agent and global rows only."""
    pack = _pack(tmp_path, declarations=[_decl("acc"), _decl("world_acc", scope="global")])
    env = _env(_compile(pack))
    compiler = CommandCompiler_for(env)
    commands = compiler.compile_commands(
        CommandParser().parse_commands(
            [CommandConfig(modify="acc", value="acc + bar.energy"), CommandConfig(modify="world_acc", value="world_acc + 2.0")]
        )
    )
    bars = {name: env.meters[:, idx] for name, idx in env.meter_name_to_index.items()}
    energy = _meter(env, "energy")

    class _Effect:
        world = 1
        intensity = 1.0
        elapsed_ticks = 0
        duration_remaining = 1

    context = EffectContext(bars=bars, vfs_registry=env.vfs_registry, effect=_Effect())
    for command in commands:
        CommandExecutor().execute(command, context)
    assert _read(env, "acc") == pytest.approx([0.0, energy[1]])
    assert _read(env, "world_acc") == [0.0, 2.0]


def CommandCompiler_for(env: VectorizedHamletEnv):  # noqa: N802
    from townlet.effects.compiler import CommandCompiler

    return CommandCompiler(
        env.command_symbols.namespace, context=EFFECT_PIPELINE, time_enabled=True, expressions=env.command_symbols.expressions
    )


def test_compiler_and_environment_build_one_command_namespace(tmp_path: Path) -> None:
    """The no-drift proof for command pipelines: the compiler's namespace, built from the raw declarations as stage 6
    builds it, equals the environment's, built from the compiled artifact, entry for entry."""
    from townlet.universe.compilers.effects import EffectsCompiler
    from townlet.universe.compilers.vfs import VFSCompiler
    from townlet.universe.declarations import DeclarationStore
    from townlet.universe.raw_configs_v21 import RawConfigsV21

    universe = _compile(ITEMS, ITEMS_LEVEL)
    env = _env(universe, ITEMS_LEVEL)
    raw = RawConfigsV21.from_declarations(DeclarationStore.discover(ITEMS))
    compiled = (
        EffectsCompiler()
        .build_symbols(
            variables=VFSCompiler().build_runtime_variables(raw.variables),
            meter_names=tuple(meter.name for meter in raw.levels[ITEMS_LEVEL].bars.meters),
            compiled_vfs_profiles=universe.compiled_vfs_profiles,
            expressions={},
            time_enabled=True,
        )
        .namespace
    )
    for context in (
        INTERACTION_PIPELINE,
        INTERACTION_PIPELINE.with_item(ItemBinding.of_profile("medical")),
        EFFECT_PIPELINE,
        EFFECT_PIPELINE.with_item(ANY_ITEM),
    ):
        assert compiled.entries(context) == env.command_symbols.namespace.entries(context)


def test_every_effect_spelling_the_schema_admits_the_effect_runtime_serves(tmp_path: Path) -> None:
    """The F6 class for command pipelines: each spelling of an item-bound effect's schema reads through the real
    executor context over the environment's registry; an old spelling is served by neither side."""
    universe = _compile(ITEMS, ITEMS_LEVEL)
    env = _env(universe, ITEMS_LEVEL)
    registry = env.vfs_registry
    row = next(index for index, profile in registry.item_vfs_index_to_profile.items() if profile == "medical")
    bars = {name: env.meters[:, idx] for name, idx in env.meter_name_to_index.items()}

    class _Effect:
        world = registry.item_world(row)
        intensity = 1.0
        elapsed_ticks = 0
        duration_remaining = 1

    context = EffectContext(bars=bars, vfs_registry=registry, self_index=row, target_index=row, self_is_item=True, target_is_item=True)
    context.effect = _Effect()
    runtime = CommandExecutor()._make_eval_context(context)
    schema = env.command_symbols.namespace.schema(EFFECT_PIPELINE.with_item(ANY_ITEM))
    medical = {name for name in schema if not name.startswith("item.")} | {f"item.{name}" for name in registry.item_profile_map["medical"]}
    for spelling in medical:
        runtime.get(spelling)
    for old in ("vfs.has_food", "target.bar.energy", "self.vfs.durability", "global.vfs.tick"):
        with pytest.raises(KeyError):
            runtime.get(old)


# -- item spawn predicates ---------------------------------------------------------------


def test_spawn_predicate_canonical_spelling_compiles_and_old_refuses(tmp_path: Path) -> None:
    universe = _compile(_items_pack(tmp_path, [], spawn_when="tick >= 0.0 and bar.energy >= 0.0"), ITEMS_LEVEL)
    rule = universe.get_level(ITEMS_LEVEL).items_appearance.items[0]
    env = _env(universe, ITEMS_LEVEL)
    bars = {name: env.meters[:, idx] for name, idx in env.meter_name_to_index.items()}
    context = SpawnPredicateReads.context(bars=bars, registry=env.vfs_registry, device=torch.device("cpu"))
    assert Evaluator(context).evaluate(rule.when_ast).tolist() == [True, True]
    shutil.rmtree(tmp_path / "items")
    _refused(_items_pack(tmp_path, [], spawn_when="vfs.tick >= 0.0"), "write 'tick'", level=ITEMS_LEVEL)


# -- follow-ups 2 and 3: tick-lifetime expressions and history in spawns and effects -----


def test_spawn_predicate_calling_a_history_operator_refuses_at_compile(tmp_path: Path) -> None:
    _refused(_items_pack(tmp_path, [], spawn_when="lag(tick, 1) >= 0.0"), "'lag'", "temporal history", level=ITEMS_LEVEL)


def test_spawn_predicate_inlines_a_pure_tick_lifetime_expression(tmp_path: Path) -> None:
    pack = _items_pack(
        tmp_path,
        [],
        spawn_when="ready",
        declarations=[_decl("ready", scope="global", type="bool", lifetime="tick", expression="tick >= 0.0")],
    )
    rule = _compile(pack, ITEMS_LEVEL).get_level(ITEMS_LEVEL).items_appearance.items[0]
    assert read_paths(rule.when_ast) == {"tick"}  # `ready` is substituted by its expression


def test_spawn_predicate_reading_a_context_bound_tick_lifetime_expression_refuses(tmp_path: Path) -> None:
    pack = _items_pack(
        tmp_path,
        [],
        spawn_when="trend > 0.0",
        declarations=[_decl("trend", scope="global", lifetime="tick", expression="delta(tick)")],
    )
    _refused(pack, "tick-lifetime expression variable 'trend'", level=ITEMS_LEVEL)


def test_command_pipeline_inlines_pure_expressions_and_refuses_context_bound_tick_lifetime_ones(tmp_path: Path) -> None:
    pack = _items_pack(
        tmp_path,
        [{"modify": "bar.health", "value": "boost"}],
        declarations=[_decl("boost", lifetime="tick", expression="bar.energy * 0.5")],
    )
    universe = _compile(pack, ITEMS_LEVEL)
    env = _env(universe, ITEMS_LEVEL)
    compiled = next(item for item in env.item_manager.compiled_item_types if item.id == "medkit")
    assert read_paths(compiled.compiled_on_use[0].value_ast) == {"bar.energy"}  # inlined, not a reset literal
    shutil.rmtree(tmp_path / "items")
    pack = _items_pack(
        tmp_path,
        [{"modify": "bar.health", "value": "trend"}],
        declarations=[_decl("trend", lifetime="tick", expression="delta(bar.energy)")],
    )
    _refused(pack, "tick-lifetime expression variable 'trend'", level=ITEMS_LEVEL)


def test_cached_artifact_inlines_exactly_as_the_fresh_compile(tmp_path: Path) -> None:
    pack = _items_pack(
        tmp_path,
        [{"modify": "bar.health", "value": "boost"}],
        spawn_when="ready",
        declarations=[
            _decl("boost", lifetime="tick", expression="bar.energy * 0.5"),
            _decl("ready", type="bool", scope="global", lifetime="tick", expression="tick >= 0.0"),
        ],
    )
    fresh = UniverseCompiler().compile(pack, primary_level=ITEMS_LEVEL, use_cache=True)
    cached = UniverseCompiler().compile(pack, primary_level=ITEMS_LEVEL, use_cache=True)
    fresh_rule = fresh.get_level(ITEMS_LEVEL).items_appearance.items[0]
    cached_rule = cached.get_level(ITEMS_LEVEL).items_appearance.items[0]
    assert fresh_rule.when_ast == cached_rule.when_ast


# -- follow-up 4: one history-operator list ----------------------------------------------


def test_history_operators_are_one_predicate_on_function_specs() -> None:
    assert TEMPORAL_FUNCTIONS == {name for name, spec in FUNCTION_SPECS.items() if REQUIRES_HISTORY in spec.requires}
    assert "lag" in TEMPORAL_FUNCTIONS and "elapsed_ticks" not in TEMPORAL_FUNCTIONS
    import townlet.effects.compiler as effects_compiler
    import townlet.world.expression.history as history

    assert not hasattr(effects_compiler, "HISTORY_FUNCTIONS")
    assert not hasattr(history, "TEMPORAL_FUNCTIONS")


@pytest.mark.parametrize("call", ["lag(a, 1)", "delta(a)"])
def test_effects_refuse_context_bound_functions_by_the_same_predicate(call: str) -> None:
    compiler = command_compiler({"a": "float"})
    with pytest.raises(TypeCheckError, match="does not carry"):
        compiler.compile_commands(CommandParser().parse_commands([CommandConfig(modify="a", value=call)]))


# -- follow-up 6: the transition-rule phase ----------------------------------------------


def test_the_rule_phase_is_named_for_the_family() -> None:
    assert "apply_transition_rules" in DEFAULT_TRANSITION_PHASES
    assert not any("social" in phase for phase in DEFAULT_TRANSITION_PHASES)


# -- item 7: same-typed reference reads in writes ----------------------------------------


REFS = [_decl("aref", type="agent_ref"), _decl("aref2", type="agent_ref"), _decl("iref", type="item_ref"), _decl("iref2", type="item_ref")]


@pytest.mark.parametrize(
    ("target", "expression"),
    [
        ("aref", "aref2"),
        ("aref", "where(bar.energy > 0.5, aref2, -1)"),
        ("aref", "if bar.energy > 0.5 then aref2 else -1"),
        ("aref", "where(bar.energy > 0.5, agent_id, -1)"),
        ("iref", "iref2"),
        ("iref", "where(bar.energy > 0.5, iref2, -1)"),
    ],
)
def test_a_reference_target_admits_a_same_typed_reference_read(tmp_path: Path, target: str, expression: str) -> None:
    for kind, payload in (
        ("write", {"writes": [_write(target, expression, composition="overwrite")]}),
        ("rule", {"rules": [_rule(target, expression, composition="overwrite")]}),
    ):
        env = _env(_compile(_pack(tmp_path, declarations=REFS, name=f"{kind}", **payload)))
        _advance(env)
        assert len(_read(env, target)) == 2


@pytest.mark.parametrize(
    ("target", "expression", "needle"),
    [
        ("iref", "aref2", "declared item_ref"),
        ("aref", "iref2", "declared agent_ref"),
        ("aref", "aref2 + 1", "'aref2 + 1'"),
        ("iref", "where(bar.energy > 0.5, iref2, 0)", "not provably an entity"),
    ],
)
def test_a_reference_target_refuses_cross_typed_reads_and_arithmetic(tmp_path: Path, target: str, expression: str, needle: str) -> None:
    for kind, payload in (
        ("write", {"writes": [_write(target, expression, composition="overwrite")]}),
        ("rule", {"rules": [_rule(target, expression, composition="overwrite")]}),
    ):
        _refused(_pack(tmp_path, declarations=REFS, name=f"{kind}_{target}", **payload), needle)
