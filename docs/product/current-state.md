# Current state — Townlet · 2026-10-02

## Delivered and verified

GitHub main is **`95b2f828dae4f52d6e30e79600fc3491364a1eb5`** after
[PR #44](https://github.com/foundryside-dev/hamlet/pull/44), merged October 1 at
15:08:34 UTC. Its exact-main Lint, Config Validation and Tests all succeeded.
Hosted tests report **4,276 passed / 19 skipped / 15 warnings / 85% coverage**.
[Hosted receipt](evidence/static-access-review/hosted-delivery.md) records identities,
run links and log custody; the previous brief's local-only claim is superseded.

| Package | Accepted contract | Evidence |
| --- | --- | --- |
| Declaration Cut A | Content discovery, scoped merge, provenance/duplicates, authored clock | PDR-0149 |
| Canonical-variable Cut B | Explicit lifetime/default/expression semantics, symbols and typed token scope | PDR-0151 |
| Static access | Explicit finite roles, independent exposure, checked access/write intent, immutable policy and cache/checkpoint identity | PDR-0153 |
| Review repairs | Effect preflight/reapplication, immediate nested refusal rollback, deterministic item allocation and structured variable identities | [PDR-0156](decisions/0156-static-access-review-refusal-and-identity-repairs.md) |

PR #42 delivered the first three at `72977928`; PR #44 delivered repairs qualified
at `7eb7ded3`, with unchanged runtime/test/config source through the merge.
Retained local qualification is **4,277 passed / 18 skips / 15 warnings / 85%
coverage**, plus 397 focused item/effect and 988 compiler/oracle/access checks.
The earlier owner-requested local merge passed 432 post-merge checks. These are
separate readings, not a fresh suite during this resume.
[Verification](evidence/static-access-review/verification.md) retains their limits.
Both requested Filigree Markdown reference files were committed as `80d6a5ce`
and included in PR #44. The three review repair issues remain closed:
`hamlet-f75ff623be`, `hamlet-bae419a592`, `hamlet-940089c925`.

## Selected package: truthful episode lanes

The owner's new branch **`fix/episode-lane-accounting`** starts from main
`95b2f828`. Product discovery and source-validated implementation planning are complete; no runtime fix
or learning campaign has run. [PRD-0005](prds/0005-truthful-episode-lanes.md) is
**planned; implementation unaccepted**. Planning **`hamlet-87d3ef8e23`**
hands off to execution **`hamlet-78ad37dd49`** (unclaimed). Product scope task:
`hamlet-e484af6168`. Existing engine bug **`hamlet-d6fc84d147` is confirmed**.

Fresh real-runtime probes reproduce deterministic deaths at ticks 2/5:

- Environment survival `[5,5]` instead of `[2,5]`; ten reported transitions versus
  seven live transitions and five world ticks. Accounting error: **3**, target **0**.
- Standard/PER replay stores ten transitions and five terminal rows. Recurrent
  lengths are `[2,1,1,1,5]`; repeated finalization leaves registry survival `[1,5]`.
- RND ingestion/statistics consume ten samples; adaptive history is `[2,1,1,1,5]`.
  Adaptive weight remains 1.0. Gradient updates were suppressed in discovery.
- A lifespan-five case gives a retirement bonus to the already-dead lane at tick 5.

[Baseline evidence](evidence/episode-lanes/baseline.md) retains commands, script
copies, raw-log digests and source closure. The coordinator repeated both probes
with byte-identical logs. Runner live-transition budgeting already counts on entry
correctly; curriculum currently completes once at batch end with wrong survival,
not repeatedly on death. Planning subsequently executed real DB/TensorBoard/recording and both exporters:
DB slot0/TB early survival is five instead of two; two batches contain14 live
transitions but baseline curves claim20. Recorded slot0 contains post-death
rows, and CPU final-meter aliasing changes `.9900000095` to `.9750000238`.
The checkpoint-backed regression transition export remains correct.

[Planning receipt](evidence/episode-lanes/planning/receipt.md) adds a configuration-authored
END_LANE witness through the compiled brain, actual Q/RND updates with identifiable
phantom samples, and a controlled pinned-oracle reproduction. These are parent
defects/setup feasibility, not corrected behavior. The sink probe waited for writer
persistence; ordinary shutdown remains a separate unqualified prerequisite.

The package requires one terminal transition/finalization per lane, correct
replay/RND eligibility, stable completed outcomes, truthful consumers, explicit
cap/budget truncation and clean restart of its own bookkeeping. Authored death
wins a coincident retirement boundary; genuine retirement gets its bonus once.
Acceptance also requires actual learner/predictor update and sink witnesses,
exact parent/oracle attribution and independent criteria review. Product review
is October 9 or the first candidate, whichever is earlier; no shipment forecast.

## Recovery and product judgment

Recovery remains open. **PDR-0058's register-growth trigger remains unresolved**:
fifteen divergences, five retired and ten nonterminal. Review task
**`hamlet-4554a428b2`** must produce a concrete exit/instrument proposal. The frozen
oracle, inputs, current exit and authority grant stay intact. Episode integrity
is a prerequisite for credible learning evidence, not a substitute retirement exit.
[PDR-0157](decisions/0157-episode-lane-package-and-merged-repair-delivery.md) records
this scope and delivery reconciliation.

No current-main multi-scenario compile → render → converge milestone is qualified.
Historical M4 remains four passing token cells at training `9d4e942f`, one training
seed and its fixed protocol. Static access is not per-owner privacy
(`hamlet-83a043a9b9`); effect reset (`hamlet-d76684f549`), initial-item cache fidelity,
RNG isolation, complete BAC cognition, viewer behavior, Murk and model export
remain separate work. No north-star authoring success rate is revived.

Next action: atomically claim `hamlet-78ad37dd49` and execute the
[reviewed plan](../plans/2026-10-02-truthful-episode-lanes.md).
[PDR-0158](decisions/0158-episode-lane-plan-and-boundary-semantics.md) resolves
truncation/bootstrap, scheduling units, reset guard and strict artifact cuts.
Planning probes and the 20-pass/one-skip prerequisite gate do not accept the fix.
Keep the exit review separate; reopen scope if an actual dependency requires it.
This checkpoint is local to the new branch, with no new push or hosted reading
of its documentation commit.
