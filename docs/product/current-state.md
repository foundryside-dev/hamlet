# Current State — HAMLET / Townlet        Checkpoint: 2026-09-02 · M4 accepted, rolling into unit 5 (`PDR-0141`)

## The bets right now

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`) remains the Now bet.

- `main` remains at the fourth recovery merge (`9efadd3c`). Active branch is `project-recovery-3`;
  this checkpoint follows `e1615648` (the M4 evidence-path fix, pushed).
- WS-7 is closed. The bet has not exited: WS-3/WS-4 remain open and the oracle is still required.
- The critical path remains WS-6 `hamlet-5e39fcccb0` → WS-2 `hamlet-337b9e80fb` → WS-3
  `hamlet-1f89714685` → WS-4 `hamlet-15050f280a`, all open. The documentation rewrite
  (`hamlet-7a52a63e0b`) shows Ready but stays gated on WS-4 (`PDR-0125`).

**2. Token-observation engineering** (`PDR-0108`, `PDR-0114`, `PDR-0131`–`PDR-0141`) ·
`hamlet-fa6bb6da4a`.

- **Milestones 1–4 are accepted.** M4 closed 2026-09-02 (`PDR-0141`): feedforward 98.9925 / 99.0,
  recurrent 97.315 / 99.0 against the 79.1947 floor at the exact frozen seed-45 budget; one cohort
  identity at `9d4e942f`; `summary.json` re-validates all 3,200 raw outcomes. Durable copies under
  `docs/product/baselines/2026-09-m4-token-regression/`. `hamlet-25fc3fb955` closed at `e1615648`.
- **Unit 5 (`hamlet-55b2826a02`) is the current unit, owner-directed** (*"once its finished,
  you're preauthorised to roll into M5"*). It is unblocked on the tracker and not yet claimed. Its
  remaining precondition is inside it: the 2026-10-06 disposition of the retired-corpus trial
  packs (`PDR-0082`–`0085`, `PDR-0114` — each promoted to a fixture or deleted before migration).
- Evidence-path repairs (`PDR-0140`): the harness owns `curves.csv` / `transitions.csv`, the
  summary gates on the transition artifact, the runner records `failed` / `completed` /
  `interrupted`. Engine root cause — `env.step_counts` increments for dead agents, so every
  recorded per-agent survival is the batch episode length — filed as **`hamlet-d6fc84d147`** (P1,
  triage). It feeds rewards and curriculum under the oracle, so it needs its own differential run.

**3. Documentation truth** (`PDR-0125`) — recovery labelling complete; source-derived rewrite
gated on WS-4. `CLAUDE.md:116` false claim remains a filigree observation (`hamlet-obs-5f1ea6c254`,
expires 2026-09-15).

**4. Authoring-trial measurement** retained as record (`PDR-0111`). Pack-disposition clock
2026-10-06 — now the first act of unit 5.

**5. Weft tooling** (`PDR-0139`): health = doctor clean **and** probe 200 **and** index fresh.
Held at this resume. Warpline/wardline remain uninstalled for rework.

## What this checkpoint did

- `/own-product` RESUME → ORIENT: no drift; grant **re-confirmed unchanged by the owner**
  (2026-09-02, stamp left at 2026-08-31); umbrella `hamlet-fa6bb6da4a` acceptance text corrected
  from IQM to the `PDR-0137` raw-mean rule.
- Resumed both recurrent cells on the exact `9d4e942f` worktree (one per GPU), evaluated each
  once under the frozen protocol, re-derived every cell's artifacts, ran the four-cell summary.
- Root-caused and fixed the three `PDR-0138` evidence defects test-first (`e1615648`,
  `PDR-0140`); filed the engine defect; full `PDR-0127` gate set green (3,837 passed / 11 skipped).
- Accepted M4 (`PDR-0141`), closed `hamlet-25fc3fb955`, copied evidence under `docs/product/`,
  removed the snapshot worktree.

## Standing gates

1. Product-source pushes use Ruff, Black, mypy, no-defaults, compiler-pack validation, the default
   suite and diff integrity (`PDR-0127`). Last executed for `e1615648`.
2. Dependabot #33 (torch) and #34 (pytest) remain open since 2026-08-15; #33 is a separate
   oracle-moving unit.
3. `boundary_wrap` exercises a real axis; `items_smoke` remains demoted as evidence.
4. No release, tag, announcement, 1.0 declaration or external coordination is authorized here.

## Open questions / blocked on owner

- **Nothing escalated this session.** The grant was re-confirmed; every action (push, tracker
  edits, worktree removal, replacing two derived `curves.csv` files with truthful ones) is inside
  it. Primary evidence (checkpoints, databases, TensorBoard events) is untouched.
- **Retained wardline/warpline skill packs and `weft.toml`:** unchanged (`PDR-0139`).
- **Filigree build provenance:** unchanged (owner's dev branch at `2052e7a`).

## Decision checks

- `PDR-0132`: accept and record every milestone before starting its successor — **satisfied for
  M4 by this checkpoint**; unit 5 may start once it is committed and pushed.
- `PDR-0138`: per-cell discard-and-rerun rule — never triggered.
- `PDR-0140`: any cohort checkpoint counter non-monotone or disagreeing with `meta.json` voids that
  cell — none did.
- `PDR-0139`: tool health = doctor clean + probe 200 + index fresh — held.

## Next session starts here

1. Unit 5 is owner-preauthorised. Claim `hamlet-55b2826a02`; the first act is the trial-pack
   disposition ruling (`PDR-0082`–`0085`, `PDR-0114`): for each retired-corpus pack under
   `configs/trial_*` and `configs/trial002_*`, promote to a fixture (it must then carry a
   config-in/behaviour-out exercise) or delete — recorded as one PDR. Three tests already reference
   trial packs (`test_affordance_token_identity.py`, `test_compiled_token_coherence.py`,
   `test_token_emission.py`); check what each needs before deleting.
2. Then the migration proper per the task's acceptance: every surviving pack through its
   smoke/integration path, one committed exercise per live token type and scope, re-author
   `set_encoder_smoke` and L3 authored temporality, delete every superseded surface.
3. `hamlet-d6fc84d147` (engine survival counter) is a separate unit behind a differential run;
   do not fold it into unit 5.
