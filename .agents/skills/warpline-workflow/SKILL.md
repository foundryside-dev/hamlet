---
name: warpline-workflow
description: >
  Use when the user asks "what changed", "what breaks if I touch X", "what is the
  blast radius / change impact", "what should I re-verify before claiming done",
  "show the timeline / churn for this entity", or when working in a project that
  uses warpline for temporal change-impact tracking. warpline is the Weft federation's
  temporal authority; its MCP tools (mcp__warpline__*) answer change-impact and
  reverify questions, enrich-only, from a local-first dated store.
---

# Warpline Workflow

warpline is the federation's **temporal / change-impact authority** — "if I touch
X, what breaks, and what must I re-verify?". It owns temporal change facts and
dated edge snapshots; it does NOT own current structure (loomweave), work state
(filigree), trust policy (wardline), or governance (legis).

## The tools (endorsed name / short shim — identical schema+data)

- `warpline_change_list` / `changed` — changed entities for a repo + rev range.
  Returns `next_actions` pointing at reverify/impact. **Call this first.**
- `warpline_impact_radius_get` / `blast_radius` — downstream affected set over the
  dated snapshot. Carries mandatory `completeness` + `staleness`.
- `warpline_reverify_worklist_get` / `reverify` — the worklist to recheck before
  claiming completion. The flagship.
- `warpline_entity_timeline_get` / `timeline` — ordered change history for one
  entity; reports `sei_resolution` only, never lineage.
- `warpline_entity_churn_count_get` / `churn` — per-entity change-event counts.
- `warpline_edge_snapshot_capture` / `capture_snapshot` — the only mutating tool;
  captures dated loomweave edges into `.weft/warpline/`. Run when impact/reverify
  reports `NO_SNAPSHOT` and loomweave is available.

## Typical loop

1. `changed` (rev_range, e.g. `HEAD~1..HEAD`) → read `next_actions`.
2. `reverify` (or `blast_radius`) with the suggested arguments.
3. If `completeness: NO_SNAPSHOT`, run `capture_snapshot`, then retry.

## Reading the answer honestly

- `completeness` is `FULL | DELTA | NO_SNAPSHOT | SKIPPED`; `staleness` reports
  the snapshot commit and how far behind HEAD it is. A thin answer looks thin —
  never treat `NO_SNAPSHOT` as "nothing is affected".
- `enrichment` is a CLOSED vocab: `present` / `absent` (peer present, no fact) /
  `unavailable` (peer unreachable). Sibling absence is explicit, **never** an
  implied clean/allowed state. warpline never gates — its facts are advisory.
- Every entity carries both `locator` and `sei` (`loomweave:eid:...`, opaque).
- Every response is `meta.local_only: true`, `peer_side_effects: []`.

## References (progressive disclosure)

Load these on demand rather than reading upfront:

- **`references/tools.md`** — exact input/output schema for each of the 6 tools.
  Load when you need a tool's precise arguments or `data` shape.
- **`references/contract.md`** — the frozen success/error envelope, the closed
  enrichment + error_code vocab, SEI keying, and seam authority boundaries. Load
  when parsing a response or reasoning about a cross-member seam.
- **`references/degrade-and-federation.md`** — completeness/staleness semantics,
  how sibling absence degrades (enrich-only), and the `install`/`doctor` member
  lifecycle. Load when an answer looks thin or when wiring warpline into a repo.
- **`examples/changed-to-reverify.json`** — a worked `changed → reverify` flow
  showing the frozen envelopes end to end.
