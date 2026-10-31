# PDR-0142 — Trial-pack disposition: two promoted to fixtures, nine deleted

Date: 2026-09-02   Status: **accepted** (within the grant; the disposition options were pre-set by
`PDR-0082`–`PDR-0085` / PRD-0001 §9 and the owner preauthorised the roll into unit 5)
Author: Claude (standing product owner)
Related: `PDR-0077`, `PDR-0082`, `PDR-0083`, `PDR-0084`, `PDR-0085`, `PDR-0089`, `PDR-0111`,
`PDR-0114`, `PDR-0132`, `PDR-0141`, `hamlet-55b2826a02`

## Context

PRD-0001 §9 (criterion 7) requires every authoring-trial pack to be **promoted to a regression
fixture** — referenced by at least one test — **or deleted by 2026-10-06**; an orphan pack on that
date breaches the Pre-release hygiene guardrail. `PDR-0114` ruled that the retired corpus's packs
resolve on that clock **before migration unit 5**, that unit 5's inert-guard is satisfied by
purpose-built or promoted packs, and that reversal trigger 3 is evaluated only on packs that
survive. `PDR-0141` accepted unit 4, so the clock is now the first act of unit 5.

Measured 2026-09-02 on `project-recovery-3@8047b68c`:

| pack | compact width | census (meter/aff/item/effect/var) | bound by a test | other live citations |
| --- | ---: | --- | --- | --- |
| `trial002_money_log_gdp` | 49 | 4/4/0/1/2 | `test_compiled_token_coherence.py`, `test_token_emission.py` | — |
| `trial_k_cold` | 60 | 5/2/3/1/0 | `test_affordance_token_identity.py` | — |
| `trial002_money_int_capped` | 43 | 4/4/0/0/2 (identical to `simple`) | none | — |
| `trial_b_blind_organism` | 3,553 | 2/2/251/0/0, gridnd | none | token spec (trigger-3 example) |
| `trial_b_organism` | 14,088 | 4/3/1001/3/0, gridnd | none | — |
| `trial_b_organism_2d` | 8,047 | 4/2/1001/2/0 | none | — |
| `trial_f_durability` | 56 | 2/1/2/4/0 | none | divergence register (`exposed_to` note) |
| `trial_l_cooldown` | 67 | 4/2/2/4/0 | none | — |
| `trial_m_combo` | 72 | 4/3/2/4/0 | none | — |
| `trial_o_bidding` | 52 | 5/2/2/1/0 | none | — |
| `trial_o_bidding_blind` | 59 | 4/6/0/1/2 (`extents`, agent profile) | none | `COMPILER.md`, `transition_rules.md`, README |

The PRD's own precedent (`configs/trial002_money_*` ← `test_meter_bounds_runtime.py`) no longer
holds: that test now reads `default_curriculum`, so `trial002_money_int_capped` is an orphan.
Every trial finding is banked in `docs/product/trials/0001/` and the trial PDRs; the packs
themselves are reproducible from git at those PDRs' commits.

## Options considered

1. **Promote all eleven.** Rejected: nine would need a purpose-written config-in/behaviour-out
   exercise each, three of them carry 1,001 item slots and 3,553–14,088-float compact rows that
   `PDR-0114` already identified as the trigger-3 breach, and the probe scripts and
   `experiment.yaml` instruments are retired-corpus litter, not fixtures.
2. **Delete all eleven and rebuild coverage from scratch.** Rejected: two packs are already
   bound by tests that pin token identity and emission behaviour; deleting them deletes working
   coverage for no gain.
3. **Promote exactly the packs a test already binds; delete the rest; let unit 5 build
   purpose-built fixtures for the coverage gaps.** Chosen.

## The call

- **Promoted to fixtures:** `configs/trial002_money_log_gdp` and `configs/trial_k_cold`. They
  keep their paths (the binding tests reference them). `trial_k_cold/probe_trial_k.py` — a
  retired-instrument probe, not part of the fixture — is deleted.
- **Deleted:** `trial002_money_int_capped`, `trial_b_blind_organism`, `trial_b_organism`,
  `trial_b_organism_2d`, `trial_f_durability`, `trial_l_cooldown`, `trial_m_combo`,
  `trial_o_bidding`, `trial_o_bidding_blind`, each with its probe script.
- **Live citations corrected in the same commit:** `docs/architecture/COMPILER.md` (non-null
  `agent_profile` example → `configs/test/vfs_bar_access`, re-verified),
  `docs/config-schemas/transition_rules.md` (pair-scoped `trust` ships only in
  `L5_multi_agent`), README pack census (dated disposition sentence; `extents` declared by one
  pack). The divergence register's dated `exposed_to` note and the token spec's trigger-3
  example are historical statements and stay as written.
- **Trial records** under `docs/product/trials/0001/` each gain a dated disposition line, as
  PRD-0001 §9 requires.

## Coverage consequences for unit 5 (recorded, not deferred)

With the corpus gone, the shipped and fixture packs expose: effects only through
`trial002_money_log_gdp` (1), `trial_k_cold` (1) and the `effects_smoke` / `items_smoke`
fixtures; `gridnd` only through `configs/test/gridnd_4d_pack`; `exposed_to` through **no pack**;
**agent tokens through no pack at all** (capacity 0 in every compiled level, including
`L5_multi_agent`). Unit 5's "one committed config-in/behaviour-out exercise per live token type
and supported scope" therefore has to add purpose-built fixtures for at least agent tokens,
`exposed_to`, and the item-arena `variable_element` scope, and re-author `set_encoder_smoke`
(deleted with its three tests at `d554fb7f`) and L3 `day_phase` authoring on the accepted ABI.

## Reversal trigger

- If a future instrument (`PDR-0111`'s successor bet) needs one of the deleted packs, it is
  restored from git at its trial PDR's commit as a new fixture with its own exercise — never
  silently re-added.
- If either promoted pack loses its binding test, it is deleted under the same rule.
