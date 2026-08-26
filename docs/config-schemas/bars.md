---
title: bars.yaml — meter definitions, bounds and cascades
audience: config authors, engine developers
ai_summary: |
  Per-level meter schema. Every meter declares initial / depletion / recovery /
  bounds, and every field is REQUIRED — there are no defaults. `bounds.min` and
  `bounds.max` are enforced at six runtime sites AND supply the range for the
  observation's minmax normalization, so `bounds.max` above 1.0 is fully supported
  and is what makes an economy solvent.
reading_strategy: |
  Read "Bounds are load-bearing" first if you are changing a ceiling — it is the
  section with runtime consequences. The field tables are reference.
status: current as of 2026-08-12 (WS-1(e), PDR-0016)
---

# `bars.yaml`

One file per curriculum level, at `configs/<pack>/levels/<level>/bars.yaml`. It defines
the meters that level runs with and the cascades between them.

Every field below is **required**. The no-defaults principle applies in full: a missing
key is a compile error, not an implied zero.

```yaml
bars:
  version: "1.0"

  meters:
    - name: energy
      initial: 1.0
      depletion:
        passive: 0.01      # per tick
        move: 0.02         # per movement action
        interact: 0.05     # per INTERACT action
      recovery:
        natural: 0.0       # per tick
      bounds:
        min: 0.0
        max: 1.0
        lethal_min: true   # death on reaching min
        lethal_max: false  # death on reaching max

  cascades:
    - source: satiation
      target: energy
      threshold: 0.3       # fires while source < threshold
      strength: 0.006      # damage rate; 0.0 explicitly disables
```

## Fields

### `meters[]`

| field | type | meaning |
|---|---|---|
| `name` | str | Must match a meter declared in the pack's `environment.yaml` |
| `initial` | float | Starting value. Validated to lie within `bounds` — lower it whenever you lower `bounds.max` |
| `depletion.passive` | float | Drain per tick, applied **after** interactions within a step |
| `depletion.move` | float | Drain per movement action |
| `depletion.interact` | float | Drain per INTERACT action |
| `recovery.natural` | float | Recovery per tick (usually `0.0`) |
| `bounds.min` / `bounds.max` | float | Enforced floor and ceiling — see below. `max` must be `> min` |
| `bounds.lethal_min` / `lethal_max` | bool | Whether reaching that bound is a terminal condition |

### `cascades[]`

| field | type | meaning |
|---|---|---|
| `source` | str | Meter whose level triggers the cascade |
| `target` | str | Meter that takes the damage. **Must declare bounds** — the target's bounds become the compiled rule's clamp |
| `threshold` | float, `[0, 1]` | Fires while `source < threshold` |
| `strength` | float | Damage rate. `0.0` is an explicit disable, not a missing value |

A cascade may not target its own source.

## Bounds are load-bearing

`bounds.min`/`bounds.max` are enforced at **six** runtime sites:

1. `ActionExecutor` — after the movement debit
2. `ActionExecutor` — after the interaction debit
3. `AffordanceEngine.apply_instant_interaction`
4. `AffordanceEngine.apply_vtc_multi_tick_effects`
5. The compiled VTC **passive-depletion** program (the one that binds every tick, for every meter)
6. The compiled VTC **threshold-cascade** program (using the *target* meter's bounds)

and they additionally supply the range for the observation's declared `minmax`
normalization, so the value the network sees is `(value - bounds.min) / (bounds.max - bounds.min)`.

**`bounds.max` above 1.0 is supported and is the intended way to declare a resource
that is not a unit-interval need.** A currency meter with `bounds.max: 999999.0` holds
real amounts; before WS-1(e) six hardcoded `[0.0, 1.0]` clamps contradicted that
declaration every tick, which silently crushed every payout to `1.0` and made most
priced affordances permanently unaffordable.

### Consequences worth knowing before you change a ceiling

- **Passive depletion runs after interactions.** A meter capped at `0.5` with
  `passive: 0.01` reads back `0.49` at the end of the step it was topped up, not `0.5`.
- **`lethal_max` interacts with the ceiling.** Terminal conditions evaluate after passive
  depletion, so a lowered ceiling with `lethal_max: true` can kill the agent at the cap.
- **Changing any bound moves `transition_graph_hash`** (the clamp is part of the canonical
  transition rule) **and `observation_schema_hash`** (the normalization payload is part of
  the canonical observation entry), and therefore `vfs_hash`. That is correct and costs
  nothing pre-1.0 — recompile, do not add a compatibility branch.
- **A very large ceiling makes the meter numerically small in the observation.** At
  `bounds.max: 999999.0`, a value of `22.5` is observed as `2.25e-5` beside meters at
  ~`0.5`. The normalization is behaving as declared; a ceiling far above a meter's real
  operating range is an *authoring* problem, and the fix is to declare a truthful ceiling.

## Related

- `docs/config-schemas/variables.md` — VFS variables and their normalization specs
- `docs/config-schemas/drive_as_code.md` — reward configuration (`drive.yaml`)
- `PDR-0014`, `PDR-0015`, `PDR-0016` in `docs/product/decisions/`
