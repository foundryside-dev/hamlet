"""Compiler-owned static identity extraction for executable affordance behavior."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal, cast

from townlet.config.affordances_v2_config import AffordanceParamConfig, OpeningHoursConfig
from townlet.config.effects_config import EffectScope, ReapplyPolicy
from townlet.effects.catalog import CompiledEffect, EffectCatalog
from townlet.effects.parser import CommandParser
from townlet.effects.schema import CommandNode, CommandType
from townlet.numeric import require_float32
from townlet.world.expression import ExpressionParser
from townlet.world.expression.ast_nodes import BinaryOp, Constant, OperatorType, PathAccess

AFFORDANCE_LIFECYCLE_STAGES = ("on_start", "per_tick", "on_completion", "on_early_exit", "on_failure")
EFFECT_LIFECYCLE_STAGES = ("on_spawn", "on_tick", "on_despawn", "on_interrupt")
AFFORDANCE_WRITE_SOURCES = (
    "interaction",
    "cost",
    "cost_per_tick",
    "spawn_effect_on_spawn",
    "spawn_effect_on_tick",
    "spawn_effect_on_despawn",
    "spawn_effect_on_interrupt",
)
AFFORDANCE_WRITE_TARGETS = ("target", "self", "all")
SPAWN_EFFECT_TARGETS = ("target", "index_zero")

AffordanceLifecycleStage = Literal["on_start", "per_tick", "on_completion", "on_early_exit", "on_failure"]
AffordanceWriteSource = Literal[
    "interaction",
    "cost",
    "cost_per_tick",
    "spawn_effect_on_spawn",
    "spawn_effect_on_tick",
    "spawn_effect_on_despawn",
    "spawn_effect_on_interrupt",
]
AffordanceWriteTarget = Literal["target", "self", "all"]
SpawnEffectTarget = Literal["target", "index_zero"]


@dataclass(frozen=True)
class SpawnedEffectIdentity:
    """Executable spawn/effect identity retained on every flattened meter write."""

    target: SpawnEffectTarget
    intensity: float
    duration: int
    scope: str
    reapply_policy: str
    observable: bool

    def __post_init__(self) -> None:
        if self.target not in SPAWN_EFFECT_TARGETS:
            raise ValueError(f"Spawned effect target must be one of {SPAWN_EFFECT_TARGETS}, got {self.target!r}")
        object.__setattr__(
            self,
            "intensity",
            require_float32(self.intensity, field="spawned effect command intensity"),
        )
        if self.duration <= 0:
            raise ValueError(f"Spawned effect duration must be > 0 ticks, got {self.duration}")
        if self.scope not in tuple(member.value for member in EffectScope):
            raise ValueError(f"Spawned effect scope must be an EffectScope, got {self.scope!r}")
        if self.reapply_policy not in tuple(member.value for member in ReapplyPolicy):
            raise ValueError(f"Spawned effect reapply policy must be a ReapplyPolicy, got {self.reapply_policy!r}")


@dataclass(frozen=True)
class AffordanceMeterWrite:
    """One reachable meter write, retaining behavioral origin and target."""

    meter_name: str
    form: Literal[-1, 1]
    delta: float | None
    stage: AffordanceLifecycleStage
    source: AffordanceWriteSource
    target: AffordanceWriteTarget
    spawned_effect: SpawnedEffectIdentity | None

    def __post_init__(self) -> None:
        if not self.meter_name:
            raise ValueError("Affordance meter write must identify a target meter")
        if self.form not in (-1, 1):
            raise ValueError(f"Affordance meter write form must be -1 or 1, got {self.form}")
        if self.form == 1 and self.delta is None:
            raise ValueError("A direct affordance meter write must declare its literal delta")
        if self.delta is not None:
            object.__setattr__(self, "delta", require_float32(self.delta, field="affordance meter write delta"))
        if self.stage not in AFFORDANCE_LIFECYCLE_STAGES:
            raise ValueError(f"Affordance meter write stage must be one of {AFFORDANCE_LIFECYCLE_STAGES}, got {self.stage!r}")
        if self.source not in AFFORDANCE_WRITE_SOURCES:
            raise ValueError(f"Affordance meter write source must be one of {AFFORDANCE_WRITE_SOURCES}, got {self.source!r}")
        if self.target not in AFFORDANCE_WRITE_TARGETS:
            raise ValueError(f"Affordance meter write target must be one of {AFFORDANCE_WRITE_TARGETS}, got {self.target!r}")
        is_spawned = self.source.startswith("spawn_effect_")
        if is_spawned != (self.spawned_effect is not None):
            if is_spawned:
                requirement = "requires"
            else:
                requirement = "must not carry"
            raise ValueError(f"Affordance meter write source {self.source!r} {requirement} spawned_effect identity")


def extract_affordance_meter_writes(
    affordance: AffordanceParamConfig,
    *,
    effect_catalog: EffectCatalog | None,
) -> tuple[AffordanceMeterWrite, ...]:
    """Extract every reachable meter write without aggregating declarations.

    The executable command AST and compiled effect catalog are the sole source. Costs
    are inserted at the lifecycle points where the runtime applies them. Spawned
    effects are resolved recursively; missing references and cycles fail loudly.
    """
    command_parser = CommandParser()
    expression_parser = ExpressionParser()  # type: ignore[no-untyped-call]
    writes: list[AffordanceMeterWrite] = []
    for stage_name in AFFORDANCE_LIFECYCLE_STAGES:
        stage = _lifecycle_stage(stage_name)
        if stage == "on_start":
            writes.extend(_cost_writes(affordance.costs, stage=stage, source="cost"))
        if stage == "per_tick":
            writes.extend(_cost_writes(affordance.costs_per_tick, stage=stage, source="cost_per_tick"))
        if stage in affordance.interactions:
            stage_commands = affordance.interactions[stage]
        else:
            stage_commands = []
        commands = command_parser.parse_commands(stage_commands)
        writes.extend(
            _meter_writes(
                commands,
                expression_parser,
                effect_catalog,
                affordance.name,
                stage,
                source="interaction",
                dynamic=False,
                effect_path=(),
                spawned_effect=None,
            )
        )
    return tuple(writes)


def opening_hours_signature(opening_hours: OpeningHoursConfig) -> tuple[float, ...]:
    """Exact 24-lane availability identity for integer-hour runtime windows."""
    if not opening_hours.enabled:
        return (1.0,) * 24

    open_hours = [0.0] * 24
    for window in opening_hours.schedule:
        start_raw = int(window.start)
        end_raw = int(window.end)
        start = start_raw % 24
        end = end_raw % 24
        always_open = (end_raw - start_raw) % 24 == 0
        for hour in range(24):
            if always_open:
                inside = True
            elif start < end:
                inside = start <= hour < end
            else:
                inside = hour >= start
                if not inside:
                    inside = hour < end
            if inside:
                open_hours[hour] = 1.0
    return tuple(open_hours)


def _cost_writes(
    costs: dict[str, float],
    *,
    stage: AffordanceLifecycleStage,
    source: Literal["cost", "cost_per_tick"],
) -> Iterable[AffordanceMeterWrite]:
    for meter_name, amount in costs.items():
        yield AffordanceMeterWrite(meter_name, 1, -float(amount), stage, source, "target", None)


def _meter_writes(
    commands: Iterable[CommandNode],
    expression_parser: ExpressionParser,
    effect_catalog: EffectCatalog | None,
    affordance_name: str,
    stage: AffordanceLifecycleStage,
    *,
    source: AffordanceWriteSource,
    dynamic: bool,
    effect_path: tuple[str, ...],
    spawned_effect: SpawnedEffectIdentity | None,
) -> Iterable[AffordanceMeterWrite]:
    for command in commands:
        if command.type == CommandType.MODIFY:
            assert command.path is not None and command.value_expr is not None
            meter_target = _meter_target(command.path, affordance_name, stage)
            if meter_target is not None:
                meter_name, target = meter_target
                expression = expression_parser.parse(command.value_expr)
                delta = _affine_delta(command.path, expression, affordance_name=affordance_name, stage=stage)
                yield AffordanceMeterWrite(
                    meter_name,
                    -1 if dynamic or delta is None else 1,
                    delta,
                    stage,
                    source,
                    target,
                    spawned_effect,
                )
            continue

        if command.type == CommandType.SPAWN_EFFECT:
            yield from _spawned_effect_writes(
                command,
                expression_parser,
                effect_catalog,
                affordance_name,
                stage,
                effect_path=effect_path,
            )
        elif command.type == CommandType.IF:
            yield from _nested_writes(
                command.then_commands, expression_parser, effect_catalog, affordance_name, stage, source, effect_path, spawned_effect
            )
            yield from _nested_writes(
                command.else_commands, expression_parser, effect_catalog, affordance_name, stage, source, effect_path, spawned_effect
            )
        elif command.type == CommandType.SWITCH:
            for _when, branch in command.cases or ():
                yield from _nested_writes(
                    branch, expression_parser, effect_catalog, affordance_name, stage, source, effect_path, spawned_effect
                )
            yield from _nested_writes(
                command.default_commands,
                expression_parser,
                effect_catalog,
                affordance_name,
                stage,
                source,
                effect_path,
                spawned_effect,
            )
        elif command.type == CommandType.PARALLEL:
            yield from _meter_writes(
                command.parallel_commands or (),
                expression_parser,
                effect_catalog,
                affordance_name,
                stage,
                source=source,
                dynamic=dynamic,
                effect_path=effect_path,
                spawned_effect=spawned_effect,
            )
        elif command.type in {CommandType.DELAY, CommandType.FOR_EACH}:
            if command.type == CommandType.DELAY:
                nested = command.delay_commands
            else:
                nested = command.body
            yield from _nested_writes(
                nested, expression_parser, effect_catalog, affordance_name, stage, source, effect_path, spawned_effect
            )
        elif command.type == CommandType.SAMPLE:
            meter_target = _meter_target(command.sample_store_path, affordance_name, stage)
            if meter_target is not None:
                meter_name, target = meter_target
                yield AffordanceMeterWrite(meter_name, -1, None, stage, source, target, spawned_effect)
        elif command.type == CommandType.REDUCE:
            meter_target = _meter_target(command.reduce_target, affordance_name, stage)
            if meter_target is not None:
                meter_name, target = meter_target
                yield AffordanceMeterWrite(meter_name, -1, None, stage, source, target, spawned_effect)
        elif command.type != CommandType.SPAWN_ITEM:
            raise AssertionError(f"Unhandled affordance command type in static identity extraction: {command.type}")


def _nested_writes(
    commands: Iterable[CommandNode] | None,
    expression_parser: ExpressionParser,
    effect_catalog: EffectCatalog | None,
    affordance_name: str,
    stage: AffordanceLifecycleStage,
    source: AffordanceWriteSource,
    effect_path: tuple[str, ...],
    spawned_effect: SpawnedEffectIdentity | None,
) -> Iterable[AffordanceMeterWrite]:
    return _meter_writes(
        commands or (),
        expression_parser,
        effect_catalog,
        affordance_name,
        stage,
        source=source,
        dynamic=True,
        effect_path=effect_path,
        spawned_effect=spawned_effect,
    )


def _spawned_effect_writes(
    command: CommandNode,
    expression_parser: ExpressionParser,
    effect_catalog: EffectCatalog | None,
    affordance_name: str,
    stage: AffordanceLifecycleStage,
    *,
    effect_path: tuple[str, ...],
) -> Iterable[AffordanceMeterWrite]:
    effect_id = command.effect_id
    if effect_id is None:
        raise ValueError(f"Affordance {affordance_name!r} stage {stage!r}: spawn_effect has no effect reference")
    if effect_catalog is None or effect_id not in effect_catalog.effects:
        raise ValueError(f"Affordance {affordance_name!r} stage {stage!r}: spawn_effect references missing effect {effect_id!r}")
    if effect_id in effect_path:
        cycle = " -> ".join((*effect_path, effect_id))
        raise ValueError(f"Affordance {affordance_name!r} stage {stage!r}: spawn_effect cycle: {cycle}")
    if effect_path:
        chain = " -> ".join((*effect_path, effect_id))
        raise ValueError(
            f"Affordance {affordance_name!r} stage {stage!r}: nested spawn_effect chain {chain} "
            "cannot be represented by the fixed-width affordance identity"
        )

    effect = effect_catalog.effects[effect_id]
    spawn_identity = SpawnedEffectIdentity(
        target=_spawn_target(command, affordance_name=affordance_name, stage=stage),
        intensity=_spawn_intensity(command, affordance_name=affordance_name, stage=stage),
        duration=effect.duration,
        scope=effect.scope,
        reapply_policy=effect.reapply_policy,
        observable=effect.observable,
    )
    next_path = (*effect_path, effect_id)
    for effect_stage in EFFECT_LIFECYCLE_STAGES:
        yield from _meter_writes(
            _effect_commands(effect, effect_stage),
            expression_parser,
            effect_catalog,
            affordance_name,
            stage,
            source=_effect_source(effect_stage),
            dynamic=True,
            effect_path=next_path,
            spawned_effect=spawn_identity,
        )


def _spawn_target(command: CommandNode, *, affordance_name: str, stage: str) -> SpawnEffectTarget:
    if command.target == "target":
        return "target"
    if command.target == 0:
        return "index_zero"
    rendered: str | int | None
    if command.target is None:
        rendered = command.target_expr
    else:
        rendered = command.target
    raise ValueError(
        f"Affordance {affordance_name!r} stage {stage!r}: spawn_effect target {rendered!r} "
        "cannot execute from an affordance context or be represented exactly; use 'target' or explicit index 0"
    )


def _spawn_intensity(command: CommandNode, *, affordance_name: str, stage: str) -> float:
    if command.intensity is None:
        raise ValueError(f"Affordance {affordance_name!r} stage {stage!r}: spawn_effect intensity must be an explicit float32 literal")
    return require_float32(
        command.intensity,
        field=f"affordance {affordance_name!r} stage {stage!r} spawn_effect intensity",
    )


def _effect_commands(effect: CompiledEffect, stage: str) -> list[CommandNode]:
    commands = getattr(effect, stage)
    assert isinstance(commands, list)
    return commands


def _effect_source(stage: str) -> AffordanceWriteSource:
    source = f"spawn_effect_{stage}"
    if source not in AFFORDANCE_WRITE_SOURCES:
        raise AssertionError(f"Unhandled effect lifecycle stage in affordance identity: {stage}")
    return cast(AffordanceWriteSource, source)


def _lifecycle_stage(stage: str) -> AffordanceLifecycleStage:
    if stage not in AFFORDANCE_LIFECYCLE_STAGES:
        raise AssertionError(f"Unhandled affordance lifecycle stage in static identity: {stage}")
    return cast(AffordanceLifecycleStage, stage)


def _meter_target(path: str | None, affordance_name: str, stage: str) -> tuple[str, AffordanceWriteTarget] | None:
    if path is None:
        return None
    prefixes: tuple[tuple[str, AffordanceWriteTarget], ...] = (
        ("target.bar.", "target"),
        ("self.bar.", "self"),
        ("bar.", "all"),
    )
    for prefix, target in prefixes:
        if path.startswith(prefix):
            meter_name = path.removeprefix(prefix)
            if not meter_name or "." in meter_name:
                raise ValueError(
                    f"Affordance {affordance_name!r} stage {stage!r}: meter write path {path!r} " "does not identify exactly one meter"
                )
            return meter_name, target
    return None


def _affine_delta(
    path: str,
    expression: object,
    *,
    affordance_name: str,
    stage: str,
) -> float | None:
    if isinstance(expression, BinaryOp) and expression.op in {OperatorType.ADD, OperatorType.SUB}:
        if _is_path(expression.left, path) and isinstance(expression.right, Constant) and _is_number(expression.right.value):
            value = float(expression.right.value)
            if expression.op == OperatorType.ADD:
                delta = value
            else:
                delta = -value
            return _require_finite_affine(delta, affordance_name=affordance_name, stage=stage, path=path)
        if (
            expression.op == OperatorType.ADD
            and isinstance(expression.left, Constant)
            and _is_number(expression.left.value)
            and _is_path(expression.right, path)
        ):
            return _require_finite_affine(float(expression.left.value), affordance_name=affordance_name, stage=stage, path=path)
    return None


def _require_finite_affine(delta: float, *, affordance_name: str, stage: str, path: str) -> float:
    return require_float32(
        delta,
        field=f"affordance {affordance_name!r} stage {stage!r} affine literal delta for {path!r}",
    )


def _is_path(node: object, path: str) -> bool:
    return isinstance(node, PathAccess) and node.segments == path.split(".")


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


__all__ = [
    "AFFORDANCE_LIFECYCLE_STAGES",
    "AFFORDANCE_WRITE_SOURCES",
    "AFFORDANCE_WRITE_TARGETS",
    "EFFECT_LIFECYCLE_STAGES",
    "SPAWN_EFFECT_TARGETS",
    "AffordanceMeterWrite",
    "SpawnedEffectIdentity",
    "extract_affordance_meter_writes",
    "opening_hours_signature",
]
