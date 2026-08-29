# PDR-0016 — `bars.*.bounds` and the VFS normalization surface are one feature, and land together

Date: 2026-08-11   Status: accepted   Author: Claude (standing product owner)
Owner sign-off: **yes** — chose *"Wire bounds AND the declared normalization together"* over landing bounds alone or deferring past the freeze.
Related: PDR-0015 (bounds scope corrected), PDR-0014 (B3), PDR-0007 (options not yet enabled), PDR-0012 (no tech debt), PDR-0006 (oracle freeze)
Plan: `docs/zzz. archive/plans/2026-08-11-ws1-fix-set.md` §0.1 task 3a · tracker `hamlet-67ffbd282a`, `hamlet-fa6bb6da4a`
Recon of record: `$CLAUDE_JOB_DIR/tmp/RECON-3a.md` (four probes, 278 tool calls, all figures measured)

## Context

Reconnaissance before implementing task 3a overturned four claims in its own spec and
measured a blast radius nobody had estimated. The decisive finding is not about bounds.

**There is no LayerNorm anywhere in the shipped system.** `configs/default_curriculum/brain.yaml`
declares `type: feedforward` with `layer_norm: false`, and `SimpleQNetwork` — which CLAUDE.md
says L0/L0.5/L1 use, *"MLP … with LayerNorm"* — has **zero production construction sites**. It
is dead code. Nothing damps a large input anywhere on the path.

So wiring bounds alone, measured under an oracle policy on L1:

| | unwired | wired |
|---|---|---|
| money in the observation | 1.0 | **9281.98** (the other 123 features stay in [0,1]) |
| \|Q\|max | 0.15 | **141.5** |
| RND novelty MSE | 0.013 | **11820** (≈quadratic in money) |
| max episode length | 92 | **1000** (the cap) |
| mean episode length | 19.8 | 26.7 |

Money is monotone non-decreasing on L1 — all three depletion channels are `0.0`, natural
recovery is `0.0`, and money is neither source nor target of any declared cascade — so **RND
becomes a money odometer**: a large, permanent, never-annealing intrinsic bonus for banking
cash. The survival change also moves the input to the intrinsic-annealing gate (threshold
`100.0`, documented as requiring mean survival > 50 steps), so exploration behaviour shifts as
a second-order effect.

Meanwhile the fix is already declared and already inert. `apply_normalization`
(`vfs/observation_builder.py`) implements `minmax`, `zscore`, `log_scaled`, `one_hot`,
`cyclical_sin_cos` — is tested, is hashed into the schema hashes, and has **zero production
callers**. The compiled `obs_meters` field description literally reads *"8 meter values
(normalized)"* while nothing normalizes it. `dynamic_needs.py` even attaches
`_unit_interval_normalization()` to its `VariableDef`s, and it is never applied.

## The call

**Wire both in one unit.** `bars.*.bounds` drives the runtime ceiling at all six meter-bound
sites **and** supplies the range for the declared observation normalization.

The two are not adjacent, they are the same feature seen twice: `bounds.max` is exactly the
range a `minmax` normalizer needs, and the compiled field already claims to be normalized.
Landing bounds without normalization ships a system where a declared ceiling is honoured in
the runtime and ignored in the observation — swapping one contradiction for another.

## Rationale

The obvious objection is that this is scope growth in a batch that has grown twice already,
and that I had explicitly said *not* to add a normalization to hide the money magnitude. Both
deserve an answer.

**On the second: the distinction is where the number comes from.** Hardcoding a divisor in
the observation builder would be papering over — inventing a runtime fact to mask a config
one. Making `normalization: minmax` in the config actually drive the builder is the opposite:
it is the same strangling as the bounds wiring, applied to the surface next to it. The test
is whether an author can change the behaviour from YAML. After this, they can.

**On the first: the alternative was worse in a specific way.** Landing bounds alone would put
the tree into a state where training is measurably degraded — an RND money odometer and
Q-values three orders of magnitude out — and if the oracle freeze happened in that window,
`PDR-0006`'s oracle would capture *that* as the reference behaviour. Deferring 3a entirely
was rejected for the mirror reason: the oracle would encode a declared-but-contradicted
config as a requirement of the rebuilt system, which is precisely what WS-1 exists to prevent.

This is also the second time in this batch that a "small" fix turned out to be inert without
its neighbour. `PDR-0015` recorded the first: wiring the four clamp sites `PDR-0014` named
would have changed nothing, because `vtc.py:2384` is the site that binds. The pattern is
worth naming: **an inert declared surface is rarely inert alone.** When one is wired, check
whether the surface it feeds is also inert, before claiming the feature works.

## Consequences

- **WS-1 grows to ten units.** Task 3a now covers bounds *and* normalization.
- **Normalization touches every observation, not just money**, so it needs its own adversarial
  verification pass rather than riding on the bounds tests. Non-negotiable: this is a wider
  blast radius than the bounds half.
- **`transition_graph_hash` moves for the 15 packs declaring non-unit bounds** — not "every
  pack" as the spec claimed. 10 of 25 `bars.yaml` declare all meters at `[0.0, 1.0]` and their
  canonical rule payload is byte-identical. Zero cost under `PDR-0011`; no re-stamping.
- **No second `COMPILED_SCHEMA_VERSION` bump.** Measured: the artifact serializes zero `clamp`
  keys and `from_dict` rebuilds both programs from the serialized `bars`. D1 holds — task 2
  owns the only bump in the batch.
- **Several documentation claims are now provably false** and are corrected as part of this
  work rather than left: CLAUDE.md's `SimpleQNetwork`/`RecurrentSpatialQNetwork` architecture
  claims, its `drive_as_code.yaml` requirement (every shipped pack uses `drive.yaml`), and its
  "L0_0_minimal has 1 affordance / obs 29 dims" (measured: 14 affordances, 124 dims).
- **Two frontend defects are now visible but out of scope**, filed separately: `formatting.js`
  renders money as `value * 100` assuming `[0,1]`, so a 22.5 payout displays as "$2250"; and
  `video_renderer.py`'s hardcoded meter ordering does not match the compiled order, so
  recorded videos already mislabel four meters.

## Reversal trigger

Reopen if **any** of the following:

- **Wiring normalization turns out to require a runtime special case** — a branch on a variable
  name, or a normalizer selected by anything other than the declared spec. Same limiting
  principle as `PDR-0014`: presumptively no, and it escalates as a grammar question.
- **The normalization half materially delays the freeze.** Unlike the bounds half, this one is
  severable: bounds could land alone with the training-signal consequences stated and
  normalization re-sequenced, provided **no oracle capture or training run happens in between**.
  That proviso is the whole reason the halves are together; without it the option is void.
- **Normalizing the observation changes behaviour that the curriculum depended on being
  unnormalized.** Unlikely — nothing is normalized today — but if a pack turns out to rely on
  raw magnitudes reaching the network, that is a curriculum question and escalates, and the
  fix is to author the normalization spec, never to re-inert the surface.
