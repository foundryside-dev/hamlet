# T16 affected-consumer fixture repair R4 — runtime pending

Implemented root's explicitly cleared two-test-file correction in `/workspace/hamlet` on 2026-11-02. No production source, YAML, budget, existing assertion or scenario changed. The prior read-only audit is `T16-consumer-failure-audit.md`; its final addendum records root's acceptance and repair clearance.

## Observed prerequisite and scope

The supplied R3 failure records were read and deduplicated to four unique nodeids. Root then closed the 266-item affected suite with **4 failed,261 passed,1 skipped**,587.0036 harness wall seconds. The completed original log independently reports those same counts and581.58 pytest seconds. Root supplies original log SHA256 `e2f632b2e87f97ba215cb7a56439b593478d1de54ffa12cb97e2f614a8212efd` and preserved custody in `failed-custody.json`. Original candidate tree is `0bdd6133f2224b25bce5668e15021fa1353accba`; base/HEAD is `f575ecefda7844fbd5b7b6138ad0c6bf7b1bafd8`. No new candidate tree or index was generated here.

Source tracing established why the actual fixtures failed before any repair: the sink fixture's reset-time mutation no longer reached RR's canonical runtime training copy; the hyperparameter observer patched __init__ while the accepted for_training seam bypasses it. Root accepted that no named public per-episode cap API was removed, and required preservation of the distinct caller-cap3/authored-world-lifespan10 scenario.

The systematic-debugging, TDD/writing-good-tests and verification skills were read. The already executed original tests and exact recorded failures supply the prerequisite failure evidence. Root's explicit AST-only/no-runtime clearance overrides generic local rerun/full-suite/commit workflows. The proposed correction was already written in the audit and explicitly accepted; no new design/permission loop or scope change was introduced.

## Actual changes

`tests/test_townlet/regressions/test_episode_lane_sinks.py` now imports the already visible real `build_curriculum` symbol from the approved runner module. A fixture observer retains `training_config.training_loop` from the actual RR422–426 call, forwards every argument to original build_curriculum exactly once, and returns its real result. The existing reset-time cap injection targets that retained runtime-copy loop object. A single additional assertion requires that capture to have occurred before cap injection.

This preserves the original timing and scenario: the real authored environment, curriculum, exploration and population are initialized from lifespan10; reset checks `env.agent_lifespan == 10`; the caller then caps only the actual RR loop at3. The canonical effective carrier/hash and compiled training remain unchanged. Real compiler, environment steps, networks, replay rows/masks, completion, DB/TB and curriculum publication still run. The no-cap, budget6, budget1, real-DAC and final-meter cases retain their original setup and test bodies. No end_ticks, episode count, budget, authored YAML or expected value changed. The already-built beta upper-bound horizon remains the declared10-tick horizon, matching the timing of the original late fixture injection.

`tests/test_townlet/integration/test_runner_hyperparams_v21.py` moves its capture-and-stop observer from __init__ to public `for_training`, installed as a classmethod. The observer lists every actual required keyword-only input from POP198–223 and invents no defaults. It records the same train_frequency/sequence_length/max_grad_norm and raises the same `stop-after-population-init` sentinel before real initialization. The unchanged DummyEnv therefore remains within the original forwarding-only test scope; no fake token_spec or weakened production guard was added. All authored7/5/3.5 values and original pytest.raises/numeric assertions remain.

The cap completion/publication and bootstrap assertions remain the independent behavioral oracle. The hyperparameter test remains the existing construction-boundary forwarding observation; this repair does not claim a new real-initializer integration guarantee.

## Exact five-source custody

Complete context remains exactly **five sources**, now **3758 physical lines** (entry3743; net test growth15). No sixth helper/test/probe/source was opened or created.

| Source | Entry→current lines | Current SHA256 |
|---|---:|---|
| `src/townlet/demo/runner.py` |1017→1017|`e1c4b6c00923416f6fdf9e70976ea57a4a706e38a2ea228b4b10273906d6aacf`|
| `src/townlet/population/vectorized.py` |2146→2146|`9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a`|
| `tests/test_townlet/regressions/test_episode_lane_sinks.py` |304→312|`e6631eb7e2375165a1e1131eaf88999e8debb024d37ef736bf9eadcdacd3fbde`|
| `tests/test_townlet/integration/test_runner_hyperparams_v21.py` |119→126|`237ca50b9deb1e585c7d37d1134896b4fe1a29dde12b4de7a401210e317c4db0`|
| `tests/test_townlet/regressions/fixtures/episode_lanes.py` |157→157|`9de34aa9764fe2cef766aace4e6ebd391543621fa90def16b5614292e476ec7f`|

Pre-repair SINKS SHA256 was `29b8fd697fd11e55c6d0a28de2ecba119f933d3cb8276d36f6502e35bbf0e79b`; pre-repair HP was `ced5b1cb1a4d239112d2dadf24df3876aca08bcf758e0e611e8716483e72584c`. RR, POP and LANES hashes remain unchanged.

## Locally executed verification

One isolated standard-library `python3 -I -B` AST-only command read the same five sources and the existing HEAD versions of the two edited paths directly into memory, without source copies or project imports. Exit0 with these complete results:

- AST parsing passed for all five approved sources.
- All seven top-level SINKS test-function bodies and decorators match their original AST exactly. Parameterization, original assertions, helper-call scenarios and budgets are unchanged.
- All66 original SINKS assertion ASTs remain; the sole addition is the non-None runtime-loop capture assertion.
- All three HP assertion ASTs match their originals exactly.
- The HP observer's keyword-only argument names/order match the real for_training signature exactly, and every observer keyword-only default is absent.
- The curriculum observer's AST contains exactly one call, to the captured original build_curriculum. Its source forwards original positional/starred/keyword arguments and returns that call's result.

The complete two-file diff was read, and all five current hashes/counts above were read after the edit. Syntax and AST preservation are not runtime GREEN. No project imports/runtime, pytest/collection/compiler/linter/formatter, benchmark or additional diagnostic probe ran locally.

## Root-owned handoff

Root will run the exact same four failures first: both `test_caller_cap_keeps_authored_terminal_and_live_bootstrap` parameters, `test_caller_cap_completes_lanes_before_curriculum_publication`, and `test_demorunner_threads_training_loop_hyperparameters`. Bounded independent review, affected owners/static guards and required G2 qualification remain root-owned. This receipt claims only the source edit and the executed AST preservation checks, not a tested fix, suite PASS or repository GREEN.

Only the two explicitly cleared test files and the two requested ignored audit/repair receipts were written. The audit destination was verified ignored through `.git/info/exclude:7` `/.superpowers/`. No production/config/tracked-document/index/tracker edit, branch/worktree/project checkout/source copy/deletion, commit/push or subdelegation occurred. No operation changed any of the14 existing checkout records. Stationary now; no further source/runtime work follows without root clearance.
