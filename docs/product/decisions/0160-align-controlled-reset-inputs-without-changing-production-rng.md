# PDR-0160 — Align controlled reset inputs without changing production RNG

Date: 2026-10-02 Australia/Canberra. Status: **accepted — comparison-fixture amendment**.
Owner instruction: implement the reviewed episode-lane plan and obtain Astra's
implementation review. Related: PRD-0005, PDR-0158/0159, execution
`hamlet-78ad37dd49`, engine bug `hamlet-d6fc84d147`.

## Observed dependency

The original eight learned nine-episode attribution recipes are retained under
`runs/episode-lanes/2026-10-02/implementation/causal/population-numerics/`.
The `parent-reference`, `E2-reference`, `E3-reference` and `P1-reference` banks
use the same instrument, effective YAML and source-resolved imports. Their
standard-replay recipes fail the registered exact observation invariant at the
second episode: each Double-DQN variant changes 80 predecessor and 80 successor
observation hashes at E3→P1. PER and recurrent world-input identities remain exact.
These original standard banks are **unqualified**, even when numerical totals
reconcile. They must not be relabelled, removed or replaced.

`ReplayBuffer.sample` consumes `torch.randperm(self.size)` on the global Torch
RNG. Eligible admission changes sampled buffer sizes from `[2,4,6,8,10]` to
`[2,4,5,6,7]`. The environment's ordinary affordance reset also consumes the
global Torch RNG. The retained real countercontrol observes equal states through
tick two and unequal states beginning at the original tick-three sampler. A
natural subsequent reset produces different agent/affordance positions and
observations; meters remain equal. Restoring only the parent's post-episode
Torch RNG before the candidate's real reset makes positions, observations,
affordances and meters equal. The real PER sampler leaves Torch RNG unchanged,
and its natural reset agrees. Source anchors and exact countercontrol values are
retained in `causal/attribution-review*.json`.

This establishes shared-RNG coupling, not a production RNG-isolation repair.
Accepting arbitrary observation/shaping changes as an episode accounting
allowance would violate the plan's controlled-world comparison contract.

## Bounded decision

Add a second, explicitly controlled numerical recipe family before producing
its parent or candidate bank. Preserve the original family as failed dependency
evidence. All eight architectures/replay/Double-DQN combinations, nine episodes,
authored actions, effective YAML, actual learner and predictor updates, sample
identity and independent normalization/composition/target checks remain required.

The new external instrument controls only the randomness supplied to ordinary
episode resets one through eight:

```python
before_reset_rng = torch.get_rng_state().clone()
with torch.random.fork_rng(devices=[]):
    torch.default_generator.manual_seed(42 + episode)
    population.reset()
assert torch.equal(torch.get_rng_state(), before_reset_rng)
```

Episode zero retains the original seed-42 construction. The original real reset
executes; no position, observation, meter, action, reward, replay, learner or
predictor producer is replaced. Record reset seed, before/after RNG digests,
positions, affordance layout, meters and observations. Assert the caller's CPU Torch RNG
state is restored exactly and reset inputs agree across every compared source.
This is a CPU Torch comparison-fixture control, not an authored promise of RNG
isolation. The CPU generator alone is seeded and restored; no CUDA or other
random-generator state is touched or qualified by this control.

Run the same new instrument against the preserved clean parent, E2, E3, P1 and
the final candidate. Bind every changed numerical coordinate to its actual
causal source commit, and retain exact unchanged actions/world clocks/sticky
dones/predecessors/successors/meters/config inventories. Independent eligible-row
RMS and DAC composition, real sample/target evidence and all original acceptance
criteria still apply. A changed world input, missing/phantom sample, unexplained
numeric delta or failed control refuses qualification; there is no field-wide
exception. Preserve all earlier manifests and banks unchanged.

No production RNG, reset policy, replay warmup, optimizer schedule, artifact or
frozen-oracle input changes enter this amendment. Existing recurrent warmup
policy remains source-identical; fewer eligible stored sequences may change
the number of actual updates without changing that policy. Production RNG
isolation remains separate work. No convergence or recovery-exit claim follows.

## Review and handoff

The Astra scoped verdict is retained before creating the new bank. The
[prospective instrument registration](../evidence/episode-lanes/controlled-reset-registration.md)
freezes instrument SHA256
`f166e8f48165c46da4fba5413839b9a001e22a2da5abd04b31a6904f29eb6d77`
and recipe registration SHA256
`799ec391e1eb38c53b4e6c1c12bc0837e1131f1c5c0b3d10659c40e1f6c52d1f`
before any amended-family capture. Implementation acceptance remains
pending the complete candidate, all gates and the requested final Astra review
against PRD criteria one through eight. This decision accepts only the explicit
comparison-fixture amendment; it supplies no runtime or product acceptance.
The independent [Astra scoped review](../evidence/episode-lanes/controlled-reset-review.md)
approves this CPU-only comparison control with no blockers. Its requested CPU
clarification is incorporated below by seeding only `torch.default_generator`.
The original failed banks remain unqualified; the new bank and final candidate
are not accepted by that prospective review.
