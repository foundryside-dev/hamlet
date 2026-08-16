"""Differential-harness orchestrator: oracle worktree vs working tree.

Usage:
    uv run python -m townlet.oracle.harness            # full CPU matrix
    uv run python -m townlet.oracle.harness --cuda     # + CUDA cells
    uv run python -m townlet.oracle.harness --cell default_curriculum:L1_full_observability

Verdict per cell: AGREE | DIVERGE | HASH_MISMATCH | OLD_SIDE_ERROR |
NEW_SIDE_ERROR | SKIPPED | HARNESS_ERROR | DIVERGED_AS_REGISTERED |
REGISTERED_DIVERGENCE_ABSENT. Exit 0 iff every cell is AGREE, SKIPPED, or
DIVERGED_AS_REGISTERED naming the known-divergences entry its matrix cell
declared (hamlet-56ec575ae2 / PDR-0037).

A cell declares an expected divergence by binding a matrix.RegisteredDivergence
(currently one shape: oracle side crashes leaving no trace, with the declared
signature in the FINAL EXCEPTION TEXT of its stderr; rebuild runs and produces
a valid trace from the declared src root — DIV-003's shape, PDR-0036). The
match is narrow on purpose: an old-side failure without the signature in its
final exception, a non-crash failure (exit 0, no trace), a crash that still
wrote a trace, a new side that also fails (divergence not yet built), and an
old side that runs (stale register entry — REGISTERED_DIVERGENCE_ABSENT) all
still fail the run, as does a run in which every cell was SKIPPED.

DIV-001/002 are checkpoint-boundary and cannot manifest in an env trace, so a
DIVERGE or HASH_MISMATCH with empty register_refs is a rebuild defect or a
missing register entry — both findings: docs/oracle/known-divergences.md.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import torch

from townlet.oracle import ORACLE_TAG
from townlet.oracle.matrix import Cell, default_cells
from townlet.oracle.trace_io import CellVerdict, HarnessError, RunParams, Trace, compare_traces, load_trace

_ADJUDICATION_NOTE = (
    "A cell passes only as AGREE, SKIPPED, or DIVERGED_AS_REGISTERED naming its "
    "known-divergences entry in register_refs. DIVERGED_AS_REGISTERED requires ALL "
    "EITHER shape's conditions. Shape 1 (old-side-crash): old side crashed "
    "(nonzero exit) leaving no trace, with the registered signature inside the "
    "final exception text of its stderr; new side ran and produced a trace valid "
    "for the cell's own params from the declared src root. Shape 2 (hash-only): "
    "both sides ran, EXACTLY the enumerated provenance hashes differ — no more, "
    "no fewer — and every trace stream matches byte-for-byte. "
    "Everything else fails the run — an old-side failure without the signature or "
    "without a traceback, a non-crash failure, a crash that still wrote a trace, a "
    "registered divergence whose new side also fails (not yet built), a registered "
    "divergence that fails to manifest (REGISTERED_DIVERGENCE_ABSENT: stale "
    "register entry), and an all-SKIPPED run. A DIVERGE or HASH_MISMATCH with "
    "empty register_refs is a rebuild defect or a missing register entry. "
    "See docs/oracle/known-divergences.md."
)

# Kept small on purpose: enough of the old side's stderr tail to identify the
# crash in report.json without embedding megabytes of traceback per cell.
_STDERR_TAIL_CHARS = 2000


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def ensure_worktree(repo_root: Path, tag: str) -> Path:
    """Create (or reuse) the detached oracle worktree at .oracle/<tag>.

    Reuse is verified, not assumed: a worktree directory can survive a tag
    rewrite, a manual checkout, or an interrupted run with local edits, and
    silently comparing against that would produce verdicts for the wrong
    commit. On the reuse path this checks the worktree's HEAD against the
    tag's commit and that it is clean; either failure aborts loudly with the
    exact remedy rather than running the harness against stale or dirty
    state.
    """
    path = repo_root / ".oracle" / tag
    remedy = f"git worktree remove --force {path} && git worktree add --detach {path} {tag}"
    if (path / "src" / "townlet").is_dir():
        expected = _git(repo_root, "rev-parse", f"{tag}^{{commit}}")
        actual = _git(path, "rev-parse", "HEAD")
        if actual != expected:
            raise SystemExit(
                f"oracle worktree at {path} is at commit {actual}, but tag {tag!r} "
                f"resolves to {expected} — worktree is stale or was checked out by hand.\n"
                f"remedy: {remedy}"
            )
        status = _git(path, "status", "--porcelain")
        if status:
            raise SystemExit(f"oracle worktree at {path} has local changes:\n{status}\n" f"remedy: {remedy}")
        return path
    try:
        _git(repo_root, "worktree", "add", "--detach", str(path), tag)
    except subprocess.CalledProcessError as e:
        raise SystemExit(
            f"cannot create oracle worktree at {path} from tag {tag!r}:\n{e.stderr}\n" f"remedy: git worktree add --detach {path} {tag}"
        ) from e
    return path


@dataclass(frozen=True)
class SideFailure:
    """One side's failure to produce a trace, with its mode preserved.

    kind distinguishes "crashed" (nonzero exit — stderr is the process's real
    stderr stream) from "no_trace" (exit 0 but no --out written — stderr is a
    HARNESS-SYNTHESIZED diagnostic embedding the out path, stdout and stderr).
    The expectation matcher requires kind == "crashed": collapsing both modes
    into one string let a non-crash satisfy "the oracle crashed with SIG"
    whenever SIG appeared in the synthesized text (adversarial finding,
    reproduced — a driver bug would have been certified as the registered
    divergence)."""

    kind: str  # "crashed" | "no_trace"
    stderr: str


def _final_exception_text(stderr: str) -> str | None:
    """The exception line(s) of the LAST traceback block in stderr, or None.

    The registered-divergence signature is matched against THIS, never the
    whole stream: frame lines (indented) are excluded so a signature cannot
    match a file path or source line, and everything before the final
    traceback is excluded so a signature cannot match a warning, a log line,
    or an earlier handled exception that merely co-occurred with an unrelated
    crash. Multi-line exception messages (unindented continuation lines) are
    kept. None — no traceback at all — never matches: fail closed."""
    idx = stderr.rfind("Traceback (most recent call last):")
    if idx == -1:
        return None
    block = stderr[idx:].split("\n", 1)[1] if "\n" in stderr[idx:] else ""
    lines = [ln for ln in block.splitlines() if ln.strip() and not ln.startswith("  ")]
    return "\n".join(lines) if lines else None


# The oracle side's frozen config root (hamlet-2090c9f16d). Deliberately NOT
# under configs/: scripts/validate_compiler_cli.py walks that tree recursively,
# and a fixture deliberately held at an older schema must not be re-validated
# against the current one.
ORACLE_PACK_ROOT = "oracle_fixtures"

# Build caches, not declarations — excluded from the drift comparison.
_PACK_DRIFT_IGNORE = {".compiled", "__pycache__"}


def _pack_files(pack_dir: Path) -> dict[str, bytes]:
    """Every declaration file in a pack, keyed by path relative to the pack."""
    out: dict[str, bytes] = {}
    if not pack_dir.is_dir():
        return out
    for path in sorted(pack_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(pack_dir)
        if _PACK_DRIFT_IGNORE & set(rel.parts):
            continue
        out[str(rel)] = path.read_bytes()
    return out


def pack_drift(old_pack_root: Path, new_pack_root: Path, logical_pack: str) -> dict[str, list[str]]:
    """Byte-level delta between the pack as the OLD side reads it and as the NEW
    side reads it — the two roots the sides actually resolve, not
    `oracle_fixtures/` vs the repo root by construction. For an oracle run the
    old root IS the frozen fixture tree; for a self-comparison both roots are
    the live tree and the delta is empty for the honest reason
    (hamlet-6f98e38a36).

    Empty dict means the freeze is a provable no-op for this pack. A non-empty
    result is NOT automatically a defect — once a pack-schema divergence is
    declared, the two sides read different inputs by design — but it must never
    be silent, which is the failure mode PDR-0052's reversal trigger names: a
    frozen pack that has rotted into a different universe still compiles, and
    then every cell AGREEs about nothing.
    """
    frozen = _pack_files(old_pack_root / logical_pack)
    live = _pack_files(new_pack_root / logical_pack)
    # No live pack means there is no drift question to answer — the run will
    # fail at compile with a far clearer message than a drift verdict, and
    # synthetic cells (unit tests) legitimately name packs that exist on
    # neither side. "Live pack with no frozen counterpart" IS the defect and
    # is reported below; "neither exists" is a caller error, reported by the
    # compiler.
    if not live:
        return {}
    delta: dict[str, list[str]] = {}
    only_frozen = sorted(set(frozen) - set(live))
    only_live = sorted(set(live) - set(frozen))
    changed = sorted(f for f in set(frozen) & set(live) if frozen[f] != live[f])
    if only_frozen:
        delta["only_in_frozen"] = only_frozen
    if only_live:
        delta["only_in_live"] = only_live
    if changed:
        delta["differing"] = changed
    if not frozen:
        delta["missing_frozen_pack"] = [str(old_pack_root / logical_pack)]
    return delta


def run_side(*, driver: Path, src: Path, params: RunParams, out: Path, repo_root: Path, pack_root: Path) -> SideFailure | None:
    """Run the driver under one side's src AND its own pack root.

    pack_root is per-side because the oracle pins code but not inputs
    (hamlet-2090c9f16d): pack DTOs are extra="forbid", so one new key in a
    live pack crashes every cell on the oracle side for a schema reason.
    params.pack stays logical — compare_traces requires params equality.
    """
    cmd = [
        sys.executable,
        "-P",  # do not prepend the script dir to sys.path (stdlib-shadowing guard)
        str(driver),
        "--pack",
        params.pack,
        "--pack-root",
        str(pack_root),
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
        return SideFailure(kind="crashed", stderr=result.stderr)
    if not out.exists():
        # A driver that exits 0 without writing --out (argparse SystemExit
        # swallowed upstream, a driver bug) must not be treated as success —
        # left uncaught, load_trace raises FileNotFoundError deep inside
        # run_cell instead of yielding a side-error verdict (FIX 4). Kept
        # distinct from "crashed": this synthesized text embeds stdout and
        # harness-authored phrasing, which must never satisfy a registered
        # crash signature.
        return SideFailure(
            kind="no_trace",
            stderr=f"driver exited 0 but did not write --out file {out}\n" f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
    return None


def _validate_lone_trace(trace: Trace, cell: Cell) -> None:
    """Sanity for the matched-divergence path, where there is no old trace to
    compare against: the lone new trace must at least prove it is THIS cell's
    run. A driver that ignored its argv (or wrote truncated arrays) would
    otherwise certify the wrong experiment as a registered divergence."""
    p = cell.params
    if trace.params != p:
        raise HarnessError(
            f"lone new trace for cell {cell.cell_id} carries params {trace.params}, "
            f"but the cell declared {p} — harness/driver bug, not a finding"
        )
    expected_shapes = {
        "obs": (p.steps + 1, p.num_agents),
        "rewards": (p.steps, p.num_agents),
        "dones": (p.steps, p.num_agents),
    }
    actual_shapes = {
        "obs": trace.obs.shape[:2],
        "rewards": trace.rewards.shape,
        "dones": trace.dones.shape,
    }
    if trace.obs.ndim != 3 or actual_shapes != expected_shapes:
        raise HarnessError(
            f"lone new trace for cell {cell.cell_id} has inconsistent array shape(s): "
            f"{actual_shapes} vs declared params {p} — harness/driver bug, not a finding"
        )


def run_cell(
    *, repo_root: Path, old_src: Path, old_pack_root: Path, new_src: Path, cell: Cell, run_dir: Path, run_cuda: bool
) -> CellVerdict:
    """Adjudicate one cell: old side (old_src, old_pack_root) vs new side (new_src, repo_root).

    A side is a code root AND a pack root (hamlet-2090c9f16d, hamlet-6f98e38a36).
    The new side always reads the live tree. The old side reads whatever the
    caller names: `repo_root / ORACLE_PACK_ROOT` for a real oracle run, or
    `repo_root` for a self-comparison — which has no oracle side and so no
    frozen inputs. Required, not defaulted, so a self-comparison cannot be
    written by omission and silently read the frozen fixtures again.
    """
    if cell.params.device == "cuda":
        if not run_cuda:
            return CellVerdict(kind="SKIPPED", cell_id=cell.cell_id, detail={"reason": "cuda not requested"})
        if not torch.cuda.is_available():
            return CellVerdict(kind="SKIPPED", cell_id=cell.cell_id, detail={"reason": "cuda unavailable"})
    driver = new_src / "townlet" / "oracle" / "driver.py"
    safe = cell.cell_id.replace(":", "_")
    old_out = run_dir / f"{safe}.old.npz"
    new_out = run_dir / f"{safe}.new.npz"
    expected = cell.expected

    new_pack_root = repo_root

    drift = pack_drift(old_pack_root, new_pack_root, cell.params.pack)
    if drift and not cell.declares_pack_divergence:
        # Undeclared drift: the oracle would be certifying a universe nobody
        # authors. Fail the cell rather than compare two different worlds.
        return CellVerdict(
            kind="HARNESS_ERROR",
            cell_id=cell.cell_id,
            detail={
                "reason": "frozen oracle pack differs from the live pack with no declared divergence",
                "pack": cell.params.pack,
                "frozen_root": str(old_pack_root),
                "delta": drift,
                "fix": (
                    "Either re-freeze the fixture (the change was not a schema divergence) or declare "
                    "the divergence on this cell and register it in docs/oracle/known-divergences.md."
                ),
            },
        )

    old_failure = run_side(driver=driver, src=old_src, params=cell.params, out=old_out, repo_root=repo_root, pack_root=old_pack_root)
    if old_failure is not None:
        # The registered shape (DIV-003 / PDR-0036) is "the oracle side fails
        # to produce a trace, crashing with the registered signature". Every
        # conjunct is checked; each miss stays red with its own reason
        # (hamlet-56ec575ae2: "the match must be narrow"):
        #   - kind == "crashed": a no_trace failure is a driver/harness bug,
        #     and its synthesized text (embedding stdout and harness phrasing)
        #     must never satisfy a crash signature;
        #   - not old_out.exists(): a side that wrote a complete trace and
        #     THEN died did not "fail to produce a trace" — suppressing that
        #     would discard a comparable trace;
        #   - signature ∈ final exception text only: co-occurrence anywhere
        #     else in the stream (warnings, frame paths, earlier handled
        #     errors) certifies nothing about WHY the process died.
        exception_text = _final_exception_text(old_failure.stderr) if old_failure.kind == "crashed" else None
        matched = (
            expected is not None
            and old_failure.kind == "crashed"
            and not old_out.exists()
            and exception_text is not None
            and expected.old_stderr_substring in exception_text
        )
        if not matched:
            detail: dict[str, object] = {"side": "old", "failure_kind": old_failure.kind, "stderr": old_failure.stderr}
            if expected is not None:
                if old_failure.kind != "crashed":
                    status = "old side failed without crashing (exited 0, wrote no trace) — not the registered crash shape"
                elif old_out.exists():
                    status = "old side crashed but STILL wrote a trace — not the registered fails-to-produce-a-trace shape"
                elif exception_text is None:
                    status = "old side crashed with no Python traceback on stderr — cannot anchor the registered signature"
                else:
                    status = (
                        "old side crashed WITHOUT the registered signature in its final exception — "
                        "unmatched failure, not the registered divergence"
                    )
                detail["expectation"] = {
                    "register_ref": expected.register_ref,
                    "expected_substring": expected.old_stderr_substring,
                    "status": status,
                }
            return CellVerdict(kind="OLD_SIDE_ERROR", cell_id=cell.cell_id, detail=detail)
        assert expected is not None and exception_text is not None  # narrowed by `matched`

        # The registered old-side crash. NOT yet a pass: pre-knockdown BOTH
        # sides crash, and the old side runs first — passing on the old crash
        # alone would certify a knockdown that never happened. The rebuild
        # must actually RUN and produce a valid trace to prove the divergence.
        new_failure = run_side(driver=driver, src=new_src, params=cell.params, out=new_out, repo_root=repo_root, pack_root=new_pack_root)
        if new_failure is not None:
            return CellVerdict(
                kind="NEW_SIDE_ERROR",
                cell_id=cell.cell_id,
                detail={
                    "side": "new",
                    "failure_kind": new_failure.kind,
                    "stderr": new_failure.stderr,
                    "expectation": {
                        "register_ref": expected.register_ref,
                        "status": (
                            "old side failed as registered, but the new side failed too — " "the registered divergence is not (yet) built"
                        ),
                    },
                },
            )
        new_trace = load_trace(new_out)
        _validate_lone_trace(new_trace, cell)
        # FIX 5 analog for the lone-trace path: the compare path proves
        # injection by old != new code_root, but here no old trace exists, so
        # the new trace must prove it ran the declared src root outright.
        if Path(new_trace.code_root).resolve() != new_src.resolve():
            raise HarnessError(
                f"lone new trace for cell {cell.cell_id} reports code_root "
                f"{new_trace.code_root!r}, but the declared new src is {new_src} — "
                f"PYTHONPATH injection did not take effect on the new side"
            )
        return CellVerdict(
            kind="DIVERGED_AS_REGISTERED",
            cell_id=cell.cell_id,
            detail={
                "register_ref": expected.register_ref,
                "matched_substring": expected.old_stderr_substring,
                "old_final_exception": exception_text[:_STDERR_TAIL_CHARS],
                "old_stderr_tail": old_failure.stderr[-_STDERR_TAIL_CHARS:],
                "new_code_root": new_trace.code_root,
            },
            register_refs=(expected.register_ref,),
        )

    new_failure = run_side(driver=driver, src=new_src, params=cell.params, out=new_out, repo_root=repo_root, pack_root=new_pack_root)
    if new_failure is not None:
        detail = {"side": "new", "failure_kind": new_failure.kind, "stderr": new_failure.stderr}
        if expected is not None:
            detail["expectation"] = {
                "register_ref": expected.register_ref,
                "status": "registered OLD-side crash did not manifest (old side ran), and the new side failed",
            }
        return CellVerdict(kind="NEW_SIDE_ERROR", cell_id=cell.cell_id, detail=detail)

    old_trace = load_trace(old_out)
    new_trace = load_trace(new_out)

    # PYTHONPATH injection guard (FIX 5): nothing else asserts the injection
    # actually took effect. If it silently failed, both subprocesses would
    # import the SAME working-tree townlet regardless of which src root was
    # declared — every cell would trivially AGREE and the whole differential
    # run's evidence would be a false AGREE. Gated on old_src != new_src so
    # the deliberate self-comparison test (old_src == new_src) is unaffected.
    if old_src != new_src and old_trace.code_root == new_trace.code_root:
        return CellVerdict(
            kind="HARNESS_ERROR",
            cell_id=cell.cell_id,
            detail={
                "reason": "PYTHONPATH injection did not take effect — both sides ran the same code",
                "code_root": old_trace.code_root,
            },
        )

    verdict = compare_traces(old_trace, new_trace, cell_id=cell.cell_id, hash_divergence=cell.hash_divergence)
    if expected is not None:
        # The old side RAN on a cell registered to crash: the registered
        # divergence did not manifest. This must fail even — especially — when
        # the traces AGREE: an expectation that never fires is a stale
        # register entry, and letting it pass would leave suppression
        # machinery armed with nothing to suppress (PDR-0037 reversal
        # trigger 3). The underlying comparison is carried as evidence, never
        # as the verdict: a trace-level DIVERGE here is NOT the registered
        # old-side-crash divergence and must not be passed off as it.
        return CellVerdict(
            kind="REGISTERED_DIVERGENCE_ABSENT",
            cell_id=cell.cell_id,
            detail={
                "register_ref": expected.register_ref,
                "underlying_kind": verdict.kind,
                "underlying_detail": verdict.detail,
                "reason": (
                    "old side ran; the registered old-side crash did not manifest — "
                    "the register entry is stale or the surface regressed to agreement"
                ),
            },
        )
    return verdict


def run_cell_safely(
    *, repo_root: Path, old_src: Path, old_pack_root: Path, new_src: Path, cell: Cell, run_dir: Path, run_cuda: bool
) -> CellVerdict:
    """run_cell, contained (FIX 4).

    run_cell is called once per matrix cell in main()'s loop, with
    write_report deferred until after the whole loop. Without containment,
    any escaping exception (HarnessError on a params mismatch,
    FileNotFoundError from load_trace if a driver exits 0 without writing
    --out, anything else) aborts the entire run and destroys report.json for
    the cells already computed. An exception here becomes a HARNESS_ERROR
    verdict for just this cell instead.
    """
    try:
        return run_cell(
            repo_root=repo_root,
            old_src=old_src,
            old_pack_root=old_pack_root,
            new_src=new_src,
            cell=cell,
            run_dir=run_dir,
            run_cuda=run_cuda,
        )
    except Exception as e:  # noqa: BLE001 — containment boundary, see docstring
        return CellVerdict(
            kind="HARNESS_ERROR",
            cell_id=cell.cell_id,
            detail={"exception_type": type(e).__name__, "message": str(e)},
        )


def _collect_run_meta(repo_root: Path, oracle_ref: str, run_id: str) -> dict[str, object]:
    """Commit-level provenance for report.json — gathered once per run, not
    per trace (a trace's own metadata carries only params/hashes/code_root,
    see trace_io.py). A separate function, called by main() BEFORE the cell
    loop, so a git failure here (check=True) aborts at pre-flight instead of
    destroying every verdict run_cell_safely already computed (FIX 4)."""
    return {
        "oracle_ref": oracle_ref,
        "oracle_commit": _git(repo_root, "rev-parse", f"{oracle_ref}^{{commit}}"),
        "new_commit": _git(repo_root, "rev-parse", "HEAD"),
        "new_dirty": bool(_git(repo_root, "status", "--porcelain")),
        "generated": run_id,
    }


def exit_code(verdicts: list[CellVerdict]) -> int:
    """Pass iff every cell is AGREE/SKIPPED with EMPTY refs, or
    DIVERGED_AS_REGISTERED with NON-EMPTY refs (hamlet-56ec575ae2).

    Belt-and-braces in both directions: a matched kind that names no register
    entry, and a clean kind that somehow carries one, are both contract
    breaches — refuse to look green on either. Still an allowlist: any kind
    not named here (including REGISTERED_DIVERGENCE_ABSENT and anything new)
    fails."""
    if not verdicts:
        return 1  # an empty run proves nothing; refuse to look green
    if all(v.kind == "SKIPPED" for v in verdicts):
        return 1  # a run that executed nothing proves nothing either — same rule
    for v in verdicts:
        if v.kind in ("AGREE", "SKIPPED"):
            if v.register_refs:
                return 1  # refs may be populated ONLY by the expectation matcher
            continue
        if v.kind == "DIVERGED_AS_REGISTERED":
            if not v.register_refs:
                return 1  # a matched divergence must name its register entry
            continue
        return 1
    return 0


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
    cells = list(default_cells())
    if args.cell:
        wanted = set(args.cell)
        cells = [c for c in cells if ":".join(c.cell_id.split(":")[:2]) in wanted]
        if not cells:
            raise SystemExit(f"no matrix cell matches {sorted(wanted)}")

    run_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = repo_root / "runs" / "differential" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    # Gathered BEFORE the cell loop, not after (FIX 4): a git failure here
    # (index.lock contention, a concurrent git operation — exactly what the
    # "not safe to run concurrently with itself" note warns about) would
    # otherwise destroy every verdict already computed by run_cell_safely,
    # reintroducing the all-or-nothing failure mode containment was built to
    # eliminate. Gathered up front, a git failure aborts at pre-flight
    # instead, before any cell executes — consistent with the harness's
    # other pre-flight failures — and it means new_dirty records the tree
    # the cells actually ran against.
    meta = _collect_run_meta(repo_root, args.oracle_ref, run_id)

    verdicts = []
    for cell in cells:
        verdict = run_cell_safely(
            repo_root=repo_root,
            old_src=worktree / "src",
            old_pack_root=repo_root / ORACLE_PACK_ROOT,  # the oracle side reads FROZEN inputs
            new_src=repo_root / "src",
            cell=cell,
            run_dir=run_dir,
            run_cuda=args.cuda,
        )
        detail = "" if not verdict.detail else f"  {json.dumps(verdict.detail)[:120]}"
        print(f"{verdict.kind:<16} {verdict.cell_id}{detail}")
        verdicts.append(verdict)

    report = write_report(run_dir, verdicts, meta)
    code = exit_code(verdicts)
    print(f"\nreport: {report}\nexit: {code}")
    return code


if __name__ == "__main__":
    sys.exit(main())
