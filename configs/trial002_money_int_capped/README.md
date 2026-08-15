# Trial 002 — money A: "an int between 1 and 100, capped for an individual"

One half of the owner's Trial 002 scope example (`PDR-0047`):

> *"Money might be an int between 1 and 100 capped for an individual, or it might be a log float
> that models a GDP multiplied by through sin(time)."*

Forked from `configs/simple` at `07b26ed5`. **Only `money` differs from that pack**, so any
behavioural difference is attributable to the money declaration alone.

| file | change |
|---|---|
| `environment.yaml` | `money.range_type: normalized` → **`integer`** |
| `levels/L0_simple/bars.yaml` | `money` `initial 0.5` → `10.0`, `bounds` `[0.0, 1.0]` → **`[1.0, 100.0]`** |

Nothing else in the pack is touched. The sibling pack is `configs/trial002_money_log_gdp`.

## Result — measured 2026-08-15, recorded in `PDR-0051`

**The domain is authorable. The type is not.**

- ✅ Compiles. `bounds [1.0, 100.0]` reach the observation normalizer as
  `minmax min=1.0 max=100.0`, and the cap is enforced at runtime: writing `500.0` / `-20.0`
  clamps to `100.0` / `1.0` within three ticks.
- ❌ **`range_type: integer` is completely inert.** Switching every meter in the pack from
  `normalized` to `integer` and changing nothing else leaves **all five provenance hashes
  byte-identical** (`observation_schema_hash`, `vfs_hash`, `variable_schema_hash`,
  `transition_graph_hash`, `action_schema_hash`) and `total_dims` unchanged at 108. The literal
  string `integer` survives in exactly one place in the compiled universe —
  `u.environment.environment.meters[2].range_type`, the echoed raw config — and in no derived
  artifact.
- ❌ **The runtime stores floats regardless.** `vectorized_env.py:335` allocates
  `self.meters` as `torch.float32` unconditionally, with no branch on `range_type`. A bar
  declared `integer` holds `33.33300018310547` across three ticks without complaint.

The DTO says so itself — `config/environment_config.py:27`:
*"Metadata only for UI; does not affect obs_dim."*

**This is a declared-accepted-inert failure, not a rejection.** The pack goes green while the
author's declaration does nothing. See `hamlet-365e996511`.

## Reproduce

```bash
UV_CACHE_DIR=.uv-cache PYTHONPATH=$(pwd)/src uv run python -c "
from pathlib import Path
from townlet.universe.compiler import UniverseCompiler
c = UniverseCompiler()
u = c.compile(Path('configs/trial002_money_int_capped'), primary_level='L0_simple')
print([f.normalization for f in u.vfs_observation_fields if f.id == 'obs_meters'])
"
```
