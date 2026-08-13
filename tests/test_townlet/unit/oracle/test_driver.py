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
    driver.run_trace(pack=PACK, level=LEVEL, num_agents=4, steps=3, seed=42, device="cpu", out=out)
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
        driver.run_trace(pack=PACK, level=LEVEL, num_agents=4, steps=3, seed=42, device="cpu", out=out)
    ta, tb = load_trace(a), load_trace(b)
    np.testing.assert_array_equal(ta.obs, tb.obs)
    np.testing.assert_array_equal(ta.rewards, tb.rewards)


def test_driver_source_is_self_contained() -> None:
    """The driver must run under the frozen tag's src, where townlet.oracle
    does not exist. Any import of townlet.oracle is a defect by construction."""
    source = Path(driver.__file__).read_text()
    assert not re.search(r"from\s+townlet\.oracle|import\s+townlet\.oracle", source)
