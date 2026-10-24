# Presentation Configuration (`presentation` declaration)

---
## AI-Friendly Frontmatter

**Purpose**: How an observer (the live-inference frontend) *shows* a universe — labels, value
formats, colours, affordance icons — declared by the pack, optional, observer-only.

**When to Read**: Building a showcase / "locked" pack that should render prettified stats;
changing how the frontend renders meters or affordances; wondering why the frontend no longer
shows `$` for a meter called `money`.

**AI-Friendly Summary**:
The `presentation` declaration is **optional** and **observer-only**. The universe compiler
discovers it by content like every other pack-scope family (the filename is transport —
`presentation.yaml` is a convention, `display.yaml` works the same), resolves its meter and
affordance references in stage 5, and carries the parsed `PresentationConfig` on the artifact as
`CompiledUniverse.presentation`. The live-inference server reads it from the artifact and forwards
it on the `connected` message. It enters no semantic hash — presentation cannot change
observations, rewards, transitions, or checkpoint compatibility. **Absent is the honest
default**: every meter renders from its declared `bars.yaml` bounds, uniformly (bar = fraction of
the declared range, value shown plainly, "critical" = within 20% of a declared lethal bound,
relationships drawn from declared cascades). No site — compiler, server or frontend — may infer
presentation from a variable's or affordance's name. An entry for a meter or affordance the pack
does not declare is a located compile refusal (`[UAC-RES-PRESENTATION] file:line`), not an
ignored key.

**Reading Strategy**:
- **Quick**: "Schema" below is the whole surface — three format kinds, two entry types.
- **Why it is shaped this way**: `docs/product/decisions/0025-*.md` (declared, not deleted;
  honest by default) and `0023-*.md` (money units are nominal).

**Related Documents**:
- `docs/config-schemas/bars.md` — where a meter's bounds and lethality are declared (the honest
  default renders from these).
- `src/townlet/config/presentation_config.py` — the DTO.
- `src/townlet/universe/compiler.py` (`_resolve_presentation`) — the stage 5 reference check.
- `src/townlet/demo/presentation.py` — the meter-metadata and presentation payloads.
- `frontend/src/utils/formatting.js` — the honest rendering rules on the consumer side.

---

**Status**: In production (live-inference server + frontend), 2026-08-17.
**Version**: 1.0

---

## Overview

The product's rule for the presentation layer (owner-ruled, `PDR-0025`):

1. **Default: honest.** Every meter renders from its declared range, uniformly. A meter called
   `money` is a normalised variable like every other meter and is shown as one.
2. **Opt-in: declared.** A pack may declare how a variable is presented. A showcase pack turns
   currency formatting on deliberately; the curriculum packs do not.
3. **Never: inferred.** Neither the server nor the frontend decides a variable is money because
   it is *named* `money`. That would be the presentation layer knowing what the game is.

The `presentation` declaration is the declared surface for rule 2. It is **observer-only by design**: the
frontend may read a declared format, but the *engine* must stay unaware. If a presentation
setting ever needed to affect observations, rewards or transitions, it would be in the wrong
layer (that is `PDR-0025`'s reversal trigger).

## Where it lives, who reads it

```
configs/<pack>/
├── stratum.yaml, environment.yaml, ...   # compiled by the universe compiler
├── presentation.yaml                     # OPTIONAL observer settings; discovered by content
└── levels/<level>/bars.yaml              # declares bounds + lethality the honest default uses
```

- Discovered by the universe compiler as the pack-scope `presentation` family: a document whose
  top level is `version` with `meters` and `affordances` mappings, in any `.yaml`/`.yml` under
  the pack root (see [declaration discovery](declarations.md)). The filename is transport.
- Validated in two places, both at compile time: `PresentationConfig` at parse (stage 1), and
  the meter / affordance references against the pack's `environment` declaration in stage 5
  (`[UAC-RES-PRESENTATION]`).
- Carried on the artifact as `CompiledUniverse.presentation` (`None` when absent) and
  serialized with it (artifact schema 1.34). It enters **no** semantic hash: compiling a pack with
  and without the declaration retains identical `environment_hash`, `items_hash`, `brain_hash`,
  `bars_hash`, `affordances_hash`, `vfs_hash`, `observation_schema_hash`, `action_schema_hash`,
  `transition_graph_hash` and `drive_hash` (`tests/test_townlet/unit/demo/test_presentation.py`),
  and no checkpoint gate compares it. The compiler's *cache key* hashes every discovered
  document, so adding the declaration invalidates a compile cache — a transport-cache effect, not
  an execution-semantic change.
- Read by the live-inference server from the compiled universe it already holds
  (`LiveInferenceServer._build_observer_metadata`, `_affordance_icon`); nothing re-opens a file.
- Forwarded to the frontend on the `connected` message as `presentation` (or `null`), next to
  `meters` (declared bounds/lethality/cascades per meter, compiled order — see "Payload").

## Schema

```yaml
version: "1.0"                       # required, pinned

meters:                              # required (may be {}), keyed by meter name
  money:
    label: Money                     # display label
    format:                          # exactly one of the three kinds
      kind: currency                 # plain | percent | currency
      symbol: "$"                    # currency ONLY (forbidden on the other kinds)
      decimals: 0                    # all kinds, ≥ 0
    color: "#fbbf24"                 # CSS colour for the meter's bar

affordances:                         # required (may be {}), keyed by affordance name
  EAT:
    label: Eat
    icon: "🍽️"                       # glyph rendered for the affordance
```

**Field rules**

| field | type | notes |
|---|---|---|
| `version` | `"1.0"` | required |
| `meters.<name>` | entry | `<name>` must be a meter the compiled universe declares |
| `meters.<name>.label` | non-empty string | required |
| `meters.<name>.format.kind` | `plain` / `percent` / `currency` | required |
| `meters.<name>.format.decimals` | int ≥ 0 | required on every kind |
| `meters.<name>.format.symbol` | non-empty string | required for `currency`, forbidden otherwise |
| `meters.<name>.color` | non-empty string | required; any CSS colour |
| `affordances.<name>` | entry | `<name>` must be an affordance the compiled universe declares |
| `affordances.<name>.label` | non-empty string | required |
| `affordances.<name>.icon` | non-empty string | required |

Every model is `extra="forbid"`; a declared entry declares **all** of its fields (no partial
entries, no per-field defaults). Meters and affordances you do not list simply get the honest
default.

**Format kinds**

- `plain` — the raw value with `decimals` places (`22.5`).
- `percent` — the value as a percentage of the meter's declared `bounds` range, with `decimals`
  places (`85%`). Note this is *of the declared range*, not `value × 100`.
- `currency` — `symbol` followed by the raw value with `decimals` places (`$23`). Showcase packs
  only; the curriculum packs must not use it (`PDR-0025`).

## The honest default (what you get without the file)

The frontend renders every meter from the `meters` payload alone:

- **bar width / `aria-valuenow`** = `(value − bounds.min) / (bounds.max − bounds.min)`, clamped
  to [0, 1] — a large-range meter is a mostly-empty bar, not a bar pegged at 100%;
- **value** = the raw number, precision chosen from the range width (range ≤ 1 → 2 decimals,
  ≤ 100 → 1, else 0) — never `%`, never a currency symbol;
- **critical** = the meter has a declared lethal bound and the value is within 20% of the range
  of it;
- **relationships** = the declared cascade edges (`bars.yaml: cascades`), rendered as
  "→ target + target";
- **affordance glyph** = a deterministic abbreviation of the affordance name, never a lookup
  table: split on non-alphanumerics; two or more words → first letter of each of the first three
  (`DRINK_WATER` → `DW`, `CLEAN_HOUSE` → `CH`); one word → its first two characters (`EAT` →
  `EA`); upper-cased (`frontend/src/utils/formatting.js: nameGlyph`);
- **death certificate** = only meters near a *declared* lethal bound are listed (within 30% of
  the range → "low", within 20% → "critical"), shown with the same formatting rules; a meter
  with no lethal bound never appears, whatever its magnitude.

## Payload (what the server sends)

On `connected`:

```json
"meters": [
  {"name": "energy", "index": 0, "bounds": {"min": 0.0, "max": 1.0},
   "lethal_min": true, "lethal_max": false,
   "cascades_to": [], "cascades_from": ["satiation", "mood"]},
  ...
],
"presentation": null
```

`presentation` is `null` or the validated file as JSON (`{"meters": {...}, "affordances": {...}}`).
Per-affordance `icon` in `state_update.grid.affordances[]` is the declared icon or `null`.

## Failure modes (all loud, all at compile time)

| mistake | result |
|---|---|
| entry for a meter/affordance the pack does not declare | `[UAC-RES-PRESENTATION] <file>:<line>` in stage 5, naming the offender and the declared set |
| `symbol` on a non-currency format, or missing on `currency` | `[LOAD_ERROR]` at parse |
| unknown `kind`, missing field, stray key, wrong `version` | `[LOAD_ERROR]` at parse |
| document missing one of `version` / `meters` / `affordances` | not recognised as a presentation declaration: `[DECLARATION_UNKNOWN]` at discovery |
| declaration absent | not an error — the honest default |

## What this file is not

- Not `cues` (`environment.yaml`): cues are threshold-triggered *signals* (currently an inert
  surface); presentation is static rendering metadata.
- Not a way to change behaviour. If you want a meter observed differently, that is `range_type`
  in `environment.yaml` (`docs/config-schemas/variables.md`), which *is* hashed. Presentation is
  compiled — discovered, resolved and carried — but never hashed.
