# Vision

This page says what Townlet is for, who it serves, what it deliberately refuses to be, and what
has been demonstrated so far. It condenses the project's product record as of October 2026; the
full decision history is in git.

## From playing a game to writing one

Townlet started as a teaching tool: let students learn graduate-level reinforcement learning by
playing something that felt like The Sims. Its purpose has since moved one level up. **The
interesting activity is no longer playing the simulation but authoring it.**

Townlet is a deep-RL substrate expressed as configuration. The whole universe (variables, observations,
spatial topology, affordances, effects, items, rewards and curriculum) is declared in YAML,
compiled into a frozen, content-addressed `CompiledUniverse`, and executed on PyTorch tensors
(on a GPU when one is available).
Someone with an idea for a game mechanic should be able to turn it into a running, trainable and
reproducible environment by writing config: no environment subclass, no observation-tensor
plumbing, no reward-function code.

Each major subsystem exists to move one category of "you must write Python for this" into "you
can declare this":

| Subsystem | What becomes declarable |
| --- | --- |
| Universe compiler | Discovery, validation and compilation of a whole config pack |
| VFS (variable and feature system) | Typed state, scopes, access policies and observation exposure |
| VTC (transition compiler) | Action writes, passive dynamics, cascades and terminal conditions |
| DAC (drive as code) | Reward functions: extrinsic, intrinsic, shaping and modifiers |
| Strata | Spatial topology, from aspatial worlds to eight-dimensional grids |
| BAC (brain as code) | Network architecture, optimizer, loss, replay and Q-learning variant |

The longer arc has three steps. First the world is config (largely shipped). Then the agent's
mind is config too: today that covers network and training choices, while cognitive topology and
think-loop execution graphs remain design only. Finally, world and mind pass through one compiler
into one content-addressed artifact.

## The demonstration world

`configs/default_curriculum`, the survival "town", is the first-class demonstration of the
substrate, not its limit. It has to make two claims at once:

1. **Power:** this is an impressive thing you can build.
2. **Generality:** you could equally build anything else.

Those pull against each other. A demo that impresses because it was special-cased destroys the
second claim. So the demo is bound by a **dogfooding rule**: it must be authored through the
same door as any user, in config, through the standard compiler, with no privileged Python path.
Any place it needs Python that an outside author could not use is an authorability gap, and the
most telling kind.

## Who it serves

- **The researcher-builder** who runs their own experiments on it. Trustworthiness and fast
  iteration come first.
- **The prototyping modeller:** anyone working on game development, simulation or abstract
  models of the real world who wants a trained agent for their own system. They author a
  simplified scenario, train against it, and leave with a model plus an interface contract. The
  contract is the declared variables and actions, not the substrate, so a policy trained on a
  coarse world can be dropped into a higher-fidelity one that exposes the same telemetry. A
  model-export path does not exist yet and is the main gap for this user.
- **The novice author,** someone with a mechanic idea and no RL engineering background. They are
  the standard the framework is judged by rather than a current user. Every barrier that needs
  Python is a defect against them.
- **Students and instructors,** now as authors rather than players.

It is **not** for teams that want a production RL training platform, an agent-serving runtime or
a Gym-compatible environment zoo. Townlet favours expressiveness, authorability and provenance
over generality and API stability.

## What it refuses to be

- **Backwards compatible before 1.0.** Old configs and checkpoints fail loudly. A compatibility
  shim is a defect.
- **A carrier of technical debt, including in "experimental" RL code.** Failing gates, accepted
  but inert config, computed but unused outputs and known-wrong docs are all debt. Something that
  simply has not been built yet is not.
- **A producer of production-ready agents.** The goal is understanding, not benchmark scores.
- **A bug-fixer of interesting failures.** Reward hacking and pathological emergent strategies
  are preserved and documented as [teachable moments](teachable_moments/).
- **Implicitly defaulted.** Every behavioural parameter is explicit, because hidden defaults make
  universes irreproducible.
- **Domain-aware in the runtime.** The engine never branches on what a variable means or is
  called. Domain meaning lives in compiled artifacts.

## What has been demonstrated

**Changing the world's dimensionality is a config edit.** In August 2026 the survival world was
moved onto a six-dimensional grid by changing about six lines of `stratum.yaml` (`grid` to
`gridnd`, `dimension_sizes: [4, 4, 4, 4, 4, 4]`) and no source code. It compiled, reset and
stepped; the movement actions expanded automatically to twelve (`DIM0_NEG` to `DIM5_POS`); and
every meter, affordance, item, effect and reward carried over unchanged. Partial observability on
N-dimensional grids was not supported at the time, so the partially observable levels had to be
switched to full vision. This is one hand-run witness of one axis, not a measured authoring
success rate.

**The token observation transfers across worlds.** Observations are typed tokens with a fixed
per-type schema. Measured on 2026-10-31, all 33 compilable shipped levels (2-D and 3-D grids,
N-dimensional grids, continuous and aspatial worlds) share one token type schema hash,
`de093a6e9f59924e`, while the flat observation width ranges from 19 to 474. Transfer is a
property of the type schema rather than of a fixed width.

**Token networks match the earlier raster baseline.** A frozen L2 (partial observability)
baseline trained on the old raster observation reached a seed-level IQM of 98.99 mean greedy
survival steps across five seeds. In September 2026 all four token architectures cleared the
80% acceptance floor (79.19) at the same environment-step budget, seed 45:

| Architecture | Aggregator | Mean greedy survival | Parameters |
| --- | --- | --- | --- |
| Token feedforward | mean | 98.99 | 62,095 |
| Token feedforward | attention | 99.00 | 128,143 |
| Token recurrent | mean | 97.32 | 194,191 |
| Token recurrent | attention | 99.00 | 260,239 |

This is an engineering regression gate, not a multi-seed convergence study of the current
default scenarios. That study has not been done.

## Known gaps

- **Brain as code** beyond network and training choices: cognitive topology, goals and
  think-loop graphs.
- **Model export** for the prototyping modeller.
- **A second, genuinely different world** authored entirely in config, to test the generality
  claim along the domain axis as well as the spatial one.
- **The intended curriculum.** The five shipped levels are three distinct universes, and the
  "low energy delirium" lesson they were meant to teach is not yet implemented. See
  [teachable moments](teachable_moments/low_energy_delerium.md).
- **A measured authoring rate:** a fixed corpus of mechanic ideas, each attempted in config
  only, with `git diff --stat src/townlet/` checked afterwards.
