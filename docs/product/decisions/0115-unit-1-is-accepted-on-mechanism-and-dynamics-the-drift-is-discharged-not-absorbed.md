# PDR-0115 — Migration unit 1 is ACCEPTED on mechanism + dynamics evidence; the red matrix is adjudicated as pre-existing drift and discharged, not absorbed

Date: 2026-08-23   Status: **accepted** (within grant: accept-against-criteria; the
acceptance criterion's literal miss is adjudicated below with its own reversal trigger)
Author: Claude (standing product owner)
Related: `PDR-0114` (the spec §6 unit 1 implements), `PDR-0074` (verdict vocabulary),
`PDR-0037` (record-then-bind), `PDR-0033` (narrowness), `PDR-0012`/`PDR-0013`
(no-tech-debt: the discharge-vehicle requirement this executes)
Tracker: `hamlet-fa6bb6da4a` (comments 233–235) · Commits: `9e7197e6..1960dee6` ·
Discharge: `hamlet-5cc071f4b6` (P1) · Defer vehicles: `hamlet-f7631a4672` (cosmetics),
comment 234 (unit-3 batch)

## Context

Unit 1 rebuilt the differential harness so DIV-008's adjudication is expressible before
the token cut: trace format v4 (actions as a recorded, adjudicated stream +
`action_source`), driver `--actions` scripted replay (loudly validated), the third
declared divergence shape (`RegisteredStreamDivergence`), non-short-circuiting per-stream
`compare_traces` with a preflight exemption for declared streams, and the harness
`--scripted` flow. Six TDD tasks, subagent-driven, task reviews + final whole-branch
review clean (zero Critical/Important).

The plan's literal acceptance — "full CPU matrix exit 0, all-AGREE" — was NOT met: both
runs exited 1 with all ten CPU cells `HASH_MISMATCH`.

## The call

**Unit 1 is accepted.** The failure was adjudicated (implementer diagnosis + a dedicated
independent review, each reproducing the evidence): six commits landed on
`project-recovery-2` after the oracle tag moving provenance hashes with no register
entries — the first harness run since. Every stream (`obs`/`actions`/`rewards`/`dones`)
is byte-identical old-vs-new in BOTH plain and scripted modes, so the scripted flow
demonstrably works end-to-end and dynamics are clean; the hash gate fired exactly as
designed on real, unregistered drift. The hash-gate code itself is byte-identical to the
oracle tag, and none of the suspect commits touch `src/townlet/oracle/` — the unit did
not cause what it detected.

Per no-tech-debt, the miss is discharged, not waived: **`hamlet-5cc071f4b6`** (P1) —
bisect, adjudicate, register-or-fix until the matrix exits 0 — filed as a **hard gate
before unit 3 registers DIV-008**. (Executed and closed the next day inside unit 2 —
`PDR-0116`.)

## Reversal trigger

If the drift is later shown to be caused by unit 1's own changes (contradicting the
byte-identical-gate-code evidence), unit 1's acceptance reopens and the unit is re-run
against a corrected baseline. Discharged unfired: `PDR-0116` records the drift measured
per-commit to three specific pre-unit movers.
