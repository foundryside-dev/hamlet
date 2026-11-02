# T15 independent adversarial runtime r2

**PASS: four selected cases, zero failures.** Actual job result JSON reports exit0 and58.44433879852295 seconds harness wall; pytest log reports4 passed in52.72s. This closes the selected independent runtime disposition accompanying the scoped R1 source/spec approval. No new material finding arose. Broader T15 qualification and whole-BAC acceptance remain open.

## Exact execution and identity

Executed only the cleared command from `/workspace/hamlet`:

```text
env TMPDIR=/workspace/bac-review-2026-11-01/qualification/scratch/tmp-wave08-r3 python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave09-astra-main-r2-spec.json
```

Read the spec data, actual result JSON, full test log and all three process identity JSONs after completion. Did not infer success from the outer wrapper exit. Result: `/workspace/bac-review-2026-11-01/qualification/wave09-astra-main-r2/independent-main-result.json`. Log: same directory `independent-main.log`, SHA256 `ebc14d0457c43c8450e9166336199a2d60b34fe238814d10ec2da648bb8fd1c2`.

Frozen global candidate tree `929bc8952a2e797871d15376e2ef61a8aec73ca5`, HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`. Manifest SHA256 `dc2881963a1b4871bb45d6459d618db56bfde636af11a3a28c8ee8b0f524b5e3`; harness SHA256 `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`. Controller, gw0 and gw1 independently record that exact HEAD/tree, imported module `/workspace/hamlet/src/townlet/__init__.py`, Torch2.11.0+cu130, and one Torch thread each. Pytest used two workers with worksteal and the explicit workspace basetemp from the spec.

The four actual collected/executed nodes, all within `tests/test_townlet/regressions/bac/test_learner_legality.py`:

- `test_load_before_first_step_adopts_current_replay_and_clocks[load-active-current-feedforward-True]`
- `test_load_before_first_step_adopts_current_replay_and_clocks[load-active-current-recurrent-True]`
- `test_recurrent_one_window_readiness_distinguishes_laws[successive_without_replacement-0]`
- `test_recurrent_one_window_readiness_distinguishes_laws[independent_with_replacement-1]`

## What passed

The feedforward current-PER case now satisfies storage disjointness, saved-input/eager-optimizer immutability and exact paired continuation after the original optimizer-alias failure. The recurrent current-PER case reaches the formerly blocked archive/load path and passes the same strict ownership, actual sampled-batch, RNG, model/state and clock assertions. Both use the actual population loader and retained current history.

The new L3/min1/B2 recurrent contrast passes with retained3/sampleable1: successive performs no sampler draw or optimizer/scheduler/target advancement, while replacement draws two real copies of the one window and changes actual network parameters. Both preserve the required vector-tick/beta pacing and exclude pending collector rows from retained sampleability. No tolerance, objective or preservation requirement was weakened.

Spec and code-quality dispositions from R1 remain APPROVE for the inspected repair scope. Independent selected-runtime disposition is now PASS. These four cases do not replace the complete owned suite, affected B03/owner suites, six guards or required full G2. Root's separate L2/L8 BPTT runtime was concurrent and is not claimed passing by this reviewer.

## Post-run whole-source receipt

The exact five inspected sources remain unchanged from R1, **5 files/3940 lines**, verified by fresh post-run hashes:

| Source | Lines | SHA256 |
|---|---:|---|
| src/townlet/population/vectorized.py |2146|9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a|
| src/townlet/training/replay_contract.py |222|3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c|
| src/townlet/training/q_targets.py |80|39485fe2447dc4065bd7b806775c93c0e66b51827b088605fba98505b100491f|
| src/townlet/config/bac_options.py |294|10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916|
| tests/test_townlet/regressions/bac/test_learner_legality.py |1198|5f6273a8054bde34f89ab77eb98c8b4c0bb9428b586511b976cecae19c33e71e|

No wrapper, identity-plugin, BPTT-test, provider, buffer, network, fixture, conftest or other sixth source was opened. No custom probe, source/index/tracked edit, branch/worktree/source copy/deletion/subdelegation/commit/publication occurred. Root reports the cleared global manifest guards151 source paths,573 configs,13 artifacts and14 worktrees; this report records the executed harness and observed process identities without inventing an additional whole-repository review. Only this ignored prose receipt is newly written; R0/R1 review history and failed causal evidence remain intact.

Full ICM transition-context reward/update/continuation/E2E remains REQUIRED OPEN T18e/T18f; the selector sentinel retains its narrow meaning. Full native continuation remains T24/T25. Fresh final22 lenses/synthesis, all54 requirements, learning/E2E, coverage>=70%, slow/applicable hardware, finite T40 and exact-tip remote CI remain owed.
