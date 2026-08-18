# Current State — HAMLET / Townlet        Checkpoint: 2026-08-18 · thirty-second checkpoint (`PDR-0085`: Trial O, the fourth of nine, is RUN — PASS, the corpus's first STRUCTURAL prediction falsified, north-star 4 of 4; a three-lens methodology review of the instrument is IN FLIGHT)

## The bets right now — there are two

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Unchanged, in flight,
no horizon change, untouched this session. Exits when the **pinned oracle can be RETIRED**
(`PDR-0058`): (1) every `known-divergences.md` entry terminal — open (DIV-001/002
`tag-stamped`; DIV-003/004/005 `retired`; DIV-006 `built`); (2) harness verdict vocabulary
re-earned — **MET** (`PDR-0074`), narrowed to the four profile-variable cells; (3) `Gates
green` on a suite that hides nothing — **MET on `main`**, nightly now **3-for-3 GREEN**
(latest run `32107696959`, 08-18).

**2. Measure the authoring claim — the INSTRUMENT IS IN USE** (`PDR-0077`) · tracker
`hamlet-5fa1f7bfc0` (`in_progress`) · spec PRD-0001 · metric: north-star **Zero-Python
authoring rate (world)**, standing bar ≥8 of 9 by 2026-10-06. **Fourth reading: 4 of 4 trials
run, split 0 ABSENT / 0 INERT / 0 BLOCKED — all four PASS** (`PDR-0085`). Trial O falsified
the corpus's first *structural* prediction (the clearing phase was predicted ABSENT and is
declarable). Remaining: 5 trials at one per session (B, D, E, J, K — D/E/J multi-agent with
the heaviest structural predictions), then 2 blind re-runs before any reading publishes.
**GATE ON PUBLICATION (`PDR-0085` reversal trigger): a three-lens methodology review is in
flight — no north-star reading publishes over an open confirmed validity defect.**

## What this session did

- **RESUME/ORIENT**: workspace loaded, grant re-confirmed **unchanged** by the owner (stamp
  stays 2026-08-16 per the standing rule). ORIENT found real drift: **branch Lint had been
  RED for four pushes** since the Trial F commit (two E501s in `probe_trial_f.py`) — the last
  two checkpoints never read the remote gate. Fixed at `a3318624`, CI green on the fix.
- **DECIDE**: owner chose **"trial four: multi-agent"**. Executor selected **O (adversarial
  bidding)** from D/E/J/O — untouched clearing-phase axis, structural prediction, best
  one-session fit (`PDR-0085`).
- **DISPATCH/ACCEPT — `PDR-0085`**: Trial O executed per the ACTIVE protocol at pin
  `a3318624`. **Headline PASS on all six facets, both legs** — simultaneous bids, declared
  3-tick collection window, `for_each: all_agents` clearing (swap-tested), exact award/charge,
  no-bid guard, full observation encoding. Pack compiled and probe passed on the first attempt
  of each. Suite 3281/16/0 before commit `2dcc2273`, pushed.
- **By-catch filed, not fixed** (protocol §8): `hamlet-4cd664a955` — effect `scope: global`
  validates but every spawn path hardcodes agent scope (INERT); `hamlet-77e4f8b3e3` — no
  declarative path to a standing world process from reset (ABSENT). Both routed WS-4.
- **Owner raised two post-freeze corpus candidates** mid-session — Q (sin/cos day-night
  forcing; recon: no trig in the expression vocabulary) and R (heliotropism; recon: no
  orientation state in the continuous substrate) — captured in
  `docs/product/prds/0001-corpus-candidates.md`, **outside** the frozen corpus, predictions
  deferred to a future re-freeze.
- **Owner directed a methodology review of the trial instrument**: three Fable reviewers
  dispatched (construct-validity critic; RL-practitioner lens; statistical-inference lens on
  a full-context fork). Results land after this checkpoint; findings route to the next
  session's DECIDE and may become `proposed` PDRs.

## Reversal triggers — state as of this session

- `PDR-0081` triggers: **armed, none fired** — 0 budget-limited records in 4 trials (O was
  the first multi-agent-adjacent trial and fit the budget); no blind re-run yet.
- **`PDR-0085` NEW trigger: publication gates on the methodology review** — a CONFIRMED
  validity defect re-scopes the readings by a new PDR before anything publishes.
- `PDR-0068` trigger (bank the merge before the next unit): **not lit** — 21 commits ahead of
  `origin/main` (`a3318624`, `2dcc2273`, plus the prior 19) against the ~30 threshold; the
  span includes two `src/townlet/` units and the oracle move, so the next merge owes
  `PDR-0039` gate 2 in full.
- Pack-disposition clock (`PDR-0082`–`PDR-0085`): **FOUR packs** — `trial_l_cooldown`,
  `trial_f_durability`, `trial_m_combo`, `trial_o_bidding` — each promoted to a fixture or
  deleted by **2026-10-06**, else PRD-0001 criterion 7 rejects the bet. One
  fixture-promotion session would clear all four.
- `PDR-0058` trigger 2 (register only grows): not touched.

## Blocked on / flagged for the owner (not blocking)

- **Nothing escalated this session.** No vision/grant change, no release, no deprecation, no
  pricing, no data deletion, no external party. `vision.md` untouched.
- **Dependabot on `main`**: PRs `#33` (torch) and `#34` (pytest) still open; any merge to
  `main` is yours.
- **`CLAUDE.md:65` still cites the deleted `REVIEW-2026-08-15…` file** (eleventh sighting;
  owner's file, deferred by choice).
- CI Tests on `2dcc2273` was in progress at checkpoint (Lint and Config Validation green);
  read it before citing the branch fully green at that commit.
- Cosmetic: `black --check .` repo-wide flags three archival files under
  `docs/plans/2026-08-11-ws1-pinning-test-sources/` — outside the CI gate, left as
  point-in-time records on purpose.

## Open questions

- **The methodology review's verdict** — the biggest open input. All four predictions have
  fallen, three surface-choice and now one structural; the review asks whether the instrument
  measures the vision's claim (novice-trivial authoring) or something easier (expert finds
  any declared surface). Its findings are the next session's first read.
- **Blind re-runs** (criterion 3): four records on file; the standing agent has read them all,
  so a blind executor must be a dispatched fresh agent at the trial's pinned commit. Worth
  scheduling before the backlog grows further.
- Prediction calibration: the miscalibration mechanism looks consistent (predictions score
  the first-reached surface; trials score any declared surface) — D/E/J are where the
  structural predictions get their hardest test.
- Unchanged: `exposed_to` hidden default (unfiled); `recurrent_vision_window_side` non-square
  raise (unfiled); `hamlet-1ad6383186`, `hamlet-7cd887c9e5`, `hamlet-266a0a41f0`,
  `tests/README.md` staleness → WS-5, `cues` inert.

## Next session starts here

**Read the methodology review results first** — three reports (construct validity, RL
practice, statistical inference); adjudicate findings into filed issues, `proposed` PDRs, or
protocol amendments, remembering the corpus is frozen and the four completed trials stand
unless a confirmed defect re-scopes them (`PDR-0085`). Then choose: **run trial five** (B, D,
E, J, K — protocol §3 preflight first; D/E/J are the structural tests) — **or dispatch a
blind re-run** of L, F, M, or O (criterion 3; fresh-context executor barred from
`docs/product/trials/`) — **or clear the pack-disposition clock** (promote four packs to
fixtures in one session, discharging the 2026-10-06 risk). The WS-4 queue
(`hamlet-4cd664a955`, `hamlet-77e4f8b3e3`, `hamlet-f1dec55b9d`, `hamlet-d45331a367`,
`hamlet-6b24c0bd83`, `hamlet-fba3d5aa3c`, plus the older items) continues alongside in
strangler sessions. Work continues on `project-recovery-2`.
