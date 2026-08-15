# Warpline frozen contract (reference)

Authoritative source: `<weft-root>/pm/2026-06-13-warpline-interface-lock.md`
(FROZEN). warpline implements TO this contract; it is never edited locally.

## Success envelope (every outbound tool)

```json
{
  "schema": "warpline.<contract>.v1",
  "ok": true,
  "query": {"repo": "...", "tool": "...", "arguments": {}, "filters": {},
            "sort": {"by": "...", "order": "asc"}, "page": {"limit": 50, "cursor": null}},
  "data": {},
  "warnings": [],
  "next_actions": {},
  "enrichment": {"sei": "...", "edges": "...", "work": "...", "risk": "...",
                  "governance": "...", "requirements": "..."},
  "meta": {"producer": {"tool": "warpline", "version": "..."},
            "local_only": true, "peer_side_effects": []}
}
```

- `enrichment` CLOSED vocab: `present | absent | unavailable` (plus
  `stale | partial | skipped` for `edges`). `absent` = peer present, no fact;
  `unavailable` = peer unreachable. Neither is ever a transport error or an
  implied clean/allowed state.

## Error envelope (`warpline.error.v1`)

```json
{"code": -32602, "message": "invalid params",
 "data": {"schema": "warpline.error.v1", "error_code": "...", "rejected_field": "...",
          "retryability": "retry_safe|retry_with_changes|fatal", "hint": "...", "details": {}}}
```

CLOSED `error_code` set: `missing_required_field, invalid_repo, invalid_rev_range,
invalid_entity_ref, invalid_changed_refs, invalid_depth, invalid_filter,
invalid_sort, peer_unavailable, snapshot_unavailable, internal_error`. Switch on
`error_code`, not message text.

## Keying

Every entity carries BOTH `locator` and `sei` (`loomweave:eid:<32-hex>`, opaque —
warpline never mints or parses it). `warpline_entity_key_id` is warpline-internal and
NOT a federation key; key on `sei` (preferred) or `locator`.

## Seam boundaries (deconfliction-first; advisory never gates)

- loomweave owns current structure + SEI minting/resolution.
- filigree owns work state; warpline reads links, never files/closes/claims.
- wardline owns trust policy; warpline re-derives risk as ordering signal, never a
  clean/allow verdict. wardline absent → `risk: unavailable`, never `clean`.
- legis owns governance + the rename feed; warpline emits advisory impact only. The
  `governance` enrichment echoes legis `governance_read.v1` (verified clearances
  only): `absent` = "no verified clearance" (conflates ungoverned / unknown-SEI /
  actively-blocked), never "ungoverned"; the clearance `content_hash` is echoed, not
  re-verified against the current body.
