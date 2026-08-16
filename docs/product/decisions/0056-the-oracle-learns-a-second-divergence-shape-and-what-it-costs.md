# PDR-0056 — the oracle learns a second divergence shape, and this is what it costs

Date: 2026-08-15   Status: **accepted** (autonomous, within grant — a harness change, not a
product-direction change; reported to the owner as the schedule-changing item of the session)
Author: Claude (standing product owner)
Owner sign-off: reported and acknowledged (*"1-3 are all noted"*) before the dependent work began.
Not a vision or strategy change, so it did not require sign-off; recorded here because it changes
**what the project's correctness instrument certifies**, which is worth an owner-legible record.

Related: `PDR-0037` (register before the cut), `PDR-0033` (a suppression mechanism is a machine
for manufacturing false AGREEs if it is loose), `PDR-0006` (the strangler), `PDR-0052` (whose
reversal trigger named the silent-and-green failure this guards)
Tracker: `hamlet-2090c9f16d` (the sibling defect, closed at `49bdf28e`)
Commits: `ecc37241`, `02643fe8`, `43b4f33e` · Register: `DIV-004`

## Context — a blocker found while verifying something else

W1 was written, tested and green. Verifying it against the oracle surfaced a structural problem
one layer above it:

**`compare_traces` compared provenance hashes FIRST and short-circuited on inequality, before
comparing a single trace stream.** So the harness could not express *"provenance moved as
intended, behaviour did not"* at all.

WS-4's entire purpose is changing the authoring surface, and every authoring change moves the
compiled hashes by construction. The oracle would therefore have gone **blind on exactly the
surface it exists to guard**, for the whole remaining duration of the stream. This is the same
shape as `hamlet-2090c9f16d` one layer up: the harness stops answering at the moment of use.

## The call

A **second `RegisteredDivergence` shape**, `RegisteredHashDivergence`, added because a register
entry needed it — the bar its sibling class sets for new shapes, not speculation.

Narrowness is the whole design:

- `hash_fields` is **enumerated**, never a wildcard.
- The observed set must equal the declared set **exactly**. An undeclared mover is
  `HASH_MISMATCH`; a declared field that did **not** move is `REGISTERED_DIVERGENCE_ABSENT`, the
  same treatment the crash shape gets when the oracle stops crashing.
- Streams are then compared **in full, byte-exact**. The declaration suppresses provenance
  inequality and nothing else.

`DIV-004` covers the whole normalization-vocabulary programme as **one entry**, because the
frozen fixture sits at the pre-programme schema for its entire duration; three entries would
describe three moments of one state.

## What it costs — measured, not designed in

A six-lens adversarial review ran 14 tests trying to smuggle a stream difference past the
suppression — reset-obs, last-obs, reward, done, `-0.0` vs `0.0`, NaN — and **failed in every
one**. The mechanism holds. But the review surfaced two real losses of signal, and they belong in
the record rather than in a footnote:

1. **`AGREE` is now unreachable for every cell in the 16-cell matrix.** All ten standing cells
   necessarily return `DIVERGED_AS_REGISTERED`, and the six DIV-003 cells return it via the crash
   shape. **Exit 0 no longer means "old and new agree"** — it means "everything diverged exactly
   as registered". That is a weaker statement, and it is weaker for as long as the entry lives.
2. **The pack-drift guard is armed on zero cells.** All 16 declare `pack_divergence="DIV-004"`,
   and that field is a **boolean** gate — declaring it blesses *arbitrary* drift between frozen
   fixture and live pack, not merely the schema change it was declared for. The machinery built
   at `49bdf28e` days earlier is inert while this entry is open.

Neither was visible from inside the change. Both were found by an instrument pointed at it, which
is the argument for pointing one.

## Consequences

1. Every future WS-4 cut can be verified against the oracle instead of blinding it. That was the
   alternative, and it was not acceptable.
2. The costs above are recorded in `docs/oracle/known-divergences.md` under DIV-004, where
   someone reading a green matrix will see them.
3. Hash movement is now **measured** at each cut against a git worktree at the pre-cut commit —
   never predicted. W1 measured three movers; W2/W3/W4 re-measured and found a fourth. The
   prediction was written down first, so a surprise would have been visible as one.

## Reversal trigger

- **Re-tag the oracle** if a THIRD cut needs to widen `hash_fields` again. A register entry that
  suppresses more at every cut is converging on suppressing everything, and at that point the
  honest move is to move the tag forward rather than keep widening the exception. Both costs
  above dissolve when the tag moves.
- **Revert the shape entirely** if any test ever demonstrates a stream difference passing as
  `DIVERGED_AS_REGISTERED`. That is `PDR-0033`'s false-AGREE machine, and the response is
  reversal, not relaxation of the test.
- **Split `pack_divergence` from a boolean into a declared file set** if drift is ever found in a
  matrix pack that the declaring entry did not intend. Cost 2 above is the standing reason to
  expect this.
