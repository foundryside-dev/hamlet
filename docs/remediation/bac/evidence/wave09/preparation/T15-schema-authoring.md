# T15 bounded schema authoring handoff

Stationary source tree: `/workspace/hamlet`; integration owner remains root. No staging, commits, branches, worktrees, source copies, deletes, or subdelegation performed. No project imports, pytest, or runtime validation performed while the main writer was active.

## Authorization and causal RED

Root relayed Astra MEDIUM technical APPROVE before production editing. Review artifact: `T15-schema-and-selector-extension-review-r1.md`, SHA-256 `3daa2e2184fdc28d50d74ee5bf05a7aff208e32558504796c0771244f3749c79` (root-provided binding, not independently reread).

The root-owned actual broad RED run at `/workspace/bac-review-2026-11-01/qualification/wave09-red-r2/blocked-prerequisites.json` observed five schema-blocked cases. Root reported the causal failure was the production `ReplayBufferConfig.validate_batch_size_le_min_size` constraint, with owned learner RED 123 FAIL / 4 PASS. These are relayed observations, not runtime results claimed by this worker. DTO tests were written before the approved production change; no synthetic/local RED run was substituted.

## Exact change

Only production file modified: `src/townlet/config/training_v2_config.py`. Removed obsolete `batch_size <= min_size` validator and clarified the replay DTO/min_size descriptions: warmup counts retained eligible transitions, and backend readiness separately determines sampleability. All three positive required counts, `min_size <= capacity`, and forbidden extra fields remain unchanged. No batch-to-capacity proxy or replacement policy was added.

Only test file modified: `tests/test_townlet/unit/config/test_training_v2_config_dto.py`. Replaced obsolete B<=min assertion with B>min acceptance cases (including B3/min1/cap2), preserved-valid geometry controls, positive-count and required-field controls, and forbidden-extra control. Added direct public PER proof parameterized over `independent_with_replacement` and `successive_without_replacement`: empty replay refuses as warmup without advancing serialized owned PCG64 RNG; one recorded transition meets min1; replacement samples three units from N1; successive remains batch-unavailable and refusal preserves owned RNG. Readiness itself preserves RNG in both modes. RewardTensor construction uses root's exact source-verified public constructor relay without opening its source.

## Bounded source inventory

Read AGENTS.md and CLAUDE.md, then only these five implementation/test source files (initial total 2534 lines, final 2605). Did not open conftest, helpers, state.py, per_sampling.py, or any sixth implementation/test source.

| Source | Initial lines | Initial SHA-256 | Final lines | Final SHA-256 |
|---|---:|---|---:|---|
| src/townlet/config/training_v2_config.py | 443 | d103aafbfe4e7fd4e957b71fd0651c6b6d8bebb98de4581d9d53e2356907ca68 | 435 | ad097576f88e1e2a09ae816ccff823e9623e7d5584b0d0411b07efb2f6ba1dfc |
| src/townlet/training/replay_contract.py | 222 | 3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c | 222 | 3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c |
| src/townlet/training/replay_buffer.py | 677 | d6fd0517488cfde5291c33ce03f67923c407af932794fb8a902b10e1d137f1c8 | 677 | d6fd0517488cfde5291c33ce03f67923c407af932794fb8a902b10e1d137f1c8 |
| src/townlet/training/prioritized_replay_buffer.py | 1092 | 290eadca0305658abdd4aec361a9b167ac63d7a887438b602c19c2eaf9020de9 | 1092 | 290eadca0305658abdd4aec361a9b167ac63d7a887438b602c19c2eaf9020de9 |
| tests/test_townlet/unit/config/test_training_v2_config_dto.py | 100 | 9a6dfd73c23bbd2ef9fc73bbbbd55f98788afb89ed027233949cdf4591785164 | 179 | eaeed185ee43e72b7c7179705b52fb53dd8085e7ca366c2f5c9b0bd52e0c61be |

## Static verification

From `/workspace/hamlet`, all exit 0:

```text
.venv/bin/black --check src/townlet/config/training_v2_config.py tests/test_townlet/unit/config/test_training_v2_config_dto.py
  2 files would be left unchanged.
.venv/bin/ruff check src/townlet/config/training_v2_config.py tests/test_townlet/unit/config/test_training_v2_config_dto.py
  All checks passed!
git diff --check -- src/townlet/config/training_v2_config.py tests/test_townlet/unit/config/test_training_v2_config_dto.py
  no output
```

Initial owned Black formatting was applied before the final checks. Inventory collected with `wc -l` and `sha256sum` over exactly the five listed sources.

## Root integration follow-up / limits

Root must execute DTO tests and affected learner cases after all writers close, then own broad Green and review. Runtime correctness of the new test has not yet been observed here. New direct proof uses canonical flat transition replay only; recurrent batches count windows and are intentionally outside this bounded source inventory. Source reads established existing backend behavior, and the production change adds authoring capability rather than changing backend readiness or sampling invariants. Existing worktrees remain untouched.
