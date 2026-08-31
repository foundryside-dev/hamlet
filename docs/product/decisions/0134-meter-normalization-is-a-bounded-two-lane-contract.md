# PDR-0134 — Meter normalization is a bounded two-lane contract

Date: 2026-08-31   Status: **accepted** (engineering reconciliation within the standing grant)
Author: Codex (standing product owner)
Supersedes in part: `PDR-0053`, `PDR-0057`
Implements: `PDR-0132` milestone 2, `hamlet-1e335e0363`

## Context

`PDR-0057` made all nine VFS normalization kinds authorable as meter `range_type` values in
the old variable-width observation ABI. The token cut then replaced that ABI with a fixed
two-lane value block and bounded payloads, but `MeterTokenPublisher` silently substituted a
clamped bars-derived minmax value. `environment.yaml` still accepted all nine declarations even
though none reached the observation.

The regression cannot be repaired by replaying the old promise unchanged. `one_hot` requires C
lanes; `none`, `zscore`, and `masked_value` can emit unbounded values; and `rank_scaled` couples
one world's observation to other independent worlds in the batch. Encoding those shapes into two
lanes would either change their meaning or introduce a hidden translation. Neither is an honest
engineering contract.

This project is pre-release with zero users. Compatibility is not a product requirement.

## The call

`meters[].range_type` remains the sole authority for how a meter enters a token, but its vocabulary
is contracted to exactly the transformations that are bounded and fit the fixed two-lane block:

- `minmax`, with `clip: true` required;
- `log_scaled`, with `clip: true` required;
- `cyclical_sin_cos`, using both value lanes; and
- `binary`, using lane 0.

The meter surface deletes `none`, `zscore`, `one_hot`, `rank_scaled`, and `masked_value`. It does
not map them, warn about them, or preserve aliases. The broader VFS normalization vocabulary is
unchanged for state that is not exposed as a token.

The compiler joins each environment meter to its bars declaration by name once, derives the range
parameters from the bars bounds, and persists the complete declaration beside each level's
`TokenSpec`. Runtime binds those compiler-owned declarations to live tensor columns and feeds the
resulting spec into the same value normalizer used by other token values. It does not repeat the
configuration join. A missing, duplicate or reordered declaration is a loud error.
Non-finite declared meter values, bounds, rates, normalization parameters and affordance deltas
refuse at validation or compilation; they never enter a token signature.

The executable numeric contract is IEEE float32, not merely finite Python float. Compilation
canonicalizes admitted scalars to the exact runtime value and refuses overflow, authored nonzero
values that underflow to zero, bounds or interior initials that collapse after conversion, an
infinite range span, and non-finite reciprocal/log/cyclical factors. Static features are likewise
canonical float32 values inside `[-1, 1]`; declaration magnitude and element-count descriptors are
saturated before tensorization, and signed meter rates retain their direction.

Each level's compiled `TokenSpec` records the meter's static signature, including the selected
normalization kind and its bounded canonical parameter. Compiled affordance signatures inherit the
same target-meter identity recursively. Therefore a change to `range_type` changes both the emitted
dynamic value and the identity presented to the network. The environment, encoder, population and
token network consume the selected level's `TokenSpec`; none falls back to the compiled universe's
primary-level alias.

## Why this is not backwards compatibility work

The old nine-kind meter surface existed for a deleted ABI and has no users. Keeping dead members
as parseable-but-refused declarations would leave a lying authoring surface; mapping them into new
semantics would be a compatibility shim. Both are deleted. Existing packs are rewritten to the
bounded contract in the same checkpoint.

## Acceptance

1. Distinct admitted declarations produce their mathematically expected live token values,
   including the two-lane cyclical pair.
2. Two otherwise identical meter declarations with different admitted `range_type` values compile
   to different per-level meter signatures and recursive affordance target signatures.
3. Every deleted kind, `clip: false`, and every parameter that is non-finite or loses executable
   meaning in float32 fails loudly at DTO validation or compilation; no alias, translation,
   fallback or deprecated member exists.
4. The environment, encoder, population and token network consume the selected level's `TokenSpec`
   with no fallback to the primary-level alias.
5. Every shipped and test pack compiles under the contracted surface.
6. Focused token/config tests, selected-level population tests, the compiler-pack validator, and the
   full engineering gates pass.

The acceptance evidence is being rerun over the expanded affordance/effect and artifact-coherence
boundary in `PDR-0135`. Milestone 3 remains held until that larger current diff passes the full
default suite and static gates.

## Consequences

- `PDR-0057`'s claim that all nine kinds are authorable is historical for the deleted observation
  ABI, not a current product promise.
- The fixed token schema widens in immutable meter identity and the recursive affordance target
  identity that carries it. `PDR-0135` widens the same static surface again. After the
  exposed-initializer correction, the current L1 full serialization is 4,090 floats rather than
  the intermediate 1,580-float meter-only reading: 3,272,000,000 bytes, or 3,120.4 MiB, per 100,000
  float32 observation pairs. Its `variable_element` count is zero because expression-backed
  exposure is refused until milestone 3 static context can encode executable initializer identity;
  the time variable remains live but unexposed. Milestone 3 moves that static context out of
  replay, so it does not spend the 120-float dynamic replay cap.
- Adding a normalization whose output needs more than two lanes, is unbounded, or depends on other
  worlds requires a superseding representation PDR. It is not a config-only change.
