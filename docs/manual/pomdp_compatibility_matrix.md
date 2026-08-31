# POMDP token-visibility reference

Townlet implements partial observability by filtering typed spatial tokens. It does not build a
grid raster or local window. A level with `active_vision: partial` keeps the compiled `TokenSpec`
and flat observation width unchanged, then passes its normalized `vision_range` to the
substrate's `visible()` method for every observation tick.

## Compatibility matrix

| Substrate | Partial visibility | Radius conversion | Relative-position payload |
| --- | --- | --- | --- |
| Grid2D | Supported | `max(1, ceil(vision_range * longest_axis / 2))` cells | `egocentric_delta()` divided by `max(axis_size - 1, 1)` |
| Grid3D | Supported | Same discrete formula | Same discrete normalization |
| GridND | Supported | Same discrete formula for any supported rank | Same discrete normalization on every axis |
| Continuous 1D–3D | Supported | `vision_range * longest_extent / 2` world units | `egocentric_delta()` divided by each axis extent |
| ContinuousND | Supported | Same continuous formula | Same continuous normalization on every axis |
| Aspatial | Pass-all | No radius; every entity is visible | Width-zero deltas |

Every spatial substrate combines per-axis deltas with its declared distance metric. `wrap`
uses the toroidal shortest path; clamp, bounce and sticky use ordinary in-bounds deltas.

## Configuration

The stratum declares which vision modes its levels may select:

```yaml
stratum:
  version: "1.0"
  # substrate block omitted
  vision_support: both
  temporal_support: disabled
  observation_mode:
    mode: full_auto
```

The level selects partial visibility and supplies the required normalized range:

```yaml
curriculum:
  version: "1.0"
  active_vision: partial
  vision_range: 0.5
  active_temporal: false
  day_length: null
```

`stratum.vision_support` must admit `curriculum.active_vision`. The compiler reports
`VISION_INCOMPATIBLE` when the declarations disagree.

At runtime:

- Global visibility passes `None` to `visible()`, which admits every compiled entity slot that is
  otherwise present.
- Partial visibility passes `vision_range`. Publishers clear both presence and payload for each
  out-of-range spatial token.
- `egocentric_delta()` supplies bounded entity-minus-observer offsets using the same per-axis
  denominator as normalized absolute positions.
- The observer's `self` token remains present. Aspatial substrates expose no positional lanes.

## Network choice

Partial visibility does not impose a network type. `feedforward`, `dueling`, and `token_set`
consume one observation frame and carry no memory. Use the token-native recurrent architecture
when the policy must integrate information over time:

```yaml
architecture:
  type: recurrent
  recurrent:
    token_embed_dim: 128
    q_head_hidden_dim: 128
    aggregator:
      type: attention
      num_heads: 4
    lstm:
      hidden_size: 128
      num_layers: 1
      dropout: 0.0
```

`RecurrentTokenQNetwork` applies the shared token-set encoder to every frame, runs one LSTM call
over the pooled sequence, and applies its Q-head to every recurrent output. The `mean` aggregator
is also valid; it takes no `num_heads` key.

## Authoritative implementation surfaces

- Token schema and serialization: `src/townlet/universe/dto/token_spec.py`
- Token publishers: `src/townlet/environment/token_publishers.py`
- Substrate visibility contract: `src/townlet/substrate/base.py`
- Token-native networks: `src/townlet/agent/networks.py`
- Brain schema: `docs/config-schemas/brain.md`
- Stratum semantics: `docs/architecture/STRATA.md` §7
