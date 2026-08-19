# PDR-0094 — An idea's bucket is the most severe class among its failing facets: INERT > BLOCKED > ABSENT, so Trial K counts BLOCKED

Date: 2026-08-20   Status: **accepted** (owner-ruled at the resume)
Author: Claude (standing product owner)
Supersedes nothing. Completes: `PDR-0092`'s deliberately open gap.

Related: `PDR-0079` (every miss classifies ABSENT/INERT/BLOCKED; escalation watches INERT),
`PDR-0086` (Appendix A), `PDR-0092` (Trial K, which surfaced the gap and left it open)
Artifacts: `docs/product/prds/0001-trial-protocol.md` — new **A.6.1**; `docs/product/metrics.md`
— north-star row split

## Context

Protocol A.6 rules only the INERT tiebreak: an idea counts INERT if **any** failing facet is
INERT. It is silent on an idea whose failing facets carry no INERT at all — which is exactly
Trial K (F1 ABSENT; F7 BLOCKED on the named surface and ABSENT for the capability). `PDR-0092`
recorded the gap and **refused to self-adjudicate it**, leaving `metrics.md`'s split incomplete
and carrying the hole explicitly. It was the single item blocking the published split.

## Options

1. **Precedence completion** — most severe class among failing facets wins, ordering
   INERT > BLOCKED > ABSENT. K counts BLOCKED.
2. **Decisive-facet rule** — bucket by the facet that decides the headline. K counts ABSENT
   (F1 is the precondition three other passes are conditional on).
3. **Leave K unbucketed**, report by facet, publish the split as 0/0/1 plus a footnote.

## Call

**Option 1, the owner's ruling.** A.6.1 is written into the protocol, K counts **BLOCKED**, and
the idea split reads **0 ABSENT / 0 INERT / 2 BLOCKED (B, K)** over six settled.

## Rationale

The ordering extends A.6's own stated logic — *conservative in the direction the escalation clause
exists to protect*. INERT is worst because the substrate lies to the author; BLOCKED next because
a declared surface refuses; ABSENT least because an unbuilt surface is a build list, not a lie.

The decisive-facet alternative was heard and rejected on a specific ground: it makes bucketing an
**executor judgment**. A.6.1 is applied by reading the facet table, so a blind re-run derives the
same bucket from the same classifications — which matters directly, because the second blind
re-run is idea B, a FAIL whose classification comparison is exactly what the reject branch turns
on. A rule requiring judgment would have imported executor variance into the one comparison
designed to detect it.

The ruling was takeable at all because it **cannot move the escalation counter**: the INERT count
is 0 under either option. Nothing gated on this choice except the published split's completeness.

It was recorded as A.6.1 and committed **before the first blind re-run returned**, with the
amendment stating its own pre-registration — a bucketing rule timestamped after the run it governs
is worth nothing.

## Reversal trigger

If a future trial produces failing facets whose most-severe class **misrepresents the finding** —
concretely, an idea bucketed BLOCKED on one incidental refused surface while its substantive
failure is a broad ABSENT — reopen A.6.1 and consider a two-part report (bucket + headline cause)
rather than a single bucket. The trigger fires on the trial record, not on discomfort with a
number.
