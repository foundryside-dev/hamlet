# Independent N1 owner consumer alignment SPEC + QUALITY review

2026-11-10. Reviewer: bac_astra_n1_owner_alignment_review. **SPEC: PASS. QUALITY: PASS for the exact bounded test-alignment patch.** No blocking or nonblocking code defect found in this alignment. This is a static review verdict, not an owner runtime GREEN or whole-program closure.

Read repository AGENTS.md first. Its current-generation-only rule supports replacing the obsolete exact expectations directly. Read the preparation/sealed-writer report and canonical patch. Obtained file metadata before source bodies; inspected all five complete bodies, rereading the truncated RND test portion. No sixth source body, imported implementation, fixture/configuration body, helper reflection, source copy, checkout, worktree, branch, index mutation, project import, runtime, pytest, probe, compilation or formatter was used. Only this ignored review prose was written; git check-ignore confirmed its ignored destination.

## Exact reviewed identities

| Source | Lines | SHA256 |
| --- | ---: | --- |
| tests/test_townlet/regressions/bac/test_rnd_service.py | 635 | ee37f0b02c5a5fea42ba067d53ecc9242b6209e51018081482c7a5e49c0ec381 |
| tests/test_townlet/regressions/bac/test_icm_provider.py | 353 | 65ed02515abae732e99fb922c8a26137ef063522b207aaa41ad4023904a9860b |
| tests/test_townlet/regressions/bac/test_pw_backend_factory.py | 530 | 565c9279a86d3da3d1998762289c0a20f3b3823c5ccfd0f4770d32a708092061 |
| src/townlet/exploration/rnd.py | 910 | 30d3e9fba6ae6f90ffdda425c986bd6abecaf70e3728bdf104ca21ca832adc78 |
| src/townlet/exploration/icm.py | 541 | f6cdecb466ac99b4dfe63ec00417495c3117e8947c5793e54c0dd71aa76d4964 |

Total: five source bodies / 2969 lines, below five / 5000. Canonical T18e-N1-OWNER-CONSUMER-ALIGNMENT.patch SHA256: c7ffaf044dff8c5f910fe17fcc16f217a53e245ec3e7858c51d9b9abf2f522e3. Independently read the actual two-test working-tree diff and hashed its output: identical SHA256. The complete actual diff contains exactly two hunks: three literal substitutions and two assertions. Factory and production identities match the supplied frozen inventory.

## Specification and source evidence

RND checkpoint_state at rnd.py:554 emits rnd-state-v3; its predictor_service emits exact version 3 and origin. _prepare_state at :740 requires the current exact schema; :746 onward requires exact service fields and exact integer version 3. Origin at :777 must be an exact int with 0 <= O <= U; Adam S = (U-O) + signed optimizer_step_offset. Constructor :228 initializes O=0. prepare_learning_reset at :834 validates genuine paired fresh learning and retained configuration, replaces learning, sets O=U and displacement zero at :895, and leaves lifetime service counters, pending queue, clock and spent budget in the retained current state.

ICM checkpoint_state at icm.py:297 emits icm-state-v3; prepare_state at :389 requires it. Origin at :431 is an exact nonnegative integer bounded by U; _optimizer_state receives U-O at :469 and requires strict Adam steps and complete state matching that epoch count. Constructor :120 starts O=0. prepare_learning_reset at :482 sets O=U and loss zero while retaining service obligations. Neither implementation accepts v2 as a fallback.

The RND edited test at test_rnd_service.py:171 performs two actual direct minibatches, leaves one FIFO row, and never resets. The O0 expectation at :194 is therefore correct despite nonzero U. It still rejects diagnostic import through validate/prepare/load for learned and fresh destinations with full unchanged-state comparisons, restores the complete native state, compares diagnostic state and exact FIFO, advances both instances with real updates and compares full results, then rejects an extra key.

The ICM edited test at test_icm_provider.py:116 snapshots a genuinely constructed, untrained instance. The O0 expectation at :122 is correct. Subsequent independent objective/reward checks, action/successor sensitivity, no reward-phase learning or admission, eligibility and malformed transition refusal remain unchanged. The edits preserve exact schema equality; they neither compute expected labels from output nor accept a version set.

All ordinary fixtures in the three test bodies are no-reset controls. Their existing Adam expectations remain valid at O0. Lifetime conservation A=C+D+P and C=qU must remain lifetime equations; this patch correctly does not change them to epoch arithmetic. ICM mandatory count M and ordinary budget remain bounded by lifetime U-M. Public RND manual optimizer work remains supported: manual-history tests retain real Adam steps with U0, explicit displacement, full restore, and next real service equality. Existing empty/reset_steps corruption cases change optimizer history while leaving O0/displacement0 intact and remain incoherent transports. A legitimate learning reset also changes origin and installs validated fresh paired learning; these corruption cases should not be weakened.

## Quality, speculation and remaining gaps

- No severity-rated defect: the actual diff changes only approved expectations and adds two adjacent initialization assertions. No skip, xfail, removed assertion, broadened exception, forged counter, production behavior change, compatibility adapter or fallback is introduced.
- Refuted concern: updating v2 expectations hides an implementation regression. Both inspected producers and consumers consistently require v3; unchanged exact assertions now represent the approved generation.
- Refuted concern: the origin field invalidates existing lifetime/manual-work assertions. These fixtures have O0, so their existing equations remain correct. Source distinguishes lifetime counters from epoch Adam steps.
- Refuted concern: corruption refusal should be relaxed because reset permits empty Adam. The corrupted snapshots retain origins/displacements inconsistent with empty or zero-step Adam; real reset has additional state changes and validation.
- Informational test limit: the new assertions compare origin to zero; they do not independently prove exact integer rejection or nonzero-origin reset behavior. That coverage belongs to the separately qualified native reset packet; duplicating that scope is unnecessary for this five-line alignment. Exact integer validation was inspected in both production bodies.
- Required root runtime gate, not a static defect: the repaired owner packet has not been run by this reviewer. Root must seal final R17 after the separate parent seal and execute actual owner qualification. A static PASS cannot establish execution of the ICM assertions or later owner nodes.

The factory test remains unchanged and preserves actual backend class/geometry/parameters, mutable independence, ambient/order/spectator independence, binding refusal before constructors/draws, actual candidate-stream progress, global selector independence, zero-width behavior and active foreign-owner refusal. Its imported factory, RNG owner, adaptive and other backend implementations are outside this source boundary; their correctness is not independently authenticated here.

## Evidence attribution and closure boundary

The preparation report and root task record the actual pre-edit owner packet: 233 collected, then fail-fast 20 PASS / 1 FAIL at expected rnd-state-v2 versus actual rnd-state-v3. That remains causal RED evidence; no later owner node outcome is inferred. Root and independent Astra each separately reported 61 native passes on the approved production packet. Those are attributed facts, not reviewer-executed results. The preparation report also attributes scoped Black and Ruff passes to the test writer; this reviewer did not rerun them.

Root identifies MainNoDefaults601 as a causally traced separate parent fix2 outside these five bodies, with the original author its sole writer. No POP6/parent body was inspected and this test patch does not repair or qualify it. R17 and subsequent actual owner233 results remain root responsibilities.

This review closes only SPEC + QUALITY of the exact current-generation owner-test alignment patch at the identities above. It does not close whole parent, BANK/ENV, RNG custody or provenance, boundary/revision authentication, histories/epochs, ledger H/F, all-family reset dispatch, release or whole-program serving/transfer requirements. No premature GREEN claim is made.
