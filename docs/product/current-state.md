# Current State — HAMLET / Townlet        Checkpoint: 2026-08-22 · thirty-ninth checkpoint (`PDR-0107`: **relational/message observation exposure WAITS for token observations** — the decision gate `hamlet-fa8ed299c5` is adjudicated and closed, no fixed-width relational blocks get built, and the Phase A work plan for the token-observation pivot is written, committed, and **gated behind the `PDR-0090` freeze**. A side-thread session by owner direction; the instrument decision from `PDR-0106` remains the governing escalation and was NOT touched)

## The bets right now — there are two

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Unchanged, in
flight. Exits when the **pinned oracle can be RETIRED** (`PDR-0058`):
(1) register entries terminal — open (DIV-001/002 `tag-stamped`; 003/004/005 `retired`;
006 `built`); (2) harness verdict vocabulary — **MET** (`PDR-0074`); (3) `Gates green` on a suite
that hides nothing — **MET on `main`** as of the 2026-08-20 nightly at `04062872`.
⚠️ `hamlet-a141ab5db3` still dents condition 3's *reading* — a green compile over no
artifact, on a **shipped** pack.

**2. Measure the authoring claim** (`PDR-0077`, `PDR-0086`) · tracker `hamlet-5fa1f7bfc0`
(`in_progress`) · spec PRD-0001 + protocol incl. Appendices A **and B**.
**⛔ THE INSTRUMENT IS NOT ACCEPTED AND NOTHING PUBLISHES** (`PDR-0106`, unchanged this
session). State of the corpus, retained as record only: 6 of 9 settled (L, F, M, O PASS;
B, K FAIL), split 0/0/2, INERT surfaces 4 in 6 trials, 3 pending (D, E, J — all multi-agent).

## Criterion 3 has FAILED — unchanged, read `PDR-0106` before quoting any north-star number

Both blind re-runs done and split: O reproduced PASS (`PDR-0095`, the vacuous one), B did not
reproduce (`PDR-0106` — three of five mapped core pairs disagree, two invert). §7's reject
branch FIRED. B.1 absorbed the 5-vs-8 cardinality divergence as designed (`PDR-0096` does not
fire). The live fork: **does run 2's global-profile `tensorNd` PASS survive an evidence
audit?** Everything downstream of the north-star waits on that.

## What this session did

- **Adjudicated and closed the relational-exposure decision gate** `hamlet-fa8ed299c5`
  (`PDR-0107`, commit `7dc6f66c`): pair/group/message state is first observed as **token
  observations** under `hamlet-fa6bb6da4a`. Fixed-width relational blocks are manufactured
  debt under the owner-authoritative token direction (`PDR-0044` + `PDR-0012`) and are
  forbidden while it stands. The narrow aggregate interim is the pre-decided fallback ONLY
  against a named consumer, scoped to that consumer's reads. Evidence: both packs with
  pair-scope variables set `observable: false`; no shipped pack declares social-residue
  rules; the substrate freeze blocks any landing anyway.
- **Tracker re-pointed to match:** `hamlet-424adcb84f` (dynamic variables) now blocks on
  `hamlet-fa6bb6da4a` (the token path) instead of the closed decision ticket;
  `hamlet-fa6bb6da4a` carries a comment recording its FOURTH consumer and the post-corpus
  sequencing pressure this puts on it and on `hamlet-0d0115383e`.
- **Wrote the Phase A work plan for the token-observation pivot**
  (`docs/superpowers/plans/2026-08-22-token-observation-pivot-phase-a.md`, commits
  `60028c41` + `dbefce9c`): five TDD tasks — level-overridable `brain.yaml` (PDR-0027 half 1),
  lineage legibility via `pack_brain_hash` + load banner (half 2), a committed `set_encoder`
  pack, the config-in/behaviour-out proof PDR-0017 names as the first unit, and the outcome
  adjudication that fires the right PDR-0017 trigger (a design-level failure ESCALATES, per
  trigger 2). Phase B deliberately unplanned — it depends on the proof's outcome. **Execution
  is gated on the `PDR-0090` freeze lifting**; the gate is written into the plan itself.
- Owner mid-session correction applied: the plan's first draft accommodated pre-stamp
  checkpoints silently — the exact backcompat shape CLAUDE.md forbids. Amended to raise.

## Reversal triggers — state as of this session

- `PDR-0107` (new): **armed.** Reopens if (a) a concrete consumer needs relational/message
  observability before the `set_encoder` proof passes → build the narrow interim scoped to
  that consumer; (b) `set_encoder` proves broken AND the owner redirects away from tokens →
  fixed-width becomes the path; (c) the token migration lands → closes naturally.
- `PDR-0095`: **FIRED** (2026-08-20). No north-star reading publishes. Still the governing
  constraint.
- `PDR-0106`: pending the `tensorNd` evidence audit — unsound collapses the disagreement to
  executor error; sound stands the rejection and reopens run 1's four tickets.
- `PDR-0105`: reopens if a Shape 1 site needs its consumer built too, or the grep signature
  returns fewer than six sites.
- `PDR-0101` trigger 2: **CLEARED** (2026-08-20 nightly). `PDR-0102` trigger 2: unchanged.
- `PDR-0079` trigger 3: **DISCHARGED**; read the by-catch on the 24 (`prd-0001-trial` label).
- `PDR-0090` (substrate freeze): **armed — and now also gates the Phase A pivot plan.** Lift
  condition (trial nine + both re-runs) remains entangled with the instrument decision.
- Pack-disposition clock: **NINE packs** promoted-or-deleted by **2026-10-06**.

## Blocked on / flagged for the owner (all carried from the thirty-eighth checkpoint — nothing new this session)

1. **What happens to the instrument** (`PDR-0106`) — the live escalation. Recommendation
   unchanged: commission the `tensorNd` evidence audit first (`PDR-0098` pattern); do not
   rebuild the protocol before the diagnosis.
2. **`hamlet-a141ab5db3`** — place it by decision (WS-7 or WS-4), not by sweep.
3. **WS-7 (`hamlet-e3af412673`, P0)** — park it or schedule it; untouched since ~2026-08-17.
4. **`hamlet-83c8e3b50e` (P1)** — CI silent on main's third merge; the deciding test is the
   next merge. Change no workflow config before that reading exists.
5. Dependabot `#33`/`#34` open on `main`, plus **4 vulnerability alerts**.
6. `CLAUDE.md:65` stale citation (owner's file, deferred by choice).

## Open questions

- **Does run 2's `tensorNd` finding invalidate run 1's four tickets?** (`hamlet-1b9af9088c` +
  three siblings) — gated on the audit.
- **Protocol defect G-P1** (template-copy vs blinding) — needs the B.1 treatment.
- **A.6.1 is load-bearing beyond its scope** — bucket follows facet enumeration, which a
  blind re-run varies.
- Persistent-lifetime globals + effects surviving reset: intent or defect (third
  reproduction); persistence should arguably be *declarable*.
- **The blind pack is NOT yet in tree** (`configs/trial_b_blind_organism`, worktree only).
  Land it with its §10 guardrails (validate + full suite, ~28 min) or delete it deliberately;
  on the 2026-10-06 clock either way.
- Retro-derivation of discovery paths for L/F/M/O — still owed under `PDR-0097`'s caveat.
- Next corpus revision: candidates Q/R, plus the statistician's substrate-naive stratum.
- (New, minor) `SetEncoderConfig.token_field_name` validates only at network-build time, not
  compile time — the PDR-0052 shape; the Phase A plan says file it at execution.

## Next session starts here

**Unchanged: the instrument decision is the only thing that moves anything** — first move is
the **`tensorNd` evidence audit** (commissioned, fresh agent, `PDR-0098` pattern), question:
*does a global-profile `tensorNd` VFS variable express an entity as a set of occupied cells
at pin `1ef1d950`?*

Then, in rough order of value:

- The four tickets that answer turns on (`hamlet-1b9af9088c` + siblings).
- **WS-4 Shape 1 as one unit** — six sites, one greppable signature (`PDR-0105`).
- Trial seven (D, E or J) — record, not reading, while the instrument is unaccepted.
- **When the `PDR-0090` freeze lifts:** execute the Phase A pivot plan
  (`docs/superpowers/plans/2026-08-22-token-observation-pivot-phase-a.md`) — claim
  `hamlet-0d0115383e` then `hamlet-fa6bb6da4a`.
- Cheap cleanup: nine-pack disposition queue, L/F/M/O discovery-path retro-derivation.

Work continues on `project-recovery-2`.
