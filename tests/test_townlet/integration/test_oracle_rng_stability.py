"""Seeded-random action draws are call-order stable on the current tree.

The scripted-action mode exists because RNG-stream coupling across the token cut
would decorrelate traces for a non-defect reason (spec §5). This pins the
BASELINE: two same-seed runs of the driver on ONE tree draw identical actions and
produce identical streams — so any future actions-stream divergence is real
evidence of RNG-consumption change, not noise. (Round-2 systems review asked for
exactly this check before trusting unit 1's all-AGREE as a clean baseline.)
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from townlet.oracle.driver import run_trace

PACK = "configs/test/model_config"
LEVEL = "L0_test"


def _trace(tmp_path: Path, name: str) -> dict[str, np.ndarray]:
    out = tmp_path / name
    run_trace(
        pack=PACK,
        pack_root=str(Path.cwd()),
        level=LEVEL,
        num_agents=2,
        steps=25,
        seed=1234,
        device="cpu",
        out=out,
        actions_path=None,
    )
    with np.load(out if out.suffix == ".npz" else out.with_suffix(".npz")) as data:
        return {k: np.asarray(data[k]) for k in ("obs", "rewards", "dones", "actions")} | {
            "action_source": json.loads(str(data["meta"]))["action_source"]
        }


def test_same_seed_same_tree_draws_identical_actions_and_streams(tmp_path):
    a = _trace(tmp_path, "a.npz")
    b = _trace(tmp_path, "b.npz")
    assert a["action_source"] == b["action_source"] == "seeded-random"
    for key in ("actions", "obs", "rewards", "dones"):
        np.testing.assert_array_equal(a[key], b[key]), key
