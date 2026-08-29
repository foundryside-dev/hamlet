# PDR-0119 — The exit door is load-bearing: train here, deploy there, same declared telemetry

Date: 2026-08-24   Status: **accepted** (records owner statements made in-session;
no agent decision — the vision content is the owner's own words. Incorporating wording
into `vision.md` is flagged for owner sign-off, per the vision-change gate.)
Author: Claude (standing product owner), content by John
Related: `PDR-0024` (export axis named 2026-08-12, audience widened 2026-08-13 — this
extends it), `PDR-0114` (token design — the ABI the export contract lands on),
`PDR-0016` (structure vs scale)
Tracker: `hamlet-0cdb8a6d1a` (no model export path — promoted by this articulation from
known gap to vision-load-bearing)

## Context

The owner articulated the end-state loop in full: a game designer sits down, asks "can I
teach an agent to learn how to play my game", authors it as config, trains — and then
**takes the trained model and drops it into their real game, provided they keep the same
interfaces**. Elaborations, same session: engine bindings (Unreal, Unity, Godot) come
"when we're in a position where it's needed"; and the **fidelity-abstraction claim** —
train an agent to sail a ship on a 2D surface, drop it into a high-fidelity naval
simulation, "the agent is seeing the same telemetry so it works seamlessly."

## The call (what this records)

1. **The interface is the declared manifest, not the substrate**: variables + bounds +
   normalization on the observation side, the declared action vocabulary + cadence on
   the action side. Fidelity lives below the interface. The compiled hashes
   (`vfs_hash`, `observation_schema_hash`, `drive_hash`) are what make "same
   interfaces" checkable rather than hopeful.
2. **Consequences adopted**: `hamlet-0cdb8a6d1a` (export path) is vision-load-bearing,
   sequenced after the token migration (export against the token ABI, not the dying
   raster); normalization-at-exposure defects are vision-critical, being closed inside
   unit 3's cut; the action side of the contract (engine accepts the declared discrete
   vocabulary at the declared cadence) is the harder half and belongs in any binding
   design.
3. **Not scheduled**: bindings and the export unit are intent, owner's to promote;
   nothing enters Now.

## Reversal trigger

If a real deployment attempt shows the declared-telemetry contract insufficient in
practice (a policy that cannot act sensibly on a host publishing the same manifest at
the same cadence), the fidelity-abstraction claim is re-examined as a design problem —
before any binding work is funded.
