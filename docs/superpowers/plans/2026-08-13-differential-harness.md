# Differential Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `src/townlet/oracle/` — the differential harness that runs the frozen oracle worktree (`oracle-2026-08-13`) and the working tree against the same config pack + seed and bit-compares their env-step traces (WS-7 content 3, spec: `docs/superpowers/specs/2026-08-13-differential-harness-design.md`).

**Architecture:** A self-contained driver script produces a trace `.npz` (obs/rewards/dones + provenance hashes); the harness spawns it twice per matrix cell — once with `PYTHONPATH` at the oracle worktree's `src`, once at the working tree's `src` — then compares provenance hashes (stage 1) and exact trace bytes (stage 2), emitting per-cell verdicts and a JSON report.

**Tech Stack:** Python 3.13, numpy (npz traces), torch, argparse, subprocess. No new dependencies.

## Global Constraints

- Run everything through `uv run` (e.g. `uv run pytest`, `uv run python -m …`).
- All four gates must stay green: `uv run ruff check src/townlet`, `uv run black src/townlet tests/`, `uv run mypy src/townlet`, `uv run pytest`.
- `driver.py` is **self-contained**: it may import stdlib, numpy, torch, `townlet.determinism`, `townlet.universe.compiler`, `townlet.environment.vectorized_env` — and **never anything from `townlet.oracle`** (it must run under the frozen tag's `src`, where `townlet.oracle` does not exist).
- The trace/compare module is named `trace_io.py`, NOT `trace.py` — a file named `trace.py` would shadow stdlib `trace` when the driver runs by file path. Driver subprocesses are invoked with `python -P` (no script-dir on `sys.path`) as a second guard.
- The oracle ref has one machine-readable authority: `townlet.oracle.ORACLE_TAG`.
- No hidden defaults in the matrix: every cell declares pack, level, num_agents, steps, seed, device explicitly.
- TDD throughout: failing test first, then minimal implementation. Commit per task.
- Commit messages end with: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task 1: Package scaffold + trace format (`trace_io.py`: RunParams, Trace, save/load)

**Files:**
- Create: `src/townlet/oracle/__init__.py`
- Create: `src/townlet/oracle/trace_io.py`
- Create: `tests/test_townlet/unit/oracle/test_trace_io.py`
- Modify: `.gitignore` (append `.oracle/`; also append `runs/differential/` unless `runs/` is already ignored — check with `grep -n "^runs" .gitignore`)

**Interfaces:**
- Produces: `ORACLE_TAG: str` in `townlet/oracle/__init__.py`; `RunParams` (frozen dataclass: `pack: str, level: str, num_agents: int, steps: int, seed: int, device: str`); `Trace` (frozen dataclass: `params: RunParams, hashes: dict[str, str | None], obs: np.ndarray, rewards: np.ndarray, dones: np.ndarray`); `save_trace(path: Path, trace: Trace) -> None`; `load_trace(path: Path) -> Trace`; `TRACE_FORMAT_VERSION = 1`.

- [ ] **Step 1: Write the failing test**

`tests/test_townlet/unit/oracle/test_trace_io.py`:

```python
"""Trace file format: save/load round-trip (WS-7 differential harness)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from townlet.oracle.trace_io import RunParams, Trace, load_trace, save_trace

PARAMS = RunParams(
    pack="configs/default_curriculum",
    level="L0_0_minimal",
    num_agents=4,
    steps=3,
    seed=42,
    device="cpu",
)


def _mk_trace(**overrides) -> Trace:
    rng = np.random.default_rng(0)
    fields = dict(
        params=PARAMS,
        hashes={"vfs_hash": "abc123", "items_hash": None},
        obs=rng.random((4, 4, 7), dtype=np.float32),  # steps+1, agents, obs_dim
        rewards=rng.random((3, 4), dtype=np.float32),
        dones=np.zeros((3, 4), dtype=bool),
    )
    fields.update(overrides)
    return Trace(**fields)


def test_save_load_round_trip(tmp_path: Path) -> None:
    trace = _mk_trace()
    path = tmp_path / "trace.npz"
    save_trace(path, trace)
    loaded = load_trace(path)
    assert loaded.params == trace.params
    assert loaded.hashes == trace.hashes  # includes the None-valued items_hash
    np.testing.assert_array_equal(loaded.obs, trace.obs)
    np.testing.assert_array_equal(loaded.rewards, trace.rewards)
    np.testing.assert_array_equal(loaded.dones, trace.dones)
    assert loaded.obs.dtype == np.float32
    assert loaded.dones.dtype == np.bool_


def test_load_rejects_unknown_format_version(tmp_path: Path) -> None:
    trace = _mk_trace()
    path = tmp_path / "trace.npz"
    save_trace(path, trace)
    # Corrupt the version in-place by rewriting the meta payload.
    import json

    data = dict(np.load(path, allow_pickle=False))
    meta = json.loads(str(data["meta"]))
    meta["format_version"] = 999
    data["meta"] = np.array(json.dumps(meta))
    np.savez_compressed(path, **data)
    with pytest.raises(ValueError, match="format_version"):
        load_trace(path)


def test_oracle_tag_constant() -> None:
    from townlet.oracle import ORACLE_TAG

    assert ORACLE_TAG == "oracle-2026-08-13"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_townlet/unit/oracle/test_trace_io.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'townlet.oracle'`

- [ ] **Step 3: Write minimal implementation**

`src/townlet/oracle/__init__.py`:

```python
"""Differential harness for the strangler rewrite (WS-7, PDR-0006, PDR-0030).

Runs the frozen oracle worktree and the working tree against the same declared
universe and seed, and asserts their env-step traces agree everywhere
docs/oracle/known-divergences.md does not say otherwise.
"""

# The single machine-readable authority for the current oracle ref. When the
# oracle moves forward (PDR-0030 reversal path), this constant moves with the
# new tag; docs/oracle/ORACLE.md records the history.
ORACLE_TAG = "oracle-2026-08-13"

__all__ = ["ORACLE_TAG"]
```

`src/townlet/oracle/trace_io.py`:

```python
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
            raise ValueError(
                f"trace {path} has format_version {meta['format_version']}; "
                f"this harness reads {TRACE_FORMAT_VERSION}"
            )
        return Trace(
            params=RunParams(**meta["params"]),
            hashes=dict(meta["hashes"]),
            obs=data["obs"],
            rewards=data["rewards"],
            dones=data["dones"],
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_townlet/unit/oracle/test_trace_io.py -v`
Expected: 3 PASS

- [ ] **Step 5: Update `.gitignore`**

Check `grep -n "^runs" .gitignore`. Append `.oracle/` (always) and `runs/differential/` (only if `runs/` is not already covered).

- [ ] **Step 6: Commit**

```bash
git add src/townlet/oracle/ tests/test_townlet/unit/oracle/ .gitignore
git commit -m "feat(WS-7): oracle package scaffold + trace file format

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Comparison (`compare_traces` + `CellVerdict`)

**Files:**
- Modify: `src/townlet/oracle/trace_io.py` (append)
- Test: `tests/test_townlet/unit/oracle/test_compare.py`

**Interfaces:**
- Consumes: `Trace`, `RunParams` from Task 1.
- Produces: `CellVerdict` (frozen dataclass: `kind: str` — one of `"AGREE" | "DIVERGE" | "HASH_MISMATCH" | "OLD_SIDE_ERROR" | "NEW_SIDE_ERROR" | "SKIPPED"`, `cell_id: str`, `detail: dict[str, object]`, `register_refs: tuple[str, ...] = ()`); `compare_traces(old: Trace, new: Trace, cell_id: str) -> CellVerdict`; `HarnessError(RuntimeError)`.

**Comparison semantics (from spec):** params differing between sides is a harness bug → raise `HarnessError`. Hashes compared as dicts — any differing key set or value → `HASH_MISMATCH`, traces not consulted. Arrays compared bit-exactly in step order: reset obs first, then per step `obs[t+1]`, `rewards[t]`, `dones[t]`. First divergent (step, stream) reported; `step=0` with `stream="obs"` means the reset observation. `indices` capped at 10 entries; `max_abs_diff` computed for the divergent float stream (omit for `dones`).

- [ ] **Step 1: Write the failing test**

`tests/test_townlet/unit/oracle/test_compare.py`:

```python
"""compare_traces: the harness's judgement logic (WS-7 differential harness)."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from townlet.oracle.trace_io import (
    CellVerdict,
    HarnessError,
    RunParams,
    Trace,
    compare_traces,
)

PARAMS = RunParams(
    pack="configs/default_curriculum",
    level="L0_0_minimal",
    num_agents=4,
    steps=3,
    seed=42,
    device="cpu",
)


def _mk_trace() -> Trace:
    rng = np.random.default_rng(7)
    return Trace(
        params=PARAMS,
        hashes={"vfs_hash": "abc", "action_schema_hash": "def", "items_hash": None},
        obs=rng.random((4, 4, 7), dtype=np.float32),
        rewards=rng.random((3, 4), dtype=np.float32),
        dones=np.zeros((3, 4), dtype=bool),
    )


def test_identical_traces_agree() -> None:
    verdict = compare_traces(_mk_trace(), _mk_trace(), cell_id="c1")
    assert verdict.kind == "AGREE"
    assert verdict.cell_id == "c1"
    assert verdict.register_refs == ()


def test_reward_perturbation_locates_first_divergence() -> None:
    old, new = _mk_trace(), _mk_trace()
    new.rewards[1, 2] += 0.5  # step 1, agent 2
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    assert verdict.detail["step"] == 1
    assert verdict.detail["stream"] == "rewards"
    assert [2] == [idx[0] for idx in verdict.detail["indices"]]
    assert verdict.detail["max_abs_diff"] == pytest.approx(0.5)


def test_reset_obs_divergence_reports_step_zero() -> None:
    old, new = _mk_trace(), _mk_trace()
    new.obs[0, 0, 0] += 1.0
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    assert verdict.detail["step"] == 0
    assert verdict.detail["stream"] == "obs"


def test_earliest_step_wins_across_streams() -> None:
    old, new = _mk_trace(), _mk_trace()
    new.dones[0, 1] = True  # step 0 of dones == trace step 0
    new.rewards[2, 0] += 1.0
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    assert verdict.detail["step"] == 0
    assert verdict.detail["stream"] == "dones"
    assert "max_abs_diff" not in verdict.detail


def test_hash_mismatch_short_circuits_traces() -> None:
    old, new = _mk_trace(), _mk_trace()
    object.__setattr__(new, "hashes", {**old.hashes, "vfs_hash": "OTHER"})
    new.rewards[0, 0] += 1.0  # would also diverge, must not be reached
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "HASH_MISMATCH"
    assert verdict.detail["mismatched"] == {"vfs_hash": {"old": "abc", "new": "OTHER"}}


def test_differing_hash_key_sets_are_a_mismatch() -> None:
    old, new = _mk_trace(), _mk_trace()
    object.__setattr__(new, "hashes", {**old.hashes, "novel_hash": "x"})
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "HASH_MISMATCH"
    assert "novel_hash" in verdict.detail["mismatched"]


def test_params_mismatch_is_a_harness_bug() -> None:
    old, new = _mk_trace(), _mk_trace()
    object.__setattr__(new, "params", dataclasses.replace(PARAMS, seed=43))
    with pytest.raises(HarnessError, match="params"):
        compare_traces(old, new, cell_id="c1")


def test_verdict_is_json_serializable() -> None:
    import json

    old, new = _mk_trace(), _mk_trace()
    new.rewards[1, 2] += 0.5
    verdict = compare_traces(old, new, cell_id="c1")
    json.dumps(dataclasses.asdict(verdict))  # must not raise
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_townlet/unit/oracle/test_compare.py -v`
Expected: FAIL — `ImportError: cannot import name 'CellVerdict'`

- [ ] **Step 3: Write minimal implementation** (append to `trace_io.py`)

```python
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
            f"trace params differ between sides for cell {cell_id}: "
            f"{old.params} vs {new.params} — harness bug, not a finding"
        )

    mismatched = {
        name: {"old": old.hashes.get(name), "new": new.hashes.get(name)}
        for name in sorted(set(old.hashes) | set(new.hashes))
        if old.hashes.get(name) != new.hashes.get(name)
    }
    if mismatched:
        return CellVerdict(kind="HASH_MISMATCH", cell_id=cell_id, detail={"mismatched": mismatched})

    for (old_step, old_stream, old_arr), (_, _, new_arr) in zip(
        _stream_steps(old), _stream_steps(new), strict=True
    ):
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
            detail["max_abs_diff"] = float(
                np.max(np.abs(old_arr.astype(np.float64) - new_arr.astype(np.float64)))
            )
        return CellVerdict(kind="DIVERGE", cell_id=cell_id, detail=detail)

    return CellVerdict(kind="AGREE", cell_id=cell_id, detail={})
```

Note the adjudication order within a step: `dones` and `rewards` for step *t* are emitted before `obs[t+1]` because that is causal order inside `env.step` — a divergent done at step 0 must be reported at step 0, not as its obs echo at step 1.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_townlet/unit/oracle/test_compare.py -v`
Expected: 8 PASS

- [ ] **Step 5: Commit**

```bash
git add src/townlet/oracle/trace_io.py tests/test_townlet/unit/oracle/test_compare.py
git commit -m "feat(WS-7): trace comparison — two-stage verdicts (hashes, then bit-exact streams)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: The injected driver (`driver.py`)

**Files:**
- Create: `src/townlet/oracle/driver.py`
- Test: `tests/test_townlet/unit/oracle/test_driver.py`

**Interfaces:**
- Consumes: `RunParams`, `Trace`, `save_trace` — **but NOT by import**. The driver re-declares nothing: it builds the meta dict and calls `np.savez_compressed` itself with the exact same keys/format (format_version 1). This duplication is deliberate and load-bearing: the driver must run under the tag's `src` where `townlet.oracle` does not exist. A comment in both files cross-references the pairing, and `test_trace_io.py`'s round-trip plus the integration test (Task 5) pin the formats to each other.
- Produces: `collect_provenance_hashes(universe) -> dict[str, str | None]`; `run_trace(pack: str, level: str, num_agents: int, steps: int, seed: int, device: str, out: Path) -> None`; `main(argv: list[str] | None = None) -> int`; CLI `python -P src/townlet/oracle/driver.py --pack … --level … --num-agents … --steps … --seed … --device … --out …`.

- [ ] **Step 1: Write the failing test**

`tests/test_townlet/unit/oracle/test_driver.py`:

```python
"""Driver smoke test: produces a valid trace file in-process (WS-7)."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from townlet.oracle import driver
from townlet.oracle.trace_io import load_trace

PACK = "configs/default_curriculum"
LEVEL = "L0_0_minimal"


def test_driver_writes_a_loadable_trace(tmp_path: Path) -> None:
    out = tmp_path / "trace.npz"
    driver.run_trace(
        pack=PACK, level=LEVEL, num_agents=4, steps=3, seed=42, device="cpu", out=out
    )
    trace = load_trace(out)
    assert trace.params.level == LEVEL
    assert trace.params.seed == 42
    assert trace.obs.shape[0] == 4  # steps + 1, reset included
    assert trace.obs.shape[1] == 4  # num_agents
    assert trace.rewards.shape == (3, 4)
    assert trace.dones.shape == (3, 4)
    assert trace.dones.dtype == np.bool_
    # Provenance hashes: every *_hash field on CompiledUniverse, required ones set.
    assert trace.hashes["vfs_hash"]
    assert trace.hashes["observation_schema_hash"]
    assert "training_hash" in trace.hashes


def test_driver_is_deterministic_for_same_seed(tmp_path: Path) -> None:
    a, b = tmp_path / "a.npz", tmp_path / "b.npz"
    for out in (a, b):
        driver.run_trace(
            pack=PACK, level=LEVEL, num_agents=4, steps=3, seed=42, device="cpu", out=out
        )
    ta, tb = load_trace(a), load_trace(b)
    np.testing.assert_array_equal(ta.obs, tb.obs)
    np.testing.assert_array_equal(ta.rewards, tb.rewards)


def test_driver_source_is_self_contained() -> None:
    """The driver must run under the frozen tag's src, where townlet.oracle
    does not exist. Any import of townlet.oracle is a defect by construction."""
    source = Path(driver.__file__).read_text()
    assert not re.search(r"from\s+townlet\.oracle|import\s+townlet\.oracle", source)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_townlet/unit/oracle/test_driver.py -v`
Expected: FAIL — `ImportError` (no module `townlet.oracle.driver`)

- [ ] **Step 3: Write minimal implementation**

`src/townlet/oracle/driver.py`:

```python
"""The injected trace producer for the differential harness.

SELF-CONTAINED BY RULE: this file is executed by file path in BOTH sides'
interpreters — including the frozen oracle worktree, where townlet.oracle does
not exist. It may import stdlib, numpy, torch, and townlet modules present at
the oracle tag ONLY. It must never import from townlet.oracle (pinned by
test_driver_source_is_self_contained).

The trace file it writes is format_version 1, matching
townlet/oracle/trace_io.py exactly (keys: obs, rewards, dones, meta). The
pairing is pinned by the Task 5 integration test.

Recipe mirrors tests/test_townlet/integration/test_determinism.py::_trace_hash,
the recipe whose determinism is verified CPU + CUDA at the tag (PDR-0030).
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import traceback
from pathlib import Path

import numpy as np
import torch

from townlet.determinism import seed_all
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

TRACE_FORMAT_VERSION = 1


def collect_provenance_hashes(universe: object) -> dict[str, str | None]:
    """Every *_hash field on CompiledUniverse, by reflection.

    Reflection rather than a hardcoded list so the driver reports whatever
    hash surface its OWN side actually has — a field added or removed by the
    rebuild shows up as a key-set difference, which compare_traces flags.
    """
    return {
        f.name: getattr(universe, f.name)
        for f in dataclasses.fields(universe)  # type: ignore[arg-type]
        if f.name.endswith("_hash")
    }


def run_trace(
    *, pack: str, level: str, num_agents: int, steps: int, seed: int, device: str, out: Path
) -> None:
    universe = UniverseCompiler().compile(Path(pack), primary_level=level, use_cache=False)
    seed_all(seed)
    env = VectorizedHamletEnv(
        universe=universe, level_name=level, num_agents=num_agents, device=torch.device(device)
    )
    obs = env.reset()
    obs_frames = [obs.cpu().numpy().copy()]
    reward_frames: list[np.ndarray] = []
    done_frames: list[np.ndarray] = []
    for _ in range(steps):
        # Actions drawn on CPU so the stream is device-independent, then moved
        # to the env device — same as the verified determinism recipe.
        actions = torch.randint(0, env.action_dim, (env.num_agents,)).to(env.device)
        obs, rewards, dones, _ = env.step(actions)
        obs_frames.append(obs.cpu().numpy().copy())
        reward_frames.append(rewards.cpu().numpy().copy())
        done_frames.append(dones.cpu().numpy().copy())

    meta = {
        "format_version": TRACE_FORMAT_VERSION,
        "params": {
            "pack": pack,
            "level": level,
            "num_agents": num_agents,
            "steps": steps,
            "seed": seed,
            "device": device,
        },
        "hashes": collect_provenance_hashes(universe),
    }
    np.savez_compressed(
        out,
        obs=np.stack(obs_frames).astype(np.float32),
        rewards=np.stack(reward_frames).astype(np.float32),
        dones=np.stack(done_frames).astype(bool),
        meta=np.array(json.dumps(meta)),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Produce one differential-harness trace.")
    parser.add_argument("--pack", required=True)
    parser.add_argument("--level", required=True)
    parser.add_argument("--num-agents", type=int, required=True)
    parser.add_argument("--steps", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--device", required=True, choices=("cpu", "cuda"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        run_trace(
            pack=args.pack,
            level=args.level,
            num_agents=args.num_agents,
            steps=args.steps,
            seed=args.seed,
            device=args.device,
            out=args.out,
        )
    except Exception:  # noqa: BLE001 — boundary: full traceback to stderr, nonzero exit
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_townlet/unit/oracle/test_driver.py -v`
Expected: 3 PASS (compiles L0_0_minimal twice; expect ~30–60s, in line with other compiling unit tests)

- [ ] **Step 5: Commit**

```bash
git add src/townlet/oracle/driver.py tests/test_townlet/unit/oracle/test_driver.py
git commit -m "feat(WS-7): self-contained trace driver — runs under either side's src

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: The declared matrix (`matrix.py`)

**Files:**
- Create: `src/townlet/oracle/matrix.py`
- Test: `tests/test_townlet/unit/oracle/test_matrix.py`

**Interfaces:**
- Consumes: `RunParams` from Task 1.
- Produces: `Cell` (frozen dataclass: `params: RunParams`, property `cell_id: str` = `f"{Path(params.pack).name}:{params.level}:{params.device}:seed{params.seed}"`); `default_cells(include_cuda: bool = False) -> tuple[Cell, ...]`.

- [ ] **Step 1: Write the failing test**

`tests/test_townlet/unit/oracle/test_matrix.py`:

```python
"""The declared comparison matrix — explicit cells, no discovery magic (WS-7)."""

from __future__ import annotations

from townlet.oracle.matrix import Cell, default_cells

LEVELS = (
    "L0_0_minimal",
    "L0_5_dual_resource",
    "L1_full_observability",
    "L2_partial_observability",
    "L3_temporal_mechanics",
)


def test_default_matrix_is_the_five_levels_on_cpu() -> None:
    cells = default_cells()
    assert tuple(c.params.level for c in cells) == LEVELS
    assert all(c.params.device == "cpu" for c in cells)
    assert all(c.params.pack == "configs/default_curriculum" for c in cells)
    assert all(c.params.num_agents == 4 for c in cells)
    assert all(c.params.steps == 100 for c in cells)
    assert all(c.params.seed == 42 for c in cells)


def test_cuda_flag_appends_cuda_variants() -> None:
    cells = default_cells(include_cuda=True)
    assert len(cells) == 10
    cuda = [c for c in cells if c.params.device == "cuda"]
    assert tuple(c.params.level for c in cuda) == LEVELS


def test_cell_id_is_unique_and_readable() -> None:
    cells = default_cells(include_cuda=True)
    ids = [c.cell_id for c in cells]
    assert len(set(ids)) == len(ids)
    assert "default_curriculum:L0_0_minimal:cpu:seed42" in ids
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_townlet/unit/oracle/test_matrix.py -v`
Expected: FAIL — no module `townlet.oracle.matrix`

- [ ] **Step 3: Write minimal implementation**

`src/townlet/oracle/matrix.py`:

```python
"""The declared comparison matrix.

Cells are DECLARED, not discovered — per the no-defaults principle, every
parameter of every cell is explicit here. The five default_curriculum levels
are three distinct universes (PDR-0018); all five are cells anyway, because
the harness compares runtimes, not curricula.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from townlet.oracle.trace_io import RunParams

_DEFAULT_PACK = "configs/default_curriculum"
_DEFAULT_LEVELS = (
    "L0_0_minimal",
    "L0_5_dual_resource",
    "L1_full_observability",
    "L2_partial_observability",
    "L3_temporal_mechanics",
)


@dataclass(frozen=True)
class Cell:
    params: RunParams

    @property
    def cell_id(self) -> str:
        p = self.params
        return f"{Path(p.pack).name}:{p.level}:{p.device}:seed{p.seed}"


def default_cells(include_cuda: bool = False) -> tuple[Cell, ...]:
    devices = ("cpu", "cuda") if include_cuda else ("cpu",)
    return tuple(
        Cell(
            RunParams(
                pack=_DEFAULT_PACK,
                level=level,
                num_agents=4,
                steps=100,
                seed=42,
                device=device,
            )
        )
        for device in devices
        for level in _DEFAULT_LEVELS
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_townlet/unit/oracle/test_matrix.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add src/townlet/oracle/matrix.py tests/test_townlet/unit/oracle/test_matrix.py
git commit -m "feat(WS-7): declared differential matrix — five levels, cpu default, cuda opt-in

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Orchestrator + CLI (`harness.py`) with subprocess integration test

**Files:**
- Create: `src/townlet/oracle/harness.py`
- Test: `tests/test_townlet/unit/oracle/test_harness.py` (verdict aggregation, report shape — no subprocesses)
- Test: `tests/test_townlet/integration/test_differential_harness.py` (subprocess self-comparison, marked slow)

**Interfaces:**
- Consumes: `Trace`, `load_trace`, `compare_traces`, `CellVerdict`, `HarnessError` (Task 1–2); `Cell`, `default_cells` (Task 4); `ORACLE_TAG`; driver CLI (Task 3).
- Produces: `ensure_worktree(repo_root: Path, tag: str) -> Path`; `run_side(*, driver: Path, src: Path, params: RunParams, out: Path, repo_root: Path) -> str | None` (None on success, captured stderr on failure); `run_cell(*, repo_root: Path, old_src: Path, new_src: Path, cell: Cell, run_dir: Path) -> CellVerdict`; `exit_code(verdicts: list[CellVerdict]) -> int` (0 iff every kind is AGREE or SKIPPED, else 1); `write_report(run_dir: Path, verdicts: list[CellVerdict], meta: dict[str, object]) -> Path`; `main(argv: list[str] | None = None) -> int`.

- [ ] **Step 1: Write the failing unit test**

`tests/test_townlet/unit/oracle/test_harness.py`:

```python
"""Harness verdict aggregation and report writing — no subprocesses here (WS-7)."""

from __future__ import annotations

import json
from pathlib import Path

from townlet.oracle.harness import exit_code, write_report
from townlet.oracle.trace_io import CellVerdict


def _v(kind: str, cell: str = "c") -> CellVerdict:
    return CellVerdict(kind=kind, cell_id=cell, detail={})


def test_exit_zero_only_for_agree_and_skipped() -> None:
    assert exit_code([_v("AGREE"), _v("SKIPPED")]) == 0
    assert exit_code([_v("AGREE"), _v("DIVERGE")]) == 1
    assert exit_code([_v("HASH_MISMATCH")]) == 1
    assert exit_code([_v("OLD_SIDE_ERROR")]) == 1
    assert exit_code([_v("NEW_SIDE_ERROR")]) == 1
    assert exit_code([]) == 1  # an empty run proves nothing; refuse to look green


def test_report_carries_verdicts_meta_and_register_pointer(tmp_path: Path) -> None:
    verdicts = [_v("AGREE", "cell-a"), _v("DIVERGE", "cell-b")]
    meta = {"oracle_ref": "oracle-2026-08-13", "new_commit": "abc"}
    path = write_report(tmp_path, verdicts, meta)
    report = json.loads(path.read_text())
    assert report["meta"]["oracle_ref"] == "oracle-2026-08-13"
    assert [v["cell_id"] for v in report["verdicts"]] == ["cell-a", "cell-b"]
    assert report["verdicts"][1]["register_refs"] == []
    assert "known-divergences" in report["adjudication_note"]
```

- [ ] **Step 2: Run unit test to verify it fails**

Run: `uv run pytest tests/test_townlet/unit/oracle/test_harness.py -v`
Expected: FAIL — no module `townlet.oracle.harness`

- [ ] **Step 3: Write the implementation**

`src/townlet/oracle/harness.py`:

```python
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
    result = subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True, text=True, check=True
    )
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
            f"cannot create oracle worktree at {path} from tag {tag!r}:\n{e.stderr}\n"
            f"remedy: git worktree add --detach {path} {tag}"
        ) from e
    return path


def run_side(
    *, driver: Path, src: Path, params: RunParams, out: Path, repo_root: Path
) -> str | None:
    """Run the driver under one side's src. None on success, stderr text on failure."""
    cmd = [
        sys.executable,
        "-P",  # do not prepend the script dir to sys.path (stdlib-shadowing guard)
        str(driver),
        "--pack", params.pack,
        "--level", params.level,
        "--num-agents", str(params.num_agents),
        "--steps", str(params.steps),
        "--seed", str(params.seed),
        "--device", params.device,
        "--out", str(out),
    ]
    env = {**os.environ, "PYTHONPATH": str(src)}
    result = subprocess.run(cmd, cwd=repo_root, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        return result.stderr
    return None


def run_cell(
    *, repo_root: Path, old_src: Path, new_src: Path, cell: Cell, run_dir: Path
) -> CellVerdict:
    if cell.params.device == "cuda" and not torch.cuda.is_available():
        return CellVerdict(
            kind="SKIPPED", cell_id=cell.cell_id, detail={"reason": "cuda unavailable"}
        )
    driver = new_src / "townlet" / "oracle" / "driver.py"
    safe = cell.cell_id.replace(":", "_")
    old_out = run_dir / f"{safe}.old.npz"
    new_out = run_dir / f"{safe}.new.npz"
    for side, src, out, kind in (
        ("old", old_src, old_out, "OLD_SIDE_ERROR"),
        ("new", new_src, new_out, "NEW_SIDE_ERROR"),
    ):
        stderr = run_side(
            driver=driver, src=src, params=cell.params, out=out, repo_root=repo_root
        )
        if stderr is not None:
            return CellVerdict(
                kind=kind, cell_id=cell.cell_id, detail={"side": side, "stderr": stderr}
            )
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
        "verdicts": [
            {**asdict(v), "register_refs": list(v.register_refs)} for v in verdicts
        ],
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
```

- [ ] **Step 4: Run unit test to verify it passes**

Run: `uv run pytest tests/test_townlet/unit/oracle/test_harness.py -v`
Expected: 2 PASS

- [ ] **Step 5: Write the failing integration test**

`tests/test_townlet/integration/test_differential_harness.py`:

```python
"""Subprocess self-comparison: working tree vs working tree must AGREE (WS-7).

Exercises the real driver-subprocess plumbing (PYTHONPATH injection, -P flag,
trace round-trip through files, compare) WITHOUT needing the oracle worktree —
both sides are the working tree, so CI never depends on a tag being present.
A full old-vs-new run is a CLI operation, not a suite test (by design)."""

from __future__ import annotations

from pathlib import Path

import pytest

from townlet.oracle.harness import run_cell
from townlet.oracle.matrix import Cell
from townlet.oracle.trace_io import RunParams

pytestmark = pytest.mark.slow

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_self_comparison_agrees(tmp_path: Path) -> None:
    cell = Cell(
        RunParams(
            pack="configs/default_curriculum",
            level="L0_0_minimal",
            num_agents=4,
            steps=10,
            seed=42,
            device="cpu",
        )
    )
    verdict = run_cell(
        repo_root=REPO_ROOT,
        old_src=REPO_ROOT / "src",
        new_src=REPO_ROOT / "src",
        cell=cell,
        run_dir=tmp_path,
    )
    assert verdict.kind == "AGREE", verdict.detail


def test_driver_failure_is_a_loud_side_error(tmp_path: Path) -> None:
    cell = Cell(
        RunParams(
            pack="configs/default_curriculum",
            level="NO_SUCH_LEVEL",
            num_agents=4,
            steps=2,
            seed=42,
            device="cpu",
        )
    )
    verdict = run_cell(
        repo_root=REPO_ROOT,
        old_src=REPO_ROOT / "src",
        new_src=REPO_ROOT / "src",
        cell=cell,
        run_dir=tmp_path,
    )
    assert verdict.kind == "OLD_SIDE_ERROR"  # old side runs first, fails first
    assert "NO_SUCH_LEVEL" in str(verdict.detail["stderr"]) or verdict.detail["stderr"]
```

- [ ] **Step 6: Run integration test to verify it passes**

Run: `uv run pytest tests/test_townlet/integration/test_differential_harness.py -v`
Expected: 2 PASS (two driver subprocesses each compiling the pack; expect a few minutes)

- [ ] **Step 7: Commit**

```bash
git add src/townlet/oracle/harness.py tests/test_townlet/unit/oracle/test_harness.py tests/test_townlet/integration/test_differential_harness.py
git commit -m "feat(WS-7): differential harness orchestrator — worktree mgmt, subprocess drivers, verdict report

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Gates + acceptance (all-AGREE vs oracle; mutation-verified DIVERGE)

**Files:**
- No new files. Runs the four gates and the two acceptance criteria from the spec against the real oracle worktree.

**Interfaces:**
- Consumes: the finished CLI from Task 5.

- [ ] **Step 1: Run all four gates**

```bash
uv run ruff check src/townlet
uv run black --check src/townlet tests/
uv run mypy src/townlet
uv run pytest
```
Expected: all pass (pytest count grows by the new oracle tests, 0 failed). Fix anything red before proceeding — reformat with `uv run black src/townlet tests/` if black complains.

- [ ] **Step 2: Acceptance (a) — full CPU matrix vs the oracle, all AGREE**

```bash
rm -f configs/**/*.msgpack   # house rule: purge compile caches before measuring
uv run python -m townlet.oracle.harness
```
Expected: five lines `AGREE`, exit 0, report under `runs/differential/`. **If any cell is not AGREE: STOP. Do not fix, do not paper over — that is a finding about the oracle or the harness; report it to the session owner verbatim.**

- [ ] **Step 3: Acceptance (b) — mutation-verified DIVERGE**

Locate the reward composition in `src/townlet/environment/dac_engine.py` (the method that returns the per-step total reward tensor; find it with `grep -n "def " src/townlet/environment/dac_engine.py`). Add `+ 0.001` to its return value as an **uncommitted** edit. Then:

```bash
uv run python -m townlet.oracle.harness --cell default_curriculum:L0_0_minimal
```
Expected: `DIVERGE` with `stream == "rewards"` at an early step, exit 1. Then revert and re-verify green:

```bash
git restore src/townlet/environment/dac_engine.py
uv run python -m townlet.oracle.harness --cell default_curriculum:L0_0_minimal
```
Expected: `AGREE`, exit 0.

- [ ] **Step 4: CUDA spot-check (this machine has CUDA)**

```bash
uv run python -m townlet.oracle.harness --cuda --cell default_curriculum:L0_0_minimal
```
Expected: both the cpu and cuda cells `AGREE`, exit 0.

- [ ] **Step 5: Record the acceptance evidence**

Note the run-ids and verdict lines for the session log / tracker comment (WS-7 `hamlet-e3af412673`). Do not delete `runs/differential/` outputs — they are experimental evidence under the data-deletion clause.

- [ ] **Step 6: Final commit (docs only if anything was touched)**

If `.gitignore` or docs changed in this task, commit them:

```bash
git add -A && git status --short   # review first; expect only intentional changes
git commit -m "test(WS-7): differential harness accepted — all-AGREE vs oracle, mutation-verified DIVERGE

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Self-review notes (done at plan time)

- **Spec coverage:** driver (Task 3), trace format + compare (Tasks 1–2), matrix (Task 4), orchestrator/CLI/worktree/report/exit codes (Task 5), acceptance a/b + gates (Task 6). Register `register_refs` binding point: Task 2 dataclass + Task 5 report test. `.gitignore`: Task 1. Spec's `trace.py` is `trace_io.py` here — deliberate rename, stdlib-shadowing hazard, recorded in Global Constraints.
- **Known deliberate duplication:** the driver re-implements trace *writing* (not reading) so it stays importable under the tag. Pinned by the Task 5 integration test, which round-trips driver-written files through `load_trace`.
- **Type consistency check:** `CellVerdict.kind` is `str` (not an Enum) so `dataclasses.asdict` stays JSON-serializable without custom encoding; verdict kinds appear as string literals in exactly the six spellings listed in Task 2.
