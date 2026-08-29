"""Unit tests for scripts/l2_baseline.py pure functions (token-obs unit 3, Task 1).

Only the pure functions are tested here — pack seed rewriting and IQM. Training,
greedy eval and curve extraction are exercised operationally in Task 2 (they need
real GPU runs and are not unit-testable without violating the Phase-0 src freeze).
"""

import importlib.util
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
