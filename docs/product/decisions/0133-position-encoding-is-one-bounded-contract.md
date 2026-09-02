# PDR-0133 — Position encoding is one bounded contract

Date: 2026-08-31   Status: **accepted** (milestone 1 engineering checkpoint)
Author: Codex (standing product owner)
Related: `PDR-0132`, `hamlet-6a4a6596bd`

## Context

The token cut made substrate position width independent of `observation_encoding`, but left the
old `relative` / `scaled` / `absolute` selector in config DTOs, factories and substrate
constructors. The selector was therefore inert at schema construction while still selecting raw,
potentially unbounded egocentric deltas in part of the runtime. `div003_scaled` had become a
byte-identical differential cell that claimed evidence for an axis it could no longer observe.

This is a pre-release product with no users. Preserving an obsolete spelling, constructor
argument, configuration value or transition path would create two contracts where the product
needs one.

## The call

There is one spatial encoding contract:

- absolute positions are normalized per substrate axis to `[0, 1]`;
- egocentric deltas are normalized per substrate axis to `[-1, 1]`; and
- aspatial substrates carry no position coordinates.

The `observation_encoding` field is deleted from the current DTOs, factories, constructors,
documentation, examples and shipped packs. Supplying it is an extra-field validation error. Raw
grid deltas and the three mode branches are deleted; there is no alias, defaulted legacy
selector, compatibility shim or migration reader.

`div003_scaled` is replaced by `boundary_wrap`, a real differential cell whose declared axis is
wrap-boundary behaviour. The copied packs under `oracle_fixtures/` remain byte-oriented inputs to
the pinned old executable and may therefore contain the old key. They are not loadable current
configuration and are protected by pack-drift tests; retaining old oracle evidence does not
retain an old product API. This explicitly narrows `PDR-0132`'s instruction to delete the key from
"fixtures": executable current fixtures are clean; immutable old-side oracle inputs stay frozen.

## Evidence

- Red-first regression: 12 failures proved that three DTOs and eight constructors still exposed
  the old surface and that the spatial delta contract was not pinned. The same file now has 12
  passing cases.
- Focused substrate/config/environment slice: 427 passed, 6 skipped.
- Oracle matrix and substrate seam: 45 passed.
- Full default suite: 3,307 passed, 11 skipped, 84% coverage.
- Shipped-pack compiler validation passed, including the expected-failure fixtures.
- Repository gates passed: Ruff, Black, mypy over 173 source files, the no-defaults guard and
  `git diff --check`.
- Literal census: zero references to `observation_encoding` remain in current runtime code,
  scripts, shipped configs or ordinary tests. The only executable current-tree occurrence is the
  regression that proves rejection.

## Consequences

The first of `PDR-0132`'s five milestones is complete. The next milestone restores declared meter
`range_type` semantics into token live values; it does not reopen position encoding.

If a future engineering requirement genuinely needs a different position representation, it
must introduce one replacement ABI with new measured constraints. It does not revive this
selector or add a dual path.
