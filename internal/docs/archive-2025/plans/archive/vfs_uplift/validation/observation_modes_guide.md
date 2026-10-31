# Observation Modes Guide (full_auto | max_compact | full_manual)

## Overview
- `observation_mode` lives in `stratum.yaml` under `stratum.observation_mode`.
- Modes control which observation fields are emitted (and therefore obs_dim).
- Defaults to `full_auto` if omitted.

## Modes
- `full_auto`: include all configured observation fields. Masked fields remain allocated to keep dims stable.
- `max_compact`: drop masked/inactive fields to minimize obs_dim. Different strata may produce different obs_dim depending on masking.
- `full_manual`: include only the explicit `include_fields` list. Fails fast if the list is empty or contains unknown field names.

## Usage
```yaml
stratum:
  observation_mode:
    mode: full_auto  # or max_compact, full_manual
    # include_fields: ["obs_grid_encoding", "obs_meters"]  # required when mode=full_manual
```

## Guidance
- Choose `full_auto` when you want shape stability across curricula and levels.
- Choose `max_compact` when minimizing obs_dim matters more than shape stability (e.g., ablations or tight models).
- Choose `full_manual` when you need strict control over layout; list every field to keep.

## Validation
- `full_manual` requires a non-empty `include_fields` list; unknown names raise errors at compile time.
- `max_compact` removes any field whose description contains `MASKED` (compiler-produced masks).

## References
- Config reference examples: `configs/reference/config-complete.yaml` and `configs/reference/model_pack/stratum.yaml`.
- Tests: `tests/test_townlet/unit/universe/test_observation_modes.py`, `tests/test_townlet/integration/test_observation_modes_integration.py`.
