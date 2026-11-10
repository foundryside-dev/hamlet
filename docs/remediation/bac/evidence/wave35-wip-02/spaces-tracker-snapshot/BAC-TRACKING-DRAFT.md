# BAC Work Completed and Remaining

Updated 11 November 2026, Australia/Sydney. Status snapshot: 07:59 AEDT (10 November, 20:59 UTC).

BAC has **28 qualified releases out of the original 66 packages**, with **38 original packages still requiring qualification**. Subsequent component work has delivered substantial private curiosity, curriculum and checkpoint foundations. Connecting those components through the real population and runner, proving the complete behavior, and completing final BAC acceptance remain substantial work. Package counts do not measure the percentage of engineering effort completed.

# Current position

| Area | Status | What this means |
| --- | --- | --- |
| Original package releases | 28 qualified, 38 remaining | Scoped releases retain their evidence; final acceptance on one common source revision is still owed. |
| Later component delivery | Bounded components accepted | Curriculum producers, world identity and state foundations, provider factory, private bank, same-scope checkpoint and explicit private initialization components have progressed; their integrated packages are not released. |
| Current work | Parent integration needs repairs; environment tests reach the missing producer | The local, unpushed parent implementation has six material P2 review findings and is not approved. The first repair round is underway, beginning with batch retry, reset activation and mixed-participant completion; all six remain open until review and execution. All 63 staged cases collected: 41 parent cases and 22 new environment cases. The first focused provider-phase case failed at the missing environment runtime-binding method, with no setup errors or skips. Environment and reward-calculator production code remains unchanged. This is expected prerequisite failure evidence, not an integration pass. |
| Published checkpoint | [31beef58](https://github.com/foundryside-dev/hamlet/commit/31beef58892fe651daf6c9965f372b3643523ce2) | Pushed, with exact remote revision and tree verified. Exact-revision CI is terminal: [configuration passed](https://github.com/foundryside-dev/hamlet/actions/runs/42888280047), [lint failed](https://github.com/foundryside-dev/hamlet/actions/runs/42888280323) and [tests failed](https://github.com/foundryside-dev/hamlet/actions/runs/42888279948). No failure cause is inferred from workflow status alone. |
| Overall BAC acceptance | Full-repository gate failed; no boundary release | The published baseline full execution at exact source 30a802a9 finished with 1,010 failed, 7,285 passed, 21 skipped and 231 errors, plus 40 warnings. The current source has not had another full run while known causal prerequisites remain. Source and process identity verification passed, but the repository gate did not. Global mypy now reports ten errors: the existing nine oracle/population errors plus the reward-composer caller missing the new required scale argument; CUDA is unavailable and unqualified. |

The accepted conversion component supports explicit fresh-private initialization and cloning learned state while preserving the complete source archive as inactive history. Native inherited counters and future per-world counters remain distinct, with explicit origin and epoch provenance. Ordered native dictionaries and Torch metadata survive owned transport. The native metadata repair passed 16 cases in both root and independent Astra runs; the repaired existing owner suite passed 31 cases in each run, with one CUDA skip each. The earlier combined 973-pass result included the none-scale repair; the latest coherent component suite has 1,123 passes and three CUDA skips. These selections overlap and must not be added together. These results qualify the bounded component; actual population, runner, native-parent admission and captured-replay sampling and learning remain open.

# Work completed

The 28 qualified original releases cover these delivered areas:

| Delivered behavior | Qualified package IDs |
| --- | --- |
| Finite authored numerics, portable options, exploration resolution, effective identity, historical archive and fresh-buffer import, lossless sidecar lowering, canonical launch and CLI transport, canonical discovery | T01, T02, T18a, T03, T03a, T04, T05, T06, T07 |
| Legal action selection and successor masks, completed-lane action gating, uniform and prioritized replay, real short windows, matching PER estimators, recurrent PER, production collection and learner readiness | T08, T08a, T09, T09a, T10, T11, T12, T13, T14, T15 |
| Effective runner warmup, descriptor/value interactions, bounded RND service and tails, count novelty, ICM, completion envelopes and clock ledger | T16, T17, T18, T18b, T18c, T19 |
| Explicit curiosity scope and seeds, private RNG foundations, recording work that survives shutdown | PW01, PW02, T33 |

Later accepted component work is tracked separately:

- **Curriculum and world foundations:** completion-driven curriculum and option/factory producers, compiled roster and identity/state maintenance, and world-state owner components. Their actual joint runtime routing remains open.

- **Provider construction and service:** typed events and local clocks, RNG binding, the five-provider factory and separate policy selector; RND, ICM and adaptive providers perform real updates using their declared local service and native-state contracts.

- **Private curiosity bank:** independently owned state for all five provider families, local replay and service, completion publication and failure custody. The explicit shared alternative retains grouped behavior. The bounded bank passed 84 root and 84 independent cases, with 551 covering passes and three CUDA skips.

- **Same-scope checkpoint component:** off-side validation and preparation of models, gradients, optimizer, RNG, clocks, phases, caches and history; strict identity checks, owned installation and current replay-component preservation. It passed 147 root and 147 independent cases, with 635 covering passes and three CUDA skips. These overlapping selections are not added together.

These bank and checkpoint results use bounded component fixtures. They do not prove complete DQN/runner parent admission, captured replay sampling or ordinary end-to-end resume. The [published qualification evidence](https://github.com/foundryside-dev/hamlet/blob/30a802a996fe8bf7cd63e53d211fa8b2cd028f77/docs/remediation/bac/evidence/wave34-wip-01.json) and [runtime contract](https://github.com/foundryside-dev/hamlet/blob/30a802a996fe8bf7cd63e53d211fa8b2cd028f77/docs/remediation/bac/CURRENT-EXPLORATION-RUNTIME-CONTRACT.md) record the reviewed runtime component and current curriculum consumer repair. The runtime component passed 150 independent tests and a coherent 1,123-pass selection with three CUDA skips, plus independent source/specification and documentation truth review. The repair uses the real completed-event API, with no compatibility-only adapter: 52 migrated cases and 175 event regressions passed, for 227 passes. Compiler CLI validation also passed for 34 packs across 35 processes with verified source, import and thread identities. The subsequent full-repository run at the exact pushed source failed after 2,003.7499 seconds. Verification covered 797 source files, 573 configurations, 13 artifacts, all five pytest processes, the index and registry custody; the separately verified poisoning child also passed its assertions. Failure triage identifies 1,241 deduplicated failed test-node/phase records across 160 affected source files and 15 terminal-signature groups, chiefly missing world-identity constructor inputs, required reservation/activation, old curriculum/provider calls and stale option/schema assertions. These records are not 1,241 independent algorithmic defects. Repair causal prerequisites until tests reach their intended assertions before another broad run. The failed baseline and triage are now published in the [latest checkpoint evidence](https://github.com/foundryside-dev/hamlet/blob/31beef58892fe651daf6c9965f372b3643523ce2/docs/remediation/bac/evidence/wave35-wip-01.json). The [intrinsic-scale composer contract](https://github.com/foundryside-dev/hamlet/blob/31beef58892fe651daf6c9965f372b3643523ce2/docs/remediation/bac/CURRENT-INTRINSIC-SCALE-COMPOSER-CONTRACT.md) records the new bounded math/API component: raw reward 2 × scale 0.5 × weight 0.25 × modifier 2 produces intrinsic reward 0.5 and total reward 1.6 in the tested case. Current-candidate compiler CLI validation passed for 34 packs across 35 processes in 171.4223 seconds, with 798-source, import and thread identity verification. Four cheap guards pass. These checks do not establish current full-repository or all-family end-to-end qualification.

# Work remaining

Every one of the 38 original packages still awaiting qualification appears once below. Some contain accepted components; each still owes its full package behavior and integration evidence.

| Workstream and packages | Remaining deliverable and completion condition |
| --- | --- |
| Provider foundations — PW04, PW03, PW05, PW06 | Complete backend/native consumer coherence, factory and bank runtime use, and strict checkpoint integration. Pass the real ordinary runner checkpoint and full owner suites; component approval alone does not close these packages. |
| Explicit conversion — PW07 | Bounded fresh-private and learned-template conversion, current-owner checks and the combined component gate have passed independent review. Complete real native-parent and runner integration and full package qualification, preserving source archives, compatible state and truthful origin/counter semantics. |
| Runtime curiosity routing — T18d, T18e, PW08a, PW08, T18f | Connect the five providers, canonical per-world reward scales, population, environment, runner and current native-parent transport. The eligible-none and checkpoint-cache prerequisite is complete. The T18d runtime component is reviewed but unreleased; the intrinsic-scale primitive passed the same 29 cases in root and independent runs. The local parent implementation now needs six P2 repairs: failed batch retry, reset activation ordering, mixed-participant completion, stable role-owner restore identity, valid transfer support and native clock correlation. The 63 collected parent/environment cases and first expected missing-producer failure do not close integration. Actual environment equality, phase order, replay/learning, inactive-world behavior and ordinary checkpoint smoke remain owed. |
| Curriculum integration — T20, T21, T22, T23 | Integrate accepted curriculum producers and provenance, implement per-world dynamics, and prove each world's completion and controller decisions reach its own mechanics through population and runner. |
| Checkpoint and restart — T24, PW09, T25, T26 | Finish boundary/schema and selection, scope/binding dispatch, full predictor/replay/clock restoration and one episode-end transaction. Prove atomic refusal, captured replay preservation and usable sampling/readiness, plus durable intent/effect reentry. |
| Transfer and serving — T27, T28, T29, T30, PW10, T31, T32 | Deliver explicit evaluation modes and reset, truthful partial and strict transfer, effective artifact identity, schema-aware target-state policy, explicit private source-world selection, process-isolated serving, and a current all-family evaluator. |
| Outputs and diagnostics — T34, T35, T36, PW11 | Own recorder failures during runner cleanup; preserve sink units and outcomes, effective hyperparameters and intervention reporting, and per-world scope, origin and scale diagnostics. A scalar summary must never replace per-world reward scales. |
| Isolation and lifecycle proof — PW12, PW13, PW14, PW15 | Inventory actual simulator state owners; prove private rewards and state across real curiosity updates, reset/resume/conversion and archived history; verify each controller lane and the declared shared-Q feedback boundary. |
| Joint acceptance and learning — T37, T38, T39, PW16, T40 | Complete learning-support, restart/transfer/serve/discovery and persisted-output matrices; prove truthful shared/private support and run the finite original learning protocol plus the strict cohort after integrity gates pass. |

# Next delivery steps

1. Repair the full-gate failure prerequisites in bounded groups: current world identity and activation contracts, current curriculum/provider consumers, and option/schema assertions. Reach the intended assertions before repeating the broad gate; obtain a passing full run before boundary release. Preserve the existing component, consumer-repair and compiler CLI evidence.

2. Repair the six parent findings: preserve retry or recovery after batch-commit failure; publish reset activation only after preparation succeeds; complete mixed-participant batches correctly; preserve registered role-owner identity during restore; restore valid transfer capability; and validate native service, cache and parent clocks together. Native reset and correlation interface capsules are ready, but independent technical design review and implementation remain owed. Implement the environment runtime binding, pre-physics claim and canonical raw/scale reward delivery after the intended missing-producer failure, then prove the genuine pipeline. Keep one successor, the existing phase order and total_steps + 1 authority; complete replay sampling, readiness and learning, all-child restore and ordinary runner evidence.

3. Repair all ten current caller type errors, including the mandatory scale argument at the reward-composer caller, resolve test CI failures from their actual logs, and obtain required exact-revision CI results. Retain the passing compiler CLI evidence and complete the default repository, coverage, slow and applicable hardware gates.

4. Finish curriculum, checkpoint/restart, transfer/serving and diagnostics packages in dependency order, followed by the complete isolation and joint acceptance evidence.

# Final completion criteria

- All **54 effective requirements**, **22 fresh final design and implementation review lenses**, and independent synthesis pass on the final common immutable source, with no unresolved P1/P2 findings or unapproved in-scope gaps.

- Real runtime evidence covers all four Q families, all five curiosity providers and both scopes through compilation, rollout, updates, save/load and serving. Private isolation uses real local learning and complete named state owners, including lifecycle and controlled shared-Q cases.

- The original T40 learning protocol is retained. The additional strict cohort is exactly **12 runs**: four families × seeds 11, 29 and 47, each with 10,000 eligible training transitions and 20 evaluation episodes per seed, using explicit per-world adaptive RND and actual local predictor updates. Record controls, metrics, failures and deviations; do not infer a causal shared/private comparison from differing settings.

- Required default full-repository, coverage of at least 70%, slow, applicable hardware, static and exact-final-remote CI checks pass. Source-verified documentation and supported end-to-end scenarios agree with the actual behavior.

The [accepted per-world requirements](https://github.com/foundryside-dev/hamlet/blob/a7c4cd0b19c410114aaabdd9284888fef159e84e/docs/remediation/bac/PER-WORLD-CURIOSITY-ADDENDUM.md) define the finite isolation and learning obligations. Current tracking reflects later accepted amendments, including the 54-requirement and 22-lens totals.

# Decisions and boundaries

**No user decision or access blocker is currently pending.** The open parent findings and native interface review are engineering work. Strict per-world curiosity is required, with the explicit shared alternative preserved; omitted scope retains shared behavior. Shared Q and policy feedback remain permitted under the declared controlled-trace isolation guarantee.

Current producers, callers, tests and documentation must evolve together without new legacy adapters or compatibility loaders. Historical artifacts have been inspected and exported. Obsolete unmasked replay starts fresh as approved by the owner, with its archive preserved; captured current replay remains preserved. Existing K01 qualifications for exact stochastic or mid-episode simulator continuation remain explicit and do not introduce a new simulator upgrade requirement.

This is a private tracking Page. Its repository links remain subject to the viewer's GitHub access. It records the stated snapshot and is not configured for automatic updates.

