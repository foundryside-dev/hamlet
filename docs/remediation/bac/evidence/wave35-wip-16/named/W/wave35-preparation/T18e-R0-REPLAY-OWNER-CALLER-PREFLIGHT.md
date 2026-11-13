# Recurrent owner-test current-API repair preflight

2026-11-13. Read-only source diagnosis for frozen R84 candidate `aa583c282043c445c2286b0b93df244cad9149c5`, base `29d0204a70b6eef0017b3cee638812e2cc5c7899`, in the existing `/workspace/hamlet` integration checkout. This document is the only write. Implementation and runtime qualification remain with root after the separate grant. No production changes are proposed.

## Scope and budget

Read the owner brief and repository AGENTS.md first. Measured the four admitted whole bodies before reading: owner test611, sequential replay1930, replay contract374, RNG custody371 = **4 bodies / 3286 lines**. All four were inspected; no fifth body or external imported implementation was opened. The public Fix-B, replay and core API capsules supplied external context; the older replay capsule is historical, with current signatures established directly from the admitted source and Fix-B delta. No whole plan or context history was read. No imports, tests, static checks, Git/index operations, branches, worktrees, execution copies, deletions or delegation occurred.

## Confirmed caller repairs

The owner module has **21 source call sites** missing required explicit lineage. Original line numbers below refer to its current 611-line body, not future edited positions.

| Public method | Original lines | Required update |
| --- | --- | --- |
| `sample_sequences` | 101, 117, 132, 186, 392, 416, 432 | Add `lineage=None` to every call, including intended refusal calls and positional `(1, 3)` call432. |
| `load_from_serialized` | 127, 288, 291, 294, 297, 314, 405, 427, 442, 465, 476, 511, 534 | Add `lineage=None` to every call, including malformed input/refusal cases and both parametrized tests. |
| `load_for_mode` | 401 | Add `lineage=None` while preserving `requested_mode="recorded_full_resume"` and the historical-legality refusal assertion. |

Every listed call is genuinely standalone in this module: no enclosing domain operation, backend activation or nested callback supplies an active operation. Explicit None is therefore the authentic caller declaration. Do not invent a parent lease or wrap the suite in one; constructors register owners while idle. If a future test deliberately introduces genuine nesting, it must obtain and pass the exact active `RNGOperation`, with owners constructed before that operation. There is no such nesting to repair here.

`sample_sequences` is guarded by `replay_sample`; `_required_lineage` refuses omission before intended sample behavior. The two public loaders also require explicit keyword lineage and forward that declaration through their real preparation/installation paths. Their standalone internal calls are sequential operations, not caller-held nesting. `serialize`, `validate_serialized`, storage, `clear`, stats and read properties do not acquire a public lineage argument; leave their callers unchanged. This module has no direct calls to `sample_batch`, `prepare_serialized`, `materialize_validated`, `load_prepared` or archive preparation requiring further caller migration.

Preserve all original exact state, version/kind/key-set, capacity, tensor-contract, component, archive, input nonmutation, readiness/refusal, clear and stats assertions. Do not catch the missing-lineage TypeError, broaden exceptions, provide a default/fallback, skip tests or alter production to satisfy these callers.

## Confirmed fixture mismatch and finite correction

`test_sample_sequences_masks_post_terminal` at91 patches `random.choice` at97, but the current direct sampler actually calls `random.choices(valid_episodes, weights=episode_lengths, k=1)[0]` followed by `random.randint`. Replace that obsolete patch with an explicit-signature `random.choices` patch accepting `(population, weights, k)` and returning `[population[0]]`; retain the current start-zero randint patch. This exercises the real direct sampler and retains deterministic selection without replacing a production method. Only one episode currently exists, so the stale choice patch is ineffective rather than evidence of a demonstrated random failure.

The same test stores `make_episode(6)`, whose only terminal is index5, then samples indices0..3. Its comment says terminal index3, but that fixture does not currently exercise a terminal in the sampled window. Make that intent concrete by creating the six-row episode locally, setting `dones` to `[False, False, False, True, False, False]`, then storing it in this existing unconfigured legacy/inspection buffer. Keep the original four-row mask-all-True and composed-reward assertions. Add a second six-row direct sample with explicit standalone lineage and assert mask exactly `[[True, True, True, True, False, False]]`; retain reward-value checks for that sample as well. The stored six rows and terminal/post-terminal transport are intentional in this direct legacy masking test. Do not move this fixture into configured captured storage: `_captured_rows` correctly refuses real rows continuing after a terminal. The separate existing archive/inspection roundtrip test already intentionally uses the unconfigured direct path for `[False, True, False]`; preserve it.

No further invalid-state fixture change is established by this inspection. The `qualified_buffer` fixture declares action_dim8, and its current qualified cases store lengths3..5 with actions0..length-1 and a final terminal, satisfying the current action and terminal bounds. Existing malformed dtype/shape/kind/key/capacity/version fixtures are deliberate negative inputs; preserve their exact refusal and nonmutation assertions. Unconfigured format5 remains intentional transport for archival import, while configured format6 remains active replay. Do not change either into a compatibility route.

## Proposed writes and execution handoff

After root's separate test-only grant, write **only** `tests/test_townlet/unit/training/test_sequential_replay_buffer.py`: the 21 lineage arguments, the corrected actual sampler patch, the local terminal fixture correction and the additional actual post-terminal assertion/sample above. Proposed owner test cap **650 lines** (current611; allowance39), keeping the four-body packet at **at most3325 lines**, under the stated five-body/5000 ceiling; the fifth body remains unused and requires root routing. No added helper module, fixture body, imports or production changes are needed. Existing 49 collected cases remain the intended owner selection; no new parametrization/test nodes are proposed.

Root's supplied actual R84 evidence is owner collection49 and the `-x` gate's **1 PASS / 1 FAIL**, with first failing node:

`tests/test_townlet/unit/training/test_sequential_replay_buffer.py::TestSequentialReplayBuffer::test_sample_sequences_masks_post_terminal`

The failure at old line101 is `Missing required keyword-only argument: 'lineage'`, before its intended masking assertions. Supplied log: `/workspace/bac-review-2026-11-01/qualification/wave35-r84-owner-sequential/owner-sequential.log`. That log was not opened or rerun by this preflight. The supplied 107 ordinary regression passes and negative-custody inventory are root evidence, not independently reproduced here.

First rerun selection after implementation is the exact failing node above with root's existing qualified runtime/provenance wrapper. Then select the complete owner module `tests/test_townlet/unit/training/test_sequential_replay_buffer.py` (49 collected cases), initially retaining `-x` if root wants first-blocker progression, followed by the complete selection for a terminal result. Root owns exact executable, environment, artifact attempt and any combined regression requalification. This preflight grants no execution.

Source facts above establish the missing arguments and fixture mismatches. They do **not** establish that the repaired node or all49 will pass; no repaired source exists and no runtime/static/type checks were run. Any new blocker after these finite prerequisite updates needs actual evidence and root routing, rather than speculative changes or widened assertions.
