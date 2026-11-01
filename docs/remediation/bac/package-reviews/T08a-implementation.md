# T08a implementation receipt — frozen for independent review

- candidate_sha: base `050a1a70e979aa03724219b81e848093820f044f` plus the three owned uncommitted files below; no stage/commit/push.
- scope: exact-zero illegal sampler weights and explicit producer eligibility, preserving existing direct API and dead transport. T15/T18d production wiring remains owed.
- actual source inventory: action_selection.py 120 lines W; q_targets.py 80 R; new test_action_probabilities.py 90 W; existing test_epsilon_greedy_selection.py 148 W. Four files, 438 whole-file lines. No other implementation/test/helper source read. Existing execute-only suites do not expand read inventory. Fifth reviewer probe slot unused.

## API and behavior

`epsilon_greedy_action_selection(q_values, epsilons, action_masks=None)` retains its signature and legacy all-false unmasked-argmax transport semantics. It does not know membership and cannot diagnose live-empty rows. Empty-mask rows now stay outside multinomial entirely; valid rows normalize only their true mask entries, with illegal entries exactly zero.

Added `epsilon_greedy_action_selection_eligible(q_values, epsilons, action_masks, *, eligible)` with required bool[N] producer membership. Rejects eligible empty masks before sampling even at epsilon zero. Inactive rows return unmasked argmax transport and consume no random draws. `action_masks=None` explicitly permits unconstrained selection. Producer must supply actual membership, not infer it from empty masks. No EPS/RND/POP/environment caller edits. T15/T18d must wire this entrypoint or equivalent truthful filter/select/scatter.

## Evidence and commands

Direct installed Python also asserted `torch.get_num_threads() == 1` under the same thread environment. All tests ran from `/workspace/hamlet`, with `PYTHONPATH=/workspace/hamlet/src`, `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=`. Existing installed environment used via `UV_NO_SYNC=1 UV_CACHE_DIR=/tmp/uv-cache uv run`; initial plain uv launch failed on read-only cache, then cache override without NO_SYNC attempted unavailable hatchling network resolution. Those setup failures are not red evidence.

Root import assertion before causal red verified `townlet.__file__ == /workspace/hamlet/src/townlet/__init__.py`; pre-edit AS SHA256 was `c5362a5078c7ecce9dfac0727364a346988054e83228975abaf0939369d48d3e`. Final root and action_selection import paths plus final AS hash explicitly asserted. Root HEAD stayed at the above base. Concurrent ENV work means this is bounded mutable-worktree evidence, not whole-repository identity evidence; root owns immutable snapshot checks.

- focused_commands: `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_action_probabilities.py -q` with the environment above. Red: 11 failed; actual native sampler input was `[[1e-8,1]]` instead of exact `[[0,1]]`, legacy dead rows leaked into sampler batch, and new eligibility API was absent. Green: 11 passed (0.07s). Logs `/tmp/t08a-red.log`, `/tmp/t08a-green.log`.
- owner_suite_commands: `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/unit/exploration/test_epsilon_greedy_selection.py tests/test_townlet/unit/exploration/test_exploration_strategies.py tests/test_townlet/unit/exploration/test_rnd_normalization.py tests/test_townlet/unit/exploration/test_rnd_stats_update_timing.py -q` with same environment: 74 passed (4.54s), `/tmp/t08a-owner.log`.
- static_commands: scoped `uv run ruff check` on three changed Python files passed; scoped `uv run black` unchanged; scoped `uv run black --check` passed (3 files unchanged). All standing repository static commands delegated to root's immutable gate, not claimed here.
- review_record: pending fresh independent review by root.
- full_suite_status: not run by worker.
- full_suite_reason: shared mutable worktree with concurrent ENV writer; coordinator must assess existing behavioral/public-contract early-full trigger and qualify immutable candidate.
- unrun_checks: repository-wide Ruff/Black/mypy/defaults/compiler/doc guards, full pytest and coverage/hardware gates; coordinator-owned.
- next_full_gate: root earlier-trigger assessment before dependency release, otherwise mandated G2; focused evidence is not repository green.

Tests directly capture real torch.multinomial input for both APIs; cover epsilon0/1, mixed per-lane epsilon, true live-empty rejection, dead empty transport, inactive nonempty masks excluded from all sampling, explicit unmasked selection, and malformed eligibility shape/dtype. Existing DEAD fixture now states eligibility explicitly alongside preserved legacy behavior. No rare-event sampling claim.

## Frozen SHA256

- `src/townlet/exploration/action_selection.py`: `2a2ddfbd9aaf01afa14b0d1907fa1f3c8823f253dcdc8d16a8ff4054bf3768b8`
- `src/townlet/training/q_targets.py` (read-only): `39485fe2447dc4065bd7b806775c93c0e66b51827b088605fba98505b100491f`
- `tests/test_townlet/regressions/bac/test_action_probabilities.py`: `e5e5813fdb3a9da2fba4eaea2ca5d1815dc6aa08507a6cd78bd746aab7c57241`
- `tests/test_townlet/unit/exploration/test_epsilon_greedy_selection.py`: `a777035e3356a145c15d2c6140f13cb5a943bfc30db35292ca5f4c743011c636`


## Gate repair 1 — defaults ratchet, refrozen

Independent review of the initial candidate passed, but the standing defaults guard found 615 whitelisted violations against ceiling614. Root stopped before expensive full-suite launch. Reproduced using `UV_NO_SYNC=1 UV_CACHE_DIR=/tmp/uv-cache uv run python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt --ratchet .defaults-ratchet --show-whitelisted`: AS115 ASG002 conditional assignment introduced the additional count (`/tmp/t08a-defaults-red.log`).

Replaced only that assignment with an ordinary explicit if/else. No semantic, whitelist, ratchet or policy change. AS now120 lines; full read inventory438 lines. The frozen AS hash above is the repaired version; other file hashes unchanged.

Repair verification used installed `/workspace/hamlet/.venv/bin/python -m pytest` with the same PYTHONPATH and one-thread environment above. Focused exact regression:11 passed (`/tmp/t08a-repair-green.log`). Same B05 owner command:72 passed,2 failed (`/tmp/t08a-repair-owner.log`), in `TestRNDCheckpointCompleteness::test_rnd_restores_network_weights` and `::test_rnd_restores_optimizer_state`; both report `ValueError: RND Adam history does not match versioned service optimizer updates`. This is current shared-tree evidence, superseding the initial74-pass result for the current combined tree. No additional RND or test source inspected; root notified to coordinate separate RND repair/snapshot qualification.

Whole `/workspace/hamlet/.venv/bin/python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt --ratchet .defaults-ratchet` passes at614 (`/tmp/t08a-defaults-green.log`). Scoped Ruff and Black checks on all three owned Python files pass. Remaining standing static/full gates remain root-owned. Same independent reviewer must review this narrow branch rewrite before release; current owner-suite failure is explicitly unresolved by T08a.
