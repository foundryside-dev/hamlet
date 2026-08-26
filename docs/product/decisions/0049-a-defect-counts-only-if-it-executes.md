# PDR-0049 — A defect counts only if it executes: the name-blindness violations were measured, two were struck, and the metric's counting rule changes

Date: 2026-08-15   Status: **accepted** (a correction of the agent's own measurement and of a
metric definition — within the grant; the *principle* it corrects is owner-stated and untouched)
Author: Claude (standing product owner)
Corrects: `PDR-0045`'s two cited instances — **by pointer, not by overwrite** (the `PDR-0020`
practice). The principle stands entirely.
Related: `PDR-0045` (the compiler is name-blind), `PDR-0047` (the positive form of the same rule),
`PDR-0033` (a green tool is not evidence), `PDR-0010` (a recorded green is not a green),
`PDR-0012` (no tech debt until 1.0 — the authority for deleting rather than fixing)
Tracker: `hamlet-60dd3c4b53` (closed by deletion+correction), `hamlet-2fe1c34ebb` (the live defect
found instead), `hamlet-f9090ec3e8` (flaky gate found while verifying)

## Context

`PDR-0045` recorded the owner's principle — the compiler must not infer meaning from a variable's
name — and cited two measured violations, filed as `hamlet-60dd3c4b53`. Both were established by
**reading code**. Executed at `1b25c99d`, neither holds:

1. **`vfs_adapter.py:31-41` is dead code.** `vfs_to_observation_spec` / `VFSAdapter` have zero
   callers in `src/`; the only repo-wide references were their own two test files; importing
   `townlet.universe.compiler` does not put the module in `sys.modules` at all. The observation
   spec is built by `compilers/observation.py`, which hardcodes a literal per block — the
   adapter's `position`/`meter` vocabulary appears in **no** compiled output. **So the
   load-bearing consequence — "a pack naming its currency `credits` gets a different observation
   schema hash" — is false in the shipped compiler.**
2. **`metadata.py:83` executes but nothing consumes it.** `EAT` does compile to `cost=5.0` from
   the literal `"money"` key — but `AffordanceInfo.cost` has **zero consumers**
   (`grep -rn "\.cost\b"` over `src/` and `frontend/src/` → 0; `affordance_metadata` is read only
   for `.name`). Real in the artifact, inert in behaviour: the computed-but-unconsumed shape of
   `hamlet-2dde1015fe`.

## The call

**Resolve by deletion plus correction, not by the fix the issue proposed** — and change the
counting rule that produced the wrong number.

- **The dead module and its two test files are deleted** (`1478363e`), under `PDR-0012` /
  `CLAUDE.md`: not in use, delete it. **Proved inert before deletion was claimed**: all five
  levels' `observation_schema_hash`, `action_schema_hash`, `vfs_hash`, `variable_schema_hash` and
  `transition_graph_hash` are byte-identical before and after. Because nothing in production
  reached the code, **no oracle or divergence process was engaged** — the harness had nothing to
  adjudicate.
- **`PDR-0045` is corrected by pointer.** A banner strikes the two instances and states what the
  recon found instead. The original text stays legible, so the error is visible rather than
  laundered.
- **The `Demo dogfooding — privileged-Python count` metric changes its counting rule**, and this
  matters more than the number moving ≥6 → ≥4: **count executed behaviour, not grep hits.** A site
  that branches on a name is a privileged-Python instance only *if it runs*. The original
  enumeration was a static sweep, and a metric created to police false claims had inflated itself
  by exactly the mechanism it exists to catch.
- **Four artifacts that had propagated the false claim were corrected in the same commit**:
  `metrics.md`, `current-state.md`, `PDR-0045`, and `docs/architecture/archive/UNIVERSE-COMPILER.md:36` (which claimed
  compiler stage 5 uses the now-deleted adapter).

## Rationale, and the lesson worth keeping

The tempting alternative was to fix `_semantic_from_name` — it is four lines and the fix is
obvious. That would have shipped a change to code that never runs, moved no behaviour, and left
the metric overcounting. **The cheapest fix would have been indistinguishable from progress.**

The generalisable rule: *an issue filed from code reading is a hypothesis, not a measurement.*
This project already knows a green tool is not evidence (`PDR-0033`) and a recorded green is not a
green (`PDR-0010`). This adds the mirror: **a red found by reading is not a defect until it
executes.** Name-based special-casing is the hardest form to see (`PDR-0045`); the second-hardest
thing to see is that the special-casing you found is unreachable.

Note what this does **not** touch: `PDR-0045`'s principle is owner-stated and stands, `PDR-0047`
gives it its positive form, and there are still live name-branching sites — the frontend pair
(`hamlet-0dd4ac24d9`) and the curriculum pair. Striking two instances is not striking the rule.

## Consequences

**1. The recon's real yield is `hamlet-2fe1c34ebb`** — `semantic_type` has three disagreeing
vocabularies and no authority, the authored declaration is never consulted, and `default="custom"`
violates the No-Defaults Principle on a parameter that feeds a provenance hash. That is now a
decided direction under `PDR-0047` and raised to P1.

**2. A second finding came from verifying, not from the work**: `hamlet-f9090ec3e8` —
`test_vfs_overhead_under_limit` failed once and passed once on an unchanged tree. It asserts a 5%
wall-clock ratio measured under always-on coverage instrumentation, and it sits in the CI gate.
Ruled out as deletion-caused on two independent grounds before being dismissed (no random-ordering
plugin; it collects *before* the deleted tests).

**3. `hamlet-0dd4ac24d9`'s "enumerate the sites" precondition is met but reduced** — the
enumeration exists; two of its six entries are struck.

## Reversal trigger

- **Reverse the deletion** if any consumer of `vfs_to_observation_spec` or `VFSAdapter` is found
  outside the deleted tests — that would mean the zero-caller measurement was wrong, and the
  correct response is restoring from git history and re-opening `hamlet-60dd3c4b53` as filed.
- **Reverse the counting-rule change** if "count executed behaviour" starts hiding real
  authorability defects — specifically, if a site is excluded as unreachable and an author then
  hits it. Unreachable-today is not unreachable-by-design, and the rule must not become an excuse
  to stop counting.
- **Re-open the `metadata.py:83` reclassification** the moment anything reads
  `AffordanceInfo.cost`. It is currently inert; a consumer makes it a live name-branching defect
  again, immediately.
