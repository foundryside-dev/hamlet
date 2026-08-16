# Trial 002 — money B: "a log float that models a GDP multiplied by through sin(time)"

The other half of the owner's Trial 002 scope example (`PDR-0047`). Forked from `configs/simple`
at `07b26ed5`; sibling pack is `configs/trial002_money_int_capped`.

| file | change |
|---|---|
| `environment.yaml` | `money.range_type: normalized` → **`unbounded`** |
| `levels/L0_simple/bars.yaml` | `money` `initial 0.5` → `1000.0`, `bounds [0.0, 1.0]` → **`[1.0, 1000000.0]`** |
| `variables_reference.yaml` | **new** — declares `money` observable with `normalization.kind: log_scaled`, `min 1.0`, `max 1e6` |
| `effects.yaml` | **new effect `business_cycle`** — `on_tick: modify bar.money = 1000.0 * (2.0 + phase_sin(elapsed_ticks, 24.0))` |
| `levels/L0_simple/affordances.yaml` | `WORK.interactions.on_start` gains `spawn_effect: business_cycle` |

## Result — measured 2026-08-15, recorded in `PDR-0051`

**The dynamic is fully authorable. The log scaling is not.**

### ✅ The sin(time) dynamic works, end to end, in config

`PDR-0047` predicted this would fail on "the absent bar-level expression binding." **That
prediction is falsified.** The binding exists — not on the bar, but through
`effects.yaml` → affordance `interactions`. After one INTERACT with WORK, money traces
`1000·(2 + sin(2πk/24))` for 27 consecutive ticks, matching the closed form exactly at every
tick:

```
2000.0 2258.8 2500.0 2707.1 2866.0 2965.9 3000.0 2965.9 2866.0 2707.1 2500.0 2258.8
2000.0 1741.2 1500.0 1292.9 1134.0 1034.1 1000.0 1034.1 1134.0 1292.9 1500.0 1741.2 ...
```

Two real constraints found on the way, both surfaced by *honest, listing* compiler errors:

1. **No world clock in the effect expression scope.** `tick` is not a variable; the available
   set is `intensity`, `elapsed_ticks`, `duration_remaining`, and the `bar.*` / `vfs.*` paths.
   `elapsed_ticks` is effect-lifetime-local and substitutes acceptably here only because the
   effect is long-lived.
2. **No episode-start hook.** `EffectManager.spawn_effect` has exactly one production caller
   (`effects/executor.py:228`), inside effect execution itself — so an effect can only be
   spawned by another effect or by an affordance interaction. A world process that should simply
   *be running* has to be bootstrapped by an agent walking onto a tile.

### ❌ The log scaling is declared, accepted, and silently discarded

`variables_reference.yaml` declares `money` with `normalization.kind: log_scaled`. It validates,
the pack compiles green, and the compiled observation contains **only `minmax`** — no
`log_scaled` anywhere, and no standalone `money` field at all. What the agent actually sees:

| money | observed | minmax predicts | log_scaled would give |
|---:|---:|---:|---:|
| 1 | 0.000000 | 0.000000 | 0.000000 |
| 10 | 0.000009 | 0.000009 | 0.166667 |
| 1,000 | 0.000999 | 0.000999 | 0.500000 |
| 100,000 | 0.099999 | 0.099999 | 0.833333 |
| 1,000,000 | 1.000000 | 1.000000 | 1.000000 |

Linear to six decimal places. The entire operating range 1 → 100,000 is crushed into
`[0, 0.0999]` — the agent is effectively blind to money, which is the exact failure log scaling
exists to prevent.

**The cause is structural, not a missing capability.** All ten `vfs.md` §9.2 normalisation kinds
are implemented in `vfs/observation_builder.py`. But
`universe/compilers/observation.py::_meter_normalization` returns **one**
`NormalizationSpec(kind="minmax", …)` for the *entire meter block*, chosen by the compiler from
declared bounds. No meter can carry a per-meter kind, so eight of the ten kinds are unreachable
for bars no matter what any pack declares. A meter also cannot declare normalization directly —
`environment.yaml` `meters[]` is `extra="forbid"` and rejects the key outright.

### 🐛 Bug found incidentally: effects survive `reset()`

`env.reset()` correctly restores `money` to its declared `initial` (1000.0), but the
`business_cycle` effect keeps ticking across the episode boundary with `elapsed_ticks`
continuing — one WAIT after a reset yields `2258.8`, i.e. tick 1 of the *previous* episode's
cycle. Episode state leaks into the next episode.
