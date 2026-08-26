# PDR-0044 — The token-observation direction was authoritative from the outset; `PDR-0017` mis-read "orthogonal" as "optional"

Date: 2026-08-15   Status: **accepted** (within grant — corrects the provenance record of a prior
PDR; internal repo documentation, git-reversible)
Author: Claude (standing product owner)
Owner sign-off: the correction **is** the owner's, stated directly — *"yes, the comment was
orthogonal to the work at the time but it was authoritative"* — in response to my characterising
it as newly firmed-up.
Related: `PDR-0017` (corrects its provenance framing, preserves its sequencing), `PDR-0016`
(structure vs scale), `PDR-0009` (per-level architecture gap)
Tracker: `hamlet-fa6bb6da4a`, blocked by `hamlet-0d0115383e`

## Context

`PDR-0017` recorded the owner's 2026-08-11 proposal to *"move to embedded transformers to 'solve'
our obs problem"*, together with the immediate clarification: *"more of an orthogonal comment …
we should have put a pin in that a long time ago"*.

`PDR-0017` read that clarification as a **disclaimer of authority** — a musing captured for later
— and wrote that *"the owner also disclaimed the urgency directly"*. On 2026-08-15, while
dispositioning the observation-dimension documents, I again described the direction as having
been *"recorded, not started"* and only now firming up. The owner corrected that reading.

## The distinction that was missed

**"Orthogonal" answers *when*, not *whether*.** The owner was declining to redirect a session
mid-flight. That is a statement about sequencing, not about standing. `PDR-0017` collapsed the
two — and, having collapsed them, used the supposed disclaimer as a *supporting premise for
deferral*. The record then read as though the direction carried less weight than it did.

## What changes

1. **Provenance corrected.** The direction has been owner-authoritative since **2026-08-11**, not
   since 2026-08-15. The recent statement — *"the dims manual is being replaced in its entirety
   because we are going to use embedded transformers"* — is a restatement of a standing decision,
   not a promotion of a captured idea.

2. **One premise in `PDR-0017` is struck.** *"The owner also disclaimed the urgency directly"* is
   false and must not be cited again as grounds for deferring this work.

3. **The sequencing survives — on its own merits.** `PDR-0017`'s option 3 stands: the first unit
   is a config-in/behaviour-out test proving `set_encoder` runs at all, not the transformer. That
   conclusion never depended on the owner's urgency; it rests on the argument that carried it —
   *an unexercised code path in this codebase is not presumptively working*, with six declarative
   features shipped inert as the base rate. **Authority over *what* does not settle *what
   order*.** The conclusion was right, for one wrong reason among several right ones.

4. **Priority rises.** The fixed-width observation is now a known dead end carrying an owner
   directive, not a parked idea. `hamlet-fa6bb6da4a` should not sit indefinitely behind the
   recovery, and `hamlet-0d0115383e` (per-level `architecture` is not overridable) gains its
   **third** consumer — it already blocked the documented MLP→LSTM progression and the
   `set_encoder` proof.

5. **The HLD does not contest this.** `PDR-0017`'s third reversal trigger fires if the divergence
   map concludes the target observation is *not* token-based, noting the HLD had not yet been
   read on the question. It has now been: grep across `docs/architecture/hld/` for
   `token|attention|transformer|set_encoder|deepset|permutation` returns only incidental hits —
   a reservation token in `09-affordance-semantics`, *attention* as a bar name, "attention
   memory" among recurrent state types. The HLD specifies **no** observation encoding, fixed or
   token-based. The trigger does not fire; the design authority is silent, not opposed.

6. **The doc disposition was retroactively correct.** `docs/zzz. archive/vfs/observation-dimension-formulas.md`,
   `observation-dimension-manual-validation.md` and `docs/zzz. archive/vfs-integration-guide.md` were marked
   *superseded in full, do not correct* rather than having their arithmetic fixed. That is the
   right call under "authoritative" and would have been wrong under "captured musing" — the
   **method** is obsolete, not the numbers: a token observation has no total width to validate.

## Rationale — the failure mode worth naming

**Treating a scheduling signal as an authority signal.** The owner deferred *timing*; I recorded
*reduced commitment*. The error is asymmetric and self-perpetuating: a direction recorded as
tentative gets sequenced late, late sequencing produces no evidence, and absence of evidence
keeps it recorded as tentative. Nothing in the record ever contradicts the original mis-read.

It is also the mirror image of the failure this recovery exists to fix. `docs/` is full of
**intent mislabelled as record** — designs marked "Approved for Implementation" that were never
built. This is the same class of defect running the other way: a **decision mislabelled as
intent**. Both corrupt the record by mis-stating epistemic status rather than facts, and both are
invisible to any check that only verifies claims against code.

Standing practice, recorded here: **when an owner defers timing, record the timing deferral and
the authority separately.** Where a phrase — *"orthogonal"*, *"put a pin in it"*, *"for later"* —
could carry either meaning, ask which is meant rather than inferring the weaker one. Inferring
the weaker reading is not the conservative choice; it silently discards a directive.

## Consequences

- **`PDR-0017` is not rewritten.** Per the practice in `PDR-0020`, the original framing is
  preserved and corrected by pointer, not overwritten. A status line referring here has been
  added to it; its analysis, options, and reversal triggers are untouched and still govern.
- **The structure/scale split in `PDR-0017` is unaffected** and remains the most useful thing it
  records: tokens fix observation *structure*, not *magnitude*. Scale still belongs to the
  declared normalization surface. A future session must not read "the transformer direction was
  authoritative all along" as "the obs problem is solved by tokens".
- **No code changes and no re-sequencing inside the current work.** This corrects a record.
- **Observation dimension documentation is closed as a line of work.** Nothing further should be
  spent reconciling width tables; see the superset/activity-mask measurement recorded against
  `hamlet-7a52a63e0b` for what the numbers actually are while the current scheme lives.

## Reversal trigger

Reopen if **any** of the following:

- **The owner names a different observation direction.** This PDR records authority, so a change
  of direction supersedes it outright rather than qualifying it.
- **`set_encoder` proves inert or broken.** Already `PDR-0017`'s second trigger; it escalates as a
  design fork — repair or replace the token path — rather than being decided in-flight. Raised
  priority does not license answering that question without the owner.
- **The first unit shows the token path cannot express the current observation** (e.g. the grid
  encoding has no natural token form). Then the migration is a redesign, not an aggregator
  upgrade, and the cost basis in `PDR-0017` is wrong.
