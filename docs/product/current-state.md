# Current State — HAMLET / Townlet        Checkpoint: 2026-08-18 · thirtieth checkpoint (`PDR-0083`: Trial F, the second of nine, is RUN — PASS, prediction CONFIRMED, north-star 2 of 2 with the aggregate prediction at its ceiling)

## The bets right now — there are two

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Unchanged, in flight,
no horizon change. Exits when the **pinned oracle can be RETIRED** (`PDR-0058`).

| # | condition | status 2026-08-18 (`main` = `4222a917`, branch = `fb56fbbd`) |
|---|---|---|
| 1 | every `known-divergences.md` entry terminal | open — DIV-001/002 `tag-stamped` (checkpoint-boundary, own rebuilds pending); DIV-003/004/005 `retired`; DIV-006 `built` |
| 2 | harness verdict vocabulary re-earned (`PDR-0056`) | **MET** (`PDR-0074`), narrowed by DIV-006 to the four profile-variable cells |
| 3 | `Gates green` on a suite that hides nothing (`PDR-0059`) | **MET on `main`** — nightly now **2-for-2 GREEN** (second scheduled run `32107696959`, 08-18); `main` still does not carry units 3/4 |

**2. Measure the authoring claim — the INSTRUMENT IS IN USE** (`PDR-0077`) · tracker
`hamlet-5fa1f7bfc0` (`in_progress`) · spec PRD-0001 · metric: north-star **Zero-Python authoring
rate (world)**, standing bar ≥8 of 9 by 2026-10-06. **Second reading: 2 of 2 trials run, split
0 ABSENT / 0 INERT / 0 BLOCKED** (`PDR-0082` Trial L falsified its prediction; `PDR-0083` Trial F
confirmed its). Remaining: 7 trials at one per session, then 2 blind re-runs (criterion 3)
before any reading publishes.

## What this session did

- **RESUME/ORIENT**: workspace loaded, tracker reconciled, grant re-confirmed **unchanged**
  (stamp stays 2026-08-16 per the standing rule; no `vision.md` touch). No material drift found;
  one new fact: the nightly on `main` went 2-for-2 green.
- **DECIDE**: owner chose "Run trial two" (option 1 of the resume brief's proposals). The
  executor selected **F (tool durability)** from the eight remaining — items-axis diversity, and
  the only predicted-PASS left, so it stressed the aggregate prediction's ceiling (`PDR-0083`).
- **DISPATCH/ACCEPT — `PDR-0083`**: Trial F executed per the ACTIVE protocol at pin `e5f7dd7a`.
  **Headline PASS on all four pre-committed facets, both legs** — the wear state is a declared
  item-scoped VFS variable, USE decrements it 3→2→1→0 (idle ticks unchanged), at zero the
  guarded effect stops firing, `obs_item_slots` tracks the value at compiled offset 58.
  **The prediction (PASS) is CONFIRMED — the corpus's first.** Record
  `docs/product/trials/0001/F-20260818.md`; pack `configs/trial_f_durability/`; suite 3281/16/0
  before commit; commit `fb56fbbd`, pushed.
- **By-catch filed, not fixed** (protocol §8): `hamlet-fba3d5aa3c` (a pack with ZERO affordances
  validates and compiles, then crashes at the first observation — declared-and-crashing; routed
  WS-4) and `hamlet-6f27878731` (`docs/config-schemas/items.md` stale in three load-bearing
  places: if-command syntax, item_profiles schema, the false "no item observations" claim;
  routed to `hamlet-7a52a63e0b`). Label `prd-0001-trial`.

## Reversal triggers — state as of this session

- `PDR-0081` triggers: **armed, none fired** — 0 budget-limited records in 2 trials; no blind
  re-run yet; both mid-trial loud errors (stale copied `.compiled`; zero-affordance crash) were
  pack-side, neither stressed the BLOCKED line.
- `PDR-0068` trigger (bank the merge before the next unit): **not lit** — 16 commits ahead of
  `main` against a ~30 threshold; the span includes two `src/townlet/` units and the oracle
  move, so the next merge owes `PDR-0039` gate 2 in full.
- `PDR-0058` trigger 2 (register only grows): not touched.
- Pack-disposition clock (`PDR-0082`/`PDR-0083`): **two packs** — `configs/trial_l_cooldown/`
  and `configs/trial_f_durability/` — must each be promoted to a fixture or deleted by
  **2026-10-06** or PRD-0001 criterion 7 rejects the bet.

## Blocked on / flagged for the owner (not blocking)

- **Nothing escalated this session.** No vision/grant change, no release, no deprecation, no
  pricing, no data deletion, no external party. `vision.md` untouched.
- **Dependabot on `main`**: PRs `#33` (torch 2.11→2.13) and `#34` (pytest 8.4.2→9.0.3) still
  open; any merge to `main` is yours.
- **`CLAUDE.md:65` still cites the deleted `REVIEW-2026-08-15…` file** (ninth sighting; a
  deferred decision, not an oversight — proposed as a bet 08-17 and not chosen).
- Next merge to `main` owes `PDR-0039` gate 2 (README re-verification by method) over 16 commits
  including two src units and the oracle move.
- Cosmetic: filigree CLI needs `--actor claude` on updates to `claude`-assigned issues; the
  comment command is `add-comment`, not `comment`.

## Open questions

- **Prediction calibration, updated**: 1 falsified (L, optimistically for the substrate),
  1 confirmed (F). The aggregate ("1, possibly 2, pass") is at its ceiling — the next pass
  falsifies it, and `PDR-0082`'s lesson (predictions scored the first surface an author would
  reach, not the space of declared surfaces) points that way. The seven remaining trials decide.
- **Blind re-runs are now possible** (two records on file). Criterion 3 wants 2 of 9 by
  2026-10-06, chosen by the comparer, fresh session at the first run's pinned commit, executor
  barred from `docs/product/trials/`. Worth scheduling before the record backlog grows.
- Unchanged: `exposed_to` hidden default in the three profile validators (unfiled);
  `recurrent_vision_window_side` raises on a non-square window (unfiled); `hamlet-1ad6383186`
  (item layout), `hamlet-7cd887c9e5` (reference pack does not compile), `hamlet-266a0a41f0`
  (triage), `tests/README.md` staleness → WS-5, `cues` inert.

## Next session starts here

**Run trial three** — pick from B, D, E, J, K, M, O (protocol
`docs/product/prds/0001-trial-protocol.md`, §3 preflight first: P1 corpus hash, a mismatch voids
the trial) — **or dispatch a blind re-run of L or F** (criterion 3; needs a fresh session that
has not read the trial records). One trial is one session's work; the WS-4 queue (`exposed_to`
default, `hamlet-1ad6383186`, `hamlet-7cd887c9e5`, `hamlet-d45331a367`, `hamlet-6b24c0bd83`,
now `hamlet-fba3d5aa3c`) continues alongside in strangler sessions. Work continues on
`project-recovery-2`.
