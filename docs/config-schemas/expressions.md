# Expression Language Reference

> **Function inventory is generated.** The table under [Function Reference](#function-reference)
> is rendered from the registry `FUNCTION_SPECS` (`src/townlet/world/expression/functions.py`)
> by `scripts/gen_expression_functions_doc.py`; a test fails when the two disagree, so the table
> is the registry. The registry is also what the type checker and the evaluator run from, and
> `tests/test_townlet/unit/world/expression/test_function_registry_agreement.py` holds every
> function's declared return type to its evaluated dtype and batch shape.
>
> Two caveats that remain true (2026-10-24). First, the compile-time schemas resolve only these
> path roots: `bar.*`, `vfs.*`, `self.vfs.*` and `target.vfs.*` for VFS expressions, plus
> `target.bar.*` and `global.vfs.*` inside effects; `temporal.*`, `self.position`, `item.*` and the
> other roots the namespace list below mentions do not resolve, and the engine step counter is read
> through the bare `tick` variable. Second, the YAML examples in this file are illustrative, not
> test-pinned.

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
variables:
  version: '1.0'
  extents: {}
  item_profiles: []
  declarations:
  - id: is_critical
    scope: agent
    type: bool
    lifetime: episode
    semantic_type: custom
    initial_value: false
    exposed_to: []
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

## Functions That Do Not Exist

These spellings appear in older notes and fail at type check with `Unknown function '<name>'`:
`sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sqrt`, `count`, `random`, `bernoulli`, `normal`,
`has_item`, `length`. Use `phase_sin` / `phase_cos` for periodic signals, `x ** 0.5` for a square
root, `count_where` to count true conditions, `uniform` / `normal_dist` for random draws, and
`distance(v, v)` with a zero vector for a vector's length. The authority on what you can call is
the [Function Reference](#function-reference).


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

**Note**: Index access is not type-checked against an element type; the checker treats every indexed element as `float`.

### Function Calls

Invoke a registered function with positional arguments:

```
function_name(arg1, arg2, ...)
```

**Examples:**
```
max(bar.energy, 0.0)                        # Ensure non-negative
clamp(bar.health + 0.2, 0.0, 1.0)           # Add health, clamp to [0,1]
mean(bar.energy, bar.health)                # Each agent's mean of two meters
distance(vfs.position, vfs.home)            # Per-agent distance between two vec2f variables
```

**Type checking**: every call is checked against the registry: an unknown name, a wrong
argument count or a wrong argument type is a compile-time `TypeCheckError`. The return type is
the declared one in the [Function Reference](#function-reference); the evaluator produces that
dtype, and a scalar-typed result keeps the `[batch]` axis of its per-agent inputs.

## Function Reference

<!-- BEGIN GENERATED: expression-functions (scripts/gen_expression_functions_doc.py) -->
49 functions are registered. A scalar-typed result (`int`, `float`, `bool`) keeps the batch axis of its
per-agent inputs; a vector-typed result (`vec2f`, `vec3f`, `vecNf`) keeps it in front of the vector axis. No function
collapses the batch axis. A literal has no batch axis, so a result built only from literals is unbatched:
`one_hot(2, 3)` is `[3]`, `one_hot(bar.slot, 3)` is `[batch, 3]`.

### Math

Element-wise over numeric scalars.

| Function | Returns | What it computes | Needs |
|---|---|---|---|
| `abs(x)` | int when every argument is int, else float | Absolute value. | — |
| `clamp(x, low, high)` | int when every argument is int, else float | Clamp `x` into `[low, high]`. | — |
| `clamp01(x)` | float | Clamp `x` into `[0.0, 1.0]`. | — |
| `max(a, b)` | int when every argument is int, else float | Element-wise maximum of two numbers. | — |
| `min(a, b)` | int when every argument is int, else float | Element-wise minimum of two numbers. | — |
| `sigmoid(x)` | float | Logistic sigmoid `1 / (1 + exp(-x))`. | — |
| `smoothstep(edge0, edge1, x)` | float | Hermite interpolation of `x` from 0 at `edge0` to 1 at `edge1`. | — |
| `tanh(x)` | float | Hyperbolic tangent. | — |
| `threshold(x, low, high)` | bool | `x > low`, forced true once `x >= high` (a two-level trigger). | — |

### Statistics

Reduced across the *arguments*, never across agents: `mean(bar.energy, bar.health)` is each agent's own mean.

| Function | Returns | What it computes | Needs |
|---|---|---|---|
| `argmax(a, b, ...)` | int | Zero-based position of the largest argument. | — |
| `argmin(a, b, ...)` | int | Zero-based position of the smallest argument. | — |
| `count_where(c1, c2, ...)` | int | How many of the bool arguments are true. | — |
| `max_all(a, b, ...)` | int when every argument is int, else float | Largest of the arguments. | — |
| `mean(a, b, ...)` | float | Arithmetic mean of the arguments. | — |
| `min_all(a, b, ...)` | int when every argument is int, else float | Smallest of the arguments. | — |
| `product(a, b, ...)` | float | Product of the arguments. | — |
| `sum(a, b, ...)` | float | Sum of the arguments. | — |
| `variance(a, b, ...)` | float | Population variance of the arguments. | — |

### Logic and masks

Boolean combination and masked selection; `gather`/`scatter` index rows of a per-agent value.

| Function | Returns | What it computes | Needs |
|---|---|---|---|
| `all(c1, c2, ...)` | bool | True when every bool argument is true. | — |
| `any(c1, c2, ...)` | bool | True when at least one bool argument is true. | — |
| `gather(values, index)` | the type of `values` | `values[index]`: read another row of a per-agent value by integer index. | — |
| `masked_add(value, delta, mask)` | the numeric type of `value` and `delta` (promoted) | `value + delta` where `mask` holds, `value` elsewhere. | — |
| `masked_set(value, replacement, mask)` | the type of `value` (numeric pairs promote) | `replacement` where `mask` holds, `value` elsewhere. | — |
| `one_hot(index, classes)` | vecNf of width `classes` | One-hot vector of width `classes` (a literal >= 2) with a 1.0 at `index`. | — |
| `scatter(base, index, updates)` | the type of `base` | A copy of `base` with `updates` written at `index`. | — |
| `where(condition, if_true, if_false)` | the branch type (numeric branches promote) | Select `if_true` where `condition` holds, else `if_false`; the branches must share a type. | — |

### Sampling

Random draws take the shape of their first argument; noise fields are deterministic in their inputs.

| Function | Returns | What it computes | Needs |
|---|---|---|---|
| `normal_dist([mean[, std]])` | float | Gaussian draw; one draw per element of `mean`, a single scalar draw with no arguments. | — |
| `perlin_noise(x[, y[, seed]])` | float | Deterministic 2-D Perlin gradient noise at `(x, y)`. | — |
| `simplex_noise(x[, y[, seed]])` | float | Alias of `perlin_noise`: the same gradient-noise field, not a simplex lattice. | — |
| `uniform([low[, high]])` | float | Uniform draw in `[low, high)` (`[0, 1)` with one or no arguments); one draw per element of `low`. | — |

### Temporal

History operators read the temporal history the VFS evaluator maintains; `time_in_window` measures a 24-tick day.

| Function | Returns | What it computes | Needs |
|---|---|---|---|
| `delta(x)` | int when every argument is int, else float | `x - lag(x, 1)`, 0 on the first tick. | temporal history on the context |
| `elapsed_ticks([start[, now]])` | int | Ticks since `start` (clamped at 0); `now` defaults to the engine step, and with no arguments the step itself. | the engine step counter on the context |
| `ema(x, alpha)` | float | Exponential moving average of `x` with smoothing `alpha` in `(0, 1]`. | temporal history on the context |
| `falling_edge(flag)` | bool | True on the tick `flag` turns from true to false. | temporal history on the context |
| `lag(x, n)` | int when every argument is int, else float | The value `x` held `n` ticks ago (0 before the history is that deep). | temporal history on the context |
| `moving_average(x, window)` | float | Mean of `x` over the last `window` ticks including this one. | temporal history on the context |
| `phase_cos(time, period)` | float | `cos(2π · time / period)`. | — |
| `phase_sin(time, period)` | float | `sin(2π · time / period)`. | — |
| `rate_of_change(x, window)` | float | `(x - lag(x, window)) / window`. | temporal history on the context |
| `rising_edge(flag)` | bool | True on the tick `flag` turns from false to true. | temporal history on the context |
| `time_in_window(time, start, end)` | bool | True when `time` modulo a 24-tick day lies in `[start, end)`, wrapping past midnight. | — |

### Spatial

Vector variables only (`vec2i`, `vec3i`, `vec2f`, `vec3f`, `vecNi`, `vecNf`); the distance between two scalars is `abs(a - b)`. Both vectors must share a width: `vec2*` against `vec3*` is refused at compile time; a `vecN*` or `tensor2d` width is only known at run time, and a mismatch there raises an error naming the function. Int and float vectors mix freely and are measured in float.

| Function | Returns | What it computes | Needs |
|---|---|---|---|
| `distance(a, b[, "manhattan" \| "euclidean"])` | float | Distance between two vector variables of one width, measured in float (default euclidean). | — |
| `manhattan_distance(a, b)` | float | L1 distance between two vector variables of one width, measured in float. | — |
| `nearest(point, candidates[, "manhattan" \| "euclidean"])` | int | Row index of the candidate nearest to `point`; `candidates` is a vector variable or a tensor2d of rows. | — |
| `normalize(v)` | the float vector type of `v`'s width (vec2f, vec3f or vecNf) | `v` scaled to unit euclidean length (the zero vector stays zero). | — |
| `within_radius(a, b, radius[, "manhattan" \| "euclidean"])` | bool | True when `distance(a, b)` is at most `radius`. | — |

### Affordance

Read the agent and affordance positions the engine threads into the context.

| Function | Returns | What it computes | Needs |
|---|---|---|---|
| `direction_to_affordance("NAME"[, "manhattan" \| "euclidean"])` | vecNf of the substrate's position width | Unit vector from each agent towards the named affordance (zero at the affordance or when it is not deployed). | agent and affordance positions on the context |
| `distance_to_affordance("NAME"[, "manhattan" \| "euclidean"])` | float | Each agent's distance to the named affordance (default manhattan); infinity when it is not deployed. | agent and affordance positions on the context |
| `in_range("NAME", radius[, "manhattan" \| "euclidean"])` | bool | True for each agent within `radius` of the named affordance. | agent and affordance positions on the context |
<!-- END GENERATED: expression-functions -->


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
4. **Functions**: Signature lookup in the registry `FUNCTION_SPECS` (see [Function Reference](#function-reference))

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
expression: "tick % 24 >= 18"

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
# Global derived state - night detection
- id: is_night
  scope: global
  type: bool
  lifetime: episode
  semantic_type: custom
  initial_value: false
  exposed_to: []
  expression: "tick % 24 >= 18"

# Agent derived state - crisis state
- id: is_crisis
  scope: agent
  type: bool
  lifetime: episode
  semantic_type: custom
  initial_value: false
  exposed_to: []
  expression: "bar.energy < 0.2 or bar.health < 0.2"

# Global derived state - shared motivation decay
- id: motivation
  scope: global
  type: scalar
  lifetime: episode
  semantic_type: custom
  initial_value: 1.0
  exposed_to: []
  expression: "max(0.1, 1.0 - (tick / 10000.0))"
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
# In variables.declarations (complete required fields shown in variables.md):
- id: is_crisis
  type: bool
  expression: "bar.energy < 0.2 or bar.health < 0.2"

- id: is_night
  type: bool
  expression: "tick % 24 >= 18"

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
- id: is_night
  type: bool
  expression: "tick % 24 >= 18"

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

Not in the registry today (they fail at type check with `Unknown function`):

- Inventory queries: `has_item()`, `count_items()`
- Nearest-agent queries: `nearest_agent()`
- Vector arithmetic with operators (`position + velocity`); vectors are consumed by the
  spatial functions only
- Array types (`list[int]`, `list[float]`), index-access type checking, `len()`, `slice()`
- Lambda expressions and higher-order functions

---


## See Also

- **VFS Configuration**: `docs/config-schemas/variables.md` - Variable definitions and computed variables
- **Effects System**: `docs/plans/2025-11-15-phase-5-effects-integration.md` - Effect value expressions
- **Drive As Code**: `docs/config-schemas/drive_as_code.md` - Reward modifiers (future)
- **Implementation**: `src/townlet/world/expression/` - Parser, evaluator, type checker source code
- **Tests**: `tests/test_townlet/unit/world/expression/` - Expression system test suite
