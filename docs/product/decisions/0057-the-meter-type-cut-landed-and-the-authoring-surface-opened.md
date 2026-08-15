# PDR-0057 — the meter type cut landed: nine kinds authorable, and the review found two things I did not

Date: 2026-08-15   Status: **accepted** (autonomous, within grant — implementation of an
owner-approved ruling)
Author: Claude (standing product owner)
Owner sign-off: **yes**, on both the unit and the method —

> *"2 yes"* · *"ok, 1-3 are all noted, plesae proceed with W2/W3 using ultracode"*

Implements: `PDR-0053` ruling (a), `PDR-0054` W2–W8
Related: `PDR-0052` (underspecification is a compile error), `PDR-0045` (never branch on a
variable's name), `PDR-0016` (bounds and normalization are one feature), `PDR-0049` (a defect
counts only if it executes), `PDR-0056` (the oracle shape this rode on)
Tracker: `hamlet-3d3039f340` (closed), `hamlet-365e996511` (closed, subsumed)
Commits: `2535a306`, `43b4f33e`

## What shipped

`range_type` stopped being an inert `Literal["normalized","unbounded","integer"]` and became a
**nine-member discriminated union tagged by the VFS normalization kind's own name**. The meter
block stopped being one `obs_meters` field of width == meter count and became **one field per
meter**, each carrying its own spec. `_meter_normalization` was deleted outright rather than
parameterized — `PDR-0054`'s own reversal trigger said that growing a second path beside it would
mean the split was not the root fix.

**Acceptance, both legs of the ticket, met exactly.** `money=1000` under `log_scaled` observes
**0.500000**, not `0.000999` — and the whole predicted table matches to six decimal places.

`hamlet-365e996511` closes with it: `range_type` cannot be inert now, because it *is* the
selector. The old `unbounded` member was **deleted, not mapped** — translating it to a log family
would have been precisely the hidden default this programme exists to remove.

## Three things the plan did not have, found by pointing an instrument at the code first

The cut was preceded by a five-surface census with an adversarial challenge on each. It changed
the design, which is the argument for running it:

1. **`vtc.py` merges bars and VFS variables into ONE evaluation namespace and raises on
   collision.** A per-meter variable named `energy` would have broken every pack that writes a
   bar — at runtime, on the first tick. Hence namespaced `obs_meter_<name>` ids, **asserted** at
   compile time rather than trusted to a prefix the next reader takes for cosmetic.
2. **`build_activity` did not enforce group contiguity** — first-seen start, last-seen end — so
   interleaved semantic groups silently produced a slice spanning foreign dimensions. Harmless
   while every group was one field; W6 sizes a **network layer** from that slice, so it becomes a
   wrong tensor shape far from its cause. Now a compile error.
3. **`population/vectorized.py` WARNED on an obs_dim mismatch and loaded the checkpoint anyway.**
   Meter count no longer characterises the observation, so that warning was the check that would
   have caught this class. Promoted to an error.

## What the adversarial review proved, and what it cost

Six lenses over the committed diff, each finding then facing a skeptic prompted to refute it:
**23 findings, 21 refuted with executed repros, 2 minor survivors** — both fixed with regression
tests.

The most valuable output was not a finding. The authoring lens **executed all nine members end to
end on two levels: 9/9 compile, 9/9 observe, 9/9 step.** Before this session the tree had never
exercised more than two. That is the ticket's real claim, tested rather than asserted.

The two survivors were both mine to own:

- The reference config was left **self-contradicting by this work** — the migration matched a
  bare value, so the one line with a trailing comment kept the deleted member, while a comment
  eight lines above still taught the old vocabulary. A file whose whole job is to be copied,
  contradicting itself inside one hunk, reachable by no gate.
- `one_hot` was **not cross-validated against declared bounds**, so a pack compiled green and
  died on the first observation with a message naming no meter, no value and no file.

**The measured cost: ~21% on `env.step`, ~32% on `_get_observations`** (reproduced twice
independently). Eight per-meter registry reads and writes per tick instead of one vectorized
pair. **Accepted deliberately.** This product trades throughput for authorability by design; the
alternative was leaving 8 of 9 normalization kinds unauthorable. Recorded so nobody rediscovers
it as a mystery — the review's own skeptic confirmed the measurement and refuted the
classification, which is the right split.

## Consequences

1. **The north-star moves.** `vfs.md` §9.2's ten kinds stopped being a list of things the runtime
   can do that no pack can ask for. Nine of nine are now authorable and executed.
2. **A `PDR-0045` name-branch is gone**, not preserved: `networks.py` addresses the meter block
   through `group_slices["bars"]`. The bare `except Exception` that turned "I cannot find the
   meter block" into a silent fallback went with it.
3. **The whole restructure is provably behaviour-preserving** for the shipped packs: 16/16 oracle
   cells, CPU and CUDA, **every trace stream byte-identical** across 100 steps × 5 levels.
4. `COMPILED_SCHEMA_VERSION` 1.14 → 1.15, so every stale cache fails loudly instead of serving a
   different layout.

## Reversal trigger

- **Reverse the per-meter split** if any consumer is found that needs the meter block as a single
  `ObservationField` object rather than a contiguous span. `group_slices` was the evidence it
  would not be; a counter-example falsifies it.
- **Reverse `range_type` to a separate normalization field** (`PDR-0052` option (b)) if a meter
  needs two independent type facts that force a member per combination.
- **Escalate the throughput trade to the owner** if `env.step` cost is ever measured as blocking
  a real training run — not before. The number is recorded; a number is not a problem until
  something it gates fails.
- **Re-open the "all nine are authorable" claim** if a kind is found that compiles but cannot be
  used on a substrate other than Grid2D. The review's coverage explicitly stopped at Grid2D L1/L2
  and said so.
