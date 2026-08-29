# Effects Scheduler Plan (Delay Command Support)

Goal: Introduce a tick-aligned scheduler to support a `delay` command (and other time-based behaviors) under vectorized DRL constraints. Scheduler must be safe, capped, and deterministic.

## Requirements

- Tick-aligned execution: run due items exactly on tick boundaries within `EffectsManager.tick`.
- Vectorized-aware: avoid per-element Python loops; store per-scope/ID to enable batched handling where possible.
- Time-disable guard: reject scheduling when “time disabled” flag is set.
- Caps/safety: configurable max queued items and max delay (ticks); fail fast if exceeded; optional cascade/depth cap.
- Cancellation: cancel scheduled entries when effects despawn/interrupt or entities are removed.
- Persistence: optionally checkpoint scheduler state (current_tick, pending queue) for save/load.
- Deterministic ordering: FIFO per tick for reproducibility.
- Scope awareness: tie entries to scope (global/agent/item/affordance) to invalidate if the scope disappears.
- Integration hooks: enqueue from commands (delay), drain in `EffectsManager.tick`; accessible from other time-based systems.
- Metrics/introspection: counters for queued, executed, dropped.

## Design Outline

- Data structure: `Scheduler` holding `current_tick` and a dict/map `pending: dict[int, list[ScheduledItem]]` keyed by due_tick. `ScheduledItem` includes {commands, scope, entity_id, context overrides}.
- API:
  - `schedule(commands, delay_ticks, scope, entity_id, context_overrides)` → validates ticks >=0, caps, time-enabled flag.
  - `advance_to(tick)` or `drain_due(current_tick)` → return due items for execution; purge after execution.
  - `cancel(scope, entity_id)` → drop pending items tied to that scope/id.
- Caps:
  - `MAX_DELAY_TICKS` (e.g., 1_000) and `MAX_SCHEDULED_ITEMS` (e.g., 10_000) configurable; scheduling beyond caps raises.
- Integration in `EffectsManager.tick`:
  - At start/end of tick, call `scheduler.drain_due(current_tick)` and execute returned command lists with fresh `ExecutionContext` (propagate `current_tick`, bars, vfs_registry, effect_manager, etc.).
  - Pass scheduler/time-enabled flag into `ExecutionContext` or executor to let `delay` validate.
- Command plumbing:
  - `delay` command: compiler parses/tc ticks expr (int >=0), enforces caps; rejects when time disabled. Executor enqueues `do` block via scheduler.
- Scope invalidation:
  - Scheduled items carry scope/id; on despawn/interruption/entity removal, call `scheduler.cancel(scope, id)`.
- Persistence (optional phase 2):
  - Expose `state_dict()/load_state_dict()` for scheduler; include in checkpoints with `current_tick`.

## Validation Rules (delay)

- `ticks_expr` type-checks as int, >=0, <= MAX_DELAY_TICKS.
- Time-disabled flag: delay rejected at compile/execute when disabled.
- Queued item count may not exceed MAX_SCHEDULED_ITEMS.
- Scope/id required for agent/item/affordance contexts; global allowed with None id.

## Test Plan

- Unit tests for Scheduler:
  - Enqueue/dequeue at exact ticks; FIFO order within tick.
  - Cap enforcement on max_delay and max_items.
  - Cancel removes pending items for a given scope/id.
  - Time-disabled flag causes schedule rejection.
- Command-level tests for delay:
  - Compiler rejects non-int/negative ticks; enqueues valid ticks when time enabled.
  - Executor enqueues `do` block; `EffectsManager.tick` executes after N ticks.
  - Default zero delay executes on same tick.
  - Cancellation on despawn removes scheduled commands.
- Integration smoke:
  - One effect with `delay` modifies bar after N ticks; verify ticking applies it.
  - Caps hit raise errors.

## Open Questions

- Default values for MAX_DELAY_TICKS and MAX_SCHEDULED_ITEMS.
- Whether to execute delayed commands before or after on_tick in the same tick (ordering). Proposed: drain before on_tick to keep delays exact.
- Persistence priority: required now or deferred?
