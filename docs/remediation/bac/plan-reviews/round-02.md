# BaC plan review — round 02

**Verdict: CHANGES REQUIRED**

Reviewed plan: `docs/superpowers/plans/2026-11-01-bac-remediation-upgrades.md`.
Exact SHA256 verified before and after review: `71a0a08b0659ab3877a7a984844a9d5e158b2fb51940cee9f9c6a4f59e07b671`.
Reviewer: same fresh Astra MEDIUM technical reviewer. Review only; no implementation, tests, baseline edits or delegation.

## One remaining blocker: explicitly authorize the retained historical-defect exception

**Locations:** P2 historical policy lines 78–93, especially line 89; T15 regression line 431; acceptance ledger line 868.

The format inventory and preserving access policy now resolve the implementation ambiguity identified in round 01: exact current-at-pin demo9/population6/uniform4/PER4/sequential5 inputs dispatch losslessly to tagged legacy access, unsupported earlier versions do not acquire an invented promise, and newly admitted rows capture real masks. This is concrete and technically implementable.

However, line 431 deliberately asserts that imported rows continue to produce target51 instead of legal target3. That is the known D01 wrong-direction defect retained in callable auto-resume, not merely absence of a new optional guarantee. Line 868 changes the exit rule to zero unresolved P1/P2 **“in the qualified current contract”**, while the accepted legacy operation remains unqualified. No explicit authorized scope exception is cited. Technical review cannot silently narrow the user's zero-unresolved-P1/P2/zero-unapproved-in-scope-gap closure requirement by assigning a legacy label.

**Required correction:** obtain and record the authorized owner's exact scope decision for this finite pre-capture exception, with an `approval_reference` applying to D01/C05/C10 and any historical X01/C08 limitation that is intentionally retained. State the applicable artifact versions, retained operations, known incorrect/unrecoverable behavior, and that new rows/runs have no exemption. The exception must not become a generic waiver for future failures. Alternatively, choose and test a concrete repair/import policy that meets C05; any loss of working restore/history access remains separately approval-required. The reviewer does **not** require destroying old history, inventing masks, or prohibiting legacy access.

The coordinator was asked for this explicit decision during review. At report issuance no approval record was supplied. Once an authorized narrow exception is documented and consistently incorporated/referenced, no additional blocking technical issue was found in this revision. A later approval must identify the exact final plan hash; this report itself grants no scope approval.

## Round 01 dispositions

- **R1 resolved:** P5a and T18a–T18f define all five accepted selectors, precedence, field roles, typed provider state, canonical successor-phase novelty, predecessor-phase RND service, complete ICM transition context, single DAC scaling, epsilon synchronization and once-only owned completion. Tests exercise real runner → environment → composer → replay rewards. Coordinator X01 evidence is explicitly separate from the original 21 defects; none/zero-scale canonical reward must become zero. The existing bound provider route is correctly recognized rather than mistakenly recomposed.
- **R2 implementation ambiguity resolved; scope authorization outstanding as above:** exact supported versions, identity recipes, pre-storage HC contract, per-buffer adapters, current/legacy tags, atomic refusals and joint tests are now selected. A retained known defect cannot be counted as repaired solely by qualification language.
- **R3 resolved:** F01–F17 inspect current final source at a common detached `FINAL_SHA`; each has a bounded source/probe inventory, fresh other-model reviewer, source/probe obligations and GREEN/NOT GREEN verdict. Independent synthesis reconciles all IDs, repair refreshes changed/dependent lenses and same-SHA gates, and unchanged lenses must recheck final source/diffs before reissuing. Earlier package receipts no longer substitute for final source review.
- Prior nonblocking notes addressed: the actual legacy sequence proposal and correction are explicit; PER tests now check the actual draw law; MLP omission names an existing parameter key; stray leading patch characters are removed.

## Technical and coverage assessment

D01–D21 are all mapped to real implementation/proof tasks: legality, sequence readiness, committed epsilon/checkpoint boundaries, numeric latest, durable shutdown, finite construction, warmup, matching PER estimators, exact-zero action mass, curriculum metrics/horizon/bounds/per-world routing, sidecar validation, truthful transfer, serving modes, authored cadence, content discovery and recurrent PER. D01's retained historical exception is the sole remaining closure issue. D11 remains a probability-mass finding; D15 gets a new full-population witness; D17 remains malformed utility input rather than a normal-producer allegation.

G01–G09 are all delivered or qualified through explicit tasks: mean binding, recurrent geometry, bounded predictor service, pending-tail continuation, adaptation units, gamma zero, serving view/reset/isolation, authored/effective identity and schema-aware transfer. None is silently moved into optional roadmap scope. X01 has its own resolver/provider/composition tasks, real zero/nonzero contrasts and final F08/F16/F17 verification.

C01 operational four-family matrix; C02 effective/preset/finite resolution; C03 canonical public discovery; C04 binding/context preservation; C05 historical legality; C06 exact sampling/readiness; C07 owned events/clocks; C08 provider/reward/service ownership; C09 per-world curriculum; C10 explicit restart/import boundaries; C11 partial/strict/fresh/retained transfer; C12 serving/evaluation/isolation; C13 durable accepted output all have implementation and independent final evidence ownership. C05/C08/C10 legacy closure needs the scope decision above; this does not weaken current captured-path acceptance.

K01–K06 retain explicit dispositions: exact RNG/mid-episode guarantee deferred; generic stage mechanics retained with roadmap; loaders extended and historical FF evaluator preserved; richer criteria retained with truthful roles; K05 index defect repaired; cognition targets unbuilt and allowed. B04-C01 retains API-level evidence plus separate reachability qualification and robust numerical repair. Refuted LR/layout/toggle/base/cache claims stay excluded.

The without-replacement residual-total estimator remains sound for the ordered successive law and stated batch-mean reduction; replacement weights and legacy sequence correction target their separately declared objectives. Recurrent priorities operate on context-dependent window units, not falsely interchangeable row losses. Real-length padding/hidden-state, historical masks, RND FIFO/tail, binding-preserving mean, deterministic/MC inference and recorder acceptance-fence/failure contracts remain concrete.

The 48 implementation-package inventories include new tests and remain at most five files/4880 projected lines; the 17 final lenses include their scratch probes and remain at most five files/4630 projected lines. Dependencies put T18a before effective resolution, T03a before storage schemas, T19 before provider completion wiring, and serialize shared mutable files. Actual ceilings must still be recounted before dispatch as the plan requires.

## Nonblocking implementation clarifications

Count-provider quantization should pin `floor(value / quantization_width)` (or another explicitly chosen signed-boundary rule), the no-stat result for an unseen key, and its finite key representation in the T18b receipt. These are ordinary bounded implementation decisions; do not let a positive-only test accidentally leave negative-bin behavior undefined.

The finite learning cohort is defined, with authentic constant/random/scripted controls and no implied convergence claim. Final review/gate refresh after harness or documentation changes is explicit. Technical approval starts the already-authorized implementation/repair cycle; it is not the completion of that cycle.

## User policy and inspection receipt

No capability removal is selected: presets, zero widths, linear/interaction mean, attention, sampling and pacing modes, current stage/recording choices, public loaders, partial transfer and stochastic serving remain available. Count/ICM additions are finite additive implementations of accepted selectors. Preserving historical access is consistent with that policy; exempting its known defect from the final closure bar requires the explicit scope decision, distinct from a removal approval.

Cumulative implementation inspection remains exactly one allowed file: pinned `src/townlet/training/sequential_replay_buffer.py` lines 160–330, conservatively charged its full 543 lines. No additional implementation/test file was opened in this round. Coordinator boundary facts and X01 JSON were read as attributed evidence; the coordinator probe source was not opened. No new probe/test campaign was run by this reviewer.
