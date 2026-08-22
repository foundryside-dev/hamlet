"""compare_traces: the harness's judgement logic (WS-7 differential harness)."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from townlet.oracle.matrix import RegisteredHashDivergence
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
        actions=np.zeros((3, 4), dtype=np.int64),
        code_root="/fake/src",
        pack_root="/fake/pack-root",
        action_source="seeded-random",
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


def test_action_divergence_locates_the_actions_stream() -> None:
    old, new = _mk_trace(), _mk_trace()
    new.actions[0, 1] += 1
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    assert verdict.detail["step"] == 0
    assert verdict.detail["stream"] == "actions"


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


def test_negative_zero_vs_zero_diverges_and_localizes() -> None:
    """0.0 == -0.0 under value equality but their bytes differ — the spec
    requires byte-exact comparison, so this must DIVERGE, not AGREE."""
    old, new = _mk_trace(), _mk_trace()
    old.rewards[0, 0] = 0.0
    new.rewards[0, 0] = -0.0
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    assert verdict.detail["step"] == 0
    assert verdict.detail["stream"] == "rewards"
    assert [0] == [idx[0] for idx in verdict.detail["indices"]]


def test_identical_nan_agrees() -> None:
    """NaN != NaN under value equality but identical bytes are identical —
    byte-exact comparison must treat this as AGREE, not a false DIVERGE."""
    old, new = _mk_trace(), _mk_trace()
    old.rewards[0, 0] = np.nan
    new.rewards[0, 0] = np.nan
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "AGREE"


def test_shape_mismatch_diverges_instead_of_false_agreeing() -> None:
    """tobytes() is shape-blind: np.zeros((4,)) and np.zeros((4,1)) serialize
    identically. A rebuild that returns rewards as [num_agents,1] instead of
    [num_agents] must DIVERGE, not silently AGREE via byte equality."""
    old, new = _mk_trace(), _mk_trace()
    object.__setattr__(new, "rewards", new.rewards.reshape(3, 4, 1))
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    assert verdict.detail["step"] == 0
    assert verdict.detail["stream"] == "rewards"
    assert verdict.detail["old_shape"] == [4]
    assert verdict.detail["new_shape"] == [4, 1]
    assert verdict.detail["old_dtype"] == "float32"
    assert verdict.detail["new_dtype"] == "float32"
    # JSON-safe.
    import json

    json.dumps(dataclasses.asdict(verdict))


def test_dtype_mismatch_diverges() -> None:
    old, new = _mk_trace(), _mk_trace()
    object.__setattr__(new, "dones", new.dones.astype(np.int64))
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    assert verdict.detail["stream"] == "dones"
    assert verdict.detail["old_dtype"] == "bool"
    assert verdict.detail["new_dtype"] == "int64"


def test_shape_preflight_runs_before_byte_comparison() -> None:
    """Shape/dtype divergence must be caught even when the reshaped array's
    bytes happen to be identical to the original (tobytes() alone would
    falsely AGREE)."""
    old, new = _mk_trace(), _mk_trace()
    same_bytes_reshaped = old.rewards.reshape(3, 4, 1).copy()
    assert same_bytes_reshaped.tobytes() == old.rewards.tobytes()
    object.__setattr__(new, "rewards", same_bytes_reshaped)
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    assert verdict.detail["old_shape"] == [4]
    assert verdict.detail["new_shape"] == [4, 1]


def test_broadcast_incompatible_shapes_diverge_not_raise() -> None:
    """Before the shape preflight, a broadcast-incompatible mismatch reached
    _divergence_mask and raised ValueError instead of yielding a verdict —
    exactly the case (emitted tensor vs. declared VFS schema width) the
    harness exists to catch. Must DIVERGE, never raise."""
    old, new = _mk_trace(), _mk_trace()
    object.__setattr__(new, "rewards", np.zeros((3, 7), dtype=np.float32))  # 7 != 4, not broadcastable
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    assert verdict.detail["old_shape"] == [4]
    assert verdict.detail["new_shape"] == [7]


def test_absent_hash_key_distinguished_from_none_value() -> None:
    """.get(name) returns None both when a key is missing and when it is
    present with value None — a field ABSENT from the rebuild's hash surface
    must not be indistinguishable from a field PRESENT but unset."""
    old, new = _mk_trace(), _mk_trace()
    object.__setattr__(old, "hashes", {"items_hash": None})
    object.__setattr__(new, "hashes", {})
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "HASH_MISMATCH"
    assert "items_hash" in verdict.detail["mismatched"]
    assert verdict.detail["mismatched"]["items_hash"]["old"] is None
    assert verdict.detail["mismatched"]["items_hash"]["new"] == "<absent>"


def test_nan_vs_number_diverges_with_json_safe_verdict() -> None:
    import json

    old, new = _mk_trace(), _mk_trace()
    old.rewards[0, 0] = np.nan
    new.rewards[0, 0] = 1.0
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    assert verdict.detail["step"] == 0
    assert verdict.detail["stream"] == "rewards"
    assert [0] == [idx[0] for idx in verdict.detail["indices"]]
    assert verdict.detail["max_abs_diff"] == "non-finite"
    dumped = json.dumps(dataclasses.asdict(verdict))
    assert "NaN" not in dumped
    json.loads(dumped)  # must be valid JSON, not the bare-NaN literal


# --- the hash-only divergence shape (DIV-004, PDR-0054) ----------------------
#
# The second RegisteredDivergence shape: provenance moved as registered,
# behaviour did not. Before it existed, compare_traces returned HASH_MISMATCH
# and short-circuited BEFORE comparing a single stream — so on any authoring-
# surface change (which is all of WS-4) the harness could not compare the thing
# that matters. These tests pin that the declaration suppresses ONLY the
# provenance inequality, never a behavioural one.


def _declare(*fields: str, ref: str = "DIV-004") -> RegisteredHashDivergence:
    return RegisteredHashDivergence(register_ref=ref, hash_fields=fields)


def test_declared_hash_move_with_identical_streams_passes_as_registered() -> None:
    old, new = _mk_trace(), _mk_trace()
    new.hashes["vfs_hash"] = "moved"
    verdict = compare_traces(old, new, cell_id="c1", hash_divergence=_declare("vfs_hash"))
    assert verdict.kind == "DIVERGED_AS_REGISTERED"
    assert verdict.register_refs == ("DIV-004",)
    assert verdict.detail["shape"] == "hash-only"


def test_an_undeclared_hash_moving_alongside_a_declared_one_still_fails() -> None:
    """The declaration is enumerated, not a wildcard: a rebuild that moves more
    than the entry claims must stay red, and the report must say which."""
    old, new = _mk_trace(), _mk_trace()
    new.hashes["vfs_hash"] = "moved"
    new.hashes["action_schema_hash"] = "also moved"
    verdict = compare_traces(old, new, cell_id="c1", hash_divergence=_declare("vfs_hash"))
    assert verdict.kind == "HASH_MISMATCH"
    assert verdict.register_refs == ()
    assert verdict.detail["undeclared_movers"] == ["action_schema_hash"]


def test_a_declared_hash_that_does_not_move_is_a_stale_entry() -> None:
    """Symmetric with REGISTERED_DIVERGENCE_ABSENT for the crash shape: an
    expectation that never fires leaves suppression machinery armed with
    nothing to suppress (PDR-0037 reversal trigger 3)."""
    old, new = _mk_trace(), _mk_trace()
    new.hashes["vfs_hash"] = "moved"
    verdict = compare_traces(old, new, cell_id="c1", hash_divergence=_declare("vfs_hash", "items_hash"))
    assert verdict.kind == "REGISTERED_DIVERGENCE_ABSENT"
    assert verdict.register_refs == ()
    assert verdict.detail["declared_but_unmoved"] == ["items_hash"]


def test_a_declaration_never_suppresses_a_stream_divergence() -> None:
    """The load-bearing guarantee. If this ever fails, the shape has become the
    false-AGREE machine PDR-0033 warns about and must be reverted, not relaxed."""
    old, new = _mk_trace(), _mk_trace()
    new.hashes["vfs_hash"] = "moved"
    new.rewards[1, 2] += 0.5
    verdict = compare_traces(old, new, cell_id="c1", hash_divergence=_declare("vfs_hash"))
    assert verdict.kind == "DIVERGE"
    assert verdict.register_refs == ()
    assert verdict.detail["step"] == 1


def test_no_declaration_leaves_the_original_hash_behaviour_untouched() -> None:
    old, new = _mk_trace(), _mk_trace()
    new.hashes["vfs_hash"] = "moved"
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "HASH_MISMATCH"
    assert verdict.register_refs == ()


def test_a_declaration_with_nothing_to_declare_does_not_launder_an_agree() -> None:
    """Streams agree and no hash moved, but the cell declared one would: that is
    a stale entry, and reporting AGREE would hide it."""
    verdict = compare_traces(_mk_trace(), _mk_trace(), cell_id="c1", hash_divergence=_declare("vfs_hash"))
    assert verdict.kind == "REGISTERED_DIVERGENCE_ABSENT"
