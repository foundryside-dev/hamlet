# Static epistemic access execution evidence

Implementation and local integration are authorized by the owner's explicit
"execute the plan and commit and merge the changes" instruction. Publication is
outside that authorization. PRD-0004 is accepted at qualified source
`b70fda104e5061ed2735e8b31b7f8f9caaf99f19`; local integration is recorded separately.

## Before bank

Instrumentation commit: `0fdb16eadfa7e4096a238959ba113e92e90fb5af`.
Its product code/configuration is unchanged from the reviewed planning parent
`bd34b5381050509af58e3e5c9cb2c2e7321ec801`.

Capture command (own locked Python 3.13.1 environment, CPU):

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python scripts/check_epistemic_access.py capture --output runs/static-epistemic-access/before
```

The command exited 0 before any product edit. The bank contains 31 compiled cases,
884 identity readings, ten CPU trajectories and eleven reset recipes. It records
exact YAML bytes, input and report digests, trace parameters and retained raw trace
locations. The `before/manifest.json` resolves all report files and the ignored raw
NPZ directory. Loading the relocated bank passed source/input/inventory/digest
validation. CUDA was not executed.

Comparator controls: 46 passed; focused Ruff and Black passed. Controls include
missing/duplicate cases, missing identity readings, substituted recipes, invalid
source/config bytes, altered raw trace digests, missing/stale attribution and changed
observation/action/reward/done streams. No learned-convergence claim is made.

## Qualified evidence

- [Acceptance report](acceptance.md): eight criteria, actual measured outcomes and scope.
- [Accepting decision](../../decisions/0153-static-epistemic-access-accepted-against-prd-0004.md).
- [Commands](qualification-commands.md), [terminal gate receipt](local-gates.json) and `logs/`.
- [Direct-parent result](qualified-parent-report.json) and [frozen CPU result](qualified-frozen-report.json).
- [Exact attribution](attributions.json), [canonical reconstruction](canonical-schema-attribution.json), [frozen/live inputs](frozen-live-inputs.json).
- [Independent policy review](independent-acceptance-policy.json), [intent review](independent-acceptance-intent.json), [raw-evidence reconstruction](final-review-b70fda10.json).
- [Fresh graph](final-caller-closure.json), [AST closure](final-ast-closure.json), [actual-parent permitted-command comparison](real-parent-comparison.json).
- [Banked and retained raw digests](qualified-evidence-digests.json).

Raw trajectories remain in the ignored execution worktree runs directories named
by the manifests. Preserve that worktree while these receipts depend on it. The
acceptance documentation is a descendant of the tested execution source; later
documentation heads are not substituted for the actual qualified source identity.
Local integration receives its own receipt after merge and postmerge checks.
