# PDR-0098 — Trial F's evidence audit: the PASS STANDS, and the broken worked example is a protocol defect rather than a verdict defect

Date: 2026-08-20   Status: **accepted** (owner directed the audit; the outcome falls in a branch pre-committed before it ran)
Author: Claude (standing product owner)

Related: `PDR-0083` (Trial F's PASS), `PDR-0086` / A.9 (the owner's prior Trial F adjudication),
`PDR-0096` (B.3, the amendment that raised the question)
Artifacts: `docs/product/trials/0001/F-evidence-audit-20260820.md` (new; `F-20260818.md`
untouched)

## Context

Amendment B.3 established that protocol §4's worked example — *"`inspect --format json` shows an
observation field for the wear variable"* — describes an output the command cannot produce. That
worked example is **Trial F's own shape**, so a recorded PASS in the north-star numerator rested,
on its face, on a command that could not have produced its evidence.

## Options

1. Let F's PASS stand — the owner already adjudicated F once (`PDR-0086`/A.9).
2. Commission an evidence audit by a fresh agent before any reading publishes.
3. Escalate to a full blind re-run of F, consuming or adding a criterion-3 slot.

## Call

**Option 2, the owner's choice.** Three outcomes were pre-committed **before the audit ran**, so
the finding could not be adjudicated under time pressure: *stands* → record it; *stands but the
pre-committed evidence was not what was executed* → a protocol defect B.3 already covers, recorded
by the standing agent; *not supported by its record* → moves the north-star numerator, therefore an
**owner** ruling, escalated.

**Outcome: F's PASS stands.** All four facets meet their pre-committed standards. The middle and
third branches did not fire.

## Rationale

The discriminator was verified independently by the standing agent rather than taken from the
audit: at the **trial commit itself** (`git show fb56fbbd:`), facet 1's pre-committed evidence is a
**disjunction** — *"`inspect --format json` **(or the compiled artifact)** shows the wear variable
declared"* — and the executor ran the sound disjunct. Facet 4 never named `inspect` at all
(*"a declared observation field named by the compiled spec"*). The three load-bearing words predate
the methodology review, so they are not a later softening. Nothing was substituted: the record
names X-or-Y and runs Y.

The audit did not merely agree. It ruled out facet 3's INERT false-pass class by making the `else`
branch observable on a scratchpad copy (proving `USE` still dispatches and the **declared guard**
is what stops the effect), ruled out energy saturation, verified facet 4 four independent ways
(source order, `mask[58]`, values across reset/GET/USE/DROP with the registry still holding 2.0
after DROP, and uniqueness of the carrying index), and confirmed B.3 on F's own pack while finding
a failure mode B.3 misses: with no cache built `inspect` exits 1 outright.

Engine drift since F's pin: **none** (`git diff --stat e5f7dd7a..HEAD -- src/townlet/` empty),
which is what licenses checking a 2026-08-18 verdict at HEAD.

By-catch filed, not fixed: `hamlet-17a7f03bc9` (a broken tool and an empty hand both encode 0.0 —
an author cannot declare "absent" distinctly from "zero"), `hamlet-f2a37a8c8a` (item-scoped
variables unreachable through `registry.get()`, filed explicitly as **not** independently
re-verified), and a third reproduction on `hamlet-bf42ac60b5`.

## Reversal trigger

If a later reader establishes that facet 1's disjunction was **added after** the trial commit — the
one fact this call rests on — F's verdict reopens immediately. The check is
`git show fb56fbbd:docs/product/trials/0001/F-20260818.md`, and it was run. Separately: if
`hamlet-17a7f03bc9` turns out to mean the wear value was never distinguishable from absence *at the
offset facet 4 relied on*, facet 4's evidence weakens and F returns to the owner.
