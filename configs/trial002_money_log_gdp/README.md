# Trial 002 — money B: "a log float that models a GDP multiplied by through sin(time)"

The GDP half of the owner's Trial 002 scope example (`PDR-0047`). This live pack is forked from
`configs/simple`; its sibling is `configs/trial002_money_int_capped`.

## Current meter contract

`environment.yaml` is the sole authority for how a meter enters a token. The meter vocabulary is
exactly four bounded transformations:

- `minmax` with `clip: true`;
- `log_scaled` with `clip: true`;
- `cyclical_sin_cos` with a finite positive `period`; and
- `binary` with a finite `threshold`.

There are no aliases, translations or fallbacks for deleted kinds. Range-based members take their
minimum and maximum from the matching declaration in `levels/<level>/bars.yaml`; authors do not
repeat those bounds on a parallel observation field.

## What this pack declares

| File | Declaration |
|---|---|
| `environment.yaml` | `money.range_type: {kind: log_scaled, clip: true}` |
| `levels/L0_simple/bars.yaml` | `money` starts at `1000.0` with bounds `[1.0, 1000000.0]` |
| `effects.yaml` | `business_cycle` writes `1000 * (2 + sin(2πk/24))` from effect-local elapsed time |
| `levels/L0_simple/affordances.yaml` | interacting with `WORK` starts `business_cycle` |

`variables_reference.yaml` intentionally declares no variables. Its former `money` entry was a
dead parallel declaration: meter observation semantics come only from `meters[].range_type`.

## Working log-scaled observation

The runtime clamps money to its bars bounds and publishes
`log1p(money - 1) / log1p(999999)` in value lane 0. The second value lane stays zero.

| money | observed |
|---:|---:|
| 1 | 0.000000 |
| 10 | 0.166667 |
| 1,000 | 0.500000 |
| 100,000 | 0.833333 |
| 1,000,000 | 1.000000 |

The compiled per-level meter signature records `log_scaled`, and recursive affordance target
signatures inherit that identity. Changing this declaration to another admitted kind changes the
network-visible semantic identity without changing the fixed token width.

The original Trial 002 finding was historical: the time-based dynamic was authorable, while an
earlier compiler silently substituted minmax observation. The current pack keeps the same dynamic
and now executes the authored log-scaled observation directly.
