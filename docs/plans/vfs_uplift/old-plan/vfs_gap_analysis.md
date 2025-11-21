# VFS / Effects / Expression Gaps Plan (Runtime NotImplemented Cleanup)

## Scope
Close remaining runtime `NotImplementedError` stubs across Expressions, VFS registry, and Effects `for_each` collections. Substrate gaps are noted but blocked pending design decisions.

## Plan

1) Expression functions & type checker
- Extend `Evaluator.visit_function_call` with domain functions used by configs (distance, dot, sqrt/exp/log, clamp01 or similar).
- Implement function signature validation and index-access type checking in `TypeChecker`.
- Tests: update `tests/test_townlet/unit/world/expression/test_evaluator.py` and `test_type_checker.py` for new functions and index rules.

2) VFS registry completeness
- Implement `VariableRegistry.read`/`write` for global/agent/agent_private scopes with proper access control and device handling (currently only ITEM scope is implemented).
- Tests: expand `tests/test_townlet/unit/vfs/test_registry.py` to cover read/write and permission failures across scopes.

3) Effects `for_each` collections
- Implement `inventory_items` resolution (define shape: instance_ids or (agent_idx, slot_idx, instance_id); wire required inventory reference into ExecutionContext).
- Implement `active_effects` resolution (define shape: effect identifiers/scope indices; expose needed state from EffectManager).
- Tests: add coverage for `effects/collections.py` and executor-level tests exercising `for_each` with both new collections.

4) Executor clarity
- Keep strict NotImplemented for unknown command types but improve messaging; validate new `for_each` collection support.
- Tests: ensure unsupported command types fail fast; supported types pass.

5) Substrate gaps (not implemented; decision needed before work)
- Continuous/continuousND: POMDP support, neighbor queries, and `get_all_positions` remain unimplemented. Decision needed: design discretization/neighbor semantics vs. keep “not supported.”
- GridND N≥4 POMDP: currently guarded. Decide whether to sustain the guardrail or design a scalable local-window strategy.
- Action for now: document limitations in guides/schemas; no code changes until a design decision is made.
