# World identity design review R1

Verdict: **CHANGE REQUEST — finite contract amendments, not a plan restart.** Approve the additive declaration placement and ENV's sole accepted-cursor/reset/closure ownership in principle. Do not yet freeze the proposed signatures as an implementation-ready dependent receipt. The missing items below are design gaps, not claims of observed runtime defects in unimplemented APIs. Root can settle these routine additive choices without user approval.

## Scope and evidence

Read repository AGENTS.md, the current no-compat amendment's identity/boundary/completion and finite-slice obligations, wave13 WORLD-IDENTITY-READINESS and WORLD-IDENTITY-DEPENDENCY-READINESS prose, and wave14 WORLD-IDENTITY-DESIGN-HANDOFF. Selectively inspected only ENV, WS and RP from the proposed inventory: environment/vectorized_env.py (1714), exploration/world_curiosity_state.py (734), config/exploration_policy.py (768), actual **3/3216**. Proposed ceilings remain ENV2300 + WS800 + RP1200 + test_world_episode_identity.py500 + new config/world_roster.py200 = **5/5000**. No sixth implementation/helper/probe/fixture/test source was opened. EF/VFS facts below are attributed dependency-receipt evidence, not independent source review. No imports, runtime, tests, Git/index operations, source edits/copies, branches/worktrees, deletion or subagents. This report is the sole write; root metadata is untouched.

Direct evidence confirms the premise: ENV76 constructor and ENV848 classmethod lack roster/seed transport; ENV756 reset mutates in place, including VFS reset at828 before observation encoding; constructor layout sampling precedes first reset. WS155 consumes exact IDs and preserves separate membership/binding and per-ID private RNG identity; RP supplies policy/service vocabulary rather than a real lifecycle producer. No proposed lifecycle API is already established by that evidence.

## Required changes

### R1 — High: completed-boundary release/bootstrap/restore handshake is not yet callable

**Contract:** ENV alone accepts resets; T26 alone decides that all completion, ledger, epsilon, selection and closure obligations have completed. The next reset and completed checkpoint require their agreement.

**Witness:** `prepare_episode(*, batch_episode)` has no release input, setter or bound authority. The design says it requires T26's matching release, whose precise typed handoff is deferred. `close_episode` precedes T26 publication. A first-ever episode has no completed boundary, and a fresh restored ENV has neither the old in-process authority identity nor a defined replacement release. An implementer must invent hidden mutable access, a boolean assertion, or refuse bootstrap/restore. If snapshot eligibility requires a release that is only produced by serialization, a circular boundary results; the text does not intentionally require that cycle but has not excluded it with a concrete API.

**Remedy:** Identity owner must freeze the release type, transport/installation method, issuer binding and idempotency/content validation now; T26 later implements issuance. Explicitly distinguish initial cursor0 bootstrap, active accepted episode, closed awaiting release, released completed boundary, restoring and quarantine. Specify that T26 publishes release after effects and closure, independently of saving; ENV accepts the exact matching release before next prepare/save. Restore validates semantic completed state jointly, then rebinds fresh capabilities without rerunning closure. Record behavior for duplicate/wrong/stale releases and batch nonreuse. Do not require T26 runtime implementation before the identity producer can be tested against the frozen interface.

**Witnesses:** bootstrap succeeds exactly once; close alone cannot authorize prepare/save; matching release does, wrong release is pure refusal; interruption after closure/before release recovers by equal retry; restored completed state can prepare the next fresh episode without a second closure/epsilon effect.

### R2 — High: fresh row permutation conflicts with unspecified ordered identity equality

**Contract:** restore the same authored membership and per-ID learned state/cursors in a requested fresh lane order; preserve exact native validation and canonical event deduplication.

**Witness:** the roster manifest is ordered and included verbatim in execution identity; the envelope also stores `lane_world_ids`, a lane-ordered last-closed accepted tuple and completion content. Restoring checkpoint order `(A,B)` into requested `(B,A)` can either fail roster/execution-identity equality or require rewriting accepted row/event content. Rewriting `(batch, agent_idx)` or its fingerprint would invalidate the accepted canonical completion record. The design does not define which equality is authoritative or where requested order enters `prepare_world_restore`.

**Remedy:** Freeze exact restore arguments and equality rules: persist the authored manifest unchanged; distinguish its original order from destination binding; compare membership/config semantics for reorder eligibility while validating saved binding integrity separately. Preserve historical events/fingerprints and their saved binding unchanged; construct a new next-episode binding by exact ID. State whether execution identity splits semantic membership from binding or carries both with explicit validation. Check every bank/POP/WS validator through owner receipts rather than assuming they tolerate reordered descriptor hashes. If a different precise scheme is chosen, publish it before coding.

**Witnesses:** a genuine native `(A,B)` boundary restores into fresh `(B,A)`; next tuples reverse by ID, historical event content does not change, learned/private RNG state stays attached to ID; changed membership and corrupt saved binding refuse before any installation. The proposed distinct-cursor case needs a valid provenance: every current full-roster reset advances every cursor together from0, so an invented unequal map is only a validation/routing fixture, not evidence of a reachable native history. Keep unequal-map support if required, but label and validate its construction honestly.

### R3 — High: mixed participation retirement needs an exact bank handoff and persisted invariant

**Contract:** every successful full reset consumes each accepted sequence; only genuine participated events have completion effects; an inactive lane remains eligible for the next accepted sequence without a fabricated outcome.

**Witness:** after accepting `(A:1,B:1)`, only A participates. ENV can close sequence1 for the batch; PW05 has no specified retirement call, receipt or state representation for B's begun-but-uncompleted1. Its next begin at2 may reject a still-active1, or a future validator may incorrectly require B's last completed cursor to equal ENV's accepted1. Generic “cross-owner cursor consistency” is insufficient because accepted, completed and retired cursors intentionally differ here.

**Remedy:** Freeze identity-to-PW05 retirement input/receipt semantics and exact consistency equations before the identity receipt is consumed. PW05 owns the later implementation and native fields: accepted sequence, genuine completion marker/content, and explicit nonparticipating retirement disposition must be distinguishable. Retirement is prepared with the whole boundary, committed idempotently without completion/history/scale/epsilon effects, and must finish before closure/release. Equal retry after interruption succeeds; changed participation/content refuses. Empty attempts must use the explicit failed/abandoned phase and reconstruction path, never this mixed completion path. Name an ENV method/transition for abandonment, rather than leaving it only in narrative.

**Witnesses:** A-only participation with B retirement permits next sequence2, no B outcome/effect, native restore preserves the distinction; interrupt retirement acknowledgement and repeat once; forged completed-B or contradictory retirement refuses atomically. All-empty attempt blocks step/prepare/save until reconstruction.

### R4 — Medium: required roster's caller custody remains a choice rather than a frozen handoff

**Contract:** exact authored IDs must originate in a persistent run-owned declaration and reach actual construction before randomization; no row-derived replacement or hidden no-ID path.

**Witness:** the new declaration object is well placed, but the handoff leaves T23 to choose concrete manifest input. Its proposed exact schema does not spell serialized key/value representations or loading/custody interface. A caller could freshly reauthor an ordered list on resume, or expose only a constructor argument with no run-manifest source, while claiming producer completion. The report honestly labels the missing caller; this is a remaining dependency, not evidence that such an input exists.

**Remedy:** Root freeze one small contract now: exact `WorldRosterDeclaration` serialized keys/types, ownership/copy rules, run input name and where its manifest is retained, checkpoint-vs-request mismatch behavior, and required forwarding kwargs for ENV/classmethod/EF. T23 implements the selected runner input, T24 persists/validates it, and the named serial EF/VFS slice forwards it. No need to inspect their code here or choose a new general configuration framework. Distinguish additive producer acceptance from integrated constructor/caller acceptance.

**Witnesses:** real caller consumes one explicit declaration, forwards identical bytes/seed before construction randomness, omission refuses; resume uses persisted membership and the explicitly permitted requested binding operation, never a newly synthesized roster.

## Accepted design decisions and refuted objections

The 200-line declaration module is an additive data owner, not a second episode coordinator. Explicit authored stable strings are a valid roster construction policy; allocator invention is unnecessary. The five-file ceiling is arithmetically valid, but not proof the implementation/tests fit; reslice before exceeding any named ceiling.

Provisional POP/bank preflight followed by one ENV reset acceptance and idempotent accepted activation resolves the amendment's bind/begin-before-reset order. It does not license a preflight that advances private cursors. Retain the accepted receipt through post-reset activation interruptions and block rollout until all activation receipts agree. The acknowledgement-interruption test already proposed is appropriate.

Late reset failure quarantine is compatible with in-place reset. The design explicitly avoids claiming rollback and correctly preserves original reset observations for equal retries after rollout. The implementation must cover interruption during installation with a fail-closed phase; a sequence of ordinary Python assignments alone does not prove atomic installation. No need to reopen every engine helper to implement honest quarantine.

Fresh construction/current-boundary permutation preserves the accepted fresh-episode checkpoint guarantee; no inspected current API establishes arbitrary live row relocation or exact mid-episode continuation. Thus refusing live relabeling is not a confirmed capability removal. Actual simulator permutation/RNG independence remains unqualified until the separately named VFS/simulator owner supplies direct accepted-ID consumption and tests. Leaving the scalar increment/row-key VFS unchanged cannot qualify that boundary, but this design does not claim otherwise.

No proposed removal of the five exploration choices, four network/replay families, authored mechanics, static/adversarial or stage/rate options, current learned-state continuation, private RNG/state isolation or shared Q boundary is identified. Authorizing legacy protocol removal does not authorize lockstep-only world identity or reduced independence. Keep those qualification obligations explicit.

## Approval path

Root may accept additive placement/ownership now and amend the four finite handoffs above in prose. Then a tests-first bounded implementation can begin with exact types, state transitions and owner contracts; PW05/T23/T24–T26 need not be implemented in this producer slice. Tests within this slice prove producer behavior through frozen consumer interfaces, while genuine native/multi-owner/simulator tests remain with the stated finite owners. Do not require those later final integrations to accept a narrow producer interface, and do not call interface acceptance integrated qualification. No runtime or release result is asserted by this review.
