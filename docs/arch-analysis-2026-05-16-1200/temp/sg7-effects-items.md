# SG7 — Effects & Items

## Part A: Effects

**Location:** `src/townlet/effects/` (2,878 LOC, 10 files)
**Confidence:** High — read `__init__.py`, `catalog.py`, `schema.py`, `parser.py`, `collections.py`, `manager.py`, `executor.py`, `context.py`, `scheduler.py`, and `compiler.py` in full; cross-checked imports of `townlet.effects.*` from both `universe/` and `environment/vectorized_env.py`.

### Responsibility

Effects are HAMLET's general-purpose "state-mutation pipeline": a tiny declarative
command language compiled out of YAML, attached to entities (agents, items,
affordances, globals) with a lifecycle (spawn / tick / despawn / interrupt), and
executed against GPU tensors via pre-compiled expression ASTs.

Effects are the lower-level mechanism behind affordance side-effects, item
interactions (`on_pickup` / `on_use` / `on_drop` / custom verbs), and time-based
status modifiers. The catalog of effect *definitions* is produced by the
Universe compiler (SG2/SG3); runtime instances and scheduling live entirely in
`effects/manager.py` + `effects/scheduler.py` and are owned by
`VectorizedHamletEnv` (`environment/vectorized_env.py:335-345`).

### Effect model

A compiled effect (`catalog.py:15-30`, `CompiledEffect`) is just a record with:

- `id` (catalog key), `scope` (string form of `EffectScope`: `global` / `agent`
  / `item` / `affordance`), `duration` (ticks), `intensity` (float), and
  `reapply_policy` (`renew` / `merge` / `replace` / `stack`).
- `observable` flag — controls whether the effect surfaces in agent
  observations.
- Four pipelines of compiled `CommandNode`s: `on_spawn`, `on_tick`,
  `on_despawn`, `on_interrupt`.

The catalog (`catalog.py:33-103`) is a dict keyed by `effect_id`, plus a
deterministic `effect_name_to_id` integer table built in `__post_init__` so
effects can be encoded into observation tensors with stable indices
(`get_effect_index`, `catalog.py:129-133`). Construction is via
`EffectCatalog.from_config`, which:

1. Parses each `EffectDefinition.on_*` list with `CommandParser`
   (`parser.py:14`).
2. If a type schema is supplied, runs `CommandCompiler.compile_commands`
   (`compiler.py:14`) — this is the type checker and AST baker (see below).

Runtime instances are `ActiveEffect` dataclasses (`manager.py:36-56`),
tracking `effect_id`, a per-`EffectManager` `instance_id`, the
`target_entity_id`, scope, current `intensity`, `duration_total` /
`duration_remaining` / `elapsed_ticks`, `spawn_step`, `observable`, and the
catalog `effect_index` for observation encoding.

### Command (Effect-kernel) model

`CommandType` (`schema.py:19-31`) enumerates 10 kinds: `MODIFY`, `SPAWN_EFFECT`,
`SPAWN_ITEM`, `SAMPLE`, `IF`, `FOR_EACH`, `SWITCH`, `REDUCE`, `PARALLEL`,
`DELAY`. A `CommandNode` (`schema.py:34-121`) is a wide dataclass holding every
possible field for every command type, plus pre-compiled AST handles
(`value_ast`, `condition_ast`, `target_ast`, `collection_ast`, `case_asts`,
`reduce_*_ast`, `delay_ticks_ast`, `sample_param_asts`). The "wide struct +
type tag" shape avoids a virtual dispatch hierarchy at the cost of
many `None`-valued fields per node.

Compile-time validation (`compiler.py`) does, per type:

- **MODIFY** — requires `path` in schema and that the parsed `value_expr`
  type-checks to the path's declared type (`compiler.py:41-66`).
- **SPAWN_EFFECT** — requires `effect_id`, a target literal or expression
  evaluating to `int`, and an explicit `intensity` (`:68-87`).
- **SAMPLE** — validates distribution (uniform/normal/lognormal/exponential/
  bernoulli/categorical), required params, target path/type compatibility,
  parses each param expression to an AST (`:89-158`).
- **IF** — condition must be `bool` (`:160-185`).
- **FOR_EACH** — uses either a registered collection name (`COLLECTION_RESOLVERS`
  in `effects/collections.py`) or an arbitrary collection expression; rejects
  nested `for_each` outright (`:187-245`). The `nested` check walks every
  child-block kind to enforce this.
- **SWITCH** — first-match equality, type-aligned cases (`:247-271`).
- **REDUCE** — fixed-size collections only (`list`/`tensor`); accumulator and
  iterator symbols are temporarily injected into the type-checker schema for
  body checking (`:273-321`). This is the only place in the compiler that
  mutates `type_checker.schema` mid-pass.
- **PARALLEL** — at least one branch; *disjoint-writes* enforced statically
  across `MODIFY.path` and `REDUCE.reduce_target` (`:323-360`). At runtime
  PARALLEL still executes branches sequentially (`executor.py:589-592`); the
  "parallel" label is purely a write-disjointness assertion, not a concurrency
  primitive.
- **DELAY** — gated on `time_enabled` (so non-temporal levels reject any
  `delay`), `ticks` expression must be `int`, body must be non-empty
  (`:362-382`).
- **SPAWN_ITEM** — requires `item_type`; if `position` is not
  `random` / `self` / `target`, parses the position expression (`:384-396`).

### Execution model

`CommandExecutor` (`executor.py:104-737`) walks `CommandNode`s and dispatches
on `command.type`. Important properties:

- **Never reparses expressions at runtime** — the executor evaluates the
  pre-compiled ASTs that the compiler stored on each node
  (`executor.py:107-113`, comment at top of file). Anywhere the AST is
  missing, the executor raises rather than re-parsing.
- **`_TargetAwareExecutionContext`** (`executor.py:21-101`) extends the
  generic expression context with `self.` / `target.` prefix handling and
  routes `self.vfs.*` through the VFS registry when `self_is_item=True`,
  using `vfs_registry.get_item_profile_for_index` and
  `read_item` — i.e. item-scoped VFS lives in a separate profile-indexed
  tensor, not the agent VFS storage. This is the seam between effects and the
  VFS system (SG5).
- **Cascade depth** is capped at `MAX_CASCADE_DEPTH = 10`
  (`executor.py:16, 190-191`). Each `spawn_effect` increments `spawn_depth`
  via `manager.spawn_effect(... spawn_depth=context.spawn_depth+1)`
  (`manager.py:230`) so a chain of effects spawning effects from their
  `on_spawn` will fail-fast at depth 10.
- **`FOR_EACH`** caps collection size at `MAX_COLLECTION_SIZE = 256`
  (`collections.py:10`) and re-runs the cap check at runtime; for the
  registered `inventory_items` collection it dereferences the slot
  `instance_id` to its `vfs_index` so the body sees the item's VFS slot, not
  its instance id (`executor.py:464-482`).
- **`SAMPLE`** seeds a per-context `torch.Generator` lazily, mixing
  `context.seed` (if any) with `context.current_tick`
  (`executor.py:316-323`). Six distributions are wired
  (`uniform`/`normal`/`lognormal`/`exponential`/`bernoulli`/`categorical`).
  `bernoulli` cast and `categorical` reshape both align dtype with the
  target tensor.
- **`DELAY`** does not execute the body — it pushes the commands onto
  `Scheduler` (`executor.py:594-640`) with the entity's scope/`self_index`
  recorded as the cancel key, plus a `context_overrides` blob that
  re-materialises self/target/spawn_depth/effect on dispatch.

`Scheduler` (`scheduler.py`) is a tick-keyed `dict[int, list[ScheduledItem]]`
with caps (`MAX_DELAY_TICKS = 1000`, `MAX_SCHEDULED_ITEMS = 10000`), atomic
`schedule` / `advance` / `drain_due` / `cancel` / `reset` /
`state_dict` / `load_state_dict`. `time_enabled=False` makes `schedule` raise,
which combined with `compiler.py:365-366` enforces "no delays on non-temporal
levels" both at compile and at runtime.

### Runtime: `EffectManager`

`manager.py` is the canonical place where effect lifecycle meets the
environment.

- **Storage** is scope-bucketed: `global_effects: list`, `agent_effects: dict[int, list]`,
  `item_effects: dict[int, list]`, `affordance_effects: dict[str, list]`
  (`manager.py:88-92`).
- **`spawn_effect`** (`manager.py:94-240`) — looks up the compiled definition,
  resolves reapply policy against any existing effect on the same target:
  - `renew` → reset `duration_remaining` and return existing.
  - `merge` → add `intensity`; if there is an `on_interrupt` pipeline, run it
    once with `interrupt_reason="merged_by_effect"`.
  - `replace` → cancel scheduled work tied to the old instance via
    `_cancel_scheduled_for_effect`, run `on_interrupt`
    (`interrupt_reason="replaced_by_effect"`), remove the old, fall through to
    create a new one.
  - default (stack) → create a new instance alongside the existing one.
  New instances get a monotonic `instance_id`, are added to the right scope
  bucket, and their `on_spawn` pipeline runs with `spawn_depth+1`.
- **`tick`** (`manager.py:345-404`) — per environment step: (1) advance scheduler
  and drain due items; (2) tick global and agent effects in reverse order,
  decrementing `duration_remaining`, executing `on_tick`, and despawning at
  zero; (3) drain zero-delay items that the just-run `on_tick`/`on_despawn`
  bodies may have enqueued. Item and affordance buckets are *not* iterated
  in `tick` — item-scoped effect ticking lives elsewhere (or hasn't been
  wired through this codepath yet).
- **`cancel_effect`** (`manager.py:601-697`) — locates an instance across all
  four scope buckets by `instance_id`, runs `on_interrupt` with
  `"manually_cancelled"`, then removes. Notably it does NOT run `on_despawn`
  for manual cancellation.
- **`NullItemManager`** (`manager.py:23-33`) is a no-op stand-in injected when
  the level has no items, so `spawn_item` commands raise loudly rather than
  silently dropping.

### Collection resolvers

`collections.py` registers four named iterables for `FOR_EACH`
(`COLLECTION_RESOLVERS`, `:57-62`):

- `all_agents` — `range(batch_size)`.
- `nearby_agents` — requires `radius`, `self_index`, and `agent_positions` on
  the context; uses `torch.norm` for euclidean distance and excludes self.
- `inventory_items` — yields instance ids from the agent's inventory slots
  (`>= 0`).
- `active_effects` — yields `target_entity_id` of each agent-scoped active
  effect.

`register_collection_resolver` allows extensions but there are no other
callers in-tree.

### Dependencies

- **Inbound:**
  - `src/townlet/universe/compiler.py:15` and `universe/pipeline.py:8` —
    universe pipeline builds the `EffectCatalog` (compile stage) and threads
    it through `CompiledLevel` (`compiled.py:25`).
  - `src/townlet/universe/compilers/effects.py:8` — the universe sub-compiler
    that ultimately calls `EffectCatalog.from_config`.
  - `src/townlet/universe/compilers/observation.py:14` — observation builder
    uses `EffectCatalog.get_effect_index` for effect-slot encoding.
  - `src/townlet/environment/vectorized_env.py:335-491` — env instantiates
    `CommandExecutor`, `EffectManager`, and threads them into
    `ItemManager`/`ItemActionHandler`.
  - `src/townlet/items/manager.py:22-23` and `items/action_handlers.py:14-15`
    — ItemManager re-uses `CommandCompiler` to compile item-interaction
    pipelines, and `ItemActionHandler` builds `ExecutionContext`s and runs
    `CommandExecutor`.

- **Outbound:**
  - `townlet.config.effects_config` — `EffectsConfig`, `CommandConfig`,
    `EffectScope`, `EffectDefinition` DTOs.
  - `townlet.world.expression` — `ExpressionParser`, `Evaluator`,
    `TypeChecker`, and the lower `ExecutionContext` used by `Evaluator`
    (so the effect system is parameterised by an external expression
    language).
  - `townlet.vfs.registry.VariableRegistry` — for path resolution
    (`vfs.*`, `target.vfs.*`, `self.vfs.*`), item-profile lookups, and
    reference-type traversal (`agent_ref` / `item_ref` in
    `context.py:283-340`).
  - `torch` (tensors, generators, distances).

### Patterns observed

- **AST baking at compile time** is consistent across every command kind:
  every expression string is parsed once into a `*_ast` attribute on the
  `CommandNode`, and the executor assumes the AST is present. This is a clean
  separation that pays off in inner loops.
- **Wide-record AST node** with a `CommandType` discriminator instead of a
  subclass hierarchy. Trade-off: simple `dataclass(eq=True)` for hashing/
  copying but many `None`-valued fields per instance.
- **Scope-bucketed storage** (`global_effects` list + three dicts) keeps
  membership lookups O(scope_size) and avoids a flat scan, but
  `get_all_active_effects` exists for tests and is the only flat view.
- **Fail-forward null managers** (`NullItemManager`, `_NullEffectManager` in
  `context.py:15-22`) are constructed in `__post_init__` so any
  `ExecutionContext` always has *some* manager; using them raises with a
  clear message rather than `AttributeError`.
- **Disjoint-writes** for `PARALLEL` is a static check, not a runtime one
  — branches still run sequentially.
- **Cascade depth** is a constant in the executor module
  (`MAX_CASCADE_DEPTH = 10`), not configurable per level.
- **Item-VFS routing via `self_is_item`** — the same `self.vfs.*` syntax
  resolves differently depending on a boolean on the context, switching from
  agent-VFS index into the per-profile item table. This is the single largest
  coupling point between effects and items.

### Concerns

- **`ExecutionContext.__post_init__` (`context.py:49-57`) silently replaces
  `None` managers with raising stubs.** That's fine for safety but it means
  `context.item_manager is None` is never true downstream, and callers that
  *do* check for `None` (e.g. `executor.py:252`) can be tricked because the
  field is now `_NullItemManager`. Some callers handle this via duck-typed
  `spawn_item` raising; others use truthy checks. Mixed convention.
- **`item_effects` and `affordance_effects` buckets are written to by
  `_add_to_scope` (`manager.py:250-260`) but never iterated by `tick`.** Their
  lifecycle therefore depends entirely on manual `cancel_effect` /
  `despawn` paths. If any compiled effect uses `EffectScope.ITEM` or
  `EffectScope.AFFORDANCE`, its `on_tick` pipeline will not execute and its
  duration will never tick down. This is either: (a) an unimplemented case,
  (b) a deliberate "those scopes are not yet used", or (c) a latent bug.
  `_despawn_effect` itself only handles `EffectScope.AGENT` removal
  (`manager.py:550-551`), which corroborates "not yet wired".
- **Inline `from ... import` inside hot paths** — `manager.py` has 8
  in-function imports of `ExecutionContext`. Cheap thanks to module caching,
  but unusual and suggests the import graph wasn't cleanly separable when
  this was written. Can be hoisted under `TYPE_CHECKING` + explicit
  top-of-file imports for clarity.
- **`get_all_active_effects` is documented "for testing"** but is the only
  flat view of state; any future debug/inspection tooling will likely re-use
  it and inherit its O(total_effects) cost. Fine; just worth noting.
- **`reapply_policy` is a string field on `CompiledEffect`**
  (`catalog.py:23`) but on the DTO it's an enum (`effects_config.ReapplyPolicy`).
  The catalog flattens it back to its `.value`. Stringly-typed enum at the
  runtime boundary is mildly fragile (a typo in a new policy goes
  unrecognised, falls through the if-chain, and the effect silently stacks).
- **`PARALLEL` is not actually parallel.** The name is load-bearing in the
  YAML/spec but the executor runs branches sequentially
  (`executor.py:589-592`). The disjoint-writes check is good, but the
  word "parallel" implies properties the runtime does not provide.
- **Scheduler state is dict-of-list keyed by tick**; `cancel` does a linear
  scan over every bucket (`scheduler.py:75-82`). For the 10k-item cap that's
  fine, but agent-resets at episode boundary loop over agents
  (`vectorized_env.py:783-786`) and each call is a full scan.

---

## Part B: Items

**Location:** `src/townlet/items/` (1,602 LOC, 5 files)
**Confidence:** High — read `__init__.py`, `instance.py`, `inventory.py`,
`action_handlers.py` in full, and `manager.py` lines 1-1000 in full (the
remainder covers respawn scheduling variants already established by
lines 562-990).

### Responsibility

Items are world objects — apples, weapons, etc. — that have a position
(when on the grid), a per-profile VFS state (e.g. `durability`,
`freshness`), and three lifecycle interactions (`on_pickup`, `on_use`,
`on_drop`) plus configurable custom verbs. Agents have fixed-size
inventories (`InventoryState`) backed by a `[batch, max_items_per_agent]`
int tensor. The item subsystem owns spawn/despawn lifecycle, periodic and
scripted respawning, and dispatch for item-related actions in the
environment.

Crucially, *items have no behaviour of their own beyond the effect commands
they declare* — all state-mutation goes through the effect executor, with
the item itself as `self` and the acting agent as `target`. The items
package is therefore the lifecycle owner + dispatch layer; the actual
"interaction" semantics live in YAML and the effect runtime.

### Item model

`ItemInstance` (`instance.py:10-49`) is the minimum runtime record:

- Identity / appearance: `name`, `icon`, `tags`, `item_type` (catalog key),
  `instance_id` (monotonic counter).
- Spatial: `position` — `tuple[int|float, ...]`, supports both grid and
  continuous coords.
- VFS routing: `vfs_index` (slot in `[max_items, num_profile_vars]` tensor),
  `vfs_profile` (e.g. `"food_stats"`).
- Lifecycle: `spawn_tick`, `duration_total`, `duration_remaining` (None =
  permanent), `tick()` decrements, `is_expired()` triggers despawn.
- Sharing: `exclusive: bool` (default True) — exclusive items leave the
  world when picked up; shared items remain in place and have a *set* of
  holder agents (`holder_agent_ids`).
- `holder_agent_id` (property, `:43-48`) returns an arbitrary holder for
  single-holder API compatibility — a hint that the multi-holder model is
  newer than the single-holder one.

The compiled item type (`manager.py:31-53`, `CompiledItemType`) holds the
type-level metadata (`id`, `vfs_profile`, `duration`, `cooldown`, `name`,
`icon`, `tags`, `exclusive`) plus the pre-compiled effect-command pipelines
for `on_pickup`/`on_use`/`on_drop` and two dicts of custom verbs:
`compiled_local_commands` (agent must stand on the item) and
`compiled_inventory_commands` (agent must hold the item).

### Inventory representation

`InventoryState` (`inventory.py`) is tensor-backed:

- `slots: torch.Tensor[batch, max_items_per_agent]` of `int64`, `-1` =
  empty (`:41-46`).
- `items: dict[int, ItemInstance]` for per-instance metadata.
- `add_item` finds the first empty slot, enforces "no duplicates per agent"
  and "exclusive items can only be held by one agent", returns `False` on a
  full inventory (`DENY_PICKUP` policy, `:51-86`).
- `remove_item` clears the slot but *keeps* the metadata in `self.items` so
  DROP can re-place the same `ItemInstance` (`:88-113`, with the explicit
  "Actually DON'T remove" comment at `:107`).
- `purge_instance` (`:148-162`) is the cleanup hook called by
  `ItemManager.despawn_item` — clears the instance id from every agent's
  slots and from `self.items`. Comment explicitly calls this an "I2 memory
  leak fix."

### Action surface (`ItemActionHandler`)

`action_handlers.py:27` is the dispatch layer between the environment's
discrete action space and item lifecycle:

- `handle_get_action` (`:142-190`) — pickup: scan `active_items` for a
  positional match, `add_item` to inventory, lift from world if
  exclusive, run `on_pickup` effects with the agent as `target` and the
  item as `self` (`self_is_item=True`, `:108-119`).
- `handle_use_slot_action` (`:192-233`) — read slot, run `on_use` effects;
  does NOT remove the item from inventory (consumption is the effect's
  responsibility — e.g. a `modify` on `self.vfs.durability` and then a
  conditional `despawn`).
- `handle_drop_slot_action` (`:346-384`) — exclusive items return to the
  grid via `ItemManager.place_item` (reusing the existing instance), shared
  items just clear the slot.
- `handle_custom_action` (`:298-344`) — dispatches custom local/inventory
  verbs by action name, looks up the compiled command list, runs through
  `CommandExecutor`.
- `compute_custom_action_masks` (`:265-296`) — builds an action mask: a
  custom verb is available only if the agent currently holds (inventory
  scope) or stands on (local scope) at least one matching item.
- `_positions_match` (`:125-140`) — float-tolerant comparison so continuous
  substrates work without forced int rounding.

The interaction-execution path constructs an `ExecutionContext` with
`target_index=agent_idx` and `self_index=item.vfs_index, self_is_item=True`,
which is what makes `self.vfs.durability` in YAML resolve into the item-VFS
storage (`executor.py:77-92`).

### `ItemManager`

`manager.py:56` is the long-lived owner of:

- The compiled item-type list (`compiled_item_types`) and a parallel
  `custom_action_specs` registration for the action space.
- `active_items: dict[int, ItemInstance]` — currently on the grid.
- `held_items: dict[int, ItemInstance]` — currently in some inventory.
- `vfs_free_slots: set[int]` — pool of `vfs_index` values.
- `cooldown_until`, `respawn_timers`, `rule_spawn_counts`,
  `next_scheduled_tick`, `script_indices` — bookkeeping for the four
  spawn schedules (`periodic`, `normal`, `poisson`, `time_window`).
- `_position_index: dict[tuple, set[int]]` — O(1) occupancy lookup.

Key operations:

- `spawn_item` (`:299-405`) — allocates a `vfs_index`, initialises item-VFS
  state from the profile's `initial_value`s, optionally applies
  `initial_state` overrides, registers the instance in
  `VariableRegistry.register_item_instance`, updates the position index.
- `lift_item` (`:407-438`) — pickup half of `place_item`; for exclusive
  items it moves the instance from `active_items` to `held_items` and
  removes it from the position index. The VFS slot is *not* freed — the
  item still exists and continues to tick.
- `place_item` (`:440-471`) — drop half; moves from `held_items` to
  `active_items` at the new position.
- `despawn_item` (`:473-560`) — pops from whichever side holds the item,
  calls `vfs_registry.unregister_item_instance`, calls
  `inventory.purge_instance` (the I2 fix), cancels scheduled effect
  commands tied to this item, frees the VFS slot, sets cooldowns and
  respawn timers per the appearance config.
- `tick` (`:562-590`) — despawn-expired-first, then tick the rest in both
  `active_items` and `held_items` so held items still age.
- `find_spawn_location` (`:253-284`) — implements the four position
  strategies the effect-level `spawn_item` command uses
  (`self`/`target`/`random`/`explicit`).
- `spawn_initial_items` / `process_respawns` / `_should_spawn_rule` /
  `_iter_positions` / `_resolve_respawn_positions` / `_schedule_allows_spawn`
  (`:600-990`) — the rule engine for `ItemsAppearanceConfig`. Schedules
  support `periodic` (timer-based), `normal` (Gaussian inter-arrival),
  `poisson` (per-tick Bernoulli of `1-exp(-rate)`), and `time_window`
  (start/end gating). Placements support `random`, `fixed`,
  `grid` (spacing), and `scripted` (per-tick event list).
  `_should_spawn_rule` evaluates a compiled `rule.when_ast` expression
  against the current bars+VFS+temporal context — items can therefore
  be gated by world state, not just time.

### Dependencies

- **Inbound:**
  - `src/townlet/environment/vectorized_env.py:27` — env imports
    `InventoryState`, `ItemActionHandler`, `ItemManager` and wires them
    together at `:440-471`.
  - `src/townlet/effects/manager.py` — only indirectly: `ItemManager` is
    threaded *into* `EffectManager.spawn_effect` / `tick` /
    `cancel_effect` as a parameter, so effect→item is via parameter
    injection, not import. `effect_manager.cancel_scheduled_for_entity`
    is called by `ItemManager.despawn_item:506`.

- **Outbound:**
  - `townlet.config.items_config` — `ItemsCatalogConfig`,
    `ItemsAppearanceConfig`, `SpawnPlacementConfig`, `SpawnScheduleConfig`,
    `build_item_command_action_name`.
  - `townlet.effects.compiler.CommandCompiler` + `effects.parser.CommandParser`
    — item types compile their own interaction pipelines via the effect
    compiler (`manager.py:96-124`); items are clients of the effects
    sub-language.
  - `townlet.effects.context.ExecutionContext` +
    `townlet.effects.executor.CommandExecutor` — used by
    `ItemActionHandler` to execute compiled commands
    (`action_handlers.py:14-15, 108-123`).
  - `townlet.vfs.registry.VariableRegistry` —
    `register_item_instance` / `unregister_item_instance` /
    `item_profile_map` / `item_vfs` / `item_profiles` / `read_item` /
    `write_item`.
  - `townlet.world.expression.context.ExecutionContext` and
    `Evaluator` — directly used inside `_should_spawn_rule`
    (`manager.py:626-642`) so spawn predicates can reference world state.
  - `torch`, `math`, `logging`, `os` (debug log gating).

### Patterns observed

- **Tensor-backed inventory with dict-sidecar metadata.** `slots` is a
  pure GPU tensor for fast batch reads (masking, counts); `items` is a
  Python dict for the messy per-instance attributes. The pattern is
  consistent with the rest of Townlet's "tensor for vectorisable state,
  dict for sparse metadata."
- **Items are pure data + YAML behaviour.** No Python class per item type;
  everything is `CompiledItemType` parameterised by compiled command
  lists. New item types are pure config.
- **`self_is_item` is the routing seam.** It's a single boolean on
  `ExecutionContext` that flips `self.vfs.*` resolution from agent-batched
  tensor indexing to per-profile item-table lookup. This is elegant but
  the seam is fragile: any caller that forgets to set the flag will
  silently read from the wrong tensor.
- **DENY_PICKUP** policy for full inventories rather than auto-drop.
- **Static action specs registered at construction time** — the env reads
  `get_custom_action_specs()` once when wiring the action space; no
  dynamic re-registration is supported.
- **Per-rule keys** (`_rule_key`) are smuggled onto rule objects via
  `setattr` (`manager.py:892`) so `rule_spawn_counts` can survive config
  identity. Mildly unusual; cleaner alternatives exist (rule index in the
  config, named rules).
- **Continuous-position support** via float-tolerant matching even though
  most of the spawn machinery rounds to ints (`find_spawn_location:264`).
  Mixed grid/continuous design.

### Concerns

- **`get_item` (`inventory.py:115-129`) raises on invalid slot, but
  `slots[agent_idx, slot_idx]` would already raise.** Defensive but
  redundant.
- **The "Actually DON'T remove" comment in `inventory.remove_item`
  (`:107-108`)** is exactly the kind of thing that should be a docstring
  invariant, not an inline TODO. The implicit contract — "popped items
  stay in `self.items` until `purge_instance` or until they're re-added
  via `place_item`+`add_item`" — needs to be stated.
- **`spawn_item` returns `None` for three failure modes** (capacity,
  cooldown, no VFS slot) without distinguishing them. Callers can't tell
  why a spawn failed except by introspection, which the appearance-rule
  loop relies on (`:864-871`). A small fail-forward result type or
  exception would be more diagnostic.
- **`despawn_item` quietly returns for unknown ids** (`:493-494`) — easy
  to miss double-frees. Logging via `HAMLET_DEBUG_ITEMS` env var helps,
  but the silent path is still permissive.
- **Two near-identical placement resolvers** —`_iter_positions` and
  `_resolve_respawn_positions` (`:645-789`) are 95% the same code. The
  duplication risks drift; one of them is already slightly different
  for the `random` branch (initial uses `grid_size` arg, respawn uses
  `self.grid_size`).
- **`process_respawns` is long and branchy** (`:895-993`) — the
  scheduling-state machine for each schedule type is spread across both
  `_schedule_allows_spawn` and `process_respawns`, and the
  "retry vs. successful spawn" branches at the bottom duplicate the
  scheduling code in `despawn_item:519-549`. Extracting a `next_due_tick`
  helper would tighten this.
- **Hidden `setattr(rule, "_rule_key", ...)`** breaks the assumption that
  config DTOs are immutable. If `ItemsAppearanceConfig` becomes a
  Pydantic frozen model later, this will fail.
- **`compute_custom_action_masks`** is O(agents × inventory_slots) for
  inventory verbs and O(agents × active_items) for local verbs, evaluated
  every step. For 256 agents and 256 items that's 65k checks per masked
  verb — fine, but worth noting if items scale.
- **`Literal["local", "inventory"]` is repeated** in three places
  (`manager.py:90`, `:596`, `action_handlers.py:65` etc.). A `CustomVerbScope`
  alias would centralise it.

---

## Historical note (migration script)

`scripts/migrate_affordances_to_effects.py` (top-of-file docstring +
`migrate_affordance` body) documents a one-shot conversion from the legacy
affordance schema — where each affordance had a flat
`effects: {meter: delta}` dict (or, in a slightly newer revision, an
`effect_pipeline: {on_start, per_tick, on_completion, on_early_exit,
on_failure}` block) — into the current schema where affordances have an
`interactions:` block of effect commands. The conversion is mechanical:

```yaml
# old
effects: {energy: 0.1}
# new
interactions:
  on_start: [{modify: target.bar.energy, value: target.bar.energy + 0.1}]
```

This is the bridge from the pre-effects-runtime world to today's
"affordances are just compiled effect pipelines" architecture. Costs /
`costs_per_tick` were *not* migrated (deliberately — they remain
affordability gates, separate from the effect pipeline).

**Status assessment vs. CLAUDE.md's no-backwards-compat rule:** the script
is a one-shot CLI tool, not runtime code, and there is no surviving runtime
support for the old `effects:` / `effect_pipeline:` schema (the affordance
DTO no longer accepts those fields — to be confirmed by SG4, but no
runtime parser for them exists in `src/townlet/effects/` or
`config/effects_config.py`). Per the project's stance, this script is a
prime candidate for deletion now that every config pack has been migrated
— git history preserves it. If any unmigrated YAML still exists in
`configs/` (e.g. legacy fixtures), it should fail loudly rather than be
migrated on the fly.

Recommend: delete `scripts/migrate_affordances_to_effects.py` after
confirming no remaining `effects:` / `effect_pipeline:` blocks under
`configs/` and no calls into it from CI.

---

## Open questions

- **Item-scoped and affordance-scoped effects: are they intentionally
  un-ticked by `EffectManager.tick`?** The buckets are populated by
  `_add_to_scope` but `tick` only iterates `global_effects` and
  `agent_effects`. Either no compiled effect currently uses
  `EffectScope.ITEM` / `EffectScope.AFFORDANCE`, or there's a latent
  semantic gap. Worth checking the effect catalog in
  `configs/*/effects.yaml` (SG2 surface).
- **Where does `EffectScope.AFFORDANCE` actually get used?** The bucket
  is keyed by `str(target_entity_id)` (`manager.py:255-260`), which
  suggests the key is an affordance string id, but every other scope uses
  int ids. The mixing is suspicious — likely an early design that was
  never finished.
- **`reapply_policy="stack"` is implicit (the unhandled fall-through case
  at `manager.py:197`).** Is it documented anywhere as the default, or is
  it an accident of the if-elif chain?
- **`use_double_dqn`-style explicit "policy must be set" discipline does
  not appear in the items pack** — many fields on
  `CompiledItemType` (`duration`, `cooldown`) are `int | None` with
  meaning-by-absence. Is this in tension with CLAUDE.md's "no implicit
  defaults" principle, or are these genuinely optional?
- **Is `held_items` ever a substitute for `vfs_registry.item_vfs`?** Both
  carry per-item state across the pickup/drop boundary, but `held_items`
  is Python objects and `item_vfs` is a tensor. Confirm the invariant
  that `held_item.vfs_index` always references a valid live row.
- **Custom action specs are flattened into the global action space** —
  how does this interact with checkpoint transfer ("global vocabulary
  enables checkpoint transfer", per CLAUDE.md)? If a level adds a
  custom verb, do agents trained on the parent vocabulary still
  load? This is an SG6 (action space) / SG7 boundary question.
