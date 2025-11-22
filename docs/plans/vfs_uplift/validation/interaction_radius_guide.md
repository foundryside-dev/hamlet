# Interaction Radius Guide (Continuous Substrates)

**Scope:** Continuous and ContinuousND substrates only. Grid and Aspatial substrates do **not** use `interaction_radius`.

## What Is `interaction_radius`?

- Required scalar distance threshold that gates all proximity-based interactions on continuous substrates (affordances, items, custom verbs).
- Units match the substrate’s coordinate system (e.g., meters in `continuous`, arbitrary units in `continuousnd`).
- There are **no defaults**: configs must set it explicitly (compiler hard-errors otherwise).

## Configuration

Set the value in `stratum.yaml` under the substrate block:

```yaml
stratum:
  version: "1.0"
  substrate:
    type: continuous
    continuous:
      width: 10.0
      height: 10.0
      movement_delta: 0.5
      interaction_radius: 1.0  # REQUIRED for continuous substrates
```

For N-dimensional substrates:

```yaml
stratum:
  substrate:
    type: continuousnd
    continuousnd:
      dimension_sizes: [10.0, 6.0, 4.0]
      movement_delta: 0.5
      interaction_radius: 0.8  # REQUIRED
```

## Validation Rules

- Must be **positive** (`gt 0`).
- Must be **≤ each dimension’s range**; oversized radii are rejected.
- Compiler enforces presence for continuous/continuousnd; missing values fail early.
- Substrate emits a **warning** if `interaction_radius < movement_delta` (too small to reach neighbors per step).

## Usage Semantics

- Interaction succeeds when `distance <= interaction_radius` (Euclidean by default for continuous; metric defined by substrate).
- Applies to affordance use, item pickup/drop, and local custom verbs on continuous substrates.
- No effect on grid/aspatial substrates (tile/slot based).

## Recommendations

- Start with `interaction_radius == movement_delta` for symmetric step-and-interact behavior.
- Increase slightly (e.g., `movement_delta * 1.2`) if agents frequently “just miss” interactions due to float positioning.
- Keep well below the smallest dimension size to avoid all-encompassing proximity.
