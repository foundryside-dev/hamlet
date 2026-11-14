# Candidate execution addendum: gate cadence and T08a context

**Status:** proposed, with independent activation paths. Sections1–3 (pytest cadence) require **two keys**: exact-hash Astra MEDIUM technical approval **and** an explicit John/authorized-Emmy cadence exception with a recorded reference. Section4 (PF-06 T08a context expansion) requires exact-hash technical approval only and can activate while the cadence exception is pending. This document does not edit or replace the byte-frozen plan.

**Plan:** `docs/superpowers/plans/2026-11-01-bac-remediation-upgrades.md`, SHA256 `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1`.

**Scope:** two finite execution changes: repository-suite cadence and complete T08a source ownership. Accepted capabilities, approved historical replay decision, package proof/review standard, final acceptance criteria, final review wave, learning protocol and remote CI remain unchanged. No production source/test changes are made by this document.

## Why an explicit amendment is justified

The coordinator measured the original full repository suite at880 seconds on four CPUs. Repeating that unchanged suite before every one of48 package commits costs about42240 seconds (11h44m) of serial suite time alone, before meaningful implementation, focused proofs and independent review. This is an estimate from the coordinator's measured baseline, not a new benchmark or a promised completion time.

The frozen plan requires the full standing gate before every implementation commit. The planner also previously read STATUS §4.3's literal heading, “The gate, run before every commit”; this addendum explicitly proposes to supersede that **cadence**, rather than pretending the existing text did not say it. It preserves all listed checks and final repository/CI scope. STATUS §1 binds the §4 working method; technical approval alone cannot supersede its per-commit full pytest requirement. Before any such gate is deferred, record both exact-hash technical approval and an explicit John/authorized-Emmy cadence exception. T01's already-running full gate continues unchanged; independent work continues under the original cadence while the owner key is pending.

## 1. Required evidence for every package, before dependency release

1. Verify exact source candidate, import path, native fixture validity and nonempty collection before costly execution. Record base SHA plus patch/content identity until the candidate commit exists, then the immutable candidate SHA. No mutable-tree claim substitutes for the detached verifier's actual SHA.
2. Run the package's exact new regression/proof red for the intended cause, implement the bounded change, run it green, and run its relevant existing owner suites from the B report/approved brief. The receipt lists exact test paths, markers, counts, skips and commands; “unit tests” alone is insufficient. Existing suites may execute without extra source inspection; executable helpers read/written still count.
3. Keep the standing non-pytest checks before every package commit: Ruff, Black, mypy, no-defaults lint/ratchet, compiler CLI validation and generated-expression-doc check. These can run concurrently within the measured four-CPU budget. This conservative proposal does not trade away a cheap guard to save pytest time. Exact commands remain those in the frozen plan.
4. Obtain the required fresh other-model adversarial package review against the actual fixed source/contract, including authored negative controls and relevant cross-seam probes. Repair, rerun affected evidence and independently re-review blockers before any dependent package is released. Candidate commits remain unreleased until those requirements pass; this addendum changes no coordinator commit/review integrity rule.
5. The package receipt records `candidate_sha`, `scope`, `focused_commands`, `owner_suite_commands`, `static_commands`, `review_record`, `full_suite_status`, `full_suite_reason`, `unrun_checks`, and `next_full_gate`. A local focused-only pass is labeled **package evidence**, never repository green or BaC qualified. No failure is dismissed merely because the full suite is scheduled later.

Only after **both cadence activation keys** are recorded can the **full pytest repository suite** be deferred to the following bounded checkpoints when no earlier trigger applies. A package worker cannot self-waive a trigger: the coordinator records applicability and its precise reason, and the package reviewer can require an earlier full gate.

## 2. Concrete mandatory full-suite checkpoints

A checkpoint waits for the listed packages and all their dependency reviews/repairs, runs the full standing pytest invocation at one candidate SHA, and records its exact result. The boundaries below are source/contract integration points, not an arbitrary number of commits.

| Checkpoint | Required coherent package closure | Required integration evidence before full suite |
|---|---|---|
| G1 configuration/discovery | T01, T02, T08, T18a, T03, T03a, T04, T05, T06, T07 | Explicit old-document options, effective/authored identities, lossless sidecars, public transport/loaders, native archival-format dispatch policy and schema contract. T08 and T18a are included because G1's actual DAG requires them. |
| G2 replay/learner | G1 plus T08a, T09, T10, T11, T12, T13, T14, T15, T16 | Actual active eligibility, exact historical masks, approved old-history archives outside replay, real short windows, retained warmup, matching PER laws, recurrent PER and real target/gradient direction through runner. |
| G3 exploration/curriculum | G2 plus T17, T18, T19, T18b, T18c, T18d, T18e, T18f, T20, T21, T22, T23 | All five authored providers, successor reward/predecessor predictor phases, one canonical runtime scale, bounded service/state, owned outcomes/clocks, per-lane completed curriculum/adaptation and actual per-world depletion. T19 precedes facade/completion wiring as the DAG requires. |
| G4 restart/transfer/serving | G3 plus T24, T25, T26, T27, T28, T29, T30, T31, T32 | Numeric latest and committed boundary, current full resume, approved archive/fresh replay with preserved available state/clocks, atomic failures, truthful partial/strict/schema transfer, isolated declared serving and current evaluator. |
| G5 persistence/telemetry | G4 plus T33, T34, T35, T36 | Accepted-output fence/drain/file-index receipt, actual runner failure/status ordering, same owned canonical sink outcomes/units and honest effective/intervention metadata. T33 can be implemented earlier after its own dependencies, but G5 integrates its consumers. |
| G6 integrated acceptance candidate | G5 plus T37, T38, T39, source-verified docs and any prepared T40 harness source | All joint authored witnesses and support/acceptance ledger at a common immutable SHA. Run all final required repository checks/coverage/slow and available hardware selection, not just the standing no-cov suite. Then perform the17 final current-source/spec/design lenses and independent synthesis at that same candidate. |
| G7 final post-learning/current-source refresh | T40 finite learning evidence plus any resulting code/harness/docs or repair commits | Keep the existing final-SHA refresh rule: final repository gates,17-lens current-source refresh/synthesis, joint evidence, finite acceptance and mandatory remote CI all apply to final bytes. Unchanged-source receipt refreshes follow the approved plan; no old hash approves new code. |

At G1–G5 the full standing pytest command remains `CUDA_VISIBLE_DEVICES= uv run pytest tests -q --no-cov -p no:cacheprovider -n 4 --dist worksteal` (record a different bounded worker invocation only for a concrete environment reason). The four-worker choice implements the plan's four-CPU quota rather than blindly using five affinity CPUs. Non-pytest checks still run as above. At G6/G7 every final command and required CI/hardware/coverage limitation remains exactly as the approved plan requires.

A full-suite pass at G1–G5 is a regression gate for that candidate. It does not declare unresolved later D/G/X01 contracts repaired or authorize marking the whole subsystem green.

## 3. Earlier full-gate triggers with bounded impact rules

| Change/event | Required immediate evidence | Full-suite timing |
|---|---|---|
| Existing consumed schema/ABI meaning changes: tensor shape/dtype/unit, an existing public signature/result, active/inactive interpretation, enum meaning or population/episode ownership | Run the actual direct consumers' suites/probes plus producer tests and fresh review. Identify every changed consumed field/method; owner inventory remains bounded. | Full suite before releasing that changed interface to dependent packages, even if its planned milestone is later. A newly declared additive module with no executable existing consumers does not trigger this solely because it defines an interface. |
| Existing effective/hash/identity recipe, accepted config precedence, compiled/cache payload, replay/episode/checkpoint serialization version/keys, historical access or validation/install compatibility changes | Current/old identity/roundtrip/import/atomicity/native data controls and all known direct producer/consumer suites. | Full suite at that change's candidate before package release. Standalone HC policy/envelope scaffolding without changing an existing loader is distinct from subsequently wiring the adapter into a public restore path; the latter triggers. |
| Common executable fixture/conftest, dependency/test runner configuration, shared collection, import routing, frozen-input inventory or broad authoring defaults change | Collection/import/fixture/source-SHA preflight, all real affected consumer suites and static guards. | Full suite before release. Adding an isolated new native data attachment/new test module without altering shared executable fixtures is not automatically broad impact; demonstrate its collection/consumer isolation. No fixture-helper source exemption. |
| Failure/surprise implicates a distant subsystem, or impact analysis cannot bound consumers | Reproduce causally, run the actual affected consumers now and independently review repairs. | Full suite before affected boundary is reported green or dependent work uses the repaired contract. Uncertainty is not a reason to postpone. |
| Material cross-slice repair to canonical reward/legality/completion/clocks, effective identity, archival/restore transaction or training/serving isolation | Owner regression plus actual affected consumers immediately; fresh independent fix review, retaining old negative controls. | Full suite at the repaired candidate before boundary green. Then refresh affected final lens/ledger/common-SHA gates as required. |
| Internal algorithm/helper implementation following an already approved unchanged interface, or an isolated additive provider/encoder branch whose old paths/serialization contracts are unchanged | Exact red/green/owner suites and fresh review prove the boundary and controls; record actual unaffected consumers. | May defer to its next named G checkpoint. A label such as “internal” is insufficient if any prior trigger actually applies. |
| Documentation/result-only edit | Required source/evidence consistency and doc/static checks, plus any changed executable example's consumer test. | Intermediate local commits may defer to next named checkpoint; **final** documentation/harness changes still invoke the plan's final-SHA refresh/gates. Required remote CI is never waived. |

These are contract/impact triggers, not “every new function means rerun the whole repository”. For example, defining RC's typed DTO/QT helper before any runtime wiring or defining an unused CountExploration class can be proved locally until integration; changing an existing replay restore's accepted format or wiring a scale factor into actual canonical rewards cannot use that exemption. Each trigger decision is recorded in the receipt and is reviewable.

If an early full gate already passes at the exact SHA that closes its named milestone with no later source/data/fixture change, it satisfies that milestone; do not rerun an identical suite merely to give the same candidate a second label. Any intervening relevant change requires the prescribed new evidence. Failed checks require a causal repair; never blanket rerun until a random pass.

## 4. PF-06: independent technical-only T08a context expansion

The approved task says to adjust an existing all-invalid expectation, but its inventory has no existing test file. Root has supplied the exact boundary evidence: `tests/test_townlet/unit/exploration/test_epsilon_greedy_selection.py` is144 lines; `test_all_false_action_masks_returns_greedy_action` at line22 explicitly labels its lane DEAD. This independently activatable PF-06 amendment adds that file as an owned modification/read after exact-hash technical approval; it does not depend on a cadence exception. It does not authorize treating a dead transport row as a broken live state or deleting valid behavior.

| T08a complete implementer AND reviewer context | Access | Projected ceiling |
|---|---|---:|
| `src/townlet/exploration/action_selection.py` | modify |160 |
| `src/townlet/training/q_targets.py` | read-only |180 |
| `tests/test_townlet/regressions/bac/test_action_probabilities.py` | create/test |350 |
| `tests/test_townlet/unit/exploration/test_epsilon_greedy_selection.py` | modify/test |210 |
| **Total** | **4 files** | **900 lines** |

The210-line ceiling conservatively includes the current144 lines plus eligibility annotation/meaningful tests. Recount before dispatch; no extra EPS/RND source/test file is implied. If another test source must be opened/changed, the coordinator must explicitly recount/reslice first.

T08a's new regression must prove both: disabled live actions get exact0 sampling probability and an active nonterminal all-false legal set diagnoses; an explicitly dead/inactive all-false transport row preserves its dummy/greedy API behavior without contributing any sample, predictor admission or learner experience. The old dead-row test gains an explicit eligibility marker (or the exact approved helper/caller adapter equivalent), not a changed claim that the row is live-invalid. T15 POP owns real active-eligible membership before calling the strategy (filter/select/scatter or explicit mask), correcting the currently fabricated temp dones=False; T18d and T27 preserve that boundary. No empty live row can be excused as inactive, and no historical successor mask is fabricated.

For recurrent T12/T14/T15, the supplied root clarification is unchanged: lengths/real-valid unroll membership and loss_mask are distinct. Anchor loss_mask selects the final real row; it cannot decide hidden unroll validity. Window-mean denominator counts real rows. This is existing P2 semantics, not a new objective.

## 5. Separate activation keys and unchanged completion bar

### 5.1 PF-06 source-context key — technical approval only

The same Astra MEDIUM review must identify this file's exact final SHA256 and approve Section4's complete4-file/900-line T08a context and preserved dead/live semantics. The coordinator may then record that external technical review reference and activate **only PF-06** in ignored execution metadata/task receipts. It does not require, imply or wait for a cadence exception. Until that technical approval exists, the frozen v3 T08a context remains authoritative and the omitted old test cannot be silently read/edited.

### 5.2 Cadence keys — technical approval plus explicit owner exception

Sections1–3 become effective only when **both** are recorded:

1. **Technical key:** same Astra MEDIUM exact-hash approval of this final addendum, including full-gate checkpoints, early triggers and unchanged final standard.
2. **Owner key:** explicit John or authorized-Emmy approval of the concrete per-package full-pytest cadence exception, with a recorded reference identifying the reviewed addendum SHA256, authorizer/authority, scope and retained gates. Record `cadence_exception_reference` and `approved_addendum_sha256`; do not infer this exception from technical approval, general autonomy, historical-replay approval, elapsed time or silence.

The coordinator surfaces the concrete technically reviewed cadence request to the owner and records the actual answer before activating cadence. While that owner exception is pending, **the original per-commit full pytest cadence remains effective**, T01's gate is unchanged, and independently authorized work continues under that cadence. PF-06 may already be active under5.1. A cadence denial leaves Sections1–3 inactive without undoing technically approved PF-06.

After both cadence keys exist, the coordinator records both external references and updates only ignored execution metadata/receipts with the changed gate selection. The approved v3 plan remains byte-identical; no silent rewrite or checkbox mutation. If this addendum changes after technical review, its new hash requires re-review, and the owner reference must cover the final reviewed cadence scope/hash before activation.

### 5.3 Unchanged completion bar

- No package is released without its local regression/owner/static evidence, actual fixed-SHA fresh review and repairs. No boundary is green before its required full gate. Every receipt names unrun checks and the next mandatory full gate.
- Approved `BAC-HISTORY-A-2026-11-01`, all D21+X01/G9/C13 coverage, zero unresolved P1/P2/zero unapproved in-scope gaps, complete final repository gates,17 lenses/synthesis, authored joint evidence, honest K/candidate/P3 status, T40's finite learning and required remote CI remain unchanged.
- This amendment grants no capability reduction, merge/publication authority or new project scope. Its time savings come from avoiding unneeded repeated distant test execution only after the cadence exception is explicitly authorized, not weakening the final standard or accepting a known broken optimizer path.
