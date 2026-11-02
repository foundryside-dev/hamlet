# T15 R1a — ownership RED instrumentation, verified fixture/static repairs

Main returns stationary before any optimizer ownership production repair. Root reports closed R0 runtime: owned29FAIL/121PASS, B0342FAIL/125PASS, five guards PASS and no-defaults FAIL623>613. The four flat post-step model discrepancies remain unresolved until the new causal ownership assertions execute. Prior R0 artifacts/receipts remain unchanged.

## Complete bounded context and hashes

| Whole source | Actual lines / ceiling | SHA256 |
|---|---:|---|
| `src/townlet/population/vectorized.py` | 2146 / 3000 | `6548abfe25bc58e8ff0dad00638387898f9a6504357a07e2c42c646915b9ef52` |
| `src/townlet/training/replay_contract.py` — unchanged | 222 / 250 | `3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c` |
| `src/townlet/training/q_targets.py` — unchanged | 80 / 100 | `39485fe2447dc4065bd7b806775c93c0e66b51827b088605fba98505b100491f` |
| `src/townlet/config/bac_options.py` — unchanged | 294 / 300 | `10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916` |
| Owned `test_learner_legality.py` | 1198 / 1300 | `5f6273a8054bde34f89ab77eb98c8b4c0bb9428b586511b976cecae19c33e71e` |

Actual context **5/3940**; projected **5/4950**, hard5/5000 unchanged. No sixth implementation/test/helper/linter source was opened. Separate fixture-owner paths were observed only in git status, not read/edited. Root remains sole index/integration/ratchet owner; no staging/commit or worktree/source-copy operation occurred.

## Exact repairs and new causal controls

- Corrected the residual oracle to explicit float64, retaining the required production float64 errors. Recurrent archive setup now uses the verified public prepare_archived_import→load_prepared pair, and current6→7 beta reads the public serialized priority_state.beta. No sampler/backend contract was weakened.
- The deliberately manual attachment fixture deep-copies optimizer state before direct Torch load, so framework aliasing is not attributed to population loading. The production raw population load still uses shallow `dict(checkpoint['optimizer'])` at POP2039 and `optimizer.load_state_dict` at2055; these ownership lines are untouched.
- Permanent raw-load assertions now require target optimizer storage to be disjoint from the saved payload and the other target. After the lazy update, saved input and eager optimizer must remain byte-equal to snapshots. Current observations and train/eval modes are compared before stepping; actual sampled DTO rows/actions/rewards/masks/IDs/weights/receipts are compared. Torch, NumPy and Python RNG streams are restored for the eager control and their resulting states are compared. These assertions isolate payload ownership from sampling/input/mode/clock differences without tolerance changes.
- Added recurrent L3/min1/B2 contrast with exactly three retained transitions but one sampleable window. Successive must skip without sampler RNG draw or optimizer/LR/target changes; replacement must sample that one real window twice and actually change network parameters. Both still advance the vector tick and beta. All earlier cases/assertions remain.
- Converted exactly the11 newly introduced production ternary assignments to explicit identical if/else branches. No parameter default, behavioral/provenance rule, waiver or ratchet value changed. Root supplied the no-defaults-linter interpretation; this main did not inspect/run that sixth source. Root owns confirming the actual count and lowering the data ratchet if required.

## Next causal execution and static result

Intended new failing ownership selector is `tests/test_townlet/regressions/bac/test_learner_legality.py::test_load_before_first_step_adopts_current_replay_and_clocks[load-active-current-feedforward-False]` (root confirms current collected spelling). It should first fail the explicit storage-disjointness assertion if the shallow-load hypothesis is correct; no ownership fix may precede root's observed causal RED. The new `test_recurrent_one_window_readiness_distinguishes_laws` supplies both law controls.

Target-only Black `--check` and Ruff both pass for POP and the owned test. No project imports/runtime/pytest/collection, production optimizer fix, other source edit, index operation or commit was performed. No runtime acceptance is claimed; raw optimizer storage sharing remains a concrete hypothesis pending root's new assertion. Return stationary for root identity capture, causal RED and the next bounded repair clearance.
