# Cut B direct-parent evidence comparator

`scripts/check_declaration_cut_b.py` compares the 31-case / 884-reading parent
inventory at `599cad15` with current source and declarations. Its reports are
separate from the existing fixed-oracle matrix.

Run from the isolated worktree, after the implementation checkpoint is committed:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python scripts/check_declaration_cut_b.py --output runs/differential/declaration-cut-b-parent-measurement
```

This first measurement intentionally exits nonzero when hashes or reset readings
changed without attribution. The report is evidence for causal review, not a
permission generator. Inspect every `after-census.json` product path and the
`after-inputs.json` complete live-input/frozen-input inventories. Bisect scope-only
and canonical-variable changes independently before authoring exact attributions.

An attribution file has the following shape (values are examples, not allowances):

```json
{
  "entries": [
    {
      "kind": "hash",
      "pack": "configs/example",
      "level": "L0",
      "path": "/all_levels.L0.variable_schema_hash",
      "before_present": true,
      "after_present": true,
      "before": "exact measured before hash",
      "after": "exact measured after hash",
      "cause": "canonical lifetime/initial-value lowering; named product diffs",
      "causing_commit": "exact causing commit",
      "register_ref": "DIV-014"
    }
  ]
}
```

`kind` is `hash`, `trace_hash` or `reset`; the pack, level and structural path
identify one reading. Both presence flags are required. Omit a `before`/`after`
value only when that side was absent. The attribution requires exact before/after
values, an explicit cause, a causing commit and a register reference. Stale or
duplicate entries fail, as do numeric/bool substitutions. A census hash and the
selected-level trace hash are distinct readings and require separate entries.
No wildcard or field-wide allowance exists.

Use a fresh output directory for qualification:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python scripts/check_declaration_cut_b.py --output runs/differential/declaration-cut-b-parent-qualified --attributions docs/product/evidence/declaration-cut-b/attributions.json
```

Each after trace replays the exact banked parent action array. The comparator
verifies the banked NPZ file digest, trace parameters/hashes and each array's
shape/dtype/byte digest before running it. All four after streams must match the
parent bytes, including signed zeros and NaN payloads. No historical DIV-008
observation suppression applies here. A driver error, stream mismatch, missing
attribution or stale attribution keeps qualification false and exit nonzero.

`--skip-cpu` is a diagnostic census mode that always exits nonzero and records
`qualified: false`; it cannot establish behavioral acceptance. The helper records
current HEAD and working-tree status. A product acceptance claim additionally
requires a clean source/config/test checkpoint; a working-tree run remains a
measurement and does not become clean-tip evidence merely because HEAD is present.

The eleven reset/step/reset censuses are rerun with their original seeds, lane
count and action indices. They measure existing lane state and permit no implicit
reset change. This is deliberately narrower than proving the full lifetime
contract, which requires its own mutating config-in acceptance tests.

The existing frozen matrix must also run with the verified existing clean
`oracle-2026-08-17` worktree. Preserve all oracle fixtures. Register B under the next
unused DIV entry with individually bisected causes; do not widen or repurpose older
output declarations. Typed binding scope should change only variable-token
observation identity and its composite, preserving layout where scope does not
alter emitted transport. Canonical variable restructuring may independently move
`environment_hash`; PDR-0147 requires that cause be isolated and registered.
