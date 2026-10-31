# RND intrinsic-reward distribution across the token cut — MEASURED

Date measured: 2026-08-26 · Unit-3 Task 11 of the token-observation migration
(`hamlet-fa6bb6da4a`) · spec
`docs/superpowers/specs/2026-08-22-token-observation-representation-design.md` §3b

This is the measurement §3b's decision clause requires: *"the cut's adjudication includes a
**measured** intrinsic-reward distribution comparison on identical states pre/post cut"*,
plus its clause (b), *"per-step intrinsic reward vs presence-flip count"*. It sits beside
`record.md` (the L2 survival baseline) because it complements those curves: `record.md` is
the denominator for `PDR-0114` reversal trigger 1; this file is the instrument for §3b's
named risk, which trigger 1 alone cannot see.

## Why this is a comparison on IDENTICAL states, and not an approximation of one

The state pairing was not synthesized. It is what the differential harness already produces
in `--scripted` mode: both sides step the same world, from the same seed, with **byte-identical
actions** replayed from a file, and the criterion adjudicated at this same commit confirms
`actions` / `dones` / `rewards` are byte-exact on every cell. So the two `obs` arrays in a
cell's trace pair are the **same 101 world states under two observation encodings** — pre-cut
fixed-width superset + activity mask, post-cut token serialization. Source traces:
`runs/differential/20260826-172349` (the scripted acceptance run, `new_dirty: false`).

**The reset artefact §F warns about cannot contaminate this.** Task 9's judgement call 5 —
a cross-universe RND reset re-rolls the fixed network and carries epsilon forward — is a
*training-loop* concern. Nothing is reset here mid-measurement: each side constructs a fresh
`RNDExploration` from the same `torch.manual_seed(42)`, the predictor is trained online over
the trace exactly as the rollout path trains it (accumulate, update at batch size), and
epsilon plays no part because no action is selected. What is measured is the cut's effect,
not a reset's.

**The one thing this comparison cannot hold fixed, stated plainly.** The two sides' RND
networks necessarily have different input widths (that *is* the cut), so their fixed networks
are different random functions. Per-step values are therefore not comparable; the
**distribution** is, which is exactly what §3b asks for. Read the table as "did the novelty
signal stay in a workable regime", never as "did novelty change by X on step t".

## Distribution, per cell

Normalized intrinsic reward (`RNDExploration.compute_intrinsic_rewards`, `update_stats=True`),
over 101 observations × 4 agents per cell.

| cell | obs dim pre → post | PRE mean / median / p95 / max | POST mean / median / p95 / max | PRE first20 → last20 | POST first20 → last20 |
|---|---|---|---|---|---|
| `default_curriculum:L0_0_minimal` | 120 → 1132 | 9.19 / 9.94 / 12.46 / 14.96 | 12.99 / 13.16 / 17.32 / 18.85 | 4.77 → 12.00 | 10.25 → 10.78 |
| `default_curriculum:L0_5_dual_resource` | 120 → 1132 | 9.19 / 9.94 / 12.46 / 14.96 | 12.99 / 13.16 / 17.32 / 18.85 | 4.77 → 12.00 | 10.25 → 10.78 |
| `default_curriculum:L1_full_observability` | 120 → 1132 | 9.19 / 9.94 / 12.46 / 14.96 | 12.99 / 13.16 / 17.32 / 18.85 | 4.77 → 12.00 | 10.25 → 10.78 |
| `default_curriculum:L2_partial_observability` | 120 → 1132 | 7.58 / 8.03 / 10.29 / 11.67 | 11.82 / 12.51 / 13.62 / 14.67 | 4.15 → 9.85 | 8.18 → 12.63 |
| `default_curriculum:L3_temporal_mechanics` | 120 → 1132 | 8.91 / 9.60 / 11.90 / 13.97 | 12.97 / 13.16 / 17.32 / 18.86 | 4.83 → 11.29 | 10.25 → 10.76 |
| `div003_cubic_partial:L2_partial_observability` | 350 → 1132 | 6.29 / 6.72 / 8.81 / 9.51 | 13.47 / 14.56 / 15.79 / 16.73 | 3.17 → 8.53 | 8.55 → 14.66 |
| `div003_rect:L1_full_observability` | 104 → 1132 | 10.38 / 11.25 / 12.69 / 13.65 | 12.55 / 12.54 / 16.53 / 18.04 | 6.44 → 11.96 | 9.83 → 10.91 |
| `div003_scaled:L1_full_observability` | 122 → 1132 | 17.66 / 17.86 / 20.72 / 23.09 | 10.30 / 10.08 / 13.87 / 15.62 | 16.02 → 16.80 | 11.33 → 8.06 |
| `effects_smoke:L0_effects` | 59 → 272 | 8.61 / 8.94 / 11.94 / 13.57 | 9.34 / 10.08 / 12.43 / 13.29 | 4.51 → 11.47 | 4.80 → 12.25 |
| `items_smoke:L0_smoke` | 61 → 1121 | 1.28 / 0.01 / 4.84 / 8.33 | 8.10 / 8.68 / 11.61 / 12.06 | 3.31 → 0.71 | 3.87 → 11.36 |

**Finding: the novelty signal stays in the same regime.** Post-cut means land in 8.1–13.5 on
every cell; pre-cut spanned 1.3–17.7. The signal neither collapses to zero (no
"everything looks identical") nor blows up (no saturating perpetual-novelty pump). It moves
in *both* directions across cells — `div003_scaled` falls 17.66 → 10.30 while `items_smoke`
rises 1.28 → 8.10 — which is the signature of a re-scaled random projection, not of a
systematic drift the cut introduced. The nine-times-wider observation did **not** produce a
nine-times-larger novelty signal: the running-std normalization inside
`compute_intrinsic_rewards` absorbs the width, which is the property that makes the annealing
gate's threshold (`100.0`) still meaningful after the cut.

`items_smoke` is the one cell whose distribution changes character rather than scale: its
pre-cut median was `0.01` — a 61-dim observation that barely moved, so novelty was near-nil —
against a post-cut `8.68`. That is more signal, not less, and it is what a wider, actually
varying observation should do.

## The named risk (§3b): presence flips, and whether they pump

§3b's risk is that presence flips are large discontinuous jumps, so novelty becomes partly a
visibility-churn detector and pacing the boundary becomes an intrinsic-reward pump. Measured
on the post-cut side: presence lanes lead every serialized token row
(`TokenSpec.row_layout()`), so a flip is directly countable per step.

| cell | total presence flips (100 steps × 4 agents × all tokens) | steps with ≥1 flip | max flips in one step | corr(per-step intrinsic, flip count) |
|---|---|---|---|---|
| `default_curriculum:L2_partial_observability` | 262 | 65 | 12 | **+0.029** |
| `div003_cubic_partial:L2_partial_observability` | 219 | 57 | 12 | **+0.019** |
| `items_smoke:L0_smoke` | 60 | 26 | 4 | **+0.206** |
| every other cell | **0** | 0 | 0 | undefined (no flips) |

**Finding: no boundary-farming pump on any shipped pack.** The correlation between per-step
intrinsic reward and presence-flip count is ≈0 on both POMDP cells (+0.029, +0.019) and weak
on `items_smoke` (+0.206, over 26 flipping steps). If visibility churn were driving novelty,
this is where it would show, and it does not. Recorded as the instrument §3b(c) asks for —
"an interesting failure is only valuable if the instrument to see it exists first" — not as
proof it can never happen: 100 steps of scripted play is a small window, and a *trained*
agent that has learned to pace a boundary is precisely what this instrument exists to catch
later.

**A second finding, unasked for and worth having.** Seven of the ten cells show **zero**
presence flips across the whole trace: their observed entity set is completely static. Only
partial observability (the two POMDP cells) and item carrying (`items_smoke`) make anything
appear or disappear. So the `dynamic`-filler token types are barely exercised by the shipped
fleet — the same shape as `hamlet-aba6171ff7` (every `variable_element` slot in the fleet is
inert). The presence mechanism is built and correct; almost nothing in the demo content
drives it.

## Reproducing

```bash
UV_CACHE_DIR=.uv-cache uv run python -m townlet.oracle.harness --scripted   # produces the trace pairs
# then: load each cell's {old,new}.npz, run RNDExploration(obs_dim=W) from torch.manual_seed(42)
# over the obs stream with update_stats=True and the online predictor update, per side.
```

The trace pair is the artifact that matters; the RND driver is a dozen lines over it. Kept as
a recorded procedure rather than a checked-in script because it is a one-shot adjudication
measurement, not a gate — turning it into a gate is `hamlet-aba6171ff7`-adjacent follow-on
work, listed in the spec §3b(b) training-diagnostics clause.
