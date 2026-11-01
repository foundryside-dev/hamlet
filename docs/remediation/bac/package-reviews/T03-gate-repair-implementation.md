# T03 gate assertion repair receipt

Status: **target frozen; scoped verification passed; fresh independent repair review and root full-gate rerun pending.**

## Cause and bounded repair

In existing `/workspace/hamlet`, changed only line155 of
`tests/test_townlet/unit/universe/test_compiled_artifact_required_fields.py`:
exact expected schema `"1.40"` -> `"1.41"`.
All test nodes, strict required-field assertions, fixtures and production bytes remain unchanged.

Read AGENTS and T03 implementation/review receipts as references. The compiled source declares1.41 (line173), adds required `effective_run` (line203), explicitly dispatches known1.40 fields (lines555–558), derives honest current provenance for1.40 (lines699–702), and refuses unknown schemas (line836). This matches both receipts: the reviewed additive schema makes the old exact pin stale.

## Two-file implementation/test inventory

| Access | File | Lines | SHA256 before | SHA256 frozen |
| --- | --- | ---: | --- | --- |
| read-only | src/townlet/universe/compiled.py | 1615 | 494f9676c236349f12c875c82dde821a85a3bf5077cae15654c78e8ac1630710 | same |
| modify | tests/test_townlet/unit/universe/test_compiled_artifact_required_fields.py | 285 | b536b92588fe7b87b81dc79effc75aa6630718de293349aad1ae83d19dc86933 | cd99a009b217cade1e9896fa4b0e926dadb6b4657ac41c05fd6f89760f963730 |

Total **1900 lines**, exactly the authorized two-file inventory. No other implementation/test/helper source inspected. Runtime imports and ordinary existing data fixtures were used without opening helper source. Verification used inline Python, not new repository helper files.

## Exact executions and results

All commands ran from `/workspace/hamlet`, with installed tools and prefix:

```sh
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/hamlet/src .venv/bin/python - <<'PY'
# inline harness below, with the exact args listed next
PY
```

The harness sets `torch.set_num_threads(1)`, records identity before/after, and calls `pytest.main(args)`. Exact pytest argv:

```text
RED:
["--no-cov", "-p", "no:cacheprovider", "-q", "tests/test_townlet/unit/universe/test_compiled_artifact_required_fields.py::test_scope_surface_cut_bumps_exact_artifact_schema"]
GREEN exact node:
["--no-cov", "-p", "no:cacheprovider", "-q", "tests/test_townlet/unit/universe/test_compiled_artifact_required_fields.py::test_scope_surface_cut_bumps_exact_artifact_schema"]
GREEN module:
["--no-cov", "-p", "no:cacheprovider", "-q", "tests/test_townlet/unit/universe/test_compiled_artifact_required_fields.py"]
```

- RED before edit: **1 failed in0.07s**, exit1, exactly `assert '1.41' == '1.40'` at line155. Log `/tmp/bac-T03-gate-repair-red.log`.
- GREEN exact node: **1 passed in0.04s**, exit0. Log `/tmp/bac-T03-gate-repair-green-node.log`.
- GREEN module: **124 passed in9.32s**, exit0. Log `/tmp/bac-T03-gate-repair-green-module.log`.
- Scoped commands below each exited0, with separate before/after identity boundaries, in `/tmp/bac-T03-gate-repair-static.log`:

```sh
.venv/bin/ruff check tests/test_townlet/unit/universe/test_compiled_artifact_required_fields.py
.venv/bin/black --check tests/test_townlet/unit/universe/test_compiled_artifact_required_fields.py
git diff --check -- tests/test_townlet/unit/universe/test_compiled_artifact_required_fields.py
```

An initial wrapper construction misplaced shell redirection after the heredoc terminator; Python exited with SyntaxError before imports/test execution. The corrected command redirected before the heredoc. That harness error is not RED evidence.

Identity at every completed test/static before/after boundary: HEAD `049e305df42392373a52c9eb76552abbd74a5b2b`; actual import `/workspace/hamlet/src/townlet/__init__.py`; Torch threads1; source/test hashes as above. Each run asserts identical before/after records, including Git status and index SHA256 `06b62484dda2c9edf442ca212bc0b55c957e99c0486d166b5a00548b48e18818`. RED has the original test hash; all green/static runs have frozen test hash. Index bytes stayed unchanged, with the original four staged T03 paths still root-owned. Final unstaged diff is exactly the one-line assertion change.

## Inline test harness

The exact executed harness is reproduced below; use each exact argv above as `args`. Each run redirected its stdout/stderr to its named log before `<<'PY'`.

```python
import hashlib, json, os, subprocess, sys
from pathlib import Path
import torch, townlet
torch.set_num_threads(1)
root = Path.cwd()
paths = ["src/townlet/universe/compiled.py", "tests/test_townlet/unit/universe/test_compiled_artifact_required_fields.py"]
def identity():
    result = {"head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(), "import": townlet.__file__, "torch_threads": torch.get_num_threads(), "sha256": {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths}, "index_sha256": hashlib.sha256((root / ".git/index").read_bytes()).hexdigest(), "status": subprocess.check_output(["git", "status", "--porcelain"], text=True)}
    assert result["head"] == "049e305df42392373a52c9eb76552abbd74a5b2b"
    assert result["import"] == "/workspace/hamlet/src/townlet/__init__.py"
    assert result["torch_threads"] == 1
    assert result["sha256"][paths[0]] == "494f9676c236349f12c875c82dde821a85a3bf5077cae15654c78e8ac1630710"
    return result
before = identity()
print("BEFORE " + json.dumps(before), flush=True)
import pytest
args = <exact argv above>
print("PYTEST_ARGS " + json.dumps(args), flush=True)
code = pytest.main(args)
after = identity()
print("AFTER " + json.dumps(after), flush=True)
assert before == after
print("PYTEST_EXIT " + str(int(code)), flush=True)
sys.exit(code)
```

No full repository suite, Git stage/commit, branch/worktree/checkout/repository copy, delegation or new tests occurred. No production rollback, relaxed comparison, skip, fixture mutation, rule/plan/progress change, or original failed `/tmp/bac-verify-T03-4175e78397`/backup modification occurred. This receipt does not claim repository green or final T03 acceptance.

