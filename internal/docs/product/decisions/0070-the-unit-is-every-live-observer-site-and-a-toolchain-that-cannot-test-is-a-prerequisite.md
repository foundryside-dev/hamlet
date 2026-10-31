# PDR-0070 — unit 2 is *every live observer site*, dead sites are recorded not fixed, and a frontend that cannot be built or tested is a prerequisite taken inside the unit

Date: 2026-08-17   Status: **accepted** (scope owner-chosen at the 2026-08-17 `/own-product`
resume from three options; the prerequisite call and the dead-site rule are the agent's,
inside the grant — prioritise the backlog, accept against criteria)
Author: Claude (standing product owner)
Owner sign-off: **yes** on scope (*"All live observer sites"*); prerequisite and dead-site rule
recorded here for provenance, not escalated (reversible, in-grant)

Related: `PDR-0069` (the home), `PDR-0025` (call #1: *"no name-based special cases anywhere in
the presentation layer"*), `PDR-0045` (a name branch counts only if it executes), `PDR-0012`
(debt is what is wired wrong; failing/unrunnable gates are debt), `PDR-0068` (the queue runs
before the merge; its ~30-commits trigger is now near)
Tracker: `hamlet-0dd4ac24d9` (closed), `hamlet-d892e161c0` (closed — the prerequisite),
`hamlet-102db4c2e0` (filed — the dead site), `hamlet-16ae192d42` (recording, untouched)
Evidence: `fb791193`, `a5cca764`; `frontend/src/utils/formatting.test.js`,
`frontend/src/components/MeterPanel.test.js`, `frontend/src/stores/simulation.test.js`

## Context

The recon (2026-08-17) turned a one-function ticket (`formatting.js:24`, `if (name ===
'money')`) into a layer-wide finding: the name-branching was **observer-wide** — hardcoded meter
tiers, a meter-relationship map, name-keyed colours (with raw hex for two meters), `mood` /
`social` semantics driving strobe classes, per-meter-name CSS tokens in two files, an
affordance-icon table in the frontend **and a second one in the server** (`live_inference.py`
`AFFORDANCE_ICON_MAP`, name→emoji, live), plus a death certificate that printed `value × 100 %`
for every meter (a 22.5 balance rendered "2250%"). Three readings of scope led to materially
different work — narrow (the ticket's function), meters-only, or every live site — so the owner
was asked.

Separately: **`frontend/package.json` did not exist**, so nothing under `frontend/` could be
built or tested. `hamlet-d892e161c0` (P1, WS-0, ready) had been open since 2026-05-16.

## Options (scope)

1. **All live observer sites** — meters and affordance icons, server and frontend; dead sites
   recorded, not fixed. — *chosen*
2. Meters only; icon maps filed as follow-up.
3. Narrow: `formatting.js` + bounds; the rest filed.

## The call

**Scope: option 1**, because `PDR-0025` already says "anywhere" and the server-side icon table
is privileged Python in `src/townlet` — leaving it would have closed the ticket while the
runtime still knew what EAT looks like.

**Two calls inside the grant, recorded here:**

- **The prerequisite is part of the unit.** A frontend change cannot be *accepted against
  criteria* without a build and a test run, and there was no toolchain. `hamlet-d892e161c0` was
  taken first, minimally: `package.json` with dependencies matching the actual imports (`vue`,
  `pinia`; dev `vite`, `@vitejs/plugin-vue`, and `vitest` / `@vue/test-utils` / `jsdom` because
  the unit adds tests), lockfile tracked per `.gitignore`'s own instruction, `npm install` and
  `vite build` verified. The `.gitignore` blanket `*.json` triage stays with WS-0 — the
  negation for the manifest already existed; the file had simply never been written.
- **Dead sites are recorded, not fixed inside the unit.** `AffordanceGraph.vue` is fed by an
  `affordance_graph` message no server emits and keys on legacy names no pack uses — its gold
  `Job` colour never executes (`PDR-0045`: count executed behaviour). It is left byte-identical
  and filed (`hamlet-102db4c2e0`, under WS-4) as *delete, or capture the intent and rebuild
  from the compiled transition graph*. `recording/video_renderer.py` stays under
  `hamlet-16ae192d42`. Two *unreferenced* components hardcoding legacy affordance names
  (`AffordanceLegend.vue`, `ReferencePanel.vue`) were deleted — dead code with no capability
  behind it, not a deferred option.

## Rationale

The narrow reading would have satisfied the ticket's headline (22.5 no longer "$2250") while
the same layer kept eight other ways of knowing what the game is; the meters-only reading would
have closed the meter half and left a name→emoji table *in the server*. "Anywhere" was already
ruled; only its cost was open, and the cost was mostly the missing toolchain — which was a
P1 debt of its own (`PDR-0012`: an untestable surface is a gate that cannot fail).

The dead-site rule keeps the unit's claim honest: it says *no live site infers presentation
from a name* — verified by a grep gate that returns nothing outside the dead component and
tests — not *no such text exists*. Deleting `AffordanceGraph.vue` may well be right, but that
is a delete-vs-capture decision (`PDR-0007` shape) and belongs to its own ticket.

## What landed (verified by execution)

- Server: `AFFORDANCE_ICON_MAP` deleted; `connected` carries `meters` + `presentation`; icons
  are declared or `null`. Frontend: no function in `formatting.js` takes a name; MeterPanel is
  one flat compiled-order list; tiers, relationship map, colours-by-name, mood/social semantics,
  strobes, `AFFORDANCE_ICONS`, dead thresholds, per-name CSS tokens gone; death certificate
  judged from declared lethal bounds. Real `connected` frame read from a live server on a
  fresh checkpoint: `presentation=None`, eight meters in compiled order, money `max 999999.0`.
- Gates: pytest 3247 / 16 / 0 (+27); ruff, black, mypy, `no_defaults_lint` clean; **`npm test`
  37 / 37 — the frontend has a test gate for the first time**; `vite build` clean; matrix
  16/16 `DIVERGED_AS_REGISTERED`, exit 0.

## Reversal trigger

- **A live name-branch reappears in the presentation layer** — the grep gate in comment 158 of
  `hamlet-0dd4ac24d9` returns a hit outside `AffordanceGraph.vue` and tests. Re-open the unit;
  the surface was not the path of least resistance.
- **`hamlet-102db4c2e0` is closed by re-feeding `AffordanceGraph.vue` from names** rather than
  from the compiled transition graph. That is the dead site coming back to life as the same
  defect.
- **The frontend gate goes dark again** — `npm test` or `vite build` stops running locally or
  in CI without a recorded reason. An untestable surface re-opens `PDR-0012`'s category.
