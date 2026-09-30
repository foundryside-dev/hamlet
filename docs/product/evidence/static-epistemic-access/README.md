# Static epistemic access execution evidence

Implementation and local integration are authorized by the owner's explicit
"execute the plan and commit and merge the changes" instruction. Publication is
outside that authorization. PRD-0004 acceptance remains pending.

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

Implementation, after comparison, frozen CPU qualification, full local gates and
independent acceptance will be recorded separately after execution.
