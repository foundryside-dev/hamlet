# PDR-0110 — The `tensorNd` audit is adjudicated: Branch A, run 2's B-F2 PASS stands, and `PDR-0106`'s rejection stands as genuine search variance

Date: 2026-08-22   Status: **accepted** (the pre-commitment assigned Branch A's adjudication to
the standing agent; the escalation branches B/C did not fire) · the **instrument decision
itself remains ESCALATED** — see "What remains the owner's" below
Author: Claude (standing product owner)
Owner sign-off: the commissioning was the owner's (2026-08-21 resume, `PDR-0106`
recommendation 1); the grant was re-confirmed at the 2026-08-22 resume, in the same exchange
that directed this adjudication ("confirm and commission the audit").
Related: `PDR-0106` (the rejection this audits), `PDR-0098` (the pattern),
`PDR-0087`/`PDR-0095`/`PDR-0096` (the re-run lineage), `PDR-0090` (the freeze, since
superseded for the VFS stream by `PDR-0108`)
Records: `docs/product/trials/0001/B-tensornd-audit-precommitment-20260821.md` (branches fixed
before dispatch), `B-tensornd-audit-20260821.md` (the audit, fresh agent, pin `1ef1d950`)

## Context

`PDR-0106` rejected the instrument on idea B's blind re-run and escalated what happens next,
recommending first a commissioned evidence audit of run 2's `tensorNd` B-F2 PASS — the largest
of the three disagreements, and the one that forks everything. The owner commissioned it at the
2026-08-21 resume. The pre-commitment (three outcome branches, adjudicator fixed per branch)
was committed at `e234635f`, 21 minutes **before** the audit record at `6e3b53a5` — the
pre-commitment's own integrity rule holds, verified by `git log --follow` this session.

The audit's verdict: **Branch A — SOUND.** All four clauses of B-F2's countersigned accepted
evidence hold, established by falsification-designed probes (an asymmetric three-cell pattern
no broadcast can produce; twelve write routes enumerated with verbatim refusals; the
"one entity" claim attacked via `population.size: 2`; eight false-pass classes ruled out).

## Independent verification (the standing agent's owed half)

Per the pre-commitment ("the discriminator is verified by the standing agent as well, not
taken from the audit"), re-verified 2026-08-22 in a fresh worktree pinned at `1ef1d950` —
necessary rather than ceremonial, because `src/townlet/` has moved since the audit (the
2026-08-21/22 VFS-refresh and token-pivot commits), so HEAD no longer equals the pin. Probes
written independently of the audit's scripts, packs rebuilt from the run-2 blind pack:

| audit claim | independent result (2026-08-22, pin `1ef1d950`) |
|---|---|
| per-cell state real: asymmetric `initial_value` reads back exactly, raw storage and `registry.get()` agreeing | exact — `[(0,0,0,0,0), (0,0,0,0,1), (1,2,0,2,1)]` on both surfaces |
| observation per-cell faithful at row-major flat indices | nonzero obs indices `[15, 16, 157]`, exactly as computed |
| R1: cell-indexed `modify` refused at compile, indexed expression read as an unknown variable name | `CompilationError`, same shape |
| R6: whole-container write floods | 3 → 243 |
| C3b: `target.vfs` slab write exists, agent-indexed, not per-cell | 3 → 82 = the 81-cell slab plus the one pre-existing cell outside it — arithmetically exact against the audit's 1 → 81 |

## The call

1. **Branch A is adopted.** Run 2's B-F2 PASS stands, scored on the letter of the
   countersigned pre-commitment — which asks for shape/coordinates, `occupied_count > 1` at
   some tick, 5-tuple cells, and not-a-union-of-positions, all met. The audit's §6 honesty is
   preserved here: a reader who holds that "a set of occupied cells" implicitly requires
   per-cell **authorability** would land on Branch C. That reading is rejected because the
   countersigned list assigns adjacency/growth to B-F5 and directability to B-F6 — both of
   which run 2 itself scored FAIL — and because `PDR-0098`'s discipline is to score the letter
   of the pre-commitment, not to re-adjudicate at maximum-knowledge time.
2. **`PDR-0106`'s rejection STANDS.** The largest disagreement is genuine search variance
   between two competent executors, not executor error. Criterion 3 remains unmet; the
   north-star row remains unpublishable in full — rate, denominator, split, arithmetic.
3. **The re-reading of run 1's four tickets is routed, not performed** — and it was in fact
   already performed on 2026-08-21: framing-narrowed comments stand on `hamlet-1b9af9088c`,
   `hamlet-3f97369711`, `hamlet-4857e6824b`, `hamlet-6c49488b22` (mechanics intact, set-of-cells
   premise falsified as stated; none closes on this ground). Run 1's record is not re-scored
   (Appendix B scope rule).

## Provenance repair — recorded plainly

The adjudication was **enacted on 2026-08-21 without its decision record**: the audit landed,
the eight gaps were filed (`hamlet-cf16cdb6c4` A-G1, `hamlet-57a5126baa` A-G2,
`hamlet-8c354c90bb` A-G3-adjacent, `hamlet-3c9f408fcd` A-G4, `hamlet-cb0ccdaa98` A-G5,
`hamlet-c6c6c241c5` A-G6, `hamlet-0268336cd1` A-G7, `hamlet-8b5af63108` A-G8, plus
`hamlet-f54b887148` from §9), the four tickets were commented "adjudicated BRANCH A" — and no
PDR was written and no checkpoint ran. The thirty-ninth checkpoint (2026-08-22, a deliberately
narrow side-thread) was then written unaware, still calling the audit "the first move" and
carrying `hamlet-a141ab5db3` as an open owner escalation after `03764c6b` had fixed it. This
PDR is the missing record; the fortieth checkpoint carries the full reconciliation. The
lesson is the standing one from `product-state-and-continuity`: work that skips CHECKPOINT is
work the next session contradicts.

Consequence noted, not hidden: several audit gaps were **fixed within a day** under the VFS
refresh (A-G1 at `0f0f2b57` — the expression-write class opens; A-G2 at `15a9702f`;
`hamlet-9e1ae3b7a2` zone/group/message at `6b752b3c`). Those fixes moved the substrate past
the pin; every corpus reading remains protected by executing at pinned commits (`PDR-0108`
restates this), and none of it re-scores any trial.

## What remains the owner's — the escalation, sharpened

`PDR-0106` escalated *what happens to the instrument*; the audit was its recommended first
step, now done. The diagnosis is confirmed: **search variance**. The fork the owner now faces:

- **(a) Amend the protocol with a search-variance control** (e.g., a pre-registered surface
  checklist both executors enumerate against) and re-run criterion 3 — the targeted amendment
  `PDR-0106` recommendation 2 deferred until the diagnosis existed. It now exists.
- **(b) Accept the instrument with a widened construct caveat** — verdict-level
  reproducibility held (FAIL/FAIL, and O reproduced); classification-level did not; publish
  headline verdicts only, never the ABSENT/INERT/BLOCKED split.
- **(c) Retire the corpus reading as record-only** and spend the remaining trials (D, E, J) as
  discovery, not measurement.

No branch is taken here. Trials D/E/J remain runnable as **record, not reading**, under any
branch.

## Reversal trigger

Reopen this adjudication if any of:

- **B-F2's countersigned text is re-read by the owner to require per-cell authorability** —
  the Branch C reading the audit stated and this PDR rejected. The facts need no re-audit;
  only the scoring flips (B-F2 → PARTIAL), and the disagreement narrows rather than collapses.
- **Either verification is shown contaminated** — e.g., the pinned-source `PYTHONPATH`
  arrangement demonstrably importing live-tree code. Both the audit (§3.2) and this session's
  re-verification printed and checked the import path; a contradiction reopens both.
- **A future probe at the pin contradicts the asymmetric read-back or the R1 refusal** — the
  two load-bearing facts. Cardinalities from post-pin trees do not qualify; the pin is the
  claim's scope.
