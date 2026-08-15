# Frozen oracle inputs

**Do not edit these packs to make a test pass, and do not delete them as duplicates.**
They are the differential harness's *frozen inputs*, the input-side twin of the pinned
`.oracle/<tag>` code worktree. Closes `hamlet-2090c9f16d`; rationale in `PDR-0052`.

## Why this directory exists

The oracle pinned **code** at `oracle-2026-08-13` but resolved `--pack` against the **live**
tree — `harness.py::run_side` ran both sides with `cwd=repo_root`, varying only `PYTHONPATH`.
Every pack DTO is `ConfigDict(extra="forbid")`, so a single new key in a live pack made the
frozen oracle reject it at Stage 1 and **all 16 cells crashed for a schema reason** instead of
yielding a verdict. Measured against the frozen `src`:

```
environment.meters.0.normalization
  Extra inputs are not permitted [type=extra_forbidden]
```

WS-4's whole purpose is changing the authoring surface, so every future authoring change would
have hit this identically — the harness would go blind exactly when it was needed most.

## How it works

Each side resolves the **same logical `--pack`** against its **own `--pack-root`**: the oracle
side reads this directory, the new side reads the repo root. `RunParams.pack` stays logical
because `compare_traces` requires params equality across sides; the resolved root is recorded in
the trace beside `code_root`, where it is reported but never compared.

## The rule that keeps this honest

Freezing inputs introduces a failure worse than the bug it fixes, because it is **silent and
green**: a frozen pack that rots into a different universe still compiles, and then every cell
AGREEs about nothing (`PDR-0052`'s reversal trigger).

So: **frozen and live must be byte-identical unless the matrix cell declares a divergence.**
Undeclared drift fails the cell with `HARNESS_ERROR`. Today every pack here is an exact copy, so
the freeze is a provable no-op — pinned by `test_the_freeze_is_a_provable_no_op_today`.

Setting `Cell.pack_divergence` is the **recorded human judgement** that the two packs still
describe the same universe in two schemas. It is never inferred from the fact that they differ,
and it does not bless whatever the comparison then finds — a declared *input* delta and an
accepted *output* delta are two separate decisions, the second belonging in
`docs/oracle/known-divergences.md`.

## When you change a live pack

1. If it is not a schema change, re-freeze: copy the live pack over its fixture here.
2. If it **is** a schema change, leave the fixture at the old schema, set `pack_divergence` on
   the affected cells, and register the entry. That is the case this directory exists for.

## Why not under `configs/`

`scripts/validate_compiler_cli.py` walks `configs/` recursively (it is the CI config-validation
gate). A fixture deliberately held at an older schema must not be re-validated against the
current one — and the packs must not be double-counted. Pinned by
`test_fixtures_live_outside_configs`.
