# PDR-0052 — Underspecification is a compile error, and VFS must first be wired so a type can be defined cleanly — in that order

Date: 2026-08-15   Status: **accepted** (owner-made — an authoring-grammar ruling, which
`PDR-0016`'s first reversal trigger and `PDR-0047`'s second reserve for the owner)
Author: Claude (standing product owner)
Owner sign-off: **yes**, given in two consecutive statements that form one ruling. Asked to gate
on *"which normalisation kind a meter gets when unspecified"*:

> *"there's no such thing as unspecified here, the compiler should throw an error if a type is
> underspecified"*

and immediately after:

> *"this also means all of the various components of vfs need to be wired up so you can define a
> type cleanly"*

Completes: `PDR-0045` (name-blind — negative rule), `PDR-0047` (closed vocabularies, declaration
is authoritative — positive rule). **This is the third leg: completeness.**
Related: `PDR-0051` (Trial 002 — the measurement this rules on), `PDR-0016` (bounds +
normalization are one feature), `PDR-0037` (register before the cut), `PDR-0012` (no tech debt
before 1.0), the No-Defaults Principle in `CLAUDE.md`
Tracker: `hamlet-3d3039f340` (the wiring), `hamlet-2fe1c34ebb` (`semantic_type` authority),
`hamlet-365e996511` (`range_type` selection), plus one issue filed by this PDR

## Context

`PDR-0051` measured Trial 002 and escalated exactly one question: closing the normalisation gap
means deciding **what kind a meter gets when the author does not say**. Under `PDR-0047` rule 2
and No-Defaults there should be no default — but requiring a declaration breaks every shipped
pack, and `PDR-0047`'s second reversal trigger reserves that judgement for the owner.

The owner refused the premise of the question rather than answering it, which is the stronger
move: there is no "unspecified" case to assign a value to. An incomplete type is not a type with
a gap to fill; it is a **compile error**.

## The call

**Two clauses, and the order between them is the load-bearing content.**

### Clause 1 — completeness is enforced, not defaulted

> A type is either fully specified by the author or the compilation fails. The compiler never
> completes a partial declaration.

This is the third leg of a rule that was already two-thirds built. Together:

| PDR | rule | shape |
|---|---|---|
| `PDR-0045` | the compiler must not infer from a **name** | negative |
| `PDR-0047` | the author picks from a **closed vocabulary**, and the declaration is authoritative | positive |
| **`PDR-0052`** | an **incomplete** declaration is an error, never a filled-in default | completeness |

Name-blind, closed, complete. That is a type system rather than a bag of optional metadata, and
it is what *"it should work like a regular compiler"* (`PDR-0047`) actually requires — a C
compiler does not guess at a missing type, and it does not silently accept one it will ignore.

This retires the last hiding place for the failure shape this project keeps finding.
`default="custom"` (`hamlet-2fe1c34ebb`) and every sibling hidden default are now errors by rule,
not open questions.

### Clause 2 — the surface must be able to express a complete type first

> *"all of the various components of vfs need to be wired up so you can define a type cleanly"*

**Clause 2 is a precondition for clause 1, not a companion to it.** Enforcing completeness
against a surface that cannot express completeness does not produce correct packs; it produces
packs that cannot be written at all. `PDR-0051` measured precisely this: an author declaring an
unbounded resource today has **no valid declaration available** —

- `environment.yaml` `meters[]` rejects a `normalization` key (`extra="forbid"`);
- the meter block admits one compiler-chosen `minmax` for all meters;
- `variables_reference.yaml` accepts the declaration and silently discards it;
- the one path that does build observation fields caps at `minmax|zscore` — **2 of the 10
  implemented kinds, everywhere, not just for bars.**

Turn clause 1 on first and every honest author of an unbounded resource is blocked with no legal
move. That is strictly worse than today's silent wrong answer, because today at least the pack
runs. **Wire, then enforce.**

## Measured cost, honestly

- **108 meter declarations across 25 packs** would come into scope of a completeness check
  (8 in `default_curriculum`, 12 in `model_config_12meter`, 1–8 elsewhere). That is bounded
  mechanical work, and `CLAUDE.md` explicitly endorses it: *old configs should fail loudly*.
- **44 variable declarations already declare a normalization method** and would need no new
  field — but their vocabulary must widen from 3 methods to the full ten kinds.

## The one fork this ruling does not settle — **owner decision required**

`range_type` (`normalized`/`unbounded`/`integer`) and a normalization declaration **encode
overlapping information**. Two ways to make a meter's type complete:

- **(a) `range_type` becomes the complete type declaration** — a closed, *parameterized*
  vocabulary where each member fully determines the normalizer and its required parameters
  (`unbounded` demands a log family and its bounds; `integer` demands integer backing). No new
  field, the 108 declarations already exist, and the error fires when the chosen member's
  parameters are missing.
- **(b) a separate required normalization block per meter**, alongside `range_type`.

**Recommendation: (a).** Two reasons. The owner said *"if a **type** is underspecified"* — the
unit being declared is the type, not a bag of parallel fields. And (b) walks straight into
`PDR-0047`'s second reversal trigger: roughly 100 of the 108 meters are bounded `[0,1]` and would
all write the identical `kind: minmax`, whose parameters are already implied by declared bounds —
*"every pack writing the same value because there is only one sensible choice"*, which that
trigger names as the signal that a field is structural rather than authored. (b) would also leave
`range_type` inert beside it, preserving the exact defect `hamlet-365e996511` exists to kill.

This is flagged, not decided.

## Consequence that gates the work: **the oracle's inputs are not frozen**

Found while scoping this, and it is bigger than this ruling — measured, not read:

`harness.py::run_side` runs **both** sides with `cwd=repo_root`, varying only `PYTHONPATH`, and
`--pack` is a live relative path (`configs/default_curriculum`). The frozen worktree's own
`.oracle/oracle-2026-08-13/configs/` is never used, and carries no `differential/` at all.
**So both the oracle and the rebuild read config packs from the live working tree.**

Verified by executing the frozen oracle's compiler against a pack carrying one new meter key:

```
PYTHONPATH=.oracle/oracle-2026-08-13/src  →
  environment.meters.0.normalization
  Extra inputs are not permitted [type=extra_forbidden]
```

Every pack DTO is `extra="forbid"`, so **any new key in any pack file makes all 16 harness cells
crash on the oracle side** — not diverge, crash. The oracle pins the *code* and leaves its
*inputs* live, and WS-4's entire purpose is changing those inputs. This is a structural defect in
the harness, not a cost of this ruling, and it will break every future authoring-surface change
identically.

**The harness is green as of this PDR** (`default_curriculum:L1_full_observability` → AGREE /
SKIPPED, exit 0), and the Trial 002 packs are outside the matrix — `_DEFAULT_PACK` and
`_DIV003_FIXTURES` are hardcoded, so adding packs cannot perturb it. Checked rather than assumed.

Filed separately as a precondition for the WS-4 stream. Recommended fix: **freeze the harness's
fixture packs** alongside the pinned code, so pack evolution stops blinding the oracle.

## Consequences

1. **Sequence is fixed and non-negotiable:** freeze the oracle's inputs → wire the VFS type
   surface (`hamlet-3d3039f340`, widened to the full 2-of-10 ceiling) → require complete
   declarations → turn the error on. Each step is verifiable before the next.
2. **`hamlet-3d3039f340`'s owner gate is now closed** — the answer is "no default, error
   instead", pending only the (a)/(b) fork above.
3. **`hamlet-2fe1c34ebb`'s `default="custom"` is decided by rule**, not by a fresh judgement.
4. **`hamlet-365e996511` is subsumed if (a) is chosen** — under (a), honouring `range_type` *is*
   the completeness mechanism rather than a separate selection fix.
5. **Hash-moving throughout — `PDR-0037` order applies.** Register entries first, verified against
   the oracle at the tag, then the cut. Note this now interacts with the oracle-input gap: the
   register must be written while the oracle can still read the packs.
6. **No code changed by this PDR.**

## Reversal trigger

- **Reverse clause 1's scope** if "complete" cannot be defined for some legitimate type without
  forcing authors to state something the engine could derive structurally — that is `PDR-0047`
  fork (b) resurfacing, and it means the boundary between authored and structural was drawn in
  the wrong place for that field.
- **Reverse the order in clause 2** only if wiring proves to depend on the error existing (e.g.
  the surface cannot be designed without knowing what "incomplete" rejects). Presumptively false;
  if it turns out true, the two land together as one unit, never error-first.
- **Escalate again rather than deciding** if the (a)/(b) fork cannot be settled by the owner
  before the wiring starts — building against the wrong one is the expensive mistake here, and
  `PDR-0051` is the standing evidence that a trial beats an inference.
- **Reverse the "freeze the fixtures" recommendation** if freezing inputs would let the rebuild
  drift from packs authors actually write — a harness that only ever sees frozen fixtures stops
  testing the live authoring surface. The fix must freeze the *oracle side's* view without
  blinding the *new side* to real packs.
