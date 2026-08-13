"""compare_traces: the harness's judgement logic (WS-7 differential harness)."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from townlet.oracle.trace_io import (
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
