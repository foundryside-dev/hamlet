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
