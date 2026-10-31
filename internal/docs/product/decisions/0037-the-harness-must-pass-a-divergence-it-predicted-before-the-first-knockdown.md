# PDR-0037 — The harness must be able to PASS a divergence it predicted, before the first knockdown cuts

Date: 2026-08-14   Status: **accepted** (within grant — dispatch / reprioritize inside the
committed Now bet; sequences existing WS-7 work, commits no new bet)
Author: Claude (standing product owner)
Related: `PDR-0032` (trace-only v1 — the scope assumption this closes), `PDR-0033` (a
verification tool gets an adversarial pass before it is trusted — applies to this change),
`PDR-0035` (the knockdown this gates), `PDR-0036` (the entry whose diff shape exposes it),
`PDR-0010` (the Gates-green lesson: an unusable gate is worse than no gate)
Tracker: `hamlet-e3af412673` (WS-7 content 3 ↔ content 5) · `hamlet-<new>` (the unit)

## Context

Found while planning content 5, in code accepted three days earlier as content 3.

The differential harness decides pass/fail at `src/townlet/oracle/harness.py:190-193`:

```python
def exit_code(verdicts: list[CellVerdict]) -> int:
    if not verdicts:
        return 1  # an empty run proves nothing; refuse to look green
    return 0 if all(v.kind in ("AGREE", "SKIPPED") for v in verdicts) else 1
```

The verdict vocabulary is `AGREE | DIVERGE | HASH_MISMATCH | OLD_SIDE_ERROR | NEW_SIDE_ERROR |
SKIPPED | HARNESS_ERROR`. **None of them means *diverged exactly as the register said it
would*.** The harness states the assumption in its own docstring (`harness.py:11`,
`trace_io.py:88`):

> No register entry can manifest in an env trace today (DIV-001/002 are checkpoint-boundary).

That was **true when written.** `PDR-0032` scoped v1 trace-only for exactly that reason, and
the reasoning was sound at the time. The first knockdown makes it false: `PDR-0035`'s whole
point is that three configurations which crashed in the oracle run in the rebuild, and
`PDR-0036` records that as a trace-visible intended divergence.

Consequence if left alone: a **correctly rebuilt** substrate makes the harness exit 1 —
`OLD_SIDE_ERROR` on every new cell — and *"run the harness before and after every knockdown
step, exit 0 iff every cell AGREE or SKIPPED"* stops being a usable gate at the very first
knockdown it is used for. The operator's only recourse is to read the report by eye and decide
which reds are fine, which is how a gate becomes decorative. That is `PDR-0010`'s lesson
arriving early enough to prevent instead of diagnose.

## Options

1. **Cut the seam first, fix the harness when it goes red.** Discover the contract gap at
   first use.
2. **Close the register-suppression seam before cutting** — declare expected divergences per
   cell, populate `register_refs`, and widen `exit_code` so a divergence matching its
   registered entry passes while an unmatched one still fails.
3. **Exempt this knockdown from the harness** — judge it by hand, defer suppression until a
   knockdown that needs it less awkwardly.

## The call

**Option 2.** Three reasons, in order of weight:

1. **The hook already exists.** `CellVerdict.register_refs: tuple[str, ...] = ()`
   (`trace_io.py:96`) is documented in the code as *"the binding point for known-divergences
   entries; empty in v1"*, and is already serialized into the run report
   (`harness.py:201`). Nothing populates it and `exit_code` ignores it. This is closing a seam
   the design deliberately left — not redesigning the harness, and not re-opening `PDR-0032`.
2. **Option 1 inverts the register's purpose.** The register exists so intended diffs are
   *recorded up front rather than discovered by a failing diff* (`known-divergences.md:13-14`).
   Cutting first and reacting to red is the exact practice the register was built to replace.
3. **Option 3 is how a gate dies.** The first knockdown is the one that establishes whether
   the strangler's safety net works. Exempting it teaches that the harness is advisory.

**`PDR-0033`'s standing practice applies and is not optional here.** This is verdict-emitting
code, and a suppression mechanism is a machine for manufacturing false AGREEs if it is loose —
a too-broad `register_refs` match would wave through real rebuild defects on the same surface.
It gets one review pass briefed to hunt **wrong passes** before its verdicts are trusted.

Worth recording as the general form: `PDR-0033` taught *ask what a green tool cannot see.*
This is the inverse — **ask what its red cannot distinguish.**

## Consequences

- **Content 5's order changes:** (1) close the register-suppression seam; (2) append DIV-003;
  (3) extend the declared matrix with cells exercising the three crashing configs; (4) cut the
  seam. The register's rule — entry before seam — is preserved.
- **The matrix must grow.** `matrix.py:36-58` hardcodes `configs/default_curriculum` × 5 levels
  × {cpu, cuda}; none of the three crashing combinations is in any cell, so the divergence is
  currently unexercised. `RunParams.pack` is per-cell and cells are declared in that file by
  design, so this is a pack fixture plus cell declarations, inside the knockdown's scope.
- **`PDR-0032` reversal trigger 2 was checked and does NOT fire.** It arms when *"a rebuild
  changes config schema such that the oracle can no longer parse the shared pack."* The schema
  is unchanged; both sides parse the same pack; the oracle fails at `env.reset()`, not at
  parse. Adjacent, checked, not triggered — recorded so the next session does not re-check it.

## Reversal trigger

- **If the adversarial pass on the suppression mechanism finds a way for a registered entry to
  mask an unrelated real divergence** on the same surface, suppression is too coarse: narrow
  the match (per-field, per-step) or abandon per-cell suppression for an explicit
  expected-shape assertion instead of a pass-through.
- **If a knockdown is later found to have been judged by a suppressed divergence that was not
  the registered one**, this mechanism has produced the false AGREE `PDR-0033` exists to
  prevent, and it needs a stronger correctness argument than review.
- **Fold this back** if two consecutive knockdowns register no trace-visible divergence — the
  suppression path would then be unexercised machinery, and unexercised machinery in a
  verdict-emitting tool is itself a risk.
