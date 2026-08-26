# PDR-0124 — The token cut is adjudicated: the unit lands with nine defects open and named, and reversal trigger 3 is ESCALATED, not absorbed

Date: 2026-08-26   Status: **accepted** for the landing decision · **ESCALATED** for the
width cap (see "What the owner must decide")
Author: Claude (standing product owner)
Related: `PDR-0114` (the token design + trigger 3), `PDR-0123` (the cap is not moved; the
measurement is brought forward to here), `PDR-0037` (record-then-bind), `PDR-0033`
(narrowness), `PDR-0066` (a declaration reaching nothing is removed), `PDR-0012`/`PDR-0013`
(no tech debt), `PDR-0074` (the oracle move-forward precedent, pre-registered for this task
and not triggered)
Evidence: unit-3 Task 11 report; matrix acceptance runs `20260826-172349` (`--scripted`) and
`20260826-172441` (plain), both exit 0; `docs/oracle/known-divergences.md#div-008`;
`docs/product/baselines/2026-08-l2-preraster/rnd-intrinsic-distribution-across-the-cut.md`

## Context

Unit 3 replaced the observation ABI: the fixed-width superset with a per-level activity mask
became a compiled `TokenSpec`. The cut landed at Task 10; Task 11 is the adjudication — bind
DIV-008 against a measured mover set, read spec §5 off the resulting matrix, and rule on what
the cut left open.

Two things were true walking in. The §5 criterion — *tokens change what agents see, never what
the world does* — was verified on **2 of 10** cells, because `compare_traces` returns
`HASH_MISMATCH` before any stream comparison and DIV-008 was unbound, so eight cells never
reached the comparison at all. And `PDR-0123` had ruled that if Task 11's re-measurement landed
≥8×, trigger 3 fires **here**, not at unit 5.

## The calls

**1. The §5 criterion is verified, and the unit lands on it.** Binding DIV-008 let the other
eight cells reach the stream comparison. All ten executed cells return
`DIVERGED_AS_REGISTERED` with `shape: "hash+stream"` and a `streams` key **present**
containing exactly `{"obs"}` — in both scripted and plain mode. `actions`, `dones` and
`rewards` are byte-exact across the cut on every cell. This is stated in the form that
distinguishes it from the error a controller correction had to make against the Task-10
report: an **absent** `streams` key means never compared; a **present** one containing only
`obs`, in a verdict that reached stream comparison, is the proof.

**2. The unit lands with nine defects OPEN and RECORDED, and one that BLOCKED, fixed first.**
`hamlet-02684be106` (L3 unobservable) blocked and was fixed declaratively at `9563dc45` before
the binding — a shipped curriculum level whose entire distinguishing feature the agent cannot
see is not something to land a unit on top of. The other nine do not block. Landing with
defects named is honest; growing the task until it cannot land is not (`PDR-0012`'s shape,
applied to scope rather than to debt). Per-defect rulings are on `hamlet-fa6bb6da4a`.

**3. Two matrix cells are demoted as evidence, in writing.** `div003_scaled` can no longer
discriminate its own axis (`observation_encoding` is inert: `scaled` and `relative` compile to
a byte-identical TokenSpec), and `items_smoke`'s three item types are byte-identical apart
from position. Both still pass. **A cell that has stopped measuring what it was added to
measure is worse than a missing cell, because it reads green.** Recorded so no future reader
cites either as evidence for the axis it no longer sees.

**4. DIV-006 and DIV-011 retire into DIV-008; DIV-010 does not.** The discriminator applied:
*does this entry's own cause independently move the field, and does the other entry still
describe something that exists?* DIV-011 retires by its own pre-registered condition. DIV-006
retires because its new-side surface was **deleted** — binding it would certify a ghost.
DIV-010 stays, because the tick `VariableDef` is still injected and still moves the hash
independently of the cut.

**5. Reversal trigger 3 is FIRED and ESCALATED.** See below. No lever is taken and the cap is
not edited.

## Trigger 3: the measurement and the three levers, drilled with data

**Measured: L1 `total_dims` = 1132** against a pre-cut allocated 120 = **9.43×**, above the 8×
cap. (Not `PDR-0123`'s 1080/9.0× — the L3 temporal declaration added one `variable_element`
token, 52 dims, on all five levels.) Census: `self` 1×18, `meter` 8×12, `affordance` 14×66,
`item` 2×21, `variable_element` 1×52; `agent` and `effect` capacity 0. **924 of 1132 — 82% —
is the affordance block.** 8× of 120 is 960, so ≥172 dims must go.

**Lever 1 — meter-signature variance. REFUTED BY THE DATA; there is no width here.**
Measured across L1's eight real meters: **seven of the eight declared parameters vary**, and
all **eight meters have distinct full signatures**. Only `lethal_max` is constant (every meter
declares it false). Removing it would save 64 dims → 1068 = 8.9×, still over — and it would be
removing a declared parameter from a per-universe **transfer contract** because *this* pack's
meters happen to agree, which is the trap in miniature. The signature is doing exactly the job
spec §1 gives it: name-free identity that discriminates eight meters eight ways. Nothing to
reclaim.

**Lever 2 — position padding. Big enough, and NOT TAKEABLE.** Rank-adaptive padding on a
rank-2 substrate would save **210 dims** (18.6%) → **922 = 7.68×, under the cap**. It is
refused because it breaks the property `PDR-0123`'s own condition names. Payload width is
fixed per type **across all universes** (spec §1, first invariant), and that is not decorative:
measured 2026-08-26, `token_type_schema_hash` — the transfer contract, and the field the
checkpoint gate compares for token nets — is **identical across a 2-D grid, a 3-D cubic grid
and an aspatial universe** (`428982ef5d81dd26` on `default_curriculum`,
`differential/div003_cubic_partial`, `aspatial_test` and all three `token_transfer_*` packs,
whose `total_dims` range 162–1132). Rank-adaptive padding makes that hash rank-dependent, so a
Grid2D-trained checkpoint stops loading into a Grid3D universe. **`MAX_POSITION_RANK` is what
buys cross-substrate transfer; the 210 dims are its price.** Changing it is a superseding
decision on spec §1, not a Task-11 tuning.

**Lever 3 — K. Right-sizeable by the data, and still not enough.** Measured across the whole
`configs/` fleet from the compiled affordance metadata — 175 affordance declarations: **0
deltas ×19, 1 ×88, 2 ×66, 3 ×2, and nothing above 3.** The two threes are both in
`configs/test/action_masking`. So **K=4's fourth slot is provably absent-marked on every pack
in the fleet**, and K=3 is right-sized *by the declared data* rather than by the cap — the
distinction `PDR-0123` insists on. But K=3 gives **978 = 8.15×**, still over. K=2 gives
6.87× and would truncate two real declarations: that is cap-chasing, and lossy, and is
refused.

**Conclusion: no lever brings it under 8× while preserving spec §1's
identity-by-declared-parameters property.** `PDR-0123`'s reversal trigger fires exactly as
written.

## What the owner must decide (ESCALATED — outside the standing grant)

`PDR-0114` is **REOPENED** on the cap itself. The cap is not silently edited and no lever is
taken. Four options, with what each costs:

1. **Accept 9.43× and move the cap**, recording that 82% of the width is the affordance block
   and that the block is doing real work (the effect summary is the mechanism by which an agent
   can tell what an affordance *does* without being told its name). Cost: a reversal trigger
   moved to fit a measurement, which is the anti-pattern triggers exist to prevent — so if this
   is the call it needs the reasoning written down, not just the number changed.
2. **Take K=3 anyway** on its own data justification (nothing in the fleet declares 4), landing
   at 8.15× and moving the cap by a hair rather than by 18%. Honest, but leaves zero headroom:
   the next author who declares a fourth effect gets it silently dropped, so it should come with
   a loud compile-time advisory at K, not silence.
3. **Reopen spec §1's fixed-width invariant** and take the 210-dim padding lever, accepting
   that cross-substrate transfer becomes rank-scoped. This is the only option that gets under
   8× on today's content, and it trades the property the padding exists to buy. It should not
   be taken to satisfy a width cap.
4. **Keep both the cap and the constants and treat 9.43× as a debt against unit 5**, where
   the pack migration may change the census anyway (item and `variable_element` capacities are
   near zero on `default_curriculum` today and will not stay that way).

The measurement is not ambiguous and none of the levers is a free win. This is a real
trade — width against transfer generality against declared-content headroom — and it is the
owner's, not the agent's.

## Reversal trigger

If unit 5's pack migration moves L1's census materially (in either direction), re-measure
before acting on whichever option is chosen: the affordance block's 82% share is a property of
`default_curriculum`'s fourteen affordances and eight meters, not of the framework.
