# HAMLET Reference Model Pack (runnable example)

This pack is a minimal, self-consistent v2.1.1 configuration intended for smoke testing and as a starting point. It mirrors the reference spec but with concrete values you can run through the compiler/CLI.

Layout:
- experiment.yaml (experiment metadata)
- stratum.yaml (world topology)
- environment.yaml (vocabulary)
- actions.yaml (action vocab)
- agent.yaml (defaults for drive/brain)
- levels/L0_demo/
  - curriculum.yaml (masking)
  - bars.yaml (meter behavior)
  - affordances.yaml (affordance behavior)
  - training.yaml (hyperparams)
  - items.yaml (appearance)
- items.yaml (catalog)
- vfs_profiles.yaml (global/agent/item profiles)
- effects.yaml (reusable effects)

How to validate:
```
uv run python -m townlet.compiler validate configs/reference/model_pack
```
