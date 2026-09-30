# Cut B qualification and delivery evidence

Status: implementation locally qualified and integrated. Hosted acceptance is pending.
Authority: [PRD-0003](../../prds/0003-declaration-store-cut-b-one-variable-contract.md),
PDR-0147 and accepted Cut A PDR-0149. No calendar deadline was added for B.

## Checkpoints

| Checkpoint | Recorded state |
| --- | --- |
| Baseline | `599cad15706ac8824c3f8e38276da6440c4816a3`, local `project-recovery-4` |
| Plan and parent bank | `4e1c01c0`, committed before production edits |
| Comparator with negative controls | `d7a71520` |
| Isolated typed-scope implementation | `8a234b61acdff44ccef5939db7cb1dc8f8ebb9f3` |
| Isolated scope identity bank | `4c06c846`: 106 observation-schema/VFS movements; no layout movement |
| Canonical implementation | `8060ef19b820ddada047570825865b69e6b38b3b` |
| Final fixture/consumer cleanup | `73f52c20e16e31ddbda9ec4ac637e02840ffb9de` |
| Clock-negative fixture and final tested source | `baced7dba659ab2024a3f164f18c450695000362` |
| Final direct-parent and frozen CPU qualification | Both exit 0 at `baced7db`; source/input tree clean, frozen run entire tree clean |
| Local integration | Fast-forward to `ded73a68c0b91a9e7209a1f2588ca660d236eba7` on local `project-recovery-4`; 87 post-integration checks passed |
| Feature push / B PR | Not performed; publication authorization required by automatic approval review |
| Hosted B checks | Not run; neither prior Cut A CI nor local checks substitute |
| Full PRD-0003 acceptance | Pending hosted checks and final delivery checkpoint |

## Criterion readings

| PRD criterion | Local reading and evidence |
| --- | --- |
| 1: One model | PASS. Required wrapped `variables` catalog, one DTO, no old authoring readers/DTOs/aliases. All live packs and executable positive fixtures converted. Old surface/type/permission payloads are negative controls with transport provenance; frozen fixtures remain historical evidence. `test_variables_dto.py`, declaration-store/edge tests and independent source inventory establish the boundary. |
| 2: State semantics | PASS. `test_canonical_variable_runtime.py` exercises declared writes, tick/episode/persistent reset and derived state both direct and cache-loaded. DTO/compilation/consumer-shape tests cover explicit null, deterministic tensor initializers, batch shape, eager restrictions and item refusals. All eleven parent reset censuses match. |
| 3: Symbols | PASS within supported consumers. One registry roster and profile-qualified item identities; configured global/agent writes and named rewards use the same state, including cache roundtrip. Unknown names/collisions refuse with origins. Scalar/bool global/agent reward consumers are qualified. This repairs the omitted-symbol defect, without promising generic pair/tensor reward reductions or a complete relational world. |
| 4: Scope | PASS. `test_token_binding_scope.py` and compiled-token-coherence tests cover mixed routing, dotted registry IDs, item profiles, required/mismatched scope, explicit null for non-variable bindings and persistence. Schema **1.28** refuses old artifacts. Registry exposure requires float32-backed state. Compact layout/type-schema and direct-parent observation bytes remain unchanged. |
| 5: Attribution | PASS. 31 cases / 884 hash readings; exactly 212 measured movements, each with values and a causing commit; none unexplained or stale. Ten direct-parent CPU trajectories (40 observation/action/reward/done arrays) and eleven reset censuses match byte-for-byte. Frozen matrix: ten CPU cells `DIVERGED_AS_REGISTERED`, ten CUDA cells explicitly `SKIPPED`, exit 0. Old source and frozen fixtures unchanged. |
| 6: Gates | LOCAL PASS: full default suite **4,055 passed / 18 skipped / 84% coverage**, exit 0. Ruff, Black, mypy, no-defaults and public CLI fleet exit 0; whitelist unchanged. Focused runtime/shape/persistence/negative-control suites pass. Hosted checks pending explicit publication approval. |
| 7: Hygiene | PASS. Active variables/declarations/compiler/VFS and changed item/effects/reward/expression docs use the new contract and name unsupported combinations. Internal expression/item profiles are compiler-owned execution products. Dated historical sketches remain explicitly non-normative. Independent review found no compatibility path. |
| 8: Independent checkpoint | Independent specification and quality reviews GO for local implementation; full-suite and local-integration conditions passed. Product acceptance still requires the hosted gate. This evidence and PDR-0150 distinguish local qualification from product acceptance. |

## Identity attribution and reproducibility

The 180 census changes comprise 53 observation-schema, 53 VFS composite, 31 environment,
31 transport config and 12 variable-schema readings. Selected trajectory metadata contributes
32 further identity readings; output arrays do not change. Environment identity moves because
the raw DTO no longer contains even an empty historical variable field; it is not a measured
world-state change. The twelve variable-schema changes are the reviewed fixed access policy,
removal of hidden inert normalization and canonical vector-dimension descriptor changes.

[attributions.json](attributions.json) records every exact value and cause. The
[canonical descriptor attribution](canonical-schema-attribution.json) supplies payload evidence;
[scope-only-hashes.json](scope-only-hashes.json) isolates the earlier scope change.
DIV-014 and the complete six-pack [input manifest](../../../oracle/declaration-cut-b-inputs.json)
cover precise frozen/live input drift. Historical output allowances were not expanded.
The direct-parent comparison has no historical observation allowance.

[Qualification commands](qualification-commands.md) and
[banked report digests](qualified-evidence-digests.json) point to final source `baced7db`.
Before evidence consists of `before-hashes.json`, `before-variable-products.json`,
`before-variable-transports.json`, `before-cpu-traces.json` and `before-resets.json`.
Raw NPZ trajectories remain in retained ignored run directories; they are not committed.
The comparator requires the retained before NPZ files whose digests and replay inputs are banked.
`--skip-cpu` is diagnostic only and cannot return qualified success.

## Gates and reviews

The [machine gate record](local-gates.json) retains commands, source checkpoint and terminal
exit statuses. Python 3.13.1, Torch 2.11.0+cu130 and Pydantic 2.13.4 run in the task's separate,
frozen all-extras environment. CUDA's presence in the installed version is not hardware qualification.

- Ruff: pass; Black: 561 files unchanged; mypy: 176 files, no errors.
- No-defaults: 176 files; unchanged 122-pattern whitelist (113 structural and nine line-based).
- Compiler CLI fleet: every positive pack plus three expected-negative fixtures, pass.
- Task-2 scope gate: 448 passed; canonical DTO/VFS/provenance: 83 passed; effect type gate: 14 passed.
- Complete internal constructor/runtime evaluation check: 117 passed, one skipped.
- Final independent criterion recheck: 18 passed. Final clock module: 25 passed; independent clock slice: 14 passed.
- Final full local suite: **4,055 passed, 18 skipped, 15 warnings, 84% coverage**, exit 0, 977.17 seconds.

Specification review preceded code-quality review. Review covered each PRD criterion, complete
old-surface caller inventory, variable descriptor causes, fixed permission boundary, expression
shape/refusal semantics, item limitations, input SHA inventory and evidence coherence.
The final clock-negative correction had an additional independent GO: it makes a hidden boolean
DTO-valid, preserving both origin assertions and reaching the intended clock-reference refusal.

An earlier full run had 4,054 passes and one failure: a boolean clock fixture hit the correctly
enforced registry-exposure refusal before reaching the clock check. The fixture now uses hidden
boolean state and a boolean expression. That earlier run is not acceptance. The complete rerun
passed; focused passes were not added to the earlier count.

## Custody and boundaries

Task branch/worktree: `feat/declaration-store-cut-b` at `/tmp/hamlet-declaration-cut-b`.
Preserve it and its ignored measurement traces while publication is pending.
Local integration completed on `project-recovery-4` at `ded73a68`; 87 focused checks passed in
21.11 seconds from the parent’s proper environment/import path. The execution-bearing tree
is identical to fully tested `baced7db`. See [local integration](local-integration.json).
Subsequent delivery-record changes are documentation/evidence only. No parent/main push occurred.
Parent's two pre-existing dirty Filigree skill references must remain byte-identical; both banked
SHA256 values are `27b0487e302939f67d6e1e2a4e1b66b531904944e9bf41b88e8c125e2ec0846a`.
The frozen oracle is verified at `4222a9176e68e232a0e46c7004183440e27f22c3`; it was read only.

Automatic approval review rejected pushing this private implementation to GitHub and creating
a draft PR because source export to that destination requires explicit user authorization.
No publication occurred. Once authorized, the B draft PR should be stacked against
`feat/declaration-store-cut-a` (existing draft PR #40); remote `project-recovery-4` predates accepted
Cut A, so targeting it would misrepresent the B-only diff. Local integration stays on its agreed parent.

This work does not repair initial item-appearance cache loss, carried-item publication, item-state
locality/capacity, effects reset or terminal-lane accounting. It does not qualify browser UX,
learned convergence, CUDA, Murk, BAC cognition, full privacy/access-role authoring, arbitrary
pair/tensor reward reductions or a unified command graph. Expression-shape diagnostics identify
the variable and variables-family source; exact merged declaration-line mapping remains wider
compiler diagnostics work.
