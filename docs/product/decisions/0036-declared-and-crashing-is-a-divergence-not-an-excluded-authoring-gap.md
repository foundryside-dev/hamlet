# PDR-0036 — "Declared-and-crashing" is a divergence; the register's authoring-gap exclusion does not reach it

Date: 2026-08-14   Status: **accepted** (within grant — a scope call on an existing artifact's
own rules; commits no new work beyond the entry it authorizes)
Author: Claude (standing product owner)
Related: `PDR-0035` (the knockdown whose entry this authorizes), `PDR-0028` (the routing rule
the exclusion implements), `PDR-0034` (inertness is invisible to a differential instrument —
the reasoning this PDR inverts), `PDR-0007` (not-yet-enabled vs inert)
Tracker: `hamlet-e3af412673` (WS-7) · Artifact: `docs/oracle/known-divergences.md`

## Context

The first knockdown (`PDR-0035`) fixes three declared substrate configurations that today
compile and then crash at `env.reset()`: `observation_encoding: scaled`; `topology: cubic`
with `active_vision: partial`; and `width != height` (assessment §3, executed — these are
among the few findings verified by running, not source-traced).

Registering that divergence runs into the register's own exclusion clause
(`known-divergences.md:29`):

> **What does NOT belong here:** … **Authoring-surface gaps** (declared-but-inert,
> unauthorable) → WS-4 (`PDR-0028`).

The three crashes plausibly fall under it — the assessment files them in §4's *authorability
ledger* and routes the fix to WS-4 at line 227. Writing a register entry for a surface the
register's own text may send elsewhere is precisely the hazard `PDR-0034` caught one
checkpoint from doing damage: an instrument credited with scope its definition does not give
it. So the question has to be settled and recorded, not stepped over.

## Options

1. **Honour the exclusion literally** — these are authoring-surface gaps, so no register
   entry; route the crash fixes to WS-4 and pick a different first knockdown.
2. **Register them** — argue that "declared-and-crashing" is a third category the exclusion's
   two named cases do not cover.
3. **Widen the exclusion clause** to name crashes explicitly, either way, and follow it.

## The call

**Option 2**, on the exclusion's *reason* rather than its wording.

- The clause names two things: **inert** (declared, silently ignored) and **unauthorable**
  (no YAML door exists at all). These crashes are neither: the door exists, the value
  validates, and the runtime dies. That is a third category — *declared-and-broken*.
- The exclusion exists **because inert surfaces produce no divergence.** That is `PDR-0034`'s
  finding stated from the other side: a surface inert in the oracle and inert in the rebuild
  yields identical traces and correctly reads AGREE, so registering it would be meaningless.
  A crashing config that the rebuild fixes produces a large, trace-visible divergence. The
  reason for the exclusion does not reach it.
- **Filing and adjudication are different axes.** WS-4 vs WS-7 decides who does the work
  (`PDR-0035` decides it: the knockdown). The register decides what the harness is told. If
  the rebuilt system behaves differently from the oracle on any surface, the register must
  carry it or the harness reports a rebuild defect — regardless of which stream did the work.

Option 3 is deferred, not rejected: the clause is not wrong, it is silent on a case that had
not arisen. If a second declared-and-crashing surface comes up, widen the clause then, with
two instances to generalize from instead of one.

## Consequences

- **DIV-003** is authorized: the substrate→observation-dim seam, recorded **before** the seam
  is cut, per the register's own rule (`known-divergences.md:125`).
- The expected diff shape is unusual and must be stated in the entry: the oracle side does not
  merely differ, it **fails to produce a trace at all** (`OLD_SIDE_ERROR`), while the rebuild
  produces one. That shape is what makes `PDR-0037` blocking.
- The register's `What does NOT belong here` section is left **unedited**. This PDR is the
  record of why one case sits outside it; amending the artifact on a single instance would be
  generalizing from one.

## Reversal trigger

- **Reverse** if the knockdown's own work shows the three crashes are in fact fixed by
  *enabling a declared-but-inert surface* rather than by repairing a broken one — that would
  put them inside the exclusion as written, and the entry should be withdrawn and the work
  routed to WS-4.
- **Widen the exclusion clause** (Option 3) once a second declared-and-crashing surface is
  registered, so the rule is generalized from evidence rather than from this one case.
