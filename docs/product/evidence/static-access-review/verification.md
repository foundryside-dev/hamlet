# Static-access review repair — local verification receipt

Date: 2026-10-01
Branch: `fix/static-access-review`
Final execution source: `7eb7ded3b2f9aa625828a02fe751713e0eed4c9f`
Preceding repair: `c3faa4bfa9c4b7a391f530e8c97a45cded908cb3`
Base: `792c6704c84812adb24d20a5d75553aaee261648` (documentation-only after published `72977928`).
Tracker: `hamlet-f75ff623be`, `hamlet-bae419a592`, `hamlet-940089c925`.

## Local gates

| Command / scope | Reading |
| --- | --- |
| `.venv/bin/pytest -q` | 4,295 collected; 4,277 passed / 18 skipped / 15 warnings; 85% coverage; 989.23s, exit 0; no marker exclusion; execution tree unchanged from final source |
| `.venv/bin/python -m pytest tests/test_townlet/unit/items tests/test_townlet/unit/effects tests/test_townlet/integration/test_effect_cascades.py tests/test_townlet/integration/test_items_effects_cascade.py tests/test_townlet/regressions/test_effect_cascade_state.py tests/test_townlet/regressions/test_effect_spawn_denial.py -q --no-cov` | 397 passed, 1.70s, exit 0; subagent tool result, session 77301/chunk 76ac16; no original log file |
| `.venv/bin/pytest --no-cov -q tests/test_townlet/unit/universe tests/test_townlet/unit/oracle tests/test_townlet/integration/test_effects_compilation_pipeline.py tests/test_townlet/integration/test_effects_compiled_catalog.py tests/test_townlet/integration/test_static_epistemic_access.py tests/test_townlet/integration/test_static_epistemic_checkpoint_identity.py` | 988 passed, 155.02s, exit 0; before final allocator follow-up; declaration cases replayed after full-compiler assertions were added |
| `.venv/bin/ruff check src tests` | Passed, exit 0 |
| `.venv/bin/black --check src tests` | 576 unchanged files, exit 0 |
| `.venv/bin/mypy src` | 179 source files, exit 0; two existing annotation-unchecked notes |
| `.venv/bin/python scripts/no_defaults_lint.py src/townlet --whitelist .defaults-whitelist.txt` | Clean, 695 existing whitelist matches; 122 patterns unchanged; exit 0 |
| `.venv/bin/python scripts/validate_compiler_cli.py` | All shipped packs/levels validated; negative fixtures refused as expected; exit 0 |
| `git diff --check` | Passed, exit 0 |

Two earlier full-suite attempts were intentionally interrupted for independent
counterexample repairs. Neither is counted as a passing suite.

Existing skip scope was checked against the completed log and source: seven CUDA
hardware tests, six substrate DTO validation cases, two deferred expression
type-checking cases, two explicitly flaky episode/runner cases, and one fixture
lacking a `Bar` affordance. Total 18. No marker filter conceals these cases. Their skip count does not
establish those unresolved contracts or CUDA acceptance.

## Test-first and independent checks

Direct admission/reapplication regressions exposed seven failures before pipeline
preflight. Discovery/symbol/provenance probes exposed false collisions and a wrong
clock-origin diagnostic while genuine duplicate cases still refused.

Direct child preflight still left a live parent after nested refusal. Durable tests
verify restoration of bars, VFS arenas/private tensor aliases, active effects,
scheduled work, real item spawning and affordance availability. Successful dynamic
targets observe prior writes and sample once. Independent review found disabled
item services and compiled SWITCH branches; both counterexamples failed before
correction and pass after it. Paired histories exposed the hidden free-slot cursor;
deterministic lowest-free allocation preserves the subsequent public item/row result.

## Retained local logs

Files are under `runs/static-access-review/2026-10-01/` (ignored runtime artifacts).
These digests identify original captured logs, except the 397-case result above,
which is explicitly a transcribed tool-result receipt.

| File | SHA-256 |
| --- | --- |
| full-suite.log | 93b382e138e452195786fab751c8e428290890eef7cd0db4dda70b93913024bd |
| main-checks.log (subsequent local merge) | 2d129ce2ddc4735f31685288762e526bb254d60a34449a5472fe65398cdc5562 |
| compiler-focused.log | 88a7ca1ce56b09bfb4b10f46f02bac2a160fcf7cef514afb23411b5b36085de0 |
| runtime-focused.log (earlier 293 cases) | 0699b197cb8b9228c6d7430f31c4dccd524185de86d211f9d526af172ef47193 |
| ruff.log | 82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18 |
| black.log | 5d057f50391b96bdab5e004755400fa240f66cdc614b54f09739db463bc90fe4 |
| mypy.log | 1a9288e80a0713630312193466232610d5c07840c3f5c8396b9c514a49bad1a9 |
| no-defaults.log | b3d6a8601fbc82cff1eed7530664d8859ded646eafce50de20dff8b543206845 |
| fleet.log | 5fa530459a1ad0a70ea2ec0ce2dd4bf651d6f001edb876d15abad7aa9b3b6912 |
| review-counterexample-red.log | 53f5f02a45c80182ddac6de201a2d98a8942f1f85037ed726b20abe300d6ddae |

Both unrelated dirty skill files retain SHA-256
`27b0487e302939f67d6e1e2a4e1b66b531904944e9bf41b88e8c125e2ec0846a`:
`.agents/skills/filigree-workflow/references/error-codes.md` and
`.claude/skills/filigree-workflow/references/error-codes.md`.

## Acceptance limits

At the original branch qualification, no push, main merge, hosted CI, release or
deployment was performed. The subsequent owner-requested local integration is
recorded below. No new learning/convergence campaign or frozen
trajectory qualification is claimed. Item allocation after reuse intentionally
changes to the lowest available row. Cascade capture is linear in supplied state;
its performance is unmeasured. New rollback regressions exercise CPU; initialized
CUDA RNG restoration is implemented but not independently exercised here.
Future delayed execution and whole ticks are outside immediate admission atomicity.
Recovery and PDR-0058's fired exit review remain open.

## Subsequent owner-requested local integration

The owner requested: "please merge it onto main". After refreshing `origin/main`
(still `72977928`), local main fast-forwarded from `792c6704` to
**`a370814ab446af04afe5274772eb2799499d9e10`**. Its tree exactly matches the
qualified repair branch; execution remains unchanged from `7eb7ded3`. Actual
imports resolve to `/home/john/hamlet/src/townlet`.

Fresh post-merge checks: **432 passed in 11.95s, exit 0**. Scope: all item/effect
units, declaration-edge compilation cases, both cascade integrations, static
write-intent runtime and both denial regression modules (`--no-cov -q`). The
4,277-case full pass above is retained qualification, not a new merge-time full run.

At integration, both unrelated dirty paths retained their original contents, modes
and dirty status.
The merged task branch was retired after successful verification. The primary
checkout, other worktrees and raw evidence are retained. No push was performed;
there is no new hosted CI reading. A documentation-only follow-up records this
integration without changing qualified execution code.

The owner then explicitly requested committing the two changed reference Markdown
files. Commit **`80d6a5ce6f0ec4b04ee9ef461f8b687a5c2d0f71`** includes exactly
`.agents/skills/filigree-workflow/references/error-codes.md` and
`.claude/skills/filigree-workflow/references/error-codes.md`. Their file contents
remain at the custody digest above; only their Git status changes to committed.
No runtime code changes or new test claims follow from this documentation commit.
