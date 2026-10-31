## Gaps

Full defect sites, reproductions and refutations: `review-2026-10-24/findings_items.md`
(F-numbers) and filigree ids.

| id | sev | gap | source |
|---|---|---|---|
| I1 | P1 | Cached compile drops `items_appearance` (compiler WP1) | F1 |
| I2 | P1 | Items never spawn off Grid2D/Grid3D (strata WP4) | F2, hamlet-6c49488b22 |
| I3 | P1 | DAC compares raw meters against a `[0,1]` vocabulary; `money_crisis` can never fire | F3 |
| I4 | P1 | `base_reward: 0.0` and omitted `base_reward` become 1.0 | F4 |
| I5 | P1 | `completion_bonus` pays every tick; VTC completion rules never evaluated | F5 |
| I6 | P1 | Opening hours and `timing_bonus` hardcode a 24-tick day | F6 |
| I7 | P2 | Dead agents still move and use items | F7 |
| I8 | P2 | Two affordances on one cell both fire | F8 |
| I9 | P2 | `approach_reward` Euclidean regardless of metric; pays fully on aspatial | F9 |
| I10 | P2 | Opening hours and `timing_bonus` silently inert on non-temporal levels | F11 |
| I11 | P2 | Held exclusive items invisible; broken tool equals empty hand | hamlet-4b931faaf4, hamlet-17a7f03bc9 |
| I12 | P2 | Item tokens carry no identity; `owner_slot` lanes never produced | hamlet-559cc74246, F13 |
| I13 | P2 | `on_drop` never invoked; `spawn_item` unreachable; interaction progress undeclarable | hamlet-628e202bf7, hamlet-1b9af9088c, hamlet-266a0a41f0 |
| I14 | P2 | Inert vocabulary: `recovery.natural`, capability and masking DTOs, intrinsic `*_config`, `composition`, `cues`, `category`, `on_early_exit`/`on_failure`, docstring promises | F12, hamlet-d45331a367, hamlet-6b24c0bd83 |
| I15 | P3 | Hard-coded `+1.0` retirement; refused spawns counted; placement ignores occupancy | F10, F14, F15 |
| I16 | P3 | Whitelist residue and hidden defaults | F16 |
