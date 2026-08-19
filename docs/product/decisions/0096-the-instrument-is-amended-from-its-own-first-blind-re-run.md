# PDR-0096 — The instrument is amended from its own first blind re-run: Appendix B adopts all four proposals, pre-registered before the second

Date: 2026-08-20   Status: **accepted** (owner-ruled: adopt all four, pre-registered now)
Author: Claude (standing product owner)

Related: `PDR-0086` (Appendix A and the precedent that amendments are owner-approved and
pre-registered), `PDR-0095` (the re-run that produced these), `PDR-0094` (A.6.1, the same
discipline earlier the same day)
Artifacts: `docs/product/prds/0001-trial-protocol.md` — new **Appendix B** (B.1–B.6);
`docs/product/trials/0001/O-comparison-20260820.md` §6 (the drafts) and §9.1/§9.4 (the checks)

## Context

The O comparison proposed four amendments with drafted text. Amending the instrument mid-corpus is
an owner call under the `PDR-0086` precedent, so they were escalated rather than applied.

## Options

1. Adopt all four now, pre-registered before idea B's re-run.
2. Adopt only B.1 (the false-reject risk), defer the rest.
3. Defer all four to the next session.

## Call

**Option 1.** Appendix B carries B.1–B.4 verbatim from the comparer, plus B.5 (two minor items)
and B.6 (the discovery-path caveat, `PDR-0097`).

## Rationale

**B.1 is the one that had to land.** A.1 requires a countersigned facet list to be adopted; §7
forbids the blind executor from opening any prior record. Inherit the list and the re-run stops
testing enumeration — the exact step where this comparison found its largest divergence. Enumerate
independently and cardinality diverges again. A.1 did not fix that; it **suppressed** it by
single-sourcing. A.8 is silent. This is the only finding to date that could produce a **false
REJECT**: two independently countersigned lists diverging on cardinality would fire a branch no
engine defect earned. B.1 makes blinding win and adds a mapping step stating the rule both ways —
cardinality alone never fires; an unmapped facet **neither** run demonstrated declarable does.

**Scope, and the one place B overrides A.** Appendix A pin-scopes blind re-runs to the protocol
text at their first run's pin. That rule stops a later change from re-scoring a **completed**
trial, and it stands. It does not sensibly govern a re-run that **has not executed yet** — applying
current governance text to a future execution is not retroactive re-scoring. Without the override
B.1 would be inert for the very run it was written for, since idea B's first run pinned at
`1ef1d950`. Nothing in B re-scores L, F, M, O, B or K.

**Two checks were run that changed what was adopted, and both are recorded:**

1. **B.3's replacement probe was verified executable before adoption** (§9.4). B.3 removes an
   unexecutable probe from §6 and mandates three `CompiledUniverse` attributes instead. Adopting
   those names on the comparer's word would have reintroduced the exact defect B.3 removes, one
   paragraph later. All five resolve at HEAD (`observation_spec`, `.fields`,
   `observation_activity`, `.active_mask`, `compiled_effect_catalog`).
2. **O's own verdict was checked against B.1** (§9.1), because passing under old §7 and amending
   immediately after invites the charge of amending-to-fit. It survives: O1 is satisfied implicitly
   by run 1's pack, O2 was PASSed by run 2 at the identical pin, so neither unmapped facet meets
   B.1's "neither run demonstrated" trigger. Had run 2 found O2 ABSENT, B.1 **would** fire where
   old §7 did not — evidence the amendment catches a real case rather than ratifying this one.

## Reversal trigger

If idea B's blind re-run fires §7's reject branch **on a ground B.1 was written to prevent**
(a mapping or cardinality dispute rather than a genuine classification conflict), B.1 has failed
and Appendix B reopens. If B.2's granularity rule does not produce converging facet counts across
two independent enumerations of the same idea, B.2 is insufficient and the comparer must report it
as a defect in that section, as B.2 itself instructs.
