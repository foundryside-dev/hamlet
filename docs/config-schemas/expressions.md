# Expression Language Reference

> ⛔ **Restored to the live tree 2026-08-26 — this document UNDERSTATES the engine. Do not use its "planned" lists to decide what you can author.**
>
> Verified against `src/townlet/world/expression/functions.py` on 2026-08-26: the function
> registry `FUNCTION_SPECS` holds **49 working functions**. This document describes a small
> fraction of them and labels several *shipped* ones "planned but not yet implemented".
>
> **That is the most damaging way a doc in this repo can be wrong.** A designer who reads
> "planned" against the spatial and statistical functions concludes the declarative surface
> cannot express their idea and reaches for Python — which `CLAUDE.md` names as the exact
> product defect this project exists to prevent. The framework is more capable than this file
> says.
>
> **⚠️ These NINE ship today, despite being listed below as "planned"** (all present in
> `FUNCTION_SPECS`): `distance`, `within_radius`, `mean`, `sum`, `min`, `max`,
> `distance_to_affordance`, `manhattan_distance`, `perlin_noise`.
>
> **⚠️ "Function signature validation is deferred to Phase 2 (requires function registry)" is
> false.** The registry exists and type checking is wired:
> `world/expression/type_checker.py:358-366` — `visit_function_call` imports `FUNCTION_SPECS`,
> raises `Unknown function '<name>'` for anything absent, then calls `spec.validate_args()`.
>
> **⚠️ Two whole capability families are invisible here — 19 functions, entirely undocumented:**
> - *Temporal:* `lag`, `delta`, `ema`, `moving_average`, `rate_of_change`, `rising_edge`,
>   `falling_edge`, `elapsed_ticks`, `time_in_window`, `phase_sin`, `phase_cos`
> - *Tensor:* `gather`, `scatter`, `one_hot`, `masked_add`, `masked_set`, `argmin`, `argmax`,
>   `count_where` (`where` and `normalize` appear only incidentally — `normalize` is listed under
>   "Phase 3 planned" while it ships)
>
> **✅ The "planned" label IS correct for these** — genuinely absent from the registry, and they
> fail at **type-check** time (not parse) with `Unknown function`: `sin`, `cos`, `tan`, `asin`,
> `acos`, `atan`, `sqrt`, `count`, `random`, `bernoulli`, `normal`, `has_item`.
> (Note `normal_dist` and `uniform` *do* ship — the absent spellings are `normal` and `random`.)
>
> **⚠️ "Division always returns float" is FALSE, and it is stated twice.** Verified empirically:
> `42 / 10` type-checks to **`int`**; only `1.0 / 2` and `42 / 10.0` give `float`. This is the
> most treacherous error here, because `compile_variable` rejects a declared-vs-inferred type
> mismatch — so an author who trusts the sentence gets a compile failure with **no obvious link
> back to the sentence that caused it**. Fix: declare an operand or the variable as float
> (`42 / 10.0`).
>
> **⚠️ `temporal.*` — the single reconciled account** (this doc, `effects.md` and earlier notes
> disagreed; resolved at source 2026-08-26):
> - It **parses**, and the runtime context has a reader
>   (`world/expression/context.py:64-65`, `:234-237`).
> - But **no schema builder ever emits a `temporal.*` key.** `build_expression_schema`
>   (`universe/compilers/vfs.py:136-152`; sole caller `universe/compiler.py:454`) emits only
>   `bar.*`, `vfs.*`, `self.vfs.*`, `target.vfs.*`. Anything validated against that schema
>   therefore **fails at compile time**.
> - At runtime only the **item spawn-rule** path populates it, and only with the single key
>   `tick` (`items/manager.py:624`, `:630`). The **effects** path passes `temporal={}`
>   (`effects/executor.py:43`, `:739`), so it always raises there.
> - **✅ Correct working form: the bare `tick` variable** — the engine-written step counter,
>   reserved at `universe/compilers/vfs.py:130-132`. Do not write `temporal.tick`.
>
> **⚠️ Three of the six path roots this document teaches do not resolve**, for the same reason:
> the compile-time schema emits only the four roots listed above.
>
> **⚠️ The YAML examples in this file do not all compile.** Treat every example as
> unverified until the fix pass pins them with a test.
>
> **✅ Correct as documented** (do not "fix" these): the ternary form is `if C then A else B` —
> the Python conditional form failing is not a defect. And `sqrt`/`sin`/`cos` fail at
> **type-check**, not parse.
>
> Until this is rewritten, **`src/townlet/world/expression/functions.py` is the authority** on
> what you can call. Tracked as `hamlet-8f2e13c5a9`.
>
> *This document was audited twice on 2026-08-26 with materially different results; the second
> pass found the first had under-reported it. A doc this wrong should not be signed off on a
> single read — the durable answer is test-pinned examples, not repeated human passes.*


## Overview

The HAMLET Expression Language is a declarative, type-safe scripting language for specifying dynamic behaviors in configuration files. Expressions enable data-driven gameplay mechanics without Python code changes.

**Where expressions are used:**
- **VFS (Variable & Feature System)**: Computed variables (`expression: "bar.energy < 0.2"`)
- **Effects System**: Dynamic effect values (`value: "target.bar.health + (0.2 * intensity)"`)
- **Drive As Code (DAC)**: Reward modifiers (future), shaping bonuses (future)
- **Action Dependencies**: Preconditions (future), resource costs (future)

**Key characteristics:**
- **GPU-native**: Evaluates on batched tensors for vectorized environments
- **Type-safe**: Compile-time type checking prevents runtime errors
- **Declarative**: Pure expressions, no side effects or assignments
- **Pedagogical**: Simple syntax accessible to students learning RL

**Architecture:**
```
YAML Config → Parser → AST → Type Checker → Evaluator → GPU Tensors
```

## Syntax

### Literals

Expression Language supports four literal types:

**Integers** (type: `int`):
```
42
-10
0
```

**Floats** (type: `float`):
```
0.05
-10.3
1.0
1e-3      # Scientific notation
1.5e-5    # Scientific notation
```

**Note**: `42` is an integer, `42.0` is a float. This distinction matters for type checking.

**Booleans** (type: `bool`):
```
true
false
```

**Strings** (type: `str`):
```
"energy"
'Fridge'
"Escaped \"quotes\""
```

### Variables

Simple identifiers reference values from the execution context:

```
intensity       # Effect intensity parameter
duration        # Effect duration parameter
slot_index      # Item inventory slot
```

**Note**: Variables must be defined in the expression schema (VFS variables, effect parameters, etc.). Undefined variables fail type checking.

### Path Access

Dot notation accesses nested state:

```
bar.energy                  # Agent's energy meter
bar.health                  # Agent's health meter
vfs.is_night               # Global VFS variable
vfs.agent.motivation       # Agent VFS variable
temporal.tick              # Current simulation tick
target.bar.health          # Target agent's health (in effects)
self.position              # Item's position (in item expressions)
```

**Path namespaces:**
- `bar.*` - Meter values (energy, health, satiation, etc.)
- `vfs.*` - VFS variables (global or agent scope)
- `temporal.*` - Time-based values (tick, day, hour, is_night)
- `target.*` - Target entity in effects (agent, item, affordance)
- `self.*` - Current entity in expressions (item age, position)
- `item.*` - Item-local state when evaluating item rules (e.g., `item.vfs.durability`)

**Type checking**: Paths must exist in the schema. Invalid paths fail at compile time.

### Operators

Expression Language supports arithmetic, comparison, and logical operators with C-style precedence.

#### Arithmetic Operators

```
a + b           # Addition
a - b           # Subtraction
a * b           # Multiplication
a / b           # Division (always returns float)
a % b           # Modulo (remainder)
a ** b          # Exponentiation (right-associative)
-a              # Unary negation
```

**Type rules:**
- Operands must be numeric (`int` or `float`)
- `int op int → int` (except division)
- `int op float → float` (type promotion)
- `float op float → float`
- Division always returns `float`

**Examples:**
```
bar.energy + 0.05           # Add to energy
bar.health * 2              # Double health
temporal.tick % 24          # Hour of day (0-23)
2 ** 3                      # Power: 8
```

#### Comparison Operators

```
a == b          # Equal
a != b          # Not equal
a < b           # Less than
a > b           # Greater than
a <= b          # Less than or equal
a >= b          # Greater than or equal
```

**Type rules:**
- Operands must be numeric
- Returns `bool`

**Examples:**
```
bar.energy < 0.2            # Crisis detection
bar.health > 50             # Health threshold
temporal.tick >= 18         # Night time check
```

#### Logical Operators

```
a and b         # Logical AND
a or b          # Logical OR
not a           # Logical NOT
```

**Type rules:**
- Operands must be `bool`
- Returns `bool`

**Examples:**
```
bar.energy < 0.2 or bar.health < 0.2        # Any crisis
bar.energy > 0.5 and vfs.is_night           # Energy and night
not (bar.health > 50)                       # Health not above 50
```

## Integration Examples

### VFS Variables

```yaml
vfs_profiles:
  agent_profiles:
    player:
      variables:
        is_critical:
          type: bool
          expression: "bar.energy < 0.2 or bar.health < 0.3"
```

### Effect Conditions

```yaml
effects_catalog:
  effects:
    regeneration:
      commands:
        - type: "if"
          condition: "target.bar.health < 0.5"
          then:
            - type: "modify"
              path: "target.bar.health"
              operation: "add"
              value: 0.1
```

### Spawn Conditions (Items)

```yaml
spawn_rules:
  - item_type: "apple"
    when: "not vfs:is_winter and bar.energy < 0.8"
```

## Type System Reference

- **int**: Integer values (1, 42, -10)
- **float**: Floating-point values (0.5, 3.14, -2.7)
- **bool**: Boolean values (true, false)
- **str**: String values ("energy")
- **list**: Homogeneous lists (Phase 1 limited support)

**Implicit conversions**

✅ Allowed: int → float (e.g., `bar.energy * 10` promotes 10 to 10.0)

❌ Forbidden: bool ↔ numeric. Use explicit comparisons:
- Wrong: `bar.energy and bar.health`
- Right: `bar.energy > 0 and bar.health > 0`

## Troubleshooting

- **Undefined variable**: `Path 'vfs.foo' not found in schema` → Ensure the variable is declared in the relevant profile.
- **Type mismatch**: `Logical operator and requires bool operands` → Wrap numeric expressions in comparisons.
- **Unknown path**: `Path 'item.vfs.durability' not found` → Ensure schema includes item VFS variables for item contexts.

## Phase 2 Roadmap (Deferred Operators)

The following operators are planned but not yet implemented:

**Trigonometric:** `sin`, `cos`, `tan`, `asin`, `acos`, `atan`

**Spatial:** `distance(pos1, pos2)`, `within_radius(pos, center, radius)`

**Statistical:** `mean(list)`, `sum(list)`, `count(list)`, `min(list)`, `max(list)`

**Stochastic:** `random()`, `bernoulli(p)`, `normal(mean, std)`

#### Operator Precedence

Operators are evaluated in the following order (highest to lowest):

| Precedence | Operators          | Associativity | Example                    |
|------------|-------------------|---------------|----------------------------|
| 1          | `()`, `[]`, `.`   | Left          | `(a + b)`, `arr[i]`, `bar.energy` |
| 2          | `-` (unary), `not` | Right        | `-x`, `not active`         |
| 3          | `**`              | Right         | `2 ** 3 ** 4` → `2 ** (3 ** 4)` |
| 4          | `*`, `/`, `%`     | Left          | `a + b * c` → `a + (b * c)` |
| 5          | `+`, `-`          | Left          | `a - b + c` → `(a - b) + c` |
| 6          | `==`, `!=`, `<`, `>`, `<=`, `>=` | Left | `a < b == c < d` |
| 7          | `and`             | Left          | `a and b and c`            |
| 8          | `or`              | Left          | `a or b or c`              |

**Use parentheses for clarity:**
```
a + b * c               # Parses as: a + (b * c)
(a + b) * c             # Override precedence
bar.energy < 0.2 or bar.health < 0.2    # Clear intent
```

### Conditional Expressions (If-Then-Else)

Ternary conditional operator for branching logic:

```
if condition then true_branch else false_branch
```

**Type rules:**
- `condition` must be `bool`
- `true_branch` and `false_branch` must have same type
- Returns type of branches

**Examples:**
```
if bar.energy < 0.2 then 1.0 else 0.0                       # Crisis bonus
if vfs.is_night then 0.5 else 1.0                           # Time multiplier
if bar.health > 50 then "healthy" else "injured"            # Status string
if a then (if b then 1.0 else 2.0) else 3.0                 # Nested conditionals
```

**GPU execution**: Uses `torch.where()` for vectorized evaluation across all agents. Both branches are evaluated (no short-circuit).

### Index Access (Arrays)

Access array/list elements by integer index:

```
inventory[0]              # Constant index
items[slot_index]         # Variable index
values[i + 1]             # Computed index
grid[x][y]                # Nested access (chained IndexAccess nodes)
```

**Type rules:**
- Base must be array/list type
- Index must be `int`
- Returns element type

**Note**: Index access type checking is deferred to Phase 4 (requires array types in schema).

### Function Calls

Invoke built-in or domain-specific functions:

```
function_name(arg1, arg2, ...)
```

**Standard math functions:**
```
max(a, b)                 # Element-wise maximum
min(a, b)                 # Element-wise minimum
abs(x)                    # Absolute value
clamp(x, min_val, max_val) # Clamp to range
```

**Examples:**
```
max(bar.energy, 0.0)                        # Ensure non-negative
clamp(bar.health + 0.2, 0.0, 1.0)          # Add health, clamp to [0,1]
abs(target.position.x - self.position.x)    # Distance (1D)
```

**Domain-specific functions (Phase 2 - planned):**
```
distance_to_affordance("Fridge")            # Spatial distance
has_item("Apple")                            # Inventory check
perlin_noise(x, y, seed)                     # Procedural generation
manhattan_distance(pos1, pos2)               # L1 distance
```

**Type checking**: Function signature validation is deferred to Phase 2 (requires function registry).

## Type System

Expression Language uses static type checking to catch errors at compile time (UAC stage) before runtime evaluation.

### Primitive Types

**Numeric types:**
- `int` - Integer values (42, -10, 0)
- `float` - Floating-point values (0.05, -10.3, 1e-3)

**Other primitives:**
- `bool` - Boolean values (true, false)
- `str` - String literals ("energy", 'Fridge')

### Type Inference

Types are inferred bottom-up from leaves to root:

1. **Constants**: Inferred from Python type (`42` → `int`, `0.5` → `float`, `true` → `bool`)
2. **Variables/Paths**: Looked up in schema (`bar.energy` → schema["bar.energy"] → `float`)
3. **Operators**: Type-specific rules (see below)
4. **Functions**: Signature lookup (Phase 2)

### Type Promotion

Numeric operations follow automatic type promotion:

```
int + int → int
int + float → float
float + float → float
```

**Example:**
```
42 + 10        # Type: int (result: 52)
42 + 10.0      # Type: float (result: 52.0)
bar.energy + 1 # Type: float (bar.energy is float, promotes 1 to 1.0)
```

### Type Checking Rules

**Arithmetic operators** (`+`, `-`, `*`, `/`, `%`, `**`):
- Both operands must be numeric (`int` or `float`)
- Type promotes to `float` if either operand is `float`
- Division always returns `float`

**Comparison operators** (`==`, `!=`, `<`, `>`, `<=`, `>=`):
- Both operands must be numeric
- Returns `bool`

**Logical operators** (`and`, `or`, `not`):
- Operands must be `bool`
- Returns `bool`

**Conditional expressions** (`if-then-else`):
- Condition must be `bool`
- True and false branches must have same type
- Returns branch type

### Type Errors

Type checker raises `TypeCheckError` with descriptive messages:

**Unknown variable:**
```
Expression: bar.unknown_var + 10
Error: Path 'bar.unknown_var' not found in schema. Available paths: ['bar.energy', 'bar.health']
```

**Type mismatch (arithmetic):**
```
Expression: "hello" + 5
Error: Arithmetic operator + requires numeric operands, got incompatible types str and int
```

**Type mismatch (logical):**
```
Expression: bar.energy and bar.health
Error: Logical operator and requires bool operands, got incompatible types float and float
```

**Conditional branch mismatch:**
```
Expression: if condition then 1 else "two"
Error: If branches must have same type. Got int (true) and str (false)
```

## Examples

### Simple Expressions

**Constant values:**
```yaml
expression: "0.05"              # Float literal
expression: "42"                # Integer literal
expression: "true"              # Boolean literal
```

**Variable access:**
```yaml
expression: "intensity"         # Effect parameter
expression: "duration"          # Effect parameter
```

**Path access:**
```yaml
expression: "bar.energy"        # Agent's energy meter
expression: "vfs.is_night"      # Global VFS variable
```

### Arithmetic Expressions

**Meter modifications:**
```yaml
# Energy regeneration
value: "target.bar.energy + 0.05"

# Health boost with intensity scaling
value: "target.bar.health + (0.2 * intensity)"

# Damage over time
value: "target.bar.health - (0.02 * intensity)"
```

**Computed values:**
```yaml
# Average of two meters
expression: "(bar.energy + bar.health) / 2.0"

# Hour of day (0-23)
expression: "temporal.tick % 24"

# Energy deficit
expression: "1.0 - bar.energy"
```

### Boolean Expressions

**Crisis detection:**
```yaml
# Single resource crisis
expression: "bar.energy < 0.2"

# Any resource crisis
expression: "bar.energy < 0.2 or bar.health < 0.2"

# Critical crisis (multiple resources)
expression: "bar.energy < 0.1 and bar.health < 0.1"
```

**Time-based conditions:**
```yaml
# Night time (ticks 18-23, 0-5 in 24-tick day)
expression: "temporal.tick % 24 >= 18 or temporal.tick % 24 < 6"

# Simplified night check (using modulo wrap)
expression: "temporal.tick % 24 >= 18"

# Day time
expression: "temporal.tick % 24 >= 6 and temporal.tick % 24 < 18"
```

**Item state:**
```yaml
# Food spoilage (item age > 100 ticks)
expression: "self.age > 100"

# Weapon durability check
expression: "self.durability > 0"
```

### Conditional Expressions

**Context-aware bonuses:**
```yaml
# Crisis bonus (1.0 in crisis, 0.0 otherwise)
expression: "if bar.energy < 0.2 then 1.0 else 0.0"

# Time-of-day multiplier
expression: "if vfs.is_night then 0.5 else 1.0"

# Status-based reward
expression: "if bar.health > 0.8 then 10.0 else 5.0"
```

**Nested conditionals:**
```yaml
# Tiered bonuses
expression: "if bar.energy < 0.2 then 2.0 else (if bar.energy < 0.5 then 1.0 else 0.0)"

# Complex logic
expression: "if vfs.is_night and bar.energy < 0.3 then 3.0 else 1.0"
```

### Complex Expressions

**VFS computed variables:**
```yaml
# Global profile - night detection
- name: is_night
  type: bool
  expression: "temporal.tick % 24 >= 18"

# Agent profile - crisis state
- name: is_crisis
  type: bool
  expression: "bar.energy < 0.2 or bar.health < 0.2"

# Agent profile - motivation decay
- name: motivation
  type: float
  expression: "max(0.1, 1.0 - (temporal.tick / 10000.0))"
```

**Effect modifications:**
```yaml
# Energy regeneration with time-of-day scaling
value: "target.bar.energy + (0.05 * intensity * (if vfs.is_night then 1.5 else 1.0))"

# Health decay with crisis acceleration
value: "target.bar.health - (0.02 * (if bar.health < 0.2 then 2.0 else 1.0))"

# Conditional resource transfer
value: "if target.bar.energy < 0.5 then target.bar.energy + 0.1 else target.bar.energy"
```

**Drive As Code (future):**
```yaml
# Modifier - crisis suppression
expression: "if bar.energy < 0.2 or bar.health < 0.2 then 0.0 else 1.0"

# Shaping bonus - efficiency reward
expression: "if temporal.tick < 100 then 0.1 else 0.0"
```

### Function Call Examples

**Range clamping:**
```yaml
# Add energy, clamp to [0,1]
value: "clamp(target.bar.energy + 0.2, 0.0, 1.0)"

# Ensure non-negative
value: "max(target.bar.health - 0.05, 0.0)"
```

**Math operations:**
```yaml
# Absolute value for distance
expression: "abs(target.position.x - self.position.x)"

# Nested function calls
expression: "max(abs(bar.energy - 0.5), abs(bar.health - 0.5))"
```

## Type Checking

### Compile-Time Validation

Type checking occurs during UAC (Universe Compiler) parsing, before any expressions execute. This catches errors early in the development cycle.

**Validation process:**
1. Parser converts expression string to AST
2. Type checker traverses AST bottom-up
3. Each node's type is inferred from children
4. Type rules enforce compatibility (numeric ops, bool ops, etc.)
5. Type errors abort compilation with descriptive messages

**Benefits:**
- **Fail fast**: Catch errors before training starts
- **Clear errors**: Descriptive messages with available variables
- **Safe refactoring**: Renaming variables fails if expressions break
- **Documentation**: Schema serves as expression API documentation

### Error Messages

Type checker provides actionable error messages with context:

**Unknown variable:**
```
Expression: motivation + 0.1
Error: Variable 'motivation' not found in schema.
       Available variables: ['intensity', 'duration', 'slot_index']
```

**Unknown path:**
```
Expression: bar.stamina < 0.5
Error: Path 'bar.stamina' not found in schema.
       Available paths: ['bar.energy', 'bar.health', 'bar.mood']
```

**Type mismatch:**
```
Expression: bar.energy and bar.health
Error: Logical operator and requires bool operands, got incompatible types float and float

Fix: Use comparison first: (bar.energy > 0.5) and (bar.health > 0.5)
```

**Branch type mismatch:**
```
Expression: if bar.energy < 0.2 then 1 else 0.5
Error: If branches must have same type. Got int (true) and float (false)

Fix: Make both branches same type: if bar.energy < 0.2 then 1.0 else 0.5
```

### Schema Requirements

Expressions require a schema defining available variables and their types:

**VFS expressions:**
```python
schema = {
    "bar.energy": "float",
    "bar.health": "float",
    "temporal.tick": "int",
    "vfs.is_night": "bool",
}
```

**Effect expressions:**
```python
schema = {
    "target.bar.energy": "float",
    "target.bar.health": "float",
    "intensity": "float",
    "duration": "int",
}
```

**Item expressions:**
```python
schema = {
    "self.age": "int",
    "self.durability": "int",
    "bar.energy": "float",  # Host agent's meters
}
```

## Performance

### Parsing Overhead

**Compilation phase** (once per config load):
- Expression strings → AST via pyparsing (~100μs per expression)
- Type checking via AST traversal (~50μs per expression)
- AST cached in compiled UAC artifacts

**Optimization**: Packrat parsing enabled for ~2x speedup on complex expressions.

**Impact**: Negligible. Parsing happens once during config load, not per-step.

### Evaluation Speed

**Runtime execution** (per environment step):
- AST traversal with GPU tensor operations
- Vectorized across all agents (batch_size)
- Dominated by tensor ops, not AST traversal

**Benchmarks** (from `tests/test_townlet/performance/test_expression_benchmarks.py`):
- Simple arithmetic (`bar.energy + 0.05`): ~10μs per 1024-agent batch
- Complex expression (`(a + b) * (c - d) / e`): ~25μs per 1024-agent batch
- Conditional (`if x > 0 then y else z`): ~15μs per 1024-agent batch

**Bottleneck**: Tensor operations (addition, comparison, where), not expression structure.

**Scaling**: Linear with batch size, O(1) with expression complexity (GPU parallelism).

### Caching

**AST caching**:
- Parsed ASTs stored in UAC compiled artifacts
- No re-parsing during training
- Loaded once at environment initialization

**Execution context caching**:
- ExecutionContext reused across steps
- Tensors updated in-place (bars, vfs, temporal)
- No garbage collection overhead

**Impact**: Training performance unaffected by expression complexity. 10M steps with complex expressions has same performance as simple expressions.

## Best Practices

### 1. Always Use Parentheses for Clarity

Precedence rules are correct but not always intuitive. Use parentheses to make intent explicit:

```yaml
# Ambiguous
expression: "bar.energy * 2 + bar.health / 5"

# Clear
expression: "(bar.energy * 2.0) + (bar.health / 5.0)"
```

### 2. Clamp Values After Modifications

Meter values should stay in valid ranges (typically [0,1]):

```yaml
# Bad - can overflow
value: "target.bar.energy + 0.2"

# Good - clamped to [0,1]
value: "clamp(target.bar.energy + 0.2, 0.0, 1.0)"
```

### 3. Use Consistent Types in Conditionals

Both branches must have the same type:

```yaml
# Bad - type mismatch (int vs float)
expression: "if bar.energy < 0.2 then 1 else 0.0"

# Good - both float
expression: "if bar.energy < 0.2 then 1.0 else 0.0"
```

### 4. Avoid Complex Nesting

Break complex expressions into VFS computed variables:

```yaml
# Bad - hard to read
expression: "if (bar.energy < 0.2 or bar.health < 0.2) and (temporal.tick % 24 >= 18) then 2.0 else (if bar.energy < 0.5 then 1.0 else 0.0)"

# Good - use VFS variables
# In vfs_profiles.yaml:
- name: is_crisis
  type: bool
  expression: "bar.energy < 0.2 or bar.health < 0.2"

- name: is_night
  type: bool
  expression: "temporal.tick % 24 >= 18"

# In effects.yaml:
expression: "if vfs.is_crisis and vfs.is_night then 2.0 else (if bar.energy < 0.5 then 1.0 else 0.0)"
```

### 5. Use Meaningful Variable Names

VFS computed variables should have descriptive names:

```yaml
# Bad
- name: x
  type: bool
  expression: "bar.energy < 0.2"

# Good
- name: energy_crisis
  type: bool
  expression: "bar.energy < 0.2"
```

### 6. Comment Complex Logic

Add YAML comments explaining non-obvious expressions:

```yaml
# Night time: ticks 18-23 in 24-tick day cycle
- name: is_night
  type: bool
  expression: "temporal.tick % 24 >= 18"

# Tiered crisis bonuses: 2x for severe (<0.1), 1.5x for moderate (<0.2)
value: "if bar.energy < 0.1 then 2.0 else (if bar.energy < 0.2 then 1.5 else 1.0)"
```

### 7. Test Expressions in Isolation

Use integration tests to verify expression behavior:

```python
# Test crisis detection
parser = ExpressionParser()
ast = parser.parse("bar.energy < 0.2 or bar.health < 0.2")

schema = {"bar.energy": "float", "bar.health": "float"}
type_checker = TypeChecker(schema)
type_checker.check(ast)  # Verify type correctness

context = ExecutionContext(
    bars={"energy": torch.tensor(0.1), "health": torch.tensor(0.8)},
    vfs={}, affordances={}, temporal={}
)
evaluator = Evaluator(context)
result = evaluator.evaluate(ast)
assert result.item() is True  # Energy crisis detected
```

### 8. Avoid Division by Zero

Use `max()` to ensure non-zero denominators:

```yaml
# Bad - can divide by zero
expression: "bar.energy / bar.health"

# Good - ensure denominator >= 0.001
expression: "bar.energy / max(bar.health, 0.001)"
```

### 9. Prefer `max()/min()` Over Conditionals

For simple clamping, use functions instead of if-then-else:

```yaml
# Verbose
expression: "if bar.energy < 0.0 then 0.0 else bar.energy"

# Concise
expression: "max(bar.energy, 0.0)"
```

### 10. Profile Expression Performance

If expressions are bottlenecks (rare), use benchmarks to identify culprits:

```bash
uv run pytest tests/test_townlet/performance/test_expression_benchmarks.py -v
```

**Note**: Expression evaluation is almost never the bottleneck. GPU tensor operations (environment step, neural network forward pass) dominate training time.

---

## Future Extensions

**Phase 2 - Domain-Specific Functions** (planned):
- Spatial functions: `distance_to_affordance()`, `nearest_agent()`
- Inventory queries: `has_item()`, `count_items()`
- Statistical functions: `mean()`, `sum()`, `count()`

**Phase 3 - Vector Types** (planned):
- `vec2i`, `vec3i` types for positions
- Vector arithmetic: `position + velocity`
- Magnitude: `length(vec)`, `normalize(vec)`

**Phase 4 - Array Types** (planned):
- List/array types: `list[int]`, `list[float]`
- Index access type checking
- Array functions: `len()`, `slice()`

**Phase 5 - Lambda Expressions** (speculative):
- Higher-order functions: `map()`, `filter()`, `reduce()`
- Anonymous functions: `lambda x: x * 2`

---

## See Also

- **VFS Configuration**: `docs/config-schemas/variables.md` - Variable definitions and computed variables
- **Effects System**: `docs/plans/2025-11-15-phase-5-effects-integration.md` - Effect value expressions
- **Drive As Code**: `docs/config-schemas/drive_as_code.md` - Reward modifiers (future)
- **Implementation**: `src/townlet/world/expression/` - Parser, evaluator, type checker source code
- **Tests**: `tests/test_townlet/unit/world/expression/` - Expression system test suite
