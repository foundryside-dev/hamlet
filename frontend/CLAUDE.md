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

- Affordance icons: `frontend/src/utils/constants.js`
- Meter colors: `frontend/src/styles/tokens.js`
- Grid cell size: `frontend/src/utils/constants.js`
