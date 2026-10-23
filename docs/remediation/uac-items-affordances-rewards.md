# Universe-as-Code B: items, affordances, meters and rewards — gap analysis and remediation plan

Scope: `src/townlet/items/` (manager, action_handlers, inventory, instance),
`environment/affordance_engine.py`, `dac_engine.py`, `reward_calculator.py`,
`action_executor.py` (INTERACT and item dispatch), the item/affordance/meter token publishers,
`config/items_config.py`, `affordances_v2_config.py`, `bars_v2_config.py`, `drive_as_code.py`,
`affordance_masking.py`, `environment_config.py`.
Evidence: `review-2026-10-24/findings_items.md`, scripts `review-2026-10-24/items/`.

## What the subsystem promises

README and `docs/config-schemas/`: items are declared in a catalog with profile-qualified
identities and placed by level appearance rules on any substrate; affordances have costs,
effects, opening hours, multi-tick interactions and capacity; meters have bounds, depletion and
recovery; rewards are entirely declared in `drive.yaml` with modifiers, extrinsic, intrinsic and
shaping components and the formula `extrinsic + intrinsic × Π modifiers + shaping`; all fields
required, no defaults.

## What it does

The DAC formula is exact on a hand-computed batch. Item-slot observation values are normalized,
reset clears items, inventories and item state fully, the same-tick GET race is clean, the
five levels' affordance files are byte-identical, and no executable branch in the reward path
names a meter.

The declared semantics drift from the executed ones in five places that change what a policy
learns. Modifiers and thresholds are compared against raw meter values while the DTO forces their
vocabulary into zero-to-one, so a money-crisis modifier on a money meter bounded at a million
can never fire. A `base_reward` of zero is silently one. The completion bonus pays on every tick
of a multi-tick interaction. Opening hours assume a 24-tick day. Items do not spawn on anything
but a 2-D or 3-D grid, and a cached compile drops the appearance rules entirely. Around those,
the usual layer of declared-and-inert: `recovery.natural`, `on_drop`, the capability vocabulary,
`approach_reward` ignoring the substrate metric, dead agents still acting.

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

## Remediation plan

### WP1 — Items on every substrate (I1, I2)

Depends on compiler WP1 (serialization) and strata WP4 (rank-generic position typing). Here:
`spawn_initial_items`, `find_spawn_location`, `grid` and `random` placement iterate
`position_dim` axes using substrate extents; aspatial either refuses `items_appearance` or gets a
positionless item mode (recommend refusal until a pack needs it). Verification: `p12_misc.py`
gridnd case spawns; `p10_gridnd_items.py` reports extents for every family. Size: M.

### WP2 — DAC on declared semantics (I3, I4, I5)

Three changes, one package, because they are the reward path and should land together:

- **Normalize before compare.** `reward_calculator.py` passes meters normalized by their declared
  bounds to every modifier, bonus and threshold, so the `[0,1]` vocabulary the DTO enforces is
  the vocabulary the engine compares. The docstring at `dac_engine.py:863` already claims this.
- **Delete the `or 1.0` defaults.** `base` and `base_reward` become required on their strategies
  (the DTO currently defaults them to `None`); the engine reads them without `getattr`.
- **Completion means completion.** DAC's `completion_bonus` reads `completion_mask` from the
  interaction-progress result, not "interacted this tick". Delete
  `compile_vtc_interaction_completion_bonuses` and `completion_bonus_rules`; they have never been
  evaluated and their only effect is on a hash.

Verification: `p13_more.py` money-crisis multiplier is 0.0 at money 1; `dac_formula.py` and
`p14_final.py` show `extrinsic [0,0]` for `base_reward: 0.0` and a parse refusal when omitted;
`p9_multitick.py` (ii) pays 0.1 once at completion. Re-run the oracle differential cells after
this lands; the reward stream will move on every pack with a modifier, and that is the point.
Size: M. **Sixth in the cross-subsystem order; nothing about convergence is meaningful before it.**

### WP3 — One clock for hours (I6, I10)

Owned by effects WP5 for `time_in_window`; here: `TimeRange` and affordance hour bounds validate
against the declared `day_length` at cross-validate instead of `le=23`; `opening_hours.enabled`
and `timing_bonus` on a non-temporal level refuse at compile the way `multi_tick` does.
Verification: `p9_multitick.py` (iii) with 48; `p13_more.py` and `p14_final.py` non-temporal cases
refuse. Size: S.

### WP4 — Dead agents, overlapping affordances, metric-aware approach (I7, I8, I9)

Apply the `~dones` gate to movement and every item dispatch. Refuse overlapping fixed affordance
positions at cross-validate; if overlap is a wanted mechanic, INTERACT targets exactly one
affordance by a declared priority. `approach_reward` routes through `substrate.distance()` and
refuses at compile on aspatial. Verification: `p7_dead_agent.py` shows no state change;
`p8_two_aff.py` refuses at compile; `p12_misc.py` manhattan 6 pays 0; `p14_final.py` aspatial
refuses. Size: S.

### WP5 — Held items and item identity (I11, I12)

Held exclusive items stay in the item token with `carried = 1` and the holder's slot in
`owner_slot`; `lift_item` moves the row's locality, not its existence. The `held_items` store
either feeds the `ItemSlotBatch` or is deleted in favour of a `holder` field on the instance.
Item identity: the static payload per slot carries the profile's declared parameter signature
(the same recursive-identity rule meters and affordances use), so apple and coin differ by what
they are, not by name. Verification: `p1_items_obs.py` medkit row `presence=1 carried=1
owner_slot=<agent>` after GET; apple and coin rows differ in non-position lanes. Size: M.

### WP6 — Inert lifecycle hooks (I13)

Call `_execute_interaction(..., "on_drop")` from `handle_drop_slot_action`. `spawn_item` either
gets positions threaded (effects WP3) and a `position` that accepts `self`, `target` or a
coordinate list validated against `position_dim`, or is deleted; the plan recommends threading,
since trial B's whole premise needs it. Interaction progress becomes a declarable exposure: an
engine-written agent variable (`semantic_type: interaction_progress`) the author may expose, or
nothing; the test that asserts it is NOT observable is deleted either way. Verification:
`p2_on_drop.py` pays the drop effect; `p6_spawn_item_pos.py` spawns at `target`; `p11_l3.py`
finds the exposure when declared. Size: M.

### WP7 — Delete inert vocabulary (I14)

Delete: `recovery.natural` (and remove it from the meter identity payload; `layout_hash` moves,
which is correct), `config/capability_config.py`, `config/affordance_masking.py`,
`IntrinsicStrategyConfig.strategy` and the four `*_config` blocks (or bind the runtime exploration
module to them and delete the `training.yaml: intrinsic.*` spelling; one authority, and
`drive.yaml` is the declared home of reward structure, so recommend binding here and deleting
there), `ExtrinsicStrategyConfig.variable`, `CompositionConfig` entirely, `TriggerCondition`,
one of the two `vfs_variable` shaping DTOs, `environment.yaml` `category` and `cues`,
`on_early_exit`/`on_failure` stage names, the `aggregation`/`hybrid` docstring promises. Make
cross-strategy fields a tagged union so `multiplicative` cannot carry `bar_bonuses`.
Verification: every shipped pack re-validates after the fields are removed from it;
`dac_formula.py` cross-strategy case refuses at parse. Size: M.

### WP8 — Declared retirement and spawn accounting (I15)

Either add a `retirement_bonus` shaping type and move the `+1.0` into every shipped `drive.yaml`
(the differential will move; register it), or delete the term. Count only successful spawns
toward `max_total`. Random placement checks occupancy or the DTO says stacking is allowed.
Verification: `p12_misc.py` tick-99 case and `max_items_in_world: 2` case. Size: S.

### WP9 — Whitelist (I16)

After WP2 and WP7, run the lint with an empty whitelist over this seam and keep only entries that
name a line and a structural reason. Delete the `affordance_config.py` line. Size: S.

## Docs to correct in the same changes

- `docs/config-schemas/bars.md:97`: delete `recovery.natural` (WP7).
- `docs/config-schemas/items.md:449, 653`: `position: "target.position"` (WP6), `on_drop`
  executes once it does (WP6).
- `docs/config-schemas/drive_as_code.md`: lift the staleness banner once WP2 and WP7 land; state
  that comparisons are on normalized meters; delete `composition`, `aggregation`, `hybrid`.
- `README.md` "Rewards": delete the "accepted but inert" paragraph once WP7 lands.
