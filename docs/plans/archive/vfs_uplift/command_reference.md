# Effects Command DSL – Draft Reference

Scope: Effects command language (YAML) used by the World/Effects compiler. Expression parsing remains in the expression parser; commands wrap expressions or collections and execute behavior. This draft captures existing `if`/`for_each` and speculative additions for roadmap alignment.

## Fully Implemented

### modify

**Syntax**
```yaml
- modify: <target_path>
  value: <expr>
```

**Notes**
- Target path must exist in schema; value expression is parsed and type-checked to match target type.
- Runtime: evaluator computes value AST; executor writes to target.

### spawn_effect

**Syntax**
```yaml
- spawn_effect: <effect_id>
  target: <"self" | "target" | int | expr>
  intensity: <float>
```

**Notes**
- Simple targets (`self`/`target`/int) bypass expression parsing; non-simple targets parsed/type-checked as int.
- Runtime: executor delegates to effect manager; cascading effects apply caps in manager (see code).

### spawn_item

**Syntax**
```yaml
- spawn_item: <item_type>
  position: <expr or literal>
  quantity: <int>
  initial_state: <mapping>
```

**Notes**
- Position is parsed when non-trivial; quantity/static fields validated in DTOs; executor hands off to item manager (when present).

### if

**Syntax**
```yaml
- if: <bool_expr>
  then: [<commands>]
  else: [<commands>]   # optional, defaults to []
```

**Semantics**
- Evaluate condition once; run only the matching branch. Nested `if` allowed. Side effects are strictly from the chosen branch.

**Validation**
- Condition must type-check as `bool`.
- Branch commands must type-check in the current context.

### for_each

**Syntax**
```yaml
- for_each: <collection_expression>   # expression parsed by ExpressionParser
  as: <iterator_variable>             # identifier bound per element
  do:                                 # required list of commands
    - <command using iterator>
    - ...
```

**Semantics**
- Evaluate `collection_expression` once to an iterable (list/tensor/resolver output).
- Iterate sequentially; no break/continue; order follows the collection. Empty collection → no-op.
- Bind `iterator_variable` within `do`; scope is limited to the block.
- Nested `for_each`: **disallowed**. Compiler will reject nested `for_each` until vectorized semantics are defined.

**Validation**
- Collection must type-check as iterable; element type inferred for iterator binding.
- Iterator name must be an identifier and not a reserved keyword.
- Add iterator symbol to type-checker scope for `do` expressions.
- Enforce iteration cap (256) to prevent runaway loops; fail fast when size known or at runtime otherwise.
- Resolver signatures (current impl):
  - `all_agents()` → iterable[int]
  - `nearby_agents(radius: float)` → iterable[int]
  - `inventory_items()` → iterable[int]
  - `active_effects()` → iterable[int]
- Body commands type-check with iterator in scope (e.g., `iterator.vfs.foo`).

**Runtime**
- Resolve collection; enforce cap; iterate; bind iterator in child context; execute body. Fail fast on unknown resolver.

**Examples**
- AoE heal: `for_each: "nearby_agents(radius=2)", as: agent, do: [modify agent.bar.health ...]`
- Inventory consume: iterate `held_items()`, conditional modify + spawn_effect.
- Static list multiply: `for_each: "[1,2,3,4,5]", as: i, do: modify target.vfs.multiplier`.

### switch / case

**Status:** ✅ PRODUCTION (equality-based matching only)

**Motivation**: Avoid deeply nested `if`; clearer multi-branch control.

**Syntax**
```yaml
- switch: <expr>
  cases:
    - when: <expr>      # compares to switch expr or boolean guard (to decide)
      do: [<commands>]
    - when: <expr>
      do: [<commands>]
  default: [<commands>] # optional, defaults to []
```

**Semantics**
- Evaluate `switch` once; evaluate cases in order using **equality matching**; first matching case runs; else default branch if provided.

**Validation**
- All `when` expressions type-check; must be comparable to `switch` type (equality mode only).
- Branch commands type-check; at least one case or default must be present.
- Type mismatches rejected at compile time.

**Runtime**
- Executor evaluates switch expression, compares against each case in order, runs first match.
- Supports scalar and tensor comparisons with broadcasting.

**Examples**
```yaml
- switch: "vfs.mode"
  cases:
    - when: "1"
      do:
        - modify: "bar.energy"
          value: "10"
    - when: "2"
      do:
        - spawn_effect: "boost"
  default:
    - modify: "bar.energy"
      value: "5"
```

### Item custom verbs (local & inventory)

**Status:** ✅ PRODUCTION

**Purpose**: Per-item actions beyond GET/USE/DROP, gated by proximity (local) or possession (inventory).

**Config surface** (`items.yaml` experiment catalog):
- `interactions.local_commands[]` and `interactions.inventory_commands[]` entries shaped as:
  ```yaml
  local_commands:
    - name: OPEN_CHEST
      description: "Open chest on the ground"
      effects:
        - modify: target.bar.energy
          value: target.bar.energy + 0.1
  inventory_commands:
    - name: DRINK_POTION
      description: "Drink while held"
      effects:
        - modify: target.bar.health
          value: target.bar.health + 0.2
  ```
- Item metadata is required: `name`, `icon`, `tags` (enforced in DTOs).

**Action naming**: Compiler emits stable action names:
- Local: `ITEM_LOCAL_<ITEM_ID>_<COMMAND_NAME>` (uppercase)
- Inventory: `ITEM_INVENTORY_<ITEM_ID>_<COMMAND_NAME>`

**Masking & dispatch**:
- Local verbs enabled only when the matching item type is co-located with the agent.
- Inventory verbs enabled only when the agent holds an instance of the matching item type.
- Commands execute through the Effects runtime (same validation/caps as other commands).

### while / repeat-until (guarded loops)

**Status:** ❌ NOT IMPLEMENTED (planned for future)

**Motivation**: Controlled loops with explicit caps; high risk without safeguards.

**Syntax (while)**
```yaml
- while: <bool_expr>
  do: [<commands>]
  max_iters: <int>   # required cap
```

**Semantics**
- Evaluate condition at loop head; stop when false or `max_iters` reached. Side effects accumulate.

**Validation**
- Condition must be `bool`.
- `max_iters` required and > 0 (enforced limit, e.g., 256).
- Disallow nested unbounded loops; consider banning nested while within for_each.

**Test Scenarios (target: ~10)**
- Happy path: `while x < 3` with `max_iters: 5`, `do` increments `x`; stops at condition false.
- Cap triggers: condition always true → stops at `max_iters` with clear error/message.
- Negative/zero `max_iters` → validation error.
- Nested while inside for_each rejected (if we enforce) → validation error.
- Condition non-bool → type-check error.
- State mutation visibility: changes in `do` affect next condition eval.
- Empty `do` allowed? (decide; test per decision.)
- Line/col surfaced in cap/condition errors.
- Interaction with iterator binding (if inside for_each): ensure forbidden or works as spec’d.
- Deterministic iteration count for known bounds (optional optimization test).

### parallel / fan-out

**Status:** ✅ PRODUCTION (disjoint-write enforcement)

**Motivation**: Express independent branches without order coupling.

**Syntax**
```yaml
- parallel:
    - <command>
    - <command>
```

**Semantics**
- Logical parallel: branches see the same input context; executed sequentially but must have disjoint write targets.
- Compiler enforces disjoint-write validation - conflicting writes rejected at compile time.

**Validation**
- All branches must write to different targets (no overlapping paths).
- Empty branch list rejected.
- Branch commands must type-check independently.

**Runtime**
- Branches execute sequentially in order listed.
- Each branch sees original context state (not mutations from previous branches).

**Examples**
```yaml
- parallel:
    - modify: "bar.energy"
      value: "10"
    - modify: "bar.health"
      value: "5"
    # Both modify different bars - allowed
```

### reduce / accumulate

**Status:** ✅ PRODUCTION (fixed-size tensor/list only)

**Motivation**: Fold a collection into a single value with explicit accumulator.

**Syntax**
```yaml
- reduce:
    collection: <expr>
    reduce_as: <iterator_variable>
    reduce_init: <expr>
    reduce_body: <expr_using_accumulator_and_iterator>
    reduce_into: <target_path>
```

**Semantics**
- Evaluate collection to fixed-size iterable; seed accumulator with `init`; for each element, compute new accumulator via `body`; write final accumulator to `into`.
- Collection must be fixed-size tensor or list (no ragged/unknown-length collections).

**Validation**
- Collection must type-check as `list` or `tensor` (enforces fixed-size constraint).
- Iterator binding same as `for_each`; accumulator type inferred from init.
- Accumulator type must be consistent across iterations; `into` type must match.
- Cap enforced same as `for_each` (256 elements).

**Runtime**
- Evaluates init, iterates collection, updates accumulator, writes to target.
- All fields (collection, iterator, init, body, into) are required.

**Examples**
```yaml
- reduce:
    collection: "[1, 2, 3, 4, 5]"
    reduce_as: "i"
    reduce_init: "0"
    reduce_body: "acc + i"
    reduce_into: "vfs.sum"
    # Result: vfs.sum = 15
```

### delay / schedule

**Status:** ✅ PRODUCTION (requires `time_enabled`)

**Motivation**: Time-shifted execution via scheduler.

**Syntax**
```yaml
- delay: <ticks_expr>
  do: [<commands>]
```

**Semantics**
- Schedule `do` to run after the evaluated number of ticks.
- Scheduler drains at start of each tick; zero-delay commands execute in same tick.
- **Requires `time_enabled: true`** - compilation fails when time disabled.

**Validation**
- `ticks_expr` must type-check as `int` with value >= 0 and <= 1,000 (MAX_DELAY_TICKS).
- `time_enabled` must be true (enforced at compile time).
- Queue cap of 10,000 items (MAX_SCHEDULED_ITEMS) enforced at runtime.

**Runtime**
- Evaluates ticks expression, enqueues commands with executor context.
- Scheduler persists commands across ticks and executes them at correct time.
- Zero-delay executes after current command completes but within same tick.

**Examples**
```yaml
- delay: "3"
  do:
    - modify: "bar.energy"
      value: "bar.energy + 5"
    # Executes 3 ticks later
```

### emit / event

**Status:** ❌ NOT IMPLEMENTED (planned for future)

**Motivation**: Publish events to be handled by other systems/effects.

**Syntax**
```yaml
- emit: "event_name"
  payload:
    key1: <expr>
    key2: <expr>
```

**Semantics**
- Raise an event with evaluated payload. Consumes an event bus; downstream handling out of scope here.

**Validation**
- Event name non-empty; payload expressions type-check; enforce payload size cap.

**Test Scenarios (target: ~6)**
- Happy path: emit with small payload; event bus receives expected payload.
- Empty event name → validation error.
- Payload expr type error → type-check error.
- Payload size exceeds cap → validation error.
- Reserved event name handling (if any) → error/allow per decision.
- Missing payload block defaults to empty dict (if allowed) or validation error (decide; test).

## Planning Pattern for New Commands

1) Write a focused DSL spec (syntax, semantics, validation, runtime rules, caps) and examples.
2) Decide AST shape (command-level node) and avoid expression grammar changes unless necessary.
3) Extend type checker (symbol table, type rules) and executor semantics; add caps/safeguards up front.
4) Add 10–20 unit tests per command (positive/negative, caps, edge cases) before integration tests.

## Runtime Limits & Caps

- `MAX_COLLECTION_SIZE`: 256 (for_each collection cap)
- `max_iters` (while): required, but while currently disallowed
- Nested for_each: untested/unsupported; add validation before use
- Scheduler: `MAX_DELAY_TICKS` = 1_000, `MAX_SCHEDULED_ITEMS` = 10_000; scheduling rejected when `time_enabled` is false.
