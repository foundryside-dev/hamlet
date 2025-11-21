# Refactor Plan: ExecutionContext, for_each collections registry, item_id → item_type

Goal: Reduce call-site boilerplate, make collection resolution extensible, and fix item terminology. This is a breaking change under fail-forward semantics.

## Scope
1) ExecutionContext refactor to dataclass + copy/with_* helper; update call sites.
2) Collection resolver registry (open/closed) instead of if/elif in effects/collections.py.
3) Rename spawn_item command field item_id → item_type across schema/executor/tests/config references.

## Files to read/modify
- src/townlet/effects/context.py
- src/townlet/effects/executor.py
- src/townlet/effects/collections.py
- src/townlet/effects/schema.py (CommandNode)
- src/townlet/items/manager.py (spawn_item signature already item_type)
- Tests: tests/test_townlet/unit/effects/*, integration tests touching spawn_item/for_each (effect_cascades, aoe_effects, items_integration, spawn_item_end_to_end, expression_vfs_effects)
- Config fixtures (if any) referencing item_id for spawn_item commands

## Plan

### 1) ExecutionContext dataclass + copy helper
- Convert ExecutionContext to a @dataclass (frozen=False), with defaults where sensible:
  - bars: dict[str, torch.Tensor]
  - vfs_registry: VariableRegistry
  - self_index: int | None = None
  - target_index: int | None = None
  - effect: Any | None = None
  - self_is_item: bool = False
  - effect_manager: Any | None = None
  - item_manager: Any | None = None
  - spawn_depth: int = 0
  - agent_positions: torch.Tensor | None = None
  - interrupt_reason: str | None = None
  - current_tick: int = 0
  - target_is_item: bool = False
  - iterator_value: Any | None = None (optional if useful)
- In __post_init__, set null fallbacks for effect_manager/item_manager to the existing _NullEffectManager/_NullItemManager. Keep fail-fast behavior in spawn ops, but allow modify-only contexts.
- Add a copy/with_ method: def copy(self, **overrides) -> ExecutionContext: return replace(self, **overrides)
- Update call sites to use copy or minimal overrides:
  - manager.py spawn_effect/on_spawn/on_interrupt/on_tick/on_despawn contexts
  - executor for for_each child contexts
  - affordance_engine, item_action_handlers, tests constructing ExecutionContext
- Remove manual hasattr copying (agent_positions, inventory) where copy is used; include those fields in the dataclass so replace carries them automatically.
- Tests: ensure existing unit tests still construct valid contexts; adjust to pass bare minimum overrides as before, aided by defaults.

### 2) Collection resolver registry
- In effects/collections.py:
  - Define a CollectionResolver protocol/type alias.
  - Implement resolver functions for existing collections: all_agents, nearby_agents, inventory_items, active_effects (reuse logic). Each should accept (context, **kwargs) and return list[int].
  - Add a registry dict COLLECTION_RESOLVERS = {...} prepopulated.
  - Add register_collection_resolver(name, resolver) to allow extensions.
  - Update resolve_collection to dispatch via registry and enforce max_count/cap: resolver = COLLECTION_RESOLVERS.get(name) else ValueError; after resolve, if len > max_count raise.
  - Thread through **kwargs (e.g., radius) from executor when calling resolve_collection.
- Executor: adjust import/usage to pass radius via kwargs; no logic change otherwise.
- Tests: update for_each unit tests to still pass; add a small test that an unknown resolver raises, and that registry can be extended (optional if time). Keep inventory_items behavior (skip -1, return ints, map to item.vfs_index in executor).

### 3) Rename item_id → item_type for spawn_item commands
- schema.py CommandNode: rename field to item_type; keep optional backward alias if needed? (fail-forward means we can drop alias, but we must update all references).
- executor: use command.item_type when calling item_manager.spawn_item; remove “item_id” comment.
- Any parser/DTO that populates CommandNode for spawn_item should map to item_type.
- Tests: update all spawn_item CommandNode constructions to item_type=...; update YAML/fixtures if present.
- Config docs (if any in tests) may need updates; check test fixtures for item_id usage.

## Testing matrix
- Unit: effects/test_spawn_effect.py, test_spawn_item_position_resolution.py, test_for_each.py, test_execution_context.py, test_command_executor.py, test_lifecycle_interrupt.py.
- Integration: test_effect_cascades.py, test_aoe_effects.py, test_items_integration.py, test_spawn_item_end_to_end.py, test_expression_vfs_effects.py (and any spawn_item users).
- Ruff/Black to satisfy style.

## Risks/Mitigations
- Dataclass conversion may break callers relying on positional args; ensure all uses are keyword-based (search for ExecutionContext( without keywords; fix).
- Registry pattern: ensure existing behavior unchanged; keep defaults for radius handling.
- item_id rename: ensure no lingering references in tests/configs; fail-forward allows breaking configs, but clean up in repo fixtures.

## Steps to execute
1) Convert ExecutionContext to dataclass with copy; update all call sites; run targeted unit tests (context, command_executor, spawn_effect, for_each).
2) Implement collection registry and adjust executor call; run for_each unit + integration AoE.
3) Rename item_id → item_type across code/tests; run spawn_item unit + items integration.
4) Run broader integration subset (effect_cascades, items_integration, spawn_item_end_to_end, expression_vfs_effects) and Ruff check.
