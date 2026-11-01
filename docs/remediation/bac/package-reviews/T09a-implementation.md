# T09a implementation receipt — inactive physical action admission

Status: owned executor and new regression module frozen for independent other-model review. X03 is repaired in the bounded physical-action surface, with causal red/green evidence. No whole-BAC, full-simulator freeze, or release-green claim. No stage, commit, push, subagent dispatch, frozen-plan/root-ledger edit, or changes to other packets.

## Identity and source inventory

Checkout `/workspace/hamlet`; HEAD before/after `050a1a70e979aa03724219b81e848093820f044f`. This is a mutable working-tree candidate, identified by owned-file hashes, not by HEAD alone. Before expensive execution and again on the final candidate run, asserted `townlet.__file__` resolves to `/workspace/hamlet/src/townlet/__init__.py`. Direct installed `.venv/bin/python`, CPU, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, explicit `torch.set_num_threads(1)`.

| Access | Source | Initial lines | Frozen lines | SHA256 |
| --- | --- | ---: | ---: | --- |
| Write | `src/townlet/environment/action_executor.py` | 291 | 299 | `c0f1c2ee2396e35e192d11d81d79f5a25f1112d3ef8143adbff367011dbbe980` |
| Read | `src/townlet/environment/vectorized_env.py` | 1714 | 1714 | `849cacc1b94e13109d3ba5391b1d30668a89db308a3e228f3476a0f5457b595d` |
| Read | `tests/test_townlet/regressions/bac/test_successor_producer.py` | 212 | 212 | `c88043817f6996f02a1a7cb732e96b1afdc1a70c548b7b956c7da125eb605670` |
| New | `tests/test_townlet/regressions/bac/test_inactive_action_execution.py` | absent | 244 | `851986aa7f17350c8c769b939a400207ac718c97acfaf23ed0e657e3f41bab67` |

Four logical implementation/test files, **2469 frozen lines**; same logical executor baseline additionally loaded for the isolated causal comparison, conservatively **2760 lines including both revisions**, below 3000. Baseline executor SHA256: `fafc6e34c8806cf9f681a5b6eb797828b1309953aa7efbe03a1635c3375e3161`. Hashes were checked again after verification and match. No item-handler, conftest, other implementation/test/helper, or external T09 review probe source was opened. Existing owner suites were execute-only. Other reads: own brief first, AGENTS, T09/B11 reports, Markdown specifications, authored YAML and filename discovery. User preservation requirements override AGENTS deletion guidance.

## Repair and preserved behavior

`VectorizedHamletEnv.step()` computes activity and calls the action executor before terminal evaluation. The executor now captures `~env.dones` on entry and intersects it with physical substrate movement, movement debit, GET, USE_SLOT, DROP_SLOT, and custom-item action admission. The actual action vector is unchanged and continues to reach VTC with the existing explicit activity mask. No public signature/default, action vocabulary, live legality semantics, capability, or item implementation changed.

Completed velocity is retained too: assigning a zero displacement to every row would mutate a completed row whose final eligible movement had nonzero velocity. Live rows still publish their current displacement.

The prior INTERACT intent distinction is deliberately preserved. `substrate_mask` remains the action-ID-range intent mask; the new `active_substrate_mask` gates physical movement only. `interact_intent.any()` still triggers `_handle_interactions`, including the existing `_update_affordance_tracking` timing; the separate entry-active interaction mask gates actual interaction and debit. The existing rationale remains in source with an explicit explanation of the new separation. Existing dead-interaction gating, action-cost and VTC interaction-progress owner suites passed. This preserves the repo-owner ruling; it is not a claim that every tracking field is frozen by this packet.

## Authored regression evidence

The fixture uses the counted existing producer helper's real pack, compiler, reset and action API. It authors real item commands, lane death, and spatial movement costs. No runtime done, meter, inventory, mask, or position state is injected. Every submitted live action is independently checked against predecessor legality; completed slots alone may carry otherwise-illegal transport actions.

Permanent tests cover:

- Exact X03: both worlds GET then WAIT; world 0 terminates via authored rules. `[DROP_SLOT_0, WAIT]` must leave its held inventory unchanged while world 1 advances from step 2 to 3.
- Four worlds with two authored terminal rows and two live siblings; dead WAIT/GET/DROP/USE plus local TOUCH and inventory POLISH verbs, each with exclusive and nonexclusive/shared item types. Live GET/DROP changes actual inventory, and USE/custom verbs increment money by the authored literal 1.0.
- Completed observation, meter, position, velocity, inventory and bounded item identity/position/holder snapshots remain equal during continuing siblings and all-completed extra steps. These use the manager interfaces already visible in ENV, not invented owner snapshot APIs.
- Real grid movement on terminal-causing and retirement-causing steps executes; following dead movement and dead WAIT preserve nonzero final velocity. Live siblings still move and pay the authored health debit 0.1.
- GET/DROP/USE/local/inventory actions execute on the eligible terminal-causing step. Subsequent transport actions cannot repeat the effects.
- Canonical committed successor masks, historical mask ownership, literal entry-activity/step counts, zero inactive rewards, once-only authored/retirement events, and all-completed extra steps remain correct.

Initial collection caught a relative-import mistake, corrected before causal red. Expanded fixture calibration caught incorrect custom-command YAML shape (the accepted shape is a list of `{name, effects}` declarations) and the real spatial affordance placement requirement (authored randomization enabled). Those setup failures are not causal evidence.

## Red and green

All execution from `/workspace/hamlet`, with environment prefix:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=/workspace/hamlet/src
```

Collection/import were checked before the first regression execution. Initial new-test command:

```bash
.venv/bin/python -m pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_inactive_action_execution.py -q
```

Before production edits, **1 causal failure in 0.31s**, `/tmp/t09a-red.txt`: inventory changed from `[[0], [1]]` to `[[-1], [1]]`; entry activity `[False, True]`, counts `[2,3]`, zero old-lane reward and no repeated completion had already passed. Expanded movement-only pre-fix run: **2 causal failures**, `/tmp/t09a-movement-red.txt`. Initial repaired matrix: **20 passed in 11.60s**, `/tmp/t09a-green.txt`.

After final fixture checks and adding dead WAIT/nonzero-velocity controls, the exact final **22-case matrix** was run against the original executor method in an isolated process, with no working-file mutation. The original full executor source was obtained by `git show HEAD:src/townlet/environment/action_executor.py`, hash-checked against the pre-edit file, compiled in a private namespace, and only that process's `ActionExecutor._execute_actions` was replaced with the original method. All other candidate dependencies remained current. This is an executor-delta causal comparison, not a full dependency-tree revert.

Exact comparison command (prefix above):

```bash
.venv/bin/python - <<'PY'
import pathlib
import subprocess
import pytest
import torch
import townlet
from townlet.environment.action_executor import ActionExecutor
assert pathlib.Path(townlet.__file__).resolve() == pathlib.Path('/workspace/hamlet/src/townlet/__init__.py')
torch.set_num_threads(1)
namespace = {'__name__': 't09a_original_executor'}
source = subprocess.check_output(['git', 'show', 'HEAD:src/townlet/environment/action_executor.py'], text=True)
exec(compile(source, '<original action_executor.py>', 'exec'), namespace)
ActionExecutor._execute_actions = namespace['ActionExecutor']._execute_actions
raise SystemExit(pytest.main(['--no-cov', '-p', 'no:cacheprovider', '-q', 'tests/test_townlet/regressions/bac/test_inactive_action_execution.py']))
PY
```

Result: **18 failed / 4 passed in 23.32s**, expected exit 1, `/tmp/t09a-final-matrix-red.txt`. All 18 failures are intended assertions: exact DROP; shared/exclusive GET/DROP/USE/local/inventory freeze; movement and WAIT after terminal/retirement movement; repeated USE/local/inventory terminal effects. Four original controls pass (two WAIT item controls and terminal GET/DROP, whose immediate repetition is already a no-op). No collection/setup error remains in this final causal comparison.

Fresh final candidate command:

```bash
.venv/bin/python -c 'import pathlib, pytest, torch, townlet; torch.set_num_threads(1); assert pathlib.Path(townlet.__file__).resolve() == pathlib.Path("/workspace/hamlet/src/townlet/__init__.py"); print(townlet.__file__, torch.get_num_threads()); raise SystemExit(pytest.main(["--no-cov", "-p", "no:cacheprovider", "-q", "tests/test_townlet/regressions/bac/test_inactive_action_execution.py"]))'
```

**22 passed in 12.29s**, exit 0, `/tmp/t09a-final-green.txt`.

## Owner and static gates

Combined final candidate owner command (prefix above):

```bash
.venv/bin/python -c 'import pytest, torch; torch.set_num_threads(1); raise SystemExit(pytest.main(["--no-cov", "-p", "no:cacheprovider", "-q", "tests/test_townlet/regressions/bac/test_inactive_action_execution.py", "tests/test_townlet/regressions/bac/test_successor_producer.py", "tests/test_townlet/regressions/test_episode_lane_environment.py", "tests/test_townlet/unit/environment/test_action_masking.py", "tests/test_townlet/unit/training/test_episode_accounting.py", "tests/test_townlet/integration/test_authored_episode_lanes.py", "tests/test_townlet/unit/items", "tests/test_townlet/integration/test_dead_agent_interaction_gating.py", "tests/test_townlet/integration/test_custom_item_verbs_integration.py", "tests/test_townlet/integration/test_action_costs.py", "tests/test_townlet/integration/test_items_integration.py", "tests/test_townlet/unit/vfs/test_vtc_action_writes.py", "tests/test_townlet/unit/vfs/test_vtc_interaction_progress.py"]))'
```

**313 passed in 94.75s**, exit 0, `/tmp/t09a-owners.txt`: final 22 + T09 producer 5 + B11 owner selection 80 + additional item/action/VTC owners 206. No skipped/xfail/failed result. No-default guard unit tests additionally **39 passed**, `/tmp/t09a-no-defaults.txt`.

Final scoped commands all passed:

```bash
.venv/bin/ruff check src/townlet/environment/action_executor.py tests/test_townlet/regressions/bac/test_inactive_action_execution.py
.venv/bin/black --check src/townlet/environment/action_executor.py tests/test_townlet/regressions/bac/test_inactive_action_execution.py
.venv/bin/mypy --follow-imports=silent src/townlet/environment/action_executor.py
git diff --check -- src/townlet/environment/action_executor.py tests/test_townlet/regressions/bac/test_inactive_action_execution.py
.venv/bin/python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt --ratchet .defaults-ratchet
```

Ruff clean; Black two unchanged files; scoped mypy one source file clean. Whole no-default scan: 184 files, **614 whitelisted violations at unchanged ceiling 614**, clean, `/tmp/t09a-defaults-ratchet.txt`. No ratchet/whitelist changes. Initial formatter/import-order issues were fixed before final verification.

## Limits and remaining release requirements

The snapshot assertions are named bounded witnesses, not a complete simulator-state inventory. Full-world state ownership/snapshot proof remains PW12. Shared-item controls use nonexclusive items in independent worlds; they do not assert one physical item instance can cross worlds. No new learner/population implementation was read; B11 execution corroborates existing completion ownership. No GPU, every-substrate, arbitrary external invalid-input, or exhaustive temporal/tracking-state qualification is claimed.

Fresh independent other-model adversarial review is pending. Root must create the new fixed sumtree and complete its collection, owner checks, six standing guards and full suite before any dependent release (including T15/T18e). Root stopped the obsolete wave before its full gate because of X03. This worker did not run or claim the repository-wide full pytest/coverage gate; no release self-waiver. Other ENV/AS/RND/POP/RP packets remain untouched by this worker.
