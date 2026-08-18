# Current State — HAMLET / Townlet        Checkpoint: 2026-08-19 · thirty-fourth checkpoint (`PDR-0087`: Trial B — the fifth of nine, the first under Appendix A — is run: **FAIL, prediction CONFIRMED**, the corpus's first failed idea and first BLOCKED classification; north-star 5 of 9 settled, 4 PASS / 1 FAIL, split 0/0/1)

## The bets right now — there are two

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Unchanged, in
flight, untouched this session. Exits when the **pinned oracle can be RETIRED** (`PDR-0058`):
(1) register entries terminal — open (DIV-001/002 `tag-stamped`; 003/004/005 `retired`;
006 `built`); (2) harness verdict vocabulary — **MET** (`PDR-0074`); (3) `Gates green` on a
suite that hides nothing — **MET on `main`**, nightly green again 2026-08-18.

**2. Measure the authoring claim — instrument in use under Appendix A** (`PDR-0077`,
`PDR-0086`, `PDR-0087`) · tracker `hamlet-5fa1f7bfc0` (`in_progress`) · spec PRD-0001 +
protocol incl. Appendix A · metric: north-star **Zero-Python authoring rate (world)** —
expert-ceiling expressibility reading, construct preamble mandatory. **State: 5 of 9
SETTLED (L, F, M, O PASS; B FAIL), 4 pending (D, E, J, K; D/E/J multi-agent), split
0 ABSENT / 0 INERT / 1 BLOCKED; INERT surfaces encountered: 3 in 5 trials.** Then 2 blind
re-runs (owner picks the pair, ≥1 of {L, M, O}) before any reading publishes. Prospective
rows now have first readings: novice-facing (B: all passing facets docs-reachable — first
counter-evidence to the 0-of-4-docs-first prior; L/F/M/O retro-derivation still owed) and
trains-without-incident (B: 6 of 7 clean; double-reset FAIL — reset leak reproduced).

## What this session did

- **RESUME → ORIENT clean**: CI green on all checkpoint pushes (the brief's open loose end),
  nightly on `main` green, no drift; grant re-confirmed unchanged by the owner; owner chose
  **trial five = B** (the ontology-breaker).
- **Trial B run end-to-end under Appendix A** — the appendix's first outing, every step
  executed: A.1 countersign by a fresh agent (7 facets adopted verbatim + one vocabulary
  reconciliation note — countersign-reconciliation note 1 of the 3 that graduate
  countersigning to a PRD criterion), A.2 search pre-registration (CONFIRMED — all winning
  surfaces pre-listed), A.3 discovery paths, A.4 leg-(c) column, A.5 record integrity held
  (probe outputs before verdict text throughout).
- **Headline FAIL, prediction CONFIRMED** (`PDR-0087`, record
  `docs/product/trials/0001/B-20260819.md`, pin `1ef1d950`): facets 1/4/5 PASS; facets 2/3
  BLOCKED — an entity that is a set of occupied cells is not expressible. The sharpest
  finding: **`spawn_item` is unreachable end-to-end from config** (`hamlet-1b9af9088c`, P1)
  — coordinates refused at parse by both DTOs, string strategies refused at runtime because
  the one production call site (`vectorized_env.py:1036`) never passes `agent_positions`
  through a fully-threaded parameter; docs claim "fully implemented and production-ready";
  tests hand-supply what the runtime never does. Also filed: `hamlet-3f97369711` (no
  per-cell scope, ABSENT), `hamlet-4857e6824b` (agent spawn positions undeclarable,
  ABSENT), `hamlet-6c49488b22` (N-D static item placement refused at parse),
  `hamlet-45f501e15b` (`max_items_per_agent: 0` silently nullifies the items catalog —
  INERT surface, counted), `hamlet-02bd5a3eaa` (zone scope dead vocabulary). Comment 169
  on `hamlet-d76684f549` (reset leak reproduced in a second pack). **Nothing fixed —
  file-never-fix held, even at P1.**
- Packs `configs/trial_b_organism/` (L0_organism + L1_contested for B3) and
  `configs/trial_b_organism_2d/` (B1) — disposition OUTSTANDING, **six** packs now on the
  2026-10-06 clock.

## Reversal triggers — state as of this session

- `PDR-0086` triggers: countersign-reconciliation notes at 1 of 3; the "0 of 4 docs-first"
  prior has its first counter-instance (B, live-annotated); construct preamble intact —
  no reading published without it.
- `PDR-0087` new trigger: if the `spawn_item` wiring lands and a re-run turns B's facets
  2–3, the FAIL stands for THIS reading (pinned substrate) — the flip is Trend content,
  not a re-scoring.
- `PDR-0081` budget triggers: armed, none fired — 0 budget-limited records in 5 trials.
- `PDR-0068` (merge banking): ~24 commits ahead of `origin/main` after this session's
  commits vs ~30 threshold — not lit, creeping; the next merge owes `PDR-0039` gate 2.
- Pack-disposition clock: **SIX packs** (L, F, M, O, B×2) promoted-or-deleted by
  **2026-10-06**, else PRD criterion 7 rejects the bet.
- `PDR-0079` trigger 3 watch: the ABSENT/unactioned by-catch list keeps growing (now 10+
  items across five trials) — the review's named failure mode; a WS-4 triage session is
  becoming due.

## Blocked on / flagged for the owner (not blocking)

- **Blind re-run pair selection is YOURS** (Appendix A.8): two of {L, F, M, O, B}, at least
  one from {L, M, O}; comparer is you or an owner-appointed fresh agent. If O: pre-brief on
  the tie case. (B is now also a candidate — a FAIL re-run would test the reject branch
  from the other side.)
- Dependabot `#33`/`#34` on `main` still open; merges to `main` are yours.
- `CLAUDE.md:65` stale citation (thirteenth sighting; owner's file, deferred by choice).

## Open questions

- Whether `hamlet-1b9af9088c` (spawn_item wiring — a one-argument call-site omission plus
  two DTO typings) is a WS-4 unit worth sequencing soon: it unblocks B's re-run story, J's
  durable-posting facet, and the items-as-world-state authoring family all at once.
- Retro-derivation of discovery paths for L/F/M/O (cheap, still owed — B's live annotation
  set the format).
- Whether persistent-lifetime globals + effects surviving reset is intent or defect
  (comment 167/169 on `hamlet-d76684f549`) — B makes the second reproduction; per the
  methodology review, persistence should arguably be *declarable*.
- Next corpus revision (after the nine + blind re-runs): candidates Q/R waiting, plus the
  statistician's substrate-naive stratum proposal.
- Unchanged: `exposed_to` hidden default (unfiled); `recurrent_vision_window_side`
  non-square raise (unfiled); `hamlet-1ad6383186`, `hamlet-7cd887c9e5`,
  `hamlet-266a0a41f0`, `tests/README.md` staleness → WS-5, `cues` inert.

## Next session starts here

**Run trial six under Appendix A** — preflight §3, countersign (A.1), search
pre-registration (A.2), leg-(c) (A.4). Pick from D, E, J, K: **K** (world-acts-on-agent,
the only untouched axis; its doubted surfaces — zone scope, equipped-item modifier chains —
now have direct evidence: zone is confirmed dead, `hamlet-02bd5a3eaa`) or **D/E/J**
(multi-agent; note J's durable-posting facet is discounted twice over by O's and B's
findings). **Alternatively**: the L/F/M/O discovery-path retro-derivation (one short
session), a blind re-run (needs the owner's pair pick), clearing the six-pack disposition
queue, or a WS-4 triage of the trial by-catch backlog (`PDR-0079` trigger 3 watch). Work
continues on `project-recovery-2`.
