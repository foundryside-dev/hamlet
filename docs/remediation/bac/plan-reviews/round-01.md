# BaC plan review — round 01

**Verdict: CHANGES REQUIRED**

Reviewed plan: `docs/superpowers/plans/2026-11-01-bac-remediation-upgrades.md`.
Exact SHA256, verified before and after reading: `adcbf635e3230752be9e876862ca0b28b24c1819e1bfe46c3ddce457c407649d`.
Reviewer: fresh Astra, MEDIUM reasoning, planning review only. No implementation, tests, design-authority edits or delegation performed.

## Blocking corrections

### R1 — C08 runtime exploration resolution has no implementing package

**Plan locations:** P1 lines 48–58; P5 lines 94–100; T16 lines 375–383; T18 lines 395–403; T25 lines 465–473; C08 coverage line 682.

The plan resolves replay/RND service options and reports effective intrinsic values, but does not define the owner, precedence or factory interface that selects the accepted exploration strategy and intrinsic-weight/annealing parameters from authored drive/training declarations. T18 changes predictor service; T25 replaces the predictor admission bypass; neither routes strategy selection. B05's contract table explicitly records this existing unfinished seam, and BAC-C08 requires one runtime owner. Generic field-role metadata does not establish the selected runtime behavior.

**Required correction:** add a bounded task (or explicitly extend an existing task within its read budget) defining the resolved exploration policy fields, precedence/active-inactive roles, supported strategy construction, runner/population wiring, and continuation ownership. Supply authored strategy/parameter contrast tests through real runner construction and reward composition, including zero weight, per-lane epsilon synchronization and once-only adaptive completion. Preserve accepted choices; where a choice is currently unqualified, explicitly disposition it rather than claiming C08 closed by predictor service alone. Request coordinator-owned interface evidence instead of exceeding the source budget.

### R2 — Historical replay preservation remains an undecided contract

**Plan locations:** P2 artifact policy line 74; T24 lines 455–463; T38 line 602; exit lines 706, 711.

The plan correctly forbids invented masks and silent history deletion, but defers the actual supported-version inventory and preserving import policy until T24, after T10–T12 have changed strict storage schemas. A maskless constrained history is merely labeled unqualified at joint acceptance. There is no executable selected route for its existing learned-state access, nor a decision establishing that such access was never supported. Consequently a worker cannot both implement strict new legality and satisfy the promised historical access/zero-unapproved-gap exit without making a new scope decision.

**Required correction:** inventory the supported historical format/access promises now using bounded owner evidence, then define the selected version/mode dispatch and acceptance tests before the storage packages run. A separately explicit preserved legacy access mode may remain honestly outside the new historical-legality guarantee; sufficient immutable reconstruction is another possible route if actually available. Do not silently select dropping replay, all-legal fabrication, or refusal of formerly supported restore. If preservation is impossible, identify the exact concrete approval-dependent alternative and affected artifacts; do not count this row closed or treat technical plan review as approval for it. Include uniform, PER and recurrent import tests and atomic failures.

### R3 — The final independent spec/design/code review is not an executable gate

**Plan locations:** final gate line 617; documentation pass line 713; stop-rule paragraph line 715.

Package reviewers are fresh and bounded, but their approvals precede later changes to shared files such as POP, RR, CK and LIVE. The final verification worker reads only three joint tests and the evaluator; the documentation worker relies on earlier source receipts. The final paragraph mentions full-spec review without assigning fresh final source-review packages, inventories, a common immutable SHA, or final verdict/closure criteria. Running the suites and checking documentation against historical package receipts does not deliver the newly requested fresh independent final spec + design + code review.

**Required correction:** define a final review wave after integration/documentation at one immutable candidate SHA, with explicit bounded source inventories covering the affected contracts (split reviewers to maintain five files/5000 lines each), fresh other-model assignment, current source citations/authored probes, D/G/C ledger reconciliation and cross-seam synthesis. Route P1/P2 or in-scope gaps to repair, re-review affected packages, then refresh final candidate review/gates until the finite exit ledger is satisfied. Preserve honest K/roadmap and P3 dispositions. Approval should start implementation, not end the task; the existing authorization statement is correct.

## Nonblocking clarifications

- P3's conditional residual-total estimator is mathematically sound for the ordered successive draw law. With the specified batch-mean reduction, each coefficient is `((B-k)+1/q_k)/N`; the full-population all-one special case is valid. Independent replacement weights, stopped gradients, factor-one normalization and beta-one-only unbiasedness are appropriately explicit. Tests should check the actual sampler's ordered law as well as a separately enumerated formula.
- P2 preserves historical length-weighted episode/start draws and promises correction, but should spell out `p(window)=episode_length/sum(valid_episode_lengths)/(episode_length-L+1)` for fixed-full legacy sampling, its with-replacement correction toward the declared uniform window objective, and the adapter's selection rule. This prevents an implementer accidentally applying the PER successive sampler's receipt to the legacy sequence law.
- T28's literal `encoder.encoders.meter.bias` omission applies to the linear encoder. For the MLP mode, target an actual shared layer bias by its final declared key; a nonexistent-key test would not prove incomplete shared-parameter reporting.
- Remove literal leading `+` characters in the final ledger/documentation paragraphs. They currently read like unapplied patch lines.

## Coverage audit

All 21 defect IDs are explicitly mapped to implementing/proving tasks; none are missing from the register: D01 T08–T15/T37; D02 T12/T15–T16/T37; D03 T24–T26/T38; D04 T24/T26–T27/T38; D05 T33–T34/T39; D06–D08 T01–T03; D09 T10–T16/T37; D10 T13–T15/T37; D11 T08a/T37; D12–D14 T19–T23/T35/T37; D15 T22–T23/T37; D16 T04/T33/T38; D17 T28/T30/T38; D18 T15/T27/T31–T32/T38; D19 T02/T24–T26/T36/T38; D20 T05–T07/T32/T38; D21 T14–T16/T37–T38. D11/D15/D17 evidence limitations are accurately preserved.

All nine gaps are mapped: G01 interaction encoder/T17; G02 readiness/retention/T12–T16; G03 service/T18/T25; G04 tail/T18/T25–T26; G05 adaptation/T20–T23; G06 gamma/T01–T03; G07 serving/T27/T31–T32; G08 identities/T02–T03/T29; G09 artifact/transfer/T24/T28–T30. Adopted gaps are not dismissed as out of scope.

Contract audit: C01 operational matrix present; C02 effective/preset/finite semantics present, exploration resolution needs R1; C03 public discovery present; C04 additive mean binding proof present; C05 current historical masks and recurrent boundaries present, old imports need R2; C06 estimator/readiness/recurrent PER present; C07 clocks/outcomes present; **C08 incomplete under R1**; C09 per-world metrics/adaptation present; **C10 historical access incomplete under R2**; C11 explicit partial/fresh/retained transfer present; C12 modes/reset/isolation present; C13 durable drain/receipts present. All contract closure claims additionally depend on R3's final independent review.

K01–K06 have explicit bounded dispositions: exact stochastic continuation deferred; generic stages/mechanics retained with roadmap; public loaders extended and historical evaluator preserved; richer criteria retained with truthful status; K05 repaired; cognition targets unbuilt and permitted. B04-C01 remains an API candidate with finite-numeric repair and separate production reachability qualification. Refuted scheduler/layout/toggle/base-brain/cache hypotheses are excluded from defect work.

## Policy, budgets and execution check

The preferred plan preserves mean/attention/linear choices, zero-width policies, presets, PER draw choices, RND pacing, accepted stage/recording fields, public loaders and partial transfer. No categorical cognition/algorithm ban or selected capability consolidation was found. Historical restore is a concrete remaining policy decision, not permission to remove access. Technical approval cannot substitute for the user's reduction approval.

The table declares all 41 package inventories including T08a for workers and reviewers; listed inventories have at most five files and at most 4880 projected lines, with new tests included. Shared mutations are serially ordered and recount/split is required if projected ceilings are exceeded. Final review inventories still need R3. The finite learning cohort and named controls are present; no learning success is claimed. The expanded authorized implementation/repair loop and zero unresolved P1/P2/zero unapproved in-scope gaps are stated, but are not yet fully executable because of R1–R3.

Actual reviewer implementation inspection: only pinned `src/townlet/training/sequential_replay_buffer.py`, lines 160–330; conservatively charged the full 543-line file. Four allowed files remain unopened. Reference reads include the plan brief, r2 design, complete findings/manifest, approval items, detailed B04/B05/B10 evidence and relevant B09/VFS methodology excerpts. No sixth-file or broad implementation scan occurred.
