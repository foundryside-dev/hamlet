# PDR-0081 — the trial protocol is ACTIVE and the instrument is whole: blind re-runs pin the commit, leg (a) counts untracked files, one session is the budget, and BLOCKED means the idea was refused, not the pack

Date: 2026-08-18   Status: **accepted** (owner chose the session's bet item — "write the trial
protocol", option 1 of the resume brief's proposals; the protocol's four design calls are the
agent's, within grant, on the `PDR-0079` pattern)
Author: Claude (standing product owner)
Owner sign-off: **yes** on the bet item; the design calls are autonomous within grant

Related: `PDR-0077` (the bet — this completes its instrument-existence half), `PDR-0078` (the bar
governs the metric), `PDR-0079` (the ABSENT/INERT/BLOCKED taxonomy the protocol operationalises),
`PDR-0080` (the frozen corpus this protocol executes against), `PDR-0051` (Trial 002's two-leg
method, now generalised), `PDR-0047` (predictions are mandatory because one was falsified)
Tracker: `hamlet-5fa1f7bfc0` (claimed `in_progress` this session; description reconciled to the
amended N=9 shape)
Artifacts: `docs/product/prds/0001-trial-protocol.md` (**ACTIVE** — mechanics dry-run passed
2026-08-18 at `2c1275d6`, every documented command executed once, all outputs matched),
`docs/product/trials/0001/TEMPLATE.md`, plan at `docs/plans/2026-08-18-trial-protocol.md`.
Commits `7cd19f17` → `99b69540`, pushed.

## Context — the corpus without a protocol is half an instrument

`PDR-0080` froze the corpus and drew the trial set, meeting criterion 1 a week early — but no
trial could run: criterion 3 (2 of 9 re-run blind, reproducing their verdicts) requires a written
protocol, and every verdict taken without one would be an executor's private judgment. The owner
chose this as the session's work from four proposed next moves.

## The four design calls (each changes what a verdict means)

1. **Blind re-runs execute at the first run's pinned commit**, in a `git worktree`. Criterion 3
   tests *protocol reproducibility*; a re-run at a newer commit conflates that with substrate
   drift — a disagreement could mean "the protocol is underspecified" or "WS-4 landed a unit",
   and the instrument must not be rejected (or accepted) on the wrong one. The per-trial commit
   pin exists exactly to make this separable.
2. **Leg (a) checks untracked files**: `git status --porcelain src/townlet/` must be empty
   alongside the PRD's `git diff --stat`. A *new* file under `src/townlet/` is invisible to
   `diff --stat` against the index — a hole through which a "zero-diff" pass could carry engine
   code. Faithful strengthening of criterion 4's intent, not a change to it.
3. **One working session is the effort budget, with a stopping rule** (all facets settled, or
   each unsettled facet classified at its furthest established point and the record marked
   budget-limited). A protocol without a stopping rule is not reproducible — one executor simply
   tries harder, and criterion 3 would measure persistence, not the substrate.
4. **BLOCKED means the *idea's declaration* was refused loudly.** A compile error naming a
   mistake in the executor's own pack is fixed and the trial continues. Without this line every
   typo would score the substrate BLOCKED, and `Failure loudness` — where loud refusal is the
   *good* news — would read as failure.

Also pre-committed per trial: the facet list and, per facet, the leg-(b) evidence the executor
will accept — written before authoring starts, append-only after. Without it, "observable" is
executor judgment and criterion 3 fails on vocabulary rather than on the substrate.

## Rationale

Each call closes a specific way the instrument could produce an unfalsifiable or wrong verdict
while appearing to work. The protocol was verified the only way a document can be: by executing
every command it documents against the live tree (dry-run at `2c1275d6` — corpus hash matched,
`validate` exit 0, `inspect --format json` emitted the artifact) before the Status line was
allowed to read ACTIVE.

## Reversal trigger

- **If a blind re-run disagrees with its first run** (criterion 3), the protocol is
  underspecified: the instrument is not accepted, no north-star reading is published, and the
  underspecified section returns to design under a superseding PDR.
- **If two of the first three trials end budget-limited**, the one-session budget is mis-sized —
  it is measuring the clock, not the substrate — and §5's budget is re-set by a superseding PDR
  *before* further trials run.
- **If a verdict hinges on whether a loud error was "about the pack" or "about the idea"** and
  two executors could reasonably disagree, call 4's line is not sharp enough and returns to
  design — that ambiguity is exactly what criterion 3's blind runs exist to surface.
