# Current State — HAMLET / Townlet        Checkpoint: 2026-08-19 · thirty-fifth checkpoint (`PDR-0088`–`PDR-0092`: Trial K — the sixth of nine — is run and **FAILS**, and the **≥80% target is now arithmetically unreachable for this corpus**; the substrate is frozen for the measurement; the blind re-run pair is O + B; two countersign conflicts were escalated and owner-ruled *before* authoring)

## The bets right now — there are two

**1. Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Unchanged, in
flight, untouched this session. Exits when the **pinned oracle can be RETIRED** (`PDR-0058`):
(1) register entries terminal — open (DIV-001/002 `tag-stamped`; 003/004/005 `retired`;
006 `built`); (2) harness verdict vocabulary — **MET** (`PDR-0074`); (3) `Gates green` on a
suite that hides nothing — **MET on `main`**. ⚠️ Trial K put a dent in condition 3's *reading*:
the suite is 3281/16/0 green over a hole — three declared VFS scopes hard-crash any pack using
them, possible only because no test instantiates them (`PDR-0092`).

**2. Measure the authoring claim** (`PDR-0077`, `PDR-0086`) · tracker `hamlet-5fa1f7bfc0`
(`in_progress`) · spec PRD-0001 + protocol incl. Appendix A · metric: north-star **Zero-Python
authoring rate (world)** — expert-ceiling expressibility reading, construct preamble mandatory.
**State: 6 of 9 SETTLED (L, F, M, O PASS; B, K FAIL), 3 pending (D, E, J — all multi-agent).**
Idea split `0 ABSENT / 0 INERT / 1 BLOCKED` **+ K unbucketed (open protocol gap, below)**.
INERT surfaces encountered: **4 in 6 trials**. Then blind re-runs **O + B** (`PDR-0089`) before
any reading publishes.

⚠️ **The ≥80% bar (8 of 9) cannot now be met**: 2 FAILs cap the reading at 7 of 9 = 77.8%. Per
`PDR-0078` this is a **finding about the substrate, not a failed bet** — acceptance sits on the
instrument precisely so a low number can't be gamed by an easy corpus. The remaining three
trials still run; they establish *how far* below and *which axes*, which is the product signal.

## What this session did

- **RESUME → ORIENT**: six drift items found. Branch Lint had been **red since the last
  checkpoint push** (dead probe line, second occurrence of that shape) — fixed, B1 probe re-run
  byte-identical, pushed. Grant re-confirmed and its stamp corrected at an approved touch
  (`PDR-0088`).
- **Measured that `src/townlet/` has not moved once across all six trials** — the readings share
  one engine *de facto*. That reframed the `spawn_item` P1 from a sequencing question into a
  construct question; owner ruled **fix after the corpus** (`PDR-0090`).
- **Trial K run end-to-end under Appendix A** — nine countersigned facets, all settled, not
  budget-limited. **Headline FAIL** (`PDR-0092`, record `docs/product/trials/0001/K-20260819.md`,
  pin `3434b2fa`). Two P1s filed, **nothing fixed**: `hamlet-9e1ae3b7a2` (zone/group/message
  scopes validate and compile, then hard-crash at env construction — registry kwargs defaulting
  to 0 that nothing passes and no YAML sets) and `hamlet-a737e444c0` (effects are blind to
  position and time — the second instance of the `hamlet-1b9af9088c` pattern). Plus
  `hamlet-628e202bf7` (item `on_drop` INERT) and five reproduction comments.
- **Two countersign conflicts escalated, not adjudicated** (`PDR-0091`). The agent had drafted a
  reconciliation that adopted the strict bar while claiming not to resolve it — that *was*
  resolving it, at maximum-knowledge time, with the outcome already predictable. Owner ruled
  before authoring: F7 is a capability bar; F9 left unruled and reported honestly.

## The finding, in one line

> **An author can express two of the three answers, and cannot make the problem happen on its
> own.** The winter rule is declarative and exact; its *ignition* is not. This inverts the
> corpus's own summary ("can express the problem but not the answers to it").

## Reversal triggers — state as of this session

- `PDR-0090` (substrate freeze): armed. Lifts at trial nine + both re-runs; re-litigated if
  2026-10-06 arrives with trials outstanding, or if a defect makes the protocol unrunnable.
- `PDR-0092`: if the two new P1s land and a re-run turns F7/F1, **the FAIL stands for this
  reading** — the flip is Trend content, not a re-scoring. Boundary cases 6/7/8/9 are
  **deferred, not waived**.
- `PDR-0089`: any verdict or classification disagreement in the O or B re-run fires criterion
  3's reject branch — the instrument is not accepted and **no reading publishes**.
- `PDR-0091`: countersign-reconciliation notes now **2 of 3**; at 3 the practice graduates to a
  PRD criterion.
- `PDR-0086`: construct preamble intact — no reading published without it.
- `PDR-0068` (merge banking): **27 commits** ahead of `origin/main` vs ~30 threshold — close,
  not lit. The next merge owes `PDR-0039` gate 2.
- Pack-disposition clock: **SEVEN packs** promoted-or-deleted by **2026-10-06**.
- `PDR-0079` trigger 3: the ABSENT/unactioned by-catch list keeps growing (13+ across six
  trials). A WS-4 triage session is overdue.

## Blocked on / flagged for the owner

1. **K's idea-level bucket — BLOCKS the published split.** Appendix A.6 rules only the INERT
   tiebreak and is silent on an idea whose failing facets are **ABSENT and BLOCKED with no
   INERT** — exactly K. `metrics.md` carries the gap explicitly rather than resolving it. Not
   self-adjudicated.
2. **WS-7 (`hamlet-e3af412673`, P0) — park it or schedule it.** Flagged stale; the flag is right
   about the *lease*, not the status. Genuinely mid-flight but untouched since ~2026-08-17
   because every session has run bet 2. Deliberately neither re-claimed (would recreate the
   staleness) nor reset to open (it is not un-started) — comment 176 records why.
3. **This checkpoint commit is NOT pushed.** `/product-checkpoint` forbids pushing; `PDR-0046`
   grants it freely for this branch and every prior checkpoint pushed. Flagged rather than
   resolved unilaterally — say the word, or push it yourself.
4. **O's blind-re-run comparer is owed a pre-brief** that the first run's facet 4 never
   exercised the tie case (A.8).
5. Dependabot `#33`/`#34` on `main` still open; merges to `main` are yours.
6. `CLAUDE.md:65` stale citation (fourteenth sighting; owner's file, deferred by choice).

## Open questions

- Whether the two new P1s change WS-4's shape: `hamlet-a737e444c0` (effects blind to position
  and time) plus `hamlet-1b9af9088c` (spawn_item) are now **two confirmed instances of one
  pattern** — the grammar declares capability the execution path never threads data for. That
  may be a single unit rather than three tickets.
- Whether persistent-lifetime globals + effects surviving reset is intent or defect — **third**
  reproduction now (comment 172), and the first to isolate that global VFS variables do not
  reset while meters do. Per the methodology review, persistence should arguably be *declarable*.
- Retro-derivation of discovery paths for L/F/M/O (cheap, still owed; B and K set the format).
- A protocol lint step for trial packs — two branch-Lint reds in four sessions, both probe
  E501s. Proposed, not decided.
- Next corpus revision (after the nine + re-runs): candidates Q/R waiting, plus the
  statistician's substrate-naive stratum proposal.
- Unchanged: `exposed_to` hidden default (unfiled); `recurrent_vision_window_side` non-square
  raise (unfiled); `hamlet-1ad6383186`, `hamlet-7cd887c9e5`, `hamlet-266a0a41f0`,
  `tests/README.md` staleness → WS-5, `cues` inert.

## Next session starts here

**Answer question 1 above** (K's bucket) — it is the only thing blocking `metrics.md`'s split
from being complete. Then pick one:

- **Trial seven** under Appendix A — D, E or J, all multi-agent, where the corpus's pessimistic
  priors get their real test. Note J's durable-posting facet is now discounted three times over
  (O's, B's and K's findings all bear on it).
- **A blind re-run** (O or B) — the pair is chosen, so this is now unblocked and is the only
  work that moves *publication* rather than the numerator.
- **WS-4 triage of the trial by-catch** — 13+ items, `PDR-0079` trigger 3 overdue, and the
  two-instances-of-one-pattern question above would shape it.
- Cheap cleanup: L/F/M/O discovery-path retro-derivation, the protocol lint amendment, the
  seven-pack disposition queue.

Work continues on `project-recovery-2`.
