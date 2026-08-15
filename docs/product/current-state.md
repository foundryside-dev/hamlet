# Current State — HAMLET / Townlet        Checkpoint: 2026-08-16 (latest) · twentieth checkpoint

## The bet right now

**Strangler rewrite behind the compiled-universe contract** (`PDR-0006`). Unchanged, in flight, no
horizon change. It exits when the **pinned oracle can be RETIRED** (`PDR-0058`, owner-ruled) — not
when anything merges. Merging is a publication step *inside* the bet.

The three exit conditions, read rather than asserted:

| # | condition | status 2026-08-16 |
|---|---|---|
| 1 | every `known-divergences.md` entry terminal | open |
| 2 | harness verdict vocabulary re-earned or successor recorded (`PDR-0056`) | open — **and newly worse, see below** |
| 3 | `Gates green` read on a suite that hides nothing (`PDR-0059`) | **substantially advanced, NOT met** — deselect 33 → 2 |

Work continues on **`project-recovery-2`**, now **17 commits ahead** of `main` (16 + this checkpoint). Merge gate 2
(README re-sweep at the merge commit, `PDR-0039`) is owed again by all of them.

## What this checkpoint did

- **Ran both remaining issues from `hamlet-a0832f9004` to ground and closed all three**
  (`hamlet-551be983a8`, `hamlet-9a4b3e9b73`, and the parent). Landed `e62a5e4a`, pushed.
- **Settled the escalation fork before writing a line of test code** (`PDR-0061`). `multi_tick` and
  wraparound hours **execute** — an 18→28 window is open at 02:00 across midnight; progress runs
  1→2→3→0 at `duration_ticks=4`; `costs_per_tick` is charged every tick. `PDR-0059`'s trigger did
  **not** fire: the pack was the defect, not the engine.
- **Removed the `slow` marker after measuring it** (`PDR-0062`). The three files run 31 tests in
  **34.8s** — "slow" was simply false. Default suite now: **3189 passed, 16 skipped, 2 deselected,
  0 failed**; arithmetic exact (3157 + 31 + 1).
- **Made a mandatory parameter required at binding** (`PDR-0064`) and deleted the dead fixture that
  had been asserting a signature which never existed.

## Blocked on nothing. Flagged for the owner (not blocking, but you should know)

**The differential harness cannot currently certify anything** (`PDR-0063`, `hamlet-6f98e38a36`,
P1). Its `test_self_comparison_agrees` runs `old_src` and `new_src` **both pointed at `src`** and
does **not** return `AGREE` — `environment.yaml` differs from the frozen fixture in
`oracle_fixtures/`. This is the instrument the entire strangler is measured against, and
`ORACLE.md`'s rule — *"a diff against the oracle is a defect in the rebuild unless the register says
otherwise"* — only means something if the instrument agrees with itself.

**Deliberately not fixed here.** The harness offers a fork: re-freeze the fixture, or register the
divergence. That is a specification call about what the oracle attests, and taking it in passing to
tidy a checkpoint is precisely what the pinned oracle exists to prevent. **It wants someone holding
the oracle context — that is the decision awaiting you.** Nothing is blocked on it meanwhile.

Also worth knowing: **the hidden-failure count was never 31, it was 33.** `hamlet-a0832f9004`
enumerated failures from a CI log naming three files and never asked what *else* the marker
covered. The fourth file is the harness above.

## Open questions

- **Exit condition 3 says "hides nothing", and 2 is not nothing.** `-m "not slow"` stays in
  `addopts` only until `hamlet-6f98e38a36` closes; `PDR-0062`'s reversal trigger says they come out
  in the same commit. If that issue is open at the next checkpoint, the exclusion must be
  re-stated, not inherited.
- **No shipped pack declares a `multi_tick` affordance or a wrapping schedule.** Both engine
  capabilities are now verified live, but their only exerciser is a test pack. `PDR-0061`'s
  reversal trigger fires the day a real pack declares one.
- **An agent cannot observe its own interaction progress** (`hamlet-266a0a41f0`) and no config pack
  can declare it observable — an "only by editing Python" gap, latent until a pack ships multi-tick.

## Next session starts here

**`hamlet-6f98e38a36`** — the differential harness, if the owner wants the oracle question taken
now; it is P1, it blocks exit condition 3, and it degrades condition 2. It needs the
re-freeze-vs-register decision above.

If instead the preference is to keep pushing the authoring surface, the queue is unchanged and
`hamlet-a0832f9004`'s displacement has now cleared: **`hamlet-2fe1c34ebb`** (P1, `semantic_type`
has three disagreeing vocabularies and no authority) is the originally sequenced next unit, with
**`hamlet-0dd4ac24d9`** (P1, presentation hardcoded by variable name) behind it. Note
`hamlet-45b35cfee5` (filed this session — `interaction_type` has two disagreeing vocabularies and a
hidden default) is the *same shape* as `hamlet-2fe1c34ebb` and could be taken in one pass with it.
