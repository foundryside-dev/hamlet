# Recurrent owner caller/fixture test-only report

2026-11-13. Implemented the accepted PREFLIGHT under the subsequent OWNER-CALLER-GRANT in the existing integration checkout. **Owned application write is complete and frozen** for root's exact-source capture and runtime qualification. No production source was edited.

Only application file changed: `tests/test_townlet/unit/training/test_sequential_replay_buffer.py`. Added explicit standalone `lineage=None` to all21 original caller sites (7 direct samples, 13 serialized loaders, 1 mode loader). No caller in this test module holds an enclosing operation requiring actual nested lineage. Corrected the direct sampler patch from unused `random.choice` to actual `random.choices`, accepting its explicit `(population, weights, k)` signature. Corrected the six-row fixture to terminal index3, retained the original four-row all-true mask and composed-reward assertions, and added a real six-row direct sample asserting exact post-terminal mask `[[True, True, True, True, False, False]]` and all six composed reward values. The new sample also supplies explicit standalone lineage, yielding22 current affected calls. The intentional legacy direct-path post-terminal fixture stays unconfigured. All existing test cases, refusal matches and exact-state assertions remain present; no skips, compatibility defaults, production changes or new test nodes were added.

## Frozen body counts and SHA256

| Body | Lines | SHA256 |
| --- | ---: | --- |
| `tests/test_townlet/unit/training/test_sequential_replay_buffer.py` | 617 | `15c6b65d60e45c4e865689593de42d2079dc34318949462c51b257a5923796b2` |
| `src/townlet/training/sequential_replay_buffer.py` | 1930 | `e261a0caca68c74cc36bdb9469b126aa0bdae38eeababf358a20bf96f8373317` |
| `src/townlet/training/replay_contract.py` | 374 | `8de53fc6814a16bafb703728ed396d7b9a1298afdb415be4ec8d1d85ac1502a1` |
| `src/townlet/exploration/rng_custody.py` | 371 | `9d6cd6fcfe62d8e53bda1e6ce7b34a89454ccc88373b5ec4cd072fe004ad66fb` |

Exactly4 admitted whole bodies /3292 lines; test growth6, below test650/projected3325 and hard5/5000. Fifth body remains unused. Production hashes match the directly reviewed preflight capsule identities.

## Actual development checks

Executed from `/workspace/hamlet`, both exit0:

```text
.venv/bin/black --check tests/test_townlet/unit/training/test_sequential_replay_buffer.py
All done! 1 file would be left unchanged.

.venv/bin/ruff check --no-cache tests/test_townlet/unit/training/test_sequential_replay_buffer.py
All checks passed!
```

Read-only `rg` inspection confirms every current direct sample/serialized loader/mode loader call supplies explicit lineage. `wc -l` and `sha256sum` supplied the exact observations above. No imports/runtime/pytest/mypy, Git/index work, copies, branches, worktrees, deletion or delegation occurred. The only other write is this authorized prose report. These development checks establish formatting/lint only, not runtime behavior or suite acceptance.

## Root execution handoff

First causal selection remains `tests/test_townlet/unit/training/test_sequential_replay_buffer.py::TestSequentialReplayBuffer::test_sample_sequences_masks_post_terminal` (original missing-lineage blocker). Then qualify the full owner module, expected49 cases from root's earlier actual collection, plus required retained checks under root-owned exact-source provenance and independent review. This actor did not collect or execute those selections. No further source edits will occur without root routing.
