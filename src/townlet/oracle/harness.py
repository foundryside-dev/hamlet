"""Differential-harness orchestrator: oracle worktree vs working tree.

Usage:
    uv run python -m townlet.oracle.harness            # full CPU matrix
    uv run python -m townlet.oracle.harness --cuda     # + CUDA cells
    uv run python -m townlet.oracle.harness --cell default_curriculum:L1_full_observability

Verdict per cell: AGREE | DIVERGE | HASH_MISMATCH | OLD_SIDE_ERROR |
NEW_SIDE_ERROR | SKIPPED. Exit 0 iff every cell is AGREE or SKIPPED.
No register entry can manifest in an env trace today (DIV-001/002 are
checkpoint-boundary), so any DIVERGE or HASH_MISMATCH is a rebuild defect or a
missing register entry — both findings: docs/oracle/known-divergences.md.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import torch

from townlet.oracle import ORACLE_TAG
from townlet.oracle.matrix import Cell, default_cells
from townlet.oracle.trace_io import CellVerdict, RunParams, compare_traces, load_trace

_ADJUDICATION_NOTE = (
    "v1 is trace-only: no known-divergences entry can manifest in an env trace "
    "(DIV-001/002 are checkpoint-boundary), so every DIVERGE or HASH_MISMATCH is "
    "a rebuild defect or a missing register entry. See docs/oracle/known-divergences.md."
)


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def ensure_worktree(repo_root: Path, tag: str) -> Path:
    """Create (or reuse) the detached oracle worktree at .oracle/<tag>."""
    path = repo_root / ".oracle" / tag
    if (path / "src" / "townlet").is_dir():
        return path
    try:
        _git(repo_root, "worktree", "add", "--detach", str(path), tag)
    except subprocess.CalledProcessError as e:
        raise SystemExit(
            f"cannot create oracle worktree at {path} from tag {tag!r}:\n{e.stderr}\n" f"remedy: git worktree add --detach {path} {tag}"
        ) from e
    return path


def run_side(*, driver: Path, src: Path, params: RunParams, out: Path, repo_root: Path) -> str | None:
    """Run the driver under one side's src. None on success, stderr text on failure."""
    cmd = [
        sys.executable,
        "-P",  # do not prepend the script dir to sys.path (stdlib-shadowing guard)
        str(driver),
        "--pack",
        params.pack,
        "--level",
        params.level,
        "--num-agents",
        str(params.num_agents),
        "--steps",
        str(params.steps),
        "--seed",
        str(params.seed),
        "--device",
        params.device,
        "--out",
        str(out),
    ]
    env = {**os.environ, "PYTHONPATH": str(src)}
    result = subprocess.run(cmd, cwd=repo_root, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        return result.stderr
    return None


def run_cell(*, repo_root: Path, old_src: Path, new_src: Path, cell: Cell, run_dir: Path) -> CellVerdict:
    if cell.params.device == "cuda" and not torch.cuda.is_available():
        return CellVerdict(kind="SKIPPED", cell_id=cell.cell_id, detail={"reason": "cuda unavailable"})
    driver = new_src / "townlet" / "oracle" / "driver.py"
    safe = cell.cell_id.replace(":", "_")
    old_out = run_dir / f"{safe}.old.npz"
    new_out = run_dir / f"{safe}.new.npz"
    for side, src, out, kind in (
        ("old", old_src, old_out, "OLD_SIDE_ERROR"),
        ("new", new_src, new_out, "NEW_SIDE_ERROR"),
    ):
        stderr = run_side(driver=driver, src=src, params=cell.params, out=out, repo_root=repo_root)
        if stderr is not None:
            return CellVerdict(kind=kind, cell_id=cell.cell_id, detail={"side": side, "stderr": stderr})
    return compare_traces(load_trace(old_out), load_trace(new_out), cell_id=cell.cell_id)


def exit_code(verdicts: list[CellVerdict]) -> int:
    if not verdicts:
        return 1  # an empty run proves nothing; refuse to look green
    return 0 if all(v.kind in ("AGREE", "SKIPPED") for v in verdicts) else 1


def write_report(run_dir: Path, verdicts: list[CellVerdict], meta: dict[str, object]) -> Path:
    path = run_dir / "report.json"
    payload = {
        "meta": meta,
        "adjudication_note": _ADJUDICATION_NOTE,
        "verdicts": [{**asdict(v), "register_refs": list(v.register_refs)} for v in verdicts],
    }
    path.write_text(json.dumps(payload, indent=2))
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Differential harness: oracle vs working tree.")
    parser.add_argument("--cuda", action="store_true", help="include CUDA cells")
    parser.add_argument(
        "--cell",
        action="append",
        default=None,
        metavar="PACK:LEVEL",
        help="run only matching cells (pack dir name + level), repeatable",
    )
    parser.add_argument("--oracle-ref", default=ORACLE_TAG)
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[3]
    worktree = ensure_worktree(repo_root, args.oracle_ref)
    cells = list(default_cells(include_cuda=args.cuda))
    if args.cell:
        wanted = set(args.cell)
        cells = [c for c in cells if ":".join(c.cell_id.split(":")[:2]) in wanted]
        if not cells:
            raise SystemExit(f"no matrix cell matches {sorted(wanted)}")

    run_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = repo_root / "runs" / "differential" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    verdicts = []
    for cell in cells:
        verdict = run_cell(
            repo_root=repo_root,
            old_src=worktree / "src",
            new_src=repo_root / "src",
            cell=cell,
            run_dir=run_dir,
        )
        detail = "" if not verdict.detail else f"  {json.dumps(verdict.detail)[:120]}"
        print(f"{verdict.kind:<16} {verdict.cell_id}{detail}")
        verdicts.append(verdict)

    meta: dict[str, object] = {
        "oracle_ref": args.oracle_ref,
        "oracle_commit": _git(repo_root, "rev-parse", f"{args.oracle_ref}^{{commit}}"),
        "new_commit": _git(repo_root, "rev-parse", "HEAD"),
        "new_dirty": bool(_git(repo_root, "status", "--porcelain")),
        "generated": run_id,
    }
    report = write_report(run_dir, verdicts, meta)
    code = exit_code(verdicts)
    print(f"\nreport: {report}\nexit: {code}")
    return code


if __name__ == "__main__":
    sys.exit(main())
