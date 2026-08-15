# PDR-0045 — The scenario author sets the scale; the compiler sees a name and a set of parameters, and must not know what any of them mean

Date: 2026-08-15   Status: **accepted** (within grant — records an owner-stated design principle
and files its measured violations; no code changed)
Author: Claude (standing product owner)
Owner sign-off: **yes** — stated directly: *"the answer on scale is 'the author of the scenario
sets the scale' — if they're modelling a town, money might be a constant capped at 200, if
they're modelling economy money might be logarithmic or what have you, but importantly VFS means
that the compiler doesn't know what money is, it sees a name, and a set of parameters and builds
it."*
Extends: `PDR-0023` (money units are nominal), `PDR-0020` (`range_type` routes the scale fix),
`PDR-0016` (bounds + normalization are one feature), `PDR-0006` (strangler), `PDR-0007`
(universality and configurability as the default)
Tracker: `hamlet-60dd3c4b53` (filed by this PDR), `hamlet-365e996511`, `hamlet-0dd4ac24d9`

## Context

`PDR-0023` dissolved the *unit* question — money is denominated in money units, and no fact of
the matter makes `22.5` "really" $22.50. What it left open was the constructive half: if the
engine has no opinion about what money is, **who decides how it is scaled?**

The owner's answer closes it. **The scenario author does, per variable, as a declaration.** A
town pack may cap money at 200 and treat it as a bounded meter; an economy pack may declare it
log-scaled and unbounded. Both are correct, because "correct" is a property of the authored
scenario, not of the engine.

And the load-bearing half is the second clause: **the compiler sees a name and a set of
parameters and builds it.** Not "the compiler has a sensible default for money" — the compiler
has no concept of money at all. `money` is a string an author chose, no different from `credits`,
`gold`, `substrate_ph`, or `q3_opex`.

## The call

**Accepted as a standing rule, testable against the tree:**

> No engine or compiler code may branch on a variable's *name*. A variable is a name plus
> declared parameters. Any behaviour that varies per variable must be driven by a declared
> parameter, never inferred from what the variable is called.

This subsumes the scale question rather than answering it: scale is one more declared parameter.
It also gives every future "should the engine special-case X?" question a mechanical answer.

**The rule already has a correct implementation in-tree, and it is the model:**
`config/drive_as_code.py:500` declares `money_bar: str = Field(description="Money bar name")` —
**required, no default**. `dac_engine.py:721` reads `config.money_bar` and resolves the index.
The engine knows *"some bar plays a currency role in this reward component"*; the author binds
which one. The engine holds the **role**; the author holds the **referent**. That is the shape
every site should take.

## Measured violations (2026-08-15, `project-recovery`)

Filed as `hamlet-60dd3c4b53`. This is also the enumeration `hamlet-0dd4ac24d9` asks for before
it can close — and it found the defect one layer deeper than presentation.

1. **`universe/adapters/vfs_adapter.py:31-41` — the compiler infers semantics from the name.**
   `_semantic_from_name` substring-matches against
   `["energy","health","satiation","mood","fitness","hygiene","money"]` — a hardcoded English
   vocabulary of `default_curriculum`'s meters — to assign `semantic_type`.

   **And `semantic_type` is hashed into the observation field UUID**
   (`universe/dto/observation_spec.py:21-30`). So a pack that names its currency `credits`
   instead of `money` gets a different provenance hash, for a reason with no structural meaning.
   The framework/instance boundary is breached *inside the compiler*, and the breach is
   load-bearing on identity.

2. **`universe/compilers/metadata.py:83`** — `aff.costs.get("money", 0.0)` collapses an
   affordance's cost dict to one scalar by looking up the literal key `"money"`. An author whose
   currency is `credits` gets `cost=0.0` everywhere.

3. Lower priority, same class: `curriculum/static.py:44` and `curriculum/adversarial.py:31-59`
   (hardcoded `active_meters` vocabularies); `recording/video_renderer.py:35,216` (hardcoded
   meter names and colours — recording is slated for removal under `hamlet-16ae192d42`).

## Rationale

This is `PDR-0006`'s *"the runtime should not know what the game is"* stated one level more
precisely, and it explains why that principle keeps being violated in small ways: **name-based
inference does not look like special-casing.** `if name == "money"` reads as a helpful default,
not as a hardcoded domain fact — which is how it survived in the compiler while the same defect
was being tracked in the frontend.

The designer-facing test from CLAUDE.md decides it cleanly. Ask *"can a designer express this in
a config pack?"* An author whose currency is `gold` cannot get it classified as a meter by any
amount of YAML. Their only recourse is to edit `_semantic_from_name` and add their word to a
Python list. That is the product defect the framing exists to catch.

It is also worth recording *why this is the right principle rather than merely a tidy one*:
`vision.md` names the prototyping modeller and *"anyone interested in game dev, simulations, or
modelling the real world in an abstract way"*. That audience does not have meters called
`hygiene`. For a factory, market, or ecology pack, nearly every variable currently classifies as
`None`. The framework silently works best for exactly one universe — the demonstration —
which is the failure mode CLAUDE.md warns about when it says not to harden `default_curriculum`'s
content into the framework.

## Consequences

- **`hamlet-60dd3c4b53` filed** (P1, WS-4) with both compiler sites, the hash consequence, and
  the `money_bar` contrast as the fix model.
- **`hamlet-0dd4ac24d9`'s "enumerate other sites" precondition is satisfied**, and its scope is
  now known to extend below the frontend. The two should be sequenced together: fixing display
  while the compiler still name-matches leaves the deeper defect in a provenance hash.
- **`hamlet-365e996511` (`range_type: unbounded` is inert) is the constructive half of this PDR.**
  It is the mechanism by which an author's declared scale actually takes effect. Under this
  principle its priority argument strengthens: without it, "the author sets the scale" is a
  statement the system cannot honour.
- **Fixing site 1 moves observation field UUIDs and the observation schema hash.** This is a
  registered-divergence change under `PDR-0030`'s pinned oracle, not a drive-by edit. Check
  `docs/oracle/known-divergences.md` before starting.
- **No code changed by this PDR.**

## Reversal trigger

Reopen if **any** of the following:

- **A case appears where name-blindness is genuinely impossible** — some behaviour that must vary
  per variable but cannot be expressed as a declared parameter. Then the rule needs a stated
  exception with a reason, not a quiet violation. Presumptively there is no such case; the
  `money_bar` pattern generalises.
- **Declaring semantic type per variable turns out to be onerous for authors** (e.g. it forces
  boilerplate on every variable in every pack). Then the fix is a declared default *at the pack
  or profile level* — still authored, still not inferred from the name.
- **The token-observation migration (`PDR-0044`, `hamlet-fa6bb6da4a`) removes `semantic_type`
  entirely.** Then site 1's hash consequence dissolves on its own, and only the metadata site
  and the general rule survive. Worth checking before investing in a fix to site 1.
