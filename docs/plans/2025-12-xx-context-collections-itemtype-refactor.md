# Refactor Plan: ExecutionContext, for_each collections registry, item_id → item_type

Goal: Reduce call-site boilerplate, make collection resolution extensible, and fix item terminology. This is a breaking change under fail-forward semantics.

## Scope
1) ExecutionContext refactor to dataclass + copy/with_* helper; update call sites. ✅
2) Collection resolver registry (open/closed) instead of if/elif in effects/collections.py. ✅
3) Rename spawn_item command field item_id → item_type across schema/executor/tests/config references. ✅

## Files to read/modify
- src/townlet/effects/context.py
- src/townlet/effects/executor.py
- src/townlet/effects/collections.py
- src/townlet/effects/schema.py (CommandNode)
- src/townlet/items/manager.py (spawn_item signature already item_type)
- Tests: tests/test_townlet/unit/effects/*, integration tests touching spawn_item/for_each (effect_cascades, aoe_effects, items_integration, spawn_item_end_to_end, expression_vfs_effects)
- Config fixtures (if any) referencing item_id for spawn_item commands

## Plan

### 1) ExecutionContext dataclass + copy helper ✅
- Converted `ExecutionContext` to a dataclass with defaults and `copy(**overrides)`; Null managers wired in `__post_init__`.
- Added fields for iterator_value/inventory so child contexts retain them without manual hasattr copies.
- Executor now uses `copy` for for_each child contexts; existing call sites remain keyworded.

### 2) Collection resolver registry ✅
- Added resolver functions and registry with `register_collection_resolver`; `resolve_collection` dispatches through the registry and enforces caps.
- Executor now passes kwargs (radius) through; for_each tests unchanged and passing.

### 3) Rename item_id → item_type for spawn_item commands ✅
- Dropped the item_id alias; executor/schema/tests all use `item_type`.
- Updated spawn_item unit/integration tests; parser already mapped to item_type.

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
