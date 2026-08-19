# PDR-0087 — Trial B is run under Appendix A and FAILS: the corpus's first failed idea, its first confirmed FAIL prediction, and the first BLOCKED classification

Date: 2026-08-19   Status: **accepted** (autonomous within grant; the trial-five = B
choice was the owner's, made at this session's resume)
Author: Claude (standing product owner)

Related: `PDR-0077` (the bet), `PDR-0081` (protocol), `PDR-0086` (Appendix A — this is
the first trial run under it), `PDR-0082`–`PDR-0085` (the four passes), `PDR-0079`
(classification vocabulary)
Tracker: `hamlet-5fa1f7bfc0` (the bet) · filed this trial: `hamlet-1b9af9088c` (P1,
spawn_item unreachable end-to-end), `hamlet-3f97369711` (no per-cell state),
`hamlet-4857e6824b` (agent spawn positions undeclarable), `hamlet-6c49488b22` (item
fixed placement typed 2-D), `hamlet-45f501e15b` (items catalog silently nullified),
`hamlet-02bd5a3eaa` (zone scope dead) · comment 169 on `hamlet-d76684f549` (reset leak
reproduced in a second pack)
Artifacts: record `docs/product/trials/0001/B-20260819.md` (pin `1ef1d950`) · packs
`configs/trial_b_organism/` (levels L0_organism, L1_contested), `configs/trial_b_organism_2d/`
· probes in the packs

## Context

The owner confirmed the grant unchanged at resume and chose trial five = **B, the
spreading organism** — their headline idea and the corpus's one true ontology-breaker
(an entity that is a set of occupied cells rather than a point). First trial under
protocol Appendix A, executed in full: preflight (corpus hash byte-exact), **A.1
facet countersigning** by a fresh non-executing agent (7 facets adopted verbatim, one
vocabulary reconciliation note), **A.2 search pre-registration** written before the
countersigned list arrived, **A.3 discovery paths** recorded, **A.4 leg-(c)
trains-without-incident column** carried for the first time.

## The verdict

**Headline FAIL** on the countersigned facets: 1 (5-D substrate), 4 (declared-position
food warehouse, gated absorption exact) and 5 (approach gradient; reward moves by its
declared amount) PASS; **2 (mass, not point) and 3 (rooted outward growth) FAIL,
classified BLOCKED** — every declarative route to a durable organism-occupied cell is
refused loudly: explicit coordinates at parse (both DTOs type `position` as string),
the string strategies at runtime (no production pipeline passes `agent_positions` —
one call-site omission behind a fully-threaded parameter), static N-D placement at
parse (`fixed_positions` typed 2-D). The reachable representation is exactly the
group-of-agents workaround the corpus pre-named and the countersigner pre-ruled
never-PASS; the probe shows its failure concretely (the occupied set shrank at tick 1).
Diagnostics: **B1** localizes the failure as substrate-independent (same refusal on
2-D; 2-D differs only in parse-level static placement); **B3** shows exclusive
permanent membership, per-organism observation-encoded extents, and shared-source
absorption all work, while contested CELL occupancy inherits the gap.

**Prediction CONFIRMED** — "FAIL, or a heavy PARTIAL via a group-of-agents workaround"
is exactly what happened. Prediction record: 2 confirmed (F, B) of 5 resolved. State:
**5 of 9 settled — 4 PASS, 1 FAIL; idea split 0 ABSENT / 0 INERT / 1 BLOCKED; INERT
escalation counter 0 of 3; INERT surfaces encountered: 3 in 5 trials** (the new one:
`max_items_per_agent: 0` silently nullifying the items catalog).

## Why BLOCKED and not ABSENT or INERT (the first exercise of that branch)

Per §6: the surface exists and is documented (`spawn_item` with `position`, effects.md:
"fully implemented and production-ready"), it validates and compiles, and every
execution path refuses it with a loud ValueError naming the missing context — not a
pack mistake. That is the BLOCKED definition verbatim. It is not INERT (nothing is
silent — except the items-catalog nullification, which IS counted as an INERT surface)
and not ABSENT (the vocabulary exists; the wiring does not). The deeper reading — no
per-cell state scope exists at all — is filed as its own ABSENT feature
(`hamlet-3f97369711`), because fixing the spawn_item wiring alone would still leave a
multi-cell entity's spatial layout unobservable on gridnd.

## Appendix A, first outing — what it changed

- The countersigner's facet 2 bar ("multi-cell extent readable in the encoded
  observation, attributable to ONE declared entity") was stricter than the executor's
  pre-registered phrasing and governed the verdict — exactly the interpretation-
  pre-commitment A.1 exists to provide. Countersign-reconciliation note 1 of the three
  that would graduate countersigning to a PRD criterion (`PDR-0086` trigger).
- The search plan was CONFIRMED (all winning surfaces pre-listed; no found-by-search
  annotation owed) — the first-reach record continues strong.
- Discovery paths: every PASSING facet's winning surface was **docs-reachable** (shipped
  examples + config-schema docs), first-reached surface worked each time — the first
  counter-evidence to the "0 of 4 docs-first" prior feeding the novice-facing row.
  The FAILING facets required source reading only to establish that the refusal is
  engine-wide.
- Leg (c) produced its first readings: 6 of 7 probes clean; **double-reset FAIL**
  (3 effect instances survive `env.reset()`, stale global in the first post-reset
  observation) — the `hamlet-d76684f549` shape reproduced in a second independent pack,
  exactly as the prospective row's pre-statement predicted for O-shaped packs.

## What was deliberately NOT done

- **No fix was attempted** for any gap, including the one-argument call-site omission
  behind `hamlet-1b9af9088c` — file-never-fix held (PRD non-goal 1), even at P1.
- **The corpus and prior records are untouched.**
- **No verdict language was softened**: the workaround expresses spread-toward-food
  (an agent-swarm mechanic, arguably interesting) but that is not the idea the corpus
  froze, and the headline says FAIL.

## Reversal triggers

- If `hamlet-1b9af9088c` (spawn_item wiring) lands and a re-run of the same pack under
  the same protocol turns facets 2–3, the FAIL stands for THIS corpus reading (the
  substrate is measured as-of the pin) and the flip is the Trend story, not a
  re-scoring.
- If the blind re-run of B (if the owner selects it) reaches a different surface set or
  classification, §7's reject branch fires as written.
- The aggregate context: the agent's pre-registration said "1, possibly 2, pass" — at
  4 passes that is long-falsified; B's FAIL does not un-falsify it (falsified is
  falsified; the record stands).
