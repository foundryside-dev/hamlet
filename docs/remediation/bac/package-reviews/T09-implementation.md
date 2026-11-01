# T09 implementation receipt — successor legality producer

Status: owned files frozen for fresh independent Astra review; no commit/stage/push performed. This is focused evidence, not a repository-green declaration.

## Candidate and scope

- candidate_sha / predecessor: `050a1a70e979aa03724219b81e848093820f044f` (T08); T09 is the uncommitted owned-file content hashed below.
- Checkout/import: `/workspace/hamlet`; asserted `townlet.__file__ == /workspace/hamlet/src/townlet/__init__.py`; `torch.get_num_threads() == 1`.
- Only implementation changes: `src/townlet/environment/vectorized_env.py` plus new `tests/test_townlet/regressions/bac/test_successor_producer.py`.
- No capability reductions, helper-source expansion, physics changes, root-ledger changes, frozen-plan changes, dependency installs, or subagents. Existing `get_action_masks()` remains unchanged.
- Production change: build canonical masks through `get_action_masks()` after the same successor observation, item processing, terminal/retirement status and next-action hour have committed; clone into `info['successor_action_masks']`. Diagnose truly live empty rows with pack, level, tick and agent indices. Terminal/inactive empty rows remain valid; no fabricated legal action.
- The diagnostic occurs after the transition has committed. It does not promise rollback or alter authored transition semantics.

## Bounded source inventory

Exactly four implementation/test sources inspected (existing whole-file sizes charged, including the new test):

| Access | File | Initial lines | Frozen lines | Ceiling | SHA256 |
| --- | --- | ---: | ---: | ---: | --- |
| Modify | `src/townlet/environment/vectorized_env.py` | 1702 | 1714 | 2000 | `849cacc1b94e13109d3ba5391b1d30668a89db308a3e228f3476a0f5457b595d` |
| Read only | `src/townlet/environment/action_mask_builder.py` | 206 | 206 | 250 | `5d02f08f94c68bbd63b4491a5ed00a432a3fbadbec6b9a02572d544bfbcb7174` |
| Read only | `src/townlet/training/replay_contract.py` | 222 | 222 | 250 | `3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c` |
| New test | `tests/test_townlet/regressions/bac/test_successor_producer.py` | absent | 212 | 350 | `c88043817f6996f02a1a7cb732e96b1afdc1a70c548b7b956c7da125eb605670` |

Total frozen inventory: **4 files / 2354 lines**, below the projected 2850-line limit. Existing owner tests were executed without opening them. Other reads were AGENTS, task brief, reports, Markdown specifications and authored YAML only.

## Authored proofs and causal red/green

The new test copies `configs/aspatial_test` into pytest's scratch directory, declares an exclusive item, real initial spawn, a disabled custom action, configurable real GET-only action set and authored lane death. It compiles with `use_cache=False`, then uses actual reset, GET, DROP and WAIT steps. No injected meter/done/inventory/mask state or mocked builder is used.

Assertions cover:

- Actual GET changes from legal to illegal after pickup fills inventory, then legal again after DROP. Captured masks equal the canonical builder at the returned successor; observations equal current committed encoding.
- Globally disabled action mass remains zero at every captured successor.
- Historical masks survive the next live step and reset. Mutating another returned mask does not affect environment masks or prior history.
- Authored lane death publishes terminal all-false legality, preserves entry-active admission and once-only terminal event; a later tick freezes the completed lane's count and rewards while its sibling advances. All-inactive extra ticks remain valid all-false/no-event/zero-reward.
- External stop after two live ticks retains `done=False` with the real selectable mask; reset cannot rewrite it.
- GET-only live pickup creates a genuine empty successor, raising a located diagnostic without inventing a rescue action.
- GET-only pickup coincident with retirement allows terminal empty legality and publishes retirement status.

Collection/import checked before execution. Five tests collected successfully. Initial fixture authoring mistakes (empty tags and a list-form enabled_actions rejected by the current parser) were corrected before meaningful red evidence; they are not counted as causal failures. The accepted complete GET-only authored surface is `enabled_actions: {custom: [GET]}`.

focused_commands (all from `/workspace/hamlet`, prefix `PYTHONPATH=/workspace/hamlet/src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`):

```bash
.venv/bin/python -m pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_successor_producer.py -q
```

- Causal red before production edit: **5 failed in 1.19s**; four `KeyError: 'successor_action_masks'`, one expected live-empty diagnostic `DID NOT RAISE`. Full retained output: `/tmp/t09-red.txt`.
- Initial green: **5 passed in 1.18s**.
- Final after formatting: **5 passed in 1.82s**.
- This is the same focused selection as the planned `uv run pytest` command. Bare uv initially failed its unwritable default cache; temporary-cache uv attempted an unavailable PyPI editable build. Coordinator directed use of the existing `.venv/bin/python -m pytest` toolchain instead. No package synchronization/install succeeded or was needed. `UV_NO_SYNC=1` collection/import had also passed.

## Owner suites and local checks

owner_suite_commands (same PYTHONPATH/OMP/MKL prefix):

```bash
.venv/bin/python -m pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/test_episode_lane_environment.py tests/test_townlet/unit/environment/test_action_masking.py tests/test_townlet/unit/training/test_episode_accounting.py tests/test_townlet/integration/test_authored_episode_lanes.py --collect-only -q
.venv/bin/python -m pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/test_episode_lane_environment.py tests/test_townlet/unit/environment/test_action_masking.py tests/test_townlet/unit/training/test_episode_accounting.py tests/test_townlet/integration/test_authored_episode_lanes.py -q
```

**80 collected; 80 passed in 15.05s**. Outputs: `/tmp/t09-owner-collection.txt`, `/tmp/t09-owner-green.txt`.

static_commands executed locally:

```bash
.venv/bin/ruff check src/townlet/environment/vectorized_env.py tests/test_townlet/regressions/bac/test_successor_producer.py
.venv/bin/black --check src/townlet/environment/vectorized_env.py tests/test_townlet/regressions/bac/test_successor_producer.py
git diff --check -- src/townlet/environment/vectorized_env.py tests/test_townlet/regressions/bac/test_successor_producer.py
```

All passed on frozen content. Ruff import order and Black formatting were corrected before the final green.

## Review and remaining coordinator gates

- review_record: pending independent Astra review of this bounded content; root coordinates the immutable candidate snapshot and fixes/re-review if required.
- full_suite_status: not run by this worker; no self-waiver or repository-green claim.
- full_suite_reason: coordinator owns same-snapshot global gates and earlier-trigger assessment. New step metadata and the live-empty diagnostic require actual consumer/full-boundary assessment before dependent release; this receipt does not authorize deferral.
- unrun_checks: repository-wide Ruff, Black, mypy, no-defaults lint, compiler CLI validation, expression-document validation and full pytest are coordinator-owned; fresh independent review pending.
- next_full_gate: **G2**, or earlier if the coordinator's actual patch/consumer assessment triggers it.

Frozen files will not be edited further absent a specific review repair request.
