"""Trace file format: save/load round-trip (WS-7 differential harness)."""

from __future__ import annotations

import json
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
        actions=np.zeros((3, 4), dtype=np.int64),
        code_root="/fake/oracle-tag/src",
        pack_root="/fake/pack-root",
        action_source="seeded-random",
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
    assert loaded.code_root == trace.code_root


def test_load_rejects_unknown_format_version(tmp_path: Path) -> None:
    trace = _mk_trace()
    path = tmp_path / "trace.npz"
    save_trace(path, trace)
    # Corrupt the version in-place by rewriting the meta payload.
    data = dict(np.load(path, allow_pickle=False))
    meta = json.loads(str(data["meta"]))
    meta["format_version"] = 999
    data["meta"] = np.array(json.dumps(meta))
    np.savez_compressed(path, **data)
    with pytest.raises(ValueError, match="format_version"):
        load_trace(path)


def test_oracle_tag_constant() -> None:
    from townlet.oracle import ORACLE_TAG

    assert ORACLE_TAG == "oracle-2026-08-17"


def _v4_trace(tmp_path, steps=2, num_agents=2, obs_dim=3):
    """Round-trippable v4 trace with actions. Reused by later tasks' tests."""
    from townlet.oracle.trace_io import RunParams, Trace, load_trace, save_trace

    params = RunParams(pack="p", level="L", num_agents=num_agents, steps=steps, seed=1, device="cpu")
    trace = Trace(
        params=params,
        hashes={"config_hash": "abc"},
        obs=np.zeros((steps + 1, num_agents, obs_dim), dtype=np.float32),
        rewards=np.zeros((steps, num_agents), dtype=np.float32),
        dones=np.zeros((steps, num_agents), dtype=bool),
        actions=np.zeros((steps, num_agents), dtype=np.int64),
        code_root="/src",
        pack_root="/packs",
        action_source="seeded-random",
    )
    path = tmp_path / "t.npz"
    save_trace(path, trace)
    return trace, load_trace(path)


def test_v4_round_trips_actions_and_action_source(tmp_path):
    trace, loaded = _v4_trace(tmp_path)
    np.testing.assert_array_equal(loaded.actions, trace.actions)
    assert loaded.actions.dtype == np.int64
    assert loaded.action_source == "seeded-random"


def test_v3_trace_refuses_loudly(tmp_path):
    """Zero-backcompat: a pre-actions trace is regenerated, never accommodated."""
    from townlet.oracle.trace_io import load_trace

    meta = {"format_version": 3, "params": {}, "hashes": {}, "code_root": "x", "pack_root": "y"}
    path = tmp_path / "old.npz"
    np.savez_compressed(
        path,
        obs=np.zeros((1, 1, 1), dtype=np.float32),
        rewards=np.zeros((0, 1), dtype=np.float32),
        dones=np.zeros((0, 1), dtype=bool),
        meta=np.array(json.dumps(meta)),
    )
    with pytest.raises(ValueError, match="format_version 3"):
        load_trace(path)


def test_stream_steps_order_actions_dones_rewards_obs(tmp_path):
    from townlet.oracle.trace_io import _stream_steps

    trace, _ = _v4_trace(tmp_path, steps=1)
    names = [(step, stream) for step, stream, _ in _stream_steps(trace)]
    assert names == [(0, "obs"), (0, "actions"), (0, "dones"), (0, "rewards"), (1, "obs")]
