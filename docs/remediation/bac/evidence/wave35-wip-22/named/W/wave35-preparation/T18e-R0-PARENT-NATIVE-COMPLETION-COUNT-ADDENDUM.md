# Native completion count clarification

2026-11-14. Read-only clarification for active C1 writer/root. Only already-charged W/core regions re-read; body budget remains 4,842 lines/four bodies. No APP edit, test/runtime/import, Git/worktree operation or additional body inspection.

`WorldRNGState.activate_under` delegates to `_activate` (W790–795), which opens its own `domain.operation(..., operation_kind="rng", lineage=...)` (W798–799). It therefore adds a core completion phase; it is not merely the private-frame direct synchronization path.

`OwnedWorldBackend.call` opens `_scope("call", lineage)` (W1001; operation at W911), then directly opens `_rng._activate("service", custody)` (W1007). For an ordinarily entered successful call, **the wrapper itself contributes exactly two nested core completion phases, inner RNG activation then outer owner call**. Any further operation scopes created by its callback are additional and not counted here. This remains true for empty CPU device tuples: core nested exit always calls `_finish` (C1081–1091), and `_finish` calls `_complete(devices)` (C530–541). The empty `_complete` performs no CUDA synchronize, but its function invocation still exists.

Private `_globals` additionally calls `_synchronize` (W451–463) for RNG capture/restoration; that direct loop is distinct from the two core `_complete` calls. Neither private frame reuse nor the absence of CUDA devices removes the operation context at W799. These contexts use core `operation`, not `device_invocation`, so counting three BANK invocation handles does not count native operation-only completion phases.

No full BANK/count-provider trace is asserted: those bodies remain opaque/uninspected. A proposed trace with one `native` completion per entered `OwnedWorldBackend.call` undercounts the wrapper by one. The C1 writer must combine this exact native contribution with its own actual BANK call sites and callback work.

Verified unchanged source seals:

- W `src/townlet/exploration/world_curiosity_state.py`, 1361 lines: `433b3563457fbf68d26d47d73dc375c1382e0cc77d0987a4c9d4f62f3cdfcce3`.
- C `src/townlet/exploration/rng_custody.py`, 1195 lines: `6cb01ca77b58db5f4c4784dc36da566c06cf68c2a7c2ce227bb780549f3344f8`.

Original native supplier remains unchanged at SHA256 `7cb54762da2ecffae75091d06725afac71d83097f615cd364fc79ed1f54f0ba9`. This addendum changes no qualification or capability status.
