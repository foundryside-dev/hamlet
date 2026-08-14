# PDR-0040 — The register-suppression seam is closed; PDR-0037's narrowing trigger fired during its own review and was answered by prescription

Date: 2026-08-15   Status: **accepted** (within grant — ACCEPT of dispatched work against
`PDR-0037`'s stated criteria; no new bet, no scope change)
Author: Claude (standing product owner)
Related: `PDR-0037` (the decision this executes and accepts), `PDR-0033` (the mandatory
adversarial pass — applied, and this time applied *to itself*), `PDR-0036` (DIV-003's shape),
`PDR-0035` (the knockdown this unblocks), `PDR-0032` (trace-only v1 — unchanged by this)
Tracker: `hamlet-56ec575ae2` (closed, `9a75b581`) · `hamlet-e3af412673` (WS-7, content 5 step 1)

## What was accepted

`9a75b581`. The harness can now PASS a divergence the register predicted, and nothing else new:

- A matrix cell declares its binding: `RegisteredDivergence(register_ref, old_stderr_substring)`.
- The match is **conjunctive**: old side crashed (nonzero exit — `SideFailure` now discriminates
  a real crash from the exit-0-no-trace driver-bug mode) **and** wrote no trace **and** the
  signature appears inside the **final exception text** of its stderr (last traceback block,
  frame lines excluded) **and** the new side ran, its lone trace validating against the cell's
  own params, shapes, and `code_root`. Each failed conjunct lands red with its own reason.
- `exit_code` passes AGREE/SKIPPED with empty refs and `DIVERGED_AS_REGISTERED` with non-empty
  refs, and nothing else — both inversions fail, unknown kinds fail, empty and all-SKIPPED runs
  fail.

Acceptance criteria came from `PDR-0037` and the issue: matched divergence passes; unmatched
divergence — including an unmatched `OLD_SIDE_ERROR` — still fails; the match is narrow; the
adversarial pass ran **before** the verdicts are trusted. All met. Evidence on the issue: 93
oracle unit tests (19 new, written red-first), a 10-mutant battery all killed, full CPU matrix
vs `oracle-2026-08-13` AGREE×5 exit 0 both mid-state and final, full suite 3085/0, gates clean.

## The part that is a decision, not a status: the trigger fired

`PDR-0037` reversal trigger 1 armed on *"the adversarial pass finds a way for a registered
entry to mask an unrelated real divergence."* **It fired.** The pass (5 lenses, 2 refuters per
finding, 57 agents) found four such ways in the first implementation: `"RuntimeError:"` defeats
a bare-identifier check by one character and matches every crash of that class; a signature
anywhere in the stream certifies co-occurrence, not cause; the exit-0-no-trace synthesized
diagnostic (which embeds *stdout* and harness-authored text) satisfied "crashed with SIG"
(reproduced, not hypothesized); and a crash *after* a complete trace was written was suppressed
although the registered shape is "fails to produce a trace."

The trigger's own prescription was followed rather than the decision reopened: **narrow the
match** — which is what the conjunctive, final-exception-anchored form is. Recorded design
edges, so they are not relitigated:

- **One expectation shape only** (old-crash/new-runs). New shapes arrive when a register entry
  needs them. Unexercised machinery in a verdict-emitting tool is itself a risk.
- **The harness never reads the register at runtime.** Binding integrity is enforced at
  declaration (validation) and test time: every declared ref must exist as a `## DIV-NNN`
  heading **and** that entry must carry `Harness shape: old-side-crash`. Runtime markdown
  parsing was rejected as fragile; the typo-bind is killed by the marker test instead.
- **Entry lifecycle is not parsed and does not need to be**: a not-yet-built divergence lands
  `NEW_SIDE_ERROR` and a stale one lands `REGISTERED_DIVERGENCE_ABSENT` — both red, so lifecycle
  state is behaviorally enforced from both directions.
- **Dtype pins were deliberately omitted** from lone-trace validation: the driver casts at write
  time, so the check could never fire (refuters' argument, verified against `driver.py`).

## The finding about the instrument itself

The `PDR-0033` pass **failed twice while running, and both failures would have corrupted the
verdict if unexamined**:

1. The first run's verify phase died on a session limit; the fail-closed partition labeled every
   unverified finding "confirmed." Right default, wrong label — **a fail-closed KEEP is not a
   confirmation**, and treating it as one would have meant acting on 21 "confirmed" findings of
   which 15 had never been examined. Resolved by resuming from cache; the hunt was never re-paid.
2. The mutation adversary's method was silently broken: pytest's `pythonpath = ["src"]` ini
   setting outranks the `PYTHONPATH` environment variable, so its "surviving mutants" were
   measured against unmutated code. Caught only because the re-run battery **probed first**
   (inject a top-level raise, demand the suite scream). The five reported survivors happened to
   be logically real coverage holes — the *conclusions* survived, the *evidence* did not.

The general form joins the carry-in family: `PDR-0010` (a recorded green is not a green),
`PDR-0033` (ask what a green tool cannot see), `PDR-0037` (ask what its red cannot distinguish),
and now: **a verifier is not self-verifying — probe the instrument before believing its
results.** Concretely: any future mutation testing in this repo must inject a loud probe first,
and any multi-agent verdict partition must be checked for verifier failures before its labels
are read as verdicts.

## Reversal trigger

- **Reopen the matcher** if a DIV-003-armed run ever passes `DIVERGED_AS_REGISTERED` where the
  old side's recorded `old_final_exception` does not match the register entry's documented
  crash — that is the false AGREE surviving four conjuncts, and it needs a stronger correctness
  argument than review (this restates `PDR-0037` trigger 2 for the built mechanism).
- **Adjust the anchor, never abandon it**: if DIV-003's real crashes turn out to be
  un-anchorable (no Python traceback on stderr; signature cannot live in the final exception
  text), the fix is a new anchor shape with its own adversarial pass — not a fallback to
  whole-stream matching, which is the exact hole this closed.
- `PDR-0037` trigger 3 carries forward unchanged: fold the suppression path back out if two
  consecutive knockdowns register no trace-visible divergence.
