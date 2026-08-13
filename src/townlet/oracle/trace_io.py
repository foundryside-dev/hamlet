"""Trace file format for the differential harness.

Named trace_io, NOT trace: the driver runs by file path, and a sibling
trace.py would shadow stdlib `trace` for any interpreter with this directory
on sys.path.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

TRACE_FORMAT_VERSION = 1


@dataclass(frozen=True)
class RunParams:
    """Everything that identifies one differential run of one side."""

    pack: str
    level: str
    num_agents: int
    steps: int
    seed: int
    device: str


@dataclass(frozen=True)
class Trace:
    """One side's recorded env-step trace plus its compiled provenance hashes."""

    params: RunParams
    hashes: dict[str, str | None]
    obs: np.ndarray  # (steps + 1, num_agents, obs_dim) float32; index 0 is reset
    rewards: np.ndarray  # (steps, num_agents) float32
    dones: np.ndarray  # (steps, num_agents) bool


def save_trace(path: Path, trace: Trace) -> None:
    meta = {
        "format_version": TRACE_FORMAT_VERSION,
        "params": asdict(trace.params),
        "hashes": trace.hashes,
    }
    np.savez_compressed(
        path,
        obs=trace.obs,
        rewards=trace.rewards,
        dones=trace.dones,
        meta=np.array(json.dumps(meta)),
    )


def load_trace(path: Path) -> Trace:
    with np.load(path, allow_pickle=False) as data:
        meta = json.loads(str(data["meta"]))
        if meta["format_version"] != TRACE_FORMAT_VERSION:
            raise ValueError(f"trace {path} has format_version {meta['format_version']}; " f"this harness reads {TRACE_FORMAT_VERSION}")
        return Trace(
            params=RunParams(**meta["params"]),
            hashes=dict(meta["hashes"]),
            obs=data["obs"],
            rewards=data["rewards"],
            dones=data["dones"],
        )


class HarnessError(RuntimeError):
    """A defect in the harness or its invocation — not a differential finding."""


@dataclass(frozen=True)
class CellVerdict:
    """The harness's judgement for one matrix cell.

    register_refs is the binding point for known-divergences entries; empty in
    v1 because no current entry can manifest in an env trace (DIV-001/002 are
    checkpoint-boundary). Any DIVERGE or HASH_MISMATCH is therefore a rebuild
    defect or a missing register entry — see docs/oracle/known-divergences.md.
    """

    kind: str  # AGREE | DIVERGE | HASH_MISMATCH | OLD_SIDE_ERROR | NEW_SIDE_ERROR | SKIPPED
    cell_id: str
    detail: dict[str, object]
    register_refs: tuple[str, ...] = ()


_MAX_REPORTED_INDICES = 10


def _stream_steps(trace: Trace) -> list[tuple[int, str, np.ndarray]]:
    """Trace arrays flattened into adjudication order: reset obs, then per-step."""
    entries: list[tuple[int, str, np.ndarray]] = [(0, "obs", trace.obs[0])]
    for t in range(trace.params.steps):
        entries.append((t, "dones", trace.dones[t]))
        entries.append((t, "rewards", trace.rewards[t]))
        entries.append((t + 1, "obs", trace.obs[t + 1]))
    return entries


def compare_traces(old: Trace, new: Trace, cell_id: str) -> CellVerdict:
    if old.params != new.params:
        raise HarnessError(
            f"trace params differ between sides for cell {cell_id}: " f"{old.params} vs {new.params} — harness bug, not a finding"
        )

    mismatched = {
        name: {"old": old.hashes.get(name), "new": new.hashes.get(name)}
        for name in sorted(set(old.hashes) | set(new.hashes))
        if old.hashes.get(name) != new.hashes.get(name)
    }
    if mismatched:
        return CellVerdict(kind="HASH_MISMATCH", cell_id=cell_id, detail={"mismatched": mismatched})

    for (old_step, old_stream, old_arr), (_, _, new_arr) in zip(_stream_steps(old), _stream_steps(new), strict=True):
        if np.array_equal(old_arr, new_arr):
            continue
        diff_indices = np.argwhere(old_arr != new_arr)
        detail: dict[str, object] = {
            "step": old_step,
            "stream": old_stream,
            "indices": [list(map(int, idx)) for idx in diff_indices[:_MAX_REPORTED_INDICES]],
            "diff_count": int(len(diff_indices)),
        }
        if old_arr.dtype != np.bool_:
            detail["max_abs_diff"] = float(np.max(np.abs(old_arr.astype(np.float64) - new_arr.astype(np.float64))))
        return CellVerdict(kind="DIVERGE", cell_id=cell_id, detail=detail)

    return CellVerdict(kind="AGREE", cell_id=cell_id, detail={})
