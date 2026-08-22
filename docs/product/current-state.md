# Current State — HAMLET / Townlet        Checkpoint: 2026-08-22 · fortieth checkpoint (`PDR-0110`: **the `tensorNd` audit is adjudicated — Branch A, SOUND — the rejection stands as search variance, and the instrument fork is the owner's.** This checkpoint also reconciles TWO sessions that ran without checkpointing: the 2026-08-21 audit+VFS session and the 2026-08-22 token-pivot session — the thirty-ninth checkpoint was written blind to the first of them and part of the second)

## The bets right now — there are three

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). In flight. Exits
when the **pinned oracle can be RETIRED** (`PDR-0058`): (1) register entries terminal — open
(DIV-001/002 `tag-stamped`; 003/004/005 `retired`; 006 `built`; **DIV-007 new** — items_smoke
stale brain.yaml stub, registered at `9956e95b`); (2) harness verdict vocabulary — **MET**
(`PDR-0074`); (3) `Gates green` — **MET on `main`** (2026-08-20 nightly at `04062872`).
`hamlet-a141ab5db3` no longer dents condition 3's reading — **FIXED 2026-08-21** (`03764c6b`:
agent profiles serialize to cache, failed cache write fails compile).

**2. Measure the authoring claim** (`PDR-0077`, `PDR-0086`) · tracker `hamlet-5fa1f7bfc0`.
**⛔ NOTHING PUBLISHES** (`PDR-0106`) — and the recommended first step is now DONE:
**the `tensorNd` audit is adjudicated Branch A, SOUND (`PDR-0110`)**. Run 2's B-F2 PASS
stands; the rejection stands as **genuine search variance**; criterion 3 remains unmet.
Record retained: 6 of 9 settled (L, F, M, O PASS; B, K FAIL), split 0/0/2, 3 pending
(D, E, J — runnable as record, not reading). **The instrument fork is the owner's** — see
"Blocked on" below.

**3. Token-observation encoding** (`PDR-0108`, owner-directed Later→Now 2026-08-22).
**Phase A is FULLY EXECUTED and its proof adjudicated (`PDR-0109`): `PDR-0017` trigger 1
FIRED — the token path is real.** `brain.yaml` is level-overridable with lineage stated at
load (`hamlet-0d0115383e` CLOSED); the first `set_encoder` pack exists
(`configs/test/set_encoder_smoke`); the config-in/behaviour-out proof is green (tokens move
Q-values, permutation invariance, gradients flow). Remaining scope on `hamlet-fa6bb6da4a` is
the migration proper; **the next unit — the aggregator upgrade (mean-pool → self-attention) —
is schedulable directly.** Phase B order per `PDR-0109`: aggregator → full token
representation → relational/message exposure as tokens (discharges `PDR-0107`) → dynamic
variables (`hamlet-424adcb84f`).

## What the fortieth checkpoint reconciled (three sessions)

- **2026-08-21 (un-checkpointed):** owner commissioned the `tensorNd` audit at that day's
  resume; pre-commitment `e234635f` landed BEFORE the audit `6e3b53a5` (integrity holds);
  verdict Branch A. The session then *enacted* the adjudication without recording it: eight
  gaps filed (A-G1 `hamlet-cf16cdb6c4` … A-G8 `hamlet-8b5af63108`, plus `hamlet-f54b887148`),
  four Trial-B tickets framing-narrowed, blind pack landed in tree (`f2bb6de7`, §10
  guardrails discharged). Same day, under the VFS refresh: **A-G1 FIXED** (`0f0f2b57` — the
  global expression-write class opens), **A-G2 FIXED** (`15a9702f`), **zone/group/message
  scopes FIXED** (`6b752b3c`, `hamlet-9e1ae3b7a2`), `hamlet-a141ab5db3` FIXED, and an
  independent VFS gap analysis landed (129 cells: 63 WORKS / 9 INERT / 26 BLOCKED / 31
  ABSENT, `vfs-gap-analysis-20260821.md`).
- **2026-08-22 token session (un-checkpointed):** `PDR-0108` + `PDR-0109` as summarized in
  bet 3. The `PDR-0090` freeze is **superseded for this stream** by the owner's direction;
  trial readings stay protected by pinned-commit execution.
- **This session:** grant re-confirmed unchanged at resume; audit integrity verified by git
  order; **standing-agent independent verification at pin `1ef1d950`** (fresh worktree,
  probes written independently): asymmetric per-cell read-back exact on raw+accessor, obs
  indices `[15,16,157]` exact, R1 cell-indexed write refused at compile, C3b slab write
  3→82 — arithmetically exact against the audit's 1→81. `PDR-0110` written (adjudication +
  provenance repair); ticket comment 214 on `hamlet-5fa1f7bfc0`.

## Reversal triggers — state

- `PDR-0106`: **RESOLVED by the audit** — Branch A means the rejection stands; re-adjudication
  branch (unsound) is dead.
- `PDR-0095`: **still FIRED.** No north-star reading publishes until the owner rules on the
  instrument.
- `PDR-0110` (new): **armed.** Reopens if the owner re-reads B-F2 as requiring per-cell
  authorability (Branch C reading — scoring flips to PARTIAL, disagreement narrows not
  collapses); if either verification is shown contaminated; if a probe at the pin contradicts
  the asymmetric read-back or R1 refusal.
- `PDR-0109` (new): **armed.** Reopens if the aggregator upgrade shows the DeepSets proof
  didn't generalize; if training (not just forward/backward) fails on the token path; if a
  compiled block has no natural token form (also `PDR-0044` trigger 3).
- `PDR-0107`: **armed**, being serviced — exits when the token migration lands.
- `PDR-0090`: superseded for the VFS/token stream by `PDR-0108`; pins protect the corpus.
- Pack-disposition clock: **NINE+ packs** (seven trial + two blind + audit scratch is gone)
  promoted-or-deleted by **2026-10-06**.

## Blocked on / flagged for the owner

1. **THE INSTRUMENT FORK (`PDR-0110`) — the live escalation, now sharpened by the audit.**
   Diagnosis confirmed: search variance. Choose: **(a)** amend the protocol with a
   search-variance control (pre-registered surface checklist) and re-run criterion 3;
   **(b)** accept the instrument with a widened caveat — publish headline verdicts only,
   never the split; **(c)** retire the corpus reading as record-only. Everything north-star
   waits on this.
2. **WS-7 (`hamlet-e3af412673`, P0)** — park it or schedule it; untouched since ~2026-08-17.
3. **`hamlet-83c8e3b50e` (P1)** — CI silent on `main`'s third merge; the deciding test is the
   next merge (~30 commits ahead now). Change no workflow config before that reading.
4. Dependabot `#33`/`#34` open on `main`, plus **4 vulnerability alerts**.
5. `CLAUDE.md:65` stale citation (owner's file, deferred by choice).
6. `vision.md` `Last reviewed` stamp reads 2026-08-20; re-confirmed unchanged 2026-08-22 —
   stamp debt carried per the 2026-08-15 rule, corrected at the next approved touch.

## Open questions

- **Protocol defect G-P1** (template-copy vs blinding) — still owed the B.1 treatment if
  branch (a) is chosen.
- **A.6.1 is load-bearing beyond its scope** — bucket follows facet enumeration, which blind
  re-runs vary; feeds the branch-(a) design if chosen.
- Persistent-lifetime globals: now filed as `hamlet-0268336cd1` (no declarable
  "episode-scoped global"); the third reproduction stands.
- Retro-derivation of discovery paths for L/F/M/O — still owed under `PDR-0097`'s caveat.
- Next corpus revision candidates: Q/R + the statistician's substrate-naive stratum.
- `SetEncoderConfig.token_field_name` validates only at network-build time — filed per the
  Phase A plan (PDR-0052 shape).
- The 2026-08-21 VFS gap analysis (129 cells) has not been triaged into the WS-4 queue —
  cheap, high-signal input for Shape-1 sequencing.

## Next session starts here

**The owner's instrument ruling (fork a/b/c in `PDR-0110`) is the only thing that unblocks
the north-star.** Independent of it, in rough order of value:

- **Phase B unit 1: the aggregator upgrade** (mean-pool → self-attention) on
  `hamlet-fa6bb6da4a` — pre-authorized by `PDR-0109`, moves Config-surface coverage.
- **WS-4 Shape 1 as one unit** — six sites, one greppable signature (`PDR-0105`); triage the
  VFS gap analysis into its queue first.
- Trial seven (D, E or J) — record, not reading, under any instrument branch.
- Cheap queue: nine-pack disposition clock (2026-10-06), L/F/M/O discovery-path
  retro-derivation.

Work continues on `project-recovery-2`.
