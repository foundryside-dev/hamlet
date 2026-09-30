# Clean Cut B qualification commands

Working directory: `/tmp/hamlet-declaration-cut-b`. Source: `73f52c20e16e31ddbda9ec4ac637e02840ffb9de`.
Core: `8060ef19b820ddada047570825865b69e6b38b3b`. Python 3.13.1, separate frozen all-extras environment.

The direct-parent command returned **0**:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python scripts/check_declaration_cut_b.py --output runs/differential/declaration-cut-b-73f52c20-parent-qualified --attributions docs/product/evidence/declaration-cut-b/attributions.json
```

All six after JSON products are banked as `qualified-parent-*`; NPZ trajectories remain in the ignored run directory. The before NPZ digests and exact replay parameters are recorded in `before-cpu-traces.json`. This comparator requires those retained trace files. It does not inherit historical observation allowances.

The earlier da035e50 frozen run returned 0 but included an untracked pending acceptance draft (`new_dirty:true`). The final frozen run parked that unpublished draft in `/tmp` and verified the entire repository clean before/after. It returned **0**, with 10 CPU registered divergences and 10 explicit CUDA skips. No source or input bytes changed between runs. The frozen old source and fixtures were never edited or constructed by this command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python - <<'PY_FROZEN'
from pathlib import Path
from townlet.oracle.harness import run_cell_safely,write_report,exit_code,_collect_run_meta,_git
from townlet.oracle.matrix import default_cells
root=Path.cwd();old=Path('/home/john/hamlet/.oracle/oracle-2026-08-17');tag='oracle-2026-08-17'
assert not _git(root,'status','--porcelain')
assert _git(old,'rev-parse','HEAD')==_git(root,'rev-parse',f'{tag}^{{commit}}')
assert not _git(old,'status','--porcelain')
run_id='declaration-cut-b-73f52c20-frozen-clean-cpu';run_dir=root/'runs'/'differential'/run_id
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
PY_FROZEN
```

Review each exact hash attribution in `attributions.json`, isolated scope evidence in `scope-only-hashes.json` and descriptor causes in `canonical-schema-attribution.json`. These causes are reviewed; the comparison script checks values and completeness rather than deriving an authorization from matching field names.
