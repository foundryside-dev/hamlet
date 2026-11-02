# T15 existing fixture repair R1 — stationary for root execution

Prepared 2026-11-02 in existing `/workspace/hamlet`, HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`. Root explicitly confirmed all R0 runtimes closed before authorizing exactly these two observed fixture corrections. This worker ran no project import/runtime, pytest/collection, compiler or gate; there is no behavioral GREEN claim. Prior causal failure DATA and the detailed static audit are preserved in `T15-existing-fixture-audit.md`.

## Changes and preserved assertions

`tests/test_townlet/regressions/fixtures/episode_lanes.py::controlled_action_schedule` now derives ascending eligible world indices from real entry `~env.dones`, asserts provider Q `(K,A)` and state observation count K, resolves the original full-N authored schedule, projects its actions into those K rows, asserts mask shape `(K,A)` and checks each eligible selected action remains legal. It returns K actions to the actual provider call. Finite-Q, state-row alignment, full-N authored-action shape, mask presence and per-active-action legality assertions all remain. New K action/mask geometry assertions strengthen alignment. No RNG call was added. Witness actions retain the full-N authored schedule; witness Q values retain actual provider outputs, now K rows. The witness docstring states those distinct roles. `observe_environment_steps` is byte-for-byte unchanged: original real env.step still receives/records full-N transport, sticky done/reward/info and exact world ticks. The seven actual transition/lifecycle proof is preserved for root retest, not replaced by synthetic ENV execution.

`tests/test_townlet/unit/population/test_recurrent_training.py::TestEpisodeBuffering::test_store_episode_and_reset_adds_to_buffer` still builds its original five random manual rows. A comment explicitly labels them synthetic unit inputs, not captured authored ENV evidence. Each row now supplies restrictive one-hot bool[A] successor legality with allowed action `(i+1)%A`, and a scalar bool True recorded flag on the existing CPU device. This declares synthetic successor legality rather than fabricating all-legal historical ENV proof. An assertion requires both legality lists to align with all five observations; two new assertions verify those lists are empty after reset. Every original success/observation-reset/positive-replay assertion remains. No production collector, buffer method or validation changed.

The old maskless twenty-episode smoke and scheduler-persistence controls are untouched. As already recorded in the audit, their current assertions do not prove actual optimizer learning/progress. Root explicitly excludes that optional diagnostic cleanup from this observed-failure repair; T15 owned actual-update/prefix controls independently carry learning acceptance. No capability/public method was removed or renamed, and no skip/xfail/assertion reduction was introduced.

## Complete source inventory and final identities

Exactly the same five whole sources were inspected; **3313 current lines total**, below five/5000. No sixth source, imported fixture implementation, conftest, POP, SB, RB, provider, runner or other test was opened. Only RT and AL below were edited.

| Source | Current lines | Current SHA256 |
|---|---:|---|
| `tests/test_townlet/unit/population/test_vectorized_population.py` | 1884 | `9e0b50095cd29470afc92d42a740a800e34c731aea12abfa96a7d60d89b1015c` |
| `tests/test_townlet/unit/population/test_recurrent_training.py` | 573 | `32f3a4e7996a5798c17b10a1ae69ad6d22631a2421549c33501f3764560325f9` |
| `tests/test_townlet/unit/population/test_double_dqn_algorithm.py` | 324 | `b9b12150109541ed53f75fc692661c305f075b616827bac4c37a83afbe859e5a` |
| `tests/test_townlet/unit/population/test_action_selection.py` | 375 | `81ffc9ef6390f2a64471f3e9daf3ea77c751d1bc0e97ff6cbd5b03eede65b2b1` |
| `tests/test_townlet/regressions/fixtures/episode_lanes.py` | 157 | `9de34aa9764fe2cef766aace4e6ebd391543621fa90def16b5614292e476ec7f` |

## Executed verification and remaining root work

Fresh owned checks both exited0:

```text
.venv/bin/black --check tests/test_townlet/regressions/fixtures/episode_lanes.py tests/test_townlet/unit/population/test_recurrent_training.py
# 2 files would be left unchanged
.venv/bin/ruff check tests/test_townlet/regressions/fixtures/episode_lanes.py tests/test_townlet/unit/population/test_recurrent_training.py
# All checks passed
```

The complete two-file diff was read after editing, and all five hashes/counts were measured. These static checks do not prove runtime correctness. Root owns retesting all B03 shared-helper consumers and the buffering unit, exact candidate identity/gates and separate review. Bootstrap/BPTT/lane-learning/factory failures have separate owners; no diagnosis or workaround for them is introduced here.

No branch/worktree/source copy/deletion, project imports/runtime/pytest, tracker/index/commit/publication or subdelegation occurred. Existing fourteen worktrees were preserved. Concurrent main/other-owner disjoint edits are outside this worker's custody. Only the two named existing test/helper files and this ignored report were written in this repair turn. Return stationary; no further writes until root clearance.
