# T17 independent R1 static review

2026-11-02. Candidate tree `5d4685b55ccd85879d0627bb55bbc20277c58af4`, base `a0802a442bc7ea529de650b8705629923a0e6c72`, as identified by the root handoff and `wave11/r1-candidate.json`. Existing `/workspace/hamlet` only. Static disposition: **no confirmed blocking implementation defect found within the five-source boundary**. This is not runtime acceptance or full programme qualification.

The task brief's historical readiness prohibition is superseded by root's actual R1 review scope. Reviewed its accepted P4/G01 contract, implementation receipt, complete R1 patch package, candidate manifest metadata/inventory, and the complete five named sources. Independently counted and SHA256-hashed those sources; all match the manifest: NET655 `24d4a8627255dab42b3b9b64995c62235f71f25ea04cdbaace6616f1b6e899ed`; NF179 `31b1340b6a125754ae15dbcc981223a4a6f4056ebf9db38ffbe63ba0ff9dd75c`; read-only BC568 `6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079`; read-only OP294 `10dc3ef7dc288d954147046c95bc8362df2162f3829986be26b2724e86dd4916`; owned test640 `bdb25f6e33bae64ede392dfb8ed4fbe4b7521a6dc201184e547decaeabefe544`. Total2336. No sixth implementation/helper/probe/test was opened. Supplier fixture/ENV handoff prose was consulted, without following implementation links.

## Severity and disposition

- **Confirmed P0/P1/P2 defects: none found.** Actual mode wiring, placement and preserved computations support the accepted contract.
- **Nonblocking evidence limitation:** `test_token_binding.py:543` names an object `old`, but constructs it from the current class, whose retained constructor and new route share `_initialize`. Thus equality proves current direct/explicit/omitted route equivalence, not an independent prepatch golden execution. The reviewed patch supplies the additional historical preservation evidence: unchanged linear layer geometry/order, unchanged forward/pooling/attention/LSTM/head code, and no new RNG-consuming operation before those modules. No runtime historical golden comparison is claimed. A future independent baseline oracle would strengthen regression detection; this is optional, not a request to expand T17 or alter the frozen test.
- **Qualification pending:** my independent runtime has not run. Root separately reported meaningful R0 28 failed/6 passed with real fixture valid, and subsequently R1 owned34 passed/no skips with custody PASS. These are attributed root results, not my own runs, and counts alone do not establish acceptance. Affected consumers/guards were still running when root sent that update.

## Contract and code assessment

P4 requires an explicit validated encoder pair, omission retaining recorded linear, both mean and attention, a per-type joint descriptor/live-payload Linear→ReLU→Linear before pooling, exact old linear state/behavior, target-owned nonpersistent context, and constructive binding/absence/memory evidence.

1. **Effective mode routing — concern refuted.** BC:147/172 independently attach `TokenEncoderOptions` to token-set/recurrent configurations. OP:23–42 rejects unknown modes, missing/nonpositive interaction width, and a linear hidden width; omission resolves centrally to versioned linear semantics. NF:79–93 and153–164 resolve that declaration and pass both explicit values into the matching wrapper. NET:252/449/553 require both keyword-only values. Constructors retain their historical linear meaning, per the adopted seam, without inventing an interaction width.
2. **Post-pooling MLP or affine-only implementation — refuted.** NET:312–335 creates one direct Linear or Sequential per live type, with nonlinear-mode Linear indices0/2 and explicit hidden geometry. NET:380–383 assembles fixed descriptor plus live payload and passes the complete payload to that row encoder before any pooling. The exact two-row feature at test:328/471 yields ReLU(v+c−1), hence (.0+.75)/2=.375 versus (.0+.25)/2=.125. This is constructive, not an assertion that random Q weights distinguish.
3. **Lost mean/attention or changed linear state — refuted statically.** Linear ModuleDict names, creation order, zero type vectors and subsequent attention/head/LSTM order are preserved in the supplied diff. Mode/width attributes are Python values, not new state tensors. NET:387–418 retains masked mean, actual QKV attention with MATH backend, key exclusion/all-empty guard, output masking and count clamp. Test:489 independently computes content-weighted nonuniform attention, so the suite does not establish attention preservation solely by forcing uniform attention. Simple/dueling/factory feedforward code is unchanged.
4. **Source context overwrites target context — refuted within the supplied API boundary.** NET:312 constructs its assembler from each supplied target spec, with no replacement/loading of context. Test:363 and590 move context and compact rows together, construct a fresh target, strictly load learned state, compare pooled/Q/hidden results within1e-6, reject context/scatter state keys, and include the opposite compact-row-only reassignment control. The claim that assembler context/scatter buffers are nonpersistent and absent poisoned rows become exact-zero assembled rows is attributed to fixture handoff sections “Target-owned assembly” and “Preserved linear control”; I did not inspect TI. NET's output-side mask then cuts absent encoder parameter gradients for finite assembled rows. This does not claim a separate checkpoint transfer/refusal implementation was reviewed.
5. **Vacuous authored binding/absence evidence — refuted by test construction.** Test:177–243 compiles authored complementary variables, uses public reset/legal WAIT, asserts actual values/presence and equality of every other compact coordinate, and derives its denominator from the live roster. Test:513 selects a Q output and checks an analytic LayerNorm/head result, not random weights. Test:590–640 first proves present MLP parameter gradients nonzero, then verifies poisoned/clean absence equality, exact-zero absent type/row gradients, and exact-zero all-empty pooled output/all encoder gradients. It correctly does not require the biased Q-head to output zero.
6. **Recurrent history weakened or reset each frame — refuted statically.** NET:637–655 preserves zero hidden construction, flattened per-frame encoder, one sequence-level LSTM call, returned hidden state and head. Test:398 proves whole/threaded sequence agreement and one LSTM call, compares the same current frame after different histories, requires interaction-mode selected-Q separation and truthful linear alias, and requires nonzero recurrent gradient. Dropout and hidden geometry remain forwarded unchanged.

No request for redesign, source expansion, capability removal or optional programme follows from this review.

## Proposed independent verification — not yet executed

Bounded selection: the following12 exact existing nodes, all under `tests/test_townlet/regressions/bac/test_token_binding.py::`. IDs are derived statically from the existing decorators; no collection was run. Run only after root separately clears/schedules runtime against the unchanged candidate, using root's sanctioned environment/thread/plugin controls.

```text
test_from_resolved_encoder_requires_explicit_selection[interaction_mlp-3-attention-recurrent]
test_from_resolved_encoder_requires_explicit_selection[linear-None-mean-encoder]
test_mean_can_bind_descriptor_value[token_set]
test_mean_can_bind_descriptor_value[recurrent]
test_authored_mean_can_bind_descriptor_value[token_set]
test_attention_retains_nonuniform_row_interactions[interaction_mlp-recurrent]
test_attention_retains_nonuniform_row_interactions[linear-token_set]
test_linear_mean_is_preserved[mean-recurrent]
test_linear_mean_is_preserved[attention-token_set]
test_semantic_permutation_absence_and_memory[interaction_mlp-mean-recurrent]
test_semantic_permutation_absence_and_memory[interaction_mlp-attention-recurrent]
test_semantic_permutation_absence_and_memory[linear-attention-token_set]
```

This selection attacks invalid/missing selection, both factory families' exact mean witness, authored selected Q, true nonuniform attention in both modes, legacy route state/forward equality, context ownership, poisoned absence and both MLP layers' gradients, all-empty gradients, and recurrent history under both aggregators. No sixth probe or new test is proposed.

Custody: this ignored receipt is the only write. No project imports/runtime/collection/pytest/compiler/lint, source/index/commit/push/delegation, new branch/worktree/project source copy/deletion occurred. Existing14 worktrees were left untouched. The ignore rule was verified before writing. Stationary pending root runtime clearance.

## Static cadence-trigger assessment (follow-up)

Read EXECUTION-ADDENDUM.md Sections1–3 as prose, SHA256 `2b73403fcd9d139e46009c2f49add6dbe6f99310ce37018ffcf839230845d370`. Fresh hashes of all five reviewed sources still equal the inventory above. This assessment does not supply or assume the addendum's two activation keys; root must establish those recorded keys before using its deferral rules.

Section3's additive-encoder exemption is supported for the numeric/model-state seam: unchanged linear parameter names, module creation order, forward semantics and existing serialization are visible in the reviewed patch; interaction mode introduces separate Sequential parameter keys without redefining the retained linear ones. Neither adding an isolated test module nor adding a classmethod alone mandates an early full gate. Subject to activated cadence and no prior trigger, the next named checkpoint for T17 would be G3.

There is nevertheless a concrete changed construction seam: NF:80/154 now invokes `from_resolved_encoder`, and NET:262–272/462–473/569–583 allocates via `cls.__new__` plus `_initialize`, bypassing `__init__`. Retained direct signatures are unchanged, but factory construction no longer traverses an initializer hook. Root reports an actual direct integration consumer failure at `test_recurrent_brain_yaml_trains_the_recurrent_weight_matrix` that instruments `__init__`. I have not opened that consumer or its failure artifact and cannot independently classify the hook as supported production behavior versus test instrumentation. The original no-blocker static verdict is therefore limited by this newly reported cross-seam evidence; it does not dispose of that failure.

Sections1.4–1.5 require causal repair/review and forbid dismissing the failed consumer because a later full suite is planned. If the separate owner establishes a changed consumed public construction contract, Section3's consumed-interface trigger requires full suite before dependent release. If its impact cannot be bounded or implicates a distant subsystem, the failure/surprise trigger likewise requires full suite before boundary green. If the owner instead demonstrates a bounded obsolete instrumentation hook and preserves the actual BPTT/gradient oracle without changing a consumed contract, the additive-encoder exemption remains a candidate, subject to successful affected-consumer evidence and root's recorded applicability decision. No unconditional deferral or automatic full-gate verdict is made here; root owns that choice after causal evidence. No additional source, runtime, or test edits accompanied this append.
