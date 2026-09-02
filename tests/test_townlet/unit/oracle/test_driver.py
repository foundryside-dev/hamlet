"""Driver smoke test: produces a valid trace file in-process (WS-7)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pytest

from townlet.oracle import driver
from townlet.oracle.trace_io import TRACE_FORMAT_VERSION, load_trace

PACK = "configs/default_curriculum"
LEVEL = "L0_0_minimal"


def test_driver_writes_a_loadable_trace(tmp_path: Path) -> None:
    out = tmp_path / "trace.npz"
    driver.run_trace(pack=PACK, pack_root=".", level=LEVEL, num_agents=4, steps=3, seed=42, device="cpu", out=out)
    trace = load_trace(out)
    assert trace.params.level == LEVEL
    assert trace.params.seed == 42
    assert trace.obs.shape[0] == 4  # steps + 1, reset included
    assert trace.obs.shape[1] == 4  # num_agents
    assert trace.rewards.shape == (3, 4)
    assert trace.dones.shape == (3, 4)
    assert trace.dones.dtype == np.bool_
    assert trace.actions.shape == (3, 4)
    assert trace.actions.dtype == np.int64
    assert trace.action_source == "seeded-random"
    # Provenance hashes: shared universe hashes plus the selected level's hashes.
    assert trace.hashes["vfs_hash"]
    assert trace.hashes["observation_schema_hash"]
    assert "training_hash" in trace.hashes
    # FIX 5: the driver records the code root it actually imported townlet
    # from, so the harness can catch a failed PYTHONPATH injection.
    assert trace.code_root
    assert Path(trace.code_root).name == "src"


def test_driver_format_version_matches_trace_io() -> None:
    """driver.py is self-contained and cannot import trace_io.py, so the two
    modules' TRACE_FORMAT_VERSION constants must be kept in sync by hand."""
    assert driver.TRACE_FORMAT_VERSION == TRACE_FORMAT_VERSION == 4


def test_driver_is_deterministic_for_same_seed(tmp_path: Path) -> None:
    a, b = tmp_path / "a.npz", tmp_path / "b.npz"
    for out in (a, b):
        driver.run_trace(pack=PACK, pack_root=".", level=LEVEL, num_agents=4, steps=3, seed=42, device="cpu", out=out)
    ta, tb = load_trace(a), load_trace(b)
    np.testing.assert_array_equal(ta.obs, tb.obs)
    np.testing.assert_array_equal(ta.rewards, tb.rewards)
    np.testing.assert_array_equal(ta.actions, tb.actions)


def test_driver_source_is_self_contained() -> None:
    """The driver must run under the frozen tag's src, where townlet.oracle
    does not exist. Any import of townlet.oracle is a defect by construction."""
    source = Path(driver.__file__).read_text()
    assert not re.search(r"from\s+townlet\.oracle|import\s+townlet\.oracle", source)


def _run(tmp_path, out_name, actions_path=None, steps=3, seed=7):
    from townlet.oracle.driver import run_trace

    out = tmp_path / out_name
    run_trace(
        pack="configs/test/model_config",
        pack_root=str(Path.cwd()),
        level="L0_test",
        num_agents=2,
        steps=steps,
        seed=seed,
        device="cpu",
        out=out,
        actions_path=actions_path,
    )
    return np.load(out.with_suffix(".npz")) if not out.name.endswith(".npz") else np.load(out)


def test_scripted_actions_are_stepped_verbatim(tmp_path):
    first = _run(tmp_path, "a.npz")
    recorded = first["actions"]
    script = tmp_path / "script.npz"
    np.savez_compressed(script, actions=recorded)
    replay = _run(tmp_path, "b.npz", actions_path=script)
    np.testing.assert_array_equal(replay["actions"], recorded)
    meta = json.loads(str(replay["meta"]))
    assert meta["action_source"].startswith("scripted:")
    # Same seed + same actions ⇒ identical dynamics on one tree:
    np.testing.assert_array_equal(replay["obs"], first["obs"])
    np.testing.assert_array_equal(replay["rewards"], first["rewards"])


def test_scripted_actions_wrong_shape_refuses(tmp_path):
    script = tmp_path / "bad.npz"
    np.savez_compressed(script, actions=np.zeros((99, 2), dtype=np.int64))
    with pytest.raises(ValueError, match="actions shape"):
        _run(tmp_path, "c.npz", actions_path=script)


def test_scripted_actions_out_of_range_refuses(tmp_path):
    script = tmp_path / "oob.npz"
    np.savez_compressed(script, actions=np.full((3, 2), 10_000, dtype=np.int64))
    with pytest.raises(ValueError, match="action_dim"):
        _run(tmp_path, "d.npz", actions_path=script)


def test_scripted_actions_wrong_key_refuses(tmp_path):
    script = tmp_path / "nokey.npz"
    np.savez_compressed(script, foo=np.zeros((3, 2), dtype=np.int64))
    with pytest.raises(ValueError, match="no 'actions' array"):
        _run(tmp_path, "e.npz", actions_path=script)


def test_scripted_actions_non_integer_dtype_refuses(tmp_path):
    script = tmp_path / "float.npz"
    np.savez_compressed(script, actions=np.zeros((3, 2), dtype=np.float32))
    with pytest.raises(ValueError, match="not integer"):
        _run(tmp_path, "f.npz", actions_path=script)
