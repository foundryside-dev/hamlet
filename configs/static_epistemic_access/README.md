# Static epistemic access witness

Compile with primary level `L0_simple`. `ADVANCE` increases public state and the
engine-only `hidden_score`; `WAIT` leaves both unchanged. Extrinsic reward reads
`hidden_score` by its declared name and multiplies it by 0.5. The global
`immutable_scale` and agent-scoped `readable_unexposed` are runtime-immutable literals.

Only `public_state` has a variable-element observation binding. Engine-only state
refuses agent accessor reads. Agent-readable state does not acquire a binding until
explicitly exposed. Rewards can reveal information about hidden state; this is no
information-theoretic secrecy claim.

The integration witness runs two independent agent rows and two resets from both
cold and MessagePack-loaded artifacts. This pack has no items. Separate qualified
item probes allocate controlled instances and explicitly exclude initial item
appearance cache fidelity, held-item observations, ownership and spatial privacy.
This is a correctness witness, not a learning or convergence qualification.
