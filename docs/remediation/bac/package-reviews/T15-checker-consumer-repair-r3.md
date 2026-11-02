# T15 existing checker consumer repair R3 — stationary for root runtime/review

Root reports all R3a runtimes closed and four intended checker RED failures: three recipes reached eligible-K IndexError wrapped by the strict selector assertion; first-write control proved genuine push_recorded storage before admitted_observation=None. Root-supplied RED log SHA2560aa04ee8494d6c4776cc3cb85de697becb89368f320c0c486210c8a73c86fdf9,28.53wall. Separate checkpoint2 repaired cases PASS42.47wall are root-attributed and not reexecuted here. This worker then received explicit narrow script repair clearance. No runtime GREEN is claimed.

## Exact complete context and custody

Exactly3 whole implementation/test/helper sources,3575 physical lines, below5000. No fourth source, runner/buffer/oracle/conftest/provider/helper implementation was opened. The separate checkpoint test was not read or edited.

| Complete source | Lines | SHA256 |
|---|---:|---|
| scripts/check_episode_lanes.py — repaired |1036|19e0b83130f2467a2bfd890dc79e95de6d7694e79f7fa996fa16c66b43e62eb7|
| src/townlet/population/vectorized.py — unchanged |2146|9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a|
| tests/test_townlet/unit/oracle/test_episode_lane_comparator.py — strict R3 tests unchanged |393|5a259e6ab4236caf3d1b20323ee089522c101b4e91d8a294e2deb84595536d30|

No project import/runtime/pytest/collection, index/commit/push, branch/worktree/source checkout/copy, .oracle action or subagent was performed. The only tracked source write this phase is scripts/check_episode_lanes.py; this receipt is ignored under /.superpowers/.

## Narrow causal repair

The scripted provider callback now projects its authored full-world schedule onto independently derived actual entry eligibility ~env.dones, verifies population completion consistency, accepts actual K Q/mask/state rows, and returns only eligible scripted actions after genuine legal-mask checking. It does not fabricate masks or invoke another sampler, alter epsilon, restore inactive selection draws or modify population code.

Full-N selected_q_values capture moves to measured_step entry and consumes the real population.last_selected_q_values with required full-N geometry. The actual full-N actions reaching the original environment step remain unmodified and recorded there. Inactive argmax transport is preserved exactly rather than rewritten as WAIT or synthesized from an eligible subset. The R3 strict test compares both Q/actions and canonical total/components with that real boundary.

The same measured_step entry installs an idempotent observer on the actual current replay object after production binding and before admission. It wraps push_recorded, not the old low-level push, passes all positional/keyword arguments through unchanged exactly once, returns the original result and propagates original failures. It records matched predecessor hashes only after the genuine write succeeds. Buffer identity is checked each step so a new bound object receives its own observer; the old constructor object cannot strand observation. The per-tick seen lanes remain excluded across chunks so a duplicate row cannot silently overwrite earlier admission. Existing unknown/ambiguous identity refusals remain. Direct population recipes and runner_reset's new actual population/env closures both use this same real boundary.

No reward arithmetic, RewardTensor, successor masks, replay admission/collection, buffer construction/sampling, warmup/readiness, episode/training clocks, completion/lifecycle/reset, budget accounting, source identity, manifest schemas, coordinate inventories or comparison allowances change. Old low-level push remains untouched and supported. Existing collector.errors/semantic-verdict distinction remains as documented in the audit; no verdict policy was silently altered. No missing historical masks are reconstructed.

## Actual static verification; root runtime/review remains pending

Passed owned checks:

```text
.venv/bin/black --check scripts/check_episode_lanes.py tests/test_townlet/unit/oracle/test_episode_lane_comparator.py
.venv/bin/ruff check scripts/check_episode_lanes.py tests/test_townlet/unit/oracle/test_episode_lane_comparator.py
```

Strict regression test hash is unchanged from the root-observed RED. Root should rerun the four causal nodes through its verified no-new-checkout import/fixture harness, then the complete comparator and affected/full gates, with fresh Astra review of actual source. Synthetic identity fixture remains explicitly UNIT provenance; it does not qualify a clean committed standalone capture. Preserve original RED/test SHA/tree bindings.

## Exact native-only capture handoff after required gates and local clean commit

Keep source_identity's clean committed-source requirement. Root first completes required owner/static/full-repository gates, locally commits the exact candidate tree, and checks clean execution-bearing source. Then native capture runs against that new real commit before push/publication qualification. No allow-dirty bypass, identity flag, reference checkout, automatic oracle utility or new worktree is authorized. The existing native pack is configs/test/episode_lanes. Existing output directories must be preserved; choose a fresh explicit suffix on rerun. Ensure the explicit TMPDIR exists through root's normal artifact setup.

```bash
cd /workspace/hamlet
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/workspace/bac-review-2026-11-01/tmp /workspace/hamlet/.venv/bin/python -P /workspace/hamlet/scripts/check_episode_lanes.py capture --source-root /workspace/hamlet --config-root /workspace/hamlet/configs/test/episode_lanes --recipe authored-two-five --output /workspace/bac-review-2026-11-01/t15-checker-authored-r3
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/workspace/bac-review-2026-11-01/tmp /workspace/hamlet/.venv/bin/python -P /workspace/hamlet/scripts/check_episode_lanes.py capture --source-root /workspace/hamlet --config-root /workspace/hamlet/configs/test/episode_lanes --recipe two-episodes-reset --output /workspace/bac-review-2026-11-01/t15-checker-reset-r3
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/workspace/bac-review-2026-11-01/tmp /workspace/hamlet/.venv/bin/python -P /workspace/hamlet/scripts/check_episode_lanes.py capture --source-root /workspace/hamlet --config-root /workspace/hamlet/configs/test/episode_lanes --recipe budget-six --output /workspace/bac-review-2026-11-01/t15-checker-budget-r3
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/workspace/bac-review-2026-11-01/tmp /workspace/hamlet/.venv/bin/python -P /workspace/hamlet/scripts/check_episode_lanes.py capture --source-root /workspace/hamlet --config-root /workspace/hamlet/configs/test/episode_lanes --recipe passive-two-five --output /workspace/bac-review-2026-11-01/t15-checker-passive-r3
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/workspace/bac-review-2026-11-01/tmp /workspace/hamlet/.venv/bin/python -P /workspace/hamlet/scripts/check_episode_lanes.py capture --source-root /workspace/hamlet --config-root /workspace/hamlet/configs/test/episode_lanes --recipe death-at-lifespan --output /workspace/bac-review-2026-11-01/t15-checker-death-r3
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/workspace/bac-review-2026-11-01/tmp /workspace/hamlet/.venv/bin/python -P /workspace/hamlet/scripts/check_episode_lanes.py capture --source-root /workspace/hamlet --config-root /workspace/hamlet/configs/test/episode_lanes --recipe healthy-retirement --output /workspace/bac-review-2026-11-01/t15-checker-retirement-r3
```

Root must validate every capture's contract.qualified=true and errors=[] plus exact inventory and genuine new source stamp/import/config/action/instrument identity. capture exit0 alone does not require qualification. Preserve full-N actual action differences and strict manifest comparisons; do not rewrite old artifacts or classify synthetic unit metadata as clean capture. No capture command above was run by this author.

Return stationary for root execution and fresh actual-source review.
