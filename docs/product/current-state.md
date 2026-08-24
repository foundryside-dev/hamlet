# Current State — HAMLET / Townlet        Checkpoint: 2026-08-24 · forty-third checkpoint (`PDR-0117`–`PDR-0121`: **unit 3 mid-flight — baselines training, DIV-008 recorded unbound, the cut fully planned — and the architecture reset in one session**: corpus archived, six-doc HLD source-verified Current, filenames ruled convention, VFS audit adjudicated, compiler cleanup executed in a worktree)

## The bets right now

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Steady state
this session; the compiler cleanup (`PDR-0121`, `hamlet-af929afa06`) is hygiene inside
it — parked on an UNMERGED worktree branch (`worktree-agent-afe91c72ba726babd`, 8
commits, hash-identical verified) awaiting the landing gate below.

**2. Token-observation encoding** (`PDR-0108`/`PDR-0114`) · tracker `hamlet-fa6bb6da4a`.
**UNIT 3 IS MID-FLIGHT.** Plan:
`docs/superpowers/plans/2026-08-24-token-obs-unit3-baselines-div008-cut.md`; SDD ledger:
`.superpowers/sdd/2026-08-24-token-obs-unit3-baselines-div008-cut/progress.md`.
- Tasks 1/3/4 landed + reviewed: `scripts/l2_baseline.py` (train/eval/curves, greedy
  eval built from scratch — `EvaluationConfig` is inert, `hamlet-ea959ab97c`); the
  comment-234/242 oracle carry-forward batch; **DIV-008 recorded, NOT bound**
  (record-then-bind — binding by measurement at Task 11).
- Task 2 in flight: **five seeds (42–46) training at E=5000** (floor rule + plateau
  calibration ~ep 400 + the runner's ep-5000 randomization event as hard cap; src-tree
  PIN `1a3b0e7c…`, tree-hash form). Operator killed their llama-server mid-session →
  all five run concurrently. Per-seed on completion: `eval --episodes 100 --eval-seed
  12345` + `curves`; then the frozen record at
  `docs/product/baselines/2026-08-l2-preraster/record.md` (IQM = trigger-1 denominator).
- Phase 2 (Tasks 5–11, the atomic cut) fully expanded, delta-check gated, with the
  re-sequencing addendum (exposure/normalization/max_active_effects INTO the cut; Task
  11 carries an oracle move-forward decision point).
- **FREEZE: no src/townlet or configs/ edits on the main tree until all 5 seeds are
  trained AND greedy-evaled.** All session src work went to the worktree; all main-tree
  commits were docs/CLAUDE.md/README only.

**3. Measure the authoring claim** — retired as record (`PDR-0111`), unchanged.
Instrument redesign still awaits owner promotion; 2026-10-06 pack-disposition clock.

## What this checkpoint did

- Recorded `PDR-0119` (owner's train-here-deploy-there vision articulation; export
  `hamlet-0cdb8a6d1a` now vision-load-bearing; extends `PDR-0024`), `PDR-0120` (VFS
  audit adjudicated — epistemic-access unit shaped into Next), `PDR-0121` (compiler
  two-era assessment + owner-directed cleanup, landing gate defined). `PDR-0117`
  (files-are-transport) and `PDR-0118` (six-doc HLD; owner-amended five→six) were
  recorded mid-session at the owner's direction.
- Roadmap: two shaped units added to Next (declaration-store compiler; epistemic
  access); token bullet stamped with unit-3 state. Metrics: documentation-truth
  movement + the in-flight baseline reading noted.
- Tracker: 9 tickets filed this session (6 audit, compiler cleanup task, hybrid
  substrate `hamlet-157deba962`, declared propagation); comments 243–248 on the
  respective threads. Owner separately archived the wider docs/ legacy tree
  (`c4e8bd58`, "zzz. archive").

## Standing gates & in-flight state (read before acting)

1. **Baseline completion drives everything**: on each seed's completion notification →
   verify exit 0 + 5000 episodes → eval + curves → last one → assemble + commit the
   record → Task 2 complete → **freeze lifts**.
2. **Then land the compiler cleanup**: rebase `worktree-agent-afe91c72ba726babd` onto
   tip, re-run FULL gate set (hashes byte-identical, suite, mypy, matrix both modes),
   merge — `PDR-0121`'s reversal trigger governs (any hash movement → do not land).
3. **Then Phase 2 of the cut** (Tasks 5–11 per the expanded plan).

## Reversal triggers — state

- `PDR-0114` armed (≥80% of the frozen baseline at equal env-steps — the baseline being
  minted IS this trigger's denominator; 8×width / 25% step-time caps; no-natural-token
  surface; payload-identical entities).
- `PDR-0120` armed (if token exposure work doesn't compose with per-token access
  gating, the epistemic unit moves UP the sequence).
- `PDR-0121` armed (post-rebase gate re-run must be clean or the branch doesn't land).
- `PDR-0117` armed (if discovery-merge degrades error provenance beyond repair, fall
  back to a thin pack.yaml index — never the filename mandate).
- Pack-disposition clock **2026-10-06** (`PDR-0111` + `PDR-0114` gate before unit 5).

## Blocked on / flagged for the owner

1. **`vision.md` wording for `PDR-0119`** — the train-here-deploy-there articulation is
   PDR-recorded; incorporating it into `vision.md` §use-cases awaits your sign-off on
   wording (vision-change gate; the content is your own words).
2. Instrument redesign — promote or park (unchanged).
3. WS-7 (`hamlet-e3af412673`, P0) — park or schedule (unchanged).
4. `hamlet-83c8e3b50e` — CI silent on `main`'s third merge; deciding test = next merge.
5. Dependabot #33/#34 + 4 vulnerability alerts on `main` (unchanged).

## Open questions

- Whether the six-doc HLD needs a maintenance rule (e.g., gate-2-style re-verification
  at each merge) or decays like its predecessor — candidate for the next merge's gate.
- `docs/config-schemas/variables.md` is stale (2025-11) and now the weakest doc on the
  trusted path — replace or archive when the declaration-store unit fixes what it
  describes.
- Seed-level greedy eval is deterministic within seed (all agents identical survival) —
  recorded in the protocol; the 5-seed distribution carries the comparison.

## Next session starts here

**If baselines are done**: assemble/commit the frozen record (Task 2), lift the freeze,
land the compiler cleanup branch (gate re-run first), then dispatch Phase 2 Task 5. **If
still training**: the completion notifications drive; nothing else is blocked — all
docs/planning work is exhausted. Branch `project-recovery-2`, all pushed.
