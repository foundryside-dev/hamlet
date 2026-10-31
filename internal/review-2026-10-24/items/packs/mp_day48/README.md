# HAMLET Reference Model Pack (runnable example)

This is a runnable reference pack for the current compiler. Its canonical `variables` declaration replaces the historical profile language in `../config-complete.yaml`; that dated design sketch is not a supported schema. Filenames below are transport conventions.

Layout:

- experiment.yaml (experiment metadata)
- stratum.yaml (world topology)
- environment.yaml (vocabulary)
- actions.yaml (action vocab)
- brain.yaml (brain configuration)
- levels/L0_demo/
  - curriculum.yaml (masking)
  - bars.yaml (meter behavior)
  - affordances.yaml (affordance behavior)
  - drive.yaml (reward function)
  - training.yaml (hyperparams)
  - items.yaml (appearance)
- items.yaml (catalog)
- variables.yaml (canonical global/agent/item declarations and item schema catalog)
- effects.yaml (reusable effects)

How to validate:

```
uv run python -m townlet.universe validate configs/reference/model_pack --primary-level L0_demo
```
