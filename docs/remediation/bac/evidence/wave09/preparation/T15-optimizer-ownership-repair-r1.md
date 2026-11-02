# T15 raw optimizer ownership repair R1

The [causal ownership RED](/workspace/bac-review-2026-11-01/qualification/wave09-r1a-causal/causal.log), SHA256 `cc0d546bd840e688fe3813e68aee67902c6db815231d74f349ad3fca3d764cad`, confirmed actual shared optimizer tensor storage in all four affected flat restore cases at candidate096cdb7d98a9725181658c44b3ed84a6d0d72e82. Its [machine result](/workspace/bac-review-2026-11-01/qualification/wave09-r1a-causal/causal-result.json) records exit1 and112.173863 seconds. Root supplied the executed failure interpretation; this repair did not rerun it. Prior evidence remains unchanged.

Changed exactly one production line in POP2039: the validated optimizer mapping is now copied with `copy.deepcopy(dict(...))` before `optimizer.load_state_dict`. This owns nested tensor storage and containers while preserving values, validation order, learned clocks, hyperparameters and install semantics. The existing copy import is reused; no new default, ternary assignment, waiver or ratchet change was introduced. Allocation/copy still precedes live population installation.

Permanent storage-disjointness, saved/eager post-step immutability, exact sampled-input, RNG, mode and clock assertions remain unchanged. No tolerance, case, sampler requirement or fixture assertion was removed. The separately supported manual optimizer-attachment fixture continues to own its deliberate direct Torch payload independently.

| Complete source | Lines | SHA256 |
|---|---:|---|
| `src/townlet/population/vectorized.py` |2146|`9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a`|
| `src/townlet/training/replay_contract.py` |222|`3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c`|
| `src/townlet/training/q_targets.py` |80|`39485fe2447dc4065bd7b806775c93c0e66b51827b088605fba98505b100491f`|
| `src/townlet/config/bac_options.py` |294|`10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916`|
| Owned `test_learner_legality.py` — unchanged |1198|`5f6273a8054bde34f89ab77eb98c8b4c0bb9428b586511b976cecae19c33e71e`|

Actual whole-source context remains5/3940, projected5/4950, hard5/5000. No sixth implementation/test/helper was read. Target-only Black `--check` and Ruff passed for POP and the owned test. Root's ratchet612 remains untouched. Separate supplier-owner files were observed only through status, not read/edited. No project imports/runtime/pytest/collection, other production change, index/staging/commit, branch/worktree/source copy/subagent or publication occurred.

Return stationary for root's fresh causal GREEN and remaining owned/owner/gate/review work. This is an unexecuted repair candidate, not a passing runtime or release claim.
