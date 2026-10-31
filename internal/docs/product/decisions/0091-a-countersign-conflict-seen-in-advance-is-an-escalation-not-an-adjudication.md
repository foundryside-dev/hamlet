# PDR-0091 — A countersign conflict seen in advance is an escalation, not an adjudication: F7 is a capability bar and F9 is left unruled

Date: 2026-08-19   Status: **accepted** (both rulings are the owner's, made BEFORE authoring began)
Author: Claude (standing product owner)

Related: `PDR-0086` (Appendix A.1 countersigning; A.9 the Trial F precedent), `PDR-0092`
(the trial these rulings governed), `PDR-0078` (acceptance is on the instrument)
Artifacts: `docs/product/trials/0001/K-20260819.md` — reconciliation notes 1 and 2, with the
superseded draft retained

## Context

Appendix A.1 requires the facet list to be enumerated by a party that will not execute the
trial, then **adopted verbatim or reconciled in a dated note before authoring starts**. Its
stated rationale: pre-commitment previously bound *evidence* but not *interpretation*, and
interpretation was executor-owned at maximum-knowledge time.

Trial K's countersigner returned a strict list — nine facets, all three mitigation paths
required, thirteen boundary cases, eleven pre-excluded cheats. Two of its provisions collided
with governing documents:

1. It offered a **three-way headline** (all three → PASS, exactly two → PARTIAL, one → FAIL).
   Protocol §1 makes the headline **binary**.
2. **F7 bound a capability to a named surface** — "go inside" must be declared as a
   zone-scoped property, not a coordinate comparison and not an affordance buff. That is a
   faithful reading of the corpus, which names `zone`. It conflicts with `PDR-0086`'s construct
   preamble, which defines this north-star as *"an expert executor finding **ANY** declarative
   surface."*

The second conflict was close to decisive. Trial B by-catch (`hamlet-02bd5a3eaa`) already
showed `zone` was in trouble, so under the strict bar F7 was a near-certain FAIL, and the
all-three ruling would have carried that to a headline FAIL **before a line of YAML existed**.

## What the agent did first, and why it was wrong

The agent drafted a reconciliation that adopted the strict bar *and* assigned itself the extra
work of probing both variants, prefaced "I am not resolving this at maximum-knowledge time."
That preface was false: choosing the bar and choosing the extra work **is** resolving it, taken
by the executor, at exactly the moment A.1 exists to prevent.

The Trial F precedent (`PDR-0086` A.9) does not cover it. There the owner adjudicated *after*
the run, because nobody saw the conflict in advance. **Here it was visible in advance — which
converts an adjudication into an escalation.** Foreseeability is the whole distinction.

## The calls

**Reconciliation 1 — mechanical, no judgement.** Protocol §1 overrides the countersigner's
three-way headline. The PARTIAL band maps to **FAIL**; the facet table carries the nuance. The
countersigner's *bar* is untouched, only the name of the middle band. (Countersign-reconciliation
note **2 of the 3** that graduate countersigning to a PRD criterion; note 1 was Trial B's.)

**Reconciliation 2 — escalated, owner-ruled before authoring:**

- **F7 is a CAPABILITY bar.** It tests "location determines the environmental property".
  `zone` is tried **first** because the corpus names it; its failure is recorded as a
  search-dependence finding and the dead surface filed as by-catch — the pattern set by Trials
  L and O. Cheat #6's substance survives: a bare coordinate comparison in a probe script is not
  a declared region, and an agent-initiated shelter buff does not count, because it breaks the
  world→agent axis the idea exists to test.
- **F9 is NOT pre-ruled.** Whether "item-scoped state read by an effect gate" and "regional
  property read by an effect gate" are one declaration surface or two is left open. The record
  reports, per path, exactly where the mitigating state is declared and where it is read, and
  the owner adjudicates. The agent is explicitly not to settle it by choosing a convenient
  reading once it knows which way its pack needs it to go.

## Rationale

The instrument's value rests on the executor not being able to move the bar. A.1 is the
mechanism, but A.1 alone is insufficient: an executor who can *reconcile* can still relax a bar
under a plausible-sounding governing-document conflict. The durable rule this PDR sets:

> **A conflict between the countersign and a governing document is reconciled by the executor
> only when the resolution is mechanical (one document plainly overrides another on a point of
> form). When the resolution requires judgement about what the trial measures — and especially
> when the executor can already predict which way the resolution moves the verdict — it
> escalates to the owner before authoring.**

Reconciliation 1 is the mechanical case; reconciliation 2 was the judgement case, and the
predictability of its effect is precisely what made escalation mandatory rather than optional.

## Reversal trigger

If a future countersign conflict is reconciled by the executor and the trial's verdict then
turns out to hinge on that reconciliation, this rule has failed in practice: the escalation
test is being applied too narrowly, and A.1 needs a hard rule (escalate **every** non-mechanical
reconciliation) rather than a judgement-based one. Watch for it at each of the remaining trials
and both blind re-runs; the countersign-reconciliation note count (now 2 of 3) is the counter
that triggers the graduation to a PRD criterion.
