# Qualification commands

Execution source: `b70fda104e5061ed2735e8b31b7f8f9caaf99f19`, clean
`/tmp/hamlet-static-epistemic-access` on `feat/static-epistemic-access`.
An isolated environment was installed with `uv sync --all-extras --locked`:
Python 3.13.1, Torch 2.11.0+cu130, Pydantic 2.13.4. No parent environment was repurposed.
The commands below were executed before accepting documentation was added; retain
that distinction when reproducing a clean-source comparison.

## Local gates

```bash
.venv/bin/ruff check
.venv/bin/black --check .
.venv/bin/mypy src
.venv/bin/python scripts/no_defaults_lint.py src --whitelist .defaults-whitelist.txt
.venv/bin/python scripts/validate_compiler_cli.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -m pytest
```

Actual terminal statuses, counts and logs are in [local-gates.json](local-gates.json).
The full suite used the repository's normal default pytest selection and coverage;
no optional CUDA execution or learned-policy qualification is implied.

## Direct-parent qualification

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python scripts/check_epistemic_access.py compare --before docs/product/evidence/static-epistemic-access/before --output runs/static-epistemic-access/qualified-b70fda10 --attributions docs/product/evidence/static-epistemic-access/attributions.json
```

The comparator validates the retained before manifest/raw digests before comparing.
It rejects changed permitted streams, stale or unexplained identities and reset
differences. Outputs are retained both in the bank and ignored run directory.
Use a new output directory when reproducing.

## Frozen CPU qualification

The existing clean frozen worktree is used read-only. It is not constructed,
installed into, indexed or modified by this invocation. `oracle_fixtures` is the
unchanged frozen input pack root in the live source checkout.
Save the following as a temporary Python file, then execute it from the clean
source worktree with `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python <file>`.
Change only the run id for a new run; the directory must not already exist.

```python
from pathlib import Path
from townlet.oracle.harness import run_cell_safely,write_report,exit_code,_collect_run_meta,_git
from townlet.oracle.matrix import default_cells
root=Path.cwd();old=Path('/home/john/hamlet/.oracle/oracle-2026-08-17');tag='oracle-2026-08-17'
assert not _git(root,'status','--porcelain')
assert _git(old,'rev-parse','HEAD')==_git(root,'rev-parse',f'{tag}^{{commit}}')
assert not _git(old,'status','--porcelain')
run_id='static-epistemic-b70fda10-frozen-clean-cpu';run_dir=root/'runs'/'differential'/run_id
run_dir.mkdir(parents=True,exist_ok=False)
meta=_collect_run_meta(root,tag,run_id);meta['oracle_worktree']=str(old)
meta['oracle_access']='existing verified clean worktree; no writes or construction'
vs=[]
for cell in default_cells():
 v=run_cell_safely(repo_root=root,old_src=old/'src',old_pack_root=root/'oracle_fixtures',new_src=root/'src',cell=cell,run_dir=run_dir,run_cuda=False,scripted=cell.scripted_actions)
 print(v.kind,v.cell_id,flush=True);vs.append(v)
write_report(run_dir,vs,meta)
assert not _git(old,'status','--porcelain')
assert not _git(root,'status','--porcelain')
raise SystemExit(exit_code(vs))
```

The run returns the public harness's aggregate exit code, rather than treating the
existence of a report as success. All ten CPU cells are DIVERGED_AS_REGISTERED;
ten CUDA cells explicitly skip. Independent evidence review recomputed the CPU
verdicts and parent stream/reset checks from retained raw NPZ arrays.

## Closure and evidence

A fresh isolated Loomweave extraction was made with:

```bash
loomweave worktree analyze /tmp/hamlet-static-epistemic-access
```

Its returned SEIs were used for entity/caller queries; the retained graph receipt
states extractor exclusions. The supplemental syntactic inventory and manual
receiver reconciliation retain all production sites and the unresolved candidates.
Actual parent command parity uses fresh, source-isolated processes for the unchanged
bd34b538 parent and qualified b70fda10 source, with output and full Torch RNG bytes.
Those reports disclose actual import origins and source digests.

No push, PR, hosted CI, browser or convergence command is part of this acceptance.
Authorized local merge and postmerge checks are recorded separately.
