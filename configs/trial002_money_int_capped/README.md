# Trial 002 — money A: "an int between 1 and 100, capped for an individual"

The capped-money half of the owner's Trial 002 scope example (`PDR-0047`). This live pack is forked
from `configs/simple`; its sibling is `configs/trial002_money_log_gdp`.

## Current meter contract

`environment.yaml` is the sole authority for how a meter enters a token. The meter vocabulary is
exactly four bounded transformations:

- `minmax` with `clip: true`;
- `log_scaled` with `clip: true`;
- `cyclical_sin_cos` with a finite positive `period`; and
- `binary` with a finite `threshold`.

There are no aliases, translations or fallbacks for deleted kinds. In particular, `integer` is not
a current member. Meter state remains float32; `range_type` controls bounded observation semantics,
not numeric storage type.

## What this pack declares

| File | Declaration |
|---|---|
| `environment.yaml` | `money.range_type: {kind: minmax, clip: true}` |
| `levels/L0_simple/bars.yaml` | `money` starts at `10.0` with enforced bounds `[1.0, 100.0]` |

The bars bounds cap the live meter state. The same bounds parameterize the token normalizer, so
value lane 0 publishes `(money - 1) / 99` after clamping and value lane 1 stays zero:

| money | observed |
|---:|---:|
| 1 | 0.000000 |
| 10 | 0.090909 |
| 100 | 1.000000 |

The compiled per-level meter signature records `minmax`. Changing this declaration to another
admitted kind changes the network-visible semantic identity without changing the fixed token width.

The original Trial 002 finding was historical: the old `integer` literal validated but did not
affect runtime or observation. The current pack deletes that inert surface and states the behavior
it actually supports: bounded float state with a working clipped minmax observation.
