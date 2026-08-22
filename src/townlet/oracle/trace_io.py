"""Trace file format for the differential harness.

Named trace_io, NOT trace: the driver runs by file path, and a sibling
trace.py would shadow stdlib `trace` for any interpreter with this directory
on sys.path.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

TRACE_FORMAT_VERSION = 4

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
    actions: np.ndarray  # (steps, num_agents) int64 — the actions actually stepped
    code_root: str  # resolved src root this side actually imported townlet from (FIX 5)
    # Resolved config root this side read its pack from (hamlet-2090c9f16d).
    # Like code_root it is REPORTED, never compared: once a pack-schema
    # divergence is declared the two sides read different roots by design.
    # RunParams.pack stays logical so compare_traces' params equality holds.
    pack_root: str
    # "seeded-random" (drawn from the run seed) or "scripted:<sha256-16>" (replayed
    # from a file). REPORTED, never compared — the compared truth is the actions
    # STREAM itself: equal bytes mean equal actions regardless of how each side
    # obtained them, which is exactly what the scripted replay flow relies on.
    action_source: str


def save_trace(path: Path, trace: Trace) -> None:
    meta = {
        "format_version": TRACE_FORMAT_VERSION,
        "params": asdict(trace.params),
        "hashes": trace.hashes,
        "code_root": trace.code_root,
        "pack_root": trace.pack_root,
        "action_source": trace.action_source,
    }
    np.savez_compressed(
        path,
        obs=trace.obs,
        rewards=trace.rewards,
        dones=trace.dones,
        actions=trace.actions,
        meta=np.array(json.dumps(meta)),
    )


def load_trace(path: Path) -> Trace:
    with np.load(path, allow_pickle=False) as data:
        meta = json.loads(str(data["meta"]))
        if meta["format_version"] != TRACE_FORMAT_VERSION:
            raise ValueError(
                f"trace {path} has format_version {meta['format_version']}; " f"this harness reads format_version {TRACE_FORMAT_VERSION}"
            )
        return Trace(
            params=RunParams(**meta["params"]),
            hashes=dict(meta["hashes"]),
            obs=data["obs"],
            rewards=data["rewards"],
            dones=data["dones"],
            actions=data["actions"],
            code_root=meta["code_root"],
            pack_root=meta["pack_root"],
            action_source=meta["action_source"],
        )


class HarnessError(RuntimeError):
    """A defect in the harness or its invocation — not a differential finding."""


@dataclass(frozen=True)
class CellVerdict:
    """The harness's judgement for one matrix cell.

    register_refs names the known-divergences entries this cell's observed
    outcome matched. It is populated ONLY by the harness's expectation matcher
    and ONLY on kind="DIVERGED_AS_REGISTERED" (hamlet-56ec575ae2); exit_code
    enforces both directions. DIV-001/002 are checkpoint-boundary and cannot
    manifest in an env trace, so a DIVERGE or HASH_MISMATCH — necessarily with
    empty refs — is a rebuild defect or a missing register entry: see
    docs/oracle/known-divergences.md.
    """

    # AGREE | DIVERGE | HASH_MISMATCH | OLD_SIDE_ERROR | NEW_SIDE_ERROR |
    # SKIPPED | HARNESS_ERROR | DIVERGED_AS_REGISTERED | REGISTERED_DIVERGENCE_ABSENT
    kind: str
    cell_id: str
    detail: dict[str, object]
    register_refs: tuple[str, ...] = ()


_MAX_REPORTED_INDICES = 10


def _stream_steps(trace: Trace) -> list[tuple[int, str, np.ndarray]]:
    """Trace arrays flattened into adjudication order: reset obs, then per-step.

    Within each step, actions precede dones and rewards, which precede obs[t+1] —
    mirroring env.step's causal order: the action taken at step t causes the
    termination and reward observed at step t, which cause obs[t+1]. A divergent
    done or reward at step t reflects the agent's actual termination/reward at that
    step and must be attributed to step t, not misattributed as an obs[t+1] echo.
    """
    entries: list[tuple[int, str, np.ndarray]] = [(0, "obs", trace.obs[0])]
    for t in range(trace.params.steps):
        entries.append((t, "actions", trace.actions[t]))
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


def compare_traces(
    old: Trace, new: Trace, cell_id: str, *, hash_divergence: Any = None, stream_divergence: Any = None
) -> CellVerdict:
    """Adjudicate one cell from both sides' traces.

    `hash_divergence` (matrix.RegisteredHashDivergence) permits — and requires —
    exactly the named provenance hashes to differ. `stream_divergence`
    (matrix.RegisteredStreamDivergence) permits — and requires — exactly the
    named trace STREAMS to diverge, shape changes included, while every other
    stream stays byte-exact. Both are typed loosely to keep this module free of
    a matrix import. Adjudication no longer stops at the first mismatching
    stream: every stream is compared in full, so a registered obs divergence
    can never mask the rewards/dones verdict (SA-C1, token-obs design §5/§6
    unit 1).
    """
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
    declared: frozenset[str] = hash_divergence.declared if hash_divergence is not None else frozenset()
    observed = frozenset(mismatched)

    if declared and observed != declared:
        # Either shape is a finding, and they are reported apart because they
        # mean opposite things: an undeclared mover is a rebuild changing more
        # than the entry claims; a declared field that did NOT move is a stale
        # entry, the same condition REGISTERED_DIVERGENCE_ABSENT names for the
        # crash shape. Neither may pass.
        undeclared = sorted(observed - declared)
        absent = sorted(declared - observed)
        hash_detail: dict[str, object] = {
            "mismatched": mismatched,
            "declared": sorted(declared),
            "register_ref": hash_divergence.register_ref,
        }
        if undeclared:
            hash_detail["undeclared_movers"] = undeclared
        if absent:
            hash_detail["declared_but_unmoved"] = absent
        kind = "HASH_MISMATCH" if undeclared else "REGISTERED_DIVERGENCE_ABSENT"
        return CellVerdict(kind=kind, cell_id=cell_id, detail=hash_detail)

    if mismatched and not declared:
        return CellVerdict(kind="HASH_MISMATCH", cell_id=cell_id, detail={"mismatched": mismatched})

    declared_streams: frozenset[str] = stream_divergence.declared if stream_divergence is not None else frozenset()

    # Collect findings for EVERY stream; never return mid-scan (SA-C1).
    findings: dict[str, dict[str, object]] = {}

    def _record(stream: str, entry: dict[str, object]) -> None:
        if stream not in findings:
            entry["diff_entries"] = 1
            findings[stream] = entry
        else:
            findings[stream]["diff_entries"] = int(findings[stream]["diff_entries"]) + 1  # type: ignore[call-overload]

    for (old_step, stream, old_arr), (_, _, new_arr) in zip(_stream_steps(old), _stream_steps(new), strict=True):
        if old_arr.shape != new_arr.shape or old_arr.dtype != new_arr.dtype:
            # Shape/dtype preflight (FIX 1) — still BEFORE byte comparison, but it
            # RECORDS rather than returns: for a declared stream this IS the
            # expected divergence (the token cut changes obs width, and bytes of
            # different shapes cannot be compared); for an undeclared stream it is
            # adjudicated red below with everything else.
            _record(
                stream,
                {
                    "step": old_step,
                    "shape_changed": True,
                    "old_shape": list(old_arr.shape),
                    "new_shape": list(new_arr.shape),
                    "old_dtype": str(old_arr.dtype),
                    "new_dtype": str(new_arr.dtype),
                },
            )
            continue
        if old_arr.tobytes() == new_arr.tobytes():
            continue
        if stream in declared_streams:
            # Expected to diverge — record cheaply, skip localization.
            _record(stream, {"step": old_step, "shape_changed": False})
            continue
        mask = _divergence_mask(old_arr, new_arr)
        if not mask.any():
            mask = np.ones_like(mask)
        diff_indices = np.argwhere(mask)
        entry: dict[str, object] = {
            "step": old_step,
            "shape_changed": False,
            "indices": [list(map(int, idx)) for idx in diff_indices[:_MAX_REPORTED_INDICES]],
            "diff_count": int(len(diff_indices)),
        }
        if old_arr.dtype != np.bool_:
            diffs = np.abs(old_arr[mask].astype(np.float64) - new_arr[mask].astype(np.float64))
            max_abs_diff = float(np.max(diffs)) if diffs.size else 0.0
            entry["max_abs_diff"] = max_abs_diff if np.isfinite(max_abs_diff) else "non-finite"
        _record(stream, entry)

    diverged = frozenset(findings)
    undeclared_streams = diverged - declared_streams
    unmoved_streams = declared_streams - diverged

    if undeclared_streams:
        return CellVerdict(
            kind="DIVERGE",
            cell_id=cell_id,
            detail={
                "streams": {name: findings[name] for name in sorted(diverged)},
                "undeclared_streams": sorted(undeclared_streams),
                **({"declared_streams": sorted(declared_streams)} if declared_streams else {}),
            },
        )
    if unmoved_streams:
        # A declared stream that never diverged is a stale entry — the exact
        # condition REGISTERED_DIVERGENCE_ABSENT names for the other two shapes.
        return CellVerdict(
            kind="REGISTERED_DIVERGENCE_ABSENT",
            cell_id=cell_id,
            detail={
                "register_ref": stream_divergence.register_ref,
                "declared_but_unmoved_streams": sorted(unmoved_streams),
                "streams": {name: findings[name] for name in sorted(diverged)},
            },
        )

    refs: tuple[str, ...] = ()
    if declared:  # the hash declaration manifested exactly (checked above)
        refs = refs + (hash_divergence.register_ref,)
    if declared_streams:
        if stream_divergence.register_ref not in refs:
            refs = refs + (stream_divergence.register_ref,)
    if refs:
        return CellVerdict(
            kind="DIVERGED_AS_REGISTERED",
            cell_id=cell_id,
            detail={
                "shape": ("hash+stream" if declared and declared_streams else "hash-only" if declared else "stream-only"),
                **({"mismatched": mismatched} if declared else {}),
                **({"streams": {name: findings[name] for name in sorted(diverged)}} if declared_streams else {}),
            },
            register_refs=refs,
        )
    return CellVerdict(kind="AGREE", cell_id=cell_id, detail={})
