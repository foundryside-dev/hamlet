"""The oracle's INPUTS are frozen, not just its code (hamlet-2090c9f16d).

The oracle pins code at a tag but resolved `--pack` against the live tree, and every
pack DTO is `extra="forbid"` — so one new key in a live pack made the frozen oracle
reject it at Stage 1 and every cell crashed for a schema reason instead of yielding a
verdict. Each side now resolves the same LOGICAL pack against its OWN root.

The guard these tests protect is the drift check. Freezing inputs introduces a new
failure mode that is worse than the bug it fixes, because it is silent and green: a
frozen pack that rots into a different universe still compiles, and then every cell
AGREEs about nothing (PDR-0052's reversal trigger). So drift is a per-cell failure
unless the cell explicitly declares it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import townlet.oracle.harness as harness_mod
from townlet.oracle.harness import ORACLE_PACK_ROOT, pack_drift, run_cell
from townlet.oracle.matrix import Cell, default_cells
from townlet.oracle.trace_io import RunParams

REPO_ROOT = Path(__file__).resolve().parents[4]


def _matrix_packs() -> list[str]:
    return sorted({cell.params.pack for cell in default_cells()})


def test_every_matrix_pack_has_a_frozen_fixture() -> None:
    """A live pack with no frozen counterpart means the oracle side has nothing
    to read — the exact hole this change closes."""
    missing = [p for p in _matrix_packs() if not (REPO_ROOT / ORACLE_PACK_ROOT / p).is_dir()]
    assert not missing, f"matrix packs with no frozen fixture under {ORACLE_PACK_ROOT}/: {missing}"


@pytest.mark.parametrize("logical_pack", _matrix_packs())
def test_every_drifting_pack_is_declared_by_every_cell_that_reads_it(logical_pack: str) -> None:
    """The freeze was a provable no-op until DIV-004; now it is not, and this
    test is what stopped that from being absorbed silently.

    It was written as `pack_drift(...) == {}` and it FAILED the moment the
    first schema change landed — which is exactly the job. Rewritten to the
    weaker-but-still-load-bearing claim: drift is permitted only where every
    cell reading that pack names a register entry for it. A pack that drifts
    with even one cell silent still fails here, before the harness runs.
    """
    drift = pack_drift(REPO_ROOT, logical_pack)
    readers = [cell for cell in default_cells() if cell.params.pack == logical_pack]
    assert readers, f"no matrix cell reads {logical_pack}"
    undeclared = [cell.cell_id for cell in readers if not cell.declares_pack_divergence]
    if drift:
        assert (
            not undeclared
        ), f"{logical_pack} drifts from its frozen fixture but these cells declare nothing: {undeclared}\n  drift: {drift}"
    else:
        # No drift is the resting state, and a declaration with nothing to
        # declare is a stale entry — the same failure REGISTERED_DIVERGENCE_ABSENT
        # names for output divergences.
        stale = [cell.cell_id for cell in readers if cell.declares_pack_divergence]
        assert (
            not stale
        ), f"{logical_pack} is byte-identical to its frozen fixture, but these cells still declare a pack divergence: {stale}"


def test_fixtures_live_outside_configs() -> None:
    """scripts/validate_compiler_cli.py walks configs/ recursively. Frozen
    fixtures held deliberately at an older schema must not be re-validated
    against the current one, so they must not live under configs/."""
    assert not ORACLE_PACK_ROOT.startswith("configs")
    assert not (REPO_ROOT / "configs" / ORACLE_PACK_ROOT).exists()


def test_undeclared_drift_fails_the_cell(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Silent drift is the failure mode freezing introduces. Undeclared, it must
    fail the cell — never quietly compare two different universes."""
    monkeypatch.setattr(harness_mod, "pack_drift", lambda *_a, **_k: {"differing": ["environment.yaml"]})
    cell = Cell(RunParams(pack="configs/default_curriculum", level="L0_0_minimal", num_agents=1, steps=1, seed=1, device="cpu"))
    assert cell.declares_pack_divergence is False

    verdict = run_cell(repo_root=tmp_path, old_src=tmp_path, new_src=tmp_path, cell=cell, run_dir=tmp_path, run_cuda=False)

    assert verdict.kind == "HARNESS_ERROR"
    assert verdict.detail["delta"] == {"differing": ["environment.yaml"]}
    assert "declared divergence" in str(verdict.detail["reason"])


def test_declared_drift_lets_the_cell_proceed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Declaring the divergence is the recorded human judgement that the two
    packs still describe the same universe in two schemas. It lets the cell run;
    it does NOT bless whatever the comparison then finds."""
    monkeypatch.setattr(harness_mod, "pack_drift", lambda *_a, **_k: {"differing": ["environment.yaml"]})
    calls: list[str] = []

    def fake_run_side(*, driver: Path, src: Path, params: RunParams, out: Path, repo_root: Path, pack_root: Path):
        calls.append(str(pack_root))
        return harness_mod.SideFailure(kind="crashed", stderr="stop here — the cell got past the drift gate")

    monkeypatch.setattr(harness_mod, "run_side", fake_run_side)
    cell = Cell(
        RunParams(pack="configs/default_curriculum", level="L0_0_minimal", num_agents=1, steps=1, seed=1, device="cpu"),
        pack_divergence="DIV-EXAMPLE",
    )
    assert cell.declares_pack_divergence is True

    verdict = run_cell(repo_root=tmp_path, old_src=tmp_path, new_src=tmp_path, cell=cell, run_dir=tmp_path, run_cuda=False)

    assert verdict.kind != "HARNESS_ERROR"
    assert calls == [str(tmp_path / ORACLE_PACK_ROOT)], "the old side must resolve the FROZEN root"


def test_absent_live_pack_is_not_reported_as_drift(tmp_path: Path) -> None:
    """No live pack means there is no drift question — the compiler reports the
    real problem far more clearly, and synthetic unit-test cells legitimately
    name packs that exist on neither side."""
    assert pack_drift(tmp_path, "configs/does_not_exist") == {}


def test_live_pack_without_a_fixture_is_reported(tmp_path: Path) -> None:
    """The inverse, and the one that matters: a real pack the oracle cannot see."""
    live = tmp_path / "configs" / "orphan"
    live.mkdir(parents=True)
    (live / "environment.yaml").write_text("environment: {}\n")
    assert "missing_frozen_pack" in pack_drift(tmp_path, "configs/orphan")


def test_build_caches_are_not_drift(tmp_path: Path) -> None:
    """.compiled is a build artifact, not a declaration — it appears in live
    packs and never in fixtures, and must not be mistaken for schema drift."""
    for root in (tmp_path / "configs" / "p", tmp_path / ORACLE_PACK_ROOT / "configs" / "p"):
        root.mkdir(parents=True)
        (root / "environment.yaml").write_text("environment: {}\n")
    cache = tmp_path / "configs" / "p" / ".compiled"
    cache.mkdir()
    (cache / "universe-L0.msgpack").write_bytes(b"\x00binary cache\x00")

    assert pack_drift(tmp_path, "configs/p") == {}
