# Current State — HAMLET / Townlet        Checkpoint: 2026-08-22 · forty-first checkpoint (`PDR-0111`: **the instrument fork is RULED (c) — the corpus reading is RETIRED AS RECORD**, owner-ruled at the resume; `PDR-0112`: **Phase B unit 1 landed — the set-encoder aggregator is a declared choice**, `ba2766e6`)

## The bets right now — two live, one substantially complete

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). In flight. Exits
when the **pinned oracle can be RETIRED** (`PDR-0058`): (1) register entries terminal — open
(DIV-001/002 `tag-stamped`; 003/004/005 `retired`; 006 `built`; DIV-007 registered at
`9956e95b`); (2) harness verdict vocabulary — **MET** (`PDR-0074`); (3) `Gates green` — **MET
on `main`** (2026-08-20 nightly at `04062872`). Untouched this session.

**2. Measure the authoring claim** (`PDR-0077`) · tracker `hamlet-5fa1f7bfc0` (comment 216).
**SUBSTANTIALLY COMPLETE — the fork is ruled (c), `PDR-0111`:** the corpus reading is
**retired as record**, terminal for this corpus. No rate/denominator/split ever publishes;
the six trial records, both blind re-runs, the audit, and 30+ by-catch tickets are the banked
product signal; `PDR-0095`'s fired trigger discharged by retirement. Remaining scope is
record-keeping only: optional D/E/J as record, L/F/M/O discovery-path retro-derivation,
the **2026-10-06 pack-disposition clock** (nine packs). **Instrument redesign
(search-variance control + revised corpus, candidates Q/R) is a separate future bet awaiting
the owner's promotion.**

**3. Token-observation encoding** (`PDR-0108`) · tracker `hamlet-fa6bb6da4a` (comment 215).
**Phase B unit 1 LANDED (`PDR-0112`, `ba2766e6`): the set-encoder aggregator is a DECLARED,
required config choice** — `{type: mean}` | `{type: attention, num_heads: N}` — with
attention authored in `set_encoder_smoke` via an `L1_attention` level-override `brain.yaml`
(first real use of the `PDR-0027` fork mechanism; `brain_forked` asserted). Permutation
invariance pinned on both paths; 607 affected unit + 7 integration tests green; `PDR-0109`'s
reversal trigger did **not** fire (attention needed no new plumbing). **Next unit: token
representation of the full observation — the migration proper, and the big design document**
(then relational/message exposure as tokens discharging `PDR-0107`, then dynamic variables
`hamlet-424adcb84f`).

## What this checkpoint did

- **Recorded the owner's instrument ruling** as `PDR-0111` (fork (c), retire as record) and
  propagated it: north-star row marked RETIRED AS RECORD in `metrics.md`, roadmap bullet
  updated, ticket comment 216.
- **Recorded and accepted Phase B unit 1** as `PDR-0112` (declared aggregator; the
  declared-vs-replace fork was put to the owner, who chose declared). Committed and pushed
  at `ba2766e6` before this checkpoint.
- Grant re-confirmed unchanged at the resume; the owner chose carrying the `vision.md` stamp
  debt (reads 2026-08-20) over an approved touch — the `PDR-0093` shape, again. No horizon
  change.

## Reversal triggers — state

- `PDR-0111` (new): **armed.** Breached if any artifact quotes a rate/split from the retired
  corpus as a published reading; reopens only by owner commissioning a successor instrument.
- `PDR-0112` (new): **armed.** Reopens if training fails on the attention path; if the
  full-token design can't use the aggregator block's shape; if a declared `attention` proves
  behaviourally inert.
- `PDR-0109`: first trigger checked this session — did **not** fire. Training-loop trigger
  still armed.
- `PDR-0107`: armed, being serviced — exits when the token migration lands.
- `PDR-0095`: **discharged by retirement** (`PDR-0111`).
- Pack-disposition clock: nine packs promoted-or-deleted by **2026-10-06**.

## Blocked on / flagged for the owner

1. **Instrument redesign as a future bet** — promote or park: a successor north-star
   instrument (search-variance control, revised corpus with Q/R + substrate-naive stratum).
   Until promoted, the north-star reads `UNREAD` and that is the honest state.
2. **WS-7 (`hamlet-e3af412673`, P0)** — park it or schedule it; untouched since ~2026-08-17.
3. **`hamlet-83c8e3b50e` (P1)** — CI silent on `main`'s third merge; deciding test is the
   next merge (29 commits ahead now). Change no workflow config before that reading.
4. Dependabot `#33`/`#34` + **4 vulnerability alerts** on `main`.
5. `vision.md` stamp debt (reads 2026-08-20; re-confirmed unchanged 2026-08-22 twice) —
   corrected at the next approved touch, per the standing rule.

## Open questions

- The 2026-08-21 VFS gap analysis (129 cells) still untriaged into the WS-4 queue — cheap,
  high-signal input for Shape-1 sequencing.
- `SetEncoderConfig.token_field_name` still resolves only at network-build time (PDR-0052
  shape; filed).
- Persistent-lifetime globals (`hamlet-0268336cd1`); L/F/M/O discovery-path retro-derivation
  (record-keeping under `PDR-0111`).

## Next session starts here

**The token migration's unit 2 — the full-observation token representation design** — is the
main line (`hamlet-fa6bb6da4a`, pre-scoped by `PDR-0109`/`PDR-0112`). It is the big design
document: how meters/spatial/affordance blocks become tokens, superseding the superset+mask
fixed-width ABI. `PDR-0044` trigger 3 (a compiled block with no natural token form) is the
live escalation risk inside it. Independent alternatives: WS-4 Shape 1 (six sites,
`PDR-0105`) after triaging the VFS gap analysis; the cheap record-keeping queue.

Work continues on `project-recovery-2`.
