## Gaps

Full defect sites, reproductions and refutations: `review-2026-10-24/findings_vfs.md`
(referenced below as F-numbers) and the filigree ids where a backlog bug is folded in.

| id | sev | gap | source |
|---|---|---|---|
| V1 | P1 | Four graph phases never executed by `step()`; writes there compile green and never apply; five later phases compile green and crash | F1, hamlet-cebe51077a |
| V2 | P1 | Action writes infer the agent axis from `shape[0] == num_agents`; non-agent scopes silently masked or crash by `num_agents` | F2 |
| V3 | P1 | `evaluation_mode: eager` evaluates statics from compile-time literals | F3 |
| V4 | P2 | `extents.num_affordances` required and ignored | F4 |
| V5 | P2 | Variable id equal to a meter name compiles; detected only inside VTC apply | F5 |
| V6 | P2 | `reward_component_program` compiled and hashed, never run; `compile_vtc_bounds_clamps` uncalled | F6 |
| V7 | P2 | Agent-scope expressions cannot read globals, including the clock | F8 |
| V8 | P2 | Bare `vfs.X` write to an agent variable writes the whole batch per interactor | hamlet-b9a3bcbde2 |
| V9 | P2 | `zone` scope: storage, no consumer | hamlet-02bd5a3eaa |
| V10 | P2 | Unreachable registry modes and zero-caller functions; `semantic_type` required and unconsumed for hidden variables | F10 |
| V11 | P3 | Engine/VTC writes coerce dtype where `set()` validates | F7, hamlet-2ca2cb373f residual |
| V12 | P3 | `variable_schema_hash` ignores shape and initializer | F9 |
| V13 | P3 | Random initializers draw once and restore on reset | F11 |
| V14 | P3 | Expressions see `social_residue` writes one tick late | F13 |
| V15 | P3 | Residue: stale docstring, four dead whitelist lines, inert accumulators in `configs/simple`, VFS.md §6 claims | F12 |
