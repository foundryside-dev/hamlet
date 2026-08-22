"""compare_traces: the harness's judgement logic (WS-7 differential harness)."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from townlet.oracle.matrix import RegisteredHashDivergence, RegisteredStreamDivergence
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


def _trace(
    *,
    obs: np.ndarray | None = None,
    rewards: np.ndarray | None = None,
    dones: np.ndarray | None = None,
    actions: np.ndarray | None = None,
    hashes: dict[str, str | None] | None = None,
    obs_dim: int = 7,
    obs_shift: float = 0.0,
) -> Trace:
    # Independent RNGs (not one shared, sequential stream): overriding obs_dim
    # must not perturb the number of draws consumed and thereby change the
    # unrelated rewards array by coincidence.
    base_obs = np.random.default_rng(7).random((4, 4, obs_dim), dtype=np.float32)
    if obs_shift:
        base_obs = base_obs + obs_shift
    base_rewards = np.random.default_rng(70).random((3, 4), dtype=np.float32)
    return Trace(
        params=PARAMS,
        hashes=hashes if hashes is not None else {"vfs_hash": "abc", "action_schema_hash": "def", "items_hash": None},
        obs=obs if obs is not None else base_obs,
        rewards=rewards if rewards is not None else base_rewards,
        dones=dones if dones is not None else np.zeros((3, 4), dtype=bool),
        actions=actions if actions is not None else np.zeros((3, 4), dtype=np.int64),
        code_root="/fake/src",
        pack_root="/fake/pack-root",
        action_source="seeded-random",
    )


def test_identical_traces_agree() -> None:
    verdict = compare_traces(_trace(), _trace(), cell_id="c1")
    assert verdict.kind == "AGREE"
    assert verdict.cell_id == "c1"
    assert verdict.register_refs == ()


def test_reward_perturbation_locates_first_divergence() -> None:
    old, new = _trace(), _trace()
    new.rewards[1, 2] += 0.5  # step 1, agent 2
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    entry = verdict.detail["streams"]["rewards"]
    assert entry["step"] == 1
    assert [2] == [idx[0] for idx in entry["indices"]]
    assert entry["max_abs_diff"] == pytest.approx(0.5)


def test_action_divergence_locates_the_actions_stream() -> None:
    old, new = _trace(), _trace()
    new.actions[0, 1] += 1
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    entry = verdict.detail["streams"]["actions"]
    assert entry["step"] == 0


def test_reset_obs_divergence_reports_step_zero() -> None:
    old, new = _trace(), _trace()
    new.obs[0, 0, 0] += 1.0
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    entry = verdict.detail["streams"]["obs"]
    assert entry["step"] == 0


def test_every_diverging_stream_is_reported() -> None:
    """Was test_earliest_step_wins_across_streams: pre-Task-4 adjudication
    short-circuited on the first mismatching stream and reported only it.
    Task 4 replaces that with full-trace collection, so BOTH streams that
    diverge here are reported, not just the earliest one."""
    old, new = _trace(), _trace()
    new.dones[0, 1] = True  # step 0 of dones == trace step 0
    new.rewards[2, 0] += 1.0
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    assert set(verdict.detail["streams"]) == {"dones", "rewards"}
    assert verdict.detail["streams"]["dones"]["step"] == 0
    assert "max_abs_diff" not in verdict.detail["streams"]["dones"]
    assert verdict.detail["streams"]["rewards"]["step"] == 2


def test_hash_mismatch_short_circuits_traces() -> None:
    old, new = _trace(), _trace()
    object.__setattr__(new, "hashes", {**old.hashes, "vfs_hash": "OTHER"})
    new.rewards[0, 0] += 1.0  # would also diverge, must not be reached
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "HASH_MISMATCH"
    assert verdict.detail["mismatched"] == {"vfs_hash": {"old": "abc", "new": "OTHER"}}


def test_differing_hash_key_sets_are_a_mismatch() -> None:
    old, new = _trace(), _trace()
    object.__setattr__(new, "hashes", {**old.hashes, "novel_hash": "x"})
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "HASH_MISMATCH"
    assert "novel_hash" in verdict.detail["mismatched"]


def test_params_mismatch_is_a_harness_bug() -> None:
    old, new = _trace(), _trace()
    object.__setattr__(new, "params", dataclasses.replace(PARAMS, seed=43))
    with pytest.raises(HarnessError, match="params"):
        compare_traces(old, new, cell_id="c1")


def test_verdict_is_json_serializable() -> None:
    import json

    old, new = _trace(), _trace()
    new.rewards[1, 2] += 0.5
    verdict = compare_traces(old, new, cell_id="c1")
    json.dumps(dataclasses.asdict(verdict))  # must not raise


def test_negative_zero_vs_zero_diverges_and_localizes() -> None:
    """0.0 == -0.0 under value equality but their bytes differ — the spec
    requires byte-exact comparison, so this must DIVERGE, not AGREE."""
    old, new = _trace(), _trace()
    old.rewards[0, 0] = 0.0
    new.rewards[0, 0] = -0.0
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    entry = verdict.detail["streams"]["rewards"]
    assert entry["step"] == 0
    assert [0] == [idx[0] for idx in entry["indices"]]


def test_identical_nan_agrees() -> None:
    """NaN != NaN under value equality but identical bytes are identical —
    byte-exact comparison must treat this as AGREE, not a false DIVERGE."""
    old, new = _trace(), _trace()
    old.rewards[0, 0] = np.nan
    new.rewards[0, 0] = np.nan
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "AGREE"


def test_shape_mismatch_diverges_instead_of_false_agreeing() -> None:
    """tobytes() is shape-blind: np.zeros((4,)) and np.zeros((4,1)) serialize
    identically. A rebuild that returns rewards as [num_agents,1] instead of
    [num_agents] must DIVERGE, not silently AGREE via byte equality."""
    old, new = _trace(), _trace()
    object.__setattr__(new, "rewards", new.rewards.reshape(3, 4, 1))
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    entry = verdict.detail["streams"]["rewards"]
    assert entry["step"] == 0
    assert entry["shape_changed"] is True
    assert entry["old_shape"] == [4]
    assert entry["new_shape"] == [4, 1]
    assert entry["old_dtype"] == "float32"
    assert entry["new_dtype"] == "float32"
    # JSON-safe.
    import json

    json.dumps(dataclasses.asdict(verdict))


def test_dtype_mismatch_diverges() -> None:
    old, new = _trace(), _trace()
    object.__setattr__(new, "dones", new.dones.astype(np.int64))
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    entry = verdict.detail["streams"]["dones"]
    assert entry["old_dtype"] == "bool"
    assert entry["new_dtype"] == "int64"


def test_shape_preflight_runs_before_byte_comparison() -> None:
    """Shape/dtype divergence must be caught even when the reshaped array's
    bytes happen to be identical to the original (tobytes() alone would
    falsely AGREE)."""
    old, new = _trace(), _trace()
    same_bytes_reshaped = old.rewards.reshape(3, 4, 1).copy()
    assert same_bytes_reshaped.tobytes() == old.rewards.tobytes()
    object.__setattr__(new, "rewards", same_bytes_reshaped)
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    entry = verdict.detail["streams"]["rewards"]
    assert entry["old_shape"] == [4]
    assert entry["new_shape"] == [4, 1]


def test_broadcast_incompatible_shapes_diverge_not_raise() -> None:
    """Before the shape preflight, a broadcast-incompatible mismatch reached
    _divergence_mask and raised ValueError instead of yielding a verdict —
    exactly the case (emitted tensor vs. declared VFS schema width) the
    harness exists to catch. Must DIVERGE, never raise."""
    old, new = _trace(), _trace()
    object.__setattr__(new, "rewards", np.zeros((3, 7), dtype=np.float32))  # 7 != 4, not broadcastable
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    entry = verdict.detail["streams"]["rewards"]
    assert entry["old_shape"] == [4]
    assert entry["new_shape"] == [7]


def test_absent_hash_key_distinguished_from_none_value() -> None:
    """.get(name) returns None both when a key is missing and when it is
    present with value None — a field ABSENT from the rebuild's hash surface
    must not be indistinguishable from a field PRESENT but unset."""
    old, new = _trace(), _trace()
    object.__setattr__(old, "hashes", {"items_hash": None})
    object.__setattr__(new, "hashes", {})
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "HASH_MISMATCH"
    assert "items_hash" in verdict.detail["mismatched"]
    assert verdict.detail["mismatched"]["items_hash"]["old"] is None
    assert verdict.detail["mismatched"]["items_hash"]["new"] == "<absent>"


def test_nan_vs_number_diverges_with_json_safe_verdict() -> None:
    import json

    old, new = _trace(), _trace()
    old.rewards[0, 0] = np.nan
    new.rewards[0, 0] = 1.0
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "DIVERGE"
    entry = verdict.detail["streams"]["rewards"]
    assert entry["step"] == 0
    assert [0] == [idx[0] for idx in entry["indices"]]
    assert entry["max_abs_diff"] == "non-finite"
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
    old, new = _trace(), _trace()
    new.hashes["vfs_hash"] = "moved"
    verdict = compare_traces(old, new, cell_id="c1", hash_divergence=_declare("vfs_hash"))
    assert verdict.kind == "DIVERGED_AS_REGISTERED"
    assert verdict.register_refs == ("DIV-004",)
    assert verdict.detail["shape"] == "hash-only"


def test_an_undeclared_hash_moving_alongside_a_declared_one_still_fails() -> None:
    """The declaration is enumerated, not a wildcard: a rebuild that moves more
    than the entry claims must stay red, and the report must say which."""
    old, new = _trace(), _trace()
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
    old, new = _trace(), _trace()
    new.hashes["vfs_hash"] = "moved"
    verdict = compare_traces(old, new, cell_id="c1", hash_divergence=_declare("vfs_hash", "items_hash"))
    assert verdict.kind == "REGISTERED_DIVERGENCE_ABSENT"
    assert verdict.register_refs == ()
    assert verdict.detail["declared_but_unmoved"] == ["items_hash"]


def test_a_declaration_never_suppresses_a_stream_divergence() -> None:
    """The load-bearing guarantee. If this ever fails, the shape has become the
    false-AGREE machine PDR-0033 warns about and must be reverted, not relaxed."""
    old, new = _trace(), _trace()
    new.hashes["vfs_hash"] = "moved"
    new.rewards[1, 2] += 0.5
    verdict = compare_traces(old, new, cell_id="c1", hash_divergence=_declare("vfs_hash"))
    assert verdict.kind == "DIVERGE"
    assert verdict.register_refs == ()
    assert verdict.detail["streams"]["rewards"]["step"] == 1


def test_no_declaration_leaves_the_original_hash_behaviour_untouched() -> None:
    old, new = _trace(), _trace()
    new.hashes["vfs_hash"] = "moved"
    verdict = compare_traces(old, new, cell_id="c1")
    assert verdict.kind == "HASH_MISMATCH"
    assert verdict.register_refs == ()


def test_a_declaration_with_nothing_to_declare_does_not_launder_an_agree() -> None:
    """Streams agree and no hash moved, but the cell declared one would: that is
    a stale entry, and reporting AGREE would hide it."""
    verdict = compare_traces(_trace(), _trace(), cell_id="c1", hash_divergence=_declare("vfs_hash"))
    assert verdict.kind == "REGISTERED_DIVERGENCE_ABSENT"


# --- non-short-circuiting per-stream adjudication (SA-C1, hamlet-fa6bb6da4a) --
#
# compare_traces used to return on the FIRST mismatching stream. That masked
# every later stream: a registered obs divergence (the token cut changes
# total_dims) could hide a real rewards/dones regression riding along with it.
# These tests pin the replacement: every stream is scanned to completion, and
# RegisteredStreamDivergence narrows in BOTH directions — a declared stream
# that never diverges is as much a finding as an undeclared one that does.

DIV8_STREAMS = RegisteredStreamDivergence(register_ref="DIV-008", streams=("obs",))


def test_undeclared_divergence_reports_every_stream_not_just_the_first():
    """SA-C1: today the first mismatching stream (frame-zero obs) masks the rest."""
    old = _trace()
    new = _trace(obs=old.obs + 1.0, rewards=old.rewards + 1.0)
    v = compare_traces(old, new, "cell")
    assert v.kind == "DIVERGE"
    assert set(v.detail["streams"]) == {"obs", "rewards"}


def test_registered_obs_divergence_with_clean_dynamics_passes():
    old = _trace()
    new = _trace(obs=old.obs + 1.0)
    v = compare_traces(old, new, "cell", stream_divergence=DIV8_STREAMS)
    assert v.kind == "DIVERGED_AS_REGISTERED"
    assert v.register_refs == ("DIV-008",)


def test_registered_obs_shape_change_is_exempt_from_preflight():
    """(d): the token cut changes total_dims — a declared stream may differ in SHAPE."""
    old = _trace(obs_dim=4)
    new = _trace(obs_dim=9)
    v = compare_traces(old, new, "cell", stream_divergence=DIV8_STREAMS)
    assert v.kind == "DIVERGED_AS_REGISTERED"
    assert v.detail["streams"]["obs"]["shape_changed"] is True


def test_registered_obs_but_rewards_also_diverge_fails():
    old = _trace()
    new = _trace(obs=old.obs + 1.0, rewards=old.rewards + 0.5)
    v = compare_traces(old, new, "cell", stream_divergence=DIV8_STREAMS)
    assert v.kind == "DIVERGE"
    assert "rewards" in v.detail["streams"]
    assert v.register_refs == ()


def test_undeclared_shape_change_still_hard_fails():
    old = _trace(obs_dim=4)
    new = _trace(obs_dim=9)
    v = compare_traces(old, new, "cell")
    assert v.kind == "DIVERGE"
    assert v.detail["streams"]["obs"]["shape_changed"] is True


def test_declared_stream_that_never_diverges_is_a_stale_entry():
    old = _trace()
    new = _trace()  # byte-identical
    v = compare_traces(old, new, "cell", stream_divergence=DIV8_STREAMS)
    assert v.kind == "REGISTERED_DIVERGENCE_ABSENT"
    assert v.detail["declared_but_unmoved_streams"] == ["obs"]


def test_hash_and_stream_declarations_compose_under_one_ref():
    """The DIV-008 shape: hashes move as declared AND obs diverges as declared."""
    hd = RegisteredHashDivergence(register_ref="DIV-008", hash_fields=("observation_schema_hash",))
    old = _trace(hashes={"observation_schema_hash": "a", "config_hash": "z"})
    new = _trace(hashes={"observation_schema_hash": "b", "config_hash": "z"}, obs_shift=1.0)
    v = compare_traces(old, new, "cell", hash_divergence=hd, stream_divergence=DIV8_STREAMS)
    assert v.kind == "DIVERGED_AS_REGISTERED"
    assert v.register_refs == ("DIV-008",)  # deduped, one entry binding both shapes


def test_actions_stream_divergence_is_adjudicated():
    """RNG-stream coupling becomes visible: differing draws are an actions DIVERGE."""
    old = _trace()
    new = _trace(actions=old.actions + 1)
    v = compare_traces(old, new, "cell")
    assert v.kind == "DIVERGE"
    assert "actions" in v.detail["streams"]
