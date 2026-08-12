# PDR-0022 — `config_hash_warning` warns where the guardrail forbids warning; the plan contradicts itself and the call is the owner's

Date: 2026-08-12   Status: **accepted** — owner adopted the recommendation 2026-08-13 (*"I'll take your recommendation"*). See Resolution below.
Author: Claude (standing product owner)
Related: PDR-0008 (provenance breaches), PDR-0012 (no tech debt), PDR-0021 (adjacent gaps filed), PDR-0006 (oracle freeze)
Plan: `docs/plans/2026-08-11-ws1-fix-set.md` §0 warning W4 vs Task 4 change 5 · §0.3 correction 21
Tracker: `hamlet-1029f99f4b` (task 5, where this lands either way)

## Context

`checkpoint_utils.config_hash_warning` compares a checkpoint's `config_hash` against the current
universe's and returns a **warning string** on mismatch. One production caller
(`demo/runner.py:354`), two test assertions.

**The WS-1 plan contradicts itself about it, and the contradiction is load-bearing.**

- **§0 warning W4** says resolve it *in this batch*, on the grounds that retaining it "for
  DemoRunner parity" is the *keeping-obsolete-code-just-in-case* antipattern (`PDR-0012`).
- **Task 4 change 5** says *"do not touch `config_hash_warning`."*

§0 outranks task text where they conflict, so W4 governs — but **"resolve" is not necessarily
"delete"**, and the plan never says which. Task 4 therefore left it untouched and surfaced it
rather than picking silently.

## Why it is a genuine product question, not a code detail

The **Provenance-integrity** guardrail's target is *"no silent acceptance."* A warning **is**
silent acceptance in every non-interactive context — training runs, CI, the live-inference
server. Nothing blocks; a line goes to a log nobody reads.

But `config_hash` is also the **broadest signal the system has.** It covers
experiment / stratum / environment / actions / items — five surfaces that, per
`hamlet-2dde1015fe`, have **no hard check of their own**. So the weakest guard is currently the
only guard over the widest area. Deleting it narrows coverage; keeping it as a warning leaves
the widest area protected by something that does not stop anything.

## Options

1. **Delete it and its caller.** Cleanest under `PDR-0012`; task 5's check count drops from five
   to four. **Cost:** the five pack-level surfaces lose their only signal until
   `hamlet-2dde1015fe` lands.
2. **Make it raise.** Aligns the broadest signal with the guardrail's own target. **Cost:** any
   pack edit that moves `config_hash` — including comment and whitespace edits, which it is
   sensitive to — becomes a hard resume failure. That is a real authoring-ergonomics change and
   may be experienced as the system fighting the author.
3. **Keep it as a warning, and say so deliberately** — i.e. `PDR-0012` has one recorded
   exception, argued rather than inherited. Honest, but it is the retention-on-parity-grounds
   argument W4 already rejected.
4. **Delete it *and* pull `hamlet-2dde1015fe` forward** so the five surfaces get hard checks in
   the same batch. Closes the gap properly — and directly contradicts `PDR-0021`, which just
   decided those gaps are filed, not folded.

## Recommendation

**Option 1, conditional on `hamlet-2dde1015fe` being entered in the known-divergences register.**
It is the only option consistent with both `PDR-0012` and `PDR-0021`, and it does not pretend a
warning is a guard. Option 2 is defensible and I would not argue against it — but it changes
authoring ergonomics on the eve of a freeze, which is the wrong moment to discover it is
annoying.

**This is recorded as `proposed` and not acted on.** The plan's own two halves disagree; picking
one silently is how a contradiction becomes an unexamined precedent.

## Consequences of leaving it open

- **Task 5 cannot state its final check count** — five or four, depending.
- **The `config_hash_warning` code path is untouched meanwhile**, so nothing breaks; this
  blocks a decision, not the work.
- If it is still unresolved when task 5 lands, task 5 should implement **around** it and this
  PDR stays open rather than being resolved by default. A decision made by drift is the failure
  mode this workspace exists to prevent.

## Resolution (2026-08-13)

The owner adopted the recommendation: **Option 1 — delete `config_hash_warning` and its caller,
conditional on `hamlet-2dde1015fe` being entered in WS-7's known-divergences register.**

Consequences now binding:

- **Task 5's final check count is FOUR** (`assert_checkpoint_vfs_hash`,
  `assert_checkpoint_dimensions` incl. the four per-level content hashes, `brain_hash`,
  `drive_hash` — no warning leg). The §0 W4 / task-4 contradiction is resolved in W4's favour,
  with "resolve" = delete.
- **The condition is a real precondition, not decoration**: if the freeze approaches and
  `hamlet-2dde1015fe` is not in the divergences register, the deletion has not met its terms —
  register it first or the five pack-level surfaces lose their only signal silently.
- The **(if deleted)** reversal trigger below is now the live one.

## Reversal trigger

Once decided, reopen if:

- **(if deleted) a config divergence reaches a run that `config_hash` would have caught** and no
  other hash moved. That is direct evidence the coverage loss was real, and
  `hamlet-2dde1015fe` becomes urgent rather than sequenced.
- **(if made to raise) authors hit it on edits that change no behaviour** — comments, key
  reordering, whitespace. Then the signal is too broad to be hard, and the correct fix is to
  narrow what `config_hash` covers, not to soften the check back to a warning.
