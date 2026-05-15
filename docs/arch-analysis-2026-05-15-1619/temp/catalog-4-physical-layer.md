## Physical Layer (substrate + world + items)

**Location:** `src/townlet/substrate/`, `src/townlet/world/`, `src/townlet/items/`

**Responsibility:** Provides spatial positioning abstractions (Grid2D/3D/ND, Continuous, Aspatial), expression evaluation for dynamic configuration (on_pickup/on_use/on_drop Effects), and inventory + item-instance lifecycle management.

**Internal Structure:**

- **substrate/** — Substrate type hierarchy (8 concrete types): SpatialSubstrate protocol, Grid2D/Grid3D/GridND, Continuous1D/2D/3D/ND, Aspatial
- **world/** — Expression language runtime: type system (ScalarType, BoolType, Vec2/3Type), AST nodes, parser, type checker, evaluator; used to execute variable_reference.yaml expressions in Effects
- **items/** — Inventory slots [batch, max_items], ItemInstance dataclass (position, vfs_index, exclusive, holder_agent_ids), action handlers for on_pickup/on_use/on_drop

**Substrate Hierarchy:**

```
SpatialSubstrate (abstract protocol)
├── Grid2DSubstrate (8×8 to N×N square grids, position_dim=2)
├── Grid3DSubstrate (cubic grids, position_dim=3)
├── GridNDSubstrate (n-dimensional grids, position_dim=N)
├── Continuous1DSubstrate (1D bounded interval, position_dim=1)
├── Continuous2DSubstrate (2D rectangle, position_dim=2)
├── Continuous3DSubstrate (3D box, position_dim=3)
├── ContinuousNDSubstrate (n-dimensional continuous, position_dim=N)
└── AspatialSubstrate (no positioning, position_dim=0, reveal: "meters are the true universe")
```

**Boundary Modes** (all grid types): `clamp` (hard walls), `wrap` (toroidal), `bounce` (elastic reflection), `sticky` (stay-in-place)

**Distance Metrics** (all types): `manhattan`, `euclidean`, `chebyshev`; Aspatial always returns zero distance

**World / Expression System:**

The expression evaluator (Evaluator.evaluate()) is the runtime interpreter for variable_reference.yaml constraint expressions. It:
- Parses constraint DSL (e.g., `bar.energy > 50 && vfs.is_day`) into AST via ExpressionParser
- Type-checks at compile time via TypeChecker (ScalarType, BoolType, Vec2/3Type validators)
- Evaluates on GPU tensors at runtime via Visitor pattern (ExecutionContext provides bars/vfs/affordances/temporal)

**Integration with VFS:** ExecutionContext.get(path) resolves dotted paths ("bar.energy", "vfs.is_night", "affordance_positions.water") — used by Effects compiler to bind constraint expressions and by CommandExecutor to evaluate on_pickup/on_use/on_drop Effect commands.

**Items / Inventory:**

- **InventoryState**: Fixed-size per-agent inventory [batch, max_items], slots tensor (instance IDs, -1 = empty), items dict for metadata lookup
- **ItemInstance**: Runtime state—position, vfs_index (into item_vfs tensor), exclusive flag, holder_agent_ids (supports multi-holder items), lifecycle timers (spawn_tick, duration_remaining)
- **ItemActionHandler**: Dispatches on_pickup/on_use/on_drop via CommandExecutor, evaluates Effects in execution context with item VFS index for self-modification

**Dependencies:**

- **Inbound (to Physical Layer):**
  - `environment/` calls SubstrateFactory.build() to instantiate substrate from SubstrateConfig; reads substrate.position_dim, substrate.position_dtype for tensor shape validation; calls substrate.get_default_actions() to compose action space (ACTION SPACE CONTRACT: Movement[0:N] + INTERACT[-2] + WAIT[-1])
  - `environment/action_builder.py` composes substrate default actions with custom/affordance actions
  - `vectorized_env.py` (lines 185–310) validates substrate compatibility with partial_observability, initializes positions, encodes observations
  - `effects/` uses world.expression (Evaluator, Parser, TypeChecker) to compile and execute Effects (on_pickup/on_use/on_drop)
  - `vfs/` evaluator binds world.expression.ExecutionContext for constraint evaluation
  
- **Outbound (from Physical Layer):**
  - substrate → config/stratum_config (SubstrateConfig DTO read-only)
  - world.expression → effects/executor (CommandExecutor uses Evaluator)
  - items → environment/vectorized_env, effects/executor
  - No circular dependencies; clean layering

**Patterns Observed:**

1. **Protocol/Strategy:** SpatialSubstrate abstract base, concrete implementations override boundary/distance behavior
2. **Visitor:** AST evaluation (Visitor pattern for expressions)
3. **Factory:** SubstrateFactory.build() centralizes substrate instantiation
4. **Dataclass + GPU Tensors:** ItemInstance (Python dataclass) + InventoryState (GPU tensor slots)
5. **Execution Context:** ExecutionContext provides scope for expression evaluation (bars/vfs/affordances/temporal, position context)

**Concerns:**

- **State Leakage:** ItemInstance.position can be tuple[int,...] or tuple[float,...] (dual typing, lines 23); position mismatch if substrate type changes at runtime without updating items
- **Aspatial Default Actions:** AspatialSubstrate.get_default_actions() (lines 141–162) returns only [INTERACT] (1 action), not [INTERACT, WAIT] as base class docstring implies (line 92: "WAIT (last position)"). Missing WAIT action may break downstream action indexing
- **Half-Implemented Vision Range:** Grid3D supports encode_partial_observation() but vectorized_env.py (lines 290, 302–308) rejects 3D POMDP if observation_encoding != 'relative'. Continuous substrates also unsupported (line 262). POMDP practically limited to Grid2D with vision_range ≤ 2
- **Continuous Observation Encoding:** Config allows observation_encoding={relative,scaled,absolute} (grid2d.py:40) but vectorized_env enforces 'relative' for POMDP (line 306), creating silent config error if users specify otherwise
- **Expression Type Mismatch Risk:** world.expression.TypeChecker validates at compile time; runtime ExecutionContext.get() can return mismatched types if VFS/bars not initialized correctly (no runtime type guard in Evaluator.visit_*)

**Confidence:** **High** — substrate hierarchy is complete, factory pattern well-established, expression system cleanly integrated. Concerns are known limitations (POMDP on 3D/Continuous) and soft type safety (runtime type checking absent), not missing functionality.
