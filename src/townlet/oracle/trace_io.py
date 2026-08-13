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

TRACE_FORMAT_VERSION = 2

# Sentinel distinguishing an ABSENT hash key from a key PRESENT with value
# None — dict.get(name) alone conflates the two, which would let a field
# added or removed by a rebuild masquerade as unchanged (FIX 2).
_ABSENT = object()


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
    code_root: str  # resolved src root this side actually imported townlet from (FIX 5)


def save_trace(path: Path, trace: Trace) -> None:
    meta = {
        "format_version": TRACE_FORMAT_VERSION,
        "params": asdict(trace.params),
        "hashes": trace.hashes,
        "code_root": trace.code_root,
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
            code_root=meta["code_root"],
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

    kind: str  # AGREE | DIVERGE | HASH_MISMATCH | OLD_SIDE_ERROR | NEW_SIDE_ERROR | SKIPPED | HARNESS_ERROR
    cell_id: str
    detail: dict[str, object]
    register_refs: tuple[str, ...] = ()


_MAX_REPORTED_INDICES = 10


def _stream_steps(trace: Trace) -> list[tuple[int, str, np.ndarray]]:
    """Trace arrays flattened into adjudication order: reset obs, then per-step.

    Within each step, dones and rewards precede obs[t+1] to mirror env.step's causal
    order: a divergent done at step t reflects the agent's actual termination at that
    step and must be attributed to step t, not misattributed as an obs[t+1] echo.
    """
    entries: list[tuple[int, str, np.ndarray]] = [(0, "obs", trace.obs[0])]
    for t in range(trace.params.steps):
        entries.append((t, "dones", trace.dones[t]))
        entries.append((t, "rewards", trace.rewards[t]))
        entries.append((t + 1, "obs", trace.obs[t + 1]))
    return entries


def _divergence_mask(old_arr: np.ndarray, new_arr: np.ndarray) -> np.ndarray:
    """Elementwise divergence used to localize a byte-level mismatch.

    Plain value equality (`!=`) gets two float cases wrong relative to the
    byte-exact AGREE/DIVERGE decision above it: -0.0 and 0.0 compare equal
    despite differing bytes (a real divergence would be missed), and NaN
    never compares equal to itself despite identical bytes (an identical
    value would be falsely localized as diverging). This mask corrects both
    so localization always agrees with the byte-level verdict.
    """
    if not np.issubdtype(old_arr.dtype, np.floating):
        return np.asarray(old_arr != new_arr)
    old_nan = np.isnan(old_arr)
    new_nan = np.isnan(new_arr)
    both_nan = old_nan & new_nan
    value_diff = (old_arr != new_arr) & ~both_nan
    nan_mismatch = old_nan ^ new_nan
    both_zero = (old_arr == 0) & (new_arr == 0)
    sign_diff = both_zero & (np.signbit(old_arr) != np.signbit(new_arr))
    return np.asarray(value_diff | nan_mismatch | sign_diff)


def compare_traces(old: Trace, new: Trace, cell_id: str) -> CellVerdict:
    if old.params != new.params:
        raise HarnessError(
            f"trace params differ between sides for cell {cell_id}: " f"{old.params} vs {new.params} — harness bug, not a finding"
        )

    mismatched: dict[str, dict[str, object]] = {}
    for name in sorted(set(old.hashes) | set(new.hashes)):
        # .get(name) alone cannot distinguish an ABSENT key from a key
        # PRESENT with value None (eleven *_hash fields default to None) —
        # use a sentinel default so a field added/removed by the rebuild is
        # never mistaken for an unchanged field (FIX 2).
        old_val = old.hashes.get(name, _ABSENT)
        new_val = new.hashes.get(name, _ABSENT)
        if old_val != new_val:
            mismatched[name] = {
                "old": "<absent>" if old_val is _ABSENT else old_val,
                "new": "<absent>" if new_val is _ABSENT else new_val,
            }
    if mismatched:
        return CellVerdict(kind="HASH_MISMATCH", cell_id=cell_id, detail={"mismatched": mismatched})

    for (old_step, old_stream, old_arr), (_, _, new_arr) in zip(_stream_steps(old), _stream_steps(new), strict=True):
        # Shape/dtype preflight (FIX 1): tobytes() serializes the C-order
        # buffer only — it is shape-blind. np.zeros((4,)) and np.zeros((4,1))
        # produce identical bytes despite differing rank, which would let a
        # rebuild returning e.g. rewards as [num_agents,1] instead of
        # [num_agents] report a false AGREE. This must run BEFORE the byte
        # comparison and before _divergence_mask, which raises ValueError on
        # broadcast-incompatible shapes rather than yielding a verdict.
        if old_arr.shape != new_arr.shape or old_arr.dtype != new_arr.dtype:
            return CellVerdict(
                kind="DIVERGE",
                cell_id=cell_id,
                detail={
                    "step": old_step,
                    "stream": old_stream,
                    "old_shape": list(old_arr.shape),
                    "new_shape": list(new_arr.shape),
                    "old_dtype": str(old_arr.dtype),
                    "new_dtype": str(new_arr.dtype),
                },
            )
        # Comparison is exact bytes, per spec: value equality is wrong for
        # -0.0 vs 0.0 (equal value, different bytes) and NaN vs NaN (equal
        # bytes, "unequal" value).
        if old_arr.tobytes() == new_arr.tobytes():
            continue
        mask = _divergence_mask(old_arr, new_arr)
        if not mask.any():
            # Bytes differ but nothing trips value/NaN/sign localization
            # (e.g. two distinct NaN bit-payloads) — flag every position
            # rather than silently reporting an empty divergence.
            mask = np.ones_like(mask)
        diff_indices = np.argwhere(mask)
        detail: dict[str, object] = {
            "step": old_step,
            "stream": old_stream,
            "indices": [list(map(int, idx)) for idx in diff_indices[:_MAX_REPORTED_INDICES]],
            "diff_count": int(len(diff_indices)),
        }
        if old_arr.dtype != np.bool_:
            diffs = np.abs(old_arr[mask].astype(np.float64) - new_arr[mask].astype(np.float64))
            max_abs_diff = float(np.max(diffs)) if diffs.size else 0.0
            detail["max_abs_diff"] = max_abs_diff if np.isfinite(max_abs_diff) else "non-finite"
        return CellVerdict(kind="DIVERGE", cell_id=cell_id, detail=detail)

    return CellVerdict(kind="AGREE", cell_id=cell_id, detail={})
