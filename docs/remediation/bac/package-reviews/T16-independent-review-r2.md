# T16 independent implementation review r2 — static

Disposition: **spec PASS at the static boundary; quality PASS at the static boundary; no blocking defect found. Runtime qualification remains pending/root-owned.** This is a fresh review of the actual implementation and its observers, not a plan review or authorization to execute.

Candidate manifest names base `f575ecefda7844fbd5b7b6138ad0c6bf7b1bafd8` and tree `d57c3e3fc5303533fe2b7e3e220f85e3e8ba7d36`. I read the complete `wave10/r2-review.patch` and all five actual source files independently. The diff comprises only RR (33 additions/17 deletions) and the new 526-line test; POP, BC and OF are context. The current five SHA256 values independently match the manifest. This bounded verification does not attest every other manifest entry or reconstruct the global candidate tree.

## Source custody

| Complete source | Physical lines | Independently computed SHA256 |
|---|---:|---|
| `src/townlet/demo/runner.py` |1017|`e1c4b6c00923416f6fdf9e70976ea57a4a706e38a2ea228b4b10273906d6aacf`|
| `src/townlet/population/vectorized.py` |2146|`9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a`|
| `src/townlet/config/brain_config.py` |568|`6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079`|
| `src/townlet/agent/optimizer_factory.py` |162|`56af1a9c8edb70a25b43a6e10aa3080d9a7b8becff112924e21a9429d994717d`|
| `tests/test_townlet/regressions/bac/test_runner_readiness.py` |526|`4b9fdcc73192b91db199111b4c2a07186e50fa1afc5bd6a77aa1e2909660939a`|

Total **5 whole implementation/test sources, 4419 physical lines**, within effective five-source/4900 projection and absolute 5000 boundary. The effective appended context supersedes the original three-file projection. I read AGENTS.md and the complete requested task brief, interface readiness, test authoring, observer repair and implementation receipts. The omitted resolver/buffer/sampler/environment/network/provider implementations were not opened; their contracts are limited to the supplied source-verified prose. No sixth helper, conftest or probe was read or created.

## Implementation assessment

1. RR401–454 consistently takes the learner loop, batch, size and related constructor inputs from `effective_run.training`. RR461 uses the canonical effective brain, avoiding an additional local override pass. BC534–568 establishes the intended five override fields; POP directly assigns gamma, including zero. The patch adds no new default table, fallback or authoring field.
2. RR462–497 forwards the complete resolved replay object and declared `min_size` to the real `for_training` seam. POP's `_ReplaySetup.create` checks all six leaves, exact minimum/horizon/tick integers and explicit Generator/origin; it owns deep copies. `_new_replay` actually creates selected recurrent PER eagerly and configures flat PER sampling. This is source-level behavior evidence beyond a factory name.
3. The fresh PCG64 generator takes the selected training seed, is separate from global NumPy, and is marked `authored`. Beta's horizon is executed maximum episodes times declared per-episode cap. Origin names the launch episode override when present, otherwise the training episode field, and always the cap/declaration origin and upper-bound vector-tick unit. Neither population size nor live-transition budget replaces that product.
4. Fresh tick zero and fresh replay construction precede RR522's existing checkpoint load. There is no new post-load reconfiguration or reseeding. POP's loader restores replay, optimizer, scheduler, target and cumulative counters; it marks replay loaded, clears constructor-pristine markers and invalidates binding. Subsequent binding adopts/validates the installed state instead of classifying it as pristine. Episode reset clears local collectors/hidden state, not retained replay or cumulative clocks. This supports preservation statically; it is not an end-to-end resume execution claim.
5. All non-runner public constructor/inspection/serving routes remain untouched. No archive deletion, mask fabrication, alternate wrong-target learner, historical clock reset, false non-PER brain, or manual production replay attachment was added. Existing History A and strict per-world B/shared-alternative ownership remain in force. Native demo10/population7 migration/atomic-resume work is still T24/T25 scope; the inspected current POP constant remains6, so no native7 implementation claim is made here.
6. The diff is small and localized, and the new origin construction is readable. It reuses the qualified factory instead of duplicating replay assembly. No actionable correctness or maintainability defect attributable to this patch was established.

## Observer and acceptance assessment

The owned tests execute real `DemoRunner.run`, production compilation, actual rollout/admission, actual replay sampling, configured loss, Q optimizer and checkpoint path. They author YAML data copies only. The callbacks invoke originals once and return original batches/losses; none inject synthetic replay, force actions, fabricate targets, bypass readiness or substitute networks. `_learn` observation adds a readiness read, relying on the supplied read-only readiness contract.

The repaired scheduler observer patches its class, not its instance, calls the original with the actual scheduler and filters the recorded instance. It therefore avoids placing its local callback into scheduler state. The optimizer observer checks real parameter changes and finite parameters/optimizer state. Loss observation records actual computed targets against the sampled objective rewards. Factory invocation alone cannot satisfy these checks.

| Required control | Static test adequacy |
|---|---|
| Declared warmup1000 | Both feedforward and recurrent PER run 1004 transitions, B2 independently of minimum1000. Tests assert zero updates after two retained rows and at every cold opportunity, then an actual first 0→1 update at ready support; pending recurrent rows cannot satisfy the threshold early. |
| Real recurrent PER/both laws | Both authored laws reach genuine learning checks, inspect captured7 policy before rollout and receipt mode during sampling, and distinguish B3 replacement support2 from successive batch-unavailable support2. |
| Four families | Feedforward uniform, dueling PER, token_set PER and recurrent PER retain genuine declared architectures and require finite, changing Q weights. |
| Frequency3/target2/LR | Literal opportunity ticks3/6/9/12/15, successful ticks6/9/12/15, target copies at successes2/4 and explicit StepLR factors establish distinct vector and successful-update clocks. |
| Gamma0 | Actual learner targets must exactly equal actual sampled rewards, in all four families, while optimization genuinely occurs. |
| Fixed-full diagnostic/adaptive control | Capacity1/L8 fixed-full must report sampleable0, no optimizer/sample/scheduler/target work and unchanged weights/state; adaptive-prefix must use actual length1 and learn. Repeated unchanged diagnostic is rejected. |
| Owned stream/eager policy | Public initial PCG64 state/origin and final state advancement accompany real samples/updates; initial recurrent captured7 includes all six leaves, fresh tick0 and exact horizon. |
| Effective provenance | Canonical brain/options/provenance are observed and retained; authored omission of priority_reduction remains distinguishable from resolved max_abs. These are preservation observations, not independent resolver correctness proof. |

Root reports R0's two failures were observer-induced checkpoint PicklingErrors, followed by the class-level repair. Root reports R1's two meaningful failures after finite genuine optimization and checkpoint publication: global rather than owned flat sampler; initial sequential5 rather than selected7. Those are the correct causal defects for this change. Warmup, post-binding learning, gamma and clocks were existing behavior and are correctly retained as controls. I did not execute those historical runs or independently read their logs. R2 collection12PASS and ongoing narrow/guard executions are root-attributed; this review claims no R2 runtime outcome.

## Gaps and severity

**No blocking defect.** The following are evidence limits, not demands for new implementation or a new planning loop:

- **Medium proof gap, tracked outside this fresh-only witness:** `observe_load` expressly requires no checkpoint. The owned tests cannot prove current replay/priorities/RNG/history/clocks survive real runner resume. Static ordering is correct, but native continuation/atomicity remains with existing checkpoint owners and T24/T25. Do not elevate the fresh-run PASS to resume qualification.
- **Low coverage gap:** all fixtures use seed42 and an explicit episode override, so these tests alone would not detect a hardcoded42 mutation or exercise the no-override origin branch. All use N1, so runtime evidence does not distinguish an erroneous N multiplier. Actual reviewed code correctly uses the selected seed, handles both origin branches, and contains no N multiplier; these are not observed production defects.
- **Low proof limit:** both law labels/support behaviors and finite positive weights are observed, but this file does not re-prove ordered PER probabilities, estimator unbiasedness, every option's alternate value, recurrent BPTT, or uniform-adapter mathematics. Those remain storage/sampler/learner owner evidence. Likewise snapshots of the runner's own provenance establish preservation, not independent derivation truth.
- **Release qualification remains open:** no local runtime, full suite, affected-owner suite or six-guard result was produced by this reviewer. Root retains the exact candidate tests, earlier-full-trigger assessment and mandatory G2, followed by exact-tip CI/publication. The supplied package status remains25/66 qualified; all final54 requirements/22 lenses remain owed.

Curiosity scope is the existing shared AdaptiveIntrinsic/RND instance constructed from selected training and attached to one population; finite fixtures use N1. The patch neither proves private-world isolation nor repairs provider-source precedence. Local clock units are retained eligible transitions for warmup, vector ticks for beta, successful Q optimizer updates for LR/target. RND work can continue during Q warmup. Fixed-full remains a truthful unavailable mode in its impossible-window control; adaptive-prefix is an additive selectable alternative.

## Execution boundary

Only static shell reads, line/hash counts, targeted diff summary and ignore-status verification were performed. No project import, pytest/collection, linter, compiler, runtime, probe, source/test/tracked-doc/index edit, tracker action, commit/push, source checkout/copy/deletion, branch/worktree or subdelegation occurred. The only write is this ignored report (`git check-ignore` confirms its path). Existing14 checkouts were not touched; no fresh global-worktree custody claim is inferred from that nonmutation.

Independent runtime is **NOT RUN** and awaits a concrete root assignment/clearance under the existing identity harness. This static PASS clears no runtime or release gate on its own.

## R3 narrow static addendum

R3 manifest names tree `0bdd6133f2224b25bce5668e15021fa1353accba`, same base. Independent current hashes confirm all four production files unchanged; owned test is now529 lines/SHA256 `2352066710ef7d97de02efb498021f26f7ffc50e2ce2afe96ea6ba4bbee04ce4`, total4422. Root's binding reports only `test_real_runner_window_diagnostic` changed and all other helper/test ASTs equal. I inspected the changed callable directly.

**Narrow static disposition: PASS.** The old single-count assertion was too strong: POP's diagnostic key includes reason, retained transitions and sampleable units. Retained0→1 is a legitimate signature change even when both states are capacity_window_impossible. R3 requires the exact two ordered messages (retained0/sampleable0 then retained1/sampleable0), preserving the preceding rejection of duplicate messages. This is a stricter truthful state-sequence oracle, not suppression of logging, removal of the zero-update control or production accommodation. All unchanged weights/optimizer/scheduler, unavailable-support and adaptive-prefix controls remain present.

The R2 static assessment missed this test-oracle defect. Root's actual R2 result was11 PASS/1 assertion FAIL, not whole-file GREEN; the earlier static PASS must not be interpreted as anticipating that assertion's validity. Root reports the corrected individual case PASS and Black/Ruff PASS; those results remain attributed. The fresh independent three-case runtime was explicitly cleared by root under the R3 locked identity spec; its actual result will be recorded separately in `T16-independent-runtime-r3.md`.
