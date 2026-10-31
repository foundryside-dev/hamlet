# SG5 — Substrate & World Expression DSL

Two co-located but unrelated subsystems share this report: the spatial
substrate hierarchy (`src/townlet/substrate/`) and the expression DSL
(`src/townlet/world/`). They do not import each other.

---

## Part A: Substrate

**Location:** `src/townlet/substrate/` (3,798 LOC across 9 `.py` files; counted via `wc -l`)

**Files:**
- `base.py` (323 LOC) — abstract base class `SpatialSubstrate`
- `factory.py` (152 LOC) — `SubstrateFactory.build()`
- `aspatial.py` (162 LOC) — `AspatialSubstrate`
- `grid2d.py` (605 LOC) — `Grid2DSubstrate`
- `grid3d.py` (620 LOC) — `Grid3DSubstrate`
- `gridnd.py` (537 LOC) — `GridNDSubstrate` (N≥4)
- `continuous.py` (766 LOC) — `ContinuousSubstrate` base + `Continuous{1,2,3}DSubstrate`
- `continuousnd.py` (504 LOC) — `ContinuousNDSubstrate` (N≥4)
- `__init__.py` (31 LOC) — re-exports

**Confidence:** High for the inheritance pattern, action emission, boundary
handling, distance metrics, and encoding (read each subclass's `__init__`,
`apply_movement`, `compute_distance`, `get_default_actions`, and at least
one encoder per family). Medium for `_encode_full_grid` semantics in
non-2D substrates and POMDP semantics in 3D — I read Grid2D's full-grid
encoder in detail and only verified Grid3D/GridND distance + actions, not
their encoder bodies.

### Responsibility

A substrate is an abstract spatial container: it defines how agent
positions are represented (dimensionality, dtype), how they evolve under
movement deltas, how distance is computed, how the substrate is encoded
into observations, and which discrete actions it natively supports. The
substrate is explicitly described as **optional** — `AspatialSubstrate`
(`aspatial.py:9`) is a first-class substrate with `position_dim == 0` and
the pedagogical note that "the meters (bars) are the true universe"
(`aspatial.py:11-13`).

The hierarchy is a classic ABC + subclass pattern. `SpatialSubstrate`
(`base.py:12`) declares 11 abstract methods plus two abstract properties
(`position_dim`, `position_dtype`). Every concrete substrate implements
the same surface; the factory (`factory.py:15`) is the only construction
seam.

### Substrate catalog

| File | Class | `position_dim` | `position_dtype` | Boundary modes | Distance metrics | Default actions | POMDP support |
|---|---|---|---|---|---|---|---|
| `aspatial.py:9` | `AspatialSubstrate` | 0 | `torch.long` | n/a | always 0 | `[INTERACT]` (`aspatial.py:141-162`) | empty tensor (`aspatial.py:119-135`) |
| `grid2d.py:12` | `Grid2DSubstrate` | 2 | `torch.long` | clamp/wrap/bounce/sticky (`grid2d.py:100-133`) | manhattan/euclidean/chebyshev (`grid2d.py:147-157`) | 4 cardinal + 4 diagonal (if `enable_diagonals`) + `INTERACT` (`grid2d.py:159-303`) | 5×5 local window via `encode_partial_observation` (`grid2d.py:542-601`) |
| `grid3d.py:13` | `Grid3DSubstrate` | 3 | `torch.long` | clamp/wrap/bounce/sticky | manhattan/euclidean/chebyshev (`grid3d.py:132-139`) | 4 XY cardinal + 4 XY diagonals + 2 Z (`UP_Z`/`DOWN_Z`) + `INTERACT` (`grid3d.py:141-…`) | supported per CLAUDE.md when `vision_range ≤ 2` (not re-verified in source) |
| `gridnd.py:12` | `GridNDSubstrate` | N (4-100) | `torch.long` | clamp/wrap/bounce/sticky (`gridnd.py:82-89`, `gridnd.py:170-174`) | manhattan/euclidean/chebyshev (`gridnd.py:178-204`) | `2N` directional `DIM{i}_{NEG,POS}` + `INTERACT` (`gridnd.py:206-…`) | none |
| `continuous.py:13` | `ContinuousSubstrate` (base) | 1-3 | `torch.float32` (`continuous.py:35`) | clamp/wrap/bounce/sticky (`continuous.py:157-198`) | euclidean/manhattan/chebyshev (`continuous.py:200-213`) | none on base class (`continuous.py:391-399` raises) | none (`continuous.py:344-358` raises `NotImplementedError`) |
| `continuous.py:402` | `Continuous1DSubstrate` | 1 | float32 | inherited | inherited | `[LEFT, RIGHT, INTERACT]` (`continuous.py:429-474`) | none |
| `continuous.py:477` | `Continuous2DSubstrate` | 2 | float32 | inherited | inherited | discretised `MOVE_{dir_idx}_{mag_idx}` over `num_directions × (num_magnitudes−1)` + `INTERACT` (`continuous.py:508-627`) | none |
| `continuous.py:630` | `Continuous3DSubstrate` | 3 | float32 | inherited | inherited | 6 axis-aligned moves (`UP/DOWN/LEFT/RIGHT/UP_Z/DOWN_Z`) + `INTERACT` (`continuous.py:665-…`) | none |
| `continuousnd.py:12` | `ContinuousNDSubstrate` | N (4-100) | float32 | clamp/wrap/bounce/sticky (`continuousnd.py:82-89`, ~`continuousnd.py:170-222`) | euclidean/manhattan/chebyshev (`continuousnd.py:226-252`) | `2N` directional `DIM{i}_{NEG,POS}` + `INTERACT` (`continuousnd.py:382-…`) | inherited from continuous (none) |

### Key components

#### Base class — `SpatialSubstrate` (`base.py:12-323`)

ABC with abstract surface:

- **Properties:** `position_dim` (`base.py:32-43`), `position_dtype`
  (`base.py:45-60`); concrete `action_space_size` derived from
  `get_default_actions()` (`base.py:62-74`).
- **Action contract:** `get_default_actions()` (`base.py:76-104`)
  encodes the canonical ordering as a docstring contract — movement
  first, then `INTERACT` at position `-2`, then `WAIT` at position `-1`.
  Note: the actual substrates (e.g., `Grid2DSubstrate`, see
  `grid2d.py:285-301`) emit `INTERACT` as the **last** action and do not
  emit `WAIT` themselves — the comment at `grid2d.py:285` explicitly
  flags this: "INTERACT always present (WAIT is custom-only via
  actions.yaml)". The base-class docstring at `base.py:99-102` is
  **stale** relative to the implementations. WAIT exists at the
  `ActionConfig`/global-vocabulary layer, not at substrate level.
- **State manipulation:** `initialize_positions`, `apply_movement`,
  `compute_distance` (`base.py:106-159`).
- **Observation surface:** `encode_observation` + `get_observation_dim`
  (full obs, `base.py:161-193`), `normalize_positions` (always
  relative-to-[0,1], `base.py:195-218`), `encode_partial_observation`
  (POMDP window, `base.py:293-323`).
- **Affordance/action support:** `get_valid_neighbors` (`base.py:220-235`),
  `is_on_position` (`base.py:237-256`), `get_all_positions`
  (`base.py:258-270`), `get_capacity` (`base.py:272-291`).

The base docstring at `base.py:176-181` lists outdated
observation-dim numbers ("Grid2D (8×8, relative): 66"). The
implementation in `Grid2DSubstrate.get_observation_dim`
(`grid2d.py:467-484`) actually returns `width*height + {2,4,2}` for
`{relative, scaled, absolute}` — i.e., **66 only when 8×8 relative**.
The base-class docstring is not contractually wrong but is presented as
universal, which is misleading.

#### Factory — `SubstrateFactory.build()` (`factory.py:15-152`)

Static dispatcher keyed on `SubstrateConfig.type` ∈ {`"grid"`,
`"continuous"`, `"gridnd"`, `"continuousnd"`, `"aspatial"`}, with grid
further branched on `topology` ∈ {`"square"`, `"cubic"`} and continuous
further branched on `dimensions` ∈ {1, 2, 3}. Higher-dimensional grids
go through the `gridnd`/`continuousnd` types (factory does not collapse
to `GridND` for low N). The `device` parameter is currently **unused**
(`factory.py:31-33` documents this explicitly: "reserved for future
use") — substrates are device-agnostic and take device per-call.

#### Grid2DSubstrate — representative discrete pattern (`grid2d.py:12-605`)

- **Coordinate convention:** `[x, y]` with origin top-left, y increases
  downward (`grid2d.py:17-21`).
- **Movement:** Deltas come in as `float32` and are cast to `long`
  (`grid2d.py:97-98`); `wrap` uses modulo, `bounce` uses a fold-and-mirror
  scheme (`grid2d.py:111-125`), `sticky` reverts the affected axis to
  the prior value (`grid2d.py:127-133`).
- **Observation:** Three modes — `relative` (`grid2d.py:305-326`),
  `scaled` (adds width/height metadata, `grid2d.py:328-361`), `absolute`
  (raw int as float, `grid2d.py:363-377`). `_encode_full_grid`
  (`grid2d.py:379-431`) overlays an occupancy grid with values `{0:
  empty, 1: affordance, 2: agent}` and clamps agent+affordance overlap
  to `2.0`. The final encoding concatenates the flat grid with the
  position features (`grid2d.py:452-465`).
- **POMDP window:** `encode_partial_observation` builds a
  `(2r+1)×(2r+1)` local window centred on each agent, marking
  affordances within the window; out-of-bounds cells are zeros
  (`grid2d.py:542-601`). The implementation uses a Python loop over
  agents and affordances — **not vectorised**.

#### ContinuousSubstrate — representative continuous pattern (`continuous.py:13-399`)

- **Constructor invariants** (`continuous.py:60-117`): rejects
  `dimensions ∉ {1,2,3}`, rejects bounds whose range is smaller than
  `interaction_radius` (with a concrete diagnostic), warns when
  `interaction_radius < movement_delta` (agent may "step over"
  affordances), and **requires** an explicit `action_discretization`
  dict (no implicit defaults — `continuous.py:61-65`). This is faithful
  to the no-defaults principle in `CLAUDE.md`.
- **Movement:** Deltas are pre-scaled by `movement_delta`
  (`continuous.py:160`). Boundary modes are continuous analogues:
  `wrap` shifts to `[0, range_size)` then modulos; `bounce` folds into
  `[0, 2*range_size)` then mirrors the upper half (`continuous.py:157-198`).
- **Distance:** Three metrics, same families as discrete grids
  (`continuous.py:200-213`).
- **Interaction:** `is_on_position` is proximity-based (`distance ≤
  interaction_radius`, `continuous.py:215-221`); discrete grids require
  exact match (`grid2d.py:524-532`).
- **POMDP:** Explicitly disabled —
  `encode_partial_observation` raises `NotImplementedError` with the
  rationale "continuous spaces have infinite positions in any local
  region" (`continuous.py:344-358`).
- **Discretised actions** (`continuous.py:508-627`,
  `Continuous2DSubstrate`): generates
  `num_directions × (num_magnitudes − 1)` directional actions named
  `MOVE_<dir>_<mag>` (`continuous.py:591-606`), spanning angles
  `[0, 2π)` and magnitudes `[1/(M-1), …, 1.0]`. Actions are cached
  after first generation (`continuous.py:516-522`). There is a code
  smell at `continuous.py:583-585` — energy/hygiene/satiation scaling
  is computed and then discarded (assigned to `_`). The comment at
  `continuous.py:581-582` admits it is "a design placeholder".

#### AspatialSubstrate — degenerate case (`aspatial.py:9-162`)

Implements every abstract method as the empty/identity:
`initialize_positions` returns `[N, 0]`, `apply_movement` returns
unchanged, `compute_distance` returns zeros (`aspatial.py:54-61`),
`is_on_position` returns all-True (`aspatial.py:98-109`),
`encode_partial_observation` returns `[N, 0]` (`aspatial.py:119-135`).
Default actions are `[INTERACT]` only (`aspatial.py:141-162`) — no
`WAIT`, matching the actual convention rather than the base-class
docstring contract.

#### GridND/ContinuousND — N-dimensional generalisation

Both fan out movement to `2N` axis-aligned actions named `DIM{i}_NEG` /
`DIM{i}_POS` (`gridnd.py:206-…`, `continuousnd.py:382-…`); both warn at
`N ≥ 10` about action-space size (`gridnd.py:68-74`,
`continuousnd.py:82-88`); both cap at 100 dimensions. ContinuousND uses
the same boundary scheme as Continuous2D/3D but expressed over an
arbitrary bounds list. ContinuousND lacks `encode_partial_observation`
override and inherits the continuous "not supported" behaviour.

### Public API

The package re-exports the concrete substrates and the factory
(`substrate/__init__.py:20-30`):

```
SpatialSubstrate, Grid2DSubstrate, Grid3DSubstrate, GridNDSubstrate,
Continuous1DSubstrate, Continuous2DSubstrate, Continuous3DSubstrate,
ContinuousNDSubstrate, AspatialSubstrate, SubstrateFactory
```

Callers (`grep` confirmed):
- `townlet.environment.vectorized_env` (constructs via factory at
  `vectorized_env.py:149`; imports `ContinuousSubstrate` at `:28`)
- `townlet.universe.compilers.observation` (`observation.py:15`)
- `townlet.universe.compilers.actions` (`actions.py:14`)
- `townlet.environment.substrate_action_validator` (`substrate_action_validator.py:11`)
- `townlet.environment.action_builder` (`action_builder.py:9`,
  uses base class as a type)
- `townlet.demo.live_inference` (multiple imports for runtime
  introspection)

### Patterns observed

1. **ABC + factory + Pydantic config.** Configuration enters as
   `SubstrateConfig` (in `townlet.config.stratum_config` per
   `factory.py:5`), the factory dispatches on `config.type`/`topology`,
   and concrete substrates expose a uniform interface. Closed-set
   dispatch — no plugin/registry mechanism; adding a substrate requires
   editing the factory and `__init__.py`.

2. **Canonical action-ordering contract documented but partially
   honoured.** The base contract (`base.py:80-104`) demands
   `[movement…, INTERACT, WAIT]`. In practice, substrates emit
   `[movement…, INTERACT]` only; WAIT is added downstream via
   `actions.yaml`. The grid2d source comment (`grid2d.py:285-286`)
   makes this explicit. This is harmless but the base-class docstring
   is **stale**.

3. **Three encoding modes (`relative`/`scaled`/`absolute`) as a
   first-class enum-via-Literal.** Every substrate replicates the same
   three-branch encoding logic (grid2d:443-450, continuous:307-313,
   gridnd:~301-307, continuousnd:301-308). Duplicated rather than
   centralised — adding a fourth mode requires touching every substrate.

4. **No-defaults posture honoured in continuous code paths.**
   `ContinuousSubstrate.__init__` (`continuous.py:61-65`) refuses
   construction without explicit `action_discretization`; bounds and
   movement parameters have no defaults. Grids are looser
   (`Grid3DSubstrate.__init__` defaults `distance_metric="manhattan"`,
   `grid3d.py:49`, and `observation_encoding="relative"`,
   `grid3d.py:50`) — this contradicts the no-defaults rule for
   behavioural parameters but is shielded by Pydantic at the config
   layer.

5. **Vectorisation is uneven.** `apply_movement`,
   `compute_distance`, `initialize_positions`,
   `_encode_full_grid` (Grid2D), and `is_on_position` are tensor-native
   and batched. `encode_partial_observation` in Grid2D
   (`grid2d.py:580-598`) uses a Python double loop over agents and
   affordances — likely a bottleneck for large `num_agents` at L2.

6. **Continuous substrates classify three pieces of state as
   "discrete-only":** `get_all_positions` raises, `get_capacity`
   returns `None`, `get_valid_neighbors` raises. The
   `supports_enumerable_positions` method (`grid2d.py:603-605`,
   `continuous.py:387-389`) gives callers a clean predicate.

### Concerns

- **Stale base-class contract.** `SpatialSubstrate.get_default_actions`
  docstring (`base.py:80-104`) describes a `[…, INTERACT, WAIT]`
  ordering, but no concrete substrate emits WAIT. Either WAIT should
  be reintroduced at substrate level, or the docstring should be
  rewritten. Per the CLAUDE.md "delete antipatterns" rule, the
  divergence should be reconciled now rather than carried.

- **Stale observation-dim numbers in base docstring.**
  `base.py:176-181` and `:185-192` quote specific dims ("Grid2D (8×8,
  relative): 66" etc.) — these are valid only at one grid size and at
  one encoding mode. Misleading for new readers.

- **Dead computation in `_generate_discretized_actions`.**
  `continuous.py:583-585` computes magnitude-scaled costs into `_` and
  drops them. The comment at `:581-582` calls this a "design
  placeholder". This is exactly the kind of dead code that CLAUDE.md
  says to delete pre-release.

- **Grid2D POMDP path is non-vectorised.** Double Python loop at
  `grid2d.py:581-598`. Acceptable for the demonstrated 8×8 / few-agent
  L2 config but will not scale.

- **Defaults on Grid3D.** `Grid3DSubstrate.__init__`
  (`grid3d.py:49-50`) defaults both `distance_metric` and
  `observation_encoding`. The Pydantic substrate config is
  presumably the gate, but the constructor itself contradicts the
  no-defaults principle.

- **Aspatial `compute_distance` ignores `pos2`.** `aspatial.py:54-61`
  always returns zeros. Mathematically appropriate for the substrate,
  but the unused parameter could be marked or asserted-empty to catch
  miscalls.

- **`_encode_full_grid` exists on `Grid2DSubstrate` and is part of
  `encode_observation`** (`grid2d.py:452-465`). It is not declared on
  the base class, so other substrates do not implement it. This means
  `encode_observation` semantics diverge across substrates: Grid2D
  emits `width*height + position_dims`; Grid3D's analogue (not read in
  this pass) and ContinuousSubstrate emit only position dims
  (`continuous.py:294-314`, returns position-only encoding). This is
  a real semantic asymmetry hidden behind a common method name.

---

## Part B: World Expression DSL

**Location:** `src/townlet/world/` (3,131 LOC: 11 files = 9 source `.py`
+ `py.typed` markers; `wc -l` totals 3,141 for source files alone)

**Files:**
- `__init__.py` (98 LOC) — public re-exports
- `expression/__init__.py` (62 LOC) — sub-package re-exports
- `expression/ast_nodes.py` (309 LOC) — dataclasses + Visitor interface
- `expression/parser.py` (251 LOC) — pyparsing grammar
- `expression/evaluator.py` (145 LOC) — tensor-backed evaluator
- `expression/type_checker.py` (425 LOC) — bottom-up type inference
- `expression/functions.py` (1,186 LOC) — function registry (signatures
  + eval bodies, 48 built-ins)
- `expression/context.py` (310 LOC) — runtime `ExecutionContext` with
  reference traversal
- `expression/history.py` (194 LOC) — `TemporalHistory` ring buffers for
  temporal operators
- `types/__init__.py` (23 LOC) — `Type` protocol re-exports
- `types/primitive.py` (128 LOC) — `ScalarType`, `BoolType`, `Vec{2,3,4}Type`

**Confidence:** High for the grammar shape, evaluator semantics, AST
node inventory, context resolution rules, and temporal history
mechanics — read every file in full or in detail. Medium-high for the
function catalog (48 registrations confirmed; per-spec arity verified
by `grep`, but only a representative sample of `eval_fn` bodies was
read).

### Responsibility

A self-contained expression language used as the substrate for
declarative configuration across HAMLET. Per the docstring
(`world/__init__.py:1-8`), it is consumed by VFS computed fields,
the Effects system commands, the Items system actions, and dynamic
state computations. Verified via grep:

- `effects/compiler.py:8-9` — parser + type-checker (compile-time)
- `effects/executor.py:11-12` — context + evaluator (runtime)
- `items/manager.py:25-26` — same runtime pair
- `universe/compilers/vfs.py:16-17` — parser + type-checker for VFS
- `universe/compiler.py:46` — `TypeCheckError` for diagnostics
- `vfs/{evaluator,generalisation,history,profiles,vtc}.py` — various
  AST-walking integrations

The expression layer is one of the central seams between YAML and
the GPU runtime. The end-to-end pipeline is
**source → parser → AST → type-checker → evaluator → tensor**, with a
side-channel `TemporalHistory` for temporal operators.

### Grammar overview

`ExpressionParser._build_grammar` (`parser.py:55-236`) defines the
grammar with pyparsing, with packrat caching enabled
(`parser.py:35`).

**Productions** (top-down):

- `expression` → `expression_with_ops` (operator-precedence root,
  `parser.py:216-232`)
- `primary` → `(constant | function_call | if_expression |
  path_or_variable)` then zero or more postfix `[expr]` for index
  access (`parser.py:136-150`)
- `constant` → `bool_literal | numeric_literal | string_literal`
  (`parser.py:84`)
- `bool_literal` → `"true"` | `"false"` (`parser.py:62-65`)
- `numeric_literal` → strict float regex `[+-]?(\d+\.\d*([eE]…)?|\d+[eE]…)`
  **then** `signed_integer` (`parser.py:71-76`). The order plus the
  strict float regex is load-bearing: it ensures `"42"` parses as `int`
  (the comment at `parser.py:68-70` explains pyparsing's `fnumber`
  greedily eats integers, which would break type-checking for array
  indices).
- `string_literal` → double- or single-quoted, `\` escape
  (`parser.py:79-81`)
- `function_call` → `identifier "(" expr ("," expr)* ")"` —
  attempted *before* path_or_variable (`parser.py:100-102`)
- `path_or_variable` → `identifier ("." identifier)*`; if single
  segment and not a keyword, becomes `Variable`, else `PathAccess`
  (`parser.py:104-114`)
- `if_expression` → `"if" expr "then" expr "else" expr`
  (`parser.py:117-128`)
- `index_access` → postfix `"[" expr "]"+` over primary, building
  nested `IndexAccess` left-to-right (`parser.py:132-147`)

**Operator precedence** (`parser.py:216-232`, lowest first by reading
order is the convention of `infixNotation`):

| Level | Operators | Associativity | Notes |
|---|---|---|---|
| Unary | `-`, `not` | right | `parser.py:219` |
| Power | `**` | **right** | Custom `make_right_binop` so `a**b**c → a**(b**c)` (`parser.py:194-213, 220`) |
| Multiplicative | `*`, `/`, `%` | left | `parser.py:221` |
| Additive | `+`, `-` | left | `parser.py:222` |
| Comparison | `==`, `!=`, `<=`, `>=`, `<`, `>` | left | `parser.py:223-228` |
| Logical AND | `and` | left | `parser.py:229` |
| Logical OR | `or` | left | `parser.py:230` |

**Reserved keywords** that cannot be variable names: `true`, `false`,
`and`, `or`, `not`, `if`, `then`, `else` (`parser.py:87`,
enforced at `parser.py:109-110`).

**Not parseable from source:** `Switch` and `Reduce` AST nodes
(`ast_nodes.py:274-309`) are declared but have **no production** in
`parser.py` (verified by `grep`, no `switch` / `reduce` tokens). They
must be constructed programmatically — presumably by higher-level
compilers (effects/items) that translate YAML-block syntax directly to
these nodes. The `Reduce.target` field (`ast_nodes.py:306`) is
explicitly described as "for the command layer".

### AST and evaluator

#### AST shape (`ast_nodes.py:1-309`)

- `ASTNode` base dataclass (`@dataclass(frozen=True, kw_only=True)`,
  `ast_nodes.py:43-69`) carries optional `line`/`column`/`type_annotation`
  metadata, declares `accept(visitor)` as the dispatch method.
- `ASTVisitor` (`ast_nodes.py:72-116`) declares
  `visit_{constant, variable, path_access, binary_op, unary_op,
  function_call, if_then_else, index_access, switch, reduce}`.
- Concrete nodes are frozen dataclasses with positional fields:
  - **Leaves:** `Constant(value)` (`:119-133`), `Variable(name)`
    (`:136-151`), `PathAccess(segments)` (`:154-170`)
  - **Operators:** `BinaryOp(left, op, right)` (`:173-190`),
    `UnaryOp(op, operand)` (`:193-208`); `OperatorType` is an enum
    listing 16 operators (`:13-40`).
  - **Compound:** `FunctionCall(function_name, arguments)`
    (`:211-229`), `IfThenElse(condition, true_branch, false_branch)`
    (`:232-250`), `IndexAccess(base, index)` (`:253-271`)
  - **Command-layer (parser-inaccessible):** `Switch(switch_expr,
    cases, default)` (`:274-288`), `Reduce(collection, iterator, init,
    body, target)` (`:291-309`)

Strategy is **textbook Visitor**: each node implements `accept(v) →
v.visit_<kind>(self)`. The same AST is walked by `Evaluator`,
`TypeChecker`, and a `vfs.history` walker (`vfs/history.py`,
imports `ASTVisitor`).

#### Evaluator (`evaluator.py:1-145`)

GPU-native, tree-walking, single-pass — no compilation to bytecode,
no DAG common-subexpression elimination, no caching across
invocations.

- `Evaluator(context: ExecutionContext)`, single entry point
  `evaluate(node) → torch.Tensor` (`evaluator.py:19-27`).
- `visit_constant` lifts Python values to `torch.tensor` on the
  context device; strings pass through as Python `str`
  (`evaluator.py:29-33`) — note the bogus `# type: ignore` because the
  return type is widened to `torch.Tensor` but strings can leak.
- `visit_binary_op` (`evaluator.py:44-80`): all 16 operators are
  delegated to torch tensor operators (`+`, `-`, ..., `&`, `|`).
  Logical AND/OR use bitwise `&`/`|` (`:75-78`) — relies on the
  type-checker having pre-validated operand dtypes are `bool` tensors.
- `visit_unary_op` (`evaluator.py:82-93`): negation `-`, logical not
  via `~`.
- `visit_if_then_else` (`evaluator.py:109-128`): **vectorised** via
  `torch.where`; condition, true_branch, and false_branch are all
  evaluated unconditionally — no short-circuiting. This is critical
  to understanding behaviour: side-effect-free expressions are fine,
  but expressions that read from references with invalid indices will
  evaluate both branches.
- `visit_function_call` (`evaluator.py:95-107`): dispatches through
  `FUNCTION_SPECS[name].eval_fn(args, context, arg_nodes)`. The
  `arg_nodes` parameter (the raw AST args) is passed in addition to
  the evaluated `args` — temporal operators (lag/ema/etc.) need the
  un-evaluated path to look up the history key.
- `visit_index_access` (`evaluator.py:130-145`): tensor indexing
  `base[index_long]`.
- **No visitor methods for `Switch` / `Reduce`.** Falls back to the
  base `ASTVisitor.visit_*` which raises `NotImplementedError`.

#### Type checker (`type_checker.py:1-425`)

Bottom-up inference, schema-driven. The schema is a flat
`dict[str, str]` mapping dotted paths to type names like `"float"`,
`"int"`, `"bool"`, `"str"`, `"agent_ref"`, `"item_ref"`.

- **Promotion rule:** arithmetic of `int+int → int`, anything with
  `float` → `float` (`:280-282`).
- **Comparison rule:** equality is permissive (matching types or
  numeric-pair); ordering is numeric-only (`:293-307`).
- **Logical rule:** strict bool-only (`:310-315`).
- **If-then-else:** condition must be `"bool"`, branches must
  unify exactly (`:375-406`).
- **Function dispatch:** delegates to
  `FUNCTION_SPECS[name].validate_args(...) → return_type(...)`
  (`:358-373`).
- **Reference traversal:** `_resolve_reference_path` (`:151-212`) is
  a recursive walker for the `vfs.<ref>.<vfs|bar>.<…>` family. It
  handles `agent_ref` (hops into `target.*`) and `item_ref` (hops into
  `self.*`), letting a path like `vfs.partner.vfs.bar.energy` resolve
  by chaining through the schema. The `ref` segment is stripped at
  `:157` so paths can be written with or without the explicit `ref`
  marker — this mirrors the runtime `ExecutionContext.get`
  (`context.py:53`).
- **Index access:** index must be `int`; element type defaults to
  `"float"` for downstream arithmetic (`:408-425`). Container element
  type is **not tracked** — this is a real type-system limitation.
- `_lookup_ref_type`, `_fallback_target_lookup`, `_fallback_item_lookup`
  (`:214-238`) are helpers, with the latter two appearing **unused**
  by `_resolve_reference_path` after a refactor (the new recursive
  `resolve` closure at `:170-212` supersedes them). Dead code per
  CLAUDE.md guidance.

### Built-in functions catalog

48 functions registered via `FUNCTION_SPECS` (counted by grepping
`^\s+name="…"` in `functions.py`; one registry shared by both
type-checker and evaluator at `type_checker.py:360` and
`evaluator.py:100`).

The `FunctionSpec` dataclass (`functions.py:19-26`) bundles `name`,
`min_args`, `max_args` (None = variadic), `return_type` (callable on
arg-type list), `validate_args` (callable on arg-type list, raises),
and `eval_fn` (callable on evaluated tensors + context + raw AST
args).

#### Arithmetic / math (10)

| Name | Arity | Returns | Notes |
|---|---|---|---|
| `max` | ≥1 | numeric | element-wise across tensors (`:272`) |
| `min` | ≥1 | numeric | (`:322`) |
| `abs` | 1 | numeric | (`:333`) |
| `clamp` | 3 | numeric | `(value, lo, hi)` (`:344`) |
| `clamp01` | 1 | numeric | shortcut for `clamp(x, 0, 1)` (`:357`) |
| `sigmoid` | 1 | float | `torch.sigmoid` (`:370`) |
| `tanh` | 1 | float | `torch.tanh` (`:383`) |
| `smoothstep` | 3 | float | cubic Hermite interp (`:396-407`) |
| `mean` | ≥1 | float | stacks then `torch.mean` (`:411`) |
| `variance` | ≥1 | float | (`:424`) |

#### Reductions (11)

| Name | Arity | Returns | Notes |
|---|---|---|---|
| `sum` | ≥1 | numeric | (`:437`) |
| `product` | ≥1 | numeric | (`:450`) |
| `normalize` | ≥1 | float | (`:463`) |
| `min_all` | ≥1 | numeric | (`:478`) |
| `max_all` | ≥1 | numeric | (`:491`) |
| `count_where` | ≥1 | int | (`:504`) |
| `argmin` | ≥1 | int | (`:517`) |
| `argmax` | ≥1 | int | (`:530`) |
| `threshold` | 2 | bool | (`:543`) |
| `all` | ≥1 | bool | (`:558`, body `_eval_all` at `:134`) |
| `any` | ≥1 | bool | (`:569`, body `_eval_any` at `:138`) |

#### Masking / tensor ops (5)

| Name | Arity | Returns | Notes |
|---|---|---|---|
| `where` | 3 | promoted | `torch.where(bool, a, b)` (`:580`) |
| `masked_add` | 3 | numeric | `_eval_masked_add` (`:146`, `:594`) |
| `masked_set` | 3 | numeric | `_eval_masked_set` (`:151`, `:609`) |
| `gather` | 2 | numeric | tensor indexing (`:156`, `:624`) |
| `scatter` | 3 | numeric | (`:164`, `:638`) |
| `one_hot` | 2 | float | (`:174`, `:653`) |

(That's actually 6 — listed as tensor ops.)

#### Stochastic / noise (4)

`perlin_noise` (`:287`), `simplex_noise` (`:304`), `normal_dist`
(`:670`), `uniform` (`:687`).

#### Temporal operators (10)

All require `ExecutionContext.history` (a `TemporalHistory`,
`context.py:37`); the spec key is built from the first AST argument by
`_temporal_key` (`functions.py:184-191`):

| Name | Arity | Notes |
|---|---|---|
| `time_in_window` | varies | (`:780`) |
| `phase_sin` | (`:794`) | trig of cycle phase |
| `phase_cos` | (`:808`) | |
| `elapsed_ticks` | (`:822`) | |
| `lag` | (`:835`) | look back `n` ticks via ring buffer (`history.py:74-95`) |
| `delta` | (`:850`) | first-difference |
| `moving_average` | (`:879`) | over a window (`history.py:97-132`) |
| `ema` | (`:897`) | exponential moving average (`history.py:134-146`) |
| `rate_of_change` | (`:915`) | `(current − lagged)/window` (`history.py:148-152`) |
| `rising_edge` | (`:933`) | (`history.py:154-166`) |
| `falling_edge` | (`:949`) | |

The `TemporalHistory` (`history.py:19-194`) maintains per-key ring
buffers up to `MAX_WINDOW_SIZE = 256` (`history.py:16`,
enforced at `:39-40`); each buffer is `(batch, window, *value_shape)`;
warm-length is tracked per agent so partial windows don't read zeros
spuriously (`:48-49, :92-94`). `reset()` clears everything; `to(device)`
migrates all buffers in place.

#### Spatial / domain (7)

| Name | Arity | Notes |
|---|---|---|
| `distance` | varies | (`:1044`, body `:995`) |
| `manhattan_distance` | (`:1060`, body `:999`) | |
| `within_radius` | (`:1074`, body `:1003`) | |
| `nearest` | (`:1089`, body `:1009`) | |
| `distance_to_affordance` | (`:1105`) | resolves affordance position via context |
| `in_range` | (`:1129`) | |
| `direction_to_affordance` | (`:1163`) | |

These are HAMLET-domain functions — they read from
`context.affordance_positions` / `agent_positions` and bake the
spatial semantics directly. Distance metric is selected by an
optional final string literal in some signatures (validated via
`_ensure_optional_string_arg` at `functions.py:69-71`).

### Execution context (`context.py:13-310`)

`ExecutionContext` is a dataclass with 16 fields holding all runtime
state the evaluator may touch: `bars`, `vfs`, `affordances`, `temporal`
dicts; optional `affordance_positions`, `agent_positions`, `device`,
`vfs_types`, `num_agents`, `self_indices`, `target_indices`,
`item_vfs`, `item_profile_map`, `item_index_to_profile`, `history`,
`step`.

The `get(path)` method (`:40-73`) is the runtime mirror of the type
checker's `visit_path_access`. Path roots:
- `bar.<name>` (`_read_bar`, `:203-206`)
- `affordance.<name>.<field>...` (`_read_affordance`, `:208-231`),
  supports `Mapping` lookup and `getattr` traversal — affordance
  state need not be a flat dict.
- `temporal.<name>` (`_read_temporal`, `:233-236`)
- `global.vfs.<…>` (resolves via `_resolve_vfs_chain` with
  `scope="global"`, `:65-68`)
- `vfs.<…>` / `self.<…>` / `target.<…>` (`_resolve_entity_path`,
  `:75-98`)

Reference traversal at runtime mirrors the type-checker's
`_resolve_reference_path` but with valid-mask handling for negative
or out-of-bounds indices: `_reference_valid_mask` (`:289-293`)
produces a boolean mask, `_mask_reference_output` (`:295-302`) zeros
out invalid lanes after gather. Item references additionally consult
`item_profile_map` to find the column in `item_vfs`
(`:171-201`).

### Type system (`world/types/primitive.py:1-128`)

A small `Protocol`-based validator system: `Type` (`:13-28`), and
implementations `ScalarType`, `BoolType`, `Vec2Type`, `Vec3Type`,
`Vec4Type` (`:31-128`). Each implements `validate(tensor) → bool`
checking dtype and shape. `ScalarType` requires `float32` + 1D;
`BoolType` requires `bool` + 1D; `Vec*Type` require `float32` + 2D
with the trailing dimension matching.

**Caveat:** Despite being re-exported from `world/__init__.py` and
listed in the public API, `grep` for `from townlet.world.types` returns
**only the package's own `__init__.py`** (`/types/__init__.py:7`).
These validators do not appear to be used in `expression/`,
`type_checker.py` (which uses string-based type names), or any external
consumer. They may be vestigial scaffolding from an earlier design or
reserved for a future runtime-validation pass.

The type checker (`type_checker.py`) uses *string* type names
("int"/"float"/"bool"/"str"/"agent_ref"/"item_ref"/etc.) entirely
disjoint from the `Type` protocol. The two type systems are not
integrated.

### Patterns observed

1. **Visitor pattern, faithfully implemented.** All AST traversal goes
   through `accept(visitor)`. Three known visitors today: `Evaluator`,
   `TypeChecker`, and `vfs.history`'s walker (`vfs/history.py:6`).

2. **Shared function registry.** `FUNCTION_SPECS` is the single source
   of truth for both type signature and evaluation; signatures cannot
   drift from implementations (`functions.py:19-27`). Adding a built-in
   means a single `_register(FunctionSpec(...))` call. The pattern is
   clean and extensible.

3. **Pyparsing grammar with packrat caching** (`parser.py:35`) — chosen
   for ergonomics over speed. The strict float regex
   (`parser.py:71-73`) is a deliberate workaround for
   `pyparsing.fnumber`'s integer-eating behaviour, with a comment
   explaining why.

4. **Two-phase pipeline.** Compile-time path: `ExpressionParser →
   TypeChecker → schema-validated AST`. Runtime path:
   `AST → ExecutionContext → Evaluator → tensor`. The
   `effects/compiler.py` (`compiler.py:8-9`) and
   `effects/executor.py` (`executor.py:11-12`) callers confirm this
   split. Type errors surface at compile time (DAC / VFS compilation),
   never at evaluation.

5. **Eager evaluation, vectorised via `torch.where`.** No
   short-circuit semantics for `and`/`or` (uses `&`/`|`) or `if/then/else`
   (uses `torch.where`). All branches are always evaluated. This is
   appropriate for GPU dispatch but is a behavioural footgun if
   expressions rely on `if cond then safe_path else dangerous_path`.

6. **Reference traversal duplicated** in `type_checker.py` and
   `context.py`. The traversal rules (`ref` stripping, `agent_ref` →
   `target.*` hop, `item_ref` → `self.*` hop) are reimplemented at
   compile time and at runtime. A single shared resolver would
   reduce risk of drift.

7. **Dormant AST nodes.** `Switch` and `Reduce` exist in `ast_nodes.py`
   but cannot be parsed and cannot be evaluated by `Evaluator`.
   Presumably constructed directly by the command-layer compilers
   (Effects/Items) and walked by a different visitor. This is **not
   visible from `world/expression/`** alone; would need a parallel
   review of the command-layer code to confirm.

### Concerns

- **Two disjoint type systems.** `world/types/primitive.py` defines
  protocol-based `Type` validators that are not consumed by
  `type_checker.py` or anything else in `expression/`. The type
  checker operates on string type names. Either the protocol types
  should be deleted (per CLAUDE.md) or wired in; carrying both is
  technical debt.

- **String type-checker tags are stringly-typed.** "int", "float",
  "bool", "str", "agent_ref", "item_ref" are scattered as bare
  strings. An enum (or even a `Literal` alias) would be safer and
  greppable.

- **Dead helper methods in `TypeChecker`.** `_lookup_ref_type`,
  `_fallback_target_lookup`, `_fallback_item_lookup`
  (`type_checker.py:214-238`) appear unused after the recursive
  `resolve` closure subsumed them. Should be deleted.

- **Eager branch evaluation has no documented warning.** `IfThenElse`
  semantics (`evaluator.py:109-128`) evaluate both branches
  unconditionally. Authors writing
  `if has_target then target.bar.energy else 0.0` will get reference
  lookups even when `has_target` is false; `_mask_reference_output`
  hides errors by zeroing-out invalid lanes (`context.py:295-302`)
  but performance and side-effect implications are non-obvious.

- **`Switch` / `Reduce` are unparseable** and the docstring on
  `Reduce.target` (`ast_nodes.py:306`) gestures at "the command layer".
  If these nodes are exclusively a command-layer concern, they
  arguably belong outside `expression/ast_nodes.py`. As they stand,
  reading `expression/` in isolation gives an incomplete picture.

- **`functions.py` is 1,186 LOC of mostly-mechanical registrations.**
  Each `FunctionSpec` is ~10-15 lines of lambda-heavy boilerplate.
  Splitting into a few thematic submodules (`functions/arithmetic.py`,
  `functions/temporal.py`, `functions/spatial.py`) would improve
  navigability without changing semantics.

- **`_eval_one_hot` requires `class_count` to be a scalar tensor with
  `numel() == 1`** (`functions.py:175-178`) but the type checker only
  knows it's an int — there's no compile-time guarantee. A
  scalar-typed function-arg category in the schema would catch this.

- **Logical `and`/`or` use bitwise `&`/`|`** (`evaluator.py:75-78`).
  This is correct only when both operands are bool tensors of
  matching shape. The type checker enforces bool operands
  (`type_checker.py:310-315`) but not shape; a non-broadcastable
  shape mismatch is a runtime tensor error rather than a
  type-system message.

- **No source-position propagation from pyparsing.** The
  `ASTNode.line` / `column` fields exist (`ast_nodes.py:53-54`) but
  the parser never populates them — every `setParseAction` callable
  constructs the node with positional args only. Errors surface
  without source position, which complicates user-facing diagnostics
  in DAC / VFS YAML.

---

## Cross-system dependencies (Substrate + World)

These two subsystems share a directory tree but are otherwise
**decoupled**.

### Inbound — substrate

Imports of `townlet.substrate.*` (from `grep`):

- `townlet.environment.vectorized_env` (factory build,
  `vectorized_env.py:149`; type-import of `ContinuousSubstrate` at `:28`)
- `townlet.universe.compilers.observation` (`observation.py:15`)
- `townlet.universe.compilers.actions` (`actions.py:14`)
- `townlet.environment.substrate_action_validator` (`:11`)
- `townlet.environment.action_builder` (`:9`)
- `townlet.demo.live_inference` (multiple, runtime introspection)

### Inbound — world / expression

Imports of `townlet.world.*` or `townlet.world.expression.*`:

- `townlet.effects.{compiler,executor}` (entire pipeline)
- `townlet.items.manager` (runtime evaluation)
- `townlet.universe.compiler` (TypeCheckError import)
- `townlet.universe.compilers.vfs` (parser + type-checker)
- `townlet.universe.compiled` (parser, lazy import at `:760`, `:906`)
- `townlet.vfs.{evaluator, generalisation, history, profiles, vtc}`
  (every module reads the AST + context)

### Outbound

- **Substrate:** depends on `torch` and on
  `townlet.environment.action_config.ActionConfig` (`base.py:9`,
  `grid2d.py:7`, etc.) and `townlet.environment.affordance_layout`
  (`grid2d.py:8`, `grid3d.py:7`). Configuration types live in
  `townlet.config.stratum_config` (`factory.py:5`).
- **World:** depends on `torch`, `pyparsing` (parser only,
  `parser.py:5-19`), and within-package only. No outbound dependency
  on `substrate`, environment, universe, or VFS — the DSL is the
  leaf of its layer.

### Coupling note

`base.py:9` uses a `TYPE_CHECKING` import of `ActionConfig` to avoid a
hard cycle with `townlet.environment.action_config`. Concrete
substrates (e.g., `grid2d.py:7`) take the unconditional import,
because their `get_default_actions` constructs `ActionConfig`
instances. The substrate package therefore sits **below**
`townlet.environment.action_config` in the import graph but above
`townlet.config.stratum_config`.

---

## Open questions

1. **Are `Switch` and `Reduce` actually constructed anywhere?** I
   confirmed they're not parsed and have no `visit_*` implementation in
   `Evaluator` or `TypeChecker`. A grep across `townlet/` for
   `Switch(` / `Reduce(` would say definitively whether they're live
   nodes built by command-layer compilers or stranded scaffolding.

2. **What populates `ASTNode.line` / `column`?** The parser doesn't.
   Are higher-level compilers (YAML loaders) supposed to thread
   source positions in? If yes, where? If no, the fields should be
   removed.

3. **Is `world/types/primitive.py` reachable?** Public-API exports
   suggest yes; grep finds no consumers. Either it's an architectural
   placeholder for future runtime validation, or it's dead.

4. **Why does `Grid3DSubstrate.__init__` default `distance_metric`
   and `observation_encoding`** (`grid3d.py:49-50`) when `Grid2DSubstrate`
   (`grid2d.py:39-40`) defaults `observation_encoding` but requires
   `distance_metric`, and `ContinuousSubstrate` requires both? The
   no-defaults principle is unevenly applied across the substrate
   family.

5. **Is the `_encode_full_grid` semantics intentionally asymmetric
   across substrates?** Grid2D's `encode_observation`
   (`grid2d.py:452-465`) concatenates the full grid with position
   features. `ContinuousSubstrate.encode_observation`
   (`continuous.py:294-314`) emits only position features.
   `AspatialSubstrate.encode_observation` emits an empty tensor. The
   downstream observation builder (in `universe/compilers/observation.py`,
   not read in this pass) presumably depends on the substrate identity
   to know what dimensions it's getting. A consistent contract would
   help.

6. **Is the duplication of reference-traversal logic between
   `type_checker.py` (`_resolve_reference_path`, lines 151-212) and
   `context.py` (`_resolve_entity_path` / `_resolve_vfs_chain`, lines
   75-201) intentional?** Compile-time and runtime walkers naturally
   diverge slightly (the runtime has indices, the type-checker has
   types), but the segment-stripping and ref-hopping rules are
   logically the same and could share a helper.
