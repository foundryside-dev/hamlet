# PDR-0132 — Token recovery runs as five checkpointed milestones

Date: 2026-08-31   Status: **accepted** (owner-directed standing plan)
Author: Codex (standing product owner)
Related: `PDR-0114`, `PDR-0131`, `hamlet-fa6bb6da4a`

## Context

`PDR-0131` selected the representation direction, but its sequence still lived partly as prose
inside one umbrella issue. That is too coarse for the next work. Two semantic regressions must be
settled before the compact ABI is designed, engineering regression evidence must be accepted
before pack migration, and each boundary can invalidate assumptions made about the next one.

The owner directed that this become an ongoing plan with a product checkpoint after every
milestone. The tracker therefore carries separate implementation and acceptance units rather
than one task whose status hides where the evidence actually stands.

## The call

Run token recovery as these five milestones, in this order:

1. **Canonical bounded positions — `hamlet-6a4a6596bd`.** Delete the inert
   `observation_encoding` field from DTOs, configs, docs, fixtures and shipped packs. Establish
   one bounded position and egocentric-delta encoding; raw grid deltas do not remain as a hidden
   alternative. Remove or repurpose `div003_scaled` so the differential matrix does not claim to
   exercise a deleted axis.
2. **Meter range normalization — `hamlet-1e335e0363`.** Restore the declared `range_type`
   transformation into meter-token live values. This surface is wired, not silently deleted.
   Tests must show that distinct declared transformations produce the distinct expected values
   while descriptor identity and the emitted dynamic value remain consistent.
3. **Compact replay ABI — `hamlet-1b1caf552a`.** Implement `PDR-0131`: immutable token context
   lives once in the compiled artifact, replay stores compact dynamic state, and the fixed schema
   is reconstructed at the network boundary. The L1 target is 118 floats and the acceptance cap
   is 120; the old full-payload ABI is deleted.
4. **Unit 4 engineering regression — `hamlet-25fc3fb955`.** Under `PDR-0137`, accept the
   four feedforward/recurrent × mean/attention cells against the raw 79.19 greedy-survival floor
   on deterministic representative seed 45 at its full frozen transition budget, with the named
   transfer, visibility, recurrent-memory, batch-size and aggregation evidence recorded.
5. **Unit 5 pack migration — `hamlet-55b2826a02`.** After Unit 4 and the 2026-10-06 trial-pack
   disposition condition, migrate every surviving shipped pack to the accepted ABI and delete
   the superseded configuration and code paths.

The implementation umbrella `hamlet-fa6bb6da4a` depends on milestone 5 and closes only after all
three child milestones are terminal. Milestone 3 depends on both semantic repairs; milestone 4
depends on milestone 3; milestone 5 depends on milestone 4. The two semantic repairs remain
independently startable, but product execution takes them in the order above.

## Checkpoint contract

A milestone is not handed off merely because code exists. Before starting the next milestone:

1. its Filigree issue is terminal with the acceptance evidence and exact verification commands
   recorded;
2. `current-state.md` is rewritten to the new present, and the roadmap/metrics are refreshed if
   their committed intent or readings moved;
3. any non-trivial product or representation call is captured in a new PDR; and
4. the checkpoint is committed and pushed on the active `project-recovery*` branch.

If evidence from a milestone invalidates an assumption behind the accepted next milestone, stop
at the boundary and re-plan in a new PDR. Do not skip, combine, or retrospectively paper over the
checkpoint. This is sequencing and evidence control, not a compatibility programme: the project
remains pre-release and every superseded path is deleted.
