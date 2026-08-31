# PDR-0136 — Compact token transport preserves dynamic effect identity

Date: 2026-08-31   Status: **accepted** (milestone 3 engineering checkpoint)
Author: Codex (standing product owner)
Clarifies and implements: `PDR-0131`
Related: `PDR-0132`, `PDR-0134`, `PDR-0135`, `hamlet-1b1caf552a`

## Context

`PDR-0131` ruled that replay should store changing state, not repeat immutable compiled
descriptors in every transition. The engineering question was where that boundary actually lies.
The earlier 118-float reading was a design target for the then-anticipated addition of one scalar;
it was not a current census. The compiled roster now shows that L1 needs 115 compact floats while
retaining a 4,090-float fixed projection boundary.

Most token identity is immutable compiled context: slot bindings, position/rank descriptors,
meter normalization, variable identity and affordance behaviour. Effect slots are different. A
scope-budget slot can hold a different effect definition in each world, so the live
`context_index` is transport metadata rather than static slot identity.

## The call

`TokenSpec.total_dims` is the sole environment, transition and replay ABI. The environment
allocates the compact tensor first and publishers write only dynamic lanes. There is no complete
fixed-observation encoder, reconstruction callable, compression pass or compatibility reader.

The fixed projection schema remains the model-transfer boundary. `TokenInputAssembler` expands
one named token type at a time inside `TokenSetQNetwork`, attaches compiler-owned context, projects
those rows immediately and releases them before the next type. Flat, dueling, RND and the current
recurrent reader consume compact observations directly.

Variable coordinates and rank descriptors are compiled immutable element context. Effect
`context_index` remains a compact dynamic lane because the effect occupying a slot varies by
world. Present selectors must be exact, finite float32 integers in catalog range; absent rows are
zero and do not consult the selector.

The current widths are:

| substrate | rank | compact ABI | fixed projection |
| --- | ---: | ---: | ---: |
| Grid2D / L1 | 2 | 115 | 4,090 |
| Grid3D | 3 | 149 | 4,090 |
| aspatial | 0 | 19 | 394 |

The three ranks share `token_type_schema_hash`; their rank-specific layouts have distinct
`layout_hash` values. Aspatial is true rank zero: it does not invent a coordinate lane.

At replay capacity 100,000, the L1 observation and next-observation pair is exactly
92,000,000 bytes (`torch.float32`). The former 118 target would be 94,400,000 bytes; it remains a
valid budget example, not the current census.

## Artifact cut

This is a one-way pre-release cut:

- compiled artifact: `1.26`;
- projected token schema: `token-1.1`;
- compact transport: `compact-1`;
- outer checkpoint: `5`;
- population checkpoint: `4`;
- standard and prioritized replay: `4`; and
- sequential replay: `5`.

Each reader requires the exact integer version, exact kind and exact current key/schema. Previous
artifacts fail before live state mutates. Replay restore validates once, materializes one candidate
and installs it only after complete population/network/optimizer/scheduler/exploration validation.
There is no migration, old-key reader or dual format.

The dead public `set_encoder` architecture and `SetEncoderQNetwork` are deleted. `token_set` is
the only set architecture. The serializer that omitted absent `token_set` solely to preserve old
`brain_hash` values is also deleted; exact current dumps use the exact current field set.

## Acceptance

Milestone 3 is accepted on pushed implementation `project-recovery-3@d554fb7f`:

1. Grid2D, Grid3D and aspatial compile, artifact-round-trip, reset/step and reconstruct each type
   exactly at the projection boundary, with visibility/presence pinned.
2. Feedforward, dueling, token-set mean, token-set attention and RND update at batch 256. The
   current recurrent reader performs a real four-step batch-256 BPTT update and changes LSTM
   parameters.
3. Standard, prioritized and sequential replay round-trip the compact ABI and refuse their
   immediately previous versions.
4. A runtime/AST guard proves there is no complete fixed-observation API or 4,090-wide allocation.
5. The default suite passes 3,824 tests with 11 skips and 84% coverage. Ruff, Black, mypy,
   no-defaults, compiler-pack validation and diff integrity are green.
6. Two fresh processes on the exact clean pushed SHA measured encoding ratios
   `0.1618647585026199` and `0.16272129673268468`; the accepted maximum is
   `0.16272129673268468`, below the `0.25` limit.

## Consequences

`PDR-0126` remains superseded by `PDR-0131`: the 9.43x result was a replay-layout defect, not debt
to carry into pack migration. This decision clarifies the current census as 115, while preserving
118 as the one-scalar target used in the earlier constraint analysis.

Milestone 3 proves compact transport, batch-256 plumbing and current recurrent BPTT mechanics. It
does not claim the token-native recurrent replacement or the 79.19 IQM equal-step regression.
Those remain milestone 4 (`hamlet-25fc3fb955`). Pack migration remains milestone 5
(`hamlet-55b2826a02`).
