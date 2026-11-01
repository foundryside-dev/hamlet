# Review provenance

Historical finding/triage source identity remains historical; see the final implementation receipt for repaired-source qualification and required remaining X04.

Original `MEAN-TD-TRIAGE.md`, SHA256 `d4562d2cb241dff87e921e0a0c9540cb54832785a6dbf36c6ef8f1ee8fae8b76`, retained unchanged; portable rendering normalizes execution paths.

# Mean TD telemetry: bounded independent triage

Verdict: confirmed existing defect, required repair; not optional P3. No implementation or runtime execution performed by this reviewer.

## Scope and identity

Reviewed only these five whole implementation/test files (3247 lines total). SHA256 values below were checked before and after review and were identical. The first three match the diagnostic manifest `.superpowers/sdd/2026-11-01-bac-remediation-upgrades/wave07/red-r1-candidate.json`; brain_config and state are absent from that manifest and are locally bound by the recorded hashes. This is scoped source identity, not a claim that the global tree/index remains frozen while the root authors PB/PS/HC.

| File | Lines | SHA256 |
|---|---:|---|
| src/townlet/population/vectorized.py | 1854 | 38d8c969a8acfc5f49a3c5c7e532f6f10b34844af12ca37e8696123511e47d3b |
| tests/test_townlet/regressions/bac/test_per_native_learner.py | 270 | 6348f247dc9b5060a650f87fe8bee1d9c18ece46a868c40b6021f0360c19da16 |
| src/townlet/config/bac_options.py | 294 | 10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916 |
| src/townlet/config/brain_config.py | 568 | 6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079 |
| src/townlet/training/state.py | 261 | a9e88c8977081c1ad9abbc3d85d260f61139a5257894e1900770447bb9f061b0 |

Base HEAD supplied: `41edeb0858cba98a8dcb6ba2af36355457ef4e0a`. Original diagnostic candidate: `2cfb5360ae46aa67fc2506743b469f257696c324`. Reading that HEAD's vectorized.py through `git show | sha256sum` gives the same hash above; scoped git diff for the four production files is empty. Thus this defect predates the current T13 production work. The new test exposes it; it did not introduce the producer expression.

Read AGENTS.md, CLAUDE.md, STATUS severity bar, relevant review brief, receiving-code-review skill, BAC.md, accepted design baseline and frozen plan, T15/T35 extracted task prose, and causal-red-clearance.json. User preservation and approved history A override old blanket deletion guidance. No user-only rule was adopted; no new user decision is inferred. No sixth implementation, helper, sampler, compiler, environment, runner or sink source was opened. No import, runtime, test, probe, helper, branch/worktree, source copy/edit, index/stage/commit or git-write-tree action occurred. This ignored report is the sole write.

## Defect: authored finite TD mean becomes infinity (P1 under local bar)

Exact producer: `src/townlet/population/vectorized.py:1029` assigns `(q_target - q_pred).abs().mean().item()` to `last_td_error`. The inputs and reduction remain float32; `.item()` happens only after reduction. For the observed two equal finite absolute residuals `1.9999999360571385e38`, the intermediate sum is `3.999999872114277e38`, beyond float32 range, while their arithmetic mean is exactly the finite representable per-row value. A Python float conversion after that reduction cannot recover it. `get_training_metrics()` at lines1129–1141 publishes the stored value unchanged as `td_error`.

Semantic contract: this existing producer computes the unweighted mean absolute pre-update TD residual over the sampled rows. It is separate from the configured Huber objective and PER importance weights (lines1008–1033). No config in the assigned files redefines the metric as a sum or allows infinity to mean a finite mean. BAC §1 requires inspectable/reviewable cognition; accepted BAC-C13 (design baseline lines149–157) is the truthful telemetry umbrella. C13's detailed text does not literally specify a finite-TD-mean rule: the precise metric semantics come from the existing producer/API, not an invented quoted clause. T35 explicitly preserves existing useful counters/API. The numerical value is wrong, not merely a misleading generic label.

Severity follows `docs/remediation/STATUS.md:156–164` and the adopted review brief: P1 includes wrong behavior or silent corruption reachable from an authored pack. This case has actual admitted authored-pack reachability and an incorrect public numerical result. Scope the P1 to telemetry; no optimizer, policy, replay-content, determinism or isolation corruption is established by this observation. Even a narrower interpretation reserving P1 for learning behavior leaves a P2 broken metric contract. P3 covers nits/doc drift/dead code/performance, none of which describes returning infinity for a finite mathematical metric. The unusual magnitude does not change the admitted-input or public-output facts.

Observed evidence, independently read rather than rerun:

- `qualification/wave07-red-r1-narrow/native-alpha0-control.log`, SHA256 `ed145846f07341d21d07e78b57babecf172e9acaf63b4e23674d213d95593558`: both actual updates publish `mean_td_logging: "inf"`; each has finite Huber loss `4.999999840142846e37`, six changed parameter tensors and Adam step1/2. The test passes because it deliberately records TD telemetry without asserting its correctness.
- `qualification/wave07-red-r1-narrow/native-alpha1-causal.log`, SHA256 `0a16aa91fbf9c855ddc3133451209fc7e61a4860cbd27cdde49f63c71b70650a`: first actual update has the same telemetry error and finite optimizer evidence; second sample fails with probabilities-not-summing-to-one. The two failures have distinct owners/causes.

Both logs admit feedforward256/128, Adam lr0.0001, Huber delta0.25, gamma0, target1000, two worlds, replay capacity/batch/minsize2, frequency1, authored reward base2e38, no composition normalization/clipping. `test_per_native_learner.py:119–136` asserts finite loss/parameters/Adam states and real changes; lines159–177 derive independent float64 residual/priority/probability evidence; line180 records the telemetry separately. The apparent success of the alpha0 control is not a waiver of this defect.

## Finite owner and acceptance gap

Assign producer repair to existing **T15**, whose accepted whole-file owner is population/vectorized.py (task-T15.md:9–15; frozen plan:437–445). **T35** owns sink units/outcomes and does not own this producer; it may consume a truthful T15 metric receipt in its existing sink checks. Do not move or mask the calculation in a sink. Frozen plan SHA256 remains `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1`.

Propose a bounded additive T15 acceptance, recorded in its active execution overlay rather than modifying the frozen plan:

1. Exercise the real learner with the same admitted high-reward alpha0 witness. After each of two successful optimizer updates, assert `get_training_metrics()['td_error']` is finite and agrees with an independent float64 pre-update residual mean (relative tolerance2e-6); assert unchanged semantic definition, real parameter changes, finite loss and Adam state. The existing alpha1 case should also assert the metric once T13 sampling is repaired. Retain the modest control. Never replace the value with a clamp, zero, string, omitted field, or reject this working authored reward as the telemetry remedy.
2. Cover both existing TD producer branches in T15's owned learner test file: flat (uniform and PER) and recurrent valid-row mean (`vectorized.py:947–948`), with at least two large finite valid residuals and identifiable padded/invalid rows excluded. Single-row and modest unequal residual controls prevent denominator/masking mistakes. This is bounded to this metric, not a general numerical audit. Recurrent overflow is a static same-pattern risk, not separately claimed as an executed authored incident.
3. Accumulate the diagnostic mean in a sufficiently wide/stable representation before reduction while preserving its unweighted sample/valid-row semantics and leaving the loss/gradient/priority objectives unchanged. Demonstrate the causal red before the fix and green after it; run T15's standing focused/gate/review requirements. A producer/API assertion closes this defect; no unverified assertion about downstream SQL/TensorBoard handling is needed. Any actual sink failure uncovered in T35 belongs to its existing package.

T15's projected inventory is already5 files/4880 lines. Put the bounded regression in its existing owned learner test file and recount; if growth breaches the cap, the coordinator must reslice under the existing bounded-review rules before dispatch. Do not quietly open a sixth native test file inside T15's reviewer context. Existing native evidence can be consumed via this receipt and existing tests executed without opening them. No new work package is required, and the 66-package plan is not declared complete or reduced by this finding.

## Refuted / unproved / optional dispositions

- Refuted: mean-TD infinity proves optimizer divergence. The supplied completed updates have finite actual losses, parameters and Adam state, with real changes.
- Refuted: sampler normalization alone causes the metric error. Alpha0 completes two samples/updates with the same wrong metric; the producer has its own float32 reduction.
- Refuted: T13 introduced the source defect. The producer bytes equal HEAD and the diagnostic manifest.
- Unproved here: any downstream serialization crash, dashboard corruption, controller feedback, or recurrent authored incident. Those require their own bounded evidence, not inference from this scalar.
- Optional P3: none assigned. General numerical improvements beyond this metric are outside this bounded triage and are not silently converted into requirements.

The root remains sole integration owner. Reviewer is stationary after this report; T13 PB/PS/HC production was neither inspected nor changed.
