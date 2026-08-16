# Frontend Visualization (Vue 3)

**Location**: `frontend/src/components/`

## Rendering modes (substrate-specific)

- **Spatial** (Grid2D/3D substrates): `Grid.vue`, SVG-based 2D grid — cells, agent
  positions, affordances, heat map overlay, agent trails, novelty heatmap (RND).
- **Aspatial** (aspatial substrates): `AspatialView.vue`, meters-only dashboard — meter
  bars with color coding, affordance list, action log.

**Rationale**: Aspatial universes have no position concept — rendering a fake grid would be
pedagogically harmful. Never add a grid view for aspatial substrates.

## WebSocket

Server broadcasts on `localhost:8766`; the frontend connects on mount. Start the stack with
the `live-inference` skill.

## Customization

Presentation is **declared, honest by default, never inferred from a variable's name**
(PDR-0025). Icons, labels, meter colours and value formats are no longer edited in JS — they
are declared in the pack's `presentation.yaml` (observer-only, optional; the universe compiler
never reads it). Absent that file the frontend renders the honest default: every meter shows
its raw value against its declared range (no `%`, no `$`), every affordance shows a
name-derived abbreviation, and one generic colour scheme applies to all.

- What the server sends: `connected.meters` (declared bounds / lethal_min / lethal_max /
  cascades per meter, compiled index order) and `connected.presentation` (the pack's
  `presentation.yaml` as JSON, or `null`). Kept in `stores/simulation.js` as
  `meterMetadata` / `presentation`. Empty metadata = server predates the contract → the meter
  panel renders nothing rather than guessing.
- Rendering rules (default precision, `percent`/`currency`/`plain` formats, criticality =
  within 20% of a lethal bound, abbreviation glyphs, cascade text): `src/utils/formatting.js`,
  every function documented and covered by `formatting.test.js`. Nothing in that module takes
  a meter or affordance name to decide how a value looks.
- Do not add a name→icon or name→colour table anywhere under `src/`. If a pack wants a look,
  it declares it in `presentation.yaml`.
- Grid cell size: `frontend/src/utils/constants.js`

## Tests

`cd frontend && npm test` (vitest, jsdom). `npm run build` must also pass.
