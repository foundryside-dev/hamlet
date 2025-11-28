# P1-VFS-OPERATORS-DSL — Expand Expression Operator Support

**Priority:** P1 (Important)
**Category:** VFS / Expression DSL
**Status:** MISSING (functions stubbed)
**Effort:** ~2–3 days (coding + tests)
**Owner:** TBD

## Problem
The VFS expression engine only supports a minimal operator set (arithmetic/comparison/logical, ternary, indexing, and four functions: `max/min/abs/clamp`). All richer operators referenced in VARIABLE_SUBSYSTEM.md (noise, smoothing, thresholds, distance, aggregation, moving averages, normalization, etc.) are absent. Using them currently raises `NotImplementedError` in the evaluator or schema/type errors. This blocks the documented DSL.

## Current State
- **Parser:** Handles literals, variables/path access, unary/binary ops, ternary, index access, and generic function calls (names allowed syntactically).
- **TypeChecker:** Validates arithmetic/comparison/logical ops; knows `max/min/abs/clamp` only; index type checking is unimplemented.
- **Evaluator:** Implements arithmetic/comparison/logical, ternary, index access; function calls limited to `max/min/abs/clamp`; unknown functions raise `NotImplementedError`.
- **Config guard:** `variables_reference.yaml` still rejects `expression` fields (keep guard unless explicitly enabled); VFS profiles may carry expressions.

## Required Implementation (Prioritized)

**Do Now (vectorized-safe):**
- Function registry shared by TypeChecker + Evaluator.
- Math/utility: `sigmoid`, `tanh`, `smoothstep`, `clamp01`, `mean`, `variance`, `normalize(list)`, `sum`, `product`, `min_all`, `max_all`.
- Aggregation/logic helpers: `count_where`, `argmin`, `argmax`.
- Noise/sampling: `normal_dist`, `uniform` (torch-backed).
- Threshold/hysteresis: `threshold(lo, hi)` (stateless clamp-like).
- Index/type checking for tensors/lists; validate integer indices.
- Tests for all above + failure paths; docs update to mark supported set.

**Maybe Later (needs state/history or efficient substrate access):**
- Temporal/derivative (high usefulness): `delta`, `lag`, `moving_average`, `ema`, `rate_of_change`, `falling_edge`, `rising_edge` (requires history buffers in ExecutionContext; plan small-window batched tensors).
- Spatial hooks (high usefulness on grids): `distance_to_affordance`, `in_range` using precomputed distance fields or batched nearest-neighbor on affordance positions; `direction_to_affordance` (medium) if we add unit-vector outputs.
- Noise: `perlin_noise`, `simplex_noise` (low; likely gated/omitted unless a vectorized impl is available).

**Do Not Do (for now):**
- Any function requiring non-vectorized per-agent loops or unavailable substrate hooks without a plan to batch; leave unimplemented with clear errors.

## Acceptance Criteria
- TypeChecker recognizes all listed functions with correct signatures and errors on arity/type mismatch.
- Evaluator executes the functions correctly (numeric parity with torch/utility helpers).
- Index-access type checking implemented for tensor/list-like values.
- Unknown functions raise a clear error.
- Tests added and passing (unit + integration).
- Documentation reflects the supported operator/function set and any limitations.

## References
- Code: `src/townlet/world/expression/parser.py`, `.../type_checker.py`, `.../evaluator.py`, `.../ast_nodes.py`
- Doc: `docs/plans/vfs_uplift/VARIABLE_SUBSYSTEM.md`
- Context providers: `townlet.effects.context.ExecutionContext` / VFS registry accessors
