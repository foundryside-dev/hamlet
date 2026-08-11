# PDR-0025 — Presentation is *declared*, not deleted: honest by default, prettified only where a pack opts in

Date: 2026-08-12   Status: accepted (the "locked variant" as a distributable product is **Later / proposed** — see Consequences)
Author: Claude (standing product owner)
Owner statement: *"we might offer a 'variant' where you can download a 'locked' experiment that does have prettified stats (i.e. money is turned into money) but that would be more in the realm of 'look at this cool thing I designed' rather than regular use."*
Amends: `PDR-0023` — corrects the *fix* it prescribed for `hamlet-0dd4ac24d9`. Its call (units are nominal; do not moneyfy by default) stands.
Tracker: `hamlet-0dd4ac24d9` (re-scoped by this), plus a new inert-surface finding recorded below

## Context

`PDR-0023` recorded the owner's *"don't moneyfy"* and concluded the fix was to **delete** the
frontend's `if (name === 'money')` special case. The owner has now drawn a line I had collapsed:

- **Regular use** — honest display. A dollar is not a dollar; it is a normalised variable, and
  hiding that teaches a false model.
- **A locked showcase variant** — *"look at this cool thing I designed"* — where prettified
  stats are appropriate, because the audience is looking at a *designed artefact*, not learning
  what the substrate is.

So the defect was never "currency display exists." It is **that the display is hardcoded by
variable name, and therefore not a choice anyone can make.**

## The call

**Presentation becomes a declared surface with an honest default.**

1. **Default: honest.** Every meter renders from its declared range, uniformly. No name-based
   special cases anywhere in the presentation layer.
2. **Opt-in: declared.** A pack may declare how a variable is presented. A showcase pack turns
   currency formatting on deliberately; the curriculum packs do not.
3. **Never: inferred.** The frontend must not decide a variable is money because it is called
   `money`. That is the presentation layer knowing what the game is.

This is the owner's own VFS framing (`PDR-0020`) applied one layer out: **authors declare intent,
the system enforces mechanics.** It is also `PDR-0016`'s limiting principle restated — the test
is whether an author can change the behaviour from YAML. After this, they can.

## The surface already exists, and it is inert

`configs/*/environment.yaml` declares `cues:` with a `display:` block:

```yaml
cues:
  - name: low_energy_warning
    trigger: {bar: energy, threshold: 0.2, direction: below}
    display: {icon: "⚠️", color: "#FF6B6B"}
```

There is a `CuesCompiler` (`universe/cues_compiler.py`), a config schema (`config/cues.py`), and
a symbol-table entry. Measured 2026-08-12: `CuesCompiler` is **instantiated at
`compiler.py:69` and never called** — two references in the entire codebase, the import and the
constructor. `grep -rn "cue" frontend/src/` returns **zero hits**.

So the declared presentation surface exists, is schema'd, is compiled-adjacent, and **drives
nothing** — the same disease as `bars.*.bounds`, the VFS normalization ABI, `range_type`, and
`clamp_and_validate`. This is the **seventh** confirmed instance.

That is the good news for scoping: this is a *wiring* job with an existing declaration to wire,
not a new schema to invent. Whether `cues` is the right home for value formatting (it currently
models threshold-triggered signals, not formatting) is a design question for the implementer —
but the precedent that presentation is authored, not hardcoded, is already in the config.

## Rationale

The version of this fix in `PDR-0023` — delete the special case — would have been correct and
insufficient. It removes the false teaching, and it also removes the *capability*, leaving no
path back to it except re-hardcoding. The owner's variant would then have required exactly the
special case we had just deleted.

Declaring it costs no more and preserves both: the curriculum stays honest, and a showcase pack
can be pretty without a code change. Deleting a capability because its only implementation was
wrong is how a project loses a feature twice.

**One thing this deliberately does not do:** it does not make prettified display *available* to
the curriculum packs as a convenience. The default is honest and the curriculum packs keep it.
The point of the split is that the showcase is a different artefact with a different audience,
not that prettification is a preference.

## Consequences

- **`hamlet-0dd4ac24d9` is re-scoped** from "delete the special case" to "presentation is
  declared; honest default; no name-based branches." Its three underlying defects are unchanged
  and still real — the display is factually wrong post-WS-1(e) (22.5 → "$2250", bar pegged at
  100%), it hardcodes a domain fact, and the current behaviour teaches the wrong model.
- **A new inert surface is recorded**: `cues` / `CuesCompiler`, uncalled and unconsumed. Counted
  on the Declared-but-inert guardrail.
- **"Locked experiment" is a new product concept and is NOT decided here.** It is a third kind
  of artifact, distinct from the two already in play: the **oracle freeze** (internal reference
  for the rebuild) and the **model export** (`PDR-0024` — model + contract for a game dev's
  engine). A locked showcase is a *distributable* artifact for sharing a design. Recorded in
  `roadmap.md` under **Later** as intent only; building or distributing one is outward-facing
  and would escalate.
- **`PDR-0023`'s reversal trigger is partly satisfied already.** It said to reopen if *"a
  pedagogical argument is made FOR moneyfication."* The owner has made a narrower one — for
  showcase, not for teaching — and this PDR is the response.

## Reversal trigger

Reopen if **any** of the following:

- **Declaring presentation requires the runtime to interpret it.** The frontend may read a
  declared format; the *engine* must stay unaware. If a presentation spec starts affecting
  observations, rewards or transitions, the surface is in the wrong layer.
- **The honest default gets overridden in the curriculum packs.** If the shipped teaching levels
  turn prettification on, the split has collapsed and the owner's distinction is not being
  honoured — this PDR's whole basis.
- **`cues` proves to be the wrong home** and a new top-level presentation surface is needed.
  Fine, but it should be a deliberate schema decision, not an accretion onto a surface that
  models something else.
