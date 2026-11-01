# Execution addendum technical review

**Verdict: CHANGES REQUIRED — activation authority only.**

Reviewed file: `.superpowers/sdd/2026-11-01-bac-remediation-upgrades/execution-addendum.md`.
Exact SHA256: `53f643f4430369c5535a7bdbc19b0651850ec503e4e0bb84058335c22d1c52ed`, verified before and after review.
Reviewer: the same Astra MEDIUM reviewer of approved v3, using its retained context. No implementation/test source was read; no code, plan or tests were edited.

## Blocking correction

**Locations:** opening Status, justification's final paragraph, §5 lines79–80.

The addendum currently becomes effective upon technical-review approval and says the coordinator then records an external review/override reference. That is insufficient authority to change the standing cadence. `docs/remediation/STATUS.md:27` explicitly makes §3 and §4 binding; `STATUS.md:166` names §4.3 “The gate, run before every commit”. The coordinator's general execution authorization and this reviewer's technical verdict do not themselves supersede that specific owner rule.

**Required revision:** make cadence activation require both (1) exact-hash technical approval and (2) an explicit John or duly authorized Emmy exception to STATUS §4.3's full-suite-per-commit cadence, identifying this bounded G1–G7/trigger replacement and retaining all other gates. Record the actual exception reference when granted; do not infer approval from elapsed time, general autonomy, historical-replay Option A, or this review. Until both conditions hold, continue v3's existing cadence. Separate the T08a inventory/eligibility clarification from cadence if the coordinator wants to activate that independently under technical approval.

No owner exception was supplied with this review request. Root therefore needs to obtain that narrow cadence ruling before deferring any mandatory per-commit full suite. This is an authority qualification, not a technical objection to the proposed testing method.

## Technical assessment

The proposed cadence preserves the accepted quality standard if activated through the proper authority:

- Every package keeps causal red/green proofs, relevant existing owner suites, all standing non-pytest guards, actual fixed-source fresh other-model review and repaired blockers before dependency release.
- G1–G7 are concrete coherent integration checkpoints with actual contract probes, rather than an arbitrary commit interval. G6/G7 preserve the entire final repository/coverage/slow/applicable-hardware scope, 17 current-source/spec/design lenses, independent synthesis, joint evidence, T40 and mandatory remote CI.
- Changes to consumed interfaces, effective identities, configuration precedence, serialization/restore, shared fixtures/dependencies, unbounded-impact failures or material cross-slice contracts force an earlier full suite. Isolated unused additive modules are distinguished from wiring changes. The coordinator records trigger applicability, and the reviewer can require an earlier gate.
- Receipts distinguish package evidence from repository green, name unrun checks and the next full gate, and never permit an unresolved failure merely because another gate is planned. Identical candidate evidence may satisfy coincident checkpoints without a duplicate invocation.

The remaining operational risk is delayed discovery of distant regressions in a nominally local change. Mandatory impact analysis, direct-consumer checks, conservative uncertainty triggers and integration/final gates contain that risk. Many planned configuration, serialization and wiring packages will still trigger full suites; the baseline multiplication is an illustrative upper-cost estimate, not a promised saving.

## T08a technical assessment

The revised complete inventory is valid: action_selection160 + q_targets180 + new regression350 + existing epsilon-selection test210 = **4 files/900 projected lines**, for both implementer and reviewer. The existing144-line test fact is coordinator-supplied evidence, not an additional source read by this reviewer.

The correction preserves dead/inactive all-false transport-row dummy/greedy behavior while requiring exact-zero illegal mass and a diagnostic for a genuinely live nonterminal empty legal set. POP owns eligibility; downstream provider/serving adapters must preserve it. No dead row may enter experience or predictor admission, and no live row may be relabeled dead to evade legality. Separating recurrent unroll membership from anchor loss_mask correctly preserves the already approved objective. No technical blocker was found in this bounded context amendment.

## Scope and authority

Approved v3 SHA remains `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1`. This review does not mutate it, activate the proposed cadence, waive a gate, grant broader scope, or approve merge/publication. The exact historical Option A approval remains separate and unchanged. After the activation wording is corrected, the addendum can receive technical approval without waiting for the owner exception, provided it clearly remains inactive for cadence until that second authorization exists.
