# T15 actual candidate independent review r0

Verdict: **REQUEST CHANGES / qualification pending**. Static production design/source review found no confirmed material P1/P2 implementation defect in the bounded candidate. The regression package has one confirmed dtype-oracle defect and one required recurrent-readiness coverage gap; both need repair and scoped re-review. This is not T15 release, whole-BAC closure, or a passing runtime review.

## Identity and complete source boundary

Reviewed existing `/workspace/hamlet`, HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`, root-frozen candidate tree `f4ae7e65c2f2a1ffc944c19342490b8f48d6c9bf`. Read the actual main review diff and candidate manifest, the actual-candidate brief, task-T15, full approved interface R1 and its Astra R1 review, schema/selector extension review, implementation receipt, and source-verified flat/provider/sequence/history API prose. The corrected uniform sequence contract is explicit: all six leaves resolve non-None; for_replay preserves the supplied sampling_mode string; POP uses that exact value.

Exactly five complete implementation/test sources, **3815 lines**, within hard five/5000:

| Source | Lines | SHA256 |
|---|---:|---|
| src/townlet/population/vectorized.py | 2128 | e1accf8f6b0d9b884d37931facadcb030505552bdbe2d29d1733ee19fb021b02 |
| src/townlet/training/replay_contract.py | 222 | 3eaa725bd6d592b7524dd249125877eb91a1f707d4dfd12fbfb59b5b6cc6356c |
| src/townlet/training/q_targets.py | 80 | 39485fe2447dc4065bd7b806775c93c0e66b51827b088605fba98505b100491f |
| src/townlet/config/bac_options.py | 294 | 10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916 |
| tests/test_townlet/regressions/bac/test_learner_legality.py | 1091 | be3330518a5e25163a7b9e0d3e4a1e963454b73d70e66eb0c4df5f613b1c2658 |

No sixth buffer/provider/network/runner/schema/fixture/conftest/probe source was read. The separate schema approval is attributed, not re-reviewed here. Skill using-superpowers was read and its dispatched-subagent stop applies. Root remains integration/index owner; no branch/worktree/source copy/deletion/index/commit/subdelegation or publication occurred. All14 worktrees remain untouched. Only this ignored prose report is written.

## Required corrections

### R1 — P2 regression oracle rejects the required float64 residuals

`tests/test_townlet/regressions/bac/test_learner_legality.py:624` compares `errors[0, mask[0]].abs()` with a default-float32 `torch.tensor([2.0, 3.0, 2.0])` using `torch.testing.assert_close`'s dtype checking. POP735–737 deliberately allocates float64 errors and promotes each operand before subtraction; the spy at test604–606 preserves that dtype. Thus the PER cases fail this assertion even for the required correct numerical result. Sixteen parameter combinations reach this PER-only comparison. Static evidence is decisive about the mismatched types; root's execution still needs to identify the actual observed failures.

Repair the expected tensor to explicit float64 and retain the value/mask assertion. Do not downcast production errors, disable the numerical checks, or weaken X04. Re-run the exact prefix/BPTT/objective/stable-feedback node, then the full owned suite on the revised identity.

### R2 — required evidence gap: retained transitions versus recurrent window cardinality

The law/readiness contrast at test458 is flat-only. Recurrent tests cover both PER laws with sufficient units, capacity1 with B1, and zero-window diagnostics, but no owned learner test establishes the crucial case where retained transitions exceed B while distinct recurrent sampleable units are below B. This is explicit in the approved schema extension and actual candidate brief. Source POP638–648 and699–712 delegates the correct request/readiness contract; this gap is not evidence of a production defect.

Add a bounded permanent control in this same owned test file: fixed_full L3, one completed length3 episode, min_transitions1/B2. Successive must skip from one sampleable window despite retained3>=B; replacement must perform an actual optimizer update from that same positive support. Assert retained/sampleable counts and successful-update/scheduler/target/sampler-RNG preservation on the skipped opportunity, while vector pacing continues. Root accepted this required addition during review. Do not count pending live collectors as stored windows or fabricate padding.

## Spec compliance assessment

The implementation follows the approved construction and learner design in the examined source. Public __init__ and for_training use one initializer (160–456). Required setup inputs validate resolved options, exact integer domains, Generator/origin/horizon provenance and own copies (109–151). The passed brain is retained and drives network/replay construction; compiled policy resolution supplies the declared minimum and seed/limit provenance (497–518), without a sixth override. Serving/inspection does not enter lazy learner setup merely because the training carrier exists.

Lazy binding distinguishes pristine constructor ownership by identity plus complete serialized equality and clock/load markers (578–625), not occupancy alone. Qualified loaded/attached buffers are validated and adopted. Existing archives, sampler state and IDs are not reset by first-step entry. Sequential adaptation builds offside; legacy inspection archives merge through the documented bridge. Current6-to-prioritized7 load prepares at restored tick without changing the live tick (1993–2005). Current7 clock consistency is checked before load; load resets the binding marker and last-paced clock to the actual restored total (2007–2055). Full native envelope/atomic continuation remains T24/T25.

Action selection validates eligibility/mask geometry and live-empty support before provider sampling, slices every temporary state tensor and per-row epsilon, calls the real provider once, and scatters into full-N transport argmax (995–1027,1207–1247). Public selectors also use actual eligibility. Same-step committed successor masks enter exact admitted flat rows or recurrent fragments (1276–1307); flat capacity overflow is chunked in original row order. Canonical total reward remains independent of optional replay components. Recurrent fragment commit remains after that step's learning opportunity and occurs once on completion/flush.

The learning path uses real request/readiness/sample_batch, not the old16-episode gate. Beta pacing runs every vector tick before the scheduled learner opportunity (627–648,1313–1317). Successful optimizer work alone advances update/scheduler/target counters (741–750). Recurrent rollouts are not reset on unreadiness. Flat B1 uses squeeze(-1).

Recurrent evaluation groups real lengths, retains graph-connected online prefixes, advances a separate target prefix under no-grad, and branches each stored successor from the corresponding network's after-current hidden state (659–697). Bootstrap hidden is discarded. There is no adjacent-observation assumption or padded forward. QT validates historical legality, masks legal selection and excludes terminal/gamma0 rows from bootstrap values. Recurrent loss selects only declared objective rows, averages within each unit and applies the returned float64 weight once before batch-mean (713–734). Stable IDs and canonical masks feed backend priority APIs without reimplementing epsilon/reducer rules (753–758).

X04 uses detached operands promoted before subtraction and computes unweighted mean over all sampled real rows, independent of anchor/loss masks and weights (735–739). Large-finite tests retain two real flat optimizer updates and finite parameters/Adam assertions; recurrent numerical controls include unequal lengths, padding poison, nonuniform weights and B1. Their execution is still required; source plausibility is not a PASS.

The genuine ICM sentinel exercises actual filtered selection then stops at the second env.step boundary (923–983). It cannot establish second-step reward, replay insertion, completion or learning. Full ICM transition-context reward/update/continuation/E2E remains REQUIRED OPEN T18e/T18f, with no waiver of T15 selection or all-provider final acceptance.

## Code quality assessment and refuted hypotheses

Production quality is acceptable for scoped re-review, subject to runtime/static gates. Helpers separate setup, binding, pacing, request construction, recurrent evaluation and optimization without duplicating the constructor or backend sampling math. The main maintainability cost is unavoidable state/adaptation branching at the replay boundary; the explicit serialized-policy checks and offside installation make the ownership decisions inspectable. No additional material production-quality finding is confirmed.

Refuted by source: first-step unconditional replay replacement; empty occupancy as permission to reset; uniform sequence sampling_mode=None; crossed recurrent online/target hidden states; detached current-prefix BPTT; successor branch advancing the current prefix; padding multiplied by zero after arithmetic; applying unit weights twice; flat B1 scalar squeeze; using physical receipt positions for PER feedback; querying current ENV legality during learner target construction; paced beta only on optimizer updates; treating ICM sentinel as full ICM reward success.

Unconfirmed test-oracle risk, not a production finding: test820's eager/lazy continuation comparison saves/restores torch RNG only. The documented uniform sequential adapter uses Python random; if a uniform recurrent equality failure appears, establish equal Python draw state before inferring replay corruption. Root has been notified to diagnose actual output rather than preemptively change the source.

## Runtime evidence and outstanding verification

No project import, pytest/collection, custom probe, compiler or static guard was executed by this reviewer. Root required static-only work while its identity-controlled campaigns occupied the resources.

Root-attributed evidence: collection PASS150 nodes (127 learner +23 DTO), exact frozen tree/HEAD,144 guarded paths,573 configs,13 artifacts and14 worktrees. Root then reports the selected focused33 PASS in54.70 wall seconds, identity guards unchanged; receipt `/workspace/bac-review-2026-11-01/qualification/wave09-green-r0-focused/focused-result.json`, log SHA256 `ded1bc732baac3e7e064f3147ad9cef3d783fee3959ecc93f45b315ef078d4e5`. Full owned150 is active at `wave09-green-r0-owned`, static guards at `wave09-guards-r0`; neither is reported passing here.

Exact owned command to run through root's approved import/identity/fixture/TMPDIR/basetemp wrapper:

```text
uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_learner_legality.py -q
```

Scoped re-review should independently execute selected existing owned nodes after root clears resources, especially exact_prefix_bptt_objective_stable_feedback_and_unweighted_td, load_before_first_step_adopts_current_replay_and_clocks, captured_six_adapts_offside_at_restored_tick_for_selected_recurrent_per, all_providers_select_only_true_eligible_rows, and the new recurrent law/cardinality control. No uncounted sixth executable probe is authorized or needed.

Before release: repair R1/R2 and any actual runtime failures; freeze revised hashes; fresh scoped review; owned and affected replay/population/B03 bootstrap/BPTT/lane-learning suites; all six standing static guards; triggered full G2. Final same-source22 lenses plus synthesis, all54 requirements, learning/E2E, repository coverage>=70%, slow/applicable hardware, finite T40 and exact-tip remote CI remain owed. This review does not close them.
