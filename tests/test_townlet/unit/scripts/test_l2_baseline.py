"""Unit tests for scripts/l2_baseline.py pure functions (token-obs unit 3, Task 1).

Only the pure functions are tested here — pack seed rewriting and IQM. Training,
greedy eval and curve extraction are exercised operationally in Task 2 (they need
real GPU runs and are not unit-testable without violating the Phase-0 src freeze).
"""

import csv
import importlib.util
import sqlite3
from argparse import Namespace
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).parents[4] / "scripts" / "l2_baseline.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("l2_baseline", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def baseline():
    return _load_module()


def _make_pack(root: Path, seed: int = 42) -> Path:
    pack = root / "pack"
    level_dir = pack / "levels" / "L2_partial_observability"
    level_dir.mkdir(parents=True)
    (pack / "stratum.yaml").write_text("substrate:\n  type: grid\n")
    (level_dir / "training.yaml").write_text(
        "run_metadata:\n"
        '  output_subdir: "L2_partial_observability"\n'
        "\n"
        "training:\n"
        '  version: "1.0"\n'
        f"  seed: {seed}\n"
        "\n"
        "  population:\n"
        "    size: 8\n"
    )
    return pack


class TestRewriteSeed:
    def test_rewrite_changes_exactly_the_seed_line(self, baseline, tmp_path):
        src = _make_pack(tmp_path, seed=42)
        dst = tmp_path / "copy"
        diff = baseline.rewrite_seed(src, dst, seed=123)

        # The copy exists and carries the new seed; nothing else moved.
        new_text = (dst / "levels" / "L2_partial_observability" / "training.yaml").read_text()
        assert "  seed: 123\n" in new_text
        assert "seed: 42" not in new_text
        removed = [ln for ln in diff.splitlines() if ln.startswith("-") and not ln.startswith("---")]
        added = [ln for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
        assert removed == ["-  seed: 42"]
        assert added == ["+  seed: 123"]
        # The untouched sibling file is byte-identical.
        assert (dst / "stratum.yaml").read_text() == (src / "stratum.yaml").read_text()

    def test_zero_or_multiple_seed_lines_refuse(self, baseline, tmp_path):
        src = _make_pack(tmp_path, seed=42)
        cfg = src / "levels" / "L2_partial_observability" / "training.yaml"
        cfg.write_text(cfg.read_text() + "  seed: 7\n")  # a second seed line
        with pytest.raises(ValueError, match="exactly one"):
            baseline.rewrite_seed(src, tmp_path / "copy2", seed=123)

        cfg.write_text("training:\n  population:\n    size: 8\n")  # no seed line
        with pytest.raises(ValueError, match="exactly one"):
            baseline.rewrite_seed(src, tmp_path / "copy3", seed=123)


class TestIQM:
    def test_iqm_drops_tails(self, baseline):
        assert baseline.iqm([0, 0, 10, 10, 10, 10, 100, 100]) == 10.0

    def test_iqm_small_n_falls_back_to_mean(self, baseline):
        # n < 4 cannot shed a quartile each side; documented fallback is the mean.
        assert baseline.iqm([1.0, 2.0, 3.0]) == 2.0

    def test_iqm_empty_refuses(self, baseline):
        with pytest.raises(ValueError):
            baseline.iqm([])


def _write_accounting_run(run_dir: Path, *, duplicate: bool, wrong_survival: bool, old_columns: bool) -> None:
    """Persist real SQL and event files; the exporter consumes both boundaries."""
    from torch.utils.tensorboard import SummaryWriter

    from townlet.demo.database import DemoDatabase

    run_dir.mkdir()
    if old_columns:
        connection = sqlite3.connect(run_dir / "demo.db")
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("CREATE TABLE episodes (episode_id INTEGER, survival_time INTEGER, epsilon REAL, intrinsic_weight REAL)")
            connection.execute("INSERT INTO episodes VALUES (0, 2, 0.0, 0.0)")
            connection.commit()
        finally:
            connection.close()
    else:
        with DemoDatabase(run_dir / "demo.db") as database:
            for episode in (0, 1):
                database.insert_episode(
                    episode_id=episode,
                    timestamp=1.0,
                    survival_time=2,
                    batch_episode_steps=5,
                    live_agent_transitions=7,
                    completion_reason="authored_terminal",
                    total_reward=0.0,
                    extrinsic_reward=0.0,
                    intrinsic_reward=0.0,
                    shaping_reward=0.0,
                    intrinsic_weight=0.0,
                    curriculum_stage=0,
                    epsilon=0.0,
                    observation_schema_hash="accounting-test",
                )
    writer = SummaryWriter(str(run_dir / "tensorboard"))
    try:
        for episode in (0, 1):
            writer.add_scalar("agent_0/Episode/Survival_Time", 3 if wrong_survival else 2, episode)
            writer.add_scalar("agent_1/Episode/Survival_Time", 5, episode)
        if duplicate:
            writer.add_scalar("agent_0/Episode/Survival_Time", 2, 0)
    finally:
        writer.close()


class TestEpisodeAccountingCurves:
    def test_lane_batch_and_live_units_are_distinct(self, baseline, tmp_path):
        run_dir = tmp_path / "run"
        _write_accounting_run(run_dir, duplicate=False, wrong_survival=False, old_columns=False)
        baseline.cmd_curves(Namespace(run_dir=str(run_dir)))
        with (run_dir / "curves.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        assert [row["survival_steps_agent0"] for row in rows] == ["2", "2"]
        assert [row["batch_episode_steps"] for row in rows] == ["5", "5"]
        assert [row["live_agent_transitions"] for row in rows] == ["7", "7"]
        assert [row["total_live_agent_transitions_cumulative"] for row in rows] == ["7", "14"]

    @pytest.mark.parametrize("control", ["duplicate", "wrong_survival", "old_columns", "missing_events"])
    def test_incompatible_or_inconsistent_accounting_refuses_without_input_changes(self, baseline, tmp_path, control):
        run_dir = tmp_path / "run"
        _write_accounting_run(
            run_dir, duplicate=control == "duplicate", wrong_survival=control == "wrong_survival", old_columns=control == "old_columns"
        )
        if control == "missing_events":
            for path in (run_dir / "tensorboard").iterdir():
                path.unlink()
        inputs = {path: path.read_bytes() for path in run_dir.rglob("*") if path.is_file()}
        with pytest.raises((ValueError, sqlite3.OperationalError)):
            baseline.cmd_curves(Namespace(run_dir=str(run_dir)))
        assert all(path.read_bytes() == value for path, value in inputs.items())
        assert not (run_dir / "demo.db-wal").exists()
        assert not (run_dir / "demo.db-shm").exists()
