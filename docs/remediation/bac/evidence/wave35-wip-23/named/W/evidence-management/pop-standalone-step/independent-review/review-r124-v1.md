# Independent R124 POP standalone step/cleanup review

**REQUEST CHANGES — the planned prerequisite is not yet accepted.** Two P2 findings remain. The three caller edits themselves match the accepted standalone supplier contracts; eight new cleanup cases and ten original handoff cases pass. The complete required selection is **21 PASS / 2 FAIL**, not a 23-case green gate. No P0/P1 defect identified in this bounded delta.

Reviewer: `/root/bac_astra_wip22_terminal_review`; implementation producer: `/root/bac_pop_standalone_step_prepare`; runtime producer: `/root`. This is a fresh actual source/design review, distinct from the earlier terminal WIP22 evidence review. Exact source/independence/evidence references are in `independence-source-inventory-r124-v1.json`.

## Findings

**R124-1 — P2: reconcile failed-step diagnostic export with genuine quarantine.** Correcting POP2115 to `runtime_failure` now completes real runtime/BANK quarantine, as required. But POP `get_checkpoint_state` still permits `_has_failed_step_diagnostic()` and then calls the healthy-only `exploration.checkpoint_state()` at2507. The required existing pace case at `test_parent_intrinsic_handoff.py:543` reaches this export and fails with `RuntimeError: curiosity bank quarantined`. I predicted this from the owned POP source and exact C1 supplier contract before reading the completed run; the original trace confirms it. Failed-progress/clock/nonreexecution assertions preceding export pass, but portable diagnostic and nonrestorability assertions after it do not run.

Resolve the diagnostic contract explicitly while retaining genuine quarantine, truthful failed progress and refusal to install failed work. A failed diagnostic must not be relabeled a healthy child checkpoint, bypass BANK health, restore the old invalid reason, or simply delete the intended diagnostic/nonrestore assertions. The current three-edit plan overlooked this consequence; green focused cleanup alone cannot close its unchanged original gate.

**R124-2 — P2: the required A-only representative still has an obsolete standalone sample witness.** The actual traceback at `test_initial_participation_population.py:301` shows its own `sample_batch(ReplayRequest(...))` omits required `lineage`, so the test fails before its remaining replay/isolation/next-cycle assertions. Two genuine A-only steps, two retained transitions and one optimizer update have already passed their preceding assertions, demonstrating that the production `_learn` repair is reached. This is a remaining fixture-interface omission rather than evidence that production sample still fails. Migrate that standalone witness under its separately authorized file scope, preserving every behavioral assertion and genuine step/readiness choreography. This reviewer did not open that773-line body; the location and causal sequence are attributed to the preserved original execution trace. There is available numerical budget for a later authorized addition, but no such source read or edit was inferred here.

## Source and contract assessment

R124 base `23701174e5418aca5e8fc90cbe694f773d3ebff6`, candidate tree `dcca172ecf66991adab06ae2ea7e7c5c1714cf87`, manifest SHA256 `f63c225e8d12669906f89cc78fef468cd6da01ddcdab01d18ca859d2fcb0e25c`.

| Charged body | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/population/vectorized.py | 3163 | ea05fddb584cc7836e663e2aa2cada3c4dca1fcbc08584e030efa1816ac4bf38 |
| tests/test_townlet/regressions/bac/test_parent_intrinsic_handoff.py | 791 | 2621285b5d259be7f4bf8eb5e7b2ae1d2eb29c867923a7e2aa043c9e6246f7ef |
| tests/test_townlet/regressions/bac/test_population_standalone_step_cleanup.py | 102 | d59505029082a518f888bdc5937a6e23fbb56aac1681d2ce901e504ed6b37509 |

This packet charges4056/three whole bodies; the prior115-line metadata helper makes cumulative4171/four, below5000/five. I inspected the owned producer control flow and tests, exact Git delta, plan and handoff. No other APP implementation bodies were opened. The replay/core, recurrent and runtime/BANK quarantine interfaces are attributed to the plan's exact sealed suppliers, not claimed independently re-reviewed here. Current R124 source/config/protected inventories all rehash without mismatch. The handoff SHA256 is `2102102034f2df397ff87e5efccdc3e8ecd4a4e2e47e46259b6ad55449df2b51`.

POP800 now passes explicit `lineage=None` to admitted sampling after actual readiness; no default, ambient authority, altered readiness or parent capability is introduced. Fresh `for_training` binds its actual replay so the ordinary fixture avoids the separate constructor/rebind adaptation path. Sample failure remains before optimizer mutation; normal success retains existing sample/reward/ledger/update assertions. The existing parent-handoff witness adds only the same explicit standalone argument.

POP2115 now passes the supplier's accepted `runtime_failure` reason with the genuine accepted identity. The surrounding handler retains reached-stage progress, `_failed_step`, separate ordered runtime and ENV cleanup attempts, secondary-error notes and bare re-raise. This is ordinary admitted episode quarantine, not a callback-free common-poison completion consumer. No active-parent, device or restore authority is gained.

The new tests use genuine reset/activation, actual ENV physics and actual replay sampling. The physics seam fails after real physics and before replay; the sample seam delegates a successful sample before raising the same retained primary object. Required-keyword wrappers expose omitted lineage instead of accepting it silently. Shared/per_world and cleanup-ok/cleanup-raises make eight distinct cases. Secondary cleanup injection occurs only after genuine runtime/BANK quarantine completes, and ENV abandonment must still finish. Assertions cover exact accepted identity/reasons/order, primary object identity, notes, stage/tick/replay cut, unchanged Q parameters, zero optimizer count, healthy checkpoint refusal and refusal before second physics/cleanup. These are causal assertions, not fabricated authority or tests of a mocked successful producer.

## Actual validation and limits

R123 retains nine FAIL/one PASS, custody PASS: original shared-none and four sample cases expose omitted lineage; four physics cases expose the invalid cleanup reason; original ENV-stage control passes. R124's exact original shared-none representative passes first with custody PASS. Its result overlaps the subsequent23 selection and is not added as a24th unique case.

The complete R124 selection finishes **21 PASS / 2 FAIL**, exit1, 21.422716290006065 seconds outer job duration (pytest summary16.88s). Root negative custody reports source/index/import/thread/fixture PASS,822 source guards,573 configs,13 protected artifacts and three process identities for two xdist workers. The eight new cases, ten original family/scope handoff cases and three nonpace partial-failure cases pass; pace diagnostic and A-only witness fail as above. The original result/log hashes and negative custody are retained. This reviewer performed no application execution or new adversarial probe; actual root regression failures already substantiate both findings.

Global Ruff, three scoped Black checks and defaults600/600 PASS; global mypy remains FAIL with12 errors in two files. All six static log hashes were checked against their records. The decrease from15 diagnostics is not a green global type gate. Author's earlier cache-startup and formatting failures remain in its handoff.

Required standalone constructor/rebind/restore lifecycle, ENV/parent/cohort integration, recurrent/runner/CUDA work and the unchanged full C1 owner gate remain OPEN. R121215 FAIL/266 PASS is not rerun or waived here. Repair/reconcile the two demonstrated blockers and execute the preserved causal cases and full unchanged intended selection before accepting this prerequisite. No APP, public documentation, index, Git, branch, worktree, source-copy or deletion action was performed by this reviewer.
