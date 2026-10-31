# PDR-0131 — Token width is a replay-layout problem: static context leaves the transition

Date: 2026-08-31   Status: **accepted** (standing product owner, under the grant re-confirmed
unchanged by the human owner at this session)
Author: Codex (standing product owner)
Supersedes: `PDR-0126`
Related: `PDR-0114`, `PDR-0123`, `PDR-0124`, `hamlet-fa6bb6da4a`

## Context

The 9.43× reading was treated as one undifferentiated observation-width problem. That hides the
actual engineering cost. The default replay buffer preallocates both observations and next
observations on the training device (`replay_buffer.py:99-105`) for 100,000 transitions
(`configs/default_curriculum/brain.yaml:28`). At 1,132 float32 values, those two tensors consume
905,600,000 bytes (863.6 MiB), versus 96,000,000 bytes (91.6 MiB) at the pre-cut width of 120:
an extra 772.1 MiB per buffer.

The L1 token census also shows why. Of the 1,132 serialized floats:

- about 810 are immutable descriptors repeated on every tick — meter signatures, affordance
  interaction/effect declarations, variable descriptors and declared ranks;
- 204 more are padding coordinates out to `MAX_POSITION_RANK = 8`;
- the live state, stored at the substrate's actual rank, is 118 floats for the current census:
  self 5, meters 24, affordances 70, items 16, variable elements 3.

The 8× trigger caught a real smell, but raw network-input width is the wrong acceptance proxy.
Static declaration context may legitimately be large; duplicating it in every replay transition
is the defect.

## The call

**Split the representation.** The compiled universe carries immutable per-slot token context
once. Replay stores only compact dynamic state: presence, live values and coordinates at the
substrate's actual rank. The token network combines both at its boundary and expands coordinates
into the existing fixed per-type schema before projection.

The fixed network schema and `token_type_schema_hash` remain the cross-substrate transfer
contract. Presence gates static context, so a hidden or absent token cannot leak declarations
through the separate context. Token-native feedforward and recurrent networks attach the static
context before their per-type projections. Universe-bound flat/dueling networks consume the same
compact dynamic serialization without a second observation pipeline. The full-payload-per-transition ABI is deleted. There is no dual
path, compatibility shim, legacy checkpoint loader or migration route; old artifacts fail loudly.

The 8× serialized-width cap is retired as an acceptance gate. It is replaced by the costs that
matter:

1. L1 dynamic replay width is at most 120 floats and contains no repeated immutable descriptor.
2. A 100,000-transition observation pair is at most 96,000,000 float32 bytes before allocator
   overhead.
3. Default batch size 256 remains viable and observation encoding remains below 25% of
   `env.step`.
4. Grid2D, Grid3D and aspatial universes keep one token-type schema and pass checkpoint-load,
   visibility and reconstructed-input parity tests.
5. Unit 4 runs against this ABI; token feedforward and recurrent configurations each reach the
   standing 79.19 IQM regression floor at equal environment steps before unit 5 is accepted.

## Sequencing

1. Fix `hamlet-6a4a6596bd` and `hamlet-1e335e0363`; both now block the token task explicitly.
2. Implement the compact dynamic ABI in `hamlet-fa6bb6da4a`, deleting the old representation.
3. Run unit 4 engineering acceptance on the compact ABI.
4. Migrate every shipped pack in unit 5. Do not spend training time on an ABI already selected
   for deletion.

If compact-flat state cannot preserve visibility or transfer while meeting the byte budget, stop
and choose one different token ABI (the previously captured typed-stream design is a candidate).
Do not retain both.

## Tracker reconciliation

The stale token umbrella was rewritten to this engineering scope and its expired claim released.
WS-7 (`hamlet-e3af412673`) was closed: determinism, oracle pinning, differential harness,
divergence register and first seam cut are delivered. Its remaining P3 CLI-hardening child
(`hamlet-1073af4d4e`) was reparented to the recovery milestone, so closure hides no work.
