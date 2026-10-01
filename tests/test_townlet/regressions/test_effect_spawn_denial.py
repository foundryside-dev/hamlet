"""Rejected lifecycle writes must precede any effect admission/reapplication state."""

from copy import deepcopy
from dataclasses import asdict

import pytest
import torch

from townlet.effects.catalog import CompiledEffect, EffectCatalog
from townlet.effects.compiler import CommandCompiler
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.manager import EffectManager
from townlet.effects.schema import CommandNode, CommandType
from townlet.vfs.profiles import CompiledItemProfile, CompiledVariable
from townlet.vfs.registry import VariableRegistry


def _setup(policy: str) -> tuple[EffectManager, VariableRegistry, dict[str, torch.Tensor]]:
    profiles = {
        profile: CompiledItemProfile(
            profile_name=profile,
            variables=[
                CompiledVariable(
                    name="charge",
                    type="float",
                    exposed_to=(),
                    lifetime="episode",
                    readable_by=("engine",),
                    writable_by=writers,
                    initial_value=2.0,
                )
            ],
        )
        for profile, writers in [("writable", ("engine",)), ("sealed", ())]
    }
    registry = VariableRegistry([], 2, torch.device("cpu"), max_items=2, item_profiles=profiles)
    for index, profile in enumerate(profiles):
        registry._initialize_item_row(profile, index)
        registry.register_item_instance(index, profile)
    effect = CompiledEffect(
        id="charging",
        scope="item",
        duration=5,
        reapply_policy=policy,
        observable=True,
        on_spawn=[],
        on_tick=[_write("bar.energy", "bar.energy + 1.0")],
        on_despawn=[],
        on_interrupt=[],
    )
    manager = EffectManager(
        catalog=EffectCatalog(effects={effect.id: effect}, max_active_effects={"global": 0, "agent": 0, "item": 2, "affordance": 0}),
        command_executor=CommandExecutor(),
    )
    return manager, registry, {"energy": torch.full((2,), 3.0)}


def _write(path: str, value: str) -> CommandNode:
    return CommandCompiler({"self.vfs.charge": "float", "bar.energy": "float"}).compile_command(
        CommandNode(type=CommandType.MODIFY, path=path, value_expr=value)
    )


def _pipeline_with_denial() -> list[CommandNode]:
    """Earlier mutation, RNG and scheduling expose a late authorization failure."""
    compiler = CommandCompiler({"self.vfs.charge": "float", "bar.energy": "float"})
    return compiler.compile_commands(
        [
            CommandNode(type=CommandType.MODIFY, path="bar.energy", value_expr="9.0"),
            CommandNode(
                type=CommandType.SAMPLE,
                sample_store_path="bar.energy",
                sample_distribution="uniform",
                sample_params={"min": 0.0, "max": 1.0},
            ),
            CommandNode(type=CommandType.DELAY, delay_ticks_expr="2", delay_commands=[_write("bar.energy", "7.0")]),
            CommandNode(type=CommandType.MODIFY, path="self.vfs.charge", value_expr="2.0"),
        ]
    )


@pytest.mark.parametrize("entry", ["manager", "command"])
def test_denied_item_spawn_cannot_leave_a_live_effect(entry: str) -> None:
    manager, registry, bars = _setup("stack")
    manager.catalog.effects["charging"].on_spawn = [_write("self.vfs.charge", "2.0")]
    with pytest.raises(PermissionError, match="sealed"):
        if entry == "manager":
            manager.spawn_effect("charging", 1, 1.0, 0, bars=bars, vfs_registry=registry)
        else:
            command = CommandCompiler({}).compile_command(
                CommandNode(type=CommandType.SPAWN_EFFECT, effect_id="charging", target_expr="1 + 0", intensity=1.0)
            )
            CommandExecutor().execute(command, ExecutionContext(bars=bars, vfs_registry=registry, effect_manager=manager))
    # A later tick must not execute the rejected effect's otherwise permitted hook.
    manager.tick(bars, registry, current_step=1)
    assert torch.equal(bars["energy"], torch.full((2,), 3.0))
    assert manager.get_all_active_effects() == []
    assert manager.item_effects == {}
    assert manager.next_instance_id == 0


@pytest.mark.parametrize(
    "policy, denied_hook", [("stack", "on_spawn"), ("merge", "on_interrupt"), ("replace", "on_interrupt"), ("replace", "on_spawn")]
)
def test_denied_reapplication_preserves_existing_effect_and_all_state(policy: str, denied_hook: str) -> None:
    manager, registry, bars = _setup(policy)
    existing = manager.spawn_effect("charging", 1, 1.0, 0, bars=bars, vfs_registry=registry)
    existing.duration_remaining = 3
    existing.elapsed_ticks = 2
    manager.scheduler.schedule([_write("bar.energy", "5.0")], 4, scope="item", entity_id=1)
    effect = manager.catalog.effects["charging"]
    setattr(effect, denied_hook, _pipeline_with_denial())
    if policy == "replace" and denied_hook == "on_spawn":
        effect.on_interrupt = [_write("bar.energy", "6.0")]
    before_effect = asdict(existing)
    before_pending = deepcopy(manager.scheduler.pending)
    before_rng = torch.get_rng_state().clone()
    assert registry.item_vfs is not None
    before_vfs = registry.item_vfs.clone()
    with pytest.raises(PermissionError, match="sealed"):
        manager.spawn_effect("charging", 1, 0.5, 2, bars=bars, vfs_registry=registry)
    assert torch.equal(bars["energy"], torch.full((2,), 3.0))
    assert torch.equal(registry.item_vfs, before_vfs)
    assert torch.equal(torch.get_rng_state(), before_rng)
    assert manager.scheduler.pending == before_pending
    assert asdict(existing) == before_effect
    assert manager.get_all_active_effects() == [existing]
    assert manager.next_instance_id == 1


def test_item_spawn_authorizes_the_resolved_profile() -> None:
    manager, registry, bars = _setup("stack")
    manager.catalog.effects["charging"].on_spawn = [_write("self.vfs.charge", "4.0")]
    manager.spawn_effect("charging", 0, 1.0, 0, bars=bars, vfs_registry=registry)
    assert registry.read_item("writable", "charge", 0, reader="engine") == 4.0
    with pytest.raises(PermissionError, match="sealed"):
        manager.spawn_effect("charging", 1, 1.0, 0, bars=bars, vfs_registry=registry)
    assert len(manager.get_all_active_effects()) == 1
    assert registry.read_item("sealed", "charge", 1, reader="engine") == 2.0


@pytest.mark.parametrize("policy", ["renew", "merge"])
def test_reapplication_does_not_authorize_unused_spawn_hook(policy: str) -> None:
    manager, registry, bars = _setup(policy)
    existing = manager.spawn_effect("charging", 1, 1.0, 0, bars=bars, vfs_registry=registry)
    existing.duration_remaining = 2
    manager.catalog.effects["charging"].on_spawn = [_write("self.vfs.charge", "9.0")]
    reapplied = manager.spawn_effect("charging", 1, 0.5, 1, bars=bars, vfs_registry=registry)
    assert reapplied is existing
    assert existing.duration_remaining == (5 if policy == "renew" else 2)
    assert existing.intensity == (1.0 if policy == "renew" else 1.5)
    assert manager.next_instance_id == 1


def _child_spawn(target_expr: str) -> CommandNode:
    return CommandCompiler({"bar.energy": "float"}).compile_command(
        CommandNode(type=CommandType.SPAWN_EFFECT, effect_id="child", target_expr=target_expr, intensity=1.0)
    )


def _add_child(manager: EffectManager) -> None:
    manager.catalog.effects["child"] = CompiledEffect(
        id="child",
        scope="item",
        duration=5,
        reapply_policy="stack",
        observable=True,
        on_spawn=[_write("self.vfs.charge", "4.0")],
        on_tick=[],
        on_despawn=[],
        on_interrupt=[],
    )


@pytest.mark.parametrize("policy", ["stack", "merge", "replace"])
def test_descendant_denial_restores_parent_reapplication_and_aliases(policy: str) -> None:
    manager, registry, bars = _setup(policy)
    _add_child(manager)
    existing = manager.spawn_effect("charging", 1, 1.0, 0, bars=bars, vfs_registry=registry)
    manager.scheduler.schedule([_write("bar.energy", "5.0")], 4, scope="item", entity_id=1)
    pending_list = manager.scheduler.pending[4]
    scope_list = manager.item_effects[1]
    energy = bars["energy"]
    before_effect = asdict(existing)
    before_rng = torch.get_rng_state().clone()
    pipeline = [
        _write("bar.energy", "9.0"),
        CommandCompiler({"bar.energy": "float"}).compile_command(
            CommandNode(type=CommandType.DELAY, delay_ticks_expr="2", delay_commands=[_write("bar.energy", "7.0")])
        ),
        _child_spawn("where(uniform(0.0, 1.0) > -1.0, 1, 0)"),
    ]
    effect = manager.catalog.effects["charging"]
    if policy == "merge":
        effect.on_interrupt = pipeline
    else:
        effect.on_spawn = pipeline
    with pytest.raises(PermissionError, match="sealed"):
        manager.spawn_effect("charging", 1, 0.5, 2, bars=bars, vfs_registry=registry)
    assert bars["energy"] is energy
    assert torch.equal(energy, torch.full((2,), 3.0))
    assert manager.item_effects == {1: [existing]}
    assert manager.item_effects[1] is scope_list
    assert manager.scheduler.pending == {4: pending_list}
    assert manager.scheduler.pending[4] is pending_list
    assert asdict(existing) == before_effect
    assert manager.next_instance_id == 1
    assert torch.equal(torch.get_rng_state(), before_rng)


def test_denied_top_level_dynamic_target_preserves_rng() -> None:
    manager, registry, bars = _setup("stack")
    _add_child(manager)
    before_rng = torch.get_rng_state().clone()
    with pytest.raises(PermissionError, match="sealed"):
        CommandExecutor().execute(
            _child_spawn("where(uniform(0.0, 1.0) > -1.0, 1, 0)"),
            ExecutionContext(bars=bars, vfs_registry=registry, effect_manager=manager),
        )
    assert torch.equal(torch.get_rng_state(), before_rng)
    assert manager.get_all_active_effects() == []


def test_successful_cascade_uses_prior_writes_and_samples_target_once() -> None:
    manager, registry, bars = _setup("stack")
    _add_child(manager)
    manager.catalog.effects["charging"].on_spawn = [
        _write("bar.energy", "9.0"),
        _child_spawn("where(bar.energy[0] > 8.0 and uniform(0.0, 1.0) > -1.0, 0, 1)"),
    ]
    torch.manual_seed(16)
    torch.rand(())
    expected_rng = torch.get_rng_state().clone()
    torch.manual_seed(16)
    manager.spawn_effect("charging", 0, 1.0, 0, bars=bars, vfs_registry=registry)
    assert registry.read_item("writable", "charge", 0, reader="engine") == 4.0
    assert [effect.effect_id for effect in manager.get_all_active_effects()] == ["charging", "child"]
    assert torch.equal(torch.get_rng_state(), expected_rng)


@pytest.mark.parametrize("entry", ["context", "environment"])
def test_successful_cascade_with_disabled_item_service(entry: str) -> None:
    from townlet.environment.null_managers import NullItemManager

    manager, registry, bars = _setup("stack")
    _add_child(manager)
    manager.catalog.effects["charging"].on_spawn = [_child_spawn("0")]
    if entry == "context":
        command = CommandCompiler({}).compile_command(
            CommandNode(type=CommandType.SPAWN_EFFECT, effect_id="charging", target=0, intensity=1.0)
        )
        CommandExecutor().execute(command, ExecutionContext(bars=bars, vfs_registry=registry, effect_manager=manager))
    else:
        manager.spawn_effect("charging", 0, 1.0, 0, bars=bars, vfs_registry=registry, item_manager=NullItemManager())
    assert registry.read_item("writable", "charge", 0, reader="engine") == 4.0


def test_compiled_switch_cascade_denial_preserves_parent_state() -> None:
    manager, registry, bars = _setup("stack")
    _add_child(manager)
    switch = CommandCompiler({"bar.energy": "float"}).compile_command(
        CommandNode(type=CommandType.SWITCH, switch_expr="1", cases=[("1", [_child_spawn("1")])])
    )
    # Execution consumes compiled branches; source diagnostics are not authority.
    switch.cases = []
    manager.catalog.effects["charging"].on_spawn = [_write("bar.energy", "9.0"), switch]
    with pytest.raises(PermissionError, match="sealed"):
        manager.spawn_effect("charging", 1, 1.0, 0, bars=bars, vfs_registry=registry)
    assert torch.equal(bars["energy"], torch.full((2,), 3.0))
    assert manager.get_all_active_effects() == []
    assert manager.next_instance_id == 0
