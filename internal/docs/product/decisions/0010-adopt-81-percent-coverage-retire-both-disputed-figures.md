# PDR-0010 — Adopt 81% as the coverage reading; retire both disputed figures; record gates at 1 of 4

Date: 2026-08-11   Status: accepted   Author: Claude (standing product owner)   Owner sign-off: n/a (within grant — instrumenting and reading metrics)
Related: PDR-0008, metrics.md (Test coverage, Gates green, Documentation truth), tracker `hamlet-6730ba7915` (README), `hamlet-ad2773718a` (WS-5)

## Context

Two guardrail rows had been unreadable since **2026-05-16**, and `current-state.md` carried the
coverage question as an open blocker on the README rewrite:

- **Test coverage — DISPUTED, 19% vs 70%.** The README badge claims 70%; the 2026-05-16 quality
  assessment measured 19% from a single `.coverage` artefact of unverified run-scope and rated its
  own headline number *"High-risk unreliable"* in §0.2. `metrics.md` instructed: treat **both** as
  unusable, cite neither.
- **Gates green — "passed at milestone baseline, not re-run."** Three months old.

Both are cheap to resolve and neither had been. One clean full-suite run settles them.

## Options considered

1. **Leave both unread until WS-5** — pro: no effort now. Con: the README rewrite
   (`hamlet-6730ba7915`) is owner-endorsed and *blocked* on the coverage question, and the README
   currently publishes an unverified quality claim on a public repo.
2. **Replace 70% with the 19% figure** — pro: it is the more recent measurement. Con: its own
   report calls it unreliable; substituting one untrusted number for another is not a reading.
3. **Run the full suite under coverage and adopt what it says** — the option taken.

## The call

**Option 3.** One full-suite run under coverage was executed (2942 tests, 7m53s).

- **Test coverage: 81%** (`--cov=townlet`, whole suite). Both disputed figures are retired.
- **Gates green: 1 of 4**, not 4 of 4:

  | gate | result |
  |---|---|
  | `ruff check src/townlet` | pass |
  | `black --check src/townlet` | fail — `environment/dac_engine.py` (+3 under `tests/`) |
  | `mypy src/townlet` | fail — 3 errors in 2 files |
  | `pytest` | fail — 1 of 2942 |

### The 19% is explained, not merely superseded

Re-running a **single** test overwrote `.coverage` and reported `TOTAL 16%`. That is the same
shape and nearly the same magnitude as the disputed 19%, produced by exactly the mechanism the
2026-05-16 report suspected of its own number: a `.coverage` artefact from a partial run. The
figure was never a measurement of the suite. Recording this because the *explanation* is what
stops it being re-litigated; a superseded number returns, a diagnosed one does not.

### The one test failure is a stale fixture, and it is evidence *for* a metric

`test_item_vfs_observation_build` builds a VFS registry that never populates `item_profile_map`,
then points an inventory at row 0. Production now refuses that with
`RuntimeError: Item VFS observation cannot resolve exposed variables for VFS row index 0`, under a
comment reading *"Missing profiles or variables are configuration errors, not 'no exposed values'
cases."* That is a deliberate **loudness** tightening the benchmark fixture predates. It is a red
gate caused by the product getting better, and it counts toward **Failure loudness**, not against it.

## Rationale

Option 3 beat option 1 on cost: the run is one command and it unblocked an endorsed, owner-approved
work item that had been waiting on it. It beat option 2 because a guardrail whose value is
"a number somebody measured once" is not a guardrail — the point of the row is to be falsifiable,
and neither disputed figure could be.

The `Gates green` result is the more important of the two. It had been recorded as green for three
months while three of four were red. Nothing about the failures is deep — one autoformat, three
type errors, one stale fixture — which is precisely why they went unnoticed: no one was looking,
because the workspace said they were green. A guardrail that is not re-read is not a guardrail.

## Consequences

- **The README's 70% badge is confirmed false** and joins the `Documentation truth` count. It errs
  *low* — the real figure is better — which does not make it less wrong on a public repo.
- **The README rewrite is unblocked** on this question: it may now cite 81%, or cite nothing.
- **Gates are not fixed by this decision.** They are recorded as measured. Fixing them is
  engineering work and is deliberately not bundled into a checkpoint.

## Reversal trigger

Reopen this PDR if **any** of the following:

- **A second full-suite run under coverage disagrees materially with 81%** (more than ±5 points).
  A single run is one reading; the whole point of this PDR is that unreplicated coverage numbers
  are how the project got into a two-number dispute in the first place.
- **The 81% figure is cited publicly before it is replicated.** Publishing an unverified quality
  claim is the exact failure this row exists to catch, and it would be the second time.
- `Gates green` is still below 4 of 4 at the oracle freeze (`PDR-0006`). Freezing an oracle whose
  own type-checking and formatting gates fail makes those failures the rebuilt system's baseline.
